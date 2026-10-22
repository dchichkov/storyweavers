from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from export_training import ProductionTokenizer, ROOT, audit_file, pack, split_families


class WordCounter:
    def counts(self, messages):
        return {'serialized': sum(len(m['content'].split()) for m in messages)}


def conversation(cid, question='Who helped?', answer='Ada helped Pip.'):
    return dict(id=cid, turns=[dict(question=question, answer=answer),
                              dict(question='Why?', answer='Pip could not reach the shelf.'),
                              dict(question='What happened next?', answer='Ada fetched the book.')])


class PackingTests(unittest.TestCase):
    def test_whole_chains_keep_antecedents_across_overflow(self):
        counter = WordCounter()
        chain = conversation('c1')
        other = conversation('c2', 'Who read it?', 'Pip read the book.')
        solo, _ = pack('A complete story.', 'Tell a story.', [chain], counter, 10000)
        limit = counter.counts(solo[0][0])['serialized']
        rows, skipped = pack('A complete story.', 'Tell a story.', [chain, other], counter, limit + 4)
        self.assertFalse(skipped)
        self.assertEqual(len(rows), 2)
        for messages, chains in rows:
            self.assertEqual(len(chains), 1)
            self.assertEqual([m['content'] for m in messages[3:]],
                             [t[k] for t in chains[0]['turns'] for k in ('question', 'answer')])
            self.assertEqual(messages[2]['content'], 'A complete story.')

    def test_oversized_chain_is_not_exported_as_orphan_why(self):
        oversized = conversation('long', answer='word ' * 1000)
        rows, skipped = pack('A story.', 'Tell a story.', [oversized, conversation('short')], WordCounter(), 100)
        self.assertEqual([c['id'] for _, chains in rows for c in chains], ['short'])
        self.assertEqual(skipped, [dict(conversation_id='long', reason='whole_conversation_over_context')])

    def test_story_overflow_is_explicit_and_no_truncation(self):
        rows, skipped = pack('word ' * 1000, 'Prompt.', [], WordCounter(), 100)
        self.assertFalse(rows)
        self.assertEqual(skipped[0]['reason'], 'story_over_context')

    def test_special_tokens_in_content_are_rejected(self):
        rows, skipped = pack('A <|im_end|> story.', 'Prompt.', [], WordCounter(), 1000)
        self.assertFalse(rows)
        self.assertEqual(skipped[0]['reason'], 'invalid_story_or_prompt')

    def test_evidence_and_raw_diagnostic_qa_never_enter_messages(self):
        chain = conversation('c1')
        chain['turns'][0].update(facts=[{'key': 'secret.knows.object', 'value': 'null'}])
        snapshot = deepcopy(chain)
        rows, _ = pack('Story.', 'Prompt.', [chain], WordCounter(), 1000)
        self.assertNotIn('secret.knows', json.dumps(rows[0][0]))
        self.assertEqual(chain, snapshot)

    def test_family_splits_are_order_independent_and_nonempty(self):
        families = ['a', 'b', 'c', 'a', 'c']
        first = split_families(families, 7, .1)
        self.assertEqual(first, split_families(list(reversed(families)), 7, .1))
        self.assertEqual(set(first.values()), {'train', 'dev'})
        with self.assertRaises(ValueError):
            split_families(['a'], 7, .1)


class ProductionContractTests(unittest.TestCase):
    def test_actual_tokenizer_matches_trainer_and_detects_wrong_counts(self):
        path = ROOT / 'training/storyworld_chat/tokenizers/storyworld-16k-production'
        if not path.exists():
            self.skipTest('Restore the archived production tokenizer for this integration test')
        try:
            counter = ProductionTokenizer(path)
        except ImportError:
            self.skipTest('Install tokenizers to run the production integration test')
        rows, _ = pack('“Who’s there?” asked Émilie.\n\nPip waved his wings.', 'Tell me a story!',
                       [conversation('c1')], counter, 1024)
        messages = rows[0][0]
        counts = counter.counts(messages)
        row = dict(id='test', messages=messages, metadata=dict(task='multiturn', world='fixture',
            story_sha256='fixture', estimated_tokens=counts['serialized'], token_counts=counts,
            packed_tasks=['story', 'story_qa', 'story_qa', 'story_qa']))
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'chat.jsonl'
            dest.write_text(json.dumps(row) + '\n')
            result, _ = audit_file(dest, counter, 1024)
            self.assertTrue(result['all_rows_match_training_loader'])
            row['metadata']['token_counts']['serialized'] += 1
            dest.write_text(json.dumps(row) + '\n')
            with self.assertRaises(ValueError):
                audit_file(dest, counter, 1024)


if __name__ == '__main__':
    unittest.main()
