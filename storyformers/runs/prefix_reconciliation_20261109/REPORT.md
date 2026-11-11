# Luna annotation review and reconciliation

Reviewed 2026-11-09. The complete **753-word trail story** was aligned against
the existing agent-authored, independently reviewed annotation. I inspected all
POS/lemma disagreements and selected **17 causal prefixes** for detailed semantic
review, two live Luna/Flex prompt trials, and explicit agent corrections.

The original full-story Luna output remains unchanged. The corrected examples
below are a selected review set, **not a newly corrected 753-word training corpus**.

## Whole-story comparison

| Measurement | Reviewed retrospective labels | Original causal Luna |
|---|---:|---:|
| Lexical records | 753 | 753 |
| Top-level field occurrences | 6,838 | 6,008 |
| Distinct field names | 132 | 98 |
| Mean fields per word | 9.08 | 7.98 |

Agreement was **741/753 for POS (98.4%)** and **748/753 for lemma (99.3%)**.
These are agreement figures, not accuracy scores. Counts exclude token/index,
positions and reserved supporting tables; those tables carry additional meaning.

The main deficit was semantic coverage: the original Luna records contained no
top-level goal, social-commitment or narrative-family fields, compared with 22,
14 and 3 field occurrences respectively in the reviewed version. Dialogue-family
fields occurred 9 times versus 347. This does not establish that all of the
retrospective fields were available at their respective prefixes.

**Do not copy the whole-story labels backward.** At `placed`, the compass and
recipient have not appeared. At bare `wanted` or `hoped`, the content is still
unknown. Those omissions are correct. The completed goal can instead appear on
the later complement's record, while the earlier record remains immutable.

The [lexical adjudications](lexical_adjudications.json) distinguish prefix
ambiguity from tagging conventions: for example, `to`, `until`, `brass`, and
`her` can lack the continuation used by the retrospective tag. Participial
adjectives also differ in whether their lemma is the adjective or base verb.
I did not turn these disagreements into automatic error labels.

Full counts and differences: [comparison.json](luna_v3_refined/comparison.json).

## Contract reconciliation

The default prefix contract is now **v3**, with the original 1,024 definitions,
seven existing extensions, and two new typed bundles: **1,033 registered names**.
This is a vocabulary, not a requirement to emit 1,033 fields or an increase in
the number of implemented grammar heads.

| Meaning from the Grammarworlds inventory | Storyformer treatment |
|---|---|
| Plot function, stage, archetypes, cast, stakes, earlier narrative links | New `plot` bundle. `plot.role` stays separate from participant `role`; readings are prefix-grounded candidates. |
| Literal drawings/reflections and their physical carriers | New `depiction` bundle; image, carrier and optional real referent retain separate identities. |
| Desired outcome / motivation / goal progress | Reuse `goal_owner_id`, `goal_content_id`, `goal_status`, `goal_motivation`, `goal_tradeoff`, and related `goal_*` fields. |
| Promises and open obligations | Reuse `promise_content_id`, `plan_commitment_status`, `obligation_*`; do not infer fulfilled obligations from a promise alone. |
| Belief and supporting evidence | Reuse `belief_*` and `epistemic_*` with holder/content/scope bindings. The extra belief example exercises the contract; this trail replay is not a live belief benchmark. |
| Narrative expectations, tension, changes and closure | Reuse `narrative_expectation`, `narrative_tension_*`, `narrative_change_*`, `narrative_resolution_evidence`, `narrative_closure_candidate`. |
| Shared entity/recipient bindings | Existing `entity_id`, `antecedent_id`, `recipient_id`, `entity_merge_candidate` and scoped reference tables. Prompt support does not prove stable model resolution. |
| Time estimates / deadlines | Existing `temporal_*` fields; available time differs from actual duration. Local token positions remain separate. |
| Native dependencies, replayed effects, sampled simulator times, executable plot-stage transitions, source-transfer provenance | Not fabricated from prose. These require engine evidence or a separate implementation. |
| Plot reranking weights and joint next-token distributions | Outside annotation reconciliation; adding labels does not implement a planner or trained projection. |

The prompt now has **18 causal examples**, plus a compact checklist after the
large catalog and before variable story text. It explicitly asks for the word's
enclosing goal/promise/operator content, including on nouns and pronouns. It
also addresses earliest possessive-name anchors, imperative actors, nested quote
scope, lexical modal classes and depicted referents. Existing examples avoid
the trail's target answers; diagnostic expectations are never sent to Luna.

