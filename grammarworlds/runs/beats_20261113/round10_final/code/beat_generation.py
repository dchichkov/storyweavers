"""Optional scene beats over shared grammar, grounded prefix context and memory.

The pre-event beat and its native action form one atomic scene. Native guards
remain authoritative; requests/attention/commitments are separately recorded.
"""
from copy import deepcopy
from dataclasses import replace,asdict
import json

from .beat_annotations import DETAILS,reading
from .event_scales import _binding
from .plot_annotations import _context
from .grammar import Node,seq,choice,text,expand
from .storytelling.surface import detokenize
from .storytelling.semantic_rules import tagged


def initialize(w,budget):
    if type(budget) is not int or not 0<=budget<=12:raise ValueError('beat budget must be an integer from 0 to 12')
    if not budget:return
    if 'beats' in w.narrative:
        if w.narrative['beats']['budget']!=budget:raise ValueError('cannot reset a continuing beat budget')
        return
    w.narrative['beats']=dict(schema='beat-memory-v1',budget=budget,used=0,expanded_triggers=[],
                             details={},history=[],speech_acts=[])


def native_context(pack,w,f):
    scenario,prefix,mapping,kind=_binding(pack,w,f)
    context=_context(scenario,kind,prefix,mapping,w.entities,w.history)
    return scenario,prefix,mapping,kind,context


def _ref(w,e):
    entity=w.entities[e]
    return tagged(seq('referent:'+e,entity.noun if entity.kind=='person' else 'the '+entity.noun),
                  entity=e,nominal=dict(type='entity',entity=e),lexical_role='entity')


def _place(w,e):
    """Resolve containment (wheel → cart → person → courtyard), without loops."""
    seen=set()
    while e in w.entities and e not in seen:
        seen.add(e);n=w.entities[e].location
        if n==e:return e
        e=n
    return e


def _line(w,actor,listener,*parts,tense='past'):
    content=seq('beat.utterance',*parts)
    node=seq('dialogue.speaker:'+actor,_ref(w,actor),'said,' if tense=='past' else 'says,',Node('text','quote.open',('“',)),
             content,Node('text','quote.close',('”',)))
    return seq('dialogue.listener:'+actor+':'+listener,node)


