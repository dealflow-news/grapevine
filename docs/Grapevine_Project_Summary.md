# Grapevine Intelligence OS — Project Summary
**Dealflow.News / V4G | April 2026 | Confidential**
**Version 2.1 — updated after Phase 2 Sprint 1 (10 April 2026)**

---

## What Grapevine is

Grapevine is the editorial market intelligence OS for Dealflow.News / V4G. It sits between raw deal signals (`market_intelligence` table) and commercial mandate work — capturing, enriching, curating, and packaging Benelux lower mid-market M&A intel for distribution.

**Not SaaS** — a content and institutional memory layer that activates movers & shakers and drives inbound mandates/referrals.

**Flow:**
```
Raw signal → intel_capture.py → WHISPER_NOTE draft
    → Curate/score → Pattern Candidate flag
    → ◉ Extract Card (Edge Function) → KNOWLEDGE_CARD draft
    → Promote → audience selection → Distribution
```

**Primary audience:** Founders 55+, family offices, PE partners, notaries, boutique M&A lawyers — Benelux, €5–50M EV focus.

---

## Infrastructure

| Key | Value |
|-----|-------|
| Supabase project | `rirkgpsdcaxnowwmliof` |
| REST base | `https://rirkgpsdcaxnowwmliof.supabase.co/rest/v1` |
| V4G party_id | `38cff812-397f-5fb4-bf18-a0e8b42b2a69` |
| Frontend | `index.html` (was `grapevine_phase1.html`) — vanilla HTML/JS, hardcoded anon key |
| Hosting | `https://grapevine.dealflow.news` (GitHub Pages — repo: `dealflow-news/grapevine`) |
| Backend | `intel_capture.py` (nightly 03:00) + `score_grapevine.py` |
| Edge Function | `grapevine-to-card` — Supabase Edge Function (Deno) |
| Models | Sonnet for enrichment + card extraction · Haiku for scoring |
| Auth model | Single-user — anon key with RLS · full auth deferred to Phase 3 |

---

## Core table: grapevine_notes

### Canonical enum values — use exactly

| Field | Values |
|-------|--------|
| `note_type` | `WHISPER_NOTE` \| `KNOWLEDGE_CARD` |
| `status` | `draft` \| `active` \| `archived` |
| `sensitivity_level` | `PUBLIC` \| `CLIENTSAFE` \| `INTERNALONLY` \| `RESTRICTED` |
| `visibility_scope` | `PRIVATE` \| `TEAM` \| `ORG` \| `CLIENT` \| `PUBLIC` |
| `intended_audience` | `internal` \| `client` \| `mover_shaker` \| `external_broad` |
| `review_status` | `pending` \| `approved` \| `rejected` |
| `link_status` | `unlinked` \| `link_pending` \| `linked` \| `unresolved` |
| `capture_origin` | `signal_enrich` \| `whisper_report` \| `intel_quicksave` \| `drop_point` |

### Governance rules (non-negotiable)
- **INTERNALONLY / RESTRICTED** must never appear in `CLIENT` or `PUBLIC` visibility — enforced in UI + RLS.
- **Soft delete only:** `is_deleted = true` — no hard deletes from UI.
- **Linker is non-blocking:** On Promote → `link_status = link_pending` · resolved async in Phase 2.
- **WHISPER_NOTE** = internal intel, sensitivity INTERNALONLY/TEAM. Never distributed directly.
- **KNOWLEDGE_CARD** = editorial asset, reusable across firms. Audience set at Promote.

### Approval flow
```
draft (review_status=pending)
  → Promote click → audience selector modal
  → active (review_status=approved, link_status=link_pending)
  → Linker resolves async → link_status=linked
```

### Key structured_data fields (JSONB)

**Scoring:**
`newsworthiness_score` · `newsworthiness_rationale` · `newsletter_angle`

**Pattern Library (Phase 2):**
`pattern_candidate` · `pattern_name` · `pattern_rationale` · `editorial_angle`

**Whisper metadata:**
`fact_table` · `source_box` · `what_we_know` · `what_we_dont_know` · `source_language`

**Knowledge Card:**
`core_insight` · `deal_implication` · `misread_risk` · `best_use` · `source_pattern_name` · `source_pattern_rationale` · `source_whisper_note_id`

---

