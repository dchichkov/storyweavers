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
│parse.py │ │cluster.py │  ← Analysis & GPU clustering
└─────────┘ └───────────┘
                │
                ▼
    Story pattern clusters
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
- NLTK for linguistic processing (when available)
- Compositional execution of kernel functions

**Key design:** Kernels ARE valid Python code. They're parsed with `ast.parse()` and executed against a registry of kernel implementations.

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

### `cluster.py` — GPU-Accelerated Clustering
Uses RAPIDS (cuGraph, cuML) for:
- Weisfeiler-Lehman graph hashing of kernel ASTs
- UMAP dimensionality reduction
- DBSCAN/K-Means clustering to find story archetypes

### `parse.py` — Kernel Analysis
Parses extracted kernels, computes statistics, and identifies the most common narrative patterns.

### `story.py` — Narrative Algebra Framework
Experimental implementation of the kernel algebra with `Story` and `physical` classes.

## Adding New Kernels (Coding Agent Workflow)

The recommended approach for expanding kernel coverage is **interactive development with a coding agent** (like Claude, Cursor, etc.) rather than automated LLM synthesis.

### Why Coding Agent > Automated Synthesis

1. **Context-aware**: The agent sees the full codebase and existing patterns
2. **Iterative refinement**: Can test, debug, and improve implementations in real-time
3. **Consistent style**: Follows established conventions in the codebase
4. **Better error handling**: Can handle edge cases discovered during testing
5. **Documentation**: Naturally documents decisions and patterns

### Workflow: Sample → Study → Implement → Test

**Critical:** Always sample real usage examples before implementing a kernel!

#### Step 1: Identify Missing Kernels
```bash
python sample.py -l              # List common missing kernels
python sample.py -e              # Explore a random missing kernel  
python sample.py -k KernelName   # Explore a specific kernel
```

#### Step 2: Sample Usage Examples
```bash
# See how a kernel is actually used in the dataset
python sample.py -k Apology -n 5

# Example output shows:
#   - Original story summary
#   - Full kernel structure
#   - How the target kernel fits in context
#   - What other kernels it's commonly paired with
```

#### Step 3: Study the Patterns
Look for:
- **Arguments**: What characters/objects are typically passed?
- **Context**: What kernels come before/after?
- **Variations**: Different ways the same kernel is used
- **Character state**: What emotions are affected?

#### Step 4: Implement the Kernel
Create new kernels in **separate files** (e.g., `gen5k01.py`, `gen5k02.py`) to keep `gen5.py` as a representative core sample:

```python
# gen5k01.py - Additional Kernel Pack #01
from gen5 import REGISTRY, StoryContext, StoryFragment, Character

@REGISTRY.kernel("Apology")
def kernel_apology(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    ...
```

#### Step 5: Test with Real Data
```bash
# Test by sampling the same kernel again - it should now generate
python sample.py -k Apology -n 3

# Import the kernel pack in your code:
from gen5 import generate_story
import gen5k01  # Registers additional kernels
```

### Example Session

```bash
$ python sample.py -k Quest -n 2

KERNEL:
Hero(Character, Curious + Determined)
Quest(Hero,
    longing=Find(Special),
    process=Search + Heed(Voice) + Enter(mine),
    obstacle=Fear + mine(twisting),
    outcome=Safety + Joy)

# Now you understand: Quest takes goal, process, obstacle, outcome kwargs
# and typically involves Fear → Joy emotional arc
```

### How to Add a Kernel (After Sampling!)

1. **Sample the kernel** to understand its usage patterns
2. **Ask the coding agent** to implement the kernel:
> "Add a kernel for `Rescue` that handles characters rescuing each other"

3. **The agent adds it to a kernel pack file** following the pattern:
```python
@REGISTRY.kernel("Rescue")
def kernel_rescue(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Someone is rescued."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        chars[1].Fear -= 15
        chars[1].Joy += 10
        return StoryFragment(f"{chars[0].name} rescued {chars[1].name}!")
    elif chars:
        return StoryFragment(f"{chars[0].name} was rescued!")
    
    return StoryFragment("Someone came to the rescue!")
```

4. **Test immediately**:
```bash
python gen5.py
```

### Kernel Implementation Pattern

Every kernel follows this structure:

```python
@REGISTRY.kernel("KernelName")
def kernel_name(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Docstring describing what this kernel does."""
    
    # 1. Parse arguments
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    # 2. Update character state (optional)
    if chars:
        chars[0].Joy += 10  # or Fear, Love, Sadness, etc.
    
    # 3. Generate text based on arguments
    if len(chars) >= 2:
        return StoryFragment(f"{chars[0].name} verbed {chars[1].name}.")
    elif chars:
        return StoryFragment(f"{chars[0].name} verbed.")
    
    # 4. Handle concept/state usage (when no character present)
    return StoryFragment("verbed", kernel_name="KernelName")
```

### Meta-Pattern Kernels

For narrative structures like `Journey`, `Cautionary`, `Friendship`:

```python
@REGISTRY.kernel("Journey")
def kernel_journey(ctx: StoryContext, character: Character = None, **kwargs):
    parts = []
    
    if 'state' in kwargs:
        parts.append(f"{character.name} was {_state_to_phrase(kwargs['state'])}.")
    
    if 'catalyst' in kwargs:
        parts.append(f"But then, {_event_to_phrase(kwargs['catalyst'])}!")
    
    if 'process' in kwargs:
        parts.append(f"{character.name} {_action_to_phrase(kwargs['process'])}.")
    
    if 'transformation' in kwargs:
        parts.append(f"After that, {character.name} felt {kwargs['transformation']}.")
    
    return StoryFragment(' '.join(parts))
```

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
| `story.py` | Kernel algebra experiments | ❌ No |
| `AGENTS.md` | Instructions for coding agents | ❌ No |
| `gen.py`, `gen2.py`, `gen3.py`, `gen4.py` | Earlier generation attempts | Varies |

## For Coding Agents

See **[AGENTS.md](AGENTS.md)** for detailed instructions on implementing new kernels.
