# 🌿 Grapevine — Intelligence OS

**V4G / Dealflow.News | Benelux Lower Mid-Market M&A Intelligence**

Grapevine is the editorial market intelligence OS for Dealflow.News. It sits between raw deal signals and commercial mandate work — capturing, enriching, curating, and packaging Benelux lower mid-market M&A intel for distribution.

## What it does

- **Curate** — Review, promote and archive enriched WHISPER_NOTEs from the nightly IntelCapture pipeline
- **Knowledge Base** — Browse and search KNOWLEDGE_CARDs distilled from pattern-candidate whispers
- **Drop Point** — Manual deep capture: paste URLs, text, or upload files directly to the corpus
- **◉ Extract Card** — One-click Knowledge Card extraction via AI (Edge Function)

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML/JS — single file, no build step |
| Database | Supabase / PostgreSQL (`rirkgpsdcaxnowwmliof`) |
| AI Enrichment | Claude Sonnet (MarketWhisperSnippet + KnowledgeCardExtractor) |
| AI Scoring | Claude Haiku (newsworthiness scoring) |
| Edge Function | `grapevine-to-card` — Supabase Edge Function (Deno) |
| Hosting | GitHub Pages → `grapevine.dealflow.news` |

## Flow

```
Raw signal (market_intelligence)
    ↓  intel_capture.py (nightly 03:00)
WHISPER_NOTE draft (grapevine_notes)
    ↓  Analyst: Curate → Promote
WHISPER_NOTE active
    ↓  Edit → ☑ Pattern Candidate → ◉ Extract Card
KNOWLEDGE_CARD draft
    ↓  KB tab → Promote → audience selection
KNOWLEDGE_CARD active → Distribution
```

## Pattern Library

Notes flagged as `pattern_candidate=true` appear in the **◉ Candidates** tab. Four editorial layers:

1. **Pattern Name** — short, addressable label
2. **Pattern Rationale** — structural story: drivers, mechanism, time horizon
3. **Editorial Angle** — communication layer: how to frame it for the audience
4. **◉ Extract Card** → KnowledgeCardExtractor (Claude Sonnet via Edge Function)

## Governance

| Field | Values |
|-------|--------|
| `note_type` | `WHISPER_NOTE` \| `KNOWLEDGE_CARD` |
| `sensitivity_level` | `PUBLIC` \| `CLIENTSAFE` \| `INTERNALONLY` \| `RESTRICTED` |
| `visibility_scope` | `PRIVATE` \| `TEAM` \| `ORG` \| `CLIENT` \| `PUBLIC` |
| `capture_origin` | `signal_enrich` \| `whisper_report` \| `intel_quicksave` \| `drop_point` |

**Rule:** `INTERNALONLY` / `RESTRICTED` never reach `CLIENT` or `PUBLIC` visibility.

## Backend scripts

- `intel_capture.py` — Nightly enrichment + `--to-card` CLI for manual card extraction
- `score_grapevine.py` — Batch newsworthiness scoring for existing notes

## Deployment

Hosted on GitHub Pages at `grapevine.dealflow.news`.

---

*Dealflow.News · Confidential · April 2026*
