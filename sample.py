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
    python sample.py -k Search          # Sample stories using the "Search" kernel
    python sample.py --explore-missing  # Pick a random missing kernel and sample its usages
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


def find_stories_with_kernel(file_path: str, kernel_name: str, limit: int = 100) -> list:
    """Find stories that use a specific kernel."""
    import re
    matches = []
    
    with open(file_path, 'r') as f:
        for line in f:
            try:
                record = json.loads(line)
                kernel = record.get('kernel', '') or ''
                if not kernel:
                    continue
                # Look for kernel name as function call or reference
                # Match: KernelName( or KernelName, or KernelName) or KernelName\n or +KernelName
                pattern = rf'\b{re.escape(kernel_name)}\b'
                if re.search(pattern, kernel):
                    matches.append(record)
                    if len(matches) >= limit:
                        break
            except json.JSONDecodeError:
                continue
    
    return matches


def collect_missing_kernels(file_path: str, sample_size: int = 500) -> dict:
    """Scan stories and collect missing kernel frequencies."""
    from collections import Counter
    
    missing_counts = Counter()
    records = load_jsonl(file_path, limit=sample_size)
    
    for record in records:
        kernel = record.get('kernel', '')
        _, missing = check_kernel_coverage(kernel)
        # Filter out likely character names (single capitalized words that appear as first arg)
        for m in missing:
            missing_counts[m] += 1
    
    return missing_counts


def is_likely_kernel_not_name(kernel_name: str, records: list) -> bool:
    """Heuristic: check if this is likely a kernel (action/pattern) vs a character name."""
    # Common kernel patterns (verbs, patterns)
    kernel_patterns = [
        'Search', 'Find', 'Play', 'Run', 'Walk', 'Jump', 'Fly', 'Swim',
        'Help', 'Share', 'Give', 'Take', 'Make', 'Build', 'Create',
        'Learn', 'Teach', 'Show', 'Tell', 'Ask', 'Answer',
        'Love', 'Like', 'Want', 'Need', 'Feel', 'Think',
        'Happy', 'Sad', 'Angry', 'Scared', 'Surprised',
        'Quest', 'Journey', 'Adventure', 'Mission',
        'Conflict', 'Fight', 'Battle', 'Challenge',
        'Loss', 'Win', 'Fail', 'Success',
        'Start', 'End', 'Begin', 'Finish',
        'Attempt', 'Try', 'Effort',
    ]
    
    # If it matches common patterns, likely a kernel
    for pattern in kernel_patterns:
        if pattern.lower() in kernel_name.lower():
            return True
    
    # Check usage patterns in records
    call_count = 0
    ref_count = 0
    for record in records[:20]:
        kernel = record.get('kernel', '')
        # Count as call if followed by (
        if f'{kernel_name}(' in kernel:
            call_count += 1
        # Count as reference if appears without (
        elif kernel_name in kernel:
            ref_count += 1
    
    # If mostly used as function calls, likely a kernel
    return call_count > ref_count


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
    parser.add_argument('-k', '--kernel', type=str, default=None,
                        help='Sample stories that use a specific kernel')
    parser.add_argument('--explore-missing', '-e', action='store_true',
                        help='Pick a random missing kernel and sample stories using it')
    parser.add_argument('--list-missing', '-l', action='store_true',
                        help='List most common missing kernels')
    
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
    
    # Mode: List missing kernels
    if args.list_missing:
        print(f"Scanning {file_path} for missing kernels...")
        missing_counts = collect_missing_kernels(str(file_path), sample_size=1000)
        
        print(f"\n{'='*70}")
        print("MOST COMMON MISSING KERNELS")
        print('='*70)
        print(f"{'Kernel':<30} {'Count':<10} {'Likely Type'}")
        print('-'*70)
        
        # Get sample records for heuristic
        sample_records = load_jsonl(str(file_path), limit=100)
        
        for kernel_name, count in missing_counts.most_common(30):
            likely_kernel = is_likely_kernel_not_name(kernel_name, sample_records)
            type_str = "🔧 kernel" if likely_kernel else "👤 name/trait"
            print(f"{kernel_name:<30} {count:<10} {type_str}")
        
        return 0
    
    # Mode: Explore a random missing kernel
    if args.explore_missing:
        print(f"Scanning {file_path} for missing kernels...")
        missing_counts = collect_missing_kernels(str(file_path), sample_size=500)
        
        # Get sample records for heuristic
        sample_records = load_jsonl(str(file_path), limit=100)
        
        # Filter to likely kernels (not character names)
        likely_kernels = [
            (k, c) for k, c in missing_counts.most_common(50)
            if is_likely_kernel_not_name(k, sample_records) and c >= 3
        ]
        
        if not likely_kernels:
            print("No missing kernels found!")
            return 1
        
        # Pick a random one (weighted by frequency)
        kernel_name = random.choice([k for k, c in likely_kernels[:20]])
        print(f"\n🎲 Randomly selected missing kernel: {kernel_name}")
        args.kernel = kernel_name
    
    # Mode: Sample stories using a specific kernel
    if args.kernel:
        print(f"Finding stories that use '{args.kernel}'...")
        matches = find_stories_with_kernel(str(file_path), args.kernel, limit=100)
        
        if not matches:
            print(f"No stories found using kernel '{args.kernel}'")
            return 1
        
        print(f"Found {len(matches)} stories using '{args.kernel}'")
        
        # Sample from matches
        n = min(args.num, len(matches))
        samples = random.sample(matches, n)
        
        print(f"\n{'='*70}")
        print(f"EXPLORING KERNEL: {args.kernel}")
        print(f"Showing {n} example{'s' if n > 1 else ''} of how '{args.kernel}' is used")
        print('='*70)
        
        for i, record in enumerate(samples, 1):
            display_sample(record, show_original=args.show_original, index=i)
        
        # Show implementation suggestion
        print(f"\n{'='*70}")
        print(f"💡 IMPLEMENTATION SUGGESTION FOR: {args.kernel}")
        print('='*70)
        print(f"""
To implement this kernel, add to gen5.py:

@REGISTRY.kernel("{args.kernel}")
def kernel_{args.kernel.lower()}(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    '''TODO: Describe what {args.kernel} does based on examples above.'''
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    char = chars[0] if chars else ctx.current_focus
    
    if char:
        # TODO: Update character state
        # char.Joy += 10
        return StoryFragment(f"{{char.name}} {args.kernel.lower()}ed.")
    
    # No character - used as concept
    return StoryFragment("{args.kernel.lower()}", kernel_name="{args.kernel}")
""")
        return 0
    
    # Default mode: Random sampling
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

