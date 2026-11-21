"""Proposals name a grounded operation and retain their narrative evidence."""
import unittest

from .storytelling.runtime import generate,replay
from .story_memory import annotate


class BeatChoiceTests(unittest.TestCase):
    def test_camp_transfer_proposal_is_concrete_and_hypothetical(self):
        seen=0
        for seed in (7,19,43):
            row=generate('camp',seed,beat_budget=6,continuations='expanded')
            replay(row);annotate(row)
            for event in row['final_world']['history']:
                for c in event.get('beat_decision',{}).get('candidates',[]):
                    if c['id']=='committing' and event['frame']['kind']=='share_light':
                        seen+=1
                        self.assertEqual(c['proposal'],dict(lemma='give',object='lantern',recipient='helper'))
                        self.assertIn('I will give you the lantern',c['text'])
                        self.assertLess(c['discovery_event'],event['id'])
            attrs=[a for trace in row['trace'] for a in trace['attribute_table'].values()
                   if a.get('action_scope')=='proposed_action' and a['action']['lemma']=='give']
            self.assertTrue(attrs)
            self.assertTrue(all(a['hypothetical'] for a in attrs))
            recipients=[a for a in attrs if a.get('syntax_role')=='recipient']
            self.assertTrue(recipients)
            self.assertTrue(all(a['entity']=='helper' for a in recipients))
        self.assertGreater(seen,0)

    def test_no_generic_proposals_and_no_reaction_to_unrevealed_weighing(self):
        for scenario in ('camp','seaside','trail','repair','market'):
            row=generate(scenario,43,beat_budget=6,continuations='expanded');replay(row)
            self.assertNotIn('another way',row['story'])
            for event in row['final_world']['history']:
                if scenario=='market' and event['frame']['kind']=='discover_leaf':
                    self.assertIsNone(event.get('beat_decision'))
                for candidate in event.get('beat_decision',{}).get('candidates',[]):
                    self.assertNotIn('another way',candidate['text'])

    def test_discovery_link_crosses_intervening_helper_action(self):
        row=generate('repair',43,beat_budget=6,continuations='expanded');replay(row);annotate(row)
        by_id={e['id']:e for e in row['final_world']['history']}
        event=next(e for e in by_id.values() if e['frame']['kind']=='refit_and_test')
        proposals=[c for c in event['beat_decision']['candidates'] if c['speech_act']]
        self.assertTrue(proposals)
        for c in proposals:
            self.assertEqual(by_id[c['discovery_event']]['frame']['kind'],'diagnose_string')
            self.assertGreater(c['preceding_event'],c['discovery_event'])
            self.assertEqual(c['related_events'][0]['basis'],'authored_link')


if __name__=='__main__':unittest.main()
