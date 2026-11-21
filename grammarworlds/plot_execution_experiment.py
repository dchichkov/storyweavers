"""Audit stage-wise plot generation, source selection and rejected false payoffs."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from .plot_continuation import catalogue,run
from .story_memory import load_documents,annotate
from .coarse_outline import EXAMPLES,generate_outline
from .scale_continuation import catalogue as coarse_catalogue


def experiment(memory,out,seeds):
    docs=load_documents(memory);pool=catalogue(docs)
    out.mkdir(parents=True,exist_ok=False);results=[];baseline=[]
    with gzip.open(out/'traces.jsonl.gz','wt') as sink:
        for plan in ('adapt_gift','changed_approach'):
            for seed in seeds:
                r=run(pool,plan,seed=seed)
                for row in r['rows']:annotate(row)
                results.append(r);sink.write(json.dumps(r,separators=(',',':'))+'\n');sink.flush()
                print(plan,seed,r['summary'],flush=True)
        # Same source pool, two original coarse-outline seeds. Capability labels
        # alone can report success while changing the object between the steps.
        coarse=coarse_catalogue(docs)
        for seed in seeds[:2]:
            r=generate_outline(coarse,EXAMPLES['adapt_gift'],seed=seed)
            objects=[]
            for need in r['mission']['needs']:
                key=need['evidence'][0] if need['evidence'] else None
                c=r['rows'][-1]['final_world']['narrative']['commitments'].get(key,{}) if r['rows'] else {}
                from .plot_execution import source_bindings
                objects.append(source_bindings(c['source'],c['mapping']).get('object') if c else None)
            r['experiment']='coarse_labels_baseline';r['bound_objects_at_milestones']=objects
            r['same_object_at_milestones']=bool(objects) and None not in objects and len(set(objects))==1
            baseline.append(r);sink.write(json.dumps(r,separators=(',',':'))+'\n');sink.flush()
            print('baseline',seed,r['summary'],objects,flush=True)
    summary=dict(source_documents=len(docs),source_worlds=len({c['scenario'] for c in pool}),
        native_branches=len(pool),runs=[dict(plan=r['plan'],seed=r['seed'],reason=r['reason'],**r['summary']) for r in results],
        baseline=[dict(seed=r['seed'],label_success=r['summary']['success'],same_object=r['same_object_at_milestones'],
                       objects=r['bound_objects_at_milestones'],sources=r['summary']['sources']) for r in baseline])
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Executable plot stages and shared physical bindings','',
        f"Pool: {len(docs)} source documents from {summary['source_worlds']} worlds; {len(pool)} distinct native source branches. "
        'Inputs contain a plot contract, Nia, Omar and a workshop. No source scenario, object, recipient or fine-event sequence is specified.','',
        'The planner previews native source suffixes, rejects incompatible bindings and unfinished plot trajectories, '
        'then samples a normalized distribution over prefixes ending at the next plot milestone. '
        'Completed stages and obligations are updated from actual execution. It preserves the same object (and gift recipient) '
        'through all stages. Each chosen prefix is generated through the existing annotated-token grammar.','',
        '| Plot | Seed | Complete, narrated, on time | Stage sources | Resumes | Simulated seconds |',
        '|---|---:|---|---|---:|---:|']
    for r in results:
        s=r['summary'];lines.append(f"| {r['plan']} | {r['seed']} | {s['success']} | {' → '.join(s['sources'])} | {s['resumed']} | {s['seconds']} |")
    lines+=['','## Capability-only comparison','',
        'This small matched-pool comparison checks identity, not literary quality. The old coarse planner only requires '
        'capability labels in order. Its object IDs below are diagnostic readings of the selected source targets, not constraints it enforced.','',
        '| Seed | Coarse labels complete | Same object | Selected sources |',
        '|---|---|---|---|']
    for r in baseline:
        lines.append(f"| {r['seed']} | {r['summary']['success']} | {r['same_object_at_milestones']} | {' → '.join(r['summary']['sources'])} |")
    for r in results:
        lines+=['',f"## {r['plan']}, seed {r['seed']}",'',r['story'],'',
            f"Bindings: `{json.dumps(r['plot']['bindings'],sort_keys=True)}`.",'',
            '| Stage | Native event | Narrative evidence | Narrated |',
            '|---|---|---|---|']
        for s in r['plot']['stages']:
            e=s['evidence'];n=r['plot']['narration_requirements'].get(s['name'],{})
            links=', '.join(l['relation']+' #'+str(l['source_event']) for l in e['incoming_links']) if e else ''
            lines.append(f"| {s['name']} | {e['source_kind'] if e else 'unresolved'} | {links or '—'} | {n.get('status','pending')} |")
        lines+=['',f"Open obligations: {r['summary']['open_obligations']}. Missing narration: {r['summary']['missing_narration']}."]
    lines+=['','## Limits','',
        '- The implementation executes two local plot structures, not all nine archetypes. Existing source annotations supply the available readings.',
        '- Full native suffix lookahead strongly favors coherent reuse of one authored story. This is staged retrieval and execution, not evidence of inventing novel cross-source plots.',
        '- Setup/payoff obligations and same-entity checks are enforced. Discovery links are authored narrative relations over actual events; they are not an automatically inferred causal theory.',
        '- Character knowledge records only new native `knows_*`/`understands_*` states. Reader exposure records narrated events and typed referents. There is no general false-belief, hidden-motive or reader-comprehension model.',
        '- Narration gates require visible text with relevant typed entities for each plot milestone. This catches silent or unrelated endings, but does not measure elegance or guarantee explicit causal connective wording.',
        '- No added connective prose, runtime LLM or learned weights. The stronger coherence here comes primarily from preserving authored relationships and rejecting incompatible continuations.',
        '- All durations remain authored estimates. No deadline was imposed in these samples; pottery can take days.','']
    (out/'report.md').write_text('\n'.join(lines))
    root=Path(__file__).parent
    files=['plot_execution.py','plot_continuation.py','plot_execution_experiment.py','event_scales.py',
           'plot_annotations.py','storytelling/runtime.py','storytelling/event_lines.py']
    (out/'manifest.json').write_text(json.dumps(dict(input=str(memory),source_sha256={f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files}),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--memory',type=Path,default=Path('grammarworlds/runs/plot_annotations_20261108'))
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seeds',type=int,nargs='+',default=[7,19,42,103])
    a=p.parse_args();experiment(a.memory,a.out,a.seeds)
