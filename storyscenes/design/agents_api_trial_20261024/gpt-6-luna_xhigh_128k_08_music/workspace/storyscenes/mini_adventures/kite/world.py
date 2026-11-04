'''A bounded, replayable community-music-room adventure; no runtime model calls.'''
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .prose import render


@dataclass(frozen=True, kw_only=True)
class Parameters:
    child: str = 'Mara'
    newcomer: str = 'June'
    drum_head_taut: bool = True
    ribbon_length_cm: int = 48
    room_busy: bool = False
    chairs_ready: bool = True

    def __post_init__(self):
        for label, value in (('child', self.child), ('newcomer', self.newcomer)):
            if (not isinstance(value, str) or not 1 <= len(value) <= 24
                    or not value[0].isalpha()
                    or any(not (ch.isalpha() or ch in "-'") for ch in value)):
                raise ValueError(f'{label} must be a short plain name')
        if self.child.casefold() == self.newcomer.casefold():
            raise ValueError('The child and newcomer need distinct names')
        for label in ('drum_head_taut', 'room_busy', 'chairs_ready'):
            if type(getattr(self, label)) is not bool:
                raise ValueError(f'{label} must be boolean')
        if type(self.ribbon_length_cm) is not int or not 10 <= self.ribbon_length_cm <= 80:
            raise ValueError('ribbon_length_cm must be an integer from 10 to 80')


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        drum_head_taut=rng.choice((True, False)),
        ribbon_length_cm=rng.choice((18, 48, 62)),
        room_busy=rng.choice((False, True)),
        chairs_ready=rng.choice((False, True)),
    )


SCENES = (
    'borrow_drum', 'newcomer_arrives', 'make_space', 'ribbon_cue', 'quiet_demo',
    'open_invitation', 'accept_beat', 'pass_for_now', 'duet', 'listening_pattern',
    'ending_duet', 'ending_listening',
)

_STATE_KEYS = {
    'room.location', 'room.busy', 'room.chairs_ready', 'room.ready',
    'child.name', 'child.goal', 'newcomer.name', 'newcomer.present',
    'newcomer.location', 'newcomer.feeling', 'newcomer.choice',
    'newcomer.can_pass', 'newcomer.heard_demo', 'child.invited',
    'child.pressure_free', 'drum.owner', 'drum.location', 'drum.borrowed',
    'drum.head_taut', 'drum.last_use', 'ribbon.length_cm', 'ribbon.location',
    'ribbon.visible', 'vignette.ribbon_done', 'music.lead_done',
    'music.completed', 'music.outcome', 'music.response', 'story.ended',
    'story.outcome',
}


def initial(params):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    state = {
        'room.location': 'community_music_room',
        'room.busy': params.room_busy,
        'room.chairs_ready': params.chairs_ready,
        'room.ready': False,
        'child.name': params.child,
        'child.goal': 'share_music_without_pressure',
        'newcomer.name': params.newcomer,
        'newcomer.present': False,
        'newcomer.location': 'hall',
        'newcomer.feeling': 'not_met',
        'newcomer.choice': 'undecided',
        'newcomer.can_pass': False,
        'newcomer.heard_demo': False,
        'child.invited': False,
        'child.pressure_free': False,
        'drum.owner': 'Ms Vale',
        'drum.location': 'shelf',
        'drum.borrowed': False,
        'drum.head_taut': params.drum_head_taut,
        'drum.last_use': 'unused',
        'ribbon.length_cm': params.ribbon_length_cm,
        'ribbon.location': 'child',
        'ribbon.visible': False,
        'vignette.ribbon_done': False,
        'music.lead_done': False,
        'music.completed': False,
        'music.outcome': '',
        'music.response': '',
        'story.ended': False,
        'story.outcome': '',
    }
    validate(state)
    return state


def _valid_name(value):
    return (isinstance(value, str) and 1 <= len(value) <= 24 and value[0].isalpha()
            and all(ch.isalpha() or ch in "-'" for ch in value))


