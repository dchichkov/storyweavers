# Luna: short stories and reading QA

12 randomly selected past-tense stories per world; duplicates retained. Luna / Flex / reasoning none. Prose uses the unchanged calibrated 0–9 story-set rubric; QA is a separate text-only judgment. No hidden state or reference story is given to either judge.

| World | Story quality / 9 | Diversity / 9 | QA quality / 9 | Grounded answers | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| rescue | 7.00 | 2 | 7.89 | 36/36 | 36/36 |

Complete: True. 12 stories and 36 QA pairs judged.

## QA defects

{
  "too_shallow": 4
}

## Representative QA findings

### rescue

- **s000003:q5 (7/9): Why did Sam wait?** Answer: The kitten was frightened. Sam waited. Luna: Correct, but repeats the reason and action rather than explaining further.
- **s000009:q5 (7/9): Why did Ben wait?** Answer: The puppy was frightened. Ben waited. Luna: The reason is correct, but the second clause simply restates the question.
- **s000029:q5 (7/9): Why did Lily wait?** Answer: The rabbit was frightened. Lily waited. Luna: Correctly gives the reason, then merely repeats that Lily waited.

## Separately sampled QA follow-ups

- rescue: The original 12-story QA call timed out with an uncertain server outcome and was not resent. This diagnostic uses six uniformly selected, previously unselected stories from the same frozen pool (seed 778). Prose still uses the original 12-story sample; QA uses these six stories. Inputs and responses: rescue/qa_followup/.

## Limits

One Luna judgment per set; scores are diagnostic, not human-validated guarantees. QA scores use a new rubric and are not comparable to the literary score. Repeated templates are correlated: many flagged pairs can reflect one recurring defect. Earlier runs use different samples and versions, so no causal before/after improvement is claimed. Present-tense outputs were mechanically checked earlier but are not included in this model evaluation. No story rules were changed during evaluation.

[Detailed prose ratings and plot groups](report.md). Raw requests, responses, selected text, QA, usage and source snapshots are retained.
