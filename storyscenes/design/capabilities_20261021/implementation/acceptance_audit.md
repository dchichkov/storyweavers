# Independent Acceptance Audit

2026-10-22. Scope: all three approved capability slices. Authority is the frozen
[acceptance matrix](acceptance_matrix.md), [DECISIONS](../DECISIONS.md), and
[INTEGRATION_GATES](../INTEGRATION_GATES.md). Only this new report is auditor-owned;
implementation, original ledger, and evidence bundles were not edited.

**Disposition: partial acceptance, not goal closure.** The implemented bounded
domain semantics have substantial direct proof. They do not yet establish every
approved setting-specific narrative and reader contrast. No requirements are
removed by this report, and deliberately deferred policies remain deferred.

## Next Blockers

1. **E6 / D06: inspect and execute Mill's five correction fixtures when ready.**
   This work is in flight and unreviewed here, not credited as passed. In the
   audited code, generic tests cover dated/current belief slots, failed-check
   retention, narrow inscription authority, and common underlying sources.
   They do not themselves prove all five corrected stories. The most substantive
   missing behavior is the Harbor no-fresh-report contrast: retain Pavel's dated
   belief while an explicit freshness rule defers current clearance. A new
   observation, automatic uncertainty, or a generic delayed-report example is
   not an equivalent substitute. Verify the other four named corrections under
   their actual authority/source/time premises, without physical repair being
   inferred from revision. Do not duplicate Mill's work or introduce general trust.
2. **E-F2 / X6: make the historical-accuracy mask test non-vacuous.**
   `CapabilityIntegrationTests.test_g2_old_report_remains_historical_after_movement_and_revision`
   asserts that masked `historical_truth/report` abstains, but a direct auditor
   probe found that the same unmasked query already abstains. No production
   statement of that kind is generated. Establish a supported historical-accuracy
   baseline from the rendered original observation/report, then remove its
   necessary support and require abstention. Keep false-at-reference-time,
   evidenced later change, and unresolved present applicability distinct.
   This is a bounded reader contrast, not a request for a general inference engine.
3. **Finish the few joint falsifier contrasts whose evidence is still thinner
   than their domain implementation.** P-F4 has real adopted delivery-claim proof
   now, but its outdated-authority-claim variant still lacks equivalent real
   speech/adoption evidence; the physical claim test uses a custom no-write stub.
   S-F3's separately accepted/performed second return has real simulation tests,
   but its reader check uses a handwritten `Statement`; exercise that exact
   two-offer branch through production `render`/`Reader` and masks. G2 also needs
   the explicit omitted-second-observation and changed-reference-time contrasts,
   not just closed-container and unknown-prior substitutes. These can extend
   existing shared fixtures; no new capability family is needed.
4. **T1 / X7: complete the approved distinct setting bindings, then capture v3.**
   The three `loan_story` specs are identical after stripping entity names/title.
   `choices.py` now proves genuine choice sensitivity, and the new Harbor D08
   fixture adds a different request/route structure. That is real progress, but
   not yet the complete Library booking/ledger, Harbor capacity/restricted-grant/
   freshness/occluded-diagnostic, and Observatory dated-recording/source-identity/
   live-substitute contrasts in the frozen fixture table. Reuse current operations
   and parameterize those remaining causal structures; do not build 27 programs.
   After the in-flight corrections and parent patches settle, capture current
   full/retained prose, QA, and paired interventions in v3 and read them together.
   A snapshot refresh alone cannot close the behavioral gaps above.

## Evidence And Verification

- Observed full command: `env PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s storyscenes -q`:
  **326 tests passed** before the latest three Harbor return-request tests were
  added. This count is a run result, not a full acceptance claim. Focused and full
  follow-up runs were launched for the latest additions; see the final run note.
- Inspected named assertions, current domain/reader code, generated stories and
  answers; ran local replay/reader probes. No paid calls or model judging.
- `evidence_v1`: manifest bytes/hashes verified; all 11 saved paths reproduce
  their exact saved traces. Historical evidence only: its prose predates custody
  QA and wrongly gives the no-prior variant an expectation in its opening.
