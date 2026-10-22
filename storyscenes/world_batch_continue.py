#!/usr/bin/env python3
"""Drain/resume a frozen world batch with a work-conserving quota scheduler.

Run only after its previous process has exited. No uncertain request is retried:
its world is quarantined, the reservation is retained, and the next predeclared
seed is used. Saved completed responses resume without a new API call.
"""
import argparse
import asyncio
from collections import Counter
import json
from pathlib import Path
import shutil

import world_batch as b


def resume_pauses(out):
    audit = []
    for world in sorted(p for p in out.iterdir() if p.is_dir() and (p / 'seed.json').exists()):
        failure = world / 'failure.json'
        if not failure.exists(): continue
        error = json.loads(failure.read_text())
        if not error.get('paid_stage_stopped'): continue
        unknown, incomplete = [], []
        for request in world.glob('*.request.json'):
            if request.name.startswith('judge_'): continue
            response = request.with_name(request.name.replace('.request.json', '.response.json'))
            if not response.exists(): unknown.append(request.name)
            elif json.loads(response.read_text()).get('status') != 'completed': incomplete.append(response.name)
        resumable = ('Run stopped before dispatch' in error['error'] and not unknown and not incomplete)
        record = dict(world=world.name, original_failure=error, unknown_requests=unknown,
                      incomplete_responses=incomplete,
                      action='resume_saved_responses' if resumable else 'quarantine_and_use_next_predeclared_seed',
                      reservation_policy='retain every original reservation; never infer zero billing from missing response')
        if resumable:
            failure.rename(world / 'drain_pause.json')
        else:
            b.f.save(world / 'replacement_provenance.json', record)
        audit.append(record)
    path = out / 'continuation_audit.json'
    old = json.loads(path.read_text()) if path.exists() else []
    b.f.save(path, old + audit)


async def run(args):
    from openai import AsyncOpenAI
    out, briefs = b.prepare(args)
    resume_pauses(out)
    (out / 'STOP').unlink(missing_ok=True)
    source = Path(__file__).resolve()
    snapshot = out / '_scheduling' / source.name
    snapshot.parent.mkdir(exist_ok=True)
    if snapshot.exists() and b.f.digest(snapshot) != b.f.digest(source):
        raise ValueError('Continuation scheduler changed')
    if not snapshot.exists(): shutil.copyfile(source, snapshot)
    ledger = b.f.Budget(args.campaign.resolve() / 'budget.json', 15)
    b.f.load_key(args.api_key_file)
    contract = (out / '_authoring' / 'AUTHORING_COMPACT.md').read_text()
    completed = Counter()
    used = set()
    evaluations = []
    for brief in briefs:
        world = out / brief['world_id']
        if (world / 'summary.json').exists():
            completed[brief['theater']] += 1
            used.add(world.name)
            if any(not (world / f'judge_{phase}.result.json').exists() or
                   not json.loads((world / f'judge_{phase}.result.json').read_text()).get('ok')
                   for phase in ('story', 'qa')):
                evaluations.append(brief)
        elif (world / 'failure.json').exists(): used.add(world.name)
    inflight = Counter()
    pending = {}
    halted = False
    consecutive_transport_failures = 0

    def next_job():
        if halted or (out / 'STOP').exists(): return None
        if evaluations: return evaluations.pop(0), False
        available = [brief for brief in briefs if brief['world_id'] not in used
                     and completed[brief['theater']] + inflight[brief['theater']] < args.per_theme]
        if not available: return None
        # Catch up lagging themes, without exceeding their accepted+pending quota.
        brief = min(available, key=lambda x: (completed[x['theater']] + inflight[x['theater']], x['index']))
        used.add(brief['world_id'])
        inflight[brief['theater']] += 1
        return brief, True

    async with AsyncOpenAI(base_url='https://api.openai.com/v1', timeout=900, max_retries=0) as client:
        async def one(brief, author):
            world = out / brief['world_id']
            if author:
                try:
                    await b.cw.world_run(client, b.w.WorldBudget(ledger, world, args.world_budget),
                        world, brief, contract, cost_profile='cache-only')
                except Exception as exc:
                    world.mkdir(exist_ok=True)
                    stopped = isinstance(exc, b.cw.PaidStageStopped)
                    b.f.save(world / 'failure.json', dict(world=world.name, ok=False, error=str(exc), paid_stage_stopped=stopped))
                    print(f'{world.name}: FAILED {exc}', flush=True)
                    if stopped:
                        b.f.save(world / 'replacement_provenance.json', dict(
                            action='quarantined; next predeclared seed may be used',
                            error=str(exc), reservation_policy='original reservations remain held; no request retry'))
                    return dict(accepted=False, error=str(exc), transport='Connection error' in str(exc) or 'timed out' in str(exc))
            try:
                item, rows = await b.selected_samples(world)
                budget = b.w.WorldBudget(ledger, world, .40)
                await b.judge(client, budget, world, 'story', item, b.f.quality.request_body(item, cache_prompts=True))
                qa_rows = [row for row in rows if row['conversations']]
                if qa_rows:
                    body = b.cq.request_body(qa_rows)
                    counts = [len(row['conversations']) for row in qa_rows]
                    body['text']['format']['schema']['properties']['stories']['items']['properties']['conversations'].update(
                        minItems=min(counts), maxItems=max(counts))
                    await b.judge(client, budget, world, 'qa', qa_rows, body)
            except Exception as exc:
                b.f.save(world / 'evaluation_failure.json', dict(error=str(exc)))
                print(f'{world.name}: EVALUATION FAILED {exc}', flush=True)
            return dict(accepted=True, transport=False)

        while True:
            while len(pending) < args.concurrency:
                job = next_job()
                if job is None: break
                brief, author = job
                pending[asyncio.create_task(one(brief, author))] = job
            if not pending: break
            done, _ = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                brief, author = pending.pop(task)
                result = task.result()
                if author:
                    inflight[brief['theater']] -= 1
                    completed[brief['theater']] += result['accepted']
                    consecutive_transport_failures = consecutive_transport_failures + 1 if result['transport'] else 0
                if ('Budget cap' in result.get('error', '') or consecutive_transport_failures >= 3):
                    halted = True
                    print('Dispatch paused: campaign cap or repeated transport failures. In-flight calls may finish.', flush=True)
            current = b.report(out, ledger)
            print(f'PROGRESS {current["accepted_worlds"]}/100 worlds; {current["story_quality"]["rated_stories"]} stories graded; '
                  f'run cost ${current["cost"]["usd_high"]:.4f}', flush=True)
    final = b.report(out, ledger)
    return int(final['accepted_worlds'] != final['target_worlds'] or
               final['story_quality']['rated_stories'] != 3 * final['target_worlds'] or bool(final['failed_judges']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--api-key-file', type=Path)
    parser.add_argument('--concurrency', type=int, default=10)
    args = parser.parse_args()
    settings = json.loads((args.out / 'settings.json').read_text())
    for name in ('seed', 'per_theme', 'max_attempts_per_theme', 'world_budget'):
        setattr(args, name, settings[name])
    args.campaign = Path(settings['campaign'])
    if args.concurrency < 1: parser.error('Positive concurrency required')
    raise SystemExit(asyncio.run(run(args)))
