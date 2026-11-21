from dataclasses import dataclass, asdict
from copy import deepcopy
from random import Random

from grammarworlds.world import World, Entity, Fact, Frame, Kernel, kernel
from grammarworlds.portable.language import Language, load_lexicon


LEXICON = {
    'names': {},
    'nouns': {
        'cup': {}, 'mug': {}, 'handle': {}, 'wall': {}, 'dent': {},
        'thumb': {}, 'thumb rest': {}, 'shaping rib': {}, 'sponge': {},
        'kiln': {}, 'workshop': {}, 'teapot': {},
        'tea': {'mass': True}, 'glaze': {'mass': True}
    },
    'adjectives': {
        'old': {}, 'stiff': {}, 'thin': {}, 'thick': {}, 'wide': {},
        'stable': {}, 'dented': {}, 'borrowed': {}
    },
    'prepositions': {},
    'adverbs': {},
    'verbs': {
        'struggle': {'forms': ['struggle', 'struggled', 'struggled'], 'valencies': ['VV']},
        'place': {'forms': ['place', 'placed', 'placed'], 'valencies': ['V2']},
        'give': {'forms': ['give', 'gave', 'given'], 'valencies': ['V3']},
        'shape': {'forms': ['shape', 'shaped', 'shaped'], 'valencies': ['V2']},
        'slip': {'forms': ['slip', 'slipped', 'slipped'], 'valencies': ['V']},
        'inspect': {'forms': ['inspect', 'inspected', 'inspected'], 'valencies': ['V2']},
        'soften': {'forms': ['soften', 'softened', 'softened'], 'valencies': ['V2']},
        'make': {'forms': ['make', 'made', 'made'], 'valencies': ['V3']},
        'smooth': {'forms': ['smooth', 'smoothed', 'smoothed'], 'valencies': ['V2']},
        'dry': {'forms': ['dry', 'dried', 'dried'], 'valencies': ['V']},
        'bisque': {'forms': ['bisque', 'bisqued', 'bisqued'], 'valencies': ['V2']},
        'cool': {'forms': ['cool', 'cooled', 'cooled'], 'valencies': ['V']},
        'glaze': {'forms': ['glaze', 'glazed', 'glazed'], 'valencies': ['V2']},
        'fire': {'forms': ['fire', 'fired', 'fired'], 'valencies': ['V2']},
        'pour': {'forms': ['pour', 'poured', 'poured'], 'valencies': ['V2']}
    }
}


@dataclass
class PotteryWorld(World):
    def facts_for_attention(self):
        result = []
        for eid, entity in sorted(self.entities.items()):
            if entity.location in self.entities:
                place = self.entities[entity.location].noun
            else:
                place = entity.location
            result.append(Fact('loc:' + eid, entity.noun + ' is at ' + place,
                               ('location', eid, entity.location)))
            for state in sorted(entity.state):
                result.append(Fact('state:' + eid + ':' + state,
                                   entity.noun + ' has state ' + state,
                                   ('state', eid, state)))
            for name, value in sorted(entity.memes.items()):
                result.append(Fact('meme:' + eid + ':' + name,
                                   entity.noun + ' has ' + name + ' ' + str(value),
                                   ('actor', eid, name.lower()), value))
        for flag in sorted(self.flags):
            result.append(Fact('flag:' + flag, 'Current milestone: ' + flag,
                               ('milestone', flag)))
        for event in self.history:
            kind = event['frame']['kind']
            result.append(Fact('event:' + str(event['id']),
                               'Previous event: ' + kind, ('recent', kind)))
        return result


