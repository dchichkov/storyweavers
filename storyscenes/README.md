# Storyscenes

An isolated prototype for **seed → theater → executable scene constraints →
three validated previews → conditional prose**. All current authoring and repair
uses **gpt-5.6-luna**. Finished generators use Python's standard library and make
no API calls. Older engines and scripts are untouched.

The [mini-adventure design write-up](MINI_ADVENTURES.md) explains the two-level
approach and its current limits. The hand-authored
[prototype](design/mini_adventure_20261023/README.md)
tests a different scale: roughly fifty-word locally simulated scenes, selected
into coherent seven- or eight-scene routes through a shared world. It includes
five saved stories, optional vignettes, physical parameter variations, three
compatible endings, and replay tests. It is isolated from the existing factory;
no paid judging or training-data quality claim accompanies this prototype.

The opt-in [compact authoring path](COMPACT.md) moves world definitions into a
small data compiler: reusable role-bound patterns compose with `+`, `/` controls
selection weight, and the library derives knowledge/loan bookkeeping and named
prose slots. It avoids asking Luna to write both a prose plan and Python mechanics.
See [AUTHORING_COMPACT.md](AUTHORING_COMPACT.md) for the executable format.

The older capability and long-scene experiments are preserved as a
[negative-result checkpoint](EXPERIMENT_RETROSPECTIVE.md): mechanical correctness
and high judge scores did not establish convincing, diverse, economical story
production. The following results retain their historical protocols; they are
not a recommendation to scale those generators.

