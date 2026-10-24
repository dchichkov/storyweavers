# Three-slice acceptance

2026-10-22. Parent closeout of the approved bounded physical, epistemic and
social implementation. This applies to the new opt-in
`storyscenes.capabilities.v1` path, not a migration of legacy worlds or approval
to produce training data. **The three-slice implementation is complete within
the approved bounded scope.** All non-deferred ledger requirements have evidence
below; the independent [site-grant follow-up](site_review.md) closes the last
specific review finding without claiming broader literary acceptance.

The [frozen ledger](acceptance_matrix.md) remains the requirement specification.
[DECISIONS](../DECISIONS.md) controls scope. Earlier
[acceptance_audit.md](acceptance_audit.md) and [final_review.md](final_review.md)
are preserved as historical findings, not overwritten with a clean review.

## Verification

From the repository root:

```bash
./.venv/bin/python -m unittest discover -s storyscenes -p 'test_*.py'
./.venv/bin/python -m unittest discover -s storyworlds -p 'test_*.py'
./.venv/bin/python -m storyscenes.capabilities.verify --out /tmp/capability-evidence-new
```

- StoryScenes: **369 passed**, including **231 capability tests**, the frozen
  independent H/G4's **16 tests**, and legacy regression coverage.
- StoryWorlds: **123 passed**. No paid generation or judge calls.
- **20 frozen legacy cases** compare old/current/public execution; old engines,
  owner/knowledge semantics and frozen batches were not changed.
- [Evidence v4](evidence_v4/summary.json): **50 narrative cases, 10 atomic
  rejection cases, 668 enacted events, 552 retained events, 934 QA rows and
  1,845 necessary-support masks**. Every masked answer abstains. The deliberately
  accepted-but-uncollected prefix does not claim its eventual return goal.
- V4's **139 manifest-listed files** plus its manifest are saved, including
  the executable runtime. All 60 saved paths replay exactly in a separate
  process using only that frozen runtime. All 50 retained traces, prose and QA
  replay exactly; all 10 rejected operations preserve their state fingerprint.
- V1-V4 remain separate directories. All historical manifest bytes/hashes pass.
  V3's own frozen runtime reproduces 53 paths and 45 retained prose/QA records.
  V1/V2 predate runtime freezing: their hashes were checked, but replay under
  today's changed schema is not claimed.

The evidence writer refuses overwrite and checks for runtime-source changes
during a batch. `test_capability_verify.py` checks hashes, masks, isolated frozen
replay and overwrite refusal. `git diff --check` also passes.

## Requirement map

All entries refer to executable tests under `storyscenes/`. `test_` is part of
each actual method name. The table covers bounded assertions, not a proof of
arbitrary Python extensions or unrestricted English entailment. Artifact names
refer to `evidence_v4/<name>.json`; each also has its typed `.world.json`.

