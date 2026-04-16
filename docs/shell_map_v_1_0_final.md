# Shell Map v1.0

## Status
Architecture direction: APPROVED
Version: 1.0 - 16 April 2026
Applies to: product, UX, data model, routing, backlog, vocabulary
Not to be reopened without version bump to v1.1+

## Purpose
This document defines the three-shell product architecture for the V4G intelligence stack.

It exists to prevent the platform from collapsing into one overloaded interface. The platform should be built as **one intelligence backbone, three shells**, each with a distinct job-to-be-done, vocabulary, and operating model.

It also establishes that lightweight reader feedback remains separate from editorial production through a dedicated object such as `editorial_cue`, rather than entering the signal or note corpus directly.

## Core principle
The shells are **not permission variants of the same UI**. They are different working environments over a shared intelligence backbone.

- **Shell 1 - Editor Workbench** creates, curates, enriches, connects, and packages intelligence.
- **Shell 2 - Mandate Workspace** applies intelligence to live mandates and commercial execution.
- **Shell 3 - View Layer** lets non-operators read, follow, and lightly guide future coverage.

The feedback loop from Shell 3 back into Shell 1 happens only through a lightweight cue mechanism, not through direct note creation or editorial mutation.

---

## 1. Executive shell overview

| Shell | Mission | Primary mode | Owns | Explicitly excludes |
|---|---|---|---|---|
| Editor Workbench | Turn raw inputs into structured, reusable intelligence | Editorial production | Today, Curate, Knowledge Base, Drop Point, Briefing Studio | Mandate execution, reader-safe consumption surface |
| Mandate Workspace | Turn intelligence into mandate advantage | Commercial application | Mandate selector, thesis panel, match feed, action board, brief pack | Ingest, raw editorial triage, promote/archive/extract flows |
| View Layer | Deliver curated intelligence safely to non-operators | Consumption with light feedback | Today / Briefings read surface, Signals read, Knowledge read, optional watchlist snapshots, editorial cue composer | Ingest, editing, promote, archive, operator vocabulary |

---

## 2. Shell 1 - Editor Workbench

### Mission
The Editor Workbench is the production environment where raw material becomes structured, governed, reusable intelligence.

### Primary users
- Intelligence editors
- Analysts
- Research operators
- Internal writers
- Governance / quality users

### Main jobs
- Ingest new material from URL, file, manual, or batch input
- Review and assess candidate signals and notes
- Enrich, connect, and prioritize intelligence objects
- Surface convergence and pattern candidates
- Maintain reusable memory through cards and knowledge objects
- Package output for briefings, newsletter drafting, and editorial reuse

### Owns
- **Today** - editorial command deck
- **Curate** - evidence review, promote, refine, and connect
- **Knowledge Base** - reusable memory and library-grade intelligence
- **Drop Point** - deliberate intake and ingestion
- **Briefing Studio** - output generation and audience-aware editorial packaging

### Explicitly excludes
- Deep mandate execution workflow
- Mandate action tracking as a primary operating model
- Reader-safe passive consumption surfaces
- Simplified partner/client reading mode inside the same shell

### Interaction model
- Dense, operator-grade, evidence-visible
- Optimized for decision speed and editorial control
- May use drawers, queues, multi-step flows, and explicit governance states
- May expose operator concepts such as draft, active, archived, candidate, extract, enrich, promote

### Vocabulary - allowed
- draft
- active
- archived
- candidate
- enrich
- extract
- promote
- evidence
- provenance
- review
- pattern candidate

### Vocabulary - avoid
- contact-ready
- next action needed
- simplified reader language that hides operator intent when precision matters

### Success test
This shell is successful if an editor can move from raw input to governed, reusable intelligence with speed, confidence, and visible provenance.

---

## 3. Shell 2 - Mandate Workspace

### Mission
The Mandate Workspace is the application environment where intelligence is translated into mandate advantage, outreach logic, and next commercial action.

### Primary users
- V4G deal team
- Mandate owners
- Partners steering assignments
- Internal execution and commercial roles

### Main jobs
- Define or refine mandate thesis and search rails
- Review which intelligence items matter to a specific mandate
- Turn patterns and signals into target hypotheses and outreach thinking
- Prepare mandate briefs, talking points, and worklists
- Track what intelligence has already informed a mandate
- Identify missing information that blocks mandate progress

### Owns
- **Mandate selector** - active mandate context chooser
- **Thesis panel** - search rails, intent, and interpretation lens
- **Match feed** - relevant subset of notes, cards, and patterns
- **Action board** - next moves, targets, follow-ups, blockers
- **Brief pack** - reusable mandate-facing output

### Explicitly excludes
- Ingest and intake workflows
- Raw editorial triage
- Promote / archive / enrich / extract mechanics
- Workbench-heavy classification controls
- Reader-safe public or partner consumption surface

### Interaction model
- Narrower, calmer, more actionable than the Workbench
- Focused on relevance, timing, and next move
- Shows why something matters to a mandate, not why it matters editorially in general
- Uses execution states rather than editorial states

### Vocabulary - allowed
- relevant
- watch
- priority
- contact-ready
- next action
- target hypothesis
- thesis fit
- mandate brief
- blocker
- follow-up

