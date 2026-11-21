"""Consent-preserving musical choices: solo, written collaboration or private duet."""

from .lexicon import with_shared
from .operations import Change, committed, enabled
from ..world import Entity,Frame,kernel
from ..portable.worlds.music import make_world as original_world

LEXICON=with_shared({
    'nouns':{'rhythm':{},'answer':{},'beat':{},'audience':{}},
    'adjectives':{'quiet':{},'different':{},'written':{},'ready':{},'answering':{},'loud':{}},
    'adverbs':{'aloud':{},'softly':{},'alone':{}},
    'verbs':{
             'bow':{'forms':['bow','bowed','bowed'],'valencies':['V']},
             'smile':{'forms':['smile','smiled','smiled'],'valencies':['V']},
             'hear':{'forms':['hear','heard','heard'],'valencies':['V2']},

             'clap':{'forms':['clap','clapped','clapped'],'valencies':['V']},
             'listen':{'forms':['listen','listened','listened'],'valencies':['V']},
             'answer':{'forms':['answer','answered','answered'],'valencies':['V2']},
             'choose':{'forms':['choose','chose','chosen'],'valencies':['V2','VV']}}
})
KERNELS={k.name:k for k in [
    kernel('opening',excludes=['opened'],adds=['opened'],query=['goal']),
    kernel('borrow',['opened'],['borrowed'],['borrowed'],query=['physical']),
    kernel('invite',['borrowed'],['invited'],['invited'],query=['desire']),
    kernel('decline',['invited'],['declined'],['declined'],query=['partner','fear']),
    kernel('choose_solo',['declined'],['chosen'],['chosen','solo_plan'],base=.5,query=['hero','desire'],preferences=[('Desire',.6)]),
    kernel('offer_pattern',['declined'],['chosen'],['chosen','pattern_plan'],base=.7,query=['partner','trust'],preferences=[('Trust',1.1)]),
    kernel('offer_private',['declined'],['chosen'],['chosen','private_plan','private_consent'],base=.2,query=['partner','readiness'],preferences=[('Readiness',.8)]),
    kernel('write_pattern',['pattern_plan'],['pattern_written'],['pattern_written'],query=['partner','trust']),
    kernel('prepare_solo',['solo_plan'],['prepared'],['prepared'],query=['desire']),
    kernel('prepare_pattern',['pattern_written'],['prepared'],['prepared'],query=['trust']),
    kernel('pickup',['private_plan'],['prepared'],['prepared'],query=['physical']),
    kernel('perform',['prepared'],['performed'],['performed'],query=['performance']),
    kernel('join',['prepared','private_plan'],['performed'],['performed'],query=['trust']),
    kernel('response',['performed'],['responded'],['responded'],query=['care']),
    kernel('return',['responded'],[],[],query=['physical']),
    kernel('ending',['responded'],[],['ended'],query=['choice'])
]}


def make_world(seed=0,**options):
    w=original_world(seed,**options)
    w.entities['paper']=Entity('paper','paper','object','piano',properties={'portable'})
    w.entities['pencil']=Entity('pencil','pencil','tool','piano',properties={'write','portable'})
    return w