- `evidence_v2`: manifest bytes/hashes verified; all **22** saved paths reproduce
  exact traces, including three blocked prefixes; all **19** stored retained
  traces reproduce. It contains 19 narrative cases, three atomic rejection cases,
  support spans, full/retained QA, and dependency-mask results. Inspected
  `EvidenceWriterTests.test_manifest_masks_replays_and_rejected_interventions` and
  the writer's per-dependency mask loop. This tests declared support, not arbitrary
  English entailment. V2 predates the latest exact-task promise wording and D08
  addition; current rendering differs. Do not overwrite either historical bundle.
- Separately ran legacy `test_algebra`: 15 passed, including stale-belief Tell
  and wrong-lender Return. Legacy capability pins cover frozen/current subprocess
  replays and public dispatch, not a migration to new ownership semantics.

### Current Patches Credited

Initial-provenance validators were inspected, not merely reported complete:
`InitialProvenanceTests.test_forged_inspection_claim_receipt_comprehension_and_revision_are_rejected`,
`test_pending_delivered_accepted_declined_and_completed_requests_are_not_initial`,
`test_promises_refusals_and_domain_receipts_are_not_static_configuration`, and
`test_legitimate_operations_full_replay_and_selected_replay_remain_valid` passed.
The earlier incompatible fabricated-receipt fixture was corrected to expect
initial rejection; the initial full-run error is not a current blocker.

`CapabilityChoiceTests` now supplies genuine G3: both handoffs execute from the
same pre-state; consuming the one resource blocks the other; priority reversal
changes which promise breaches; action-only, promise-only, refusal-after-breach,
late repair and release/new-terms histories remain distinct. Selected replay,
motive masks and focused follow-ups were inspected and passed. Its earlier
full-versus-retained document comparison was corrected to compare selected full
output against retained replay, as required, not to demand unused prose survive.

Parent custody/claimed-return patches were inspected and passed. Bench QA really
says the atlas is in the bag at the courtyard, no one physically holds it, Inez
owns it, Nia remains responsible, and L is outstanding; path masks abstain.
The real adopted return claim leaves L active, the grant inactive, and no deposit
receipt. The G2 search guards and seed 0/1/42 regression were inspected: the old
observation/report precede hidden movement and the later view retains time 2.

The promise ambiguity found during this audit is **resolved in current code**:
`test_promise_outcome_prose_and_qa_identify_the_exact_task` and direct output now
name delivery to Bea versus Cleo in both questions and outcomes. The Harbor
`separate_return_request_story` and all three `SeparateReturnRequestTests` were
read: outbound acceptance/promise survive withdrawal; the separately accepted
return completes through `bring_back:1`; independent outbound performance may
fulfill the promise but cannot complete the withdrawn request. Do not demand
these fixes again. Their latest run results are recorded below.

## Compact Requirement Map

`proved` means direct bounded semantic assertions were inspected and executed,
not universal correctness or full three-setting narrative acceptance. `partial`
means some required contrast/evidence remains open; `missing` identifies a
specific unproved subcase. A proved domain row does not override partial X6/X7/T1.

Test prefixes below identify actual classes under `storyscenes/`:
`C` = `test_capability_core.CapabilityCoreTests`; `B` =
`test_capability_boundaries.CapabilityBoundaryTests`; `P` =
`test_capability_physical.PhysicalTests`; `E` =
`test_capability_epistemic.EpistemicTests`; `RQ` / `PR` / `SB` / `SP` / `SE` =
`test_capability_social.RequestTests` / `PromiseTests` / `BoundedEventTests` /
`PhysicalIntegrationTests` / `EpistemicPerformanceTests`; `I` =
`test_capability_integration.CapabilityIntegrationTests`; `CH` =
`test_capability_choices.CapabilityChoiceTests`; `CU` =
`test_capability_custody_reading.CapabilityCustodyReadingTests`; `CR` =
`test_capability_claimed_return.ClaimedReturnTests`; `RR` =
`test_capability_return_request.SeparateReturnRequestTests`; `IP` =
`test_capability_initial_provenance.InitialProvenanceTests`; `L` =
`test_capability_legacy.CapabilityLegacyReplayTests`. Every method below has its
literal `test_` prefix. Artifact names refer to `evidence_v2/<name>.json` unless
otherwise stated. Live-only tests have no claim of a saved v2 narrative.

