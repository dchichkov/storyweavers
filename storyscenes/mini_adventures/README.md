# Story-First Scenario Inventory

The [two-agent authoring trial](../design/authoring_trial_20261024/README.md)
adds independent short-scene packs alongside the original Smallest Sea prototype.
Each pack owns a reference story, a mapped scene inventory, local mechanics,
prose, and tests. Packs share the atomic transition engine and the tools here.

New authors should start from the saved
[v3 authoring brief](../design/authoring_trial_20261024/AUTHORING_AGENT.v3.md.in).
It incorporates supervised repairs from this trial; it has not been tested as
a new one-shot prompt. Use [LocalPlay](local_play.py) for atomic action/trace
infrastructure and keep scenario-specific rules in the pack.

```bash
./.venv/bin/python -m storyscenes.mini_adventures list
./.venv/bin/python -m storyscenes.mini_adventures list --scenes
./.venv/bin/python -m storyscenes.mini_adventures run bakery --seed 0 --scenes 8
./.venv/bin/python -m storyscenes.mini_adventures run greenhouse --seed 0 --scenes 7
./.venv/bin/python -m storyscenes.mini_adventures audit bakery --seed 0 --count 50 --out /tmp/bakery-new-audit
./.venv/bin/python -m storyscenes.mini_adventures verify /tmp/bakery-new-audit
```

`audit` samples every seed at both lengths, retaining failures and duplicates.
It checks explicit event preconditions, state changes, scene guards, full replay,
deterministic generation, and inventory coverage. It records text lengths, quoted
word fraction (approximate), outcomes, exact text counts, and default-XZ pooled
compression. None is a substitute for reading the stories.

The output directory must be new. It contains every attempt, all generated texts
(including rejected ones), passing JSONL rows, a summary, and hash-addressed
source copies in an importable package tree. To run frozen source, change into
that audit's `source/` directory and invoke the same module with an absolute
Python interpreter path. `verify` checks source hashes and reproduces every
saved attempt with an isolated interpreter importing only that frozen tree.
No API requests occur in generation or audit.

The inventory is deliberately pack-scoped. Being listed together does not mean
that bakery and greenhouse scenes can be mixed arbitrarily: each has its own
cast, props, state schema, and compatibility constraints. Shared helpers should
have real consumers and tests before becoming engine APIs.
