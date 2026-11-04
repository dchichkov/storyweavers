'''A bounded, replayable fruit-market adventure built from local plays.'''
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
    scale_bias_units: int = 2
    order_units: int = 14
    apples_stock_units: int = 20
    scale_wobbles: bool = False
    neighbor_will_mix: bool = True

    def __post_init__(self):
        for key, low, high in (
            ('scale_bias_units', 1, 3),
            ('order_units', 10, 20),
            ('apples_stock_units', 8, 24),
        ):
            value = getattr(self, key)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f'{key} must be an integer in [{low}, {high}]')
        for key in ('scale_wobbles', 'neighbor_will_mix'):
            if type(getattr(self, key)) is not bool:
                raise ValueError(f'{key} must be boolean')


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        scale_bias_units=rng.choice((1, 2, 3)),
        order_units=rng.choice((10, 12, 14, 16, 18, 20)),
        apples_stock_units=rng.choice((8, 10, 12, 14, 18, 22, 24)),
        scale_wobbles=rng.choice((False, True)),
        neighbor_will_mix=rng.choice((False, True)),
    )


SCENES = (
    'market_order', 'vignette_bruised_apple', 'vignette_pear_sample',
    'fill_order', 'inspect_scale', 'tell_neighbor', 'conceal_error',
    'settle_order', 'return_scale', 'ending',
)

_STATE_KEYS = (
    'scenario.scale_bias_units', 'scenario.order_units',
    'scenario.apples_stock_units', 'scenario.scale_wobbles',
    'scenario.neighbor_will_mix', 'market.phase', 'market.location',
    'helper.location', 'helper.decision', 'helper.knows_error',
    'helper.apologized', 'neighbor.location', 'neighbor.initial_will_mix',
    'neighbor.will_mix', 'neighbor.tasted_pear', 'neighbor.sample_units',
    'neighbor.informed', 'neighbor.detected', 'neighbor.trust',
    'scale.owner', 'scale.location', 'scale.bias_original',
    'scale.bias_units', 'scale.bias_known', 'scale.wobbles',
    'scale.settled', 'scale.reference_units',
    'scale.reference_reading_units', 'scale.reading_units',
    'scale.error_found', 'scale.verified', 'scale.returned',
    'order.units', 'order.status', 'order.apples', 'order.pears',
    'order.payment', 'basket.location', 'apples.total', 'apples.available',
    'child.apple_units', 'child.received_apple', 'pears.total',
    'pears.available', 'story.ended', 'story.outcome',
)


def initial(params):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    state = {
        'scenario.scale_bias_units': params.scale_bias_units,
        'scenario.order_units': params.order_units,
        'scenario.apples_stock_units': params.apples_stock_units,
        'scenario.scale_wobbles': params.scale_wobbles,
        'scenario.neighbor_will_mix': params.neighbor_will_mix,
        'market.phase': 'start',
        'market.location': 'fruit_market',
        'helper.location': 'fruit_market',
        'helper.decision': '',
        'helper.knows_error': False,
        'helper.apologized': False,
        'neighbor.location': 'market',
        'neighbor.initial_will_mix': params.neighbor_will_mix,
        'neighbor.will_mix': params.neighbor_will_mix,
        'neighbor.tasted_pear': False,
        'neighbor.sample_units': 0,
        'neighbor.informed': False,
        'neighbor.detected': False,
        'neighbor.trust': 0,
        'scale.owner': 'keeper',
        'scale.location': 'keeper',
        'scale.bias_original': params.scale_bias_units,
        'scale.bias_units': params.scale_bias_units,
        'scale.bias_known': None,
        'scale.wobbles': params.scale_wobbles,
        'scale.settled': not params.scale_wobbles,
        'scale.reference_units': 5,
        'scale.reference_reading_units': None,
        'scale.reading_units': None,
        'scale.error_found': False,
        'scale.verified': False,
        'scale.returned': False,
        'order.units': params.order_units,
        'order.status': 'not_started',
        'order.apples': 0,
        'order.pears': 0,
        'order.payment': 'none',
        'basket.location': 'none',
        'apples.total': params.apples_stock_units,
        'apples.available': params.apples_stock_units,
        'child.apple_units': 0,
        'child.received_apple': False,
        'pears.total': 24,
        'pears.available': 24,
        'story.ended': False,
        'story.outcome': '',
    }
    validate(state)
    return state


