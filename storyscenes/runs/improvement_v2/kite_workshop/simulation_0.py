import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)
    family = rng.randrange(3)

    if family == 0:
        label = 'Grandma'
        mina_belief = 'Pip'
        pip_job = 'quiet_delivery'
        tavi_belief = 'ordinary_note'
        scraps_owner = 'mina'
    elif family == 1:
        label = 'garden_birds'
        mina_belief = 'garden_birds'
        pip_job = 'quiet_delivery'
        tavi_belief = 'birthday_secret'
        scraps_owner = 'mina'
    else:
        label = 'cloud_dragon'
        mina_belief = 'cloud_dragon'
        pip_job = 'perform_aloud'
        tavi_belief = 'ordinary_note'
        scraps_owner = 'pip'

    entities = {
        'mina': {'name': 'Mina', 'kind': 'child'},
        'pip': {'name': 'Pip', 'kind': 'young dragon'},
        'tavi': {'name': 'Tavi', 'kind': 'child'},
        'kite': {'name': 'paper kite', 'kind': 'prop'},
        'spool': {'name': 'spool of string', 'kind': 'prop'},
        'scraps': {'name': 'bright paper scraps', 'kind': 'prop'},
        'tube': {'name': 'wooden message tube', 'kind': 'prop'},
        'bell': {'name': 'brass wind-bell', 'kind': 'prop'},
        'table': {'name': 'rooftop worktable', 'kind': 'setting'},
    }

    initial = {
        'mina.place': 'roof',
        'pip.place': 'roof',
        'tavi.place': 'roof',
        'kite.place': 'roof',
        'spool.place': 'roof',
        'scraps.place': 'roof',
        'tube.place': 'table',
        'bell.place': 'table',
        'table.place': 'roof',

        'mina.beliefs.recipient': mina_belief,
        'pip.beliefs.job': pip_job,
        'tavi.beliefs.message': tavi_belief,

        'mina.knows.tube.label': None,
        'pip.knows.tube.label': None,
        'tavi.knows.tube.label': label if rng.choice((True, False)) else None,
        'pip.knows.kite.owner': rng.choice((True, False)),

        'mina.wants': 'smooth_flight',
        'pip.wants': 'dragon_flourish',
        'tavi.wants': 'included_surprise',

        'kite.owner': 'mina',
        'spool.owner': 'mina',
        'scraps.owner': scraps_owner,
        'tube.owner': 'mina',
        'bell.owner': 'mina',

        'tube.label': label,
        'tube.delivered_to': None,
        'tube.open': False,

        'scraps.color': rng.choice(('blue', 'gold', 'red')),
        'bell.tone': rng.choice(('bright', 'low')),

        'kite.tail': False,
        'kite.fin': False,
        'kite.bell': False,
        'kite.flight_style': None,
        'kite.launched': False,
        'kite.response': False,

        'pip.agreement': None,
        'tavi.trust': False,
        'tavi.surprise_spoken': False,
    }

    scenes = (
        observe(
            'read_label', 'mina', 'tube.label',
            requires=(
                C('mina.place', 'eq', 'roof'),
                C('tube.place', 'eq', 'table'),
                C('tube.owner', 'eq', 'mina'),
                C('tube.open', 'eq', False),
            ),
            summary='Mina opened the wooden tube and read its label',
        ),

        tell(
            'tell_pip_label', 'mina', 'pip', 'tube.label',
            requires=(
                C('mina.place', 'eq', 'roof'),
                C('pip.place', 'eq', 'roof'),
                C('mina.knows.tube.label', 'ne', None),
            ),
            summary='Mina told Pip what the tube label said',
        ),

        tell(
            'tell_tavi_label', 'mina', 'tavi', 'tube.label',
            requires=(
                C('mina.place', 'eq', 'roof'),
                C('tavi.place', 'eq', 'roof'),
                C('mina.knows.tube.label', 'ne', None),
                C('tavi.beliefs.message', 'eq', 'birthday_secret'),
            ),
            summary='Mina told Tavi the real name on the message tube',
        ),

        scene(
            'tavi_blurts_secret', 'Belief', ('tavi',),
            when=(
                C('tavi.place', 'eq', 'roof'),
                C('tube.label', 'eq', 'garden_birds'),
                C('tavi.beliefs.message', 'eq', 'birthday_secret'),
                C('tavi.surprise_spoken', 'eq', False),
            ),
            set_values={'tavi.surprise_spoken': True},
            summary='Tavi announced that the supposed birthday secret needed a grand audience',
        ),

        scene(
            'tavi_learns_truth', 'Turn', ('mina', 'tavi'),
            when=(
                C('tube.label', 'eq', 'garden_birds'),
                C('tavi.surprise_spoken', 'eq', True),
                C('tavi.knows.tube.label', 'eq', 'garden_birds'),
                C('tavi.trust', 'eq', False),
            ),
            set_values={'tavi.trust': True},
            summary='Tavi learned that the message belonged to the garden birds',
            pivotal=True,
        ),

        transfer(
            'give_tube_pip', 'mina', 'pip', 'tube',
            requires=(
                C('mina.place', 'eq', 'roof'),
                C('pip.place', 'eq', 'roof'),
                C('tube.owner', 'eq', 'mina'),
                C('pip.knows.tube.label', 'ne', None),
            ),
            summary='Mina placed the message tube in Pip’s careful claws',
        ),

        transfer(
            'give_tube_tavi', 'mina', 'tavi', 'tube',
            requires=(
                C('mina.place', 'eq', 'roof'),
                C('tavi.place', 'eq', 'roof'),
                C('tube.owner', 'eq', 'mina'),
                C('tube.label', 'eq', 'garden_birds'),
                C('tavi.trust', 'eq', True),
            ),
            summary='Mina trusted Tavi with the tube for the garden birds',
        ),

        transfer(
            'give_bell_tavi', 'mina', 'tavi', 'bell',
            requires=(
                C('mina.place', 'eq', 'roof'),
                C('tavi.place', 'eq', 'roof'),
                C('bell.owner', 'eq', 'mina'),
                C('tube.label', 'eq', 'garden_birds'),
                C('tavi.trust', 'eq', True),
            ),
            summary='Mina handed Tavi the little brass wind-bell',
        ),

        scene(
            'tie_bell', 'Making', ('tavi',),
            when=(
                C('tavi.place', 'eq', 'roof'),
                C('bell.owner', 'eq', 'tavi'),
                C('kite.place', 'eq', 'roof'),
                C('kite.bell', 'eq', False),
                C('tube.label', 'eq', 'garden_birds'),
            ),
            set_values={'kite.bell': True},
            summary='Tavi tied the bell beneath the kite’s paper nose',
        ),

        scene(
            'attach_tail', 'Making', ('mina',),
            when=(
                C('mina.place', 'eq', 'roof'),
                C('kite.owner', 'eq', 'mina'),
                C('scraps.owner', 'eq', 'mina'),
                C('kite.tail', 'eq', False),
                C('mina.knows.tube.label', 'ne', None),
            ),
            set_values={'kite.tail': True},
            summary='Mina fastened a bright paper tail to steady the kite',
        ),

        scene(
            'attach_dragon_fin', 'Making', ('pip',),
            when=(
                C('pip.place', 'eq', 'roof'),
                C('scraps.owner', 'eq', 'pip'),
                C('pip.knows.tube.label', 'eq', 'cloud_dragon'),
                C('pip.wants', 'eq', 'dragon_flourish'),
                C('kite.fin', 'eq', False),
            ),
            set_values={'kite.fin': True},
            summary='Pip clipped a proud dragon fin along the kite before Mina could object',
        ),

        scene(
            'quiet_agreement', 'Turn', ('pip',),
            when=(
                C('tube.label', 'eq', 'Grandma'),
                C('pip.knows.tube.label', 'eq', 'Grandma'),
                C('pip.beliefs.job', 'eq', 'quiet_delivery'),
                C('pip.agreement', 'eq', None),
            ),
            set_values={'pip.agreement': 'quiet_helper'},
            summary='Pip decided that a soft, steady flight could still be splendid',
            pivotal=True,
        ),

        scene(
            'dragon_agreement', 'Performance', ('mina', 'pip'),
            when=(
                C('tube.label', 'eq', 'cloud_dragon'),
                C('kite.fin', 'eq', True),
                C('pip.knows.tube.label', 'eq', 'cloud_dragon'),
                C('pip.agreement', 'eq', None),
            ),
            set_values={'pip.agreement': 'performer'},
            summary='Mina gave Pip one careful nod: the dragon flourish could be the message',
        ),

        scene(
            'test_smooth', 'Test', ('mina', 'pip'),
            when=(
                C('tube.label', 'eq', 'Grandma'),
                C('kite.tail', 'eq', True),
                C('tube.owner', 'eq', 'pip'),
                C('pip.agreement', 'eq', 'quiet_helper'),
                C('kite.flight_style', 'eq', None),
            ),
            set_values={'kite.flight_style': 'smooth'},
            summary='The kite rose in a calm little arc above the worktable',
        ),

        scene(
            'test_bird_signal', 'Test', ('mina', 'tavi'),
            when=(
                C('tube.label', 'eq', 'garden_birds'),
                C('kite.tail', 'eq', True),
                C('kite.bell', 'eq', True),
                C('tube.owner', 'eq', 'tavi'),
                C('tavi.trust', 'eq', True),
                C('kite.flight_style', 'eq', None),
            ),
            set_values={'kite.flight_style': 'ringing_signal'},
            summary='The kite lifted, and its small bell chimed toward the garden',
        ),

        scene(
            'test_dragon_dance', 'Test', ('mina', 'pip'),
            when=(
                C('tube.label', 'eq', 'cloud_dragon'),
                C('kite.fin', 'eq', True),
                C('tube.owner', 'eq', 'pip'),
                C('pip.agreement', 'eq', 'performer'),
                C('kite.flight_style', 'eq', None),
            ),
            set_values={'kite.flight_style': 'dragon_dance'},
            summary='The fin caught the breeze and sent the kite swooping in a dragon loop',
        ),

        scene(
            'smoke_puff', 'Performance', ('pip',),
            when=(
                C('pip.place', 'eq', 'roof'),
                C('kite.flight_style', 'eq', 'dragon_dance'),
                C('pip.agreement', 'eq', 'performer'),
            ),
            set_values={'pip.wants': 'dragon_message_ready'},
            summary='Pip puffed one neat smoke-ring, shaped exactly like a surprised dragon',
        ),

        scene(
            'launch_kite', 'Launch', ('mina',),
            when=(
                C('mina.place', 'eq', 'roof'),
                C('kite.owner', 'eq', 'mina'),
                C('spool.owner', 'eq', 'mina'),
                C('kite.flight_style', 'ne', None),
                C('kite.launched', 'eq', False),
            ),
            set_values={'kite.launched': True},
            summary='Mina ran three steps and let the kite climb into the sunny air',
        ),

        scene(
            'grandma_response', 'Response', ('mina', 'pip'),
            when=(
                C('kite.launched', 'eq', True),
                C('tube.label', 'eq', 'Grandma'),
                C('kite.flight_style', 'eq', 'smooth'),
                C('tube.owner', 'eq', 'pip'),
                C('tube.delivered_to', 'eq', None),
            ),
            set_values={'tube.delivered_to': 'Grandma', 'kite.response': True},
            summary='The smooth kite carried the tube down to Grandma',
        ),

        scene(
            'bird_response', 'Response', ('tavi',),
            when=(
                C('kite.launched', 'eq', True),
                C('tube.label', 'eq', 'garden_birds'),
                C('kite.flight_style', 'eq', 'ringing_signal'),
                C('tube.owner', 'eq', 'tavi'),
                C('tube.delivered_to', 'eq', None),
            ),
            set_values={'tube.delivered_to': 'garden_birds', 'kite.response': True},
            summary='The ringing kite delivered its hello to the garden birds',
        ),

        scene(
            'cloud_dragon_response', 'Response', ('pip',),
            when=(
                C('kite.launched', 'eq', True),
                C('tube.label', 'eq', 'cloud_dragon'),
                C('kite.flight_style', 'eq', 'dragon_dance'),
                C('tube.owner', 'eq', 'pip'),
                C('pip.wants', 'eq', 'dragon_message_ready'),
                C('tube.delivered_to', 'eq', None),
            ),
            set_values={'tube.delivered_to': 'cloud_dragon', 'kite.response': True},
            summary='The looping kite sent its message beneath Pip’s tiny dragon shadow',
        ),
    )

    rules = (
        Rule(
            'a delivered message followed a launch',
            must=(C('kite.launched', 'eq', True),),
            when=(C('tube.delivered_to', 'ne', None),),
        ),
        Rule(
            'a response belongs to a delivered message',
            must=(C('tube.delivered_to', 'ne', None),),
            when=(C('kite.response', 'eq', True),),
        ),
    )

    return WorldSpec(
        'The Kite That Carried Three Kinds of Hello',
        entities,
        initial,
        scenes,
        goal=(
            C('kite.launched', 'eq', True),
            C('kite.response', 'eq', True),
        ),
        rules=rules,
        labels={
            'tube.label': 'the name on the message tube',
            'scraps.color': 'the color of the paper scraps',
            'bell.tone': 'the wind-bell’s note',
            'kite.flight_style': 'the kite’s way of flying',
        },
        prune=True,
        premise_keys=(
            'tube.label',
            'mina.beliefs.recipient',
            'pip.beliefs.job',
            'scraps.color',
        ),
        outcome_keys=(
            'tube.delivered_to',
            'kite.flight_style',
            'pip.agreement',
        ),
    )
