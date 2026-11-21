"""Protect the reusable authoring boundary and the SDK wire representation."""
import json
import unittest

from .authoring_trial import author_request, MODELS, quality


class AuthoringCacheTests(unittest.TestCase):
    def test_tasks_change_only_suffix_and_preserve_all_inputs(self):
        sources = {"z.py": "z = 1", "a.py": "a = 2"}
        first = author_request(MODELS["terra"], sources, "story A", contract="task A", gaps=["gap A"])
        second = author_request(MODELS["terra"], dict(reversed(list(sources.items()))),
                                "story B", contract="task B", gaps=["gap B"])
        self.assertEqual(first["input"][0], second["input"][0])
        self.assertEqual(first["prompt_cache_key"], second["prompt_cache_key"])
        self.assertNotEqual(first["input"][1], second["input"][1])
        prefix = first["input"][0]["content"][0]
        self.assertEqual(json.loads(prefix["text"].split("\n", 1)[1])["current_ruleset"], sources)
        self.assertEqual(prefix["prompt_cache_breakpoint"], {"mode": "explicit"})
        self.assertEqual(json.loads(first["input"][1]["content"]),
                         dict(task="task A", source_story="story A", known_mismatches=["gap A"]))

    def test_changed_rules_and_models_get_distinct_keys(self):
        key = author_request(MODELS["terra"], {"a.py": "v1"}, "story")["prompt_cache_key"]
        for model, source in [(MODELS["luna"], "v1"), (MODELS["terra"], "v2")]:
            self.assertNotEqual(key, author_request(model, {"a.py": source}, "story")["prompt_cache_key"])

    def test_sdk_transport_keeps_boundary_and_flex_high(self):
        body = author_request(MODELS["terra"], {"a.py": "a"}, "story")
        wire = quality.api_requests.sdk_kwargs(body)
        self.assertEqual(wire["extra_body"]["prompt_cache_options"], {"mode": "explicit", "ttl": "30m"})
        self.assertEqual(wire["input"], body["input"])
        self.assertEqual(wire["service_tier"], "flex")
        self.assertEqual(wire["reasoning"], {"effort": "high"})
        self.assertIn("prompt_cache_options", body)


if __name__ == "__main__":
    unittest.main()
