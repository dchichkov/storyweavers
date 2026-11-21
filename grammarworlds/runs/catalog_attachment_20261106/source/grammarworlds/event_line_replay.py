"""Bind local event lines to a world and sample a legal partial-order replay.

Only explicit portable operations execute. Source annotations are evidence for
ports, never permission to apply arbitrary state diffs or source-world flags.
"""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import asdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import random

from .grammar import Derivation, Forest, expand
from .world import Entity, Fact, Frame, World, kernel
from .storytelling.continuations import ExpandedLanguage
from .storytelling.head_adapter import StoryHeads
from .storytelling.operations import Change, can_transfer, committed
from .storytelling.surface import scene, detokenize

FIELDS = {
    'intent': {'actor','item'}, 'offer': {'actor','listener'},
    'fetch': {'actor','item','source'}, 'transfer': {'actor','item','recipient'},
    'patch_paper': {'actor','item','tool'},
}
KINDS = {'actor':{'person'}, 'listener':{'person'}, 'recipient':{'person'},
         'source':{'place'}, 'tool':{'tool'}, 'item':{'object','tool','material','food','plant_part'}}


def paper_world():
    """Explicitly stronger fixture: paper material and paper-patching ability."""
    from .underdefined_probe import initial_world
    w = initial_world()
    w.entities['book'].properties.add('paper')
    for person in ('ada','omar'):
        w.entities[person].properties.add('can_patch_paper')
    return w


def world_from_dict(data, *, allow_history=False):
    data = deepcopy(data)
    if data.get('history') and not allow_history:
        raise ValueError('file input must describe an initial world, without history')
    data['entities'] = {i: Entity(**{**e, 'properties':set(e['properties']), 'state':set(e['state'])})
                        for i,e in data['entities'].items()}
    data['facts'] = {i:Fact(**{**f,'tags':tuple(f['tags'])}) for i,f in data['facts'].items()}
    data['flags'] = set(data['flags'])
    return World(**data)


def project_source(graph, focus, event_ids):
    """Two reviewed kite ports; unknown source semantics fail explicitly.

    The item/tool come from annotations, not a search/replace on source prose.
    Whole-story flags and guard reads are recorded as context, not transferred.
    """
    line = {x['event_id'] for x in graph['entities'][focus]['line'] if x['participation']=='participant'}
    if not event_ids or event_ids != sorted(set(event_ids)) or not set(event_ids) <= line:
        raise ValueError('select an ordered, nonempty segment of the entity line')
    events = {e['id']:e for e in graph['events']}
    result = dict(schema='attached-event-lines-v1', roles={}, events={}, lines=[], source={
        'scenario':graph['scenario'], 'seed':graph['seed'], 'entity':focus,
        'text_sha256':graph['text_sha256'], 'event_ids':event_ids,
        'port_policy':'reviewed portable operations replace source-specific guard/flag context'})
    bindings, context = {}, []
    def bind(role, source_id, kind):
        if role in bindings and bindings[role] != source_id:
            raise ValueError('inconsistent role across selected source events')
        bindings[role] = source_id; result['roles'][role] = kind
    for eid in event_ids:
        event = events[eid]; f=event['frame']; port=(graph['scenario'],event['kind'])
        bind('worker', f['actor'], 'person')
        if f['actor'] != focus: raise ValueError('this port requires the focal acting entity')
        if port == ('kite','fetch_tape'):
            if len(event['movements']) != 1: raise ValueError('unsupported fetch effects')
            move=event['movements'][0]; item=move['item']
            if event['effects'] != {item:{'location':dict(before=move['source'],after=f['actor'])}}:
                raise ValueError('source fetch contains additional effects')
            bind('tool',item,'tool');bind('supply',move['source'],'place')
            result['events']['fetch'] = dict(op='fetch',actor='worker',item='tool',source='supply')
        elif port == ('kite','mend'):
            item=f['patient'];delta=event['effects'].get(item,{}).get('state',{})
            if (set(event['effects'])!={item} or set(event['effects'][item])!={'state'}
                    or set(delta.get('after',[]))-set(delta.get('before',[]))!={'repaired'}
                    or set(delta.get('before',[]))-set(delta.get('after',[]))!={'torn'}):
                raise ValueError('source mend is not the reviewed torn-to-repaired transition')
            bind('item',item,'object');bind('tool',f['instrument'],'tool')
            result['events']['patch'] = dict(op='patch_paper',actor='worker',item='item',tool='tool')
        else:
            raise ValueError(f'no portable operation for {port[0]}:{port[1]}; source effects were not applied')
        context.append(dict(event_id=eid, source_contract=event['global_contract'],
                            source_dependencies=event['dependencies']))
    result['source']['role_origins']=bindings
    result['source']['untransferred_context']=context
    result['source']['target_requirements']=['paper material','paper-patching capability',
        'reachable supply for fetching','item and repair tool held by patching actor']
    result['lines']=[dict(entity='worker',steps=list(result['events']))]
    if 'patch' in result['events']: result['lines'].append(dict(entity='item',steps=['patch']))
    result['lines'].append(dict(entity='tool',steps=list(result['events'])))
    return result


