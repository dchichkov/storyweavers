"""Deterministic conversation quality/grounding checks, not a literary judge."""
from collections import Counter
import re

from conversation import Conversation, fingerprint


def sentence_count(text):
    # A bare "Yes." must not inflate the full-response rate.
    return len([p for p in re.split(r'[.!?]+(?:\s+|$)', text) if len(p.split()) >= 3])


def check_conversation(trace, conversation, paragraphs=None):
    errors = []
    if conversation['trace_sha256'] != fingerprint(trace): errors.append('wrong_trace')
    dialog = Conversation(trace, paragraphs)
    seen = set()
    for turn in conversation['turns']:
        if turn['question'] in seen: errors.append('duplicate_question')
        seen.add(turn['question'])
        expected = dialog.ask(turn['question'])
        if turn != expected: errors.append('followup_or_evidence_mismatch')
        if not turn['answer'].strip() or not re.search(r'[.!?][”"]?$', turn['answer']): errors.append('bare_answer')
        if turn['answerable']:
            if not turn['facts'] and not turn['event_ids'] and not turn.get('utterances'): errors.append('ungrounded_answer')
            for utterance in turn.get('utterances', []):
                known = next((u for u in dialog.dialogue if u['id']==utterance['id']), None)
                if known != utterance: errors.append('wrong_utterance')
                if utterance['at'] > turn['focus']['at']: errors.append('future_utterance')
                for span in utterance['quotes']:
                    text = paragraphs[utterance['paragraph']]['text'] if paragraphs else ''
                    if text[span['start']:span['end']] != span['text']: errors.append('wrong_quote')
            for fact in turn['facts']:
                at = fact['at']
                if not 0 <= at <= turn['focus']['at']: errors.append('future_fact'); continue
                state = trace['initial'] if at == 0 else trace['events'][at-1]['after']
                if fact['key'] not in state or type(state[fact['key']]) is not type(fact['value']) or state[fact['key']] != fact['value']:
                    errors.append('wrong_fact')
            if any(i < 1 or i > turn['focus']['at'] for i in turn['event_ids']): errors.append('future_event')
        if re.search(r'\b\w+\.knows\.|\b[a-z]+_[a-z_]+\b|\bnull\b', turn['answer']): errors.append('raw_state_fragment')
    return sorted(set(errors))


def measure(rows):
    kinds = Counter(); defects = Counter(); answers = []; count = 0; multi_turn = 0; stories = 0; abstentions = 0
    for row in rows:
        stories += 1
        if row.get('conversation_metadata',{}).get('dialogue_enabled') and row.get('paragraphs'):
            if '\n\n'.join(p['text'].strip() for p in row['paragraphs']) != row['story']:
                defects['dialogue_story_mismatch'] += 1
        for conversation in row['conversations']:
            count += 1; multi_turn += len(conversation['turns']) >= 3
            paragraphs = row.get('paragraphs') if row.get('conversation_metadata',{}).get('dialogue_enabled',False) else None
            defects.update(check_conversation(row['trace'], conversation, paragraphs))
            for turn in conversation['turns']:
                kinds[turn['kind']] += 1
                if turn['answerable']: answers.append(turn['answer'])
                else: abstentions += 1
    return dict(stories=stories, conversations=count, three_pair_conversations=multi_turn,
                answered_turns=len(answers), abstentions=abstentions, kinds=dict(kinds), defects=dict(defects),
                multi_sentence_fraction=sum(sentence_count(a) >= 2 for a in answers)/max(1,len(answers)),
                mean_answer_words=sum(len(a.split()) for a in answers)/max(1,len(answers)))


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('samples', type=Path, help='JSONL produced by qa.py --json')
    args = parser.parse_args()
    report = measure(json.loads(line) for line in args.samples.read_text().splitlines() if line.strip())
    print(json.dumps(report, indent=2))
    raise SystemExit(int(bool(report['defects']) or report['conversations'] == 0))
