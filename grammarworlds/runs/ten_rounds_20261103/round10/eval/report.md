# Luna: short stories and reading QA

20 randomly selected past-tense stories per world; duplicates retained. Luna / Flex / reasoning none. Prose uses the unchanged calibrated 0–9 story-set rubric; QA is a separate text-only judgment. No hidden state or reference story is given to either judge.

| World | Story quality / 9 | Diversity / 9 | QA quality / 9 | Grounded answers | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| rescue | 7.00 | 2 | 8.17 | 120/120 | 120/120 |
| kite | 7.20 | 3 | 8.12 | 120/120 | 120/120 |
| key | 6.00 | 2 | 7.83 | 120/120 | 120/120 |
| music | 7.00 | 2 | 7.24 | 120/120 | 120/120 |
| greenhouse | 5.80 | 2 | 7.53 | 120/120 | 120/120 |
| library | 6.00 | 2 | 8.07 | 120/120 | 120/120 |
| pottery | 7.00 | 2 | 7.67 | 120/120 | 120/120 |

Complete: True. 140 stories and 840 QA pairs judged.

## QA defects

{
  "too_shallow": 159,
  "wrong_focus": 4
}

## Representative QA findings

### rescue

- **s000014:q0 (7/9): Why was Lily hungry at the end?** Answer: The rabbit ate the bread that Lily had meant to eat. It rested in the warm blanket after the rescue. Luna: The rabbit ate Lily's intended bread; the blanket detail does not explain her hunger.
- **s000028:q0 (7/9): Why was Lily hungry at the end?** Answer: The rabbit ate the bread that Lily had meant to eat. It rested in the warm blanket after the rescue. Luna: The rabbit ate Lily's intended bread; the blanket detail does not explain her hunger.
- **s000058:q0 (7/9): Why was Sam hungry at the end?** Answer: The rabbit ate the bread that Sam had meant to eat. It rested in the warm blanket after the rescue. Luna: The rabbit ate Sam's intended bread; the blanket detail does not explain his hunger.

### kite

- **s000014:q0 (7/9): What did they watch at the end?** Answer: Lily and Dad watched the patched kite dancing above the meadow. The tape had covered its tear. Luna: The tape detail is unnecessary padding beyond what they watched.
- **s000014:q1 (7/9): Who wanted to fly the kite?** Answer: Lily wanted to fly the kite. The kite was torn. Luna: The extra torn-kite detail is not needed to identify Lily.
- **s000028:q0 (7/9): What did they watch at the end?** Answer: Lily and Dad watched the patched kite dancing above the meadow. The tape had covered its tear. Luna: The tape detail is unnecessary padding beyond what they watched.

### key

- **s000014:q1 (7/9): Who wanted to read inside?** Answer: Lily wanted to read a storybook inside. The door was locked. Luna: Correctly identifies Lily; the extra locked-door detail is relevant context.
- **s000028:q1 (7/9): Who wanted to read inside?** Answer: Lily wanted to read a storybook inside. The door was locked. Luna: Correctly identifies Lily; the extra locked-door detail is relevant context.
- **s000058:q1 (7/9): Who wanted to read inside?** Answer: Sam wanted to read a storybook inside. The door was locked. Luna: Correctly identifies Sam; the extra locked-door detail is relevant context.

### music

- **s000014:q0 (7/9): How did Mateo respond after Nia played?** Answer: Mateo clapped, and Nia bowed. Nia had performed before Dalia. Luna: Correct response, but the added performance detail is padding beyond how Mateo responded.
- **s000014:q1 (7/9): What did Nia hope to do?** Answer: Nia hoped to play a duet with Mateo. She borrowed the little drum from Dalia. Luna: Correctly states her hope; borrowing the drum is unrelated padding.
- **s000014:q3 (7/9): How did Nia prepare her solo?** Answer: Nia practiced a soft beat and a loud beat. She had chosen to perform a solo. Luna: The practiced beats answer how she prepared; the solo choice repeats context.

### greenhouse

- **s000028:q0 (6/9): What happened to the sunflower after it waited?** Answer: The sunflower was watered after Mr Bell repaired the tap. The tomato seedlings stood under the repaired shade cloth. Luna: It says the sunflower was watered after the tap repair, but adds unrelated detail about the seedlings' shade.
- **s000058:q0 (6/9): What did Nia promise after seeing the brown leaf?** Answer: Nia promised to water the tomato seedlings first tomorrow. The brown leaf remained under the repaired shade cloth. Luna: The promise is correct, but the second sentence merely repeats an unrelated ending detail.
- **s000023:q0 (6/9): What did Nia promise after seeing the brown leaf?** Answer: Nia promised to water the tomato seedlings first tomorrow. The brown leaf remained under the repaired shade cloth. Luna: It gives the promise, then adds a redundant detail about the brown leaf.

### library

- **s000014:q1 (8/9): How did Mina's drawing plan turn out?** Answer: Mina showed Jun her moon drawing. Ms Alvarez had reserved the atlas for her. Luna: Reports the completed moon drawing and the atlas reservation.
- **s000014:q2 (8/9): What did Mina want to do?** Answer: Mina wanted to sketch the moon. She held a moon atlas. Luna: Correctly states Mina's goal and adds the relevant atlas detail.
- **s000014:q3 (8/9): Where did the children search without finding the book?** Answer: They did not find the book in the window nook. Mina and Jun searched there together. Luna: Identifies the window nook and says they did not find the book there.

### pottery

- **s000014:q0 (7/9): How did Bea use the dent after Mr Ivo checked the cup?** Answer: Bea shaped the dent into a thumb rest with the sponge. Mr Ivo had said the cup's wall was thick. Luna: The dent becomes a thumb rest; the extra wall-thickness detail is supported.
- **s000014:q1 (7/9): Where did Grandpa Len rest his thumb?** Answer: Grandpa Len rested his thumb in the thumb rest. Bea had shaped the dent into that thumb rest. Luna: Correctly identifies the thumb rest and its origin.
- **s000028:q0 (7/9): How did Bea use the dent after Mr Ivo checked the cup?** Answer: Bea shaped the dent into a thumb rest with the sponge. Mr Ivo had said the cup's wall was thick. Luna: The dent becomes a thumb rest; the extra wall-thickness detail is supported.

## Separately sampled QA follow-ups

- kite: Original response hit its output-token limit (terminal, no valid assessment). The identical stories, QA, rubric and schema were repeated with a 40,000-token cap; original request/response remain unchanged. This is not a new sample or a score-selected retry. Inputs and responses: kite/qa_output_recovery/.

## Limits

One Luna judgment per set; scores are diagnostic, not human-validated guarantees. QA scores use a new rubric and are not comparable to the literary score. Repeated templates are correlated: many flagged pairs can reflect one recurring defect. Earlier runs use different samples and versions, so no causal before/after improvement is claimed. Present-tense outputs were mechanically checked earlier but are not included in this model evaluation. No story rules were changed during evaluation.

[Detailed prose ratings and plot groups](prose_ratings.md). Raw requests, responses, selected text, QA, usage and source snapshots are retained.
