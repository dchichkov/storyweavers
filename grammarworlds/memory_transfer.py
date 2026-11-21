"""Transfer source mechanics through live, reversible entity views.

Intact annotated documents select bounded native programs. Missing physical
carriers may be imported; effects are always executed by the donor's guards,
never copied from an observed after-state. This intentionally permits source
motives, props and local physics to accompany a character.
"""
from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
import math
import random
import re

from .grammar import Node
from .world import Entity, Fact, Frame, World
from .storytelling.runtime import setup, generate, replay
from .storytelling.plans import plan
from .storytelling.seed_worlds.catalog import SEED_SCENARIOS
from .story_memory import validate


def receiving_world():
    return World('joined', {
        'nia': Entity('nia','Nia','person','workshop',pronoun='she',properties={'can_hold','can_help'}),
        'omar': Entity('omar','Omar','person','workshop',pronoun='he',properties={'can_hold','can_help'}),
        'workshop': Entity('workshop','workshop','place','workshop',properties={'reachable'}),
    }, 'nia','omar','','','workshop',{})


def decode_world(data):
    data=deepcopy(data)
    data['entities']={key:Entity(**{**e,'properties':set(e['properties']),'state':set(e['state'])})
                      for key,e in data['entities'].items()}
    data['facts']={key:Fact(**{**f,'tags':tuple(f['tags'])}) for key,f in data['facts'].items()}
    data['flags']=set(data['flags'])
    return JoinedWorld(**data)


class JoinedWorld(World):
    def facts_for_attention(self):
        facts=list(self.facts.values())
        for e in self.entities.values():
            facts += [Fact('loc:'+e.id,e.noun+' is at '+e.location,('physical','location',e.id)),
                      Fact('state:'+e.id,e.noun+': '+', '.join(sorted(e.state)),('physical','state',e.id))]
            facts += [Fact(e.id+'.'+name,e.noun+': '+name,('actor',name.lower(),e.id),value)
                      for name,value in e.memes.items()]
            facts += [Fact('state:'+e.id+':'+state,e.noun+': '+state,('physical','state',e.id))
                      for state in sorted(e.state)]
        facts += [Fact('flag:'+flag,flag,('history',)) for flag in sorted(self.flags)]
        facts += [Fact('event:'+str(e['id']),e['frame']['kind'],('recent',)) for e in self.history]
        return facts


def _frame(data):
    return Frame(**{**data,'cause_ids':tuple(data['cause_ids'])})


def _words(text):
    return set(re.findall(r'[a-z]+',text.lower()))-{'a','an','the','to','with','and','of','for','in','on'}