## Pattern Library — Phase 2 core concept

Notes with `pattern_candidate=true` appear in the **◉ Candidates** tab in Curate. Four editorial layers:

| Layer | Field | Purpose |
|-------|-------|---------|
| Decision | `pattern_candidate` (bool) | Forces explicit decision: is this a structural pattern? |
| Conceptual | `pattern_name` | Short label — addressable, linkable, searchable |
| Analytical | `pattern_rationale` | Structural story: drivers, mechanism, time horizon |
| Communication | `editorial_angle` | How to frame it for the audience |

**Auto-flag:** `intel_capture.py` sets `pattern_candidate=true` when `newsworthiness_score ≥ 8`.
**Manual flag:** Edit panel in Curate → ☑ Pattern Candidate → fill 3 fields → Save.
**Extract:** ◉ Extract Card button → `grapevine-to-card` Edge Function → KNOWLEDGE_CARD draft.
**Clear:** `pattern_candidate` set to `false` automatically after card creation.

---

## UI — index.html (4 active tabs + 1 Phase 2)

| Tab | Status | Purpose |
|-----|--------|---------|
| **Grapevine / Curate** | ✅ Live | Draft/Active/Archived/◉ Candidates filters. Detail pane: body_md (markdown rendered), score, Edit, Promote, Archive, Delete (custom modal). Pattern Candidate toggle in Edit. ◉ Extract Card button (pattern candidates only). |
| **Knowledge Base** | ✅ Live | Active cards default. Show drafts / Include archived toggles. Left panel: card list (420px). Right panel: flex:1 detail. Promote/Edit/Archive in sticky footer. |
| **Drop Point** | ✅ Live | File/URL/text capture. SHA256 dedup. source_type→note_type suggest. Batch queue → Supabase. |
| **Intel Pulse** | 🔜 Phase 2 | Disabled, grayed in sidebar. Mandate signal matching. |

### Light/Dark mode
Segmented control in sidebar bottom: `☀ Light` / `🌙 Dark`. Persisted via `localStorage`.
- Dark: deep moss/graphite (`#141715` base), teal accent (`#6db6ae`)
- Light: warm editorial paper (`#f6f2ea` base), petrol teal (`#0f5c5a`)

### Active MANDATES config (hardcoded in HTML)
| Stage | Name | Sector | Geo | Score |
|-------|------|--------|-----|-------|
| Active | Sassicaia | Industrials | BE | 82 |
| Active | Brunello | Healthcare | BE | 65 |
| Active | Flamaway | Fire Safety | BE | 71 |
| Suspects | Railnova | Rail IoT | BE | 88 |
| Suspects | AE/Adapt&Enable | IT Consulting | BE | 95 |
| Prep | Healthcare NL | Healthcare | NL | 55 |
| Prep | Insurance BE/NL | Insurance | BE/NL | 62 |

---

## Backend scripts

### intel_capture.py ✅ v1.1
Nightly enrichment + Knowledge Card extraction.

**Canonical values written:**
`note_type='WHISPER_NOTE'` · `visibility_scope='TEAM'` · `sensitivity_level='PUBLIC'` · `intended_audience='internal'` · `link_status='unlinked'` · `capture_origin='signal_enrich'`

**Auto-flag pattern candidates:**
Score ≥ 8 → `pattern_candidate=true` + `pattern_name=title` + `pattern_rationale=newsletter_angle`

```bash
python intel_capture.py                              # nightly run
python intel_capture.py --dry-run --limit=3          # preview
python intel_capture.py --mi-id=<uuid>               # single re-enrich
python intel_capture.py --to-card=<note_id>          # extract KNOWLEDGE_CARD
python intel_capture.py --to-card=<note_id> --dry-run  # preview card
```

**`--to-card` guards:**
- note_type must be WHISPER_NOTE
- pattern_candidate must be true
- Clears pattern_candidate=false on source note after card creation

### score_grapevine.py ✅ v1.1
Batch newsworthiness scoring. Filter: `note_type=WHISPER_NOTE` + `status in (draft,active)` + `is_deleted=false`.

```bash
python score_grapevine.py          # score unscored notes
python score_grapevine.py --all    # rescore all
python score_grapevine.py --dry-run
```

### grapevine-to-card Edge Function ✅ v1.0
Supabase Edge Function (Deno). Called by ◉ Extract Card button in UI.

