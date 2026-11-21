# Story beats on annotated text

Beat annotations cover the twenty source worlds without changing their text.
The optional generation grammar adds reactions, dialogue, inspection and
reminders inside native scenes. It uses the same annotated-word distribution as
the rest of the story, not a prose rewrite after generation. No runtime LLM.

## Use

```python
from grammarworlds.storytelling.runtime import generate, replay
from grammarworlds.story_memory import annotate

row = generate('pottery', 211, beat_budget=2, continuations='expanded')
print(row['presented_story'])
replay(row)
document = annotate(row)
```

Source generation now attaches `title`, `presentation`, and `presented_story`
by default; `story` and `raw_story` retain the exact generated body. The CLI and
experiment reports display the framed version. Use `--raw` at the CLI or
`presentation=False` in Python to omit framing. Joined plot results use
`story` for the complete framed plot and `raw_story` for its body; their native
rows remain raw. `presentation.body_offset` / `body_length` locate that body.
Framing uses a separate random stream and adds no physical events.

`beat_budget=0` (the default) disables expansion and preserves baseline native
generation. Two is a useful short-story cap; six allows more room. This is a
maximum, not an insertion quota. Integer budgets from zero through twelve are
accepted. The last slot is reserved for a previously planted detail when one is
available; the sampler may still choose immediate action and spend no slot.

```bash
.venv/bin/python -m grammarworlds.storytelling --scenario museum --seed 103 --beat-budget 6 --continuations expanded --qa
.venv/bin/python -m unittest grammarworlds.test_beats -v
```

For the joined pool, use `plot_continuation.run(pool, 'changed_approach',
seed=19, beat_budget=2)`. The budget, detail memory and used triggers persist
across resumed stages. Entity references are receiving-world IDs.

## Existing text annotations

`annotate(row)` adds `event.beats` and token `memory.beats` as scene context.
The six kinds are `expectation`, `interruption`, `reaction`, `discovery`,
`choice`, and `payoff`. Supporting logistics can have an empty list rather than
an invented dramatic function. Each reading records an `experiencer`, relevant
`object` where known, `preceding_event`, `speech_act`, evidence scope and basis.
The native readings are authored interpretations of existing event roles.

Actual additional beats are distinguished with `phase='pre_event'`; native
scene readings have `phase='native_scene'`. Token `memory.beat_candidates`
retains the conditional beat interpretations and probabilities of that token.
This avoids calling every word in a compound scene a reaction just because
the scene starts with one. Live token bundles also carry `beat` context before
sampling; they do not contain future observed consequences.

The [full annotated pool](runs/beats_20261115/annotated_pool/summary.json)
preserves original prose, token positions, candidate attributes and posterior
probabilities. The exporter replays archived frames and verifies their physical
effects. For previously expanded stories, it applies the **recorded** beat
choices and restores their recorded detail ledger. It checks archived weights
for internal consistency, without pretending those weights are today's policy.
Archives with complete narrative snapshots are checked against them; old native
archives explicitly report the narrower physical-replay scope.

## Expansion and state

After a narrated setback, available constructions include hesitation, looking
closely at the affected object, asking a nearby helper, and immediate action.
The object comes from the setback and must have appeared in narrated references.
A hidden frame patient is insufficient: the library's unmentioned mitten must
not become the subject of an inspection. A general reaction may instead refer
to a previously introduced central object. An unrevealed physical failure is
not automatically a reader-visible setback.
Inspection requires physical access; dialogue requires a co-located listener.
Inspection records attention but does not manufacture discovery or knowledge.

After a discovery, a protagonist's next compatible action can be preceded by
a commitment or suggestion. An authored `uses_discovery` link can carry that
connection across intervening logistical events. There is at most one voiced
proposal per discovery. The utterance names an accessible tool or a grounded
transfer, such as “I will give you the lantern”; there is no generic “another
way” fallback. If the native scene already voices that character's choice,
the additional generic commitment is suppressed. Native dialogue annotations
also distinguish suggestions, disagreement and admissions. Concealment is not
invented without a supporting knowledge/visibility model.

