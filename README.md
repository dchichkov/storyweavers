# Storyweavers

**Narrative Algebra: Extracting and Composing Story Kernels**

Storyweavers explores whether stories can be decomposed into compact, algebraic "kernels" — composable narrative patterns that can generate surface text. The project extracts these kernels from the TinyStories dataset (~2M children's stories) and investigates whether a small library of ~1-5K kernels can reconstruct coherent story datasets.

## ⭐ North Star: The Memeplex Model — see [`story.py`](story.py)

The canonical design lives in **[`story.py`](story.py)** (the "Storyweavers Design Summary"). Everything in this repo should be measured against it. The core idea:

- **Everything is a memeplex, and a memeplex *is* a story.** A concept (`Love`, `Fear`, `Envy`), a verb/action, a character, and a whole narrative are the *same kind of object* — composable via the algebra (`+` composition / co-occurrence, `+=` accumulation, `/` attention dilution). They differ only in scale, not in kind.
- **Memeplexes are platonic forms; they only matter once *embedded* in a physical carrier.** A memeplex must be embedded in something physical — captured in a *book*, alive in a *person*, or alive across *many people* — to affect the narrative. *"Stories need to have associated physical objects, or story weight is zero"* (`story.py`). An un-embedded concept has **zero weight** and must not change the story.
- **Track the physical level and how much of each concept is present.** Each physical carrier holds *magnitudes* of the concepts embedded in it (`Entity.memes` in `gen6.py` is the seed of this). The story is the evolving state of these embedded magnitudes.
- **The world model should only allow *compatible* moves.** Generation must be consistent with the memeplexes already present and how they interact. Example: declare a lion `Scar(Character, lion)` and max out its `Envy` memeplex — the world model should then only permit Envy-compatible moves, and the generated narrative must stay consistent with a maxed-Envy character (no out-of-character kindness unless something first changes the embedded state).

> **Worked example.** `Listen(animal, other, Content)` embeds a fraction of `Content` into `animal` (`animal.Story += Content / 10`) and weakly merges group identity (`animal.We += other.We / 100`). The `/` keeps weak influences weak; only embedded, sufficiently-weighted memeplexes surface in the narrative. See the `Listen` / `Purr` / `Tell` / `Care` sketches in `story.py`.
>
> **Runnable proof-of-concept on gen6:** [`memeplex_demo.py`](memeplex_demo.py) implements `Listen` / `Purr` as gen6 kernels that move `Story`/`Love`/`We` magnitudes between carriers (attention-diluted as in `story.py`). Crucially the **accumulated weights drive the prose**: more purrs raise the listener's `Love`, which escalates the narration and changes a state-chosen ending (`Closeness` reads the pair's total `Love` + shared `Story` links). It also reframes `Tell → Listen` with an AST rewrite. Run `python memeplex_demo.py`.

**Where the implementation stands vs. the north star** (honest):

| Principle | Status in `gen6.py` |
|---|---|
| Per-carrier concept magnitudes (`Entity.memes`) | ✅ partial — exists and accumulates |
| Concept embedding via `+=` (`@REGISTRY.addition`) | ✅ partial — some concepts attach to carriers |
| **Embed-or-zero-weight** (drop un-embedded concepts) | ❌ not enforced — surfaces as the `literal_concept` defect ("There was bravery.") |
| **Memeplex == story** (one uniform representation) | ❌ kernels, concepts, characters are still three things |
| **Compatibility / only-allow-compatible-moves** | ❌ not built (design sketch in `TODO.md` → `constraint_pass`) |
| Physical / plausibility model | ❌ minimal (object owner/status only) |

See [`TODO.md`](TODO.md) for the north-star backlog that closes these gaps, and [`QUALITY.md`](QUALITY.md) for how quality/fidelity is measured against it.

## TODO
**[TODO.md](TODO.md)** For gaps and next steps. The top of TODO.md has a status update on the unified `gen6.py` engine.

