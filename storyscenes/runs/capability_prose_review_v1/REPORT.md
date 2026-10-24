# Capability prose: local matched review

No new judge scores. No API calls. Historical scores apply only to historical texts.

Same-path comparisons keep the exact original simulation; fresh runs use the same selected seeds with narrative prerequisites.
These are 30 previously successful, judge-selected positions, not an unbiased yield benchmark.

| World | Old words | New words | Old paragraphs | New paragraphs | Fresh returns |
| --- | ---: | ---: | ---: | ---: | ---: |
| harbor | 269.0 | 166.0 | 25.0 | 9.2 | 10/10 |
| library | 473.0 | 243.5 | 52.5 | 15.0 | 10/10 |
| observatory | 155.2 | 109.0 | 12.3 | 7.4 | 10/10 |

All 30 old trace hashes and diagnostic texts reproduced exactly; historical files were not changed.

QA is regenerated from visible retained statements, so omission reduces question coverage as well as prose.
Compaction is not evidence of better diversity, motivation or literary quality.

## harbor:19248: new rendering, original path

Ari, Bo and Cy were at the workshop. Ari inspected the tide gauge. The tide gauge was at the workshop at time 0.

Ari sent Cy this report: "The tide gauge was at the workshop at time 0."

Bo closed the instrument case. Bo picked up the instrument case from the workshop. Bo carried the instrument case from the workshop to the jetty.

Bo set the instrument case down at the jetty.

At time 2, Cy received Ari's report. The report described time 0, not its arrival at time 2. It did not establish the current location.

Ari went from the workshop to the jetty. Ari opened the instrument case.

Ari inspected the tide gauge. The tide gauge was at the jetty at time 2.

Ari had believed that the tide gauge was at the workshop at time 2. Now Ari accepted that the tide gauge was at the jetty at time 2.

Cy accepted that the tide gauge was at the workshop at time 0.

### Fresh constrained path

Ari, Bo and Cy were at the workshop. Ari inspected the tide gauge. The tide gauge was at the workshop at time 0.

Ari sent Cy this report: "The tide gauge was at the workshop at time 0."

Bo closed the instrument case. Bo picked up the instrument case from the workshop. Bo carried the instrument case from the workshop to the jetty.

Bo set the instrument case down at the jetty.

At time 2, Cy received Ari's report. The report described time 0, not its arrival at time 2. It did not establish the current location.

Ari went from the workshop to the jetty. Ari opened the instrument case.

Ari inspected the tide gauge. The tide gauge was at the jetty at time 2.

Ari had believed that the tide gauge was at the workshop at time 2. Now Ari accepted that the tide gauge was at the jetty at time 2.

Cy accepted that the tide gauge was at the workshop at time 0.

## library:19245: new rendering, original path

Inez, Nia and Sol were at the reading room. Inez offered Nia a loan of the atlas. "It must come back to the return cabinet," Inez said.

"Will you return the atlas to the return cabinet?" Inez asked Nia.

"I'll bring the atlas back to the return cabinet," Nia agreed.

Nia collected the atlas. The loan had now begun. Inez still owned the atlas.

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

Inez, Nia and Sol were at the reading room. Inez offered Nia a loan of the atlas. "It must come back to the return cabinet," Inez said.

"Will you return the atlas to the return cabinet?" Inez asked Nia.

"I'll bring the atlas back to the return cabinet," Nia agreed.

Nia collected the atlas. The loan had now begun. Inez still owned the atlas.

"I will return the atlas to the return cabinet," Nia told Inez.

"I promise to return the atlas to the return cabinet by time 5," Nia told Inez.

Nia put the atlas in the carrying bag. Nia picked up the carrying bag from the reading room. Nia carried the carrying bag from the reading room to the courtyard.

Nia set the carrying bag down at the courtyard. Nia remained responsible for returning the atlas. Nia picked up the carrying bag from the courtyard. Nia carried the carrying bag from the courtyard to the reading room.

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

The star chart was at the observatory dome.

### Fresh constrained path

Noor and Vale were at the observatory dome. "Will you hand the star chart to me?" Vale asked Noor.

"I will hand the star chart to you," Noor told Vale.

"I promise to hand the star chart to you before time 8," Noor told Vale.

At time 8, Noor handed the star chart to Vale.

Noor had missed the deadline: the promise was to hand the star chart to Vale before time 8.

"Will you hand the calibration card to me?" Vale asked Noor.

"No, I won't hand the calibration card to you," Noor told Vale. "I want to finish my own observation before taking another job," Noor explained.

The star chart was at the observatory dome.