def make_world(seed=0):
    rng = Random(seed)
    people = {'animate', 'can_hold'}
    entities = {
        'Bea': Entity('Bea', 'Bea', 'person', 'workshop', pronoun='she',
                      properties=set(people), memes={'Care': rng.uniform(0.6, 1.0),
                                                     'Fear': rng.uniform(0.1, 0.8)}),
        'Mr Ivo': Entity('Mr Ivo', 'Mr Ivo', 'person', 'workshop', pronoun='he',
                         properties=set(people), memes={'Trust': 0.8}),
        'Grandpa Len': Entity('Grandpa Len', 'Grandpa Len', 'person', 'workshop',
                              pronoun='he', properties=set(people), state={'stiff_hand'}),
        'cup': Entity('cup', 'cup', 'object', 'bench',
                      state={'wet', 'thick', 'stable', 'wide_handle'}),
        'shaping rib': Entity('shaping rib', 'shaping rib', 'object', 'Bea',
                              state={'borrowed'}),
        'sponge': Entity('sponge', 'sponge', 'object', 'bench'),
        'kiln': Entity('kiln', 'kiln', 'object', 'workshop'),
        'bench': Entity('bench', 'bench', 'object', 'workshop'),
        'shelf': Entity('shelf', 'shelf', 'object', 'workshop'),
        'old mug': Entity('old mug', 'mug', 'object', 'Grandpa Len',
                          state={'thin_handle'}),
        'blue glaze': Entity('blue glaze', 'glaze', 'material', 'bench',
                             state={'blue'}),
        'teapot': Entity('teapot', 'teapot', 'object', 'bench', state={'tea'})
    }
    return PotteryWorld(scenario='pottery', entities=entities, hero='Bea',
                        helper='Mr Ivo', target='cup', tool='shaping rib',
                        setting='workshop', facts={}, flags={'rib_borrowed'})


KERNELS = {
    'need': kernel('need', adds=('need_seen',)),
    'goal': kernel('goal', requires=('need_seen',), adds=('goal_said',)),
    'shape': kernel('shape', requires=('goal_said',), adds=('shaped',)),
    'slip': kernel('slip', requires=('shaped',), adds=('slipped',)),
    'inspect': kernel('inspect', requires=('slipped',), adds=('inspected',)),
    'fetch_sponge': kernel('fetch_sponge', requires=('inspected',), adds=('sponge_fetched',)),
    'thumb': kernel('thumb', requires=('inspected', 'sponge_fetched'),
                    excludes=('design_chosen',),
                    adds=('design_chosen', 'thumb_design', 'wall_checked'),
                    base=0.3, query=('care', 'state'),
                    preferences=(('care', 1.5), ('fear', -0.25))),
    'smooth': kernel('smooth', requires=('inspected', 'sponge_fetched'),
                     excludes=('design_chosen',),
                     adds=('design_chosen', 'smooth_design', 'wall_checked'),
                     query=('care', 'fear', 'state'),
                     preferences=(('fear', 0.7), ('care', -0.35))),
    'return_rib': kernel('return_rib', requires=('design_chosen',), adds=('rib_returned',)),
    'return_sponge': kernel('return_sponge', requires=('design_chosen',), adds=('sponge_returned',)),
    'shelve': kernel('shelve', requires=('rib_returned', 'sponge_returned'), adds=('shelved',)),
    'dry': kernel('dry', requires=('shelved', 'design_chosen', 'wall_checked'), adds=('dried',)),
    'load_bisque': kernel('load_bisque', requires=('dried',), adds=('bisque_loaded',)),
    'bisque': kernel('bisque', requires=('bisque_loaded',), adds=('bisqued',)),
    'cool_bisque': kernel('cool_bisque', requires=('bisqued',), adds=('bisque_cooled',)),
    'unload_bisque': kernel('unload_bisque', requires=('bisque_cooled',), adds=('bisque_unloaded',)),
    'glaze': kernel('glaze', requires=('bisque_unloaded',), adds=('glaze_done',)),
    'load_final': kernel('load_final', requires=('glaze_done',), adds=('final_loaded',)),
    'fire': kernel('fire', requires=('final_loaded',), adds=('fire_done',)),
    'cool_final': kernel('cool_final', requires=('fire_done',), adds=('final_cooled',)),
    'deliver': kernel('deliver', requires=('final_cooled',), adds=('collected',)),
    'give': kernel('give', requires=('collected',), adds=('gifted',)),
    'use': kernel('use', requires=('gifted',), adds=('tea_served',)),
    'ending': kernel('ending', requires=('tea_served', 'rib_returned', 'sponge_returned'),
                     adds=('ended',))
}


