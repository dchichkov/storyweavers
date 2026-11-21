"""Two guarded rescue strategies, with costs carried by real objects and people."""

from .lexicon import with_shared
from .operations import Change, committed, enabled
from ..world import Entity, Fact, Frame, World, kernel, make_world as original_world

LEXICON = with_shared({
    'nouns': {'bread': {'mass': True}, 'window': {}, 'basket': {}, 'rope': {}, 'lunch': {'mass': True}},
    'adjectives': { 'still': {}, 'hungry': {}, 'safe': {}, 'frightened': {}},
    'adverbs': {'carefully': {}},
    'prepositions': {'below': {}},
    'verbs': {
        'shiver': {'forms':['shiver','shivered','shivered'],'valencies':['V']},
        'steady': {'forms':['steady','steadied','steadied'],'valencies':['V2']},
        'lower': {'forms':['lower','lowered','lowered'],'valencies':['V2']},
        'climb': {'forms':['climb','climbed','climbed'],'valencies':['V','V2']},
        'enter': {'forms':['enter','entered','entered'],'valencies':['V2']},
        'eat': {'forms':['eat','ate','eaten'],'valencies':['V2']},

        'share': {'forms':['share','shared','shared'],'valencies':['V2']},
        'touch': {'forms':['touch','touched','touched'],'valencies':['V2']},
    },
})
KERNELS = {k.name:k for k in [
    kernel('notice', excludes=['noticed'], adds=['noticed'], query=['problem']),
    kernel('choose_ladder', ['noticed'], ['chosen'], ['chosen','ladder_plan'], query=['trust','fear'],
           preferences=[('Trust',1.8),('Fear',-1.2)]),
    kernel('choose_basket', ['noticed'], ['chosen'], ['chosen','basket_plan'], query=['care','fear'],
           preferences=[('Care',0.8),('Fear',0.7)]),
    kernel('prepare_ladder', ['ladder_plan'], ['prepared'], ['prepared'], query=['tool']),
    kernel('prepare_basket', ['basket_plan'], ['prepared'], ['prepared'], query=['care','tool']),
    kernel('load_basket', ['basket_plan','prepared'], ['loaded'], ['loaded'], query=['care']),
    kernel('place_basket', ['loaded'], ['placed'], ['placed'], query=['tool']),
    kernel('rescue_lift', ['prepared','ladder_plan'], ['rescued'], ['rescued','solved'], query=['trust','goal']),
    kernel('basket_wait', ['placed'], ['waited'], ['waited'], query=['care','fear']),
    kernel('basket_enter', ['waited'], ['entered'], ['entered'], query=['care','goal']),
    kernel('basket_lower', ['entered'], ['rescued'], ['rescued','solved'], query=['goal']),
    kernel('shelter', ['rescued'], ['sheltered'], ['sheltered'], query=['care','goal']),
    kernel('ending', ['sheltered'], [], ['ended'], query=['outcome']),
]}


def make_world(seed=0, **options):
    w=original_world('rescue',seed,**options)
    w.entities['helper'].properties.add('can_climb')
    w.entities['bread'].location='hero'
    w.entities['basket']=Entity('basket','basket','object','cottage',properties={'portable','can_contain'})
    w.entities['rope']=Entity('rope','rope','tool','window',properties={'lower','portable'})
    w.entities['target'].state.add('shivering')
    return w


