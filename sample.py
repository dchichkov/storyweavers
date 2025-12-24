#!/usr/bin/env python3
"""
sample.py - Sample and generate stories from kernels

Randomly samples stories from TinyStories_kernels and generates text using gen5.py.
Useful for testing kernel coverage and comparing generated vs original stories.

Usage:
    python sample.py                    # Sample 1 random story
    python sample.py -n 5               # Sample 5 random stories
    python sample.py -f data01          # Sample from specific file
    python sample.py --show-original    # Also show original story text
"""

import json
import random
import argparse
import ast
from pathlib import Path

# Import gen5 generation engine
from gen5 import generate_story, KernelExecutor, REGISTRY


def load_jsonl(file_path: str, limit: int = None) -> list:
    """Load records from a JSONL file."""
    records = []
    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def sample_stories(file_path: str, n: int = 1) -> list:
    """Sample n random stories from a JSONL file."""
    records = load_jsonl(file_path)
    if not records:
        print(f"No records found in {file_path}")
        return []
    
    n = min(n, len(records))
    return random.sample(records, n)


def check_kernel_syntax(kernel: str) -> tuple:
    """Check if kernel is valid Python AST. Returns (is_valid, error_msg)."""
    try:
        ast.parse(kernel)
        return True, None
    except SyntaxError as e:
        return False, str(e)


def extract_kernel_names(kernel: str) -> list:
    """Extract all kernel function names from a kernel string."""
    try:
        tree = ast.parse(kernel)
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id[0].isupper():  # Uppercase = kernel
                    names.add(node.func.id)
            elif isinstance(node, ast.Name) and node.id[0].isupper():
                names.add(node.id)
        return sorted(names)
    except:
        return []


def check_kernel_coverage(kernel: str) -> tuple:
    """Check how many kernels are implemented. Returns (implemented, missing)."""
    names = extract_kernel_names(kernel)
    implemented = [n for n in names if n in REGISTRY]
    missing = [n for n in names if n not in REGISTRY and n != 'Character']
    return implemented, missing


def display_sample(record: dict, show_original: bool = False, index: int = None):
    """Display a sampled story with its kernel and generated text."""
    kernel = record.get('kernel', '')
    original = record.get('story', '')
    summary = record.get('summary', '')
    
    header = f"SAMPLE {index}" if index else "SAMPLE"
    print(f"\n{'='*70}")
    print(header)
    print('='*70)
    
    # Show summary if available
    if summary:
        print(f"\n📋 SUMMARY: {summary[:200]}{'...' if len(summary) > 200 else ''}")
    
    # Show kernel
    print(f"\n📝 KERNEL:")
    print("-" * 40)
    print(kernel.strip() if kernel else "[No kernel]")
    
    # Check syntax
    is_valid, error = check_kernel_syntax(kernel)
    if not is_valid:
        print(f"\n⚠️  SYNTAX ERROR: {error}")
    
    # Check coverage
    implemented, missing = check_kernel_coverage(kernel)
    if missing:
        print(f"\n⚠️  MISSING KERNELS: {', '.join(missing)}")
    
    # Generate story
    print(f"\n🤖 GENERATED:")
    print("-" * 40)
    if kernel:
        try:
            generated = generate_story(kernel)
            print(generated if generated.strip() else "[Empty output]")
        except Exception as e:
            print(f"[Generation error: {e}]")
    else:
        print("[No kernel to generate from]")
    
    # Show original if requested
    if show_original and original:
        print(f"\n📖 ORIGINAL:")
        print("-" * 40)
        print(original[:500] + ('...' if len(original) > 500 else ''))
    
    # Stats
    print(f"\n📊 STATS:")
    print(f"   Kernels used: {len(implemented)} implemented, {len(missing)} missing")
    if implemented:
        print(f"   Implemented: {', '.join(implemented[:10])}{'...' if len(implemented) > 10 else ''}")


def main():
    parser = argparse.ArgumentParser(
        description='Sample and generate stories from TinyStories kernels'
    )
    parser.add_argument('-n', '--num', type=int, default=1,
                        help='Number of stories to sample (default: 1)')
    parser.add_argument('-f', '--file', type=str, default='data00',
                        help='Data file to sample from (default: data00)')
    parser.add_argument('--show-original', '-o', action='store_true',
                        help='Also display original story text')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducibility')
    parser.add_argument('--stats', action='store_true',
                        help='Show coverage statistics for sampled kernels')
    
    args = parser.parse_args()
    
    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
    
    # Build file path
    file_path = Path('TinyStories_kernels') / f'{args.file}.kernels.jsonl'
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        print("Available files:")
        for f in Path('TinyStories_kernels').glob('*.kernels.jsonl'):
            print(f"  - {f.stem.replace('.kernels', '')}")
        return 1
    
    print(f"Sampling {args.num} {'story' if args.num == 1 else 'stories'} from {file_path}")
    
    # Sample stories
    samples = sample_stories(str(file_path), args.num)
    
    if not samples:
        return 1
    
    # Display each sample
    all_implemented = set()
    all_missing = set()
    
    for i, record in enumerate(samples, 1):
        display_sample(record, show_original=args.show_original, index=i)
        
        # Collect stats
        impl, miss = check_kernel_coverage(record.get('kernel', ''))
        all_implemented.update(impl)
        all_missing.update(miss)
    
    # Show aggregate stats
    if args.stats and len(samples) > 1:
        print(f"\n{'='*70}")
        print("AGGREGATE STATISTICS")
        print('='*70)
        print(f"Total unique kernels seen: {len(all_implemented) + len(all_missing)}")
        print(f"Implemented: {len(all_implemented)}")
        print(f"Missing: {len(all_missing)}")
        if all_missing:
            print(f"\nMissing kernels to implement:")
            for k in sorted(all_missing):
                print(f"  - {k}")
    
    return 0


if __name__ == '__main__':
    exit(main())

