#!/usr/bin/env python3
"""
Check for duplicate kernel variants across all gen6 kernel packs.

gen6 intentionally registers *multiple typed variants* per kernel name (typed
dispatch picks the matching one). A genuine duplicate is therefore two variants
for the same name with the *same parameter-type signature* - the binder can
never tell them apart, so one shadows the other.

Usage:
    python check_duplicates.py              # List duplicate variants
    python check_duplicates.py --source     # Also show source location/code
    python check_duplicates.py -s           # Short form
"""

import argparse
import inspect

parser = argparse.ArgumentParser(description='Check for duplicate kernel variants (gen6)')
parser.add_argument('--source', '-s', action='store_true',
                    help='Show source location/code of duplicate variants')
args = parser.parse_args()

print("Checking for duplicate kernel variants (gen6)...")
print("=" * 70)

# gen6registry loads gen6 + all gen6kXX / char6kXX packs.
from gen6registry import REGISTRY


def _sig_key(variant) -> tuple:
    """A dispatch key: the ordered parameter-type names (excluding the World ctx)."""
    key = []
    params = list(variant.signature.parameters.values())
    for p in params[1:]:  # skip the leading World/ctx parameter
        ann = variant.hints.get(p.name, p.annotation)
        name = getattr(ann, "__name__", str(ann))
        key.append((p.kind.name, name))
    return tuple(key)


dup_count = 0
for name, variants in sorted(REGISTRY.kernels.items()):
    seen: dict = {}
    for v in variants:
        seen.setdefault(_sig_key(v), []).append(v)
    for key, group in seen.items():
        if len(group) > 1:
            dup_count += 1
            print(f"\nDUPLICATE: {name}  signature={key}")
            for v in group:
                try:
                    src_file = inspect.getsourcefile(v.fn)
                    _, line = inspect.getsourcelines(v.fn)
                    print(f"  - {src_file}:{line}")
                    if args.source:
                        print("    " + "    ".join(inspect.getsource(v.fn).splitlines(True)))
                except (OSError, TypeError):
                    print(f"  - {v.fn!r}")

print("\n" + "=" * 70)
total_variants = sum(len(v) for v in REGISTRY.kernels.values())
print(f"Kernel names: {len(REGISTRY.kernels)}   Total variants: {total_variants}")
if dup_count:
    print(f"\n{dup_count} duplicate variant group(s) found.")
    print("To fix: keep the better implementation and remove the redundant variant,")
    print("or differentiate them by parameter type so dispatch can choose.")
else:
    print("\nNo duplicate variants found. Clean!")
