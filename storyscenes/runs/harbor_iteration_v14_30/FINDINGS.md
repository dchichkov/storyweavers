# Alternatives improve the stories, not the scaling result

Checkpoint: 2026-10-23. Same paired Terra/Luna Flex judges, unchanged 0-9
literary and QA rubrics. No paid requests remain active at this checkpoint.

## What changed

The shared-rope scenario now has three additional enacted responses to a
resource conflict, using the existing physical and social laws:

- A spring clip holds the chart while the rope goes to the launch tub.
- Ari moves the display onto the jetty board; time spent carrying the chart
  does not count toward its planned hanging time.
- Cy chooses the workshop basin, and Bo explicitly releases the deadline
  before it expires. The loan still requires an actual return.

Resource removal changes the executed result. A clip cannot lift the tub cover;
a closed board cannot hold the chart; an unavailable basin prevents that
alternative; a late release cannot retroactively erase a missed deadline.
This advances state-driven narration over physical carriers. It remains an
authored priority policy, not general autonomous planning or learned prose.

## Paid results

| Preserved batch | Seeds | Storytelling Terra / Luna | Overall Terra / Luna | Diversity Terra / Luna | Estimated USD |
| --- | --- | ---: | ---: | ---: | ---: |
| v14_10 | 4000-4009 | 7.500 / 7.500 | 8.000 / 7.800 | 5 / 5 | 0.04148005 |
| v14_30 | 5000-5029 | 7.867 / 7.900 | 8.100 / 7.967 | 5 / 4 | 0.11813005 |

All forty story positions received valid ratings from both judges, with no
storytelling score below seven. All 20 paid calls returned valid assessments.
Ten-story QA: 59/59 usable for each judge, overall 8.966/8.932. Thirty-story QA:
178/179 Terra, 168/179 Luna, overall 8.961/8.832. These are judge decisions,
not verified correctness labels. The sampling protocol uses up to six uniformly
selected single-turn questions per story; a declined loan can supply only five.

The ten includes clip and board outcomes. The thirty includes four clip
outcomes and one negotiated basin outcome, but no board outcome. No samples
were replaced to improve coverage. Both judges recognize consequential choices
and concrete closing images, but penalize recurring errands, harbor launches
and repeated wording. Plot groups are 5/8 in ten and 13/19 in thirty; the
different grouping granularities are not calibrated counts of unique plots.

The new sampler also puts more pressure on shared-rope scheduling: display
duration is sampled from 3/5 and deadline from 4/6. Earlier versions used a
different distribution. Fresh seeds and changed mechanics mean this is not a
matched causal estimate of the improvement over v11.

## Local hundred and finite audit

The separate, unjudged `../harbor_iteration_v14_100_local/` uses seeds
30000-30099. All 100 serialize and replay exactly; 92 exact texts and 37
mechanical plot signatures are not evidence of 92 distinct narratives.
The twenty shared-rope positions contain 14 exact texts and six outcomes.

Story-only XZ: 144,050 -> 8,316 bytes, 5.773%, or 83.16 bytes/story.
Using nested prefixes of this SAME hundred, shuffled with seed 777:

| Prefix | Exact texts | Raw bytes | XZ bytes | XZ bytes/story |
| --- | ---: | ---: | ---: | ---: |
| 10 | 10 | 14,103 | 3,840 | 384.00 |
| 30 | 30 | 43,899 | 6,348 | 211.60 |
| 100 | 92 | 144,050 | 8,316 | 83.16 |

Of 743 paragraph positions, only 134 are exact distinct paragraphs. Counting
each paragraph once removes 22,483 of 27,383 whitespace-delimited word positions
(82.1%). This is a literal repetition diagnostic, not a semantic score or a
suggestion that sentence shuffling creates new stories.

`../harbor_iteration_campaign/shared_rope_space_v14.json` exhausts all 1,152
configurations in nine declared axes and every local renderer choice. Result:
**28 exact texts, 36 action paths, seven outcomes**. Other conditions are held
at defaults; this is not the full harbor generator. The prior five-axis branch
audit found 16 texts. Adding these alternatives expanded a small finite menu;
it did not establish a large diversity multiplier.

## Manual checks and corrections

- Read all ten stories, all six shared-rope stories in the thirty, and one
  example of every shared-rope outcome present in the local hundred, with QA.
- The board scene has an ambiguous pronoun: after attaching the chart, Bo
  "accepted it" actually means the rope. Current prose names the rope.
  `../harbor_iteration_v15_100_local/` preserves the matched rerun: only
  harbor:30044 changes text; all 100 traces and QA sets are unchanged. No new
  paid scores are claimed for this correction.
- Terra rejects harbor:5021/c000 for saying the case reached the jetty before
  Cy collected the rope, although that is the narrated two-trip sequence.
- Luna rejects harbor:5011/c002 for assigning the rope to Cy, although the
  actual answer says "Bo delivered the rope". It also rejects harbor:5027/c004
  for mentioning Ari's workshop visit, which the preceding paragraph states.
  Do not distort the prose to accommodate these false rejections or overwrite
  their saved grades. Neither judge is ground truth.
- Full regression after the pronoun correction: **477 StoryScenes tests pass**.
  The 32-configuration alternative matrix checks serialized exact replay,
  physical preconditions, QA anchors and spans. Paragraph provenance remains
  a support declaration, not an English entailment proof.

## Budget and interpretation

These two evaluations cost an estimated **$0.15961010**, based on returned usage.
Across the original comparisons and this campaign, priced usage is $2.85610385
and retained unpriced reservations are $1.60114200: **$4.45724585 committed**
against the existing $5 cap, leaving **$0.54275415**. No unknown reservations
were released. Estimates are not invoice reconciliation or coding-agent costs.

The new hundred is local-only. Its whole-set story request alone requires a
$0.639245 conservative reservation, exceeding the remaining headroom. Do not
weaken the cap or quietly replace the established protocol to dispatch it.
The earlier hundred-per-script and pooled results remain preserved separately.

Scene-level writing can produce readable stories under these laws. The next
useful experiment is not another synonym bank or fourth hard-coded rescue:
factor substitution, relocation and renegotiation into reusable goal components,
then test held-out combinations with narrative plans derived from the resulting
causal trace. Require new dependency structures and changing outcomes under
resource-removal tests; reject disconnected episode concatenation. Until that
works, treat these as a small set of canonical stories, not a training-data
multiplier. The diversity goal is still open.
