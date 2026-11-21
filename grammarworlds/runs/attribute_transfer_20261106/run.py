"""Reproduce imported-attribute examples and surface-only comparisons."""
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from grammarworlds.event_line_replay import paper_world, project_source, replay, verify
from grammarworlds.event_pool import attach, retrieve
from grammarworlds.pool_mechanics import PoolLines
from grammarworlds.test_event_pool import unrelated_world, unrelated_brief
from grammarworlds.world import Entity


def main():
    out = Path(__file__).parent
    graph = json.loads((ROOT/'grammarworlds/runs/entity_event_lines_20261106/refined/kite.json').read_text())
    template = project_source(graph, 'hero', [e['id'] for e in graph['events'] if e['kind'] in {'fetch_tape', 'mend'}])
    bindings = dict(worker='ada', item='book', tool='tape', supply='bench')
    cast = unrelated_world()
    cast.entities['omar'] = Entity('omar', 'Omar', 'person', 'garden', pronoun='he',
                                  properties={'can_hold', 'can_portal'})
    brief = unrelated_brief()
    brief['roles']['actor'] = {'candidates': [{'entity': 'ada', 'weight': 3}, {'entity': 'omar', 'weight': 1}]}
    candidates, _ = retrieve(brief, cast)
    probabilities = {c['bindings']['actor']: c['probability'] for c in candidates}
    assert probabilities == {'ada': .75, 'omar': .25}
    incompatible = cast.clone()
    incompatible.entities['omar'].properties.remove('can_portal')
    feasible, rejected = retrieve(brief, incompatible)
    assert len(feasible) == 1 and feasible[0]['bindings']['actor'] == 'ada'

    rows = []
    matched = enabled = 0
    for seed in range(10):
        attachment = attach(brief, cast, seed=seed)
        cases = [
            ('kite_to_book', paper_world(), template, bindings, {}),
            ('hat_local_cast', attachment['world'], attachment['template'], attachment['bindings'], {'driver_class': PoolLines}),
        ]
        for name, world, line, bound, options in cases:
            annotated = replay(world, line, bound, seed, heads=False, **options)
            surface = replay(world, line, bound, seed, heads=False, predict_attributes=False, **options)
            assert annotated['story'] == surface['story']
            assert annotated['final_world'] == surface['final_world']
            assert annotated['status'] == 'complete'
            verify(annotated, line, **options)
            for scene, old in zip(annotated['trace'], surface['trace']):
                assert [p['choices'] for p in scene['word_trace']] == [p['choices'] for p in old['word_trace']]
            matched += 1
            active = replay(world, line, bound, seed, heads=True, **options)
            verify(active, line, **options)
            assert active['status'] == 'complete'
            enabled += 1
            if seed == 7:
                rows.append(dict(case=name, **active))
    summary = dict(matched_surface_runs=matched, head_enabled_replayed=enabled,
                   actor_probabilities=probabilities,
                   incompatible_remaining=[dict(actor=c['bindings']['actor'], probability=c['probability']) for c in feasible],
                   rejected=rejected)
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    with gzip.open(out/'samples.jsonl.gz', 'wt') as stream:
        for row in rows:
            stream.write(json.dumps(row)+'\n')
    lines = ['# Imported attribute examples', '',
             'Seed 7 selected in advance; heads enabled. No prose filtering or repair.', '',
             f'{matched} matched runs preserve prose, world state and word distributions with heads off.',
             f'{enabled} head-enabled runs complete and replay successfully.', '',
             'Actor alternatives: Ada 75%, Omar 25%. Removing Omar\'s portal capability rejects that binding; Ada then has 100%.', '']
    for row in rows:
        lines += ['## '+row['case'], '', row['story'], '']
    lines += ['## Inspecting attributes', '',
              'The compressed sample traces contain joint predictions, attribute tables, positioned tokens, and source/target transfer decisions.',
              'The book keeps its own paper/torn state until repair; flyable/fragile source-kite features remain audit-only.',
              'The imported hat program keeps the local actor, rabbit, hat and audience bindings. Source names remain provenance-only.', '',
              'This verifies adaptation and sampling compatibility, not a new independent prose-quality evaluation.', '']
    (out/'report.md').write_text('\n'.join(lines))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
