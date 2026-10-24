# Capability implementation

The user approved slices 1-3 on 2026-10-22. Historical design documents remain
unchanged; their earlier authorization status describes the design checkpoint.

## Scope

1. Physical continuity, scoped consent, loans and immediate authorized return.
2. Accessible evidence, communication and explicit belief revision.
3. Typed requests/refusals, promises, finite deadlines, release and late repair.

All three remain required. The reconciled DECISIONS.md and INTEGRATION_GATES.md
are acceptance requirements, not assumed completed features. Deliberately
deferred policies stay deferred as specified there. No paid API evaluation is
authorized by this implementation goal.

## Completed scope

- Implemented: shared opt-in schema, typed codec, atomic transactions, bounded
  immutable events, deterministic replay and dependency-preserving selection.
- Implemented: physical/loan, evidence/revision and request/promise operations.
  Initial worlds reject fabricated event history; authored wrong beliefs and
  static configuration remain valid premises.
- Implemented: G1 custody/refused-return/authorized-deposit, G2 hidden movement
  and historical reports, and G3 genuine competing promises, including explicit
  action-only, promise-only, opposite-priority and release/replacement branches.
- Verified independently: frozen H/G4 and its masking/repetition interventions,
  16 unchanged tests. Original failing findings remain in `holdout_review.md`.
- Verified: 20 frozen legacy cases via old/current/public paths; no legacy engine
  files changed. Final StoryScenes discovery passes 369 tests, including 231
  capability tests; StoryWorld regression discovery passes 123 tests.
- Completed: requirement-by-requirement [acceptance record](ACCEPTANCE.md),
  full/retained frozen replay evidence, semantic prose/QA readings and independent
  review follow-up. All three approved slices are implemented. This is bounded
  semantic conformance, not literary acceptance or training-data readiness.

## Audit fixes

- Closed initial-history laundering in physical, epistemic and social inputs.
- Preserved exact certification targets, refusal targets and historical times
  in prose/QA. Inaccessible inspection is narrated as an attempt, not completion.
- Added visible, event-time location/holder/owner/borrower/loan-status support.
  Masking placement/path support suppresses the corresponding answers; closed
  container movement does not disclose its contents.
- Removed the invented prediction from the no-prior-belief example's opening.
- Seed 42 exposed an old observation occurring after movement. The G2 fixture
  now explicitly orders its initial observation/report before the hidden move,
  with the absent observer following only afterward. Seeds 0/1/42 are pinned.
- Added all five D06 corrections, including explicit freshness-policy deferral;
  historical report comparisons now have positive controls before masking.
- Executed real stale-authority claims, receive-only A2 after settled A1, and
  separately identified first/second return offers with production QA support.
- Distinct bindings cover Library ledger/room booking, Harbor capacity/site
  grants/diagnostic/return requests, and Observatory time/source/substitution.
  The final reviewer found that Harbor authority traveled with the recipient;
  optional `Grant.place` now constrains both grantee and object, rechecked at
  offer and performance. Restricted/unrestricted travel controls and the
  independent [site review](site_review.md) verify the fix.

`evidence_v1/` through `evidence_v4/` are preserved separately. V4 contains
50 narrative cases, 10 atomic rejection cases, 934 QA rows and 1,845 support
masks, plus a frozen executable runtime and SHA-256 manifest. Its 60 full paths
and 50 retained prose/QA replays reproduce exactly from that runtime. All older
batch hashes also pass; V3 replays against its own frozen runtime. V1/V2 predate
runtime freezing and are historical records, not current-schema replay promises.
The writer refuses to overwrite any batch. No paid calls were made.

Next work is literary realization and authoring usability, then a separately
authorized sampled quality/diversity trial. Diagnostic prose, exact uniqueness
and tiny-corpus compression are not training-data acceptance. Previously deferred
policies, including delayed settlement, remain deferred; see ACCEPTANCE.md.

New work lives under `storyscenes/capabilities/`; legacy `runtime.py`, `algebra.py`
and frozen runs retain their meanings. The new physical carrier, evidence and
obligation records move toward story.py's north star: embedded state drives
compatible action and narration, with no runtime LLM calls.
