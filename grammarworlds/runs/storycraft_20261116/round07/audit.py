import json,math
from pathlib import Path
from collections import Counter
from grammarworlds.storytelling.runtime import generate,replay
from grammarworlds.storytelling.qa import questions
from grammarworlds.test_storycraft import BRANCHES
out=Path('grammarworlds/runs/storycraft_20261116/round07');out.mkdir(exist_ok=False)
summary={};samples=[]
for name in BRANCHES:
 counts=Counter();lengths=[];steps=choices=unknown=total=qa_count=0
 for seed in range(2000,2020):
  row=generate(name,seed,edition='crafted');assert replay(row)
  history=row['final_world']['narrative']['storycraft']['history']
  branch=next(h['name'] for h in history if h['name'] in BRANCHES[name]);counts[branch]+=1
  lengths.append(len(row['story'].split()));qa=questions(row,100);qa_count+=len(qa)
  for scene in row['trace']:
   for step in scene['word_trace']:
    steps+=1;choices+=len(step['choices'])>1
    assert math.isclose(sum(c['probability'] for c in step['annotated_choices']),1,abs_tol=1e-9)
   for a in scene['attribute_table'].values():
    total+=1;unknown+=a['pos']=='X'
  samples.append(dict(scenario=name,seed=seed,branch=branch,story=row['presented_story'],qa=qa))
 summary[name]=dict(samples=20,branches=dict(counts),words=dict(min=min(lengths),max=max(lengths),mean=sum(lengths)/20),
  token_steps=steps,steps_with_multiple_words=choices,multiple_word_fraction=choices/steps,
  unique_bundles=total,unresolved_pos_bundles=unknown,qa_pairs=qa_count)
for name in BRANCHES:
 row=generate(name,2007,edition='crafted',symbolic_heads=True)
 assert replay(row)
summary['symbolic_head_smoke']=dict(samples=3,replay=True)
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(out/'samples.json').write_text(json.dumps(samples,indent=2)+'\n')
print(json.dumps(summary,indent=2))
