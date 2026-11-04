'''A bounded, replayable kite adventure built from atomic local plays.'''
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
import random
from pathlib import Path

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError

from .prose import render


@dataclass(frozen=True, kw_only=True)
class Parameters:
    wind: int = 3
    gust: int = 1
    reel_length: int = 30
    frame_sound: bool = True
    tail_weight: int = 2
    shyness: int = 3

    def __post_init__(self):
        for name, low, high in (
            ('wind', 1, 5), ('gust', 0, 4), ('reel_length', 12, 45),
            ('tail_weight', 1, 4), ('shyness', 1, 4),
        ):
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f'{name} must be an integer in [{low}, {high}]')
        if type(self.frame_sound) is not bool:
            raise ValueError('frame_sound must be boolean')


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        wind=rng.choice((1, 2, 3, 4, 5)),
        gust=rng.choice((0, 1, 2, 3, 4)),
        reel_length=rng.choice((12, 16, 22, 28, 36, 42)),
        frame_sound=rng.choice((True, False)),
        tail_weight=rng.choice((1, 2, 3, 4)),
        shyness=rng.choice((1, 2, 3, 4)),
    )


_STATE_TYPES = {
    'story.phase': str, 'story.ended': bool, 'story.outcome': str,
    'story.want': str, 'story.mark_seen': bool, 'story.wind_seen': bool,
    'party.location': str, 'child.name': str, 'child.role': str,
    'neighbor.name': str, 'neighbor.location': str, 'neighbor.accepted': bool,
    'neighbor.shyness': int, 'neighbor.comfort': str, 'neighbor.trust': int,
    'neighbor.role': str, 'neighbor.participated': bool,
    'neighbor.flight_participant': bool,
    'reel.owner': str, 'reel.location': str, 'reel.borrowed': bool,
    'reel.length': int, 'reel.remaining': int, 'reel.line_out': int,
    'reel.patch_used': int, 'reel.used_for_flight': bool,
    'weather.wind': int, 'weather.gust': int, 'wind.observed': bool,
    'wind.vane': str,
    'kite.location': str, 'kite.original_frame_sound': bool,
    'kite.frame_inspected': bool, 'kite.frame_ok': None,
    'kite.repaired': bool, 'kite.ready': bool, 'kite.tail_weight': int,
    'kite.mark': str, 'kite.signature': str, 'kite.height': str,
    'kite.initial_lift': None, 'kite.tangled': bool, 'kite.line_checked': bool,
    'kite.flight_ready': None, 'kite.flight_completed': bool,
    'kite.flight_succeeded': bool, 'kite.folded': bool, 'kite.displayed': bool,
}


def initial(params):
    if not isinstance(params, Parameters):
        raise TypeError('params must be Parameters')
    state = {
        'story.phase': 'start', 'story.ended': False, 'story.outcome': '',
        'story.want': 'fly a kite with June, not merely beside her',
        'story.mark_seen': False, 'story.wind_seen': False,
        'party.location': 'workshop', 'child.name': 'Nia', 'child.role': 'none',
        'neighbor.name': 'June', 'neighbor.location': 'lane',
        'neighbor.accepted': False, 'neighbor.shyness': params.shyness,
        'neighbor.comfort': 'unasked', 'neighbor.trust': 0,
        'neighbor.role': 'none', 'neighbor.participated': False,
        'neighbor.flight_participant': False,
        'reel.owner': 'Tomas', 'reel.location': 'workshop',
        'reel.borrowed': False, 'reel.length': params.reel_length,
        'reel.remaining': params.reel_length, 'reel.line_out': 0,
        'reel.patch_used': 0, 'reel.used_for_flight': False,
        'weather.wind': params.wind, 'weather.gust': params.gust,
        'wind.observed': False, 'wind.vane': 'untested',
        'kite.location': 'workshop',
        'kite.original_frame_sound': params.frame_sound,
        'kite.frame_inspected': False, 'kite.frame_ok': None,
        'kite.repaired': False, 'kite.ready': False, 'kite.tail_weight': 0,
        'kite.mark': '', 'kite.signature': '', 'kite.height': 'untried',
        'kite.initial_lift': None, 'kite.tangled': False,
        'kite.line_checked': False, 'kite.flight_ready': None,
        'kite.flight_completed': False, 'kite.flight_succeeded': False,
        'kite.folded': False, 'kite.displayed': False,
    }
    validate(state)
    return state


