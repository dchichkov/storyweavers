# Existing behavior and design boundaries

Read-only architecture audit by the coordinator, 2026-10-21. The proposal round
does not change these implementations. Links point to source, not proposed APIs.

## Mechanics

| Existing behavior | Evidence | Consequence for the proposal |
| --- | --- | --- |
| State is a map of scalar values; every key is embedded in a named entity. | `runtime.py`: `validate_spec`; `algebra.py`: `scalar`, `build` | Typed propositions, loan records, and requests need an explicit new representation/compiler. They do not already exist just because a proposal names them. |
| A scene contains guards, atomic set/inc/copy effects, actors, usage bounds and a label. | `runtime.py`: `Scene`, `transition` | Reuse the atomic-transition principle, but do not treat an arbitrary label as a verified domain operation. |
| A transition returns `None` for a failed guard, invariant violation, or unchanged state. | `runtime.py`: `transition` | Distinguish planner-rejected candidates from attempted failures and meaningful events with unchanged physical state. Do not invent irrelevant flags solely to bypass this behavior. |
| `Observe` copies a physical fact; perceptual eligibility is supplied by the author. | `runtime.py`: `observe` | Access, attention, occlusion, and the difference between evidence and belief require explicit contracts. |
| `Tell` copies a speaker's stored belief into the listener's slot. | `runtime.py`: `tell`; `test_algebra.py`: stale-belief test | Preserve legacy semantics. A new communication model must separate claim, receipt, comprehension, acceptance and world truth. |
| `Transfer` changes one `.owner` slot after checking the giver. | `runtime.py`: `transfer` | Historical `.owner` mixes meanings. A new legal-owner/custodian distinction cannot be silently inferred for old datasets. |
| `Lend` and `Return` reuse transfer plus `.loaned_by`; Return checks the designated lender. | `algebra.py`: `compose` | Multiple loans, delegated receipt, and ownership-preserving custody changes require a new explicit contract. |
| `Move(actor, prop, destination)` changes only `prop.location`, requiring `prop.owner == actor`. | `algebra.py`: `compose` | Do not retrofit carrier travel into frozen Move. New carrying must coordinate custody and effective location. |
| Role-bound immutable kernels compose through state keys and namespaces. | `algebra.py`: `Kernel.bind`, `Pattern`, `compose` | This is a useful extension point. A capability must be reusable across all three settings, not an English-title-specific scene. |

## Planning, motives, and evidence

- `runtime.solve` is bounded goal-directed author-side search. It does not imply
  that characters know the goal or the complete world. Legality and choice must
  distinguish world facts from each character's available information.
- `causes` are built from last writers of guard/copy/increment dependencies.
  They are useful provenance, not a sufficient representation of a motive,
  intention, social justification, or a philosophical cause.
- `planning.prune_path` preserves goal/outcome dependencies and pivotal scenes,
  then replays. New request/refusal/dialogue evidence must not disappear merely
  because a physical endpoint remains reachable without it. Any future change
  must retain the existing replay guarantee.
- A rejected candidate is not a failed attempt that the story may narrate. An
  attempt, its observed result, and a subsequent explanation need actual events.
- New designs should record a meaningful event without requiring that the world
  become physically different. Finite usage/step bounds must still prevent loops.

## Prose and QA

- `prose.render_book` selects conditional cards and fills known names/phrases.
  It records tested/bound facts, but does not verify every free-English claim.
- `dialogue.py` supports attributed utterances, reply references and claims;
  these remain evidence annotations, not a complete speech-act state machine.
- `conversation.Conversation._build_starters` infers question types from existing
  event labels/fields and also creates state questions. It is not a universal
  interpreter for hypothetical new capability records.
- `Conversation.causal_answer` explicitly explains enabling prerequisites.
  Proposed motive answers require additional evidence, not repackaged guards.
- Reader-grounded QA must depend on what the selected narrative establishes.
  Hidden true state can support simulator debugging, not silently become a
  reading-comprehension answer. Unsupported answers must abstain.
- A paragraph's evidence annotations must not be treated as proof that its free
  text states those facts. Future validation needs both structure checks and
  semantic/manual review; a model judge is fallible too.

## Compatibility boundary

Recommended future work is opt-in and versioned. Preserve legacy builders,
fixtures, exports, recorded traces and interpretation. Do not migrate `.owner`
to legal ownership automatically. New records need their own schema/version and
an explicit adapter when they enter rendering/QA. Existing scalar-only rules
remain a constraint to address, not an invitation to hide JSON inside strings.

Only a small initial vocabulary is needed: entity/location, possession and
ownership, proposition/belief/evidence, request/action specification, and a
commitment/loan identifier. Exact fields and interfaces await worker proposals.
Capability expansion should be driven by concrete story/test needs, not by
building a general ontology in advance.

## Preservation evidence

The coordinator captured SHA-256 values for 11 mechanics, rendering, QA and test
files at the start of the design round. The final artifact check will compare
them and record any changes without reverting work by others. No runtime tests
are claimed merely because the proposals contain proposed acceptance tests.
