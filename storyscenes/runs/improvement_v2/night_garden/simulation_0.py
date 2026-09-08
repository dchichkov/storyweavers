import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)

    entities = {
        'mira': {'name': 'Mira', 'kind': 'child'},
        'sol': {'name': 'Sol', 'kind': 'child'},
        'luma': {'name': 'Luma', 'kind': 'moth'},
        'lamp': {'name': 'the lantern lamp', 'kind': 'prop'},
        'screen': {'name': 'the paper shadow-screen', 'kind': 'prop'},
        'ribbon': {'name': 'the blue ribbon', 'kind': 'prop'},
        'flowers': {'name': 'the bowl of moonflowers', 'kind': 'prop'},
        'gate': {'name': 'the garden gate', 'kind': 'prop'},
        'welcome': {'name': 'the garden welcome', 'kind': 'occasion'},
    }

    premise = rng.choice(('shadow', 'ribbon', 'lamp_guest'))

    initial = {
        'mira.memes.curiosity': 2,
        'mira.memes.spectacle': 2,
        'mira.knows.lamp.lit': None,
        'mira.knows.luma.preference': None,
        'mira.ribbon_request': False,
        'mira.agreed_mode': None,
        'mira.delighted': False,

        'sol.memes.calm': 2,
        'sol.knows.lamp.lit': None,
        'sol.knows.luma.preference': None,
        'sol.agreed_mode': None,
        'sol.ribbon_trade': False,
        'sol.delighted': False,

        'luma.preference': 'flowers',
        'luma.location': 'garden',

        'lamp.lit': False,
        'lamp.owner': 'mira',

        'screen.position': 'side',
        'screen.owner': 'sol',

        'ribbon.owner': 'mira',
        'ribbon.tied': False,

        'flowers.open': False,
        'gate.open': False,

        'welcome.mode': None,
        'welcome.ready': False,
        'welcome.guest_content': False,
    }

    if premise == 'shadow':
        initial.update({
            'lamp.lit': True,
            'screen.position': 'behind_lamp',
            'luma.location': 'screen',
            'luma.preference': 'screen',
        })
    elif premise == 'ribbon':
        initial.update({
            'ribbon.owner': 'sol',
            'ribbon.tied': True,
            'flowers.open': False,
            'luma.location': 'garden',
            'luma.preference': 'flowers',
        })
    else:
        initial.update({
            'lamp.lit': True,
            'luma.location': 'lamp',
            'luma.preference': 'flowers',
            'welcome.mode': 'bright',
            'welcome.guest_content': 'unexpected',
        })

    scenes = (
        scene(
            'open_gate', 'Invite', ('mira',),
            when=(C('mira.memes.spectacle', 'ge', 1),),
            set_values={'gate.open': True},
            summary='Mira opened the gate and called Luma to the garden.',
        ),
        observe(
            'look_lamp', 'mira', 'lamp.lit',
            requires=(C('gate.open', 'eq', True),),
            summary='Mira checked whether the lantern was lit.',
        ),
        scene(
            'notice_luma_shadow', 'Discover', ('sol',),
            when=(
                C('gate.open', 'eq', True),
                C('sol.knows.lamp.lit', 'eq', True),
                C('luma.location', 'eq', 'screen'),
            ),
            set_values={'sol.knows.luma.preference': 'screen'},
            increments={'sol.memes.calm': 1},
            summary='Sol found Luma behind the screen, away from the glare.',
        ),
        tell(
            'tell_sol_lamp', 'mira', 'sol', 'lamp.lit',
            requires=(
                C('gate.open', 'eq', True),
                C('mira.knows.lamp.lit', 'ne', None),
            ),
            summary='Mira told Sol what the lantern was doing.',
            pivotal=True,
        ),
        scene(
            'move_screen', 'Prepare', ('sol',),
            when=(
                C('gate.open', 'eq', True),
                C('lamp.lit', 'eq', True),
                C('luma.location', 'eq', 'screen'),
                C('sol.knows.luma.preference', 'eq', 'screen'),
            ),
            set_values={'screen.position': 'in_front'},
            summary='Sol moved the screen into the lantern glow.',
        ),
        scene(
            'untie_ribbon', 'Trade', ('sol',),
            when=(
                C('gate.open', 'eq', True),
                C('ribbon.owner', 'eq', 'sol'),
                C('ribbon.tied', 'eq', True),
            ),
            set_values={'ribbon.tied': False, 'sol.ribbon_trade': True},
            summary='Sol untied the blue ribbon from the gate.',
        ),
        transfer(
            'transfer_ribbon', 'sol', 'mira', 'ribbon',
            requires=(
                C('gate.open', 'eq', True),
                C('ribbon.tied', 'eq', False),
                C('sol.ribbon_trade', 'eq', True),
            ),
            summary='Sol gave Mira the blue ribbon for the flower bowl.',
        ),
        scene(
            'tie_flower', 'Prepare', ('mira',),
            when=(
                C('gate.open', 'eq', True),
                C('ribbon.owner', 'eq', 'mira'),
                C('ribbon.tied', 'eq', False),
            ),
            set_values={'ribbon.tied': True, 'mira.ribbon_request': True},
            summary='Mira tied the ribbon around the moonflower bowl.',
        ),
        scene(
            'open_flowers', 'Prepare', ('sol',),
            when=(C('gate.open', 'eq', True), C('flowers.open', 'eq', False)),
            set_values={'flowers.open': True},
            summary='Sol opened the moonflowers into a soft landing path.',
        ),
        observe(
            'notice_luma', 'sol', 'luma.preference',
            requires=(C('gate.open', 'eq', True),),
            summary='Sol watched closely to see where Luma wished to land.',
        ),
        tell(
            'tell_mira_preference', 'sol', 'mira', 'luma.preference',
            requires=(
                C('gate.open', 'eq', True),
                C('sol.knows.luma.preference', 'ne', None),
            ),
            summary='Sol told Mira what Luma had chosen.',
            pivotal=True,
        ),
        scene(
            'dim_lamp', 'Adjust', ('mira',),
            when=(
                C('gate.open', 'eq', True),
                C('lamp.lit', 'eq', True),
                C('mira.knows.luma.preference', 'eq', 'flowers'),
            ),
            set_values={'lamp.lit': False},
            summary='Mira lowered the lantern so it would not glare.',
        ),
        scene(
            'choose_shadow', 'Negotiate', ('mira', 'sol'),
            when=(
                C('gate.open', 'eq', True),
                C('screen.position', 'eq', 'in_front'),
                C('sol.knows.luma.preference', 'eq', 'screen'),
            ),
            set_values={
                'welcome.mode': 'shadow',
                'mira.agreed_mode': 'shadow',
                'sol.agreed_mode': 'shadow',
            },
            summary='Mira and Sol chose a shadow welcome together.',
        ),
        scene(
            'choose_moonflower', 'Negotiate', ('mira', 'sol'),
            when=(
                C('gate.open', 'eq', True),
                C('flowers.open', 'eq', True),
                C('mira.knows.luma.preference', 'eq', 'flowers'),
                C('sol.knows.luma.preference', 'eq', 'flowers'),
            ),
            set_values={
                'welcome.mode': 'moonflower',
                'mira.agreed_mode': 'moonflower',
                'sol.agreed_mode': 'moonflower',
            },
            summary='Mira and Sol chose a moonflower welcome together.',
        ),
        scene(
            'perform_shadow', 'Perform', ('mira', 'sol'),
            when=(
                C('welcome.mode', 'eq', 'shadow'),
                C('screen.position', 'eq', 'in_front'),
                C('lamp.lit', 'eq', True),
            ),
            set_values={'welcome.guest_content': True, 'mira.delighted': True},
            summary='The lantern made leaves and tiny wings dance on the screen.',
        ),
        scene(
            'invite_luma', 'Invite', ('sol',),
            when=(
                C('gate.open', 'eq', True),
                C('flowers.open', 'eq', True),
                C('sol.knows.luma.preference', 'eq', 'flowers'),
            ),
            set_values={'sol.delighted': True},
            summary='Sol quietly offered Luma the moonflower path.',
        ),
        scene(
            'luma_lands', 'Arrive', ('luma',),
            when=(
                C('welcome.mode', 'eq', 'moonflower'),
                C('flowers.open', 'eq', True),
                C('luma.preference', 'eq', 'flowers'),
            ),
            set_values={
                'luma.location': 'flowers',
                'welcome.guest_content': True,
            },
            summary='Luma settled among the moonflowers.',
        ),
        scene(
            'welcome_done', 'Celebrate', ('mira', 'sol'),
            when=(
                C('gate.open', 'eq', True),
                C('welcome.mode', 'ne', None),
                C('welcome.guest_content', 'ne', False),
            ),
            set_values={'welcome.ready': True},
            summary='The children let the welcome become what Luma had made it.',
        ),
    )

    rules = (
        Rule(
            'shadow_welcome_needs_screen',
            (C('screen.position', 'eq', 'in_front'),),
            when=(C('welcome.mode', 'eq', 'shadow'),),
        ),
        Rule(
            'moonflower_welcome_needs_petals',
            (C('flowers.open', 'eq', True),),
            when=(C('welcome.mode', 'eq', 'moonflower'),),
        ),
        Rule(
            'bright_guest_needs_lantern',
            (C('lamp.lit', 'eq', True),),
            when=(
                C('welcome.mode', 'eq', 'bright'),
                C('luma.location', 'eq', 'lamp'),
            ),
        ),
    )

    return WorldSpec(
        'The Lantern That Learned to Whisper',
        entities,
        initial,
        scenes,
        goal=(C('welcome.ready', 'eq', True),),
        rules=rules,
        labels={
            'lamp.lit': 'the lantern light',
            'luma.location': 'Luma’s landing place',
            'ribbon.owner': 'the ribbon holder',
            'flowers.open': 'the moonflowers',
            'welcome.mode': 'the kind of welcome',
            'welcome.guest_content': 'Luma’s response',
        },
        prune=True,
        premise_keys=('lamp.lit', 'luma.location', 'ribbon.owner', 'flowers.open'),
        outcome_keys=('welcome.mode', 'luma.location', 'welcome.guest_content'),
    )
