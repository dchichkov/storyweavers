from copy import deepcopy
from dataclasses import replace
import json
import unittest

import algebra as a
import compact_prose as cp
from runtime import solve, transition, realize, StoryError
from prose import render_book


def world():
    return dict(title='The borrowed lens',
        entities={
            'ada':dict(name='Ada',kind='child',state={'memes.Curiosity':2}),
            'ben':dict(name='Ben',kind='child',state={'memes.Care':1}),
            'box':dict(name='box',kind='prop',state={'latch':'left','open':False}),
            'lens':dict(name='lens',kind='prop',state={'owner':'ben'}),
        },
        compose={
            'news':dict(op='DiscoverAndShare',args=['ada','ben','box.latch']),
            'loan':dict(op='Lend',args=['ben','ada','lens'],when={'ben.knows.box.latch':'left','ben.memes.Care':['ge',1]}),
            'open':dict(op='Act',actors=['ada'],when={'lens.owner':'ada','ada.knows.box.latch':'left'},set={'box.open':True}),
            'return':dict(op='Return',args=['ada','ben','lens'],when={'box.open':True}),
        },
        goal={'box.open':True,'lens.owner':'ben','lens.loaned_by':None},
        outcomes=['box.open','lens.owner'])


class AlgebraTests(unittest.TestCase):
    def test_composed_discovery_loan_and_return_share_causal_state(self):
        doc=world(); before=deepcopy(doc)
        trace=solve(a.build(doc),11)
        self.assertEqual([e['scene'] for e in trace['events']],
                         ['news.notice','news.share','loan','open','return'])
        self.assertEqual(trace['final']['lens.owner'],'ben')
        self.assertIsNone(trace['final']['lens.loaned_by'])
        self.assertIn(2,trace['events'][2]['causes'])
        self.assertIn(3,trace['events'][3]['causes'])
        self.assertEqual(doc,before)

    def test_missing_component_or_meme_blocks_composition(self):
        spec=a.build(world())
        with self.assertRaisesRegex(StoryError,'No valid composition'):
            solve(replace(spec,scenes=tuple(s for s in spec.scenes if s.id!='news.share')))
        doc=world();doc['entities']['ben']['state']['memes.Care']=0
        with self.assertRaisesRegex(StoryError,'No valid composition'):solve(a.build(doc))

    def test_addition_is_associative_and_not_execution_concatenation(self):
        p=a.compose({'a':dict(op='Observe',args=['ada','box.latch'])})
        q=a.compose({'b':dict(op='Observe',args=['ben','box.latch'])})
        z=a.Pattern()
        self.assertEqual((p+q)+z,p+(q+z));self.assertEqual(p+z,p)
        # Both independent discoveries can come first despite the expression order.
        spec=a.build(world())
        initial=dict(spec.initial,**{'ada.knows.box.latch':None,'ben.knows.box.latch':None})
        spec=replace(spec,initial=initial,scenes=(p+q).scenes,
                     goal=(a.Condition('ada.knows.box.latch','eq','left'),a.Condition('ben.knows.box.latch','eq','left')),
                     outcome_keys=(),prune=False)
        paths={tuple(e['scene'] for e in solve(spec,s)['events']) for s in range(30)}
        self.assertEqual(paths,{('a','b'),('b','a')})

    def test_division_preserves_effects_and_guards_without_mutating_definition(self):
        p=a.compose({'a':dict(op='Observe',args=['ada','box.latch'])})
        q=p/4
        self.assertEqual(q.scenes[0].effects,p.scenes[0].effects)
        self.assertEqual(q.scenes[0].requires,p.scenes[0].requires)
        self.assertEqual(q.scenes[0].weight,.25);self.assertEqual(p.scenes[0].weight,1)
        for invalid in (0,-1,float('inf'),True):
            with self.assertRaises(StoryError):p/invalid

    def test_roles_rebind_nested_composites_without_changing_definition(self):
        definition={'roles':['a','b','f'],'body':{'news':dict(op='DiscoverAndShare',args=['$a','$b','$f'])}}
        kernel=a.Kernel.define(definition['roles'],definition['body'])
        definition['body'].clear()
        left=kernel.bind(['ada','ben','box.latch'],'first',a.SHARED_KERNELS)
        right=kernel.bind(['ben','ada','box.latch'],'second',a.SHARED_KERNELS)
        self.assertEqual(left.scenes[0].actors,('ada',))
        self.assertEqual(right.scenes[0].actors,('ben',))
        self.assertEqual(len((left+right).scenes),4)
        with self.assertRaisesRegex(StoryError,'duplicate'):left+left

    def test_recursion_and_unknown_roles_fail_closed(self):
        k=a.Kernel.define(['a'],{'again':dict(op='Loop',args=['$a'])})
        with self.assertRaisesRegex(StoryError,'Recursive'):
            a.compose({'x':dict(op='Loop',args=['ada'])},{'Loop':k})
        k=a.Kernel.define(['a'],{'look':dict(op='Observe',args=['$who','box.latch'])})
        with self.assertRaisesRegex(StoryError,'Unbound'):k.bind(['ada'],'x',{})

    def test_explicit_stale_belief_survives_auto_declaration_and_tell(self):
        doc=world();doc['entities']['ada']['state']['knows.box.latch']='right'
        spec=a.build(doc);s=next(s for s in spec.scenes if s.id=='news.share')
        after=transition(spec.initial,s)
        self.assertEqual(after['ben.knows.box.latch'],'right')
        self.assertEqual(after['box.latch'],'left')

    def test_return_cannot_repay_the_wrong_lender(self):
        doc=world();doc['entities']['third']=dict(name='Third',kind='child')
        doc['compose']['return']['args']=['ada','third','lens']
        with self.assertRaisesRegex(StoryError,'No valid composition'):solve(a.build(doc))

    def test_independent_variations_and_explicit_cases(self):
        doc=world();doc['vary']={'curiosity':[{'ada.memes.Curiosity':1},{'ada.memes.Curiosity':2}],
                               'care':[{'ben.memes.Care':1},{'ben.memes.Care':2}]}
        combinations=a.configurations(doc)
        self.assertEqual(len(combinations),4)
        states={tuple(a.build(doc,choices=c).initial[k] for k in ('ada.memes.Curiosity','ben.memes.Care')) for c in combinations}
        self.assertEqual(states,{(1,1),(1,2),(2,1),(2,2)})
        a.build(doc).initial['box.open']=True
        self.assertFalse(a.build(doc).initial['box.open'])
        doc['vary']['care'][0]['ada.memes.Curiosity']=0
        with self.assertRaisesRegex(StoryError,'overwrite'):a.build(doc)

    def test_carriers_keys_and_typos_are_not_silently_invented(self):
        for key,value in [('actors',['ghost']),('set',{'abstract.done':True}),('piviotal',True)]:
            doc=world();doc['compose']['open'][key]=value
            with self.assertRaises(StoryError):a.build(doc)
        doc=world();doc['entities']['lens']['state']['owner']='nobody'
        with self.assertRaisesRegex(StoryError,'physical carrier'):a.build(doc)

    def test_named_patch_updates_only_its_component(self):
        doc=world();replacement=deepcopy(doc['compose']['open']);replacement['summary']='Ada opened the box'
        patched=a.patch_world(doc,{'edits':[dict(section='compose',id='open',value=replacement)]})
        self.assertNotIn('summary',doc['compose']['open'])
        self.assertEqual(patched['compose']['news'],doc['compose']['news'])
        solve(a.build(patched))


