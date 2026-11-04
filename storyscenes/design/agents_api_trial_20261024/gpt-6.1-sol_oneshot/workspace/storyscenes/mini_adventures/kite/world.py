"""Bounded scene composition, with atomic shared-engine actions."""
from copy import deepcopy
from dataclasses import dataclass, asdict
import argparse
import random

from storyscenes.runtime import StoryError
from storyscenes.mini_adventures.local_play import LocalPlay
from .prose import render


@dataclass(frozen=True, kw_only=True)
class Parameters:
    wind: int = 1
    gentle: bool = True
    frayed: bool = True
    mend: bool = True

    def __post_init__(self):
        if type(self.wind) is not int or not 0 <= self.wind <= 2:
            raise ValueError('wind must be an integer from 0 to 2')
        for key in ('gentle', 'frayed', 'mend'):
            if type(getattr(self, key)) is not bool:
                raise ValueError(key + ' must be boolean')


def parameters(seed):
    r = random.Random(seed)
    return Parameters(wind=r.randrange(3), gentle=r.choice((True, False)),
                      frayed=r.choice((True, False)), mend=r.choice((True, False)))


def initial(p):
    if not isinstance(p, Parameters):
        raise TypeError('Parameters required')
    return {'story.stage': 0, 'story.ended': False, 'story.outcome': '',
            'party.location': 'workshop', 'reel.owner': 'nan', 'reel.holder': 'nan',
            'reel.sound': not p.frayed, 'reel.wound': True, 'reel.checked': False,
            'kite.location': 'mara', 'kite.flew': False, 'kite.decorated': False,
            'mara.want': 'include_ivo', 'ivo.trust': False, 'ivo.role': 'undecided',
            'ivo.bird_seen': False, 'ivo.drawing': False, 'weather.wind': p.wind,
            'mara.gentle': p.gentle, 'mara.will_mend': p.mend}


def validate(s):
    if type(s['story.stage']) is not int or not 0 <= s['story.stage'] <= 6:
        raise StoryError('Invalid stage')
    if s['party.location'] not in ('workshop', 'step', 'field'):
        raise StoryError('Invalid place')
    if s['reel.owner'] != 'nan' or s['reel.holder'] not in ('nan', 'mara', 'ivo'):
        raise StoryError('The reel remains borrowed')
    if s['kite.flew'] and not (s['reel.sound'] and s['weather.wind'] == 1 and s['ivo.trust']):
        raise StoryError('Flight lacks a sound line, suitable wind or willing partner')
    if s['story.ended'] and not (s['party.location'] == 'workshop' and
            s['reel.holder'] == 'nan' and s['reel.sound'] and s['reel.wound'] and
            s['story.outcome']):
        raise StoryError('Unfinished return')


SCENES = ('welcome', 'borrow', 'invite', 'bird', 'window', 'field', 'return',
          'ending_air', 'ending_table')


def guard(scene_id, s):
    if scene_id not in SCENES:
        raise StoryError('Unknown scene: ' + scene_id)
    if s['story.ended']:
        return False
    stage = s['story.stage']
    if scene_id in ('bird', 'window'):
        return stage == 3 and not s[{'bird': 'ivo.bird_seen', 'window': 'kite.decorated'}[scene_id]]
    if scene_id.startswith('ending_'):
        return stage == 5 and scene_id == ('ending_air' if s['kite.flew'] else 'ending_table')
    return stage == {'welcome': 0, 'borrow': 1, 'invite': 2, 'field': 3, 'return': 4}[scene_id]


