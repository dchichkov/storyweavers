# Can low-effort authors produce new microdramas?

**Yes, for a bounded story-world assignment with a fixed API and independent
review.** Two fresh GPT-6.1 Sol subagents at low reasoning effort produced new
executable stories using the existing microdrama engine. Each needed two short
parent review rounds. The parent changed no candidate implementation code.

Use [the revised authoring prompt](../AUTHORING_PROMPT_V2.md) for another trial.
Replace CANDIDATE, PREMISE, and DESTINATION; provide the existing engine and this
folder's evaluator. The original frozen [prompt](../AUTHORING_PROMPT.md),
[protocol](PROTOCOL.md), first submissions, and repair ledger remain available.
The revised prompt incorporates lessons from this run; it has not yet been tested
in a fresh authoring trial.

## What the authors produced

| Candidate | Read a generated story | Material outcomes | Final checks |
|---|---|---|---|
| Floodgate: *The Weight Beneath the Water* | [Full rescue](floodgate/output/case1.txt), [knowledge without help](floodgate/output/case3.txt), [distracted reading](floodgate/output/case0.txt) | Forty sacks saved, or twenty-four saved and sixteen lost | 40 grid runs; seven grounded questions per run; author self-tests and independent physical interventions |
| Orchard: *The White Ribbons* | [Whole orchard](orchard/output/case1.txt), [two rows](orchard/output/case3.txt), [failed trial](orchard/output/case0.txt) | Six, two, or zero surviving rows | 40 grid runs; seven grounded questions per run; author self-tests and independent physical interventions |

Both have a clear desire and obstacle, a practical attempt, a consequential turn,
and a final physical image. The orchard has the more varied settlement: effort
can preserve some fruit without saving everything. The floodgate more sharply
separates clearing a false accusation from actually repairing the mechanism.

The counts are **80 runs and 560 answer checks**, not 80 distinct plots or 560
different question templates. Both authors chose fixed encounter order; changing
the scheduler seed introduces no narrative variation. The eight input cases
vary access, cooperation, and distraction. Each directory retains every seed-zero
story, its event trace, questions, and the complete evaluator report.

## What the initial green checks missed

Both first completed submissions passed all shared checks. Those versions are
preserved under `first_submissions/`. Author self-revision before submission is
described in each `AUTHOR_NOTES.md`; “first submission” does not mean first draft.

| Review | Floodgate | Orchard |
|---|---|---|
| Round 1 | A supposedly generic practice wrote `ida.applied` even when Ren was bound as the learner. Added actor-correct effects and independent force/load checks. | Correct construction directly implied warmth; dawn ignored the frost flag. Added independent cold/resistance comparisons and explicit fixed-premise validation. |
| Round 2 | The low-level practice used a lever without checking the learner's temporary control. Added loan/colocation prerequisites and rollback tests. | A later paragraph still blamed bad construction after a sound shelter failed from excessive cold. Repaired the neighboring scene and natural-language counts. |

The authors made these repairs themselves. The shared engine, original prompt,
and evaluator stayed byte-for-byte unchanged. `parent_review.py` independently
reproduces the original wrong-actor defect and verifies its repair, checks
unborrowed-tool rejection, and runs four additional physical counterfactuals.

In those counterfactuals the public inputs remain unchanged:

- A heavier gate defeats full knowledge and willing helpers.
- A heavier small sluice defeats its trial while the separately loaded large
  gate can still be opened with help. A failed local trial need not predetermine
  every later result.
- Severe trial cold defeats a correctly constructed orchard shelter.
- Severe overnight cold destroys blossoms beneath roofs that passed the earlier
  trial. The story and answer preserve that different cause of failure.

The resulting stories and traces are in `parent_evidence/`. The severe-cold case
was especially useful: it exposed a prose inconsistency that replay and fact-ID
checks could not detect.

## How I would scale the workflow

1. **Keep the assignment small and the interface fixed.** Give an author a cast,
   physical conflict, schema boundary, and four functions to implement. Provide
   working shared execution primitives instead of asking it to invent an engine.
2. **Generate a candidate library in parallel.** Each author owns one directory;
   preserve submissions and avoid edits to common infrastructure. A coordinator
   assigns different premises and tracks genuine outcome diversity.
3. **Run cheap checks on every candidate.** Exhaust its declared input space,
   replay traces, check references, and test failed actions. Do not let the author
   redefine the evaluator. Keep rejected candidates as evidence.
4. **Use independent review for what those checks miss.** Rebind roles, change a
   physical condition, inspect tool custody, and read the resulting story and QA
   together. Send specific defects back to the original author.
5. **Promote only reviewed units.** Keep a manifest of preconditions, effects,
   roles, physical assumptions, and narrative exposures. Test combinations before
   treating a unit as interchangeable with another author's work.

This trial supports parallel **production of bounded story-worlds**. It does not
yet demonstrate arbitrary mixing of scenes across those worlds. Their domain
practices were written separately; the reuse demonstrated here is the engine/API
plus bindings within each author's practice. The next integration experiment
should require two authors to use the same prewritten reading/testing/borrowing
practices in different settings, then swap or combine encounters under held-out
conditions.

## Limits

The subsequent [standard Terra quality/diversity evaluation](standard_judge_v1/REPORT.md)
rated ten randomly selected positions per world, retaining duplicates. Floodgate
scored 7.2/9 quality and orchard 7.4/9; both scored 1/9 diversity. The sample
missed full rescue in both worlds. Across the entire tested grid there are only
four and six exact texts respectively, and scheduler seeds add no variation.
See the report for branch-level scores, sampling limits, and raw evidence.

This tests Sol 6.1 at low reasoning effort. It supplies no measurements for a
smaller model, token cost, or 10,000-agent economics. The two premises were chosen
by the parent and share a knowledge–practice–cooperation structure, which narrows
the experiment. Outputs are authored prose over finite worlds; they do not use
models at runtime. Explanatory sentences can still be didactic, and background
props or gestures are not fully simulated.

Mechanical evidence supports declared facts, not automatic English entailment.
The parent read successful and contrasting failure stories, QA, and all four
physical variants; this was an author-team review, not a blinded reader study.
The small numerical mechanics are narrative devices, not engineering or
agricultural recommendations. Neither pack is a production-ready general action
library: arbitrary state edits and arbitrary cross-pack composition were not
exhaustively tested.

## Reproduce

From the repository root:

```bash
python3 -B -m microdrama.authoring_trial_20261024.evaluate --candidate floodgate
python3 -B -m microdrama.authoring_trial_20261024.floodgate.selftest
python3 -B -m microdrama.authoring_trial_20261024.evaluate --candidate orchard
python3 -B -m microdrama.authoring_trial_20261024.orchard.selftest
python3 -B -m microdrama.authoring_trial_20261024.parent_review
```

`trial.json` contains requested model settings, frozen-input fingerprints,
submission receipt times, and the repair ledger. `summary.json` records final
artifact counts and fingerprints. `first_submissions/` is archival evidence;
current runnable packages are `floodgate/` and `orchard/`.
