"""Provide ordered coarse event types; sample their native detailed realizations.

Names are human-readable labels. `offer` is an explicit capability from the
scale bank, not a free-text query or a fine-event identifier.
"""
from copy import deepcopy
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from .event_scale_bank import BANK
from .event_scales import set_mission
from .memory_transfer import receiving_world
from .scale_continuation import catalogue, run
from .story_memory import load_documents


EXAMPLES = {
    'transport_delivery_performance': [
        dict(name='Make transport usable', offer='transport_ready'),
        dict(name='Deliver something', offer='delivery'),
        dict(name='Put on a performance', offer='performance'),
    ],
    'route_drawing': [
        dict(name='Find a safe route', offer='safe_route'),
        dict(name='Make a drawing', offer='artwork'),
    ],
    'adapt_gift': [
        dict(name='Adapt something for its user', offer='accessible_design'),
        dict(name='Give a gift', offer='gift'),
    ],
}


def outline_world(events, *, world=None, seed=0, budget_seconds=None):
    """Compile coarse events to ordered, physically carried completion needs."""
    known={tag for s in BANK.values() for ep in s['episodes'] for tag in ep['offers']}
    if not events:raise ValueError('provide at least one coarse event')
    if budget_seconds is not None and budget_seconds<=0:raise ValueError('budget must be positive')
    w=(world or receiving_world()).clone()
    needs=[]
    for i,event in enumerate(events):
        if set(event)-{'name','offer'}:raise ValueError('coarse event accepts name and offer only')
        if event.get('offer') not in known:raise ValueError('unknown coarse event type: '+str(event.get('offer')))
        if not isinstance(event.get('name'),str) or not event['name'].strip():raise ValueError('coarse event needs a name')
        needs.append(dict(name=event['name'],offer=event['offer'],requires=[needs[-1]['name']] if i else []))
    now=w.narrative.get('clock',{}).get('seconds',0)
    set_mission(w,dict(name=' → '.join(e['name'] for e in events),carrier=w.hero,
        persistence='until_achieved_or_abandoned',deadline_seconds=None if budget_seconds is None else now+budget_seconds,
        needs=needs),seed)
    return w


def generate_outline(candidates,events,*,world=None,seed=0,budget_seconds=None,max_episodes=None):
    initial=outline_world(events,world=world,seed=seed,budget_seconds=budget_seconds)
    result=run(candidates,initial,seed=seed,max_episodes=max_episodes if max_episodes is not None else len(events)+2)
    result['provided_coarse_events']=deepcopy(events)
    return result


def experiment(memory,out,seeds):
    docs=load_documents(memory);pool=catalogue(docs)
    out.mkdir(parents=True,exist_ok=False)
    results=[]
    with gzip.open(out/'traces.jsonl.gz','wt') as sink:
        for name,events in EXAMPLES.items():
            for seed in seeds:
                r=generate_outline(pool,events,seed=seed)
                r['experiment']=name
                sink.write(json.dumps(r,separators=(',',':'))+'\n');sink.flush()
                results.append(r)
                print(name,seed,r['summary'],flush=True)
    summary=dict(source_documents=len(docs),source_worlds=len({c['scenario'] for c in pool}),
        candidate_prefixes=len(pool),runs=[dict(outline=r['experiment'],seed=r['seed'],reason=r['reason'],**r['summary']) for r in results])
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Coarse outlines expanded through the twenty-world pool','',
        'Input: Nia, Omar, a workshop, and an ordered list of coarse capability types. No props, fine events, '
        'source scenarios or bindings were supplied. No deadline was imposed, so a craft can take days. '
        'Each input is compiled to an ordered goal; existing lookahead ranks and samples detailed native programs. '
        'Names are display labels, not parsed natural language.','',
        f'Pool: {len(pool)} observed episode-ending prefixes from {len(docs)} intact annotated documents. '
        'Selection remains probabilistic; unrelated detours are possible. Completion means the native episodes '
        'supporting each coarse type executed in order on the receiving protagonist. It does not yet require '
        'adjacent coarse events to concern the same object.','',
        '| Outline | Seed | Completed | Selected sources | Resumed prefixes | Simulated time |',
        '|---|---:|---|---|---:|---:|']
    for r in results:
        s=r['summary'];lines.append(f"| {r['experiment']} | {r['seed']} | {s['success']} | {' → '.join(s['sources'])} | {s['resumed']} | {s['seconds']} s |")
    for r in results:
        lines += ['',f"## {r['experiment']}, seed {r['seed']}",'',
            '**Provided:** '+ ' → '.join(e['name']+' (`'+e['offer']+'`)' for e in r['provided_coarse_events']),
            '',r['story'],'','### Latent selection trace','',
            '| Selected episode | New fine events | Resume | New imports | Coarse needs advanced | Probability when chosen |',
            '|---|---:|---|---:|---|---:|']
        for d in r['decisions']:
            c=d['candidates'][d['selected']]
            if c.get('stop'):continue
            lines.append(f"| {c['scenario']}: {c['episode']} | {c['events']} | {c['resumed']} | {c['imports']} | {', '.join(c['progress']) or 'none'} | {c['probability']:.3f} |")
        lines+=['',f"Outcome: {r['reason']}; {r['summary']['needs_achieved']}/{len(r['provided_coarse_events'])} coarse needs met."]
    lines+=['','## Interpretation','',
        'These are raw generated outputs, without hand-written connective prose. Read the text alongside the '
        'latent trace: capability success is weaker than a single coherent plot. A route and a drawing can '
        'come from different settings; a gifted object need not be the previously adapted object. A resumed '
        'prefix retains its existing entities and executes only the remaining events. Source prefixes can '
        'also import prerequisite scenes, motives and supporting characters.','',
        'No new runtime kernels or language-model calls were added. The input adapter reuses the existing '
        'physical-carrier goal machinery and native guards. `traces.jsonl.gz` preserves candidate distributions, '
        'token attributes, complete replay specifications and the executed fine events.','']
    (out/'report.md').write_text('\n'.join(lines))
    root=Path(__file__).parent
    files=['coarse_outline.py','scale_continuation.py','event_scales.py','event_scale_bank.py','memory_transfer.py','storytelling/runtime.py']
    (out/'manifest.json').write_text(json.dumps(dict(source_sha256={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files}),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--memory',type=Path,default=Path('grammarworlds/runs/event_scales_20261108'))
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seeds',type=int,nargs='+',default=[7,19])
    a=p.parse_args();experiment(a.memory,a.out,a.seeds)
