# Ten rounds: final Luna comparison

Ten implementation rounds are complete. Generation still uses weighted typed grammar, guarded symbolic kernels and carrier-grounded attention. Luna is an offline evaluator; no LLM generates or repairs prose at runtime.

All scores are 0–9. Each cell comes from one Luna/Flex/reasoning-none assessment of each world set, using unchanged calibrated prose and separate text-only QA rubrics. Each version has 20 uniformly selected past-tense stories per world (140 total); duplicates remain.

| Evaluation | Story quality | Within-world diversity | QA quality | Grounded QA | Usable QA |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original, development | 5.57 | 0.86 | 7.30 | 82.0% | 82.0% |
| Final, same development positions | 6.57 | 2.14 | 7.80 | 100.0% | 100.0% |
| Original, fresh seeds | 5.56 | 1.00 | 7.22 | 90.1% | 90.1% |
| Final, same fresh positions | 6.60 | 1.86 | 7.88 | 98.2% | 98.2% |

Development seeds are 0–59; fresh seeds are 1000–1059, reserved before the campaign. The final version was frozen before its fresh outputs were judged; no changes were made in response to fresh scores. These are unseen draws within the same seven authored worlds, not novel-world generalization.

The old source snapshot was restored with unchanged portable dependencies. It exactly reproduced all 420 original past-tense pool stories **and QA** before producing fresh samples. Identical sampled positions and identical system rubrics are checked by `comparison.py`. The old QA and current QA differ in number/content, so QA gains compare each version’s question sets, not identical questions.

## Fresh sample by world

| World | Original quality | Final quality | Original diversity | Final diversity | Final QA | Grounded answers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| rescue | 6.00 | 8.00 | 1 | 2 | 8.33 | 120/120 |
| kite | 6.00 | 7.00 | 1 | 3 | 7.47 | 105/120 |
| key | 5.00 | 6.00 | 1 | 1 | 8.56 | 120/120 |
| music | 4.90 | 7.00 | 1 | 2 | 7.24 | 120/120 |
| greenhouse | 5.00 | 5.20 | 1 | 2 | 7.62 | 120/120 |
| library | 6.00 | 6.00 | 1 | 1 | 8.29 | 120/120 |
| pottery | 6.00 | 7.00 | 1 | 2 | 7.67 | 120/120 |

## Architecture and physical verification

- 63 tests passed, including physical interventions, consent, tools, conservation, firing/cooling, ownership, ambiguity-safe pronouns and transitive evidence failures.
- 840 fresh unfiltered stories (both tenses) completed and replayed; 5040 QA pairs retained exact visible evidence and event/entity IDs.
- 44,908 carrier-removal, prerequisite-removal and forged-actor checks rejected invalid execution without mutation.
- 824 first branching states were compared with attention on/off; 824 changed event mass, while every comparison retained exactly the same legal frames. This measures causal influence on authored probabilities, not learned attention or calibrated uncertainty.
- Fresh lengths: 60–113 words, mean 90.4. At least two speakers and five distinct QA pairs per story; actual final samples contain six.
- Every word (including punctuation and END) is sampled from the normalized forest. Token probabilities telescope to surface mass; the semantic event is selected from the posterior and executed once. Prediction is pure.
- The frozen GF/Codeco-derived modules and original evidence are unchanged. New plans, speech constructions and world packs layer above them. This prototype does not implement the full memeplex algebra or full GF/Codeco languages.

## Limits and next work

Diversity remains low: there are only two or three major causal outcomes per world. More event-order paths are not automatically more distinct plots. Scores vary across single judge calls; intermediate rounds use different subsets, so their means are not a clean learning curve. No human validation or independent repeated judge estimate is claimed.

Remaining defects include procedural prose, repetitive dialogue/names, thin character responses and literal-recall QA. All 15 fresh grounding failures are kite answers that call the material paper where the visible story only names a kite; this remains unresolved in the frozen final version. Exact evidence links and physical replay do not prove every English entailment; Luna’s raw grounding judgments are retained, including questionable flags. Meaningful contextual answers remain multi-sentence; thin trace answers use one complete sentence instead of padding.

Two final QA responses hit the 20,000-token output limit (development kite and fresh greenhouse). Their identical samples/rubrics were repeated with a 40,000-token allowance; incomplete responses are retained and contribute no ratings. No valid low-scoring response was retried.

The original round-2 QA request timed out after dispatch and was not resent. A separately recorded six-story follow-up is used for that round’s QA diagnostic; its prose used twelve stories. See its follow-up manifest.

[Ten-round ledger](REPORT.md) · [Fresh stories and QA](final_heldout_audit/samples.md) · [Final development evaluation](round10/eval/REPORT.md) · [Final fresh evaluation](final_heldout_eval/REPORT.md) · [Original fresh evaluation](baseline_heldout_eval/REPORT.md)
