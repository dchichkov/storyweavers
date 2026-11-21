"""Correspondence rules propose grounded distributions, never source mutations."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from .event_mapping import load_bank, validate_bank, project_candidates, mapping_distribution, generate_mapped
from .event_line_replay import paper_world, project_source, replay


class EventMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads((Path(__file__).parent/'runs/entity_event_lines_20261106/refined/kite.json').read_text())
        cls.ids = [e['id'] for e in cls.graph['events'] if e['kind'] in {'fetch_tape', 'mend'}]

    def competing_world(self):
        world = paper_world()
        world.entities['ada'].properties.add('can_repair')
        world.entities['book'].properties.add('physics:kite')
        return world

    def test_legacy_import_now_comes_from_bank(self):
        template = project_source(self.graph, 'hero', self.ids)
        self.assertEqual(template['source']['mapping_rules'], ['fetch.portable_tool', 'repair.paper'])
        self.assertEqual(template['source']['event_origins']['patch']['mapping_rule'], 'repair.paper')
        self.assertEqual(template['events']['fetch']['item'], 'tool')
        row = replay(paper_world(), template, dict(worker='ada', item='book', tool='tape', supply='bench'), heads=False)
        self.assertEqual(row['status'], 'complete')
        self.assertEqual(row['trace'][0]['attribute_transfer']['fetch']['semantic_mapping'], 'declarative_mapping_grammar')

    def test_infers_bindings_without_names_or_explicit_hints(self):
        world = paper_world(); before = world.to_dict()
        result = mapping_distribution(self.graph, 'hero', self.ids, world)
        self.assertEqual(len(result['candidates']), 1)
        chosen = result['candidates'][0]
        self.assertEqual(chosen['bindings'], dict(worker='ada', item='book', tool='tape', supply='bench'))
        self.assertEqual(chosen['probability'], 1)
        self.assertTrue(any(r.get('bindings', {}).get('worker') == 'omar' for r in result['rejected']))
        self.assertEqual(world.to_dict(), before)

    def test_two_rules_compete_on_same_complete_binding(self):
        world = self.competing_world()
        candidates = mapping_distribution(self.graph, 'hero', self.ids, world)['candidates']
        self.assertEqual(len(candidates), 2)
        probabilities = {c['rules'][-1]: c['probability'] for c in candidates}
        self.assertEqual(probabilities, {'repair.paper': 2/3, 'repair.kite': 1/3})
        self.assertEqual(candidates[0]['bindings'], candidates[1]['bindings'])

    def test_context_factors_change_distribution_not_physics(self):
        world = self.competing_world(); before = world.to_dict()
        candidates = mapping_distribution(self.graph, 'hero', self.ids, world,
                                           rule_factors={'repair.kite': 4})['candidates']
        self.assertEqual({c['rules'][-1]: c['probability'] for c in candidates},
                         {'repair.paper': 1/3, 'repair.kite': 2/3})
        self.assertEqual(world.to_dict(), before)
        candidates = mapping_distribution(self.graph, 'hero', self.ids, paper_world(),
                                           rule_factors={'repair.kite': 1000})['candidates']
        self.assertEqual([c['rules'][-1] for c in candidates], ['repair.paper'])

    def test_distinct_entity_bindings_remain_separate_candidates(self):
        world = paper_world()
        world.entities['poster'] = deepcopy(world.entities['book'])
        world.entities['poster'].id = 'poster'; world.entities['poster'].noun = 'poster'
        result = mapping_distribution(self.graph, 'hero', self.ids, world)
        self.assertEqual({c['bindings']['item']: c['probability'] for c in result['candidates']},
                         {'book': .5, 'poster': .5})
        bound = mapping_distribution(self.graph, 'hero', self.ids, world, bindings={'item': 'poster'})
        self.assertEqual(len(bound['candidates']), 1)
        self.assertEqual(bound['candidates'][0]['bindings']['item'], 'poster')

    def test_new_source_kind_is_added_by_data_only(self):
        graph = deepcopy(self.graph); graph['scenario'] = 'unrelated_paper_story'
        for event in graph['events']:
            if event['kind'] == 'mend': event['kind'] = 'restore_page'
        bank = load_bank()
        for rule in bank['rules']:
            if rule['id'] == 'repair.paper':
                rule['id'] = 'repair.page'; rule['source']['kinds'] = ['restore_page']
        row, attached = generate_mapped(graph, 'hero', self.ids, paper_world(), bank=bank, seed=7)
        self.assertEqual(row['status'], 'complete')
        self.assertIn('repair.page', attached['rules'])
        self.assertIn('repair the book', row['story'])

    def test_extra_source_effects_fail_closed(self):
        for field, value in [('state', {'before':['torn'], 'after':['repaired', 'flying']}),
                             ('location', {'before':'hero', 'after':'sky'})]:
            graph = deepcopy(self.graph)
            event = next(e for e in graph['events'] if e['kind'] == 'mend')
            event['effects']['target'][field] = value
            with self.assertRaisesRegex(ValueError, 'not the reviewed'):
                mapping_distribution(graph, 'hero', self.ids, paper_world())

    def test_inconsistent_source_role_across_events_is_not_silently_rebound(self):
        graph = deepcopy(self.graph)
        event = next(e for e in graph['events'] if e['kind'] == 'fetch_tape')
        event['movements'][0]['item'] = 'other_tool'
        event['effects']['other_tool'] = event['effects'].pop('tool')
        with self.assertRaisesRegex(ValueError, 'inconsistent source role'):
            project_candidates(graph, 'hero', self.ids)

    def test_blocked_programs_are_reported_without_partial_import(self):
        world = paper_world(); world.entities['tape'].location = 'omar'
        before = world.to_dict()
        result = mapping_distribution(self.graph, 'hero', self.ids, world)
        self.assertFalse(result['candidates'])
        self.assertTrue(any('blocking' in r for r in result['rejected']))
        self.assertEqual(world.to_dict(), before)
        with self.assertRaisesRegex(ValueError, 'no feasible event mapping'):
            generate_mapped(self.graph, 'hero', self.ids, world)

    def test_validation_and_limits(self):
        for weight in [0, -1, True, float('nan')]:
            bank = load_bank(); bank['rules'][0]['weight'] = weight
            with self.assertRaises(ValueError): validate_bank(bank)
        bank = load_bank(); bank['rules'][0]['target']['event']['op'] = 'arbitrary_code'
        with self.assertRaisesRegex(ValueError, 'unsupported target'): validate_bank(bank)
        bank = load_bank(); bank['rules'][0]['source']['equals']['frame.actor'] = '$missing'
        with self.assertRaisesRegex(ValueError, 'unbound rule'): validate_bank(bank)
        for factors in [{'absent': 1}, {'repair.paper': 0}, {'repair.paper': float('inf')}]:
            with self.assertRaises(ValueError):
                mapping_distribution(self.graph, 'hero', self.ids, paper_world(), rule_factors=factors)
        with self.assertRaisesRegex(ValueError, 'limit exceeded'):
            mapping_distribution(self.graph, 'hero', self.ids, self.competing_world(), limit=1)
        with self.assertRaisesRegex(ValueError, 'unknown target binding'):
            mapping_distribution(self.graph, 'hero', self.ids, paper_world(), bindings={'typo': 'ada'})

    def test_generation_replays_both_rule_paths_with_target_annotations(self):
        world = self.competing_world(); before = world.to_dict(); seen = set()
        for seed in range(6):
            row, attached = generate_mapped(self.graph, 'hero', self.ids, world, seed=seed)
            self.assertEqual(row['status'], 'complete'); seen.add(attached['rules'][-1])
            self.assertEqual(len(row['source']['mapping_distribution']['candidates']), 2)
            self.assertIn('repaired', row['final_world']['entities']['book']['state'])
            self.assertNotIn('flyable', row['final_world']['entities']['book']['properties'])
            for scene in row['trace']:
                for prediction in scene['word_trace']:
                    self.assertAlmostEqual(sum(c['probability'] for c in prediction['annotated_choices']), 1)
                for attrs in scene['attribute_table'].values():
                    self.assertEqual(attrs['event']['roles']['actor'], 'ada')
        self.assertEqual(seen, {'repair.paper', 'repair.kite'})
        self.assertEqual(world.to_dict(), before)


if __name__ == '__main__':
    unittest.main()
