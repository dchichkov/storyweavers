"""Behavioral interventions, grounding and compression for decision beats."""
from copy import deepcopy
import unittest

from .storytelling.runtime import generate,replay,setup,build_forest
from .storytelling.qa import questions
from .story_memory import annotate
from .test_storycraft import BRANCHES,frame
from .storytelling.revisions.decision_policy import reminder,reminder_weights,motif,render,initialize
from .storytelling.revisions.language import clause
from .storytelling.attribute_grammar import expand_attributes

APPRAISALS={'pottery':('usefulness','design','deadline'),
            'music':('together','public_turn','contribution'),
            'greenhouse':('both','show','risk')}


def run_saved(p,w,saved):
    f=frame(saved)
    decision=p.select_narration(w,f,saved['narrative_decision']['labels'])
    event=p.commit(w,f,saved['sentence']);p.commit_narration(w,event,decision)
    for k in ('referents','speakers','narrated'):event[k]=saved[k]


def prefix(row,kind):
    p,w=setup(row['scenario'],row['seed'],**row['options'])
    for saved in row['final_world']['history']:
        if saved['frame']['kind']==kind:return p,w,frame(saved)
        run_saved(p,w,saved)
    raise AssertionError('missing event '+kind)


def masses(p,w,attention=True):
    forest,_=build_forest(p,w,predict_attributes=True,attention=attention)
    result={}
    for d in forest.derivations:result[d.frame.kind]=result.get(d.frame.kind,0)+d.probability
    return result,forest


class DecisionBeatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows={(name,branch):generate(name,19,edition='crafted',decision_beats=True,choice=branch)
                  for name,branches in BRANCHES.items() for branch in branches}

    def test_all_branches_replay_export_and_have_actual_costs_and_payoffs(self):
        for key,row in self.rows.items():
            with self.subTest(path=key):
                self.assertTrue(replay(row));annotate(row)
                m=row['final_world']['narrative']['storycraft']['decisions']
                self.assertEqual(len(m['appraisals']),1)
                self.assertTrue(m['observed_costs']);self.assertTrue(m['payoffs'])
                by_id={h['id']:h for h in row['final_world']['history']}
                for a in m['appraisals']:
                    self.assertTrue(a['evidence_events'])
                    self.assertTrue(all(i<a['event'] and by_id[i]['narrated'] for i in a['evidence_events']))
                for cost in m['observed_costs']:
                    self.assertEqual(cost['status'],'observed')
                    self.assertTrue(set(cost['states'])<=set(by_id[cost['event']]['after']['entities'][cost['carrier']]['state']))
                for payoff in m['payoffs']:
                    self.assertLess(payoff['setup_event'],payoff['event'])
                    self.assertNotEqual(payoff['earlier_meaning'],payoff['meaning'])
                    for carrier,states in payoff['evidence'].items():
                        self.assertTrue(set(states)<=set(by_id[payoff['event']]['before']['entities'][carrier]['state']))
                for q in questions(row,100):
                    for ev in q['evidence']:self.assertEqual(row['story'][ev['start']:ev['end']],ev['text'])

    def test_appraisals_change_real_branch_probabilities(self):
        expected={'pottery':('design','remake'),'music':('together','choose_private'),'greenhouse':('show','choose_flower')}
        for name,(favored,branch) in expected.items():
            values={}
            for appraisal in APPRAISALS[name]:
                row=generate(name,19,edition='crafted',decision_beats=True,appraisal='appraise_'+appraisal)
                chosen=next(h['frame']['kind'] for h in row['final_world']['history'] if h['frame']['kind'].removeprefix('crafted_') in BRANCHES[name])
                p,w,_=prefix(row,chosen);before=w.to_dict()
                probabilities,forest=masses(p,w)
                self.assertEqual(before,w.to_dict())
                self.assertEqual(set(probabilities),{'crafted_'+b for b in BRANCHES[name]})
                self.assertAlmostEqual(sum(probabilities.values()),1)
                self.assertTrue(all(0<p<1 for p in probabilities.values()))
                values[appraisal]=probabilities['crafted_'+branch]
                ablated,_=masses(p,w,attention=False)
                self.assertTrue(all(abs(p-1/3)<1e-9 for p in ablated.values()))
                for evidence in forest.evidence.values():
                    for term in evidence['decision_beats']['contributions']:
                        self.assertLess(term['source_event'],len(w.history)+1)
            self.assertGreater(values[favored],max(v for k,v in values.items() if k!=favored)+.1)

    def test_missing_utterance_blocks_action_even_with_physical_flags_intact(self):
        cases=[('pottery','remake','crafted_remake','remake_warning'),
               ('music','choose_private','crafted_shut_door','door_promise'),
               ('music','choose_written','crafted_give_credit','credit_promise'),
               ('greenhouse','choose_share','crafted_hold_handle','hold_request')]
        for name,branch,kind,key in cases:
            p,w,f=prefix(self.rows[name,branch],kind)
            del w.narrative['storycraft']['decisions']['utterances'][key]
            before=w.to_dict()
            with self.assertRaises(ValueError):p.commit(w,f,'forged action')
            self.assertEqual(before,w.to_dict())

    def test_promise_is_fulfilled_only_by_its_later_action(self):
        row=self.rows['music','choose_private']
        p,w,_=prefix(row,'crafted_shut_door')
        m=w.narrative['storycraft']['decisions']
        self.assertEqual(m['utterances']['door_promise']['status'],'uttered')
        self.assertIn('open',w.entities['door'].state)
        saved=next(h for h in row['final_world']['history'] if h['frame']['kind']=='crafted_shut_door')
        run_saved(p,w,saved)
        self.assertEqual(m['utterances']['door_promise']['status'],'fulfilled')
        self.assertEqual(m['utterances']['door_promise']['resolved_event'],saved['id'])
        self.assertIn('closed',w.entities['door'].state)
        link=next(x for x in m['dialogue_links'] if x['key']=='door_promise')
        self.assertLess(link['source_event'],link['event'])

    def test_appraisal_needs_visible_evidence_and_valid_controls(self):
        row=self.rows['pottery','remake']
        kind='crafted_'+row['final_world']['narrative']['storycraft']['decisions']['appraisals'][0]['name']
        p,w,f=prefix(row,kind)
        w.history[-1]['narrated']=False
        before=w.to_dict()
        with self.assertRaises(ValueError):p.commit(w,f,'unsupported appraisal')
        self.assertEqual(before,w.to_dict())
        for options in ({'choice':'appraise_design'},{'appraisal':'invented'},{'compression':'off'}):
            with self.assertRaises(ValueError):setup('pottery',edition='crafted',decision_beats=True,**options)
        with self.assertRaises(ValueError):setup('pottery',edition='crafted',decision_beats='yes')

    def test_surface_only_generation_retains_same_executed_story(self):
        for name in BRANCHES:
            a=generate(name,71,edition='crafted',decision_beats=True)
            b=generate(name,71,edition='crafted',decision_beats=True,predict_attributes=False)
            self.assertEqual(a['story'],b['story'])
            self.assertEqual(a['final_world'],b['final_world'])

    def test_payoffs_need_visible_setup_and_matching_current_state(self):
        for name,branch,kind,key,carrier,state in [
                ('pottery','keep_dent','crafted_use','gift_shape','cup','thumb_hollow'),
                ('music','choose_private','crafted_end_private','answer','hero','played_private'),
                ('greenhouse','choose_seedlings','crafted_end_seedlings','ribbon','ribbon','water_first_marker')]:
            p,w,f=prefix(self.rows[name,branch],kind)
            for missing in ('setup','state'):
                changed=w.clone()
                if missing=='setup':del changed.narrative['storycraft']['decisions']['details'][key]
                else:changed.entities[carrier].state.discard(state)
                before=changed.to_dict()
                with self.assertRaises(ValueError):p.commit(changed,f,'unearned payoff')
                self.assertEqual(before,changed.to_dict())

    def test_compression_is_semantic_and_keeps_new_meanings(self):
        row=self.rows['music','choose_private'];p,w,_=prefix(row,'crafted_end_private')
        n=reminder('entry','program','withdrawn',clause('program','remain','Both names were crossed out.'))
        before=w.to_dict();compressed=reminder_weights(w,n)
        self.assertAlmostEqual(compressed['say']/(compressed['say']+compressed['omit']),.15/1.15)
        self.assertEqual(before,w.to_dict())
        w.narrative['storycraft']['decisions']['compression']=False
        plain=reminder_weights(w,n);self.assertEqual(plain['say'],plain['omit'])
        changed=deepcopy(n);changed['meaning']='restored'
        self.assertEqual(reminder_weights(w,changed)['omit'],0)
        changed=deepcopy(n);changed['carrier']='paper'
        self.assertEqual(reminder_weights(w,changed)['omit'],0)
        rows=list(expand_attributes(render(n,w)))
        self.assertAlmostEqual(sum(r[1] for r in rows),1)
        self.assertIn((),{r[0] for r in rows})

    def test_appraisal_redundancy_is_omitted_but_first_explanation_remains(self):
        for appraisal,redundant in [('appraise_risk',True),('appraise_both',False)]:
            row=generate('greenhouse',19,edition='crafted',decision_beats=True,
                         appraisal=appraisal,choice='choose_seedlings')
            self.assertTrue(replay(row));annotate(row)
            reminder=next(x for x in row['final_world']['narrative']['storycraft']['decisions']['reminders'] if x['key']=='risk')
            self.assertEqual(reminder['weights']['redundant'],redundant)
            self.assertEqual(reminder['selected'],'omit' if redundant else 'say')
            self.assertIn('My flower will have to miss the show.',row['story'])
            if not redundant:self.assertIn("I don't want to risk the little ones.",row['story'])

    def test_candidate_attributes_do_not_claim_future_outcomes(self):
        saw_contract=saw_detail=saw_appraisal=False
        for row in self.rows.values():
            for scene in row['trace']:
                table=scene['attribute_table']
                for step in scene['word_trace']:
                    self.assertAlmostEqual(sum(c['probability'] for c in step['annotated_choices']),1)
                    for c in step['annotated_choices']:
                        a=table[c['attributes']];d=a['storycraft']['decisions']
                        self.assertTrue(all(x['event']<scene['event_id'] for x in d['prior_appraisals']+d['observed_costs']))
                        self.assertEqual(a['event']['status'],'proposed')
                        saw_contract|='dialogue_contract' in a
                        saw_detail|='narrative_detail' in a
                        saw_appraisal|=bool(d['appraisal'])
        self.assertTrue(saw_contract and saw_detail and saw_appraisal)

    def test_refusal_and_resources_survive_policy_reranking(self):
        for branch in BRANCHES['music']:
            self.assertIn('public_refused',self.rows['music',branch]['final_world']['entities']['partner']['state'])
        for branch in BRANCHES['greenhouse']:
            for h in self.rows['greenhouse',branch]['final_world']['history']:
                for snap in (h['before'],h['after']):
                    quantities=[]
                    for key in ('barrel','can','sunflower','tomatoes'):
                        units=[int(s.rsplit('_',1)[1]) for s in snap['entities'][key]['state'] if s.startswith('water_units_')]
                        self.assertEqual(len(units),1);quantities+=units
                    self.assertEqual(sum(quantities),2)

    def test_policy_rebinds_carriers_without_world_specific_names(self):
        # Shared motif/reader policy operates on IDs and meanings, not Bea/Nia.
        _,w=setup('music',0,edition='crafted',decision_beats=True)
        w.entities['paper'].noun='stone tablet'
        w.narrative['storycraft']['decisions']['details']['message']=dict(carrier='paper',meaning='unread',event=1)
        n=reminder('message','paper','unread',clause('hero','see','{paper:the} was still unread.',object='paper'))
        self.assertTrue(reminder_weights(w,n)['redundant'])
        self.assertIn('stone tablet',' '.join(next(expand_attributes(render(n,w)))[0]))
        self.assertNotIn('Nia',str(n))


if __name__=='__main__':unittest.main()