def play_scene(params, state, scene_id):
    if not guard(scene_id, state):
        raise StoryError('Incompatible scene: ' + scene_id)
    x = LocalPlay(state, actors=('mara', 'ivo', 'nan'), validate=validate)
    def act(name, req=None, **changes):
        x.act(name, requires=req, **changes)
    stage = state['story.stage']
    if scene_id == 'welcome':
        act('choose_company', {'mara.want': 'include_ivo'}, **{'story.stage': 1})
    elif scene_id == 'borrow':
        act('borrow_and_inspect', {'reel.holder': 'nan', 'party.location': 'workshop'},
            **{'reel.holder': 'mara', 'reel.checked': True})
        if not x.state['reel.sound'] and state['mara.will_mend']:
            act('cut_fray_and_retie', {'reel.checked': True}, **{'reel.sound': True})
        act('visit_step', **{'party.location': 'step', 'story.stage': 2})
    elif scene_id == 'invite':
        act('offer_quiet_role' if state['mara.gentle'] else 'call_for_a_launch',
            {'party.location': 'step'}, **{'ivo.trust': state['mara.gentle'],
            'ivo.role': 'reel' if state['mara.gentle'] else 'watcher', 'story.stage': 3})
    elif scene_id == 'bird':
        act('watch_sparrow', {'party.location': 'step'}, **{'ivo.bird_seen': True})
    elif scene_id == 'window':
        act('add_blue_window', {'party.location': 'step'}, **{'kite.decorated': True})
    elif scene_id == 'field':
        act('walk_to_lower_field', {'party.location': 'step'}, **{'party.location': 'field'})
        flight = state['reel.sound'] and state['weather.wind'] == 1 and state['ivo.trust']
        if flight:
            act('ivo_pays_out_line', {'reel.sound': True, 'ivo.trust': True, 'weather.wind': 1},
                **{'reel.holder': 'ivo', 'reel.wound': False, 'kite.flew': True})
        else:
            act('keep_kite_grounded', **{'ivo.role': 'observer'})
        act('finish_field_visit', **{'story.stage': 4})
    elif scene_id == 'return':
        if not x.state['reel.wound']:
            act('land_and_wind', {'party.location': 'field'}, **{'reel.wound': True})
        act('walk_back', **{'party.location': 'workshop'})
        if not x.state['reel.sound']:
            act('nan_and_mara_replace_frayed_end', {'reel.checked': True}, **{'reel.sound': True})
        act('return_useful_reel', {'reel.sound': True, 'reel.wound': True},
            **{'reel.holder': 'nan', 'story.stage': 5})
    else:
        if scene_id == 'ending_table':
            act('make_room_for_ivo_drawing', {'party.location': 'workshop'}, **{'ivo.drawing': True})
        act('close_afternoon', {'reel.holder': 'nan'}, **{'story.stage': 6,
            'story.ended': True, 'story.outcome': 'shared_flight' if state['kite.flew'] else 'shared_table',
            'mara.want': 'satisfied'})
    return {'id': scene_id, 'before': deepcopy(state), 'after': deepcopy(x.state),
            'events': deepcopy(x.events), 'text': render(scene_id, state, x.state)}


def replay(params, path):
    s = initial(params)
    episodes = []
    for sid in path:
        if sid in [e['id'] for e in episodes]:
            raise StoryError('Repeated scene')
        e = play_scene(params, s, sid)
        episodes.append(e)
        s = e['after']
    return episodes


def generate(seed=0, *, count=8, params=None):
    if type(count) is not int or count not in (7, 8):
        raise ValueError('Exactly seven or eight scenes required')
    p = parameters(seed) if params is None else params
    initial(p)
    rng = random.Random(seed)
    attempts = 0
    def search(s, path):
        nonlocal attempts
        if len(path) == count:
            return path if s['story.ended'] else None
        if s['story.ended']:
            return None
        choices = [sid for sid in SCENES if sid not in path and guard(sid, s)]
        rng.shuffle(choices)
        for sid in choices:
            attempts += 1
            if attempts > 1000:
                raise StoryError('Search budget exhausted')
            e = play_scene(p, s, sid)
            result = search(e['after'], path + [sid])
            if result is not None:
                return result
        return None
    path = search(initial(p), [])
    if path is None:
        raise StoryError('No route')
    episodes = replay(p, path)
    return {'seed': seed, 'parameters': asdict(p), 'scene_count': count, 'path': path,
            'episodes': episodes, 'story': '\n\n'.join(e['text'] for e in episodes),
            'final_state': deepcopy(episodes[-1]['after']), 'search_attempts': attempts}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    args = parser.parse_args()
    print(generate(args.seed, count=args.scenes)['story'])
