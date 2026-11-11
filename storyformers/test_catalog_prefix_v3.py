from copy import deepcopy
import json
from pathlib import Path
import unittest

from . import catalog_prefix_annotation as v2, catalog_prefix_v3 as v3
from .annotate_prefixes import contract_for, extract
from .prefix_annotation import request_prefix
from .test_prefix_annotation import raw_response


class ReconciledPrefixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.examples = json.loads(v3.EXAMPLES.read_text())
        cls.prefix = v3.shared_prefix()

    def test_all_examples_and_existing_names(self):
        for example in self.examples:
            v3.validate_record(example["prefix"],example["response"])
        self.assertEqual(set(v3.registry()) - set(v2.registry()), {"plot", "depiction"})
        self.assertNotIn("goal", v3.registry())

    def test_historical_contract_and_prompt_remain_reproducible(self):
        frozen = v2.ROOT / "runs/prefix_catalog_full_story_20261108/prompt.json"
        if frozen.exists():
            self.assertEqual(v2.shared_prefix(),json.loads(frozen.read_text())["prefix"])
        example=self.examples[0]
        body=v2.prefix_request(example["prefix"],0)
        self.assertIs(contract_for(body),v2)
        self.assertEqual(extract(body,raw_response(example["response"]))[0],example["response"])

    def test_new_contract_preserves_prefix_isolation_and_cache_layout(self):
        a=v3.prefix_request("Ada wanted a kite.",2,prefix=self.prefix)
        b=v3.prefix_request("Ada wanted an apple.",2,prefix=self.prefix)
        self.assertEqual(a,b)
        self.assertEqual(request_prefix(a),"Ada wanted")
        self.assertIs(contract_for(a),v3)
        self.assertEqual(a["prompt_cache_options"],{"mode":"explicit","ttl":"30m"})
        self.assertEqual(a["input"][0],v3.prefix_request("Ada wanted a kite.",6,prefix=self.prefix)["input"][0])

    def test_narrative_role_does_not_replace_participant_role(self):
        example=next(e for e in self.examples if e["prefix"]=="Ada wanted to mend a kite")
        row=v3.validate_record(example["prefix"],example["response"])
        self.assertEqual(row["role"],"patient")
        self.assertEqual(row["plot"]["role"],"desire")
        with self.assertRaisesRegex(ValueError,"unregistered feature"):
            v2.validate_record(example["prefix"],row)

    def test_future_plot_evidence_and_native_claims_rejected(self):
        example=next(e for e in self.examples if e["prefix"]=="Ada wanted")
        for patch in ({"plot_id":"plot999"},{"evidence_indices":[999]},
                      {"status":"observed"},{"native_dependencies":[]},{"role":"actor"},
                      {"role":[]},{"stage":{}},{"basis":[]}):
            row=deepcopy(example["response"]);row["plot"].update(patch)
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                v3.validate_record(example["prefix"],row)

    def test_plot_links_are_earlier_and_not_mechanically_verified(self):
        example=next(e for e in self.examples if e["prefix"].startswith("Omar"))
        row=deepcopy(example["response"])
        row["plot"]["incoming_links"][0]["mechanically_verified"]=True
        with self.assertRaisesRegex(ValueError,"mechanical verification"):
            v3.validate_record(example["prefix"],row)

    def test_depiction_identity_cannot_collapse(self):
        example=next(e for e in self.examples if e["prefix"].startswith("A bird"))
        row=deepcopy(example["response"])
        row["depiction"]["referent_id"]=row["entity_id"]
        with self.assertRaisesRegex(ValueError,"distinct"):
            v3.validate_record(example["prefix"],row)

    def test_lexical_modal_enum_reconciles_existing_field(self):
        row=dict(index=2,token="could",pos="v",lemma="can",scope_id="s0",modal_auxiliary_class="ability_family")
        with self.assertRaisesRegex(ValueError,"unsupported value"):
            v3.validate_record("Ada could",row)
        row["modal_auxiliary_class"]="can"
        v3.validate_record("Ada could",row)

    def test_quotation_anchor_and_scope_cycles_rejected(self):
        example=next(e for e in self.examples if e["prefix"].startswith("Mika"))
        row=deepcopy(example["response"])
        scopes=row["_references"]["scopes"]
        quote=next(k for k in scopes if k.startswith("q"))
        scopes[quote]["parent"]=row["scope_id"]
        with self.assertRaisesRegex(ValueError,"cycles"):
            v3.validate_record(example["prefix"],row)
        row=dict(index=2,token="Ada",pos="n",lemma="Ada",scope_id="q3",
                 _references={"scopes":{"q3":{"kind":"quotation","parent":"s0"}}})
        with self.assertRaisesRegex(ValueError,"opening quote"):
            v3.validate_record("“ Ada",row)


if __name__ == "__main__":
    unittest.main()
