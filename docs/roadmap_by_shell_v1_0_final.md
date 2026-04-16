# Roadmap by Shell v1.0

## Status
Architecture planning baseline: APPROVED
Version: 1.0 — 16 April 2026
Companion to: Shell Map v1.0, Backbone Object Map v1.0, Cross-Shell Routing Map v1.0, Vocabulary Lock v1.0
Applies to: product backlog, sprint planning, build sequencing, feature gating, schema decisions, resourcing, design scoping
Not to be reopened without version bump to v1.1+

## Purpose

This document translates the three-shell architecture into a sequenced build roadmap.

It exists to prevent roadmap drift. The platform should no longer be planned as one expanding app with an undifferentiated feature backlog. It should be planned as **three shells on one backbone**, each with its own sequencing, readiness criteria, and operating goals.

The roadmap is structured by shell first, then by phase, then by deliverable.

---

## Core planning rule

**Build the shells in the order in which they create leverage.**

1. **Shell 1 — Editor Workbench** comes first because it creates the governed intelligence corpus.
2. **Shell 2 — Mandate Workspace** comes second because it converts that intelligence into commercial advantage.
3. **Shell 3 — View Layer** comes third because it exposes curated output safely and closes the lightweight feedback loop.

Without Shell 1, Shell 2 has weak inputs.
Without Shell 1 and Shell 2 discipline, Shell 3 becomes a premature surface without enough trustworthy substance.

---

## Executive roadmap overview

| Shell | Role in sequence | Why now / later | Current status | Primary objective |
|---|---|---|---|---|
| Editor Workbench | First build track | Creates corpus, workflows, governance, routing, and packaging foundation | Active build track | Production-grade editorial operating shell |
| Mandate Workspace | Second build track | Depends on stable editorial objects and routing into mandate context | Next design/build track | Intelligence-to-mandate application shell |
| View Layer | Third build track | Depends on stable packaging, filtering, and safe read surfaces | Later track | Reader-safe consumption shell with lightweight cue loop |

---

## Track 1 — Editor Workbench

### Strategic objective
Make Grapevine a production-grade editorial operating shell where a single editor can run the full intelligence cycle: ingest → curate → connect → pattern → package → brief.

### What success looks like
- Raw intake becomes governed editorial objects consistently
- Editors can move from signal to note to card/pattern to briefing without shell confusion
- Today works as a true editorial command deck, not a decorative dashboard
- Packaging and routing are stable enough to feed Shell 2 and Shell 3

### Shell 1 scope
- Today
- Curate
- Knowledge Base
- Drop Point
- Briefing Studio

---

### Phase S1-A — Architecture consolidation

**Goal**: Lock the architecture, object model, routing, and vocabulary before scaling feature work.

**Deliverables**
- Shell Map v1.0
- Backbone Object Map v1.0
- Cross-Shell Routing Map v1.0
- Vocabulary Lock v1.0
- Roadmap by Shell v1.0

**Status**: COMPLETED

**Exit criteria**
- Shell ownership is explicit
- Object ownership is explicit
- Routing rules are explicit
- Language policy is explicit
- Roadmap is shell-structured

---

### Phase S1-B — Workbench interaction foundation

**Goal**: Stabilise the operator-grade interaction model of the Workbench.

**Deliverables**
- Grapevine Today wireframe
- Interaction spec
- Annotated wireframe
- Component spec
- Shell-specific interaction rules

**Status**: In progress / foundational design layer created

**Exit criteria**
- Today has clear inline vs drawer vs deep-page rules
- Component hierarchy is stable enough for implementation
- Workbench is explicitly labelled Shell 1 only

---

### Phase S1-C — Sprint E: Workbench MVP delivery

**Goal**: Ship the first usable Editor Workbench surface as a real operating shell.

**Theme**: Today as editorial command deck + Briefing Studio as first output surface

