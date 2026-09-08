import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)

    entities = {
        'ada': {'name': 'Ada', 'kind': 'child'},
        'pip': {'name': 'Pip', 'kind': 'squirrel'},
        'nia': {'name': 'Nia', 'kind': 'neighbor'},
        'button': {'name': 'cinnamon button', 'kind': 'pastry'},
        'berryjar': {'name': 'berry jam jar', 'kind': 'prop'},
        'label': {'name': 'paper label', 'kind': 'prop'},
        'basket': {'name': 'pastry basket', 'kind': 'prop'},
        'stall': {'name': 'bakery stall', 'kind': 'place'},
    }

    mark = rng.choice(('cinnamon', 'cinnamon', 'pepper'))
    label_text = rng.choice(('cinnamon', 'pepper'))
    promise = rng.choice(('trade', 'share', 'brave_taste'))

    initial = {
        'ada.promise': promise,
        'ada.agreement': None,
        'ada.knows.label.text': None,
        'ada.knows.button.mark': None,

        'pip.agreement': None,
        'pip.knows.label.text': None,
        'pip.knows.button.mark': None,

        'nia.belief': label_text,
        'nia.agreement': None,
        'nia.content': False,
        'nia.knows.label.text': None,
        'nia.knows.button.mark': None,

        'button.mark': mark,
        'button.owner': 'ada',
        'button.location': 'stall',
        'button.shared': False,

        'berryjar.owner': 'nia',
        'berryjar.open': False,
        'berryjar.location': 'stall',

        'label.text': label_text,
        'label.attached': False,
        'label.location': 'stall',

        'basket.owner': 'ada',
        'basket.location': 'stall',
        'stall.open': True,
    }

    scenes = (
        scene(
            'attach_label', 'Labeling', ('pip', 'label', 'button'),
            when=(C('label.attached', 'eq', False),),
            set_values={'label.attached': True},
            summary='Pip pinned his chosen label to the pastry',
        ),
        observe(
            'inspect_label', 'ada', 'label.text',
            requires=(
                C('label.attached', 'eq', True),
                C('ada.knows.label.text', 'eq', None),
            ),
            summary='Ada read the label',
        ),
        observe(
            'pip_observe_mark', 'pip', 'button.mark',
            requires=(
                C('label.attached', 'eq', True),
                C('pip.knows.button.mark', 'eq', None),
            ),
            summary='Pip inspected the pastry mark',
        ),
        tell(
            'tell_mark_ada', 'pip', 'ada', 'button.mark',
            when=(
                C('pip.knows.button.mark', 'ne', None),
                C('ada.knows.button.mark', 'eq', None),
            ),
            summary='Pip told Ada what mark was on the pastry',
        ),
        tell(
            'tell_mark_nia', 'ada', 'nia', 'button.mark',
            when=(
                C('ada.knows.button.mark', 'ne', None),
                C('nia.knows.button.mark', 'eq', None),
            ),
            summary='Ada told Nia what she had baked',
        ),
        scene(
            'pip_defends_label', 'Pride', ('pip',),
            when=(
                C('label.attached', 'eq', True),
                C('pip.knows.button.mark', 'ne', None),
                C('label.text', 'ne', 'cinnamon'),
            ),
            set_values={'pip.agreement': 'defend_label'},
            summary='Pip proudly defended the label',
        ),
        scene(
            'correct_label', 'Labeling', ('ada', 'label'),
            when=(
                C('label.attached', 'eq', True),
                C('ada.knows.button.mark', 'ne', None),
                C('ada.knows.label.text', 'ne', None),
                C('label.text', 'ne', 'cinnamon'),
            ),
            copies={'label.text': 'ada.knows.button.mark'},
            summary='Ada replaced the mistaken label',
        ),
        scene(
            'offer_jar', 'Exchange', ('nia', 'berryjar'),
            when=(
                C('berryjar.owner', 'eq', 'nia'),
                C('nia.agreement', 'eq', None),
            ),
            set_values={'nia.agreement': 'jar_offer'},
            summary='Nia offered her berry jam',
        ),
        scene(
            'choose_share', 'Agreement', ('ada', 'nia'),
            when=(
                C('ada.promise', 'eq', 'share'),
                C('nia.agreement', 'eq', 'jar_offer'),
                C('ada.agreement', 'eq', None),
            ),
            set_values={'ada.agreement': 'share'},
            summary='Ada chose to make the pastry a shared treat',
            pivotal=True,
        ),
        scene(
            'accept_brave_taste', 'Agreement', ('ada', 'nia', 'pip'),
            when=(
                C('ada.promise', 'eq', 'brave_taste'),
                C('pip.agreement', 'eq', 'defend_label'),
                C('button.mark', 'eq', 'pepper'),
                C('nia.agreement', 'eq', 'jar_offer'),
                C('ada.agreement', 'eq', None),
            ),
            set_values={'ada.agreement': 'brave_taste'},
            summary='Ada accepted Pip’s daring tasting idea',
            pivotal=True,
        ),
        scene(
            'open_jar', 'Exchange', ('nia', 'berryjar'),
            when=(
                C('berryjar.owner', 'eq', 'nia'),
                C('berryjar.open', 'eq', False),
                C('nia.agreement', 'eq', 'jar_offer'),
            ),
            set_values={'berryjar.open': True},
            summary='Nia opened the berry jam',
        ),
        transfer(
            'give_jar', 'nia', 'ada', 'berryjar',
            when=(
                C('berryjar.owner', 'eq', 'nia'),
                C('berryjar.open', 'eq', True),
                C('ada.promise', 'in', ('trade', 'brave_taste')),
            ),
            summary='Nia handed Ada the open jam jar',
        ),
        transfer(
            'trade_button', 'ada', 'nia', 'button',
            when=(
                C('button.owner', 'eq', 'ada'),
                C('berryjar.owner', 'eq', 'ada'),
                C('berryjar.open', 'eq', True),
                C('ada.promise', 'in', ('trade', 'brave_taste')),
                C('nia.knows.button.mark', 'ne', None),
            ),
            summary='Ada traded the pastry for the jam',
        ),
        scene(
            'taste_sweet', 'Tasting', ('nia', 'button'),
            when=(
                C('button.owner', 'eq', 'nia'),
                C('button.mark', 'eq', 'cinnamon'),
                C('berryjar.open', 'eq', True),
                C('nia.knows.button.mark', 'eq', 'cinnamon'),
                C('nia.content', 'eq', False),
            ),
            set_values={
                'nia.content': 'sweet_trade',
                'button.shared': False,
            },
            summary='Nia tasted the cinnamon button',
            pivotal=True,
        ),
        scene(
            'taste_savory', 'Tasting', ('nia', 'button'),
            when=(
                C('button.owner', 'eq', 'nia'),
                C('button.mark', 'eq', 'pepper'),
                C('berryjar.open', 'eq', True),
                C('ada.agreement', 'eq', 'brave_taste'),
                C('nia.content', 'eq', False),
            ),
            set_values={
                'nia.content': 'savory_surprise',
                'button.shared': False,
            },
            summary='Nia tasted the pepper button with berry jam',
            pivotal=True,
        ),
        scene(
            'share_button', 'Tasting', ('ada', 'nia', 'pip', 'button'),
            when=(
                C('button.owner', 'eq', 'ada'),
                C('berryjar.open', 'eq', True),
                C('ada.agreement', 'eq', 'share'),
                C('nia.content', 'eq', False),
            ),
            set_values={
                'nia.content': 'shared_treat',
                'button.shared': True,
            },
            summary='Ada broke the pastry into shared pieces',
            pivotal=True,
        ),
        scene(
            'final_bow', 'Celebration', ('pip', 'label'),
            when=(
                C('nia.content', 'in',
                  ('sweet_trade', 'savory_surprise', 'shared_treat')),
                C('label.text', 'eq', 'button.mark'),
                C('pip.agreement', 'ne', 'label_celebrated'),
            ),
            set_values={'pip.agreement': 'label_celebrated'},
            summary='Pip celebrated the true label',
        ),
    )

    return WorldSpec(
        'The Cinnamon Button Exchange',
        entities,
        initial,
        scenes,
        goal=(
            C('nia.content', 'in',
              ('sweet_trade', 'savory_surprise', 'shared_treat')),
        ),
        rules=(),
        labels={
            'button.mark': 'the pastry’s flavor',
            'label.text': 'the label’s word',
            'nia.content': 'Nia’s tasting result',
            'button.owner': 'the pastry’s owner',
            'pip.agreement': 'Pip’s final agreement',
        },
        prune=True,
        premise_keys=(
            'button.mark',
            'label.text',
            'nia.belief',
            'ada.promise',
        ),
        outcome_keys=(
            'button.owner',
            'nia.content',
            'pip.agreement',
            'button.shared',
        ),
    )

