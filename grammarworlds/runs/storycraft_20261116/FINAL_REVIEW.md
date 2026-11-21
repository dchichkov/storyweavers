# Final development review: round06

This review covers the actual saved outputs in `round06/{pottery,music,greenhouse}/samples.jsonl.gz`: three forced branches per world, at seeds 101 and 307, for **18 revised/original pairs**. I read the prose before inspecting QA evidence. These seeds were new to this reviewer, but the designs and implementation condition were known. This is **unblinded development review**, not a condition-masked trial or independent statistical validation.

## Preference result and scope

**16 revised preferences, 2 ties, 0 original preferences.** The ties are the two greenhouse seedlings-only branches. This supports a qualitative improvement in these authored prototypes. It does not establish equal-length efficiency, the quality of unforced branch selection, transfer to a new world, or improvement across all 20 worlds.

The original body is reused for all three revised branches at each world/seed; there are only six distinct original bodies. The revised branches are also closely related. The 18 judgements should not be treated as independent trials.

| World | Seed | Revised branch | Revised / original words | Preference | Reason |
|---|---:|---|---:|---|---|
| Pottery | 101 | keep_dent | 187 / 105 | Revised | Hiding and then displaying the dent makes the change in Bea's priorities visible. |
| Pottery | 101 | remake | 207 / 105 | Revised | The drawing stands in for the late gift; the lost birthday deadline remains a real cost. |
| Pottery | 101 | make_bowl | 194 / 105 | Revised | Grandpa proposes the alternative and Bea physically relinquishes the drawn design. |
| Pottery | 307 | keep_dent | 180 / 110 | Revised | Recipient need, the imperfect object and one-handed use form a coherent payoff. |
| Pottery | 307 | remake | 197 / 110 | Revised | The wider handle now has a visible practical reason; the drawing-to-cup ending carries time and cost. |
| Pottery | 307 | make_bowl | 190 / 110 | Revised | The ending demonstrates usefulness rather than restating that the damage was fixed. |
| Music | 101 | choose_private | 197 / 61 | Revised | Negotiated privacy is honored, and crossing out the names costs a public turn. |
| Music | 101 | choose_solo | 205 / 61 | Revised | Both people's wishes persist; the answering hand embodies the changed arrangement. |
| Music | 101 | choose_written | 225 / 61 | Revised | Conditional permission, actual credit and written marks create a clear chain. |
| Music | 307 | choose_private | 193 / 95 | Revised | The repeated answering rhythm links the opening partnership to the private ending. |
| Music | 307 | choose_solo | 205 / 95 | Revised | Nia explicitly retains her own wish while respecting the refusal; the loss is legible. |
| Music | 307 | choose_written | 225 / 95 | Revised | The original already has written music, but the revision gives its authorship and performance a negotiated meaning. |
| Greenhouse | 101 | choose_share | 233 / 113 | Revised | The show establishes what staying costs; the unused trolley and ribbon pay off that setup. |
| Greenhouse | 101 | choose_flower | 262 / 113 | Revised | Nia's initial preference, delayed recognition and irreversible leaf damage make the correction consequential. |
| Greenhouse | 101 | choose_seedlings | 244 / 113 | Tie | The dry sunflower is a clear cost, but the reason to reject adequate sharing remains weak and logistics occupy much of the extra text. |
| Greenhouse | 307 | choose_share | 230 / 92 | Revised | The revised version adds a competing desire and time cost to the original's uncomplicated sharing solution. |
| Greenhouse | 307 | choose_flower | 259 / 92 | Revised | The revised mistake-and-response arc is more developed, though the compared original takes a different branch. |
| Greenhouse | 307 | choose_seedlings | 241 / 92 | Tie | More concrete setup and ending, but an underexplained sacrifice and long mechanism sequence offset those gains. |

Total displayed body words across these pairs: **3,874 revised vs 1,728 original**, an increase of about **124%**. Individual increases range from 64% to 269%. None is within a 20% length band. These preferences must not be described as a matched-length gain. Several comparisons also differ in branch outcome, so they compare overall versions, not the isolated effect of one added beat.

## Prior defects: resolution check

