"""Reviewed physical motifs: visible planting, changed state, same carrier."""
import unittest

from .beat_annotations import DETAILS
from .beat_generation import commit, options
from .grammar import text
from .story_memory import annotate
from .storytelling.runtime import generate, setup
from .world import Frame


NEW_WORLDS = ('greenhouse', 'library', 'snow', 'picnic', 'market', 'camp',
              'orchard', 'costume', 'pond', 'festival')


class BeatDetailEvidenceTests(unittest.TestCase):
    def test_callback_metadata_matches_phrases_and_native_kernels(self):
        for scenario in NEW_WORLDS:
            pack, world = setup(scenario, 3000)
            for spec in DETAILS[scenario]:
                with self.subTest(scenario=scenario):
                    self.assertIn(spec['entity'], world.entities)
                    self.assertTrue(set(spec['setup'].split()) <= pack.KERNELS.keys())
                    self.assertTrue(set(spec['result'].split()) <= pack.KERNELS.keys())
                    self.assertNotEqual(spec['state'], spec['callback']['state'])
                    for tense in ('past', 'present'):
                        self.assertEqual(len(text(spec['callback'][tense]).children), len(spec['callback'][tense + '_pos']))
                        self.assertEqual(spec['callback'][tense + '_pos'][-1], 'PUNCT')

    def test_ten_visible_same_entity_setups_and_later_changed_states(self):
        for scenario in NEW_WORLDS:
            row = generate(scenario, 3000, continuations='expanded');doc = annotate(row)
            history = {e['id']: e for e in row['final_world']['history']}
            for spec in DETAILS[scenario]:
                with self.subTest(scenario=scenario):
                    detail = doc['beats']['details'][scenario + ':' + spec['name']]
                    setup_event = history[detail['setup_event']]
                    self.assertTrue(setup_event['narrated'])
                    self.assertTrue(setup_event['sentence'])
                    self.assertIn(spec['state'], setup_event['after']['entities'][spec['entity']]['state'])
                    results = [e for e in row['final_world']['history']
                               if e['frame']['kind'] in spec['result'].split()]
                    self.assertTrue(results)
                    self.assertTrue(any(spec['callback']['state'] in e['before']['entities'][spec['entity']]['state']
                                        for e in results))
                    for event in doc['events']:
                        for link in event['detail_links']:
                            self.assertEqual(link['entity'], spec['entity'])
                            self.assertLess(link['setup_event'], link['result_event'])

    def test_optional_callback_requires_the_actual_changed_state(self):
        for scenario in NEW_WORLDS:
            row = generate(scenario, 3000, continuations='expanded')
            pack, world = setup(scenario, 3000, beat_budget=6)
            spec = DETAILS[scenario][0];found = False
            for saved in row['final_world']['history']:
                frame = Frame(**{**saved['frame'], 'cause_ids':tuple(saved['frame']['cause_ids'])})
                if frame.kind in spec['result'].split():
                    before = world.to_dict()
                    candidates = options(pack, world, frame)
                    echoes = [c for c in candidates if c['detail'] == scenario + ':' + spec['name']]
                    if echoes:
                        self.assertEqual(world.to_dict(), before)
                        self.assertEqual(echoes[0]['object'], spec['entity'])
                        self.assertIn(spec['callback']['state'], world.entities[spec['entity']].state)
                        broken = world.clone();broken.entities[spec['entity']].state.discard(spec['callback']['state'])
                        self.assertFalse(any(c['detail'] == echoes[0]['detail'] for c in options(pack, broken, frame)))
                        found = True;break
                record = pack.commit(world, frame, saved['sentence'])
                record['narrated'] = saved['narrated'];commit(pack, world, record, None)
            self.assertTrue(found, scenario)


if __name__ == '__main__':
    unittest.main()
