# Symbolic heads in the story generator

The seven-world generator can rerank every next-word distribution using symbolic
heads. This is an opt-in experiment with authored weights, not a trained model.
The existing event-level attention remains enabled independently.

```sh
.venv/bin/python -m grammarworlds.storytelling --scenario pottery --seed 7 --heads --qa
.venv/bin/python -m grammarworlds.storytelling --scenario all --heads --head-strength 0.5
.venv/bin/python -m grammarworlds.storytelling --scenario library --heads --head-ids P023 --json
.venv/bin/python -m grammarworlds.storytelling --scenario all --heads --head-profile seed
```

Python: `generate("pottery", 7, symbolic_heads=True, head_strength=1.0)`.
Omitting `--heads` preserves baseline sampling. Strength zero preserves the
baseline draws while recording activations. Strength must be finite in [0, 10].

Add `--continuations expanded` (Python: `continuations="expanded"`) for a wider
typed grammar: lexical alternatives, recipient order, tool-phrase placement,
direct/polite wishes, tentative offers, and clause splitting. Original remains
the default. The [continuation comparison](../runs/expanded_continuations_20261105/report.md)
tests both grammars with heads off/on. Agreement receivers now abstain from
influencing construction choices unless competing agreement forms exist.

## What is attached

The library has 15 table heads and 49 deferred program heads. The adapter loads
the 15 tables, but supplies inputs for **six**; this does not make all 64 live.

| Head | Live input | Current limitation |
|---|---|---|
| P001 subject number | Explicit subject's physical entity and number | Conservative name/pronoun matching; grammar already enforces agreement |
| P002 person agreement | Pronoun at the current prefix boundary | Grammar already chooses the correct form |
| P007 coordination | Exact seed-table conjunct immediately before and/but/or | Only those seed patterns are recognized |
| P013 word sense | Current cue word plus an earlier exact cue in the same event prefix | No general word-sense parser |
| P023 instrument suitability | Union of guard-approved instruments for the resolved actor | Manual profile projects tool affordances into action-word preferences |
| P059 contextual continuation | Current subject/speaker's carrier-bound concept magnitudes | Manual high/low bins and lexical preferences; no learned counts |

P003–P006, P015–P016, P032, P044, and P047 await adapters for their structural,
ordering, restoration, register, or speech-intent inputs. Their tables can run
when explicitly supplied inputs, but are not activated by this adapter.
Selecting a deferred program head such as P024 raises `ProgramRequired`.

In the current samples, four heads activate: P001, P002, P023, P059. Only P023
and P059 change distributions. P007/P013's supported patterns do not occur.
The output metadata records `adapted_ids` and `awaiting_adapter` separately.

## Manual weights

Edit [head_weights.json](head_weights.json). This separate live profile leaves
all 150 original executable seed examples unchanged. The `seed` profile uses
the original tables; their sparse illustrative vocabulary has little overlap
with this generator's actual inputs and decisions.

- P001's manual profile accepts entity-number keys rather than enumerating
  every character's name in the original seed table.
- P023 maps a physically available tool to an affordance: sponge → shape,
  ladder → reach, lantern → illuminate, tape → repair. It favors appropriate
  direct verbs by 2 and use/used/uses by 0.7. At a 50/50 shaped/used fork,
  strength 1 yields `2 / (2 + .7) = 74.07%` for shaped. This is a stylistic
  extension of the original instrument-selection head, not evidence that it
  learned tool use. Some other affordance multipliers are 1.4.
- P059 reads concepts only from an existing person. A magnitude ≥0.5 selects
  the high bin; an absent concept supplies no feature. For example, high Fear
  applies a 0.85 multiplier to can, low Fear applies 1.15, and high Desire
  favors want/choose by 1.2. The current query is the last subject word.
  These are experimental heuristics, not validated psychological relationships.
  This profile explicitly uses **multipliers**, not fabricated corpus counts.
