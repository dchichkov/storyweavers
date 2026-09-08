import random
from runtime import WorldSpec, Condition as C, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)
    mode = rng.randrange(3)

    if mode == 0:
        tangled, brave, plan, invited = True, 1, 'quiet', True
    elif mode == 1:
        tangled, brave, plan, invited = False, 0, 'quiet', True
    else:
        tangled, brave, plan, invited = False, 1, 'grand', False

    entities = {
        'mara': {'name': 'Mara', 'kind': 'child'},
        'nia': {'name': 'Nia', 'kind': 'child'},
        'bo': {'name': 'Bo', 'kind': 'child'},
        'puck': {'name': 'Puck', 'kind': 'paper puppet'},
        'curtain': {'name': 'red curtain', 'kind': 'prop'},
        'ribbon': {'name': 'blue ribbon', 'kind': 'prop'},
        'sun': {'name': 'paper sun', 'kind': 'prop'},
        'clouds': {'name': 'cloud puppets', 'kind': 'prop'},
        'stool': {'name': 'low stool', 'kind': 'prop'},
        'stage': {'name': 'courtyard stage', 'kind': 'place'},
        'audience': {'name': 'courtyard audience', 'kind': 'group'},
    }

    initial = {
        'curtain.tangled': tangled,
        'curtain.form': 'hanging',
        'curtain.location': 'stage',
        'ribbon.owner': 'mara',
        'ribbon.location': 'basket',
        'sun.location': 'basket',
        'clouds.location': 'basket',
        'stool.location': 'stage',
        'stage.performance': 'none',
        'stage.location': 'courtyard',
        'audience.invited': invited,
        'audience.present': False,
        'audience.location': 'courtyard',
        'audience.response': 'none',
        'nia.brave': brave,
        'nia.shadow_request': True,
        'nia.agreed': False,
        'nia.content': False,
        'bo.plan': plan,

        'mara.knows.curtain.tangled': None,
        'mara.knows.bo.plan': None,
        'mara.knows.audience.invited': None,
        'mara.knows.nia.shadow_request': None,
        'nia.knows.nia.shadow_request': True,
        'bo.knows.audience.invited': None,
    }

    scenes = (
        scene(
            'greet_audience', 'Greeting', ('mara', 'nia', 'bo'),
            when=(C('audience.present', 'eq', False),),
            set_values={'audience.present': True},
            summary='The children welcomed the courtyard audience',
        ),
        observe(
            'notice_curtain', 'mara', 'curtain.tangled',
            requires=(C('curtain.tangled', 'eq', True),),
            summary='Mara noticed the breeze-tangled curtain',
        ),
        observe(
            'notice_bo_plan', 'mara', 'bo.plan',
            requires=(C('bo.plan', 'eq', 'grand'),),
            summary='Mara noticed Bo planning a grand finale',
        ),
        observe(
            'notice_invitation', 'mara', 'audience.invited',
            requires=(C('audience.invited', 'eq', False),),
            summary='Mara noticed that the audience had not been invited close',
        ),
        tell(
            'tell_nia_to_mara', 'nia', 'mara', 'nia.shadow_request',
            when=(C('nia.knows.nia.shadow_request', 'eq', True),),
            summary='Nia told Mara she wanted a hidden shadow role',
        ),
        tell(
            'tell_mara_to_bo', 'mara', 'bo', 'audience.invited',
            when=(
                C('mara.knows.audience.invited', 'eq', False),
                C('mara.knows.bo.plan', 'eq', 'grand'),
            ),
            summary='Mara told Bo the audience was not yet close',
        ),
        transfer(
            'transfer_ribbon_to_bo', 'mara', 'bo', 'ribbon',
            when=(C('mara.knows.curtain.tangled', 'eq', True),),
            summary='Mara handed the blue ribbon to Bo',
        ),
        scene(
            'untangle_curtain_with_ribbon', 'Rescue', ('bo', 'mara'),
            when=(
                C('mara.knows.curtain.tangled', 'eq', True),
                C('ribbon.owner', 'eq', 'bo'),
                C('curtain.tangled', 'eq', True),
            ),
            set_values={
                'curtain.tangled': False,
                'ribbon.location': 'curtain',
            },
            summary='Bo caught the curtain with the blue ribbon',
        ),
        transfer(
            'transfer_ribbon_to_nia', 'mara', 'nia', 'ribbon',
            when=(
                C('mara.knows.nia.shadow_request', 'eq', True),
            ),
            summary='Mara gave Nia the blue ribbon',
        ),
        scene(
            'agree_small_role', 'Courage', ('mara', 'nia'),
            when=(
                C('mara.knows.nia.shadow_request', 'eq', True),
                C('nia.brave', 'eq', 0),
                C('ribbon.owner', 'eq', 'mara'),
            ),
            set_values={
                'nia.agreed': True,
                'nia.brave': 1,
            },
            summary='Nia agreed to perform behind the curtain',
            pivotal=True,
        ),
        scene(
            'fold_curtain_into_shadow_screen', 'Shadows', ('nia', 'mara'),
            when=(
                C('nia.agreed', 'eq', True),
                C('ribbon.owner', 'eq', 'nia'),
                C('curtain.tangled', 'eq', False),
            ),
            set_values={
                'curtain.form': 'shadow_screen',
                'curtain.location': 'stage',
            },
            summary='Nia folded the curtain into a glowing shadow screen',
        ),
        scene(
            'invite_audience_close', 'Invitation', ('bo', 'mara'),
            when=(
                C('bo.knows.audience.invited', 'eq', False),
                C('bo.plan', 'eq', 'grand'),
                C('audience.invited', 'eq', False),
            ),
            set_values={
                'audience.invited': True,
                'audience.location': 'stage',
            },
            summary='Bo invited everyone to follow the show across the courtyard',
            pivotal=True,
        ),
        scene(
            'place_sun_high', 'Sky', ('bo',),
            when=(
                C('bo.plan', 'eq', 'grand'),
                C('audience.invited', 'eq', True),
            ),
            set_values={'sun.location': 'high'},
            summary='Bo lifted the paper sun high above the stage',
        ),
        scene(
            'place_clouds_low', 'Sky', ('mara', 'bo'),
            when=(
                C('bo.plan', 'eq', 'grand'),
                C('sun.location', 'eq', 'high'),
            ),
            set_values={'clouds.location': 'low'},
            summary='Mara set the cloud puppets bobbing low',
        ),
        scene(
            'perform_kite_rescue', 'Performance', ('bo', 'mara'),
            when=(
                C('curtain.tangled', 'eq', False),
                C('ribbon.owner', 'eq', 'bo'),
                C('audience.present', 'eq', True),
            ),
            set_values={
                'stage.performance': 'kite_rescue',
                'audience.response': 'delighted',
                'nia.content': True,
            },
            summary='Puck flew as a kite puppet in the rescue show',
        ),
        scene(
            'perform_shadow_story', 'Performance', ('nia', 'mara'),
            when=(
                C('curtain.form', 'eq', 'shadow_screen'),
                C('nia.agreed', 'eq', True),
                C('audience.present', 'eq', True),
            ),
            set_values={
                'stage.performance': 'shadow_story',
                'audience.response': 'quietly_charmed',
                'nia.content': True,
            },
            summary='Nia performed a quiet shadow story behind the screen',
        ),
        scene(
            'perform_weather_parade', 'Performance', ('bo', 'mara', 'nia'),
            when=(
                C('bo.plan', 'eq', 'grand'),
                C('audience.invited', 'eq', True),
                C('sun.location', 'eq', 'high'),
                C('clouds.location', 'eq', 'low'),
                C('audience.present', 'eq', True),
            ),
            set_values={
                'stage.performance': 'weather_parade',
                'audience.response': 'delighted',
                'nia.content': True,
            },
            summary='The children performed a wandering weather parade',
        ),
        scene(
            'bow_and_share_paper_sun', 'Finale', ('mara', 'nia', 'bo'),
            when=(
                C('stage.performance', 'ne', 'none'),
                C('audience.response', 'ne', 'none'),
            ),
            set_values={'sun.location': 'shared'},
            summary='The children bowed beneath the shared paper sun',
        ),
    )

    return WorldSpec(
        'The Courtyard Wind-Up Show',
        entities,
        initial,
        scenes,
        goal=(
            C('stage.performance', 'ne', 'none'),
            C('audience.response', 'ne', 'none'),
            C('nia.content', 'eq', True),
        ),
        rules=(),
        labels={
            'curtain.tangled': 'the curtain tangled',
            'stage.performance': 'the performance',
            'audience.response': 'the audience response',
            'nia.content': 'Nia content',
        },
        prune=True,
        premise_keys=(
            'curtain.tangled',
            'nia.brave',
            'bo.plan',
            'ribbon.owner',
        ),
        outcome_keys=(
            'stage.performance',
            'audience.response',
            'nia.content',
        ),
    )

