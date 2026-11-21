"""Physical interventions and attention changes for new causal story branches."""
from copy import deepcopy
from dataclasses import replace
import unittest
from .engine import score_frame,softmax
from .world import Frame
from .storytelling.runtime import generate,replay,setup,build_forest


class BranchTests(unittest.TestCase):
    def test_key_borrowing_never_claims_original_was_found(self):
        from .storytelling.qa import questions
        seen=set()
        for seed in range(12):
            row=generate('key',seed);self.assertTrue(replay(row))
            state=row['final_world']; borrowed='borrowed' in state['flags'];seen.add(borrowed)
            self.assertIn('open',state['entities']['door']['state'])
            if borrowed:
                self.assertEqual(state['entities']['spare']['location'],'helper')
                self.assertIn('lost',state['entities']['target']['state'])
                self.assertIn('search_reminder',state['entities']['note']['state'])
                q=next(q for q in questions(row) if q['id'].endswith(':outcome'))
                self.assertIn('still missing',q['answer'])
            else:self.assertEqual(state['entities']['target']['location'],'hook')
        self.assertEqual(seen,{False,True})

    def test_key_unlocking_requires_the_actual_held_key(self):
        checked=set()
        for seed in (0,1):
            row=generate('key',seed);pack,w=setup('key',seed)
            for e in row['final_world']['history']:
                f=Frame(**{**e['frame'],'cause_ids':tuple(e['frame']['cause_ids'])})
                if f.kind.startswith('unlock_'):
                    altered=w.clone();altered.entities[f.instrument].location='elsewhere'
                    before=altered.to_dict()
                    with self.assertRaises(ValueError):pack.commit(altered,f,'')
                    self.assertEqual(before,altered.to_dict());checked.add(f.kind)
                pack.commit(w,f,e['sentence'])
        self.assertEqual(checked,{'unlock_spare','unlock_original'})

    def test_kite_paths_include_repair_failure_and_material_reuse(self):
        paths=set()
        for seed in range(24):
            row=generate('kite',seed);self.assertTrue(replay(row))
            state=row['final_world']; flags=set(state['flags']);target=state['entities']['target']
            path='failed_then_sail' if 'failed' in flags else ('direct_sail' if 'converted' in flags else 'fly')
            paths.add(path)
            if 'converted' in flags:
                self.assertEqual(target['noun'],'sail')
                self.assertEqual(target['location'],'boat')
                self.assertEqual(state['entities']['boat']['location'],'pond')
                self.assertNotIn('flyable',target['properties'])
            else:self.assertEqual(target['location'],'sky')
        self.assertEqual(paths,{'fly','direct_sail','failed_then_sail'})

    def test_kite_conversion_and_launch_need_tools_and_material(self):
        row=generate('kite',0);pack,w=setup('kite',0)
        checks=0
        for e in row['final_world']['history']:
            f=Frame(**{**e['frame'],'cause_ids':tuple(e['frame']['cause_ids'])})
            changes={'cut_sail':('scissors','basket'),'attach_sail':('string','basket'),
                     'launch_boat':('target','meadow')}
            if f.kind in changes:
                altered=w.clone();entity,location=changes[f.kind];altered.entities[entity].location=location
                before=altered.to_dict()
                with self.assertRaises(ValueError):pack.commit(altered,f,'')
                self.assertEqual(before,altered.to_dict());checks+=1
            pack.commit(w,f,e['sentence'])
        self.assertEqual(checks,3)

    def test_rescue_strategies_have_distinct_physical_consequences(self):
        seen=set()
        for seed in range(12):
            row=generate('rescue',seed);self.assertTrue(replay(row))
            w=row['final_world'];basket='basket_plan' in w['flags'];seen.add(basket)
            self.assertEqual('eaten' in w['entities']['bread']['state'],basket)
            self.assertEqual('hungry' in w['entities']['hero']['state'],basket)
            self.assertTrue({'safe','warm'}<=set(w['entities']['target']['state']))
        self.assertEqual(seen,{False,True})

    def test_rescue_interventions_block_missing_physical_prerequisites(self):
        tested=set()
        for seed in (0,2):
            row=generate('rescue',seed);pack,w=setup('rescue',seed)
            for e in row['final_world']['history']:
                f=Frame(**{**e['frame'],'cause_ids':tuple(e['frame']['cause_ids'])})
                changes={
                    'rescue_lift': [('tool','location','shed'),('helper','location','outside')],
                    'load_basket': [('basket','location','cottage'),('bread','location','kitchen')],
                    'basket_lower': [('rope','location','window'),('target','location','ledge')],
                    'shelter': [('blanket','location','elsewhere')],
                }
                for entity,attribute,value in changes.get(f.kind,[]):
                    altered=w.clone();setattr(altered.entities[entity],attribute,value)
                    before=altered.to_dict()
                    self.assertNotIn(f,[ff for _,ff in pack.candidates(altered)])
                    with self.assertRaises(ValueError):pack.commit(altered,f,'')
                    self.assertEqual(before,altered.to_dict());tested.add(f.kind)
                pack.commit(w,f,e['sentence'])
        self.assertEqual(tested,{'rescue_lift','load_basket','basket_lower','shelter'})

    def test_rescue_attention_changes_real_strategy_and_word_probabilities(self):
        pack,w=setup('rescue',2)
        f=pack.candidates(w)[0][1];pack.commit(w,f,'')
        distributions=[]
        for fear in (0,1):
            altered=w.clone();altered.entities['hero'].memes['Fear']=fear
            before=altered.to_dict();forest,_=build_forest(pack,altered)
            masses={}
            for d in forest.derivations:masses[d.frame.kind]=masses.get(d.frame.kind,0)+d.probability
            distributions.append(masses)
            self.assertEqual(before,altered.to_dict())
            self.assertAlmostEqual(sum(c['probability'] for c in forest.predict(())['choices']),1)
        self.assertGreater(distributions[1]['choose_basket'],distributions[0]['choose_basket'])

if __name__=='__main__':unittest.main()
