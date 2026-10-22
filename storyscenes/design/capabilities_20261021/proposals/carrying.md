# Carrying: physical continuity without implied entitlement

## Scope and existing behavior

Design only; no implementation or passing tests claimed. Reuse role-bound opportunities (`algebra.Pattern`, `Kernel.bind`), atomic validation (`runtime.transition`), and event snapshots (`runtime.solve`), not prescribed scene order.

Currently `runtime.transfer` writes `.owner`; `algebra.compose` implements Lend/Return through that slot and `.loaned_by`. Move requires the actor in `.owner` and changes only the prop's `.location`. `test_algebra.AlgebraTests` verifies lender matching and stale-belief transmission, not carrying. Preserve frozen interpretations; never infer legal ownership from legacy `.owner`.

The 100-world report and `storyscenes/TODO.md` identify stale locations, duplicate handovers, and offstage questions. `Conversation.clause` realizes owner as "had"; `causal_answer` explains guards, not motives. New paths need versioned QA. `prose.render_book` bindings do not prove English entailment; retain story-only review.

Toward `story.py`'s north star: objects remain physically embedded; actors' wants and Care guide choices. No universal ontology or runtime language models.

## Reusable contract

**Proposed opt-in `physical_v1`.** Bind actor, object, source, destination, and optional recipient. Located entities have one immediate `parent` and relation: `at` a place, `on` a support, `in` a container, or `held_by` an actor. Places terminate paths; actors are at places. References must exist; cycles are invalid. Explicit unknown placement blocks operations requiring co-location; it is not "nowhere."

`effective_place(x, time)` walks the physical path. `custodian(x, time)` is the actor on that path, if any; it describes physical possession, not responsibility, entitlement, or permission. A book inside a tote held by Ada is indirectly in Ada's custody. A tote on a table has no physical custodian, even if Ada remains its borrower. Immediate handholding is a separate query. Derived values are not independently writable slots.

Declarations provide portability, mass/hand demand, container capacity/open state, actor limits, and routes. Loads count nested contents once. Containers are passive; exclude carts, passengers, joint lifting, coercion, and gravity simulation.

**Operations and reads.** `Pickup(actor, object, source)` requires the declared source, reachable co-location, accessible containment path, portability, and sufficient resulting mass/hand capacity. It reparents the object to `held_by actor`. Taking from another actor requires explicit `Handoff`, not Pickup. `Put(actor, object, target, relation)` requires direct holding, reachable target, appropriate open container/support, capacity, and an acyclic resulting graph. It reparents the object and frees the corresponding hands. Both validate resulting ancestor loads.

`Travel(actor, destination, route)` requires an available connection, traversal requirements, and valid load. It changes the actor's place atomically; descendants' effective places change without rewriting containment. Closed bags travel without revealing contents. Free-hand requirements account for bags and held tools.

`Handoff(giver, recipient, object, receipt_id)` requires direct holding, co-location, recipient readiness/acceptance evidence, and recipient capacity. One transaction reparents the object; there is no interval with two holders. Acceptance of this receipt is not permission to borrow. Physical pickup without authorization can remain executable; policy may discourage it or attach consequences, but must not call it physically impossible. Consent, legal ownership, loan state, return discharge, and promises are never carrying effects.

**Evidence and failures.** Emit operation/event ID, participants, version, pre/post edges, affected descendants, timed paths, route/load/access reads, and receipt/motive references. Paths cite every edge, including unchanged edges and initial facts. Motive links cite the actor's recorded goal/belief, not last-writer dependencies. Reference authorization separately.

Illegal candidates yield diagnostics without fictional events. An authored attempt may record an actual effort and perceived result even with unchanged placement, but needs a new bounded event contract; current `transition` rejects no-ops. Do not add dummy flags. Preserve meaningful attempt/speech evidence through explicit retention dependencies and replay, not blanket pivotal tagging. `planning.prune_path` presently preserves pivotal scenes and state dependencies only; this extension is unresolved. Repeating Pickup while already holding is not a second transfer. Unknown route, closed access, excessive load, nonportable objects, wrong source, and cycles fail closed.

These graph predicates, events, and derived reads need extensions beyond existing scalar guards. Use typed checks, not JSON hidden in strings or setting-specific rules.

## Story 1: Library - The Book That Stayed in the Tote

**Premise and evidence.** Ada wants to finish a reserved astronomy book before closing; librarian Inez wants it ready for the next reader. Library ownership and Ada's existing loan are separate facts. Initially the book is in a closed tote on the returns table; both people are in the reading room. Ada still believes it is on her reading desk. The opening shows the packing and closure and states her mistaken expectation; the reader sees both layers without granting Ada omniscience.

