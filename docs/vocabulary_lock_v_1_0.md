# Vocabulary Lock v1.0

## Status
Architecture baseline: APPROVED
Version: 1.0 - 16 April 2026
Companion to: Shell Map v1.0, Backbone Object Map v1.0, Cross-Shell Routing Map v1.0
Applies to: UI copy, product naming, labels, workflow language, empty states, button text, navigation, onboarding, backlog grooming, design review
Not to be reopened without version bump to v1.1+

## Purpose
This document locks the vocabulary of the V4G intelligence product across the three shells.

Its purpose is to protect product clarity.
The same backbone objects may appear across different shells, but they must not be described in the same language everywhere. Each shell has a different job-to-be-done, a different level of cognitive load, and a different permission model.

Vocabulary is therefore part of architecture, not a cosmetic copy layer.

---

## Core rule
**One backbone does not mean one language.**

- **Shell 1 - Editor Workbench** uses editorial and governance language.
- **Shell 2 - Mandate Workspace** uses commercial and execution language.
- **Shell 3 - View Layer** uses reader-safe, insight-led language.

If a user can infer the wrong mental model from the language, the vocabulary is wrong even if the screen is visually correct.

---

## 1. Executive shell vocabulary overview

| Shell | Language mode | What the language should feel like | What it must not feel like |
|---|---|---|---|
| Editor Workbench | Editorial production | Precise, operator-grade, evidence-aware | Reader-safe simplified marketing copy |
| Mandate Workspace | Commercial application | Actionable, calm, mandate-specific | Editorial workflow jargon |
| View Layer | Curated consumption | Clear, confident, light, high-trust | Operator console language |

---

## 2. Shell 1 - Editor Workbench vocabulary

### Language intent
The Editor Workbench is the production shell.
Its language should make editorial state, evidence quality, review status, provenance, and packaging logic explicit.

### Allowed core vocabulary
- draft
- active
- archived
- candidate
- pattern candidate
- extract
- enrich
- promote
- review
- evidence
- provenance
- confidence
- sensitivity
- audience
- packaging
- routing
- curation
- verification
- linkage
- cluster
- convergence

### Preferred labels
- **Today**
- **Curate**
- **Knowledge Base**
- **Drop Point**
- **Briefing Studio**
- **Signal Desk**
- **Draft Lane**
- **Evidence Queue**
- **Pattern Resurfacing**

### Preferred verbs
- review
- enrich
- promote
- extract
- archive
- route
- verify
- link
- assign
- escalate
- draft

### Avoid in Workbench
- contact-ready
- next action needed
- watch only
- who cares as primary framing
- overly simplified “news feed” language that hides editorial state
- passive consumer language where explicit governance language is needed

### UI writing rule
Workbench copy should optimize for precision over softness.
If an item is blocked, candidate, draft, low-evidence, or unresolved, say so directly.

### Examples
**Good**
- Promote to Active
- Evidence incomplete
- Pattern candidate
- Low-confidence signal
- Route to Briefing Studio

**Avoid**
- Save for later thoughts
- Looks useful
- Maybe relevant
- Ready for people

---

## 3. Shell 2 - Mandate Workspace vocabulary

### Language intent
The Mandate Workspace applies intelligence to live mandates.
Its language should feel narrower, calmer, and closer to commercial decision-making.
It should explain usefulness, readiness, and next move, not editorial process.

### Allowed core vocabulary
- relevant
- watch
- priority
- contact-ready
- next action
- thesis fit
- target hypothesis
- outreach angle
- brief pack
- blocker
- follow-up
- mandate relevance
- search rail
- match
- action board
- reviewed for mandate

### Preferred labels
- **Mandate Workspace**
- **Mandate selector**
- **Thesis panel**
- **Match feed**
- **Action board**
- **Brief pack**
- **Watch list**
- **Priority items**
- **Next moves**

### Preferred verbs
- review for mandate
- mark relevant
- prioritize
- prepare outreach
- add to brief
- watch
- dismiss for mandate
- assign follow-up
- escalate

### Avoid in Mandate Workspace
- draft
- active
- archived
- promote
- extract
- ingest
- editorial candidate
- evidence jargon as primary UI language
- operator copy suggesting the user is editing canonical intelligence

### UI writing rule
Mandate language must frame intelligence as a means to action.
The user here should feel they are steering a live process, not working inside an editorial machine.

### Examples
**Good**
- Relevant to mandate
- Add to brief pack
- Priority for outreach
- Contact-ready target hypothesis
- Next action required

**Avoid**
- Promote note
- Extract card
- Archive item
- Candidate state
- Ingest source

---

## 4. Shell 3 - View Layer vocabulary

### Language intent
The View Layer is for reading, scanning, following, and lightly shaping future coverage.
Its language should feel clear, trustworthy, and free of operator burden.

### Allowed core vocabulary
- why it matters
- what to watch
- themes
- briefings
- signals
- knowledge
- patterns
- who cares
- question
- angle
- usefulness
- related themes
- follow this
- see more

### Preferred labels
- **Today** or **Briefings**
- **Signals**
- **Knowledge**
- **Themes**
- **What to watch**
- **Help us cover this better**

### Preferred verbs
- read
- follow
- explore
- see why it matters
- ask a question
- suggest an angle
- flag usefulness

### Avoid in View Layer
- draft
- archived
- promote
- extract
- ingest
- candidate
- evidence type
- sensitivity level
- taxonomy burden
- workflow states that expose production mechanics

