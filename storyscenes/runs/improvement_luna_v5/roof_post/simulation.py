import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)

    entities = {
        'mina': {'name': 'Mina', 'kind': 'child'},
        'pip': {'name': 'Pip', 'kind': 'dragon'},
        'jun': {'name': 'Jun', 'kind': 'pigeon'},
        'roof_post': {'name': 'roof post', 'kind': 'prop'},
        'invitation_stack': {'name': 'invitation stack', 'kind': 'prop'},
        'ribbon_bundle': {'name': 'ribbon bundle', 'kind': 'prop'},
        'berry_basket': {'name': 'berry basket', 'kind': 'prop'},
        'paper_sail': {'name': 'paper sail', 'kind': 'prop'},
    }

    hooks = ['safe', 'crowded', 'bird_high']
    conditions = ['sturdy', 'delicate', 'already-folded']
    styles = ['carry', 'fly', 'decorate']

    initial = {
        'mina.curiosity': 2,
        'mina.promise': False,
        'mina.thanked': False,
        'mina.knows.roof_post.open_hook': None,
        'mina.knows.invitation_stack.condition': None,
        'mina.knows.jun.request': None,

        'pip.help_style': rng.choice(styles),
        'pip.agrees_to_share': False,
        'pip.knows.jun.request': None,
        'pip.knows.roof_post.open_hook': None,
        'pip.knows.invitation_stack.condition': None,
        'pip.knows.paper_sail.attached': None,

        'jun.request': None,
        'jun.agreement': False,
        'jun.guided': False,

        'roof_post.open_hook': rng.choice(hooks),
        'roof_post.selected_hook': None,

        'invitation_stack.owner': 'mina',
        'invitation_stack.location': 'mina',
        'invitation_stack.condition': rng.choice(conditions),
        'invitation_stack.delivered': False,
        'invitation_stack.ribboned': False,
        'invitation_stack.mode': None,

        'ribbon_bundle.owner': 'mina',
        'ribbon_bundle.tied': False,

        'berry_basket.owner': 'mina',
        'berry_basket.location': 'mina',

        'paper_sail.owner': 'mina',
        'paper_sail.attached': False,
        'paper_sail.flight': 'none',
    }

    scenes = (
        scene(
            'place_stack', 'Invitation', ('mina',),
            when=(
                C('invitation_stack.owner', 'eq', 'mina'),
                C('invitation_stack.location', 'eq', 'mina'),
            ),
            set_values={
                'invitation_stack.location': 'beside_post',
                'mina.promise': True,
            },
            summary='Mina placed the invitations beside the roof post',
        ),
        observe(
            'look_post', 'mina', 'roof_post.open_hook',
            requires=(
                C('mina.promise', 'eq', True),
                C('invitation_stack.location', 'eq', 'beside_post'),
            ),
            summary='Mina inspected the roof post',
        ),
        observe(
            'notice_cargo', 'mina', 'invitation_stack.condition',
            requires=(
                C('mina.promise', 'eq', True),
                C('invitation_stack.location', 'eq', 'beside_post'),
            ),
            summary='Mina noticed the condition of the invitations',
        ),
        scene(
            'ask_Jun', 'Conversation', ('mina', 'jun'),
            when=(
                C('mina.promise', 'eq', True),
                C('jun.request', 'eq', None),
            ),
            set_values={
                'jun.request': 'quiet_corner',
                'mina.knows.jun.request': 'quiet_corner',
            },
            summary='Mina asked Jun where the bird guests should gather',
        ),
        tell(
            'tell_Pip_request', 'mina', 'pip', 'jun.request',
            when=(
                C('mina.knows.jun.request', 'eq', 'quiet_corner'),
                C('jun.request', 'eq', 'quiet_corner'),
            ),
            summary='Mina told Pip about Jun’s quiet corner',
        ),
        scene(
            'choose_safe_hook', 'Preparation', ('mina',),
            when=(
                C('mina.knows.roof_post.open_hook', 'ne', None),
                C('invitation_stack.location', 'eq', 'beside_post'),
            ),
            copies={'roof_post.selected_hook': 'roof_post.open_hook'},
            summary='Mina chose an open hook',
        ),
        scene(
            'tie_ribbon', 'Preparation', ('mina',),
            when=(
                C('mina.knows.invitation_stack.condition', 'ne', None),
                C('ribbon_bundle.owner', 'eq', 'mina'),
                C('ribbon_bundle.tied', 'eq', False),
            ),
            set_values={
                'ribbon_bundle.tied': True,
                'invitation_stack.ribboned': True,
            },
            summary='Mina tied a ribbon around the invitations',
        ),
        scene(
            'attach_paper_sail', 'Preparation', ('mina',),
            when=(
                C('pip.help_style', 'eq', 'fly'),
                C('paper_sail.owner', 'eq', 'mina'),
                C('paper_sail.attached', 'eq', False),
                C('invitation_stack.condition', 'in', ('sturdy', 'already-folded')),
            ),
            set_values={'paper_sail.attached': True},
            summary='Mina attached the paper sail',
        ),
        transfer(
            'Pip_grabs_stack', 'mina', 'pip', 'invitation_stack',
            when=(
                C('pip.help_style', 'in', ('carry', 'fly')),
                C('mina.knows.invitation_stack.condition', 'eq', 'delicate'),
                C('invitation_stack.location', 'eq', 'beside_post'),
            ),
            summary='Pip grabbed the delicate invitations',
        ),
        scene(
            'Mina_stops_fragile_cargo', 'Rescue', ('mina', 'pip'),
            when=(
                C('invitation_stack.owner', 'eq', 'pip'),
                C('invitation_stack.condition', 'eq', 'delicate'),
            ),
            set_values={
                'invitation_stack.owner': 'mina',
                'invitation_stack.condition': 'creased',
                'invitation_stack.location': 'beside_post',
            },
            summary='Mina took back the invitations with a bent corner',
        ),
        scene(
            'Pip_offers_sail', 'Choice', ('pip',),
            when=(
                C('pip.help_style', 'eq', 'decorate'),
                C('pip.knows.jun.request', 'eq', 'quiet_corner'),
                C('paper_sail.attached', 'eq', False),
            ),
            set_values={
                'paper_sail.attached': True,
                'pip.agrees_to_share': True,
            },
            summary='Pip offered a sail for two different invitations',
            pivotal=True,
        ),
        scene(
            'Mina_accepts_shared_plan', 'Choice', ('mina', 'pip'),
            when=(
                C('pip.agrees_to_share', 'eq', True),
                C('mina.knows.jun.request', 'eq', 'quiet_corner'),
                C('invitation_stack.ribboned', 'eq', True),
            ),
            set_values={
                'jun.agreement': True,
                'invitation_stack.mode': 'shared',
            },
            summary='Mina accepted Pip’s shared plan',
            pivotal=True,
        ),
        scene(
            'post_first_invite', 'Delivery', ('mina',),
            when=(
                C('roof_post.selected_hook', 'ne', None),
                C('invitation_stack.owner', 'eq', 'mina'),
                C('invitation_stack.ribboned', 'eq', True),
                C('invitation_stack.condition', 'in', ('sturdy', 'already-folded')),
                C('jun.agreement', 'eq', False),
            ),
            set_values={
                'invitation_stack.delivered': True,
                'invitation_stack.location': 'selected_hook',
                'invitation_stack.mode': 'posted',
            },
            summary='Mina posted the first invitation',
        ),
        scene(
            'fly_sail_invite', 'Performance', ('pip',),
            when=(
                C('paper_sail.attached', 'eq', True),
                C('paper_sail.flight', 'eq', 'none'),
                C('invitation_stack.owner', 'eq', 'mina'),
                C('invitation_stack.ribboned', 'eq', True),
                C('invitation_stack.condition', 'in', ('sturdy', 'already-folded')),
                C('jun.agreement', 'eq', False),
            ),
            set_values={
                'paper_sail.flight': 'landed',
                'invitation_stack.delivered': True,
                'invitation_stack.location': 'high_hook',
                'invitation_stack.mode': 'sail',
            },
            summary='Pip flew an invitation to the high hook',
        ),
        scene(
            'Jun_guides_roof_route', 'Guidance', ('jun',),
            when=(
                C('jun.agreement', 'eq', True),
                C('jun.request', 'eq', 'quiet_corner'),
                C('jun.guided', 'eq', False),
            ),
            set_values={'jun.guided': True},
            summary='Jun guided the route to the quiet corner',
        ),
        scene(
            'deliver_basket', 'Delivery', ('mina', 'pip', 'jun'),
            when=(
                C('jun.guided', 'eq', True),
                C('invitation_stack.mode', 'eq', 'shared'),
                C('invitation_stack.owner', 'eq', 'mina'),
            ),
            set_values={
                'invitation_stack.delivered': True,
                'invitation_stack.location': 'quiet_corner',
            },
            summary='The shared invitations reached the quiet corner',
        ),
        scene(
            'gather_after_wobble', 'Delivery', ('mina', 'pip'),
            when=(
                C('invitation_stack.owner', 'eq', 'mina'),
                C('invitation_stack.condition', 'eq', 'creased'),
                C('invitation_stack.ribboned', 'eq', True),
            ),
            set_values={
                'invitation_stack.delivered': True,
                'invitation_stack.location': 'roof_neighbors',
                'invitation_stack.mode': 'hand-carried',
            },
            summary='Mina and Pip carried the softened invitations together',
        ),
        scene(
            'thank_you', 'Affection', ('mina', 'pip'),
            when=(
                C('invitation_stack.delivered', 'eq', True),
                C('mina.thanked', 'eq', False),
            ),
            set_values={'mina.thanked': True},
            summary='Mina thanked Pip',
        ),
    )

    labels = {
        'roof_post.open_hook': 'the roof post’s open hook',
        'invitation_stack.condition': 'the invitation paper',
        'invitation_stack.location': 'the invitation place',
        'invitation_stack.mode': 'the delivery style',
        'paper_sail.flight': 'the paper sail’s flight',
        'jun.agreement': 'Jun’s agreement',
    }

    return WorldSpec(
        'The Roof-Post Invitation Flight',
        entities,
        initial,
        scenes,
        goal=(C('invitation_stack.delivered', 'eq', True),),
        rules=(),
        labels=labels,
        prune=True,
        premise_keys=(
            'roof_post.open_hook',
            'invitation_stack.condition',
            'pip.help_style',
        ),
        outcome_keys=(
            'invitation_stack.delivered',
            'invitation_stack.condition',
            'paper_sail.flight',
            'jun.agreement',
        ),
    )


