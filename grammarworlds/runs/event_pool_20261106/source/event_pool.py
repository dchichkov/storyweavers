"""Retrieve authored event fragments from concise, role-based story briefs.

Retrieval is a small symbolic planner over reviewed programs. It returns ranked
alternatives with reasons; it never executes imported source code or prose.
"""
import argparse
from collections import Counter
from copy import deepcopy
import gzip
import json
from pathlib import Path
import random

from .catalog_attachment import bare_world, Unresolved
from .event_line_replay import replay, verify
from .pool_fragments import FRAGMENTS, ROOTS, entity_pool
from .pool_mechanics import PoolLines
from .pool_qa import questions
from .world import Entity


def expand_fragment(root, *, fragments=None, limit=128):
    """Expand nested fragments with lexical role substitution and provenance."""
    fragments=FRAGMENTS if fragments is None else fragments
    result=[]
    def walk(steps,scope,path,active):
        for index,step in enumerate(steps):
            here=path+[str(index)]
            if 'fragment' in step:
                key=step['fragment']
                if key in active:raise ValueError('recursive fragment: '+key)
                if key not in fragments:raise ValueError('unknown fragment: '+key)
                frag=fragments[key]
                if set(step['bind'])!=set(frag['params']):raise ValueError('fragment parameter mismatch: '+key)
                try:child={p:scope[v] for p,v in step['bind'].items()}
                except KeyError as exc:raise ValueError('unbound fragment role') from exc
                walk(frag['steps'],child,here+[key],active|{key})
            else:
                if step.get('op') not in PoolLines.fields:raise ValueError('unregistered operation')
                if set(step)-{'op'}!=PoolLines.fields[step['op']]:raise ValueError('operation signature mismatch')
                try:event={k:scope[v] for k,v in step.items() if k!='op'}
                except KeyError as exc:raise ValueError('unbound event role') from exc
                result.append(dict(event=dict(op=step['op'],**event),path=here))
                if len(result)>limit:raise ValueError('fragment expansion limit')
    walk(root['steps'],{r:r for r in root['roles']},[],set())
    return result


def _compatible(entity,spec):
    return (entity.kind==spec['kind'] and set(spec.get('properties',[]))<=entity.properties
            and set(spec.get('state',[]))<=entity.state
            and not set(spec.get('exclude_state',[]))&entity.state)


