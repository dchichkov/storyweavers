# Managed Agents Versus One-Shot Trial

October 24, 2026. User authorized up to $10 for this new experiment, using current
models, Flex and limited reasoning. [Runner documentation](../../AUTHORING_API.md).

## Status

**Direct prose follow-up:** [Twenty matched Luna/high stories](luna_high_direct_20/MANUAL_REVIEW.md)
completed and were judged, mean 764 words. Terra assigned every story 9/9 overall,
but manual reading found continuity errors it missed: this is a judge ceiling,
not proof of flawless prose. Generation cost estimate: $0.03197 for twenty.
[Read all stories](luna_high_direct_20/STORIES.md). Current conservative campaign
accounting is $6.579959, including unchanged unknown-usage holds of $5.15.

**Latest batch:** [Twenty distinct seeds at xhigh/128k](LUNA_XHIGH_128K_20_REVIEW.md)
returned 19 bundles and one HTTP 500. Five are 100/100 runnable untouched; library
alone passes every mechanical gate. Conditional judge mean: quality 7.8/9,
diversity 2.4/9. At that close, campaign accounting was $6.435479 including $5.15 in
unknown-usage reservations. All amounts below are historical snapshots.

**Latest:** [Luna xhigh review](LUNA_XHIGH_REVIEW.md): 100/100 runnable untouched,
but reference/scene lengths fail; Terra quality 7.2/9, diversity 3/9. Output used
57,503 of 64,000 tokens, completed without truncation. Current campaign accounting
is $5.521780 including the unchanged $5 hold. Earlier amounts below are historical.

**Follow-up:** [Luna high-reasoning review](LUNA_HIGH_REVIEW.md) records an
additional authorized one-shot, exact-duplicate normalization, two manual code
fixes and Terra judging. It reaches 100/100 runtime checks after repair, but
still has prose/state defects. Quality 8.0/9, diversity 1/9. The sections below
retain the initial low-reasoning comparison and its historical accounting;
current conservative campaign accounting is $5.457458 including the $5 hold.

Implementation, four live requests, independent checks and manual review complete.
The configured key's read-only Agents API session-list check returned HTTP 200.
After the initial execution approval block, the user explicitly replied:
**"Authorize this source upload and experiment"** to the question specifying
the 13 allowlisted project files, task/checker, OpenAI Responses/Agents API
destinations, exclusion of credentials/datasets/Git history, and the $10 budget.
Both managed sessions have been cancelled/deleted; no remote work remains.
No general success-rate conclusion is possible from one scenario per arm.

## Results

| Model | Mode | Complete bundle | Independent positions | Pack tests | Result |
| --- | --- | --- | --- | --- | --- |
| gpt-6-luna | Managed agent | No | Not runnable | Never ran tests | Agent explicitly abandoned incomplete draft |
| gpt-6-luna | One-shot | Yes | 0/100 | 1/5 pass, 4 errors | Planner/guard contradictions; reference 1,137 words |
| gpt-6.1-sol | Managed agent | No | Not assessed | No visible tool activity | Inconclusive: cancelled after 307 seconds without usage telemetry |
| gpt-6.1-sol | One-shot | Yes | 100/100 | 4/5 pass, 1 failure | Scene-length test fails |

