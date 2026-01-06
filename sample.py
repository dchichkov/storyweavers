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
import re
import inspect
from pathlib import Path

# Import gen5 registry (auto-loads all kernel packs)
from gen5registry import generate_story, REGISTRY, KernelExecutor


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
    """Find stories that use a specific kernel. Returns list of (line_num, record) tuples."""
    import re
    matches = []
    
    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            try:
                record = json.loads(line)
                kernel = record.get('kernel', '') or ''
                if not kernel:
                    continue
                # Look for kernel name as function call or reference
                # Match: KernelName( or KernelName, or KernelName) or KernelName\n or +KernelName
                pattern = rf'\b{re.escape(kernel_name)}\b'
                if re.search(pattern, kernel):
                    matches.append((i, record))  # Store line number with record
                    if len(matches) >= limit:
                        break
            except json.JSONDecodeError:
                continue
    
    return matches


def collect_missing_kernels(file_path: str, sample_size: int = 500, include_characters: bool = False) -> tuple:
    """
    Scan stories and collect missing kernel frequencies.
    Returns (missing_counts, character_names_set)
    
    Args:
        file_path: Path to the kernels JSONL file
        sample_size: Number of stories to sample
        include_characters: If True, include character names in missing_counts
    """
    from collections import Counter
    
    missing_counts = Counter()
    all_character_names = set()
    records = load_jsonl(file_path, limit=sample_size)
    
    # First pass: collect all character names
    for record in records:
        kernel = record.get('kernel', '')
        all_character_names.update(extract_character_names_from_kernel(kernel))
    
    # Second pass: collect missing kernels
    for record in records:
        kernel = record.get('kernel', '')
        _, missing = check_kernel_coverage(kernel)
        for m in missing:
            # Optionally exclude character names
            if include_characters or m not in all_character_names:
                missing_counts[m] += 1
    
    return missing_counts, all_character_names


def extract_character_names_from_kernel(kernel_str: str) -> set:
    """
    Use AST to extract character names from kernel definition.
    Looks for patterns like: Name(Character, ...) 
    """
    if not kernel_str:
        return set()
    
    try:
        tree = ast.parse(kernel_str)
    except:
        return set()
    
    character_names = set()
    
    class CharacterVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            # Check if this is a call like Name(Character, ...)
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                # Check if first argument is 'Character'
                if node.args and isinstance(node.args[0], ast.Name):
                    if node.args[0].id == 'Character':
                        character_names.add(func_name)
            self.generic_visit(node)
    
    visitor = CharacterVisitor()
    visitor.visit(tree)
    return character_names


def is_character_name(kernel_name: str, character_names: set) -> bool:
    """Check if a kernel name is actually a character name."""
    return kernel_name in character_names


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


def get_kernel_source(kernel_name: str) -> tuple:
    """Get the source code of a kernel implementation with file/line info.
    
    Returns: (source_code, file_path, line_number) or (None, None, None) if not found
    """
    if kernel_name not in REGISTRY.kernels:
        return None, None, None
    
    kernel_func = REGISTRY.kernels[kernel_name]
    try:
        source = inspect.getsource(kernel_func)
        file_path = inspect.getsourcefile(kernel_func)
        line_number = inspect.getsourcelines(kernel_func)[1]
        
        # Make file path relative to project root if possible
        if file_path:
            try:
                file_path = Path(file_path).relative_to(Path.cwd())
            except ValueError:
                # If not in current directory, just use absolute path
                pass
        
        return source, file_path, line_number
    except Exception as e:
        return f"# Could not retrieve source: {e}", None, None


