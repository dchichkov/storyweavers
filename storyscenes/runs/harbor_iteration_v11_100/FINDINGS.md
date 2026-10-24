# Coupled harbor goals: good prose, limited diversity

This is a bounded, hand-authored experiment. Offline execution generates the
stories; neither judge writes or repairs them. Scores use the unchanged 0-9
rubric. Terra is gpt-5.6-terra and Luna is gpt-6-luna, both Flex with reasoning
none. All positions, including exact duplicates, are retained.

## Results

| Set | Seeds | Storytelling Terra / Luna | Diversity Terra / Luna | Exact texts | XZ bytes/story |
| --- | --- | ---: | ---: | ---: | ---: |
| v10 ten | 0-9 | 7.90 / 8.00 | 5 / 6 | 10/10 | 362.00 |
| v11 thirty | 3000-3029 | 7.90 / 7.90 | 5 / 5 | 29/30 | 189.20 |
| v11 hundred | 20000-20099 | 7.82 / 7.96 | 5 / 4 | 85/100 | 77.12 |

Both judges grade every story in the hundred at least seven for storytelling.
Terra's mean overall is 8.00; Luna's is 7.96. The hundred has 35 mechanical
signatures, but these are not 35 independently established plots. Its story-only
archive compresses 141,325 bytes to 7,712 (5.46%), using shuffled JSON strings
and XZ preset 9, exactly as in earlier trials.

All 42 paid requests returned valid results. Each judge graded 600 single-turn
QA items: Terra accepts 596 (99.3%), Luna 570 (95.0%). Mean QA overall is
8.962/8.753. These are historical v11 answers, not the revised local v13 QA.
The paired hundred-story plus QA evaluation cost an estimated $0.37902615.

For context, v9's hundred scored storytelling 7.79/7.78 and diversity 5/5;
96/100 exact texts compressed to 69.60 bytes/story. v11 changes the number of
purposes and the seed range, so this is not a matched causal comparison.
The larger archive also contains longer stories (269.04 versus 248.33 words
on average). More compressed bytes do not by themselves demonstrate a diversity
gain. The new scores do not establish such a gain either.

## What Actually Interacts

Ari wants a chart hanging in the window. Cy wants to sail. Bo needs rope and
tools to lift the launch tub's cover before the ferry bell. The same rope is
borrowed for the chart, removing weight from the tool case so Cy can carry it,
but temporarily denying Bo a launch resource.

The physical and social consequences are executed, not merely claimed in prose:

- Without removing the rope, Cy cannot lift the full case.
- A carried coil cannot stand in for a rope already hung at the window.
- Without the rope at the jetty, Bo cannot open the tub.
- Prioritizing the return can shorten the display and permit an actual launch.
- Prioritizing a long display can cost the launch. The late return settles the
  loan but leaves the timing promise breached, with a repair receipt.
- Declining the loan leaves the rope available and puts the chart flat instead.

The last-launch rule is not weakened to produce a happy ending. Replays include
JSON serialization/deserialization, not just replay of an in-memory object.
These changes move toward physical-carrier-driven narrative composition. They
do not implement general autonomous character planning or prove English entailment.

## The Remaining Ceiling

The new branch accounts for most of the hundred's exact repeats:

| Purpose | Positions | Exact texts |
| --- | ---: | ---: |
| Measuring stick | 20 | 20 |
| Carrying | 20 | 19 |
| Boat loan | 20 | 20 |
| Parcel | 20 | 18 |
| Shared rope | 20 | 8 |

The [bounded space audit](../harbor_iteration_campaign/shared_rope_space_v11.json)
executes all 72 combinations of display duration, deadline, return priority,
direct-path availability and caution, holding other conditions at defaults.
Every conditional renderer-choice leaf is enumerated. It finds 21 action paths,
four outcomes, and only 16 exact texts. This is not an audit of the entire harbor
generator. Action-path differences can still be incidental clock/route differences.

