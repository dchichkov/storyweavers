from __future__ import annotations

import asyncio
import json
import unittest

from storypatches.artifacts import APPLY_PATCH_TOOL, patch_output, request_body
from storypatches.catalog import BASIC_PLOTS, sample_seed
from storypatches.patches import PatchSlot, apply_patch, compose_variants, parse_patch, patch_slots, validate_patch
from storypatches.pipeline import normalize_base_url, official_openai
from storypatches.quality import qa_report, has_dialogue


def fixture_bundle() -> tuple[dict[str, str], dict]:
    seed = sample_seed(7, 1).to_dict()
    seed["words"] = ["apple", "bridge", "cloud"]
    outline = {
        "title": "The Cloud Bridge",
        "premise": "Two friends carry an apple over a bridge.",
        "cast": [{"name": "Mina", "kind": "child", "role": "builder"},
                 {"name": "Taro", "kind": "child", "role": "helper"}],
        "objects": [{"name": "apple", "carrier_of": "kindness"}],
        "setting": "garden",
        "kernels": ["Quest", "Friendship", "Discovery"],
        "beats": [{"id": f"b{i}", "kernel": "Quest", "actor": "Mina",
                   "action": "acts", "state_change": "the bridge improves"} for i in range(4)],
        "variations": [{"name": f"v{i}", "kernels": ["Quest", "Friendship", "Discovery"],
                        "change": "A different safe attempt succeeds."} for i in range(3)],
        "dialogue_plan": [],
        "ending_image": "An apple rests below a cloud.",
    }
    sentence = ("Mina and Taro carried an apple toward the bridge under a silver cloud. "
                "They tested each board carefully, helped one another, and learned what made the crossing safe. "
                "Their patient work changed the wobbly path into a steady way home.")
    story_lines = ["# The Cloud Bridge", ""]
    for section in ("opening", "setup", "inciting", "attempt", "turn", "ending"):
        story_lines += [f"<!-- section:{section} -->", sentence, ""]
    questions = [{
        "id": f"q{i:02d}",
        "question": f"Question {i}?",
        "answer": "The friends worked together. Their careful test made the bridge safe.",
        "follow_up_question": "Why did that matter?",
        "follow_up_answer": "The apple could cross safely. The friends also trusted each other.",
    } for i in range(1, 7)]
    return {
        "outline.json": json.dumps(outline, indent=2) + "\n",
        "story.md": "\n".join(story_lines).rstrip() + "\n",
        "conversations.json": json.dumps(questions, indent=2) + "\n",
    }, seed


def small_patch(bundle: dict[str, str], number: int, section: str, question: int) -> str:
    story_line = bundle["story.md"].split(f"<!-- section:{section} -->\n", 1)[1].splitlines()[0]
    old_question = f'    "question": "Question {question}?",'
    return f"""*** Begin Patch
*** Update File: story.md
@@ {section}
 <!-- section:{section} -->
-{story_line}
+{story_line} Detail {number} made this moment distinct.
*** Update File: conversations.json
@@ q{question:02d}
     "id": "q{question:02d}",
-{old_question}
+    "question": "What changed in detail {number}?",
*** End Patch
"""


class CatalogTests(unittest.TestCase):
    def test_seed_is_reproducible_and_has_requested_shape(self):
        first = sample_seed(42, 0)
        self.assertEqual(first, sample_seed(42, 0))
        self.assertEqual(len(first.words), 3)
        self.assertTrue(3 <= len(first.kernels) <= 5)
        self.assertEqual(len(BASIC_PLOTS), 7)
        self.assertTrue(first.dialogue_required)
        self.assertFalse(sample_seed(42, 1).dialogue_required)

    def test_exactly_one_hundred_patch_slots(self):
        slots = patch_slots()
        self.assertEqual(len(slots), 100)
        self.assertEqual(len({slot.id for slot in slots}), 100)


