# Agent Instructions: Implementing Story Kernels

This document provides instructions for coding agents (Claude, Cursor, etc.) working on the Storyweavers kernel implementation.

> **Engine:** Storyweavers runs on the **gen6** engine — all new work targets
> gen6. The previous **gen5** engine and its packs now live in [`legacy/`](legacy/)
> for reference only; they are no longer wired into the tooling (`coverage.py`,
> `sample.py`, `check_duplicates.py` all run on gen6).

---

## gen6 Authoring ⭐

gen6 is a typed, fault-tolerant engine. Key properties (and how it differs from
the legacy gen5 engine):

- **Typed dispatch, multiple variants.** A kernel name can have several
  implementations distinguished by parameter type hints (`Character`,
  `Physical`, `Actor`). The dispatcher binds arguments to the best-fitting
  variant; you don't parse `*args` yourself.
- **`Actor` = "the doer".** A parameter typed `Actor` matches a character
  argument, but also falls back to the current protagonist (`ctx.actor`) when
  omitted. Use it for the kernel's subject so implicit/nested calls still work.
- **Coherency layer is automatic.** Pronouns and transitions are applied by an
  AST pass + `ctx.say(subject)` — do **not** hand-roll pronoun logic in kernels.
- **Never crashes.** Unknown kernels / unmatched signatures degrade to a
  readable fallback sentence instead of raising. Your job is to raise *quality*,
  not to prevent exceptions.
- **Return a plain `str`** (one or more sentences). The engine wraps it in a
  `Trace` and records effects automatically.

### gen6 Workflow

> **⚠️ ALWAYS sample real usage BEFORE writing a kernel definition.** Do not
> guess a signature. Sample several stories that use the kernel, read how it is
> actually called in the dataset (positional vs keyword args, which types, what
> it composes with), and only then write the implementation + variants. This is
> the single most important rule for producing kernels that match real data.

```bash
# 1. Find high-frequency missing kernels (defaults to gen6)
python coverage.py --missing --top 30
python sample.py -l

# 2. REQUIRED: sample several real usages of the SPECIFIC kernel before coding it.
#    Read the argument shapes + what it pairs with; --show-source shows existing
#    variants and the original-vs-generated stories side by side.
python sample.py -k Quest -n 5 --seed 42 --show-source

# 3. Only now implement in a kernel pack (gen6kXX.py), then test
python gen6k01.py
python sample.py -k Quest -n 3 --seed 42

# 4. Measure coverage + end-to-end execution
python coverage.py --brief --execute 3000
python -c "from gen6registry import get_kernel_count, get_variant_count; print(get_kernel_count(), get_variant_count())"
```

Why sampling first matters in gen6: typed dispatch picks variants by argument
*shape*, so you must know the real shapes (e.g. `Quest(hero, goal=...)` vs
`Quest(Search(x), chars, result=...)`) to type the parameters correctly and add
the right extra variants. Skipping this step produces kernels that silently fall
through to the generic fallback.

### gen6 Kernel Template

```python
# gen6kXX.py
from gen6 import REGISTRY, World, Entity, Trace, Character, Physical, Actor, \
    to_phrase, state_to_phrase, action_to_phrase, event_to_phrase, NLGUtils

@REGISTRY.kernel("Discover")
def Discover(ctx: World, char: Actor, thing: Physical = None, **kw) -> str:
    """Discover(char, thing) / Discover(char) -- char finds something."""
    char.Joy += 0.4
    ctx.actor = char
    if thing is not None:
        ctx.current_object = thing
        return f"{ctx.say(char)} discovered {thing}."
    return f"{ctx.say(char)} made a wonderful discovery."

# Add another variant for a different argument shape:
@REGISTRY.kernel("Discover")
def DiscoverConcept(ctx: World, char: Actor, what, **kw) -> str:
    return f"{ctx.say(char)} discovered {to_phrase(what)}."
```

**Variable-arity characters (`*args`).** The dataset often passes a variable
number of characters (e.g. `Visit(zoo, Timmy, Mom, Gorilla)`,
`Apology(Anna, Ben, Lily)`). The binder supports `*args`, which can be
type-filtered — it only matches when *every* leftover positional arg fits:

```python
@REGISTRY.kernel("Visit")
def VisitPlaceGroup(ctx: World, place: Physical, *visitors: Character) -> str:
    if visitors:
        ctx.actor = visitors[0]
    names = NLGUtils.join_list([str(v) for v in visitors]) or "everyone"
    return f"{names} went to {place}."
```