No arm meets **all** acceptance requirements untouched. Sol's one-shot passes
the independent state/event/prose replay checks, inventory mapping and reference
length (1,035 words), but its own test rejects short scenes (minimum observed:
35 words, below even its test's relaxed 38-word minimum). This is not a runtime
or trace failure. The generated test stops on its first assertion failure, so it
does not prove all 200 positions promised in that test were exercised.

Sol's agent session showed only the initial user item in progress snapshots,
and null usage through the final poll. It was stopped by our missing-telemetry
watchdog, **not** by an observed model failure. Flex scheduling latency is one
possible explanation, not an established cause. This arm cannot establish
whether Sol with a harness is better than Sol one-shot.

Luna's managed session completed normally after approximately 123 seconds; it
was not stopped by the watchdog. It inspected files and wrote draft code, then
explicitly said the inventory, tests, README and bundle were missing. Saved
command items preserve the drafting attempt. No published artifacts were
available; the session was deleted after transcript collection.

Manual review of Luna's untouched one-shot `world.py` found:

- `repair_choice` sets `reel.returned=True`, but `final_flight` requires False.
- Its core route contains six scenes; its only insertion produces seven, not
  the requested seven/eight. A later length check cannot fix the missing scenes.
- It can insert the late wind vignette before its prerequisite repair choice.
- Opening prose declares the string frayed even with a sound reel; flight prose
  assumes wind, and closing/flight prose references the optional blue ribbon.
- State moves the party to the common while the following prose still describes
  the workshop. The `shy` parameter never changes the generated action/prose.

These are independent compatibility, state/prose and diversity defects, not a
single typo. No repairs were applied to either experimental output.

## Sol One-Shot Reading

The three uniformly sampled saved outputs (selection seed 777) are in
`gpt-6.1-sol_oneshot/manual_random_samples.json`. They are positions 5029/7,
5007/8 and 5047/7. A fourth, deliberately selected flight ending was read as a
branch diagnostic, not represented as a random sample. Source and pack tests
were also inspected. At this initial close, no numerical LLM judge scores had
been purchased; these initial observations were manual.

### Requested Follow-Up

[Full manual and standard-judge review](standard_judge_v1/REVIEW.md) now covers
ten uniformly sampled untouched stories, plus an exhaustive local parameter
check. Terra scored quality/storytelling **8.1/9**, diversity **2/9**; all 48
parameter/length diagnostic cases passed replay. The prose is promising, but
deferred repair needs motivation and most branches converge to the same ending.
The one-shot-plus-repair workflow remains a recommendation, not a completed
repair experiment. [Read the ten selected stories](standard_judge_v1/STORIES.md).

The stories are recognizably stories: a child changes how she includes a shy
neighbour, dialogue expresses the social difficulty, a shared flight or drawing
provides an actual closing activity, and the borrowed reel is returned usable.
Early repair, weather and invitation style have real downstream effects. The
code uses detached LocalPlay actions and bounded guarded search rather than
Luna's inconsistent fixed route list.

Remaining weaknesses:

- Only 30 exact texts and six distinct routes in 100 requested positions.
  Ninety end at the drawing table; ten share a flight. Average length 352 words.
- The XZ/LZMA diagnostic is 202,820 bytes to 2,536 bytes (1.25%) for these 100
  texts in checker order. This is not the earlier 1,000-samples-per-world
  protocol and should not be compared directly to its compression ratios.
- Optional vignettes add pleasant dialogue, but are mostly independent inserts;
  their flags do not affect later action or prose. Both appear at length eight.
- The calm-weather branch says the kite cannot lift and then they watch other
  kites. That is an underexplained physical detail, not a trace contradiction.
- The field ending collapses several different causes into the same shared
  drawing response. Limited semantic variety remains even when replay is exact.
- Nine executable scene IDs consolidate the approximately 20 reference
  encounters. This is disclosed in the mapping, not 20 independently playable
  scenes. The model's README accurately describes a small story family.

## Interpretation

A capable one-shot can produce a mechanically sound starting pack for this
scenario. It did not produce an acceptance-ready pack, and a coding harness
alone did not rescue Luna. Recommend a **draft -> independent checks -> bounded
repair -> prose/diversity review** workflow, with an agent available for repair,
rather than assuming every pack needs a lengthy agent session from scratch.

This is a feasibility probe, not proof that the proposed hybrid has a measured
success rate. We did not run the hybrid repair arm or repair the saved candidates.
Repeat across several scenarios before selecting a production authoring model.
Keep short scene authoring and deterministic simulation checks separate from
claims about corpus diversity or training value.

## Accounting

| Arm | Conservative returned estimate | Unsettled reservation |
| --- | ---: | ---: |
| Luna agent | $0.110592 (includes $0.10 sandbox margin) | - |
| Luna one-shot | $0.013311 | - |
| Sol agent | Unknown | $5.00 |
| Sol one-shot | $0.258020 | - |

Returned estimates total **$0.381922**; adding the unreleased Sol reservation
accounts for **$5.381922 of the $10 allowance**. These deliberately conservative
estimates are not invoices. Unknown usage is not treated as free; cancellation
and deletion do not establish zero billing. See `budget.json`, raw responses,
session metadata and cleanup confirmations. These figures describe the initial
four-request close. The requested judge follow-up added a conservative $0.0250815
allowance: current accounting is $0.40700368 returned estimates plus the unchanged
$5 unknown-usage reservation. No additional generation or agent runs were made.

## Prepared Protocol

One matched kite-workshop scenario, using `gpt-6-luna` and `gpt-6.1-sol`, low
reasoning and Flex. Each model has a single-response arm and a managed coding
arm. Use exactly the prepared common task and engine bundle; no parent repairs
will count as a successful untouched output. All failures remain in results.
The agent may run tests and repair files autonomously within one user task.

Untouched completion requires a complete downloadable file bundle, reference
within 900-1100 prose words, mapped executable inventory, 100/100 generated
seed/length positions with exact trace/state/prose replay, and nonempty passing
pack tests. Inspect actual code and random prose as a separate gate: green tests
do not establish physical plausibility, motives, optional scenes, causal parameter
variation or literary quality. Do not silently fix generated code to count a pass.

The new shared $10 cap includes model calls, sandbox estimates and any subsequent
judging. The agent watchdog is not a provider-side hard spending cap; see the
runner documentation for reservations, early stopping, missing-usage behavior,
cleanup and uncertainty. No automatic retries or fallback model/tier.

`gpt-6-luna_agent_preflight_v1/` preserves the first offline preparation before
adding unique request metadata for unknown-creation recovery. It was never
dispatched. All four dispatched arms have matching input-source hashes. Raw
requests, responses, dispatch markers, checks and failures remain saved.

## Verification

- 14 runner unit tests pass, including unsafe paths, repeated dispatch, changed
  prepared requests, changed validation sources, reservations and recovery.
- Combined runner, LocalPlay and Smallest Sea regression suite: 38 tests pass.
- The independent checker was exercised offline using the existing greenhouse
  pack as a fixture: 100/100 seed/length positions passed exact replay and all
  26 existing pack tests passed. This is a validator test, not a new generated arm.
- macOS isolation was exercised against repository credential access and a
  loopback network connection: both were denied. No key contents were printed.
- Initial deny-default sandbox policies prevented macOS/Python startup; the
  corrected policy allows system bootstrap reads while denying user-directory
  data reads, network and writes outside the temporary workspace.

`runner_snapshot/` and `runner_source_hashes.json` preserve the runner version
used for paid dispatch. After the experiment exposed the failure path, the
working runner was hardened to collect final evidence even on cancellation and
to return a failed command when `check.json` says the pack failed. The independent
checker and grading criteria did not change. Initial Sol cancellation evidence
is limited to progress snapshots; the new cleanup collection is regression-tested,
not retroactively claimed to have run on that session.

Prepared inputs and requests contain only the explicit source allowlist, task
and checker. They do not include credentials, datasets, Git history or unrelated
workspace experiments. Nothing is automatically merged into the main inventory.
