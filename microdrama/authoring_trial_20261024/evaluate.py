"""Shared evaluator frozen before dispatch; candidate code is trusted local Python."""
import argparse
from copy import deepcopy
from dataclasses import asdict
import importlib
import itertools
import json
from pathlib import Path
import re

from microdrama.engine import World, compose, digest, replay


ROOT = Path(__file__).parent
KEYS = ('access', 'cooperate', 'distraction')


def configurations():
    return [dict(zip(KEYS, values)) for values in itertools.product((True, False), repeat=3)]


def produce(pack, config, seed):
    world = pack.build_world(dict(config))
    assert isinstance(world, World)
    assert world.state['valley.ended'] is False and world.state['valley.outcome'] == ''
    initial = deepcopy(world.state)
    dramas = pack.dramas()
    assert 6 <= len(dramas) <= 12, 'Use 6–12 bounded encounters'
    episodes, choices = compose(world, dramas, None, seed)
    paragraphs = []
    for ep in episodes:
        before = deepcopy(ep)
        rendered = pack.render(ep)
        assert ep == before, 'Rendering mutated a historical episode'
        assert rendered, 'Every selected encounter needs a performance'
        for n, p in enumerate(rendered):
            assert p['text'].strip()
            assert p['evidence'] and set(p['evidence']) <= set(ep.event_ids)
            assert set(p['reveals']) <= set(ep.after)
            paragraphs.append(dict(p, id=f'{ep.id}.{n+1}', drama=ep.id))
    snapshot = deepcopy(world.state)
    qa = pack.questions(world, episodes)
    assert world.state == snapshot, 'Questions mutated state'
    return {'title': pack.TITLE, 'config': dict(config), 'seed': seed,
            'initial': initial, 'final': world.state,
            'entities': world.entities, 'events': [asdict(e) for e in world.history],
            'choices': choices, 'paragraphs': paragraphs, 'qa': qa}


def validate(pack, row):
    state = deepcopy(row['initial'])
    snapshots = {}
    w = pack.build_world(row['config'])
    previous = set()
    for event in row['events']:
        assert set(event['causes']) <= previous
        assert set(event['actors']) <= set(row['entities'])
        state = replay(state, [event])
        w.validate(state)
        snapshots[event['id']] = deepcopy(state)
        previous.add(event['id'])
    assert state == row['final'] and state['valley.ended'] is True
    assert isinstance(state['valley.outcome'], str) and state['valley.outcome']
    text = '\n\n'.join(p['text'] for p in row['paragraphs'])
    assert 450 <= len(text.split()) <= 900, f"Story length: {len(text.split())}; expected 450–900 words"
    qa = row['qa']
    assert len(qa) >= 6
    assert len({q['question'].casefold().strip() for q in qa}) == len(qa)
    assert len({q['answer'].casefold().strip() for q in qa}) == len(qa)
    for q in qa:
        assert len(q['answer'].split()) >= 14 and len(re.findall(r'[.!?](?:\s|$)', q['answer'])) >= 2
        assert q['facts'], 'Answers need evidence'
        for fact in q['facts']:
            assert snapshots[fact['event']][fact['key']] == fact['value'], q['question']
            assert any(fact['event'] in p['evidence'] and fact['key'] in p['reveals']
                       for p in row['paragraphs']), 'Question uses a fact not exposed by the prose'
    return len(text.split())


def evaluate(candidate):
    assert re.fullmatch('[a-z][a-z0-9_]*', candidate), 'Invalid candidate name'
    pack = importlib.import_module(f'microdrama.authoring_trial_20261024.{candidate}.pack')
    output = ROOT / candidate / 'output'
    output.mkdir(parents=True, exist_ok=True)
    rows, errors, summaries = [], [], []
    for index, config in enumerate(configurations()):
        for seed in range(5):
            try:
                row = produce(pack, config, seed)
                words = validate(pack, row)
                assert row == produce(pack, config, seed), 'Generation is nondeterministic'
                rows.append(row)
                summaries.append({'case': index, 'config': config, 'seed': seed,
                                  'outcome': row['final']['valley.outcome'], 'words': words,
                                  'state_hash': digest(row['final'])})
                if seed == 0:
                    (output/f'case{index}.json').write_text(json.dumps(row, indent=2, ensure_ascii=False)+'\n')
                    (output/f'case{index}.txt').write_text(row['title']+'\n\n'+'\n\n'.join(p['text'] for p in row['paragraphs'])+'\n')
            except Exception as exc:
                errors.append({'case': index, 'config': config, 'seed': seed, 'error': f'{type(exc).__name__}: {exc}'})
    outcomes = sorted({r['final']['valley.outcome'] for r in rows})
    if len(outcomes) < 2:
        errors.append({'error': 'Need at least two material outcomes'})
    # Input settings and an outcome name alone are not material consequences.
    witnesses = []
    for a, b in itertools.combinations([r for r in rows if r['seed'] == 0], 2):
        changed_inputs = [k for k in KEYS if a['config'][k] != b['config'][k]]
        if len(changed_inputs) != 1 or a['final']['valley.outcome'] == b['final']['valley.outcome']:
            continue
        differences = [k for k in a['final'] if k != 'valley.outcome' and
                       a['final'][k] != b['final'].get(k) and
                       (a['final'][k] != a['initial'].get(k) or b['final'].get(k) != b['initial'].get(k))]
        if differences:
            witnesses.append({'input': changed_inputs[0], 'a': a['config'], 'b': b['config'], 'changed_state': differences})
    if not witnesses:
        errors.append({'error': 'No matched material counterfactual'})
    report = {'candidate': candidate, 'passed': not errors, 'runs': len(rows), 'outcomes': outcomes,
              'errors': errors, 'counterfactuals': witnesses, 'cases': summaries,
              'mechanical_only': True,
              'pack_hash': digest((ROOT/candidate/'pack.py').read_text())}
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('candidate','passed','runs','outcomes','errors')}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', required=True)
    args = parser.parse_args()
    raise SystemExit(0 if evaluate(args.candidate)['passed'] else 1)
