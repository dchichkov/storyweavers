"""Narrative contracts, physical counterfactuals and annotated distributions."""
from copy import deepcopy
import unittest

from .storytelling.runtime import generate, replay, setup, build_forest
from .storytelling.qa import questions
from .storytelling.revisions import pack
from .storytelling.revisions.engine import CraftedPack
from .story_memory import annotate
from .world import Frame

BRANCHES = {'pottery': ('keep_dent', 'remake', 'make_bowl'),
            'music': ('choose_private', 'choose_solo', 'choose_written'),
            'greenhouse': ('choose_share', 'choose_flower', 'choose_seedlings')}


def frame(event):
    return Frame(**{**event['frame'], 'cause_ids': tuple(event['frame']['cause_ids'])})


class StorycraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {(name, branch): generate(name, 19, edition='crafted', choice=branch)
                    for name, branches in BRANCHES.items() for branch in branches}

    def test_all_nine_paths_have_grounded_endings_and_full_answers(self):
        for (name, branch), row in self.rows.items():
            with self.subTest(name=name, branch=branch):
                self.assertTrue(replay(row))
                annotate(row)
                memory = row['final_world']['narrative']['storycraft']
                self.assertTrue(memory['completed'])
                self.assertTrue(all(o['status'] == 'resolved' for o in memory['obligations'].values()))
                self.assertEqual(memory['history'][-1]['event'], row['scenes'][-1]['event_id'])
                self.assertIn(memory['history'][-1]['function'], {'final_image', 'payoff'})
                self.assertEqual(row['title'], memory['title'])
                self.assertEqual(row['presentation']['opening']['text'], '')
                qa = questions(row, 100)
                self.assertGreaterEqual(len(qa), 4)
                self.assertEqual(len({q['question'] for q in qa}), len(qa))
                for q in qa:
                    self.assertGreaterEqual(q['answer'].count('.'), 2)
                    self.assertTrue(q['event_ids'])
                    for e in q['evidence']:
                        self.assertEqual(row['story'][e['start']:e['end']], e['text'])
                        start = row['presentation']['body_offset'] + e['start']
                        self.assertEqual(row['presented_story'][start:start+len(e['text'])], e['text'])

    def test_pottery_cannot_deliver_hot_clay_and_keeps_its_cost(self):
        for branch in BRANCHES['pottery']:
            row = self.rows['pottery', branch]
            p, w = setup('pottery', 19, edition='crafted', choice=branch)
            checked = False
            for saved in row['final_world']['history']:
                f = frame(saved)
                if f.kind in {'crafted_give', 'crafted_give_late', 'crafted_give_bowl'}:
                    altered = w.clone()
                    altered.entities['cup'].state.difference_update({'safe', 'cool'})
                    altered.entities['cup'].state.add('hot')
                    before = altered.to_dict()
                    with self.assertRaises(ValueError): p.commit(altered, f, '')
                    self.assertEqual(before, altered.to_dict()); checked = True
                p.commit(w, f, saved['sentence'])
            self.assertTrue(checked)
            self.assertIn('surprise_lost', w.entities['hero'].state)
            if branch == 'remake': self.assertIn('birthday_missed', w.entities['hero'].state)
            if branch == 'make_bowl': self.assertEqual(w.entities['cup'].noun, 'bowl')
            if branch == 'keep_dent': self.assertIn('dented', w.entities['cup'].state)

    def test_music_refusal_persists_and_promises_need_fulfillment(self):
        for branch in BRANCHES['music']:
            row = self.rows['music', branch]
            p, w = setup('music', 19, edition='crafted', choice=branch)
            for saved in row['final_world']['history']:
                f = frame(saved)
                removals = {'crafted_play_private': [('door','closed'), ('partner','private_agreed'), ('program','slot_reallocated')],
                            'crafted_play_written': [('hero','credit_spoken'), ('partner','pattern_use_permitted')]}
                for carrier, state in removals.get(f.kind, []):
                    altered = w.clone(); altered.entities[carrier].state.discard(state)
                    before = altered.to_dict()
                    with self.assertRaises(ValueError): p.commit(altered, f, '')
                    self.assertEqual(before, altered.to_dict())
                p.commit(w, f, saved['sentence'])
            self.assertIn('public_refused', w.entities['partner'].state)
            if branch == 'choose_private': self.assertIn('public_turn_lost', w.entities['hero'].state)
            if branch == 'choose_written': self.assertIn('credited', w.entities['partner'].state)

    def test_greenhouse_conserves_water_in_every_snapshot(self):
        for branch in BRANCHES['greenhouse']:
            row = self.rows['greenhouse', branch]
            for event in row['final_world']['history']:
                for snapshot in (event['before'], event['after']):
                    total = 0
                    for entity in ('barrel', 'can', 'tomatoes', 'sunflower'):
                        states = snapshot['entities'][entity]['state']
                        units = [s for s in states if s.startswith('water_units_')]
                        self.assertEqual(len(units), 1)
                        total += int(units[0].removeprefix('water_units_'))
                    self.assertEqual(total, 2)
                    self.assertIn('broken', snapshot['entities']['tap']['state'])
            final = row['final_world']['entities']
            if branch == 'choose_flower':
                self.assertIn('brown', final['leaf']['state'])
                self.assertIn('water_units_0', final['tomatoes']['state'])
            if branch == 'choose_seedlings': self.assertIn('water_units_0', final['sunflower']['state'])

    def test_invalid_authoring_and_narrative_obligations_fail_before_mutation(self):
        spec = deepcopy(pack('pottery').spec)
        spec['events'][0]['effects'] = {'cup': {'location': 'missing'}}
        with self.assertRaises(ValueError): CraftedPack(spec)
        spec = deepcopy(pack('pottery').spec)
        spec['events'][0]['after'] = ['missing']
        with self.assertRaises(ValueError): CraftedPack(spec)
        for options in ({'choice':'plan'}, {'care':float('nan')}, {'pride':2}):
            with self.assertRaises(ValueError): setup('pottery', edition='crafted', **options)
        p, w = setup('pottery', edition='crafted')
        f = p.candidates(w)[0][1]
        w.narrative['storycraft']['obligations']['birthday_gift'] = {'status':'open'}
        before = w.to_dict()
        with self.assertRaises(ValueError): p.commit(w, f, '')
        self.assertEqual(before, w.to_dict())
        row = self.rows['pottery', 'keep_dent']
        p, w = setup('pottery', 19, edition='crafted', choice='keep_dent')
        for saved in row['final_world']['history'][:-1]: p.commit(w, frame(saved), saved['sentence'])
        w.narrative['storycraft']['obligations']['unpaid'] = {'status':'open'}
        before = w.to_dict()
        with self.assertRaises(ValueError): p.commit(w, frame(row['final_world']['history'][-1]), '')
        self.assertEqual(before, w.to_dict())

    def test_speech_cannot_happen_across_unconnected_locations(self):
        row = self.rows['music', 'choose_private']
        p, w = setup('music', 19, edition='crafted', choice='choose_private')
        for saved in row['final_world']['history']:
            if saved['frame']['kind'] == 'crafted_refuse_public': break
            p.commit(w, frame(saved), saved['sentence'])
        w.entities['partner'].location = 'hall'; before = w.to_dict()
        with self.assertRaises(ValueError): p.commit(w, frame(saved), '')
        self.assertEqual(before, w.to_dict())

    def test_attributes_are_distributions_over_proposals_and_prefix_state(self):
        seen_acts = set(); seen_determiner = False
        for row in self.rows.values():
            for scene in row['trace']:
                table = scene['attribute_table']
                for step in scene['word_trace']:
                    self.assertAlmostEqual(sum(c['probability'] for c in step['choices']), 1)
                    self.assertAlmostEqual(sum(c['probability'] for c in step['annotated_choices']), 1)
                    for c in step['annotated_choices']:
                        a = table[c['attributes']]
                        self.assertEqual(a['event']['status'], 'proposed')
                        self.assertTrue(all(i < scene['event_id'] for i in a['storycraft']['earlier_events']))
                        if a.get('entity') and c['word'].lower() == 'the':
                            self.assertEqual(a['pos'], 'DET'); seen_determiner = True
                        if 'speech_act' in a:
                            seen_acts.add(a['speech_act']['name'])
                            self.assertEqual(a['speech_act']['scope'], 'candidate_utterance')
        self.assertTrue({'promise', 'request', 'condition', 'admit'} <= seen_acts)
        self.assertTrue(seen_determiner)

    def test_attention_changes_branch_mass_without_changing_support(self):
        row = self.rows['pottery', 'keep_dent']
        p, w = setup('pottery', 19, edition='crafted')
        for saved in row['final_world']['history']:
            if saved['frame']['kind'] == 'crafted_keep_dent': break
            p.commit(w, frame(saved), saved['sentence'])
        masses = []
        for care in (0, 1):
            w.entities['hero'].memes['Care'] = care; before = w.to_dict()
            forest, _ = build_forest(p, w, predict_attributes=True)
            mass = {}
            for d in forest.derivations: mass[d.frame.kind] = mass.get(d.frame.kind, 0) + d.probability
            self.assertEqual(set(mass), {'crafted_'+b for b in BRANCHES['pottery']})
            self.assertAlmostEqual(sum(mass.values()), 1)
            self.assertEqual(before, w.to_dict()); masses.append(mass)
        self.assertGreater(masses[1]['crafted_keep_dent'], masses[0]['crafted_keep_dent'])


if __name__ == '__main__': unittest.main()