| Gate | Status | Named tests and current evidence; limit |
| --- | --- | --- |
| X1 | proved | `C.test_explicit_version_boundary`, `B.test_json_requires_an_explicit_schema_field`, `L.test_public_cli_preserves_frozen_dispatch`, `L.test_frozen_replays_match_pins_across_hash_seeds`; `legacy_baseline.json`, typed codec and explicit render/Reader adapters. Legacy builders also exercised by `test_algebra`. |
| X2 | proved | `C.test_one_writer_and_no_hidden_mutation`, `test_declared_read_write_contracts`, `test_atomic_postcondition`; B's immutable payload/snapshot tests; IP tests above. V2 full/retained traces and three unchanged blocked-deposit fingerprints. |
| X3 | proved | `E.test_hidden_truth_variations_offer_identical_belief_based_intents`, `B.test_intent_access_is_rechecked_after_access_changes`, H hidden-safety contrast. This certifies intentional-query separation, not a new autonomous character planner; `solve` remains author-side search. |
| X4 | proved | `C.test_rejection_is_not_attempt_and_is_atomic`, `SB.test_rejected_booking_is_not_attempt_but_real_check_is_evidence`, H rejected candidate/repetition tests; blocked v2 cases and promise-only unresolved/breached history, not success-only selection. |
| X5 | proved | `P.test_path_and_authority_dependencies_survive_selection`, `CH.test_replay_pruning_retains_choice_evidence_promises_and_refusal_not_every_event`, H selected replay; v2's 19 exact retained replays. Actual acknowledgments/unused attention prune; evidence and authored reasons survive. |
| X6 | partial | CU path masks, `I.test_real_renderer_masking_removes_refusal_reason_and_reply_target`, CH motive/follow-up tests, H manual review and v2 masks. Missing non-vacuous historical-accuracy control and production two-return-offer reader contrast. No blanket English-entailment or reader-horizon certification. |
| X7 | partial | V1/v2 stories and QA read together; live G3/H outputs manually inspected. Distinct integrated structures and post-patch v3 review remain; uniqueness/compression figures are not semantic or literary pass scores. |
| P1 | proved | `P.test_p_f2_bench_placement_removes_holder_not_debt`, `test_p_f2_cabinet_collection_no_imaginary_holder`, `test_closed_contents_move_without_exposure`; CU bench QA; `library_return`, `harbor_closed_case`. Owner/borrower/holder/path stay distinct. |
| P2 | proved | `P.test_pickup_wrong_source_remote_closed_and_other_holder`, `test_route_closed_and_occupied_hands`, `test_cycles_actor_parent_and_recursive_load_invariants`, `test_finite_routes_mass_and_exact_travel_receipt`. Domain fixtures cover physics; not all are integrated setting narratives. |
| P3 | proved | `P.test_readiness_bound_to_giver_object_recipient_operation`, `test_committed_receipts_are_immutable`, `test_consent_comprehension_and_readiness_are_distinct`, `test_g1_decline_then_new_offer_immediate_settlement`; receipt changes in `library_return`. |
| P4 | proved | `P.test_collection_window_start_inclusive_end_exclusive_no_debt`, `test_one_active_loan_per_object_not_per_agreement`, `test_p_f3_current_lending_and_release_grants_rechecked`; `observatory_accepted_uncollected` and real `library_claim_only_return`. |
| P5 | proved | `P.test_old_loan_receipt_and_offer_cannot_settle_new_checkout`, `test_generic_put_never_settles_or_latches`, `test_current_return_authority_rechecked`, `test_p_f5_missing_latch_rejects_all_effects`; `library_return` versus all three blocked v2 deposits. Delayed settlement is not credited. |
| P6 | proved | `P.test_current_custody_source_and_access_rechecked_after_consent`, `test_p_f3_readiness_does_not_reserve_recipient_capacity`, CU bench/path/follow-up tests; live QA plus v2 custody statements. No partial physical/social commit on rejection. |
| E1 | proved | `E.test_attention_then_inspection_has_real_event_time_paths_no_belief`, `test_ef3_complete_visible_domain_exact_false_and_zero_are_not_unknown`, `test_inaccessible_channels_instruments_and_failed_delivery_are_atomic`; H actual partial inspection. |
| E2 | proved | `E.test_forwarded_report_retains_actual_source_and_parent_not_attribution`, `test_receipt_and_comprehension_are_not_adoption_and_unheard_basis_fails`, `test_ef2_g2_delayed_report_copies_stored_time_not_current_truth`; `harbor_dated_report` and CU late receipt/time test. |
| E3 | proved | `E.test_registration_and_frozen_keyword_only_records` checks sole belief-head writer; `test_no_unsupported_revision_no_latest_writer_no_opposite_on_reject`, `test_explicit_unknown_prior_initializes_not_resolves`, IP forged-history tests. V2 disposition histories retain predecessors. |
| E4 | partial | Old report/current location remain distinct in E/I delayed-report tests and `harbor_dated_report`/`harbor_closed_case`; CU no-prior opening fixed. Missing reviewed full false-at-reference / evidenced-change / present-applicability reader contrast; D06 freshness branch is in flight. |
| E5 | proved | `E.test_ef5_repeated_warning_reinspection_one_source_bounded_and_replayable`, `test_adoption_adds_new_matching_support_only_once`, H distinct warning receipts/source and finite budget; live H manual evidence, not 19 independent-source stories. |
| E6 | partial | `E.test_distinct_reference_times_need_distinct_heads_even_with_same_value`, `test_ef3_occluded_failed_partial_inspection_preserves_prior_not_absence`, `test_ef2_wrong_or_old_inscription_is_only_ink_without_narrow_authority`, `test_independent_carriers_of_same_exposure_keep_one_underlying_source` prove domain pieces. **Missing reviewed named five-correction integration; Mill's work pending.** |
| E7 | proved | `E.test_ef1_evidence_orders_have_one_explicit_resolution_and_immutable_prior`, `test_ef1_unknown_prior_initializes_without_discovery`; parents unchanged by revision, no corrective-action prerequisite; `harbor_dated_report` and closed/no-prior controls cite actual evidence times. E4/E6 limits remain separate. |
| S1 | proved | `RQ.test_undelivered_stale_proxy_and_duplicate_responses_emit_nothing`, `P.test_refuse_adapter_dispatches_owner_helper_without_double_writer`, `SP.test_loan_refusal_is_owned_by_physical_adapter`; H exact certification response and v2 declined return. |
| S2 | proved | `RQ.test_acceptance_acknowledgment_and_performance_are_distinct`, `test_receipt_before_acceptance_does_not_complete_request`, `SB.test_rejected_booking_is_not_attempt_but_real_check_is_evidence`, CH accepted-request pre-state test. |
| S3 | proved | `RQ.test_falsifier_one_withdrawal_preserves_acceptance_and_old_promise`, `SP.test_withdrawal_does_not_prohibit_independent_physical_action`; new RR baseline, independent outbound branch, production QA/masks/replay. No implicit reverse request or promise release. Latest RR run note below. |
| S4 | proved | `PR.test_exact_domain_actor_object_operation_result_terms_version`, `test_same_tick_but_precreation_receipt_cannot_fulfill`, `SP.test_exact_loan_receipt_and_version_are_required_without_duplicating_debt`, `SE.test_real_completion_claim_cannot_substitute_for_postcreation_performance`; CH exact resource/substitute replacement. |
| S5 | proved | `PR.test_falsifier_two_strict_and_inclusive_same_tick`, `test_same_tick_postcreation_receipt_can_fulfill_and_replay`; `observatory_strict_boundary` versus `observatory_inclusive_boundary`. Assessment waits for closed interval; not absence of prose. |
| S6 | proved | `PR.test_release_is_beneficiary_authorized_not_fulfillment`, `test_release_and_new_linked_terms_preserve_original`, `test_late_repair_does_not_erase_breach`; CH replacement/late-repair tests; `observatory_released`, `observatory_late_repair`, `observatory_released_replaced`. |
| S7 | proved | `CH.test_both_understood_promises_physically_selectable_then_consumption_blocks_other`, `test_new_request_refusal_after_breach_cannot_cancel_old_promise`, `test_reason_changes_with_fixed_props_and_guards_are_not_motives`, `test_reader_qa_motive_mask_and_focused_followups_use_rendered_choice`; three competing-promise artifacts and reversed priority. Supported attributed reasons, not inferred objective diagnoses. |
| T1 | partial | `CH.test_resource_choice_not_names_or_title_changes_semantic_outcome`, reason-change test, authoring role-binding test and RR distinct Harbor structure. Renaming works and priority changes outcomes. Three G1 name bindings alone do not prove the frozen three-world structural contrasts; D06 work pending. |
| T2 | partial | G1: I/P/CR tests plus `library_return`, grant/wrong-loan/latch negatives and claim-only adoption. G3: CH actual competing choices plus action-only/promise-only/replacement, replay and QA. G2: I dated-report/closed/no-prior/search-seed tests; omitted-second-observation/reference-time paired reader controls remain open. H is separate below. |

