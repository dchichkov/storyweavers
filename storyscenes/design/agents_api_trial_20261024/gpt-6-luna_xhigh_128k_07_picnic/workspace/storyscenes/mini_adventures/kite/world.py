'''Bounded, local-play picnic adventure. No runtime language model or network.'''
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
import random

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError


@dataclass(frozen=True, kw_only=True)
class Parameters:
    blanket_weight: int = 2
    gust_force: int = 2
    basket_latched: bool = True
    priority: str = 'blanket'
    bread_rolls: int = 3
    delay_minutes: int = 14

    def __post_init__(self):
        if type(self.blanket_weight) is not int or not 1 <= self.blanket_weight <= 3:
            raise ValueError('blanket_weight must be an integer from 1 to 3')
        if type(self.gust_force) is not int or not 1 <= self.gust_force <= 3:
            raise ValueError('gust_force must be an integer from 1 to 3')
        if type(self.basket_latched) is not bool:
            raise ValueError('basket_latched must be boolean')
        if not isinstance(self.priority, str) or self.priority not in ('blanket', 'lunch'):
            raise ValueError('priority must be blanket or lunch')
        if type(self.bread_rolls) is not int or not 1 <= self.bread_rolls <= 4:
            raise ValueError('bread_rolls must be an integer from 1 to 4')
        if type(self.delay_minutes) is not int or not 5 <= self.delay_minutes <= 30:
            raise ValueError('delay_minutes must be an integer from 5 to 30')


