'''Bounded, offline village-festival adventure with atomic local plays.'''
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import random

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError

from .prose import render


@dataclass(frozen=True, kw_only=True)
class Parameters:
    spool_length_cm: int = 240
    gusty: bool = False
    rainy: bool = False
    posts_sturdy: bool = True
    jo_reach_cm: int = 70
    knot_slips: bool = False

    def __post_init__(self):
        if type(self.spool_length_cm) is not int or not 100 <= self.spool_length_cm <= 320:
            raise ValueError('spool_length_cm must be an integer from 100 through 320')
        if type(self.jo_reach_cm) is not int or not 45 <= self.jo_reach_cm <= 100:
            raise ValueError('jo_reach_cm must be an integer from 45 through 100')
        for name in ('gusty', 'rainy', 'posts_sturdy', 'knot_slips'):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f'{name} must be a boolean')


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        spool_length_cm=rng.choice((120, 180, 220, 260)),
        gusty=rng.choice((False, True)),
        rainy=rng.choice((False, True)),
        posts_sturdy=rng.choice((True, True, False)),
        jo_reach_cm=rng.choice((50, 65, 80)),
        knot_slips=rng.choice((False, True)),
    )


SCENES = (
    'borrow_spool', 'meet_neighbor', 'color_vignette', 'knot_vignette',
    'choose_layout', 'hang_bunting', 'welcome', 'return_spool',
    'ending_square', 'ending_hall',
)


_BOOL_KEYS = {
    'story.ended', 'festival.open', 'Jo.met', 'Jo.invited', 'Jo.helped',
    'Jo.welcomed', 'Jo.chose_colors', 'spool.borrowed', 'spool.returned',
    'bunting.colors_chosen', 'bunting.hung', 'weather.gusty', 'weather.rainy',
    'anchors.sturdy', 'knot.slips', 'knot.secure', 'knot.practiced',
    'knot.reinforced', 'layout.chosen', 'community.welcomed',
}
_INT_KEYS = {
    'Jo.reach_cm', 'Jo.trust', 'spool.length_cm', 'spool.remaining_cm',
    'spool.used_cm', 'layout.height_cm', 'string.display_cm',
}


def initial(params):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    state = {
        'story.ended': False,
        'story.outcome': '',
        'festival.place': 'square',
        'festival.open': False,
        'Leni.location': 'square',
        'Leni.goal': 'welcome_the_new_neighbor',
        'Jo.location': 'square',
        'Jo.met': False,
        'Jo.invited': False,
        'Jo.reach_cm': params.jo_reach_cm,
        'Jo.helped': False,
        'Jo.welcomed': False,
        'Jo.trust': 0,
        'Jo.chose_colors': False,
        'spool.owner': 'Mrs Bell',
        'spool.holder': 'Mrs Bell',
        'spool.location': 'bell_shed',
        'spool.borrowed': False,
        'spool.returned': False,
        'spool.length_cm': params.spool_length_cm,
        'spool.remaining_cm': params.spool_length_cm,
        'spool.used_cm': 0,
        'bunting.location': 'basket:square',
        'bunting.pattern': 'red-and-white',
        'bunting.colors_chosen': False,
        'bunting.hung': False,
        'weather.gusty': params.gusty,
        'weather.rainy': params.rainy,
        'anchors.sturdy': params.posts_sturdy,
        'knot.slips': params.knot_slips,
        'knot.secure': not params.knot_slips,
        'knot.practiced': False,
        'knot.reinforced': False,
        'layout.chosen': False,
        'layout.mode': 'none',
        'layout.height_cm': 0,
        'string.display_cm': 0,
        'community.welcomed': False,
    }
    validate(state)
    return state


