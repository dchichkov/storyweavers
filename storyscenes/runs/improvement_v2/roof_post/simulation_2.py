import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)

    entities = {
        'ada': {'name': 'Ada', 'kind': 'child'},
        'pip': {'name': 'Pip', 'kind': 'young dragon'},
        'jun': {'name': 'Jun', 'kind': 'neighbor'},
        'post': {'name': 'roof post', 'kind': 'place'},
        'basket': {'name': 'wicker basket', 'kind': 'prop'},
        'invites': {'name': 'three invitations', 'kind': 'prop'},
        'ribbon': {'name': 'blue ribbon', 'kind': 'prop'},
        'lantern': {'name': 'paper lantern', 'kind': 'prop'},
        'bell': {'name': 'tiny brass bell', 'kind': 'prop'},
        'garden': {'name': 'roof garden', 'kind': 'place'},
    }

    pinned = rng.choice((False, True))
    lantern_cargo = rng.choice((False, True))
    flight_belief = rng.choice((False, True))

    initial = {
        'ada.memes.Curiosity': 2,
        'ada.want': 'neat',
        'ada.knows.ada.want': 'neat',
        'ada.knows.post.invites_pinned': None,
        'ada.knows.basket.contains_lantern': None,
        'ada.knows.pip.believes_flight': None,
        'pip.want': 'help',
        'pip.belief': 'quiet',
        'pip.believes_flight': flight_belief,
        'pip.knows.ada.want': None,
        'pip.performance_agreed': False,
        'pip.performance': 'none',
        'post.invites_pinned': pinned,
        'post.ribboned': False,
        'basket.contains_lantern': lantern_cargo,
        'basket.safe': True,
        'basket.owner': 'ada',
        'invites.location': 'post' if pinned else 'table',
        'invites.delivered': False,
        'invites.route': 'unknown',
        'invites.owner': 'ada',
        'ribbon.owner': 'ada',
        'ribbon.used': False,
        'lantern.lit': False,
        'bell.rung': False,
        'garden.party_ready': False,
        'garden.decorated': False,
        'jun.invited': False,
        'jun.knows.invites.delivered': None,
    }

    scenes = (
        observe(
            'observe_pin', 'ada', 'post.invites_pinned',
            requires=(C('ada.memes.Curiosity', 'ge', 1),),
            summary='Ada saw whether the wind had pinned the invitations to the roof post.',
        ),
        observe(
            'observe_cargo', 'ada', 'basket.contains_lantern',
            requires=(C('basket.owner', 'eq', 'ada'),),
            summary='Ada peeked into the basket and checked for the paper lantern.',
        ),
        observe(
            'observe_belief', 'ada', 'pip.believes_flight',
            requires=(C('pip.want', 'eq', 'help'),),
            summary='Ada noticed that Pip was expecting a grand flying delivery.',
        ),
        tell(
            'tell_plan', 'ada', 'pip', 'ada.want',
            requires=(C('ada.want', 'eq', 'neat'),),
            summary='Ada told Pip that she wanted the invitations delivered neatly.',
        ),
        transfer(
            'transfer_ribbon', 'ada', 'pip', 'ribbon',
            requires=(C('ribbon.owner', 'eq', 'ada'),),
            summary='Ada handed Pip the blue ribbon.',
        ),
        scene(
            'tie_ribbon', 'Tie', ('pip',),
            when=(
                C('ribbon.owner', 'eq', 'pip'),
                C('ada.knows.post.invites_pinned', 'eq', True),
                C('post.invites_pinned', 'eq', True),
                C('basket.contains_lantern', 'eq', False),
                C('pip.believes_flight', 'eq', False),
            ),
            set_values={'post.ribboned': True, 'ribbon.used': True},
            summary='Pip tied the blue ribbon around the wind-pinned invitations.',
        ),
        scene(
            'pin_invites', 'Secure', ('ada',),
            when=(
                C('ada.knows.post.invites_pinned', 'eq', True),
                C('post.invites_pinned', 'eq', True),
                C('post.ribboned', 'eq', True),
                C('basket.contains_lantern', 'eq', False),
                C('pip.believes_flight', 'eq', False),
            ),
            set_values={
                'invites.location': 'post',
                'invites.route': 'post',
                'invites.delivered': True,
            },
            summary='Ada made the ribboned roof-post delivery ready for Jun.',
        ),
        scene(
            'lift_basket', 'Carry', ('pip',),
            when=(
                C('basket.owner', 'eq', 'ada'),
                C('ada.knows.basket.contains_lantern', 'eq', False),
                C('basket.contains_lantern', 'eq', False),
                C('pip.believes_flight', 'eq', False),
            ),
            set_values={'basket.owner': 'pip'},
            summary='Pip lifted the empty basket with extremely serious dragon toes.',
        ),
        scene(
            'set_down_basket', 'SetDown', ('pip',),
            when=(C('basket.owner', 'eq', 'pip'),),
            set_values={'basket.owner': 'ada'},
            summary='Pip set the basket down beside the moonmelon trellis.',
        ),
        scene(
            'carry_plain', 'Carry', ('ada',),
            when=(
                C('ada.knows.post.invites_pinned', 'eq', False),
                C('ada.knows.basket.contains_lantern', 'eq', False),
                C('ada.knows.pip.believes_flight', 'eq', False),
                C('post.invites_pinned', 'eq', False),
                C('basket.contains_lantern', 'eq', False),
                C('pip.believes_flight', 'eq', False),
            ),
            set_values={
                'invites.location': 'trellis',
                'invites.route': 'walk',
                'invites.delivered': True,
            },
            summary='Ada carried the plain invitations along the quiet roof-garden path.',
        ),
        scene(
            'carry_to_trellis', 'Carry', ('ada',),
            when=(
                C('ada.knows.basket.contains_lantern', 'eq', True),
                C('basket.contains_lantern', 'eq', True),
                C('basket.owner', 'eq', 'ada'),
                C('basket.safe', 'eq', True),
                C('pip.believes_flight', 'eq', False),
            ),
            set_values={
                'invites.location': 'trellis',
                'invites.route': 'lantern',
                'invites.delivered': True,
            },
            summary='Ada carried the invitations carefully beneath the moonmelon trellis.',
        ),
        scene(
            'light_lantern', 'Light', ('ada',),
            when=(
                C('invites.route', 'eq', 'lantern'),
                C('basket.contains_lantern', 'eq', True),
            ),
            set_values={'lantern.lit': True, 'garden.decorated': True},
            summary='Ada lit the paper lantern beside the delivered invitations.',
        ),
        scene(
            'tell_pip_quiet', 'Talk', ('ada', 'pip'),
            when=(
                C('ada.knows.pip.believes_flight', 'eq', True),
                C('pip.believes_flight', 'eq', True),
                C('pip.knows.ada.want', 'eq', 'neat'),
            ),
            set_values={'pip.belief': 'neat'},
            summary='Ada explained that neat could still have one small flourish.',
        ),
        scene(
            'agree_flight', 'Turn', ('ada', 'pip'),
            when=(
                C('ada.knows.pip.believes_flight', 'eq', True),
                C('pip.believes_flight', 'eq', True),
                C('pip.knows.ada.want', 'eq', 'neat'),
                C('pip.belief', 'eq', 'neat'),
            ),
            set_values={
                'pip.performance_agreed': True,
                'pip.performance': 'airmail',
            },
            pivotal=True,
            summary='Ada and Pip agreed on a tiny, tidy air-mail performance.',
        ),
        scene(
            'flap_delivery', 'Fly', ('pip',),
            when=(
                C('pip.performance_agreed', 'eq', True),
                C('pip.performance', 'eq', 'airmail'),
                C('ribbon.owner', 'eq', 'pip'),
                C('invites.owner', 'eq', 'ada'),
            ),
            set_values={
                'invites.location': 'trellis',
                'invites.route': 'flight',
                'invites.delivered': True,
                'ribbon.used': True,
                'garden.decorated': True,
            },
            summary='Pip floated the invitations down on a blue-ribbon air-mail loop.',
        ),
        scene(
            'return_ribbon', 'Share', ('pip',),
            when=(
                C('ribbon.owner', 'eq', 'pip'),
                C('invites.delivered', 'eq', True),
            ),
            set_values={'ribbon.owner': 'ada'},
            summary='Pip returned the ribbon after the delivery was finished.',
        ),
        scene(
            'jun_accepts', 'Welcome', ('jun',),
            when=(
                C('invites.delivered', 'eq', True),
                C('invites.location', 'in', ('post', 'trellis')),
            ),
            set_values={'jun.invited': True},
            pivotal=True,
            summary='Jun accepted an invitation and climbed up to the roof garden.',
        ),
        observe(
            'jun_sees_delivery', 'jun', 'invites.delivered',
            requires=(
                C('jun.invited', 'eq', True),
                C('invites.delivered', 'eq', True),
            ),
            summary='Jun saw that the invitations had truly arrived.',
        ),
        scene(
            'ring_bell', 'Finish', ('ada',),
            when=(
                C('jun.invited', 'eq', True),
                C('jun.knows.invites.delivered', 'eq', True),
            ),
            set_values={'bell.rung': True, 'garden.party_ready': True},
            summary='Ada rang the tiny brass bell for the moonmelon party.',
        ),
    )

    rules = (
        Rule(
            'party_has_guest',
            must=(C('jun.invited', 'eq', True),),
            when=(C('garden.party_ready', 'eq', True),),
        ),
        Rule(
            'bell_marks_party',
            must=(C('bell.rung', 'eq', True),),
            when=(C('garden.party_ready', 'eq', True),),
        ),
    )

    return WorldSpec(
        'The Roof-Post Invitation Flight',
        entities,
        initial,
        scenes,
        goal=(C('garden.party_ready', 'eq', True),),
        rules=rules,
        labels={
            'invites.route': 'the invitation delivery route',
            'basket.safe': 'the basket stayed safe',
            'pip.performance': 'Pip’s performance',
            'garden.decorated': 'the roof garden decorations',
        },
        prune=True,
        premise_keys=(
            'post.invites_pinned',
            'basket.contains_lantern',
            'pip.believes_flight',
        ),
        outcome_keys=(
            'invites.route',
            'garden.decorated',
            'pip.performance_agreed',
        ),
    )
