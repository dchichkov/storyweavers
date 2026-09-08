import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer

def build(seed):
    rng = random.Random(seed)
    branch = rng.randrange(3)

    entities = {
        'ada': {'name': 'Ada', 'kind': 'child'},
        'ben': {'name': 'Ben', 'kind': 'child'},
        'pip': {'name': 'Pip', 'kind': 'magpie'},
        'box': {'name': 'wooden museum box', 'kind': 'prop'},
        'marble': {'name': 'red marble', 'kind': 'prop'},
        'key': {'name': 'brass key', 'kind': 'prop'},
        'button': {'name': 'blue button', 'kind': 'prop'},
        'card': {'name': 'visitor card', 'kind': 'prop'},
        'display': {'name': 'museum display', 'kind': 'prop'},
        'visitor': {'name': 'library keeper', 'kind': 'person'},
        'sister': {'name': 'Ben’s sister', 'kind': 'person'},
    }

    if branch == 0:
        contents = 'marble'
        card_status = 'written'
        expectation = 'quiet'
        agreement = 'unagreed'
        arrived = False
        ada_belief = 'marble'
    elif branch == 1:
        contents = 'button'
        card_status = 'written'
        expectation = 'quiet'
        agreement = 'unagreed'
        arrived = False
        ada_belief = 'dull'
    else:
        contents = 'marble'
        card_status = 'blank'
        expectation = 'quiet'
        agreement = 'unagreed'
        arrived = True
        ada_belief = 'marble'

    initial = {
        'ada.memes.Curiosity': 2,
        'ben.memes.Kindness': 2,
        'pip.memes.Mischief': 2,
        'ada.knows.box.contents': ada_belief,
        'ada.knows.visitor.expectation': None,
        'ada.knows.button.owner': None,
        'ben.knows.box.contents': None,
        'ben.knows.marble.owner': 'ben',
        'ben.knows.visitor.expectation': None,
        'pip.knows.button.owner': 'pip',
        'box.contents': contents,
        'box.open': False,
        'box.owner': 'ada',
        'marble.owner': 'ben',
        'marble.borrowed_from': 'sister',
        'key.owner': 'ada',
        'button.owner': 'pip',
        'card.owner': 'ada',
        'card.status': card_status,
        'display.status': 'empty',
        'display.owner': 'ada',
        'visitor.arrived': True,
        'visitor.expectation': expectation,
        'visitor.greeted': False,
        'visitor.mood': 'unknown',
        'ben.agreement': agreement,
        'pip.motive': 'keep',
        'display.mode': 'unset',
    }

    scenes = (
        observe(
            'inspect_contents', 'ada', 'box.contents',
            requires=(C('ada.memes.Curiosity', 'ge', 1),),
            summary='Ada peeked into the museum box'
        ),
        scene(
            'open_box', 'Opening Promise', ('ada',),
            when=(
                C('box.open', 'eq', False),
                C('ada.knows.box.contents', 'ne', None),
            ),
            set_values={'box.open': True},
            summary='Ada opened the museum box'
        ),
        tell(
            'tell_contents', 'ada', 'ben', 'box.contents',
            when=(C('box.open', 'eq', True),),
            summary='Ada told Ben what the box held'
        ),
        scene(
            'request_lend_marble', 'Borrowed Treasure', ('ben',),
            when=(
                C('box.open', 'eq', True),
                C('box.contents', 'eq', 'marble'),
                C('ben.knows.marble.owner', 'eq', 'ben'),
                C('ben.agreement', 'eq', 'unagreed'),
            ),
            set_values={'ben.agreement': 'lend'},
            summary='Ben asked to lend the red marble proudly',
            pivotal=True
        ),
        transfer(
            'return_marble', 'ben', 'sister', 'marble',
            when=(
                C('box.open', 'eq', True),
                C('box.contents', 'eq', 'marble'),
                C('ben.knows.marble.owner', 'eq', 'ben'),
                C('ben.agreement', 'eq', 'unagreed'),
            ),
            summary='Ben returned the red marble to his sister'
        ),
        scene(
            'offer_button', 'Magpie Bargain', ('pip', 'ada'),
            when=(
                C('box.open', 'eq', True),
                C('box.contents', 'eq', 'button'),
                C('ada.knows.box.contents', 'eq', 'button'),
                C('pip.knows.button.owner', 'eq', 'pip'),
                C('button.owner', 'eq', 'pip'),
                C('key.owner', 'eq', 'ada'),
            ),
            set_values={
                'button.owner': 'ada',
                'key.owner': 'pip',
                'pip.motive': 'share',
            },
            summary='Pip traded the blue button for the brass key',
            pivotal=True
        ),
        scene(
            'arrange_trusted', 'Curation', ('ada', 'ben'),
            when=(
                C('box.open', 'eq', True),
                C('box.contents', 'eq', 'marble'),
                C('ben.agreement', 'in', ('lend', 'return')),
            ),
            set_values={'display.status': 'trusted'},
            summary='Ada arranged the marble with its borrowing story'
        ),
        scene(
            'arrange_dazzling', 'Curation', ('ada', 'pip'),
            when=(
                C('box.open', 'eq', True),
                C('box.contents', 'eq', 'button'),
                C('button.owner', 'eq', 'ada'),
                C('key.owner', 'eq', 'pip'),
                C('pip.motive', 'eq', 'share'),
            ),
            set_values={'display.status': 'dazzling'},
            summary='Ada arranged the button and key as a dazzling display'
        ),
        scene(
            'arrange_surprising', 'Curation', ('ada', 'pip'),
            when=(
                C('box.open', 'eq', True),
                C('box.contents', 'eq', 'button'),
                C('button.owner', 'eq', 'pip'),
                C('pip.motive', 'eq', 'keep'),
            ),
            set_values={'display.status': 'surprising'},
            summary='Ada made a display around Pip’s unwilling blue button'
        ),
        scene(
            'write_invitation', 'Invitation', ('ada',),
            when=(
                C('card.owner', 'eq', 'ada'),
                C('card.status', 'eq', 'blank'),
            ),
            set_values={'card.status': 'written'},
            summary='Ada wrote an invitation for the library keeper'
        ),
        transfer(
            'invite_keeper', 'ada', 'ben', 'card',
            when=(
                C('card.owner', 'eq', 'ada'),
                C('card.status', 'eq', 'written'),
            ),
            summary='Ada handed Ben the museum invitation'
        ),
        scene(
            'greet_visitor', 'Greeting', ('ben',),
            when=(
                C('visitor.arrived', 'eq', True),
                C('visitor.greeted', 'eq', False),
                C('card.owner', 'eq', 'ben'),
            ),
            set_values={'visitor.greeted': True},
            summary='Ben greeted the arriving library keeper'
        ),
        observe(
            'inspect_expectation', 'ben', 'visitor.expectation',
            requires=(
                C('visitor.arrived', 'eq', True),
                C('visitor.greeted', 'eq', True),
            ),
            summary='Ben noticed what sort of museum the keeper expected'
        ),
        tell(
            'tell_keeper_expectation', 'ben', 'ada', 'visitor.expectation',
            when=(
                C('ben.knows.visitor.expectation', 'ne', None),
                C('visitor.greeted', 'eq', True),
            ),
            summary='Ben told Ada what the keeper expected'
        ),
        scene(
            'perform_whisper_tour', 'Performance', ('ada',),
            when=(
                C('visitor.greeted', 'eq', True),
                C('display.status', 'in', ('trusted', 'dazzling')),
                C('ada.knows.visitor.expectation', 'eq', 'quiet'),
            ),
            set_values={'display.mode': 'whisper'},
            summary='Ada performed a whisper tour of the small wonders'
        ),
        scene(
            'perform_button_concert', 'Performance', ('pip',),
            when=(
                C('visitor.greeted', 'eq', True),
                C('display.status', 'eq', 'surprising'),
                C('pip.motive', 'eq', 'keep'),
                C('visitor.expectation', 'eq', 'quiet'),
            ),
            set_values={'display.mode': 'concert'},
            summary='Pip performed a ridiculous button concert'
        ),
        scene(
            'visitor_delights', 'Visitor Response', ('visitor',),
            when=(
                C('display.mode', 'eq', 'whisper'),
                C('visitor.mood', 'eq', 'unknown'),
            ),
            set_values={'visitor.mood': 'delighted'},
            summary='The keeper smiled at the gentle tour'
        ),
        scene(
            'visitor_puzzles', 'Visitor Response', ('visitor',),
            when=(
                C('display.mode', 'eq', 'concert'),
                C('visitor.mood', 'eq', 'unknown'),
            ),
            set_values={'visitor.mood': 'puzzled'},
            summary='The keeper blinked at the button concert'
        ),
    )

    return WorldSpec(
        'The Museum of Small Things',
        entities,
        initial,
        scenes,
        goal=(
            C('display.status', 'ne', 'empty'),
            C('visitor.mood', 'ne', 'unknown'),
        ),
        rules=(),
        labels={
            'box.contents': 'what the box held',
            'display.status': 'the display',
            'display.mode': 'the kind of tour',
            'visitor.mood': 'the keeper’s mood',
            'ben.agreement': 'Ben’s marble decision',
            'pip.motive': 'Pip’s button plan',
        },
        prune=True,
        premise_keys=(
            'box.contents',
            'card.status',
            'visitor.expectation',
            'ben.agreement',
        ),
        outcome_keys=(
            'display.status',
            'display.mode',
            'visitor.mood',
        ),
    )