def validate(state):
    if not isinstance(state, dict):
        raise StoryError('State must be a dictionary')
    expected = _BOOL_KEYS | _INT_KEYS | {
        'story.outcome', 'festival.place', 'Leni.location', 'Leni.goal', 'Jo.location',
        'spool.owner', 'spool.holder', 'spool.location', 'bunting.location',
        'bunting.pattern', 'layout.mode',
    }
    if set(state) != expected:
        raise StoryError('State keys do not match the village-festival world')
    for key in _BOOL_KEYS:
        if type(state[key]) is not bool:
            raise StoryError(f'{key} must be boolean')
    for key in _INT_KEYS:
        if type(state[key]) is not int:
            raise StoryError(f'{key} must be an integer')
    for key in expected - _BOOL_KEYS - _INT_KEYS:
        if not isinstance(state[key], str):
            raise StoryError(f'{key} must be a string')

    if state['festival.place'] not in ('square', 'hall'):
        raise StoryError('Unknown festival location')
    if state['Leni.location'] != state['festival.place'] or state['Jo.location'] != state['festival.place']:
        raise StoryError('The children and the festival display must share a location')
    if state['Jo.reach_cm'] not in range(45, 101) or state['Jo.trust'] not in range(4):
        raise StoryError('Invalid neighbor reach or trust')
    if not 100 <= state['spool.length_cm'] <= 320:
        raise StoryError('Invalid spool length')
    if not 0 <= state['spool.remaining_cm'] <= state['spool.length_cm']:
        raise StoryError('Invalid remaining string')
    if state['spool.remaining_cm'] + state['spool.used_cm'] != state['spool.length_cm']:
        raise StoryError('String must be conserved')
    if state['spool.owner'] != 'Mrs Bell':
        raise StoryError('The spool remains Mrs Bell’s property')
    if not state['spool.borrowed']:
        if (state['spool.holder'], state['spool.location'], state['spool.returned'], state['spool.used_cm']) != (
                'Mrs Bell', 'bell_shed', False, 0):
            raise StoryError('Unborrowed spool has inconsistent custody')
    elif state['spool.returned']:
        if (state['spool.holder'], state['spool.location']) != ('Mrs Bell', 'bell_shed'):
            raise StoryError('Returned spool has inconsistent custody')
    elif (state['spool.holder'], state['spool.location']) != ('Leni', 'Leni'):
        raise StoryError('Borrowed spool must remain with Leni until returned')
    if state['spool.returned'] and not state['spool.borrowed']:
        raise StoryError('A spool cannot be returned before it is borrowed')

    if state['bunting.pattern'] not in ('red-and-white', 'blue-and-gold'):
        raise StoryError('Unknown bunting pattern')
    if state['Jo.chose_colors'] != state['bunting.colors_chosen']:
        raise StoryError('Color choice must belong to Jo and the bunting together')
    if state['bunting.colors_chosen'] != (state['bunting.pattern'] == 'blue-and-gold'):
        raise StoryError('Chosen colors and displayed pattern disagree')
    if state['bunting.location'] not in ('basket:square', 'basket:hall', 'square_line', 'hall_rail'):
        raise StoryError('Unknown bunting location')

    if state['knot.secure'] != (not state['knot.slips'] or state['knot.reinforced']):
        raise StoryError('Knot security must follow its material and reinforcement')
    if state['knot.practiced'] and not state['knot.reinforced']:
        raise StoryError('A practiced knot must be reinforced')
    expected_used = (10 if state['knot.practiced'] else 0) + state['string.display_cm']
    if state['spool.used_cm'] != expected_used:
        raise StoryError('Practice and display string use must be accounted for')

    if state['layout.mode'] not in ('none', 'square', 'hall'):
        raise StoryError('Unknown display layout')
    if not state['layout.chosen']:
        if (state['layout.mode'], state['layout.height_cm'], state['festival.place']) != ('none', 0, 'square'):
            raise StoryError('Unchosen layout has moved or placed the display')
    elif state['layout.mode'] == 'square':
        available = state['spool.length_cm'] - (10 if state['knot.practiced'] else 0)
        if (state['festival.place'] != 'square' or state['layout.height_cm'] != 55
                or state['weather.gusty'] or state['weather.rainy'] or not state['anchors.sturdy']
                or state['Jo.reach_cm'] < 55 or available < 180 or not state['knot.secure']):
            raise StoryError('Square layout is not physically safe and reachable')
    elif state['layout.mode'] == 'hall':
        available = state['spool.length_cm'] - (10 if state['knot.practiced'] else 0)
        if state['festival.place'] != 'hall' or state['layout.height_cm'] != 35 or available < 80:
            raise StoryError('Hall layout is not physically reachable or supplied')

    if not state['bunting.hung']:
        if state['Jo.helped'] or state['string.display_cm'] != 0:
            raise StoryError('Unhung bunting cannot already be in use')
        expected_location = 'basket:hall' if state['layout.mode'] == 'hall' else 'basket:square'
        if state['bunting.location'] != expected_location:
            raise StoryError('Bunting basket location does not follow the selected layout')
    else:
        expected_location = 'square_line' if state['layout.mode'] == 'square' else 'hall_rail'
        expected_length = 180 if state['layout.mode'] == 'square' else 80
        if (not state['layout.chosen'] or state['bunting.location'] != expected_location
                or state['string.display_cm'] != expected_length or not state['Jo.helped']
                or not state['knot.secure'] or state['Jo.reach_cm'] < state['layout.height_cm']):
            raise StoryError('Hung bunting must be secure, accounted for, and reachable')

    if state['Jo.met'] != state['Jo.invited']:
        raise StoryError('Jo’s meeting and invitation must agree')
    if state['Jo.helped'] and not state['Jo.met']:
        raise StoryError('Jo cannot help before meeting Leni')
    if state['Jo.welcomed'] != state['festival.open'] or state['community.welcomed'] != state['festival.open']:
        raise StoryError('The public welcome must match the open festival')
    if state['festival.open'] and (not state['bunting.hung'] or not state['Jo.helped']):
        raise StoryError('The festival cannot open before the shared display is ready')
    if state['Leni.goal'] != ('fulfilled' if state['festival.open'] else 'welcome_the_new_neighbor'):
        raise StoryError('Leni’s goal must reflect the completed welcome')
    if state['story.ended']:
        expected_outcome = 'shared_square' if state['layout.mode'] == 'square' else 'sheltered_hall'
        if (not state['festival.open'] or not state['spool.returned']
                or state['story.outcome'] != expected_outcome):
            raise StoryError('Ending requires a completed welcome and returned spool')
    elif state['story.outcome']:
        raise StoryError('An unfinished story has no outcome')


