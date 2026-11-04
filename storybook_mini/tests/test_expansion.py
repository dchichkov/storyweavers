"""Held-out linguistic cases, explicit failure cases and cross-layer invariants."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from storybook_mini.content import STORIES
from storybook_mini.discourse import DiscourseHistory
from storybook_mini.extended_content import borrowed_lamp
from storybook_mini.experiment import export_comparison, make_study
from storybook_mini.lexicon import LEXICON
from storybook_mini.model import Entity as E, Fact as F, Proposition as P, Story, simulate
from storybook_mini.morphology import verb_phrase
from storybook_mini.pipeline import CONFIGS, audit_realization, generate
from storybook_mini.story_io import save_story, load_story, story_from_dict
from dataclasses import asdict


def sample(facts, entities=None):
    entities = entities or (E("ada", "girl", "Ada", "she"), E("bea", "girl", "Bea", "she"),
        E("box", "wooden box", short_noun="box", state={"condition": "broken"}),
        E("basket", "wicker basket"), E("table", "table"))
    return simulate(Story("heldout", "Held-out linguistic case", tuple(entities), tuple(facts)))


class LinguisticTests(unittest.TestCase):
    def test_companion_is_grounded_and_does_not_receive_another_objects_relative_clause(self):
        world = sample((F("1", "a", "take", "ada", "box", companion="bea"),
                        F("2", "a", "be", "box", value="broken")))
        r = generate(world)
        self.assertIn("with Bea", r["text"])
        self.assertNotIn("relative", r["metrics"]["revision_rules"])
        self.assertTrue(any(ref["role"] == "companion" and ref["entity"] == "bea"
                            for ref in r["trace"]["references"]))

    def test_group_speaker_and_singular_they_have_correct_deixis(self):
        for number, expected in (("plural", "We are ready"), ("singular", "I am ready")):
            world = sample((F("1", "a", "say", "team", listener="ada",
                              speech=P("be", "team", value="ready")),), (
                E("team", "team", "Team", "they", number=number), E("ada", "girl", "Ada", "she")))
            self.assertIn(expected, generate(world)["text"])

    def test_relative_clause_requires_explicit_description(self):
        world = sample((F("1", "a", "find", "ada", "box"), F("2", "a", "be", "box", value="broken")))
        self.assertIn("box, which was broken", generate(world)["text"])
        self.assertEqual(generate(world)["metrics"]["revision_rules"], {"relative": 1})
        self.assertIn("The box was broken.", generate(world, "no_revision")["text"])

    def test_relative_cannot_modify_the_wrong_last_noun(self):
        world = sample((F("1", "a", "put", "ada", "box", "table"), F("2", "a", "be", "box", value="broken")))
        self.assertNotIn("relative", generate(world)["metrics"]["revision_rules"])

    def test_shared_verb_preserves_both_objects(self):
        world = sample((F("1", "a", "take", "ada", "box"), F("2", "a", "take", "ada", "basket")))
        r = generate(world)
        self.assertEqual(r["text"], "Ada took a wooden box and a wicker basket.")
        self.assertEqual(r["metrics"]["revision_rules"], {"shared_verb": 1})

    def test_negative_objects_are_not_collapsed_into_ambiguous_scope(self):
        world = sample((F("1", "a", "take", "ada", "box", negative=True),
                        F("2", "a", "take", "ada", "basket", negative=True)))
        self.assertNotIn("shared_verb", generate(world)["metrics"]["revision_rules"])
        self.assertIn("did not take", generate(world)["text"])

    def test_contrast_markers_are_chosen_with_revision(self):
        world = sample((F("1", "a", "want", "ada", goal=P("open", "ada", "box")),
                        F("2", "a", "open", "ada", "box", negative=True, contrast="1")))
        self.assertIn(", but did not open", generate(world)["text"])
        self.assertIn("However,", generate(world, "no_revision")["text"])
        self.assertNotIn("but", generate(world, "no_markers")["text"])
        self.assertNotIn("However", generate(world, "no_markers")["text"])

    def test_no_causal_marker_without_authored_link(self):
        world = sample((F("1", "a", "open", "ada", "box"), F("2", "a", "smile", "bea")))
        self.assertEqual(generate(world)["metrics"]["markers"], 0)

    def test_wants_do_not_execute_their_goal(self):
        world = sample((F("1", "a", "want", "ada", goal=P("open", "ada", "box")),))
        self.assertIn("wanted to open", generate(world)["text"])
        self.assertEqual(world.final_state["box"]["physical"], {"condition": "broken"})

    def test_structured_dialogue_tracks_speaker_and_hearer(self):
        world = sample((F("1", "a", "say", "ada", listener="bea", speech=P("thank", "ada", "bea")),))
        self.assertEqual(generate(world)["text"], '“I thank you,” Ada said to Bea.')
        # Deixis is necessary grammar and survives removing narrative discourse history.
        self.assertEqual(generate(world, "no_discourse")["text"], '“I thank you,” Ada said to Bea.')

    def test_dialogue_future_does_not_perform_transfer(self):
        entities = (E("ada", "girl", "Ada", "she"), E("bea", "girl", "Bea", "she"),
                    E("box", "box", state={"owner": "bea"}))
        world = sample((F("1", "a", "say", "ada", listener="bea",
                          speech=P("return", "ada", "box", "bea", tense="future")),), entities)
        self.assertIn("I will return your box to you", generate(world)["text"])
        self.assertEqual(world.final_state["box"]["physical"]["owner"], "bea")

    def test_ownership_and_custody_are_distinct_in_prose(self):
        world = simulate(STORIES["lamp_supper"])
        lending = next(h for h in world.history if h["fact"]["predicate"] == "lend")
        self.assertEqual(lending["after"]["lamp"]["physical"]["owner"], "iris")
        self.assertEqual(lending["after"]["lamp"]["physical"]["custodian"], "nell")
        self.assertIn("I will return your lamp to you", generate(world)["text"])
        self.assertNotIn("Nell’s lamp", generate(world)["text"])

    def test_same_gender_competitor_survives_one_interruption(self):
        h = DiscourseHistory(sample((F("1", "a", "smile", "ada"),)).story.entities)
        for refs, subject in ((("ada", "bea"), "ada"), (("ada", "box"), "ada")):
            h.start_sentence("room")
            for i, eid in enumerate(refs):
                h.refer(eid, "subject" if i == 0 else "object", "x")
            h.end_sentence(subject)
        h.start_sentence("room")
        self.assertEqual(h.refer("ada", "subject", "y"), "Ada")
        self.assertIn("bea", h.choices[-1]["rivals"])

    def test_object_pronouns_cannot_leak_across_scene_boundary(self):
        world = sample((F("1", "a", "take", "ada", "box"), F("2", "b", "open", "ada", "box")))
        self.assertIn("Ada opened the box.", generate(world)["text"])
        self.assertNotIn("opened it", generate(world)["text"])

    def test_reflexives_follow_binding_even_without_discourse(self):
        world = sample((F("1", "a", "look", "ada", "ada"),))
        for version in CONFIGS:
            self.assertIn("looked at herself", generate(world, version)["text"])

    def test_mass_and_plural_nouns_and_agreement(self):
        entities = (E("oil", "lamp oil", mass=True),
                    E("boards", "boards", pronoun="they", number="plural", state={"condition": "wet"}),
                    E("ada", "girl", "Ada", "she"))
        world = sample((F("1", "a", "have", "ada", "oil"), F("2", "b", "be", "boards", value="wet")), entities)
        self.assertIn("some lamp oil", generate(world)["text"])
        self.assertIn("Some boards were wet.", generate(world)["text"])

    def test_tense_and_polarity_are_realized_from_structures(self):
        cases = [("be", "present", False, 1, False, "am"),
                 ("be", "past", True, 3, True, "were not"),
                 ("give", "past_perfect", False, 3, False, "had given"),
                 ("extinguish", "past_perfect", False, 3, False, "had blown out"),
                 ("carry", "present", False, 3, False, "carries"),
                 ("have", "present", True, 3, False, "does not have"),
                 ("take", "future", True, 1, False, "will not take")]
        for predicate, tense, negative, person, plural, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(verb_phrase(LEXICON[predicate][0], tense, negative,
                                             person=person, plural=plural), expected)

    def test_topic_break_blocks_aggregation(self):
        world = sample((F("1", "a", "take", "ada", "box", topic="packing"),
                        F("2", "a", "take", "ada", "basket", topic="leaving")))
        r = generate(world)
        self.assertEqual(r["metrics"]["aggregations"], 0)
        self.assertEqual(r["trace"]["sentences"][1]["break_reason"], "topic_change")

    def test_paragraph_control_preserves_sentence_content(self):
        world = simulate(STORIES["lamp_supper"])
        full, flat = generate(world), generate(world, "no_organization")
        self.assertEqual(full["text"].replace("\n\n", " "), flat["text"])
        self.assertEqual(flat["metrics"]["paragraphs"], 1)
        self.assertGreater(full["metrics"]["paragraphs"], 1)


class IntegrityTests(unittest.TestCase):
    def test_json_roundtrip_preserves_fingerprint_and_all_seven_tellings(self):
        with tempfile.TemporaryDirectory() as temp:
            for story in STORIES.values():
                path = Path(temp) / "content.json"
                save_story(path, story)
                original, loaded = simulate(story), simulate(load_story(path))
                self.assertEqual(original.fingerprint, loaded.fingerprint)
                for version in CONFIGS:
                    self.assertEqual(generate(original, version), generate(loaded, version))

    def test_json_rejects_unknown_schema_fields(self):
        data = asdict(STORIES["lamp_return"])
        data["execute"] = "arbitrary code"
        with self.assertRaisesRegex(ValueError, "Story JSON"):
            story_from_dict(data)

    def test_structural_audit_detects_a_dropped_embedded_role(self):
        world = simulate(STORIES["lamp_supper"])
        r = generate(world)
        refs = [ref for ref in r["trace"]["references"] if ref["role"] != "goal.object"]
        with self.assertRaisesRegex(ValueError, "semantic role"):
            audit_realization(world, r["trace"]["sentences"], refs)

    def test_descriptions_cannot_smuggle_in_physical_actions(self):
        with self.assertRaisesRegex(ValueError, "cannot change"):
            sample((F("1", "a", "be", "box", value="broken", effects=(("box", "owner", "ada"),)),))

    def test_negated_actions_cannot_smuggle_in_success_effects(self):
        with self.assertRaisesRegex(ValueError, "cannot change"):
            sample((F("1", "a", "open", "ada", "box", negative=True,
                       effects=(("box", "open", True),)),))

    def test_unknown_embedded_entity_and_invalid_goal_binding_fail_closed(self):
        for prop, error in ((P("bake", "ada", "missing"), "ungrounded"),
                            (P("bake", "bea", "box"), "bind")):
            with self.assertRaisesRegex(ValueError, error):
                sample((F("1", "a", "want", "ada", goal=prop),))

    def test_two_outcomes_preserve_the_owners_real_need(self):
        for fuel in (1, 3):
            world = simulate(borrowed_lamp(fuel))
            state = world.final_state
            self.assertEqual(state["loaf"]["physical"]["baked"], fuel == 3)
            self.assertEqual(state["lamp"]["physical"]["fuel"], 1)
            self.assertEqual(state["lamp"]["physical"]["owner"], "iris")
            self.assertEqual(state["lamp"]["physical"]["custodian"], "iris")
            self.assertFalse(state["lamp"]["physical"]["return_due"])
            self.assertTrue(state["lamp"]["physical"]["lit"])
            self.assertEqual(state["iris"]["physical"]["location"], "steps")

    def test_export_contains_both_added_controls_and_inspection_view(self):
        with tempfile.TemporaryDirectory() as temp:
            outputs = export_comparison(Path(temp), ("lamp_return",))
            self.assertEqual({r["version"] for r in outputs}, set(CONFIGS))
            html = (Path(temp) / "research.html").read_text()
            self.assertIn("speech.subject", html)
            self.assertIn("no_organization", html)
            self.assertIn("active_conversation", html)


if __name__ == "__main__":
    unittest.main()
