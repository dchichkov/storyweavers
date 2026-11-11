# Pilot review and prompt v1 decision

Both pilots have been read against their full source and corrected after an
independent semantic review. Shape/type/link checks are clean. These are reviewed
annotations with documented ambiguities, not a claim of exhaustive or infallible
semantic labels.

| Story | Words | Lossless records | Entities | Events | Scopes | Propositions |
|---|---:|---:|---:|---:|---:|---:|
| 01 bakery | 854 | 1,941 | 68 | 160 | 46 | 30 |
| 02 puppets | 841 | 1,899 | 63 | 165 | 45 | 42 |

The pilots together use 302 canonical fields from the available 1,024. Sparse
omission means unknown or unannotated. The highest per-word field count in either
pilot is 35; no activation quota was imposed. Spaces and punctuation are generated
locally; every word has manually selected contextual POS and lemma.

## Corrections and lessons carried forward

- Participant arrays use entity IDs. The original catalog's display-name examples
  conflict with the existing annotation pipeline; the explicit trial override
  resolves this without silently modifying the catalog.
- Historical repair/telling references now share event identities; actual speech
  acts remain separate. Secondary physical/fictional events retain their own
  participant bundles. The final bakery inscription addressee was corrected to
  Hobb rather than inheriting the dialogue audience.
- Semantic actor no longer supplies grammatical subject unconditionally.
  Part/whole metonymy and physical-prop/fictional-object roles have explicit links.
- Negated desire is not automatically an avoidance goal. Goal and promise content
  propositions describe the intended state/action, rather than embedding the
  whole desire or promise again.
- Assertion attribution, event factuality and commitments have separate fields.
  The three shared assertion statuses are checked inside object bundles too.
- Modal/pronoun/contraction lemmas follow an explicit shared policy. Exact source
  surfaces remain unchanged. Anchors retain their stated, distinct units.
- Empty containers can have restricted domains; linings are parts, not contents.
  Appearance is distinct from material, and reflection from light emission.
- Prospective returns, rejected plans, performed fiction, recalled events and
  tentative emotion interpretations retain their own scope and evidence.

Five provisional shared definitions are available in the v1 extension registry:
`event_bindings`, `figurative_mapping`, `enactment`, `appearance_color` and
`part_whole_relation`. They remain proposals beyond the original catalog and are
not automatically installed in the Storyformer runtime. The helper can reuse an
exact agreed definition with `use_extension`.

## Next batch

Prompt v0 is frozen with the pilots. Prompt v1 adds the lessons above, four
concrete examples extracted from the corrected annotations, the shared extension
registry, and a requirement to report source continuity gaps rather than invent
missing events. Batch 1 uses v1 for all six stories (03–08). Its feedback will be
reviewed as a group before preparing v2.

The user requested six concurrent annotation workers. An additional-worker probe
was rejected with `agent thread limit reached` while three workers and the root
coordinator were active. Therefore the six-story logical batch uses two waves.

See `pilot_preflight.md` for the independent review and each pilot's `feedback.json`
for unresolved ambiguity. Partial dependency coverage, non-exhaustive event
segmentation, and heterogeneous legacy property strings remain known limitations.
These are whole-story retrospective annotations, as requested; the separate
causal-prefix corpus has not been produced by this run.
