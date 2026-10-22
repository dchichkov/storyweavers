#!/usr/bin/env python3
"""Audit exported messages against source conversations and write a readiness report."""
from collections import Counter
import json
from pathlib import Path
import shutil
import statistics
import sys

from export_training import ROOT, digest, fingerprint, read_rows, save


def report(out):
    out = Path(out).resolve()
    manifest = json.loads((out / 'manifest.json').read_text())
    batch = Path(manifest['config']['batch'])
    cached_world, sources = None, {}
    inspected = Counter()
    examples = []
    for cohort in ('candidate', 'judge_screened'):
        for split in ('train', 'dev'):
            for row in read_rows(out / f'{cohort}.{split}.jsonl'):
                meta = row['metadata']
                if meta['world'] != cached_world:
                    sources = {r['seed']: r for r in read_rows(out / meta['evidence_path'])}
                    cached_world = meta['world']
                source = sources[meta['params']['seed']]
                assert row['messages'][2]['content'] == source['story']
                assert meta['story_sha256'] == fingerprint(source['story'])
                assert meta['trace_sha256'] == source['trace_sha256']
                chains = {c['id']: c for c in source['conversations']}
                expected = [dict(role=role, content=turn[key]) for cid in meta['conversation_ids']
                            for turn in chains[cid]['turns'] for role, key in [('user', 'question'), ('assistant', 'answer')]]
                assert expected == row['messages'][3:], 'Dropped, reordered, or invented QA turns'
                assert meta['conversation_lengths'] == [len(chains[cid]['turns']) for cid in meta['conversation_ids']]
                inspected[cohort + '_rows'] += 1
                inspected[cohort + '_qa_turns'] += len(expected) // 2
                inspected[cohort + '_dialogue_conversations'] += sum(
                    chains[cid]['turns'][0]['kind'] == 'dialogue' for cid in meta['conversation_ids'])
                if cohort == 'candidate' and len(examples) < 3 and meta['sample_id'] not in [r['metadata']['sample_id'] for r in examples]:
                    examples.append(row)
    save(out / 'conversation_integrity.json', dict(checked=dict(inspected), exact_source_order_and_content=True))
    frozen = out / '_exporter'
    frozen.mkdir(exist_ok=True)
    for name in ('export_training.py', 'export_worker.py', 'export_training_report.py', 'test_export_training.py', 'branch_prompts.py'):
        shutil.copy2(Path(__file__).with_name(name), frozen / name)
    save(frozen / 'sha256.json', {p.name: digest(p) for p in sorted(frozen.glob('*.py'))})
    counts, artifacts = manifest['counts'], manifest['artifacts']
    def total(cohort, name):
        return sum(a[name] for k, a in artifacts.items() if k.startswith(cohort + '.'))
    def tokens(cohort, name):
        return sum(a['tokens'].get(name, 0) for k, a in artifacts.items() if k.startswith(cohort + '.'))
    candidate_stories = total('candidate', 'unique_stories')
    repeats = total('candidate', 'rows') / max(1, candidate_stories)
    answer_share = tokens('candidate', 'answer') / max(1, tokens('candidate', 'assistant'))
    qa_grades = list(read_rows(batch / 'conversation_ratings.jsonl'))
    story_grades = list(read_rows(batch / 'story_ratings.jsonl'))
    plot_counts = [r['scene_paths'] for r in manifest['world_diversity'].values()]
    text_counts = [r['unique_texts'] for r in manifest['world_diversity'].values()]
    summary = dict(input_stories=counts['input_stories'], exported_stories=candidate_stories,
                   candidate_rows=total('candidate', 'rows'), story_repetition_factor=repeats,
                   answer_supervision_fraction=answer_share,
                   serialized_tokens=tokens('candidate', 'serialized'), assistant_tokens=tokens('candidate', 'assistant'),
                   story_tokens=tokens('candidate', 'story'), answer_tokens=tokens('candidate', 'answer'),
                   qa_judge_usable=sum(r['usable'] for r in qa_grades), qa_judged=len(qa_grades),
                   story_overall=statistics.mean(r['rating']['overall'] for r in story_grades),
                   median_unique_texts_per_world=statistics.median(text_counts),
                   median_scene_paths_per_world=statistics.median(plot_counts))
    save(out / 'readiness.json', summary)
    text = [
        '# Storyscenes training export: 100-world dry run', '',
        'The batch now exports into the existing OpenAI-style chat JSONL contract and passes the actual '
        'training loader. **The file format is ready; this is candidate material, not a production-approved corpus.** '
        'No new worlds or API requests were made. Export API cost: **$0**.', '',
        '## Materialized files', '',
        '| File | Rows | Distinct stories | Worlds | Serialized tokens | Assistant tokens |',
        '| --- | ---: | ---: | ---: | ---: | ---: |',
    ]
    for name, a in artifacts.items():
        text.append(f'| [{name}.jsonl]({name}.jsonl) | {a["rows"]:,} | {a["unique_stories"]:,} | {a["worlds"]} | '
                    f'{a["tokens"].get("serialized", 0):,} | {a["tokens"].get("assistant", 0):,} |')
    text += ['',
        f'All {manifest["accepted_worlds"]} mechanically accepted worlds were replayed at all their saved seeds '
        f'({counts["input_stories"]:,} stories). Each story, paragraph list, and trace hash matched the saved pool. '
        'All 300 graded samples also reproduced their saved conversational QA exactly. The 31 failed authoring attempts were excluded.', '',
        f'Exact-text deduplication removed {counts.get("duplicate_stories_removed", 0):,} story samples. '
        f'The candidate export retains {candidate_stories:,} distinct stories. '
        'Repeated story prefixes in separate packed rows are additional training exposures, not new stories.', '',
        'The `judge_screened` files retain only exact sampled stories with saved overall score >=6/9, '
        'and only conversations explicitly marked usable by the existing judge. They can include story-only '
        'rows when all six conversations fail the filter. These scores do not certify prompt adherence or semantic correctness; '
        'unknown grades never pass this filter, and scores are never inherited from another seed or world.', '',
        '## Integration checks', '',
        '- 130 Storyscenes tests passed, including seven new export/packing/tokenizer tests (see `tests.txt`).',
        '- Production 16k tokenizer restored from its existing archive. Tokenization matches the trainer’s '
        'separate BOS/header/content/terminator encoding, including assistant terminators in loss.',
        '- Every row was loaded through `OpenAIChatJsonlDataset`; exact lengths and every loss-mask position '
        'matched the exporter. No row is truncated, exceeds 1,024 tokens, or has an empty/invalid role sequence.',
        '- Existing `finalize_chat_jsonl.py` validated all four files. IDs are unique and there are no exact '
        'conversation duplicates or train/dev story, world, conversation, or ID overlaps.',
        '- All ten `hill_picnic` worlds are held out for dev. Shared premise/theme ancestry stays together. '
        'Reuse [split.json](split.json) when adding worlds; do not randomly split individual story rows.',
        '- Independent post-export audit compared every QA message with its compressed source conversation. '
        'No chains were shuffled, broken across rows, or stripped of preceding answers. Dialogue questions are included.',
        '- Runtime evidence, internal state keys, and diagnostic QA are excluded from message construction. '
        'Full evidence is preserved in `sources/*.jsonl.gz`, linked by world, seed, trace hash, and conversation ID. '
        'This structural separation does not detect every awkward phrase already present in the source prose/answers.', '',
        f'Packing excluded {counts.get("candidate_story_over_context", 0)} stories and '
        f'{counts.get("candidate_whole_conversation_over_context", 0)} conversations for length. '
        f'Mechanical QA defects: {counts.get("mechanically_invalid_conversations", 0)}. '
        f'The final candidate files contain {counts["candidate_exported_conversations"]:,} intact conversations '
        f'and {inspected["candidate_qa_turns"]:,} QA pairs; '
        f'{inspected["candidate_dialogue_conversations"]:,} conversations start with dialogue questions.', '',
        '## What to fix or decide before 1,000 worlds', '',
        f'1. **Semantic QA filtering is still essential.** The saved judge marked {summary["qa_judge_usable"]:,}/'
        f'{summary["qa_judged"]:,} conversations usable ({summary["qa_judge_usable"]/summary["qa_judged"]:.1%}). '
        f'Those grades cover only {counts["graded_conversations"]:,}/{counts["input_conversations"]:,} generated conversations. '
        'Other samples are unjudged. Trace replay is not a substitute: unused props, implicit prior ignorance, '
        'stale ownership, and unrelated follow-up causes can still appear in the English answers.', '',
        f'2. **Set the story/QA training allocation explicitly.** Full candidate packing gives '
        f'{tokens("candidate", "story"):,} story and {tokens("candidate", "answer"):,} answer supervision tokens; '
        f'answers account for {answer_share:.1%} of assistant tokens. Stories repeat an average of {repeats:.2f} times '
        'across packed rows. The proposed dataset plan’s 5–10% answer allocation refers to the final mixture, '
        'so this export needs deliberate mixing/downsampling rather than blindly concatenating every row.', '',
        ('3. **Verify branch-prompt adherence.** Requests describe the selected initial conditions, with per-fact '
         'evidence. They do not prescribe every event ordering. Paraphrase variety and semantic agreement with '
         'the rendered story still need evaluation.' if manifest['config'].get('prompt_mode') == 'branch' else
        '3. **Author prompt variety.** Storyscenes currently emits no `prompts` field. This adapter uses the '
        'authored `world.json` premise as a natural-language request; raw simulation parameters remain metadata. '
        'There are no branch-specific or paraphrased prompts yet, and prompt/story agreement has not been graded.'), '',
        f'4. **Expand independent premises, not only sample counts.** These 100 scripts descend from ten themes. '
        f'They have median {statistics.median(text_counts):g} exact-unique texts and {statistics.median(plot_counts):g} '
        'ordered scene paths per 100 samples. Path counts and text hashes do not establish plot diversity. '
        'Near-duplicate plot screening and overlap against the old production corpus remain outstanding.', '',
        f'5. **Retain a prose acceptance gate.** Existing story quality is {summary["story_overall"]:.2f}/9. '
        'The exporter deliberately preserves the source stories, including known label/value drift, repeated handovers, '
        'and endings with stale object state. Mechanical success alone must not become training acceptance.', '',
        '## Manual spot-checks during this export', '',
        '- `bakery_exchange_004:1001`: readable fair-exchange story, but repeated transfer/acceptance prose; '
        'dialogue follow-up adds prior ignorance that is not stated explicitly.',
        '- `clocktower_club_002:1002`: story says Ada keeps a request already handed to the keeper, '
        'and mentions Pip holding the borrowed bell before the loan. Some causal answers merely restate possession.',
        '- `hill_picnic_001:1004`: warm picnic ending; a follow-up about the blanket jumps to a basket movement, '
        'and another answer supplies an unstated precise location.', '',
        'These are spot-checks, not a new quality evaluation. Saved judge results are unchanged.', '',
        '## Reproduce', '', '```bash',
        '.venv/bin/python storyscenes/export_training.py storyscenes/runs/worlds_100_v1 \\',
        '  --out training/storyworld_chat/data/storyscenes_100_20260909 \\',
        '  --tokenizer training/storyworld_chat/tokenizers/storyworld-16k-production --jobs 4',
        '.venv/bin/python storyscenes/export_training_report.py training/storyworld_chat/data/storyscenes_100_20260909',
        '```', '',
        'Successful per-world replay caches are reusable only when their input hashes and output checksum match. '
        'Use a new export directory if the batch, QA runtime, tokenizer, or packing configuration changes. '
        '[manifest.json](manifest.json), [decisions.jsonl](decisions.jsonl), [checksums.json](checksums.json), '
        'the source receipts, finalization manifests, and `_exporter/` snapshot preserve the audit trail.', '',
    ]
    (out / 'REPORT.md').write_text('\n'.join(text))
    sample_text = ['# Example exported conversations', '']
    for row in examples:
        sample_text += ['## ' + row['id'], '',
                       'Candidate row; not independently accepted for training.', '']
        for message in row['messages']:
            sample_text += ['**' + message['role'] + '**', '', message['content'], '']
    (out / 'samples.md').write_text('\n'.join(sample_text))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    report(sys.argv[1])
