# Luna: short stories and reading QA

10 randomly selected past-tense stories per world; duplicates retained. Luna / Flex / reasoning none. Prose uses the unchanged calibrated 0–9 story-set rubric; QA is a separate text-only judgment. No hidden state or reference story is given to either judge.

| World | Story quality / 9 | Diversity / 9 | QA quality / 9 | Grounded answers | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| rescue | 7.00 | 2 | 8.02 | 60/60 | 60/60 |
| kite | 7.20 | 3 | 7.37 | 55/60 | 48/60 |
| key | 7.00 | 2 | 8.15 | 60/60 | 60/60 |
| music | 6.00 | 2 | 6.58 | 50/60 | 50/60 |
| greenhouse | 5.60 | 2 | 8.17 | 60/60 | 60/60 |
| library | 6.50 | 2 | 7.92 | 60/60 | 60/60 |
| pottery | 6.00 | 2 | 8.75 | 60/60 | 60/60 |

Complete: True. 70 stories and 420 QA pairs judged.

## QA defects

{
  "too_shallow": 19,
  "ungrounded_answer": 7,
  "bad_evidence": 7,
  "missing_causality": 15,
  "not_answerable": 10
}

## Representative QA findings

### rescue

- **s000014:q5 (7/9): Why did Lily wait?** Answer: The rabbit was frightened. Lily waited. Luna: The reason is correct, but the second sentence merely repeats that Lily waited.
- **s000028:q5 (7/9): Why did Lily wait?** Answer: The rabbit was frightened. Lily waited. Luna: The reason is correct, but the second sentence merely repeats that Lily waited.
- **s000058:q5 (7/9): Why did Sam wait?** Answer: The rabbit was frightened. Sam waited. Luna: The reason is correct, but the second sentence merely repeats that Sam waited.

### kite

- **s000058:q3 (4/9): Why did Sam choose a different use for the paper?** Answer: The kite was torn. Sam wanted to make a sail from its paper. Luna: It gives the torn kite and Sam's intention, but does not explain why that led him to choose another use.
- **s000023:q3 (4/9): Why did Nora choose a different use for the paper?** Answer: The kite was torn. Nora wanted to make a sail from its paper. Luna: The answer gives Nora's plan and the kite's condition but does not explain why she chose the different use.
- **s000053:q3 (4/9): Why did Sam choose a different use for the paper?** Answer: The kite was torn. Sam wanted to make a sail from its paper. Luna: It states that the kite was torn and Sam wanted a sail, but does not explain why he chose that alternative.

### key

- **s000014:q3 (7/9): Where was the lantern?** Answer: Lily fetched the lantern from the porch. Luna: The answer gives the porch as the lantern’s source, though the question asks where it was.
- **s000028:q3 (7/9): Where was the lantern?** Answer: Lily fetched the lantern from the porch. Luna: The answer gives the porch as the lantern’s source, though the question asks where it was.
- **s000058:q3 (7/9): Where was the lantern?** Answer: Sam fetched the lantern from the porch. Luna: The answer gives the porch as the lantern’s source, though the question asks where it was.

### music

- **s000014:q3 (3/9): Why was Mateo unwilling to play for an audience?** Answer: Mateo said he was not ready for the audience. Nia had hoped to play a duet with him. Luna: The story says Mateo was not ready for an audience but does not explain why.
- **s000028:q3 (3/9): Why was Mateo unwilling to play for an audience?** Answer: Mateo said he was not ready for the audience. Nia had hoped to play a duet with him. Luna: The story says Mateo was not ready for an audience but does not explain why.
- **s000058:q3 (3/9): Why was Mateo unwilling to play for an audience?** Answer: Mateo said he was not ready for the audience. Nia had hoped to play a duet with him. Luna: The story says Mateo was not ready for an audience but does not explain why.

### greenhouse

- **s000014:q0 (7/9): What was still damaged at the end?** Answer: A leaf was still brown, although the seedlings stood under the repaired shade cloth. Nia had watered the sunflower first. Luna: Correctly identifies the brown leaf; the added details are supported but not needed.
- **s000014:q5 (7/9): Why did Nia secure an umbrella above the seedlings?** Answer: The shade cloth had fallen. Nia secured an umbrella above the seedlings with a garden tie. Luna: The fallen shade cloth is a clear reason for the umbrella; the answer repeats the action.
- **s000028:q0 (7/9): How were the plants protected at the end?** Answer: The tomato seedlings and sunflower stood under the umbrella. Nia had divided the water equally between them. Luna: The answer states both plants were under the umbrella, though the water-sharing detail is extra.

### library

- **s000014:q4 (7/9): How did they get the whale book down?** Answer: Ms Alvarez lifted the whale book down with a ladder. Jun had spotted a star bookmark on the high shelf. Luna: Correctly says Ms Alvarez used a ladder; the bookmark detail is extra but supported.
- **s000028:q5 (7/9): How did they get the whale book down?** Answer: Ms Alvarez lifted the whale book down with a ladder. Jun had spotted a star bookmark on the high shelf. Luna: Correctly says Ms Alvarez used a ladder; the high-shelf bookmark detail is supported.
- **s000058:q5 (7/9): How did they get the whale book down?** Answer: Ms Alvarez lifted the whale book down with a ladder. Jun had spotted a star bookmark on the high shelf. Luna: Correctly says Ms Alvarez used a ladder; the high-shelf bookmark detail is supported.

### pottery

- **s000014:q0 (8/9): How did Bea use the dent after Mr Ivo checked the cup?** Answer: Bea shaped the dent into a thumb rest with the sponge. Mr Ivo had said the cup's wall was thick. Luna: Directly answers how the dent became a thumb rest; the wall comment is extra but supported.
- **s000014:q1 (8/9): Where did Grandpa Len rest his thumb?** Answer: Grandpa Len rested his thumb in the thumb rest. Bea had shaped the dent into that thumb rest. Luna: Identifies the thumb rest, with supported context about how Bea made it.
- **s000028:q0 (8/9): How did Bea use the dent after Mr Ivo checked the cup?** Answer: Bea shaped the dent into a thumb rest with the sponge. Mr Ivo had said the cup's wall was thick. Luna: Directly answers how the dent became a thumb rest; the wall comment is extra but supported.

## Limits

One Luna judgment per set; scores are diagnostic, not human-validated guarantees. QA scores use a new rubric and are not comparable to the literary score. Repeated templates are correlated: many flagged pairs can reflect one recurring defect. Earlier runs use different samples and versions, so no causal before/after improvement is claimed. Present-tense outputs were mechanically checked earlier but are not included in this model evaluation. No story rules were changed during evaluation.

[Detailed prose ratings and plot groups](prose_ratings.md). Raw requests, responses, selected text, QA, usage and source snapshots are retained.
