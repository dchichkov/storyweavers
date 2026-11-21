"""Fragment retrieval, role rebinding, causal joins and physics invariants."""
from copy import deepcopy
import unittest

from .event_pool import attach, demo_brief, expand_fragment, generate, retrieve
from .pool_fragments import ROOTS, FRAGMENTS
from .pool_mechanics import PoolLines
from .catalog_attachment import bare_world, Unresolved
from .event_line_replay import replay, verify
from .world import Entity


def unrelated_world(magic=True):
    w=bare_world();w.setting='garden';w.hero='ada';w.helper='teo'
    w.entities={
        'ada':Entity('ada','Ada','person','garden',pronoun='she',properties={'can_hold'}|({'can_portal'} if magic else set())),
        'teo':Entity('teo','Teo','person','garden',pronoun='he',properties={'can_hold'}),
        'pet':Entity('pet','brown rabbit','animal','pen',properties={'rabbit','calm'},state={'hungry'}),
        'prop':Entity('prop','velvet hat','object','desk',properties={'hat','rabbit_capacity'}|({'portal_hat'} if magic else set()),state={'bound'} if magic else {'open'}),
        'pen':Entity('pen','pen','place','garden',properties={'reachable'}),
        'desk':Entity('desk','desk','place','garden',properties={'reachable'}),
        'bell':Entity('bell','bell','object','garden',properties={'rings'},state={'silent'}),
    }
    return w


def unrelated_brief():
    return dict(schema='event-pool-v1',intent='reveal',setting='garden',roles={'rabbit':'pet','hat':'prop'})


