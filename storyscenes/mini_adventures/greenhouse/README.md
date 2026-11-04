# The Window Between Them

Round 4, seed ingredient 822263077. Reference written first: 997 prose words
(1,002 including the heading). The reference is unchanged from the frozen draft.
The inventory retains twenty reference/alternate encounters mapped onto nineteen
runtime scenes. The waiting beat is consolidated into the two repair encounters;
the inventory does not claim it is independently playable. Four scenes are
optional: measuring stick, snail, tea, notebook. Seven scenes form the complete
spine; eight includes one vignette. Runtime selection uses bounded DFS over
guards, not a list of prewritten complete routes.

## Run

```bash
.venv/bin/python -m storyscenes.mini_adventures.greenhouse.world --seed 822263077 --scenes 8
.venv/bin/python -m unittest storyscenes.mini_adventures.greenhouse.test_world
```

Integration entry point: `storyscenes.mini_adventures.greenhouse.world`.
Episodes and replay return JSON-native dictionaries. `party.location` tracks
Mara; Ivo has his own location, particularly for the separation ending.

## Consequences

Six validated dimensions are weather, repair tape, damp seeds, honesty policy,
Ivo's readiness, and rescue strategy. Wind requires securing the vent closed;
heat requires holding it open. A notched wooden stay braces the closed frame
in wind or carries the raised frame's weight in heat. Tape or parcel string
fastens the stay's foot to its bracket; paper is only a rain screen or padding,
never the structural support for glass. No tape means unwrapping the parcel and
borrowing a seed tin; available tape leaves the parcel intact. Choosing a pot
relay instead leaves two seedlings damaged during the half-hour move. Damp
seeds or damaged tomatoes defer
planting. Honesty cannot undo crop loss, and a successful repair cannot buy
forgiveness while Mara maintains her lie.

- `joint_care`: live tomatoes, planted fresh beans, admission and a receptive
  friend; Mara receives a spare key.
- `supervised_trial`: admission but damaged plants/seeds or a guarded friend;
  Ivo retains the key and agrees to a supervised Saturday visit.
- `separation`: Mara maintains her lie; she leaves carrying rejected beans,
  even if her repair saved the tomatoes.

This follows the memeplex north star by embedding trust, knowledge, custody and
plant condition in named carriers and letting those states constrain later
action/prose. No gen6/gen7 engine changes or runtime language models are used.

## Evidence

Twenty-six pack tests pass. They cover 200 first-seed routes (0-99 at both lengths), all
64 parameter corners at both lengths (128 further routes), deterministic exact
replay, atomic rejection, absent optional effects, spatial continuity, inaccessible
seeds, outcome guards, and counterfactual seed-carrier and forgiveness effects.
Round 2 adds checks for declined-but-available repair materials, timed damage
progression with survivors, different heat/wind injuries, rigid pane support,
atomic rejection of missing supports and instant crop loss, visible watering,
and requesting/opening a tin only when needed. Metadata counts exclude the title.
Across seeds 0-99, the 200 routes yield 94 supervised trials, 76 separations and
30 joint-care outcomes. Scene lengths are 47-73 words; maximum search visits 13.
These counts describe mechanically valid routes, not independent plot diversity.

`first_draws.md/jsonl` preserve the original consecutive three assignment-seed
draws at each length. Reading found a contradictory repair claim in a failed
rescue; that is retained as evidence, not a current-quality example.
`first_draws_v2.md/jsonl` record the round-1 corrected same draws. They contain no joint
success and lean heavily on the same optional encounter; nothing was filtered.
`targeted_examples.jsonl` explicitly uses parameter overrides to demonstrate
the success, restricted access, loss, and rejected-gift branches. These are
diagnostic examples, not random quality estimates.

## Round 2 Review

Implemented all five requests in the frozen GREENHOUSE_REVIEW.md without changing
the reference, sampled parameter distribution, scene IDs, or prior samples.
`shelter_parcel` now changes only parcel location. Mara and Ivo inspect the stay
and tape first. Mara declines either available tape or unwrapping for string,
believing relocation will be quicker. The sagging tray cannot carry its rooted
pots as a batch. Two fifteen-minute local actions free and move six pots each,
conserving all twelve: exposed becomes stressed, then damaged. Wind bruises
leaves before two stems snap in another gust; heat first wilts leaves, then
leaves two seedlings scorched but alive. All pots reach the lower bench. The
heat version also opens the door for air, with that state carried through to
departure. Failure is partial and consequential, not a toggle that kills plants
when a parcel moves. The usable-tape counterfactual still saves the plants and
can earn a key.