def proposals(documents, request):
    """A normalized distribution over distinct observed branches, not seed counts.

    `event` is an exact event name. `query` ranks names, carrier nouns and action
    annotations; it is a lexical retrieval cue, not an intention parser.
    `extent=story` extends through the source ending. Default stops at the match.
    """
    if not (request.get('event') or request.get('query') or request.get('scenario')):
        raise ValueError('supply an event, query or source scenario')
    if request.get('extent','event') not in {'event','story'}:
        raise ValueError('extent must be event or story')
    grouped={}
    for doc in documents:
        if doc['scenario'] not in SEED_SCENARIOS:continue
        if request.get('scenario') and request['scenario']!=doc['scenario']:continue
        events=doc['events'];matches=[];document_words=set()
        for i,event in enumerate(events):
            if request.get('event') and request['event'] not in {event['kind'],event['name']}:continue
            words=_words(event['name'])
            for entity in event['participants']:
                initial=doc['entities'][entity]['initial']
                if initial:words |= _words(initial['noun'])
            for tid in event['token_ids']:
                for c in doc['tokens'][tid]['candidates']:
                    action=doc['attributes'][c['attributes']].get('action') or {}
                    words |= _words(action.get('lemma',''))
            document_words.update(words)
            overlap=len(words & _words(request.get('query','')))
            if request.get('query') and not overlap:continue
            matches.append((overlap,i))
        if not matches:continue
        # Prefer the strongest match; later ties tend to include the result.
        overlap,index=max(matches)
        document_overlap=len(document_words & _words(request.get('query','')))
        stop=len(events) if request.get('extent')=='story' else index+1
        selected=events[:stop]
        signature=json.dumps(dict(frames=[e['frame'] for e in selected],
                                  options=doc.get('source_options',{})),sort_keys=True)
        key=(doc['scenario'],signature)
        reference=dict(document=doc['id'],scenario=doc['scenario'],seed=doc['seed'],
                       text_sha256=doc['text_sha256'],matched_event=events[index]['id'],
                       event_ids=[e['id'] for e in selected],token_ids=[t for e in selected for t in e['token_ids']])
        if key not in grouped:
            grouped[key]=dict(scenario=doc['scenario'],seed=doc['seed'],source_options=doc.get('source_options',{}),
                frames=[deepcopy(e['frame']) for e in selected],references=[],score=1.+overlap,
                document_overlap=document_overlap,
                requested_event=events[index]['kind'],prerequisite_events=stop-1)
        grouped[key]['references'].append(reference)
    candidates=list(grouped.values())
    if request.get('query') and candidates:
        # A precise cue should not retrieve an unrelated repair merely because
        # one generic verb matches. Keep maximal whole-document cue coverage.
        best=max(c['document_overlap'] for c in candidates)
        candidates=[c for c in candidates if c['document_overlap']==best]
    total=sum(c['score'] for c in candidates)
    for c in candidates:c['probability']=c['score']/total
    return candidates


def _source(unit):
    options = {k:v for k,v in unit.get('source_options',{}).items() if k not in {'multiscale','plot_annotations'}}
    return setup(unit['scenario'],unit['seed'],**options)


def _prepare(world, unit, index, hints, leak, *, reuse=True):
    """Bind identity, import initial carriers, record every added attribute."""
    pack, source=_source(unit)
    serial=index
    while (any(e.startswith(f'u{serial}__') for e in world.entities)
           or any(f.startswith(f'u{serial}__') for f in world.flags)
           or any(e.get('transfer',{}).get('prefix')==f'u{serial}__' for e in world.history)):
        serial+=1
    prefix=f'u{serial}__';mapping={};audit=[]
    if set(hints)-source.entities.keys():raise ValueError('unknown source binding')
    automatic={source.hero:world.hero} if world.hero in world.entities else {}
    if source.helper != source.hero and world.helper in world.entities:
        automatic[source.helper]=world.helper
    for sid,entity in source.entities.items():
        target=hints.get(sid,automatic.get(sid))
        if target is None and entity.kind=='place' and sid==source.setting:
            target=world.setting
        if target is None:
            # Reuse only a unique matching physical description, never "any object".
            hits=[eid for eid,e in world.entities.items() if e.kind==entity.kind and e.noun==entity.noun
                  and entity.properties<=e.properties and eid not in mapping.values()]
            if not hits and leak and sid==source.target and entity.state:
                # A unique problem-state match can bind an analogous receiving
                # target. Do not use generic kind/portability alone as evidence.
                hits=[eid for eid,e in world.entities.items() if e.kind==entity.kind
                      and entity.properties<=e.properties and entity.state<=e.state
                      and eid not in mapping.values()]
            target=hits[0] if reuse and len(hits)==1 and entity.kind!='person' else prefix+sid
        if target in mapping.values():raise ValueError('distinct source roles cannot alias')
        if target in world.entities and world.entities[target].kind!=entity.kind:
            raise ValueError('mistyped receiving carrier: '+target)
        if sid in hints and target not in world.entities:raise ValueError('binding names missing target carrier')
        mapping[sid]=target
    # Old worlds use location strings that are not entities. Materialize them.
    locations={e.location for e in source.entities.values()}|{source.setting}
    for loc in locations-source.entities.keys():
        mapping[loc]=world.setting if loc==source.setting else prefix+re.sub(r'\W+','_',loc)
    for sid,entity in source.entities.items():
        tid=mapping[sid]
        if tid not in world.entities:
            imported=deepcopy(entity);imported.id=tid;imported.location=mapping.get(entity.location,entity.location)
            world.entities[tid]=imported
            audit.append(dict(kind='import_entity',source=sid,target=tid,initial=asdict(imported)))
        else:
            target=world.entities[tid]
            if entity.kind!='person' and entity.noun!=target.noun:
                if not leak:raise ValueError('renamed role analogy requires leakage')
                audit.append(dict(kind='role_analogy',source=sid,target=tid,
                                  source_noun=entity.noun,target_noun=target.noun))
            if entity.kind=='person':
                additions=entity.state-target.state;props=entity.properties-target.properties
                memes={k:v for k,v in entity.memes.items() if k not in target.memes}
                if (additions or props or memes) and not leak:
                    raise ValueError('person needs source attributes; enable leakage or supply compatible carrier')
                if additions or props or memes:
                    target.state.update(additions);target.properties.update(props);target.memes.update(memes)
                    audit.append(dict(kind='character_attributes',source=sid,target=tid,
                                      states=sorted(additions),properties=sorted(props),memes=memes))
            elif not entity.properties<=target.properties:
                raise ValueError('receiving object lacks source affordances: '+tid)
    for sid in locations-source.entities.keys():
        tid=mapping[sid]
        if tid not in world.entities:
            world.entities[tid]=Entity(tid,sid,'place',tid,properties={'reachable'})
            audit.append(dict(kind='import_place',source=sid,target=tid))
    for flag in source.flags:world.flags.add(prefix+flag)
    if world.hero not in world.entities:world.hero=mapping[source.hero]
    if world.helper not in world.entities:world.helper=mapping[source.helper]
    for key,fact in source.facts.items():
        world.facts[prefix+key]=replace(fact,id=prefix+key)
    unit.update(prefix=prefix,mapping=mapping,leakage=audit)
    return unit


