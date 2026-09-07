# Luna: Five Repaired-Example Batches

Run date: 2026-09-07 UTC. Five batches of five worlds, each using one different
manually repaired example instead of Puddles. All 25 responses are preserved.

## Result

**20/25 runnable worlds; Mini overall 7.00/9 across those 20.** Garnet had the
highest story score; Grocery had the strongest sampled text diversity. Thud
produced readable but severely repetitive output. This is a five-task pilot,
not enough evidence to declare a winning example for production.

| Example | Raw runnable | After automatic repair / extraction recovery | Own `--verify` passes | Mini overall /9 | Median distinct stories per `-n 100` request | Median slot-normalized patterns | Mean story words | Mean story + story-QA words |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Previous upgraded Puddles pilot | 3/5 | 4/5 | 2/5 | 6.25 | 89 | 23.5 | 163.6 | 268.3 |
| Quesadilla | 2/5 | 3/5 | 2/5 | 6.00 | 100 | 2 | 222.1 | 346.5 |
| Thud | 5/5 | 5/5 | 4/5 | 7.20 | 61 | 4 | 109.1 | 195.7 |
| Dining mystery | 3/5 | 3/5 | 3/5 | 6.67 | 98 | 45 | 224.0 | 359.6 |
| Garnet | 4/5* | 4/5 | 4/5 | **7.50** | 100 | 25 | 171.0 | 282.7 |
| Grocery | 5/5 | **5/5** | 3/5 | 7.20 | 100 | **90** | 218.9 | 334.5 |

*Garnet initially materialized only four files, three runnable. The fifth saved
response contained a separate commentary message followed by a valid Python
final answer. Excluding commentary recovered that fourth runnable world with
no source edit or additional generation request.

Scores exclude unrunnable worlds and use one story per runnable world. Word
lengths are averages of the per-world sample means. QA length includes story
questions and answers, not world-facts QA or generation prompts.

The local check requested `-n 100 --seed 2026090605 --qa --json` from each world.
Thud's dining-room world returned only 27 stories; the other 19 runnable worlds
returned 100 each. Total: **1,927 stories**, with **1,744 distinct within-world
texts**. This is not a globally deduplicated training export. Several generated
CLIs deduplicate internally, so these are requested output counts, not a common
budget of exactly 100 raw RNG draws. All 20 runnable worlds reproduced identical
JSON under two different `PYTHONHASHSEED` values.

Slot-normalized patterns use the existing contributor-analysis heuristic after
exact deduplication. They are **not counts of independent plots**. In particular,
changing unused params can change normalization even when the prose is identical;
deduplicating first prevents counting that artifact as diversity. The previous
Puddles samples were checked using this same calculation.

## Controlled Settings

- Generation: `gpt-5.6-luna`, reasoning `none`, Flex, source mode, 32,000 output-token limit.
- Five concurrent requests per batch; five batches run concurrently, at most 25 requests.
- Seed: `2026090605`, reused from the Puddles pilot. The five seed requests are identical apart from target paths.
- No prompt addendum. Each request includes exactly one repaired example, plus the standard contract and helper sources.
- Judge: `gpt-5.4-mini`, actual response model `gpt-5.4-mini-2026-03-17`, Flex, unchanged baseline-calibrated 0-9 protocol, temperature 0.
- Quality sample seeds: 777-781 in manifest job order. Static QA: ten variants, seed 42.
- Existing automatic repair only; no hand repairs to generated Python in this comparison.

The prompt wrapper changed from "Two complete examples" to "Complete examples"
when arbitrary example selection was added. Target directories are also deeper
than the previous Puddles pilot. These are small but real comparison caveats.
The selected repaired examples are intentionally selected references, not a
random sample of all repaired worlds. Their own `--verify` and 100-story sampling
checks passed before generation.

## Per-Task Scores

| Seed task | Puddles | Quesadilla | Thud | Dining | Garnet | Grocery |
|---|---:|---:|---:|---:|---:|---:|
| Decide / darling / dining-room quest | 6 | 4 | 4 | 7 | 8 | 6 |
| Gingham / magic / nursery rhyme | 7 | syntax failure | 8 | 8 | 6 | 8 |
| Nose / sharing / bedtime | 5 | 6 | 8 | 5 | syntax failure | 7 |
| Bury / teamwork / fable | 7 | 8 | 8 | syntax failure | 8 | 8 |
| Naked / bravery / friendship rhyme | syntax failure | syntax failure | 8 | syntax failure | 8 | 7 |

