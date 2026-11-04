'''Bounded, stateful mini-adventure about a borrowed sled and a snowy errand.'''
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
    route_choice: str = 'patient'
    snow_cm: int = 8
    runner_condition: str = 'sound'
    load_kg: int = 2
    has_mittens: bool = True
    friend_race_pressure: int = 2

    def __post_init__(self):
        if self.route_choice not in ('patient', 'race'):
            raise ValueError('route_choice must be patient or race')
        if type(self.snow_cm) is not int or not 0 <= self.snow_cm <= 20:
            raise ValueError('snow_cm must be an integer from 0 through 20')
        if self.runner_condition not in ('sound', 'loose'):
            raise ValueError('runner_condition must be sound or loose')
        if type(self.load_kg) is not int or not 1 <= self.load_kg <= 4:
            raise ValueError('load_kg must be an integer from 1 through 4')
        if type(self.has_mittens) is not bool:
            raise ValueError('has_mittens must be boolean')
        if type(self.friend_race_pressure) is not int or not 1 <= self.friend_race_pressure <= 3:
            raise ValueError('friend_race_pressure must be an integer from 1 through 3')


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        route_choice=rng.choice(('patient', 'race')),
        snow_cm=rng.choice((3, 8, 15)),
        runner_condition=rng.choice(('sound', 'loose')),
        load_kg=rng.choice((1, 2, 3)),
        has_mittens=rng.choice((True, False)),
        friend_race_pressure=rng.choice((1, 2, 3)),
    )


def initial(params):
    if not isinstance(params, Parameters):
        raise TypeError('params must be Parameters')
    return {
        'story.ended': False,
        'story.outcome': '',
        'square.snow_cm': params.snow_cm,
        'child.location': 'square',
        'child.route_choice': params.route_choice,
        'child.route': '',
        'child.route_taken': '',
        'child.journey_result': '',
        'child.hands_cold': False,
        'child.tired': False,
        'child.feeling': 'hopeful',
        'friend.location': 'square',
        'friend.race_pressure': params.friend_race_pressure,
        'friend.mood': 'curious',
        'friend.following': False,
        'friend.helped': False,
        'friend.knows_lane': False,
        'bundle.location': 'stall',
        'bundle.owner': 'child',
        'bundle.contents': 'all',
        'bundle.secured': False,
        'bundle.weight_kg': params.load_kg,
        'sled.owner': 'stallkeeper',
        'sled.location': 'stall',
        'sled.condition': params.runner_condition,
        'sled.start_condition': params.runner_condition,
        'sled.borrowed': False,
        'sled.borrowed_once': False,
        'sled.used_for_delivery': False,
        'sled.load_kg': 0,
        'sled.returned': False,
        'sled.repaired': False,
        'sled.checked': False,
        'mittens.owner': 'child' if params.has_mittens else 'friend',
        'mittens.location': 'child' if params.has_mittens else 'friend',
        'mittens.available': params.has_mittens,
        'mittens.worn': params.has_mittens,
        'mittens.borrowed': False,
        'mittens.secured': False,
        'mittens.used': False,
        'mittens.returned': False,
        'neighbor.location': 'home',
        'neighbor.received_supplies': False,
        'neighbor.received_soup': False,
        'neighbor.lamp_lit': False,
        'neighbor.feeling': 'waiting',
    }


SCENES = (
    'borrow_sled', 'prepare_supplies', 'mittens_vignette', 'bell_vignette',
    'race_decision', 'journey', 'deliver_supplies', 'return_sled',
    'ending_patient', 'ending_race', 'ending_spill',
)


