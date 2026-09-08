#!/usr/bin/env python3
"""Audit returned tokens, unknown requests, and scale authoring separately from QA."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import factory as f


def add_costs(first, second):
    merged=dict(first)
    for key in ('requests','priced_requests','unpriced_requests','input_tokens','output_tokens','usd_low','usd_high'):
        merged[key]=first[key]+second[key]
    return merged


def audit(root, seen=None):
    seen=set() if seen is None else seen
    if root in seen: raise ValueError('Cycle in authoring provenance')
    seen.add(root)
    groups=defaultdict(list); worlds=defaultdict(list); requests=[]
    unknown=[]
    for p in sorted(root.glob('*/*.request.json')):
        if p.parent.name == 'quality': continue
        stage=p.name.removesuffix('.request.json')
        body=json.loads(p.read_text())
        response_path=p.with_name(stage+'.response.json')
        role=('evaluation' if stage=='critic' else 'authoring')
        family=('mechanics_patch' if 'simulation_patch' in stage else
                'mechanics' if 'simulation' in stage else
                'prose_patch' if 'catalog_patch' in stage else
                'prose' if 'catalog' in stage or 'generator' in stage else
                'plan' if stage=='plan' else stage)
        row=dict(world=p.parent.name,stage=stage,role=role,model=body['model'],
                 output_cap=body['max_output_tokens'],input_characters=len(json.dumps(body['input'])))
        if not response_path.exists():
            row['status']='unknown'; unknown.append(str(p.relative_to(root))); requests.append(row); continue
        response=json.loads(response_path.read_text())
        cost=f.trial_cost.token_cost(response.get('model',''),response.get('usage') or {},response.get('service_tier','unknown'))
        row.update(status=response.get('status'),actual_model=response.get('model'),tier=response.get('service_tier'),cost=cost,
                   reasoning_tokens=(response.get('usage',{}).get('output_tokens_details') or {}).get('reasoning_tokens',0))
        groups[(role,body['model'],family)].append({'response':response})
        if role=='authoring': worlds[p.parent.name].append({'response':response})
        requests.append(row)
    quality=[]
    if (root/'quality/quality.jsonl').exists():
        quality=[json.loads(x) for x in (root/'quality/quality.jsonl').read_text().splitlines()]
    if quality:
        groups[('evaluation','gpt-5.6-terra','set_judge')]=quality
    summaries=[json.loads(p.read_text()) for p in root.glob('*/summary.json') if (p.parent/'simulation.py').exists()]
    success=sum(bool(s.get('ok')) for s in summaries)
    author=f.trial_cost.summarize([r for rows in worlds.values() for r in rows])
    own_author=dict(author)
    parent=None
    settings=json.loads((root/'settings.json').read_text()) if (root/'settings.json').exists() else {}
    if settings.get('from_run'):
        parent=audit(Path(settings['from_run']).resolve(),seen)
        author=add_costs(author,parent['authoring'])
    evaluation=f.trial_cost.summarize([r for k,rows in groups.items() if k[0]=='evaluation' for r in rows])
    own_evaluation=dict(evaluation)
    if parent and settings.get('reuse_review'):
        # A reused diagnostic still had a price. Its cost must not disappear
        # from the production-with-review projection merely because it is cached.
        inherited_review=f.trial_cost.summarize([])
        for group in parent['groups']:
            if group['stage']=='critic': inherited_review=add_costs(inherited_review,group)
        evaluation=add_costs(evaluation,inherited_review)
    projection=None
    if success:
        projection=dict(successful_worlds=success,attempted_worlds=len(list(root.glob('*/seed.json'))),
            returned_authoring_usd_per_success=author['usd_high']/success,
            returned_authoring_usd_for_20000=author['usd_high']/success*20000,
            authoring_input_tokens_for_20000=author['input_tokens']/success*20000,
            authoring_output_tokens_for_20000=author['output_tokens']/success*20000,
            same_evaluation_usd_for_20000=evaluation['usd_high']/success*20000,
            caveat='Linear estimate from this small batch including failed attempts. Excludes unknown paid outcomes, human review, hosting, and a change in success/acceptance rate or prices. Mechanical success is not literary acceptance.')
    inherited_unknown=[] if not parent else parent['unknown_requests'] + parent.get('inherited_unknown_requests',[])
    return dict(run=str(root),authoring=author,own_authoring=own_author,
        inherited_authoring=None if not parent else dict(run=parent['run'],cost=parent['authoring']),
        evaluation=evaluation,own_evaluation=own_evaluation,unknown_requests=unknown,inherited_unknown_requests=inherited_unknown,
        groups=[dict(role=role,model=model,stage=stage,**f.trial_cost.summarize(rows)) for (role,model,stage),rows in sorted(groups.items())],
        per_world={w:f.trial_cost.summarize(rows) for w,rows in sorted(worlds.items())},
        projection=projection,requests=requests)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    p.add_argument('--out',type=Path)
    args=p.parse_args(); result=audit(args.run.resolve())
    if args.out: f.save(args.out,result)
    else: print(json.dumps(result,indent=2))
