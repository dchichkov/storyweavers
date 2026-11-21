"""Ten larger Luna/Flex continuation runs, ten updates each, one shared budget."""

import argparse
import asyncio
from copy import deepcopy
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import time
import uuid

import httpx

from .annotation import fingerprint, sdk_kwargs
from .grammar import MatchBudgetExceeded
from .neuron_review import model_fingerprint
from .online import score
from .online_batches import BATCH_INSTRUCTIONS, train_batches
from .online_experiment import ROOT, DATA, cases
from .online_teacher import Teacher, atomic_json
from .presentation import framing_checks, render
from .refine import load_documents
from .transformer import Storyformer

CHECKPOINT = ROOT/'runs/online_batches_20261115/batch_04/final_model.json'
FEEDBACK = """
CONTINUATION EXPERIMENT:
previous_decision.candidate_scores contains current-batch loss, replay loss,
conflicts and syntax complexity for the preceding alternatives. Learn from
rejected candidates: distinguish replay regression from insufficient batch
improvement or a complexity penalty. free_generation is an unprompted sample
from the PRE-UPDATE model, not gold training data. Look for systematic generation
failures while preserving valid alternatives. You may propose grammar/head
repairs grounded in the revealed training documents; never treat the generated
sample's tokens as labels or claim that the teacher has passed a gate. This
sample is diagnostic; the acceptance gate still measures current-batch and
replay likelihood, not human story quality.
"""


def before_send_failure(error):
    """Only connection establishment failures are known not to have sent HTTP."""
    current, seen = error, set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, (httpx.ConnectError, httpx.ConnectTimeout)):
            return True
        current = current.__cause__
    return False


async def safe_dispatch(directory, body, client, retries=2):
    """Retry definite free Flex/connect failures; ambiguous outcomes stay blocked."""
    response_path = directory/'response.json'
    if response_path.exists():
        return json.loads(response_path.read_text())
    attempts = directory/'attempts'
    attempts.mkdir(exist_ok=True)
    previous = sorted(attempts.iterdir())
    identifier = str(uuid.uuid4())
    if previous:
        last = previous[-1]
        error = json.loads((last/'error.json').read_text()) if (last/'error.json').exists() else {}
        if not (error.get('before_send') or (error.get('status') == 429 and error.get('code') == 'flex_unavailable')):
            raise RuntimeError('ambiguous previous dispatch; retain reservation and inspect before retry')
        identifier = json.loads((last/'dispatch.json').read_text())['idempotency_key']
    for retry in range(max(5, retries + 1)):
        attempt = attempts/f'{len(list(attempts.iterdir()))+1:03d}'
        attempt.mkdir()
        atomic_json(attempt/'dispatch.json',dict(started_at=time.time(),request_sha256=fingerprint(body),
                                               idempotency_key=identifier))
        started = time.monotonic()
        try:
            response = await client.responses.create(**sdk_kwargs(body),extra_headers={'Idempotency-Key':identifier})
            raw = response.model_dump(mode='json')
            atomic_json(response_path,raw)
            atomic_json(attempt/'completed.json',dict(elapsed_seconds=time.monotonic()-started))
            return raw
        except Exception as exc:
            status,code = getattr(exc,'status_code',None),getattr(exc,'code',None)
            safe = before_send_failure(exc)
            atomic_json(attempt/'error.json',dict(type=type(exc).__name__,status=status,code=code,
                before_send=safe,elapsed_seconds=time.monotonic()-started))
            if not (safe or (status == 429 and code == 'flex_unavailable')) or retry == max(5,retries+1)-1:
                raise
            print(f'{directory.parent.name}/{directory.name}: retrying definite free failure on Flex',flush=True)
            await asyncio.sleep(min(5*2**retry,30))


