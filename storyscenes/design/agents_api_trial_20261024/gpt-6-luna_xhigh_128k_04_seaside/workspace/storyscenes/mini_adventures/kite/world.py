from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
import re

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .prose import render


@dataclass(frozen=True, kw_only=True)
class Parameters:
    older_name: str = 'Mara'
    younger_name: str = 'Niko'
    tide: str = 'low'
    wind: str = 'calm'
    map_rotated: bool = False
    legend_faded: bool = False

    def __post_init__(self):
        for field in ('older_name', 'younger_name'):
            value = getattr(self, field)
            if type(value) is not str or not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]{0,23}', value):
                raise ValueError(f'{field} must be a short plain name')
        if self.older_name.casefold() == self.younger_name.casefold():
            raise ValueError('The siblings need distinct names')
        if type(self.tide) is not str or self.tide not in ('low', 'rising'):
            raise ValueError('tide must be low or rising')
        if type(self.wind) is not str or self.wind not in ('calm', 'gusty'):
            raise ValueError('wind must be calm or gusty')
        for field in ('map_rotated', 'legend_faded'):
            if type(getattr(self, field)) is not bool:
                raise ValueError(f'{field} must be boolean')


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        tide=rng.choice(('low', 'rising')),
        wind=rng.choice(('calm', 'gusty')),
        map_rotated=rng.choice((False, True)),
        legend_faded=rng.choice((False, True)),
    )


def initial(params):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    return {
        'story.ended': False, 'story.outcome': '',
        'party.location': 'kiosk', 'party.goal': '', 'party.route': '',
        'party.destination': '', 'party.choice': '', 'party.mistake': False,
        'party.knows_wrong': False, 'party.shelter_found': False,
        'party.picnic_done': False, 'party.shared_choice': False,
        'party.returned_map': False,
        'shore.tide': params.tide, 'weather.wind': params.wind,
        'older.name': params.older_name, 'younger.name': params.younger_name,
        'older.goal': 'find a sheltered place before the tide turns',
        'younger.goal': 'have a real say in the route',
        'older.ignored_warning': False, 'older.admitted_mistake': False,
        'younger.asked_map': False, 'younger.spoke_up': False,
        'younger.chose_seat': False, 'siblings.shared_pause': False,
        'map.holder': 'aunt', 'map.location': 'kiosk', 'map.borrowed': False,
        'map.orientation': 'rotated' if params.map_rotated else 'upright',
        'map.legend': 'faded' if params.legend_faded else 'clear',
        'map.read': False, 'map.clue_source': '', 'map.corrected': False,
        'map.correction': '',
        'fisher.location': 'gull_post', 'fisher.float': 'snagged',
        'fisher.helped': False, 'fisher.clue': False,
        'shell.holder': 'tidepool',
        'blanket.location': 'older', 'blanket.secured': False,
        'blanket.anchor': 'unset', 'food.status': 'packed',
    }


_STATE_KEYS = frozenset(initial(Parameters()))


