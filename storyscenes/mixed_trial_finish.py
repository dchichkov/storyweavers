#!/usr/bin/env python3
"""Bounded extra replacements after the first mixed trial exhausted a slot."""
import asyncio
import json
from pathlib import Path

import mixed_trial as trial


async def run():
    from openai import AsyncOpenAI
    out = trial.ROOT / 'runs/mixed_seed_v1'
    settings = json.loads((out / 'settings.json').read_text())
    # Only the human-requested live contract correction may differ. Use its
    # original, hash-checked snapshot for this experiment's remaining worlds.
    for name, digest in json.loads((out / 'source_hashes.json').read_text()).items():
        source = out / '_authoring' / name if name == 'AUTHORING_COMPACT.md' else trial.ROOT / name
        if trial.f.digest(source) != digest:
            raise ValueError('Source changed: ' + name)
    contract = (out / '_authoring/AUTHORING_COMPACT.md').read_text()
    ledger = trial.f.Budget(Path(settings['campaign']) / 'budget.json', 15)
    trial.f.load_key(trial.ROOT.parent / '.API_KEY')
    all_briefs = trial.briefs_for(settings['seed'], 58)
    extras = [all_briefs[i] for i in (37, 47, 57)]
    manifest = out / 'supplemental_attempts.json'
    if not manifest.exists():
        trial.f.save(manifest, dict(reason='Slot 7 exhausted indices 7,17,27; fill its missing accepted world without replacing grades.',
                                   briefs=extras))
        original = json.loads((out / 'briefs.json').read_text())
        trial.f.save(out / 'initial_briefs.json', original)
        trial.f.save(out / 'briefs.json', original + extras)
    async with AsyncOpenAI(base_url='https://api.openai.com/v1', timeout=900, max_retries=0) as client:
        for brief in extras:
            report = trial.batch.report(out, ledger)
            if report['accepted_worlds'] >= 10: break
            world = out / brief['world_id']
            if (world / 'failure.json').exists(): continue
            try:
                await trial.cw.world_run(client, trial.w.WorldBudget(ledger, world, .15), world, brief, contract, cost_profile='cache-only')
            except Exception as exc:
                trial.f.save(world / 'failure.json', dict(world=world.name, ok=False, error=str(exc)))
                print(world.name, 'FAILED', str(exc), flush=True)
                continue
            item, rows = await trial.batch.selected_samples(world)
            budget = trial.w.WorldBudget(ledger, world, .40)
            await trial.batch.judge(client, budget, world, 'story', item, trial.f.quality.request_body(item, cache_prompts=True))
            qa_rows = [r for r in rows if r['conversations']]
            body = trial.batch.cq.request_body(qa_rows)
            counts = [len(r['conversations']) for r in qa_rows]
            body['text']['format']['schema']['properties']['stories']['items']['properties']['conversations'].update(minItems=min(counts), maxItems=max(counts))
            await trial.batch.judge(client, budget, world, 'qa', qa_rows, body)
    report = trial.batch.report(out, ledger)
    print('FINAL', report['accepted_worlds'], report['story_quality']['rated_stories'], report['cost']['usd_high'], flush=True)
    return int(report['accepted_worlds'] != 10 or report['story_quality']['rated_stories'] != 30 or bool(report['failed_judges']))


if __name__ == '__main__':
    raise SystemExit(asyncio.run(run()))
