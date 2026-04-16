# V4G Intelligence Product Architecture Note

## Purpose

This note defines a future-proof product architecture for three connected environments: the **Editor Workbench**, the **Mandate Workspace**, and the **View Layer**. The goal is to create a coherent path from intelligence creation, to mandate application, to client-safe or partner-safe consumption, while preserving a lightweight contribution mechanism in the view experience.[file:54][cite:19][cite:22][cite:28]

The current `index.html` already behaves like an editor-first workbench, with clear workbench features such as Curate review states, Knowledge Base filters, Drop Point ingest, and a disabled Intel Pulse area that points toward a separate mandate logic.[file:54] Rather than continuing to compress all future usage into one shell, the architecture should evolve toward one shared intelligence engine with three distinct environments.[file:54][cite:55][cite:57]

## Core principle

The platform should be understood as **one intelligence backbone, three shells**.[file:54][cite:27] The backbone contains the canonical notes, signals, cards, entities, evidence, and audience logic; the shells shape these assets into different user experiences according to the user’s job-to-be-done.[file:54][cite:23][cite:57]

The three shells are not just permission variants of the same interface. They represent different modes of work: creating and curating intelligence, applying intelligence to active mandates, and consuming intelligence with only a minimal ability to guide future coverage.[file:54][cite:19][cite:28]

## Shell 1 — Editor Workbench

### Mission

The Editor Workbench is the production environment where raw inputs become structured, usable intelligence.[file:54][cite:28] Its mission is to help editors and analysts detect, assess, enrich, connect, prioritise, and package signals into cards, patterns, and publishable outputs.[cite:19][cite:21][cite:23]

### Primary users

- Intelligence editors
- Analysts
- Research operators
- Internal writers
- Governance users responsible for quality and provenance controls[cite:23][cite:57]

### Main jobs

- Ingest new material through manual, URL, file, or batch input.[file:54]
- Review and promote whispers or candidate items into active intelligence.[file:54]
- Link signals to knowledge cards, sectors, lenses, and entities.[file:54][cite:27]
- Surface convergence, weekly themes, and pattern candidates for further treatment.[cite:21]
- Draft briefings, notes, newsletters, and publishable content through a guided editorial workflow.[cite:18]

### Recommended tab structure

| Tab | Role | Why it belongs here |
|---|---|---|
| Today | Daily editorial command deck | Start-of-day triage, pattern surfacing, mandate teaser, prioritisation.[cite:58] |
| Curate | Evidence review and assessment | This is the judgment layer where signals are read, promoted, linked, and refined.[file:54][cite:28] |
| Knowledge Base | Reusable memory and precedent | Houses patterns, standards, and library-grade knowledge objects.[file:54] |
| Drop Point | Intake and ingestion | The current app already includes single and batch import modes suited to workbench behaviour.[file:54] |
| Briefing Studio | Output generation | Supports thesis-based drafting and editorial angle creation after source selection.[cite:18] |

### UX principles

The Editor Workbench should optimise for **decision speed with visible evidence**.[cite:19][cite:58] Left-hand scanning, right-hand sensemaking, and visible provenance are consistent with the user’s earlier preferred UI direction and with the current two-pane patterns already present in Curate and Intel Pulse.[file:54][cite:19]

This shell may expose operator concepts such as draft, active, archived, candidate, extract, enrich, and promote because these are part of the editorial production process.[file:54] It should remain dense, powerful, and slightly technical, because its users are trained operators rather than passive readers.[cite:23][cite:28]

### What should stay out

The Editor Workbench should not become the final home for deep mandate execution. It may contain mandate awareness through teasers and handoffs, but the actual management of mandate-specific targets, actions, and deal-team workflows belongs elsewhere.[file:54]

## Shell 2 — Mandate Workspace

### Mission

The Mandate Workspace is the application environment where intelligence is turned into mandate advantage.[file:54] It applies the broader editorial and signal layer to a narrower, action-oriented context: active buy mandates, sell mandates, add-on searches, target landscapes, outreach preparation, and situational updates.[file:54][cite:24]

### Primary users

- V4G deal team
- Mandate owners
- Partners steering specific assignments
- Internal commercial and execution roles[cite:24]

### Main jobs

