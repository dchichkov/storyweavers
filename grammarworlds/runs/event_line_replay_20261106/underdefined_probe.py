"""Bare-world baseline and an explicitly added, unordered shared-family adapter.

This is an experiment, not a new story pack. No repair operator, plot sequence,
ending, repetition penalty, source-story retrieval, or runtime model is added.
The adapter supplies role bindings which the current generator cannot discover.
"""
import argparse
from collections import Counter
from dataclasses import asdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
from types import SimpleNamespace

from .grammar import Derivation, Forest, expand
from .world import Entity, Fact, Frame, World, kernel
from .storytelling.continuations import ExpandedLanguage
from .storytelling.head_adapter import StoryHeads
from .storytelling.operations import Change, can_transfer, committed
from .storytelling.runtime import build_forest
from .storytelling.surface import scene, detokenize

GOAL = dict(actor='ada', action='repair', patient='book', desired_state='repaired')
PREMISE = ('Ada and Omar are in a garden. Ada holds a torn book and wants to repair it. '
           'Tape is on a reachable bench in the garden. Both people can carry objects '
           'and offer help; Omar is willing to help. No events or ending are supplied.')


def initial_world():
    return World('underdefined', {
        'ada': Entity('ada', 'Ada', 'person', 'garden', pronoun='she',
                      properties={'can_hold', 'can_help'}, memes={'Desire': .8, 'Fear': .2, 'Trust': .6}),
        'omar': Entity('omar', 'Omar', 'person', 'garden', pronoun='he',
                       properties={'can_hold', 'can_help'}, memes={'Care': .8, 'Trust': .6}),
        'book': Entity('book', 'book', 'object', 'ada', properties={'portable'}, state={'torn'}),
        'tape': Entity('tape', 'tape', 'tool', 'bench', properties={'portable', 'repair'}),
        'bench': Entity('bench', 'bench', 'place', 'garden', properties={'reachable'}),
    }, hero='ada', helper='omar', target='book', tool='tape', setting='garden', facts={
        'problem': Fact('problem', 'The book is torn.', ('problem', 'goal')),
        'helper_available': Fact('helper_available', 'Omar is nearby and willing to help.', ('helper', 'trust')),
    })


def strict_baseline():
    results = []
    for attention in (False, True):
        w = initial_world()
        before = w.to_dict()
        # Give the existing builder a pack with literally no story/event part.
        pack = SimpleNamespace(candidates=lambda world: [])
        try:
            build_forest(pack, w, attention=attention, continuations='expanded')
        except ValueError as error:
            results.append(dict(attention=attention, story='', error=str(error),
                                token_steps=0, candidate_events=0))
        else:
            raise AssertionError('Bare-world behavior changed; inspect the new result')
        assert w.to_dict() == before
    return results


def candidates(w):
    """NEW adapter: bind existing families to physical roles, with no ordering.

    Equal mass per legal binding is a probe convention, not a learned policy.
    No event-query preferences are added; attention below is existing word heads.
    """
    rows = []
    people = [i for i,e in w.entities.items() if e.kind == 'person']
    actor, patient = GOAL['actor'], GOAL['patient']
    if actor in people and patient in w.entities:
        rows.append((kernel('intent'), Frame('intent', actor, patient)))
    for actor in people:
        person = w.entities[actor]
        for listener in people:
            if actor != listener and person.location == w.entities[listener].location:
                if 'can_help' in person.properties:
                    rows.append((kernel('offer'), Frame('offer', actor, listener)))
                for item in w.entities:
                    if can_transfer(w, item, actor, listener):
                        rows.append((kernel('transfer'), Frame('transfer', actor, item, destination=listener)))
        if 'can_hold' not in person.properties:
            continue
        for item,e in w.entities.items():
            source = w.entities.get(e.location)
            if ('portable' in e.properties and source and source.kind == 'place'
                    and 'reachable' in source.properties and source.location == person.location):
                rows.append((kernel('fetch'), Frame('fetch', actor, item, destination=actor)))
    return rows


@committed(candidates, {'fetch': (Change('@patient', '@actor'),),
                        'transfer': (Change('@patient', '@destination'),)})
def commit(w, frame):
    pass


def render(w, frame):
    """Bind meanings to existing families; no authored sentence strings."""
    g = ExpandedLanguage(w)
    if frame.kind == 'intent':
        return scene(g.say_intent(frame.actor, 'want', g.v(GOAL['action'], g.ref(frame.patient))))
    if frame.kind == 'offer':
        from .portable.nouns import pronoun
        return scene(g.offer(frame.actor, g.v('help', pronoun('you')), listener=frame.patient))
    if frame.kind == 'transfer':
        return scene(g.transfer(frame.actor, g.ref(frame.destination), g.ref(frame.patient)))
    if frame.kind == 'fetch':
        return g.fetch_scene(frame.actor, frame.patient, w.entities[frame.patient].location)
    raise ValueError(frame.kind)


