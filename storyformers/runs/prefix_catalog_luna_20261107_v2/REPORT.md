# Luna/Flex causal catalog annotation smoke run

Input: `Mara took scissors. She did not cut the ribbon.`

Nine word prefixes produced nine accepted word records, with ten spaces and
punctuation spans generated locally. Concatenating all 19 records reproduces the
source exactly. The model was gpt-6-luna on Flex, low reasoning, with four parallel
requests after the shortest-prefix warmup. No previous position's model response
was supplied to a later position.

The shared prompt contains the complete 1,024-field definitions, seven agreed
extensions and nine causal examples. Its naming, scope, polarity, uncertainty,
representation and physical-state guidance is adapted from the reviewed
whole-story v4 prompt. The retrospective policy and examples were replaced with
prefix-only guidance. Output uses sparse typed JSON with local validation, plus
per-prefix reference snapshots rather than a merged retrospective entity table.

## Measured result

| Measurement | Result |
| --- | ---: |
| Accepted lexical records | 9 |
| Local nonword records | 10 |
| Provider responses, including correction | 10 |
| Validation corrections | 1 |
| Peak simultaneous requests, from dispatch journals | 4 |
| Input tokens across all 10 responses | 575,812 |
| Cached input tokens | 517,542 |
| Cache-write tokens | 57,691 |
| Output tokens, including reasoning | 2,997 |
| Cache-read share, including cold warmup | 89.88% |
| Cache-read share after cold warmup | 99.82% |
| Distinct feature keys used, including event_bindings | 34 |

These totals include both the rejected and corrected scope record. Raw usage and
dispatch evidence are saved beside each response. The summary's elapsed time is
the final resume invocation, not an end-to-end latency benchmark. Frozen request
bodies, the shared prompt and all provider responses are retained.

## Semantic inspection

All nine final records and their supporting tables were read against their exact
prefixes. `Mara` introduces a person without anticipating an action or assigning
age/gender. `took` establishes an obtain event with empty patient/instrument lists.
`scissors` adds the now-seen patient in its own reference snapshot and supplies
Mara as holder. `She` resolves to Mara. `did` keeps its auxiliary-versus-lexical
interpretation unresolved at that boundary. `not` opens a negation scope without
inventing its following predicate. `cut` records a negated cutting event with
unknown patient/instrument. `the` begins an incomplete noun phrase. `ribbon`
supplies the negated event's patient, without asserting a cut or treating the
earlier scissors as an observed instrument. The earlier records remain unchanged.

This is a small smoke sample, not a general semantic accuracy estimate or a claim
of exhaustive annotation. It exercises 34 keys out of the available catalog.
Companion references remain per-prefix snapshots; downstream grammar lookup of
these tables still needs an explicit adapter.

## Failures and corrections

The first attempt, preserved in `../prefix_catalog_luna_20261107/`, used `Lily
took scissors. She did not cut the thread.` It made nine provider calls. Local
validation rejected the unsupported event_type `cut`; semantic inspection also
found that the open `cut` prefix incorrectly assigned the earlier scissors as
its patient. That attempt is retained as a diagnostic, not an accepted dataset.

The prompt was revised to include all enum values, an explicit distinction
between an available earlier object and a new predicate's patient/instrument,
and a ninth causal example. The new run used the different Mara/ribbon text.
Its `cut` record correctly left patient/instrument unresolved.

One new-run record used s11 for `not` at lossless index 11, instead of s12. A
single separately journaled correction supplied the validation error and allowed
span anchors after the unchanged cached prefix. Luna returned s12. Both responses
are preserved in `prefixes/000011/response.json` and
`prefixes/000011/repairs/001/response.json` under the story directory. No accepted
response was manually edited. The runner permits at most one such validation
correction; refusals, incomplete/wrong-tier responses and ambiguous dispatch
failures are not retried by this mechanism. Both calls count toward usage.

## Files and verification

- `000000_f5388058b2ce/annotations.json`: assembled causal latent stream.
- `000000_f5388058b2ce/reference_snapshots.json`: supporting metadata by target.
- `prompt.json`, `manifest.json`, `summary.json`: frozen inputs and run metadata.
- `measured_metrics.json`: measured cache, concurrency and record counts.
- `000000_f5388058b2ce/prefixes/`: every request, response, validation and attempt.

Offline tests cover catalog types/enums, future-reference rejection, identical
requests for identical prefixes with different continuations, cache boundaries,
local nonwords, unchanged earlier snapshots, bounded parallel scheduling,
validation-correction limits, complete usage accounting and credential-free
reuse of saved responses. The accepted live sample also passed exact source
reconstruction and local validation. These are structural checks; the semantic
inspection is described separately above.

The existing explicit cache boundaries and 30-minute TTL follow the
[official prompt-caching guide](https://developers.openai.com/api/docs/guides/prompt-caching).
The runner retains the [Flex timeout and tier](https://developers.openai.com/api/docs/guides/flex-processing),
with SDK automatic retries disabled and definite Flex-unavailable retries only.
