# Storyweavers

**Narrative Algebra: Extracting and Composing Story Kernels**

Storyweavers explores whether stories can be decomposed into compact, algebraic "kernels" — composable narrative patterns that can generate surface text. The project extracts these kernels from the TinyStories dataset (~2M children's stories) and investigates whether a small library of ~1-5K kernels can reconstruct coherent story datasets.

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
    │  gen5.py │  ← Classical NLG generation engine
    └──────────┘
         │
         ▼
   Generated stories
```

## Key Components

### `kernel.py` — Kernel Extraction
Uses LLMs (via OpenAI-compatible API) to extract story kernels from raw text. Processes the TinyStories dataset with async concurrency.

### `gen5.py` — Classical Generation Engine ⭐

The main generation engine that converts kernels to stories **without LLMs at runtime**. Uses:
- Python AST parsing (kernels are valid Python)
- Template-based sentence generation
- Compositional execution of kernel functions

**Key design:** Kernels ARE valid Python code. They're parsed with `ast.parse()` and executed against a registry of kernel implementations.

## Generation Engine Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         KERNEL STRING                                │
│  "Lily(Character, girl, Curious)                                    │
│   Journey(Lily, catalyst=Discovery(rainbow), transformation=Happy)" │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        ast.parse()                                   │
│                    Python AST Tree                                   │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      KernelExecutor                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ _eval_node(node)                                             │   │
│  │   ├── ast.Call → lookup REGISTRY, execute kernel function   │   │
│  │   ├── ast.BinOp(+) → _compose() fragments                   │   │
│  │   ├── ast.BinOp(/) → attention dilution                     │   │
│  │   └── ast.Name → resolve character or concept               │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
          ┌─────────────┐ ┌───────────┐ ┌─────────────┐
          │  REGISTRY   │ │StoryContext│ │TemplateEngine│
          │ 800+ kernels│ │ characters │ │ templates   │
          │ @kernel()   │ │ emotions   │ │ categories  │
          │ decorators  │ │ focus      │ │ slot-fill   │
          └─────────────┘ └───────────┘ └─────────────┘
                    │            │            │
                    └────────────┼────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      StoryFragment                                   │
│  { text: "Lily discovered a rainbow!", weight: 1.0, kernel: "..." } │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    StoryContext.render()                             │
│  - Filter by weight threshold                                        │
│  - Join fragments with spacing                                       │
│  - Clean up punctuation                                              │
│  - Capitalize sentences                                              │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        GENERATED STORY                               │
│  "Once upon a time, there was a curious girl named Lily.            │
│   But then, Lily discovered a rainbow! Lily learned something       │
│   important. After that, Lily felt happy."                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Data Structures

| Class | Purpose | Key Fields |
|-------|---------|------------|
| `Character` | Story character with emotional state | `name`, `char_type`, `traits`, `Joy`, `Fear`, `Love`, `Anger`, `Sadness`, `pronouns` |
| `StoryFragment` | Generated text piece with metadata | `text`, `weight`, `kernel_name` |
| `StoryContext` | Execution state for generation | `characters`, `fragments`, `current_focus`, `current_object` |
| `KernelRegistry` | Maps kernel names → functions | `kernels`, `metadata`, `templates` |
| `TemplateEngine` | Category-based template selection | `templates` dict, `generate()` method |
| `KernelExecutor` | AST interpreter for kernels | `execute()`, `_eval_node()`, `_compose()` |

### Kernel Function Pattern

```python
@REGISTRY.kernel("KernelName")
def kernel_name(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Kernel that does something."""
    # 1. Parse arguments
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    # 2. Update character emotional state
    if chars:
        chars[0].Joy += 10
    
    # 3. Generate text with character context
    if chars:
        return StoryFragment(f"{chars[0].name} did something.")
    
    # 4. Or return as concept (for composition in parent kernels)
    return StoryFragment("something", kernel_name="KernelName")
```

### Helper Functions

| Function | Purpose |
|----------|---------|
| `_to_phrase(value)` | Convert any value to natural language phrase |
| `_state_to_phrase(value)` | Convert state/emotion to descriptive phrase |
| `_action_to_phrase(value)` | Convert action to past-tense verb phrase |
| `_event_to_phrase(value)` | Convert event to "One day, X happened" format |
| `_get_default_actor(ctx, chars)` | Get protagonist when no character specified |
| `NLGUtils.past_tense(verb)` | Conjugate verb to past tense |
| `NLGUtils.article(word)` | Get "a" or "an" for word |
| `NLGUtils.join_list(items)` | Join with Oxford comma |

```python
# Example kernel execution
kernel = '''
Lily(Character, girl, Resourceful)
Encounter(Lily, wolf, forest)
Fear(Lily)
Run(Lily)
Whistle(Lily, loud)
Run(wolf)
'''

story = generate_story(kernel)
# Output: "There once was a resourceful girl named Lily. Lily came across 
#          a wolf. Lily was scared. Lily ran as fast as she could. 
#          Lily whistled very loud. The wolf ran away."
```


### `sample.py` `parse.py` `coverage.py` — Kernel Analysis
Parses extracted kernels, computes statistics, and identifies the most common narrative patterns.

### `story.py` — Narrative Algebra Framework
Experimental implementation of the kernel algebra with `Story` and `physical` classes.

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
python gen5.py
```

### Generate from Custom Kernel
```python
from gen5 import generate_story

kernel = '''
Tim(Character, boy, Brave)
Monster(Character, scary)
Encounter(Tim, Monster)
Fear(Tim)
Brave(Tim)
Run(Monster)
Joy(Tim)
'''

print(generate_story(kernel))
```

## Philosophy

The project is grounded in the idea that narratives are composed of reusable **memetic objects** — patterns that propagate through culture. By decomposing stories into kernels, we can:

1. **Compress** narrative knowledge into a small, interpretable library
2. **Compose** new stories by combining kernels algebraically
3. **Analyze** what fundamental patterns make stories work
4. **Train** models on structured narrative representations

**LLM usage is restricted to synthesis time** (extracting kernels, clustering, defining new kernel implementations). At generation time, stories are produced through classical execution — no LLM calls, just template filling and compositional algebra.

This is an exploration of story as code — where narrative structure becomes executable algebra.

## File Overview

| File | Purpose | LLM Required |
|------|---------|--------------|
| `kernel.py` | Extract kernels from stories | ✅ Yes |
| `parse.py` | Analyze kernel statistics | ❌ No |
| `cluster.py` | Cluster similar stories | ❌ No |
| `sample.py` | Sample & explore kernel usage | ❌ No |
| `coverage.py` | Check kernel implementation coverage | ❌ No |
| `gen5.py` | Core generation engine (representative kernels) | ❌ No |
| `gen5k01.py` | Kernel Pack #01 (additional kernels) | ❌ No |
| `chark01.py` | Kernel Pack #01 (character kernels) | ❌ No |
| `story.py` | Kernel algebra experiments | ❌ No |
| `AGENTS.md` | Instructions for coding agents | ❌ No |
| `gen.py`, `gen2.py`, `gen3.py`, `gen4.py` | Earlier generation attempts | Varies |

## For Coding Agents

See **[AGENTS.md](AGENTS.md)** for detailed instructions on implementing new kernels.
