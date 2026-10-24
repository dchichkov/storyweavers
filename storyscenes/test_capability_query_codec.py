"""Structured query values retain their declared record type across JSON."""
from dataclasses import replace
import json
import unittest

from storyscenes.capabilities.api import registry
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import CapabilityError, Query, matches
from storyscenes.capabilities.epistemic import Result
from storyscenes.harbor_story import Conditions, build


class QueryCodecTests(unittest.TestCase):
    def test_result_guards_roundtrip_in_goals_and_requirements(self):
        spec = build(Conditions())
        result = Result(kind="exact", value="deep enough")
        equal = Query(table="propositions", key="depth", field="result", value=result)
        member = replace(equal, op="in", value=(Result(kind="exact", value="too shallow"), result))
        spec = replace(spec, goal=(equal, member), actions=(replace(spec.actions[0], requires=(equal, member)),))
        restored = loads(registry(), dumps(spec))
        self.assertEqual(restored, spec)
        state = registry().initial(restored)
        self.assertTrue(all(matches(state, q) for q in restored.goal))
        self.assertIsInstance(restored.actions[0].requires[0].value, Result)

    def test_malformed_result_rejected_before_execution(self):
        spec = build(Conditions())
        data = json.loads(dumps(spec))
        guard = next(a for a in data["actions"] if a["id"] == "launch")["requires"][1]
        guard["value"]["unexpected"] = "not a result field"
        with self.assertRaises(CapabilityError):
            loads(registry(), json.dumps(data))

    def test_missing_record_comparison_stays_none(self):
        spec = replace(build(Conditions()), goal=(Query(table="propositions", key="absent", field="result", value=None),))
        restored = loads(registry(), dumps(spec))
        self.assertIsNone(restored.goal[0].value)
        self.assertTrue(matches(registry().initial(restored), restored.goal[0]))


if __name__ == "__main__":
    unittest.main()
