"""Repeat only a known output-limit failure, with identical inputs and a larger cap."""
import argparse
import asyncio
import json
from pathlib import Path
from .. import judge
from ..authoring_trial import call
from .evaluate import validate_qa, report


async def recover(out, scenario):
    judge.verify_artifacts(out)
    original=out/scenario/'qa'
    raw=judge.read(original/'response.json')
    if raw.get('status')!='incomplete' or raw.get('incomplete_details',{}).get('reason')!='max_output_tokens':
        raise ValueError('Only a recorded, terminal output-limit failure can be repeated')
    target=out/scenario/'qa_output_recovery'
    if not target.exists():
        target.mkdir()
        body=judge.read(original/'request.json');body['max_output_tokens']=40000
        judge.save(target/'request.json',body);judge.save(target/'input.json',judge.read(original/'input.json'))
        entries=judge.read(out/'qa_followups.json') if (out/'qa_followups.json').exists() else {}
        entries[scenario]=dict(directory=target.name,
            sha256={n:judge.digest(target/n) for n in ('input.json','request.json')},
            note='Original response hit its output-token limit (terminal, no valid assessment). The identical stories, QA, rubric and schema were repeated with a 40,000-token cap; original request/response remain unchanged. This is not a new sample or a score-selected retry.')
        judge.save(out/'qa_followups.json',entries)
    response=await call(target)
    value=validate_qa(json.loads(judge.quality.final_text(response)),judge.read(target/'input.json'))
    judge.save(target/'result.json',dict(scenario=scenario,ok=True,assessment=value,
        response={k:response.get(k) for k in ['id','model','status','service_tier','usage']}))
    report(out)
    print(scenario,'output-limit recovery complete',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--scenario',required=True)
    a=p.parse_args();asyncio.run(recover(a.out,a.scenario))
