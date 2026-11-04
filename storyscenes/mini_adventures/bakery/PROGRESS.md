# Bakery Round 1

Reference complete: 963 words, written first from seed 757654805: village bakery,
borrowed lantern, keeping a surprise secret.

Inventory complete: twenty executable encounters, explicit consolidation note,
seven optional encounters, three outcomes. Six validated parameter dimensions.

Simulator complete: shared atomic transition API, bounded exact-length search,
local failed wick attempt preserved, explicit carrying/return and fuel accounting.
First assignment-seed draw read; it postpones supper because fuel runs out.
Tests complete: eleven focused tests passed, covering 200 seeded routes and 288
parameter-grid routes, plus targeted counterfactuals. All six first draws read
and saved without filtering. The report records sampling skew and fixed-backbone
limits. Round 1 ready for parent review; no shared-library changes requested.

## Round 2

Implemented the parent review's five requests. Reference and Round 1 samples
unchanged. Count clarification: 957 prose words; 963 including the title.

Reserved one actual fuel measure for Vale's cellar. Oil in the bottle, oil in
the reservoir, and cumulative burning are conserved after every atomic action.
The one-measure case does not light or load the oven; the two-measure case can
start but must stop rather than consume the cellar reserve. Optional refilling
can still change the outcome without being silently enacted on omitted routes.

Early furniture-van urgency now refuses extra time equally for confession and
secret extension requests. Temporary handoff does not settle the loan; an
explicit usable-wick/oil check does. Final prop placement is enacted. Cooling
no longer adds an unacknowledged delay before return.

Postponement leaves an unanswered salvage request and a conditional invitation
before personal departure tomorrow. It does not predict that the baker succeeds
or that breakfast happens. Six matched first draws and two labeled successful
parameter counterfactuals read locally. Sixteen tests pass, with the same 200
seeded and 288 grid routes plus targeted review regressions. New samples use
`round_02_*` names. See `ROUND2_REPORT.md`; no shared-library changes requested.

## Round 3

Shared helper complete: `mini_adventures/local_play.py` and nine focused tests.
Bakery's scenario-specific LocalPlay subclasses it; movement, custody, fuel,
and loan settlement remain local. Shared API matches the parent's contract.

Prose complete: successful endings retain all enacted checks but replace
"usable lantern" and "Now it's returned" with a small exchange about cellar
steps and bread. No action, parameter, selector, or outcome rules changed.

Tests complete: 27 focused tests passed (nine shared, eighteen bakery).
All 100 frozen Round 2 positions preserve parameters, paths, search attempts,
states and events exactly; only eleven successful stories' endings differ.
Read all ten new full samples (0, 1, 6, 42, 757654805 at both lengths), saved
separately as `round_03_samples.*`. Diagnostic outcome recipes documented and
tested in the new pack README. Frozen reference compared byte-for-byte equal.
No prior samples or greenhouse files edited. See `ROUND3_REPORT.md`.

## Round 4

Verification-only release pass complete. Shared helper and bakery source/tests/
inventory remain byte-identical to frozen Round 3. Stable API/adapter signatures,
four CLI-to-API comparisons, help/invalid-count behavior, and all three README
diagnostic recipes pass. Final focused suite: 27 tests pass in 7.391 seconds.

All 100 frozen Round 3 rows reproduce exactly in current and frozen-source fresh
interpreters, including prose and replayed episodes. All 24 preserved sample rows
reproduce from their original frozen rounds; Markdown matches their saved prose.
Reference bytes agree with all three frozen copies. Old artifacts were not edited.

No missing boundary found, so no new regression or generation changes. No held-out
1000-1049 seeds sampled; external snapshots and complete-suite gate remain the
parent's work. New `RELEASE_NOTES.md`, `ROUND4_REPORT.md`, and `release_checks.json`
record results and existing failure-skew/quality limits. No greenhouse/helper edits.

Final receipt notes an external concurrent shared-test-only change: two mock
targets made module-relative. Did not edit or revert it; verified the exact diff
and reran the 27-test suite successfully. Helper implementation remains unchanged.
