"""Grounded appraisal, utterance commitments and reader-aware motif grammar.

Specifications supply meanings and effects; this module never parses English.
Every ledger entry is bound to a carrier and an actually selected construction.
"""
from copy import deepcopy
import math

from ...grammar import seq, choice, text
from ..semantic_rules import tagged


def motif(key, carrier, meaning, node, *, phase='setup', guards=None):
    return dict(kind='motif',key=key,carrier=carrier,meaning=meaning,node=node,
                phase=phase,guards=guards or {})


def reminder(key, carrier, meaning, node):
    return motif(key,carrier,meaning,node,phase='reminder')


def utterance(key, speaker, listener, act, node):
    return dict(kind='utterance',key=key,speaker=speaker,listener=listener,act=act,node=node)


def walk(node):
    yield node
    for child in node.get('nodes',[]):yield from walk(child)
    for key in ('node','content'):
        if key in node:yield from walk(node[key])


def label(node):
    if node['kind']=='utterance':return 'decision.utterance:'+node['key']
    return 'decision.'+node['phase']+':'+node['key']+':'+node['meaning']


def memory(w):return w.narrative['storycraft']['decisions']


def initialize(w, *, appraisal=None, compression=True):
    w.narrative['storycraft']['decisions']=dict(schema='decision-beats-v1',
        appraisal_constraint=appraisal,compression=compression,appraisals=[],
        utterances={},dialogue_links=[],details={},payoffs=[],observed_costs=[],reminders=[])


def validate(spec):
    entities=spec['entities'];events={e['name'] for e in spec['events']}
    declarations=set()
    for e in spec['events']:
        a=e.get('appraisal')
        if a:
            if a['carrier'] not in entities or a['object'] not in entities:raise ValueError('unbound appraisal')
            if not a['evidence'] or not set(a['evidence'])<=events:raise ValueError('appraisal needs source events')
            if any(not math.isfinite(v) or not 0<=v<=1 for v in a['priorities'].values()):raise ValueError('invalid appraisal priorities')
        if any(not math.isfinite(v) or not -1<=v<=1 for v in e.get('stakes',{}).values()):raise ValueError('invalid decision stakes')
        for contract in e.get('observed_costs',[]):
            if contract['carrier'] not in entities or not contract['states']:raise ValueError('cost needs physical evidence')
        for node in walk(e['surface']):
            if node['kind']=='utterance':
                declarations.add(node['key'])
                if any(entities.get(node[k],{}).get('kind')!='person' for k in ('speaker','listener')):raise ValueError('utterance needs people')
                if not any(n['kind']=='speech' and all(n[k]==node[k] for k in ('speaker','listener','act')) for n in walk(node['node'])):
                    raise ValueError('utterance contract does not match speech')
            if node['kind']=='motif':
                if node['carrier'] not in entities or node['phase'] not in {'setup','payoff','reminder'}:raise ValueError('invalid motif binding')
                if any(i not in entities for i in node['guards']):raise ValueError('unbound motif guard')
                if node['phase']=='payoff' and not node['guards']:raise ValueError('payoff needs physical evidence')
    for e in spec['events']:
        if not set(e.get('requires_utterances',[]))<=declarations:raise ValueError('unknown required utterance')
        if not set(e.get('resolves_utterances',{}))<=set(e.get('requires_utterances',[])):raise ValueError('resolution needs utterance prerequisite')
        if not set(e.get('resolves_utterances',{}).values())<={'answered','fulfilled','honored'}:raise ValueError('unknown dialogue resolution')


def ready(w,e):
    m=memory(w)
    if e.get('appraisal'):
        if m['appraisal_constraint'] and m['appraisal_constraint']!=e['name']:return False
        executed={h['name'] for h in w.narrative['storycraft']['history']}
        if not set(e['appraisal']['evidence'])<=executed:return False
        visible={h['frame']['kind'].removeprefix('crafted_') for h in w.history if h.get('narrated')}
        if not set(e['appraisal']['evidence'])<=visible:return False
    if not set(e.get('requires_utterances',[]))<=m['utterances'].keys():return False
    for cost in e.get('observed_costs',[]):
        if cost['carrier'] not in w.entities:return False
        state=set(w.entities[cost['carrier']].state)
        change=e['effects'].get(cost['carrier'],{})
        state.difference_update(change.get('remove',[]));state.update(change.get('add',[]))
        if not set(cost['states'])<=state:return False
    for n in walk(e['surface']):
        if n['kind']!='motif':continue
        if any(i not in w.entities or not set(states)<=w.entities[i].state for i,states in n['guards'].items()):return False
        if n['phase']=='payoff':
            setup=m['details'].get(n['key'])
            if not setup or setup['carrier']!=n['carrier'] or setup['meaning']==n['meaning']:return False
    return True


