# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Position in the V4G Intelligence Platform

This repo is one of four in the V4G stack. Per the V4G Intelligence Platform Roadmap v1.1 (Feb 2026), dealflow.news is positioned as a Phase 3 (Q3 2026) public-facing M&A intelligence layer built on the Golden Safe backend. Grapevine is the **editorial / intelligence curation** surface of that layer — distinct from ticker.dealflow.news which is the publication / Focus Terminal surface.

| Repo | Role |
|---|---|
| golden-safe-repo | Canonical truth layer, schema, governance doctrine |
| ticker-dealflow | Focus Terminal — publication + intake pipeline |
| **grapevine-repo (this)** | **Editorial OS — curation, knowledge cards, briefings** |
| v4g-ingestion | Heavy ingestion pipeline (NBB/KBO/PB) |

Companion documentation (in V4G doc system, not in this repo):
- `01_V4G_Intelligence_Platform_Roadmap_v1_1.docx` — phase status, 3-layer classification model (Sector/Theme/Thesis), governance rules
- `03_GoldenSafe_Architecture_ADR_v2.docx` — 4-layer data architecture (Raw/Core/Enrichment/Intelligence), ADR-005 through ADR-010

Note: this repo introduces its OWN three-layer model (S1/S2/S3 + BB) for UI/UX concerns. That is a different abstraction than the Roadmap's classification layers or the ADR's ETL layers — see "Architecture" below.

For platform doctrine and conventions across all four repos: see `../golden-safe-repo/CLAUDE.md`. For the authoritative schema dictionary: `../golden-safe-repo/exports/golden_safe/golden_safe_dictionary_v6.md`.

## What Grapevine is

Editorial market intelligence OS for V4G — Ventures4Growth (Dealflow.News). Single-user, single-tenant tool covering Benelux + Northern France lower mid-market M&A (EV €5–50M). **Not a SaaS** — a content + institutional-memory layer.

Live at https://grapevine.dealflow.news (GitHub Pages, auto-deployed from `main`).

## Repo layout — and what is and isn't built here

```
index.html                              # The entire UI (vanilla HTML/JS, ~3300 lines, single file)
grapevine_addons.sql                    # Idempotent schema add-ons (run in Supabase SQL Editor)
supabase/functions/grapevine-to-card/   # Deno Edge Function — only backend code that lives here
scripts/*.py                            # Local copies of nightly enrichment/scoring scripts
promote_kb_drafts.py                    # One-shot batch enrich/promote utility
docs/                                   # Architecture lock + project briefing (READ THESE)
```

Backend scripts (`intel_capture.py`, `score_grapevine.py`, etc.) also live in the sibling repo `dealflow-news/golden-safe-repo`, and the raw-signal pipeline lives in `dealflow-news/ticker-dealflow` (`dealflow_pipeline.py`). The copies in `scripts/` are runnable but the canonical home is `golden-safe-repo`.

## Architecture — three shells, one backbone

This is **the** mental model — applies to every feature decision (`docs/shell_map_v_1_0_final.md`, `docs/backbone_object_map_v_1_0.md`).

| Shell | Name | Status | Owns |
|-------|------|--------|------|
| **S1** | Editor Workbench | Active build (Sprint E/F) | Today · Curate · Knowledge Base · Drop Point · Briefing Studio |
| **S2** | Mandate Workspace | Sprint G+ | Mandate matching, action board, brief pack |
| **S3** | View Layer | Sprint 3.x | Reader-safe surfaces, editorial cues |
| **BB** | Shared backbone | Ongoing | Schema, RLS, routing metadata |

**Build order:** S1 → S2 → S3. Without S1 depth, S2 has weak inputs. Tickets must be labeled S1/S2/S3/BB; cross-shell tickets must be split.

### Canonical objects (all rows in `grapevine_notes`, distinguished by `note_type` + JSONB)

