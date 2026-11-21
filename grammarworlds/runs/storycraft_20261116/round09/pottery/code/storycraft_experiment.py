"""Inspect authored-content revisions as sampled stories, state traces and QA."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import gzip,hashlib,json,re,shutil
from pathlib import Path

from .storytelling.runtime import generate,replay
from .storytelling.qa import questions
from .story_memory import annotate


def words(s):return len(re.findall(r"\w+(?:['’]\w+)*",s))


def run(out,scenarios,seeds,change,choices=None):
    out.mkdir(parents=True,exist_ok=False);root=Path(__file__).parent
    files=list((root/'storytelling/revisions').glob('*.py'))+[root/p for p in
        ['storytelling/runtime.py','storytelling/__main__.py','storytelling/attribute_grammar.py',
         'storytelling/surface.py','storytelling/qa.py','story_presentation.py','storycraft_experiment.py']]
    files+=list(root.glob('test_storycraft*.py'))
    manifest={}
    for f in files:
        name=f.relative_to(root);target=out/'code'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(f,target);manifest[str(name)]=hashlib.sha256(f.read_bytes()).hexdigest()
    summary=dict(change=change,started_at=datetime.now(timezone.utc).isoformat(),samples=[])
    report=['# '+out.name,'',change,'','These are actual classical-generator outputs. Baselines retain their original content; length differences are reported.','']
    with gzip.open(out/'samples.jsonl.gz','wt') as sink:
        for scenario in scenarios:
            for seed in seeds:
                for branch in choices or [None]:
                    options={'edition':'crafted',**({'choice':branch} if branch else {})}
                    row=generate(scenario,seed,**options);replay(row);doc=annotate(row);qa=questions(row,12)
                    assert row['final_world']['narrative']['storycraft']['completed']
                    for q in qa:
                        assert all(row['story'][e['start']:e['end']]==e['text'] for e in q['evidence'])
                    baseline=generate(scenario,seed,beat_budget=6,continuations='expanded')
                    memory=row['final_world']['narrative']['storycraft']
                    info=dict(scenario=scenario,seed=seed,conditioned_choice=branch,
                              words=words(row['story']),baseline_words=words(baseline['story']),
                              events=[h['name'] for h in memory['history']],
                              costs=[h['cost'] for h in memory['history'] if h['cost']],qa=len(qa))
                    summary['samples'].append(info)
                    sink.write(json.dumps(dict(row=row,annotations=doc,qa=qa,baseline=baseline,summary=info),separators=(',',':'))+'\n')
                    report += [f'## {scenario} / seed {seed} / '+str(branch or 'sampled'),'',row['presented_story'],'',
                               f"Body words: {info['words']}; old generator: {info['baseline_words']}.",'',
                               '**Executed events:** '+', '.join(info['events']),
                               '**Retained costs:** '+'; '.join(info['costs']),'',
                               '**Old generator, same seed**','',baseline['presented_story'],'']
                    for q in qa:report += ['Q: '+q['question'],'A: '+q['answer'],'']
    summary['finished_at']=datetime.now(timezone.utc).isoformat()
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'report.md').write_text('\n'.join(report)+'\n')
    print(json.dumps(dict(samples=len(summary['samples']),out=str(out))))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--scenarios',nargs='+',default=['pottery','music','greenhouse'])
    p.add_argument('--seeds',nargs='+',type=int,default=[7,19]);p.add_argument('--choices',nargs='+')
    p.add_argument('--change',required=True);a=p.parse_args();run(a.out,a.scenarios,a.seeds,a.change,a.choices)
