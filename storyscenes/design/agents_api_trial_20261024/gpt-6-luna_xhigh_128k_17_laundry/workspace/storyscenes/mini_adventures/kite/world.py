'''A bounded washing-line adventure built from guarded atomic local plays.'''
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
import random

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .prose import render


ITEMS = ('sheet', 'shirt', 'towel', 'socks')
SCENES = (
    'borrow_bag', 'sky_signs', 'save_snail', 'peg_rhyme_vignette',
    'prepare_wash', 'hang_wash', 'weather_turn', 'protect_wash',
    'ending_line', 'ending_shelter', 'ending_rain',
)
OPTIONAL = frozenset(('save_snail', 'peg_rhyme_vignette'))


@dataclass(frozen=True, kw_only=True)
class Parameters:
    peg_count: int = 8
    shower_after: int = 6
    windy: bool = False
    line_strength: bool = True
    shelter_open: bool = True
    sheet_heavy: bool = False
    priority: str = 'sheet'

    def __post_init__(self):
        if type(self.peg_count) is not int or not 4 <= self.peg_count <= 12:
            raise ValueError('peg_count must be an integer in [4, 12]')
        if type(self.shower_after) is not int or not 3 <= self.shower_after <= 6:
            raise ValueError('shower_after must be an integer in [3, 6]')
        for name in ('windy', 'line_strength', 'shelter_open', 'sheet_heavy'):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f'{name} must be a boolean')
        if self.priority not in ('sheet', 'small') or not isinstance(self.priority, str):
            raise ValueError("priority must be 'sheet' or 'small'")


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        peg_count=rng.choice((5, 6, 8, 10)),
        shower_after=rng.choice((3, 4, 5, 6)),
        windy=rng.choice((False, True)),
        line_strength=rng.choice((False, True)),
        shelter_open=rng.choice((False, True)),
        sheet_heavy=rng.choice((False, True)),
        priority=rng.choice(('sheet', 'small')),
    )


def initial(params):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    return {
        'story.ended': False, 'story.outcome': '',
        'cfg.peg_count': params.peg_count, 'cfg.shower_after': params.shower_after,
        'cfg.windy': params.windy, 'cfg.line_strength': params.line_strength,
        'cfg.shelter_open': params.shelter_open, 'cfg.sheet_heavy': params.sheet_heavy,
        'cfg.priority': params.priority,
        'child.name': 'Nia', 'neighbor.name': 'Mae', 'child.borrowed': False,
        'child.priority': '', 'child.feeling': 'hopeful', 'child.remembers_rhyme': False,
        'child.choice': '', 'neighbor.trust': 0, 'neighbor.helped': False,
        'peg_bag.owner': 'Mae', 'peg_bag.location': 'bench', 'peg_bag.returned': False,
        'peg_bag.used': False, 'peg_bag.pegs': params.peg_count, 'pegs.in_use': 0,
        'weather.clock': 0, 'weather.raining': False, 'weather.seen': False,
        'weather.checked': False,
        'line.location': 'shared_garden', 'line.prepared': False, 'line.safe': False,
        'wash.prepared': False, 'wash.attempted': False, 'wash.fully_hung': False,
        'wash.resolution': 'pending', 'wash.wet': False, 'wash.protected': False,
        'sheet.location': 'basket', 'sheet.pegs': 0,
        'shirt.location': 'basket', 'shirt.pegs': 0,
        'towel.location': 'basket', 'towel.pegs': 0,
        'socks.location': 'basket', 'socks.pegs': 0,
        'shelter.location': 'covered_shed',
        'snail.location': 'path', 'snail.safe': False,
        'vignette.snail_done': False, 'vignette.rhyme_done': False,
    }