def validate(state):
    if not isinstance(state, dict) or set(state) != set(_STATE_TYPES):
        raise StoryError('State keys do not match the kite world')
    for key, expected in _STATE_TYPES.items():
        value = state[key]
        if expected is None:
            if value is not None and type(value) is not bool:
                raise StoryError(f'Invalid nullable boolean: {key}')
        elif type(value) is not expected:
            raise StoryError(f'Invalid type for {key}')

    enums = {
        'story.phase': {'start', 'borrowed', 'invited', 'built', 'field', 'launched', 'responded', 'ended'},
        'story.outcome': {'', 'shared_flight', 'shared_grounded_kite'},
        'party.location': {'workshop', 'lane', 'commons'},
        'neighbor.location': {'lane', 'workshop', 'commons'},
        'neighbor.comfort': {'unasked', 'quiet', 'curious'},
        'neighbor.role': {'none', 'reel', 'tail'},
        'child.role': {'none', 'reel', 'tail'},
        'reel.owner': {'Tomas'}, 'reel.location': {'workshop', 'Nia'},
        'wind.vane': {'untested', 'steady', 'gusty'},
        'kite.location': {'workshop', 'party', 'commons', 'workshop_rack', 'workshop_window'},
        'kite.height': {'untried', 'ground', 'low', 'high'},
        'kite.mark': {'', 'blue star'},
        'kite.signature': {'', 'Nia + June'},
    }
    for key, allowed in enums.items():
        if state[key] not in allowed:
            raise StoryError(f'Invalid value for {key}')

    for key, low, high in (
        ('neighbor.shyness', 1, 4), ('neighbor.trust', 0, 1),
        ('weather.wind', 1, 5), ('weather.gust', 0, 4),
        ('reel.length', 12, 45), ('reel.remaining', 0, 45),
        ('reel.line_out', 0, 8), ('reel.patch_used', 0, 3),
        ('kite.tail_weight', 0, 4),
    ):
        if not low <= state[key] <= high:
            raise StoryError(f'Out-of-range state: {key}')
    if state['reel.line_out'] not in (0, 8) or state['reel.patch_used'] not in (0, 3):
        raise StoryError('The kite uses one measured length of line')
    if state['reel.remaining'] + state['reel.line_out'] + state['reel.patch_used'] != state['reel.length']:
        raise StoryError('Borrowed string must be conserved')
    if state['reel.borrowed'] != (state['reel.location'] == 'Nia'):
        raise StoryError('Reel custody and loan status disagree')
    if state['reel.line_out'] and not (state['reel.borrowed'] and state['reel.used_for_flight']):
        raise StoryError('Line can only be out while the borrowed reel is in use')

    if state['story.mark_seen'] != (state['kite.mark'] == 'blue star'):
        raise StoryError('The optional mark must have been enacted')
    if state['story.wind_seen'] != state['wind.observed']:
        raise StoryError('Wind knowledge must come from its vignette')
    if state['wind.observed'] != (state['wind.vane'] != 'untested'):
        raise StoryError('Wind-vane observation is inconsistent')
    if state['neighbor.accepted'] != (state['neighbor.comfort'] != 'unasked'):
        raise StoryError('Invitation and comfort state disagree')
    if state['neighbor.participated'] and not state['neighbor.accepted']:
        raise StoryError('June cannot participate without accepting')
    if state['neighbor.participated'] != (state['neighbor.role'] != 'none'):
        raise StoryError('June participation and role disagree')
    if state['neighbor.flight_participant'] and not state['neighbor.participated']:
        raise StoryError('A flight participant must have joined the outing')

    if state['kite.frame_inspected']:
        if type(state['kite.frame_ok']) is not bool:
            raise StoryError('An inspected frame needs a known condition')
    elif state['kite.frame_ok'] is not None:
        raise StoryError('Frame condition was learned before inspection')
    if state['kite.repaired'] != (state['reel.patch_used'] == 3):
        raise StoryError('A frame repair must account for its string')
    if state['kite.repaired'] and (state['kite.original_frame_sound'] or state['kite.frame_ok'] is not True):
        raise StoryError('Repair state contradicts the original frame')
    if state['kite.ready']:
        if not state['kite.frame_inspected'] or state['kite.tail_weight'] not in (1, 2, 3, 4):
            raise StoryError('A prepared kite needs an inspected frame and tail')
    elif state['kite.tail_weight'] != 0:
        raise StoryError('Tail weight set before preparation')

    if state['kite.initial_lift'] is None:
        if state['kite.height'] != 'untried' or state['reel.used_for_flight']:
            raise StoryError('Flight state changed before the first attempt')
    elif type(state['kite.initial_lift']) is bool:
        if state['kite.height'] == 'untried' or not state['reel.used_for_flight']:
            raise StoryError('First attempt and reel use disagree')
    else:
        raise StoryError('Invalid first-lift result')
    if state['kite.flight_ready'] is not None:
        if type(state['kite.flight_ready']) is not bool or not state['kite.line_checked'] or not state['neighbor.participated']:
            raise StoryError('Second-flight decision lacks its enacted checks')
    if state['kite.flight_succeeded'] and not state['kite.flight_completed']:
        raise StoryError('A successful flight must be completed')
    if state['kite.displayed'] and (state['kite.location'] != 'workshop_window' or not state['kite.signature']):
        raise StoryError('A displayed kite must be signed and in the window')

    if state['story.ended'] != (state['story.phase'] == 'ended'):
        raise StoryError('Story ending flag and phase disagree')
    if not state['story.ended'] and state['story.outcome']:
        raise StoryError('Outcome set before the ending')
    if state['story.ended']:
        if not state['story.outcome'] or state['party.location'] != 'workshop':
            raise StoryError('Ending must resolve at the workshop')
        if state['neighbor.location'] != 'workshop' or state['neighbor.flight_participant'] is not True:
            raise StoryError('June must return with the kite')
        if state['reel.location'] != 'workshop' or state['reel.borrowed'] or state['reel.line_out'] != 0:
            raise StoryError('The borrowed reel must be rewound and returned')
        if not state['reel.used_for_flight'] or not state['kite.flight_completed'] or not state['kite.folded']:
            raise StoryError('The outing must reach a completed physical outcome')
        if state['kite.signature'] != 'Nia + June':
            raise StoryError('Both children must sign the kite')
        if state['story.outcome'] == 'shared_flight':
            if not state['kite.flight_succeeded'] or state['kite.location'] != 'workshop_rack' or state['kite.displayed']:
                raise StoryError('Flying ending contradicts the final kite state')
        elif state['story.outcome'] == 'shared_grounded_kite':
            if state['kite.flight_succeeded'] or state['kite.location'] != 'workshop_window' or not state['kite.displayed']:
                raise StoryError('Grounded ending contradicts the final kite state')
    return None


