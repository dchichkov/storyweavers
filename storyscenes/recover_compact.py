#!/usr/bin/env python3
"""Explicit bounded continuation of a returned, output-capped JSON draft.

Never retries an unknown paid outcome. The original prefix and accounting are
retained; Luna writes only its missing suffix, then the normal validator/repair
and prose pipeline resumes in a separate run directory.
"""
import argparse
import asyncio
import json
from pathlib import Path
import shutil

import compact_workshop as c
import factory as f
import workshop as w


async def main(args):
    from openai import AsyncOpenAI
    source=args.world.resolve();out=args.out.resolve();world=out/source.name
    if out.exists():raise ValueError('Recovery requires a new output directory; inspect existing paid stages before retrying')
    response=json.loads((source/'world_0.response.json').read_text())
    request=json.loads((source/'world_0.request.json').read_text())
    if response.get('status')!='incomplete' or (response.get('incomplete_details') or {}).get('reason')!='max_output_tokens':
        raise ValueError('Only a known output-cap truncation can use this continuation')
    if request['model']!='gpt-5.6-luna' or request.get('service_tier')!='flex':raise ValueError('Luna/Flex source required')
    prefix=f.quality.final_text(response)
    if not prefix.lstrip().startswith('{'):raise ValueError('No JSON prefix to continue')
    f.load_key(args.api_key_file)
    world.mkdir(parents=True)
    f.save(out/'settings.json',dict(protocol='storyscenes_compact_suffix_recovery',seed=20260907,count=1,
        model='gpt-5.6-luna',service_tier='flex',critic=False,campaign=str(args.campaign.resolve())))
    for folder,names in [('_runtime',c.RUNTIME),('_authoring',c.AUTHORING+['recover_compact.py'])]:
        dest=out/folder;dest.mkdir()
        for name in names:shutil.copyfile(c.ROOT/name,dest/name)
    brief=json.loads((source/'seed.json').read_text())
    f.save(world/'seed.json',brief)
    f.save(world/'continued_prefix.json',dict(source=str(source),response_sha256=f.digest(source/'world_0.response.json'),
        prefix=prefix,note='Original returned tokens, including the incomplete draft, remain in the parent comparison.'))
    budget=f.Budget(args.campaign.resolve()/'budget.json',15.0)
    wb=w.WorldBudget(budget,world,.15)
    prompt=(request['input'][-1]['content']+'\n\nThe response was cut off at its output limit. '
        'Return JSON {"suffix":"..."} containing ONLY the exact missing tail of the world JSON. '
        'Continue at the exact final character; do not repeat or rewrite the prefix. Finish the remaining scene opportunities, goal, outcomes and required fields. '
        'Maintain declared physical keys and at least three meaningful outcomes. No explanation or Markdown.\nEXACT PREFIX:\n'+prefix)
    schema=w.obj(dict(suffix={'type':'string'}))
    async with AsyncOpenAI(base_url='https://api.openai.com/v1',timeout=900,max_retries=0) as client:
        tail=await c.ask(client,wb,world,'world_suffix',c.json_request(prompt,schema=schema,tokens=1800,effort='low'))
        f.save(world/'suffix.json',tail)
        document=json.loads(prefix+tail['suffix'])
        contract=(out/'_authoring'/'AUTHORING_COMPACT.md').read_text()
        try:summary=await c.world_run(client,wb,world,brief,contract,prepared_world=document)
        except Exception as exc:
            summary=dict(world=world.name,ok=False,error=str(exc));f.save(world/'failure.json',summary)
    f.save(out/'summary.json',[summary])
    if summary['ok']:await f.evaluate(out,budget,1)
    return int(not summary['ok'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--world',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--campaign',type=Path,default=c.ROOT/'improvements/20260908')
    p.add_argument('--api-key-file',type=Path)
    raise SystemExit(asyncio.run(main(p.parse_args())))
