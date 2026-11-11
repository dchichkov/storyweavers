"""Behavioral checks for causal training, sparse counts, and lexical residuals."""

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from . import FrequencyHead, FrequencyStoryformer as Storyformer, WordNetLexicon, causal_mask, encode, tokenize
from .__main__ import documents


class TokenOnlyLexicon:
    """A test fixture only; production uses WordNet by default."""

    def lookup(self, token):
        return {"pos": None, "lemma": token.casefold(), "synsets": []}


def latents(*tokens):
    return [{"token": token} for token in tokens]


class FrequencyTests(unittest.TestCase):
    def test_trigram_is_conditional_on_final_bigram(self):
        head = FrequencyHead().fit(["the rabbit runs"] * 3 + ["the rabbit rests"])
        result = head.read(latents("old", "the", "rabbit"))
        self.assertEqual(result.distribution, {"runs": .75, "rests": .25})
        self.assertEqual(result.recent_tokens, ("old", "the", "rabbit"))
        self.assertEqual(result.matched_context, ("the", "rabbit"))
        self.assertEqual(result.order, 3)
        self.assertEqual(result.observations, 4)

    def test_backoff_and_empty_model(self):
        head = FrequencyHead().fit(["the rabbit runs", "a rabbit rests"])
        self.assertEqual(head.read(latents("unknown", "rabbit")).order, 2)
        self.assertEqual(head.read(latents("unknown")).order, 1)
        self.assertEqual(head.read([]).distribution["rabbit"], 2 / 6)
        self.assertEqual(FrequencyHead().read([]).distribution, {})

    def test_top_ten_is_sparse_and_reports_omitted_mass(self):
        head = FrequencyHead()
        for i in range(12):
            head.observe(["the", "rabbit"], f"word{i:02d}", weight=i + 1)
        result = head.read(latents("the", "rabbit"))
        self.assertEqual(len(result.distribution), 10)
        self.assertEqual(list(result.distribution)[:2], ["word11", "word10"])
        self.assertNotIn("word00", result.distribution)
        self.assertAlmostEqual(sum(result.distribution.values()), 1)
        self.assertAlmostEqual(result.retained_mass, 75 / 78)
        self.assertAlmostEqual(result.distribution["word11"], 12 / 75)
        before = deepcopy(head.counts)
        head.read(latents("missing", "key"))
        self.assertEqual(head.counts, before)

    def test_boundaries_and_ties(self):
        head = FrequencyHead().fit(["a b", "c d"])
        self.assertNotIn(("b",), head.counts)
        self.assertNotIn(("a", "b"), head.counts)
        result = head.read([], top_k=2)
        self.assertEqual(list(result.distribution), ["a", "b"])

    def test_weighted_grammar_bridge(self):
        from grammarworlds.grammar import choice

        head = FrequencyHead().fit_grammar(choice("move", "rabbit runs", "rabbit rests", weights=(3, 1)))
        self.assertEqual(head.read(latents("rabbit")).distribution, {"runs": .75, "rests": .25})

    def test_reject_invalid_weights_and_saved_rows(self):
        head = FrequencyHead()
        for weight in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                head.observe([], "rabbit", weight=weight)
        for rows in ([{"context": [], "next": {"rabbit": -1}}],
                     [{"context": ["a", "b", "c"], "next": {"d": 1}}],
                     [{"context": [], "next": {"rabbit": 1}}] * 2):
            with self.assertRaises(ValueError):
                FrequencyHead.from_rows(rows)


