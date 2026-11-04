'''A bounded pottery adventure composed from guarded, atomic mini-plays.'''
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
    clay_grams: int = 240
    sponge_damp: bool = True
    wheel_level: bool = True
    kiln_even: bool = True
    finish_choice: str = 'keep'

    def __post_init__(self):
        if type(self.clay_grams) is not int or not 180 <= self.clay_grams <= 280:
            raise ValueError('clay_grams must be an integer in [180, 280]')
        for name in ('sponge_damp', 'wheel_level', 'kiln_even'):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f'{name} must be boolean')
        if self.finish_choice not in ('keep', 'repair'):
            raise ValueError('finish_choice must be keep or repair')


def _check_parameters(p):
    if not isinstance(p, Parameters):
        raise ValueError('params must be a Parameters instance')


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    clay = rng.choice((190, 215, 240, 255, 270))
    choice = rng.choice(('keep', 'repair')) if clay >= 230 else 'keep'
    return Parameters(clay_grams=clay, sponge_damp=rng.choice((True, False)),
                      wheel_level=rng.choice((True, False)), kiln_even=rng.choice((True, False)),
                      finish_choice=choice)


STATE_KEYS = (
    'story.ended', 'story.outcome', 'mina.goal', 'mina.location', 'mina.has_rib',
    'mina.knows_thumb_rest', 'mina.helped_omi', 'omi.needs_help', 'omi.clay_wedged',
    'grandpa.location', 'grandpa.has_gift', 'grandpa.used_gift', 'clay.initial',
    'clay.remaining', 'clay.location', 'clay.wedged', 'sponge.location', 'sponge.damp',
    'rib.owner', 'rib.location', 'rib.clean', 'rib.usable', 'rib.used', 'cup.owner',
    'cup.location', 'cup.stage', 'cup.mass', 'cup.rim', 'cup.wall_thin', 'cup.handle',
    'cup.thumb_rest', 'cup.treatment', 'cup.decided', 'cup.pour_lip', 'cup.slow_dried',
    'cup.glazed', 'cup.cracked', 'cup.use', 'craft.finish_choice', 'kiln.even',
)


def initial(params):
    _check_parameters(params)
    return {
        'story.ended': False, 'story.outcome': '',
        'mina.goal': 'make Grandpa a cup he can hold with stiff fingers',
        'mina.location': 'workshop', 'mina.has_rib': False,
        'mina.knows_thumb_rest': False, 'mina.helped_omi': False,
        'omi.needs_help': True, 'omi.clay_wedged': False,
        'grandpa.location': 'home', 'grandpa.has_gift': False, 'grandpa.used_gift': False,
        'clay.initial': params.clay_grams, 'clay.remaining': params.clay_grams,
        'clay.location': 'covered_tray', 'clay.wedged': False,
        'sponge.location': 'basin', 'sponge.damp': params.sponge_damp,
        'rib.owner': 'Vale', 'rib.location': 'peg', 'rib.clean': True,
        'rib.usable': True, 'rib.used': False,
        'cup.owner': 'Mina', 'cup.location': 'none', 'cup.stage': 'none',
        'cup.mass': 0, 'cup.rim': 'none', 'cup.wall_thin': False,
        'cup.handle': 'none', 'cup.thumb_rest': False,
        'cup.treatment': 'undecided', 'cup.decided': False, 'cup.pour_lip': False,
        'cup.slow_dried': False, 'cup.glazed': False, 'cup.cracked': False,
        'cup.use': 'none', 'craft.finish_choice': params.finish_choice,
        'kiln.even': params.kiln_even,
    }


