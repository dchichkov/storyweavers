# First 30-story holdout

Seeds 1000-1029, no filtering/replacement; 30/30 generation and serialized replay
passes, 30 exact-unique texts, 16 mechanical descriptors. Story-only pooled XZ:
36,847 -> 5,320 bytes, 177.3 compressed bytes per story. This shows substantial
repetition despite exact uniqueness.

All 14 API requests returned. Estimated returned-usage cost $0.11472115.
Luna's complete assessment: storytelling 7.133, overall 7.900, diversity 5/9.
Both judges accepted 176/180 QA conversations as usable. These are model grades,
not a gold entailment audit or a multi-turn evaluation.

Terra graded all 30 stories but omitted s000009 and s000011 from its plot-group
partition. The strict validator correctly rejects that set assessment. Its raw
storytelling mean is 7.467 and raw diversity 5, but these are diagnostic values,
not an accepted complete judge result. Do not silently patch the group list.

Manual review sampled the newly appearing declined loan, correct parcel, late
return and shallow-water postponement alongside their QA. The straightforward
correct-parcel branch is weak on a consequential turn. The loan refusal has a
coherent choice but quiet ending. These remain in the evaluation distribution.

Next: regrade the identical 30 stories with plot-group membership attached to
each required story rating, preserving the literary rubric and calibration.
Use `harbor_iteration_v8_30_judge_v2`; no new QA requests are needed. Keep this
original assessment and its missing-group failure as evidence.