def candidates(w):
    es=w.entities
    if not {'hero','helper','target','tool','bread','blanket','basket','rope'} <= es.keys():return []
    h,p,t=es['hero'],es['helper'],es['target']
    together=h.location==p.location=='garden'
    result=[]
    for k in KERNELS.values():
        if not enabled(w, k):continue
        kind=k.name; actor='hero'; patient='target'; instrument=''; destination=''
        legal=True
        if kind=='notice':legal=t.location=='ledge' and 'stranded' in t.state and together and es['bread'].location=='hero'
        elif kind.startswith('choose_'):
            legal=t.location=='ledge' and together and 'stranded' in t.state
            actor='helper'
            if kind=='choose_ladder':legal &= 'reach' in es['tool'].properties and 'can_climb' in p.properties
            else:legal &= es['bread'].location=='hero' and es['basket'].location=='cottage' and es['rope'].location=='window'
        elif kind=='prepare_ladder':
            legal=together and es['tool'].location=='shed' and 'reach' in es['tool'].properties
            instrument='tool'
        elif kind=='prepare_basket':
            legal=together and es['bread'].location=='hero' and es['basket'].location=='cottage' and es['rope'].location=='window' and 'lower' in es['rope'].properties
            actor='helper';instrument='basket';destination='helper'
        elif kind=='load_basket':
            legal=together and es['bread'].location=='hero' and es['basket'].location=='helper'
            patient='bread';destination='basket'
        elif kind=='place_basket':
            legal=together and es['basket'].location=='helper' and es['bread'].location=='basket' and es['rope'].location=='window' and 'lower' in es['rope'].properties
            actor='helper';patient='basket';instrument='rope';destination='ledge'
        elif kind=='rescue_lift':
            legal=together and es['tool'].location=='hero' and 'steady' in es['tool'].state and 'can_climb' in p.properties and 'stranded' in t.state and t.location=='ledge'
            actor='helper';instrument='tool';destination='hero'
        elif kind=='basket_wait':
            legal=h.location=='garden' and p.location=='window' and es['basket'].location=='ledge' and es['bread'].location=='basket' and t.location=='ledge'
        elif kind=='basket_enter':
            legal=t.location=='ledge' and es['basket'].location=='ledge' and es['bread'].location=='basket' and 'calm' in t.state
            actor='target';patient='basket';destination='basket'
        elif kind=='basket_lower':
            legal=t.location=='basket' and es['basket'].location=='ledge' and 'attached' in es['rope'].state and p.location=='window' and es['rope'].location=='helper' and 'lower' in es['rope'].properties and h.location=='garden'
            actor='helper';patient='basket';instrument='rope';destination='garden'
        elif kind=='shelter':
            legal='safe' in t.state and h.location=='garden' and t.location in {'hero','basket'} and es['blanket'].location=='cottage'
            destination='cottage'
        elif kind=='ending':
            legal=h.location=='cottage' and t.location=='blanket' and es['blanket'].location=='cottage' and {'safe','warm'}<=t.state
            actor='target'
        if legal:result.append((k,Frame(kind,actor,patient,instrument,destination,('problem',) if 'rescued' not in w.flags else ('outcome',))))
    return result


CHANGES = {
    'prepare_ladder': (Change('tool', 'hero', add=('steady',)),),
    'prepare_basket': (Change('basket', 'helper'),),
    'load_basket': (Change('bread', 'basket'),),
    'place_basket': (Change('basket', 'ledge'), Change('rope', 'helper', add=('attached',)), Change('helper', 'window')),
    'rescue_lift': (Change('target', 'hero', add=('safe',), remove=('stranded',)),),
    'basket_wait': (Change('target', add=('calm',), remove=('frightened',)),),
    'basket_enter': (Change('target', 'basket'), Change('bread', 'target', add=('eaten',)), Change('hero', add=('hungry',))),
    'basket_lower': (Change('basket', 'garden'), Change('target', add=('safe',), remove=('stranded',))),
    'shelter': (Change('hero', 'cottage'), Change('target', 'blanket', add=('warm',), remove=('cold', 'frightened', 'shivering'))),
    'ending': (Change('target', add=('resting',)),),
}


@committed(candidates, CHANGES)
def commit(w, f):
    if f.kind == 'rescue_lift': w.entities['hero'].memes['Trust'] += .3
    elif f.kind == 'basket_wait': w.entities['target'].memes['Fear'] = .2
    elif f.kind == 'shelter': w.entities['hero'].memes['Joy'] += .5