def candidates(w):
    e=w.entities
    if not {'hero','partner','teacher','drum','spare','program','paper','pencil'}<=e.keys():return []
    h,p=e['hero'],e['partner'];room=w.setting;together=h.location==p.location==room
    teacher=e['teacher'].location==room
    result=[]
    for k in KERNELS.values():
        if not enabled(w, k):continue
        name=k.name;legal=together;actor='hero';patient='';instrument='';destination=''
        if name=='opening':legal &= 'wants_duet' in h.state
        elif name=='borrow':legal &= teacher and e['drum'].location=='shelf';patient='drum';destination='hero'
        elif name=='invite':legal &= e['drum'].location=='hero';patient='partner'
        elif name=='decline':legal &= 'public_unready' in p.state;actor='partner'
        elif name=='choose_solo':legal &= e['drum'].location=='hero'
        elif name=='offer_pattern':legal &= p.memes.get('Trust',0)>=.35 and e['paper'].location=='piano' and e['pencil'].location=='piano';actor='partner'
        elif name=='offer_private':legal &= p.memes.get('Readiness',0)>=.5 and e['spare'].location=='shelf';actor='partner'
        elif name=='write_pattern':
            legal &= e['paper'].location=='piano' and e['pencil'].location=='piano' and 'write' in e['pencil'].properties and 'pattern_consent' in p.state
            actor='partner';patient='paper';instrument='pencil'
        elif name in {'prepare_solo','prepare_pattern'}:
            legal &= e['drum'].location=='hero' and e['program'].location=='piano'
            if name=='prepare_pattern':legal &= 'rhythm' in e['paper'].state
            patient='program'
        elif name=='pickup':
            legal &= 'consented' in p.state and p.memes.get('Readiness',0)>=.5 and e['spare'].location=='shelf'
            actor='partner';patient='spare';destination='partner'
        elif name=='perform':
            legal &= e['drum'].location=='hero' and 'solo' in e['program'].state and 'private_plan' not in w.flags and teacher
            instrument='drum'
        elif name=='join':
            legal &= 'consented' in p.state and p.memes.get('Readiness',0)>=.5 and e['drum'].location=='hero' and e['spare'].location=='partner'
            actor='partner';patient='hero';instrument='spare'
        elif name=='response':legal &= teacher;actor='partner' if 'private_plan' not in w.flags else 'hero'
        elif name=='return':
            for entity,holder in [('drum','hero'),('spare','partner')]:
                if together and e[entity].location==holder:result.append((k,Frame(name,holder,entity,entity,'shelf',('shelf',))))
            continue
        elif name=='ending':
            legal &= e['drum'].location==e['spare'].location=='shelf'
            if 'pattern_plan' in w.flags:legal &= 'rhythm' in e['paper'].state and 'pattern_played' in h.state
            if 'private_plan' in w.flags:legal &= 'joined' in p.state
        if legal:result.append((k,Frame(name,actor,patient,instrument,destination,('duet','boundary'))))
    return result


CHANGES = {
    'borrow': (Change('drum', 'hero'),),
    'decline': (Change('partner', add=('declined_public',)),),
    'choose_solo': (Change('hero', add=('accepted_boundary',)),),
    'offer_pattern': (Change('partner', add=('pattern_consent',)), Change('hero', add=('accepted_boundary',))),
    'offer_private': (Change('partner', add=('consented',)), Change('hero', add=('accepted_boundary',))),
    'write_pattern': (Change('paper', add=('rhythm',)),),
    'prepare_solo': (Change('program', add=('solo',)), Change('hero', add=('practiced', 'soft_beat', 'loud_beat'))),
    'prepare_pattern': (Change('program', add=('solo',)), Change('hero', add=('practiced',))),
    'pickup': (Change('spare', 'partner'),),
    'perform': (Change('hero', add=('performed_solo',)),),
    'join': (Change('partner', add=('joined',)),),
    'return': (Change('@patient', 'shelf'),),
}


@committed(candidates, CHANGES)
def commit(w, f):
    e = w.entities
    if f.kind == 'perform' and 'pattern_plan' in w.flags: e['hero'].state.add('pattern_played')
    elif f.kind == 'response':
        if 'private_plan' not in w.flags: e['partner'].state.add('applauded'); e['hero'].state.add('bowed')
        else: e['hero'].state.update({'heard_answer', 'smiled'}); e['partner'].state.add('smiled')
        e['hero'].memes['Joy'] = .8; e['partner'].memes['Trust'] = min(1, e['partner'].memes['Trust'] + .2)
    elif f.kind == 'ending' and 'pattern_plan' in w.flags:
        e['paper'].location = 'shelf'; e['hero'].state.add('wants_repeat_rhythm')
