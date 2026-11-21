"""Active semantic copy of Terra library round2; original evidence unchanged.

The original retrieval guards remain; the active campaign adds weighted atlas
choices and picture-making consequences. Historical authored evidence is frozen.
"""
from .lexicon import with_shared
from .operations import Change, committed, enabled, can_transfer

from copy import deepcopy
from random import Random

from grammarworlds.world import World, Entity, Fact, Frame, kernel
from grammarworlds.portable.language import Language, load_lexicon


LEXICON = with_shared({
    'names': {},
    'nouns': {
        'whale book': {}, 'moon atlas': {},
        'book trolley': {}, 'mitten': {}, 'star bookmark': {},
        'window nook': {}, 'astronomy shelf': {}, 'high shelf': {},
        'front desk': {}, 'display table': {}, 'trolley station': {},
        'storeroom': {},   'moon': {}, 'whale': {},
          'drawing': {}
    },
    'adjectives': {'moon': {}, 'whale': {}},
    'prepositions': {},
    'adverbs': {},
    'verbs': {
        'show': {'forms': ['show', 'showed', 'shown'], 'valencies': ['V3']},
        'place': {'forms': ['place', 'placed', 'placed'], 'valencies': ['V2']},


        'lend': {'forms': ['lend', 'lent', 'lent'], 'valencies': ['V3']},
        'reserve': {'forms': ['reserve', 'reserved', 'reserved'], 'valencies': ['V2']},
        'check': {'forms': ['check', 'checked', 'checked'], 'valencies': ['V2']},



        'recognize': {'forms': ['recognize', 'recognized', 'recognized'], 'valencies': ['V2']}
    }
})


def _kernel(name, requires=(), adds=(), excludes=()):
    preferences = {
        'return_trolley': (('Care', 0.6), ('Fear', -0.3), ('Trust', 0.1)),
        'return_ladder': (('Care', -0.2), ('Fear', 0.6), ('Trust', 0.1)),
        'checkout_atlas': (('Care', -0.1), ('Fear', 0.1), ('Trust', 0.7))
    }.get(name, (('Care', 0.2), ('Fear', 0.1), ('Trust', 0.1)))
    return kernel(name, requires=requires, excludes=excludes, adds=adds,
                  base=1.0, query=('actor', 'location', 'recent', 'care', 'fear', 'trust'),
                  preferences=preferences)


KERNELS = {
    'wish': _kernel('wish', adds=('wished',), excludes=('wished',)),
    'missing': _kernel('missing', ('wished',), ('missing_introduced', 'promised_help'), ('missing_introduced',)),
    'borrow': _kernel('borrow', ('missing_introduced',), ('trolley_borrowed',), ('trolley_borrowed',)),
    'place_atlas': _kernel('place_atlas', ('trolley_borrowed',), ('atlas_on_desk',), ('atlas_on_desk',)),
    'failed_search': _kernel('failed_search', ('atlas_on_desk',), ('searched_nook',), ('searched_nook',)),
    'clue': _kernel('clue', ('searched_nook',), ('clue',), ('clue',)),
    'request_help': _kernel('request_help', ('clue',), ('help_requested',), ('help_requested',)),
    'reserve_atlas': _kernel('reserve_atlas', ('help_requested',), ('atlas_reserved',), ('atlas_reserved', 'atlas_released')),
    'release_atlas': _kernel('release_atlas', ('help_requested',), ('atlas_released',), ('atlas_reserved', 'atlas_released')),
    'fetch_ladder': _kernel('fetch_ladder', ('help_requested',), ('ladder_fetched',), ('ladder_fetched',)),
    'retrieve': _kernel('retrieve', ('clue', 'ladder_fetched'), ('book_retrieved',), ('book_retrieved',)),
    'recognize': _kernel('recognize', ('book_retrieved',), ('book_seen',), ('book_seen',)),
    'checkout': _kernel('checkout', ('book_seen',), ('book_checked_out',), ('book_checked_out',)),
    'checkout_atlas': _kernel('checkout_atlas', ('atlas_reserved', 'book_checked_out'), ('atlas_checked_out',), ('atlas_checked_out',)),
    'return_trolley': _kernel('return_trolley', ('book_checked_out',), ('trolley_returned',), ('trolley_returned',)),
    'return_ladder': _kernel('return_ladder', ('book_checked_out', 'ladder_fetched'), ('ladder_returned',), ('ladder_returned',)),
    'share_picture': _kernel('share_picture', ('atlas_released','book_checked_out'), ('drawing_invited',), ('drawing_invited',)),
    'sketch_whale': _kernel('sketch_whale', ('drawing_invited',), ('drawing_done',), ('drawing_done',)),
    'share_atlas': _kernel('share_atlas', ('atlas_checked_out',), ('drawing_invited',), ('drawing_invited',)),
    'sketch_moon': _kernel('sketch_moon', ('atlas_checked_out','drawing_invited'), ('drawing_done',), ('drawing_done',)),
    'ending': _kernel('ending', ('book_checked_out', 'trolley_returned', 'ladder_returned','drawing_done'), ('ended',))
}
KERNELS['reserve_atlas'] = kernel('reserve_atlas',requires=('help_requested',),
    excludes=('atlas_reserved','atlas_released'),adds=('atlas_reserved',),base=1.4,
    query=('hero',),preferences=(('Care',-1.8),('Trust',.5)))
