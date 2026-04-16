# Backbone Object Map v1.0

## Status
Architecture baseline - **APPROVED**

## Purpose
This document defines the canonical object layer for the V4G intelligence product.

It exists to make the three-shell architecture operational.
The shells cannot remain only a UX concept; they need a shared object model with clear visibility, write ownership, and routing rules.

This object map answers five questions for every backbone object:

1. What is it?
2. Which shell can see it?
3. Which shell can create it?
4. Which shell can mutate it?
5. What is it routed into next?

---

# 1. Design principles

## 1.1 One backbone, different shell behavior
All three shells read from the same intelligence backbone, but they interact with the objects differently.

- **Editor Workbench** creates, curates, enriches, and governs.
- **Mandate Workspace** applies and annotates relevance for live mandate use.
- **View Layer** consumes a selected subset and contributes only lightweight cues.

## 1.2 Object ownership must be explicit
Every canonical object needs a clear answer to:
- who owns the truth
- who may enrich it
- who may only read it
- which state changes are allowed where

## 1.3 Shells should not invent shadow objects without reason
If two shells need the same thing, use one canonical object with shell-specific views where possible.
Only create a shell-local object when the job-to-be-done is structurally different.

## 1.4 Reader feedback must remain separate from editorial production
Reader or partner feedback must never write directly into note or card objects.
That contribution belongs in a lightweight object such as `editorial_cue`.

---

# 2. Executive object overview

| Object | Core purpose | Canonical owner | Visible in | Writable in |
|---|---|---|---|---|
| `signal` | Raw or lightly processed intelligence event | Backbone / Workbench ingestion layer | Workbench, partly Mandate, selected View subset | Workbench only |
| `intel_note` | Curated editorial note derived from one or more signals | Editor Workbench | Workbench, partly Mandate, selected View subset | Workbench only |
| `knowledge_card` | Reusable, generalized intelligence object | Editor Workbench | Workbench, Mandate, selected View subset | Workbench only |
| `pattern` | Higher-order recurring market pattern | Editor Workbench | Workbench, Mandate, selected View subset | Workbench only |
| `entity` | Canonical company / party / actor / person reference | Backbone / entity layer | All shells as permitted | Backbone-admin + controlled Workbench enrichments |
| `evidence_link` | Provenance and support reference for signal/note/card/pattern | Workbench governance layer | Workbench, partly Mandate, rarely View | Workbench only |
| `audience_profile` | Audience and visibility logic | Backbone governance layer | Workbench, Mandate, View via filtered output | Governance only |
| `mandate` | Live commercial context object | Mandate Workspace | Mandate, partly Workbench teaser, optional View snapshot | Mandate Workspace only |
| `mandate_match` | Relevance link between intelligence and mandate | Mandate Workspace | Mandate, teaser in Workbench | Mandate Workspace primarily |
| `briefing_collection` | Curated output assembly object | Workbench / Briefing Studio | Workbench, later View as published result | Workbench only |
| `editorial_cue` | Lightweight feedback from View into editorial loop | View Layer creates, Workbench reviews | View, Workbench, optionally routed to Mandate | View create, Workbench review/update |

---

# 3. Canonical objects

# 3.1 `signal`

## Definition
A `signal` is the earliest durable intelligence object representing an observed event, mention, source item, change, or relevant market indicator.
It is not yet fully editorialized.

## Purpose
- preserve intake from feeds, uploads, manual capture, or automation
- hold the earliest usable intelligence unit
- feed triage, enrichment, clustering, and later editorial conversion

## Typical source origins
- public news
- regulatory records
- structured databases
- marketplace listings
- company disclosures
- human whispers
- manual capture
- file / URL / text ingest

## Shell visibility
- **Editor Workbench**: full visibility
- **Mandate Workspace**: filtered subset only when relevant
- **View Layer**: selected subset only if intentionally exposed in reader-safe form

## Create rights
- Workbench ingestion flows
- approved automated pipelines

## Edit / mutate rights
- Workbench only

## Typical mutable fields
- triage state
- confidence
- linked entities
- linked pattern candidate flag
- routing / watch flags
- dedup resolution

## Not allowed
- Mandate Workspace should not rewrite signal editorial truth
- View Layer should never create or edit `signal`

## Likely lifecycle
`captured` → `triaged` → `linked` / `dismissed` / `drafted` / `clustered`

## Routed into
- `intel_note`
- `pattern`
- `mandate_match`
- `briefing_collection` only indirectly through downstream editorial objects