def options(pack,w,f,tense='past'):
    scenario,prefix,mapping,kind,info=native_context(pack,w,f)
    if not info:return []
    memory=w.narrative.get('beats')
    if not memory or memory['used']>=memory['budget']:return []
    hero=mapping.get('hero',w.hero);helper=mapping.get('helper',w.helper)
    objects=info['roles'].get('central_object',[])
    obj=f.patient or (objects[0] if objects else '')
    if obj not in w.entities or hero not in w.entities:return []
    previous=next((e for e in reversed(w.history) if e.get('narrated')),None)
    if not previous:return []
    prev_kind=previous['frame']['kind']
    prev=_context(scenario,prev_kind[len(prefix):],prefix,mapping,w.entities,w.history[:-1]) if prev_kind.startswith(prefix) else None
    if prev and prev['role'] in {'setback','failed_attempt','conflict','threat'}:
        # React to the failed object, not an incidental patient of the next
        # action (the instruction label or the tray being moved to safety).
        affected=previous['frame']['patient'] or previous['frame']['instrument']
        if affected in w.entities:obj=affected
    trigger=previous['id'];role=info['role']
    candidates=[]
    def add(name,weight,node,beat,speech=None,detail=None):
        candidates.append(dict(id=name,weight=weight,node=node,kind=beat,speech_act=speech,
            experiencer=hero,object=obj,preceding_event=trigger,detail=detail,
            source_scenario=scenario,prefix=prefix,scope='pre_event_candidate',
            listener=helper if speech else None,knowledge_change=False))
    together=helper in w.entities and helper!=hero and _place(w,helper)==_place(w,hero)
    if prev and prev['role'] in {'setback','failed_attempt','conflict','threat'} and trigger not in memory['expanded_triggers']:
        add('reaction',2,seq('beat.reaction',_ref(w,hero),'hesitated.' if tense=='past' else 'hesitates.'),'reaction')
        if _place(w,obj)==_place(w,hero):
            add('inspection',2,seq('beat.inspection',_ref(w,hero),'looked closely at' if tense=='past' else 'looks closely at',_ref(w,obj),'.'),'reaction')
        if together:
            add('asking',2,_line(w,hero,helper,'Could you help me with',_ref(w,obj),'?',tense=tense),'reaction','asking')
    if f.actor==hero and role in {'revision','choice','decisive_action'} and prev and prev['role'] in {'clue','discovery'}:
        if together:
            tool=f.instrument or f.destination
            concrete=tool in w.entities and w.entities[tool].kind not in {'person','place'} and _place(w,tool)==_place(w,hero)
            action=(_ref(w,tool),'.') if concrete else ('another way.',)
            add('committing',2,_line(w,hero,helper,'I will try',*action,tense=tense),'choice','committing')
            add('suggesting',1,_line(w,hero,helper,'Let us try',*action,tense=tense),'choice','suggesting')
            for c in candidates[-2:]:c['planned_event']=f.kind
    # Echoes may only read recorded setups and currently verified physical state.
    for key,detail in memory['details'].items():
        if detail['prefix']!=prefix or detail['source_scenario']!=scenario or detail.get('used'):continue
        if kind not in detail['results']:continue
        entity=detail['entity'];states=w.entities[entity].state
        phrase=None
        if detail['name']=='dent':
            if 'thumb_rest' in states:phrase=seq('beat.echo','The dent had become a thumb rest.' if tense=='past' else 'The dent has become a thumb rest.')
            elif 'bowl_shape' in states:phrase=seq('beat.echo','The dent was gone now.' if tense=='past' else 'The dent is gone now.')
            elif 'smoothed' in states:phrase=seq('beat.echo','The dent was smooth now.' if tense=='past' else 'The dent is smooth now.')
        elif detail['name']=='grip' and 'stiff_hand' in states:
            phrase=seq('beat.echo',_ref(w,entity),"still had a stiff hand." if tense=='past' else 'still has a stiff hand.')
        elif detail['name']=='locked_wheel' and 'smooth' in states:
            phrase=seq('beat.echo','The wheel that had locked now turned freely.' if tense=='past' else 'The wheel that locked now turns freely.')
        elif detail['name']=='rattle' and 'repaired' in states:
            phrase=seq('beat.echo',_ref(w,entity),'no longer rattled.' if tense=='past' else 'no longer rattles.')
        elif detail['name']=='moving_light' and 'fixed' in states:
            phrase=seq('beat.echo','This time,',_ref(w,entity),'stayed still.' if tense=='past' else 'stays still.')
        elif detail['name']=='large_shadow' and 'small' in states:
            phrase=seq('beat.echo','This was the small shadow' if tense=='past' else 'This is the small shadow',
                       _ref(w,hero),'had wanted.' if tense=='past' else 'wanted.')
        if phrase:
            add('echo:'+key,2,phrase,'payoff',detail=key)
            candidates[-1]['object']=entity
            candidates[-1]['perspective']='narrator'
            candidates[-1]['setup_event']=detail['setup_event']
    # A native scene may already voice its character's choice. Do not preface
    # that with a second generic "I will try" line from the same speaker.
    if any(c['id'] in {'committing','suggesting'} for c in candidates):
        from .storytelling.plans import plan
        native=(pack.render_scene(w,f,tense,continuations='original') if hasattr(pack,'render_scene') else
                plan(w,f,tense,getattr(pack,'LEXICON',None)))
        def speaks(node):
            return node.label=='dialogue.speaker:'+hero or any(speaks(c) for c in node.children if isinstance(c,Node))
        if native and speaks(native.node):
            candidates=[c for c in candidates if c['id'] not in {'committing','suggesting'}]
    if memory['budget']-memory['used']==1 and any(not d['used'] for d in memory['details'].values()):
        # A short story keeps room for an earned reminder at the resolution.
        candidates=[c for c in candidates if c['detail']]
    for c in candidates:
        if not c['detail'] and trigger in memory['expanded_triggers']:c['weight']*=.1
        if any(b['id']==c['id'] for b in memory['history']):c['weight']*=.25
    if not candidates:return []
    add('immediate',3,text(''),'choice')
    total=sum(c['weight'] for c in candidates)
    for c in candidates:
        c['probability']=c['weight']/total
        c['text']=detokenize(next(expand(c['node']))[0])
        c['actor_name']=w.entities[hero].noun
        c['object_name']=w.entities[c['object']].noun
        c['listener_name']=w.entities[helper].noun if c['listener'] else None
    return candidates