def validate(state):
    if not isinstance(state, dict) or set(state) != set(initial(Parameters()).keys()):
        raise StoryError('State has missing or undeclared keys')
    bool_keys = {
        'story.ended', 'child.hands_cold', 'child.tired', 'friend.following',
        'friend.helped', 'friend.knows_lane', 'bundle.secured', 'sled.borrowed',
        'sled.borrowed_once', 'sled.used_for_delivery', 'sled.returned',
        'sled.repaired', 'sled.checked', 'mittens.available', 'mittens.worn',
        'mittens.borrowed', 'mittens.secured', 'mittens.used', 'mittens.returned',
        'neighbor.received_supplies', 'neighbor.received_soup', 'neighbor.lamp_lit',
    }
    int_keys = {'square.snow_cm', 'friend.race_pressure', 'bundle.weight_kg', 'sled.load_kg'}
    for key in bool_keys:
        if type(state[key]) is not bool:
            raise StoryError(f'{key} must be boolean')
    for key in int_keys:
        if type(state[key]) is not int:
            raise StoryError(f'{key} must be an integer')
    for key in set(state) - bool_keys - int_keys:
        if type(state[key]) is not str:
            raise StoryError(f'{key} must be a string')

    choices = {
        'child.route_choice': ('patient', 'race'),
        'child.route': ('', 'patient', 'race'),
        'child.route_taken': ('', 'bakery_lane', 'square_road', 'straight_run'),
        'child.journey_result': ('', 'patient', 'race_clean', 'race_spill'),
        'child.feeling': ('hopeful', 'settled', 'buoyant', 'relieved'),
        'friend.location': ('square', 'road', 'neighbor'),
        'friend.mood': ('curious', 'good_humored', 'stung', 'eager', 'helpful', 'pleased', 'concerned', 'honest'),
        'bundle.location': ('stall', 'square', 'sled', 'road', 'child', 'neighbor'),
        'bundle.owner': ('child', 'neighbor'),
        'bundle.contents': ('all', 'bread_oil'),
        'sled.owner': ('stallkeeper', 'child'),
        'sled.location': ('stall', 'square', 'road', 'neighbor'),
        'sled.condition': ('sound', 'loose', 'needs_repair'),
        'sled.start_condition': ('sound', 'loose'),
        'mittens.owner': ('child', 'friend'),
        'mittens.location': ('child', 'friend'),
        'neighbor.location': ('home',),
        'neighbor.feeling': ('waiting', 'grateful', 'understanding'),
        'story.outcome': ('', 'patient_delivery', 'race_delivery', 'spill_recovery'),
    }
    for key, allowed in choices.items():
        if state[key] not in allowed:
            raise StoryError(f'Invalid value for {key}')
    if not 0 <= state['square.snow_cm'] <= 20 or not 1 <= state['bundle.weight_kg'] <= 4:
        raise StoryError('Snow or bundle weight is outside its range')
    if not 1 <= state['friend.race_pressure'] <= 3:
        raise StoryError('Friend race pressure is outside its range')
    if state['sled.start_condition'] != state['sled.condition'] and not state['sled.repaired'] and state['sled.condition'] == 'sound':
        raise StoryError('A changed runner needs an enacted repair')

    if state['mittens.worn'] != (state['mittens.location'] == 'child'):
        raise StoryError('Worn mittens must be with Mina')
    if state['mittens.available']:
        if state['mittens.owner'] != 'child' or state['mittens.borrowed'] or state['mittens.returned']:
            raise StoryError('Owned mittens cannot become a loan')
    else:
        if state['mittens.owner'] != 'friend':
            raise StoryError('The spare mittens belong to Jo')
        if not state['mittens.borrowed'] and (state['mittens.location'] != 'friend' or state['mittens.worn']):
            raise StoryError('Unborrowed mittens must remain with Jo')
        if state['mittens.borrowed'] and state['mittens.location'] == 'friend' and not state['mittens.returned']:
            raise StoryError('Borrowed mittens returned without a return action')
        if state['mittens.returned'] and (not state['mittens.borrowed'] or state['mittens.location'] != 'friend' or state['mittens.worn']):
            raise StoryError('Returned mittens have inconsistent custody')
    if state['mittens.used'] and (state['child.journey_result'] == '' or not (state['mittens.available'] or state['mittens.borrowed'])):
        raise StoryError('Mittens use must follow a journey')

    if state['sled.borrowed'] != (state['sled.owner'] == 'child'):
        raise StoryError('Sled owner and current loan status disagree')
    if state['sled.borrowed_once'] != (state['sled.borrowed'] or state['sled.returned']):
        raise StoryError('Sled loan history is inconsistent')
    if state['sled.location'] == 'stall' and state['sled.owner'] != 'stallkeeper':
        raise StoryError('A borrowed sled cannot be at the stall')
    if state['sled.borrowed'] and state['sled.location'] == 'stall':
        raise StoryError('The borrowed sled is still at the stall')
    if state['sled.used_for_delivery'] and not state['sled.borrowed_once']:
        raise StoryError('The sled cannot be used before it is borrowed')
    if state['sled.load_kg'] not in (0, state['bundle.weight_kg']):
        raise StoryError('Sled load and bundle weight disagree')
    if state['bundle.location'] == 'sled' and (not state['sled.borrowed'] or not state['bundle.secured']):
        raise StoryError('A bundle on the sled must be secured to a borrowed sled')
    if state['bundle.secured'] and state['bundle.location'] != 'sled':
        raise StoryError('A secured bundle must be on the sled')
    if state['bundle.location'] in ('road', 'child') and state['bundle.contents'] != 'bread_oil':
        raise StoryError('Only salvaged provisions can be on the road or carried by Mina')
    if state['bundle.location'] == 'neighbor' and state['bundle.owner'] != 'neighbor':
        raise StoryError('Delivered provisions belong to Mr. Vale')
    if state['bundle.location'] != 'neighbor' and state['bundle.owner'] != 'child':
        raise StoryError('Undelivered provisions remain with Mina')

    result = state['child.journey_result']
    route = state['child.route']
    if result == '' and (state['child.route_taken'] != '' or state['child.hands_cold'] or state['child.tired'] or state['mittens.used']):
        raise StoryError('Journey effects appeared before travel')
    if result != '' and route == '':
        raise StoryError('Travel requires a route choice')
    if route == '' and (result != '' or state['child.location'] != 'square'):
        raise StoryError('Mina moved before choosing a route')
    if result == 'patient' and (route != 'patient' or state['child.route_taken'] != ('bakery_lane' if state['friend.knows_lane'] else 'square_road')):
        raise StoryError('Patient route does not match the known lane')
    if result in ('race_clean', 'race_spill') and (route != 'race' or state['child.route_taken'] != 'straight_run'):
        raise StoryError('Race result does not match the chosen route')
    if result == 'race_spill' and state['bundle.contents'] != 'bread_oil':
        raise StoryError('A race spill must lose the soup')
    if result in ('patient', 'race_clean') and state['bundle.contents'] != 'all':
        raise StoryError('A full delivery must retain all provisions')
    if result == '' and state['bundle.contents'] != 'all':
        raise StoryError('Provisions cannot spill before the journey')
    if result != '' and state['child.hands_cold'] != (not state['mittens.used']):
        raise StoryError('Cold hands must reflect the grip used on the journey')
    if result == 'patient' and state['child.tired'] != (state['square.snow_cm'] >= 12 and not state['friend.knows_lane']):
        raise StoryError('Patient-route fatigue does not match snow and route knowledge')
    if result == 'race_clean' and state['child.tired']:
        raise StoryError('A clean race cannot leave the recorded spill fatigue')
    if result == 'race_spill' and not state['child.tired']:
        raise StoryError('A spill must leave the children tired')
    if state['child.location'] == 'road' and (result == '' or state['neighbor.received_supplies']):
        raise StoryError('Road location does not match journey progress')
    if state['child.location'] == 'neighbor' and not state['neighbor.received_supplies']:
        raise StoryError('Mina cannot arrive before the delivery')
    if state['neighbor.received_supplies'] != (state['bundle.location'] == 'neighbor'):
        raise StoryError('Delivery and bundle location disagree')
    if state['neighbor.lamp_lit'] != state['neighbor.received_supplies']:
        raise StoryError('The delivered lamp oil must be used at the home')
    if state['neighbor.received_soup'] != (state['neighbor.received_supplies'] and state['bundle.contents'] == 'all'):
        raise StoryError('Soup delivery does not match the bundle contents')
    if state['neighbor.received_supplies'] and state['neighbor.feeling'] == 'waiting':
        raise StoryError('The neighbor has not responded to a completed delivery')
    if state['friend.helped'] and result == '':
        raise StoryError('Jo cannot help on a journey that has not begun')
    if state['sled.used_for_delivery'] != (result != ''):
        raise StoryError('Sled use and journey do not agree')
    if state['sled.returned'] and (not state['neighbor.received_supplies'] or state['sled.location'] != 'stall' or state['sled.borrowed']):
        raise StoryError('Returned sled is not at its owner’s stall')
    if state['sled.repaired'] and state['sled.condition'] != 'sound':
        raise StoryError('A repaired sled must be usable')

    if state['story.ended']:
        expected = {'patient': 'patient_delivery', 'race_clean': 'race_delivery', 'race_spill': 'spill_recovery'}
        if (not state['sled.returned'] or not state['sled.checked'] or state['sled.condition'] != 'sound'
                or not state['neighbor.received_supplies'] or state['child.location'] != 'square'
                or state['friend.location'] != 'square' or not state['friend.helped']
                or (state['mittens.borrowed'] and not state['mittens.returned'])
                or state['story.outcome'] != expected.get(result)):
            raise StoryError('The ending leaves a required outcome unfinished')
    elif state['story.outcome'] != '':
        raise StoryError('An unfinished story cannot have an outcome')


