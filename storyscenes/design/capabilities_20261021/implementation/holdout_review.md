# Independent Holdout H / G4 Review

2026-10-22. Frozen authority: `acceptance_matrix.md`, HOLDOUT H. This is an
independent cross-family acceptance fixture, not an implementation demo. No
expected outcomes were relaxed, no tests skipped/marked expected-failure, and no
runtime, renderer, prior social files, or acceptance ledger were edited.

## Reproduction and Result

From the repository root:

```bash
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=storyscenes .venv/bin/python -m unittest test_capability_holdout -v
```

Observed: **16 tests, 13 pass, 3 fail**. H is **not accepted** yet. The failures
are reader/realization regressions below, not simulated-world transition failures.
Fixture: `storyscenes/test_capability_holdout.py::holdout_spec`; deterministic
explicit replay, no random seed or search success filtering. Every run constructs
the default `api.registry()` and calls production `realize.render` and
`reading.Reader`. There are no custom operations, synthetic event/receipt rows,
handwritten `Statement` objects, callbacks, or paid API calls.

## Failing Regressions

1. **H-R1: Certification terms disappear from the delivered request.**
   `HoldoutReaderTests.test_delivered_request_prose_preserves_internal_safety_certification_not_generic_inspection`
   expects the request/answer to express certification of the internal seal as
   safe. Authored finite terms are `certify the internal seal safe now`, operation
   `inspection`, exact fact `internal_fact`, required value `safe`, version 1.
   Actual renderer/answer: `"Will you inspect internal seal?" B asked A.`
   `realize.action_phrase` drops the certification/result distinction. Checking
   an indicator, inspecting a seal, and certifying its safety are not equivalent.

2. **H-R2: Reply-target QA is marked supported without identifying the task.**
   `HoldoutReaderTests.test_reply_target_qa_names_the_declined_certification_and_focused_reason`
   asks `Which request did A decline?` through the existing response interface.
   Actual answer: `"No, I decline," A answered B.` The hidden response focus and
   request dependency are correct, but the answer does not identify internal
   safety certification. Render/answer the exact target, rather than treating its
   invisible ID as natural-language support. Do not infer a different request.

3. **H-R3: Historical-report follow-up loses the enacted explanation.**
   `HoldoutReaderTests.test_repeated_historical_warning_followup_keeps_second_event_not_first`
   selects claim `warning:2`: reference time 0, acquisition/emission time 1.
   Its explicit rendered explanation belongs to `warning:2`, with reference time
   1. `Reader.follow_up("why")` forces the claim's time 0 and returns unsupported,
   despite that same-event explanation being visible. Preserve both kinds of
   time and the selected event; do not fall back to `warning:1` or collapse the
   second warning's evidence time into a fresh inspection.

These are coordinator-owned fixes. The tests assert required behavior directly;
they do not pin the defects as desired output.

## World and Event Evidence

At the harbor bench, A and B are co-located with a closed, latched instrument.
The external indicator is reachable outside it; the internal seal is inside it.
The hidden internal signal is authored `safe`, but no actor reads that signal in
the baseline. The indicator's complete visible domain is only `indicator`;
its actual result is **partial**, with alternatives `safe` / `unsafe` and no
exact value. This is neither exact false nor an inaccessible/unknown result.
No actor belief asserts safety or its opposite. The partial result is an actual
executed inspection, not an invented consequence of guard rejection.

Full baseline, 13 events:

```text
focus_indicator:1
inspect_indicator:1
warning:1
receive_first:1
understand_first:1
focus_internal:1
draft_request:1
deliver_request:1
decline:1
later:1
warning:2
receive_repeat:1
understand_repeat:1
```

`inspect_internal` is also submitted while the instrument is sealed. It rejects
with identical before/after fingerprints, no use count, evidence, attempt, reply,
or story event. `focus_internal:1` is attention only, not an inspection.

Both warnings reference the same proposition from `partial_indicator`, evidence
IDs `("partial_indicator",)`, source IDs `("indicator",)`, and no added parent
claim. They have different IDs and emission times 0/1. Both have separate actual
delivery/comprehension records for B. `warning` has `max_uses=2`; a third use
rejects without changing anything. There is no repetition-enabling world flag,
new independent corroboration, or automatic belief update.

