"""Active semantic copy of Terra pottery round2; original evidence unchanged.

The active campaign adds a third, two-handed bowl design while preserving the
material, firing, cooling and possession prerequisites of the authored pack.
"""
from dataclasses import dataclass, asdict
from copy import deepcopy
from random import Random

from grammarworlds.world import World, Entity, Fact, kernel
from grammarworlds.portable.language import Language, load_lexicon


LEXICON = {
    'names': {},
    'nouns': {
        'cup': {}, 'bowl': {}, 'hand': {}, 'mug': {}, 'handle': {}, 'wall': {}, 'dent': {},
        'edge': {}, 'finger': {}, 'thumb': {}, 'thumb rest': {},
        'shaping rib': {}, 'sponge': {}, 'kiln': {}, 'workshop': {},
        'teapot': {}, 'tea': {'mass': True}, 'glaze': {'mass': True}
    },
    'adjectives': {
        'old': {}, 'stiff': {}, 'thin': {}, 'thick': {}, 'wide': {},
        'stable': {}, 'dented': {}, 'borrowed': {}, 'two': {}
    },
    'prepositions': {},
    'adverbs': {},
    'verbs': {
        'struggle': {'forms': ['struggle', 'struggled', 'struggled'], 'valencies': ['VV']},
        'give': {'forms': ['give', 'gave', 'given'], 'valencies': ['V3']},
        'shape': {'forms': ['shape', 'shaped', 'shaped'], 'valencies': ['V2']},
        'reshape': {'forms': ['reshape', 'reshaped', 'reshaped'], 'valencies': ['V2']},
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
            holder = self.entities.get(entity.location)
            place = holder.noun if holder else entity.location
            result.append(Fact('loc:' + eid, entity.noun + ' is at ' + place,
                               ('location', eid, entity.location)))
            for state in sorted(entity.state):
                result.append(Fact('state:' + eid + ':' + state,
                                   entity.noun + ' has state ' + state,
                                   ('state', eid, state)))
            for name, value in sorted(entity.memes.items()):
                result.append(Fact(eid + '.' + name,
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
    person = {'animate', 'can_hold'}
    entities = {
        'hero': Entity('hero', 'Bea', 'person', 'workshop', pronoun='she',
                       properties=set(person),
                       memes={'Care': rng.uniform(0.6, 1.0), 'Fear': rng.uniform(0.1, 0.8)}),
        'helper': Entity('helper', 'Mr Ivo', 'person', 'workshop', pronoun='he',
                         properties=set(person), memes={'Trust': 0.8}),
        'grandpa': Entity('grandpa', 'Grandpa Len', 'person', 'workshop', pronoun='he',
                          properties=set(person)|{'two_hands'}, state={'stiff_hand'}),
        'cup': Entity('cup', 'cup', 'object', 'bench',
                      state={'wet', 'thick', 'stable', 'wide_handle'}),
        'tool': Entity('tool', 'shaping rib', 'object', 'hero', state={'borrowed'}),
        'sponge': Entity('sponge', 'sponge', 'object', 'bench'),
        'kiln': Entity('kiln', 'kiln', 'object', 'workshop'),
        'bench': Entity('bench', 'bench', 'object', 'workshop'),
        'shelf': Entity('shelf', 'shelf', 'object', 'workshop'),
        'old_mug': Entity('old_mug', 'mug', 'object', 'grandpa',
                          state={'old', 'thin_handle'}),
        'blue_glaze': Entity('blue_glaze', 'glaze', 'material', 'bench', state={'blue'}),
        'teapot': Entity('teapot', 'teapot', 'object', 'bench', state={'tea'})
    }
    return PotteryWorld(scenario='pottery', entities=entities, hero='hero',
                        helper='helper', target='cup', tool='tool', setting='workshop',
                        facts={}, flags={'rib_borrowed'})


KERNELS = {
    'need': kernel('need', adds=('need_seen',)),
    'goal': kernel('goal', requires=('need_seen',), adds=('goal_said',)),
    'shape': kernel('shape', requires=('goal_said',), adds=('shaped',)),
    'slip': kernel('slip', requires=('shaped',), adds=('slipped',)),
    'inspect': kernel('inspect', requires=('slipped',), adds=('inspected',)),
    'consult': kernel('consult', requires=('inspected',), adds=('consulted',)),
    'fetch_sponge': kernel('fetch_sponge', requires=('consulted',), adds=('sponge_fetched',)),
    'thumb': kernel('thumb', requires=('inspected', 'sponge_fetched'),
                    excludes=('design_chosen', 'smooth_design'),
                    adds=('design_chosen', 'thumb_design', 'wall_checked'),
                    query=('care', 'fear', 'state'),
                    preferences=(('Care', 1.5), ('Fear', -0.25))),
    'smooth': kernel('smooth', requires=('inspected', 'sponge_fetched'),
                     excludes=('design_chosen', 'thumb_design'),
                     adds=('design_chosen', 'smooth_design', 'wall_checked'),
                     query=('care', 'fear', 'state'),
                     preferences=(('Fear', 0.7), ('Care', -0.35))),
    'remake': kernel('remake', requires=('consulted','sponge_fetched'),
                     excludes=('design_chosen','thumb_design','smooth_design'),
                     adds=('design_chosen','bowl_design','wall_checked'),
                     query=('care','fear','state'),base=-.1,
                     preferences=(('Fear',.8),('Care',.2))),
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


def candidates(w):
    from grammarworlds.world import Frame

    if w.finished:
        return []
    e = w.entities
    required = ('hero', 'helper', 'grandpa', 'cup', 'tool', 'sponge', 'kiln',
                'bench', 'shelf', 'old_mug', 'blue_glaze', 'teapot')
    if any(eid not in e for eid in required):
        return []
    cup = e['cup']
    facts = {fact.id for fact in w.facts_for_attention()}
    result = []

    def here(*ids):
        return all(e[eid].location == 'workshop' for eid in ids)

    def offer(kind, actor, patient='', instrument='', destination='', causes=(), guard=True):
        k = KERNELS[kind]
        if (guard and k.requires <= w.flags and not (k.excludes & w.flags)
                and not (k.adds & w.flags) and all(c in facts for c in causes)):
            result.append((k, Frame(kind, actor, patient, instrument, destination, tuple(causes))))

    design_ok = (
        ('thumb_design' in w.flags and 'smooth_design' not in w.flags
         and 'thumb_rest' in cup.state)
        or ('smooth_design' in w.flags and 'thumb_design' not in w.flags
            and 'smoothed' in cup.state)
        or ('bowl_design' in w.flags and not {'thumb_design','smooth_design'} & w.flags
            and {'bowl_shape','two_hand_grip'} <= cup.state)
    )
    design_ok = design_ok and len({'thumb_design','smooth_design','bowl_design'} & w.flags)==1
    grip_ok = ('wide_handle' in cup.state if 'bowl_design' not in w.flags else
               {'bowl_shape','two_hand_grip'} <= cup.state and 'two_hands' in e['grandpa'].properties)

    offer('need', 'grandpa', 'old_mug',
          causes=('state:grandpa:stiff_hand', 'state:old_mug:thin_handle', 'loc:old_mug'),
          guard=here('grandpa') and e['old_mug'].location == 'grandpa'
                and {'old', 'thin_handle'} <= e['old_mug'].state
                and 'stiff_hand' in e['grandpa'].state)
    offer('goal', 'hero', 'cup', destination='grandpa',
          causes=('flag:need_seen', 'loc:cup', 'state:cup:wide_handle'),
          guard=here('hero', 'grandpa', 'bench') and cup.location == 'bench'
                and 'wide_handle' in cup.state)
    offer('shape', 'hero', 'cup', 'tool',
          causes=('flag:goal_said', 'loc:tool', 'state:cup:wet'),
          guard=here('hero', 'helper', 'bench') and cup.location == 'bench'
                and 'wet' in cup.state and e['tool'].location == 'hero'
                and 'borrowed' in e['tool'].state)
    offer('slip', 'hero', 'cup', 'tool',
          causes=('flag:shaped', 'loc:tool', 'state:cup:wet'),
          guard=here('hero', 'bench') and e['tool'].location == 'hero'
                and cup.location == 'bench' and 'wet' in cup.state
                and 'dented' not in cup.state)
    offer('inspect', 'helper', 'cup',
          causes=('state:cup:dented', 'state:cup:thick', 'loc:helper'),
          guard=here('helper', 'bench') and cup.location == 'bench'
                and {'wet', 'dented', 'thick', 'stable'} <= cup.state)
    offer('fetch_sponge', 'hero', 'sponge', destination='hero',
          causes=('flag:inspected', 'loc:sponge', 'state:cup:dented'),
          guard=here('hero', 'bench') and e['sponge'].location == 'bench'
                and cup.location == 'bench' and 'dented' in cup.state)
    offer('consult','grandpa','cup',causes=('flag:inspected','loc:grandpa'),
          guard=here('grandpa','hero','helper') and 'two_hands' in e['grandpa'].properties)
    design_guard = (here('hero', 'bench') and cup.location == 'bench'
                    and e['sponge'].location == 'hero'
                    and {'wet', 'dented', 'thick', 'stable', 'wide_handle'} <= cup.state)
    offer('thumb', 'hero', 'cup', 'sponge',
          causes=('flag:inspected', 'state:cup:dented', 'state:cup:thick', 'loc:sponge', 'hero.Care'),
          guard=design_guard)
    offer('smooth', 'hero', 'cup', 'sponge',
          causes=('flag:inspected', 'state:cup:dented', 'state:cup:thick', 'loc:sponge', 'hero.Fear'),
          guard=design_guard)
    offer('remake','hero','cup','tool',causes=('flag:consulted','state:cup:wet','state:cup:dented','loc:tool'),
          guard=design_guard and e['tool'].location=='hero' and 'two_hands' in e['grandpa'].properties)
    offer('return_rib', 'hero', 'tool', destination='helper',
          causes=('flag:design_chosen', 'loc:tool', 'loc:helper'),
          guard=here('hero', 'helper') and e['tool'].location == 'hero')
    offer('return_sponge', 'hero', 'sponge', destination='bench',
          causes=('flag:design_chosen', 'loc:sponge', 'loc:bench'),
          guard=here('hero', 'bench') and e['sponge'].location == 'hero')
    offer('shelve', 'hero', 'cup', destination='shelf',
          causes=('flag:rib_returned', 'flag:sponge_returned', 'loc:cup'),
          guard=here('hero', 'bench', 'shelf') and cup.location == 'bench'
                and 'wet' in cup.state and design_ok)
    offer('dry', 'cup', 'cup', destination='shelf',
          causes=('flag:wall_checked', 'state:cup:wall_checked', 'state:cup:wet', 'loc:cup'),
          guard=here('shelf') and cup.location == 'shelf' and design_ok
                and {'wet', 'wall_checked', 'safe_edges'} <= cup.state)
    offer('load_bisque', 'helper', 'cup', destination='kiln',
          causes=('state:cup:dry', 'loc:cup', 'loc:kiln'),
          guard=here('helper', 'shelf', 'kiln') and cup.location == 'shelf'
                and 'dry' in cup.state)
    offer('bisque', 'helper', 'cup', 'kiln',
          causes=('state:cup:dry', 'loc:cup', 'loc:helper'),
          guard=here('helper', 'kiln') and cup.location == 'kiln'
                and 'dry' in cup.state and 'bisque' not in cup.state)
    offer('cool_bisque', 'cup', 'cup', 'kiln',
          causes=('flag:bisqued', 'state:cup:hot', 'loc:cup'),
          guard=here('kiln') and cup.location == 'kiln' and {'bisque', 'hot'} <= cup.state)
    offer('unload_bisque', 'helper', 'cup', destination='bench',
          causes=('flag:bisque_cooled', 'state:cup:cool', 'loc:cup'),
          guard=here('helper', 'kiln', 'bench') and cup.location == 'kiln'
                and {'bisque', 'cool'} <= cup.state and 'hot' not in cup.state)
    offer('glaze', 'hero', 'cup', 'blue_glaze',
          causes=('state:cup:bisque', 'loc:cup', 'loc:blue_glaze'),
          guard=here('hero', 'bench') and cup.location == 'bench'
                and {'bisque', 'cool'} <= cup.state and 'hot' not in cup.state
                and e['blue_glaze'].location == 'bench' and 'blue' in e['blue_glaze'].state)
    offer('load_final', 'helper', 'cup', destination='kiln',
          causes=('state:cup:glazed', 'loc:cup', 'loc:kiln'),
          guard=here('helper', 'bench', 'kiln') and cup.location == 'bench'
                and {'bisque', 'glazed', 'cool'} <= cup.state and 'hot' not in cup.state)
    offer('fire', 'helper', 'cup', 'kiln',
          causes=('state:cup:glazed', 'loc:cup', 'loc:helper'),
          guard=here('helper', 'kiln') and cup.location == 'kiln'
                and 'glazed' in cup.state and 'fired' not in cup.state)
    offer('cool_final', 'cup', 'cup', 'kiln',
          causes=('state:cup:fired', 'state:cup:hot', 'loc:cup'),
          guard=here('kiln') and cup.location == 'kiln' and {'fired', 'hot'} <= cup.state)
    offer('deliver', 'helper', 'cup', destination='hero',
          causes=('flag:final_cooled', 'state:cup:cool', 'loc:cup', 'loc:hero'),
          guard=here('helper', 'hero', 'kiln') and cup.location == 'kiln'
                and {'fired', 'cool'} <= cup.state and 'hot' not in cup.state)
    offer('give', 'hero', 'cup', destination='grandpa',
          causes=('state:cup:fired', 'state:cup:safe_edges', 'loc:cup', 'loc:grandpa'),
          guard=here('hero', 'grandpa') and cup.location == 'hero' and design_ok
                and {'fired', 'cool', 'safe_edges', 'stable'} <= cup.state and grip_ok
                and 'hot' not in cup.state)
    offer('use', 'grandpa', 'cup', 'teapot',
          causes=('flag:gifted', 'state:cup:fired', 'loc:cup', 'state:teapot:tea'),
          guard=here('grandpa', 'bench') and cup.location == 'grandpa'
                and 'fired' in cup.state and 'tea' not in cup.state
                and e['teapot'].location == 'bench' and 'tea' in e['teapot'].state)
    offer('ending', 'grandpa', 'cup',
          causes=('state:cup:tea', 'state:cup:fired', 'loc:cup', 'loc:tool', 'loc:sponge'),
          guard=here('grandpa', 'helper', 'bench') and cup.location == 'grandpa'
                and design_ok and {'tea', 'fired', 'safe_edges', 'stable'} <= cup.state and grip_ok
                and e['tool'].location == 'helper' and e['sponge'].location == 'bench')
    return result




def commit(w, frame, sentence):
    match = next((k for k, candidate in candidates(w) if candidate == frame), None)
    if match is None:
        raise ValueError('Forged or stale frame')
    before = w.snapshot()
    e = w.entities
    cup = e['cup']
    kind = frame.kind
    if kind == 'shape':
        cup.state.add('shaped')
    elif kind == 'slip':
        cup.state.add('dented')
    elif kind == 'fetch_sponge':
        e['sponge'].location = 'hero'
        e['hero'].state.add('hoped_to_smooth')
    elif kind == 'thumb':
        cup.state.update(('thumb_rest', 'safe_edges', 'wall_checked'))
    elif kind == 'smooth':
        cup.state.update(('smoothed', 'safe_edges', 'wall_checked'))
    elif kind == 'remake':
        cup.noun='bowl';cup.state.difference_update({'dented','wide_handle'})
        cup.state.update(('bowl_shape','two_hand_grip','safe_edges','wall_checked'))
    elif kind == 'return_rib':
        e['tool'].location = 'helper'
    elif kind == 'return_sponge':
        e['sponge'].location = 'bench'
    elif kind == 'shelve':
        cup.location = 'shelf'
    elif kind == 'dry':
        cup.state.remove('wet')
        cup.state.add('dry')
    elif kind in ('load_bisque', 'load_final'):
        cup.location = 'kiln'
    elif kind == 'bisque':
        cup.state.update(('bisque', 'hot'))
    elif kind in ('cool_bisque', 'cool_final'):
        cup.state.remove('hot')
        cup.state.add('cool')
    elif kind == 'unload_bisque':
        cup.location = 'bench'
    elif kind == 'glaze':
        cup.state.update(('glazed', 'blue'))
    elif kind == 'fire':
        cup.state.discard('cool')
        cup.state.update(('fired', 'hot'))
    elif kind == 'deliver':
        cup.location = 'hero'
    elif kind == 'give':
        cup.location = 'grandpa'
    elif kind == 'use':
        e['teapot'].state.remove('tea')
        cup.state.add('tea')
    elif kind == 'ending':
        if 'bowl_design' in w.flags:
            e['grandpa'].state.add('holding_with_two_hands')
        elif 'thumb_design' in w.flags:
            e['grandpa'].state.add('thumb_in_rest')
        else:
            e['grandpa'].state.add('holding_wide_handle')
    w.flags.update(match.adds)
    w.focus = frame.actor
    record = {'id': len(w.history) + 1, 'frame': asdict(frame), 'sentence': sentence,
              'before': before, 'after': w.snapshot()}
    w.history.append(record)
    return record
