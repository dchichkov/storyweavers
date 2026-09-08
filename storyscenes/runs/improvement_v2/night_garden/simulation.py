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
        'sol.knows.luma.location': None,
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
            set_values={
                'gate.open': True,
                'mira.ribbon_request': True,
            },
            summary='Mira opened the garden gate, called Luma in, and asked for the blue ribbon to decorate a landing place.',
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
            set_values={
                'sol.knows.luma.preference': 'screen',
                'sol.knows.luma.location': 'screen',
            },
            increments={'sol.memes.calm': 1},
            summary='Sol found Luma behind the screen, where the lantern glare could not reach her.',
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
            summary='Sol moved the screen into the lantern glow so its leaf shapes could become gentle shadows.',
        ),
        scene(
            'untie_ribbon', 'Trade', ('sol',),
            when=(
                C('gate.open', 'eq', True),
                C('ribbon.owner', 'eq', 'sol'),
                C('ribbon.tied', 'eq', True),
                C('mira.ribbon_request', 'eq', True),
            ),
            set_values={
                'ribbon.tied': False,
                'sol.ribbon_trade': True,
            },
            summary='Sol untied the blue ribbon from the gate after hearing Mira’s plan for the flowers.',
        ),
        transfer(
            'transfer_ribbon', 'sol', 'mira', 'ribbon',
            requires=(
                C('gate.open', 'eq', True),
                C('ribbon.tied', 'eq', False),
                C('sol.ribbon_trade', 'eq', True),
                C('mira.ribbon_request', 'eq', True),
            ),
            summary='Sol gave Mira the blue ribbon, choosing a flower decoration over a gate decoration.',
        ),
        scene(
            'tie_flower', 'Prepare', ('mira',),
            when=(
                C('gate.open', 'eq', True),
                C('ribbon.owner', 'eq', 'mira'),
                C('ribbon.tied', 'eq', False),
                C('mira.ribbon_request', 'eq', True),
            ),
            set_values={'ribbon.tied': True},
            summary='Mira tied the blue ribbon around the moonflower bowl.',
        ),
        scene(
            'open_flowers', 'Prepare', ('sol',),
            when=(
                C('gate.open', 'eq', True),
                C('flowers.open', 'eq', False),
            ),
            set_values={'flowers.open': True},
            summary='Sol opened the moonflowers into a soft landing path.',
        ),
        scene(
            'notice_luma', 'Discover', ('sol',),
            when=(
                C('gate.open', 'eq', True),
                C('luma.location', 'ne', 'screen'),
            ),
            copies={
                'sol.knows.luma.preference': 'luma.preference',
                'sol.knows.luma.location': 'luma.location',
            },
            summary='Sol watched Luma closely and saw both her chosen place and what she preferred.',
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
                C('welcome.mode', 'ne', 'bright'),
            ),
            set_values={'lamp.lit': False},
            summary='Mira lowered the lantern so its glow would guide rather than glare.',
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
            summary='Mira and Sol agreed that a soft shadow welcome suited Luma better than a grand glare.',
        ),
        scene(
            'choose_moonflower', 'Negotiate', ('mira', 'sol'),
            when=(
                C('gate.open', 'eq', True),
                C('flowers.open', 'eq', True),
                C('ribbon.owner', 'eq', 'mira'),
                C('ribbon.tied', 'eq', True),
                C('mira.knows.luma.preference', 'eq', 'flowers'),
                C('sol.knows.luma.preference', 'eq', 'flowers'),
            ),
            set_values={
                'welcome.mode': 'moonflower',
                'mira.agreed_mode': 'moonflower',
                'sol.agreed_mode': 'moonflower',
            },
            summary='Mira and Sol agreed that the ribboned moonflowers would make the welcome.',
        ),
        scene(
            'perform_shadow', 'Perform', ('mira', 'sol'),
            when=(
                C('welcome.mode', 'eq', 'shadow'),
                C('screen.position', 'eq', 'in_front'),
                C('lamp.lit', 'eq', True),
                C('luma.location', 'eq', 'screen'),
            ),
            set_values={
                'welcome.guest_content': True,
                'mira.delighted': True,
                'sol.delighted': True,
            },
            summary='Together the children made leaf shadows and tiny wing-shapes dance across the screen.',
        ),
        scene(
            'accept_lamp_guest', 'Perform', ('mira', 'sol'),
            when=(
                C('gate.open', 'eq', True),
                C('lamp.lit', 'eq', True),
                C('luma.location', 'eq', 'lamp'),
                C('sol.knows.luma.location', 'eq', 'lamp'),
                C('welcome.mode', 'eq', 'bright'),
            ),
            set_values={
                'mira.agreed_mode': 'bright',
                'sol.agreed_mode': 'bright',
                'mira.delighted': True,
                'sol.delighted': True,
            },
            summary='Mira and Sol made a tiny, quiet performance below Luma’s chosen lamp-rim seat.',
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
            summary='Luma settled among the open moonflowers.',
        ),
        scene(
            'welcome_done', 'Celebrate', ('mira', 'sol'),
            when=(
                C('gate.open', 'eq', True),
                C('welcome.mode', 'in', ('shadow', 'moonflower', 'bright')),
                C('welcome.guest_content', 'ne', False),
                C('mira.agreed_mode', 'ne', None),
                C('sol.agreed_mode', 'ne', None),
            ),
            set_values={'welcome.ready': True},
            summary='The children let the welcome become the kind Luma had made possible.',
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
            'moonflower_welcome_needs_ribbon',
            (
                C('ribbon.owner', 'eq', 'mira'),
                C('ribbon.tied', 'eq', True),
            ),
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
