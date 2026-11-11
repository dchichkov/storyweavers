# Final live annotation check

Two sequential requests used `gpt-6-luna`, Flex, low reasoning and the same
instruction/schema/five-example prefix. Both completed, passed local validation,
and were read together with their original text. No model output was edited.

| Story | Words | Cache reads | Cache writes | Result |
| --- | ---: | ---: | ---: | --- |
| `Lily took scissors, needle and some thread` | 7 | 0 | 6,795 | Accepted |
| `Lily, a girl, took scissors, a needle and some thread. She used them to mend her torn coat.` | 18 | 6,795 | 0 | Accepted |

The second, different story reused the complete shared cached prefix. Both
outputs preserve every original character, including spaces and punctuation.
The corresponding arrays and provider usage are saved in each story directory.

Manual observations:

- The short fragment labels Lily as a person and `took` as `obtain object`.
  It identifies scissors, needle and thread as three distinct patients and
  does not invent a repair purpose.
- The extended story labels Lily as a girl, resolves `She` and `her` to her ID,
  and labels the acquisition `obtain repair tool`. The `mend` repair event
  affects the coat and uses the three previously obtained objects.
- `She`, `used`, `them`, `mend` and `coat` share the repair event ID `ev2`.
  There is no phantom event link. The plural `them` links by role/event without
  inventing a separate unsupported entity that combines the tools.
- The structured attributes extension is present on every token. Additional
  attribute types can be introduced through the prompt and consistent examples.

The [initial run](../annotation_smoke_20261106/REPORT.md) exposed an event link
without a trigger. The [second run](../annotation_smoke_v2_20261106/REPORT.md)
fixed that link but over-inferred a repair purpose in the short fragment. Their
raw evidence remains saved. The final prompt adds an explicit construction rule
and a contrasting tool-only example.

Verification: 43 offline tests passed across `storyformers.test_annotation`,
`storyformers.test_storyformers`, and `grammarworlds.test_grammarworlds`.
Tests cover exact reconstruction, malformed/omitted tokens, entity/event links,
pronoun and negation examples, cache boundaries and transport, saved response
reuse, rejected output retention, and safe handling of uncertain dispatches.
The original frequency predictor's demo remains deterministic.

Scope: two short development stories establish wiring and cache reuse, not a
held-out annotation accuracy score. Entity, event and purpose labels remain
model judgments. Full-story labels can use later evidence and are offline
supervision, not automatically valid causal predictor inputs.

Official request semantics: [prefix caching](https://developers.openai.com/api/docs/guides/prompt-caching),
[Flex processing](https://developers.openai.com/api/docs/guides/flex-processing),
and [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna).
