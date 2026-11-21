"""Text-preserving annotation retrieval and guarded cross-world execution."""
from copy import deepcopy
import unittest

from .storytelling.runtime import generate, SCENARIOS
from .story_memory import annotate, query, retrieve, generate_retrieved, validate
from .event_line_replay import paper_world, world_from_dict
from .world import Entity


def craft_world():
    world = paper_world()
    world.entities['ada'].properties.update({'can_shape_clay','can_drum','can_prepare_support',
                                            'can_sketch_moon','can_repair_fixture'})
    world.entities['ada'].state.add('practiced')
    world.entities.update(
        clay=Entity('clay','cup','object','bench',properties={'clay'},state={'wet'}),
        rib=Entity('rib','shaping rib','tool','ada',properties={'shape'}),
        drum=Entity('drum','drum','instrument','ada',properties={'portable','physics:drum'}),
        ladder=Entity('ladder','ladder','tool','bench',properties={'portable','reach'}),
        tap=Entity('tap','tap','object','garden',properties={'repairable_fixture'},state={'broken'}),
        sheet=Entity('sheet','paper','object','ada',properties={'drawable'},state={'blank'}),
        pencil=Entity('pencil','pencil','tool','ada',properties={'draw'}),
        atlas=Entity('atlas','atlas','object','ada',properties={'moon_reference'},state={'moon_picture'}))
    return world


class StoryMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {s: generate(s,3000,continuations='expanded',symbolic_heads=True) for s in SCENARIOS}
        cls.documents = [annotate(row) for row in cls.rows.values()]

    def test_all_seven_texts_tokens_and_candidate_attributes_are_preserved(self):
        for doc in self.documents:
            row = self.rows[doc['scenario']]
            self.assertTrue(validate(doc)); self.assertEqual(doc['text'],row['story'])
            self.assertEqual(len(doc['tokens']),len(row['attribute_generation']['tokens']))
            for token, source in zip(doc['tokens'],row['attribute_generation']['tokens']):
                self.assertEqual(token['token'],source['token'])
                self.assertEqual(token['position'],source['position'])
                for candidate, original in zip(token['candidates'],source['candidates']):
                    self.assertEqual(candidate['probability'],original['probability'])
                    self.assertEqual(doc['attributes'][candidate['attributes']],
                        row['trace'][source['scene_index']]['attribute_table'][original['attributes']])
            self.assertTrue(all('text' not in e for e in doc['events']))

    def test_annotating_does_not_modify_input(self):
        row = self.rows['kite']; before = deepcopy(row)
        annotate(row)
        self.assertEqual(row,before)

    def test_queries_return_references_and_keep_context_available(self):
        hits = query(self.documents,event_kind='mend',entity='target',entity_property='flyable')
        self.assertEqual(len(hits),1)
        hit = hits[0]; doc = next(d for d in self.documents if d['id']==hit['document'])
        self.assertIn('repair.paper',hit['mapping_rules'])
        self.assertTrue(hit['token_ids'])
        self.assertNotIn('text',hit)
        self.assertGreater(len(doc['tokens']),len(hit['token_ids']))
        self.assertTrue(query(self.documents,action='cover'))
        self.assertFalse(query(self.documents,event_kind='made_up'))

    def test_every_world_has_a_reviewed_mapping_in_sample(self):
        covered = {h['scenario'] for h in query(self.documents,portable_only=True)}
        self.assertEqual(covered,set(SCENARIOS))
        visible = {h['scenario'] for h in query(self.documents,portable_only=True) if h['token_ids']}
        self.assertEqual(visible,set(SCENARIOS))

    def test_source_observations_are_separate_from_prediction_attributes(self):
        for doc in self.documents:
            for token in doc['tokens']:
                self.assertEqual(token['memory']['scope'],'source_event_boundaries')
                for candidate in token['candidates']:
                    self.assertEqual(doc['attributes'][candidate['attributes']]['event']['status'],'proposed')
                for obs in token['memory']['entity_observations']:
                    if obs['confirmed_in_source_event']:
                        self.assertIn('before',obs); self.assertIn('after',obs)

    def test_silent_events_have_boundaries_without_invented_words(self):
        silent = [e for d in self.documents for e in d['events'] if e['anchor']['silent']]
        self.assertTrue(silent)
        self.assertTrue(all(not e['token_ids'] for e in silent))

    def test_new_practice_and_clay_events_generate_in_unrelated_world(self):
        world = craft_world(); before = world.to_dict()
        for operation, entity, state in [('shape_clay','clay','shaped'),('perform_solo','ada','performed_solo'),
                                         ('prepare_support','ladder','steady'),('repair_fixture','tap','repaired'),
                                         ('sketch_moon','sheet','moon_drawing')]:
            row = generate_retrieved(self.documents,world,operations=[operation],bindings={'worker':'ada'},seed=7)
            self.assertEqual(row['status'],'complete')
            self.assertIn(state,row['final_world']['entities'][entity]['state'])
            self.assertIn('Ada',row['story'])
            self.assertTrue(row['source']['memory_retrieval']['references'])
        self.assertEqual(world.to_dict(),before)

    def test_source_emotion_and_rename_are_not_forced_on_target_drawing(self):
        world = craft_world()
        row = generate_retrieved(self.documents,world,operations=['sketch_moon'],seed=7)
        self.assertEqual(row['final_world']['entities']['ada']['memes'],world.entities['ada'].memes)
        self.assertEqual(row['final_world']['entities']['sheet']['noun'],'paper')
        self.assertTrue(row['source']['untransferred_context'][0]['source_entity_effects'])

    def test_compound_watering_and_checkout_are_not_reduced_to_simple_transfers(self):
        for kind in ('water_first','water_second','checkout'):
            hits = query(self.documents,event_kind=kind)
            self.assertTrue(hits)
            self.assertTrue(all(not h['mapping_rules'] for h in hits))

    def test_requery_after_fetch_exposes_repair_without_copying_source_state(self):
        world = paper_world()
        self.assertFalse(retrieve(self.documents,world,operations=['patch_paper'])['candidates'])
        fetch = generate_retrieved(self.documents,world,operations=['fetch'],bindings={'worker':'ada'},seed=7)
        current = world_from_dict(fetch['final_world'],allow_history=True)
        repaired = generate_retrieved(self.documents,current,operations=['patch_paper'],seed=7)
        self.assertEqual(repaired['final_world']['entities']['book']['state'],['repaired'])
        self.assertNotIn('flyable',repaired['final_world']['entities']['book']['properties'])
        self.assertEqual(repaired['final_world']['history'][0],fetch['final_world']['history'][0])

    def test_duplicate_source_records_do_not_inflate_mapping_mass(self):
        a = retrieve(self.documents,paper_world(),operations=['fetch'])
        b = retrieve(self.documents*2,paper_world(),operations=['fetch'])
        self.assertEqual(len(a['candidates']),len(b['candidates']))
        for x,y in zip(a['candidates'],b['candidates']):
            self.assertEqual(x['probability'],y['probability'])
            self.assertEqual(len(y['references']),2*len(x['references']))

    def test_missing_ability_blocks_instead_of_importing_it(self):
        world = craft_world(); world.entities['ada'].properties.remove('can_shape_clay')
        before = world.to_dict()
        result = retrieve(self.documents,world,operations=['shape_clay'])
        self.assertFalse(result['candidates']); self.assertTrue(result['rejected'])
        self.assertEqual(world.to_dict(),before)

    def test_corrupt_source_text_and_token_references_rejected(self):
        for change in ('text','token','owner'):
            doc = deepcopy(self.documents[0])
            if change=='text': doc['text'] += ' altered'
            elif change=='token': doc['tokens'][0]['token']='altered'
            else: doc['tokens'][0]['memory']['event_id']=-1
            with self.assertRaises(ValueError):validate(doc)


if __name__=='__main__':unittest.main()