def _in_workshop(w, *ids):
    for eid in ids:
        seen = set()
        current = eid
        while current in w.entities:
            if current in seen:
                return False
            seen.add(current)
            current = w.entities[current].location
        if current != 'workshop':
            return False
    return True


def candidates(w):
    if w.finished:
        return []
    e = w.entities
    needed = ('Bea', 'Mr Ivo', 'Grandpa Len', 'cup', 'shaping rib', 'sponge',
              'kiln', 'bench', 'shelf', 'old mug', 'blue glaze', 'teapot')
    if any(x not in e for x in needed):
        return []
    cup = e['cup']
    facts = {fact.id for fact in w.facts_for_attention()}
    result = []

    def add(kind, actor, patient='', instrument='', destination='', causes=()):
        k = KERNELS[kind]
        if (k.requires <= w.flags and not (k.excludes & w.flags)
                and not (k.adds & w.flags) and all(c in facts for c in causes)):
            result.append((k, Frame(kind, actor, patient, instrument, destination, tuple(causes))))

    if (e['old mug'].location == 'Grandpa Len' and 'thin_handle' in e['old mug'].state
            and 'stiff_hand' in e['Grandpa Len'].state
            and _in_workshop(w, 'Grandpa Len', 'old mug')):
        add('need', 'Grandpa Len', 'old mug', causes=('state:Grandpa Len:stiff_hand', 'state:old mug:thin_handle'))
    if (e['old mug'].location == 'Grandpa Len'
            and _in_workshop(w, 'Bea', 'Grandpa Len', 'cup', 'bench')):
        add('goal', 'Bea', 'cup', 'old mug', 'bench',
            ('flag:need_seen', 'loc:old mug', 'loc:cup'))
    if (e['shaping rib'].location == 'Bea' and 'borrowed' in e['shaping rib'].state
            and cup.location == 'bench' and 'wet' in cup.state
            and _in_workshop(w, 'Bea', 'Mr Ivo', 'cup', 'shaping rib')):
        add('shape', 'Bea', 'cup', 'shaping rib', causes=('flag:goal_said', 'loc:shaping rib', 'state:cup:wet'))
    if (e['shaping rib'].location == 'Bea' and cup.location == 'bench'
            and 'wet' in cup.state and 'dented' not in cup.state
            and _in_workshop(w, 'Bea', 'shaping rib', 'cup')):
        add('slip', 'Bea', 'cup', 'shaping rib', causes=('flag:shaped', 'loc:shaping rib', 'state:cup:wet'))
    if (cup.location == 'bench' and {'wet', 'dented', 'thick', 'stable'} <= cup.state
            and _in_workshop(w, 'Mr Ivo', 'cup')):
        add('inspect', 'Mr Ivo', 'cup', causes=('state:cup:dented', 'state:cup:thick', 'loc:Mr Ivo'))
    if e['sponge'].location == 'bench' and _in_workshop(w, 'Bea', 'sponge', 'bench'):
        add('fetch_sponge', 'Bea', 'sponge', destination='Bea',
            causes=('flag:inspected', 'loc:sponge'))
    if (cup.location == 'bench' and e['sponge'].location == 'Bea'
            and {'wet', 'dented', 'thick', 'stable', 'wide_handle'} <= cup.state
            and _in_workshop(w, 'Bea', 'cup', 'sponge')):
        add('thumb', 'Bea', 'cup', 'sponge', causes=('state:cup:dented', 'state:cup:thick', 'loc:sponge', 'meme:Bea:Care'))
        add('smooth', 'Bea', 'cup', 'sponge', causes=('state:cup:dented', 'state:cup:thick', 'loc:sponge', 'meme:Bea:Fear'))
    if e['shaping rib'].location == 'Bea' and _in_workshop(w, 'Bea', 'Mr Ivo', 'shaping rib'):
        add('return_rib', 'Bea', 'shaping rib', destination='Mr Ivo',
            causes=('flag:design_chosen', 'loc:shaping rib', 'loc:Mr Ivo'))
    if e['sponge'].location == 'Bea' and _in_workshop(w, 'Bea', 'sponge', 'bench'):
        add('return_sponge', 'Bea', 'sponge', destination='bench',
            causes=('flag:design_chosen', 'loc:sponge', 'loc:bench'))
    if cup.location == 'bench' and 'wet' in cup.state and _in_workshop(w, 'Bea', 'cup', 'shelf'):
        add('shelve', 'Bea', 'cup', destination='shelf',
            causes=('flag:rib_returned', 'flag:sponge_returned', 'loc:cup'))
    if cup.location == 'shelf' and 'wet' in cup.state and _in_workshop(w, 'cup', 'shelf'):
        add('dry', 'cup', 'cup', destination='shelf',
            causes=('flag:wall_checked', 'state:cup:wet', 'loc:cup'))
    if (cup.location == 'shelf' and 'dry' in cup.state
            and _in_workshop(w, 'Mr Ivo', 'cup', 'shelf', 'kiln')):
        add('load_bisque', 'Mr Ivo', 'cup', destination='kiln',
            causes=('state:cup:dry', 'loc:cup', 'loc:kiln'))
    if (cup.location == 'kiln' and 'dry' in cup.state and 'bisque' not in cup.state
            and _in_workshop(w, 'Mr Ivo', 'cup', 'kiln')):
        add('bisque', 'Mr Ivo', 'cup', 'kiln', causes=('state:cup:dry', 'loc:cup', 'loc:Mr Ivo'))
    if (cup.location == 'kiln' and {'bisque', 'hot'} <= cup.state
            and _in_workshop(w, 'cup', 'kiln')):
        add('cool_bisque', 'cup', 'cup', 'kiln', causes=('flag:bisqued', 'state:cup:hot'))
    if (cup.location == 'kiln' and {'bisque', 'cool'} <= cup.state
            and _in_workshop(w, 'Mr Ivo', 'cup', 'kiln', 'bench')):
        add('unload_bisque', 'Mr Ivo', 'cup', destination='bench',
            causes=('flag:bisque_cooled', 'state:cup:cool', 'loc:cup'))
    if (cup.location == 'bench' and {'bisque', 'cool'} <= cup.state
            and e['blue glaze'].location == 'bench' and 'blue' in e['blue glaze'].state
            and _in_workshop(w, 'Bea', 'cup', 'blue glaze')):
        add('glaze', 'Bea', 'cup', 'blue glaze', causes=('state:cup:bisque', 'loc:cup', 'loc:blue glaze'))
    if (cup.location == 'bench' and {'bisque', 'glazed', 'cool'} <= cup.state
            and _in_workshop(w, 'Mr Ivo', 'cup', 'bench', 'kiln')):
        add('load_final', 'Mr Ivo', 'cup', destination='kiln',
            causes=('state:cup:glazed', 'loc:cup', 'loc:kiln'))
    if (cup.location == 'kiln' and 'glazed' in cup.state and 'fired' not in cup.state
            and _in_workshop(w, 'Mr Ivo', 'cup', 'kiln')):
        add('fire', 'Mr Ivo', 'cup', 'kiln', causes=('state:cup:glazed', 'loc:cup', 'loc:Mr Ivo'))
    if cup.location == 'kiln' and {'fired', 'hot'} <= cup.state and _in_workshop(w, 'cup', 'kiln'):
        add('cool_final', 'cup', 'cup', 'kiln', causes=('state:cup:fired', 'state:cup:hot'))
    if (cup.location == 'kiln' and {'fired', 'cool'} <= cup.state
            and _in_workshop(w, 'Mr Ivo', 'Bea', 'cup', 'kiln')):
        add('deliver', 'Mr Ivo', 'cup', destination='Bea',
            causes=('flag:final_cooled', 'loc:cup', 'loc:Bea'))
    design_ok = (('thumb_design' in w.flags and 'thumb_rest' in cup.state)
                 or ('smooth_design' in w.flags and 'smoothed' in cup.state))
    if (cup.location == 'Bea' and design_ok
            and {'fired', 'cool', 'safe_edges', 'stable', 'wide_handle'} <= cup.state
            and _in_workshop(w, 'Bea', 'Grandpa Len', 'cup')):
        add('give', 'Bea', 'cup', destination='Grandpa Len',
            causes=('state:cup:fired', 'state:cup:safe_edges', 'loc:cup', 'loc:Grandpa Len'))
    if (cup.location == 'Grandpa Len' and 'fired' in cup.state
            and e['teapot'].location == 'bench' and 'tea' in e['teapot'].state
            and _in_workshop(w, 'Grandpa Len', 'cup', 'teapot')):
        add('use', 'Grandpa Len', 'cup', 'teapot', causes=('flag:gifted', 'state:cup:fired', 'state:teapot:tea'))
    if (cup.location == 'Grandpa Len' and design_ok
            and {'tea', 'fired', 'safe_edges', 'stable', 'wide_handle'} <= cup.state
            and e['shaping rib'].location == 'Mr Ivo' and e['sponge'].location == 'bench'
            and _in_workshop(w, 'Grandpa Len', 'cup')):
        add('ending', 'Grandpa Len', 'cup', causes=('state:cup:tea', 'state:cup:fired', 'loc:cup'))
    return result