def _assemble(brief,root,world,records):
    w=world.clone();bindings={};audit=[];new=set();used=set()
    setting=brief.get('setting',w.setting or 'garden')
    if w.entities and setting!=w.setting:raise Unresolved('existing world setting differs')
    w.setting=setting
    # Environmental conditions are explicit input, never inferred from a goal.
    context=set(brief.get('environment',[]))
    if setting not in w.entities:
        w.entities[setting]=Entity(setting,setting,'place','',properties=context)
        audit.append(dict(action='construct',entity=setting,reason='brief setting',properties=sorted(context)))
    elif not context<=w.entities[setting].properties:raise Unresolved('existing environment lacks requested condition')
    supplied=brief.get('roles',{})
    if not set(supplied)<=set(root['roles']):raise Unresolved('brief has roles absent from fragment')
    for role,spec in root['roles'].items():
        hint=supplied.get(role,{})
        if isinstance(hint,str):hint={'entity':hint}
        if not isinstance(hint,dict):raise ValueError('role hint must be an object or entity ID')
        if set(hint)-{'entity','name','noun','properties','state','kind','prototype'}:raise ValueError('unknown role hint fields')
        requested=deepcopy(spec)
        requested['properties']=list(set(spec.get('properties',[]))|set(hint.get('properties',[])))
        if hint.get('kind',spec['kind'])!=spec['kind']:raise Unresolved('role kind conflict: '+role)
        def compatible(ent):
            return (_compatible(ent,requested) and (not hint.get('noun') or ent.noun==hint['noun'])
                    and ('state' not in hint or set(hint['state'])==ent.state))
        existing=hint.get('entity')
        inferred_location=spec.get('from_location')
        if not existing and not hint and inferred_location in bindings:
            carrier=w.entities[bindings[inferred_location]]
            if bindings[inferred_location] not in new and carrier.location in w.entities:
                existing=carrier.location
        if existing:
            if existing not in w.entities or not compatible(w.entities[existing]):raise Unresolved('incompatible existing '+role)
            if existing in used:raise Unresolved('distinct roles cannot alias: '+role)
            if 'state' in hint and set(hint['state'])!=w.entities[existing].state:raise Unresolved('existing state contradicts hint')
            bindings[role]=existing;used.add(existing)
            audit.append(dict(action='reuse',role=role,entity=existing,reason='explicit/inferred physical binding'))
            continue
        # Named local entities may satisfy the role without importing a copy.
        name=hint.get('name')
        local=[eid for eid,e in world.entities.items() if eid not in used and compatible(e)
               and (not name or name==e.noun)]
        preferred=world.hero if role=='actor' else (world.helper if role=='audience' else '')
        if len(local)>1 and preferred in local:local=[preferred]
        if len(local)==1:
            eid=local[0];bindings[role]=eid;used.add(eid)
            audit.append(dict(action='reuse',role=role,entity=eid,reason='compatible local carrier (world role resolves ties)'))
            continue
        if len(local)>1:raise Unresolved('ambiguous existing carriers for '+role)
        prototype=hint.get('prototype',spec['prototype'])
        if spec.get('construct')=='sky':
            ent=Entity('','sky','place',setting,properties={'airspace'});origin='constructed sky'
        else:
            if prototype not in records:raise Unresolved('missing prototype: '+prototype)
            ent=deepcopy(records[prototype]['entity']);origin=records[prototype]['source']
        # Explicit target details may replace defaults on NEW instances. Existing
        # entities above never receive inferred skill/property/state upgrades.
        if 'state' in hint:ent.state=set(hint['state'])
        if 'noun' in hint:ent.noun=hint['noun']
        if 'name' in hint:ent.noun=hint['name']
        if not _compatible(ent,requested):raise Unresolved('prototype does not satisfy '+role)
        eid='pool_'+role;serial=2
        while eid in w.entities:eid=f'pool_{role}_{serial}';serial+=1
        ent.id=eid
        # Source-scene goals are not required, but optional physical flavor can
        # travel with the prototype (e.g. ribbon, hat shape, concept magnitudes).
        if ent.kind=='person':ent.state=set(hint.get('state',[]))
        ent.properties.difference_update({'borrowed','belongs_to_friend'})
        w.entities[eid]=ent;bindings[role]=eid;used.add(eid);new.add(eid)
        audit.append(dict(action='import',role=role,entity=eid,prototype=prototype,source=origin,
                          reason='explicit anchor' if role in supplied else 'fragment dependency',
                          inherited_properties=sorted(ent.properties),inherited_state=sorted(ent.state)))
    for role,eid in bindings.items():
        if eid in new:
            dest=root['roles'][role]['location']
            destination=setting if dest=='@setting' else bindings[dest]
            w.entities[eid].location=destination
            audit.append(dict(action='place',entity=eid,destination=destination,reason='authored bundle placement'))
    w.hero=bindings.get('actor','');w.helper=bindings.get('audience','')
    w.target=bindings.get('rabbit',bindings.get('item',''));w.tool=bindings.get('hat','')
    return w,bindings,audit


def _template(key,root,expanded,bindings,world,audit):
    events={f'e{i:03d}':item['event'] for i,item in enumerate(expanded)}
    template=dict(schema='attached-event-lines-v1',roles={r:world.entities[e].kind for r,e in bindings.items()},
        events=events,lines=[],source=dict(kind='event-pool',fragment=key,authored_source=root['source'],
        assembly=audit,expansion={f'e{i:03d}':item['path'] for i,item in enumerate(expanded)}))
    for role in bindings:
        steps=[sid for sid,e in events.items() if role in [v for k,v in e.items() if k!='op']]
        if steps:template['lines'].append(dict(entity=role,steps=steps))
    return template


def feasible(world,template,bindings):
    """Dry-run on a clone, including guards/effects; no generated prose inspected."""
    w=world.clone();driver=PoolLines(w,template,bindings)
    while not driver.complete:
        candidates=driver.candidates(w)
        if not candidates:
            return False,{sid:driver.reasons(sid) for sid in driver.frontier()}
        driver.commit(candidates[0][1],'')
    return True,{}


