# Expanded continuation space

The expanded grammar gives the word heads more room to act while retaining the
seven existing worlds and their physical rules. On fresh seeds, choice points
rose from 2.8% to 7.4% of token steps, and distinct texts rose from 144 to 267 out
of 280. This increases wording/syntactic variety; it does not introduce new plot
types or establish better literary quality.

## What changed

`storytelling/continuations.py` builds alternatives from typed phrases before
sampling, without rewriting finished prose:

- Controlled action-verb alternatives: find/locate/discover, repair/fix,
  sketch/draw, practice/rehearse, shape/form, and others, restricted to compatible
  constructions. Explicit inflections preserve agreement and tense.
- Recipient constructions: “gave Jun the book” / “gave the book to Jun,”
  including transfers inside infinitives.
- Four tool constructions: “used the sponge to shape…”, “shaped…with the sponge”,
  “With the sponge, Bea shaped…”, and “Using the sponge, Bea shaped…”.
- Direct/polite wishes: “I want…” / “I would like…”.
- Direct/tentative offers: “I can…” / “I could…”. This intentionally varies
  pragmatic force for the same permitted action. Negative and past-modal
  meanings are left unchanged.
- Joined/separate clauses, preserving order and explicit contrast. Causal
  clauses keep their because link.

The expansion preserves original supported texts, participants, physical
effects, QA claims, and total prior mass for each available event. Tests compare
both forests at identical world states in both tenses. The existing limit of
512 derivations per event remains enforced. The portable GF/Codeco files are
unchanged; this is a local extension over them.

The adapter now resolves subjects after fronted tool phrases. Agreement
receivers are gated when there are no competing agreement forms, preventing
them from favoring a copula over an equally grammatical modal. The manual
weight file is unchanged from the previous experiment.

## Four-word example

Greenhouse seed 7 at `Nia said, “I`:

| Next word | Expanded grammar | With manual heads |
|---|---:|---:|
| want | 26.0% | 27.8% |
| would | 26.0% | 25.4% |
| can | 24.0% | 23.4% |
| could | 24.0% | 23.4% |

These lead to existing legal watering plans with different ways to express a
wish or offer. P059 reads Nia's carrier-bound Care and Desire; the authored
Desire receiver mildly favors want. There is no guarantee of four choices at
every step, and no invalid candidates are added to inflate the count.

## Evaluation

Development: seeds 0–4, seven worlds, both tenses, four profiles, 280 generations.
Reading those samples prompted removal of stilted present “I decide…” and
replacement of repeated “However” transitions with sentence-initial “But.”
Negative find clauses also omit discover.

Final comparison: frozen choices, seeds 2000–2019, seven worlds, both tenses,
280 stories/profile, 1,120 total. These are fresh seeds for this experiment,
not held-out worlds. Each grammar has its own heads-off baseline.

| Measure | Original, off | Original, heads | Expanded, off | Expanded, heads |
|---|---:|---:|---:|---:|
| Token steps with a choice | 982 | 988 | 2,583 | 2,585 |
| Fraction with a choice | 2.81% | 2.83% | 7.36% | 7.37% |
| Steps with ≥4 candidates | 0 | 0 | 189 | 192 |
| Head-changed distributions | 0 | 260 | 0 | 464 |
| Texts changed by heads / 280 | — | 30 | — | 33 |
| Distinct texts / 280 | 144 | 142 | 267 | 267 |
| Distinct event-kind paths | 64 | 64 | 64 | 62 |
| Mean words/story | 90.54 | 90.43 | 90.59 | 90.55 |

Token steps include punctuation and END. Distinct counts are summed within
the 14 world/tense groups, each containing 20 seeds. Heads-off conditional
entropy rose from 0.0246 to 0.0776 bits per token step. Mean length remains
about 91 words.

Heads change about 1.8 times as many distributions with the expansion. However,
the fraction of choice points affected falls (26.3% → 17.9%), and only 33 sampled
texts change versus 30 previously. Much of the new continuation space is outside
the sparse receiver tables. Surface diversity clearly increases; the additional
benefit of these particular manual heads is more modest.

All 1,120 final generations completed and replayed. All 6,720 QA pairs passed
the implemented evidence, uniqueness, question-kind and response-shape checks.
The earlier 280 development generations passed too. **88 tests passed**,
including same-state event prior/support/claim preservation, negative scope,
inflection, recipient order, strength-zero identity, consent, and the earlier
suites. Frozen portable hashes and the final source manifest were verified.

## Sample reading and limits

Seed 2000, past tense, all seven worlds was selected before generation and
read with its QA. The stories retain premises, physical turns, and ending
images. Examples include “Mina sketched…” and a remade bowl that Grandpa Len
holds with two hands. QA still refers to the selected story. Repetitive names
and formulaic clauses remain. This is manual inspection, not a blind preference
study or a Luna evaluation.

Matched seeds still share a variable-length random stream: different wording
can change later draws. Changed event paths do not isolate a head's plot
preference. Same-state forest tests establish preserved event priors; rollout
path counts are descriptive.

## Use and artifacts

```sh
.venv/bin/python -m grammarworlds.storytelling \
  --scenario all --seed 7 --continuations expanded --heads --qa
.venv/bin/python -m grammarworlds.storytelling.head_comparison --expanded \
  --out /tmp/expanded-story-comparison --start 2000 --count 20
```

Omit `--heads` to sample the expanded grammar without word reranking.
`--head-strength` scales manual weights. Original remains the default mode
for reproducible baselines and pinned stories.

- [Expanded stories and QA](expanded_samples.md).
- [All four profiles, paired samples and QA](heldout/samples.md).
- [Summary](heldout/summary.json), [source manifest](heldout/manifest.json), [all records](heldout/stories_qa.jsonl.gz).
- [Development summary](development/summary.json) and [development samples](development/samples.md), from the earlier wording revision.
- [Implementation](../../storytelling/continuations.py).

Next: populate receivers for the new constructions and evaluate a predeclared
quality or held-out prediction target. More semantic event choices require new
guarded kernels and corresponding QA, beyond this wording/syntax expansion.
