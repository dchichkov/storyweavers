# Luna: short stories and reading QA

20 randomly selected past-tense stories per world, from 60 positions; duplicates retained. Luna / Flex / reasoning none. Prose uses the unchanged calibrated 0–9 story-set rubric; QA is a separate text-only judgment. No hidden state or reference story is given to either judge.

| World | Story quality / 9 | Diversity / 9 | QA quality / 9 | Grounded answers | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| rescue | 6.00 | 1 | 7.33 | 120/120 | 120/120 |
| kite | 6.00 | 1 | 7.20 | 80/100 | 80/100 |
| key | 5.00 | 0 | 7.82 | 110/120 | 110/120 |
| music | 5.00 | 2 | 6.64 | 47/115 | 47/115 |
| greenhouse | 5.00 | 0 | 7.67 | 120/120 | 120/120 |
| library | 6.00 | 1 | 7.91 | 120/120 | 120/120 |
| pottery | 6.00 | 1 | 6.46 | 71/120 | 71/120 |

Complete: True. 140 stories and 815 QA pairs judged.

## QA defects

{
  "too_shallow": 249,
  "ungrounded_answer": 148,
  "bad_evidence": 68,
  "awkward_answer": 40,
  "not_answerable": 9
}

## Representative QA findings

### rescue

- **s000014:q1 (7/9): Who wanted to solve the problem?** Answer: Lily wanted to solve it. Lily wanted to rescue the rabbit. Luna: Correctly identifies Lily; the second sentence repeats the same point.
- **s000014:q2 (7/9): Where was the ladder?** Answer: The ladder was in the shed. Dad told Lily where to find it. Luna: The shed is correct; the extra sentence merely repeats that Dad gave the information.
- **s000014:q3 (7/9): How was the problem solved?** Answer: Lily used the ladder. Lily lifted the rabbit down. Luna: Correctly explains the rescue; the two sentences repeat the same action.

### kite

- **s000014:q4 (6/9): What happened at the end?** Answer: The kite danced in the sky. It could fly again. Luna: The kite dancing in the sky is supported, but that it could fly again is not stated.
- **s000028:q4 (6/9): What happened at the end?** Answer: The kite danced in the sky. It could fly again. Luna: The kite dancing in the sky is supported, but that it could fly again is not stated.
- **s000058:q4 (6/9): What happened at the end?** Answer: The kite danced in the sky. It could fly again. Luna: The kite dancing in the sky is supported, but that it could fly again is not stated.

### key

- **s000028:q3 (4/9): How was the problem solved?** Answer: Lily used a lantern. Lily found the key under the bench. Luna: The story says Lily found the key with the lantern, not that she used the lantern.
- **s000023:q3 (4/9): How was the problem solved?** Answer: Nora used a lantern. Nora found the key under the bench. Luna: The story says Nora found the key with the lantern, not that she used the lantern.
- **s000036:q3 (4/9): How was the problem solved?** Answer: Nora used a lantern. Nora found the key under the bench. Luna: The story says Nora found the key with the lantern, not that she used the lantern.

### music

- **s000014:q3 (5/9): Where were the instruments at the end?** Answer: Both drums were on the shelf. Neither character was holding a drum then. Luna: Both drums were on the shelf; the text does not say neither character was holding one.
- **s000028:q3 (5/9): Where were the instruments at the end?** Answer: Both drums were on the shelf. Neither character was holding a drum then. Luna: The shelf location is supported, but the claim about neither character holding a drum is not.
- **s000058:q3 (5/9): Where were the instruments at the end?** Answer: Both drums were on the shelf. Neither character was holding a drum then. Luna: The drums were on the shelf; their not being held is an unsupported addition.

### greenhouse

- **s000014:q1 (7/9): Who explained the problem with the tap?** Answer: Mr Bell said the tap was broken. He told Nia. Luna: Mr Bell is identified correctly; the second sentence merely repeats the exchange.
- **s000014:q2 (7/9): How did Nia water the seedlings?** Answer: Nia used the watering can. She watered the tomato seedlings with it. Luna: The watering-can detail is correct, but the second sentence repeats it.
- **s000028:q1 (7/9): Who explained the problem with the tap?** Answer: Mr Bell said the tap was broken. He told Nia. Luna: Mr Bell is identified correctly; the second sentence merely repeats the exchange.

### library

- **s000058:q0 (7/9): Why did Mina put her atlas back?** Answer: Mina chose to help Jun. She returned the atlas to the display table. Luna: The text links returning the atlas with choosing to help Jun, though the causal link is implicit.
- **s000023:q0 (7/9): Why did Mina put her atlas back?** Answer: Mina chose to help Jun. She returned the atlas to the display table. Luna: The text links returning the atlas with choosing to help Jun, though the causal link is implicit.
- **s000017:q0 (7/9): Why did Mina put her atlas back?** Answer: Mina chose to help Jun. She returned the atlas to the display table. Luna: The text links returning the atlas with choosing to help Jun, though the causal link is implicit.

### pottery

- **s000023:q0 (3/9): How did Bea use the dent?** Answer: Bea shaped a thumb rest. She used the sponge. Luna: The story does not establish that the thumb rest was made from or used the dent.
- **s000036:q0 (3/9): How did Bea use the dent?** Answer: Bea shaped a thumb rest. She used the sponge. Luna: The story does not establish that the thumb rest was made from or used the dent.
- **s000048:q0 (3/9): How did Bea use the dent?** Answer: Bea shaped a thumb rest. She used the sponge. Luna: The story does not establish that the thumb rest was made from or used the dent.

## Limits

One Luna judgment per set; scores are diagnostic, not human-validated guarantees. QA scores use a new rubric and are not comparable to the literary score. Repeated templates are correlated: many flagged pairs can reflect one recurring defect. Earlier runs use different samples and versions, so no causal before/after improvement is claimed. Present-tense outputs were mechanically checked earlier but are not included in this model evaluation. No story rules were changed during evaluation.

[Detailed prose ratings and plot groups](report.md). Raw requests, responses, selected text, QA, usage and source snapshots are retained.