def validate(state):
    if not isinstance(state, dict):
        raise StoryError('State must be a dictionary')
    expected = set(initial(Parameters()))
    if set(state) != expected:
        raise StoryError(f'Invalid state keys: missing={expected - set(state)}, extra={set(state) - expected}')
    if any(type(value) not in (str, bool, int) for value in state.values()):
        raise StoryError('World state values must be JSON-native scalar values')

    bool_keys = (
        'story.ended', 'cfg.windy', 'cfg.line_strength', 'cfg.shelter_open',
        'cfg.sheet_heavy', 'child.borrowed', 'child.remembers_rhyme', 'neighbor.helped',
        'peg_bag.returned', 'peg_bag.used', 'weather.raining', 'weather.seen',
        'weather.checked', 'line.prepared', 'line.safe', 'wash.prepared',
        'wash.attempted', 'wash.fully_hung', 'wash.wet', 'wash.protected',
        'snail.safe', 'vignette.snail_done', 'vignette.rhyme_done',
    )
    if any(type(state[k]) is not bool for k in bool_keys):
        raise StoryError('A boolean state field has the wrong type')
    int_keys = ('cfg.peg_count', 'cfg.shower_after', 'neighbor.trust', 'peg_bag.pegs',
                'pegs.in_use', 'weather.clock', 'sheet.pegs', 'shirt.pegs', 'towel.pegs', 'socks.pegs')
    if any(type(state[k]) is not int for k in int_keys):
        raise StoryError('An integer state field has the wrong type')
    if not 4 <= state['cfg.peg_count'] <= 12 or not 3 <= state['cfg.shower_after'] <= 6:
        raise StoryError('Embedded parameter is out of range')
    if state['weather.clock'] < 0 or state['neighbor.trust'] < 0:
        raise StoryError('Clock and trust cannot be negative')
    if state['cfg.priority'] not in ('sheet', 'small'):
        raise StoryError('Invalid embedded priority')
    if state['child.name'] != 'Nia' or state['neighbor.name'] != 'Mae':
        raise StoryError('This pack has a fixed embedded cast')
    if state['child.feeling'] not in ('hopeful', 'focused', 'proud', 'relieved', 'disappointed'):
        raise StoryError('Unknown child feeling')
    if state['child.priority'] not in ('', 'sheet', 'small'):
        raise StoryError('Unknown laundry priority')
    if state['child.choice'] not in ('', 'leave', 'shelter', 'gather'):
        raise StoryError('Unknown weather choice')
    if state['peg_bag.owner'] not in ('Mae', 'Nia'):
        raise StoryError('Unknown peg-bag owner')
    if state['peg_bag.location'] not in ('bench', 'Nia', 'Mae'):
        raise StoryError('Unknown peg-bag location')
    if not state['child.borrowed']:
        if (state['peg_bag.owner'], state['peg_bag.location'], state['peg_bag.returned']) != ('Mae', 'bench', False):
            raise StoryError('Unborrowed bag has inconsistent custody')
    elif state['peg_bag.returned']:
        if (state['peg_bag.owner'], state['peg_bag.location']) != ('Mae', 'Mae'):
            raise StoryError('Returned bag has inconsistent custody')
    elif (state['peg_bag.owner'], state['peg_bag.location']) != ('Nia', 'Nia'):
        raise StoryError('Borrowed bag has inconsistent custody')
    if state['peg_bag.returned'] != state['story.ended']:
        raise StoryError('The bag is returned exactly when the story ends')
    if state['peg_bag.pegs'] + state['pegs.in_use'] != state['cfg.peg_count']:
        raise StoryError('Peg count is not conserved')

    required_sheet_pegs = 4 if state['cfg.windy'] or state['cfg.sheet_heavy'] else 2
    item_cost = {'sheet': required_sheet_pegs, 'shirt': 2, 'towel': 1, 'socks': 1}
    locations = {}
    total_in_use = 0
    for item in ITEMS:
        location = state[f'{item}.location']
        pegs = state[f'{item}.pegs']
        if location not in ('basket', 'line', 'shelter_rack', 'indoor_rack'):
            raise StoryError(f'Unknown location for {item}')
        if pegs < 0 or pegs > item_cost[item]:
            raise StoryError(f'Invalid peg allocation for {item}')
        if location == 'line' and pegs != item_cost[item]:
            raise StoryError(f'{item} on the line needs its allocated pegs')
        if location in ('basket', 'indoor_rack') and pegs != 0:
            raise StoryError(f'{item} in {location} cannot retain borrowed pegs')
        if location == 'shelter_rack' and pegs not in (0, item_cost[item]):
            raise StoryError(f'Invalid sheltered peg allocation for {item}')
        locations[item] = location
        total_in_use += pegs
    if total_in_use != state['pegs.in_use']:
        raise StoryError('Peg allocations disagree with the in-use total')
    all_on_line = all(locations[item] == 'line' for item in ITEMS)
    if state['wash.fully_hung'] != all_on_line:
        raise StoryError('Full-line flag disagrees with garment locations')
    expected_safe = (all_on_line and state['cfg.line_strength'] and
                     (not state['cfg.windy'] or state['sheet.pegs'] >= 4))
    if state['line.safe'] != expected_safe:
        raise StoryError('Line safety disagrees with its support and load')
    if state['line.location'] != 'shared_garden' or state['shelter.location'] != 'covered_shed':
        raise StoryError('Fixed garden fixture moved')
    if state['line.prepared'] != state['wash.prepared']:
        raise StoryError('Preparation flags disagree')
    if state['child.priority'] != (state['cfg.priority'] if state['wash.prepared'] else ''):
        raise StoryError('Priority choice is not consistent with preparation')
    if state['wash.attempted'] and not state['wash.prepared']:
        raise StoryError('Cannot hang unprepared washing')
    if state['peg_bag.used'] and not state['wash.attempted']:
        raise StoryError('Bag cannot be useful before the hanging pass')
    if state['weather.raining'] != (state['weather.clock'] >= state['cfg.shower_after']):
        raise StoryError('Rain state disagrees with elapsed time')
    if state['weather.seen'] != (state['weather.clock'] >= 1 or state['weather.checked']):
        raise StoryError('Weather observation disagrees with elapsed time')
    if state['weather.checked'] and (not state['wash.attempted'] or state['weather.clock'] < 4):
        raise StoryError('Weather turn occurred before the hanging pass')
    if state['weather.checked'] != bool(state['child.choice']):
        raise StoryError('Weather choice is missing or premature')
    if state['vignette.snail_done'] != state['snail.safe']:
        raise StoryError('Snail vignette and safety disagree')
    if state['snail.location'] != ('marigolds' if state['snail.safe'] else 'path'):
        raise StoryError('Snail location disagrees with its rescue')
    if state['vignette.rhyme_done'] != state['child.remembers_rhyme']:
        raise StoryError('Rhyme memory has no enacted source')
    if state['wash.protected'] != (state['wash.resolution'] == 'shelter'):
        raise StoryError('Cover state disagrees with the chosen resolution')
    if state['wash.wet'] and not state['weather.raining']:
        raise StoryError('Washing cannot be rain-wet before the shower')

    resolution = state['wash.resolution']
    if resolution not in ('pending', 'line', 'shelter', 'basket'):
        raise StoryError('Unknown wash resolution')
    if resolution == 'pending':
        if state['weather.checked'] or state['story.ended']:
            raise StoryError('Pending washing cannot pass the resolution scene')
    elif resolution == 'line':
        if not (all_on_line and state['line.safe'] and not state['weather.raining'] and not state['wash.wet']):
            raise StoryError('Dry-line resolution is not physically supported')
    elif resolution == 'shelter':
        if not state['cfg.shelter_open'] or not all(locations[i] == 'shelter_rack' for i in ITEMS):
            raise StoryError('Shelter resolution has laundry outside the shelter')
    elif resolution == 'basket':
        expected_location = 'indoor_rack' if state['story.ended'] else 'basket'
        if (not state['weather.raining'] or not state['wash.wet'] or
                any(locations[i] != expected_location for i in ITEMS)):
            raise StoryError('Rain-recovery resolution is incomplete')

    if state['neighbor.helped'] and not (state['story.ended'] and resolution in ('shelter', 'basket')):
        raise StoryError('Neighbour help must belong to a completed recovery')
    if not state['story.ended']:
        if state['story.outcome']:
            raise StoryError('An unfinished story cannot have an outcome')
    else:
        expected_outcome = {'line': 'hung_before_shower', 'shelter': 'covered_in_shed',
                            'basket': 'caught_then_rehung'}.get(resolution)
        if (not expected_outcome or state['story.outcome'] != expected_outcome or
                not state['peg_bag.used'] or not state['peg_bag.returned']):
            raise StoryError('Ending is not complete or does not match the enacted outcome')
        if resolution == 'basket' and not state['neighbor.helped']:
            raise StoryError('Rain recovery needs the neighbour’s completed help')


