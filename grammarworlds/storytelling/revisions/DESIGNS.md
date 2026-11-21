# Three content prototypes: decisions that leave a mark

These are **human-authored design exemplars, not generator outputs**. They propose new content for three existing grammarworlds. Names and some objects are retained; deadlines, permissions, losses and several events are new requirements, not facts already available in the runtime.

The current pottery story already has a useful transformation, the music story already has a refusal, and the greenhouse already has scarcity. Their weakest point is how quickly those tensions disappear. These revisions give each protagonist a particular expectation, allow a decision to defeat part of it, and retain evidence of that decision at the end.

## Shared implementation contract

- Model each new beat as a guarded event with effects before giving it prose. A decorative reaction must not substitute for a choice.
- Attach wants, reluctance and changed commitments to a person; attach loss and payoff to the relevant object or relationship. No free-floating “lesson” entity should render.
- Store `desired_outcome`, `available_alternatives`, `chosen_action`, `rejected_alternative`, `cost`, `decision_reason` and `consequence_ref` on decision events. These are proposed fields. References must point to recorded events/entities, and visible QA must cite the corresponding narrated evidence.
- Dialogue may change knowledge, a permission, an agreement or a plan. A spoken promise does not perform its promised physical action. Record listener and response separately.
- A branch is substantive when its final world differs: timing, ownership, permission, retained damage, public participation or use. Vocabulary variants are not branches.
- Sample a distribution over legal decision events, then sample the annotated words realizing that event. Preserve per-candidate meanings and probabilities; do not paste a complete exemplar into the runtime.
- Compress routine operations into a scene only after all necessary native transitions execute. Drying, firing, cooling, travel and resource accounting still happen even when their prose is short.
- End with one observable consequence. Do not append an explanation of the same consequence, a generic moral or an extra callback that merely repeats it.

## 1. Pottery — A Place for His Thumb

**Tension:** Bea wants a flawless birthday gift that can stand beside Grandpa Len's old mug. Grandpa needs a cup he can hold comfortably. Accepting help from the recipient means spoiling the surprise and surrendering her planned shape; remaking preserves her design ambition but misses the birthday.

### Exemplar: keep and adapt the dent

Bea had made Grandpa Len a blue cup for his birthday. She wanted it to stand beside his old mug, straight and smooth. Then her shaping rib slipped. A dent appeared below the handle.

She turned that side toward the wall.

“I can start again,” she told Mr Ivo.

“You can. But a new cup won't be ready for Saturday.”

Grandpa was coming to collect her. Bea put the cup behind the sponge, then moved the sponge away.

“Your present has gone wrong.”

Grandpa bent over the bench. His stiff fingers could not curl around the narrow handle of his old mug. He held his hand beside the new cup instead.

“My thumb wants somewhere here,” he said.

“Where the dent is?”

He nodded. Bea had wanted a surprise. Now Grandpa knew the present, and the cup would never look like her drawing. She picked up the sponge and rounded the dent into a shallow hollow.

Mr Ivo dried, fired and glazed the cup. On Saturday, after its final firing and cooling, Bea set it on Grandpa's table with the dent facing him.

Grandpa poured his tea. His thumb settled into the hollow, and his other hand stayed in his lap.

### Distinct branches

| Branch | Decision and cause | Persistent cost | Different ending image |
|---|---|---|---|
| Keep the thumb hollow | Bea reveals the spoiled surprise; Grandpa identifies a useful grip; Bea adapts the thick, uncracked wall. | Surprise lost; visible dent deliberately retained. | Grandpa holds the cup in one hand, thumb in the hollow. |
| Remake and arrive late | After hearing the firing schedule, Bea chooses a fresh design with a larger handle and gives Grandpa the drawing on Saturday. | Finished gift absent on the birthday; Bea must return later rather than claim success immediately. | A week later, Grandpa removes the drawing from beside his old mug and puts the finished cup there. |
| Change the kind of gift | Grandpa says two hands would be easier; Bea cuts down the wet cup and shapes a low bowl. | Original cup design and handle abandoned; gift can no longer be used one-handed. | Grandpa cups the bowl in both palms while Bea pours. |

### Required state and effects

| Event name | Preconditions | Committed effects / evidence |
|---|---|---|
| See the dent | Cup wet, wall thick, no crack; Bea owns the drawing and intends a surprise. | Cup `dented`; Bea knows dent; drawing retains `smooth_cup_design`. |
| Hear the schedule | Mr Ivo knows the firing schedule; Bea present. | Bea knows `remake_misses_birthday`; no cup is fired by speech. |
| Reveal the present | Grandpa present; gift not previously revealed. | Grandpa knows gift; `surprise_preserved=false`; links to Bea's initial intention. |
| Ask about the grip | Grandpa `stiff_hand`; cup safely on bench. | A recipient preference is recorded: `thumb_hollow` or `two_hands`, with Grandpa as speaker. Do not have Grandpa lift unfired clay. |
| Choose the redesign | Applicable recipient preference known; material still workable. | Exactly one design selected; retained dent / removed handle / discarded first blank recorded on the cup. Remake records a later completion date. |
| Finish the gift | Each drying, bisque, glaze, final firing and cooling guard satisfied. | Cup safe for use; completion time compared with birthday; no shortcut from speech to usable ceramic. |
| Use the gift | Gift handed to Grandpa; safe, cool, suitable shape. | Actual grip recorded. Final image allowed only for that grip and branch. |

