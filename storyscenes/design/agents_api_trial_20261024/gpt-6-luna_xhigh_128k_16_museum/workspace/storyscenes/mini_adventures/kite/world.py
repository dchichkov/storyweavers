'''Bounded, replayable museum shadow-exhibit adventure. No runtime model calls.'''
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
import math
import random

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .prose import render


@dataclass(frozen=True, kw_only=True)
class Parameters:
    label_target: str = 'near_torch'
    room_ambient: bool = False
    torch_charge: int = 3
    screen_distance_cm: int = 120
    figure_kind: str = 'card'

    def __post_init__(self):
        if self.label_target not in ('near_torch', 'near_screen'):
            raise ValueError('label_target must be near_torch or near_screen')
        if type(self.room_ambient) is not bool:
            raise ValueError('room_ambient must be boolean')
        if type(self.torch_charge) is not int or not 1 <= self.torch_charge <= 3:
            raise ValueError('torch_charge must be an integer from 1 through 3')
        if type(self.screen_distance_cm) is not int or not 80 <= self.screen_distance_cm <= 160:
            raise ValueError('screen_distance_cm must be an integer from 80 through 160')
        if self.figure_kind not in ('card', 'lace'):
            raise ValueError('figure_kind must be card or lace')


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        label_target=rng.choice(('near_torch', 'near_screen')),
        room_ambient=rng.choice((False, True)),
        torch_charge=rng.choice((1, 2, 3)),
        screen_distance_cm=rng.choice((80, 100, 120, 140, 160)),
        figure_kind=rng.choice(('card', 'lace')),
    )


def _figure_distance(position, screen_distance):
    return 25 if position == 'near_torch' else screen_distance - 15


def _magnification(screen_distance, figure_distance):
    return round(screen_distance / figure_distance, 2)


def _observation(screen_distance, figure_distance, charge, ambient, kind):
    score = charge + (0 if ambient else 1) - (1 if kind == 'lace' else 0)
    if score < 3:
        return 'unreadable'
    size = 'large' if _magnification(screen_distance, figure_distance) >= 2 else 'small'
    quality = 'clear' if score >= 4 else 'soft'
    return f'{quality}_{size}'


def _readable(observation):
    return observation.startswith(('clear_', 'soft_'))


def _size(observation):
    return observation.split('_')[-1] if _readable(observation) else ''


def initial(params):
    if not isinstance(params, Parameters):
        raise TypeError('initial expects Parameters')
    distance = params.screen_distance_cm
    return {
        'story.ended': False, 'story.outcome': '',
        'children.location': 'foyer',
        'mara.want': 'make a striking shadow exhibit',
        'tavi.want': 'understand the label rather than guess',
        'children.cooperation': 0, 'children.hypothesis': '',
        'children.learned': False, 'children.lesson': '',
        'torch.owner': 'museum', 'torch.location': 'attendant_counter',
        'torch.borrowed': False, 'torch.checked': False, 'torch.on': False,
        'torch.charge': params.torch_charge, 'torch.last_use': '',
        'screen.location': 'north_wall', 'screen.distance_cm': distance,
        'room.initial_ambient': params.room_ambient, 'room.ambient': params.room_ambient,
        'figure.location': 'activity_table', 'figure.kind': params.figure_kind,
        'figure.position': 'near_screen',
        'figure.distance_cm': _figure_distance('near_screen', distance),
        'label.location': 'north_wall', 'label.target': params.label_target,
        'label.original_target': params.label_target, 'label.read': False,
        'label.corrected': False, 'label.note': '',
        'mara.knows_label': False, 'tavi.knows_label': False,
        'shadow.first_done': False, 'shadow.first_observation': '',
        'shadow.first_position': '', 'shadow.first_distance_cm': 0,
        'shadow.first_magnification': 0.0, 'shadow.first_ambient': None,
        'shadow.second_done': False, 'shadow.second_observation': '',
        'shadow.second_position': '', 'shadow.second_distance_cm': 0,
        'shadow.second_magnification': 0.0, 'shadow.second_ambient': None,
        'shadow.evidence': '', 'shadow.larger_position': '',
        'investigation.done': False,
        'visitor.present': False, 'visitor.location': 'next_table',
        'visitor.reassured': False,
        'sketch.made': False, 'sketch.location': 'blank_page',
        'sketch.first_observation': '', 'sketch.first_magnification': 0.0,
        'exhibit.ready': False, 'exhibit.note_posted': False,
        'staff.received_result': '',
    }