### Vocabulary - avoid
- draft
- archived
- promote
- extract
- ingest
- candidate as editorial process language

### Success test
This shell is successful if a deal team can convert intelligence into mandate action without needing to understand the editorial operating model behind it.

---

## 4. Shell 3 - View Layer

### Mission
The View Layer is the read-mostly environment where non-operators can follow curated intelligence safely, clearly, and with minimal cognitive load.

### Primary users
- Partners who want awareness without workbench complexity
- Internal readers outside the editor team
- Selected clients or ecosystem participants in later phases
- Readers of briefings, patterns, and curated signals

### Main jobs
- Monitor current themes and notable signals
- Read selected intelligence safely
- Understand why an item matters and to whom it matters
- Follow sectors, patterns, lenses, or mandates at a high level
- Lightly shape future coverage through one small contribution mechanism

### Owns
- **Today / Briefings read surface** - curated daily and periodic reading experience
- **Signals read** - selected stream, not operator queue
- **Knowledge read** - clean card library subset
- **Optional watchlist or mandate snapshots** - reader-safe summaries only
- **Editorial cue composer** - one lightweight write affordance

### Explicitly excludes
- Ingest
- Editing
- Promote / archive / extract actions
- Deep classification controls
- Operator queues and workbench process states
- Full mandate execution tools

### Interaction model
- Read-mostly, clean, confidence-building
- Minimal operational risk
- One lightweight contribution loop only
- Should feel curated, not unfinished or operator-facing

### Vocabulary - allowed
- why it matters
- themes
- briefings
- what to watch
- who cares
- question
- angle
- usefulness

### Vocabulary - avoid
- draft
- archived
- ingest
- promote
- extract
- evidence-type jargon
- taxonomy and classification burden on the reader

### Write affordance - the only input allowed
The View Layer has exactly one write affordance.
A single button - labelled **"Help us cover this better"** or similar - opens a micro composer with three prompt types:

| Prompt | Core question | Purpose |
|---|---|---|
| Question | What should we look at next? | Feeds future research agenda |
| Angle | What angle is underexplored? | Improves Briefing Studio inputs |
| Usefulness | Who would care about this? | Surfaces audience fit and distribution logic |

Submissions create an `editorial_cue` object - never a note, never a whisper.
The `editorial_cue` fields are: `cue_id`, `source_item_id`, `cue_type`, `cue_text`, `created_by`, `status` (`NEW` / `REVIEWED` / `USED` / `DISMISSED`).

Only the Editor Workbench may review, route, or dismiss cues.

### Success test
This shell is successful if a reader can understand and trust the intelligence quickly, while contributing useful directional feedback without entering editor logic.

---

## 5. Shell boundaries and handoff rules

### Rule 1 - One backbone, separate working modes
All shells read from the same intelligence backbone, but they do not collapse into one interaction model.

### Rule 2 - Editorial state lives in Shell 1
Status changes such as draft, active, archived, promote, pattern candidate, and packaging decisions are owned by the Editor Workbench.

### Rule 3 - Mandate action lives in Shell 2
Relevance, mandate fit, target readiness, action sequencing, and commercial next steps are owned by the Mandate Workspace.

### Rule 4 - Reader contribution stays lightweight in Shell 3
The View Layer may create lightweight cues, but may not create notes or mutate editorial objects directly.

### Rule 5 - Teasers may exist, substitutes may not
- Workbench may show a small mandate teaser.
- View Layer may show small watch or mandate snapshots.
- But neither may replace the full Mandate Workspace.

---

## 6. Immediate product implications

### Product implication 1
Do not keep designing as if this is one expanding app with more tabs.
Design as three products on one backbone.

### Product implication 2
The current Grapevine Today work should be explicitly labeled as **Shell 1 only**.
It is the Today surface of the Editor Workbench, not the universal homepage for all future users.

### Product implication 3
Mandate Radar should be treated as a bridge concept now, and as the seed of the Mandate Workspace later.
It should not be allowed to grow into a half-mandate shell inside the Workbench.

### Product implication 4
The View Layer should not be a cleaned-up Grapevine clone.
It needs its own reading logic, its own language, and one lightweight feedback loop.

### Product implication 5
Backlog and roadmap should be cut per shell, not per page only.
Every ticket should belong to a shell.

---

## 7. Companion artifacts

To operationalize this Shell Map, the companion architecture artifacts are:

1. **Backbone Object Map v1.0**
   - canonical objects
   - visibility by shell
   - write ownership by shell

2. **Cross-Shell Routing Map v1.0**
   - how objects and cues move between shells
   - handoff logic
   - publishing and review routes

3. **Vocabulary Lock v1.0**
   - shell-by-shell language policy
   - allowed vs banned UI terminology

4. **Roadmap by shell**
   - Shell 1 - Editor Workbench
   - Shell 2 - Mandate Workspace
   - Shell 3 - View Layer

---

## 8. Decision statement

The V4G intelligence product should now be treated as:

**one intelligence backbone, three shells, three vocabularies, three jobs-to-be-done.**

This Shell Map is the approved baseline needed to keep editorial production, mandate application, and safe consumption from collapsing into one overloaded interface.