def _act(play, name, requires=None, changes=None):
    play.act(name, requires=requires or {}, **(changes or {}))


def _tick_changes(state):
    clock = state['weather.clock'] + 1
    return {'weather.clock': clock, 'weather.raining': clock >= state['cfg.shower_after']}


def _hang_one(play, item, cost):
    state = play.state
    if item == 'sheet' and state['cfg.sheet_heavy'] and not state['cfg.line_strength']:
        return False
    if state['peg_bag.pegs'] < cost or state[f'{item}.location'] != 'basket':
        return False
    future_sheet_pegs = cost if item == 'sheet' else state['sheet.pegs']
    future_locations = {name: state[f'{name}.location'] for name in ITEMS}
    future_locations[item] = 'line'
    fully_hung = all(future_locations[name] == 'line' for name in ITEMS)
    safe = (fully_hung and state['cfg.line_strength'] and
            (not state['cfg.windy'] or future_sheet_pegs >= 4))
    changes = {
        f'{item}.location': 'line', f'{item}.pegs': cost,
        'peg_bag.pegs': state['peg_bag.pegs'] - cost,
        'pegs.in_use': state['pegs.in_use'] + cost,
        'wash.fully_hung': fully_hung, 'line.safe': safe,
    }
    action = {'sheet': 'clip_sheet_corners', 'shirt': 'clip_shirt',
              'towel': 'peg_towel', 'socks': 'peg_socks'}[item]
    _act(play, action, {'wash.prepared': True, 'wash.attempted': False,
                        'peg_bag.owner': 'Nia'}, changes)
    return True


