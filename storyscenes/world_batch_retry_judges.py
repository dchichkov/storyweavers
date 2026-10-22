#!/usr/bin/env python3
"""Explicit, bounded recovery of rejected (429) judge requests, never valid grades.

Run after authoring exits: the campaign ledger must have a single writer.
Original rejection reservations and request artifacts are retained.
"""
import argparse
import asyncio
import json
from pathlib import Path

import world_batch as b


async def run(out, key):
    from openai import AsyncOpenAI
    settings = json.loads((out / 'settings.json').read_text())
    for name, digest in json.loads((out / 'source_hashes.json').read_text()).items():
        if b.f.digest(b.ROOT / name) != digest: raise ValueError('Frozen source changed: ' + name)
    ledger = b.f.Budget(Path(settings['campaign']) / 'budget.json', 15)
    b.f.load_key(key)
    async with AsyncOpenAI(base_url='https://api.openai.com/v1', timeout=900, max_retries=0) as client:
        for path in sorted(out.glob('*/judge_*.result.json')):
            if path.name not in ('judge_story.result.json', 'judge_qa.result.json'): continue
            original = json.loads(path.read_text())
            if original.get('ok') or not original.get('error', '').startswith('Error code: 429'): continue
            world, phase = path.parent, original['phase']
            base = 'judge_' + phase
            body = json.loads((world / (base + '.request.json')).read_text())
            item = json.loads((world / (base + '.input.json')).read_text())
            if body.get('model') != 'gpt-5.6-terra' or body.get('service_tier') != 'flex':
                raise ValueError('Recovery must preserve the Terra/Flex judge')
            b.f.save(world / (base + '.original_rejection.json'), original)
            for attempt in range(1, 4):
                stage = f'{base}_recovery_{attempt:02d}'
                result = dict(world=world.name, phase=phase, ok=False, recovery_stage=stage,
                              reason='Original judge request was explicitly rejected with HTTP 429; no accepted grade replaced.')
                try:
                    raw = await b.f.api_artifact(client, b.w.WorldBudget(ledger, world, .40), world, stage, body)
                    response = json.loads((world / (stage + '.response.json')).read_text())
                    if response.get('service_tier') != 'flex': raise ValueError('Unexpected returned service tier')
                    value = json.loads(raw)
                    if phase == 'qa':
                        value, removed = b.normalize_identical_duplicates(value)
                        if removed: b.f.save(world / (stage + '.normalization.json'), dict(removed=removed, normalized=value))
                        assessment = b.cq.validate(value, item)
                    else:
                        assessment = b.f.quality.validate(value, item)
                    result.update(ok=True, assessment=assessment,
                        response={k:response.get(k) for k in ('id','model','status','service_tier','usage')})
                except Exception as exc:
                    result['error'] = str(exc)
                b.f.save(world / (stage + '.result.json'), result)
                print(world.name, stage, 'OK' if result['ok'] else result.get('error'), flush=True)
                if result['ok']:
                    b.f.save(path, result)
                    break
                if not result['error'].startswith('Error code: 429'): break
                await asyncio.sleep(20)
    report = b.report(out, ledger)
    return int(bool(report['failed_judges']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--api-key-file', type=Path)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.out.resolve(), args.api_key_file)))
