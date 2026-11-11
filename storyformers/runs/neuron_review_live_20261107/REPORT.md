# Offline neuron revision smoke check — November 7, 2026

This round used only the generated 19-token synthetic corpus from the induction
baseline. The corpus and trained model were regenerated exactly to verify that
no user stories or private training data entered the payload; see
[synthetic_payload_check.json](synthetic_payload_check.json).

The selected neuron was layer 0, head slot 3, originally `learned_4`:

```text
match: any earlier tokens, then current.pos = v
emit:  __grammar_4 = true
```

The [training profile](profile/profile.json) records 192 matched targets out of
1,311. Its evidence includes different valid continuations of identical verb-final
prefixes and their positive/negative contributions relative to ablation.

## LLM proposals

The [first Luna/Flex proposal](proposal/proposal.json) left the neuron unchanged,
citing insufficient evidence to narrow its pattern without losing useful
continuations. The next call supplied an explicit naming-only objective; its
[proposal](canonical_names/proposal.json) renamed the neuron to
`suffix_verb_context`, retaining the grammar, feature and weights. The LLM did
not propose an attribute binding. The binding/reuse mechanisms are covered by
local tests; this live round demonstrates neuron naming.

| Call | Input tokens | Cached input | Cache write | Output tokens |
| --- | ---: | ---: | ---: | ---: |
| General revision | 6,022 | 0 | 1,267 | 479 |
| Naming objective | 6,063 | 1,267 | 0 | 575 |

Raw requests, responses, usage, dispatch journals and proposals are retained in
the corresponding directories. Only training evidence was sent to Luna. The
second call reused the fixed instruction prefix despite its different objective.

## Evaluation

The [naming evaluation](canonical_evaluation/evaluation.json) accepted the
revision on 443 validation targets:

| Metric | Before | After |
| --- | ---: | ---: |
| Joint next-latent NLL | 1.0461159744254949 | 1.0461159744254949 |
| Target coverage | 100% | 100% |
| Contradictions of observed attributes | 0 | 0 |
| Grammar complexity | 1,113 | 1,113 |

No weight refitting was used. The original checkpoint is untouched. The accepted
copy, including registry metadata, is
[accepted_model.json](canonical_evaluation/accepted_model.json). This is a
behavior-preserving naming change, not a likelihood improvement or proof of
semantic correctness. Test examples did not participate in proposal generation
or acceptance.