def generate(seed, *, heads=True, steps=8, strength=1):
    w, rng = initial_world(), random.Random(seed)
    initial = w.to_dict()
    adapter = StoryHeads(w, strength=strength) if heads else None
    traces, counts, texts = [], Counter(), []
    for _ in range(steps):
        available = candidates(w)
        if not available:
            break
        before = w.to_dict()
        derivations = []
        for _, frame in available:
            for tokens, probability, rules in expand(render(w, frame).node):
                derivations.append(Derivation(tokens, probability/len(available), frame, rules))
        assert before == w.to_dict()
        forest = Forest(derivations, {})
        tokens, trace = (), []
        for _ in range(max(len(d.tokens) for d in forest.derivations)+1):
            prediction = (adapter.predict(forest, tokens, w, tense='past', available=available)
                          if adapter else forest.predict(tokens))
            choices = prediction['choices']
            assert math.isclose(sum(c['probability'] for c in choices), 1)
            assert all(c['probability'] > 0 for c in choices)
            chosen = rng.choices(choices, weights=[c['probability'] for c in choices])[0]
            prediction.update(selected=chosen['word'], selected_probability=chosen['probability'])
            trace.append(prediction)
            counts['token_steps'] += 1
            counts['choice_steps'] += len(choices) > 1
            counts['four_way_steps'] += len(choices) >= 4
            counts['changed_distribution_steps'] += prediction.get('head_total_variation', 0) > 1e-10
            for h in prediction.get('symbolic_heads', []):
                if h['status'] == 'active': counts[h['head_id']+'_active'] += 1
            if chosen['word'] == '<END>':
                break
            tokens += (chosen['word'],)
        else:
            raise AssertionError('Unfinished word sampling')
        posterior = forest.event_posterior(tokens)
        frame = rng.choices(list(posterior), weights=list(posterior.values()))[0]
        text = detokenize(tokens)
        record = commit(w, frame, text)
        labels = set.intersection(*(set(d.rules) for d in forest.derivations
                                    if d.frame == frame and d.tokens == tokens))
        record.update(referents=sorted(x.split(':',1)[1] for x in labels if x.startswith('referent:')),
                      speakers=sorted(x.split(':',1)[1] for x in labels if x.startswith('dialogue.speaker:')),
                      narrated=True)
        traces.append(dict(frame=asdict(frame), word_trace=trace))
        texts.append(text)
    assert 'torn' in w.entities['book'].state
    assert not w.finished
    return dict(seed=seed, heads=heads, story=' '.join(texts), metrics=dict(counts),
                initial_world=initial, final_world=w.to_dict(), trace=traces,
                goal_reached=GOAL['desired_state'] in w.entities['book'].state,
                stop_reason='step_limit' if len(traces)==steps else 'no_available_event')


def run(out, count=20, steps=8):
    if count < 1 or steps < 1:
        raise ValueError('count and steps must be positive')
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    literal = strict_baseline()
    rows = [generate(seed, heads=heads, steps=steps) for seed in range(count) for heads in (False, True)]
    # Replay every probe independently using physical candidate validation.
    for row in rows:
        w = initial_world()
        for event in row['final_world']['history']:
            frame = Frame(**{**event['frame'], 'cause_ids':tuple(event['frame']['cause_ids'])})
            record = commit(w, frame, event['sentence'])
            for key in ('referents', 'speakers', 'narrated'): record[key] = event[key]
        assert w.to_dict() == row['final_world']
    zero = generate(0, heads=True, strength=0, steps=steps)
    assert zero['story'] == rows[0]['story'] and zero['final_world'] == rows[0]['final_world']
    summary = {}
    for heads in (False, True):
        subset = [r for r in rows if r['heads']==heads]
        counts = Counter()
        for row in subset: counts.update(row['metrics'])
        summary['heads_on' if heads else 'heads_off'] = dict(counts,
            runs=len(subset), distinct_texts=len({r['story'] for r in subset}),
            goals_reached=sum(r['goal_reached'] for r in subset),
            choice_fraction=counts['choice_steps']/counts['token_steps'])
    summary['matched_texts_changed'] = sum(rows[i]['story']!=rows[i+1]['story'] for i in range(0,len(rows),2))
    summary['literal_baseline'] = literal
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'input.json').write_text(json.dumps(dict(premise=PREMISE, goal=GOAL, world=initial_world().to_dict()),indent=2)+'\n')
    with gzip.open(out/'traces.jsonl.gz','wt') as sink:
        for row in rows: sink.write(json.dumps(row)+'\n')
    lines = ['# Underdefined world: raw samples', '', PREMISE, '',
        'Literal current runtime: empty output; `no available event` with attention off/on.', '',
        'The samples below use the NEW unordered role-binding adapter and existing shared grammar/word heads. '
        'They are eight-event fragments, not completed stories. Seeds 0–4 selected before generation. '
        'No reroll, filtering, ending or prose repair.', '']
    for row in rows:
        if row['seed'] < 5:
            lines += [f"## Seed {row['seed']}, heads {'on' if row['heads'] else 'off'}",'',row['story'],'']
    (out/'samples.md').write_text('\n'.join(lines))
    root = Path(__file__).resolve().parent
    sources = [Path(__file__)] + list((root/'storytelling').glob('*.py')) + list((root/'storytelling').glob('*.json'))
    sources += list((root/'portable').rglob('*.py')) + list((root/'portable/lexicon').glob('*.json'))
    sources += list((root/'symbolic_heads').rglob('*.py')) + list((root/'symbolic_heads/data').glob('*.json'))
    sources += [root/'grammar.py', root/'world.py']
    (out/'manifest.json').write_text(json.dumps(dict(count=count, steps=steps,
        source_sha256={str(p.relative_to(root.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2)+'\n')
    (out/'probe_source.py').write_text(Path(__file__).read_text())
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--count', type=int, default=20)
    parser.add_argument('--steps', type=int, default=8)
    parser.add_argument('--line', type=Path, help='Optional world/template/bindings JSON for guarded local-line replay')
    args = parser.parse_args()
    if args.line:
        from .event_line_replay import run_file
        run_file(args.line, args.out, args.count, args.steps)
    else:
        run(args.out, args.count, args.steps)
