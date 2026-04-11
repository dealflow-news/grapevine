#!/usr/bin/env python3
"""
IntelCapture — Nightly Intel-to-Grapevine enrichment + KnowledgeCard extraction
v1.1 | 2026-04-10

Reads unprocessed market_intelligence items, enriches each one via the
MarketWhisperSnippet prompt (Claude Sonnet + web search), and writes
a structured draft note to grapevine_notes.

Notes land as status='draft' — an analyst reviews before promoting to active.

Usage:
    python intel_capture.py                       # live run, default limit=10
    python intel_capture.py --dry-run             # fetch + call LLM, print only, no DB writes
    python intel_capture.py --limit=3             # process max 3 items
    python intel_capture.py --mi-id=<uuid>        # target one specific market_intelligence item
    python intel_capture.py --dry-run --limit=3   # test run
    python intel_capture.py --to-card=<note_id>   # extract KNOWLEDGE_CARD from pattern-candidate WHISPER_NOTE
    python intel_capture.py --to-card=<note_id> --dry-run  # preview card, no DB write
"""

import os, sys, json, re, textwrap, time
# Windows cp1252 fix
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'): sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from datetime import datetime, timezone, timedelta
from anthropic import Anthropic

# ── Config ─────────────────────────────────────────────────────────────────
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'): continue
                if '=' not in line: continue
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()

ANTHROPIC_KEY  = os.environ.get('ANTHROPIC_API_KEY', '')
SUPABASE_URL   = os.environ.get('SUPABASE_URL', 'https://rirkgpsdcaxnowwmliof.supabase.co')
SUPABASE_KEY   = os.environ.get('SUPABASE_SERVICE_KEY', '')
MODEL_SONNET   = os.environ.get('MODEL_SONNET', 'claude-sonnet-4-6')
MODEL_HAIKU    = os.environ.get('MODEL_HAIKU',  'claude-haiku-4-5-20251001')

DRY_RUN  = '--dry-run' in sys.argv
_lim_arg = next((a for a in sys.argv if a.startswith('--limit=')), None)
LIMIT    = int(_lim_arg.replace('--limit=', '')) if _lim_arg else 10
_mi_arg  = next((a for a in sys.argv if a.startswith('--mi-id=')), None)
TARGET_MI_ID = _mi_arg.replace('--mi-id=', '') if _mi_arg else None

_card_arg = next((a for a in sys.argv if a.startswith('--to-card=')), None)
TARGET_CARD_NOTE_ID = _card_arg.replace('--to-card=', '') if _card_arg else None

client = Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None

# ── Supabase helpers (minimal, same pattern as pipeline) ───────────────────
import httpx

def sb_get(table, params=None):
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
    }
    r = httpx.get(f'{SUPABASE_URL}/rest/v1/{table}', params=params, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def sb_post(table, data):
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation,resolution=ignore-duplicates',
    }
    r = httpx.post(f'{SUPABASE_URL}/rest/v1/{table}', json=data, headers=headers, timeout=30)
    if r.status_code in (200, 201): return r.json()
    if r.status_code == 409: return None
    raise Exception(f"HTTP {r.status_code}: {r.text[:200]}")

def sb_patch(table, filter_params, data):
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal',
    }
    r = httpx.patch(f'{SUPABASE_URL}/rest/v1/{table}',
                    params=filter_params, json=data, headers=headers, timeout=30)
    return r.status_code in (200, 204)

# ── MarketWhisperSnippet prompt ────────────────────────────────────────────
# Preserved verbatim from V4G specification.
# Do NOT alter the prompt structure — it produces a specific 3-section output
# that the parser below depends on.

MARKET_WHISPER_SYSTEM = """Act like a senior investigative M&A journalist and market-intelligence editor with 25 years' experience covering European mid-market deals, specializing in Benelux (BE/NL/LU) and Northern France (FR). You turn "market whispers" into verified, decision-ready briefs with disciplined sourcing.
Objective: Produce one standardized Market Whisper Snippet from the provided inputs and corroborate it with exactly ONE additional credible public source via online search.
Operating rules:
- If both text and link are provided: extract primarily from INPUT_TEXT; use INPUT_LINK only to clarify context.
- If only a link is provided and you cannot access it: say you could not access it and proceed only with what is visible (preview/snippet). Do not invent missing content.
- Use conservative attribution ("according to…", "the post claims…"). Never fabricate valuation, terms, timing, or status.
- Mid-market lens: focus on corporates and sponsors, typical EV range ~€20m–€500m (do not state numbers unless sourced).
Workflow:
1) Normalize: identify TEXT, LINK, or BOTH; separate what is explicitly stated from assumptions.
2) Extract deal signals: parties (buyer/sponsor/target), sector, geography (fit to JURISDICTION), rationale, timing, advisors, ownership, deal type.
3) Classify each item: FACT / INFERENCE / UNVERIFIED.
4) Mandatory online search: find exactly ONE additional credible public source that adds at least one new fact.
   - Prefer by jurisdiction:
     BE: Crossroads Bank for Enterprises (BCE/KBO), regulator filings, company site
     NL: KVK, AFM filings (if relevant), company site
     LU: RCS, company site
     FR: Infogreffe/INPI, BODACC, company site, reputable business press
   - Avoid sources that merely repeat the original post.
5) Reconcile: report conflicts; keep the most conservative interpretation.
Output exactly in this structure:
A) MARKET WHISPER SNIPPET (120–180 words, present tense, newsroom tone)
- Headline: [Sector/Deal] – [JURISDICTION]
- Lead: 1–2 sentences + why it matters in this market
- Key details (bullets): Who / Target / Location / Deal type (FACT/INFERENCE) / Advisors / Status (FACT/UNVERIFIED)
- What we know (2 bullets)
- What we don't know (2 bullets)
- Confidence: Low/Medium/High + 1-sentence justification
B) FACT TABLE (markdown table)
Item | Extracted from (Text/Link) | Classification | Notes
C) SOURCE BOX
- Input source: "Provided by user" (+ URL if supplied)
- Extra source (exactly 1): URL + publisher/org + date + new fact(s) added
Hard constraints:
- Use exactly ONE extra public source (no more, no less).
- If no credible corroborating source is found: write "No credible corroborating source found", include the exact search query used, then stop.
- Do not exceed 180 words for section A.
Take a deep breath and work on this problem step-by-step."""