The request's delivery and direct finite-term understanding are both
`deliver_request:1`. Its sole response is `declined`, response event `decline:1`.
Decision `certification_decline` binds that exact request/version, A, B, and
support `inspect_indicator:1`. Its reason is attributed speech, not a factual
diagnosis inferred from guards. A duplicate initial decline rejects.

Physics remains identical to initial state: `parents`, `ownership`, `containers`,
`loans`, `receipts`. No opening, transfer, repair, promise, request completion,
domain performance receipt, belief head, or belief disposition appears. Only the
finite clock advances to 1; the ending remains unresolved.

### Root Selection and Replay

Roots: `understand_first:1`, `decline:1`, `understand_repeat:1`. Closure contains
12 events: the full list above **except** unused `focus_internal:1`.
`replay_selection` reproduces the exact selected immutable events, response,
partial evidence, reason, counts, and source lineage. Full replay equals the
original state. Rendering the original with selected visibility exactly equals
rendering the retained replay, including generated QA. Rejection is never retained
as a fictional attempt. Both removal interventions and the exact-inspection branch
also have successful selected replay checks.

## Captured Production Prose

No authored opening/ending or manual narrative annotations are supplied. The
following is actual baseline output, retained verbatim to expose the two semantic
wording failures rather than silently repairing them in this review:

```text
A inspected external indicator. The check left internal seal's internal safety unresolved.

A sent B this report: "The check left internal seal's internal safety unresolved."

"Only the external indicator was checked; the internal seal has not been inspected," A explained.

B received A's report.

B wanted to ask A to inspect internal seal.

"Will you inspect internal seal?" B asked A.

"No, I decline," A answered B.

"I cannot certify the internal seal safe because I have inspected only the external indicator, not the internal seal," A explained.

A sent B this report: "The check left internal seal's internal safety unresolved."

"Only the external indicator was checked; the internal seal has not been inspected," A explained.

B received A's report.
```

Semantic reading: the partial check and repeated warning remain unresolved;
neither safety nor unsafe status is asserted as fact. The causal sentence is
properly attributed. However, the delivered request is weakened, and the target
answer does not identify the request. The grammar is utilitarian; no literary
quality score or general English-entailment pass is claimed.

### Baseline QA and Follow-ups

| Question / focus | Actual answer and support | Review |
| --- | --- | --- |
| What did A check, and what remained unknown? / `partial_indicator` | `A inspected external indicator. The check left internal seal's internal safety unresolved.` Event `inspect_indicator:1`, reference/acquired 0. | Grounded partial result, not exact negative. |
| What did B request? / `certify_internal_seal` | `"Will you inspect internal seal?" B asked A.` Event `deliver_request:1`, time 0. | Fails H-R1: lacks certification/safe result. |
| Which request did A decline? / `certify_internal_seal` | `"No, I decline," A answered B.` Request + response support, time 0. | Fails H-R2 despite `supported=True`. |
| Why did A decline? / same response follow-up | `A gave this reason: I cannot certify the internal seal safe because I have inspected only the external indicator, not the internal seal.` Request, response, reason support; event `decline:1`, time 0. | Grounded attributed explanation; same focused event/time. |
| What did A repeat? / `warning:2` | `A sent B this report: "The check left internal seal's internal safety unresolved."` Event `warning:2`, reference 0, acquired 1. | Keeps the old signal's time. |
| Why? / follow-up to `warning:2` | `The story does not establish that.` | Fails H-R3: explicit explanation exists at that same event. |

### Exact Support Spans

Offsets below are half-open character positions in the captured production story.
The test verifies every slice equals its statement text and checks event/entity
references and acquisition times. IDs use `<event>/<kind>/<focus>`.

| Span | Event / kind / focus | Entity IDs | Reference / acquired |
| --- | --- | --- | --- |
| 0:90 | `inspect_indicator:1 / observation / partial_indicator` | a, indicator, seal | 0 / 0 |
| 92:174 | `warning:1 / claim / warning:1` | a, b, seal | 0 / 0 |
| 176:273 | `warning:1 / why / warning:1` | a | 0 / 0 |
| 275:297 | `receive_first:1 / receipt / warning:1` | b | 0 / 0 |
| 299:342 | `draft_request:1 / intention / certify_internal_seal` | b | 0 / 0 |
| 344:388 | `deliver_request:1 / request / certify_internal_seal` | b, a | 0 / 0 |
| 390:420 | `decline:1 / response / certify_internal_seal` | a, b | 0 / 0 |
| 422:553 | `decline:1 / why / certify_internal_seal` | a | 0 / 0 |
| 555:637 | `warning:2 / claim / warning:2` | a, b, seal | 0 / 1 |
| 639:736 | `warning:2 / why / warning:2` | a | 1 / 1 |
| 738:760 | `receive_repeat:1 / receipt / warning:2` | b | 1 / 1 |