class EventPoolTests(unittest.TestCase):
    def test_short_line_pulls_detailed_fragment_objects_and_mechanics(self):
        a=attach(demo_brief())
        self.assertEqual(a['fragment'],'hat.portal_bound')
        self.assertEqual(len(a['template']['events']),13)
        self.assertEqual(len(a['bindings']),9)
        self.assertEqual(set(demo_brief()['roles']),{'rabbit','hat'})
        self.assertEqual({x['role'] for x in a['audit'] if x['action']=='import' and x['reason']=='fragment dependency'},
                         {'actor','audience','source','stage','food','ribbon','wand'})
        self.assertTrue(any('hat.unbind' in p for p in a['template']['source']['expansion'].values()))

    def test_nested_substitution_and_cycle_and_signature_validation(self):
        root=dict(roles={'magician':{},'spectator':{},'bunny':{},'prop':{}},steps=[dict(fragment='rabbit.reveal',bind={
            'actor':'magician','audience':'spectator','rabbit':'bunny','hat':'prop'})])
        expanded=expand_fragment(root)
        self.assertEqual(expanded[1]['event']['rabbit'],'bunny')
        self.assertEqual(expanded[1]['event']['actor'],'magician')
        cyclic={'loop':dict(params=[],steps=[dict(fragment='loop',bind={})])}
        with self.assertRaisesRegex(ValueError,'recursive'):expand_fragment(dict(roles={},steps=[dict(fragment='loop',bind={})]),fragments=cyclic)
        with self.assertRaisesRegex(ValueError,'limit'):expand_fragment(ROOTS['hat.portal_bound'],limit=2)
        broken=deepcopy(root);broken['steps'][0]['bind'].pop('rabbit')
        with self.assertRaisesRegex(ValueError,'parameter'):expand_fragment(broken)

    def test_existing_rabbit_hat_and_people_rebound_without_source_identity(self):
        w=unrelated_world();before=w.to_dict();row,a=generate(unrelated_brief(),w)
        self.assertEqual(row['status'],'complete');self.assertEqual(w.to_dict(),before)
        self.assertEqual(a['bindings']['rabbit'],'pet');self.assertEqual(a['bindings']['hat'],'prop')
        self.assertEqual(a['bindings']['actor'],'ada');self.assertEqual(a['bindings']['audience'],'teo')
        self.assertNotIn('Merlin',row['story']);self.assertNotIn('June',row['story'])
        self.assertIn('Ada',row['story']);self.assertIn('brown rabbit',row['story'])
        self.assertEqual(row['final_world']['entities']['bell'],before['entities']['bell'])
        self.assertEqual(row['initial_world']['entities']['pet'],before['entities']['pet'])
        self.assertEqual(row['initial_world']['entities']['prop'],before['entities']['prop'])
        self.assertEqual(len([e for e in row['final_world']['entities'].values() if e['kind']=='animal']),1)

    def test_ordinary_hat_gets_stage_mechanism_and_keeps_physics(self):
        w=unrelated_world(False);row,a=generate(unrelated_brief(),w)
        self.assertEqual(a['fragment'],'hat.stage');self.assertEqual(row['status'],'complete')
        self.assertNotIn('portal_hat',row['final_world']['entities']['prop']['properties'])
        self.assertNotIn('can_portal',row['final_world']['entities']['ada']['properties'])
        operations=[t['operation'] for t in row['trace']]
        self.assertLess(operations.index('open_eyes'),operations.index('peek_rabbit'))
        self.assertIn('hide_rabbit',operations);self.assertNotIn('portal_rabbit',operations)
        self.assertNotIn('wand',a['bindings']);self.assertNotIn('ribbon',a['bindings'])

    def test_open_hat_skips_obstacle_and_can_rank_multiple_mechanisms(self):
        brief=demo_brief('ambiguous');cs,rejected=retrieve(brief)
        self.assertEqual({c['fragment'] for c in cs},{'hat.portal_open','hat.stage'})
        self.assertAlmostEqual(sum(c['probability'] for c in cs),1)
        selected={attach(brief,seed=i)['fragment'] for i in range(20)}
        self.assertEqual(selected,{'hat.portal_open','hat.stage'})
        row,forced=generate(brief,fragment='hat.portal_open')
        self.assertAlmostEqual(sum(c['probability'] for c in forced['retrieval']['candidates']),1)
        self.assertNotIn('failed_portal',[x['operation'] for x in row['trace']])
        self.assertNotIn('again',row['story'])

    def test_new_character_can_inherit_source_flavor(self):
        brief=demo_brief();brief['roles']['actor']={'name':'Merlinus'}
        row,a=generate(brief)
        self.assertIn('Merlinus',row['story'])
        self.assertIn('June',row['story'])
        self.assertIn('carrot',row['story'])
        self.assertEqual(next(x['prototype'] for x in a['audit'] if x.get('role')=='actor'),'magic:performer')

    def test_pool_contains_existing_kite_and_library_ports(self):
        cases=[dict(schema='event-pool-v1',intent='fly',setting='meadow',environment=['windy'],roles={'item':{}}),
               dict(schema='event-pool-v1',intent='draw',setting='garden',roles={'item':{}})]
        for brief in cases:
            row,a=generate(brief);self.assertEqual(row['status'],'complete')
            self.assertTrue(a['fragment'].startswith(('kite.','library.')))
        cases[0]['environment']=[]
        with self.assertRaises(Unresolved):attach(cases[0])

    def test_grounded_replay_across_modes_and_seeds(self):
        for mode in ['magic','stage','ambiguous']:
            for seed in range(6):
                row,a=generate(demo_brief(mode),seed=seed)
                self.assertEqual(row['status'],'complete');verify(row,a['template'],driver_class=PoolLines)
                rabbit=row['final_world']['entities'][a['bindings']['rabbit']]
                self.assertIn('revealed',rabbit['state']);self.assertIn('fed',rabbit['state'])
                self.assertNotIn('hidden',rabbit['state']);self.assertNotIn('hungry',rabbit['state'])
                self.assertEqual(rabbit['location'],a['bindings']['stage'])

    def test_static_and_runtime_ablation_of_carriers_and_affordances(self):
        w=unrelated_world();w.entities['prop'].properties.discard('portal_hat')
        before=w.to_dict()
        with self.assertRaises(Unresolved):attach(unrelated_brief(),w)
        self.assertEqual(before,w.to_dict())
        a=attach(demo_brief());w=a['world'];t=a['template'];b=a['bindings']
        w.entities[b['hat']].properties.discard('portal_hat')
        row=replay(w,t,b,driver_class=PoolLines)
        self.assertEqual(row['status'],'blocked');verify(row,t,driver_class=PoolLines)
        self.assertNotIn('revealed',row['final_world']['entities'][b['rabbit']]['state'])

    def test_every_missing_carrier_rejects_commit_atomically(self):
        a=attach(demo_brief());w=a['world'];d=PoolLines(w,a['template'],a['bindings']);count=0
        while not d.complete:
            _,f=d.candidates(w)[0]
            for slot in d.fields[d.events[f.kind]['op']]:
                eid=d.events[f.kind][slot];entity=w.entities.pop(eid);before=w.to_dict();cursors=d.cursors[:]
                with self.assertRaises(ValueError):d.commit(f,'forged')
                self.assertEqual(w.to_dict(),before);self.assertEqual(d.cursors,cursors)
                w.entities[eid]=entity;count+=1
            d.commit(f,'fixture')
        self.assertGreater(count,40)

    def test_unsupported_goal_and_missing_anchors_do_not_pick_random_story(self):
        brief=demo_brief();brief['intent']='turn_into_dragon'
        with self.assertRaises(Unresolved):attach(brief)
        brief=demo_brief();del brief['roles']['rabbit']
        with self.assertRaises(Unresolved):attach(brief)

    def test_missing_recovery_or_reveal_fragment_does_not_get_patched_silently(self):
        roots=deepcopy(ROOTS);roots['hat.portal_bound']['steps'].pop(1)
        with self.assertRaises(Unresolved):attach(demo_brief(),roots=roots)
        fragments=deepcopy(FRAGMENTS);del fragments['rabbit.reveal']
        with self.assertRaisesRegex(ValueError,'unknown fragment'):attach(demo_brief(),fragments=fragments)

    def test_qa_tracks_actual_mechanism_and_bound_entities(self):
        for magic in (False,True):
            row,a=generate(unrelated_brief(),unrelated_world(magic))
            kinds={q['kind'] for q in row['qa']}
            self.assertTrue({'mechanism','outcome'}<=kinds)
            self.assertEqual('cause' in kinds,magic)
            mechanism=next(q['answer'] for q in row['qa'] if q['kind']=='mechanism')
            self.assertEqual('transport' in mechanism,magic)
            self.assertEqual('closed their eyes' in mechanism,not magic)
            for q in row['qa']:
                self.assertTrue(set(q['entity_ids'])<=row['final_world']['entities'].keys())
                self.assertTrue(set(q['event_ids'])<={e['id'] for e in row['final_world']['history']})
                self.assertGreaterEqual(q['answer'].count('.'),2)
                self.assertNotIn('Merlin',q['answer'])

    def test_input_pool_and_world_are_immutable(self):
        brief=demo_brief();before=deepcopy(brief);roots=deepcopy(ROOTS);fragments=deepcopy(FRAGMENTS)
        generate(brief)
        self.assertEqual(brief,before);self.assertEqual(ROOTS,roots);self.assertEqual(FRAGMENTS,fragments)


if __name__=='__main__':unittest.main()
