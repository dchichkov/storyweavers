import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer

def build(seed):
    rng = random.Random(seed)

    entities = {
        'ada': {'name': 'Ada', 'kind': 'child'},
        'bo': {'name': 'Bo', 'kind': 'child'},
        'pip': {'name': 'Pip', 'kind': 'moth'},
        'gate': {'name': 'garden gate', 'kind': 'prop'},
        'lamp': {'name': 'hand lamp', 'kind': 'prop'},
        'moon': {'name': 'paper moon', 'kind': 'prop'},
        'bell': {'name': 'silver bell', 'kind': 'prop'},
        'flowers': {'name': 'moonflowers', 'kind': 'prop'},
        'ribbon': {'name': 'welcome ribbon', 'kind': 'prop'},
    }

    brightness = rng.choice(('bright', 'soft'))
    pip_location = rng.choice(('leaves', 'gate'))
    ada_plan = rng.choice(('moving', 'tableau'))
    bo_plan = rng.choice(('bell', 'flowers'))

    initial = {
        'ada.memes.Curiosity': 2,
        'bo.memes.Care': 2,
        'pip.location': pip_location,
        'pip.content': 'shy',
        'pip.invited': False,
        'gate.open': False,
        'lamp.brightness': brightness,
        'lamp.owner': 'ada',
        'moon.position': 'basket',
        'bell.rung': False,
        'flowers.ready': False,
        'ribbon.tied': False,
        'ada.plan': ada_plan,
        'bo.plan': bo_plan,
        'performed.mode': 'none',
        'ada.knows.pip.location': None,
        'bo.knows.pip.location': None,
        'ada.knows.lamp.brightness': None,
        'bo.knows.lamp.brightness': None,
    }

    scenes = (
        scene(
            'open_gate', 'Invitation', ('ada',),
            when=(C('gate.open', 'eq', False),),
            set_values={'gate.open': True, 'pip.invited': True},
            summary='Ada opened the gate and called a welcome into the dark garden',
        ),
        observe(
            'look_for_pip', 'ada', 'pip.location',
            requires=(C('gate.open', 'eq', True),),
            summary='Ada noticed where Pip was hiding',
        ),
        observe(
            'inspect_lamp', 'ada', 'lamp.brightness',
            requires=(
                C('gate.open', 'eq', True),
                C('lamp.owner', 'eq', 'ada'),
            ),
            summary='Ada checked the lamp glow',
        ),
        tell(
            'tell_pip_place', 'ada', 'bo', 'pip.location',
            when=(
                C('gate.open', 'eq', True),
                C('ada.knows.pip.location', 'ne', None),
            ),
            summary='Ada told Bo where Pip was hiding',
        ),
        tell(
            'tell_lamp', 'ada', 'bo', 'lamp.brightness',
            when=(
                C('gate.open', 'eq', True),
                C('ada.knows.lamp.brightness', 'ne', None),
            ),
            summary='Ada told Bo how bright the lamp was',
        ),
        transfer(
            'pass_lamp', 'ada', 'bo', 'lamp',
            when=(
                C('gate.open', 'eq', True),
                C('ada.knows.lamp.brightness', 'ne', None),
            ),
            summary='Ada passed the lamp to Bo',
        ),
        scene(
            'choose_still_tableau', 'Character Turn', ('ada',),
            when=(
                C('ada.plan', 'eq', 'moving'),
                C('ada.knows.pip.location', 'eq', 'leaves'),
            ),
            set_values={'ada.plan': 'tableau'},
            summary='Ada changed her grand show into a still moon tableau',
            pivotal=True,
        ),
        scene(
            'tie_welcome_ribbon', 'Preparation', ('bo',),
            when=(
                C('gate.open', 'eq', True),
                C('ribbon.tied', 'eq', False),
            ),
            set_values={'ribbon.tied': True},
            summary='Bo tied the welcome ribbon to the gate',
        ),
        scene(
            'place_paper_moon', 'Preparation', ('ada',),
            when=(
                C('gate.open', 'eq', True),
                C('moon.position', 'eq', 'basket'),
            ),
            set_values={'moon.position': 'gate'},
            summary='Ada hung the paper moon on the gate',
        ),
        scene(
            'ring_soft_bell', 'Invitation', ('bo',),
            when=(
                C('gate.open', 'eq', True),
                C('bo.plan', 'eq', 'bell'),
                C('bell.rung', 'eq', False),
            ),
            set_values={'bell.rung': True},
            summary='Bo rang one soft silver note',
        ),
        scene(
            'scent_moonflowers', 'Welcome', ('bo',),
            when=(
                C('gate.open', 'eq', True),
                C('bo.plan', 'eq', 'flowers'),
                C('flowers.ready', 'eq', False),
            ),
            set_values={'flowers.ready': True},
            summary='Bo brushed the moonflowers so their scent drifted out',
        ),
        scene(
            'soften_lamp_ada', 'Adjustment', ('ada',),
            when=(
                C('lamp.owner', 'eq', 'ada'),
                C('lamp.brightness', 'eq', 'bright'),
                C('ada.knows.lamp.brightness', 'eq', 'bright'),
            ),
            set_values={'lamp.brightness': 'soft'},
            summary='Ada shaded the lamp until its glow became soft',
        ),
        scene(
            'soften_lamp_bo', 'Adjustment', ('bo',),
            when=(
                C('lamp.owner', 'eq', 'bo'),
                C('lamp.brightness', 'eq', 'bright'),
                C('bo.knows.lamp.brightness', 'eq', 'bright'),
            ),
            set_values={'lamp.brightness': 'soft'},
            summary='Bo shaded the lamp until its glow became soft',
        ),
        scene(
            'perform_moving_shadows', 'Performance', ('ada',),
            when=(
                C('gate.open', 'eq', True),
                C('ada.plan', 'eq', 'moving'),
                C('lamp.brightness', 'eq', 'bright'),
                C('moon.position', 'eq', 'gate'),
            ),
            set_values={'performed.mode': 'shadows'},
            summary='Ada performed a sweeping shadow show',
        ),
        scene(
            'perform_still_tableau', 'Performance', ('ada',),
            when=(
                C('gate.open', 'eq', True),
                C('ada.plan', 'eq', 'tableau'),
                C('lamp.brightness', 'eq', 'soft'),
                C('moon.position', 'eq', 'gate'),
            ),
            set_values={'performed.mode': 'tableau'},
            summary='Ada performed a quiet paper-moon tableau',
        ),
        scene(
            'pip_lands_flowers', 'Guest Response', ('pip',),
            when=(
                C('pip.invited', 'eq', True),
                C('flowers.ready', 'eq', True),
                C('performed.mode', 'eq', 'none'),
            ),
            set_values={
                'pip.location': 'moonflowers',
                'pip.content': 'curious',
            },
            summary='Pip landed among the moonflowers',
        ),
        scene(
            'pip_follows_moon', 'Guest Response', ('pip',),
            when=(
                C('pip.invited', 'eq', True),
                C('performed.mode', 'eq', 'tableau'),
                C('ribbon.tied', 'eq', True),
                C('moon.position', 'eq', 'gate'),
            ),
            set_values={
                'pip.location': 'ribbon',
                'pip.content': 'welcomed',
            },
            summary='Pip followed the paper moon to the ribbon',
        ),
        scene(
            'pip_hides_bright_motion', 'Guest Response', ('pip',),
            when=(
                C('pip.invited', 'eq', True),
                C('performed.mode', 'eq', 'shadows'),
                C('lamp.brightness', 'eq', 'bright'),
            ),
            set_values={
                'pip.location': 'gate',
                'pip.content': 'startled',
            },
            summary='Pip fluttered behind the gate after the bright moving shadows',
        ),
    )

    return WorldSpec(
        'The Moonlit Welcome',
        entities,
        initial,
        scenes,
        goal=(C('pip.content', 'ne', 'shy'),),
        rules=(),
        labels={
            'lamp.brightness': 'the lamp glow',
            'pip.location': 'Pip’s hiding place',
            'ada.plan': 'Ada’s performance',
            'bo.plan': 'Bo’s welcome',
            'pip.content': 'Pip’s feeling',
            'performed.mode': 'the performance',
        },
        prune=True,
        premise_keys=(
            'lamp.brightness',
            'pip.location',
            'ada.plan',
            'bo.plan',
        ),
        outcome_keys=(
            'pip.location',
            'pip.content',
            'performed.mode',
        ),
    )
