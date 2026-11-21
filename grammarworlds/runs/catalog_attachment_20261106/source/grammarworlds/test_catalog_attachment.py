"""Catalog assembly, physical dependencies, and existing replay compatibility."""
from copy import deepcopy
import unittest

from .catalog_attachment import (CatalogLines, Unresolved, attach, bare_world,
                                 catalog, example_line)
from .event_line_replay import replay, verify
from .world import Entity


class CatalogAttachmentTests(unittest.TestCase):
    def test_three_sources_and_dependency_closure(self):
        bare=bare_world();before=bare.to_dict();w,t,b,audit=attach(example_line(),bare)
        self.assertEqual(before,bare.to_dict())
        imports=[a for a in audit if a['action']=='import']
        self.assertEqual({a['source']['world'] for a in imports},{'kite','library','music'})
        self.assertEqual(len(imports),10)
        self.assertEqual(len(w.entities),12)
        self.assertEqual({a['prototype'] for a in imports if a['dependency']},
                         {'kite:tool','kite:string','library:paper','library:pencil','library:atlas','music:drum'})
        self.assertEqual(w.entities[b['visitor']].noun,'Mino')
        self.assertEqual(w.entities[b['musician']].noun,'Niah')
        self.assertEqual(w.entities[b['musician']].state,set()) # no source duet goal
        self.assertEqual(w.flags,set());self.assertEqual(w.history,[])
        self.assertNotIn('music:teacher',{a['prototype'] for a in imports})

    def test_samples_execute_and_verify_physical_changes(self):
        w,t,b,_=attach(example_line());before=w.to_dict();orders=set()
        for seed in range(8):
            for heads in (False,True):
                row=replay(w,t,b,seed,heads=heads,driver_class=CatalogLines)
                verify(row,t,driver_class=CatalogLines)
                self.assertEqual(row['status'],'complete');self.assertEqual(len(row['trace']),7)
                e=row['final_world']['entities']
                self.assertTrue({'repaired','flying'}<=set(e[b['kite']]['state']))
                self.assertNotIn('torn',e[b['kite']]['state'])
                self.assertIn('moon_drawing',e[b['_visitor_paper']]['state'])
                self.assertIn('sounded',e[b['_musician_instrument']]['state'])
                orders.add(tuple(x['line_event'] for x in row['trace']))
        self.assertGreater(len(orders),1)
        self.assertEqual(before,w.to_dict())

    def test_no_catalog_and_no_dependencies_fail_explicitly(self):
        with self.assertRaisesRegex(Unresolved,'prototype'): attach(example_line(),records={})
        with self.assertRaisesRegex(Unresolved,'missing dependency'): attach(example_line(),dependencies=False)
        records=catalog();del records['kite:tool']
        with self.assertRaisesRegex(Unresolved,'prototype'): attach(example_line(),records=records)

    def test_unsupported_physics_is_not_invented(self):
        line=example_line();line['events'][3]['op']='summon_rabbit'
        with self.assertRaisesRegex(Unresolved,'reviewed physics'): attach(line)
        records=catalog();records['kite:target']['entity'].properties.remove('physics:kite')
        with self.assertRaises(Unresolved): attach(example_line(),records=records)

    def test_unknown_and_ambiguous_names_do_not_become_wizards(self):
        line=example_line();line['mentions']['repairer']['name']='Merlinus'
        with self.assertRaises(Unresolved): attach(line)
        records=catalog();records['another:mina']=deepcopy(records['library:hero'])
        with self.assertRaisesRegex(Unresolved,'ambiguous'): attach(example_line(),records=records)

    def test_compatible_local_repairer_is_reused_without_overwrite(self):
        w=bare_world();w.entities['local_sam']=Entity('local_sam','Sammy','person','meadow',
            properties={'can_hold','can_repair','can_help'},memes={'Care':.15},state={'sleepy'})
        before=w.to_dict();resolved,t,b,a=attach(example_line(),w)
        self.assertEqual(b['repairer'],'local_sam')
        self.assertEqual(resolved.entities['local_sam'],w.entities['local_sam'])
        self.assertEqual(before,w.to_dict())
        self.assertEqual(replay(resolved,t,b,driver_class=CatalogLines)['status'],'complete')

    def test_conflicting_existing_context_and_explicit_binding_rejected(self):
        w=bare_world();w.entities['meadow']=Entity('meadow','meadow','place','',properties=set())
        before=w.to_dict()
        with self.assertRaises(Unresolved): attach(example_line(),w)
        self.assertEqual(w.to_dict(),before)
        line=example_line();line['mentions']['repairer']['entity']='missing'
        with self.assertRaises(Unresolved): attach(line)

    def test_missing_wind_blocks_without_fabricating_weather(self):
        line=example_line();line['context']['properties']=[]
        w,t,b,_=attach(line);row=replay(w,t,b,driver_class=CatalogLines)
        self.assertEqual(row['status'],'blocked');self.assertIn('wind is absent',row['blocked']['flight'])
        self.assertIn('repaired',row['final_world']['entities'][b['kite']]['state'])
        self.assertNotIn('flying',row['final_world']['entities'][b['kite']]['state'])

    def test_guard_mutations_leave_rejected_events_unchanged(self):
        w,t,b,_=attach(example_line());d=CatalogLines(w,t,b);checks=0
        while not d.complete:
            _,f=d.candidates(w)[0]
            for role in d.fields[d.events[f.kind]['op']]:
                victim=d.events[f.kind][role];entity=w.entities.pop(victim);before=w.to_dict();cursors=d.cursors[:]
                with self.assertRaises(ValueError): d.commit(f,'forged')
                self.assertEqual(w.to_dict(),before);self.assertEqual(d.cursors,cursors)
                w.entities[victim]=entity;checks+=1
            d.commit(f,'fixture')
        self.assertGreater(checks,15)

    def test_wrong_tool_and_fragile_kite_do_not_pass_as_working_physics(self):
        w,t,b,_=attach(example_line());w.entities[b['_kite_repair_tool']].properties.clear()
        row=replay(w,t,b,driver_class=CatalogLines)
        self.assertEqual(row['status'],'blocked');self.assertNotIn('repaired',row['final_world']['entities'][b['kite']]['state'])
        w,t,b,_=attach(example_line());w.entities[b['kite']].state.add('fragile')
        row=replay(w,t,b,driver_class=CatalogLines)
        self.assertEqual(row['status'],'blocked');self.assertIn('kite is not flight-ready',row['blocked']['flight'])

    def test_draw_only_line_is_independent_of_demo_cast_and_kite(self):
        line={'schema':'catalog-line-v1','context':{'setting':'meadow'},'mentions':{'artist':{'name':'Mina'}},
              'events':[dict(id='draw',op='sketch_moon',actor='artist')]}
        w,t,b,a=attach(line)
        self.assertEqual({x['source']['world'] for x in a if x['action']=='import'},{'library'})
        self.assertEqual(replay(w,t,b,driver_class=CatalogLines)['status'],'complete')

    def test_donor_worlds_remain_unchanged_and_physics_is_exported_explicitly(self):
        records=catalog();before=deepcopy(records);attach(example_line(),records=records)
        self.assertEqual(records,before)
        self.assertEqual(records['kite:target']['packages'],['kite:mend','kite:test_flight'])
        self.assertIn('can_drum',records['music:hero']['additions'])
        self.assertIn('moon_picture',records['library:atlas']['entity'].state)


if __name__=='__main__': unittest.main()
