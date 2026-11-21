"""Bounded catalog retrieval ahead of local-line replay; no runtime language model.

Catalog evidence is copied from three worlds. Reviewed exports describe portable
capabilities/dependencies; they do not claim to infer arbitrary physics from text.
"""
import argparse
from collections import Counter
from copy import deepcopy
from difflib import SequenceMatcher
import gzip
import json
from pathlib import Path

from .world import Entity, World
from .attribute_transfer import entity_profile
from .event_line_replay import AttachedLines, replay, verify, FIELDS, KINDS
from .storytelling.operations import Change
from .storytelling.continuations import ExpandedLanguage
from .storytelling.surface import scene
from .storytelling import kite_world, library_world, music_world

# Each slot has a kind and hard affordance requirements. Dependencies are tied
# to the actor/item prototype, not a table of experiment-specific role bindings.
SPECS = {
    'premise': {'actor': ('person', ()), 'item': ('object', ('physics:kite',))},
    'wish_flight': {'actor': ('person', ('can_hold',)), 'item': ('object', ('physics:kite',))},
    'offer': {'actor': ('person', ('can_help',)), 'listener': ('person', ())},
    'mend_kite': {'actor': ('person', ('can_repair',)), 'item': ('object', ('physics:kite',)), 'tool': ('tool', ('repair',))},
    'sketch_moon': {'actor': ('person', ('can_sketch_moon',)), 'item': ('object', ('drawable',)),
                    'tool': ('tool', ('draw',)), 'reference': ('object', ('moon_reference',))},
    'fly_kite': {'actor': ('person', ('can_hold',)), 'item': ('object', ('physics:kite',)),
                 'tool': ('object', ('tie',)), 'destination': ('place', ('airspace',))},
    'celebrate': {'actor': ('person', ('can_drum',)), 'item': ('object', ('physics:kite',)),
                  'tool': ('instrument', ('physics:drum',))},
}
# Portable dependencies established by reviewing the donor guards and effects.
DEPENDENCIES = {
    ('mend_kite', 'tool'): ('item', 'repair_tool'),
    ('sketch_moon', 'item'): ('actor', 'paper'),
    ('sketch_moon', 'tool'): ('actor', 'pencil'),
    ('sketch_moon', 'reference'): ('actor', 'atlas'),
    ('fly_kite', 'tool'): ('item', 'tether'),
    ('celebrate', 'tool'): ('actor', 'instrument'),
}


def catalog():
    """Versioned export profiles; source setup seed 1 avoids the fragile kite."""
    worlds = {name: pack.make_world(1) for name, pack in
              [('kite', kite_world), ('library', library_world), ('music', music_world)]}
    records = {}
    for name, w in worlds.items():
        for eid, ent in w.entities.items():
            key = name + ':' + eid
            records[key] = dict(entity=deepcopy(ent), source=dict(world=name, entity=eid, seed=1),
                                additions=[], links={}, packages=[])
    def export(key, properties=(), links=None, packages=()):
        r = records[key]; r['entity'].properties.update(properties)
        r['additions'] = list(properties); r['links'] = links or {}; r['packages'] = list(packages)
    export('kite:hero', ('can_help',))
    export('kite:target', ('physics:kite',), {'repair_tool':'kite:tool', 'tether':'kite:string'},
           ('kite:mend', 'kite:test_flight'))
    export('library:hero', ('can_sketch_moon',),
           {'paper':'library:paper', 'pencil':'library:pencil', 'atlas':'library:atlas'}, ('library:sketch_moon',))
    export('library:paper', ('drawable','portable'))
    export('library:atlas', ('moon_reference',))
    export('music:hero', ('can_drum',), {'instrument':'music:drum'}, ('music:perform',))
    export('music:drum', ('physics:drum',))
    return records


def bare_world():
    return World('catalog_attachment', {}, '', '', '', '', 'meadow', {})


def example_line():
    return dict(schema='catalog-line-v1',
        context={'setting':'meadow', 'properties':['windy']},
        mentions={'visitor':{'name':'Mino'}, 'repairer':{'name':'Sammy'},
                  'musician':{'name':'Niah'}, 'kite':{'noun':'kite'}},
        events=[
            dict(id='premise', op='premise', actor='visitor', item='kite'),
            dict(id='wish', op='wish_flight', actor='visitor', item='kite'),
            dict(id='offer', op='offer', actor='repairer', listener='visitor'),
            dict(id='repair', op='mend_kite', actor='repairer', item='kite'),
            dict(id='picture', op='sketch_moon', actor='visitor'),
            dict(id='flight', op='fly_kite', actor='visitor', item='kite'),
            dict(id='music', op='celebrate', actor='musician', item='kite')])


class Unresolved(ValueError):
    pass


