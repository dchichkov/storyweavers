from dataclasses import asdict
from copy import deepcopy
from random import Random

from grammarworlds.world import World, Entity, Fact, Frame, kernel
from grammarworlds.portable.language import Language, load_lexicon


LEXICON = {
    'names': {},
    'nouns': {
        'whale book': {}, 'moon atlas': {}, 'book trolley': {},
        'mitten': {}, 'star bookmark': {}, 'window nook': {},
        'astronomy shelf': {}, 'high shelf': {}, 'front desk': {},
        'display table': {}, 'trolley station': {}, 'storeroom': {}
    },
    'adjectives': {},
    'prepositions': {},
    'adverbs': {'out': {}},
    'verbs': {
        'place': {'forms': ['place', 'placed', 'placed'], 'valencies': ['V2']},
        'search': {'forms': ['search', 'searched', 'searched'], 'valencies': ['V2']},
        'help': {'forms': ['help', 'helped', 'helped'], 'valencies': ['V2']},
        'agree': {'forms': ['agree', 'agreed', 'agreed'], 'valencies': ['VV']},
        'lend': {'forms': ['lend', 'lent', 'lent'], 'valencies': ['V3']},
        'give': {'forms': ['give', 'gave', 'given'], 'valencies': ['V3']},
        'reserve': {'forms': ['reserve', 'reserved', 'reserved'], 'valencies': ['V2']},
        'check': {'forms': ['check', 'checked', 'checked'], 'valencies': ['V2']},
        'read': {'forms': ['read', 'read', 'read'], 'valencies': ['V2']}
    }
}


def _kernel(name, requires=(), adds=(), excludes=()):
    return kernel(name, requires=requires, excludes=excludes, adds=adds,
                  base=1.0, query=('actor', 'location', 'recent'),
                  preferences=(('care', 0.2), ('trust', 0.1)))


