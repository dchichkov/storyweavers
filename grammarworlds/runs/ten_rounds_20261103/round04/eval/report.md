# Luna: short stories and reading QA

12 randomly selected past-tense stories per world; duplicates retained. Luna / Flex / reasoning none. Prose uses the unchanged calibrated 0–9 story-set rubric; QA is a separate text-only judgment. No hidden state or reference story is given to either judge.

| World | Story quality / 9 | Diversity / 9 | QA quality / 9 | Grounded answers | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| key | 5.75 | 1 | 7.83 | 72/72 | 72/72 |

Complete: True. 12 stories and 72 QA pairs judged.

## QA defects

{
  "too_shallow": 12
}

## Representative QA findings

### key

- **s000014:q1 (7/9): Who wanted to read inside?** Answer: Lily wanted to read a storybook inside. The door was locked. Luna: Lily is identified correctly, but the extra locked-door detail does not add much.
- **s000028:q1 (7/9): Who wanted to read inside?** Answer: Lily wanted to read a storybook inside. The door was locked. Luna: Lily is identified correctly, but the extra locked-door detail does not add much.
- **s000058:q1 (7/9): Who wanted to read inside?** Answer: Sam wanted to read a storybook inside. The door was locked. Luna: Sam is identified correctly, but the extra locked-door detail does not add much.

## Limits

One Luna judgment per set; scores are diagnostic, not human-validated guarantees. QA scores use a new rubric and are not comparable to the literary score. Repeated templates are correlated: many flagged pairs can reflect one recurring defect. Earlier runs use different samples and versions, so no causal before/after improvement is claimed. Present-tense outputs were mechanically checked earlier but are not included in this model evaluation. No story rules were changed during evaluation.

[Detailed prose ratings and plot groups](report.md). Raw requests, responses, selected text, QA, usage and source snapshots are retained.
