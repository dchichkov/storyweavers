"""Plot labels preserve evidence scope, carrier identity and source posteriors."""
from copy import deepcopy
import unittest

from .plot_annotations import annotate_plots,validate_bank,validate_plots
from .plot_bank import BANK,ARCHETYPES
from .storytelling.runtime import generate,setup,build_forest,replay
from .story_memory import annotate
from .memory_transfer import run,decode_world,attach


class PlotAnnotationTests(unittest.TestCase):
    def test_bank_covers_all_twenty_without_inventing_all_nine_arcs(self):
        self.assertTrue(validate_bank())
        labels={a['name'] for s in BANK.values() for a in s['archetypes']}
        self.assertLess(labels,set(ARCHETYPES));self.assertEqual(len(BANK),20)
        self.assertFalse(BANK['music']['archetypes'])

    def test_annotation_preserves_text_and_conditional_posteriors(self):
        d=annotate(generate('repair',7));before=deepcopy(d)
        annotate_plots(d);self.assertEqual(d,before)  # Idempotent as well.
        self.assertEqual(d['text'],before['text']);self.assertEqual(d['attributes'],before['attributes'])
        by_kind={e['kind']:e for e in d['events']}
        finding=by_kind['diagnose_string'];repair=by_kind['refit_and_test']
        self.assertEqual(finding['plot']['role'],'discovery')
        self.assertTrue(any(l['source_event']==finding['id'] and l['relation']=='uses_discovery' for l in repair['plot']['incoming_links']))
        self.assertEqual(repair['plot']['observed_consequences'],repair['effects'])
        self.assertTrue(all(not l['mechanically_verified'] for l in repair['plot']['incoming_links']))
        for t in d['tokens']:self.assertIn('plot',t['memory'])

    def test_live_candidates_do_not_contain_future_observations(self):
        p,w=setup('repair',7,plot_annotations=True,multiscale=True)
        before=w.to_dict();forest,_=build_forest(p,w,predict_attributes=True)
        self.assertEqual(w.to_dict(),before)
        for a in forest.attribute_table.values():
            plot=a['plot']
            self.assertEqual(plot['scope'],'receiving_prefix')
            self.assertEqual(plot['incoming_links'],[])
            self.assertNotIn('observed_consequences',plot)
            self.assertNotIn('native_dependencies',plot)
        while not p.candidates(w)[0][1].kind=='refit_and_test':p.commit(w,p.candidates(w)[0][1],'')
        plot=p.plot_context(w,p.candidates(w)[0][1])
        known={e['id'] for e in w.history}
        self.assertTrue(plot['incoming_links'])
        self.assertTrue(all(l['source_event'] in known for l in plot['incoming_links']))

    def test_opt_in_metadata_changes_neither_prose_nor_world(self):
        for scenario in ('repair','music','pottery'):
            base=generate(scenario,7,multiscale=True)
            row=generate(scenario,7,multiscale=True,plot_annotations=True)
            self.assertEqual(base['story'],row['story']);self.assertEqual(base['final_world'],row['final_world'])
            self.assertTrue(replay(row));self.assertTrue(validate_plots(annotate(row)))

    def test_joined_roles_bind_to_receiving_entities_and_do_not_create_global_plot(self):
        docs=[annotate(generate(s,7)) for s in ('repair','museum')]
        row=run(docs,[dict(event='refit_and_test'),dict(event='controlled_trial')],seed=7,plot_annotations=True)
        d=annotate(row);self.assertTrue(replay(row));self.assertEqual(len(d['plots']['nodes']),2)
        for node in d['plots']['nodes'].values():
            self.assertEqual(node['roles']['protagonist'],['nia'])
            self.assertEqual(node['scope'],'transferred_source_arc')
        for trace in row['trace']:
            for a in trace['attribute_table'].values():
                self.assertEqual(a['plot']['roles']['protagonist'],['nia'])
                self.assertLessEqual({x for ids in a['plot']['roles'].values() for x in ids},row['initial_world']['entities'].keys())

    def test_partial_program_has_no_unobserved_payoff_link(self):
        doc=annotate(generate('repair',7))
        row=run([doc],[dict(event='admit_and_shelter')],seed=7,plot_annotations=True)
        d=annotate(row)
        self.assertTrue(all(l['relation']!='payoff_of' for n in d['plots']['nodes'].values() for l in n['links']))
        corrupt=deepcopy(d)
        node=next(iter(corrupt['plots']['nodes'].values()))
        node['links'].append(dict(source_event=99,target_event=1,relation='payoff_of'))
        with self.assertRaises(ValueError):validate_plots(corrupt)

    def test_archived_world_without_plot_support_stays_valid(self):
        d=annotate(generate('kite',7,plot_annotations=True))
        self.assertNotIn('plots',d)


if __name__=='__main__':unittest.main()
