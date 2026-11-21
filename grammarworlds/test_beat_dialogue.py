"""Optional dialogue must not reveal a future clue or repeat native speech."""
import unittest

from .storytelling.runtime import generate, replay
from .story_memory import annotate


class BeatDialogueTests(unittest.TestCase):
    def decisions(self, scenario, seed=41):
        row=generate(scenario,seed,beat_budget=6,continuations='expanded')
        replay(row);annotate(row)
        return row,[(e,d) for e in row['final_world']['history']
                    if (d:=e.get('beat_decision'))]

    def test_no_request_repeats_an_admission_or_choice_in_same_scene(self):
        for scenario,kind in [('repair','admit_and_shelter'),('orchard','protect_branch'),
                              ('biscuit','agree_share')]:
            row,decisions=self.decisions(scenario)
            for event,decision in decisions:
                if event['frame']['kind']==kind:
                    self.assertNotIn('asking',{c['id'] for c in decision['candidates']})
            self.assertNotIn('?” '+row['final_world']['entities']['hero']['noun']+' said',row['story'])

    def test_prior_request_does_not_get_a_second_generic_request(self):
        row,decisions=self.decisions('snow')
        event,decision=next((e,d) for e,d in decisions if e['frame']['kind']=='leave_race')
        self.assertNotIn('asking',{c['id'] for c in decision['candidates']})

    def test_future_clue_is_not_used_as_the_current_problem(self):
        seen=0
        for seed in (7,19,41,43):
            row,decisions=self.decisions('camp',seed)
            for event,decision in decisions:
                if event['frame']['kind'] in {'bell_clue','collar_clue'}:
                    seen+=1
                    for candidate in decision['candidates']:
                        self.assertEqual(candidate['object'],'rabbit')
                        self.assertNotIn(candidate['id'],{'asking','inspection'})
        self.assertGreater(seen,0)

    def test_environmental_obstacle_is_not_a_generic_help_target(self):
        seen=0
        for seed in (7,19,41,43):
            _,decisions=self.decisions('seaside',seed)
            for event,decision in decisions:
                if event['frame']['kind'] in {'milo_reads_map','tessa_checks_map'}:
                    seen+=1
                    self.assertNotIn('asking',{c['id'] for c in decision['candidates']})
        self.assertGreater(seen,0)

    def test_nonredundant_pottery_request_remains_available(self):
        _,decisions=self.decisions('pottery')
        candidate_sets=[{c['id'] for c in d['candidates']} for e,d in decisions
                        if e['frame']['kind']=='inspect']
        self.assertTrue(any('asking' in ids for ids in candidate_sets))

    def test_hidden_frame_patient_is_not_a_narrated_problem(self):
        row,decisions=self.decisions('library',907)
        self.assertNotIn('looked closely at the mitten',row['story'])
        by_id={e['id']:e for e in row['final_world']['history']}
        checked=0
        for event,decision in decisions:
            previous=by_id[decision['candidates'][0]['preceding_event']]
            if previous['frame']['kind']=='failed_search':
                checked+=1
                self.assertNotIn('mitten',previous['referents'])
                self.assertTrue(all(c['object']!='mitten' for c in decision['candidates']))
        self.assertGreater(checked,0)


if __name__=='__main__':unittest.main()
