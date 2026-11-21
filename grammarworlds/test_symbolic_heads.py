"""Contracts, independent probability calculations, and actual Forest integration."""

from copy import deepcopy
import math
from pathlib import Path
import random
import unittest

from .engine import build_forest
from .grammar import Derivation, Forest, choice, expand
from .world import Frame, make_world
from .symbolic_heads import HeadContext, HeadLibrary, ProgramRequired, Source, TableFormatError, load_library, predict, sample
from .symbolic_heads.__main__ import demo
from .symbolic_heads.runtime import Lookup


class SymbolicHeadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library = load_library()

    def test_inventory_covers_proposals_with_ten_diverse_examples_each(self):
        self.assertEqual(self.library.ids, tuple(f'P{i:03d}' for i in range(1,65)))
        inventory = Path(__file__).with_name('proposed_symbolic_attention_inventory.md').read_text()
        counts = {}
        for id in self.library.ids:
            s = self.library.describe(id)
            self.assertIn(f'| {id} · Proposed | {s["name"]} |', inventory)
            self.assertTrue(s['description'])
            self.assertEqual(len(s['examples']), 10)
            self.assertEqual(len({e['description'] for e in s['examples']}),10)
            counts[s['status']] = counts.get(s['status'],0)+1
        self.assertEqual(counts, {'table':15,'program_required':49})

    def test_all_150_seed_examples_transmit_features_and_adjust_distributions(self):
        for id in self.library.ids:
            s = self.library.describe(id)
            if s['status'] != 'table':
                continue
            for e in s['examples']:
                with self.subTest(example=e['id']):
                    result = self.library.rerank(e['grammar_weights'],
                        [HeadContext(id,e['query'],e['scope'])], [Source(**v) for v in e['sources']])
                    self.assertEqual(result['heads'][0]['features'], e['expected_features'])
                    p = result['probabilities']
                    self.assertAlmostEqual(sum(p.values()),1)
                    self.assertEqual(set(p),set(e['grammar_weights']))
                    self.assertTrue(all(v>0 for v in p.values()))
                    self.assertGreater(p[e['favored']], result['base'][e['favored']])
                    self.assertLess(p[e['disfavored']], result['base'][e['disfavored']])
                    node = choice('example.word_slot', *e['grammar_weights'],
                                  weights=tuple(e['grammar_weights'].values()))
                    forest = Forest([Derivation(words,weight,Frame('example','actor'),rules)
                                     for words,weight,rules in expand(node)],{})
                    received = predict(forest,(),self.library,
                        [HeadContext(id,e['query'],e['scope'])], [Source(**v) for v in e['sources']])
                    for candidate in received['choices']:
                        self.assertAlmostEqual(candidate['probability'],p[candidate['word']])
                        self.assertIn('example.word_slot',candidate['grammar_rules'])

    def test_all_49_program_contracts_raise_specific_exceptions(self):
        for id in self.library.ids:
            s = self.library.describe(id)
            if s['status'] != 'program_required':
                continue
            with self.subTest(head=id):
                for base in ({'word':1}, {}):
                    with self.assertRaises(ProgramRequired) as caught:
                        self.library.rerank(base,[HeadContext(id,'query','scope')],[])
                    self.assertIsInstance(caught.exception, NotImplementedError)
                    self.assertEqual(caught.exception.head_id,id)
                    self.assertEqual(caught.exception.algorithm,s['required_program'])
                self.assertTrue(all(e['status']=='design_fixture_not_executed' for e in s['examples']))

    def test_river_water_counts_against_hand_calculation(self):
        result = self.library.rerank({'flows':.4,'sings':.1,'freezes':.3,'sparkles':.2},
            [HeadContext('P059','river','clause')], [Source('r','active_context_feature','clause','water')])
        expected = {'flows':12.4/14,'sings':1.1/14,'freezes':.3/14,'sparkles':.2/14}
        for w,p in expected.items():
            self.assertAlmostEqual(result['probabilities'][w],p)

    def test_same_feature_different_query_changes_continuation(self):
        memory = [Source('m','active_context_feature','s','moisture')]
        seed = self.library.rerank({'sprouts':1,'rusts':1},[HeadContext('P059','seed','s')],memory)
        iron = self.library.rerank({'sprouts':1,'rusts':1},[HeadContext('P059','iron','s')],memory)
        self.assertGreater(seed['probabilities']['sprouts'],seed['probabilities']['rusts'])
        self.assertGreater(iron['probabilities']['rusts'],iron['probabilities']['sprouts'])

    def test_multipliers_against_hand_calculation(self):
        result = self.library.rerank({'are':3,'is':1},[HeadContext('P001','present_be','s')],
            [Source('subject','grammatical_subject','s','boats')])
        self.assertAlmostEqual(result['probabilities']['are'],12/12.25)
        self.assertAlmostEqual(result['probabilities']['is'],.25/12.25)

    def test_receiver_does_not_restore_grammar_exclusions(self):
        result = self.library.rerank({'are':0,'is':1},[HeadContext('P001','present_be','s')],
            [Source('subject','grammatical_subject','s','boats')])
        self.assertEqual(result['probabilities'],{'is':1})
        self.assertIn('are',result['heads'][0]['outside_grammar'])

    def test_count_mass_outside_grammar_is_excluded(self):
        result = self.library.rerank({'sings':1,'waits':1},[HeadContext('P059','river','s')],
            [Source('r','active_context_feature','s','water')])
        self.assertEqual(set(result['probabilities']),{'sings','waits'})
        self.assertAlmostEqual(result['probabilities']['sings'],.75)
        self.assertIn('flows',result['heads'][0]['outside_grammar'])

    def test_attention_normalizes_and_preserves_conflicting_features(self):
        result = self.library.activate(HeadContext('P001','present_be','s'),[
            Source('a','grammatical_subject','s','boats'),Source('b','grammatical_subject','s','boat')])
        self.assertEqual(result['features'],{'plural':.5,'singular':.5})
        self.assertAlmostEqual(sum(r['attention'] for r in result['sources']),1)

    def test_multiple_heads_add_log_factors_and_zero_strength_is_neutral(self):
        memory=[Source('number','grammatical_subject','s','boats'),
                Source('person','subject_person','s','they')]
        contexts=[HeadContext('P001','present_be','s'),HeadContext('P002','present_be','s')]
        result=self.library.rerank({'are':1,'is':1},contexts,memory)
        self.assertAlmostEqual(result['probabilities']['are'],16/(16+.0625))
        neutral=self.library.rerank({'are':3,'is':1},[HeadContext('P001','present_be','s',0)],memory)
        self.assertAlmostEqual(neutral['probabilities']['are'],.75)

    def test_query_conditioned_value_mapping_does_not_mix_argument_roles(self):
        source=[Source('state','predicate_argument_state','s','patient_filled')]
        put=self.library.activate(HeadContext('P006','put','s'),source)
        lend=self.library.activate(HeadContext('P006','lend','s'),source)
        self.assertEqual(put['features'],{'location_remaining':1})
        self.assertEqual(lend['features'],{'recipient_remaining':1})

    def test_weighted_selection_and_projection_are_separate(self):
        spec = self.library.describe('P001')
        spec['selection'] = [{'tokens':['q','a'],'weight':3},{'tokens':['q','b'],'weight':1}]
        spec['projection'] = [{'tokens':['a','plural'],'weight':1},{'tokens':['a','singular'],'weight':1},
                              {'tokens':['b','singular'],'weight':1}]
        lib = HeadLibrary([spec])
        result = lib.activate(HeadContext('P001','q','s'),[
            Source('a','grammatical_subject','s','a'),Source('b','grammatical_subject','s','b')])
        self.assertAlmostEqual(result['features']['plural'],.375)
        self.assertAlmostEqual(result['features']['singular'],.625)
        self.assertAlmostEqual(result['sources'][0]['attention'],.75)

    def test_trigram_override_retains_other_bigram_defaults(self):
        t = Lookup([{'tokens':['x','a'],'weight':2}, {'tokens':['x','b'],'weight':3},
                    {'tokens':['q','x','a'],'weight':4}])
        self.assertEqual(t.outputs('q','x'),{'a':4,'b':3})
        self.assertEqual(t.outputs('other','x'),{'a':2,'b':3})

    def test_scope_channel_and_query_distractors_cannot_leak(self):
        request = [HeadContext('P001','present_be','s')]
        for source in [Source('a','grammatical_subject','other','boats'),
                       Source('a','object_number','s','boats'),
                       Source('a','grammatical_subject','s','unlisted')]:
            result = self.library.rerank({'are':2,'is':1},request,[source])
            self.assertEqual(result['heads'][0]['status'],'abstained')
            self.assertAlmostEqual(result['probabilities']['are'],2/3)
        result = self.library.activate(HeadContext('P001','unlisted_query','s'),[
            Source('a','grammatical_subject','s','boats')])
        self.assertEqual(result['features'],{})

    def test_low_confidence_weakens_effect_even_for_one_source(self):
        context=[HeadContext('P001','present_be','s')]
        high=self.library.rerank({'are':1,'is':1},context,[Source('a','grammatical_subject','s','boats')])
        low=self.library.rerank({'are':1,'is':1},context,[Source('a','grammatical_subject','s','boats',.1)])
        zero=self.library.rerank({'are':1,'is':1},context,[Source('a','grammatical_subject','s','boats',0)])
        self.assertGreater(high['probabilities']['are'],low['probabilities']['are'])
        self.assertGreater(low['probabilities']['are'],.5)
        self.assertEqual(zero['probabilities'],{'are':.5,'is':.5})

    def test_missing_projection_abstains_and_missing_receiver_is_neutral(self):
        spec=self.library.describe('P001')
        spec['projection']=[]
        args=({'are':1,'is':1},[HeadContext('P001','present_be','s')],[Source('a','grammatical_subject','s','boats')])
        self.assertEqual(HeadLibrary([spec]).rerank(*args)['heads'][0]['status'],'abstained')
        spec=self.library.describe('P001'); spec['receiver']=[]
        self.assertEqual(HeadLibrary([spec]).rerank(*args)['probabilities'],{'are':.5,'is':.5})

    def test_missing_count_rows_back_off_to_grammar(self):
        spec=self.library.describe('P059'); spec['receiver']=[]
        result=HeadLibrary([spec]).rerank({'a':3,'b':1},[HeadContext('P059','river','s')],
            [Source('r','active_context_feature','s','water')])
        self.assertAlmostEqual(result['probabilities']['a'],.75)

    def test_duplicate_sources_and_requests_are_rejected(self):
        source=Source('a','grammatical_subject','s','boats')
        ctx=HeadContext('P001','present_be','s')
        with self.assertRaises(ValueError): self.library.activate(ctx,[source,source])
        with self.assertRaises(ValueError): self.library.rerank({'are':1},[ctx,ctx],[source])

    def test_invalid_tables_fail_at_load(self):
        for rows in [ [{'tokens':['x'],'weight':1}], [{'tokens':'xy','weight':1}],
                      [{'tokens':['x','y'],'weight':0}], [{'tokens':['x','y'],'weight':-1}],
                      [{'tokens':['x','y'],'weight':float('nan')}],
                      [{'tokens':['x','y'],'weight':1}]*2 ]:
            with self.subTest(rows=rows),self.assertRaises(TableFormatError): Lookup(rows)

    def test_invalid_probabilities_and_gates_rejected(self):
        for p in [-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError): self.library.rerank({'a':p},[],[])
        for confidence in [-1,1.1,float('nan')]:
            with self.assertRaises(ValueError): Source('id','c','s','k',confidence)
        with self.assertRaises(ValueError): HeadContext('P001','q','s',float('inf'))

    def test_extreme_finite_weights_remain_normalized(self):
        result=self.library.rerank({'a':1e308,'b':1e-308},[],[])['probabilities']
        self.assertTrue(all(math.isfinite(p) and p>0 for p in result.values()))
        self.assertAlmostEqual(sum(result.values()),1)

    def test_actual_world_forest_preserves_grammar_and_state(self):
        world=make_world('rescue',seed=7)
        before=deepcopy(world)
        forest=build_forest(world)
        original=forest.predict(())
        # Explicit symbol context may influence only words the actual Forest permits.
        result=predict(forest,(),self.library,[HeadContext('P001','present_be','s')],
            [Source('a','grammatical_subject','s','boats')])
        self.assertEqual(world,before)
        self.assertEqual(original,forest.predict(()))
        self.assertEqual({c['word'] for c in result['choices']},{c['word'] for c in original['choices']})
        self.assertIn('grammar_prefix_probability',result)
        self.assertNotIn('prefix_probability',result)

    def test_full_eight_word_sampling_with_grammar_metadata(self):
        result=demo(7)
        self.assertEqual(result['words'],8)
        self.assertTrue(result['semantic_support'])
        step=result['trace'][2]
        self.assertEqual(len(step['choices']),4)
        self.assertTrue(all(c['grammar_rules'] and c['events'] for c in step['choices']))
        self.assertEqual(result['trace'][-1]['selected'],'<END>')
        self.assertAlmostEqual(result['sequence_probability'],12.4/14)
        self.assertEqual(result,demo(7))

    def test_sampling_respects_distribution_not_only_argmax(self):
        rng=random.Random(4)
        prediction={'choices':[{'word':'a','probability':.8},{'word':'b','probability':.2}]}
        draws=[sample(prediction,rng) for _ in range(2000)]
        self.assertTrue(.75<draws.count('a')/len(draws)<.85)
        with self.assertRaises(ValueError): sample({'choices':[]},rng)

    def test_inspection_cannot_mutate_loaded_tables(self):
        spec=self.library.describe('P001'); spec['selection'].clear()
        self.assertTrue(self.library.describe('P001')['selection'])

    def test_unsupported_prefix_remains_unsupported(self):
        forest=Forest([Derivation(('hello',),1,Frame('test','hero'),())],{})
        result=predict(forest,('ungrammatical',),self.library,[],[])
        self.assertEqual(result['choices'],[])
        self.assertIn('error',result)


if __name__ == '__main__':
    unittest.main()
