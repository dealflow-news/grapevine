# Cross-Shell Routing Map v1.0

## Status
Architecture baseline: APPROVED
Version: 1.0 - 16 April 2026
Companion to: Shell Map v1.0, Backbone Object Map v1.0, Vocabulary Lock v1.0
Applies to: routing logic, workflow design, UI handoffs, queue design, API orchestration, review paths
Not to be reopened without version bump to v1.1+

## Purpose
This document defines how canonical objects move between the three shells of the V4G intelligence product.

- **Shell Map** defines what each shell is.
- **Backbone Object Map** defines which objects exist and who may touch them.
- **Routing Map** defines how those objects actually move, hand off, and change context between shells.

Its purpose is to prevent object confusion, duplicated workflows, and hidden ownership drift between Editor Workbench, Mandate Workspace, and View Layer.

---

## 1. Routing principles

### 1.1 Routing follows object ownership
Objects must move between shells without losing their canonical owner.
A route may change the context in which an object is used, but it must not silently transfer editorial or commercial truth to the wrong shell.

### 1.2 Handoffs are explicit
A shell may suggest, surface, or route an object to another shell, but handoff must be explicit.
Examples:
- Workbench may suggest mandate relevance
- View Layer may create editorial cues
- Mandate Workspace may consume editorial objects

None of those suggestions should silently overwrite canonical state.

### 1.3 Teaser is not transfer of ownership
A teaser in one shell does not mean that shell now owns the deeper workflow.
Examples:
- Mandate teaser on Workbench Today does not replace Mandate Workspace
- Briefing teaser in View Layer does not expose Briefing Studio assembly logic

### 1.4 Routing should preserve explainability
For every routed object, it should remain possible to answer:
- where it came from
- why it was routed
- who routed it
- what state it entered next

### 1.5 Reader feedback routes into review, not production
Anything coming from the View Layer enters a lightweight review queue first.
No reader action should create a signal, note, card, or pattern directly.

---

## 2. Executive routing overview

| Route | From | To | Trigger | Output |
|---|---|---|---|---|
| Editorial intake | External / ingestion | Editor Workbench | Capture, import, automation | `signal` |
| Signal drafting | Editor Workbench | Editor Workbench | Enrich, draft, cluster, promote | `intel_note` |
| Knowledge extraction | Editor Workbench | Editor Workbench | Extract / generalize / confirm | `knowledge_card`, `pattern` |
| Packaging | Editor Workbench | Editor Workbench / View Layer | Briefing Studio assembly and publish | `briefing_collection` -> published surface |
| Mandate relevance | Editor Workbench / Mandate Workspace | Mandate Workspace | Suggest or confirm relevance | `mandate_match` |
| Mandate exploitation | Mandate Workspace | Mandate Workspace | Review, prioritize, action | action board, brief pack, watch state |
| Reader contribution | View Layer | Editor Workbench | Micro composer submit | `editorial_cue` |
| Cue escalation | Editor Workbench | Mandate Workspace or Briefing Studio | Editor review and routing | routed cue outcome |

---

## 3. Core routing chains

### 3.1 Editorial production route
This is the main production chain.

**Flow**  
`capture` -> `signal` -> `intel_note` -> `knowledge_card` and/or `pattern` -> `briefing_collection`

**Shell path**
- ingestion enters **Editor Workbench**
- editorial transformation remains in **Editor Workbench**
- selected outputs later appear in **View Layer**

**Meaning**
This route converts raw or semi-raw market material into governed editorial intelligence.

**Notes**
- `signal` stays pre-editorial
- `intel_note` carries editorial judgment
- `knowledge_card` and `pattern` capture durable meaning
- `briefing_collection` packages output for downstream use

---

### 3.2 Mandate application route
This is the commercial application chain.

**Flow**  
`mandate` + relevant `signal` / `intel_note` / `knowledge_card` / `pattern` / `entity` -> `mandate_match` -> `action board` / `brief pack`

**Shell path**
- source intelligence usually originates in **Editor Workbench**
- application happens in **Mandate Workspace**
- teaser or summary may appear back in **Editor Workbench**

**Meaning**
This route does not change editorial truth. It changes commercial relevance inside a mandate context.

**Notes**
- mandate relevance belongs in `mandate_match`, not in the base editorial object
- Workbench may suggest a match
- Mandate Workspace confirms, prioritizes, or dismisses it

---

### 3.3 Reader contribution route
This is the lightweight feedback chain.

**Flow**  
View Layer item -> `editorial_cue` -> Workbench review queue -> `USED` / `DISMISSED` / routed to Today / Briefing Studio / Mandate Workspace