- `signal` / `intel_note` → `note_type = 'WHISPER_NOTE'` — raw or curated whisper; never distributed directly
- `knowledge_card` → `note_type = 'KNOWLEDGE_CARD'` — reusable editorial asset; audience set at Promote
- `pattern` → `structured_data.pattern_candidate = true` (staging only; gets own object in Sprint F)
- `mandate` → hardcoded JS array in `index.html` (`MANDATES`, ~line 929) until Sprint G migrates to DB

Mandate relevance belongs in `mandate_match`, **not** as a field on `intel_note`. Reader feedback belongs in `editorial_cue`, **not** in any note. These lines must not blur.

## Vocabulary lock — non-cosmetic

Each shell speaks a different language. Crossing them in UI copy is an architecture bug, not a copy nit (`docs/vocabulary_lock_v_1_0.md`).

- **S1 (Editor Workbench)** — editorial production: *draft · active · archived · candidate · review · enrich · promote · extract · evidence · provenance*
- **S2 (Mandate Workspace)** — commercial: *relevant · watch · priority · contact-ready · next action · thesis fit · mandate brief*
- **S3 (View Layer)** — reader-safe: *why it matters · what to watch · themes · briefings*

**Banned in S1:** "contact-ready", "next action needed", "who cares" framings, generic SaaS copy. The Today-tab Mandate teaser is the only S1/S2 bridge surface — it shows awareness, not execution vocabulary.

## Database — `grapevine_notes` is the table

Single Supabase project (`rirkgpsdcaxnowwmliof`). Almost everything lives in one table with rich JSONB (`structured_data`, `kb_tags`).

### Canonical enum values — use exactly (match DB CHECK constraints, no underscores)

| Field | Values |
|-------|--------|
| `note_type` | `WHISPER_NOTE` \| `KNOWLEDGE_CARD` |
| `status` | `draft` \| `active` \| `archived` |
| `sensitivity_level` | `PUBLIC` \| `CLIENTSAFE` \| `INTERNALONLY` \| `RESTRICTED` |
| `visibility_scope` | `PRIVATE` \| `TEAM` \| `ORG` \| `CLIENT` \| `PUBLIC` |
| `review_status` | `pending` \| `approved` \| `rejected` |
| `capture_origin` | `signal_enrich` \| `whisper_report` \| `intel_quicksave` \| `drop_point` |

### Governance rules (non-negotiable, enforced in UI + RLS)

- **INTERNALONLY / RESTRICTED** must never appear in `CLIENT` or `PUBLIC` visibility scope.
- **Soft delete only** — set `is_deleted = true`. Never hard-delete from UI.
- **`gn_anon_select`** RLS policy blocks INTERNALONLY + RESTRICTED. **`gn_anon_insert`** allows drafts only. Service role has full access.
- **WHISPER_NOTE** stays internal. Distribution audience is set when promoting to KNOWLEDGE_CARD.

The browser carries the **anon key** in plaintext (`index.html:921`). That is intentional — RLS is the actual gate.

## Frontend — `index.html`

A single ~3300-line file. No bundler, no framework, no build step. Tab routing via `switchTab()` (`index.html:1136`); each tab has a top-level `render<Tab>()` function. Supabase access via `sbGet`/`sbPost`/`sbPatch` helpers (`index.html:942+`). Edge Function calls go to `EDGE_FN_URL` (line 924).

State lives in a single module-level `state` object — mutate it, then call the right `render*` function. There is no virtual DOM and no reactive layer.

When adding UI: edit `index.html` directly. Don't reach for a framework.

## Edge Function — `supabase/functions/grapevine-to-card/index.ts`

One Deno function, six routes. Calls Anthropic API directly using `ANTHROPIC_API_KEY` env var. Uses `claude-sonnet-4-6` for enrichment/extraction and `claude-haiku-4-5-20251001` for scoring/tagging.

| Route | Purpose |
|-------|---------|
| `GET /health` | Version check |
| `POST /extract` `{note_id}` | WHISPER → KC, or enrich KC in place |
| `POST /prescreen` `{filename, text?, base64?}` | Batch pre-scan verdict + kb_tags |
| `POST /enrich` `{title, text}` | Batch KC enrichment + kb_tags |
| `POST /tag` `{note_id}` | Tag existing card |
| `POST /ingest` `{note}` | Direct insert via service key |

