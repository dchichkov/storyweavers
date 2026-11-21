"""Reproducible rule-bank mapping examples; no runtime model or prose repair."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from grammarworlds.event_mapping import generate_mapped, mapping_distribution
from grammarworlds.event_line_replay import paper_world, project_source, replay
from grammarworlds.world import Entity


def main():
    out = Path(__file__).parent
    graph = json.loads((ROOT/'grammarworlds/runs/entity_event_lines_20261106/refined/kite.json').read_text())
    ids = [e['id'] for e in graph['events'] if e['kind'] in {'fetch_tape', 'mend'}]
    mixed = paper_world()
    mixed.entities['ada'].properties.add('can_repair')
    mixed.entities['kite'] = Entity('kite', 'kite', 'object', 'ada',
        properties={'portable', 'physics:kite', 'flyable'}, state={'torn', 'grounded'})
    configurations = [('book_only', paper_world(), {}), ('book_or_kite', mixed, {}),
                      ('favor_kite', mixed, {'rule_factors': {'repair.kite': 4}})]
    samples, summary = [], {}
    for name, world, options in configurations:
        distribution = mapping_distribution(graph, 'hero', ids, world, **options)
        initial = world.to_dict(); counts = Counter()
        for heads in (False, True):
            for seed in range(10):
                row, chosen = generate_mapped(graph, 'hero', ids, world, seed=seed, heads=heads, **options)
                assert row['status'] == 'complete'
                assert world.to_dict() == initial
                counts[chosen['rules'][-1]] += 1
                if heads and seed in (0, 7): samples.append(dict(case=name, **row))
        summary[name] = dict(completed=20, selections=dict(counts),
            candidates=[{k:v for k,v in c.items() if k != 'template'} for c in distribution['candidates']],
            rejected=distribution['rejected'])
    # Compare the archived procedural projection with its bank replacement.
    old = json.loads((ROOT/'grammarworlds/runs/event_line_replay_20261106/inputs/solo.json').read_text())
    new = project_source(graph, 'hero', ids)
    for seed in range(10):
        before = replay(paper_world(), old['template'], old['bindings'], seed, heads=False)
        after = replay(paper_world(), new, old['bindings'], seed, heads=False)
        assert before['story'] == after['story']
        assert before['final_world']['entities'] == after['final_world']['entities']
        assert before['final_world']['flags'] == after['final_world']['flags']
        assert [p['choices'] for s in before['trace'] for p in s['word_trace']] == [p['choices'] for s in after['trace'] for p in s['word_trace']]
    summary['legacy_projection'] = dict(matched_runs=10, prose=True, entities=True, flags=True, word_probabilities=True,
        metadata_change='All participating roles now have local lines, including the supply; provenance records rule IDs.')
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    with gzip.open(out/'samples.jsonl.gz', 'wt') as stream:
        for sample in samples: stream.write(json.dumps(sample)+'\n')
    text = ['# Event mapping bank experiment', '',
            '60 complete, replay-verified runs: three configurations × ten seeds × heads off/on.',
            'Ten comparisons against the archived procedural projection preserve prose, physical entities, flags, and word probabilities.', '',
            'The source is the annotated kite fetch/mend segment. No target bindings are supplied.',
            'The mixed target explicitly contains both a torn book and a torn kite; Ada has both repair capabilities.',
            'The tape and bench are inferred from their affordances; wrong-holder bindings are rejected by simulation.', '',
            '| Context | Book repair | Kite repair |', '|---|---:|---:|',
            '| Only book is compatible | 100% | 0% |',
            '| Book and kite compatible | 66.67% | 33.33% |',
            '| Same world; kite rule ×4 context factor | 33.33% | 66.67% |', '',
            'These are authored weights, not calibrated likelihoods or learned attention. Samples below use seeds 0 and 7 chosen in advance.', '']
    for sample in samples:
        selected = sample['source']['mapping_distribution']
        text += [f"## {sample['case']}, seed {sample['seed']}", '', sample['story'], '',
                 'Rules: '+', '.join(selected['selected_rules'])+'. Target: '+selected['selected_bindings']['item']+'.', '']
    text += ['## Limits', '',
             'The resulting text is a short event segment, not a newly authored complete story. This is an architectural and grounding check, not a Luna quality evaluation.',
             'One full mapping is selected before token generation. Entity state is never averaged across alternatives.', '']
    (out/'report.md').write_text('\n'.join(text))
    sources = ['grammarworlds/event_mapping.py', 'grammarworlds/mapping_bank/core.json',
               'grammarworlds/event_line_replay.py', 'grammarworlds/attribute_transfer.py',
               'grammarworlds/test_event_mapping.py', str(Path(__file__).relative_to(ROOT))]
    (out/'manifest.json').write_text(json.dumps({p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}, indent=2)+'\n')
    print(json.dumps({name: value.get('completed', value.get('matched_runs')) for name,value in summary.items()}))


if __name__ == '__main__':
    main()