def build_whisper_user_prompt(jurisdiction, input_text, input_link):
    parts = [f"JURISDICTION: {jurisdiction}"]
    if input_text:
        parts.append(f"INPUT_TEXT:\n{input_text[:1500]}")
    else:
        parts.append("INPUT_TEXT: (blank)")
    parts.append(f"INPUT_LINK: {input_link or '(blank)'}")
    return "\n\n".join(parts)

# ── LLM call with web search ───────────────────────────────────────────────

def call_market_whisper(jurisdiction, input_text, input_link, editorial_hints=None):
    """
    Call Claude Sonnet with web_search tool enabled.
    The MarketWhisperSnippet prompt requires exactly ONE online search
    to corroborate with a credible public source.
    Returns raw response text.
    """
    if not client:
        raise RuntimeError("No Anthropic client — set ANTHROPIC_API_KEY")

    user_prompt = build_whisper_user_prompt(jurisdiction, input_text, input_link)
    if editorial_hints:
        hint_lines = []
        if editorial_hints.get('why_it_matters'):
            hint_lines.append(f"Why it matters (editor): {editorial_hints['why_it_matters']}")
        if editorial_hints.get('trend_signal'):
            hint_lines.append(f"Trend/signal (editor): {editorial_hints['trend_signal']}")
        if editorial_hints.get('parties_to_watch'):
            hint_lines.append(f"Parties to watch (editor): {editorial_hints['parties_to_watch']}")
        if editorial_hints.get('uncertainty'):
            hint_lines.append(f"Key uncertainty (editor): {editorial_hints['uncertainty']}")
        # Include full editorial body if available (from body-only notes)
        if editorial_hints.get('editorial_body') and not hint_lines:
            hint_lines.append(f"Editorial context (full): {editorial_hints['editorial_body'][:800]}")
        # Lens/hypothesis comes first — it's the editorial anchor
        lens = editorial_hints.get('lens') or editorial_hints.get('title','')
        if lens:
            user_prompt += f'\n\n--- EDITORIAL LENS (analyst framing — use as primary angle) ---\n{lens}'
        if hint_lines:
            user_prompt += '\n\n--- EDITORIAL CONTEXT (supporting hints) ---\n' + '\n'.join(hint_lines)

    r = client.messages.create(
        model=MODEL_SONNET,
        max_tokens=1500,
        system=MARKET_WHISPER_SYSTEM,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{'role': 'user', 'content': user_prompt}]
    )

    # Collect all text blocks (tool results are handled by the model internally)
    full_text = '\n'.join(
        block.text for block in r.content
        if hasattr(block, 'text') and block.type == 'text'
    ).strip()

    return full_text

# ── Output parser ─────────────────────────────────────────────────────────

def parse_whisper_output(raw_text):
    """
    Parse the three-section MarketWhisperSnippet output into structured fields.
    Returns dict with: title, body_md, summary_short, confidence, structured_data
    """
    result = {
        'title': '',  # ** stripped below
        'body_md': '',
        'summary_short': '',
        'confidence': 'medium',
        'structured_data': {
            'fact_table': '',
            'source_box': '',
            'whisper_meta': {},
            'raw_output': raw_text,
        }
    }

    # Split on section markers
    section_a = ''
    section_b = ''
    section_c = ''

    # Find A) B) C) markers (case-insensitive, allow whitespace)
    a_match = re.search(r'A\)\s*MARKET WHISPER SNIPPET', raw_text, re.IGNORECASE)
    b_match = re.search(r'B\)\s*FACT TABLE', raw_text, re.IGNORECASE)
    c_match = re.search(r'C\)\s*SOURCE BOX', raw_text, re.IGNORECASE)

    if a_match and b_match:
        section_a = raw_text[a_match.start():b_match.start()].strip()
    if b_match and c_match:
        section_b = raw_text[b_match.start():c_match.start()].strip()
    if c_match:
        section_c = raw_text[c_match.start():].strip()

    # If section markers not found, use full text as body
    if not section_a:
        section_a = raw_text

    # Strip 'A) MARKET WHISPER SNIPPET' header line from body before storing
    clean_a = re.sub(r'^.*?A\)\s*MARKET WHISPER SNIPPET.*?\n+', '', section_a, flags=re.IGNORECASE).strip()
    # Also strip any leading ⚠️ note blocks (inaccessible URL warnings)
    clean_a = re.sub(r'^⚠.*?\n\n---\n+', '', clean_a, flags=re.DOTALL).strip()
    result['body_md'] = clean_a
    result['structured_data']['fact_table'] = section_b
    result['structured_data']['source_box'] = section_c

    # Extract headline
    headline_match = re.search(r'Headline:\s*(.+)', section_a)
    if headline_match:
        result['title'] = headline_match.group(1).replace('**','').strip()
    else:
        # Fallback: use first meaningful line of section_a as title
        for line in clean_a.split('\n'):
            t = line.strip().lstrip('#').strip().replace('**','').strip()
            if len(t) > 10 and not t.startswith('-') and not t.startswith('*'):
                result['title'] = t[:150]
                break

    # Extract lead (first 1-2 sentences after "Lead:")
    lead_match = re.search(r'Lead:\s*(.+?)(?=\n[-•*]|\nKey details|\nWhat we)', section_a, re.DOTALL)
    if lead_match:
        result['summary_short'] = lead_match.group(1).replace('**','').strip()[:300]
    else:
        # Fallback: first non-empty line after headline
        lines = [l.strip() for l in section_a.split('\n') if l.strip() and 'Headline' not in l]
        if lines:
            result['summary_short'] = lines[0].replace('**','').strip()[:300]

    # Extract confidence
    conf_match = re.search(r'Confidence:\s*(Low|Medium|High)', section_a, re.IGNORECASE)
    if conf_match:
        result['confidence'] = conf_match.group(1).lower()

    # Extract what we know / don't know
    know_match = re.search(r'What we know\s*[:\n](.*?)(?=What we don|$)', section_a, re.DOTALL | re.IGNORECASE)
    dontknow_match = re.search(r"What we don'?t know\s*[:\n](.*?)(?=Confidence:|$)", section_a, re.DOTALL | re.IGNORECASE)
    if know_match:
        result['structured_data']['whisper_meta']['what_we_know'] = know_match.group(1).strip()
    if dontknow_match:
        result['structured_data']['whisper_meta']['what_we_dont_know'] = dontknow_match.group(1).strip()

    return result

