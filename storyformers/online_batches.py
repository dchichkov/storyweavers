"""Ten-round batch-size comparisons with a shared Luna/Flex spending ledger."""

import argparse
import asyncio
from collections import Counter
from copy import deepcopy
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import random
from time import perf_counter

from .annotation import fingerprint
from .grammar import MatchBudgetExceeded
from .learning import LearningBatch
from .neuron_review import model_fingerprint
from .neuron_spec import neuron_spec
from .online import backward_batch, choose, empty_patch, observe, packet, score
from .online_experiment import ROOT, DATA, CHECKPOINT, bootstrap, cases
from .online_teacher import Teacher, TeacherResponseError, atomic_json
from .presentation import framing_checks, render
from .refine import load_documents
from .transformer import Storyformer

BATCH_INSTRUCTIONS = """
BATCH MODE (supersedes the one-observation framing above):
One backward pass has now used ALL causal targets in batch_summary, each with
its own prefix. context/target identify one representative error, not the only
training observation. batch_examples includes high-loss and structural-boundary
examples; their selection is not a frequency estimate. Use batch_summary and
batch_target_counts for frequencies. Propose one compact repair that improves
mean loss over the entire batch, while retaining earlier replay behavior.
You may derive reusable features and revise heads plus output consumers when
the batch supports that abstraction. Do not assert story phases from future
words or gold labels. Ordinary word and punctuation rules are also valid.
No held-out examples enter this packet. batch_documents are already revealed
training stories, with only token/POS records; each learned grammar still sees
only its own causal prefix at runtime. Use these stories to understand repeated
structure; do not copy whole documents into grammar rules.
"""


def batch_packet(weighted, pairs, before, gradient, replay, documents, previous):
    learner = LearningBatch(weighted, pairs=pairs)
    summary = learner.report(max_examples=12)
    # Hard errors plus starts/separators/ends: do not hide structural evidence
    # behind a long list of interchangeable low-probability lexical choices.
    examples = summary.pop('high_loss_examples')
    compact = [dict(context=e['context'], target=e['target'], count=e['count'],
                    probability_after_gradient=e['probability']) for e in examples[:8]]
    selected = {fingerprint([e['context'], e['target']]) for e in compact}
    for context, target in pairs:
        if not context or target['token'] in ('\n\n', '<END>'):
            key = fingerprint([context, target])
            if key not in selected and len(compact) < 16:
                compact.append(dict(context=context, target=target))
                selected.add(key)
    worst = examples[0]
    pair = (worst['context'], worst['target'])
    evidence = packet(weighted, pair, observe(before, pair), gradient, replay, previous)
    evidence.update(mode='batch', batch_summary=summary,
                    batch_before_update=score(before, pairs), batch_examples=compact,
                    batch_documents=documents,
                    batch_target_counts=dict(Counter(target['token'] for _, target in pairs)))
    # Expose relevant root definitions with stable rule indices for reweighting.
    for item in examples:
        if len(evidence['output_roots']) >= 8:
            break
        word = item['target']['token']
        evidence['output_roots'][word] = neuron_spec(weighted.projection.neurons[word])
    # The API budget adapter has a conservative byte ceiling. Keep complete
    # definitions, never truncate JSON or rewrite the actual gradient/gate batch.
    def size():
        return len(json.dumps(evidence, ensure_ascii=False).encode())
    while size() > 78000 and len(evidence['batch_examples']) > 4:
        evidence['batch_examples'].pop()
    while size() > 78000 and len(evidence['batch_documents']) > 1:
        evidence['batch_documents'] = evidence['batch_documents'][:-1]
    evidence['shown_document_count'] = len(evidence['batch_documents'])
    evidence['batch_document_count'] = len(documents)
    return evidence


