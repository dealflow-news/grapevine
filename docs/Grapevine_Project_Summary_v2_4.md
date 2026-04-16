# Grapevine Intelligence OS — Project Summary
**Dealflow.News / V4G — Ventures4Growth, Ghent | April 2026 | Confidential**
**Version 2.4 — Architecture baseline adopted (16 April 2026)**

---

## What Grapevine is

Grapevine is the editorial market intelligence OS for V4G — Ventures4Growth. It sits between raw deal signals and commercial mandate work — capturing, enriching, curating, and packaging Benelux + Northern France lower mid-market M&A intel for distribution.

**Not SaaS** — a content and institutional memory layer that activates movers & shakers and drives inbound mandates and referrals.

**Coverage region:** Belgium · Netherlands · Luxembourg · Northern France (Hauts-de-France, Grand Est) · EV €5–50M

**Flow:**
```
Raw signal → dealflow_pipeline.py → raw_signals table
    → gs_nightly_enrich.py → WHISPER_NOTE draft (grapevine_notes)
    → Curate: review / score / pattern candidate
    → ◉ Extract Card (Edge Function /extract) → KNOWLEDGE_CARD draft
    → Drop Point: manual ingest (PDF/DOCX/URL/text) → KNOWLEDGE_CARD draft
    → KB: review → Promote → Distribution
    → Briefing Studio (Sprint E): editorial angle → publishable output
```

---

## Three-Shell Architecture — APPROVED baseline (16 April 2026)

Grapevine is built as **one intelligence backbone, three shells**. This is the approved mental model for all product, backlog, and build decisions from this point forward.

| Shell | Name | Mission | Current status |
|-------|------|---------|---------------|
| **S1** | Editor Workbench | Create, curate, enrich, connect, package intelligence | ✅ Active build track |
| **S2** | Mandate Workspace | Apply intelligence to live mandates and commercial execution | 🔜 Sprint G+ |
| **S3** | View Layer | Deliver curated intelligence safely to non-operators | 🔜 Sprint 3.x |
| **BB** | Shared backbone | Schema, RLS, routing metadata, object lineage | Ongoing |

**Build order rule:** S1 first (creates corpus) → S2 second (applies corpus) → S3 third (exposes selected corpus). Without S1 depth, S2 has weak inputs. Without S1+S2 discipline, S3 has no trustworthy substance.

### Backlog labels — use on every ticket and feature decision
- **S1** — Editor Workbench feature
- **S2** — Mandate Workspace feature
- **S3** — View Layer feature
- **BB** — Shared backbone (schema, RLS, routing metadata only)

Cross-shell tickets must be split before entering a sprint. If a ticket cannot be labeled, the scope is unclear.

### Shell 1 — Editor Workbench: owns these zones
Today · Curate · Knowledge Base · Drop Point · Briefing Studio

### Shell 2 — Mandate Workspace: owns these zones (Sprint G+)
Mandate selector · Thesis panel · Match feed · Action board · Brief pack

### Shell 3 — View Layer: owns these zones (Sprint 3.x)
Briefings read surface · Signals read · Knowledge read · Editorial cue composer

---

## Canonical Object Map

One backbone, shell-specific access. Every feature decision must map to one of these objects.

| Canonical object | DB equivalent in grapevine_notes | Shell write rights | Notes |
|-----------------|----------------------------------|-------------------|-------|
| `signal` | `note_type = 'WHISPER_NOTE'` (pre-editorial) | S1 only | Raw or lightly processed event |
| `intel_note` | `note_type = 'WHISPER_NOTE'` (curated/active) | S1 only | Carries editorial judgment |
| `knowledge_card` | `note_type = 'KNOWLEDGE_CARD'` | S1 only | Reusable, durable intelligence |
| `pattern` | `structured_data.pattern_candidate = true` (staging) | S1 only | Sprint F: own object/state |
| `entity` | Not yet modelled | BB | Future sprint |
| `evidence_link` | `structured_data.source_access` + `source_box` | S1 only | Provenance layer |
| `audience_profile` | `sensitivity_level` + `visibility_scope` fields | BB/governance | Distribution gating |
| `mandate` | Hardcoded JS array (Sprint G → DB) | S2 only | Teaser in S1 is read-only |
| `mandate_match` | Not yet modelled (Sprint G) | S2 only | Relevance link, not editorial truth |
| `briefing_collection` | Sprint E → textarea output; Sprint F → persisted KC | S1 only | Assembly object |
| `editorial_cue` | Not yet modelled (Sprint F schema) | S3 creates, S1 reviews | Lightweight reader feedback — never a note |

