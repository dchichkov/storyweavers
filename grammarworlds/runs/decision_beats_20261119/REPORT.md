# Decision beats: implementation and development audit

The three crafted worlds—pottery, music and greenhouse—now support an opt-in
shared policy in which interpretation changes choice probabilities, dialogue
creates requirements, and an ending can depend on a visibly established detail.
There are nine authored appraisals across the three worlds. The existing nine
main branches remain available; this does not add new plots or roll the policy
out to the original twenty worlds.

```bash
.venv/bin/python -m grammarworlds.storytelling --scenario music --edition crafted --decision-beats --appraisal appraise_together --seed 19 --qa
```

Omit `--appraisal` to sample the interpretation too. Generation remains entirely
classical, including the distributions over annotated tokens. The original and
previous crafted modes keep their existing behavior.

## What now changes behavior

| Requirement | Implemented behavior | Verification |
|---|---|---|
| Appraisal | Visible evidence permits an interpretation event, which writes bounded priorities onto the physical character. Later choices combine those priorities with authored forecast stakes. | Changing appraisal changes branch probabilities while retaining all three options. Disabling attention disables these scoring contributions. |
| Costly choices | Observed costs require concrete carrier states after the action; forecasts remain separate. | All nine branches replay with verified costs. Examples include losing the public concert slot, missing a birthday, and leaving one's flower dry. |
| Consequential dialogue | Actions can require an actual earlier utterance. Responses and fulfilled promises link back to it. | Removing a required utterance blocks the action even if physical flags remain. Promising to close a door leaves it open until the closing action happens. |
| Earned payoffs | A detail must have been visibly introduced on the same carrier, acquire a changed meaning, and satisfy current physical guards. | Missing setup or invalid state rejects a payoff without mutation. Setup links survive intervening reminders and annotated export. |
| Compression | Already-expressed meanings receive lower probability of repetition. New meanings and different carriers must still be expressed. | Paired runs reduce spoken reminders while preserving final physical states; tests keep new information and the actual costly action mandatory. |

The shared mechanism is in
[`decision_policy.py`](../../storytelling/revisions/decision_policy.py), with
authored story bindings in
[`decision_bank.py`](../../storytelling/revisions/decision_bank.py).
Interpretations affect generation through magnitudes carried by physical
characters, while costs and payoffs depend on concrete objects and actions. This
follows the project's memeplex north star rather than emitting abstract concepts
as independent story facts.

## Choice distributions

For music, with the same seed and character traits, changing the appraisal gives
these probabilities at the main decision:

| What matters to Nia | Private duet | Solo performance | Perform Mateo's written answer |
|---|---:|---:|---:|
| Playing together | 66.1% | 4.7% | 29.2% |
| Keeping the public turn | 3.6% | 56.6% | 39.8% |
| Preserving Mateo's contribution | 5.3% | 18.7% | 76.0% |

These are interventions in an authored probability model, not learned behavior
or quality scores. Appraisal influences rather than forces a choice. Forecasts
do not become future facts. Full distributions for all nine conditions are in
[`round02/summary.json`](round02/summary.json).

Sixty unconditioned samples reached every main branch: pottery 8/7/5,
music 4/7/9, and greenhouse 8/7/5 in their respective branch orders. The audit
checked normalization at 18,170 joint token steps. Mean body lengths were
216, 221 and 271 words, respectively.

## Compression ablation

Two hundred paired stories used fixed appraisals and branches, forty seeds per
condition. Each pair differed only in whether known reminders were downweighted.
Across 280 reminder opportunities, spoken repetitions fell from **128 (45.7%)
to 39 (13.9%)**. Final physical entities and flags were identical in every pair;
the reader's narrative memory intentionally differs.

| Condition | Spoken without compression | Spoken with compression | Mean words without → with |
|---|---:|---:|---:|
| Pottery: remake | 19/40 | 6/40 | 229.6 → 227.9 |
| Music: private duet | 16/40 | 7/40 | 197.1 → 194.6 |
| Greenhouse: share | 20/40 | 6/40 | 262.4 → 260.6 |
| Greenhouse: flower | 37/80 | 10/80 | 286.0 → 282.1 |
| Greenhouse: seedlings | 36/80 | 10/80 | 273.7 → 268.9 |

For a first known reminder, the weights are `say=0.15, omit=1`, versus equal
weights without compression. Unknown information is mandatory. This is explicit
semantic annotation, not automatic paraphrase detection. Compression saves a
few words; appraisals usually make the stories longer overall.

## Prose review and iterations

[`round02/samples.md`](round02/samples.md) contains nine paired stories with QA,
conditioned on the same final branch. These are development comparisons, not a
blind evaluation. The appraisals add roughly 0–22 words in these examples.

In the music private-duet example, Nia interprets Mateo's abandoned sticks as
making the concert turn less important. Her invitation then leads to a request
for a closed door, a promise, the loss of the public slot, and an actual door
closing before the duet. The ending returns to the answering drums:

> Behind the closed door, neither drum was quiet for long.

The paired example is 191 words in both versions. This illustrates a causal
chain and an earned image; it does not establish aggregate quality improvement.

The first audit is preserved in [`round01/`](round01/). Editorial changes after
reading the samples softened a deadline appraisal that overstated a preference,
removed redundant looking/putting-down actions, and marked actual repeated
greenhouse explanations as known information. The explanation is retained when
the earlier appraisal did not supply it. The flower's withdrawal from the show
remains explicit in either case. Giving Mateo credit is treated as fulfillment
of a promise, not as a cost; the written-performance branch instead records the
absence of the public duet partner.

## Verification and reproducibility

- Broad integration checkpoint: **374 tests passed** in [`tests.log`](tests.log).
- After the final export changes: **44 targeted tests passed** in
  [`export_tests.log`](export_tests.log), including 12 decision-policy tests and
  storycraft, event-line and story-memory coverage.
- All **27 appraisal × branch combinations** generated, replayed, and exported
  with QA; see [`combinations.jsonl`](combinations.jsonl).
- All nine archived round-two rows replayed with the final code. Their annotated
  exports preserve nine payoff links and 22 dialogue links; see
  [`export_check.json`](export_check.json) and
  [`annotated_samples.jsonl.gz`](annotated_samples.jsonl.gz).
- Prefix-time candidates distinguish proposed attributes from observed history.
  Exported observations carry `replayed_source_event` scope and dependencies on
  earlier evidence, utterances, setups and reader knowledge.
- The final code snapshot is in [`final_code/`](final_code/) with SHA-256 hashes
  in [`final_manifest.json`](final_manifest.json). The round-two snapshot predates
  the export-only addition; its archived generation still replays exactly.

Reproduce the probability and compression audit with a fresh output directory:

```bash
.venv/bin/python -m grammarworlds.decision_beats_experiment --out /tmp/decision-beats-audit
```

## Limits and next useful test

This is three authored story families using shared mechanisms. Stakes,
interpretations and semantic detail keys are manually specified. Events within
a branch still have largely fixed order. Annotation remains construction-level
in places, with unknown POS retained rather than fabricated. Reminders can still
be sampled deliberately. No Luna or independent quality evaluation was run for
this change, and no learned quality gain or general transfer ability is claimed.

The next useful test is a fourth world bound to the same policy without changing
the mechanism, followed by an equally concise, blind comparison. A later pass
can add incomplete beliefs and competing commitments, but adding more beat
labels alone would not demonstrate better storytelling.
