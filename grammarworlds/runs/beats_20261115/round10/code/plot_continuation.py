"""Rank and sample one executable plot stage at a time from the whole source pool.

Native suffix lookahead protects against binding an object for which the bank
contains no completion. This bounded planner favors reuse; it does not invent
new mechanics or solve arbitrary cross-source planning problems.
"""
from copy import deepcopy
import random

from .event_scales import ScalePack,initialize
from .memory_transfer import JoinedPack,decode_world,receiving_world,proposals
from .scale_continuation import _variants,_serialize
from .plot_execution import PLANS,set_plot,compatible
from .storytelling.runtime import generate,replay


def catalogue(documents):
    from .plot_bank import BANK
    return [c for scenario in BANK for c in proposals(documents,dict(scenario=scenario,extent='story'))]


def rank(w,pool,previous=(),*,lookahead=True):
    p=w.narrative['plot_execution'];start=p['active_stage'];options=[];rejections=[]
    if start==len(p['stages']):return [],[]
    for c in pool:
        for initial,unit,offset,resumed in _variants(w,c,previous):
            if not compatible(w,unit['scenario'],unit['mapping']):
                rejections.append(dict(source=unit['scenario'],reason='shared_binding_mismatch'));continue
            preview=initial.clone();native=JoinedPack([unit]);initialize(native,preview,0);driver=ScalePack(native)
            first=None
            try:
                for n in range(offset,len(unit['frames'])):
                    frames=driver.candidates(preview)
                    if not frames:break
                    record=driver.commit(preview,frames[0][1],'')
                    q=preview.narrative['plot_execution']
                    if first is None and q['active_stage']>start:
                        first=dict(stop=n+1,event=record['id'],stage=deepcopy(q['stages'][start]),
                                   plot=deepcopy(q))
                completion=preview.narrative['plot_execution']['active_stage']==len(p['stages'])
            except ValueError:
                completion=False
            if first is None:
                rejections.append(dict(source=unit['scenario'],reason='no_stage_progress'));continue
            if lookahead and not completion:
                rejections.append(dict(source=unit['scenario'],reason='no_native_suffix_completion'));continue
            bounded=deepcopy(unit);bounded['frames']=bounded['frames'][:first['stop']]
            imports=sum(x['kind'].startswith('import') for x in unit['leakage'])
            events=first['stop']-offset
            # Explicit positive weights; support is narrowed by guards/contracts.
            score=(4. if resumed else 1.)/(1.+.10*events+.05*imports)
            from .event_scales import time_distribution
            dist=time_distribution(unit['scenario'],tuple(f['kind'] for f in unit['frames'][offset:]))
            deadline=w.narrative['mission'].get('deadline_seconds')
            now=w.narrative['clock']['seconds']
            fit=sum(v for t,v in dist.items() if deadline is None or now+t<=deadline)
            score*=.001+fit
            options.append(dict(initial=initial,unit=bounded,summary=dict(source=unit['scenario'],
                stage=p['stages'][start]['name'],end=bounded['frames'][-1]['kind'],new_events=events,
                imports=imports,resumed=resumed,score=score,bindings=first['plot']['bindings'],
                completion_in_source_suffix=completion,deadline_probability=fit,
                stage_evidence=first['stage']['evidence'])))
    # Several complete source branches can have the identical current prefix.
    # Give that prefix one vote; do not count duplicate future branches as mass.
    distinct={}
    import json
    for option in options:
        u=option['unit']
        key=json.dumps([u['scenario'],u['prefix'],u['mapping'],u['frames'],u['source_options']],sort_keys=True)
        distinct.setdefault(key,option)
    options=list(distinct.values());total=sum(c['summary']['score'] for c in options)
    for c in options:c['summary']['probability']=c['summary']['score']/total
    return options,rejections


def run(pool,plan='changed_approach',*,seed=7,world=None,bindings=None,previous=(),lookahead=True,deadline_seconds=None,presentation=True,beat_budget=0):
    w=decode_world((world or receiving_world()).to_dict())
    if 'plot_execution' not in w.narrative:
        set_plot(w,plan,seed=seed,bindings=bindings,deadline_seconds=deadline_seconds)
    elif w.narrative['plot_execution']['kind']!=plan:
        raise ValueError('receiving plot differs from requested plan')
    if beat_budget:
        from .beat_generation import initialize
        initialize(w,beat_budget)
    if any(e not in w.entities for e in w.narrative['plot_execution']['bindings'].values()):
        raise ValueError('missing physical plot binding')
    # Callers resuming a saved run supply its returned units alongside the world.
    previous=deepcopy(list(previous));rng=random.Random(seed);rows=[];decisions=[];reason='stage_limit'
    for step in range(len(PLANS[plan]['stages'])):
        p=w.narrative['plot_execution']
        if p['status']=='abandoned':reason='abandoned';break
        if w.narrative['mission'].get('overdue'):reason='deadline';break
        if p['active_stage']==len(p['stages']):reason=p['status'];break
        candidates,rejections=rank(w,pool,previous,lookahead=lookahead)
        if not candidates:reason='no_compatible_continuation';break
        selected=rng.choices(range(len(candidates)),weights=[c['summary']['probability'] for c in candidates])[0]
        decisions.append(dict(stage=p['stages'][p['active_stage']]['name'],selected=selected,
            candidates=[c['summary'] for c in candidates],rejections=rejections,
            bindings_before=deepcopy(p['bindings'])))
        choice=candidates[selected]
        transfer=_serialize(dict(schema='joined-native-transfer-v1',initial_world=choice['initial'].to_dict(),
            units=[choice['unit']],decisions=[],leak=True))
        row=generate('joined',seed*100+step,transfer=transfer,multiscale=True,plot_annotations=True,continuations='expanded',presentation=False,
                     **({'beat_budget':beat_budget} if beat_budget else {}))
        replay(row);rows.append(row);w=decode_world(row['final_world'])
        previous=[u for u in previous if u['prefix']!=choice['unit']['prefix']]+[choice['unit']]
    p=w.narrative['plot_execution']
    if p['active_stage']==len(p['stages']):reason=p['status']
    result=dict(schema='plot-continuation-v1',plan=plan,seed=seed,reason=reason,
        story=' '.join(row['story'] for row in rows),rows=rows,decisions=decisions,
        final_world=w.to_dict(),plot=deepcopy(p),summary=dict(
            success=p['status']=='achieved' and not w.narrative['mission'].get('overdue'),
            completed_stages=p['active_stage'],total_stages=len(p['stages']),bindings=p['bindings'],
            sources=[r['options']['transfer']['units'][0]['scenario'] for r in rows],
            resumed=sum(d['candidates'][d['selected']]['resumed'] for d in decisions),
            seconds=w.narrative['clock']['seconds'],
            open_obligations=sum(o['status']=='open' for o in p['obligations']),
            missing_narration=sum(n['status']!='satisfied' for n in p['narration_requirements'].values())),units=_serialize(previous))
    result['raw_story']=result['story']
    if presentation:
        from .story_presentation import present
        result=present(result)
    return result
