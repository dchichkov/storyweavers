"""Audit all 100 live iterations before reporting the larger continuation suite."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import statistics

from .annotation import fingerprint
from .neuron_review import model_fingerprint
from .online_teacher import atomic_json
from .transformer import Storyformer
from .refine import load_documents


def report(root):
    read=lambda p:json.loads(p.read_text())
    manifest=read(root/'manifest.json')
    data_path=next(Path(p) for p in manifest['source_sha256'] if p.endswith('presentation_20261110/train.jsonl'))
    documents=load_documents(data_path)
    def pair_key(context,target):
        return (tuple((r['token'],r['pos']) for r in context),(target['token'],target['pos']))
    completion=read(root/'completed.json')
    assert completion['decisions']==100 and len(manifest['runs'])==10
    assert all(sha256(Path(p).read_bytes()).hexdigest()==s for p,s in manifest['source_sha256'].items())
    budget=read(root/'budget.json')
    expected_calls={f"{r['name']}/step_{i:03d}" for r in manifest['runs'] for i in range(10)}
    assert expected_calls.issubset(budget['calls'])
    unresolved={k:v for k,v in budget['calls'].items() if k not in expected_calls}
    for identifier,entry in unresolved.items():
        assert entry['state']=='unresolved' and entry['original_identifier'] in expected_calls
        assert identifier.startswith(entry['original_identifier']+'/unresolved_')
        assert entry['accounted_usd']==entry['reserved_usd']
        directory=root/entry['original_identifier']
        plans=[read(p) for p in directory.glob('uncertain_recovery_*.json')]
        plan=next(p for p in plans if p['archive_identifier']==identifier)
        assert plan['prepared'] and plan['request_sha256']==entry['request_sha256']
        assert (root/plan['archive_directory']).is_dir()
    evaluation=read(root/'evaluation.json');samples=read(root/'samples.json')
    initial=Storyformer.load(root/'initial_model.json')
    initial_hash=model_fingerprint(initial)
    assert initial_hash==manifest['initial_model_sha256']
    prefix_hashes=set();rows=[];total_observations=0;errors=[]
    for config in manifest['runs']:
        name=config['name'];directory=root/name
        before=control_before=initial_hash
        decisions=[]
        for i in range(10):
            step=directory/f'step_{i:03d}';decision=read(step/'decision.json')
            assert decision['document_indices']==config['document_indices'][i*config['batch_size']:(i+1)*config['batch_size']]
            assert decision['before_model_sha256']==before and decision['control_before_sha256']==control_before
            before=decision['selected_model_sha256'];control_before=decision['control_sha256']
            assert model_fingerprint(Storyformer.load(step/'model.json'))==before
            assert model_fingerprint(Storyformer.load(step/'control.json'))==control_before
            receipt=read(step/'receipt.json');request=read(step/'request.json')
            assert receipt==budget['calls'][str(step.relative_to(root))]
            assert receipt['state']=='settled' and receipt['model']=='gpt-6-luna' and receipt['service_tier']=='flex'
            assert request['service_tier']=='flex' and request['prompt_cache_options']=={'mode':'explicit','ttl':'30m'}
            assert receipt['request_sha256']==fingerprint(request)
            prefix_hashes.add(fingerprint([request['input'][0],request['prompt_cache_key']]))
            evidence=json.loads(request['input'][1]['content'])
            assert evidence['base_model_sha256']==evidence['patch_template']['base_model_sha256']
            assert evidence['batch_document_count']==config['batch_size']
            docs=[documents[j] for j in decision['document_indices']]
            expected_targets=sum(len(doc) for doc in docs)
            assert decision['targets']==expected_targets
            assert decision['backward']['steps']==1
            assert evidence['batch_summary']['targets']==expected_targets
            assert all(v['current']['targets']==expected_targets for v in decision['scores'].values())
            legal={pair_key(doc[max(0,k-initial.context_size):k],target) for doc in docs for k,target in enumerate(doc)}
            assert pair_key(evidence['context'],evidence['target']) in legal
            assert all(pair_key(e['context'],e['target']) in legal for e in evidence['batch_examples'])
            assert evidence['batch_documents']==docs[:evidence['shown_document_count']]
            assert 'free_generation' in evidence
            if i:assert 'candidate_scores' in evidence['previous_decision']
            if decision.get('teacher_error') or decision['error']:
                errors.append(dict(run=name,iteration=i+1,error=decision.get('teacher_error') or decision['error']))
            decisions.append(decision)
        model=Storyformer.load(directory/'final_model.json')
        assert model_fingerprint(model)==before
        assert model_fingerprint(Storyformer.load(directory/'weights_only_model.json'))==control_before
        for split in ('validation','test'):
            assert evaluation[split][name+'_teacher']['model_sha256']==before
            assert evaluation[split][name+'_control']['model_sha256']==control_before
        group=[s for s in samples if s['model']==name+'_teacher']
        assert len(group)==5 and {s['seed'] for s in group}==set(range(5))
        assert all(s['model_sha256']==before for s in group)
        counts=Counter(d['adopted'] for d in decisions)
        observations=sum(d['targets'] for d in decisions);total_observations+=observations
        row=dict(run=name,batch_size=config['batch_size'],seed=config['seed'],targets=observations,
                 adoptions=dict(counts),test=evaluation['test'][name+'_teacher'],control=evaluation['test'][name+'_control'],
                 validation=evaluation['validation'][name+'_teacher'],framing=sum(s['complete_framing'] for s in group),
                 ended=sum(s['ended'] for s in group),heads=[h.neuron.name for l in model.layers for h in l.heads if h],
                 new_fields=sorted(set(model.features)-set(initial.features)),
                 added_output_rules=sum(len(n.rules) for n in model.projection.neurons.values())-sum(len(n.rules) for n in initial.projection.neurons.values()))
        rows.append(row)
    assert len(prefix_hashes)==1
    for split in ('validation','test'):
        assert len(evaluation[split])==21 and evaluation[split]['initial']['model_sha256']==initial_hash
    assert len(samples)==55
    calls=[budget['calls'][k] for k in sorted(expected_calls)]
    attempts=[read(p) for p in root.glob('run_*/step_*/**/error.json')]
    audit=dict(runs=10,iterations_per_run=10,completed_teacher_calls=100,observations=total_observations,
        model='gpt-6-luna',service_tier='flex',unchanged_sources=True,verified_checkpoint_chains=True,
        cache_hit_calls=sum(c['usage']['input_tokens_details']['cached_tokens']>0 for c in calls),
        input_tokens=sum(c['usage']['input_tokens'] for c in calls),output_tokens=sum(c['usage']['output_tokens'] for c in calls),
        cached_tokens=sum(c['usage']['input_tokens_details']['cached_tokens'] for c in calls),
        cache_write_tokens=sum(c['usage']['input_tokens_details'].get('cache_write_tokens',0) for c in calls),
        estimated_cost_usd=sum(c['estimated_cost_usd'] for c in calls),
        accounted_usd=sum(c['accounted_usd'] for c in budget['calls'].values()),
        unresolved_reservations=unresolved,unresolved_upper_usd=sum(c['accounted_usd'] for c in unresolved.values()),prior_accounted_usd=manifest['prior_accounted_usd'],
        transport_errors=attempts,proposal_errors=errors)
    assert audit['accounted_usd']+audit['prior_accounted_usd']<=10
    atomic_json(root/'audit.json',audit);atomic_json(root/'summary.json',rows)
    def metric(row,key,percent=False):
        return f"{row[key]:.1%}" if percent and key in row else f"{row[key]:.3f}" if key in row else 'ERROR'
    lines=['# Ten larger continuation runs','',
        'Ten independent runs completed ten training iterations each, starting from the best previous four-story checkpoint. Five seeds use eight stories per iteration; five use sixteen. All positions contribute to one output-weight gradient per iteration, followed by one live Luna grammar proposal and a full-batch/replay gate.','',
        'The runs share the 192-story synthetic token/POS training pool. Their 1,200 story exposures overlap across runs; these are not 1,200 unique new stories. Within a run, stories are sampled without replacement. Paired batch sizes share a shuffled order. Model capacity stays context 32, one layer and sixteen head slots.','',
        'The teacher now receives the previous candidate scores and a short pre-update generated sample. Generated tokens are diagnostic, never gold targets. The gate remains next-token likelihood plus replay protection; it does not directly optimize story quality. This combined protocol change is not an isolated ablation of batch size or feedback.','',
        'All training was frozen before evaluating validation/test rows 24–47 (24 stories each), outside the earlier online pilot subsets. Controls start from the identical checkpoint and receive the same ten weight updates and replay gate, without new teacher edits. Runtime generation makes no LLM calls.','',
        '## Held-out results','',
        f"Starting checkpoint on this test slice: NLL **{metric(evaluation['test']['initial'],'joint_nll')}**, accuracy **{metric(evaluation['test']['initial'],'accuracy',True)}**.",'',
        '| Run | Stories/step | Targets | Teacher edits | Test NLL | Accuracy | Control NLL | Complete framing |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| [{r['run']}]({r['run']}/training_report.json) | {r['batch_size']} | {r['targets']} | {r['adoptions'].get('teacher',0)}/10 | {metric(r['test'],'joint_nll')} | {metric(r['test'],'accuracy',True)} | {metric(r['control'],'joint_nll')} | {r['framing']}/5 |")
    lines += ['', 'Five-run averages (with observed range; not a confidence interval):','']
    for size in (8,16):
        valid=[r for r in rows if r['batch_size']==size and 'accuracy' in r['test']]
        if valid:
            acc=[r['test']['accuracy'] for r in valid];loss=[r['test']['joint_nll'] for r in valid]
            lines.append(f"- Batch {size}: accuracy {statistics.mean(acc):.1%} ({min(acc):.1%}–{max(acc):.1%}); NLL {statistics.mean(loss):.3f} ({min(loss):.3f}–{max(loss):.3f}), {len(valid)}/5 evaluable runs.")
    lines += ['', 'All five samples from every teacher model, including failures, are included below. The exact-template framing check is not a general narrative-quality judge.','', '## Learned structure','',
              '| Run | Added output rules | Occupied heads | New fields |','|---|---:|---:|---|']
    for r in rows:lines.append(f"| {r['run']} | {r['added_output_rules']} | {len(r['heads'])} | {', '.join(r['new_fields']) or 'none'} |")
    lines+=['','## Unfiltered generations','']
    for name in ['initial']+[r['run']+'_teacher' for r in rows]:
        lines += [f'### {name}','']
        for s in [s for s in samples if s['model']==name]:
            lines += [f"Seed {s['seed']}:",'','```text',s.get('text',s.get('error','')),'```','']
    lines += ['## Accounting and verification','',
        f"All 100 logical teacher steps have settled Luna/Flex responses. Prefix-cache hits: {audit['cache_hit_calls']}/100; cached input {audit['cached_tokens']:,} tokens; cache writes {audit['cache_write_tokens']:,}. Total input {audit['input_tokens']:,}, output including reasoning {audit['output_tokens']:,} tokens.",'',
        f"New estimated cost: **${audit['estimated_cost_usd']:.6f}**. Conservative new accounting: ${audit['accounted_usd']:.6f}; including earlier experiments: **${audit['accounted_usd']+audit['prior_accounted_usd']:.6f}**, below $10. Known-response usage estimates exclude any unknown charges; unresolved attempts retain their entire conservative reservation in the total. Usage estimates are not a billing invoice. [Official Luna pricing](https://developers.openai.com/api/docs/models/gpt-6-luna) was checked before dispatch.",'',
        f"Unresolved earlier attempts: {len(unresolved)}, with ${audit['unresolved_upper_usd']:.6f} reserved conservatively. These attempts were preserved and any retry was separately reserved. Proposal/validation errors recorded: {len(errors)}. Transport failures/rejections: {len(attempts)}; the journal distinguishes definite free retryable failures from unknown outcomes. Original attempts are preserved. [Audit](audit.json), [budget](budget.json), [evaluation](evaluation.json), [summary](summary.json).",'',
        'The audit checks all 100 model/control transitions, source hashes, served model/tier, request fingerprints, cache-prefix identity, every evaluation checkpoint, and all 55 generations. Per-step folders preserve evidence, replay examples, proposal, receipt, decision and both checkpoints. The test suite passed 157 tests before live execution and 159 tests after adding unknown-outcome recovery checks.','',
        '```sh','.venv/bin/python -m storyformers.online_scale \\','  --out storyformers/runs/online_scale_20261119 --concurrency 3',
        '.venv/bin/python -m storyformers.scale_report storyformers/runs/online_scale_20261119','```','',
        'The first command resumes this suite without repeating committed steps. A different directory creates new paid requests and its own ledger; the spending limit is per suite, not an account-wide limit.','']
    (root/'REPORT.md').write_text('\n'.join(lines))
    print(json.dumps(audit,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path)
    report(parser.parse_args().root)
