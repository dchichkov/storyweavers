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
    act=('asking' if any(x in kind for x in ('request','consult','invite')) else
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
        event['beats']=[beat] if beat else []
        saved=history[event['id']]
        event['beat_expansion']=deepcopy(saved.get('beat_decision'))
        event['detail_links']=[]
        for spec in DETAILS.get(kind,[]):
            entity=mapping.get(spec['entity'],spec['entity']);key=prefix+kind+':'+spec['name']
            after=saved['after']['entities'].get(entity,{})
            if native in spec['setup'].split() and spec['state'] in after.get('state',[]):
                details.setdefault(key,dict(name=spec['name'],entity=entity,setup_event=event['id'],
                    initial_state=deepcopy(after),revisits=[]))
            if native in spec['result'].split() and key in details and details[key]['setup_event']<event['id']:
                link=dict(detail=key,setup_event=details[key]['setup_event'],result_event=event['id'],
                          entity=entity,observed_state=deepcopy(after),basis='replayed_state_and_authored_link')
                event['detail_links'].append(link);details[key]['revisits'].append(link)
        for tid in event['token_ids']:
            doc['tokens'][tid]['memory']['beats']=deepcopy(event['beats'])
            doc['tokens'][tid]['memory']['detail_links']=deepcopy(event['detail_links'])
        previous=event['id']
    doc['beats']=dict(schema='story-beats-v1',kinds=list(KINDS),details=details)
    return doc
