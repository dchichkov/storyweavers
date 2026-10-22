#!/usr/bin/env python3
"""Export a frozen Storyscenes batch into the existing StoryWorld chat contract.

Offline candidate data, not a semantic acceptance certificate. Conversation
chains are atomic when packing; trace/evidence stays in compressed sidecars.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from training.storyworld_chat.export_openai_chat_jsonl import DEFAULT_SYSTEM
from training.storyworld_chat.finalize_chat_jsonl import validate_row
from training.storyworld_chat.train_chat import OpenAIChatJsonlDataset
from branch_prompts import branch_prompt

VERSION = 'storyscenes_training_v1'
SPECIAL = ('<|im_start|>', '<|im_end|>', '<|begin_of_text|>', '<|endoftext|>', '<|pad|>')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read_rows(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


class ProductionTokenizer:
    """Expose exactly the two tokenizer methods used by train_chat's dataset."""
    def __init__(self, path):
        from tokenizers import Tokenizer
        self.backend = Tokenizer.from_file(str(path / 'tokenizer.json'))
        config = json.loads((path / 'tokenizer_config.json').read_text())
        self.bos_token = config.get('bos_token')
        if isinstance(self.bos_token, dict):
            self.bos_token = self.bos_token['content']

    def encode(self, text, add_special_tokens=False):
        return self.backend.encode(text, add_special_tokens=add_special_tokens).ids

    @lru_cache(maxsize=50000)
    def count(self, text):
        return len(self.encode(text))

    def counts(self, messages):
        """Segmented encoding and loss counts match OpenAIChatJsonlDataset."""
        serialized = self.count(self.bos_token) if self.bos_token else 0
        story = answer = 0
        assistant_index = 0
        for message in messages:
            content = self.count(message['content'])
            footer = self.count('<|im_end|>\n')
            serialized += self.count('<|im_start|>' + message['role'] + '\n') + content + footer
            if message['role'] == 'assistant':
                if assistant_index == 0:
                    story += content + footer
                else:
                    answer += content + footer
                assistant_index += 1
        return dict(serialized=serialized, story=story, answer=answer, assistant=story + answer)


def split_families(families, seed, dev_fraction):
    families = sorted(set(families))
    if len(families) < 2:
        raise ValueError('At least two source families are required for a held-out split')
    ranked = sorted(families, key=lambda name: fingerprint([seed, name]))
    dev_count = min(len(families) - 1, max(1, round(len(families) * dev_fraction)))
    return {family: 'dev' if family in ranked[:dev_count] else 'train' for family in families}


def safe_content(text):
    return isinstance(text, str) and bool(text.strip()) and not any(t in text for t in SPECIAL)


def pack(story, prompt, conversations, counter, max_tokens):
    """Return full stories plus whole, ordered conversation chains; never truncate."""
    base = [dict(role='system', content=DEFAULT_SYSTEM), dict(role='user', content=prompt),
            dict(role='assistant', content=story)]
    if not all(safe_content(m['content']) for m in base):
        return [], [dict(reason='invalid_story_or_prompt')]
    if counter.counts(base)['serialized'] > max_tokens:
        return [], [dict(reason='story_over_context')]
    rows, skipped, current, chains = [], [], list(base), []
    for conversation in conversations:
        turns = conversation['turns']
        addition = [dict(role=role, content=turn[key]) for turn in turns
                    for role, key in [('user', 'question'), ('assistant', 'answer')]]
        if not addition or not all(safe_content(m['content']) for m in addition):
            skipped.append(dict(conversation_id=conversation['id'], reason='invalid_conversation'))
            continue
        if counter.counts(base + addition)['serialized'] > max_tokens:
            skipped.append(dict(conversation_id=conversation['id'], reason='whole_conversation_over_context'))
            continue
        if counter.counts(current + addition)['serialized'] > max_tokens:
            rows.append((current, chains))
            current, chains = list(base), []
        current += addition
        chains = chains + [conversation]
    rows.append((current, chains))
    return rows, skipped


