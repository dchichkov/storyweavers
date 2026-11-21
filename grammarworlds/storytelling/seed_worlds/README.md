# Twenty Luna seeds, twenty grammarworlds

The source collection is
`storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/`.
Music, greenhouse, library and pottery already existed. This directory supplies
the other **16**, completing all 20. Rescue, kite and key are earlier prototypes,
so the joined runtime has **23 worlds**. `catalog.py` records the one-to-one source
mapping and hashes the original full text; generated rows and memory documents
retain that provenance.

| Seed | World | Physical/narrative turn |
|---:|---|---|
| 01 | bakery | Deliver the smudged birthday cake; the lonely recipient accepts it |
| 02 | puppets | Make and secure a replacement star, then speak in the play |
| 03 | greenhouse (existing) | Share limited water and repair the supply |
| 04 | seaside | Correct the mistaken landmark before the tide closes the way |
| 05 | library (existing) | Help recover a missing book while adapting a drawing plan |
| 06 | snow | Abandon a race to free the delivery sled |
| 07 | picnic | Save the lunch rather than chase a sign toward the river |
| 08 | music (existing) | Adapt a performance while respecting a friend's boundary |
| 09 | market | Admit a weighing error, remove the leaf and correct the order |
| 10 | camp | Stay with a frightened companion and share the lantern |
| 11 | pottery (existing) | Adapt a damaged gift to the recipient's grip |
| 12 | orchard | Leave the unripe high pear and use the bruised ripe one |
| 13 | costume | Share the cape and lift its hem instead of damaging it |
| 14 | pond | Free the snagged net before retrieving and tethering the boat |
| 15 | repair | Diagnose the trapped string after tightening locks the wheel |
| 16 | museum | Fix the light in place to make the shadow experiment work |
| 17 | laundry | Move clean washing under shelter when the prop slips |
| 18 | trail | Use an accessible route and a compass-guided detour together |
| 19 | festival | Move reachable bunting to preserve access through the gate |
| 20 | biscuit | Rejoin the last dough lump and combine both children's designs |

## Representation and generation

Each source has an authored Python data module. `schema.py` supplies concise
constructors for entities, named events, guards, effects, typed surface
expressions, QA claims and local alternatives. `engine.py` executes those
contracts. `chain` expands into explicit named dependencies; `fork` provides
mutually exclusive event alternatives that join at the next dependency.
There is no runtime language model, raw-prose parser or arbitrary evaluation of
text as code.

The surface expressions compile through the existing GF/Codeco-derived typed
phrase grammar, expanded continuations and joint annotated-token sampler.
They are not stored final sentences. Entity references, clause roles, actions,
speakers/listeners and proposed event attributes accompany each token candidate.
Both past/present tense and symbolic word heads work through the usual runtime.

Every new world has a bounded physical graph, two-speaker dialogue, a state-driven
turn and an ending image. The alternatives affect physical state or the acting
participant. These are compact adaptations of the original 600–900-word stories,
not complete reproductions. Secondary characters, travel, timing, exact quantities
and some loan obligations are deliberately simplified; each module states its
preserved core and local adaptations.

The memeplex north star is preserved by grounding every actor and effect in an
entity, checking guards before commitment, and using persistent states to enable
later scenes. Prediction and rejected commitments do not mutate the input world.
The full memeplex composition algebra is not implemented here.

## Reuse and annotations

`story_memory.annotate` preserves the whole generated text and sampled tokens,
then adds source event/entity observations. All newly authored events are
searchable through these annotations, including the compound ones.

The joined mapping bank additionally loads `mapping_bank/seed_stories.json`:
six shared rules for typed fetch, put and handoff operations. They match the
complete source entity diff, not just a verb. Target carriers must satisfy their
own types, capabilities, location and operation guards. Compound actions such as
unsticking a net, diagnosing a wheel or baking dough are not reduced to transfers
merely to increase executable coverage. The bank can retrieve from all 20 seeds;
it does not yet make all their complex mechanics portable.

## Use and verify

```sh
.venv/bin/python -m grammarworlds.storytelling --scenario repair --seed 7 --heads --continuations expanded --qa
.venv/bin/python -m grammarworlds.storytelling --scenario festival --seed 7 --json
.venv/bin/python -m grammarworlds.portable --scenario biscuit --qa
.venv/bin/python -m unittest grammarworlds.test_seed_worlds -q
.venv/bin/python -m grammarworlds.storytelling.seed_worlds.audit --out /tmp/twenty-seed-worlds --count 20
```

The audit exports full traces, intact annotated story memory, preselected examples,
QA, original source hashes, physical guard interventions and one receiving-world
reuse sample from every seed family. At 20 samples per family it also requires
coverage of every registered event kind. The tests check story-specific ending
states, guard rejection without mutation, source coverage, annotated tokens,
meaningful event alternatives and executable reuse in the underdefined receiver.

[Current samples and coverage](../../runs/seed_worlds_20261107_v4/report.md).
Mechanical success is not a prose-quality score. Repeated names, compressed causal
explanations and narrow local variation remain limitations; no new Luna evaluation
is claimed for this expansion.