def validate(state):
    if type(state) is not dict or set(state) != _STATE_KEYS:
        raise StoryError('State has missing or undeclared keys')
    if any(type(value) not in (str, bool, int) for value in state.values()):
        raise StoryError('State values must be JSON-native scalars')
    if state['party.location'] not in {
        'kiosk', 'fork', 'gull_post', 'strand_turn', 'bluff_path',
        'crescent_cove', 'harbor_awning',
    }:
        raise StoryError('Unknown party location')
    if state['party.goal'] not in ('', 'sheltered_picnic'):
        raise StoryError('Unknown party goal')
    if state['shore.tide'] not in ('low', 'rising') or state['weather.wind'] not in ('calm', 'gusty'):
        raise StoryError('Invalid environmental state')
    if state['map.orientation'] not in ('rotated', 'upright') or state['map.legend'] not in ('faded', 'clear'):
        raise StoryError('Invalid map state')
    if state['map.clue_source'] not in ('', 'fisher', 'legend', 'coastline'):
        raise StoryError('Invalid map clue')
    if state['map.holder'] not in ('aunt', 'younger'):
        raise StoryError('Unknown map holder')
    if state['map.borrowed'] != (state['map.holder'] != 'aunt'):
        raise StoryError('Map custody and loan status disagree')
    expected_map_location = 'kiosk' if state['map.holder'] == 'aunt' else 'party'
    if state['map.location'] != expected_map_location:
        raise StoryError('Map location and holder disagree')
    if state['party.goal'] == '' and (state['map.borrowed'] or state['party.location'] != 'kiosk'):
        raise StoryError('The expedition cannot start without borrowing the map')
    if state['map.borrowed'] and state['party.goal'] != 'sheltered_picnic':
        raise StoryError('A borrowed map needs an active purpose')
    if state['party.knows_wrong'] and not (state['party.mistake'] and state['map.read']):
        raise StoryError('The landmark correction lacks evidence')
    if state['older.admitted_mistake'] != state['party.knows_wrong']:
        raise StoryError('The apology and landmark discovery disagree')
    if state['older.ignored_warning'] != (state['party.mistake'] and not state['party.knows_wrong']):
        raise StoryError('The warning state is inconsistent')
    if not state['party.mistake']:
        if state['party.location'] not in ('kiosk', 'fork') or state['party.knows_wrong']:
            raise StoryError('The party moved before the mistaken turn')
    elif not state['party.route'] and state['party.location'] != 'gull_post':
        raise StoryError('The mistaken landmark must be reached before choosing a route')
    if state['party.route'] == '':
        if state['party.destination'] or state['party.choice'] or state['party.shared_choice']:
            raise StoryError('Route details exist before a route was chosen')
    elif state['party.route'] == 'strand':
        if state['shore.tide'] != 'low' or state['party.destination'] != 'crescent_cove' or state['party.choice'] != 'strand':
            raise StoryError('The low-tide route is inconsistent')
        if state['party.location'] not in ('strand_turn', 'crescent_cove', 'kiosk'):
            raise StoryError('The party left the strand route')
    elif state['party.route'] == 'bluff':
        if state['shore.tide'] != 'rising' or state['party.destination'] != 'harbor_awning' or state['party.choice'] != 'bluff':
            raise StoryError('The rising-tide route is inconsistent')
        if state['party.location'] not in ('bluff_path', 'harbor_awning', 'kiosk'):
            raise StoryError('The party left the bluff route')
    else:
        raise StoryError('Unknown route')
    if state['party.route'] and not (state['party.knows_wrong'] and state['party.shared_choice']):
        raise StoryError('The route was chosen without correcting the map together')
    target_locations = ('crescent_cove', 'harbor_awning')
    if state['party.shelter_found']:
        if state['party.location'] not in target_locations + ('kiosk',):
            raise StoryError('Shelter flag and location disagree')
        expected = 'crescent_cove' if state['party.route'] == 'strand' else 'harbor_awning'
        if not state['party.route'] or (state['party.location'] != 'kiosk' and state['party.location'] != expected):
            raise StoryError('The found shelter does not match the route')
    elif state['party.location'] in target_locations:
        raise StoryError('A shelter location must be recorded as found')
    if state['younger.chose_seat'] and not state['party.shelter_found']:
        raise StoryError('A picnic seat was chosen before reaching shelter')
    if state['party.shared_pause'] is False and (
        state['shell.holder'] != 'tidepool' or state['younger.chose_seat']
    ):
        raise StoryError('A vignette consequence was lost')
    if state['fisher.location'] != 'gull_post':
        raise StoryError('The fisher is no longer at the post')
    if state['fisher.float'] not in ('snagged', 'returned'):
        raise StoryError('Unknown net-float location')
    if state['fisher.helped'] != (state['fisher.float'] == 'returned') or state['fisher.clue'] != state['fisher.helped']:
        raise StoryError('The fisher exchange is inconsistent')
    if state['shell.holder'] not in ('tidepool', 'younger', 'blanket'):
        raise StoryError('Unknown shell holder')
    if state['blanket.location'] not in ('older', 'shelter'):
        raise StoryError('Unknown blanket location')
    if state['blanket.anchor'] not in ('unset', 'calm_air', 'stones', 'bench'):
        raise StoryError('Unknown blanket anchor')
    if state['blanket.secured'] != (state['blanket.anchor'] != 'unset'):
        raise StoryError('Blanket security and anchor disagree')
    if state['food.status'] not in ('packed', 'open', 'eaten'):
        raise StoryError('Unknown food state')
    if state['party.picnic_done'] != (state['food.status'] == 'eaten'):
        raise StoryError('Picnic and food states disagree')
    if state['party.picnic_done'] and (
        not state['party.shelter_found'] or not state['blanket.secured']
        or state['blanket.location'] not in ('shelter', 'older')
    ):
        raise StoryError('The picnic is incomplete')
    if state['map.corrected'] != state['party.ended']:
        raise StoryError('The map correction and ending disagree')
    if state['party.returned_map'] != state['party.ended']:
        raise StoryError('Map return and ending disagree')
    if state['party.ended']:
        if not (state['party.picnic_done'] and state['party.shelter_found']):
            raise StoryError('The ending has no completed sheltered picnic')
        if state['party.location'] != 'kiosk' or state['map.holder'] != 'aunt' or state['map.location'] != 'kiosk':
            raise StoryError('The map was not returned at the kiosk')
        if state['blanket.location'] != 'older' or not state['party.shared_choice']:
            raise StoryError('The party left an ending action unfinished')
        if not state['map.correction'] or not state['story.outcome']:
            raise StoryError('The ending needs a useful map and an outcome')
    elif state['story.outcome'] or state['map.correction']:
        raise StoryError('An unfinished story has an ending result')