| Gate | Evidence and disposition |
| --- | --- |
| X1 | **Pass.** `test_capability_core` explicit version/strict JSON; `test_capability_boundaries` missing schema and operation-argument shape; `test_capability_legacy` frozen/public/current paths. One registry/codec and explicit renderer/Reader; no title dispatch or silent legacy conversion. |
| X2 | **Pass.** Core one-writer, declared-contract and atomic-postcondition tests; boundary immutable payload/action/snapshot tests; `test_capability_initial_provenance` rejects fabricated histories. V4 blocked fingerprints and frozen replays. |
| X3 | **Pass.** Epistemic `test_hidden_truth_variations_offer_identical_belief_based_intents`, boundary access-recheck and H hidden-safety tests. `proposals` uses accessible intent; author-side search is not misrepresented as an autonomous character policy. |
| X4 | **Pass.** Core atomic rejection/bounded event-only repetition; social enacted booking-check versus rejected candidate; H no-reply/no-repeat cases. Breach, refusal, deferred belief and unfinished booking are retained outcomes. |
| X5 | **Pass.** Physical path/authority selection; choices `test_replay_pruning_retains_choice_evidence_promises_and_refusal_not_every_event`; H unused-attention pruning; 50 saved retained replays. 116 enacted events prune in the saved corpus. |
| X6 | **Pass for controlled realization.** Reading, custody, historical-reading, returns, corrections, choices and H tests exercise exact visible support, focused event/time follow-ups, ambiguity abstention and positive unmasked controls. V4 preserves 1,845 masks. See semantic reading limits below. |
| X7 | **Pass for reviewed semantic conformance, not literary acceptance.** Production prose/QA readings below and independent historical/H/site reviews; state-driven changes, failures and ending evidence inspected separately from compression or scores. |
| P1 | **Pass.** Physical bench/cabinet/closed-contents tests; custody-reader bench/path tests; `library_return` and `harbor_closed_case`. Holder, owner, borrower and effective location are distinct. |
| P2 | **Pass.** Physical remote/wrong-source/closed/other-holder pickup, cycle, route, load and occupied-hand tests. Site tests use actual travel, not names, to change grant legality without preventing physical motion. |
| P3 | **Pass.** Physical consent/comprehension/readiness distinction, exact readiness tuple and immutable receipt tests; `library_two_return_offers` executes one separately accepted return. |
| P4 | **Pass.** Physical collection-window, one-active-loan, current lend/release grant and version tests; `observatory_accepted_uncollected`, `library_claim_only_return`; site-grant offer and activation rechecks. |
| P5 | **Pass within immediate-return scope.** Physical wrong/old loan, generic put, revoked authority, missing latch and atomic deposit tests; receive-only A2 remains active while A1 stays settled. No delayed-settlement policy is claimed. |
| P6 | **Pass.** Physical post-consent custody/capacity/access rechecks, site post-consent travel and return probes, and production custody/loan QA masks. Failed joint effects leave readiness and debt unchanged. |
| E1 | **Pass.** Epistemic event-time attention/path checks; complete exact false/zero versus unknown/partial tests; H visible external indicator versus uninspected internal seal. |
| E2 | **Pass.** Epistemic actual/attributed source lineage, delayed report, delivery/comprehension versus adoption and inaccessible-channel tests; `harbor_dated_report` and stale-authority stories. |
| E3 | **Pass.** One belief writer, explicit init/adopt/resolve/defer/reject, predecessor retention and no latest-writer/truth-copy tests; initial-history rejection. Failed or absent evidence cannot silently replace a prior belief. |
| E4 | **Pass.** Five historical-reader tests distinguish an accurate old report, evidenced later change, changed-reference disagreement and unresolved present applicability. Dated report/closed case/no second view/changed reference artifacts preserve the paired outcomes. |
| E5 | **Pass.** Epistemic repeated warning/reinspection/one-source and duplicate-adoption tests; H source-lineage and finite repetition tests. Acquisition time is not source independence. |
| E6 | **Pass.** All 20 correction tests: valid old/current Observatory slots; Pavel's explicit freshness deferral and age boundaries; Ivo's retained occluded diagnosis; Library current authority; Observatory declared source-identity rule. Baselines and negative controls are saved. |
| E7 | **Pass.** Epistemic evidence-order and unknown-prior tests plus correction reading-order tests. Revision changes belief, not physical repair; production answers cite the actual evidence/time. |
| S1 | **Pass.** Social request lifecycle stale/proxy/duplicate/undelivered checks; physical typed refusal adapters; production two-return-offer tests and H exact certification request. |
| S2 | **Pass.** Social acceptance/acknowledgment/performance and post-acceptance receipt tests; Library delayed assent, separate room booking and occupied check. Rejected booking is not a narrated attempt. |
| S3 | **Pass.** Request withdrawal and independent-action tests; all three `test_capability_return_request` tests. `harbor_separate_return_request` preserves the outbound acceptance/promise and separately accepts/completes the return. |
| S4 | **Pass.** Social exact operation/actor/object/result/recipient/terms/version and post-creation ordering tests; real completion claim and exact inspection receipt tests; chart substitution cannot satisfy live-detector terms. |
| S5 | **Pass.** Social strict/inclusive boundary and same-tick ordering tests; `observatory_strict_boundary` versus `observatory_inclusive_boundary`. Assessment requires a closed simulated interval, not missing prose. |
| S6 | **Pass.** Authorized release, linked new terms and late-repair tests. `observatory_released_replaced` leaves the original live-detector undertaking released and fulfills only the new chart undertaking; late repair preserves breach. |
| S7 | **Pass.** All 13 choice tests: both handoffs executable from one pre-state; chosen custody blocks the other; reversed priority changes breach; post-breach refusal/reason masks; ability/authority do not force assent. |
| T1 | **Pass.** Shared operations plus distinct Library ledger/booking, Harbor site/capacity/freshness/diagnostic/return-request, and Observatory recording/source identity/live-substitute structures. Name-stripping and reason-change controls are tested; three renamed loan demos alone are not credited as diversity. |
| T2 | **Pass.** G1 integrated loan/refused-return/latched deposit plus grant/wrong-loan/claim controls; G2 hidden movement/delayed report plus reference-time/visibility/no-second-view controls; G3 competing choice with action-only/promise-only/refusal/replacement controls. Each has replay and production QA. |

## Named falsifiers

