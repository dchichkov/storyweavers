# Bakery: Round 1

## Deliverable

All files are inside `storyscenes/mini_adventures/bakery/`. Parent imports
`storyscenes.mini_adventures.bakery.world`. No shared source edits, API calls,
commits, or additional agents. No export implementation added.

Written in order: `reference_story.md` (963 words), `scene_inventory.json`
(object with twenty mapped encounters), then simulator/prose and focused tests.
Inventory explains reference-beat consolidation and added alternate encounters.
Seven optional scenes remain executable; short routes have no vignette, and
eight-scene routes include exactly one. This is intentional short-cut structure,
not arbitrary selection of seven paragraphs from the reference.

## Verification

Run:

```sh
.venv/bin/python -m unittest storyscenes.mini_adventures.bakery.test_world
.venv/bin/python -m storyscenes.mini_adventures.bakery.world --seed 757654805 --scenes 8
```

Eleven tests cover seeds 0-99 at both lengths (200 routes), all 144 parameter
corner combinations at both lengths (288 routes), exact replay of states/events/
prose, JSON serialization, atomic rejection, spatial continuity, ownership and
fuel, optional omission, inventory mappings, input validation, and targeted
deadline/fuel/disclosure counterfactuals. Scene prose is checked at 40-70 words.

Across the 200 seeded routes: 38 shared suppers, 27 surprise suppers, and 135
breakfast invitations. Search visited at most 14 nodes in this batch. These are
mechanical measurements, not a literary grade or semantic-diversity estimate.

`first_draws.md` and `first_draws.jsonl` save the unfiltered first draws for seeds
0, 1, and assignment seed 757654805, each at both lengths. Read all six locally;
no rejection or hand-editing of generated stories. Seed 0 confesses and shares
the work; seed 1's seven-scene version postpones, while its eight-scene version
selects a real oil refill and earns the surprise supper. Both assignment-seed
versions postpone; the eighth scene there is just the window-note vignette.

## Consequences And Outcomes

- An early van causes the same extension request to be refused. Vale takes the
  lamp home, blocking further baking and leading to the breakfast invitation.
- Empty fuel blocks finishing even with permission. A selected refill consumes
  the actual spare oil and unlocks finishing later. Without it, a failed relight
  is preserved in the committed trace; the oven is switched off, not magically
  finished offstage.
- Confession transfers knowledge and changes Nell's embedded secrecy/trust
  magnitudes. Vale can hold his own lantern while the children finish the loaf.
  An undisclosed supper instead requires borrowing permission, returning the
  lamp, and bringing Vale back for the reveal.
- Postponement ends with unbaked bread, no supper, and a delivered invitation.
  Breakfast has not occurred and is not counted as success. This differs in
  objective and physical outcome, not merely an ending adjective.

The pack moves toward the north star by binding wants/knowledge to Nell and
Vale and consequences to physical carriers: lamp fuel/custody, the loaf, crown,
cloth, and invitation. Prose is derived from committed world transitions, not
rewritten English. No engine behavior changed.

## Honest Limits

The architecture deliberately has a fixed seven-beat backbone. Twenty authored
encounters do not imply twenty independent plots. Most sampled routes postpone;
the distribution has not been tuned or filtered to look more successful.
Surprise and shared suppers differ socially and in who holds the lantern, but
both bake the same loaf. Postponement is the substantially different outcome.

Fuel and ten-minute baking intervals are symbolic. Cooling time, supper guests,
oven thermal physics, the baker's eventual return, and breakfast are not
simulated. The early van is a boolean urgency condition rather than a moving
clock; confession permits Vale to choose to stay, without simulating his later
packing logistics. Incidental gestures and dialogue are authored texture rather
than a universal action grammar. Several optional scenes are characterization
only; the darn has a guarded ending callback, the refill affects the outcome,
and inspecting the wick affects later wording. Crown inscriptions and repairs
do not yet receive equally strong ending payoffs. No human review or calibrated
quality judgment is claimed.

Shared-library proposal: none; see `LIBRARY_PROPOSALS.md`.