SCENES = (
    'borrow_map', 'follow_white_gull', 'tidepool_pause', 'fisher_pause',
    'compare_landmarks', 'choose_safe_route', 'reach_shelter',
    'windbreak_pause', 'picnic', 'ending_cove', 'ending_harbor',
)


def guard(scene_id, state):
    validate(state)
    if scene_id not in SCENES:
        raise StoryError(f'Unknown scene: {scene_id}')
    if state['story.ended']:
        return False
    loc = state['party.location']
    if scene_id == 'borrow_map':
        return loc == 'kiosk' and state['party.goal'] == '' and state['map.holder'] == 'aunt'
    if scene_id == 'follow_white_gull':
        return loc == 'kiosk' and state['party.goal'] == 'sheltered_picnic' and state['map.borrowed'] and not state['party.mistake']
    if scene_id == 'tidepool_pause':
        return loc == 'gull_post' and state['shore.tide'] == 'low' and state['shell.holder'] == 'tidepool' and not state['party.knows_wrong']
    if scene_id == 'fisher_pause':
        return loc == 'gull_post' and not state['fisher.helped'] and not state['party.knows_wrong']
    if scene_id == 'compare_landmarks':
        return loc == 'gull_post' and state['party.mistake'] and not state['party.knows_wrong'] and state['map.borrowed']
    if scene_id == 'choose_safe_route':
        return loc == 'gull_post' and state['party.knows_wrong'] and not state['party.route']
    if scene_id == 'reach_shelter':
        return ((loc == 'strand_turn' and state['party.route'] == 'strand')
                or (loc == 'bluff_path' and state['party.route'] == 'bluff')) and not state['party.shelter_found']
    if scene_id == 'windbreak_pause':
        return loc in ('crescent_cove', 'harbor_awning') and state['party.shelter_found'] and not state['younger.chose_seat'] and not state['party.picnic_done']
    if scene_id == 'picnic':
        return loc in ('crescent_cove', 'harbor_awning') and state['party.shelter_found'] and not state['party.picnic_done']
    if scene_id == 'ending_cove':
        return loc == 'crescent_cove' and state['party.route'] == 'strand' and state['party.picnic_done']
    if scene_id == 'ending_harbor':
        return loc == 'harbor_awning' and state['party.route'] == 'bluff' and state['party.picnic_done']
    return False


