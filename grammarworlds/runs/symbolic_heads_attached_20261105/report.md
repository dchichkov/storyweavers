# Symbolic heads attached to the seven-world story generator

The integration works: manually weighted heads retrieve symbolic features from
the prefix and physical world, then alter next-word probabilities. The useful
effect demonstrated here is a controllable wording preference. This experiment
does **not** establish an improvement in overall story quality.

## Experiment

- Identical grammar, world rules, original event attention, and seeds across five
  profiles: off, original seed tables, manual, tool-only P023, state-only P059.
- Development: seeds 0–9, seven worlds, both tenses = 140 stories/profile,
  700 total. Seed 7 was also inspected while implementing the adapter.
- Evaluation after freezing the manual weights: seeds 1000–1019, seven worlds,
  both tenses = 280 stories/profile, 1,400 total. These are held-out seeds for
  this weight experiment, not new worlds or a test of domain generalization.
- All 2,100 comparison generations completed and replayed successfully. All
  12,600 generated QA pairs passed the implemented evidence/shape checks.
- No LLM ran during generation or scoring. The literary observations below are
  a qualitative inspection, not a Luna rating or blind human preference study.
- The generator's default stays off; `--heads` enables the experiment.

## Evaluation results

| Profile | Changed texts vs off / 280 | Changed token distributions | Distinct texts | Distinct event paths | Mean words |
|---|---:|---:|---:|---:|---:|
| Off | 0 | 0 | 140 | 60 | 90.31 |
| Original seed tables | 0 | 0 | 140 | 60 | 90.31 |
| Manual | 32 | 256 | 136 | 64 | 90.20 |
| P023 tool only | 32 | 120 | 136 | 64 | 90.20 |
| P059 state only | 0 | 136 | 140 | 60 | 90.31 |

Distinct counts are summed over the 14 scenario/tense groups, each with 20
seeds. Event paths are sequences of committed event kinds, not independently
authored plots. Mean within-group path entropy was 1.553 bits off and 1.588
manual. The small, mixed diversity differences do not demonstrate an improvement.

Manual changed 32/280 texts (11.4%). Its 280 stories exactly matched tool-only
texts in this evaluation. State-only made small probability changes without
crossing a sampling threshold; in development it changed 2/140 texts.

Use/used/uses was selected at 110/188 observed use-versus-other forks with heads
off and 78/188 with manual heads (58.5% → 41.5%). This measures the intended
style bias, not correctness or literary merit. Those forks include cases the
tool table does not cover.

There were 950 actual choice points among 34,882 manual token steps, including
punctuation and END. About 97.3% of steps already had one legal continuation.
Heads changed 256/950 choice distributions (26.9%), or 0.73% of all steps.
The narrow grammar gives most activations no opportunity to affect sampling.

| Manual head | Feature-bearing activations | Distributions it could change |
|---|---:|---:|
| P001 subject number | 3,914 | 0 |
| P002 person agreement | 1,046 | 0 |
| P023 tool affordance | 418 | 120 |
| P059 carrier-bound state | 3,162 | 136 |

An effective head has unequal log adjustments across the currently allowed
candidates. P001/P002 retrieve features but the grammar already enforces their
agreement decisions. P059's mean total variation on its changed predictions was
about 0.0136; P023's was about 0.2407.

The adapter supports inputs for six of the 15 executable tables. P007/P013 had
no matching contexts in these samples; the other nine await structural or
intent adapters. The 49 program-required heads remain explicitly deferred.
These numbers must not be presented as 64 working live heads.

## Example and qualitative reading

The samples were selected before generation: seed 0 for development and seed
1000 for evaluation, past tense, all seven worlds, both off and manual. The
complete texts and QA are linked below, including unchanged pairs.

In the evaluation's library story:

> Off: Ms Alvarez used the ladder to lift the whale book down.
>
> Manual: Ms Alvarez lifted the whale book down with the ladder.

At that predicate fork, the ladder retrieves the reach feature. The manual
receiver gives lifted a multiplier of 2 and used 0.7, changing 50/50 to
74.07/25.93. The ladder still exists physically, and the action was already
guard-approved. The resulting sentence is a reasonable stylistic preference;
both baseline and adjusted sentences are grammatical and grounded.

The other six preselected evaluation pairs are text-identical. Across the
samples, premises, dialogue, state-driven turns, and ending images were retained.
The prose still has repetitive names, formulaic short clauses, and authored
plot limitations. The head integration did not address those defects. QA
remains grounded in the selected world events and visible scene claims.

**Matched-seed caveat:** manual/tool-only changed 22 sampled event paths. That
does not mean the tool head preferred those later plots. Switching “used X to”
to “verb with X” changes the number of word draws, shifting the later random
stream. Fixed-prefix/world tests separately establish that a head changes the
local distribution when its tool or carrier-bound concept changes. Rollout
path differences must not be treated as isolated causal evidence for a plot bias.

## What the result supports

1. The activation → transmitted feature → receiving weights pipeline works
   inside the existing generator. Manual JSON weights provide inspectable
   control without introducing new grammatical or physical possibilities.
2. Agreement-head activation alone is redundant in this grammar. More head
   names would not solve the lack of competing continuations.
3. World-derived features can affect word distributions. Their value for story
   quality still needs a useful prediction target and better receiving tables.
4. Exact-text diversity decreased slightly. No quality gain is claimed from
   the mechanical passes, style preference, or small path-diversity increase.

The next useful experiment is to identify a repeated quality defect with two or
more legal continuations, specify the relevant grounded feature, and test its
receiver on unseen examples. With a corpus, measure held-out next-word loss or
preference quality before scaling the head inventory. A shared-randomness
evaluation that is independent of sentence length would also improve plot
comparisons.

## Reproduce and inspect

```sh
.venv/bin/python -m grammarworlds.storytelling --scenario library --seed 1000 --heads --qa
.venv/bin/python -m grammarworlds.storytelling --scenario pottery --seed 7 --heads --head-strength 0.5
.venv/bin/python -m grammarworlds.storytelling.head_comparison \
  --out /tmp/story-head-evaluation --start 1000 --count 20
```

- [Integration guide](../../storytelling/HEADS.md) and [editable manual weights](../../storytelling/head_weights.json).
- [Evaluation summary](heldout/summary.json), [source hashes](heldout/manifest.json), and [unfiltered paired stories + QA](heldout/samples.md).
- [Every evaluation text, QA set, and changed distribution](heldout/stories_qa.jsonl.gz); [full traces for preselected samples](heldout/sample_traces.jsonl.gz).
- [Development summary](development/summary.json) and [development samples](development/samples.md).

Validation: 83 tests passed across story-head interventions, storytelling,
branch/QA evaluation, the symbolic library, core grammarworlds, and portable
grammar. Tests include strength-zero baseline identity, carrier/tool removal,
speaker ambiguity, state immutability, original seed preservation, supported
word probabilities, and consent guards at high head strength. Frozen portable
grammar hashes remain unchanged.