def _map_node(node,mapping):
    def attributes(x,key=''):
        if isinstance(x,dict):return {k:attributes(v,k) for k,v in x.items()}
        if isinstance(x,list):return [attributes(v,key) for v in x]
        return mapping.get(x,x) if isinstance(x,str) and key in {'entity','speaker','listener'} else x
    label=node.label
    if label.startswith(('referent:','scoped_referent:','clause.subject:','dialogue.speaker:','dialogue.listener:')):
        parts=label.split(':');label=':'.join([parts[0],*(mapping.get(p,p) for p in parts[1:])])
    return replace(node,label=label,
        attributes=json.dumps(attributes(json.loads(node.attributes))) if node.attributes else '',
        children=tuple(_map_node(c,mapping) if isinstance(c,Node) else c for c in node.children))


class JoinedPack:
    def __init__(self,units):
        self.units=deepcopy(units);self.KERNELS={};self.sources=[]
        self.event_limit=sum(len(u['frames']) for u in units)+1
        for i,u in enumerate(self.units):
            pack,initial=_source(u);self.sources.append((pack,initial))
            for n,frame in enumerate(u['frames']):
                k=pack.KERNELS[frame['kind']];prefix=u['prefix']
                requires={prefix+x for x in k.requires}
                if i:requires.add(self.units[i-1]['prefix']+'complete')
                adds={prefix+x for x in k.adds}
                if n==len(u['frames'])-1:
                    adds.add(prefix+'complete')
                    if i==len(units)-1:adds.add('ended')
                name=prefix+k.name
                self.KERNELS[name]=replace(k,name=name,requires=frozenset(requires),
                    excludes=frozenset(prefix+x for x in k.excludes),adds=frozenset(adds))

    def view(self,w,index):
        u=self.units[index];mapping=u['mapping'];inverse={v:k for k,v in mapping.items()}
        local=self.sources[index][1].clone()
        for sid in local.entities:
            tid=mapping[sid]
            if tid not in w.entities:raise ValueError('missing receiving carrier: '+tid)
            e=deepcopy(w.entities[tid]);e.id=sid;e.location=inverse.get(e.location,e.location)
            local.entities[sid]=e
        local.flags={f[len(u['prefix']):] for f in w.flags if f.startswith(u['prefix'])}
        local.history=[]
        for e in w.history:
            if e.get('transfer',{}).get('prefix')==u['prefix']:
                saved=deepcopy(e['transfer']['native_event'])
                saved.update(referents=[inverse[x] for x in e.get('referents',[]) if x in inverse],
                             speakers=[inverse[x] for x in e.get('speakers',[]) if x in inverse],narrated=e.get('narrated',False))
                local.history.append(saved)
        local.focus=inverse.get(w.focus,'')
        return local

    def _next(self,w):
        for index,u in enumerate(self.units):
            if u['prefix']+'complete' not in w.flags:
                n=sum(e.get('transfer',{}).get('prefix')==u['prefix'] for e in w.history)
                return index,n
        return None

    def _bound(self,index,frame,w):
        u=self.units[index];m=u['mapping']
        def cause(c):
            parts=c.split(':')
            if parts[0] in {'loc','state'} and len(parts)>1 and parts[1] in m:
                return ':'.join([parts[0],m[parts[1]],*parts[2:]])
            if c.startswith('flag:'):return 'flag:'+u['prefix']+c[5:]
            if '.' in c and c.rsplit('.',1)[0] in m:
                entity,feature=c.rsplit('.',1);return m[entity]+'.'+feature
            if c.startswith('event:'):
                source_id=int(c[6:])
                return next('event:'+str(e['id']) for e in w.history
                            if e.get('transfer',{}).get('prefix')==u['prefix']
                            and e['transfer']['native_event']['id']==source_id)
            return u['prefix']+c
        return Frame(u['prefix']+frame.kind,*(m.get(getattr(frame,k),getattr(frame,k))
            for k in ('actor','patient','instrument','destination')),
            tuple(cause(c) for c in frame.cause_ids))

    def candidates(self,w):
        item=self._next(w)
        if item is None or w.finished:return []
        index,n=item;u=self.units[index]
        if n>=len(u['frames']):return []
        try:local=self.view(w,index)
        except ValueError:return []
        expected=_frame(u['frames'][n])
        for _,frame in self.sources[index][0].candidates(local):
            if frame==expected:
                bound=self._bound(index,frame,w)
                return [(self.KERNELS[bound.kind],bound)]
        return []

    def render_scene(self,w,f,tense,*,continuations):
        index,n=self._next(w);u=self.units[index];local=self.view(w,index)
        lexicon=deepcopy(getattr(self.sources[index][0],'LEXICON',{}))
        for sid,e in local.entities.items():
            if e.kind!='person' and e.noun!=self.sources[index][1].entities[sid].noun:
                # Keep the donor's plural/mass lexicon intact for unchanged nouns.
                from .portable.language import load_lexicon
                lexicon.setdefault('nouns',{}).setdefault(e.noun,deepcopy(load_lexicon()['nouns'].get(e.noun,{})))
        rendered=plan(local,_frame(u['frames'][n]),tense,lexicon,continuations=continuations)
        if rendered is None:return None
        # Source QA contains hardcoded names/motives. Never relabel it as target QA.
        return replace(rendered,node=_map_node(rendered.node,u['mapping']),claims=[])

    def commit(self,w,f,sentence):
        if not any(frame==f for _,frame in self.candidates(w)):raise ValueError('forged or stale transferred frame')
        index,n=self._next(w);u=self.units[index];m=u['mapping'];local=self.view(w,index)
        before=w.snapshot();native=self.sources[index][0].commit(local,_frame(u['frames'][n]),sentence)
        # Guards executed on a clone. Only a successful native commitment is mirrored.
        for sid,e in local.entities.items():
            target=deepcopy(e);target.id=m[sid];target.location=m.get(e.location,e.location)
            w.entities[target.id]=target
        w.flags={f for f in w.flags if not f.startswith(u['prefix'])}|{u['prefix']+f for f in local.flags}
        if n+1==len(u['frames']):
            w.flags.add(u['prefix']+'complete')
            if index==len(self.units)-1:w.flags.add('ended')
        w.focus=f.actor
        record=dict(id=len(w.history)+1,frame=asdict(f),sentence=sentence,before=before,after=w.snapshot(),
                    transfer=dict(unit=index,prefix=u['prefix'],source_scenario=u['scenario'],source_event=native['id'],
                                  source_kind=native['frame']['kind'],native_event=native))
        w.history.append(record);return record