_STATE_KEYS = frozenset(initial(Parameters()))
_SCENE_IDS = (
    'borrow_torch', 'first_demo', 'read_label', 'vignette_visitor',
    'vignette_sketch', 'inspect_setup', 'retest', 'ending_show',
    'ending_correct_label', 'ending_honest',
)
SCENES = _SCENE_IDS


def validate(state):
    if not isinstance(state, dict) or set(state) != _STATE_KEYS:
        raise StoryError('State has missing or undeclared keys')
    for key, value in state.items():
        if value is not None and type(value) not in (str, bool, int, float):
            raise StoryError(f'Non-scalar state value: {key}')
        if type(value) is float and not math.isfinite(value):
            raise StoryError(f'Nonfinite state value: {key}')

    bool_keys = (
        'story.ended', 'torch.borrowed', 'torch.checked', 'torch.on',
        'room.initial_ambient', 'room.ambient', 'label.read', 'label.corrected',
        'mara.knows_label', 'tavi.knows_label', 'shadow.first_done',
        'shadow.second_done', 'investigation.done', 'children.learned',
        'visitor.present', 'visitor.reassured', 'sketch.made',
        'exhibit.ready', 'exhibit.note_posted',
    )
    if any(type(state[key]) is not bool for key in bool_keys):
        raise StoryError('Boolean state has an invalid type')
    integer_keys = (
        'children.cooperation', 'torch.charge', 'screen.distance_cm',
        'figure.distance_cm', 'shadow.first_distance_cm', 'shadow.second_distance_cm',
    )
    if any(type(state[key]) is not int for key in integer_keys):
        raise StoryError('Integer state has an invalid type')
    for key in ('shadow.first_magnification', 'shadow.second_magnification',
                'sketch.first_magnification'):
        if type(state[key]) not in (int, float) or not math.isfinite(state[key]):
            raise StoryError(f'Invalid measurement: {key}')

    if state['children.location'] not in ('foyer', 'activity_room'):
        raise StoryError('Unknown children location')
    if state['screen.location'] != 'north_wall' or state['label.location'] != 'north_wall':
        raise StoryError('The screen and label are fixed to the north wall')
    if not 80 <= state['screen.distance_cm'] <= 160:
        raise StoryError('Screen distance is outside the validated range')
    if state['torch.charge'] not in (1, 2, 3):
        raise StoryError('Invalid torch charge')
    if state['figure.kind'] not in ('card', 'lace'):
        raise StoryError('Unknown figure material')
    if state['label.target'] not in ('near_torch', 'near_screen') or state['label.original_target'] not in ('near_torch', 'near_screen'):
        raise StoryError('Unknown label target')
    if state['label.target'] != state['label.original_target'] and not state['label.corrected']:
        raise StoryError('Label changed without a correction')
    if state['label.corrected'] and not (
        state['label.original_target'] == 'near_screen' and state['label.target'] == 'near_torch'
    ):
        raise StoryError('Only a reversed screen-side instruction can be corrected')
    if state['room.ambient'] and not state['room.initial_ambient']:
        raise StoryError('Ambient light cannot increase during the experiment')

    if state['torch.owner'] not in ('museum', 'children'):
        raise StoryError('Unknown torch custodian')
    if state['torch.owner'] == 'children':
        if not state['torch.borrowed'] or state['torch.location'] != 'activity_table':
            raise StoryError('Borrowed torch location and custody disagree')
    else:
        expected_location = 'return_desk' if state['torch.borrowed'] else 'attendant_counter'
        if state['torch.location'] != expected_location:
            raise StoryError('Museum torch location and custody disagree')
    if state['torch.on'] and state['torch.owner'] != 'children':
        raise StoryError('The returned torch cannot be on')
    if state['torch.checked'] and not state['torch.borrowed']:
        raise StoryError('Torch cannot be checked before borrowing')

    if state['figure.position'] not in ('near_torch', 'near_screen'):
        raise StoryError('Unknown figure position')
    expected_distance = _figure_distance(state['figure.position'], state['screen.distance_cm'])
    if state['figure.distance_cm'] != expected_distance:
        raise StoryError('Figure position and physical distance disagree')
    if state['children.cooperation'] < 0:
        raise StoryError('Cooperation cannot be negative')

    if state['shadow.first_done']:
        if not state['torch.checked'] or state['shadow.first_position'] != 'near_screen':
            raise StoryError('First trial did not use the starting setup')
        distance = state['screen.distance_cm'] - 15
        expected = _observation(state['screen.distance_cm'], distance, state['torch.charge'],
                                state['shadow.first_ambient'], state['figure.kind'])
        if (state['shadow.first_distance_cm'] != distance
                or not math.isclose(state['shadow.first_magnification'], _magnification(state['screen.distance_cm'], distance))
                or state['shadow.first_observation'] != expected):
            raise StoryError('First shadow does not match its physical setup')
    elif any((state['shadow.first_observation'], state['shadow.first_position'],
              state['shadow.first_distance_cm'], state['shadow.first_magnification'] != 0.0,
              state['shadow.first_ambient'] is not None)):
        raise StoryError('Incomplete first-trial state')

    if state['shadow.second_done']:
        if not state['investigation.done'] or state['shadow.second_position'] != 'near_torch':
            raise StoryError('Second trial lacks the controlled setup')
        distance = 25
        expected = _observation(state['screen.distance_cm'], distance, state['torch.charge'],
                                state['shadow.second_ambient'], state['figure.kind'])
        if (state['shadow.second_distance_cm'] != distance
                or not math.isclose(state['shadow.second_magnification'], _magnification(state['screen.distance_cm'], distance))
                or state['shadow.second_observation'] != expected):
            raise StoryError('Second shadow does not match its physical setup')
        readable = (_readable(state['shadow.first_observation'])
                    and _readable(state['shadow.second_observation']))
        evidence = 'near_torch' if readable else 'inconclusive'
        larger = 'near_torch' if readable else ''
        lesson = 'near_torch_makes_larger' if readable else 'comparison_too_dim'
        if (state['shadow.evidence'] != evidence or state['shadow.larger_position'] != larger
                or not state['children.learned'] or state['children.lesson'] != lesson):
            raise StoryError('Inference does not follow the recorded observations')
    elif any((state['shadow.second_observation'], state['shadow.second_position'],
              state['shadow.second_distance_cm'], state['shadow.second_magnification'] != 0.0,
              state['shadow.second_ambient'] is not None, state['shadow.evidence'],
              state['shadow.larger_position'], state['children.learned'], state['children.lesson'])):
        raise StoryError('Incomplete second-trial state')
    if state['investigation.done'] and not state['children.hypothesis']:
        raise StoryError('Investigation has no stated question')
    if state['label.read'] != (state['mara.knows_label'] and state['tavi.knows_label']):
        raise StoryError('Label knowledge is inconsistent')

    if not state['visitor.present'] and (state['visitor.location'] != 'next_table' or state['visitor.reassured']):
        raise StoryError('Absent visitor has an impossible location or response')
    if state['visitor.present'] and state['visitor.location'] != 'activity_room':
        raise StoryError('Visitor location is inconsistent')
    if state['sketch.made']:
        if (not state['shadow.first_done'] or state['sketch.location'] != 'activity_table'
                or state['sketch.first_observation'] != state['shadow.first_observation']
                or not math.isclose(state['sketch.first_magnification'], state['shadow.first_magnification'])):
            raise StoryError('Sketch does not preserve the first observation')
    elif (state['sketch.location'] != 'blank_page' or state['sketch.first_observation']
          or state['sketch.first_magnification'] != 0.0):
        raise StoryError('Unmade sketch has recorded contents')

    if state['story.ended']:
        outcome = state['story.outcome']
        if (not outcome or state['torch.owner'] != 'museum' or state['torch.location'] != 'return_desk'
                or state['torch.on'] or state['torch.last_use'] != 'paired comparison'
                or state['staff.received_result'] != outcome):
            raise StoryError('Ending left the borrowed torch or result unfinished')
        if outcome == 'accurate_demonstration':
            if not (state['shadow.evidence'] == 'near_torch' and state['label.target'] == 'near_torch'
                    and state['exhibit.ready'] and not state['exhibit.note_posted']):
                raise StoryError('Accurate demonstration ending lacks its evidence')
        elif outcome == 'corrected_label':
            if not (state['shadow.evidence'] == 'near_torch' and state['label.corrected']
                    and state['exhibit.ready'] and not state['exhibit.note_posted']):
                raise StoryError('Correction ending lacks its evidence')
        elif outcome == 'honest_inconclusive':
            if not (state['shadow.evidence'] == 'inconclusive' and state['exhibit.note_posted']
                    and not state['exhibit.ready'] and state['label.note']):
                raise StoryError('Inconclusive ending lacks an honest note')
        else:
            raise StoryError('Unknown ending outcome')
    elif state['story.outcome'] or state['staff.received_result']:
        raise StoryError('An unfinished story cannot already have an outcome')