def _set(play, action, requires, changes):
    play.act(action, requires, **changes)


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    validate(state)
    if scene_id not in SCENES or not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    play = LocalPlay(state, actors=('older', 'younger', 'aunt', 'fisher'), validate=validate)

    if scene_id == 'borrow_map':
        _set(play, 'ask_aunt_for_map', {'party.location': 'kiosk', 'map.holder': 'aunt'}, {
            'party.goal': 'sheltered_picnic', 'younger.asked_map': True,
        })
        _set(play, 'borrow_aunts_map', {'party.goal': 'sheltered_picnic', 'map.borrowed': False}, {
            'map.holder': 'younger', 'map.location': 'party', 'map.borrowed': True,
        })
    elif scene_id == 'follow_white_gull':
        _set(play, 'walk_to_path_fork', {'party.location': 'kiosk', 'map.borrowed': True}, {
            'party.location': 'fork',
        })
        _set(play, 'follow_white_gull_post', {'party.location': 'fork', 'map.borrowed': True}, {
            'party.location': 'gull_post', 'party.mistake': True,
            'younger.spoke_up': True, 'older.ignored_warning': True,
        })
    elif scene_id == 'tidepool_pause':
        _set(play, 'pick_up_striped_shell', {'party.location': 'gull_post', 'shell.holder': 'tidepool'}, {
            'shell.holder': 'younger', 'siblings.shared_pause': True,
        })
    elif scene_id == 'fisher_pause':
        _set(play, 'free_fishers_net_float', {'party.location': 'gull_post', 'fisher.float': 'snagged'}, {
            'fisher.float': 'returned', 'fisher.helped': True, 'fisher.clue': True,
            'siblings.shared_pause': True,
        })
    elif scene_id == 'compare_landmarks':
        if play.state['map.orientation'] == 'rotated':
            _set(play, 'turn_map_north', {'map.orientation': 'rotated'}, {
                'map.orientation': 'upright',
            })
        if play.state['fisher.clue']:
            _set(play, 'use_fishers_landing_clue', {'map.orientation': 'upright', 'fisher.clue': True}, {
                'map.read': True, 'map.clue_source': 'fisher', 'party.knows_wrong': True,
                'older.admitted_mistake': True, 'older.ignored_warning': False,
            })
        else:
            if play.state['map.legend'] == 'clear':
                _set(play, 'read_clear_map_legend', {'map.orientation': 'upright', 'map.legend': 'clear'}, {
                    'map.read': True, 'map.clue_source': 'legend',
                })
            else:
                _set(play, 'trace_coastline_on_faded_map', {'map.orientation': 'upright', 'map.legend': 'faded'}, {
                    'map.read': True, 'map.clue_source': 'coastline',
                })
            _set(play, 'match_post_to_shoreline', {'map.read': True, 'party.mistake': True}, {
                'party.knows_wrong': True, 'older.admitted_mistake': True,
                'older.ignored_warning': False,
            })
    elif scene_id == 'choose_safe_route':
        if play.state['shore.tide'] == 'low':
            _set(play, 'choose_low_strand_together', {
                'party.location': 'gull_post', 'party.knows_wrong': True, 'shore.tide': 'low',
            }, {
                'party.location': 'strand_turn', 'party.route': 'strand',
                'party.destination': 'crescent_cove', 'party.choice': 'strand',
                'party.shared_choice': True,
            })
        else:
            _set(play, 'choose_high_bluff_together', {
                'party.location': 'gull_post', 'party.knows_wrong': True, 'shore.tide': 'rising',
            }, {
                'party.location': 'bluff_path', 'party.route': 'bluff',
                'party.destination': 'harbor_awning', 'party.choice': 'bluff',
                'party.shared_choice': True,
            })
    elif scene_id == 'reach_shelter':
        if play.state['party.route'] == 'strand':
            _set(play, 'reach_half_moon_cove', {'party.location': 'strand_turn', 'shore.tide': 'low'}, {
                'party.location': 'crescent_cove', 'party.shelter_found': True,
            })
        else:
            _set(play, 'reach_harbor_awning', {'party.location': 'bluff_path', 'shore.tide': 'rising'}, {
                'party.location': 'harbor_awning', 'party.shelter_found': True,
            })
    elif scene_id == 'windbreak_pause':
        _set(play, 'let_younger_choose_the_seat', {
            'party.shelter_found': True, 'younger.chose_seat': False,
        }, {
            'younger.chose_seat': True, 'siblings.shared_pause': True,
        })
    elif scene_id == 'picnic':
        _set(play, 'unroll_blanket_in_shelter', {
            'party.shelter_found': True, 'blanket.location': 'older',
        }, {'blanket.location': 'shelter'})
        if play.state['weather.wind'] == 'gusty':
            anchor = 'stones' if play.state['party.location'] == 'crescent_cove' else 'bench'
            _set(play, 'weight_blanket_against_gusts', {
                'blanket.location': 'shelter', 'blanket.secured': False,
            }, {'blanket.secured': True, 'blanket.anchor': anchor})
        else:
            _set(play, 'spread_blanket_in_still_air', {
                'blanket.location': 'shelter', 'blanket.secured': False,
            }, {'blanket.secured': True, 'blanket.anchor': 'calm_air'})
        _set(play, 'open_lunch_basket', {'food.status': 'packed'}, {'food.status': 'open'})
        if play.state['shell.holder'] == 'younger':
            _set(play, 'set_shell_beside_map', {'shell.holder': 'younger'}, {'shell.holder': 'blanket'})
        _set(play, 'share_the_packed_lunch', {
            'food.status': 'open', 'blanket.secured': True,
        }, {'food.status': 'eaten', 'party.picnic_done': True})
    else:
        if play.state['shell.holder'] == 'blanket':
            _set(play, 'pick_up_shell_before_leaving', {'shell.holder': 'blanket'}, {
                'shell.holder': 'younger',
            })
        _set(play, 'fold_blanket_after_lunch', {'blanket.location': 'shelter'}, {
            'blanket.location': 'older',
        })
        location = 'crescent_cove' if scene_id == 'ending_cove' else 'harbor_awning'
        _set(play, 'walk_back_to_aunt_junes_kiosk', {'party.location': location, 'party.picnic_done': True}, {
            'party.location': 'kiosk',
        })
        if scene_id == 'ending_cove':
            outcome = 'A sheltered picnic at Crescent Cove; the corrected map is returned.'
            correction = 'White gull post is the ferry landing; the half-moon marks Crescent Cove.'
        else:
            outcome = 'A sheltered picnic beneath the harbor awning; the corrected map is returned.'
            correction = 'White gull post is the ferry landing; the bluff reaches the harbor awning at rising tide.'
        _set(play, 'return_corrected_map_and_finish', {
            'party.location': 'kiosk', 'map.holder': 'younger', 'map.borrowed': True,
            'party.picnic_done': True,
        }, {
            'map.holder': 'aunt', 'map.location': 'kiosk', 'map.borrowed': False,
            'map.corrected': True, 'map.correction': correction,
            'party.returned_map': True, 'story.ended': True, 'story.outcome': outcome,
        })

    after = deepcopy(play.state)
    return {
        'id': scene_id,
        'before': deepcopy(state),
        'after': after,
        'events': deepcopy(play.events),
        'text': render(scene_id, params, state, after),
    }


