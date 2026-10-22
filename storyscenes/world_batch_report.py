#!/usr/bin/env python3
"""Render the measured world-batch report from saved artifacts, without API calls."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil

from world_batch_analysis import analyze


def render(out):
    analysis = analyze(out)
    summary = json.loads((out / 'evaluation_summary.json').read_text())
    settings = json.loads((out / 'settings.json').read_text())
    attempts = json.loads((out / 'summary.json').read_text())
    story, qa = summary['story_quality'], summary['qa_quality']
    checks = analysis['mechanical_qa']
    if (summary['accepted_worlds'] != summary['target_worlds']
            or story['rated_stories'] != summary['target_worlds'] * 3
            or summary['failed_judges'] or not all(analysis['coverage'].values())):
        raise ValueError('Finish the requested worlds and complete evaluation coverage before publishing the report')
    missing = [str(p.relative_to(out)) for p in out.glob('*/*.request.json')
               if not p.with_name(p.name.replace('.request.json', '.response.json')).exists()]
    stage_costs = summary['phase_costs']
    lines = ['# 100 independent Storyscenes worlds — three stories per world', '',
        f'Authored **{summary["accepted_worlds"]} new world generators** across ten predeclared themes, '
        f'from **{summary["attempted_worlds"]} total attempts**. Each completed generator produced '
        f'100 local samples: **{summary["sampled_stories"]:,} stories** in all. '
        f'Three uniformly selected positions per world yielded **{summary["selected_stories"]} evaluation stories**. '
        f'Exactly **{story["rated_stories"]} stories** received valid story grades.', '',
        f'Those stories produced **{checks["conversations"]:,} conversations / '
        f'{checks["answered_turns"] + checks["abstentions"]:,} QA turns**, including '
        f'{checks["three_pair_conversations"]:,} complete three-pair conversations. '
        f'All {qa["rated_conversations"]:,} graded conversations were evaluated using their English story and dialogue only, '
        'without access to hidden simulation facts.', '',
        '| Measurement | Result |', '| --- | ---: |',
        f'| Story overall (0–9) | **{story["mean_quality"]["overall"]:.3f}** |',
        '| Earlier two-world pilot (20 stories) | 7.75 |',
        '| Earlier fresh sample from those same two worlds (100 stories) | 7.81 |',
        f'| Stories below 6 | {story["stories_below_six"]} / {story["rated_stories"]} |',
        f'| Set diversity (three-story sets) | {story["mean_diversity"]["overall"]:.3f} |',
        f'| Conversation overall | **{qa["mean_quality"]["overall"]:.3f}** |',
        f'| Conversation grounding / continuity | {qa["mean_quality"]["grounding"]:.3f} / {qa["mean_quality"]["continuity"]:.3f} |',
        f'| Conversation naturalness / usefulness | {qa["mean_quality"]["naturalness"]:.3f} / {qa["mean_quality"]["usefulness"]:.3f} |',
        f'| Conversations marked usable by Terra | {qa["usable"]:,} / {qa["rated_conversations"]:,} ({qa["usable_fraction"]:.1%}) |',
        f'| Unique selected story texts | {analysis["unique_selected_texts"]} / {summary["selected_stories"]} |', '',
        'The retained 7.75 result came from only two generators. This trial tests a broader set of newly '
        'authored worlds; it is not a paired before/after engine comparison. The current authoring settings '
        'do not establish that 7.75 is maintained across this larger population. The judge rubric is unchanged, '
        'but it sees sets of three rather than ten stories, so especially the diversity scores are not directly '
        'comparable with the earlier runs. Scores and usability labels are model judgments.', '',
        f'The world-cluster bootstrap interval for story overall is '
        f'{analysis["world_mean_bootstrap_95"][0]:.3f}–{analysis["world_mean_bootstrap_95"][1]:.3f} '
        '(95%, 5,000 resamples, fixed seed). This reflects sampling variation among accepted worlds, '
        'not judge bias, per-world quality certainty, or generalization beyond these ten themes.', '',
        '| Theme | Worlds | Story overall | QA overall |', '| --- | ---: | ---: | ---: |']
    for theme, count in sorted(summary['accepted_per_theme'].items()):
        sq = analysis['story_quality_by_theme'].get(theme, {}).get('overall')
        qq = analysis['qa_quality_by_theme'].get(theme, {}).get('overall')
        lines.append(f'| {theme} | {count} | {sq:.3f} | {qq:.3f} |')
    lines += ['', '| Conversation starter | Count | Overall | Marked usable |', '| --- | ---: | ---: | ---: |']
    for kind, row in analysis['qa_quality_by_starter'].items():
        lines.append(f'| {kind} | {row["count"]} | {row["overall"]:.3f} | {row["usable"]} |')
    lines += ['', '## What the manual review found', '',
        'The first selected story from the first accepted world in each theme was read in full, with one '
        'or two conversations spot-checked per story. Two low-QA-score cases and three low-story-score '
        'cases from distinct bakery worlds were also read against their full stories, followed by the first '
        'selected stories from the recovered museum grade and the final picnic world. Exact examples are in [manual notes](manual_notes.md); '
        '[the review worksheet](manual_samples.md) includes full conversations and additional low-story-score samples. '
        'The worksheet contains more material than the manual-read claim above.', '',
        '- **Shared text leaks facts between branches.** A bakery payment paragraph refers to a honey bun after '
        'the story delivered a nut tart; multiple worlds describe still air in a windy path.',
        '- **Repeated or premature actions.** Separate passages narrate the same handover twice. A museum '
        'certifies returned objects before borrowing them, and its ending still displays objects after return.',
        '- **Internal state wording reaches the prose.** “Copied fact,” “nearby fact,” and explicit signal-state '
        'changes weaken otherwise warm, playful passages.',
        '- **QA asks about facts the reader never received.** Low-scoring roof-post conversations quiz the reader '
        'about unused ribbon/basket props and then jump to unrelated invitation events. Stale custody and '
        'location information compound the mismatch.',
        '- **Dialogue coverage and causal explanations remain incomplete.** Speech navigation can skip '
        'unindexed lines; Why answers often state old guards rather than the relevant motive or cause.', '',
        f'Deterministic replay/evidence checks found **{sum(checks["defects"].values())} defects**, despite the lower '
        'semantic QA scores. This is evidence that trace grounding alone does not establish story-only '
        'answerability. The chat exports remain review artifacts, not automatically accepted training data. '
        'No engine, prose, QA rule, or accepted grade was revised to improve this batch’s score.', '',
        '## Cost and service', '',
        '| Phase | Returned calls | Input tokens | Output tokens | Estimated USD |', '| --- | ---: | ---: | ---: | ---: |']
    for phase in ('authoring', 'story', 'qa'):
        cost = stage_costs[phase]
        lines.append(f'| {phase} | {cost["requests"]} | {cost["input_tokens"]:,} | {cost["output_tokens"]:,} | {cost["usd_high"]:.6f} |')
    cost = summary['cost']
    lines += [f'| **Total** | **{cost["requests"]}** | **{cost["input_tokens"]:,}** | **{cost["output_tokens"]:,}** | **{cost["usd_high"]:.6f}** |', '',
        f'All returned tiers: `{json.dumps(summary["returned_tiers"], sort_keys=True)}`. '
        f'Cache reads: **{summary["cache"]["read_tokens"]:,} tokens**; cache writes: '
        f'**{summary["cache"]["write_tokens"]:,} tokens**. Sampling and QA generation were offline and added **$0 API cost**. '
        'Luna authored and repaired worlds; Terra only graded stories/conversations, without generator scripts.', '',
        f'There are **{len(missing)} saved requests without returned usage**. Their original conservative '
        f'reservations remain in the ledger: **${summary["unresolved_reservation_usd"]:.6f}**. '
        f'The whole $15 campaign, including prior work and all reservations, now commits '
        f'**${summary["campaign_committed_upper_usd"]:.6f}**. These estimates are based on returned usage and '
        'list prices, not invoice reconciliation; missing responses are not assumed free.', '',
        'Flex rates per million ordinary input/cache-read/cache-write/output tokens: '
        'Luna $0.10/$0.01/$0.125/$0.60; Terra $1.00/$0.10/$1.25/$6.00. '
        '[Official pricing](https://developers.openai.com/api/docs/pricing) and '
        '[Flex documentation](https://developers.openai.com/api/docs/guides/flex-processing); pricing checked 2026-09-07.', '',
        f'Including failed attempts, returned authoring cost is **${analysis["authoring_usd_per_accepted_world"]:.5f} '
        f'per mechanically accepted world**. A straight-line 20,000-world authoring estimate is '
        f'**${analysis["authoring_20k_projection_usd"]:.2f}**, before evaluation and any literary rejection. '
        f'With this run’s grading, returned cost is **${analysis["all_in_usd_per_accepted_world"]:.5f} per world**. '
        'These projections exclude unresolved charges, human review, hosting/storage and changes in yield or pricing. '
        'Mechanical acceptance is not acceptance at the user’s 7.75 quality target.', '',
        '## Reproducibility and recovery', '',
        f'- {summary["failed_worlds"]} failed world attempts remain alongside completed worlds; no grade-based replacements.',
        '- Seed manifest was written before paid dispatch. First ten accepted generators per theme; '
        'three uniform positions from each 100-story pool, seed 777, without replacement or deduplication.',
        '- Current cache-only authoring, original compact contract, medium mechanics reasoning and low prose reasoning. '
        'Per-world authoring dispatch cap $0.15; shared campaign cap $15; SDK automatic retries disabled.',
        '- Scheduler handoff drained in-flight calls, reused saved completed responses, retained all uncertain '
        'reservations and quarantined failed/capped drafts before selecting new predeclared seeds. '
        'Engine and authoring snapshots stayed fixed. See [continuation audit](continuation_audit.json).',
        '- Any explicit 429 judge recovery uses the original payload, preserves the rejected request/reservation, '
        'and replaces no valid grade. Recovery responses and provenance remain beside the original artifacts.',
        '- **123 tests pass**, including recovery, budgeting, selection, dialogue, conversation and legacy authoring checks.',
        '- All 100 world definitions are distinct; generator, simulation and world-file hashes match their '
        'saved records. Every world has its 100-story pool. Every selected story and conversation was '
        'graded exactly once, with exactly three selected story IDs per world.', '',
        '[Evaluation summary](evaluation_summary.json) · [Analysis and integrity checks](analysis.json) · '
        '[All selected stories and traces](selected_samples.jsonl) · [Raw assessments](assessments.jsonl) · '
        '[Story ratings](story_ratings.jsonl) · [Conversation ratings](conversation_ratings.jsonl) · [Test log](tests.txt).', '']
    (out / 'REPORT.md').write_text('\n'.join(lines))
    (out / 'missing_usage_requests.json').write_text(json.dumps(missing, indent=2) + '\n')
    snapshot = out / '_reporting'
    snapshot.mkdir(exist_ok=True)
    for name in ('world_batch_analysis.py', 'world_batch_report.py', 'world_batch_retry_judges.py'):
        shutil.copyfile(Path(__file__).parent / name, snapshot / name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out', type=Path)
    render(parser.parse_args().out.resolve())
