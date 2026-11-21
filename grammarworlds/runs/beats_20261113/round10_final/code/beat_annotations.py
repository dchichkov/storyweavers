"""Reusable beat readings on intact source events and their existing tokens."""
from copy import deepcopy

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


def reading(kind,role,frame,previous,*,scope='completed_source_observation'):
    beat=ROLE_KIND.get(role)
    if kind in {'admit_and_shelter','admit_error','decline','response'}:beat='reaction'
    if not beat:return None
    act=('asking' if any(x in kind for x in ('request','invite')) else
         'suggesting' if kind=='consult' else
         'admitting' if kind in {'admit_and_shelter','admit_error'} else
         'disagreeing' if kind=='decline' else 'committing' if role in {'promise','choice'} else None)
    return dict(kind=beat,experiencer=frame['actor'],object=frame['patient'] or frame['instrument'] or None,
                preceding_event=previous,speech_act=act,scope=scope,basis='authored_event_reading')


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
        beat=reading(native,plot.get('role'),frame,previous)
        # A missing coarse patient is filled from authored central-object roles.
        if beat and not beat['object']:
            objects=plot.get('roles',{}).get('central_object',[])
            beat['object']=objects[0] if len(objects)==1 else None
        event['beats']=[dict(beat,phase='native_scene')] if beat else []
        saved=history[event['id']]
        if beat and not saved.get('speakers'):
            beat['speech_act']=None
            event['beats'][0]['speech_act']=None
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
            token['memory']['beat_candidates']=[dict(probability=c['probability'],
                beat=deepcopy(doc['attributes'][c['attributes']].get('beat',beat))) for c in token['candidates']]
            token['memory']['detail_links']=deepcopy(event['detail_links'])
        previous=event['id']
    doc['beats']=dict(schema='story-beats-v1',kinds=list(KINDS),details=details)
    validate_beats(doc)
    return doc


def validate_beats(doc):
    if 'beats' not in doc:return True
    import math
    prior={e['id'] for e in doc.get('plot_prior_events',[])}
    for event in doc['events']:
        for beat in event.get('beats',[]):
            if beat['kind'] not in KINDS:raise ValueError('unknown beat kind')
            if beat['experiencer'] not in doc['entities']:raise ValueError('unbound beat experiencer')
            if beat['object'] is not None and beat['object'] not in doc['entities']:raise ValueError('unbound beat object')
            if beat['preceding_event'] is not None and beat['preceding_event'] not in prior:
                raise ValueError('missing or future beat predecessor')
        prior.add(event['id'])
        for tid in event['token_ids']:
            choices=doc['tokens'][tid]['memory'].get('beat_candidates',[])
            if not choices or not math.isclose(sum(c['probability'] for c in choices),1.,abs_tol=1e-8):
                raise ValueError('unnormalized token beat posterior')
    return True
