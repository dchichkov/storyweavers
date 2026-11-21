"""Multi-scale commitments and coarse world time over guarded native execution."""
from copy import deepcopy
from functools import lru_cache
import math
import random

from .event_scale_bank import BANK,DURATIONS

BANDS={'second':5,'minute':60,'hour':3600,'day':86400}


def duration(scenario,event):
    if (scenario,event) in DURATIONS:return dict(DURATIONS[scenario,event])
    dialogue={'goal','wish','promise','offer','ask','decline','invite','notice','admit','request','thank'}
    return ({'second':.95,'minute':.05} if set(event.split('_'))&dialogue
            else {'second':.15,'minute':.85})


def origins(pack,world):
    if hasattr(pack,'units'):
        return [(u['scenario'],u['prefix'],u['mapping']) for u in pack.units]
    return [(world.scenario,'', {e:e for e in world.entities})] if world.scenario in BANK else []


def _binding(pack,w,f):
    for scenario,prefix,mapping in origins(pack,w):
        if not prefix or f.kind.startswith(prefix):return scenario,prefix,mapping,f.kind[len(prefix):]
    return w.scenario,'',{},f.kind


def occurred(world,prefix,events):
    return any(e['frame']['kind'] in {prefix+k for k in events} for e in world.history)


def check(world,predicate,*,prefix='',mapping=None):
    mapping=mapping or {};kind=predicate['kind']
    if kind=='flag':return prefix+predicate['value'] in world.flags
    if kind=='occurred':return occurred(world,prefix,predicate['events'])
    entity=world.entities.get(mapping.get(predicate.get('entity'),predicate.get('entity')))
    if entity is None:return False
    if kind=='state':return predicate['value'] in entity.state
    if kind=='location':return entity.location==mapping.get(predicate['value'],predicate['value'])
    raise ValueError('unknown completion predicate: '+kind)


def initialize(pack,w,seed):
    n=w.narrative
    n.setdefault('schema','event-scales-v1')
    n.setdefault('clock',dict(seconds=0,step=0,seed=seed,model='authored_duration_bands'))
    n.setdefault('commitments',{})
    for scenario,prefix,mapping in origins(pack,w):
        if scenario not in BANK:continue
        spec=BANK[scenario];hero=mapping.get('hero',w.hero)
        root=prefix+scenario+' / '+spec['goal']
        common=dict(carrier=hero,source=scenario,prefix=prefix,mapping=mapping,
                    persistence=spec['persistence'],deadline_seconds=None)
        n['commitments'].setdefault(root,dict(common,name=spec['goal'],scale='story',status='active',
            duration=spec['duration'],parents=[],checks=spec['checks']+[dict(kind='flag',value='ended')]))
        for ep in spec['episodes']:
            key=prefix+scenario+' / '+ep['name']
            n['commitments'].setdefault(key,dict(common,name=ep['name'],scale='episode',status='proposed',
                parents=[root],events=ep['events'],offers=ep['offers'],duration=ep['duration'],
                checks=[dict(kind='occurred',events=ep['ends'])]))
    refresh(w)


def refresh(w):
    n=w.narrative;now=n['clock']['seconds']
    for key,c in n['commitments'].items():
        if c['status']=='abandoned':continue
        before=c['status'];missing=c['carrier'] not in w.entities
        satisfied=not missing and all(check(w,p,prefix=c['prefix'],mapping=c['mapping']) for p in c['checks'])
        started=c.get('started_at') is not None or c['scale']=='story'
        overdue=c.get('deadline_seconds') is not None and now>c['deadline_seconds']
        c['status']=('achieved' if satisfied else 'blocked' if missing or overdue else 'active' if started else 'proposed')
        if satisfied and before!='achieved':c['achieved_at']=now
        if not satisfied:c.pop('achieved_at',None)
    refresh_mission(w)