KERNELS['release_atlas'] = kernel('release_atlas',requires=('help_requested',),
    excludes=('atlas_reserved','atlas_released'),adds=('atlas_released',),base=0,
    query=('hero',),preferences=(('Care',1.8),))


class LibraryWorld(World):
    def facts_for_attention(self):
        facts = []
        for eid, entity in sorted(self.entities.items()):
            facts.append(Fact('loc:' + eid, entity.noun + ' is at ' + entity.location,
                              ('location', eid, entity.location)))
            for state in sorted(entity.state):
                facts.append(Fact('state:' + eid + ':' + state,
                                  entity.noun + ' is ' + state,
                                  ('state', eid, state)))
            for name, value in sorted(entity.memes.items()):
                facts.append(Fact(eid + '.' + name,
                                  entity.noun + ' has ' + name + ' ' + str(value),
                                  ('actor', eid, name.lower()), value))
        for flag in sorted(self.flags):
            facts.append(Fact('flag:' + flag, 'The world has ' + flag,
                              ('flag', flag)))
        for event in self.history:
            kind = event['frame']['kind']
            facts.append(Fact('event:' + str(event['id']), 'Previously: ' + kind,
                              ('recent', kind)))
        return facts


def make_world(seed=0):
    rng = Random(seed)

    def person(eid, name, pronoun):
        return Entity(eid, name, 'person', 'library', pronoun=pronoun,
                      properties={'animate', 'can_hold'},
                      memes={'Care': 0.2 + 0.6 * rng.random(),
                             'Fear': 0.2 + 0.6 * rng.random(),
                             'Trust': 0.2 + 0.6 * rng.random()})

    entities = {
        'hero': person('hero', 'Mina', 'she'),
        'helper': person('helper', 'Ms Alvarez', 'she'),
        'friend': person('friend', 'Jun', 'he'),
        'book': Entity('book', 'whale book', 'object', 'high_shelf',
                       properties={'blue', 'belongs_to_friend'}, state={'missing','whale_picture'}),
        'atlas': Entity('atlas', 'moon atlas', 'object', 'hero',state={'moon_picture'}),
        'paper': Entity('paper','paper','object','hero',state={'blank'}),
        'pencil': Entity('pencil','pencil','tool','hero',properties={'draw','portable'}),
        'tool': Entity('tool', 'book trolley', 'object', 'station',
                       properties={'can_hold'}),
        'ladder': Entity('ladder', 'ladder', 'object', 'store'),
        'mitten': Entity('mitten', 'mitten', 'object', 'window_nook'),
        'bookmark': Entity('bookmark', 'star bookmark', 'object', 'book',
                           state={'visible'})
    }
    return LibraryWorld(scenario='library', entities=entities, hero='hero',
                        helper='helper', target='book', tool='tool',
                        setting='library', facts={})