@dataclass(frozen=True, kw_only=True)
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
    if scene_id == 'borrow_bag':
        return not state['child.borrowed']
    if not state['child.borrowed']:
        return False
    if scene_id == 'save_snail':
        return not state['wash.prepared'] and not state['vignette.snail_done']
    if scene_id == 'peg_rhyme_vignette':
        return not state['wash.prepared'] and not state['vignette.rhyme_done']
    if scene_id == 'sky_signs':
        return not state['weather.seen']
    if scene_id == 'prepare_wash':
        return state['weather.seen'] and not state['wash.prepared']
    if scene_id == 'hang_wash':
        return state['wash.prepared'] and not state['wash.attempted']
    if scene_id == 'weather_turn':
        return state['wash.attempted'] and not state['weather.checked']
    if scene_id == 'protect_wash':
        return state['weather.checked'] and state['wash.resolution'] == 'pending'
    if scene_id == 'ending_line':
        return (state['wash.resolution'] == 'line' and state['wash.fully_hung'] and
                state['line.safe'] and not state['weather.raining'])
    if scene_id == 'ending_shelter':
        return state['wash.resolution'] == 'shelter' and state['cfg.shelter_open']
    if scene_id == 'ending_rain':
        return (state['wash.resolution'] == 'basket' and state['weather.raining'] and
                state['wash.wet'] and not state['cfg.shelter_open'])
    return False


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    validate(state)
    for field in ('peg_count', 'shower_after', 'windy', 'line_strength',
                  'shelter_open', 'sheet_heavy', 'priority'):
        if state[f'cfg.{field}'] != getattr(params, field):
            raise StoryError('Parameters do not match this world state')
    if not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    play = LocalPlay(state, actors=('Nia', 'Mae'), validate=validate)

    if scene_id == 'borrow_bag':
        _act(play, 'ask_and_borrow_peg_bag',
             {'peg_bag.owner': 'Mae', 'peg_bag.location': 'bench'},
             {'child.borrowed': True, 'peg_bag.owner': 'Nia', 'peg_bag.location': 'Nia'})
    elif scene_id == 'sky_signs':
        changes = _tick_changes(play.state)
        changes['weather.seen'] = True
        _act(play, 'read_the_approaching_shower', {'child.borrowed': True}, changes)
    elif scene_id == 'save_snail':
        _act(play, 'move_snail_to_marigolds', {'snail.location': 'path'},
             {'snail.location': 'marigolds', 'snail.safe': True, 'vignette.snail_done': True})
    elif scene_id == 'peg_rhyme_vignette':
        _act(play, 'learn_maes_peg_rhyme', {'child.borrowed': True},
             {'vignette.rhyme_done': True, 'child.remembers_rhyme': True,
              'neighbor.trust': play.state['neighbor.trust'] + 1})
    elif scene_id == 'prepare_wash':
        changes = _tick_changes(play.state)
        changes.update({'line.prepared': True, 'wash.prepared': True,
                        'child.priority': params.priority, 'child.feeling': 'focused'})
        _act(play, 'test_line_and_choose_priority', {'weather.seen': True}, changes)
    elif scene_id == 'hang_wash':
        sheet_cost = 4 if params.windy or params.sheet_heavy else 2
        order = ('sheet', 'shirt', 'towel', 'socks') if params.priority == 'sheet' else ('shirt', 'towel', 'socks', 'sheet')
        for item in order:
            _hang_one(play, item, sheet_cost if item == 'sheet' else {'shirt': 2, 'towel': 1, 'socks': 1}[item])
        changes = _tick_changes(play.state)
        changes.update({'wash.attempted': True, 'peg_bag.used': play.state['pegs.in_use'] > 0})
        _act(play, 'finish_the_hanging_pass', {'wash.prepared': True, 'wash.attempted': False}, changes)
    elif scene_id == 'weather_turn':
        changes = _tick_changes(play.state)
        raining = changes['weather.raining']
        if play.state['wash.fully_hung'] and play.state['line.safe'] and not raining:
            choice = 'leave'
        elif params.shelter_open:
            choice = 'shelter'
        else:
            choice = 'gather'
        changes.update({'weather.checked': True, 'child.choice': choice})
        _act(play, 'notice_wind_and_choose_a_response', {'wash.attempted': True}, changes)
    elif scene_id == 'protect_wash':
        state_now = play.state
        if state_now['child.choice'] == 'leave':
            _act(play, 'check_the_secure_line', {'child.choice': 'leave'},
                 {'wash.resolution': 'line', 'child.feeling': 'proud'})
        elif state_now['child.choice'] == 'shelter':
            changes = {f'{item}.location': 'shelter_rack' for item in ITEMS}
            changes.update({'wash.resolution': 'shelter', 'wash.protected': True,
                            'wash.wet': state_now['weather.raining'], 'wash.fully_hung': False,
                            'line.safe': False, 'child.feeling': 'relieved'})
            _act(play, 'move_all_washing_under_cover',
                 {'child.choice': 'shelter', 'cfg.shelter_open': True}, changes)
        else:
            clock = max(state_now['weather.clock'], state_now['cfg.shower_after'])
            changes = {f'{item}.location': 'basket' for item in ITEMS}
            changes.update({f'{item}.pegs': 0 for item in ITEMS})
            changes.update({'peg_bag.pegs': state_now['cfg.peg_count'], 'pegs.in_use': 0,
                            'weather.clock': clock, 'weather.raining': True,
                            'wash.resolution': 'basket', 'wash.wet': True,
                            'wash.fully_hung': False, 'line.safe': False,
                            'child.feeling': 'disappointed'})
            _act(play, 'gather_everything_as_the_shower_arrives',
                 {'child.choice': 'gather'}, changes)
    elif scene_id == 'ending_line':
        _act(play, 'return_the_used_bag_and_finish_on_the_line', {'wash.resolution': 'line'},
             {'peg_bag.owner': 'Mae', 'peg_bag.location': 'Mae', 'peg_bag.returned': True,
              'neighbor.trust': play.state['neighbor.trust'] + 1,
              'story.ended': True, 'story.outcome': 'hung_before_shower'})
    elif scene_id == 'ending_shelter':
        _act(play, 'return_the_bag_after_sheltering_the_wash', {'wash.resolution': 'shelter'},
             {'peg_bag.owner': 'Mae', 'peg_bag.location': 'Mae', 'peg_bag.returned': True,
              'neighbor.trust': play.state['neighbor.trust'] + 1, 'neighbor.helped': True,
              'story.ended': True, 'story.outcome': 'covered_in_shed'})
    elif scene_id == 'ending_rain':
        changes = {f'{item}.location': 'indoor_rack' for item in ITEMS}
        changes.update({'peg_bag.owner': 'Mae', 'peg_bag.location': 'Mae', 'peg_bag.returned': True,
                        'neighbor.trust': play.state['neighbor.trust'] + 1, 'neighbor.helped': True,
                        'story.ended': True, 'story.outcome': 'caught_then_rehung',
                        'child.feeling': 'relieved'})
        _act(play, 'tell_mae_and_rehang_the_wash_indoors',
             {'wash.resolution': 'basket', 'weather.raining': True}, changes)

    after = deepcopy(play.state)
    validate(after)
    return Episode(id=scene_id, before=deepcopy(state), after=after,
                   events=tuple(deepcopy(play.events)), text=render(scene_id, params, state, after))