Watering now appears in sow prose before the ending's watered soil. Store prose
either shows a new request/opening before unwrapping the beans or identifies the
already-open borrowed tin. Local event order matches those handoffs.

The independent parent verifier was rerun read-only on the exact 100 frozen
positions. All pass; every path and outcome category is unchanged: 42 supervised
trials, 40 separations, 18 joint-care endings. Scene lengths there are 47-68 words.
There are 45 exact texts and 33 paths, still strongly repetitive; neither this
diagnostic nor the unchanged outcome counts establishes literary improvement.
The four consecutive seed-0/1 stories at both lengths were read in full, plus
all eight weather/tape/damp repair-and-settlement variants and both no-tape
failure variants.

New evidence lives in `round_02_samples/`: unfiltered seed-0/1 first draws,
explicitly targeted parameter variants, the same-position mechanical summary,
and hashes of preserved earlier samples/reference. Previous sample files remain
untouched. No shared-library changes are proposed.

## Diagnostic Parameter Recipes

These are explicit overrides for inspecting outcomes, not first-draw samples,
frequency estimates or a replacement for the unfiltered distribution. Every
dimension is specified. `test_documented_diagnostic_recipes` checks all three at
both lengths. The seed only chooses compatible optional encounters here.

```python
from storyscenes.mini_adventures.greenhouse.world import Parameters, generate

recipes = {
    "joint_care": Parameters(weather="wind", tape=False, damp_seeds=False,
                             honest=True, receptive=True, strategy="patch"),
    "supervised_trial": Parameters(weather="wind", tape=True, damp_seeds=False,
                                   honest=True, receptive=False, strategy="patch"),
    "separation": Parameters(weather="heat", tape=True, damp_seeds=False,
                             honest=False, receptive=True, strategy="patch"),
}
for expected, params in recipes.items():
    row = generate(0, count=8, params=params)
    assert row["final_state"]["story.outcome"] == expected
    print(expected, row["story"], sep="\n")
```

The joint-care recipe sacrifices wrapping and earns shared access. The trial
recipe deliberately saves and plants everything but withholds independent access;
it is not a failure to repair. The separation recipe also repairs successfully,
but Mara's repeated lie prevents reconciliation. For a damaged-crop trial, use
`Parameters(weather="heat", tape=True, damp_seeds=False, honest=True,
receptive=True, strategy="shelter")`: the unused tape is a missed opportunity.
No sampling probabilities have changed.

## Round 3 Audit

The shelter reply explicitly names Mara as the speaker. Ivo's joining the relay
is now a separate event after her choice, not an automatic change to his plan
inside her decision event. The prose shows him joining before the shared work.
Store and joint-ending exchanges also identify the alternating speakers.

Tea now uncaps, pours, drinks and recaps in that order. Two half-cup servings
are conserved across flask, filled cups and `tea.servings_drunk`. After drinking,
the cups and flask are empty and the flask is capped. Omitting the vignette
leaves the full capped flask untouched. The prose says they drain their cups,
matching actual consumption rather than merely a first sip.

Auditing ordinary transfers also found that Ivo's exit was recorded after Mara
closed the door. In joint/trial endings, both now exit through the open door
before it closes; in separation he stays inside as narrated. Existing tin
borrowing/opening, paper placement, seed custody, watering and key transfer were
checked and remain enacted. `tin.borrowed` records permission received, not a
continuing debt: the tin stays on Ivo's bench/shelf. Gestures such as setting a
thumb on the bench are intentionally not given individual state keys.

New `round_03_samples/` evidence contains unfiltered seeds 0/1/3/6 at both
lengths, explicitly labeled recipe examples, same-position verification and
hashes of preserved prior evidence. The reference and older samples are unchanged.
The independent verifier passes all 100 frozen round-2 positions with unchanged
paths and outcome categories (42 trials, 40 separations, 18 joint-care endings).
All eleven positions containing tea now finish with empty cups and two consumed
servings. The eight full stories at seeds 0/1/3/6, both lengths, were read after
the changes. All twenty-four pack tests plus ten shared-review tests pass.

## Authoring Notes