def _parameters_match(params, state):
    if (params.label_target != state['label.original_target']
            or params.room_ambient != state['room.initial_ambient']
            or params.torch_charge != state['torch.charge']
            or params.screen_distance_cm != state['screen.distance_cm']
            or params.figure_kind != state['figure.kind']):
        raise StoryError('Parameters do not describe this state')


@dataclass(frozen=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f'Unknown scene: {scene_id}')
    validate(state)
    if state['story.ended']:
        return False
    if scene_id == 'borrow_torch':
        return state['children.location'] == 'foyer' and not state['torch.borrowed']
    if scene_id == 'first_demo':
        return (state['children.location'] == 'activity_room' and state['torch.owner'] == 'children'
                and state['torch.checked'] and not state['shadow.first_done'])
    if scene_id == 'read_label':
        return state['shadow.first_done'] and not state['label.read']
    if scene_id in ('vignette_visitor', 'vignette_sketch'):
        if not (state['shadow.first_done'] and state['label.read'] and not state['investigation.done']):
            return False
        return not state['visitor.present'] if scene_id == 'vignette_visitor' else not state['sketch.made']
    if scene_id == 'inspect_setup':
        return (state['shadow.first_done'] and state['label.read'] and not state['investigation.done']
                and state['figure.position'] == 'near_screen' and not state['torch.on'])
    if scene_id == 'retest':
        return state['investigation.done'] and not state['shadow.second_done']
    if not state['shadow.second_done']:
        return False
    evidence = state['shadow.evidence']
    if scene_id == 'ending_show':
        return evidence == 'near_torch' and state['label.target'] == 'near_torch'
    if scene_id == 'ending_correct_label':
        return evidence == 'near_torch' and state['label.target'] == 'near_screen'
    if scene_id == 'ending_honest':
        return evidence == 'inconclusive'
    return False