### UI writing rule
The View Layer should feel curated, not unfinished.
If the user sees disabled operator concepts or process jargon, the shell is leaking Workbench language.

### Examples
**Good**
- Why it matters
- What should we look at next?
- What angle is underexplored?
- Who would care about this?
- Explore related themes

**Avoid**
- Promote this note
- Archive item
- Extract pattern
- Source type classification
- Evidence completeness matrix

---

## 5. Locked names and labels

### 5.1 Shell names
These names are locked for v1.0:

- **Editor Workbench**
- **Mandate Workspace**
- **View Layer**

Do not replace them casually with generic terms such as “Admin”, “App”, “Dashboard”, or “Portal”.

### 5.2 Key zone and product labels
The following labels are approved and should be treated as the preferred vocabulary set:

#### Workbench
- Today
- Curate
- Knowledge Base
- Drop Point
- Briefing Studio
- Signal Desk
- Draft Lane
- Evidence Queue
- Pattern Resurfacing

#### Mandate shell
- Mandate Workspace
- Mandate selector
- Thesis panel
- Match feed
- Action board
- Brief pack

#### Reader shell
- Today / Briefings
- Signals
- Knowledge
- Themes
- What to watch
- Help us cover this better

### 5.3 Bridging names
These may appear as bridge labels but must not silently replace full shells:

- **Mandate Radar** = bridge or teaser concept, not the full mandate shell
- **Market Pulse** = lighter market-facing signal surface, not the Workbench Today

---

## 6. Write affordance lock for View Layer

The View Layer has exactly one write affordance.
Its language is locked as a lightweight contribution mechanism, not as submission or editing.

### Preferred CTA
**Help us cover this better**

### Allowed prompt types
- **Question** - What should we look at next?
- **Angle** - What angle is underexplored?
- **Usefulness** - Who would care about this?

### Forbidden framing
Do not frame this as:
- submit intel
- add a note
- edit coverage
- classify content
- enrich this item

### Reason
The View Layer creates `editorial_cue`, not `signal`, not `intel_note`, not `knowledge_card`.
The language must protect that distinction.

---

## 7. Cross-shell translation rules

The same underlying object may need different language in different shells.
That is expected and required.

### Example 1 - `intel_note`
- **Workbench**: draft / active / archived note
- **Mandate**: relevant note / mandate insight
- **View**: briefing item / insight / signal context

### Example 2 - `pattern`
- **Workbench**: pattern candidate / confirmed pattern
- **Mandate**: recurring logic / thesis pattern
- **View**: theme / recurring market pattern

### Example 3 - `mandate_match`
- **Workbench teaser**: mandate-note match flagged
- **Mandate**: relevant / priority / contact-ready match
- **View**: usually not shown at all

### Rule
Do not force one object name to appear identically across shells when that would import the wrong mental model.

---

## 8. Banned vocabulary by shell

### 8.1 Banned in Mandate Workspace
These belong to editorial production and must not dominate mandate UI:
- draft
- archived
- promote
- extract
- ingest
- candidate
- packaging status

### 8.2 Banned in View Layer
These belong to operator workflows and must not appear in reader-facing UI:
- draft
- archived
- promote
- extract
- ingest
- sensitivity level
- evidence type
- pattern candidate
- verification queue
- provenance mechanics

### 8.3 Banned everywhere as generic fallback
These are too vague and should not become lazy product language:
- dashboard
- stuff
- items
- content bucket
- smart feed
- engine zone
- intel thing

Use precise product language instead.

---

## 9. Copy governance rules

### Rule 1 - Vocabulary follows shell, not object only
A note does not force note language everywhere.
Language must follow the user’s job in that shell.

### Rule 2 - Buttons should imply correct rights
If a user cannot change canonical truth, the CTA must not suggest they can.

### Rule 3 - Empty states must reinforce shell identity
- Workbench empty states may reference curation and review
- Mandate empty states should reference thesis and match relevance
- View empty states should reference what to follow or read next

### Rule 4 - Tooltips may be more explicit than labels
Short labels are fine, but tooltips and helper text should preserve architectural clarity.

### Rule 5 - Avoid mixed shell language on one screen
A single screen should not mix Workbench jargon and View-layer phrasing without a very explicit reason.

---

## 10. Review checklist for new features

Before approving a new feature or screen, confirm:

1. Which shell does it belong to?
2. Does the language match that shell’s job-to-be-done?
3. Does any label import the wrong workflow model?
4. Are action labels consistent with actual permissions?
5. Are banned terms leaking into the wrong shell?
6. Does the screen use canonical locked names where relevant?

If the answer to any of these is unclear, the feature is not ready for final copy lock.

---

## 11. Open decisions for v1.1

1. Should Workbench Today keep the label **Today**, or evolve into a more explicit product name later?
2. Should the View Layer use **Briefings** as its primary homepage label instead of **Today**?
3. Should **Pattern Resurfacing** remain a Workbench term, or become a more neutral label in shared contexts?
4. Should **Brief pack** remain mandate-specific, or become a subtype under a broader packaging vocabulary?
5. Do we need a bilingual naming policy later for client-facing surfaces in NL / FR / EN?

---

## 12. Decision statement

Vocabulary is now locked as an architectural layer of the product.

- **Shell Map** defines the shells.
- **Backbone Object Map** defines the objects.
- **Cross-Shell Routing Map** defines the movement.
- **Vocabulary Lock** defines how each shell should speak.

From this point onward, copy, labels, and product naming should be reviewed against this document before finalization.

