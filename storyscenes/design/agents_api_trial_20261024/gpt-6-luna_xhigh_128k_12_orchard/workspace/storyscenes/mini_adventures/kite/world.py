'''Bounded, deterministic local-play adventure set in a small pear orchard.'''
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
    reach_cm: int = 160
    windy: bool = False
    low_ripe: int = 3
    windfalls: int = 1
    basket_handle: str = 'sound'
    crate_level: bool = True

    def __post_init__(self):
        if type(self.reach_cm) is not int or not 100 <= self.reach_cm <= 190:
            raise ValueError('reach_cm must be an integer from 100 through 190')
        if type(self.windy) is not bool:
            raise ValueError('windy must be a boolean')
        if type(self.low_ripe) is not int or not 1 <= self.low_ripe <= 4:
            raise ValueError('low_ripe must be an integer from 1 through 4')
        if type(self.windfalls) is not int or not 1 <= self.windfalls <= 3:
            raise ValueError('windfalls must be an integer from 1 through 3')
        if self.basket_handle not in ('sound', 'frayed') or not isinstance(self.basket_handle, str):
            raise ValueError('basket_handle must be sound or frayed')
        if type(self.crate_level) is not bool:
            raise ValueError('crate_level must be a boolean')


SCENES = (
    'borrow_basket', 'vignette_crate', 'vignette_memory', 'survey_tree',
    'choose_harvest', 'pick_fruit', 'share_snack', 'ending_full', 'ending_small',
)
MAX_SCENE_ATTEMPTS = 8

_STATE_KEYS = (
    'story.location', 'story.ended', 'story.outcome', 'mira.want', 'theo.want',
    'friends.memory', 'friends.shared', 'basket.borrowed', 'basket.returned',
    'basket.owner', 'basket.location', 'basket.handle', 'basket.capacity',
    'basket.load', 'basket.cleaned', 'crate.level', 'crate.tested',
    'crate.location', 'crate.used_as_table', 'picnic.surface', 'tree.reach_cm',
    'tree.windy', 'tree.low_ripe', 'tree.windfalls', 'tree.surveyed',
    'tree.safe_reach', 'tree.remaining_low', 'tree.picked_low',
    'tree.gathered_ground', 'tree.damaged', 'harvest.plan', 'harvest.count',
    'harvest.source', 'snack.done', 'snack.pear_halves', 'param.reach_cm',
    'param.windy', 'param.low_ripe', 'param.windfalls', 'param.basket_handle',
    'param.crate_level',
)


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        reach_cm=rng.choice((120, 145, 160, 175)),
        windy=rng.choice((False, True)),
        low_ripe=rng.choice((1, 2, 3, 4)),
        windfalls=rng.choice((1, 2, 3)),
        basket_handle=rng.choice(('sound', 'frayed')),
        crate_level=rng.choice((True, False)),
    )


def initial(params):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    state = {
        'story.location': 'shed_gate', 'story.ended': False, 'story.outcome': '',
        'mira.want': 'share a pear snack', 'theo.want': 'leave the tree unharmed',
        'friends.memory': False, 'friends.shared': False,
        'basket.borrowed': False, 'basket.returned': False, 'basket.owner': 'Vale',
        'basket.location': 'shed', 'basket.handle': params.basket_handle,
        'basket.capacity': 3 if params.basket_handle == 'sound' else 1,
        'basket.load': 0, 'basket.cleaned': False,
        'crate.level': params.crate_level, 'crate.tested': False,
        'crate.location': 'orchard_edge', 'crate.used_as_table': False,
        'picnic.surface': 'cloth',
        'tree.reach_cm': params.reach_cm, 'tree.windy': params.windy,
        'tree.low_ripe': params.low_ripe, 'tree.windfalls': params.windfalls,
        'tree.surveyed': False, 'tree.safe_reach': False,
        'tree.remaining_low': params.low_ripe, 'tree.picked_low': 0,
        'tree.gathered_ground': 0, 'tree.damaged': False,
        'harvest.plan': '', 'harvest.count': 0, 'harvest.source': '',
        'snack.done': False, 'snack.pear_halves': 0,
        'param.reach_cm': params.reach_cm, 'param.windy': params.windy,
        'param.low_ripe': params.low_ripe, 'param.windfalls': params.windfalls,
        'param.basket_handle': params.basket_handle, 'param.crate_level': params.crate_level,
    }
    validate(state)
    return state


