"""Entity projections preserve physical identity and shared-event constraints."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import unittest

from .grammar import expand
from .storytelling.continuations import ExpandedLanguage
from .storytelling.event_lines import factorize, local_slice
from .storytelling.runtime import SCENARIOS, generate, setup


class EventLineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {s: generate(s,3000,continuations='expanded',symbolic_heads=True) for s in SCENARIOS}
        cls.graphs = {s:factorize(r) for s,r in cls.rows.items()}

    def test_all_worlds_have_consistent_entity_projections(self):
        for scenario,row in self.rows.items():
            before=deepcopy(row)
            graph=factorize(row)
            self.assertEqual(row,before)
            index={e['id']:e for e in graph['events']}
            for entity,record in graph['entities'].items():
                self.assertEqual(record['final'],row['final_world']['entities'][entity])
                for step in record['line']:
                    event=index[step['event_id']]
                    self.assertEqual(step['tags'],event['entity_tags'][entity])
                    self.assertEqual(step['own_effects'],event['effects'].get(entity,{}))
                    for peer in step['peers']:
                        matching=next(x for x in graph['entities'][peer]['line'] if x['event_id']==event['id'])
                        self.assertIn(entity,matching['peers'])
            for event in graph['events']:
                self.assertFalse(event['guard_reads_complete'])
                for entity in event['effects']:
                    self.assertIn('changed',event['entity_tags'][entity])

    def test_handoff_is_one_event_on_three_entity_lines(self):
        graph=self.graphs['library']
        event=next(e for e in graph['events'] if e['kind']=='checkout')
        self.assertIn('source_holder',event['entity_tags']['helper'])
        self.assertIn('destination_holder',event['entity_tags']['friend'])
        self.assertIn('moved',event['entity_tags']['book'])
        for entity in ('helper','friend','book'):
            self.assertTrue(any(e['event_id']==event['id'] for e in graph['entities'][entity]['line']))
        self.assertEqual(event['effects']['book']['location'],dict(before='helper',after='friend'))

    def test_cup_to_bowl_keeps_entity_identity_and_name_change(self):
        for seed in range(20):
            row=generate('pottery',seed)
            if any(e['frame']['kind']=='remake' for e in row['final_world']['history']): break
        else: self.fail('No remake branch in fixed seed range')
        graph=factorize(row)
        event=next(e for e in graph['events'] if e['kind']=='remake')
        self.assertEqual(event['effects']['cup']['noun'],dict(before='cup',after='bowl'))
        self.assertIn('renamed',event['entity_tags']['cup'])
        self.assertNotIn('bowl',graph['entities'])

    def test_effects_find_participants_omitted_by_coarse_frame(self):
        event=next(e for e in self.graphs['key']['events'] if e['kind'].startswith('unlock_'))
        self.assertEqual(event['frame']['actor'],'hero')
        self.assertIn('moved',event['entity_tags']['helper'])
        self.assertNotIn('frame.actor',event['entity_tags']['helper'])
        self.assertIn('helper',event['participants'])

    def test_grammar_subjects_recover_coactors_without_guessing_possessors(self):
        reserve=next(e for e in self.graphs['library']['events'] if e['kind']=='reserve_atlas')
        self.assertIn('grammatical_subject',reserve['entity_tags']['helper'])
        search=next(e for e in self.graphs['library']['events'] if e['kind']=='failed_search')
        for entity in ('hero','friend'):
            self.assertIn('grammatical_subject',search['entity_tags'][entity])
        pack,w=setup('pottery',7)
        g=ExpandedLanguage(w,lexicon=pack.LEXICON)
        sentence=g.s(g.possess(g.ref('grandpa'),g.cn('hand')),g.be('stiff'))
        for _,_,labels in expand(sentence.node):
            self.assertNotIn('clause.subject:grandpa',labels)

    def test_both_speech_forms_keep_explicit_speaker_listener_pair(self):
        pack,w=setup('music',7)
        g=ExpandedLanguage(w,lexicon=pack.LEXICON)
        alternatives=list(expand(g.offer('partner',g.v('help',g.ref('hero')),listener='hero')))
        self.assertTrue(any('told' in tokens for tokens,_,_ in alternatives))
        self.assertTrue(any('said' in tokens for tokens,_,_ in alternatives))
        for _,_,labels in alternatives:
            self.assertIn('dialogue.listener:partner:hero',labels)
        event=next(e for e in self.graphs['music']['events'] if e['kind']=='decline')
        self.assertIn(dict(speaker='partner',listener='hero'),event['dialogue'])
        self.assertIn('listener',event['entity_tags']['hero'])

    def test_local_slice_exposes_joins_and_global_dependencies(self):
        graph=self.graphs['library']
        line=[e for e in graph['entities']['book']['line'] if e['participation']=='participant']
        index=next(i for i,e in enumerate(line) if e['kind']=='checkout')
        part=local_slice(graph,'book',index,index+1)
        self.assertEqual(part['entry_state']['location'],'helper')
        self.assertEqual(part['exit_state']['location'],'friend')
        self.assertTrue(part['joins'])
        self.assertTrue(part['incoming_dependencies'])
        self.assertTrue(part['outgoing_dependencies'])
        self.assertTrue(part['requires_guard_revalidation'])
        self.assertFalse(part['independently_executable'])
        before=deepcopy(graph)
        part['events'][0]['tags'].append('invented')
        self.assertEqual(graph,before)

    def test_invalid_trace_rejected(self):
        row=deepcopy(self.rows['key']);row['story']+=' invented ending'
        with self.assertRaises(ValueError): factorize(row)
        row=deepcopy(self.rows['key']);row['final_world']['entities']['hero']['noun']='Someone else'
        with self.assertRaises(ValueError): factorize(row)

    def test_listener_annotations_preserve_previous_generation(self):
        archive=Path(__file__).parent/'runs/shared_core_iterations_20261105/final_merged/sample_traces.jsonl.gz'
        compared=0
        with gzip.open(archive,'rt') as source:
            for old in map(json.loads,source):
                if old['profile']!='expanded_manual': continue
                # This pin isolates listener annotations against the archived
                # word-only sampler; joint prediction has its own parity tests.
                new=generate(old['scenario'],3000,continuations='expanded',
                             symbolic_heads=True,predict_attributes=False)
                self.assertEqual(new['story'],old['story'])
                self.assertEqual(new['final_world'],old['final_world'])
                for a,b in zip(new['trace'],old['trace'],strict=True):
                    for x,y in zip(a['word_trace'],b['word_trace'],strict=True):
                        self.assertEqual(x['selected'],y['selected'])
                        self.assertEqual([(c['word'],c['probability']) for c in x['choices']],
                                         [(c['word'],c['probability']) for c in y['choices']])
                compared+=1
        self.assertEqual(compared,7)


if __name__=='__main__': unittest.main()