---

# 3.2 `intel_note`

## Definition
An `intel_note` is the canonical editorial note object that turns one or more signals into a readable, governed, reusable intelligence unit.

## Purpose
- hold structured editorial output at note level
- preserve judgment, context, linked entities, linked patterns, and audience relevance
- serve as the base object for curation, retrieval, briefing, and mandate application

## Typical forms
- whisper note
- sector note
- situation note
- angle note
- context note

## Shell visibility
- **Editor Workbench**: full visibility
- **Mandate Workspace**: relevant subset only
- **View Layer**: selected and audience-safe subset only

## Create rights
- Workbench only
  - manual drafting
  - promoted/enriched signal conversion
  - cluster-derived drafting

## Edit / mutate rights
- Workbench only

## Typical mutable fields
- status
- title
- summary
- body
- audience
- sensitivity
- linked entities
- linked cards
- linked patterns
- evidence completeness
- editorial priority

## Not allowed
- Mandate Workspace may not edit note editorial state
- View Layer may not create or alter notes
- reader contribution must never land here directly

## Likely lifecycle
`draft` → `active` → `archived`

## Routed into
- `knowledge_card`
- `pattern`
- `briefing_collection`
- `mandate_match`
- selected View surfaces

---

# 3.3 `knowledge_card`

## Definition
A `knowledge_card` is a reusable intelligence object that generalizes signals and notes into durable insight.

## Purpose
- preserve precedent and reusable reasoning
- support retrieval, thematic memory, and editorial reuse
- provide mandate and reader-safe intelligence in a structured form

## Examples
- pattern explanation cards
- sector logic cards
- precedent cards
- thesis-support cards

## Shell visibility
- **Editor Workbench**: full visibility
- **Mandate Workspace**: strong relevance
- **View Layer**: selected subset, often ideal for curated reading

## Create rights
- Workbench only

## Edit / mutate rights
- Workbench only

## Typical mutable fields
- title
- core insight
- why it matters
- observable signals
- deal implication
- best use
- confidence
- linked patterns
- linked entities
- audience suitability

## Not allowed
- Mandate Workspace may reference cards but not rewrite them
- View Layer may read selected cards but not change them

## Likely lifecycle
`draft` → `active` → `retired` or `archived`

## Routed into
- `briefing_collection`
- `mandate_match`
- View Layer knowledge surfaces

---

# 3.4 `pattern`

## Definition
A `pattern` is a higher-order recurring market logic inferred from multiple signals, notes, or cards.
It is more stable and more interpretive than a single note.

## Purpose
- capture repeated structure across observations
- improve retrieval and framing
- connect daily signals to durable market logic

## Shell visibility
- **Editor Workbench**: full visibility and authoring
- **Mandate Workspace**: visible where useful for thesis and outreach
- **View Layer**: selected subset for reader-safe insight

## Create rights
- Workbench only

## Edit / mutate rights
- Workbench only

## Typical mutable fields
- pattern name
- rationale
- angle
- scope
- sectors
- geographies
- confidence
- linked signals
- linked notes
- linked cards
- confirmation state

## Likely lifecycle
`candidate` → `confirmed` → `active library` → `retired`

## Not allowed
- Mandate Workspace should not confirm or redefine patterns
- View Layer should never change pattern definitions

## Routed into
- `knowledge_card`
- `briefing_collection`
- `mandate_match`
- View Layer pattern surfaces

---

# 3.5 `entity`

## Definition
An `entity` is the canonical reference object for a company, investor, advisor, founder, family, fund, or other actor relevant to intelligence and mandates.

## Purpose
- support identity consistency across shells
- enable linking, aggregation, filtering, and explainability
- prevent free-text duplication of parties and actors

## Shell visibility
- **Editor Workbench**: visible and linkable
- **Mandate Workspace**: visible and important
- **View Layer**: visible where audience-safe

## Create rights
- backbone/admin flows
- controlled Workbench enrichment only where policy allows

## Edit / mutate rights
- entity governance layer primarily
- limited Workbench enrichment under controlled rules

## Typical mutable fields
- canonical name
- aliases
- type
- sector anchors
- geography anchors
- key identifiers
- link status / certainty

## Not allowed
- View Layer cannot create or alter entity truth
- Mandate Workspace should not fork entity identity

## Routed into
- signals
- notes
- cards
- patterns
- mandate matches
- view surfaces

---

# 3.6 `evidence_link`

## Definition
An `evidence_link` is the provenance-support object that connects a signal, note, card, or pattern to one or more supporting sources.

