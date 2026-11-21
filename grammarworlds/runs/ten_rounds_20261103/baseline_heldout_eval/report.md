# Luna: short stories and reading QA

20 randomly selected past-tense stories per world; duplicates retained. Luna / Flex / reasoning none. Prose uses the unchanged calibrated 0–9 story-set rubric; QA is a separate text-only judgment. No hidden state or reference story is given to either judge.

| World | Story quality / 9 | Diversity / 9 | QA quality / 9 | Grounded answers | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| rescue | 6.00 | 1 | 7.33 | 120/120 | 120/120 |
| kite | 6.00 | 1 | 7.60 | 100/100 | 100/100 |
| key | 5.00 | 1 | 7.50 | 120/120 | 120/120 |
| music | 4.90 | 1 | 6.27 | 50/118 | 50/118 |
| greenhouse | 5.00 | 1 | 7.50 | 120/120 | 120/120 |
| library | 6.00 | 1 | 8.00 | 120/120 | 120/120 |
| pottery | 6.00 | 1 | 6.35 | 107/120 | 107/120 |

Complete: True. 140 stories and 818 QA pairs judged.

## QA defects

{
  "too_shallow": 240,
  "ungrounded_answer": 101,
  "bad_evidence": 101,
  "not_answerable": 13
}

## Representative QA findings

### rescue

- **s000014:q1 (7/9): Who wanted to solve the problem?** Answer: Lily wanted to solve it. Lily wanted to rescue the kitten. Luna: Correctly names Lily, but repeats the same point in two sentences.
- **s000014:q3 (7/9): How was the problem solved?** Answer: Lily used the ladder. Lily lifted the kitten down. Luna: Correctly explains the rescue, but splits one fact into repetitive sentences.
- **s000014:q4 (7/9): What happened at the end?** Answer: The kitten rested in the warm blanket. It was warm at the end. Luna: Gives the ending, then redundantly restates that the blanket was warm.

### kite

- **s000014:q1 (7/9): Who wanted to solve the problem?** Answer: Lily wanted to solve it. Lily wanted to repair the kite. Luna: Lily is correct; the second sentence repeats the same point.
- **s000014:q4 (7/9): What happened at the end?** Answer: The kite danced in the sky. It could fly again. Luna: The kite danced in the sky; that it could fly again is not stated.
- **s000028:q1 (7/9): Who wanted to solve the problem?** Answer: Ben wanted to solve it. Ben wanted to repair the kite. Luna: Ben is correct; the second sentence repeats the same point.

### key

- **s000014:q1 (7/9): Who wanted to solve the problem?** Answer: Lily wanted to solve it. Lily wanted to find the key. Luna: Correctly names Lily, but repeats the same idea in two sentences.
- **s000014:q2 (7/9): Where was the lantern?** Answer: The lantern was on the porch. Dad told Lily where to find it. Luna: Correct location; the second sentence merely repeats that Dad told her.
- **s000014:q4 (7/9): What happened at the end?** Answer: Lily stepped through the door. The door was open. Luna: Accurate ending, with the second sentence restating that the door was open.

### music

- **s000014:q0 (5/9): Whose choice did Nia accept?** Answer: Nia accepted Mateo's choice. She left the decision to him. Luna: The story says Nia accepted Mateo's choice, but not that she left the decision to him.
- **s000014:q2 (5/9): How did Nia perform her solo?** Answer: Nia performed the solo on a drum. She performed on her own. Luna: The little drum is stated; performing alone is not.
- **s000014:q3 (5/9): Where were the instruments at the end?** Answer: Both drums were on the shelf. Neither character was holding a drum then. Luna: The drums are on the shelf, but the text does not say neither character was holding one.

### greenhouse

- **s000014:q1 (7/9): Who explained the problem with the tap?** Answer: Mr Bell said the tap was broken. He told Nia. Luna: Mr Bell is identified as the person who said the tap was broken; the second sentence is redundant.
- **s000014:q2 (7/9): How did Nia water the seedlings?** Answer: Nia used the watering can. She watered the tomato seedlings with it. Luna: The watering can and tomato seedlings are supported, though the answer repeats the same fact.
- **s000014:q5 (7/9): How did Nia protect the seedlings after the cloth fell?** Answer: Nia secured an umbrella above the seedlings. She used a garden tie. Luna: It gives the umbrella and garden tie used to protect them.

### library

- **s000014:q0 (8/9): Why did Mina put her atlas back?** Answer: Mina chose to help Jun. She returned the atlas to the display table. Luna: The story links Mina returning the atlas with choosing to help Jun.
- **s000014:q1 (8/9): What did Mina want to do?** Answer: Mina wanted to sketch craters. She held a moon atlas. Luna: Both the sketching goal and atlas are directly stated.
- **s000014:q2 (8/9): Who promised to help Jun?** Answer: Mina promised to help Jun. Jun had said his whale book was missing. Luna: Mina makes the promise; the added context is also supported.

### pottery

- **s000014:q0 (2/9): How did Bea use the dent?** Answer: Bea shaped a thumb rest. She used the sponge. Luna: The story says Bea made a thumb rest, not that she used the dent to make it.
- **s000058:q0 (2/9): How did Bea use the dent?** Answer: Bea shaped a thumb rest. She used the sponge. Luna: The story says Bea made a thumb rest, not that she used the dent to make it.
- **s000023:q0 (2/9): How did Bea use the dent?** Answer: Bea shaped a thumb rest. She used the sponge. Luna: The story says Bea shaped a thumb rest, not that she used the dent to make it.

## Limits

One Luna judgment per set; scores are diagnostic, not human-validated guarantees. QA scores use a new rubric and are not comparable to the literary score. Repeated templates are correlated: many flagged pairs can reflect one recurring defect. Earlier runs use different samples and versions, so no causal before/after improvement is claimed. Present-tense outputs were mechanically checked earlier but are not included in this model evaluation. No story rules were changed during evaluation.

[Detailed prose ratings and plot groups](prose_ratings.md). Raw requests, responses, selected text, QA, usage and source snapshots are retained.