The fixed spine has seven commitments: arrive, enter, confront, discover the
vent problem, choose a response, settle the beans, leave. Guards select local
alternatives from physical/social state; an eight-scene route adds one optional
encounter. New prose must describe the selected local actions, not borrow useful
events from omitted scenes. In particular, preserve the difference between
partial plant damage and total loss, and between a successful repair and
forgiveness. Use the diagnostic recipes to inspect those boundaries, then read
unfiltered complete stories so the recipes do not hide their prevalence.

Round 3 deferred helper adoption until parent release. Round 4 now uses the
approved `storyscenes.mini_adventures.local_play.LocalPlay` without editing it.
The pack-local `world.LocalPlay` subclasses it, supplying the two actor IDs and
the greenhouse validator. Only initialization and atomic action/trace recording
were replaced. `relay_pots`, the scene-local location precondition wrapper,
weather/custody/tea invariants, scene guards, outcome logic, search and prose
remain pack-local and unchanged.

### Minimal Local-Action API

For another author, the shared constructor is
`LocalPlay(state, *, actors, validate)` and the operation is
`act(name, requires=None, **changes)`. The instance exposes `.state` and
`.events`. Preconditions are equality mappings; changes set existing declared
state keys. The validator raises for scenario-invalid states. The helper copies
and validates initial state, applies `runtime.transition`, validates candidates,
then commits detached events containing `action`, `requires` and changed-field
`before`/`after` pairs. Failed conditions, invariants and no-ops commit neither
state nor events. Mutable input and trace payloads are detached; the helper does
not select scenes, enforce story-specific rules or render prose.

The greenhouse adapter already supplies actors and validation, so a local play
can be authored as follows:

```python
from storyscenes.mini_adventures.greenhouse.world import LocalPlay, Parameters, initial

play = LocalPlay(initial(Parameters()))
play.act("clear_gate_stone", {"gate.stone": True}, **{"gate.stone": False})
assert play.state["gate.stone"] is False
assert play.events[0]["changes"]["gate.stone"] == {"before": True, "after": False}
```

For a new pack, use its own subclass to pass its actors and validator, and keep
physical multi-action routines there. Do not move `relay_pots` or the greenhouse
rules into the generic helper. Exact replay, illegal-action atomicity, tea
conservation and door-order tests remain migration gates.

## Round 4 Release Verification

All 100 frozen round-3 JSON rows reproduce exactly as complete dictionaries,
including episodes, prose, parameters, final state and search counts, from both
serialized parameter overrides and seed-sampled parameters. Replaying every
serialized path also exactly reproduces its saved episodes. The independent
verifier and inventory checks pass on all 100. No migration defect was found;
no renderer, inventory, scene rule or sampling changes were needed.

```bash
.venv/bin/python -m unittest storyscenes.mini_adventures.greenhouse.test_world storyscenes.mini_adventures.test_local_play storyscenes.mini_adventures.test_review
```

All 45 tests pass: 26 greenhouse, nine helper and ten review tests. New adapter
tests verify inherited action delegation through the shared transition path,
the greenhouse actors, preserved event shape, rejection atomicity with an
existing trace, and initial invalid-state rejection without caller mutation.
`round_04_verification.json` records the exact-row results and preservation hashes.
Reference, renderer and inventory bytes equal the frozen round-3 source; all
historical sample hashes were preserved. No new story batch was exported and
the held-out 1000-1049 seeds were not sampled. Parent owns held-out runs, final
snapshots and full-repository verification.

## Honest Limits

The seven-scene spine is deliberately rigid. Encounter alternatives and outcomes
are meaningful, but this remains one authored reconciliation premise, not a broad
story generator. Parameters prescribe choices rather than modeling an autonomous
decision-making character. The two timed exposure batches are a bounded
symbolic model, not calibrated botanical timing or weather physics. Rooted pots
and the tray's brittleness are fixed scenario assumptions. Repair geometry is
specific to the notched stay and bracket, not a general material solver. Most
plants survive the failed choice; no long-term recovery is simulated.
Incidental gestures are not individually traced. Seed
custody is modeled as a batch, not individual bean counts. The original reference
has more emotional breathing room than short routes. No literary grade, human
approval, multi-turn QA, or cost advantage is claimed.

Next gate is the parent's independent matched/held-out source-tree checks and
complete StoryScenes suite. Fixed-spine repetition, the credibility of the slower
relocation mistake and the conditional Saturday visit remain matters for reading,
not proof supplied by exact replay. No broad diversity expansion is claimed.
