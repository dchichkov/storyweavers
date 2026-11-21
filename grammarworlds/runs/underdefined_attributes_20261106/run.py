"""Run the existing unordered bare-world actions through the joint sampler.

From the repository root:
  .venv/bin/python -m grammarworlds.runs.underdefined_attributes_20261106.run
No new operators, event sequence, ending, or prose edits are supplied.
"""
from dataclasses import asdict
import json
import math
from pathlib import Path
import random

from grammarworlds.underdefined_probe import initial_world, candidates, render, commit, PREMISE, GOAL
from grammarworlds.grammar import Derivation
from grammarworlds.world import Frame
from grammarworlds.storytelling.attribute_grammar import expand_attributes, candidate_attributes
from grammarworlds.storytelling.attribute_sampler import AttributeForest
from grammarworlds.storytelling.head_adapter import StoryHeads
from grammarworlds.storytelling.surface import detokenize
from grammarworlds.symbolic_heads.positions import Position, SymbolicRotary


def run(seed=7, steps=8):
    world, rng = initial_world(), random.Random(seed)
    initial = world.to_dict()
    heads = StoryHeads(world)
    traces, stream, scenes = [], [], []
    sentence = local = 0
    boundary = False
    rotary = SymbolicRotary()
    for index in range(steps):
        available = candidates(world)
        if not available:
            break
        before = world.to_dict()
        rows, attributes = [], []
        for kernel, frame in available:
            for words, p, rules, annotation in expand_attributes(render(world, frame).node):
                rows.append(Derivation(words, p/len(available), frame, rules))
                attributes.append(candidate_attributes(words, annotation, frame, world, kernel, before['entities']))
        assert before == world.to_dict()
        forest = AttributeForest(rows, {}, attributes)
        prefix, trace = (), []
        for _ in range(max(len(d.tokens) for d in forest.derivations)+1):
            p = heads.predict(forest, prefix, world, tense='past', available=available)
            forest.reconcile_word_weights(p)
            assert math.isclose(sum(c['probability'] for c in p['annotated_choices']), 1, abs_tol=1e-9)
            chosen = rng.choices(p['choices'], weights=[c['probability'] for c in p['choices']])[0]
            p.update(selected=chosen['word'], selected_probability=chosen['probability'])
            posterior = forest.observe(chosen['word'], p)
            p['selected_attributes'] = posterior
            trace.append(p)
            if chosen['word'] == '<END>':
                break
            word = chosen['word']
            if boundary and word not in {'”', '.', '!', '?'}:
                sentence += 1
                local, boundary = 0, False
            position = Position(f'underdefined:seed:{seed}', len(stream), sentence, local)
            stream.append(dict(token=word, position=asdict(position), rotary=rotary.encode(position),
                scene_index=index, candidates=[dict(probability=c['probability'],
                **forest.attribute_table[c['attributes']]) for c in posterior]))
            local += 1
            boundary = boundary or word in {'.', '!', '?'}
            prefix += (word,)
        else:
            raise AssertionError('word sampling did not finish')
        posterior = forest.event_posterior(prefix)
        frame = rng.choices(list(posterior), weights=list(posterior.values()))[0]
        prose = detokenize(prefix)
        record = commit(world, frame, prose)
        labels = set.intersection(*(set(d.rules) for d in forest.derivations if d.frame == frame and d.tokens == prefix))
        record.update(referents=sorted(r.split(':',1)[1] for r in labels if r.startswith('referent:')),
                      speakers=sorted(r.split(':',1)[1] for r in labels if r.startswith('dialogue.speaker:')),
                      narrated=True)
        traces.append(dict(frame=asdict(frame), attribute_table=forest.attribute_table, word_trace=trace))
        scenes.append(prose)
    final = world.to_dict()
    replayed = initial_world()
    for saved in final['history']:
        frame = Frame(**{**saved['frame'], 'cause_ids':tuple(saved['frame']['cause_ids'])})
        record = commit(replayed, frame, saved['sentence'])
        record.update({k:saved[k] for k in ('referents','speakers','narrated')})
    assert replayed.to_dict() == final
    metrics = dict(words=len(stream), generation_steps=sum(len(t['word_trace']) for t in traces),
        uncertain_token_steps=sum(len(t['candidates'])>1 for t in stream),
        word_choice_steps=sum(len(p['choices'])>1 for t in traces for p in t['word_trace']),
        head_changed_steps=sum(p.get('head_total_variation',0)>1e-10 for t in traces for p in t['word_trace']))
    return dict(seed=seed, premise=PREMISE, story=' '.join(scenes), metrics=metrics,
        stop_reason='step_limit' if len(traces)==steps else 'no_available_event',
        goal_reached=GOAL['desired_state'] in world.entities['book'].state,
        initial_world=initial, final_world=final, tokens=stream, trace=traces, replay_verified=True)


if __name__ == '__main__':
    output = Path(__file__).parent
    row = run()
    (output/'sample.json').write_text(json.dumps(row, indent=2)+'\n')
    (output/'sample.md').write_text('# Under-defined story with joint token attributes\n\n'+row['premise']+
        '\n\nSeed 7, eight events, existing heads on. No reroll or prose edits.\n\n'+row['story']+
        '\n\nGoal reached: '+str(row['goal_reached'])+'. Stop: '+row['stop_reason']+'. Physical replay verified.\n\n'+
        '```json\n'+json.dumps(row['metrics'], indent=2)+'\n```\n')
    print(row['story'])
    print(json.dumps(row['metrics']))
    print('Goal reached:', row['goal_reached'], '| stop:', row['stop_reason'])
