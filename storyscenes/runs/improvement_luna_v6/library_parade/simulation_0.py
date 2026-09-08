import random
from runtime import WorldSpec, Condition as C, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)
    start = rng.randrange(3)

    entities = {
        'mayor': {'name': 'Mayor Mallow', 'kind': 'adult'},
        'nia': {'name': 'Nia', 'kind': 'child'},
        'tuck': {'name': 'Tuck', 'kind': 'adult'},
        'cart': {'name': 'wooden cart', 'kind': 'prop'},
        'banner': {'name': 'parade banner', 'kind': 'prop'},
        'books': {'name': 'library books', 'kind': 'prop'},
        'bell': {'name': 'brass bell', 'kind': 'prop'},
    }

    if start == 0:
        owner = 'mayor'
        location = 'parade_lane'
        loaded = False
        mayor_want = 'float'
    elif start == 1:
        owner = 'tuck'
        location = 'neighborhood_stop'
        loaded = True
        mayor_want = 'bookmobile'
    else:
        owner = 'nia'
        location = 'library_door'
        loaded = True
        mayor_want = 'reading_room'

    initial = {
        'mayor.memes.Boast': 2,
        'mayor.want': mayor_want,
        'mayor.knows.cart.loaded': None,
        'mayor.knows.cart.location': None,
        'mayor.knows.books.waiting': None,
        'mayor.knows.cart.shelves': None,
        'mayor.knows.cart.shelves_open': None,
        'nia.memes.Care': 2,
        'nia.want': 'deliver',
        'nia.invited_children': False,
        'nia.knows.cart.loaded': None,
        'nia.knows.cart.location': None,
        'nia.knows.books.waiting': None,
        'nia.knows.mayor.want': None,
        'tuck.memes.Craft': 2,
        'tuck.knows.cart.shelves': True,
        'tuck.knows.cart.shelves_open': True,
        'tuck.knows.mayor.want': None,
        'tuck.knows.cart.loaded': None,
        'cart.owner': owner,
        'cart.location': location,
        'cart.loaded': loaded,
        'cart.decorated': False,
        'cart.mode': 'none',
        'cart.performer': None,
        'cart.shelves': True,
        'banner.owner': 'mayor',
        'banner.attached': False,
        'books.waiting': True,
        'bell.owner': 'tuck',
        'bell.rung': False,
    }

    scenes = (
        scene(
            'invite_square', 'Invitation', ('nia', 'mayor', 'tuck'),
            when=(C('nia.invited_children', 'eq', False),),
            set_values={'nia.invited_children': True},
            summary='Nia invited everyone to meet in the library square',
            weight=1.2,
        ),
        observe(
            'look_cart', 'mayor', 'cart.loaded',
            requires=(
                C('nia.invited_children', 'eq', True),
                C('mayor.knows.cart.loaded', 'eq', None),
            ),
            summary='Mallow looked into the cart',
        ),
        observe(
            'look_books', 'mayor', 'books.waiting',
            requires=(
                C('nia.invited_children', 'eq', True),
                C('mayor.knows.books.waiting', 'eq', None),
            ),
            summary='Mallow noticed the waiting books',
        ),
        observe(
            'learn_mayor_plan', 'tuck', 'mayor.want',
            requires=(
                C('nia.invited_children', 'eq', True),
                C('tuck.knows.mayor.want', 'eq', None),
            ),
            summary='Tuck listened for Mallow’s plan',
        ),
        tell(
            'tell_cart_purpose', 'nia', 'mayor', 'books.waiting',
            when=(
                C('nia.knows.books.waiting', 'eq', True),
                C('mayor.knows.books.waiting', 'eq', None),
            ),
            summary='Nia told Mallow that the books were waiting for children',
            pivotal=True,
        ),
        tell(
            'tell_folding_shelves', 'tuck', 'mayor', 'cart.shelves',
            when=(
                C('tuck.knows.cart.shelves', 'eq', True),
                C('mayor.knows.cart.shelves', 'eq', None),
            ),
            summary='Tuck revealed the cart’s hidden folding shelves',
            pivotal=True,
        ),
        transfer(
            'transfer_cart_to_nia', 'tuck', 'nia', 'cart',
            when=(
                C('cart.owner', 'eq', 'tuck'),
                C('cart.loaded', 'eq', True),
                C('cart.location', 'eq', 'neighborhood_stop'),
            ),
            summary='Tuck handed the loaded cart to Nia',
        ),
        scene(
            'load_books', 'Loading', ('nia',),
            when=(
                C('cart.owner', 'eq', 'nia'),
                C('cart.location', 'eq', 'library_door'),
                C('cart.loaded', 'eq', False),
            ),
            set_values={'cart.loaded': True},
            summary='Nia loaded the waiting books',
        ),
        scene(
            'unload_books', 'Unloading', ('nia',),
            when=(
                C('cart.owner', 'eq', 'nia'),
                C('cart.loaded', 'eq', True),
                C('mayor.knows.books.waiting', 'eq', True),
                C('mayor.want', 'eq', 'reading_room'),
            ),
            set_values={'cart.loaded': False},
            summary='Nia lifted the books out for a cozy gathering',
        ),
        scene(
            'attach_banner', 'Decoration', ('mayor',),
            when=(
                C('cart.owner', 'eq', 'mayor'),
                C('cart.loaded', 'eq', False),
                C('mayor.knows.cart.loaded', 'eq', False),
                C('mayor.want', 'eq', 'float'),
                C('banner.attached', 'eq', False),
            ),
            set_values={'banner.attached': True, 'cart.decorated': True,
                        'cart.mode': 'float'},
            summary='Mallow attached the banner to make a grand float',
        ),
        scene(
            'fold_shelves', 'Revelation', ('tuck', 'mayor'),
            when=(
                C('cart.loaded', 'eq', False),
                C('mayor.want', 'eq', 'reading_room'),
                C('mayor.knows.books.waiting', 'eq', True),
                C('mayor.knows.cart.shelves', 'eq', True),
                C('cart.mode', 'eq', 'none'),
            ),
            set_values={'cart.mode': 'reading_room'},
            summary='The cart unfolded into a tiny reading room',
            pivotal=True,
        ),
        scene(
            'move_cart_to_square', 'Moving', ('nia', 'tuck'),
            when=(
                C('nia.invited_children', 'eq', True),
                C('cart.location', 'in', ('library_door', 'neighborhood_stop')),
            ),
            set_values={'cart.location': 'parade_lane'},
            summary='The friends rolled the cart to the parade lane',
        ),
        scene(
            'move_cart_to_neighborhood', 'Moving', ('nia',),
            when=(
                C('cart.owner', 'eq', 'nia'),
                C('cart.loaded', 'eq', True),
                C('cart.location', 'eq', 'parade_lane'),
            ),
            set_values={'cart.location': 'neighborhood_stop',
                        'cart.mode': 'bookmobile'},
            summary='Nia rolled the bookmobile to the neighborhood stop',
        ),
        scene(
            'invite_children', 'Sharing', ('nia',),
            when=(
                C('cart.location', 'in', ('parade_lane', 'neighborhood_stop')),
                C('nia.invited_children', 'eq', True),
                C('cart.mode', 'eq', 'reading_room'),
            ),
            set_values={'nia.invited_children': True},
            increments={'nia.memes.Care': 1},
            summary='Nia opened the reading room to the children',
            pivotal=True,
        ),
        scene(
            'ring_bell', 'Performance', ('tuck',),
            when=(
                C('bell.owner', 'eq', 'tuck'),
                C('bell.rung', 'eq', False),
                C('cart.performer', 'ne', None),
            ),
            set_values={'bell.rung': True},
            summary='Tuck rang the brass bell',
        ),
        scene(
            'perform_big_loop', 'Performance', ('mayor',),
            when=(
                C('cart.mode', 'eq', 'float'),
                C('cart.location', 'eq', 'parade_lane'),
                C('cart.decorated', 'eq', True),
            ),
            set_values={'cart.performer': 'mayor'},
            summary='Mallow performed a towering parade loop',
        ),
        scene(
            'perform_book_route', 'Performance', ('nia',),
            when=(
                C('cart.mode', 'eq', 'bookmobile'),
                C('cart.location', 'eq', 'neighborhood_stop'),
                C('cart.loaded', 'eq', True),
                C('nia.invited_children', 'eq', True),
            ),
            set_values={'cart.performer': 'nia'},
            summary='Nia performed a book route for neighborhood children',
        ),
        scene(
            'perform_reading_room', 'Performance', ('nia',),
            when=(
                C('cart.mode', 'eq', 'reading_room'),
                C('cart.location', 'eq', 'parade_lane'),
                C('nia.invited_children', 'eq', True),
            ),
            set_values={'cart.performer': 'nia'},
            summary='Nia performed a story inside the traveling reading room',
        ),
    )

    return WorldSpec(
        'The Library Parade and the Cart with Three Jobs',
        entities,
        initial,
        scenes,
        goal=(C('cart.mode', 'in', ('float', 'bookmobile', 'reading_room')), C('cart.performer', 'ne', None)),
        rules=(),
        labels={
            'cart.mode': 'the cart’s job',
            'cart.location': 'the cart’s place',
            'cart.owner': 'the cart’s keeper',
            'cart.performer': 'the performer',
            'cart.loaded': 'the loaded books',
            'banner.attached': 'the high banner',
            'bell.rung': 'the ringing bell',
        },
        prune=True,
        premise_keys=('cart.owner', 'cart.location', 'cart.loaded', 'mayor.want'),
        outcome_keys=('cart.mode', 'cart.location', 'cart.performer'),
    )



