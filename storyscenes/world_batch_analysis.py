#!/usr/bin/env python3
"""Offline analysis and review selection for a completed world_batch run."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random
import statistics as stats

import factory as f
from qa_checks import measure


def analyze(out):
    summary = json.loads((out / 'evaluation_summary.json').read_text())
    attempts = json.loads((out / 'summary.json').read_text())
    samples = [json.loads(line) for line in (out / 'selected_samples.jsonl').read_text().splitlines()]
    assessments = [json.loads(line) for line in (out / 'assessments.jsonl').read_text().splitlines()]
    themes = {r['world']: r['theme'] for r in attempts}
    sample_map = {r['sample_id']: r for r in samples}
    story_scores, conversation_scores, world_means = [], [], []
    for result in assessments:
        if not result.get('ok'): continue
        if result['phase'] == 'story':
            item = json.loads((out / result['world'] / 'selection.json').read_text())
            ids = {s['id']: s['sample_id'] for s in item['stories']}
            for score in result['assessment']['story_ratings']:
                story_scores.append(dict(world=result['world'], theme=themes[result['world']],
                    sample_id=ids[score['id']], rating=score['rating'], note=score['note']))
            world_means.append(result['assessment']['rating']['overall'])
        else:
            for story in result['assessment']['stories']:
                source = {c['id']: c for c in sample_map[story['id']]['conversations']}
                for score in story['conversations']:
                    conversation_scores.append(dict(world=result['world'], theme=themes[result['world']],
                        sample_id=story['id'], kind=source[score['id']]['turns'][0]['kind'], **score))
    expected_stories = {r['sample_id'] for r in samples}
    expected_conversations = {(r['sample_id'], c['id']) for r in samples for c in r['conversations']}
    actual_stories = [r['sample_id'] for r in story_scores]
    actual_conversations = [(r['sample_id'], r['id']) for r in conversation_scores]
    checks = dict(unique_sample_ids=len(sample_map) == len(samples),
        exactly_three_per_world=all(n == 3 for n in Counter(r['world'] for r in samples).values()),
        every_story_graded_once=len(actual_stories) == len(expected_stories) and set(actual_stories) == expected_stories,
        every_conversation_graded_once=len(actual_conversations) == len(expected_conversations) and set(actual_conversations) == expected_conversations)
    accepted = [row for row in attempts if row['status'] == 'accepted']
    artifacts = []
    for row in accepted:
        world = out / row['world']
        artifacts.append(dict(world=row['world'],
            hashes_match=all(f.digest(world / (name + suffix)) == row[name + '_sha256']
                             for name, suffix in [('world', '.json'), ('simulation', '.py'), ('generator', '.py')]),
            pool_size=len((world / 'samples.jsonl').read_text().splitlines()),
            world_sha256=f.digest(world / 'world.json')))
    checks.update(all_world_artifact_hashes_match=all(row['hashes_match'] for row in artifacts),
                  all_world_pools_have_100_stories=all(row['pool_size'] == 100 for row in artifacts),
                  distinct_world_definitions=len({row['world_sha256'] for row in artifacts}) == len(accepted))
    rng = random.Random(888)
    bootstrap = sorted(stats.mean(rng.choices(world_means, k=len(world_means))) for _ in range(5000)) if world_means else []
    def breakdown(rows, key):
        groups = defaultdict(list)
        for row in rows: groups[row[key]].append(row)
        return {name: dict(count=len(group), overall=stats.mean(r['rating']['overall'] for r in group),
                          **(dict(usable=sum(r['usable'] for r in group)) if 'usable' in group[0] else {}))
                for name, group in sorted(groups.items())}
    failure_counts = Counter()
    for row in attempts:
        if row['status'] != 'failed': continue
        world = out / row['world']
        failures = sorted(world.glob('world_*.failure.json')) + sorted(world.glob('text_*.failure.json'))
        error = json.loads(failures[-1].read_text())['error'] if failures else row.get('error', '')
        failure_counts[error.split(':', 1)[0][:150]] += 1
    analysis = dict(coverage=checks, artifacts=artifacts, mechanical_qa=measure(samples),
        unique_selected_texts=len({r['story'] for r in samples}),
        story_rating_histogram=dict(Counter(r['rating']['overall'] for r in story_scores)),
        story_quality_by_theme=breakdown(story_scores, 'theme'),
        qa_quality_by_theme=breakdown(conversation_scores, 'theme'),
        qa_quality_by_starter=breakdown(conversation_scores, 'kind'),
        world_mean_bootstrap_95=[bootstrap[125], bootstrap[4874]] if bootstrap else None,
        uncertainty_note='Resamples accepted worlds, with three stories clustered per world. Does not measure judge bias or theme generalization.',
        final_failure_messages=dict(failure_counts),
        authoring_usd_per_accepted_world=summary['phase_costs']['authoring']['usd_high'] / max(1, summary['accepted_worlds']),
        all_in_usd_per_accepted_world=summary['cost']['usd_high'] / max(1, summary['accepted_worlds']),
        authoring_20k_projection_usd=summary['phase_costs']['authoring']['usd_high'] / max(1, summary['accepted_worlds']) * 20000)
    f.save(out / 'analysis.json', analysis)
    for name, rows in [('story_ratings', story_scores), ('conversation_ratings', conversation_scores)]:
        (out / (name + '.jsonl')).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    # One complete, mechanically accepted story per theme, independent of grade.
    # Additional low-score cases are separate and explicitly labeled.
    selected, seen = [], set()
    for row in samples:
        theme = themes[row['world']]
        if theme not in seen:
            seen.add(theme)
            selected.append((row['sample_id'], 'first accepted world in theme; first randomly selected story'))
    for score in sorted(story_scores, key=lambda r: (r['rating']['overall'], r['sample_id']))[:5]:
        if score['sample_id'] not in {s[0] for s in selected}:
            selected.append((score['sample_id'], 'additional low story-score review'))
    prose = ['# Manual review samples', '']
    for sample_id, reason in selected:
        row = sample_map[sample_id]
        prose += [f'## {sample_id}', '', reason, '', row['story'], '']
        for conversation in row['conversations']:
            prose += [f'### {conversation["id"]}', '']
            for turn in conversation['turns']:
                prose += ['Q: ' + turn['question'], '', 'A: ' + turn['answer'], '']
    (out / 'manual_samples.md').write_text('\n'.join(prose))
    return analysis


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out', type=Path)
    print(json.dumps(analyze(parser.parse_args().out), indent=2))