def validate(state):
    if not isinstance(state, dict) or set(state) != _STATE_KEYS:
        raise StoryError('State keys do not match this adventure')
    for key in ('room.busy', 'room.chairs_ready', 'room.ready', 'newcomer.present',
                'newcomer.can_pass', 'newcomer.heard_demo', 'child.invited',
                'child.pressure_free', 'drum.borrowed', 'drum.head_taut',
                'ribbon.visible', 'vignette.ribbon_done', 'music.lead_done',
                'music.completed', 'story.ended'):
        if type(state[key]) is not bool:
            raise StoryError(f'{key} must be boolean')
    if type(state['ribbon.length_cm']) is not int or not 10 <= state['ribbon.length_cm'] <= 80:
        raise StoryError('Invalid ribbon length')
    for key in ('room.location', 'child.name', 'child.goal', 'newcomer.name',
                'newcomer.location', 'newcomer.feeling', 'newcomer.choice',
                'drum.owner', 'drum.location', 'drum.last_use', 'ribbon.location',
                'music.outcome', 'music.response', 'story.outcome'):
        if not isinstance(state[key], str):
            raise StoryError(f'{key} must be text')
    if not _valid_name(state['child.name']) or not _valid_name(state['newcomer.name']):
        raise StoryError('Invalid character name in state')
    if state['child.name'].casefold() == state['newcomer.name'].casefold():
        raise StoryError('Characters must have distinct names')
    if state['room.location'] != 'community_music_room':
        raise StoryError('The cast must remain in the community music room')
    if state['child.goal'] != 'share_music_without_pressure':
        raise StoryError('The child’s motive changed unexpectedly')
    if state['room.ready'] and (not state['room.chairs_ready'] or not state['newcomer.present']):
        raise StoryError('A welcoming space needs a newcomer and a usable chair')
    if state['newcomer.present']:
        if state['newcomer.location'] != 'room' or state['newcomer.feeling'] == 'not_met':
            raise StoryError('Newcomer presence and location disagree')
    elif state['newcomer.location'] != 'hall' or state['newcomer.feeling'] != 'not_met':
        raise StoryError('An absent newcomer cannot have an in-room state')
    if state['newcomer.feeling'] not in ('not_met', 'hesitant', 'curious', 'at_ease', 'settled', 'content'):
        raise StoryError('Unknown newcomer feeling')
    if state['newcomer.choice'] not in ('undecided', 'join', 'listen'):
        raise StoryError('Unknown response choice')
    if state['child.invited'] != state['child.pressure_free'] or state['child.invited'] != state['newcomer.can_pass']:
        raise StoryError('An invitation must include a genuine option to pass')
    if state['newcomer.choice'] != 'undecided' and not state['child.invited']:
        raise StoryError('The newcomer cannot answer an invitation that was not made')
    if state['newcomer.heard_demo'] and not state['newcomer.present']:
        raise StoryError('A newcomer cannot hear an in-room demonstration from the hall')
    if state['drum.borrowed']:
        if state['drum.owner'] != state['child.name'] or state['drum.location'] != 'child':
            raise StoryError('Borrowed drum ownership and location disagree')
    elif state['drum.owner'] != 'Ms Vale' or state['drum.location'] != 'shelf':
        raise StoryError('The drum must be with its owner or properly borrowed')
    if state['drum.last_use'] not in ('unused', 'demonstration', 'open_call', 'soft_call',
                                      'call_and_response', 'listening_pattern'):
        raise StoryError('Unknown drum use')
    if state['ribbon.location'] not in ('child', 'stand', 'drum_handle'):
        raise StoryError('Unknown ribbon location')
    if state['ribbon.visible'] != (state['ribbon.location'] != 'child'):
        raise StoryError('Ribbon visibility and location disagree')
    if state['music.completed']:
        if not state['music.lead_done']:
            raise StoryError('A completed exchange needs an opening pattern')
        expected = 'duet' if state['newcomer.choice'] == 'join' else 'listening'
        if state['music.outcome'] != expected:
            raise StoryError('Music outcome does not match the newcomer’s choice')
        if not state['music.response']:
            raise StoryError('Completed music needs an enacted response')
    elif state['music.outcome'] or state['music.response']:
        raise StoryError('Unfinished music cannot have a completed outcome')
    if state['story.ended'] != bool(state['story.outcome']):
        raise StoryError('Ending flag and outcome disagree')
    if state['story.ended'] and not (
        state['music.completed'] and not state['drum.borrowed']
        and state['drum.owner'] == 'Ms Vale' and state['drum.location'] == 'shelf'
        and state['ribbon.location'] == 'child' and not state['ribbon.visible']
    ):
        raise StoryError('The ending must return the useful borrowed drum and the ribbon')


def _matches_parameters(params, state):
    if (state['child.name'] != params.child or state['newcomer.name'] != params.newcomer
            or state['drum.head_taut'] != params.drum_head_taut
            or state['ribbon.length_cm'] != params.ribbon_length_cm
            or state['room.busy'] != params.room_busy):
        raise StoryError('Parameters do not match the supplied world state')
    # Chairs are rearranged during play, so their initial setting is not inferable
    # from a later state. It is used only by the make_space scene itself.


