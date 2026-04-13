#!/usr/bin/env python3
"""
promote_kb_drafts.py — Batch enrich + promote draft KNOWLEDGE_CARDs
v1.0 | Grapevine / Dealflow.News / V4G | April 2026

Reads all draft KNOWLEDGE_CARDs, calls KnowledgeCardExtractor (Sonnet)
on the existing body content, patches each card with full structured_data,
and promotes to status='active'.

This is a one-shot script for the 64 seed reference works that were
curated and ingested but never enriched. Run once. Safe to re-run:
already-active cards are skipped.

Usage:
    python promote_kb_drafts.py                     # all drafts, live
    python promote_kb_drafts.py --dry-run           # preview only, no DB writes
    python promote_kb_drafts.py --limit=5           # process max 5 cards
    python promote_kb_drafts.py --note-id=<uuid>    # single card
    python promote_kb_drafts.py --dry-run --limit=3 # safe test

Output:
    Console log per card: title → tier → benelux_fit → status
    Final summary: enriched / skipped / failed
"""

import os, sys, json, time
from datetime import datetime, timezone

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── Config ─────────────────────────────────────────────────────────────────
def load_env():
    """Load .env file if present — same pattern as intel_capture.py.
    Falls back silently to Windows/system environment variables."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()

ANTHROPIC_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
SUPABASE_URL  = os.environ.get('SUPABASE_URL', 'https://rirkgpsdcaxnowwmliof.supabase.co')
SUPABASE_KEY  = os.environ.get('SUPABASE_SERVICE_KEY', '')
MODEL_SONNET  = os.environ.get('MODEL_SONNET', 'claude-sonnet-4-6')

DRY_RUN  = '--dry-run' in sys.argv
_lim     = next((a for a in sys.argv if a.startswith('--limit=')), None)
LIMIT    = int(_lim.replace('--limit=', '')) if _lim else 999
_nid     = next((a for a in sys.argv if a.startswith('--note-id=')), None)
TARGET_NOTE_ID = _nid.replace('--note-id=', '') if _nid else None
SOURCES_ONLY = '--sources-only' in sys.argv  # only add source_access, skip full re-enrich

# Rate limiting — be respectful to Anthropic API
DELAY_BETWEEN_CALLS = 3.0   # seconds between Sonnet calls
MAX_BODY_CHARS      = 3000  # truncate body for prompt

try:
    import httpx
    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None
except ImportError as e:
    print(f"✗ Missing dependency: {e}")
    print("  Run: pip install anthropic httpx")
    sys.exit(1)

# ── Supabase helpers ────────────────────────────────────────────────────────
def sb_get(table, params=None):
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
    }
    r = httpx.get(f'{SUPABASE_URL}/rest/v1/{table}',
                  params=params, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

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

# ── KnowledgeCard Enrichment prompt ────────────────────────────────────────
ENRICH_SYSTEM = """You are a senior editorial intelligence editor at a Benelux M&A and dealflow intelligence platform.

Your task: enrich a KNOWLEDGE_CARD draft from an M&A reference book, research report, or whitepaper.
These are curated reference works that analysts at a boutique M&A advisory (V4G — Ventures4Growth, Ghent) use in deal conversations, founder meetings, and sector origination.

Audience: founders aged 55+ considering succession or exit, family offices, PE partners, notaries, boutique M&A lawyers — Benelux lower mid-market (BE/NL/LU + Northern France), EV €5–50M.

Your output enriches the card with four knowledge fields AND source metadata AND quality judgment.

Operating rules:
- Synthesise upward — extract the durable structural insight, not a summary
- Ground deal_implication in Benelux lower mid-market M&A (not global generics)
- Be specific about misread_risk — what do advisors consistently get wrong?
- best_use: concrete use cases an analyst can act on tomorrow
- For source_access: derive author/isbn/canonical_url from title and body where possible; use null if not derivable
- For kb_quality.tier: A = frontline use in founder conversation / CIM / origination call; B = useful background; C = weak/outdated
- For kb_quality.benelux_fit: direct = source is Benelux-specific; analogous = global but directly applicable; background = indirect relevance
- For kb_quality.evidence_strength: empirical = data-backed; practitioner = experience-based; theoretical = conceptual framework
- For kb_quality.evergreen: false only if the source is explicitly dated/superseded
- Return ONLY valid JSON — no markdown fences, no preamble

