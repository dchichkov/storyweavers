import random
from runtime import WorldSpec, Condition as C, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)
    mode = seed % 3

    entities = {
        'lila': {'name': 'Lila', 'kind': 'child'},
        'tomas': {'name': 'Tomas', 'kind': 'child'},
        'moss': {'name': 'Moss', 'kind': 'donkey'},
        'juniper': {'name': 'Aunt Juniper', 'kind': 'guest'},
        'wagon': {'name': 'small wagon', 'kind': 'prop'},
        'basket': {'name': 'picnic basket', 'kind': 'prop'},
        'quilt': {'name': 'blue quilt', 'kind': 'prop'},
        'bell': {'name': 'brass bell', 'kind': 'prop'},
        'crown': {'name': 'paper crown', 'kind': 'prop'},
        'fizz': {'name': 'berry fizz', 'kind': 'prop'},
        'picnic': {'name': 'picnic', 'kind': 'event'},
    }

    if mode == 0:
        juniper_climb = True
        juniper_wish = 'hill'
        moss_role = 'guest'
        tomas_wish = 'hill'
        wagon_load = 2
        food_loaded = True
        decor_loaded = True
        bell_loc = 'top'
    elif mode == 1:
        juniper_climb = False
        juniper_wish = 'hill'
        moss_role = 'cart'
        tomas_wish = 'hill'
        wagon_load = 0
        food_loaded = False
        decor_loaded = False
        bell_loc = 'foot'
    else:
        juniper_climb = False
        juniper_wish = 'quiet'
        moss_role = 'guest'
        tomas_wish = 'hill'
        wagon_load = 0
        food_loaded = False
        decor_loaded = False
        bell_loc = 'foot'

    initial = {
        'lila.location': 'foot',
        'tomas.location': 'foot',
        'moss.location': 'foot',
        'juniper.location': 'foot',
        'juniper.can_climb': juniper_climb,
        'juniper.wish': juniper_wish,
        'juniper.invited': False,
        'juniper.delighted': False,
        'tomas.wish': tomas_wish,
        'moss.belief_role': moss_role,
        'moss.agreement': False,
        'moss.content': False,
        'moss.procession': False,
        'wagon.load': wagon_load,
        'wagon.food_loaded': food_loaded,
        'wagon.decor_loaded': decor_loaded,
        'wagon.location': 'foot',
        'basket.owner': 'lila',
        'quilt.owner': 'lila',
        'quilt.spread': False,
        'quilt.location': 'foot',
        'bell.owner': 'lila',
        'bell.location': bell_loc,
        'bell.rung': False,
        'bell.tied': False,
        'crown.owner': 'lila',
        'crown.location': 'foot',
        'crown.worn': False,
        'fizz.owner': 'lila',
        'fizz.shared': False,
        'picnic.location': 'wagon',
        'picnic.performed': False,

        'lila.knows.juniper.can_climb': None,
        'lila.knows.juniper.location': None,
        'lila.knows.juniper.wish': None,
        'lila.knows.moss.belief_role': None,
        'lila.knows.tomas.wish': None,
        'tomas.knows.juniper.can_climb': None,
        'tomas.knows.juniper.location': None,
        'tomas.knows.juniper.wish': None,
        'tomas.knows.moss.belief_role': None,
        'tomas.knows.tomas.wish': None,
        'moss.knows.juniper.can_climb': None,
        'moss.knows.juniper.location': None,
        'moss.knows.juniper.wish': None,
        'moss.knows.moss.belief_role': None,
        'juniper.knows.juniper.can_climb': None,
        'juniper.knows.juniper.location': None,
        'juniper.knows.juniper.wish': None,
        'juniper.knows.moss.belief_role': None,
    }

    scenes = (
        observe(
            'notice_juniper',
            'lila',
            'juniper.can_climb',
            requires=(C('lila.location', 'eq', 'foot'),),
            summary='Lila noticed whether Aunt Juniper could climb',
        ),
        observe(
            'notice_juniper_place',
            'lila',
            'juniper.location',
            requires=(C('lila.location', 'eq', 'foot'),),
            summary='Lila noticed where Aunt Juniper was waiting',
        ),
        observe(
            'notice_juniper_wish',
            'lila',
            'juniper.wish',
            requires=(C('lila.knows.juniper.location', 'eq', 'foot'),),
            summary='Lila learned what sort of picnic Juniper wanted',
        ),
        tell(
            'tell_tomas_climb',
            'lila',
            'tomas',
            'juniper.can_climb',
            when=(C('lila.knows.juniper.can_climb', 'ne', None),),
            summary='Lila told Tomas about the hill',
        ),
        tell(
            'correct_tomas_belief',
            'lila',
            'tomas',
            'juniper.location',
            when=(C('lila.knows.juniper.location', 'eq', 'foot'),),
            summary='Lila told Tomas that Juniper was below the hill',
            pivotal=True,
        ),
        tell(
            'tell_juniper_wish',
            'lila',
            'tomas',
            'juniper.wish',
            when=(C('lila.knows.juniper.wish', 'ne', None),),
            summary='Lila told Tomas Juniper’s picnic wish',
        ),
        observe(
            'ask_moss',
            'tomas',
            'moss.belief_role',
            requires=(C('tomas.location', 'eq', 'foot'),),
            summary='Tomas asked Moss what sort of helper he meant to be',
        ),
        tell(
            'tell_moss_role',
            'tomas',
            'lila',
            'moss.belief_role',
            when=(C('tomas.knows.moss.belief_role', 'ne', None),),
            summary='Tomas told Lila what Moss thought',
        ),
        scene(
            'load_food',
            'Load',
            ('lila',),
            when=(
                C('wagon.load', 'lt', 2),
                C('wagon.food_loaded', 'eq', False),
                C('basket.owner', 'eq', 'lila'),
            ),
            set_values={'wagon.food_loaded': True, 'picnic.location': 'wagon'},
            increments={'wagon.load': 1},
            summary='Lila loaded the picnic food',
        ),
        scene(
            'load_decor',
            'Load',
            ('tomas',),
            when=(
                C('wagon.load', 'lt', 2),
                C('wagon.decor_loaded', 'eq', False),
            ),
            set_values={'wagon.decor_loaded': True},
            increments={'wagon.load': 1},
            summary='Tomas loaded the decorations',
        ),
        scene(
            'invite_hilltop',
            'Welcome',
            ('lila', 'juniper'),
            when=(
                C('lila.knows.juniper.can_climb', 'eq', True),
                C('lila.knows.juniper.wish', 'eq', 'hill'),
                C('juniper.location', 'eq', 'foot'),
            ),
            set_values={'juniper.invited': True},
            summary='Lila invited Juniper to the hilltop',
        ),
        scene(
            'juniper_climb',
            'Welcome',
            ('juniper',),
            when=(
                C('juniper.invited', 'eq', True),
                C('juniper.can_climb', 'eq', True),
                C('juniper.location', 'eq', 'foot'),
            ),
            set_values={'juniper.location': 'top'},
            summary='Juniper climbed to the hilltop',
        ),
        transfer(
            'offer_crown_moss',
            'lila',
            'moss',
            'crown',
            when=(
                C('lila.knows.moss.belief_role', 'eq', 'cart'),
                C('moss.location', 'eq', 'foot'),
            ),
            summary='Lila offered Moss the paper crown',
        ),
        scene(
            'moss_agree',
            'Welcome',
            ('moss', 'lila'),
            when=(
                C('crown.owner', 'eq', 'moss'),
                C('moss.belief_role', 'eq', 'cart'),
                C('moss.agreement', 'eq', False),
            ),
            set_values={'moss.agreement': True, 'moss.content': True},
            summary='Moss agreed to pull one bundle proudly',
            pivotal=True,
        ),
        scene(
            'spread_quilt',
            'Welcome',
            ('lila',),
            when=(
                C('quilt.owner', 'eq', 'lila'),
                C('quilt.spread', 'eq', False),
                C('juniper.location', 'eq', 'foot'),
            ),
            set_values={'quilt.spread': True, 'quilt.location': 'foot'},
            summary='Lila spread the blue quilt below the hill',
        ),
        scene(
            'make_meadow_party',
            'Welcome',
            ('tomas', 'juniper'),
            when=(
                C('juniper.location', 'eq', 'foot'),
                C('juniper.wish', 'eq', 'quiet'),
                C('quilt.spread', 'eq', True),
                C('wagon.food_loaded', 'eq', True),
            ),
            set_values={'picnic.location': 'foot'},
            summary='The food became a quiet meadow picnic',
        ),
        scene(
            'crown_moss',
            'Performance',
            ('moss', 'tomas'),
            when=(
                C('crown.owner', 'eq', 'moss'),
                C('quilt.spread', 'eq', True),
                C('picnic.location', 'eq', 'foot'),
                C('moss.location', 'eq', 'foot'),
            ),
            set_values={
                'crown.worn': True,
                'picnic.performed': True,
            },
            summary='Moss wore the paper crown at the meadow party',
        ),
        scene(
            'ring_bell_for_guest',
            'Performance',
            ('tomas', 'juniper'),
            when=(
                C('juniper.location', 'eq', 'top'),
                C('bell.location', 'eq', 'top'),
                C('bell.owner', 'eq', 'lila'),
            ),
            set_values={
                'bell.rung': True,
                'picnic.location': 'top',
                'picnic.performed': True,
            },
            summary='Tomas rang the brass bell for Juniper',
        ),
        scene(
            'share_berry_fizz',
            'Sharing',
            ('lila', 'juniper'),
            when=(
                C('wagon.food_loaded', 'eq', True),
                C('picnic.performed', 'eq', True),
                C('fizz.owner', 'eq', 'lila'),
            ),
            set_values={
                'fizz.shared': True,
                'juniper.delighted': True,
            },
            summary='Lila shared the berry fizz',
        ),
        transfer(
            'tie_bell_to_moss',
            'lila',
            'moss',
            'bell',
            when=(
                C('moss.agreement', 'eq', True),
                C('bell.owner', 'eq', 'lila'),
                C('wagon.food_loaded', 'eq', True),
            ),
            summary='The bell was tied to Moss’s harness',
        ),
        scene(
            'moss_leads_procession',
            'Performance',
            ('moss', 'tomas', 'juniper'),
            when=(
                C('moss.agreement', 'eq', True),
                C('bell.owner', 'eq', 'moss'),
                C('juniper.location', 'eq', 'foot'),
                C('wagon.food_loaded', 'eq', True),
            ),
            set_values={
                'bell.tied': True,
                'moss.procession': True,
                'picnic.location': 'foot',
                'picnic.performed': True,
                'juniper.delighted': True,
            },
            summary='Moss led the one-bundle celebration to Juniper',
        ),
    )

    return WorldSpec(
        'The Picnic That Came to You',
        entities,
        initial,
        scenes,
        goal=(C('juniper.delighted', 'eq', True),),
        rules=(),
        labels={
            'juniper.location': 'Aunt Juniper’s place',
            'picnic.location': 'picnic place',
            'moss.content': 'Moss’s happiness',
            'picnic.performed': 'the celebration',
        },
        prune=True,
        premise_keys=(
            'wagon.load',
            'juniper.can_climb',
            'moss.belief_role',
            'tomas.wish',
        ),
        outcome_keys=(
            'picnic.location',
            'moss.content',
            'juniper.delighted',
            'picnic.performed',
        ),
    )

