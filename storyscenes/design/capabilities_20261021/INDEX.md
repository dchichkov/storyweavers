# The 27 story outlines

Nine capability proposals, each with a library, harbor, and observatory story.
These are outlines and illustrative QA, not generated final prose or graded
training samples. Read [the shared decisions](DECISIONS.md) alongside the original
proposals: cross-review found corrections that are retained as explicit overrides.

| Capability / proposal | Neighborhood library | Harbor workshop | Mountain observatory |
| --- | --- | --- | --- |
| [carrying](proposals/carrying.md) | The Book That Stayed in the Tote | One Hand for the Rail | The Last Warm Pack |
| [lending](proposals/lending.md) | The Lamp Before Four | The Dry-Bench Loan | The Detector That Stayed Upstairs |
| [returning](proposals/returning.md) | The Right Pair of Hands | The Gauge That Stayed Aboard | A Place for the Star Plate |
| [observing](proposals/observing.md) | The Book Behind the Apron | A Glint Before the Tide | The Reading from Six O'Clock |
| [informing](proposals/informing.md) | The Atlas Behind the Desk | The Clearance That Arrived Late | One Glimmer, Two Voices |
| [discovering mistake](proposals/discovering_mistake.md) | The Wrong Wednesday | The Motor That Was Turning | Yesterday's Bright Point |
| [requesting](proposals/requesting.md) | The Card Before the Cart | Accepted at the Workshop Door | The Blank in the Transit Log |
| [promising](proposals/promising.md) | One More Chapter | The Latch After the Bell | Two Promises, One Cell |
| [refusing](proposals/refusing.md) | A Place Away from the Microphone | The Gauge That Stayed Ashore | The Frame That Never Arrived |

## What is in each proposal

- One reusable contract, with existing behavior distinguished from new semantics.
- Three premises, event outlines, consequential choices and ending images.
- Dialogue that changes requests, information or commitments.
- Two interventions per story: 54 proposed changed-condition cases in total.
- Three QA pairs per story: 81 illustrative pairs with required reader evidence.
- Cross-capability dependencies and proposed acceptance tests.

These counts describe design examples, not executed test cases or quality scores.
The coordinator read all nine proposals. Peer cross-review is preserved separately
in [physical](reviews/physical.md), [epistemic](reviews/epistemic.md), and
[social](reviews/social.md) reviews. An author reviewed neighboring capabilities;
these are not independent blind evaluations.

## Particularly useful design examples

- **The Book That Stayed in the Tote:** moving a container moves its contents,
  without updating everyone's beliefs or discharging a loan.
- **The Detector That Stayed Upstairs:** accepting loan terms without ever
  collecting the equipment creates no completed handover or return debt.
- **One Glimmer, Two Voices:** two messages about one sighting are not independent
  corroboration. Keeping a claim unconfirmed is a legitimate ending.
- **The Motor That Was Turning:** disproving one diagnosis does not identify the
  actual fault or repair it. Apply the failed-inspection correction in D06.
- **Two Promises, One Cell:** two individually feasible commitments can conflict;
  fulfilling one does not erase the other.
- **The Gauge That Stayed Ashore:** lack of lending authority differs from
  physical inability and unwillingness; a substitute service has its own cost.

Start with [the synthesis](SYNTHESIS.md) for the recommended implementation slices
and remaining approval boundary. [Integration gates](INTEGRATION_GATES.md) test
interactions between capability groups rather than only these authored plots.

