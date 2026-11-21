# Authored storytelling prototypes

`edition='crafted'` opts into rewritten pottery, music and greenhouse stories.
The default twenty-world generator is unchanged. This experiment invests in
content: concrete wants, conflicting needs, choices with costs, and endings that
show what those choices changed. It does not claim a general plot planner.

```bash
.venv/bin/python -m grammarworlds.storytelling --scenario music --edition crafted --seed 19 --qa
.venv/bin/python -m grammarworlds.storytelling --scenario pottery --edition crafted --story-choice remake --seed 19 --qa
.venv/bin/python -m unittest grammarworlds.test_storycraft
```

The three authored decision sets are:

| World | Branch events | Persistent distinction |
|---|---|---|
| Pottery | `keep_dent`, `remake`, `make_bowl` | Visible thumb hollow; wider handle arriving after the birthday; original cup shape abandoned for a bowl. All reveal the surprise. |
| Music | `choose_private`, `choose_solo`, `choose_written` | Public slot surrendered; public performance without a partner; partner's written rhythm performed with promised credit. |
| Greenhouse | `choose_share`, `choose_flower`, `choose_seedlings` | Shared water requires tending shade; flower-first leaves a browned leaf; seedlings-first leaves the flower dry. A finite can and unavailable helper prevent an effortless reset. |

Without `choice`, the existing word sampler samples these event alternatives.
`care` and `pride` in the Python API influence event probabilities through
existing grounded attention scoring. They do not override physical guards.
`choice` conditions a branch before sampling rather than forcing an impossible
execution. Different seeds also select local equivalent wording variants.

## What executes

The small adapter in `storytelling/revisions/engine.py` compiles authored event
specifications into existing `World`, `Frame`, kernels and word forests. It
tracks physical entities, concept magnitudes, prerequisites, mutually exclusive
choices and narrative obligations. Invalid bindings are rejected at authoring;
stale frames, missing physical prerequisites, absent interlocutors and unpaid
ending obligations are rejected before mutation.

Every physical operation still executes, including drying/firing/cooling that
has an empty surface. The reader receives a short transition instead of a
procedural list. All generated text comes from the sampled grammar; no model or
English rewriting runs at generation time. Consistent with `story.py`, choices
and effects have physical carriers, and concept magnitudes influence compatible
moves rather than appearing as bare abstract nouns.

An obligation becoming `resolved` means the story has addressed it, **not** that
the initial wish succeeded. A public-duet wish can resolve in a solo ending. The
recorded physical states and final image distinguish fulfillment from giving up
or changing the goal. Cost and motivation descriptions are authored readings;
they are not a learned utility function or automatically inferred causality.

## Live annotations and QA

Candidate tokens carry `storycraft` metadata: narrative function, desired
outcome, motivation, proposed cost, prior event IDs, causal predecessor IDs and
open obligations. This context is built from the prefix world. It never exposes
future realized states as current facts. Obligation guards affect eligibility;
existing attention weights affect the distribution over compatible choices.

Authored utterances also carry `speech_act` (name, speaker, listener and
`candidate_utterance` scope), and fragments carry `narrative_role`. A request or
promise does not execute its proposed action. Separate events and state guards
implement answers, permission, door closure and public credit.

These are **fragment-level semantic annotations**. Some fragments contain
several clauses; their supplied subject/predicate describes the fragment and is
not a complete parse of every word. `action_scope` and `annotation_status` say
`authored_fragment`. Unknown lexical POS remains `X`; references, determiners and
speech framing receive supported tags. Do not treat this as exhaustive tagging.

QA comes from selected scene claims with transitive support links. Tests check
that citations include actual writing, waiting, closing, asking and helping,
rather than only intentions. Exact offsets are checked separately from semantic
review. Presentation preserves the raw story and evidence offsets; authored
titles and the native opening avoid redundant introductions.

## Evidence and limits

See [the experiment report](runs/storycraft_20261116/REPORT.md), archived samples,
and the independent development reviews. The rewritten stories are substantially
longer than the originals. A preference for these examples does not isolate a
benefit from the architecture, attention heads, or equal-length prose.

