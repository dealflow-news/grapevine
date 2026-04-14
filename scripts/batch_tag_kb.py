#!/usr/bin/env python3
"""
batch_tag_kb.py — Grapevine Taxonomy B1 Backfill
Assigns kb_tags (library_domain, asset_type, ma_lens, strategic_themes, sector)
to all active KNOWLEDGE_CARDs via the Edge Function /tag route.

Usage:
    python batch_tag_kb.py [--dry-run] [--limit 10]
"""
import os, sys, json, time, httpx
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line: continue
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()

SUPABASE_URL  = os.environ.get('SUPABASE_URL', 'https://rirkgpsdcaxnowwmliof.supabase.co')
SUPABASE_KEY  = (os.environ.get('SUPABASE_SERVICE_KEY')
              or os.environ.get('SUPABASE_ANON_KEY')
              # Fallback: hardcoded anon key (Edge Function uses own service key)
              or 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJpcmtncHNkY2F4bm93d21saW9mIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE4NjU2OTYsImV4cCI6MjA4NzQ0MTY5Nn0.zZux0_8odNgdltD7LYF5C_zpRPx0Bdvg6q0omZV72Lg')
EDGE_FN_URL   = f"{SUPABASE_URL.replace('/rest/v1','').replace('https://','https://')}/functions/v1/grapevine-to-card"
DRY_RUN       = '--dry-run' in sys.argv
LIMIT_ARG     = next((sys.argv[sys.argv.index('--limit')+1] for i,a in enumerate(sys.argv) if a=='--limit'), None)
LIMIT         = int(LIMIT_ARG) if LIMIT_ARG else 200
DELAY         = 1.5  # seconds between calls (Haiku rate limit)

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
}

def sb_get(path, params=None):
    r = httpx.get(f'{SUPABASE_URL}/rest/v1/{path}', params=params, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def call_tag(note_id):
    r = httpx.post(
        f'{EDGE_FN_URL}/tag',
        json={'note_id': note_id},
        headers={**headers, 'Authorization': f'Bearer {SUPABASE_KEY}'},
        timeout=30
    )
    r.raise_for_status()
    return r.json()

def main():
    print(f"\n{'='*60}")
    print(f"  Grapevine Taxonomy B1 Backfill  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}  |  Limit: {LIMIT}")
    print(f"{'='*60}\n")

    # Fetch cards without kb_tags or with incomplete kb_tags
    print("[1] Fetching KNOWLEDGE_CARDs to tag...")
    rows = sb_get('grapevine_notes', {
        'select': 'note_id,title,status,structured_data',
        'note_type': 'eq.KNOWLEDGE_CARD',
        'is_deleted': 'eq.false',
        'status': 'in.(active,draft)',
        'order': 'created_at.asc',
        'limit': str(LIMIT),
    })

    # Filter: only cards without kb_tags
    to_tag = []
    already_tagged = 0
    for r in rows:
        sd = r.get('structured_data') or {}
        if isinstance(sd, str):
            try: sd = json.loads(sd)
            except: sd = {}
        if sd.get('kb_tags', {}).get('library_domain'):
            already_tagged += 1
        else:
            to_tag.append(r)

    print(f"  Total fetched: {len(rows)}")
    print(f"  Already tagged: {already_tagged}")
    print(f"  To tag now: {len(to_tag)}\n")

    if DRY_RUN:
        print("DRY RUN — showing first 5:")
        for r in to_tag[:5]:
            print(f"  • {r['note_id'][:8]} {r['title'][:60]}")
        return

    ok = 0; err = 0; skipped = 0
    results = []

    for i, card in enumerate(to_tag):
        nid   = card['note_id']
        title = card['title'] or '(untitled)'
        print(f"  [{i+1}/{len(to_tag)}] {title[:65]}…")

        try:
            result = call_tag(nid)
            if result.get('ok'):
                tags = result.get('kb_tags', {})
                conf = result.get('confidence', '?')
                print(f"    ld={tags.get('library_domain','')}  at={tags.get('asset_type','')}  conf={conf}")
                print(f"    ml={tags.get('ma_lens',[])}  th={tags.get('strategic_themes',[])}  sc={tags.get('sector',[])}")
                ok += 1
                results.append({'note_id': nid, 'title': title, 'kb_tags': tags, 'confidence': conf})
            else:
                print(f"    ! Error: {result.get('error','unknown')}")
                err += 1
        except Exception as e:
            print(f"    ! Exception: {str(e)[:80]}")
            err += 1

        time.sleep(DELAY)

    print(f"\n{'='*60}")
    print(f"  DONE: {ok} tagged  |  {err} errors  |  {already_tagged} skipped (already tagged)")
    print(f"{'='*60}\n")

    # Save results log
    if results:
        log_path = f"batch_tag_log_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(log_path, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"  Log saved: {log_path}")

if __name__ == '__main__':
    main()
