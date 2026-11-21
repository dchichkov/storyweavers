# Luna: short stories and reading QA

12 randomly selected past-tense stories per world; duplicates retained. Luna / Flex / reasoning none. Prose uses the unchanged calibrated 0–9 story-set rubric; QA is a separate text-only judgment. No hidden state or reference story is given to either judge.

| World | Story quality / 9 | Diversity / 9 | QA quality / 9 | Grounded answers | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| library | 5.00 | 2 | 7.81 | 72/72 | 72/72 |

Complete: True. 12 stories and 72 QA pairs judged.

## QA defects

{}

## Representative QA findings

### library

- **s000014:q4 (7/9): How did they get the whale book down?** Answer: Ms Alvarez lifted the whale book down with a ladder. Jun had spotted a star bookmark on the high shelf. Luna: The ladder brought the book down; the bookmark detail is supported but unnecessary.
- **s000028:q0 (7/9): Why did Mina put her atlas back?** Answer: Mina chose to help Jun. She returned the atlas to the display table. Luna: Connects returning the atlas with choosing to help Jun, though the motive is implicit.
- **s000028:q5 (7/9): How did they get the whale book down?** Answer: Ms Alvarez lifted the whale book down with a ladder. Jun had spotted a star bookmark on the high shelf. Luna: Correctly says Ms Alvarez used a ladder; the bookmark detail is extraneous.

## Limits

One Luna judgment per set; scores are diagnostic, not human-validated guarantees. QA scores use a new rubric and are not comparable to the literary score. Repeated templates are correlated: many flagged pairs can reflect one recurring defect. Earlier runs use different samples and versions, so no causal before/after improvement is claimed. Present-tense outputs were mechanically checked earlier but are not included in this model evaluation. No story rules were changed during evaluation.

[Detailed prose ratings and plot groups](report.md). Raw requests, responses, selected text, QA, usage and source snapshots are retained.