def attach(line, world=None, *, records=None, dependencies=True, threshold=.55):
    """Resolve a structured line transactionally; return provenance and bindings.

    Names rank compatible prototypes; they are neither identity proofs nor
    arbitrary capability grants. Unknown/ambiguous matches fail closed. Existing
    entities are reused only when compatible; imported defaults never overwrite
    existing carriers. No objects are added to the caller's world.
    """
    if line.get('schema') != 'catalog-line-v1': raise ValueError('unknown catalog line schema')
    w = (world if world is not None else bare_world()).clone()
    records = deepcopy(records if records is not None else catalog())
    context = line['context']; setting = context['setting']; audit = []; bindings = {}; origins = {}
    if setting not in w.entities:
        w.entities[setting] = Entity(setting, setting, 'place', '', properties=set(context.get('properties', [])))
        audit.append(dict(action='construct', entity=setting, evidence='explicit line context'))
    elif not set(context.get('properties', [])) <= w.entities[setting].properties:
        raise Unresolved('existing setting contradicts required context')
    w.setting = setting
    events = deepcopy(line['events']); requirements = {}; hints = deepcopy(line.get('mentions', {})); inferred = {}
    if not events or len({e['id'] for e in events}) != len(events): raise ValueError('nonempty, unique event IDs required')
    for event in events:
        op = event['op']
        if op not in SPECS: raise Unresolved('no reviewed physics for '+op)
        if set(event)-{'id','op'}-set(SPECS[op]): raise ValueError('unknown event slots')
        for slot, (kind, props) in SPECS[op].items():
            if slot not in event:
                if not dependencies: raise Unresolved('missing dependency '+event['id']+'.'+slot)
                if slot == 'destination' and op == 'fly_kite':
                    role = '_airspace'; hints[role] = {'construct':'airspace'}
                else:
                    rule = DEPENDENCIES.get((op,slot))
                    if not rule or rule[0] not in event: raise Unresolved('cannot infer '+event['id']+'.'+slot)
                    parent, relation = event[rule[0]], rule[1]
                    role = '_'+parent+'_'+relation; inferred[role] = (parent, relation)
                event[slot] = role
            role = event[slot]
            if role in requirements and requirements[role][0] != kind: raise Unresolved('conflicting role kinds')
            requirements.setdefault(role, (kind,set()))[1].update(props)
    def compatible(e, role):
        kind, props = requirements[role]
        return e.kind == kind and props <= e.properties
    def score(e, hint):
        query = hint.get('name', hint.get('noun', ''))
        return SequenceMatcher(None, query.lower(), e.noun.lower()).ratio() if query else 0
    active = set()
    def resolve(role):
        if role in bindings: return bindings[role]
        if role in active: raise Unresolved('cyclic catalog dependency')
        active.add(role); hint = hints.get(role, {}); wanted = None
        if role in inferred:
            parent, relation = inferred[role]; resolve(parent)
            key = origins.get(parent)
            wanted = records[key]['links'].get(relation) if key else None
            if not wanted: raise Unresolved('no catalog dependency '+parent+'.'+relation)
        if hint.get('construct') == 'airspace':
            eid = setting+'_sky'
            if eid in w.entities and not compatible(w.entities[eid],role): raise Unresolved('incompatible airspace')
            if eid not in w.entities:
                w.entities[eid] = Entity(eid,'sky','place',setting,properties={'airspace'})
                audit.append(dict(action='construct',entity=eid,evidence='fly_kite destination requirement'))
            bindings[role]=eid; active.remove(role); return eid
        # Explicit local binding is useful for underdefined worlds and ablations.
        local = hint.get('entity')
        if local:
            if local not in w.entities or not compatible(w.entities[local],role): raise Unresolved('incompatible local entity '+local)
            if local in bindings.values(): raise Unresolved('distinct roles cannot alias')
            bindings[role]=local
            # A local entity is not assumed to share a prototype just by its name.
            audit.append(dict(action='reuse',role=role,entity=local,evidence='explicit local binding'))
            active.remove(role); return local
        candidates = [(score(e,hint),eid) for eid,e in w.entities.items()
                      if compatible(e,role) and eid not in bindings.values() and score(e,hint)>=threshold]
        if candidates and not wanted:
            candidates.sort(reverse=True)
            if len(candidates)>1 and candidates[0][0]-candidates[1][0]<.08: raise Unresolved('ambiguous local match '+role)
            _,eid=candidates[0]; bindings[role]=eid
            audit.append(dict(action='reuse',role=role,entity=eid,evidence='compatible local name match'))
            active.remove(role); return eid
        ranked = sorted([(1. if wanted==key else score(r['entity'],hint),key) for key,r in records.items()
                         if compatible(r['entity'],role) and (not wanted or wanted==key)
                         and key not in origins.values()], reverse=True)
        if not ranked or ranked[0][0]<threshold: raise Unresolved('no compatible prototype for '+role)
        if len(ranked)>1 and ranked[0][0]-ranked[1][0]<.08: raise Unresolved('ambiguous prototype for '+role)
        confidence,key=ranked[0]; record=records[key]; e=deepcopy(record['entity']); source_location=e.location
        eid='import_'+key.replace(':','_')
        if eid in w.entities: raise Unresolved('catalog instance ID collision: '+eid)
        e.id=eid
        # Target line names are local names; source identity remains provenance.
        if e.kind=='person': e.noun=hint.get('name',e.noun);e.state=set()
        # Borrowing is a source-scene relation, not an intrinsic instrument trait.
        dropped_properties=e.properties & {'borrowed','belongs_to_friend'}
        e.properties.difference_update(dropped_properties)
        e.location=setting
        if role in inferred:
            parent,_=inferred[role]
            if w.entities[bindings[parent]].kind=='person': e.location=bindings[parent]
        w.entities[eid]=e; bindings[role]=eid; origins[role]=key
        audit.append(dict(action='import',role=role,entity=eid,prototype=key,match_score=round(confidence,4),
            alternatives=[dict(prototype=k,score=round(s,4)) for s,k in ranked[:3]],
            source=record['source'],export_additions=record['additions'],physics=record['packages'],
            dependency=list(inferred[role]) if role in inferred else None,
            relocation=dict(source=source_location,target=e.location),
            discarded_person_states=sorted(record['entity'].state) if e.kind=='person' else [],
            discarded_relational_properties=sorted(dropped_properties)))
        active.remove(role); return eid
    for role in requirements: resolve(role)
    # Equipment required by an operation starts within reach. This is assembly,
    # not a silently executed fetch: its placement is logged above and here.
    for event in events:
        if event['op']=='fly_kite':
            role=event['tool'];eid=bindings[role]
            if role in origins:
                w.entities[eid].location=bindings[event['actor']]
                audit.append(dict(action='place',entity=eid,holder=bindings[event['actor']],evidence='exported tether placement'))
    template=dict(schema='attached-event-lines-v1', roles={r:k for r,(k,_) in requirements.items()},
        events={e['id']:{k:v for k,v in e.items() if k!='id'} for e in events}, lines=[],
        source={'kind':'catalog-composition','input':deepcopy(line),'retrieval':audit})
    template['source']['attribute_sources'] = {role:dict(origin=deepcopy(records[key]['source']),
        entity=entity_profile(records[key]['entity'])) for role,key in origins.items()}
    for role in requirements:
        template['lines'].append(dict(entity=role,steps=[e['id'] for e in events if role in [v for k,v in e.items() if k not in {'id','op'}]]))
    people=[bindings[r] for r,(k,_) in requirements.items() if k=='person']
    w.hero=people[0];w.helper=people[1] if len(people)>1 else '';w.target=bindings.get('kite','');w.tool=''
    CatalogLines(w,template,bindings)  # structural validation before returning
    return w,template,bindings,audit