def _params_match(params, state):
    expected = {
        'child.route_choice': params.route_choice,
        'square.snow_cm': params.snow_cm,
        'sled.start_condition': params.runner_condition,
        'bundle.weight_kg': params.load_kg,
        'mittens.available': params.has_mittens,
        'friend.race_pressure': params.friend_race_pressure,
    }
    if any(state[key] != value for key, value in expected.items()):
        raise StoryError('Parameters do not match the starting world')


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f'Unknown scene: {scene_id}')
    validate(state)
    if state['story.ended']:
        return False
    if scene_id == 'borrow_sled':
        return (not state['sled.borrowed_once'] and state['child.location'] == 'square'
                and state['sled.owner'] == 'stallkeeper' and state['bundle.location'] == 'stall')
    if scene_id == 'mittens_vignette':
        return (state['sled.borrowed'] and state['bundle.location'] == 'square'
                and state['child.route'] == '' and not state['mittens.secured'])
    if scene_id == 'bell_vignette':
        return (state['sled.borrowed'] and state['bundle.location'] == 'square'
                and state['child.route'] == '' and not state['friend.knows_lane'])
    if scene_id == 'prepare_supplies':
        return state['sled.borrowed'] and state['bundle.location'] == 'square' and not state['bundle.secured']
    if scene_id == 'race_decision':
        return state['bundle.location'] == 'sled' and state['child.route'] == ''
    if scene_id == 'journey':
        return (state['child.route'] in ('patient', 'race') and state['child.journey_result'] == ''
                and state['child.location'] == 'square' and state['bundle.location'] == 'sled')
    if scene_id == 'deliver_supplies':
        return state['child.location'] == 'road' and not state['neighbor.received_supplies']
    if scene_id == 'return_sled':
        return state['neighbor.received_supplies'] and state['child.location'] == 'neighbor' and not state['sled.returned']
    if scene_id == 'ending_patient':
        return (state['sled.returned'] and state['sled.checked'] and state['sled.condition'] == 'sound'
                and state['child.route'] == 'patient' and state['child.journey_result'] == 'patient'
                and state['neighbor.received_soup'] and state['friend.helped'])
    if scene_id == 'ending_race':
        return (state['sled.returned'] and state['sled.checked'] and state['sled.condition'] == 'sound'
                and state['child.route'] == 'race' and state['child.journey_result'] == 'race_clean'
                and state['neighbor.received_soup'] and state['friend.helped'])
    if scene_id == 'ending_spill':
        return (state['sled.returned'] and state['sled.checked'] and state['sled.condition'] == 'sound'
                and state['child.route'] == 'race' and state['child.journey_result'] == 'race_spill'
                and state['neighbor.received_supplies'] and not state['neighbor.received_soup']
                and state['friend.helped'])
    return False