**Mapping rule:** Mandate relevance belongs in `mandate_match`, not as a field on `intel_note`. Reader feedback belongs in `editorial_cue`, not in `signal` or `intel_note`. These lines must not blur.

---

## Vocabulary Lock — apply to all UI copy (S1)

Shell 1 uses editorial production language. Apply consistently to all labels, buttons, empty states, and tooltips.

### Approved S1 labels
Today · Curate · Knowledge Base · Drop Point · Briefing Studio · Signal Desk · Draft Lane · Evidence Queue · Pattern Resurfacing

### Approved S1 verbs
review · enrich · promote · extract · archive · route · verify · link · assign · draft

### Approved S1 states
draft · active · archived · candidate · pattern candidate

### Banned in S1
contact-ready · next action needed · who cares (as primary framing) · passive consumer language that hides editorial state

### S2 vocabulary (do not let bleed into S1)
relevant · watch · priority · contact-ready · next action · thesis fit · mandate brief · brief pack

### S3 vocabulary (do not let bleed into S1)
why it matters · what to watch · themes · briefings · help us cover this better

**One-screen rule:** A single screen must not mix S1 editorial jargon with S2 execution language. The Mandate teaser in Today is a bridge surface — it shows awareness, not mandate execution vocabulary.

---

## Architecture Lock v1.0.2 — Mandate Radar section: SUPERSEDED

The Architecture Lock v1.0.2 (approved earlier in Sprint D) planned **Mandate Radar** as a Sprint E tab with its own schema. This section is **superseded by Shell Map v1.0 (16 April 2026)**.

**What changed:**
- Mandate Radar as a standalone tab is cancelled
- Mandate matching logic moves to **Shell 2 — Mandate Workspace** (Sprint G+)
- A lightweight **Mandate teaser card** at the bottom of Today (S1) replaces it — read-only, hardcoded JS array, bridge surface only
- No mandate schema in Sprint E

All other sections of Architecture Lock v1.0.2 remain valid.

---

## Sprint E — Locked scope (Shell 1 only)

**Theme:** Today as editorial command deck + Briefing Studio as first output surface.

| Step | What | File | Shell |
|------|------|------|-------|
| E.1 | Add Today nav entry + tab shell | index.html | S1 |
| E.2 | KPI strip (5 live counts via Supabase SELECT) | index.html | S1 |
| E.3 | Lens preset pills (static array → filter signal feed) | index.html | S1 |
| E.4 | Signal feed in Today (reuse Curate list logic, filtered) | index.html | S1 |
| E.5 | Pattern resurfacing card (group by domain, count ≥ 3) | index.html | S1 |
| E.6 | Mandate teaser card (hardcoded array + domain match) | index.html | S1 — bridge teaser only |
| E.7 | Rename Intel Pulse → Briefing Studio, enable nav | index.html | S1 |
| E.8 | Briefing Studio thesis selector + source picker | index.html | S1 |
| E.9 | Claude API editorial angle call + output workspace | index.html | S1 |

**KPIs for E.2:** New this week · Signals needing review · Avg score · Tier A KCs · Promoted today

**Lens presets for E.3:** Distress · Succession · PE Entry · Growth Signal · Asset Sale · Founder Exit

**Nav position:** Today as first tab above Curate

