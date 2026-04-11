# Grapevine Intelligence OS — Briefing v2.1
**Dealflow.News / V4G | April 2026 | Confidential**
**Supersedes: Grapevine_Briefing_v2.0.docx**

---

## 1. What Grapevine is

Grapevine is the editorial market intelligence OS for Dealflow.News / V4G. It is **not SaaS** — it is a content and institutional memory layer that:

- Captures and enriches raw Benelux lower mid-market M&A signals
- Curates and scores editorial notes (WHISPER_NOTE)
- Distils recurring patterns into reusable knowledge assets (KNOWLEDGE_CARD)
- Packages outputs for newsletter, briefing packs, and movers & shakers distribution

**One-liner:** From raw deal signal to mandate-activating knowledge asset — with governance, scoring, and editorial workflow.

---

## 2. Two-layer content architecture

```
Layer 1 — WHISPER_NOTE (internal)
├── Raw intel, enriched signals, market whispers
├── sensitivity: INTERNALONLY / TEAM
├── Never distributed directly
└── pattern_candidate=true → ready for extraction

Layer 2 — KNOWLEDGE_CARD (editorial asset)
├── Structural pattern distilled from whisper
├── Reusable across firms, broad dealflow audience
├── Audience set at Promote: internal → external_broad
└── source_ref_id → links back to source WHISPER_NOTE
```

### The Knowledge Guardian workflow
```
WHISPER_NOTE (nightly via intel_capture.py)
    ↓ analyst reviews in Curate
    ↓ Edit → ☑ Pattern Candidate
    ↓ fills: Pattern Name + Rationale + Editorial Angle
    ↓ ◉ Extract Card button
    ↓ grapevine-to-card Edge Function (Claude Sonnet)
KNOWLEDGE_CARD draft
    ↓ KB tab → review → Promote → audience
KNOWLEDGE_CARD active → Distribution
```

Two extraction paths:
- **Nightly automatic:** `intel_capture.py --to-card` (score ≥ 8 auto-flagged)
- **Manual on-demand:** ◉ Extract Card button in Curate UI → Edge Function

---

## 3. Pattern Library — four editorial layers

Every pattern candidate has four structured layers:

| Layer | Field | Description |
|-------|-------|-------------|
| **Decision** | `pattern_candidate` (bool) | Explicit flag: is this a structural pattern? |
| **Conceptual** | `pattern_name` | Short addressable label (max 12 words) |
| **Analytical** | `pattern_rationale` | Structural story: drivers, mechanism, time horizon |
| **Communication** | `editorial_angle` | How to frame it for the audience — the editorial anchor |

These four fields are the primary input to the KnowledgeCardExtractor prompt. Richer input → sharper card.

**Auto-flag logic in intel_capture.py:**
- Score ≥ 8 → `pattern_candidate=true`, `pattern_name=title`, `pattern_rationale=newsletter_angle`
- Score 6-7 → `pattern_candidate=false` (analyst can promote manually)
- After card creation → `pattern_candidate=false` (cleared automatically)

---

## 4. KnowledgeCardExtractor — prompt architecture

**System prompt:** Senior editorial intelligence editor at a Benelux M&A/dealflow platform. Audience: founders 55+, family offices, PE partners, notaries, boutique M&A lawyers. Goal: immediately useful in a real deal conversation.

**Four output questions:**
1. **CORE INSIGHT** — Structural pattern, why recurring now (2-3 sentences, present tense)
2. **DEAL IMPLICATION** — How should a deal professional change their approach (2-3 sentences, actionable)
3. **MISREAD RISK** — Most dangerous misinterpretation (1-2 sentences, direct)
4. **BEST USE** — 3-5 concrete use cases (founder opener, sector memo, CIM angle, etc.)

**Input to prompt:**
```
pattern_name, pattern_rationale, editorial_angle
title, summary, body_md excerpt (2000 chars)
```

