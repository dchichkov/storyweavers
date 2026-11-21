"""A torn kite can fly after repair, or its paper can become a boat's sail."""
from dataclasses import asdict
from ..world import Entity, Fact, Frame, kernel, make_world as original_world

LEXICON={
    'nouns':{'paper':{'mass':True},'sail':{},'boat':{},'pond':{},'scissors':{'plural':'scissors'},'string':{'mass':True}},
    'adjectives':{'thin':{},'torn':{},'small':{},'patched':{}},
    'adverbs':{'again':{},'away':{},'instead':{}},
    'prepositions':{'across':{}},
    'verbs':{'fly':{'forms':['fly','flew','flown'],'valencies':['V','V2']},
             'make':{'forms':['make','made','made'],'valencies':['V2']},
             'tear':{'forms':['tear','tore','torn'],'valencies':['V','V2']},
             'cut':{'forms':['cut','cut','cut'],'valencies':['V2']},
             'sail':{'forms':['sail','sailed','sailed'],'valencies':['V']},
             'tie':{'forms':['tie','tied','tied'],'valencies':['V2']},
             'set':{'forms':['set','set','set'],'valencies':['V2']},
             'watch':{'forms':['watch','watched','watched'],'valencies':['V2']}}
}
KERNELS={k.name:k for k in [
    kernel('notice',excludes=['noticed'],adds=['noticed'],query=['problem']),
    kernel('inspect', ['noticed'], ['inspected'], ['inspected'],query=['obstacle']),
    kernel('choose_patch',['inspected'],['chosen'],['chosen','patch'],base=1.8,query=['care','trust'],preferences=[('Care',0.6),('Trust',1)]),
    kernel('choose_sail',['inspected'],['chosen'],['chosen','sail_plan'],query=['curiosity'],preferences=[('Curiosity',1.1)]),
    kernel('fetch_tape',['patch'],['prepared'],['prepared'],query=['tool']),
    kernel('mend',['prepared'],['mended'],['mended'],query=['care']),
    kernel('test_flight',['mended'],['tested'],['tested'],query=['goal']),
    kernel('reconsider',['tested'],['reconsidered'],['reconsidered','sail_plan'],query=['curiosity']),
    kernel('fetch_scissors',['sail_plan'],['scissors_ready'],['scissors_ready'],query=['helper']),
    kernel('cut_sail',['scissors_ready'],['converted'],['converted'],query=['goal']),
    kernel('attach_sail',['converted'],['attached'],['attached'],query=['tool']),
    kernel('launch_boat',['attached'],['launched'],['launched','solved'],query=['goal']),
    kernel('ending',[],[],['ended'],query=['outcome']),
]}


def make_world(seed=0,**options):
    w=original_world('kite',seed,**options)
    if seed%3==0:w.entities['target'].state.add('fragile')
    w.entities['boat']=Entity('boat','boat','object','meadow',properties={'float','portable'},state={'needs_sail'})
    w.entities['scissors']=Entity('scissors','scissors','tool','basket',number='plural',pronoun='they',properties={'cut','portable'})
    w.entities['string']=Entity('string','string','object','hero',properties={'tie','portable'})
    return w


def candidates(w):
    if not {'hero','helper','target','tool','boat','scissors','string'}<=w.entities.keys():return []
    e=w.entities;t=e['target'];together=e['hero'].location==e['helper'].location=='meadow'
    result=[]
    for k in KERNELS.values():
        if not k.requires<=w.flags or k.excludes&w.flags:continue
        name=k.name;legal=together;actor='hero';patient='target';instrument='';destination=''
        if name in {'notice','inspect','choose_patch','choose_sail'}:legal &= t.location=='meadow' and 'torn' in t.state
        if name=='fetch_tape':legal &= e['tool'].location=='basket' and 'repair' in e['tool'].properties
        elif name=='mend':
            legal &= e['tool'].location=='hero' and 'torn' in t.state and t.location=='meadow'
            instrument='tool'
        elif name=='test_flight':legal &= 'repaired' in t.state and t.location=='meadow'
        elif name=='reconsider':legal &= 'torn' in t.state and 'failed' in w.flags
        elif name=='fetch_scissors':legal &= e['scissors'].location=='basket' and 'cut' in e['scissors'].properties;actor='helper';patient='scissors'
        elif name=='cut_sail':
            legal &= t.location=='meadow' and 'torn' in t.state and e['scissors'].location=='helper' and 'cut' in e['scissors'].properties
            actor='helper';instrument='scissors'
        elif name=='attach_sail':
            legal &= 'sail' in t.state and t.location=='meadow' and e['boat'].location=='meadow' and e['string'].location=='hero'
            instrument='string';destination='boat'
        elif name=='launch_boat':
            legal &= t.location=='boat' and e['boat'].location=='meadow' and 'attached' in t.state and 'float' in e['boat'].properties
            patient='boat';destination='pond'
        elif name=='ending':
            legal &= ('flying' in t.state and t.location=='sky') or ('sailing' in e['boat'].state and e['boat'].location=='pond' and t.location=='boat')
        if legal:result.append((k,Frame(name,actor,patient,instrument,destination,('outcome',) if 'solved' in w.flags else ('problem',))))
    return result


def commit(w,f,sentence):
    if f not in [f for _,f in candidates(w)]:raise ValueError('invalid kite event')
    before=w.snapshot();e=w.entities;t=e['target'];w.flags.update(KERNELS[f.kind].adds)
    if f.kind=='fetch_tape':e['tool'].location='hero'
    elif f.kind=='mend':t.state.discard('torn');t.state.add('repaired')
    elif f.kind=='test_flight':
        if 'fragile' in t.state:
            t.state.discard('repaired');t.state.add('torn');w.flags.add('failed');e['hero'].memes['Curiosity']+=0.15
        else:
            t.location='sky';t.state.discard('grounded');t.state.add('flying');w.flags.add('solved');e['hero'].memes['Joy']+=0.5
    elif f.kind=='fetch_scissors':e['scissors'].location='helper'
    elif f.kind=='cut_sail':
        t.noun='sail';t.state.difference_update({'torn','repaired','grounded'});t.state.add('sail');t.properties.discard('flyable')
    elif f.kind=='attach_sail':
        t.location='boat';t.state.add('attached');e['string'].location='boat';e['boat'].state.discard('needs_sail')
    elif f.kind=='launch_boat':e['boat'].location='pond';e['boat'].state.add('sailing');e['hero'].memes['Joy']+=0.4
    w.focus=f.actor
    event=dict(id=len(w.history)+1,frame=asdict(f),sentence=sentence,before=before,after=w.snapshot())
    w.history.append(event);return event