| Earlier finding | Result in saved round06 outputs | Evidence / remaining qualification |
|---|---|---|
| Pottery conceal/reveal variants do not connect | Pass | Bea hides the dent, then explicitly brings out the cup with the dent toward Grandpa. |
| Birthday on Saturday and intended surprise absent from prose | Pass | Both are stated in the opening before the deadline dialogue. |
| Lost colon in the opening | Pass | Current openings use separate complete sentences. |
| Remake lacks evidence for a wider handle | Improved / pass at basic causal level | Both preference variants now mention inadequate room in the old mug's handle. The shared thumb-support dialogue still gives the alternative branches a slightly mechanical common setup. |
| Private music says crossed-out line is empty | Pass | The final image now describes names beneath pencil marks. |
| Helper is indefinitely available in greenhouse | Partial | Mr Bell states a bus duty and actually leaves. This establishes an immediate conflict, but meeting a bus does not by itself establish unavailability for the entire afternoon. |
| Leaf damage appears instantaneous | Improved | The leaf is already curled and ten minutes pass before Nia notices browning. This is sufficient narrative progression for this prototype; it is not a calibrated plant physiology claim. |
| All-seedlings choice lacks a reason over adequate sharing | Partial / still weak | Looking at the curled leaf conveys concern. The authoritative advice still says half plus shade is enough, so the full-can sacrifice needs a distinct belief, urgency or preference to become fully persuasive. |
| Generic titles weaken presentation | Pass | “The Cup in the Drawing,” “The Answering Beat” and “One Can Left” are tied to story content. |
| Event-log rhythm and redundant implementation steps | Not fully resolved | Named subjects, literal dialogue tags and separate can/umbrella operations still dominate stretches, particularly in greenhouse. |

## QA evidence audit

The saved sample files contain **136 QA pairs and 314 evidence slices**. I mechanically checked all 314 slices against their raw-story offsets; all match. Semantic review focused on the previously identified scope failures and new helper-departure questions. Offset validity is not proof that an answer follows from its evidence.

The key previously missing execution evidence is now present:

- **Pottery disclosure:** includes the earlier birthday-surprise setup as well as the reveal.
- **Music private duet:** includes the actual after-concert move and door closure, not only Mateo's requested condition.
- **Music written rhythm:** includes Mateo actually drawing/tapping the rhythm, not only his offer.
- **Greenhouse umbrella:** the fuller assistance question now includes request, holding and tying events.

These targeted corrections **pass** in the reviewed archive. Answers remain tied to the branch taken; for example, the late cup is not described as ready on the birthday, and the brown leaf is not described as healed.

Remaining QA issues:

1. **Temporal overstatement:** “Why could Mr Bell not tend the umbrella all afternoon?” is stronger than the visible fact that he must meet a bus. Ask why he had to leave at that moment, or narrate the duty that keeps him away through the relevant show window. Do not let a short departure imply permanent unavailability.
2. **Scope precision:** “school gate” appears in answers while the visible departure says “the gate.” The world may name it a school gate, but the textual evidence only identifies a gate associated with the class bus. If the goal is text-answerable QA, use the surface-established description or introduce the school explicitly.
3. **Repeated questions:** greenhouse now asks what Nia requested, how Mr Bell responded, and how he helped secure the umbrella. These are grounded but overlap heavily. Music still separately asks what Mateo offered and what he allowed. More evidence should support fewer, better questions rather than automatically adding near-duplicates.
4. **Reviewer-like wording:** “Did remaking the cup remove the cost of Bea's choice?” remains less natural than “Was the new cup ready for Grandpa's birthday?” The retained-consequence check is useful; the wording need not expose the evaluator's terminology.

## Concrete conclusion

**Pass, limited claim:** The three authored prototypes now show more character-led storytelling than their displayed originals. The strongest improvements are consequential negotiation in music, transformed physical meaning in pottery, and an irreversible consequence plus an opportunity cost in greenhouse. These are additions to the stories themselves, not merely annotation labels.

**Not yet passed:** The proposed condition-masked and near-equal-length comparison gates. No such comparison is present here. The output also does not establish general autonomous composition or broadly learned storytelling; the meaningful branches and endings are authored.

**Remaining editorial priority:** Compress the greenhouse mechanism sequence while clarifying the seedlings-only choice. The current risk is adding a new sentence for every grounding concern until the central decision is buried. Keep the necessary state transitions, but let several routine operations share a concise narrated scene. Across all three worlds, paragraph rhythm and lighter attribution could improve flow without adding plot machinery.

## Reviewed archive identities

SHA-256 of the `samples.jsonl.gz` files:

- Pottery: `0f0710582e5a491cc5f8acf0f5c14783c6d6f972ffadc483b25804a94e49e5a4`
- Music: `090f46ab1dcb1461c8e465a697c23901c079cd305efe7f0fc9dc823576cb5c11`
- Greenhouse: `4dc1dc7a17539ff2ba537cf4c03d33555ffb186ceae7c2bfd9f7db764a7ccee3`

Later source changes do not retroactively change these judgements. A new sample archive is needed to verify later corrections.
