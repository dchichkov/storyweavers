# One-Shot Versus Managed Coding Agent

This runner tests whether a small playable scenario can be authored in one
model response or benefits from a coding harness's execution/repair loop.
It uses OpenAI's **Agents API**, not the Agents SDK and not a local Codex
subscription. Its REST transport works with the repository's existing httpx
dependency, without upgrading the OpenAI SDK used by older experiments.

## Matched Task

[Task](authoring_api_task.md): roughly 1,000-word reference, approximately 20
encounters, a 7/8-scene stateful generator, focused tests and limitations.
Both modes get the same explicit engine/example files and seed ingredients.
The scenario is a kite workshop with a borrowed reel and a shy new neighbour.

- `oneshot`: one Responses API request, 32,000 output-token limit, structured
  file bundle, no tools, no feedback and no parent repairs.
- `agent`: one user task in a managed coding sandbox; the harness can inspect
  files, execute tests, inspect samples and repair its own code before returning.
  It must publish `/workspace/outputs/bundle.json`.
- Models: `gpt-6-luna` and `gpt-6.1-sol`, both `low` reasoning and `flex`.
- No claim that the two modes consume equal tokens or have identical internal
  system prompts. One scenario per arm is a feasibility probe, not a success-rate
  estimate. An agent turn is not a single model inference.

The task adapts lessons from the earlier supervised trial but is a new saved
brief, not a test of its unmodified v3 prompt. It explicitly separates state
tracking from narration and asks for believable physical dependencies.

## Security And Accounting

The `INPUTS` tuple in [authoring_api.py](authoring_api.py) is the entire source
allowlist. No recursive repository upload, API keys, datasets, Git history,
hidden traces or other experiments. Task/checker files are added separately.
Cloud sandbox: 1 GB, outbound network disabled, subagents disabled, no secrets.
Downloaded output paths are validated and never merged into the working tree.
Local generated code runs with macOS Seatbelt, no network or repository access,
an empty credential environment, a temporary workspace and a 180-second limit.
Other platforms fail closed until an equivalent sandbox is supplied.

The current experiment has a **new $10 total authorization**, separate from
the historical story-judging campaign. An exclusive lock prevents overlapping
runners from racing its ledger. Reservations happen before requests; unknown
outcomes retain their reservation. No automatic paid retries or tier fallback.

**Agents API has no documented per-session hard spend limit.** The runner polls
usage every ten seconds, stops early at $0.70 (Luna) / $1.20 (Sol) conservative
model estimates, reserves $2/$5 respectively for overshoot, and cancels at 15
minutes or after five minutes with no reported usage. Estimates bound cache-write
and long-context rates conservatively; returned agent costs add a $0.10 sandbox
margin. Usage is best-effort, so this is not a provider-enforced billing cap.
Do not run unattended production jobs under a strict financial guarantee on
this mechanism alone. Use provider-side project controls where appropriate.

The runner saves session/turn/item metadata and artifacts before deleting its
own session to release the sandbox. It does not delete unrelated sessions.
If creation has an unknown outcome, `recover` searches by the unique request
metadata, collects saved work and requests cancellation/deletion without making
another session. Unconfirmed cleanup must be resolved before more spending.

## Commands

```bash
# Preparation is offline. Each arm's output directory must be new.
./.venv/bin/python storyscenes/authoring_api.py prepare --model gpt-6-luna --mode agent
./.venv/bin/python storyscenes/authoring_api.py run --model gpt-6-luna --mode agent --api-key-file .API_KEY
./.venv/bin/python storyscenes/authoring_api.py check --model gpt-6-luna --mode agent

# Repeat with --mode oneshot and/or --model gpt-6.1-sol.
# Recover an interrupted agent run, never blindly repeat its paid request:
./.venv/bin/python storyscenes/authoring_api.py recover --model gpt-6-luna --mode agent --api-key-file .API_KEY

./.venv/bin/python -m unittest storyscenes.test_authoring_api
```

Default evidence directory: `storyscenes/design/agents_api_trial_20261024/`.
Do not choose a new campaign directory merely to bypass a spent allowance.

The independent checker uses 50 seeds at both lengths, exact event/state/prose
replay, inventory coverage, reference word count and the generated tests. All
requested positions, including failures, remain in `check.json`. The test seeds
are visible in the supplied checker, so these are not blind held-out cases.
The command fails when the assessment fails, while preserving `check.json`.
Mechanical validity is distinct from prose quality and diversity. Read random
complete samples and grade successful outputs with the standard judge; retain
failed arms in the experiment denominator.

## First Live Trial

[Saved results and manual review](design/agents_api_trial_20261024/README.md):
Luna one-shot failed 100/100 route positions; Luna agent stopped incomplete.
Sol one-shot passed all 100 replay positions but failed its own scene-length
test and remained repetitive. Sol agent was cancelled for missing usage
telemetry, making that comparison inconclusive. No generated pack was repaired
or promoted into the main inventory. This supports trying a one-shot draft plus
validated repair workflow, not declaring either mode production-ready.

## Official Sources

Checked October 24, 2026:
- [Agents API](https://developers.openai.com/api/docs/guides/agents-api/overview)
- [Session schema](https://developers.openai.com/api/reference/resources/beta/subresources/agents/subresources/sessions/methods/create)
- [Hosted environments](https://developers.openai.com/api/docs/guides/agents-api/environments/openai-hosted)
- [Files and artifacts](https://developers.openai.com/api/docs/guides/agents-api/environments/files)
- [Usage limitations](https://developers.openai.com/api/docs/guides/agents-api/observability)
- [Models](https://developers.openai.com/api/docs/models) and [pricing](https://developers.openai.com/api/docs/pricing)

API key permissions: `api.agents.read`, `api.agents.write`, and
`api.responses.write`. The user explicitly authorized the allowlisted source
upload and live experiment in chat. That authorization is saved with the
campaign; it does not authorize uploading additional repository files.