def validate(state):
    if not isinstance(state, dict) or set(state) != set(STATE_KEYS):
        raise StoryError('State keys do not match this world')
    if any(type(value) not in (str, bool, int) for value in state.values()):
        raise StoryError('State values must be JSON-native scalars')
    if type(state['story.ended']) is not bool or type(state['story.outcome']) is not str:
        raise StoryError('Invalid story outcome fields')
    if state['story.ended'] != bool(state['story.outcome']):
        raise StoryError('Ended state and outcome disagree')
    for key in ('mina.has_rib', 'mina.knows_thumb_rest', 'mina.helped_omi',
                'omi.needs_help', 'omi.clay_wedged', 'grandpa.has_gift',
                'grandpa.used_gift', 'clay.wedged', 'sponge.damp', 'rib.clean',
                'rib.usable', 'rib.used', 'cup.wall_thin', 'cup.thumb_rest',
                'cup.decided', 'cup.pour_lip', 'cup.slow_dried', 'cup.glazed',
                'cup.cracked', 'kiln.even'):
        if type(state[key]) is not bool:
            raise StoryError(f'{key} must be boolean')
    if type(state['clay.initial']) is not int or not 180 <= state['clay.initial'] <= 280:
        raise StoryError('Invalid original clay amount')
    if any(type(state[k]) is not int or state[k] < 0 for k in
           ('clay.remaining', 'cup.mass')):
        raise StoryError('Clay amounts must be nonnegative integers')
    if state['clay.remaining'] + state['cup.mass'] != state['clay.initial']:
        raise StoryError('Clay mass was lost or duplicated')
    if state['craft.finish_choice'] not in ('keep', 'repair'):
        raise StoryError('Invalid flaw choice')
    if state['rib.owner'] not in ('Vale', 'Mina') or state['rib.location'] not in ('peg', 'worktable', 'wheel'):
        raise StoryError('Invalid rib custody or location')
    if (state['rib.owner'] == 'Vale') != (state['rib.location'] == 'peg'):
        raise StoryError('The rib cannot be in two places or owned by the wrong person')
    if state['mina.has_rib'] != (state['rib.owner'] == 'Mina'):
        raise StoryError('Mina and the rib custody record disagree')
    if state['rib.owner'] == 'Mina' and state['rib.location'] == 'wheel' and not state['rib.used']:
        raise StoryError('An unused rib cannot already be on the wheel')
    if state['cup.stage'] not in ('none', 'raw', 'in_kiln', 'fired', 'cracked'):
        raise StoryError('Unknown cup stage')
    if state['cup.rim'] not in ('none', 'crooked', 'wavy', 'even'):
        raise StoryError('Unknown rim shape')
    if state['cup.treatment'] not in ('undecided', 'kept', 'repaired'):
        raise StoryError('Unknown flaw treatment')
    if state['cup.use'] not in ('none', 'drink', 'pencil_holder'):
        raise StoryError('Unknown cup use')
    if state['cup.owner'] not in ('Mina', 'Grandpa'):
        raise StoryError('Unknown cup owner')
    if state['cup.stage'] == 'none':
        if state['cup.location'] != 'none' or state['cup.rim'] != 'none' or state['cup.mass'] != 0:
            raise StoryError('A cup without clay has physical features')
    elif state['cup.stage'] == 'raw':
        if state['cup.location'] not in ('drying_shelf', 'sheltered_shelf'):
            raise StoryError('Raw cup is not on a drying shelf')
        if state['cup.rim'] not in ('crooked', 'wavy', 'even'):
            raise StoryError('Raw cup has no rim')
    elif state['cup.stage'] == 'in_kiln':
        if state['cup.location'] != 'kiln' or not state['cup.glazed'] or not state['cup.decided']:
            raise StoryError('Cup cannot be fired before it is glazed and finished')
    elif state['cup.stage'] in ('fired', 'cracked'):
        if state['cup.location'] not in ('cooling_rack', 'Grandpa_table'):
            raise StoryError('Fired cup is not cooling or gifted')
        if state['cup.glazed'] is not True or not state['cup.decided']:
            raise StoryError('Fired cup lacks its finish')
        if state['cup.cracked'] != (state['cup.stage'] == 'cracked'):
            raise StoryError('Crack flag and firing result disagree')
    if state['cup.decided'] != (state['cup.treatment'] != 'undecided'):
        raise StoryError('Choice and treatment disagree')
    if state['cup.treatment'] == 'kept' and not state['cup.pour_lip']:
        raise StoryError('Keeping the flaw must give the low edge a purpose')
    if state['cup.treatment'] == 'repaired' and (state['cup.pour_lip'] or state['cup.rim'] != 'even'):
        raise StoryError('A repaired rim is inconsistent')
    if state['cup.thumb_rest'] and not state['mina.knows_thumb_rest']:
        raise StoryError('A thumb rest needs its remembered design cue')
    if state['sponge.location'] not in ('basin', 'wheel', 'Omi_hands'):
        raise StoryError('Unknown sponge location')
    if state['story.ended']:
        if (state['rib.owner'] != 'Vale' or state['rib.location'] != 'peg' or
                not state['rib.clean'] or not state['rib.usable'] or not state['rib.used']):
            raise StoryError('The borrowed shaping tool was not returned useful')
        if (state['cup.owner'] != 'Grandpa' or state['cup.location'] != 'Grandpa_table' or
                not state['grandpa.has_gift'] or not state['grandpa.used_gift']):
            raise StoryError('The gift was not delivered and used')
        expected = {
            ('fired', 'kept'): ('crooked_rim_cup_in_use', 'drink'),
            ('fired', 'repaired'): ('smoothed_cup_in_use', 'drink'),
            ('cracked', 'kept'): ('cracked_cup_repurposed_as_pencil_holder', 'pencil_holder'),
        }
        pair = (state['cup.stage'], state['cup.treatment'])
        if pair not in expected or (state['story.outcome'], state['cup.use']) != expected[pair]:
            raise StoryError('Ending does not match the cup that was made')
    else:
        if state['story.outcome'] or state['grandpa.used_gift']:
            raise StoryError('An unfinished story has a completed outcome')
        if state['cup.owner'] == 'Grandpa' or state['cup.use'] != 'none':
            raise StoryError('An unended story has already delivered its gift')
    return None