def guard(scene_id, state):
    validate(state)
    if scene_id not in SCENES:
        raise StoryError(f'Unknown scene: {scene_id}')
    if state['story.ended']:
        return False
    if scene_id == 'borrow_drum':
        return not state['drum.borrowed'] and not state['child.invited']
    if scene_id == 'newcomer_arrives':
        return state['drum.borrowed'] and not state['newcomer.present']
    if scene_id == 'make_space':
        return state['newcomer.present'] and not state['room.ready']
    if scene_id == 'ribbon_cue':
        return (state['room.ready'] and not state['child.invited']
                and not state['vignette.ribbon_done'] and state['ribbon.location'] == 'child')
    if scene_id == 'quiet_demo':
        return (state['room.ready'] and not state['child.invited']
                and not state['newcomer.heard_demo'] and state['drum.borrowed'])
    if scene_id == 'open_invitation':
        return state['room.ready'] and not state['child.invited']
    if scene_id == 'accept_beat':
        return (state['child.invited'] and state['newcomer.choice'] == 'undecided'
                and (not state['room.busy'] or state['ribbon.visible'] or state['newcomer.heard_demo']))
    if scene_id == 'pass_for_now':
        return state['child.invited'] and state['newcomer.choice'] == 'undecided'
    if scene_id == 'duet':
        return state['newcomer.choice'] == 'join' and not state['music.completed']
    if scene_id == 'listening_pattern':
        return state['newcomer.choice'] == 'listen' and not state['music.completed']
    if scene_id == 'ending_duet':
        return (state['music.completed'] and state['music.outcome'] == 'duet'
                and state['drum.borrowed'] and not state['story.ended'])
    if scene_id == 'ending_listening':
        return (state['music.completed'] and state['music.outcome'] == 'listening'
                and state['drum.borrowed'] and not state['story.ended'])
    return False


def _episode(scene_id, params, before, play):
    after = deepcopy(play.state)
    validate(after)
    text = render(scene_id, params, before, after)
    word_count = len(text.split())
    if not 40 <= word_count <= 70:
        raise StoryError(f'{scene_id} prose has {word_count} words; expected 40 to 70')
    if not play.events:
        raise StoryError(f'{scene_id} enacted no local action')
    return {
        'id': scene_id,
        'before': deepcopy(before),
        'after': after,
        'events': deepcopy(play.events),
        'text': text,
    }


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    validate(state)
    _matches_parameters(params, state)
    if not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    before = deepcopy(state)
    x = LocalPlay(state, actors=(params.child, params.newcomer, 'Ms Vale'), validate=validate)

    if scene_id == 'borrow_drum':
        x.act('ask_to_borrow', {'drum.owner': 'Ms Vale', 'drum.location': 'shelf'}, **{
            'drum.owner': params.child, 'drum.location': 'child', 'drum.borrowed': True})
    elif scene_id == 'newcomer_arrives':
        x.act('welcome_without_closing_the_door', {'drum.borrowed': True}, **{
            'newcomer.present': True, 'newcomer.location': 'room', 'newcomer.feeling': 'hesitant'})
    elif scene_id == 'make_space':
        if x.state['room.chairs_ready']:
            x.act('leave_an_open_chair', {'newcomer.present': True, 'room.ready': False}, **{
                'room.ready': True})
        else:
            x.act('move_a_stool_into_the_circle', {'newcomer.present': True, 'room.ready': False,
                                                   'room.chairs_ready': False}, **{
                'room.chairs_ready': True, 'room.ready': True})
    elif scene_id == 'ribbon_cue':
        location = 'stand' if x.state['ribbon.length_cm'] >= 35 else 'drum_handle'
        action = 'drape_ribbon_on_stand' if location == 'stand' else 'loop_short_ribbon_on_handle'
        x.act(action, {'ribbon.location': 'child', 'vignette.ribbon_done': False}, **{
            'ribbon.location': location, 'ribbon.visible': True, 'vignette.ribbon_done': True})
    elif scene_id == 'quiet_demo':
        x.act('play_one_unasked_for_beat', {'newcomer.present': True, 'drum.borrowed': True,
                                            'newcomer.heard_demo': False}, **{
            'newcomer.heard_demo': True, 'drum.last_use': 'demonstration'})
    elif scene_id == 'open_invitation':
        x.act('offer_choices_without_a_demand', {'room.ready': True, 'child.invited': False}, **{
            'child.invited': True, 'child.pressure_free': True, 'newcomer.can_pass': True})
    elif scene_id == 'accept_beat':
        requirements = {'child.invited': True, 'newcomer.choice': 'undecided'}
        if x.state['room.busy']:
            requirements['room.busy'] = True
            if x.state['ribbon.visible']:
                requirements['ribbon.visible'] = True
            else:
                requirements['newcomer.heard_demo'] = True
        else:
            requirements['room.busy'] = False
        x.act('choose_one_beat', requirements, **{
            'newcomer.choice': 'join', 'newcomer.feeling': 'curious'})
    elif scene_id == 'pass_for_now':
        x.act('choose_listening_instead', {'child.invited': True, 'newcomer.can_pass': True,
                                           'newcomer.choice': 'undecided'}, **{
            'newcomer.choice': 'listen', 'newcomer.feeling': 'at_ease'})
    elif scene_id == 'duet':
        action = 'play_open_call' if x.state['drum.head_taut'] else 'tap_a_soft_call'
        use = 'open_call' if x.state['drum.head_taut'] else 'soft_call'
        x.act(action, {'drum.borrowed': True, 'newcomer.choice': 'join'}, **{
            'music.lead_done': True, 'drum.last_use': use})
        x.act('answer_with_one_beat', {'music.lead_done': True, 'newcomer.choice': 'join'}, **{
            'music.completed': True, 'music.outcome': 'duet',
            'music.response': 'one beat', 'drum.last_use': 'call_and_response',
            'newcomer.feeling': 'settled'})
    elif scene_id == 'listening_pattern':
        x.act('play_a_pattern_for_listening', {'drum.borrowed': True, 'newcomer.choice': 'listen'}, **{
            'music.lead_done': True, 'drum.last_use': 'listening_pattern'})
        x.act('name_the_sound_together', {'music.lead_done': True, 'newcomer.choice': 'listen'}, **{
            'music.completed': True, 'music.outcome': 'listening',
            'music.response': 'rain', 'newcomer.feeling': 'content'})
    else:
        if x.state['ribbon.visible']:
            x.act('retrieve_ribbon', {'ribbon.visible': True}, **{
                'ribbon.location': 'child', 'ribbon.visible': False})
        x.act('return_the_borrowed_drum', {'drum.borrowed': True, 'drum.owner': params.child}, **{
            'drum.owner': 'Ms Vale', 'drum.location': 'shelf', 'drum.borrowed': False})
        outcome = 'a freely chosen duet' if scene_id == 'ending_duet' else 'a welcome without a duet'
        x.act('finish_with_the_music_shared', {'drum.borrowed': False, 'music.completed': True}, **{
            'story.ended': True, 'story.outcome': outcome})

    return _episode(scene_id, params, before, x)