def _parameters_match(params, state):
    expected = {
        'weather.wind': params.wind, 'weather.gust': params.gust,
        'reel.length': params.reel_length,
        'kite.original_frame_sound': params.frame_sound,
        'neighbor.shyness': params.shyness,
    }
    if any(state[key] != value for key, value in expected.items()):
        raise StoryError('Parameters do not match this world state')


def _act(play, name, requires=None, changes=None):
    play.act(name, requires=requires or {}, **(changes or {}))


@dataclass(frozen=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


SCENES = (
    'workshop', 'invite', 'vignette_mark', 'prepare_kite', 'vignette_ribbon',
    'walk_to_commons', 'first_flight', 'response', 'ending_flight', 'ending_grounded',
)


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f'Unknown scene: {scene_id}')
    validate(state)
    if state['story.ended']:
        return False
    phase = state['story.phase']
    if scene_id == 'workshop':
        return phase == 'start' and state['party.location'] == 'workshop'
    if scene_id == 'invite':
        return phase == 'borrowed' and state['party.location'] == 'lane' and state['reel.borrowed']
    if scene_id == 'vignette_mark':
        return phase == 'invited' and not state['story.mark_seen']
    if scene_id == 'prepare_kite':
        return phase == 'invited' and state['party.location'] == 'lane'
    if scene_id == 'vignette_ribbon':
        return phase == 'built' and not state['story.wind_seen']
    if scene_id == 'walk_to_commons':
        return phase == 'built' and state['party.location'] == 'lane'
    if scene_id == 'first_flight':
        return phase == 'field' and state['party.location'] == 'commons'
    if scene_id == 'response':
        return phase == 'launched' and state['kite.initial_lift'] is not None
    if scene_id == 'ending_flight':
        return phase == 'responded' and state['kite.flight_ready'] is True
    if scene_id == 'ending_grounded':
        return phase == 'responded' and state['kite.flight_ready'] is False
    return False