SCENES = (
    'borrow_rib', 'old_handle_memory', 'wedge_clay', 'shape_cup',
    'sheltered_shelf', 'decide_flaw', 'fire_cup',
    'ending_kept', 'ending_repaired', 'ending_cracked',
)
_OPTIONAL = frozenset(('old_handle_memory', 'sheltered_shelf'))
_ENDINGS = frozenset(('ending_kept', 'ending_repaired', 'ending_cracked'))


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f'Unknown scene: {scene_id}')
    validate(state)
    if state['story.ended']:
        return False
    if scene_id == 'borrow_rib':
        return state['rib.owner'] == 'Vale' and not state['mina.has_rib']
    if scene_id == 'old_handle_memory':
        return state['mina.has_rib'] and not state['mina.knows_thumb_rest'] and not state['clay.wedged']
    if scene_id == 'wedge_clay':
        return state['mina.has_rib'] and not state['clay.wedged']
    if scene_id == 'shape_cup':
        return (state['clay.wedged'] and state['sponge.location'] == 'wheel' and
                state['sponge.damp'] and state['cup.stage'] == 'none' and
                state['rib.owner'] == 'Mina')
    if scene_id == 'sheltered_shelf':
        return (state['cup.stage'] == 'raw' and not state['cup.decided'] and
                not state['cup.slow_dried'] and state['omi.needs_help'])
    if scene_id == 'decide_flaw':
        if state['cup.stage'] != 'raw' or state['cup.decided'] or not state['rib.used']:
            return False
        if state['craft.finish_choice'] == 'repair':
            return state['clay.remaining'] >= 30 and state['sponge.damp']
        return True
    if scene_id == 'fire_cup':
        return state['cup.stage'] == 'raw' and state['cup.decided']
    if scene_id == 'ending_kept':
        return state['cup.stage'] == 'fired' and state['cup.treatment'] == 'kept'
    if scene_id == 'ending_repaired':
        return state['cup.stage'] == 'fired' and state['cup.treatment'] == 'repaired'
    if scene_id == 'ending_cracked':
        return state['cup.stage'] == 'cracked' and state['cup.treatment'] == 'kept'
    return False