def _expected_outcome(state):
    prefix = 'honest' if state['helper.decision'] == 'honest' else 'repaired_after_concealment'
    return f"{prefix}_{state['order.status']}"


def validate(state):
    if not isinstance(state, dict) or set(state) != set(_STATE_KEYS):
        raise StoryError('State keys do not match this scenario')
    int_keys = (
        'scenario.scale_bias_units', 'scenario.order_units',
        'scenario.apples_stock_units', 'neighbor.sample_units',
        'neighbor.trust', 'scale.bias_original', 'scale.bias_units',
        'scale.reference_units', 'order.units', 'order.apples', 'order.pears',
        'apples.total', 'apples.available', 'child.apple_units',
        'pears.total', 'pears.available',
    )
    for key in int_keys:
        if type(state[key]) is not int:
            raise StoryError(f'{key} must be an integer')
    bool_keys = (
        'scenario.scale_wobbles', 'scenario.neighbor_will_mix',
        'helper.knows_error', 'helper.apologized', 'neighbor.initial_will_mix',
        'neighbor.will_mix', 'neighbor.tasted_pear', 'neighbor.informed',
        'neighbor.detected', 'scale.wobbles', 'scale.settled',
        'scale.error_found', 'scale.verified', 'scale.returned',
        'child.received_apple', 'story.ended',
    )
    for key in bool_keys:
        if type(state[key]) is not bool:
            raise StoryError(f'{key} must be boolean')
    for key in ('scale.bias_known', 'scale.reference_reading_units', 'scale.reading_units'):
        if state[key] is not None and type(state[key]) is not int:
            raise StoryError(f'{key} must be an integer or None')
    if not 1 <= state['scenario.scale_bias_units'] <= 3:
        raise StoryError('Invalid original scale error')
    if not 10 <= state['scenario.order_units'] <= 20:
        raise StoryError('Invalid order size')
    if not 8 <= state['scenario.apples_stock_units'] <= 24:
        raise StoryError('Invalid apple stock')
    if state['scale.bias_original'] != state['scenario.scale_bias_units']:
        raise StoryError('Original scale bias changed')
    if state['scale.wobbles'] != state['scenario.scale_wobbles']:
        raise StoryError('Scale condition changed')
    if state['order.units'] != state['scenario.order_units']:
        raise StoryError('The order size changed without consent')
    if state['apples.total'] != state['scenario.apples_stock_units']:
        raise StoryError('Initial apple stock changed')
    if state['neighbor.initial_will_mix'] != state['scenario.neighbor_will_mix']:
        raise StoryError('Initial customer preference changed')
    if state['scale.owner'] not in ('keeper', 'helper'):
        raise StoryError('Unknown scale owner')
    if state['scale.location'] != state['scale.owner']:
        raise StoryError('Scale custody and location disagree')
    if state['scale.bias_units'] not in range(4):
        raise StoryError('Invalid current scale bias')
    if state['scale.reference_units'] != 5:
        raise StoryError('The reference weight must be 500 grams')
    if state['market.location'] != 'fruit_market' or state['helper.location'] != 'fruit_market':
        raise StoryError('The action left the market without a move')
    if state['market.phase'] not in ('start', 'order', 'filled', 'checked', 'decided', 'settled', 'returned', 'ended'):
        raise StoryError('Unknown story phase')
    if state['helper.decision'] not in ('', 'honest', 'concealed'):
        raise StoryError('Unknown decision')
    if state['neighbor.location'] not in ('market', 'home'):
        raise StoryError('Unknown neighbor location')
    if state['neighbor.trust'] not in (-1, 0, 1):
        raise StoryError('Invalid trust change')
    if state['order.status'] not in ('not_started', 'pending', 'full', 'mixed', 'refunded'):
        raise StoryError('Unknown order status')
    if state['order.payment'] not in ('none', 'paid', 'returned'):
        raise StoryError('Unknown payment state')
    if state['basket.location'] not in ('none', 'helper', 'neighbor', 'market'):
        raise StoryError('Unknown basket location')
    if state['apples.available'] < 0 or state['pears.available'] < 0:
        raise StoryError('Fruit stock cannot be negative')
    if state['order.apples'] < 0 or state['order.pears'] < 0:
        raise StoryError('Basket quantities cannot be negative')
    if state['apples.available'] + state['child.apple_units'] + state['order.apples'] != state['apples.total']:
        raise StoryError('Apples were created or lost')
    if state['pears.available'] + state['neighbor.sample_units'] + state['order.pears'] != state['pears.total']:
        raise StoryError('Pears were created or lost')
    if state['child.apple_units'] not in (0, 1) or state['child.received_apple'] != (state['child.apple_units'] == 1):
        raise StoryError('The child apple vignette is inconsistent')
    if state['neighbor.sample_units'] not in (0, 1) or state['neighbor.tasted_pear'] != (state['neighbor.sample_units'] == 1):
        raise StoryError('The pear sample is inconsistent')
    if state['neighbor.tasted_pear'] and not state['neighbor.will_mix']:
        raise StoryError('A tasted pear can change the neighbor’s preference')
    if state['scale.error_found'] != state['helper.knows_error']:
        raise StoryError('The helper’s knowledge and scale test disagree')
    if state['scale.error_found']:
        if state['scale.bias_known'] != state['scale.bias_original']:
            raise StoryError('The discovered bias is inaccurate')
        if state['scale.reference_reading_units'] is None:
            raise StoryError('The reference weight was not read')
    elif state['scale.bias_known'] is not None:
        raise StoryError('Scale error was recorded before inspection')
    if state['scale.verified'] and (state['scale.bias_units'] != 0 or state['scale.reference_reading_units'] != 5):
        raise StoryError('A repaired scale must read zero correctly')
    if state['scale.returned'] and (state['scale.owner'] != 'keeper' or not state['scale.verified']):
        raise StoryError('The borrowed scale was not returned useful')
    if state['market.phase'] == 'start':
        if state['order.status'] != 'not_started' or state['scale.owner'] != 'keeper':
            raise StoryError('The initial market state is inconsistent')
    elif state['order.status'] == 'not_started':
        raise StoryError('An opened market order must be tracked')
    if state['order.status'] == 'pending':
        if state['market.phase'] not in ('order', 'filled', 'checked', 'decided'):
            raise StoryError('Pending order has an incompatible phase')
        if state['order.apples'] > state['order.units'] or state['order.pears'] != 0:
            raise StoryError('Pending basket quantity is invalid')
        if state['market.phase'] == 'order':
            if state['basket.location'] != 'none' or state['order.apples'] != 0:
                raise StoryError('Basket exists before filling')
        elif state['basket.location'] not in ('helper', 'neighbor'):
            raise StoryError('Pending basket has no physical location')
    else:
        if state['order.status'] in ('full', 'mixed'):
            if state['order.apples'] + state['order.pears'] != state['order.units']:
                raise StoryError('Delivered order is not the requested weight')
            if state['basket.location'] != 'neighbor' or state['order.payment'] != 'paid':
                raise StoryError('Delivered order and payment disagree')
        elif state['order.status'] == 'refunded':
            if state['order.apples'] != 0 or state['order.pears'] != 0:
                raise StoryError('Refunded basket still contains fruit')
            if state['basket.location'] != 'market' or state['order.payment'] != 'returned':
                raise StoryError('Refunded order was not returned')
        if state['market.phase'] in ('settled', 'returned', 'ended') and state['order.status'] not in ('full', 'mixed', 'refunded'):
            raise StoryError('Settled phase has no outcome')
    if state['helper.decision'] == 'honest':
        if not state['neighbor.informed'] or state['neighbor.trust'] != 1 or not state['helper.apologized']:
            raise StoryError('Honest disclosure was not enacted')
    if state['helper.decision'] == 'concealed' and state['market.phase'] in ('settled', 'returned', 'ended'):
        if not state['neighbor.detected'] or not state['neighbor.informed'] or state['neighbor.trust'] != -1 or not state['helper.apologized']:
            raise StoryError('Concealment has no enacted consequence')
    if state['story.ended'] != (state['market.phase'] == 'ended'):
        raise StoryError('Ending flag and phase disagree')
    if state['story.ended']:
        if state['scale.owner'] != 'keeper' or not state['scale.returned'] or not state['scale.verified']:
            raise StoryError('Ending leaves the borrowed scale unusable or unreturned')
        if state['story.outcome'] != _expected_outcome(state):
            raise StoryError('Ending label does not match the enacted result')
    elif state['story.outcome'] != '':
        raise StoryError('An unfinished story cannot have an outcome')


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f'Unknown scene: {scene_id}')
    if state.get('story.ended') is True:
        return False
    phase = state.get('market.phase')
    if scene_id == 'market_order':
        return phase == 'start'
    if scene_id in ('vignette_bruised_apple', 'vignette_pear_sample'):
        if phase != 'order':
            return False
        if scene_id == 'vignette_bruised_apple':
            return not state.get('child.received_apple', True) and state.get('apples.available', 0) > 0
        return not state.get('neighbor.tasted_pear', True) and state.get('pears.available', 0) > 0
    if scene_id == 'fill_order':
        return phase == 'order' and state.get('scale.owner') == 'helper'
    if scene_id == 'inspect_scale':
        return phase == 'filled' and state.get('scale.owner') == 'helper'
    if scene_id in ('tell_neighbor', 'conceal_error'):
        return phase == 'checked' and state.get('helper.decision') == ''
    if scene_id == 'settle_order':
        return phase == 'decided'
    if scene_id == 'return_scale':
        return phase == 'settled' and state.get('scale.owner') == 'helper'
    if scene_id == 'ending':
        return phase == 'returned'
    return False