class _Rejected(ValueError):
    pass


def _observation_fields(state, which, position):
    distance = _figure_distance(position, state['screen.distance_cm'])
    observation = _observation(state['screen.distance_cm'], distance, state['torch.charge'],
                               state['room.ambient'], state['figure.kind'])
    return {
        f'shadow.{which}_done': True,
        f'shadow.{which}_observation': observation,
        f'shadow.{which}_position': position,
        f'shadow.{which}_distance_cm': distance,
        f'shadow.{which}_magnification': _magnification(state['screen.distance_cm'], distance),
        f'shadow.{which}_ambient': state['room.ambient'],
        'torch.last_use': 'first trial' if which == 'first' else 'paired comparison',
    }


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise TypeError('play_scene expects Parameters')
    validate(state)
    _parameters_match(params, state)
    if not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    before = deepcopy(state)
    play = LocalPlay(state, actors=('Mara', 'Tavi'), validate=validate)

    if scene_id == 'borrow_torch':
        play.act('enter_activity_room', {'children.location': 'foyer'},
                 **{'children.location': 'activity_room'})
        play.act('borrow_museum_torch', {'torch.owner': 'museum', 'torch.location': 'attendant_counter'},
                 **{'torch.owner': 'children', 'torch.location': 'activity_table', 'torch.borrowed': True})
        play.act('check_torch_switch', {'torch.owner': 'children', 'torch.borrowed': True},
                 **{'torch.checked': True, 'torch.on': True})
        play.act('switch_off_after_check', {'torch.on': True}, **{'torch.on': False})
    elif scene_id == 'first_demo':
        play.act('switch_on_for_first_trial', {'torch.owner': 'children', 'torch.checked': True},
                 **{'torch.on': True})
        play.act('cast_first_shadow', {'torch.on': True, 'figure.position': 'near_screen'},
                 **_observation_fields(play.state, 'first', 'near_screen'))
    elif scene_id == 'read_label':
        play.act('read_printed_peg_instruction', {'shadow.first_done': True, 'label.read': False},
                 **{'label.read': True, 'mara.knows_label': True, 'tavi.knows_label': True})
    elif scene_id == 'vignette_visitor':
        play.act('welcome_watching_visitor', {'visitor.present': False},
                 **{'visitor.present': True, 'visitor.location': 'activity_room'})
        play.act('show_june_the_paper_figure', {'visitor.present': True},
                 **{'visitor.reassured': True})
    elif scene_id == 'vignette_sketch':
        play.act('record_first_outline_honestly', {'shadow.first_done': True, 'sketch.made': False},
                 **{'sketch.made': True, 'sketch.location': 'activity_table',
                    'sketch.first_observation': play.state['shadow.first_observation'],
                    'sketch.first_magnification': play.state['shadow.first_magnification']})
    elif scene_id == 'inspect_setup':
        play.act('switch_off_before_moving_figure', {'torch.on': False},
                 **{'torch.last_use': 'first trial'})
        if play.state['room.ambient']:
            play.act('draw_window_shade', {'room.ambient': True}, **{'room.ambient': False})
        play.act('move_figure_to_lamp_side', {'figure.position': 'near_screen', 'torch.on': False},
                 **{'figure.position': 'near_torch', 'figure.distance_cm': 25})
        play.act('state_distance_question', {'figure.position': 'near_torch'},
                 **{'investigation.done': True, 'children.hypothesis': 'compare the two distances',
                    'children.cooperation': 1})
    elif scene_id == 'retest':
        play.act('switch_on_for_comparison', {'torch.owner': 'children', 'investigation.done': True},
                 **{'torch.on': True})
        play.act('cast_second_shadow', {'torch.on': True, 'figure.position': 'near_torch'},
                 **_observation_fields(play.state, 'second', 'near_torch'))
        readable = (_readable(play.state['shadow.first_observation'])
                    and _readable(play.state['shadow.second_observation']))
        evidence = 'near_torch' if readable else 'inconclusive'
        lesson = 'near_torch_makes_larger' if readable else 'comparison_too_dim'
        play.act('compare_the_two_readings', {'shadow.first_done': True, 'shadow.second_done': True},
                 **{'shadow.evidence': evidence,
                    'shadow.larger_position': 'near_torch' if readable else '',
                    'children.learned': True, 'children.lesson': lesson})
    elif scene_id == 'ending_show':
        play.act('leave_tested_display_ready', {'label.target': 'near_torch', 'shadow.evidence': 'near_torch'},
                 **{'exhibit.ready': True})
        _return_torch(play)
        _finish(play, 'accurate_demonstration')
    elif scene_id == 'ending_correct_label':
        play.act('correct_reversed_peg_label', {'label.target': 'near_screen', 'shadow.evidence': 'near_torch'},
                 **{'label.target': 'near_torch', 'label.corrected': True,
                    'label.note': 'Lamp-side peg makes the larger shadow.'})
        play.act('leave_corrected_display_ready', {'figure.position': 'near_torch'},
                 **{'exhibit.ready': True})
        _return_torch(play)
        _finish(play, 'corrected_label')
    elif scene_id == 'ending_honest':
        play.act('post_inconclusive_comparison_note', {'shadow.evidence': 'inconclusive'},
                 **{'label.note': 'Today’s shadows were too faint for a fair comparison.',
                    'exhibit.note_posted': True})
        _return_torch(play)
        _finish(play, 'honest_inconclusive')
    else:
        raise StoryError(f'No play implementation for {scene_id}')

    after = deepcopy(play.state)
    return Episode(scene_id, before, after, tuple(deepcopy(play.events)),
                   render(scene_id, params, before, after))