# ── KnowledgeCardExtractor ─────────────────────────────────────────────────

KNOWLEDGE_CARD_SYSTEM = """You are a senior editorial intelligence editor at a Benelux M&A and dealflow intelligence platform.
Your task: distil a WHISPER_NOTE flagged as a pattern candidate into a KNOWLEDGE_CARD — a durable, reusable knowledge asset for Benelux deal professionals.

Audience (always apply):
- Founders aged 55+ considering succession or exit, family offices, PE partners, notaries, boutique M&A lawyers, corporate development professionals
- Geography: Benelux lower mid-market (BE/NL/LU + Northern FR), EV range €5–50M
- Goal: the card must be immediately useful in a real deal conversation — not a newsletter summary, not a market overview
- Tone: senior advisory — precise, non-generic, editorial authority

The card must answer four questions:
1. CORE INSIGHT     — What is the structural pattern, and why is it recurring in this market now? (2–3 sentences, present tense, pattern-level — not deal-specific)
2. DEAL IMPLICATION — How should a deal professional change their approach: in a founder meeting, a sector origination call, or a CIM? (2–3 sentences, actionable)
3. MISREAD RISK     — What is the most dangerous misinterpretation of this pattern that leads advisors to misjudge the deal or the founder? (1–2 sentences, direct)
4. BEST USE        — List 3–5 concrete use cases. Prefer: "founder conversation opener", "sector origination memo", "CIM angle", "valuation anchor", "mandate pitch", "newsletter lead"

Operating rules:
- If editorial_angle is provided: treat it as the PRIMARY framing anchor — the card must reflect this editorial lens
- If sector_focus is provided: ensure deal_implication and best_use are explicitly grounded in those sectors/geographies
- Synthesise upward from the whisper — never paraphrase the source note
- Write for broad dealflow audience — reusable across firms, not firm-specific
- English only, no jargon padding, no hedge words ("may", "could potentially")
- Keep core_insight under 180 words

Return ONLY valid JSON, no markdown fences:
{
  "title": "<Pattern name — sharp, memorable, max 12 words>",
  "core_insight": "<2–3 sentences>",
  "deal_implication": "<2–3 sentences>",
  "misread_risk": "<1–2 sentences>",
  "best_use": ["<use case 1>", "<use case 2>", "<use case 3>"]
}"""


def call_knowledge_card_extractor(whisper_note):
    """
    Call Claude Sonnet to extract a KNOWLEDGE_CARD from a pattern-candidate WHISPER_NOTE.
    Returns parsed dict with title, core_insight, deal_implication, misread_risk, best_use.
    Raises on failure — caller handles.
    """
    if not client:
        raise RuntimeError("No Anthropic client — set ANTHROPIC_API_KEY")

    sd = whisper_note.get('structured_data') or {}
    if isinstance(sd, str):
        try: sd = json.loads(sd)
        except: sd = {}

    # Build user prompt — include analyst framing if available
    editorial_angle = sd.get('editorial_angle', '').strip()
    sector_focus    = sd.get('sector_focus', '').strip()

    user_prompt = f"""Source WHISPER_NOTE to distil:

PATTERN ANCHOR
pattern_name:      {sd.get('pattern_name', '(not set)')}
pattern_rationale: {sd.get('pattern_rationale', '(not set)')}

SOURCE NOTE
title:   {whisper_note.get('title', '')}
country: {whisper_note.get('geo_country', '')}
summary: {whisper_note.get('summary_short', '')}

body excerpt:
{(whisper_note.get('body_md') or '')[:2000]}"""

    # Append editorial framing if present — this is the primary editorial anchor
    if editorial_angle or sector_focus:
        user_prompt += "\n\n--- EDITORIAL FRAMING ---"
        if editorial_angle:
            user_prompt += f"\neditorial_angle: {editorial_angle[:500]}"
        if sector_focus:
            user_prompt += f"\nsector_focus:    {sector_focus[:200]}"

    r = client.messages.create(
        model=MODEL_SONNET,
        max_tokens=800,
        system=KNOWLEDGE_CARD_SYSTEM,
        messages=[{'role': 'user', 'content': user_prompt}]
    )

    text = r.content[0].text.strip()
    text = text.replace('```json', '').replace('```', '').strip()
    j_start = text.find('{')
    j_end   = text.rfind('}') + 1
    if j_start >= 0 and j_end > j_start:
        text = text[j_start:j_end]

    parsed = json.loads(text)
    for key in ('title', 'core_insight', 'deal_implication', 'misread_risk', 'best_use'):
        if key not in parsed:
            raise ValueError(f"KnowledgeCardExtractor: missing key '{key}' in response")
    return parsed

