"""Executable ports and typed realizations used by the event-fragment pool."""
from .catalog_attachment import CatalogLines
from .storytelling.operations import Change
from .storytelling.continuations import ExpandedLanguage
from .storytelling.surface import scene
from .portable.nouns import pronoun
from .portable.features import NP
from .grammar import seq
from .world import Frame

SIGNATURES = {
    'show_premise': {'actor','audience','rabbit','source'},
    'take_hat': {'actor','hat','stage'},
    'promise_show': {'actor','audience','hat'},
    'failed_portal': {'actor','rabbit','hat','wand','source'},
    'notice_binding': {'actor','hat','ribbon'},
    'untie_hat': {'actor','hat','ribbon'},
    'portal_rabbit': {'actor','rabbit','hat','wand','source'},
    'close_eyes': {'actor'}, 'open_eyes': {'actor'},
    'hide_rabbit': {'actor','audience','rabbit','hat','source'},
    'peek_rabbit': {'actor','audience','rabbit','hat'},
    'lift_rabbit': {'actor','audience','rabbit','hat'},
    'applaud_reveal': {'actor','rabbit','holder'},
    'settle_rabbit': {'actor','rabbit','hat','stage'},
    'feed_rabbit': {'actor','rabbit','food','stage'},
    'rabbit_final_image': {'actor','rabbit','hat','food','stage'},
}

LEXICON = {
    'nouns':{w:{} for w in ["magician's hat",'hat','top hat','rabbit','wand','ribbon','hutch','table','carrot','surprise','trick','ear','brim','eye']},
    'adjectives':{w:{} for w in ['open','tight','loose','quiet']},
    'prepositions':{w:{} for w in ['beside','above','out of','inside','around']},
    'adverbs':{'again':{},'gently':{}},
    'verbs':{
        'wait':{'forms':['wait','waited','waited'],'valencies':['V']},
        'raise':{'forms':['raise','raised','raised'],'valencies':['V2']},
        'tap':{'forms':['tap','tapped','tapped'],'valencies':['V2']},
        'stay':{'forms':['stay','stayed','stayed'],'valencies':['V']},
        'untie':{'forms':['untie','untied','untied'],'valencies':['V2']},
        'appear':{'forms':['appear','appeared','appeared'],'valencies':['V']},
        'disappear':{'forms':['disappear','disappeared','disappeared'],'valencies':['V']},
        'lift':{'forms':['lift','lifted','lifted'],'valencies':['V2']},
        'pull':{'forms':['pull','pulled','pulled'],'valencies':['V2']},
        'clap':{'forms':['clap','clapped','clapped'],'valencies':['V']},
        'laugh':{'forms':['laugh','laughed','laughed'],'valencies':['V']},
        'nibble':{'forms':['nibble','nibbled','nibbled'],'valencies':['V2']},
        'close':{'forms':['close','closed','closed'],'valencies':['V2']},
        'open':{'forms':['open','opened','opened'],'valencies':['V2']},
        'show':{'forms':['show','showed','shown'],'valencies':['V3']},
        'settle':{'forms':['settle','settled','settled'],'valencies':['V2']},
    },
}


class PoolLanguage(ExpandedLanguage):
    def ref(self, entity_id, *, subject=False, first=False, adjectives=()):
        entity=self.world.entities[entity_id]
        known=any(entity_id in event.get('referents',[]) for event in self.world.history if event.get('narrated'))
        if known and not first and 'hat' in entity.properties:
            phrase=self.n('hat',*adjectives)
            return NP(*(seq('referent:'+entity_id,getattr(phrase,case))
                        for case in ('subject','object','possessive')),phrase.agreement)
        return super().ref(entity_id,subject=subject,first=first,adjectives=adjectives)