async def train_batches(out, initial, documents, indices, batch_size, anchors, teacher, *, feedback=False):
    out.mkdir(exist_ok=True)
    model, control = deepcopy(initial), deepcopy(initial)
    decisions, seen, previous = [], [], None
    started = perf_counter()
    for iteration in range(10):
        ids = indices[iteration * batch_size:(iteration + 1) * batch_size]
        batch_documents = [documents[i] for i in ids]
        pairs = cases(batch_documents)
        # Deterministic, bounded replay with both old anchors and past batches.
        replay = anchors + random.Random(9100 + iteration).sample(seen, min(64, len(seen)))
        directory = out / f'step_{iteration:03d}'
        directory.mkdir(exist_ok=True)
        if (directory / 'decision.json').exists():
            decision = json.loads((directory / 'decision.json').read_text())
            if (decision['before_model_sha256'] != model_fingerprint(model)
                    or decision['control_before_sha256'] != model_fingerprint(control)
                    or decision['document_indices'] != ids):
                raise ValueError('batch resume mismatch')
            model = Storyformer.load(directory / 'model.json')
            control = Storyformer.load(directory / 'control.json')
            if (model_fingerprint(model) != decision['selected_model_sha256']
                    or model_fingerprint(control) != decision['control_sha256']):
                raise ValueError('batch checkpoint mismatch')
        else:
            before = score(model, pairs)
            weighted, gradient = backward_batch(model, pairs)
            evidence = batch_packet(weighted, pairs, model, gradient, replay, batch_documents, previous)
            if feedback:
                # Diagnostic only: generated tokens are never treated as gold
                # labels, and no held-out document enters teacher feedback.
                try:
                    rows = model.generate([], 40, seed=iteration)
                    evidence['free_generation'] = dict(records=rows, text=render(rows),
                                                       **framing_checks(rows))
                except (ValueError, ArithmeticError, MatchBudgetExceeded) as exc:
                    evidence['free_generation'] = dict(error=f'{type(exc).__name__}: {exc}')
            atomic_json(directory / 'evidence.json', evidence)
            atomic_json(directory / 'replay.json', replay)
            print(f'{out.name} {iteration+1}/10: {len(pairs)} targets, before NLL={before["joint_nll"]:.3f}; teacher...', flush=True)
            teacher_error = None
            try:
                revision = await teacher(evidence, directory)
            except TeacherResponseError as exc:
                teacher_error = str(exc)
                revision = empty_patch(weighted)
            selected, decision = choose(model, weighted, revision, pairs[0], replay, current_pairs=pairs)
            control_weighted, _ = backward_batch(control, pairs)
            control_selected, control_decision = choose(control, control_weighted, empty_patch(control_weighted),
                                                        pairs[0], replay, current_pairs=pairs)
            decision.update(document_indices=ids, targets=len(pairs), prediction_before_update=before,
                            before_model_sha256=model_fingerprint(model), backward=gradient,
                            control_before_sha256=model_fingerprint(control), control_sha256=model_fingerprint(control_selected),
                            weight_control=control_decision['adopted'], teacher_error=teacher_error)
            model, control = selected, control_selected
            model.save(directory / 'model.json')
            control.save(directory / 'control.json')
            atomic_json(directory / 'decision.json', decision)
            print(f'  {out.name}: {decision["adopted"]}; NLL={decision["scores"][decision["adopted"]]["current"]["joint_nll"]:.3f}; error={teacher_error or decision["error"]}', flush=True)
        decisions.append(decision)
        seen.extend(pairs)
        previous = dict(adopted=decision['adopted'], error=decision['teacher_error'] or decision['error'])
        if feedback:
            previous['candidate_scores'] = decision['scores']
            previous['replay_tolerance'] = decision['replay_tolerance']
    model.save(out / 'final_model.json')
    control.save(out / 'weights_only_model.json')
    total = sum(d['targets'] for d in decisions)
    result = dict(batch_stories=batch_size, iterations=10, observations=total,
                  prequential_nll=sum(d['prediction_before_update']['joint_nll'] * d['targets'] for d in decisions) / total,
                  prequential_accuracy=sum(d['prediction_before_update']['accuracy'] * d['targets'] for d in decisions) / total,
                  adoptions=dict(Counter(d['adopted'] for d in decisions)),
                  training_seconds_this_invocation=perf_counter()-started,
                  final_model_sha256=model_fingerprint(model), control_sha256=model_fingerprint(control))
    atomic_json(out / 'training_report.json', result)
    return model, control


