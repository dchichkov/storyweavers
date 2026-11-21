"""Reusable beat readings on intact source events and their existing tokens."""
from copy import deepcopy
import math

KINDS=('expectation','interruption','reaction','discovery','choice','payoff')
ROLE_KIND={**dict.fromkeys(('desire','promise','lack'),'expectation'),
           **dict.fromkeys(('setback','failed_attempt','conflict','threat'),'interruption'),
           **dict.fromkeys(('clue','discovery'),'discovery'),
           **dict.fromkeys(('choice','revision','decisive_action'),'choice'),
           **dict.fromkeys(('payoff','final_image'),'payoff')}

# Concrete motifs refer to entity/state observations, never text matching.
DETAILS={
 'pottery':[
  dict(name='grip',entity='grandpa',state='stiff_hand',setup='need goal',result='ending',object='cup'),
  dict(name='dent',entity='cup',state='dented',setup='slip',result='thumb smooth remake ending',object='cup')],
 'repair':[
  dict(name='locked_wheel',entity='wheel',state='locked',setup='tighten_wrongly',result='refit_and_test quiet_wheel',object='wheel'),
  dict(name='rattle',entity='cart',state='rattling',setup='cart_goal',result='move_plants quiet_wheel',object='cart')],
 'museum':[
  dict(name='moving_light',entity='torch',state='moving',setup='moving_light',result='controlled_trial little_wings',object='torch'),
  dict(name='large_shadow',entity='shadow',state='large',setup='exhibit_goal moving_light',result='controlled_trial little_wings',object='shadow')],
}


# A physical doer is not necessarily the person whose story changes. These
# reviewed exceptions come from source scenes and typed world effects.
EXPERIENCERS = {
    ('greenhouse', 'shade_break'): ('hero', 'protagonist_perspective_on_physical_setback'),
    ('museum', 'read_small_print'): ('hero', 'authored_recipient_of_control_explanation'),
    ('trail', 'felix_clears_ivy'): ('leni', 'authored_perception_subject'),
    ('pond', 'drifting_boat'): ('helper', 'authored_desire_speaker'),
    ('orchard', 'pear_promise'): ('helper', 'authored_gift_desire_speaker'),
}

# Desire, ability, and plot-level choice are not themselves promises/requests.
# These functions require both a reviewed scene and its actual speaking person.
SPEECH_READINGS = {
    ('pottery', 'consult'): ('grandpa', 'suggesting'),
    ('repair', 'admit_and_shelter'): ('hero', 'admitting'),
    ('market', 'admit_error'): ('hero', 'admitting'),
    ('laundry', 'ask_help'): ('hero', 'asking'),
    ('library', 'request_help'): ('hero', 'asking'),
    ('music', 'invite'): ('hero', 'asking'),
    ('music', 'decline'): ('partner', 'disagreeing'),
    ('music', 'choose_solo'): ('hero', 'committing'),
    ('music', 'offer_pattern'): ('partner', 'suggesting'),
    ('music', 'offer_private'): ('partner', 'suggesting'),
    ('greenhouse', 'promise_repair'): ('caretaker', 'committing'),
    ('greenhouse', 'ending'): ('hero', 'committing'),
}


def _entity_kind(entities, entity):
    value = (entities or {}).get(entity)
    if value is None:return None
    if not isinstance(value, dict):return value.kind
    if 'initial' in value:value = value.get('initial') or value.get('final') or {}
    return value.get('kind')


def reading(kind, role, frame, previous, *, scope='completed_source_observation',
            scenario=None, mapping=None, roles=None, entities=None, speakers=None):
    """An authored narrative perspective, not a new emotion or knowledge fact.

    ``speakers`` is omitted for a live construction and supplied after selection.
    """
    beat = ROLE_KIND.get(role)
    if kind in {'admit_and_shelter', 'admit_error', 'decline', 'response'}:beat = 'reaction'
    if not beat:return None
    mapping = mapping or {}
    experiencer = frame['actor'];basis = 'frame_actor_perspective'
    override = EXPERIENCERS.get((scenario, kind))
    if override:
        experiencer = mapping.get(override[0], override[0]);basis = override[1]
    if entities is not None and _entity_kind(entities, experiencer) != 'person':
        people = [p for p in (roles or {}).get('protagonist', []) if _entity_kind(entities, p) == 'person']
        if len(people) != 1:return None
        experiencer = people[0];basis = 'protagonist_perspective_on_physical_event'
    act = None;speech = SPEECH_READINGS.get((scenario, kind))
    if speech and mapping.get(speech[0], speech[0]) == experiencer:
        if speakers is None or experiencer in speakers:act = speech[1]
    return dict(kind=beat, experiencer=experiencer, experiencer_basis=basis,
                action_actor=frame['actor'], object=frame.get('patient') or frame.get('instrument') or None,
                preceding_event=previous, speech_act=act, scope=scope, basis='authored_event_reading',
                source_kind=kind, source_scenario=scenario)


