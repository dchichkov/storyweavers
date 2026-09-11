"""Compose saved patch pairs without inference or network calls."""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
from pathlib import Path

from .artifacts import save_json, save_text
from .kernel_author import render
from .span_patches import bundle, digest, apply_pair, story_value


def compose(base, pairs, *, count=5000, seed=42, minimum=3, maximum=5, max_attempts=100000):
    if count < 1 or minimum < 1 or maximum < minimum or max_attempts < 1:
        raise ValueError('invalid count, patch range, or attempt limit')
    valid, invalid, single_results = [], [], set()
    ids = set()
    for pair in pairs:
        try:
            if pair.get('version') != 1 or pair.get('base_sha256') != digest(base):
                raise ValueError('patch pair belongs to another base or version')
            if not isinstance(pair.get('id'), str) or not pair['id'] or pair['id'] in ids:
                raise ValueError('missing or duplicate pair ID')
            result = apply_pair(base, pair)
            key = digest(result['story'])
            if key in single_results or result['kernel'] == base['kernel'] or result['story'] == base['story']:
                raise ValueError('duplicate or unchanged standalone result')
            single_results.add(key)
            ids.add(pair['id'])
            valid.append(pair)
        except (ValueError, KeyError, TypeError, SyntaxError) as exc:
            invalid.append({'id': pair.get('id'), 'error': str(exc)})
    valid.sort(key=lambda p: p['id'])
    n = len(valid)
    maximum = min(maximum, n)
    possible = sum(math.comb(n, k) for k in range(minimum, maximum + 1))
    rng = random.Random(seed)
    # Enumerate small spaces to detect exhaustion; sample large spaces with a bound.
    if possible <= max_attempts:
        choices = [c for k in range(minimum, maximum + 1) for c in itertools.combinations(range(n), k)]
        rng.shuffle(choices)
    else:
        choices = (tuple(sorted(rng.sample(range(n), rng.randint(minimum, maximum)))) for _ in range(max_attempts))
    records, seen_sets, seen_stories = [], set(), {digest(base['story'])}
    rejected, duplicates, draws = 0, 0, 0
    for chosen in choices:
        draws += 1
        if chosen in seen_sets:
            continue
        seen_sets.add(chosen)
        current = base
        try:
            # Canonical ID order: reproducible, no order-search or repair.
            for index in chosen:
                current = apply_pair(current, valid[index])
        except (ValueError, KeyError, TypeError, SyntaxError):
            rejected += 1
            continue
        key = digest(current['story'])
        if key in seen_stories:
            duplicates += 1
            continue
        seen_stories.add(key)
        records.append({'patch_ids': [valid[i]['id'] for i in chosen], 'bundle': current})
        if len(records) == count:
            break
    return records, {'requested': count, 'generated': len(records), 'complete': len(records) == count,
                     'valid_pairs': n, 'invalid_pairs': invalid, 'possible_sets': possible,
                     'draws': draws, 'attempted_sets': len(seen_sets), 'conflicts': rejected,
                     'duplicate_outputs': duplicates, 'seed': seed,
                     'semantic_fidelity_judged': False, 'llm_calls': 0}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--pairs', type=Path, required=True, help='directory searched recursively for pair.json')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--count', type=int, default=5000)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--min-patches', type=int, default=3)
    p.add_argument('--max-patches', type=int, default=5)
    p.add_argument('--max-attempts', type=int, default=100000)
    args = p.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise ValueError('use an empty output directory')
    base = bundle((args.base / 'kernel.txt').read_text(), json.loads((args.base / 'story.json').read_text()))
    paths = sorted(args.pairs.rglob('pair.json'))
    pairs = [json.loads(path.read_text()) for path in paths]
    records, summary = compose(base, pairs, count=args.count, seed=args.seed,
                               minimum=args.min_patches, maximum=args.max_patches,
                               max_attempts=args.max_attempts)
    summary['base_sha256'] = digest(base)
    summary['pair_files'] = [str(path) for path in paths]
    for i, record in enumerate(records):
        directory = args.out / f'v{i:05d}'
        value = story_value(record['bundle'])
        save_text(directory / 'kernel.txt', record['bundle']['kernel'])
        save_json(directory / 'story.json', value)
        save_text(directory / 'story.md', render(value))
        save_json(directory / 'provenance.json', {'patch_ids': record['patch_ids'], 'base_sha256': digest(base)})
    save_json(args.out / 'summary.json', summary)
    print(f"Generated {len(records)}/{args.count} candidates; zero LLM calls. See {args.out / 'summary.json'}")
    return 0 if summary['complete'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
