# Capability worlds

An opt-in implementation of the approved [three-slice design](design/capabilities_20261021/SYNTHESIS.md).
The schema is `storyscenes.capabilities.v1`. Existing Python/compact worlds,
frozen runtimes and the old owner/knowledge interpretation are not migrated.

All three approved slices now pass their bounded semantic acceptance gates:
physical continuity/loans, evidence/belief revision, and requests/promises/refusals.
Mechanical tests are not literary-quality scores or approval for training data.
See the [acceptance report](design/capabilities_20261021/implementation/ACCEPTANCE.md)
for requirement-level evidence, independent findings/fixes and remaining limits.

## Run locally

From the repository root, without credentials or network access:

```bash
python -m storyscenes.capabilities --example library --demo-path --qa
python -m storyscenes.capabilities --example harbor --demo-path --qa
python -m storyscenes.capabilities --example observatory --demo-path --qa
python -m storyscenes.capabilities --example choice --demo-path --qa
python -m storyscenes.capabilities --example library --seed 42 --json --qa
python -m storyscenes.capabilities --example library --demo-path --diagnostic --qa
python -m unittest discover -s storyscenes -p 'test_capability_*.py'
```

`--demo-path` replays a specific example path. Omitting it runs bounded,
seeded author-side search over the declared candidate actions. The default
library, harbor and observatory story profiles add narrative prerequisites; use
`--diagnostic` for the original permissive fixtures and verbose rendering.
Externally loaded worlds retain their own prerequisites in either view. Rejected
candidates are not narrated failures. An actual bounded attempt or speech act
may produce an event without changing physical state.

Save the typed initial world, then load it through the strict JSON boundary:

```bash
python -m storyscenes.capabilities --example library --demo-path --save-world /tmp/library-capabilities.json
python -m storyscenes.capabilities --world /tmp/library-capabilities.json --seed 42 --json --qa
```

Saving refuses to overwrite an existing file. JSON contains real typed record
objects, not Python expressions or encoded JSON inside scalar state strings.
The loader rejects unknown fields/tables/operations and missing schema versions.
Initial inputs also reject event-derived receipts, interactions and belief
history. They are initial-world definitions, not a checkpoint-import format.
Explicit authored beliefs, including wrong ones, remain allowed.

Preserve a local evidence batch (use a new directory on each run):

```bash
python -m storyscenes.capabilities.verify --out /tmp/capability-evidence-new
```

This saves strict-schema worlds, full and retained replay traces, rendered stories,
QA/spans, missing-support answers, blocked interventions, a frozen executable
runtime and SHA-256 manifests. The retained [v4 batch](design/capabilities_20261021/implementation/evidence_v4/summary.json)
has 50 scenarios and 10 atomic rejection cases; earlier batches remain intact.
The `choice` example demonstrates two feasible promises competing for one prop;
`choices.py` binds it in all three settings and supplies paired interventions.

## Shared execution

`core.py` owns the version boundary, records, atomic transaction writer, finite
event IDs, deterministic replay, search and narrative dependency selection.
Domain handlers declare table reads/writes. They inspect the same pre-state,
stage nonconflicting effects, and commit only when all invariants hold.

`authoring.py` provides role-bound `Kernel`/`Pattern` composition with `+` and
attention division with `/`. Binding is structural, never source-string
substitution. Every action is embedded in a physical actor; domain state and
evidence refer to physical carriers. `proposals()` uses accessible actor intent,
while physical legality remains a separate execution check. The search itself
is an author-side planner, not a general autonomous character policy.

| Family | Owned records and semantics |
| --- | --- |
| Physical | Acyclic parent paths, derived place/holder, separate legal ownership; bounded routes/capacity; scoped grants, exact consent/readiness, immutable performance receipts, loans and immediate return. |
| Epistemic | Timed propositions, exposed facts, attention/channels, actual observation, claims, delivery/comprehension and one explicit belief writer with retained predecessors. |
| Social | Delivered/understood single-addressee requests, interaction-owned responses, withdrawal, explicit promises, exact receipt matching, strict/inclusive deadlines, release and late repair. |

An optional `Grant.place` restricts both grantee and object to that place when
the grant is used. Omitting it means no place restriction, not no other grant
restrictions. Lending is checked at offer and again at activation; returns
recheck their own grant at performance. Consent/readiness cannot carry a
dry-bench-only grant aboard a launch.

Belief policies are narrow declared rules, not general inference. For example,
`freshness` requires a named report source and bounded maximum age, preserving
dated beliefs while explicitly adopting or deferring a current one. An accepted
recent report can still be wrong; the rule does not consult hidden truth.

