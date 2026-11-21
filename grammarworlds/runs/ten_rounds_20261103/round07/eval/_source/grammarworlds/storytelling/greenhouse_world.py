"""Scarce water, competing care targets, and three physically different outcomes."""
from dataclasses import asdict
from ..world import Entity,Fact,Frame,World,kernel
from ..portable.worlds.heldout import make_world as original_world

LEXICON={
    'nouns':{'water':{'mass':True},'can':{},'leaf':{'plural':'leaves'},'half':{},'share':{},'soil':{'mass':True}},
    'adjectives':{'full':{},'empty':{},'damp':{},'brown':{},'shaded':{},'dry':{},'watered':{}},
    'prepositions':{'of':{},'beside':{}},
    'adverbs':{'first':{},'equally':{},'tomorrow':{}},
    'verbs':{'have':{'forms':['have','had','had'],'valencies':['V2']},
             'divide':{'forms':['divide','divided','divided'],'valencies':['V2']},
             'wait':{'forms':['wait','waited','waited'],'valencies':['V']},
             'pour':{'forms':['pour','poured','poured'],'valencies':['V2']},
             'move':{'forms':['move','moved','moved'],'valencies':['V2']},
             'keep':{'forms':['keep','kept','kept'],'valencies':['V2']}}
}

class GreenhouseWorld(World):
    def facts_for_attention(self):
        e=self.entities
        facts=[Fact('water',f"Barrel water: {e['barrel'].memes['Water']}; can water: {e['can'].memes['Water']}",('resource','planning')),
               Fact('plants','The plants need water and shade.',('goal','care')),
               Fact('shade','The umbrella is '+e['umbrella'].location,('tool','planning'))]
        for name,value in e['hero'].memes.items():
            facts.append(Fact('hero.'+name,name,('hero',name.lower()),value))
        return facts

KERNELS={k.name:k for k in [
    kernel('notice',excludes=['noticed'],adds=['noticed'],query=['goal']),
    kernel('borrow',['noticed'],['borrowed'],['borrowed'],query=['resource']),
    kernel('fill',['borrowed'],['filled'],['filled'],query=['resource']),
    kernel('choose_seedlings',['filled'],['chosen'],['chosen','seedlings_first'],query=['care'],preferences=[('Care',.45)]),
    kernel('choose_flower',['filled'],['chosen'],['chosen','flower_first'],base=.3,query=['desire'],preferences=[('Desire',.5)]),
    kernel('choose_share',['filled'],['chosen'],['chosen','share_plan'],base=.5,query=['care','desire'],preferences=[('Care',.25),('Desire',.25)]),
    kernel('water_first',['chosen'],['first_water'],['first_water'],query=['care']),
    kernel('shade_break',['first_water'],['shade_broken'],['shade_broken'],query=['shade']),
    kernel('secure',['shade_broken'],['protected'],['protected'],query=['care','tool']),
    kernel('move_flower',['protected','share_plan'],['flower_shaded'],['flower_shaded'],query=['care']),
    kernel('repair_tap',['protected'],['tap_repaired'],['tap_repaired'],query=['resource']),
    kernel('refill',['tap_repaired'],['refilled'],['refilled'],query=['resource']),
    kernel('water_second',['refilled'],['second_water'],['second_water'],query=['care']),
    kernel('repair_shade',['second_water'],['shade_repaired'],['shade_repaired'],query=['tool']),
    kernel('promise_repair',['flower_shaded'],['deferred'],['deferred'],query=['planning']),
    kernel('return',[],['returned'],['returned'],query=['physical']),
    kernel('ending',['returned'],[],['ended'],query=['goal'])
]}

def make_world(seed=0,*,care=.9,desire=.7):
    if not 0<=care<=1 or not 0<=desire<=1:raise ValueError('concept magnitude must be in [0,1]')
    base=original_world(seed)
    w=GreenhouseWorld(**base.__dict__)
    e=w.entities;e['hero'].memes.update(Care=care,Desire=desire)
    e['barrel'].memes['Water']=2;e['can'].memes['Water']=0
    e['sunflower'].memes['Water']=e['tomatoes'].memes['Water']=0
    e['leaf']=Entity('leaf','leaf','plant_part','tomatoes',state={'green'})
    return w


