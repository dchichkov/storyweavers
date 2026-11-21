"""Paired prose, decision-probability interventions and compression ablation."""
import argparse
from collections import Counter
from dataclasses import asdict
import gzip,hashlib,json,math
from pathlib import Path
import re,shutil

from .storytelling.runtime import generate,replay,setup,build_forest
from .storytelling.revisions import pack
from .storytelling.qa import questions
from .story_memory import annotate
from .world import Frame


def words(s):return len(re.findall(r"\w+(?:['’]\w+)*",s))


def distribution(row,branch):
    p,w=setup(row['scenario'],row['seed'],**row['options'])
    for h in row['final_world']['history']:
        if h['frame']['kind']=='crafted_'+branch:break
        f=Frame(**{**h['frame'],'cause_ids':tuple(h['frame']['cause_ids'])})
        decision=p.select_narration(w,f,h['narrative_decision']['labels'])
        event=p.commit(w,f,h['sentence']);p.commit_narration(w,event,decision)
        for key in ('referents','speakers','narrated'):event[key]=h[key]
    before=w.to_dict();forest,_=build_forest(p,w,predict_attributes=True);mass={}
    for d in forest.derivations:mass[d.frame.kind.removeprefix('crafted_')]=mass.get(d.frame.kind.removeprefix('crafted_'),0)+d.probability
    assert w.to_dict()==before
    return mass


def run(out):
    out.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).parent
    files=list((root/'storytelling/revisions').glob('*.py'))+[root/p for p in
      ('storytelling/runtime.py','storytelling/event_lines.py','storytelling/attribute_grammar.py',
       'storytelling/__main__.py','decision_beats_experiment.py','test_decision_beats.py')]
    manifest={}
    for source in files:
        path=source.relative_to(root);target=out/'code'/path;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target);manifest[str(path)]=hashlib.sha256(source.read_bytes()).hexdigest()
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    summary=dict(distributions=[],random_samples={},compression={},checked_joint_steps=0)
    prose=['# Decision beats: actual paired samples','',
      'Both versions use the crafted edition and the same final branch. The new version also samples an appraisal and tracks visible narrative evidence. These are development examples, not blind quality scores.','']
    with gzip.open(out/'paired.jsonl.gz','wt') as sink:
        for name in ('pottery','music','greenhouse'):
            p=pack(name,decision_beats=True)
            branches=[e['name'] for e in p.events.values() if e['group'] and e['group']!='appraisal']
            appraisals=[e['name'] for e in p.events.values() if e.get('appraisal')]
            for appraisal in appraisals:
                row=generate(name,19,edition='crafted',decision_beats=True,appraisal=appraisal)
                assert replay(row);annotate(row)
                branch=next(h['name'] for h in row['final_world']['narrative']['storycraft']['history'] if h['name'] in branches)
                baseline=generate(name,19,edition='crafted',choice=branch)
                qa=questions(row,100);probs=distribution(row,branch)
                for q in qa:
                    for evidence in q['evidence']:assert row['story'][evidence['start']:evidence['end']]==evidence['text']
                summary['distributions'].append(dict(scenario=name,appraisal=appraisal,probabilities=probs,chosen=branch))
                sink.write(json.dumps(dict(row=row,baseline=baseline,qa=qa))+'\n')
                prose += [f'## {name}: {appraisal} → {branch}','',row['presented_story'],'',
                    f"Words: {words(row['story'])}; baseline: {words(baseline['story'])}.",'',
                    'Decision probabilities: '+', '.join(f'{k} {v:.1%}' for k,v in probs.items()),'',
                    '**Baseline with the same branch**','',baseline['presented_story'],'']
                for q in qa:prose+=['Q: '+q['question'],'A: '+q['answer'],'']
            counts=Counter();totals=[]
            for seed in range(5000,5020):
                r=generate(name,seed,edition='crafted',decision_beats=True)
                assert replay(r)
                m=r['final_world']['narrative']['storycraft']['decisions']
                assert m['appraisals'] and m['payoffs'] and m['observed_costs']
                b=next(h['name'] for h in r['final_world']['narrative']['storycraft']['history'] if h['name'] in branches)
                counts[b]+=1;totals.append(words(r['story']))
                for t in r['trace']:
                    for step in t['word_trace']:
                        assert math.isclose(sum(c['probability'] for c in step['annotated_choices']),1.,abs_tol=1e-9)
                        summary['checked_joint_steps']+=1
            summary['random_samples'][name]=dict(count=20,branches=dict(counts),mean_words=sum(totals)/len(totals))
    compression_cases=[('pottery','remake','appraise_design'),
                       ('music','choose_private','appraise_together'),
                       ('greenhouse','choose_share','appraise_both'),
                       ('greenhouse','choose_flower','appraise_show'),
                       ('greenhouse','choose_seedlings','appraise_risk')]
    for name,branch,appraisal in compression_cases:
        observed={};paired=[]
        for enabled in (False,True):
            spoken=0;total=0;lengths=[];states=[]
            for seed in range(6000,6040):
                r=generate(name,seed,edition='crafted',decision_beats=True,appraisal=appraisal,choice=branch,compression=enabled)
                assert replay(r)
                m=r['final_world']['narrative']['storycraft']['decisions']
                reminders=m['reminders'];spoken+=sum(x['selected']=='say' for x in reminders);total+=len(reminders)
                assert all(x['weights']['redundant'] for x in reminders)
                lengths.append(words(r['story']));states.append((r['final_world']['entities'],r['final_world']['flags']))
            observed[str(enabled)]=dict(samples=40,reminders=total,spoken=spoken,mean_words=sum(lengths)/len(lengths))
            paired.append(states)
        assert paired[0]==paired[1], 'compression changed physical outcomes'
        summary['compression'][name+':'+branch]=observed
    (out/'samples.md').write_text('\n'.join(prose)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    run(p.parse_args().out)
