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
    dough_grams: int = 140
    dough_chilled: bool = True
    flour_available: bool = True
    cutters_tacky: bool = False
    oven_preheated: bool = False
    share_plan: str = 'equal'

    def __post_init__(self):
        if type(self.dough_grams) is not int or not 70 <= self.dough_grams <= 180:
            raise ValueError('dough_grams must be an integer from 70 to 180')
        for name in ('dough_chilled', 'flour_available', 'cutters_tacky', 'oven_preheated'):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f'{name} must be a boolean')
        if type(self.share_plan) is not str or self.share_plan not in ('equal', 'gift_first'):
            raise ValueError('share_plan must be equal or gift_first')


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        dough_grams=rng.choice((80, 100, 120, 140, 160)),
        dough_chilled=rng.choice((True, False)),
        flour_available=rng.choice((True, False)),
        cutters_tacky=rng.choice((True, False)),
        oven_preheated=rng.choice((True, False)),
        share_plan=rng.choice(('equal', 'gift_first')),
    )


def initial(params):
    if not isinstance(params, Parameters):
        raise ValueError('params must be Parameters')
    params.__post_init__()
    return {
        'story.started': False, 'story.goal': '', 'story.ended': False, 'story.outcome': '',
        'family.location': 'family_kitchen', 'mara.want': 'make a thank-you gift',
        'eli.want': 'share the last dough fairly', 'siblings.trust': 0,
        'dough.grams': params.dough_grams, 'dough.chilled': params.dough_chilled,
        'dough.location': 'covered_bowl', 'dough.prepared': False, 'dough.quality': 'unset',
        'dough.floured': False, 'dough.for_gift': 0, 'dough.for_home': 0,
        'cutters.owner': 'Mrs Flores', 'cutters.carrier': 'Mrs Flores',
        'cutters.location': 'neighbor_shelf', 'cutters.tacky': params.cutters_tacky,
        'cutters.clean': not params.cutters_tacky, 'cutters.ready': False,
        'cutters.borrowed': False, 'cutters.used': False, 'cutters.returned': False,
        'oven.preheated': params.oven_preheated,
        'share.resolved': False, 'share.plan': '',
        'cookies.baked': False, 'cookies.gift_ready': False, 'cookies.home_ready': False,
        'cookies.boxed': False, 'siblings.shared_scraps': False,
        'gift.status': 'none', 'card.status': 'none',
        'kitchen.timer_song': False, 'memory.shared': False,
        'neighbor.dough_ready': True, 'neighbor.cutter_used': False,
    }


SCENES = (
    'start', 'borrow_cutters', 'flour_memory', 'prepare_dough', 'timer_song',
    'divide_dough', 'bake', 'wrap_box', 'ending_gift', 'ending_note',
)
_OPTIONAL = frozenset(('flour_memory', 'timer_song'))
_CORE_FLAGS = (
    'story.started', 'cutters.borrowed', 'dough.prepared', 'share.resolved',
    'cookies.baked', 'gift.wrapped', 'story.ended',
)