class ModelTests(unittest.TestCase):
    def model(self, **kwargs):
        return Storyformer(lexicon=TokenOnlyLexicon(), **kwargs)

    def test_teacher_forcing_has_no_target_or_future(self):
        model = self.model(context_size=3)
        examples = list(model.training_examples("one two three four five six"))
        self.assertEqual(examples[0].context, ())
        self.assertEqual(examples[0].target, "one")
        self.assertEqual(examples[-1].context, ("three", "four", "five"))
        self.assertEqual(examples[-1].target, "six")
        self.assertEqual(examples[-1].target_position, 5)
        # The optimized count trainer must equal the explicit causal examples.
        reference = FrequencyHead()
        for example in examples:
            reference.observe(example.context, example.target)
        model.fit(["one two three four five six"])
        self.assertEqual(model.head.counts, reference.counts)

    def test_future_suffix_cannot_change_earlier_readouts(self):
        model = self.model().fit(["the rabbit runs", "the rabbit rests"])
        left = model.forward("the rabbit runs away")
        right = model.forward("the rabbit eats carrots")
        prefix = model.forward("the rabbit")
        self.assertEqual(left.predictions[:2], right.predictions[:2])
        self.assertEqual(left.predictions[:2], prefix.predictions)
        self.assertEqual(left.residual_stream[:2], prefix.residual_stream)
        self.assertEqual(causal_mask(3), [[True, False, False], [True, True, False], [True, True, True]])

    def test_blocks_receive_only_visible_memory(self):
        seen = []

        class RecordingBlock:
            def forward(self, latent, attention):
                seen.append([row["position"] for row in attention.visible])
                return latent

        model = self.model()
        model.blocks = (RecordingBlock(),)
        model.forward("the rabbit runs")
        self.assertEqual(seen, [[0], [0, 1], [0, 1, 2]])
        with self.assertRaises(NotImplementedError):
            model.fit(["the rabbit runs"])

    def test_context_is_bounded_and_blocks_are_identity(self):
        text = " ".join(["rabbit"] * 260)
        model = self.model(num_blocks=4)
        result = model.forward(text)
        self.assertEqual(len(result.residual_stream), 256)
        self.assertEqual(result.residual_stream[0]["position"], 4)
        self.assertEqual(result.residual_stream[-1]["position"], 259)
        self.assertEqual(result.residual_stream, encode(tokenize(text)[-256:], model.lexicon, offset=4))
        result.residual_stream[0]["synsets"].append("local-edit")
        self.assertEqual(result.residual_stream[1]["synsets"], [])

    def test_count_updates_save_load_and_empty_prompt(self):
        model = self.model().fit(["the rabbit runs"])
        model.fit(["the rabbit rests"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.json"
            model.save(path)
            loaded = Storyformer.load(path, lexicon=TokenOnlyLexicon())
        self.assertEqual(loaded.predict("the rabbit"), {"rests": .5, "runs": .5})
        self.assertEqual(loaded.predict(""), model.predict(""))
        self.assertEqual(loaded.head.counts, model.head.counts)

    def test_corpus_reader_uses_only_requested_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stories.jsonl"
            path.write_text('{"story": "rabbit runs", "kernel": "IgnoreThis()"}\n\n')
            self.assertEqual(list(documents(path, "story")), ["rabbit runs"])


class WordNetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # This integration check is required: never replace WordNet with seeds.
        cls.lexicon = WordNetLexicon()

    def test_actual_rabbit_latent_and_ambiguity(self):
        rabbit = encode(["Rabbit"], self.lexicon)[0]
        self.assertEqual(rabbit["token"], "rabbit")
        self.assertEqual(rabbit["surface"], "Rabbit")
        self.assertEqual(rabbit["pos"], "n")
        self.assertIn("rabbit.n.01", rabbit["synsets"])
        self.assertIn("v", rabbit["pos_candidates"])
        self.assertEqual(rabbit["lexname"], "noun.animal")
        rabbit["synsets"].clear()
        self.assertIn("rabbit.n.01", self.lexicon.lookup("rabbit")["synsets"])

    def test_unknowns_punctuation_and_tokenization(self):
        self.assertIsNone(self.lexicon.lookup("zxqvunknown")["pos"])
        self.assertEqual(self.lexicon.lookup(".")["lexicon"], "unknown")
        self.assertEqual(tokenize("Rabbit's carrot, isn't it? 12.5"),
                         ["Rabbit's", "carrot", ",", "isn't", "it", "?", "12.5"])


if __name__ == "__main__":
    unittest.main()