def score(w,e):
    """Expected stakes are forecasts, never observed future outcomes."""
    m=memory(w);contributions=[]
    if e.get('stakes') and m['appraisals']:
        a=m['appraisals'][-1];carrier=w.entities[a['carrier']]
        for dimension,value in e['stakes'].items():
            priority=carrier.memes.get('Decision_'+dimension,0.)
            contributions.append(dict(dimension=dimension,priority=priority,forecast=value,
                contribution=1.5*priority*value,carrier=a['carrier'],source_event=a['event']))
    return dict(scope='forecast_from_committed_appraisal',contributions=contributions,
                logit=sum(x['contribution'] for x in contributions))


def reminder_weights(w,n):
    m=memory(w);known=m['details'].get(n['key'])
    redundant=bool(known and known['carrier']==n['carrier'] and known['meaning']==n['meaning'])
    count=sum(r['key']==n['key'] and r['meaning']==n['meaning'] and r['selected']=='say' for r in m['reminders'])
    # A new meaning must be expressed. Repeated information can be omitted;
    # it remains possible when the author disables compression for an ablation.
    if not redundant:return dict(say=1.,omit=0.,redundant=False)
    return dict(say=.15/(1+count) if m['compression'] else 1.,omit=1.,redundant=True)


def render(node,w):
    from .language import render as render_language
    inner=render_language(node['node'],w);tag=label(node)
    if node['kind']=='utterance':
        return tagged(seq(tag,inner),dialogue_contract={k:node[k] for k in ('key','speaker','listener','act')})
    attrs={k:deepcopy(node[k]) for k in ('key','carrier','meaning','phase')}
    if node['phase']=='reminder':
        weights=reminder_weights(w,node);attrs['compression']=weights
        full=seq(tag+':say',inner)
        if not weights['omit']:return tagged(full,narrative_detail=attrs)
        return tagged(choice('decision.reminder',full,seq(tag+':omit',text('')),
                             weights=(weights['say'],weights['omit'])),narrative_detail=attrs)
    return tagged(seq(tag,inner),narrative_detail=attrs)


def select(w,e,labels):
    selected=set(x for x in labels if x.startswith('decision.'))
    entries=[];valid=set()
    for n in walk(e['surface']):
        if n['kind'] not in {'motif','utterance'}:continue
        tag=label(n)
        if n['kind']=='motif' and n['phase']=='reminder':
            weights=reminder_weights(w,n)
            for variant in ('say','omit'):
                if weights[variant]>0:
                    valid.add(tag+':'+variant)
                    if tag+':'+variant in selected:entries.append(dict(node={k:deepcopy(v) for k,v in n.items() if k!='node'},selected=variant,weights=weights))
        else:
            valid.add(tag)
            if tag in selected:entries.append(dict(node={k:deepcopy(v) for k,v in n.items() if k!='node'}))
    # Choice-node labels carry no commitment; exact construction labels do.
    selected.discard('decision.reminder')
    if not selected<=valid:raise ValueError('unknown decision construction')
    return dict(labels=sorted(selected),entries=entries)


def commit_event(w,e):
    m=memory(w);eid=len(w.history)+1
    for key in e.get('requires_utterances',[]):
        source=m['utterances'][key]
        resolution=e.get('resolves_utterances',{}).get(key)
        m['dialogue_links'].append(dict(key=key,source_event=source['event'],event=eid,
                                       relation=resolution or 'depends_on'))
        if resolution:source.update(status=resolution,resolved_event=eid)
    if e.get('appraisal'):
        a=deepcopy(e['appraisal']);a.update(event=eid,name=e['name'])
        a['evidence_events']=[h['event'] for h in w.narrative['storycraft']['history'] if h['name'] in a['evidence']]
        for key in w.entities[a['carrier']].memes:
            if key.startswith('Decision_'):w.entities[a['carrier']].memes[key]=0.
        for dimension,value in a['priorities'].items():w.entities[a['carrier']].memes['Decision_'+dimension]=value
        m['appraisals'].append(a)
    for cost in e.get('observed_costs',[]):m['observed_costs'].append(dict(deepcopy(cost),event=eid,status='observed'))


def commit_narration(w,record,decision):
    m=memory(w);eid=record['id']
    for item in decision['entries']:
        n=item['node']
        if n['kind']=='utterance':
            m['utterances'][n['key']]=dict(key=n['key'],speaker=n['speaker'],listener=n['listener'],act=n['act'],event=eid,status='uttered')
            continue
        if n['phase']=='reminder':
            m['reminders'].append(dict(key=n['key'],meaning=n['meaning'],event=eid,
                                      selected=item['selected'],weights=item['weights']))
            if item['selected']=='omit':continue
        old=m['details'].get(n['key'])
        entry=dict(key=n['key'],carrier=n['carrier'],meaning=n['meaning'],event=eid,
                   setup_event=old.get('setup_event',old['event']) if old and old['carrier']==n['carrier'] else eid)
        if n['phase']=='payoff':
            m['payoffs'].append(dict(entry,earlier_meaning=old['meaning'],
                                    evidence=deepcopy(n['guards'])))
        m['details'][n['key']]=entry
    record['narrative_decision']=deepcopy(decision)
    record['after']=w.snapshot()
