# Three-world content review

Reviewed actual generated outputs for all three forced branches of pottery, music and greenhouse, seed 19, using `generate(scenario, 19, edition='crafted', choice=branch)` and `questions(row, 20)`. Compared each against the original edition at seed 19 with expanded continuations and beat budget 6. This is an **unblinded development review of nine stories**, not the heldout condition-masked evaluation proposed in `BASELINE_REVIEW.md`.

The inspected outputs were captured locally in `/tmp/storycraft_content_review_samples.json`. This review describes that snapshot; later edits can legitimately supersede individual findings.

## Judgement

These versions do more actual storytelling than the originals. My order of improvement is **music, pottery, greenhouse**. I prefer the revised text in all nine inspected pairs when allowed its extra length, but that observation cannot isolate improved narrative decisions from a much larger word budget. No same-length comparison or random-branch generalization is established here.

| World / branch | Revised body words | Original body words | Length increase | Revised overall judgement | Main reason |
|---|---:|---:|---:|---:|---|
| Music / private | 188 | 94 | 100% | 4/5 | Refusal, a specific negotiated condition, a foregone public turn, and an answering-beat payoff. |
| Music / solo | 202 | 94 | 115% | 4/5 | Nia respects refusal without abandoning her own wish; the answering beat changes who supplies it. |
| Music / written | 223 | 94 | 137% | 4/5 | The alternative has a condition, credit is actually given, and the written marks carry the absent partner into the ending. |
| Pottery / keep dent | 178 | 103 | 73% | 4/5 | Concealing then deliberately presenting the dent makes the changed standard of success visible. |
| Pottery / remake | 202 | 103 | 96% | 3/5 | The late gift has a real retained cost and the drawing becomes a useful interim object; the chosen remedy needs a better reason. |
| Pottery / bowl | 191 | 103 | 85% | 4/5 | Grandpa proposes a usable alternative; removing the handle visibly gives up Bea's original plan. |
| Greenhouse / share | 209 | 128 | 63% | 3/5 | A show deadline and shared water give the final ribbon/seedling image meaning; the adult's availability undermines the forced tradeoff. |
| Greenhouse / flower | 224 | 128 | 75% | 3/5 | The first decision leaves permanent damage; the corrective act does not erase it. The speed of damage and adult availability need attention. |
| Greenhouse / seedlings | 225 | 128 | 76% | 3/5 | The flower remains dry and tomorrow's obligation stays open; the decision has costs but too little explanation for choosing this over sharing. |

Scores use `QUALITY.md`'s whole-story 1–5 anchors: 3 means acceptable but flawed, 4 means good with a remaining issue. Fidelity to original wording is not a goal for this expressly authorized rewrite. Baseline overall judgements for these three specific old outputs are approximately 3/5. These scores are one editor's assessments, not a calibrated model score.

## Corrections that matter most

### 1. The greenhouse tradeoff needs an unavailable alternative

Mr Bell can hand over the can, explain the problem, catch and hold the umbrella, and move the flower with Nia. Why can he not keep the umbrella adjusted while she goes to the show? The text currently insists “You must stay” without making that constraint credible.

Add one concrete competing duty or limit for Mr Bell and execute it. For example, he can help briefly but must leave to collect the children; the story should then show him leaving rather than retain an indefinitely available adult. This would make Nia's missed show a consequence of a real decision instead of a rule imposed by the narrator. Do not merely add `helper_unavailable` metadata.

The seedlings-first branch also needs a reason to give the whole can to them after Mr Bell has explicitly said that half plus shade is enough. A reader can infer generosity, but the chosen sacrifice is currently less intelligible than the available sharing option. Distinct recipient needs or different beliefs could justify it; alternatively, keep sharing as the rational default and treat this branch as a character-specific choice rather than universally better conduct.

### 2. Pottery's remake branch needs its own diagnosis

All branches first establish “My thumb needs somewhere here” and “Where the dent is?” The keep-dent solution follows directly. The remake solution jumps to “I want to make the handle bigger,” even in the variant that never mentions an old mug's narrow handle. Why abandon the proposed thumb support and accept a missed birthday?

Let Grandpa demonstrate a handle problem or ask for the wider handle in the remake branch, or let Bea test and discover that the hollow alone is insufficient. Do not make the larger-handle choice an unexplained preference after a different diagnosis. The bowl branch already does better by giving Grandpa an explicit alternative request.

The late-gift ending is good material: the drawing stands in for the cup and is moved aside when the usable object arrives. Retain that concrete continuity while fixing the motivation.

### 3. Retain consequences without making every ending punitive

