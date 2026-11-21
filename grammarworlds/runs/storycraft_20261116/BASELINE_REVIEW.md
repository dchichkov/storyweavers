# Baseline storytelling review — 2026-11-16

Review scope: independently read all 20 standalone `seed=1103`, past-tense, budget-2 stories in `../beats_20261115/final_audit/source_samples.jsonl.gz`; detailed judgements below cover ten diverse stories. Read the preceding report, `QUALITY.md`, and the design in `story.py`. These are editorial judgements of the rendered stories, not a fresh Luna evaluation, a statistical estimate of all seeds, or an assessment of unseen original stories. Fidelity is intentionally unscored because original source prose was not reviewed alongside these outputs.

## Main finding

The generator already knows many worthwhile story ingredients. It usually narrates them as a completed task checklist. Adding more hesitations, inspections and statements that an object is now fixed will not address that. The larger opportunity is to make a character's **reason for choosing** legible, let that choice affect another person or something the character values, and end with an action whose meaning depends on the beginning.

The strongest existing material is not the optional beat layer: Nia's sunflower costs the tomatoes a brown leaf; Bea makes the damaged cup useful for Grandpa Len; Mateo chooses a private duet. Those premises can support stories. They need narrative attention concentrated on the contested moment, rather than uniformly on fetching, borrowing, placing and returning objects.

Physical grounding remains important. The emotional change should reside in a person's actions and relationships with a concrete carrier: who receives the lantern, who holds the cup, whose seedlings lose a leaf. Abstract labels such as `selflessness` or `realization` would not, by themselves, improve the text.

## Ten detailed baseline judgements

Scores follow the 1–5 anchors in `QUALITY.md` for coherence, naturalness and overall. A 3 is acceptable but flawed. These are rounded editorial scores, not confidence intervals. The structural diagnosis deliberately asks more than whether the story has a goal and an ending sentence.

| Story | Coherence | Naturalness | Overall | Specific evidence and diagnosis |
|---|---:|---:|---:|---|
| Greenhouse | 4 | 3 | 3 | The one-can constraint, selfish first choice, brown leaf and tomorrow promise create a real causal/emotional arc. However, the text jumps from the leaf to umbrella work and adult repairs. We do not see what Nia notices or why she changes priorities. The last brown leaf is a meaningful persistent cost; retain it. |
| Pottery | 4 | 3 | 3 | Grandpa's stiff hand and a dent becoming a thumb rest are a strong setup/payoff. “I would like a thumb rest” announces the solution with little discovery. “The dent had become a thumb rest” followed immediately by Grandpa's thumb restating it over-explains the payoff. Firing twice contributes little at this length. |
| Music | 4 | 3 | 3 | Mateo expresses a boundary; the private duet respects it and achieves a changed version of Nia's goal. Nia's initial desire is only a duet, however, so agreeing to privacy costs her nothing visible. The signup-sheet title promises an object absent from the body. The moment could become a story if public performance matters to Nia and she chooses companionship. |
| Bakery | 3 | 2 | 2 | Loneliness supplies stakes, but smudged icing barely changes anything. Tessa neither worries about it nor weighs returning/replacing the cake. “I am pleased” states satisfaction without an interpersonal exchange. The glowing candle is promising; opening the window is not clearly connected to loneliness. |
| Library | 4 | 3 | 3 | Mina postpones her moon drawing and promises help; Jun later helps her. That reciprocity is meaningful. Ms Alvarez reserves the atlas and retrieves the book, so the protagonist's possible sacrifice and useful contribution are faint. The clue is noticed, then solved by an adult without tension. |
| Repair | 2 | 2 | 2 | The attempted fix locks the wheel and the hidden string explains the failure: a useful causal spine. “I am wrong” is generic, and Niko placing the tray followed by “She loosened the nut” confuses agency. Long logistics flatten the discovery; the final tray and wheel images compete. |
| Festival | 4 | 2 | 3 | Blocking the entrance and relocating the string are materially consequential. Rafi's wish to tie the flag can make participation the issue, but the bread cart drives the correction more visibly than Rafi's access. The help request addresses equipment; “I need space” is the better line. Several final lines redundantly confirm success. |
| Camp | 3 | 2 | 2 | Nora stays with frightened Theo and gives him the lantern; these can embody care rather than simply rescue. The bell clue is unexplained and the rabbit is freed immediately. Theo's role remains receiving/returning objects. “The toy rabbit was free now” contributes nothing between freeing and handing it over. |
| Picnic | 2 | 2 | 2 | Hunger, a welcome for Theo, a drifting sign, an unsteady basket, a stone on a blanket and an apology appear without a clear shared causal line. Why does Theo apologize? What happened to the sign? Saving the sandwich is potentially meaningful but the competing pressures are not dramatized. |
| Trail | 3 | 2 | 2 | Stamp-seeking and a level path could conflict productively. The fallen birch prompts a detour but nobody appears to give anything up. Map, compass, marker, salamander, stamp and sketchbook all receive near-equal attention. The ending lists two possessions rather than showing a changed relationship or a decision paid off. |

The other ten inspected bodies reinforce the pattern. Snow has a genuine cost (Tomas leaves the race) but barely attends to it. Costume has a potentially generous transfer followed by clothing logistics. Market has a correction and a patient customer, but a generic confession. Museum supports a perceptual discovery but renders instruction rather than surprise. Puppets, orchard, pond, laundry and biscuit have concrete actions and some strong final objects; their decisive moments remain hurried. Seaside offers a safety choice, but Milo's worry is stated once and the map supplies an immediate solution.

## What would count as a substantial improvement

