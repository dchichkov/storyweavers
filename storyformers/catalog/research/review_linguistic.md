# Cross-review of the linguistic catalog shard

Reviewed 2026-11-07 against `sources/linguistic.py`, the current Storyformer matcher and registry, and the prefix annotation's compact POS convention. This was a semantic and compatibility review, not an empirical claim that the proposed features improve a trained model.

## Verified scope

- `build()` produces 256 linked attribute/head/grammar triples in eight families of 32.
- 76 grammar seeds use the existing readable neuron DSL; 180 declare adapter requirements for incremental parses, feature unification, syntax-node IDs, scope stacks, and gap/coordination tracking.
- All 76 native grammars parsed and all **152** authored positive/contrastive fixtures executed successfully during review.
- Native grammars use bounded sequences, gaps, literal/finite alternatives, captures, and finite lookup projection. The inspected native subset does not hide recursive parsing, arbitrary unification, graph traversal, or future-token reads.
- Native lexical mappings generally describe finite candidate readings; structural adapters preserve alternative analyses and distinguish syntax from semantic event truth.

## Findings corrected during review

| Finding | Why it mattered | Correction verified |
| --- | --- | --- |
| `mood` mapped modal auxiliaries such as `may` to `modal` | This confounded morphosyntactic mood with modal meaning and duplicated `modal_auxiliary_class`. | Replaced with a visible mandative bare-`be` subjunctive construction. `may/v` no longer triggers `mood`. |
| `negation_marker_form` required `pos=adv` for every marker | Prefix annotations use compact `part` for `not`/clitic negation; the seed could miss actual input while passing its artificial fixture. | The seed accepts `part`/`adv` as appropriate. Direct `not/part` and `never/adv` checks activate. |
| `reflexive_form` forced `themselves` to third-person plural | Singular-they usage means the surface form alone cannot establish plural number. | The value now retains number uncertainty: `third_person_number_underspecified`. |
| `heard singing` was presented as an NP-plus-participial perception construction | No NP is visible, and `singing` may be an event nominal. | The description and output now preserve a `gerund_or_event_nominal_candidate`. A noun-tagged `singing` is not falsely claimed to prove a participial clause. |
| Punctuation was normalized to `unknown` | Locally synthesized punctuation in the actual annotation path uses `pos=punct`. | `clause_speech_form` accepts actual `punct` as well as the older `unknown` convention. Direct `?/punct` activates. |
| Modal lookup treated every `can/v` as an auxiliary | The repository's compact `v` does not distinguish modal `can` from lexical canning. | Ambiguous `can` was removed from this finite seed; it now abstains pending a richer construction. |

Relevant current source locations: [lexical seed helper](/Users/dmitry/storyweavers/storyformers/catalog/sources/linguistic.py:32), [reflexive morphology](/Users/dmitry/storyweavers/storyformers/catalog/sources/linguistic.py:258), [verbal seeds](/Users/dmitry/storyweavers/storyformers/catalog/sources/linguistic.py:331).

## Two further naming/scope clarifications corrected

1. `agreement_controller_id` used example value `np1`, a constituent-node identifier, while its computation text said “NP head anchor,” which suggests a token anchor. The computation now explicitly returns the NP node ID. The distinction matters for downstream joins.
2. The native suffix `Who left` also fits a still-open interrogative clause embedded as a subject, as in `Who left remains unknown`. Its output is now `subject_wh_clause_candidate`, with independent-question versus embedded-interrogative ambiguity stated explicitly. Clause category and speech act remain separate.

These are finite-seed precision improvements, not reasons to force a general parser into the native matcher.

## Remaining limits to retain in documentation

The native subset has intentionally narrow lexical coverage. “No match” for an unlisted word means unknown coverage, not grammatical invalidity. Positive-only detectors such as an irregular-form flag need separate evidence before writing false. Likewise, a partial prefix may admit both a completed constituent and an open extension; adapter outputs must preserve that ambiguity rather than retroactively importing the eventual continuation.

Several scalar fields describe a selected constituent or dependency rather than the current surface token itself. A future adapter should preserve the selected parse-node/edge identity when writing these into the current residual slot; otherwise a consumer may accidentally interpret an adjective's relation as the current noun's relation. The catalog declares these scopes, but the current residual runtime does not enforce a full parse-node type system.

The shard's source citations motivate grammatical distinctions. They do not establish these exact authored fields, examples, or neuron layouts as extracted GF rules or discovered neural mechanisms. The GF-inspired local implementation is a selected Python adaptation, not a full GF compiler/runtime.