async def run(out):
    out.mkdir(parents=True, exist_ok=True)
    with (out / '.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        prior_path = ROOT / 'runs/online_20261115_live/budget.json'
        prior = json.loads(prior_path.read_text())
        prior_spend = sum(r['accounted_usd'] for r in prior['calls'].values())
        paths = [CHECKPOINT, DATA/'train.jsonl', DATA/'validation.jsonl', DATA/'test.jsonl',
                 ROOT/'runs/induction_baseline/train.jsonl', prior_path]
        sources = {str(p): sha256(p.read_bytes()).hexdigest() for p in paths}
        documents = load_documents(DATA/'train.jsonl')
        vocabulary = [dict(token=w, pos=p) for w,p in sorted({(r['token'],r['pos']) for d in documents for r in d})]
        initial = bootstrap(CHECKPOINT, vocabulary)
        anchors = cases(load_documents(ROOT/'runs/induction_baseline/train.jsonl')[:2])
        indices = list(range(len(documents)))
        random.Random(20261115).shuffle(indices)
        manifest = dict(batch_sizes=[1,4,12], iterations=10, document_order=indices[:120],
                        initial_model_sha256=model_fingerprint(initial), source_sha256=sources,
                        model='gpt-6-luna', service_tier='flex', previous_accounted_usd=prior_spend,
                        remaining_budget_usd=10-prior_spend, evaluation_indices=list(range(8,24)),
                        policy='All positions in each batch; one averaged gradient; one teacher patch; full batch and replay gate. '
                               'Independent initial checkpoint per size; nested training-document order. '
                               'Evaluate all runs only after all training is frozen.')
        if (out/'manifest.json').exists():
            if json.loads((out/'manifest.json').read_text()) != manifest:
                raise ValueError('run manifest changed')
        elif any(p.name != '.lock' for p in out.iterdir()):
            raise ValueError('new batch suite requires an empty directory')
        atomic_json(out/'manifest.json', manifest)
        initial.save(out/'initial_model.json')
        from openai import AsyncOpenAI
        key = os.environ.get('OPENAI_API_KEY') or (ROOT.parent/'.API_KEY').read_text().strip()
        async with AsyncOpenAI(api_key=key, base_url='https://api.openai.com/v1', timeout=300, max_retries=0) as client:
            teacher = Teacher(client, out, 'gpt-6-luna', vocabulary, budget=10-prior_spend, max_output_tokens=8192)
            teacher.prefix += BATCH_INSTRUCTIONS
            teacher.key = 'storyformers-batches-v1:' + fingerprint([teacher.prefix, teacher.model])[:24]
            # Independent model branches overlap teacher waits, with a shared
            # asyncio budget lock and immutable per-branch patch fingerprints.
            trained = await asyncio.gather(*(train_batches(out/f'batch_{size:02d}', initial, documents,
                            indices, size, anchors, teacher) for size in manifest['batch_sizes']))
        evaluation = {}
        frozen = [model_fingerprint(m) for pair in trained for m in pair]
        for split in ('validation','test'):
            pairs = cases(load_documents(DATA/f'{split}.jsonl')[8:24])
            evaluation[split] = {'initial': score(initial,pairs)}
            for size,(model,control) in zip(manifest['batch_sizes'],trained):
                print(f'Evaluating {split} batch {size}: {len(pairs)} targets', flush=True)
                evaluation[split][f'batch_{size:02d}'] = dict(teacher=score(model,pairs),weights_only=score(control,pairs))
            atomic_json(out/'evaluation.json',evaluation)
        samples=[]
        candidates=[('initial',initial)] + [(f'batch_{size:02d}_{name}',m)
            for size,pair in zip(manifest['batch_sizes'],trained) for name,m in zip(('teacher','weights_only'),pair)]
        for name,model in candidates:
            for seed in range(5):
                rows=model.generate([],64,seed=seed)
                samples.append(dict(model=name,seed=seed,text=render(rows),records=rows,**framing_checks(rows)))
        atomic_json(out/'samples.json',samples)
        assert frozen == [model_fingerprint(m) for pair in trained for m in pair]
        assert all(sha256(Path(p).read_bytes()).hexdigest()==s for p,s in sources.items())
        print('All three ten-iteration runs, frozen evaluation and samples completed.',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    asyncio.run(run(parser.parse_args().out))


if __name__=='__main__':
    main()
