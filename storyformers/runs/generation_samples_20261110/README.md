# Storyformer generation samples — 2026-11-10

All 18 samples shown in the conversation are retained here. The model is the accepted checkpoint from the [learning emulation](../learning_emulation_20261109/REPORT.md). It has a 19-token vocabulary and was trained on token/POS records.

## Sampling protocol

- Empty context: seeds 0–11, maximum 20 new tokens.
- Prompts `Lily ate` and `Lily used`: seeds 0–2 each, maximum 16 new tokens. Prompt records contain POS `pn` and `v`.
- Sample the model's top-ten token/bundle distribution. No filtering, rejection, reranking, or grammar repair.
- All 18 samples generated END before their token limit. Display removes END and spaces before periods; [samples.json](samples.json) retains raw tokens, full latent dictionaries, settings, and the model fingerprint.

| Prompt | Seed | Generation |
|---|---:|---|
| (empty) | 0 | Tom found the red needles. |
| (empty) | 1 | Ben took the red pears. |
| (empty) | 2 | Tom took red apples. |
| (empty) | 3 | Ben slowly found the small apples. |
| (empty) | 4 | Ben quickly found small apples. |
| (empty) | 5 | Mia found the scissors. |
| (empty) | 6 | Tom found the red small pears. |
| (empty) | 7 | Lily quickly took red pears. |
| (empty) | 8 | Ben used red scissors. |
| (empty) | 9 | Lily slowly ate apples. |
| (empty) | 10 | Lily slowly took small scissors. |
| (empty) | 11 | Lily slowly used the small scissors. |
| Lily ate | 0 | Lily ate apples. |
| Lily ate | 1 | Lily ate red pears. |
| Lily ate | 2 | Lily ate pears. |
| Lily used | 0 | Lily used the needles. |
| Lily used | 1 | Lily used red scissors. |
| Lily used | 2 | Lily used scissors. |

Seed 6 retains the awkward adjective sequence “red small.” These are short synthetic sentences, not multi-sentence storytelling.

```sh
.venv/bin/python -m storyformers.sample_generations --out /tmp/storyformer-samples.json
```

Model fingerprint: `1107641e710b7e51a3a5925a0814e32e7fee0c14e3566ab4011b8af9a6b93c70`.
