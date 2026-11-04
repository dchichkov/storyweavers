"""Bounded bakery mini-plays over the shared atomic transition runtime."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import random

from storyscenes.runtime import StoryError
from ..local_play import LocalPlay as AtomicLocalPlay
from .prose import render


@dataclass(frozen=True, kw_only=True)
class Parameters:
    fuel: int = 2
    early_van: bool = False
    decision: str = "confess"
    wick_stuck: bool = True
    spare_oil: bool = True
    torn_crown: bool = False

    def __post_init__(self):
        if type(self.fuel) is not int or not 1 <= self.fuel <= 3:
            raise ValueError("fuel must be an integer from 1 to 3")
        if self.decision not in ("confess", "request_extension", "return_now"):
            raise ValueError("Unknown decision")
        for key in ("early_van", "wick_stuck", "spare_oil", "torn_crown"):
            if type(getattr(self, key)) is not bool:
                raise ValueError(f"{key} must be boolean")


def parameters(seed):
    r = random.Random(seed)
    return Parameters(fuel=r.choice((1, 2, 3)), early_van=r.choice((False, True)),
                      decision=r.choice(("confess", "request_extension", "return_now")),
                      wick_stuck=r.choice((False, True)), spare_oil=r.choice((False, True)),
                      torn_crown=r.choice((False, True)))


OPTIONAL = ("glove", "darn", "crown", "refill", "inspect_wick", "window_note", "mend_crown")
SCENES = ("launch", "borrow", *OPTIONAL, "bake", "knock", "confess", "request_extension",
          "return_now", "finish_secret", "finish_together", "postpone", "ending_secret",
          "ending_together", "ending_postponed")


def initial(p):
    if not isinstance(p, Parameters):
        raise ValueError("Expected Parameters")
    return {
        "story.stage": "new", "story.outcome": "", "story.ended": False,
        "party.location": "bakery", "baker.location": "town", "bulb.working": False,
        "oven_room.windowless": True, "nell.plan": p.decision, "nell.wants_secret": False,
        "nell.knows_wick": False, "nell.knows_fuel": None,
        "nell.memes.Secrecy": 0, "nell.memes.Trust": 0,
        "vale.location": "workshop", "vale.knows": False, "vale.early_van": p.early_van,
        "lantern.owner": "vale", "lantern.holder": "vale", "lantern.location": "workshop",
        "lantern.fuel": p.fuel, "lantern.lit": False, "lantern.wick_stuck": p.wick_stuck,
        "lantern.wheel_tested": False, "lantern.reservoir_open": False,
        "lantern.fuel_used": 0, "fuel.initial_total": p.fuel + int(p.spare_oil),
        "loan.reserve": 1, "loan.extended": False, "loan.returned": False,
        "loan.usable_checked": False, "vale.cellar_light_secured": False,
        "oil.available": p.spare_oil, "oil.units": int(p.spare_oil), "glove.location": "counter",
        "cloth.darn_visible": False, "crown.words": "VALE", "crown.location": "counter",
        "crown.torn": p.torn_crown, "crown.mended": False, "notice.hidden": False,
        "oven.open": False, "oven.on": False, "oven.minutes_left": 20,
        "loaf.location": "tin", "loaf.ready": False, "table.served": False,
        "invitation.location": "none", "invitation.accepted": False,
        "baker_request.location": "none", "bread.checked": False,
        "cups.location": "shelf", "lantern.resting": False,
        **{f"scene.{s}": False for s in SCENES},
    }


def validate(s):
    if s["party.location"] not in ("bakery", "workshop", "lane", "oven_room"):
        raise StoryError("Unknown party location")
    if s["vale.location"] not in ("bakery", "lane", "workshop", "oven_room"):
        raise StoryError("Unknown Vale location")
    if s["lantern.owner"] != "vale" or s["lantern.holder"] not in ("nell", "vale", "shelf"):
        raise StoryError("Lantern ownership/custody invalid")
    expected = {"nell": s["party.location"], "vale": s["vale.location"], "shelf": "oven_room"}
    if s["lantern.location"] != expected[s["lantern.holder"]]:
        raise StoryError("Lantern separated from its carrier")
    if type(s["lantern.fuel"]) is not int or not 0 <= s["lantern.fuel"] <= 4:
        raise StoryError("Fuel out of bounds")
    if (type(s["oil.units"]) is not int or s["oil.units"] not in (0, 1)
            or s["oil.available"] != bool(s["oil.units"])
            or type(s["lantern.fuel_used"]) is not int or s["lantern.fuel_used"] < 0
            or s["lantern.fuel"] + s["oil.units"] + s["lantern.fuel_used"] != s["fuel.initial_total"]):
        raise StoryError("Oil must be conserved across reservoir, bottle, and burning")
    if s["loan.reserve"] != 1 or s["lantern.fuel"] < s["loan.reserve"]:
        raise StoryError("Must preserve the owner's cellar-light reserve")
    if s["lantern.lit"] and (s["lantern.fuel"] == 0 or s["lantern.reservoir_open"]):
        raise StoryError("Unsafe or unfueled flame")
    if s["oven.minutes_left"] not in (0, 10, 20):
        raise StoryError("Invalid baking time")
    if s["loaf.ready"] != (s["oven.minutes_left"] == 0):
        raise StoryError("Unbaked loaf cannot be ready")
    if s["table.served"] and not (s["loaf.ready"] and s["loaf.location"] == "table"):
        raise StoryError("Table needs actual baked bread")
    if s["loan.returned"] and s["lantern.holder"] != "vale":
        raise StoryError("Returned lantern missing")
    if s["loan.returned"] and not (s["loan.usable_checked"] and s["vale.cellar_light_secured"]
                                   and not s["lantern.wick_stuck"] and not s["lantern.reservoir_open"]):
        raise StoryError("Settling a loan requires usable light for the owner")
    if s["loan.extended"] and s["vale.early_van"]:
        raise StoryError("The early van cannot wait, even for a disclosed supper")
    if s["lantern.resting"] and not (s["lantern.holder"] == "vale"
                                      and s["lantern.location"] == "bakery"):
        raise StoryError("Lantern may rest at Vale's place only when he is there")
    if s["story.ended"]:
        outcome = s["story.outcome"]
        if outcome not in ("surprise_supper", "shared_supper", "breakfast_instead"):
            raise StoryError("Ending needs an outcome")
        if not s["loan.returned"] or s["lantern.lit"] or s["oven.on"] or s["oven.open"]:
            raise StoryError("Unfinished loan or unsafe ending")
        if s["party.location"] != "bakery":
            raise StoryError("Party not home")
        if (outcome != "breakfast_instead") != s["table.served"]:
            raise StoryError("Outcome contradicts meal")
        if outcome == "breakfast_instead" and s["invitation.location"] != "vale":
            raise StoryError("Unsent invitation")
        if outcome == "breakfast_instead" and (s["invitation.accepted"] or s["baker_request.location"] != "counter"):
            raise StoryError("Postponement must remain a request, not an agreed future success")


@dataclass(frozen=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: list[dict]
    text: str


class LocalPlay(AtomicLocalPlay):
    def __init__(self, state):
        super().__init__(state, actors=("nell", "kit", "vale"), validate=validate)

    def move(self, destination, *, with_vale=False):
        origin = self.state["party.location"]
        if {origin, destination} not in ({"bakery", "lane"}, {"lane", "workshop"},
                                        {"bakery", "oven_room"}):
            raise StoryError("No adjacent doorway or path")
        changes = {"party.location": destination}
        requires = {"party.location": origin}
        if self.state["lantern.holder"] == "nell":
            changes["lantern.location"] = destination
        if with_vale:
            requires["vale.location"] = origin
            changes["vale.location"] = destination
            if self.state["lantern.holder"] == "vale":
                changes["lantern.location"] = destination
        self.act(f"walk:{origin}:{destination}", requires, **changes)

    def hand(self, recipient):
        s = self.state
        if s["vale.location"] != s["party.location"]:
            raise StoryError("Cannot hand a lantern across locations")
        source = "vale" if recipient == "nell" else "nell"
        self.act(f"hand_lantern_to_{recipient}", {"lantern.holder": source,
                 "lantern.lit": False, "vale.location": s["party.location"]},
                 **{"lantern.holder": recipient})

    def settle_loan(self):
        s = self.state
        self.act("check_usable_lantern_and_settle_loan", {
            "lantern.holder": "vale", "lantern.lit": False,
            "lantern.wick_stuck": False, "lantern.reservoir_open": False,
            "lantern.fuel": s["lantern.fuel"], "loan.reserve": 1,
            "loan.returned": False}, **{"loan.usable_checked": True,
            "vale.cellar_light_secured": True, "loan.returned": True})

    def move_vale(self, destination):
        origin = self.state["vale.location"]
        if {origin, destination} not in ({"bakery", "lane"}, {"lane", "workshop"}):
            raise StoryError("No adjacent route for Vale")
        changes = {"vale.location": destination}
        if self.state["lantern.holder"] == "vale":
            changes["lantern.location"] = destination
        self.act(f"vale_walks:{origin}:{destination}", {"vale.location": origin}, **changes)


def guard(scene_id, s):
    if scene_id not in SCENES or s["story.ended"] or s[f"scene.{scene_id}"]:
        return False
    phase = s["story.stage"]
    if scene_id == "launch":
        return phase == "new" and s["party.location"] == "bakery"
    if scene_id == "borrow":
        return phase == "planned" and s["party.location"] == "bakery" and s["lantern.holder"] == "vale"
    if scene_id in OPTIONAL:
        return (phase == "borrowed" and s["party.location"] == "bakery"
                and (scene_id != "refill" or s["oil.available"])
                and (scene_id != "mend_crown" or s["crown.torn"]))
    if scene_id == "bake":
        return phase == "borrowed" and s["party.location"] == "bakery" and s["lantern.holder"] == "nell" and s["lantern.fuel"] > 0
    if scene_id == "knock":
        return phase == "checked" and s["party.location"] == "oven_room"
    if scene_id in ("confess", "request_extension", "return_now"):
        return phase == "asked" and s["party.location"] == s["vale.location"] == "bakery"
    if scene_id in ("finish_secret", "finish_together"):
        return (phase == "decided" and s["loan.extended"] and s["lantern.holder"] == "nell"
                and s["lantern.fuel"] > s["loan.reserve"] and s["oven.on"]
                and s["oven.minutes_left"] == 10 and s["party.location"] == "bakery"
                and s["vale.knows"] == (scene_id == "finish_together"))
    if scene_id == "postpone":
        return phase == "decided" and (not s["loan.extended"]
            or s["lantern.fuel"] <= s["loan.reserve"] or not s["oven.on"])
    if scene_id == "ending_secret":
        return phase == "served" and not s["vale.knows"] and s["table.served"]
    if scene_id == "ending_together":
        return phase == "served" and s["vale.knows"] and s["table.served"]
    if scene_id == "ending_postponed":
        return phase == "postponed" and not s["loaf.ready"]
    return False


def play_scene(params, state, scene_id):
    validate(state)
    if not guard(scene_id, state):
        raise StoryError(f"Illegal scene: {scene_id}")
    x = LocalPlay(state)
    def act(name, req=None, **changes):
        x.act(name, req, **changes)
    if scene_id == "launch":
        act("hide_crown_and_plan_supper", {"story.stage": "new"}, **{
            "story.stage": "planned", "crown.location": "under_counter",
            "nell.wants_secret": True, "nell.memes.Secrecy": 2})
    elif scene_id == "borrow":
        x.move("lane")
        x.move("workshop")
        x.hand("nell")
        x.move("lane")
        x.move("bakery")
        act("promise_return", **{"story.stage": "borrowed"})
    elif scene_id == "glove":
        act("pin_oversized_glove", {"glove.location": "counter"}, **{"glove.location": "noticeboard"})
    elif scene_id == "darn":
        act("turn_mend_outward", **{"cloth.darn_visible": True})
    elif scene_id == "crown":
        act("write_thanks_on_reverse", **{"crown.words": "THANK YOU"})
    elif scene_id == "window_note":
        act("cover_supper_notice", **{"notice.hidden": True})
    elif scene_id == "mend_crown":
        act("paste_paper_strip", {"crown.torn": True}, **{"crown.torn": False, "crown.mended": True})
    elif scene_id == "inspect_wick":
        act("inspect_cold_wheel", {"lantern.lit": False}, **{"nell.knows_wick": True})
    elif scene_id == "refill":
        act("open_cold_reservoir", {"lantern.lit": False, "oil.available": True}, **{"lantern.reservoir_open": True})
        act("pour_spare_oil", {"lantern.reservoir_open": True}, **{
            "lantern.fuel": x.state["lantern.fuel"] + x.state["oil.units"],
            "oil.units": 0, "oil.available": False})
        act("close_reservoir", **{"lantern.reservoir_open": False})
    elif scene_id == "bake":
        act("read_fuel_level_and_reserve_cellar_oil", {"lantern.lit": False},
            **{"nell.knows_fuel": x.state["lantern.fuel"]})
        x.move("oven_room")
        act("try_wick_wheel_failed" if x.state["lantern.wick_stuck"] else "try_wick_wheel",
            {"lantern.holder": "nell", "lantern.wick_stuck": x.state["lantern.wick_stuck"]},
            **{"lantern.wheel_tested": True})
        if x.state["lantern.wick_stuck"]:
            act("free_jammed_wheel", {"lantern.lit": False, "lantern.wheel_tested": True}, **{"lantern.wick_stuck": False})
        if x.state["lantern.fuel"] > x.state["loan.reserve"]:
            act("light_lantern", {"lantern.wick_stuck": False, "lantern.reservoir_open": False}, **{"lantern.lit": True})
            act("set_on_stone_shelf", **{"lantern.holder": "shelf"})
            act("open_oven", **{"oven.open": True})
            act("load_loaf", {"oven.open": True, "loaf.location": "tin"}, **{"loaf.location": "oven", "oven.on": True})
            act("close_and_bake_ten_minutes", {"lantern.lit": True}, **{
                "oven.open": False, "oven.minutes_left": 10, "story.stage": "checked"})
        else:
            act("decline_to_burn_cellar_reserve", {"lantern.fuel": 1, "oven.on": False},
                **{"story.stage": "checked"})
    elif scene_id == "knock":
        if x.state["lantern.lit"]:
            act("extinguish_after_first_ten_minutes", {"lantern.holder": "shelf", "lantern.lit": True}, **{
                "lantern.lit": False, "lantern.fuel": x.state["lantern.fuel"] - 1,
                "lantern.fuel_used": x.state["lantern.fuel_used"] + 1})
            act("pick_up_lantern", **{"lantern.holder": "nell"})
        x.move("bakery")
        x.move_vale("lane")
        x.move_vale("bakery")
        act("vale_knocks", **{"story.stage": "asked"})
    elif scene_id == "confess":
        act("tell_vale_and_invite_help", **{"vale.knows": True, "loan.extended": not state["vale.early_van"],
            "nell.memes.Secrecy": 0, "nell.memes.Trust": 2, "story.stage": "decided"})
        if state["vale.early_van"]:
            x.hand("vale")
            x.settle_loan()
            x.move_vale("lane")
            x.move_vale("workshop")
    elif scene_id == "request_extension":
        act("request_ten_more_minutes", **{"loan.extended": not state["vale.early_van"], "story.stage": "decided"})
        if state["vale.early_van"]:
            x.hand("vale")
            x.settle_loan()
        x.move_vale("lane")
        x.move_vale("workshop")
    elif scene_id == "return_now":
        x.hand("vale")
        x.settle_loan()
        x.move_vale("lane")
        x.move_vale("workshop")
        act("decide_return_now", **{"story.stage": "decided"})
    elif scene_id in ("finish_secret", "finish_together"):
        together = scene_id == "finish_together"
        x.move("oven_room", with_vale=together)
        if together:
            x.hand("vale")
        act("relight_for_final_check", {"lantern.holder": "vale" if together else "nell",
            "loan.extended": True}, **{"lantern.lit": True})
        act("finish_baking", {"loaf.location": "oven", "oven.on": True}, **{"oven.minutes_left": 0, "loaf.ready": True})
        act("open_oven_for_check", **{"oven.open": True})
        act("tap_crust_and_lift_together", {"oven.open": True, "loaf.ready": True}, **{"bread.checked": True, "loaf.location": "rack"})
        act("close_and_turn_off_oven", **{"oven.open": False, "oven.on": False})
        act("extinguish_after_check", **{"lantern.lit": False,
            "lantern.fuel": x.state["lantern.fuel"] - 1,
            "lantern.fuel_used": x.state["lantern.fuel_used"] + 1})
        act("carry_hot_loaf_with_towels", {"loaf.location": "rack"}, **{"loaf.location": "kit"})
        x.move("bakery", with_vale=together)
        act("set_loaf_on_table", **{"loaf.location": "table", "table.served": True, "story.stage": "served"})
    elif scene_id == "postpone":
        x.move("oven_room", with_vale=state["vale.location"] == "bakery")
        if x.state["oven.on"]:
            act("turn_off_oven_without_claiming_finished_bread", {"oven.open": False}, **{"oven.on": False})
        x.move("bakery", with_vale=x.state["vale.location"] == "oven_room")
        act("write_request_for_baker_and_tentative_invitation", **{
            "baker_request.location": "counter", "invitation.location": "nell", "story.stage": "postponed"})
    elif scene_id.startswith("ending_"):
        if scene_id == "ending_secret" or (scene_id == "ending_postponed" and x.state["vale.location"] == "workshop"):
            x.move("lane")
            x.move("workshop")
            if x.state["lantern.holder"] == "nell":
                x.hand("vale")
            if not x.state["loan.returned"]:
                x.settle_loan()
            if scene_id == "ending_secret":
                act("invite_vale_to_supper", **{"vale.knows": True})
                x.move("lane", with_vale=True)
                x.move("bakery", with_vale=True)
            else:
                act("deliver_breakfast_invitation", **{"invitation.location": "vale", "vale.knows": True})
                x.move("lane")
                x.move("bakery")
        else:
            if x.state["lantern.holder"] == "nell":
                x.hand("vale")
            if not x.state["loan.returned"]:
                x.settle_loan()
            if scene_id == "ending_postponed":
                act("deliver_breakfast_invitation", **{"invitation.location": "vale", "vale.knows": True})
        if scene_id == "ending_postponed":
            act("leave_cups_ready_not_breakfast_made", **{"cups.location": "counter",
                "crown.location": "counter"})
        else:
            act("rest_lantern_at_vales_place", {"lantern.holder": "vale", "vale.location": "bakery"},
                **{"lantern.resting": True})
            act("place_crown_at_table", **{"crown.location": "vale" if scene_id == "ending_secret" else "table"})
        outcome = {"ending_secret": "surprise_supper", "ending_together": "shared_supper",
                   "ending_postponed": "breakfast_instead"}[scene_id]
        act("complete_evening", **{"story.outcome": outcome, "story.ended": True, "story.stage": "ended"})
    act("record_encounter", **{f"scene.{scene_id}": True})
    return Episode(scene_id, deepcopy(state), x.state, x.events, render(scene_id, state, x.state))


def replay(params, path):
    s = initial(params)
    result = []
    for scene_id in path:
        episode = play_scene(params, s, scene_id)
        result.append(episode)
        s = episode.after
    return result


def generate(seed=0, *, count=8, params=None):
    if type(count) is not int or count not in (7, 8):
        raise ValueError("count must be 7 or 8")
    p = parameters(seed) if params is None else params
    s = initial(p)
    rng = random.Random(seed)
    attempts = 0

    def search(state, path):
        nonlocal attempts
        attempts += 1
        if attempts > 2000:
            raise StoryError("Search budget exhausted")
        if state["story.ended"]:
            return path if len(path) == count else None
        if len(path) >= count:
            return None
        candidates = [i for i in SCENES if guard(i, state)]
        rng.shuffle(candidates)
        for i in candidates:
            if i in ("confess", "request_extension", "return_now") and i != p.decision:
                continue
            # One vignette is the intentional difference between short and long cuts.
            if i in OPTIONAL and (count == 7 or any(j in OPTIONAL for j in path)):
                continue
            ep = play_scene(p, state, i)
            found = search(ep.after, path + [i])
            if found:
                return found
        return None

    path = search(s, [])
    if path is None:
        raise StoryError("No complete route")
    episodes = replay(p, path)
    return {"seed": seed, "parameters": asdict(p), "scene_count": len(path), "path": path,
            "story": "\n\n".join(e.text for e in episodes),
            "episodes": [asdict(e) for e in episodes], "final_state": episodes[-1].after,
            "search_attempts": attempts}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--scenes", type=int, default=8)
    args = parser.parse_args()
    print(generate(args.seed, count=args.scenes)["story"])


if __name__ == "__main__":
    main()