`advance_time` closes a finite simulated interval. Promise assessment requires
the clock to pass the deadline, so no later event can be inserted at the same
tick to erase a breach. Exact boundary performance differs for `strict_before`
and `inclusive_by`. A breached obligation never makes physical action illegal.

## Reader boundary

`realize.py` reads event-time records to produce controlled text statements.
`reading.py` receives only those selected statements and their exact text spans,
not the world state. Questions and focused follow-ups require visible support.
Masking a reason, reply or target removes that support and forces abstention.
Simulator facts remain separately available in the trace.

Free authored opening/closing flourishes carry no automatic QA evidence.
Structured provenance does not prove arbitrary English entailment; templates
and final rendered story/QA pairs still require semantic reading review. The
diagnostic renderer remains available as `render()`. `render_story()` uses the
same event-time records with a selective narrative view. This is an initial
prose improvement, not a new literary benchmark winner.

### Selective prose pass

The [local matched review](runs/capability_prose_review_v2/MANUAL_REVIEW.md)
preserves all 30 judged paths and compares their exact old/new realizations,
then runs the same selected seeds with the new story prerequisites. No paid
calls or fresh quality scores were involved. V1 remains as an intermediate
checkpoint; v2 also prevents duplicate QA anchors within grouped paragraphs.

- Repeated custody snapshots and internal bookkeeping are suppressed. Ownership,
  return responsibility at a pause, actual return settlement, dialogue and
  consequential belief changes remain visible. Adjacent physical actions can
  share a paragraph without changing execution order.
- Suppressed statements are unavailable to reading QA. Retained assertions keep
  their visible dependency closure; masking support still forces abstention.
- Questions name visible paragraphs rather than internal event IDs. Exact text
  spans account for grouped paragraphs and recompute after masking.
- Openings use initial co-location, not invented wants. A closing location is
  used only when its entire parent path remains unchanged after the supported
  snapshot. Partial event views get neither automatic opening nor closing.
- `story_examples.py` adds authored prerequisites: the library return follows
  the loaded trip and return journey; the observatory accepts and promises before
  its boundary-time handoff, then receives the next request after assessment.
  These are not new universal physical/social laws. Conformance examples still
  permit a pre-promise handoff, and historical paths are never reordered in prose.

These changes move toward state-driven narrative over physical carriers without
adding runtime LLMs. They do not supply a general character policy or increase
plot diversity. See the manual review for unresolved motivation and style issues.

```bash
python storyscenes/review_capability_prose.py \
  --baseline storyscenes/runs/capability_scoring_v2 \
  --out storyscenes/runs/my_new_local_prose_review
```

This offline command refuses an existing output directory, freezes current
sources, checks exact historical trace/text reproduction, saves both comparison
arms and verifies that historical files did not change.

### Purposeful story profiles

The [second local pass](runs/capability_prose_review_v4/MANUAL_REVIEW.md) uses
existing physical, observation, communication and promise operations to make the
examples consequential. `examples.py` remains the permissive conformance library;
`story_examples.py` supplies these default CLI/trial profiles:

- Library: the accepted request is to inspect a courtyard marker. The atlas is
  a required observation instrument. Nia's inspection completes that task and
  supplies a report to Inez, before the loan is returned and settled.
- Observatory: a scheduled calibration reading must be available and observed
  before the chart is handed over. `promise_story(reading_at=6)` fulfills the
  promise; the default time 8 and a later time 10 breach it. This is an authored
  availability schedule, not a general model of work duration.
- Harbor: a corrected report enables Cy's trip to the jetty and actual retrieval
  of the gauge. The later inspection cannot be consumed on the original visit.
  `delayed_report_story(correction_enabled=False)` blocks that causal path.
- `loan_story(readable=False)` leaves the inspection unknown and prevents its
  completion. Making the atlas inaccessible also prevents the reading. These
  are regression interventions, not successful-story branches in the sampler.

The world state and narrative can be replayed without an LLM. Reader explanations
retain explicit support: masking the correction or its adoption prevents QA from
claiming it motivated Cy's trip. Hearing and believing can share a sentence but
retain separate, maskable assertions and exact spans.

```bash
python storyscenes/review_capability_prose.py \
  --baseline storyscenes/runs/capability_scoring_v2 \
  --out storyscenes/runs/my_purposeful_review \
  --fresh-count 20 --fresh-seed 44000
```

V4 preserves 30 matched and 60 independent positions; all return and replay.
V3's failed positions remain available alongside it. Both use the same bounds.
The newer review also saves current typed worlds and a separate independent-seed
JSONL with full evidence. Each fixed profile currently produces **one distinct
visible story**: do not count repeated seeds as new training examples. Parameter
variation and alternative outcomes remain the next diversity task. Tests: 407
StoryScenes passed at that checkpoint. The subsequent
[paired judging](runs/capability_judge_comparison_v2/MANUAL_REVIEW.md) scores these
revised plots **4/9 with both judges**, still insufficient literary quality.

