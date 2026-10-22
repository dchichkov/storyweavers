# Informing Capability: Claims Without Omniscience

## Scope and existing behavior

Design only; nothing proposed is implemented or tested. In `storyscenes/runtime.py`, `tell` requires a non-null speaker belief and copies it into the listener's `.knows.*` slot. `observe` copies truth into belief; perceptual access is authored. `algebra.compose` supplies these operations; `build` preserves initial beliefs. `test_algebra.py::test_explicit_stale_belief_survives_auto_declaration_and_tell` demonstrates wrong-value transmission without changing truth.

`dialogue.collect_dialogue` already indexes quotations, attributed participants, claims and reasons; those annotations do not execute speech acts. `Conversation.source_answer` follows a belief's last writer, `truth_answer` checks its timed truth, and `causal_answer` explains enabling guards, not motivation. `prose.render_book` preserves selected fact bindings and speech spans, not proof of English entailment. The 100-world `REPORT.md` and `TODO.md` identify offstage questions, unindexed speech and weak causal focus despite zero deterministic evidence defects.

Propose opt-in `communication_v2` under a separately versioned world/compiler/QA adapter. Missing version means historical `Tell`; never reinterpret frozen traces. The new contract distinguishes assertion, delivery, comprehension, acceptance and truth. It advances `story.py` by embedding information in speakers, recipients and physical messages, with character-held motives affecting choices rather than free-floating concepts.

## Reusable contract

**Participants and content.** `Communicate(speaker, recipient, claim, channel)` binds people and a physical channel. Claims have ID, proposition `(subject, predicate, value)`, temporal scope, utterance time, attributed source and optional evidence/parent-claim IDs. Support declared scalar predicates, including false; unknown is not false. Immutable content is carried by utterances/documents, not invented physical "claim entities."

Separate what the speaker attributes from verified provenance: "the keeper says" is not proof the keeper spoke. Actual provenance references accessible observations or earlier receipts; relaying preserves the chain and original scope. A claimed observation time can itself be unsupported. Honest reporting reads a speaker belief; attributed quotation reads a received claim. Explicit fabrication may supply another value, but falsehood alone never establishes lying or intent.

**Reads and legality.** Read speaker content access, channel reachability, recipient identity, any authored attention/language condition, and choice-relevant embedded state. A shared room can enable speech but does not prove hearing. A remote message needs a working link or transported carrier, not planner omniscience. No truth prerequisite: false and stale reports remain legal. Motive references identify a speaker goal and its decision relationship; channel guards alone cannot answer "why did she tell him?"

**Writes and recipient updates.** An atomic communication event records assertion and delivery result. Delivery appends a recipient receipt with comprehension `understood`, `uninterpreted` or `unknown`; accepted beliefs and truth remain unchanged. `RespondToClaim(recipient, receipt, disposition, basis)` records `adopt`, `reject` or `defer`. Nonconflicting adoption requires understood content and a supported policy, then updates the belief head with claim/source IDs, retaining its predecessor. Conflicting adoption instead references the single revision owned by discovering_mistake; informing must not overwrite belief a second time. Rejection means non-adoption, not believing the opposite. Deferral records pending consideration; acknowledgment means receipt only. No global trust score or recency-wins rule.

**Evidence and failure.** Events retain actor IDs, claim/receipt IDs, delivery/comprehension result, before/after belief references, actual and attributed source, content scope, emission/delivery times, policy inputs, reason references and correction/reply links. World validity is evaluated separately as supported, contradicted or unknown at a specified time. A once-correct report need not justify a present-tense inference. False-at-scope and later-outdated remain distinguishable.

An unreachable candidate is unexecuted, not a narrated failed attempt. A deliberate transmission attempt can instead produce a bounded failure event with an observable result, such as link loss; it creates no receipt. Repeated understood speech may add a genuinely distinct utterance/receipt without changing belief. `runtime.transition` currently rejects unchanged state, and `planning.prune_path` can discard irrelevant preparation. The extension therefore needs meaningful bounded event records even without physical changes, plus typed evidence/response dependencies retained through pruning and replay. Do not add dummy flags. Current scalar-only state cannot already hold these records: a new validated record representation/compiler is required, not JSON hidden in strings.

**Non-goals.** Informing does not grant permission, transfer custody, fulfill promises, detect mistakes, prove comprehension from text proximity, or compel compliance. QA requires both trace support and visible selected-story evidence; hidden truth supports debugging only. Every answer tracks claim, recipient, event and time focus; missing support triggers abstention.

## Story 1: Library - The Atlas Behind the Desk

**Premise and state.** Eli wants an atlas for tonight's neighborhood walk; librarian Mara wants to help him leave prepared. The atlas is behind the desk, although Mara's unchanged catalogue belief says it is on loan. Jo has seen it there. The reader receives the atlas's position, Mara's mistaken belief and Eli's goal. Choice: Mara can repeat her answer or consider Jo's report. The ending shows Eli opening the atlas under the desk lamp; no moral-success requirement drives the engine.

