import asyncio
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import shutil
import tempfile

import api_requests as api
import authoring_cache as ac
import compact_prose as cp
import factory as f
import compact_workshop as cw
import algebra as a
from runtime import StoryError

ROOT = Path(__file__).resolve().parent


def fixture():
    root = ROOT/'runs/compact_algebra_v2/library_parade'
    return [json.loads((root/name).read_text()) for name in
            ('world.json','prose_slots.json','texts.json','samples_with_trace.json')]


class AuthoringCacheTests(unittest.TestCase):
    def test_seeds_change_suffix_not_cache_prefix_or_key(self):
        body=cw.json_request('',schema=ac.text_schema(),effort='low')
        before=deepcopy(body)
        one=api.cached_request(body,'Stable instructions',{'seed':1},'test')
        two=api.cached_request(body,'Stable instructions',{'seed':2},'test')
        self.assertEqual(body,before)
        self.assertEqual(one['input'][0],two['input'][0])
        self.assertEqual(one['prompt_cache_key'],two['prompt_cache_key'])
        self.assertNotEqual(one['input'][1],two['input'][1])
        self.assertNotIn('prompt_cache_breakpoint',json.dumps(one['input'][1]))
        self.assertEqual(one['prompt_cache_options'],{'mode':'explicit','ttl':'30m'})
        self.assertEqual(one['service_tier'],'flex')

    def test_contract_and_model_settings_version_cache_key(self):
        body=cw.json_request('',effort='low')
        key=api.cached_request(body,'a',{},'test')['prompt_cache_key']
        other=deepcopy(body);other['reasoning']['effort']='medium'
        self.assertNotEqual(key,api.cached_request(other,'a',{},'test')['prompt_cache_key'])
        self.assertNotEqual(key,api.cached_request(body,'b',{},'test')['prompt_cache_key'])

    def test_evidence_factoring_is_lossless_and_state_boundaries_stay_separate(self):
        doc,skeleton,texts,previews=fixture()
        old=deepcopy(skeleton);payload=ac.prose_payload(doc,skeleton,previews)
        for card in payload['cards']:
            original=skeleton['slots'][ac.aliases(skeleton)[card['id']]]
            evidence=deepcopy(card['evidence'])
            if 'state' in evidence:
                evidence['state']={**payload['common_boundary_facts'][card['section']],**evidence['state']}
            self.assertEqual(evidence,original['evidence'])
        self.assertEqual(skeleton,old)
        self.assertLess(len(api.compact(payload)),len(api.compact(skeleton)))

    def test_fixed_schema_aliases_preserve_exact_catalog(self):
        doc,skeleton,texts,previews=fixture()
        response={'cards':[{'id':alias,'text':texts['cards'][key][0]} for alias,key in ac.aliases(skeleton).items()]}
        expanded=ac.expand_texts(skeleton,response)
        self.assertEqual(cp.catalog(skeleton,expanded),cp.catalog(skeleton,texts))
        for broken in [response['cards'][:-1],response['cards']+[response['cards'][0]],
                       response['cards']+[{'id':'other','text':'Oops.'}]]:
            with self.assertRaises(StoryError):ac.expand_texts(skeleton,{'cards':broken})

    def test_short_named_repairs_retain_stale_text_precondition(self):
        doc,skeleton,texts,previews=fixture()
        alias=next(iter(ac.aliases(skeleton)));key=ac.aliases(skeleton)[alias]
        old=texts['cards'][key][0]
        patch=ac.expand_patch(skeleton,{'edits':[{'id':alias,'old':old,'new':'Ada smiled at the little cart.'}]})
        updated=cp.patch_texts(skeleton,texts,patch)
        self.assertEqual(updated['cards'][key],['Ada smiled at the little cart.'])
        with self.assertRaisesRegex(StoryError,'Stale'):cp.patch_texts(skeleton,updated,patch)

    def test_cached_judge_preserves_rubric_calibration_ids_and_schema(self):
        item={'stories':[{'id':'s000001','story':'A small story.'}]}
        old=f.quality.request_body(item);new=f.quality.request_body(item,cache_prompts=True)
        self.assertEqual(new.pop('prompt_cache_options'),{'mode':'explicit','ttl':'30m'})
        self.assertEqual(old,new)

    def test_full_prose_cache_policy_preserves_original_request(self):
        path=ROOT/'runs/compact_algebra_v2/library_parade/text_0.request.json'
        original=json.loads(path.read_text())
        actual=api.without_cache_writes(original)
        self.assertNotIn('prompt_cache_breakpoint',json.dumps(actual))
        self.assertEqual(actual.pop('prompt_cache_options'),{'mode':'explicit','ttl':'30m'})
        self.assertEqual(actual,original)

    def test_default_cache_only_preserves_complete_authoring_requests(self):
        doc,skeleton,texts,previews=fixture()
        requests={}
        async def run(root,profile):
            captured=[]
            async def answer(client,budget,world,stage,body):
                captured.append(deepcopy(body))
                return deepcopy(doc if stage=='world_0' else texts)
            with patch.object(cw,'ask',side_effect=answer):
                await cw.world_run(None,None,root/profile,{'seed':1},
                                   (ROOT/'AUTHORING_COMPACT.md').read_text(),cost_profile=profile)
            requests[profile]=captured
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'_runtime').mkdir()
            for name in cw.RUNTIME:shutil.copyfile(ROOT/name,root/'_runtime'/name)
            for profile in ('legacy','cache-only'):asyncio.run(run(root,profile))
        self.assertEqual(len(requests['legacy']),2)
        for old,new in zip(requests['legacy'],requests['cache-only']):
            self.assertEqual(new.pop('prompt_cache_options'),{'mode':'explicit','ttl':'30m'})
            self.assertEqual(old,new)

    def test_sdk_sends_canonical_cache_fields_over_http(self):
        import httpx
        from openai import AsyncOpenAI
        body=api.cached_request(cw.json_request('',effort='low'),'Instructions',{'seed':1},'test')
        seen=[]
        def handler(request):
            seen.append(json.loads(request.content))
            return httpx.Response(200,json={'id':'test','object':'response','created_at':0,
                'model':'gpt-5.6-luna','status':'completed','output':[],'service_tier':'flex'})
        async def run():
            async with AsyncOpenAI(api_key='test-placeholder',max_retries=0,
                    http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))) as client:
                await client.responses.create(**api.sdk_kwargs(body))
        asyncio.run(run())
        self.assertEqual(seen,[body])

    def test_costs_price_cached_reads_and_writes_separately(self):
        usage={'input_tokens':10000,'output_tokens':2000,
               'input_tokens_details':{'cached_tokens':3000,'cache_write_tokens':1000}}
        c=f.trial_cost.token_cost('gpt-5.6-luna',usage,'flex')
        self.assertAlmostEqual(c['usd_high'],(6000*.1+3000*.01+1000*.125+2000*.6)/1e6)
        self.assertAlmostEqual(f.trial_cost.token_cost('gpt-5.6-luna',usage,'default')['usd_high'],2*c['usd_high'])

    def test_named_deletion_repairs_reserved_kernel_without_rewriting_world(self):
        from test_algebra import world
        doc=world();original=deepcopy(doc)
        doc['kernels']={'DiscoverAndShare':{'roles':[],'body':{}}}
        with self.assertRaisesRegex(StoryError,'reserved'):a.build(doc)
        patch={'edits':[{'section':'kernels','id':'DiscoverAndShare','value':None}]}
        repaired=a.patch_world(doc,patch)
        self.assertEqual(a.build(repaired),a.build(original))
        self.assertIn('DiscoverAndShare',doc['kernels'])
        with self.assertRaisesRegex(StoryError,'missing'):a.patch_world(repaired,patch)

    def test_completed_loan_counts_as_an_outcome_even_when_endpoints_match(self):
        from test_algebra import world
        from runtime import solve
        from quality_checks import unfinished_outcomes
        trace=solve(a.build(world()),11)
        keys=['lens.owner','lens.loaned_by','box.open']
        row=dict(trace=trace,diagnostics={'outcome_writes':keys})
        self.assertEqual(trace['initial']['lens.owner'],trace['final']['lens.owner'])
        self.assertEqual(unfinished_outcomes([row]),[])
        # Merely declaring the same closed loan without executing it is inert.
        trace['events']=[]
        self.assertEqual(unfinished_outcomes([row]),['lens.loaned_by','lens.owner'])

    def test_preflight_reports_all_bad_composites_without_changing_world(self):
        from test_algebra import world
        doc=world();doc['compose']['news']['summary']='A whole story.'
        doc['compose']['second']=dict(op='DiscoverAndShare',args=['ben','ada','box.latch'],when={'box.open':True})
        old=deepcopy(doc)
        with self.assertRaises(StoryError) as cm:ac.preflight(doc)
        self.assertIn('compose.news',str(cm.exception));self.assertIn('compose.second',str(cm.exception))
        self.assertEqual(doc,old)
        ac.preflight(world())


if __name__=='__main__':unittest.main()