def fetch_intel_items():
    """
    Fetch market_intelligence items that:
    - are not run_metrics (type != 'run')
    - have status = 'open'
    - have a meaningful headline
    - were created in the last 48h
    - don't already have a grapevine_note linked

    If TARGET_MI_ID is set: bypass ALL filters — fetch that exact item
    regardless of status, date, or existing notes.
    """

    # ── Direct bypass for --mi-id ─────────────────────────────────────────
    if TARGET_MI_ID:
        print(f"  → Direct fetch: {TARGET_MI_ID} (bypassing all filters)")
        # Debug: print full URL being called
        import urllib.parse
        params_debug = {'select': 'mi_id,scope,payload,period_start,generated_by,status,created_at', 'mi_id': f'eq.{TARGET_MI_ID}', 'limit': '1'}
        print(f"  → URL: {SUPABASE_URL}/rest/v1/market_intelligence?{urllib.parse.urlencode(params_debug)}")
        rows = sb_get('market_intelligence', {
            'select': 'mi_id,scope,payload,period_start,generated_by,status,created_at',
            'mi_id': f'eq.{TARGET_MI_ID}',
            'limit': '1',
        }) or []
        # Fallback: try without eq. prefix (some PostgREST versions)
        if not rows:
            rows = sb_get('market_intelligence', {
                'select': 'mi_id,scope,payload,period_start,generated_by,status,created_at',
                'mi_id': TARGET_MI_ID,
                'limit': '1',
            }) or []
        if not rows:
            print(f"  ✗ mi_id not found: {TARGET_MI_ID}")
            return []
        item = rows[0]
        payload = item.get('payload')
        if isinstance(payload, str):
            try: payload = json.loads(payload)
            except: payload = {}
        item['_payload'] = payload or {}
        item['_editorial_hints'] = None
        item['_replace_note_id'] = None

        # Check for existing note — extract hints + mark for replacement
        existing = sb_get('grapevine_notes', {
            'select': 'note_id,body_md,body,structured_data,title',
            'source_ref_id': f'eq.{TARGET_MI_ID}',
            'source_ref_type': 'eq.mi_id',
        }) or []
        for n in existing:
            sd = n.get('structured_data') or {}
            if isinstance(sd, str):
                try: sd = json.loads(sd)
                except: sd = {}
            body_text = n.get('body') or ''
            def extract_bullet(body, label):
                import re as _re
                m = _re.search(rf'·\s*{label}[:\.]+\s*(.+?)(?=\n·|$)', body, _re.IGNORECASE|_re.DOTALL)
                return m.group(1).strip()[:300] if m else ''
            hints = {
                'title':            n.get('title',''),
                'lens':             sd.get('lens','') or n.get('title',''),
                'why_it_matters':   sd.get('why_it_matters','')   or extract_bullet(body_text, 'Why it matters'),
                'trend_signal':     sd.get('trend_signal','')     or extract_bullet(body_text, 'Trend'),
                'parties_to_watch': sd.get('parties_to_watch','') or extract_bullet(body_text, 'Parties to watch'),
                'uncertainty':      sd.get('uncertainty','')      or extract_bullet(body_text, 'Uncertainty'),
                'editorial_body':   body_text[:1000] if body_text else '',
            }
            if any(v for v in hints.values() if v):
                item['_editorial_hints'] = hints
                print(f"  → Hints extracted from existing note: {[k for k,v in hints.items() if v]}")
            if not n.get('body_md'):
                item['_replace_note_id'] = n['note_id']
                print(f"  → Will replace minimal note: {n['note_id']}")

        print(f"  → Status was: {item.get('status')} — processing regardless")
        return [item]

    # ── Normal fetch (no TARGET_MI_ID) ────────────────────────────────────
    since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')

    # Fetch items in two groups:
    # 1. Analyst-touched (handled_curated, handled_quicksave) — process immediately
    # 2. Open items older than 4h — analyst had time to decide, auto-process as backlog
    grace_cutoff = (datetime.now(timezone.utc) - timedelta(hours=4)).strftime('%Y-%m-%dT%H:%M:%SZ')

    params_curated = {
        'select': 'mi_id,scope,payload,period_start,generated_by,status',
        'period_type': 'neq.run',
        'status': 'in.(handled_curated,handled_quicksave)',
        'created_at': f'gte.{since}',
        'limit': str(LIMIT * 3),
    }
    params_open = {
        'select': 'mi_id,scope,payload,period_start,generated_by,status',
        'period_type': 'neq.run',
        'status': 'eq.open',
        'created_at': f'gte.{since}',
        'created_at2': f'lte.{grace_cutoff}',  # only old enough open items
        'limit': str(LIMIT * 3),
    }

    # Note: PostgREST doesn't support two filters on same column via params dict
    # Use a single query with OR logic isn't available — use two fetches and merge
    rows_curated = sb_get('market_intelligence', params_curated) or []
    # For open items: filter by created_at <= grace_cutoff (older than 4h)
    params_open_fixed = {
        'select': 'mi_id,scope,payload,period_start,generated_by,status',
        'period_type': 'neq.run',
        'status': 'eq.open',
        'created_at': f'gte.{since}',
        'order': 'period_start.desc',
        'limit': str(LIMIT * 3),
    }
    rows_open_all = sb_get('market_intelligence', params_open_fixed) or []
    # Keep only open items older than 4h (analyst grace period)
    rows_open = [r for r in rows_open_all
                 if r.get('created_at','') <= grace_cutoff]
    rows = rows_curated + rows_open

    # Filter: must have a headline, not a run_metrics row
    items = []
    for row in rows:
        try:
            payload = row.get('payload')
            if isinstance(payload, str):
                payload = json.loads(payload)
            if not payload:
                continue
            # Skip run_metrics
            if payload.get('type') == 'run_metrics':
                continue
            headline = payload.get('headline', '')
            if not headline or len(headline.strip()) < 30:
                continue
            row['_payload'] = payload
            items.append(row)
        except Exception:
            continue

    # Check for existing notes (bookmark/quicksave = minimal; enriched = has body_md)
    if items and not TARGET_MI_ID:
        mi_ids = [r['mi_id'] for r in items]
        existing_notes = sb_get('grapevine_notes', {
            'select': 'note_id,source_ref_id,structured_data,title,body_md',
            'source_ref_type': 'eq.mi_id',
            'source_ref_id': f'in.({",".join(mi_ids)})',
        }) or []

        # Fully enriched (has body_md) → skip entirely
        already_enriched = {n['source_ref_id'] for n in existing_notes if n.get('body_md')}

        # Minimal notes (no body_md) → extract hints, mark for replacement after enrichment
        # NOTE: notes with body (editorial hints) but no body_md are also treated as minimal
        # because body_md = the actual Market Whisper article, body = editorial questions only
        minimal_by_mi = {}
        hints_by_mi   = {}
        for n in existing_notes:
            if not n.get('body_md'):
                minimal_by_mi[n['source_ref_id']] = n['note_id']
                sd = n.get('structured_data') or {}
                if isinstance(sd, str):
                    try: sd = json.loads(sd)
                    except: sd = {}
                # Also parse editorial hints from note.body (bullet format)
                body_text = n.get('body') or ''
                def extract_bullet(body, label):
                    import re as _re
                    m = _re.search(rf'·\s*{label}[:\.]+\s*(.+?)(?=\n·|$)', body, _re.IGNORECASE|_re.DOTALL)
                    return m.group(1).strip()[:300] if m else ''

                hints = {
                    'title':             n.get('title',''),
                    'lens':              sd.get('lens','') or n.get('title',''),
                    'why_it_matters':    sd.get('why_it_matters','')    or extract_bullet(body_text, 'Why it matters'),
                    'trend_signal':      sd.get('trend_signal','')      or extract_bullet(body_text, 'Trend'),
                    'parties_to_watch':  sd.get('parties_to_watch','')  or extract_bullet(body_text, 'Parties to watch'),
                    'uncertainty':       sd.get('uncertainty','')       or extract_bullet(body_text, 'Uncertainty'),
                    'editorial_body':    body_text[:1000] if body_text else '',
                }
                if any(v for v in hints.values() if v):
                    hints_by_mi[n['source_ref_id']] = hints

        for item in items:
            item['_editorial_hints']  = hints_by_mi.get(item['mi_id'])
            item['_replace_note_id']  = minimal_by_mi.get(item['mi_id'])

        # Process only non-enriched items (minimal notes will be replaced)
        items = [r for r in items if r['mi_id'] not in already_enriched]

    return items[:LIMIT]

