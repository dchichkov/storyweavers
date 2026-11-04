"""Behavioral checks; literary evaluation is recorded separately in REVIEW.md."""
from copy import deepcopy
from dataclasses import asdict
import itertools
import json
import unittest

from .engine import Memeplex, Microdrama, StoryError, compose, digest, replay
from .palace import Parameters, build_world, library, practice, read_book
from .prose import narrate, render
from .qa import Conversation, questions
from .runtime import generate


def combinations():
    for values in itertools.product(("open", "locked"), (1, 2, 4), ("shared", "separate"), (True, False), (True, False)):
        yield Parameters(*values)


def expected_outcome(p):
    # Independent policy oracle derived from the authored scenario specification.
    if p.access == "locked" or p.attention == 4 or (p.attention == 2 and not p.mentor):
        return "closed_palace"
    return "library" if p.work == "shared" else "night_school"


def check_story(story):
    w = story.world
    assert w.state["valley.ended"]
    assert replay(w.initial, w.history) == w.state
    assert w.state["palace.outcome"] == expected_outcome(story.params)
    event_ids = {e.id for e in w.history}
    current = deepcopy(w.initial)
    snapshots = {}
    previous = set()
    for event in w.history:
        assert set(event.causes) <= previous
        current = replay(current, [event])
        w.validate(current)
        snapshots[event.id] = deepcopy(current)
        previous.add(event.id)
    for p in story.paragraphs:
        assert p.text.strip() and set(p.evidence) <= event_ids
    answers = questions(story)
    assert len({a.question for a in answers}) == len(answers)
    assert len({a.answer for a in answers}) == len(answers)
    for a in answers:
        assert a.answerable and a.facts and a.paragraphs
        assert len(a.answer.split()) >= 14 and a.answer.count(".") >= 2
        for fact in a.facts:
            assert snapshots[fact.event][fact.key] == fact.value
            assert any(fact.event in p.evidence and fact.key in p.reveals for p in story.paragraphs)
    assert story.episodes[0].id == "opening" and story.episodes[-1].id == "ending"
    assert "window" in story.paragraphs[-1].text or "rainwater" in story.paragraphs[-1].text
    return len(answers)


class AlgebraAndTransactions(unittest.TestCase):
    def setUp(self):
        self.w = build_world(Parameters())

    def test_content_composes_and_dilutes_without_effect_until_embedded(self):
        initial = digest(self.w.state)
        content = Memeplex.atom("Question", 2) + Memeplex.atom("Question", 1)
        content += Memeplex.atom("Curiosity", 2)
        self.assertEqual(digest(self.w.state), initial)
        self.w.act("test", "embed", ["mira"], lambda t: t.embed("mira", content / 2))
        self.assertEqual(self.w.state["mira.meme.Question"], 1.5)
        self.assertEqual(self.w.state["mira.meme.Curiosity"], 3)

    def test_invalid_algebra(self):
        for weight in (-1, float("inf"), float("nan")):
            with self.assertRaises(StoryError):
                Memeplex.atom("Question", weight)
        for divisor in (0, .5, -1, float("inf")):
            with self.assertRaises(StoryError):
                Memeplex.atom("Question") / divisor

    def test_unknown_carrier_rejected(self):
        with self.assertRaises(StoryError):
            self.w.act("test", "ghost", [], lambda t: t.embed("ghost", Memeplex.atom("Question")))
        self.assertEqual(self.w.state, self.w.initial)

    def test_action_rolls_back_effects_and_history(self):
        def fail(t):
            t.set("soup.lit", True)
            t.set("cottage.owner", "pigs")
        with self.assertRaises(StoryError):
            self.w.act("test", "illegal_seizure", ["pigs"], fail)
        self.assertEqual(self.w.state, self.w.initial)
        self.assertEqual(self.w.history, [])
        self.assertEqual(self.w.last_writer, {})

    def test_entire_encounter_rolls_back_after_second_action_fails(self):
        def bad(w, p):
            w.act("bad", "valid", ["wolf"], lambda t: t.set("soup.lit", True))
            w.act("bad", "invalid", ["wolf"], lambda t: t.set("wolf.location", "nowhere"))
        with self.assertRaises(StoryError):
            compose(self.w, [Microdrama("bad", lambda s: True, bad)], Parameters())
        self.assertEqual(self.w.state, self.w.initial)
        self.assertEqual(self.w.history, [])

    def test_remote_knowledge_does_not_teleport(self):
        with self.assertRaises(StoryError):
            self.w.act("test", "read_remote", ["mira"], lambda t: t.absorb("foundations", "mira"))
        self.assertEqual(self.w.state, self.w.initial)

    def test_encounter_rejects_unrecorded_effect(self):
        def bad(w, p):
            w.act("bad", "valid", ["wolf"], lambda t: t.set("soup.lit", True))
            w.state["valley.ended"] = True
        with self.assertRaises(StoryError):
            compose(self.w, [Microdrama("bad", lambda s: True, bad)], Parameters())
        self.assertEqual(self.w.state, self.w.initial)
        self.assertFalse(self.w.history)

    def test_locked_book_rejects_even_when_colocated(self):
        self.w.act("test", "approach", ["mira"], lambda t: t.move("mira", "depot"))
        before = deepcopy(self.w.state)
        with self.assertRaises(StoryError):
            self.w.act("test", "read_locked", ["mira"], lambda t: t.absorb("foundations", "mira"))
        self.assertEqual(self.w.state, before)

    def test_unobserved_fact_is_not_a_memory(self):
        with self.assertRaises(StoryError):
            self.w.act("test", "observe_remote", ["mira"], lambda t: t.observe("mira", "fox", "fox.took_cheese", "mira.saw_theft"))

    def test_duplicate_drama_ids_rejected(self):
        d = library(Parameters())[0]
        with self.assertRaises(StoryError):
            compose(self.w, [d, d], Parameters())