The same four task types rated in Puddles average 7.00 for Thud and 7.25 for
Grocery, versus Puddles' 6.25. Those are useful matched-task observations, not
statistically reliable model-quality estimates.

## Manual Reading

I read all 20 judged stories, examined the diversity samples, and inspected
representative source paths behind the failures.

1. **Quesadilla: copying and slot errors.** The nose story becomes another
   missing-quesadilla mystery, a clear sign of example-domain carryover. It has
   "A a peppery tickle" and a sentence fragment about two cups. The dining-room
   story loses track of its object: recipe card, note, envelope, and celebration
   are mixed. The fable scores 8 but all 100 distinct texts collapse to one
   normalized pattern. High exact uniqueness here is mostly slot substitution.

2. **Thud: complete stories, tiny output space.** The Gingham world contains
   exactly four fully written arcs with literal names. It calls `.format(name=...)`
   on text that has no corresponding placeholders. Thus 100 outputs contain
   only four distinct stories, despite the 8/9 quality score. The world and QA
   can name a different child from the prose. Another story gives both roles
   the name Ben. Other Thud worlds also use small arc banks with substitutions.

3. **Dining: some genuine scene development, but inconsistent bindings.**
   Its Gingham story follows a broken-thread problem through a repair to an
   ending image. The nose story mixes Mira with literal Noor/Ada names and an
   unrelated helper. Two scripts do not parse because mnemonic hexadecimal
   salts contain non-hex letters: `0xBURI3` and `0xBRA7E`.

4. **Garnet: the most promising prose in this pilot.** Separate arc builders
   keep many problems, decisions, resolutions, and final images together. The
   dining-room script has five such builders rather than freely combining
   unrelated endings. This helps explain its coherent outputs, but is still
   authored arc selection, not proof of a rich state-driven simulation. Its
   Gingham story still says "a tiny cloth a yellow finch"; the nose script has
   a malformed f-string. The recovered friendship rhyme scores 8.

5. **Grocery: broad combinations, insufficient compatibility.** All five
   worlds returned 100 distinct texts, but story details sometimes disagree.
   The dining-room sample rescues a ring, then closes on a rescued blue napkin;
   it mixes the sampled name Pip with literal Darling. The source independently
   chooses quest, suspense, monologue, and ending, allowing those contradictions.
   The nose story announces a new visitor without clearly introducing one.
   Its teamwork fable is a stronger complete story, though the underlying
   generator still largely narrates a fixed sequence and then sets success flags.

**Interpretation:** corrected examples do transmit useful organization and story
structure. They do not automatically transmit the constraints that make those
examples coherent. The next focused test should retain Garnet's linked causal
arcs or Grocery's breadth while requiring names, objects, causes, and ending
images to come from the same selected scenario. Thud should not be selected on
its quality average alone.

## Runtime And Verification Defects

- One successful automatic repair: Quesadilla's nose world. All other failing
  repair attempts rolled back. The five remaining syntax errors were left
  intact to preserve the generation comparison.
- Two Quesadilla scripts have trailing quote errors; two Dining scripts have
  invalid hexadecimal literals; Garnet's nose script has a malformed f-string.
- Four runnable worlds fail their own verification. Quesadilla's fable and
  Grocery's fable require exact words absent from some otherwise valid stories;
  Thud's nose world omits the required seed word in an arc; Grocery's friendship
  rhyme compares a two-field Python tuple with a three-field ASP tuple.
- Only 10/25 pass a bare CLI invocation with `PYTHONPATH` unset. The ten other
  runnable worlds need the pipeline's `PYTHONPATH=storyworlds` because their
  hard-coded parent-directory import setup does not reach the shared helpers
  at this nested target depth. This is distinct from story/runtime sampling
  under the normal pipeline environment.
- Mini grades narrative prose only. The static QA duplication check and own
  verification are separate checks, not evidence that Mini validated the QA.

## Preserved Artifacts

Main bundle: [luna_repaired_examples_20260907](luna_repaired_examples_20260907/).
Generated Python: [worlds directory](../worlds/luna_repaired_examples_20260907/).
Portable local snapshot: [luna_repaired_examples_20260907.tgz](luna_repaired_examples_20260907.tgz),
containing this report, the full batch bundle, and all 25 materialized scripts.
The raw JSONLs and snapshots are retained locally; this run was not committed or pushed.

