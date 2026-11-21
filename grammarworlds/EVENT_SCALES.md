# Event scales and world time

The joined twenty-world pool now has three authored episodes per source story,
covering all 249 fine-event kinds. Source documents remain intact. Their tokens
link to a story goal, an episode, an entity-specific event chain and the existing
fine event. Chains are participant threads derived inside an episode; they do
not yet constitute independently authored causal subplans.

This is opt-in at runtime:

```bash
.venv/bin/python -m grammarworlds.storytelling --scenario repair --seed 7 --multiscale --json
.venv/bin/python -m grammarworlds.event_scales_experiment --out /tmp/scales-audit
```

## What the annotations mean

`event_scale_bank.py` names goals and episodes, lists their fine-event membership,
records completion predicates/capabilities, and supplies approximate duration
bands. `event_scales.py` carries these commitments on physical entities and
updates them from native execution. Missing carriers block their commitments;
merely narrating an intention does not achieve them. Story completion requires
physical state predicates and the native source ending. Episode completion
requires one of its actual terminal events. Chains currently inherit their
parent episode's completion condition.

Before a token is sampled, its candidate attribute bundle includes:

- Story/episode/chain membership, physical carrier and current status.
- The candidate event's duration distribution and current world time.
- Contribution relations and, when present, the receiver's persistent mission.

END candidates include these attributes too, including for silent events.
Retrospective source annotations are marked `completed_source_observation`;
predictions use `receiving_prefix`. Neither historical final states nor predicted
success are substituted for the receiving world's present state.

The clock samples a duration once per committed fine event, using a separate
deterministic random stream. Representative durations are 5 seconds, 1 minute,
1 hour and 1 day. Pottery drying/firing/cooling and biscuit baking have explicit
longer-duration distributions. These are authored estimates, not empirical time
measurements. Higher-level duration distributions are descriptive priors and
are **not** added again. Events run serially; overlap and calendar scheduling
are not implemented.

Commitments have proposed, active, achieved, blocked and abandoned states,
optional absolute deadlines in seconds, and persistence metadata. Abandoned
commitments stay abandoned. Achievement reflects current completion predicates;
if a required physical state is lost, that commitment becomes unresolved again.
An achieved but late receiving mission is explicitly marked overdue and does
not count as an on-time success.

## Choosing a next episode

`scale_continuation.py` provides a classical, bounded lookahead sampler:

1. Enumerate observed source prefixes ending at annotated episode boundaries.
   Duplicate observations do not increase their sampling weight.
2. Infer physical bindings using native transfer. Explicitly record imported
   props and character attributes. Already-started compatible prefixes can
   resume with the same carrier bindings and remaining fine events.
3. Preview the native guards/effects on a clone. Compute actual progress on
   receiving goal predicates, not just tag overlap.
4. Rank feasible alternatives and sample a normalized distribution. The
   contextual weight is:

   `(1 + 200 × newly_met_needs + 2 × completed_source_goals)`
   `× (0.001 + probability_of_finishing_before_deadline)`
   `/ (1 + 0.1 × new_event_count + 0.05 × imports)`

5. Execute the selected program with the existing word/attribute sampler,
   advance time, refresh the goal and repeat. STOP has weight 0.02 while the
   goal is unresolved; once achieved, STOP is the only option. Deadlines,
   missing goal carriers and episode limits can also terminate a run.

Weights are hand-authored. The baseline samples feasible alternatives uniformly.
Both policies retain native guard checks and the same source prefix space.
Duration fit uses the convolution of fine-event duration distributions; it does
not peek at the eventual sampled clock outcome.

The receiving goal is an explicit graph of named needs, physical predicates,
capabilities and optional prerequisites. It is **not** inferred from free text.
For example, the experiment asks for a working trolley, a controlled shadow,
and then a performance. No source story names or event order are supplied.
A capability is credited only after an episode really completes on the goal's
carrier and starts after its prerequisite needs were met. Merely importing a
`performance` label is insufficient.

## What remains limited

A selected episode may include its entire prerequisite prefix. Fine-event order
inside it remains the observed native order. Partial source goals can remain
open once the receiving mission finishes. The combined prose can still read as
linked mini-stories, with donor motives leaking between them; the receiver's
long-range goal is not consistently realized as a shared opening and ending.
The test demonstrates better goal-directed selection on a designed fixture,
not general planning or improved literary quality. No runtime LLM is involved.

The implementation follows the memeplex north star by attaching commitments to
physical carriers and using executed state to accept/reject prospective moves.
It does not yet implement general composition of abstract goals as memeplexes.

Tests: `test_event_scales.py`. Measured examples and full distributions:
[runs/event_scales_20261108/report.md](runs/event_scales_20261108/report.md).

## Providing a coarse outline

`coarse_outline.py` accepts a list such as:

```python
[
    {"name": "Find a safe route", "offer": "safe_route"},
    {"name": "Make a drawing", "offer": "artwork"},
]
```

`generate_outline(pool, events, seed=7)` starts with Nia, Omar and a workshop,
compiles the list to ordered coarse needs, and uses the existing sampler to
choose guarded source programs. No fine-event sequence or prop bindings are
supplied. The `offer` values are typed capabilities from the current bank;
display names are not parsed as English instructions. A single source program
can fulfill multiple successive coarse events. Sampling can also take detours.

Run the three-outline/two-seed probe with:

```bash
.venv/bin/python -m grammarworlds.coarse_outline --out /tmp/coarse-outlines
```

[Raw generations and inspection](runs/coarse_outlines_20261108/report.md) show
both coherent source reuse and abrupt cross-source combinations. Coarse events
currently share a protagonist, but do not require shared patients or recipients:
`adapt → gift` can adapt a costume and give a biscuit. Explicit shared role
bindings are the next useful constraint to add.
