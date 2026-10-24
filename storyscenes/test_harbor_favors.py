from dataclasses import replace
from itertools import permutations, product
import unittest

from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import Action, CapabilityError, Entity, execute, matches, replay
from storyscenes.capabilities.physical import Route
from storyscenes.capabilities.reading import Reader
from storyscenes.harbor_favors_story import ACTORS, POLICIES, Conditions, build, generate, registry, waiting_cycle


class HarborFavorTests(unittest.TestCase):
    def test_ownership_policy_grid_has_exact_json_replay_and_settled_loans(self):
        reg = registry()
        for owners, policies in product(permutations(ACTORS), product(POLICIES, repeat=3)):
            with self.subTest(owners=owners, policies=policies):
                row, spec, state, doc = generate(config=Conditions(owners=owners, policies=policies))
                self.assertEqual(replay(reg, loads(reg, dumps(spec)), row["path"]), state)
                self.assertTrue(all(matches(state, q) for q in spec.goal))
                self.assertTrue(all(loan.status == "discharged" for loan in state.tables["loans"].values()))
                self.assertEqual({t: state.get("parents", t).parent for t in ("rope", "scissors", "lantern")},
                                 dict(zip(("rope", "scissors", "lantern"), owners)))
                self.assertGreaterEqual(len(Reader(doc).questions()), 3)

    def test_three_way_cycle_stays_unfinished_when_everyone_insists_on_first(self):
        row, _, state, _ = generate(config=Conditions(policies=("work_first",) * 3))
        self.assertEqual(row["plot"]["outcome"], "waiting")
        self.assertEqual(len(waiting_cycle(state)), 3)
        self.assertFalse(state.tables["loans"])
        self.assertFalse(state.tables["favor_results"])
        self.assertNotIn("could not be lent", row["story"])

    def test_one_reciprocal_choice_changes_all_three_physical_results(self):
        blocked, _, _, _ = generate(config=Conditions(policies=("work_first",) * 3))
        row, _, state, _ = generate(config=Conditions(policies=("reciprocate", "work_first", "work_first")))
        self.assertEqual(row["plot"]["completed_projects"], ["cy", "bo", "ari"])
        self.assertEqual(row["plot"]["changed_priority"], ["ari"])
        self.assertEqual(row["plot"]["waiting_replies"], 3)
        self.assertIn("I do not have to be first", row["story"])
        self.assertNotIn("I can be second", row["story"])
        self.assertTrue(all(inquiry.heard_by == ACTORS for inquiry in state.tables["favor_inquiries"].values()))
        self.assertNotEqual(blocked["trace_sha256"], row["trace_sha256"])
        self.assertEqual(state.get("parents", "boat_ari").parent, "tub_ari")
        self.assertTrue(state.get("containers", "parcel_bo").open)
        self.assertEqual(state.get("evidence", "reading_cy").outcome, "exact")

    def test_lend_first_does_not_fabricate_completion_of_the_lenders_job(self):
        row, _, state, _ = generate(config=Conditions(policies=("work_first", "lend_first", "work_first")))
        self.assertEqual(row["plot"]["completed_projects"], ["ari"])
        self.assertFalse(state.get("containers", "parcel_bo").open)
        self.assertEqual(row["plot"]["waiting_replies"], 0)

    def test_completed_initial_state_cannot_replace_enacted_work(self):
        c = Conditions(projects=("flags",) * 3, owners=("ari",) * 3)
        spec = build(c)
        records = dict(spec.records)
        records["containers"] = tuple(replace(r, open=True) for r in records["containers"])
        spec = replace(spec, records=records)
        state = registry().initial(spec)
        done = next(a for a in spec.actions if a.id == "done_ari")
        self.assertIsNone(execute(registry(), spec, state, done))

    def test_relaxation_needs_an_enacted_cycle_not_a_policy_flag(self):
        spec = build(Conditions(policies=("reciprocate",) * 3))
        state = registry().initial(spec)
        relax = next(a for a in spec.actions if a.id == "relax_ari")
        self.assertIsNone(execute(registry(), spec, state, relax))

    def test_meeting_after_separate_replies_does_not_create_shared_knowledge(self):
        spec = build(Conditions(policies=("reciprocate", "work_first", "work_first")))
        records = dict(spec.records)
        records["entities"] += (Entity(id="outside", kind="place", name="outside"),)
        records["parents"] = tuple(replace(p, parent="outside") if p.id == "cy" else p for p in records["parents"])
        records["routes"] = (Route(id="in", source="outside", destination="workshop"),
                             Route(id="out", source="workshop", destination="outside"))
        travel = tuple(Action(id=f"{actor}_{route}", operation="travel", actor=actor, args={"route": route})
                       for actor, route in (("cy", "in"), ("ari", "out"), ("ari", "in")))
        spec = replace(spec, records=records, actions=spec.actions + travel)
        path = ("ask_ari_1", "reply_ari_1", "cy_in", "ari_out", "ask_bo_1", "reply_bo_1",
                "ari_in", "ask_cy_1", "reply_cy_1")
        reg = registry()
        state = replay(reg, spec, path)
        self.assertEqual(len(waiting_cycle(state)), 3)
        self.assertEqual(state.get("favor_inquiries", "ari_1").heard_by, ("ari", "bo"))
        self.assertEqual(state.get("favor_inquiries", "bo_1").heard_by, ("bo", "cy"))
        self.assertEqual(state.get("favor_inquiries", "cy_1").heard_by, ACTORS)
        relax = next(a for a in spec.actions if a.id == "relax_ari")
        self.assertIsNone(execute(reg, spec, state, relax))
        renewed = path + ("ask_ari_2", "reply_ari_2", "ask_bo_2", "reply_bo_2")
        informed = replay(reg, spec, renewed)
        self.assertIsNotNone(execute(reg, spec, informed, relax))

    def test_loan_cannot_be_offered_before_the_owner_replies_ready(self):
        row, spec, _, _ = generate(config=Conditions(policies=("work_first", "lend_first", "work_first")))
        state = replay(registry(), spec, ("ask_ari_1",))
        offer = next(a for a in spec.actions if a.id == "offer_ari_1")
        self.assertIsNone(execute(registry(), spec, state, offer))
        state = replay(registry(), spec, ("ask_ari_1", "reply_ari_1"))
        self.assertIsNotNone(execute(registry(), spec, state, offer))

    def test_return_offer_is_not_settlement(self):
        row, spec, _, _ = generate(config=Conditions(policies=("work_first", "lend_first", "work_first")))
        path = row["path"][:row["path"].index("return_ari")]
        state = replay(registry(), spec, path)
        finish = next(a for a in spec.actions if a.id == "finish")
        self.assertEqual(state.get("loans", "loan_ari").status, "active")
        self.assertIsNone(execute(registry(), spec, state, finish))

    def test_work_cannot_be_completed_before_actual_use(self):
        row, spec, _, _ = generate(config=Conditions(policies=("work_first", "lend_first", "work_first")))
        state = replay(registry(), spec, row["path"][:row["path"].index("open_ari")])
        done = next(a for a in spec.actions if a.id == "done_ari")
        self.assertIsNone(execute(registry(), spec, state, done))

    def test_requests_require_colocation(self):
        spec = build(Conditions())
        records = dict(spec.records)
        records["entities"] += (Entity(id="outside", kind="place", name="outside"),)
        records["parents"] = tuple(replace(p, parent="outside") if p.id == "bo" else p for p in records["parents"])
        spec = replace(spec, records=records)
        ask = next(a for a in spec.actions if a.id == "ask_ari_1")
        self.assertIsNone(execute(registry(), spec, registry().initial(spec), ask))

    def test_masking_keeps_answers_anchored_to_the_visible_sequence(self):
        row, _, state, doc = generate(config=Conditions())
        self.assertFalse(Reader(doc.mask(("opening",))).questions())
        event_ids = {e.id for e in state.events} | {"initial/favor_projects/ari"}
        for statement, span in zip(doc.statements, doc.spans()):
            self.assertTrue(set(statement.event_ids) <= event_ids)
            self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)
        self.assertNotIn("scissors was", row["story"])

    def test_no_preloaded_favor_history(self):
        _, spec, state, _ = generate(config=Conditions())
        records = dict(spec.records, favor_results=tuple(state.tables["favor_results"].values()))
        with self.assertRaisesRegex(CapabilityError, "enacted"):
            registry().initial(replace(spec, records=records))

    def test_same_project_types_still_refer_to_distinct_physical_artifacts(self):
        row, _, state, doc = generate(config=Conditions(projects=("flags",) * 3,
            owners=("bo", "bo", "cy"), policies=("work_first",) * 3))
        self.assertTrue(state.get("containers", "parcel_bo").open)
        self.assertTrue(state.get("containers", "parcel_ari").open)
        self.assertFalse(state.get("containers", "parcel_cy").open)
        self.assertIn("Bo's parcel", row["story"])
        self.assertIn("Ari's own flags", row["story"])
        self.assertIn("my paper flags", row["story"])
        first = next(s.text for s in doc.statements if s.id == "done_bo:1")
        second = next(s.text for s in doc.statements if s.id == "done_ari:1")
        self.assertLess(len(second), len(first))


if __name__ == "__main__":
    unittest.main()
