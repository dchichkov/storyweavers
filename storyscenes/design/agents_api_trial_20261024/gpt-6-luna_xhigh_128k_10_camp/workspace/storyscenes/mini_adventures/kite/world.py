"""A bounded, offline campsite adventure with atomic local plays."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
import random
from pathlib import Path

from storyscenes.runtime import StoryError
from storyscenes.mini_adventures.local_play import LocalPlay
from .prose import render

SITES = ('tent_edge', 'fern_hollow')
SCENES = (
    'borrow_lantern', 'tell_about_fox', 'shadow_vignette', 'trail_vignette',
    'choose_search', 'search_fox', 'return_to_camp', 'ending_found', 'ending_lost',
)
OPTIONAL = frozenset(('shadow_vignette', 'trail_vignette'))


@dataclass(frozen=True, kw_only=True)
class Parameters:
    toy_site: str = 'fern_hollow'
    kit_memory: str = 'tent_edge'
    daylight_minutes: int = 2
    lantern_charge: int = 2
    toy_covered: bool = True
    ground_wet: bool = False
    search_policy: str = 'sweep'

    def __post_init__(self):
        if type(self.toy_site) is not str or self.toy_site not in SITES:
            raise ValueError('toy_site must be tent_edge or fern_hollow')
        if type(self.kit_memory) is not str or self.kit_memory not in SITES:
            raise ValueError('kit_memory must be tent_edge or fern_hollow')
        if type(self.daylight_minutes) is not int or not 0 <= self.daylight_minutes <= 2:
            raise ValueError('daylight_minutes must be an integer from 0 to 2')
        if type(self.lantern_charge) is not int or not 1 <= self.lantern_charge <= 3:
            raise ValueError('lantern_charge must be an integer from 1 to 3')
        if type(self.toy_covered) is not bool or type(self.ground_wet) is not bool:
            raise ValueError('toy_covered and ground_wet must be booleans')
        if type(self.search_policy) is not str or self.search_policy not in ('conserve', 'sweep'):
            raise ValueError('search_policy must be conserve or sweep')


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        toy_site=rng.choice(SITES),
        kit_memory=rng.choice(SITES),
        daylight_minutes=rng.choice((0, 1, 2)),
        lantern_charge=rng.choice((1, 2, 3)),
        toy_covered=rng.choice((True, False)),
        ground_wet=rng.choice((True, False)),
        search_policy=rng.choice(('conserve', 'sweep')),
    )


def initial(params):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    return {
        'story.ended': False, 'story.outcome': '',
        'camp.location': 'camp', 'mira.location': 'camp', 'kit.location': 'camp',
        'dad.location': 'camp',
        'mira.goal': 'help_kit_and_return_lantern', 'mira.promise': False,
        'mira.search_policy': params.search_policy, 'mira.search_choice_made': False,
        'mira.boots_muddy': False,
        'kit.goal': 'find_pip', 'kit.fear': 0, 'kit.courage': 0,
        'kit.memory_site': params.kit_memory, 'kit.remembers_site': False,
        'kit.hand_in_mira': False, 'kit.boots_muddy': False,
        'kit.has_fox': False, 'kit.comfort': 'none', 'kit.accepted_loss': False,
        'dad.goal': 'keep_children_safe_and_cook_supper', 'dad.used_lantern': False,
        'lantern.owner': 'dad', 'lantern.holder': 'none', 'lantern.location': 'camp_table',
        'lantern.borrowed': False, 'lantern.returned': False, 'lantern.lit': False,
        'lantern.charge': params.lantern_charge, 'lantern.initial_charge': params.lantern_charge,
        'lantern.used_to_search': False, 'lantern.used_to_guide': False,
        'fox.owner': 'kit', 'fox.initial_site': params.toy_site, 'fox.location': params.toy_site,
        'fox.covered_initial': params.toy_covered, 'fox.covered': params.toy_covered,
        'fox.recovered': False,
        'search.started': False, 'search.complete': False, 'search.found': False,
        'search.first_checked': False, 'search.first_area': '', 'search.second_checked': False,
        'search.stop_reason': '',
        'sky.initial_minutes': params.daylight_minutes, 'sky.minutes_left': params.daylight_minutes,
        'ground.wet': params.ground_wet,
        'shadow.played': False, 'trail.lesson': False, 'trail.marked': False,
        'trail.marker_used': False,
        'return.safe': False, 'return.path': '',
    }


_STATE_KEYS = frozenset(initial(Parameters()).keys())
_BOOL_KEYS = frozenset((
    'story.ended', 'mira.promise', 'mira.search_choice_made', 'mira.boots_muddy',
    'kit.remembers_site', 'kit.hand_in_mira', 'kit.boots_muddy', 'kit.has_fox',
    'kit.accepted_loss', 'dad.used_lantern', 'lantern.borrowed', 'lantern.returned',
    'lantern.lit', 'lantern.used_to_search', 'lantern.used_to_guide',
    'fox.covered_initial', 'fox.covered', 'fox.recovered', 'search.started',
    'search.complete', 'search.found', 'search.first_checked', 'search.second_checked',
    'ground.wet', 'shadow.played', 'trail.lesson', 'trail.marked', 'trail.marker_used',
    'return.safe',
))
_STRING_KEYS = _STATE_KEYS - _BOOL_KEYS - frozenset((
    'kit.fear', 'kit.courage', 'lantern.charge', 'lantern.initial_charge',
    'sky.initial_minutes', 'sky.minutes_left',
))


def validate(state):
    if not isinstance(state, dict) or set(state) != _STATE_KEYS:
        raise StoryError('State keys do not match this world')
    for key in _BOOL_KEYS:
        if type(state[key]) is not bool:
            raise StoryError(f'{key} must be boolean')
    for key in ('kit.fear', 'kit.courage', 'lantern.charge', 'lantern.initial_charge',
                'sky.initial_minutes', 'sky.minutes_left'):
        if type(state[key]) is not int:
            raise StoryError(f'{key} must be an integer')
    for key in _STRING_KEYS:
        if type(state[key]) is not str:
            raise StoryError(f'{key} must be a string')
    if state['camp.location'] not in ('camp', *SITES):
        raise StoryError('Unknown campsite location')
    if not (state['mira.location'] == state['kit.location'] == state['camp.location']):
        raise StoryError('The siblings must travel together')
    if state['dad.location'] != 'camp':
        raise StoryError('Dad remains at the family campsite')
    if state['mira.goal'] != 'help_kit_and_return_lantern' or state['kit.goal'] != 'find_pip':
        raise StoryError('Character motives changed unexpectedly')
    if state['dad.goal'] != 'keep_children_safe_and_cook_supper' or state['fox.owner'] != 'kit':
        raise StoryError('Character or toy identity changed unexpectedly')
    if state['fox.initial_site'] not in SITES or state['kit.memory_site'] not in SITES:
        raise StoryError('Invalid remembered or actual toy site')
    if state['mira.search_policy'] not in ('conserve', 'sweep'):
        raise StoryError('Invalid search policy')
    if not 1 <= state['lantern.initial_charge'] <= 3:
        raise StoryError('Invalid initial lantern charge')
    if not 0 <= state['lantern.charge'] <= state['lantern.initial_charge']:
        raise StoryError('Lantern charge cannot be created or negative')
    if not 0 <= state['sky.minutes_left'] <= state['sky.initial_minutes'] <= 2:
        raise StoryError('Daylight cannot increase')
    if not 0 <= state['kit.fear'] <= 2 or state['kit.courage'] not in (0, 1):
        raise StoryError('Invalid emotional state')
    if not state['fox.covered_initial'] and state['fox.covered']:
        raise StoryError('A toy cannot become covered after the search begins')
    if state['fox.location'] not in (*SITES, 'kit_hand', 'kit_bedroll'):
        raise StoryError('Unknown toy location')
    if state['fox.recovered'] != (state['fox.location'] in ('kit_hand', 'kit_bedroll')):
        raise StoryError('Toy location and recovery disagree')
    if state['kit.has_fox'] != (state['fox.location'] == 'kit_bedroll'):
        raise StoryError('Kit and toy locations disagree')
    if state['fox.recovered'] and state['fox.covered']:
        raise StoryError('A covered toy cannot already be recovered')
    if state['lantern.owner'] != 'dad':
        raise StoryError('The borrowed lantern remains Dad’s property')
    holder_location = {'none': 'camp_table', 'mira': 'mira_hand', 'kit': 'kit_hand', 'dad': 'dad_hand'}
    if state['lantern.holder'] not in holder_location or state['lantern.location'] != holder_location[state['lantern.holder']]:
        raise StoryError('Lantern holder and location disagree')
    if state['lantern.borrowed']:
        if state['lantern.returned'] or state['lantern.holder'] not in ('mira', 'kit'):
            raise StoryError('Borrowed lantern is not with a sibling')
    elif state['lantern.returned']:
        if state['lantern.holder'] != 'dad':
            raise StoryError('Returned lantern must be with Dad')
    elif state['lantern.holder'] != 'none':
        raise StoryError('Unborrowed lantern must remain on the camp table')
    if state['lantern.lit'] and state['lantern.charge'] <= 0:
        raise StoryError('An empty lantern cannot be lit')
    if (state['lantern.borrowed'] or state['lantern.returned']) and not state['mira.promise']:
        raise StoryError('The borrowing promise must be enacted')
    if state['shadow.played'] != (state['kit.courage'] == 1):
        raise StoryError('The shadow vignette and earned courage disagree')
    if state['trail.marker_used'] and not state['trail.marked']:
        raise StoryError('Unplaced reflectors cannot guide the return')
    if state['mira.search_choice_made'] != state['search.started']:
        raise StoryError('Search choice and search state disagree')
    if state['search.first_area'] not in ('', *SITES):
        raise StoryError('Unknown first search area')
    if state['search.second_checked'] and not state['search.first_checked']:
        raise StoryError('A second search requires a first search')
    if state['search.complete'] and not (state['search.started'] and state['search.first_checked']):
        raise StoryError('Search completion lacks an enacted search')
    if state['search.found'] != state['fox.recovered']:
        raise StoryError('Search result and toy recovery disagree')
    if state['search.stop_reason'] not in ('', 'found_first', 'found_second', 'conserve', 'low_light'):
        raise StoryError('Unknown search outcome')
    if state['search.complete']:
        if state['search.found'] and state['search.stop_reason'] not in ('found_first', 'found_second'):
            raise StoryError('Found search lacks its enacted result')
        if not state['search.found'] and state['search.stop_reason'] not in ('conserve', 'low_light'):
            raise StoryError('Unsuccessful search lacks a stopping reason')
    if state['kit.comfort'] not in ('none', 'blue_camp_blanket'):
        raise StoryError('Unknown comfort item')
    if state['kit.accepted_loss'] != (state['kit.comfort'] == 'blue_camp_blanket'):
        raise StoryError('Comfort and acceptance disagree')
    if state['return.path'] not in ('', 'lantern', 'reflectors', 'daylight', 'campfire'):
        raise StoryError('Unknown return route')
    if state['return.safe'] != (state['return.path'] != ''):
        raise StoryError('Return route and safety state disagree')
    if state['return.safe'] and (state['camp.location'] != 'camp' or not state['search.complete']):
        raise StoryError('Safe return requires a completed search at camp')
    if state['return.path'] == 'reflectors' and not state['trail.marker_used']:
        raise StoryError('Reflector route was not established')
    if state['return.path'] == 'lantern' and not state['lantern.used_to_guide']:
        raise StoryError('Lantern route was not enacted')
    if state['dad.used_lantern'] and not (state['lantern.returned'] and state['lantern.lit']):
        raise StoryError('Dad can use the lantern only after it is returned and lit')
    if state['story.ended'] != (state['story.outcome'] != ''):
        raise StoryError('Ended state and outcome disagree')
    if state['story.outcome'] not in ('', 'fox_recovered', 'comforted_with_fox_missing'):
        raise StoryError('Unknown ending')
    if state['story.ended']:
        if not (state['return.safe'] and state['camp.location'] == 'camp' and state['lantern.returned']):
            raise StoryError('Ending leaves the family or borrowed lantern unfinished')
        if state['story.outcome'] == 'fox_recovered':
            if not state['kit.has_fox'] or state['kit.accepted_loss']:
                raise StoryError('Success ending does not match the toy state')
        elif state['fox.recovered'] or not state['kit.accepted_loss']:
            raise StoryError('Comfort ending does not match the toy state')
    return None


def _check_params_state(params, state):
    expected = (
        ('fox.initial_site', params.toy_site), ('kit.memory_site', params.kit_memory),
        ('sky.initial_minutes', params.daylight_minutes),
        ('lantern.initial_charge', params.lantern_charge),
        ('fox.covered_initial', params.toy_covered), ('ground.wet', params.ground_wet),
        ('mira.search_policy', params.search_policy),
    )
    if any(state[key] != value for key, value in expected):
        raise StoryError('Parameters do not describe this state')


@dataclass(frozen=True, kw_only=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


def guard(scene_id, state):
    validate(state)
    if scene_id not in SCENES:
        raise StoryError(f'Unknown scene: {scene_id}')
    if state['story.ended']:
        return False
    at_camp = state['camp.location'] == 'camp'
    if scene_id == 'borrow_lantern':
        return at_camp and not state['lantern.borrowed'] and not state['mira.promise']
    if scene_id == 'tell_about_fox':
        return at_camp and state['lantern.borrowed'] and not state['kit.remembers_site']
    if scene_id in ('shadow_vignette', 'trail_vignette'):
        if not (at_camp and state['kit.remembers_site'] and not state['search.started']):
            return False
        if scene_id == 'shadow_vignette':
            return not state['shadow.played']
        return not state['trail.lesson']
    if scene_id == 'choose_search':
        return at_camp and state['kit.remembers_site'] and not state['search.started']
    if scene_id == 'search_fox':
        return state['search.started'] and not state['search.complete'] and state['camp.location'] in SITES
    if scene_id == 'return_to_camp':
        return state['search.complete'] and not state['return.safe'] and state['camp.location'] in SITES
    if scene_id == 'ending_found':
        return state['return.safe'] and at_camp and state['search.found'] and not state['story.ended']
    if scene_id == 'ending_lost':
        return state['return.safe'] and at_camp and not state['search.found'] and not state['story.ended']
    return False


def _recover_fox(play, result):
    site = play.state['camp.location']
    if play.state['fox.covered']:
        play.act('lift_cover_from_fox', requires={'fox.location': site, 'fox.covered': True},
                 **{'fox.covered': False})
    play.act('pick_up_pip', requires={'fox.location': site, 'search.complete': False},
             **{'fox.location': 'kit_hand', 'fox.recovered': True, 'search.found': True,
                'search.complete': True, 'search.stop_reason': result})


def _return_lantern(play):
    play.act('return_lantern_to_dad', requires={'lantern.borrowed': True, 'return.safe': True},
             **{'lantern.borrowed': False, 'lantern.returned': True,
                'lantern.holder': 'dad', 'lantern.location': 'dad_hand'})
    if play.state['lantern.charge'] > 0:
        play.act('dad_lights_supper', requires={'lantern.returned': True, 'lantern.lit': False},
                 **{'lantern.lit': True, 'dad.used_lantern': True})


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    validate(state)
    _check_params_state(params, state)
    if not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    before = deepcopy(state)
    play = LocalPlay(state, actors=('Mira', 'Kit'), validate=validate)

    if scene_id == 'borrow_lantern':
        play.act('dad_lends_lantern', requires={'lantern.owner': 'dad', 'lantern.borrowed': False},
                 **{'lantern.borrowed': True, 'lantern.holder': 'mira', 'lantern.location': 'mira_hand'})
        play.act('promise_to_return_lantern', requires={'lantern.borrowed': True},
                 **{'mira.promise': True})
        play.act('switch_on_lantern', requires={'lantern.charge': play.state['lantern.charge']},
                 **{'lantern.lit': True})
    elif scene_id == 'tell_about_fox':
        play.act('kit_reveals_missing_fox', requires={'lantern.borrowed': True},
                 **{'kit.remembers_site': True, 'kit.fear': 2})
    elif scene_id == 'shadow_vignette':
        play.act('make_fox_shadow_together', requires={'lantern.lit': True, 'kit.fear': 2},
                 **{'shadow.played': True, 'kit.courage': 1, 'kit.fear': 1})
        play.act('kit_takes_the_lantern', requires={'lantern.holder': 'mira'},
                 **{'lantern.holder': 'kit', 'lantern.location': 'kit_hand'})
    elif scene_id == 'trail_vignette':
        play.act('dad_clips_reflectors_to_guyline', requires={'dad.location': 'camp'},
                 **{'trail.lesson': True, 'trail.marked': True})
    elif scene_id == 'choose_search':
        play.act('mira_agrees_search_policy', requires={'mira.search_choice_made': False},
                 **{'mira.search_choice_made': True})
        if not play.state['lantern.lit']:
            play.act('relight_for_search', requires={'lantern.charge': play.state['lantern.charge']},
                     **{'lantern.lit': True})
        site = play.state['kit.memory_site']
        changes = {
            'camp.location': site, 'mira.location': site, 'kit.location': site,
            'search.started': True, 'search.first_area': site,
        }
        action = 'walk_to_tent_edge' if site == 'tent_edge' else 'walk_to_fern_hollow'
        if site == 'fern_hollow' and play.state['ground.wet']:
            changes.update({'mira.boots_muddy': True, 'kit.boots_muddy': True, 'kit.hand_in_mira': True})
            action = 'hold_hands_on_wet_roots'
        play.act(action, requires={'kit.remembers_site': True, 'mira.search_choice_made': True},
                 **changes)
    elif scene_id == 'search_fox':
        charge = play.state['lantern.charge']
        minutes = play.state['sky.minutes_left']
        play.act('sweep_remembered_site',
                 requires={'search.started': True, 'lantern.lit': True, 'lantern.charge': charge},
                 **{'lantern.charge': charge - 1, 'lantern.lit': False,
                    'lantern.used_to_search': True, 'sky.minutes_left': max(0, minutes - 1),
                    'search.first_checked': True})
        if play.state['camp.location'] == play.state['fox.location']:
            _recover_fox(play, 'found_first')
        else:
            policy = play.state['mira.search_policy']
            charge_left = play.state['lantern.charge']
            minutes_left = play.state['sky.minutes_left']
            if policy == 'sweep' and (charge_left > 0 or minutes_left > 0):
                second_site = 'fern_hollow' if play.state['camp.location'] == 'tent_edge' else 'tent_edge'
                changes = {'camp.location': second_site, 'mira.location': second_site,
                           'kit.location': second_site}
                if second_site == 'fern_hollow' and play.state['ground.wet']:
                    changes.update({'mira.boots_muddy': True, 'kit.boots_muddy': True,
                                    'kit.hand_in_mira': True})
                    move_action = 'cross_wet_roots_together'
                else:
                    move_action = 'check_the_other_site'
                play.act(move_action, requires={'search.first_checked': True}, **changes)
                if play.state['lantern.charge'] > 0:
                    if not play.state['lantern.lit']:
                        play.act('relight_for_second_sweep',
                                 requires={'lantern.charge': play.state['lantern.charge']},
                                 **{'lantern.lit': True})
                    charge = play.state['lantern.charge']
                    minutes = play.state['sky.minutes_left']
                    play.act('spend_second_lantern_sweep',
                             requires={'lantern.lit': True, 'lantern.charge': charge},
                             **{'lantern.charge': charge - 1, 'lantern.lit': False,
                                'lantern.used_to_search': True,
                                'sky.minutes_left': max(0, minutes - 1),
                                'search.second_checked': True})
                else:
                    minutes = play.state['sky.minutes_left']
                    play.act('search_in_last_daylight',
                             requires={'sky.minutes_left': minutes},
                             **{'sky.minutes_left': minutes - 1, 'search.second_checked': True})
                if play.state['camp.location'] == play.state['fox.location']:
                    _recover_fox(play, 'found_second')
                else:
                    play.act('stop_after_empty_sweep', requires={'search.second_checked': True},
                             **{'search.complete': True, 'search.stop_reason': 'low_light'})
            else:
                reason = 'conserve' if policy == 'conserve' else 'low_light'
                action = 'turn_back_by_agreement' if reason == 'conserve' else 'stop_when_light_runs_out'
                play.act(action, requires={'search.first_checked': True},
                         **{'search.complete': True, 'search.stop_reason': reason})
    elif scene_id == 'return_to_camp':
        if play.state['lantern.charge'] > 0:
            if not play.state['lantern.lit']:
                play.act('switch_lantern_on_for_return',
                         requires={'lantern.charge': play.state['lantern.charge']},
                         **{'lantern.lit': True})
            charge = play.state['lantern.charge']
            fear = play.state['kit.fear']
            play.act('follow_lantern_beam_home',
                     requires={'lantern.lit': True, 'lantern.charge': charge},
                     **{'lantern.charge': charge - 1, 'lantern.lit': False,
                        'lantern.used_to_guide': True, 'camp.location': 'camp',
                        'mira.location': 'camp', 'kit.location': 'camp',
                        'kit.fear': max(0, fear - 1), 'kit.hand_in_mira': False,
                        'return.safe': True, 'return.path': 'lantern'})
        else:
            fear = play.state['kit.fear']
            if play.state['trail.marked']:
                path = 'reflectors'
                action = 'follow_dads_reflector_tabs'
                extra = {'trail.marker_used': True}
            elif play.state['sky.minutes_left'] > 0:
                path = 'daylight'
                action = 'backtrack_while_the_path_is_visible'
                extra = {}
            else:
                path = 'campfire'
                action = 'follow_the_glow_of_camp'
                extra = {}
            changes = {
                'camp.location': 'camp', 'mira.location': 'camp', 'kit.location': 'camp',
                'kit.fear': max(0, fear - 1), 'kit.hand_in_mira': False,
                'return.safe': True, 'return.path': path,
            }
            changes.update(extra)
            play.act(action, requires={'search.complete': True, 'lantern.charge': 0}, **changes)
    elif scene_id == 'ending_found':
        play.act('settle_pip_beside_kit', requires={'fox.location': 'kit_hand'},
                 **{'fox.location': 'kit_bedroll', 'kit.has_fox': True, 'kit.fear': 0})
        _return_lantern(play)
        play.act('finish_with_pip_home', requires={'kit.has_fox': True, 'lantern.returned': True},
                 **{'story.ended': True, 'story.outcome': 'fox_recovered'})
    elif scene_id == 'ending_lost':
        play.act('offer_kit_the_blue_blanket', requires={'fox.recovered': False},
                 **{'kit.comfort': 'blue_camp_blanket', 'kit.accepted_loss': True, 'kit.fear': 0})
        _return_lantern(play)
        play.act('finish_with_siblings_together', requires={'kit.accepted_loss': True, 'lantern.returned': True},
                 **{'story.ended': True, 'story.outcome': 'comforted_with_fox_missing'})

    after = deepcopy(play.state)
    validate(after)
    text = render(scene_id, params, before, after)
    return Episode(id=scene_id, before=before, after=after,
                   events=tuple(deepcopy(play.events)), text=text)


def _episode_json(episode):
    return {
        'id': episode.id, 'before': deepcopy(episode.before), 'after': deepcopy(episode.after),
        'events': deepcopy(list(episode.events)), 'text': episode.text,
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise TypeError('params must be a Parameters instance')
    if not isinstance(path, (tuple, list)):
        raise TypeError('path must be a list or tuple of scene IDs')
    state = initial(params)
    episodes = []
    used = set()
    for scene_id in path:
        if scene_id in used:
            raise StoryError('A scene cannot be repeated in this scenario')
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode.after
        used.add(scene_id)
    return tuple(episodes)


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    chosen = parameters(seed) if params is None else params
    if not isinstance(chosen, Parameters):
        raise TypeError('params must be a Parameters instance')
    rng = random.Random(seed)
    attempts = 0

    def visit(state, episodes, used):
        nonlocal attempts
        remaining = count - len(episodes)
        if remaining == 0:
            return episodes if state['story.ended'] else None
        choices = [scene_id for scene_id in SCENES
                   if scene_id not in used and guard(scene_id, state)
                   and (not scene_id.startswith('ending_') or remaining == 1)]
        rng.shuffle(choices)
        for scene_id in choices:
            attempts += 1
            if attempts > 10000:
                raise StoryError('Bounded scene search exhausted its 10000-attempt budget')
            episode = play_scene(chosen, state, scene_id)
            result = visit(episode.after, episodes + (episode,), used | {scene_id})
            if result is not None:
                return result
        return None

    result = visit(initial(chosen), (), frozenset())
    if result is None:
        raise StoryError('No compatible route reaches an ending at this scene count')
    final_state = deepcopy(result[-1].after)
    rows = [_episode_json(episode) for episode in result]
    return {
        'seed': seed,
        'parameters': asdict(chosen),
        'scene_count': count,
        'path': [episode.id for episode in result],
        'story': '\n\n'.join(episode.text for episode in result),
        'episodes': rows,
        'final_state': final_state,
        'search_attempts': attempts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    parser.add_argument('--params', type=Path, help='JSON file of Parameters overrides')
    args = parser.parse_args()
    chosen = parameters(args.seed)
    if args.params:
        overrides = json.loads(args.params.read_text(encoding='utf-8'))
        if not isinstance(overrides, dict):
            parser.error('--params must contain a JSON object')
        chosen = Parameters(**(asdict(chosen) | overrides))
    row = generate(args.seed, count=args.scenes, params=chosen)
    print(row['story'])


if __name__ == '__main__':
    main()
