import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)
    case = rng.randrange(3)

    entities = {
        'ada': {'name': 'Ada', 'kind': 'child'},
        'pip': {'name': 'Pip', 'kind': 'dragon'},
        'keeper': {'name': 'Mr. Bellweather', 'kind': 'keeper'},
        'bell': {'name': 'brass bell', 'kind': 'prop'},
        'flag': {'name': 'feather flag', 'kind': 'prop'},
        'invitation': {'name': 'red invitation ribbon', 'kind': 'prop'},
        'notebook': {'name': 'club notebook', 'kind': 'prop'},
        'key': {'name': 'wooden key', 'kind': 'prop'},
        'neighbor': {'name': 'sleeping neighbor', 'kind': 'person'},
    }

    initial = {
        'bell.owner': 'keeper',
        'bell.unlocked': False,
        'bell.soft_rope': True,
        'bell.last_sound': None,
        'flag.color': 'red' if case == 0 else 'blue',
        'flag.meaning': 'signal_is_not_invitation',
        'invitation.owner': 'ada',
        'invitation.delivered': False,
        'notebook.owner': 'ada',
        'notebook.ready': False,
        'key.owner': 'keeper',
        'neighbor.awake': case != 1,
        'neighbor.response': None,
        'ada.promise.noisy': case == 1,
        'pip.believes.sneeze_loud': case == 2,
        'pip.chose.gentle': None,
        'notebook.meeting_done': False,

        'keeper.knows.flag.meaning': 'signal_is_not_invitation',
        'ada.knows.flag.color': None,
        'ada.knows.flag.meaning': None,
        'ada.knows.neighbor.awake': None,
        'pip.knows.flag.meaning': None,
        'pip.knows.bell.soft_rope': None,
        'pip.knows.neighbor.awake': None,
    }

    scenes = (
        observe(
            'notice_flag',
            'ada',
            'flag.color',
            requires=(C('ada.knows.flag.color', 'eq', None),),
            summary='Ada noticed the feather flag',
        ),
        tell(
            'keeper_explains_flag',
            'keeper',
            'ada',
            'flag.meaning',
            when=(C('ada.knows.flag.color', 'ne', None),),
            summary='Mr. Bellweather explained the flag',
        ),
        tell(
            'ada_tells_pip_flag',
            'ada',
            'pip',
            'flag.meaning',
            when=(C('ada.knows.flag.meaning', 'ne', None),),
            summary='Ada told Pip what the flag meant',
        ),
        observe(
            'notice_neighbor',
            'ada',
            'neighbor.awake',
            requires=(C('ada.knows.neighbor.awake', 'eq', None),),
            summary='Ada checked the neighbor’s window',
        ),
        tell(
            'ada_tells_pip_neighbor',
            'ada',
            'pip',
            'neighbor.awake',
            when=(C('ada.knows.neighbor.awake', 'ne', None),),
            summary='Ada told Pip about the window',
        ),
        observe(
            'inspect_soft_rope',
            'pip',
            'bell.soft_rope',
            requires=(C('pip.knows.bell.soft_rope', 'eq', None),),
            summary='Pip found the soft practice rope',
        ),
        transfer(
            'hand_over_invitation',
            'ada',
            'keeper',
            'invitation',
            when=(
                C('pip.knows.flag.meaning', 'eq', 'signal_is_not_invitation'),
                C('invitation.owner', 'eq', 'ada'),
            ),
            summary='Ada handed over the ribbon invitation',
        ),
        scene(
            'deliver_invitation',
            'Welcome',
            ('keeper', 'ada', 'pip'),
            when=(
                C('invitation.owner', 'eq', 'keeper'),
                C('invitation.delivered', 'eq', False),
            ),
            set_values={'invitation.delivered': True},
            summary='The keeper delivered the invitation',
        ),
        scene(
            'prepare_notebook',
            'Welcome',
            ('ada', 'pip'),
            when=(
                C('invitation.delivered', 'eq', True),
                C('notebook.ready', 'eq', False),
            ),
            set_values={'notebook.ready': True},
            summary='Ada opened the club notebook',
        ),
        transfer(
            'lend_key',
            'keeper',
            'pip',
            'key',
            when=(
                C('notebook.ready', 'eq', True),
                C('key.owner', 'eq', 'keeper'),
            ),
            summary='The keeper lent Pip the wooden key',
        ),
        scene(
            'unlock_bell',
            'Welcome',
            ('pip', 'keeper'),
            when=(
                C('key.owner', 'eq', 'pip'),
                C('bell.unlocked', 'eq', False),
            ),
            set_values={'bell.unlocked': True},
            summary='Pip unlocked the bell',
        ),
        scene(
            'choose_gentle',
            'Turning',
            ('pip',),
            when=(
                C('bell.unlocked', 'eq', True),
                C('pip.knows.bell.soft_rope', 'eq', True),
                C('pip.chose.gentle', 'eq', None),
            ),
            set_values={'pip.chose.gentle': True},
            summary='Pip chose the gentle chime',
            pivotal=True,
        ),
        scene(
            'choose_grand',
            'Turning',
            ('pip',),
            when=(
                C('bell.unlocked', 'eq', True),
                C('pip.knows.flag.meaning', 'eq', 'signal_is_not_invitation'),
                C('pip.believes.sneeze_loud', 'eq', False),
                C('pip.chose.gentle', 'eq', None),
            ),
            set_values={'pip.chose.gentle': False},
            summary='Pip chose the grand chime',
            pivotal=True,
        ),
        scene(
            'perform_gentle_meeting',
            'Performance',
            ('ada', 'pip', 'keeper'),
            when=(
                C('invitation.delivered', 'eq', True),
                C('notebook.ready', 'eq', True),
                C('bell.unlocked', 'eq', True),
                C('pip.chose.gentle', 'eq', True),
                C('notebook.meeting_done', 'eq', False),
            ),
            set_values={
                'notebook.meeting_done': True,
                'bell.last_sound': 'soft',
            },
            summary='The club performed a gentle meeting',
        ),
        scene(
            'perform_grand_meeting',
            'Performance',
            ('ada', 'pip', 'keeper'),
            when=(
                C('invitation.delivered', 'eq', True),
                C('notebook.ready', 'eq', True),
                C('bell.unlocked', 'eq', True),
                C('pip.chose.gentle', 'eq', False),
                C('notebook.meeting_done', 'eq', False),
            ),
            set_values={
                'notebook.meeting_done': True,
                'bell.last_sound': 'grand',
            },
            summary='The club performed a grand meeting',
        ),
        scene(
            'neighbor_pleased',
            'Audience',
            ('neighbor', 'ada', 'pip'),
            when=(
                C('notebook.meeting_done', 'eq', True),
                C('bell.last_sound', 'eq', 'soft'),
                C('neighbor.awake', 'eq', True),
                C('neighbor.response', 'eq', None),
            ),
            set_values={'neighbor.response': 'pleased'},
            summary='The neighbor joined with sleepy muffins',
        ),
        scene(
            'neighbor_quiet',
            'Audience',
            ('neighbor', 'ada', 'pip'),
            when=(
                C('notebook.meeting_done', 'eq', True),
                C('bell.last_sound', 'eq', 'soft'),
                C('neighbor.awake', 'eq', False),
                C('neighbor.response', 'eq', None),
            ),
            set_values={'neighbor.response': 'quiet'},
            summary='The neighbor welcomed the quiet meeting',
        ),
        scene(
            'neighbor_amused',
            'Audience',
            ('neighbor', 'ada', 'pip'),
            when=(
                C('notebook.meeting_done', 'eq', True),
                C('bell.last_sound', 'eq', 'grand'),
                C('neighbor.awake', 'eq', True),
                C('neighbor.response', 'eq', None),
            ),
            set_values={'neighbor.response': 'amused'},
            summary='The neighbor laughed at the grand bonk',
        ),
        scene(
            'neighbor_startled',
            'Audience',
            ('neighbor', 'ada', 'pip'),
            when=(
                C('notebook.meeting_done', 'eq', True),
                C('bell.last_sound', 'eq', 'grand'),
                C('neighbor.awake', 'eq', False),
                C('neighbor.response', 'eq', None),
            ),
            set_values={'neighbor.response': 'startled'},
            summary='The neighbor woke with a startled grin',
        ),
    )

    return WorldSpec(
        'The Clocktower Club: Three Chimes and a Dragon',
        entities,
        initial,
        scenes,
        goal=(
            C('notebook.meeting_done', 'eq', True),
            C('neighbor.response', 'ne', None),
        ),
        rules=(),
        labels={
            'bell.last_sound': 'the bell sound',
            'neighbor.response': 'the neighbor’s response',
            'pip.chose.gentle': 'Pip’s chime choice',
        },
        prune=True,
        premise_keys=(
            'flag.color',
            'neighbor.awake',
            'pip.believes.sneeze_loud',
            'invitation.delivered',
        ),
        outcome_keys=(
            'notebook.meeting_done',
            'bell.last_sound',
            'neighbor.response',
            'pip.chose.gentle',
        ),
    )