class StoryBehavior(unittest.TestCase):
    def test_determinism(self):
        self.assertEqual(generate(seed=17).bundle(), generate(seed=17).bundle())

    def test_false_beliefs_do_not_change_material_truth(self):
        s = generate()
        self.assertEqual([s.world.state[h + ".cause"] for h in ("straw", "wood", "brick")], ["wind", "mud", "bad_foundation"])
        rain = next(ep for ep in s.episodes if ep.id == "rain")
        self.assertEqual(rain.after["wolf.location"], "shore")
        self.assertTrue(s.world.state["pigs.blame_cheese"])
        self.assertTrue(s.world.state["fox.took_cheese"])

    def test_witness_changes_local_belief_without_persuading_everyone(self):
        s = generate(Parameters(witness=True))
        self.assertEqual(s.world.state["mira.meme.BlameWolf"], 0)
        self.assertEqual(s.world.state["tansy.meme.BlameWolf"], 3)
        self.assertTrue(s.world.state["pigs.blame_cheese"])
        self.assertTrue(s.world.state["mira.saw_theft"])

    def test_access_counterfactual(self):
        open_story, closed = generate(), generate(Parameters(access="locked"))
        self.assertEqual(open_story.world.state["palace.outcome"], "library")
        self.assertEqual(closed.world.state["palace.outcome"], "closed_palace")
        self.assertFalse(closed.world.state["mira.read"])
        self.assertFalse(closed.world.state["drain.tested"])

    def test_attention_and_mentoring_counterfactual(self):
        p = Parameters(attention=2)
        self.assertEqual(generate(p).world.state["palace.outcome"], "library")
        self.assertEqual(generate(Parameters(attention=2, mentor=False)).world.state["palace.outcome"], "closed_palace")
        self.assertEqual(generate(Parameters(attention=4)).world.state["palace.outcome"], "closed_palace")

    def test_private_skill_is_not_automatically_collective_power(self):
        s = generate(Parameters(work="separate"))
        self.assertTrue(s.world.state["mira.skilled"] and s.world.state["tansy.skilled"])
        self.assertFalse(s.world.state["palace.coalition"])
        self.assertEqual(s.world.state["palace.outcome"], "night_school")
        self.assertEqual(s.world.state["foundations.location"], "brick")
        self.assertTrue(s.world.state["foundations.accessible"])
        self.assertEqual(s.world.state["foundations.owner"], "pigs")
        self.assertTrue(s.world.state["wolf.coerced"])

    def test_restoration_requires_explicit_restitution(self):
        s = generate()
        before = s.episodes[-1].before
        self.assertEqual(before["cottage.occupant"], "pigs")
        self.assertFalse(before["wolf.free"])
        self.assertEqual(s.world.state["cottage.occupant"], "wolf")
        self.assertTrue(s.world.state["wolf.free"])
        self.assertEqual(s.world.state["cottage.owner"], "wolf")

    def test_skill_needs_a_physical_trial(self):
        s = generate()
        ep = next(ep for ep in s.episodes if ep.id == "practice_bridge")
        self.assertFalse(ep.before["tansy.skilled"])
        self.assertGreaterEqual(ep.before["tansy.meme.BridgeCraft"], 1.5)
        w = build_world(Parameters())
        w.state = deepcopy(ep.before)
        w.act("test", "widen_span", ["tansy"], lambda t: t.set("bridge.span", 4))
        practice("tansy", "bridge", "BridgeCraft")(w, Parameters())
        self.assertFalse(w.state["bridge.works"])
        self.assertFalse(w.state["tansy.skilled"])

    def test_same_reading_practice_binds_another_book(self):
        s = generate()
        ep = next(ep for ep in s.episodes if ep.id == "commission")
        w = build_world(Parameters())
        w.state = deepcopy(ep.after)
        w.act("test", "divide_attention", ["mira"], lambda t: t.set("mira.attention_divisor", 2))
        read_book("mira", "bridges")(w, Parameters(attention=2))
        self.assertEqual(w.state["mira.meme.BridgeCraft"], 1)
        self.assertEqual(w.state["mira.meme.DrainCraft"], 0)

    def test_optional_encounters_and_order_change(self):
        runs = [generate(seed=i) for i in range(10)]
        paths = {tuple(ep.id for ep in s.episodes) for s in runs}
        self.assertGreater(len(paths), 1)
        self.assertTrue(any("soup" not in path or "paper" not in path for path in paths))
        self.assertEqual({s.world.state["palace.outcome"] for s in runs}, {"library"})

    def test_replay_rejects_stale_base_and_changed_trace(self):
        s = generate()
        initial = deepcopy(s.world.initial); initial["valley.wind"] = 4
        with self.assertRaises(StoryError):
            replay(initial, s.world.history)
        events = [asdict(e) for e in s.world.history]
        events[0]["changes"]["soup.lit"]["after"] = False
        with self.assertRaises(StoryError):
            replay(s.world.initial, events)

    def test_narration_is_pure_and_historical(self):
        s = generate()
        before = digest(s.world.state)
        self.assertEqual(narrate(s.episodes, s.params), s.paragraphs)
        self.assertEqual(digest(s.world.state), before)
        self.assertEqual(narrate(s.episodes, Parameters(work="separate", attention=4)), s.paragraphs)
        s.world.state["cottage.occupant"] = "pigs"
        self.assertEqual(narrate(s.episodes, s.params), s.paragraphs)
        opening = render(s.episodes[0], s.params)
        self.assertFalse(opening[0].reveals)
        self.assertTrue(opening[-1].reveals)


