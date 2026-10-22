#!/usr/bin/env python3
"""Author independent Luna/Flex worlds and grade three random stories per world.

Keeps the compact cache-only engine and both existing judge rubrics unchanged.
Failed authoring attempts remain visible; replacements are based on mechanical
acceptance only, never on a judge's score. No LLM calls occur during sampling.
"""
import argparse
import asyncio
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import random
import shutil
import time

import compact_workshop as cw
import factory as f
import workshop as w
import conversation_quality as cq
from qa import enrich, chat_records
from qa_checks import measure

ROOT = Path(__file__).resolve().parent
EXTRA_SOURCES = ['world_batch.py', 'qa_checks.py', 'evaluation/conversation_quality.py',
                 'evaluation/openai_world_set_quality.py', 'evaluation/openai_story_quality.py',
                 'evaluation/trial_cost.py']


def write_rows(path, rows):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))


def briefs_for(seed, max_attempts_per_theme):
    rng = random.Random(seed)
    return [dict(index=attempt * len(f.THEATERS) + i, seed=rng.getrandbits(32),
                 theater=theme, premise=premise, world_id=f'{theme}_{attempt + 1:03d}')
            for attempt in range(max_attempts_per_theme)
            for i, (theme, premise) in enumerate(f.THEATERS)]