class ScaleTeacher(Teacher):
    def request(self, packet):
        data = deepcopy(packet)
        def body():
            result = super(ScaleTeacher,self).request(data)
            result['input'][1]['content'] = json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            return result
        result = body()
        while len(json.dumps(result,ensure_ascii=False).encode()) + 4096 > 118000:
            if data.get('batch_documents'):
                data['batch_documents'].pop()
                data['shown_document_count'] = len(data['batch_documents'])
            elif len(data.get('batch_examples',[])) > 2:
                data['batch_examples'].pop()
            elif len(data['output_roots']) > 1:
                removable = [w for w in data['output_roots'] if w != data['target']['token']]
                del data['output_roots'][removable[-1]]
            else:
                raise ValueError('essential teacher evidence exceeds byte budget')
            result = body()
        return result


def settings():
    documents = load_documents(DATA/'train.jsonl')
    runs = []
    for seed in range(5):
        order = list(range(len(documents)))
        random.Random(20261119+seed).shuffle(order)
        for size in (8,16):
            runs.append(dict(name=f'run_{len(runs)+1:02d}_b{size:02d}',seed=20261119+seed,
                             batch_size=size,document_indices=order[:10*size]))
    return runs


def checked_score(model,pairs):
    try:
        return score(model,pairs)
    except (ValueError,ArithmeticError,MatchBudgetExceeded) as exc:
        return dict(error=f'{type(exc).__name__}: {exc}',targets=len(pairs))


def evaluate(out,manifest):
    """Only after all 100 decisions exist; persist each completed model score."""
    assert all((out/r['name']/f'step_{i:03d}/decision.json').exists() for r in manifest['runs'] for i in range(10))
    path = out/'evaluation.json'
    results = json.loads(path.read_text()) if path.exists() else {}
    for split in ('validation','test'):
        pairs = cases(load_documents(DATA/f'{split}.jsonl')[24:48])
        target = results.setdefault(split,{})
        candidates = [('initial',out/'initial_model.json')]+[(f"{r['name']}_{kind}",out/r['name']/file)
            for r in manifest['runs'] for kind,file in [('teacher','final_model.json'),('control','weights_only_model.json')]]
        for name,checkpoint in candidates:
            model = Storyformer.load(checkpoint)
            digest = model_fingerprint(model)
            if name in target:
                assert target[name]['model_sha256'] == digest
                continue
            print(f'Evaluation {split}/{name}: {len(pairs)} targets',flush=True)
            target[name] = dict(model_sha256=digest,**checked_score(model,pairs))
            atomic_json(path,results)
    sample_path = out/'samples.json'
    samples = json.loads(sample_path.read_text()) if sample_path.exists() else []
    candidates = [('initial',out/'initial_model.json')]+[(f"{r['name']}_teacher",out/r['name']/'final_model.json') for r in manifest['runs']]
    for name,checkpoint in candidates:
        model = Storyformer.load(checkpoint)
        digest = model_fingerprint(model)
        for seed in range(5):
            saved = next((s for s in samples if s['model']==name and s['seed']==seed),None)
            if saved:
                assert saved['model_sha256']==digest
                continue
            try:
                rows = model.generate([],64,seed=seed)
                row = dict(records=rows,text=render(rows),**framing_checks(rows))
            except (ValueError,ArithmeticError,MatchBudgetExceeded) as exc:
                row = dict(error=f'{type(exc).__name__}: {exc}',complete_framing=False,ended=False)
            samples.append(dict(model=name,seed=seed,model_sha256=digest,**row))
            atomic_json(sample_path,samples)
    assert all(sha256(Path(p).read_bytes()).hexdigest()==s for p,s in manifest['source_sha256'].items())
    atomic_json(out/'completed.json',dict(runs=10,iterations_per_run=10,decisions=100,
                                        evaluation_models_per_split=21,samples=len(samples)))
    print('All 100 training iterations, held-out evaluations and generations completed.',flush=True)


