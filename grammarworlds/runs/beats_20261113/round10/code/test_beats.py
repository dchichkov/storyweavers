from copy import deepcopy
import unittest

from .storytelling.runtime import generate,replay,setup
from .story_memory import annotate
from .beat_generation import options
from .beat_annotations import validate_beats
from .world import Frame


class BeatTests(unittest.TestCase):
    def test_post_setback_options_share_affected_object(self):
        for source,trigger,obj in [('museum','moving_light','shadow'),('repair','tighten_wrongly','wheel')]:
            p,w=setup(source,7,beat_budget=6)
            row=generate(source,7)
            for e in row['final_world']['history']:
                f=Frame(**{**e['frame'],'cause_ids':tuple(e['frame']['cause_ids'])})
                record=p.commit(w,f,e['sentence']);record['narrated']=e['narrated']
                if f.kind==trigger:break
            before=w.to_dict();c=options(p,w,p.candidates(w)[0][1])
            self.assertEqual({x['id'] for x in c},{'reaction','inspection','asking','immediate'})
            self.assertEqual({x['object'] for x in c},{obj})
            self.assertAlmostEqual(sum(x['probability'] for x in c),1.)
            self.assertEqual(w.to_dict(),before)
            w.entities[w.helper].location='elsewhere'
            w.entities[obj].location='elsewhere'
            remote=options(p,w,p.candidates(w)[0][1])
            self.assertNotIn('asking',{c['id'] for c in remote})
            self.assertNotIn('inspection',{c['id'] for c in remote})

    def test_replay_budgets_and_intact_annotation(self):
        for scenario in ('pottery','repair','museum'):
            for budget in (2,6):
                r=generate(scenario,19,beat_budget=budget,continuations='expanded')
                self.assertTrue(replay(r));before=deepcopy(r);d=annotate(r)
                self.assertEqual(r,before);self.assertEqual(d['text'],r['story'])
                self.assertLessEqual(r['final_world']['narrative']['beats']['used'],budget)
                for e in d['events']:
                    for b in e['beats']:
                        self.assertIn(b['experiencer'],d['entities'])
                        if b['preceding_event']:self.assertLess(b['preceding_event'],e['id'])
                    for link in e['detail_links']:self.assertLess(link['setup_event'],e['id'])

    def test_inspection_records_attention_without_inventing_knowledge(self):
        r=generate('museum',7,beat_budget=6,continuations='expanded')
        memory=r['final_world']['narrative']['beats']
        inspection=next(b for b in memory['history'] if b['id']=='inspection')
        self.assertFalse(inspection['knowledge_change']);self.assertEqual(inspection['kind'],'reaction')
        event=next(e for e in r['final_world']['history'] if e['id']==inspection['event'])
        self.assertEqual(event['after']['entities']['hero']['memes']['Attention'],.1)
        self.assertTrue(replay(r))

    def test_expanded_tokens_retain_their_own_beat_posterior(self):
        r=generate('museum',7,beat_budget=6,continuations='expanded');d=annotate(r)
        self.assertTrue(any(b.get('phase')=='pre_event' for e in d['events'] for b in e['beats']))
        self.assertTrue(any(c['beat'] and c['beat'].get('id')=='inspection'
                            for t in d['tokens'] for c in t['memory']['beat_candidates']))
        bad=deepcopy(d)
        event=next(e for e in bad['events'] if e['beats'])
        event['beats'][0]['preceding_event']=9999
        with self.assertRaises(ValueError):validate_beats(bad)

    def test_details_are_planted_in_visible_text(self):
        r=generate('pottery',19,beat_budget=2,continuations='expanded')
        history={e['id']:e for e in r['final_world']['history']}
        for d in r['final_world']['narrative']['beats']['details'].values():
            self.assertTrue(history[d['setup_event']]['narrated'])
        self.assertEqual(r['final_world']['narrative']['beats']['details']['pottery:grip']['setup_event'],2)

    def test_present_tense_expansions_replay(self):
        for source in ('pottery','repair','museum'):
            r=generate(source,7,beat_budget=6,tense='present',continuations='expanded')
            self.assertTrue(replay(r));annotate(r)
            self.assertNotIn(' said,',r['story'])
            self.assertNotIn(' hesitated.',r['story'])
            self.assertNotIn(' stayed still.',r['story'])

    def test_joined_plot_preserves_one_budget_and_rebound_carriers(self):
        from .plot_continuation import catalogue,run
        pool=catalogue([annotate(generate('pottery',3006))])
        r=run(pool,'changed_approach',seed=19,beat_budget=2)
        self.assertTrue(r['summary']['success'])
        used=[row['final_world']['narrative']['beats']['used'] for row in r['rows']]
        self.assertEqual(used,sorted(used));self.assertLessEqual(used[-1],2)
        for row in r['rows']:
            self.assertTrue(replay(row));d=annotate(row)
            for e in d['events']:
                for b in e['beats']:
                    self.assertIn(b['experiencer'],row['final_world']['entities'])
                    self.assertNotEqual(b['experiencer'],'hero')

    def test_silent_choices_are_not_dialogue_and_consultation_is_suggestion(self):
        r=generate('pottery',7);d=annotate(r)
        consult=next(e for e in d['events'] if e['kind']=='consult')
        self.assertEqual(consult['beats'][0]['speech_act'],'suggesting')
        for e in d['events']:
            source=next(h for h in r['final_world']['history'] if h['id']==e['id'])
            if not source['speakers']:
                self.assertTrue(all(b['speech_act'] is None for b in e['beats']))

    def test_beat_qa_requires_the_actual_earlier_text(self):
        from .beat_qa import questions
        r=generate('pottery',7,beat_budget=6,continuations='expanded')
        qs=questions(r);self.assertTrue(qs)
        self.assertTrue(any(q['kind']=='beat_dialogue' for q in qs))
        for q in qs:
            self.assertEqual(len(q['event_ids']),2)
            for e in q['evidence']:self.assertEqual(r['story'][e['start']:e['end']],e['text'])
            self.assertLessEqual(set(q['entity_ids']),r['final_world']['entities'].keys())
        bad=deepcopy(r)
        previous={b['preceding_event'] for b in r['final_world']['narrative']['beats']['history']}
        bad['scenes']=[s for s in bad['scenes'] if s['event_id'] not in previous]
        self.assertEqual(questions(bad),[])

    def test_callbacks_focus_the_detail_and_commitments_name_the_planned_action(self):
        found=False
        for seed in (7,19,42,103,211):
            r=generate('museum',seed,beat_budget=6,continuations='expanded')
            memory=r['final_world']['narrative']['beats']
            for b in memory['history']:
                if b['detail']:
                    self.assertEqual(b['object'],memory['details'][b['detail']]['entity'])
                    self.assertLess(b['setup_event'],b['event'])
                if b['speech_act'] in {'committing','suggesting'}:
                    found=True
                    e=next(e for e in r['final_world']['history'] if e['id']==b['event'])
                    self.assertEqual(b['planned_event'],e['frame']['kind'])
                    tool=e['frame']['instrument'] or e['frame']['destination']
                    self.assertIn(r['final_world']['entities'][tool]['noun'],b['text'])
        self.assertTrue(found)


if __name__=='__main__':unittest.main()
