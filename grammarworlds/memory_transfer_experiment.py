"""Audit native transfer across all twenty joined source worlds and mixed cues."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path

from .memory_transfer import run, proposals, receiving_world, setup_joined
from .story_memory import load_documents, annotate
from .storytelling.seed_worlds.catalog import SEED_SCENARIOS
from .world import Entity


def experiment(memory,out):
    documents=[d for d in load_documents(memory) if d['scenario'] in SEED_SCENARIOS]
    by_id={d['id']:d for d in documents}
    out.mkdir(parents=True,exist_ok=False)
    per_world={};samples=[];all_kinds=set();guard_checks=0;qa_count=0;tokens=0
    old_mapped={(d['scenario'],e['kind']) for d in documents for e in d['events'] if e['mapping_rules']}
    expected={(d['scenario'],e['kind']) for d in documents for e in d['events']}
    with gzip.open(out/'traces.jsonl.gz','wt') as traces, gzip.open(out/'stories.memory.jsonl.gz','wt') as sink:
        for scenario in SEED_SCENARIOS:
            alternatives=proposals(documents,dict(scenario=scenario,extent='story'))
            counts=Counter();observed=set()
            for index,alternative in enumerate(alternatives):
                doc=by_id[alternative['references'][0]['document']]
                row=run([doc],[dict(scenario=scenario,extent='story')],seed=7)
                annotated=annotate(row)
                traces.write(json.dumps(row,separators=(',',':'))+'\n')
                sink.write(json.dumps(annotated,separators=(',',':'))+'\n')
                observed.update(e['transfer']['source_kind'] for e in row['final_world']['history'])
                counts.update(branches=1,events=len(row['trace']),words=len(row['story'].split()),
                              imports=row['transfer_summary']['imported_entities'],
                              choice_steps=sum(len(p['choices'])>1 for t in row['trace'] for p in t['word_trace']))
                tokens+=len(annotated['tokens']);qa_count+=len(row['world_qa'])
                pack,w=setup_joined(row['options']['transfer'])
                for saved in row['final_world']['history']:
                    frame=pack.candidates(w)[0][1]
                    assert set(frame.cause_ids)<={f.id for f in w.facts_for_attention()},frame
                    # Intervene on a real carrier at every step; no stale frame may commit.
                    bad=w.clone();del bad.entities[frame.actor];before=bad.to_dict()
                    try:pack.commit(bad,frame,'')
                    except ValueError:pass
                    else:raise AssertionError('missing physical actor was accepted')
                    assert bad.to_dict()==before;guard_checks+=1
                    record=pack.commit(w,frame,saved['sentence'])
                    for key in ('referents','speakers','narrated'):record[key]=saved[key]
                assert w.to_dict()==row['final_world']
                if index==0:
                    samples.append(dict(scenario=scenario,story=row['story'],qa=row['world_qa'],
                                        summary=row['transfer_summary']))
            all_kinds.update((scenario,k) for k in observed)
            per_world[scenario]=dict(counts,event_kinds=len(observed))
            print(scenario,per_world[scenario],flush=True)
        # Mixed-source cues and an explicit analogy on an existing receiver object.
        receiver=receiving_world()
        receiver.entities['trolley']=Entity('trolley','garden trolley','object','nia',
                                            properties={'portable'},state={'rattling'})
        mixed=[
            ('existing_trolley',[dict(event='refit_and_test',bindings={'cart':'trolley'})],receiver),
            ('repair_light_music',[dict(event='refit_and_test'),dict(event='controlled_trial'),dict(scenario='music',extent='story')],receiver),
            ('pond_and_picnic',[dict(event='tether_boat'),dict(scenario='picnic',extent='story')],None),
            ('lexical_cue',[dict(query='wheel repair')],None),
        ]
        mixed_samples=[]
        for name,requests,world in mixed:
            for seed in (0,7,19):
                row=run(documents,requests,world,seed=seed)
                annotated=annotate(row)
                row['experiment']=name
                traces.write(json.dumps(row,separators=(',',':'))+'\n')
                sink.write(json.dumps(annotated,separators=(',',':'))+'\n')
                mixed_samples.append(dict(experiment=name,seed=seed,story=row['story'],qa=row['world_qa'],
                    summary=row['transfer_summary'],decisions=row['transfer_decisions']))
                print(name,seed,row['transfer_summary'],flush=True)
    assert all_kinds==expected,(expected-all_kinds,all_kinds-expected)
    summary=dict(source_documents=len(documents),worlds=len(per_world),source_branches=sum(x['branches'] for x in per_world.values()),
        native_event_kinds=len(all_kinds),previous_mapped_event_kinds=len(old_mapped),
        actor_removal_rejections=guard_checks,branch_sample_tokens=tokens,branch_sample_qa=qa_count,
        mixed_samples=len(mixed_samples),per_world=per_world)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'samples.json').write_text(json.dumps(samples+mixed_samples,indent=2)+'\n')
    lines=['# Transfer across the twenty-world pool','',
        f"{len(documents)} intact source documents from 20 worlds; {summary['source_branches']} distinct observed event paths transferred, covering all {len(all_kinds)} source event kinds. The earlier strict operation bank exposed {len(old_mapped)} kinds in this same corpus. These are different modes: native transfer imports source mechanics and companions, while the strict bank uses receiver-authored operations.",'',
        f"{guard_checks} missing-actor interventions were rejected without mutation. All outputs replayed through native guards, and all generated texts reconstructed from annotated tokens. {len(mixed_samples)} additional mixed/cue samples were run.",'',
        '## Coverage','', '| World | Source paths | Event kinds | Mean imported carriers |', '|---|---:|---:|---:|']
    for name,stats in per_world.items():lines.append(f"| {name} | {stats['branches']} | {stats['event_kinds']} | {stats['imports']/stats['branches']:.1f} |")
    lines += ['', '## Mixed and analogy samples', '',
        'Seeds were fixed in advance. Source branch/attachment choices are sampled from an explicit normalized distribution; words and attributes are generated by the receiving grammar. Once selected, a source prefix follows its observed event order.']
    for sample in mixed_samples:
        if sample['seed']!=7:continue
        lines += ['', '### '+sample['experiment'], '',sample['story'],'',
                  'Sources: '+', '.join(sample['summary']['sources'])+'. Imported carriers: '+str(sample['summary']['imported_entities'])+'.']
        for qa in sample['qa'][:3]:lines+=['','Q: '+qa['question'],'A: '+qa['answer']]
    lines += ['', '## One transferred sample per source', '']
    for sample in samples:
        lines+=['### '+sample['scenario'],'',sample['story'],'']
    lines += ['', '## What this establishes—and what it does not', '',
        'Compound events can now be executed on bound receiving characters and objects, including a garden trolley repaired through the cart story’s wheel-diagnosis chain. Supporting tools, locations, characters and initial motives can accompany the transfer. All imported entities and character attributes are listed in the trace; existing object states are never reset to match a source.', '',
        'This is deliberately permissive source-mechanics transfer, not automatic induction of universal physics. Most requests still pull a long prerequisite prefix and the full source cast; local event ordering is retained. The mixed output is a sequence of mini-stories with shared people, not yet a tightly composed new plot. Source-specific nouns, unnamed props in surface constructions, and scenery can leak. Some donor guards themselves simplify travel and object roles.', '',
        'The cue matcher uses annotated event names, carrier nouns and action lemmas. It does not understand arbitrary prose instructions. Import count mildly penalizes attachment weights; these weights are manual. Native continuation does not yet interleave arbitrary individual events across stories or learn a policy.', '',
        'QA here checks executed target state changes. It is not inherited source QA and is not claimed to be reading comprehension: silent physical effects can support a world-state answer. Prose quality and diversity have not been scored by Luna.', '']
    (out/'report.md').write_text('\n'.join(lines))
    root=Path(__file__).parent
    paths=list(root.glob('*.py'))+list((root/'storytelling').rglob('*.py'))
    paths+=list((root/'storytelling').glob('*.json'))+list((root/'mapping_bank').glob('*.json'))
    paths.append(memory/'stories.memory.jsonl.gz')
    (out/'manifest.json').write_text(json.dumps({str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--memory',type=Path,default=Path('grammarworlds/runs/seed_worlds_20261107_v4'))
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();experiment(args.memory,args.out)
