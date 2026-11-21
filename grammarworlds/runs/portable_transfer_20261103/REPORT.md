# Python grammar-port transfer trial — 2026-11-03

Selected GF rules were adapted into our own typed Python grammar and weighted
Node/Forest sampler. Codeco's reference/scope mechanism was independently
implemented from its paper. **This generator does not call GF.** It is not a
complete GF RGL or ACE grammar port.

The catalog has 29 contracts: 21 GF-derived adaptations, three Codeco-style
mechanisms, and five local composition/binding constructions. Counts refer to
contracts/functions, not raw grammar productions. Their responsibilities overlap
with the baseline's 34 labels; the counts must not be added.

## Transfer boundary

Rescue, kite, key, and music were developed first. The recovery world guards and
effects remain the original ones. Music semantics were extracted from the saved
Terra pack, while realization now uses shared typed constructions.

We then froze shared Python/core-lexicon hashes in
`../../portable/sources/pre_holdout_freeze.json`, before reading the greenhouse
source `storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/03_greenhouse/story.txt`.
Its compact adaptation needed:

- **0 new or modified shared grammatical constructions.** Frozen hashes match.
- **32 lexical entries:** 18 nouns, 8 adjectives, 6 verbs, not all used in every story.
- **13 new event kernels**, with explicit resource, location, shade, repair, and
  return state; plus their event-to-phrase mappings.

This demonstrates reuse across one additional manually authored story. It is
not a blind/generalization benchmark. Richer details of the source, such as the
specific broken clip, the grandmother's porch, and the final droplet, are omitted
or simplified. The held-out world still needed substantial semantic authoring.

## Mechanical audit

100 consecutive seeds, 0–99, in both past and present. No filtering, repair,
deduplication, or selecting only successful samples. All word distributions use
the original exact finite-forest marginalization; meanings remain latent until
the sampled sentence finishes.

| World | Completed and replayed | Guard interventions | Distinct event-kind sequences |
| --- | ---: | ---: | ---: |
| Rescue | 200/200 | 200 | 9 |
| Kite | 200/200 | 200 | 12 |
| Key | 200/200 | 200 | 15 |
| Music | 200/200 | 740 | 24 |
| Greenhouse transfer | 200/200 | 1,000 | 17 |
| Total | **1,000/1,000** | **2,340** | — |

The audit traversed 112,072 predicted symbols, including punctuation/stopping;
9,656 steps offered multiple next symbols. Event-kind sequences are not distinct
plots, and agreement/tense variation is not narrative diversity.

Interventions check held tools; both music performers' presence/instruments;
consent; returning both instruments before an ending; finite water sources;
a full can before watering; and repaired shade before closing temporary cover.
This set is diagnostic, not proof that every possible intervention is handled.

The full suite passes **33 tests**, including the original baseline tests and
10 port tests. One port test checks **51 raw GF-generated reference sentences**,
normalizing initial capitalization and the documented contracted/uncontracted
negative difference. Other tests cover argument types, agreement, object case,
possession, articles, scope leakage, prediction purity, prefix normalization,
world replay, distinct same-kernel frames, and the held-out hash boundary.
Generation also runs with Python's site packages disabled (`python -S`).

## Author context

The query `complement hope invitation` retrieves **8 contracts / 1,867 characters**
under a 3,000-character cap, without implementation source. Dependency closures
are included; a contract is omitted whole if its closure cannot fit. A test adds
100,000 unrelated synthetic metadata entries and gets the same context. Those
are **not 100,000 executable grammar rules**, and no Terra authoring rerun was
conducted. This tests prompt selection, not model performance or grammar runtime
scalability.

## Quality and limitations

The new prose is generally plainer than Terra's original hand-authored music
realization. It preserves visible problems, turns, and ending states, but often
reads like an event log. Repeated names, sparse sensory detail, and constrained
plots remain. Existing Luna/Terra judge scores do not apply to this version;
**no literary quality or diversity improvement is claimed**.

The grammar handles a selected English subset. Codeco scopes/reference matching
are present, but its ACE rule inventory and chart parser are not. The generator
still enumerates a finite forest, capped at 512 derivations per event frame.
Large recursive grammars require further runtime work.

The next experiment should judge this version independently, improve shared
discourse/aggregation, then transfer to more source stories using focused
rule/lexicon contexts and record every new construction required.

## Artifacts and reproduction

- `stories.jsonl`: all 1,000 stories, frames, and final physical states.
- `samples.md`: first four past-tense seeds per world, **20 unfiltered examples**.
- `*_trace.json`: first past-tense seed per world, full word probabilities and states.
- `summary.json`: counts, retrieval result, source-story hash, elapsed time.
- `source_hashes.json`: implementation hashes used for the audit.
- `../../portable/sources/`: upstream provenance/license, freeze, GF oracle outputs.

```sh
.venv/bin/python -m grammarworlds --verify
.venv/bin/python -m grammarworlds.portable.audit --out /tmp/new-port-trial --count 100
.venv/bin/python -S -m grammarworlds.portable --scenario heldout --seed 7
```