# ── Build grapevine_notes row ─────────────────────────────────────────────

def build_grapevine_note(mi_row, parsed):
    payload = mi_row['_payload']
    country = (payload.get('country') or '').upper() or 'BE'
    lang    = payload.get('lang') or 'nl'
    url     = payload.get('url') or ''

    title = parsed['title'] or payload.get('headline', '')[:200]

    # ── Derive source_type from payload (spec v2.2 §3.2) ─────────────────────
    def _derive_source_type(p):
        sc  = (p.get('source_code') or '').upper()
        sig = (p.get('article_signal_type') or '').lower()
        src = (p.get('source') or '').lower()
        if sc == 'WHISPER':                             return 'HUMAN_WHISPER'
        if 'regulation' in sig or 'regulatory' in sig: return 'REGULATORY_RECORD'
        if 'legal' in sig or 'court' in sig:            return 'LEGAL_PROCEEDING'
        if sc in ('PITCHBOOK', 'CRUNCHBASE', 'DEALROOM', 'CAPIQ'):
                                                        return 'STRUCTURED_DB_FEED'
        if 'fusacq' in src or 'bbmatch' in src:        return 'MARKETPLACE_LISTING'
        if 'advisor' in sig or 'tombstone' in sig:     return 'ADVISOR_ANNOUNCEMENT'
        return 'PUBLIC_NEWS'   # safe default for RSS / media items

    source_type = _derive_source_type(payload)

    return {
        # ── Content ──────────────────────────────────────────────────────────
        'body':               parsed['body_md'],   # legacy NOT NULL column — keep
        'note_type':          'WHISPER_NOTE',      # spec v2.2: canonical enum value
        'content_kind':       'market_whisper',    # legacy descriptive field — keep
        'capture_origin':     'signal_enrich',     # spec v2.2 capture_origin enum
        'title':              title.replace('**', '').strip()[:300],
        'body_md':            parsed['body_md'],
        'summary_short':      parsed['summary_short'][:300] if parsed['summary_short'] else None,
        'summary_llm':        parsed['summary_short'][:300] if parsed['summary_short'] else None,

        # ── Classification (spec v2.2 §3 + §4) ───────────────────────────────
        'source_type':        source_type,
        'evidence_type':      'DOCUMENT',    # RSS/media items are structured documents
        'sensitivity_level':  'PUBLIC',      # pipeline output is public intel by default
        'visibility_scope':   'TEAM',        # spec v2.2: canonical enum (was 'internal')
        'intended_audience':  'internal',    # spec v2.2: default at creation
        'confidence':         parsed['confidence'],
        'time_sensitivity':   'SHORT_TERM',  # default for news items; analyst can override

        # ── Status & governance ───────────────────────────────────────────────
        'status':             'draft',
        'review_status':      'pending',     # spec v2.2: requires analyst Promote
        'link_status':        'unlinked',    # spec v2.2: Linker runs on Promote
        'is_ai_derived':      True,
        'is_deleted':         False,

        # ── Provenance ────────────────────────────────────────────────────────
        'source_ref_type':    'mi_id',
        'derived_from':       [{'type': 'market_intelligence', 'id': mi_row['mi_id']}],
        'source_ref_id':      mi_row['mi_id'],
        'created_by':         'intel_capture_v1',

        # ── Structured data ───────────────────────────────────────────────────
        'structured_data':    {
            **parsed['structured_data'],
            'source_language':      lang,        # original source language (nl/fr/en)
            'initial_signal_type':  payload.get('article_signal_type', ''),
            'initial_confidence':   payload.get('confidence', 0),
            'analyst_lens':         (mi_row.get('_editorial_hints') or {}).get('title', ''),
        },

        # ── Filters ───────────────────────────────────────────────────────────
        'geo_country':        country,
        'language_code':      'en',    # note is always English (MarketWhisperSnippet)
        'freshness_date':     mi_row.get('period_start'),

        # ── Legacy fields kept for backward-compat ────────────────────────────
        'gold_status':        'grapevine',
        'usable_for':         ['thought_leadership', 'sector_research'],
        'tags':               [country.lower(), payload.get('source', ''), lang],
        'note_version':       1,
        'is_current':         True,

        # ── Legacy classification fields (kept; may not exist on all schemas) ─
        'evidence_status':    'editorial',
        'layer_scope':        'grapevine',
        'confidentiality_tier': 'internal',
    }

