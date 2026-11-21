"""Reading QA must be grounded in visible text, including branch differences."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from .storytelling.runtime import generate, replay, setup, build_forest, SCENARIOS
from .storytelling.qa import questions
from .storytelling.surface import SpeechLanguage

PINS = Path(__file__).parent / "storytelling/pins"


class StorytellingTests(unittest.TestCase):
    def test_all_worlds_both_tenses_grounded_full_qa_and_dialogue(self):
        for scenario in SCENARIOS:
            for tense in ("past", "present"):
                for seed in (0, 7):
                    row = generate(scenario, seed, tense=tense)
                    self.assertTrue(replay(row))
                    self.assertLess(len(row["story"].split()), 120)
                    self.assertGreaterEqual(len({p for s in row["scenes"] for p in s["speakers"]}), 2)
                    qa = questions(row)
                    self.assertGreaterEqual(len(qa), 5)
                    self.assertEqual(len({q["question"] for q in qa}), len(qa))
                    self.assertGreaterEqual(len({q["kind"] for q in qa}), 3)
                    self.assertTrue(any(q["answer"].count(".") >= 2 for q in qa))
                    for q in qa:
                        self.assertTrue(q["answer"].endswith("."))
                        self.assertGreaterEqual(len(q["answer"].split()), 3)
                        self.assertTrue(q["event_ids"] and q["entity_ids"])
                        for e in q["evidence"]:
                            self.assertEqual(row["story"][e["start"]:e["end"]], e["text"])

    def test_hidden_events_never_supply_reading_questions(self):
        row = generate("pottery", 7)
        hidden = {e["id"] for e in row["final_world"]["history"] if not e["narrated"]}
        self.assertTrue(hidden)
        self.assertTrue(any(e["frame"]["kind"] == "glaze" and not e["narrated"] for e in row["final_world"]["history"]))
        for q in questions(row, 50):
            self.assertFalse(set(q["event_ids"]) & hidden)
            self.assertNotIn("blue", q["answer"].lower())
        for changed in ("story", "span"):
            broken = deepcopy(row)
            if changed == "story": broken["story"] += " Another cup appeared."
            else: broken["scenes"][0]["start"] += 1
            with self.assertRaises(ValueError): questions(broken)

    def test_pottery_questions_follow_actual_design_branch(self):
        seen = set()
        for seed in range(8):
            row = generate("pottery", seed)
            qa = questions(row)
            flags = row["final_world"]["flags"]
            branch = next(k for k in ("thumb_design","smooth_design","bowl_design") if k in flags)
            seen.add(branch)
            design = next(q for q in qa if q["id"].endswith(":design"))
            self.assertEqual("thumb rest" in design["answer"], branch == "thumb_design")
            self.assertEqual("smoothed" in design["answer"], branch == "smooth_design")
            self.assertEqual("bowl" in design["answer"], branch == "bowl_design")
        self.assertEqual(seen, {"thumb_design","smooth_design","bowl_design"})

    def test_unwilling_music_never_claims_private_duet(self):
        for seed in range(5):
            row = generate("music", seed, partner_willing=False)
            self.assertNotIn("Nia and Mateo played", row["story"])
            self.assertFalse(any("private duet" in (q["question"] + q["answer"]).lower() for q in questions(row, 50)))
            replay(row)

    def test_prediction_is_pure_and_internal_steps_keep_guards(self):
        pack, w = setup("pottery", 7)
        before = w.to_dict()
        build_forest(pack, w)
        self.assertEqual(w.to_dict(), before)
        row = generate("pottery", 7)
        from .world import Frame
        for event in row["final_world"]["history"]:
            f = Frame(**{**event["frame"], "cause_ids": tuple(event["frame"]["cause_ids"])})
            if f.kind == "bisque":
                altered = w.clone()
                altered.entities["cup"].state.discard("dry")
                self.assertNotIn(f, [x for _, x in pack.candidates(altered)])
                with self.assertRaises(ValueError): pack.commit(altered, f, "")
            pack.commit(w, f, event["sentence"])

    def test_dialogue_rejects_remote_listener(self):
        _, w = setup("library", 7)
        w.entities["friend"].location = "outside"
        g = SpeechLanguage(w)
        with self.assertRaises(ValueError):
            g.line("hero", g.me(g.be("ready")), listener="friend")

    def test_contextual_answers_require_all_visible_evidence(self):
        row = generate("pottery", 7)
        design = next(q for q in questions(row, 50) if q["id"].endswith(":design"))
        self.assertGreaterEqual(len(design["evidence"]), 2)
        self.assertIn("thick", " ".join(e["text"] for e in design["evidence"]))
        broken = deepcopy(row)
        for scene in broken["scenes"]:
            scene["claims"] = [c for c in scene["claims"] if c["key"] != "inspection"]
        self.assertFalse(any(q["id"].endswith(":design") for q in questions(broken, 50)))
        broken = deepcopy(row)
        broken["scenes"][0]["claims"].append(deepcopy(broken["scenes"][0]["claims"][0]))
        with self.assertRaises(ValueError):
            questions(broken)

    def test_pinned_stories_and_full_qa(self):
        files = sorted(PINS.glob("*.json"))
        self.assertGreaterEqual(len(files), 7)
        for path in files:
            expected = json.loads(path.read_text())
            row = generate(expected["scenario"], expected["seed"])
            actual = dict(scenario=row["scenario"], seed=row["seed"], story=row["story"], qa=questions(row))
            self.assertEqual(actual, expected, path.name)


if __name__ == "__main__":
    unittest.main()
