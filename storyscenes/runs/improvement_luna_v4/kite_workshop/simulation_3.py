import random
from runtime import WorldSpec, Condition as C, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)

    entities = {
        'pip': {'name': 'Pip', 'kind': 'young dragon'},
        'nia': {'name': 'Nia', 'kind': 'child'},
        'ember': {'name': 'Aunt Ember', 'kind': 'recipient'},
        'kite': {'name': 'bright paper kite', 'kind': 'prop'},
        'thread': {'name': 'blue thread', 'kind': 'prop'},
        'ribbon': {'name': 'red ribbon', 'kind': 'prop'},
        'feather': {'name': 'soft feather', 'kind': 'prop'},
        'message': {'name': 'sealed message', 'kind': 'prop'},
        'mailbox': {'name': 'Aunt Ember’s mailbox', 'kind': 'prop'},
    }

    mark = rng.choice(('dragon', 'weather', 'gathering'))
    audience = rng.choice(('private', 'public'))
    tail = rng.choice(('none', 'ribbon', 'feather'))
    safe_preference = rng.choice(('thread', 'feather'))

    initial = {
        'kite.tail_material': tail,
        'kite.selected_tail': None,
        'kite.tail_attached': False,
        'kite.airborne': False,
        'kite.carrying': None,
        'kite.owner': 'nia',
        'message.mark': mark,
        'message.text_kind': None,
        'message.delivered': False,
        'message.tucked': False,
        'message.owner': 'pip',
        'mailbox.audience': audience,
        'mailbox.reply': None,
        'pip.knows.message.purpose': (
            'dragon_drawing' if mark == 'dragon' else 'dragon_drawing'
        ),
        'pip.knows.message.mark': None,
        'pip.knows.mailbox.audience': None,
        'nia.knows.message.purpose': None,
        'nia.knows.message.mark': None,
        'nia.knows.mailbox.audience': None,
        'nia.safe_preference': safe_preference,
        'nia.agrees.public_flight': False,
        'pip.content': False,
    }

    scenes = (
        observe(
            'inspect_message', 'nia', 'message.mark',
            requires=(C('message.owner', 'eq', 'pip'),),
            summary='Pip examined the little mark on the sealed message',
        ),
        observe(
            'inspect_audience', 'nia', 'mailbox.audience',
            requires=(C('message.delivered', 'eq', False),),
            summary='Nia noticed who gathered near Aunt Ember’s mailbox',
        ),
        tell(
            'tell_mark', 'nia', 'pip', 'message.mark',
            when=(C('nia.knows.message.mark', 'ne', None),),
            summary='Nia told Pip what the mark really meant',
        ),
        tell(
            'tell_audience', 'nia', 'pip', 'mailbox.audience',
            when=(C('nia.knows.mailbox.audience', 'ne', None),),
            summary='Nia told Pip whether the mailbox was private or public',
        ),
        scene(
            'choose_thread', 'Tail Choice', ('nia', 'pip'),
            when=(
                C('pip.knows.mailbox.audience', 'eq', 'private'),
                C('nia.safe_preference', 'eq', 'thread'),
                C('kite.selected_tail', 'eq', None),
            ),
            set_values={'kite.selected_tail': 'thread'},
            summary='They chose the blue thread for a neat private flight',
        ),
        scene(
            'choose_feather', 'Tail Choice', ('nia', 'pip'),
            when=(
                C('pip.knows.mailbox.audience', 'eq', 'private'),
                C('nia.safe_preference', 'eq', 'feather'),
                C('kite.selected_tail', 'eq', None),
            ),
            set_values={'kite.selected_tail': 'feather'},
            summary='They chose the feather for a quiet private flight',
        ),
        scene(
            'choose_ribbon', 'Tail Choice', ('nia', 'pip'),
            when=(
                C('pip.knows.mailbox.audience', 'eq', 'public'),
                C('kite.selected_tail', 'eq', None),
            ),
            set_values={'kite.selected_tail': 'ribbon'},
            summary='They chose the red ribbon for a grand public swoop',
        ),
        transfer(
            'hand_kite_to_pip', 'nia', 'pip', 'kite',
            when=(C('kite.selected_tail', 'ne', None),),
            summary='Nia handed the prepared kite to Pip',
        ),
        transfer(
            'hand_message_to_nia', 'pip', 'nia', 'message',
            when=(
                C('pip.knows.message.mark', 'ne', None),
                C('message.text_kind', 'eq', None),
            ),
            summary='Pip handed the sealed message to Nia for its final wording',
        ),
        scene(
            'rewrite_dragon', 'Message Turn', ('nia', 'pip'),
            when=(
                C('pip.knows.message.mark', 'eq', 'dragon'),
                C('mailbox.audience', 'eq', 'private'),
                C('message.owner', 'eq', 'nia'),
            ),
            set_values={'message.text_kind': 'dragon_drawing'},
            pivotal=True,
            summary='They made the message a dragon drawing',
        ),
        scene(
            'rewrite_weather', 'Message Turn', ('nia', 'pip'),
            when=(
                C('pip.knows.message.mark', 'eq', 'weather'),
                C('message.owner', 'eq', 'nia'),
            ),
            set_values={'message.text_kind': 'weather_note'},
            pivotal=True,
            summary='They changed the message into a useful weather note',
        ),
        scene(
            'rewrite_sky', 'Message Turn', ('nia', 'pip'),
            when=(
                C('pip.knows.message.mark', 'in', ('dragon', 'weather', 'gathering')),
                C('mailbox.audience', 'eq', 'public'),
                C('message.owner', 'eq', 'nia'),
            ),
            set_values={'message.text_kind': 'sky_cheer'},
            pivotal=True,
            summary='They changed the message into a sky cheer for the gathering',
        ),
        scene(
            'attach_tail', 'Assembly', ('pip', 'nia'),
            when=(
                C('kite.owner', 'eq', 'pip'),
                C('kite.selected_tail', 'ne', None),
                C('kite.tail_attached', 'eq', False),
            ),
            set_values={
                'kite.tail_attached': True,
            },
            copies={'kite.tail_material': 'kite.selected_tail'},
            summary='They tied the chosen tail to the kite',
        ),
        scene(
            'tuck_message', 'Assembly', ('nia', 'pip'),
            when=(
                C('message.owner', 'eq', 'nia'),
                C('message.text_kind', 'ne', None),
                C('message.tucked', 'eq', False),
            ),
            set_values={'message.tucked': True},
            summary='Nia tucked the newly worded message into the kite pocket',
        ),
        scene(
            'invite_shared_flight', 'Invitation', ('pip', 'nia'),
            when=(
                C('pip.knows.mailbox.audience', 'eq', 'public'),
                C('kite.owner', 'eq', 'pip'),
                C('message.tucked', 'eq', True),
            ),
            set_values={'nia.agrees.public_flight': True},
            summary='Pip invited Nia to fly the kite before the gathering',
        ),
        scene(
            'launch_kite', 'Performance', ('pip', 'nia'),
            when=(
                C('kite.owner', 'eq', 'pip'),
                C('kite.tail_attached', 'eq', True),
                C('message.tucked', 'eq', True),
                C('mailbox.audience', 'eq', 'private'),
            ),
            set_values={'kite.airborne': True},
            summary='Pip launched the kite toward the quiet mailbox',
        ),
        scene(
            'launch_public_kite', 'Performance', ('pip', 'nia'),
            when=(
                C('kite.owner', 'eq', 'pip'),
                C('kite.tail_attached', 'eq', True),
                C('message.tucked', 'eq', True),
                C('mailbox.audience', 'eq', 'public'),
                C('nia.agrees.public_flight', 'eq', True),
            ),
            set_values={'kite.airborne': True},
            summary='Pip and Nia launched the kite over the gathering',
        ),
        scene(
            'deliver_private', 'Delivery', ('pip',),
            when=(
                C('kite.airborne', 'eq', True),
                C('mailbox.audience', 'eq', 'private'),
                C('message.text_kind', 'ne', 'weather_note'),
            ),
            set_values={
                'kite.carrying': 'private_message',
                'message.delivered': True,
                'mailbox.reply': 'green_flag',
                'pip.content': True,
            },
            summary='The kite carried the private message to Aunt Ember',
        ),
        scene(
            'deliver_weather', 'Delivery', ('pip', 'nia'),
            when=(
                C('kite.airborne', 'eq', True),
                C('message.text_kind', 'eq', 'weather_note'),
            ),
            set_values={
                'kite.carrying': 'weather_note',
                'message.delivered': True,
                'mailbox.reply': 'silver_sun',
                'pip.content': True,
            },
            summary='The low kite delivered the weather note safely',
        ),
        scene(
            'deliver_public', 'Delivery', ('pip', 'nia'),
            when=(
                C('kite.airborne', 'eq', True),
                C('mailbox.audience', 'eq', 'public'),
                C('nia.agrees.public_flight', 'eq', True),
                C('message.text_kind', 'eq', 'sky_cheer'),
            ),
            set_values={
                'kite.carrying': 'sky_cheer',
                'message.delivered': True,
                'mailbox.reply': 'cheer',
                'pip.content': True,
            },
            summary='The kite carried its sky cheer above the children',
        ),
    )

    return WorldSpec(
        'The Kite That Carried Three Kinds of News',
        entities,
        initial,
        scenes,
        goal=(C('pip.content', 'eq', True),),
        rules=(),
        labels={
            'kite.tail_material': 'the kite tail',
            'message.text_kind': 'the message',
            'mailbox.reply': 'the mailbox reply',
            'mailbox.audience': 'the mailbox audience',
        },
        prune=True,
        premise_keys=(
            'kite.tail_material',
            'message.mark',
            'mailbox.audience',
            'nia.safe_preference',
        ),
        outcome_keys=(
            'message.delivered',
            'kite.tail_material',
            'mailbox.reply',
        ),
    )

