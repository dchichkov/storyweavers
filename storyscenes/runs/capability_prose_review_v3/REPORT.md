# Capability prose: local matched review

No new judge scores. No API calls. Historical scores apply only to historical texts.

Same-path comparisons keep the exact original simulation; fresh runs use the same selected seeds with narrative prerequisites.
These are 30 previously successful, judge-selected positions, not an unbiased yield benchmark.

| World | Old words | New words | Old paragraphs | New paragraphs | Fresh returns |
| --- | ---: | ---: | ---: | ---: | ---: |
| harbor | 269.0 | 164.0 | 25.0 | 10.2 | 5/10 |
| library | 473.0 | 240.5 | 52.5 | 15.7 | 10/10 |
| observatory | 155.2 | 106.3 | 12.3 | 7.4 | 10/10 |

All 30 old trace hashes and diagnostic texts reproduced exactly; historical files were not changed.

QA is regenerated from visible retained statements, so omission reduces question coverage as well as prose.
Compaction is not evidence of better diversity, motivation or literary quality.

## Independent seed smoke

Seeds 44000 through 44019; 2 CPU seconds, 6 wall seconds, 6,000 nodes per position.
These are three fixed profiles, not a representative world population or a diversity benchmark.
- harbor: 6/20 returned and replayed.
- library: 20/20 returned and replayed.
- observatory: 20/20 returned and replayed.

## harbor:19248: new rendering, original path

Ari, Bo and Cy were at the workshop. Ari inspected the tide gauge. The tide gauge was at the workshop at time 0.

Ari sent Cy this report: "The tide gauge was at the workshop at time 0."

Bo closed the instrument case. Bo picked up the instrument case from the workshop. Bo carried the instrument case from the workshop to the jetty.

Bo set the instrument case down at the jetty.

At time 2, Cy received Ari's report. The report described time 0, not its arrival at time 2. It did not establish the current location.

Ari went from the workshop to the jetty. Ari opened the instrument case.

Ari inspected the tide gauge. The tide gauge was at the jetty at time 2.

Ari had believed that the tide gauge was at the workshop at time 2. Now Ari accepted that the tide gauge was at the jetty at time 2.

Cy believed Ari's report.

The instrument case was at the jetty.

### Fresh constrained path

Per-seed CPU time limit exceeded

## library:19245: new rendering, original path

Inez, Nia and Sol were at the reading room. Inez offered Nia a loan of the atlas. "It must come back to the return cabinet," Inez said.

"Will you return the atlas to the return cabinet?" Inez asked Nia.

"I'll bring the atlas back to the return cabinet," Nia agreed.

Nia collected the atlas on loan. Inez still owned the atlas.

Nia put the atlas in the carrying bag.

"I will return the atlas to the return cabinet," Nia told Inez.

"I promise to return the atlas to the return cabinet by time 5," Nia told Inez.

"Can you accept the atlas as my return?" Nia asked Sol. This was the first return offer for this loan.

Nia picked up the carrying bag from the reading room.

"No," Sol answered the first return offer. "I am not authorized to settle this loan," Sol explained.

Nia carried the carrying bag from the reading room to the courtyard. Nia set the carrying bag down at the courtyard. Nia remained responsible for returning the atlas.

Inez authorized Nia to return the atlas to the return cabinet.

Nia picked up the carrying bag from the courtyard. Nia carried the carrying bag from the courtyard to the reading room.

Nia returned the atlas to the return cabinet. The latch clicked shut. That authorized return settled Nia's first loan of the atlas.

Nia had kept the promise to return the atlas to the return cabinet by time 5.

The atlas was inside the return cabinet at the reading room.

### Fresh constrained path

Inez, Nia and Sol were at the reading room. "Will you inspect the stone marker?" Inez asked Nia. "Use the atlas to read the marker in the courtyard," Inez explained.

"I will inspect the stone marker," Nia told Inez.

Inez offered Nia a loan of the atlas. "It must come back to the return cabinet," Inez said.

"I'll bring the atlas back to the return cabinet," Nia agreed.

Nia collected the atlas on loan. Inez still owned the atlas.

"I promise to return the atlas to the return cabinet by time 5," Nia told Inez.

Nia put the atlas in the carrying bag. Nia picked up the carrying bag from the reading room. Nia carried the carrying bag from the reading room to the courtyard.

Nia set the carrying bag down at the courtyard. Nia remained responsible for returning the atlas.

Using the atlas, Nia inspected the stone marker. The stone marker named the walled garden as its destination.

Nia picked up the carrying bag from the courtyard. Nia carried the carrying bag from the courtyard to the reading room.

"The stone marker named the walled garden as its destination," Nia told Inez.

Inez heard Nia's report and believed it.

"Can you accept the atlas as my return?" Nia asked Sol. This was the first return offer for this loan.

"No," Sol answered the first return offer. "I am not authorized to settle this loan," Sol explained.

Inez authorized Nia to return the atlas to the return cabinet.

Nia returned the atlas to the return cabinet. The latch clicked shut. That authorized return settled Nia's first loan of the atlas.

Nia had kept the promise to return the atlas to the return cabinet by time 5.

The atlas was inside the return cabinet at the reading room.

## observatory:19287: new rendering, original path

Noor and Vale were at the observatory dome. "Will you hand the star chart to me?" Vale asked Noor.

"I will hand the star chart to you," Noor told Vale.

Noor handed the star chart to Vale.

"I promise to hand the star chart to you before time 8," Noor told Vale.

"Will you hand the calibration card to me?" Vale asked Noor.

Noor had missed the deadline: the promise was to hand the star chart to Vale before time 8.

"No, I won't hand the calibration card to you," Noor told Vale. "I want to finish my own observation before taking another job," Noor explained.

Vale held the star chart.

### Fresh constrained path

Noor and Vale were at the observatory dome. "Will you hand the star chart to me?" Vale asked Noor.

"I will hand the star chart to you," Noor told Vale.

"I promise to hand the star chart to you before time 8," Noor told Vale. "I want to check my calibration reading first," Noor explained.

The clock reached 8. "The calibration reading is due at time 8," Noor explained.

Noor inspected the calibration card. The calibration card's reading was ready at time 8.

At time 8, Noor handed the star chart to Vale.

Noor had missed the deadline: the promise was to hand the star chart to Vale before time 8.

"Will you hand the calibration card to me?" Vale asked Noor.

"No, I won't hand the calibration card to you," Noor told Vale. "I want to finish my own observation before taking another job," Noor explained.

Vale held the star chart.
