# Executable receiving plots

The plot annotations now participate in event selection. Two explicit receiving
contracts are implemented over the twenty-world pool:

- `adapt_gift`: establish a desire → adapt an object for its user → give that
  same object to that user → demonstrate the useful result.
- `changed_approach`: establish a desire → fail → discover why → change the
  approach using that discovery → achieve the goal → show the changed world.

These are local reusable trajectories, not implementations of every stage of
all nine archetypes. Inputs specify the contract, not donor stories or native
event names. The existing native guards remain authoritative for every action.

## Shared identities and stage contracts

`plot_execution.py` stores receiving state under `World.narrative.plot_execution`.
The state has a physical `carrier`, `bindings`, an `active_stage`, and `stages`
with allowed narrative roles, conditions, predecessor requirements, status and
evidence. The first accepted setup binds a source's central target to `object`;
the gift contract also binds `recipient`. Both must remain the same physical
IDs throughout the plot. Renaming a cup to a bowl preserves its identity.

Recipient inference uses a uniquely named recipient, beneficiary or partner in
the source plot annotation. It does not guess among ambiguous people. Optional
initial `bindings` constrain candidate matches; they do not override native
compatibility or force arbitrary source roles onto unsuitable objects.

A role label alone cannot satisfy the principal physical stages:

- Adaptation requires an actual change to the bound object and an authored
  adaptation capability on that source episode.
- Giving requires the object's actual location to change to the bound recipient,
  who must be a person other than the protagonist. Packing a gift into a tin
  is not enough.
- Failure/changed approach require relevant physical changes. A changed approach
  must reference an earlier discovery through an authored `uses_discovery` link.
- Discovery must link to an executed setback of this receiving plot.
- A payoff must have an actual change plus either a setup link or satisfaction
  of the source goal's physical checks.
- The ending must satisfy physical source-goal checks and refer to earlier plot
  progress, or demonstrate a relevant physical change itself.

Each event can advance at most one stage. Supporting events still run with their
ordinary guards. Their labels do not create extra plot progress.

## Obligations, knowledge and narration

The setup opens a `resolve_initial_desire` obligation with the bound identities
and setup event reference. A valid payoff/gift resolves it. The ending is a
separate stage, so an obligation being resolved does not by itself finish the
narrative contract.

`knowledge_evidence` records actual clue/discovery events related to the setback.
`character_knowledge` records only new native entity states named `knows_*` or
`understands_*`, with the event that introduced them. Authored discovery labels
are not treated as proof of arbitrary character beliefs. `reader_knowledge`
records narrated event exposure and typed referents; it is not a comprehension
or hidden-information inference model.

Each stage opens a `narration_requirements` entry. Once the ordinary word sampler
has rendered the event, the generator supplies its actual narration flag and
typed entity references. The stage must have visible text referring to a
relevant carrier. Final images require a relevant object/recipient/instrument,
not just a protagonist mention. An unbound recipient/beneficiary also qualifies
when that ending actually changes their physical state (for example, Grandpa's
thumb resting in the newly shaped cup). A physically complete plot with a silent or
unrelated milestone is marked `narration_incomplete`, not successful.

No English text is parsed to manufacture state changes, and no connective prose
is appended after generation. These checks are a minimum narration gate, not a
style score or a guarantee that every causal link is explicitly verbalized.

## Selection and lookahead

`plot_continuation.py` uses distinct observed native source branches. For each
possible attachment it previews the native program on a clone, including plot
stage updates. It rejects shared-binding mismatches and candidates with no
stage progress. By default it also requires that the remaining native suffix
could complete the plot. This avoids choosing a costume adaptation when no
available continuation gives that same costume to its intended recipient.

The selected program is cut at the **next** stage boundary and regenerated with
the normal word/attribute sampler. The next selection starts from the resulting
world and can resume the same prefix. One full source branch is not silently
counted as several already-executed choices.