Weights are positive authored preferences, normalized with the immediate-action
alternative. Previously used forms are downweighted. Every sampled word records
its distribution. `beat_decision` records the candidates and selected form;
`World.narrative.beats` records budget use, detail memory, executed beat history
and actual speech acts. Requests are recorded as uttered, not automatically
answered. Attention/caution changes attach to the physical experiencing person.

A pre-event beat and the following native action execute as one atomic scene.
The native action's guards and physical effects remain authoritative. Replay
recomputes beat eligibility and compares the recorded distribution before
applying the selected beat. These are not independently scheduled physical
events, and they currently share the native scene's time estimate.

## Concrete details and endings

Sixteen authored detail mappings currently cover thirteen worlds:

| Source | Details |
|---|---|
| Pottery | Grandpa's stiff hand; the dent |
| Cart repair | The locked wheel; the rattle |
| Museum | The moving light; the large shadow |
| Greenhouse | Broken shade cloth → repaired cloth |
| Library | Missing book → found book |
| Snow | Stuck sled → freed sled |
| Picnic | Unsteady basket → secured basket |
| Market | Underweight bag → corrected weight |
| Camp | Missing rabbit → freed rabbit |
| Orchard | Bending branch → unbent branch |
| Costume | Tripping cape → safe cape |
| Pond | Snagged net → freed net |
| Festival | Blocked gate → cleared gate |

Detail memory records a **visible** setup event and its physical state. A later
reminder needs that setup, the same entity and a currently satisfied state check.
It can mention the dent becoming a thumb rest, or the previously moving torch
staying still. Each source arc gets at most one explicit reminder from the expansion grammar,
even if it has several motifs. A joined continuation retains the earlier setup's
receiving entity and actual state. Such inherited setups have
`setup_in_document=False` and an explicit `prior_setup_events` record; they do
not acquire invented local text evidence.
Historical `detail_links` separately record authored setup/result associations
and the replayed result state. Those links are not proofs that the prose already
expressed the relationship elegantly.

Beat QA validates the selected decision against executed memory and uses the
actual selected utterance/action plus earlier text evidence. The later evidence
span stops at the beat, before the native action. Proposals can cite the earlier
discovery rather than unrelated intervening logistics. `presentation_evidence`
explicitly maps raw evidence into the displayed story. A resumed segment cannot answer a callback question whose setup text
is outside that segment. Native QA remains available alongside the new checks.

## Typed token attributes

Schema `story-beats-v2` keeps the scene reading separate from each candidate's
own interpretation. `memory.beat_candidates` retains the original attribute ID
and exact probability; its reading follows that alternative's event, not the
completed scene. Native readings distinguish `action_actor` from the human
`experiencer`; speech readings require actual authored speaker evidence.

Optional constructions supply authored POS, lexical lemma, clause subject,
action arguments, semantic scope, hypothetical status and setup evidence.
In “Let us try the torch,” the verb and object share the embedded proposal;
in “safe to wear,” the cape is the object and the wearer remains unspecified.
These are grammars for known constructions, not an English parser. Unknown
vocabulary/constructions remain explicitly unresolved. A within-scene reference
pass requires a name after a known subject change; it does not solve arbitrary
cross-scene coreference.

## Evidence and limits

The [November 15 campaign](runs/beats_20261115/REPORT.md) adds ten actual
code-and-sample refinement rounds after a separate presentation preflight.
The [November 13 campaign](runs/beats_20261113/REPORT.md) remains historical
evidence; its original test count is not a claim about today's code. Reports
include framed text, nearby-length baselines, QA, decisions and source snapshots.
Closest-length baselines are not always within 10% of the expanded word count.
No Luna or calibrated literary-quality evaluation was run in this pass.

The shared reaction/dialogue grammar applies across the twenty-world bank.
Seven worlds still have no authored concrete motif. Authored source plots
dominate story structure; general cross-source plot invention is not established.
Some reactions remain generic, callbacks can repeat a nearby result, and
cross-scene pronouns can remain ambiguous. Beat syntax and state validation
make these problems inspectable; they do not establish better storytelling.

The next useful quality gate is whether a beat adds new narrative information
at matched length: a decision with a cost, a consequential character reaction,
or a payoff that transforms an earlier detail. More repeated state descriptions
should not count as progress. Such additions need authored causal evidence and
carrier state before they can influence the word distribution.