def _minimum_remaining(state):
    if state['story.ended']:
        return 0
    if not state['party.goal']:
        return 7
    if not state['party.mistake']:
        return 6
    if not state['party.knows_wrong']:
        return 5
    if not state['party.route']:
        return 4
    if not state['party.shelter_found']:
        return 3
    if not state['party.picnic_done']:
        return 2
    return 1


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    params = parameters(seed) if params is None else params
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    rng = random.Random(seed)
    attempts = 0
    nodes = 0

    def search(state, path):
        nonlocal attempts, nodes
        nodes += 1
        if nodes > 4000:
            raise StoryError('Bounded scene search exhausted its node budget')
        remaining = count - len(path)
        if remaining < _minimum_remaining(state):
            return None
        if remaining == 0:
            return path if state['story.ended'] else None
        used = {episode['id'] for episode in path}
        choices = [scene_id for scene_id in SCENES if scene_id not in used and guard(scene_id, state)]
        rng.shuffle(choices)
        for scene_id in choices:
            attempts += 1
            if attempts > 10000:
                raise StoryError('Bounded scene search exhausted its attempt budget')
            episode = play_scene(params, state, scene_id)
            answer = search(episode['after'], path + [episode])
            if answer is not None:
                return answer
        return None

    episodes = search(initial(params), [])
    if episodes is None:
        raise StoryError('No compatible story reaches an ending at this length')
    texts = [episode['text'] for episode in episodes]
    return {
        'seed': seed,
        'parameters': asdict(params),
        'scene_count': count,
        'path': [episode['id'] for episode in episodes],
        'story': '\n\n'.join(texts),
        'episodes': deepcopy(episodes),
        'final_state': deepcopy(episodes[-1]['after']),
        'search_attempts': attempts,
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    if isinstance(path, (str, bytes)):
        raise ValueError('path must be a sequence of scene IDs')
    state = initial(params)
    episodes = []
    for scene_id in path:
        if scene_id in {episode['id'] for episode in episodes}:
            raise StoryError('A scene cannot be repeated')
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode['after']
    return episodes


def main():
    parser = argparse.ArgumentParser(description='Generate an offline seaside-path mini-adventure.')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    parser.add_argument('--params', type=Path, help='Optional JSON object of parameter overrides')
    args = parser.parse_args()
    base = asdict(parameters(args.seed))
    if args.params:
        overrides = json.loads(args.params.read_text(encoding='utf-8'))
        if not isinstance(overrides, dict):
            parser.error('--params must contain a JSON object')
        base.update(overrides)
    try:
        params = Parameters(**base)
        row = generate(args.seed, count=args.scenes, params=params)
    except (ValueError, StoryError) as exc:
        parser.error(str(exc))
    print(row['story'])


if __name__ == '__main__':
    main()
