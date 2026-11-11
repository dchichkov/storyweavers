# Final consistency verification: 12_orchard and 13_costume

Accepted. This was a bounded comparison of the final consistency corrections, not a new broad story review. I compared every current annotation record and all companion files against the preserved snapshots, read the affected source paragraphs and catalog definitions, and independently reran validation.

## 12_orchard

Exactly seven word records changed, each only in `modal_auxiliary_class`:

| Word | Surface | Previous value | Current lexical family | Preserved `modal_base.kind` |
|---|---|---|---|---|
| 119 | may | permission | may | permission |
| 178 | can | permission | can | permission |
| 440 | could | ability | can | ability |
| 597 | won’t | prediction | will | prediction |
| 603 | might | epistemic_possibility | may | epistemic_possibility |
| 608 | can | ability | can | ability |
| 751 | will | prediction | will | prediction |

A0418 defines a lexical modal class without imposing a contextual modal sense. The normalized modal lemmas keep that lexical distinction separate from the existing permission, ability, prediction, and epistemic interpretations. The local borrowing permission, crate permission, hypothetical reach, pear-preference predictions, and cutting ability retain their holders, targets, polarity, and scopes. All other fields on these records are identical to the snapshot. Only `author.py` and `annotations.jsonl` changed; all companion artifacts are byte-identical.

## 13_costume

Exactly one annotation record changed: w761, “rested,” lost `spatial_frame_kind=mirror_reflection`. A0515 concerns intrinsic, observer-relative, or geographical direction frames; a mirror-reflection world is a different semantic distinction. The existing `spatial_configuration` still places the cape between the crescent and ribbon in the reflected arrangement, under scope s15. The physical return to the cupboard and hook remains distinct.

The corresponding evidence entry now names only `spatial_configuration` and explicitly explains that the mirror arrangement is neither a directional reference frame nor a relocation of the physical cape. The only other changes are the matching authoring line and derived validation counts: the removed field lowers the distinct-feature count from 179 to 178. Entity, event, scope, proposition, metadata, feedback, and extension files are unchanged.

## Verification and provenance

- Both independent validator calls returned zero errors.
- Snapshot annotation hashes match `reviews/annotation_snapshots.json`: orchard `7a9395d0de61f290a2163b9a8c8c07c0475881e64b965ea674dfd3a154371933`; costume `9f77405778ed6e91f6bcb28ac85a5985336657cd77b30f28f5f4097bed70484d`.
- Current annotation hashes: orchard `58e9d1ac7b9f3d0c7ebd764a8e114fa17e0486ff4a03bd0aaa3bd3e4deaf4adc`; costume `aa143107a90af56628a789994164922795cd1e3555b6dd432c729828f1a803d0`.
- Token counts and lossless token records are unchanged: 1,859 orchard tokens and 1,757 costume tokens.
- No unrelated annotation or companion-file changes were found. No separate per-word review views exist for these stories in the run, so none required regeneration.
- Frozen prompts, examples, registries, and preserved snapshots were not edited during this verification.