| Step | What | File | Effort | Outcome |
|---|---|---|---|---|
| E.1 | Add Today nav entry + tab shell | index.html | 15 min | Shell 1 landing surface exists |
| E.2 | KPI strip (5 live counts via Supabase SELECT) | index.html | 30 min | Daily editorial pulse |
| E.3 | Lens preset pills (static array → filter signal feed) | index.html | 45 min | Theme-based filtering, no DB migration |
| E.4 | Signal feed in Today (reuse Curate list logic, filtered) | index.html | 30 min | Filtered editorial feed inside Today |
| E.5 | Pattern resurfacing card (group by domain, count ≥ 3) | index.html | 45 min | Convergence visibility |
| E.6 | Mandate teaser card (hardcoded array + domain match) | index.html | 30 min | Bridge awareness — teaser only |
| E.7 | Rename Intel Pulse → Briefing Studio, enable nav | index.html | 10 min | Tab structure complete |
| E.8 | Briefing Studio thesis selector + source picker | index.html | 60 min | Editorial source assembly |
| E.9 | Claude API editorial angle call + output workspace | index.html | 60 min | First publishable draft from Workbench |

**Total estimated effort**: ~6 hours clean build
**Build order**: E.1–E.6 Today first, then E.7–E.9 Briefing Studio

**KPIs for E.2**: New this week · Signals needing review · Avg score · Tier A KCs · Promoted today
**Lens presets for E.3**: Distress · Succession · PE Entry · Growth Signal · Asset Sale · Founder Exit
**Nav position**: Today as first tab above Curate