def validate(state):
    if not isinstance(state, dict):
        raise StoryError('state must be a dictionary')
    required = set(initial(Parameters()))
    if set(state) != required:
        raise StoryError('state keys do not match the declared world')
    bool_keys = (
        'story.started', 'story.ended', 'dough.chilled', 'dough.prepared', 'dough.floured',
        'cutters.tacky', 'cutters.clean', 'cutters.ready', 'cutters.borrowed',
        'cutters.used', 'cutters.returned', 'oven.preheated', 'share.resolved',
        'cookies.baked', 'cookies.gift_ready', 'cookies.home_ready', 'cookies.boxed',
        'siblings.shared_scraps', 'kitchen.timer_song', 'memory.shared',
        'neighbor.dough_ready', 'neighbor.cutter_used',
    )
    if any(type(state[k]) is not bool for k in bool_keys):
        raise StoryError('boolean state has an invalid type')
    if any(type(state[k]) is not int for k in ('siblings.trust', 'dough.grams', 'dough.for_gift', 'dough.for_home')):
        raise StoryError('numeric state has an invalid type')
    if any(type(state[k]) is not str for k in (
        'story.goal', 'story.outcome', 'family.location', 'mara.want', 'eli.want',
        'dough.location', 'dough.quality', 'cutters.owner', 'cutters.carrier',
        'cutters.location', 'share.plan', 'gift.status', 'card.status',
    )):
        raise StoryError('text state has an invalid type')
    if not 70 <= state['dough.grams'] <= 180 or state['siblings.trust'] < 0:
        raise StoryError('numeric state is outside its range')
    if state['family.location'] not in ('family_kitchen', 'neighbor_step', 'neighbor_kitchen'):
        raise StoryError('unknown family location')
    if state['cutters.owner'] != 'Mrs Flores':
        raise StoryError('the borrowed cutters cannot change owner')
    if state['cutters.carrier'] == 'Mrs Flores':
        expected_location = 'neighbor_counter' if state['cutters.returned'] else 'neighbor_shelf'
    elif state['cutters.carrier'] == 'siblings':
        expected_location = 'family_counter'
    else:
        raise StoryError('unknown cutter carrier')
    if state['cutters.location'] != expected_location:
        raise StoryError('cutter carrier and location disagree')
    if state['cutters.ready'] and not state['cutters.clean']:
        raise StoryError('unclean cutters cannot be ready')
    if state['cutters.borrowed'] != (state['cutters.carrier'] == 'siblings' or state['cutters.returned']):
        raise StoryError('borrowed-tool continuity is broken')
    if state['cutters.used'] and not state['cutters.borrowed']:
        raise StoryError('the cutters must be borrowed before use')
    if state['dough.location'] not in ('covered_bowl', 'family_counter'):
        raise StoryError('unknown dough location')
    if state['story.started'] != (state['dough.location'] == 'family_counter'):
        raise StoryError('the dough was moved without beginning the task')
    if state['story.started'] and not state['story.goal']:
        raise StoryError('a started story needs a goal')
    if not state['story.started'] and state['story.goal']:
        raise StoryError('an unstarted story cannot have a goal')
    if state['dough.prepared'] and not state['cutters.borrowed']:
        raise StoryError('preparation requires the borrowed cutters')
    if state['dough.quality'] not in ('unset', 'neat', 'rough'):
        raise StoryError('unknown dough quality')
    if state['dough.prepared'] != (state['dough.quality'] != 'unset'):
        raise StoryError('dough preparation and quality disagree')
    if state['share.plan'] not in ('', 'equal', 'gift_first'):
        raise StoryError('unknown sharing plan')
    if state['share.resolved']:
        if not state['dough.prepared'] or state['share.plan'] not in ('equal', 'gift_first'):
            raise StoryError('sharing cannot precede preparation')
        if state['dough.for_gift'] < 0 or state['dough.for_home'] < 0:
            raise StoryError('dough portions cannot be negative')
        if state['dough.for_gift'] + state['dough.for_home'] != state['dough.grams']:
            raise StoryError('the last dough must be conserved')
    elif state['dough.for_gift'] or state['dough.for_home'] or state['share.plan']:
        raise StoryError('unresolved dough cannot have assigned portions')
    if state['cookies.baked']:
        if not state['share.resolved'] or not state['oven.preheated'] or not state['cutters.used']:
            raise StoryError('baking requires divided dough, a warm oven, and used cutters')
        expected_gift = state['dough.quality'] == 'neat' and state['dough.for_gift'] >= 60
        expected_home = state['dough.for_home'] >= 20
        if state['cookies.gift_ready'] != expected_gift or state['cookies.home_ready'] != expected_home:
            raise StoryError('baked result disagrees with dough quality or allocation')
    elif state['cookies.gift_ready'] or state['cookies.home_ready'] or state['cookies.boxed']:
        raise StoryError('unbaked dough cannot produce boxed biscuits')
    if state['gift.status'] not in ('none', 'boxed', 'not_made', 'delivered'):
        raise StoryError('unknown gift status')
    if state['card.status'] not in ('none', 'written', 'attached', 'delivered'):
        raise StoryError('unknown card status')
    if state['gift.status'] in ('boxed', 'delivered'):
        if not state['cookies.gift_ready'] or not state['cookies.boxed']:
            raise StoryError('a biscuit gift must be baked and boxed')
    if state['gift.status'] == 'not_made' and state['cookies.gift_ready']:
        raise StoryError('a viable gift cannot be marked as unmade')
    if state['cookies.boxed'] and state['gift.status'] not in ('boxed', 'delivered'):
        raise StoryError('boxed cookies need a gift status')
    if state['gift.wrapped'] if 'gift.wrapped' in state else False:
        raise StoryError('undeclared state')
    if state['cutters.returned']:
        if not state['cutters.clean'] or not state['cutters.ready'] or not state['cutters.used']:
            raise StoryError('returned cutters must be clean, ready, and useful')
    if state['neighbor.cutter_used'] and not state['cutters.returned']:
        raise StoryError('Mrs Flores cannot use cutters she has not received')
    if state['story.ended']:
        if (state['family.location'] != 'neighbor_kitchen' or not state['cutters.returned']
                or not state['neighbor.cutter_used'] or state['card.status'] != 'delivered'
                or state['gift.status'] not in ('delivered', 'not_made')
                or not state['siblings.shared_scraps'] or not state['story.outcome']):
            raise StoryError('ending leaves the delivery, return, or reconciliation unfinished')
    elif state['story.outcome']:
        raise StoryError('an unfinished story cannot have an outcome')
    if state['gift.wrapped'] if 'gift.wrapped' in state else False:
        raise StoryError('unreachable')
    return True


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f'unknown scene: {scene_id}')
    validate(state)
    if state['story.ended']:
        return False
    if scene_id == 'start':
        return not state['story.started']
    if scene_id == 'borrow_cutters':
        return state['story.started'] and not state['cutters.borrowed']
    if scene_id == 'flour_memory':
        return state['cutters.borrowed'] and not state['dough.prepared'] and not state['memory.shared']
    if scene_id == 'prepare_dough':
        return state['cutters.borrowed'] and not state['dough.prepared']
    if scene_id == 'timer_song':
        return state['dough.prepared'] and not state['share.resolved'] and not state['kitchen.timer_song']
    if scene_id == 'divide_dough':
        return state['dough.prepared'] and not state['share.resolved']
    if scene_id == 'bake':
        return state['share.resolved'] and not state['cookies.baked']
    if scene_id == 'wrap_box':
        return state['cookies.baked'] and not state.get('gift.wrapped', False)
    if scene_id == 'ending_gift':
        return state.get('gift.wrapped', False) and state['gift.status'] == 'boxed'
    if scene_id == 'ending_note':
        return state.get('gift.wrapped', False) and state['gift.status'] == 'not_made'
    return False