- Several retrieved concepts share attention; their log adjustments are
  weighted by their feature masses. A single concept's multiplier therefore
  need not appear undiluted in the final probability.

Concepts stay attached to physical people and instruments to guarded world
actions, aligning the experiment with the memeplex north star. There is no
runtime LLM and no invented unembedded concept carrier.

## Sampling and trace

For each allowed word, the adapter adds the head's weighted log multiplier to
the grammar's log probability, then normalizes across the existing candidates.
It never adds new words or removes positive grammar support. The receiver can
change both wording and the mass of compatible event branches.

Inputs use the emitted prefix and committed world. A quote's explicit speaker
can resolve “I”; an ambiguous third-person pronoun abstains. Complex and
possessive subjects abstain. The adapter does not inspect a chosen future frame
or suffix. Candidate tools come from all currently legal frames for that actor,
not from whichever frame will eventually be sampled.

Every word trace records original and adjusted probabilities, head features,
source entity/token IDs, attention weights, log adjustments, and total variation
distance. Activation alone is not usefulness: equal changes to every allowed
candidate cancel during normalization. `head_total_variation` measures the
actual change, and the comparison distinguishes active from effective heads.

Sequence likelihood is now the product of adjusted word probabilities. The
old forest mass is stored separately as `grammar_probability`. The conditional
posterior over frames for identical completed text remains valid: every
derivation of that text receives the same prefix/world factors, so they cancel
in that conditional posterior. State changes still occur only after commitment.

## Evaluation

```sh
.venv/bin/python -m unittest grammarworlds.test_story_heads grammarworlds.test_storytelling
.venv/bin/python -m grammarworlds.storytelling.head_comparison \
  --out /tmp/story-head-comparison --start 1000 --count 20
```

The comparison uses identical grammar and seeds for off, original seed tables,
manual tables, tool-only, and state-only profiles, across all seven worlds and
both tenses. It checks completion/replay, supported normalized word choices,
dialogue, full responses, question diversity, and exact QA evidence spans.
Saved artifacts include source hashes, summaries, all texts/QA, every changed
distribution, and full traces for the preselected samples.

These are mechanical and diversity measures, not literary quality grades.
Matched seeds also have a limitation: different wording can consume different
numbers of random draws, changing a later plot without a direct plot preference.
The fixed-world/prefix intervention tests isolate head effects from that issue.

See [the experiment report](../runs/symbolic_heads_attached_20261105/report.md)
for measured results and unfiltered paired samples. Useful next work is better
feature/receiver coverage and an independent quality or next-word-loss target,
before expanding the number of heads.

## Shared scene families and optional tuned weights

The [shared-core experiment](../runs/shared_core_iterations_20261105/report.md)
moves common physical effects, transfer guards, lexicon and scene constructions
out of individual world packs. In expanded mode the shared speech families also
offer explicit listeners, `Let me…`, future intentions and explicit future
promises. A capability statement is distinct from an offer. Quote resolution
supports `said/says`, `told/tells <listener>` and `Let me` while requiring an
unambiguous physical speaker.

```sh
.venv/bin/python -m grammarworlds.storytelling --scenario all --seed 3000 \
  --continuations expanded --heads --qa
.venv/bin/python -m grammarworlds.storytelling --scenario all --seed 3000 \
  --continuations expanded --heads --head-profile tuned --qa
.venv/bin/python -m grammarworlds.storytelling.head_comparison --expanded --tuned \
  --out /tmp/shared-core-heads --start 3000 --count 20
```

The separate [tuned weights](head_weights_tuned.json) broaden tool-affordance
coverage, equalize preferences within synonymous action families, and soften
tool/state multipliers. Existing seed/manual weights remain unchanged. On fresh
seeds the merged expanded grammar increases choice-step frequency from 7.36%
to 10.82%; four-way choices do not increase. The tuned receiver changes fewer
distributions (413 versus 425) and texts (18 versus 23 of 280) than manual, with
no established quality advantage. It remains optional. More grammar choices
do not automatically make the existing heads more effective.
