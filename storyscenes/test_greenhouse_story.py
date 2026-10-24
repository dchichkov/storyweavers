"""Resource and timing interventions on a stylized plant-care world."""
from dataclasses import replace
import unittest

from storyscenes.greenhouse_story import Conditions, generate, registry
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import execute, replay
from storyscenes.capabilities.reading import Reader


class GreenhouseStoryTests(unittest.TestCase):
    def setup_world(self, config):
        row, spec, state, doc = generate(config=config)
        engine = registry()
        actions = {a.id: a for a in spec.actions}
        return row, spec, state, doc, engine, actions

    def test_ten_seeds_have_replay_and_grounded_spans(self):
        for seed in range(10):
            row, spec, state, doc = generate(seed)
            self.assertEqual(replay(registry(), loads(registry(), dumps(spec)), row["path"]), state)
            anchors = {e.id for e in state.events} | {f"initial/{t}/{r.id}" for t, rs in spec.records.items() for r in rs}
            for statement, span in zip(doc.statements, doc.spans()):
                self.assertTrue(set(statement.event_ids) <= anchors)
                self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)
            self.assertGreaterEqual(len(row["qa"]), 6)
            self.assertEqual(len(row["qa"]), len({q["question"] for q in row["qa"]}))

    def test_opposite_soil_states_need_opposite_treatments(self):
        for wet, method in ((True, "drain"), (False, "water")):
            row, spec, state, _, eng, actions = self.setup_world(Conditions(wet=wet))
            before = eng.initial(spec)
            self.assertIsNone(execute(eng, spec, before, actions[method]))
            inspected = execute(eng, spec, before, actions["inspect_fern"])
            self.assertIsNone(execute(eng, spec, inspected, actions["water" if wet else "drain"]))
            self.assertEqual(state.get("plants", "fern").moisture, 1)
            self.assertTrue(state.get("plants", "fern").recovered)
            treated = execute(eng, spec, inspected, actions[method])
            again = replace(actions[method], id="again")
            spec = replace(spec, actions=spec.actions + (again,))
            self.assertIsNone(execute(eng, spec, treated, again))

    def test_water_conservation_including_soil_drainage_and_puddle(self):
        def total(state):
            return sum(state.get("garden_supplies", k).units for k in ("tap", "jug", "can", "drain_tray", "puddle")) + sum(p.moisture for p in state.tables["plants"].values())
        for c in (Conditions(wet=True), Conditions(full_can=False), Conditions(purpose="leak"), Conditions(purpose="leak", washer=False)):
            _, spec, state, _, eng, _ = self.setup_world(c)
            self.assertEqual(total(eng.initial(spec)), total(state))

    def test_non_water_supply_cannot_fill_can(self):
        _, spec, _, _, eng, actions = self.setup_world(Conditions(full_can=False))
        bad = replace(actions["fill"], id="bad_fill", args={"source": "washer"})
        spec = replace(spec, actions=spec.actions + (bad,))
        self.assertIsNone(execute(eng, spec, eng.initial(spec), bad))

    def test_stake_requires_length_and_cord_and_stays_attached(self):
        row, spec, state, _, eng, actions = self.setup_world(Conditions(purpose="support"))
        self.assertIn("support", row["path"])
        self.assertEqual(state.get("parents", "tall_stake").parent, "fern")
        self.assertEqual(state.get("garden_supplies", "cord").units, 0)
        before = replay(eng, spec, ["measure_stake"])
        self.assertIsNone(execute(eng, spec, before, actions["try_short"]))
        lifted = execute(eng, spec, state, actions["lift_fern_bench"])
        self.assertIsNotNone(lifted)
        self.assertEqual(lifted.get("parents", "tall_stake").parent, "fern")
        for c in (Conditions(purpose="support", tall_stake=False), Conditions(purpose="support", cord=False)):
            row, spec, state, _, eng, actions = self.setup_world(c)
            self.assertIn("put_fern_shelter", row["path"])
            before = replay(eng, spec, ["measure_stake"])
            self.assertIsNone(execute(eng, spec, before, actions["support"]))
            self.assertTrue(state.get("plants", "fern").recovered)

    def test_late_arrival_needs_real_lamp_charge(self):
        for charged in (True, False):
            row, spec, state, _, eng, actions = self.setup_world(Conditions(purpose="light", late_friend=True, charged_lamp=charged))
            before = replay(eng, spec, row["path"][:row["path"].index("put_ivy_sill") + 1])
            self.assertEqual(before.tick, 3)
            self.assertIsNone(execute(eng, spec, before, actions["sun_ivy"]))
            self.assertEqual(state.get("plants", "ivy").recovered, charged)
            self.assertEqual(state.get("garden_supplies", "lamp").units, 0)
            lit = execute(eng, spec, before, actions["lamp_ivy"])
            if charged:
                self.assertEqual(lit.tick, 5)
            else:
                self.assertIsNone(lit)

    def test_sill_capacity_and_inspection_reach_are_real(self):
        row, spec, _, _, eng, actions = self.setup_world(Conditions(purpose="light"))
        before = replay(eng, spec, row["path"][:row["path"].index("sun_fern")])
        holding = execute(eng, spec, before, actions["lift_ivy_bench"])
        self.assertIsNone(execute(eng, spec, holding, actions["put_ivy_sill"]))
        _, spec, _, _, eng, actions = self.setup_world(Conditions(purpose="light", late_friend=True))
        self.assertIsNone(execute(eng, spec, eng.initial(spec), actions["inspect_ivy"]))

    def test_recovery_requires_waiting_and_masking_removes_dependent_qa(self):
        _, spec, _, doc, eng, actions = self.setup_world(Conditions())
        self.assertIsNone(execute(eng, spec, eng.initial(spec), actions["morning"]))
        self.assertLess(len(Reader(doc.mask(["look"])).questions()), len(Reader(doc).questions()))

    def test_prose_variation_does_not_change_simulation(self):
        a, _, _, _ = generate(0, prose_seed=1)
        b, _, _, _ = generate(0, prose_seed=4)
        self.assertEqual(a["trace_sha256"], b["trace_sha256"])
        self.assertEqual(a["plot"], b["plot"])


if __name__ == "__main__":
    unittest.main()
