import copy
from dataclasses import replace
import json
import random
import unittest

import runtime as r
from runtime import Condition as C, Rule, WorldSpec, scene
from prose import render_book, lint
from test_storyscenes import fixture


class PlanningTests(unittest.TestCase):
    def test_always_on_rule_does_not_keep_unused_loan(self):
        spec = fixture()
        spare = scene('busywork','Loan',('ben',),set_values={'key.used':True},weight=10000)
        rule = Rule('valid flag',(C('key.used','in',(True,False)),))
        result = r.solve(replace(spec, scenes=(spare,)+spec.scenes, rules=spec.rules+(rule,), prune=True), 1)
        self.assertNotIn('busywork',[e['scene'] for e in result['events']])

    def test_shared_kernel_keywords_have_consistent_semantics(self):
        s = r.observe('look','ada','box.latch',when=(C('key.used','eq',True),),pivotal=True)
        self.assertIsNone(r.transition(fixture().initial,s))
        self.assertTrue(s.pivotal)

    def test_irrelevant_loan_is_removed_but_knowledge_chain_remains(self):
        spec = fixture()
        spare = scene('busywork','Loan',('ben',), set_values={'key.used':True}, summary='Ben polished a spare key', weight=10000)
        spec = replace(spec, scenes=(spare,)+spec.scenes, prune=True)
        result = r.solve(spec, 1)
        self.assertIn('busywork', result['pruned_scenes'])
        self.assertEqual([e['scene'] for e in result['events']], ['look','explain','lend','unlock'])
        self.assertEqual(result['events'][-1]['causes'], [1,3])

    def test_rule_only_dependency_is_preserved(self):
        spec = WorldSpec('Load', {'cart':{'name':'cart','kind':'prop'}},
            {'cart.reinforced':False,'cart.load':0},
            (scene('reinforce','Build',('cart',),set_values={'cart.reinforced':True},summary='reinforced'),
             scene('load','Carry',('cart',),set_values={'cart.load':4},summary='loaded')),
            (C('cart.load','eq',4),),
            (Rule('heavy needs reinforcement',(C('cart.reinforced','eq',True),),(C('cart.load','ge',3),)),), prune=True)
        self.assertEqual([e['scene'] for e in r.solve(spec)['events']], ['reinforce','load'])

    def test_explicit_character_turn_is_kept(self):
        spec = fixture()
        turn = scene('reconsider','Humility',('ben',),set_values={'ben.memes.Care':2},summary='Ben reconsidered',weight=10000,pivotal=True)
        result = r.solve(replace(spec, scenes=(turn,)+spec.scenes, prune=True), 0)
        self.assertIn('reconsider',[e['scene'] for e in result['events']])

    def test_keyword_effects_do_not_reverse_copy_arguments(self):
        s = scene('copy','Tell',('ada',),copies={'ada.knows.box.latch':'box.latch'})
        state = r.transition(fixture().initial,s)
        self.assertEqual(state['ada.knows.box.latch'],'left')


def card(text, when=None):
    return {'text':text,'when':when or []}


def book_for(trace):
    return dict(openings=[card('Ada wanted the box open.')],
                scenes=[dict(scene=e['scene'],role='bridge',variants=[card(e['summary']+'.')]) for e in trace['events']],
                endings=[card('The lid stood open.')],lexicon=[])


class ProseTests(unittest.TestCase):
    def test_opening_cannot_cite_future_state(self):
        trace=r.solve(fixture())
        def bad(run,rng):
            p=render_book(run,rng,book_for(run)); p[0]['facts']=[dict(at=4,key='box.open',value=True)]; return p
        with self.assertRaisesRegex(r.StoryError,'future state'):
            r.realize(trace,bad)

    def test_correct_state_variant_is_selected(self):
        trace = r.solve(fixture())
        book = book_for(trace)
        book['endings'] = [card('The lid stayed shut.',[dict(key='box.open',op='eq',value=False,at='after')]),
                           card('The lid stood open.',[dict(key='box.open',op='eq',value=True,at='after')])]
        result = r.realize(trace,lambda run,rng:render_book(run,rng,book))
        self.assertTrue(result['story'].endswith('The lid stood open.'))
        self.assertEqual(result['paragraphs'][-1]['facts'],[dict(at=4,key='box.open',value=True)])

    def test_missing_phrase_fails_instead_of_leaking_enum(self):
        trace=r.solve(fixture()); book=book_for(trace)
        book['openings']=[card('The latch {phrase:box.latch}.')]
        with self.assertRaisesRegex(r.StoryError,'Missing grammatical'):
            render_book(trace,random.Random(0),book)
        book['lexicon']=[dict(key='box.latch',value='left',text='leaned to the left')]
        self.assertEqual(render_book(trace,random.Random(0),book)[0]['text'],'The latch leaned to the left.')

    def test_bridges_join_without_dropping_events(self):
        trace=r.solve(fixture()); book=book_for(trace)
        result=r.realize(trace,lambda run,rng:render_book(run,rng,book))
        self.assertEqual(len(result['paragraphs']),3)
        self.assertEqual(result['paragraphs'][1]['event_ids'],[1,2,3,4])

    def test_known_bad_prose_is_flagged(self):
        self.assertIn('unresolved_alternative',lint('It held—or did not hold—in the breeze.'))
        self.assertIn('literal_state_value',lint('It bore a family_mark.'))
        self.assertIn('repeated_word',lint('A borrowed borrowed button lay there.'))
        self.assertEqual(lint('The family mark looked like a tiny fish.'),[])

    def test_fact_cannot_contradict_trace(self):
        trace=r.solve(fixture())
        def bad(run,rng):
            p=render_book(run,rng,book_for(run)); p[-1]['facts']=[dict(at=4,key='box.open',value=False)]; return p
        with self.assertRaisesRegex(r.StoryError,'Contradicted prose fact'):
            r.realize(trace,bad)

    def test_before_and_after_are_distinct(self):
        trace=r.solve(fixture()); book=book_for(trace)
        book['scenes'][-1]['variants']=[card('Ada lifted the closed lid.',[
            dict(key='box.open',op='eq',value=False,at='before'),
            dict(key='box.open',op='eq',value=True,at='after')])]
        p=render_book(trace,random.Random(0),book)
        self.assertIn('Ada lifted the closed lid.',p[1]['text'])


