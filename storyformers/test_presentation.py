"""Presentation split isolation, literal layout targets, and real grammar execution."""

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from .grammar import canonical
from .induction import induce
from .presentation import BREAK, CLOSINGS, END, OPENINGS, evaluate, framing_checks, make_corpus, render, run
from .synthetic import make_corpus as sentence_corpus
from .transformer import Storyformer


class PresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bodies = sentence_corpus()
        cls.corpus, cls.metadata = make_corpus(cls.bodies)

    def test_disjoint_compositions_with_known_vocabulary_and_unchanged_bodies(self):
        before = deepcopy(self.bodies)
        self.assertEqual((self.corpus, self.metadata), make_corpus(self.bodies))
        self.assertEqual(before, self.bodies)
        documents, pairs = {}, {}
        for split, rows in self.corpus.items():
            documents[split] = {canonical(doc) for doc in rows}
            self.assertEqual(len(documents[split]), len(rows))
            pairs[split] = {(meta['opening'], meta['closing']) for meta in self.metadata[split]}
            self.assertEqual({meta['opening'] for meta in self.metadata[split]}, set(range(len(OPENINGS))))
            self.assertEqual({meta['closing'] for meta in self.metadata[split]}, set(range(len(CLOSINGS))))
            for index, (doc, meta) in enumerate(zip(rows, self.metadata[split])):
                start, stop = meta['spans']['body']
                self.assertEqual(doc[start:stop], self.bodies[split][index][:-1])
                self.assertTrue(all(set(row) == {'token', 'pos'} for row in doc))
                self.assertEqual(doc.count(BREAK), 2)
                self.assertEqual(doc.count(END), 1)
                self.assertTrue(framing_checks(doc)['complete_framing'])
        for a, b in (('train', 'validation'), ('train', 'test'), ('validation', 'test')):
            self.assertFalse(documents[a] & documents[b])
            self.assertFalse(pairs[a] & pairs[b])
        vocabulary = {canonical(row) for doc in self.corpus['train'] for row in doc}
        self.assertTrue(all(canonical(row) in vocabulary for split in ('validation', 'test')
                            for doc in self.corpus[split] for row in doc))

    def test_layout_is_predicted_and_display_does_not_repair_bad_samples(self):
        doc = self.corpus['train'][2]
        self.assertIn("'s", render(doc))
        self.assertEqual(render(doc).count('\n\n'), 2)
        self.assertNotIn('<END>', render(doc))
        bad = [row for row in doc if row != BREAK]
        self.assertNotIn('\n', render(bad))
        self.assertFalse(framing_checks(bad)['complete_framing'])
        self.assertFalse(framing_checks(doc[:-1])['ended'])

    def test_new_tokens_are_learned_and_checkpoint_preserves_predictions(self):
        result = induce(self.corpus['train'][:32], max_rules=4, min_support=2, weight_steps=2,
                        context_size=32, validation_documents=self.corpus['validation'][:2])
        self.assertIn('\n\n', result.model.projection.neurons)
        self.assertIn('Once', result.model.projection.neurons)
        doc = self.corpus['test'][0]
        stop = self.metadata['test'][0]['spans']['title_break'][0]
        prefix = doc[:stop]
        prediction = result.model.predict(prefix)
        self.assertGreater(prediction.probability(BREAK), 0)
        # Future closing labels cannot change an earlier residual or prediction.
        short, long = result.model.forward(prefix), result.model.forward(doc)
        self.assertEqual(short.next_latent.to_dict(), long.predictions[stop - 1].to_dict())
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'model.json'
            result.model.save(path)
            restored = Storyformer.load(path)
        self.assertEqual(prediction.to_dict(), restored.predict(prefix).to_dict())
        # Fixed-lookback caching must preserve full-prefix section scores exactly.
        documents, metadata = self.corpus['test'][:3], self.metadata['test'][:3]
        self.assertEqual(evaluate(result.model, documents, metadata),
                         evaluate(result.model, documents, metadata, cache_suffix=3))

    def test_refuses_to_overwrite_existing_experiment(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / 'train.jsonl'
            marker.write_text('original sentence data')
            with self.assertRaisesRegex(ValueError, 'empty output directory'):
                run(folder)
            self.assertEqual(marker.read_text(), 'original sentence data')


if __name__ == '__main__':
    unittest.main()