The private music branch gives up the concert but gains an answering partner. The solo branch keeps the concert but loses the duet. Both are legitimate outcomes. “Nia bowed alone” and the unused second sticks give the solo branch a melancholy emphasis; that is not inherently a defect, but avoid presenting it as a moral punishment for respecting Mateo's refusal while keeping her own turn. If the intended tone is mixed rather than sad, one brief mutually respectful response from Mateo could clarify it without conjuring a duet.

In the private branch, the names are crossed out, then “their line was empty.” A crossed-out entry is not literally empty. The ending can refer to crossed-out names or an unused concert slot while keeping the strong contrast with the active drums behind the door.

### 4. Make elapsed time and action support believable

The greenhouse flower-first sample has Nia pour the water, the cloth fall, and a leaf turn brown almost immediately. This is readable symbolic causality, but a real-time presentation makes the damage seem instantaneous. A small passage of time or noticing an already drying edge would make the physical consequence easier to accept. Preserve the existing leaf afterward; do not reset it to green.

The ribbon in the seedlings branch is untied and tied around the same pot again. The new meaning is conveyed by “water first tomorrow,” but the physical change is slight. An explicit reminder position or different knot would make the final image carry that meaning more independently; avoid explaining it twice.

### 5. Compress explanation and routine work before expanding again

These are 178–225-word stories, often nearly or more than twice the baseline length. The added words generally purchase motive and consequence, but there is still room to compress:

- Pottery can shorten repeated full names and the dialogue that asks about the dent before every possible decision.
- Greenhouse spends separate sentences handing over/filling/returning the can and asking/holding/tying/moving the umbrella. Preserve the joint action, but compress its routine implementation.
- Music written has offer, permission, writing, handback, listing, practice, introduction and performance. Credit is meaningful; pencil handback is probably expendable at this length.

A useful next comparison is against a compressed revision that preserves the same choice and payoff. If the shorter version reads better, that is a gain rather than a loss of beat coverage.

Paragraph breaks would also help readers see setup, decision and payoff. The current single long body paragraph flattens rhythm even where the event structure has improved. Generic framing such as “The Tale of Nia” and “Once upon a time, Nia was at the practice room” contributes less than the authored opening already does; substantive authored titles would better fit these prototypes.

## QA findings

The questions now address motives, promises, alternatives and retained costs instead of only possessions. Most answers are supported by the **whole story**, and the previous pottery Saturday/surprise and missing-preference issues are substantially improved. However, evidence slices still sometimes fail to support a sentence in the answer.

1. **Greenhouse, all branches — umbrella assistance.** “How did Mr Bell help Nia secure the umbrella?” answers that he held the handle after Nia asked. Its evidence cites only the later tying/moving event: “Nia tied the handle to the heavy pot. Together they moved the flower beside the tray.” Include the actual request and hold events.
2. **Music, private — completed condition vs promised condition.** “Where did Nia and Mateo finally play together?” says after the concert, in the room, with the door closed. The evidence includes the condition being negotiated and the drums playing, but omits the actual wait/move and door-closing events. A promise that the door will be shut does not itself prove fulfillment. Cite execution.
3. **Music, written — writing vs planned writing.** “Who wrote the answering rhythm, and who performed it?” does not cite the actual writing event. Existing marks and credit support an inference, but the direct writing event is available and should be included.
4. **Pottery, all branches — prior surprise.** “What did Bea give up when she asked for help?” cites only disclosure. Include the opening surprise setup as well if its evidence is intended to support the whole answer, including what was lost.
5. **Question economy.** Music written asks what Mateo offered and what he allowed; these are close variants of the same conditional permission. At a six-question limit, one could be replaced by a question contrasting the original duet with the performed arrangement, if that contrast is trace-supported.
6. **Natural wording.** “Did remaking the cup remove the cost of Bea’s choice?” sounds like evaluation terminology. “Was the new cup ready for Grandpa's birthday?” tests the same retained consequence in language a story reader would use.

These are evidence-scope and presentation issues, not claims that the recorded whole-story outcomes are false. Exact text offsets alone cannot validate that a cited slice entails an answer.

## What is still missing beyond this review

The three prototypes now have authored narrative design; that is a real improvement in the tested slice. What remains unproven is whether the generator can select and compose these consequential beats effectively under less authored conditions, preserve their meaning under transfer, and produce varied stories without repeatedly using the same sacrifice-and-accommodation structure. More attribute names will not prove that.

Next useful evidence: repair the listed causal gaps, compare compressed variants, and run heldout branch/initial-condition combinations with prose reviewed before traces. Keep unpopular but legitimate choices available; ensure their consequences follow from the world rather than a blanket moral preference.