def candidate_reading(doc, attributes, previous):
    """Project one token's own latent candidate, never the committed scene.

    Old archives lack live beat fields. Their historical reconstruction reads
    only the candidate event roles and the authored bank; it cannot inspect
    completed effects, future events, or the selected event's beat reading.
    """
    if 'beat' in attributes:
        return deepcopy(attributes['beat']), 'recorded_candidate_attributes'
    from .plot_bank import BANK
    event = attributes.get('event') or {}
    kind = event.get('source_kind');scenario = doc['scenario'];mapping = {}
    if scenario == 'joined':
        units = doc.get('source_options', {}).get('transfer', {}).get('units', [])
        unit = next((u for u in units if kind and kind.startswith(u['prefix'])), None)
        if unit is None:return None, 'unavailable_candidate_reading'
        scenario = unit['scenario'];mapping = unit['mapping'];kind = kind[len(unit['prefix']):]
    spec = BANK.get(scenario, {})
    role = spec.get('events', {}).get(kind, {}).get('role')
    frame = event.get('roles', {})
    if not role or not frame.get('actor'):return None, 'unavailable_candidate_reading'
    roles = {r: [mapping.get(e, e) for e in ids if mapping.get(e, e) in doc['entities']]
             for r, ids in spec['roles'].items()}
    beat = reading(kind, role, frame, previous, scope='reconstructed_candidate_event',
                   scenario=scenario, mapping=mapping, roles=roles, entities=doc['entities'],
                   speakers=[attributes['speaker']] if attributes.get('speaker') else [])
    if beat and not beat['object']:
        objects = roles.get('central_object', [])
        beat['object'] = objects[0] if len(objects) == 1 else None
    return beat, 'candidate_event_and_authored_bank'


def token_beat_candidates(doc, token, previous):
    result = []
    for candidate in token['candidates']:
        aid = candidate['attributes']
        if aid not in doc['attributes']:raise ValueError('missing token attributes')
        beat, basis = candidate_reading(doc, doc['attributes'][aid], previous)
        result.append(dict(probability=candidate['probability'], attributes=aid, beat=beat, basis=basis))
    return result


def annotate_beats(doc,*,row):
    """Add interpretations without changing prose, tokens or their posteriors."""
    history={e['id']:e for e in row['final_world']['history']}
    previous=row['initial_world']['history'][-1]['id'] if row['initial_world']['history'] else None
    details={}
    for event in doc['events']:
        plot=event.get('plot',{});kind=plot.get('source_scenario')
        frame=event['frame'];native=event['kind'];mapping={};prefix=''
        for u in row.get('options',{}).get('transfer',{}).get('units',[]):
            if native.startswith(u['prefix']):mapping=u['mapping'];prefix=u['prefix'];break
        native=native[len(prefix):]
        saved=history[event['id']]
        beat=reading(native,plot.get('role'),frame,previous, scenario=kind, mapping=mapping,
                     roles=plot.get('roles'), entities=doc['entities'], speakers=saved.get('speakers', []))
        # A missing coarse patient is filled from authored central-object roles.
        if beat and not beat['object']:
            objects=plot.get('roles',{}).get('central_object',[])
            beat['object']=objects[0] if len(objects)==1 else None
        event['beats']=[dict(beat,phase='native_scene')] if beat else []
        if beat and beat['speech_act']:
            evidence=[tid for tid in event['token_ids'] if any(
                doc['attributes'][c['attributes']].get('speaker') == beat['experiencer']
                for c in doc['tokens'][tid]['candidates'])]
            event['beats'][0]['speech_evidence']=dict(speaker=beat['experiencer'],
                token_ids=evidence, basis='selected_scene_speaker_and_typed_token_candidates')
        event['beat_expansion']=deepcopy(saved.get('beat_decision'))
        decision=saved.get('beat_decision')
        if decision and decision['selected']!='immediate':
            selected=next(c for c in decision['candidates'] if c['id']==decision['selected'])
            event['beats'].insert(0,dict({k:deepcopy(v) for k,v in selected.items() if k not in {'weight','probability'}},
                                       phase='pre_event',scope='completed_source_observation'))
        event['detail_links']=[]
        for spec in DETAILS.get(kind,[]):
            entity=mapping.get(spec['entity'],spec['entity']);key=prefix+kind+':'+spec['name']
            after=saved['after']['entities'].get(entity,{})
            if event['narrated'] and native in spec['setup'].split() and spec['state'] in after.get('state',[]):
                details.setdefault(key,dict(name=spec['name'],entity=entity,setup_event=event['id'],
                    initial_state=deepcopy(after),revisits=[]))
            if native in spec['result'].split() and key in details and details[key]['setup_event']<event['id']:
                link=dict(detail=key,setup_event=details[key]['setup_event'],result_event=event['id'],
                          entity=entity,observed_state=deepcopy(after),basis='replayed_state_and_authored_link')
                event['detail_links'].append(link);details[key]['revisits'].append(link)
        for tid in event['token_ids']:
            token=doc['tokens'][tid]
            token['memory']['beats']=deepcopy(event['beats'])
            token['memory']['beat_candidates']=token_beat_candidates(doc,token,previous)
            token['memory']['detail_links']=deepcopy(event['detail_links'])
        previous=event['id']
    doc['beats']=dict(schema='story-beats-v2',kinds=list(KINDS),details=details,
                      scope='completed_source_observation')
    validate_beats(doc)
    return doc


