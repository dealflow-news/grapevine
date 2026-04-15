#!/usr/bin/env python3
"""
score_grapevine.py — Batch newsworthiness scoring voor bestaande grapevine_notes
v1.1 | 2026-04-10

Scoort bestaande notes op nieuwswaarde (0-10) en schrijft score naar
structured_data.newsworthiness_score + newsworthiness_rationale.

Usage:
    python score_grapevine.py --dry-run    # print scores, geen DB writes
    python score_grapevine.py              # live run, update alle unscored notes
    python score_grapevine.py --all        # herscoor ook al gescoorde notes
"""

import os, sys, json, time
from datetime import datetime
from anthropic import Anthropic
import httpx

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

ANTHROPIC_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
SUPABASE_URL  = os.environ.get('SUPABASE_URL', 'https://rirkgpsdcaxnowwmliof.supabase.co')
SUPABASE_KEY  = os.environ.get('SUPABASE_SERVICE_KEY', '')
MODEL         = os.environ.get('MODEL_SONNET', 'claude-sonnet-4-6')

DRY_RUN  = '--dry-run' in sys.argv
RESCORE  = '--all' in sys.argv

client = Anthropic(api_key=ANTHROPIC_KEY) if ANTHROPIC_KEY else None

# ── Supabase helpers ────────────────────────────────────────────────────────
def sb_get(table, params=None):
    headers = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
    r = httpx.get(f'{SUPABASE_URL}/rest/v1/{table}', params=params, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def sb_patch(table, filter_params, data):
    headers = {
        'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json', 'Prefer': 'return=minimal',
    }
    r = httpx.patch(f'{SUPABASE_URL}/rest/v1/{table}',
                    params=filter_params, json=data, headers=headers, timeout=30)
    return r.status_code in (200, 204)

# ── Scoring prompt ──────────────────────────────────────────────────────────
SCORE_SYSTEM = """You are an editorial scoring engine for a Benelux M&A newsletter.
Score each Market Whisper note on NEWSWORTHINESS for a Benelux mid-market M&A audience.

Scoring criteria (weight):
1. Deal specificity (25%): Named parties > sector trends > pure opinion
2. Regional relevance (25%): BE/NL/LU/FR(Nord) = DIRECT (top score) > other EU > global
3. Mid-market fit (20%): EV €5M–€500M range signals > mega deals > micro deals
4. Recency signal (15%): Concrete recent deal > historical reference > timeless trend
5. Source quality (15%): Named publication/press release > Google News aggregate

Return ONLY valid JSON, no markdown:
{
  "score": <integer 1-10>,
  "rationale": "<one sentence explaining the score>",
  "newsletter_angle": "<one sentence: how to frame this for readers>"
}"""

def score_note(note):
    """Score a single note. Returns (score, rationale, angle) or None."""
    if not client:
        return None

    # Build compact input for scoring
    payload = {
        'title':       note.get('title', ''),
        'summary':     note.get('summary_short', ''),
        'confidence':  note.get('confidence', ''),
        'country':     note.get('geo_country', ''),
        'body_excerpt': (note.get('body_md') or '')[:600],
    }

    prompt = f"""Score this Benelux M&A newsletter note:

Title: {payload['title']}
Country: {payload['country']}
Confidence: {payload['confidence']}
Summary: {payload['summary']}
Body excerpt: {payload['body_excerpt']}"""

    try:
        r = client.messages.create(
            model=os.environ.get('MODEL_HAIKU', 'claude-haiku-4-5-20251001'),  # simple classification
            max_tokens=200,
            system=SCORE_SYSTEM,
            messages=[{'role': 'user', 'content': prompt}]
        )
        text = r.content[0].text.strip()
        text = text.replace('```json','').replace('```','').strip()
        parsed = json.loads(text)
        score   = max(1, min(10, int(parsed.get('score', 5))))
        rationale = str(parsed.get('rationale', ''))[:600]
        angle     = str(parsed.get('newsletter_angle', ''))[:600]
        return score, rationale, angle
    except Exception as e:
        print(f"    ⚠ Score error: {e}")
        return None

# ── Main ────────────────────────────────────────────────────────────────────
def run():
    print("=" * 60)
    print(f"GRAPEVINE SCORER v1.1 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE'} | Rescore all: {RESCORE}")
    print("=" * 60)

    if not client:
        print("✗ No ANTHROPIC_API_KEY"); return
    if not DRY_RUN and not SUPABASE_KEY:
        print("✗ No SUPABASE_SERVICE_KEY — use --dry-run"); return

    # Fetch notes
    params = {
        'select': 'note_id,title,summary_short,confidence,geo_country,body_md,structured_data,status',
        # FIXED v1.1: filter on note_type + status + soft-delete (replaces obsolete capture_origin=signal_enrich)
        'note_type':  'eq.WHISPER_NOTE',
        'status':     'in.(draft,active)',
        'is_deleted': 'eq.false',
        'order': 'created_at.asc',
        'limit': '100',
    }
    notes = sb_get('grapevine_notes', params) or []

    # Filter: skip already scored unless --all
    if not RESCORE:
        notes = [n for n in notes
                 if not (n.get('structured_data') or {}).get('newsworthiness_score')]

    if not notes:
        print("  Nothing to score — all notes already have a score (use --all to rescore)")
        return

    print(f"\n  {len(notes)} note(s) to score\n")

    results = []
    scored = 0
    failed = 0

    for i, note in enumerate(notes, 1):
        title = (note.get('title') or 'Untitled')[:60]
        print(f"  [{i}/{len(notes)}] {title}…")

        result = score_note(note)
        if not result:
            failed += 1
            continue

        score, rationale, angle = result
        score_bar = '█' * score + '░' * (10 - score)
        print(f"           Score: {score}/10  [{score_bar}]")
        print(f"           {rationale}")

        results.append({
            'note_id':  note['note_id'],
            'title':    note.get('title',''),
            'country':  note.get('geo_country',''),
            'status':   note.get('status',''),
            'score':    score,
            'rationale': rationale,
            'angle':    angle,
        })

        if not DRY_RUN:
            # Merge score into existing structured_data
            sd = note.get('structured_data') or {}
            if isinstance(sd, str):
                try: sd = json.loads(sd)
                except: sd = {}
            sd['newsworthiness_score']     = score
            sd['newsworthiness_rationale'] = rationale
            sd['newsletter_angle']         = angle
            sb_patch('grapevine_notes',
                     {'note_id': f'eq.{note["note_id"]}'},
                     {'structured_data': sd})
            scored += 1

        # Pause between calls (rate limit)
        if i < len(notes):
            time.sleep(3)

    # Summary
    print(f"\n{'='*60}")
    print(f"SCORING SUMMARY")
    print(f"{'='*60}")

    if results:
        results.sort(key=lambda x: -x['score'])
        print(f"\n  {'Score':<8} {'Country':<6} {'Status':<10} Title")
        print(f"  {'─'*8} {'─'*6} {'─'*10} {'─'*40}")
        for r in results:
            bar = '█' * r['score'] + '░' * (10 - r['score'])
            print(f"  {r['score']}/10 [{bar}] {r['country']:<4} {r['status']:<10} {r['title'][:45]}")

        avg = sum(r['score'] for r in results) / len(results)
        print(f"\n  Average score : {avg:.1f}/10")
        print(f"  High (8-10)   : {sum(1 for r in results if r['score']>=8)}")
        print(f"  Mid  (5-7)    : {sum(1 for r in results if 5<=r['score']<8)}")
        print(f"  Low  (1-4)    : {sum(1 for r in results if r['score']<5)}")

    if not DRY_RUN:
        print(f"\n  Scored: {scored} | Failed: {failed}")
        print(f"  → Scores stored in structured_data.newsworthiness_score")
    else:
        print(f"\n  DRY RUN — no writes made")
    print(f"{'='*60}")

if __name__ == '__main__':
    run()