# ── Newsworthiness scoring ──────────────────────────────────────────────────
SCORE_SYSTEM = """You are an editorial scoring engine for a Benelux M&A newsletter.
Score each Market Whisper note on NEWSWORTHINESS for a Benelux mid-market M&A audience.

Scoring criteria (weight):
1. Deal specificity (25%): Named parties > sector trends > pure opinion
2. Benelux relevance (25%): BE/LU > NL > FR > other
3. Mid-market fit (20%): EV €5M-€500M signals > mega deals > micro deals
4. Recency signal (15%): Concrete recent deal > historical reference > timeless trend
5. Source quality (15%): Named publication/press release > Google News aggregate

Return ONLY valid JSON, no markdown:
{"score": <integer 1-10>, "rationale": "<one sentence>", "newsletter_angle": "<one sentence framing for readers>"}"""

def score_note(title, summary, confidence, country, body_excerpt):
    """Score a single note for newsworthiness. Returns dict or None."""
    if not client:
        return None
    prompt = f"""Score this Benelux M&A newsletter note:
Title: {title}
Country: {country}
Confidence: {confidence}
Summary: {summary[:200]}
Body excerpt: {body_excerpt[:400]}"""
    try:
        r = client.messages.create(
            model=MODEL_HAIKU,   # scoring is simple classification — Haiku is faster + cheaper
            max_tokens=150,
            system=SCORE_SYSTEM,
            messages=[{'role': 'user', 'content': prompt}]
        )
        text = r.content[0].text.strip().replace('```json','').replace('```','').strip()
        # Find JSON object boundaries — guard against trailing content
        j_start = text.find('{')
        j_end   = text.rfind('}') + 1
        if j_start >= 0 and j_end > j_start:
            text = text[j_start:j_end]
        parsed = json.loads(text)
        return {
            'newsworthiness_score':     max(1, min(10, int(parsed.get('score', 5)))),
            'newsworthiness_rationale': str(parsed.get('rationale', ''))[:600],
            'newsletter_angle':         str(parsed.get('newsletter_angle', ''))[:600],
        }
    except Exception as e:
        print(f"    ⚠ Score error: {e}")
        return None


# ── Main ──────────────────────────────────────────────────────────────────

