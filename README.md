# Storyweavers

**Narrative Algebra: Extracting and Composing Story Kernels**

Storyweavers explores whether stories can be decomposed into compact, algebraic "kernels" — composable narrative patterns that can generate surface text. The project extracts these kernels from the TinyStories dataset (~2M children's stories) and investigates whether a small library of ~1-5K kernels can reconstruct coherent story datasets.

## Core Concept: Story Kernels

A **story kernel** is a symbolic, algebraic representation of a narrative's structure. It captures characters, their traits, narrative arcs, and emotional transformations in a composable format.

### Example

**Original Story:**
> Once upon a time, there was a big whale. The whale loved to swim in the deep blue sea. The whale was very delicate and kind to all the little fish. One day, the whale wanted to test how fast he could swim...

**Extracted Kernel:**
```
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
    │ story.py │  ← Kernel algebra & generation
    │  gen.py  │
    └──────────┘
         │
         ▼
   Generated stories
```

## Key Components

### `kernel.py` — Kernel Extraction
Uses LLMs (via OpenAI-compatible API) to extract story kernels from raw text. Processes the TinyStories dataset with async concurrency.

### `story.py` — Narrative Algebra Framework
Implements the core `Story` and `physical` classes:
- **`Story`**: Memetic objects with attention algebra (`/`, `+`, `+=`)
- **`physical`**: Atomic, terminal objects (no internal structure)
- **`@Stories`**: Decorator that registers reusable kernel functions
- **`@Characters`**: Creates characters bridging physical and story layers

### `cluster.py` — GPU-Accelerated Clustering
Uses RAPIDS (cuGraph, cuML) for:
- Weisfeiler-Lehman graph hashing of kernel ASTs
- UMAP dimensionality reduction
- DBSCAN/K-Means clustering to find story archetypes

### `parse.py` — Kernel Analysis
Parses extracted kernels, computes statistics, and identifies the most common narrative patterns.

### `gen.py` / `gen2.py` — Kernel → Text Generation
Converts kernel representations back into natural language stories.

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

### Extract Kernels
```bash
# Set up LLM endpoint
export LOCALHOST_BASE_URL="http://localhost:8001/v1"
export LOCALHOST_API_KEY="your-key"

# Run extraction
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

### Generate Stories from Kernels
```bash
python gen.py
# or
python gen2.py
```

## Philosophy

The project is grounded in the idea that narratives are composed of reusable **memetic objects** — patterns that propagate through culture. By decomposing stories into kernels, we can:

1. **Compress** narrative knowledge into a small, interpretable library
2. **Compose** new stories by combining kernels algebraically
3. **Analyze** what fundamental patterns make stories work
4. **Train** models on structured narrative representations

This is an exploration of story as code — where narrative structure becomes executable algebra.
