import random
from runtime import WorldSpec, Condition as C, Rule, scene, observe, tell, transfer


def build(seed):
    rng = random.Random(seed)

    entities = {
        'mina': {'name': 'Mina', 'kind': 'child librarian'},
        'tuck': {'name': 'Tuck', 'kind': 'cart builder'},
        'bramble': {'name': 'Mayor Bramble', 'kind': 'mayor'},
        'cart': {'name': 'the book cart', 'kind': 'prop'},
        'books': {'name': 'the book bundle', 'kind': 'prop'},
        'sash': {'name': 'the red parade sash', 'kind': 'prop'},
        'bell': {'name': 'the brass bell', 'kind': 'prop'},
        'prize': {'name': 'the golden megaphone', 'kind': 'prop'},
        'steps': {'name': 'the library steps', 'kind': 'place'},
        'homes': {'name': 'the readers’ homes', 'kind': 'place'},
    }

    motive = rng.choice(('biggest', 'biggest', 'useful'))
    audience_location = rng.choice((None, 'square', 'homes'))
    judge_belief = rng.choice(('mayor', 'mayor', 'readers'))
    load_style = rng.choice(('tower', 'matched'))
    bell_attached = rng.choice((False, False, True))
    crowd = rng.choice(('small', 'small', 'busy'))
    bundle = rng.choice(('moon tales', 'puzzle books', 'dragon dictionaries'))

    initial = {
        'mina.location': 'library',
        'mina.memes.ReadersFirst': 2,
        'mina.knows.audience_location': audience_location,
        'mina.knows.books.waiting': None,
        'mina.knows.bramble.motive': None,

        'tuck.location': 'library',
        'tuck.memes.PrideInWheels': 2,
        'tuck.belief.judge': judge_belief,
        'tuck.knows.bramble.motive': None,
        'tuck.knows.books.waiting': None,

        'bramble.location': 'library',
        'bramble.memes.Boastfulness': 2,
        'bramble.motive': motive,
        'bramble.invitation': False,
        'bramble.knows.books.waiting': None,
        'bramble.knows.steps.crowd': None,
        'bramble.agreement': False,

        'cart.owner': 'tuck',
        'cart.location': 'library',
        'cart.loaded': False,
        'cart.load_style': load_style,
        'cart.sash': False,
        'cart.bell': bell_attached,
        'cart.display_ready': False,

        'books.owner': 'mina',
        'books.location': 'library',
        'books.bundle': bundle,
        'books.waiting': True,
        'books.delivered': False,

        'sash.owner': 'bramble',
        'sash.location': 'library',

        'bell.owner': 'tuck',
        'bell.location': 'library',

        'prize.owner': 'bramble',
        'prize.location': 'library',

        'steps.crowd': crowd,
        'homes.readers_waiting': True,

        'parade.kind': 'none',
    }

    scenes = (
        scene(
            'tie_sash', 'Invitation', ('bramble',),
            when=(
                C('bramble.invitation', 'eq', False),
                C('sash.owner', 'eq', 'bramble'),
                C('cart.location', 'eq', 'library'),
            ),
            set_values={
                'bramble.invitation': True,
                'cart.sash': True,
                'sash.owner': 'cart',
                'sash.location': 'cart',
            },
            summary='Mayor Bramble tied the red sash to the cart and announced a golden-megaphone prize.',
        ),
        observe(
            'hear_boast', 'mina', 'bramble.motive',
            requires=(C('bramble.invitation', 'eq', True),),
            summary='Mina heard what Mayor Bramble hoped the parade would become.',
        ),
        observe(
            'tuck_hears_boast', 'tuck', 'bramble.motive',
            requires=(C('bramble.invitation', 'eq', True),),
            summary='Tuck listened closely to the mayor’s parade announcement.',
        ),
        observe(
            'inspect_waiting_books', 'mina', 'books.waiting',
            requires=(
                C('bramble.invitation', 'eq', True),
                C('books.location', 'eq', 'library'),
            ),
            summary='Mina found the books still waiting for their readers.',
        ),
        tell(
            'tell_tuck_about_readers', 'mina', 'tuck', 'books.waiting',
            requires=(
                C('mina.knows.books.waiting', 'eq', True),
                C('tuck.location', 'eq', 'library'),
            ),
            summary='Mina told Tuck that readers were waiting beyond the library.',
        ),
        scene(
            'prepare_for_mayor', 'Misunderstanding', ('tuck',),
            when=(
                C('bramble.invitation', 'eq', True),
                C('tuck.belief.judge', 'eq', 'mayor'),
                C('tuck.knows.bramble.motive', 'eq', 'biggest'),
                C('cart.location', 'eq', 'library'),
            ),
            set_values={'cart.display_ready': True},
            summary='Tuck polished the cart for what he thought was a mayoral judging.',
        ),
        scene(
            'switch_to_matched', 'Choice', ('mina',),
            when=(
                C('mina.knows.books.waiting', 'eq', True),
                C('cart.loaded', 'eq', False),
                C('cart.load_style', 'eq', 'tower'),
            ),
            set_values={'cart.load_style': 'matched'},
            summary='Mina chose reader-sized piles instead of a towering stack.',
        ),
        scene(
            'load_matched_books', 'Sharing', ('mina',),
            when=(
                C('bramble.invitation', 'eq', True),
                C('mina.knows.books.waiting', 'eq', True),
                C('books.owner', 'eq', 'mina'),
                C('cart.location', 'eq', 'library'),
                C('cart.loaded', 'eq', False),
                C('cart.load_style', 'eq', 'matched'),
            ),
            set_values={'cart.loaded': True},
            summary='Mina loaded books chosen for particular waiting readers.',
            pivotal=True,
        ),
        scene(
            'stack_high', 'Performance', ('tuck',),
            when=(
                C('bramble.invitation', 'eq', True),
                C('cart.display_ready', 'eq', True),
                C('cart.location', 'eq', 'library'),
                C('cart.loaded', 'eq', False),
                C('cart.load_style', 'eq', 'tower'),
            ),
            set_values={'cart.loaded': True},
            summary='Tuck stacked the books into a wobbling, splendid tower.',
        ),
        scene(
            'attach_bell', 'Performance', ('tuck',),
            when=(
                C('cart.owner', 'eq', 'tuck'),
                C('cart.location', 'eq', 'library'),
                C('cart.bell', 'eq', False),
                C('bell.owner', 'eq', 'tuck'),
            ),
            set_values={
                'cart.bell': True,
                'bell.owner': 'cart',
                'bell.location': 'cart',
            },
            summary='Tuck clipped the brass bell onto the cart handle.',
        ),
        scene(
            'ring_square', 'Performance', ('tuck', 'bramble'),
            when=(
                C('bramble.invitation', 'eq', True),
                C('cart.sash', 'eq', True),
                C('cart.bell', 'eq', True),
                C('cart.loaded', 'eq', True),
                C('cart.load_style', 'eq', 'tower'),
                C('cart.location', 'eq', 'library'),
            ),
            set_values={
                'cart.location': 'steps',
                'bramble.location': 'steps',
                'parade.kind': 'spectacle',
            },
            summary='The sash streamed as Tuck rang the bell and rolled the towering cart to the square.',
        ),
        scene(
            'turn_to_homes', 'Choice', ('mina', 'tuck'),
            when=(
                C('bramble.invitation', 'eq', True),
                C('mina.knows.books.waiting', 'eq', True),
                C('cart.loaded', 'eq', True),
                C('cart.load_style', 'eq', 'matched'),
                C('cart.location', 'eq', 'library'),
            ),
            set_values={
                'cart.location': 'homes',
                'mina.location': 'homes',
                'tuck.location': 'homes',
                'parade.kind': 'delivery',
            },
            summary='Mina turned the cart down the short lane toward the waiting readers.',
            pivotal=True,
        ),
        scene(
            'deliver_first_book', 'Sharing', ('mina',),
            when=(
                C('parade.kind', 'eq', 'delivery'),
                C('cart.location', 'eq', 'homes'),
                C('books.delivered', 'eq', False),
                C('books.owner', 'eq', 'mina'),
                C('homes.readers_waiting', 'eq', True),
            ),
            set_values={
                'books.delivered': True,
                'books.location': 'homes',
                'cart.loaded': False,
            },
            summary='Mina handed the first waiting reader a book from the rolling cart.',
        ),
        scene(
            'mayor_follows', 'Following', ('bramble',),
            when=(
                C('bramble.invitation', 'eq', True),
                C('bramble.location', 'eq', 'library'),
                C('cart.location', 'in', ('homes', 'steps')),
            ),
            copies={'bramble.location': 'cart.location'},
            summary='Mayor Bramble hurried after the cart, expecting cheers to catch up with him.',
        ),
        observe(
            'discover_small_crowd', 'bramble', 'steps.crowd',
            requires=(
                C('bramble.location', 'in', ('homes', 'steps')),
                C('steps.crowd', 'eq', 'small'),
            ),
            summary='Mayor Bramble noticed that the square had only a very small crowd.',
        ),
        tell(
            'tell_mayor_about_readers', 'mina', 'bramble', 'books.waiting',
            requires=(
                C('mina.knows.books.waiting', 'eq', True),
                C('bramble.knows.steps.crowd', 'eq', 'small'),
            ),
            summary='Mina told Mayor Bramble exactly who was waiting for books.',
        ),
        scene(
            'agree_small_can_be_grand', 'Understanding', ('bramble',),
            when=(
                C('bramble.knows.books.waiting', 'eq', True),
                C('bramble.knows.steps.crowd', 'eq', 'small'),
                C('bramble.agreement', 'eq', False),
            ),
            set_values={'bramble.agreement': True},
            summary='Mayor Bramble decided that a small parade could still arrive grandly.',
            pivotal=True,
        ),
        transfer(
            'give_prize_to_tuck', 'bramble', 'tuck', 'prize',
            requires=(
                C('bramble.agreement', 'eq', True),
                C('books.delivered', 'eq', True),
                C('prize.owner', 'eq', 'bramble'),
            ),
            summary='Mayor Bramble gave Tuck the golden megaphone for the cart’s steady wheels.',
        ),
        transfer(
            'give_prize_to_mina', 'bramble', 'mina', 'prize',
            requires=(
                C('bramble.agreement', 'eq', True),
                C('prize.owner', 'eq', 'bramble'),
                C('cart.location', 'eq', 'library'),
            ),
            summary='Mayor Bramble placed the golden megaphone in Mina’s hands.',
        ),
        scene(
            'quiet_parade', 'Welcome', ('mina', 'tuck', 'bramble'),
            when=(
                C('bramble.agreement', 'eq', True),
                C('prize.owner', 'eq', 'mina'),
                C('cart.sash', 'eq', True),
                C('cart.bell', 'eq', True),
                C('cart.loaded', 'eq', True),
                C('cart.load_style', 'eq', 'matched'),
                C('cart.location', 'eq', 'library'),
            ),
            set_values={
                'cart.location': 'steps',
                'mina.location': 'steps',
                'tuck.location': 'steps',
                'bramble.location': 'steps',
                'parade.kind': 'welcome',
            },
            summary='The cart made a gentle book welcome on the library steps, with one soft bell chime.',
        ),
    )

    rules = (
        Rule(
            'delivered_books_leave_cart',
            must=(C('cart.loaded', 'eq', False),),
            when=(C('books.delivered', 'eq', True),),
        ),
        Rule(
            'welcome_has_mayors_agreement',
            must=(C('bramble.agreement', 'eq', True),),
            when=(C('parade.kind', 'eq', 'welcome'),),
        ),
    )

    return WorldSpec(
        'The Library Parade Cart',
        entities,
        initial,
        scenes,
        goal=(C('parade.kind', 'in', ('spectacle', 'delivery', 'welcome')),),
        rules=rules,
        labels={
            'parade.kind': 'the kind of parade',
            'cart.load_style': 'the cart’s book arrangement',
            'bramble.agreement': 'the mayor’s new agreement',
            'prize.owner': 'the keeper of the golden megaphone',
        },
        prune=True,
        premise_keys=(
            'bramble.motive',
            'mina.knows.audience_location',
            'tuck.belief.judge',
            'cart.load_style',
        ),
        outcome_keys=(
            'parade.kind',
            'books.delivered',
            'prize.owner',
        ),
    )
