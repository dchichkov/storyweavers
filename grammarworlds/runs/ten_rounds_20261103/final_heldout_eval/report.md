# Luna: short stories and reading QA

20 randomly selected past-tense stories per world; duplicates retained. Luna / Flex / reasoning none. Prose uses the unchanged calibrated 0–9 story-set rubric; QA is a separate text-only judgment. No hidden state or reference story is given to either judge.

| World | Story quality / 9 | Diversity / 9 | QA quality / 9 | Grounded answers | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| rescue | 8.00 | 2 | 8.33 | 120/120 | 120/120 |
| kite | 7.00 | 3 | 7.47 | 105/120 | 105/120 |
| key | 6.00 | 1 | 8.56 | 120/120 | 120/120 |
| music | 7.00 | 2 | 7.24 | 120/120 | 120/120 |
| greenhouse | 5.20 | 2 | 7.62 | 120/120 | 120/120 |
| library | 6.00 | 1 | 8.29 | 120/120 | 120/120 |
| pottery | 7.00 | 2 | 7.67 | 120/120 | 120/120 |

Complete: True. 140 stories and 840 QA pairs judged.

## QA defects

{
  "too_shallow": 151,
  "ungrounded_answer": 15,
  "bad_evidence": 15
}

## Representative QA findings

### rescue

- **s000014:q0 (8/9): Why was Lily hungry at the end?** Answer: The kitten ate the bread that Lily had meant to eat. It rested in the warm blanket after the rescue. Luna: The bread-eating explains the hunger; the blanket-resting sentence adds unrelated padding.
- **s000014:q1 (8/9): What interrupted the meal?** Answer: A kitten was shivering on a high ledge. Lily wanted to eat the bread. Luna: Identifies the shivering kitten as interrupting Lily's intended meal.
- **s000014:q2 (8/9): Who noticed that the animal needed help?** Answer: Lily said the kitten needed help. Luna: Correctly identifies Lily as the one who said the kitten needed help.

### kite

- **s000014:q0 (5/9): What happened to the torn kite at the end?** Answer: Its paper became the sail on a boat. Lily and Dad watched the boat sail across the pond. Luna: The kite was cut into a sail, but the story does not say it was made of paper; the excerpts likewise do not support that claim.
- **s000028:q0 (5/9): What happened to the torn kite at the end?** Answer: Its paper became the sail on a boat. Ben and Mum watched the boat sail across the pond. Luna: The kite was cut into a sail, but the story does not say it was made of paper; the excerpts likewise do not support that claim.
- **s000058:q0 (5/9): What happened to the torn kite at the end?** Answer: Its paper became the sail on a boat. Nora and Dad watched the boat sail across the pond. Luna: The kite was cut into a sail, but the story does not say it was made of paper; the excerpts likewise do not support that claim.

### key

- **s000014:q0 (8/9): What changed by the end?** Answer: Lily opened the storybook beside Dad. The found key was on the hook. Luna: Covers the storybook and key's final locations.
- **s000014:q1 (8/9): Who wanted to read inside?** Answer: Lily wanted to read a storybook inside. The door was locked. Luna: Clearly identifies Lily; the extra locked-door detail is supported.
- **s000014:q4 (8/9): How was the missing key found?** Answer: Lily found it under the bench with the lantern. The lantern came from the porch. Luna: Says where and how the key was found; extra lantern origin is relevant.

### music

- **s000014:q0 (7/9): How did Mateo respond after Nia played?** Answer: Mateo clapped, and Nia bowed. Nia had performed before Dalia. Luna: Correctly gives Mateo’s clap; the added performance context is unnecessary.
- **s000014:q1 (7/9): What did Nia hope to do?** Answer: Nia hoped to play a duet with Mateo. She borrowed the little drum from Dalia. Luna: Correctly states her hope; the borrowed-drum detail is extra.
- **s000014:q3 (7/9): How did Nia prepare her solo?** Answer: Nia practiced a soft beat and a loud beat. She had chosen to perform a solo. Luna: Gives the practice details; the solo-choice sentence repeats context.

### greenhouse

- **s000014:q0 (7/9): What happened to the sunflower after it waited?** Answer: The sunflower was watered after Mr Bell repaired the tap. The tomato seedlings stood under the repaired shade cloth. Luna: The answer identifies the sunflower’s later watering; the seedlings detail is supported but not needed.
- **s000014:q1 (7/9): Who wanted to water the sunflower?** Answer: Nia wanted to water the sunflower. The tomato seedlings were thirsty too. Luna: Nia is clearly identified, with the seedlings’ thirst as a supported extra detail.
- **s000028:q0 (7/9): What did Nia promise after seeing the brown leaf?** Answer: Nia promised to water the tomato seedlings first tomorrow. The brown leaf remained under the repaired shade cloth. Luna: The promise is correct; the remaining brown leaf is an unnecessary but supported extra.

### library

- **s000014:q1 (8/9): How did Mina's drawing plan turn out?** Answer: Mina showed Jun her moon drawing. Ms Alvarez had reserved the atlas for her. Luna: It asks for the outcome, and the answer gives Mina's completed drawing and its display to Jun.
- **s000014:q2 (8/9): What did Mina want to do?** Answer: Mina wanted to sketch the moon. She held a moon atlas. Luna: Clearly answers Mina's plan; holding the atlas is an accurate, relevant extra detail.
- **s000014:q4 (8/9): How did they get the whale book down?** Answer: Ms Alvarez lifted the whale book down with a ladder. Jun had spotted a star bookmark on the high shelf. Luna: Correctly says Ms Alvarez used a ladder; the star-bookmark detail is supported but not needed.

### pottery

- **s000014:q0 (7/9): How did Bea use the dent after Mr Ivo checked the cup?** Answer: Bea shaped the dent into a thumb rest with the sponge. Mr Ivo had said the cup's wall was thick. Luna: Correctly identifies the thumb rest, but the wall-thickness sentence adds irrelevant padding.
- **s000014:q1 (7/9): Where did Grandpa Len rest his thumb?** Answer: Grandpa Len rested his thumb in the thumb rest. Bea had shaped the dent into that thumb rest. Luna: Correct location; the extra sentence about how the rest was made is redundant.
- **s000028:q0 (7/9): How did Bea change the dent after Mr Ivo checked the cup?** Answer: Bea smoothed the dent with the sponge. Mr Ivo had said the cup's wall was thick. Luna: Correctly says Bea smoothed the dent; the wall-thickness detail is irrelevant padding.

## Separately sampled QA follow-ups

- greenhouse: Original response hit its output-token limit (terminal, no valid assessment). The identical stories, QA, rubric and schema were repeated with a 40,000-token cap; original request/response remain unchanged. This is not a new sample or a score-selected retry. Inputs and responses: greenhouse/qa_output_recovery/.

## Limits

One Luna judgment per set; scores are diagnostic, not human-validated guarantees. QA scores use a new rubric and are not comparable to the literary score. Repeated templates are correlated: many flagged pairs can reflect one recurring defect. Earlier runs use different samples and versions, so no causal before/after improvement is claimed. Present-tense outputs were mechanically checked earlier but are not included in this model evaluation. No story rules were changed during evaluation.

[Detailed prose ratings and plot groups](prose_ratings.md). Raw requests, responses, selected text, QA, usage and source snapshots are retained.