class CatalogLines(AttachedLines):
    fields={**FIELDS, **{op:set(slots) for op,slots in SPECS.items()}}
    kinds={**KINDS, 'item':KINDS['item']|{'instrument'}, 'tool':{'tool','object','instrument'},
           'reference':{'object'}, 'destination':{'place'}}

    def effects(self,e):
        op=e['op']
        if op=='mend_kite': return (Change(e['item'],add=('repaired',),remove=('torn',)),)
        if op=='sketch_moon': return (Change(e['item'],add=('moon_drawing',),remove=('blank',)),)
        if op=='fly_kite': return (Change(e['item'],e['destination'],add=('flying',),remove=('grounded',)),)
        if op=='celebrate': return (Change(e['actor'],add=('performed_solo',)),Change(e['tool'],add=('sounded',)))
        return super().effects(e)

    def reasons(self,sid,w=None):
        w=w or self.world;e=self.events[sid];op=e['op']
        if op not in SPECS or op=='offer': return super().reasons(sid,w)
        if w.finished: return ['world is marked ended']
        if any(e[s] not in w.entities for s in SPECS[op]): return ['missing carrier']
        bad=[]
        def need(ok,why):
            if not ok: bad.append(why)
        for slot,(kind,props) in SPECS[op].items():
            ent=w.entities[e[slot]];need(ent.kind==kind and set(props)<=ent.properties,'missing affordance: '+slot)
        actor=w.entities[e['actor']]; item=w.entities[e['item']]
        need(actor.location==w.setting,'actor is not at scene')
        def accessible(ent): return ent.location in {actor.id,w.setting}
        if op in {'premise','wish_flight','mend_kite','fly_kite'}: need(accessible(item),'kite is not accessible')
        if op in {'premise','wish_flight','mend_kite'}: need('torn' in item.state,'kite is not torn')
        if op=='mend_kite': need(accessible(w.entities[e['tool']]),'repair tool is not accessible')
        if op=='sketch_moon':
            need(all(w.entities[e[s]].location==actor.id for s in ('item','tool','reference')),'drawing materials are not held')
            need('blank' in item.state,'paper is not blank')
            need('moon_picture' in w.entities[e['reference']].state,'reference has no moon picture')
        if op=='fly_kite':
            need('repaired' in item.state and not {'torn','fragile'} & item.state,'kite is not flight-ready')
            need('flyable' in item.properties,'kite cannot fly')
            need(w.entities[e['tool']].location==actor.id,'tether is not held')
            need(w.setting in w.entities and 'windy' in w.entities[w.setting].properties,'wind is absent')
            need(w.entities[e['destination']].location==w.setting,'airspace is elsewhere')
        if op=='celebrate':
            need('flying' in item.state,'kite is not flying')
            need(item.location in w.entities and w.entities[item.location].location==actor.location,'kite is out of sight')
            need(w.entities[e['tool']].location==actor.id,'drum is not held')
        return bad

    def commit(self,frame,prose):
        record=super().commit(frame,prose)
        record['bound_roles']={k:v for k,v in self.events[frame.kind].items() if k!='op'}
        return record

    def render(self,sid):
        e=self.events[sid];op=e['op']
        if op not in SPECS or op=='offer': return super().render(sid)
        lex=deepcopy(kite_world.LEXICON)
        for pack in (library_world,music_world):
            for category,entries in pack.LEXICON.items(): lex.setdefault(category,{}).update(entries)
        lex['nouns'].update({'sky':{},'meadow':{}})
        lex['verbs']['beat']={'forms':['beat','beat','beaten'],'valencies':['V2']}
        g=ExpandedLanguage(self.world,lexicon=lex);a=e['actor'];item=e['item']
        if op=='premise': return scene(g.s(a,g.adv(g.v('find',g.ref(item,adjectives=('torn',))),g.pp('in',g.n(self.world.setting)))))
        if op=='wish_flight': return scene(g.say_intent(a,'want',g.v('fly',g.ref(item))))
        if op=='mend_kite': return scene(g.using(a,g.v('repair',g.ref(item)),g.ref(e['tool'])))
        if op=='sketch_moon':
            return scene(g.s(a,g.v('hold',g.ref(e['reference']))),
                g.using(a,g.adv(g.v('sketch',g.n('moon')),g.pp('on',g.ref(item))),g.ref(e['tool'])))
        if op=='fly_kite': return scene(g.s(a,g.adv(g.v('fly',g.ref(item)),g.pp('with',g.ref(e['tool'])))))
        if op=='celebrate':
            return scene(g.join(g.s(a,g.v('beat',g.ref(e['tool']))),g.s(item,g.adv(g.v('fly'),g.pp('in',g.n('sky')))),'and'))
        raise ValueError(op)


