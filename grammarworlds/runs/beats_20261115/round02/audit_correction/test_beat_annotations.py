"""Evidence checks for beat readings on intact source documents."""
from copy import deepcopy
import unittest

from .beat_annotations import reading, annotate_beats, validate_beats
from .story_memory import annotate
from .storytelling.runtime import generate
from .storytelling.seed_worlds.catalog import SEED_SCENARIOS


class BeatAnnotationEvidenceTests(unittest.TestCase):
    def document(self, scenario, seed=3000):
        return annotate(generate(scenario, seed, continuations='expanded'))

    def event(self, document, kind):
        return next(e for e in document['events'] if e['kind'] == kind)

    def test_reviewed_experiencers_differ_from_physical_actor(self):
        for scenario, kind, expected, actor in (
            ('greenhouse', 'shade_break', 'hero', 'cloth'),
            ('museum', 'read_small_print', 'hero', 'helper'),
            ('trail', 'felix_clears_ivy', 'leni', 'helper'),
            ('pond', 'drifting_boat', 'helper', 'hero'),
            ('orchard', 'pear_promise', 'helper', 'hero'),
        ):
            with self.subTest(scenario=scenario):
                event = self.event(self.document(scenario), kind)
                beat = event['beats'][0]
                self.assertEqual(beat['experiencer'], expected)
                self.assertEqual(beat['action_actor'], actor)
                self.assertNotEqual(beat['experiencer_basis'], 'frame_actor_perspective')

    def test_event_name_and_any_speaker_do_not_imply_speech_act(self):
        for scenario, kind in (
            ('bakery', 'birthday_request'), ('festival', 'rethink_access'),
            ('orchard', 'pear_promise'), ('puppets', 'make_replacement'),
        ):
            with self.subTest(scenario=scenario):
                event = self.event(self.document(scenario), kind)
                self.assertTrue(any('speaker' in tags for tags in event['entity_tags'].values()))
                self.assertIsNone(event['beats'][0]['speech_act'])

    def test_supported_speech_has_same_person_and_visible_token_evidence(self):
        for scenario, kind, expected in (
            ('pottery', 'consult', 'suggesting'), ('laundry', 'ask_help', 'asking'),
            ('market', 'admit_error', 'admitting'), ('music', 'decline', 'disagreeing'),
        ):
            with self.subTest(scenario=scenario):
                doc = self.document(scenario);event = self.event(doc, kind)
                beat = event['beats'][0]
                self.assertEqual(beat['speech_act'], expected)
                evidence = beat['speech_evidence']
                self.assertEqual(evidence['speaker'], beat['experiencer'])
                self.assertTrue(evidence['token_ids'])
                self.assertIn('speaker', event['entity_tags'][beat['experiencer']])
                self.assertTrue(set(evidence['token_ids']) <= set(event['token_ids']))

    def test_shared_reading_rebinds_and_requires_the_specific_speaker(self):
        frame = dict(actor='receiver', patient='target', instrument='')
        people = {'receiver': dict(kind='person'), 'recipient': dict(kind='person'),
                  'target': dict(kind='object')}
        before = deepcopy(people)
        args = dict(scenario='pottery', mapping={'grandpa': 'recipient'},
                    roles={'protagonist': ['receiver']}, entities=people)
        # A helper talking does not mean the recipient made a suggestion.
        silent = reading('consult', 'discovery', frame, 1, speakers=['receiver'], **args)
        self.assertIsNone(silent['speech_act'])
        # The physical actor must match the reviewed speech subject as well.
        frame['actor'] = 'recipient'
        voiced = reading('consult', 'discovery', frame, 1, speakers=['recipient'], **args)
        self.assertEqual(voiced['speech_act'], 'suggesting')
        self.assertEqual(people, before)

    def test_twenty_world_native_experiencers_are_people(self):
        count = 0
        for scenario in SEED_SCENARIOS:
            doc = self.document(scenario)
            for event in doc['events']:
                for beat in event['beats']:
                    record = doc['entities'][beat['experiencer']]
                    self.assertEqual((record['initial'] or record['final'])['kind'], 'person')
                    count += 1
        self.assertEqual(len(SEED_SCENARIOS), 20)
        self.assertGreater(count, 100)

    def test_archived_posterior_uses_each_candidate_event_not_selected_scene(self):
        row = generate('bakery', 3000, continuations='expanded')
        doc = annotate(row)
        # Simulate the original archive, which predates live beat attributes.
        for attributes in doc['attributes'].values():attributes.pop('beat', None)
        before = deepcopy(doc)
        annotate_beats(doc, row=row)
        alternatives = 0
        for event in doc['events']:
            for tid in event['token_ids']:
                token = doc['tokens'][tid]
                for candidate, projected in zip(token['candidates'], token['memory']['beat_candidates']):
                    attributes = doc['attributes'][candidate['attributes']]
                    self.assertEqual(projected['attributes'], candidate['attributes'])
                    self.assertEqual(projected['probability'], candidate['probability'])
                    if projected['beat']:
                        self.assertEqual(projected['beat']['source_kind'], attributes['event']['source_kind'])
                        self.assertEqual(projected['beat']['scope'], 'reconstructed_candidate_event')
                    alternatives += attributes['event']['source_kind'] != event['kind']
        self.assertGreater(alternatives, 0)
        self.assertEqual(doc['text'], before['text'])
        self.assertEqual(doc['attributes'], before['attributes'])
        self.assertEqual([(t['token'], t['position'], t['candidates']) for t in doc['tokens']],
                         [(t['token'], t['position'], t['candidates']) for t in before['tokens']])

    def test_validator_rejects_invalid_or_reassigned_posterior(self):
        doc = self.document('pottery')
        for probability in (-1, 2, float('nan'), float('inf'), True):
            bad = deepcopy(doc)
            bad['tokens'][0]['memory']['beat_candidates'][0]['probability'] = probability
            with self.subTest(probability=probability), self.assertRaises(ValueError):validate_beats(bad)
        bad = deepcopy(doc)
        bad['tokens'][0]['memory']['beat_candidates'][0]['attributes'] = 'different event'
        with self.assertRaisesRegex(ValueError, 'differs from candidate'):validate_beats(bad)
        bad = deepcopy(doc)
        bad['tokens'][0]['memory']['beat_candidates'][0]['beat'] = {'kind': 'payoff'}
        with self.assertRaisesRegex(ValueError, 'differs from candidate'):validate_beats(bad)
        bad = deepcopy(doc);bad['tokens'][0]['memory']['beats'] = []
        with self.assertRaisesRegex(ValueError, 'context differs'):validate_beats(bad)

    def test_validator_rejects_future_detail_and_foreign_entity(self):
        doc = self.document('pottery')
        index = next(i for i, e in enumerate(doc['events']) if e['detail_links'])
        for field, value in [('setup_event', 999999), ('result_event', -1), ('entity', 'tool')]:
            bad = deepcopy(doc);bad['events'][index]['detail_links'][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'detail link'):validate_beats(bad)

    def test_old_v1_annotations_remain_readable(self):
        doc = self.document('pottery');doc['beats']['schema'] = 'story-beats-v1'
        for token in doc['tokens']:
            for candidate in token['memory']['beat_candidates']:
                candidate.pop('attributes');candidate.pop('basis')
        self.assertTrue(validate_beats(doc))

    def test_posterior_roundoff_is_preserved_without_clamping(self):
        row = generate('pottery', 3000, continuations='expanded');doc = annotate(row)
        token = next(t for t in doc['tokens'] if len(t['candidates']) == 1)
        token['candidates'][0]['probability'] = 1.0000000000000002
        annotate_beats(doc, row=row)
        self.assertEqual(token['memory']['beat_candidates'][0]['probability'], 1.0000000000000002)
        self.assertTrue(validate_beats(doc))


if __name__ == '__main__':
    unittest.main()
