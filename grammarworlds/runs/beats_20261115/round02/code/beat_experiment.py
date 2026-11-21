"""Record one inspectable beat refinement round; never fabricate ten iterations."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil

from .storytelling.runtime import generate,replay
from .storytelling.qa import questions
from .story_memory import annotate

FILES=['beat_annotations.py','beat_generation.py','beat_experiment.py','storytelling/runtime.py',
       'storytelling/attribute_grammar.py','storytelling/event_lines.py','story_memory.py','plot_continuation.py',
       'beat_qa.py','storytelling/qa.py','test_beats.py','story_presentation.py','test_story_presentation.py']


def words(s):return len(re.findall(r"\w+(?:['’]\w+)*",s))


def run(out,seeds,change,scenarios=('pottery','repair','museum')):
    started=datetime.now(timezone.utc).isoformat()
    out.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).parent
    manifest={}
    files=sorted(set(FILES)|{p.name for p in root.glob('test_beat*.py')})
    for f in files:
        target=out/'code'/f;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/f,target)
        manifest[f]=hashlib.sha256((root/f).read_bytes()).hexdigest()
    summaries=[];lines=['# Beat refinement '+out.name,'',change,''];counts=Counter()
    with gzip.open(out/'traces.jsonl.gz','wt') as sink:
        for scenario in scenarios:
            # Fixed seed pool, chosen without looking at quality; match by length.
            baselines=[generate(scenario,seed,continuations='expanded') for seed in range(500,516)]
            for seed in seeds:
                for budget in (2,6):
                    r=generate(scenario,seed,beat_budget=budget,continuations='expanded')
                    replay(r);d=annotate(r);qa=questions(r,4)
                    memory=r['final_world']['narrative']['beats']
                    baseline=min(baselines,key=lambda b:abs(words(b['story'])-words(r['story'])))
                    chosen=[e['beat_decision']['selected'] for e in r['final_world']['history'] if e.get('beat_decision')]
                    counts.update(chosen)
                    framed=r['presentation'];start=framed['body_offset']
                    assert r['presented_story'][start:start+framed['body_length']]==r['story']
                    for q in qa:
                        assert all(r['story'][e['start']:e['end']]==e['text'] for e in q['evidence'])
                    info=dict(scenario=scenario,seed=seed,budget=budget,used=memory['used'],words=words(r['story']),
                        presentation_styles={k:framed[k]['styles'] for k in ('title','opening','closing')},
                        qa_count=len(qa),
                        baseline_seed=baseline['seed'],baseline_words=words(baseline['story']),selected=chosen,
                        annotated_beats=sum(len(e['beats']) for e in d['events']),
                        detail_links=sum(len(e['detail_links']) for e in d['events']))
                    summaries.append(info)
                    sink.write(json.dumps(dict(row=r,annotations=d,qa=qa,baseline=baseline,summary=info),separators=(',',':'))+'\n')
                    lines += [f'## {scenario}, seed {seed}, budget {budget}','',r['presented_story'],'',
                              'Choices: '+', '.join(chosen)+'.',
                              f"Words: {info['words']}; nearest fixed-pool baseline: {info['baseline_words']} (seed {baseline['seed']}).",'',
                              '**Nearest-length baseline**','',baseline['presented_story'],'']
                    for q in qa:lines += ['Q: '+q['question'],'A: '+q['answer'],'']
    (out/'report.md').write_text('\n'.join(lines))
    (out/'summary.json').write_text(json.dumps(dict(change=change,started_at=started,
        finished_at=datetime.now(timezone.utc).isoformat(),runs=summaries,choices=counts),indent=2)+'\n')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(runs=len(summaries),choices=counts)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seeds',nargs='+',type=int,default=[7,19]);p.add_argument('--change',required=True)
    p.add_argument('--scenarios',nargs='+',default=['pottery','repair','museum'])
    a=p.parse_args();run(a.out,a.seeds,a.change,a.scenarios)
