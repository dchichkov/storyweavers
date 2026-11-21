"""Evidence checks for beat readings on intact source documents."""
from copy import deepcopy
import unittest

from .beat_annotations import reading, annotate_beats, validate_beats, _validate_beat_references
from .story_memory import annotate
from .storytelling.runtime import generate
from .storytelling.seed_worlds.catalog import SEED_SCENARIOS


class BeatAnnotationEvidenceTests(unittest.TestCase):
    def test_discovery_references_reject_future_unseen_and_wrong_source(self):
        original = annotate(generate('museum', 19, beat_budget=6, continuations='expanded'))
        for mutation in ('future_discovery', 'future_related', 'non_discovery', 'not_visible', 'wrong_plan'):
            doc = deepcopy(original)
            event = next(e for e in doc['events'] if any('discovery_event' in c
                         for c in (e.get('beat_expansion') or {}).get('candidates', [])))
            candidate = next(c for c in event['beat_expansion']['candidates'] if 'discovery_event' in c)
            if mutation == 'future_discovery':candidate['discovery_event'] = event['id']
            elif mutation == 'future_related':candidate['related_events'][0]['event'] = event['id']
            elif mutation == 'non_discovery':
                candidate['discovery_event'] = doc['events'][0]['id']
                candidate['related_events'][0]['event'] = doc['events'][0]['id']
            elif mutation == 'not_visible':
                next(e for e in doc['events'] if e['id'] == candidate['discovery_event'])['narrated'] = False
            else:candidate['planned_event'] = 'little_wings'
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'discovery|related beat'):
                validate_beats(doc)

    def test_authored_discovery_bridges_logistics_but_adjacent_claim_does_not(self):
        doc = annotate(generate('market', 19, beat_budget=6, continuations='expanded'))
        event = self.event(doc, 'correct_weight')
        candidate = next(c for c in event['beat_expansion']['candidates'] if 'discovery_event' in c)
        self.assertEqual(candidate['related_events'][0]['basis'], 'authored_link')
        self.assertNotEqual(candidate['preceding_event'], candidate['discovery_event'])
        self.assertTrue(validate_beats(doc))
        candidate['related_events'][0]['basis'] = 'adjacent_discovery'
        with self.assertRaisesRegex(ValueError, 'not adjacent'):validate_beats(doc)
        # Sharing light follows a clue, but the bank does not claim this action
        # uses that clue: the weaker adjacent reading must remain explicit.
        doc = annotate(generate('camp', 19, beat_budget=6, continuations='expanded'))
        candidate = next(c for c in self.event(doc, 'share_light')['beat_expansion']['candidates']
                         if 'discovery_event' in c)
        candidate['related_events'][0]['basis'] = 'authored_link'
        with self.assertRaisesRegex(ValueError, 'unsupported authored'):validate_beats(doc)

    def test_resumed_discovery_keeps_bound_source_arc(self):
        # Both units have the same authored native kinds; their prefixes are
        # different physical bindings and must never share discovery evidence.
        doc = dict(scenario='joined', source_options=dict(transfer=dict(units=[
            dict(scenario='museum', prefix='u0__'), dict(scenario='museum', prefix='u1__')])))
        prior = {4:dict(id=4, kind='u0__read_small_print', narrated=True),
                 5:dict(id=5, kind='u0__exhibit_goal', narrated=False)}
        beat = dict(discovery_event=4, planned_event='u0__clay_support', related_events=[
            dict(event=4, relation='uses_discovery', basis='adjacent_discovery')])
        _validate_beat_references(doc, beat, 'u0__clay_support', prior)
        beat['planned_event'] = 'u1__clay_support'
        with self.assertRaisesRegex(ValueError, 'bound source arc'):
            _validate_beat_references(doc, beat, 'u1__clay_support', prior)

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

    def joined_rows(self):
        from .plot_continuation import catalogue, run
        pool = catalogue([annotate(generate('pottery', 3006))])
        return run(pool, 'changed_approach', seed=19, beat_budget=6)['rows']

    def test_joined_detail_setups_survive_document_boundaries(self):
        from .beat_qa import questions
        rows = self.joined_rows();last = annotate(rows[-1])
        self.assertEqual(set(last['beats']['details']), {'u0__pottery:grip', 'u0__pottery:dent'})
        expected = {'u0__pottery:grip': ('u0__grandpa', 2), 'u0__pottery:dent': ('u0__cup', 4)}
        links = [link for event in last['events'] for link in event['detail_links']]
        self.assertEqual({link['detail'] for link in links}, set(expected))
        current = {e['id'] for e in last['events']}
        for key, (entity, setup) in expected.items():
            detail = last['beats']['details'][key]
            self.assertEqual((detail['entity'], detail['setup_event']), (entity, setup))
            self.assertFalse(detail['setup_in_document'])
            self.assertNotIn(setup, current)
        for proof in last['beats']['prior_setup_events']:
            self.assertFalse(proof['text_available'])
            self.assertTrue(proof['narrated'])
        for link in links:
            self.assertFalse(link['setup_in_document'])
            self.assertEqual(link['entity'], expected[link['detail']][0])
            self.assertIn(link['result_event'], current)
        # Preserved history references do not conjure earlier prose for QA.
        self.assertFalse(any(q['kind'] == 'detail_payoff' for q in questions(rows[-1])))

    def test_inherited_detail_evidence_fails_closed(self):
        row = self.joined_rows()[-1];doc = annotate(row)
        for mutation in ('future', 'invisible', 'unbound', 'different_entity'):
            bad = deepcopy(row)
            detail = bad['initial_world']['narrative']['beats']['details']['u0__pottery:dent']
            if mutation == 'future':detail['setup_event'] = 99999
            elif mutation == 'invisible':
                next(e for e in bad['initial_world']['history'] if e['id'] == detail['setup_event'])['narrated'] = False
            elif mutation == 'unbound':detail['entity'] = 'missing'
            else:detail['entity'] = 'u0__tool'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                annotate_beats(deepcopy(doc), row=bad)
        broken = deepcopy(doc);broken['beats']['prior_setup_events'][0]['text_available'] = True
        with self.assertRaisesRegex(ValueError, 'prior detail'):validate_beats(broken)


if __name__ == '__main__':
    unittest.main()
