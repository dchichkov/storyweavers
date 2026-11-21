"""Reusable annotations on intact story token streams; no detached prose chunks.

Historical observations stay separate from prefix-time candidate attributes.
Retrieval returns references into a document, then uses reviewed target mappings.
"""
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
import math
import random
import gzip
from pathlib import Path

from .event_mapping import load_bank, _match, mapping_distribution, _positive
from .storytelling.event_lines import factorize
from .storytelling.surface import detokenize


def memory_files(path):
    """Prefer the full branch archive; per-world previews need not cover a world."""
    path = Path(path)
    if path.is_file(): return [path]
    archive = path / 'stories.memory.jsonl.gz'
    paths = [archive] if archive.is_file() else sorted(path.glob('*.memory.json'))
    if not paths: raise ValueError('no annotated story documents found')
    return paths


def load_documents(path):
    documents = []
    for file in memory_files(path):
        if file.name.endswith('.jsonl.gz'):
            with gzip.open(file, 'rt') as stream:
                documents.extend(json.loads(line) for line in stream if line.strip())
        else:
            documents.append(json.loads(file.read_text()))
    if not documents: raise ValueError('empty story memory')
    for doc in documents: validate(doc)
    return documents


def annotate(row, *, bank=None):
    """Preserve all sampled units and prose, adding source-memory attributes."""
    if 'attribute_generation' not in row:
        raise ValueError('joint token attributes required')
    graph = factorize(row)  # Validates text alignment and complete physical replay.
    bank = load_bank() if bank is None else bank
    namespace = hashlib.sha256(json.dumps(dict(scenario=row['scenario'], seed=row['seed'],
        text=row['text_sha256'], options=row.get('options', {})), sort_keys=True).encode()).hexdigest()
    doc = dict(schema='annotated-story-memory-v1', id=namespace, scenario=row['scenario'], seed=row['seed'],
        text=row['story'], text_sha256=row['text_sha256'], tokens=[], attributes={},
        entities=deepcopy(graph['entities']), events=[],
        observation_scope='completed_source_story_only', source_options=deepcopy(row.get('options', {})))
    if 'source_story' in row:
        doc['source_story'] = deepcopy(row['source_story'])
    for token in row['attribute_generation']['tokens']:
        index = len(doc['tokens'])
        if token['position']['token'] != index:
            raise ValueError('non-contiguous token positions')
        trace = row['trace'][token['scene_index']]
        candidates = []
        for choice in token['candidates']:
            aid = f"{token['scene_index']}:{choice['attributes']}"
            doc['attributes'][aid] = deepcopy(trace['attribute_table'][choice['attributes']])
            candidates.append(dict(probability=choice['probability'], attributes=aid))
        doc['tokens'].append(dict(id=index, **{k: deepcopy(v) for k,v in token.items() if k != 'candidates'},
            candidates=candidates, memory=dict(event_id=trace['event_id'], status='observed_source',
                                              scope='source_event_boundaries')))
    if detokenize([t['token'] for t in doc['tokens']]) != row['story']:
        raise ValueError('sampled tokens do not reconstruct original text')
    cursor = 0
    for event in graph['events']:
        enriched = {k:deepcopy(v) for k,v in event.items() if k != 'text'}
        token_ids = [t['id'] for t in doc['tokens'] if t['memory']['event_id'] == event['id']]
        # Silent source transitions stay metadata at an exact token boundary.
        enriched.update(name=event['kind'].replace('_',' '), token_ids=token_ids,
            anchor=dict(token=token_ids[0] if token_ids else cursor, silent=not bool(token_ids)),
            mapping_rules=[r['id'] for r in bank['rules'] if 'catalog' in r['profiles'] and _match(r,event,graph) is not None])
        doc['events'].append(enriched)
        if not token_ids and cursor < len(doc['tokens']):
            doc['tokens'][cursor]['memory'].setdefault('prior_silent_events', []).append(event['id'])
        for index in token_ids:
            token = doc['tokens'][index]
            posterior = defaultdict(float)
            for choice in token['candidates']:
                entity = doc['attributes'][choice['attributes']].get('entity')
                if entity: posterior[entity] += choice['probability']
            observations = []
            for entity, probability in sorted(posterior.items()):
                entries = [e for e in graph['entities'][entity]['line'] if e['event_id'] == event['id']]
                if not entries:
                    # Candidate meaning may differ from the finally committed event.
                    observations.append(dict(entity=entity, binding_probability=probability,
                                             confirmed_in_source_event=False))
                    continue
                entry = entries[0]
                observations.append(dict(entity=entity, binding_probability=probability,
                    confirmed_in_source_event=True, before=deepcopy(entry['before']), after=deepcopy(entry['after']),
                    tags=entry['tags'], changes=deepcopy(entry['own_effects'])))
            token['memory'].update(event_name=enriched['name'], participants=event['participants'],
                entity_tags=deepcopy(event['entity_tags']), entity_observations=observations,
                mapping_rules=enriched['mapping_rules'])
        if token_ids: cursor = token_ids[-1]+1
    from .event_scales import annotate_scales
    annotate_scales(doc)
    if row['final_world'].get('narrative'):
        doc['narrative_outcome'] = deepcopy(row['final_world']['narrative'])
    if 'commitments' in row['final_world'].get('narrative',{}):
        history = {e['id']:e for e in row['final_world']['history']}
        for event in doc['events']:
            observed = history[event['id']]
            if 'time' in observed:
                event['time'] = deepcopy(observed['time'])
                event['scales'] = [m['id'] for m in observed['event_scales']['memberships']]
                for tid in event['token_ids']:
                    doc['tokens'][tid]['memory']['scales'] = event['scales']
        doc['event_scales'] = dict(schema='event-scale-annotations-v1',
            scope='completed_source_observation',nodes=deepcopy(row['final_world']['narrative']['commitments']))
    from .plot_annotations import annotate_plots
    annotate_plots(doc, row=row)
    from .beat_annotations import annotate_beats
    annotate_beats(doc,row=row)
    validate(doc)
    return doc