**Today tab anatomy**
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
│  MANDATE TEASER  (bottom card — teaser only)        │
└─────────────────────────────────────────────────────┘
```

**Sprint E architectural constraints**
- Shell 1 only — no mandate execution workflow
- No new Supabase schema additions
- No nav layout rewrite
- Mandate teaser reads from hardcoded JS array
- Briefing Studio output lives in textarea (copy/paste) — no persistence yet

**What is explicitly out of Sprint E**
- Full Mandate Workspace
- Lens preset persistence (Sprint F)
- Briefing Studio output persistence (Sprint F)
- editorial_cue schema (Sprint F)
- Public View Layer

**Exit criteria**
- Editors can ingest, triage, draft, review, and retrieve intelligence in one coherent shell
- Today works as an operator command deck
- Curate and Knowledge Base are operational for real use
- Briefing Studio produces a first draft from thesis + source selection

---

### Phase S1-D — Sprint F: Workbench hardening

**Goal**: Make Shell 1 reliable enough to act as the canonical production shell and lay the groundwork for Shell 2 and Shell 3 objects.

**Planned scope**
- Lens preset persistence (user_presets table — first Supabase migration)
- Briefing Studio output persistence (save as briefing_pack KC)
- editorial_cue object schema (forward-compatible bridge for Shell 3)
- Workbench editorial_cue review queue stub
- Pattern candidate confirmation flow
- Evidence completeness queue improvements
- Better state handling, empty states, and failure states
- Queue and review ergonomics

**Sprint F architectural constraint**: Shell 1 core + editorial_cue schema as a forward-compatible object. No Shell 3 UX yet.

**Exit criteria**
- Cards and patterns have stable editorial lifecycle
- Evidence and review bottlenecks are visible and manageable
- Workbench is ready to feed Shell 2 meaningfully
- editorial_cue object exists in schema

---

### Phase S1-E — Sprint G: Shell 1 to Shell 2 bridge

**Goal**: Lay mandate object foundation and prepare Workbench-to-Mandate handoff.

**Planned scope**
- mandate and mandate_match schema (Supabase migration)
- Replace hardcoded mandate JS array with DB-backed mandate objects
- Workbench Today mandate teaser reads from DB
- mandate_match suggestion flow from Workbench (suggestion only, not full Shell 2)
- Resolve Routing Map OD1: mandate_match created directly or via pre-match suggestion object

**Sprint G architectural constraint**: Mandate schema lives in backbone. Mandate UX remains a teaser in Shell 1. Full Shell 2 surface begins in Sprint H / Sprint 2.1.

---

### Phase S1-F — Briefing Studio full delivery

**Goal**: Create the first complete packaging layer inside Shell 1.

**Planned scope**
- Briefing collections with audience-aware packaging
- Editorial angle assembly
- Routing toward publishable outputs
- Stable enough Briefing Studio to unlock View Layer prerequisite gate

**Exit criteria**
- Workbench can produce coherent packaged outputs consistently
- Packaging is governed and routed, not ad hoc
- Prerequisite gate for Shell 3 is met

---

## Track 2 — Mandate Workspace

### Strategic objective
Build a dedicated commercial application shell where the V4G deal team can apply intelligence to live mandates without needing to understand the editorial operating model behind it.

### What success looks like
- Deal teams see relevance, priority, and next move clearly
- Mandate usefulness is stored in `mandate_match`, not smuggled into editorial objects
- The shell feels calmer and narrower than the Workbench
- It becomes the home of commercial action, not a tab inside Today

### Shell 2 scope
- Mandate selector
- Thesis panel
- Match feed
- Action board
- Brief pack
- Mandate-side routing and feedback logic

---

### Phase S2-A — Mandate Workspace definition

**Goal**: Turn Mandate Radar from bridge concept into proper shell design.

**Deliverables**
- Mandate Workspace concept note
- Mandate-side wireframe
- Interaction model
- Shell-specific vocabulary review
- Object usage validation against `mandate` and `mandate_match`

**Status**: Next track

**Exit criteria**
- Mandate Workspace is no longer treated as a Workbench tab extension
- Core anatomy is stable
- Bridge vs true shell boundary is explicit

---

### Phase S2-B — Mandate Workspace v0.1: matching core (Sprint H / Sprint 2.1)

**Goal**: Minimal viable mandate execution surface.

**Planned scope**
- Mandate selector (reads mandate objects from DB)
- Thesis panel (mandate intent, search rails, lens filters)
- Match feed (filtered notes, cards, patterns relevant to active mandate)
- Basic action states: relevant / watch / priority / dismissed
- Output as copy/export only — no brief pack yet

**Architectural constraint**: New shell — do not extend Today or Curate for mandate execution. Separate nav entry or dedicated route.
**Vocabulary constraint**: Use Mandate Workspace vocabulary only. No draft, promote, enrich, extract, archived in this shell.

**Exit criteria**
- Mandate relevance can be managed without editing editorial truth
- Workbench teaser and shell handoff are working coherently

---

### Phase S2-C — Mandate Workspace v0.2: action and output (Sprint 2.2+)

**Planned scope**
- Action board (next moves, follow-ups, blockers, contact-readiness states)
- Brief pack (mandate-facing output assembly)
- Mandate-to-Workbench feedback handoff object
- Mandate history and reviewed-for-mandate tracking

**Exit criteria**
- Shell supports live mandate use, not just relevance browsing
- User can move from intelligence to action cleanly

---

## Track 3 — View Layer

### Strategic objective
Build a reader-safe consumption shell that exposes selected intelligence clearly and closes the loop through lightweight editorial cues — without leaking any Workbench operator mechanics.

### What success looks like
- Readers trust what they see
- The shell feels curated, not operational
- No Workbench jargon leaks through
- Reader feedback improves coverage without polluting the corpus

### Shell 3 scope
- Today / Briefings read surface
- Signals read surface
- Knowledge read surface
- Optional watchlist or mandate snapshots
- Editorial cue composer

### Prerequisite gate before Sprint 3.1
- Briefing Studio producing at least weekly publishable output
- editorial_cue schema live in Supabase
- audience_profile logic implemented

---

### Phase S3-A — View Layer framing

**Goal**: Define the reader shell as its own product, not as a cleaned-up Grapevine clone.

**Deliverables**
- View Layer concept note
- Homepage naming decision (leaning: **Briefings** over **Today** for the reader shell)
- Shell-specific wireframe
- Cue composer UX
- Audience-safe content selection logic

**Exit criteria**
- View Layer mental model is distinct from Workbench
- Cue mechanism is explicit and bounded
- Shell 3 vocabulary is locked

---

### Phase S3-B — Reader-safe surfaces (Sprint 3.1)

**Goal**: Expose curated content safely.

**Planned scope**
- Briefings read surface (published briefing_collection objects)
- Signals read (selected intel_note subset, audience-safe)
- Knowledge read (selected knowledge_card subset)
- Shell-appropriate empty states and copy
- Simplified filtering and exploration

**Architectural constraint**: No operator vocabulary. No Workbench states or queues. Read only.

**Exit criteria**
- Selected output can be consumed safely without operator confusion
- Shell vocabulary is consistently reader-safe

---

### Phase S3-C — Editorial cue loop (Sprint 3.2)

**Goal**: Complete the lightweight feedback loop from View Layer into editorial production.

**Planned scope**
- "Help us cover this better" CTA
- Micro composer with three prompt types:
  - Question — What should we look at next?
  - Angle — What angle is underexplored?
  - Usefulness — Who would care about this?
- editorial_cue creation flow
- Workbench review queue integration
- Optional cue submission history for reader

**Architectural constraint**: editorial_cue is a queue object, not a shortcut around curation. No cue bypasses Workbench review.

**Exit criteria**
- Reader feedback enters the system safely
- Cues can be routed back into research, briefing, or mandate context
- No cue creates a note automatically

---

### Phase S3-D — View Layer depth (Sprint 3.3+)

**Planned scope**
- Thematic following (sector, lens, pattern subscriptions)
- Optional watchlist snapshots (reader-safe mandate summaries)
- Bilingual surface consideration (NL / FR / EN)
- Partner-accessible view with authentication and access tiers

---

## Backlog governance rules

| Rule | Statement |
|---|---|
| Rule 1 | Every backlog ticket belongs to Shell 1, Shell 2, Shell 3, or Shared backbone. Cross-shell tickets must be split before entering a sprint. |
| Rule 2 | Shell 1 tickets must not introduce Shell 2 execution logic. Teasers allowed. Mandate execution workflow is not. |
| Rule 3 | Shell 2 tickets must not import editorial state management. Consuming editorial objects is allowed. Rewriting them is not. |
| Rule 4 | Shell 3 tickets must not expose operator mechanics. Read and editorial_cue creation only. |
| Rule 5 | New Supabase tables must map to a canonical object in the Backbone Object Map. Ad hoc shadow tables require explicit justification. |
| Rule 6 | Vocabulary must be checked against the Vocabulary Lock before any copy finalization. |
| Rule 7 | The Shared backbone bucket must stay smaller than the shell buckets. If it grows too large, the roadmap is drifting toward "one app" thinking. |

### Backlog bucket labels
- **S1** — Editor Workbench
- **S2** — Mandate Workspace
- **S3** — View Layer
- **BB** — Shared backbone (schema, RLS, routing metadata, object lineage only)

---

## Milestone map

| Milestone | Outcome |
|---|---|
| M1 | Architecture consolidation set approved ✅ |
| M2 | Shell 1 interaction and component foundation stable |
| M3 | Sprint E delivered — usable Shell 1 MVP |
| M4 | Shell 1 hardened enough to feed other shells |
| M5 | Mandate Workspace v0.1 defined and scoped |
| M6 | Mandate Workspace matching core live |
| M7 | View Layer concept and cue loop designed |
| M8 | Reader-safe surfaces and cue workflow launched |

---

## Immediate next actions

1. **Ship Sprint E** as a Shell 1-only deliverable — ~6 hours, E.1–E.9 as specified above
2. **Plan Sprint F** — editorial_cue schema + governance depth
3. **Scope Sprint G** — mandate schema groundwork, not full Shell 2 yet
4. **Tag existing backlog items** by shell (S1 / S2 / S3 / BB)
5. **Do not begin Shell 3 UX** until Briefing Studio is producing real publishable output

---

## Open decisions for v1.1

1. Should Mandate Workspace v0.1 be a new tab in index.html or a separate file/route?
2. Should View Layer v0.1 be a separate deployment (subdomain) or an authenticated view mode within index.html?
3. Should editorial_cue creation require authentication or allow lightweight anonymous contribution with rate limiting?
4. Should Sprint G mandate schema include mandate_match directly or a lighter pre-match suggestion object first?
5. Should Shell 2 v0.1 begin with mandate_match only, or include action board from day one?
6. Should Shell 3 start with Briefings only, or include Signals and Knowledge simultaneously?
7. When is Briefing Studio considered "stable enough" to unlock the View Layer prerequisite gate?
8. Do we need explicit staffing/ownership per shell in the next roadmap version?
9. When does the Mandate Workspace transition from internal-only to partner-accessible?

---

## Decision statement

The V4G intelligence product roadmap is now locked to the shell architecture.

- **Shell 1 — Editor Workbench**: active, Sprint E in progress
- **Shell 2 — Mandate Workspace**: next, schema groundwork in Sprint G
- **Shell 3 — View Layer**: later, prerequisite is editorial corpus depth

From this point onward, sprint planning, feature gating, and schema decisions should be validated against this roadmap and the four companion architecture documents.
