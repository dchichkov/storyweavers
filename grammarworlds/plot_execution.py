"""Small executable plot contracts over guarded physical events.

Two reusable trajectories bind receiving identities, maintain setup/payoff
obligations, and separate character-state evidence from reader exposure.
"""
from copy import deepcopy
from functools import lru_cache

from .event_scales import check, set_mission
from .event_scale_bank import BANK as SCALES
from .plot_annotations import _context


def stage(name,roles,condition,*,link=None):
    return dict(name=name,allowed_roles=roles.split(),condition=condition,
                requires_link=link,require_narration=True)


PLANS={
 'adapt_gift':dict(name='Make a useful gift for someone',variables=['object','recipient'],stages=[
    stage('establish_desire','desire promise','introduce'),
    stage('adapt_for_recipient','revision','adapt'),
    stage('give_same_object','payoff final_image','give'),
    stage('show_useful_result','final_image','ending')]),
 'changed_approach':dict(name='Learn from a failed attempt',variables=['object'],stages=[
    stage('establish_desire','desire promise','introduce'),
    stage('attempt_fails','failed_attempt setback','changed'),
    stage('discover_why','discovery clue','discovery',link='setback'),
    stage('change_approach','revision decisive_action','changed',link='discovery'),
    stage('achieve_goal','payoff decisive_action','payoff',link='setup'),
    stage('show_changed_world','final_image','ending')]),
}


@lru_cache(maxsize=32)
def target_id(scenario):
    from .storytelling.runtime import setup
    return setup(scenario)[1].target


def source_bindings(scenario,mapping):
    from .plot_bank import BANK
    spec=BANK[scenario];result=dict(object=mapping.get(target_id(scenario),target_id(scenario)))
    for role in ('recipient','beneficiary','partner'):
        values=spec['roles'].get(role,[])
        if len(values)==1:
            result['recipient']=mapping.get(values[0],values[0]);break
    return result


def set_plot(w,name,*,seed=0,bindings=None,deadline_seconds=None):
    if name not in PLANS:raise ValueError('unknown plot contract')
    if 'plot_execution' in w.narrative:raise ValueError('receiver already has a plot')
    spec=deepcopy(PLANS[name]);bindings=dict(bindings or {})
    if set(bindings)-set(spec['variables']):raise ValueError('unknown plot binding')
    if any(value not in w.entities for value in bindings.values()):raise ValueError('plot binding has no physical carrier')
    if w.hero not in w.entities:raise ValueError('plot needs a protagonist')
    stages=spec['stages']
    for i,s in enumerate(stages):
        s.update(status='pending',requires=[stages[i-1]['name']] if i else [],evidence=None)
    w.narrative['plot_execution']=dict(schema='executable-plot-v1',kind=name,name=spec['name'],
        carrier=w.hero,variables=spec['variables'],bindings=bindings,stages=stages,active_stage=0,
        status='active',obligations=[],knowledge_evidence=[],character_knowledge={},
        reader_knowledge=[],narration_requirements={})
    set_mission(w,dict(name=spec['name'],carrier=w.hero,deadline_seconds=deadline_seconds,
        needs=[dict(name=s['name'],checks=[dict(kind='flag',value='plot:'+s['name'])],
                    requires=s['requires']) for s in stages]),seed)


def compatible(w,scenario,mapping):
    p=w.narrative['plot_execution'];values=source_bindings(scenario,mapping)
    return all(values.get(k)==v for k,v in p['bindings'].items())


def _changed(w,before,ids):
    return any(e in before['entities'] and e in w.entities and
               (before['entities'][e]['state']!=sorted(w.entities[e].state) or
                before['entities'][e]['location']!=w.entities[e].location)
               for e in ids)