**Today anatomy:**
```
┌─────────────────────────────────────────────────────┐
│  KPI STRIP  [New · Promoted · Avg score · ...]      │
├─────────────────────────────────────────────────────┤
│  LENS PRESETS  [Distress · Succession · PE · ...]   │
├─────────────────────┬───────────────────────────────┤
│  SIGNAL FEED        │  DETAIL / PREVIEW PANE        │
│  (filtered by lens) │  (KC or whisper expanded)     │
├─────────────────────┴───────────────────────────────┤
│  PATTERN RESURFACING  ["3 signals converge on X"]   │
├─────────────────────────────────────────────────────┤
│  MANDATE TEASER  (bottom card — S1 bridge only)     │
└─────────────────────────────────────────────────────┘
```

**Hard constraints for Sprint E:**
- S1 only — no mandate execution workflow
- No new Supabase schema changes
- No nav layout rewrite
- Mandate teaser reads hardcoded JS array only
- Briefing Studio output lives in textarea (copy/paste) — no persistence until Sprint F
- `editorial_cue` schema deferred to Sprint F

**Explicitly out of Sprint E:** Full Mandate Workspace · Lens preset persistence · Briefing Studio output persistence · `editorial_cue` schema · View Layer

---

## Sprint F — Planned scope (S1 hardening + BB groundwork)

- Lens preset persistence (`user_presets` table — first Supabase migration since spec freeze)
- Briefing Studio output persistence (save as `briefing_pack` KC)
- `editorial_cue` object schema (forward-compatible bridge for S3)
- Workbench `editorial_cue` review queue stub
- Pattern candidate confirmation flow
- Evidence completeness queue improvements

**Sprint F architectural constraint:** S1 core + `editorial_cue` schema as forward-compatible object. No S3 UX yet.

---

## Sprint G — Planned scope (S1→S2 bridge)

- `mandate` and `mandate_match` schema (Supabase migration)
- Replace hardcoded mandate JS array with DB-backed mandate objects
- Workbench Today mandate teaser reads from DB
- `mandate_match` suggestion flow from S1 Curate to S2

---

## Infrastructure

| Key | Value |
|-----|-------|
| Supabase project | `rirkgpsdcaxnowwmliof` |
| REST base | `https://rirkgpsdcaxnowwmliof.supabase.co/rest/v1` |
| Frontend | `index.html` — vanilla HTML/JS, hosted at `https://grapevine.dealflow.news` |
| Repo | `dealflow-news/grapevine` (GitHub Pages) |
| Pipeline repo | `dealflow-news/ticker-dealflow` (`dealflow_pipeline.py` v1.16) |
| Backend repo | `dealflow-news/golden-safe-repo` (`gs_nightly_enrich.py`, `intel_capture.py`, `score_grapevine.py`) |
| Edge Function | `grapevine-to-card` v1.6 — Supabase Edge Function (Deno) |
| Models | Sonnet 4 for enrichment/extraction · Haiku for scoring/tagging/prescreen |
| Auth model | Single-user — anon key with RLS · full auth deferred to S3 |
| Ticker | `https://dealflow.news` — `ticker_index.html` in `ticker-dealflow` repo |

---

## Core table: grapevine_notes

### Canonical enum values — use exactly

| Field | Values |
|-------|--------|
| `note_type` | `WHISPER_NOTE` \| `KNOWLEDGE_CARD` |
| `status` | `draft` \| `active` \| `archived` |
| `sensitivity_level` | `PUBLIC` \| `CLIENTSAFE` \| `INTERNALONLY` \| `RESTRICTED` |
| `visibility_scope` | `PRIVATE` \| `TEAM` \| `ORG` \| `CLIENT` \| `PUBLIC` |
| `review_status` | `pending` \| `approved` \| `rejected` |
| `link_status` | `unlinked` \| `link_pending` \| `linked` \| `unresolved` |
| `capture_origin` | `signal_enrich` \| `whisper_report` \| `intel_quicksave` \| `drop_point` |