The random hundred contains sixteen complete displays, three declined rope
loans and one shortened display. It contains no late-rope return. That branch
is counterfactually tested but cannot inherit a sampled judge grade. No samples
were replaced to make the distribution look more varied.

The useful conclusion is narrower than "composition solved diversity": sharing
a resource gives the story a genuine dependency, but one authored solution
policy plus a small set of paragraphs still collapses. Another whole-plot
renderer or more synonyms would not demonstrate a general solution.

## Prose And QA Review

Scene-sized realization supplies an opening desire, enacted turn, dialogue and
ending image. The best moments follow physical consequences, such as a chart
losing its rope so a boat can gain water. Administrative loan and promise
records stay in the trace rather than becoming paragraphs of event-log prose.
This requires substantial author work; API judging cost is not the total cost
of producing these generators.

The unjudged v10 thirty is preserved. Manual reading caught an implied second
promise and a red sail not declared in this branch's world. v11 corrects both.
Only harbor:3019's text changes; all thirty trace hashes match. All ten earlier
texts remain unchanged.

The thirty-story QA review found a real visibility issue: harbor:3001's story
does not name the workshop, while two answers do. Current v12 removes that
extra starting place, answers the route question with the visible short path,
and clarifies that taking the boat off display starts a return rather than
completing a handover. Its local hundred has identical stories and trace hashes
to v11; 39 QA sets change. No new paid QA grades are claimed for those answers.
v13 additionally corrects a real presupposition: after a declined rope offer,
"Did lending the rope change who owned it?" still suggests an actual loan.
The new question asks who owned the rope Bo offered to lend; its answer does not
presuppose acceptance or require a return after a refusal. All stories/traces
still match, and 59 QA sets now differ from v11. This is not a new scored batch.

Do not treat every judge rejection as truth. In the thirty, Luna rejects
harbor:3001's opening of the tub because the story says Bo lifted its cover;
rejects harbor:3012's handover into ready hands even though the story explicitly
has Ari wait until Cy is ready; and places the tub at the quay in harbor:3019
despite the story locating it at the jetty. These are false rejections.
Conversely, "directly to Cy" can be read as a direct route and is worth clarifying
when the actual return requires a search. Preserve both the grades and this
independent reading; do not silently relabel the scored results.

## Reproduction And Budget

This directory preserves sources, all 100 serialized worlds, traces, exact
statements/spans, unfiltered samples, judge requests and raw responses.
`report.md` and `comparison.json` record final QA coverage and returned cost.
The cap remains the original shared $5, including earlier retained reservations.
At completion, combined commitment is $4.29763575, leaving $0.70236425.
Returned-usage estimates total $2.69649375; prior retained reservations account
for $1.601142. All new requests have settled; no paid process remains active.

Initially, large concurrent reservations caused 36 local budget rejections.
These jobs had neither request nor response artifacts and were not dispatched.
Their `*.not_dispatched.json` files and the initial partial report are retained.
Sequential first dispatch reuses the six already returned responses; it does
not retry uncertain paid requests or release old reservations.

The current local suite passes 471 tests. Current QA-only corrections are frozen
in `../harbor_iteration_v13_100_qa_local/`; use this directory's frozen runtime
to reproduce the historically judged v11 inputs.

## Next Hypothesis

Keep world execution and literary realization separate. Test reusable goal
components whose actions change another component's actual prerequisites,
including failed plans and revisions of intent. Select narrative scenes around
those causal changes rather than around every legal operation. Continue to
require a physical ending and reader-answerable QA.

The next success criterion is a measurable increase in distinct causal stories
on fresh thirty- and hundred-position sets while storytelling remains above
seven. Do not claim success from more parameter bits, a larger archive, a
renamed purpose, or higher exact-text uniqueness alone. The current evidence
supports good authored prose over simulation, not a large training-data
multiplier from each script.