def _minimum_remaining(state):
    if state['story.ended']:
        return 0
    if not state['drum.borrowed']:
        return 7
    if not state['newcomer.present']:
        return 6
    if not state['room.ready']:
        return 5
    if not state['child.invited']:
        return 4
    if state['newcomer.choice'] == 'undecided':
        return 3
    if not state['music.completed']:
        return 2
    return 1


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    p = parameters(seed) if params is None else params
    if not isinstance(p, Parameters):
        raise ValueError('params must be a Parameters instance')
    rng = random.Random(seed)
    attempts = 0
    budget = 5000

    def search(state, episodes):
        nonlocal attempts
        remaining = count - len(episodes)
        if remaining < _minimum_remaining(state):
            return None
        if state['story.ended']:
            return episodes if remaining == 0 else None
        if remaining == 0:
            return None
        used = {episode['id'] for episode in episodes}
        choices = [scene_id for scene_id in SCENES
                   if scene_id not in used and guard(scene_id, state)
                   and (not scene_id.startswith('ending_') or remaining == 1)]
        rng.shuffle(choices)
        for scene_id in choices:
            attempts += 1
            if attempts > budget:
                raise StoryError(f'Scene search budget exhausted ({budget} attempts)')
            episode = play_scene(p, state, scene_id)
            answer = search(episode['after'], episodes + (episode,))
            if answer is not None:
                return answer
        return None

    episodes = search(initial(p), ())
    if episodes is None:
        raise StoryError('No compatible route at the requested length')
    return {
        'seed': seed,
        'parameters': asdict(p),
        'scene_count': count,
        'path': [episode['id'] for episode in episodes],
        'story': '\n\n'.join(episode['text'] for episode in episodes),
        'episodes': [deepcopy(episode) for episode in episodes],
        'final_state': deepcopy(episodes[-1]['after']),
        'search_attempts': attempts,
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    if not isinstance(path, (list, tuple)) or len(path) not in (7, 8):
        raise StoryError('Replay requires a seven- or eight-scene path')
    if len(set(path)) != len(path):
        raise StoryError('A scene cannot be repeated')
    state = initial(params)
    episodes = []
    for scene_id in path:
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode['after']
    if not state['story.ended']:
        raise StoryError('Replay path did not reach an ending')
    return episodes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    parser.add_argument('--params', type=Path, help='JSON file of parameter overrides')
    args = parser.parse_args()
    overrides = json.loads(args.params.read_text(encoding='utf-8')) if args.params else {}
    if not isinstance(overrides, dict):
        parser.error('--params must contain a JSON object')
    p = Parameters(**(asdict(parameters(args.seed)) | overrides))
    print(generate(args.seed, count=args.scenes, params=p)['story'])


if __name__ == '__main__':
    main()