# gift.wrapped is an ordinary state key declared below by _initial_with_wrapping.
def _initial_with_wrapping(params):
    state = initial(params)
    state['gift.wrapped'] = False
    return state


# Replace initial's dictionary source with the same declared key set for all callers.
_initial_base = initial

def initial(params):
    state = _initial_base(params)
    state['gift.wrapped'] = False
    return state


def validate(state):
    if not isinstance(state, dict):
        raise StoryError('state must be a dictionary')
    required = set(initial(Parameters()))
    if set(state) != required:
        raise StoryError('state keys do not match the declared world')
    bool_keys = (
        'story.started', 'story.ended', 'dough.chilled', 'dough.prepared', 'dough.floured',
        'cutters.tacky', 'cutters.clean', 'cutters.ready', 'cutters.borrowed',
        'cutters.used', 'cutters.returned', 'oven.preheated', 'share.resolved',
        'cookies.baked', 'cookies.gift_ready', 'cookies.home_ready', 'cookies.boxed',
        'siblings.shared_scraps', 'kitchen.timer_song', 'memory.shared',
        'neighbor.dough_ready', 'neighbor.cutter_used', 'gift.wrapped',
    )
    if any(type(state[k]) is not bool for k in bool_keys):
        raise StoryError('boolean state has an invalid type')
    if any(type(state[k]) is not int for k in ('siblings.trust', 'dough.grams', 'dough.for_gift', 'dough.for_home')):
        raise StoryError('numeric state has an invalid type')
    if any(type(state[k]) is not str for k in (
        'story.goal', 'story.outcome', 'family.location', 'mara.want', 'eli.want',
        'dough.location', 'dough.quality', 'cutters.owner', 'cutters.carrier',
        'cutters.location', 'share.plan', 'gift.status', 'card.status',
    )):
        raise StoryError('text state has an invalid type')
    if not 70 <= state['dough.grams'] <= 180 or state['siblings.trust'] < 0:
        raise StoryError('numeric state is outside its range')
    if state['family.location'] not in ('family_kitchen', 'neighbor_step', 'neighbor_kitchen'):
        raise StoryError('unknown family location')
    if state['cutters.owner'] != 'Mrs Flores':
        raise StoryError('the borrowed cutters cannot change owner')
    if state['cutters.carrier'] == 'Mrs Flores':
        expected_location = 'neighbor_counter' if state['cutters.returned'] else 'neighbor_shelf'
    elif state['cutters.carrier'] == 'siblings':
        expected_location = 'family_counter'
    else:
        raise StoryError('unknown cutter carrier')
    if state['cutters.location'] != expected_location:
        raise StoryError('cutter carrier and location disagree')
    if state['cutters.ready'] and not state['cutters.clean']:
        raise StoryError('unclean cutters cannot be ready')
    if state['cutters.borrowed'] != (state['cutters.carrier'] == 'siblings' or state['cutters.returned']):
        raise StoryError('borrowed-tool continuity is broken')
    if state['cutters.used'] and not state['cutters.borrowed']:
        raise StoryError('the cutters must be borrowed before use')
    if state['dough.location'] not in ('covered_bowl', 'family_counter'):
        raise StoryError('unknown dough location')
    if state['story.started'] != (state['dough.location'] == 'family_counter'):
        raise StoryError('the dough was moved without beginning the task')
    if state['story.started'] != bool(state['story.goal']):
        raise StoryError('story goal and start state disagree')
    if state['dough.prepared'] and not state['cutters.borrowed']:
        raise StoryError('preparation requires the borrowed cutters')
    if state['dough.quality'] not in ('unset', 'neat', 'rough'):
        raise StoryError('unknown dough quality')
    if state['dough.prepared'] != (state['dough.quality'] != 'unset'):
        raise StoryError('dough preparation and quality disagree')
    if state['share.plan'] not in ('', 'equal', 'gift_first'):
        raise StoryError('unknown sharing plan')
    if state['share.resolved']:
        if not state['dough.prepared'] or state['share.plan'] not in ('equal', 'gift_first'):
            raise StoryError('sharing cannot precede preparation')
        if state['dough.for_gift'] < 0 or state['dough.for_home'] < 0:
            raise StoryError('dough portions cannot be negative')
        if state['dough.for_gift'] + state['dough.for_home'] != state['dough.grams']:
            raise StoryError('the last dough must be conserved')
    elif state['dough.for_gift'] or state['dough.for_home'] or state['share.plan']:
        raise StoryError('unresolved dough cannot have assigned portions')
    if state['cookies.baked']:
        if not state['share.resolved'] or not state['oven.preheated'] or not state['cutters.used']:
            raise StoryError('baking requires divided dough, a warm oven, and used cutters')
        expected_gift = state['dough.quality'] == 'neat' and state['dough.for_gift'] >= 60
        expected_home = state['dough.for_home'] >= 20
        if state['cookies.gift_ready'] != expected_gift or state['cookies.home_ready'] != expected_home:
            raise StoryError('baked result disagrees with dough quality or allocation')
    elif state['cookies.gift_ready'] or state['cookies.home_ready'] or state['cookies.boxed']:
        raise StoryError('unbaked dough cannot produce boxed biscuits')
    if state['gift.status'] not in ('none', 'boxed', 'not_made', 'delivered'):
        raise StoryError('unknown gift status')
    if state['card.status'] not in ('none', 'written', 'attached', 'delivered'):
        raise StoryError('unknown card status')
    if state['gift.status'] in ('boxed', 'delivered') and not (state['cookies.gift_ready'] and state['cookies.boxed']):
        raise StoryError('a biscuit gift must be baked and boxed')
    if state['gift.status'] == 'not_made' and state['cookies.gift_ready']:
        raise StoryError('a viable gift cannot be marked as unmade')
    if state['cookies.boxed'] and state['gift.status'] not in ('boxed', 'delivered'):
        raise StoryError('boxed cookies need a gift status')
    if state['gift.wrapped']:
        if not state['cookies.baked'] or state['card.status'] not in ('written', 'attached'):
            raise StoryError('wrapping requires a finished bake and a note')
        if not state['cutters.clean'] or not state['cutters.ready']:
            raise StoryError('the borrowed cutters must be cleaned before the visit')
        if state['gift.status'] not in ('boxed', 'not_made'):
            raise StoryError('the selected gift outcome is not ready')
    if state['cutters.returned']:
        if not state['cutters.clean'] or not state['cutters.ready'] or not state['cutters.used']:
            raise StoryError('returned cutters must be clean, ready, and useful')
    if state['neighbor.cutter_used'] and not state['cutters.returned']:
        raise StoryError('Mrs Flores cannot use cutters she has not received')
    if state['story.ended']:
        if (state['family.location'] != 'neighbor_kitchen' or not state['cutters.returned']
                or not state['neighbor.cutter_used'] or state['card.status'] != 'delivered'
                or state['gift.status'] not in ('delivered', 'not_made')
                or not state['siblings.shared_scraps'] or not state['story.outcome']):
            raise StoryError('ending leaves the delivery, return, or reconciliation unfinished')
    elif state['story.outcome']:
        raise StoryError('an unfinished story cannot have an outcome')
    return True


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f'unknown scene: {scene_id}')
    validate(state)
    if state['story.ended']:
        return False
    if scene_id == 'start':
        return not state['story.started']
    if scene_id == 'borrow_cutters':
        return state['story.started'] and not state['cutters.borrowed']
    if scene_id == 'flour_memory':
        return state['cutters.borrowed'] and not state['dough.prepared'] and not state['memory.shared']
    if scene_id == 'prepare_dough':
        return state['cutters.borrowed'] and not state['dough.prepared']
    if scene_id == 'timer_song':
        return state['dough.prepared'] and not state['share.resolved'] and not state['kitchen.timer_song']
    if scene_id == 'divide_dough':
        return state['dough.prepared'] and not state['share.resolved']
    if scene_id == 'bake':
        return state['share.resolved'] and not state['cookies.baked']
    if scene_id == 'wrap_box':
        return state['cookies.baked'] and not state['gift.wrapped']
    if scene_id == 'ending_gift':
        return state['gift.wrapped'] and state['gift.status'] == 'boxed'
    if scene_id == 'ending_note':
        return state['gift.wrapped'] and state['gift.status'] == 'not_made'
    return False


