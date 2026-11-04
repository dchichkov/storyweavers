import unittest
from dataclasses import asdict
from .world import Parameters, generate, initial, play_scene, replay, guard
from storyscenes.runtime import StoryError

class KiteTests(unittest.TestCase):
    def test_seeded_lengths_and_replay(self):
        for seed in range(100):
            for count in (7,8):
                row=generate(seed,count=count); self.assertEqual(len(row['episodes']),count)
                self.assertEqual(row['story'],'\n\n'.join(e['text'] for e in row['episodes']))
                self.assertEqual([dict(id=e['id'],before=e['before'],after=e['after'],events=list(e['events']),text=e['text']) for e in replay(Parameters(**row['parameters']),row['path'])],row['episodes'])
                self.assertTrue(row['final_state']['story.ended'])
    def test_bad_params_and_failed_action_atomic(self):
        for kw in ({'wind':True},{'wind':4},{'shy':1},{'name':'<x>'}):
            with self.assertRaises(ValueError): Parameters(**kw)
        p=Parameters(); s=initial(p); old=dict(s)
        with self.assertRaises(StoryError): play_scene(p,s,'closing')
        self.assertEqual(s,old)
    def test_optional_vignettes(self):
        a=generate(5,count=7); b=generate(5,count=8)
        self.assertFalse(any(x in a['path'] for x in ('ribbon_vignette','wind_vignette')))
        self.assertTrue(any(x in b['path'] for x in ('ribbon_vignette','wind_vignette')))
    def test_counterfactual_wind_and_reel(self):
        a=generate(2,params=Parameters(wind=2,reel_sound=True,spare_line=True)); b=generate(2,params=Parameters(wind=2,reel_sound=False,spare_line=True))
        self.assertNotEqual(a['final_state']['story.outcome'],b['final_state']['story.outcome'])
    def test_action_continuity(self):
        row=generate(1)
        for ep in row['episodes']:
            state=ep['before']
            for e in ep['events']:
                for k,v in e['requires'].items(): self.assertEqual(state[k],v)
                self.assertTrue(e['changes'])
                for k,v in e['changes'].items(): self.assertEqual(state[k],v['before']); state[k]=v['after']
            self.assertEqual(state,ep['after'])

if __name__=='__main__': unittest.main()
