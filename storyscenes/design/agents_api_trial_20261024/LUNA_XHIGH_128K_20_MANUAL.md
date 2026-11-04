# Manual Reading Notes

Completed reading of all seven available successful-pack samples. No repairs
or selection changes are applied.
Read the reproducibly selected successful story per available pack; selections
are conditional on runtime success and are distinct from the ten-story judge.
No successful sample exists for packs with zero runnable positions.

| Pack | Observations from the selected story |
| --- | --- |
| Music | A complete, gentle listening-not-playing resolution, but literal `{child}` leaks into the opening. Pronouns are sometimes ambiguous between Mara and June. Repeated permission/consent dialogue makes the scene feel instructional. |
| Festival | The invitation, reachable task and completed shared welcome form a clear arc in the surviving sample. The 55-centimetre bunting line in a public square needs a spatial explanation so it is not simply a trip obstacle. Only 3/100 positions run, so this is a heavily selected survivor. |
| Trail | A coherent accommodation-and-discovery arc; the missed pool ends with a shared frog drawing rather than an empty promise. The story's claim that a brook landmark corrects a wandering compass needs a clearer physical explanation. The two failing positions are strict 72-word scene assertions, not broken route logic. |
| Greenhouse | Premise, concrete watering and a fallback salvage ending are present. Ownership reminders read like bookkeeping. The final cutting rescue is asserted immediately rather than demonstrating later survival; the label/rubber-band detour has little payoff in this selected path. |
| Market | Stronger consequential choice: Nella knowingly conceals a faulty reading, loses the sale, refunds payment and restores the scale's usefulness. This is a real causal/emotional branch, not a synonym change. The ending drifts from a clinic tart to dinner plans; the basket is called full-looking despite the preceding explicit shortage. |
| Repair | The wrong diagnosis, missing spacer and refusal of an unsafe improvised fix give a clear causal turn. However, the fallback scene already delivers every pot and creates a warning; the next scene narrates carrying the pots and writing the warning again. The closing repeats these completions rather than adding much. |
| Library | The one fully mechanically passing pack still has a causal gap in its selected story: an explicitly current catalogue reveals the actual location, but the children search the window seat and trolley and then give up without explaining why the known shelf was not searched. The honest disappointment ending is readable, yet the planner's successful replay does not make that choice convincing. |

Early failure classes from saved checker reports (not repaired): pottery's
gift/ending invariant fires during an intermediate action; orchard's borrowed
basket/location invariant fires; costume has route exhaustion and a no-op
agreement action; festival has a display/layout invariant. These are distinct
from API failure, reference-length compliance and prose-length assertions.

Further raw checker classes: seaside reads missing key `party.shared_pause`;
puppets, picnic, pond, laundry and biscuit reject intermediate preparation or
resolution states; museum cannot find complete routes. These are candidates
for subsequent bounded repair, but no fixes are included in this baseline.

Camp rejects the borrowing promise state. Snow does not reach runtime sampling:
its scene inventory is invalid JSON. Bakery returns HTTP 500, so no story or
token usage is available. These should not be conflated with generated-code
runtime failures.

All five packs eligible for the standard judge were reviewed manually here;
trail and festival were also read as explicitly conditional survivors. The
other eleven executed packs have no successful sampled stories to read.
