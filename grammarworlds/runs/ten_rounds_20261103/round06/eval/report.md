# Luna: short stories and reading QA

12 randomly selected past-tense stories per world; duplicates retained. Luna / Flex / reasoning none. Prose uses the unchanged calibrated 0–9 story-set rubric; QA is a separate text-only judgment. No hidden state or reference story is given to either judge.

| World | Story quality / 9 | Diversity / 9 | QA quality / 9 | Grounded answers | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| greenhouse | 6.00 | 2 | 8.07 | 72/72 | 72/72 |

Complete: True. 12 stories and 72 QA pairs judged.

## QA defects

{}

## Representative QA findings

### greenhouse

- **s000014:q4 (7/9): What did Nia use to water the plants?** Answer: Nia used the watering can to water the sunflower. Luna: The watering can is correct, though the question asks about plants plural and the answer mentions only the sunflower.
- **s000014:q5 (7/9): Why did Nia secure an umbrella above the seedlings?** Answer: The shade cloth had fallen. Nia secured an umbrella above the seedlings with a garden tie. Luna: The fallen shade cloth gives a reasonable cause for securing the umbrella, though the answer mostly repeats events.
- **s000028:q0 (7/9): How were the plants protected at the end?** Answer: The tomato seedlings and sunflower stood under the umbrella. Nia had divided the water equally between them. Luna: Correctly says both plants ended under the umbrella; the added water detail is true but not needed.

## Limits

One Luna judgment per set; scores are diagnostic, not human-validated guarantees. QA scores use a new rubric and are not comparable to the literary score. Repeated templates are correlated: many flagged pairs can reflect one recurring defect. Earlier runs use different samples and versions, so no causal before/after improvement is claimed. Present-tense outputs were mechanically checked earlier but are not included in this model evaluation. No story rules were changed during evaluation.

[Detailed prose ratings and plot groups](report.md). Raw requests, responses, selected text, QA, usage and source snapshots are retained.