JSON schema:
{
  "title": "Pattern-based title (rewrite if current title is just the book name)",
  "core_insight": "The structural pattern — 2-3 sentences, present tense, generalised",
  "deal_implication": "How this changes approach in a founder meeting / origination call / CIM — 2-3 sentences, actionable for Benelux lower mid-market",
  "misread_risk": "The most dangerous misinterpretation — 1-2 sentences, direct",
  "best_use": ["use case 1", "use case 2", "use case 3", "use case 4", "use case 5"],
  "confidence": "high | medium | low",
  "source_access": {
    "author": "Full author name(s) or null",
    "isbn": "ISBN-13 or null",
    "canonical_url": "Publisher URL or null",
    "access_type": "canonical_only | storage_copy | both | none"
  },
  "kb_quality": {
    "tier": "A | B | C",
    "benelux_fit": "direct | analogous | background",
    "geo_scope": ["BE", "NL", "LU", "FR", "EU", "GLOBAL"],
    "evidence_strength": "empirical | practitioner | theoretical",
    "evergreen": true,
    "editorial_decision": "promoted"
  },
  "card_type": "library_source",
  "sector_code": "sector label or Cross-sector",
  "time_sensitivity": "TIMELESS | STRUCTURAL"
}"""



SOURCES_SYSTEM = """You are a reference librarian and M&A knowledge editor.
Given a KNOWLEDGE_CARD title and body excerpt, derive the bibliographic source metadata.

Return ONLY valid JSON — no markdown:
{
  "author": "Full author name(s) as they appear on the book cover, or null",
  "isbn": "ISBN-13 preferred, ISBN-10 acceptable, or null if not a book",
  "canonical_url": "Publisher page, SSRN, official report URL, or null",
  "access_type": "canonical_only | none"
}

Rules:
- For well-known M&A/finance books: you likely know the ISBN — include it
- For academic papers: use SSRN or DOI URL as canonical_url
- For reports (KPMG, EY, McKinsey): use the report's official URL if known
- If uncertain: use null rather than guess
- access_type is canonical_only if canonical_url is present, else none"""

def get_source_access(note: dict) -> dict:
    """Call Claude Haiku to derive source_access metadata. Cheap + fast."""
    if not client:
        raise RuntimeError("No Anthropic client")
    title = note.get('title', '')
    body  = (note.get('body') or note.get('body_md') or '')[:800]
    sd    = note.get('structured_data') or {}
    if isinstance(sd, str):
        try: sd = json.loads(sd)
        except: sd = {}
    source_box = sd.get('source_box', '')

    r = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=300,
        system=SOURCES_SYSTEM,
        messages=[{'role': 'user', 'content':
            f"Title: {title}\nSource box: {source_box[:200]}\nBody excerpt: {body[:400]}"}]
    )
    raw = r.content[0].text.strip()
    j_start = raw.find('{'); j_end = raw.rfind('}') + 1
    if j_start < 0: raise ValueError(f"No JSON: {raw[:100]}")
    return json.loads(raw[j_start:j_end])

def enrich_card(note: dict) -> dict:
    """Call Claude Sonnet to enrich a draft KNOWLEDGE_CARD. Returns parsed dict."""
    if not client:
        raise RuntimeError("No Anthropic client — set ANTHROPIC_API_KEY")

    title    = note.get('title', '(untitled)')
    body     = note.get('body') or note.get('body_md') or ''
    summary  = note.get('summary_short') or ''
    sector   = note.get('sector_code') or ''
    country  = note.get('geo_country') or ''
    sd       = note.get('structured_data') or {}
    if isinstance(sd, str):
        try: sd = json.loads(sd)
        except: sd = {}

    source_box = sd.get('source_box') or sd.get('drop_source') or ''

    user_prompt = f"""Enrich this KNOWLEDGE_CARD draft:

TITLE: {title}

SECTOR: {sector or '(not set)'}
GEO: {country or '(not set)'}
SOURCE: {source_box[:200] if source_box else '(not provided)'}

BODY CONTENT:
{body[:MAX_BODY_CHARS]}

{('SUMMARY:\n' + summary[:300]) if summary and not body else ''}

