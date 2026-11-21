"""Grounded scale completion, causal token attributes, clocks and coarse sampling."""
from copy import deepcopy
import unittest

from .event_scale_bank import BANK
from .event_scales import validate_bank, refresh, set_mission, time_distribution
from .memory_transfer import receiving_world, decode_world
from .scale_continuation import catalogue, demonstration, rank, run, _variants
from .story_memory import annotate, validate
from .storytelling.runtime import generate, setup, replay, build_forest


class EventScaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows={s:generate(s,3007,multiscale=True) for s in BANK}
        cls.docs=[annotate(r) for r in cls.rows.values()]
        cls.pool=catalogue(cls.docs)

    def test_bank_and_all_worlds_replay_with_grounded_scale_graphs(self):
        self.assertTrue(validate_bank())
        for row,doc in zip(self.rows.values(),self.docs):
            with self.subTest(scenario=row['scenario']):
                self.assertTrue(replay(row));self.assertTrue(validate(doc))
                n=row['final_world']['narrative'];clock=n['clock'];history=row['final_world']['history']
                self.assertEqual(clock['step'],len(history))
                self.assertEqual(clock['seconds'],sum(e['time']['duration_seconds'] for e in history))
                self.assertTrue(all(c['status']=='achieved' for c in n['commitments'].values() if c['scale']=='story'))
                previous=0
                for e in history:
                    self.assertEqual(e['time']['start_seconds'],previous)
                    previous=e['time']['end_seconds']
                for event in doc['events']:
                    self.assertLessEqual(set(event['scales']),doc['event_scales']['nodes'].keys())
                for token in doc['tokens']:
                    self.assertLessEqual(set(token['memory'].get('scales',[])),doc['event_scales']['nodes'].keys())

    def test_attributes_exist_before_sampling_and_do_not_predict_achievement(self):
        pack,w=setup('repair',7,multiscale=True);before=w.to_dict()
        forest,_=build_forest(pack,w,predict_attributes=True)
        prediction=forest.predict()
        self.assertEqual(w.to_dict(),before)
        self.assertAlmostEqual(sum(c['probability'] for c in prediction['annotated_choices']),1.)
        for a in forest.attribute_table.values():
            self.assertIn('event_scales',a)  # Includes END/silent-event attributes.
            info=a['event_scales'];self.assertEqual(info['start_seconds'],0)
            self.assertEqual(len(info['memberships']),3)
            self.assertTrue(all(m['status']!='achieved' for m in info['memberships']))

    def test_optional_metadata_preserves_surface_and_silence_advances_time(self):
        for scenario in ('repair','music','pottery'):
            a=generate(scenario,3007);b=self.rows[scenario]
            self.assertEqual(a['story'],b['story'])
            self.assertNotIn('narrative',a['final_world'])
        silent=[e for r in self.rows.values() for e in r['final_world']['history'] if not e['sentence']]
        self.assertTrue(silent)
        self.assertTrue(all(e['time']['duration_seconds']>0 for e in silent))

    def test_intent_missing_carrier_deadline_abandonment_and_forged_event(self):
        pack,w=setup('repair',7,multiscale=True)
        frame=pack.candidates(w)[0][1];pack.commit(w,frame,'I will repair it.')
        root=next(c for c in w.narrative['commitments'].values() if c['scale']=='story')
        self.assertEqual(root['status'],'active')
        root['deadline_seconds']=0;refresh(w);self.assertEqual(root['status'],'blocked')
        root['status']='abandoned';refresh(w);self.assertEqual(root['status'],'abandoned')
        before=w.to_dict()
        with self.assertRaises(ValueError):pack.commit(w,frame,'stale promise')
        self.assertEqual(w.to_dict(),before)
        w=decode_world(self.rows['repair']['final_world']);del w.entities['hero'];refresh(w)
        self.assertTrue(all(c['status']=='blocked' for c in w.narrative['commitments'].values() if c['scale']=='story'))

    def test_duration_convolution_and_realistic_pottery_lower_bound(self):
        a=time_distribution('repair',('cart_goal','refit_and_test'))
        self.assertAlmostEqual(sum(a.values()),1.)
        self.assertEqual(min(a),10);self.assertEqual(max(a),120)
        b=time_distribution('pottery',('dry','bisque','cool_bisque','fire','cool_final'))
        self.assertGreaterEqual(min(b),18000)
        self.assertAlmostEqual(sum(b.values()),1.)

    def test_catalogue_deduplicates_and_ranking_is_pure(self):
        self.assertEqual(len(self.pool),len(catalogue(self.docs*2)))
        self.assertEqual({c['scenario'] for c in self.pool},set(BANK))
        w=demonstration(7);before=w.to_dict()
        subset=[c for c in self.pool if c['scenario'] in ('repair','museum','pottery')]
        choices,stop=rank(w,subset)
        self.assertEqual(w.to_dict(),before)
        self.assertAlmostEqual(sum(c['summary']['probability'] for c in choices)+stop['probability'],1.)
        productive=sum(c['summary']['probability'] for c in choices if c['summary']['progress'])
        self.assertGreater(productive,.9)
        late=[c['summary'] for c in choices if c['unit']['scenario']=='pottery' and c['unit']['requested_event']=='ending']
        self.assertTrue(late);self.assertTrue(all(c['deadline_probability']==0 for c in late))

    def test_resuming_native_prefix_executes_only_new_events_on_same_objects(self):
        from .memory_transfer import attach
        from .scale_continuation import _serialize
        doc=next(d for d in self.docs if d['scenario']=='repair')
        spec=attach([doc],[dict(event='admit_and_shelter',bindings={'cart':'trolley'})],demonstration(7))
        first=generate('joined',7,transfer=spec,multiscale=True)
        w=decode_world(first['final_world']);old=spec['units'][0]
        target=next(c for c in self.pool if c['scenario']=='repair' and c['requested_event']=='refit_and_test')
        initial,unit,offset,resumed=next(_variants(w,target,[old]))
        self.assertTrue(resumed);self.assertEqual(offset,len(old['frames']))
        self.assertEqual(unit['mapping'],old['mapping']);self.assertEqual(unit['leakage'],[])
        transfer=_serialize(dict(initial_world=initial.to_dict(),units=[unit]))
        second=generate('joined',8,transfer=transfer,multiscale=True)
        self.assertTrue(replay(second))
        self.assertEqual(len(second['trace']),len(target['frames'])-offset)
        self.assertEqual(second['final_world']['history'][:offset],first['final_world']['history'])
        self.assertIn('repaired',second['final_world']['entities']['trolley']['state'])
        self.assertGreater(second['final_world']['narrative']['clock']['seconds'],w.narrative['clock']['seconds'])

    def test_capability_requires_executed_episode_on_carrier_after_prerequisites(self):
        w=demonstration();n=w.narrative
        # A label or a proposed episode is not evidence of a performance.
        n['commitments']['fake']=dict(scale='episode',status='proposed',offers=['performance'],carrier='nia',started_at=0)
        from .event_scales import refresh_mission
        refresh_mission(w)
        self.assertEqual(n['mission']['needs'][-1]['status'],'waiting')
        w.entities['trolley'].state={'repaired'};w.entities['shadow'].state={'small','controlled'}
        n['clock']['seconds']=10;refresh_mission(w)
        n['commitments']['fake']['status']='achieved';refresh_mission(w)
        self.assertEqual(n['mission']['needs'][-1]['status'],'active')  # Too early.
        n['commitments']['fake']['started_at']=10;n['commitments']['fake']['carrier']='omar';refresh_mission(w)
        self.assertEqual(n['mission']['status'],'active')
        with self.assertRaises(ValueError):set_mission(w,dict(carrier='nia',needs=[dict(name='a',requires=['b'],offer='x')]))

    def test_goal_conditioned_run_transfers_real_effects_and_reports_distribution(self):
        result=run(self.pool,seed=7,max_episodes=4)
        self.assertTrue(result['summary']['success']);self.assertEqual(result['reason'],'goal_achieved')
        self.assertEqual(result['summary']['needs_achieved'],3)
        for decision in result['decisions']:
            self.assertAlmostEqual(sum(c['probability'] for c in decision['candidates']),1.)
        for row in result['rows']:self.assertTrue(replay(row));self.assertTrue(validate(annotate(row)))
        mission=result['mission']
        self.assertTrue(mission['needs'][-1]['evidence'])
        # Goal is copied into receiving token candidates, not only the final report.
        first=result['rows'][0]
        attrs=first['trace'][0]['attribute_table'].values()
        self.assertTrue(all(a['event_scales']['primary_goal']['status']=='active' for a in attrs))


if __name__=='__main__':unittest.main()