def _square_is_safe(state):
    available = state['spool.remaining_cm']
    return (not state['weather.rainy'] and not state['weather.gusty']
            and state['anchors.sturdy'] and state['Jo.reach_cm'] >= 55
            and available >= 180 and state['knot.secure'])


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f'Unknown scene: {scene_id}')
    validate(state)
    if state['story.ended']:
        return False
    if scene_id == 'borrow_spool':
        return not state['spool.borrowed']
    if scene_id == 'meet_neighbor':
        return state['spool.borrowed'] and not state['Jo.met']
    if scene_id == 'color_vignette':
        return state['Jo.invited'] and not state['layout.chosen'] and not state['Jo.chose_colors']
    if scene_id == 'knot_vignette':
        return state['Jo.invited'] and not state['layout.chosen'] and not state['knot.practiced']
    if scene_id == 'choose_layout':
        return state['Jo.invited'] and not state['layout.chosen']
    if scene_id == 'hang_bunting':
        return state['layout.chosen'] and not state['bunting.hung']
    if scene_id == 'welcome':
        return state['bunting.hung'] and not state['festival.open']
    if scene_id == 'return_spool':
        return state['festival.open'] and state['spool.borrowed'] and not state['spool.returned']
    if scene_id == 'ending_square':
        return state['spool.returned'] and state['layout.mode'] == 'square'
    if scene_id == 'ending_hall':
        return state['spool.returned'] and state['layout.mode'] == 'hall'
    return False