Taxonomy v1.2 is embedded as a prompt constant (`TAXONOMY_PROMPT`) — when taxonomy changes, update it here too.

## Commands

### Frontend
Just open `index.html` in a browser, or push to `main` to deploy to GitHub Pages. No build step.

### Edge Function
```
supabase functions deploy grapevine-to-card
```

### Schema add-ons
Run `grapevine_addons.sql` in the Supabase SQL Editor. Idempotent — safe to re-run.

### Python scripts — common flags

All scripts read `.env` from their own directory (looks for `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`). They use the **service key**, not anon — they bypass RLS.

```
python scripts/intel_capture.py --dry-run --limit=3        # safe test
python scripts/intel_capture.py --limit=10                 # default nightly run
python scripts/intel_capture.py --mi-id=<uuid>             # one market_intelligence item
python scripts/intel_capture.py --to-card=<note_id>        # WHISPER → KC extraction

python scripts/score_grapevine.py --dry-run                # preview scores
python scripts/score_grapevine.py                          # score unscored notes
python scripts/score_grapevine.py --all                    # re-score everything

python promote_kb_drafts.py --dry-run --limit=3            # preview promotion
python promote_kb_drafts.py --note-id=<uuid>               # single card
python promote_kb_drafts.py --sources-only                 # only patch source_access
```

There is no test suite, no linter, no type checker configured.

## Sprint constraints — read before scoping

Current sprint context lives in `docs/Grapevine_Project_Summary_v2_4.md` and `docs/Grapevine_Changelog_v2_4.md`. Check those before assuming what's in scope.

Hard constraints that have come up:
- **No new Supabase schema in Sprint E** — first migration since spec-freeze lands in Sprint F.
- **Briefing Studio output stays in a textarea** until Sprint F adds persistence.
- **Mandate teaser is hardcoded JS** until Sprint G.
- **`editorial_cue` schema is deferred** to Sprint F as a forward-compatible bridge to S3.

## Conventions that aren't obvious from the code

- Actor strings (`reviewed_by`, `approved_by`, `created_by`) are **plain text**, not UUIDs — there is no users table. Use values like `chris.raman`, `intel_capture_v1`, `analyst`.
- Region `FR(N)` (Hauts-de-France, Grand Est) is scored **equal to BE/NL/LU** — `DIRECT`, not analogous.
- Newsworthiness score ≥ 8 auto-flags `structured_data.pattern_candidate = true`.
- Newsletter / publication language is **Belgian-Dutch leaning** in some scripts (see `score_grapevine.py` docstring) — that's intentional, don't "translate" it.

## What not to do

1. Never put INTERNALONLY or RESTRICTED notes in CLIENT or PUBLIC visibility_scope — enforced by RLS, but UI must also gate.
2. Never hard-delete from the UI — soft delete only (`is_deleted = true`).
3. Never distribute a WHISPER_NOTE directly — audience is set when promoting to KNOWLEDGE_CARD.
4. Never blur object boundaries: mandate relevance lives in `mandate_match`, NOT as a field on intel_note. Reader feedback lives in `editorial_cue`, NOT on any note.
5. Never cross shell vocabulary in UI copy (e.g. don't put "contact-ready" in S1) — that is an architecture bug, not a copy nit.
6. Never add new Supabase schema in Sprint E — first migration since spec-freeze lands in Sprint F.
7. Never reach for a framework / bundler / build step for the frontend — `index.html` stays a single vanilla file by design.
8. Never use the anon key for backend scripts — they use the service key and bypass RLS by design.
9. Never "translate" Belgian-Dutch script docstrings / output — that's intentional, not a typo.
10. Never change taxonomy in the Edge Function prompt without also updating `TAXONOMY_PROMPT` in the same file.

## How this file evolves

Bump version + add changelog entry when canonical objects, governance rules, or shell boundaries change. Schema dictionary and platform doctrine changes live in `../golden-safe-repo/` — reference them, don't duplicate.

- v1.0 · 2026-05-21 — initial via /init + V4G platform integration