def play_scene(params, state, scene_id):
    _check_parameters(params)
    validate(state)
    if not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    before = deepcopy(state)
    x = LocalPlay(state, actors=('Mina', 'Mrs. Vale', 'Omi', 'Grandpa'), validate=validate)
    if scene_id == 'borrow_rib':
        x.act('borrow_wooden_rib', {'rib.owner': 'Vale', 'rib.location': 'peg'},
              **{'rib.owner': 'Mina', 'rib.location': 'worktable', 'mina.has_rib': True})
    elif scene_id == 'old_handle_memory':
        x.act('remember_grandpas_thumb_hollow', {'mina.knows_thumb_rest': False},
              **{'mina.knows_thumb_rest': True})
    elif scene_id == 'wedge_clay':
        x.act('carry_clay_to_wheel', {'clay.location': 'covered_tray'},
              **{'clay.location': 'wheel'})
        sponge_changes = {'sponge.location': 'wheel'}
        if not x.state['sponge.damp']:
            sponge_changes['sponge.damp'] = True
        x.act('wet_and_wring_sponge' if not x.state['sponge.damp'] else 'set_damp_sponge_by_wheel',
              {'sponge.location': 'basin'}, **sponge_changes)
        x.act('wedge_and_center_clay', {'clay.location': 'wheel', 'clay.wedged': False},
              **{'clay.wedged': True})
    elif scene_id == 'shape_cup':
        thin = params.clay_grams < 220 or not params.wheel_level
        x.act('shape_cup_with_borrowed_rib',
              {'clay.wedged': True, 'rib.owner': 'Mina', 'rib.location': 'worktable'},
              **{'cup.stage': 'raw', 'cup.location': 'drying_shelf', 'cup.mass': 180,
                 'clay.remaining': params.clay_grams - 180,
                 'cup.rim': 'crooked' if not params.wheel_level else 'wavy',
                 'cup.wall_thin': thin, 'cup.handle': 'broad',
                 'cup.thumb_rest': x.state['mina.knows_thumb_rest'],
                 'cup.treatment': 'undecided', 'cup.decided': False, 'cup.pour_lip': False,
                 'cup.slow_dried': False, 'cup.glazed': False, 'cup.cracked': False,
                 'cup.use': 'none', 'rib.location': 'wheel', 'rib.clean': False, 'rib.used': True})
    elif scene_id == 'sheltered_shelf':
        x.act('move_cup_out_of_draft', {'cup.location': 'drying_shelf'},
              **{'cup.location': 'sheltered_shelf', 'cup.slow_dried': True})
        x.act('lend_sponge_to_omi', {'sponge.location': 'wheel', 'omi.needs_help': True},
              **{'sponge.location': 'Omi_hands'})
        x.act('help_omi_wring_his_clay', {'sponge.location': 'Omi_hands'},
              **{'omi.clay_wedged': True, 'omi.needs_help': False})
        x.act('take_sponge_back_to_wheel', {'sponge.location': 'Omi_hands'},
              **{'sponge.location': 'wheel', 'mina.helped_omi': True})
    elif scene_id == 'decide_flaw':
        if params.finish_choice == 'keep':
            x.act('pinch_low_edge_into_pouring_lip',
                  {'cup.stage': 'raw', 'cup.decided': False, 'sponge.damp': True},
                  **{'cup.treatment': 'kept', 'cup.decided': True, 'cup.pour_lip': True})
        else:
            remaining = x.state['clay.remaining']
            x.act('add_reserved_clay_to_thin_side',
                  {'cup.stage': 'raw', 'cup.decided': False, 'sponge.damp': True,
                   'clay.remaining': remaining},
                  **{'clay.remaining': remaining - 30, 'cup.mass': x.state['cup.mass'] + 30,
                     'cup.wall_thin': False})
            x.act('compress_rim_with_borrowed_rib', {'rib.owner': 'Mina', 'rib.used': True},
                  **{'cup.rim': 'even', 'cup.treatment': 'repaired',
                     'cup.decided': True, 'cup.pour_lip': False})
    elif scene_id == 'fire_cup':
        x.act('brush_on_clear_glaze', {'cup.stage': 'raw', 'cup.decided': True},
              **{'cup.glazed': True})
        x.act('load_cup_into_kiln', {'cup.stage': 'raw', 'cup.glazed': True},
              **{'cup.stage': 'in_kiln', 'cup.location': 'kiln'})
        crack = (not params.kiln_even and x.state['cup.wall_thin'] and
                 not x.state['cup.slow_dried'] and x.state['cup.treatment'] == 'kept')
        x.act('fire_and_cool_cup', {'cup.stage': 'in_kiln'},
              **{'cup.stage': 'cracked' if crack else 'fired',
                 'cup.location': 'cooling_rack', 'cup.cracked': crack})
    elif scene_id in _ENDINGS:
        x.act('clean_and_return_rib', {'rib.owner': 'Mina', 'rib.used': True},
              **{'rib.owner': 'Vale', 'rib.location': 'peg', 'rib.clean': True,
                 'rib.usable': True, 'mina.has_rib': False})
        use = 'pencil_holder' if scene_id == 'ending_cracked' else 'drink'
        x.act('give_cup_to_grandpa', {'cup.owner': 'Mina', 'cup.location': 'cooling_rack'},
              **{'cup.owner': 'Grandpa', 'cup.location': 'Grandpa_table', 'cup.use': use,
                 'grandpa.has_gift': True})
        outcome = {
            'ending_kept': 'crooked_rim_cup_in_use',
            'ending_repaired': 'smoothed_cup_in_use',
            'ending_cracked': 'cracked_cup_repurposed_as_pencil_holder',
        }[scene_id]
        x.act('grandpa_uses_the_gift', {'grandpa.has_gift': True, 'grandpa.used_gift': False},
              **{'grandpa.used_gift': True, 'story.ended': True, 'story.outcome': outcome})
    episode = {
        'id': scene_id, 'before': before, 'after': deepcopy(x.state),
        'events': deepcopy(x.events),
        'text': render(scene_id, params, before, x.state),
    }
    return episode


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    p = parameters(seed) if params is None else params
    _check_parameters(p)
    start = initial(p)
    rng = random.Random(seed)
    wanted_optional = count - 6
    attempts = 0
    budget = 2000

    def search(state, episodes):
        nonlocal attempts
        remaining = count - len(episodes)
        optional_used = sum(ep['id'] in _OPTIONAL for ep in episodes)
        if remaining == 0:
            return episodes if state['story.ended'] and optional_used == wanted_optional else None
        if optional_used > wanted_optional:
            return None
        choices = [scene_id for scene_id in SCENES
                   if scene_id not in {ep['id'] for ep in episodes} and guard(scene_id, state)]
        rng.shuffle(choices)
        for scene_id in choices:
            if scene_id in _OPTIONAL and optional_used >= wanted_optional:
                continue
            if scene_id in _ENDINGS:
                if remaining != 1 or optional_used != wanted_optional:
                    continue
            elif remaining == 1:
                continue
            attempts += 1
            if attempts > budget:
                raise StoryError(f'Scene search budget exhausted ({budget} attempts)')
            episode = play_scene(p, state, scene_id)
            answer = search(episode['after'], episodes + (episode,))
            if answer is not None:
                return answer
        return None

    episodes = search(start, ())
    if episodes is None:
        raise StoryError('No complete route at the requested length and parameters')
    return {
        'seed': seed,
        'parameters': asdict(p),
        'scene_count': count,
        'path': [ep['id'] for ep in episodes],
        'story': '\n\n'.join(ep['text'] for ep in episodes),
        'episodes': [deepcopy(ep) for ep in episodes],
        'final_state': deepcopy(episodes[-1]['after']),
        'search_attempts': attempts,
    }


def replay(params, path):
    _check_parameters(params)
    state = initial(params)
    episodes = []
    seen = set()
    for scene_id in path:
        if scene_id in seen:
            raise StoryError(f'Scene repeated: {scene_id}')
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode['after']
        seen.add(scene_id)
    return episodes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--scenes', type=int, choices=(7, 8), default=8)
    parser.add_argument('--params', help='Path to a JSON object of complete Parameters fields')
    args = parser.parse_args()
    supplied = None
    if args.params:
        payload = json.loads(open(args.params, encoding='utf-8').read())
        if not isinstance(payload, dict):
            parser.error('--params must contain a JSON object')
        supplied = Parameters(**payload)
    row = generate(args.seed, count=args.scenes, params=supplied)
    print(row['story'])


if __name__ == '__main__':
    main()
