"""Offline, bounded mini-adventure about a borrowed net and a toy boat."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
import random

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError

from .prose import render


@dataclass(frozen=True, kw_only=True)
class Parameters:
    net_reach_cm: int = 180
    boat_distance_cm: int = 125
    net_mesh: str = 'intact'
    wind: str = 'calm'
    weeds: bool = False

    def __post_init__(self):
        for name, low, high in (('net_reach_cm', 60, 240), ('boat_distance_cm', 60, 240)):
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f'{name} must be an integer in [{low}, {high}]')
        if self.net_mesh not in ('intact', 'torn') or not isinstance(self.net_mesh, str):
            raise ValueError('net_mesh must be intact or torn')
        if self.wind not in ('calm', 'breezy', 'gusty') or not isinstance(self.wind, str):
            raise ValueError('wind must be calm, breezy, or gusty')
        if type(self.weeds) is not bool:
            raise ValueError('weeds must be boolean')


def _check_seed(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')


def parameters(seed):
    _check_seed(seed)
    rng = random.Random(seed)
    return Parameters(
        net_reach_cm=rng.choice((105, 145, 190, 215)),
        boat_distance_cm=rng.choice((95, 130, 165, 205)),
        net_mesh=rng.choice(('intact', 'intact', 'torn')),
        wind=rng.choice(('calm', 'breezy', 'gusty')),
        weeds=rng.choice((False, True)),
    )


_STATE_TYPES = {
    'story.spotted': bool, 'story.ended': bool, 'story.outcome': str,
    'mara.motive': str, 'jules.motive': str,
    'mara.place': str, 'jules.place': str, 'mara.position': str, 'jules.position': str,
    'mara.promised_bank': bool, 'jules.promised_bank': bool, 'friend.mood': str,
    'boat.owner': str, 'boat.location': str, 'boat.stuck': bool, 'boat.seen': bool,
    'boat.story_shared': bool, 'boat.usable': bool, 'boat.distance_cm': int,
    'boat.near_net': bool, 'boat.returned_to_jules': bool,
    'pond.weeds': bool, 'pond.wind': str, 'pond.sightline_checked': bool,
    'pond.gust_observed': bool, 'pond.wind_window': bool, 'reed.gap_seen': bool,
    'bank.safe_setup': bool,
    'net.owner': str, 'net.location': str, 'net.available': bool, 'net.borrowed': bool,
    'net.returned': bool, 'net.reach_cm': int, 'net.mesh': str, 'net.mesh_checked': bool,
    'net.in_water': bool, 'net.snagged': bool, 'net.angle': str, 'net.used_for': str,
    'attempt.done': bool, 'attempt.result': str, 'ending.drawing_done': bool,
}


def initial(params):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    state = {
        'story.spotted': False, 'story.ended': False, 'story.outcome': '',
        'mara.motive': 'help Jules without making the pond more dangerous',
        'jules.motive': 'get his grandfather’s little boat back',
        'mara.place': 'bank', 'jules.place': 'bank',
        'mara.position': 'standing', 'jules.position': 'standing',
        'mara.promised_bank': False, 'jules.promised_bank': False,
        'friend.mood': 'calm',
        'boat.owner': 'Jules', 'boat.location': 'pond', 'boat.stuck': True,
        'boat.seen': False, 'boat.story_shared': False, 'boat.usable': False,
        'boat.distance_cm': params.boat_distance_cm, 'boat.near_net': False,
        'boat.returned_to_jules': False,
        'pond.weeds': params.weeds, 'pond.wind': params.wind,
        'pond.sightline_checked': False, 'pond.gust_observed': False,
        'pond.wind_window': False, 'reed.gap_seen': False, 'bank.safe_setup': False,
        'net.owner': 'keeper', 'net.location': 'shed', 'net.available': True,
        'net.borrowed': False, 'net.returned': False,
        'net.reach_cm': params.net_reach_cm, 'net.mesh': params.net_mesh,
        'net.mesh_checked': False, 'net.in_water': False, 'net.snagged': False,
        'net.angle': 'unset', 'net.used_for': 'unused',
        'attempt.done': False, 'attempt.result': 'pending', 'ending.drawing_done': False,
    }
    validate(state)
    return state


def validate(state):
    if type(state) is not dict or set(state) != set(_STATE_TYPES):
        raise StoryError('State keys do not match this scenario')
    for key, expected in _STATE_TYPES.items():
        if type(state[key]) is not expected:
            raise StoryError(f'Invalid type for {key}')
    for key in ('boat.distance_cm', 'net.reach_cm'):
        if not 60 <= state[key] <= 240:
            raise StoryError(f'Invalid range for {key}')
    if state['net.mesh'] not in ('intact', 'torn'):
        raise StoryError('Unknown net mesh')
    if state['pond.wind'] not in ('calm', 'breezy', 'gusty'):
        raise StoryError('Unknown wind state')
    if state['mara.place'] != 'bank' or state['jules.place'] != 'bank':
        raise StoryError('Both children must remain on the bank')
    if state['mara.position'] not in ('standing', 'kneeling') or state['jules.position'] not in ('standing', 'behind_line'):
        raise StoryError('Unknown bank position')
    if state['bank.safe_setup'] != (state['mara.position'] == 'kneeling' and state['jules.position'] == 'behind_line'):
        raise StoryError('Bank setup and child positions disagree')
    if state['bank.safe_setup'] != (state['mara.promised_bank'] and state['jules.promised_bank']):
        raise StoryError('The safety agreement and setup disagree')
    if state['reed.gap_seen'] and not (state['pond.weeds'] and state['pond.sightline_checked']):
        raise StoryError('A reed gap can only be seen after checking weedy water')
    if state['pond.wind_window'] and state['pond.wind'] != 'breezy':
        raise StoryError('A lull was recorded in the wrong wind')
    if state['story.spotted'] != state['boat.seen']:
        raise StoryError('The boat sighting is inconsistent')
    if state['friend.mood'] not in ('calm', 'worried', 'hopeful', 'relieved', 'pleased', 'settled'):
        raise StoryError('Unknown friend mood')
    if state['net.owner'] == 'keeper':
        if state['net.location'] != 'shed' or state['net.borrowed'] or not state['net.available']:
            raise StoryError('Keeper custody is inconsistent')
    elif state['net.owner'] == 'Mara':
        if state['net.location'] != 'bank' or not state['net.borrowed'] or state['net.available']:
            raise StoryError('Borrowed net custody is inconsistent')
    else:
        raise StoryError('Unknown net owner')
    if state['net.returned'] and (state['net.owner'] != 'keeper' or not state['attempt.done']):
        raise StoryError('The net cannot be returned before it has been used')
    if state['net.snagged'] and not (state['net.in_water'] and state['pond.weeds']):
        raise StoryError('A snagged net must be in the weeds')
    if state['net.in_water'] and not (state['net.borrowed'] and state['bank.safe_setup']):
        raise StoryError('Only the safely positioned borrower may use the net')
    if state['net.angle'] not in ('unset', 'open', 'gap', 'wrong_edge', 'short'):
        raise StoryError('Unknown net angle')
    if state['net.used_for'] not in ('unused', 'retrieval', 'weed_test', 'mesh_test', 'reach_check', 'safety_check'):
        raise StoryError('Unknown net use')
    if state['attempt.result'] not in ('pending', 'held', 'weed_snag', 'mesh_slip', 'retrieved',
                                       'weeds', 'mesh_torn', 'out_of_reach', 'gust'):
        raise StoryError('Unknown attempt result')
    if state['attempt.done'] == (state['attempt.result'] in ('pending', 'held', 'weed_snag', 'mesh_slip')):
        raise StoryError('Attempt completion and result disagree')
    if state['attempt.done'] and not (state['bank.safe_setup'] and state['net.mesh_checked']):
        raise StoryError('An attempt requires a checked net and safe bank setup')
    if state['boat.location'] not in ('pond', 'net', 'bank', 'friend'):
        raise StoryError('Unknown boat location')
    if state['boat.stuck'] != (state['boat.location'] == 'pond'):
        raise StoryError('Boat location and snag state disagree')
    if state['boat.location'] == 'net' and not (state['net.in_water'] and state['attempt.result'] == 'held'):
        raise StoryError('The boat is not held by the net')
    if state['net.in_water'] and state['boat.location'] == 'net' and state['attempt.result'] != 'held':
        raise StoryError('Only a successful catch can hold the boat')
    if state['boat.location'] == 'pond' and state['boat.usable']:
        raise StoryError('A boat still in the pond is not ready to sail')
    if state['boat.location'] in ('net', 'pond') and state['boat.usable']:
        raise StoryError('The boat is not usable before it reaches the bank')
    if state['boat.location'] == 'bank' and not (state['attempt.done'] and state['attempt.result'] == 'retrieved' and state['boat.usable']):
        raise StoryError('A recovered boat must have been lifted safely')
    if state['attempt.done'] and state['attempt.result'] == 'retrieved' and state['boat.location'] not in ('bank', 'friend'):
        raise StoryError('A retrieved boat must remain out of the pond')
    if state['boat.near_net'] and not (state['net.mesh'] == 'torn' and state['attempt.result'] in ('mesh_slip', 'mesh_torn')):
        raise StoryError('The close pass belongs to the torn-mesh attempt')
    if state['boat.returned_to_jules'] != (state['boat.location'] == 'friend'):
        raise StoryError('Boat hand-back and location disagree')
    if state['boat.location'] == 'friend' and not state['boat.usable']:
        raise StoryError('A returned boat must be usable')
    if state['story.ended']:
        if state['story.outcome'] == 'boat_recovered':
            if not (state['boat.location'] == 'friend' and state['net.returned'] and not state['ending.drawing_done']):
                raise StoryError('Recovered ending is incomplete')
        elif state['story.outcome'] == 'boat_left_in_pond':
            if not (state['boat.location'] == 'pond' and state['net.returned'] and state['ending.drawing_done']):
                raise StoryError('Safe-loss ending is incomplete')
        else:
            raise StoryError('An ended story needs a recognized outcome')
    elif state['story.outcome'] or state['ending.drawing_done'] or state['boat.location'] == 'friend':
        raise StoryError('An unfinished story contains ending effects')
    return True


SCENES = (
    'spot_boat', 'remember_boat', 'read_reeds', 'borrow_net', 'bank_plan',
    'cast_net', 'return_net', 'ending_boat_home', 'ending_boat_left',
)


def guard(scene_id, state):
    validate(state)
    if scene_id not in SCENES:
        raise StoryError(f'Unknown scene: {scene_id}')
    if state['story.ended']:
        return False
    if scene_id == 'spot_boat':
        return not state['story.spotted']
    if scene_id == 'remember_boat':
        return state['story.spotted'] and not state['boat.story_shared'] and not state['net.borrowed']
    if scene_id == 'read_reeds':
        return state['story.spotted'] and not state['pond.sightline_checked'] and not state['net.borrowed']
    if scene_id == 'borrow_net':
        return state['story.spotted'] and not state['net.borrowed'] and not state['net.returned'] and state['net.available']
    if scene_id == 'bank_plan':
        return state['net.borrowed'] and state['net.mesh_checked'] and not state['bank.safe_setup']
    if scene_id == 'cast_net':
        return state['bank.safe_setup'] and state['net.borrowed'] and state['net.mesh_checked'] and not state['attempt.done']
    if scene_id == 'return_net':
        return state['attempt.done'] and state['net.borrowed'] and not state['net.in_water']
    if scene_id == 'ending_boat_home':
        return state['net.returned'] and state['boat.location'] == 'bank'
    if scene_id == 'ending_boat_left':
        return state['net.returned'] and state['boat.location'] == 'pond'
    return False


class _Play:
    def __init__(self, state):
        self.local = LocalPlay(state, actors=('Mara', 'Jules'), validate=validate)

    @property
    def state(self):
        return self.local.state

    @property
    def events(self):
        return self.local.events

    def act(self, name, requires=None, **changes):
        self.local.act(name, requires or {}, **changes)


def _failure_reason(state):
    if state['pond.wind'] == 'gusty':
        return 'gust'
    if state['net.reach_cm'] < state['boat.distance_cm'] + 10:
        return 'out_of_reach'
    if state['net.mesh'] != 'intact':
        return 'mesh_torn'
    if state['pond.weeds'] and not state['reed.gap_seen']:
        return 'weeds'
    return None


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    validate(state)
    if (state['net.reach_cm'], state['boat.distance_cm'], state['net.mesh'], state['pond.wind'], state['pond.weeds']) != (
        params.net_reach_cm, params.boat_distance_cm, params.net_mesh, params.wind, params.weeds
    ):
        raise StoryError('Parameters do not match the embedded world')
    if not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    before = deepcopy(state)
    x = _Play(state)
    s = x.state

    if scene_id == 'spot_boat':
        x.act('notice_stuck_boat', {'mara.place': 'bank', 'jules.place': 'bank', 'boat.location': 'pond'},
              **{'story.spotted': True, 'boat.seen': True, 'friend.mood': 'worried'})
    elif scene_id == 'remember_boat':
        x.act('share_boat_memory', {'story.spotted': True, 'boat.owner': 'Jules'},
              **{'boat.story_shared': True, 'friend.mood': 'hopeful'})
    elif scene_id == 'read_reeds':
        if s['pond.weeds']:
            x.act('find_gap_between_reeds', {'pond.weeds': True, 'pond.sightline_checked': False},
                  **{'pond.sightline_checked': True, 'reed.gap_seen': True})
        else:
            x.act('check_clear_sightline', {'pond.weeds': False, 'pond.sightline_checked': False},
                  **{'pond.sightline_checked': True})
    elif scene_id == 'borrow_net':
        x.act('keeper_lends_long_net', {'story.spotted': True, 'net.owner': 'keeper', 'net.available': True},
              **{'net.owner': 'Mara', 'net.location': 'bank', 'net.available': False, 'net.borrowed': True})
        x.act('inspect_net_mesh', {'net.owner': 'Mara', 'net.borrowed': True},
              **{'net.mesh_checked': True})
    elif scene_id == 'bank_plan':
        x.act('mark_safe_edge', {'mara.place': 'bank', 'jules.place': 'bank', 'net.owner': 'Mara'},
              **{'bank.safe_setup': True, 'mara.position': 'kneeling', 'jules.position': 'behind_line'})
        x.act('agree_no_wading', {'bank.safe_setup': True},
              **{'mara.promised_bank': True, 'jules.promised_bank': True})
    elif scene_id == 'cast_net':
        reason = _failure_reason(s)
        if reason is None:
            if s['pond.wind'] == 'breezy':
                x.act('wait_for_a_lull', {'pond.wind': 'breezy', 'pond.wind_window': False},
                      **{'pond.wind_window': True})
            angle = 'gap' if s['pond.weeds'] else 'open'
            x.act('choose_clear_approach', {'bank.safe_setup': True}, **{'net.angle': angle})
            req = {
                'bank.safe_setup': True, 'mara.promised_bank': True, 'jules.promised_bank': True,
                'net.borrowed': True, 'net.mesh_checked': True, 'net.in_water': False,
                'net.reach_cm': s['net.reach_cm'], 'boat.distance_cm': s['boat.distance_cm'],
                'net.mesh': 'intact', 'pond.wind': s['pond.wind'], 'pond.weeds': s['pond.weeds'],
                'reed.gap_seen': s['reed.gap_seen'], 'net.angle': angle,
            }
            if s['pond.wind'] == 'breezy':
                req['pond.wind_window'] = True
            x.act('lower_hoop_under_boat', req,
                  **{'net.in_water': True, 'net.used_for': 'retrieval', 'boat.location': 'net',
                     'boat.stuck': False, 'attempt.result': 'held'})
            x.act('lift_boat_from_bank', {'boat.location': 'net', 'net.in_water': True,
                                          'mara.place': 'bank', 'jules.place': 'bank'},
                  **{'boat.location': 'bank', 'net.in_water': False, 'attempt.done': True,
                     'attempt.result': 'retrieved', 'boat.usable': True, 'friend.mood': 'relieved'})
        elif reason == 'gust':
            x.act('observe_gust_and_hold_back', {'pond.wind': 'gusty', 'bank.safe_setup': True},
                  **{'pond.gust_observed': True, 'net.used_for': 'safety_check',
                     'attempt.done': True, 'attempt.result': 'gust'})
        elif reason == 'out_of_reach':
            x.act('measure_shortfall_from_bank', {'bank.safe_setup': True,
                                                  'net.reach_cm': s['net.reach_cm'],
                                                  'boat.distance_cm': s['boat.distance_cm']},
                  **{'net.angle': 'short', 'net.used_for': 'reach_check',
                     'attempt.done': True, 'attempt.result': 'out_of_reach'})
        elif reason == 'mesh_torn':
            x.act('aim_at_boat', {'bank.safe_setup': True, 'net.mesh': 'torn'},
                  **{'net.angle': 'open'})
            x.act('test_torn_mesh', {'net.borrowed': True, 'net.mesh_checked': True,
                                     'bank.safe_setup': True},
                  **{'net.in_water': True, 'net.used_for': 'mesh_test', 'boat.near_net': True,
                     'attempt.result': 'mesh_slip'})
            x.act('draw_net_back_safely', {'net.in_water': True, 'boat.location': 'pond'},
                  **{'net.in_water': False, 'attempt.done': True, 'attempt.result': 'mesh_torn'})
        else:
            x.act('aim_at_wrong_reed_edge', {'pond.weeds': True, 'reed.gap_seen': False,
                                             'bank.safe_setup': True},
                  **{'net.angle': 'wrong_edge'})
            x.act('catch_reeds_not_boat', {'net.borrowed': True, 'bank.safe_setup': True,
                                           'pond.weeds': True, 'reed.gap_seen': False},
                  **{'net.in_water': True, 'net.snagged': True, 'net.used_for': 'weed_test',
                     'attempt.result': 'weed_snag'})
            x.act('ease_empty_net_free', {'net.in_water': True, 'net.snagged': True,
                                          'mara.place': 'bank', 'jules.place': 'bank'},
                  **{'net.in_water': False, 'net.snagged': False, 'attempt.done': True,
                     'attempt.result': 'weeds'})
    elif scene_id == 'return_net':
        x.act('return_useful_net_to_keeper', {'net.owner': 'Mara', 'net.borrowed': True,
                                              'attempt.done': True, 'net.in_water': False},
              **{'net.owner': 'keeper', 'net.location': 'shed', 'net.available': True,
                 'net.borrowed': False, 'net.returned': True})
    elif scene_id == 'ending_boat_home':
        x.act('hand_boat_back_to_jules', {'boat.location': 'bank', 'net.returned': True},
              **{'boat.location': 'friend', 'boat.returned_to_jules': True,
                 'friend.mood': 'pleased', 'story.ended': True, 'story.outcome': 'boat_recovered'})
    else:
        x.act('draw_the_boat_together_on_dry_path', {'boat.location': 'pond', 'net.returned': True},
              **{'ending.drawing_done': True, 'friend.mood': 'settled',
                 'story.ended': True, 'story.outcome': 'boat_left_in_pond'})

    after = deepcopy(x.state)
    text = render(scene_id, params, before, after)
    return {'id': scene_id, 'before': before, 'after': after,
            'events': deepcopy(x.events), 'text': text}


def _core_remaining(state):
    return sum((
        not state['story.spotted'],
        not state['net.borrowed'] and not state['net.returned'],
        not state['bank.safe_setup'],
        not state['attempt.done'],
        not state['net.returned'],
        not state['story.ended'],
    ))


def generate(seed=0, *, count=8, params=None):
    _check_seed(seed)
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    p = parameters(seed) if params is None else params
    if not isinstance(p, Parameters):
        raise TypeError('params must be a Parameters instance')
    rng = random.Random(seed)
    attempts = 0
    limit = 10000

    def search(state, episodes):
        nonlocal attempts
        remaining = count - len(episodes)
        if remaining < _core_remaining(state):
            return None
        if remaining == 0:
            return episodes if state['story.ended'] else None
        if state['story.ended']:
            return None
        choices = [scene_id for scene_id in SCENES
                   if scene_id not in {ep['id'] for ep in episodes} and guard(scene_id, state)]
        rng.shuffle(choices)
        for scene_id in choices:
            if scene_id.startswith('ending_') and remaining != 1:
                continue
            attempts += 1
            if attempts > limit:
                raise StoryError(f'Scene search budget exhausted ({limit} attempts)')
            episode = play_scene(p, state, scene_id)
            answer = search(episode['after'], episodes + (episode,))
            if answer is not None:
                return answer
        return None

    episodes = search(initial(p), ())
    if episodes is None:
        raise StoryError('No compatible complete route at the requested length')
    episode_rows = [deepcopy(ep) for ep in episodes]
    return {
        'seed': seed,
        'parameters': asdict(p),
        'scene_count': count,
        'path': [ep['id'] for ep in episode_rows],
        'story': '\n\n'.join(ep['text'] for ep in episode_rows),
        'episodes': episode_rows,
        'final_state': deepcopy(episode_rows[-1]['after']),
        'search_attempts': attempts,
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    if isinstance(path, (str, bytes)):
        raise TypeError('path must be a sequence of scene IDs')
    state = initial(params)
    episodes = []
    seen = set()
    for scene_id in path:
        if scene_id in seen:
            raise StoryError('A scene cannot be repeated')
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode['after']
        seen.add(scene_id)
    return episodes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    parser.add_argument('--params', help='JSON object overriding seeded Parameters')
    args = parser.parse_args()
    try:
        overrides = json.loads(args.params) if args.params else {}
        if not isinstance(overrides, dict):
            raise ValueError('--params must be a JSON object')
        values = asdict(parameters(args.seed))
        values.update(overrides)
        p = Parameters(**values)
        print(generate(args.seed, count=args.scenes, params=p)['story'])
    except (ValueError, TypeError, StoryError, json.JSONDecodeError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
