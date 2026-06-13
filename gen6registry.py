"""
gen6registry.py - Central registry that loads all gen6 kernel packs.

Mirrors gen5registry.py for the gen6 engine: it imports the base `gen6` module
and auto-discovers `gen6kXX.py` (and `char6kXX.py`) packs, registering their
kernels into the shared `REGISTRY` via their `@REGISTRY.kernel(...)` decorators.

Usage:
    from gen6registry import REGISTRY, generate_story
    story = generate_story(kernel_string)
"""

import importlib
from pathlib import Path

from gen6 import (  # noqa: F401  (re-exported for tooling)
    REGISTRY,
    Executor,
    World,
    Entity,
    Trace,
    Character,
    Physical,
    Actor,
    NLGUtils,
    to_phrase,
    state_to_phrase,
    action_to_phrase,
    event_to_phrase,
    rewrite_tree,
    tag_coherence,
    narrate,
    generate,
    generate_world,
    DEFAULT_RULES,
)

_loaded_packs = []


def _load_kernel_packs():
    """Discover and import all gen6kXX.py and char6kXX.py kernel pack modules."""
    global _loaded_packs
    base_dir = Path(__file__).parent

    for prefix in ("gen6k", "char6k"):
        for i in range(1, 100):
            module_name = f"{prefix}{i:02d}"
            if (base_dir / f"{module_name}.py").exists():
                try:
                    importlib.import_module(module_name)
                    _loaded_packs.append(module_name)
                except Exception as e:  # pragma: no cover - diagnostic only
                    print(f"Warning: Failed to load {module_name}: {e}")


_load_kernel_packs()


def generate_story(kernel: str, rules=None, coherence: bool = True) -> str:
    """Generate a story from a kernel string using the full registry."""
    return generate(kernel, rules=rules, coherence=coherence)


def get_kernel_count() -> int:
    """Number of registered kernel names (each may have multiple typed variants)."""
    return len(REGISTRY.kernels)


def get_variant_count() -> int:
    """Total number of registered kernel variants across all names."""
    return sum(len(v) for v in REGISTRY.kernels.values())


def list_loaded_packs() -> list:
    return ["gen6"] + _loaded_packs


def list_kernels() -> list:
    return sorted(REGISTRY.kernels.keys())


if __name__ == "__main__":
    print("=" * 70)
    print("GEN6 REGISTRY - Kernel Pack Loader")
    print("=" * 70)
    print(f"\nLoaded packs:   {', '.join(list_loaded_packs())}")
    print(f"Kernel names:   {get_kernel_count()}")
    print(f"Total variants: {get_variant_count()}")
    print("\nAll kernels:")
    for i, name in enumerate(list_kernels(), 1):
        print(f"  {i:3d}. {name}")