class ProseScaffoldTests(unittest.TestCase):
    def test_endings_share_outcome_and_drop_incidental_facts(self):
        doc=world();doc['vary']={'curiosity':[{'ada.memes.Curiosity':1},{'ada.memes.Curiosity':2}]}
        specs=[a.build(doc,choices={'curiosity':i}) for i in range(2)]
        traces=[solve(s,0) for s in specs]
        sk=cp.scaffold(traces,specs)
        ends=[v for v in sk['slots'].values() if v['section']=='endings']
        self.assertEqual(len(ends),1)
        self.assertNotIn('ada.memes.Curiosity',ends[0]['evidence']['state'])
        self.assertTrue(ends[0]['evidence']['state']['box.open'])
        guards={c['key']:c['value'] for c in ends[0]['when']}
        self.assertEqual(guards,ends[0]['evidence']['state'])
        self.assertNotIn('ada.memes.Curiosity',guards)

    def example(self):
        spec=a.build(world()); traces=[solve(spec,s) for s in range(4)]
        sk=cp.scaffold(traces,[spec])
        texts={'cards':{k:['A small warm sentence.']*v['variants'] for k,v in sk['slots'].items()}}
        return traces,sk,texts

    def test_compiled_catalog_preserves_trace_and_covers_events(self):
        traces,sk,texts=self.example();book=cp.catalog(sk,texts)
        result=realize(traces[0],lambda run,rng:render_book(run,rng,book),1)
        self.assertEqual(result['trace'],traces[0])
        self.assertEqual({i for p in result['paragraphs'] for i in p['event_ids']},set(range(1,6)))

    def test_named_card_patch_survives_order_changes_and_rejects_stale_edits(self):
        _,sk,texts=self.example();key=next(iter(texts['cards']))
        patch={'edits':[dict(id=key,old=texts['cards'][key],new=['A fresh warm sentence.']*len(texts['cards'][key]))]}
        reordered=deepcopy(texts);reordered['cards']=dict(reversed(list(reordered['cards'].items())))
        changed=cp.patch_texts(sk,reordered,patch)
        self.assertEqual(changed['cards'][key],patch['edits'][0]['new'])
        with self.assertRaisesRegex(StoryError,'Stale'):cp.patch_texts(sk,changed,patch)
        self.assertEqual(texts['cards'][key],patch['edits'][0]['old'])

    def test_changed_state_never_uses_an_unconditional_observation_card(self):
        traces,sk,texts=self.example();book=cp.catalog(sk,texts)
        row=deepcopy(traces[0]);row['events'][0]['after']['ada.knows.box.latch']='right'
        with self.assertRaisesRegex(StoryError,'No eligible prose card'):
            realize(row,lambda run,rng:render_book(run,rng,book),0)


if __name__=='__main__':unittest.main()