## Score fresh generation

The first [fresh sampling baseline](runs/capability_scoring_v2/LOCAL_REVIEW.md)
returned 1,973 of 4,000 planned positions under the limits below. All returned
stories replay, but the prose remains diagnostic and heavily repetitive.
The local report preserves manual examples, compression, failures and provenance.
The [paid matched judge comparison](runs/capability_judge_comparison_v1/MANUAL_REVIEW.md)
scores the same 30 selected texts at 2.667/9 with Terra and 3.000/9 with GPT-6 Luna.
Both judge the outputs as repetitive event logs rather than finished stories.

`compare_capability_judges.py` runs a separate paired campaign without modifying
the frozen sampler or rubric. It shares one budget across both models and changes
only the model ID between paired requests (Flex, reasoning none, store false).

To judge a saved local prose review without generating a replacement batch:

```bash
python storyscenes/compare_capability_judges.py prepare \
  --review storyscenes/runs/capability_prose_review_v4 \
  --previous-comparison storyscenes/runs/capability_judge_comparison_v1 \
  --out storyscenes/runs/my_revised_judging --budget 1
# Explicitly paid: repeat with evaluate and --api-key-file .API_KEY.
```

This verifies the original matched seed IDs, saved source copies, current runtime,
exact replay, rendered stories and conversations before creating requests. It
uses `fresh_seeds.jsonl`, not the same-old-path ablation. Previous committed spend
plus the new cap must fit the shared $5 authorization; unknown previous outcomes
must be reconciled first. The completed V2 report preserves partial QA coverage
and bounded manual recovery of explicit Flex rejections; it does not impute grades.

```bash
python storyscenes/compare_capability_judges.py prepare \
  --baseline storyscenes/runs/my_capability_trial \
  --out storyscenes/runs/my_capability_judge_comparison --budget 5
python storyscenes/compare_capability_judges.py evaluate \
  --baseline storyscenes/runs/my_capability_trial \
  --out storyscenes/runs/my_capability_judge_comparison --budget 5 \
  --api-key-file .API_KEY
```

The saved comparison reuses completed grades, including failures, rather than
resending paid requests. Do not additionally run the standalone evaluator on the
same baseline: one comparison should own its paid scoring campaign. Prepare a
new baseline first with the command below. Historical campaigns require their
preserved runtime; the current source-lock check correctly refuses to resume
an old sampler after these implementation changes. Read saved reports directly
instead of updating historical hashes or overwriting old grades.

`capability_trial.py` adapts fresh seeded outputs to the existing
`story_set_quality_v1` and `story_conversation_quality_v1` Terra/Flex judges.
It does not use the pinned demo path's authored opening/ending or silently
replace failing seeds. Preparation is offline; evaluation is explicitly paid.

```bash
python storyscenes/capability_trial.py prepare \
  --out storyscenes/runs/my_capability_trial --count 1000 --seed 19000 \
  --workers 6 --max-nodes 6000 --cpu-seconds 2 --wall-seconds 6
python storyscenes/capability_trial.py evaluate \
  --out storyscenes/runs/my_capability_trial --budget 5 --api-key-file .API_KEY
```

The four current CLI story profiles are sampled at every requested seed. A repeating CPU signal
limits search; a parent process also kills and reaps each disposable worker at
the wall limit (including startup). A timeout is not proof that the world has
no legal outcome. Wall-limited attempts have unknown CPU usage, not zero usage.
Quality judging selects up to ten returned positions per demo without dedup;
it is conditional on sampling success. Fewer than two returned stories leave a
demo ungraded. All failures remain visible in the generation-yield denominator.
QA uses six uniform supported questions per selected story, with same-event
why follow-ups when supported; its conversation mix differs from the older
three-turn conversation benchmark.

Each batch preserves source hashes/copies, typed worlds, JSONL attempts,
compressed full traces and a single XZ story corpus. Raw requests, responses,
grades and a persistent local spending ledger are retained. Resuming reuses
completed work and refuses changed sources/settings; an uncertain request is
never automatically resent. The budget guard is not provider-side billing.

The geometric formula is unchanged, but the adapted strict mechanical gate
requires every planned seed to return and replay exactly. The separate table
also reports actual yield, quality, semantic diversity, exact uniqueness and
action multisets so reordering cannot be mistaken for plot diversity. Pooled
compression retention is distinct from compressed/raw size. Full conformance
tests and the saved scripted paths are not substitutes for this sampling test.

## Next prose experiment

