"""Questions must preserve selected utterances, temporal evidence and raw offsets."""
from copy import deepcopy
import unittest

from .storytelling.runtime import generate
from .beat_qa import questions,presentation_evidence


class BeatQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.camp=generate('camp',43,beat_budget=6,continuations='expanded')
        cls.pottery=generate('pottery',43,beat_budget=6,continuations='expanded')

    def test_proposal_evidence_excludes_following_execution(self):
        row=self.camp
        q=next(q for q in questions(row) if q['kind']=='beat_dialogue')
        self.assertIn('I will give you the lantern',q['answer'])
        scene=next(s for s in row['scenes'] if s['event_id']==q['event_ids'][-1])
        self.assertLess(q['evidence'][-1]['end'],scene['end'])
        self.assertNotIn(scene['text'][len(q['evidence'][-1]['text']):].strip(),q['answer'])
        for item in q['evidence']:
            self.assertEqual(row['story'][item['start']:item['end']],item['text'])
        for item in presentation_evidence(row,q):
            self.assertEqual(row['presented_story'][item['start']:item['end']],item['text'])

    def test_prior_discovery_not_intervening_logistics_anchors_proposal(self):
        found=False
        for seed in range(20):
            row=generate('repair',seed,beat_budget=6,continuations='expanded')
            beats={b['event']:b for b in row['final_world']['narrative']['beats']['history']}
            for q in questions(row):
                b=beats[q['event_ids'][-1]]
                if b.get('discovery_event') and b['discovery_event']!=b['preceding_event']:
                    self.assertEqual(q['event_ids'][0],b['discovery_event'])
                    found=True;break
            if found:break
        self.assertTrue(found)

    def test_detail_question_names_its_carrier(self):
        q=next(q for q in questions(self.pottery) if q['kind']=='detail_payoff')
        self.assertIn('the bowl',q['question'])
        self.assertIn('dented',q['answer'])
        self.assertIn('dent was gone',q['answer'])

    def test_spoken_tool_is_in_evidence_bindings_even_when_patient_differs(self):
        row=generate('market',701,beat_budget=6,continuations='expanded')
        q=next(q for q in questions(row) if 'I will try the brass scale' in q['answer'])
        self.assertIn('scale',q['entity_ids'])
        self.assertIn('bag',q['entity_ids'])
        self.assertNotIn('dial',q['entity_ids'])

    def test_corrupted_trace_or_text_cannot_supply_answers(self):
        for corruption in ('body','span','memory','decision','detail','display'):
            with self.subTest(corruption=corruption):
                row=deepcopy(self.pottery)
                if corruption=='body':row['story']+=' extra'
                elif corruption=='span':row['scenes'][0]['start']+=1
                elif corruption=='memory':row['final_world']['narrative']['beats']['history'][0]['text']='Invented.'
                elif corruption=='decision':
                    event=next(e for e in row['final_world']['history'] if e.get('beat_decision',{}).get('selected','immediate')!='immediate')
                    event['beat_decision']['selected']='immediate'
                elif corruption=='detail':
                    memory=row['final_world']['narrative']['beats']
                    detail=memory['details'][memory['history'][0]['detail']]
                    detail['setup_event']=9999
                else:row['presentation']['body_offset']+=1
                with self.assertRaises(ValueError):
                    qs=questions(row)
                    for q in qs:presentation_evidence(row,q)

    def test_present_tense_answers_keep_the_selected_surface(self):
        row=generate('camp',43,beat_budget=6,continuations='expanded',tense='present')
        qs=questions(row);self.assertTrue(qs)
        beats={b['event']:b for b in row['final_world']['narrative']['beats']['history']}
        for q in qs:self.assertTrue(q['answer'].endswith(beats[q['event_ids'][-1]]['text']))
        self.assertTrue(any(' says,' in q['answer'] for q in qs))


if __name__=='__main__':unittest.main()
