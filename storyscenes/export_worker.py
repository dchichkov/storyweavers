#!/usr/bin/env python3
"""Replay saved samples and QA with their frozen runtime, without API access."""
import gzip
import json
from pathlib import Path
import sys


def main(world, out):
    world, out = Path(world).resolve(), Path(out)
    frozen = world.parent / '_runtime'
    if not (frozen / 'qa.py').is_file():
        raise ValueError('A frozen QA/runtime snapshot is required')
    sys.path.insert(0, str(frozen))
    import worker
    import qa
    from qa_checks import check_conversation

    saved = [json.loads(line) for line in (world / 'samples.jsonl').read_text().splitlines()]
    selected = {r['seed']: r for r in map(json.loads, (world / 'selected_samples.jsonl').read_text().splitlines())}
    settings = json.loads((world.parent / 'settings.json').read_text())
    if len({r['seed'] for r in saved}) != len(saved):
        raise ValueError('Duplicate sample seeds')
    temp = out.with_suffix('.tmp')
    with gzip.open(temp, 'wt', encoding='utf-8') as handle:
        for original in saved:
            row = worker.sample(world, [original['seed']], prose=True,
                                prose_seed=original['prose_seed'])[0]
            for key in ('story', 'paragraphs', 'trace_sha256'):
                if row[key] != original[key]:
                    raise ValueError(f'Replay mismatch: {world.name}:{row["seed"]}:{key}')
            row = qa.enrich(row, qa_seed=settings['qa_seed'], limit=settings['qa_limit'],
                            pairs=settings['qa_pairs'])
            if row['seed'] in selected:
                for key in ('story', 'trace', 'conversations', 'conversation_metadata'):
                    if row[key] != selected[row['seed']][key]:
                        raise ValueError(f'Graded sample changed: {world.name}:{row["seed"]}:{key}')
            row['export_qa_errors'] = {c['id']: errors for c in row['conversations']
                                      if (errors := check_conversation(row['trace'], c, row['paragraphs']))}
            # The diagnostic `qa` list contains state fragments; never train on it.
            row.pop('qa', None)
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')
    temp.replace(out)
    return len(saved)


if __name__ == '__main__':
    print(main(*sys.argv[1:]))