def _return_torch(play):
    play.act('switch_off_and_return_borrowed_torch',
             {'torch.owner': 'children', 'torch.on': True, 'torch.borrowed': True},
             **{'torch.on': False, 'torch.owner': 'museum', 'torch.location': 'return_desk',
                'torch.last_use': 'paired comparison'})


def _finish(play, outcome):
    play.act('give_attendant_the_result_and_finish', {'torch.owner': 'museum', 'torch.on': False},
             **{'story.ended': True, 'story.outcome': outcome, 'staff.received_result': outcome})


def _episode_dict(episode):
    return {
        'id': episode.id, 'before': deepcopy(episode.before), 'after': deepcopy(episode.after),
        'events': deepcopy(list(episode.events)), 'text': episode.text,
    }


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
    budget = 1000

    def search(state, path):
        nonlocal attempts
        remaining = count - len(path)
        if remaining == 0:
            return path if state['story.ended'] else None
        if remaining < 0:
            return None
        used = {episode.id for episode in path}
        candidates = [scene_id for scene_id in SCENES
                      if scene_id not in used and guard(scene_id, state)
                      and (not scene_id.startswith('ending_') or remaining == 1)]
        rng.shuffle(candidates)
        for scene_id in candidates:
            attempts += 1
            if attempts > budget:
                raise StoryError(f'Scene search budget exhausted ({budget})')
            episode = play_scene(p, state, scene_id)
            answer = search(episode.after, path + (episode,))
            if answer is not None:
                return answer
        return None

    episodes = search(initial(p), ())
    if episodes is None:
        raise StoryError('No compatible complete route at the requested length')
    story = '\n\n'.join(episode.text for episode in episodes)
    return {
        'seed': seed,
        'parameters': asdict(p),
        'scene_count': count,
        'path': [episode.id for episode in episodes],
        'story': story,
        'episodes': [_episode_dict(episode) for episode in episodes],
        'final_state': deepcopy(episodes[-1].after),
        'search_attempts': attempts,
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise TypeError('replay expects Parameters')
    state = initial(params)
    episodes = []
    for scene_id in path:
        if scene_id in {episode.id for episode in episodes}:
            raise StoryError(f'Scene cannot be repeated: {scene_id}')
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode.after
    return tuple(episodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    parser.add_argument('--params', help='JSON file containing parameter overrides')
    args = parser.parse_args()
    try:
        overrides = json.loads(open(args.params, encoding='utf-8').read()) if args.params else {}
        if not isinstance(overrides, dict):
            raise ValueError('--params must contain a JSON object')
        p = Parameters(**(asdict(parameters(args.seed)) | overrides))
        row = generate(args.seed, count=args.scenes, params=p)
    except (ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(row['story'])


if __name__ == '__main__':
    main()