**Note:** Cards are generic editorial assets — not V4G-internal. Audience = any Benelux deal professional. Internal V4G context lives in the WHISPER_NOTE, not the card.

---

## 5. Schema — canonical enum values

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

### structured_data JSONB fields

**Scoring:**
```
newsworthiness_score          integer 1-10
newsworthiness_rationale      text
newsletter_angle              text
```

**Pattern Library:**
```
pattern_candidate             boolean
pattern_name                  text (max 12 words)
pattern_rationale             text (structural story)
editorial_angle               text (communication layer)
```

**KNOWLEDGE_CARD output:**
```
core_insight                  text
deal_implication              text
misread_risk                  text
best_use                      text[]
source_pattern_name           text
source_pattern_rationale      text
source_whisper_note_id        uuid
```

**WHISPER_NOTE metadata:**
```
fact_table                    text (markdown table)
source_box                    text
what_we_know                  text
what_we_dont_know             text
source_language               text (nl/fr/en)
initial_signal_type           text
initial_confidence            numeric
analyst_lens                  text
```

---

## 6. UI — index.html

Hosted at `https://grapevine.dealflow.news` (GitHub Pages, repo: `dealflow-news/grapevine`).

### Curate tab
- Status bar: **Drafts · Active · Archived · ◉ Candidates**
- Candidates tab: all notes with `pattern_candidate=true`, shows pattern_name badge + "Card exists" if already extracted
- Detail panel footer (sticky, always visible):
  - Draft: `↑ Promote · ◉ Extract Card (if candidate) · ✎ Edit · Archive · 🗑`
  - Active: `✓ Active · ◉ Extract Card (if candidate) · ✎ Edit · Archive`
  - Archived: `Archived · 🗑`
- Edit mode fields: Title · Summary · Audience · Sensitivity · Sector · Confidence + Pattern Candidate section
- Delete: custom modal (not browser confirm), soft-delete via `is_deleted=true`

### Knowledge Base tab
- Default: active KNOWLEDGE_CARDs only
- Toggles: `☐ Show drafts` (replaces active view) · `☐ Include archived`
- Layout: 420px card list left · flex:1 detail right
- Detail footer: Promote · Edit · Archive (drafts) / Edit · Archive (active)
- Sections: Core Insight (teal block) · Deal Implication · ⚠ Misread Risk (gold block) · Best Use (pills)

### Light/Dark mode
Segmented control `☀ Light` / `🌙 Dark` — bottom of sidebar. Persisted in localStorage.

---

## 7. Backend — intel_capture.py v1.1

```bash
python intel_capture.py                              # nightly run (limit=10)
python intel_capture.py --limit=25                   # larger batch
python intel_capture.py --dry-run --limit=3          # preview only
python intel_capture.py --mi-id=<uuid>               # single re-enrich
python intel_capture.py --to-card=<note_id>          # extract KNOWLEDGE_CARD
python intel_capture.py --to-card=<note_id> --dry-run
```

**`--to-card` flow:**
1. Fetch WHISPER_NOTE (must have `pattern_candidate=true`)
2. Call KnowledgeCardExtractor (Claude Sonnet, 800 tokens)
3. Write KNOWLEDGE_CARD draft (`capture_origin=whisper_report`)
4. Clear `pattern_candidate=false` on source note

**Auto-flag in nightly run:**
After scoring, if score ≥ 8 and not already flagged:
```python
structured_data['pattern_candidate'] = True
structured_data['pattern_name'] = title[:120]
structured_data['pattern_rationale'] = newsletter_angle[:400]
```

---

## 8. Edge Function — grapevine-to-card v1.0

```
POST /functions/v1/grapevine-to-card/extract
Authorization: Bearer <anon_key>
{ "note_id": "uuid" }
```

**Response (success):**
```json
{ "ok": true, "note_id": "uuid", "title": "...", "status": "draft", "duplicate": false }
```

**Response (duplicate):**
```json
{ "ok": true, "note_id": "uuid", "title": "...", "duplicate": true }
```

