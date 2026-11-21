"""Guarded authored story arcs using World, Frame and the existing word forest.

This is an opt-in content pack adapter, not a new sampler. Decisions mutate
physical carriers; narrative contracts record why an option is offered and
which cost/result was actually executed. No English parsing or runtime model.
"""
from copy import deepcopy
import math
from random import Random

from ...world import World,Entity,Fact,Frame,kernel
from ..operations import committed
from ..surface import Scene,claim
from .language import render,sequence


def entity(noun,kind='object',location='work',*,state=(),memes=None,pronoun='it'):
    return dict(noun=noun,kind=kind,location=location,state=list(state),memes=memes or {},pronoun=pronoun)


def event(name,*surface,after=(),requires=(),excludes=(),group=None,actor='hero',patient='',
          instrument='',destination='',effects=None,guards=None,base=0.,preferences=(),
          function='action',motivation=None,cost=None,opens=(),closes=(),qa=(),ending=False):
    return dict(name=name,surface=sequence(*surface),after=list(after),requires=list(requires),
        excludes=list(excludes),group=group,actor=actor,patient=patient,instrument=instrument,
        destination=destination,effects=effects or {},guards=guards or {},base=base,
        preferences=list(preferences),function=function,motivation=motivation,cost=cost,
        opens=list(opens),closes=list(closes),qa=list(qa),ending=ending)


class CraftedWorld(World):
    def facts_for_attention(self):
        facts=list(self.facts.values())
        for i,e in self.entities.items():
            facts.extend(Fact(i+'.'+name,e.noun+' carries '+name,('actor',name.lower(),i),value)
                         for name,value in e.memes.items())
            facts.extend(Fact('state:'+i+':'+s,e.noun+' is '+s,('state',i,s)) for s in e.state)
        return facts


class CraftedPack:
    event_limit=24
    LEXICON={}

    def __init__(self,spec):
        self.spec=deepcopy(spec);self.events={e['name']:e for e in spec['events']}
        if len(self.events)!=len(spec['events']):raise ValueError('duplicate crafted event')
        self.KERNELS={}
        for name,e in self.events.items():
            requires=['done:'+x for x in e['after']]+e['requires']
            excludes=['done:'+name]+e['excludes']+(['chosen:'+e['group']] if e['group'] else [])
            adds=['done:'+name]+(['chosen:'+e['group']] if e['group'] else [])+(['ended'] if e['ending'] else [])
            self.KERNELS[name]=kernel('crafted_'+name,requires,excludes,adds,base=e['base'],
                                     query=('care','fear','pride','trust','state'),preferences=e['preferences'])
        self.commit=committed(self.candidates)(self._effects)

    def make_world(self,seed=0,*,choice=None,care=None,pride=None):
        rng=Random(seed)
        if choice is not None and choice not in self.events:raise ValueError('unknown crafted branch')
        entities={i:Entity(id=i,properties={'animate','can_hold'} if e['kind']=='person' else {'physical'},
                          **{**deepcopy(e),'state':set(e['state'])}) for i,e in self.spec['entities'].items()}
        for name,value in (('Care',care),('Pride',pride)):
            if value is not None and (not isinstance(value,(float,int)) or not math.isfinite(value) or not 0<=value<=1):
                raise ValueError('trait override must be finite and in [0,1]')
            entities['hero'].memes[name]=rng.uniform(.2,.9) if value is None else value
        return CraftedWorld(self.spec['name'],entities,'hero',self.spec['helper'],self.spec['target'],
            self.spec['tool'],'work',{'premise':Fact('premise',self.spec['premise'],('goal','care'))},
            narrative={'storycraft':dict(schema='crafted-story-v1',title=self.spec['title'],
                desired_outcome=self.spec['desire'],choice_constraint=choice,history=[],obligations={},
                completed=False)})

    def candidates(self,w):
        result=[]
        forced=w.narrative['storycraft']['choice_constraint']
        for name,e in self.events.items():
            k=self.KERNELS[name]
            if not k.requires<=w.flags or k.excludes&w.flags:continue
            if e['group'] and forced and self.events[forced]['group']==e['group'] and name!=forced:continue
            if any(not set(states)<=w.entities[i].state for i,states in e['guards'].items()):continue
            if any(i not in w.entities for i in (e['actor'],e['patient'],e['instrument'],e['destination']) if i):continue
            result.append((k,Frame(k.name,e['actor'],e['patient'],e['instrument'],e['destination'])))
        return result

    def _effects(self,w,f):
        e=self.events[f.kind.removeprefix('crafted_')]
        for i,changes in e['effects'].items():
            carrier=w.entities[i]
            carrier.state.difference_update(changes.get('remove',()))
            carrier.state.update(changes.get('add',()))
            if 'location' in changes:
                if changes['location'] not in w.entities:raise ValueError('unbound effect location')
                carrier.location=changes['location']
            for concept,delta in changes.get('memes_delta',{}).items():
                carrier.memes[concept]=max(0.,min(1.,carrier.memes.get(concept,0.)+delta))
        memory=w.narrative['storycraft'];eid=len(w.history)+1
        for obligation in e['opens']:
            if obligation in memory['obligations']:raise ValueError('duplicate narrative obligation')
            memory['obligations'][obligation]=dict(carrier=e['actor'],setup_event=eid,status='open')
        for obligation in e['closes']:
            if obligation not in memory['obligations']:raise ValueError('closing an unplanted obligation')
            memory['obligations'][obligation].update(status='resolved',result_event=eid)
        memory['history'].append(dict(event=eid,name=e['name'],function=e['function'],
                                      motivation=e['motivation'],cost=e['cost']))
        if e['ending']:
            if any(o['status']=='open' for o in memory['obligations'].values()):raise ValueError('unpaid story obligation')
            memory['completed']=True

    def render_scene(self,w,f,tense='past',**options):
        if tense!='past':raise ValueError('crafted prototypes currently author past-tense narration only')
        e=self.events[f.kind.removeprefix('crafted_')]
        return Scene(render(e['surface'],w),deepcopy(e['qa']))

    def narrative_context(self,w,f):
        e=self.events[f.kind.removeprefix('crafted_')]
        return dict(scope='candidate_event',function=e['function'],desired_outcome=self.spec['desire'],
                    motivation=e['motivation'],proposed_cost=e['cost'],
                    earlier_events=[h['event'] for h in w.narrative['storycraft']['history']],
                    open_obligations=[k for k,v in w.narrative['storycraft']['obligations'].items() if v['status']=='open'])