def replay_world(batch, world, out, timeout):
    source_paths = [world / name for name in ('world.json', 'simulation.py', 'generator.py',
                                              'samples.jsonl', 'selected_samples.jsonl')]
    source_paths += sorted((batch / '_runtime').glob('*.py'))
    source_paths += [batch / 'settings.json', Path(__file__).with_name('export_worker.py'),
                     Path(__file__).with_name('qa_checks.py')]
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in source_paths}
    dest = out / 'sources' / (world.name + '.jsonl.gz')
    receipt = dest.with_suffix('.receipt.json')
    if receipt.exists() and dest.exists():
        saved = json.loads(receipt.read_text())
        if saved['sources'] == hashes and saved['sha256'] == digest(dest):
            return saved
        raise ValueError('Replay cache changed; use a new output directory: ' + str(dest))
    env = {k: v for k, v in os.environ.items()
           if not any(word in k.upper() for word in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    result = subprocess.run([sys.executable, str(Path(__file__).with_name('export_worker.py')),
                             str(world), str(dest)], env=env, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise ValueError(world.name + ': ' + result.stderr[-3000:])
    saved = dict(world=world.name, sources=hashes, sha256=digest(dest), samples=int(result.stdout.strip()))
    save(receipt, saved)
    return saved


def audit_file(path, tokenizer, max_tokens):
    dataset = OpenAIChatJsonlDataset(path, tokenizer, max_tokens)
    ids, conversations, stories, worlds = set(), set(), set(), set()
    totals, histogram, tasks = Counter(), Counter(), Counter()
    max_length = 0
    for index, row in enumerate(dataset.rows):
        validate_row(row, path, index + 1, max_tokens)
        if row['id'] in ids:
            raise ValueError('Duplicate row ID')
        key = fingerprint(row['messages'])
        if key in conversations:
            raise ValueError('Duplicate conversation')
        ids.add(row['id']); conversations.add(key)
        metadata = row['metadata']
        counts = tokenizer.counts(row['messages'])
        encoded = dataset[index]
        if len(encoded['input_ids']) != counts['serialized'] or counts != metadata['token_counts']:
            raise ValueError('Trainer truncation or token count mismatch')
        if sum(t != -100 for t in encoded['labels']) != counts['assistant']:
            raise ValueError('Trainer loss mask mismatch')
        # Also compare every label position, not only the aggregate count.
        expected = [-100] * (tokenizer.count(tokenizer.bos_token) if tokenizer.bos_token else 0)
        for message in row['messages']:
            expected += [-100] * tokenizer.count('<|im_start|>' + message['role'] + '\n')
            content = tokenizer.encode(message['content']) + tokenizer.encode('<|im_end|>\n')
            expected += content if message['role'] == 'assistant' else [-100] * len(content)
        if expected != encoded['labels']:
            raise ValueError('Trainer label positions differ')
        assistant_turns = sum(m['role'] == 'assistant' for m in row['messages'])
        if len(metadata['packed_tasks']) != assistant_turns:
            raise ValueError('Task metadata differs from message roles')
        if not all(safe_content(m['content']) for m in row['messages']):
            raise ValueError('Special token in message content')
        totals.update(counts)
        histogram[str(assistant_turns - 1)] += 1
        tasks[metadata['task']] += 1
        stories.add(metadata['story_sha256']); worlds.add(metadata['world'])
        max_length = max(max_length, counts['serialized'])
    return dict(rows=len(ids), unique_stories=len(stories), worlds=len(worlds), tokens=dict(totals),
                max_tokens=max_length, followup_histogram=dict(histogram), tasks=dict(tasks),
                sha256=digest(path), all_rows_match_training_loader=True), (ids, conversations, stories, worlds)


def run(args):
    batch, out = args.batch.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / 'sources').mkdir(exist_ok=True)
    attempts = json.loads((batch / 'summary.json').read_text())
    accepted = sorted((r for r in attempts if r['status'] == 'accepted'), key=lambda r: r['world'])
    if not accepted:
        raise ValueError('No accepted worlds')
    for item in accepted:
        for name, suffix in [('world', '.json'), ('simulation', '.py'), ('generator', '.py')]:
            if digest(batch / item['world'] / (name + suffix)) != item[name + '_sha256']:
                raise ValueError('Authored artifact changed: ' + item['world'])
    family_map = split_families([r['theme'] for r in attempts], args.seed, args.dev_fraction)
    if args.split_manifest:
        family_map = json.loads(args.split_manifest.read_text())['families']
        if not all(family_map.get(r['theme']) in ('train', 'dev') for r in accepted):
            raise ValueError('Prior split manifest must assign every source family')
    split = dict(seed=args.seed, grouping='theme/shared seed premise ancestry', families=family_map,
                 worlds={r['world']: family_map[r['theme']] for r in accepted})
    config = dict(protocol=VERSION, batch=str(batch), seed=args.seed, max_context_tokens=args.max_context_tokens,
                  split=split, tokenizer_sha256=digest(args.tokenizer / 'tokenizer.json'),
                  prompt_mode=args.prompt_mode,
                  prompt_renderer_sha256=digest(Path(__file__).with_name('branch_prompts.py')) if args.prompt_mode == 'branch' else None,
                  prompt='world premise plus selected initial conditions' if args.prompt_mode == 'branch' else 'world premise',
                  screened_policy='Exact saved story grade overall >= 6 and exact conversation grade usable=true; no grade propagation',
                  authoring_or_judge_calls=0)
    if (out / 'config.json').exists() and json.loads((out / 'config.json').read_text()) != config:
        raise ValueError('Export configuration changed; choose a new output directory')
    save(out / 'config.json', config); save(out / 'split.json', split)
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = [executor.submit(replay_world, batch, batch / r['world'], out, args.timeout) for r in accepted]
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if i % 10 == 0 or i == len(futures):
                print(f'Replayed and checked {i}/{len(futures)} worlds ({result["world"]})', flush=True)
    tokenizer = ProductionTokenizer(args.tokenizer)
    story_scores = {r['sample_id']: r for r in read_rows(batch / 'story_ratings.jsonl')}
    qa_scores = {(r['sample_id'], r['id']): r for r in read_rows(batch / 'conversation_ratings.jsonl')}
    keys = [(cohort, split) for cohort in ('candidate', 'judge_screened') for split in ('train', 'dev')]
    handles = {key: (out / ('.'.join(key) + '.raw.jsonl')).open('w') for key in keys}
    decisions = (out / 'decisions.jsonl').open('w')
    counts, seen, paths = Counter(), {}, defaultdict(set)
    sampled_texts = defaultdict(set)
    seen_messages = {cohort: set() for cohort in ('candidate', 'judge_screened')}
    namespace = fingerprint([config['batch'], config['tokenizer_sha256']])[:12]
    try:
        for item in accepted:
            world = batch / item['world']
            spec = json.loads((world / 'world.json').read_text())
            prompt = 'Write a short children’s story with this premise:\n' + spec['premise']
            split_name = split['worlds'][item['world']]
            rows = list(read_rows(out / 'sources' / (item['world'] + '.jsonl.gz')))
            random.Random(f'{args.seed}:{item["world"]}').shuffle(rows)
            # Prefer rated exemplars when identical text occurs at several seeds.
            rows.sort(key=lambda row: f'{item["world"]}:{row["seed"]}' not in story_scores)
            for index, source in enumerate(rows):
                prompt_evidence = None
                if args.prompt_mode == 'branch':
                    prompt, prompt_evidence = branch_prompt(spec, source)
                sample_id = f'{item["world"]}:{source["seed"]}'
                text_key = fingerprint(source['story'])
                paths[item['world']].add(tuple(e['scene'] for e in source['trace']['events']))
                sampled_texts[item['world']].add(text_key)
                counts['input_stories'] += 1
                counts['input_conversations'] += len(source['conversations'])
                counts['input_qa_turns'] += sum(len(c['turns']) for c in source['conversations'])
                counts['mechanically_invalid_conversations'] += len(source['export_qa_errors'])
                grade = story_scores.get(sample_id)
                counts['graded_stories'] += grade is not None
                counts['graded_conversations'] += sum((sample_id, c['id']) in qa_scores for c in source['conversations'])
                decision = dict(sample_id=sample_id, world=item['world'], split=split_name,
                                prompt_evidence=prompt_evidence,
                                story_sha256=text_key, story_grade=grade, qa_grades={
                                    c['id']: qa_scores.get((sample_id, c['id'])) for c in source['conversations']},
                                mechanical_qa_errors=source['export_qa_errors'], rows={}, skipped={})
                if text_key in seen:
                    counts['duplicate_stories_removed'] += 1
                    decision.update(reason='exact_duplicate_story', duplicate_of=seen[text_key]['sample_id'])
                    counts['cross_split_duplicate_stories_removed'] += seen[text_key]['split'] != split_name
                    decisions.write(json.dumps(decision, ensure_ascii=False) + '\n')
                    continue
                seen[text_key] = dict(sample_id=sample_id, split=split_name)
                for cohort in ('candidate', 'judge_screened'):
                    if cohort == 'judge_screened' and (not grade or grade['rating']['overall'] < 6):
                        continue
                    conversations = [c for c in source['conversations'] if c['id'] not in source['export_qa_errors']]
                    if cohort == 'judge_screened':
                        conversations = [c for c in conversations if qa_scores.get((sample_id, c['id']), {}).get('usable') is True]
                    packed, skipped = pack(source['story'], prompt, conversations, tokenizer, args.max_context_tokens)
                    decision['skipped'][cohort] = skipped
                    for skip in skipped:
                        counts[cohort + '_' + skip['reason']] += 1
                    decision['rows'][cohort] = []
                    for packed_index, (messages, chains) in enumerate(packed):
                        message_key = fingerprint(messages)
                        if message_key in seen_messages[cohort]:
                            counts[cohort + '_duplicate_conversations_removed'] += 1
                            continue
                        seen_messages[cohort].add(message_key)
                        token_counts = tokenizer.counts(messages)
                        followups = sum(len(c['turns']) for c in chains)
                        row_id = f'storyscenes:{namespace}:{sample_id}:{cohort}:{packed_index}'
                        metadata = dict(task='multiturn' if chains else 'story', world=str(world.relative_to(ROOT)),
                            source_family=item['theme'], sample_index=index, sample_id=sample_id,
                            params=dict(seed=source['seed'], prose_seed=source['prose_seed']),
                            split=split_name, protocol=VERSION, cohort=cohort, review_status='candidate_requires_semantic_review',
                            prompt_source='trace.premise' if prompt_evidence else 'world.json:premise',
                            prompt_evidence=prompt_evidence, story_sha256=text_key,
                            trace_sha256=source['trace_sha256'], generator_sha256=item['generator_sha256'],
                            evidence_path=f'sources/{item["world"]}.jsonl.gz',
                            conversation_ids=[c['id'] for c in chains], conversation_lengths=[len(c['turns']) for c in chains],
                            packed_followups=followups, packed_tasks=['story'] + ['story_qa'] * followups,
                            max_context_tokens=args.max_context_tokens, estimated_tokens=token_counts['serialized'],
                            token_counts=token_counts, token_counter='production_tokenizer_trainer_segmented')
                        row = dict(id=row_id, messages=messages, metadata=metadata)
                        validate_row(row, out, index + 1, args.max_context_tokens)
                        handles[cohort, split_name].write(json.dumps(row, ensure_ascii=False) + '\n')
                        decision['rows'][cohort].append(row_id)
                        counts[cohort + '_exported_conversations'] += len(chains)
                decisions.write(json.dumps(decision, ensure_ascii=False) + '\n')
    finally:
        for handle in handles.values():
            handle.close()
        decisions.close()
    artifacts, overlap = {}, {}
    for cohort in ('candidate', 'judge_screened'):
        split_sets = {}
        for split_name in ('train', 'dev'):
            stem = cohort + '.' + split_name
            dest = out / (stem + '.jsonl')
            subprocess.run([sys.executable, str(ROOT / 'training/storyworld_chat/finalize_chat_jsonl.py'),
                            str(out / (stem + '.raw.jsonl')), '--out', str(dest), '--manifest',
                            str(out / (stem + '.finalization.json')), '--max-context-tokens', str(args.max_context_tokens)], check=True)
            artifacts[stem], split_sets[split_name] = audit_file(dest, tokenizer, args.max_context_tokens)
        overlap[cohort] = {name: len(a & b) for name, a, b in zip(
            ('ids', 'conversations', 'stories', 'worlds'), split_sets['train'], split_sets['dev'])}
        if any(overlap[cohort].values()):
            raise ValueError('Cross-split leakage')
    checksums = {str(p.relative_to(out)): digest(p) for p in sorted((out / 'sources').glob('*'))}
    checksums.update({str(p.relative_to(ROOT)): digest(p) for p in [Path(__file__),
                      Path(__file__).with_name('export_worker.py'), ROOT / 'training/storyworld_chat/train_chat.py',
                      ROOT / 'training/storyworld_chat/finalize_chat_jsonl.py',
                      batch / 'summary.json', batch / 'story_ratings.jsonl', batch / 'conversation_ratings.jsonl']})
    save(out / 'checksums.json', checksums)
    manifest = dict(protocol=VERSION, config=config, accepted_worlds=len(accepted), counts=dict(counts),
                    artifacts=artifacts, split_overlap=overlap, api_cost_usd=0,
                    world_diversity={name: dict(unique_texts=len(sampled_texts[name]), scene_paths=len(paths[name]))
                                     for name in sorted(sampled_texts)},
                    limitations=['Candidate data; trace validity does not prove English entailment.',
                                 'Only exact saved grades are reused. All other QA/stories are ungraded.',
                                 'Branch prompts describe starting conditions, not all event choices; semantic adherence still needs review.',
                                 'Exact duplicate screening only; plot-level and cross-corpus overlap remain unaudited.',
                                 'QA packing repeats story supervision; choose task weights before production training.'])
    save(out / 'manifest.json', manifest)
    print(json.dumps(dict(counts=counts, artifacts=artifacts, split_overlap=overlap), indent=2))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batch', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--tokenizer', required=True, type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--max-context-tokens', type=int, default=1024)
    parser.add_argument('--seed', type=int, default=20260909)
    parser.add_argument('--dev-fraction', type=float, default=0.1)
    parser.add_argument('--split-manifest', type=Path, help='Reuse family assignments when scaling up')
    parser.add_argument('--prompt-mode', choices=('branch', 'premise'), default='branch')
    args = parser.parse_args()
    if args.jobs < 1 or args.timeout < 1 or args.max_context_tokens < 64 or not 0 < args.dev_fraction < 1:
        parser.error('Invalid jobs, timeout, context limit, or split fraction')
    run(args)


if __name__ == '__main__':
    main()
