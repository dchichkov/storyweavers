import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer

def build(seed):
    rng = random.Random(seed)
    mode = rng.randrange(4)

    entities = {
        'pip': {'name': 'Pip', 'kind': 'frog'},
        'mina': {'name': 'Mina', 'kind': 'child'},
        'jojo': {'name': 'Jojo', 'kind': 'child'},
        'nella': {'name': 'Nella', 'kind': 'snail'},
        'mic': {'name': 'floating pebble microphone', 'kind': 'prop'},
        'bells': {'name': 'reed-bell garland', 'kind': 'prop'},
        'prize': {'name': 'Golden Pebble', 'kind': 'prop'},
        'invite': {'name': 'paper invitation', 'kind': 'prop'},
        'chime': {'name': 'shell chime', 'kind': 'prop'},
        'stage': {'name': 'lily-pad stage', 'kind': 'place'},
        'shore': {'name': 'pond shore', 'kind': 'place'},
        'reeds': {'name': 'nearby reeds', 'kind': 'place'},
        'nook': {'name': 'reed nook', 'kind': 'place'},
    }

    mic_owner = 'jojo' if mode in (0, 2) else 'pip'
    bells_location = 'scattered' if mode == 1 else 'shore'
    invite_delivered = mode == 3
    belief = False
    chime_owner = 'nella' if mode in (0, 2, 3) else 'pip'
    nella_location = 'reeds' if mode in (0, 2) else 'nook'

    initial = {
        'pip.location': 'shore',
        'pip.style': 'booming' if mode == 2 else 'unset',
        'pip.performance.completed': False,
        'mina.location': 'shore',
        'mina.knows.nella.location': None,
        'mina.knows.nella.likes_music': None,
        'jojo.location': 'shore',
        'jojo.knows.nella.location': nella_location if mode == 3 else None,
        'jojo.knows.nella.likes_music': belief,
        'jojo.knows.chime.owner': 'prize' if mode == 3 else None,
        'nella.location': nella_location,
        'nella.likes_music': True,
        'nella.attended': False,
        'nella.response': None,
        'mic.location': 'shore',
        'mic.owner': mic_owner,
        'bells.location': bells_location,
        'bells.owner': 'mina',
        'prize.location': 'shore',
        'prize.owner': 'jojo',
        'invite.location': 'shore',
        'invite.delivered': invite_delivered,
        'chime.location': 'reeds',
        'chime.owner': chime_owner,
        'stage.location': 'pond',
        'shore.location': 'pond',
        'reeds.location': 'pond',
        'nook.location': 'reeds',
    }

    scenes = (
        observe(
            'observe_nella_nook', 'mina', 'nella.location',
            requires=(C('mina.knows.nella.location', 'eq', None),),
            summary='Mina noticed where Nella was listening'
        ),
        observe(
            'observe_nella_music', 'mina', 'nella.likes_music',
            requires=(
                C('mina.knows.nella.location', 'ne', None),
                C('mina.knows.nella.likes_music', 'eq', None),
            ),
            summary='Mina discovered that Nella liked music'
        ),
        tell(
            'tell_jojo_about_nella', 'mina', 'jojo', 'nella.likes_music',
            when=(C('mina.knows.nella.likes_music', 'eq', True),),
            summary='Mina told Jojo what she had discovered'
        ),
        scene(
            'deliver_invitation', 'Invitation', ('mina', 'nella'),
            when=(
                C('invite.delivered', 'eq', False),
                C('mina.knows.nella.location', 'ne', None),
                C('invite.location', 'eq', 'shore'),
            ),
            set_values={'invite.delivered': True, 'invite.location': 'reeds'},
            summary='Mina carried the invitation to Nella'
        ),
        scene(
            'find_scattered_bells', 'Preparation', ('mina', 'jojo'),
            when=(
                C('bells.location', 'eq', 'scattered'),
                C('mina.location', 'eq', 'shore'),
            ),
            set_values={'bells.location': 'shore'},
            summary='Mina and Jojo gathered the scattered reed bells'
        ),
        transfer(
            'lend_microphone', 'jojo', 'pip', 'mic',
            when=(
                C('jojo.location', 'eq', 'shore'),
                C('pip.location', 'eq', 'shore'),
                C('mic.owner', 'eq', 'jojo'),
            ),
            summary='Jojo lent the pebble microphone to Pip'
        ),
        scene(
            'place_bells', 'Preparation', ('mina',),
            when=(
                C('bells.location', 'eq', 'shore'),
                C('mina.location', 'eq', 'shore'),
            ),
            set_values={'bells.location': 'stage'},
            summary='Mina hung the reed bells around the lily-pad stage'
        ),
        scene(
            'promise_quiet_song', 'Character Turn', ('pip', 'jojo'),
            when=(
                C('jojo.knows.nella.likes_music', 'eq', True),
                C('pip.style', 'ne', 'quiet'),
            ),
            set_values={'pip.style': 'quiet'},
            summary='Pip promised a gentle song instead of a booming finale',
            pivotal=True
        ),
        scene(
            'promise_splash_song', 'Performance Plan', ('pip', 'jojo'),
            when=(
                C('jojo.knows.nella.likes_music', 'eq', False),
                C('nella.attended', 'eq', False),
                C('pip.style', 'ne', 'splash'),
            ),
            set_values={'pip.style': 'splash'},
            summary='Pip kept the splashy concert plan'
        ),
        scene(
            'trade_prize_for_chime', 'Trade', ('pip', 'nella'),
            when=(
                C('chime.owner', 'eq', 'nella'),
                C('prize.owner', 'eq', 'jojo'),
                C('nella.attended', 'eq', True),
            ),
            set_values={'chime.owner': 'pip', 'prize.owner': 'nella'},
            summary='Pip traded the Golden Pebble for Nella’s shell chime'
        ),
        scene(
            'welcome_nella', 'Welcome', ('nella', 'mina'),
            when=(
                C('invite.delivered', 'eq', True),
                C('nella.attended', 'eq', False),
            ),
            set_values={'nella.attended': True, 'nella.location': 'stage'},
            summary='Nella came to the lily-pad stage',
            pivotal=True
        ),
        scene(
            'perform_quiet_concert', 'Performance', ('pip', 'mina', 'jojo', 'nella'),
            when=(
                C('pip.style', 'eq', 'quiet'),
                C('mic.owner', 'eq', 'pip'),
                C('bells.location', 'eq', 'stage'),
                C('nella.attended', 'eq', True),
                C('chime.owner', 'eq', 'pip'),
            ),
            set_values={
                'pip.performance.completed': True,
                'nella.response': 'delighted',
            },
            summary='Pip performed a quiet concert with Nella’s shell chime'
        ),
        scene(
            'perform_splash_concert', 'Performance', ('pip', 'mina', 'jojo'),
            when=(
                C('pip.style', 'eq', 'splash'),
                C('mic.owner', 'eq', 'pip'),
                C('bells.location', 'eq', 'stage'),
                C('nella.attended', 'eq', False),
            ),
            set_values={
                'pip.performance.completed': True,
                'nella.response': 'pond_cheer',
                'prize.owner': 'jojo',
            },
            summary='Pip performed a booming splash concert for the pond crowd'
        ),
        scene(
            'perform_private_concert', 'Performance', ('pip', 'mina', 'jojo'),
            when=(
                C('pip.style', 'eq', 'quiet'),
                C('mic.owner', 'eq', 'pip'),
                C('bells.location', 'eq', 'stage'),
                C('nella.attended', 'eq', False),
                C('nella.location', 'eq', 'reeds'),
            ),
            set_values={
                'pip.performance.completed': True,
                'nella.response': 'private_warmth',
            },
            summary='Pip performed a quiet concert for the hidden listener'
        ),
    )

    return WorldSpec(
        'The Pond Concert and the Listener in the Reeds',
        entities,
        initial,
        scenes,
        goal=(
            C('pip.performance.completed', 'eq', True),
            C('nella.response', 'ne', None),
        ),
        rules=(),
        labels={
            'pip.style': 'concert style',
            'nella.response': 'Nella’s response',
            'prize.owner': 'Golden Pebble owner',
            'nella.attended': 'Nella attending',
            'pip.performance.completed': 'concert completed',
        },
        prune=True,
        premise_keys=(
            'mic.owner',
            'bells.location',
            'invite.delivered',
            'jojo.knows.nella.likes_music',
            'chime.owner',
        ),
        outcome_keys=(
            'pip.style',
            'nella.response',
            'prize.owner',
        ),
    )