### `gen6.py` — Unified Engine (typed world + rewrites + coherency) ⭐ New

`gen6.py` assembles the experiments below into a single, self-contained engine:

```
source --[declarative rewrites]--> --[coherence tagging]--> --[typed-world execution]--> --[narrate]--> story
```

- **Typed kernels + dispatch** (from `wrld6.py`): kernels declare typed params (`Character`, `Physical`, `Actor`); a backtracking binder selects the matching variant; uppercase "meme" slots carry concept-specific `+=` behaviour; effects and narration are traced automatically.
- **AST → AST rewrites** (from `rewr6.py`): declarative rules rewrite kernel source **before** execution (normalization, enrichment, prerequisites). Patterns use kernel calls + `+` composition with `__`-prefixed metavariables (e.g. `__C`, `__S`).
- **Coherency layer**: a single AST pass (`tag_coherence`) tracks narration order and tags repeated-subject kernels so the renderer uses **pronouns** (and `_transition` connectors) — instead of every kernel deciding this on its own.

```bash
python gen6.py
```

```python
from gen6 import generate
print(generate("""
Lily(Character, girl, Curious)
Fear(Lily, dog) + Brave(Lily)
Joy(Lily)
"""))
# "Once upon a time, there was a little curious girl named Lily.
#  Lily became afraid of the dog. Even though she was afraid, she was brave.
#  She felt full of joy."
```

**Kernel packs & tooling.** Additional kernels live in `gen6kXX.py` packs and are auto-loaded by `gen6registry.py`. The analysis tools run on gen6:

```bash
python coverage.py --brief --execute 3000         # measure dataset coverage
python sample.py -k Quest -n 3 --seed 42 --show-source
python check_duplicates.py                         # find duplicate typed variants
python gen6registry.py                             # list loaded packs + kernel/variant counts
```

gen6 executes ~all parseable stories end-to-end (the typed dispatch degrades unknown kernels to a readable fallback instead of raising). The remaining work is growing the kernel library; see [TODO.md](TODO.md) for the roadmap and current metrics. `wrld6.py` / `rewr6.py` are the reference demos `gen6.py` was built from. The previous engine (`gen5.py` and its `gen5kXX` / `char5kXX` packs) now lives in [`legacy/`](legacy/) for reference only — it is no longer wired into the tooling.

### AST → AST Transforms (Reference Demos)

`rewr6.py` (which composes with `wrld6.py`) is the rewrite prototype `gen6.py` was built from:

- **Purpose**: apply declarative “story algebra” rewrite rules to the kernel source **before** execution (pronouns, transitions, prerequisites, normalization).
- **Rule syntax**: write patterns and outputs using kernel calls and `+` composition; use `__`-prefixed names (e.g. `__C`, `__OBJ`) as metavariables inside rewrite patterns.

Try them:

```bash
python wrld6.py
python rewr6.py
```

`ast_rewrite_transform_demo.py` shows the next step: a candidate AST transform
that only applies after both structural and world-model checks pass. The demo
tries to rewrite `Friendship(__A, __B)` into `Lovers(__A, __B)`, but skips the
rewrite when the second endpoint is not a declared character, or when executing
the story up to the old ending leaves too little embedded `Love` in either
carrier. When mutual hugs have already embedded enough `Love`, the generated
ending changes from "became good friends" to "let their friendship grow into
love."

```bash
python ast_rewrite_transform_demo.py
```

## Core Concept: Story Kernels

A **story kernel** is a symbolic, algebraic representation of a narrative's structure. It captures characters, their traits, narrative arcs, and emotional transformations in a composable format.

### Example

**Original Story:**
> Once upon a time, there was a big whale. The whale loved to swim in the deep blue sea. The whale was very delicate and kind to all the little fish. One day, the whale wanted to test how fast he could swim...