`*args` constraints: fixed positional params before `*args` cannot be supplied by
keyword in the same call (rare in the dataset); keyword phases still go through
`**kw`. See `gen6k02.py` for a complete worked example built via this workflow.

Notes:
- **Meta / structural kernels** (Quest, Journey, Cautionary, Conflict,
  Resolution, Encounter, Transformation, Friendship-with-phases) take a subject
  plus `**kw` phases (`state`, `catalyst`, `process`, `insight`, `outcome`, …)
  and render each with the `*_to_phrase` helpers. See `gen6k01.py` for examples.
- **Memeplex `+=` behaviour** (e.g. `char.Fear += dog`) is defined separately
  with `@REGISTRY.addition("Fear", Character)` handlers in `gen6.py`.
- Use `ctx.say(subject)` for the grammatical subject; within a multi-sentence
  kernel use `subject.pronoun("subject")` for continuation sentences.

### Character Packs (`char6kXX.py`)

**Named characters with default type + traits go in `char6kXX.py` packs**, not in
the action-kernel packs. `gen6registry.py` auto-loads `char6kXX.py` the same way
it loads `gen6kXX.py`, so anything you register there is available everywhere.

Know which path applies before writing one:

- **Explicit declaration is handled by the engine — no pack needed.** A call
  whose first arg is `Character`, e.g. `Lily(Character, girl, Curious)`, is
  intercepted by the executor (`_character_decl`) and turned into an entity +
  "Once upon a time, there was a little curious girl named Lily." This is how the
  dataset declares characters almost everywhere, so it already works out of the box.
- **A `char6kXX.py` pack is only for the no-arg shorthand** (`Lily()`, `Mom()`,
  `Spot()`) and its per-name defaults. Without a pack, bare `Lily()` falls through
  to the generic fallback. Register one kernel per common name; the full
  `Lily(Character, …)` form still overrides the defaults.

Character names are auto-detected and **excluded from coverage**, so a char pack
does not move the coverage number — it improves the *readability* of stories that
use the shorthand. Template (typed like any gen6 kernel, returns `str`):

```python
# char6k01.py - named-character defaults (auto-loaded by gen6registry)
from gen6 import REGISTRY, World, NLGUtils

def _named(name: str, kind: str, *traits: str):
    @REGISTRY.kernel(name)
    def _decl(ctx: World, *args, **kw) -> str:
        if name in ctx.entities:                 # already introduced -> refocus
            ctx.actor = ctx.entities[name]
            return ""
        first = not any(e.kind == "character" for e in ctx.entities.values())
        ent = ctx.character(name, kind, list(traits))
        ctx.actor = ent
        lead = "little " if kind in ("boy", "girl", "child") else ""
        desc = f"{lead}{(traits[0] + ' ') if traits else ''}{kind}".strip()
        art = NLGUtils.article(desc)
        if first:
            return f"Once upon a time, there was {art} {desc} named {name}."
        return f"There was also {art} {desc} named {name}."

for _n, _k, *_t in [
    ("Lily", "girl", "curious"), ("Tim", "boy", "curious"),
    ("Mom", "mother", "caring"), ("Spot", "dog", "loyal"),
]:
    _named(_n, _k, *_t)
```

(The previous engine's `char5k01.py` has ~70 such names; porting it to
`char6k01.py` is a tracked TODO. Ideally factor the intro sentence into one shared
gen6 helper so the pack and `_character_decl` stay in sync.)

### gen6 Quality Pass: World Model & Rewrites

After a batch of kernels is added (or periodically), do a **quality pass**.
Coverage measures *whether* a kernel runs; this pass measures *how well the
story reads*. Run it whenever `--execute` is healthy but you haven't eyeballed
real output recently.

**Step A — Audit fully-covered stories (read real output).** Coverage hides
quality problems, so generate stories where *every* kernel is implemented and
read them:

```bash
python - <<'PY'
import json, random
from coverage import extract_character_names, count_coverage
from gen6registry import REGISTRY, generate_story
impl = set(REGISTRY.kernels)
rows = []
with open("TinyStories_kernels/data00.kernels.jsonl") as f:
    for i, line in enumerate(f):
        if i >= 20000: break
        k = json.loads(line).get("kernel", "") or ""
        try: import ast; ast.parse(k)
        except: continue
        ch = extract_character_names(k); cov, tot = count_coverage(k, impl, ch)
        if tot >= 6 and cov == tot: rows.append((i, k))
random.seed(0)
for i, k in random.sample(rows, 5):
    print(f"=== data00:{i} ==="); print(generate_story(k)); print()
PY
```

