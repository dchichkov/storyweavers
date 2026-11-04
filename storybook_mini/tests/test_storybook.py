from collections import Counter
from copy import deepcopy
from dataclasses import asdict, replace
import json
from pathlib import Path
import re
import tempfile
import unittest

from storybook_mini.content import STORIES, LANTERN, KITE, MINI_IDS
from storybook_mini.discourse import DiscourseHistory
from storybook_mini.experiment import (FACTORS, all_outputs, balanced_orders,
    export_comparison, make_study, summarize_ratings)
from storybook_mini.lexicon import choose_words
from storybook_mini.model import Entity, Fact, Story, simulate
from storybook_mini.pipeline import VERSIONS, CONFIGS, generate, content_roles
from storybook_mini.planning import plan_sentences
from storybook_mini.realization import realize
from storybook_mini.revision import revise


class ContentTests(unittest.TestCase):
    def test_all_ablations_preserve_content_and_input(self):
        for story in STORIES.values():
            world = simulate(story)
            original = deepcopy(asdict(world))
            for version in CONFIGS:
                result = generate(world, version)
                self.assertEqual(result["content_sha256"], world.fingerprint)
                self.assertEqual([fid for s in result["trace"]["sentences"] for fid in s["fact_ids"]],
                                 [f.id for f in story.facts])
                self.assertEqual(asdict(world), original)
                # Every entity role survives into the reference decisions, including ellipsis.
                for fact in story.facts:
                    refs = [(r["role"], r["entity"]) for r in result["trace"]["references"] if r["fact_id"] == fact.id]
                    self.assertEqual(Counter(refs), Counter(content_roles(fact)))

    def test_unembedded_concept_rejected(self):
        broken = replace(LANTERN, facts=(Fact("x", "home", "feel", "mara", value="Envy"),))
        with self.assertRaisesRegex(ValueError, "not been embedded"):
            simulate(broken)

    def test_missing_carrier_rejected(self):
        broken = replace(LANTERN, facts=(Fact("x", "home", "feel", "Fear", value="Fear"),))
        with self.assertRaisesRegex(ValueError, "ungrounded"):
            simulate(broken)

    def test_guard_rejects_incompatible_action(self):
        broken = replace(LANTERN, facts=tuple(f for f in LANTERN.facts if f.id != "l09"))
        with self.assertRaisesRegex(ValueError, "failed precondition"):
            simulate(broken)

    def test_invalid_causality_rejected(self):
        facts = (replace(LANTERN.facts[0], cause="l02"),) + LANTERN.facts[1:]
        with self.assertRaisesRegex(ValueError, "cause must precede"):
            simulate(replace(LANTERN, facts=facts))

    def test_descriptions_require_world_support(self):
        facts = tuple(replace(f, value="whole") if f.id == "k07" else f for f in KITE.facts)
        with self.assertRaisesRegex(ValueError, "contradicts"):
            simulate(replace(KITE, facts=facts))

    def test_emotion_wording_tracks_magnitude(self):
        # No text is rewritten: a changed embedded state changes the planned complement.
        facts = tuple(replace(f, meme_deltas=(("mara", "Fear", 0.3),)) if f.id == "l06"
                      else replace(f, meme_deltas=(("mara", "Fear", -0.3),)) if f.id == "l10"
                      else f for f in LANTERN.facts)
        text = generate(simulate(replace(LANTERN, facts=facts)))["text"]
        self.assertIn("felt uneasy", text)
        self.assertNotIn("felt afraid", text)

    def test_final_images_have_physical_support(self):
        lantern = simulate(LANTERN).final_state
        self.assertTrue(lantern["lantern"]["physical"]["lit"])
        self.assertEqual(lantern["lantern"]["physical"]["location"], "hook")
        kite = simulate(KITE).final_state
        self.assertTrue(kite["kite"]["physical"]["airborne"])
        self.assertEqual(kite["patch"]["physical"]["location"], "kite")

    def test_bad_role_fails_closed(self):
        facts = (replace(LANTERN.facts[0], object="lantern"),)
        with self.assertRaisesRegex(ValueError, "object role"):
            plan_sentences(simulate(replace(LANTERN, facts=facts)))


