#!/usr/bin/env python3
"""Create a matched-theater comparison without changing the judge rubric."""
import argparse
import json
from pathlib import Path
import factory as f
from cost_report import audit


def load(path): return json.loads(path.read_text())
def rows(path): return [json.loads(line) for line in path.read_text().splitlines()]


def compare(baseline,run,campaign):
    old=load(baseline/'quality/summary.json'); new=load(run/'quality/summary.json')
    a={r['script']:r for r in rows(baseline/'quality/quality.jsonl')}
    b={r['script']:r for r in rows(run/'quality/quality.jsonl')}
    if set(a)!=set(b) or not all(r['ok'] for r in b.values()):
        raise ValueError('Need the same fully evaluated theater set')
    cost=audit(run); f.save(run/'cost_audit.json',cost)
    ledger=load(campaign/'budget.json')
    accounted=ledger['committed_upper_usd']
    returned=sum(e['cost']['usd_high'] for e in ledger['entries'] if e.get('status')=='returned' and e.get('cost',{}).get('known'))
    unknown=[e for e in ledger['entries'] if e.get('status')!='returned' or not e.get('cost',{}).get('known')]
    verification=load(run/'verification.json')
    world_rows=[]
    for name in sorted(b):
        spec=load(run/name/'summary.json')
        world_rows.append(dict(world=name,before_quality=a[name]['rating']['overall'],quality=b[name]['rating']['overall'],
            before_diversity=a[name]['diversity']['overall'],diversity=b[name]['diversity']['overall'],
            judged_plot_groups=len(b[name]['plot_groups']),**spec['stats']))
    report=dict(baseline=str(baseline),run=str(run),old=old,new=new,worlds=world_rows,
        cost=cost,campaign=dict(returned_usd=returned,accounted_with_reservations_usd=accounted,unknown_requests=len(unknown),limit_usd=ledger['limit_usd']))
    f.save(run/'comparison.json',report)
    text=['# Storyscenes: Luna-only improvement pass','',
          f"Ten theater generators use Luna for all authoring and repair. Saved generators make no API calls. The same judge rated {new['rated_stories']} uniformly sampled stories across {new['rated_worlds']} worlds.",'',
          '| Metric /9 | Original prototype | Luna improvement | Change |',
          '|---|---:|---:|---:|']
    for metric in ['overall','coherence','style','grammar','storytelling']:
        x=old['mean_quality'][metric];y=new['mean_quality'][metric]
        text.append(f'| {metric.title()} | {x:.2f} | {y:.2f} | {y-x:+.2f} |')
    x=old['mean_diversity']['overall'];y=new['mean_diversity']['overall']
    text+= [f'| Within-world diversity | {x:.2f} | {y:.2f} | {y-x:+.2f} |','',
        f"Stories below 6 overall: **{old['stories_below_six']} → {new['stories_below_six']} of 100**.",'',
        '| World | Quality before → after | Diversity before → after | Judged plot groups | Scene sets /100 | Outcomes /100 |',
        '|---|---:|---:|---:|---:|---:|']
    for r in world_rows:
        text.append(f"| [{r['world']}]({r['world']}/samples.md) | {r['before_quality']:.2f} → {r['quality']:.2f} | {r['before_diversity']} → {r['diversity']} | {r['judged_plot_groups']} | {r['scene_sets']} | {r['outcomes']} |")
    text+=['','## What changed','',
        'The planner slices away irrelevant preparation, then replays the retained actions against guards and invariants. Intended outcome fields must change in some sampled path, catching goals that stop before a delivery, performance or response. Knowledge and ownership use shared kernels; keyword APIs and safe state-key renames reduce authoring friction.','',
        'A common data-only renderer selects complete text cards from initial/before/after state, groups routine bridges, and expands explicit grammatical phrase mappings. Endings are conditional on final facts. It rejects missing cards, raw state leakage, unresolved alternatives, repeated words and contradictory/future fact bindings. Free English assertions still require semantic review.','',
        'All current authoring and routine repair uses Luna. Initial mechanics are written once per draft; subsequent repairs return bounded source edits or catalog edits. The measured second pass inherits Luna drafts rather than paying to regenerate them. Their costs, including failed attempts and abandoned catalogs, are included below. Terra only performs separate evaluation. The earlier Terra-heavy experiment was stopped and is accounted for as development overhead.','',
        'These changes move toward the memeplex model: immutable definitions compose over mutable state on physical carriers; beliefs and motives gate compatible behavior; realization reads that state. This is still a small operational subset, not a universal algebra or a proven kernel library distilled from storyscripts.','',
        '## Cost and 20,000-world projection','',
        '| Scope | Returned input tokens | Returned output tokens | Estimated USD |','|---|---:|---:|---:|']
    for title,key in [('Luna authoring, including inherited failed drafts','authoring'),('Separate evaluation for this final batch','evaluation')]:
        c=cost[key];text.append(f"| {title} | {c['input_tokens']:,} | {c['output_tokens']:,} | ${c['usd_high']:.4f} |")
    text+=['','Current-run stage breakdown (the linked cost audit separates inherited draft costs):','',
        '| Model and stage | Requests | Input tokens | Output tokens | USD |','|---|---:|---:|---:|---:|']
    for g in cost['groups']:
        text.append(f"| {g['model']} / {g['stage']} | {g['requests']} | {g['input_tokens']:,} | {g['output_tokens']:,} | ${g['usd_high']:.4f} |")
    p=cost['projection']
    text+=['',f"Measured authoring cost: **${p['returned_authoring_usd_per_success']:.4f} per mechanically successful world**. A straight-line projection is **${p['returned_authoring_usd_for_20000']:.0f} for 20,000 worlds**. Repeating both the three-story trace review and the ten-story Terra set judge for every world would add approximately **${p['same_evaluation_usd_for_20000']:.0f}**. Runtime sampling itself uses no paid model tokens. The evaluated protocol includes bounded review feedback; its quality is not established for unreviewed authoring at the authoring-only price.",'',
        'This includes failed and superseded Luna attempts; it does not assume that the first response succeeds. It is a small-batch estimate, not a quotation: a lower literary acceptance rate, different world complexity, unknown API outcomes, operational costs or changed prices will change it. Output totals include reasoning. Costs use returned model and service tier, not merely requested Flex.','',
        f"Full improvement campaign, including the stopped Terra experiment: **${returned:.4f}** in returned-usage estimates; **${accounted:.4f}** accounted for including {len(unknown)} uncertain outcomes/reservations, under the **${ledger['limit_usd']:.0f}** authorization. These figures exclude the earlier prototype's separate budget and are not invoice reconciliation.",'',
        '## Validation and comparison limits','',
        f"Offline verification: {sum(r['ok'] for r in verification)}/{len(verification)} worlds; {sum(r.get('fresh_samples',0) for r in verification)} fresh samples and {sum(r.get('pinned_replays',0) for r in verification)} pinned replays. The baseline hash/pin audit is saved in the campaign directory.",'',
        'The theater briefs, design seed, sample seeds and uniform judging seed match the baseline. Plans, model allocation, runtime and prose interface changed together, so this measures the combined intervention rather than isolating one cause. The same judge/rubric/calibration were used. This is neither a matched one-stage control nor evidence of production-level acceptance. Ordered paths, scene sets and distinct scalar outcomes are diagnostics; only the plot-group judge estimates semantic diversity.','',
        'Artifacts: [manual readings](manual_review.md), [judge report](quality/report.md), [exact judge inputs](quality/inputs.json), [verification](verification.json), [request/token audit](cost_audit.json), [machine-readable comparison](comparison.json).','']
    (run/'REPORT.md').write_text('\n'.join(text))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',type=Path,default=Path('storyscenes/runs/prototype_v1'))
    p.add_argument('--run',type=Path,required=True);p.add_argument('--campaign',type=Path,required=True)
    args=p.parse_args();r=compare(args.baseline.resolve(),args.run.resolve(),args.campaign.resolve())
    print(json.dumps({'before':r['old']['mean_quality'],'after':r['new']['mean_quality'],'cost':r['cost']['projection']},indent=2))