**Guards:**
- `note_type === 'WHISPER_NOTE'`
- `pattern_candidate === true`
- Duplicate check: `source_ref_id=noteId AND note_type=KNOWLEDGE_CARD AND is_deleted=false`

**Secrets required:** `ANTHROPIC_API_KEY` · `SUPABASE_URL` · `SUPABASE_SERVICE_ROLE_KEY`

---

## 9. RLS — current policies

| Policy | Role | Cmd | USING | WITH CHECK |
|--------|------|-----|-------|------------|
| `gn_service_all` | service_role | ALL | true | true |
| `gn_anon_insert` | anon | INSERT | — | status=draft AND is_deleted=false |
| `gn_anon_select` | anon | SELECT | sensitivity NOT IN (INTERNALONLY, RESTRICTED) | — |
| `gn_anon_update` | anon | UPDATE | true | true |

**Note:** `gn_anon_update` WITH CHECK=true required for soft-delete (setting `is_deleted=true` would otherwise be blocked by the previous `is_deleted=false` check).

---

## 10. Newsworthiness scoring

**Model:** Claude Haiku (fast, cheap — simple classification)

| Criterion | Weight |
|-----------|--------|
| Deal specificity (named parties) | 25% |
| Benelux relevance (BE/LU > NL > FR) | 25% |
| Mid-market fit €5M–€500M | 20% |
| Recency signal | 15% |
| Source quality | 15% |

**Output fields:** `newsworthiness_score` (1-10) · `newsworthiness_rationale` · `newsletter_angle`

**Pattern candidate threshold:** score ≥ 8 → auto-flag

---

## 11. Deployment

| Component | URL / Location |
|-----------|---------------|
| Grapevine UI | `https://grapevine.dealflow.news` |
| GitHub repo | `github.com/dealflow-news/grapevine` |
| Edge Function | `https://rirkgpsdcaxnowwmliof.supabase.co/functions/v1/grapevine-to-card` |
| Supabase | `https://rirkgpsdcaxnowwmliof.supabase.co` |
| intel_capture.py | Windows Task Scheduler · 03:00 daily |

---

## 12. Phase roadmap

### Phase 1 ✅ Completed
Core UI · intel_capture.py · scoring · soft delete · pattern flag · deployment

### Phase 2 Sprint 1 ✅ Completed (10 April 2026)
- `--to-card` CLI
- `grapevine-to-card` Edge Function
- ◉ Extract Card UI button
- Pattern Library (4 layers)
- Auto-flag (score ≥ 8)
- ◉ Candidates tab
- KB sticky footer + Edit mode
- Light/dark mode (editorial palette)
- `grapevine.dealflow.news` live

### Phase 2 — Remaining
- Linker engine (link_pending → linked)
- Newsletter digest generator
- Windows Task Scheduler setup for intel_capture.py

### Phase 3 — Planned
- Auth (Supabase auth or Cloudflare Access)
- Client-facing KB (filtered by visibility_scope)
- NL/FR translation pipeline
- Collections → briefing packs
- Intel Pulse tab activation

---

## 13. Active files — upload to Claude Project

| File | Version | Role |
|------|---------|------|
| `Grapevine_Project_Summary.md` | v2.1 | Session starter — upload first |
| `Grapevine_Briefing_v2.1.md` (this) | v2.1 | Full context reference |
| `Grapevine_Functional_Spec_v2.2.docx` | Frozen | Primary spec — do not reopen without version bump |
| `index.html` | Live | Production UI |
| `intel_capture.py` | v1.1 | Nightly enrichment + --to-card |
| `score_grapevine.py` | v1.1 | Batch scoring |
| `grapevine_addons.sql` | Applied | Schema addons |

## Obsolete — do not reference
`Grapevine_Briefing_v2.0.docx` · `grapevine_phase1.html` · All pre-v2.1 summaries.

---

*Dealflow.News / V4G · Confidential · April 2026*