@dataclass(frozen=True, kw_only=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    validate(state)
    if not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    x = LocalPlay(state, actors=('Leni', 'Jo'), validate=validate)

    if scene_id == 'borrow_spool':
        x.act('borrow_spool', {
            'spool.owner': 'Mrs Bell', 'spool.holder': 'Mrs Bell',
            'spool.borrowed': False, 'spool.location': 'bell_shed',
        }, **{
            'spool.holder': 'Leni', 'spool.location': 'Leni', 'spool.borrowed': True,
        })

    elif scene_id == 'meet_neighbor':
        x.act('invite_jo_to_choose', {
            'spool.borrowed': True, 'Jo.met': False, 'Jo.invited': False,
        }, **{'Jo.met': True, 'Jo.invited': True, 'Jo.trust': 1})

    elif scene_id == 'color_vignette':
        x.act('jo_chooses_colors', {
            'Jo.invited': True, 'Jo.chose_colors': False,
            'bunting.pattern': 'red-and-white',
        }, **{
            'Jo.chose_colors': True, 'bunting.colors_chosen': True,
            'bunting.pattern': 'blue-and-gold',
        })

    elif scene_id == 'knot_vignette':
        remaining = x.state['spool.remaining_cm'] - 10
        used = x.state['spool.used_cm'] + 10
        x.act('practice_and_reinforce_knot', {
            'spool.holder': 'Leni', 'knot.practiced': False,
        }, **{
            'spool.remaining_cm': remaining, 'spool.used_cm': used,
            'knot.practiced': True, 'knot.reinforced': True, 'knot.secure': True,
        })

    elif scene_id == 'choose_layout':
        if _square_is_safe(x.state):
            x.act('choose_reachable_square_line', {
                'festival.place': 'square', 'layout.chosen': False,
                'weather.rainy': False, 'weather.gusty': False,
                'anchors.sturdy': True, 'knot.secure': True,
                'Jo.reach_cm': x.state['Jo.reach_cm'],
                'spool.remaining_cm': x.state['spool.remaining_cm'],
            }, **{
                'layout.chosen': True, 'layout.mode': 'square', 'layout.height_cm': 55,
            })
        else:
            x.act('carry_basket_and_people_to_hall', {
                'festival.place': 'square', 'layout.chosen': False,
                'bunting.location': 'basket:square',
            }, **{
                'festival.place': 'hall', 'Leni.location': 'hall', 'Jo.location': 'hall',
                'bunting.location': 'basket:hall',
            })
            x.act('choose_reachable_sheltered_rail', {
                'festival.place': 'hall', 'layout.chosen': False,
            }, **{'layout.chosen': True, 'layout.mode': 'hall', 'layout.height_cm': 35})

    elif scene_id == 'hang_bunting':
        if x.state['layout.mode'] == 'hall' and not x.state['knot.secure']:
            x.act('make_double_rail_hitch', {
                'layout.mode': 'hall', 'knot.secure': False,
            }, **{'knot.secure': True, 'knot.reinforced': True})
        length = 180 if x.state['layout.mode'] == 'square' else 80
        remaining = x.state['spool.remaining_cm'] - length
        used = x.state['spool.used_cm'] + length
        location = 'square_line' if x.state['layout.mode'] == 'square' else 'hall_rail'
        x.act('hang_bunting_with_jo', {
            'layout.chosen': True, 'bunting.hung': False,
            'spool.borrowed': True, 'spool.holder': 'Leni',
            'knot.secure': True, 'bunting.location': x.state['bunting.location'],
            'Jo.location': x.state['festival.place'],
        }, **{
            'bunting.location': location, 'bunting.hung': True,
            'string.display_cm': length, 'spool.remaining_cm': remaining,
            'spool.used_cm': used, 'Jo.helped': True, 'Jo.trust': 2,
        })

    elif scene_id == 'welcome':
        x.act('open_shared_welcome', {
            'bunting.hung': True, 'Jo.helped': True,
            'festival.open': False, 'Jo.welcomed': False,
        }, **{
            'festival.open': True, 'Jo.welcomed': True,
            'community.welcomed': True, 'Leni.goal': 'fulfilled', 'Jo.trust': 3,
        })

    elif scene_id == 'return_spool':
        x.act('return_spool_to_mrs_bell', {
            'spool.owner': 'Mrs Bell', 'spool.holder': 'Leni',
            'spool.borrowed': True, 'spool.returned': False,
            'festival.open': True,
        }, **{
            'spool.holder': 'Mrs Bell', 'spool.location': 'bell_shed', 'spool.returned': True,
        })

    elif scene_id in ('ending_square', 'ending_hall'):
        outcome = 'shared_square' if scene_id == 'ending_square' else 'sheltered_hall'
        x.act('complete_welcome', {
            'festival.open': True, 'spool.returned': True,
            'story.ended': False, 'story.outcome': '',
        }, **{'story.ended': True, 'story.outcome': outcome})

    after = deepcopy(x.state)
    return Episode(
        id=scene_id,
        before=deepcopy(state),
        after=after,
        events=tuple(deepcopy(x.events)),
        text=render(scene_id, params, state, after),
    )


def _minimum_remaining(state):
    return sum((
        not state['spool.borrowed'],
        not state['Jo.met'],
        not state['layout.chosen'],
        not state['bunting.hung'],
        not state['festival.open'],
        not state['spool.returned'],
        not state['story.ended'],
    ))


def _episode_dict(episode):
    return {
        'id': episode.id,
        'before': deepcopy(episode.before),
        'after': deepcopy(episode.after),
        'events': [deepcopy(event) for event in episode.events],
        'text': episode.text,
    }


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('This adventure supports exactly seven or eight scenes')
    p = params if params is not None else parameters(seed)
    if not isinstance(p, Parameters):
        raise TypeError('params must be a Parameters instance')
    start = initial(p)
    rng = random.Random(seed)
    attempts = 0

    def search(state, episodes):
        nonlocal attempts
        remaining = count - len(episodes)
        if remaining < _minimum_remaining(state):
            return None
        if remaining == 0:
            return episodes if state['story.ended'] else None
        candidates = [scene_id for scene_id in SCENES if guard(scene_id, state)]
        rng.shuffle(candidates)
        for scene_id in candidates:
            if scene_id.startswith('ending_') and remaining != 1:
                continue
            attempts += 1
            if attempts > 5000:
                raise StoryError('Scene search budget exhausted')
            episode = play_scene(p, state, scene_id)
            if remaining - 1 < _minimum_remaining(episode.after):
                continue
            result = search(episode.after, episodes + (episode,))
            if result is not None:
                return result
        return None

    episodes = search(start, ())
    if episodes is None:
        raise StoryError('No compatible complete route at the requested length')
    episode_rows = [_episode_dict(episode) for episode in episodes]
    return {
        'seed': seed,
        'parameters': asdict(p),
        'scene_count': count,
        'path': [episode.id for episode in episodes],
        'story': '\n\n'.join(episode.text for episode in episodes),
        'episodes': episode_rows,
        'final_state': deepcopy(episodes[-1].after),
        'search_attempts': attempts,
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    if isinstance(path, (str, bytes)):
        raise TypeError('path must be a sequence of scene IDs')
    state = initial(params)
    episodes = []
    for scene_id in path:
        if scene_id in {episode.id for episode in episodes}:
            raise StoryError('A scene cannot be repeated')
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode.after
    return tuple(episodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    args = parser.parse_args()
    row = generate(args.seed, count=args.scenes)
    print(row['story'])


if __name__ == '__main__':
    main()