class RepairTests(unittest.TestCase):
    def test_plain_card_text_preserves_conditions(self):
        from repairs import patch_catalog
        book={'endings':[card('Old.',[dict(key='box.open',op='eq',value=True,at='after')])]}
        fixed=patch_catalog(book,{'edits':[dict(path='/endings/0',value_json='The lid stood open.')]})
        self.assertEqual(fixed['endings'][0]['when'],book['endings'][0]['when'])
        self.assertEqual(fixed['endings'][0]['text'],'The lid stood open.')

    def test_non_flex_dispatch_is_refused(self):
        import asyncio
        from pathlib import Path
        from workshop import artifact,request
        body=request('x','gpt-5.6-luna');body['service_tier']='default'
        with self.assertRaisesRegex(ValueError,'Only Flex'):
            asyncio.run(artifact(None,None,Path('/private/tmp/unused_storyscenes_world'),'simulation_0',body))

    def test_nested_json_text_newlines_are_data(self):
        from repairs import patch_catalog
        book={'endings':[card('Old.')]}
        fixed=patch_catalog(book,{'edits':[dict(path='/endings/0/text',value_json='"First.\nSecond."')]})
        self.assertEqual(fixed['endings'][0]['text'],'First.\nSecond.')

    def test_critic_samples_different_outcomes_before_more_of_same(self):
        from workshop import critic_selection
        rows=[dict(seed=i,trace={'outcome':{'box.open':x}}) for i,x in enumerate([False,False,True,'ajar','ajar'])]
        self.assertEqual([r['seed'] for r in critic_selection(rows)],[0,2,3])

    def test_key_rename_updates_beliefs_without_touching_prose(self):
        from repairs import patch_source
        source="state = {'show.mode': 'quiet', 'ada.knows.show.mode': None}\ntext = 'A show.mode is a label'\n"
        fixed=patch_source(source,{'edits':[],'renames':[dict(old='show.mode',new='lamp.show_mode')]})
        self.assertIn("'lamp.show_mode'",fixed)
        self.assertIn("'ada.knows.lamp.show_mode'",fixed)
        self.assertIn("'A show.mode is a label'",fixed)

    def test_unfinished_outcome_is_detected_even_when_other_outcomes_vary(self):
        from quality_checks import unfinished_outcomes
        rows=[{'trace':{'initial':{'cart.mode':'none','cart.performed':False},'final':{'cart.mode':v,'cart.performed':False}},
               'diagnostics':{'outcome_writes':['cart.mode','cart.performed']}} for v in ('float','library','room')]
        self.assertEqual(unfinished_outcomes(rows),['cart.performed'])

    def test_source_edits_fail_closed_on_ambiguous_target(self):
        from repairs import patch_source
        with self.assertRaisesRegex(ValueError,'exactly once'):
            patch_source('x=1\nx=1\n',{'edits':[{'old':'x=1','new':'x=2'}]})

    def test_source_cannot_be_replaced_wholesale(self):
        from repairs import patch_source
        source='x=1\n'*200
        with self.assertRaisesRegex(ValueError,'fragment'):
            patch_source(source,{'edits':[{'old':source,'new':'x=2'}]})

    def test_catalog_patch_is_atomic_and_narrow(self):
        from repairs import patch_catalog
        book={'endings':[card('Old.')],'scenes':[]}
        updated=patch_catalog(book,{'edits':[{'path':'/endings/0/text','value_json':'"New."'}]})
        self.assertEqual(updated['endings'][0]['text'],'New.')
        self.assertEqual(book['endings'][0]['text'],'Old.')
        with self.assertRaisesRegex(ValueError,'individual'):
            patch_catalog(book,{'edits':[{'path':'/endings','value_json':'[]'}]})

    def test_authoring_refuses_stronger_model_before_any_request(self):
        import asyncio
        from pathlib import Path
        from workshop import artifact, request
        with self.assertRaisesRegex(ValueError,'must use Luna'):
            asyncio.run(artifact(None,None,Path('/private/tmp/unused_storyscenes_world'),'simulation_0',request('x','gpt-5.6-terra')))


if __name__=='__main__':
    unittest.main()