def advance(w,record,scenario,prefix,mapping):
    p=w.narrative.get('plot_execution')
    if not p or p['status'] in {'achieved','abandoned'} or p['active_stage']>=len(p['stages']):return
    if p['carrier'] not in w.entities or any(e not in w.entities for e in p['bindings'].values()):
        p['status']='blocked';return
    kind=record['frame']['kind'][len(prefix):]
    info=_context(scenario,kind,prefix,mapping,w.entities,w.history[:-1])
    if info is None or not compatible(w,scenario,mapping):return
    values=source_bindings(scenario,mapping);before=record['before'];eid=record['id']
    current=p['stages'][p['active_stage']]
    completed=[s for s in p['stages'] if s['status']=='achieved']
    setup_ids={s['evidence']['event'] for s in completed if s['condition']=='introduce'}
    setback_ids={s['evidence']['event'] for s in completed if s['name']=='attempt_fails'}
    prior_discoveries={e['event'] for e in p['knowledge_evidence']}
    links=info['incoming_links']
    # Knowledge is constrained to an actual clue/discovery linked to this setback.
    if info['role'] in {'clue','discovery'} and any(l['source_event'] in setback_ids for l in links):
        p['knowledge_evidence'].append(dict(event=eid,kind=kind,actor=record['frame']['actor'],
            source_links=deepcopy(links),binding=values['object'],basis='executed_authored_discovery'))
        for entity,old in before['entities'].items():
            if entity not in w.entities:continue
            added=w.entities[entity].state-set(old['state'])
            for value in sorted(added):
                if value.startswith(('knows_','understands_')):
                    p['character_knowledge'].setdefault(entity,[]).append(dict(state=value,event=eid,
                        basis='native_epistemic_state_change'))
    if info['role'] not in current['allowed_roles']:return
    if any(k not in values or values[k] not in w.entities for k in p['variables']):return
    if len(set(values[k] for k in p['variables']))!=len(p['variables']):return
    obj=w.entities[values['object']];condition=current['condition']
    if condition=='introduce':
        if info['roles'].get('protagonist')!=[p['carrier']]:return
    elif condition=='adapt':
        # A changed object, with an authored adaptation function and a user.
        if record['frame']['patient']!=obj.id or not _changed(w,before,[obj.id]):return
        source_offers={tag for ep in SCALES[scenario]['episodes'] if kind in ep['events'] for tag in ep['offers']}
        if 'accessible_design' not in source_offers:return
    elif condition=='give':
        recipient=values['recipient']
        if w.entities[recipient].kind!='person' or recipient==p['carrier']:return
        if record['frame']['patient']!=obj.id or obj.location!=recipient:return
        if before['entities'][obj.id]['location']==recipient:return
    elif condition=='changed':
        relevant=info['roles'].get('central_object',[obj.id])+info['roles'].get('instrument',[])
        if not _changed(w,before,relevant):return
    elif condition=='discovery':
        if not any(e['event']==eid for e in p['knowledge_evidence']):return
    elif condition=='payoff':
        if not _changed(w,before,list(w.entities)):return
    elif condition=='ending':
        if not all(check(w,c,prefix=prefix,mapping=mapping) for c in SCALES[scenario]['checks']):return
        if p['kind']=='adapt_gift' and obj.location!=values['recipient']:return
        if not any(l['source_event'] in {s['evidence']['event'] for s in completed} for l in links):
            # Some source endings prove physical usability directly, e.g. pottery.
            if not _changed(w,before,info['roles'].get('recipient',[])+[obj.id]):return
    required=current['requires_link']
    if required=='setback' and not any(l['source_event'] in setback_ids for l in links):return
    if required=='discovery' and not any(l['source_event'] in prior_discoveries and l['relation']=='uses_discovery' for l in links):return
    if required=='setup' and not any(l['source_event'] in setup_ids and l['relation'] in {'payoff_of','revises_original_goal'} for l in links):
        if not all(check(w,c,prefix=prefix,mapping=mapping) for c in SCALES[scenario]['checks']):return
    if condition=='introduce':
        p['bindings'].update({k:values[k] for k in p['variables']})
        p['obligations'].append(dict(name='resolve_initial_desire',setup_event=eid,status='open',
                                    bindings=deepcopy(p['bindings']),resolution_event=None))
    current.update(status='achieved',evidence=dict(event=eid,source=scenario,source_kind=kind,
        bindings=deepcopy(p['bindings']),incoming_links=deepcopy(links)),achieved_at=w.narrative['clock']['seconds'])
    # An ending can show the effect on the object's user instead of naming the
    # object again (e.g. Grandpa's thumb rests in the cup's new thumb rest).
    # Only an actually changed recipient/beneficiary qualifies this way.
    affected_users=[e for role in ('recipient','beneficiary') for e in info['roles'].get(role,[])
                    if condition=='ending' and _changed(w,before,[e])]
    p['narration_requirements'][current['name']]=dict(event=eid,status='pending',
        expected_entities=sorted(set([*p['bindings'].values(),
            *info['roles'].get('central_object',[]),*info['roles'].get('instrument',[]),
            *affected_users,
            *([] if condition=='ending' else [p['carrier']])])),observed_entities=[])
    record['plot_transition']=dict(stage=current['name'],index=p['active_stage'],bindings=deepcopy(p['bindings']))
    w.flags.add('plot:'+current['name']);p['active_stage']+=1
    if condition in {'give','payoff'}:
        for obligation in p['obligations']:
            obligation.update(status='resolved',resolution_event=eid)
    if p['active_stage']==len(p['stages']):p['status']='structurally_complete'


def finalize_narration(w,record):
    """Typed referents and actual narration are supplied by generation/replay.

    This records exposure, not a claim that every sentence is stylistically good
    or that a character learned every fact the narrator described.
    """
    p=w.narrative.get('plot_execution')
    if not p:return
    transition=record.get('plot_transition')
    if record.get('narrated'):
        p['reader_knowledge'].append(dict(event=record['id'],referents=list(record.get('referents',[])),
            stage=transition['stage'] if transition else None,basis='narrated_native_event'))
    if transition:
        need=p['narration_requirements'][transition['stage']]
        seen=set(record.get('referents',[]))|set(record.get('speakers',[]))
        need['observed_entities']=sorted(seen&set(need['expected_entities']))
        need['status']='satisfied' if record.get('narrated') and need['observed_entities'] else 'missing'
    if p['active_stage']==len(p['stages']):
        p['status']='achieved' if all(n['status']=='satisfied' for n in p['narration_requirements'].values()) else 'narration_incomplete'
    record['after']=w.snapshot()
