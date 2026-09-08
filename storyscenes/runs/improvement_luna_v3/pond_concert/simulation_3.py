import random
from runtime import WorldSpec, Condition as C, scene, observe, tell, transfer

def build(seed):
    rng = random.Random(seed)
    mode = rng.randrange(3)

    entities = {
        'frog': {'name': 'Frog', 'kind': 'animal'},
        'mia': {'name': 'Mia', 'kind': 'child'},
        'teo': {'name': 'Teo', 'kind': 'child'},
        'nora': {'name': 'Nora', 'kind': 'neighbor'},
        'lily': {'name': 'floating lily', 'kind': 'prop'},
        'bell': {'name': 'silver bell', 'kind': 'prop'},
        'reed': {'name': 'reed flute', 'kind': 'prop'},
        'boat': {'name': 'leaf boat', 'kind': 'prop'},
        'invitation': {'name': 'pond invitation', 'kind': 'prop'},
        'concert': {'name': 'pond concert', 'kind': 'prop'},
    }

    initial = {
        'frog.belief': 'loud' if mode == 0 else 'unknown',
        'frog.knows.nora.want': None,
        'frog.performed': False,
        'mia.want': 'dance' if mode == 1 else 'concert',
        'mia.knows.nora.want': None,
        'teo.want': 'lullaby' if mode == 1 else 'concert',
        'teo.knows.nora.want': None,
        'nora.want': 'quiet' if mode == 0 else 'lullaby' if mode == 1 else 'join',
        'nora.content': False,
        'nora.response': 'none',
        'lily.owner': 'nora' if mode == 2 else 'frog',
        'bell.owner': 'mia',
        'reed.owner': 'teo',
        'boat.owner': 'nora',
        'invitation.sent': False,
        'concert.style': 'none',
    }

    scenes = (
        observe(
            'notice_nora',
            'frog',
            'nora.want',
            requires=(C('frog.knows.nora.want', 'eq', None),),
            summary='Frog watched Nora beside the pond',
        ),
        tell(
            'tell_mia',
            'frog',
            'mia',
            'nora.want',
            when=(C('frog.knows.nora.want', 'ne', None),),
            summary='Frog told Mia what Nora wanted',
        ),
        tell(
            'tell_teo',
            'frog',
            'teo',
            'nora.want',
            when=(C('frog.knows.nora.want', 'ne', None),),
            summary='Frog told Teo what Nora wanted',
        ),
        scene(
            'choose_soft',
            'Choice',
            ('frog', 'teo'),
            when=(
                C('frog.knows.nora.want', 'eq', 'quiet'),
                C('teo.knows.nora.want', 'eq', 'quiet'),
                C('nora.want', 'eq', 'quiet'),
            ),
            set_values={'concert.style': 'soft'},
            summary='They chose a hush-soft concert',
            pivotal=True,
        ),
        scene(
            'choose_duet',
            'Choice',
            ('mia', 'teo'),
            when=(
                C('mia.want', 'eq', 'dance'),
                C('teo.want', 'eq', 'lullaby'),
                C('mia.knows.nora.want', 'eq', 'lullaby'),
                C('teo.knows.nora.want', 'eq', 'lullaby'),
                C('nora.want', 'eq', 'lullaby'),
            ),
            set_values={'concert.style': 'duet'},
            summary='They chose a dancing lullaby',
            pivotal=True,
        ),
        scene(
            'invite_nora',
            'Invitation',
            ('mia', 'nora'),
            when=(
                C('mia.knows.nora.want', 'eq', 'join'),
                C('nora.want', 'eq', 'join'),
                C('lily.owner', 'eq', 'nora'),
            ),
            set_values={'invitation.sent': True},
            summary='Mia invited Nora onto the water',
        ),
        transfer(
            'lend_lily',
            'nora',
            'frog',
            'lily',
            when=(C('invitation.sent', 'eq', True),),
            summary='Nora lent over the floating lily',
        ),
        scene(
            'choose_boat',
            'Choice',
            ('frog', 'mia', 'teo'),
            when=(
                C('teo.knows.nora.want', 'eq', 'join'),
                C('nora.want', 'eq', 'join'),
                C('lily.owner', 'eq', 'frog'),
            ),
            set_values={'concert.style': 'boat'},
            summary='They chose a floating boat concert',
            pivotal=True,
        ),
        transfer(
            'trade_bell',
            'mia',
            'teo',
            'bell',
            when=(C('concert.style', 'eq', 'duet'),),
            summary='Mia handed Teo the silver bell',
        ),
        scene(
            'perform_soft',
            'Performance',
            ('frog', 'teo'),
            when=(C('concert.style', 'eq', 'soft'), C('teo.knows.nora.want', 'eq', 'quiet')),
            set_values={'frog.performed': True, 'nora.content': True},
            summary='Frog performed a soft pond song',
        ),
        scene(
            'perform_duet',
            'Performance',
            ('frog', 'mia', 'teo'),
            when=(
                C('concert.style', 'eq', 'duet'),
                C('bell.owner', 'eq', 'teo'),
            ),
            set_values={'frog.performed': True, 'nora.content': True},
            summary='Frog performed a dancing lullaby',
        ),
        scene(
            'perform_boat',
            'Performance',
            ('frog', 'mia', 'teo', 'nora'),
            when=(
                C('concert.style', 'eq', 'boat'),
                C('lily.owner', 'eq', 'frog'),
            ),
            set_values={'frog.performed': True, 'nora.content': True},
            summary='Frog performed from the floating lily',
        ),
        scene(
            'quiet_bow',
            'Ending',
            ('frog',),
            when=(
                C('concert.style', 'eq', 'soft'),
                C('frog.performed', 'eq', True),
            ),
            set_values={'nora.response': 'bubble'},
            summary='Nora answered with one round silver bubble',
        ),
        scene(
            'duet_bow',
            'Ending',
            ('frog',),
            when=(
                C('concert.style', 'eq', 'duet'),
                C('frog.performed', 'eq', True),
            ),
            set_values={'nora.response': 'ripples'},
            summary='Nora tapped the water in time',
        ),
        scene(
            'boat_bow',
            'Ending',
            ('frog',),
            when=(
                C('concert.style', 'eq', 'boat'),
                C('frog.performed', 'eq', True),
            ),
            set_values={'nora.response': 'parade'},
            summary='Nora sailed the lily in a slow circle',
        ),
    )

    return WorldSpec(
        'The Pond Concert and the Neighbor with the Quietest Ears',
        entities,
        initial,
        scenes,
        goal=(
            C('frog.performed', 'eq', True),
            C('nora.content', 'eq', True),
        ),
        rules=(),
        labels={
            'concert.style': 'concert style',
            'nora.want': "Nora's wish",
            'nora.response': "Nora's response",
        },
        prune=True,
        premise_keys=(
            'frog.belief',
            'mia.want',
            'lily.owner',
            'nora.want',
        ),
        outcome_keys=(
            'concert.style',
            'frog.performed',
            'nora.response',
            'lily.owner',
        ),
    )