## Thirteen Falsifiers

| Falsifier | Status | Actual named tests / evidence and remaining distinction |
| --- | --- | --- |
| P-F1 | partial | `P.test_p_f1_receive_only_once_and_delayed_settlement_unsupported` proves active debt, one handoff, unchanged placement after later authority, no settlement operation. `test_old_loan_receipt_and_offer_cannot_settle_new_checkout` proves old/new isolation separately. Exact A1-untouched/A2-receive-only combined trace is not captured. Positive delayed settlement remains deferred, not failed or passed. |
| P-F2 | proved | `P.test_p_f2_bench_placement_removes_holder_not_debt`, `test_p_f2_cabinet_collection_no_imaginary_holder`; CU bench QA/path masks and `library_return` receipts distinguish passive source, holder absence and continuing borrower. |
| P-F3 | proved | `P.test_p_f3_readiness_does_not_reserve_recipient_capacity`, `test_p_f3_capacity_changes_after_loan_consent`, `test_p_f3_current_lending_and_release_grants_rechecked`; reject helpers compare pre-state, receipts and readiness. Search rejection creates no attempt. |
| P-F4 | partial | `CR.test_heard_and_adopted_delivery_claim_does_not_return_or_grant_authority` and `library_claim_only_return` now prove genuine claim/adoption versus active debt/no grant/no deposit. `P.test_p_f4_claims_do_not_deliver_or_grant_authority` is a stub claim, not the outdated-authority speech/adoption branch. E closed-container/delayed-report tests prove no content reveal or belief refresh separately. |
| P-F5 | proved | `P.test_p_f5_latched_deposit_and_dependencies_replay`, `test_p_f5_missing_latch_rejects_all_effects`, `test_path_and_authority_dependencies_survive_selection`; v2 missing-latch rejection and successful retained return; L frozen pins separately protect legacy meaning. |
| E-F1 | proved | `E.test_ef1_evidence_orders_have_one_explicit_resolution_and_immutable_prior`, `test_ef1_unknown_prior_initializes_without_discovery`; asserts histories/predecessors and one disposition, not final-value equality alone. |
| E-F2 | partial | `E.test_ef2_wrong_or_old_inscription_is_only_ink_without_narrow_authority`, `test_ef2_g2_delayed_report_copies_stored_time_not_current_truth`; `harbor_dated_report` and I masking test. Historical-accuracy unmasked control missing as described above; do not credit an always-abstaining query as intervention sensitivity. |
| E-F3 | proved | `E.test_ef3_occluded_failed_partial_inspection_preserves_prior_not_absence`, `test_ef3_complete_visible_domain_exact_false_and_zero_are_not_unknown`, `test_false_zero_result_equality_and_resolution_are_type_sensitive`; H partial/unknown controls. D06 named diagnostic integration remains a separate E6 obligation. |
| E-F4 | proved | `E.test_ef4_closed_container_motion_does_not_observe_or_fulfill_inspection`, `test_ef4_requested_promised_inspection_needs_actual_accessible_event`; SE exact/partial/unperformed inspection matching. Actual accessible inspection carries its own path/evidence and completes separately; promise alone cannot. |
| E-F5 | proved | `E.test_ef5_repeated_warning_reinspection_one_source_bounded_and_replayable` plus frozen H source lineage, reply/reason masks and selected replay. Reinspection has distinct sample times; repeated warning does not add sources or duplicate revision. |
| S-F1 | proved | `RQ.test_falsifier_one_withdrawal_preserves_acceptance_and_old_promise`, `SP.test_withdrawal_does_not_prohibit_independent_physical_action`, RQ duplicate/proxy response test; new RR accepted outbound/independent physical branch adds concrete Harbor binding. |
| S-F2 | proved | `PR.test_falsifier_two_strict_and_inclusive_same_tick`, `test_release_is_beneficiary_authorized_not_fulfillment`, `test_late_repair_does_not_erase_breach`; SE real completion claim test and boundary/release/late-repair v2 artifacts. Receipt order and closed interval are checked. |
| S-F3 | partial | `SP.test_falsifier_three_typed_refused_return_then_separate_settlement`, `P.test_g1_decline_then_new_offer_immediate_settlement` prove typed first decline, distinct second acceptance, and one settlement receipt. SP's reader assertion is handcrafted; I's production mask test covers decline/deposit, not this exact second-offer handover. Add the production reader contrast, not a new lifecycle. |

