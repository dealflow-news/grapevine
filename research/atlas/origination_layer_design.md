# DESIGN — Origination layer (`contact_route` over time) + Atlas artifact storage

**Status:** design / proposal · **Owner:** V4G Data Ops · 2026-06-07
**Context:** the Belgian Entrepreneur & Capital Atlas 75→100 carries a `contact_route` per actor
("warm intro via Philippe Vlerick, co-investor"; "M&A Awards Belgium community"). This is the
highest-leverage field — the *origination* in "origination machine" — and it has no home in GS yet.
This doc specs where it lands, how it evolves over time, and where the source artifact itself is stored.

Legend: **[GROUNDED]** existing GS object · **[PROPOSED]** new, build under GS-SOP-003 · **[VERIFY]** CC.

---

## 1. What `contact_route` actually is

Not a fact about the actor — a fact about **our access to them**. It is:
- **Directional:** from a node *we can reach* → to the *target actor*.
- **Bridged:** via a person ("Philippe Vlerick"), a community ("M&A Awards Belgium"), a shared
  deal ("co-investor Smartphoto"), an advisor, a family tie, a board overlap, a school network.
- **Living / temporal:** warmth and status change as V4G actually works the route. The atlas gives
  a *seed estimate*; reality updates it.

Two axes that must stay separate:
- **actor-confidence** (atlas `confidence` 1–5: how active/relevant the target is) → feeds the
  **Intelligence Tier** (Gold/Platinum). **[GROUNDED — PARTY_INTELLIGENCE_TIERS]**
- **route-warmth** (how warm *our* path is) → the new origination layer below. Different axis.

---

## 2. Where it lands: a new `origination_routes` edge layer **[PROPOSED]**

`contact_route` does **not** fit the existing layers:
- `person_party_links` = **formal** mandate (director/UBO/board). A warm-intro path is **informal
  access** — wrong table. **[GROUNDED]**
- M&A Lens (`ma_next_angle='approach'`) records *that* we should approach + the thesis, but is
  single-valued per party — it can't hold many temporal multi-actor routes. **[GROUNDED]**
- `party_signal_observations` = point-in-time events, not a living route-state. **[GROUNDED]**

So a dedicated edge layer — the **informal access graph**, a meta-overlay on the entity graph:

```
public.origination_routes   [FACT] (proposed)
  route_id            uuid PK
  target_party_id     uuid  FK party_registry        -- the actor we want to reach
  target_person_id    uuid  FK person_registry NULL   -- if the route targets a person
  via_type            text  CHECK {person, co_investment, advisor, family, prior_deal,
                                   community, school_network, board_overlap, direct}
  via_person_id       uuid  FK person_registry NULL    -- the bridge person (e.g. Philippe Vlerick)
  via_party_id        uuid  FK party_registry  NULL    -- the bridge entity
  via_label           text  NULL                        -- free bridge ("M&A Awards Belgium")
  warmth              text  CHECK {cold, indicative, warm, activated}   -- OUR access
  status              text  CHECK {potential, in_progress, activated, stale, declined}
  confidence          int   CHECK 1..5                  -- seed confidence (atlas)
  observed_at         date                              -- when first recorded
  last_touched_at     timestamptz NULL                  -- last real interaction
  activated_at        timestamptz NULL
  source_code         text  FK ref_sources              -- provenance (SRC_ATLAS seed; later CRM)
  notes               text
  created_at/updated_at
  + RLS, service_role-only, like every write surface.
```
Naming/columns are CC/Chris's call; this is the shape. **[VERIFY]** against existing relationship
tables so it doesn't duplicate something + the CHECK sets land in `golden_safe_taxonomy`.

**Why an edge layer pays off:** once routes accumulate (the bridge person Philippe Vlerick is himself
V5 in the atlas, with his own party), the route graph becomes a *who-can-warm-intro-whom* meta-graph
over the entity graph → you can compute the **shortest warm path to any target actor**. That is the
origination-machine endgame.

---

## 3. How it evolves *over time* (the point of the question)

The atlas **seeds**; operations **maintain**. The layer is alive:

