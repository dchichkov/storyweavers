#!/usr/bin/env python3
"""Matched fresh-run accounting: include failed drafts, reasoning and all retries."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics

import factory as f


def measure(root):
    requests=[];responses=[];by_world=defaultdict(lambda:dict(requests=0,output=0,reasoning=0,input=0))
    stages=defaultdict(lambda:dict(requests=0,output=0,reasoning=0,input=0))
    for path in sorted(root.glob('*/*.request.json')):
        body=json.loads(path.read_text())
        if body['model']!='gpt-5.6-luna':raise ValueError('Authoring comparison requires Luna only')
        if body.get('service_tier')!='flex':raise ValueError('Authoring comparison requires Flex only')
        stage=path.name.removesuffix('.request.json')
        kind=('repair' if 'patch' in stage else 'initial')+' '+('prose' if stage.startswith(('text','catalog')) else 'mechanics/plan')
        record=dict(world=path.parent.name,stage=stage,requested_tier=body['service_tier'],returned=False)
        response_path=path.with_name(stage+'.response.json')
        stats=dict(requests=1,input=0,output=0,reasoning=0)
        if response_path.exists():
            response=json.loads(response_path.read_text());usage=response.get('usage') or {}
            responses.append({'response':response})
            stats.update(input=usage.get('input_tokens',0),output=usage.get('output_tokens',0),
                         reasoning=(usage.get('output_tokens_details') or {}).get('reasoning_tokens',0))
            record.update(returned=True,status=response.get('status'),actual_model=response.get('model'),actual_tier=response.get('service_tier'),**stats)
        requests.append(record)
        for dest in (by_world[path.parent.name],stages[kind]):
            for k,v in stats.items():dest[k]+=v
    summary=json.loads((root/'summary.json').read_text())
    judge_path=root/'quality'/'quality.jsonl'
    judges=[json.loads(x) for x in judge_path.read_text().splitlines()] if judge_path.exists() else []
    good_judges={r['script']:r for r in judges if r['ok']}
    totals={k:sum(s[k] for s in by_world.values()) for k in ('requests','input','output','reasoning')}
    return dict(run=str(root.resolve()),attempted=len(summary),successful=sum(r['ok'] for r in summary),
                summaries=summary,authoring=totals,stages=dict(stages),worlds=dict(by_world),requests=requests,
                cost=f.trial_cost.summarize(responses),
                evaluation_cost=f.trial_cost.summarize([r for r in judges if r.get('response')]),
                unknown=[r for r in requests if not r['returned']],
                ratings={name:dict(quality=r['rating'],diversity=r['diversity'],stories_below_six=r['stories_below_six']) for name,r in good_judges.items()})


def compare(control, compact, out, recoveries=()):
    old,new=measure(control),measure(compact)
    new['recoveries']=[]
    for path in recoveries:
        data=measure(path);new['recoveries'].append(data)
        for world in data['worlds']:
            if json.loads((compact/world/'seed.json').read_text())!=json.loads((path/world/'seed.json').read_text()):
                raise ValueError('Recovery seed mismatch: '+world)
            for key,value in data['worlds'][world].items():new['worlds'][world][key]+=value
        for key,value in data['authoring'].items():new['authoring'][key]+=value
        for stage,counts in data['stages'].items():
            dest=new['stages'].setdefault(stage,dict(requests=0,input=0,output=0,reasoning=0))
            for key,value in counts.items():dest[key]+=value
        for scope in ('cost','evaluation_cost'):
            for key in ('requests','priced_requests','unpriced_requests','input_tokens','output_tokens','usd_low','usd_high'):
                new[scope][key]+=data[scope][key]
        new['requests']+=data['requests'];new['unknown']+=data['unknown']
        for row in data['summaries']:
            if row['ok']:
                new['summaries']=[row if x['world']==row['world'] else x for x in new['summaries']]
        new['ratings'].update(data['ratings'])
    new['successful']=sum(r['ok'] for r in new['summaries'])
    worlds=sorted(set(old['worlds']) | set(new['worlds']))
    for name in worlds:
        if json.loads((control/name/'seed.json').read_text())!=json.loads((compact/name/'seed.json').read_text()):
            raise ValueError('Design brief/seed mismatch: '+name)
    common=sorted(set(old['ratings']) & set(new['ratings']))
    means={}
    for name,data in [('control',old),('compact',new)]:
        means[name]={k:statistics.mean(data['ratings'][world]['quality'][k] for world in common)
                     for k in ('coherence','style','grammar','storytelling','overall')} if common else {}
        if common:means[name]['diversity']=statistics.mean(data['ratings'][world]['diversity']['overall'] for world in common)
    reduction=1-new['authoring']['output']/old['authoring']['output']
    report=dict(control=old,compact=new,matched_rated_worlds=common,matched_means=means,output_reduction=reduction)
    interrupted_path=out/'interrupted_control.json'
    if interrupted_path.exists():
        report['interrupted_control']=json.loads(interrupted_path.read_text())
    settings=json.loads((compact/'settings.json').read_text())
    ledger=json.loads((Path(settings['campaign'])/'budget.json').read_text())
    prefixes={control.name+'/',compact.name+'/', 'compact_control_v1/', 'compact_algebra_v1/'} | {p.name+'/' for p in recoveries}
    entries=[e for e in ledger['entries'] if any(e['label'].startswith(p) for p in prefixes)]
    # Set judges use judge/<theater> labels shared across runs, so the measured
    # response totals above remain the per-run evaluation accounting authority.
    report['campaign']=dict(limit_usd=ledger['limit_usd'],accounted_usd=ledger['committed_upper_usd'],
        uncertain_requests=sum(e['status']!='returned' for e in ledger['entries']),
        experiment_authoring_accounted_usd=sum(e['reserved_usd'] for e in entries),
        experiment_uncertain=[e for e in entries if e['status']!='returned'])
    development=[e for e in entries if e['label'].startswith('compact_algebra_v1/')]
    report['development']=dict(run='compact_algebra_v1',authoring_accounted_usd=sum(e['reserved_usd'] for e in development),
        note='Separate initial compiler-development trial, including over-expanded prose requests. It is not inherited by the fresh v2 benchmark.')
    out.mkdir(parents=True,exist_ok=True);f.save(out/'comparison.json',report)
    text=['# Compact Storyscenes authoring experiment','',
          'Fresh control and compact runs use the same three theater briefs, design seeds, sample seeds, Luna authoring, Flex service and unchanged Terra set judge. Neither receives semantic critic feedback. All returned authoring tokens include reasoning and failed/repair attempts. This is a small combined-interface experiment; it does not isolate each compiler feature.','',
          '| Measure | Python control | Compact algebra |','|---|---:|---:|',
          f"| Completed worlds / attempted | {old['successful']}/{old['attempted']} | {new['successful']}/{new['attempted']} |"]
    for key,label in [('requests','Luna requests'),('input','Input tokens'),('output','Output tokens'),('reasoning','Reasoning output tokens')]:
        text.append(f"| {label} | {old['authoring'][key]:,} | {new['authoring'][key]:,} |")
    for key,label in [('cost','Authoring cost estimate'),('evaluation_cost','Separate set-judge cost estimate')]:
        text.append(f"| {label} | ${old[key]['usd_high']:.4f} | ${new[key]['usd_high']:.4f} |")
    text+=['',f'Output reduction across all attempted worlds: **{reduction:.1%}**. Unknown request outcomes: {len(old["unknown"])} control, {len(new["unknown"])} compact. Unknown outcomes have no measured usage and retain budget reservations.','',
           f'Quality comparison covers the {len(common)} worlds successfully judged in both runs; completion rates above remain part of the result. Scores are 0–9.','',
           '| Dimension | Control | Compact |','|---|---:|---:|']
    for key in means['control']:
        text.append(f"| {key} | {means['control'][key]:.2f} | {means['compact'][key]:.2f} |")
    text+=['','| Theater | Control output | Compact output | Control quality | Compact quality |','|---|---:|---:|---:|---:|']
    for name in worlds:
        oq=old['ratings'].get(name,{}).get('quality',{}).get('overall','unrated')
        nq=new['ratings'].get(name,{}).get('quality',{}).get('overall','unrated')
        text.append(f"| {name} | {old['worlds'].get(name,{}).get('output',0):,} | {new['worlds'].get(name,{}).get('output',0):,} | {oq} | {nq} |")
    text+=['', '## Interrupted attempt and campaign accounting','',
        'The control reuses three completed plan responses from the interrupted compact_control_v1 attempt. They are counted once above and were not requested again. Three mechanics requests from that attempt have unrecorded paid outcomes because the disk filled; their usage is unavailable and excluded from the measured token difference. They are additional development overhead, with their full reservations retained.',
        f"The shared improvement campaign accounts for **${report['campaign']['accounted_usd']:.4f} of $15**, including {report['campaign']['uncertain_requests']} uncertain requests across this and earlier work. This is conservative local accounting, not invoice reconciliation. The exact interrupted requests and reused response hashes are saved in interrupted_control.json and the control's reused_plan_provenance.json."]
    text+=['',f"The initial compact_algebra_v1 development trial accounts for **${report['development']['authoring_accounted_usd']:.4f}** separately. It exposed an ending-card cross-product: incidental final facts produced 34 roof-post endings. The final implementation groups endings by declared outcomes, supplies only the intersection of facts across each group, and requests one wording per slot. The v2 benchmark starts fresh and includes all of its own repairs; its savings are not presented as a refund of this development cost."]
    if recoveries:
        text+=['','All bounded roof-post recovery attempts are included in the compact totals above. The original draft hit its 5,500-token cap; a 575-token continuation completed its JSON without rewriting the prefix. Six subsequent small patches still did not yield a valid composition, so it remains quarantined. Completion remains 2/3; no stronger model repaired the world.']
    text+=['','## What changed','',
        '- One executable world document replaces a prose plan followed by generated Python. Shared code supplies seeding, typed conditions/effects, knowledge slots, ownership/loan operations, wrappers and named repairs.',
        '- Immutable kernels bind roles to physical carriers. Pattern addition pools legal opportunities; division attenuates search attention. Definitions can nest; accumulated state, guarded actions and the solver determine order. This is an operational subset of the memeplex model, not yet a universal algebra of concepts, people and whole stories.',
        '- The library derives prose slot IDs and factual guards from executed traces. Endings share a declared outcome; their evidence contains only facts common to every represented trace. One wording per slot avoids paying for cosmetic duplicates. Luna writes wording only. Named edits require matching old text, preventing the earlier wrong-array-index failure.',
        '- Explicit finite initial configurations are exhaustively checked; four search seeds per configuration and 100 sampled seeds build the prose inventory. This does not enumerate every reachable action ordering; unseen prose conditions fail closed.',
        '', 'The prior pond-concert world was separately ported without changing its behavior: 300 exact trace replays and 600 exact prose/QA replays. The old definition was 7,279 characters; the compact JSON was 4,722. These are character counts, not API token measurements.',
        '', '## Limits and next gate','',
        'Three theater pairs are insufficient for a production acceptance estimate. Quality judgments have model variance. A smaller source is useful only if total authoring tokens and repair rate fall without losing story quality or causal diversity. Free English assertions still need manual semantic review; generated guard facts do not prove every sentence. Runtime remains entirely offline.',
        '', 'A post-benchmark guard strengthening makes closing cards check every common evidence fact, not only their outcome signature. Recompiling the saved text with those stronger guards preserved story text, trace and QA on 400 existing/fresh samples; only paragraph fact annotations changed. This is recorded in ending_guard_verification.json. The saved benchmark snapshots are unchanged.',
        '', 'See comparison.json for every request, stage, token count, rating and failure; see manual_review.md and verification.json for direct readings and fresh-seed validation.','']
    (out/'REPORT.md').write_text('\n'.join(text))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--control',type=Path,required=True);p.add_argument('--compact',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--recovery',type=Path,action='append',default=[])
    args=p.parse_args();result=compare(args.control,args.compact,args.out,args.recovery)
    print(json.dumps(dict(output_reduction=result['output_reduction'],quality=result['matched_means']),indent=2))
