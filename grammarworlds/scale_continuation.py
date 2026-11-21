"""Sample native source episodes using persistent physical goals and coarse time.

The goal is a predicate graph, not an English intention parser. Source prose
stays intact; candidate programs stop at annotated episode boundaries. Native
prefixes are retained, or resumed when already executed on the same carriers.
"""
from copy import deepcopy
import json
import random

from .event_scale_bank import BANK
from .event_scales import ScalePack, initialize, refresh, set_mission, time_distribution
from .memory_transfer import JoinedPack, _prepare, decode_world, proposals, receiving_world
from .storytelling.runtime import generate, replay
from .world import Entity


def catalogue(documents):
    result=[]
    for scenario,spec in BANK.items():
        docs=[d for d in documents if d['scenario']==scenario]
        for ep in spec['episodes']:
            for end in ep['ends']:
                for c in proposals(docs,dict(event=end)):
                    c['episode']=ep['name'];c['offers']=ep['offers']
                    result.append(c)
    # Retrieval frequency is not a prior. Identical observed branches get one vote.
    unique={}
    for c in result:
        key=json.dumps([c['scenario'],c['frames'],c['source_options']],sort_keys=True)
        unique.setdefault(key,c)
    return list(unique.values())


def demonstration(seed=0):
    w=receiving_world()
    w.entities['trolley']=Entity('trolley','garden trolley','object','nia',properties={'portable'},state={'rattling'})
    w.entities['shadow']=Entity('shadow','shadow','object','workshop',properties={'portable'},state={'large'})
    set_mission(w,dict(name='Prepare a demonstration together',carrier='nia',deadline_seconds=3600,
        persistence='until_achieved_or_abandoned',needs=[
            dict(name='working trolley',checks=[dict(kind='state',entity='trolley',value='repaired')]),
            dict(name='controlled shadow',checks=[dict(kind='state',entity='shadow',value=s) for s in ('small','controlled')]),
            dict(name='shared performance',offer='performance',requires=['working trolley','controlled shadow']),
        ]),seed)
    return w


def _achieved(w):
    return {n['name'] for n in w.narrative['mission']['needs'] if n['status']=='achieved'}


def _serialize(value):
    return json.loads(json.dumps(value,default=lambda x:sorted(x) if isinstance(x,set) else x))


def _variants(world,candidate,previous):
    # Extend an existing compatible source program without resetting its objects.
    for old in previous:
        if old['scenario']!=candidate['scenario']:continue
        executed=[e['transfer']['native_event']['frame'] for e in world.history
                  if e.get('transfer',{}).get('prefix')==old['prefix']]
        # JSON normalization handles tuples in live records versus lists in archives.
        if len(executed)>=len(candidate['frames']) or _serialize(executed)!=_serialize(candidate['frames'][:len(executed)]):continue
        trial=world.clone();trial.flags.discard('ended');trial.flags.discard(old['prefix']+'complete')
        unit=deepcopy(candidate);unit.update(prefix=old['prefix'],mapping=deepcopy(old['mapping']),leakage=[])
        yield trial,unit,len(executed),True
    seen=set()
    for reuse in (True,False):
        trial=world.clone();trial.flags.discard('ended')
        try:unit=_prepare(trial,deepcopy(candidate),len(previous),{},True,reuse=reuse)
        except ValueError:continue
        key=tuple(sorted(unit['mapping'].items()))
        if key in seen:continue
        seen.add(key)
        yield trial,unit,0,False


