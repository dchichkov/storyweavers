# Two-Agent Authoring Trial: Results

## Bottom Line

Two `gpt-6.1-sol` agents at **low reasoning effort** built independent scenario
packs from seeded ingredients, beginning with approximately 1,000-word stories.
They then produced scene inventories, short local simulations, compatible 7/8
scene routes, tests and examples. They reused the existing engine; one contributed
a small shared action helper that the other adopted without changing its stories.

This supports **supervised pack authoring**, not unattended production. Initial
programs passed their own tests and the independent trace checker while retaining
substantive narrative/physical mistakes. Parent reading supplied the repairs.
Neither data diversity nor lower authoring cost is established by this trial.

## Artifacts

- [Initial brief](AUTHORING_AGENT.md.in), [v2](AUTHORING_AGENT.v2.md.in), and
  [latest v3](AUTHORING_AGENT.v3.md.in). V3 compiles the lessons; it has **not**
  been tested as a fresh-context one-shot prompt.
- [Protocol and assignments](README.md), [ownership/message board](BOARD.md),
  and [initial reference reading](REFERENCE_REVIEW.md).
- [Bakery reference](../../mini_adventures/bakery/reference_story.md), 957 prose
  words; [greenhouse reference](../../mini_adventures/greenhouse/reference_story.md),
  997. Both were saved before implementation and retained unchanged.
- [Shared inventory and runner](../../mini_adventures/README.md): two packs,
  40 reference encounters mapped to 39 executable scenes. The consolidated
  greenhouse pause is not falsely counted as an executable scene.
- [First two release seeds, verbatim](SAMPLES.md). Full unfiltered batches and
  source snapshots are in each round directory, not just selected successes.

## Iterations

| Round | Work | Evidence |
| --- | --- | --- |
| 1 | Independent reference -> inventory -> complete first product | 100/100 mechanically valid per pack; parent found unusable returned light, inconsistent deadlines, instant crop loss, and missing prose links |
| 2 | Physical-purpose and cause/effect repairs | 100/100 per pack; bakery changed 22 outcomes, greenhouse kept outcomes but improved enacted rescue/damage |
| 3 | Shared helper contribution, dialogue and ordinary-state audit | 100/100 per pack; tea consumption and door/exit ordering fixed; bakery's helper extraction preserved all states/events |
| 4 | Second helper consumer; frozen-source and unseen-seed release checks | 400/400 matched/new-seed positions reproduced; full-suite discovery exposed one package-identity assertion failure |
| 5 | Narrow test-integration correction and final verification | 660/660 full-suite tests pass; 100-row bakery recheck exactly matches preserved holdout |

The same two workers were reused across rounds. Parent supervision included
saved defect lists, full-story reading, registry/audit/export tooling, and a
test-mock integration fix. This is not evidence that either worker independently
found every defect, nor that a different model would perform worse. Worker token
cost and comparative authoring cost were not measured. No external API judging
occurred during these five rounds; the subsequent requested standard-judge pass
is recorded below. No runtime LLM calls occurred.

## New-Seed Results

These are the predeclared seeds **1000-1049**, each at both lengths, evaluated
after round 4. They are held-out seeds within two known scenarios, not held-out
worlds or a blinded literary experiment. Failed attempts would be retained;
none failed generation, event-chain validation or exact replay.

| Pack | Passing | Exact texts | Words min / mean / max | Scene words | Outcomes | Pooled XZ ratio |
| --- | ---: | ---: | --- | --- | --- | ---: |
| Bakery | 100/100 | 69 | 392 / 431.0 / 468 | 52-67 | 94 postponed, 6 shared suppers, 0 surprise suppers | 1.81% |
| Greenhouse | 100/100 | 49 | 362 / 406.6 / 444 | 47-73 | 62 supervised trials, 24 separations, 14 joint-care | 1.78% |

Quote-based word fractions are approximately 18.7% and 16.6%. These are rough
dialogue diagnostics, not quality scores. XZ uses Python's default LZMA settings
on every story joined by two newlines in requested order. Exact differences may
come from wording or optional-scene insertion; neither metric proves distinct
plots. The very low compression ratios argue against a large sample multiplier.

All three outcomes per pack have executable parameter recipes and targeted
tests. The bakery surprise outcome appearing in the earlier matched set but
not in this new set is reported, not filled in with a chosen successful draw.

## Subsequent Standard-Judge Evaluation

On October 24, at the user's request, the unchanged standard
`gpt-5.6-terra` Flex judge rated ten uniformly selected saved stories per pack,
using selection seed 777 and the round-4 holdout pools. Duplicates were not
removed or replaced. The existing 0-9 story-set rubric, calibration story, and
validated group-membership output format were reused. The judge received prose
only, without source, trace, reference stories, or the earlier manual reviews.

| Pack | Rated | Overall / 9 | Storytelling / 9 | Diversity / 9 | Overall range | Plot groups |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Bakery | 10 | 7.8 | 6.8 | 2 | 7-8 | 3 |
| Greenhouse | 10 | 8.2 | 8.2 | 3 | 8-9 | 5 |