**Extracted Kernel:**
```python
Whale(Character, Imaginary, Delicate + Kind)
Test(Speed) + Community(Support, cheered) + Happy
Identity(Whale,
         new=Shark,
         reaction=Acceptance + Community(Support, Liked))
```

### Kernel Syntax

| Syntax | Meaning |
|--------|---------|
| `Name(...)` | Story kernel (uppercase = composable pattern) |
| `object` | Physical/concrete object (lowercase = terminal node) |
| `+` | Composition, co-occurrence |
| `/` | Attention dilution (e.g., `Fear / 10`) |
| `\n` | Sequence, temporal progression |
| `[a, b, c]` | Lists |

## Project Pipeline

```
TinyStories Dataset (2M stories)
         │
         ▼
    ┌─────────────┐
    │  kernel.py  │  ← LLM-based kernel extraction
    └─────────────┘
         │
         ▼
   .kernels.jsonl files
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌───────────┐
│sample.py│ │ AGENTS.md │  ← Analysis & Implementation
└─────────┘ └───────────┘
                │
                ▼
    Story Generation Engine and Kernels implementation
         │
         ▼
    ┌──────────┐
    │  gen6.py │  ← Classical NLG generation engine (typed world + rewrites)
    └──────────┘
         │
         ▼
   Generated stories
```

## Key Components

### `kernel.py` — Kernel Extraction
Uses LLMs (via OpenAI-compatible API) to extract story kernels from raw text. Processes the TinyStories dataset with async concurrency.

### `gen6.py` — Classical Generation Engine ⭐

The generation engine converts kernels to stories **without LLMs at runtime**. Uses:
- Python AST parsing (kernels are valid Python)
- Declarative AST → AST rewrites (normalize / enrich before execution)
- A coherence pass that tags repeated subjects for pronoun use
- Typed-world execution with a backtracking variant binder and traced narration

**Key design:** Kernels ARE valid Python code. They're parsed with `ast.parse()`, rewritten, then executed against a registry of typed kernel variants.

## Generation Engine Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         KERNEL STRING                                │
│  "Lily(Character, girl, Curious)                                    │
│   Journey(Lily, catalyst=Discovery(rainbow), transformation=Happy)" │
└─────────────────────────────────────────────────────────────────────┘
                                 │  ast.parse()
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Declarative rewrites (DEFAULT_RULES)               │
│   pattern → output over kernel calls + `+` composition; metavars     │
│   (`__C`, `__OBJ`) normalize / enrich the AST before execution       │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Coherence pass (tag_coherence)                     │
│   tags repeated-subject kernels so the renderer uses pronouns        │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Executor (typed world)                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ eval(node)                                                   │   │
│  │   ├── ast.Call → backtracking binder picks a typed Variant  │   │
│  │   ├── ast.BinOp(+) → _combine() traces / concepts           │   │
│  │   ├── ast.BinOp(/) → attention dilution                     │   │
│  │   └── ast.Name → resolve Entity, concept, or bare kernel    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
          ┌─────────────┐ ┌───────────┐ ┌─────────────┐
          │  Registry   │ │   World   │ │  NLGUtils    │
          │ name→[typed │ │ entities  │ │ past_tense   │
          │  Variants]  │ │ memes     │ │ article      │
          │ @kernel()   │ │ actor /   │ │ join_list    │
          │ + additions │ │ traces    │ │ meta_story   │
          └─────────────┘ └───────────┘ └─────────────┘
                    │            │            │
                    └────────────┼────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            Trace                                     │
│  { kernel: "Discovery", text: "Lily discovered a rainbow.",         │
│    effects: [...] }   ← appended to world.traces for top-level stmts │
└─────────────────────────────────────────────────────────────────────┘
                                 │  narrate(traces)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        GENERATED STORY                               │
│  "Once upon a time, there was a little curious girl named Lily.     │
│   Lily discovered a rainbow. She felt happy."                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Data Structures

