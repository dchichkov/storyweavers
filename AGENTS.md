# Agent Instructions: Implementing Story Kernels

This document provides instructions for coding agents (Claude, Cursor, etc.) working on the Storyweavers kernel implementation.

> **Engine:** Storyweavers runs on the **gen6** engine — all new work targets
> gen6. The previous **gen5** engine and its packs now live in [`legacy/`](legacy/)
> for reference only; they are no longer wired into the tooling (`coverage.py`,
> `sample.py`, `check_duplicates.py` all run on gen6).

---

## ⭐ North Star — keep aligned with the Memeplex Model

The project's canonical design is the **memeplex model** in **[`story.py`](story.py)**
(summarized in the [README North Star](README.md#-north-star-the-memeplex-model--see-storypy);
backlog in [`TODO.md`](TODO.md) "North Star"). Coverage and quality work are means
to that end — do not let them drift away from it. Before any non-trivial engine
change, re-read `story.py` and check your change against these principles:

1. **Memeplex == story.** Concepts (`Love`, `Fear`, `Envy`), actions, characters,
   and whole narratives are the *same kind* of composable object (`+`, `+=`, `/`).
2. **Embed-or-zero-weight.** A memeplex only affects the narrative once embedded
   in a physical carrier (book / person / many people). *"Stories need to have
   associated physical objects, or story weight is zero."* An un-embedded concept
   must **not** surface (this is the root of the `literal_concept` defect — a bare
   concept should bind to `ctx.actor` / `ctx.current_object` and render its
   physical manifestation, or be dropped).
3. **Track the physical level + concept magnitudes.** Carriers hold how much of
   each concept is present (`Entity.memes`); let that accumulated state drive the
   prose (prefer the world model — see the quality-pass guidance below).
4. **Only allow compatible moves.** Keep generated narrative consistent with the
   memeplexes already present (e.g. a maxed-`Envy` `Scar(Character, lion)` should
   not do out-of-character kind acts unless the embedded state changes first).

**When you touch the engine:** state in your PR how the change moves *toward* (or,
if unavoidable, why it deviates from) this north star. New kernels should let
embedded state drive text and avoid emitting un-embedded concepts as bare "There
was X." sentences.

---

## gen7 Prototype Work: StoryWorld, Sampling, and QA

gen7 is an active prototype, separate from gen6, for testing the MUD-like
StoryWorld direction. gen7 work should still follow the memeplex north star:
parse kernel ASTs into executable world frames, apply them to persistent state,
then render narrative and QA from that state. Do not turn gen7 QA into
post-processing over English prose when the frame/world trace can answer it.

For standalone `storyworlds/` scripts, also follow [`storyworlds/AGENTS.md`](storyworlds/AGENTS.md):
green constraints and grounded QA are not enough. Random samples should read
like complete stories, with a clear premise, a state-driven turn, and an ending
image that proves what changed. Treat `missing_beginning`, `missing_ending`,
`event_log_prose`, `raw_fact_fragment`, `no_final_image`, and `weak_turn` as
storytelling quality defects.

Useful commands:

```bash
python gen7.py --story-id data00:36222
python gen7.py --story-id data00:36222 --qa --qa-limit 8
python gen7_story_tests.py --run
python gen7_story_tests.py --run-qa --qa-limit 12
python gen7_story_tests.py --sample 10 --seed 777 --scan 20000 --show-qa --qa-limit 8 --show-kernel
```

### gen7 QA Quality Passes

Treat question/answer generation as part of narrative quality, not a side demo.
When improving gen7, sample QA alongside generated text and the original story,
read the failures, and improve repeated classes. The smoke test must stay green,
but green smoke only proves basic shape; it does not prove quality.

Every gen7 quality pass should include a QA pass:

1. Run `gen7_story_tests.py --sample ... --show-qa --show-kernel` and read
   original text, kernel source, generated text, questions, and answers together.
2. Fix repeated narrative or QA failures in the frame/world layer when possible.
3. Promote 5-10 rough-but-representative sampled cases into `STORY_IDS` and
   `gen7_story_tests/`, especially cases whose QA exposes role, ownership,
   causality, object-state, or lesson drift.
4. Keep both `gen7_story_tests.py --run` and
   `gen7_story_tests.py --run-qa --qa-limit 12` green before finishing.
5. Update `TODO.md` with the sampled QA defects and the next measurable smoke
   gate to add.
6. If multi-turn QA has a prototype, sample follow-up conversations in the same
   pass and judge whether the follow-up stays anchored to the prior frame/entity.

QA should be generated from `StoryWorld.history`, entity state, meme magnitudes,
relations, and frame metadata. A good QA pair is answerable from the simulated
world, grounded in entities/events that actually exist, and useful for checking
whether the engine preserved causality, ownership, roles, and lesson state.

Target answer style:

- Prefer full natural-language responses over bare noun phrases.
- Use two or three short sentences when the trace supports cause/effect or
  temporal context; one-sentence answers are only acceptable when the trace is
  genuinely too thin.
- Keep answers grounded: no entities, motives, or outcomes that are not present
  in the world trace.
- Diversify question kinds across a sample: who/what/where/how/why/what-next,
  plus role, object-state, instrument, lesson, and causal questions.
- Avoid duplicate shallow questions that only restate declarations.
- Prefer causal/contextual second sentences over generic audit sentences such as
  "That event is recorded in the story world" whenever the trace contains the
  relevant cause, result, owner, location, or later consequence.

When touching QA, update or extend `gen7_story_tests.py --run-qa` so it measures
more than nonempty output. Useful deterministic checks include duplicate-rate,
question-kind distribution, answer length/full-sentence rate, grounded entity
mentions, answerability from `StoryWorld`, and whether every QA answer is tied to
a frame/entity id. Keep the smoke test as a real quality signal: it should fail
when answers regress to bare fragments, duplicate shallow questions, or
single-sentence responses across the pinned suite. Record known QA defects in
`TODO.md` using a controlled
vocabulary such as `bare_answer`, `ungrounded_answer`, `duplicate_question`,
`wrong_focus`, `missing_causality`, `not_answerable`, `too_shallow`, and
`followup_lost_context`.

Each gen7 quality pass should sample original text, generated narrative, and QA
together; promote 5-10 rough-but-representative cases into the pinned suite; and
keep full multi-sentence responses green in the smoke test before adding new QA
surface area.

Multi-turn QA is a desired gen7 milestone. Implement it as conversation state
over the same `StoryWorld`, not as free-form text chat: follow-up questions such
as "Why?", "What happened next?", "Who helped?", and "Where was it?" should
resolve against the last referenced entity/event/question type. Multi-turn
answers should keep the same full-response, multi-sentence standard as ordinary
QA, and should fail closed when the trace has no grounded answer.

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

## Measuring Story Quality (agent-as-judge)

Coverage measures *whether* kernels run; it says nothing about whether the story
reads well. **`QUALITY.md`** defines an agent-as-judge protocol for that, with a
reproducible harness:

```bash
python quality.py --sample -n 100 --seed 42 --out quality_runs/run.jsonl
# (grade each record's scores/usable/defects per QUALITY.md)
python quality.py --report quality_runs/run.jsonl
```

`--sample` writes a deterministic worksheet of (original, kernel, generated)
triples; a coding agent scores each on 6 dimensions (grammar, coherence,
fidelity, completeness, naturalness, overall), marks `usable`, and tags
`defects` from a controlled vocabulary. `--report` aggregates means, the usable
rate, quality-by-coverage-tier, and a **defect-frequency table** that points
straight at the next quality pass. The worksheet is line-oriented JSONL so it
shards across many parallel agents. Read `QUALITY.md` before grading.

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