def candidates(w):
    e=w.entities
    required={'hero','caretaker','owner','tomatoes','sunflower','can','barrel','tap','cloth','umbrella','pot','tie','clip'}
    if not required<=e.keys():return []
    together=e['hero'].location==e['caretaker'].location=='greenhouse'
    rows=[]
    for k in KERNELS.values():
        if not k.requires<=w.flags or k.excludes&w.flags:continue
        name=k.name;actor='hero';patient='';instrument='';destination='';legal=together
        if name=='notice':legal &= 'dry' in e['tomatoes'].state and 'dry' in e['sunflower'].state
        elif name=='borrow':legal &= e['can'].location=='caretaker';patient='can';destination='hero'
        elif name=='fill':legal &= e['can'].location=='hero' and e['can'].memes['Water']==0 and e['barrel'].memes['Water']==2;patient='barrel';instrument='can'
        elif name.startswith('choose_'):legal &= e['can'].location=='hero' and e['can'].memes['Water']==2
        elif name=='water_first':
            legal &= e['can'].location=='hero' and e['can'].memes['Water']==2
            patient='sunflower' if 'flower_first' in w.flags else 'tomatoes';instrument='can'
        elif name=='shade_break':actor='cloth';patient='cloth';legal &= 'intact' in e['cloth'].state
        elif name=='secure':
            legal &= e['umbrella'].location=='hero' and 'closed' in e['umbrella'].state and 'weighted_with_pebbles' in e['pot'].state and e['tie'].location=='drawer'
            patient='umbrella';instrument='tie';destination='pot'
        elif name=='move_flower':legal &= 'open' in e['umbrella'].state and e['umbrella'].location=='pot' and e['sunflower'].location=='greenhouse';patient='sunflower';destination='bench'
        elif name=='repair_tap':legal &= 'share_plan' not in w.flags and 'broken' in e['tap'].state;actor='caretaker';patient='tap'
        elif name=='refill':legal &= 'repaired' in e['tap'].state and e['can'].location=='hero' and e['can'].memes['Water']==0;patient='tap';instrument='can'
        elif name=='water_second':
            legal &= e['can'].location=='hero' and e['can'].memes['Water']==2 and 'repaired' in e['tap'].state
            patient='tomatoes' if 'flower_first' in w.flags else 'sunflower';instrument='can'
        elif name=='repair_shade':
            legal &= e['owner'].location=='outside' and e['clip'].location=='owner' and 'broken' in e['cloth'].state
            actor='owner';patient='cloth';instrument='clip'
        elif name=='promise_repair':legal &= 'broken' in e['tap'].state;actor='caretaker';patient='tap'
        elif name=='return':
            legal &= ('shade_repaired' in w.flags or 'deferred' in w.flags) and e['can'].location=='hero' and e['can'].memes['Water']==0
            patient='can';destination='caretaker'
        elif name=='ending':
            legal &= e['can'].location=='caretaker'
            if 'share_plan' in w.flags:
                legal &= all(e[p].memes['Water']==1 and 'shaded' in e[p].state for p in ('tomatoes','sunflower')) and e['umbrella'].location=='pot' and 'open' in e['umbrella'].state
            else:legal &= all(e[p].memes['Water']==2 for p in ('tomatoes','sunflower')) and 'repaired' in e['cloth'].state
        if actor in {'hero','caretaker','owner'}:legal &= {'animate','can_hold'}<=e[actor].properties
        if legal:rows.append((k,Frame(name,actor,patient,instrument,destination,('water','plants','shade'))))
    return rows


def commit(w,f,sentence):
    if f not in [x for _,x in candidates(w)]:raise ValueError('invalid greenhouse event')
    before=w.snapshot();e=w.entities;w.flags.update(KERNELS[f.kind].adds)
    if f.kind=='borrow':e['can'].location='hero'
    elif f.kind=='fill':e['barrel'].memes['Water']=0;e['barrel'].state={'empty'};e['can'].memes['Water']=2;e['can'].state={'full'}
    elif f.kind=='water_first':
        if 'share_plan' in w.flags:
            for plant in ('tomatoes','sunflower'):e[plant].memes['Water']=1;e[plant].state.discard('dry');e[plant].state.add('damp')
        else:e[f.patient].memes['Water']=2;e[f.patient].state.discard('dry');e[f.patient].state.add('watered')
        e['can'].memes['Water']=0;e['can'].state={'empty'}
    elif f.kind=='shade_break':
        e['cloth'].state={'broken'};e['tomatoes'].state.add('exposed')
        if 'flower_first' in w.flags:e['tomatoes'].state.add('brown_leaf');e['leaf'].state={'brown'}
    elif f.kind=='secure':
        e['umbrella'].location='pot';e['umbrella'].state={'open'};e['tie'].location='umbrella';e['tomatoes'].state.discard('exposed');e['tomatoes'].state.add('shaded')
    elif f.kind=='move_flower':e['sunflower'].location='bench';e['sunflower'].state.add('shaded')
    elif f.kind=='repair_tap':e['tap'].state={'repaired'}
    elif f.kind=='refill':e['can'].memes['Water']=2;e['can'].state={'full'}
    elif f.kind=='water_second':
        e[f.patient].memes['Water']=2;e[f.patient].state.discard('dry');e[f.patient].state.add('watered');e['can'].memes['Water']=0;e['can'].state={'empty'}
    elif f.kind=='repair_shade':
        e['owner'].location='greenhouse';e['clip'].location='cloth';e['cloth'].state={'repaired'}
        e['umbrella'].state={'closed'};e['umbrella'].location='hero';e['tie'].location='drawer'
    elif f.kind=='promise_repair':e['caretaker'].state.add('promised_repair')
    elif f.kind=='return':e['can'].location='caretaker'
    elif f.kind=='ending':
        for plant in ('tomatoes','sunflower'):e[plant].state.discard('drooping');e[plant].state.add('upright')
        if 'seedlings_first' in w.flags:e['sunflower'].location='bench'
    w.focus=f.actor
    event=dict(id=len(w.history)+1,frame=asdict(f),sentence=sentence,before=before,after=w.snapshot())
    w.history.append(event);return event