def _act(play, name, requires, changes):
    play.act(name, requires=requires, **changes)


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise ValueError('params must be Parameters')
    params.__post_init__()
    if scene_id not in SCENES or not guard(scene_id, state):
        raise StoryError(f'scene not compatible with current state: {scene_id}')
    play = LocalPlay(state, actors=('mara', 'eli'), validate=validate)
    if scene_id == 'start':
        _act(play, 'claim_the_last_dough_for_thanks',
             {'story.started': False, 'family.location': 'family_kitchen'},
             {'story.started': True, 'story.goal': 'thank Mrs Flores with a cutter-made gift',
              'dough.location': 'family_counter'})
    elif scene_id == 'borrow_cutters':
        _act(play, 'go_next_door_to_ask', {'family.location': 'family_kitchen'},
             {'family.location': 'neighbor_step'})
        _act(play, 'borrow_with_permission', {'family.location': 'neighbor_step', 'cutters.borrowed': False},
             {'family.location': 'family_kitchen', 'cutters.carrier': 'siblings',
              'cutters.location': 'family_counter', 'cutters.borrowed': True})
        if play.state['cutters.tacky']:
            _act(play, 'wash_tacky_cutters', {'cutters.tacky': True},
                 {'cutters.tacky': False, 'cutters.clean': True, 'cutters.ready': True})
        else:
            _act(play, 'dry_and_check_cutters', {'cutters.tacky': False, 'cutters.clean': True},
                 {'cutters.ready': True})
    elif scene_id == 'flour_memory':
        _act(play, 'remember_grandmothers_fair_tray',
             {'cutters.borrowed': True, 'dough.prepared': False, 'memory.shared': False},
             {'memory.shared': True, 'siblings.trust': play.state['siblings.trust'] + 1})
    elif scene_id == 'prepare_dough':
        if params.flour_available:
            _act(play, 'dust_the_counter', {'dough.prepared': False, 'dough.floured': False},
                 {'dough.floured': True})
        if not play.state['oven.preheated']:
            _act(play, 'preheat_the_oven', {'oven.preheated': False}, {'oven.preheated': True})
        quality = 'neat' if play.state['dough.chilled'] or play.state['dough.floured'] else 'rough'
        _act(play, 'check_the_last_dough', {'cutters.borrowed': True, 'dough.prepared': False},
             {'dough.prepared': True, 'dough.quality': quality})
    elif scene_id == 'timer_song':
        _act(play, 'tap_a_kitchen_timer_song',
             {'dough.prepared': True, 'share.resolved': False, 'kitchen.timer_song': False},
             {'kitchen.timer_song': True, 'siblings.trust': play.state['siblings.trust'] + 1})
    elif scene_id == 'divide_dough':
        grams = play.state['dough.grams']
        if params.share_plan == 'equal':
            gift = grams // 2
            home = grams - gift
        else:
            gift = (grams * 2) // 3
            home = grams - gift
        _act(play, 'agree_on_how_to_share_the_last_dough',
             {'dough.prepared': True, 'share.resolved': False},
             {'share.resolved': True, 'share.plan': params.share_plan,
              'dough.for_gift': gift, 'dough.for_home': home})
    elif scene_id == 'bake':
        gift_ready = play.state['dough.quality'] == 'neat' and play.state['dough.for_gift'] >= 60
        home_ready = play.state['dough.for_home'] >= 20
        _act(play, 'press_borrowed_cutters_and_bake',
             {'share.resolved': True, 'oven.preheated': True, 'cutters.ready': True,
              'cookies.baked': False},
             {'cookies.baked': True, 'cookies.gift_ready': gift_ready,
              'cookies.home_ready': home_ready, 'cutters.used': True,
              'cutters.clean': False, 'cutters.ready': False})
    elif scene_id == 'wrap_box':
        _act(play, 'write_the_thank_you_card', {'cookies.baked': True, 'card.status': 'none'},
             {'card.status': 'written'})
        if play.state['cookies.gift_ready']:
            _act(play, 'line_a_tin_for_the_biscuits', {'cookies.gift_ready': True, 'gift.status': 'none'},
                 {'gift.status': 'boxed', 'cookies.boxed': True, 'card.status': 'attached'})
        else:
            _act(play, 'keep_the_note_for_an_honest_visit',
                 {'cookies.gift_ready': False, 'gift.status': 'none'}, {'gift.status': 'not_made'})
        _act(play, 'wash_and_dry_the_borrowed_cutters',
             {'cutters.used': True, 'cutters.clean': False},
             {'cutters.clean': True, 'cutters.ready': True})
        _act(play, 'finish_the_gift_or_note', {'cutters.ready': True}, {'gift.wrapped': True})
    else:
        if play.state['cookies.home_ready']:
            _act(play, 'split_the_home_biscuit', {'cookies.home_ready': True, 'siblings.shared_scraps': False},
                 {'siblings.shared_scraps': True})
        _act(play, 'walk_to_mrs_flores', {'family.location': 'family_kitchen'},
             {'family.location': 'neighbor_step'})
        _act(play, 'step_into_the_neighbor_kitchen', {'family.location': 'neighbor_step'},
             {'family.location': 'neighbor_kitchen'})
        if scene_id == 'ending_gift':
            _act(play, 'deliver_the_box_and_card',
                 {'gift.status': 'boxed', 'card.status': 'attached'},
                 {'gift.status': 'delivered', 'card.status': 'delivered'})
            outcome = 'biscuit_gift_delivered_' + play.state['share.plan']
        else:
            _act(play, 'deliver_the_honest_note',
                 {'gift.status': 'not_made', 'card.status': 'written'},
                 {'card.status': 'delivered'})
            outcome = 'honest_note_delivered_after_the_bake_missed'
        _act(play, 'return_the_clean_useful_cutters',
             {'cutters.carrier': 'siblings', 'cutters.clean': True, 'cutters.used': True},
             {'cutters.carrier': 'Mrs Flores', 'cutters.location': 'neighbor_counter',
              'cutters.returned': True})
        _act(play, 'mrs_flores_cuts_her_own_dough',
             {'cutters.returned': True, 'neighbor.dough_ready': True, 'neighbor.cutter_used': False},
             {'neighbor.cutter_used': True})
        _act(play, 'complete_the_visit', {'neighbor.cutter_used': True, 'card.status': 'delivered'},
             {'story.ended': True, 'story.outcome': outcome})
    after = deepcopy(play.state)
    validate(after)
    return Episode(scene_id, deepcopy(state), after, tuple(deepcopy(play.events)),
                   render(scene_id, params, state, after))