def run():
    print("=" * 60)
    print(f"INTEL CAPTURE v1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Mode: {'DRY RUN — no DB writes' if DRY_RUN else 'LIVE'} | Limit: {LIMIT}")
    if TARGET_MI_ID:
        print(f"Target: {TARGET_MI_ID}")
    print("=" * 60)

    if not client:
        print("✗ No ANTHROPIC_API_KEY — cannot run")
        return
    if not DRY_RUN and not SUPABASE_KEY:
        print("✗ No SUPABASE_SERVICE_KEY — use --dry-run or set the key")
        return

    # 1. Fetch
    print(f"\n[1] Fetching unprocessed intel items…")
    if DRY_RUN and not SUPABASE_KEY:
        print("  ⚠ No Supabase key — generating demo items for dry run")
        items = [_demo_item()]
    else:
        items = fetch_intel_items()

    if not items:
        print("  Nothing to process — no unprocessed intel items in last 7 days")
        return
    print(f"  {len(items)} item(s) to enrich")

    # 2. Enrich
    print(f"\n[2] Enriching with MarketWhisperSnippet…\n")
    notes_written = 0
    notes_failed  = 0

    for i, item in enumerate(items, 1):
        payload  = item['_payload']
        headline = payload.get('headline', '')
        url      = payload.get('url', '')
        country  = (payload.get('country') or 'BE').upper()
        lang     = payload.get('lang', 'nl')

        print(f"  [{i}/{len(items)}] {headline[:80]}…")
        print(f"          Country: {country} | Lang: {lang} | Source: {url[:60]}")

        # Rate limit guard — web_search responses are token-heavy (~2000 tokens each)
        # 20s pause keeps us well within 30k tokens/min on Sonnet
        if i > 1:
            import time; time.sleep(20)

        try:
            # LLM call with web search
            editorial_hints = item.get('_editorial_hints')
            is_curated = item.get('status') == 'handled_curated'

            # FIX: use full body text if available — not just the headline
            # payload.body contains the full whisper text (email, article, etc.)
            body_text = payload.get('body') or payload.get('text') or ''
            # Combine headline + body for richer context
            full_input = headline
            if body_text and len(body_text) > len(headline) + 20:
                full_input = f"{headline}\n\n{body_text[:2000]}"

            if editorial_hints:
                print(f"          → Editorial hints: {list(k for k,v in editorial_hints.items() if v)}")
            if body_text:
                print(f"          → Body text: {len(body_text)} chars (passed as input_text)")

            raw = call_market_whisper(editorial_hints=editorial_hints,
                jurisdiction = country,
                input_text   = full_input,
                input_link   = url,
            )

            # Parse output
            parsed = parse_whisper_output(raw)

            print(f"          → Title:      {parsed['title'][:70]}")
            print(f"          → Confidence: {parsed['confidence']}")
            print(f"          → Lead:       {parsed['summary_short'][:80]}…")

            # Score the note (same API call budget — fast, 150 tokens)
            score_data = score_note(
                title    = parsed['title'],
                summary  = parsed['summary_short'] or '',
                confidence = parsed['confidence'],
                country  = item['_payload'].get('country',''),
                body_excerpt = parsed['body_md'][:400] if parsed['body_md'] else ''
            )
            if score_data:
                parsed['structured_data'].update(score_data)
                print(f"          → Score:       {score_data['newsworthiness_score']}/10  {score_data['newsletter_angle'][:60]}")

                # ── Auto-flag pattern candidates ──────────────────────────────
                # Score ≥ 8 AND newsletter_angle present → structural pattern signal
                # Only flag if not already set (preserve manual overrides)
                score_val = score_data.get('newsworthiness_score', 0)
                already_flagged = parsed['structured_data'].get('pattern_candidate', False)
                if score_val >= 8 and not already_flagged:
                    parsed['structured_data']['pattern_candidate']  = True
                    parsed['structured_data']['pattern_name']       = parsed['title'][:120]
                    parsed['structured_data']['pattern_rationale']  = score_data.get('newsletter_angle', '')[:400]
                    print(f"          → Pattern:     ✓ Auto-flagged (score {score_val}/10)")
                elif score_val >= 6 and not already_flagged:
                    # Score 6-7: flag as candidate but mark for analyst review
                    parsed['structured_data']['pattern_candidate']  = False  # explicit false — analyst decides
                    print(f"          → Pattern:     — Score {score_val}/10 (analyst can promote manually)")
            else:
                print(f"          ! Score failed — note created without score (score_grapevine.py can backfill)")

            if DRY_RUN:
                print(f"\n{'─'*60}")
                print("DRY RUN — Full output:")
                print(textwrap.indent(raw[:1200], '  '))
                if len(raw) > 1200:
                    print(f"  … ({len(raw) - 1200} more chars)")
                print(f"{'─'*60}\n")
            else:
                note = build_grapevine_note(item, parsed)
                sb_post('grapevine_notes', note)

                # Archive minimal note if it existed (bookmark/quicksave → replaced by enriched)
                replace_id = item.get('_replace_note_id')
                if replace_id:
                    try:
                        sb_patch('grapevine_notes',
                                 {'note_id': f'eq.{replace_id}'},
                                 {'status': 'archived'})
                        print(f"          + Minimal note archived (replaced by enriched version)")
                    except Exception as de:
                        print(f"          ! Could not archive minimal note: {de}")

                # Mark intel item as handled
                ok = sb_patch('market_intelligence',
                              {'mi_id': f'eq.{item["mi_id"]}'},
                              {'status': 'handled_intel_capture'})
                print(f"          + Grapevine note created (draft) · mi patched: {ok}")
                notes_written += 1

        except Exception as e:
            notes_failed += 1
            print(f"          ✗ Error: {e}")
            continue

    # 3. Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"  Items processed : {len(items)}")
    if DRY_RUN:
        print(f"  Mode            : DRY RUN — no writes made")
    else:
        print(f"  Notes created   : {notes_written}")
        print(f"  Errors          : {notes_failed}")
        print(f"  → Notes land as status='draft' in grapevine_notes")
        print(f"  → Review in Focus Terminal Grapevine tab (C1, coming soon)")
    print(f"{'='*60}")


# ── --to-card entry point ──────────────────────────────────────────────────