def _minimum_remaining(state):
    if state['story.ended']:
        return 0
    if not state['child.borrowed']:
        return 7
    if not state['weather.seen']:
        return 6
    if not state['wash.prepared']:
        return 5
    if not state['wash.attempted']:
        return 4
    if not state['weather.checked']:
        return 3
    if state['wash.resolution'] == 'pending':
        return 2
    return 1


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
        raise TypeError('params must be a Parameters instance')
    rng = random.Random(seed)
    attempts = 0
    nodes = 0

    def search(state, episodes):
        nonlocal attempts, nodes
        nodes += 1
        if nodes > 5000:
            raise StoryError('Bounded scene search exhausted its node budget')
        remaining = count - len(episodes)
        minimum = _minimum_remaining(state)
        if remaining < minimum:
            return None
        if remaining == 0:
            return episodes if state['story.ended'] else None
        if state['story.ended']:
            return None
        candidates = []
        for scene_id in SCENES:
            if not guard(scene_id, state):
                continue
            if scene_id in OPTIONAL and remaining <= minimum:
                continue
            candidates.append(scene_id)
        rng.shuffle(candidates)
        for scene_id in candidates:
            attempts += 1
            if attempts > 10000:
                raise StoryError('Bounded scene search exhausted its attempt budget')
            episode = play_scene(p, state, scene_id)
            result = search(episode.after, episodes + (episode,))
            if result is not None:
                return result
        return None

    episodes = search(initial(p), ())
    if episodes is None:
        raise StoryError('No compatible route reaches an ending at this length')
    episode_rows = [_episode_dict(e) for e in episodes]
    return {
        'seed': seed,
        'parameters': asdict(p),
        'scene_count': count,
        'path': [e.id for e in episodes],
        'story': '\n\n'.join(e.text for e in episodes),
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
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode.after
    return tuple(episodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    parser.add_argument('--params', help='Optional JSON object of Parameters overrides')
    args = parser.parse_args()
    base = asdict(parameters(args.seed))
    overrides = json.loads(args.params) if args.params else {}
    if not isinstance(overrides, dict):
        parser.error('--params must be a JSON object')
    p = Parameters(**(base | overrides))
    print(generate(args.seed, count=args.scenes, params=p)['story'])


if __name__ == '__main__':
    main()
