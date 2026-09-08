# Storyscenes

An isolated prototype for **seed → theater → executable scene constraints →
three validated previews → conditional prose**. All current authoring and repair
uses **gpt-5.6-luna**. Finished generators use Python's standard library and make
no API calls. Older engines and scripts are untouched.

The opt-in [compact authoring path](COMPACT.md) moves world definitions into a
small data compiler: reusable role-bound patterns compose with `+`, `/` controls
selection weight, and the library derives knowledge/loan bookkeeping and named
prose slots. It avoids asking Luna to write both a prose plan and Python mechanics.
See [AUTHORING_COMPACT.md](AUTHORING_COMPACT.md) for the executable format.

## Run a saved world

From the repository root (Python 3.10+):

```bash
python storyscenes/run.py storyscenes/runs/improvement_luna_v6/roof_post --seed 1000
python storyscenes/run.py storyscenes/runs/improvement_luna_v6/roof_post --seed 1000 --prose-seed 42 --json
python -m unittest discover -s storyscenes -p 'test_*.py'
```

Copy the whole `storyscenes/` folder to use it elsewhere. No API key, OpenAI
package or repository data is needed to sample completed worlds. Each new run
freezes its shared modules in `_runtime/`; `run.py` automatically uses that copy.
The original prototype remains reproducible with the compatible default API.

## Author a batch

Install `requirements-authoring.txt`, then:

```bash
python storyscenes/workshop.py --out storyscenes/runs/my_trial \
  --campaign storyscenes/improvements/my_campaign \
  --seed 20260907 --count 10 --concurrency 4 \
  --api-key-file .API_KEY --evaluate
```

This makes paid OpenAI requests. Omit `--evaluate` for authoring alone. The
campaign has a $15 ceiling shared across its experiments. Each world also has a
$0.15 conservative dispatch limit (configurable with `--world-budget`). Neither
limit governs unrelated clients. Use one process per campaign ledger.

- Luna low reasoning plans the theater (3,000 maximum output tokens).
- Luna medium writes mechanics once (9,000 maximum output tokens).
- Up to six Luna low repairs return exact-match source edits or state-key renames (3,500 tokens each).
- Luna low writes a prose catalog once (11,000 maximum output tokens).
- Up to four Luna medium repairs replace individual catalog cards (4,500 tokens each).
- Failed worlds are quarantined. There is **no stronger-model authoring fallback**.
- Optional evaluation uses Terra with the unchanged quality rubric; it never
  returns generator code. The optional `--critic` is off by default, receives three stories and compact traces (no scripts),
  and returns at most three findings within 1,600 output tokens. It is recorded
  separately as evaluation; any fixes are Luna patches.

Caps include reasoning tokens. Repairs can read the complete current artifact,
plan and local diagnostics, but their output is a bounded patch. Mechanics
repairs do not receive finished stories. Prose authoring receives the frozen
simulation and executed previews; the shared renderer compiles the final Python
wrapper without another model call.

Put an empty file named `STOP` in the run directory to prevent new authoring or
critic dispatches. In-flight requests can still complete. Retain all reservations
if forcibly interrupting a request. The independent set judge is a separately
started phase; a STOP file is checked before entering that phase.

The key is never written into prompts/artifacts or inherited by generated code.
Use `OPENAI_API_KEY` to omit `--api-key-file`. Requests are saved before dispatch
and responses before execution. A saved response is reused only with its frozen
request. Flex requests allow up to 15 minutes for a response. Missing responses retain their reservations and are never silently
retried. There are no automatic transport retries or service-tier fallbacks.

Prices and supported efforts were checked against the official
[Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna),
[Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra) and
[Flex](https://developers.openai.com/api/docs/guides/flex-processing) documentation.
`cost_report.py` uses actual returned model, tier and usage, including reasoning,
and separates authoring from evaluation. Estimates are not invoice reconciliation.

```bash
python storyscenes/cost_report.py --run storyscenes/runs/my_trial --out /tmp/cost.json
```

It projects the measured authoring cost to 20,000 mechanically successful worlds,
including failed attempts in the numerator. Inherited drafts (via `--from-run`) are included in the authoring projection.
Unknown outcomes and literary rejection
still need accounting; a ten-world estimate is not a production guarantee.

## Shared execution and prose

`runtime.py` provides immutable scenes, guards, atomic effects, invariants,
seeded bounded search, causal provenance and knowledge/ownership kernels.
`scene()` uses keyword effect maps to reduce constructor errors. `Observe`,
`Tell` and `Transfer` bind knowledge and ownership changes to physical carriers.

`planning.py` removes causally irrelevant preparation, preserves pivotal
character turns and replays every retained move against its guards and rules.
Final outcomes must survive pruning. An invariant can be a real prerequisite,
so relevance analysis includes rules as well as explicit guards.

`prose.py` selects complete text variants against initial, before-event or
after-event facts. An explicit lexicon realizes scalar values as grammatical
phrases; there is no raw-enum fallback. Routine adjacent bridge cards are joined.
Endings depend on actual final state. Fact bindings accompany each paragraph,
and deterministic checks catch unsupported bindings, raw state leakage,
unresolved alternatives and repeated words. The full catalog is data, not
model-authored renderer code. `repairs.py` applies bounded, atomic edits.

Each simulation defines `build(seed)` with characters, props, embedded desires,
knowledge and candidate scenes. The planner composes legal moves across that
shared state. Scenes do not prescribe their next scene. The seed varies actual
initial conditions and available consequences, not just a prewritten route index.

The planner has complete state; characters know only what their action guards
allow. It enforces authored rules, not every unstated physical or social fact.
Fact bindings cannot prove that every free English assertion follows from them.
Manual reading and semantic evaluation remain necessary. Generated Python receives
an import/I/O lint and a credential-free, time-limited subprocess; this is not a
security sandbox for hostile source.

For the memeplex north star, definitions stay fixed while instances accumulate
state; every state key and scene binds to a carrier; embedded memes and beliefs
can gate behavior. This is a small operational subset, not yet a universal algebra
for concepts, characters and whole narratives.

## Evaluation and reproducibility

The copied StoryWorld pipeline retains its TinyStories calibration and 0–9
rubric: coherence, style, grammar, storytelling and overall. Terra judges ten
uniformly sampled positions per 100-story pool, selection seed 777, without
deduplication. It separately rates diversity and identifies causal plot groups.
Permutation counts are not presented as a count of distinct plots.

Every world saves 100 stories, three full traces, source hashes, conditional
catalogs, all authoring requests/responses, local failures and patch history.
New experiments freeze the execution runtime. Prose seeds 1–4 are compared with
one fixed world seed so wording variation cannot change the simulated events.

```bash
python storyscenes/verify.py --run storyscenes/runs/my_trial
```

The verifier replays pinned examples and samples 100 fresh seeds per world.
Mechanical QA exposes state changes and causal dependencies; it is not polished
conversational QA for children. The judge sees stories, not traces, so its scores
also need manual scrutiny.

Historical files: `factory.py`, `recover.py`, and `finalize.py` preserve the old
prototype tooling. `factory.py` no longer invokes Terra recovery implicitly.
`recover.py` is an explicitly invoked historical Terra recovery utility; use the
Luna-only workshop for new production experiments. Preserve `runs/prototype_v1`
as measured evidence, including its unsuccessful attempts and original reports.

See [the improvement report](runs/improvement_luna_v6/REPORT.md) and [the initial prototype report](runs/prototype_v1/REPORT.md). The improved batch uses optional bounded semantic feedback; its authoring-only price does not include that review.
