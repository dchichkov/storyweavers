# Batch 1 review — stories 03–08

Status: accepted. All six stories and the requested review corrections are
complete and verified. Prompt v2 is released for stories 09–14.

All six stories used frozen prompt v1 and the full 1,024-field catalog. Each
author read the complete story, explicitly annotated every word, reviewed the
assembled paragraphs, and supplied feedback. Spaces and punctuation are
synthetic lossless records. This is retrospective whole-story annotation with
local time and scope preserved, not causal-prefix annotation.

| Story | Words | Entities | Events | Distinct fields |
|---|---:|---:|---:|---:|
| Greenhouse | 738 | 76 | 129 | 126 |
| Seaside | 806 | 70 | 142 | 180 |
| Library | 759 | 73 | 139 | 221 |
| Snow | 849 | 84 | 156 | 166 |
| Picnic | 724 | 72 | 144 | 131 |
| Music | 732 | 70 | 136 | 168 |

This batch contains 4,608 words. Together with the two pilots, the run contains
6,303 annotated words. Field counts describe sparse use, not coverage quotas.
The available vocabulary remains all 1,024 catalog fields plus declared
extensions.

## Semantic review and corrections

- Greenhouse: corrected quotation audiences and a stale label-authorship
  description. Kept uncertain earlier snap chronology, plant/tray identity and
  the distinction between temporary shade and repair.
- Seaside: changed a false-belief content used as an actual cause to the actual
  attitude event; corrected positive negation targets, conditional requirement
  versus intention, downward restraint versus support, opening-only partial
  goal satisfaction, and prepositional versus direct object.
- Library: corrected Grandma's audience without changing the joint departure
  group, and preserved the exact negative content of “Not my whale.” No atlas
  checkout, invented bookmark reinsertion or reshelving performer was added.
- Snow: corrected information-seeking versus outcome desire, ability bearer,
  inherited quote attribution, local attribution of recalled events, exact
  offered/requested subtasks, and the event targeted by noncompletion. Removed
  an unsupported precise stopping location. Legacy attributes now follow the
  catalog's name/string-value wire format, also enforced by validation.
- Picnic: separated positive event content from negation and actual denial
  utterances, with explicit negation targets. Retained the sign/jug continuity
  gaps, sandwich identity alternatives, and unobserved blanket return.
- Music: author preserved program refusal versus seat tapping and the voluntary
  informal duet. Independent review requested positive content labels and a
  separate proposition for Nia's uncertainty about Mateo's desire. These,
  overt-pronoun syntax and distinct pause occurrences are corrected and verified.

Independent review evidence lives in `batch1_independent_03_04.md`,
`batch1_independent_05.md`, `batch1_independent_06.md`, and
`batch1_independent_08.md`. Root's picnic review is in `batch1_root_07.md`.
Authors' full feedback remains beside each story's annotation.

## Vocabulary and prompt decisions

Accept one additional provisional name: **affordance_supporting**. It means
explicit capacity of a surface to support a specified object, not actual
placement, bodily sitting or containment. Use the bound object payload
`{object_id, can_support}` and omit unknown placement. Reuse the previous five
extension definitions unchanged. No other batch author required a new name.

Prompt v2 includes the lessons collected in `prompt_notes_batch1.md`,
concrete corrected word excerpts, and the updated extension registry. The main
improvements concern content/polarity, inherited scope, information goals,
specific consent, roles versus audience, source gaps, and physical relations.
Retain finite/nonfinite and lemma checks and prefer existing typed fields over
new aliases.

Machine validation proves losslessness, word/POS coverage, feature registration,
types and checked references/provenance. Full-story author and independent
reviews supply the semantic evidence. Neither establishes a complete ontology
or proves that every possible feature has been annotated; supported sparsity
and explicit uncertainty are intentional.

Gate evidence: `review_run.py` verifies all eight completed story folders with
zero errors, 6,303 reconstructed words, and 429 distinct canonical fields used
across the pilots and batch1. All eight feedback files report complete author
review. Independent review files record the resolved findings. Prompt v0/v1
remain frozen; v2 and its examples/registry are saved under `prompts/`.
