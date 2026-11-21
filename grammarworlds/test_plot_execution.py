"""Physical plot contracts, shared identities, causal evidence and reader scope."""
from copy import deepcopy
import unittest

from .memory_transfer import receiving_world,decode_world,run as native_run
from .plot_execution import set_plot,finalize_narration
from .plot_continuation import catalogue,rank,run
from .story_memory import annotate
from .storytelling.runtime import generate,replay,setup,build_forest
from .world import Frame


class PlotExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=[annotate(generate(s,3007)) for s in ('pottery','costume','biscuit','repair','market','museum')]
        cls.pool=catalogue(cls.docs)

    def test_shared_object_and_recipient_survive_every_gift_stage(self):
        w=receiving_world();before=w.to_dict()
        r=run(self.pool,'adapt_gift',seed=19,world=w)
        self.assertEqual(w.to_dict(),before);self.assertTrue(r['summary']['success'])
        p=r['plot'];self.assertEqual(p['active_stage'],4)
        for s in p['stages']:self.assertEqual(s['evidence']['bindings'],p['bindings'])
        self.assertEqual(r['final_world']['entities'][p['bindings']['object']]['location'],p['bindings']['recipient'])
        self.assertEqual(r['summary']['resumed'],3)
        self.assertEqual(r['summary']['open_obligations'],0)
        self.assertTrue(all(n['status']=='satisfied' for n in p['narration_requirements'].values()))
        for row in r['rows']:self.assertTrue(replay(row));annotate(row)

    def test_unrelated_biscuit_cannot_pay_off_adapted_cape(self):
        w=receiving_world();set_plot(w,'adapt_gift')
        docs=[d for d in self.docs if d['scenario'] in {'costume','biscuit'}]
        row=native_run(docs,[dict(scenario='costume',extent='story'),dict(scenario='biscuit',extent='story')],w,
                       multiscale=True,plot_annotations=True)
        p=row['final_world']['narrative']['plot_execution']
        self.assertEqual(p['active_stage'],2)
        self.assertEqual(p['bindings']['object'],'u0__cape')
        self.assertEqual(p['obligations'][0]['status'],'open')
        self.assertEqual(p['stages'][2]['status'],'pending')
        self.assertTrue(replay(row))

    def test_changed_approach_uses_real_discovery_and_has_ending(self):
        r=run(self.pool,'changed_approach',seed=19)
        self.assertTrue(r['summary']['success']);self.assertEqual(r['summary']['completed_stages'],6)
        p=r['plot'];known={e['event'] for e in p['knowledge_evidence']}
        self.assertTrue(known)
        approach=p['stages'][3]['evidence']
        self.assertTrue(any(l['source_event'] in known and l['relation']=='uses_discovery' for l in approach['incoming_links']))
        self.assertLess(p['stages'][1]['evidence']['event'],p['stages'][2]['evidence']['event'])
        for row in r['rows']:self.assertTrue(replay(row));annotate(row)

    def test_ranking_is_pure_normalized_and_rejects_dead_end_object(self):
        w=receiving_world();set_plot(w,'adapt_gift');before=w.to_dict()
        choices,rejected=rank(w,self.pool)
        self.assertEqual(w.to_dict(),before)
        self.assertAlmostEqual(sum(c['summary']['probability'] for c in choices),1.)
        self.assertEqual({c['summary']['source'] for c in choices},{'pottery'})
        self.assertTrue(any(c['source']=='costume' and c['reason']=='no_native_suffix_completion' for c in rejected))
        self.assertEqual([c['summary']['probability'] for c in choices],
                         [c['summary']['probability'] for c in rank(w,self.pool*2)[0]])

    def test_silent_ending_does_not_pass_narration_contract(self):
        w=receiving_world();set_plot(w,'changed_approach')
        row=native_run([d for d in self.docs if d['scenario']=='repair'],[dict(scenario='repair',extent='story')],w,
                       multiscale=True,plot_annotations=True)
        p,live=setup('joined',row['seed'],**row['options'])
        for saved in row['final_world']['history']:
            f=Frame(**{**saved['frame'],'cause_ids':tuple(saved['frame']['cause_ids'])})
            last=saved is row['final_world']['history'][-1]
            e=p.commit(live,f,'' if last else saved['sentence'])
            for k in ('referents','speakers','narrated'):e[k]=saved[k]
            if last:e['narrated']=False
            finalize_narration(live,e)
        self.assertEqual(live.narrative['plot_execution']['status'],'narration_incomplete')
        self.assertEqual(live.to_dict()['entities'],row['final_world']['entities'])

    def test_current_prefix_context_excludes_future_evidence(self):
        w=receiving_world();set_plot(w,'changed_approach')
        from .memory_transfer import attach
        spec=attach([d for d in self.docs if d['scenario']=='repair'],[dict(scenario='repair',extent='story')],w)
        p,live=setup('joined',7,transfer=spec,multiscale=True,plot_annotations=True)
        before=live.to_dict();forest,_=build_forest(p,live,predict_attributes=True)
        self.assertEqual(live.to_dict(),before)
        for a in forest.attribute_table.values():
            state=a['plot']['receiving_plot']
            self.assertEqual(state['active_stage'],0)
            self.assertEqual(state['knowledge_evidence'],[]);self.assertEqual(state['reader_knowledge'],[])
            self.assertTrue(all(s['evidence'] is None for s in state['stages']))

    def test_ending_can_show_physical_effect_on_recipient(self):
        doc=annotate(generate('pottery',3006))
        r=run(catalogue([doc]),'changed_approach',seed=7)
        self.assertTrue(r['summary']['success'])
        need=r['plot']['narration_requirements']['show_changed_world']
        self.assertIn('u0__grandpa',need['observed_entities'])
        row=r['rows'][-1];self.assertTrue(replay(row));annotate(row)
        w=decode_world(row['final_world']);e=w.history[-1]
        self.assertNotEqual(e['before']['entities']['u0__grandpa']['state'],
                            e['after']['entities']['u0__grandpa']['state'])
        # Merely naming the protagonist cannot satisfy this ending's evidence.
        e['referents']=['nia'];e['speakers']=[]
        finalize_narration(w,e)
        self.assertEqual(w.narrative['plot_execution']['status'],'narration_incomplete')

    def test_character_knowledge_requires_native_epistemic_state_change(self):
        w=receiving_world();set_plot(w,'changed_approach')
        row=native_run([d for d in self.docs if d['scenario']=='repair'],[dict(scenario='repair',extent='story')],w,
                       multiscale=True,plot_annotations=True)
        p=row['final_world']['narrative']['plot_execution']
        self.assertIn('nia',p['character_knowledge'])
        for item in p['character_knowledge']['nia']:
            e=next(e for e in row['final_world']['history'] if e['id']==item['event'])
            self.assertNotIn(item['state'],e['before']['entities']['nia']['state'])
            self.assertIn(item['state'],e['after']['entities']['nia']['state'])
        self.assertTrue(p['reader_knowledge'])

    def test_native_guards_still_reject_stale_frames_without_plot_mutation(self):
        w=receiving_world();set_plot(w,'changed_approach')
        from .memory_transfer import attach
        spec=attach([d for d in self.docs if d['scenario']=='repair'],[dict(scenario='repair',extent='story')],w)
        p,live=setup('joined',7,transfer=spec,multiscale=True,plot_annotations=True)
        f=p.candidates(live)[0][1];p.commit(live,f,'');before=live.to_dict()
        with self.assertRaises(ValueError):p.commit(live,f,'forged')
        self.assertEqual(live.to_dict(),before)
        with self.assertRaises(ValueError):set_plot(w,'adapt_gift')
        with self.assertRaises(ValueError):set_plot(receiving_world(),'adapt_gift',bindings={'object':'missing'})


if __name__=='__main__':unittest.main()