def expand_scene(pack,w,f,scene,tense):
    if scene is None:return scene
    scenario,prefix,mapping,kind,info=native_context(pack,w,f)
    if info:
        native_beat=reading(kind,info['role'],asdict(f),w.history[-1]['id'] if w.history else None,
                            scope='candidate_native_event')
        if native_beat:
            if not native_beat['object']:
                objects=info['roles'].get('central_object',[])
                native_beat['object']=objects[0] if len(objects)==1 else None
            def has_speech(node):
                return node.label.startswith('dialogue.speaker:') or any(has_speech(c) for c in node.children if isinstance(c,Node))
            if not has_speech(scene.node):native_beat['speech_act']=None
            scene=replace(scene,node=tagged(scene.node,beat=dict(native_beat,phase='native_scene')))
    candidates=options(pack,w,f,tense)
    if not candidates:return scene
    nodes=[]
    for c in candidates:
        attrs={k:v for k,v in c.items() if k not in {'node','weight','probability'}}
        prefix=tagged(c['node'],beat=attrs)
        nodes.append(seq('beat.selection:'+c['id'],prefix,scene.node))
    return replace(scene,node=choice('beat.expansion',*nodes,weights=tuple(c['weight'] for c in candidates)))


def select(pack,w,f,labels,tense='past'):
    candidates=options(pack,w,f,tense)
    selected=[x.split(':',1)[1] for x in labels if x.startswith('beat.selection:')]
    if not selected:return None
    if len(selected)!=1 or selected[0] not in {c['id'] for c in candidates}:raise ValueError('invalid beat selection')
    return dict(selected=selected[0],candidates=[{k:deepcopy(v) for k,v in c.items() if k!='node'} for c in candidates])


def commit(pack,w,record,decision):
    memory=w.narrative.get('beats')
    if memory is None:return
    f=record['frame'];from .world import Frame
    frame=Frame(**{**f,'cause_ids':tuple(f['cause_ids'])})
    scenario,prefix,mapping,kind,_=native_context(pack,w,frame)
    if decision:
        picked=next(c for c in decision['candidates'] if c['id']==decision['selected'])
        if picked['id']!='immediate':
            memory['used']+=1;memory['expanded_triggers'].append(picked['preceding_event'])
            memory['history'].append(dict(deepcopy(picked),event=record['id'],scope='executed_pre_event_beat'))
            actor=w.entities[picked['experiencer']]
            concept={'reaction':'Caution','inspection':'Attention'}.get(picked['id'])
            if concept:actor.memes[concept]=actor.memes.get(concept,0.)+.1
            if picked['speech_act']:
                memory.setdefault('speech_acts',[]).append(dict(act=picked['speech_act'],
                    speaker=picked['experiencer'],listener=picked['listener'],object=picked['object'],
                    event=record['id'],preceding_event=picked['preceding_event'],
                    following_native_action=f['kind'],status='uttered'))
            if picked['detail']:memory['details'][picked['detail']]['used']=True
        record['beat_decision']=deepcopy(decision)
    for spec in DETAILS.get(scenario,[]):
        entity=mapping.get(spec['entity'],spec['entity']);key=prefix+scenario+':'+spec['name']
        if record['sentence'] and kind in spec['setup'].split() and entity in w.entities and spec['state'] in w.entities[entity].state:
            memory['details'].setdefault(key,dict(name=spec['name'],entity=entity,setup_event=record['id'],
                initial_state=sorted(w.entities[entity].state),results=spec['result'].split(),
                source_scenario=scenario,prefix=prefix,used=False))
    record['after']=w.snapshot()
