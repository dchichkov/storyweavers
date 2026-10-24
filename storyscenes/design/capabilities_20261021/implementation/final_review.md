# Bounded Final Review

2026-10-22. Independent follow-up to `acceptance_audit.md`'s four Next
Blockers only. This report owns no implementation or final acceptance decision.

## Prioritized Finding

**P2 - T1/X7's restricted dry-bench binding is still missing.**
`capabilities/returns.py:31-47,159-177` binds grants to a loan/terms ID and an
actor destination, not a place. The Harbor test genuinely proves current hand
capacity and exact A1 grant revocation versus an available A2 grant; it does
not prove the approved restricted-location contrast. A direct in-memory probe
extended `two_offer_story(harbor=True)` with a launch place, an open route,
and legal travel by borrower and receiver after acceptance/readiness. Unchanged
`finish2` then discharged A1 aboard the launch; `settle1.destination` remained
`receiver`. This is a missing setting binding, not a regression in the documented
recipient-scoped settlement operation. It cannot close the dry-bench-only versus
unrestricted grant intervention in `proposals/lending.md:60-83`. That contrast
still needs executable finite premises/guards and production QA, rather than
credit from a place name. No other correctness regression was found in the
reviewed paths; this is not a whole-repository clean bill.

## Original Blockers Rechecked

- **#1, E6/D06: closed for the five named bounded corrections.** Inspected
  `corrections.py`, freshness support/validation, and correction assertions.
  Observatory six/eight uses separate heads without rewriting six; Pavel's
  no-fresh branch preserves dated beliefs and defers under an explicit age rule;
  the occluded diagnostic preserves its prior without repair; ledger projection
  requires declared authority/current seal; exposure identity requires the named
  registry/source rule. Freshness boundaries 1/2 versus 3/15, hidden-truth
  invariance, authority/source negatives, reader-basis masks and retained replay
  are tested. Library delayed acceptance, actual booking and occupied-check
  branches are also distinct. This closes that audit gap, not every T1 binding.
- **#2, E-F2/X6: closed for the requested historical reader contrast.** All five
  historical tests passed. The unmasked time-zero report now answers positively;
  each support mask abstains. Changed-reference time-two disagreement requires
  the matching fresh observation, while omitted-second-observation retains the
  belief without asserting later change/current location. Answer roots retain
  the exact comparison evidence. This is no longer an always-abstaining test.
- **#3, joint falsifiers: the named gaps are closed.** P-F1 executes historical
  A1 settlement and A2 receive-only in one trace; A1/receipt stay unchanged and
  later authority creates no settlement. P-F4 uses real speech, delivery,
  comprehension and adoption of stale authority for both lending and returning,
  with successful controls and atomic rejection. S-F3 uses production rendering,
  exact first/second offer responses, refusal reasons, settlement dependencies,
  masks and replay. All eight return tests passed, including the three renderer
  regressions. `offer_return` records its sequence using a causal table read;
  a second-settlement-only replay root also retained the first offer in a probe.
- **#4, T1/X7: partially closed, not certified.** Library ledger/booking conflict,
  Harbor freshness/occlusion and capacity/grant checks, and Observatory dated
  reading/source identity now have real distinct structures. The finding above
  remains. Observatory live-substitute coverage was not independently reviewed
  here; neither its closure nor its absence is asserted.

## Verification And Limits

Ran `env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest
storyscenes.test_capability_historical_reading
storyscenes.test_capability_corrections storyscenes.test_capability_returns -q`:
**33 passed**. Ran boundary discovery with `-s storyscenes -p
test_capability_boundaries.py -q`: **10 passed**, including operation-signature
argument rejection through Python/JSON. An initial package-style boundary
invocation failed because that module imports `capabilities`; discovery was the
successful supported invocation, not an implementation failure.

Actually read production stories and selected QA together for historical
baseline/changed-reference/no-second-view; D06 ledger/freshness (including a
fresh-enough policy-supported belief); the other three correction baselines;
Library occupied booking; two offers and receive-only A1/A2. Exact-event return
queries distinguish the old settlement from current outstanding debt; unqualified
multi-event queries abstain by the Reader's deliberate ambiguity rule.

No implementation edits, paid calls, broad JSON audit, or full-suite rerun.
The workspace was changing during review; this is not a frozen snapshot. Parent
owns the full-suite run, evidence-v3 freeze and final audit. V3 hashes/replay,
all saved prose/QA, unrelated paths and later edits remain unreviewed. Delayed
settlement and other previously deferred policies remain deferred. No goal or
overall acceptance closure is claimed.
