'''Bounded, replayable woodland adventure using atomic LocalPlay actions.'''
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
    compass_drift: int = 0
    shortcut_open: bool = True
    rain: bool = False
    puddle_depth: int = 1
    pace_gap: int = 2
    pool_window: int = 65

    def __post_init__(self):
        if type(self.compass_drift) is not int or self.compass_drift not in (0, 1):
            raise ValueError('compass_drift must be the integer 0 or 1')
        for name in ('shortcut_open', 'rain'):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f'{name} must be boolean')
        for name, low, high in (('puddle_depth', 1, 3), ('pace_gap', 1, 3),
                                ('pool_window', 30, 90)):
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f'{name} must be an integer in [{low}, {high}]')


SCENES = (
    'borrow_compass', 'fern_vignette', 'lace_vignette', 'route_choice',
    'puddle_cross', 'ridge_walk', 'discovery', 'ending_pool', 'ending_shelter',
)

_KEYS = (
    'story.location', 'story.route', 'story.minutes', 'story.discovery',
    'story.ended', 'story.outcome', 'friend.location', 'friend.heel_supported',
    'friend.heel_sore', 'friend.knows_stream', 'friend.included', 'friend.trust',
    'friend.boots_muddy', 'lead.location', 'trail.fern_seen', 'trail.rain',
    'trail.puddle_depth', 'trail.shortcut_open', 'trail.pace_gap', 'trail.pool_window',
    'compass.owner', 'compass.holder', 'compass.borrowed', 'compass.returned',
    'compass.checked', 'compass.check_count', 'compass.drift', 'compass.calibrated',
    'compass.calibration_source', 'compass.use_count', 'compass.useful_reported',
)

_TYPES = {
    'story.location': str, 'story.route': str, 'story.minutes': int,
    'story.discovery': str, 'story.ended': bool, 'story.outcome': str,
    'friend.location': str, 'friend.heel_supported': bool, 'friend.heel_sore': bool,
    'friend.knows_stream': bool, 'friend.included': bool, 'friend.trust': int,
    'friend.boots_muddy': bool, 'lead.location': str, 'trail.fern_seen': bool,
    'trail.rain': bool, 'trail.puddle_depth': int, 'trail.shortcut_open': bool,
    'trail.pace_gap': int, 'trail.pool_window': int, 'compass.owner': str,
    'compass.holder': str, 'compass.borrowed': bool, 'compass.returned': bool,
    'compass.checked': bool, 'compass.check_count': int, 'compass.drift': int,
    'compass.calibrated': bool, 'compass.calibration_source': str,
    'compass.use_count': int, 'compass.useful_reported': bool,
}

_PARAMETER_KEYS = {
    'compass_drift': 'compass.drift', 'shortcut_open': 'trail.shortcut_open',
    'rain': 'trail.rain', 'puddle_depth': 'trail.puddle_depth',
    'pace_gap': 'trail.pace_gap', 'pool_window': 'trail.pool_window',
}


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        compass_drift=rng.choice((0, 1)),
        shortcut_open=rng.choice((True, False)),
        rain=rng.choice((False, False, True)),
        puddle_depth=rng.choice((1, 2, 3)),
        pace_gap=rng.choice((1, 2, 3)),
        pool_window=rng.choice((38, 48, 58, 72)),
    )


def initial(params):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    state = {
        'story.location': 'trailhead', 'story.route': '', 'story.minutes': 0,
        'story.discovery': '', 'story.ended': False, 'story.outcome': '',
        'friend.location': 'trailhead', 'friend.heel_supported': False,
        'friend.heel_sore': True, 'friend.knows_stream': False,
        'friend.included': False, 'friend.trust': 0, 'friend.boots_muddy': False,
        'lead.location': 'trailhead', 'trail.fern_seen': False,
        'trail.rain': params.rain, 'trail.puddle_depth': params.puddle_depth,
        'trail.shortcut_open': params.shortcut_open, 'trail.pace_gap': params.pace_gap,
        'trail.pool_window': params.pool_window, 'compass.owner': 'Inez',
        'compass.holder': 'Inez', 'compass.borrowed': False,
        'compass.returned': False, 'compass.checked': False,
        'compass.check_count': 0, 'compass.drift': params.compass_drift,
        'compass.calibrated': False, 'compass.calibration_source': 'none',
        'compass.use_count': 0, 'compass.useful_reported': False,
    }
    validate(state)
    return state


