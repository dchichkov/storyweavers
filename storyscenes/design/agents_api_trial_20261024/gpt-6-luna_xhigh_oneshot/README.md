# Luna Xhigh Follow-Up

User authorized a matched xhigh trial on October 24, 2026, under the remaining
shared $10 campaign budget. The existing $5 unknown Sol-agent reservation remains.

Only `reasoning.effort` changes from the frozen Luna-high request: high -> xhigh.
Model `gpt-6-luna`, Flex, 64,000 maximum output tokens, task, 13 source files plus
task/checker, structured bundle schema and one-shot mode remain identical.
No prior output, failures or repair advice are supplied. `comparison.json`
records the comparison; six offline high/xhigh helper tests pass.

The 64k allowance includes reasoning and visible output. For comparison, high
used 29,761 output tokens, including 15,020 reasoning tokens, without truncation.

## Status

Generation and evaluation completed. No retries, normalization or repairs.
The response completed after 799 seconds: **57,503/64,000 output tokens**,
including **41,292 reasoning tokens**, without truncation. Packaging passed.

Untouched code runs **100/100** independent positions. Full acceptance fails:
the reference has **835 words** (900-1100 required) and two sampled episodes
have **72 words** (70 maximum). Generated tests: six pass, one fails its scene
length assertion. All seven methods ran; the failed loop stopped at its first
assertion and does not prove all its promised cases were exercised.

Terra judged ten uniform unchanged stories: quality **7.2/9**, storytelling
**6.5/9**, diversity **3/9**. Full findings and comparison:
[Luna xhigh review](../LUNA_XHIGH_REVIEW.md).

Expected generation-only Flex cost is **$0.01660-$0.01882**, depending on cache
write TTL, which was not returned. Conservative campaign accounting is now
**$5.52177968/$10**, including the unchanged $5 unknown Sol-agent reservation.

## Reproduction

From the repository root, using `luna_xhigh_trial.py` in the parent directory:
`prepare`, `run --api-key-file .API_KEY`, `check`, `prepare-judge`, and
`judge --api-key-file .API_KEY`. Existing preparation/dispatch cannot be repeated
in place. Checking uses the unchanged isolated runner; judging requires all
100 saved seed/length positions to be runnable, then selects ten uniform
positions with seed 777, retaining duplicates, using the standard Terra rubric.
