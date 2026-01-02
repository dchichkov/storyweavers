#!/usr/bin/env python3
"""
Check for duplicate kernel registrations across all kernel packs.

Usage:
    python check_duplicates.py              # Show duplicate warnings only
    python check_duplicates.py --source     # Show source code of duplicates
    python check_duplicates.py -s           # Short form
"""

import sys
import argparse

parser = argparse.ArgumentParser(description='Check for duplicate kernel registrations')
parser.add_argument('--source', '-s', action='store_true',
                    help='Show source code of duplicate kernels')
args = parser.parse_args()

print("Checking for duplicate kernels...")
print("=" * 70)

if args.source:
    print("(Showing source code of duplicates)\n")

# Set the flag before importing
from gen5 import REGISTRY
if args.source:
    REGISTRY.show_duplicate_source = True

# Import gen5registry which loads all kernel packs
# This will trigger duplicate warnings
from gen5registry import REGISTRY as LOADED_REGISTRY

print("=" * 70)
print(f"Total kernels registered: {len(LOADED_REGISTRY.kernels)}")
print("\nTo fix duplicates:")
print("  1. Compare implementations using --source flag")
print("  2. Keep the better implementation")
print("  3. Remove redundant kernel definitions from other files")
