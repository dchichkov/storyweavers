"""Seeded, bounded greenhouse adventure. All committed local actions use LocalPlay."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .prose import render


@dataclass(frozen=True, kw_only=True)
class Parameters:
    heat: str = 'mild'
    can_leak: bool = False
    water_units: int = 2
    soil_dryness: int = 1
    shade_cloth: bool = True

    def __post_init__(self):
        if type(self.heat) is not str or self.heat not in {'mild', 'hot'}:
            raise ValueError('heat must be mild or hot')
        if type(self.can_leak) is not bool or type(self.shade_cloth) is not bool:
            raise ValueError('can_leak and shade_cloth must be booleans')
        if type(self.water_units) is not int or not 1 <= self.water_units <= 3:
            raise ValueError('water_units must be an integer from 1 to 3')
        if type(self.soil_dryness) is not int or not 1 <= self.soil_dryness <= 2:
            raise ValueError('soil_dryness must be an integer from 1 to 2')


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        heat=rng.choice(('mild', 'hot')),
        can_leak=rng.choice((False, True)),
        water_units=rng.choice((1, 2, 3)),
        soil_dryness=rng.choice((1, 2)),
        shade_cloth=rng.choice((False, True)),
    )


def initial(params):
    if not isinstance(params, Parameters):
        raise TypeError('params must be Parameters')
    required = params.soil_dryness + (1 if params.heat == 'hot' else 0)
    state = {
        'world.heat': params.heat,
        'world.can_leak': params.can_leak,
        'world.water_units': params.water_units,
        'world.soil_dryness': params.soil_dryness,
        'world.shade_cloth': params.shade_cloth,
        'story.goal': '',
        'story.ended': False,
        'story.outcome': '',
        'Mina.location': 'greenhouse',
        'Mina.knows_seedling_need': False,
        'can.owner': 'Ivo',
        'can.holder': 'Ivo',
        'can.location': 'rack',
        'can.leaks': params.can_leak,
        'can.sealed': False,
        'can.water': 0,
        'can.borrowed': False,
        'can.returned': False,
        'can.rinsed': False,
        'tank.units': params.water_units,
        'water.original': params.water_units,
        'water.spilled': 0,
        'water.done': False,
        'seedling.location': 'propagation_bench',
        'seedling.status': 'thirsty',
        'seedling.required': required,
        'seedling.watered_units': 0,
        'seedling.shade': 'none',
        'seedling.viable_tips': True,
        'labels.read': False,
        'band.available': False,
        'band.used': False,
        'band.location': 'label_clip',
        'neighbor.visited': False,
        'neighbor.advice': False,
        'screen.available': params.shade_cloth,
        'screen.location': 'north_rack' if params.shade_cloth else 'none',
        'tray.location': 'propagation_bench',
        'cuttings.rooted': False,
        'cuttings.location': 'none',
    }
    validate(state)
    return state


def validate(state):
    required_keys = {
        'world.heat', 'world.can_leak', 'world.water_units', 'world.soil_dryness',
        'world.shade_cloth', 'story.goal', 'story.ended', 'story.outcome',
        'Mina.location', 'Mina.knows_seedling_need', 'can.owner', 'can.holder',
        'can.location', 'can.leaks', 'can.sealed', 'can.water', 'can.borrowed',
        'can.returned', 'can.rinsed', 'tank.units', 'water.original', 'water.spilled',
        'water.done', 'seedling.location', 'seedling.status', 'seedling.required',
        'seedling.watered_units', 'seedling.shade', 'seedling.viable_tips',
        'labels.read', 'band.available', 'band.used', 'band.location',
        'neighbor.visited', 'neighbor.advice', 'screen.available', 'screen.location',
        'tray.location', 'cuttings.rooted', 'cuttings.location',
    }
    missing = required_keys - set(state)
    if missing:
        raise StoryError(f'Missing state keys: {sorted(missing)}')
    if state['world.heat'] not in {'mild', 'hot'}:
        raise StoryError('Unknown heat setting')
    if type(state['world.can_leak']) is not bool or type(state['world.shade_cloth']) is not bool:
        raise StoryError('Invalid world parameters in state')
    for key, low, high in (('world.water_units', 1, 3), ('world.soil_dryness', 1, 2)):
        if type(state[key]) is not int or not low <= state[key] <= high:
            raise StoryError(f'Invalid state value: {key}')
    bool_keys = (
        'story.ended', 'Mina.knows_seedling_need', 'can.leaks', 'can.sealed',
        'can.borrowed', 'can.returned', 'can.rinsed', 'water.done',
        'seedling.viable_tips', 'labels.read', 'band.available', 'band.used',
        'neighbor.visited', 'neighbor.advice', 'screen.available', 'cuttings.rooted',
    )
    if any(type(state[key]) is not bool for key in bool_keys):
        raise StoryError('Boolean state has an invalid type')
    if state['world.can_leak'] != state['can.leaks']:
        raise StoryError('Can condition disagrees with its parameters')
    if state['world.shade_cloth'] != state['screen.available']:
        raise StoryError('Screen availability disagrees with its parameters')
    if state['world.water_units'] != state['water.original']:
        raise StoryError('Water supply disagrees with its parameters')
    if state['seedling.required'] != state['world.soil_dryness'] + (state['world.heat'] == 'hot'):
        raise StoryError('Seedling water requirement is inconsistent')
    if state['Mina.location'] != 'greenhouse':
        raise StoryError('Mina is not in the greenhouse')
    if state['can.owner'] != 'Ivo' or state['can.holder'] not in {'Ivo', 'Mina'}:
        raise StoryError('Can ownership or custody is inconsistent')
    expected_can_location = 'rack' if state['can.holder'] == 'Ivo' else 'child'
    if state['can.location'] != expected_can_location:
        raise StoryError('Can holder and location disagree')
    if state['can.borrowed'] != (state['can.holder'] == 'Mina' or state['can.returned']):
        raise StoryError('Borrowing history and custody disagree')
    if state['can.returned'] and (state['can.holder'] != 'Ivo' or not state['can.rinsed']):
        raise StoryError('A returned can must be rinsed and back with Ivo')
    if state['can.rinsed'] != state['can.returned']:
        raise StoryError('Rinsing must accompany the return')
    for key in ('can.water', 'tank.units', 'water.original', 'water.spilled',
                'seedling.required', 'seedling.watered_units'):
        if type(state[key]) is not int or state[key] < 0:
            raise StoryError(f'Invalid water quantity: {key}')
    if state['can.water'] > state['water.original'] or state['tank.units'] > state['water.original']:
        raise StoryError('Water quantity exceeds the supply')
    if (state['tank.units'] + state['can.water'] + state['water.spilled']
            + state['seedling.watered_units'] != state['water.original']):
        raise StoryError('Water must be conserved across tank, can, spill, and soil')
    if state['water.done']:
        if state['tank.units'] != 0 or state['can.water'] != 0:
            raise StoryError('Watering must empty the filled can and tank')
    else:
        if state['water.spilled'] or state['seedling.watered_units']:
            raise StoryError('Water cannot be delivered before the watering action')
        initial_supply = state['tank.units'] == state['water.original'] and state['can.water'] == 0
        filled_supply = state['tank.units'] == 0 and state['can.water'] == state['water.original']
        if not (initial_supply or filled_supply):
            raise StoryError('Water is in an impossible container state')
    if state['can.sealed'] != state['band.used']:
        raise StoryError('The seam seal and borrowed band disagree')
    if state['band.used']:
        if state['band.location'] != 'can_spout' or state['band.available']:
            raise StoryError('A used band must be attached to the can')
    elif state['band.location'] != 'label_clip':
        raise StoryError('An unused band must remain at its label clip')
    if state['band.available'] and not state['labels.read']:
        raise StoryError('The band is available only after reading the label')
    if state['neighbor.advice'] != state['neighbor.visited']:
        raise StoryError('Neighbor advice requires the conversation')
    if state['seedling.shade'] not in {'none', 'screen', 'shelf'}:
        raise StoryError('Unknown shade source')
    if state['screen.location'] == 'over_tray':
        if not state['screen.available'] or state['seedling.shade'] != 'screen':
            raise StoryError('Screen location and shade do not agree')
    elif state['seedling.shade'] == 'screen':
        raise StoryError('A screened tray needs the screen over it')
    elif state['screen.location'] != ('north_rack' if state['screen.available'] else 'none'):
        raise StoryError('Screen has an impossible location')
    expected_tray = 'cool_shelf' if state['seedling.shade'] == 'shelf' else 'propagation_bench'
    if state['tray.location'] != expected_tray:
        raise StoryError('Tray location and shade source disagree')
    if not state['seedling.viable_tips']:
        raise StoryError('The scenario requires surviving tips for its recovery ending')
    if state['cuttings.rooted'] != (state['cuttings.location'] != 'none'):
        raise StoryError('Rooted cuttings need a physical location')
    if not state['water.done'] and state['seedling.status'] != 'thirsty':
        raise StoryError('Unwatered seedlings must remain thirsty')
    if state['water.done'] and state['seedling.shade'] == 'none':
        expected_status = ('watered' if state['seedling.watered_units'] >= state['seedling.required']
                           else 'thirsty')
        if state['seedling.status'] != expected_status:
            raise StoryError('Watering result and seedling status disagree')
    if state['water.done'] and state['seedling.shade'] != 'none' and not state['story.ended']:
        expected_status = ('stable' if state['seedling.shade'] == 'screen'
                           and state['seedling.watered_units'] >= state['seedling.required']
                           else 'sheltered')
        if state['seedling.status'] != expected_status:
            raise StoryError('Shade and watering outcome disagree')
    if state['story.ended']:
        if not state['story.goal'] or not state['can.returned'] or not state['water.done']:
            raise StoryError('Ending left an essential action unfinished')
        if state['story.outcome'] == 'seedlings_stable':
            if (state['seedling.status'] != 'stable' or state['seedling.shade'] != 'screen'
                    or state['seedling.watered_units'] < state['seedling.required']):
                raise StoryError('Stable ending lacks water or effective shade')
        elif state['story.outcome'] == 'cuttings_rooted':
            if state['seedling.status'] != 'cuttings_rooted' or not state['cuttings.rooted']:
                raise StoryError('Cuttings ending lacks rooted cuttings')
        else:
            raise StoryError('An ending needs a recognized outcome')
    elif state['story.outcome']:
        raise StoryError('An unfinished story cannot have an outcome')
    if state['cuttings.rooted'] and not state['story.ended'] and state['seedling.status'] != 'sheltered':
        raise StoryError('Cuttings can only be taken from a sheltered tray')


@dataclass(frozen=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


SCENES = (
    'notice', 'borrow_can', 'read_labels', 'talk_to_rosa', 'fill_and_water',
    'make_shade', 'return_can', 'ending_stable', 'ending_cuttings',
)


def guard(scene_id, state):
    if scene_id not in SCENES or state.get('story.ended'):
        return False
    goal = bool(state.get('story.goal'))
    if scene_id == 'notice':
        return not goal
    if not goal:
        return False
    if scene_id == 'borrow_can':
        return not state['can.borrowed'] and state['can.holder'] == 'Ivo'
    if scene_id == 'read_labels':
        return (state['can.borrowed'] and state['can.holder'] == 'Mina'
                and not state['labels.read'] and not state['water.done'])
    if scene_id == 'talk_to_rosa':
        return (state['can.borrowed'] and state['can.holder'] == 'Mina'
                and not state['neighbor.visited'] and not state['water.done'])
    if scene_id == 'fill_and_water':
        return (state['can.borrowed'] and state['can.holder'] == 'Mina'
                and not state['water.done'] and state['tank.units'] > 0)
    if scene_id == 'make_shade':
        return state['water.done'] and state['seedling.shade'] == 'none'
    if scene_id == 'return_can':
        return (state['water.done'] and state['seedling.shade'] != 'none'
                and state['can.holder'] == 'Mina' and not state['can.returned'])
    if scene_id == 'ending_stable':
        return (state['can.returned'] and not state['story.ended']
                and state['seedling.status'] == 'stable')
    if scene_id == 'ending_cuttings':
        return (state['can.returned'] and not state['story.ended']
                and state['seedling.status'] == 'sheltered')
    return False


def _check_parameters_match(params, state):
    expected = {
        'world.heat': params.heat,
        'world.can_leak': params.can_leak,
        'world.water_units': params.water_units,
        'world.soil_dryness': params.soil_dryness,
        'world.shade_cloth': params.shade_cloth,
    }
    if any(state.get(key) != value for key, value in expected.items()):
        raise StoryError('Parameters do not match this world state')


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise TypeError('params must be Parameters')
    validate(state)
    _check_parameters_match(params, state)
    if not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    play = LocalPlay(state, actors=('Mina', 'Ivo', 'Rosa'), validate=validate)

    if scene_id == 'notice':
        play.act('notice_thirsty_seedlings', **{'story.goal': 'protect Rosa seedlings'})
    elif scene_id == 'borrow_can':
        play.act('borrow_Ivos_blue_can', {'can.holder': 'Ivo', 'can.location': 'rack'},
                 **{'can.holder': 'Mina', 'can.location': 'child', 'can.borrowed': True})
    elif scene_id == 'read_labels':
        play.act('read_seedling_label', {'labels.read': False},
                 **{'labels.read': True, 'Mina.knows_seedling_need': True,
                    'band.available': True})
    elif scene_id == 'talk_to_rosa':
        play.act('ask_Rosa_about_afternoon_shade', {'neighbor.visited': False},
                 **{'neighbor.visited': True, 'neighbor.advice': True})
    elif scene_id == 'fill_and_water':
        play.act('fill_can_at_shared_tap',
                 {'can.holder': 'Mina', 'tank.units': params.water_units},
                 **{'tank.units': 0, 'can.water': params.water_units})
        if params.can_leak and play.state['band.available']:
            play.act('bind_split_seam_with_label_band',
                     {'can.leaks': True, 'band.available': True, 'labels.read': True},
                     **{'can.sealed': True, 'band.used': True, 'band.available': False,
                        'band.location': 'can_spout'})
        loss = 1 if params.can_leak and not play.state['can.sealed'] else 0
        delivered = max(0, params.water_units - loss)
        status = 'watered' if delivered >= play.state['seedling.required'] else 'thirsty'
        play.act('pour_measured_water_into_seedling_cells',
                 {'can.holder': 'Mina', 'can.water': params.water_units, 'water.done': False},
                 **{'can.water': 0, 'water.spilled': loss, 'water.done': True,
                    'seedling.watered_units': delivered, 'seedling.status': status})
    elif scene_id == 'make_shade':
        if params.shade_cloth and play.state['neighbor.advice']:
            status = ('stable' if play.state['seedling.watered_units'] >= play.state['seedling.required']
                      else 'sheltered')
            play.act('hang_screen_over_seedling_tray',
                     {'neighbor.advice': True, 'screen.available': True, 'seedling.shade': 'none'},
                     **{'screen.location': 'over_tray', 'seedling.shade': 'screen',
                        'seedling.status': status})
        else:
            play.act('move_tray_to_cool_shelf_shadow', {'seedling.shade': 'none'},
                     **{'seedling.shade': 'shelf', 'tray.location': 'cool_shelf',
                        'seedling.status': 'sheltered'})
    elif scene_id == 'return_can':
        changes = {'can.holder': 'Ivo', 'can.location': 'rack', 'can.returned': True,
                   'can.rinsed': True, 'can.sealed': False}
        requirements = {'can.holder': 'Mina', 'can.returned': False}
        if play.state['band.used']:
            requirements['band.used'] = True
            changes.update({'band.used': False, 'band.location': 'label_clip'})
        else:
            requirements['can.sealed'] = False
        play.act('rinse_and_return_borrowed_can', requirements, **changes)
    elif scene_id == 'ending_stable':
        play.act('confirm_seedlings_stable_in_screen_shade',
                 {'can.returned': True, 'seedling.status': 'stable', 'story.ended': False},
                 **{'story.ended': True, 'story.outcome': 'seedlings_stable'})
    elif scene_id == 'ending_cuttings':
        play.act('root_surviving_seedling_tips',
                 {'can.returned': True, 'seedling.status': 'sheltered',
                  'seedling.viable_tips': True},
                 **{'cuttings.rooted': True, 'cuttings.location': 'propagation_bench'})
        play.act('finish_cuttings_rescue',
                 {'cuttings.rooted': True, 'story.ended': False},
                 **{'seedling.status': 'cuttings_rooted', 'story.ended': True,
                    'story.outcome': 'cuttings_rooted'})

    after = play.state
    return Episode(
        id=scene_id,
        before=json.loads(json.dumps(state)),
        after=json.loads(json.dumps(after)),
        events=tuple(json.loads(json.dumps(play.events))),
        text=render(scene_id, params, state, after),
    )


def _preferred_vignette(params):
    required = params.soil_dryness + (1 if params.heat == 'hot' else 0)
    unsealed_delivery = max(0, params.water_units - (1 if params.can_leak else 0))
    if params.shade_cloth and unsealed_delivery >= required:
        return 'talk_to_rosa'
    return 'read_labels'


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    p = params if params is not None else parameters(seed)
    if not isinstance(p, Parameters):
        raise TypeError('params must be Parameters')
    rng = random.Random(seed)
    attempts = 0
    max_attempts = 5000
    required_vignettes = count - 6

    def search(state, episodes):
        nonlocal attempts
        remaining = count - len(episodes)
        if remaining == 0:
            return episodes if state['story.ended'] else None
        if state['story.ended']:
            return None
        used = {episode.id for episode in episodes}
        choices = [scene_id for scene_id in SCENES
                   if scene_id not in used and guard(scene_id, state)
                   and (not scene_id.startswith('ending_') or remaining == 1)
                   and (scene_id.startswith('ending_') or remaining > 1)]
        vignettes_done = int(state['labels.read']) + int(state['neighbor.visited'])
        if (not state['water.done'] and state['can.borrowed']
                and vignettes_done < required_vignettes):
            choices = [scene_id for scene_id in choices
                       if scene_id in {'read_labels', 'talk_to_rosa'}]
        rng.shuffle(choices)
        if vignettes_done == 0 and required_vignettes == 1:
            preferred = _preferred_vignette(p)
            choices.sort(key=lambda scene_id: scene_id != preferred)
        for scene_id in choices:
            attempts += 1
            if attempts > max_attempts:
                raise StoryError('Bounded scene search exhausted')
            try:
                episode = play_scene(p, state, scene_id)
            except StoryError:
                continue
            answer = search(episode.after, episodes + (episode,))
            if answer is not None:
                return answer
        return None

    episodes = search(initial(p), ())
    if episodes is None:
        raise StoryError('No complete route at the requested length')
    episode_rows = [
        {'id': episode.id, 'before': episode.before, 'after': episode.after,
         'events': list(episode.events), 'text': episode.text}
        for episode in episodes
    ]
    return {
        'seed': seed,
        'parameters': asdict(p),
        'scene_count': count,
        'path': [episode.id for episode in episodes],
        'story': '\n\n'.join(episode.text for episode in episodes),
        'episodes': episode_rows,
        'final_state': episode_rows[-1]['after'],
        'search_attempts': attempts,
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise TypeError('params must be Parameters')
    state = initial(params)
    episodes = []
    for scene_id in path:
        if any(episode.id == scene_id for episode in episodes):
            raise StoryError(f'Scene cannot be repeated: {scene_id}')
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode.after
    return tuple(episodes)


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