A story need not obey one mandatory plot template. For these short character-led stories, use the following questions as diagnostics:

1. **Desire with personal meaning:** Before the problem, can a reader explain why this character cares, beyond “I want X”?
2. **Pressure:** Does the obstacle threaten that desire or expose a competing value? A random broken object is insufficient unless its consequence matters.
3. **Choice:** Is there a moment where the character could plausibly do otherwise, with a legible reason for the selected action?
4. **Consequence:** Does the choice alter the situation, another person's response, a future option, or the character's relationship to a physical object?
5. **Payoff:** Does the final action/image answer an earlier desire, worry, promise or detail? Could it be transplanted into an unrelated story without losing much meaning?
6. **Economy and rhythm:** Are routine steps compressed so the choice and payoff have room? Does each dialogue line change knowledge, willingness, relationship or the next action?

Not every beat needs all six. Evaluate the whole story. A quiet boundary respected can be as effective as a failure-and-recovery arc. Do not require a moral sentence, costly sacrifice in every story, or three attempts just to satisfy a checker.

## Proposed evaluation gates

Freeze these criteria before reading revised samples; they are suggested acceptance gates, not a claim that current work already passes them.

- **Text-level gate:** In at least 80% of reviewed new stories, a reader can point to an actual sentence or exchange establishing the stakes, a consequential choice, and an earned payoff. Metadata alone does not satisfy this.
- **No padding gate:** Remove generic reaction/callback sentences mentally. If the story is identical in motive, inference and effect, mark those additions as expendable. At least 80% of added beat sentences should contribute information or meaningful rhythm; report deletions as legitimate improvements.
- **Native-state gate:** Important dialogue and decisions have traceable state or obligation consequences. Assertions about having helped, apologized, forgiven or fulfilled a promise must match the actual branch. An utterance is not automatic fulfillment.
- **Diversity gate:** Across at least three distinct world/premise families, inspect several materially different branch outcomes. Distinguish lexical paraphrases, surface event-order changes, and changed decisions/consequences; count them separately.
- **Comparison gate:** Review at least 18 condition-masked comparison pairs, spanning three or more premise families and heldout seeds/branches. Prefer the new story in at least 12, with at most three losses, before claiming clear improvement in that tested slice. Ties count as ties. This is an editorial gate, not significance testing.
- **Length disclosure:** Target body lengths within 20% for pairwise comparison; mark unmatched pairs rather than silently stretching or truncating prose. Also compare against a compact baseline: winning only by doubling the text is a qualified gain.
- **No regression gate:** Existing grounded QA, attribute distributions, replay, physical constraints and presentation offsets remain valid in the supported path. Independently inspect QA alongside the new stories: a formally cited answer can still be shallow or misfocused.

For fidelity, a rewrite should preserve the chosen premise and intended branch contract, not necessarily every former logistics event. This task explicitly permits new content. Keep the declared scope visible if only a prototype subset is improved.

## Condition-masked comparison workflow

1. Freeze the implementation and record hashes before drawing final samples. Select seeds and branch configurations that were not inspected during development.
2. Generate each pair from the same intended premise and compatible initial state. Record state changes and branch identity separately from prose. Preserve failures; do not replace unattractive random samples.
3. Produce a reviewer file with only randomized `A`/`B` story texts, a pair ID and neutral premise. Hide condition, selected beat labels, runtime metrics and expected winner. Randomize order independently per pair.
4. A reviewer who did not implement the changes gives a preference (`A`, `B`, `tie`) and one concrete reason; separately records missing stakes, weak choice, unsupported consequence, redundant beat, dangling setup, weak ending and reference errors. Score standalone naturalness/overall before inspecting traces.
5. Reveal the key only after judgements are saved. Then audit trace grounding and source fidelity. Report both preference outcomes and integrity failures; do not erase a preference because the losing sample had a defect.
6. Because reviewers may recognize the old generator's style, describe this as condition-masked review, not perfect blindness. A single agent's judgement is informative but not a calibrated human-panel or Luna score.

## Five heldout branch challenges

These are short challenge families for later testing, not scripts the generation must copy. Reserve a new combination of names, possessions, available tools and goals in each. A story can answer them with different genres or endings.

1. **The saved seat:** A child has kept a particular seat for a friend, but another visitor needs it to participate. The friend arrives late. Show the choice and the friend's response without resolving the conflict by conjuring an identical spare seat. Tests conflicting commitments and an earned relational payoff.
2. **The damaged gift:** An imperfect object is useful to its intended recipient. Compare a branch where the maker knows the recipient's need with one where they must ask. The maker must not know the answer before evidence or dialogue. Tests discovery, information flow and adaptation rather than generic repair.
3. **The private performance:** One character wants an audience; their partner is comfortable playing only privately. Test refusal, negotiation and a smaller success. Do not make the reluctant partner instantly brave or treat refusal as a physical obstacle to fix. Tests dialogue consequences and a changed goal.
4. **The useful wrong turn:** Two characters seek different outcomes on a shared trip. A detour can satisfy one goal while putting the other at risk. Test whether a negotiated choice and its cost persist into the ending; the final reward should not erase all tradeoffs. Tests causal continuity and competing wants.
5. **The promise after the mistake:** A first choice causes a small lasting loss. Later repair can improve the situation but cannot undo that loss. End with evidence of a changed action, or an explicitly deferred promise, rather than claiming the lesson already changed future behavior. Tests irreversible consequences and honest closure.

For each challenge, flip one relevant condition (helper unavailable, tool already held by the other character, refusal maintained, cost already incurred, or earlier promise still open). The story should change for that reason. Merely changing adjectives or appending a different moral does not pass.