def refresh_mission(w):
    """Evaluate an explicit partial-order goal against executed receiving state.

    Capability labels alone are insufficient: an episode must have completed
    on the goal's physical carrier, after the prerequisite needs were achieved.
    """
    mission=w.narrative.get('mission')
    if not mission or mission.get('status')=='abandoned':return
    now=w.narrative['clock']['seconds'];needs=mission['needs']
    present=mission['carrier'] in w.entities
    by_name={need['name']:need for need in needs}
    # Needs are supplied in topological order; reject malformed graphs at entry.
    for need in needs:
        prerequisites=[by_name[name] for name in need.get('requires',[])]
        ready=present and all(n.get('status')=='achieved' for n in prerequisites)
        threshold=max((n['achieved_at'] for n in prerequisites if n.get('status')=='achieved'),default=0)
        evidence=[]
        if need.get('offer'):
            evidence=[key for key,c in w.narrative['commitments'].items()
                      if c['scale']=='episode' and c['status']=='achieved'
                      and c['carrier']==mission['carrier'] and need['offer'] in c.get('offers',[])
                      and c.get('started_at',-1)>=threshold]
        satisfied=ready and all(check(w,p) for p in need.get('checks',[])) and (not need.get('offer') or bool(evidence))
        before=need.get('status');need['status']='achieved' if satisfied else 'active' if ready else 'waiting'
        need['evidence']=evidence
        if satisfied and before!='achieved':need['achieved_at']=now
        if not satisfied:need.pop('achieved_at',None)
    completed=all(n['status']=='achieved' for n in needs)
    overdue=mission.get('deadline_seconds') is not None and now>mission['deadline_seconds']
    mission['status']='achieved' if completed else 'blocked' if not present or overdue else 'active'
    mission['overdue']=overdue


def set_mission(w,mission,seed=0):
    """Attach a named, physically carried goal without prescribing source stories."""
    mission=deepcopy(mission);seen=set()
    for need in mission['needs']:
        if need['name'] in seen or not set(need.get('requires',[]))<=seen:
            raise ValueError('needs must be uniquely named and topologically ordered')
        if not need.get('checks') and not need.get('offer'):raise ValueError('need has no completion evidence')
        seen.add(need['name'])
    if not seen:raise ValueError('mission needs at least one completion condition')
    w.narrative.setdefault('schema','event-scales-v1')
    w.narrative.setdefault('clock',dict(seconds=0,step=0,seed=seed,model='authored_duration_bands'))
    w.narrative.setdefault('commitments',{})
    w.narrative['mission']=mission
    refresh_mission(w)


def context(pack,w,f):
    scenario,prefix,mapping,kind=_binding(pack,w,f)
    if scenario not in BANK:return dict(memberships=[],duration=duration(scenario,kind),start_seconds=w.narrative['clock']['seconds'])
    spec=BANK[scenario]
    ep=next(ep for ep in spec['episodes'] if kind in ep['events'])
    root=prefix+scenario+' / '+spec['goal'];eid=prefix+scenario+' / '+ep['name']
    focus=f.patient or f.instrument or mapping.get('hero',w.hero)
    focus_name=w.entities[focus].noun
    chain=eid+' / '+focus
    memberships=[dict(id=root,scale='story',name=spec['goal']),dict(id=eid,scale='episode',name=ep['name']),
                 dict(id=chain,scale='chain',name='Work with '+focus_name,carrier=focus,parents=[eid])]
    for m in memberships:
        saved=w.narrative['commitments'].get(m['id'],{})
        m.update(status=saved.get('status','proposed'),carrier=saved.get('carrier',m.get('carrier',f.actor)))
    return dict(memberships=memberships,duration=duration(scenario,kind),
        start_seconds=w.narrative['clock']['seconds'],scope='receiving_prefix',
        persistence='until_next_change',relations=[dict(kind='contributes_to',source=chain,target=eid),
                                                  dict(kind='contributes_to',source=eid,target=root)],
        primary_goal=deepcopy(w.narrative.get('mission',{})))