def cooperative(template):
    """An explicitly supplied extension with shared handoff events, not inference."""
    result=deepcopy(template)
    if list(result['events']) != ['fetch','patch']:
        raise ValueError('cooperative example expects the fetch/patch segment')
    result['roles']['owner']='person'
    result['events'].update(
        wish=dict(op='intent',actor='owner',item='item'),
        offer=dict(op='offer',actor='worker',listener='owner'),
        hand_in=dict(op='transfer',actor='owner',item='item',recipient='worker'),
        hand_out=dict(op='transfer',actor='worker',item='item',recipient='owner'))
    result['lines']=[dict(entity='owner',steps=['wish','offer','hand_in','hand_out']),
                     dict(entity='worker',steps=['fetch','offer','hand_in','patch','hand_out']),
                     dict(entity='item',steps=['wish','hand_in','patch','hand_out']),
                     dict(entity='tool',steps=['fetch','patch'])]
    result['source']['supplied_extension']='goal, help offer, and two coordinated handoffs'
    return result


class AttachedLines:
    fields = FIELDS
    kinds = KINDS

    def __init__(self, world, template, bindings):
        self.world=world; self.template=deepcopy(template); self.bindings=dict(bindings)
        if template.get('schema')!='attached-event-lines-v1': raise ValueError('unknown line schema')
        if set(bindings)!=set(template['roles']): raise ValueError('every declared role needs exactly one binding')
        if len(set(bindings.values()))!=len(bindings): raise ValueError('distinct roles cannot alias one entity')
        for role,kind in template['roles'].items():
            if bindings[role] not in world.entities or world.entities[bindings[role]].kind!=kind:
                raise ValueError('role type mismatch or missing carrier: '+role)
        self.events={}; self.frames={}; self.users=defaultdict(list)
        for sid,raw in template['events'].items():
            op=raw.get('op')
            if op not in self.fields or set(raw)!={'op'}|self.fields[op]: raise ValueError('unsupported operation/signature: '+str(op))
            if not all(raw[k] in bindings for k in self.fields[op]): raise ValueError('unbound role in event')
            e={k:bindings[v] for k,v in raw.items() if k!='op'};e['op']=op
            if any(world.entities[e[k]].kind not in self.kinds[k] for k in self.fields[op]):
                raise ValueError('operation role type mismatch: '+sid)
            self.events[sid]=e
            self.frames[sid]=Frame(sid,e['actor'],e.get('item',e.get('listener','')),
                                  e.get('tool',''),e.get('destination',e.get('recipient',e['actor'] if op=='fetch' else '')))
        self.lines=deepcopy(template['lines']);self.cursors=[0]*len(self.lines)
        if not self.lines or not self.events: raise ValueError('nonempty lines and events required')
        if len({line['entity'] for line in self.lines})!=len(self.lines): raise ValueError('one line per attached role')
        edges=defaultdict(set)
        for i,line in enumerate(self.lines):
            role=line['entity'];steps=line['steps']
            if role not in bindings or not steps or len(set(steps))!=len(steps): raise ValueError('invalid local line')
            for sid in steps:
                if sid not in self.events or bindings[role] not in {self.events[sid][k] for k in self.fields[self.events[sid]['op']]}:
                    raise ValueError('line refers to an unrelated or unknown event')
                self.users[sid].append(i)
            for left,right in zip(steps,steps[1:]): edges[left].add(right)
        if set(self.users)!=set(self.events): raise ValueError('unused event in attachment')
        for sid,e in self.events.items():
            involved={e[k] for k in self.fields[e['op']]}
            for i,line in enumerate(self.lines):
                if bindings[line['entity']] in involved and i not in self.users[sid]:
                    raise ValueError('shared event missing from an attached participant line: '+sid)
        remaining=set(self.events)
        while remaining:
            roots={s for s in remaining if not any(s in edges[p] for p in remaining)}
            if not roots: raise ValueError('incompatible local ordering: shared-event cycle')
            remaining-=roots
        changes={}
        for sid,e in self.events.items():
            changes[sid] = self.effects(e)
        def extra(world, frame): pass
        self._commit=committed(self.candidates,changes)(extra)

    def effects(self, e):
        if e['op']=='fetch': return (Change('@patient','@actor'),)
        if e['op']=='transfer': return (Change('@patient','@destination'),)
        if e['op']=='patch_paper': return (Change('@patient',add=('repaired',),remove=('torn',)),)
        return ()

    def frontier(self):
        result=[]
        for sid,users in self.users.items():
            if all(self.cursors[i]<len(self.lines[i]['steps']) and self.lines[i]['steps'][self.cursors[i]]==sid for i in users):
                result.append(sid)
        return sorted(result)

    def reasons(self, sid, w=None):
        w=w or self.world;e=self.events[sid];entities=w.entities
        if w.finished: return ['world is marked ended']
        roles={k:v for k,v in e.items() if k!='op'}
        missing=[v for v in roles.values() if v not in entities]
        if missing: return ['missing carrier: '+','.join(sorted(set(missing)))]
        actor=entities[e['actor']];op=e['op'];bad=[]
        def need(ok,reason):
            if not ok: bad.append(reason)
        for role in self.fields[op]: need(entities[e[role]].kind in self.kinds[role], 'operation role type changed: '+role)
        need(actor.kind=='person','actor must be a person')
        if op=='intent': need('torn' in entities[e['item']].state,'repair goal has no torn item')
        elif op=='offer':
            listener=entities[e['listener']]
            need(listener.kind=='person' and actor.id!=listener.id,'offer needs another person')
            need(listener.location==actor.location,'listener is not co-located')
            need('can_help' in actor.properties,'actor cannot offer help')
        elif op=='fetch':
            item,source=entities[e['item']],entities[e['source']]
            need('can_hold' in actor.properties,'actor cannot carry objects')
            need('portable' in item.properties,'item is not portable')
            need(source.kind=='place' and 'reachable' in source.properties,'supply is not a reachable place')
            need(item.location==source.id,'item is not at the bound supply')
            need(source.location==actor.location,'supply is not co-located')
        elif op=='transfer':
            need(actor.id!=e['recipient'],'self-transfer is not supported')
            need(can_transfer(w,e['item'],e['actor'],e['recipient']),'transfer needs a held item and co-located people')
            need('portable' in entities[e['item']].properties,'item is not portable')
            need(all('can_hold' in entities[p].properties for p in (e['actor'],e['recipient'])),'both people must be able to carry')
        elif op=='patch_paper':
            item,tool=entities[e['item']],entities[e['tool']]
            need('can_patch_paper' in actor.properties,'actor lacks paper-patching capability')
            need('paper' in item.properties,'item lacks declared paper material')
            need('torn' in item.state,'item is not torn')
            need(tool.kind=='tool' and 'repair' in tool.properties,'instrument lacks repair affordance')
            need(tool.location==actor.id,'actor is not holding the repair tool')
            need(item.location==actor.id,'actor is not holding the item')
        return bad

    def candidates(self, w):
        return [(kernel(sid),self.frames[sid]) for sid in self.frontier() if not self.reasons(sid,w)]

    def commit(self, frame, prose):
        record=self._commit(self.world,frame,prose)
        sid=frame.kind
        record['line_event']=sid;record['operation']=self.events[sid]['op']
        record['attached_entities']=[self.bindings[self.lines[i]['entity']] for i in self.users[sid]]
        for i in self.users[sid]: self.cursors[i]+=1
        return record

    def render(self, sid):
        e=self.events[sid];g=ExpandedLanguage(self.world);op=e['op']
        if op=='intent': return scene(g.say_intent(e['actor'],'want',g.v('repair',g.ref(e['item']))))
        if op=='offer':
            from .portable.nouns import pronoun
            return scene(g.offer(e['actor'],g.v('help',pronoun('you')),listener=e['listener']))
        if op=='fetch': return g.fetch_scene(e['actor'],e['item'],self.world.entities[e['source']].noun)
        if op=='transfer': return scene(g.transfer(e['actor'],g.ref(e['recipient']),g.ref(e['item'])))
        if op=='patch_paper': return scene(g.using(e['actor'],g.v('repair',g.ref(e['item'])),g.ref(e['tool'])))
        raise ValueError(op)

    @property
    def complete(self): return all(c==len(line['steps']) for c,line in zip(self.cursors,self.lines))


