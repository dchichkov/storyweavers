import asyncio,json,random
from pathlib import Path
from grammarworlds import judge
from grammarworlds.authoring_trial import call
from grammarworlds.storytelling.evaluate import qa_request,validate_qa,report
out=Path('grammarworlds/runs/ten_rounds_20261103/round02/eval')
d=out/'rescue/qa_followup'
if not d.exists():
 d.mkdir()
 pool=judge.read(out/'rescue/pool.json')
 excluded={s['source_index'] for s in judge.read(out/'rescue/input.json')['stories']}
 indices=random.Random(778).sample([i for i in range(len(pool)) if i not in excluded],6)
 stories=[]
 for i in indices:
  row=pool[i];sid=f's{i:06d}'
  stories.append(dict(id=sid,story=row['story'],qa=[dict(id=f'{sid}:q{j}',question=q['question'],answer=q['answer'],evidence=[e['text'] for e in q['evidence']]) for j,q in enumerate(row['qa'])]))
 item=dict(stories=stories);judge.save(d/'input.json',item);judge.save(d/'request.json',qa_request(item))
 judge.save(out/'qa_followups.json',{'rescue':dict(directory='qa_followup',seed=778,indices=indices,
  note='The original 12-story QA call timed out with an uncertain server outcome and was not resent. This diagnostic uses six uniformly selected, previously unselected stories from the same frozen pool (seed 778). Prose still uses the original 12-story sample; QA uses these six stories.',
  sha256={name:judge.digest(d/name) for name in ['input.json','request.json']})})
async def run():
 raw=await call(d)
 result=dict(scenario='rescue',ok=True,assessment=validate_qa(json.loads(judge.quality.final_text(raw)),judge.read(d/'input.json')),
  response={k:raw.get(k) for k in ['id','model','status','service_tier','usage']})
 judge.save(d/'result.json',result);print('follow-up complete',flush=True);report(out)
if __name__=='__main__':asyncio.run(run())