def prepare(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    settings = dict(protocol='storyscenes_100_worlds_v1', seed=args.seed,
                    target_worlds=args.per_theme * len(f.THEATERS), per_theme=args.per_theme,
                    max_attempts_per_theme=args.max_attempts_per_theme, stories_per_world=3,
                    selection_seed=777, qa_seed=777, qa_limit=6, qa_pairs=3,
                    cost_profile='cache-only', world_reasoning='medium', prose_reasoning='low',
                    service_tier='flex', author_model='gpt-5.6-luna', judge_model='gpt-5.6-terra',
                    world_budget=args.world_budget, campaign=str(args.campaign.resolve()),
                    selection='three uniform positions from 100, without replacement; duplicates retained',
                    replacement='first mechanically accepted worlds per theme; scores never influence selection')
    path = out / 'settings.json'
    if path.exists() and json.loads(path.read_text()) != settings:
        raise ValueError('Settings changed; choose a new run')
    sources = sorted(set(cw.RUNTIME + cw.AUTHORING + EXTRA_SOURCES))
    hashes = {name: f.digest(ROOT / name) for name in sources}
    saved = out / 'source_hashes.json'
    if saved.exists() and json.loads(saved.read_text()) != hashes:
        raise ValueError('Frozen source changed; choose a new run')
    for folder, names in (('_runtime', cw.RUNTIME), ('_authoring', cw.AUTHORING),
                          ('_evaluation', EXTRA_SOURCES)):
        for name in names:
            destination = out / folder / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and f.digest(destination) != hashes[name]:
                raise ValueError('Frozen snapshot changed: ' + str(destination))
            if not destination.exists(): shutil.copyfile(ROOT / name, destination)
    f.save(saved, hashes)
    f.save(path, settings)
    briefs = briefs_for(args.seed, args.max_attempts_per_theme)
    manifest = out / 'briefs.json'
    if manifest.exists() and json.loads(manifest.read_text()) != briefs:
        raise ValueError('Brief manifest changed')
    f.save(manifest, briefs)
    return out, briefs


def normalize_identical_duplicates(value):
    """Only collapse identical duplicate QA ratings, retaining an audit trail.

    Missing IDs and differing ratings still fail the existing strict validator.
    """
    result = deepcopy(value)
    removed = []
    for story in result.get('stories', []):
        seen, unique = {}, []
        for conversation in story.get('conversations', []):
            key = conversation.get('id')
            if key in seen and seen[key] == conversation:
                removed.append(dict(story=story.get('id'), conversation=key))
            else:
                seen[key] = conversation
                unique.append(conversation)
        story['conversations'] = unique
    return result, removed


async def selected_samples(world):
    pool = [json.loads(line) for line in (world / 'samples.jsonl').read_text().splitlines()]
    item = f.quality.select_set(world.name, pool, 777, count=3)
    if len(item['stories']) != 3: raise ValueError('Need exactly three selected stories')
    seeds = [pool[s['source_index']]['seed'] for s in item['stories']]
    executed = await w.execute(world, seeds, True)
    rows = []
    for selected, row in zip(item['stories'], executed):
        if selected['story'] != row['story']:
            raise ValueError('Selected story differs from frozen replay')
        row.update(world=world.name, sample_id=f'{world.name}:{row["seed"]}')
        selected['sample_id'] = row['sample_id']
        rows.append(enrich(row))
    f.save(world / 'selection.json', item)
    write_rows(world / 'selected_samples.jsonl', rows)
    write_rows(world / 'chat_review.jsonl', [record for row in rows for record in chat_records(row)])
    f.save(world / 'qa_checks.json', measure(rows))
    return item, rows


async def judge(client, budget, world, phase, item, body):
    stage = 'judge_' + phase
    path = world / (stage + '.result.json')
    if path.exists():
        saved = json.loads(path.read_text())
        if saved.get('ok'): return saved
    f.save(world / (stage + '.input.json'), item)
    result = dict(world=world.name, phase=phase, ok=False)
    try:
        if (world.parent / 'STOP').exists(): raise ValueError('Run stopped before judge dispatch')
        raw = await f.api_artifact(client, budget, world, stage, body)
        response = json.loads((world / (stage + '.response.json')).read_text())
        if response.get('service_tier') != 'flex': raise ValueError('Unexpected returned service tier')
        value = json.loads(raw)
        if phase == 'qa':
            value, removed = normalize_identical_duplicates(value)
            if removed:
                f.save(world / (stage + '.normalization.json'), dict(removed=removed, normalized=value))
            assessment = cq.validate(value, item)
        else:
            assessment = f.quality.validate(value, item)
        result.update(ok=True, assessment=assessment)
    except Exception as exc:
        result['error'] = str(exc)
    response_path = world / (stage + '.response.json')
    if response_path.exists():
        response = json.loads(response_path.read_text())
        result['response'] = {k: response.get(k) for k in ('id', 'model', 'status', 'service_tier', 'usage')}
    f.save(path, result)
    print(f'{world.name}: {stage} {"OK" if result["ok"] else "FAILED (see artifact)"}', flush=True)
    return result


def report(out, ledger):
    attempts, accepted, story_results, qa_results, samples, responses = [], [], [], [], [], []
    for brief in json.loads((out / 'briefs.json').read_text()):
        world = out / brief['world_id']
        if not world.exists(): continue
        summary_path = world / 'summary.json'
        failure_path = world / 'failure.json'
        row = dict(world=world.name, theme=brief['theater'], ok=False, status='in_progress')
        if summary_path.exists():
            row.update(json.loads(summary_path.read_text()), status='accepted')
            accepted.append(row)
        elif failure_path.exists(): row.update(json.loads(failure_path.read_text()), status='failed')
        attempts.append(row)
        for phase, results in (('story', story_results), ('qa', qa_results)):
            path = world / f'judge_{phase}.result.json'
            if path.exists(): results.append(json.loads(path.read_text()))
        path = world / 'selected_samples.jsonl'
        if path.exists(): samples.extend(json.loads(line) for line in path.read_text().splitlines())
        for path in world.glob('*.response.json'):
            response = json.loads(path.read_text())
            phase = 'story' if path.name.startswith('judge_story') else 'qa' if path.name.startswith('judge_qa') else 'authoring'
            responses.append(dict(world=world.name, phase=phase,
                response={k: response.get(k) for k in ('id', 'model', 'status', 'service_tier', 'usage')}))
    story_summary = f.quality.summarize([dict(r, **r.get('assessment', {})) for r in story_results])
    entries = [e for e in ledger.entries if e['label'].startswith(out.name + '/')]
    report = dict(target_worlds=json.loads((out / 'settings.json').read_text())['target_worlds'],
        attempted_worlds=len(attempts), accepted_worlds=len(accepted),
        failed_worlds=sum(r['status'] == 'failed' for r in attempts),
        in_progress=sum(r['status'] == 'in_progress' for r in attempts),
        accepted_per_theme=dict(Counter(r['theme'] for r in accepted)),
        story_quality=story_summary, qa_quality=cq.summarize(qa_results),
        selected_stories=len(samples), sampled_stories=sum(r['samples'] for r in accepted),
        cost=f.trial_cost.summarize(responses),
        phase_costs={phase:f.trial_cost.summarize([r for r in responses if r['phase'] == phase])
                     for phase in ('authoring', 'story', 'qa')},
        returned_tiers=dict(Counter(r['response'].get('service_tier') for r in responses)),
        cache=dict(read_tokens=sum((r['response'].get('usage') or {}).get('input_tokens_details', {}).get('cached_tokens', 0) for r in responses),
                   write_tokens=sum((r['response'].get('usage') or {}).get('input_tokens_details', {}).get('cache_write_tokens', 0) for r in responses)),
        unresolved_reservation_usd=sum(e['reserved_usd'] for e in entries if e['status'] != 'returned' or not e.get('cost', {}).get('known')),
        campaign_committed_upper_usd=sum(e['reserved_usd'] for e in ledger.entries),
        failed_judges=[dict(world=r['world'], phase=r['phase'], error=r.get('error'))
                       for r in story_results + qa_results if not r.get('ok')])
    f.save(out / 'summary.json', attempts)
    f.save(out / 'evaluation_summary.json', report)
    write_rows(out / 'selected_samples.jsonl', samples)
    write_rows(out / 'assessments.jsonl', story_results + qa_results)
    return report


async def run(args):
    from openai import AsyncOpenAI
    out, briefs = prepare(args)
    args.campaign.mkdir(parents=True, exist_ok=True)
    ledger = f.Budget(args.campaign.resolve() / 'budget.json', 15)
    f.load_key(args.api_key_file)
    contract = (out / '_authoring' / 'AUTHORING_COMPACT.md').read_text()
    semaphore = asyncio.Semaphore(args.concurrency)
    started = time.monotonic()
    async with AsyncOpenAI(base_url='https://api.openai.com/v1', timeout=900, max_retries=0) as client:
        async def theme_run(theme):
            completed = 0
            for brief in (b for b in briefs if b['theater'] == theme):
                if completed >= args.per_theme or (out / 'STOP').exists(): break
                world = out / brief['world_id']
                failure = world / 'failure.json'
                if failure.exists():
                    if json.loads(failure.read_text()).get('paid_stage_stopped'): break
                    continue
                async with semaphore:
                    if (out / 'STOP').exists(): break
                    try:
                        await cw.world_run(client, w.WorldBudget(ledger, world, args.world_budget),
                                           world, brief, contract, cost_profile='cache-only')
                    except Exception as exc:
                        stopped = isinstance(exc, cw.PaidStageStopped)
                        world.mkdir(exist_ok=True)
                        f.save(failure, dict(world=world.name, ok=False, error=str(exc), paid_stage_stopped=stopped))
                        print(f'{world.name}: FAILED {exc}', flush=True)
                        report(out, ledger)
                        if stopped: break
                        continue
                    completed += 1
                    try:
                        item, rows = await selected_samples(world)
                        budget = w.WorldBudget(ledger, world, .40)
                        await judge(client, budget, world, 'story', item,
                                    f.quality.request_body(item, cache_prompts=True))
                        qa_rows = [row for row in rows if row['conversations']]
                        if qa_rows:
                            body = cq.request_body(qa_rows)
                            counts = [len(row['conversations']) for row in qa_rows]
                            body['text']['format']['schema']['properties']['stories']['items']['properties']['conversations'].update(
                                minItems=min(counts), maxItems=max(counts))
                            await judge(client, budget, world, 'qa', qa_rows, body)
                    except Exception as exc:
                        f.save(world / 'evaluation_failure.json', dict(error=str(exc)))
                        print(f'{world.name}: EVALUATION FAILED {exc}', flush=True)
                    current = report(out, ledger)
                    print(f'PROGRESS {current["accepted_worlds"]}/{current["target_worlds"]} worlds; '
                          f'{current["story_quality"]["rated_stories"]} stories graded; '
                          f'run cost ${current["cost"]["usd_high"]:.4f}; elapsed {time.monotonic()-started:.0f}s', flush=True)
        await asyncio.gather(*(theme_run(theme) for theme, _ in f.THEATERS))
    final = report(out, ledger)
    return int(final['accepted_worlds'] != final['target_worlds'] or
               final['story_quality']['rated_stories'] != final['target_worlds'] * 3 or bool(final['failed_judges']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--campaign', type=Path, default=ROOT / 'improvements/20260908')
    parser.add_argument('--seed', type=int, default=2026090801)
    parser.add_argument('--per-theme', type=int, default=10)
    parser.add_argument('--max-attempts-per-theme', type=int, default=40)
    parser.add_argument('--concurrency', type=int, default=10)
    parser.add_argument('--world-budget', type=float, default=.15)
    parser.add_argument('--api-key-file', type=Path)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.per_theme <= args.max_attempts_per_theme or args.concurrency < 1 or not 0 < args.world_budget <= .4:
        parser.error('Invalid count, concurrency or world budget')
    if args.prepare_only:
        prepare(args)
        return 0
    return asyncio.run(run(args))


if __name__ == '__main__': raise SystemExit(main())
