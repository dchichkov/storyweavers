"""Native mechanics reuse: target carriers, live guards, distributions and provenance."""
from copy import deepcopy
from dataclasses import replace
import json
import unittest

from .world import Entity
from .memory_transfer import run, attach, proposals, receiving_world, setup_joined, decode_world
from .story_memory import annotate, validate
from .storytelling.runtime import generate, replay, setup, build_forest
from .storytelling.seed_worlds.catalog import SEED_SCENARIOS
from .storytelling.surface import detokenize


class MemoryTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs={s:annotate(generate(s,3007,continuations='expanded')) for s in SEED_SCENARIOS}

    def test_all_twenty_transfer_compound_native_programs(self):
        for scenario,doc in self.docs.items():
            with self.subTest(scenario=scenario):
                row=run([doc],[dict(scenario=scenario,extent='story')],seed=7)
                self.assertTrue(replay(row))
                self.assertTrue(validate(annotate(row)))
                self.assertEqual(len(row['trace']),len(doc['events']))
                self.assertEqual(row['transfer_summary']['sources'],[scenario])
                self.assertIn('Nia',row['story'])
                if doc['entities']['hero']['initial']['noun']!='Nia':
                    self.assertNotIn(doc['entities']['hero']['initial']['noun'],row['story'])
                self.assertTrue(row['world_qa'])
                p,w=setup_joined(row['options']['transfer'])
                for saved in row['final_world']['history']:
                    frame=p.candidates(w)[0][1]
                    self.assertLessEqual(set(frame.cause_ids),{f.id for f in w.facts_for_attention()})
                    event=p.commit(w,frame,saved['sentence'])
                    for key in ('referents','speakers','narrated'):event[key]=saved[key]
                for q in row['world_qa']:
                    self.assertEqual(q['scope'],'executed_target_world')
                    self.assertGreaterEqual(q['answer'].count('.'),2)

    def test_named_compound_event_pulls_prefix_and_existing_trolley(self):
        world=receiving_world()
        world.entities['trolley']=Entity('trolley','garden trolley','object','nia',
                                         properties={'portable'},state={'rattling'})
        before=world.to_dict();doc=deepcopy(self.docs['repair'])
        row=run([doc],[dict(event='refit_and_test',bindings={'cart':'trolley'})],world,seed=7)
        self.assertEqual(world.to_dict(),before);self.assertEqual(doc,self.docs['repair'])
        self.assertIn('garden trolley',row['story']);self.assertNotIn('blue cart',row['story'])
        self.assertEqual(row['final_world']['entities']['trolley']['state'],['repaired'])
        self.assertNotIn('repaired',row['initial_world']['entities']['trolley']['state'])
        self.assertEqual(row['trace'][-1]['frame']['kind'],'u0__refit_and_test')
        kinds=[e['transfer']['source_kind'] for e in row['final_world']['history']]
        self.assertIn('diagnose_string',kinds);self.assertNotIn('quiet_wheel',kinds)
        attributes=[a for t in row['trace'] for a in t['attribute_table'].values()]
        self.assertTrue(any(a.get('entity')=='trolley' for a in attributes))
        self.assertTrue(all(a.get('entity') in {None,*row['initial_world']['entities']} for a in attributes))

    def test_live_object_state_is_not_overwritten_to_make_transfer_fit(self):
        world=receiving_world()
        world.entities['cart']=Entity('cart','blue cart','object','nia',properties={'portable'},state={'repaired'})
        before=world.to_dict()
        with self.assertRaisesRegex(ValueError,'no feasible'):
            attach([self.docs['repair']],[dict(event='refit_and_test',bindings={'cart':'cart'})],world)
        self.assertEqual(world.to_dict(),before)

    def test_unique_problem_state_can_infer_analogous_receiving_target(self):
        world=receiving_world()
        world.entities['trolley']=Entity('trolley','garden trolley','object','nia',
                                         properties={'portable'},state={'rattling'})
        row=run([self.docs['repair']],[dict(event='refit_and_test')],world,seed=7)
        self.assertEqual(row['options']['transfer']['units'][0]['mapping']['cart'],'trolley')
        self.assertEqual(row['final_world']['entities']['trolley']['state'],['repaired'])
        candidates=row['transfer_decisions'][0]['candidates']
        reuse=next(c for c in candidates if c['bindings']['cart']=='trolley')
        self.assertGreater(reuse['probability'],.75)
        self.assertTrue(any(c['factors']['reuse_bonus']==1 for c in candidates))

    def test_missing_carrier_and_changed_guard_block_without_mutation(self):
        transfer=attach([self.docs['repair']],[dict(event='refit_and_test')])
        pack,world=setup_joined(transfer)
        while not pack.candidates(world)[0][1].kind.endswith('tighten_wrongly'):
            pack.commit(world,pack.candidates(world)[0][1],'')
        frame=pack.candidates(world)[0][1]
        for edit in ('drop_tool','remove_rattle'):
            broken=world.clone()
            if edit=='drop_tool':broken.entities['u0__spanner'].location='workshop'
            else:broken.entities['u0__cart'].state.remove('rattling')
            before=broken.to_dict()
            with self.assertRaises(ValueError):pack.commit(broken,frame,'forged')
            self.assertEqual(broken.to_dict(),before)
        broken=world.clone();del broken.entities['u0__wheel']
        self.assertEqual(pack.candidates(broken),[])

    def test_character_attribute_leakage_is_explicit_and_optional(self):
        transfer=attach([self.docs['music']],[dict(scenario='music',extent='story')])
        leaks=transfer['units'][0]['leakage']
        self.assertTrue(any(x['kind']=='character_attributes' and x['states'] for x in leaks))
        with self.assertRaisesRegex(ValueError,'source attributes'):
            attach([self.docs['music']],[dict(scenario='music')],leak=False)

    def test_three_sources_join_with_shared_people_and_separate_flags(self):
        docs=[self.docs[s] for s in ('repair','museum','music')]
        requests=[dict(scenario=s,extent='story') for s in ('repair','museum','music')]
        row=run(docs,requests,seed=7)
        self.assertEqual(row['transfer_summary']['sources'],['repair','museum','music'])
        self.assertTrue(replay(row));self.assertTrue(validate(annotate(row)))
        self.assertEqual(len(row['trace']),sum(len(d['events']) for d in docs))
        for decision in row['transfer_decisions']:
            self.assertAlmostEqual(sum(c['probability'] for c in decision['candidates']),1.)
        self.assertEqual(detokenize([t['token'] for t in row['attribute_generation']['tokens']]),row['story'])
        self.assertEqual(row['initial_world']['entities']['nia']['noun'],'Nia')
        self.assertTrue(all(not s['claims'] for s in row['scenes']))

    def test_duplicate_sources_do_not_change_probability_and_seed_is_reproducible(self):
        docs=[annotate(generate('repair',seed)) for seed in range(6)]
        request=dict(event='refit_and_test')
        a=proposals(docs,request);b=proposals(docs*2,request)
        self.assertEqual([c['probability'] for c in a],[c['probability'] for c in b])
        self.assertGreater(len(a),1)
        self.assertEqual(run(docs,[request],seed=7),run(docs,[request],seed=7))
        rows=[run(docs,[request],seed=s) for s in range(6)]
        self.assertGreater(len({tuple(t['frame']['kind'] for t in r['trace']) for r in rows}),1)

    def test_prediction_and_annotated_distributions_use_target_prefix_only(self):
        transfer=attach([self.docs['repair']],[dict(event='refit_and_test')])
        pack,world=setup_joined(transfer);before=world.to_dict()
        forest,_=build_forest(pack,world,predict_attributes=True,continuations='expanded')
        self.assertEqual(world.to_dict(),before)
        self.assertAlmostEqual(sum(c['probability'] for c in forest.predict(())['choices']),1.)
        row=run([self.docs['repair']],[dict(event='refit_and_test')],seed=7)
        for trace in row['trace']:
            for step in trace['word_trace']:
                self.assertAlmostEqual(sum(c['probability'] for c in step['choices']),1.)
        for token in row['attribute_generation']['tokens']:
            self.assertAlmostEqual(sum(c['probability'] for c in token['candidates']),1.)

    def test_live_receiver_history_survives_and_replays(self):
        first=run([self.docs['repair']],[dict(event='refit_and_test')],seed=7)
        world=decode_world(first['final_world']);world.flags.discard('ended')
        old=world.to_dict();row=run([self.docs['museum']],[dict(event='controlled_trial')],world,seed=3)
        self.assertTrue(replay(row));self.assertTrue(validate(annotate(row)))
        self.assertEqual(row['final_world']['history'][:len(old['history'])],old['history'])
        self.assertEqual(world.to_dict(),old)
        self.assertNotEqual(row['options']['transfer']['units'][0]['prefix'],'u0__')

    def test_invalid_and_aliased_bindings_fail(self):
        for bindings in ({'hero':'missing'}, {'cart':'nia'}, {'hero':'nia','helper':'nia'}, {'wrong':'nia'}):
            with self.assertRaises(ValueError):attach([self.docs['repair']],[dict(event='refit_and_test',bindings=bindings)])
        with self.assertRaises(ValueError):attach([self.docs['repair']],[dict(event='unknown')])

    def test_precise_cue_prefers_complete_context_over_generic_repair_verb(self):
        candidates=proposals(list(self.docs.values()),dict(query='repair the wheel'))
        self.assertTrue(candidates)
        self.assertEqual({c['scenario'] for c in candidates},{'repair'})

    def test_empty_receiver_can_import_people_as_well_as_objects(self):
        from .catalog_attachment import bare_world
        world=bare_world();before=world.to_dict()
        row=run([self.docs['repair']],[dict(event='refit_and_test')],world)
        self.assertTrue(replay(row));self.assertTrue(validate(annotate(row)))
        self.assertEqual(world.to_dict(),before)
        self.assertIn('Ada',row['story'])
        self.assertNotIn('',row['final_world']['entities'])


if __name__=='__main__':unittest.main()