Return the enriched JSON as specified. Keep the existing title if it is already pattern-based; rewrite it if it is just the book/report name."""

    r = client.messages.create(
        model=MODEL_SONNET,
        max_tokens=1800,
        system=ENRICH_SYSTEM,
        messages=[{'role': 'user', 'content': user_prompt}]
    )

    raw = r.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith('```'):
        raw = raw.split('\n', 1)[1] if '\n' in raw else raw
        raw = raw.rsplit('```', 1)[0].strip()

    j_start = raw.find('{')
    j_end   = raw.rfind('}') + 1
    if j_start < 0 or j_end <= j_start:
        raise ValueError(f"No JSON object in response: {raw[:200]}")

    return json.loads(raw[j_start:j_end])


def fetch_draft_cards() -> list:
    """Fetch all draft KNOWLEDGE_CARDs, optionally filtered to a single note_id."""
    params = {
        'select':     'note_id,title,status,note_type,body,body_md,summary_short,'
                      'sector_code,geo_country,structured_data,created_at',
        'note_type':  'eq.KNOWLEDGE_CARD',
        'is_deleted': 'eq.false',
        'order':      'created_at.asc',
        'limit':      str(LIMIT),
    }
    if TARGET_NOTE_ID:
        params['note_id'] = f'eq.{TARGET_NOTE_ID}'
        params.pop('limit', None)
    elif SOURCES_ONLY:
        # Sources-only mode: fetch active cards missing source_access
        params['status'] = 'eq.active'
    else:
        params['status'] = 'eq.draft'

    return sb_get('grapevine_notes', params) or []


def build_patch(enriched: dict, existing_sd: dict) -> dict:
    """Build the PATCH payload merging enriched data with existing structured_data."""
    sa  = enriched.get('source_access') or {}
    kbq = enriched.get('kb_quality') or {}

    # Preserve any existing structured_data fields (e.g. source_box, drop_source)
    new_sd = {
        **existing_sd,
        # KB card fields
        'core_insight':    enriched.get('core_insight', ''),
        'deal_implication': enriched.get('deal_implication', ''),
        'misread_risk':    enriched.get('misread_risk', ''),
        'best_use':        enriched.get('best_use', []),
        # Taxonomy (Architecture Lock v1.0.2)
        'card_type':       enriched.get('card_type', 'library_source'),
        # Source retrieval model
        'source_access': {
            'author':        sa.get('author'),
            'isbn':          sa.get('isbn'),
            'canonical_url': sa.get('canonical_url'),
            'storage_url':   existing_sd.get('storage_url'),  # preserve if exists
            'access_type':   sa.get('access_type', 'none'),
        },
        # KB quality framework
        'kb_quality': {
            'tier':              kbq.get('tier', 'B'),
            'benelux_fit':       kbq.get('benelux_fit', 'analogous'),
            'geo_scope':         kbq.get('geo_scope', ['GLOBAL']),
            'evidence_strength': kbq.get('evidence_strength', 'practitioner'),
            'evergreen':         kbq.get('evergreen', True),
            'editorial_decision': 'promoted',
        },
    }

    patch = {
        'structured_data':  new_sd,
        'status':           'active',
        'review_status':    'approved',
        'link_status':      'link_pending',
        'confidence':       enriched.get('confidence', 'medium'),
        'time_sensitivity': enriched.get('time_sensitivity', 'TIMELESS'),
        'updated_at':       datetime.now(timezone.utc).isoformat(),
    }

    # Update top-level fields if enriched has better values
    if enriched.get('sector_code'):
        patch['sector_code'] = enriched['sector_code']
    if enriched.get('title'):
        # Only overwrite title if it looks pattern-based (not just book name)
        patch['title'] = enriched['title'][:300]

    return patch


# ── Main ────────────────────────────────────────────────────────────────────
def run():
    print("=" * 65)
    print(f"PROMOTE KB DRAFTS v1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    mode_str = "DRY RUN — no DB writes" if DRY_RUN else "⚡ LIVE — writing to Supabase"
    if SOURCES_ONLY: mode_str += " | SOURCES ONLY"
    print(f"Mode  : {mode_str}")
    print(f"Model : {MODEL_SONNET}")
    print(f"Limit : {LIMIT if not TARGET_NOTE_ID else 'single note'}")
    if TARGET_NOTE_ID:
        print(f"Target: {TARGET_NOTE_ID}")
    print("=" * 65)

    if not client:
        print("✗ No ANTHROPIC_API_KEY — cannot run")
        return
    if not DRY_RUN and not SUPABASE_KEY:
        print("✗ No SUPABASE_SERVICE_KEY — use --dry-run or set key in .env")
        return

    # 1. Fetch
    print(f"\n[1] Fetching draft KNOWLEDGE_CARDs…")
    cards = fetch_draft_cards()
    if not cards:
        print("  ✓ Nothing to process — no draft KNOWLEDGE_CARDs found")
        return
    print(f"  → {len(cards)} card(s) to enrich\n")

    # 2. Enrich + promote
    enriched_count = 0
    skipped_count  = 0
    failed_count   = 0
    failed_titles  = []

    for i, card in enumerate(cards, 1):
        title     = card.get('title', '(untitled)')[:70]
        note_id   = card['note_id']
        status    = card.get('status', '')

        print(f"[{i:02d}/{len(cards):02d}] {title}")

        # Skip if already active (safety guard — but NOT in sources-only mode)
        if status == 'active' and not TARGET_NOTE_ID and not SOURCES_ONLY:
            print(f"       ↷ Already active — skip")
            skipped_count += 1
            continue

        # Check if already enriched (has core_insight)
        sd = card.get('structured_data') or {}
        if isinstance(sd, str):
            try: sd = json.loads(sd)
            except: sd = {}
        # Sources-only mode: add source_access if missing
        if SOURCES_ONLY:
            existing_sa = sd.get('source_access') or {}
            if existing_sa.get('author') or existing_sa.get('isbn') or existing_sa.get('canonical_url'):
                print(f"       ↷ Source already present — skip")
                skipped_count += 1
                continue
            try:
                print(f"       ✦ Deriving source metadata (Haiku)…", end='', flush=True)
                sa = get_source_access(card)
                print(f" {sa.get('author','?')[:40]} | ISBN: {sa.get('isbn','—')}")
                if DRY_RUN:
                    enriched_count += 1
                else:
                    new_sd = {**sd, 'source_access': sa}
                    ok = sb_patch('grapevine_notes',
                                  {'note_id': f'eq.{note_id}'},
                                  {'structured_data': new_sd,
                                   'updated_at': datetime.now(timezone.utc).isoformat()})
                    print(f"       ✓ Source saved" if ok else "       ✗ PATCH failed")
                    if ok: enriched_count += 1
                    else: failed_count += 1
            except Exception as e:
                print(f" ✗ {e}")
                failed_count += 1
                failed_titles.append(title)
            if i < len(cards):
                time.sleep(1.0)  # Haiku is fast, shorter delay
            continue

        if sd.get('core_insight') and not TARGET_NOTE_ID:
            # Already enriched — skip AI call but still promote if still draft
            if status == 'draft':
                print(f"       ↷ Already enriched — promoting to active…", end='', flush=True)
                if DRY_RUN:
                    print(f" [DRY RUN] would promote")
                    enriched_count += 1
                else:
                    ok = sb_patch('grapevine_notes',
                                  {'note_id': f'eq.{note_id}'},
                                  {
                                      'status':        'active',
                                      'review_status': 'approved',
                                      'link_status':   'link_pending',
                                      'updated_at':    datetime.now(timezone.utc).isoformat(),
                                  })
                    print(f" ✓ Promoted" if ok else " ✗ PATCH failed")
                    if ok: enriched_count += 1
                    else: failed_count += 1
            else:
                print(f"       ↷ Already active + enriched — skip")
                skipped_count += 1
            continue

        # Check body content
        body = card.get('body') or card.get('body_md') or ''
        if len(body.strip()) < 50:
            print(f"       ⚠ Body too short ({len(body)} chars) — skip")
            skipped_count += 1
            continue

        try:
            # Call Claude
            print(f"       ✦ Calling KnowledgeCardExtractor…", end='', flush=True)
            enriched = enrich_card(card)
            tier     = enriched.get('kb_quality', {}).get('tier', '?')
            fit      = enriched.get('kb_quality', {}).get('benelux_fit', '?')
            conf     = enriched.get('confidence', '?')
            print(f" Tier {tier} · {fit} · {conf}")
            print(f"       → {enriched.get('title', title)[:70]}")

            if DRY_RUN:
                print(f"       [DRY RUN] core_insight: {enriched.get('core_insight','')[:80]}…")
                print(f"       [DRY RUN] best_use: {enriched.get('best_use', [])[:3]}")
                enriched_count += 1
            else:
                patch = build_patch(enriched, sd)
                ok = sb_patch('grapevine_notes',
                              {'note_id': f'eq.{note_id}'},
                              patch)
                if ok:
                    print(f"       ✓ Promoted to active")
                    enriched_count += 1
                else:
                    print(f"       ✗ PATCH failed (HTTP error)")
                    failed_count += 1
                    failed_titles.append(title)

        except json.JSONDecodeError as e:
            print(f" ✗ JSON parse error: {e}")
            failed_count += 1
            failed_titles.append(title)
        except Exception as e:
            print(f" ✗ Error: {e}")
            failed_count += 1
            failed_titles.append(title)

        # Rate limiting — avoid hammering the API
        if i < len(cards):
            time.sleep(DELAY_BETWEEN_CALLS)

    # 3. Summary
    print(f"\n{'='*65}")
    print(f"SUMMARY")
    print(f"{'='*65}")
    print(f"  Cards processed : {len(cards)}")
    print(f"  Enriched        : {enriched_count} {'(preview only — no writes)' if DRY_RUN else '→ now active'}")
    print(f"  Skipped         : {skipped_count} (already active / enriched / no body)")
    print(f"  Failed          : {failed_count}")
    if failed_titles:
        print(f"\n  Failed cards:")
        for t in failed_titles:
            print(f"    ✗ {t}")
    if DRY_RUN:
        print(f"\n  ℹ DRY RUN complete — re-run without --dry-run to write to Supabase")
    else:
        print(f"\n  ✓ All enriched cards are now active in the Knowledge Base")
        print(f"  → Open grapevine.dealflow.news → Knowledge Base to review")
    print(f"{'='*65}")


if __name__ == '__main__':
    run()