def run(out,count=20,*,line=None):
    if count<1: raise ValueError('positive sample count required')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    line=deepcopy(line if line is not None else example_line());w,t,b,audit=attach(line)
    (out/'input_line.json').write_text(json.dumps(line,indent=2)+'\n')
    (out/'resolved.json').write_text(json.dumps(dict(world=w.to_dict(),template=t,bindings=b,audit=audit),indent=2)+'\n')
    rows=[replay(w,t,b,seed,heads=heads,driver_class=CatalogLines) for seed in range(count) for heads in (False,True)]
    for row in rows: verify(row,t,driver_class=CatalogLines)
    with gzip.open(out/'traces.jsonl.gz','wt') as f:
        for row in rows: f.write(json.dumps(row)+'\n')
    summary={}
    for heads in (False,True):
        subset=[r for r in rows if r['heads']==heads];metrics=Counter()
        for r in subset: metrics.update(r['metrics'])
        summary[str(heads)]=dict(runs=len(subset),complete=sum(r['status']=='complete' for r in subset),
            distinct_texts=len({r['story'] for r in subset}),**metrics)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'samples.md').write_text('# Three-source catalog attachment\n\nSeeds 0–4, heads on; no filtering or text repair.\n\n'+
        '\n\n'.join(f"## Seed {r['seed']}\n\n{r['story']}" for r in rows if r['heads'] and r['seed']<5)+'\n')
    print(json.dumps(summary,indent=2))
    print(rows[1]['story'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--count',type=int,default=20)
    p.add_argument('--line',type=Path,help='structured catalog-line-v1 JSON; defaults to the three-story experiment')
    args=p.parse_args();run(args.out,args.count,line=json.loads(args.line.read_text()) if args.line else None)