def _episode(scene_id, state, play, params):
    after = deepcopy(play.state)
    return Episode(
        id=scene_id, before=deepcopy(state), after=after,
        events=tuple(deepcopy(play.events)),
        text=render(scene_id, params, state, after),
    )


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise TypeError('params must be Parameters')
    validate(state)
    _parameters_match(params, state)
    if not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    play = LocalPlay(state, actors=('Nia', 'June', 'Tomas'), validate=validate)

    if scene_id == 'workshop':
        _act(play, 'borrow_string_reel',
             {'reel.location': 'workshop', 'reel.borrowed': False},
             {'reel.location': 'Nia', 'reel.borrowed': True})
        _act(play, 'leave_workshop', {'party.location': 'workshop'},
             {'party.location': 'lane', 'story.phase': 'borrowed'})

    elif scene_id == 'invite':
        comfort = 'quiet' if params.shyness >= 3 else 'curious'
        _act(play, 'invite_june_quietly',
             {'party.location': 'lane', 'neighbor.accepted': False, 'story.phase': 'borrowed'},
             {'neighbor.accepted': True, 'neighbor.comfort': comfort, 'story.phase': 'invited'})

    elif scene_id == 'vignette_mark':
        _act(play, 'draw_blue_star_together',
             {'story.phase': 'invited', 'story.mark_seen': False},
             {'story.mark_seen': True, 'kite.mark': 'blue star', 'neighbor.trust': 1})

    elif scene_id == 'prepare_kite':
        _act(play, 'return_to_workbench',
             {'party.location': 'lane', 'neighbor.accepted': True},
             {'party.location': 'workshop', 'neighbor.location': 'workshop'})
        _act(play, 'inspect_bamboo_frame',
             {'kite.frame_inspected': False, 'kite.frame_ok': None},
             {'kite.frame_inspected': True, 'kite.frame_ok': params.frame_sound})
        if not params.frame_sound and play.state['reel.remaining'] >= 15:
            _act(play, 'lash_split_spar_with_three_metres',
                 {'kite.frame_ok': False, 'reel.patch_used': 0},
                 {'kite.frame_ok': True, 'kite.repaired': True,
                  'reel.remaining': play.state['reel.remaining'] - 3, 'reel.patch_used': 3})
        _act(play, 'fit_balanced_tail',
             {'kite.ready': False, 'kite.tail_weight': 0},
             {'kite.ready': True, 'kite.tail_weight': params.tail_weight})
        _act(play, 'carry_kite_back_to_lane',
             {'party.location': 'workshop', 'kite.ready': True},
             {'party.location': 'lane', 'neighbor.location': 'lane',
              'kite.location': 'party', 'story.phase': 'built'})

    elif scene_id == 'vignette_ribbon':
        vane = 'gusty' if params.gust >= 2 else 'steady'
        _act(play, 'test_ribbon_at_weather_pole',
             {'story.phase': 'built', 'wind.observed': False},
             {'wind.observed': True, 'wind.vane': vane, 'story.wind_seen': True})

    elif scene_id == 'walk_to_commons':
        _act(play, 'carry_kite_and_reel_to_common',
             {'party.location': 'lane', 'kite.location': 'party', 'kite.ready': True},
             {'party.location': 'commons', 'neighbor.location': 'commons',
              'kite.location': 'commons', 'story.phase': 'field'})

    elif scene_id == 'first_flight':
        lift = (
            play.state['kite.frame_ok'] is True
            and 2 <= params.wind <= 4
            and play.state['kite.tail_weight'] in (2, 3)
            and params.reel_length - play.state['reel.patch_used'] >= 18
        )
        tangled = lift and params.gust >= 3
        height = 'low' if lift else 'ground'
        _act(play, 'pay_out_line_for_first_lift',
             {'party.location': 'commons', 'kite.ready': True,
              'reel.line_out': 0, 'story.phase': 'field'},
             {'kite.initial_lift': lift, 'kite.tangled': tangled,
              'kite.height': height, 'reel.remaining': play.state['reel.remaining'] - 8,
              'reel.line_out': 8, 'reel.used_for_flight': True,
              'story.phase': 'launched'})

    elif scene_id == 'response':
        if play.state['kite.tangled']:
            _act(play, 'ease_slack_and_free_line',
                 {'kite.tangled': True, 'kite.line_checked': False},
                 {'kite.tangled': False, 'kite.line_checked': True})
        else:
            _act(play, 'check_clear_line_together',
                 {'kite.tangled': False, 'kite.line_checked': False},
                 {'kite.line_checked': True})
        offer_reel = (
            play.state['neighbor.trust'] > 0
            or params.shyness <= 2
            or play.state['wind.observed']
        )
        if offer_reel:
            _act(play, 'offer_june_the_reel',
                 {'neighbor.role': 'none', 'neighbor.participated': False,
                  'kite.line_checked': True},
                 {'neighbor.role': 'reel', 'child.role': 'tail',
                  'neighbor.participated': True, 'neighbor.trust': 1})
        else:
            _act(play, 'offer_june_the_tail_and_a_choice',
                 {'neighbor.role': 'none', 'neighbor.participated': False,
                  'kite.line_checked': True},
                 {'neighbor.role': 'tail', 'child.role': 'reel',
                  'neighbor.participated': True, 'neighbor.trust': 1})
        steady_conditions = (
            play.state['kite.frame_ok'] is True
            and 2 <= params.wind <= 4
            and params.gust <= 2
            and play.state['kite.tail_weight'] in (2, 3)
            and params.reel_length - play.state['reel.patch_used'] >= 24
        )
        enough_control = play.state['neighbor.role'] == 'reel' or params.gust == 0
        safe_flight = steady_conditions and enough_control
        _act(play, 'decide_whether_a_second_run_is_safe',
             {'kite.line_checked': True, 'neighbor.participated': True},
             {'kite.flight_ready': safe_flight, 'story.phase': 'responded'})

    elif scene_id == 'ending_flight':
        _act(play, 'fly_kite_with_shared_control',
             {'kite.flight_ready': True, 'reel.line_out': 8},
             {'kite.height': 'high', 'kite.flight_completed': True,
              'kite.flight_succeeded': True, 'neighbor.flight_participant': True})
        _act(play, 'land_and_rewind_loose_line',
             {'kite.height': 'high', 'reel.line_out': 8},
             {'kite.height': 'ground', 'kite.folded': True,
              'reel.remaining': play.state['reel.remaining'] + 8, 'reel.line_out': 0})
        _act(play, 'walk_back_to_workshop', {'party.location': 'commons'},
             {'party.location': 'workshop', 'neighbor.location': 'workshop',
              'kite.location': 'workshop'})
        _act(play, 'return_borrowed_reel_to_tomas',
             {'reel.location': 'Nia', 'reel.borrowed': True},
             {'reel.location': 'workshop', 'reel.borrowed': False})
        _act(play, 'sign_and_store_flown_kite', {'kite.location': 'workshop'},
             {'kite.signature': 'Nia + June', 'kite.location': 'workshop_rack'})
        _act(play, 'finish_shared_flight', {'reel.borrowed': False},
             {'story.ended': True, 'story.phase': 'ended', 'story.outcome': 'shared_flight'})

    elif scene_id == 'ending_grounded':
        _act(play, 'fold_the_grounded_kite_together',
             {'kite.flight_ready': False, 'neighbor.participated': True},
             {'kite.height': 'ground', 'kite.flight_completed': True,
              'kite.flight_succeeded': False, 'kite.folded': True,
              'neighbor.flight_participant': True})
        _act(play, 'rewind_loose_line', {'reel.line_out': 8},
             {'reel.remaining': play.state['reel.remaining'] + 8, 'reel.line_out': 0})
        _act(play, 'walk_back_to_workshop', {'party.location': 'commons'},
             {'party.location': 'workshop', 'neighbor.location': 'workshop',
              'kite.location': 'workshop'})
        _act(play, 'return_borrowed_reel_to_tomas',
             {'reel.location': 'Nia', 'reel.borrowed': True},
             {'reel.location': 'workshop', 'reel.borrowed': False})
        _act(play, 'hang_signed_kite_in_workshop_window', {'kite.location': 'workshop'},
             {'kite.signature': 'Nia + June', 'kite.location': 'workshop_window',
              'kite.displayed': True})
        _act(play, 'finish_shared_grounded_outing', {'reel.borrowed': False},
             {'story.ended': True, 'story.phase': 'ended',
              'story.outcome': 'shared_grounded_kite'})

    return _episode(scene_id, state, play, params)


