# Grapevine Changelog v2.4
**V4G — Ventures4Growth | 16 April 2026 | Confidential**
**Deltas since Functional Spec v2.2 freeze**

---

## v2.4 — Architecture baseline adopted (16 April 2026)

### New: Three-Shell Architecture — APPROVED

Five companion documents approved and adopted as the permanent architecture baseline for Grapevine:

| Document | Version | Role |
|----------|---------|------|
| `shell_map_v1_0_final.md` | v1.0 | Defines three shells and their missions |
| `backbone_object_map_v1_0.md` | v1.0 | Canonical objects, ownership, write rights |
| `cross_shell_routing_map_v1_0_final.md` | v1.0 | How objects move between shells |
| `vocabulary_lock_v1_0.md` | v1.0 | Shell-specific copy and label governance |
| `roadmap_by_shell_v1_0_final.md` | v1.0 | Build sequence per shell |

**Core principle locked:** One intelligence backbone, three shells, three vocabularies, three jobs-to-be-done.

| Shell | Label | Status |
|-------|-------|--------|
| S1 — Editor Workbench | Active build track | Sprint E in progress |
| S2 — Mandate Workspace | Next | Sprint G+ |
| S3 — View Layer | Later | Gate: Briefing Studio producing real output |
| BB — Shared backbone | Ongoing | Schema, RLS, routing metadata |

---

### New: Canonical Object Mapping

DB objects mapped to architecture-canonical names. No schema change required.

| Canonical name | DB equivalent |
|----------------|--------------|
| `signal` | `grapevine_notes` where `note_type = 'WHISPER_NOTE'` (pre-editorial) |
| `intel_note` | `grapevine_notes` where `note_type = 'WHISPER_NOTE'` (curated/active) |
| `knowledge_card` | `grapevine_notes` where `note_type = 'KNOWLEDGE_CARD'` |
| `pattern` | Records with `structured_data.pattern_candidate = true` (Sprint F: own state) |
| `mandate` | Hardcoded JS array in `index.html` (Sprint G → DB) |
| `mandate_match` | Not yet modelled → Sprint G |
| `briefing_collection` | Sprint E: textarea output · Sprint F: persisted KC |
| `editorial_cue` | Not yet modelled → Sprint F schema |

---

### New: Vocabulary Lock applied to S1

Shell 1 editorial production language locked. Applies to all UI copy, labels, buttons, and empty states from this point forward.

- **Approved S1 labels:** Today · Curate · Knowledge Base · Drop Point · Briefing Studio
- **Approved S1 verbs:** review · enrich · promote · extract · archive · route · verify · link · draft
- **Banned in S1:** contact-ready · next action needed · passive consumer language
- **S2 vocabulary must not bleed into S1:** relevant · watch · priority · mandate brief · brief pack
- **One-screen rule:** S1 editorial jargon and S2 execution language must not appear together on the same screen without explicit architectural justification

---

### Superseded: Architecture Lock v1.0.2 — Mandate Radar section

The Architecture Lock v1.0.2 planned **Mandate Radar** as a Sprint E standalone tab with its own schema.

**This section is superseded by Shell Map v1.0 (16 April 2026).**

Rationale: Mandate Radar as a standalone tab inside S1 would have grown into a half-mandate shell inside the Workbench, violating the shell separation principle. The Shell Map correctly categorises full mandate execution as S2 territory.

**Resolution:**
- Mandate Radar tab: cancelled
- Mandate matching logic: deferred to S2 — Mandate Workspace (Sprint G+)
- Replacement in S1: lightweight **Mandate teaser card** at the bottom of Today — bridge surface only, read-only, hardcoded JS array, no edit rights, no mandate execution vocabulary

All other sections of Architecture Lock v1.0.2 remain valid.

---

### Updated: Sprint E scope confirmed and locked

Sprint E scope formally confirmed against Roadmap by Shell v1.0, Phase S1-C. No changes from pre-architecture-baseline Sprint E plan — full alignment confirmed.

Build order: E.1–E.6 (Today) → E.7–E.9 (Briefing Studio). Total ~6 hours.

Hard constraints:
- S1 only
- No new Supabase schema
- No nav layout rewrite
- Mandate teaser = hardcoded JS array, bridge only
- Briefing Studio output = textarea (no persistence until Sprint F)
- `editorial_cue` schema = Sprint F

---

### Updated: Phase roadmap restructured by shell

Phase roadmap in Project Summary now structured as S1 → S2 → S3 tracks instead of Phase 1/2/3 language. Milestones:

| Milestone | Outcome | Status |
|-----------|---------|--------|
| M1 | Architecture baseline approved | ✅ Done |
| M2 | Shell 1 interaction foundation stable | ✅ Done (wireframe + spec) |
| M3 | Sprint E delivered — usable S1 MVP | 🔜 Next |
| M4 | Shell 1 hardened (Sprint F) | Planned |
| M5 | Mandate schema groundwork (Sprint G) | Planned |
| M6 | S2 Mandate Workspace v0.1 | Planned |
| M7 | S3 View Layer concept + cue loop | Later |
| M8 | Reader-safe surfaces launched | Later |

---

### Updated: Active files list

Five new architecture baseline documents added to the Claude Project upload list. These are permanent session context documents alongside the Project Summary.

---

## v2.3 — Sprint D/E completed (16 April 2026)

*(See Grapevine_Changelog_v2_3.md for full v2.3 delta — Edge Function v1.6, Taxonomy v1.3, KB 180 KCs, Batch Import, FR(N) scope, Framework KCs ingested)*

---

*V4G — Ventures4Growth, Ghent · Dealflow.News · Confidential · April 2026*