def validate(state):
    if not isinstance(state, dict) or set(state) != set(_KEYS):
        raise StoryError('State must contain exactly the declared woodland keys')
    for key, expected in _TYPES.items():
        if type(state[key]) is not expected:
            raise StoryError(f'Invalid type for {key}')
    if state['story.location'] not in {
        'trailhead', 'fork', 'far_bank', 'lookout_edge', 'pool', 'shelter',
    }:
        raise StoryError('Unknown party location')
    if state['story.route'] not in ('', 'ridge', 'shortcut'):
        raise StoryError('Unknown route')
    if state['story.discovery'] not in ('', 'glasswing_pool', 'rain_shelter'):
        raise StoryError('Unknown discovery')
    if state['story.minutes'] < 0 or not 0 <= state['friend.trust'] <= 5:
        raise StoryError('Minutes or trust outside range')
    if state['trail.puddle_depth'] not in (1, 2, 3) or state['trail.pace_gap'] not in (1, 2, 3):
        raise StoryError('Invalid trail measurements')
    if not 30 <= state['trail.pool_window'] <= 90 or state['compass.drift'] not in (0, 1):
        raise StoryError('Invalid trail or compass parameter')
    if state['story.location'] != state['lead.location'] or state['story.location'] != state['friend.location']:
        raise StoryError('The friends must remain together at their actual location')
    if state['compass.owner'] != 'Inez' or state['compass.holder'] not in ('Inez', 'Nia'):
        raise StoryError('Compass ownership or holder is invalid')
    if state['compass.returned'] != (state['compass.borrowed'] and state['compass.holder'] == 'Inez'):
        raise StoryError('Compass borrowing and return disagree')
    if not state['compass.borrowed'] and state['compass.holder'] != 'Inez':
        raise StoryError('A compass cannot leave before it is borrowed')
    if state['compass.borrowed'] and not state['compass.returned'] and state['compass.holder'] != 'Nia':
        raise StoryError('The borrowed compass must stay with Nia')
    if state['compass.checked'] != (state['compass.check_count'] == 1):
        raise StoryError('Compass check trace is inconsistent')
    if state['compass.check_count'] not in (0, 1) or state['compass.use_count'] not in (0, 1):
        raise StoryError('Compass use count outside range')
    if state['compass.calibration_source'] not in ('none', 'north_board', 'stream'):
        raise StoryError('Unknown compass calibration source')
    if state['compass.calibrated'] != (state['compass.calibration_source'] != 'none'):
        raise StoryError('Compass calibration and source disagree')
    if state['compass.calibration_source'] == 'north_board' and state['compass.drift'] != 0:
        raise StoryError('A drifting compass cannot calibrate against the board')
    if state['compass.calibration_source'] == 'stream' and not state['friend.knows_stream']:
        raise StoryError('Stream calibration needs the observed stream bend')
    if state['trail.fern_seen'] != state['friend.knows_stream']:
        raise StoryError('The stream observation must have an enacted source')
    if state['friend.heel_supported'] == state['friend.heel_sore']:
        raise StoryError('Heel support and soreness disagree')
    if state['friend.included'] != bool(state['story.route']):
        raise StoryError('Route choice must keep Rowan included')
    if state['compass.use_count'] != int(bool(state['story.route'])):
        raise StoryError('A route requires exactly one recorded compass bearing')
    if state['compass.useful_reported'] and not state['compass.returned']:
        raise StoryError('Compass report requires its return')
    if state['story.route'] == '' and state['story.location'] != 'trailhead':
        raise StoryError('Cannot leave the trailhead without choosing a route')
    if state['story.discovery'] == '' and state['story.location'] in ('pool', 'shelter'):
        raise StoryError('A destination requires a discovery')
    if state['story.discovery'] == 'glasswing_pool' and state['story.location'] not in ('pool', 'trailhead'):
        raise StoryError('Pool discovery has an incompatible location')
    if state['story.discovery'] == 'rain_shelter' and state['story.location'] not in ('shelter', 'trailhead'):
        raise StoryError('Shelter discovery has an incompatible location')
    if state['story.ended']:
        expected = {
            'glasswing_pool': 'found_pool_together',
            'rain_shelter': 'missed_pool_found_frogs_together',
        }.get(state['story.discovery'])
        if (not expected or state['story.outcome'] != expected
                or state['story.location'] != 'trailhead' or not state['compass.returned']
                or not state['compass.useful_reported'] or not state['friend.included']):
            raise StoryError('Ending is incomplete or contradicts the enacted journey')
    elif state['story.outcome']:
        raise StoryError('An unfinished story cannot have an outcome')
    return True