Validation checks the new bundle shapes and allowed values, rejects future
plot evidence and invented mechanical verification, requires distinct image
identity, checks quotation anchors, and rejects cyclic scope ancestry. Validation
cannot establish semantic truth or correct coreference.

## Live regression results

Both trials used `gpt-6-luna`, Flex, low reasoning, eight-way concurrency, explicit
30-minute prefix caching, shortest-prefix warmup, and up to three validation
corrections per word. Each word saw only its own prefix; no prior annotations.

| Version | Diagnostic checks passed | Cases satisfying every check |
|---|---:|---:|
| Original full-story Luna records, same selected words | 13/50 | 3/17 |
| First v3 prompt trial | 25/50 | 6/17 |
| Refined v3 prompt, now the default | **39/50** | **9/17** |
| Separate agent-reconciled examples | 50/50 | 17/17 |

These are **selected, development-time diagnostics, not held-out accuracy**.
The review suite evolved while inspecting outputs: I corrected my q958/q959
off-by-one error, accepted the equivalent `negated_ability` scope name, and added
binding checks after richer records exposed wrong identities. The table rescores
all versions against the same final 50 checks. Frozen per-trial specifications
and their original evaluations remain available. The agent-corrected row is a
consistency check on authored examples, not an independent model score.

On these same 17 words, top-level fields increased from **163 / 28 distinct**
to **224 / 48 distinct**, or **9.59 to 13.18 per word**. More fields were useful,
but were not always correct:

- `her` after “promised to keep beside her” acquired promise fields, but Luna
  bound it to **Nia instead of Leni** and omitted the joint promiser group.
- `minutes` and `sprint` retained the right person names but used later or
  noncanonical entity anchors. The manual correction restores Felix e155 and
  Leni e193, respectively.
- `detour` stayed conditional but was nested under an already closed quotation.
  The current opening is **q1083**.
- `square` acquired the desired payoff fields, but its goal proposition said
  “Felix wants…” instead of describing **obtaining the stamp**. This passed the
  presence checks and still required semantic correction.
- `Loop`, `trail`, and the final depicted `triangle` still lacked the supported
  choice, setback, and candidate ending-image readings.
- The refined drawing output correctly distinguished the real salamander e1343
  from both the earlier desired referent e216 and its image e1660. The first
  trial had confused the desired and real referents.

The 17 corrected records preserve prefix boundaries and separate observed,
desired, negated and depicted meanings. They are not exhaustive gold labels for
all 1,033 dimensions. An ending-image annotation remains an interpretation;
neither the request position nor absence of future text proves the story is over.

## Artifacts and verification

- [Reconciled records](reconciled_records.json): the 17 explicit agent-corrected records.
- [Reviewed examples](reviewed_examples.json): each exact visible prefix, corrected
  response, source path and review note; suitable for later training/evaluation
  with appropriate train/test separation.
- [Change log](changes.json): changed fields and semantic rationale per word.
- [Final diagnostic evaluation](evaluation.json): all 50 checks on every version.
- Raw trials: [initial](luna_v3/) and [refined](luna_v3_refined/), including frozen
  prompts, requests, responses, correction attempts and accepted records.
- [Usage](usage.json): 44 completed responses across both trials, including 10
  validation corrections; calculated cost about **$0.119** using the archived
  2026-11-08 Luna/Flex rate snapshot. This is not an invoice or a new full-story
  cost estimate. Cache reads were 53.5% and 54.9%; these short, sparse replays
  incurred substantial cache writes despite caching being enabled.

All **42 annotation/catalog tests passed**. All 17 refined accepted records were
checked against their actual provider responses; original and correction requests
reconstructed the exact corresponding prefixes. All 17 agent-corrected examples
passed local type/reference/prefix validation and the review checks. The frozen
v2 prompt remains byte-identical; archived runs use `--contract catalog-v2`.

Rebuild the review artifacts without network calls:

```sh
.venv/bin/python -m storyformers.runs.prefix_reconciliation_20261109.reconcile
```

Use the [replay tool](../../prefix_review.py) with a fresh output directory for
another live comparison. The next meaningful evaluation is a held-out story
with explicit entity, scope and proposition-content scoring, rather than a field
count alone. The updated prompt improves coverage; it does not yet make Luna
annotations reliable enough to treat every returned semantic binding as gold.