| Falsifier | Concrete proof, including paired outcomes |
| --- | --- |
| P-F1 | Returns `test_p_f1_historical_a1_and_current_a2_receive_only_then_later_authority`: A1 and its receipt unchanged, exactly one A2 handoff, later grant creates no extra movement or discharge. `library_receive_only_new_loan`. Positive delayed settlement remains expressly deferred. |
| P-F2 | Physical bench/cabinet tests and custody QA: passive source/bench paths, no fabricated actor holder, continuing borrower and debt. `library_return`. |
| P-F3 | Physical capacity/readiness and revoked lending tests; returns dry-bench capacity intervention; sites activation/return after travel. `harbor_full_hands`, revoked-grant and out-of-place blocked cases preserve all pre-state effects. |
| P-F4 | Real claim-only return and both stale-authority speech/delivery/comprehension/adoption branches; returns positive authority-restored controls; closed-container movement tests. Accepted belief is neither authority nor performance. |
| P-F5 | Physical latched deposit/dependency selection and missing-latch atomic rejection, plus legacy pins. `library_return` versus `observatory_missing_latch`. |
| E-F1 | Epistemic both evidence orders and unknown-prior tests assert histories/predecessors and exactly one explicit resolution/init, not merely the endpoint. |
| E-F2 | Historical reader's positive accuracy control and per-support masks; corrected ledger's authority/current-seal negatives; changed-reference and no-second-view artifacts. No always-abstaining query is counted as a positive control. |
| E-F3 | Epistemic partial/failed versus complete exact-negative tests; correction occluded/visible diagnostic pair; H internal-safety unknown. No automatic opposite belief or physical repair. |
| E-F4 | Epistemic requested/promised inspection of a closed container versus actual accessible inspection; social exact/partial inspection matching and H accessible branch. Promise and movement do not inspect contents. |
| E-F5 | Epistemic repeated warning/reinspection with distinct times but one source; H repetition/removal/reason/target masks and selected replay. |
| S-F1 | Social accepted-request withdrawal and independent movement; separate-return-request baseline/outbound/blocked-route controls. Initial decline after acceptance and duplicate response reject. |
| S-F2 | Social exact checkpoint, release, late repair and false-performance tests; boundary/released/late-repair saved artifacts. Breach history and closed-interval order persist. |
| S-F3 | Returns production exact first/second offer IDs, decline/reason/acceptance/settlement masks and replay. `library_two_return_offers` and `harbor_two_return_offers`; one receipt settles only the accepted second offer. |

H/G4 remains exclusively in `test_capability_holdout.py`, not `verify.cases()` or
implementation demos. Its independently frozen 16 tests and
[review](holdout_review.md) cover partial external inspection, unknown internal
safety, two same-source warnings, the exact delivered certification request and
one decline, unchanged physics, pending-without-reply, repetition removal,
exact-access branch, reason/target masks and focused follow-ups.

## Semantic reading

The parent read saved V4 stories and QA for Library return, no-second-observation,
changed-reference report, occupied booking, Observatory release/replacement,
receive-only A1/A2 and stale lending authority. Earlier independent reviews read
all five corrections, historical report contrasts, returns and H. The site-grant
review covers the final restricted/unrestricted variants separately.

- Library return: placing the bag on the courtyard leaves no physical holder,
  but does not transfer ownership or erase the debt. Only the authorized latched
  deposit closes the loan; the ending describes that physical result.
- Missing second view: a time-zero report remains accurate for that time, but
  gives no current location. Changed reference to time two is disproved only
  by a matching-time direct inspection, never labeled an intentional lie.
- Booking: the projector reservation correction does not book the separate room.
  The enacted occupied-room check leaves an accepted request unfinished.
- Substitute: a chart does not quietly satisfy a live-detector promise. Release
  is visible and the separately stated chart undertaking has its own fulfillment.
- Two checkouts: the first settlement and second receive-only handoff are
  distinguished in text/QA. Later authority is not retroactive discharge.
- Stale authority: a real old notice/report can support a dated belief while the
  grant is revoked. Rejected collection is not rendered as an enacted failure.

The text remains diagnostic: repeated names/state summaries, administrative
dialogue, numeric checkpoint wording, mechanical boolean predicates and
single-fact answers. Some freely authored premises/endings summarize the intended
scenario and have no QA support; the renderer does not verify arbitrary flourishes.
Reader safety is proven only for its declared controlled statements and masks,
not by a general English entailment model. Some event qualifiers are deliberately
technical to distinguish identical questions at different events.

V4's 74,978 story bytes compress to 6,364 LZMA bytes; 50/50 exact uniqueness is
just a small conformance-corpus diagnostic. It is **not** a 1,000-sample diversity
score, quality score, or an estimate of usable training yield.

## Scope and next gate

No runtime LLM or paid evaluation was used. The engine embeds evidence and
actions in physical actors/carriers and validates state-compatible moves, toward
`story.py`'s memeplex north star. It does not claim the entire north star is solved.

Still deliberately deferred: delayed settlement policy, recursive delegation,
subloans, joint transport/vehicles, general contracts or amendments, responder
abandonment, probabilistic trust/diagnosis, and unlimited repeated speech.
All remain explicit exclusions, not silently passing implementations.

The next development gate is literary realization and authoring usability on this
state model, followed by a separately authorized sampled quality/diversity trial.
Do not tune away unresolved or breached outcomes, relax support masks, or feed
these diagnostic demonstrations straight into training because tests are green.
