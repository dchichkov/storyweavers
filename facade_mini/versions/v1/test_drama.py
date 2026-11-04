"""Behavioral checks for causal agency, grounded state, and interruption safety."""
from copy import deepcopy
import random
import unittest

from content import BEATS, ENDINGS, EXCHANGES, INITIAL, MIXINS
from engine import Session, apply, matches, read, replay
from play import DEMOS, run_demo


def all_performances():
    for beat in BEATS:
        for goal in beat.goals:
            yield from goal.variants
    for tiers in MIXINS.values():
        for variants in tiers:
            yield from variants
    for exchange in EXCHANGES.values():
        yield from exchange.variants
    for _, variants, _ in ENDINGS:
        yield from variants


def assert_world(test, session):
    for who, prop in (("mara", "letter"), ("eli", "receipt")):
        person = session.state["people"][who]
        if person["disclosed"]:
            for observer in ("mara", "eli", "player"):
                test.assertTrue(session.state["people"][observer]["knows"][prop])
            test.assertEqual(session.state["props"][prop]["state"], "face_up")
        if person["accountable"]:
            test.assertTrue(person["disclosed"])
        for value in person["memes"].values():
            test.assertTrue(0 <= value <= 10)
        test.assertTrue(0 <= person["trust_player"] <= 10)
        test.assertTrue(0 <= person["trust_partner"] <= 10)
    for previous, current in zip(session.events, session.events[1:]):
        test.assertEqual(previous["after"], current["before"])
    if session.events:
        test.assertEqual(session.events[-1]["after"], session.snapshot())
    goals = [e["source"] for e in session.events if e["kind"] == "goal"]
    test.assertEqual(len(goals), len(set(goals)))