## Purpose
- preserve traceability
- enable confidence and governance logic
- make visible why something is believed

## Shell visibility
- **Editor Workbench**: full visibility
- **Mandate Workspace**: limited visibility where evidence matters for confidence or action
- **View Layer**: usually abstracted or summarized, not shown in full detail by default

## Create rights
- Workbench only

## Edit / mutate rights
- Workbench only

## Typical mutable fields
- source reference
- source type
- support strength
- excerpt or support note
- contradiction flag
- verification state

## Not allowed
- View Layer cannot author evidence
- Mandate Workspace cannot complete editorial evidence stitching as canonical truth

## Routed into
- note confidence
- card confidence
- pattern confirmation
- evidence queue and governance flows

---

# 3.7 `audience_profile`

## Definition
An `audience_profile` is the governance object that captures who content is suitable for and under what visibility / sensitivity logic.

## Purpose
- separate content intelligence from distribution rules
- support shell-appropriate filtering and safe publishing
- power Briefing Studio and View Layer selection

## Shell visibility
- **Editor Workbench**: visible and actionable
- **Mandate Workspace**: relevant only through filtered output behavior
- **View Layer**: consumed indirectly through permissions and packaging

## Create rights
- governance/admin only

## Edit / mutate rights
- governance/admin only
- Workbench may apply mapped values but should not redefine the model

## Typical fields
- audience key
- sensitivity ceiling
- visibility scope
- packaging eligibility
- distribution rules

## Not allowed
- Mandate Workspace should not invent audience logic ad hoc
- View Layer should not see internal governance complexity unless needed

## Routed into
- `intel_note`
- `knowledge_card`
- `briefing_collection`
- published View Layer outputs

---

# 3.8 `mandate`

## Definition
A `mandate` is the canonical commercial context object representing an active or tracked assignment, search, or live opportunity context.

## Purpose
- hold mandate identity and scope
- provide the application frame for relevant intelligence
- anchor match logic, action boards, and brief packs

## Shell visibility
- **Mandate Workspace**: full visibility
- **Editor Workbench**: teaser or limited awareness only
- **View Layer**: optional reader-safe snapshot only, if ever exposed

## Create rights
- Mandate Workspace / commercial ops only

## Edit / mutate rights
- Mandate Workspace only

## Typical mutable fields
- mandate title
- type
- owner
- thesis
- search rails
- stage
- target scope
- active questions
- next actions

## Not allowed
- Workbench should not become mandate system of record
- View Layer cannot create or change mandates

## Routed into
- `mandate_match`
- `brief_pack`
- mandate-facing workspace views

---

# 3.9 `mandate_match`

## Definition
A `mandate_match` is the application-layer link between a mandate and a signal, note, card, pattern, or entity that appears relevant to that mandate.

## Purpose
- operationalize intelligence relevance for live mandates
- track what has already informed commercial action
- separate editorial truth from mandate usefulness

## Shell visibility
- **Mandate Workspace**: full visibility
- **Editor Workbench**: teaser summary only where appropriate
- **View Layer**: generally none

## Create rights
- Mandate Workspace primarily
- Workbench may suggest, but should not own final match truth

## Edit / mutate rights
- Mandate Workspace only

## Typical mutable fields
- mandate id
- linked object id and type
- relevance score or band
- match rationale
- action status
- last reviewed
- contact-readiness

## Not allowed
- View Layer cannot create or update mandate matches
- Workbench should not replace mandate-side decisioning here

## Likely lifecycle
`suggested` → `relevant` → `priority` → `actioned` / `dismissed`

## Routed into
- match feed
- action board
- brief pack
- mandate history

---

# 3.10 `briefing_collection`

## Definition
A `briefing_collection` is the curated packaging object that assembles notes, cards, patterns, and audience logic into a coherent output.

## Purpose
- produce briefings
- support editorial packaging and audience routing
- become the source for publishable or shareable deliverables

## Shell visibility
- **Editor Workbench**: full visibility in Briefing Studio
- **Mandate Workspace**: may consume mandate-specific output
- **View Layer**: sees only finalized/published result, not assembly tooling

## Create rights
- Workbench only

## Edit / mutate rights
- Workbench only

## Typical mutable fields
- title
- collection type
- audience
- included objects
- ordering
- editorial angle
- packaging status
- publication state

## Not allowed
- Mandate Workspace cannot perform full editorial packaging
- View Layer cannot mutate briefing collections

