"""Physical interventions and attention changes for new causal story branches."""
from copy import deepcopy
from dataclasses import replace
import unittest
from .engine import score_frame,softmax
from .world import Frame
from .storytelling.runtime import generate,replay,setup,build_forest


class BranchTests(unittest.TestCase):
    def test_remade_bowl_keeps_firing_safety_and_two_hand_requirements(self):
        row=generate('pottery',1);self.assertTrue(replay(row))
        self.assertIn('bowl_design',row['final_world']['flags'])
        self.assertEqual(row['final_world']['entities']['cup']['noun'],'bowl')
        self.assertNotIn('wide_handle',row['final_world']['entities']['cup']['state'])
        self.assertIn('holding_with_two_hands',row['final_world']['entities']['grandpa']['state'])
        pack,w=setup('pottery',1);checked=set()
        for event in row['final_world']['history']:
            f=Frame(**{**event['frame'],'cause_ids':tuple(event['frame']['cause_ids'])})
            if f.kind=='remake':
                altered=w.clone();altered.entities['cup'].state.discard('wet')
                with self.assertRaises(ValueError):pack.commit(altered,f,'')
                checked.add('wet')
            if f.kind=='give':
                for state in ('fired','cool','safe_edges','stable','two_hand_grip'):
                    altered=w.clone();altered.entities['cup'].state.discard(state)
                    with self.assertRaises(ValueError):pack.commit(altered,f,'')
                    checked.add(state)
                altered=w.clone();altered.entities['grandpa'].properties.discard('two_hands')
                with self.assertRaises(ValueError):pack.commit(altered,f,'')
                checked.add('hands')
            pack.commit(w,f,event['sentence'])
        self.assertEqual(checked,{'wet','fired','cool','safe_edges','stable','two_hand_grip','hands'})

    def test_library_choice_controls_drawing_and_attention(self):
        seen=set()
        for seed in range(12):
            row=generate('library',seed);self.assertTrue(replay(row));state=row['final_world']
            released='atlas_released' in state['flags'];seen.add(released)
            self.assertIn('whale_drawing' if released else 'moon_drawing',state['entities']['paper']['state'])
        self.assertEqual(seen,{False,True})
        row=generate('library',0);pack,w=setup('library',0)
        for event in row['final_world']['history']:
            if event['frame']['kind'] in {'reserve_atlas','release_atlas'}:break
            f=Frame(**{**event['frame'],'cause_ids':tuple(event['frame']['cause_ids'])});pack.commit(w,f,event['sentence'])
        probabilities=[]
        for care in (0,1):
            altered=w.clone();altered.entities['hero'].memes['Care']=care
            forest,_=build_forest(pack,altered);mass={}
            for d in forest.derivations:mass[d.frame.kind]=mass.get(d.frame.kind,0)+d.probability
            self.assertTrue(0<mass['release_atlas']<1)
            probabilities.append(mass['release_atlas'])
        self.assertGreater(probabilities[1],probabilities[0])

    def test_library_drawing_requires_picture_and_pencil(self):
        row=generate('library',0);pack,w=setup('library',0);checked=False
        for event in row['final_world']['history']:
            f=Frame(**{**event['frame'],'cause_ids':tuple(event['frame']['cause_ids'])})
            if f.kind.startswith('sketch_'):
                for mutation in ('pencil','picture'):
                    altered=w.clone()
                    if mutation=='pencil':altered.entities['pencil'].location='elsewhere'
                    else:altered.entities['book'].state.discard('whale_picture')
                    before=altered.to_dict()
                    with self.assertRaises(ValueError):pack.commit(altered,f,'')
                    self.assertEqual(before,altered.to_dict())
                checked=True
            pack.commit(w,f,event['sentence'])
        self.assertTrue(checked)

    def test_greenhouse_water_conservation_and_different_outcomes(self):
        seen=set()
        for seed in range(20):
            row=generate('greenhouse',seed);self.assertTrue(replay(row))
            state=row['final_world'];flags=state['flags'];e=state['entities']
            branch=next(k for k in ['share_plan','seedlings_first','flower_first'] if k in flags);seen.add(branch)
            added=0
            for event in row['final_world']['history']:
                if event['frame']['kind']=='refill':added+=2
                total=sum(event['after']['entities'][key]['memes']['Water'] for key in ['barrel','can','tomatoes','sunflower'])
                self.assertEqual(total,2+added)
            self.assertEqual(e['can']['memes']['Water'],0)
            if branch=='share_plan':
                self.assertEqual(e['tomatoes']['memes']['Water'],1)
                self.assertEqual(e['sunflower']['memes']['Water'],1)
                self.assertIn('broken',e['tap']['state'])
                self.assertIn('promised_repair',e['caretaker']['state'])
            else:self.assertIn('repaired',e['tap']['state'])
            self.assertEqual('brown' in e['leaf']['state'],branch=='flower_first')
        self.assertEqual(seen,{'share_plan','seedlings_first','flower_first'})

    def test_greenhouse_empty_can_and_missing_anchor_block_actions(self):
        row=generate('greenhouse',2);pack,w=setup('greenhouse',2);checked=set()
        for event in row['final_world']['history']:
            f=Frame(**{**event['frame'],'cause_ids':tuple(event['frame']['cause_ids'])})
            if f.kind in {'water_first','water_second','secure'}:
                altered=w.clone()
                if f.kind=='secure':altered.entities['pot'].state.discard('weighted_with_pebbles')
                else:altered.entities['can'].memes['Water']=0
                before=altered.to_dict()
                with self.assertRaises(ValueError):pack.commit(altered,f,'')
                self.assertEqual(before,altered.to_dict());checked.add(f.kind)
            pack.commit(w,f,event['sentence'])
        self.assertEqual(checked,{'water_first','water_second','secure'})

    def test_cardinal_grammar_preserves_number_agreement(self):
        from .storytelling.surface import SpeechLanguage,detokenize
        from .grammar import expand
        pack,w=setup('greenhouse',0);g=SpeechLanguage(w,lexicon=pack.LEXICON)
        for number,expected in [(1,'one can was empty'),(2,'two cans were empty')]:
            sentence=g.s(g.counted(number,'can'),g.be('empty'))
            self.assertEqual(' '.join(next(expand(sentence.node))[0]),expected)
        with self.assertRaises(ValueError):g.counted(0,'can')

    def test_music_participation_branches_and_consent_guards(self):
        seen=set(); checked=False
        for seed in range(36):
            row=generate('music',seed);self.assertTrue(replay(row))
            state=row['final_world']; flags=state['flags']
            kind='private' if 'private_plan' in flags else 'written' if 'pattern_plan' in flags else 'solo'
            seen.add(kind)
            self.assertEqual(state['entities']['drum']['location'],'shelf')
            self.assertEqual(state['entities']['spare']['location'],'shelf')
            if kind=='written':
                self.assertIn('rhythm',state['entities']['paper']['state'])
                self.assertNotIn('joined',state['entities']['partner']['state'])
            if kind=='private' and not checked:
                pack,w=setup('music',seed)
                for e in row['final_world']['history']:
                    f=Frame(**{**e['frame'],'cause_ids':tuple(e['frame']['cause_ids'])})
                    if f.kind=='join':
                        for entity in ['hero','partner','drum','spare']:
                            altered=w.clone();altered.entities[entity].location='outside'
                            with self.assertRaises(ValueError):pack.commit(altered,f,'')
                        altered=w.clone();altered.entities['partner'].state.discard('consented')
                        with self.assertRaises(ValueError):pack.commit(altered,f,'')
                        checked=True
                    pack.commit(w,f,e['sentence'])
        self.assertEqual(seen,{'private','written','solo'});self.assertTrue(checked)
        for seed in range(12):
            row=generate('music',seed,partner_willing=False)
            self.assertNotIn('private_plan',row['final_world']['flags'])
            self.assertNotIn('joined',row['final_world']['entities']['partner']['state'])

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