def display_sample(record: dict, show_original: bool = False, show_source: bool = False, index: int = None, story_id: str = None):
    """Display a sampled story with its kernel and generated text."""
    kernel = record.get('kernel', '')
    original = record.get('story', '')
    summary = record.get('summary', '')
    
    header = f"SAMPLE {index}" if index else "SAMPLE"
    print(f"\n{'='*70}")
    print(header)
    print('='*70)
    
    # Show story ID if available
    if story_id:
        print(f"\n🆔 STORY ID: {story_id}")
    
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
        print(original)
    
    # Show kernel source code if requested
    if show_source and implemented:
        print(f"\n🔧 KERNEL IMPLEMENTATIONS:")
        print("-" * 40)
        for i, kernel_name in enumerate(implemented[:10], 1):  # Limit to first 10 to avoid clutter
            source, file_path, line_num = get_kernel_source(kernel_name)
            if source:
                location = f"{file_path}:{line_num}" if file_path and line_num else "unknown location"
                print(f"\n[{i}] {kernel_name} ({location}):")
                print(source)
                print()
        if len(implemented) > 10:
            print(f"... and {len(implemented) - 10} more kernels (use fewer samples to see all)")
    
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
    parser.add_argument('--show-source', '-s', action='store_true',
                        help='Show source code of implemented kernels')
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
    parser.add_argument('--include-characters', '-c', action='store_true',
                        help='Include character names in missing kernels list (default: exclude)')
    parser.add_argument('--story-id', type=str, default=None,
                        help='Generate a specific story by ID (format: data00:123 or story_123)')
    
    args = parser.parse_args()
    
    # Mode: Generate specific story by ID
    if args.story_id:
        # Parse story ID (supports data00:123 or story_123 formats)
        if ':' in args.story_id:
            # Format: data00:123
            dataset, line_str = args.story_id.split(':', 1)
            line_num = int(line_str)
        elif args.story_id.startswith('story_'):
            # Format: story_123
            dataset = 'data00'  # default
            line_num = int(args.story_id.replace('story_', ''))
        else:
            print(f"Error: Invalid story ID format: {args.story_id}")
            print("Use format: data00:123 or story_123")
            return 1
        
        # Set deterministic seed based on story ID for reproducible template selection
        # Use hash of story_id to generate a seed
        import hashlib
        seed_hash = int(hashlib.md5(args.story_id.encode()).hexdigest()[:8], 16)
        random.seed(seed_hash)
        
        # Build file path
        file_path = Path('TinyStories_kernels') / f'{dataset}.kernels.jsonl'
        if not file_path.exists():
            print(f"Error: Dataset file not found: {file_path}")
            return 1
        
        # Read the specific story
        with open(file_path) as f:
            for i, line in enumerate(f):
                if i == line_num:
                    record = json.loads(line)
                    story_id = f"{dataset}:{i}"
                    display_sample(record, 
                                 show_original=args.show_original,
                                 show_source=args.show_source,
                                 story_id=story_id)
                    return 0
        
        print(f"Error: Line {line_num} not found in {dataset}")
        return 1
    
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
        missing_counts, character_names = collect_missing_kernels(
            str(file_path), 
            sample_size=1000,
            include_characters=args.include_characters
        )
        
        print(f"\n{'='*70}")
        print("MOST COMMON MISSING KERNELS")
        print('='*70)
        print(f"{'Kernel':<30} {'Count':<10} {'Type'}")
        print('-'*70)
        
        for kernel_name, count in missing_counts.most_common(30):
            # Show whether it's a character or kernel
            if kernel_name in character_names:
                type_str = "👤 character"
            else:
                type_str = "🔧 kernel"
            print(f"{kernel_name:<30} {count:<10} {type_str}")
        
        if not args.include_characters and character_names:
            print(f"\n({len(character_names)} character names excluded from this list)")
            print(f"Use --include-characters to see character names")
        
        return 0
    
    # Mode: Explore a random missing kernel
    if args.explore_missing:
        print(f"Scanning {file_path} for missing kernels...")
        missing_counts, character_names = collect_missing_kernels(str(file_path), sample_size=500)
        
        # Filter to kernels with at least 3 occurrences
        likely_kernels = [
            (k, c) for k, c in missing_counts.most_common(50)
            if c >= 3
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
        
        # When exploring a specific kernel, always show original by default
        show_orig = True if args.kernel else args.show_original
        
        # Extract dataset name from file_path for story IDs
        dataset = file_path.stem.replace('.kernels', '')
        
        for i, (line_num, record) in enumerate(samples, 1):
            story_id = f"{dataset}:{line_num}"
            display_sample(record, show_original=show_orig, show_source=args.show_source, index=i, story_id=story_id)
        
        # Show implementation status
        print(f"\n{'='*70}")
        if args.kernel in REGISTRY.kernels:
            print(f"✅ KERNEL IMPLEMENTED: {args.kernel}")
            print('='*70)
            print(f"\nThe '{args.kernel}' kernel is already implemented and ready to use.")
            print(f"Total kernels in registry: {len(REGISTRY.kernels)}")
        else:
            print(f"💡 IMPLEMENTATION SUGGESTION FOR: {args.kernel}")
            print('='*70)
            print(f"""
To implement this kernel, add to a new kernel pack file (e.g., gen5kXX.py):

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
        display_sample(record, show_original=args.show_original, show_source=args.show_source, index=i)
        
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