def validate(doc):
    from .plot_annotations import validate_plots
    validate_plots(doc)
    if doc.get('schema') != 'annotated-story-memory-v1':
        raise ValueError('unknown story memory schema')
    if hashlib.sha256(doc['text'].encode()).hexdigest() != doc['text_sha256']:
        raise ValueError('source text hash mismatch')
    if detokenize([t['token'] for t in doc['tokens']]) != doc['text']:
        raise ValueError('source token text mismatch')
    owners = {}
    for event in doc['events']:
        for index in event['token_ids']:
            if index in owners: raise ValueError('token belongs to multiple source events')
            owners[index] = event['id']
        if bool(event['token_ids']) == event['anchor']['silent']:
            raise ValueError('incorrect silent event marker')
    if set(owners) != set(range(len(doc['tokens']))):
        raise ValueError('source token coverage mismatch')
    for index, token in enumerate(doc['tokens']):
        if token['id'] != index or token['memory']['event_id'] != owners[index]:
            raise ValueError('source token reference mismatch')
        if not math.isclose(sum(c['probability'] for c in token['candidates']), 1., abs_tol=1e-9):
            raise ValueError('token posterior is not normalized')
        for c in token['candidates']:
            if c['attributes'] not in doc['attributes']:
                raise ValueError('missing token attributes')
    return True


def as_graph(doc):
    """Transient compatibility view; source text remains in its intact document."""
    return dict(schema='entity-event-lines-v1', scenario=doc['scenario'], seed=doc['seed'],
        story=doc['text'], text_sha256=doc['text_sha256'], entities=doc['entities'], events=doc['events'])