**Grounded QA for the exemplar:**

- Why did Bea stop hiding the cup? She wanted Grandpa's help with the damaged gift. She moved the sponge aside and told him the present had gone wrong.
- What did Bea give up by asking Grandpa? The present was no longer a surprise. Grandpa saw the cup before his birthday.
- Why was the dent kept? Grandpa indicated that his thumb needed a resting place there. Bea rounded the dent into a hollow, and he later used it while holding his tea.
- Was the cup remade? No. Bea changed the dent in the existing cup; Mr Ivo then finished that cup.

The first QA answer requires the decision's explicit help-seeking motive, not an inferred motive from moving a sponge. If that motive is not narrated, ask only what she did.

## 2. Music — The Empty Line

**Tension:** Nia wants her name on the concert sheet with Mateo's. Mateo likes answering her rhythm but does not want an audience. A private duet costs Nia her concert turn; a solo preserves it but cannot deliver the duet she wanted. A written contribution is a third agreement, not presumed consent to perform.

### Exemplar: give up the public turn

Nia had written two names on the concert sheet: Nia and Mateo. Beside them she drew two little drums.

During practice, she tapped three quick beats. Mateo answered with two slow ones. Then Dalia opened the hall door. Beyond it, chairs stood in rows.

Mateo set down his sticks.

“Take my name off,” he said.

“We practiced all week.”

“I want to play with you. I don't want everyone looking.”

Dalia laid a pencil beside the sheet. “You can play alone. But I need the final list now.”

Nia picked up one stick. She could play the first rhythm and the answering rhythm herself. She tried them, but Mateo kept his hands in his pockets.

“What if it's just us, after the concert?” she asked.

“With the door shut?”

“Shut.”

Mateo took his sticks out again. Nia crossed out both names. Dalia gave their turn to the next child.

After the last applause, they carried the drums into the practice room. Nia shut the door and tapped three quick beats. Two slow beats answered.

On the concert sheet outside, their line was empty. Inside, neither drum was quiet for long.

### Distinct branches

| Branch | Decision and cause | Persistent cost | Different ending image |
|---|---|---|---|
| Private duet | Mateo accepts a closed-door invitation; Nia withdraws both names before the list closes. | Nia loses her public turn; no later applause or surprise performance cancels the cost. | Empty concert line outside; answering drums inside the closed room. |
| Public solo | Nia accepts the refusal, removes Mateo's name and chooses her own turn. | The public duet does not happen; Mateo's readiness remains unchanged. | Nia bows alone; the unused second pair of sticks stays beside Mateo. |
| Written collaboration | Mateo offers his rhythm on paper and explicitly permits Nia to play it and name him as its writer. | Mateo remains absent from the stage; Nia gives up sole authorship credit. | Nia's finger rests beside Mateo's pencilled notes before she begins his answer. |

### Required state and effects

| Event name | Preconditions | Committed effects / evidence |
|---|---|---|
| Put down two names | Nia holds pencil; sheet accepts entries; Mateo has not consented to public performance. | Sheet lists both names; record `entry_unconfirmed`, not consent. This is Nia's mistake, not legitimate authorization. |
| Refuse the audience | Mateo sees arranged chairs; both children present. | `public_consent=false`; Nia hears refusal; Mateo's public name must be removed on every ending path. |
| Close the list | Teacher present; public slot still available. | A deadline becomes known. After allocation elsewhere, Nia cannot quietly regain that same slot. |
| Agree to private music | Nia asks for private duet; Mateo responds with closed-door condition; Nia accepts. | Conditional private consent recorded. Public consent remains false. No musical performance yet. |
| Withdraw the entry | Nia holds pencil; final list not yet allocated. | Both names removed; public slot freed, then allocated elsewhere by teacher. |
| Offer written rhythm | Mateo has paper/pencil and chooses to offer. | Paper acquires rhythm; permission to use and named credit recorded independently from public performance consent. |
| Play the chosen arrangement | Instruments held; matching consent and location; closed door for private branch. | Actual arrangement and performers recorded. Private duet cannot trigger an audience-applause scene. |

**Grounded QA for the exemplar:**

- Did Mateo refuse to play music with Nia? No. He said he wanted to play with her but did not want everyone looking. He later agreed to a duet behind a closed door.
- What did Nia give up? She crossed out her concert entry along with Mateo's. Dalia gave their turn to the next child.
- What had to happen before Mateo would play? Nia agreed to shut the practice-room door. The later duet happened in the practice room with its door closed.
- Did the audience hear their duet? No. It took place after the concert in the closed practice room, after their public entry had been withdrawn.

## 3. Greenhouse — One Can Left

