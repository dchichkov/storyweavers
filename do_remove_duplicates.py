#!/usr/bin/env python3
"""
Actually remove duplicate kernels based on the analysis.
Removes kernels by deleting the decorator and function definition.
"""

from pathlib import Path
import re

# Kernels to remove: (file, kernel_name, decorator_line, func_start, func_end)
to_remove = [
    # gen5k01.py: 11 kernels
    ('gen5k01.py', 'Break', 1014, 1015, 1028),
    ('gen5k01.py', 'Encourage', 766, 767, 780),
    ('gen5k01.py', 'Failure', 749, 750, 765),
    ('gen5k01.py', 'Success', 732, 733, 748),
    ('gen5k01.py', 'Sing', 583, 584, 597),
    ('gen5k01.py', 'Swim', 559, 560, 582),
    ('gen5k01.py', 'Dance', 530, 531, 558),
    ('gen5k01.py', 'Build', 505, 506, 529),
    ('gen5k01.py', 'Climb', 322, 323, 336),
    ('gen5k01.py', 'Danger', 296, 297, 307),
    ('gen5k01.py', 'Warn', 280, 281, 295),
    
    # gen5k02.py: 14 kernels
    ('gen5k02.py', 'Whisper', 1812, 1813, 1826),
    ('gen5k02.py', 'Observe', 1774, 1775, 1794),
    ('gen5k02.py', 'Paint', 1373, 1374, 1388),
    ('gen5k02.py', 'Cook', 1325, 1326, 1340),
    ('gen5k02.py', 'Realization', 1214, 1215, 1219),
    ('gen5k02.py', 'Splash', 1035, 1036, 1046),
    ('gen5k02.py', 'Pour', 916, 917, 930),
    ('gen5k02.py', 'Dig', 886, 887, 900),
    ('gen5k02.py', 'Decision', 653, 654, 658),
    ('gen5k02.py', 'Attempt', 596, 597, 626),
    ('gen5k02.py', 'Insight', 395, 396, 423),
    ('gen5k02.py', 'Gratitude', 366, 367, 394),
    ('gen5k02.py', 'Promise', 216, 217, 245),
    ('gen5k02.py', 'Request', 149, 150, 180),
    
    # gen5k03.py: 11 kernels
    ('gen5k03.py', 'Daddy', 1839, 1840, 1854),
    ('gen5k03.py', 'Outcome', 1781, 1782, 1806),
    ('gen5k03.py', 'Transform', 1758, 1759, 1780),
    ('gen5k03.py', 'Shy', 1475, 1476, 1486),
    ('gen5k03.py', 'Brave', 1462, 1463, 1474),
    ('gen5k03.py', 'Spot', 1280, 1281, 1300),
    ('gen5k03.py', 'Idea', 940, 941, 964),
    ('gen5k03.py', 'Excitement', 663, 664, 685),
    ('gen5k03.py', 'Acceptance', 408, 409, 429),
    ('gen5k03.py', 'Cooperation', 343, 344, 364),
    ('gen5k03.py', 'Warning', 126, 127, 151),
    
    # gen5k04.py: 8 kernels
    ('gen5k04.py', 'Cooperation', 1902, 1903, 1920),
    ('gen5k04.py', 'Reassure', 1485, 1486, 1503),
    ('gen5k04.py', 'Observe', 960, 961, 983),
    ('gen5k04.py', 'Retrieve', 785, 786, 810),
    ('gen5k04.py', 'Warning', 684, 685, 703),
    ('gen5k04.py', 'Request', 615, 616, 641),
    ('gen5k04.py', 'Confidence', 317, 318, 339),
    ('gen5k04.py', 'Return', 225, 226, 245),
    
    # gen5k05.py: 5 kernels
    ('gen5k05.py', 'Broken', 1381, 1382, 1393),
    ('gen5k05.py', 'Illness', 1299, 1300, 1319),
    ('gen5k05.py', 'Sleepy', 1055, 1056, 1063),
    ('gen5k05.py', 'Loneliness', 653, 654, 663),
    ('gen5k05.py', 'Comfort', 477, 478, 504),
    
    # gen5k06.py: 2 kernels
    ('gen5k06.py', 'Pride', 1631, 1632, 1647),
    ('gen5k06.py', 'Pick', 1165, 1166, 1186),
]

# Group by file
from collections import defaultdict
by_file = defaultdict(list)
for item in to_remove:
    filename, kernel_name, dec_line, start, end = item
    by_file[filename].append((kernel_name, dec_line, start, end))

# Sort by line number descending so we can remove from bottom to top
for filename in by_file:
    by_file[filename].sort(key=lambda x: x[1], reverse=True)

# Process each file
for filename, removals in by_file.items():
    filepath = Path(filename)
    if not filepath.exists():
        print(f"Warning: {filename} not found, skipping")
        continue
    
    print(f"\nProcessing {filename}...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for kernel_name, dec_line, start, end in removals:
        print(f"  Removing {kernel_name} (lines {dec_line}-{end})...")
        
        # Remove lines from decorator to end of function (inclusive)
        # Line numbers are 1-based, list indices are 0-based
        del lines[dec_line-1:end]
    
    # Write back
    with open(filepath, 'w') as f:
        f.writelines(lines)
    
    print(f"  ✓ Removed {len(removals)} duplicate kernels from {filename}")

print("\n" + "="*70)
print("Duplicate removal complete!")
print("="*70)
print("\nVerifying...")

