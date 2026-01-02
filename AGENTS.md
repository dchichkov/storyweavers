# Agent Instructions: Implementing Story Kernels

This document provides instructions for coding agents (Claude, Cursor, etc.) working on the Storyweavers kernel implementation.

## Overview

Storyweavers uses **story kernels** - symbolic representations of narrative patterns that can be executed to generate natural language stories. The generation happens **without LLMs at runtime** - kernels are Python-like expressions parsed with `ast` and executed against a registry of kernel implementations.

## Before You Start

**First, inspect the existing codebase:**

1. **Read `gen5.py`** - The core generation engine with ~50 representative kernel implementations
2. **Read `gen5k01.py`** - Additional kernel pack with ~50 more kernels
3. **Understand the pattern** - Each kernel is a decorated function that takes `StoryContext` and returns `StoryFragment`


## Workflow: Sample → Study → Implement → Test

### Step 1: Identify Missing Kernels

```bash
# List common missing kernels (excludes character names by default)
python sample.py -l

# Include character names in the list
python sample.py -l --include-characters

# Explore a random missing kernel
python sample.py -e

# Look for a specific kernel
python sample.py -k KernelName
```

**Note:** Character names (like Tim, Lily, Mom) are automatically detected using AST parsing of `Name(Character, ...)` patterns and excluded from the missing kernels list by default. Use `--include-characters` flag to see them.

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

**Create new kernels in a nex files** (e.g., `gen5kXX.py`) to keep `gen5.py` as a representative core sample:

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
# Test the kernel pack directly, for example for gen5k02.py
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
   Implemented kernels: 584
   Unique kernel names in dataset: 16,213
   Characters detected (excluded): 4,310

📈 COVERAGE:
   Kernel usages covered: 598,084 / 791,805 (75.5%)
   Stories with 60%+ coverage: 63,299
```

## Current Coverage

- **584 kernels** implemented
- **75.5% coverage** of kernel usages in dataset (excluding character names)
- **~63,300 stories** have 60%+ kernel coverage
- **4,310 character names** automatically detected and excluded from coverage calculations

### Top Missing Kernels to Implement

| Kernel | Usages | Notes |
|--------|--------|-------|
| Anger | 978 | Feeling or expressing anger |
| Seek | 956 | Looking for something |
| Buy | 909 | Purchasing items |
| Release | 897 | Letting go or freeing |
| Continue | 896 | Continuing an action |
| Healing | 888 | Recovery process |
| Explanation | 848 | Explaining something |
| Drink | 836 | Drinking beverages |
| Look | 821 | Looking at something |
| Wash | 820 | Washing/cleaning |

**Note:** Coverage detection now automatically identifies character names (e.g., `Lily(Character, ...)`) and excludes them from kernel counts, showing only genuine narrative patterns that need implementation.


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
- **Test with real data** - Use sample.py to verify
- **No LLMs at runtime** - All generation is classical execution