A sixty-story unconditioned audit reached all nine branches, but only about
2–4% of word steps had multiple surface options. These are three rich authored
story families, not free plot improvisation. Local wording variation is much
larger than variation in the underlying event paths.

The prototype supports past tense and the three named worlds. It does not yet
combine with the original optional beat, multiscale or plot wrappers, nor is
transfer into the joined twenty-world pool established. Those unsupported
combinations are rejected explicitly. Existing symbolic word heads can run,
but only a smoke check was done; no quality benefit is claimed.

Next useful work: factor the successful decision structures into reusable
constructions; widen grounded realizations; add character-specific beliefs and
uncertainty; compare equally concise stories with and without those structures.
Keep less generous or less successful choices available when their motives and
consequences are coherent. A beat count is not a quality measure.

## Decision beats — 2026-11-19

The optional shared decision policy now makes appraisals, dialogue commitments,
payoffs and repetition affect generation. It uses the same three crafted worlds:

```bash
.venv/bin/python -m grammarworlds.storytelling --scenario music --edition crafted --decision-beats --seed 19 --qa
.venv/bin/python -m grammarworlds.storytelling --scenario music --edition crafted --decision-beats --appraisal appraise_together --seed 19
.venv/bin/python -m grammarworlds.storytelling --scenario greenhouse --edition crafted --decision-beats --no-compression --seed 19
```

Python: `generate('music', 19, edition='crafted', decision_beats=True)`.
`appraisal` conditions an interpretation, while `choice` separately conditions
an eventual branch. Without either constraint, both are sampled distributions.
This policy is opt-in; the prior crafted edition and original twenty worlds
retain their existing behavior.

- **Appraisal:** three authored interpretations per world become executable
  events after visible evidence. They write bounded `Decision_*` priorities onto
  the appraising physical character. Later choices add `1.5 × priority ×
  forecast_stake` contributions to their logits. Stakes are authored expectations,
  not future facts. Existing attention scores still contribute; `attention=False`
  disables both scoring contributions for an ablation. No branch is forced by
  appraisal, and hard physical prerequisites remain authoritative.
- **Costs:** a separate ledger records costs only when their required carrier
  states hold after the selected action. Anticipated costs and observed costs
  are distinct. Public credit is tracked as fulfilled dialogue; the written-music
  branch's cost is the absent public duet partner, not giving someone credit.
- **Dialogue:** typed utterance constructions record the actual speaker,
  listener and act. Subsequent frames can require that recorded utterance even
  when physical flags happen to match. Responses and fulfilled promises link to
  their earlier utterance; saying the door will close does not close it.
- **Payoffs:** a carrier-bound detail must have been visibly introduced, and
  current physical state must support its changed meaning. The original setup
  event is preserved through reminders. Invalid or absent setups block a payoff.
- **Compression:** the grammar tracks meanings already expressed to the reader.
  A reminder about the same carrier and meaning gets weights `say=0.15`,
  `omit=1`, a 13.0% conditional chance of being repeated. Without compression the
  two weights are equal. A new meaning or different carrier must be expressed;
  important actions and costs sit outside the optional reminder. The greenhouse
  explanations about waiting or risk are retained when appraisal has not already
  supplied them. This is explicit semantic tagging, not paraphrase detection.

The reusable mechanism is `storytelling/revisions/decision_policy.py`; its
current story bindings and sentences are in `decision_bank.py`. Candidate token
attributes include proposed appraisal, forecast stakes and earlier observed
costs. Observed appraisals, dialogue links and payoff links also survive
`story_memory.annotate`, with `replayed_source_event` scope. They are not relabeled
as prefix-time predictions. Exported local event lines still are not permission
to execute an event independently.

This follows the memeplex north star: interpretations influence choices through
magnitudes carried by physical characters, and narrative consequences stay
bound to concrete objects and actions. It does not implement general beliefs,
learned appraisal, arbitrary transferred plots, or a transformer attention head.

[Experiment and completion evidence](runs/decision_beats_20261119/REPORT.md)
include paired prose, probability interventions and compression ablations.