## Paired Interventions

1. **Remove the enacted reply.** Baseline has 13 events; paired run has exactly
   those events minus `decline:1`. Request stays pending; response event is absent;
   refusal table is empty. No response/reason/reply-target QA or guessed follow-up
   is supported. The rejected internal candidate supplies no replacement reply.

2. **Suppress the repeat.** Paired run removes exactly `warning:2`,
   `receive_repeat:1`, `understand_repeat:1`; evidence, request, refusal, source,
   beliefs and physics otherwise match. The rendered document equals the original
   with only those events' statements removed. There is one source, not fewer
   independent sources. Baseline's third-warning rejection proves the finite cap.

3. **Keep trace fixed; mask necessary text/support together.** Each masking test
   asserts the unchanged state fingerprint, exact retained statement sequence,
   exact joined narrative, and recalculated spans. No invisible replacement text
   or hand-authored answer is injected.

Reason mask removes observation, both warning claims/explanations, and the decline
explanation: six statements, including all the quoted partial-inspection rationale.
Remaining exact narrative:

```text
B received A's report.

B wanted to ask A to inspect internal seal.

"Will you inspect internal seal?" B asked A.

"No, I decline," A answered B.

B received A's report.
```

Response remains readable. `Why did A decline?` and its response-focused
follow-up both abstain. Receipt assertions whose report support disappeared are
not independently supported QA.

Reply-target mask removes **all four** request-focused statements: intention,
delivered request, response, and attributed decline reason (the reason also names
the requested certification). Remaining exact narrative:

```text
A inspected external indicator. The check left internal seal's internal safety unresolved.

A sent B this report: "The check left internal seal's internal safety unresolved."

"Only the external indicator was checked; the internal seal has not been inspected," A explained.

B received A's report.

A sent B this report: "The check left internal seal's internal safety unresolved."

"Only the external indicator was checked; the internal seal has not been inspected," A explained.

B received A's report.
```

`Which request did A decline?` and decline-reason QA abstain. A warning-focused
follow-up asking about a response also abstains rather than jumping to a hidden
neighboring request ID.

4. **Accessible exact inspection, separate branch.** Preserve the 13 baseline
   events, advance to 2, actually open the instrument, and execute the previously
   rejected `inspect_internal` candidate. New evidence `internal_exam` is exact
   `safe`, reference/acquired 2, source IDs `("seal",)`, actor path `(a, bench)`,
   source path `(seal, instrument, bench)`. Beliefs remain empty until a separate
   executed `update_belief` using the percept policy. Earlier partial evidence,
   declined request, response ID, attributed reason, and all 13 earlier events
   are unchanged. No automatic assent, promise, request completion, or repair is
   invented. Old-visible prose is byte-for-byte unchanged; old observation QA
   remains unresolved at 0 while the new observation says safe at 2. Selected
   replay including the new explicit belief decision reproduces the full branch.

Finally, swap the hidden internal fact between `safe` and `unsafe` while sealed:
both runs expose identical intentional proposals, baseline event histories,
rendered narratives, and rejected inspection behavior. Only actual later access
can acquire that hidden result. This is a scoped H check, not a claim of a general
agent policy or completion of every acceptance-ledger item.

## Post-Fix Verification

2026-10-22, after the coordinator's renderer changes. This section supersedes the
initial failing disposition above; the original findings, output, spans, and
intervention evidence remain intact as the pre-fix record.

The reproduction command above now reports **16 tests, 16 pass, 0 failures**.
The holdout tests are unchanged: no relaxed assertions, new skips, expected-failure
annotations, replacement fixture, or hand-authored narrative support. Only this
review file was edited during this verification. The actual production prose,
Reader answers/follow-ups, masks, and separate accessible branch were also read
directly, not judged solely by test count.

**Disposition: frozen H/G4 passes for this fixture and its required interventions.**
This is not closure of the full implementation goal, another acceptance-ledger
gate, or a general literary/English-entailment claim. The full goal remains active.