@dataclass(frozen=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


def _matches_parameters(params, state):
    expected = {
        'scenario.scale_bias_units': params.scale_bias_units,
        'scenario.order_units': params.order_units,
        'scenario.apples_stock_units': params.apples_stock_units,
        'scenario.scale_wobbles': params.scale_wobbles,
        'scenario.neighbor_will_mix': params.neighbor_will_mix,
    }
    return all(state.get(key) == value for key, value in expected.items())


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    validate(state)
    if not _matches_parameters(params, state):
        raise StoryError('Parameters do not match this world state')
    if not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    x = LocalPlay(state, actors=('Nella', 'Mrs. Vale', 'Mr. Rafi'), validate=validate)

    if scene_id == 'market_order':
        x.act('write_order_and_take_payment', {'market.phase': 'start'}, **{
            'market.phase': 'order', 'order.status': 'pending', 'order.payment': 'paid',
        })
        x.act('borrow_scale', {'scale.owner': 'keeper', 'market.phase': 'order'}, **{
            'scale.owner': 'helper', 'scale.location': 'helper',
        })
    elif scene_id == 'vignette_bruised_apple':
        available = x.state['apples.available']
        x.act('give_bruised_apple_to_child', {
            'market.phase': 'order', 'child.received_apple': False,
            'apples.available': available,
        }, **{
            'apples.available': available - 1, 'child.apple_units': 1,
            'child.received_apple': True,
        })
    elif scene_id == 'vignette_pear_sample':
        available = x.state['pears.available']
        x.act('offer_neighbor_pear_sample', {
            'market.phase': 'order', 'neighbor.tasted_pear': False,
            'pears.available': available,
        }, **{
            'pears.available': available - 1, 'neighbor.sample_units': 1,
            'neighbor.tasted_pear': True, 'neighbor.will_mix': True,
        })
    elif scene_id == 'fill_order':
        if x.state['scale.wobbles'] and not x.state['scale.settled']:
            x.act('steady_wobbling_dial', {'scale.settled': False}, **{'scale.settled': True})
        before = x.state
        quantity = min(before['order.units'] - before['scale.bias_units'], before['apples.available'])
        if quantity <= 0:
            raise StoryError('There are no apples to weigh')
        reading = quantity + before['scale.bias_units']
        x.act('weigh_apples_to_order_mark', {
            'market.phase': 'order', 'scale.owner': 'helper', 'scale.settled': True,
        }, **{
            'market.phase': 'filled', 'order.apples': quantity,
            'basket.location': 'helper', 'apples.available': before['apples.available'] - quantity,
            'scale.reading_units': reading,
            'scale.settled': not before['scale.wobbles'],
        })
    elif scene_id == 'inspect_scale':
        if x.state['scale.wobbles'] and not x.state['scale.settled']:
            x.act('steady_scale_for_reference_weight', {'scale.settled': False}, **{'scale.settled': True})
        bias = x.state['scale.bias_units']
        reading = x.state['scale.reference_units'] + bias
        x.act('test_known_half_kilo_weight', {
            'market.phase': 'filled', 'scale.owner': 'helper', 'scale.settled': True,
        }, **{
            'market.phase': 'checked', 'scale.bias_known': bias,
            'scale.reference_reading_units': reading, 'scale.error_found': True,
            'helper.knows_error': True, 'scale.settled': not x.state['scale.wobbles'],
        })
    elif scene_id == 'tell_neighbor':
        x.act('admit_the_scale_error', {'market.phase': 'checked', 'helper.knows_error': True}, **{
            'market.phase': 'decided', 'helper.decision': 'honest',
            'neighbor.informed': True, 'neighbor.trust': 1,
            'helper.apologized': True,
        })
    elif scene_id == 'conceal_error':
        x.act('pretend_the_basket_is_right', {
            'market.phase': 'checked', 'helper.knows_error': True,
            'basket.location': 'helper',
        }, **{
            'market.phase': 'decided', 'helper.decision': 'concealed',
            'basket.location': 'neighbor', 'neighbor.location': 'home',
        })
    elif scene_id == 'settle_order':
        if x.state['helper.decision'] == 'concealed':
            x.act('neighbor_reweighs_and_returns', {
                'helper.decision': 'concealed', 'basket.location': 'neighbor',
                'neighbor.detected': False,
            }, **{
                'neighbor.detected': True, 'neighbor.informed': True,
                'neighbor.location': 'market', 'basket.location': 'helper',
            })
            x.act('apologize_without_excuse', {
                'neighbor.detected': True, 'helper.apologized': False,
            }, **{'helper.apologized': True, 'neighbor.trust': -1})
        needed = x.state['order.units'] - x.state['order.apples']
        available = x.state['apples.available']
        if available >= needed:
            x.act('replace_missing_apples', {
                'market.phase': 'decided', 'basket.location': 'helper',
                'apples.available': available,
            }, **{
                'market.phase': 'settled', 'order.status': 'full',
                'order.apples': x.state['order.units'],
                'apples.available': available - needed,
                'basket.location': 'neighbor', 'neighbor.location': 'home',
            })
        elif x.state['neighbor.will_mix']:
            apple_addition = available
            pear_addition = x.state['order.units'] - x.state['order.apples'] - apple_addition
            if pear_addition > x.state['pears.available']:
                raise StoryError('Not enough pears to complete the agreed blend')
            x.act('complete_order_with_pear_blend', {
                'market.phase': 'decided', 'basket.location': 'helper',
                'neighbor.will_mix': True, 'apples.available': available,
            }, **{
                'market.phase': 'settled', 'order.status': 'mixed',
                'order.apples': x.state['order.apples'] + apple_addition,
                'order.pears': pear_addition, 'apples.available': 0,
                'pears.available': x.state['pears.available'] - pear_addition,
                'basket.location': 'neighbor', 'neighbor.location': 'home',
            })
        else:
            current_apples = x.state['order.apples']
            x.act('return_payment_and_unfilled_basket', {
                'market.phase': 'decided', 'basket.location': 'helper',
                'order.apples': current_apples,
            }, **{
                'market.phase': 'settled', 'order.status': 'refunded',
                'order.payment': 'returned', 'order.apples': 0,
                'apples.available': x.state['apples.available'] + current_apples,
                'basket.location': 'market', 'neighbor.location': 'home',
            })
    elif scene_id == 'return_scale':
        x.act('reset_scale_to_zero', {
            'market.phase': 'settled', 'scale.owner': 'helper',
            'scale.bias_known': x.state['scale.bias_original'],
        }, **{
            'scale.bias_units': 0, 'scale.settled': True,
            'scale.reference_reading_units': 5,
        })
        x.act('verify_scale_with_reference_weight', {
            'scale.bias_units': 0, 'scale.reference_units': 5,
        }, **{'scale.verified': True})
        x.act('return_working_scale_to_keeper', {
            'scale.owner': 'helper', 'scale.verified': True,
        }, **{
            'scale.owner': 'keeper', 'scale.location': 'keeper',
            'scale.returned': True, 'market.phase': 'returned',
        })
    elif scene_id == 'ending':
        outcome = _expected_outcome(x.state)
        x.act('close_the_order_with_a_real_outcome', {
            'market.phase': 'returned', 'scale.returned': True,
        }, **{
            'market.phase': 'ended', 'story.ended': True,
            'story.outcome': outcome,
        })
    else:
        raise StoryError(f'No local play for scene: {scene_id}')

    after = deepcopy(x.state)
    validate(after)
    return Episode(
        id=scene_id, before=deepcopy(state), after=after,
        events=tuple(deepcopy(x.events)),
        text=render(scene_id, params, state, after),
    )


def _core_remaining(state):
    return {
        'start': 7, 'order': 6, 'filled': 5, 'checked': 4,
        'decided': 3, 'settled': 2, 'returned': 1, 'ended': 0,
    }[state['market.phase']]


def _optional_capacity(state):
    if state['market.phase'] not in ('start', 'order'):
        return 0
    return int(not state['child.received_apple']) + int(not state['neighbor.tasted_pear'])


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    p = params if params is not None else parameters(seed)
    if not isinstance(p, Parameters):
        raise ValueError('params must be a Parameters instance')
    rng = random.Random(seed)
    attempts = 0
    visited = 0

    def search(state, episodes):
        nonlocal attempts, visited
        visited += 1
        if visited > 5000:
            raise StoryError('Bounded scene search exhausted its 5000-node budget')
        remaining = count - len(episodes)
        core = _core_remaining(state)
        if remaining < core or remaining > core + _optional_capacity(state):
            return None
        if remaining == 0:
            return episodes if state['story.ended'] else None
        used = {episode.id for episode in episodes}
        choices = [scene_id for scene_id in SCENES
                   if scene_id not in used and guard(scene_id, state)]
        if remaining != 1:
            choices = [scene_id for scene_id in choices if scene_id != 'ending']
        rng.shuffle(choices)
        for scene_id in choices:
            attempts += 1
            episode = play_scene(p, state, scene_id)
            result = search(episode.after, episodes + (episode,))
            if result is not None:
                return result
        return None

    episodes = search(initial(p), ())
    if episodes is None:
        raise StoryError('No compatible complete route at the requested length')
    episode_rows = [{
        'id': episode.id,
        'before': deepcopy(episode.before),
        'after': deepcopy(episode.after),
        'events': deepcopy(list(episode.events)),
        'text': episode.text,
    } for episode in episodes]
    story = '\n\n'.join(episode['text'] for episode in episode_rows)
    return {
        'seed': seed,
        'parameters': asdict(p),
        'scene_count': count,
        'path': [episode['id'] for episode in episode_rows],
        'story': story,
        'episodes': episode_rows,
        'final_state': deepcopy(episode_rows[-1]['after']),
        'search_attempts': attempts,
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    state = initial(params)
    episodes = []
    used = set()
    for scene_id in path:
        if scene_id in used:
            raise StoryError('A scene cannot be repeated')
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode.after
        used.add(scene_id)
    return tuple(episodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    parser.add_argument('--params', type=Path, help='JSON file containing parameter overrides')
    args = parser.parse_args()
    base = asdict(parameters(args.seed))
    if args.params:
        overrides = json.loads(args.params.read_text(encoding='utf-8'))
        if not isinstance(overrides, dict):
            parser.error('--params must contain a JSON object')
        base.update(overrides)
    row = generate(args.seed, count=args.scenes, params=Parameters(**base))
    print(row['story'])


if __name__ == '__main__':
    main()
