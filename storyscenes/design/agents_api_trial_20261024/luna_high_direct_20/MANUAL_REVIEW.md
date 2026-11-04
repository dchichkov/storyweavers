# Direct Prose: Manual Reading and Judge Audit

All twenty untouched stories were read, not just the best outputs. No stories
were rewritten, excluded for quality, or sent for an unrequested second judge.

## Results

20/20 completed and judged. Mean length 764.1 words; range 684-852. Ten meet the
narrow 750-850 guidance, nine are shorter, one is two words longer. The user asked
for approximately 800 words, so this is a mild compliance issue, not twenty
failed stories. Thirteen include all three seed words literally; seven express
some seeds conceptually without using the exact word. All twenty texts differ.

Terra returned **9/9 overall, coherence, storytelling, and grammar for every
single story**. Style averages 8.25. Cross-scenario diversity is 8/9, language
diversity 7/9, with nineteen causal plot groups. This is an observed ceiling
effect: the judge fails to discriminate clear continuity defects in this batch.

Previous pack outputs averaged quality 7.8/9, conditional on the five fully
runnable packs. All five corresponding direct stories receive 9, but these are
single longer first drafts rather than ten shorter variants per executable
pack. No controlled causal claim about high versus xhigh or engine architecture
is warranted. Cross-premise diversity cannot be compared to the packs' 2.4/9
within-pack diversity.

## What Improved

The prose is substantially smoother than the pack samples: full conversations,
continuous action, individual wants, and enough space for a decision to matter.
Music, costume, puppets, and festival are useful starting references. Music lets
the newcomer choose an off-program duet rather than forcing participation;
costume gives the protagonist a meaningful sacrifice; festival actually discovers
and fixes the blocked entrance created by low bunting. These are stories rather
than event logs.

The batch still leans on a recurring borrowed-object/problem/careful-choice/
adult-approval structure inherited partly from the supplied premises. Names,
clock-time openings, sensory introductions, and glowing or trembling final
images repeat. Nineteen judge plot groups should not be interpreted as nineteen
wholly independent narrative structures.

## Missed Defects

| Story | Concrete issue | Judge response |
| --- | --- | --- |
| Library | Jun picks his star bookmark off the floor; the same bookmark then protrudes from the missing book and is described as still inside where he left it. He supposedly placed the book on a high shelf because he could not reach the picture-book shelf. Giving up the atlas is not causally necessary to request the ladder. | Coherence 9; praises the bookmark as confirmation. |
| Picnic | The sign is abandoned in reeds beside the river, and the arriving cousin explicitly praises not going after it. The ending suddenly has the sign tucked inside the blanket without any retrieval. The jug also moves from the blanket's center into the basket without an action. | Coherence 9; praises letting the sign go. |
| Repair | The wheel locks after overtightening, but Ada spins it to diagnose the noise before loosening the nut. Plants reach shelter, then the cart returns to the bench with plants apparently still aboard, making the protection outcome unclear. | Coherence 9; praises a clear mechanical cause. |
| Museum | Dot receives the dragon cutout, but the final image calls it a paper moth without an exchange. The shadow explanation is much more coherent than this final object identity. | Coherence 9; no continuity warning. |
| Pond | Mina puts the willow twig on the gravel; it reappears tucked through the returned net's handle without retrieval. | Coherence 9; no continuity warning. |
| Pottery | A handle is used before its construction is narrated; a freshly thrown cup can still make the firing deadline while restarting supposedly cannot. The thumb-rest/handle geometry is unclear. | Coherence 9; praises functional verification. |
| Bakery | A round cake acquires a corner; a morning errand with a half-hour detour ends in evening without transition. Mr. Hobb rejects a cake before being told about it. | Coherence 9; no continuity warning. |

Other stories have weaker rather than outright contradictory joins: the orchard
owner comments on cutting out the bruise after the children already ate that
pear; trail accommodates every goal just in time despite its additional detour;
greenhouse's opening leaf-selection motive is artificial. These are not all the
same severity, and omission of a trivial action alone does not make a whole
story unusable.

**Conclusion:** promising cheap reference prose, not flawless ground truth.
The state/continuity checker still has a purpose. The standard judge presently
rewards polished arc and moral choice while overlooking local contradictions.
Before optimizing against these scores, add an independent evidence-based
continuity audit or blinded paired comparison. Preserve this unmodified score
as the requested baseline rather than retroactively changing the rubric.

## Usage and Cost

Generation returned 3,414 input tokens and 127,202 output tokens, including
107,450 reasoning tokens. All twenty served Luna/Flex and completed without
truncation. Latencies: 67-258 seconds. No generation retries or failures.

At the current [Luna rates](https://developers.openai.com/api/docs/models/gpt-6-luna)
and their documented Flex discount, estimated generation is **$0.0319712** total,
or **$1.60 per thousand direct stories** at this usage. This is calculated from
reported usage, not an invoice. It is not the price of a reusable storyscene pack.

Terra returned 22,727 input and 1,934 output tokens, no cache writes or reads.
The existing ledger's deliberately conservative judge allowance is $0.0800255;
generation's conservative allowance is $0.0644545. Total newly accounted spend
is $0.14448. Shared campaign accounting is **$6.57995868 of $10**, including
the unchanged $5.15 of earlier unknown-usage holds. Do not mistake these ledger
allowances for invoiced Flex cost.

## Artifacts

- `STORIES.md`: all twenty untouched stories, with scenario and seed identifiers.
- `REPORT.md`: every per-story judge score and note.
- `summary.json`: aggregate scores, usage, lengths, and generation cost.
- `quality/`: saved judge request, raw response, validated results, and settings.
- Scenario directories: exact requests, raw responses, story text, and outcomes.
- `PROTOCOL.md`: methodology, limitations, and commands.
- `_source/`: frozen source snapshots; previous pack artifacts remain untouched.

Validation: two new offline runner tests and fourteen existing authoring tests
pass. Saved judge output validates complete, unique coverage of all twenty IDs.
