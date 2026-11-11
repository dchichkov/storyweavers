# Independent review: 12_orchard, frozen v2

Reviewed 2026-11-07. Read the complete 41-paragraph source, all 822 assembled lexical records and their sparse contextual fields, all entity/event/proposition/scope registries, feedback, and explicit grammatical subject/object assignments. Repeated-event bindings were inspected separately. No annotation source or output was edited by this reviewer.

## Findings sent to the author

1. **w680, specific distributive reference is not kind-generic.** `generic_reference=true` on “each oatcake” conflicts with the catalog definition: that field denotes a kind-level generic claim. Here e66 is a variable ranging over the actual two oatcakes e11. Retain the variable, quantifier restriction and two-pieces-per-member relation; omit the generic flag or set it false. This does not require changing the carefully limited count semantics.
2. **ev9/w8, optional capacity-label alignment.** The event label is “Tessa can hear Jun,” with `factuality=hypothetical`. The opening establishes that the orchard is small enough for auditory access, without necessarily asserting a particular hearing occurrence. Either label the hypothetical event as bare hearing, or represent the established capacity as asserted. Current annotations do not invent completed hearing, but the modal label and factuality could be clearer.

## Material checks passed

- Stable first/second/third picked fruit identities are distinct from the unreachable high pear and the partly golden resistant pear. Willa's gift is an unresolved role identity for the first or second fruit; it is not an extra pear, the third fruit, or the high fruit. Early recipient-goal mentions remain marked as intended/unspecified.
- The initial count plan and later count announcement are distinguished from allocation and delivery. Two pieces per each of two actual oatcakes does not assert that every produced piece was placed or that pieces were equal. Honey's ambiguous target remains unresolved. Eating does not imply total consumption before Bell's subsequent pear reference.
- Negative conditional antecedent p35 is separate from positive negation target p28. “She might” restores the positive wanting predicate instead of copying Jun's negative prediction. The crate-use rule, remembered Bell utterance, Tessa's/Jun's earlier picking references, bending branch, quivering buds, cut-away bruise and delivered gift reuse appropriate underlying events.
- Source facts and instructions remain scoped: no completed climbing, branch pulling, shaking or yanking is fabricated. Actual loan/return and proposed crate use are distinct. Tool fingers are not people; puppet/doll picnic context does not invent a staged fictional event.
- Body-part subjects, stem release, physical figurative shining, supported/attached fruit and the ring's earlier contact are preserved. “Untouched” at w625 is explicitly interpreted as left unpicked, avoiding contradiction with the prior ring contact.
- Bruise origin remains unknown, not assigned to the immediately previous drop or carry. No-leaf-damage is restricted to checked branches; the final unbent branch does not imply universal orchard integrity. Facial expressions do not become permanent traits or certain fine-grained emotions.

## Status

Both findings are resolved and the regenerated records were verified. W680 has `referent_kind=bound_variable` without the generic flag; w679 still restricts that variable to e11. Ev9 now labels bare hearing, keeps hypothetical factuality, and w8 separately records ability. The author's additional catalog audit also correctly replaced the legacy edibility alias at w590 with the existing `affordance_eating` field.

Accepted after semantic review and bounded verification: 822 words / 1,859 tokens, 67 entities, 160 events, 41 scopes, 36 propositions, 174 distinct fields, zero validation errors. The documented source ambiguities remain appropriate. Structural validation supports shape/link integrity rather than proving the semantic judgments.
