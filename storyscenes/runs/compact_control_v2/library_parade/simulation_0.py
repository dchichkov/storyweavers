import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)
    mode = seed % 3

    entities = {
        'mayor': {'name': 'Mayor Mallow', 'kind': 'person'},
        'juniper': {'name': 'Juniper', 'kind': 'child'},
        'bram': {'name': 'Bram', 'kind': 'person'},
        'cart': {'name': 'Pip the library cart', 'kind': 'prop'},
        'banner': {'name': 'enormous banner', 'kind': 'prop'},
        'bell': {'name': 'silver bell', 'kind': 'prop'},
        'lane': {'name': 'the narrow lane', 'kind': 'place'},
        'square': {'name': 'the town square', 'kind': 'place'},
        'guest': {'name': 'the quiet guests', 'kind': 'group'},
        'audience': {'name': 'the audience', 'kind': 'group'},
        'world': {'name': 'parade world', 'kind': 'system'},
    }

    cargo = 'empty' if mode == 0 else 'books'
    initial = {
        'mayor.case': mode,
        'mayor.boast': 'grand',
        'mayor.order': 'cover' if mode == 1 else 'none',
        'mayor.belief': 'decorations' if mode == 1 else 'unknown',
        'mayor.knows.lane.open': None,
        'mayor.knows.cart.cargo': None,

        'juniper.motive': 'readers',
        'juniper.knows.cart.cargo': None,
        'juniper.knows.cart.location': None,
        'juniper.knows.lane.open': None,
        'juniper.knows.audience.invitation': None,
        'juniper.knows.bram.promise': None,

        'bram.promise': 'bell_guest' if mode == 2 else 'none',
        'bram.knows.audience.invitation': None,
        'bram.knows.cart.cargo': None,

        'cart.cargo': cargo,
        'cart.owner': 'bram',
        'cart.location': 'library',
        'cart.decorated': 'none',

        'banner.owner': 'bram',
        'bell.owner': 'bram',
        'lane.open': True,
        'square.open': True,

        'guest.invitation': 'quiet' if mode == 2 else 'none',
        'audience.response': 'none',
        'audience.quiet_guest': 'invited' if mode == 2 else 'none',
        'audience.books_reading': False,
        'audience.book_distribution': False,
    }

    scenes = (
        observe(
            'inspect_cart', 'juniper', 'cart.cargo',
            requires=(C('juniper.motive', 'eq', 'readers'),),
            summary='Juniper peered at the cart shelves'
        ),
        observe(
            'inspect_lane', 'juniper', 'lane.open',
            requires=(C('mayor.case', 'eq', 0),),
            summary='Juniper noticed the narrow lane'
        ),
        tell(
            'tell_lane', 'juniper', 'mayor', 'lane.open',
            when=(C('juniper.knows.lane.open', 'eq', True),),
            summary='Juniper told Mayor Mallow about the lane'
        ),
        scene(
            'load_books', 'Loading', ('juniper', 'bram'),
            when=(
                C('mayor.case', 'eq', 0),
                C('juniper.knows.cart.cargo', 'eq', 'empty'),
                C('cart.cargo', 'eq', 'empty'),
            ),
            set_values={'cart.cargo': 'books'},
            summary='Juniper and Bram loaded picture books'
        ),
        scene(
            'cover_books', 'Misunderstanding', ('mayor', 'juniper'),
            when=(
                C('mayor.case', 'eq', 1),
                C('juniper.knows.cart.cargo', 'eq', 'books'),
                C('mayor.order', 'eq', 'cover'),
                C('cart.cargo', 'eq', 'books'),
            ),
            set_values={'cart.cargo': 'covered_books'},
            summary='The picture-book bundles were covered as party decorations'
        ),
        scene(
            'reveal_books', 'Discovery', ('juniper', 'mayor'),
            when=(
                C('mayor.case', 'eq', 1),
                C('cart.cargo', 'eq', 'covered_books'),
                C('juniper.knows.cart.cargo', 'eq', 'books'),
            ),
            set_values={
                'cart.cargo': 'books',
                'mayor.belief': 'books',
            },
            pivotal=True,
            summary='Juniper opened a bundle and revealed picture books'
        ),
        observe(
            'inspect_invitation', 'juniper', 'audience.invitation',
            requires=(C('mayor.case', 'eq', 2),),
            summary='Juniper checked who had been invited'
        ),
        observe(
            'inspect_bell', 'juniper', 'bram.promise',
            requires=(C('mayor.case', 'eq', 2),),
            summary='Juniper learned about Bram’s bell promise'
        ),
        tell(
            'tell_conflict', 'juniper', 'bram', 'audience.invitation',
            when=(
                C('juniper.knows.audience.invitation', 'eq', 'quiet'),
                C('juniper.knows.bram.promise', 'eq', 'bell_guest'),
            ),
            summary='Juniper told Bram that quiet guests were coming'
        ),
        transfer(
            'give_bell', 'bram', 'guest', 'bell',
            when=(
                C('mayor.case', 'eq', 2),
                C('bram.promise', 'eq', 'bell_guest'),
                C('bram.knows.audience.invitation', 'eq', 'quiet'),
                C('juniper.knows.bram.promise', 'eq', 'bell_guest'),
            ),
            set_values={'bram.promise': 'settled'},
            pivotal=True,
            summary='Bram gave the bell to the distant guest'
        ),
        transfer(
            'offer_banner', 'bram', 'juniper', 'banner',
            when=(
                C('banner.owner', 'eq', 'bram'),
                C('cart.cargo', 'eq', 'books'),
            ),
            summary='Bram handed Juniper the enormous banner'
        ),
        scene(
            'decorate_cart', 'Decorating', ('juniper', 'bram'),
            when=(
                C('cart.cargo', 'eq', 'books'),
                C('banner.owner', 'eq', 'juniper'),
                C('cart.decorated', 'eq', 'none'),
                C('mayor.case', 'in', (0, 1)),
            ),
            set_values={'cart.decorated': 'banner'},
            summary='Juniper and Bram tied the banner to the cart'
        ),
        scene(
            'silent_ribbons', 'Silent Parade', ('juniper', 'bram'),
            when=(
                C('mayor.case', 'eq', 2),
                C('cart.cargo', 'eq', 'books'),
                C('banner.owner', 'eq', 'juniper'),
                C('bram.promise', 'eq', 'settled'),
                C('cart.decorated', 'eq', 'none'),
            ),
            set_values={
                'cart.decorated': 'banner',
                'audience.quiet_guest': 'included',
            },
            summary='Bram and Juniper made a silent ribbon parade'
        ),
        scene(
            'book_rain', 'Book Parade', ('mayor', 'juniper'),
            when=(
                C('mayor.case', 'eq', 1),
                C('cart.cargo', 'eq', 'books'),
                C('mayor.belief', 'eq', 'books'),
            ),
            set_values={'audience.book_distribution': True},
            summary='Mayor Mallow chose a book-sharing parade'
        ),
        scene(
            'roll_lane', 'Movement', ('juniper', 'bram'),
            when=(
                C('mayor.case', 'eq', 0),
                C('cart.cargo', 'eq', 'books'),
                C('cart.decorated', 'eq', 'banner'),
                C('mayor.knows.lane.open', 'eq', True),
            ),
            set_values={'cart.location': 'lane'},
            summary='The cart rolled into the narrow lane'
        ),
        scene(
            'roll_square_books', 'Movement', ('juniper', 'bram'),
            when=(
                C('mayor.case', 'eq', 1),
                C('cart.cargo', 'eq', 'books'),
                C('cart.decorated', 'eq', 'banner'),
                C('audience.book_distribution', 'eq', True),
            ),
            set_values={'cart.location': 'square'},
            summary='The cart rolled into the town square'
        ),
        scene(
            'roll_square_quiet', 'Movement', ('juniper', 'bram'),
            when=(
                C('mayor.case', 'eq', 2),
                C('cart.cargo', 'eq', 'books'),
                C('cart.decorated', 'eq', 'banner'),
                C('audience.quiet_guest', 'eq', 'included'),
            ),
            set_values={'cart.location': 'square'},
            summary='The cart rolled quietly into the square'
        ),
        scene(
            'lane_response', 'Audience', ('audience',),
            when=(
                C('cart.location', 'eq', 'lane'),
                C('cart.cargo', 'eq', 'books'),
            ),
            set_values={'audience.response': 'delighted'},
            summary='Readers in the lane welcomed the book parade'
        ),
        scene(
            'reading_response', 'Audience', ('audience',),
            when=(
                C('cart.location', 'eq', 'square'),
                C('audience.book_distribution', 'eq', True),
            ),
            set_values={
                'audience.response': 'reading',
                'audience.books_reading': True,
            },
            summary='Children sat on the square stones and began reading'
        ),
        scene(
            'quiet_response', 'Audience', ('audience',),
            when=(
                C('cart.location', 'eq', 'square'),
                C('audience.quiet_guest', 'eq', 'included'),
            ),
            set_values={'audience.response': 'welcoming'},
            summary='The quiet guests welcomed the silent parade'
        ),
    )

    return WorldSpec(
        'The Library Cart Parade',
        entities,
        initial,
        scenes,
        goal=(
            C('cart.decorated', 'eq', 'banner'),
            C('cart.location', 'in', ('lane', 'square')),
            C('audience.response', 'ne', 'none'),
        ),
        rules=(),
        labels={
            'cart.cargo': 'the cart’s shelves',
            'cart.location': 'the cart’s location',
            'cart.decorated': 'the cart’s decoration',
            'audience.response': 'the audience’s response',
            'audience.quiet_guest': 'the quiet guests’ place in the parade',
        },
        prune=True,
        premise_keys=(
            'cart.cargo',
            'cart.location',
            'mayor.knows.lane.open',
            'bram.promise',
        ),
        outcome_keys=(
            'cart.location',
            'cart.cargo',
            'audience.response',
        ),
    )
