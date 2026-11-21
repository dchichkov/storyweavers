"""Reproduce source-size counts and fresh-run physical guard checks.

Run from the repository root with .venv/bin/python -m
grammarworlds.runs.shared_core_iterations_20261105.analyze.
"""
import ast
from collections import Counter
import gzip
import hashlib
import io
import json
from pathlib import Path
import tokenize

from grammarworlds.storytelling.audit import physical_checks
from grammarworlds.storytelling.runtime import setup
from grammarworlds.world import Frame

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def size(path):
    source = path.read_text()
    result = dict(bytes=len(path.read_bytes()), lines=len(source.splitlines()))
    if path.suffix == '.py':
        result['statements'] = sum(isinstance(n, ast.stmt) for n in ast.walk(ast.parse(source)))
        omitted = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE,
                   tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER}
        result['tokens'] = sum(t.type not in omitted for t in tokenize.generate_tokens(io.StringIO(source).readline))
    return result


def total(rows):
    result = Counter()
    for row in rows:
        result.update(row)
    return dict(result)


def run():
    baseline = json.loads((HERE/'baseline_custom_size.json').read_text())
    merged = {name: size(ROOT/name) for name in baseline}
    (HERE/'final_custom_size.json').write_text(json.dumps(merged, indent=2)+'\n')
    result = {'custom_before': total(baseline.values()), 'custom_after': total(merged.values())}
    for label, root in [('before', HERE/'baseline_source'), ('after', ROOT)]:
        folder = root/'grammarworlds/storytelling'
        paths = sorted(p for p in folder.iterdir() if p.suffix in {'.py', '.json'})
        result['storytelling_package_'+label] = total(size(p) for p in paths)
        result['storytelling_package_'+label]['files'] = len(paths)
    guards = Counter()
    with gzip.open(HERE/'final_merged/sample_traces.jsonl.gz', 'rt') as source:
        for line in source:
            row = json.loads(line)
            if row['profile'] != 'expanded_tuned':
                continue
            pack, world = setup(row['scenario'], row['seed'], **row.get('options', {}))
            for event in row['final_world']['history']:
                frame = Frame(**{**event['frame'], 'cause_ids': tuple(event['frame']['cause_ids'])})
                guards[row['scenario']] += physical_checks(pack, world, frame)
                record = pack.commit(world, frame, event['sentence'])
                for key in ('referents', 'speakers', 'narrated'):
                    record[key] = event[key]
            assert world.to_dict() == row['final_world']
    result['physical_guard_interventions'] = dict(guards)
    frozen = json.loads((ROOT/'grammarworlds/portable/sources/pre_holdout_freeze.json').read_text())
    assert all(hashlib.sha256((ROOT/'grammarworlds/portable'/p).read_bytes()).hexdigest() == h
               for p, h in frozen['sha256'].items())
    result['frozen_portable_files_verified'] = len(frozen['sha256'])
    # Original grammar + original receiver must remain identical on fresh seeds.
    def records(folder):
        with gzip.open(HERE/folder/'stories_qa.jsonl.gz', 'rt') as source:
            return {(r['scenario'], r['tense'], r['seed'], r['profile']): r
                    for r in map(json.loads, source)}
    old, new = records('final_baseline'), records('final_merged')
    original_keys = [k for k in old if k[-1] in {'off', 'manual'}]
    assert all(old[k] == new[k] for k in original_keys)
    result['original_records_exactly_preserved'] = len(original_keys)
    (HERE/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    run()