def validate_beats(doc):
    if 'beats' not in doc:return True
    strict = doc['beats'].get('schema') == 'story-beats-v2'
    if doc['beats'].get('schema') not in {'story-beats-v1', 'story-beats-v2'}:
        raise ValueError('unknown beat annotation schema')
    prior={e['id'] for e in doc.get('plot_prior_events',[])}
    previous = doc.get('plot_prior_events', [])[-1]['id'] if doc.get('plot_prior_events') else None
    for event in doc['events']:
        for beat in event.get('beats',[]):
            if beat['kind'] not in KINDS:raise ValueError('unknown beat kind')
            if beat['experiencer'] not in doc['entities']:raise ValueError('unbound beat experiencer')
            if beat['object'] is not None and beat['object'] not in doc['entities']:raise ValueError('unbound beat object')
            if beat['preceding_event'] is not None and beat['preceding_event'] not in prior:
                raise ValueError('missing or future beat predecessor')
            if strict and _entity_kind(doc['entities'], beat['experiencer']) != 'person':
                raise ValueError('beat experiencer is not a person')
            if strict and beat.get('action_actor') and beat['action_actor'] not in doc['entities']:
                raise ValueError('unbound beat action actor')
            if strict and beat.get('speech_evidence'):
                evidence = beat['speech_evidence']
                if evidence['speaker'] != beat['experiencer'] or 'speaker' not in event['entity_tags'].get(evidence['speaker'], []):
                    raise ValueError('beat speech speaker mismatch')
                if not evidence['token_ids'] or not set(evidence['token_ids']) <= set(event['token_ids']):
                    raise ValueError('missing beat speech token evidence')
        if strict:
            for link in event.get('detail_links', []):
                detail = doc['beats']['details'].get(link['detail'])
                if (not detail or link['setup_event'] not in prior or link['result_event'] != event['id']
                        or link['entity'] not in doc['entities'] or link['entity'] != detail['entity']
                        or link['setup_event'] != detail['setup_event']):
                    raise ValueError('invalid or future beat detail link')
        for tid in event['token_ids']:
            choices=doc['tokens'][tid]['memory'].get('beat_candidates',[])
            if (not choices or any(type(c.get('probability')) not in (int, float)
                    # Preserve archived floating-point posteriors exactly;
                    # a sum can round one ulp above one without being invalid.
                    or not math.isfinite(c['probability']) or not 0 <= c['probability'] <= 1 + 1e-12 for c in choices)
                    or not math.isclose(sum(c['probability'] for c in choices),1.,abs_tol=1e-8)):
                raise ValueError('unnormalized token beat posterior')
            if strict:
                token = doc['tokens'][tid]
                if choices != token_beat_candidates(doc, token, previous):
                    raise ValueError('token beat posterior differs from candidate attributes')
                if token['memory'].get('beats') != event.get('beats', []):
                    raise ValueError('token beat context differs from source event')
                if token['memory'].get('detail_links') != event.get('detail_links', []):
                    raise ValueError('token detail context differs from source event')
        prior.add(event['id']);previous = event['id']
    return True