def candidates(w):
    if w.finished:
        return []
    e = w.entities
    if not {'hero','helper','friend','book','atlas','tool','ladder','mitten','bookmark','paper','pencil'} <= e.keys():
        return []
    flags = w.flags
    fact_ids = {fact.id for fact in w.facts_for_attention()}
    result = []

    def add(kind, actor, patient='', instrument='', destination='', causes=()):
        k = KERNELS[kind]
        if (enabled(w, k)
                and all(c in fact_ids for c in causes)):
            result.append((k, Frame(kind, actor, patient, instrument,
                                    destination, tuple(causes))))

    hero_here = e['hero'].location == 'library'
    friend_here = e['friend'].location == 'library'
    helper_here = e['helper'].location == 'library'
    all_here = hero_here and friend_here and helper_here
    book_high = e['book'].location == 'high_shelf'
    trolley_held = e['tool'].location == 'hero'
    decision = 'atlas_reserved' in flags or 'atlas_released' in flags

    if hero_here and e['atlas'].location == 'hero':
        add('wish', 'hero', 'atlas', causes=('loc:hero', 'loc:atlas'))
    if (hero_here and friend_here and book_high and 'missing' in e['book'].state
            and 'belongs_to_friend' in e['book'].properties):
        add('missing', 'friend', 'book', causes=('flag:wished', 'loc:friend', 'state:book:missing'))
    if hero_here and helper_here and e['tool'].location == 'station':
        add('borrow', 'hero', 'tool', causes=('flag:missing_introduced', 'loc:hero', 'loc:helper', 'loc:tool'))
    if hero_here and trolley_held and e['atlas'].location == 'hero':
        add('place_atlas', 'hero', 'atlas', destination='desk',
            causes=('flag:trolley_borrowed', 'loc:atlas', 'loc:tool'))
    if (hero_here and friend_here and trolley_held and book_high
            and e['mitten'].location == 'window_nook'):
        add('failed_search', 'hero', 'mitten', 'tool',
            causes=('flag:atlas_on_desk', 'loc:friend', 'loc:tool', 'loc:mitten', 'loc:book'))
    if (hero_here and friend_here and trolley_held and book_high
            and e['bookmark'].location == 'book' and 'visible' in e['bookmark'].state):
        add('clue', 'friend', 'bookmark', 'tool',
            causes=('flag:searched_nook', 'loc:hero', 'loc:friend', 'loc:tool',
                    'loc:book', 'loc:bookmark', 'state:bookmark:visible'))
    if all_here and book_high:
        add('request_help', 'hero', 'helper', causes=('flag:clue', 'loc:hero', 'loc:friend', 'loc:helper'))
    if all_here and e['atlas'].location == 'desk' and book_high:
        add('reserve_atlas', 'hero', 'atlas', destination='desk',
                causes=('flag:help_requested', 'loc:atlas', 'loc:helper', 'hero.Care'))
        add('release_atlas', 'hero', 'atlas', destination='display',
                causes=('flag:help_requested', 'loc:atlas', 'loc:friend', 'hero.Care'))
    if all_here and decision and book_high and e['ladder'].location == 'store':
        choice = 'flag:atlas_reserved' if 'atlas_reserved' in flags else 'flag:atlas_released'
        add('fetch_ladder', 'helper', 'ladder', destination='library',
            causes=(choice, 'loc:helper', 'loc:ladder'))
    if all_here and decision and book_high and e['ladder'].location == 'library':
        choice = 'flag:atlas_reserved' if 'atlas_reserved' in flags else 'flag:atlas_released'
        add('retrieve', 'helper', 'book', 'ladder', 'helper',
            causes=('flag:clue', choice, 'loc:hero', 'loc:friend', 'loc:helper',
                    'loc:book', 'loc:ladder'))
    if friend_here and helper_here and e['book'].location == 'helper' and e['bookmark'].location == 'book':
        add('recognize', 'friend', 'book', causes=('flag:book_retrieved', 'loc:friend', 'loc:book', 'loc:bookmark'))
    if helper_here and can_transfer(w, 'book', 'helper', 'friend'):
        add('checkout', 'helper', 'book', destination='friend',
            causes=('flag:book_seen', 'loc:helper', 'loc:friend', 'loc:book'))
    if helper_here and hero_here and e['atlas'].location == 'desk' and 'reserved' in e['atlas'].state:
        add('checkout_atlas', 'helper', 'atlas', destination='hero',
            causes=('flag:atlas_reserved', 'flag:book_checked_out', 'loc:helper', 'loc:hero', 'loc:atlas', 'state:atlas:reserved'))
    if hero_here and trolley_held:
        add('return_trolley', 'hero', 'tool', destination='station',
            causes=('flag:book_checked_out', 'loc:hero', 'loc:tool'))
    if helper_here and e['ladder'].location == 'library':
        add('return_ladder', 'helper', 'ladder', destination='store',
            causes=('flag:book_checked_out', 'loc:helper', 'loc:ladder'))
    if hero_here and friend_here and e['book'].location=='friend' and 'whale_picture' in e['book'].state:
        add('share_picture','friend','book',causes=('loc:book','state:book:whale_picture'))
    if hero_here and friend_here and e['atlas'].location=='hero' and 'moon_picture' in e['atlas'].state:
        add('share_atlas','friend','atlas',causes=('loc:hero','loc:friend','loc:atlas'))
    if hero_here and 'can_hold' in e['hero'].properties and e['paper'].location=='hero' and 'blank' in e['paper'].state and e['pencil'].location=='hero' and 'draw' in e['pencil'].properties:
        if friend_here and e['book'].location=='friend' and 'open' in e['book'].state and 'whale_picture' in e['book'].state:
            add('sketch_whale','hero','paper','pencil',causes=('loc:paper','loc:pencil','state:book:whale_picture'))
        if friend_here and e['atlas'].location=='hero' and 'open' in e['atlas'].state and 'moon_picture' in e['atlas'].state:
            add('sketch_moon','hero','paper','pencil',causes=('loc:paper','loc:pencil','state:atlas:moon_picture'))
    atlas_done = (('atlas_released' in flags and e['atlas'].location == 'display') or
                  ('atlas_reserved' in flags and e['atlas'].location == 'hero'
                   and 'checked_out' in e['atlas'].state))
    if (hero_here and friend_here and e['book'].location == 'friend'
            and 'checked_out' in e['book'].state and e['tool'].location == 'station'
            and e['ladder'].location == 'store' and atlas_done
            and e['paper'].location=='hero'
            and ('whale_drawing' if 'atlas_released' in flags else 'moon_drawing') in e['paper'].state):
        choice = 'flag:atlas_released' if 'atlas_released' in flags else 'flag:atlas_reserved'
        add('ending', 'hero', 'book', causes=(choice, 'loc:hero', 'loc:friend',
            'loc:book', 'state:book:checked_out', 'loc:tool', 'loc:ladder', 'loc:atlas'))
    return result




