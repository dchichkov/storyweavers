"""Add beat readings to the existing 400-story archive without replacing text."""
import argparse
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path

from .story_memory import load_documents,validate
from .storytelling.runtime import setup
from .storytelling.surface import detokenize
from .world import Frame
from .beat_annotations import annotate_beats


def _require(condition, message):
    if not condition:raise ValueError(message)


def _check_decision(world, decision, prose):
    """Validate the recorded policy's internal evidence, not today's weights."""
    if decision is None:return
    candidates = decision.get('candidates', [])
    _require(bool(candidates), 'empty archived beat distribution')
    ids = [c.get('id') for c in candidates]
    _require(len(ids) == len(set(ids)) and all(isinstance(i, str) for i in ids), 'ambiguous archived beat IDs')
    _require(decision.get('selected') in ids, 'missing selected archived beat')
    for c in candidates:
        for key in ('weight', 'probability'):
            value = c.get(key)
            _require(type(value) in (int, float) and math.isfinite(value) and value > 0,
                     'invalid archived beat ' + key)
    total = sum(c['weight'] for c in candidates)
    _require(math.isclose(sum(c['probability'] for c in candidates), 1., abs_tol=1e-9),
             'unnormalized archived beat distribution')
    _require(all(math.isclose(c['probability'], c['weight']/total, rel_tol=1e-9, abs_tol=1e-12)
                 for c in candidates), 'archived beat probability differs from recorded weight')
    history = {e['id']:e for e in world.history}
    for c in candidates:
        _require(c.get('experiencer') in world.entities
                 and world.entities[c['experiencer']].kind == 'person', 'unbound archived beat experiencer')
        _require(c.get('object') in world.entities, 'unbound archived beat object')
        _require(c.get('preceding_event') in history and history[c['preceding_event']].get('narrated'),
                 'missing or future archived beat predecessor')
        if c.get('listener') is not None:
            _require(c['listener'] in world.entities and world.entities[c['listener']].kind == 'person',
                     'unbound archived beat listener')
        _require(c.get('knowledge_change') is False, 'unsupported archived beat knowledge change')
    picked = next(c for c in candidates if c['id'] == decision['selected'])
    if picked['id'] == 'immediate':
        _require(picked.get('text') == '', 'immediate action has an archived beat surface')
        return
    _require(bool(picked.get('text')) and prose.startswith(picked['text']), 'archived beat surface mismatch')
    memory = world.narrative.get('beats', {})
    _require(memory and memory['used'] < memory['budget'], 'archived beat budget exceeded')
    if picked.get('detail'):
        detail = memory.get('details', {}).get(picked['detail'])
        _require(detail and not detail.get('used') and detail['entity'] == picked['object']
                 and detail['setup_event'] == picked.get('setup_event') and detail['setup_event'] in history,
                 'archived callback binding mismatch')
        if detail.get('callback'):
            _require(detail['callback']['state'] in world.entities[detail['entity']].state,
                     'archived callback state mismatch')


def _recorded_detail_ledger(world, record, before, archived):
    """Plant only the historical ledger; a newer catalogue is not old state."""
    memory = world.narrative['beats'];result = deepcopy(before)
    picked = next((c for c in record.get('beat_decision', {}).get('candidates', [])
                   if c['id'] == record['beat_decision']['selected']), None)
    if picked and picked.get('detail'):result[picked['detail']]['used'] = True
    for key, detail in archived.items():
        if detail['setup_event'] != record['id']:continue
        entity = detail.get('entity')
        _require(key not in result and entity in world.entities, 'archived detail carrier mismatch')
        _require(bool(record['sentence']), 'archived detail setup is silent')
        _require(key == detail['prefix'] + detail['source_scenario'] + ':' + detail['name'],
                 'archived detail source mismatch')
        _require(sorted(world.entities[entity].state) == detail['initial_state'], 'archived detail state mismatch')
        result[key] = deepcopy(detail);result[key]['used'] = False
    memory['details'] = result


