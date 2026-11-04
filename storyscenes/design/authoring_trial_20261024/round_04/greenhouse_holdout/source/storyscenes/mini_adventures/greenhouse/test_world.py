from copy import deepcopy
from dataclasses import replace
from itertools import product
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from storyscenes.runtime import StoryError, transition
from storyscenes.mini_adventures.local_play import LocalPlay as AtomicLocalPlay
from .world import Parameters, SCENES, LocalPlay, generate, guard, initial, play_scene, replay, validate


class GreenhouseTests(unittest.TestCase):
    def test_local_adapter_delegates_atomic_actions(self):
        self.assertTrue(issubclass(LocalPlay, AtomicLocalPlay))
        self.assertIs(LocalPlay.act, AtomicLocalPlay.act)
        source = initial(Parameters())
        saved = deepcopy(source)
        x = LocalPlay(source)
        with patch("storyscenes.mini_adventures.local_play.transition", wraps=transition) as call:
            x.act("clear_gate_stone", {"gate.stone": True}, **{"gate.stone": False})
        self.assertEqual(call.call_count, 1)
        self.assertEqual(call.call_args.args[1].actors, ("mara", "ivo"))
        self.assertEqual(source, saved)
        self.assertEqual(x.events, [{"action": "clear_gate_stone", "requires": {"gate.stone": True},
                                   "changes": {"gate.stone": {"before": True, "after": False}}}])
        before, events = deepcopy(x.state), deepcopy(x.events)
        with self.assertRaises(StoryError):
            x.act("invent_tea", **{"cups.filled": True})
        self.assertEqual(x.state, before)
        self.assertEqual(x.events, events)

    def test_local_adapter_rejects_invalid_initial_state(self):
        source = initial(Parameters())
        source["cups.filled"] = True
        saved = deepcopy(source)
        with self.assertRaisesRegex(StoryError, "Tea must remain"):
            LocalPlay(source)
        self.assertEqual(source, saved)

    def check(self, row):
        p = Parameters(**row["parameters"])
        self.assertEqual(replay(p, row["path"]), row["episodes"])
        self.assertEqual(len(row["path"]), row["scene_count"])
        self.assertEqual(len(row["path"]), len(set(row["path"])))
        self.assertEqual(row["story"], "\n\n".join(e["text"] for e in row["episodes"]))
        state = initial(p)
        for e in row["episodes"]:
            self.assertEqual(e["before"], state)
            self.assertTrue(guard(e["id"], state))
            for event in e["events"]:
                for k, v in event["requires"].items():
                    self.assertEqual(state[k], v)
                self.assertTrue(event["changes"])
                for k, change in event["changes"].items():
                    self.assertEqual(state[k], change["before"])
                    state[k] = deepcopy(change["after"])
                validate(state)
            self.assertEqual(e["after"], state)
            self.assertGreaterEqual(len(e["text"].split()), 40)
            self.assertLessEqual(len(e["text"].split()), 75)
        self.assertEqual(state, row["final_state"])
        self.assertTrue(state["story.ended"])
        json.dumps(row, allow_nan=False)

    def test_hundred_seeds_both_lengths(self):
        seen, outcomes = set(), set()
        for seed, count in product(range(100), (7, 8)):
            row = generate(seed, count=count)
            self.check(row)
            seen.update(row["path"])
            outcomes.add(row["final_state"]["story.outcome"])
            self.assertEqual(row, generate(seed, count=count))
        self.assertEqual(seen, set(SCENES))
        self.assertEqual(outcomes, {"joint_care", "supervised_trial", "separation"})

    def test_full_parameter_grid(self):
        for i, values in enumerate(product(("wind", "heat"), (True, False), (True, False),
                                           (True, False), (True, False), ("patch", "shelter"))):
            p = Parameters(**dict(zip(("weather", "tape", "damp_seeds", "honest", "receptive", "strategy"), values)))
            for count in (7, 8):
                self.check(generate(i, params=p, count=count))

    def test_atomic_rejection_and_impossible_actions(self):
        p = Parameters()
        s = initial(p)
        saved = deepcopy(s)
        for sid in set(SCENES) - {"gate"}:
            with self.assertRaises(StoryError):
                play_scene(p, s, sid)
            self.assertEqual(s, saved)
        x = LocalPlay(s)
        with self.assertRaises(StoryError):
            x.act("teleport", {"door.open": True}, **{"party.location": "inside"})
        self.assertEqual(x.state, saved)
        with self.assertRaises(StoryError):
            replay(p, ["gate", "measuring", "measuring"])

    def test_omitted_vignettes_do_not_run(self):
        row = generate(0, count=7, params=Parameters())
        s = row["final_state"]
        self.assertFalse(s["mara.remembers_height"])
        self.assertEqual(s["snail.location"], "pot_rim")
        self.assertTrue(s["flask.full"])
        self.assertTrue(s["flask.capped"])
        self.assertFalse(s["cups.filled"])
        self.assertEqual(s["tea.servings_drunk"], 0)
        self.assertFalse(s["ledger.written"])
        self.assertNotIn("notebook", row["story"])

    def test_tape_changes_later_seed_carrier(self):
        p = Parameters(tape=False)
        without = generate(1, count=7, params=p)
        with_tape = generate(1, count=7, params=replace(p, tape=True))
        self.assertIn("patch_parcel", without["path"])
        self.assertIn("patch_tape", with_tape["path"])
        self.assertEqual(without["final_state"]["parcel.location"], "vent")
        self.assertEqual(with_tape["final_state"]["parcel.location"], "bench")
        self.assertIn("from the sandwich tin", without["story"])
        self.assertIn("from the parcel she opened", with_tape["story"])
        patch = next(e for e in without["episodes"] if e["id"] == "patch_parcel")
        self.assertIn("test_tape_roll", [e["action"] for e in patch["events"]])

    def test_honesty_and_damage_change_outcome(self):
        p = Parameters()
        good = generate(2, count=7, params=p)
        for changed in (replace(p, damp_seeds=True), replace(p, strategy="shelter"), replace(p, receptive=False)):
            row = generate(2, count=7, params=changed)
            self.assertEqual(row["final_state"]["story.outcome"], "supervised_trial")
            self.assertEqual(row["final_state"]["key.owner"], "ivo")
        lost = generate(2, count=7, params=replace(p, honest=False))
        self.assertEqual(lost["final_state"]["story.outcome"], "separation")
        self.assertEqual(lost["final_state"]["beans.location"], "mara_pocket")
        self.assertEqual(good["final_state"]["story.outcome"], "joint_care")
        self.assertEqual(good["final_state"]["key.owner"], "mara")

    def test_damaged_tomatoes_do_not_earn_repair_dialogue(self):
        row = generate(822263078, count=7)
        self.assertEqual(row["final_state"]["tomatoes.state"], "damaged")
        self.assertNotIn("That was help", row["story"])
        self.assertIn("You kept the present", row["story"])

    def test_missing_seeds_cannot_be_sown(self):
        row = generate(0, count=7, params=Parameters())
        s = deepcopy(next(e["before"] for e in row["episodes"] if e["id"] == "sow"))
        s["tin.location"] = "elsewhere"
        saved = deepcopy(s)
        with self.assertRaises(StoryError):
            play_scene(Parameters(), s, "sow")
        self.assertEqual(s, saved)

    def test_shelter_is_a_declined_repair_not_a_damage_switch(self):
        for weather, tape in product(("wind", "heat"), (False, True)):
            p = Parameters(weather=weather, tape=tape, strategy="shelter")
            row = generate(0, count=7, params=p)
            e = next(e for e in row["episodes"] if e["id"] == "shelter")
            actions = [event["action"] for event in e["events"]]
            choice = "decline_tape_repair" if tape else "decline_unwrapping_parcel"
            self.assertLess(actions.index("consider_tape_repair"), actions.index(choice))
            self.assertLess(actions.index("inspect_notched_wooden_stay"), actions.index(choice))
            shelter = next(event for event in e["events"] if event["action"] == "shelter_parcel")
            self.assertEqual(set(shelter["changes"]), {"parcel.location"})
            self.assertEqual(e["after"]["tape.available"], tape)
            self.assertEqual(e["after"]["stay.location"], "shelf")
            self.assertEqual(e["after"]["beans.location"], "parcel")
            self.assertEqual(e["after"]["parcel.location"], "under_bench")
            self.assertIn("Moving them will be quicker", e["text"])
            self.assertIn("tape" if tape else "parcel string", e["text"])

    def test_mara_proposes_and_ivo_joins_the_mistaken_choice(self):
        for weather, tape in product(("wind", "heat"), (False, True)):
            row = generate(0, count=7, params=Parameters(weather=weather, tape=tape, strategy="shelter"))
            e = next(e for e in row["episodes"] if e["id"] == "shelter")
            self.assertIn('"Moving them will be quicker," Mara said.', e["text"])
            self.assertIn("Ivo joined her.", e["text"])
            events = e["events"]
            choice = next(i for i, event in enumerate(events) if event["action"].startswith("decline_"))
            join = next(i for i, event in enumerate(events) if event["action"] == "ivo_joins_pot_relay")
            first_trip = next(i for i, event in enumerate(events) if event["action"] == "carry_first_six_pots")
            self.assertLess(choice, join)
            self.assertLess(join, first_trip)
            self.assertNotIn("ivo.plan", events[choice]["changes"])
            self.assertEqual(events[join]["requires"]["mara.repair_declined"], True)
            self.assertEqual(events[join]["changes"]["ivo.plan"], {"before": "", "after": "pot_relay"})

    def test_tea_is_poured_consumed_and_recapped(self):
        for honest in (True, False):
            p = Parameters(honest=honest)
            prefix = ("gate", "enter", "admit" if honest else "deflect")
            s = replay(p, prefix)[-1]["after"]
            saved = deepcopy(s)
            e = play_scene(p, s, "tea")
            self.assertEqual(s, saved)
            self.assertEqual([event["action"] for event in e["events"]],
                             ["uncap_flask", "pour_flask", "drink_tea", "recap_flask", "finish_encounter"])
            for event in e["events"]:
                for key, change in event["changes"].items():
                    s[key] = change["after"]
                validate(s)
                self.assertEqual(2 * s["flask.full"] + 2 * s["cups.filled"] + s["tea.servings_drunk"], 2)
                if event["action"] == "pour_flask":
                    self.assertTrue(s["cups.filled"])
                    self.assertEqual(s["tea.servings_drunk"], 0)
            self.assertFalse(s["cups.filled"])
            self.assertFalse(s["flask.full"])
            self.assertTrue(s["flask.capped"])
            self.assertEqual(s["tea.servings_drunk"], 2)
            self.assertIn("They drained their cups", e["text"])

    def test_tea_cannot_be_drunk_twice_or_reappear(self):
        p = Parameters()
        before = replay(p, ("gate", "enter", "admit"))[-1]["after"]
        x = LocalPlay(before)
        with self.assertRaises(StoryError):
            x.act("drink_empty_cups", {"cups.filled": True}, **{"tea.servings_drunk": 2})
        self.assertEqual(x.state, before)
        self.assertEqual(x.events, [])
        after = play_scene(p, before, "tea")["after"]
        x = LocalPlay(after)
        with self.assertRaises(StoryError):
            x.act("tea_reappears", {}, **{"cups.filled": True})
        self.assertEqual(x.state, after)
        self.assertEqual(x.events, [])
        row = generate(1, count=8)
        self.assertIn("tea", row["path"])
        self.assertEqual(row["final_state"]["tea.servings_drunk"], 2)
        self.assertFalse(row["final_state"]["cups.filled"])
        omitted = generate(1, count=7)
        self.assertNotIn("tea", omitted["path"])
        self.assertEqual(omitted["final_state"]["tea.servings_drunk"], 0)
        self.assertTrue(omitted["final_state"]["flask.full"])

    def test_both_people_exit_before_the_door_closes(self):
        for p in (Parameters(), Parameters(receptive=False), Parameters(honest=False)):
            row = generate(0, count=7, params=p)
            ending = row["episodes"][-1]
            actions = [event["action"] for event in ending["events"]]
            self.assertLess(actions.index("exit_greenhouse"), actions.index("close_greenhouse_door"))
            if p.honest:
                self.assertLess(actions.index("ivo_joins_on_path"), actions.index("close_greenhouse_door"))
                event = next(event for event in ending["events"] if event["action"] == "ivo_joins_on_path")
                self.assertTrue(event["requires"]["door.open"])
                self.assertEqual(ending["after"]["ivo.location"], "path")
            else:
                self.assertNotIn("ivo_joins_on_path", actions)
                self.assertEqual(ending["after"]["ivo.location"], "inside")

    def test_documented_diagnostic_recipes(self):
        recipes = {
            "joint_care": Parameters(weather="wind", tape=False, damp_seeds=False, honest=True,
                                     receptive=True, strategy="patch"),
            "supervised_trial": Parameters(weather="wind", tape=True, damp_seeds=False, honest=True,
                                           receptive=False, strategy="patch"),
            "separation": Parameters(weather="heat", tape=True, damp_seeds=False, honest=False,
                                     receptive=True, strategy="patch"),
        }
        for expected, p in recipes.items():
            for count in (7, 8):
                row = generate(0, count=count, params=p)
                self.check(row)
                self.assertEqual(row["final_state"]["story.outcome"], expected)

    def test_exposure_progresses_in_two_bounded_batches(self):
        for weather in ("wind", "heat"):
            row = generate(0, count=7, params=Parameters(weather=weather, strategy="shelter"))
            e = next(e for e in row["episodes"] if e["id"] == "shelter")
            first, last = [event for event in e["events"] if event["action"].startswith("carry_")]
            self.assertEqual(first["changes"]["tomatoes.state"], {"before": "exposed", "after": "stressed"})
            self.assertEqual(first["changes"]["tomatoes.exposure_minutes"]["after"], 15)
            self.assertNotIn("tomatoes.damaged", first["changes"])
            self.assertEqual(last["requires"]["tomatoes.state"], "stressed")
            self.assertEqual(last["changes"]["tomatoes.exposure_minutes"], {"before": 15, "after": 30})
            self.assertEqual(last["changes"]["tomatoes.damaged"]["after"], 2)
            self.assertEqual(e["after"]["tray.rooted_pots"], 0)
            self.assertEqual(e["after"]["tomatoes.moved"], 12)
            self.assertTrue(e["after"]["tomatoes.sheltered"])
            self.assertIn("half an hour", e["text"])
            if weather == "heat":
                self.assertEqual(e["after"]["weather.gusts"], 0)
                self.assertTrue(e["after"]["door.open"])
                self.assertIn("scorched leaves", e["text"])
                self.assertIn("They were alive", e["text"])
                self.assertNotIn("snapped", e["text"])
            else:
                self.assertEqual(e["after"]["weather.gusts"], 2)
                self.assertFalse(e["after"]["door.open"])
                self.assertIn("snapped two stems", e["text"])
                self.assertNotIn("scorched", e["text"])

    def test_available_tape_was_a_real_missed_opportunity(self):
        for weather in ("wind", "heat"):
            p = Parameters(weather=weather, tape=True, strategy="shelter")
            failed = generate(1, count=7, params=p)
            repaired = generate(1, count=7, params=replace(p, strategy="patch"))
            self.assertEqual(failed["final_state"]["tomatoes.damaged"], 2)
            self.assertEqual(repaired["final_state"]["tomatoes.damaged"], 0)
            self.assertEqual(repaired["final_state"]["tomatoes.exposure_minutes"], 0)
            self.assertEqual(repaired["final_state"]["tomatoes.moved"], 0)
            self.assertEqual(failed["final_state"]["story.outcome"], "supervised_trial")
            self.assertEqual(repaired["final_state"]["story.outcome"], "joint_care")
            self.assertFalse(repaired["final_state"]["tape.available"])
            self.assertTrue(failed["final_state"]["tape.available"])

    def test_pane_is_supported_by_wood_not_waxed_paper(self):
        for weather, tape in product(("wind", "heat"), (False, True)):
            row = generate(0, count=7, params=Parameters(weather=weather, tape=tape))
            e = next(e for e in row["episodes"] if e["id"].startswith("patch_"))
            s = e["after"]
            self.assertEqual(s["stay.location"], "vent_frame")
            self.assertTrue(s["stay.seated"])
            self.assertEqual(s["vent.fastener"], "tape" if tape else "parcel_string")
            self.assertEqual(s["vent.support"], "wooden_stay" if weather == "heat" else "hinges")
            self.assertEqual(s["vent.position"], "propped_open" if weather == "heat" else "closed")
            self.assertEqual(s["paper.use"], "wrapping" if tape else "stay_padding" if weather == "heat" else "rain_screen")
            self.assertIn("wooden stay", e["text"])
            actions = [event["action"] for event in e["events"]]
            self.assertLess(actions.index("hold_vent_frame"), actions.index("seat_wooden_stay"))
            self.assertLess(actions.index("seat_wooden_stay"), actions.index("release_secured_frame"))
            broken = deepcopy(s)
            broken["stay.location"] = "shelf"
            with self.assertRaises(StoryError):
                validate(broken)
            if weather == "heat":
                broken = deepcopy(s)
                broken["vent.support"] = "waxed_paper"
                with self.assertRaises(StoryError):
                    validate(broken)

    def test_missing_stay_rejects_repair_atomically(self):
        p = Parameters()
        s = replay(p, ("gate", "enter", "admit", "gust"))[-1]["after"]
        s["stay.location"] = "shed"
        saved = deepcopy(s)
        with self.assertRaises(StoryError):
            play_scene(p, s, "patch_parcel")
        self.assertEqual(s, saved)

    def test_instant_crop_loss_and_wrong_weather_repair_fail_closed(self):
        p = Parameters(strategy="shelter")
        s = replay(p, ("gate", "enter", "admit", "gust"))[-1]["after"]
        x = LocalPlay(s)
        for condition in ("lost", "damaged"):
            with self.assertRaises(StoryError):
                x.act("hide_parcel_and_kill_plants", {"parcel.location": "bench"},
                      **{"parcel.location": "under_bench", "tomatoes.state": condition})
            self.assertEqual(x.state, s)
            self.assertEqual(x.events, [])
        row = generate(0, count=7, params=Parameters(weather="heat"))
        wrong = deepcopy(row["final_state"])
        wrong["vent.position"] = "closed"
        with self.assertRaises(StoryError):
            validate(wrong)

    def test_watered_ending_has_a_visible_watering_handoff(self):
        for tape in (True, False):
            row = generate(0, count=7, params=Parameters(tape=tape))
            sow = next(e for e in row["episodes"] if e["id"] == "sow")
            actions = [event["action"] for event in sow["events"]]
            self.assertLess(actions.index("sow_twelve_beans"), actions.index("water_sown_pots"))
            self.assertFalse(sow["before"]["pots.watered"])
            self.assertTrue(sow["after"]["pots.watered"])
            self.assertFalse(sow["after"]["can.full"])
            self.assertIn("She watered them from the full can", sow["text"])
            self.assertIn("watered soil", row["episodes"][-1]["text"])

    def test_store_requests_and_opens_tin_only_when_needed(self):
        for tape, strategy in product((True, False), ("patch", "shelter")):
            row = generate(0, count=7, params=Parameters(tape=tape, strategy=strategy, damp_seeds=True))
            store = next(e for e in row["episodes"] if e["id"] == "store")
            actions = [event["action"] for event in store["events"]]
            if store["before"]["tin.borrowed"]:
                self.assertNotIn("borrow_and_open_tin", actions)
                self.assertIn("borrowed sandwich tin was still open", store["text"])
            else:
                self.assertLess(actions.index("borrow_and_open_tin"), actions.index("open_seed_parcel"))
                self.assertLess(actions.index("open_seed_parcel"), actions.index("spread_beans_in_tin"))
                self.assertIn("asked for his sandwich tin; Ivo opened it", store["text"])
                self.assertIn("She unwrapped the beans", store["text"])
            self.assertEqual(store["after"]["tin.location"], "shelf")
            self.assertTrue(store["after"]["tin.open"])
            self.assertFalse(row["final_state"]["pots.watered"])
            self.assertTrue(row["final_state"]["can.full"])

    def test_reference_metadata_counts_prose_not_heading(self):
        root = Path(__file__).parent
        body = root.joinpath("reference_story.md").read_text().split("\n\n", 1)[1]
        inventory = json.loads(root.joinpath("scene_inventory.json").read_text())
        self.assertEqual(len(body.split()), 997)
        self.assertEqual(inventory["reference_word_count"], 997)
        self.assertEqual(len(inventory["scenes"]), 20)
        self.assertEqual(len(SCENES), 19)

    def test_locations_and_compatible_endings(self):
        for p in (Parameters(), Parameters(honest=False), Parameters(damp_seeds=True)):
            row = generate(0, params=p, count=7)
            state = row["episodes"][-1]["before"]
            for sid in ("ending_joint", "ending_trial", "ending_apart"):
                self.assertEqual(guard(sid, state), sid == row["path"][-1])
            for e in row["episodes"][2:-1]:
                self.assertEqual(e["before"]["party.location"], "inside")
            self.assertFalse(row["final_state"]["door.open"])
            if p.honest:
                self.assertEqual(row["final_state"]["ivo.location"], "path")
            else:
                self.assertEqual(row["final_state"]["ivo.location"], "inside")

    def test_validation_and_inventory(self):
        for kwargs in ({"weather": "rain"}, {"strategy": "magic"}, {"tape": 1}, {"honest": "yes"}):
            with self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (6, 9, True):
            with self.assertRaises(ValueError):
                generate(count=count)
        inventory = json.loads(Path(__file__).with_name("scene_inventory.json").read_text())
        self.assertEqual(set(SCENES), {sid for s in inventory["scenes"] for sid in s["implemented_ids"]})


if __name__ == "__main__":
    unittest.main()