class ToolTests(unittest.TestCase):
    def test_function_patch_response(self):
        patch = "*** Begin Patch\n*** End Patch"
        response = {"output": [{"type": "function_call", "name": "apply_patch",
                                "arguments": json.dumps({"patch": patch})}]}
        self.assertEqual(patch_output(response), patch)
        response["output"].append(response["output"][0])
        with self.assertRaises(ValueError):
            patch_output(response)

    def test_single_quoted_dialogue(self):
        self.assertTrue(has_dialogue("'I can't open it,' Elara said. 'Let me help,' Barnaby replied."))
        self.assertFalse(has_dialogue("Elara's book was on Barnaby's shelf."))

    def test_custom_endpoint_request_omits_openai_only_fields(self):
        body = request_body("prefix", "suffix", model="Qwen/Qwen3.8-27B-FP8",
                            effort=None, service_tier=None, cache_mode="off", patch_tool=True)
        for key in ("service_tier", "reasoning", "prompt_cache_key",
                    "prompt_cache_options", "prompt_cache_retention"):
            self.assertNotIn(key, body)
        self.assertEqual(body["model"], "Qwen/Qwen3.8-27B-FP8")
        self.assertEqual(normalize_base_url("http://127.0.0.1:8001/"), "http://127.0.0.1:8001/v1")
        self.assertFalse(official_openai("http://127.0.0.1:8001/v1"))

    def test_patch_request_exposes_only_one_synthetic_tool(self):
        body = request_body("same prefix", "slot one", patch_tool=True)
        other = request_body("same prefix", "slot two", patch_tool=True)
        self.assertEqual(body["tools"], [APPLY_PATCH_TOOL])
        self.assertEqual(body["tool_choice"], "required")
        self.assertFalse(body["parallel_tool_calls"])
        self.assertEqual(body["prompt_cache_key"], other["prompt_cache_key"])
        self.assertEqual(body["input"][1]["content"][0], other["input"][1]["content"][0])
        self.assertNotIn("read", json.dumps(body["tools"]).lower())
        self.assertNotIn("write", json.dumps(body["tools"]).lower())

    def test_patch_tool_and_cache_fields_reach_wire(self):
        import httpx
        from openai import AsyncOpenAI

        request = request_body("same prefix", "slot one", patch_tool=True)
        sent = []

        def receive(req):
            sent.append(json.loads(req.content))
            return httpx.Response(200, json={
                "id": "resp_test", "object": "response", "created_at": 1,
                "status": "completed", "model": "gpt-5.6-luna", "output": [],
            })

        async def run():
            async with AsyncOpenAI(api_key="not-real", base_url="https://example.invalid/v1",
                    http_client=httpx.AsyncClient(transport=httpx.MockTransport(receive))) as client:
                await client.responses.create(**request)

        asyncio.run(run())
        self.assertEqual(sent, [request])

    def test_patch_output_requires_one_call_and_no_prose(self):
        response = {"output": [{"type": "custom_tool_call", "name": "apply_patch",
                                "input": "*** Begin Patch\n*** End Patch"}]}
        self.assertTrue(patch_output(response).startswith("*** Begin Patch"))
        response["output"].append({"type": "message", "content": [{"type": "output_text", "text": "done"}]})
        with self.assertRaisesRegex(ValueError, "prose"):
            patch_output(response)


class PatchTests(unittest.TestCase):
    def test_repeated_file_sections_apply_in_order(self):
        base = {"story.md": "red boat\nsmall sail\n"}
        patch = "*** Begin Patch\n*** Update File: story.md\n@@\n-red boat\n+blue boat\n*** Update File: story.md\n@@\n-small sail\n+large sail\n*** End Patch"
        self.assertEqual(apply_patch(base, patch)["story.md"], "blue boat\nlarge sail\n")

    def test_quote_equivalence_still_rejects_word_changes(self):
        base = {"story.md": "Leo\u2019s red boat.\n"}
        patch = "*** Begin Patch\n*** Update File: story.md\n@@\n-Leo's red boat.\n+Leo's blue boat.\n*** End Patch"
        self.assertEqual(apply_patch(base, patch)["story.md"], "Leo's blue boat.\n")
        with self.assertRaises(ValueError):
            apply_patch(base, patch.replace("-Leo's red", "-Leo's green"))

    def test_patch_applies_exact_context_atomically(self):
        bundle, _ = fixture_bundle()
        patch = small_patch(bundle, 1, "opening", 1)
        self.assertEqual({update.path for update in parse_patch(patch)}, {"story.md", "conversations.json"})
        updated = apply_patch(bundle, patch)
        self.assertIn("Detail 1", updated["story.md"])
        self.assertIn("detail 1", updated["conversations.json"])
        self.assertNotIn("Detail 1", bundle["story.md"])

    def test_unknown_path_and_ambiguous_context_fail(self):
        bad_path = "*** Begin Patch\n*** Update File: ../story.md\n@@\n-old\n+new\n*** End Patch"
        with self.assertRaisesRegex(ValueError, "not allowed"):
            parse_patch(bad_path)
        bundle, _ = fixture_bundle()
        ambiguous = """*** Begin Patch
*** Update File: story.md
@@
-Mina and Taro carried an apple toward the bridge under a silver cloud. They tested each board carefully, helped one another, and learned what made the crossing safe. Their patient work changed the wobbly path into a steady way home.
+Changed.
*** End Patch"""
        with self.assertRaisesRegex(ValueError, "exactly once"):
            apply_patch(bundle, ambiguous)

    def test_three_independent_patches_compose(self):
        bundle, seed = fixture_bundle()
        rows = []
        for number, section in enumerate(("opening", "inciting", "turn"), 1):
            slot = PatchSlot(f"x{number}", "trivial", "detail", section, f"q{number:02d}")
            patch = small_patch(bundle, number, section, number)
            _, digest = validate_patch(bundle, patch, slot, seed)
            rows.append({"id": slot.id, "tier": slot.tier, "section": slot.section,
                         "conversation": slot.conversation, "patch": patch,
                         "standalone_sha256": digest})
        records, conflicts = compose_variants(bundle, rows, seed, count=1)
        self.assertEqual(len(records[0]["patch_ids"]), 3)
        self.assertEqual(conflicts, {"x1": [], "x2": [], "x3": []})
        report = qa_report(records)
        self.assertEqual(report["records"], 1)
        self.assertEqual(sum(report["question_shapes"].values()), len(records[0]["questions"]))
        json.dumps(report)


if __name__ == "__main__":
    unittest.main()