class PipelineTests(unittest.TestCase):
    def test_each_switch_has_an_observable_effect(self):
        for story in STORIES.values():
            outputs = {v: generate(simulate(story), v) for v in VERSIONS}
            self.assertEqual(len({r["text"] for r in outputs.values()}), 5)
            self.assertLess(outputs["full"]["metrics"]["sentences"],
                            outputs["no_revision"]["metrics"]["sentences"])
            self.assertGreater(outputs["full"]["metrics"]["pronouns"], 0)
            self.assertFalse(any(r["pronoun"] for r in outputs["no_discourse"]["trace"]["references"]
                                 if r.get("scope") == "narration" and r.get("reason") != "reflexive_binding"))
            self.assertGreater(outputs["full"]["metrics"]["verb_forms"],
                               outputs["no_lexical"]["metrics"]["verb_forms"])

    def test_one_switch_changes_at_a_time(self):
        full = asdict(VERSIONS["full"])
        for version, field in (("no_revision", "revision"), ("no_lexical", "lexical"),
                               ("no_discourse", "discourse")):
            delta = {k for k, v in asdict(VERSIONS[version]).items() if full[k] != v}
            self.assertEqual(delta, {field})

    def test_revision_never_crosses_scene_or_dialogue(self):
        for story in STORIES.values():
            clauses = choose_words(plan_sentences(simulate(story)))
            for sentence in revise(clauses):
                self.assertEqual(len({c.scene for c in sentence.clauses}), 1)
                if any(c.quote for c in sentence.clauses):
                    self.assertEqual(len(sentence.clauses), 1)
                if sentence.relation == "cause":
                    self.assertEqual(sentence.clauses[1].cause, sentence.clauses[0].fact_id)

    def test_first_and_subsequent_mentions(self):
        h = DiscourseHistory(LANTERN.entities)
        h.start_sentence("home")
        self.assertEqual(h.refer("hook", "target", "a"), "an iron hook")
        self.assertEqual(h.refer("hook", "target", "b"), "the iron hook")

    def test_competing_same_gender_blocks_pronoun(self):
        entities = (Entity("a", "girl", "Ada", "she"), Entity("b", "girl", "Bea", "she"))
        h = DiscourseHistory(entities)
        h.start_sentence("home")
        h.refer("a", "subject", "1")
        h.refer("b", "object", "1")
        h.end_sentence("a")
        h.start_sentence("home")
        self.assertEqual(h.refer("a", "subject", "2"), "Ada")

    def test_scene_and_dialogue_reset_subject_focus(self):
        for scene, dialogue in (("new", False), ("home", True)):
            h = DiscourseHistory(LANTERN.entities)
            h.start_sentence("home")
            h.refer("mara", "subject", "a")
            h.end_sentence("mara", dialogue)
            h.start_sentence(scene)
            self.assertEqual(h.refer("mara", "subject", "b"), "Mara")

    def test_revised_object_pronoun_is_unambiguous(self):
        text = generate(simulate(LANTERN))["text"]
        self.assertIn("lit the brass lantern and carried it", text)
        self.assertIn("shielded the brass lantern and kindled it", text)
        self.assertNotIn("Mara lit it", text)  # prior context includes two inanimate entities

    def test_direct_speech_and_final_images_survive_every_ablation(self):
        for story in STORIES.values():
            for version in VERSIONS:
                text = generate(simulate(story), version)["text"]
                for f in story.facts:
                    if f.predicate == "say" and f.value:
                        self.assertIn('“' + f.value[:-1], text)
                ending = "river landing." if story.id == "lantern" else (
                    "evening sky." if story.id == "kite" else "cellar steps.")
                self.assertTrue(text.endswith(ending))
                self.assertNotIn("  ", text)

    def test_pinned_full_outputs(self):
        root = Path(__file__).resolve().parents[1] / "examples"
        for story in STORIES.values():
            self.assertEqual(generate(simulate(story))["text"] + "\n",
                             (root / f"{story.id}.full.txt").read_text(encoding="utf-8"))


class StudyTests(unittest.TestCase):
    def test_order_position_and_carryover_balance(self):
        orders = balanced_orders(10, 20, 2001)
        self.assertEqual(orders, balanced_orders(10, 20, 2001))
        for order in orders:
            self.assertEqual(sorted(order), list(range(10)))
        for position in range(10):
            self.assertEqual(Counter(o[position] for o in orders), Counter({i: 2 for i in range(10)}))
        pairs = Counter((a, b) for order in orders for a, b in zip(order, order[1:]))
        self.assertEqual(len(pairs), 90)
        self.assertEqual(set(pairs.values()), {2})

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "study"
        self.manifest = make_study(self.path, participants=2)
        # Parse precisely the packet embedded in the local form.
        self.packets = [json.loads(re.search(r"const packet = (.*);\n", p.read_text()).group(1))
                        for p in sorted(self.path.glob("p*.html"))]

    def fill(self):
        # Synthetic fixtures ONLY to test arithmetic; never exported as human results.
        for packet in self.packets:
            for item in packet["items"]:
                version = self.manifest["participants"][packet["participant_id"]][item["item_id"]]["version"]
                item["ratings"] = dict.fromkeys(FACTORS, "A" if version == "full" else "C")
        return self.packets

    def test_packets_are_blinded_and_complete(self):
        for packet in self.packets:
            self.assertEqual(len(packet["items"]), 10)
            self.assertNotIn("version", json.dumps(packet))
            for item in packet["items"]:
                self.assertEqual(set(item["ratings"].values()), {""})

    def test_study_cannot_be_overwritten(self):
        with self.assertRaises(FileExistsError):
            make_study(self.path)

    def test_empty_results_make_no_quality_claim(self):
        result = summarize_ratings(self.manifest, [])
        self.assertEqual(result["participants"], 0)
        self.assertNotIn("means", result)

    def test_blank_ratings_rejected(self):
        with self.assertRaisesRegex(ValueError, "nine"):
            summarize_ratings(self.manifest, self.packets)

    def test_paired_analysis_counts_participants(self):
        result = summarize_ratings(self.manifest, self.fill())
        contrast = result["paired_contrasts"]["pooled"]["no_revision"]["overall"]
        self.assertEqual(contrast["full_minus_ablated"], 2)
        self.assertEqual(contrast["n_participants"], 2)
        self.assertEqual(contrast["participant_sd"], 0)

    def test_duplicate_participant_rejected(self):
        packets = self.fill()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            summarize_ratings(self.manifest, packets + packets[:1])

    def test_missing_reading_rejected(self):
        packets = self.fill()
        packets[0]["items"].pop()
        with self.assertRaisesRegex(ValueError, "missing"):
            summarize_ratings(self.manifest, packets)

    def test_tampered_text_rejected(self):
        packets = self.fill()
        packets[0]["items"][0]["text"] += " Extra event."
        with self.assertRaisesRegex(ValueError, "altered"):
            summarize_ratings(self.manifest, packets)


if __name__ == "__main__":
    unittest.main()