| Class | Purpose | Key Fields |
|-------|---------|------------|
| `Entity` | Character or physical object with meme state | `name`, `kind`, `traits`, meme slots (`Joy`, `Fear`, `Love`, …), `pronoun` |
| `Trace` | Narration + effects produced by a kernel call | `kernel`, `text`, `effects` |
| `World` | Execution state for generation | `entities`, `actor`, `current_object`, `traces`, memes/links |
| `Variant` | One typed implementation of a kernel name | `name`, `fn`, `signature`, `hints` |
| `Registry` | Maps kernel names → list of typed variants | `kernels`, `additions` |
| `Executor` | AST interpreter (binds + executes variants) | `eval()`, `execute_tree()` |

### Kernel Function Pattern (typed dispatch)

```python
from gen6 import REGISTRY, World, Actor, Physical

@REGISTRY.kernel("KernelName")
def KernelName(ctx: World, hero: Actor, thing: Physical = None) -> str:
    """Kernel that does something.

    Parameters are *typed*: the binder selects this variant when the args
    match (e.g. a character + an object). `Actor` falls back to the current
    protagonist when no character is passed.
    """
    hero.Joy += 1                     # meme update on the world model
    if thing is not None:
        return f"{ctx.say(hero)} did something with {thing}."
    return f"{ctx.say(hero)} did something."
```

### Helper Functions

| Function | Purpose |
|----------|---------|
| `to_phrase(value)` | Convert any value to natural language phrase |
| `state_to_phrase(value)` | Convert state/emotion to descriptive phrase |
| `action_to_phrase(value)` | Convert action to past-tense verb phrase |
| `event_to_phrase(value)` | Convert event to "One day, X happened" format |
| `meta_story(world, hero, kw)` | Render a multi-phase structural kernel with coherent pronouns |
| `coherent(world, hero, sentences)` | Collapse repeated subjects to pronouns |
| `NLGUtils.past_tense(verb)` | Conjugate verb to past tense |
| `NLGUtils.article(word)` | Get "a" or "an" for word |
| `NLGUtils.join_list(items)` | Join with Oxford comma |

```python
from gen6 import generate

kernel = '''
Lily(Character, girl, Resourceful)
Encounter(Lily, wolf, forest)
Fear(Lily)
Brave(Lily)
Run(wolf)
'''

print(generate(kernel))
# "Once upon a time, there was a little resourceful girl named Lily.
#  Lily came across a wolf in the forest. She became afraid.
#  Even so, she was brave. The wolf ran away."
```


### `sample.py` `parse.py` `coverage.py` — Kernel Analysis
Parses extracted kernels, computes statistics, and identifies the most common narrative patterns.