def setup_joined(transfer):
    return JoinedPack(transfer['units']),decode_world(transfer['initial_world'])


def attach(documents, requests, world=None, *, seed=0, leak=True):
    """Sample compatible source branches, then freeze a replayable joined program.

    Requests are short event/query cues, not hand-written target event sequences.
    The entire observed prerequisite prefix is retained. Imports are explicit;
    existing objects keep their live state. Original inputs are never modified.
    """
    if not requests:raise ValueError('at least one transfer request required')
    for d in documents:validate(d)
    initial=decode_world((world or receiving_world()).to_dict())
    if initial.finished:raise ValueError('supply a live receiver snapshot without an ended flag')
    initial.scenario='joined'
    if initial.setting not in initial.entities:
        initial.setting=initial.setting or 'receiving_space'
        initial.entities[initial.setting]=Entity(initial.setting,'shared space','place',initial.setting,properties={'reachable'})
    rng=random.Random(seed);units=[];decisions=[]
    for request in requests:
        candidates=proposals(documents,request);feasible=[];rejected=[]
        for c in candidates:
            seen_bindings=set()
            for reuse in (True,False):
                trial=initial.clone();trial_units=deepcopy(units)
                try:
                    unit=_prepare(trial,deepcopy(c),len(units),request.get('bindings',{}),leak,reuse=reuse)
                    signature=tuple(sorted(unit['mapping'].items()))
                    if signature in seen_bindings:continue
                    seen_bindings.add(signature)
                    trial_units.append(unit);driver=JoinedPack(trial_units);simulation=trial.clone()
                    for _ in range(driver.event_limit):
                        options=driver.candidates(simulation)
                        if not options:break
                        driver.commit(simulation,options[0][1],'')
                    if not simulation.finished:raise ValueError('live native guards block the proposed source program')
                    imported=sum(x['kind'].startswith('import') for x in unit['leakage'])
                    source_target=driver.sources[-1][1].target
                    receiving_target=unit['mapping'].get(source_target)
                    reuse_bonus=4. if receiving_target in initial.entities else 1.
                    score=c['score']*reuse_bonus/(1.+.05*imported)
                    feasible.append(dict(unit=unit,world=trial,score=score,
                                         factors=dict(cue=c['score'],imports=imported,reuse_bonus=reuse_bonus)))
                except ValueError as error:
                    rejected.append(dict(scenario=c['scenario'],seed=c['seed'],reuse=reuse,reason=str(error)))
        if not feasible:raise ValueError('no feasible transfer: '+json.dumps(rejected[:8]))
        total=sum(c['score'] for c in feasible)
        probabilities=[c['score']/total for c in feasible]
        selected=rng.choices(range(len(feasible)),weights=probabilities)[0]
        chosen=feasible[selected];units.append(chosen['unit']);initial=chosen['world']
        decisions.append(dict(request=request,selected=selected,rejected=rejected,
            candidates=[dict(scenario=c['unit']['scenario'],seed=c['unit']['seed'],
                requested_event=c['unit']['requested_event'],events=len(c['unit']['frames']),
                probability=p,score=c['score'],factors=c['factors'],bindings=c['unit']['mapping'],
                references=c['unit']['references']) for c,p in zip(feasible,probabilities)]))
    transfer=dict(schema='joined-native-transfer-v1',initial_world=initial.to_dict(),units=units,
                  decisions=decisions,leak=leak)
    # Serialize the specification, including imported sets, for exact replay.
    return json.loads(json.dumps(transfer,default=lambda x:sorted(x) if isinstance(x,set) else x))