def validate(state):
    if not isinstance(state, dict) or set(state) != set(_STATE_KEYS):
        raise StoryError('State must contain exactly the declared orchard keys')
    for key, value in state.items():
        if type(value) not in (str, bool, int):
            raise StoryError(f'Non-JSON scalar state at {key}')

    bool_keys = (
        'story.ended', 'friends.memory', 'friends.shared', 'basket.borrowed',
        'basket.returned', 'basket.cleaned', 'crate.level', 'crate.tested',
        'crate.used_as_table', 'tree.windy', 'tree.surveyed', 'tree.safe_reach',
        'tree.damaged', 'snack.done', 'param.windy', 'param.crate_level',
    )
    int_keys = (
        'basket.capacity', 'basket.load', 'tree.reach_cm', 'tree.low_ripe',
        'tree.windfalls', 'tree.remaining_low', 'tree.picked_low',
        'tree.gathered_ground', 'harvest.count', 'snack.pear_halves',
        'param.reach_cm', 'param.low_ripe', 'param.windfalls',
    )
    for key in bool_keys:
        if type(state[key]) is not bool:
            raise StoryError(f'{key} must be boolean')
    for key in int_keys:
        if type(state[key]) is not int:
            raise StoryError(f'{key} must be an integer')

    if state['story.location'] not in ('shed_gate', 'orchard', 'tree', 'picnic'):
        raise StoryError('Unknown party location')
    if state['mira.want'] != 'share a pear snack' or state['theo.want'] != 'leave the tree unharmed':
        raise StoryError('Character motives cannot change in this adventure')
    if state['basket.owner'] not in ('Vale', 'friends') or state['basket.handle'] not in ('sound', 'frayed'):
        raise StoryError('Invalid basket state')
    if state['basket.capacity'] != (3 if state['basket.handle'] == 'sound' else 1):
        raise StoryError('Basket capacity disagrees with its handle')
    if state['crate.location'] not in ('orchard_edge', 'sorting_table', 'left_by_path'):
        raise StoryError('Unknown crate location')
    if state['picnic.surface'] not in ('cloth', 'crate'):
        raise StoryError('Unknown snack surface')

    if not 100 <= state['tree.reach_cm'] <= 190:
        raise StoryError('Reach is outside its validated range')
    if not 1 <= state['tree.low_ripe'] <= 4 or not 1 <= state['tree.windfalls'] <= 3:
        raise StoryError('Fruit counts are outside their validated ranges')
    for parameter_key, tree_key in (
        ('param.reach_cm', 'tree.reach_cm'), ('param.windy', 'tree.windy'),
        ('param.low_ripe', 'tree.low_ripe'), ('param.windfalls', 'tree.windfalls'),
        ('param.basket_handle', 'basket.handle'), ('param.crate_level', 'crate.level'),
    ):
        if state[parameter_key] != state[tree_key]:
            raise StoryError(f'Parameter and physical state disagree: {parameter_key}')

    if state['basket.load'] < 0 or state['basket.load'] > state['basket.capacity']:
        raise StoryError('Basket load exceeds its safe capacity')
    if state['tree.damaged']:
        raise StoryError('The tree must remain undamaged')
    if state['tree.remaining_low'] + state['tree.picked_low'] != state['tree.low_ripe']:
        raise StoryError('Low pears must be conserved')
    if not 0 <= state['tree.gathered_ground'] <= state['tree.windfalls']:
        raise StoryError('Windfalls must be conserved')

    if not state['tree.surveyed']:
        if state['tree.safe_reach'] or state['tree.picked_low'] or state['tree.gathered_ground']:
            raise StoryError('Fruit cannot be selected before the survey')
    elif state['tree.safe_reach'] != (not state['tree.windy'] and state['tree.reach_cm'] >= 145):
        raise StoryError('Safe reach disagrees with the observed wind and reach')

    plan = state['harvest.plan']
    if plan not in ('', 'low_branch', 'windfalls'):
        raise StoryError('Unknown harvest plan')
    if plan and (not state['tree.surveyed'] or plan != ('low_branch' if state['tree.safe_reach'] else 'windfalls')):
        raise StoryError('Harvest plan does not fit the survey')
    if state['harvest.count'] != state['tree.picked_low'] + state['tree.gathered_ground']:
        raise StoryError('Harvest count disagrees with fruit gathered')
    if state['harvest.count'] == 0:
        if state['harvest.source'] or state['basket.load'] or state['tree.picked_low'] or state['tree.gathered_ground']:
            raise StoryError('Empty harvest has fruit state')
    elif state['harvest.count'] > 0:
        expected_source = 'low_branch' if state['tree.picked_low'] else 'windfalls'
        if state['harvest.source'] != expected_source or plan != expected_source:
            raise StoryError('Harvest source disagrees with the chosen plan')
        if state['harvest.count'] > state['basket.capacity']:
            raise StoryError('Harvest exceeds basket capacity')
        if state['tree.safe_reach'] != (state['harvest.source'] == 'low_branch'):
            raise StoryError('Unsafe harvest method')

    if state['friends.shared'] != state['snack.done']:
        raise StoryError('Sharing state disagrees with the snack')
    if state['snack.done']:
        if state['harvest.count'] < 1 or state['snack.pear_halves'] != 2 * state['harvest.count']:
            raise StoryError('The shared snack must account for every pear')
        if state['basket.load'] != 0:
            raise StoryError('Fruit must be removed from the basket at the snack')
    elif state['snack.pear_halves'] != 0 or state['basket.load'] != state['harvest.count']:
        raise StoryError('Unshared fruit must remain in the basket')

    if state['crate.tested']:
        expected_location = 'sorting_table' if state['crate.level'] else 'left_by_path'
        if state['crate.location'] != expected_location or state['crate.used_as_table'] != state['crate.level']:
            raise StoryError('Crate state disagrees with its stability test')
        expected_surface = 'crate' if state['crate.level'] else 'cloth'
        if state['picnic.surface'] != expected_surface:
            raise StoryError('Picnic surface disagrees with the crate vignette')
    elif (state['crate.location'] != 'orchard_edge' or state['crate.used_as_table']
          or state['picnic.surface'] != 'cloth'):
        raise StoryError('An untested crate cannot affect the picnic')

    if not state['basket.borrowed']:
        if (state['basket.owner'] != 'Vale' or state['basket.location'] != 'shed'
                or state['story.location'] != 'shed_gate' or state['basket.returned']):
            raise StoryError('Unborrowed basket is not at the shed')
    elif state['basket.returned']:
        if (state['basket.owner'] != 'Vale' or state['basket.location'] != 'shed'
                or state['story.location'] != 'shed_gate' or not state['basket.cleaned']):
            raise StoryError('Returned basket was not cleaned and brought home')
    elif (state['basket.owner'] != 'friends' or state['basket.location'] != state['story.location']
          or state['story.location'] == 'shed_gate'):
        raise StoryError('Borrowed basket must travel with the friends')

    if state['basket.returned'] != state['story.ended']:
        raise StoryError('The ending must include the basket return')
    expected_outcome = 'shared_harvest' if state['harvest.count'] >= 2 else 'small_shared_snack'
    if state['story.ended']:
        if not state['snack.done'] or state['story.outcome'] != expected_outcome:
            raise StoryError('Ending does not match the completed snack')
    elif state['story.outcome']:
        raise StoryError('An unfinished story cannot have an outcome')