### `story.py` — ⭐ Canonical Design (Memeplex Model / North Star)
The **design summary and reference for the whole project** (see [North Star](#-north-star-the-memeplex-model--see-storypy)). Defines the memeplex model: `Story` (memetic, composable, uppercase) vs `physical` (atomic, terminal, lowercase); characters inherit from both; **a `Story` has weight only when embedded in a physical carrier** ("Stories need to have associated physical objects, or story weight is zero"); attention algebra (`+`, `+=`, `/`); and a physics/plausibility model for consistency. `gen6.py` currently realizes only part of this — `story.py` is the north star the engine is being pulled back toward.

## Adding New Kernels (Coding Agent Workflow)

The approach for expanding kernel coverage is **interactive development with a coding agent** (like Claude, Cursor, etc.) rather than automated LLM synthesis.
See `AGENTS.md`


## Goals

**Current:**
- Extract ~1-5K executable kernels from TinyStories (2M samples)
- Test if coherent datasets can be reconstructed from < 5K kernels
- Train LLMs on kernel-generated stories and compare performance

**Future:**
- Evaluate impact of present/absent kernels on LLM capabilities
- Extract kernels from diverse sources (children's books, movies, religious texts)
- Map to existing narrative taxonomies (ATU-AT-Motif, etc.)
- Apply to non-narrative data (intent analysis, etc.)

## Data

- **`TinyStories_all_data/`**: Original TinyStories JSON files (data00-data49.json)
- **`TinyStories_kernels/`**: Extracted kernels in JSONL format
- **`bak/`**: Backup kernel files

## Usage

### Extract Kernels (requires LLM)
```bash
export LOCALHOST_BASE_URL="http://localhost:8001/v1"
export LOCALHOST_API_KEY="your-key"
python kernel.py
```

### Analyze Kernels
```bash
python parse.py
```

### Cluster Story Patterns
```bash
python cluster.py
```

### Generate Stories (no LLM needed)
```bash
python gen6.py                 # run the engine demo
python gen6registry.py         # list loaded packs + kernel/variant counts
```

### Generate from Custom Kernel
```python
from gen6 import generate

kernel = '''
Tim(Character, boy, Brave)
Monster(Character, scary)
Encounter(Tim, Monster)
Fear(Tim)
Brave(Tim)
Run(Monster)
Joy(Tim)
'''

print(generate(kernel))
```

> To use the full kernel library (all packs), import from `gen6registry`:
> `from gen6registry import generate_story`.

## Philosophy

The project is grounded in the **memeplex model** (canonical statement in [`story.py`](story.py); summarized in [North Star](#-north-star-the-memeplex-model--see-storypy) above): narratives are reusable **memetic objects** that propagate through culture, where a concept, an action, a character, and a whole story are the *same kind of composable object* — and a memeplex only affects the narrative once it is **embedded in a physical carrier** (book / person / many people); un-embedded memeplexes have zero weight. By decomposing stories into kernels, we can:

1. **Compress** narrative knowledge into a small, interpretable library
2. **Compose** new stories by combining kernels algebraically
3. **Analyze** what fundamental patterns make stories work
4. **Train** models on structured narrative representations

The generation engine should let **embedded memeplex state drive the prose** and only permit **compatible moves** (consistent with the concepts already present and how they interact), rather than executing kernels blindly.

**LLM usage is restricted to synthesis time** (extracting kernels, clustering, defining new kernel implementations). At generation time, stories are produced through classical execution — no LLM calls, just template filling and compositional algebra.

This is an exploration of story as code — where narrative structure becomes executable algebra.

## File Overview

| File | Purpose | LLM Required |
|------|---------|--------------|
| `kernel.py` | Extract kernels from stories | ✅ Yes |
| `parse.py` | Analyze kernel statistics | ❌ No |
| `cluster.py` | Cluster similar stories | ❌ No |
| `sample.py` | Sample & explore kernel usage (gen6) | ❌ No |
| `coverage.py` | Check kernel implementation coverage (gen6) | ❌ No |
| `quality.py` | Story-quality eval harness (agent-as-judge; see `QUALITY.md`) | ❌ No |
| `check_duplicates.py` | Find duplicate typed variants (gen6) | ❌ No |
| `gen6.py` | Unified engine: typed world + AST→AST rewrites + coherency layer | ❌ No |
| `gen6registry.py` | Auto-loads `gen6kXX` / `char6kXX` packs into one registry | ❌ No |
| `gen6k01.py`, `gen6k02.py`, … | Kernel packs (added kernels) | ❌ No |
| `wrld6.py` | Typed world / dispatch prototype (demo `gen6` builds on) | ❌ No |
| `rewr6.py` | AST→AST rewrite engine prototype (demo `gen6` builds on) | ❌ No |
| `story.py` | ⭐ **Canonical design / north star** — the memeplex model (memeplex == story, embed-or-zero-weight, physical carriers, compatibility) | ❌ No |
| `AGENTS.md` | Instructions for coding agents | ❌ No |
| `legacy/` | Previous engine (`gen5.py`, `gen5kXX`, `char5kXX`, older `gen*.py`) — reference only | ❌ No |

## For Coding Agents

See **[AGENTS.md](AGENTS.md)** for detailed instructions on implementing new kernels.
