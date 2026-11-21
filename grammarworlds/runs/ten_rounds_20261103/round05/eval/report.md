# Luna: short stories and reading QA

12 randomly selected past-tense stories per world; duplicates retained. Luna / Flex / reasoning none. Prose uses the unchanged calibrated 0–9 story-set rubric; QA is a separate text-only judgment. No hidden state or reference story is given to either judge.

| World | Story quality / 9 | Diversity / 9 | QA quality / 9 | Grounded answers | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| music | 7.00 | 2 | 7.21 | 68/72 | 68/72 |

Complete: True. 12 stories and 72 QA pairs judged.

## QA defects

{
  "too_shallow": 26,
  "ungrounded_answer": 8,
  "not_answerable": 3
}

## Representative QA findings

### music

- **s000017:q3 (3/9): Why did Nia need to change her plan?** Answer: Mateo said he was not ready for the audience. Nia had hoped to play a duet with him. Luna: The story does not say Nia changed her plan; Mateo wanted to play privately, and they did.
- **s000021:q3 (3/9): Why did Nia need to change her plan?** Answer: Mateo said he was not ready for the audience. Nia had hoped to play a duet with him. Luna: Mateo’s audience reluctance is stated, but the story does not say Nia changed her plan.
- **s000034:q3 (3/9): Why did Nia need to change her plan?** Answer: Mateo said he was not ready for the audience. Nia had hoped to play a duet with him. Luna: Although Mateo says he is not ready, the story does not say Nia changed her plan.

## Limits

One Luna judgment per set; scores are diagnostic, not human-validated guarantees. QA scores use a new rubric and are not comparable to the literary score. Repeated templates are correlated: many flagged pairs can reflect one recurring defect. Earlier runs use different samples and versions, so no causal before/after improvement is claimed. Present-tense outputs were mechanically checked earlier but are not included in this model evaluation. No story rules were changed during evaluation.

[Detailed prose ratings and plot groups](report.md). Raw requests, responses, selected text, QA, usage and source snapshots are retained.