def run_to_card(note_id):
    """
    Fetch a WHISPER_NOTE with structured_data.pattern_candidate=true,
    call KnowledgeCardExtractor (Sonnet), write a new KNOWLEDGE_CARD draft.
    Source WHISPER_NOTE is NOT modified.
    """
    print("=" * 60)
    print(f"INTEL CAPTURE — TO-CARD v1.1 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Source note_id : {note_id}")
    print(f"Mode           : {'DRY RUN — no DB writes' if DRY_RUN else 'LIVE'}")
    print("=" * 60)

    if not client:
        print("✗ No ANTHROPIC_API_KEY — cannot run")
        return
    if not DRY_RUN and not SUPABASE_KEY:
        print("✗ No SUPABASE_SERVICE_KEY — use --dry-run or set the key")
        return

    # 1. Fetch source WHISPER_NOTE
    print(f"\n[1] Fetching source note…")
    rows = sb_get('grapevine_notes', {
        'select': 'note_id,note_type,title,summary_short,body_md,structured_data,geo_country,sector_code,language_code',
        'note_id':    f'eq.{note_id}',
        'is_deleted': 'eq.false',
        'limit':      '1',
    }) or []

    if not rows:
        print(f"✗ Note not found or is_deleted=true: {note_id}")
        return

    source = rows[0]

    # Guard: must be WHISPER_NOTE
    if source.get('note_type') != 'WHISPER_NOTE':
        print(f"✗ note_type is '{source.get('note_type')}' — --to-card requires WHISPER_NOTE")
        return

    # Guard: must be pattern_candidate
    sd = source.get('structured_data') or {}
    if isinstance(sd, str):
        try: sd = json.loads(sd)
        except: sd = {}

    if not sd.get('pattern_candidate'):
        print(f"✗ structured_data.pattern_candidate is not true on this note")
        print(f"  Set it via the Pattern Candidate toggle in the UI first.")
        return

    print(f"  ✓ Source: '{source.get('title', '')[:70]}'")
    print(f"  ✓ pattern_name:      {sd.get('pattern_name', '(not set)')}")
    print(f"  ✓ pattern_rationale: {str(sd.get('pattern_rationale', '(not set)'))[:80]}")

    # 2. Call KnowledgeCardExtractor
    print(f"\n[2] Calling KnowledgeCardExtractor (Sonnet)…")
    try:
        extracted = call_knowledge_card_extractor(source)
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        return

    print(f"  ✓ Title:            {extracted['title'][:70]}")
    print(f"  ✓ Core insight:     {extracted['core_insight'][:80]}…")
    print(f"  ✓ Deal implication: {extracted['deal_implication'][:80]}…")
    print(f"  ✓ Misread risk:     {extracted['misread_risk'][:80]}…")
    print(f"  ✓ Best use:         {extracted['best_use']}")

    if DRY_RUN:
        print(f"\n{'─'*60}")
        print("DRY RUN — Full extracted card:")
        print(json.dumps(extracted, indent=2, ensure_ascii=False))
        print(f"{'─'*60}")
        return

    # 3. Build KNOWLEDGE_CARD record
    card = {
        # ── Content ──────────────────────────────────────────────────────────
        'body':           extracted['core_insight'],   # legacy NOT NULL column
        'body_md':        extracted['core_insight'],
        'note_type':      'KNOWLEDGE_CARD',            # spec v2.2 canonical
        'capture_origin': 'whisper_report',            # spec v2.2 canonical
        'title':          extracted['title'][:300],
        'summary_short':  extracted['core_insight'][:300],
        'summary_llm':    extracted['core_insight'][:300],
        'content_kind':   'knowledge_card',

        # ── Classification ────────────────────────────────────────────────────
        'sensitivity_level':  'PUBLIC',
        'visibility_scope':   'TEAM',
        'intended_audience':  'internal',
        'evidence_type':      'COMPOSITE',
        'source_type':        'INTERNAL_MEMO',         # synthesised output → INTERNAL_MEMO
        'confidence':         'medium',
        'time_sensitivity':   'STRUCTURAL',            # knowledge cards are durable

        # ── Status & governance ───────────────────────────────────────────────
        'status':         'draft',
        'review_status':  'pending',
        'link_status':    'unlinked',
        'is_ai_derived':  True,
        'is_deleted':     False,

        # ── Provenance ────────────────────────────────────────────────────────
        'source_ref_type': 'note_id',
        'source_ref_id':   note_id,
        'derived_from':    [{'type': 'grapevine_note', 'id': note_id, 'note_type': 'WHISPER_NOTE'}],
        'created_by':      'intel_capture_to_card_v1',

        # ── Structured data (KB tab fields) ───────────────────────────────────
        'structured_data': {
            'core_insight':             extracted['core_insight'],
            'deal_implication':         extracted['deal_implication'],
            'misread_risk':             extracted['misread_risk'],
            'best_use':                 extracted['best_use'],
            'source_pattern_name':      sd.get('pattern_name', ''),
            'source_pattern_rationale': sd.get('pattern_rationale', ''),
            'source_whisper_note_id':   note_id,
        },

        # ── Filters ───────────────────────────────────────────────────────────
        'geo_country':    source.get('geo_country', 'BE'),
        'sector_code':    source.get('sector_code'),
        'language_code':  'en',

        # ── Legacy fields ─────────────────────────────────────────────────────
        'note_version': 1,
        'is_current':   True,
        'gold_status':  'grapevine',
        'usable_for':   ['thought_leadership', 'sector_research'],
    }

    # 4. Write to DB
    print(f"\n[3] Writing KNOWLEDGE_CARD to grapevine_notes…")
    try:
        result = sb_post('grapevine_notes', card)
        if result:
            new_id = result[0].get('note_id', '?') if isinstance(result, list) else '(created)'
            print(f"  ✓ KNOWLEDGE_CARD created : {new_id}")
            print(f"  ✓ status=draft | capture_origin=whisper_report")

            # Clear pattern_candidate on source note — card has been extracted
            cleared_sd = {**sd, 'pattern_candidate': False}
            ok = sb_patch('grapevine_notes',
                          {'note_id': f'eq.{note_id}'},
                          {'structured_data': cleared_sd})
            print(f"  ✓ Source pattern_candidate cleared : {ok}")
        else:
            print(f"  ⚠ sb_post returned None — possible duplicate (idempotent, safe to ignore)")
    except Exception as e:
        print(f"  ✗ DB write failed: {e}")
        return

    print(f"\n{'='*60}")
    print(f"TO-CARD COMPLETE")
    print(f"  → Review the new KNOWLEDGE_CARD in Grapevine UI → KB tab")
    print(f"  → Promote when ready to activate for distribution")
    print(f"{'='*60}")


def _demo_item():
    """Demo item for dry-run without DB access."""
    return {
        'mi_id': 'demo-00000000-0000-0000-0000-000000000001',
        'scope': 'region:BE',
        'period_start': datetime.now().strftime('%Y-%m-%d'),
        'status': 'open',
        'generated_by': 'dealflow_pipeline_demo',
        '_payload': {
            'headline': 'Belgisch familiebedrijf in bouwsector zoekt opvolger na 40 jaar - De Tijd',
            'url': 'https://www.tijd.be/demo',
            'country': 'BE',
            'lang': 'nl',
            'source': 'dealflow_pipeline',
            'obs_date': datetime.now().strftime('%Y-%m-%d'),
        }
    }


if __name__ == '__main__':
    if TARGET_CARD_NOTE_ID:
        run_to_card(TARGET_CARD_NOTE_ID)
    else:
        run()