**Proposed, not yet implemented or graded.** The revised evaluation shows a small
improvement, not a viable dataset. It also does not establish that world-backed
story generation is impossible: these are three conformance-derived plots and a
renderer built by selecting diagnostic statements. The older catalog path scored
7.18/9 over 300 stories from 100 worlds, but only 6.43/9 on story-only QA. Different
worlds and sample sizes prevent a causal comparison; they still identify useful
strengths and weaknesses to test together.

### Change the unit of writing

The simulator should validate atomic moves. The author should write a scene:
a goal, an obstacle, a response and an outcome. One scene can cover several
physical or conversational operations without explaining every state update.
Correctness constrains the prose; it need not dictate its sentence boundaries.

For example, a faithful compression of the library's existing travel/inspection
sequence could be: "With Inez's atlas in the carrying bag, Nia went out to the
courtyard. Nia set the bag down and used the atlas to read the stone marker."
This is an ungraded illustration, not a new generated output. It drops narrated
pickup bookkeeping; QA must not keep questions whose only evidence was dropped.
It also does not fix the weak payoff of discovering the garden. That requires
a different subsequent event, not a more colorful adjective.

### First experiment: fixed events, different writing

Use the three current successful traces as a cheap screen before expanding
semantics. Freeze events, actual speech acts, initial facts and outcomes. Compare:

| Arm | Approach | What it tests |
| --- | --- | --- |
| A | Current selective diagnostic renderer | Measured control |
| B | Authored conditional scene passages spanning several events | Can classical, reusable realization tell the same events well? |
| C | One freely written, trace-constrained reference rendition per trace | Does this plot support a good story at all? A diagnostic reference, not a runtime solution |

Author B and C offline, starting with the coding agent; no additional authoring
API call or runtime LLM is required. B should reuse the ideas in `prose.py`, not
silently change the legacy engine or copy arbitrary decoration into every branch.
Once a passage needs an unsupported reaction or consequence, flag a missing plot
fact rather than quietly invent it. C receives the same restriction; it is not
an unconstrained style control that wins by changing the events.

Use the unchanged quality rubric without revealing arm labels to judges; randomize
presentation and preserve all renditions. These three traces screen feasibility,
not diversity or generalization. If even C is weak, invest in better plots first.
If C is strong and B weak, the reusable realization contract is the bottleneck.
If B is strong, test it on unseen state branches before generalizing it.

### Preserve evidence without narrating an audit

- A scene passage declares the events and time-indexed facts it consumes, its
  branch prerequisites, and which assertions it makes visible. Custody, ownership,
  belief and dated reports must remain distinct even when sentences are combined.
- Preserve exact visible spans for statements and speech. Regenerate quote QA
  from rendered wording; do not reuse a diagnostic quote after paraphrasing it.
- QA uses the intersection of trace-supported and reader-visible facts. Count
  meaningful question coverage as well as accuracy so omission cannot game QA.
- Test each passage under alternate bindings and missing-support masks. An event
  must not be narrated twice by both a scene and an ending. A story-only semantic
  review is still necessary: declared bindings do not prove free English true.
- Do not treat dialogue density as a goal by itself. Requests, refusals, mistakes
  and repairs should change what happens, not merely restate operation names.

### Second experiment: varied, consequential plots

Only after the writing screen, build a small matched set with real alternatives:
timely versus stale information, a reachable versus unavailable return route,
and an early versus late reading with a demonstrated effect on another character.
Blocked paths need an enacted recovery or a meaningful failure ending. Currently
unreadable/blocked variants are negative tests, not completed alternative stories.

Consider **story-first authoring** here: write a few compelling scene outlines,
compile their required state changes and alternative consequences, then test
interventions. This reverses the current assumption that a legal interaction
trace automatically supplies a worthwhile plot. It still leaves simulation and
QA classical at runtime.

Predeclare a modest acceptance gate: every pilot scenario at least 6/9 overall,
no material prose/trace contradiction in manual review, at least 95% correct and
useful story-only QA on the retained coverage, and at least two genuinely distinct
causal outcomes per scenario. These are proposed engineering gates, not calibrated
claims about dataset suitability. Freeze unsuccessful variants too.

Finally sample 1,000 local outputs per accepted generator, dedup and measure
LZMA retention alongside semantic plot groups. Sentence variants cannot rescue
one fixed plot. Do not spend on a large world-authoring batch until the small
writing and branching tests pass.

## Deliberate exclusions

Receive-only handoff leaves its loan outstanding. Delayed settlement is
unsupported, as are recursive legal delegation, general contracts, responder
abandonment, probabilistic trust/perception, vehicles/joint lifting and unbounded
speech repetition. Changing promise terms uses release plus a new linked
undertaking; it does not rewrite the old promise. No runtime LLM or paid judge
is part of this implementation.