def run(documents,requests,world=None,*,seed=0,leak=True,**generation):
    transfer=attach(documents,requests,world,seed=seed,leak=leak)
    row=generate('joined',seed,transfer=transfer,continuations='expanded',**generation)
    replay(row)
    row['transfer_decisions']=transfer['decisions']
    row['transfer_summary']=dict(sources=[u['scenario'] for u in transfer['units']],
        imported_entities=sum(x['kind'].startswith('import') for u in transfer['units'] for x in u['leakage']),
        inherited_character_attributes=sum(x['kind']=='character_attributes' for u in transfer['units'] for x in u['leakage']),
        events=len(row['trace']))
    row['world_qa']=world_questions(row)
    return row


def world_questions(row,limit=8):
    """QA over executed target changes, not inherited English source claims.

    These are world-state questions. Silent effects can be evidence, so this is
    deliberately distinct from the reading-comprehension questions() API.
    """
    def phrase(eid):
        e=row['final_world']['entities'][eid]
        return e['noun'] if e['kind']=='person' else 'the '+e['noun']
    def words(states):return ' and '.join(x.replace('_',' ') for x in sorted(states))
    result=[];seen=set()
    for event in row['final_world']['history'][len(row['initial_world']['history']):]:
        before=event['before']['entities'];after=event['after']['entities'];actor=phrase(event['frame']['actor'])
        for eid,now in after.items():
            old=before[eid];name=phrase(eid);key=None
            if old['location']!=now['location']:
                destination=now['location'];source=old['location']
                if destination not in after or source not in before:continue
                prep='with' if row['final_world']['entities'][destination]['kind']=='person' else 'at'
                oldprep='with' if row['final_world']['entities'][source]['kind']=='person' else 'at'
                question=f'Where was {name} after {actor} acted?'
                answer=f'{name.capitalize()} was {prep} {phrase(destination)}. Previously, it was {oldprep} {phrase(source)}.'
                key=(eid,'location');kind='where'
            else:
                added=set(now['state'])-set(old['state']);removed=set(old['state'])-set(now['state'])
                if not added or row['final_world']['entities'][eid]['kind']=='person':continue
                question=f'How did the recorded state of {name} change?'
                answer=f'{name[:1].upper()+name[1:]} gained the state'+('s ' if len(added)>1 else ' ')+words(added)+'. '
                answer+=(('It lost the state'+('s ' if len(removed)>1 else ' ')+words(removed)+'.')
                         if removed else f'This followed {actor}’s action.')
                key=(eid,'state');kind='what'
            if key in seen:continue
            seen.add(key);result.append(dict(kind=kind,question=question,answer=answer,
                entity_ids=[eid,event['frame']['actor']],event_ids=[event['id']],scope='executed_target_world',
                evidence=dict(before=deepcopy(old),after=deepcopy(now))))
    # Prefer changed states as checks of compound mechanics, then object moves.
    result.sort(key=lambda q:q['kind']!='what')
    return result[:limit]


if __name__=='__main__':
    import argparse
    from pathlib import Path
    from .story_memory import load_documents
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--memory',type=Path,default=Path('grammarworlds/runs/seed_worlds_20261107_v4'))
    parser.add_argument('--request',action='append',help='JSON cue; repeat to join episodes: {"query":"wheel repair"}')
    parser.add_argument('--seed',type=int,default=7)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    requests=[json.loads(s) for s in (args.request or ['{"query":"wheel repair"}'])]
    row=run(load_documents(args.memory),requests,seed=args.seed)
    if args.out:args.out.write_text(json.dumps(row,indent=2)+'\n')
    print(row['story'])
    print(json.dumps(row['transfer_summary'],indent=2))