def rank(world,candidates,previous=(),*,policy='contextual'):
    """Pure bounded lookahead; return feasible alternatives and normalized mass.

    Preview complete native programs rather than treating tag similarity as a
    guarantee. Time compatibility is the full duration-distribution mass before
    the deadline. All weights are hand-authored and exposed below.
    """
    if policy not in {'contextual','plain'}:raise ValueError('unknown policy')
    if world.narrative['mission']['status']=='achieved':
        return [],dict(stop=True,score=1.,probability=1.)
    feasible=[];before=_achieved(world);now=world.narrative['clock']['seconds']
    deadline=world.narrative['mission'].get('deadline_seconds')
    for c in candidates:
        for initial,unit,offset,resumed in _variants(world,c,previous):
            simulation=initial.clone();driver=JoinedPack([unit]);initialize(driver,simulation,0)
            driver=ScalePack(driver)
            try:
                for _ in range(driver.event_limit):
                    options=driver.candidates(simulation)
                    if not options:break
                    driver.commit(simulation,options[0][1],'')
            except ValueError:continue
            if not simulation.finished:continue
            newly=_achieved(simulation)-before
            kinds=tuple(f['kind'] for f in unit['frames'][offset:])
            dist=time_distribution(unit['scenario'],kinds)
            fit=sum(p for seconds,p in dist.items() if deadline is None or now+seconds<=deadline)
            imports=sum(x['kind'].startswith('import') for x in unit['leakage'])
            closed=sum(c['scale']=='story' and c['status']=='achieved' and
                       world.narrative['commitments'].get(key,{}).get('status')!='achieved'
                       for key,c in simulation.narrative['commitments'].items())
            if policy=='plain':score=1.
            else:
                score=(1.+200.*len(newly)+2.*closed)*(0.001+fit)/(1.+.1*len(kinds)+.05*imports)
            summary=dict(scenario=unit['scenario'],episode=unit['episode'],end=unit['requested_event'],
                events=len(kinds),prerequisite_events=max(0,len(kinds)-sum(k in next(e for e in BANK[unit['scenario']]['episodes'] if e['name']==unit['episode'])['events'] for k in kinds)),
                resumed=resumed,imports=imports,progress=sorted(newly),closed_stories=closed,
                deadline_probability=fit,expected_seconds=sum(t*p for t,p in dist.items()),score=score,
                bindings=unit['mapping'])
            feasible.append(dict(initial=initial,unit=unit,summary=summary))
    stop_score=.02
    total=stop_score+sum(c['summary']['score'] for c in feasible)
    for c in feasible:c['summary']['probability']=c['summary']['score']/total
    return feasible,dict(stop=True,score=stop_score,probability=stop_score/total)


def run(candidates,world=None,*,seed=0,policy='contextual',max_episodes=6):
    if max_episodes<1:raise ValueError('max_episodes must be positive')
    w=decode_world((world or demonstration(seed)).to_dict());refresh(w)
    rng=random.Random(seed);units=[];rows=[];decisions=[];reason='episode_limit'
    for step in range(max_episodes):
        mission=w.narrative['mission']
        if mission['status']=='abandoned':reason='abandoned';break
        if mission['status']=='blocked':reason='deadline' if mission.get('overdue') else 'missing_carrier';break
        feasible,stop=rank(w,candidates,units,policy=policy)
        selected=rng.choices(range(len(feasible)+1),weights=[c['summary']['probability'] for c in feasible]+[stop['probability']])[0]
        decisions.append(dict(step=step,start_seconds=w.narrative['clock']['seconds'],
            mission=deepcopy(mission),candidates=[c['summary'] for c in feasible]+[stop],selected=selected))
        if selected==len(feasible):reason='goal_achieved' if mission['status']=='achieved' else 'sampled_stop' if feasible else 'no_feasible_episode';break
        chosen=feasible[selected]
        transfer=_serialize(dict(schema='joined-native-transfer-v1',initial_world=chosen['initial'].to_dict(),
            units=[chosen['unit']],decisions=[],leak=True))
        row=generate('joined',seed*100+step,transfer=transfer,continuations='expanded',multiscale=True)
        replay(row);rows.append(row);w=decode_world(row['final_world'])
        units=[u for u in units if u['prefix']!=chosen['unit']['prefix']]+[chosen['unit']]
    # Completion is always assessed from the resulting state, including at the limit.
    mission=w.narrative['mission']
    if mission['status']=='achieved':reason='goal_achieved'
    return dict(schema='scale-continuation-v1',seed=seed,policy=policy,reason=reason,
        mission=deepcopy(mission),clock=deepcopy(w.narrative['clock']),
        story='\n\n'.join(r['story'] for r in rows),rows=rows,decisions=decisions,
        summary=dict(success=mission['status']=='achieved' and not mission['overdue'],episodes=len(rows),
            sources=[r['options']['transfer']['units'][0]['scenario'] for r in rows],
            seconds=w.narrative['clock']['seconds'],needs_achieved=len(_achieved(w)),
            resumed=sum(d['candidates'][d['selected']].get('resumed',False) for d in decisions),
            irrelevant=sum(not d['candidates'][d['selected']].get('progress') for d in decisions if not d['candidates'][d['selected']].get('stop'))))
