"""A missing key: search independently or admit the loss and borrow a spare."""

from .operations import Change, committed, enabled
from ..world import Entity,Frame,kernel,make_world as original_world

LEXICON={
    'nouns':{'storybook':{},'hook':{},'spare key':{},'note':{},'pencil':{}},
    'adjectives':{'missing':{},'locked':{},'open':{},'spare':{}},
    'adverbs':{'tomorrow':{},'safely':{},'inside':{}},
    'prepositions':{'inside':{},'beside':{}},
    'verbs':{'lose':{'forms':['lose','lost','lost'],'valencies':['V2']},
             'admit':{'forms':['admit','admitted','admitted'],'valencies':['VS']},
             'hang':{'forms':['hang','hung','hung'],'valencies':['V2']},
             'write':{'forms':['write','wrote','written'],'valencies':['V2']},
             'leave':{'forms':['leave','left','left'],'valencies':['V2']},
             'remember':{'forms':['remember','remembered','remembered'],'valencies':['VV','VS']}}
}
KERNELS={k.name:k for k in [
    kernel('notice',excludes=['noticed'],adds=['noticed'],query=['problem']),
    kernel('offer_help',['noticed'],['offered'],['offered'],query=['helper']),
    kernel('choose_search',['offered'],['chosen'],['chosen','search_plan'],base=.8,query=['curiosity'],preferences=[('Curiosity',.5)]),
    kernel('admit_loss',['offered'],['chosen'],['chosen','admitted'],query=['trust','fear'],preferences=[('Trust',1.5),('Fear',.8)]),
    kernel('fetch_light',['search_plan'],['prepared'],['prepared'],query=['tool']),
    kernel('find_key',['prepared'],['found'],['found'],query=['goal']),
    kernel('lend_spare',['admitted'],['borrowed'],['borrowed'],query=['helper','trust']),
    kernel('unlock_original',['found'],['unlocked'],['unlocked','solved'],query=['goal']),
    kernel('unlock_spare',['borrowed'],['unlocked'],['unlocked','solved'],query=['goal']),
    kernel('hang_key',['unlocked','found'],['stored'],['stored'],query=['care']),
    kernel('return_spare',['unlocked','borrowed'],['returned'],['returned'],query=['trust']),
    kernel('write_reminder',['returned'],['stored'],['stored','promised_search'],query=['care']),
    kernel('ending',['stored'],[],['ended'],query=['outcome'])
]}


def make_world(seed=0,**options):
    w=original_world('key',seed,**options)
    w.entities['storybook']=Entity('storybook','storybook','object','hero',properties={'portable'})
    w.entities['spare']=Entity('spare','spare key','object','helper',properties={'unlocks','portable'})
    w.entities['note']=Entity('note','note','object','cottage',properties={'portable'})
    w.entities['pencil']=Entity('pencil','pencil','tool','cottage',properties={'write','portable'})
    return w


def candidates(w):
    e=w.entities
    if not {'hero','helper','target','tool','door','spare','note','pencil','storybook'}<=e.keys():return []
    together=e['hero'].location==e['helper'].location
    result=[]
    for k in KERNELS.values():
        if not enabled(w, k):continue
        name=k.name;actor='hero';patient='target';instrument='';destination='';legal=True
        if name in {'notice','offer_help','choose_search','admit_loss','lend_spare'}:
            legal=together and e['hero'].location=='courtyard' and 'locked' in e['door'].state
        if name=='notice':legal &= e['target'].location=='under bench' and 'lost' in e['target'].state and e['storybook'].location=='hero'
        elif name=='offer_help':actor='helper'
        elif name=='fetch_light':legal=e['hero'].location=='courtyard' and e['tool'].location=='porch' and 'illuminate' in e['tool'].properties
        elif name=='find_key':
            legal=e['hero'].location=='courtyard' and e['tool'].location=='hero' and 'illuminate' in e['tool'].properties and e['target'].location=='under bench' and 'lost' in e['target'].state
            instrument='tool';destination='hero'
        elif name=='lend_spare':legal &= e['spare'].location=='helper' and 'unlocks' in e['spare'].properties;actor='helper';patient='spare';destination='hero'
        elif name.startswith('unlock_'):
            instrument='target' if name=='unlock_original' else 'spare';patient='door'
            legal=e['hero'].location=='courtyard' and together and e[instrument].location=='hero' and 'unlocks' in e[instrument].properties and 'locked' in e['door'].state
        elif name=='hang_key':legal=e['hero'].location=='cottage' and e['target'].location=='hero' and 'open' in e['door'].state;destination='hook'
        elif name=='return_spare':legal=together and e['hero'].location=='cottage' and e['spare'].location=='hero';patient='spare';destination='helper'
        elif name=='write_reminder':
            legal=e['hero'].location=='cottage' and e['note'].location=='cottage' and e['pencil'].location=='cottage' and 'write' in e['pencil'].properties and 'lost' in e['target'].state
            patient='note';instrument='pencil';destination='hook'
        elif name=='ending':
            legal=together and e['hero'].location=='cottage' and 'open' in e['door'].state and e['storybook'].location=='hero'
            legal &= (e['target'].location=='hook' and 'found' in w.flags) or (e['note'].location=='hook' and 'search_reminder' in e['note'].state and e['spare'].location=='helper')
            patient='storybook'
        if legal:result.append((k,Frame(name,actor,patient,instrument,destination,('outcome',) if 'solved' in w.flags else ('problem',))))
    return result


CHANGES = {
    'fetch_light': (Change('tool', 'hero'),),
    'find_key': (Change('target', 'hero', add=('found',), remove=('lost', 'hidden')),),
    'lend_spare': (Change('@patient', '@destination'),),
    'hang_key': (Change('target', 'hook'),),
    'return_spare': (Change('@patient', '@destination'),),
    'write_reminder': (Change('note', 'hook', add=('search_reminder',)),),
    'ending': (Change('storybook', add=('open',)), Change('hero', add=('reading',))),
}


@committed(candidates, CHANGES)
def commit(w, f):
    e = w.entities
    if f.kind == 'admit_loss': e['hero'].memes['Trust'] += .3
    elif f.kind.startswith('unlock_'):
        e['door'].state.discard('locked'); e['door'].state.add('open')
        e['hero'].location = e['helper'].location = 'cottage'
    elif f.kind == 'write_reminder': e['hero'].memes['Care'] += .2
