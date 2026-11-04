"""Bounded scene composition over embedded physical and social state."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import random

from storyscenes.runtime import Condition, Scene, Effect, StoryError, transition
from .prose import render


@dataclass(frozen=True, kw_only=True)
class Parameters:
    weather: str = "wind"
    tape: bool = False
    damp_seeds: bool = False
    honest: bool = True
    receptive: bool = True
    strategy: str = "patch"

    def __post_init__(self):
        if self.weather not in ("wind", "heat") or self.strategy not in ("patch", "shelter"):
            raise ValueError("Unknown weather or strategy")
        for key in ("tape", "damp_seeds", "honest", "receptive"):
            if type(getattr(self, key)) is not bool:
                raise ValueError(f"{key} must be boolean")


def parameters(seed):
    r = random.Random(seed)
    return Parameters(weather=r.choice(("wind", "heat")), tape=r.choice((True, False)),
                      damp_seeds=r.choice((False, False, True)), honest=r.choice((True, True, False)),
                      receptive=r.choice((True, False)), strategy=r.choice(("patch", "shelter")))


def initial(p):
    if not isinstance(p, Parameters):
        raise ValueError("Expected Parameters")
    return {
        "story.stage": 0, "story.ended": False, "story.outcome": "",
        "party.location": "gate", "ivo.location": "inside", "gate.open": False, "gate.stone": True,
        "door.open": False, "parcel.location": "mara", "parcel.open": False,
        "beans.location": "parcel", "beans.damp": p.damp_seeds, "beans.inspected": False,
        "pots.watered": False, "can.full": True,
        "tin.location": "bench", "tin.open": False, "tin.borrowed": False,
        "vent.position": "open" if p.weather == "wind" else "shut",
        "vent.secured": False, "vent.attempted": False, "vent.held": False,
        "vent.fastener": "", "vent.support": "hinges", "paper.use": "wrapping",
        "stay.location": "shelf", "stay.examined": False, "stay.seated": False,
        "weather.kind": p.weather, "tape.available": p.tape, "tape.tested": False,
        "tomatoes.state": "safe", "tray.location": "bench", "tray.lift_tried": False,
        "tray.rooted_pots": 12, "weather.gusts": 0,
        "tomatoes.moved": 0, "tomatoes.damaged": 0, "tomatoes.sheltered": False,
        "tomatoes.exposure_minutes": 0, "tomatoes.location": "upper_bench",
        "mara.repair_declined": False, "ivo.plan": "",
        "mara.honest_policy": p.honest, "mara.strategy": p.strategy,
        "mara.confessed": False, "mara.remembers_height": False,
        "ivo.receptive": p.receptive, "ivo.trust": 0, "ivo.knows_truth": False,
        "ivo.invitation": "", "key.owner": "ivo", "snail.location": "pot_rim",
        "flask.full": True, "cups.filled": False, "ledger.written": False,
        **{f"scene.{s}": False for s in SCENES},
    }


SCENES = (
    "gate", "measuring", "enter", "snail", "admit", "deflect", "tea", "gust", "heat",
    "patch_tape", "patch_parcel", "shelter", "sow", "store", "return", "ledger",
    "ending_joint", "ending_trial", "ending_apart",
)


def validate(s):
    if s["party.location"] not in ("gate", "path", "inside"):
        raise StoryError("Unknown location")
    if s["beans.location"] == "parcel" and s["parcel.location"] == "vent":
        raise StoryError("Beans cannot remain in installed paper")
    if s["beans.location"] == "tin" and not s["tin.borrowed"]:
        raise StoryError("Unborrowed tin")
    if s["story.ended"] != (s["story.stage"] == 7):
        raise StoryError("Completion mismatch")
    if s["story.ended"] and (not s["story.outcome"] or s["party.location"] == "inside" or s["door.open"]):
        raise StoryError("Incomplete ending")
    if s["story.outcome"] == "joint_care" and not (
        s["mara.confessed"] and s["ivo.receptive"] and s["beans.location"] == "pots"
    ):
        raise StoryError("Unearned shared care")
    if s["tomatoes.state"] == "saved" and not s["vent.secured"]:
        raise StoryError("Unsecured rescue")
    if s["tomatoes.state"] not in ("safe", "exposed", "stressed", "damaged", "saved"):
        raise StoryError("Unknown tomato condition")
    if s["vent.secured"] and not (
        s["stay.seated"] and s["stay.location"] == "vent_frame"
        and s["vent.fastener"] in ("tape", "parcel_string")
    ):
        raise StoryError("Vent needs a seated stay and an actual fastener")
    if s["vent.secured"] and s["weather.kind"] == "heat" and s["vent.support"] != "wooden_stay":
        raise StoryError("Paper and tape cannot support the raised pane")
    if s["stay.seated"] and s["stay.location"] != "vent_frame":
        raise StoryError("Stay is not at the frame")
    if s["vent.secured"] and s["vent.position"] != (
        "closed" if s["weather.kind"] == "wind" else "propped_open"
    ):
        raise StoryError("Secured vent must address this weather")
    if not 0 <= s["tomatoes.damaged"] <= s["tomatoes.moved"] <= 12:
        raise StoryError("Invalid seedling batch counts")
    if s["tray.rooted_pots"] + s["tomatoes.moved"] != 12:
        raise StoryError("Seedlings cannot duplicate during the pot relay")
    if s["tomatoes.state"] == "damaged" and not (
        s["tomatoes.damaged"] == 2 and s["tomatoes.sheltered"]
        and s["tomatoes.exposure_minutes"] >= 30
    ):
        raise StoryError("Damage needs elapsed exposure, not a parcel movement")


def _joint(s):
    return s["mara.confessed"] and s["ivo.receptive"] and s["beans.location"] == "pots"


def guard(scene_id, s):
    if scene_id not in SCENES or s["story.ended"] or s[f"scene.{scene_id}"]:
        return False
    stage = s["story.stage"]
    if scene_id == "gate":
        return stage == 0 and s["party.location"] == "gate" and s["parcel.location"] == "mara"
    if scene_id in ("measuring", "enter"):
        return stage == 1 and s["party.location"] == "path"
    if s["party.location"] != "inside":
        return False
    if scene_id == "snail":
        return stage == 2
    if scene_id in ("admit", "deflect"):
        return stage == 2 and s["mara.honest_policy"] == (scene_id == "admit")
    if scene_id == "tea":
        return stage == 3
    if scene_id in ("gust", "heat"):
        return stage == 3 and s["weather.kind"] == ("wind" if scene_id == "gust" else "heat")
    if scene_id in ("patch_tape", "patch_parcel", "shelter"):
        if stage != 4 or not s["vent.attempted"] or s["tomatoes.state"] != "exposed":
            return False
        if scene_id == "shelter":
            return s["mara.strategy"] == "shelter" and s["parcel.location"] == "bench"
        return (s["mara.strategy"] == "patch" and s["parcel.location"] == "bench"
                and s["tape.available"] == (scene_id == "patch_tape"))
    if scene_id in ("sow", "store", "return"):
        if stage != 5:
            return False
        accessible = (s["beans.location"] == "parcel" and s["parcel.location"] in ("bench", "under_bench")) or (
            s["beans.location"] == "tin" and s["tin.location"] == "bench" and s["tin.open"])
        if not accessible:
            return False
        if not s["mara.confessed"]:
            return scene_id == "return"
        plantable = not s["beans.damp"] and s["tomatoes.state"] == "saved"
        return scene_id == ("sow" if plantable else "store")
    if scene_id == "ledger":
        return stage == 6 and s["mara.confessed"]
    if stage == 6:
        ending = "ending_apart" if not s["mara.confessed"] else "ending_joint" if _joint(s) else "ending_trial"
        return scene_id == ending
    return False


class LocalPlay:
    def __init__(self, state):
        self.state = deepcopy(state)
        self.events = []

    def act(self, action, requires, **changes):
        local = Scene(action, action, ("mara", "ivo"),
                      tuple(Condition(k, "eq", v) for k, v in requires.items()),
                      tuple(Effect(k, v) for k, v in changes.items()), action)
        after = transition(self.state, local)
        if after is None:
            raise StoryError(f"Illegal action: {action}")
        validate(after)
        delta = {k: {"before": deepcopy(self.state[k]), "after": deepcopy(v)}
                 for k, v in after.items() if self.state[k] != v}
        self.events.append({"action": action, "requires": deepcopy(requires), "changes": delta})
        self.state = after

    def relay_pots(self):
        """Two six-pot trips expose different weather costs, not instant crop death."""
        minutes = 15  # Rooted pots must be teased out, not carried as a sound tray.
        for moved, condition in ((6, "stressed"), (12, "damaged")):
            self.act("carry_first_six_pots" if moved == 6 else "carry_last_six_pots", {
                "party.location": "inside", "mara.repair_declined": True,
                "ivo.plan": "pot_relay", "vent.secured": False,
                "tomatoes.moved": moved - 6,
                "tomatoes.state": "exposed" if moved == 6 else "stressed",
                "tomatoes.exposure_minutes": (moved // 6 - 1) * minutes,
                "tray.rooted_pots": 18 - moved,
            }, **{"tomatoes.moved": moved, "tomatoes.state": condition,
                  "tray.rooted_pots": 12 - moved,
                  "weather.gusts": moved // 6 if self.state["weather.kind"] == "wind" else 0,
                  "tomatoes.exposure_minutes": moved // 6 * minutes,
                  "tomatoes.location": "split_benches" if moved == 6 else "lower_bench",
                  "tomatoes.sheltered": moved == 12, "tomatoes.damaged": 0 if moved == 6 else 2})


def play_scene(params, state, scene_id):
    validate(state)
    if not guard(scene_id, state):
        raise StoryError(f"Unavailable scene: {scene_id}")
    x = LocalPlay(state)
    def act(name, req=None, **changes):
        x.act(name, {"party.location": x.state["party.location"], **(req or {})}, **changes)

    if scene_id == "gate":
        act("clear_gate_stone", {"gate.stone": True}, **{"gate.stone": False})
        act("open_gate", {"gate.stone": False}, **{"gate.open": True})
        act("carry_parcel_to_path", {"gate.open": True, "parcel.location": "mara"}, **{"party.location": "path"})
    elif scene_id == "measuring":
        act("read_measuring_stick", **{"mara.remembers_height": True})
    elif scene_id == "enter":
        act("ask_and_open_door", **{"door.open": True})
        act("enter_greenhouse", {"door.open": True}, **{"party.location": "inside"})
        act("put_parcel_on_bench", {"parcel.location": "mara"}, **{"parcel.location": "bench"})
        act("close_door", {"door.open": True}, **{"door.open": False})
    elif scene_id == "snail":
        act("move_snail_on_leaf", {"snail.location": "pot_rim"}, **{"snail.location": "doorway_pot"})
    elif scene_id in ("admit", "deflect"):
        act("confess" if scene_id == "admit" else "repeat_excuse",
            {"parcel.location": "bench"}, **{"mara.confessed": scene_id == "admit",
            "ivo.knows_truth": scene_id == "admit", "ivo.trust": 1 if scene_id == "admit" else -1})
    elif scene_id == "tea":
        act("pour_flask", {"flask.full": True}, **{"flask.full": False, "cups.filled": True})
    elif scene_id in ("gust", "heat"):
        act("try_broken_vent_cord", {"vent.attempted": False},
            **{"vent.attempted": True, "tomatoes.state": "exposed"})
    elif scene_id in ("patch_tape", "patch_parcel"):
        act("test_tape_roll", **{"tape.tested": True})
        act("inspect_notched_wooden_stay", {"stay.location": "shelf"}, **{"stay.examined": True})
        if scene_id == "patch_parcel":
            act("borrow_and_open_tin", {"tin.location": "bench"}, **{"tin.borrowed": True, "tin.open": True})
            act("unwrap_parcel", {"parcel.location": "bench"}, **{"parcel.open": True})
            act("tip_beans_into_tin", {"parcel.open": True, "tin.open": True, "beans.location": "parcel"},
                **{"beans.location": "tin"})
            act("prepare_paper_screen" if x.state["weather.kind"] == "wind" else "pad_stay_foot",
                {"beans.location": "tin"}, **{"parcel.location": "vent",
                "paper.use": "rain_screen" if x.state["weather.kind"] == "wind" else "stay_padding"})
        else:
            act("take_repair_tape", {"tape.available": True}, **{"tape.available": False})
        act("hold_vent_frame", {"tomatoes.state": "exposed", "vent.held": False},
            **{"vent.held": True, "vent.position": "closed" if x.state["weather.kind"] == "wind" else "raised"})
        act("seat_wooden_stay", {"vent.held": True, "stay.examined": True, "stay.location": "shelf"},
            **{"stay.location": "vent_frame", "stay.seated": True,
            "vent.support": "wooden_stay" if x.state["weather.kind"] == "heat" else "hinges"})
        act("fasten_stay_with_tape" if scene_id == "patch_tape" else "lash_handle_with_parcel_string",
            {"stay.seated": True, "vent.held": True},
            **{"vent.fastener": "tape" if scene_id == "patch_tape" else "parcel_string"})
        act("release_secured_frame", {"tomatoes.state": "exposed", "stay.seated": True,
            "vent.fastener": x.state["vent.fastener"]}, **{"vent.secured": True, "vent.held": False,
            "vent.position": "closed" if x.state["weather.kind"] == "wind" else "propped_open",
            "tomatoes.state": "saved", "tomatoes.sheltered": True})
    elif scene_id == "shelter":
        act("try_lifting_brittle_tray", {"tray.location": "bench"}, **{"tray.lift_tried": True})
        act("consider_tape_repair", **{"tape.tested": True})
        act("inspect_notched_wooden_stay", {"stay.location": "shelf"}, **{"stay.examined": True})
        act("decline_tape_repair" if x.state["tape.available"] else "decline_unwrapping_parcel",
            {"tape.tested": True, "stay.examined": True, "tape.available": x.state["tape.available"]},
            **{"mara.repair_declined": True, "ivo.plan": "pot_relay"})
        act("shelter_parcel", {"parcel.location": "bench"},
            **{"parcel.location": "under_bench"})
        if x.state["weather.kind"] == "heat":
            act("open_door_for_air", {"door.open": False}, **{"door.open": True})
        x.relay_pots()
    elif scene_id in ("sow", "store", "return"):
        if scene_id == "store" and not x.state["tin.borrowed"]:
            act("borrow_and_open_tin", {"tin.location": "bench", "tin.open": False},
                **{"tin.borrowed": True, "tin.open": True})
        if x.state["beans.location"] == "parcel":
            act("retrieve_parcel", {"parcel.location": x.state["parcel.location"]}, **{"parcel.location": "hands"})
            act("open_seed_parcel", {"parcel.open": False}, **{"parcel.open": True})
        if scene_id == "sow":
            act("sow_twelve_beans", {"beans.damp": False, "tomatoes.state": "saved"},
                **{"beans.location": "pots", "ivo.invitation": "joint" if x.state["ivo.receptive"] else "supervised"})
            act("water_sown_pots", {"beans.location": "pots", "can.full": True},
                **{"pots.watered": True, "can.full": False})
        elif scene_id == "store":
            act("spread_beans_in_tin", {"tin.open": True}, **{"beans.location": "tin", "beans.inspected": True})
            act("store_tin_on_shelf", {"beans.location": "tin"},
                **{"tin.location": "shelf", "ivo.invitation": "supervised"})
        else:
            act("return_beans_to_mara", **{"beans.location": "mara", "ivo.invitation": "none"})
    elif scene_id == "ledger":
        act("write_next_visit", **{"ledger.written": True})
    else:
        if not x.state["door.open"]:
            act("open_door_to_leave", {"door.open": False}, **{"door.open": True})
        if x.state["parcel.location"] == "hands":
            act("leave_empty_paper_on_bench", **{"parcel.location": "bench"})
        act("exit_greenhouse", {"door.open": True}, **{"party.location": "path"})
        act("close_greenhouse_door", {"door.open": True}, **{"door.open": False})
        if scene_id != "ending_apart":
            act("ivo_joins_on_path", **{"ivo.location": "path"})
        if scene_id == "ending_joint":
            act("give_spare_key", {"key.owner": "ivo"}, **{"key.owner": "mara"})
        if scene_id == "ending_apart":
            act("walk_to_gate_with_beans", {"beans.location": "mara", "gate.open": True}, **{"party.location": "gate"})
            act("put_beans_in_pocket", {"beans.location": "mara"}, **{"beans.location": "mara_pocket"})

    optional = scene_id in ("measuring", "snail", "tea", "ledger")
    changes = {f"scene.{scene_id}": True}
    if not optional:
        changes["story.stage"] = state["story.stage"] + 1
    if scene_id.startswith("ending_"):
        changes.update({"story.ended": True, "story.outcome": {
            "ending_joint": "joint_care", "ending_trial": "supervised_trial", "ending_apart": "separation"}[scene_id]})
    act("finish_encounter", **changes)
    return {"id": scene_id, "before": deepcopy(state), "after": x.state,
            "events": x.events, "text": render(scene_id, state, x.state)}


def replay(params, path):
    state = initial(params)
    episodes = []
    for scene_id in path:
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode["after"]
    return episodes


def generate(seed=0, *, count=8, params=None):
    if type(count) is not int or count not in (7, 8):
        raise ValueError("Scene count must be 7 or 8")
    p = parameters(seed) if params is None else params
    rng = random.Random(seed)
    nodes = 0
    def visit(state, path):
        nonlocal nodes
        nodes += 1
        if nodes > 1000:
            raise StoryError("Search budget exhausted")
        if state["story.ended"]:
            return path if len(path) == count else None
        if len(path) >= count or len(path) + 7 - state["story.stage"] > count:
            return None
        candidates = [s for s in SCENES if guard(s, state)]
        rng.shuffle(candidates)
        for sid in candidates:
            episode = play_scene(p, state, sid)
            result = visit(episode["after"], path + [sid])
            if result is not None:
                return result
        return None
    path = visit(initial(p), [])
    if path is None:
        raise StoryError("No complete route")
    episodes = replay(p, path)
    return {"seed": seed, "parameters": asdict(p), "scene_count": count, "path": path,
            "story": "\n\n".join(e["text"] for e in episodes), "episodes": episodes,
            "final_state": deepcopy(episodes[-1]["after"]), "search_attempts": nodes}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--scenes", type=int, default=8)
    args = parser.parse_args()
    print(generate(args.seed, count=args.scenes)["story"])


if __name__ == "__main__":
    main()