### Resolution of Original Findings

**H-R1 resolved.** Actual intention and delivered-request prose now preserve the
required result, rather than substituting generic inspection:

```text
B wanted to ask A to inspect internal seal and certify its internal safety as safe.

"Will you inspect internal seal and certify its internal safety as safe?" B asked A.
```

Semantic reading: this requests an inspection *and certification of safety*, not
an assertion that the seal is safe or that inspection already happened. The
wording is somewhat repetitive ("internal seal" / "internal safety as safe"), but
the required distinction is explicit and understandable. The same certification
wording appears in the generated request answer.

**H-R2 resolved.** Actual response text names the exact requested task:

```text
"No, I decline," A answered B's request to inspect internal seal and certify its internal safety as safe.
```

`Which request did A decline?` now receives:

```text
A declined B's request to inspect internal seal and certify its internal safety as safe.
```

The answer identifies the certification task in readable language. It is backed
by `deliver_request:1` and `decline:1`, rather than merely possessing a hidden
request ID. The reply remains a refusal, not a promise, inspection, repair, or
opposite safety finding. Its focused `why` follow-up returns:

```text
A gave this reason: I cannot certify the internal seal safe because I have inspected only the external indicator, not the internal seal.
```

The reason is still explicitly attributed to A, not converted into an omniscient
diagnosis or a guard-derived motive. Response and follow-up remain focused on the
same request/decline and reference time 0.

**H-R3 resolved.** Selecting `warning:2` and then asking `why` now returns:

```text
A gave this reason: Only the external indicator was checked; the internal seal has not been inspected.
```

Its support is exactly `warning:2/claim/warning:2` plus
`warning:2/why/warning:2`; its event IDs contain only `warning:2`, not `warning:1`.
Both statements have reference time **0** and acquisition time **1**. The second
utterance therefore remains a later repetition of the same old sample, not a new
inspection, a second independent source, or a time-refreshed safety finding.

### Frozen Assertions Rechecked

| Frozen H requirement | Post-fix evidence and semantic outcome |
| --- | --- |
| Reachable instrument, visible exterior, inaccessible interior | A and the instrument remain at the harbor bench; instrument is closed/latched, seal is its child. The external indicator's executed inspection has its own accessible actor/source paths. The inaccessible internal candidate still rejects. |
| Actually performed partial check; internal safety unresolved | `partial_indicator` remains `partial`, alternatives `safe` / `unsafe`, no exact value. Actual prose says the external indicator was inspected and internal safety was **unresolved**. This is not false/unsafe, nor an enacted internal inspection. |
| Two bounded utterances with actual receipt/understanding and one source | `warning:1` / `warning:2` still have distinct emission times 0/1, receipt and comprehension identities, but identical proposition, evidence ID, and source IDs `("indicator",)`. Third warning rejects; no repetition flag, corroboration, or belief update is introduced. Rendered reports repeat the limitation and make no corroboration claim. |
| Delivered/understood certification request and one linked decline | Direct finite-term delivery/understanding remains `deliver_request:1`; decision `certification_decline` still binds the exact request/version and `decline:1`. Revised prose/QA explicitly identify the safety-certification target. Duplicate initial response still rejects. |
| Supported attributed reason, not omniscient motive inference | The refusal retains its explicit quoted reason and `inspect_indicator:1` support. Reader says "gave this reason"; it does not infer an inability, lie, or repair from hidden truth/guards. |
| Rejected candidate is not an enacted attempt/reply | Rejected internal inspection leaves the fingerprint, counts, history, evidence, and prose unchanged. It supplies no substitute refusal in the no-reply intervention. |
| No baseline promise, repair, transfer, opening, certification performance, or safety belief | Physical parent, ownership, container, loan, and receipt tables remain identical to initial state. Promise, domain-performance, belief, and disposition tables remain empty; request completion remains absent. Desired safety in a quoted request is not narrated as an achieved result. |
| Dependency retention and replay without retaining every unused event | Full trace remains 13 events. Roots retain 12, pruning unused `focus_internal:1`. Full replay, selected replay, rendered selected/retained documents, and generated QA agree. No standalone unused clock paragraph is emitted. In the no-repeat intervention, the now-unused time event can also prune without changing prose. |
| Equivalent hidden safety states do not inform choices | Swapping sealed internal truth `safe` / `unsafe` still leaves intentional proposals, baseline event histories, rejected checks, and production narrative identical. |

