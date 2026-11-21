"""Entity-local projections of grounded events, retaining their shared joins.

This is an annotation/export layer, not a replacement event planner. It records
observed writes and declared dependencies; Python guard read sets are incomplete.
Do not use a matching local projection as permission to commit an event.
"""
import argparse
from collections import defaultdict
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path

from ..world import Frame
from .runtime import SCENARIOS, generate, setup

CONTEXT_TAGS = {'mentioned', 'qa_context', 'causal_context'}


def factorize(row):
    """Replay a generated trace and project it onto all physical entity IDs.

    Replay captures full entity changes (including noun/type/property changes
    omitted by World.snapshot). No English parser guesses roles or intentions.
    """
    if hashlib.sha256(row['story'].encode()).hexdigest() != row['text_sha256']:
        raise ValueError('story text does not match trace')
    pack, world = setup(row['scenario'], row['seed'], **row.get('options', {}))
    if world.to_dict() != row['initial_world']:
        raise ValueError('initial world differs from source')
    scenes = {s['event_id']: s for s in row['scenes']}
    events, lines = [], defaultdict(list)
    flag_producers = {f: None for f in world.flags}
    field_producers = {}
    entities = deepcopy(row['initial_world']['entities'])
    for saved in row['final_world']['history'][len(row['initial_world']['history']):]:
        eid, data = saved['id'], saved['frame']
        frame = Frame(**{**data, 'cause_ids': tuple(data['cause_ids'])})
        available = [(k, f) for k, f in pack.candidates(world) if f == frame]
        if len(available) != 1 or world.snapshot() != saved['before']:
            raise ValueError('invalid or ambiguous source event')
        kernel = available[0][0]
        before = world.to_dict()['entities']
        decision=None
        if 'beats' in world.narrative:
            from ..beat_generation import select,commit as commit_beats
            labels=['beat.selection:'+saved['beat_decision']['selected']] if saved.get('beat_decision') else []
            decision=select(pack,world,frame,labels,row['tense'])
            if decision!=saved.get('beat_decision'):raise ValueError('beat decision differs from source')
        narrative_decision=None
        if getattr(pack,'decision_policy',False):
            narrative_decision=pack.select_narration(world,frame,saved['narrative_decision']['labels'])
            if narrative_decision!=saved['narrative_decision']:raise ValueError('narrative decision differs from source')
        record = pack.commit(world, frame, saved['sentence'])
        if narrative_decision is not None:pack.commit_narration(world,record,narrative_decision)
        if 'beats' in world.narrative:commit_beats(pack,world,record,decision)
        for key in ('referents', 'speakers', 'narrated'):
            record[key] = saved[key]
        if 'plot_execution' in world.narrative:
            from ..plot_execution import finalize_narration
            finalize_narration(world,record)
        after = world.to_dict()['entities']
        if world.snapshot() != saved['after']:
            raise ValueError('source effects changed')
        entities.update(after)
        tags, evidence = defaultdict(set), defaultdict(lambda: defaultdict(list))

        def tag(entity, name, source):
            if entity not in before and entity not in after:
                raise ValueError(f'unembedded entity in annotation: {entity}')
            tags[entity].add(name)
            evidence[entity][name].append(source)

        for role in ('actor', 'patient', 'instrument'):
            if data[role]: tag(data[role], 'frame.'+role, 'frame.'+role)
        if data['destination'] in entities:
            tag(data['destination'], 'frame.destination', 'frame.destination')
        for entity in saved.get('speakers', []): tag(entity, 'speaker', 'trace.speakers')
        for entity in saved.get('referents', []): tag(entity, 'mentioned', 'trace.referents')
        scene = scenes.get(eid)
        dialogue = []
        if scene:
            if (row['story'][scene['start']:scene['end']] != scene['text']
                    or scene['text'] != saved['sentence']):
                raise ValueError('scene text does not align with event')
            for label in scene['rules']:
                if label.startswith('clause.subject:'):
                    tag(label.split(':', 1)[1], 'grammatical_subject', label)
                if label.startswith('dialogue.listener:'):
                    _, speaker, listener = label.split(':', 2)
                    tag(speaker, 'speaker', label)
                    tag(listener, 'listener', label)
                    dialogue.append(dict(speaker=speaker, listener=listener))
            for claim in scene['claims']:
                for entity in claim['entities']: tag(entity, 'qa_context', 'claim:'+claim['key'])

        dependencies = []
        for flag in sorted(kernel.requires):
            dependencies.append(dict(kind='required_flag', key=flag, source_event=flag_producers.get(flag)))
        for cause in frame.cause_ids:
            parts = cause.split(':')
            entity, field = None, None
            if len(parts) >= 2 and parts[0] in {'loc', 'state'} and parts[1] in entities:
                entity, field = parts[1], 'location' if parts[0] == 'loc' else 'state'
            elif '.' in cause and cause.split('.', 1)[0] in entities:
                entity, field = cause.split('.', 1)[0], 'memes'
            if entity:
                tag(entity, 'causal_context', 'cause:'+cause)
                dependencies.append(dict(kind='declared_entity_cause', key=cause, entity=entity,
                    field=field, source_event=field_producers.get((entity, field))))
            elif cause.startswith('flag:'):
                dependencies.append(dict(kind='declared_flag_cause', key=cause,
                    source_event=flag_producers.get(cause[5:])))
            elif cause.startswith('event:'):
                dependencies.append(dict(kind='declared_event_cause', key=cause, source_event=int(cause[6:])))
            else:
                dependencies.append(dict(kind='world_fact', key=cause, source_event=None))

        effects, transfers = {}, []
        for entity in sorted(before.keys() | after.keys()):
            old, new = before.get(entity, {}), after.get(entity, {})
            delta = {key: dict(before=old.get(key), after=new.get(key))
                     for key in sorted(old.keys() | new.keys()) if old.get(key) != new.get(key)}
            if not delta: continue
            effects[entity] = delta
            tag(entity, 'changed', 'replayed_entity_diff')
            if 'location' in delta:
                tag(entity, 'moved', 'diff.location')
                source, destination = old.get('location'), new.get('location')
                move = dict(item=entity, source=source, destination=destination)
                for location, role, snapshot in ((source, 'source_holder', before),
                                                  (destination, 'destination_holder', after)):
                    if location in snapshot and snapshot[location]['kind'] == 'person':
                        tag(location, role, 'diff.location:'+entity)
                        move[role] = location
                transfers.append(move)
            if 'noun' in delta: tag(entity, 'renamed', 'diff.noun')
            for state in sorted(set(new.get('state', []))-set(old.get('state', []))):
                tag(entity, 'state.add:'+state, 'diff.state')
            for state in sorted(set(old.get('state', []))-set(new.get('state', []))):
                tag(entity, 'state.remove:'+state, 'diff.state')
            if 'memes' in delta:
                for concept in sorted(old.get('memes', {}).keys() | new.get('memes', {}).keys()):
                    if old.get('memes', {}).get(concept) != new.get('memes', {}).get(concept):
                        tag(entity, 'concept.changed:'+concept, 'diff.memes')
            for field in delta: field_producers[entity, field] = eid

        participants = sorted(e for e, ts in tags.items() if ts-CONTEXT_TAGS)
        added = sorted(set(saved['after']['flags'])-set(saved['before']['flags']))
        removed = sorted(set(saved['before']['flags'])-set(saved['after']['flags']))
        event = dict(id=eid, kind=frame.kind, frame=deepcopy(data), narrated=saved['narrated'],
            text=saved['sentence'], entity_tags={e: sorted(ts) for e, ts in sorted(tags.items())},
            tag_evidence={e: dict(v) for e,v in evidence.items()},
            participants=participants, dialogue=dialogue, movements=transfers, effects=effects,
            dependencies=dependencies, global_contract=dict(requires=sorted(kernel.requires),
                excludes=sorted(kernel.excludes), flags_added=added, flags_removed=removed),
            guard_reads_complete=False)
        events.append(event)
        for entity, ts in sorted(tags.items()):
            active = bool(ts-CONTEXT_TAGS)
            peers = [e for e in participants if e != entity] if active else []
            entry = dict(event_id=eid, kind=frame.kind, tags=sorted(ts), participation='participant' if active else 'context',
                own_effects=deepcopy(effects.get(entity, {})), peers=peers,
                shared_event=active and len(participants)>1,
                before=deepcopy(before.get(entity)), after=deepcopy(after.get(entity)))
            lines[entity].append(entry)
        for flag in added: flag_producers[flag] = eid
        for flag in removed: flag_producers.pop(flag, None)
    if world.to_dict() != row['final_world']:
        raise ValueError('final replay differs from source')
    return dict(schema='entity-event-lines-v1', scenario=row['scenario'], seed=row['seed'],
        story=row['story'], text_sha256=row['text_sha256'], events=events,
        entities={e: dict(initial=row['initial_world']['entities'].get(e), final=entities[e],
                          line=lines[e]) for e in sorted(entities)},
        limitations=['Declared dependencies are not a complete Python guard read set.',
                     'Frame actor/patient are coarse roles; compound scenes can involve additional people.',
                     'Holder tags describe physical possession, not legal ownership or intent.',
                     'Local lines project shared events; they are not independently executable.'])