**Shell path**
- contribution starts in **View Layer**
- review and routing happen in **Editor Workbench**
- optional commercial use may later surface in **Mandate Workspace**

**Meaning**
This route lets readers shape future coverage without entering editorial production directly.

**Notes**
- cues never become notes automatically
- cues never mutate the originating object directly
- cues are advisory until reviewed

---

### 3.4 Governance support route
This is the confidence and distribution chain.

**Flow**  
`evidence_link` + `audience_profile` shape note/card/pattern confidence, visibility, packaging, and shell-specific exposure

**Shell path**
- governed in **Editor Workbench / governance layer**
- consumed indirectly in **Mandate Workspace**
- surfaced as filtered or simplified logic in **View Layer**

**Meaning**
These objects are rarely front-stage, but they determine whether something is trustworthy, visible, publishable, or client-safe.

---

## 4. Route-by-route detail

### 4.1 Route A - Raw intake into Workbench

**From**
- connector feed
- manual entry
- file ingest
- URL ingest
- automated parser

**To**
- `signal`

**Owning shell**
- Editor Workbench

**Entry points**
- Drop Point
- Quick capture
- automation pipeline

**Required routing metadata**
- source origin
- created_at
- capture method
- created_by or system actor
- confidence seed if known

**Exit conditions**
A signal may then:
- be dismissed
- be linked
- be clustered
- be drafted into an `intel_note`
- be surfaced for mandate relevance suggestion later

---

### 4.2 Route B - Signal to intel_note

**From**
- `signal`

**To**
- `intel_note`

**Owning shell**
- Editor Workbench

**Trigger types**
- editor creates draft
- enrich flow
- cluster-derived drafting
- quick route such as Move to draft from Today

**Routing rule**
The new `intel_note` must preserve traceability back to its source signal(s).

**Minimum linkage expectation**
- source signal ID(s)
- editor / system origin
- created_at
- linked entities if already known

**Exit conditions**
An `intel_note` may then:
- remain draft
- become active
- be archived
- feed cards, patterns, briefings, mandate suggestions

---

### 4.3 Route C - intel_note to knowledge_card / pattern

**From**
- `intel_note`
- cluster context
- repeated signal convergence

**To**
- `knowledge_card`
- `pattern`

**Owning shell**
- Editor Workbench

**Trigger types**
- extract card
- confirm pattern candidate
- editorial generalization workflow

**Routing rule**
This route is interpretive, not merely mechanical.
It should preserve explainable lineage to its originating note or notes.

**Minimum linkage expectation**
- derived_from object IDs
- editor / reviewer
- confirmation or extraction timestamp

**Exit conditions**
- card becomes reusable memory
- pattern becomes candidate or confirmed library object
- both may later feed briefings and mandate relevance

---

### 4.4 Route D - Workbench to Mandate Workspace

**From**
- `signal`
- `intel_note`
- `knowledge_card`
- `pattern`
- `entity`

**To**
- `mandate_match`

**Owning shell**
- Mandate Workspace

**Trigger types**
- Workbench suggestion
- mandate-side pull
- automated relevance scoring
- editor or partner handoff

**Routing rule**
A routed object does not become a mandate object itself. It becomes part of a mandate context through `mandate_match`.

**Minimum linkage expectation**
- mandate ID
- source object type
- source object ID
- routed_by or suggested_by
- match rationale or reason seed
- created_at

**Exit conditions**
A mandate match may then become:
- suggested
- relevant
- priority
- actioned
- dismissed

---

### 4.5 Route E - Workbench to View Layer

**From**
- `intel_note`
- `knowledge_card`
- `pattern`
- `briefing_collection`

**To**
- View Layer surfaces

**Owning shell**
- Output remains editorially owned by Workbench; exposed through View Layer

**Trigger types**
- curation decision
- publication decision
- briefing release
- reader-safe selection logic

**Routing rule**
Only selected, audience-safe, visibility-safe content may cross into the View Layer.

**Minimum gating logic**
- audience suitability
- sensitivity compliance
- packaging eligibility
- publication status where relevant

**Exit conditions**
Objects in View may then:
- be read
- be filtered
- trigger `editorial_cue`

They must not become editable there.

---

### 4.6 Route F - View Layer to Workbench via editorial_cue

**From**
- View Layer item

**To**
- `editorial_cue`
- Workbench review queue

**Owning shell**
- created in View Layer
- reviewed in Editor Workbench

**Trigger types**
- Question
- Angle
- Usefulness