KERNELS = {
    'wish': _kernel('wish', adds=('wished',), excludes=('wished',)),
    'missing': _kernel('missing', ('wished',), ('missing_introduced',), ('missing_introduced',)),
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
    'ending': _kernel('ending', ('book_checked_out', 'trolley_returned', 'ladder_returned'), ('ended',))
}


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
                facts.append(Fact('meme:' + eid + ':' + name,
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
                       properties={'blue'}, state={'missing'}),
        'atlas': Entity('atlas', 'moon atlas', 'object', 'hero'),
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
    flags = w.flags
    fact_ids = {fact.id for fact in w.facts_for_attention()}
    result = []

    def add(kind, actor, patient='', instrument='', destination='', causes=()):
        k = KERNELS[kind]
        if (k.requires <= flags and not (k.excludes & flags)
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
    if hero_here and friend_here and book_high and 'missing' in e['book'].state:
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
        if e['hero'].memes.get('Care', 0.0) < 0.5:
            add('reserve_atlas', 'hero', 'atlas', destination='desk',
                causes=('flag:help_requested', 'loc:atlas', 'loc:helper', 'meme:hero:Care'))
        else:
            add('release_atlas', 'hero', 'atlas', destination='display',
                causes=('flag:help_requested', 'loc:atlas', 'loc:friend', 'meme:hero:Care'))
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
    if helper_here and friend_here and e['book'].location == 'helper':
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
    atlas_done = (('atlas_released' in flags and e['atlas'].location == 'display') or
                  ('atlas_reserved' in flags and e['atlas'].location == 'hero'
                   and 'checked_out' in e['atlas'].state))
    if (hero_here and friend_here and e['book'].location == 'friend'
            and 'checked_out' in e['book'].state and e['tool'].location == 'station'
            and e['ladder'].location == 'store' and atlas_done):
        choice = 'flag:atlas_released' if 'atlas_released' in flags else 'flag:atlas_reserved'
        add('ending', 'hero', 'book', causes=(choice, 'loc:hero', 'loc:friend',
            'loc:book', 'state:book:checked_out', 'loc:tool', 'loc:ladder', 'loc:atlas'))
    return result


def plan(w, frame, tense='past'):
    g = Language(w, tense)
    lex = deepcopy(load_lexicon())
    for category, entries in LEXICON.items():
        lex.setdefault(category, {}).update(deepcopy(entries))
    g.lexicon = lex
    r = g.ref
    k = frame.kind

    if k == 'wish':
        return g.sequence('hero', g.v('hold', r('atlas')),
                          g.v('hope', g.v('borrow', r('atlas'))))
    if k == 'missing':
        report = g.s('friend', g.v('say', g.s(r('book'), g.be('missing'))))
        listen = g.s('hero', g.adv(g.v('listen'), g.pp('to', r('friend'))))
        return g.join(report, listen, 'and')
    if k == 'borrow':
        request = g.s('hero', g.v('ask', r('helper'), g.v('lend', r('hero'), r('tool'))))
        loan = g.s('helper', g.v('lend', r('hero'), r('tool')))
        return g.join(request, loan, 'and')
    if k == 'place_atlas':
        return g.sequence('hero',
            g.adv(g.v('place', r('atlas')), g.pp('on', g.n('front desk'))),
            g.v('hold', r('tool')))
    if k == 'failed_search':
        search = g.s(g.both(r('hero'), r('friend')), g.v('search', g.n('window nook')))
        found = g.s('friend', g.v('find', r('mitten')))
        missed = g.s('friend', g.v('find', r('book')), negative=True)
        return g.join(g.join(search, found, 'and'), missed, 'but')
    if k == 'clue':
        search = g.s(g.both(r('hero'), r('friend')),
                     g.adv(g.v('search', g.n('astronomy shelf')), g.pp('with', r('tool'))))
        spot = g.s('friend', g.adv(g.v('spot', r('bookmark')), g.pp('on', g.n('high shelf'))))
        return g.join(search, spot, 'and')
    if k == 'request_help':
        request = g.s('hero', g.v('ask', r('helper'), g.v('help', r('friend'))))
        answer = g.s('helper', g.v('agree', g.v('help', r('friend'))))
        return g.join(request, answer, 'and')
    if k == 'reserve_atlas':
        request = g.s('hero', g.v('ask', r('helper'), g.v('reserve', r('atlas'))))
        reserved = g.s('helper', g.v('reserve', r('atlas')))
        return g.join(request, reserved, 'and')
    if k == 'release_atlas':
        returned = g.s('hero', g.adv(g.v('return', r('atlas')), g.pp('to', g.n('display table'))))
        thanks = g.s('friend', g.v('thank', r('hero')))
        return g.join(returned, thanks, 'and')
    if k == 'fetch_ladder':
        return g.s('helper', g.adv(g.v('fetch', r('ladder')), g.pp('from', g.n('storeroom'))))
    if k == 'retrieve':
        actions = g.sequence('helper', g.v('climb', r('ladder')), g.v('lift', r('book')))
        down = g.s('helper', g.adv(g.v('step'), 'down'))
        return g.join(actions, down, 'and')
    if k == 'recognize':
        seen = g.s('friend', g.v('see', r('book')))
        bookmark = g.s(r('bookmark'), g.be(g.pp('in', r('book'))))
        return g.join(seen, bookmark, 'and')
    if k == 'checkout':
        return g.sequence('helper', g.adv(g.v('check', r('book')), 'out'),
                          g.v('give', r('friend'), r('book')))
    if k == 'checkout_atlas':
        return g.sequence('helper', g.adv(g.v('check', r('atlas')), 'out'),
                          g.v('give', r('hero'), r('atlas')))
    if k == 'return_trolley':
        return g.s('hero', g.adv(g.v('return', r('tool')), g.pp('to', g.n('trolley station'))))
    if k == 'return_ladder':
        return g.s('helper', g.adv(g.v('return', r('ladder')), g.pp('to', g.n('storeroom'))))
    if k == 'ending':
        held = g.s('friend', g.v('hold', r('book')))
        reading = g.s(g.both(r('hero'), r('friend')), g.v('read', r('book')))
        return g.join(held, reading, 'and')
    raise ValueError('Unknown frame kind')


def commit(w, frame, sentence):
    match = next((k for k, f in candidates(w) if f == frame), None)
    if match is None:
        raise ValueError('Forged or stale frame')
    before = w.snapshot()
    e = w.entities
    kind = frame.kind
    if kind == 'borrow':
        e['tool'].location = 'hero'
    elif kind == 'place_atlas':
        e['atlas'].location = 'desk'
    elif kind == 'failed_search':
        e['mitten'].location = 'tool'
    elif kind == 'reserve_atlas':
        e['atlas'].state.add('reserved')
    elif kind == 'release_atlas':
        e['atlas'].location = 'display'
        e['atlas'].state.add('released')
    elif kind == 'fetch_ladder':
        e['ladder'].location = 'library'
    elif kind == 'retrieve':
        e['book'].location = 'helper'
        e['book'].state.discard('missing')
        e['book'].state.add('found')
    elif kind == 'checkout':
        e['book'].location = 'friend'
        e['book'].state.add('checked_out')
    elif kind == 'checkout_atlas':
        e['atlas'].location = 'hero'
        e['atlas'].state.discard('reserved')
        e['atlas'].state.add('checked_out')
    elif kind == 'return_trolley':
        e['tool'].location = 'station'
    elif kind == 'return_ladder':
        e['ladder'].location = 'store'
    w.flags.update(match.adds)
    w.focus = frame.actor
    event = {'id': len(w.history) + 1, 'frame': asdict(frame),
             'sentence': sentence, 'before': before, 'after': w.snapshot()}
    w.history.append(event)
    return event