For a specific kernel, `python sample.py -k Quest -n 5 -s` shows original-vs-
generated side by side.

**Step B — Recognise the recurring bug classes** (and where each is fixed):

| Symptom in output | Cause | Fix location |
|---|---|---|
| One line for a rich call (`Guidance(L, state=…, process=…)` → "L offered guidance.") | Simple kernel ignores phase kwargs | Route to `meta_story` when `is_meta_call(kw)` |
| Double subject ("Leo was Leo really wanted…") | String-splicing a child sentence into "X was {…}" | Use `render_state/action/outcome` + `child_sentences` |
| Repeated name ("Sam ran. Sam fell.") | No pronoun continuation | Build a sentence list, return `coherent(ctx, hero, sents)` |
| Bare concept jammed mid-sentence ("…butterfly. indifference Leo…") | `+` chain with a non-kernel concept | handled by `_combine`; emit concepts as own sentence |
| Literal concept ("something threat happened") | Bare-name kernel not executed as a value | handled by executor `value()`; ensure name is registered |
| Verbed noun ("Tom gratituded", "X warmthed") | stray kwarg or abstract noun hit the fallback | binder drops stray kwargs; `_looks_nounish` in `fallback_text` |
| Clause in a noun slot ("wanted Nemo explored the coral") | `to_phrase(Trace)` in an object slot | reduce the Trace (past→infinitive) — open limitation |

**Step C — Prefer the world model over bespoke string logic.** The engine
already tracks entities, memes (`Joy`, `Fear`, `Friendship`, …) and the current
actor. Use that instead of re-deriving things:

- **Subject/coherence:** end multi-sentence kernels with
  `return coherent(ctx, hero, sentences)` — it collapses repeated hero names to
  pronouns using the entity's pronoun, and respects the AST `_use_pronoun` flag.
- **Phase rendering:** assemble `sentences` with the shared helpers
  (`render_state`, `render_action`, `render_event`, `render_outcome`,
  `render_clause`, `child_sentences`) or just call `meta_story(ctx, hero, kw)`.
- **State-aware text:** read accumulated memes to vary prose. Example —
  `HappyEnd` reads `Joy`/`Love` vs `Sadness`/`Fear` and `Friendship` links to
  choose its closing line. Reading state often removes the need for a rewrite.
- **`Actor` fallback:** type a subject param `Actor` (not `Character`) so
  object-first calls inside process chains attach to the protagonist
  (`See/Find/Play/Search` do this).

**Step D — Use rewrites for normalization & enrichment** (`DEFAULT_RULES` in
`gen6.py`). Rewrites run on the AST *before* execution; metavars are `__NAME`:

```python
DEFAULT_RULES = [
    # Enrichment: add an implied trait
    Rewrite(pattern_src="__C(Character, mother, Strict)",
            output_src="__C(Character, mother, Strict + Caring)"),
    # Normalization: attach a bare emotion to the right subject
    Rewrite(pattern_src="Warning(__S, __C) + Anger",
            output_src="Warning(__S, __C) + Anger(__S)"),
]
```

Use a rewrite when the *structure/arguments* are wrong (a bare emotion that
belongs to a subject, an implied prerequisite, an enrichable character). Use the
**world model** when *runtime state* should drive the text. They compose:
`Fear(C, dog) + Brave(C)` needs no rewrite because `Brave` reads accumulated
`Fear` and narrates "Even though X was afraid, X was brave."

**Step E — Re-measure and don't regress.** Confirm execution stayed high and
spot-check the same stories before/after:

```bash
python gen6.py && python gen6k01.py && python check_duplicates.py
python coverage.py --brief --execute 3000   # execute % must not drop
```

Record what you changed and any remaining limitations in `TODO.md` (there is a
"Quality pass" section to extend), so the next run starts from the known state.

### gen6 Key Files

| File | Purpose | Modify? |
|------|---------|---------|
| `gen6.py` | Engine: typed world/dispatch, AST rewrites, coherency, NLG, fallback | Engine changes only |
| `gen6kXX.py` | Action/structural kernel packs (`gen6k01`, `gen6k02`, …) | Add to or create a new pack |
| `char6kXX.py` | Named-character default packs (auto-loaded) | Add named characters here |
| `gen6registry.py` | Auto-loads all `gen6kXX.py` / `char6kXX.py` packs — **always import from here** | NO |
| `coverage.py` / `sample.py` | Coverage + sampling tooling (gen6) | NO |
| `check_duplicates.py` | Finds duplicate typed variants (same name + identical signature) | NO |