1. **Seed (MOD-ATLAS ingest):** each `contact_route` → one or more `origination_routes` rows,
   `status='potential'`, `warmth` from the atlas phrasing (named co-investor → `indicative`;
   "warm intro via X" → `warm`), `confidence` from the entry, `source_code='SRC_ATLAS'`,
   `observed_at` = edition date. The bridge resolves to a `via_person_id`/`via_party_id` where the
   bridge is itself a known actor (Vlerick), else `via_label`.
2. **Maintain (Folk CRM + interactions):** real touches update `warmth`/`status`/`last_touched_at`.
   This is the natural bridge to the existing Folk layer (`_stg_folk_*`) — a contacted bridge person
   promotes a route `potential → in_progress → activated`. **[GROUNDED — Folk staging exists]**
3. **Densify:** every new atlas edition / OTB run / deal adds bridge edges (co-investor, board
   overlap) → the graph thickens → warm-path search gets better.
4. **Decay:** a route untouched past a window → `stale` (a sweep, like the dedup stale-open sweep).

Provenance discipline: a route always carries its `source_code`. Atlas-seeded routes stay `potential`
until a real interaction upgrades them — the atlas claims access, it doesn't prove it. Detection-
precedes-correction: seed the claimed routes, let reality confirm.

---

## 4. Storing the atlas artifact itself ("ergens stockeren")

The atlas is **curated secondary research** — the master provenance anchor for everything MOD-ATLAS
will write. Two homes, both needed:

**4a. The raw document → versioned repo artifact.** Commit the `.md` as a dated, immutable edition:
```
grapevine-repo/research/atlas/atlas_75-100_2026-06.md     (Editorial OS — origination research)
        — or v4g-ingestion/docs/research/atlas/ if you prefer it next to the ingest that reads it.
```
Editions are append-only (`…_2026-06`, `…_2026-09`); never overwrite — each edition is a provenance
snapshot. Recommend grapevine (it is Dealflow.News origination editorial), with the ingest reading it
by committed path/SHA.

**4b. Register it as a source → so every derived row can cite it.** Add `SRC_ATLAS` to `ref_sources`
(`'Entrepreneur & Capital Atlas — curated origination research'`) via GS-SOP-009. Then every
MOD-ATLAS-written row (signal, lens thesis, origination route) carries `source_code='SRC_ATLAS'` +
ideally the edition reference (path/SHA or an edition id), so the DB always points back to the master
artifact. **[VERIFY]** whether to also register the edition in a research-artifact registry row (a
`changelog`/governance entry referencing the commit SHA is the minimum). **[GROUNDED — ref_sources is
the cite anchor; SRC_ODB/SRC_KBO already work this way]**

Net: the **document is the provenance root**, the **DB rows are typed projections of it**, and
`SRC_ATLAS` is the link between them — exactly how OTB rows cite `SRC_ODB`.

---

## 5. Sequencing (no build yet)

1. **OTB lands first** (registry facts + chain nodes) — MOD-ATLAS leans on it for name→KBO resolution
   and hard figures.
2. **Store the artifact now** (4a + 4b) — cheap, and it anchors provenance before any ingest.
3. **MOD-ATLAS lane** (parse the per-entry JSON → resolve actors → write Lens/tiers/signals/chain),
   sibling of `ingest_otb`, same Render-safe RPC pattern. `contact_route` → §2 `origination_routes`.
4. **`origination_routes` layer** built under GS-SOP-003 (3-part migration + governance) when MOD-ATLAS
   reaches the contact-route phase; the Folk-CRM maintenance wiring (§3.2) is a follow-on.

---

## 6. For CC when this turn comes (recon, not now)

- Confirm no existing relationship/route table already covers this (don't duplicate). **[VERIFY]**
- `SRC_ATLAS` add to `ref_sources` (GS-SOP-009); edition-reference convention.
- The `origination_routes` CHECK sets + RLS + service_role grant; FKs to party_registry/person_registry.
- The bridge-resolution rule (when a `contact_route` bridge is a known actor → link; else `via_label`).
- The Folk-CRM → warmth/status update path (§3.2).
