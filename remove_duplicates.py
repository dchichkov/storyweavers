#!/usr/bin/env python3
"""
Analyze duplicate kernels and create a plan for removal.
Keeps better implementations based on:
1. gen5.py implementations (reference)
2. More complete implementations
3. Later file implementations (if they're better)
"""

import re
import ast
from pathlib import Path
from collections import defaultdict

# Collect all kernel registrations
duplicates = defaultdict(list)

kernel_files = [
    'gen5.py',
    'gen5k01.py',
    'gen5k02.py', 
    'gen5k03.py',
    'gen5k04.py',
    'gen5k05.py',
    'gen5k06.py',
    'gen5k07.py',
]

def extract_kernels_from_file(filepath):
    """Extract all kernel registrations and their line numbers from a file."""
    kernels = []
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            
        # Find all @REGISTRY.kernel("KernelName") decorators
        pattern = r'@REGISTRY\.kernel\(["\'](\w+)["\']\)'
        for i, line in enumerate(lines, 1):
            match = re.search(pattern, line)
            if match:
                kernel_name = match.group(1)
                # Find the function definition
                func_start = i
                func_end = i + 1
                # Scan ahead to find the end of the function
                indent_level = None
                for j in range(i, min(i + 100, len(lines))):
                    if lines[j].strip().startswith('def '):
                        # This is the function start
                        func_start = j + 1
                        indent_level = len(lines[j]) - len(lines[j].lstrip())
                    elif indent_level is not None and lines[j].strip() and not lines[j].startswith(' ' * (indent_level + 1)):
                        func_end = j
                        break
                
                func_lines = lines[func_start-1:func_end]
                kernels.append({
                    'name': kernel_name,
                    'line': i,
                    'func_start': func_start,
                    'func_end': func_end,
                    'code': '\n'.join(func_lines),
                    'length': len(func_lines)
                })
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    
    return kernels

# Scan all files
for kfile in kernel_files:
    fpath = Path(kfile)
    if not fpath.exists():
        continue
    kernels = extract_kernels_from_file(kfile)
    for k in kernels:
        duplicates[k['name']].append({
            'file': kfile,
            'line': k['line'],
            'func_start': k['func_start'],
            'func_end': k['func_end'],
            'code': k['code'],
            'length': k['length']
        })

# Find actual duplicates
dup_kernels = {k: v for k, v in duplicates.items() if len(v) > 1}

print(f"Found {len(dup_kernels)} duplicate kernels:\n")

# Create removal plan
to_remove = []

for kernel_name, locations in sorted(dup_kernels.items()):
    print(f"\n{'='*70}")
    print(f"Kernel: {kernel_name}")
    print(f"{'='*70}")
    
    # Show all locations
    for i, loc in enumerate(locations):
        print(f"\n  [{i+1}] {loc['file']}:{loc['line']} (lines: {loc['func_start']}-{loc['func_end']}, length: {loc['length']})")
    
    # Decision logic: keep gen5.py if it exists, otherwise keep the last one
    gen5_loc = [loc for loc in locations if loc['file'] == 'gen5.py']
    
    if gen5_loc:
        keep = gen5_loc[0]
        print(f"\n  ✓ KEEP: {keep['file']} (reference implementation)")
        for loc in locations:
            if loc['file'] != 'gen5.py':
                to_remove.append((kernel_name, loc))
                print(f"  ✗ REMOVE: {loc['file']}:{loc['line']}")
    else:
        # Keep the most recent (last in list, which is usually the most refined)
        keep = locations[-1]
        print(f"\n  ✓ KEEP: {keep['file']} (latest implementation)")
        for loc in locations[:-1]:
            to_remove.append((kernel_name, loc))
            print(f"  ✗ REMOVE: {loc['file']}:{loc['line']}")

print(f"\n\n{'='*70}")
print(f"SUMMARY: {len(to_remove)} kernel definitions to remove")
print(f"{'='*70}\n")

# Group by file for easier removal
by_file = defaultdict(list)
for kernel_name, loc in to_remove:
    by_file[loc['file']].append((kernel_name, loc['func_start'], loc['func_end']))

for file, removals in sorted(by_file.items()):
    print(f"\n{file}: {len(removals)} kernels to remove")
    for kernel_name, start, end in sorted(removals, key=lambda x: x[1], reverse=True):
        print(f"  - {kernel_name} (lines {start}-{end})")

print("\n" + "="*70)
print("Ready to remove duplicates? (This script just analyzed)")
print("="*70)