- Define or refine mandate thesis and search logic.
- Review signal matches relevant to a mandate.
- Translate sector or pattern intelligence into target and outreach hypotheses.
- Prepare mandate briefs, talking points, and worklists.
- Track which intelligence items have already informed the mandate.[file:54]

### Recommended workspace anatomy

| Component | Purpose | Notes |
|---|---|---|
| Mandate selector | Choose active mandate | Replaces the early Intel Pulse list concept with a cleaner execution frame.[file:54] |
| Thesis panel | Mandate intent and search rails | Converts broad editorial lenses into mandate-specific interpretation. |
| Match feed | Relevant signals and cards | A focused subset, not the full editorial feed. |
| Action board | Next moves | Call prep, outreach targets, follow-ups, missing info, watch items. |
| Brief pack | Reusable mandate output | Meeting prep, internal note, buyer/seller thesis summary. |

### UX principles

The Mandate Workspace should feel **narrower, calmer, and more actionable** than the Editor Workbench.[file:54] The user here is not trying to decide whether a signal deserves editorial attention; the user is trying to exploit relevant intelligence for a live commercial process.[cite:24]

This shell should therefore replace editorial process states with execution states such as watch, relevant, priority, contact-ready, and next-action-needed. It should not expose ingest mechanics, promote modals, or workbench-heavy classification controls unless there is a very strong operational reason.[file:54]

### Relationship to Today

Today may still show a **mandate teaser** as a bottom card because that is a useful bridge from editorial triage into execution awareness.[file:54] But that teaser should remain a handoff surface, not a substitute for a real mandate environment.

## Shell 3 — View Layer

### Mission

The View Layer is the consumption environment for users who need to **read, scan, follow, and understand**, but not operate the underlying machine.[cite:22][cite:23] It translates the same backbone into a simpler, cleaner surface with minimal cognitive load and minimal operational risk.[file:54]

### Primary users

- Partners who want signal awareness without workbench complexity
- Internal readers outside the editor team
- Selected clients or ecosystem participants in later phases
- Readers of curated briefings, selected signals, and thought leadership[cite:22]

### Main jobs

- Monitor current themes and notable signals.
- Read selected intelligence safely.
- Follow sectors, lenses, patterns, or mandates at a high level.
- Understand why an item matters and to whom it matters.
- Lightly shape future coverage through one very small input affordance.[cite:22]

### Recommended structure

| Area | Role | Why it fits the view layer |
|---|---|---|
| Today / Briefings | Daily read surface | Gives the best signal-to-context ratio for non-operators. |
| Signals | Read-only curated stream | Shows selected items, not operator queues. |
| Knowledge | Clean card library | Reader-safe subset of KB with audience filtering. |
| Watchlists or Mandates | Optional | Reader-safe snapshots only, no execution controls. |

### UX principles

The View Layer must be **read-mostly, not fully passive**.[cite:19][cite:22] It should remove workbench vocabulary such as draft, active, archived, ingest, extract, and promote, because those are editorial process concepts rather than reader value concepts.[file:54]

The design goal is clarity, confidence, and trust. Readers should feel they are seeing curated intelligence, not entering an operator console with disabled buttons.[file:54]

## The one write affordance

### Why it matters

A pure read-only surface misses an important opportunity: readers often know what deserves a second look, what angle is being missed, or who a piece of intelligence may matter to.[cite:22][cite:23] That kind of contribution is valuable, but it should not turn the reader into an editor or ask the reader to learn the workbench model.[cite:18]

The correct answer is a **single lightweight input affordance** inside the view layer. It should be framed as a contribution to future coverage, not as content editing or intel submission.[cite:18][cite:22]

### Recommended interaction model

The button should open a very small prompt composer with exactly three options:

| Prompt type | Core question | Strategic purpose |
|---|---|---|
| Question | “What should we look at next?” | Captures curiosity, gaps, next-step research leads. |
| Angle | “What angle is underexplored?” | Captures framing, thesis, or editorial opportunity. |
| Usefulness | “Who would care about this?” | Captures audience relevance and commercial usefulness. |

This triad works because it maps to three different forms of value: investigation, framing, and audience fit.[cite:18][cite:22] It is also small enough to stay intuitive and broad enough to generate useful future content signals.

### Detailed explanation of the three prompts

#### Question — “What should we look at next?”