**Six candidate beats.**
1. Ada picks up the tote from the table, within capacity, intending to take her other belongings to the lobby.
2. She travels to the lobby; the nested book follows, although no one observes inside the tote.
3. Ada puts the tote on the lobby bench and returns empty-handed to the reading room. The book stays on the bench through its parent path.
4. Finding the desk empty, Ada asks Inez to watch the room while she checks the tote. The request/acceptance changes their coordination, not the book's location.
5. Back in the lobby, Ada opens the tote and observes the book. Corrective evidence revises her belief; she chooses to retrieve it rather than give up the remaining reading time.
6. Ada picks up the book, travels back, and puts it on the reading desk. End with the open book under the lamp and the empty tote still on the lobby bench. Returning the loan is not claimed.

**Speech with effects.**
Ada to Inez: "Please watch my desk while I check the tote."
Inez to Ada: "Yes, I will stay here."
These create a request and scoped acceptance via peers, not an automatic fulfillment or promise.

**Interventions.** Remove the book from the tote initially: tote travel no longer delivers it to the lobby; inspection cannot discover it there. Have Ada retain the tote on her return: the book comes back inside it, removing the separate recovery trip. Both change physical history, not wording.

**QA; required visible support.**
- Q: Why did the book reach the lobby? A: "It was inside the tote Ada carried there. Moving the tote also moved the book." Show the initial containment and outward travel; cite beats 1-2 and the timed path.
- Linked follow-up, "Why didn't it come back with her?" A: "Ada left the tote on the lobby bench. She returned without it, so the book stayed inside it there." Show placement and empty-handed return; keep book/event focus across beats 2-3.
- Q: Did putting the book on the reading desk return the loan? A: "No return was completed in this story. Ada brought the book back to read it, rather than handing it over for return." Render that intent and explicitly leave the loan active; never infer discharge from library location.

## Story 2: Harbor - One Hand for the Rail

**Premise and evidence.** Mechanic Mara wants a replacement spindle at the boat before its departure slot; apprentice Jo wants to help without losing footing. The workshop owns the spindle, nested in a closed case on a bench. A signed-out tool remains a workshop asset. The visible narrow gangway requires one free hand; the loaded case needs two. Jo and Mara know this posted restriction. No failed lift is invented.

**Six candidate beats.**
1. Mara picks up the loaded case to leave the workshop; total mass is safe, but both hands are occupied.
2. At the quay, she checks the gangway restriction. Carrying the case across is unavailable; her recorded delivery goal motivates seeking an alternative.
3. Mara puts the case on a stable quay shelf and opens it. Jo requests the spindle alone; Mara accepts a direct receipt, not a loan or ownership transfer.
4. Mara picks up the spindle from the case and hands it to ready, co-located Jo. Jo's one-hand load fits; the case remains on the shelf with Mara.
5. Jo crosses the gangway with the spindle, retaining one free hand. A permitted route, not a generic "help" label, enables the movement.
6. Jo puts it on the boat's repair tray before the slot closes. End with the spindle beside the waiting mechanism and Jo's free hand on the rail; repair itself is not asserted.

**Speech with effects.**
Jo to Mara: "May I take just the spindle across?"
Mara to Jo: "Yes. Let me pass it to you."
Jo to Mara: "I'm ready."
The exchange supplies request acceptance and receipt readiness; only the later handoff changes custody.

**Interventions.** Widen the route to permit two-hand loads: Mara can deliver the case herself, eliminating the relay. Increase spindle hand demand to two while retaining the narrow route: the proposed relay cannot deliver it; an explicit postponed-delivery outcome remains possible. Permission cannot repair physical infeasibility.

**QA; required visible support.**
- Q: Why did they send the spindle without its case? A: "The loaded case needed both hands. The gangway required one hand free, so Jo took the smaller load." Show both constraints, their knowledge, and the choice; cite beats 2-5.
- Linked follow-up, "Who had it after the crossing?" A: "Jo still held the spindle after crossing. He put it on the boat's repair tray afterward." Resolve "it" to spindle, not case; show distinct crossing and placement events.
- Q: Did Jo become its owner? A: "No, the workshop still owned the spindle. Jo carried it to the boat for the delivery." State workshop ownership in the premise and preservation through handoff; do not equate custody with a loan.

## Story 3: Observatory - The Last Warm Pack

**Premise and evidence.** Nila wants to reach the dome for a brief observation window; Oren wants the frost-sensitive guide camera kept usable. One warm pack is inside a closed pouch inside Nila's closed backpack. The opening shows her packing it, the single remaining supply, and the camera's frost risk. Nila knows the supply; Oren does not. Backpack travel does not communicate its contents.