def _act(play, name, requires, changes):
    play.act(name, requires, **changes)


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise TypeError('params must be Parameters')
    validate(state)
    _params_match(params, state)
    if not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    play = LocalPlay(state, actors=('Mina', 'Jo', 'Mr. Vale', 'Dima'), validate=validate)

    if scene_id == 'borrow_sled':
        _act(play, 'lend_sled', {
            'sled.owner': 'stallkeeper', 'sled.location': 'stall', 'child.location': 'square',
        }, {
            'sled.owner': 'child', 'sled.location': 'square', 'sled.borrowed': True,
            'sled.borrowed_once': True,
        })
        _act(play, 'collect_provisions', {'bundle.location': 'stall'}, {'bundle.location': 'square'})
    elif scene_id == 'prepare_supplies':
        _act(play, 'secure_basket', {'bundle.location': 'square', 'sled.owner': 'child'}, {
            'bundle.location': 'sled', 'bundle.secured': True, 'sled.load_kg': params.load_kg,
        })
    elif scene_id == 'mittens_vignette':
        if params.has_mittens:
            _act(play, 'secure_mitten_cuffs', {'mittens.location': 'child', 'mittens.worn': True}, {
                'mittens.secured': True,
            })
        else:
            _act(play, 'borrow_and_wear_mittens', {'mittens.location': 'friend', 'mittens.worn': False}, {
                'mittens.location': 'child', 'mittens.worn': True, 'mittens.borrowed': True,
                'mittens.secured': True,
            })
    elif scene_id == 'bell_vignette':
        _act(play, 'notice_bakers_cleared_lane', {'friend.knows_lane': False}, {
            'friend.knows_lane': True,
        })
    elif scene_id == 'race_decision':
        if params.route_choice == 'patient':
            following = params.friend_race_pressure == 1
            mood = 'good_humored' if following else 'stung'
        else:
            following = True
            mood = 'eager'
        _act(play, 'answer_race_invitation', {'child.route': '', 'bundle.location': 'sled'}, {
            'child.route': params.route_choice, 'friend.following': following, 'friend.mood': mood,
        })
    elif scene_id == 'journey':
        mitten_grip = play.state['mittens.worn']
        if play.state['child.route'] == 'patient':
            lane = play.state['friend.knows_lane']
            following = play.state['friend.following']
            tired = params.snow_cm >= 12 and not lane
            changes = {
                'child.location': 'road', 'child.route_taken': 'bakery_lane' if lane else 'square_road',
                'child.journey_result': 'patient', 'child.hands_cold': not mitten_grip,
                'child.tired': tired, 'sled.location': 'road', 'sled.used_for_delivery': True,
                'mittens.used': mitten_grip,
            }
            if following:
                changes.update({'friend.location': 'road', 'friend.helped': True, 'friend.mood': 'helpful'})
            _act(play, 'set_out_patiently', {
                'child.route': 'patient', 'child.location': 'square', 'bundle.location': 'sled',
            }, changes)
            if not following:
                _act(play, 'jo_catches_up_to_help', {
                    'child.location': 'road', 'friend.location': 'square', 'friend.following': False,
                }, {
                    'friend.location': 'road', 'friend.following': True, 'friend.helped': True,
                    'friend.mood': 'helpful',
                })
        else:
            safe = (play.state['sled.condition'] == 'sound' and params.snow_cm <= 7
                    and params.load_kg <= 2 and mitten_grip)
            if safe:
                _act(play, 'race_over_clear_stretch', {
                    'child.route': 'race', 'child.location': 'square', 'bundle.location': 'sled',
                }, {
                    'child.location': 'road', 'child.route_taken': 'straight_run',
                    'child.journey_result': 'race_clean', 'child.hands_cold': False,
                    'child.tired': False, 'sled.location': 'road', 'sled.used_for_delivery': True,
                    'friend.location': 'road', 'friend.helped': True, 'friend.mood': 'pleased',
                    'mittens.used': mitten_grip,
                })
            else:
                changes = {
                    'child.location': 'road', 'child.route_taken': 'straight_run',
                    'child.journey_result': 'race_spill', 'child.hands_cold': not mitten_grip,
                    'child.tired': True, 'sled.location': 'road', 'sled.used_for_delivery': True,
                    'friend.location': 'road', 'friend.helped': True, 'friend.mood': 'concerned',
                    'bundle.location': 'road', 'bundle.contents': 'bread_oil',
                    'bundle.secured': False, 'mittens.used': mitten_grip,
                }
                if (play.state['sled.condition'] != 'sound' or params.snow_cm > 7 or params.load_kg > 2):
                    changes['sled.condition'] = 'needs_repair'
                _act(play, 'race_spills_soup', {
                    'child.route': 'race', 'child.location': 'square', 'bundle.location': 'sled',
                }, changes)
    elif scene_id == 'deliver_supplies':
        if play.state['child.journey_result'] == 'race_spill':
            _act(play, 'gather_bread_and_oil', {
                'bundle.location': 'road', 'bundle.contents': 'bread_oil',
            }, {'bundle.location': 'child'})
        soup_arrived = play.state['bundle.contents'] == 'all'
        _act(play, 'bring_bundle_to_mr_vale', {
            'child.location': 'road', 'bundle.location': 'sled' if soup_arrived else 'child',
        }, {
            'child.location': 'neighbor', 'friend.location': 'neighbor', 'sled.location': 'neighbor',
            'bundle.location': 'neighbor', 'bundle.owner': 'neighbor', 'bundle.secured': False,
            'neighbor.received_supplies': True, 'neighbor.received_soup': soup_arrived,
            'neighbor.lamp_lit': True,
            'neighbor.feeling': 'grateful' if soup_arrived else 'understanding',
            'friend.mood': 'pleased' if soup_arrived else 'honest',
        })
    elif scene_id == 'return_sled':
        _act(play, 'walk_back_to_square', {
            'child.location': 'neighbor', 'friend.location': 'neighbor', 'sled.location': 'neighbor',
        }, {'child.location': 'square', 'friend.location': 'square', 'sled.location': 'square'})
        _act(play, 'return_sled_to_dima', {'sled.owner': 'child', 'sled.location': 'square'}, {
            'sled.owner': 'stallkeeper', 'sled.location': 'stall', 'sled.borrowed': False,
            'sled.returned': True,
        })
        if play.state['sled.condition'] != 'sound':
            _act(play, 'straighten_runner', {'sled.owner': 'stallkeeper', 'sled.location': 'stall'}, {
                'sled.condition': 'sound', 'sled.repaired': True, 'sled.checked': True,
            })
        else:
            _act(play, 'check_runner_and_rope', {'sled.owner': 'stallkeeper', 'sled.location': 'stall'}, {
                'sled.checked': True,
            })
        if play.state['mittens.borrowed'] and not play.state['mittens.returned']:
            _act(play, 'return_jo_mittens', {'mittens.location': 'child', 'mittens.worn': True}, {
                'mittens.location': 'friend', 'mittens.worn': False, 'mittens.returned': True,
            })
    else:
        outcomes = {
            'ending_patient': ('patient_delivery', 'settled'),
            'ending_race': ('race_delivery', 'buoyant'),
            'ending_spill': ('spill_recovery', 'relieved'),
        }
        outcome, feeling = outcomes[scene_id]
        _act(play, 'finish_errand_and_accept_its_result', {
            'sled.returned': True, 'neighbor.received_supplies': True,
        }, {'story.ended': True, 'story.outcome': outcome, 'child.feeling': feeling})

    after = deepcopy(play.state)
    text = render(scene_id, params, state, after)
    words = len(text.split())
    if not 40 <= words <= 70:
        raise StoryError(f'Scene prose must contain 40 to 70 words, got {words} in {scene_id}')
    return {
        'id': scene_id,
        'before': deepcopy(state),
        'after': after,
        'events': deepcopy(play.events),
        'text': text,
    }


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    p = parameters(seed) if params is None else params
    if not isinstance(p, Parameters):
        raise TypeError('params must be Parameters')
    start = initial(p)
    validate(start)
    rng = random.Random(seed)
    attempts = 0

    def search(state, episodes, used):
        nonlocal attempts
        if len(episodes) == count:
            return episodes if state['story.ended'] else None
        remaining = count - len(episodes)
        choices = [scene_id for scene_id in SCENES if scene_id not in used and guard(scene_id, state)]
        if remaining == 1:
            choices = [scene_id for scene_id in choices if scene_id.startswith('ending_')]
        else:
            choices = [scene_id for scene_id in choices if not scene_id.startswith('ending_')]
        rng.shuffle(choices)
        for scene_id in choices:
            attempts += 1
            if attempts > 5000:
                raise StoryError('Bounded scene search exhausted its budget')
            episode = play_scene(p, state, scene_id)
            found = search(episode['after'], episodes + (episode,), used | {scene_id})
            if found is not None:
                return found
        return None

    found = search(start, (), frozenset())
    if found is None:
        raise StoryError('No complete compatible route at the requested length')
    episodes = list(found)
    story = '\n\n'.join(episode['text'] for episode in episodes)
    return {
        'seed': seed,
        'parameters': asdict(p),
        'scene_count': count,
        'path': [episode['id'] for episode in episodes],
        'story': story,
        'episodes': episodes,
        'final_state': deepcopy(episodes[-1]['after']),
        'search_attempts': attempts,
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise TypeError('params must be Parameters')
    if not isinstance(path, (list, tuple)) or len(path) not in (7, 8):
        raise StoryError('Replay path must contain seven or eight scenes')
    if any(not isinstance(scene_id, str) for scene_id in path) or len(set(path)) != len(path):
        raise StoryError('Replay path has invalid or repeated scene IDs')
    state = initial(params)
    episodes = []
    for scene_id in path:
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode['after']
    if not state['story.ended']:
        raise StoryError('Replay path does not finish the story')
    return episodes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    parser.add_argument('--params', help='JSON object containing parameter overrides')
    args = parser.parse_args()
    try:
        overrides = json.loads(args.params) if args.params is not None else {}
        if not isinstance(overrides, dict):
            raise ValueError('params must be a JSON object')
        values = asdict(parameters(args.seed))
        values.update(overrides)
        chosen = Parameters(**values)
        row = generate(args.seed, count=args.scenes, params=chosen)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(row['story'])


if __name__ == '__main__':
    main()