| Arm | Snapshotted example | Generation and judging artifacts | Generated scripts |
|---|---|---|---|
| Quesadilla | [source](luna_repaired_examples_20260907/quesadilla_mystery_to_solve_bedtime_story.py) | [batch](luna_repaired_examples_20260907/quesadilla/) | [worlds](../worlds/luna_repaired_examples_20260907/quesadilla/) |
| Thud | [source](luna_repaired_examples_20260907/thud_teamwork_rhyming_story.py) | [batch](luna_repaired_examples_20260907/thud/) | [worlds](../worlds/luna_repaired_examples_20260907/thud/) |
| Dining | [source](luna_repaired_examples_20260907/alliance_shrivel_fifty_dining_room_surprise_detective.py) | [batch](luna_repaired_examples_20260907/dining/) | [worlds](../worlds/luna_repaired_examples_20260907/dining/) |
| Garnet | [source](luna_repaired_examples_20260907/garnet_humor_curiosity_repetition_tall_tale.py) | [batch](luna_repaired_examples_20260907/garnet/) | [worlds](../worlds/luna_repaired_examples_20260907/garnet/) |
| Grocery | [source](luna_repaired_examples_20260907/huge_movement_silo_grocery_store_moral_value.py) | [batch](luna_repaired_examples_20260907/grocery/) | [worlds](../worlds/luna_repaired_examples_20260907/grocery/) |

- [examples.json](luna_repaired_examples_20260907/examples.json): canonical source paths, snapshot paths, SHA256 hashes, pre-run local checks.
- [runs.json](luna_repaired_examples_20260907/runs.json): actual commands, manifests, return codes, authoritative final quality paths and means.
- [checks.json](luna_repaired_examples_20260907/checks.json): per-world compile, runtime, verification, replay, diversity, and length results.
- [local_samples.jsonl](luna_repaired_examples_20260907/local_samples.jsonl): all 1,927 local sample rows with story QA.
- [run.py](luna_repaired_examples_20260907/run.py): five-arm driver, refusing to overwrite existing runs.
- [check.py](luna_repaired_examples_20260907/check.py): reproducible local audit, no API calls.
- [previous Puddles review](storyworld_service_20260907T022844Z_seed2026090605_n5.manual_review.md).

Generation used 266,750 input tokens, including 266,675 cache-write tokens,
and 103,077 output tokens; reported reasoning tokens were zero. These counts
exclude quality judging. Per-arm median generation latency was 58-85 seconds.

### Pipeline Issues Found During This Run

1. Same-timestamp, same-seed parallel manifests had isolated raw outputs but
   wrote quality files to the same global basename. Fixed `quality_paths()` to
   default beside each manifest, with regression tests. Rejudged the 19
   initially runnable stories into separate directories. Original logs,
   reports, logged summaries, and surviving shared files are preserved under
   `initial_shared_quality/`. **Initial `*.report.md` files are historical;
   their shared quality links are superseded by `runs.json` and this report.**
2. Source extraction included `phase=commentary` messages. It now excludes
   those messages while keeping legacy unphased responses compatible. This
   recovered one existing final-answer file. Its additional Mini rating at
   seed 781 is preserved under `garnet/recovery/` and merged into that arm's
   final quality JSONL. Before-recovery quality rows and local checks remain.

No generation was repeated. Total judging: 19 initial ratings, 19 isolated
reratings, and one recovered-file rating. No generated Python was manually
edited. Twenty-two focused factory/example and Puddles tests pass.

## Reuse

For another matched batch, use a fresh output and target directory:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_service_world_pipeline.py \
  -n 5 --seed 2026090605 --concurrency 5 \
  --model gpt-5.6-luna --reasoning-effort none --service-tier flex \
  --emit-mode source --max-output-tokens 32000 \
  --quality-model gpt-5.4-mini --repair-failures --qa-variants 10 \
  --example-file storyworlds/batches/luna_repaired_examples_20260907/garnet_humor_curiosity_repetition_tall_tale.py \
  --output-dir storyworlds/batches/<new-run> \
  --target-dir storyworlds/worlds/<new-run>
```

Repeat `--example-file` only when intentionally including multiple examples in
each request. This experiment used one per request, not all five together.