### Governance rules (non-negotiable)
- **INTERNALONLY / RESTRICTED** must never appear in CLIENT or PUBLIC visibility — enforced in UI + RLS.
- **Soft delete only:** `is_deleted = true` — no hard deletes from UI.
- **RLS:** `gn_anon_select` blocks INTERNALONLY + RESTRICTED. `gn_anon_insert` allows drafts only.
- **WHISPER_NOTE** = internal intel. Never distributed directly.
- **KNOWLEDGE_CARD** = editorial asset. Audience set at Promote.

### Key structured_data fields (JSONB)

**Scoring (WHISPER_NOTE):**
`newsworthiness_score` · `newsworthiness_rationale` · `newsletter_angle`

**Pattern Library:**
`pattern_candidate` · `pattern_name` · `pattern_rationale` · `editorial_angle`

**Whisper metadata:**
`source_box` · `what_we_know` · `what_we_dont_know` · `source_language`

**Knowledge Card:**
`core_insight` · `deal_implication` · `misread_risk` · `best_use[]`
`source_pattern_name` · `source_whisper_note_id` · `card_type` · `ebl_id`

**Taxonomy (kb_tags):**
`library_domain` · `asset_type` · `asset_class` · `ma_lens[]` · `strategic_themes[]` · `sector[]`

**Quality:**
`kb_quality.tier` (A/B/C) · `kb_quality.benelux_fit` (direct/analogous/background)

**Source:**
`source_access.canonical_url` · `storage_url` · `source_access.author`

---

## Taxonomy v1.3 FINAL

**5 Blocks + 2 metadata layers:**

| Block | Count | Prefix | Description |
|-------|-------|--------|-------------|
| A — Library Domain | 11 | `ld_*` | Primary navigation — collapsed sections in KB |
| B — Asset Type | 15 | `ka_*` | What kind of knowledge asset |
| C — M&A Lens | 12 | `ml_*` | Transactional lens (1-2 per card) |
| D — Strategic Theme | 18 | `th_*` | Cross-cutting themes (1-3 per card) |
| E — Sector | 12 | `sc_*` | Sector context (0-2 per card) |
| G — Governance | — | — | sensitivity, visibility, status, tier, benelux_fit |
| H — Smart Intelligence | — | — | S3 derived scores |

**Asset Class** (new in v1.3): `commodity` / `contextual` / `proprietary`

**Block B asset types (15):**
`ka_library_source` · `ka_pattern` · `ka_playbook` · `ka_framework` · `ka_training_note` · `ka_editorial_angle` · `ka_case_note` · `ka_benchmark` · `ka_market_map` · `ka_signal_digest` · `ka_thesis` · `ka_template` · `ka_checklist` · `ka_failure_pattern` · `ka_internal_standard`

---

## KB current state (16 April 2026)

| Metric | Value |
|--------|-------|
| Active KCs | 180 |
| Benelux fit: direct | 160 |
| Benelux fit: analogous | 19 |
| Tier A | ~140 |
| Proprietary cards | ~15 |
| Domains covered | 10/11 |

**10 Framework KCs ingested (proprietary Tier A):**
Mid-Market Pricing Reality Check · Global PE Dry Powder · V4G House Valuation Anchors · Founder Hesitation Playbook · Buyer Conviction Signals · Vendor Loan Intelligence · Platform vs Add-On Decision Tree · Private vs Public Pricing Gap · Belux M&A Landscape · Why Deals Die

---

## Edge Function: grapevine-to-card v1.6

**URL:** `https://rirkgpsdcaxnowwmliof.supabase.co/functions/v1/grapevine-to-card`

| Route | Method | Purpose |
|-------|--------|---------|
| `/health` | GET | Version check |
| `/extract` | POST `{note_id}` | WHISPER→KC or KC enrich in-place |
| `/prescreen` | POST `{filename, text?, base64?}` | Batch pre-scan verdict + tags |
| `/enrich` | POST `{title, text}` | Batch KC enrichment + tags |
| `/tag` | POST `{note_id}` | Tag existing card with kb_tags |
| `/ingest` | POST `{note}` | Direct insert via service key |

---

## UI — index.html

