# Agent Instructions: Implementing Story Kernels

This document provides instructions for coding agents (Claude, Cursor, etc.) working on the Storyweavers kernel implementation.

## Overview

Storyweavers uses **story kernels** - symbolic representations of narrative patterns that can be executed to generate natural language stories. The generation happens **without LLMs at runtime** - kernels are Python-like expressions parsed with `ast` and executed against a registry of kernel implementations.

## Before You Start

**First, inspect the existing codebase:**

1. **Read `gen5.py`** - The core generation engine with ~50 representative kernel implementations
2. **Read `gen5k01.py`** - Additional kernel pack with ~50 more kernels
3. **Understand the pattern** - Each kernel is a decorated function that takes `StoryContext` and returns `StoryFragment`

**IMPORTANT: Use `gen5registry` when checking coverage or sampling, not `gen5` directly!**

```python
# CORRECT - loads ALL kernel packs (gen5k01, gen5k02, ... gen5k99)
from gen5registry import REGISTRY, generate_story

# WRONG - only loads sample gen5.py kernels!
from gen5 import REGISTRY, generate_story
```

The `gen5registry` module auto-discovers and imports all `gen5kXX.py` files, ensuring you see all implemented kernels. Always use `sample.py` and `coverage.py` for checking coverage - they use `gen5registry` correctly.

```python
# Example kernel structure from gen5.py
@REGISTRY.kernel("KernelName")
def kernel_name(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Docstring describing what this kernel does."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 10  # Update character state
        return StoryFragment(f"{chars[0].name} did something.")
    
    return StoryFragment("something happened", kernel_name="KernelName")
```

## Workflow: Sample → Study → Implement → Test

### Step 1: Identify Missing Kernels

```bash
# List common missing kernels
python sample.py -l

# Explore a random missing kernel
python sample.py -e

# Look for a specific kernel
python sample.py -k KernelName
```

### Step 2: Sample Real Usage Examples

**Critical: Always sample before implementing!**

```bash
# See how a kernel is actually used in the dataset
python sample.py -k Apology -n 5 --seed 42
```

The output shows:
- Original story summary
- Full kernel structure
- How the target kernel fits in context
- What other kernels it's commonly paired with
- Implementation suggestion template

### Step 3: Study the Patterns

Look for:
- **Arguments**: What characters/objects are typically passed?
- **Context**: What kernels come before/after?
- **Variations**: Different ways the same kernel is used
- **Character state**: What emotions should be affected?

Example patterns from sampling:
```
Apology(Tim)                    -- single char apologizing
Apology(Tim, to=Ann)            -- char apologizing to specific person
Apology(Anna, Ben, Lily)        -- multiple chars apologizing to last one

Quest(Hero, goal=..., obstacle=..., process=..., outcome=...)
Quest(Max, Lucy, clue=..., setting=..., outcome=...)

Loss(Apple)                     -- losing an object
Loss(Mommy, Sick)               -- temporary loss of companion
```

### Step 4: Implement the Kernel

**Create new kernels in separate files** (e.g., `gen5k02.py`) to keep `gen5.py` as a representative core sample:

```python
# gen5k02.py - Additional Kernel Pack #02
"""
Document the kernels and their usage patterns at the top of the file.
"""

from gen5 import (
    REGISTRY, 
    StoryContext, 
    StoryFragment, 
    Character,
    NLGUtils,
    _to_phrase,
)

@REGISTRY.kernel("NewKernel")
def kernel_new(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Description of what this kernel does.
    
    Patterns from sampling:
      - NewKernel(char, thing)    -- pattern 1
      - NewKernel(char, to=other) -- pattern 2
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    # Implementation based on sampled patterns
    ...
```

### Step 5: Test with Real Data

```bash
# Test the kernel pack directly
python gen5k02.py

# Sample the same kernel again - should now generate properly
python sample.py -k NewKernel -n 3

# Check total kernel count (ALWAYS use gen5registry!)
python -c "from gen5registry import REGISTRY; print(len(REGISTRY.kernels))"
```

**Note:** Always use `sample.py` and `coverage.py` for checking coverage - don't write custom scripts that import `gen5` directly, as they won't see all kernel packs.

## Key Files