def _matches_params(params, state):
    for field, key in _PARAMETER_KEYS.items():
        if getattr(params, field) != state[key]:
            raise StoryError(f'Parameters disagree with state at {key}')


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f'Unknown scene: {scene_id}')
    validate(state)
    if state['story.ended']:
        return False
    location = state['story.location']
    if scene_id == 'borrow_compass':
        return location == 'trailhead' and not state['compass.borrowed']
    if scene_id == 'fern_vignette':
        return (location == 'trailhead' and state['compass.borrowed']
                and not state['story.route'] and not state['trail.fern_seen'])
    if scene_id == 'lace_vignette':
        return (location == 'trailhead' and state['compass.borrowed']
                and not state['story.route'] and not state['friend.heel_supported'])
    if scene_id == 'route_choice':
        return (location == 'trailhead' and state['compass.borrowed']
                and state['compass.checked'] and not state['story.route'])
    if scene_id == 'puddle_cross':
        return location == 'fork' and state['story.route'] in ('ridge', 'shortcut')
    if scene_id == 'ridge_walk':
        return location == 'far_bank' and state['story.route'] in ('ridge', 'shortcut')
    if scene_id == 'discovery':
        return location == 'lookout_edge' and not state['story.discovery']
    if scene_id == 'ending_pool':
        return state['story.discovery'] == 'glasswing_pool' and not state['story.ended']
    if scene_id == 'ending_shelter':
        return state['story.discovery'] == 'rain_shelter' and not state['story.ended']
    return False


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    validate(state)
    _matches_params(params, state)
    if not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    x = LocalPlay(state, actors=('Nia', 'Rowan'), validate=validate)

    if scene_id == 'borrow_compass':
        x.act('accept_compass_loan', {
            'story.location': 'trailhead', 'compass.holder': 'Inez',
            'compass.borrowed': False,
        }, **{'compass.holder': 'Nia', 'compass.borrowed': True})
        calibrated = x.state['compass.drift'] == 0
        x.act('compare_needle_with_north_board', {
            'compass.holder': 'Nia', 'compass.borrowed': True,
            'compass.checked': False,
        }, **{
            'compass.checked': True, 'compass.check_count': 1,
            'compass.calibrated': calibrated,
            'compass.calibration_source': 'north_board' if calibrated else 'none',
        })
    elif scene_id == 'fern_vignette':
        x.act('follow_stream_bend', {
            'story.location': 'trailhead', 'trail.fern_seen': False,
        }, **{
            'trail.fern_seen': True, 'friend.knows_stream': True,
            'story.minutes': x.state['story.minutes'] + 4,
        })
        if x.state['compass.drift'] == 1 and not x.state['compass.calibrated']:
            x.act('calibrate_from_stream_bend', {
                'friend.knows_stream': True, 'compass.calibrated': False,
            }, **{
                'compass.calibrated': True,
                'compass.calibration_source': 'stream',
            })
    elif scene_id == 'lace_vignette':
        x.act('patch_rubbing_heel', {
            'story.location': 'trailhead', 'friend.heel_sore': True,
        }, **{
            'friend.heel_sore': False, 'friend.heel_supported': True,
            'story.minutes': x.state['story.minutes'] + 2,
        })
    elif scene_id == 'route_choice':
        short_is_safe = (
            x.state['trail.shortcut_open'] and x.state['friend.heel_supported']
            and x.state['compass.calibrated']
        )
        common = {
            'story.location': 'trailhead', 'compass.holder': 'Nia',
            'compass.checked': True, 'story.route': '',
        }
        changes = {
            'story.route': 'shortcut' if short_is_safe else 'ridge',
            'story.location': 'fork', 'lead.location': 'fork',
            'friend.location': 'fork', 'friend.included': True,
            'friend.trust': x.state['friend.trust'] + 1,
            'compass.use_count': 1,
        }
        if short_is_safe:
            x.act('choose_shortcut_together', common | {
                'trail.shortcut_open': True, 'friend.heel_supported': True,
                'compass.calibrated': True,
            }, **changes)
        else:
            x.act('choose_ridge_together', common, **changes)
    elif scene_id == 'puddle_cross':
        shallow = x.state['trail.puddle_depth'] == 1 and not x.state['trail.rain']
        if shallow:
            x.act('cross_on_stones_together', {
                'story.location': 'fork', 'friend.included': True,
            }, **{
                'story.location': 'far_bank', 'lead.location': 'far_bank',
                'friend.location': 'far_bank',
                'story.minutes': x.state['story.minutes'] + 4,
                'friend.boots_muddy': False,
            })
        else:
            extra = 12 if x.state['trail.rain'] else 9
            x.act('take_marked_edge_around_puddle', {
                'story.location': 'fork', 'friend.included': True,
            }, **{
                'story.location': 'far_bank', 'lead.location': 'far_bank',
                'friend.location': 'far_bank',
                'story.minutes': x.state['story.minutes'] + extra,
                'friend.boots_muddy': True,
            })
    elif scene_id == 'ridge_walk':
        base = 14 if x.state['story.route'] == 'shortcut' else 24
        pace = x.state['trail.pace_gap'] if x.state['friend.heel_supported'] else 2 * x.state['trail.pace_gap']
        weather = 4 if x.state['trail.rain'] else 0
        x.act('walk_the_chosen_route_at_rowans_pace', {
            'story.location': 'far_bank', 'friend.included': True,
        }, **{
            'story.location': 'lookout_edge', 'lead.location': 'lookout_edge',
            'friend.location': 'lookout_edge',
            'story.minutes': x.state['story.minutes'] + base + pace + weather,
        })
    elif scene_id == 'discovery':
        arrives_in_window = (
            not x.state['trail.rain']
            and x.state['story.minutes'] <= x.state['trail.pool_window']
        )
        if arrives_in_window:
            x.act('find_glasswing_pool_together', {
                'story.location': 'lookout_edge', 'friend.included': True,
            }, **{
                'story.location': 'pool', 'lead.location': 'pool',
                'friend.location': 'pool', 'story.discovery': 'glasswing_pool',
                'friend.trust': x.state['friend.trust'] + 1,
            })
        else:
            x.act('turn_to_shelter_and_listen_for_frogs', {
                'story.location': 'lookout_edge', 'friend.included': True,
            }, **{
                'story.location': 'shelter', 'lead.location': 'shelter',
                'friend.location': 'shelter', 'story.discovery': 'rain_shelter',
                'friend.trust': x.state['friend.trust'] + 1,
            })
    else:
        outcome = ('found_pool_together' if scene_id == 'ending_pool'
                   else 'missed_pool_found_frogs_together')
        destination = 'pool' if scene_id == 'ending_pool' else 'shelter'
        discovery = 'glasswing_pool' if scene_id == 'ending_pool' else 'rain_shelter'
        x.act('follow_marked_trail_home_together', {
            'story.location': destination, 'story.discovery': discovery,
            'friend.included': True, 'compass.holder': 'Nia',
        }, **{
            'story.location': 'trailhead', 'lead.location': 'trailhead',
            'friend.location': 'trailhead',
        })
        x.act('return_borrowed_compass_to_inez', {
            'story.location': 'trailhead', 'compass.holder': 'Nia',
            'compass.borrowed': True,
        }, **{'compass.holder': 'Inez', 'compass.returned': True})
        x.act('report_what_the_compass_taught_them', {
            'compass.holder': 'Inez', 'compass.returned': True,
            'compass.checked': True,
        }, **{'compass.useful_reported': True})
        x.act('finish_the_expedition_together', {
            'story.location': 'trailhead', 'compass.returned': True,
        }, **{
            'story.ended': True, 'story.outcome': outcome,
            'friend.trust': x.state['friend.trust'] + 1,
        })

    after = deepcopy(x.state)
    text = render(scene_id, params, state, after)
    words = len(text.split())
    if not 40 <= words <= 70:
        raise StoryError(f'{scene_id} prose has {words} words; expected 40-70')
    return {
        'id': scene_id, 'before': deepcopy(state), 'after': after,
        'events': deepcopy(x.events), 'text': text,
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    state = initial(params)
    episodes = []
    seen = set()
    for scene_id in path:
        if scene_id in seen:
            raise StoryError(f'Scene cannot be repeated: {scene_id}')
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        seen.add(scene_id)
        state = episode['after']
    return episodes


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    p = params if params is not None else parameters(seed)
    if not isinstance(p, Parameters):
        raise TypeError('params must be a Parameters instance')
    rng = random.Random(seed)
    attempts = 0
    budget = 5000

    def search(state, episodes, used):
        nonlocal attempts
        if state['story.ended']:
            return episodes if len(episodes) == count else None
        if len(episodes) >= count:
            return None
        candidates = [sid for sid in SCENES if sid not in used and guard(sid, state)]
        rng.shuffle(candidates)
        for sid in candidates:
            attempts += 1
            if attempts > budget:
                raise StoryError(f'Scene search budget exhausted ({budget} attempts)')
            episode = play_scene(p, state, sid)
            answer = search(episode['after'], episodes + [episode], used | {sid})
            if answer is not None:
                return answer
        return None

    episodes = search(initial(p), [], set())
    if episodes is None:
        raise StoryError(f'No compatible complete route of {count} scenes')
    return {
        'seed': seed, 'parameters': asdict(p), 'scene_count': count,
        'path': [episode['id'] for episode in episodes],
        'story': '\n\n'.join(episode['text'] for episode in episodes),
        'episodes': deepcopy(episodes), 'final_state': deepcopy(episodes[-1]['after']),
        'search_attempts': attempts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    parser.add_argument('--params', help='JSON object overriding seeded parameters')
    args = parser.parse_args()
    values = asdict(parameters(args.seed))
    if args.params:
        overrides = json.loads(args.params)
        if not isinstance(overrides, dict):
            parser.error('--params must be a JSON object')
        values.update(overrides)
    try:
        row = generate(args.seed, count=args.scenes, params=Parameters(**values))
    except (ValueError, StoryError, TypeError) as exc:
        parser.error(str(exc))
    print(row['story'])


if __name__ == '__main__':
    main()
