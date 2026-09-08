# Storyscenes authoring contract v1

Write warm, intelligent, playful stories for roughly ages 5–8. Ambitious plans
are welcome; physical impossibilities presented as clever solutions are not.
The child notices, experiments, asks, changes a plan, or changes an arrangement.
Other characters have their own needs and useful knowledge. No horror or sermons.

The build seed sets initial conditions and choices in a small theater. A shared
expert system selects a compatible composition of scenes reaching the goal.
Do not encode a predetermined story as step numbers, previous-scene IDs, or a
preselected route. Use physical/social state and actors' knowledge. At least two
different solutions/endings must be reachable across seeds. Candidate scenes
may be reused in more than one path. Include 8–16 scene definitions, about 5–10
selected events per run. Use 2–4 characters, a few props, and 2–4 interacting
kernels (such as ambition, observation, mistaken belief, care, cooperation).
World-seed knobs must change causal problems/solutions, not just names/colors.

## Simulation API

Only import `random`, `math`, `itertools`, `collections`, `runtime` as needed.
Return Python source defining `build(seed: int) -> WorldSpec`.
Use `rng = random.Random(seed)` inside build. No global RNG mutation, I/O, API,
dynamic imports, exec/eval, files, or subprocesses. No prose renderer yet.

```python
from runtime import WorldSpec, Scene, Condition as C, Effect as E, Rule
from runtime import observe, tell, transfer
```

- `WorldSpec(title, entities, initial, scenes, goal, rules=(), labels=None)`
- `entities`: dict of ID -> `{ "name": "Ada", "kind": "child" }`. Include
  physical places, props and groups as well as people/animals. Use fixed IDs.
- `initial`: FLAT dict of scalar values. Every key starts with an entity ID and
  a dot. Declare EVERY property/knowledge slot before it can be used. Examples:
  `"ada.memes.Curiosity": 2`, `"ada.knows.bell.stuck": None`,
  `"bell.stuck": True`, `"bell.owner": "keeper"`.
- `C(key, op, value)`: comparisons `eq, ne, lt, le, gt, ge, in, not_in`.
  Values are constants, NOT references to other keys. Conditions are ANDed.
- `E(key, value, op="set")`: set a constant; `inc` adds a number;
  `copy` reads the named source key from the PRE-state. Multiple effects on the
  same key within one scene are invalid. Atomic changes must preserve all rules.
- `Scene(id, kernel, actors, requires, effects, summary, weight=1.0, max_uses=1)`:
  actors is a tuple of existing entity IDs. Requires/effects are tuples. Summary
  is a short factual clause describing the action, useful for debugging and QA.
  Weight is a positive number. No-op scenes are not eligible. Every scene needs
  a physical carrier; drive decisions from accumulated memes where relevant.
- `Rule(name, must, when=())`: if ALL `when` conditions hold, ALL `must` must
  hold. Empty when means always. Apply initial and after every atomic scene.
- `goal`: nonempty tuple of conditions, initially false, must become true.
- `labels`: optional human-readable labels for state keys (used in audit QA).

The solver knows all state but characters do not. Guard deliberate decisions
with the knowledge they require. Knowledge must arise from observation or
communication. Built-in kernels below compose with custom scenes; USE at least
one of them in this world. Initialize their knowledge/ownership keys first.

```python
observe("inspect_bell", "ada", "bell.stuck",
        requires=(C("ada.memes.Curiosity", "ge", 1),),
        summary="Ada inspected the bell")
# Copies bell.stuck into ada.knows.bell.stuck.
tell("explain_bell", "ada", "keeper", "bell.stuck",
     requires=(), summary="Ada explained what she found to the keeper")
# Requires ada.knows.bell.stuck != None; copies that belief to keeper's slot.
transfer("lend_rope", "keeper", "ada", "rope",
         requires=(C("keeper.memes.Care", "ge", 1),),
         summary="The keeper lent Ada the rope")
# Requires rope.owner == keeper; sets its one owner to ada.
```

Observe can happen only where direct inspection makes sense; add location or
access guards when required. Tell is allowed to transmit an outdated belief;
it does not magically synchronize reality. Custom scenes can change meme
magnitudes, relationships, ownership, physical state, needs and accomplishments.
Prefer reusable scene preconditions over branch-specific lists of paragraphs.

## Prose stage API

The simulation is frozen and supplied with three actual validated executions.
Write a complete `generator.py` importing `build` from `simulation`. You may
not redefine or alter build, the scenes, constraints, or runtime. Required:

```python
from simulation import build
from runtime import solve, realize

def render(run, rng):
    # run is a dict: title, entities, initial, final, events, labels, seed, goal.
    # Each event has id, scene, kernel, actors, summary, causes, before, after,
    # requires, changes={key: {before: old, after: new}}.
    # Compose rich prose ONLY for events actually present, in trace order.
    # Return paragraphs, not a single string.
    ...

def generate(seed, prose_seed=None):
    return realize(solve(build(seed), seed), render,
                   seed if prose_seed is None else prose_seed)
```

Each paragraph has EXACTLY `text` (nonempty string), `event_ids` (list of integer
event IDs), and `kind` (`beginning`, `scene`, `ending`). First is beginning; last
is ending. All actual events must be covered; scene/ending paragraphs must cite
their events. Ending cites the final event. Beginning may cite no events.
Do not mutate run. A prose seed may change wording but never physical events.

Aim for 250–450 words in each complete story, natural connected prose, lively
dialogue with responses, small expressive details, a consequential turn, and a
final concrete image proving what changed. Avoid one-sentence event logs.
Use event before/after state so independent scenes do not introduce contradictions
when reordered. Do not narrate absent actions or know facts before learning them.
Refer back to preceding events when justified; shared scene fragments should
still feel like one story. An imagined plan is not a completed action.
Implement every scene ID, including paths absent from the three preview runs.
Endings should reflect the actual final arrangement, not a universal happy line.
Do not emit model commentary, source fences, raw state keys, or audit terminology.
