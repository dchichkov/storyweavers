#!/usr/bin/env python3
"""Fresh offline stories + QA, unchanged story judge, separate semantic QA judge."""
import argparse
import ast
import asyncio
from collections import Counter
import json
from pathlib import Path
import random
import shutil
import time

import factory as f
import conversation_quality as cq
from conversation import Conversation, fingerprint
from dialogue import QUOTES
from prose import render_book
from qa import load_samples, enrich, chat_records
from qa_checks import measure

ROOT=Path(__file__).resolve().parent
SOURCES=('library_parade','pond_concert')


def write_rows(path,rows):
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))


def prepare(out, *, count=100, seed=19000):
    settings=dict(protocol='conversation_trial_v1',count=count,seed=seed,qa_seed=777,
        worlds=list(SOURCES),source_run='compact_algebra_v2',story_batch_size=10,qa_batch_size=5,
        story_model='gpt-5.6-terra',qa_model='gpt-5.6-terra',service_tier='flex',
        selection='consecutive fresh seeds, equal allocation, no dedup or rejection selection',
        authoring_api_calls=0,per_sample_generation_api_cost=0,
        story_judge='unchanged story_set_quality_v1; all samples graded in disjoint sets',
        qa_judge=cq.PROTOCOL)
    if (out/'settings.json').exists():
        if json.loads((out/'settings.json').read_text())!=settings:raise ValueError('Trial settings changed')
        rows=[json.loads(x) for x in (out/'samples.jsonl').read_text().splitlines()]
        if len(rows)!=count:raise ValueError('Incomplete preparation; inspect before resuming')
        return rows
    out.mkdir(parents=True,exist_ok=False)
    snapshot=out/'_evaluation';snapshot.mkdir()
    names=['conversation_trial.py','conversation.py','dialogue.py','qa.py','qa_checks.py','prose.py','runtime.py',
           'api_requests.py','factory.py','evaluation/conversation_quality.py','evaluation/openai_world_set_quality.py',
           'evaluation/openai_story_quality.py','evaluation/trial_cost.py']
    for name in names:shutil.copyfile(ROOT/name,snapshot/Path(name).name)
    f.save(out/'source_hashes.json',{name:f.digest(ROOT/name) for name in names})
    rows=[];coverage=[];started=time.monotonic()
    for name in SOURCES:
        world=ROOT/'runs/compact_algebra_v2'/name
        original=load_samples(world,seed,count//2)
        module=ast.parse((world/'generator.py').read_text())
        book=next(ast.literal_eval(n.value) for n in module.body if isinstance(n,ast.Assign)
                  and any(isinstance(t,ast.Name) and t.id=='BOOK' for t in n.targets))
        f.save(out/f'{name}_provenance.json',dict(world=str(world),
            files={n:f.digest(world/n) for n in ('generator.py','simulation.py','world.json')}))
        for item in original:
            paragraphs=render_book(item['trace'],random.Random(item['prose_seed']),book)
            if '\n\n'.join(p['text'].strip() for p in paragraphs)!=item['story']:
                raise ValueError('Current renderer changed benchmark prose')
            row=enrich(dict(item,paragraphs=paragraphs))
            row.update(world=name,sample_id=f'{name}:{row["seed"]}',story_sha256=fingerprint(row['story']))
            rows.append(row);dialog=Conversation(row['trace'],paragraphs)
            coverage.append(dict(sample_id=row['sample_id'],conversations=len(row['conversations']),
                utterances=len(dialog.dialogue),quote_spans=sum(len(QUOTES.findall(p['text'])) for p in paragraphs),
                indexed_quote_spans=sum(len(u['quotes']) for u in dialog.dialogue),
                precise_speech_events=sum(u['event_id'] is not None for u in dialog.dialogue)))
        print(f'{name}: generated {len(original)} fresh stories with QA',flush=True)
    write_rows(out/'samples.jsonl',rows)
    write_rows(out/'chat_review.jsonl',[record for row in rows for record in chat_records(row)])
    f.save(out/'coverage.json',coverage)
    checks=measure(rows)
    checks.update(generation_seconds=time.monotonic()-started,unique_story_texts=len({r['story_sha256'] for r in rows}),
                  preserved_story_texts=len(rows),generation_api_cost_usd=0)
    f.save(out/'mechanical_checks.json',checks)
    f.save(out/'settings.json',settings)
    if checks['defects']:raise ValueError('Mechanical QA defects; inspect before judging')
    return rows


def jobs_for(rows):
    jobs=[]
    for world in SOURCES:
        pool=[r for r in rows if r['world']==world];indices=list(range(len(pool)));random.Random(777).shuffle(indices)
        for offset in range(0,len(indices),10):
            batch=[pool[i] for i in indices[offset:offset+10]]
            item=f.quality.select_set(f'{world}/set_{offset//10:02d}',batch,777,count=len(batch))
            for story in item['stories']:story['sample_id']=batch[story['source_index']]['sample_id']
            jobs.append(dict(phase='story_quality',stage=f'{world}_{offset//10:02d}',input=item,
                             body=f.quality.request_body(item,cache_prompts=True)))
    shuffled=list(rows);random.Random(1777).shuffle(shuffled)
    for i in range(0,len(shuffled),5):
        batch=shuffled[i:i+5]
        jobs.append(dict(phase='qa_quality',stage=f'batch_{i//5:02d}',input=batch,body=cq.request_body(batch)))
    return jobs


class TrialBudget:
    def __init__(self,budget,label,cap):self.budget=budget;self.label=label;self.cap=cap
    def reserve(self,label,body):
        ir,_,wr,orr=f.trial_cost.FLEX_RATES[body['model']]
        upper=round((len(json.dumps(body))*max(ir,wr)+body['max_output_tokens']*orr)*2/1e6+.01,6)
        committed=sum(e['reserved_usd'] for e in self.budget.entries if e['label'].startswith(self.label+'/'))
        if committed+upper>self.cap:raise ValueError('Trial spending cap reached')
        return self.budget.reserve(self.label+'/'+label,body)
    def settle(self,index,response):self.budget.settle(index,response)


async def evaluate(out,rows,args):
    from openai import AsyncOpenAI
    for name,digest in json.loads((out/'source_hashes.json').read_text()).items():
        if f.digest(ROOT/name)!=digest:raise ValueError('Evaluation source changed since preparation: '+name)
    f.load_key(args.api_key_file)
    ledger=f.Budget(args.campaign/'budget.json',15)
    budget=TrialBudget(ledger,out.name,args.trial_budget)
    jobs=jobs_for(rows)
    f.save(out/'judge_manifest.json',[dict(phase=j['phase'],stage=j['stage'],
        samples=[s['sample_id'] for s in j['input']['stories']] if j['phase']=='story_quality'
                else [s['sample_id'] for s in j['input']],request_sha256=fingerprint(j['body'])) for j in jobs])
    sem=asyncio.Semaphore(args.concurrency)
    async with AsyncOpenAI(base_url='https://api.openai.com/v1',timeout=900,max_retries=0) as client:
        async def one(job):
            async with sem:
                directory=out/job['phase'];directory.mkdir(exist_ok=True)
                row=dict(phase=job['phase'],stage=job['stage'],ok=False)
                f.save(directory/f'{job["stage"]}.input.json',job['input'])
                try:
                    text=await f.api_artifact(client,budget,directory,job['stage'],job['body'])
                    response=json.loads((directory/f'{job["stage"]}.response.json').read_text())
                    if response.get('service_tier')!='flex':raise ValueError('Unexpected returned service tier')
                    value=json.loads(text)
                    row['assessment']=(f.quality.validate(value,job['input']) if job['phase']=='story_quality'
                                       else cq.validate(value,job['input']))
                    row['ok']=True
                except Exception as exc:
                    row['error']=str(exc)
                response_path=directory/f'{job["stage"]}.response.json'
                if response_path.exists():
                    response=json.loads(response_path.read_text())
                    row['response']={k:response.get(k) for k in ('id','model','status','service_tier','usage')}
                f.save(directory/f'{job["stage"]}.result.json',row)
                print(f'{job["phase"]}/{job["stage"]}: {"OK" if row["ok"] else "FAILED (see result artifact)"}',flush=True)
                return row
        results=await asyncio.gather(*(one(job) for job in jobs))
    return summarize(out,results,ledger)


def summarize(out,results,ledger):
    story_results=[dict(r,**r.get('assessment',{})) for r in results if r['phase']=='story_quality']
    qa_results=[r for r in results if r['phase']=='qa_quality']
    summary=dict(story_quality=f.quality.summarize(story_results),qa_quality=cq.summarize(qa_results),
                 cost=f.trial_cost.summarize(results),generation_api_cost_usd=0,
                 failed_jobs=[dict(phase=r['phase'],stage=r['stage'],error=r.get('error')) for r in results if not r['ok']])
    summary['story_quality'].update(judged_sets=sum(r['ok'] for r in story_results),requested_sets=len(story_results),
        worlds=len(SOURCES),rated_worlds=len({r['stage'].rsplit('_',1)[0] for r in story_results if r['ok']}))
    summary['phase_costs']={phase:f.trial_cost.summarize([r for r in results if r['phase']==phase])
                            for phase in ('story_quality','qa_quality')}
    responses=[r['response'] for r in results if r.get('response')]
    summary['cache']=dict(returned_tiers=dict(Counter(r.get('service_tier') for r in responses)),
        input_tokens=sum(r['usage']['input_tokens'] for r in responses),
        cached_tokens=sum(r['usage'].get('input_tokens_details',{}).get('cached_tokens',0) for r in responses),
        written_tokens=sum(r['usage'].get('input_tokens_details',{}).get('cache_write_tokens',0) for r in responses))
    entries=[e for e in ledger.entries if e['label'].startswith(out.name+'/')]
    summary['unresolved_reservation_usd']=sum(e['reserved_usd'] for e in entries if e['status']!='returned' or not e.get('cost',{}).get('known'))
    summary['campaign_committed_upper_usd']=sum(e['reserved_usd'] for e in ledger.entries)
    f.save(out/'evaluation_summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--count',type=int,default=100)
    p.add_argument('--seed',type=int,default=19000)
    p.add_argument('--evaluate',action='store_true')
    p.add_argument('--api-key-file',type=Path)
    p.add_argument('--campaign',type=Path,default=ROOT/'improvements/20260908')
    p.add_argument('--trial-budget',type=float,default=3)
    p.add_argument('--concurrency',type=int,default=4)
    args=p.parse_args()
    if args.count<20 or args.count%20 or args.concurrency<1 or not 0<args.trial_budget<=15:
        p.error('Use a positive multiple of 20 stories, positive concurrency and budget at most $15')
    rows=prepare(args.out,count=args.count,seed=args.seed)
    if args.evaluate:
        report=asyncio.run(evaluate(args.out,rows,args));print(json.dumps(report,indent=2))
        return int(bool(report['failed_jobs']))
    print(json.dumps(json.loads((args.out/'mechanical_checks.json').read_text()),indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
