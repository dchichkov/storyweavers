# Bakery: Round 2

## Review Fixes

1. **Usable return, not empty custody.** One actual measure of oil is reserved
   for Vale's dark cellar steps. Baking can use only fuel above that reserve.
   The reservoir, spare bottle, and cumulative consumption must sum to their
   initial total after every atomic transition. With one measure the loaf never
   enters the oven; with two it may start but cannot finish. An optional refill
   from two to three measures permits finishing and still returns usable light.
   No oil is invented or free refill hidden inside another scene.
2. **One urgency rule.** An early furniture van denies additional time in both
   confession and secret-extension branches. Confession changes knowledge and
   trust, not the van's ability to wait. Vale receives checked, usable light and
   goes back to the workshop. Non-urgent extensions permit ten baking minutes;
   carrying the hot tin with towels replaces the unbounded cooling wait before
   returning his lamp. The furniture collection tonight is distinct from his
   personal departure tomorrow.
3. **Requests remain requests.** Postponement leaves `Can this loaf be saved?`
   for the absent baker. Breakfast is conditional, proposed before Vale leaves
   tomorrow, not accepted or completed. The loaf stays unfinished. The existing
   `breakfast_instead` outcome ID is retained for integration compatibility; it
   denotes the failed supper and invitation, not successful breakfast.
4. **Handoff versus settlement.** Temporary custody while helping does not set
   `loan.returned`. A separate checked-wick/oil settlement secures Vale's cellar
   light. Final cups, crown, and resting-lantern actions now have state changes.
   `lantern.holder` is custody; `lantern.resting` records the final set-down at
   Vale's place while it remains in his custody.
5. **Reference count.** The unchanged reference contains 957 prose-only words,
   or 963 with its Markdown title included. Round 1's 963 used the latter count.

## Verification

```sh
.venv/bin/python -m unittest storyscenes.mini_adventures.bakery.test_world
.venv/bin/python -m storyscenes.mini_adventures.bakery.world --seed 757654805 --scenes 8
```

Sixteen tests pass, including 200 seeds/length routes and all 144 parameter
combinations at both lengths (288 routes). Every local event is replayed and
validated. Added checks cover conserved oil, usable returns, illegal consumption
of the last measure without mutation, equal early-van refusal across choices,
temporary versus settled custody, no future baking promise, tentative breakfast,
physical final props, and both reference word-count conventions. Scene lengths
remain within 40-70 words; the exact-length bounded selector is unchanged.

`round_02_samples.md` and `.jsonl` preserve six unfiltered matched first draws:
seeds 0, 1, and 757654805 at both lengths. Read all six locally. All now postpone;
in particular seed 0 no longer escapes the early van by confession, and seed 1's
refill is insufficient to finish while preserving the cellar reserve.

`round_02_targeted.md` and `.jsonl` label two explicit parameter counterfactuals
with three measures and no early van. Read both: they show the surprise supper
and the knowingly shared supper while retaining cellar oil. These are not
first draws and are not substituted for failed matched samples.

Across seeds 0-99 at both lengths: 173 postponements, 16 surprise suppers,
11 shared suppers. Maximum search nodes: 14. This worsened success distribution
is reported, not tuned away or hidden. The meaningful physical distinction is
still served bread versus an unfinished loaf and unanswered invitations.

## Scope And Limits

Changed only the bakery pack's world, prose, tests, inventory, progress, and new
Round 2 artifacts. `reference_story.md`, `first_draws.*`, and `ROUND1_REPORT.md`
remain unchanged; the parent's frozen Round 1 files were not edited. No API
calls, commits, agents, or shared-library edits/proposals.

The six-parameter, twenty-encounter, seven/eight-scene structure is retained.
This is not a general planner or a thermal simulation. One fuel measure is a
scenario-level interval sufficient for the cellar, not a calibrated burn rate.
The owner receives usable light; actually descending the cellar is outside the
story. Deadline handling is a bounded availability rule, not a moving clock.
Walking and lifting are brief actions rather than extra ten-minute intervals.
The sampler still favors postponement and repeats a narrow authored backbone.
Optional crown changes still have limited payoff. Passing tests establishes
these constraints and replay, not literary quality or human approval.

The changes advance the embedded-state north star: the lender's need remains
attached to his actual lamp and oil, permission depends on physical urgency,
and future prose claims cannot promote an unfinished loaf into successful bread.
