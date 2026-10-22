from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import factory as f
import conversation_quality as cq
from conversation_trial import jobs_for, TrialBudget


def sample(i=0,world='library_parade'):
    return dict(world=world,sample_id=f'{world}:{i}',story='Ada gave Ben a book. Ben said, “Thank you.”',
        trace={'hidden':'This must not reach the semantic judge'},
        conversations=[dict(id='c000',turns=[dict(question='What did Ben say?',answer='Ben said, “Thank you.”'),
                                            dict(question='Who was he talking to?',answer='He was talking to Ada.')])])


def assessment(row):
    return dict(stories=[dict(id=row['sample_id'],conversations=[dict(id='c000',rating={k:8 for k in cq.RATING_KEYS},
        usable=True,note='Grounded exchange.',defects=[])])])


class ConversationJudgeTests(unittest.TestCase):
    def test_semantic_judge_sees_story_and_chat_without_hidden_trace(self):
        body=cq.request_body([sample()]);serialized=json.dumps(body)
        self.assertNotIn('This must not reach',serialized)
        self.assertEqual(body['service_tier'],'flex')
        self.assertEqual(body['model'],'gpt-5.6-terra')
        self.assertEqual(body['prompt_cache_options']['mode'],'explicit')
        self.assertIn('Thank you',serialized)

    def test_validate_requires_exact_ids_complete_scores_and_real_turns(self):
        row=sample();good=assessment(row)
        self.assertEqual(cq.validate(good,[row]),good)
        bad=deepcopy(good);bad['stories'][0]['conversations'][0]['rating']['overall']=True
        with self.assertRaises(ValueError):cq.validate(bad,[row])
        bad=deepcopy(good);bad['stories'][0]['conversations']=[]
        with self.assertRaises(ValueError):cq.validate(bad,[row])
        bad=deepcopy(good);bad['stories'][0]['conversations'][0]['defects']=[dict(turn=2,tag='wrong_quote',evidence='No such turn.')]
        with self.assertRaises(ValueError):cq.validate(bad,[row])
        bad=deepcopy(good);bad['stories'].append(deepcopy(bad['stories'][0]))
        with self.assertRaises(ValueError):cq.validate(bad,[row])

    def test_all_samples_are_judged_once_by_each_protocol(self):
        rows=[sample(i,world) for world in ('library_parade','pond_concert') for i in range(50)]
        jobs=jobs_for(rows)
        stories=[s['sample_id'] for j in jobs if j['phase']=='story_quality' for s in j['input']['stories']]
        conversations=[s['sample_id'] for j in jobs if j['phase']=='qa_quality' for s in j['input']]
        expected=sorted(r['sample_id'] for r in rows)
        self.assertEqual(sorted(stories),expected);self.assertEqual(sorted(conversations),expected)
        self.assertEqual(len(jobs),30)
        job=jobs[0]
        self.assertEqual(job['body'],f.quality.request_body(job['input'],cache_prompts=True))

    def test_trial_budget_is_resumable_and_does_not_reset_campaign_limit(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger=f.Budget(Path(temp)/'budget.json',15)
            body=dict(model='gpt-5.6-terra',max_output_tokens=2000)
            scoped=TrialBudget(ledger,'trial',.04)
            scoped.reserve('qa/first',body)
            resumed=TrialBudget(f.Budget(Path(temp)/'budget.json',15),'trial',.04)
            with self.assertRaisesRegex(ValueError,'Trial spending cap'):resumed.reserve('qa/second',body)
            self.assertEqual(json.loads((Path(temp)/'budget.json').read_text())['limit_usd'],15)


if __name__=='__main__':unittest.main()
