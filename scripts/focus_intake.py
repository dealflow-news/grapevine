"""Pure provenance adapter. No network, writes, source certification or Company facts."""
import copy
import hashlib
import json
import re
from datetime import date

KINDS={'unclassified','transaction_report','rumour','denial','market_analysis','regulatory_analysis','thematic_analysis','knowledge_method','interpretation','observation'}

def metadata(value):
    if isinstance(value,str):
        try:value=json.loads(value)
        except (ValueError,TypeError):return {}
    return value if isinstance(value,dict) else {}

def valid_day(value):
    try:
        return date.fromisoformat(str(value)).isoformat()
    except (ValueError, TypeError):
        return None

def intake(row):
    p=row.get('_payload') or row.get('payload') or {}
    if not isinstance(p,dict):p={}
    hints=metadata(row.get('extraction_hints'))
    declared=hints.get('focus_intake_v1') or p.get('focus_intake_v1') or {}
    if not isinstance(declared,dict):declared={}
    title=row.get('headline') or p.get('headline') or row.get('title') or ''
    kind=declared.get('kind_hint','unclassified')
    parent_q=row.get('content_qualification') or {}
    if kind=='unclassified' and isinstance(parent_q,dict) and parent_q.get('content_kind') in KINDS:
        kind=parent_q['content_kind'] # Classification hint only; no support/date inheritance.
    if row.get('note_type')=='KNOWLEDGE_CARD' and row.get('time_sensitivity')=='TIMELESS':kind='knowledge_method'
    if kind not in KINDS:kind='unclassified'
    if kind=='unclassified':
        for pattern,k in [(r'ontkent|denies|démenti','denial'),(r'gerucht|rumou?r|possible|mogelijke|zou ','rumour'),(r'regulatory|court|jurid|regulat','regulatory_analysis'),(r'market outlook|marktbeeld|market_analysis','market_analysis'),(r'overname|acquisition|merger|buyout','transaction_report')]:
            if re.search(pattern,title+' '+str(row.get('article_signal_type','')),re.I):kind=k;break
    url=row.get('source_url') or p.get('url') or declared.get('source_url') or None
    observation=valid_day(declared.get('observation_date') or p.get('obs_date'))
    # Dates declared by a model/manual capture remain hints, never named fact dates.
    result={'contract':'focus-intake/1','kind_hint':kind,'claim_support':'unverified',
            'source_url':url,'original_text':declared.get('original_text') or row.get('body') or p.get('headline') or title,
            'observation_date':observation,'event_date':None,'publication_date':None,
            'source_event_date_hint':valid_day(row.get('date_hint')),
            'parent_id':row.get('mi_id') or row.get('signal_id') or row.get('note_id') or row.get('_whisper_id'),
            'parent_workflow_status':row.get('status') or row.get('processing_status'),
            'source_review_inherited':False,'material_update':False}
    identity={k:result[k] for k in ['kind_hint','source_url','original_text','observation_date','source_event_date_hint']}
    identity['source_input_fingerprint']=declared.get('input_fingerprint')
    result['input_fingerprint']=hashlib.sha256(json.dumps(identity,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return copy.deepcopy(result)

def publication_intake(row):
    result=intake(row)
    # Original text stays in the existing raw carrier, not the public projection.
    result.pop('original_text',None)
    return result

def qualify_draft(note, source):
    result=copy.deepcopy(note)
    meta=intake(source)
    if result.get('note_type')=='KNOWLEDGE_CARD' and meta['kind_hint']!='knowledge_method':meta['kind_hint']='thematic_analysis'
    sd=result.setdefault('structured_data',{})
    # A source review cannot certify newly generated prose.
    sd.pop('qualification_review_v1',None)
    sd['focus_intake_v1']=meta
    sd['enrichment_receipt_v1']={'parent_id':meta['parent_id'],'input_fingerprint':meta['input_fingerprint'],'source_status_preserved':True}
    result['source_url']=meta['source_url']
    result['freshness_date']=meta['observation_date']
    result['time_sensitivity']='TIMELESS' if meta['kind_hint']=='knowledge_method' else 'STRUCTURAL' if result.get('note_type')=='KNOWLEDGE_CARD' else 'SHORT_TERM'
    return result