class Questions(unittest.TestCase):
    def test_reader_cannot_see_a_future_theft(self):
        s = generate()
        before = next(i for i, p in enumerate(s.paragraphs) if p.drama == "fox")
        c = Conversation(s, "reader", before)
        self.assertFalse(c.ask("theft").answerable)
        self.assertTrue(Conversation(s, "world", before).ask("theft").answerable)

    def test_full_answers_have_real_historical_evidence(self):
        check_story(generate())
        c = Conversation(generate(), "reader")
        self.assertIn("shore", c.ask("wood").answer)

    def test_followup_focus_and_fail_closed(self):
        c = Conversation(generate(), "reader")
        self.assertFalse(c.ask("Why?").answerable)
        self.assertFalse(c.ask("Who will win the next election?").answerable)
        a = c.ask("drain"); b = c.ask("Why?")
        self.assertEqual(a.topic, b.topic)
        self.assertGreater(len(b.facts), len(a.facts))
        next_answer = c.ask("What happened next?")
        self.assertTrue(next_answer.answerable)
        self.assertNotEqual(c.event_focus, "practice_drain")
        c.ask("ending")
        self.assertFalse(c.ask("What happened next?").answerable)

    def test_next_does_not_leak_beyond_reading_position(self):
        s = generate()
        cutoff = max(i + 1 for i, p in enumerate(s.paragraphs) if p.drama == "wind")
        c = Conversation(s, "reader", cutoff)
        self.assertTrue(c.ask("straw").answerable)
        self.assertFalse(c.ask("What happened next?").answerable)

    def test_entire_finite_grid_and_unfiltered_seeds(self):
        for p in combinations():
            for seed in range(5):
                with self.subTest(parameters=asdict(p), seed=seed):
                    check_story(generate(p, seed))


if __name__ == "__main__":
    unittest.main()