def retrieve(brief,world=None,*,roots=None,fragments=None,records=None):
    if brief.get('schema')!='event-pool-v1':raise ValueError('unknown brief schema')
    world=world if world is not None else bare_world()
    roots=ROOTS if roots is None else roots;records=entity_pool() if records is None else records
    candidates=[];rejected=[]
    for key,root in roots.items():
        if brief.get('intent')!=root['intent']:continue
        if not set(root['anchors'])<=set(brief.get('roles',{})):
            rejected.append(dict(fragment=key,reason='required anchor mentions missing'));continue
        try:
            expanded=expand_fragment(root,fragments=fragments)
            w,b,audit=_assemble(brief,root,world,records)
            template=_template(key,root,expanded,b,w,audit)
            ok,blocking=feasible(w,template,b)
            if not ok:raise Unresolved('physical plan blocked: '+json.dumps(blocking,sort_keys=True))
        except Unresolved as exc:
            rejected.append(dict(fragment=key,reason=str(exc)));continue
        score=root['weight']+sum(1.5 for cue in brief.get('cues',[]) if cue in root['tags'])
        candidates.append(dict(fragment=key,score=score,world=w,template=template,bindings=b,audit=audit))
    total=sum(c['score'] for c in candidates)
    for c in candidates:c['probability']=c['score']/total
    return candidates,rejected


def attach(brief,world=None,*,seed=0,fragment=None,**options):
    candidates,rejected=retrieve(brief,world,**options)
    available=candidates
    if fragment is not None:candidates=[c for c in candidates if c['fragment']==fragment]
    if not candidates:raise Unresolved(json.dumps(dict(message='no compatible event fragment',rejected=rejected),sort_keys=True))
    chosen=random.Random(seed).choices(candidates,weights=[c['probability'] for c in candidates])[0]
    chosen['retrieval']={'candidates':[dict(fragment=c['fragment'],score=c['score'],probability=c['probability']) for c in available],
                         'rejected':rejected,'selection_seed':seed,'forced_fragment':fragment}
    chosen['template']['source']['retrieval']=deepcopy(chosen['retrieval'])
    chosen['template']['source']['brief']=deepcopy(brief)
    return chosen


def generate(brief,world=None,*,seed=0,heads=True,fragment=None,**options):
    attached=attach(brief,world,seed=seed,fragment=fragment,**options)
    row=replay(attached['world'],attached['template'],attached['bindings'],seed,heads=heads,driver_class=PoolLines)
    verify(row,attached['template'],driver_class=PoolLines)
    row['qa']=questions(row)
    return row,attached


def demo_brief(mode='magic'):
    hat={'properties':['portal_hat']} if mode=='magic' else {'properties':['rabbit_capacity'],'state':['open']}
    if mode=='stage':hat['prototype']='magic:stage_hat'
    return dict(schema='event-pool-v1',setting='garden',intent='reveal',
                roles={'rabbit':{},'hat':hat},cues=['gentle'])


def run(out,brief,count=20,world=None):
    if count<1:raise ValueError('positive count required')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    rows=[];assemblies={}
    for seed in range(count):
        for heads in (False,True):
            row,a=generate(brief,world,seed=seed,heads=heads)
            rows.append(row);assemblies.setdefault(a['fragment'],dict(world=a['world'].to_dict(),template=a['template'],bindings=a['bindings']))
    (out/'brief.json').write_text(json.dumps(brief,indent=2)+'\n')
    (out/'assemblies.json').write_text(json.dumps(assemblies,indent=2)+'\n')
    with gzip.open(out/'traces.jsonl.gz','wt') as f:
        for row in rows:f.write(json.dumps(row)+'\n')
    summary={}
    for heads in (False,True):
        subset=[r for r in rows if r['heads']==heads];metrics=Counter()
        for r in subset:metrics.update(r['metrics'])
        summary[str(heads)]=dict(runs=len(subset),completed=sum(r['status']=='complete' for r in subset),
            fragments=dict(Counter(r['source']['fragment'] for r in subset)),distinct_texts=len({r['story'] for r in subset}),**metrics)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'samples.md').write_text('# Event-pool samples\n\nSeeds 0–4, word heads on, no filtering.\n\n'+
        '\n\n'.join(f"## Seed {r['seed']} — {r['source']['fragment']}\n\n{r['story']}" for r in rows if r['heads'] and r['seed']<5)+'\n')
    print(json.dumps(summary,indent=2));print(rows[1]['story'])
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--brief',type=Path);parser.add_argument('--count',type=int,default=20)
    parser.add_argument('--mode',choices=['magic','stage','ambiguous'],default='magic')
    args=parser.parse_args();run(args.out,json.loads(args.brief.read_text()) if args.brief else demo_brief(args.mode),args.count)