**Six beats.** Candidate opportunities, not a required script:

1. Eli requests access to the atlas. Requesting records the pending request; his walking goal explains the urgency.
2. With Eli listening, Mara says it is on loan, honestly using her catalogue belief. He receives the claim, not automatic knowledge.
3. Eli provisionally adopts it under an ordinary desk-information policy; his access request remains uncompleted.
4. Jo observes the atlas behind the desk and tells Mara where she saw it. Receipt and understanding expose a conflict without silently revising Mara.
5. Discovering_mistake compares the report with Mara's belief; Mara checks the desk, revises, and explicitly corrects her earlier claim to Eli. He adopts the correction using that check as its basis.
6. The library's access action permits desk consultation, and Eli unfolds the atlas. Requesting records completion only after access occurs.

**Exchange, linked to beats 4-5.**

Jo: "I just saw the atlas behind your desk."

Mara: "You were right. Eli, I checked: it is here, not on loan."

Eli: "Then I can stop looking for another copy."

Jo delivers evidence; Mara corrects; Eli explicitly adopts through revision. His final line changes his plan, not permission.

**Interventions.** Remove Jo's delivered receipt: with no alternative check selected, Mara retains the catalogue belief and Eli leaves without desk consultation. Keep delivery but defer adoption pending inspection: Eli waits; merely hearing Jo cannot unlock the corrected-belief route.

**QA and visible evidence.** Render Mara's initial answer, Jo's observation, the check, correction and Eli's uptake; attach L1-L6 evidence IDs.

- Why did Mara give Eli a different answer later? Jo's report led her to check behind the desk. She found the atlas and corrected her earlier answer. Evidence: L4-L5 plus Mara's checking goal.
- Linked follow-up, "Did Eli believe her first answer?" Eli initially accepted that the atlas was on loan. He changed his belief after Mara's checked correction. Evidence: L3/L5; inspect the same correction's recipient and predecessor claim.
- Did Mara knowingly lie? The story shows that she believed the catalogue entry when she spoke. It does not establish an intention to deceive. Evidence: visible opening belief and L2, not mere falsity.

## Story 2: Harbor - The Clearance That Arrived Late

**Premise and state.** Mechanic Neri wants a repaired launch to depart; skipper Pavel wants to avoid the closing harbor gate. At 08:00 the gate is open, and keeper Sal records that observation in a message. A squall closes it at 08:10; delivery occurs at 08:15. Pavel still believes the gate open. The reader sees both times, closure and delayed arrival. Neri's consequential choice is to preserve the timestamp rather than shorten the message to "the gate is open." The ending leaves the repaired launch tied beside the workshop, rain tapping its new cover.

**Six beats.**

1. Sal observes the open gate and emits a timestamped report over the harbor messaging link; the content remains fixed while queued.
2. The squall closes the gate. This changes physical truth, not Sal's earlier report or Pavel's belief.
3. Neri receives the delayed report and understands its historical scope. She does not infer present clearance.
4. With Pavel listening, Neri relays the exact 08:00 scope and requests a fresh gate check, motivated by safe departure rather than a generic helpfulness label.
5. Pavel records receipt but defers adopting current clearance. A fresh keeper report, grounded in the closure observation, supports revision to closed through discovering_mistake.
6. Pavel postpones departure; a separate workshop action secures the repaired launch. Repair completion and departure remain different outcomes.

**Exchange, linked to beats 4-5.**

Neri: "Sal saw it open at eight. This arrived fifteen minutes later."

Pavel: "I heard you. I am not treating that as clearance now."

The reply acknowledges receipt and defers current clearance, not the historical observation.

**Interventions.** Deliver at 08:01 with a still-open gate and valid current-clearance policy: Pavel can adopt clearance and depart before closure. Keep late delivery but remove the fresh report: Pavel remains uncertain and waits; QA cannot say he learned the gate was closed.

**QA and visible evidence.** Render the timestamp, squall closure, actual delivery time, Pavel's deferral and fresh report; attach H1-H6 evidence.

- Why did Pavel delay despite receiving an open-gate message? The message described eight o'clock, not the gate at delivery. Pavel waited for a current check and then learned it was closed. Evidence: H3-H5 and his departure policy.
- Linked follow-up, "Was Sal wrong at eight?" Sal's eight-o'clock observation matched the open gate. The gate closed afterward, so that report no longer justified present clearance. Evidence: H1-H2; retain the report and specify its scope.
- Did the repair fail? The launch was repaired. Pavel postponed departure because of gate information, not a failed repair. Evidence: visible repair state and H5-H6; never infer repair status from waiting alone.

## Story 3: Observatory - One Glimmer, Two Voices