---

## Pinning Good Stories as Tests

When a kernel reliably produces good output, pin the story as a regression test
so later changes can't silently degrade it:

```bash
python sample.py -k Boo -n 5 --seed 42      # note the STORY ID (e.g. data00:123)
python story_tests.py --pin data00:123 --description "Tests Boo improvements"
python story_tests.py --run                  # verify; unified diff on mismatch
git add story_tests/data00_123.txt story_tests/index.json
```

Story IDs are stable and generation is deterministic, so a pinned ID always
reproduces the same output.

> **Note:** the pinned-story harness is being repointed at gen6. Some older
> gen5-era pins currently fail (gen5-style prose); re-pin them once the gen6
> output for those stories is good. See `story_tests/README.md`.

## Checking Coverage

```bash
python coverage.py                            # full report (defaults to data00)
python coverage.py --brief                    # one-line totals
python coverage.py --brief --execute 3000     # + end-to-end execution success rate
python coverage.py --missing --top 30         # top missing kernels
python coverage.py --missing --top 30 -d TinyStories_kernels/data01.kernels.jsonl
python coverage.py --implemented              # top implemented kernels
```

Coverage counts genuine narrative kernels; character names (`Lily(Character, …)`)
are auto-detected and excluded. Current metrics and the missing-kernel backlog
live in `TODO.md`.

## Philosophy

- **Always import from `gen6registry`** — it loads every pack; importing `gen6`
  alone sees only the engine's built-in kernels.
- **Use `sample.py` / `coverage.py`** — don't hand-roll scripts that import a
  single module; the tools see the full registry.
- **Sample before implementing** — match real dataset shapes (typed dispatch
  depends on it).
- **Compare before finishing** — `--show-source` shows original-vs-generated.
- **Prefer the world model** — let accumulated state (memes, actor, links) and
  the coherence pass drive prose; reach for rewrites only to fix structure.
- **Keep `gen6.py` lean** — add kernels in packs (`gen6kXX.py` / `char6kXX.py`);
  reserve engine edits for shared infrastructure.
- **No LLMs at runtime** — all generation is classical execution.

---

## Cursor Cloud specific instructions

This is a **pure-Python, stdlib-only CLI/library project** (no web server, GUI,
or database). "Running the application" means generating stories from kernels:
`python gen6.py` (engine demo), `python gen6registry.py` (lists packs + counts),
or `from gen6registry import generate_story` in Python. Standard
lint/test/coverage commands are already documented above and in `README.md`.

Non-obvious environment caveats:

- **`python` is required, not just `python3`.** The base VM only ships
  `python3`, but `story_tests.py` shells out to `python` and the docs use
  `python ...`. VM setup creates a symlink (`/usr/local/bin/python` →
  `/usr/bin/python3`, Python 3.12). If `python` is ever missing, recreate it:
  `sudo ln -sf /usr/bin/python3 /usr/local/bin/python`.
- **No third-party packages for the core flow.** The gen6 engine, packs, and the
  `coverage.py` / `sample.py` / `check_duplicates.py` / `story_tests.py` tools
  are stdlib-only — there is nothing to `pip install`. (Optional peripheral
  scripts not in the core flow need extras: `kernel.py`→`openai`+`tqdm`+an LLM
  server; `cluster.py`→`numpy`+`scikit-learn`; `test.py`→a GPU RAPIDS stack.)
- **Dataset is git-LFS `.bz2`; tooling reads decompressed `.jsonl`.**
  `coverage.py` / `sample.py` / `story_tests.py` default to
  `TinyStories_kernels/data00.kernels.jsonl`. The repo only ships
  `*.kernels.jsonl.bz2` (the `.jsonl` form is git-ignored), so it must be
  decompressed. The startup/update script decompresses `data00`. To use another
  shard (`data01`..`data14`, or the combined `data`), decompress it first:
  `bunzip2 -k TinyStories_kernels/data01.kernels.jsonl.bz2`.
- **Known-failing pinned story tests.** `python story_tests.py --run` currently
  reports `data00_14193`, `data00_3216`, and `data00_83` as FAIL — these are the
  gen5-era pins the README/quality-pass notes flag for re-pinning, **not** an
  environment problem. Re-pin them once their gen6 output is good.