def parameters(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng = random.Random(seed)
    return Parameters(
        blanket_weight=rng.choice((1, 2, 3)),
        gust_force=rng.choice((1, 2, 3)),
        basket_latched=rng.choice((True, False)),
        priority=rng.choice(('blanket', 'lunch')),
        bread_rolls=rng.choice((1, 2, 3, 4)),
        delay_minutes=rng.choice((8, 12, 17, 23)),
    )


_STATE_KEYS = (
    'party.location', 'story.ended', 'story.outcome',
    'blanket.owner', 'blanket.holder', 'blanket.location', 'blanket.borrowed',
    'blanket.clean', 'blanket.dry', 'blanket.anchored', 'blanket.weight',
    'aunt.blanket_ready', 'basket.location', 'basket.latched', 'basket.secured',
    'gust.force', 'gust.priority', 'gust.seen', 'gust.passed', 'gust.blanket_wet',
    'picnic.spread', 'picnic.seat_saved', 'picnic.alarm', 'lunch.prepared',
    'food.planned', 'food.available', 'food.lost', 'food.served', 'food.spilled',
    'fruit.available', 'fruit.served', 'crumbs.available', 'cups.ready',
    'cousins.mood', 'vignette.used', 'reed.whistled', 'sparrows.fed',
    'cousin.location', 'cousin.arrived', 'cousin.welcomed', 'cousin.trust',
    'cousin.delay_minutes', 'meal.shared', 'meal.kind',
)


def initial(params):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    state = {
        'party.location': 'home', 'story.ended': False, 'story.outcome': '',
        'blanket.owner': 'Aunt Salma', 'blanket.holder': 'Aunt Salma',
        'blanket.location': 'porch', 'blanket.borrowed': False,
        'blanket.clean': True, 'blanket.dry': True, 'blanket.anchored': False,
        'blanket.weight': params.blanket_weight, 'aunt.blanket_ready': True,
        'basket.location': 'kitchen', 'basket.latched': params.basket_latched,
        'basket.secured': False, 'gust.force': params.gust_force,
        'gust.priority': params.priority, 'gust.seen': False, 'gust.passed': False,
        'gust.blanket_wet': False, 'picnic.spread': False,
        'picnic.seat_saved': False, 'picnic.alarm': False,
        'lunch.prepared': False, 'food.planned': params.bread_rolls,
        'food.available': 0, 'food.lost': 0, 'food.served': 0,
        'food.spilled': False, 'fruit.available': 0, 'fruit.served': 0,
        'crumbs.available': 0, 'cups.ready': False, 'cousins.mood': 'steady',
        'vignette.used': False, 'reed.whistled': False, 'sparrows.fed': False,
        'cousin.location': 'lane', 'cousin.arrived': False,
        'cousin.welcomed': False, 'cousin.trust': 0,
        'cousin.delay_minutes': params.delay_minutes,
        'meal.shared': False, 'meal.kind': '',
    }
    validate(state)
    return state


def validate(state):
    if not isinstance(state, dict) or set(state) != set(_STATE_KEYS):
        raise StoryError('State keys do not match the picnic world')
    if any(type(value) not in (str, bool, int) for value in state.values()):
        raise StoryError('World state values must be JSON-native scalars')
    bool_keys = (
        'story.ended', 'blanket.borrowed', 'blanket.clean', 'blanket.dry',
        'blanket.anchored', 'aunt.blanket_ready', 'basket.latched',
        'basket.secured', 'gust.seen', 'gust.passed', 'gust.blanket_wet',
        'picnic.spread', 'picnic.seat_saved', 'picnic.alarm', 'lunch.prepared',
        'food.spilled', 'cups.ready', 'vignette.used', 'reed.whistled',
        'sparrows.fed', 'cousin.arrived', 'cousin.welcomed', 'meal.shared',
    )
    if any(type(state[key]) is not bool for key in bool_keys):
        raise StoryError('A boolean world property has the wrong type')
    integer_ranges = (
        ('blanket.weight', 1, 3), ('gust.force', 1, 3), ('food.planned', 1, 4),
        ('food.available', 0, 4), ('food.lost', 0, 4), ('food.served', 0, 4),
        ('fruit.available', 0, 2), ('fruit.served', 0, 2),
        ('crumbs.available', 0, 1), ('cousin.trust', 0, 2),
        ('cousin.delay_minutes', 5, 30),
    )
    for key, low, high in integer_ranges:
        if type(state[key]) is not int or not low <= state[key] <= high:
            raise StoryError(f'Invalid integer state: {key}')
    string_values = {
        'party.location': ('home', 'meadow'),
        'story.outcome': ('', 'shared_lunch_dry_blanket', 'shared_lunch_wet_blanket', 'fruit_after_lost_rolls'),
        'blanket.owner': ('Aunt Salma',),
        'blanket.holder': ('Aunt Salma', 'Mara'),
        'blanket.location': ('porch', 'meadow', 'shallows'),
        'basket.location': ('kitchen', 'meadow', 'home'),
        'gust.priority': ('blanket', 'lunch'),
        'cousins.mood': ('steady', 'playful'),
        'cousin.location': ('lane', 'meadow', 'home'),
        'meal.kind': ('', 'rolls_and_fruit', 'fruit_and_crumbs'),
    }
    for key, choices in string_values.items():
        if not isinstance(state[key], str) or state[key] not in choices:
            raise StoryError(f'Invalid state value: {key}')
    if state['blanket.borrowed']:
        if state['blanket.holder'] != 'Mara' or state['aunt.blanket_ready']:
            raise StoryError('Borrowed blanket custody is inconsistent')
    elif (state['blanket.holder'] != 'Aunt Salma' or state['blanket.location'] != 'porch'
          or not state['aunt.blanket_ready']):
        raise StoryError('Returned blanket must be with Aunt Salma on the porch')
    if not state['picnic.spread']:
        if state['party.location'] != 'home' or state['blanket.location'] != 'porch':
            raise StoryError('The picnic party cannot move before spreading the blanket')
    if state['picnic.seat_saved'] != state['picnic.spread']:
        raise StoryError('The saved place belongs to the established picnic')
    if state['blanket.location'] == 'shallows' and state['party.location'] != 'meadow':
        raise StoryError('A blanket in the shallows must be beside the meadow')
    if state['cousin.arrived']:
        if state['cousin.location'] not in ('meadow', 'home'):
            raise StoryError('An arrived cousin must be at the picnic or home')
    elif state['cousin.location'] != 'lane':
        raise StoryError('The cousin cannot move before arriving')
    if not state['lunch.prepared']:
        if any(state[key] for key in ('food.available', 'food.lost', 'food.served',
                                      'fruit.available', 'fruit.served', 'crumbs.available')):
            raise StoryError('Food cannot exist before lunch is prepared')
    else:
        if state['food.available'] + state['food.lost'] + state['food.served'] != state['food.planned']:
            raise StoryError('Rolls must be conserved')
        if state['fruit.available'] + state['fruit.served'] != 2:
            raise StoryError('The two apples must be conserved')
    if state['food.spilled'] != (state['food.lost'] > 0):
        raise StoryError('Spilled-food history disagrees with the lost rolls')
    if state['food.lost'] not in (0, state['food.planned']):
        raise StoryError('This picnic tracks the rolls as a single exposed batch')
    if state['vignette.used'] != (state['reed.whistled'] or state['sparrows.fed']):
        raise StoryError('Optional vignette accounting disagrees')
    if state['reed.whistled'] and state['sparrows.fed']:
        raise StoryError('Only one optional vignette fits this short route')
    if state['meal.shared'] != state['cousin.welcomed']:
        raise StoryError('A welcome and shared meal are one completed encounter')
    if state['meal.shared']:
        if (state['meal.kind'] == '' or state['food.available'] != 0
                or state['fruit.available'] != 0 or state['fruit.served'] != 2):
            raise StoryError('The shared meal is incomplete')
        if (state['meal.kind'] == 'rolls_and_fruit') != (state['food.served'] > 0):
            raise StoryError('Meal description disagrees with the rolls served')
        expected_trust = 1 if state['food.served'] > 0 else 2
        if state['cousin.trust'] != expected_trust:
            raise StoryError('Trust must reflect the enacted welcome')
    elif state['meal.kind'] or state['cousin.trust'] != 0:
        raise StoryError('A meal or trust cannot precede the welcome')
    if state['gust.passed']:
        if not state['lunch.prepared']:
            raise StoryError('The gust cannot precede lunch preparation')
        expected_wet = not (state['blanket.weight'] >= state['gust.force']
                            or state['gust.priority'] == 'blanket')
        expected_lost = (state['food.planned'] if not state['basket.latched']
                         and state['gust.force'] > 1 and state['gust.priority'] != 'lunch' else 0)
        if state['gust.blanket_wet'] != expected_wet or state['food.lost'] != expected_lost:
            raise StoryError('Gust outcomes disagree with the chosen response and parameters')
        if not state['meal.shared'] and state['food.available'] != state['food.planned'] - expected_lost:
            raise StoryError('Available rolls disagree with the gust outcome')
        if not state['meal.shared'] and state['blanket.dry'] == expected_wet:
            raise StoryError('Blanket dryness disagrees with its gust history')
    elif state['gust.blanket_wet'] or state['food.lost']:
        raise StoryError('A gust consequence cannot precede the gust')
    if state['blanket.anchored'] and (state['blanket.location'] != 'meadow'
                                      or state['meal.shared'] or state['gust.blanket_wet']):
        raise StoryError('Only a dry, unsettled picnic blanket can remain anchored')
    if state['story.ended']:
        if not (state['meal.shared'] and state['cousin.welcomed']
                and state['party.location'] == 'home' and state['cousin.location'] == 'home'
                and state['basket.location'] == 'home' and not state['blanket.borrowed']
                and state['blanket.location'] == 'porch' and state['blanket.clean']
                and state['blanket.dry'] and state['aunt.blanket_ready']
                and state['food.available'] == 0 and state['fruit.available'] == 0
                and state['story.outcome']):
            raise StoryError('The ending leaves the welcome or borrowed blanket unfinished')
    elif state['story.outcome']:
        raise StoryError('An outcome cannot precede the ending')


@dataclass(frozen=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


SCENES = (
    'borrow_blanket', 'spread_picnic', 'prepare_lunch', 'reed_whistle',
    'gust_response', 'arrival', 'crumb_sparrows', 'share_lunch',
    'ending_feast', 'ending_damp', 'ending_apples',
)


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f'Unknown scene: {scene_id}')
    validate(state)
    if state['story.ended']:
        return False
    if scene_id == 'borrow_blanket':
        return not state['blanket.borrowed'] and state['party.location'] == 'home'
    if scene_id == 'spread_picnic':
        return state['blanket.borrowed'] and not state['picnic.spread'] and state['party.location'] == 'home'
    if scene_id == 'prepare_lunch':
        return state['picnic.spread'] and not state['lunch.prepared'] and state['party.location'] == 'meadow'
    if scene_id == 'reed_whistle':
        return (state['picnic.spread'] and not state['gust.passed']
                and not state['vignette.used'] and not state['reed.whistled'])
    if scene_id == 'gust_response':
        return state['lunch.prepared'] and not state['gust.passed'] and not state['cousin.arrived']
    if scene_id == 'arrival':
        return state['gust.passed'] and not state['cousin.arrived']
    if scene_id == 'crumb_sparrows':
        return (state['cousin.arrived'] and not state['meal.shared']
                and state['crumbs.available'] == 1 and not state['vignette.used'])
    if scene_id == 'share_lunch':
        return state['cousin.arrived'] and not state['meal.shared'] and state['picnic.seat_saved']
    if scene_id.startswith('ending_'):
        if not (state['meal.shared'] and state['cousin.welcomed'] and state['blanket.borrowed']):
            return False
        if scene_id == 'ending_feast':
            return state['food.served'] > 0 and not state['gust.blanket_wet']
        if scene_id == 'ending_damp':
            return state['food.served'] > 0 and state['gust.blanket_wet']
        return state['food.served'] == 0
    raise StoryError(f'Unknown scene: {scene_id}')


def _act(play, name, requires=None, changes=None):
    play.act(name, {} if requires is None else requires, **({} if changes is None else changes))


def _render(scene_id, params, before, after):
    if scene_id == 'borrow_blanket':
        return ('At Aunt Salma’s porch, Mara asked to borrow the blue picnic blanket for Rowan’s late lunch. '
                'Kit added, “We’ll bring it back clean; she hates sitting on damp grass.” Aunt Salma handed it over. '
                '“The river makes its own weather,” she warned. Mara folded the corners over her arm, already picturing Rowan arriving to a place saved for her.')
    if scene_id == 'spread_picnic':
        return ('They walked to the riverside meadow, where the grass leaned one way and the water flashed between reeds. '
                'Mara spread the blanket beneath a willow. Kit chose a dry patch above the bank, then tucked one corner under a smooth stone. '
                '“A seat, not a sail,” she said. Mara laughed, but checked the other corners too. They left a place open for Rowan.')
    if scene_id == 'prepare_lunch':
        roll_word = 'roll' if params.bread_rolls == 1 else 'rolls'
        return (f'Kit opened the basket: {params.bread_rolls} small {roll_word}, two apples, and a jar of mint water. '
                'Mara set each roll beside a folded napkin. One broke, leaving crumbs on the borrowed blue cloth. '
                '“Rowan likes the crusty bits,” Kit said. They kept the pieces, cut the apples, and left the place between them empty.')
    if scene_id == 'reed_whistle':
        return ('While Mara arranged napkins, Kit pinched a hollow reed and blew. The note wobbled like a duck’s complaint. '
                'A gust answered from the river; Kit lowered the reed. “I didn’t call that one,” she said. '
                'Mara grinned and set the reed beside the basket. For a moment, waiting sounded like a game rather than a clock.')
    if scene_id == 'gust_response':
        if after['gust.blanket_wet']:
            return ('The gust tore one corner loose. Kit hugged the unlatched basket to her chest while Mara grabbed the blanket’s edge from the shallows. '
                    'The rolls were safe; the blue cloth came back dripping. “I chose lunch,” Kit said. Mara squeezed river water from a corner. '
                    '“And I chose you not to chase both.” Neither pretended it was dry.')
        if after['food.lost']:
            return ('At the gust, Mara caught the blanket before it could skate toward the river. Kit reached for the unlatched basket, '
                    'but rolls bounced across the grass and crumbs spun away. She saved an apple. “The blanket’s safe,” Mara said. '
                    'Kit looked at the scattered lunch. “Then we’ll have to make welcome out of what’s left.”')
        return ('A gust rushed off the river. Mara pinned the blanket’s corners with stones while Kit caught the basket against her knees. '
                'Napkins lifted, but the rolls stayed put. “That was your weather,” Kit said. Mara looked at the water, then at the empty place. '
                '“Good thing we made room for Rowan, not the wind.”')
    if scene_id == 'arrival':
        extra = (' Kit answered with the reed’s crooked note; Rowan laughed.' if after['cousins.mood'] == 'playful' else '')
        return (f'After {params.delay_minutes} minutes, Rowan appeared pushing her bicycle, one trouser cuff dark with chain grease. '
                '“The chain came loose. I thought you’d leave.” Mara patted the empty place. Kit moved the basket closer. '
                '“We saved your seat.” Rowan’s shoulders dropped. “I brought an apology, but it seems you brought lunch.” '
                f'The cousins made room without asking her to explain twice.{extra}')
    if scene_id == 'crumb_sparrows':
        return ('Rowan noticed crumbs shining on the blanket. Before anyone swept them away, two sparrows hopped beneath the willow. '
                'Kit tipped the crumbs onto a flat stone, and the birds pecked them up. “They were waiting too,” Rowan said. '
                'Mara shook the cloth gently. Their small audience vanished into the reeds, leaving the three cousins smiling.')
    if scene_id == 'share_lunch':
        if after['food.served'] > 0:
            return ('Rowan reached for the smallest roll, then paused. “Is this the part where I apologize for being late?” '
                    '“No,” Mara said. “This is the part where you eat.” They split the rolls and apples, poured mint water, and listened to Rowan’s chain story. '
                    'Kit admitted how long the wait felt; Rowan stayed for every last bite.')
        crumb_words = 'only apples' if after['sparrows.fed'] else 'apples and a scatter of crumbs'
        return (f'Rowan saw {crumb_words}. Kit told her how the gust had taken the rolls while Mara kept Aunt Salma’s blanket from the river. '
                '“You saved the thing you borrowed,” Rowan said. “We saved the fruit too,” Mara answered. Rowan cut the apples into three uneven moons, '
                'and they shared them anyway. Nobody had to pretend it was the planned lunch.')
    if scene_id == 'ending_feast':
        return ('Aunt Salma met them at the porch. The cousins rinsed the grass marks from the blanket and spread it on the sunny rail until dry again. '
                'She took it back, clean and ready for another picnic. Rowan thanked them for saving her place; Kit asked what she wanted next time. '
                '“You,” Rowan said, and Mara made room.')
    if scene_id == 'ending_damp':
        return ('They carried the damp blanket home between them, while Rowan guarded the basket. At Aunt Salma’s porch they rinsed it and spread it on the sunny rail until dry. '
                '“You kept the lunch and told the truth about the splash,” she said, taking back a clean blanket. Rowan thanked them for waiting; '
                'Kit gave her the warmest apple slice.')
    if scene_id == 'ending_apples':
        return ('On the walk home, Mara told Aunt Salma that the rolls had gone into the grass. Kit carried the blanket, clean after their rinse and dry on the porch rail. '
                'Aunt Salma took it back, useful for the next clear day. Rowan squeezed both cousins’ hands. “You kept a place for me,” she said. '
                'That mattered more than a perfect lunch.')
    raise StoryError(f'No prose for scene: {scene_id}')


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise ValueError('params must be a Parameters instance')
    validate(state)
    if scene_id not in SCENES or not guard(scene_id, state):
        raise StoryError(f'Scene not compatible with current state: {scene_id}')
    play = LocalPlay(state, actors=('Mara', 'Kit', 'Rowan'), validate=validate)
    if scene_id == 'borrow_blanket':
        _act(play, 'borrow_with_a_promise', {'blanket.holder': 'Aunt Salma', 'aunt.blanket_ready': True}, {
            'blanket.holder': 'Mara', 'blanket.borrowed': True, 'aunt.blanket_ready': False,
        })
    elif scene_id == 'spread_picnic':
        _act(play, 'walk_to_the_meadow', {'party.location': 'home', 'blanket.borrowed': True}, {
            'party.location': 'meadow',
        })
        _act(play, 'spread_and_save_a_place', {'party.location': 'meadow', 'blanket.location': 'porch'}, {
            'blanket.location': 'meadow', 'picnic.spread': True, 'picnic.seat_saved': True,
        })
    elif scene_id == 'prepare_lunch':
        _act(play, 'unpack_lunch', {'picnic.spread': True, 'basket.location': 'kitchen'}, {
            'basket.location': 'meadow', 'lunch.prepared': True,
            'food.available': play.state['food.planned'], 'fruit.available': 2,
            'crumbs.available': 1, 'blanket.clean': False, 'cups.ready': True,
        })
    elif scene_id == 'reed_whistle':
        _act(play, 'try_the_reed_whistle', {'picnic.spread': True, 'vignette.used': False}, {
            'reed.whistled': True, 'vignette.used': True, 'cousins.mood': 'playful',
        })
    elif scene_id == 'gust_response':
        _act(play, 'notice_the_river_gust', {'lunch.prepared': True, 'gust.passed': False}, {
            'gust.seen': True, 'picnic.alarm': True,
        })
        blanket_stays_dry = (play.state['blanket.weight'] >= play.state['gust.force']
                             or play.state['gust.priority'] == 'blanket')
        food_stays = (play.state['basket.latched'] or play.state['gust.force'] == 1
                      or play.state['gust.priority'] == 'lunch')
        if blanket_stays_dry:
            _act(play, 'pin_the_blanket_with_stones', {'gust.seen': True}, {
                'blanket.anchored': True,
            })
        else:
            _act(play, 'gust_pull_blanket_into_shallows', {'gust.seen': True}, {
                'blanket.location': 'shallows', 'blanket.dry': False,
            })
            _act(play, 'pull_blanket_back_to_grass', {'blanket.location': 'shallows'}, {
                'blanket.location': 'meadow',
            })
        if food_stays:
            action = 'catch_the_basket' if not play.state['basket.latched'] else 'hold_the_latched_basket'
            _act(play, action, {'lunch.prepared': True}, {'basket.secured': True})
        else:
            _act(play, 'watch_the_unlatched_rolls_scatter', {'basket.latched': False}, {
                'food.available': 0, 'food.lost': play.state['food.planned'],
                'food.spilled': True, 'basket.secured': False,
            })
        _act(play, 'finish_the_gust_response', {'gust.seen': True}, {
            'gust.passed': True, 'gust.blanket_wet': not blanket_stays_dry,
        })
    elif scene_id == 'arrival':
        greeting = {'cousin.location': 'lane', 'cousin.arrived': False}
        _act(play, 'welcome_rowan_into_the_meadow', greeting, {
            'cousin.location': 'meadow', 'cousin.arrived': True,
        })
    elif scene_id == 'crumb_sparrows':
        _act(play, 'offer_the_loose_crumbs', {'cousin.arrived': True, 'crumbs.available': 1,
                                              'vignette.used': False}, {
            'crumbs.available': 0, 'sparrows.fed': True, 'vignette.used': True,
        })
    elif scene_id == 'share_lunch':
        if play.state['food.available'] > 0:
            changes = {
                'food.available': 0, 'food.served': play.state['food.planned'],
                'fruit.available': 0, 'fruit.served': 2, 'crumbs.available': 0,
                'meal.shared': True, 'meal.kind': 'rolls_and_fruit',
                'cousin.welcomed': True, 'cousin.trust': 1,
                'blanket.anchored': False, 'basket.secured': False,
            }
            _act(play, 'share_the_saved_rolls_and_apples', {
                'cousin.arrived': True, 'food.available': play.state['food.available'],
            }, changes)
        else:
            _act(play, 'own_the_lost_rolls_and_share_apples', {
                'cousin.arrived': True, 'food.available': 0, 'fruit.available': 2,
            }, {
                'fruit.available': 0, 'fruit.served': 2, 'crumbs.available': 0,
                'meal.shared': True, 'meal.kind': 'fruit_and_crumbs',
                'cousin.welcomed': True, 'cousin.trust': 2,
                'blanket.anchored': False, 'basket.secured': False,
            })
    else:
        outcome = {
            'ending_feast': 'shared_lunch_dry_blanket',
            'ending_damp': 'shared_lunch_wet_blanket',
            'ending_apples': 'fruit_after_lost_rolls',
        }[scene_id]
        _act(play, 'carry_the_picnic_home', {
            'party.location': 'meadow', 'cousin.welcomed': True,
            'blanket.location': 'meadow', 'blanket.borrowed': True,
        }, {
            'party.location': 'home', 'cousin.location': 'home',
            'basket.location': 'home', 'blanket.location': 'porch',
        })
        _act(play, 'rinse_and_sun_the_blanket', {
            'blanket.location': 'porch', 'blanket.holder': 'Mara',
        }, {'blanket.clean': True, 'blanket.dry': True})
        _act(play, 'return_the_useful_blanket', {'blanket.borrowed': True}, {
            'blanket.holder': 'Aunt Salma', 'blanket.borrowed': False,
            'aunt.blanket_ready': True,
        })
        _act(play, 'finish_with_a_complete_welcome', {'meal.shared': True}, {
            'story.ended': True, 'story.outcome': outcome,
        })
    after = deepcopy(play.state)
    return Episode(scene_id, deepcopy(state), after, tuple(deepcopy(play.events)),
                   _render(scene_id, params, state, after))


def _minimum_core_scenes(state):
    if state['story.ended']:
        return 0
    completed = (
        not state['aunt.blanket_ready'], state['picnic.spread'],
        state['lunch.prepared'], state['gust.passed'], state['cousin.arrived'],
        state['meal.shared'], state['story.ended'],
    )
    return sum(not done for done in completed)


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(count) is not int or count not in (7, 8):
        raise ValueError('count must be exactly 7 or 8')
    p = parameters(seed) if params is None else params
    if not isinstance(p, Parameters):
        raise ValueError('params must be a Parameters instance')
    rng = random.Random(seed)
    attempts = 0

    def search(state, episodes):
        nonlocal attempts
        remaining = count - len(episodes)
        if state['story.ended']:
            return episodes if remaining == 0 else None
        if remaining < _minimum_core_scenes(state) or remaining <= 0:
            return None
        used = {episode.id for episode in episodes}
        choices = [scene_id for scene_id in SCENES
                   if scene_id not in used and guard(scene_id, state)]
        rng.shuffle(choices)
        for scene_id in choices:
            attempts += 1
            if attempts > 5000:
                raise StoryError('Bounded scene search exhausted')
            episode = play_scene(p, state, scene_id)
            answer = search(episode.after, episodes + (episode,))
            if answer is not None:
                return answer
        return None

    episodes = search(initial(p), ())
    if episodes is None:
        raise StoryError('No compatible route at the requested scene count')
    episode_rows = []
    for episode in episodes:
        row = asdict(episode)
        row['events'] = list(episode.events)
        episode_rows.append(row)
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
        raise ValueError('params must be a Parameters instance')
    if not isinstance(path, (tuple, list)):
        raise ValueError('path must be a sequence of scene IDs')
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
    parser.add_argument('--params', help='JSON file containing validated parameter overrides')
    args = parser.parse_args()
    overrides = {}
    if args.params:
        try:
            overrides = json.loads(open(args.params, encoding='utf-8').read())
        except (OSError, json.JSONDecodeError) as exc:
            parser.error(str(exc))
        if not isinstance(overrides, dict):
            parser.error('--params must contain a JSON object')
    try:
        p = Parameters(**(asdict(parameters(args.seed)) | overrides))
        row = generate(args.seed, count=args.scenes, params=p)
    except (ValueError, StoryError) as exc:
        parser.error(str(exc))
    print(row['story'])


if __name__ == '__main__':
    main()
