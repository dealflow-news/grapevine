"""Read only the current intake window completely before applying receipt filters."""
import copy
from datetime import datetime

def parsed_time(value):
    try:
        result=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return result if result.tzinfo else None
    except (ValueError,TypeError):return None


def read_pages(read, table, params, *, page_size=100, max_rows=5000):
    rows=[];seen={}
    for offset in range(0,max_rows,page_size):
        page=read(table,{**params,'order':params.get('order','created_at.desc,mi_id.asc'),
                         'offset':str(offset),'limit':str(page_size)})
        if not isinstance(page,list):raise RuntimeError('Capture queue read incomplete; retry')
        for row in page:
            key=row.get('mi_id') or row.get('note_id')
            if not key:raise RuntimeError('Capture queue identity missing; retry')
            if key in seen:
                if seen[key]!=row:raise RuntimeError('Capture input changed during reading; retry')
                raise RuntimeError('Capture pagination repeated a record; retry')
            seen[key]=copy.deepcopy(row);rows.append(row)
        if len(page)<page_size:return rows
    raise RuntimeError('Capture scan boundary reached; retain work and review selection')


def intake_window(read, since, grace_cutoff):
    select='mi_id,scope,payload,period_start,generated_by,status,created_at'
    curated=read_pages(read,'market_intelligence',{'select':select,'period_type':'neq.run',
        'status':'in.(handled_curated,handled_quicksave)','created_at':'gte.'+since})
    opened=read_pages(read,'market_intelligence',{'select':select,'period_type':'neq.run',
        'status':'eq.open','and':f'(created_at.gte.{since},created_at.lte.{grace_cutoff})'})
    # A malformed or absent date must never bypass the grace period.
    start,end=parsed_time(since),parsed_time(grace_cutoff)
    if not start or not end:raise ValueError('Valid intake window required')
    opened=[row for row in opened if parsed_time(row.get('created_at'))
            and start<=parsed_time(row['created_at'])<=end]
    return curated+opened


def linked_notes(read, ids):
    out=[]
    for offset in range(0,len(ids),100):
        out.extend(read_pages(read,'grapevine_notes',{
            'select':'note_id,source_ref_id,structured_data,title,body,body_md,created_at',
            'source_ref_type':'eq.mi_id','source_ref_id':f'in.({",".join(ids[offset:offset+100])})',
            'order':'created_at.desc,note_id.asc'},page_size=200))
    return out
