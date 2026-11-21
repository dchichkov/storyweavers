"""Inspect the underdefined controller and mapped segment without changing either."""
from collections import defaultdict
import gzip
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from grammarworlds.event_mapping import mapping_distribution, generate_mapped
from grammarworlds.event_line_replay import paper_world
from grammarworlds.underdefined_probe import initial_world


def event_mass(scene, key):
    values = defaultdict(float)
    for candidate in scene['word_trace'][0][key]:
        event = scene['attribute_table'][candidate['attributes']]['event']
        identity = json.dumps(dict(kind=event['source_kind'], roles=event['roles']), sort_keys=True)
        values[identity] += candidate['probability']
    return [dict(json.loads(identity), probability=mass) for identity, mass in values.items()]


def main():
    out = Path(__file__).parent
    graph = json.loads((ROOT/'grammarworlds/runs/entity_event_lines_20261106/refined/kite.json').read_text())
    ids = [e['id'] for e in graph['events'] if e['kind'] in {'fetch_tape', 'mend'}]
    strict = mapping_distribution(graph, 'hero', ids, initial_world())
    assert not strict['candidates']
    baseline = importlib.import_module('grammarworlds.runs.underdefined_attributes_20261106.run').run(seed=7, steps=8)
    mapped, attachment = generate_mapped(graph, 'hero', ids, paper_world(), seed=7, heads=True)
    latent = []
    for scene, committed in zip(mapped['trace'], mapped['final_world']['history']):
        selected_tokens = []
        for step in scene['word_trace']:
            if len(step['choices']) > 1 or step['selected'] in {'tape', 'book', 'repair', 'bench'}:
                selected_tokens.append(dict(token=step['selected'], choices=step['choices'],
                    posterior=[dict(probability=c['probability'], attributes=scene['attribute_table'][c['attributes']])
                               for c in step['selected_attributes']]))
        latent.append(dict(event=scene['line_event'], operation=scene['operation'], ready=scene['ready_events'],
            prior=event_mass(scene, 'annotated_choices'), committed=committed,
            tokens=selected_tokens, transfer=scene['attribute_transfer'][scene['line_event']]))
    summary = dict(seed=7, heads=True, source_events=ids, strict_fixture_mapping=strict,
        added_declarations=dict(book=['paper'], ada=['can_patch_paper'], omar=['can_patch_paper']),
        baseline=dict(story=baseline['story'], metrics=baseline['metrics'], goal_reached=baseline['goal_reached'],
            stop=baseline['stop_reason'], events=[s['frame'] for s in baseline['trace']],
            first_scene_prior=event_mass(baseline['trace'][0], 'annotated_choices')),
        mapped=dict(story=mapped['story'], status=mapped['status'], metrics=mapped['metrics'],
            goal_reached='repaired' in mapped['final_world']['entities']['book']['state'],
            mapping=mapped['source']['mapping_distribution'], latent=latent))
    assert summary['mapped']['goal_reached'] and not baseline['goal_reached']
    assert all(len(e['prior']) == 1 and abs(e['prior'][0]['probability']-1) < 1e-9 for e in latent)
    assert mapped['metrics']['choice_steps'] == 2
    (out/'inspection.json').write_text(json.dumps(summary, indent=2)+'\n')
    with gzip.open(out/'traces.jsonl.gz', 'wt') as stream:
        for mode, row in [('baseline', baseline), ('mapped', mapped)]:
            stream.write(json.dumps(dict(mode=mode, **row))+'\n')
    report = ['# Underdefined story: latent stream inspection', '',
        'Fresh seed-7 runs, heads enabled. No rerolls, text edits, new rules, or engine changes.', '',
        '## Mapped generation', '', mapped['story'], '',
        'The target has no authored event sequence. The source fetch/mend segment is explicitly selected from the annotated kite story; automatic source-segment retrieval is not involved.',
        'Target role bindings are inferred. The existing paper-world fixture declares paper material for the book and paper-patching capability for Ada and Omar.', '',
        '| Stage | Latent event | Probability | Physical consequence |',
        '|---|---|---:|---|',
        '| Mapping | fetch → paper repair; Ada/book/tape/bench | 100% | Only feasible complete binding |',
        '| Scene 1 | fetch(actor=Ada, item=tape, source=bench) | 100% | Tape: bench → Ada |',
        '| Scene 2 | patch_paper(actor=Ada, item=book, tool=tape) | 100% | Book: torn → repaired |', '',
        'Omar is rejected because he does not hold the book. Kite repair is rejected because compatible carriers/capabilities are absent.',
        'The committed segment completes and replays; it does not set a whole-story ending flag.', '',
        '## Word-level uncertainty', '',
        'There are 19 sampler steps including punctuation and two END markers. Only two steps have more than one possible word; heads change one distribution.',
        'At the start of repair: she 40%, Using 25%, With 25%, Ada 10%.',
        'After selecting she, three annotation bundles survive: use tape to repair (50%), repair with tape (25%), fix with tape (25%). All bind the same actor, object, tool and physical event.',
        'At the following step, head reweighting gives used 41.18%, fixed 29.41%, repaired 29.41%. Selecting used resolves the remaining construction ambiguity.', '',
        '## Attribute inspection', '',
        '- Tape is observed at the bench during fetch and at Ada during repair.',
        '- Book remains observed as torn during pre-commit token generation; repaired is a proposed effect until the event commits.',
        '- She resolves to Ada; the imported source name and kite-only properties are absent from live target entity attributes.',
        '- The repair verb is tagged as an embedded action with book as its object.',
        '- Defect: the book token has syntax_role=predicate despite correct entity=book and action.arguments.object=book. The shallow syntax role is inherited incorrectly under the embedded construction.',
        '- The bench mention is a nominal description without a token-local entity binding; the enclosing event correctly binds source=bench. Role-complete event metadata does not imply every mention has a local referent.', '',
        '## Original unordered controller', '', baseline['story'], '',
        'Latent events: '+ ' → '.join(s['frame']['kind'] for s in baseline['trace'])+'.',
        'It reaches the eight-event limit with the book still torn. Its available operations do not include repair.',
        'Running mapping on the unchanged original world yields zero feasible mappings because paper material and repair capabilities are undeclared; these are not silently invented.', '',
        '## Assessment', '',
        'The mapping makes an imported repair sequence executable and grounded. It has not yet produced an open-ended event predictor: source sequence selection is supplied, mapping selects one complete program, and each scene here has one ready event.',
        'The resulting segment lacks a narrated premise, turn, dialogue and ending image. Text quality remains limited by the supplied event sequence; additional annotation richness alone does not supply story structure.', '']
    (out/'report.md').write_text('\n'.join(report))
    print(mapped['story'])
    print(json.dumps(dict(mapped=mapped['metrics'], baseline=baseline['metrics'], baseline_events=[s['frame']['kind'] for s in baseline['trace']]), indent=2))


if __name__ == '__main__':
    main()
