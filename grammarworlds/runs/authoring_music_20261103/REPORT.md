# Luna and Terra: authoring grammarworlds kernels

Source: `luna_high_direct_20/08_music/story.txt` (Nia and Mateo's music-room story).
Latest available account models checked on 2026-11-03: `gpt-6-luna`, `gpt-6.1-terra`.
Both first attempts used identical ruleset/source/gap-list/contract inputs, Flex, high reasoning, and a 32,000-token output limit. Code was not manually repaired.

The shared adapter uses existing symbolic attention, normalized event priors, grammar derivations, and per-word Forest.predict sampling. Each model supplies state, candidate guards, grammar, and commit effects.

| Author / attempt | API result | Local stories | Intervention cases | Words/story | Outcomes |
| --- | --- | ---: | ---: | ---: | --- |
| luna / round1 | incomplete (max_output_tokens) | not run | — | — | — |
| luna / round2 | completed | 60/60 | 20/20 | 274.9 | private_duet: 28, solo: 32 |
| terra / round1 | completed | 60/60 | 20/20 | 257.5 | solo: 43, private_duet: 17 |

## Blinded prose judging

Each judge sees the same 20 uniformly selected positions from each 60-story pack; duplicates retained, seed 777. Author labels/model names and hidden state are absent. Existing story-set rubric and calibration, 0–9; both judges use Flex/none. No partial-success sample is silently substituted.

| Author / attempt | Luna quality | Terra quality | Luna diversity | Terra diversity |
| --- | ---: | ---: | ---: | ---: |
| luna / round2 | 7.05 | 6.60 | 3.00 | 2.00 |
| terra / round1 | 8.40 | 7.65 | 3.00 | 2.00 |

## Authoring effort

Output tokens include reasoning. Times are observed request latencies, not speed benchmarks.

| Author / attempt | Input tokens | Output tokens | Reasoning tokens | Seconds |
| --- | ---: | ---: | ---: | ---: |
| luna / round1 | 22362 | 32000 | 25022 | 308.6 |
| luna / round2 | 29437 | 17800 | 9961 | 220.2 |
| terra / round1 | 22362 | 10080 | 4607 | 79.5 |

## luna / round2: judge evidence

**luna:** All stories share the same music-room setup: Nia hopes for a duet, Mateo is hesitant about performing publicly, and she offers a solo instead. The meaningful branch is whether he later accepts a private duet (s000028, s000058, s000023, s000036, s000017, s000053, s000048, s000002, s000035, s000018, s000041) or chooses to listen while Nia respects his decision (s000014, s000021, s000034, s000057, s000042, s000039, s000024, s000038, s000007). The endings and language vary mostly in small details, not in plot structure.

**terra:** All stories share Nia’s desired duet and solo signup. Mateo declines the private invitation in s000014 but accepts in s000028, producing a modest outcome branch; s000036 and s000017 add the same knee-tapping detail without changing the path. Wording and final drum images recur closely. This assesses only the supplied sample.


## terra / round1: judge evidence

**luna:** All stories center on Nia hoping to perform a picnic duet with Mateo, who is uneasy about an audience; she performs a solo and the ending varies mainly by whether Mateo later joins privately, declines, or the possibility is left open. For example, s000023 and s000048 resolve with a private duet, s000024 and s000028 with Mateo declining, and s000042 leaves his response unstated. Wording and musical details vary modestly, but the set largely follows the same causal template; this small sample does not establish the generator’s overall diversity.

**terra:** All sampled stories use Nia's picnic duet, Mateo's audience anxiety, and Nia's solo. A minor outcome branch separates the private duet in s000023 and s000017 from the deferred duet in s000024 and s000014. Even their closing ribbon images and much of their wording recur; this describes only the supplied sample.

## Additional mismatches found after reading the output

These extra diagnostics were applied to both packs on the same seeds after the first contract checks. They are reported separately, not folded into the predeclared 60/60 and 20/20 counts. No author code was changed in response.

**luna / round2:**

- Guard/state-claim failures: `{'join_with_absent_hero': 28, 'join_without_hero_drum': 28, 'premature_both_returned_claim': 14}`.
- Stories containing identified grammatical errors: `{'the room quiet sounds': 13, 'hoped a duet': 26, 'Mateo choice stayed his': 32}`.

**terra / round1:**

- Guard/state-claim failures: `{}`.
- Stories containing identified grammatical errors: `{}`.

## Interpretation and limits

This is one selected source story and one initial implementation per model. It measures a small authoring experiment, not reliable general model ranking or automatic integration readiness.

Luna's output-limit failure remains a failed first attempt. A 64,000-token recovery, if present, receives the original task plus its truncated final output and error; it is not matched to Terra's first-pass budget.

The contract preserves the source's solo performance and allows voluntary private joining or a respectful solo ending. That intentionally constrains premise/outcome diversity. Optional phrasing and event order do not count as new plots. The larger word counts and music premise also prevent a controlled comparison with the original 60-word rescue/kite/key baseline.

Passing checks establishes sampled termination, replay/nonmutation, normalized word sampling, and specified consent/ownership guards. It does not prove every narrated detail is represented in the world, generalization to new stories, or exhaustive correctness. No LLM runs during generation.

## Reproduce

```sh
.venv/bin/python -m grammarworlds.authoring_trial check --arm terra
.venv/bin/python -m grammarworlds.authoring_trial check --arm luna --round round2
.venv/bin/python -m grammarworlds.authoring_trial report
```

A fresh `prepare --out PATH` followed by `author --out PATH` sends new paid requests. Saved completed responses are reused; only explicit Flex-capacity rejection is retried automatically. `prepare-judges` and `judge` handle the separate blinded evaluation.

Model documentation: [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [Terra](https://developers.openai.com/api/docs/models/gpt-6.1-terra).
