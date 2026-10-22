#!/usr/bin/env python3
"""Offline mixed-seed trial audit and complete selected-story reading copy."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

import factory as f
from world_batch_analysis import analyze


def run(out):
    analysis = analyze(out)
    samples = [json.loads(line) for line in (out / 'selected_samples.jsonl').read_text().splitlines()]
    grades = {r['sample_id']: r for r in map(json.loads, (out / 'story_ratings.jsonl').read_text().splitlines())}
    gallery, audits = ['# Mixed-seed trial: all selected stories', ''], []
    for world in sorted({r['world'] for r in samples}):
        brief = json.loads((out / world / 'seed.json').read_text())
        definition = json.loads((out / world / 'world.json').read_text())
        pool = [json.loads(line) for line in (out / world / 'samples.jsonl').read_text().splitlines()]
        def missing(row):
            return [word for word in brief['words'] if not re.search(r'(?<!\w)' + re.escape(word) + r'(?!\w)', row['story'], re.I)]
        chosen = [r for r in samples if r['world'] == world]
        audits.append(dict(world=world, title=definition['title'], ingredients=brief['seed_mix'], words=brief['words'],
            pool_stories=len(pool), pool_all_words=sum(not missing(r) for r in pool),
            pool_missing_word_counts=dict(Counter(w for r in pool for w in missing(r))),
            selected_all_words=sum(not missing(r) for r in chosen),
            selected_missing={r['sample_id']: missing(r) for r in chosen if missing(r)},
            unique_pool_texts=len({r['story'] for r in pool})))
        gallery += [f'## {world}: {definition["title"]}', '', 'Ingredients: ' + '; '.join(
            f'{category}: {item["id"]} — {item["hint"]}' for category, items in brief['seed_mix'].items() for item in items),
            '', 'Required words: ' + ', '.join(brief['words']), '']
        for row in chosen:
            score = grades.get(row['sample_id'])
            gallery += [f'### {row["sample_id"]}', '', row['story'], '',
                ('Terra overall: ' + str(score['rating']['overall']) + '/9. ' + score['note']) if score else 'Grade pending.', '']
    result = dict(worlds=audits, selected_all_words=sum(r['selected_all_words'] for r in audits),
        pool_all_words=sum(r['pool_all_words'] for r in audits),
        matching_note='Case-insensitive whole-word matching; inflections do not count as the exact requested word. Presence does not establish natural usage.',
        coverage=analysis['coverage'])
    f.save(out / 'seed_audit.json', result)
    (out / 'STORIES.md').write_text('\n'.join(gallery))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out', type=Path)
    print(json.dumps(run(parser.parse_args().out), indent=2, ensure_ascii=False))
