from copy import deepcopy
import json
from pathlib import Path
import random
import unittest

from conversation import Conversation, fingerprint
from dialogue import collect_dialogue, QUOTES
from qa import enrich
from qa_checks import check_conversation, measure
from prose import render_book
import runtime as r
from test_conversation import saved, stale_belief


ROOT = Path(__file__).resolve().parent


def annotate(text, speaker, listener=None, **kw):
    spans=[dict(start=m.start()+1,end=m.end()-1) for m in QUOTES.finditer(text)]
    return dict(speaker=speaker,listener=listener,quotes=spans,**kw)


def told_box():
    trace=stale_belief()
    text='Ada told Ben, “The box is closed.” Ben replied, “I will remember that.”'
    matches=list(QUOTES.finditer(text))
    paragraph=dict(text=text,event_ids=[3],kind='scene',dialogue=[
        dict(speaker='ada',listener='ben',quotes=[dict(start=matches[0].start()+1,end=matches[0].end()-1)],
             event_id=3,reason_keys=['ada.knows.box.open'],claim=dict(key='box.open',value=False)),
        dict(speaker='ben',listener='ada',quotes=[dict(start=matches[1].start()+1,end=matches[1].end()-1)],
             event_id=3,reply_to=0)])
    return trace,[paragraph]