## Frozen H Is Separate Evidence

**H/G4: proved for the frozen fixture and interventions, not for all slices.**
Inspected `holdout_review.md`, all 16 H tests, and current production baseline
prose/QA directly. `HoldoutSemanticsTests` asserts actual partial external check,
unknown internal safety, two same-source warnings with distinct receipts,
delivered certification request and one exact decline, unchanged physics,
rejected-candidate silence, finite repetition, and full/retained replay.
`HoldoutReaderTests` asserts exact support spans, certification wording,
reply target, same-event historical-warning follow-up, and both reason/target
masks. Baseline, no-reply, no-repeat and separate accessible exact-inspection
branches retain their required distinctions. Earlier H wording failures are fixed.

Current manual reading confirms that A says the internal seal is unresolved at
time 0, B requests inspection **and safety certification**, A declines that task
for the explicitly attributed reason, and warning:2's why-answer stays on that
second event with reference time 0. No certification, repair or safety belief is
invented. This independent manual evidence is not supplied by the v2 case count,
and H does not exercise loans, competing promises, or all three settings.

## Unreviewed And Deferred

- Mill's five D06 fixtures and any new freshness-policy implementation are
  **pending inspection/execution**, regardless of parent-reported completion.
- Parent patches after the inspected exact-task wording, custody, claim-only,
  G2 search-order and separate-return-request changes, and any future v3 bundle,
  are unreviewed. This report does not certify unknown later workspace changes.
- Delayed settlement policy, recursive delegation, subloans, joint transport,
  general amendment/contracts, responder abandonment, probabilistic trust,
  general diagnosis/deception and unrestricted repetition remain deferred exactly
  as frozen. Requester withdrawal, release-plus-new-undertaking, bounded speech,
  narrow authority/source rules and masked QA are required, not deferred.
- No runtime LLM, paid evaluation, arbitrary literary threshold, generic NLP
  entailment system or broader ontology is requested. Embedded physical/evidence/
  obligation state and compatible moves remain aligned with the memeplex model.

### Final Run Note

Completed after report creation: the focused RR/CH/IP command passed **24 tests**;
the same full StoryScenes discovery command passed **329 tests** (24.856 seconds),
including all three RR tests. These supersede the earlier 326-test result for the
tested workspace snapshot. They do not credit Mill's unreviewed D06 work or close
the partial gates above. The implementation goal remains active.