Feasible current prefixes are deduplicated so repeated observations or multiple
identical-prefix future branches do not inflate their probability. Their weight
is `(4 if resumed else 1) / (1 + .10 × new_events + .05 × imports)`, multiplied
by `.001 + P(remaining native suffix fits the deadline)`. Weights are normalized
before sampling. These are authored weights, not learned parameters.

The suffix-completion requirement strongly favors coherent reuse of an existing
source arc. It is bounded lookahead, not a general cross-source planner. Turn it
off with `lookahead=False` to expose binding dead ends rather than hiding them;
the physical stage checks still apply.

Live candidate attributes contain `plot.receiving_plot`, which is a copy of the
**current** receiving state. Preview outcomes stay in the selection audit and
are not inserted as observations into the token context. Timing, source-native
replay and physical guard rejection continue to work.

## Running and resuming

```python
from grammarworlds.story_memory import load_documents
from grammarworlds.plot_continuation import catalogue, run

pool = catalogue(load_documents('grammarworlds/runs/plot_annotations_20261108'))
result = run(pool, 'adapt_gift', seed=19)
print(result['story'])
print(result['plot'])
```

For a saved partial receiving world, pass its prior native units with
`previous=result['units']` so the sampler can resume rather than restart source
prefixes. `run` returns the current `final_world`, stage decisions, token-level
rows, obligations, knowledge and narration evidence. Calling `set_plot` on a
world that already has a plot is rejected rather than resetting its progress.

```bash
.venv/bin/python -m grammarworlds.plot_execution_experiment --out /tmp/plot-execution
.venv/bin/python -m unittest grammarworlds.test_plot_execution -v
```

See [the generated examples and matched-pool comparison](runs/plot_execution_20261109_v2/report.md).

## Titles, openings and closings

As of 2026-11-10, `plot_continuation.run` presents the assembled story by default.
The separate `story_presentation.py` grammar samples a title, opening and closing
word by word through `AttributeForest`. It records normalized word/attribute
distributions, authored style weights, entity references and narration roles.
Presentation has an independent random stream and never commits native events.

Traditional openings ("Once upon a time"), everyday openings ("One day"),
storyteller introductions and immediate starts are available. Closing forms
include "The End", a storyteller sign-off, or the existing final image. The
empty immediate/final-image forms leave the body boundary intact instead of
repeating its first/last event. Unfinished plots receive continuation wording;
empty generations receive no title/opening/closing.

`result['story']` contains the presented text; `raw_story` retains the intact
generated body, and native `rows` retain their original token offsets, QA and
replay semantics. `presentation` contains the three component traces and
attribute tables. These are framing annotations, not new physical event facts.
Titles may use the final object name; introductions use initial identity and
location. No unsupported weather, habits or future outcomes are invented.

```python
raw = run(pool, 'adapt_gift', seed=19, presentation=False)
from grammarworlds.story_presentation import present
classic = present(raw, opening_style='traditional', closing_style='the_end')
print(classic['story'])
```

See [eight presented examples](runs/story_presentation_20261110/report.md).
Reproduce them with `python -m grammarworlds.story_presentation_experiment
--out /tmp/story-presentation`. Framing improves presentation, not the measured
quality or completion status of the underlying plot.

## Remaining limits

Shared bindings are currently object/recipient bindings, not a full general
unification language. Source target/recipient interpretation is authored. The
stage contracts rely on authored narrative dependencies in addition to native
physical checks; they do not infer a causal theory from arbitrary English.
General beliefs, expectations, hidden motives, hypotheses, calibrated tension
and learned plot weights remain future work. The reader-exposure and narration
gates do not establish literary quality. Source-derived motives and props can
still leak, and coherent single-source reuse is not new plot invention.
The inspected samples also retain source-level narration weaknesses: a helper
can appear without an introduction, and a discovery's causal explanation may
remain implicit in the prose even when its event link is recorded.

This moves toward the memeplex design by keeping the plot's influence attached
to physical carriers, sharing their identities across composition, and advancing
only through compatible executed changes. No runtime LLM was introduced.