The baseline is still unresolved. The final report repeats that internal safety
is unresolved and that only the external indicator was checked; neither the
request nor its decline supplies the missing certification. This verifies the
intended failed/unresolved outcome without selecting a success branch.

### Required Interventions Rechecked

1. **Remove reply:** exactly `decline:1` disappears (13 -> 12 events). Request
   remains pending, no response event or refusal record appears, and response,
   reason, reply-target and unsupported follow-up questions abstain. The rejected
   check does not become the missing reply. Retained replay remains legal and
   renders the same intervention document.

2. **Suppress warning:** exactly `warning:2`, `receive_repeat:1`, and
   `understand_repeat:1` disappear (13 -> 10 events). Source count/identity,
   partial evidence, safety beliefs, request disposition, and physical state do
   not change. The narrative loses only those events' statements. The baseline's
   third-use rejection still proves finite repetition. The unused clock event
   can prune from the retained run, with identical rendered output.

3. **Mask reasons or reply targets, keeping trace fixed:** exact statement/text
   removal and recalculated support spans still pass. All causal-support text is
   removed for the reason mask; the response remains readable, but `why` and its
   focused follow-up abstain. The updated exact reason-masked narrative is:

```text
B received A's report.

B wanted to ask A to inspect internal seal and certify its internal safety as safe.

"Will you inspect internal seal and certify its internal safety as safe?" B asked A.

"No, I decline," A answered B's request to inspect internal seal and certify its internal safety as safe.

B received A's report.
```

The reply-target mask removes all four request-focused statements, including the
quoted reason that itself names certification. Its exact remaining narrative is
unchanged from the pre-fix reply-target mask captured above. Both target and
decline-reason QA abstain, as does a warning-focused follow-up about the hidden
response. Neither mask mutates simulation state or retrieves an answer from a
hidden focus ID. The reason mask does not remove the task itself: being asked to
certify safety is not evidence of why A declined it.

4. **Accessible exact internal inspection, separate branch:** after preserving
   all 13 prior events, time advances to 2 and the instrument is actually opened.
   The previously rejected operation now produces exact `internal_exam` evidence,
   source `seal`, with actor/source paths and reference/acquisition time 2. No
   belief is written until the separately executed percept-policy update. Actual
   newly rendered text is:

```text
A opened sealed instrument.

A inspected internal seal. Internal seal's internal safety was safe at time 2.

A accepted that internal seal's internal safety was safe at time 2.
```

Semantic reading: safety is newly established only after opening and actual
inspection. Old observation QA remains unresolved at 0; new observation QA says
safe at 2. Earlier partial evidence, decline, reason, request response identity,
and prior-visible narrative are unchanged. The request does not automatically
become accepted/completed, and no promise or repair appears. Explicit-belief-root
selected replay reproduces the full branch. "Opened sealed instrument" uses the
fixture's object name, not a claim that the instrument stayed closed after being
opened; its state and the subsequent inspection make that change clear.

### Updated Support Coordinates

The production baseline now has 11 supported statements and 915 characters.
Unchanged first four spans remain `0:90`, `92:174`, `176:273`, `275:297` with
their original identities. Following changed/shifted half-open spans supersede
the pre-fix coordinates above; event/entity identities remain unchanged.

| Span | Statement ID | Reference / acquired |
| --- | --- | --- |
| 299:382 | `draft_request:1/intention/certify_internal_seal` | 0 / 0 |
| 384:468 | `deliver_request:1/request/certify_internal_seal` | 0 / 0 |
| 470:575 | `decline:1/response/certify_internal_seal` | 0 / 0 |
| 577:708 | `decline:1/why/certify_internal_seal` | 0 / 0 |
| 710:792 | `warning:2/claim/warning:2` | 0 / 1 |
| 794:891 | `warning:2/why/warning:2` | 0 / 1 |
| 893:915 | `receive_repeat:1/receipt/warning:2` | 1 / 1 |

The holdout contains no physical movement or promises. Nonzero movement-time and
strict-before/inclusive-by promise wording changes therefore receive no extra
acceptance claim from this H rerun; their separate gates remain the coordinator's
responsibility. All frozen H assertions and its semantic reading outcomes above
are confirmed within the tested scope, with original findings preserved.