CHANGES = {
    'borrow': (Change('tool', 'hero'),),
    'place_atlas': (Change('atlas', 'desk'),),
    'failed_search': (Change('mitten', 'tool'),),
    'reserve_atlas': (Change('atlas', add=('reserved',)),),
    'release_atlas': (Change('atlas', 'display', add=('released',)),),
    'fetch_ladder': (Change('ladder', 'library'),),
    'retrieve': (Change('book', 'helper', add=('found',), remove=('missing',)),),
    'checkout': (Change('book', 'friend', add=('checked_out',)),),
    'checkout_atlas': (Change('atlas', 'hero', add=('checked_out',), remove=('reserved',)),),
    'return_trolley': (Change('tool', 'station'),),
    'return_ladder': (Change('ladder', 'store'),),
    'share_picture': (Change('@patient', add=('open',)),),
    'share_atlas': (Change('@patient', add=('open',)),),
    'ending': (Change('book', add=('open',)),),
}


@committed(candidates, CHANGES, flags_first=False)
def commit(w, frame):
    e = w.entities; kind = frame.kind
    if kind in {'share_picture', 'share_atlas'}:
        e['friend'].memes['Care'] = min(1, e['friend'].memes['Care'] + .2)
    elif kind in {'sketch_whale', 'sketch_moon'}:
        e['paper'].state.discard('blank'); e['paper'].state.add('whale_drawing' if kind == 'sketch_whale' else 'moon_drawing'); e['paper'].noun = 'drawing'
        e['hero'].memes['Joy'] = .7
        if kind == 'sketch_whale': e['friend'].memes['Trust'] = min(1, e['friend'].memes['Trust'] + .2)
