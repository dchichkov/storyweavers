"""Small authoring vocabulary for grounded seed-story adaptations.

Surface expressions compile through the existing typed grammar. They are not
prewritten sentences, and event effects are never inferred from English.
"""
from copy import deepcopy


def R(entity): return ['ref', entity]
def N(word, *adjectives, det='the', number='singular'): return ['noun', word, list(adjectives), det, number]
def P(word): return ['pronoun', word]
def V(word, *args): return ['verb', word, *args]
def B(value): return ['be', value]
def Can(vp): return ['can', vp]
def PP(prep, obj): return ['pp', prep, obj]
def A(vp, *mods): return ['adv', vp, *mods]
def S(actor, vp, negative=False): return ['sentence', actor, vp, negative]
def Say(actor, vp, listener='helper'): return ['say', actor, vp, listener]
def Either(*sentences): return ['either', *sentences]
def Both(a,b): return ['both', a,b]
def Using(actor, vp, tool): return ['using', actor,vp,R(tool)]
def Join(left,right,link='and'): return ['join',left,right,link]
def Poss(owner, noun): return ['possess',R(owner),noun]


def entity(noun, kind='object', location='work', *, state=(), properties=(), pronoun='it', memes=None, number='singular'):
    return dict(noun=noun, kind=kind, location=location, state=list(state), properties=list(properties),
                pronoun=pronoun, memes=memes or {}, number=number)


def person(name, pronoun, **kw):
    return entity(name,'person',pronoun=pronoun,properties=('can_hold','can_help'), **kw)


def place(noun, **kw): return entity(noun,'place',properties=('reachable',),**kw)
def tool(noun, **kw): return entity(noun,'tool',properties=('portable',),**kw)
def obj(noun, **kw): return entity(noun,properties=('portable',),**kw)


def change(entity, *, location=None, add=(), remove=(), memes=None):
    return dict(entity=entity,location=location,add=list(add),remove=list(remove),memes=memes or {})


def at(entity, location): return ['location',entity,location]
def has(entity, state): return ['state',entity,state]
def prop(entity, value): return ['property',entity,value]
def together(*entities): return ['together',*entities]


def event(name, *surface, actor='hero', patient='', instrument='', destination='',
          after=(), excludes=(), adds=(), guards=(), effects=(), qa=(), base=0., tags=(), portable=None):
    return dict(name=name, surface=list(surface), actor=actor,patient=patient,instrument=instrument,
        destination=destination, after=list(after), excludes=list(excludes), adds=list(adds),
        guards=list(guards), effects=list(effects),qa=list(qa),base=base,tags=list(tags),portable=portable)


def Q(key, kind, question, answer, *entities, supports=()):
    return dict(key=key,kind=kind,question=question,answer=answer,entities=list(entities),supports=list(supports))


def fork(name, *alternatives): return dict(fork=name, alternatives=list(alternatives))


def chain(*events):
    """Only authoring shorthand: dependencies remain named, inspectable flags."""
    result=[]; previous=None
    for item in events:
        item=deepcopy(item)
        name=item.get('fork',item.get('name'))
        alternatives=item.get('alternatives',[item])
        for variant in alternatives:
            if previous: variant['after'].append(previous)
            variant['excludes'].append(name+'_done')
            variant['adds'].append(name+'_done')
            result.append(variant)
        previous=name+'_done'
    for variant in alternatives: variant['adds'].append('ended')
    return result


def story(number, name, entities, events, *, target, tool_id, helper='helper', premise, fidelity, variants=()):
    return dict(number=number,name=name,entities=entities,events=events,target=target,tool=tool_id,
                helper=helper,premise=premise,fidelity=fidelity,variants=list(variants))