class PoolLines(CatalogLines):
    fields={**CatalogLines.fields,**SIGNATURES}
    kinds={**CatalogLines.kinds,'rabbit':{'animal'},'hat':{'object'},'audience':{'person'},
           'wand':{'tool'},'ribbon':{'object'},'stage':{'place'},'food':{'food'},'holder':{'person'}}

    def __init__(self,world,template,bindings):
        super().__init__(world,template,bindings)
        for sid,e in self.events.items():
            if e['op'] in SIGNATURES:
                self.frames[sid]=Frame(sid,e['actor'],e.get('rabbit',e.get('hat','')),
                                       e.get('wand',e.get('hat','')),e.get('stage',''))

    def effects(self,e):
        op=e['op']
        if op not in SIGNATURES: return super().effects(e)
        c=lambda role,**kw:Change(e[role],**kw)
        if op=='take_hat': return (c('hat',location=e['actor']),)
        if op=='promise_show': return (c('actor',add=('promised_surprise',)),)
        if op=='failed_portal': return (c('hat',add=('failed_attempt',)),)
        if op=='notice_binding': return (c('ribbon',add=('noticed',)),)
        if op=='untie_hat': return (c('ribbon',add=('loose',),remove=('tied',)),c('hat',add=('open',),remove=('bound',)))
        if op in {'portal_rabbit','hide_rabbit'}: return (c('rabbit',location=e['hat'],add=('hidden',)),)
        if op=='close_eyes': return (c('actor',add=('eyes_closed',)),)
        if op=='open_eyes': return (c('actor',remove=('eyes_closed',)),)
        if op=='peek_rabbit': return (c('rabbit',add=('ears_visible',)),)
        if op=='lift_rabbit': return (c('rabbit',location=e['actor'],add=('revealed',),remove=('hidden','ears_visible')),)
        if op=='applaud_reveal': return (c('actor',add=('pleased',)),)
        if op=='settle_rabbit': return (c('rabbit',location=e['stage']),c('hat',location=e['stage']))
        if op=='feed_rabbit': return (c('food',add=('offered',)),)
        if op=='rabbit_final_image': return (c('food',location=e['rabbit'],add=('nibbled',)),c('rabbit',add=('fed',),remove=('hungry',)))
        return ()

    def reasons(self,sid,w=None):
        w=w or self.world;e=self.events[sid];op=e['op']
        if op not in SIGNATURES: return super().reasons(sid,w)
        if w.finished:return ['world is marked ended']
        if any(e[k] not in w.entities for k in SIGNATURES[op]): return ['missing carrier']
        ent={k:w.entities[e[k]] for k in SIGNATURES[op]};a=ent['actor'];bad=[]
        def need(ok,reason):
            if not ok:bad.append(reason)
        for slot,v in ent.items():need(v.kind in self.kinds[slot],'wrong kind: '+slot)
        need(a.location==w.setting,'actor is not at the scene')
        for slot in ('audience','holder'):
            if slot in ent:need(ent[slot].location==a.location,'people are not together')
        for slot in ('stage','source'):
            if slot in ent:need(ent[slot].location==a.location and 'reachable' in ent[slot].properties,'place is not accessible: '+slot)
        if 'rabbit' in ent:need({'rabbit','calm'}<=ent['rabbit'].properties,'rabbit is not compatible or calm')
        if 'hat' in ent:need({'hat','rabbit_capacity'}<=ent['hat'].properties,'hat lacks rabbit capacity')
        if op=='show_premise':need(ent['rabbit'].location==e['source'],'rabbit is not in the source place')
        elif op=='take_hat':
            need('can_hold' in a.properties,'actor cannot carry');need(ent['hat'].location==e['stage'],'hat is not on stage')
        elif op=='promise_show':need(ent['hat'].location==a.id,'actor is not holding hat')
        elif op in {'failed_portal','portal_rabbit'}:
            need('can_portal' in a.properties,'actor lacks portal skill')
            need('portal_hat' in ent['hat'].properties,'this hat has no portal physics')
            need(ent['hat'].location==a.id,'actor is not holding hat')
            need(ent['wand'].location==a.id and 'portal_focus' in ent['wand'].properties,'portal focus is not held')
            need(ent['rabbit'].location==e['source'],'rabbit is not in source place')
            if op=='failed_portal':need('bound' in ent['hat'].state,'there is no tied-hat obstacle')
            else:need('open' in ent['hat'].state and 'bound' not in ent['hat'].state,'portal is not open')
        elif op in {'notice_binding','untie_hat'}:
            need(ent['ribbon'].location==e['hat'] and 'tied' in ent['ribbon'].state,'ribbon is not tied to this hat')
            need('bound' in ent['hat'].state,'hat is not bound')
            holder=w.entities.get(ent['hat'].location)
            need(holder is not None and holder.kind=='person' and holder.location==a.location,'hat cannot be inspected here')
            if op=='untie_hat':need(ent['hat'].location==a.id and 'can_hold' in a.properties,'actor cannot untie held hat')
        elif op=='close_eyes':need('eyes_closed' not in a.state,'eyes already closed')
        elif op=='open_eyes':need('eyes_closed' in a.state,'eyes already open')
        elif op=='hide_rabbit':
            need('eyes_closed' in ent['audience'].state,'audience is watching')
            need(ent['rabbit'].location==e['source'],'rabbit is not in source place')
            need(ent['hat'].location==a.id and 'open' in ent['hat'].state and 'bound' not in ent['hat'].state,'hat is not held open')
            need('can_hold' in a.properties,'actor cannot handle rabbit')
        elif op in {'peek_rabbit','lift_rabbit'}:
            need('eyes_closed' not in ent['audience'].state,'audience cannot see reveal')
            need(ent['rabbit'].location==e['hat'] and 'hidden' in ent['rabbit'].state,'rabbit is not inside this hat')
            need(ent['hat'].location==a.id and 'open' in ent['hat'].state and 'bound' not in ent['hat'].state,'hat is not held open')
            if op=='lift_rabbit':need('can_hold' in a.properties,'actor cannot lift rabbit')
        elif op=='applaud_reveal':
            need('eyes_closed' not in a.state,'audience cannot see reveal')
            need(ent['rabbit'].location==e['holder'] and 'revealed' in ent['rabbit'].state,'rabbit was not revealed by this holder')
        elif op=='settle_rabbit':need(ent['rabbit'].location==ent['hat'].location==a.id,'rabbit and hat are not both held')
        elif op=='feed_rabbit':
            need(ent['rabbit'].location==e['stage'],'rabbit is not on stage')
            need(ent['food'].location==e['stage'] and 'rabbit_food' in ent['food'].properties,'rabbit food is not available')
            need('hungry' in ent['rabbit'].state,'rabbit is not hungry')
        elif op=='rabbit_final_image':
            need(ent['rabbit'].location==ent['hat'].location==e['stage'],'rabbit and hat are not together on stage')
            need(ent['food'].location==e['stage'] and 'offered' in ent['food'].state and 'hungry' in ent['rabbit'].state,'food was not offered to hungry rabbit')
            need('open' in ent['hat'].state and 'bound' not in ent['hat'].state,'hat is not open')
        return bad

    def render(self,sid):
        e=self.events[sid];op=e['op']
        if op not in SIGNATURES:return super().render(sid)
        # New common nouns may be declared in the brief. Their inflection uses
        # the existing typed regular-noun machinery; no English postprocessing.
        lex={k:dict(v) for k,v in LEXICON.items()}
        for entity in self.world.entities.values():
            if entity.kind!='person':lex['nouns'].setdefault(entity.noun,{})
        g=PoolLanguage(self.world,lexicon=lex);a=e['actor'];r=lambda k,**kw:g.ref(e[k],**kw)
        v,s,pp=g.v,g.s,g.pp
        if op=='show_premise':return scene(s(e['audience'],v('want',v('see',g.n('trick',det='a')))),
            s(e['rabbit'],g.adv(v('wait'),pp('in',r('source')))))
        if op=='take_hat':return scene(s(a,v('raise',r('hat',first=True))))
        if op=='promise_show':return scene(g.say_intent(a,'promise',v('show',pronoun('you'),g.n('surprise',det='a')),listener=e['audience']))
        if op=='failed_portal':return scene(g.using(a,v('tap',r('hat')),r('wand')),
            s(e['rabbit'],g.adv(v('stay'),pp('in',r('source')))))
        if op=='notice_binding':return scene(s(a,g.adv(v('spot',r('ribbon',adjectives=('tight',))),pp('around',r('hat')))))
        if op=='untie_hat':return scene(s(a,v('untie',r('ribbon'))))
        if op=='portal_rabbit':
            action=v('tap',r('hat'))
            if 'failed_attempt' in self.world.entities[e['hat']].state:action=g.adv(action,'again')
            return scene(g.using(a,action,r('wand')),s(e['rabbit'],g.adv(v('disappear'),pp('from',r('source')))))
        if op=='close_eyes':return scene(s(a,v('close',g.possess(pronoun(self.world.entities[a].pronoun),g.cn('eye'),number='plural'))))
        if op=='open_eyes':return scene(s(a,v('open',g.possess(pronoun(self.world.entities[a].pronoun),g.cn('eye'),number='plural'))))
        if op=='hide_rabbit':return scene(s(a,g.adv(v('put',r('rabbit')),pp('inside',r('hat')))))
        if op=='peek_rabbit':return scene(s(g.counted(2,'ear'),g.adv(v('appear'),pp('above',r('hat')))))
        if op=='lift_rabbit':return scene(g.either(s(a,g.adv(v('lift',r('rabbit')),pp('out of',r('hat')))),
                                                       s(a,g.adv(v('pull',r('rabbit')),pp('out of',r('hat'))))))
        if op=='applaud_reveal':return scene(g.either(s(a,v('clap')),s(a,v('laugh'))))
        if op=='settle_rabbit':return scene(s(a,g.adv(v('put',g.both(r('rabbit'),r('hat'))),pp('on',r('stage')))))
        if op=='feed_rabbit':return scene(s(a,g.adv(v('put',r('food')),pp('beside',r('rabbit')))))
        if op=='rabbit_final_image':return scene(s(e['rabbit'],g.adv(v('nibble',r('food')),pp('beside',r('hat',adjectives=('open',))))))
        raise ValueError(op)