def guard(scene_id, state):
    validate(state)
    if scene_id not in SCENES or state['story.ended']:
        return False
    location = state['story.location']
    if scene_id == 'borrow_basket':
        return location == 'shed_gate' and not state['basket.borrowed']
    if scene_id == 'vignette_crate':
        return location == 'orchard' and state['basket.borrowed'] and not state['crate.tested'] and not state['tree.surveyed']
    if scene_id == 'vignette_memory':
        return location == 'orchard' and state['basket.borrowed'] and not state['friends.memory'] and not state['tree.surveyed']
    if scene_id == 'survey_tree':
        return location == 'orchard' and state['basket.borrowed'] and not state['tree.surveyed']
    if scene_id == 'choose_harvest':
        return location == 'tree' and state['tree.surveyed'] and not state['harvest.plan']
    if scene_id == 'pick_fruit':
        return location == 'tree' and bool(state['harvest.plan']) and state['harvest.count'] == 0
    if scene_id == 'share_snack':
        return location == 'tree' and state['harvest.count'] > 0 and not state['snack.done']
    if scene_id in ('ending_full', 'ending_small'):
        if location != 'picnic' or not state['snack.done'] or state['basket.returned']:
            return False
        if scene_id == 'ending_full':
            return state['harvest.count'] >= 2
        return state['harvest.count'] == 1
    return False