class DramaTests(unittest.TestCase):
    def test_authored_paths_exist_and_variants_have_defaults(self):
        self.assertEqual(len(BEATS), len({b.id for b in BEATS}))
        for performance in all_performances():
            matches(INITIAL, performance.when)
            state = deepcopy(INITIAL)
            for _, path, _ in performance.effects:
                read(state, path)
            apply(state, performance.effects)
            self.assertTrue(performance.lines)
        groups = [g.variants for b in BEATS for g in b.goals]
        groups += [v for tiers in MIXINS.values() for v in tiers]
        groups += [e.variants for e in EXCHANGES.values()]
        groups += [v for _, v, _ in ENDINGS]
        for group in groups:
            self.assertEqual(group[-1].when, ())
        for beat in BEATS:
            matches(INITIAL, beat.when)
        for exchange in EXCHANGES.values():
            for conditions, _, _ in exchange.influences:
                matches(INITIAL, conditions)

    def test_all_five_endings_have_reachable_witnesses(self):
        expected = {"repair": "repair", "distrust": "unresolved", "space": "space",
                    "silent": "unresolved", "ejected": "ejected", "leave": "left"}
        for name, outcome in expected.items():
            with self.subTest(name=name):
                session = run_demo(name)
                self.assertEqual(session.outcome, outcome)
                assert_world(self, session)
                self.assertEqual(replay(session.export()).export(), session.export())

    def test_earlier_attitude_changes_arc_with_same_later_commands(self):
        self.assertEqual(DEMOS["repair"][4:], DEMOS["distrust"][4:])
        warm, cold = run_demo("repair"), run_demo("distrust")
        self.assertEqual(warm.outcome, "repair")
        self.assertEqual(cold.outcome, "unresolved")
        self.assertNotIn("reckoning", warm.completed)
        self.assertIn("reckoning", cold.completed)
        self.assertTrue(warm.state["people"]["mara"]["accountable"])
        self.assertFalse(cold.state["people"]["mara"]["accountable"])

    def test_topic_changes_next_beat(self):
        selections = []
        for topic in ("letter", "receipt"):
            session = Session(4)
            session.start()
            session.step("listen")
            session.step("ask " + topic)
            session.step("listen")
            selections.append(session.active)
        self.assertEqual(selections, ["letter", "receipt"])

    def test_interrupt_resumes_pending_goal_exactly_once(self):
        session = Session()
        session.start()
        active, cursor = session.active, session.cursor
        session.step("ask letter")
        session.step("ask receipt")
        self.assertEqual((session.active, session.cursor), (active, cursor))
        session.step("listen")
        resumes = [e for e in session.events if e["kind"] == "resume"]
        self.assertEqual(len(resumes), 1)
        self.assertEqual(session.completed, ["arrival"])
        assert_world(self, session)

    def test_unknown_input_has_no_effect_or_clock_cost(self):
        session = Session()
        session.start()
        before = session.export()
        self.assertIn("isn't a supported action", session.step("don't support mara")[0])
        self.assertEqual(session.export(), before)

    def test_repeated_empathy_cannot_farm_trust(self):
        session = Session()
        session.start()
        session.step("empathize mara")
        trust = session.state["people"]["mara"]["trust_player"]
        for _ in range(4):
            session.step("empathize mara")
        self.assertEqual(session.state["people"]["mara"]["trust_player"], trust)
        self.assertEqual(sum(e["variant"] == "heard" for e in session.events), 1)

    def test_responsibility_requires_public_fact_and_willingness(self):
        session = Session()
        session.start()
        session.step("reflect mara")
        self.assertFalse(session.state["people"]["mara"]["accountable"])
        session.step("ask letter")
        session.step("ask letter")
        session.step("reflect mara")
        self.assertFalse(session.state["people"]["mara"]["accountable"])
        session.step("empathize mara")
        session.step("reflect mara")
        self.assertTrue(session.state["people"]["mara"]["accountable"])

    def test_no_unearned_mediation(self):
        session = Session()
        session.start()
        session.step("mediate")
        self.assertFalse(session.state["people"]["player"]["requested_talk"])
        self.assertNotEqual(session.phase(), "decision")

    def test_apology_needs_a_prior_harm_and_can_be_retried_after_one(self):
        session = Session()
        session.start()
        session.step("apologize")
        self.assertEqual(session.state["people"]["mara"]["trust_player"], 2)
        self.assertNotIn("apologize", session.used_exchanges)
        session.step("blame mara")
        self.assertEqual(session.state["people"]["mara"]["trust_player"], 0)
        session.step("apologize")
        self.assertEqual(session.state["people"]["mara"]["trust_player"], 1)
        self.assertIn("apologize", session.used_exchanges)

    def test_angry_refusal_does_not_consume_clue_and_deadline_still_ends(self):
        session = Session()
        session.start()
        for command in ("blame mara", "support eli", "provoke", "ask letter", "ask letter"):
            session.step(command)
        self.assertEqual(session.topic_tiers["letter"], 1)
        self.assertFalse(session.state["people"]["mara"]["disclosed"])
        while not session.outcome:
            session.step("ask letter")
        self.assertEqual(session.state["turn"], 24)
        self.assertEqual(session.outcome, "unresolved")
        self.assertFalse(session.state["people"]["mara"]["disclosed"])
        assert_world(self, session)

    def test_earned_mediation_can_abort_an_unfinished_argument(self):
        session = Session()
        session.start()
        for command in DEMOS["repair"][:-1]:
            session.step(command)
        session.step("listen")  # start the next topic before asking for agreement
        pending = session.active
        self.assertIsNotNone(pending)
        session.step("mediate")
        self.assertIn(pending, session.aborted)
        self.assertNotIn(pending, session.completed)
        self.assertEqual(session.active, "decision")
        self.assertFalse(session.interrupted)

    def test_second_insult_preempts_even_an_interrupted_beat(self):
        session = Session()
        session.start()
        session.step("provoke")
        session.step("ask photo")
        goal_count = sum(e["kind"] == "goal" for e in session.events)
        session.step("provoke")
        self.assertEqual(session.outcome, "ejected")
        self.assertEqual(goal_count, sum(e["kind"] == "goal" for e in session.events))
        before = session.export()
        session.step("empathize mara")
        self.assertEqual(before, session.export())

    def test_space_ending_moves_bag_key_and_character_together(self):
        session = run_demo("space")
        self.assertEqual(session.state["people"]["mara"]["location"], "hallway")
        self.assertEqual(session.state["props"]["bag"]["location"], "mara")
        self.assertEqual(session.state["props"]["key"]["location"], "mara_pocket")

    def test_seeded_random_play_terminates_and_keeps_invariants(self):
        for seed in range(150):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                session = Session(seed)
                session.start()
                # Include exits but don't let them dominate the traversal.
                actions = list(session.actions()) + ["listen"] * 8
                for _ in range(24):
                    if session.outcome:
                        break
                    session.step(rng.choice(actions))
                    assert_world(self, session)
                self.assertIsNotNone(session.outcome)
                self.assertLessEqual(session.state["turn"], 24)
                self.assertEqual(replay(session.export()).export(), session.export())


if __name__ == "__main__":
    unittest.main()