class ScalePack:
    def __init__(self,base):self.base=base
    def __getattr__(self,name):return getattr(self.base,name)
    def scale_context(self,w,f):return context(self.base,w,f)
    def commit(self,w,f,sentence):
        # Validate before any clock/commitment mutation.
        if not any(candidate==f for _,candidate in self.base.candidates(w)):
            raise ValueError('forged or stale multi-scale event')
        info=context(self.base,w,f);before=w.snapshot();clock=w.narrative['clock']
        rng=random.Random(f"{clock['seed']}:{clock['step']}:{f.kind}")
        band=rng.choices(list(info['duration']),weights=list(info['duration'].values()))[0]
        start=clock['seconds'];record=self.base.commit(w,f,sentence)
        for m in info['memberships']:
            if m['scale']=='chain' and m['id'] not in w.narrative['commitments']:
                parent=w.narrative['commitments'][m['parents'][0]]
                w.narrative['commitments'][m['id']]=dict(deepcopy(parent),name=m['name'],scale='chain',
                    carrier=m['carrier'],parents=m['parents'],status='proposed')
            c=w.narrative['commitments'][m['id']]
            c.setdefault('started_at',start)
        clock['seconds']+=BANDS[band];clock['step']+=1
        if 'plot_execution' in w.narrative:
            from .plot_execution import advance
            scenario,prefix,mapping,_ = _binding(self.base,w,f)
            advance(w,record,scenario,prefix,mapping)
        refresh(w)
        record['time']=dict(start_seconds=start,end_seconds=clock['seconds'],duration_band=band,
                            duration_seconds=BANDS[band],distribution=info['duration'],relation='after_previous')
        record['event_scales']=info
        record['before']=before;record['after']=w.snapshot()
        return record


@lru_cache(maxsize=512)
def time_distribution(scenario,kinds):
    result={0:1.}
    for kind in kinds:
        next_result={}
        for elapsed,p in result.items():
            for band,q in duration(scenario,kind).items():
                value=elapsed+BANDS[band];next_result[value]=next_result.get(value,0)+p*q
        result=next_result
    return result


def annotate_scales(doc):
    """Historical memberships on intact source tokens; never future prediction."""
    scenario=doc['scenario']
    if scenario not in BANK:return doc
    spec=BANK[scenario];nodes={};root=scenario+' / '+spec['goal']
    nodes[root]=dict(name=spec['goal'],scale='story',carrier='hero',parents=[],duration=spec['duration'],
                     persistence=spec['persistence'],checks=deepcopy(spec['checks']))
    for ep in spec['episodes']:
        eid=scenario+' / '+ep['name']
        nodes[eid]=dict(name=ep['name'],scale='episode',carrier='hero',parents=[root],
                       duration=ep['duration'],offers=ep['offers'],completion_events=ep['ends'])
        for event in doc['events']:
            if event['kind'] not in ep['events']:continue
            focus=event['frame']['patient'] or event['frame']['instrument'] or event['frame']['actor']
            chain=eid+' / '+focus
            nodes.setdefault(chain,dict(name='Work with '+doc['entities'][focus]['initial']['noun'],
                                        scale='chain',carrier=focus,parents=[eid],duration=ep['duration']))
            event['scales']=[root,eid,chain];event['duration']=duration(scenario,event['kind'])
            for tid in event['token_ids']:doc['tokens'][tid]['memory']['scales']=event['scales']
    doc['event_scales']=dict(schema='event-scale-annotations-v1',scope='completed_source_observation',nodes=nodes)
    return doc


def validate_bank():
    from .storytelling.runtime import setup
    from .storytelling.seed_worlds.catalog import SEED_SCENARIOS
    assert set(BANK)==set(SEED_SCENARIOS)
    for scenario,spec in BANK.items():
        p,w=setup(scenario);events=[k for ep in spec['episodes'] for k in ep['events']]
        assert len(events)==len(set(events)) and set(events)==set(p.KERNELS),scenario
        for ep in spec['episodes']:
            assert set(ep['ends'])<=set(ep['events'])
        for dist in [spec['duration'],*(ep['duration'] for ep in spec['episodes']),*(duration(scenario,k) for k in events)]:
            assert set(dist)<=BANDS.keys() and all(v>0 for v in dist.values()) and math.isclose(sum(dist.values()),1.)
    return True
