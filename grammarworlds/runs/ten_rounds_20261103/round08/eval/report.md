# Luna: short stories and reading QA

12 randomly selected past-tense stories per world; duplicates retained. Luna / Flex / reasoning none. Prose uses the unchanged calibrated 0–9 story-set rubric; QA is a separate text-only judgment. No hidden state or reference story is given to either judge.

| World | Story quality / 9 | Diversity / 9 | QA quality / 9 | Grounded answers | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| pottery | 7.00 | 2 | 8.00 | 72/72 | 72/72 |

Complete: True. 12 stories and 72 QA pairs judged.

## QA defects

{
  "too_shallow": 36
}

## Representative QA findings

### pottery

- **s000014:q0 (7/9): How did Bea use the dent?** Answer: Bea shaped the dent into a thumb rest with the sponge. Mr Ivo had said the cup's wall was thick. Luna: The dent-to-thumb-rest action answers the question; the extra wall-thickness sentence is unrelated padding.
- **s000014:q1 (7/9): Where did Grandpa Len rest his thumb?** Answer: Grandpa Len rested his thumb in the thumb rest. Bea had shaped the dent into that thumb rest. Luna: The thumb-rest location is clear; the second sentence repeats related context rather than adding a needed answer.
- **s000014:q4 (7/9): What happened when the shaping rib slipped?** Answer: The shaping rib slipped. The cup was dented. Luna: Correct, but repeats that the rib slipped before stating the resulting dent.

## Limits

One Luna judgment per set; scores are diagnostic, not human-validated guarantees. QA scores use a new rubric and are not comparable to the literary score. Repeated templates are correlated: many flagged pairs can reflect one recurring defect. Earlier runs use different samples and versions, so no causal before/after improvement is claimed. Present-tense outputs were mechanically checked earlier but are not included in this model evaluation. No story rules were changed during evaluation.

[Detailed prose ratings and plot groups](report.md). Raw requests, responses, selected text, QA, usage and source snapshots are retained.
