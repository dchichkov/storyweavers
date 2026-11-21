# Luna: short stories and reading QA

6 randomly selected past-tense stories per world; duplicates retained. Luna / Flex / reasoning none. Prose uses the unchanged calibrated 0–9 story-set rubric; QA is a separate text-only judgment. No hidden state or reference story is given to either judge.

| World | Story quality / 9 | Diversity / 9 | QA quality / 9 | Grounded answers | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| rescue | 6.00 | 1 | 8.83 | 36/36 | 36/36 |
| kite | 6.00 | 1 | 7.80 | 30/30 | 30/30 |
| key | 6.00 | 1 | 8.83 | 36/36 | 36/36 |
| music | 5.00 | 2 | 8.58 | 33/33 | 33/33 |
| greenhouse | 5.00 | 1 | 8.33 | 36/36 | 36/36 |
| library | 6.00 | 1 | 8.08 | 36/36 | 36/36 |
| pottery | 6.00 | 2 | 8.00 | 36/36 | 36/36 |

Complete: True. 42 stories and 243 QA pairs judged.

## QA defects

{
  "awkward_answer": 7,
  "too_shallow": 24,
  "missing_causality": 3
}

## Representative QA findings

### rescue

- **s000014:q3 (8/9): How was the problem solved?** Answer: Lily lifted the rabbit down with the ladder. The rabbit had been stranded on a high ledge. Luna: The ladder is used to lift the rabbit down; the added high-ledge detail is supported.
- **s000028:q3 (8/9): How was the problem solved?** Answer: Lily lifted the rabbit down with the ladder. The rabbit had been stranded on a high ledge. Luna: The ladder is used to lift the rabbit down; the added high-ledge detail is supported.
- **s000058:q3 (8/9): How was the problem solved?** Answer: Sam lifted the rabbit down with the ladder. The rabbit had been stranded on a high ledge. Luna: The ladder is used to lift the rabbit down; the added high-ledge detail is supported.

### kite

- **s000014:q3 (7/9): How was the problem solved?** Answer: Lily repaired the kite with tape. The kite had been torn. Luna: The answer gives the tape repair method, though the torn-kite detail is padding.
- **s000028:q3 (7/9): How was the problem solved?** Answer: Lily repaired the kite with tape. The kite had been torn. Luna: The answer gives the tape repair method, though the torn-kite detail is padding.
- **s000058:q3 (7/9): How was the problem solved?** Answer: Sam repaired the kite with tape. The kite had been torn. Luna: The repair method is correct; the torn-kite detail repeats known context.

### key

- **s000014:q3 (8/9): How was the problem solved?** Answer: Lily found the key under the bench with the lantern. The missing key had kept the door locked. Luna: The answer gives the key's location and connects the missing key to the locked door.
- **s000028:q3 (8/9): How was the problem solved?** Answer: Lily found the key under the bench with the lantern. The missing key had kept the door locked. Luna: The answer gives the key's location and connects the missing key to the locked door.
- **s000058:q3 (8/9): How was the problem solved?** Answer: Sam found the key under the bench with the lantern. The missing key had kept the door locked. Luna: Sam finds the key under the bench; the added sentence appropriately links the missing key and locked door.

### music

- **s000014:q4 (7/9): What did Nia choose to perform?** Answer: Nia chose to perform a solo. Mateo had said he was not ready. Luna: The solo is correct, but the added sentence about Mateo is unnecessary to the question.
- **s000028:q5 (7/9): What did Nia choose to perform?** Answer: Nia chose to perform a solo. Mateo had said he was not ready. Luna: The solo is correct, but the added sentence is not needed to answer what she chose.
- **s000058:q4 (7/9): What did Nia choose to perform?** Answer: Nia chose to perform a solo. Mateo had said he was not ready. Luna: It gives the correct choice but adds an unnecessary detail about Mateo.

### greenhouse

- **s000014:q2 (7/9): How did Nia water the seedlings?** Answer: Nia watered the tomato seedlings with the watering can. The tap was broken. Luna: The watering-can method is correct; the added broken-tap fact is irrelevant padding.
- **s000028:q2 (7/9): How did Nia water the seedlings?** Answer: Nia watered the tomato seedlings with the watering can. The tap was broken. Luna: The watering-can method is correct; the added broken-tap fact is irrelevant padding.
- **s000058:q2 (7/9): How did Nia water the seedlings?** Answer: Nia watered the tomato seedlings with the watering can. The tap was broken. Luna: The watering-can method is correct; the added broken-tap fact is irrelevant padding.

### library

- **s000058:q0 (6/9): Why did Mina put her atlas back?** Answer: Mina chose to help Jun. She returned the atlas to the display table. Luna: The story says she returned the atlas and chose to help, but does not explicitly say helping was why she put it back.
- **s000023:q0 (6/9): Why did Mina put her atlas back?** Answer: Mina chose to help Jun. She returned the atlas to the display table. Luna: The story says she returned the atlas and chose to help, but does not explicitly say helping was why she put it back.
- **s000017:q0 (6/9): Why did Mina put her atlas back?** Answer: Mina chose to help Jun. She returned the atlas to the display table. Luna: The story says she returned the atlas and chose to help, but does not explicitly say helping was why she put it back.

### pottery

- **s000014:q0 (7/9): How did Bea change the dent?** Answer: Bea smoothed the dent with the sponge. Mr Ivo had said the cup's wall was thick. Luna: The smoothing answer is correct; the wall-thickness sentence is unrelated padding.
- **s000014:q3 (7/9): What happened when the shaping rib slipped?** Answer: The shaping rib slipped. The cup was dented. Luna: Accurate, but repeats the question’s setup before stating the cup was dented.
- **s000014:q4 (7/9): How did Grandpa Len hold the cup at the end?** Answer: Grandpa Len held the cup's wide handle. Bea had made the cup for him because his hand was stiff. Luna: The handle answer is correct; the added explanation repeats information not needed to answer.

## Limits

One Luna judgment per set; scores are diagnostic, not human-validated guarantees. QA scores use a new rubric and are not comparable to the literary score. Repeated templates are correlated: many flagged pairs can reflect one recurring defect. Earlier runs use different samples and versions, so no causal before/after improvement is claimed. Present-tense outputs were mechanically checked earlier but are not included in this model evaluation. No story rules were changed during evaluation.

[Detailed prose ratings and plot groups](report.md). Raw requests, responses, selected text, QA, usage and source snapshots are retained.