| Tab | Shell | Status | Purpose |
|-----|-------|--------|---------|
| **Today** | S1 | 🔜 Sprint E | Editorial command deck. KPI strip · Lens presets · Signal feed · Pattern resurfacing · Mandate teaser (bridge). |
| **Grapevine / Curate** | S1 | ✅ Live | Draft/Active/Archived/◉ Candidates. Signal filter. Recency filter. Detail pane. |
| **Knowledge Base** | S1 | ✅ Live | 180 active KCs. Domain sections. Filters: Fit · Tier · Lens · Sector · Type. Active pills. |
| **Drop Point** | S1 | ✅ Live | Single + Batch Import. PDF.js. Storage upload. AI prescreen + enrichment. |
| **Briefing Studio** | S1 | 🔜 Sprint E | Replaces Intel Pulse. Thesis selector · Source picker · Claude API editorial angle · Output workspace. |

---

## Scripts

### dealflow_pipeline.py v1.16 (ticker-dealflow repo)
- 324 signals/run · 0 soft failures · 28 keywords · 21 RSS sources

### gs_nightly_enrich.py (golden-safe-repo)
- Enriches raw_signals → WHISPER_NOTE drafts · FR(N) = DIRECT

### intel_capture.py (golden-safe-repo)
- MARKET_WHISPER_SYSTEM + KNOWLEDGE_CARD_SYSTEM: Benelux + FR(N) explicit

### score_grapevine.py (golden-safe-repo)
- Newsworthiness scoring: FR(N) = DIRECT (equal to BE/NL/LU)

---

## Newsworthiness scoring

| Criterion | Weight |
|-----------|--------|
| Deal specificity (named parties) | 25% |
| Regional relevance BE/NL/LU/FR(N) = DIRECT | 25% |
| Mid-market fit €5M–€50M | 20% |
| Recency signal | 15% |
| Source quality | 15% |

Score ≥ 8 → auto-flag `pattern_candidate = true`

---

## RLS policies

| Policy | Role | Cmd | Rule |
|--------|------|-----|------|
| `gn_service_all` | service_role | ALL | Full access |
| `gn_anon_insert` | anon | INSERT | drafts only |
| `gn_anon_select` | anon | SELECT | blocks INTERNALONLY + RESTRICTED |
| `gn_anon_update` | anon | UPDATE | allows soft-delete |

---

## Active files — upload ALL to Claude Project

| File | Version | Role |
|------|---------|------|
| `Grapevine_Project_Summary.md` (this) | **v2.4** | Session starter — always load first |
| `Grapevine_Briefing_v2_2.md` | v2.2 | Full context reference |
| `Grapevine_Functional_Spec_v2_2.docx` | v2.2 | Frozen spec |
| `Grapevine_Changelog_v2_4.md` | **v2.4** | All deltas since spec freeze |
| `Grapevine_Taxonomy_v1_2_FINAL.xlsx` | v1.2→v1.3 | Taxonomy reference |
| `shell_map_v1_0_final.md` | v1.0 | **Architecture baseline — Shell definitions** |
| `backbone_object_map_v1_0.md` | v1.0 | **Architecture baseline — Canonical objects** |
| `cross_shell_routing_map_v1_0_final.md` | v1.0 | **Architecture baseline — Routing rules** |
| `vocabulary_lock_v1_0.md` | v1.0 | **Architecture baseline — Copy governance** |
| `roadmap_by_shell_v1_0_final.md` | v1.0 | **Architecture baseline — Build sequence** |
| `index.html` | Live | Production UI |
| `intel_capture.py` | v1.1+ | Backend enrichment |
| `score_grapevine.py` | v1.1+ | Batch scoring |

## Obsolete — do not reference
`Grapevine_Briefing_v2_1.md` · `Grapevine_Project_Summary_v2_1.md` · `grapevine_phase1.html` · `Grapevine_Project_Summary_v2_3.md`

---

*V4G — Ventures4Growth, Ghent · Dealflow.News · Confidential · April 2026*
