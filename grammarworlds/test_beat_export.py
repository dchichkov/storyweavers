"""Archived beats replay their recorded state, not a newly sampled policy."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from .beat_annotation_export import replay_document, export
from .beat_annotations import DETAILS
from .story_memory import annotate, load_documents
from .storytelling.runtime import generate


class BeatArchiveReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [generate('museum', 19, beat_budget=6, continuations='expanded', tense=tense)
                    for tense in ('past', 'present')]
        cls.documents = [annotate(row) for row in cls.rows]

    def test_expanded_past_and_present_preserve_entities_and_narrative(self):
        for row, doc in zip(self.rows, self.documents):
            before = deepcopy(doc)
            replayed = replay_document(doc)
            self.assertEqual(replayed['initial_world'], row['initial_world'])
            self.assertEqual(replayed['final_world']['entities'], row['final_world']['entities'])
            self.assertEqual(replayed['final_world']['narrative'], row['final_world']['narrative'])
            self.assertTrue(replayed['annotation_replay']['final_narrative_verified'])
            self.assertGreater(replayed['annotation_replay']['recorded_beats'], 0)
            self.assertEqual(doc, before)

    def test_plain_archive_needs_no_beat_outcome(self):
        row = generate('bakery', 3000, continuations='expanded');doc = annotate(row)
        replayed = replay_document(doc)
        self.assertEqual(replayed['final_world']['entities'], row['final_world']['entities'])
        self.assertFalse(replayed['annotation_replay']['final_narrative_verified'])
        self.assertFalse(replayed['annotation_replay']['current_beat_policy_recomputed'])

    def test_resumed_joined_archive_uses_receiving_history_and_plot_state(self):
        from .plot_continuation import catalogue, run
        pool = catalogue([annotate(generate('pottery', 3006))])
        result = run(pool, 'changed_approach', seed=19, beat_budget=6)
        for row in result['rows'][1:]:
            doc = annotate(row);replayed = replay_document(doc)
            self.assertEqual(replayed['initial_world'], row['initial_world'])
            self.assertEqual(replayed['final_world']['entities'], row['final_world']['entities'])
            self.assertEqual(replayed['final_world']['narrative'], row['final_world']['narrative'])
            self.assertEqual(replayed['annotation_replay']['initial_state_source'], 'receiving_transfer_options')

    def test_current_policy_and_removed_or_added_details_do_not_rewrite_history(self):
        row, doc = self.rows[0], self.documents[0]
        extra = dict(name='new_today', entity='shadow', state='large', setup='moving_light',
                     result='little_wings', object='shadow')
        for definitions in ([], DETAILS['museum'] + [extra]):
            with self.subTest(definitions=len(definitions)), patch.dict(DETAILS, {'museum': definitions}), \
                    patch('grammarworlds.beat_generation.options', side_effect=AssertionError('resampling forbidden')):
                replayed = replay_document(doc)
                self.assertEqual(replayed['final_world']['narrative'], row['final_world']['narrative'])
                self.assertEqual(replayed['final_world']['entities'], row['final_world']['entities'])

    def decision_document(self):
        doc = deepcopy(self.documents[0])
        event = next(e for e in doc['events'] if e.get('beat_expansion')
                     and e['beat_expansion']['selected'] != 'immediate')
        decision = event['beat_expansion']
        selected = next(c for c in decision['candidates'] if c['id'] == decision['selected'])
        return doc, event, decision, selected

    def test_recorded_distribution_surface_and_predecessor_are_checked(self):
        for mutation in ('negative', 'nonfinite', 'wrong_weight', 'surface', 'future', 'duplicate'):
            doc, event, decision, selected = self.decision_document()
            if mutation == 'negative':selected['probability'] = -1
            elif mutation == 'nonfinite':selected['weight'] = float('nan')
            elif mutation == 'wrong_weight':selected['weight'] *= 2
            elif mutation == 'surface':selected['text'] = 'Something absent from the archived story.'
            elif mutation == 'future':selected['preceding_event'] = 99999
            else:decision['candidates'].append(deepcopy(selected))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):replay_document(doc)

    def test_source_state_effects_and_final_narrative_are_checked(self):
        for mutation in ('initial', 'effect', 'narrative', 'event_id'):
            doc = deepcopy(self.documents[0])
            if mutation == 'initial':doc['entities']['hero']['initial']['state'].append('invented')
            elif mutation == 'effect':
                next(e for e in doc['events'] if e['effects'])['effects'] = {}
            elif mutation == 'narrative':doc['narrative_outcome']['beats']['used'] = 999
            else:doc['events'][0]['id'] = 99999
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):replay_document(doc)

    def test_export_preserves_historical_annotations_when_catalogue_removed(self):
        doc = self.documents[0]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary);source = root/'source.memory.json';source.write_text(json.dumps(doc))
            with patch.dict(DETAILS, {'museum': []}), redirect_stdout(io.StringIO()):
                export(source, root/'exported')
            result = load_documents(root/'exported')[0]
            self.assertEqual(result['text'], doc['text'])
            self.assertEqual(result['attributes'], doc['attributes'])
            self.assertEqual(result['tokens'], doc['tokens'])
            self.assertEqual(result['narrative_outcome'], doc['narrative_outcome'])
            self.assertEqual(result['beats']['export_replay']['annotation_refresh'],
                             'preserved_archived_annotations_for_changed_detail_catalogue')

    def test_failed_export_does_not_publish_partial_archive(self):
        doc, _, _, selected = self.decision_document();selected['probability'] = -1
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary);source = root/'source.memory.json';source.write_text(json.dumps(doc))
            with self.assertRaises(ValueError):export(source, root/'exported')
            self.assertFalse((root/'exported'/'stories.memory.jsonl.gz').exists())
            self.assertFalse((root/'exported'/'.stories.memory.jsonl.gz.pending').exists())


if __name__ == '__main__':
    unittest.main()
