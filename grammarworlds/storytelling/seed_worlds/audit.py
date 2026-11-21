"""Export and audit the full twenty-seed collection and its reusable memory."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from .catalog import SEED_SCENARIOS, source_record
from .engine import NAMES, pack
from ..runtime import generate, replay, setup
from ..qa import questions
from ..audit import physical_checks
from ...story_memory import annotate, generate_retrieved
from ...story_memory_export import demonstration_world
from ...event_mapping import load_bank


def run(out, count=20, start=3000):
    if count<1:raise ValueError('positive count required')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    summary={}; samples=[]; sources=[]; interventions=0; imports=[]
    with gzip.open(out/'stories.memory.jsonl.gz','wt') as memory, gzip.open(out/'traces.jsonl.gz','wt') as traces:
        for name in (*SEED_SCENARIOS,'rescue','kite','key'):
            observed=set(); paths=set(); texts=set(); metrics=Counter(); selected=None
            source=source_record(name) if name in SEED_SCENARIOS else dict(scenario=name,kind='earlier_prototype')
            if name in SEED_SCENARIOS:sources.append(source)
            for seed in range(start,start+count):
                row=generate(name,seed,continuations='expanded',symbolic_heads=True)
                replay(row);doc=annotate(row);qa=questions(row)
                assert len(qa)>=5 and len({q['kind'] for q in qa})>=3
                assert len({p for s in row['scenes'] for p in s['speakers']})>=2
                assert all(row['story'][e['start']:e['end']]==e['text'] for q in qa for e in q['evidence'])
                supported=[e for e in doc['events'] if e['mapping_rules']]
                if name in NAMES:
                    assert any(e['token_ids'] for e in supported),name
                observed.update(e['kind'] for e in doc['events'])
                paths.add(tuple(e['kind'] for e in doc['events']));texts.add(row['story'])
                steps=[p for t in row['trace'] for p in t['word_trace']]
                metrics.update(stories=1,words=len(row['story'].split()),events=len(doc['events']),
                    mapped_events=len(supported),visible_mapped_events=sum(bool(e['token_ids']) for e in supported),
                    qa_pairs=len(qa),token_steps=len(steps),
                    choice_steps=sum(len(p['choices'])>1 for p in steps),
                    head_changes=sum(p.get('head_total_variation',0)>1e-10 for p in steps))
                memory.write(json.dumps(doc,separators=(',',':'))+'\n')
                traces.write(json.dumps(row,separators=(',',':'))+'\n')
                if seed==start:
                    p,w=setup(name,seed)
                    from ...world import Frame
                    for saved in row['final_world']['history']:
                        f=Frame(**{**saved['frame'],'cause_ids':tuple(saved['frame']['cause_ids'])})
                        assert set(f.cause_ids)<={fact.id for fact in w.facts_for_attention()}
                        interventions+=physical_checks(p,w,f)
                        p.commit(w,f,saved['sentence'])
                    # One independent receiving fixture per source, no operation
                    # filter or donor-event ID. This is reuse, not story planning.
                    receiver=demonstration_world();receiver.entities['book'].location='bench'
                    reused=generate_retrieved([doc],receiver,seed=7)
                    assert reused['status']=='complete'
                    imports.append(dict(scenario=name,story=reused['story'],
                        operations=[t['operation'] for t in reused['trace']],
                        source=reused['source']['memory_retrieval']['references']))
                if seed==start+min(7,count-1):
                    selected=dict(scenario=name,seed=seed,story=row['story'],qa=qa,
                        source=source,events=[e['kind'] for e in doc['events']])
                    (out/f'{name}.memory.json').write_text(json.dumps(doc,indent=2)+'\n')
            p,_=setup(name,start)
            missing=set(p.KERNELS)-observed
            if count>=20:assert not missing,(name,missing)
            assert metrics['visible_mapped_events']>0,name
            summary[name]=dict(metrics,event_kinds=len(p.KERNELS),observed_kinds=len(observed),
                missing_kinds=sorted(missing),distinct_paths=len(paths),distinct_texts=len(texts),
                mean_words=metrics['words']/count,choice_fraction=metrics['choice_steps']/metrics['token_steps'])
            samples.append(selected)
            print(name,json.dumps(summary[name]),flush=True)
    result=dict(worlds=summary,new_worlds=len(NAMES),seed_worlds=len(SEED_SCENARIOS),runtime_worlds=len(summary),
        generated=sum(s['stories'] for s in summary.values()),physical_interventions=interventions,
        mapping_rules=len(load_bank()['rules']),receiving_demonstrations=imports)
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'samples.json').write_text(json.dumps(samples,indent=2)+'\n')
    (out/'source_coverage.json').write_text(json.dumps(sources,indent=2)+'\n')
    lines=['# Twenty seed stories as executable grammarworlds','',
        f"{len(NAMES)} newly authored worlds plus music, greenhouse, library and pottery cover all twenty Luna seeds. The older rescue, kite and key prototypes remain available separately; runtime total is 23.", '',
        f"{result['generated']} generated stories, source replay and intact-token annotation checked. {interventions} negative physical interventions rejected. {result['mapping_rules']} mapping rules in the joined bank.", '',
        'These are compact adaptations, not reproductions of the full original prose. Every new world has a physical turn, dialogue, a visible ending and at least two local event alternatives. Typed phrase constructions produce distributions over annotated words. There is no model at runtime.', '',
        '| World | New | Event kinds covered | Paths | Distinct texts | Mean words | Word-choice steps |',
        '|---|---|---:|---:|---:|---:|---:|']
    for name,s in summary.items():
        lines.append(f"| {name} | {'yes' if name in NAMES else 'existing'} | {s['observed_kinds']}/{s['event_kinds']} | {s['distinct_paths']} | {s['distinct_texts']} | {s['mean_words']:.1f} | {100*s['choice_fraction']:.1f}% |")
    lines += ['', '## Unfiltered samples and grounded QA', '',
        f'Every example below uses the preselected seed {start+min(7,count-1)}. Full source texts are linked; each annotation document preserves the complete generated story and its token attributes.', '']
    for row in samples:
        name=row['scenario'];s=pack(name).spec if name in NAMES else None
        source_link=(f"[Original seed story]({row['source']['path']}) · " if 'path' in row['source'] else 'Earlier prototype · ')
        lines += ['### '+name,'',source_link+f"[Annotated generated story]({name}.memory.json)",'',row['story'],'']
        if s:lines += ['Preserved core: '+s['fidelity'],'','Local adaptations: '+' '.join(s['variants']),'']
        lines += ['Events: '+' → '.join(row['events']), '']
        for qa in row['qa']:lines += ['Q: '+qa['question'],'A: '+qa['answer'],'']
    lines += ['## Receiving-world samples', '',
        'Each source example independently supplies one sampled legal operation into the explicit craft fixture. No event IDs or operation filters are supplied. This demonstrates live reuse; it does not imply every compound event is portable.', '']
    for row in imports:lines += [f"- **{row['scenario']}**: {row['story']}"]
    lines += ['', '## Limits', '',
        'New worlds use authored dependency graphs and physical guards; they are not inferred automatically from raw text. Branches are local and bounded. The original stories are substantially compressed: travel, quantities, timing, social obligations and secondary actions are selectively simplified.',
        'The new mapping rules cover exact single-object fetching, placing and handoffs. Compound diagnosis, cooking, controlled experiments, access decisions and consent are annotated but are not transplanted as arbitrary state changes. Source guard removal is never a substitute for target capability checks.',
        'Some realizations still read as compact action summaries, with repeated names and little sensory detail. Mechanical coverage, replay, dialogue and QA gates do not establish literary quality. No new Luna score is claimed. Future work should extend reusable causal sequences and judge quality/diversity on these new worlds.', '']
    (out/'report.md').write_text('\n'.join(lines))
    root=Path(__file__).resolve().parents[2]
    paths=list(Path(__file__).parent.glob('*.py'))+[root/'storytelling/runtime.py',root/'storytelling/plans.py',root/'story_memory.py',root/'event_mapping.py']
    # root is grammarworlds; include every mapping used by the frozen export.
    paths+=list((root/'mapping_bank').glob('*.json'))
    (out/'manifest.json').write_text(json.dumps({str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--count',type=int,default=20)
    parser.add_argument('--start',type=int,default=3000)
    args=parser.parse_args();run(args.out,args.count,args.start)
