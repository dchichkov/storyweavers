#!/usr/bin/env python3
"""Run ten mixed-seed worlds using the unchanged compact engine and 3-story judge."""
import argparse
import asyncio
import json
from pathlib import Path
import shutil

import world_batch as batch
import compact_workshop as cw
import factory as f
import workshop as w
from seed_mixer import briefs_for

ROOT = Path(__file__).resolve().parent


def prepare(args):
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    settings = dict(protocol='mixed_trial_v1', seed=args.seed, target_worlds=10,
        max_attempts_per_slot=3, stories_per_world=3, selection_seed=777,
        qa_seed=777, qa_limit=6, qa_pairs=3, cost_profile='cache-only',
        world_reasoning='medium', prose_reasoning='low', service_tier='flex',
        author_model='gpt-5.6-luna', judge_model='gpt-5.6-terra',
        world_budget=.15, campaign=str(args.campaign.resolve()),
        replacement='Each of ten slots tries indices slot, slot+10, slot+20; replace failed authors only, never low grades.')
    path = out/'settings.json'
    if path.exists() and json.loads(path.read_text()) != settings:
        raise ValueError('Settings changed; use a new run')
    sources = sorted(set(cw.RUNTIME + cw.AUTHORING + batch.EXTRA_SOURCES + ['mixed_trial.py']))
    hashes = {name: f.digest(ROOT/name) for name in sources}
    if (out/'source_hashes.json').exists() and json.loads((out/'source_hashes.json').read_text()) != hashes:
        raise ValueError('Frozen source changed; use a new run')
    for folder, names in [('_runtime',cw.RUNTIME), ('_authoring',cw.AUTHORING),
                          ('_evaluation',batch.EXTRA_SOURCES), ('_scheduling',['mixed_trial.py'])]:
        for name in names:
            dest=out/folder/name; dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists() and f.digest(dest)!=hashes[name]: raise ValueError('Snapshot differs')
            if not dest.exists(): shutil.copyfile(ROOT/name,dest)
    briefs=briefs_for(args.seed,30)
    if (out/'briefs.json').exists() and json.loads((out/'briefs.json').read_text())!=briefs:
        raise ValueError('Briefs changed')
    f.save(path,settings); f.save(out/'source_hashes.json',hashes); f.save(out/'briefs.json',briefs)
    return out,briefs


async def run(args):
    from openai import AsyncOpenAI
    out,briefs=prepare(args)
    if args.prepare_only: return 0
    ledger=f.Budget(args.campaign.resolve()/'budget.json',15)
    f.load_key(args.api_key_file)
    contract=(out/'_authoring'/'AUTHORING_COMPACT.md').read_text()
    sem=asyncio.Semaphore(3)
    async with AsyncOpenAI(base_url='https://api.openai.com/v1',timeout=900,max_retries=0) as client:
        async def slot_run(slot):
            for index in (slot,slot+10,slot+20):
                brief=briefs[index]; world=out/brief['world_id']
                if (out/'STOP').exists(): return
                if (world/'failure.json').exists(): continue
                async with sem:
                    if (out/'STOP').exists(): return
                    try:
                        await cw.world_run(client,w.WorldBudget(ledger,world,.15),world,brief,contract,cost_profile='cache-only')
                    except Exception as exc:
                        world.mkdir(exist_ok=True)
                        f.save(world/'failure.json',dict(world=world.name,ok=False,error=str(exc),
                            paid_stage_stopped=isinstance(exc,cw.PaidStageStopped)))
                        print(f'{world.name}: FAILED {exc}',flush=True)
                        batch.report(out,ledger)
                        continue
                    item,rows=await batch.selected_samples(world)
                    budget=w.WorldBudget(ledger,world,.40)
                    await batch.judge(client,budget,world,'story',item,f.quality.request_body(item,cache_prompts=True))
                    qa_rows=[r for r in rows if r['conversations']]
                    if qa_rows:
                        body=batch.cq.request_body(qa_rows)
                        counts=[len(r['conversations']) for r in qa_rows]
                        body['text']['format']['schema']['properties']['stories']['items']['properties']['conversations'].update(
                            minItems=min(counts),maxItems=max(counts))
                        await batch.judge(client,budget,world,'qa',qa_rows,body)
                    report=batch.report(out,ledger)
                    print(f'PROGRESS {report["accepted_worlds"]}/10 worlds; {report["story_quality"]["rated_stories"]}/30 story grades; '
                          f'${report["cost"]["usd_high"]:.4f} returned-usage cost',flush=True)
                    return
        await asyncio.gather(*(slot_run(slot) for slot in range(10)))
    report=batch.report(out,ledger)
    return int(report['accepted_worlds']!=10 or report['story_quality']['rated_stories']!=30 or bool(report['failed_judges']))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=20260909)
    parser.add_argument('--campaign',type=Path,default=ROOT/'improvements/20260908')
    parser.add_argument('--api-key-file',type=Path)
    parser.add_argument('--prepare-only',action='store_true')
    raise SystemExit(asyncio.run(run(parser.parse_args())))