def replay(world, template, bindings, seed=0, *, heads=True, max_events=32, driver_class=AttachedLines):
    """Replay on a clone; rejected steps never mutate it or advance cursors."""
    w=world.clone();driver=driver_class(w,template,bindings);initial=w.to_dict()
    rng=random.Random(seed);head=StoryHeads(w) if heads else None
    traces=[];texts=[];counts=Counter()
    while not driver.complete and len(traces)<max_events:
        available=driver.candidates(w)
        if not available: break
        before=w.to_dict();derivations=[]
        for _,f in available:
            for tokens,p,labels in expand(driver.render(f.kind).node):
                derivations.append(Derivation(tokens,p/len(available),f,labels))
        assert before==w.to_dict()
        forest=Forest(derivations,{})
        tokens=();trace=[]
        for _ in range(max(len(d.tokens) for d in derivations)+1):
            prediction=head.predict(forest,tokens,w,tense='past',available=available) if head else forest.predict(tokens)
            choices=prediction['choices'];assert math.isclose(sum(c['probability'] for c in choices),1)
            chosen=rng.choices(choices,weights=[c['probability'] for c in choices])[0]
            prediction.update(selected=chosen['word'],selected_probability=chosen['probability']);trace.append(prediction)
            counts['token_steps']+=1;counts['choice_steps']+=len(choices)>1
            counts['head_changed_steps']+=prediction.get('head_total_variation',0)>1e-10
            if chosen['word']=='<END>': break
            tokens+=(chosen['word'],)
        else: raise AssertionError('unfinished grammar sample')
        posterior=forest.event_posterior(tokens);frame=rng.choices(list(posterior),weights=list(posterior.values()))[0]
        prose=detokenize(tokens);event=driver.commit(frame,prose)
        labels=set.intersection(*(set(d.rules) for d in derivations if d.frame==frame and d.tokens==tokens))
        event.update(referents=sorted(x.split(':',1)[1] for x in labels if x.startswith('referent:')),
                     speakers=sorted(x.split(':',1)[1] for x in labels if x.startswith('dialogue.speaker:')),narrated=True)
        texts.append(prose);traces.append(dict(line_event=frame.kind,operation=driver.events[frame.kind]['op'],
            ready_events=[f.kind for _,f in available],word_trace=trace))
    return dict(seed=seed,heads=heads,status='complete' if driver.complete else ('limit' if len(traces)==max_events else 'blocked'),
        story=' '.join(texts),initial_world=initial,final_world=w.to_dict(),trace=traces,metrics=dict(counts),
        cursors=driver.cursors,blocked={sid:driver.reasons(sid) for sid in driver.frontier()},
        source=deepcopy(template.get('source',{})),bindings=dict(bindings))