def replay_document(doc):
    """Replay native guards and recorded beat actions without resampling.

    Recorded weights are validated for internal consistency. They are not
    claimed to match the current beat policy, and new detail definitions cannot
    silently appear in a historical world's state.
    """
    validate(doc)
    pack,w=setup(doc['scenario'],doc['seed'],**doc['source_options'])
    initial=w.to_dict()
    original_entities = {e:r['initial'] for e,r in doc['entities'].items() if r['initial'] is not None}
    _require(initial['entities'] == original_entities, 'source initial state changed')
    _require([(e['id'],e['frame']['kind']) for e in initial['history']]
             == [(e['id'],e['kind']) for e in doc.get('plot_prior_events', [])],
             'source prior event history changed')
    archived_narrative = doc.get('narrative_outcome')
    archived_beats = (archived_narrative or {}).get('beats')
    if 'beats' in w.narrative:
        _require(archived_beats is not None, 'missing archived beat outcome')
        _require(archived_beats['budget'] == w.narrative['beats']['budget'], 'archived beat budget changed')
    elif archived_beats is not None:
        raise ValueError('archived beat state has no source initialization')
    recorded_beats = 0
    for entity,record in doc['entities'].items():
        if record['initial'] is not None:
            _require(initial['entities'][entity]==record['initial'],'source initial state changed')
    for event in doc['events']:
        f=Frame(**{**event['frame'],'cause_ids':tuple(event['frame']['cause_ids'])})
        _require(event['id'] == len(w.history)+1, 'missing or duplicate archived event')
        available = [(k, frame) for k,frame in pack.candidates(w) if frame == f]
        _require(len(available) == 1, 'archived frame is not uniquely available')
        before=w.to_dict()['entities'];flags_before=set(w.flags)
        prose=detokenize([doc['tokens'][tid]['token'] for tid in event['token_ids']])
        _require(bool(prose) == event['narrated'], 'archived event narration mismatch')
        decision=event.get('beat_expansion')
        if decision is not None:
            _require('beats' in w.narrative, 'archived beat decision has no state')
            _check_decision(w, decision, prose)
            recorded_beats += decision['selected'] != 'immediate'
        details_before = deepcopy(w.narrative.get('beats', {}).get('details', {}))
        record=pack.commit(w,f,prose)
        if 'beats' in w.narrative:
            from .beat_generation import commit as commit_beats
            commit_beats(pack,w,record,deepcopy(decision))
            _recorded_detail_ledger(w,record,details_before,archived_beats['details'])
        record['speakers']=sorted(e for e,tags in event['entity_tags'].items() if 'speaker' in tags)
        record['referents']=sorted(e for e,tags in event['entity_tags'].items() if 'mentioned' in tags)
        record['narrated']=event['narrated']
        if 'plot_execution' in w.narrative:
            from .plot_execution import finalize_narration
            finalize_narration(w,record)
        record['after']=w.snapshot();after=w.to_dict()['entities']
        effects={}
        for entity in before.keys()|after.keys():
            old=before.get(entity,{});new=after.get(entity,{})
            delta={k:dict(before=old.get(k),after=new.get(k)) for k in old.keys()|new.keys() if old.get(k)!=new.get(k)}
            if delta:effects[entity]=delta
        _require(effects==event['effects'],'archived source physics changed')
        contract=event['global_contract']
        _require(sorted(w.flags-flags_before)==contract['flags_added']
                 and sorted(flags_before-w.flags)==contract['flags_removed'], 'archived flag transitions changed')
    _require(w.to_dict()['entities'] == {e:r['final'] for e,r in doc['entities'].items()},
             'archived final entities changed')
    if archived_narrative is not None:
        _require(w.narrative == archived_narrative, 'archived narrative outcome changed')
    evidence=dict(mode='recorded_native_frames_and_recorded_beat_actions',
        current_beat_policy_recomputed=False, native_guards_verified=True, entity_effects_verified=True,
        final_entities_verified=True, final_narrative_verified=archived_narrative is not None,
        native_events=len(doc['events']), recorded_beats=recorded_beats,
        initial_state_source='receiving_transfer_options' if doc['scenario']=='joined' else 'source_setup_options',
        limits=['Recorded weights are checked internally, not authenticated against a historical sampler.',
                'Archives without a narrative outcome support physical replay only.'])
    return dict(initial_world=initial,final_world=w.to_dict(),options=deepcopy(doc['source_options']),
                annotation_replay=evidence)


def _catalogue_supports_archived_setups(doc):
    from .beat_annotations import DETAILS
    for detail in doc.get('narrative_outcome', {}).get('beats', {}).get('details', {}).values():
        spec = next((s for s in DETAILS.get(detail['source_scenario'], []) if s['name'] == detail['name']), None)
        if (not spec or spec['state'] not in detail['initial_state']
                or spec['result'].split() != detail['results'] or spec.get('callback') != detail.get('callback')):
            return False
    return True


def export(source,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    counts=Counter();worlds=set();tokens=0;events=0;documents=0;replays=Counter()
    pending=out/'.stories.memory.jsonl.gz.pending'
    try:
        with gzip.open(pending,'wt') as sink:
            for doc in load_documents(source):
                before=deepcopy(doc)
                row=replay_document(doc)
                if _catalogue_supports_archived_setups(doc):
                    annotate_beats(doc,row=row)
                    refresh='current_authored_readings_over_verified_archived_events'
                else:
                    _require('beats' in doc, 'historical detail catalogue unavailable without archived annotations')
                    refresh='preserved_archived_annotations_for_changed_detail_catalogue'
                doc['beats']['export_replay']=dict(row['annotation_replay'],annotation_refresh=refresh)
                validate(doc)
                _require(doc['text']==before['text'] and doc['attributes']==before['attributes'], 'export changed original text or attributes')
                _require([(t['token'],t['candidates'],t['position']) for t in doc['tokens']]
                         ==[(t['token'],t['candidates'],t['position']) for t in before['tokens']],
                         'export changed original tokens or probabilities')
                counts.update(b['kind'] for e in doc['events'] for b in e['beats'])
                replays['narrative_verified']+=row['annotation_replay']['final_narrative_verified']
                replays['recorded_beats']+=row['annotation_replay']['recorded_beats']
                replays[refresh]+=1
                worlds.add(doc['scenario']);tokens+=len(doc['tokens']);events+=len(doc['events']);documents+=1
                sink.write(json.dumps(doc,separators=(',',':'))+'\n')
                if documents%50==0:print(documents,flush=True)
    except Exception:
        pending.unlink(missing_ok=True)
        raise
    pending.replace(out/'stories.memory.jsonl.gz')
    summary=dict(documents=documents,worlds=len(worlds),tokens=tokens,events=events,beat_counts=counts,
                 text_positions_original_attributes_and_probabilities_preserved=True,
                 replay_counts=replays,current_beat_policy_recomputed=False)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    root=Path(__file__).parent
    (out/'manifest.json').write_text(json.dumps({f:hashlib.sha256((root/f).read_bytes()).hexdigest()
          for f in ('beat_annotations.py','beat_annotation_export.py')},indent=2)+'\n')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=Path('grammarworlds/runs/plot_annotations_20261108'))
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();export(a.source,a.out)
