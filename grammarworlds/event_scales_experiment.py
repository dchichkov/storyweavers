"""Export timed annotations and compare coarse goal-guided vs plain sampling."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from .event_scale_bank import BANK
from .event_scales import validate_bank
from .scale_continuation import catalogue, run
from .story_memory import annotate
from .storytelling.runtime import generate, replay


def experiment(out,seeds):
    out.mkdir(parents=True,exist_ok=False);validate_bank();docs=[];sources=[]
    with gzip.open(out/'stories.memory.jsonl.gz','wt') as sink:
        for scenario in BANK:
            for seed in (3007,3014):
                row=generate(scenario,seed,multiscale=True,continuations='expanded');replay(row)
                doc=annotate(row);docs.append(doc);sink.write(json.dumps(doc,separators=(',',':'))+'\n')
                sources.append(dict(scenario=scenario,seed=seed,seconds=row['final_world']['narrative']['clock']['seconds'],
                                    events=len(row['trace']),story=row['story']))
    pool=catalogue(docs);results=[];examples={}
    print('source documents',len(docs),'candidate prefixes',len(pool),flush=True)
    with gzip.open(out/'continuations.jsonl.gz','wt') as sink:
        for seed in seeds:
            for policy in ('plain','contextual'):
                result=run(pool,seed=seed,policy=policy,max_episodes=4)
                results.append(dict(seed=seed,policy=policy,reason=result['reason'],**result['summary']))
                sink.write(json.dumps(result,separators=(',',':'))+'\n');sink.flush()
                examples.setdefault(policy,result)
                print(policy,seed,result['summary'],flush=True)
    metrics={}
    for policy in ('plain','contextual'):
        rows=[r for r in results if r['policy']==policy]
        metrics[policy]=dict(runs=len(rows),successes=sum(r['success'] for r in rows),
            mean_needs_achieved=sum(r['needs_achieved'] for r in rows)/len(rows),
            mean_episodes=sum(r['episodes'] for r in rows)/len(rows),
            deadline_overruns=sum(r['seconds']>3600 for r in rows),
            zero_immediate_progress_episodes=sum(r['irrelevant'] for r in rows),
            distinct_source_orders=len({tuple(r['sources']) for r in rows}))
    summary=dict(worlds=len(BANK),authored_episodes=sum(len(s['episodes']) for s in BANK.values()),
        fine_event_kinds=sum(len(e['events']) for s in BANK.values() for e in s['episodes']),
        source_documents=len(docs),candidate_prefixes=len(pool),seeds=seeds,metrics=metrics,runs=results)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Multiple event scales and world time','',
        f'{len(BANK)} worlds; 60 authored episodes; 249 fine-event kinds. Two annotated samples per world. '
        f'These yield {len(pool)} observed episode-ending prefixes. Source text is preserved in annotated documents.','',
        '## Matched receiver experiment','',
        'Nia has a rattling garden trolley and an uncontrolled shadow. The explicit goal requires a repaired trolley, '
        'a small controlled shadow, and a performance started after those preparations. Deadline: one simulated hour. '
        'No source scenarios or event sequence are supplied. Both policies use the same candidate pool, native guards, '
        'attachment variants and four-episode limit. Plain samples feasible alternatives uniformly; contextual uses '
        'physical goal progress, closure, duration fit and import/event cost. This is a small designed fixture, not a held-out literary-quality evaluation.','',
        '| Policy | Goal met on time | Mean needs met / 3 | Mean episodes | Deadline overruns | Episodes with no immediate goal progress |',
        '|---|---:|---:|---:|---:|---:|']
    for policy,m in metrics.items():
        lines.append(f"| {policy} | {m['successes']}/{m['runs']} | {m['mean_needs_achieved']:.2f} | {m['mean_episodes']:.2f} | {m['deadline_overruns']} | {m['zero_immediate_progress_episodes']} |")
    lines+=['','## Generated examples','']
    for policy,r in examples.items():
        lines+=[f"### {policy}, seed {r['seed']}",'',r['story'],'',
                f"Result: {r['reason']}; {r['clock']['seconds']} seconds; {r['summary']['needs_achieved']}/3 needs achieved.",'',
                '| Selected source | Coarse episode | New fine events | Simulated interval (seconds) | Needs advanced |',
                '|---|---|---:|---:|---|']
        for decision,row in zip((d for d in r['decisions'] if not d['candidates'][d['selected']].get('stop')),r['rows']):
            c=decision['candidates'][decision['selected']]
            lines.append(f"| {c['scenario']} | {c['episode']} | {c['events']} | {decision['start_seconds']}–{row['final_world']['narrative']['clock']['seconds']} | {', '.join(c['progress']) or 'none'} |")
        lines+=['']
    lines+=['## Boundaries and remaining defects','',
        '- Coarse goals are authored predicate graphs. There is no natural-language goal parser or learned planning policy.',
        '- Episode memberships are authored; entity-specific chains are derived participant threads, not independent causal subplans.',
        '- Time is sampled from estimated bands (5 seconds, 1 minute, 1 hour, 1 day). Events execute serially; there is no overlap scheduler. Parent duration estimates are descriptive and are not added again.',
        '- Token candidates contain current commitments and duration distributions before sampling. Retrospective source observations are labeled separately.',
        '- Native source prefixes may bring prerequisite events, props and motives. Compatible prefixes can resume on existing carriers without replaying earlier events.',
        '- The prose still resembles linked mini-stories; the shared demonstration goal is in the structured fixture and is not consistently expressed as one opening/ending in the text. This is a long-range selection improvement, not evidence of improved literary quality.',
        '- Some partial source commitments remain open when the receiving goal finishes. There is no Luna evaluation in this experiment.','',
        'Full candidate probabilities, selected token distributions, timings, native events and replay specifications: `continuations.jsonl.gz`. '
        'Intact source annotations: `stories.memory.jsonl.gz`.','']
    (out/'report.md').write_text('\n'.join(lines))
    files=['event_scales.py','event_scale_bank.py','scale_continuation.py','event_scales_experiment.py',
           'memory_transfer.py','story_memory.py','world.py','storytelling/runtime.py','storytelling/attribute_sampler.py']
    root=Path(__file__).parent
    (out/'manifest.json').write_text(json.dumps(dict(schema='event-scales-experiment-v1',
        source_sha256={str(root/f):hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files}),indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seeds',type=int,nargs='+',default=[7,19,42,103])
    a=p.parse_args();experiment(a.out,a.seeds)