def query(documents, *, event_kind=None, entity=None, entity_property=None, action=None, portable_only=False):
    """Return token/event references, never copied or rewritten text fragments.

    Action matches are candidates from sampled-token annotations, not claims
    that an embedded, quoted or negated action physically happened.
    """
    hits = []
    for doc in documents:
        for event in doc['events']:
            if event_kind and event['kind'] != event_kind: continue
            if portable_only and not event['mapping_rules']: continue
            if entity and entity not in event['participants']: continue
            if entity_property:
                if not any(entity_property in (entry['before'] or {}).get('properties', [])
                           for eid in event['participants'] for entry in doc['entities'][eid]['line']
                           if entry['event_id'] == event['id']): continue
            matching_tokens = []
            if action:
                matching_tokens = [index for index in event['token_ids'] if any(
                    doc['attributes'][c['attributes']].get('action', {}).get('lemma') == action
                    for c in doc['tokens'][index]['candidates']
                    if doc['attributes'][c['attributes']].get('action'))]
                if not matching_tokens: continue
            hits.append(dict(document=doc['id'], scenario=doc['scenario'], event_id=event['id'],
                name=event['name'], token_ids=list(event['token_ids']), matching_token_ids=matching_tokens,
                anchor=deepcopy(event['anchor']), mapping_rules=list(event['mapping_rules']),
                requires_target_guard_check=True))
    return hits


def retrieve(documents, world, *, operations=None, bank=None, bindings=None, rule_factors=None):
    """Map referenced events into the current target; deduplicate repeated seeds.

    Re-query after a target event to expose newly feasible continuations. This
    API doesn't author a goal policy or automatically stitch entire plots.
    """
    bank = load_bank() if bank is None else bank
    grouped, rejected = {}, []
    if (set(rule_factors or {}) - {r['id'] for r in bank['rules']}
            or any(not _positive(v) for v in (rule_factors or {}).values())):
        raise ValueError('positive finite factors for known mapping rules required')
    for doc in documents:
        for event in doc['events']:
            matches = [r for r in bank['rules'] if 'catalog' in r['profiles']
                and (operations is None or r['target']['event']['op'] in operations)
                and _match(r,event,as_graph(doc)) is not None]
            if not matches: continue
            ref = dict(document=doc['id'], scenario=doc['scenario'], event_id=event['id'],
                       token_ids=event['token_ids'], anchor=event['anchor'])
            result = mapping_distribution(as_graph(doc), event['frame']['actor'], [event['id']], world,
                bank=dict(schema='event-mapping-bank-v1',rules=matches), bindings=bindings,
                rule_factors={k:v for k,v in (rule_factors or {}).items() if k in {r['id'] for r in matches}})
            rejected.extend(dict(source=ref, **r) for r in result['rejected'])
            for candidate in result['candidates']:
                key = json.dumps(dict(rules=candidate['rules'],bindings=candidate['bindings'],
                    events=list(candidate['template']['events'].values())), sort_keys=True)
                if key not in grouped:
                    grouped[key] = dict(candidate, references=[], weight_policy='one_weight_per_distinct_rule_binding')
                grouped[key]['references'].append(ref)
    candidates = list(grouped.values())
    total = sum(c['score'] for c in candidates)
    for c in candidates: c['probability'] = c['score']/total
    return dict(candidates=candidates, rejected=rejected)


def generate_retrieved(documents, world, *, seed=0, heads=True, **options):
    """Generate one retrieved event with target annotations, leaving memory intact."""
    from .event_line_replay import replay, verify
    from .reusable_operations import ReusableLines
    result = retrieve(documents, world, **options)
    if not result['candidates']:
        raise ValueError('no feasible continuation in annotated story memory')
    selected = random.Random(seed).choices(result['candidates'],weights=[c['probability'] for c in result['candidates']])[0]
    template = deepcopy(selected['template'])
    template['source']['memory_retrieval'] = dict(references=deepcopy(selected['references']),
        candidates=[{k:deepcopy(v) for k,v in c.items() if k != 'template'} for c in result['candidates']],
        rejected=result['rejected'])
    row = replay(world,template,selected['bindings'],seed,heads=heads,driver_class=ReusableLines)
    verify(row,template,driver_class=ReusableLines)
    return row