**Six candidate beats.**
1. Nila picks up the backpack and travels from stores to the stair shelter. Nested supply reaches the shelter without opening either container.
2. Oren reports a timed frost reading for the camera in that shelter. Informing delivers evidence; Nila accepts it through the peer contract, not because the fact exists globally.
3. Nila states her choice to protect the camera rather than preserve her observation slot. Her embedded Care and observation goal ground this genuine tradeoff.
4. She puts down the backpack, opens it and the pouch, and takes out the warm pack. Container access and hand capacity, not ownership, govern extraction.
5. Nila places the pack in the camera's compatible warming sleeve. A separate equipment action applies its consumable warming effect; placement alone does not prevent frost.
6. Access and warming consume the remaining window under the setting's explicit clock rules. Nila travels upstairs without the backpack; the pack remains beside the camera below. End with an empty observation chair under the closed dome slit and the camera indicator steady in the shelter. Neither missed observation nor successful care is a universal moral goal.

**Speech with effects.**
Oren to Nila: "The guide camera is at its frost threshold."
Nila to Oren: "I have the last warm pack. I'll use it here."
The first line transmits a sourced reading; the second reveals inventory and declares a choice. It is not automatically a promise.

**Interventions.** Give Nila an earlier arrival: the same rescue and route can leave time for observing, removing the sacrifice without changing physics. Remove the pack from the pouch initially while leaving her belief unchanged: opening supplies corrective evidence of absence; neither placement nor warming can occur, and the camera remains at risk.

**QA; required visible support.**
- Q: Why did Nila miss the observation? A: "She chose to spend the remaining time warming the camera. Opening the nested containers and using the pack took her past the window." Show the choice, bounded durations, and elapsed deadline; physical prerequisites alone cannot answer this motive question.
- Linked follow-up, "Where was the warm pack when she went upstairs?" A: "It was in the camera's warming sleeve in the stair shelter. Nila had taken it out of her backpack before leaving." Keep the same departure time, explicitly switching focus to the pack; cite extraction, placement, and travel.
- Q: How did Oren learn she had a pack? A: "Nila told Oren she had the last pack. Carrying the closed backpack past him had not revealed its contents." Render sourced speech and explicitly opaque containment; absence of an observation event alone is insufficient reader evidence.

## Cross-capability composition

Accept the relayed boundary: lending owns authority/consent; receipt activates its agreement through joint validation. Returning owns loan ID and scoped discharge recipient/site. Carrying supplies receipt evidence, never discharges debt merely on arrival. No automatic legacy `.owner` translation.

Observing owns timed perception; informing owns claim delivery/acceptance; discovering_mistake owns belief history/revision. Library inspection corrects false belief; travel can instead make accurate belief outdated. Requesting owns requests/acceptance; promising owns commitments; refusing owns declines. Harbor readiness is receipt-specific. Observatory equipment/time effects remain explicit domain actions, not carrying effects.

Prose/QA needs rendered path facts and dialogue, not metadata alone; unseen contents remain outside character knowledge.

## Acceptance tests

- Positive: reuse identical operations across settings; paths remain continuous through travel, placement, extraction, and handoff. Carrying never changes ownership/loan fields.
- Negative: reject remote pickup, taking through closed containers, overcapacity loads, occupied-hand crossings, cyclic containment, wrong-source pickup, and double custody. Authorization alone never enables them; unauthorized feasible pickup remains physically distinguishable.
- Evidence: timed answers cite complete paths; movement never automatically updates beliefs. Suppress offstage questions and unsupported motives. All nine QA pairs need visible support and unambiguous focus/time.
- Event/replay: planner rejection emits no attempt; duplicate pickup emits no handover. Meaningful failed attempts require explicit event support and finite bounds. Pruning must preserve necessary path reads, declared speech/choice dependencies, and replay legality without dummy flags.
- Intervention: test both changes per outline, including unreachable-success cases and explicit alternative outcomes; never silently relax constraints to recover success.
- Transfer: rename actors/props and rebind settings without operation changes. Separately test containment recovery, hand-capacity relay, and resource/time sacrifice. Noun swaps, independent reorderings, and paraphrases do not establish semantic variety.
- Compatibility: legacy Move/Transfer/Lend/Return/Tell fixtures and exports retain original interpretation; only explicitly versioned new worlds enter these tests.

## Open decisions

Smallest slice: single-actor carriage, passive containers, explicit routes, mass/hands, atomic receipts, and path evidence. Renewed approval required. Coordinator decisions: graph/derived reads; agreement/receipt atomicity; receipt/loan references; reader-support/motive links; no-physical-change event retention. Defer joint carrying, carts, coercion, vehicles, continuous travel, inferred physics, and legal responsibility after unattended placement.