- URL: `https://rirkgpsdcaxnowwmliof.supabase.co/functions/v1/grapevine-to-card`
- Auth: anon key in Authorization header
- Routes: `GET /health` · `POST /extract { note_id }`
- Guards: note_type=WHISPER_NOTE, pattern_candidate=true, duplicate check
- Secrets: `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- After card creation: clears `pattern_candidate=false` on source note

**KnowledgeCardExtractor prompt reads:**
`pattern_name` · `pattern_rationale` · `editorial_angle` → 4 output fields: `core_insight`, `deal_implication`, `misread_risk`, `best_use[]`

---

## RLS policies (current state)

| Policy | Role | Cmd | Notes |
|--------|------|-----|-------|
| `gn_service_all` | service_role | ALL | Full access |
| `gn_anon_insert` | anon | INSERT | status=draft + is_deleted=false only |
| `gn_anon_select` | anon | SELECT | sensitivity NOT IN (INTERNALONLY, RESTRICTED) |
| `gn_anon_update` | anon | UPDATE | USING true / WITH CHECK true (allows soft-delete) |

---

## Newsworthiness scoring

| Criterion | Weight |
|-----------|--------|
| Deal specificity (named parties) | 25% |
| Benelux relevance (BE/LU > NL > FR) | 25% |
| Mid-market fit €5M–€500M | 20% |
| Recency signal | 15% |
| Source quality | 15% |

Score ≥ 8 → auto-flag `pattern_candidate=true`
Score 6-7 → `pattern_candidate=false` explicit (analyst can promote manually)
Score ≤ 5 → no flag

---

## Two-layer architecture

```
WHISPER_NOTE (TEAM/INTERNALONLY)     KNOWLEDGE_CARD (PUBLIC → audience at Promote)
────────────────────────────────     ──────────────────────────────────────────────
Raw intel, deal signals              Structural pattern, editorial asset
capture_origin: signal_enrich        capture_origin: whisper_report
Never distributed directly           → newsletter / briefings / movers & shakers
source_ref_id → market_intelligence  source_ref_id → whisper note_id
```

---

## Phase roadmap

### Phase 1 ✅ Completed
Curate tab · Knowledge Base · Drop Point · intel_capture.py · scoring · soft delete · pattern candidate flag · light/dark mode · editorial palette.

### Phase 2 ✅ Sprint 1 completed (10 April 2026)
- `--to-card` CLI flag in intel_capture.py
- `grapevine-to-card` Edge Function
- ◉ Extract Card button in Curate UI
- Pattern Library: 4-layer editorial structure
- Auto-flag pattern candidates (score ≥ 8)
- ◉ Candidates tab in Curate
- Knowledge Base: sticky footer actions, Edit mode, Show drafts/archived toggles
- Deployment: `https://grapevine.dealflow.news`
- Custom delete modal

### Phase 2 — Remaining
- Linker engine: on Promote → surface linked Knowledge Cards → resolve link_pending
- Newsletter digest generator
- `intel_capture.py` scheduling via Windows Task Scheduler

### Phase 3 — Planned
- Auth (Supabase auth or Cloudflare Access)
- Client-facing KB view (filtered by visibility_scope)
- NL/FR translation pipeline
- Collections → briefing packs
- Intel Pulse tab (mandate signal matching)

---

## Active files — upload ALL to Claude Project

| File | Status | Role |
|------|--------|------|
| `Grapevine_Project_Summary.md` (this) | ✅ v2.1 | Session starter |
| `Grapevine_Briefing_v2.1.md` | ✅ v2.1 | Full context reference |
| `Grapevine_Functional_Spec_v2.2.docx` | ✅ Frozen | Primary spec — do not reopen |
| `index.html` | ✅ Live | Production UI |
| `intel_capture.py` | ✅ v1.1 | Nightly enrichment + --to-card |
| `score_grapevine.py` | ✅ v1.1 | Batch scoring |
| `grapevine_addons.sql` | ✅ Applied | Schema addons |

## Obsolete — do not reference
`grapevine_phase1.html` (renamed to `index.html`) · `Grapevine_Briefing_v2.0.docx` (superseded) · All pre-v2.1 project summaries.

---

*Dealflow.News / V4G · Confidential · April 2026*