**Premise and state.** Observer Ivo wants to record a possible mountain beacon; analyst Sera wants adequate confirmation before using their limited signal battery to alert the valley. Tamsin operates the relay. Ivo sees a glimmer but cannot distinguish beacon from reflection. Sera has no accepted identification. The reader sees the uncertain observation, single source and scarce battery. Sera chooses to preserve uncertainty rather than count a relay as independent confirmation. The ending shows the unused battery beside a log marked "unconfirmed," while dawn lights the ridge.

**Six beats.**

1. Accessible sight through Ivo's instrument yields evidence of a glimmer, not proof of its cause. Observing owns this limited observation.
2. Ivo reports "a glimmer at the ridge; identity uncertain" to Tamsin over a working link. Tamsin understands and adopts only that scoped observation report.
3. Tamsin relays it to Sera, keeping Ivo's evidence ID. Sera receives and understands it, without adopting beacon identity.
4. Ivo reaches Sera directly with the same report. It is another delivery, not another independent observation.
5. Sera defers beacon classification under her confirmation policy because both messages share one source. Her Precision magnitude and battery-conservation goal make that choice eligible and motivated.
6. She records the unresolved sighting and leaves the signal battery unused. No hidden beacon truth is needed to conclude the story.

**Exchange, linked to beats 3-5.**

Tamsin: "Ivo saw a glimmer. He could not identify it."

Sera: "His direct message says the same. Those are two messages about one sighting."

Tamsin: "Then I will keep it marked unconfirmed."

The exchange transmits attribution, explains deferral and updates Tamsin's status without manufacturing evidence.

**Interventions.** Replace the second delivery with an independently accessible, identifying observation that meets Sera's policy: she can accept beacon identity and authorize a separate signaling action. Drop only Tamsin's delivery: Ivo's direct report still supports logging, but there is no two-source confusion; fewer messages alone do not imply less independent evidence.

**QA and visible evidence.** Render Ivo's uncertainty, shared source attribution, Sera's policy and final log/battery state; attach O1-O6 evidence.

- Why did Sera leave the battery unused? She lacked the independent confirmation required before signaling. Both messages described Ivo's single uncertain sighting. Evidence: O3-O6 plus her stated conservation goal.
- Linked follow-up, "Who originally saw it?" Ivo saw the glimmer through his instrument. Tamsin relayed his report rather than making another observation. Evidence: O1-O3; retain glimmer focus, not beacon identity.
- Was it really the beacon? The story does not identify the glimmer's cause. It ends with the sighting unconfirmed. Evidence: visible uncertainty and O6; abstain even if simulator-only truth exists.

## Cross-capability composition

Observing owns accessible timed evidence; informing never upgrades percepts to truth. Discovering_mistake owns conflicting revisions and preserves old beliefs. Carrying owns transported message parents and derived location, without ownership effects or instant delivery. Lending/returning own agreement, physical receipt and discharge: information about equipment never activates or discharges loans.

Outside that peer group, requesting owns the library access request and harbor fresh-check request, including pending/completed distinctions. Promising owns commitments, if later introduced; an informative reply cannot create one implicitly. Refusing owns a declined action and its reasons; rejecting a claim is epistemic disposition, not social refusal. These interfaces remain proposals, particularly while those workers are queued.

## Acceptance tests

All are proposed gates, not passing-test claims. Positive: replay atomic delivery followed by explicit adoption; confirm distinct evidence IDs and unchanged world truth. Test understood receipt with unchanged prior belief, false honest transmission, timestamp-preserving relay and uncertain content without forced classification.

Negative: reject adoption before receipt, unsupported source IDs, inaccessible channels and ambiguous temporal references. A guard-rejected candidate creates no attempted event. A recorded failed attempt creates no receipt. Repetition cannot create independent evidence or infinite loops. Reject unsupported motive/lie claims, future-evidence QA, offstage facts and acknowledgment-as-acceptance.

Intervention: execute each story's two interventions with the same content contracts; compare receipt, belief and downstream decisions, not just prose. Pruning must preserve response/correction/source dependencies and replay; changing prose seed cannot alter acceptance. Compatibility pins retain historical `Tell` copying, including wrong stored values.

Transfer: bind the same claim/receipt/update mechanics across all three settings with no title-based rules. Measure three semantic structures: false belief corrected, accurate historical information made stale, and source-dependent uncertainty retained. Renamed props, quotation variants and reordered independent speech do not count as new structures. Review each QA against visible prose as well as trace; masking a necessary passage must suppress its comprehension answer.

## Open decisions

Smallest slice: typed scalar claims, one addressed recipient, direct speech plus a timestamped queued channel, explicit dispositions, provenance links and reader-evidence filtering. Coordinator must settle record storage, event-only transition/replay support, pruning roots, temporal scope vocabulary, comprehension ownership and revision authorization. Keep bounded per-action usage and deterministic outcomes.

Defer probabilistic persuasion, group audiences, arbitrary propositions, automatic deception inference and generalized trust learning. Preserve explicit authorship of motives and acceptance policies. The three outlines specify possible outcomes, not mandatory moral resolutions or hardwired routes.
