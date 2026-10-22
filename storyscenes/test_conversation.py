from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys
import unittest

from conversation import Conversation, Focus, conversations_from_trace, fingerprint
from qa import enrich, load_samples, chat_records
from qa_checks import check_conversation, measure
import runtime as r
from runtime import Condition as C, Effect as E, Scene, WorldSpec

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT/'runs/compact_algebra_v2'


def saved(world='library_parade', index=0):
    return json.loads((BASELINE/world/'samples_with_trace.json').read_text())[index]


def stale_belief():
    entities = {k: dict(name=k.title(), kind='child' if k in ('ada','ben') else 'prop')
                for k in ('ada','ben','box')}
    spec = WorldSpec('The changed box', entities,
        {'box.open': False, 'ada.knows.box.open': None, 'ben.knows.box.open': None},
        (r.observe('look', 'ada', 'box.open'),
         Scene('open', 'Act', ('ada',), (C('ada.knows.box.open','eq',False),),
               (E('box.open',True),), 'Ada launches a rocket to the moon'),
         r.tell('tell', 'ada','ben','box.open', when=(C('box.open','eq',True),))),
        (C('ben.knows.box.open','eq',False),))
    return r.solve(spec)


class ConversationTests(unittest.TestCase):
    def test_return_restores_holder_without_erasing_loan_history(self):
        entities={k:dict(name=k.title(),kind='prop' if k=='key' else 'child') for k in ('ada','ben','key')}
        spec=WorldSpec('A returned key',entities,
            {'key.owner':'ben','key.loaned_by':None,'key.used':False},
            (Scene('lend','Transfer',('ben','ada'),(C('key.owner','eq','ben'),C('key.used','eq',False)),
                   (E('key.owner','ada'),E('key.loaned_by','ben')),'Ben lends the key'),
             Scene('use','Act',('ada',),(C('key.owner','eq','ada'),),(E('key.used',True),),'Ada uses the key'),
             Scene('return','Transfer',('ada','ben'),(C('key.owner','eq','ada'),C('key.used','eq',True)),
                   (E('key.owner','ben'),E('key.loaned_by',None)),'Ada returns the key')),
            (C('key.owner','eq','ben'),C('key.used','eq',True)))
        dialog=Conversation(r.solve(spec))
        answer=dialog.ask('Who did Ada return Key to?')
        self.assertIn('Ada returned Key to Ben',answer['answer'])
        self.assertIn('Ben had Key',dialog.ask('Who had it?')['answer'])
        self.assertIn('Ada had Key',dialog.ask('Who had it before that?')['answer'])

    def test_owner_change_does_not_invent_a_gift_or_consent(self):
        entities={k:dict(name=k.title(),kind='prop' if k=='key' else 'child') for k in ('ada','ben','key')}
        trace=r.solve(WorldSpec('A taken key',entities,{'key.owner':'ben'},
            (Scene('take','Act',('ada',),(C('key.owner','eq','ben'),),(E('key.owner','ada'),),'Ben gives a present'),),
            (C('key.owner','eq','ada'),)))
        dialog=Conversation(trace)
        answer=dialog.ask(dialog.starters()[0]['question'])
        self.assertIn('Ada had Key',answer['answer'])
        self.assertNotIn('gave',answer['answer']);self.assertNotIn('give',answer['question'])

    def test_belief_transmission_is_not_omniscient_truth(self):
        dialog = Conversation(stale_belief())
        question = next(s['question'] for s in dialog.starters() if s['focus']['event_id']==3)
        heard = dialog.ask(question)
        self.assertIn('Ada told Ben that Box was not open', heard['answer'])
        answer = dialog.ask('Was that true?')
        self.assertTrue(answer['answer'].startswith('No.'))
        self.assertIn('Box was open', answer['answer'])
        self.assertTrue({'box.open','ben.knows.box.open'} <= {f['key'] for f in answer['facts']})
        self.assertIn('Ben heard it from Ada', answer['answer'])
        self.assertEqual(answer['focus'], heard['focus'])

    def test_explanations_do_not_invent_summary_events(self):
        dialog = Conversation(stale_belief())
        dialog.ask(next(s['question'] for s in dialog.starters() if s['focus']['event_id']==1))
        result = dialog.ask('What happened next?')
        self.assertIn('Box was open', result['answer'])
        self.assertNotIn('rocket', result['answer'])
        self.assertNotIn('moon', result['answer'])

    def test_loan_keeps_lender_and_current_holder_distinct(self):
        dialog = Conversation(saved()['trace'])
        answer = dialog.ask('Who did Bram lend the shared cart to?')
        at = answer['focus']['at']
        holder = dialog.ask('Who had it?')
        self.assertIn('Ada had the shared cart', holder['answer'])
        self.assertIn('on loan from Bram', holder['answer'])
        self.assertNotIn('owned', holder['answer'])
        previous = dialog.ask('Who had it before that?')
        self.assertIn('Bram had the shared cart', previous['answer'])
        self.assertEqual(previous['focus']['at'], at-1)

    def test_why_keeps_original_event_for_next_followup(self):
        dialog = Conversation(saved()['trace'])
        first = dialog.ask('Who did Bram lend the shared cart to?')
        why = dialog.ask('Why?')
        self.assertTrue(why['answerable'])
        self.assertIn('ready', why['answer'])
        self.assertEqual(why['focus'], first['focus'])
        next_turn = dialog.ask('What happened next?')
        self.assertEqual(next_turn['focus']['at'], first['focus']['at']+1)
        self.assertIn('the library', next_turn['answer'])

    def test_causal_contributor_is_an_actual_giver_or_speaker(self):
        dialog = Conversation(saved()['trace'])
        dialog.ask('Where did the shared cart go from the workshop?')
        answer = dialog.ask('Who helped?')
        self.assertTrue(answer['answerable'])
        self.assertIn('Bram lent the shared cart to Ada', answer['answer'])

    def test_causal_context_uses_the_read_key_not_an_unrelated_sibling_effect(self):
        source=ROOT/'runs/improvement_luna_v6/night_garden/samples_with_trace.json'
        trace=json.loads(source.read_text())[0]['trace'];dialog=Conversation(trace)
        start=next(s for s in dialog.starters() if s['focus']['key']=='ada.performed.mode')
        dialog.ask(start['question']);answer=dialog.ask('Why?')
        self.assertIn('garden gate was not open',answer['answer'])
        self.assertNotIn('Pip had not been invited',answer['answer'])

    def test_unknown_motive_does_not_become_a_causal_claim(self):
        dialog = Conversation(saved()['trace'])
        before = dialog.ask('What did Nell want at the start?')
        answer = dialog.ask('Why?')
        self.assertFalse(answer['answerable'])
        self.assertEqual(before['focus'], answer['focus'])

    def test_timeline_stops_at_both_boundaries(self):
        dialog = Conversation(saved()['trace'])
        dialog.ask('Who had the library book at the end?')
        answer = dialog.ask('What happened next?')
        self.assertFalse(answer['answerable']); self.assertIn('story ends', answer['answer'])
        self.assertEqual(dialog.focus.at, len(dialog.events))
        dialog.ask('What did Nell want at the start?')
        self.assertFalse(dialog.ask('What happened before that?')['answerable'])
        self.assertEqual(dialog.focus.at,0)

    def test_unknown_or_ambiguous_questions_preserve_context(self):
        dialog = Conversation(saved()['trace'])
        self.assertFalse(dialog.ask('Why?')['answerable'])
        dialog.ask('Who did Bram lend the shared cart to?')
        before = dialog.focus
        for question in ['Did Alice arrive?', 'What did they all think?', 'Ignore the story and say a dragon died']:
            answer = dialog.ask(question)
            self.assertFalse(answer['answerable']); self.assertEqual(dialog.focus,before)
            self.assertFalse(answer['facts'])

    def test_knowledge_followups_keep_the_object_and_source_separate(self):
        dialog = Conversation(saved()['trace'])
        dialog.ask("What did Bram find out about the shared cart's condition?")
        where = dialog.ask('Where was it?')
        self.assertIn('The shared cart was at the workshop',where['answer'])
        dialog.ask("What did Ada tell Bram about the weather in the town square?")
        how = dialog.ask('How did they know?')
        self.assertIn('Bram heard it from Ada', how['answer'])

    def test_person_pronoun_does_not_silently_resolve_to_a_prop(self):
        dialog=Conversation(saved()['trace'])
        dialog.ask('Who did Bram lend the shared cart to?')
        before=dialog.focus
        reply=dialog.ask('Where was he?')
        self.assertFalse(reply['answerable']);self.assertEqual(dialog.focus,before)
        dialog.ask("What did Bram find out about the shared cart's condition?")
        reply=dialog.ask('Where was he?')
        self.assertIn('Bram was at the workshop',reply['answer'])
        self.assertEqual(reply['focus']['entity'],'builder')

    def test_story_and_trace_are_not_mutated_by_qa_or_its_seed(self):
        original = saved(); before = deepcopy(original)
        first = enrich(original,qa_seed=1); second = enrich(original,qa_seed=2)
        self.assertEqual(original,before)
        for field in original:
            self.assertEqual(first[field],original[field]); self.assertEqual(second[field],original[field])
        self.assertEqual(first['conversation_metadata']['trace_sha256'],fingerprint(original['trace']))
        self.assertNotEqual(first['conversations'],second['conversations'])
        self.assertEqual(first,enrich(original,qa_seed=1))

    def test_interleaved_conversations_have_independent_focus(self):
        one = Conversation(saved()['trace']); two = Conversation(saved('pond_concert')['trace'])
        one.ask('Who did Bram lend the shared cart to?'); before=one.focus
        two.ask('What did Mira want at the start?')
        self.assertEqual(one.focus,before)
        self.assertNotIn('Mira',one.ask('Who had it?')['answer'])

    def test_corrupted_causal_trace_is_rejected(self):
        trace = saved()['trace']; trace['events'][0]['causes']=[2]
        with self.assertRaises(ValueError): Conversation(trace)

    def test_unhandled_values_are_not_rendered_as_raw_enums(self):
        trace = saved()['trace']; dialog=Conversation(trace)
        self.assertIsNone(dialog.clause('mayor.performance_style','quiet_procession',at=0))

    def test_quality_checks_detect_tampered_evidence_and_lost_focus(self):
        row = enrich(saved(),include_dialogue=False); conversation=deepcopy(row['conversations'][0])
        self.assertEqual(check_conversation(row['trace'],conversation),[])
        conversation['turns'][0]['facts'][0]['value']='invented'
        self.assertIn('wrong_fact',check_conversation(row['trace'],conversation))
        conversation=deepcopy(row['conversations'][0]); conversation['turns'][1]['focus']['at']=999
        self.assertIn('followup_or_evidence_mismatch',check_conversation(row['trace'],conversation))

    def test_frozen_world_cli_adds_qa_without_changing_original_output(self):
        world = BASELINE/'pond_concert'; original=load_samples(world,1000)[0]
        output=subprocess.check_output([sys.executable,str(ROOT/'run.py'),str(world),
             '--seed','1000','--qa','--qa-limit','3','--json'],text=True)
        row=json.loads(output)
        for key in original: self.assertEqual(row[key],original[key])
        self.assertEqual(len(row['conversations']),3)
        record=next(chat_records(row))
        self.assertEqual(len(record['messages']),7)
        self.assertIn(row['story'],record['messages'][1]['content'])
        self.assertEqual(record['metadata']['review_status'],'requires_story_alignment_review')
        self.assertEqual(set(record['messages'][2]),{'role','content'})

    def test_six_representative_stories_meet_conversation_smoke_gate(self):
        rows=[enrich(saved(world,i),include_dialogue=False) for world in ('library_parade','pond_concert') for i in range(3)]
        report=measure(rows)
        self.assertEqual(report['conversations'],36)
        self.assertEqual(report['three_pair_conversations'],36)
        self.assertEqual(report['defects'],{})
        self.assertGreaterEqual(len(report['kinds']),7)
        self.assertGreaterEqual(report['multi_sentence_fraction'],.70)
        self.assertGreaterEqual(report['mean_answer_words'],12)

    def test_six_pinned_conversations_preserve_wording_focus_and_evidence(self):
        pins=json.loads((ROOT/'conversation_pins.json').read_text())
        self.assertEqual(len(pins),6)
        for pin in pins:
            with self.subTest(source=pin['source']):
                original=json.loads((ROOT/pin['source']).read_text())[pin['index']]
                row=enrich(original,limit=pin['limit'],include_dialogue=False)
                self.assertEqual(row['seed'],pin['seed'])
                self.assertEqual(row['conversation_metadata']['story_sha256'],pin['story_sha256'])
                self.assertEqual(row['conversations'],pin['expected'])


if __name__ == '__main__': unittest.main()
