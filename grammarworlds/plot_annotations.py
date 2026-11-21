"""Plot roles on intact source tokens, with separately scoped live candidates."""
from copy import deepcopy

from .plot_bank import BANK, ARCHETYPES, ROLE_STAGE


def _incoming(spec,kind,history,prefix):
    links=[]
    for link in spec['links']:
        if kind not in link['target'].split():continue
        sources={prefix+k for k in link['source'].split()}
        for event in history:
            if event['frame']['kind'] in sources:
                links.append(dict(source_event=event['id'],relation=link['relation'],
                    basis='authored_narrative_reading',mechanically_verified=False))
    return links


def _context(scenario,kind,prefix,mapping,entities,history):
    if scenario not in BANK or kind not in BANK[scenario]['events']:return None
    spec=BANK[scenario]
    roles={r:[mapping.get(e,e) for e in ids if mapping.get(e,e) in entities] for r,ids in spec['roles'].items()}
    return dict(plot_id=prefix+scenario+'/plot',source_scenario=scenario,
        archetypes=deepcopy(spec['archetypes']),local_pattern=spec['local_pattern'],goal=spec['goal'],
        roles=roles,unbound_roles=[r for r,ids in roles.items() if not ids],
        stakes=dict(description=spec['stakes'],basis='authored_interpretation'),
        **deepcopy(spec['events'][kind]),incoming_links=_incoming(spec,kind,history,prefix))


class PlotPack:
    """Metadata only: no changes to native guards, effects or sampling weights."""
    def __init__(self,base):self.base=base
    def __getattr__(self,name):return getattr(self.base,name)
    def plot_context(self,w,f):
        from .event_scales import _binding
        scenario,prefix,mapping,kind=_binding(self.base,w,f)
        result=_context(scenario,kind,prefix,mapping,w.entities,w.history)
        if result is not None:
            result.update(scope='receiving_prefix',status='proposed')
            if 'plot_execution' in w.narrative:
                result['receiving_plot']=deepcopy(w.narrative['plot_execution'])
        return result


def annotate_plots(doc,*,row=None):
    """Add historical narrative readings without changing text or posteriors.

    Links are human-authored interpretations over actual event references.
    Observed effects and native dependencies remain separate evidence fields.
    A transferred source arc is not advertised as the receiver's unified plot.
    """
    if doc['scenario'] in BANK:
        units=[dict(scenario=doc['scenario'],prefix='',mapping={})]
    elif doc['scenario']=='joined' and row:
        units=row.get('options',{}).get('transfer',{}).get('units',[])
    else:return doc
    plots={};history=deepcopy(row['initial_world']['history']) if row else []
    doc['plot_prior_events']=[dict(id=e['id'],kind=e['frame']['kind']) for e in history]
    for event in doc['events']:
        unit=next((u for u in units if not u['prefix'] or event['kind'].startswith(u['prefix'])),None)
        if unit:
            scenario=unit['scenario'];kind=event['kind'][len(unit['prefix']):]
            info=_context(scenario,kind,unit['prefix'],unit['mapping'],doc['entities'],history)
            if info is not None:
                info.update(scope='completed_source_observation',status='observed',
                    observed_consequences=deepcopy(event['effects']),
                    native_dependencies=deepcopy(event['dependencies']),native_guard_reads_complete=event['guard_reads_complete'])
                event['plot']=info
                node=plots.setdefault(info['plot_id'],dict(source_scenario=scenario,
                    archetypes=info['archetypes'],local_pattern=info['local_pattern'],goal=info['goal'],
                    roles=info['roles'],stakes=info['stakes'],rationale=BANK[scenario]['rationale'],
                    scope='transferred_source_arc' if doc['scenario']=='joined' else 'source_story',
                    event_ids=[],links=[]))
                node['event_ids'].append(event['id'])
                node['links'] += [dict(link,target_event=event['id']) for link in info['incoming_links']]
                for tid in event['token_ids']:
                    # Event interpretation is shared context, not the POS/action of every word.
                    doc['tokens'][tid]['memory']['plot']=deepcopy(info)
        history.append(dict(id=event['id'],frame=event['frame']))
    doc['plots']=dict(schema='plot-annotations-v1',scope='completed_source_observation',nodes=plots)
    validate_plots(doc)
    return doc


def validate_plots(doc):
    if 'plots' not in doc:return True
    events={e['id']:e for e in doc['events']}
    available=set(events)|{e['id'] for e in doc.get('plot_prior_events',[])}
    for key,node in doc['plots']['nodes'].items():
        for ids in node['roles'].values():
            if not set(ids)<=doc['entities'].keys():raise ValueError('unbound plot role')
        for eid in node['event_ids']:
            if eid not in events or events[eid].get('plot',{}).get('plot_id')!=key:raise ValueError('invalid plot event')
        for link in node['links']:
            if link['source_event'] not in available or link['target_event'] not in events:raise ValueError('missing plot dependency')
            if link['source_event']>=link['target_event']:raise ValueError('future plot evidence')
    for event in doc['events']:
        if 'plot' not in event:continue
        if event['plot']['plot_id'] not in doc['plots']['nodes']:raise ValueError('unknown plot')
        for tid in event['token_ids']:
            if doc['tokens'][tid]['memory'].get('plot')!=event['plot']:raise ValueError('token plot mismatch')
    return True


def validate_bank():
    from .storytelling.runtime import setup
    from .storytelling.seed_worlds.catalog import SEED_SCENARIOS
    assert set(BANK)==set(SEED_SCENARIOS)
    for name,spec in BANK.items():
        p,w=setup(name)
        assert set(spec['events'])==set(p.KERNELS),name
        assert all(a['name'] in ARCHETYPES and a['fit']=='partial' for a in spec['archetypes'])
        assert all(set(ids)<=w.entities.keys() for ids in spec['roles'].values()),name
        assert all(e['stage']==ROLE_STAGE[e['role']] for e in spec['events'].values())
        for link in spec['links']:
            assert set(link['source'].split())<=p.KERNELS.keys(),(name,link)
            assert set(link['target'].split())<=p.KERNELS.keys(),(name,link)
    return True
