"""Portable local lines bind physical roles, preserve joins and fail explicitly."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import unittest

from .event_line_replay import AttachedLines, cooperative, paper_world, project_source, replay, verify, world_from_dict
from .underdefined_probe import initial_world, generate


class LineReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=Path(__file__).parent/'runs/entity_event_lines_20261106/refined'
        cls.graph=json.loads((folder/'kite.json').read_text())
        cls.ids=[e['id'] for e in cls.graph['events'] if e['kind'] in {'fetch_tape','mend'}]
        cls.template=project_source(cls.graph,'hero',cls.ids)
        cls.bindings=dict(worker='ada',item='book',tool='tape',supply='bench')

    def test_port_uses_effect_object_not_coarse_fetch_patient(self):
        source=next(e for e in self.graph['events'] if e['kind']=='fetch_tape')
        self.assertEqual(source['frame']['patient'],'target')
        self.assertEqual(self.template['source']['role_origins']['tool'],'tool')
        self.assertEqual(self.template['events']['fetch']['item'],'tool')
        self.assertTrue(self.template['source']['untransferred_context'])

    def test_solo_replay_changes_only_book_and_tape(self):
        w=paper_world();before=w.to_dict()
        row=replay(w,self.template,self.bindings)
        verify(row,self.template)
        self.assertEqual(w.to_dict(),before)
        self.assertEqual(row['status'],'complete')
        after=row['final_world']
        self.assertEqual(after['entities']['book']['state'],['repaired'])
        self.assertEqual(after['entities']['tape']['location'],'ada')
        self.assertEqual(after['flags'],before['flags'])
        for entity in ('ada','omar','bench'):
            self.assertEqual(after['entities'][entity],before['entities'][entity])

    def test_joint_events_commit_once_and_allow_independent_prefix_orders(self):
        template=cooperative(self.template);bindings=dict(self.bindings,worker='omar',owner='ada')
        orders=set()
        for seed in range(12):
            row=replay(paper_world(),template,bindings,seed)
            verify(row,template);self.assertEqual(row['status'],'complete')
            history=row['final_world']['history'];order=tuple(e['line_event'] for e in history);orders.add(order)
            self.assertEqual(len(order),6);self.assertEqual(len(set(order)),6)
            for sid in ('hand_in','hand_out'):
                e=next(e for e in history if e['line_event']==sid)
                self.assertEqual(set(e['attached_entities']),{'ada','omar','book'})
            self.assertEqual(row['final_world']['entities']['book']['location'],'ada')
            self.assertEqual(row['cursors'],[len(x['steps']) for x in template['lines']])
        self.assertGreater(len(orders),1)

    def test_wrong_holder_and_undeclared_capabilities_block(self):
        row=replay(paper_world(),self.template,dict(self.bindings,worker='omar'))
        self.assertEqual(row['status'],'blocked')
        self.assertEqual(len(row['trace']),1)
        self.assertIn('actor is not holding the item',row['blocked']['patch'])
        self.assertEqual(row['final_world']['entities']['book']['state'],['torn'])
        row=replay(initial_world(),self.template,self.bindings)
        self.assertEqual(row['status'],'blocked')
        self.assertIn('item lacks declared paper material',row['blocked']['patch'])
        self.assertIn('actor lacks paper-patching capability',row['blocked']['patch'])

    def test_blocked_commit_does_not_advance_or_mutate(self):
        w=paper_world();driver=AttachedLines(w,self.template,self.bindings)
        driver.commit(driver.frames['fetch'],'fetch')
        w.entities['book'].location='omar'
        before=w.to_dict();positions=driver.cursors[:]
        with self.assertRaises(ValueError): driver.commit(driver.frames['patch'],'forged repair')
        self.assertEqual(w.to_dict(),before);self.assertEqual(driver.cursors,positions)

    def test_reordered_line_does_not_skip_missing_prerequisite(self):
        template=deepcopy(self.template)
        for line in template['lines']: line['steps'].reverse()
        w=paper_world();row=replay(w,template,self.bindings)
        self.assertEqual(row['status'],'blocked');self.assertEqual(row['story'],'')
        self.assertEqual(row['final_world'],w.to_dict())
        self.assertIn('actor is not holding the repair tool',row['blocked']['patch'])

    def test_invalid_bindings_unknown_operations_cycles_and_missing_joins(self):
        with self.assertRaises(ValueError): AttachedLines(paper_world(),self.template,dict(self.bindings,worker='book'))
        with self.assertRaises(ValueError): AttachedLines(paper_world(),self.template,dict(self.bindings,tool='absent'))
        bad=deepcopy(self.template);bad['events']['patch']['op']='magically_repair'
        with self.assertRaises(ValueError): AttachedLines(paper_world(),bad,self.bindings)
        bad=deepcopy(self.template);bad['lines'][0]['steps'].reverse()
        with self.assertRaisesRegex(ValueError,'cycle'): AttachedLines(paper_world(),bad,self.bindings)
        bad=cooperative(self.template);bad['lines'][0]['steps'].remove('hand_out')
        with self.assertRaisesRegex(ValueError,'shared event missing'):
            AttachedLines(paper_world(),bad,dict(self.bindings,worker='omar',owner='ada'))
        w=paper_world();w.entities['fetch']=deepcopy(w.entities['omar']);w.entities['fetch'].id='fetch'
        bad=deepcopy(self.template);bad['roles']['unrelated']='person'
        bad['lines'].append(dict(entity='unrelated',steps=['fetch']))
        with self.assertRaisesRegex(ValueError,'unrelated'):
            AttachedLines(w,bad,dict(self.bindings,unrelated='fetch'))

    def test_arbitrary_source_diff_is_not_executable(self):
        first=self.graph['entities']['hero']['line'][0]['event_id']
        with self.assertRaisesRegex(ValueError,'no portable operation'): project_source(self.graph,'hero',[first])
        bad=deepcopy(self.graph)
        mend=next(e for e in bad['events'] if e['kind']=='mend')
        mend['effects']['target']['state']['after'].append('flying')
        with self.assertRaisesRegex(ValueError,'not the reviewed'): project_source(bad,'hero',self.ids)

    def test_entity_ids_and_person_names_are_not_hardcoded(self):
        w=paper_world();mapping={e:'entity_'+str(i) for i,e in enumerate(w.entities)}
        entities={}
        for old,e in w.entities.items():
            e.id=mapping[old];e.location=mapping.get(e.location,e.location);entities[e.id]=e
        w.entities=entities
        for key in ('hero','helper','target','tool'):setattr(w,key,mapping[getattr(w,key)])
        w.entities[w.hero].noun='Mira';w.entities[w.helper].noun='Tao'
        row=replay(w,self.template,{r:mapping[e] for r,e in self.bindings.items()})
        self.assertEqual(row['status'],'complete');self.assertIn('Mira',row['story'])
        self.assertNotIn('Ada',row['story']);self.assertIn('bench',row['story'])

    def test_no_line_mode_keeps_underdefined_baseline(self):
        path=Path(__file__).parent/'runs/underdefined_core_20261106/traces.jsonl.gz'
        with gzip.open(path,'rt') as f:old=next(json.loads(x) for x in f if json.loads(x)['heads'])
        new=generate(old['seed'])
        self.assertEqual(new['story'],old['story']);self.assertEqual(new['final_world'],old['final_world'])

    def test_supplied_line_need_not_use_imported_role_names_or_have_a_repair(self):
        template=dict(schema='attached-event-lines-v1',roles={'speaker':'person','listener':'person'},
            events={'greeting':dict(op='offer',actor='speaker',listener='listener')},
            lines=[dict(entity='speaker',steps=['greeting']),dict(entity='listener',steps=['greeting'])])
        row=replay(initial_world(),template,dict(speaker='omar',listener='ada'))
        self.assertEqual(row['status'],'complete');self.assertEqual(len(row['trace']),1)
        self.assertEqual(row['final_world']['entities']['book']['state'],['torn'])

    def test_attachment_after_existing_history_and_ended_world(self):
        first=deepcopy(self.template)
        first['roles']={k:v for k,v in first['roles'].items() if k!='item'}
        first['events'].pop('patch')
        first['lines']=[dict(entity='worker',steps=['fetch']),dict(entity='tool',steps=['fetch'])]
        prefix=replay(paper_world(),first,{k:v for k,v in self.bindings.items() if k!='item'})
        w=world_from_dict(prefix['final_world'],allow_history=True)
        second=deepcopy(self.template)
        second['roles'].pop('supply');second['events'].pop('fetch')
        second['lines']=[line for line in second['lines'] if line['entity'] in second['roles']]
        for line in second['lines']:line['steps']=['patch']
        suffix=replay(w,second,{k:v for k,v in self.bindings.items() if k!='supply'})
        verify(suffix,second);self.assertEqual(suffix['status'],'complete')
        self.assertEqual(suffix['final_world']['history'][0],prefix['final_world']['history'][0])
        w=paper_world();w.flags.add('ended')
        blocked=replay(w,self.template,self.bindings)
        self.assertEqual(blocked['final_world'],w.to_dict())
        self.assertEqual(blocked['status'],'blocked')


if __name__=='__main__': unittest.main()