Terra praised concrete ending images and consequential decisions. It flagged
the bakery's unresolved meal and underused extension branch; greenhouse's
honesty, practical help, and qualified restoration of access scored better.
Both sets repeat their premise and much of their wording. All ten selected
bakery routes postpone supper; greenhouse has six supervised trials, two
separations, and two joint-care outcomes. These draws were retained unchanged.
Ten different strings per pack do not imply ten substantially different plots.

This supports readable individual stories, especially greenhouse, but not a
large narrative multiplier. These are two small sets under one automated judge,
not a blinded human assessment or evidence of superiority over earlier runs.
QA was not evaluated because these packs do not yet export it.

Both requests returned complete and on the requested model/Flex tier. Usage:
13,249 input and 2,009 output tokens; **$0.025303 estimated** using the existing
historical Terra rate table, not current-price verification or an invoice.
The shared campaign remains below its previously authorized $10 cap. No paid
retry or fallback was used, and no generation code changed.

[Report](standard_judge_v1/REPORT.md), [summary](standard_judge_v1/summary.json),
[exact selection](standard_judge_v1/provenance.json), and the adjacent input,
request, raw-response, rating, source-snapshot and budget files preserve the
evaluation. The [adapter](judge_stories.py) uses the existing judge and budget
helpers; its prepared inputs were checked against deterministic selection and
the standard request builder. The seven harbor-trial and ten comparison tests
pass under the repository's discovery invocation.

## What Changed In The Workflow

1. Write and preserve the good reference before building rules. Do not rewrite
   it afterward to excuse a generated inconsistency.
2. Map reference encounters to executable IDs; list prerequisites, effects and
   prose obligations. Keep shared inventory distinct from cross-world compatibility.
3. Inspect purpose, not just state: a returned but empty lantern can leave the
   owner's need unresolved. Future invitations are not completed meals.
4. Use paired counterfactuals to check constraints across branches, materials,
   and weather. A favorable plot should not make the same hard constraint vanish.
5. Read complete random routes. Trace equality does not catch implausible timing,
   missing motivation, unclear speakers, or generic instructional dialogue.
6. Audit ordinary continuity too: cups empty after drinking; characters pass
   through an open door before it closes.
7. Share only proven common mechanics. The new helper handles atomic application
   and detached trace data; plot selection, physical rules, and prose stay local.
8. Freeze every round, preserve failures, and test both direct invocation and
   repository discovery. A locally green package is not yet an integrated release.

## Limits

Both generators still have a largely fixed seven-function spine; eight scenes
usually add a vignette. Parameters and local outcomes vary, but neither pack is
a general adventure composer. The bakery is especially failure-heavy after its
obligations become real constraints. Do not make it look better by filtering.
These are small authored story families, not thousands of independent narratives.

The parent read both references and complete first-draw routes in every stage,
including all eight displayed release samples. The references retain more
texture and natural pacing; the short versions are readable but often explain
their constraints directly. This is an agent's qualitative assessment, not a
human acceptance label or a calibrated judge score. No QA/training export was
added; that is outside this authoring experiment.

## Release Verification

Final command:

```bash
./.venv/bin/python -m unittest discover -s storyscenes -p 'test_*.py'
```

**660 tests passed in 265.182 seconds.** This includes 597 prior tests and 63
new pack/helper/review tests. Direct and discovery-mode focused tests also pass.
Earlier failures remain preserved in [the release review](round_04/RELEASE_REVIEW.md)
and [bakery's round-5 note](../../mini_adventures/bakery/ROUND5_REPORT.md).

Final bakery recheck: `round_05/bakery_recheck/`, 100/100 passed and independently
reproduced; its stories.jsonl is byte-identical to `round_04/bakery_holdout/`.
This snapshot includes the corrected test source. Greenhouse's final snapshot
remains `round_04/greenhouse_holdout/`; its code did not change in round 5.
All eleven preserved parent audit batches were replayed from their own frozen
source trees. No failed or partial historical artifact was overwritten.

## Objective Evidence

| Requirement | Verified evidence |
| --- | --- |
| Saved authoring prompt | Versioned v1/v2/v3 briefs, assignments, feedback and ownership board |
| Two lightweight agents | Recorded worker handles; both spawned with explicit gpt-6.1-sol / low, fresh context |
| Seed to roughly 1,000-word reference | First seeded ingredients and both unchanged reference hashes/word counts |
| Scene inventory to working product | Registry validates 40 encounters mapped to 39 executable scene IDs; CLI runs both packs |
| Local simulation and global continuity | Exact 7/8 routes, guarded local events, parameter/counterfactual tests and state/prose replay |
| Access to and contribution to libraries | Both use the existing engine; bakery contributed LocalPlay; greenhouse adopted it with identical saved rows |
| Monitor and iterate 3-5 times | Five recorded rounds, same two workers, parent readings, concrete fixes and preserved before/after outputs |
| Verify final results | 200 new-seed routes plus matched/recheck batches; frozen-source reproduction; 660 green tests; eight verbatim release samples read |

Both workers finished and were closed. Current work is local and has not been
committed or pushed as part of this trial. The next distinct experiment would
be a fresh-agent run of v3, not more tuning of these same two packs.