def plan(w, frame, tense='past'):
    g = Language(w, tense)
    lexicon = deepcopy(load_lexicon())
    for category, entries in LEXICON.items():
        lexicon.setdefault(category, {}).update(deepcopy(entries))
    g.lexicon = lexicon
    k = frame.kind
    ref = g.ref
    n = g.n
    pp = g.pp
    v = g.v
    s = g.s
    cup = lambda: ref('cup')
    dent = lambda: g.possess(cup(), g.cn('dent'))
    handle = lambda: g.possess(cup(), g.cn('handle'))
    if k == 'need':
        hand = g.possess(ref('Grandpa Len'), g.cn('hand'))
        old_handle = g.possess(n('mug', 'old'), g.cn('handle', 'thin'))
        return g.join(s(hand, g.be('stiff')),
                      s('Grandpa Len', v('struggle', v('hold', old_handle))), 'and')
    if k == 'goal':
        put_down = s('Grandpa Len', g.adv(v('place', n('mug', 'old')), pp('on', n('bench'))))
        wish = s('Bea', v('want', v('give', ref('Grandpa Len'), cup())))
        return g.join(put_down, wish, 'and')
    if k == 'shape':
        rib = g.possess(ref('Mr Ivo'), g.cn('shaping rib', 'borrowed'))
        return s('Bea', v('use', rib, v('shape', cup())))
    if k == 'slip':
        return g.join(s(ref('shaping rib'), v('slip')), s(cup(), g.be('dented')), 'and')
    if k == 'inspect':
        wall = g.possess(cup(), g.cn('wall'))
        return g.join(s('Mr Ivo', v('inspect', wall)), s(g.possess(cup(), g.cn('wall')), g.be('thick')), 'and')
    if k == 'fetch_sponge':
        return s('Bea', g.adv(v('fetch', ref('sponge')), pp('from', n('bench'))))
    if k == 'thumb':
        first = g.adv(v('soften', dent()), pp('with', ref('sponge')))
        second = v('make', n('dent'), n('thumb rest', det='a'))
        return g.sequence('Bea', first, second)
    if k == 'smooth':
        first = s('Bea', g.adv(v('smooth', dent()), pp('with', ref('sponge'))))
        return g.join(first, s(handle(), g.be('wide')), 'and')
    if k == 'return_rib':
        return s('Bea', g.adv(v('return', ref('shaping rib')), pp('to', ref('Mr Ivo'))))
    if k == 'return_sponge':
        return s('Bea', g.adv(v('return', ref('sponge')), pp('to', n('bench'))))
    if k == 'shelve':
        return s('Bea', g.adv(v('carry', cup()), pp('from', n('bench')), pp('to', n('shelf'))))
    if k == 'dry':
        return s(cup(), g.adv(v('dry'), pp('on', n('shelf'))))
    if k == 'load_bisque':
        return s('Mr Ivo', g.adv(v('carry', cup()), pp('from', n('shelf')), pp('to', n('kiln'))))
    if k == 'bisque':
        return s('Mr Ivo', g.adv(v('bisque', cup()), pp('in', n('kiln'))))
    if k in ('cool_bisque', 'cool_final'):
        return s(cup(), g.adv(v('cool'), pp('in', n('kiln'))))
    if k == 'unload_bisque':
        return s('Mr Ivo', g.adv(v('carry', cup()), pp('from', n('kiln')), pp('to', n('bench'))))
    if k == 'glaze':
        return s('Bea', g.adv(v('glaze', cup()), pp('with', n('glaze', 'blue', det='bare'))))
    if k == 'load_final':
        return s('Mr Ivo', g.adv(v('carry', cup()), pp('from', n('bench')), pp('to', n('kiln'))))
    if k == 'fire':
        return s('Mr Ivo', g.adv(v('fire', cup()), pp('in', n('kiln'))))
    if k == 'deliver':
        return s('Mr Ivo', v('bring', ref('Bea'), cup()))
    if k == 'give':
        return s('Bea', v('give', ref('Grandpa Len'), cup()))
    if k == 'use':
        action = g.adv(v('pour', n('tea', det='bare')), pp('from', n('teapot')), pp('in', cup()))
        return s('Grandpa Len', action)
    if k == 'ending':
        if 'thumb_design' in w.flags:
            thumb = g.possess(ref('Grandpa Len'), g.cn('thumb'))
            return g.join(s('Grandpa Len', v('hold', cup())),
                          s(thumb, g.adv(v('rest'), pp('in', dent()))), 'and')
        return g.join(s('Grandpa Len', v('hold', handle())), s(cup(), g.be('blue')), 'and')
    raise ValueError('Unknown frame kind')