def local_slice(graph, entity, start=0, stop=None):
    """A local line plus the explicit boundary needed by future replacement work.

    No approval of a swap is implied: actual guards and shared joins must be
    revalidated, and global flags remain coupled in the current engine.
    """
    line = [x for x in graph['entities'][entity]['line'] if x['participation']=='participant']
    selected = line[start:stop]
    ids = {x['event_id'] for x in selected}
    events = {x['id']:x for x in graph['events']}
    incoming, outgoing, joins = [], [], []
    for entry in selected:
        event = events[entry['event_id']]
        incoming += [dict(event_id=event['id'], **d) for d in event['dependencies'] if d['source_event'] not in ids]
        if entry['shared_event']:
            joins.append(dict(event_id=event['id'], peers=entry['peers'],
                peer_effects={p:deepcopy(event['effects'].get(p, {})) for p in entry['peers']},
                movements=deepcopy(event['movements']), dialogue=deepcopy(event['dialogue'])))
    for event in graph['events']:
        if event['id'] not in ids:
            outgoing += [dict(event_id=event['id'], **d) for d in event['dependencies'] if d['source_event'] in ids]
    return dict(entity=entity, events=deepcopy(selected),
        entry_state=deepcopy(selected[0]['before']) if selected else None,
        exit_state=deepcopy(selected[-1]['after']) if selected else None,
        joins=joins, incoming_dependencies=incoming, outgoing_dependencies=outgoing,
        global_effects=[dict(event_id=i, **events[i]['global_contract']) for i in sorted(ids)],
        requires_guard_revalidation=True, independently_executable=False)


