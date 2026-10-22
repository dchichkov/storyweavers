#!/usr/bin/env python3
"""Compare returned usage, cached input and quality without excluding failures."""
import argparse
import collections
import json
from pathlib import Path
import statistics

import factory as f


def usage(runs, worlds=None):
    records, seen, pending = [], set(), []
    for root in runs:
        input_path=root/'quality'/'inputs.json'
        evaluation_inputs=json.loads(input_path.read_text()) if input_path.exists() else []
        attempt_path=root/'quality'/'attempts.jsonl'
        if attempt_path.exists():
            for attempt in map(json.loads,attempt_path.read_text().splitlines()):
                if worlds is not None and attempt['script'] not in worlds:continue
                if not (root/'quality'/f"response_{attempt['index']:03d}.json").exists():
                    pending.append(str(attempt_path)+'#'+str(attempt['index']))
        for p in sorted(root.glob('*/*.request.json')):
            if worlds is not None and p.parent.name not in worlds:
                continue
            if not p.with_name(p.name.replace('.request.json','.response.json')).exists():
                pending.append(str(p))
        paths = list(root.glob('*/*.response.json')) + list((root/'quality').glob('response_*.json'))
        for p in sorted(paths):
            phase='evaluation' if p.parent.name=='quality' else 'authoring'
            world=evaluation_inputs[int(p.stem.split('_')[1])]['script'] if phase=='evaluation' else p.parent.name
            if worlds is not None and world not in worlds:
                continue
            d=json.loads(p.read_text())
            if d['id'] in seen:continue
            seen.add(d['id'])
            u=d.get('usage') or {};detail=u.get('input_tokens_details') or {}
            cost=f.trial_cost.token_cost(d.get('model',''),u,d.get('service_tier','unknown'))
            records.append(dict(path=str(p),world=world,phase=phase,
                stage=p.name.split('.')[0],model=d.get('model'),tier=d.get('service_tier'),
                status=d.get('status'),input=u.get('input_tokens',0),output=u.get('output_tokens',0),
                cached=detail.get('cached_tokens',0),writes=detail.get('cache_write_tokens'),
                reasoning=(u.get('output_tokens_details') or {}).get('reasoning_tokens',0),cost=cost))

    def aggregate(rows):
        inputs=sum(r['input'] for r in rows);cached=sum(r['cached'] for r in rows)
        return dict(requests=len(rows),input_tokens=inputs,output_tokens=sum(r['output'] for r in rows),
            reasoning_tokens=sum(r['reasoning'] for r in rows),cached_tokens=cached,
            cache_write_tokens=sum(r['writes'] or 0 for r in rows),
            cache_write_unknown=sum(r['writes'] is None for r in rows),
            cache_hit_requests=sum(r['cached']>0 for r in rows),
            cached_fraction=cached/inputs if inputs else 0,
            tiers=dict(collections.Counter(r['tier'] for r in rows)),
            usd_low=sum(r['cost'].get('usd_low',0) for r in rows),
            usd_high=sum(r['cost'].get('usd_high',0) for r in rows),
            unpriced=sum(not r['cost']['known'] for r in rows))
    return dict(authoring=aggregate([r for r in records if r['phase']=='authoring']),
                evaluation=aggregate([r for r in records if r['phase']=='evaluation']),
                stages={s:aggregate([r for r in records if r['stage']==s])
                        for s in sorted({r['stage'] for r in records})},
                unanswered_requests=pending,records=records)


def ratings(run):
    path=run/'quality'/'quality.jsonl'
    return {r['script']:r for r in map(json.loads,path.read_text().splitlines()) if r['ok']} if path.exists() else {}


def quality(rows):
    rows=list(rows)
    if not rows:return {}
    stories=[s for r in rows for s in r['story_ratings']]
    return dict(worlds=len(rows),stories=len(stories),
        scores={k:statistics.mean(s['rating'][k] for s in stories) for k in f.quality.legacy.RATING_KEYS},
        diversity=statistics.mean(r['diversity']['overall'] for r in rows),
        stories_below_six=sum(s['rating']['overall']<6 for s in stories))


def report(run, baseline, recoveries, out):
    summary=json.loads((run/'summary.json').read_text())
    base_summary=json.loads((baseline/'summary.json').read_text())
    new_ratings,base_ratings=ratings(run),ratings(baseline)
    common=sorted(set(new_ratings)&set(base_ratings))
    matched_worlds={r['world'] for r in base_summary}
    new_cost=usage([run]);base_cost=usage([baseline,*recoveries])
    matched_cost=usage([run],matched_worlds)
    verification_path=run/'verification.json'
    verification=json.loads(verification_path.read_text()) if verification_path.exists() else None
    result=dict(run=str(run),baseline=str(baseline),recoveries=list(map(str,recoveries)),
        attempted=len(summary),successful=sum(r['ok'] for r in summary),
        baseline_attempted=len(base_summary),baseline_successful=sum(r['ok'] for r in base_summary),
        fresh_verification=verification,
        fresh_verified=sum(r['ok'] for r in verification) if verification is not None else None,
        new_usage=new_cost,baseline_usage=base_cost,new_matched_usage=matched_cost,
        matched_attempted_worlds=sorted(matched_worlds),
        new_quality=quality(new_ratings.values()),matched_quality_worlds=common,
        old_matched_quality=quality(base_ratings[w] for w in common),
        new_matched_quality=quality(new_ratings[w] for w in common),
        failures=[r for r in summary if not r['ok']],
        world_ratings={w:dict(rating=r['rating'],diversity=r['diversity']) for w,r in new_ratings.items()})
    # Every shared theater must retain the exact initial design brief.
    for name in matched_worlds:
        if json.loads((run/name/'seed.json').read_text()) != json.loads((baseline/name/'seed.json').read_text()):
            raise ValueError('Unmatched design brief: '+name)
    out.mkdir(parents=True,exist_ok=True);f.save(out/'comparison.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--baseline',type=Path,default=Path('storyscenes/runs/compact_algebra_v2'))
    p.add_argument('--recovery',type=Path,action='append',default=[])
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();r=report(args.run,args.baseline,args.recovery,args.out)
    print(json.dumps({k:v for k,v in r.items() if k not in ('new_usage','baseline_usage','new_matched_usage')},indent=2))