async def run(out, *, concurrency=3, evaluate_only=False):
    out.mkdir(parents=True,exist_ok=True)
    with (out/'.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        prior_paths = [ROOT/'runs/online_20261115_live/budget.json',ROOT/'runs/online_batches_20261115/budget.json']
        prior = sum(sum(c['accounted_usd'] for c in json.loads(p.read_text())['calls'].values()) for p in prior_paths)
        sources = [CHECKPOINT,DATA/'train.jsonl',DATA/'validation.jsonl',DATA/'test.jsonl',ROOT/'runs/induction_baseline/train.jsonl',*prior_paths]
        sources += [ROOT/p for p in ['online_scale.py','online_batches.py','online_teacher.py','online.py','learning.py','transformer.py','prompts/online_teacher_v1.txt']]
        manifest = dict(runs=settings(),iterations=10,concurrency=concurrency,model='gpt-6-luna',service_tier='flex',
                        initial_model_sha256=model_fingerprint(Storyformer.load(CHECKPOINT)),prior_accounted_usd=prior,
                        budget_usd=10-prior,source_sha256={str(p):sha256(p.read_bytes()).hexdigest() for p in sources},
                        evaluation_indices=list(range(24,48)),feedback=True,
                        policy='Ten independent continuations of best prior checkpoint. Five seeds each at 8 and 16 stories per step. '
                               'One gradient and one live teacher call per iteration. Full batch/replay gate. '
                               'Generated sample is diagnostic, not a target. All training frozen before any held-out evaluation.')
        if (out/'manifest.json').exists():
            if json.loads((out/'manifest.json').read_text()) != manifest:
                raise ValueError('suite manifest changed; preserve this experiment')
        elif any(p.name != '.lock' for p in out.iterdir()):
            raise ValueError('new suite needs an empty directory')
        atomic_json(out/'manifest.json',manifest)
        if evaluate_only:
            evaluate(out,manifest)
            return
        initial = Storyformer.load(CHECKPOINT)
        initial.save(out/'initial_model.json')
        documents = load_documents(DATA/'train.jsonl')
        vocabulary = [dict(token=w,pos=p) for w,p in sorted({(r['token'],r['pos']) for d in documents for r in d})]
        anchors = cases(load_documents(ROOT/'runs/induction_baseline/train.jsonl')[:2])
        from openai import AsyncOpenAI
        key = os.environ.get('OPENAI_API_KEY') or (ROOT.parent/'.API_KEY').read_text().strip()
        async with AsyncOpenAI(api_key=key,base_url='https://api.openai.com/v1',timeout=600,max_retries=0) as client:
            teacher = ScaleTeacher(client,out,'gpt-6-luna',vocabulary,budget=10-prior,max_output_tokens=8192,dispatch_fn=safe_dispatch)
            teacher.prefix += BATCH_INSTRUCTIONS+FEEDBACK
            teacher.key = 'storyformers-scale-v1:'+fingerprint([teacher.prefix,teacher.model])[:24]
            gate = asyncio.Semaphore(concurrency)
            async def branch(config):
                async with gate:
                    try:
                        return await train_batches(out/config['name'],initial,documents,config['document_indices'],
                                                   config['batch_size'],anchors,teacher,feedback=True)
                    except Exception as exc:
                        atomic_json(out/config['name']/'failure.json',dict(type=type(exc).__name__,message=str(exc)))
                        raise
            results = await asyncio.gather(*(branch(r) for r in manifest['runs']),return_exceptions=True)
            failures = [f"{r['name']}: {type(result).__name__}: {result}" for r,result in zip(manifest['runs'],results) if isinstance(result,BaseException)]
            if failures:
                raise RuntimeError('Other branches preserved; resume after resolving: '+'; '.join(failures))
        evaluate(out,manifest)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--concurrency',type=int,default=3,choices=range(1,5))
    parser.add_argument('--evaluate-only',action='store_true')
    args=parser.parse_args()
    asyncio.run(run(args.out,concurrency=args.concurrency,evaluate_only=args.evaluate_only))


if __name__=='__main__':
    main()
