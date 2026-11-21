"""Optional beat words carry authored actions without executing proposals."""
from copy import deepcopy
import unittest

from .grammar import Node,seq,choice,expand
from .beat_generation import _ref,_line
from .beat_grammar import annotate_beat,annotate_phrase
from .storytelling.runtime import setup
from .storytelling.semantic_rules import metadata


def terminals(node):
    """Inspect leaf annotations directly; the runtime hook is a later round."""
    if node.kind=='text':return [(word,metadata(node)) for word in node.children]
    return [item for child in node.children for item in terminals(child)]


class BeatGrammarTests(unittest.TestCase):
    def setUp(self):self.pack,self.world=setup('museum',7)

    def test_runtime_emits_the_authored_action_and_joint_distribution(self):
        from .storytelling.runtime import generate,replay
        from .story_memory import annotate
        found=set()
        for source,seed in [('pottery',7),('museum',42),('camp',43),('snow',43)]:
            row=generate(source,seed,beat_budget=6,continuations='expanded')
            replay(row);annotate(row)
            for trace in row['trace']:
                for prediction in trace['word_trace']:
                    self.assertAlmostEqual(sum(c['probability'] for c in prediction['annotated_choices']),1.)
                for attrs in trace['attribute_table'].values():
                    if attrs.get('beat',{}).get('scope')!='pre_event_candidate':continue
                    self.assertNotEqual(attrs['pos'],'X')
                    if attrs.get('action'):
                        found.add(attrs['action']['lemma'])
                        self.assertNotEqual(attrs['action_scope'],'finite_clause')
                    if attrs.get('action_scope') in {'requested_action','proposed_action','embedded_proposal'}:
                        self.assertTrue(attrs['hypothetical'])
                        self.assertTrue(attrs['quoted'])
        self.assertTrue({'hesitate','look','say','help','try','be'}<=found)

    def candidate(self,kind,**overrides):
        return dict(dict(id=kind,experiencer='hero',object='shadow',listener='helper',
            speech_act=kind if kind in {'asking','committing','suggesting'} else None,
            detail=None,preceding_event=3),**overrides)

    def assert_surface_preserved(self,original,revised):
        self.assertEqual([(w,p) for w,p,_ in expand(original)],[(w,p) for w,p,_ in expand(revised)])

    def test_reaction_and_inspection_have_own_typed_actions(self):
        for tense,hesitate,look in [('past','hesitated.','looked closely at'),('present','hesitates.','looks closely at')]:
            for kind,node in [('reaction',seq('beat.reaction',_ref(self.world,'hero'),hesitate)),
                              ('inspection',seq('beat.inspection',_ref(self.world,'hero'),look,_ref(self.world,'shadow'),'.'))]:
                before=deepcopy(self.world.to_dict())
                typed=annotate_beat(node,self.candidate(kind),self.world,tense)
                self.assert_surface_preserved(node,typed)
                attrs=terminals(typed)
                self.assertNotIn('X',{a['authored_pos'] for _,a in attrs})
                self.assertEqual(attrs[0][1]['clause']['subject']['entity'],'hero')
                self.assertEqual({a['action']['lemma'] for _,a in attrs},{'hesitate' if kind=='reaction' else 'look'})
                self.assertTrue(all(not a['hypothetical'] for _,a in attrs))
                self.assertEqual(self.world.to_dict(),before)
                if kind=='inspection':
                    self.assertEqual(next(a for w,a in attrs if w=='closely')['authored_pos'],'ADV')
                    self.assertEqual(next(a for w,a in attrs if w=='at')['authored_pos'],'ADP')
                    self.assertEqual(attrs[0][1]['action']['arguments']['oblique']['entity'],'shadow')

    def test_request_binds_listener_as_requested_actor_and_speaker_as_beneficiary(self):
        node=_line(self.world,'hero','helper','Could you help me with',_ref(self.world,'shadow'),'?')
        typed=annotate_beat(node,self.candidate('asking'),self.world)
        self.assert_surface_preserved(node,typed)
        attrs=dict(terminals(typed))
        self.assertEqual(attrs['said']['action']['lemma'],'say')
        self.assertFalse(attrs['said']['hypothetical'])
        self.assertEqual(attrs['you']['entity'],'helper')
        self.assertEqual(attrs['me']['entity'],'hero')
        self.assertEqual(attrs['help']['clause']['subject']['entity'],'helper')
        self.assertEqual(attrs['help']['action']['arguments']['object']['entity'],'hero')
        self.assertEqual(attrs['help']['action']['arguments']['oblique']['entity'],'shadow')
        self.assertTrue(attrs['help']['hypothetical'])
        self.assertEqual(attrs['Could']['authored_pos'],'AUX')
        self.assertEqual(attrs['with']['authored_pos'],'ADP')

    def test_commitment_uses_spoken_tool_not_native_patient_and_stays_hypothetical(self):
        node=_line(self.world,'hero','helper','I will try',_ref(self.world,'torch'),'.')
        typed=annotate_beat(node,self.candidate('committing',planned_event='controlled_trial'),self.world)
        self.assert_surface_preserved(node,typed)
        attrs=dict(terminals(typed))
        self.assertEqual(attrs['I']['entity'],'hero')
        self.assertEqual(attrs['will']['authored_pos'],'AUX')
        self.assertEqual(attrs['try']['action']['arguments']['object']['entity'],'torch')
        self.assertEqual(attrs['try']['action']['modality'],'intention')
        self.assertTrue(attrs['try']['hypothetical'])
        self.assertEqual(attrs['try']['action_scope'],'proposed_action')
        self.assertNotIn('controlled_trial',str(attrs['try']['action']))

    def test_suggestion_separates_let_clause_from_shared_proposed_action(self):
        node=_line(self.world,'hero','helper','Let us try',_ref(self.world,'torch'),'.')
        typed=annotate_beat(node,self.candidate('suggesting'),self.world)
        attrs=dict(terminals(typed))
        self.assertEqual(attrs['Let']['action']['lemma'],'let')
        self.assertEqual(attrs['try']['action']['lemma'],'try')
        self.assertEqual(attrs['try']['action_scope'],'embedded_proposal')
        self.assertEqual({m['entity'] for m in attrs['try']['clause']['subject']['members']},{'hero','helper'})
        self.assertEqual(attrs['us']['syntax_role'],'object')
        self.assertNotIn('entity',attrs['us'])
        self.assertTrue(attrs['Let']['hypothetical'] and attrs['try']['hypothetical'])

    def test_known_echo_keeps_setup_action_distinct_from_current_result(self):
        _,w=setup('repair',7)
        node=seq('beat.echo','The wheel that had locked now turned freely.')
        candidate=self.candidate('echo:repair:locked_wheel',object='wheel',detail='repair:locked_wheel',setup_event=3)
        typed=annotate_beat(node,candidate,w)
        self.assert_surface_preserved(node,typed)
        attrs=dict(terminals(typed))
        self.assertEqual(attrs['locked']['action']['lemma'],'lock')
        self.assertEqual(attrs['locked']['action_scope'],'detail_setup')
        self.assertEqual(attrs['locked']['evidence_event'],3)
        self.assertEqual(attrs['turned']['action']['lemma'],'turn')
        self.assertEqual(attrs['turned']['action_scope'],'detail_recollection')
        self.assertNotIn('X',{a['authored_pos'] for _,a in terminals(typed)})

    def test_generic_phrase_contract_and_unknown_echo_are_explicit(self):
        node=seq('beat.echo',_ref(self.world,'shadow'),'remained small.')
        candidate=self.candidate('echo:museum:new_detail',detail='museum:new_detail')
        unknown=annotate_beat(node,candidate,self.world)
        attrs=dict(terminals(unknown))
        self.assertEqual(attrs['remained']['authored_pos'],'X')
        self.assertNotIn('action',attrs['remained'])
        self.assertEqual(attrs['shadow']['entity'],'shadow')
        specifications=[dict(token=w,pos='PUNCT' if w=='.' else 'DET' if w=='the' else 'VERB' if w=='remained' else 'ADJ' if w=='small' else 'NOUN')
                        for w in next(expand(node))[0]]
        candidate['detail_realization']=dict(terminal_attributes=specifications,action_scope='detail_recollection',
            action=dict(lemma='remain',modality='state',arguments={}))
        typed=annotate_beat(node,candidate,self.world)
        self.assert_surface_preserved(node,typed)
        self.assertEqual(dict(terminals(typed))['remained']['action']['lemma'],'remain')
        with self.assertRaises(ValueError):annotate_phrase(node,[dict(token='wrong',pos='NOUN')])
        with self.assertRaises(ValueError):annotate_phrase(choice('alternatives',node,node),specifications)
        candidate['detail_realization']['terminal_attributes'][1]['entity']='unembedded'
        with self.assertRaises(ValueError):annotate_beat(node,candidate,self.world)

    def test_probability_branch_weights_and_input_metadata_are_unchanged(self):
        node=choice('reaction.styles',seq('beat.reaction',_ref(self.world,'hero'),'hesitated.'),
                    seq('beat.reaction',_ref(self.world,'hero'),'hesitates.'),weights=(3,1))
        saved=deepcopy(node);candidate=self.candidate('reaction');before=deepcopy(candidate)
        typed=annotate_beat(node,candidate,self.world)
        self.assert_surface_preserved(node,typed)
        self.assertEqual(node,saved);self.assertEqual(candidate,before)
        self.assertEqual(typed.weights,(3,1))
        with self.assertRaises(ValueError):annotate_beat(node,self.candidate('reaction',experiencer='missing'),self.world)

    def test_all_authored_generic_callbacks_have_pos_and_current_state_predicates(self):
        from .beat_annotations import DETAILS
        count=0
        for scenario,details in DETAILS.items():
            for detail in details:
                callback=detail.get('callback')
                if not callback:continue
                count+=1;_,w=setup(scenario,7)
                for tense in ('past','present'):
                    with self.subTest(scenario=scenario,tense=tense):
                        node=seq('beat.echo',_ref(w,detail['entity']),callback[tense])
                        candidate=dict(id='echo:'+scenario+':'+detail['name'],experiencer=w.hero,object=detail['entity'],
                            listener=None,detail=scenario+':'+detail['name'],detail_callback=callback)
                        typed=annotate_beat(node,candidate,w,tense)
                        self.assert_surface_preserved(node,typed)
                        attrs=terminals(typed)
                        self.assertNotIn('X',{a['authored_pos'] for _,a in attrs})
                        self.assertEqual(attrs[0][1]['clause']['subject']['entity'],detail['entity'])
                        self.assertEqual([a['authored_pos'] for _,a in attrs][-len(callback[tense+'_pos']):],callback[tense+'_pos'])
                        if callback['predicate']=='be_safe_to_wear':
                            wear=next(a for word,a in attrs if word=='wear')
                            self.assertTrue(wear['hypothetical'])
                            self.assertEqual(wear['action']['lemma'],'wear')
                            self.assertEqual(wear['action_scope'],'embedded_possibility')
        self.assertEqual(count,10)


if __name__=='__main__':unittest.main()
