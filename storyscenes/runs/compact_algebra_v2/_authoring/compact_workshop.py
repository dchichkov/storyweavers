#!/usr/bin/env python3
"""Luna/Flex: executable algebra -> validated traces -> named prose text slots.

No generated Python, duplicate natural-language plan, or stronger-model repair.
Uses the existing spending ledger, frozen workers and unchanged set-quality judge.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import random
import shutil

import algebra as a
import compact_prose as cp
import factory as f
import workshop as w
from runtime import solve
from planning import signatures
from quality_checks import validate_outcomes

ROOT = Path(__file__).resolve().parent
RUNTIME = w.SNAPSHOT_FILES + ['algebra.py']
AUTHORING = ['compact_workshop.py','compact_prose.py','algebra.py','factory.py','workshop.py',
             'quality_checks.py','AUTHORING_COMPACT.md']


class PaidStageStopped(RuntimeError):
    pass


async def ask(client, budget, world, stage, body):
    try:
        raw = await w.artifact(client,budget,world,stage,body)
    except Exception as exc:
        # A transport error, STOP, exhausted reservation or incomplete response
        # must not be disguised as a semantic failure followed by another call.
        raise PaidStageStopped(f'{stage}: {exc}') from exc
    return json.loads(raw)


def json_request(prompt, *, schema=None, tokens=5500, effort='medium'):
    body = w.request(prompt, 'gpt-5.6-luna', effort, schema, tokens)
    if schema is None:
        # Dynamic entity/state/instance maps are locally validated. Prose uses a
        # strict schema whose exact IDs are derived from the compiled world.
        body['text'] = {'format':{'type':'json_object'}}
    return body


def validate_mechanics(document):
    specs, traces = [], []
    # Test every finite initial configuration independently of random coverage.
    for choices in a.configurations(document):
        spec = a.build(document, choices=choices)
        specs.append(spec)
        for search_seed in range(4):
            try:
                traces.append(solve(spec, search_seed))
            except Exception as exc:
                raise ValueError(f'Initial configuration {choices}: {exc}') from exc
    rows = []
    for seed in w.POOL_SEEDS:
        spec = a.build(document, seed)
        trace = solve(spec, seed)
        specs.append(spec)
        rows.append(dict(seed=seed,trace=trace,diagnostics=dict(outcome_writes=sorted(
            {e.key for s in spec.scenes for e in s.effects if e.key in spec.outcome_keys}))))
    validate_outcomes(rows)
    stats = w.mechanical_stats(rows)
    if min(stats['outcomes'], stats['premises'], stats['scene_sets']) < 3:
        raise ValueError(f'Need at least three meaningful initial problems, consequences and scene sets: {stats}')
    if stats['events_range'][0] < 3:
        raise ValueError('Some goals finish before a developed causal story (fewer than three events)')
    traces += [r['trace'] for r in rows]
    return stats, cp.scaffold(traces, specs), traces


async def world_run(client, budget, world, brief, contract):
    world.mkdir(exist_ok=True)
    f.save(world/'seed.json',brief)
    if (world/'summary.json').exists():
        summary = json.loads((world/'summary.json').read_text())
        for name in ('simulation','generator'):
            if f.digest(world/f'{name}.py') != summary[f'{name}_sha256']:
                raise ValueError('Completed artifact changed; choose a new run')
        return summary
    base = contract + '\n\nDESIGN SEED:\n' + json.dumps(brief)
    document, feedback = None, ''
    for attempt in range(4):
        try:
            if attempt == 0:
                prompt = base + '\n\nReturn the executable world JSON only. The same object is both the plan and the simulator definition. Do not include Python or a second prose plan.'
                document = await ask(client,budget,world,'world_0',json_request(prompt))
            else:
                prompt = base + '\n\nRepair only named components with JSON {edits:[{section,id,value}]}. '
                prompt += 'Allowed sections: entities, kernels, compose, vary, rules (one named entry); goal, premises, outcomes (id equals section). '
                prompt += 'Maximum eight edits. Preserve valid alternatives. Do not remove an intended outcome merely to pass the validator.\nWORLD:\n'+json.dumps(document)+'\nFAILURE:\n'+feedback
                patch = await ask(client,budget,world,f'world_patch_{attempt}',json_request(prompt,tokens=2500,effort='low'))
                f.save(world/f'world_patch_{attempt}.json',patch)
                document = a.patch_world(document,patch)
            f.save(world/f'world_{attempt}.json',document)
            stats,skeleton,traces = validate_mechanics(document)
            f.save(world/'world.json',document)
            (world/'simulation.py').write_text(a.compile_source(document))
            previews = await w.execute(world,[0,1,2])
            # Cross-check author-side validation against the frozen worker.
            for row in previews:
                if row['trace'] != solve(a.build(document,row['seed']),row['seed']):
                    raise ValueError('Frozen runtime differs from author-side compiler')
            f.save(world/'simulation_previews.json',w.compact_rows(previews))
            f.save(world/'simulation_validation.json',dict(ok=True,configurations=len(a.configurations(document)),**stats))
            f.save(world/'prose_slots.json',skeleton)
            break
        except PaidStageStopped:
            raise
        except Exception as exc:
            if document is None: raise  # uncertain/incomplete first response is not a new draft
            feedback = str(exc)
            f.save(world/f'world_{attempt}.failure.json',dict(error=feedback))
    else:
        raise ValueError('Compact mechanics repair budget exhausted')
    frozen = f.digest(world/'simulation.py')
    context = ('Write warm, witty, physically credible stories for ages 5–8. The executable mechanics are frozen. '
               'Return text for the exact supplied slot IDs; guards, scene binding and wrappers are supplied by the library. '
               'Each slot requests one or two complete alternative phrasings. Do not write code, guards or lexicons. '
               'Openings: 35–55 words establishing the want and actual initial problem, before discoveries. '
               'Beat scenes: 25–45 words; bridges: 12–25 words. Endings: 35–55 words, one vivid image showing the achieved change. '
               'Avoid repeating the last beat in the ending or the opening in the first beat. Aim for 220–400 words per story. '
               'Keep prose modular: do not assume an event immediately preceded this one, or add offscreen exchanges, repairs, '
               'travel, success, knowledge or emotions contradicted by the evidence. Observation reveals exactly the copied fact. '
               'Borrowed objects must remain with their recorded owner until a return event. '
               'Use character names, specific wishes, playful dialogue and concrete consequences; no abstract state names or stated morals. '
               'A slot may be reused across multiple paths; assert only what its guards/evidence and fixed world facts support. '
               '\nWORLD:\n'+json.dumps(document)+'\nTHREE EXECUTED PREVIEWS:\n'+json.dumps(w.compact_rows(previews))+
               '\nNAMED TEXT SLOTS (library supplies the conditions):\n'+json.dumps(skeleton))
    texts, feedback = None, ''
    for prose_attempt in range(4):
        try:
            if prose_attempt == 0:
                texts = await ask(client,budget,world,'text_0',json_request(context,
                    schema=cp.response_schema(skeleton),tokens=9000,effort='low'))
            else:
                prompt = context+'\n\nFix only affected named cards. Return JSON {edits:[{id,old,new}]}; old and new are arrays of text variants. '
                prompt += 'The old array must exactly match its current text. Maximum eight cards. Never use numeric array paths.\nTEXTS:\n'+json.dumps(texts)+'\nFAILURE:\n'+feedback
                patch = await ask(client,budget,world,f'text_patch_{prose_attempt}',json_request(prompt,tokens=3000,effort='low'))
                f.save(world/f'text_patch_{prose_attempt}.json',patch)
                texts = cp.patch_texts(skeleton,texts,patch)
            f.save(world/f'text_{prose_attempt}.json',texts)
            book = cp.catalog(skeleton,texts)
            f.save(world/'texts.json',texts)
            f.save(world/'catalog.json',book)
            (world/'generator.py').write_text(w.compile_catalog(book))
            pool = await w.execute(world,w.POOL_SEEDS,True)
            lengths = [len(r['story'].split()) for r in pool]
            if not 150 <= min(lengths) or max(lengths)>650:
                raise ValueError(f'Story length outside 150–650 words: {min(lengths)}–{max(lengths)}')
            break
        except PaidStageStopped:
            raise
        except Exception as exc:
            if texts is None: raise
            feedback = str(exc)
            f.save(world/f'text_{prose_attempt}.failure.json',dict(error=feedback))
    else:
        raise ValueError('Compact prose repair budget exhausted')
    if f.digest(world/'simulation.py') != frozen: raise ValueError('Frozen simulation changed')
    with (world/'samples.jsonl').open('w') as out:
        for row in pool:
            compact = {k:v for k,v in row.items() if k!='trace'}
            compact.update(scene_path=[e['scene'] for e in row['trace']['events']],structure=signatures(row['trace']))
            out.write(json.dumps(compact,ensure_ascii=False)+'\n')
    f.save(world/'samples_with_trace.json',pool[:3])
    (world/'samples.md').write_text('\n\n'.join(f"## {r['title']} — seed {r['seed']}\n\n{r['story']}" for r in pool[:3])+'\n')
    summary = dict(world=world.name,title=pool[0]['title'],ok=True,samples=len(pool),
        simulation_sha256=frozen,generator_sha256=f.digest(world/'generator.py'),
        world_sha256=f.digest(world/'world.json'),word_range=[min(lengths),max(lengths)],
        mechanics_attempts=attempt+1,prose_attempts=prose_attempt+1,stats=stats,
        prose_slots=len(skeleton['slots']),unselected_scenes=skeleton['unselected_scenes'],
        mechanics_model='gpt-5.6-luna',prose_model='gpt-5.6-luna')
    f.save(world/'summary.json',summary)
    print(f"{world.name}: PASS — {stats['outcomes']} outcomes, {len(skeleton['slots'])} prose slots",flush=True)
    return summary


async def main(args):
    from openai import AsyncOpenAI
    f.load_key(args.api_key_file)
    out = args.out.resolve(); out.mkdir(parents=True,exist_ok=True)
    args.campaign.mkdir(parents=True,exist_ok=True)
    budget = f.Budget(args.campaign.resolve()/'budget.json',15.0)
    settings = dict(protocol='storyscenes_compact_v2',seed=args.seed,count=args.count,
                    service_tier='flex',model='gpt-5.6-luna',critic=False,
                    world_budget=args.world_budget,campaign=str(args.campaign.resolve()),
                    prose_variants=1,ending_groups='declared_outcomes')
    if (out/'settings.json').exists() and json.loads((out/'settings.json').read_text()) != settings:
        raise ValueError('Run settings changed; use a new directory')
    f.save(out/'settings.json',settings)
    for folder,names in (('_runtime',RUNTIME),('_authoring',AUTHORING)):
        destination = out/folder; destination.mkdir(exist_ok=True)
        for name in names:
            path=destination/name
            if path.exists() and f.digest(path)!=f.digest(ROOT/name):
                raise ValueError(f'Frozen {folder}/{name} differs; use a new directory')
            if not path.exists(): shutil.copyfile(ROOT/name,path)
    f.save(out/'runtime_provenance.json',{p.name:f.digest(p) for p in (out/'_runtime').glob('*.py')})
    contract = (out/'_authoring'/'AUTHORING_COMPACT.md').read_text()
    rng = random.Random(args.seed)
    briefs = [dict(index=i,seed=rng.getrandbits(32),theater=name,premise=premise)
              for i,(name,premise) in enumerate(f.THEATERS[:args.count])]
    sem = asyncio.Semaphore(args.concurrency)
    async with AsyncOpenAI(base_url='https://api.openai.com/v1',timeout=900,max_retries=0) as client:
        async def one(brief):
            async with sem:
                world=out/brief['theater']
                try: return await world_run(client,w.WorldBudget(budget,world,args.world_budget),world,brief,contract)
                except Exception as exc:
                    world.mkdir(exist_ok=True)
                    row=dict(world=world.name,ok=False,error=str(exc));f.save(world/'failure.json',row)
                    print(f'{world.name}: FAIL — {exc}',flush=True);return row
        rows=await asyncio.gather(*(one(b) for b in briefs))
    f.save(out/'summary.json',rows)
    if args.evaluate and any(r['ok'] for r in rows) and not (out/'STOP').exists():
        await f.evaluate(out,budget,args.concurrency)
    return int(any(not r['ok'] for r in rows))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--campaign',type=Path,default=ROOT/'improvements/20260908')
    p.add_argument('--seed',type=int,default=20260907)
    p.add_argument('--count',type=int,choices=range(1,11),default=3)
    p.add_argument('--concurrency',type=int,default=3)
    p.add_argument('--world-budget',type=float,default=.15)
    p.add_argument('--api-key-file',type=Path)
    p.add_argument('--evaluate',action='store_true')
    args=p.parse_args()
    if args.concurrency<1 or not 0<args.world_budget<=15:p.error('Invalid concurrency/world budget')
    raise SystemExit(asyncio.run(main(args)))