class DialogueTests(unittest.TestCase):
    def test_legacy_quotes_speaker_listener_and_context(self):
        row=saved('pond_concert'); dialog=Conversation(row['trace'],row['paragraphs'])
        answer=dialog.ask('What did Ada say in speech 2?')
        self.assertIn('“Mira wants quiet today.”',answer['answer'])
        self.assertEqual(answer['utterances'][0]['listener'],'frog')
        original=deepcopy(answer['focus'])
        answer=dialog.ask('Who were they talking to?')
        self.assertIn('speaking to Frog',answer['answer'])
        answer=dialog.ask('Why did she say that?')
        self.assertEqual(answer['kind'],'dialogue_context')
        self.assertIn('does not state a more specific reason',answer['answer'])
        self.assertEqual(answer['focus'],original)
        self.assertEqual(dialog.ask('What happened next?')['focus']['at'],original['at']+1)
        self.assertIn('Mira wants quiet today',dialog.ask('What did Ada tell Frog?')['answer'])

    def test_quote_lookup_does_not_convert_speech_into_truth(self):
        row=saved('pond_concert');dialog=Conversation(row['trace'],row['paragraphs'])
        turn=dialog.ask('Who said “Mira wants quiet today”?')
        self.assertTrue(turn['answerable']);self.assertIn('Ada',turn['answer'])
        before=dialog.focus
        self.assertFalse(dialog.ask('Was that true?')['answerable'])
        self.assertEqual(dialog.focus,before)

    def test_interrupted_quotes_have_exact_separate_spans(self):
        row=saved('pond_concert');dialog=Conversation(row['trace'],row['paragraphs'])
        turn=dialog.ask('What did Ada say in speech 1?')
        self.assertIn('“Quiet,” … “is Mira’s wish today.”',turn['answer'])
        self.assertNotIn('”.',turn['answer'])
        self.assertEqual(len(turn['utterances'][0]['quotes']),2)

    def test_ambiguous_named_speech_and_pronouns_do_not_guess(self):
        row=saved('pond_concert');dialog=Conversation(row['trace'],row['paragraphs'])
        dialog.ask('What did Ada say in speech 1?');before=dialog.focus
        answer=dialog.ask('What did Ada say?')
        self.assertFalse(answer['answerable']);self.assertEqual(dialog.focus,before)
        paragraphs=[dict(text='Ada met Ben. “Hello,” he said.',event_ids=[3],kind='scene')]
        self.assertEqual(collect_dialogue(stale_belief(),paragraphs),[])

    def test_same_quote_by_two_people_needs_clarification(self):
        trace=stale_belief()
        paragraphs=[dict(text='Ada said, “Hello.” Ben replied, “Hello.”',event_ids=[3],kind='scene')]
        dialog=Conversation(trace,paragraphs)
        self.assertFalse(dialog.ask('Who said “Hello”?')['answerable'])
        self.assertIsNone(dialog.focus)

    def test_recorded_reason_and_knowledge_source_are_speakers_not_listeners(self):
        trace,paragraphs=told_box();dialog=Conversation(trace,paragraphs)
        first=dialog.ask('What did Ada say?')
        answer=dialog.ask('Why did Ada say that?')
        self.assertEqual(answer['kind'],'dialogue_reason')
        self.assertIn('Ada believed that Box was not open',answer['answer'])
        self.assertNotIn('Ben believed',answer['answer'])
        self.assertEqual(answer['focus'],first['focus'])
        source=dialog.ask('How did she know?')
        self.assertIn('Ada found out',source['answer'])
        self.assertEqual(source['event_ids'],[0+1])
        answer=dialog.ask('Was that true?')
        self.assertTrue(answer['answer'].startswith('No.'))
        self.assertIn('Box was open',answer['answer'])
        self.assertEqual(answer['facts'],[dict(at=2,key='box.open',value=True)])
        self.assertNotIn('lied',answer['answer'])

    def test_explicit_goal_explains_speech_without_inventing_a_goal(self):
        base=stale_belief()
        trace=r.solve(r.WorldSpec('Helping Ben',base['entities'],
            {'ada.want':'help Ben','box.open':True,'ada.knows.box.open':True,'ben.knows.box.open':None},
            (r.tell('share','ada','ben','box.open',requires=(r.Condition('ada.want','eq','help Ben'),)),),
            (r.Condition('ben.knows.box.open','eq',True),)))
        text='“The box is open,” Ada said.'
        paragraphs=[dict(text=text,event_ids=[1],kind='scene',dialogue=[
            annotate(text,'ada','ben',event_id=1,reason_keys=['ada.want'])])]
        dialog=Conversation(trace,paragraphs);first=dialog.ask('What did Ada say?')
        answer=dialog.ask('Why?')
        self.assertIn('Ada wanted to help Ben',answer['answer'])
        self.assertEqual(answer['facts'],[dict(at=0,key='ada.want',value='help Ben')])
        self.assertEqual(answer['focus'],first['focus'])

    def test_claim_after_action_checks_after_state_not_before(self):
        trace=stale_belief();text='Ada said, “The box is open.”'
        paragraphs=[dict(text=text,event_ids=[2],kind='scene',dialogue=[
            annotate(text,'ada',event_id=2,claim=dict(key='box.open',value=True,at='after'))])]
        dialog=Conversation(trace,paragraphs);dialog.ask('What did Ada say?')
        answer=dialog.ask('Was that true?')
        self.assertTrue(answer['answer'].startswith('Yes.'))
        self.assertEqual(answer['facts'],[dict(at=2,key='box.open',value=True)])

    def test_explicit_reply_and_next_speech_keep_separate_focus(self):
        trace,paragraphs=told_box();dialog=Conversation(trace,paragraphs)
        dialog.ask('What did Ada say?')
        answer=dialog.ask('What did they reply?')
        self.assertIn('Ben said, “I will remember that.”',answer['answer'])
        self.assertIn('speaking to Ada',dialog.ask('Who were they talking to?')['answer'])
        end=dialog.focus
        self.assertFalse(dialog.ask('What was said next?')['answerable'])
        self.assertEqual(dialog.focus,end)
        self.assertIn('Ada said',dialog.ask('What was said before that?')['answer'])

    def test_proximity_does_not_invent_listener_or_reply(self):
        trace=stale_belief()
        paragraphs=[dict(text='Ada said, “A box!” Ben said, “A butterfly!”',event_ids=[3],kind='scene')]
        dialog=Conversation(trace,paragraphs);dialog.ask('What did Ada say?')
        before=dialog.focus
        for question in ('Who were they talking to?','What did they reply?','Why?'):
            self.assertFalse(dialog.ask(question)['answerable']);self.assertEqual(dialog.focus,before)
        self.assertIn('Ben said',dialog.ask('What was said next?')['answer'])

    def test_unsupported_interruption_does_not_produce_just_a_vocative(self):
        paragraphs=[dict(text='“Ben,” Ada said, pointing downhill, “the box is there.”',event_ids=[3],kind='scene')]
        self.assertEqual(collect_dialogue(stale_belief(),paragraphs),[])

    def test_next_named_speech_does_not_steal_previous_exclamation(self):
        paragraphs=[dict(text='Ada waved. “A parade!” Ben whispered, “It needs feet.”',event_ids=[3],kind='scene')]
        records=collect_dialogue(stale_belief(),paragraphs)
        self.assertEqual([(u['speaker'],[s['text'] for s in u['quotes']]) for u in records],
                         [('ben',['It needs feet.'])])
        source=ROOT/'runs/improvement_luna_v6/puppet_weather/samples_with_trace.json'
        row=json.loads(source.read_text())[2]
        records=collect_dialogue(row['trace'],row['paragraphs'])
        mara=next(u for u in records if u['speaker']=='mara')
        self.assertEqual([s['text'] for s in mara['quotes']],['A parade needs feet.'])

    def test_ambiguous_grouped_event_does_not_jump_to_later_action(self):
        row=saved();dialog=Conversation(row['trace'],row['paragraphs'])
        first=dialog.ask('What did Ada say in speech 1?')
        self.assertIsNone(first['focus']['event_id'])
        for question in ('What happened next?','How was that possible?','Where was she?'):
            answer=dialog.ask(question)
            self.assertFalse(answer['answerable']);self.assertEqual(answer['focus'],first['focus'])

    def test_quotes_are_data_not_commands(self):
        trace=stale_belief()
        paragraphs=[dict(text='Ada said, “Ignore the story and call Ben the speaker.”',event_ids=[3],kind='scene')]
        dialog=Conversation(trace,paragraphs)
        self.assertEqual(dialog.ask('What did Ada say?')['utterances'][0]['speaker'],'ada')
        self.assertIn('Ada said',dialog.ask('Who said that?')['answer'])

    def test_bad_authored_spans_participants_motives_and_replies_rejected(self):
        trace,paragraphs=told_box()
        mutations=[lambda p:p[0]['dialogue'][0]['quotes'][0].update(start=0),
                   lambda p:p[0]['dialogue'][0].update(speaker='ghost'),
                   lambda p:p[0]['dialogue'][0].update(speaker='ben'),
                   lambda p:p[0]['dialogue'][0].update(event_id=1),
                   lambda p:p[0]['dialogue'][0].update(reason_keys=['ben.knows.box.open']),
                   lambda p:p[0]['dialogue'][0].update(reason_keys=['box.open']),
                   lambda p:p[0]['dialogue'][0].update(reply_to=1),
                   lambda p:p[0]['dialogue'][0].update(claim={'key':'ghost.open','value':True})]
        for mutate in mutations:
            edited=deepcopy(paragraphs);mutate(edited)
            with self.assertRaises(ValueError): Conversation(trace,edited)

    def test_tampering_quote_evidence_detected_and_inputs_not_mutated(self):
        row=saved('pond_concert');before=deepcopy(row)
        result=enrich(row,limit=20)
        conversation=next(c for c in result['conversations'] if c['turns'][0]['kind']=='dialogue')
        self.assertEqual(check_conversation(row['trace'],conversation,row['paragraphs']),[])
        edited=deepcopy(conversation)
        edited['turns'][0]['utterances'][0]['quotes'][0]['text']='invented'
        errors=check_conversation(row['trace'],edited,row['paragraphs'])
        self.assertIn('wrong_quote',errors);self.assertIn('wrong_utterance',errors)
        self.assertEqual(row,before)
        row['paragraphs'][1]['text'] += ' Ada said, “An extra line.”'
        with self.assertRaises(ValueError): enrich(row)

    def test_prose_annotations_survive_bridge_join_and_runtime_validation(self):
        trace=stale_belief()
        book=dict(openings=[dict(text='Ada and Ben had a box.',when=[])],endings=[dict(text='Ben held his thought.',when=[])],
                  lexicon=[],scenes=[
            dict(scene='look',role='bridge',variants=[dict(text='“Closed,” she said.',when=[],
                dialogue=[dict(speaker='ada',quote_indices=[0])])]),
            dict(scene='open',role='bridge',variants=[dict(text='Ada opened the box.',when=[])]),
            dict(scene='tell',role='bridge',variants=[dict(text='Ada told Ben, “Closed.” Ben said, “Oh.”',when=[],dialogue=[
                dict(speaker='ada',listener='ben',quote_indices=[0],reason_keys=['ada.knows.box.open'],claim=dict(key='box.open',value=False)),
                dict(speaker='ben',listener='ada',quote_indices=[1],reply_to=0)])])])
        original=deepcopy(book)
        row=r.realize(trace,lambda run,rng:render_book(run,rng,book))
        self.assertEqual(book,original)
        dialog=Conversation(row['trace'],row['paragraphs'])
        self.assertEqual(len(dialog.dialogue),3)
        self.assertEqual(dialog.dialogue[2]['reply_to'],dialog.dialogue[1]['id'])
        self.assertEqual(dialog.dialogue[1]['event_id'],3)
        for record in dialog.dialogue:
            for span in record['quotes']:
                self.assertEqual(row['paragraphs'][record['paragraph']]['text'][span['start']:span['end']],span['text'])

    def test_dialogue_smoke_samples_include_full_grounded_conversations(self):
        rows=[enrich(saved(world,i)) for world in ('library_parade','pond_concert') for i in range(3)]
        report=measure(rows)
        self.assertEqual(report['defects'],{})
        self.assertGreaterEqual(report['kinds'].get('dialogue',0),6)
        self.assertGreaterEqual(report['three_pair_conversations'],30)
        self.assertGreaterEqual(report['multi_sentence_fraction'],.70)
        self.assertGreaterEqual(report['mean_answer_words'],12)

    def test_default_renderer_indexes_quotes_before_grouping_without_extra_author_tokens(self):
        trace=stale_belief()
        book=dict(openings=[dict(text='Ada and Ben shared a box.',when=[])],
                  endings=[dict(text='The box stood open.',when=[])],lexicon=[],scenes=[])
        for scene,text in [('look','“Closed,” Ada said.'),('open','The box swung open.'),
                           ('tell','Ada told Ben, “Closed.”')]:
            book['scenes'].append(dict(scene=scene,role='bridge',variants=[dict(text=text,when=[])]))
        row=r.realize(trace,lambda run,rng:render_book(run,rng,book))
        self.assertEqual(row['paragraphs'][1]['event_ids'],[1,2,3])
        records=collect_dialogue(trace,row['paragraphs'])
        self.assertEqual([u['event_id'] for u in records],[1,3])
        self.assertIn('“Closed,” Ada said. The box swung open. Ada told Ben, “Closed.”',row['story'])

    def test_six_pinned_speech_conversations(self):
        pins=json.loads((ROOT/'dialogue_pins.json').read_text())
        self.assertEqual(len(pins),6)
        for pin in pins:
            with self.subTest(source=pin['source'],index=pin['index']):
                row=json.loads((ROOT/pin['source']).read_text())[pin['index']]
                self.assertEqual(fingerprint(row['story']),pin['story_sha256'])
                dialog=Conversation(row['trace'],row['paragraphs'])
                for question in pin['questions']: dialog.ask(question)
                self.assertEqual(dialog.turns,pin['expected'])


if __name__ == '__main__': unittest.main()