This prompt is best for identifying missing evidence, adjacent themes, or unanswered implications.[cite:18] It turns the reader into a scout for the editorial agenda without asking for structured classification.

Typical high-value answers include:

- “Are there similar succession signals in adjacent industrial niches?”
- “Should we check whether this investor has made comparable moves in the Netherlands?”
- “What does this imply for founder-owned distributors?”

This prompt adds value because it feeds the future research queue and can later be routed into Today, Curate, or a briefing backlog.[cite:21]

#### Angle — “What angle is underexplored?”

This prompt is best for identifying the **story behind the signal**.[cite:18] It helps readers articulate the interpretation that has not yet been made explicit.

Typical high-value answers include:

- “This is not only distress; it may also be a succession story.”
- “The cross-border angle is stronger than the sector angle here.”
- “This should be framed as investor pattern recognition rather than deal news.”

This prompt adds value because it improves Briefing Studio inputs and helps editors move from factual capture to more differentiated publishable output.[cite:18]

#### Usefulness — “Who would care about this?”

This prompt is best for surfacing audience fit and practical relevance.[cite:22][cite:23] It is especially useful for a platform that may later serve different internal or external audiences through filtered views.

Typical high-value answers include:

- “Family business advisors would care about this.”
- “This matters mainly for lower mid-market buy-and-build funds.”
- “Corporate development teams in logistics would find this useful.”

This prompt adds value because it helps the system connect content not just to topics, but to audiences and eventual distribution logic.[cite:22]

### UX rules for the prompt feature

- The feature should use **one button**, not several competing buttons.
- The user should choose one of the three prompt types inside the composer, not before opening it.
- The interaction should take less than 20 seconds.
- The input field should stay short, with a single text box.
- The system should never ask the reader to classify note type, source type, evidence type, sector, or taxonomy values.[file:54]
- Submitted prompts should not enter the main note tables directly; they should land in a lightweight review queue or editorial cue object.[cite:55]

## Recommended object: editorial cue

The contribution coming from the View Layer should become a small object such as `editorial_cue`, `reader_prompt`, or `future_coverage_cue`. It should be intentionally lighter than a note and intentionally separate from production notes.[cite:55][cite:57]

### Suggested fields

| Field | Purpose |
|---|---|
| cue_id | Unique identifier |
| source_item_id | Which signal, briefing, card, or pattern triggered the cue |
| cue_type | `QUESTION`, `ANGLE`, or `USEFULNESS` |
| cue_text | Reader input |
| created_by | User or audience identity |
| created_at | Timestamp |
| status | `NEW`, `REVIEWED`, `USED`, `DISMISSED` |
| routed_to | Optional destination such as Today queue, Briefing Studio, or mandate context |

### Why this object matters

Separating editorial cues from notes protects the editorial corpus from noise while still preserving valuable reader feedback.[cite:23][cite:57] It also makes it possible to build downstream workflows later, such as routing high-quality cues into briefing preparation or mandate watchlists.[cite:21]

## Cross-shell workflow

A coherent future flow could work like this:

1. The **Editor Workbench** ingests and curates intelligence.[file:54][cite:28]
2. The best items surface through **Today**, cards, patterns, and briefings.[cite:58]
3. Some intelligence is routed into the **Mandate Workspace** when it becomes commercially relevant for a live mandate.[file:54][cite:24]
4. A selected subset becomes visible in the **View Layer** for consumption by non-operators.[cite:22]
5. The View Layer contributes back through **editorial cues**, not through raw notes or editing rights.[cite:18][cite:22]
6. Editors review the cue and decide whether it should influence future curation, a briefing angle, or mandate interpretation.[cite:18]

This creates a complete loop without collapsing all roles into one interface.[file:54][cite:55]

## Product recommendation

The strongest recommendation is to proceed in three stages. First, complete the **Editor Workbench** as the production-grade environment, including Today, Curate, Knowledge Base, Drop Point, and Briefing Studio.[file:54] Second, design the **Mandate Workspace** as a separate execution shell rather than extending Today into a mandate cockpit.[file:54] Third, create the **View Layer** as a clean consumption surface that includes exactly one write affordance: the lightweight editorial cue.[cite:22][cite:23]

This architecture preserves editorial quality, supports mandate execution, and opens a path to final user consumption without forcing every audience into the same mental model.[file:54][cite:19][cite:28]
