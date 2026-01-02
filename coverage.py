#!/usr/bin/env python3
"""
coverage.py - Check kernel implementation coverage against the dataset.

Usage:
    python coverage.py              # Full coverage report
    python coverage.py --brief      # Just show totals
    python coverage.py --missing    # Show top missing kernels
    python coverage.py --implemented # Show top implemented kernels
"""

import json
import ast
import re
import argparse
import warnings
from collections import Counter
from pathlib import Path

# Suppress syntax warnings from ast.parse on malformed kernels
warnings.filterwarnings('ignore', category=SyntaxWarning)


def load_registry():
    """Load the kernel registry with all kernel packs."""
    from gen5registry import REGISTRY
    return REGISTRY


def extract_character_names(kernel: str) -> set:
    """Extract character names from kernel by looking for Name(Character, ...) pattern."""
    if not kernel:
        return set()
    # Look for patterns like: Lily(Character, ...) or Mom(Character, ...)
    return set(re.findall(r'\b([A-Z][a-zA-Z]+)\s*\(\s*Character\b', kernel))


def count_coverage(kernel: str, implemented: set, characters: set = None) -> tuple[int, int]:
    """Count how many kernels in a kernel string are implemented."""
    if not kernel:
        return 0, 0
    names = set(re.findall(r'\b([A-Z][a-zA-Z]+)\s*\(', kernel))
    # Exclude character names from counting
    if characters:
        names = names - characters
    covered = len(names & implemented)
    return covered, len(names)


def main():
    parser = argparse.ArgumentParser(description='Check kernel coverage')
    parser.add_argument('--brief', '-b', action='store_true', help='Brief output')
    parser.add_argument('--missing', '-m', action='store_true', help='Show missing kernels')
    parser.add_argument('--implemented', '-i', action='store_true', help='Show implemented kernels')
    parser.add_argument('--top', '-n', type=int, default=30, help='Number of top items to show')
    parser.add_argument('--data', '-d', default='TinyStories_kernels/data00.kernels.jsonl',
                        help='Path to kernels file')
    args = parser.parse_args()
    
    # Load registry
    registry = load_registry()
    implemented = set(registry.kernels.keys())
    
    # Load stories
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Error: {data_path} not found")
        return 1
    
    with open(data_path, 'r') as f:
        stories = [json.loads(line) for line in f]
    
    # Count parseable kernels
    parseable = 0
    for s in stories:
        kernel = s.get('kernel', '')
        if kernel:
            try:
                ast.parse(kernel)
                parseable += 1
            except:
                pass
    
    # Extract all kernel names used in the dataset
    all_kernels = Counter()
    all_characters = set()
    
    for story in stories:
        kernel = story.get('kernel', '')
        if kernel:
            # Extract character names
            all_characters.update(extract_character_names(kernel))
            # Extract all kernel names
            names = re.findall(r'\b([A-Z][a-zA-Z]+)\s*\(', kernel)
            all_kernels.update(names)
    
    # Remove character names from kernel counts
    for char_name in all_characters:
        if char_name in all_kernels:
            del all_kernels[char_name]
    
    # Calculate coverage
    covered_usages = sum(count for name, count in all_kernels.items() if name in implemented)
    total_usages = sum(all_kernels.values())
    
    # Find high-coverage stories
    high_coverage_count = 0
    for s in stories:
        kernel = s.get('kernel', '')
        try:
            ast.parse(kernel)
            characters = extract_character_names(kernel)
            covered, total = count_coverage(kernel, implemented, characters)
            if total >= 5 and covered / total >= 0.6:
                high_coverage_count += 1
        except:
            pass
    
    # Output
    if args.brief:
        print(f"Kernels: {len(implemented)} | Coverage: {100*covered_usages/total_usages:.1f}% | High-coverage stories: {high_coverage_count} | Characters detected: {len(all_characters)}")
        return 0
    
    print("=" * 70)
    print("KERNEL COVERAGE REPORT")
    print("=" * 70)
    print()
    print(f"📊 DATASET: {data_path}")
    print(f"   Total stories: {len(stories):,}")
    print(f"   Parseable kernels: {parseable:,} ({100*parseable/len(stories):.1f}%)")
    print()
    print(f"🔧 IMPLEMENTATION:")
    print(f"   Implemented kernels: {len(implemented)}")
    print(f"   Unique kernel names in dataset: {len(all_kernels):,}")
    print(f"   Characters detected (excluded): {len(all_characters)}")
    print()
    print(f"📈 COVERAGE:")
    print(f"   Kernel usages covered: {covered_usages:,} / {total_usages:,} ({100*covered_usages/total_usages:.1f}%)")
    print(f"   Stories with 60%+ coverage: {high_coverage_count:,}")
    print()
    
    if args.implemented or not args.missing:
        print("=" * 70)
        print(f"✅ TOP {args.top} IMPLEMENTED KERNELS (by usage)")
        print("=" * 70)
        count = 0
        for name, usage in all_kernels.most_common(100):
            if name in implemented and count < args.top:
                print(f"   {name:25s} {usage:,}")
                count += 1
        print()
    
    if args.missing or not args.implemented:
        print("=" * 70)
        print(f"❌ TOP {args.top} MISSING KERNELS (by usage)")
        print("=" * 70)
        count = 0
        for name, usage in all_kernels.most_common(200):
            if name not in implemented and count < args.top:
                print(f"   {name:25s} {usage:,}")
                count += 1
        print()
    
    print("=" * 70)
    print("To implement missing kernels, run:")
    print("   python sample.py -k KernelName -n 3")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit(main())