@dataclass(frozen=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


def _core_remaining(state):
    return sum(not state[key] for key in _CORE_FLAGS)


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    p = params if params is not None else parameters(seed)
    if not isinstance(p, Parameters):
        raise ValueError('params must be Parameters')
    p.__post_init__()
    rng = random.Random(seed)
    attempts = 0

    def search(state, episodes):
        nonlocal attempts
        remaining = count - len(episodes)
        needed = _core_remaining(state)
        if remaining < needed:
            return None
        if state['story.ended']:
            return episodes if remaining == 0 else None
        if remaining == 0:
            return None
        used = {episode.id for episode in episodes}
        choices = [scene_id for scene_id in SCENES
                   if scene_id not in used and guard(scene_id, state)
                   and (not scene_id.startswith('ending_') or remaining == 1)
                   and (scene_id not in _OPTIONAL or remaining > needed)]
        rng.shuffle(choices)
        for scene_id in choices:
            attempts += 1
            if attempts > 2000:
                raise StoryError('bounded scene search exhausted its 2000 candidate budget')
            episode = play_scene(p, state, scene_id)
            answer = search(episode.after, episodes + (episode,))
            if answer is not None:
                return answer
        return None

    episodes = search(initial(p), ())
    if episodes is None:
        raise StoryError('no compatible route reaches an ending at this length')
    episode_rows = [asdict(episode) | {'events': list(episode.events)} for episode in episodes]
    return {
        'seed': seed, 'parameters': asdict(p), 'scene_count': count,
        'path': [episode.id for episode in episodes],
        'story': (chr(10) * 2).join(episode.text for episode in episodes),
        'episodes': episode_rows, 'final_state': deepcopy(episodes[-1].after),
        'search_attempts': attempts,
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise ValueError('params must be Parameters')
    params.__post_init__()
    state = initial(params)
    episodes = []
    used = set()
    for scene_id in path:
        if scene_id in used:
            raise StoryError('a scene cannot be repeated')
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode.after
        used.add(scene_id)
    return tuple(episodes)


def main():
    parser = argparse.ArgumentParser(description='Generate a local kitchen mini-adventure.')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    parser.add_argument('--params', help='JSON object of validated parameter overrides')
    args = parser.parse_args()
    p = parameters(args.seed)
    if args.params:
        overrides = json.loads(args.params)
        if not isinstance(overrides, dict):
            parser.error('--params must be a JSON object')
        p = Parameters(**(asdict(p) | overrides))
    row = generate(args.seed, count=args.scenes, params=p)
    print(row['story'])


if __name__ == '__main__':
    main()