**Routing rule**
A cue is feedback, not production content.
It must stay separate from notes, signals, cards, and patterns until editorial review decides otherwise.

**Minimum cue fields**
- cue_id
- source_item_id
- source_item_type
- cue_type
- cue_text
- created_by
- created_at
- status

**Review outcomes**
- `REVIEWED`
- `USED`
- `DISMISSED`
- optionally routed onward

---

### 4.7 Route G - Workbench review of editorial_cue

**From**
- `editorial_cue`

**To**
- Today queue
- Briefing Studio angle backlog
- Mandate Workspace review context
- dismissed archive state

**Owning shell**
- Editor Workbench

**Trigger types**
- editor review
- governance review
- thematic backlog triage

**Routing rule**
Review does not automatically create a note. It creates a deliberate editorial or commercial next step.

**Possible outcomes**
- route to Today for research follow-up
- route to Briefing Studio as angle input
- route to Mandate Workspace if commercially relevant
- dismiss as low value

---

### 4.8 Route H - Mandate Workspace back into Workbench

**From**
- mandate-side learning
- missing info discovered during mandate review
- match rationale refinement

**To**
- Workbench suggestion queue or editorial backlog

**Owning shell**
- Mandate Workspace originates the signal for review
- Workbench decides whether editorial corpus should change

**Routing rule**
Mandate-side insight may inform editorial coverage, but it should not directly mutate editorial truth without Workbench review.

**Suggested implementation pattern**
Use a structured handoff object or queue item rather than directly editing notes or cards.

---

## 5. Shell-specific routing rules

### 5.1 Editor Workbench routing rules
- may create and mutate editorial objects
- may suggest mandate relevance but does not own final mandate truth
- may publish selected outputs to View Layer
- may review and route `editorial_cue`

### 5.2 Mandate Workspace routing rules
- may create and mutate `mandate` and `mandate_match`
- may consume editorial objects
- may send structured feedback back to Workbench
- may not rewrite editorial state on notes, cards, or patterns

### 5.3 View Layer routing rules
- may consume selected outputs only
- may create `editorial_cue` only
- may not create `signal`, `intel_note`, `knowledge_card`, or `pattern`
- may not bypass editorial review

---

## 6. Routing states that must be visible in product design

The routing model implies several state types that UI and workflow design should make visible.

### Editorial production states
- captured
- triaged
- drafted
- active
- archived
- candidate
- confirmed

### Mandate application states
- suggested
- relevant
- priority
- actioned
- dismissed

### Cue review states
- NEW
- REVIEWED
- USED
- DISMISSED

These state families should remain shell-appropriate and not bleed into each other unnecessarily.

---

## 7. Immediate design consequences

### Consequence 1
Do not let routing hide ownership.
A routed object may gain a new context, but not a new truth owner by accident.

### Consequence 2
Mandate usefulness must stay in `mandate_match`.
Do not encode commercial relevance as permanent editorial truth inside notes.

### Consequence 3
Reader prompts must route to review, not directly to production.
`editorial_cue` is a queue object, not a shortcut around curation.

### Consequence 4
Publishing is a route, not a shell collapse.
Content exposed in View remains rooted in Workbench-owned editorial logic.

### Consequence 5
Teasers are routing aids only.
A teaser may route the user into another shell, but must not quietly recreate the deeper workflow.

---

## 8. Minimum implementation checklist

Before implementing a new feature, confirm:

1. Which canonical object is being routed?
2. Which shell owns the truth of that object?
3. Is this a suggestion, a review step, or a state mutation?
4. Does the receiving shell gain context only, or edit rights too?
5. Is lineage preserved?
6. Is routing metadata visible and auditable?
7. Does the route create any accidental shadow object?

---

## 9. Open decisions for v1.1

1. Should Workbench-to-Mandate routing create `mandate_match` directly or a pre-match suggestion object first?
2. Should Mandate-to-Workbench feedback use a dedicated handoff object?
3. Should `brief_pack` remain a subtype of `briefing_collection` or become a mandate-owned derivative?
4. How much routing metadata should be exposed in UI versus kept operational only?
5. Should View Layer cue submissions show a simple personal history or remain fire-and-forget?

---

## 10. Decision statement

The three-shell model becomes operational only when routing is explicit.

- **Shell Map** defines the shells.
- **Backbone Object Map** defines the objects.
- **Cross-Shell Routing Map** defines the movement between them.
- **Vocabulary Lock** defines how each shell should speak.

From this point onward, new workflow design should be validated against all four documents together.