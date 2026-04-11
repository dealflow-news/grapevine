# 🌿 Grapevine — Intelligence OS

**Dealflow.News / V4G | Benelux Lower Mid-Market M&A Intelligence**

Live at: **https://grapevine.dealflow.news**

## Repository structure

```
├── index.html                          # UI (served via GitHub Pages)
├── CNAME                               # grapevine.dealflow.news
├── grapevine_addons.sql                # Schema addons (apply in Supabase SQL Editor)
├── scripts/
│   ├── intel_capture.py               # Nightly enrichment + --to-card CLI (v1.1)
│   └── score_grapevine.py             # Batch newsworthiness scoring (v1.1)
├── supabase/
│   └── functions/
│       └── grapevine-to-card/
│           └── index.ts               # Edge Function: Extract Card (Deno)
└── docs/
    ├── Grapevine_Briefing_v2.1.md     # Full context reference
    └── Grapevine_Project_Summary.md   # Quick reference
```

## Deploy

- **UI:** Auto-deployed via GitHub Pages on push to `main`
- **Edge Function:** `supabase functions deploy grapevine-to-card`
- **Scripts:** Run locally via Windows Task Scheduler (03:00 daily)

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML/JS — single file |
| Database | Supabase / PostgreSQL |
| AI | Claude Sonnet (enrichment + card extraction) · Claude Haiku (scoring) |
| Edge Function | Supabase Edge Functions (Deno) |
| Hosting | GitHub Pages |

---
*Dealflow.News · Confidential · April 2026*
