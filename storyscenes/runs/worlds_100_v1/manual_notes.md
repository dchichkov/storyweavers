# Manual observations during the frozen run

Read complete first selected stories and the first two conversations for these initial examples:

- `library_parade_001:1029`: clear wish, cart repair/loan/delivery and warm ending; charming librarian/runaway-pudding line. Prose explicitly leaves the cart on loan, so QA correctly does too. The ownership follow-up Why answers with old delivery prerequisites, an unhelpful explanation of present possession.
- `clocktower_club_001:1029`: visible-signal requirement is poorly resolved by a no-bell/no-lantern plan; approval prose asserts they showed the important part without a convincing demonstration. Literal state text: “The tower’s signal changed from none to approved.” Invitation transfer is narrated twice. Dialogue QA skips explicit intervening lines while calling the next indexed utterance “next”; its claim that Mara did not yet know the weather is a hidden-state assertion.

No engine, prose, or QA rules changed in response to these observations.

- `roof_post_001:1029`: tail/wings give a pleasing physical solution, but observation and Tell repeat the weather sentence. Pip hands the bundle to Mina, then Ada hands it to Mina again. The ending is strong. QA “What happened next?” reduces the story to “Pip was ready,” losing the physical action.
- `pond_concert_001:1029`: lively musical imagery and a developed correction of an assumption. However “discovered the copied fact” exposes mechanics; Ada learns Mira wants dancing then practices for her quiet wish, without explaining the old belief until later. Invitation delivery is doubled. The ending is warmer than the intermediate state narration.
- `night_garden_001:1029`: clear welcome arc and effective final image, but “belonged to Bo for the loan” conflates custody and ownership in prose. Moth discovers its own wish as an external fact; the QA repeats “Moth” four times and says it previously did not know its own desire. This is a limitation of generic knowledge composition, visible in both trace and text.

- `hill_picnic_001:1029`: warm, physically plausible carrying problem with a clear sheltered-grove ending. It oddly leaves the children uphill watching leaves rather than participating; the story supplies no reason June cannot climb. QA adds Bo’s exact hilltop location, which is not clearly established for that observation.
- `puppet_weather_001:1029`: appealing timid-performer arc and curiosity ending, but no actual puzzle/question is supplied. “The still air offered no argument” contradicts the breeze motivating the banner fix. QA’s location/holder/location chain is grounded but repetitive.
- `kite_workshop_001:1029`: rich physical constraints (frayed ribbon, one last thread) and lovely quiet-postdragon idea, undermined by repeated raw “nearby fact”/“observed fact” language. Return-to-workshop paragraph says still air after explicitly observing breezy weather. A flight occurs before fastening the note, then the note is described as staying in the workshop. The final image claims a ribbon “fluttered proudly in memory,” less concrete than it sounds.
- `museum_of_small_things_001:1029`: story begins by certifying returns before any loans, then borrows and displays the same objects. At the end it returns both objects to owners but leaves them physically on display in the final image. This exposes return-state prerequisites and owner/location consistency, beyond surface prose. Good local imagery cannot repair that causal sequence.

- `bakery_exchange_002:1029`: strong playful label-repair setup; a nut tart is given to Nia, but the payment paragraph suddenly says “After receiving the honey bun.” The other branch’s pastry leaked into a shared card. Nia pays Ada while Pip supplies the tart, with no explanation of who benefits from this supposedly fair exchange. QA’s “wanted crunchy” and “at Nia” expose enum/grammar roughness; knowledge follow-ups merely repeat the same observation.

This completes a first-story-per-theme reading (ten independently authored worlds), with the first one or two conversations spot-checked per story; it is not a claim that every exchange in the review artifact was manually checked.

## Additional low-QA-score checks during the batch

Read the complete stories and flagged conversations for `roof_post_003:1029/c001` and `roof_post_003:1047/c002` (both graded 0 overall). These are real failures: QA asks about Red Ribbon on a basket route and Willow Basket on a simple hand-carry route, although those props never appear in the respective stories. The follow-up jumps from an irrelevant prop to invitation movement and reports stale possession, while the narrated recipient holds the invitation. This demonstrates `offstage_entity_question` and `followup_lost_context` alongside custody/location drift. QA must follow what the executed prose actually supports, not every entity available in the world definition. Raw judge grades are retained.

## Additional low-story-score checks near completion

Read these three complete stories after sorting by overall score, taking distinct worlds:

- `bakery_exchange_014:1047` (4/9): the Neighbor requests savory food and accepts a savory tart, but the payment and closing paragraphs switch to a sweet pie and leave the supposedly accepted tart on the stall. A clear, material branch mismatch, consistent with the judge’s low score.
- `bakery_exchange_011:1047` (5/9): a correctly labeled sweet bun is ceremonially “corrected,” then eaten, then said to remain on the counter. Pip also pays after another character consumes the bun he wished to trade for. Warm sentences cannot make the exchange coherent.
- `bakery_exchange_017:1029` (5/9): filling inspection and the label consistently establish berry, then the apple exchange and ending change the same bun to nut. The final grounded-state-to-prose contract remains too weak.

These late samples reinforce the initial `branch_fact_leak` and temporal-state findings rather than suggesting a new isolated defect. No scores or generators were changed after this review.

## Final recovered grade and last world

Read the first selected story in each of these worlds, plus all three judge notes:

- `museum_of_small_things_006:1029` (4/9, recovered after HTTP 429): the feather is narrated as returned before the loan, and the final image still groups the returned feather/button with the museum display. This is a real instance of the same return-order/location defects, not a suspicious recovery grade. The other two museum samples received 5/9.
- `hill_picnic_019:1029` (7/9): a clear, warm plan to bring the picnic to someone who cannot climb. The delivery takes several very short procedural paragraphs and repeats loading/delivery, but the final image resolves the initial difficulty. The other two samples received 6/9; none was replaced because of those grades.
