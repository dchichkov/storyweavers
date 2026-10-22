#!/usr/bin/env python3
"""Add offline conversational QA to a saved world's unchanged story/trace."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

from conversation import Conversation, VERSION, conversations_from_trace, fingerprint

ROOT = Path(__file__).resolve().parent


def load_samples(world, seed, count=1, prose_seed=None):
    world = Path(world).resolve()
    command = [sys.executable, str(ROOT/'run.py'), str(world), '--seed', str(seed), '-n', str(count), '--json']
    if prose_seed is not None: command += ['--prose-seed', str(prose_seed)]
    env = {k: v for k, v in os.environ.items()
           if not any(s in k.upper() for s in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD'))}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=90, check=True)
    rows = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    if len(rows) != count: raise ValueError('Wrong sample count')
    return rows


def enrich(row, *, qa_seed=777, limit=6, pairs=3, include_dialogue=True):
    result = deepcopy(row)
    paragraphs = row.get('paragraphs') if include_dialogue else None
    if paragraphs and '\n\n'.join(p['text'].strip() for p in paragraphs) != row['story']:
        raise ValueError('Dialogue paragraphs disagree with the actual story')
    result['conversations'] = conversations_from_trace(row['trace'], seed=qa_seed, limit=limit, pairs=pairs, paragraphs=paragraphs)
    result['conversation_metadata'] = dict(protocol=VERSION, seed=qa_seed,
        story_sha256=fingerprint(row['story']), trace_sha256=fingerprint(row['trace']),
        generator='offline typed state, causal provenance and attributed dialogue',
        dialogue_enabled=include_dialogue,
        story_alignment='not semantically verified; inspect prose/trace disagreements')
    return result


def chat_records(row):
    """Draft chat rows with provenance kept out of the assistant's spoken answer.

    Trace grounding does not prove English-story entailment. These are review
    artifacts; export metadata deliberately does not claim training acceptance.
    """
    for conversation in row['conversations']:
        messages = [dict(role='system', content='Answer questions about this story. Do not invent missing details.')]
        for index, turn in enumerate(conversation['turns']):
            question = ('Story:\n'+row['story']+'\n\n' if index == 0 else '') + turn['question']
            messages.extend([dict(role='user', content=question), dict(role='assistant', content=turn['answer'])])
        yield dict(messages=messages, metadata=dict(protocol=VERSION, seed=row['seed'],
            conversation_id=conversation['id'], review_status='requires_story_alignment_review',
            story_sha256=fingerprint(row['story']), trace_sha256=conversation['trace_sha256'],
            evidence=conversation['turns']))


def print_dialog(turns):
    for turn in turns:
        print(f"Q: {turn['question']}\nA: {turn['answer']}\n")


def interactive(row):
    dialog = Conversation(row['trace'], row.get('paragraphs')); starters = dialog.starters()
    print(row['story']+'\n')
    def menu():
        for i, item in enumerate(starters, 1): print(f"{i}. {item['question']}")
    menu()
    print('\nChoose a number or type a listed question. Follow with Why?, Where was it?,\nWho had it?, How did they know?, Was that true?, or What happened next?.\nFor dialogue: Why did they say that?, Who were they talking to?, What was said next?\nType help for questions, or quit to finish.')
    while True:
        try: question = input('\nYou: ').strip()
        except EOFError: break
        if question.casefold() in ('quit', 'exit'): break
        if question.casefold() == 'help': menu(); continue
        if not question: continue
        if question.isdigit() and 1 <= int(question) <= len(starters):
            question = starters[int(question)-1]['question']
        print('Story: '+dialog.ask(question)['answer'])


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('world', type=Path)
    p.add_argument('--seed', type=int, default=1000)
    p.add_argument('--prose-seed', type=int)
    p.add_argument('-n', '--count', type=int, default=1)
    p.add_argument('--qa-seed', type=int, default=777)
    p.add_argument('--limit', type=int, default=6)
    p.add_argument('--pairs', type=int, default=3, help='Maximum QA pairs per conversation (2–5)')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--json', action='store_true', help='Story, trace, conversations and evidence as JSONL')
    mode.add_argument('--chat-jsonl', action='store_true', help='Draft chat records; require story-alignment review')
    mode.add_argument('--interactive', action='store_true')
    p.add_argument('--ask', action='append', help='A starter question followed by optional follow-ups; repeat this flag')
    args = p.parse_args(argv)
    if args.count < 1 or args.limit < 1 or not 2 <= args.pairs <= 5: p.error('Use positive count/limit and two to five pairs')
    if (args.interactive or args.ask) and args.count != 1: p.error('Interactive/ask mode needs one story')
    if args.ask and (args.interactive or args.chat_jsonl): p.error('--ask supports plain text or --json')
    rows = load_samples(args.world, args.seed, args.count, args.prose_seed)
    for row in rows:
        if args.interactive: interactive(row); continue
        if args.ask:
            dialog = Conversation(row['trace'], row.get('paragraphs'))
            for question in args.ask: dialog.ask(question)
            if args.json: print(json.dumps(dict(story=row['story'], turns=dialog.turns), ensure_ascii=False))
            else: print_dialog(dialog.turns)
            continue
        result = enrich(row, qa_seed=args.qa_seed, limit=args.limit, pairs=args.pairs)
        if args.json: print(json.dumps(result, ensure_ascii=False))
        elif args.chat_jsonl:
            for record in chat_records(result): print(json.dumps(record, ensure_ascii=False))
        else:
            print(f"{row['title']} (seed {row['seed']})\n\n{row['story']}\n")
            for conversation in result['conversations']: print_dialog(conversation['turns'])


if __name__ == '__main__':
    main()