def commit(w, frame, sentence):
    match = next((k for k, f in candidates(w) if f == frame), None)
    if match is None:
        raise ValueError('Forged or stale frame')
    before = w.snapshot()
    e = w.entities
    cup = e['cup']
    k = frame.kind
    if k == 'goal':
        e['old mug'].location = 'bench'
    elif k == 'slip':
        cup.state.add('dented')
    elif k == 'fetch_sponge':
        e['sponge'].location = 'Bea'
    elif k == 'thumb':
        cup.state.update(('thumb_rest', 'safe_edges'))
    elif k == 'smooth':
        cup.state.update(('smoothed', 'safe_edges'))
    elif k == 'return_rib':
        e['shaping rib'].location = 'Mr Ivo'
    elif k == 'return_sponge':
        e['sponge'].location = 'bench'
    elif k == 'shelve':
        cup.location = 'shelf'
    elif k == 'dry':
        cup.state.remove('wet')
        cup.state.add('dry')
    elif k in ('load_bisque', 'load_final'):
        cup.location = 'kiln'
    elif k == 'bisque':
        cup.state.update(('bisque', 'hot'))
    elif k in ('cool_bisque', 'cool_final'):
        cup.state.remove('hot')
        cup.state.add('cool')
    elif k == 'unload_bisque':
        cup.location = 'bench'
    elif k == 'glaze':
        cup.state.update(('glazed', 'blue'))
    elif k == 'fire':
        cup.state.discard('cool')
        cup.state.update(('fired', 'hot'))
    elif k == 'deliver':
        cup.location = 'Bea'
    elif k == 'give':
        cup.location = 'Grandpa Len'
    elif k == 'use':
        e['teapot'].state.remove('tea')
        cup.state.add('tea')
    elif k == 'ending':
        if 'thumb_design' in w.flags:
            e['Grandpa Len'].state.add('thumb_in_rest')
        else:
            e['Grandpa Len'].state.add('holding_wide_handle')
    w.flags.update(match.adds)
    w.focus = frame.actor
    record = {'id': len(w.history) + 1, 'frame': asdict(frame), 'sentence': sentence,
              'before': before, 'after': w.snapshot()}
    w.history.append(record)
    return record