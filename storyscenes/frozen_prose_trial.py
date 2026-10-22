#!/usr/bin/env python3
"""Measure prose authoring changes on exactly the same validated world mechanics.

This is a rendering ablation, not a claim of generating worlds at zero cost.
Full fresh-world trials are reported separately, including their failures.
"""
import argparse
import asyncio
import json
from pathlib import Path
import shutil

import compact_workshop as cw
import factory as f
import workshop as w


async def main(args):
    from openai import AsyncOpenAI
    source,out=args.source.resolve(),args.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    f.load_key(args.api_key_file)
    budget=f.Budget(args.campaign.resolve()/'budget.json',15)
    f.save(out/'settings.json',dict(protocol='storyscenes_frozen_prose_cached_v2',source=str(source),
                                  model='gpt-5.6-luna',service_tier='flex',world_authoring=False,
                                  prose_layout=args.prose_layout,prose_reasoning=args.prose_reasoning))
    for folder,names in (('_runtime',cw.RUNTIME),('_authoring',cw.AUTHORING+['frozen_prose_trial.py'])):
        dest=out/folder;dest.mkdir()
        for name in names:shutil.copyfile(cw.ROOT/name,dest/name)
    f.save(out/'runtime_provenance.json',{p.name:f.digest(p) for p in (out/'_runtime').glob('*.py')})
    contract=(out/'_authoring'/'AUTHORING_COMPACT.md').read_text()
    rows=[]
    async with AsyncOpenAI(base_url='https://api.openai.com/v1',timeout=900,max_retries=0) as client:
        for s in json.loads((source/'summary.json').read_text()):
            if not s['ok']:continue
            original=source/s['world'];world=out/s['world'];world.mkdir()
            doc=json.loads((original/'world.json').read_text())
            brief=json.loads((original/'seed.json').read_text())
            f.save(world/'inherited_mechanics.json',dict(source=str(original),sha256=f.digest(original/'world.json')))
            try:
                row=await cw.world_run(client,w.WorldBudget(budget,world,.15),world,brief,contract,
                                       prepared_world=doc,cost_profile='cached',
                                       prose_layout=args.prose_layout,prose_effort=args.prose_reasoning)
                # Generation must preserve all original pinned traces.
                expected=json.loads((original/'samples_with_trace.json').read_text())
                actual=await w.execute(world,[r['seed'] for r in expected],True)
                if [r['trace'] for r in actual] != [r['trace'] for r in expected]:
                    raise ValueError('Frozen-mechanics comparison changed traces')
            except Exception as exc:
                row=dict(world=world.name,ok=False,error=str(exc));f.save(world/'failure.json',row)
            rows.append(row)
    f.save(out/'summary.json',rows)
    if any(r['ok'] for r in rows):await f.evaluate(out,budget,1,cache_prompts=True)
    return int(any(not r['ok'] for r in rows))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=Path('storyscenes/runs/compact_algebra_v2'))
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--campaign',type=Path,default=Path('storyscenes/improvements/20260908'))
    p.add_argument('--api-key-file',type=Path,default=Path('.API_KEY'))
    p.add_argument('--prose-layout',choices=['full','factored'],default='full')
    p.add_argument('--prose-reasoning',choices=['low','medium'],default='low')
    raise SystemExit(asyncio.run(main(p.parse_args())))
