# Luna: short stories and reading QA

12 randomly selected past-tense stories per world; duplicates retained. Luna / Flex / reasoning none. Prose uses the unchanged calibrated 0–9 story-set rubric; QA is a separate text-only judgment. No hidden state or reference story is given to either judge.

| World | Story quality / 9 | Diversity / 9 | QA quality / 9 | Grounded answers | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| kite | 7.00 | 3 | 7.56 | 51/72 | 51/72 |

Complete: True. 12 stories and 72 QA pairs judged.

## QA defects

{
  "ungrounded_answer": 21
}

## Representative QA findings

### kite

- **s000014:q1 (6/9): Who wanted to fly the kite?** Answer: Lily wanted to fly the kite. Its paper was torn. Luna: Lily is correct, but the story does not say the kite was made of paper.
- **s000028:q1 (6/9): Who wanted to fly the kite?** Answer: Lily wanted to fly the kite. Its paper was torn. Luna: Lily is correct, but the story does not say the kite was made of paper.
- **s000058:q0 (6/9): What happened to the torn kite at the end?** Answer: Its paper became the sail on a boat. Sam and Mum watched the boat sail away. Luna: The kite is used as sail material, but the boat sails across the pond rather than sailing away.

## Limits

One Luna judgment per set; scores are diagnostic, not human-validated guarantees. QA scores use a new rubric and are not comparable to the literary score. Repeated templates are correlated: many flagged pairs can reflect one recurring defect. Earlier runs use different samples and versions, so no causal before/after improvement is claimed. Present-tense outputs were mechanically checked earlier but are not included in this model evaluation. No story rules were changed during evaluation.

[Detailed prose ratings and plot groups](report.md). Raw requests, responses, selected text, QA, usage and source snapshots are retained.