The opt-in [capability worlds](CAPABILITIES.md) implement separate physical
custody/ownership, timed evidence and beliefs, and requests/promises/refusals.
They use one versioned schema and offline runtime; existing worlds keep their
original semantics. All three bounded semantic slices are implemented and
[verified](design/capabilities_20261021/implementation/ACCEPTANCE.md); their
diagnostic prose is not yet a training-data quality pass. A
[matched Terra/Luna evaluation](runs/capability_judge_comparison_v1/MANUAL_REVIEW.md)
confirms that: story quality is 2.67/9 versus 3.00/9 on 30 fresh selected outputs,
despite high literal QA scores. Both judges identify event-log prose and low
diversity; the total estimated grading cost was $0.126.
The subsequent [local prose pass](runs/capability_prose_review_v2/MANUAL_REVIEW.md)
adds selective narration, paragraph-grounded QA and story-specific ordering
guards. The CLI and new capability trials use it by default; `--diagnostic`
retains the conformance view.
The [second repair pass](runs/capability_prose_review_v4/MANUAL_REVIEW.md) gives
the three story profiles executable purposes and consequences: an atlas-assisted
inspection, a time-bound reading before delivery, and retrieval after a corrected
report. Its 90 runs replay, but each fixed profile produces one distinct story;
these are canonical examples, not a diversity multiplier.
The [revised paired evaluation](runs/capability_judge_comparison_v2/MANUAL_REVIEW.md)
now gives **4.00/9 from both judges**, with **0/9 diversity**. Clearer causality
helped, but the prose is still an event log. QA scores remain high (Terra 9.00 on
150/180 conversations; Luna 8.89 on all 180), not proof of story quality. Returned
grading cost was $0.106; one Terra QA request remains Flex-unavailable after one
retry. The [next prose experiment](CAPABILITIES.md#next-prose-experiment) compares
scene-level writing while holding simulated events fixed, before expanding plots.

The preserved [harbor storytelling experiment](runs/harbor_iteration_campaign/README.md)
tests scene-sized writing plus consequential goals. It now has
[complete hundred-story results](runs/replication_pooled_v1/FINDINGS.md)
from both judges: harbor **7.79/7.78**, greenhouse **7.94/7.94**, theater
**7.73/7.89** storytelling. Diversity remains **5/5**, **4/3**, **3/4**.
All 300 worlds replay, but there are only 147 exact texts; the pooled archive is
3.66% of raw text. A balanced ninety-story cross-script test scores diversity
**4/6**, not unanimous evidence of a good multiplier. High prose quality is
replicable here; meaningful structural diversity is still unsolved. All source/data
batches are preserved; generation is offline, and the same two judges share the
original $5 cap. This is hand-authored feasibility evidence, not demonstrated
automated production quality or a large diversity multiplier.

A [subsequent coupled-goal experiment](runs/harbor_iteration_v11_100/FINDINGS.md)
shares one physical rope between two characters' plans. It retains strong
storytelling (**7.82/7.96** on a fresh hundred), but diversity remains **5/4**.
Its new branch has only 16 possible texts on the audited parameter grid. This
is evidence that scene-level prose can work, not that adding parameters or
another hand-authored plot creates a large supply of distinct stories.

[Resource alternatives](runs/harbor_iteration_v14_30/FINDINGS.md) extend that
experiment with a clip, a relocated display, and a mutually released deadline.
Fresh thirty-story storytelling is **7.87/7.90**, diversity **5/4**. The expanded
branch still produces only 28 exact texts across its 1,152-configuration audit
grid. A fresh hundred replays locally but is unjudged. This strengthens the
case for a separate scene-level prose layer, not for scaling hand-authored
branch menus into a large corpus.

The opt-in [composed-goal prototype](runs/harbor_composition_v2_100_local/LOCAL_REVIEW.md)
uses bounded goal decomposition and actual resource dependencies: later work can
dismantle a display or move its light, and earlier goals must then be restored.
It executes and replays, but **does not yet solve diversity**: 576 configurations
produce only 48 texts, all ending with the same three goals satisfied. The new
hundred is unjudged (39 exact texts, 1.665% XZ ratio). Keep it as local research,
not a replacement for the scored baseline. Run it with
`python -m storyscenes.harbor_composition_story --seed 6001`.

[Persistent resource trade-offs](runs/harbor_tradeoffs_v1_10_local/FINDINGS.md)
now give those choices a lasting cost: keeping the rope or lantern for one
goal can prevent another. Terra/Luna storytelling on ten is **7.8/7.9**, but
diversity is only **3/4**. The unjudged hundred produces 70 exact texts and
compresses to **2.16%**; identical paragraphs account for 94.28% of word
positions beyond their first occurrence. Good prose is feasible; this remains
a small family of stories, not a large corpus multiplier. The paid check cost
$0.04575 and stayed under the original shared $5 cap.

The [question-led scene experiment](runs/harbor_questions_v2_10/FINDINGS.md)
uses requests, real inspections, reports and revised beliefs to drive dialogue.
Storytelling on ten is **7.5/8.0**, diversity **3/4**; QA usable is **59/60 and
60/60**. The full 32-configuration space has only **24 texts**, and a local
hundred already reaches 23. This is another readable canonical example, not
a diversity solution. Corrected local batches preserve all traces; one scored
QA answer now names the inspector explicitly and has not been regraded.
The paired check cost $0.039282 within the same $5 cap. Run
`python -m storyscenes.harbor_questions_story --seed 10003 --qa`.

The [favor-network experiment](runs/harbor_favors_v2_10/FINDINGS.md) follows
requests through independently assigned projects and lending priorities.
This regresses: ten-story storytelling is **7.1/6.2**, diversity **3/3**.
Longer dependency chains mostly yield the same borrow/work/return story.
The unjudged hundred has 56 exact texts and a **2.48%** XZ ratio. A local
972-configuration permutation audit finds 135 texts, not a full-space ceiling.
Keep it opt-in, not a baseline replacement. Local corrections record who heard
each reply and remove unsupported prose actions; those revisions are unjudged.
The paid check cost $0.041384; commitment at that checkpoint was $4.583660 of $5.

The [earlier-promise extension](runs/harbor_questions_v6_10/FINDINGS.md) adds
conflicting work, refusal, self-help, compatible deliveries and late repair to
the question-led script. Storytelling is **7.4/7.7**, diversity **4/5** on ten.
Both judges notice consequences beyond correcting a guess, but the repeated
inspection-first structure remains conspicuous. The complete 128-config space
still has only **52 texts**; an unjudged hundred has 43 and compresses to 3.57%.
Unknown bridges now lead to a separately known lane rather than needless
abandonment. A local QA-only correction focuses refusal questions on Cy;
the ten paid samples are unchanged. Commitment then was **$4.625218/$5**.

The [attempt-first extension](runs/harbor_questions_v8_10/FINDINGS.md) enacts
failed lifts, blocked crossings, early deliveries and their actual repairs.
Storytelling is **7.2/7.0**, diversity **5/5** on ten; QA usable is 58/60 and
59/60. Some stories still score six: stopping after a failed attempt does not
make a strong turn. Across 100 matched seeds, exact texts rise from 39 to 54
and XZ ratio from 3.64% to 5.52%, but repeated paragraphs still account for
82.68% of word positions. The full 256-config space has only 104 texts.
Local v9 makes an assumed load explicit in the opening; its corrected contexts
are unjudged. All old and corrected batches are retained. Conservative
commitment at that checkpoint was **$4.668147/$5**.

The [recovery-path follow-up](runs/harbor_questions_v11_10/FINDINGS.md) enacts
second inspections after removing covers and smaller lifts after refusal.
Ten-story storytelling is **7.6/7.1**, but thirty-story storytelling is
**7.733/6.900**, with diversity **5/5**. Its local hundred remains unjudged;
55 exact texts and 83.23% repeated-paragraph word positions do not establish
good diversity. The user rejected the displayed prose despite the high judge
scores. The single race-story calibration anchor and state-completion-heavy
rubric are insufficient evidence of literary quality. Calibrate against
blinded better/worse prose before further broad optimization. The shared cap
has been explicitly increased to **$10 total**, retaining historical reserves.

The separate [literary comparison](runs/literary_calibration_v1/README.md)
supports that concern for the displayed examples: Puddles beats the paint-box
story and Nell beats the empty-crate story in both orders for both judges.
Both harbor examples are rejected in every comparison. However, six of fifteen
complete two-order checks change winner, and no human pairwise labels exist.
This is diagnostic evidence, **not a calibrated replacement metric**. The
fixed-seed StoryScript references have defects too. Keep old scores intact;
improve the meaningful goal and earned payoff before scaling the generator.

[Conversational QA](CONVERSATIONAL_QA.md) adds questions, remembered follow-ups,
timed evidence and draft chat export over saved worlds. Use `run.py ... --qa`
or `qa.py ... --interactive`. It runs offline and leaves story generation alone.

[Training export](EXPORTING.md) converts frozen batches into the existing chat
dataset format, preserving complete follow-up chains and checking exact context
lengths and loss masks with the production tokenizer and training loader.
Candidate and judge-screened exports remain separate; the report measures
story repetition, answer supervision, and remaining semantic acceptance gaps.
New exports include branch-specific starting conditions in the request; see
[two complete prompt/response examples](examples/branch_prompts_v1/examples.md).
The historical generic-prompt export remains unchanged.

The [100-world trial](runs/worlds_100_v1/REPORT.md) produced 100 independent
generators from 131 attempts and graded three stories per world. Story quality
was **7.18/9**, below the earlier two-world 7.75 pilot; conversational QA was
**6.43/9** across 1,800 conversations. Returned API cost was **$2.65**, with
another **$0.17** conservatively reserved for missing usage. All returned calls
used Flex. The report includes per-theme results, manual examples and costs.

## Run a saved world

From the repository root (Python 3.10+):

```bash
python storyscenes/run.py storyscenes/runs/improvement_luna_v6/roof_post --seed 1000
python storyscenes/run.py storyscenes/runs/improvement_luna_v6/roof_post --seed 1000 --prose-seed 42 --json
python -m unittest discover -s storyscenes -p 'test_*.py'
```

Copy the whole `storyscenes/` folder to use it elsewhere. No API key, OpenAI
package or repository data is needed to sample completed worlds. Each new run
freezes its shared modules in `_runtime/`; `run.py` automatically uses that copy.
The original prototype remains reproducible with the compatible default API.

## Author a batch

For richer design seeds, [the classic/kernel mixer](SEED_MIXER.md) samples ten
lists of references, motives, kernels, themes, cast, settings, props,
complications, styles, and possible endings. Use `compact_workshop.py
--seed-source mix` for a trial; the old theater baseline remains available.

For 100 independent compact worlds with three uniformly selected stories graded
per world, including a separate conversation/dialogue evaluation:

```bash
python storyscenes/world_batch.py --out storyscenes/runs/my_100_worlds \
  --campaign storyscenes/improvements/20260908 --api-key-file .API_KEY
python storyscenes/world_batch_analysis.py storyscenes/runs/my_100_worlds
```

After the original process exits, resume paused work with the quota scheduler:

```bash
python storyscenes/world_batch_continue.py --out storyscenes/runs/my_100_worlds \
  --api-key-file .API_KEY
```

It reuses completed responses and quarantines uncertain/capped authoring drafts
before trying the next predeclared seed. After all authoring exits, the separate
`world_batch_retry_judges.py --out ... --api-key-file .API_KEY` command can recover
explicitly rejected 429 judge requests; it never replaces valid grades. Finish
with `world_batch_report.py storyscenes/runs/my_100_worlds`, which requires full
world and evaluation coverage before writing the report.

This targets ten mechanically accepted generators per each of the ten themes.
Up to 40 predeclared seeds per theme allow bounded replacement of failed
authoring attempts. All attempts and costs remain in the report; literary scores
never select replacements. Each accepted generator produces a 100-story local
pool, and exactly three uniform positions are graded without deduplication.
The original `cache-only` authoring prompts and quality rubrics are preserved.
Sampling and conversational QA generation make no API calls. The shared $15
campaign limit still applies, including outstanding uncertain requests. A
transport/paid-stage failure halts that theme for inspection rather than silently
retrying; `STOP` prevents new dispatches. Resume requires identical frozen source
and settings. Use one process per campaign ledger.

Install `requirements-authoring.txt`, then:

```bash
python storyscenes/workshop.py --out storyscenes/runs/my_trial \
  --campaign storyscenes/improvements/my_campaign \
  --seed 20260907 --count 10 --concurrency 4 \
  --api-key-file .API_KEY --evaluate
```

This makes paid OpenAI requests. Omit `--evaluate` for authoring alone. The
campaign has a $15 ceiling shared across its experiments. Each world also has a
$0.15 conservative dispatch limit (configurable with `--world-budget`). Neither
limit governs unrelated clients. Use one process per campaign ledger.

- Luna low reasoning plans the theater (3,000 maximum output tokens).
- Luna medium writes mechanics once (9,000 maximum output tokens).
- Up to six Luna low repairs return exact-match source edits or state-key renames (3,500 tokens each).
- Luna low writes a prose catalog once (11,000 maximum output tokens).
- Up to four Luna medium repairs replace individual catalog cards (4,500 tokens each).
- Failed worlds are quarantined. There is **no stronger-model authoring fallback**.
- Optional evaluation uses Terra with the unchanged quality rubric; it never
  returns generator code. The optional `--critic` is off by default, receives three stories and compact traces (no scripts),
  and returns at most three findings within 1,600 output tokens. It is recorded
  separately as evaluation; any fixes are Luna patches.

Caps include reasoning tokens. Repairs can read the complete current artifact,
plan and local diagnostics, but their output is a bounded patch. Mechanics
repairs do not receive finished stories. Prose authoring receives the frozen
simulation and executed previews; the shared renderer compiles the final Python
wrapper without another model call.

Put an empty file named `STOP` in the run directory to prevent new authoring or
critic dispatches. In-flight requests can still complete. Retain all reservations
if forcibly interrupting a request. The independent set judge is a separately
started phase; a STOP file is checked before entering that phase.

The key is never written into prompts/artifacts or inherited by generated code.
Use `OPENAI_API_KEY` to omit `--api-key-file`. Requests are saved before dispatch
and responses before execution. A saved response is reused only with its frozen
request. Flex requests allow up to 15 minutes for a response. Missing responses retain their reservations and are never silently
retried. There are no automatic transport retries or service-tier fallbacks.

Prices and supported efforts were checked against the official
[Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna),
[Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra) and
[Flex](https://developers.openai.com/api/docs/guides/flex-processing) documentation.
`cost_report.py` uses actual returned model, tier and usage, including reasoning,
and separates authoring from evaluation. Estimates are not invoice reconciliation.

```bash
python storyscenes/cost_report.py --run storyscenes/runs/my_trial --out /tmp/cost.json
```

It projects the measured authoring cost to 20,000 mechanically successful worlds,
including failed attempts in the numerator. Inherited drafts (via `--from-run`) are included in the authoring projection.
Unknown outcomes and literary rejection
still need accounting; a ten-world estimate is not a production guarantee.

## Shared execution and prose

`runtime.py` provides immutable scenes, guards, atomic effects, invariants,
seeded bounded search, causal provenance and knowledge/ownership kernels.
`scene()` uses keyword effect maps to reduce constructor errors. `Observe`,
`Tell` and `Transfer` bind knowledge and ownership changes to physical carriers.

`planning.py` removes causally irrelevant preparation, preserves pivotal
character turns and replays every retained move against its guards and rules.
Final outcomes must survive pruning. An invariant can be a real prerequisite,
so relevance analysis includes rules as well as explicit guards.

`prose.py` selects complete text variants against initial, before-event or
after-event facts. An explicit lexicon realizes scalar values as grammatical
phrases; there is no raw-enum fallback. Routine adjacent bridge cards are joined.
Endings depend on actual final state. Fact bindings accompany each paragraph,
and deterministic checks catch unsupported bindings, raw state leakage,
unresolved alternatives and repeated words. The full catalog is data, not
model-authored renderer code. `repairs.py` applies bounded, atomic edits.

Each simulation defines `build(seed)` with characters, props, embedded desires,
knowledge and candidate scenes. The planner composes legal moves across that
shared state. Scenes do not prescribe their next scene. The seed varies actual
initial conditions and available consequences, not just a prewritten route index.

The planner has complete state; characters know only what their action guards
allow. It enforces authored rules, not every unstated physical or social fact.
Fact bindings cannot prove that every free English assertion follows from them.
Manual reading and semantic evaluation remain necessary. Generated Python receives
an import/I/O lint and a credential-free, time-limited subprocess; this is not a
security sandbox for hostile source.

For the memeplex north star, definitions stay fixed while instances accumulate
state; every state key and scene binds to a carrier; embedded memes and beliefs
can gate behavior. This is a small operational subset, not yet a universal algebra
for concepts, characters and whole narratives.

## Evaluation and reproducibility

The copied StoryWorld pipeline retains its TinyStories calibration and 0–9
rubric: coherence, style, grammar, storytelling and overall. Terra judges ten
uniformly sampled positions per 100-story pool, selection seed 777, without
deduplication. It separately rates diversity and identifies causal plot groups.
Permutation counts are not presented as a count of distinct plots.

Every world saves 100 stories, three full traces, source hashes, conditional
catalogs, all authoring requests/responses, local failures and patch history.
New experiments freeze the execution runtime. Prose seeds 1–4 are compared with
one fixed world seed so wording variation cannot change the simulated events.

```bash
python storyscenes/verify.py --run storyscenes/runs/my_trial
```

The verifier replays pinned examples and samples 100 fresh seeds per world.
The original mechanical QA still exposes state changes and causal dependencies.
The optional conversational layer adds full answers and follow-ups; it uses a
bounded interpreter with explicit abstention. The story judge sees stories, not
traces, and conversational QA needs separate semantic alignment review.

Historical files: `factory.py`, `recover.py`, and `finalize.py` preserve the old
prototype tooling. `factory.py` no longer invokes Terra recovery implicitly.
`recover.py` is an explicitly invoked historical Terra recovery utility; use the
Luna-only workshop for new production experiments. Preserve `runs/prototype_v1`
as measured evidence, including its unsuccessful attempts and original reports.

See [the improvement report](runs/improvement_luna_v6/REPORT.md) and [the initial prototype report](runs/prototype_v1/REPORT.md). The improved batch uses optional bounded semantic feedback; its authoring-only price does not include that review.