## Routed into
- View Layer surfaces
- internal or external briefings
- mandate brief packs

---

# 3.11 `editorial_cue`

## Definition
An `editorial_cue` is a lightweight contribution object created from the View Layer to shape future coverage without entering the editorial corpus directly.

## Purpose
- capture reader curiosity, angle suggestions, and audience relevance
- create a safe feedback loop into editorial production
- preserve reader value without polluting canonical notes

## Cue types
- `QUESTION`
- `ANGLE`
- `USEFULNESS`

## Shell visibility
- **View Layer**: create and view own submission state if desired
- **Editor Workbench**: review, route, use, dismiss
- **Mandate Workspace**: only if routed there intentionally after editorial review

## Create rights
- View Layer only

## Edit / mutate rights
- View Layer may create only
- Workbench owns review and lifecycle updates

## Suggested fields
- cue_id
- source_item_id
- source_item_type
- cue_type
- cue_text
- created_by
- created_at
- status
- routed_to
- reviewed_by
- reviewed_at

## Statuses
- `NEW`
- `REVIEWED`
- `USED`
- `DISMISSED`

## Not allowed
- editorial cues may not create notes automatically
- cues may not be stored as signals or notes
- readers may not edit underlying intelligence objects

## Routed into
- Today review queue
- Briefing Studio angle backlog
- mandate context review if relevant

---

# 4. Read / write matrix by shell

| Object | Editor Workbench | Mandate Workspace | View Layer |
|---|---|---|---|
| `signal` | Read / Create / Update | Read subset only | Read selected subset only |
| `intel_note` | Read / Create / Update | Read subset only | Read selected subset only |
| `knowledge_card` | Read / Create / Update | Read | Read selected subset |
| `pattern` | Read / Create / Update | Read | Read selected subset |
| `entity` | Read / Limited enrich | Read | Read selected subset |
| `evidence_link` | Read / Create / Update | Read limited | Rarely read abstracted |
| `audience_profile` | Read / Apply | Read indirect | Read indirect |
| `mandate` | Read teaser only | Read / Create / Update | Optional snapshot only |
| `mandate_match` | Read teaser only | Read / Create / Update | No |
| `briefing_collection` | Read / Create / Update | Read output only | Read published output only |
| `editorial_cue` | Read / Review / Route / Update status | Read only if routed | Create / Read own status optional |

---

# 5. Cross-object logic

## 5.1 Editorial production chain
`signal` → `intel_note` → `knowledge_card` and/or `pattern` → `briefing_collection`

## 5.2 Mandate application chain
`mandate` + (`signal` / `intel_note` / `knowledge_card` / `pattern` / `entity`) → `mandate_match`

## 5.3 Reader contribution chain
View Layer item → `editorial_cue` → Workbench review → optional routing to Today / Briefing Studio / Mandate Workspace

## 5.4 Governance chain
`evidence_link` and `audience_profile` do not usually appear as front-stage user objects, but they shape confidence, visibility, and routing across all other objects.

---

# 6. Immediate design consequences

## Consequence 1
Do not model the platform only around screens.
Model it around objects first, then shells, then screens.

## Consequence 2
Mandate relevance is not an editorial note field.
It belongs in `mandate_match`, not inside `intel_note` as permanent truth.

## Consequence 3
Reader feedback is not a note.
It belongs in `editorial_cue`, not in `signal` or `intel_note`.

## Consequence 4
Audience logic should remain governed separately.
Distribution and sensitivity should not be improvised differently per shell.

## Consequence 5
The same canonical object may have three different visual expressions across the shells.
That is expected and healthy.

---

# 7. Open decisions for v1.1

The following need refinement in the next pass:

1. Should `signal` and `intel_note` stay separate physical objects or be unified with subtype/state logic?
2. Should `pattern_candidate` remain a field on `intel_note` / `signal`, or become its own staging object?
3. How much of `entity` enrichment may happen in Workbench versus admin/governance only?
4. Should `brief_pack` be a subtype of `briefing_collection` or a separate object tied to mandates?
5. Should View Layer readers be able to see their own submitted `editorial_cue` history?
6. What minimum metadata is required for `mandate_match` explainability?

---

# 8. Decision statement

The V4G intelligence product should operate on a clear canonical object layer.

The backbone is not just content storage.
It is the governed system of record for:
- signals
- notes
- cards
- patterns
- entities
- evidence
- mandates
- matches
- briefings
- editorial cues

Each shell should now be designed against this object map, rather than inventing screen-local meanings for the same thing.

