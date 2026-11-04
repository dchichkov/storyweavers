# Luna High-Reasoning Follow-Up

User requested this follow-up after asking whether higher reasoning could make
Luna viable for the two-level StoryScene pack task. It uses the remaining shared
$10 experiment allowance; the earlier unknown Sol-agent reservation remains held.

## Protocol

- Same `gpt-6-luna`, Flex, frozen task, 13 allowlisted sources plus task/checker,
  response schema and one-shot mode as the original Luna-low request.
- Only request changes: `reasoning.effort=high`, `max_output_tokens=64000` instead
  of 32000. Higher reasoning and extra headroom are changed together; this is
  not a perfectly isolated reasoning-effort ablation.
- No prior generated code, failures, judge notes or repair advice in the prompt.
- One request, no automatic retry or standard-tier fallback. Preserve raw output.
- Unmodified output gets the same independent checker (100 seed/length positions,
  inventory/reference checks, and generated tests) in the local sandbox.
- If all 100 positions are runnable, judge ten uniform positions with seed 777,
  duplicates retained, using the same Terra/Flex/none rubric and calibration.
  Read complete samples manually as a distinct check.
- No parent repair counts as one-shot success; no promotion to the main inventory.

`comparison.json` records the request comparison. Inputs were copied from the
frozen control, not reread from potentially changing project files. The initial
generation reservation is $0.15; returned usage replaces that reservation with
the existing conservative estimate. Judge reservations use the same ledger.

## Status

Completed, including a separately labelled two-fix derivative and Terra judging.
The raw response is **not a one-shot success**. See [full review](../LUNA_HIGH_REVIEW.md).

| Stage | Independent positions | Generated tests |
| --- | --- | --- |
| Raw | Rejected: duplicate file path | Not run |
| Remove byte-identical duplicate only | 17/100 | 8 methods, 168 subtest errors |
| Two manual runtime fixes, no prose edits | 100/100 | 8/8 pass |

Generation used 35,572 input and 29,761 output tokens (15,020 reasoning included).
Estimated Flex generation cost: $0.00966-$0.01189, depending on cache-write TTL,
which the response does not expose. This excludes judging and human repair time.
The conservative shared ledger counts more than the expected invoice.

## Commands

Run from the repository root. Existing prepared/dispatched outputs cannot be
overwritten or automatically rerun.

```bash
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_high_trial.py prepare
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_high_trial.py run --api-key-file .API_KEY
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_high_trial.py check
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_high_trial.py normalize
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_high_trial.py check-normalized
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_high_trial.py repair
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_high_trial.py check-repaired
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/judge_stories.py prepare --arm gpt-6-luna_high_oneshot_repaired
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/judge_stories.py judge --arm gpt-6-luna_high_oneshot_repaired --api-key-file .API_KEY
./.venv/bin/python -m unittest discover -s storyscenes/design/agents_api_trial_20261024 -p test_luna_high_trial.py
```

Five offline tests cover: only intended request fields change, frozen inputs
match their hashes, judge reuse preserves the exact rubric/selection request,
duplicate normalization, repair isolation, correct assessment hashing,
and duplicate dispatch not calling the API. Earlier judge artifacts and their
frozen helper snapshot are untouched; the working judge helper now accepts an
explicit source/output so the new trial does not overwrite the Sol assessment.