def markdown(graph):
    lines = [f"# {graph['scenario']} — entity event lines (seed {graph['seed']})", '', graph['story'], '',
        'Event IDs join the same physical event across entity lines. Context-only mentions are listed separately. '
        'Frame roles are coarse; changed/moved/holder tags come from replayed state, not prose.', '']
    for entity, record in graph['entities'].items():
        active = [e for e in record['line'] if e['participation']=='participant']
        if not active: continue
        name = record['initial']['noun'] if record['initial'] else entity
        lines += [f'## {name} (`{entity}`)', '', '| Event | Tags | Own changes | Shared with |', '|---|---|---|---|']
        for e in active:
            effects = '; '.join(f"{k}: {v['before']} → {v['after']}" for k,v in e['own_effects'].items()) or '—'
            lines.append(f"| {e['event_id']}: {e['kind']} | {', '.join(t for t in e['tags'] if t not in CONTEXT_TAGS)} | {effects} | {', '.join(e['peers']) or '—'} |")
        context = [str(e['event_id'])+':'+e['kind'] for e in record['line'] if e['participation']=='context']
        lines += ['', 'Context-only events: '+(', '.join(context) or 'none')+'.', '']
    return '\n'.join(lines)


def run(out, scenarios=SCENARIOS, seed=3000, count=10):
    if count < 1: raise ValueError('count must be positive')
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    summary = {}
    with gzip.open(out/'entity_lines.jsonl.gz', 'wt') as sink:
        for scenario in scenarios:
            seen, total, shared, lines_count = set(), 0, 0, 0
            for s in range(seed,seed+count):
                row = generate(scenario, s, continuations='expanded', symbolic_heads=True)
                graph = factorize(row)
                sink.write(json.dumps(graph)+'\n')
                seen.update(e['kind'] for e in graph['events'])
                total += len(graph['events'])
                shared += sum(len(e['participants'])>1 for e in graph['events'])
                lines_count += sum(any(x['participation']=='participant' for x in v['line']) for v in graph['entities'].values())
                if s == seed:
                    (out/(scenario+'.md')).write_text(markdown(graph))
                    (out/(scenario+'.json')).write_text(json.dumps(graph,indent=2)+'\n')
                    (out/(scenario+'_hero_slice.json')).write_text(json.dumps(local_slice(graph, row['initial_world']['hero']),indent=2)+'\n')
            pack,_=setup(scenario,seed)
            summary[scenario]=dict(stories=count, events=total, shared_events=shared,
                participating_entity_lines=lines_count, observed_kinds=sorted(seen), unobserved_kinds=sorted(set(pack.KERNELS)-seen))
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--scenario',choices=(*SCENARIOS,'all'),default='all')
    p.add_argument('--seed',type=int,default=3000)
    p.add_argument('--count',type=int,default=10)
    a=p.parse_args()
    run(a.out, SCENARIOS if a.scenario=='all' else (a.scenario,), a.seed, a.count)
