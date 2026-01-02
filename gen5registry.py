"""
gen5registry.py - Central registry that loads all kernel packs.

This module auto-discovers and imports all gen5kXX.py kernel packs,
registering their kernels into the shared REGISTRY.

Usage:
    from gen5registry import REGISTRY, generate_story
    
    # All kernels from gen5, gen5k01, gen5k02, ... gen5k99 are now available
    story = generate_story(kernel_string)
"""

import importlib
import sys
from pathlib import Path

# Import the base gen5 module
from gen5 import (
    REGISTRY,
    KernelExecutor,
    StoryContext,
    StoryFragment,
    Character,
    NLGUtils,
    _to_phrase,
    _state_to_phrase,
    _event_to_phrase,
    _action_to_phrase,
)

# Auto-discover and load all gen5kXX kernel packs
_loaded_packs = []

def _load_kernel_packs():
    """Discover and import all gen5kXX.py kernel pack modules."""
    global _loaded_packs
    
    # Get the directory containing this file
    base_dir = Path(__file__).parent
    
    # Find all gen5kXX.py files (gen5k01.py through gen5k99.py)
    for i in range(1, 100):
        module_name = f"gen5k{i:02d}"
        module_path = base_dir / f"{module_name}.py"
        
        if module_path.exists():
            try:
                # Import the module (this registers its kernels via decorators)
                importlib.import_module(module_name)
                _loaded_packs.append(module_name)
            except Exception as e:
                print(f"Warning: Failed to load {module_name}: {e}")

# Load all packs on import
_load_kernel_packs()

def generate_story(kernel: str) -> str:
    """Generate a story from a kernel string using the full registry."""
    executor = KernelExecutor(REGISTRY)
    return executor.execute(kernel)

def get_kernel_count() -> int:
    """Return the total number of registered kernels."""
    return len(REGISTRY.kernels)

def list_loaded_packs() -> list:
    """Return list of loaded kernel pack module names."""
    return ['gen5'] + _loaded_packs

def list_kernels() -> list:
    """Return sorted list of all registered kernel names."""
    return sorted(REGISTRY.kernels.keys())


if __name__ == "__main__":
    print("=" * 70)
    print("GEN5 REGISTRY - Kernel Pack Loader")
    print("=" * 70)
    print(f"\nLoaded packs: {', '.join(list_loaded_packs())}")
    print(f"Total kernels: {get_kernel_count()}")
    print("\nAll kernels:")
    for i, name in enumerate(list_kernels(), 1):
        print(f"  {i:3d}. {name}")


