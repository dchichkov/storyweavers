"""Readable prose must preserve execution and lose hidden reading evidence."""
from dataclasses import replace
import unittest

from storyscenes.capabilities.api import registry
from storyscenes.capabilities.core import execute, fingerprint, replay, solve
from storyscenes.capabilities.examples import action, delayed_report_story, loan_story, promise_story
from storyscenes.capabilities.reading import Reader
from storyscenes.capabilities.realize import render, render_story
from storyscenes.capabilities import story_examples


class CapabilityNarrativeTests(unittest.TestCase):
    def setUp(self):
        self.engine = registry()

    def test_story_is_shorter_without_mutating_trace_or_diagnostic_text(self):
        x = loan_story()
        state = replay(self.engine, x.spec, x.path)
        before = fingerprint(state)
        diagnostic = render(x.spec, state)
        story = render_story(x.spec, state)
        self.assertEqual(before, fingerprint(state))
        self.assertEqual(diagnostic, render(x.spec, state))
        self.assertLess(len(story.story.split()), .8 * len(diagnostic.story.split()))
        self.assertEqual(story.story.count("Inez still owned"), 1)
        self.assertEqual(story.story.count("remained responsible"), 1)
        self.assertNotIn("physically carried", story.story)
        self.assertIn("latch clicked shut", story.story)
        self.assertEqual(story.statements[-1].paragraph, "scene_ending")

    def test_omitted_snapshot_is_not_invisible_qa_evidence(self):
        x = loan_story()
        state = replay(self.engine, x.spec, x.path)
        self.assertTrue(Reader(render(x.spec, state)).ask("holder", "item", event_id="collect:1").supported)
        doc = render_story(x.spec, state)
        self.assertFalse(Reader(doc).ask("holder", "item", event_id="collect:1").supported)
        for answer in Reader(doc).questions():
            self.assertTrue(set(answer.statement_ids) <= {s.id for s in doc.statements})

    def test_reason_reply_target_masking_still_abstains(self):
        x = loan_story()
        doc = render_story(x.spec, replay(self.engine, x.spec, x.path))
        self.assertTrue(Reader(doc).ask("why", "RO").supported)
        for sid in ("decline:1/why/RO", "decline:1/response/RO", "return_offer:1/return_offer/RO"):
            self.assertFalse(Reader(doc.mask([sid])).ask("why", "RO").supported)

    def test_grouping_and_masking_preserve_exact_spans_and_visible_question_anchors(self):
        x = delayed_report_story()
        doc = render_story(x.spec, replay(self.engine, x.spec, x.path))
        for document in (doc, doc.mask([doc.statements[0].id])):
            for statement, span in zip(document.statements, document.spans()):
                self.assertEqual(document.story[span["start"]:span["end"]], statement.text)
            questions = Reader(document).questions()
            self.assertTrue(all("(In paragraph " in q.question for q in questions))
            self.assertFalse(any("(Event " in q.question for q in questions))
            self.assertEqual(len(questions), len({q.question for q in questions}))
            for answer in questions:
                number = int(answer.question.rsplit("paragraph ", 1)[1][:-2])
                self.assertLessEqual(number, len(document.story.split("\n\n")))

    def test_first_diagnostic_repeated_question_also_has_visible_anchor(self):
        x = delayed_report_story()
        doc = render(x.spec, replay(self.engine, x.spec, x.path))
        questions = [q.question for q in Reader(doc).questions() if "inspection establish" in q.question]
        self.assertEqual(len(questions), 2)
        self.assertTrue(all("paragraph" in q for q in questions))

    def test_repeated_physical_actions_get_distinct_visible_anchors(self):
        x = loan_story()
        doc = render_story(x.spec, replay(self.engine, x.spec, x.path))
        questions = [q.question for q in Reader(doc).questions()]
        self.assertEqual(len(questions), len(set(questions)))

    def test_partial_view_does_not_add_omniscient_opening_or_ending(self):
        x = loan_story()
        state = replay(self.engine, x.spec, x.path)
        doc = render_story(x.spec, state, visible={"deposit:1"})
        self.assertNotIn("scene_opening", {s.id for s in doc.statements})
        self.assertNotIn("scene_ending", {s.paragraph for s in doc.statements})
        self.assertFalse(Reader(doc).ask("promise_status", "P").supported)

    def test_stale_location_cannot_become_final_image(self):
        x = loan_story()
        close = action("shut_bag", "set_container", "borrower", container="bag", open=False)
        spec = replace(x.spec, actions=x.spec.actions + (close,))
        prefix = x.path[:x.path.index("outward")] + ("shut_bag", "outward")
        doc = render_story(spec, replay(self.engine, spec, prefix))
        endings = [s for s in doc.statements if s.paragraph == "scene_ending"]
        self.assertFalse(any(s.focus == "item" for s in endings))
        self.assertTrue(all(s.focus == "bag" for s in endings))

    def test_travel_does_not_reveal_a_hidden_pickup(self):
        x = loan_story()
        state = replay(self.engine, x.spec, x.path)
        doc = render_story(x.spec, state, visible={"outward:1"})
        self.assertNotIn("bag", doc.story)
        full = render_story(x.spec, state)
        self.assertFalse(Reader(full.mask(["lift:1/placement/bag"])).ask(
            "location", "borrower", event_id="outward:1").supported)

    def test_dialogue_uses_addressee_but_answers_name_the_recipient(self):
        x = promise_story()
        doc = render_story(x.spec, replay(self.engine, x.spec, x.path))
        self.assertIn('"Will you hand the star chart to me?" Vale asked Noor.', doc.story)
        self.assertIn('"I will hand the star chart to you," Noor told Vale.', doc.story)
        self.assertIn("to Vale", Reader(doc).ask("response", "R").answer)

    def test_old_handoff_before_promise_remains_legal_and_is_not_reordered(self):
        x = promise_story()
        path = ("ready", "handoff") + tuple(a for a in x.path if a not in {"ready", "handoff"})
        state = replay(self.engine, x.spec, path)
        doc = render_story(x.spec, state)
        self.assertLess(doc.story.index("Noor handed"), doc.story.index("I promise"))
        self.assertEqual(state.get("promises", "P").status, "breached")

    def test_story_profiles_reject_premature_actions_without_changing_engine_law(self):
        x = story_examples.promise_story()
        state = self.engine.initial(x.spec)
        ready = next(a for a in x.spec.actions if a.id == "ready")
        self.assertIsNone(execute(self.engine, x.spec, state, ready))
        for build in (story_examples.loan_story, story_examples.promise_story):
            x = build()
            replay(self.engine, x.spec, x.path)
            for seed in (0, 1, 42, 19245, 19287, 19564):
                state = solve(self.engine, x.spec, seed, max_nodes=6000)
                path = [e.action.id for e in state.events]
                self.assertEqual(state, replay(self.engine, x.spec, path))
                if build == story_examples.loan_story:
                    self.assertLess(path.index("homeward"), path.index("return_offer"))
                    self.assertLess(path.index("relift"), path.index("homeward"))
                    self.assertLess(path.index("promise"), path.index("pack"))
                else:
                    self.assertLess(path.index("accept"), path.index("promise"))
                    self.assertLess(path.index("promise"), path.index("handoff"))
                    self.assertLess(path.index("assess"), path.index("new_request"))


if __name__ == "__main__":
    unittest.main()