| File | Purpose | Modify? |
|------|---------|---------|
| `gen5.py` | Core engine + ~50 representative kernels | NO - keep as reference |
| `gen5k01.py` | Kernel pack #1 (~50 kernels) | Add to or create new pack |
| `sample.py` | Sampling tool for exploring kernels | NO |
| `coverage.py` | Check implementation coverage | NO |
| `README.md` | Project documentation | Update if needed |

## Implementation Guidelines

### Character State Updates
Kernels can modify character emotional state:
```python
char.Joy += 10      # Happiness
char.Sadness += 5   # Sadness  
char.Fear += 5      # Fear
char.Anger += 5     # Anger
char.Love += 5      # Affection
```

### Return Values
- With character context: `StoryFragment(f"{char.name} verbed.")`
- As concept/phrase: `StoryFragment("phrase", kernel_name="KernelName")`

### Helper Functions
Use these from gen5.py:
- `_to_phrase(arg)` - Convert argument to readable phrase
- `_state_to_phrase(state)` - Convert state to phrase
- `_action_to_phrase(action)` - Convert action to phrase
- `NLGUtils.join_list(names)` - Join list with "and"

## Checking Coverage

Use `coverage.py` to check how well the implemented kernels cover the dataset:

```bash
# Full coverage report
python coverage.py

# Brief one-liner
python coverage.py --brief

# Show top 30 missing kernels
python coverage.py --missing

# Show top 30 implemented kernels  
python coverage.py --implemented

# Show more items
python coverage.py --missing --top 50
```

Example output:
```
📊 DATASET: TinyStories_kernels/data00.kernels.jsonl
   Total stories: 100,000
   Parseable kernels: 80,766 (80.8%)

🔧 IMPLEMENTATION:
   Implemented kernels: 101
   Unique kernel names in dataset: 20,523

📈 COVERAGE:
   Kernel usages covered: 400,310 / 1,113,331 (36.0%)
   Stories with 60%+ coverage: 4,670
```

## Current Coverage

- **101 kernels** implemented
- **36% coverage** of kernel usages in dataset
- **~4,700 stories** have 60%+ kernel coverage

### Top Missing Kernels to Implement

| Kernel | Usages | Notes |
|--------|--------|-------|
| Gratitude | 6,024 | Expressing thanks |
| Request | 5,211 | Asking for something |
| Insight | 5,028 | Gaining understanding |
| Gift | 4,811 | Giving presents |
| Attempt | 4,670 | Trying to do something |
| Promise | 4,208 | Making commitments |
| Observe | 4,080 | Watching/noticing |
| Warning | 4,028 | Giving warnings |

Note: Many "missing" kernels like `Lily`, `Mom`, `Tim` are character names handled by the `Character` kernel.

## Example Session

```bash
# 1. Check what's missing
$ python sample.py -l | head -20

# 2. Sample a specific kernel
$ python sample.py -k Gratitude -n 3

# Output shows patterns like:
#   Gratitude(Lily)
#   Gratitude(Lily, to=Mom)
#   resolution=Apology(Tim)+Gratitude(Mom)

# 3. Implement based on patterns (add to gen5k01.py or new file)
@REGISTRY.kernel("Gratitude")
def kernel_gratitude(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    chars = [a for a in args if isinstance(a, Character)]
    to = kwargs.get('to', None)
    
    if chars:
        chars[0].Joy += 8
        chars[0].Love += 5
        if to:
            return StoryFragment(f"{chars[0].name} was very grateful to {to}.")
        return StoryFragment(f"{chars[0].name} felt very grateful.")
    
    return StoryFragment("there was gratitude", kernel_name="Gratitude")

# 4. Test
$ python gen5k01.py
$ python sample.py -k Gratitude -n 2
```

## Philosophy

- **Use gen5registry, not gen5** - Always import from `gen5registry` to see all kernels
- **Use sample.py and coverage.py** - Don't write custom scripts; the tools handle imports correctly
- **Sample before implementing** - Understand real usage patterns
- **Keep gen5.py clean** - It's the reference implementation
- **Use separate kernel packs** - Organize by theme or batch
- **Test with real data** - Use sample.py to verify
- **No LLMs at runtime** - All generation is classical execution