@dataclass(frozen=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


def _episode_json(episode):
    return {
        'id': episode.id, 'before': deepcopy(episode.before), 'after': deepcopy(episode.after),
        'events': [deepcopy(event) for event in episode.events], 'text': episode.text,
    }


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    validate(state)
    for key, value in asdict(params).items():
        if state[f'param.{key}'] != value:
            raise StoryError('Parameters do not match this world state')
    if scene_id not in SCENES or not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')

    play = LocalPlay(state, actors=('mira', 'theo'), validate=validate)
    if scene_id == 'borrow_basket':
        play.act('borrow_picking_basket', requires={
            'basket.owner': 'Vale', 'basket.location': 'shed', 'basket.borrowed': False,
            'story.location': 'shed_gate',
        }, **{
            'basket.owner': 'friends', 'basket.location': 'orchard',
            'basket.borrowed': True, 'story.location': 'orchard',
        })

    elif scene_id == 'vignette_crate':
        play.act('test_crate_on_ground', requires={
            'story.location': 'orchard', 'crate.tested': False,
        }, **{
            'crate.tested': True,
            'crate.location': 'sorting_table' if params.crate_level else 'left_by_path',
            'crate.used_as_table': params.crate_level,
            'picnic.surface': 'crate' if params.crate_level else 'cloth',
        })

    elif scene_id == 'vignette_memory':
        play.act('recall_last_shared_pear', requires={
            'story.location': 'orchard', 'friends.memory': False,
        }, **{'friends.memory': True})

    elif scene_id == 'survey_tree':
        play.act('walk_to_pear_tree', requires={
            'story.location': 'orchard', 'basket.location': 'orchard',
        }, **{'story.location': 'tree', 'basket.location': 'tree'})
        safe = not params.windy and params.reach_cm >= 145
        play.act('inspect_from_the_ground', requires={
            'story.location': 'tree', 'tree.surveyed': False,
        }, **{'tree.surveyed': True, 'tree.safe_reach': safe})

    elif scene_id == 'choose_harvest':
        if state['tree.safe_reach']:
            play.act('choose_gentle_low_picking', requires={
                'tree.surveyed': True, 'tree.safe_reach': True, 'harvest.plan': '',
            }, **{'harvest.plan': 'low_branch'})
        else:
            play.act('choose_ground_fruit', requires={
                'tree.surveyed': True, 'tree.safe_reach': False, 'harvest.plan': '',
            }, **{'harvest.plan': 'windfalls'})

    elif scene_id == 'pick_fruit':
        if state['harvest.plan'] == 'low_branch':
            count = min(state['tree.low_ripe'], state['basket.capacity'])
            play.act('turn_and_gather_reachable_pears', requires={
                'tree.safe_reach': True, 'harvest.plan': 'low_branch', 'basket.load': 0,
            }, **{
                'tree.remaining_low': state['tree.low_ripe'] - count,
                'tree.picked_low': count, 'harvest.count': count,
                'harvest.source': 'low_branch', 'basket.load': count,
            })
        else:
            count = min(state['tree.windfalls'], state['basket.capacity'])
            play.act('check_and_gather_windfalls', requires={
                'tree.safe_reach': False, 'harvest.plan': 'windfalls', 'basket.load': 0,
            }, **{
                'tree.gathered_ground': count, 'harvest.count': count,
                'harvest.source': 'windfalls', 'basket.load': count,
            })

    elif scene_id == 'share_snack':
        count = state['basket.load']
        play.act('carry_fruit_and_share_fairly', requires={
            'story.location': 'tree', 'basket.location': 'tree',
            'basket.load': count,
        }, **{
            'story.location': 'picnic', 'basket.location': 'picnic',
            'basket.load': 0, 'snack.done': True,
            'snack.pear_halves': 2 * count, 'friends.shared': True,
        })

    else:
        outcome = 'shared_harvest' if state['harvest.count'] >= 2 else 'small_shared_snack'
        play.act('walk_back_with_empty_basket', requires={
            'story.location': 'picnic', 'basket.location': 'picnic', 'basket.load': 0,
        }, **{'story.location': 'shed_gate', 'basket.location': 'shed_gate'})
        play.act('wipe_basket_rim', requires={
            'story.location': 'shed_gate', 'basket.owner': 'friends', 'basket.cleaned': False,
        }, **{'basket.cleaned': True})
        play.act('return_basket_and_finish', requires={
            'basket.owner': 'friends', 'basket.cleaned': True,
            'basket.returned': False, 'snack.done': True,
        }, **{
            'basket.owner': 'Vale', 'basket.location': 'shed', 'basket.returned': True,
            'story.ended': True, 'story.outcome': outcome,
        })

    after = deepcopy(play.state)
    episode = Episode(
        id=scene_id, before=deepcopy(state), after=after,
        events=tuple(deepcopy(play.events)), text=render(scene_id, state, after),
    )
    return episode


def replay(params, path):
    if isinstance(path, (str, bytes)):
        raise StoryError('path must be a sequence of scene IDs')
    try:
        scene_ids = tuple(path)
    except TypeError as exc:
        raise StoryError('path must be a sequence of scene IDs') from exc
    if len(scene_ids) not in (7, 8) or len(set(scene_ids)) != len(scene_ids):
        raise StoryError('A complete path has seven or eight distinct scenes')
    state = initial(params)
    episodes = []
    for scene_id in scene_ids:
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode.after
    if not state['story.ended']:
        raise StoryError('Path does not reach a complete ending')
    return tuple(episodes)


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    chosen = parameters(seed) if params is None else params
    if not isinstance(chosen, Parameters):
        raise ValueError('params must be a Parameters instance')

    rng = random.Random(seed)
    optional = ['vignette_crate', 'vignette_memory']
    if count == 7:
        optional = [rng.choice(optional)]
    else:
        rng.shuffle(optional)
    planned = ['borrow_basket', *optional, 'survey_tree', 'choose_harvest', 'pick_fruit', 'share_snack']

    state = initial(chosen)
    episodes = []
    attempts = 0
    for scene_id in planned:
        attempts += 1
        if attempts > MAX_SCENE_ATTEMPTS:
            raise StoryError('Bounded scene selection budget exhausted')
        if not guard(scene_id, state):
            raise StoryError(f'Planned scene is incompatible: {scene_id}')
        episode = play_scene(chosen, state, scene_id)
        episodes.append(episode)
        state = episode.after

    ending = 'ending_full' if state['harvest.count'] >= 2 else 'ending_small'
    attempts += 1
    if attempts > MAX_SCENE_ATTEMPTS or not guard(ending, state):
        raise StoryError('No compatible ending within the scene budget')
    final_episode = play_scene(chosen, state, ending)
    episodes.append(final_episode)
    state = final_episode.after

    serialized = [_episode_json(episode) for episode in episodes]
    return {
        'seed': seed, 'parameters': asdict(chosen), 'scene_count': count,
        'path': [episode.id for episode in episodes],
        'story': '\n\n'.join(episode.text for episode in episodes),
        'episodes': serialized, 'final_state': deepcopy(state),
        'search_attempts': attempts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    args = parser.parse_args()
    row = generate(args.seed, count=args.scenes)
    print(row['story'])


if __name__ == '__main__':
    main()