def replay(params, path):
    if not isinstance(params, Parameters):
        raise TypeError('params must be Parameters')
    if isinstance(path, (str, bytes)):
        raise TypeError('path must be an iterable of scene IDs')
    state = initial(params)
    episodes = []
    used = set()
    for scene_id in path:
        if scene_id in used:
            raise StoryError(f'Scene cannot be repeated: {scene_id}')
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        used.add(scene_id)
        state = episode.after
    return tuple(episodes)


def _minimum_core_remaining(state):
    return {
        'start': 7, 'borrowed': 6, 'invited': 5, 'built': 4,
        'field': 3, 'launched': 2, 'responded': 1, 'ended': 0,
    }[state['story.phase']]


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    p = parameters(seed) if params is None else params
    if not isinstance(p, Parameters):
        raise TypeError('params must be Parameters')
    rng = random.Random(seed)
    attempts = 0
    initial_state = initial(p)

    def search(state, episodes, used):
        nonlocal attempts
        remaining = count - len(episodes)
        if remaining < _minimum_core_remaining(state):
            return None
        if remaining == 0:
            return episodes if state['story.ended'] else None
        if state['story.ended']:
            return None
        choices = [scene_id for scene_id in SCENES
                   if scene_id not in used and guard(scene_id, state)
                   and (not scene_id.startswith('ending_') or remaining == 1)]
        rng.shuffle(choices)
        for scene_id in choices:
            attempts += 1
            if attempts > 5000:
                raise StoryError('Bounded scene search exceeded 5000 attempts')
            episode = play_scene(p, state, scene_id)
            answer = search(episode.after, episodes + (episode,), used | {scene_id})
            if answer is not None:
                return answer
        return None

    chosen = search(initial_state, (), set())
    if chosen is None:
        raise StoryError('No complete compatible route at the requested length')
    rows = [
        {'id': e.id, 'before': deepcopy(e.before), 'after': deepcopy(e.after),
         'events': deepcopy(list(e.events)), 'text': e.text}
        for e in chosen
    ]
    return {
        'seed': seed,
        'parameters': asdict(p),
        'scene_count': count,
        'path': [e.id for e in chosen],
        'story': '\n\n'.join(e.text for e in chosen),
        'episodes': rows,
        'final_state': deepcopy(chosen[-1].after),
        'search_attempts': attempts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    parser.add_argument('--params', type=Path, help='JSON object overriding seeded parameters')
    args = parser.parse_args()
    p = parameters(args.seed)
    if args.params:
        overrides = json.loads(args.params.read_text(encoding='utf-8'))
        if not isinstance(overrides, dict):
            parser.error('--params must contain a JSON object')
        p = Parameters(**(asdict(p) | overrides))
    print(generate(args.seed, count=args.scenes, params=p)['story'])


if __name__ == '__main__':
    main()