**Tension:** Nia wants to carry her sunflower to the afternoon flower show. The shared tomato seedlings need the last water. Keeping both kinds of plant alive requires shared water, shade and Nia's continued care, so it costs the outing. Choosing the sunflower instead leaves visible damage that cannot be repaired by a convenient refill.

### Exemplar: stay with the plants

Nia tied a yellow ribbon around her sunflower's pot. The flower show began at two, and she had cleared a place for the pot on her trolley.

Inside the greenhouse, the tomato seedlings lay against the edge of their tray.

Mr Bell turned the tap. Nothing came out. “One can left in the barrel,” he said. “The repair part won't come until tomorrow.”

Nia lifted the can toward her sunflower.

“Those were planted by the little class,” Mr Bell said, pointing to the tray.

“Will half a can be enough?”

“With shade. But the pots must stay here.”

Nia looked at the trolley. Then she poured half the water over the seedlings and half into the sunflower pot. Before she could move them together, the torn shade cloth slipped from its hook.

She opened her umbrella above the tray. Its handle slid sideways.

“Hold it,” she told Mr Bell.

While he held the handle, she tied it to the heavy pot. They moved the sunflower underneath. Its yellow ribbon brushed the tomato leaves.

At two, Nia was still turning the umbrella to follow the shade. The empty trolley stood by the door. Under the umbrella, the seedlings had lifted their heads beside her flower.

### Distinct branches

| Branch | Decision and cause | Persistent cost | Different ending image |
|---|---|---|---|
| Share and stay | Nia learns the half-water-and-shade constraint, divides the reserve, repairs temporary shade and stays to adjust it. | Flower show missed; tap remains broken; water reserve stays empty. | Show trolley unused; ribbon beside recovering seedlings. |
| Flower first, then take responsibility | Nia spends the can on her show flower. A seedling leaf browns before she shields the tray. She cancels her departure and stays; Mr Bell accepts her admission of the choice. | Brown leaf remains; no claim that shade reverses damage or supplies water. | Nia places the empty can beside the tray and shades its surviving green leaves. |
| Give the seedlings the water | Nia pours the full can on the seedlings, then shades her still-dry sunflower and withdraws it from the show. | Sunflower droops and is not show-ready; its survival is unresolved rather than asserted. | Nia unties the show ribbon and uses it to mark the pot that needs water first tomorrow. |

### Required state and effects

| Event name | Preconditions | Committed effects / evidence |
|---|---|---|
| Prepare for the show | Ribbon and trolley available; show not yet begun. | Ribbon attached to pot; intended departure time recorded; public goal has physical carriers. |
| Discover the last water | Tap broken; barrel contains two half-can units; dry plants present. | Nia learns the limit and tomorrow's earliest repair; no immediate repair branch available. |
| Learn the shade condition | Caretaker present and knows the authored horticultural constraint. | Nia knows half-water recovery requires continued shade. This is a local storyworld rule, not a general botanical claim. |
| Allocate the can | Nia holds full can; two units available. | Allocation exactly `(1,1)`, `(0,2)` or `(2,0)` for seedlings/flower; barrel and can empty. No water created. |
| Lose the shade | Cloth torn/unsupported; plants still in greenhouse. | Cloth falls; plants exposed; flower-first branch records one browned leaf on the seedlings. |
| Ask for a steady handle | Umbrella unstable; caretaker nearby. | Request recorded, then separate acceptance and holding action. Tying is illegal until caretaker is holding or another valid support is present. |
| Keep the temporary shade | Umbrella secured; Nia stays and adjusts its position through show time. | Shade exposure sufficient for watered plants' recovery; Nia misses show. Zero-water plants cannot receive `recovered` from shade alone. |
| Close the day | Branch-specific plant states observed; can returned. | Retain brown leaf, empty reserve, broken tap and missed-show state as applicable. Ending must not add repaired supply, a prize or full recovery unsupported by the trace. |

**Grounded QA for the exemplar:**

- Why did Nia divide the water? Mr Bell said half a can could be enough if the plants stayed in shade. She used half for the seedlings and half for her sunflower.
- Why did she miss the show? Keeping the shared-water plants shaded required her to stay and adjust the umbrella. She was still doing that at two, when the show began.
- What changed after Nia asked Mr Bell to hold the umbrella? He held its handle while she tied it to the heavy pot. The umbrella could then shade both kinds of plant.
- Was the tap repaired? No. Mr Bell said the part would arrive tomorrow, and the story ends with temporary shade rather than a repaired water supply.

## What to compare after implementation

Generate all branches, then several independent seeds within each branch. Compare against the existing compact stories at similar length, not only against longer versions with inserted beats. Read the complete story and QA together.

Check whether the reader can name the particular thing wanted, identify the moment it became difficult, explain the chosen alternative, and point to a remaining cost in the ending. A passing state checker cannot establish these literary properties. Also check that dialogue causes an observable update, that a final image is not immediately paraphrased, and that prose still varies without changing the branch's meaning.

These three prototypes share a decision contract but should not share a single surface template. Pottery turns an embarrassment into a usable form; music renegotiates participation; greenhouse allocates an inadequate resource and preserves a loss. Keep those causal differences visible.