def verify(row, template, *, driver_class=AttachedLines):
    w=world_from_dict(row['initial_world'],allow_history=True);driver=driver_class(w,template,row['bindings'])
    prefix_length=len(w.history)
    assert row['final_world']['history'][:prefix_length]==w.history
    for event in row['final_world']['history'][prefix_length:]:
        frame=Frame(**{**event['frame'],'cause_ids':tuple(event['frame']['cause_ids'])})
        record=driver.commit(frame,event['sentence'])
        for key in ('referents','speakers','narrated'): record[key]=event[key]
    assert w.to_dict()==row['final_world']
    assert driver.cursors==row['cursors']
    assert driver.complete==(row['status']=='complete')


def run_file(path, out, count=20, steps=32):
    if count<1 or steps<1: raise ValueError('positive run count and event limit required')
    payload=json.loads(Path(path).read_text());w=world_from_dict(payload['world'])
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    rows=[replay(w,payload['template'],payload['bindings'],seed,heads=heads,max_events=steps)
          for seed in range(count) for heads in (False,True)]
    for row in rows: verify(row,payload['template'])
    (out/'input.json').write_text(json.dumps(payload,indent=2)+'\n')
    with gzip.open(out/'traces.jsonl.gz','wt') as f:
        for row in rows:f.write(json.dumps(row)+'\n')
    summary={}
    target=payload['bindings'].get('item')
    for heads in (False,True):
        subset=[r for r in rows if r['heads']==heads];counts=Counter()
        for r in subset:counts.update(r['metrics'])
        summary['on' if heads else 'off']=dict(counts,runs=count,completed=sum(r['status']=='complete' for r in subset),
            repaired=sum('repaired' in r['final_world']['entities'][target]['state'] for r in subset) if target else None,
            item_locations=dict(Counter(r['final_world']['entities'][target]['location'] for r in subset)) if target else {},
            distinct_texts=len({r['story'] for r in subset}),distinct_event_orders=len({tuple(t['line_event'] for t in r['trace']) for r in subset}))
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Bound local-line replay','', 'Seeds 0–2 selected before generation. No text repair or filtering.','']
    for row in rows:
        if row['seed']<3:
            lines += [f"## Seed {row['seed']}, heads {row['heads']}, {row['status']}",'',row['story'] or '(no text)','']
            if row['blocked']:lines += ['Blocked: '+json.dumps(row['blocked']),'']
    (out/'samples.md').write_text('\n'.join(lines))
    print(json.dumps(summary,indent=2))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--line',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--count',type=int,default=20);p.add_argument('--steps',type=int,default=32)
    a=p.parse_args();run_file(a.line,a.out,a.count,a.steps)
