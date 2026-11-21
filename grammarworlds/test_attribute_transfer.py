"""Semantic transfer is role-based, target-grounded, explicit about ambiguity."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from .attribute_transfer import binding_alternatives, event_attributes, entity_profile
from .event_line_replay import project_source, paper_world, replay, verify, AttachedLines
from .event_pool import generate, retrieve, demo_brief
from .test_event_pool import unrelated_world, unrelated_brief
from .world import Entity


class AttributeTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        graph=json.loads((Path(__file__).parent/'runs/entity_event_lines_20261106/refined/kite.json').read_text())
        ids=[e['id'] for e in graph['events'] if e['kind'] in {'fetch_tape','mend'}]
        cls.template=project_source(graph,'hero',ids)
        cls.bindings=dict(worker='ada',item='book',tool='tape',supply='bench')

    def test_kite_to_book_preserves_repair_not_flight_or_source_identity(self):
        world=paper_world();before=world.to_dict()
        row=replay(world,self.template,self.bindings,seed=7,heads=False)
        verify(row,self.template)
        self.assertEqual(world.to_dict(),before)
        self.assertEqual(row['status'],'complete')
        self.assertNotIn('kite',row['story'])
        self.assertIn('book',row['story'])
        self.assertEqual(row['final_world']['entities']['book']['state'],['repaired'])
        patch=next(t for t in row['trace'] if t['operation']=='patch_paper')
        audit=patch['attribute_transfer']['patch']
        item=next(r for r in audit['roles'] if r['slot']=='item')
        self.assertIn('flyable',item['source_only_properties'])
        self.assertEqual(item['fields']['noun']['target'],'book')
        self.assertEqual(item['fields']['noun']['source'],'kite')
        for attributes in patch['attribute_table'].values():
            self.assertEqual(attributes['event']['name'],'repair paper object')
            self.assertEqual(attributes['event']['roles']['item'],'book')
            self.assertEqual(attributes['event']['roles']['actor'],'ada')
            self.assertEqual(attributes['event']['expected_effects'][0]['add'],['repaired'])
            if attributes.get('entity')=='book':
                self.assertIn('torn',attributes['entity_features']['state'])
                self.assertNotIn('fragile',attributes['entity_features']['state'])
                self.assertNotIn('flyable',attributes['entity_features']['properties'])
        actor=next(r for r in audit['roles'] if r['slot']=='actor')
        self.assertEqual(actor['fields']['pronoun']['target'],'she')

    def test_current_state_is_refreshed_after_imported_fetch(self):
        row=replay(paper_world(),self.template,self.bindings,heads=False)
        fetch,patch=row['trace']
        self.assertEqual(fetch['attribute_transfer']['fetch']['target_role_features']['item']['location'],'bench')
        self.assertEqual(patch['attribute_transfer']['patch']['target_role_features']['tool']['location'],'ada')
        self.assertEqual([t['position']['token'] for t in row['attribute_generation']['tokens']],
                         list(range(len(row['attribute_generation']['tokens']))))

    def test_source_unknown_attributes_and_context_are_not_live_features(self):
        template=deepcopy(self.template)
        profile=template['source']['attribute_sources']['item']['entity']
        profile.update(position={'token':999}, curse='invisible', location='source_castle')
        row=replay(paper_world(),template,self.bindings,heads=False)
        audit=row['trace'][-1]['attribute_transfer']['patch']
        item=next(r for r in audit['roles'] if r['slot']=='item')
        self.assertEqual(item['unknown_source_fields'],['curse','position'])
        self.assertEqual(item['fields']['location']['target'],'ada')
        self.assertTrue(audit['untransferred_context'])
        for attributes in row['trace'][-1]['attribute_table'].values():
            if attributes.get('entity_features'):
                self.assertNotIn('curse',attributes['entity_features'])
                self.assertNotIn('position',attributes['entity_features'])
            self.assertNotIn('source_castle',json.dumps(attributes))

    def test_target_number_is_used_when_rephrasing(self):
        world=paper_world();world.entities['book'].number='plural';world.entities['book'].pronoun='they'
        row=replay(world,self.template,self.bindings,heads=False)
        self.assertIn('books',row['story'])
        bundles=[a for event in row['trace'] for a in event['attribute_table'].values() if a.get('entity')=='book']
        self.assertTrue(bundles)
        self.assertTrue(all(a['entity_features']['number']=='plural' for a in bundles))
        self.assertTrue(all(a['entity_features']['pronoun']=='they' for a in bundles))

    def test_source_role_identity_can_split_when_target_roles_are_explicit(self):
        world=paper_world()
        template=dict(schema='attached-event-lines-v1',roles={'giver':'person','receiver':'person','item':'object'},
            events={'pass':dict(op='transfer',actor='giver',recipient='receiver',item='item')},
            lines=[dict(entity=role,steps=['pass']) for role in ('giver','receiver','item')],
            source={'attribute_sources':{role:dict(origin='same_source_person',entity=entity_profile(world.entities['ada']))
                                         for role in ('giver','receiver')}})
        driver=AttachedLines(world,template,dict(giver='ada',receiver='omar',item='book'))
        attrs,audit=event_attributes(driver,'pass')
        self.assertEqual(attrs['roles'],dict(actor='ada',recipient='omar',item='book'))
        roles={r['slot']:r for r in audit['roles']}
        self.assertEqual(roles['actor']['origin'],roles['recipient']['origin'])
        self.assertEqual(roles['recipient']['fields']['noun']['target'],'Omar')
        with self.assertRaisesRegex(ValueError,'cannot alias'):
            AttachedLines(world,template,dict(giver='ada',receiver='ada',item='book'))

    def test_missing_target_affordances_are_not_imported_from_source(self):
        world=paper_world();world.entities['ada'].properties.remove('can_patch_paper')
        row=replay(world,self.template,self.bindings)
        self.assertEqual(row['status'],'blocked')
        self.assertIn('actor lacks paper-patching capability',row['blocked']['patch'])
        self.assertNotIn('can_patch_paper',row['final_world']['entities']['ada']['properties'])
        self.assertIn('torn',row['final_world']['entities']['book']['state'])

    def test_pool_recomputes_all_roles_even_when_frame_is_coarse(self):
        world=unrelated_world();before=world.to_dict()
        row,attached=generate(unrelated_brief(),world,seed=7,heads=False)
        self.assertEqual(row['status'],'complete');self.assertEqual(world.to_dict(),before)
        reveal=next(t for t in row['trace'] if t['operation']=='lift_rabbit')
        for a in reveal['attribute_table'].values():
            self.assertEqual(a['event']['roles']['rabbit'],'pet')
            self.assertEqual(a['event']['roles']['hat'],'prop')
            self.assertEqual(a['event']['roles']['audience'],'teo')
            self.assertEqual(a['event']['roles']['actor'],'ada')
            self.assertNotIn('Merlin',json.dumps(a))
        actor=next(r for r in reveal['attribute_transfer'][reveal['line_event']]['roles'] if r['slot']=='actor')
        self.assertEqual(actor['fields']['noun']['source'],'Merlin')
        self.assertEqual(actor['fields']['noun']['target'],'Ada')

    def test_weighted_ambiguous_bindings_stay_separate_and_normalized(self):
        world=unrelated_world()
        world.entities['omar']=Entity('omar','Omar','person','garden',pronoun='he',properties={'can_hold','can_portal'})
        brief=unrelated_brief();brief['roles']['actor']={'candidates':[
            {'entity':'ada','weight':3}, {'entity':'omar','weight':1}]}
        before=world.to_dict();prior=deepcopy(brief)
        candidates,rejected=retrieve(brief,world)
        self.assertEqual(len(candidates),2)
        probs={c['bindings']['actor']:c['probability'] for c in candidates}
        self.assertEqual(probs,dict(ada=.75,omar=.25))
        self.assertEqual(world.to_dict(),before);self.assertEqual(brief,prior)
        for seed in (0,7):
            row,a=generate(brief,world,seed=seed,heads=False)
            self.assertEqual(row['status'],'complete')
            self.assertEqual(len(a['retrieval']['candidates']),2)
            self.assertTrue(all(c['bindings']['actor'] in {'ada','omar'} for c in a['retrieval']['candidates']))

    def test_incompatible_alternative_is_rejected_without_capability_grant(self):
        world=unrelated_world();world.entities['omar']=Entity('omar','Omar','person','garden',properties={'can_hold'})
        brief=unrelated_brief();brief['roles']['actor']={'candidates':[{'entity':'ada'}, {'entity':'omar'}]}
        candidates,rejected=retrieve(brief,world)
        self.assertEqual(len(candidates),1);self.assertEqual(candidates[0]['probability'],1.)
        self.assertEqual(candidates[0]['bindings']['actor'],'ada')
        self.assertTrue(any(r.get('binding_choices',{}).get('actor',{}).get('entity')=='omar' for r in rejected))
        self.assertNotIn('can_portal',world.entities['omar'].properties)

    def test_binding_candidate_validation(self):
        for options in ([],[{'entity':'ada','weight':0}],[{'entity':'ada','weight':float('nan')}],
                        [{'entity':'ada'},{'entity':'ada'}]):
            brief=unrelated_brief();brief['roles']['actor']={'candidates':options}
            with self.assertRaises(ValueError):binding_alternatives(brief)
        brief=unrelated_brief();brief['roles']['actor']={'candidates':[{'entity':str(i)} for i in range(33)]}
        with self.assertRaisesRegex(ValueError,'too many'):binding_alternatives(brief)

    def test_surface_only_ablation_preserves_prose_without_heads(self):
        for seed in range(4):
            row=replay(paper_world(),self.template,self.bindings,seed,heads=False)
            old=replay(paper_world(),self.template,self.bindings,seed,heads=False,predict_attributes=False)
            self.assertEqual(row['story'],old['story']);self.assertEqual(row['final_world'],old['final_world'])
            self.assertNotIn('attribute_generation',old)
            for step in row['trace']:
                for p in step['word_trace']:
                    self.assertAlmostEqual(sum(c['probability'] for c in p['annotated_choices']),1.)
                    self.assertAlmostEqual(sum(c['probability'] for c in p['selected_attributes']),1.)


if __name__=='__main__':unittest.main()
