"""Bounded, replayable local plays for The Courtyard Cart."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import json
import random

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError

from .prose import render


@dataclass(frozen=True, kw_only=True)
class Parameters:
    washer_available: bool = True
    spanner_fits: bool = True
    cart_load: int = 2
    bench_level: bool = True
    admission_style: str = "early"

    def __post_init__(self):
        for name in ("washer_available", "spanner_fits", "bench_level"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be a boolean")
        if type(self.cart_load) is not int or not 1 <= self.cart_load <= 3:
            raise ValueError("cart_load must be an integer from 1 through 3")
        if self.admission_style not in ("early", "late"):
            raise ValueError("admission_style must be 'early' or 'late'")


def parameters(seed):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    rng = random.Random(seed)
    return Parameters(
        washer_available=rng.choice((True, False)),
        spanner_fits=rng.choice((True, False)),
        cart_load=rng.choice((1, 2, 3)),
        bench_level=rng.choice((True, False)),
        admission_style=rng.choice(("early", "late")),
    )


SCENES = (
    "borrow", "chalk_names", "first_attempt", "reinspect", "measure_story",
    "admit_error", "keep_face", "repair", "park_it", "test_roll", "mark_out",
    "ending_repaired", "ending_rebuilt", "ending_stopped",
)

_STATE_KEYS = frozenset({
    "story.started", "story.ended", "story.outcome",
    "jo.goal", "jo.admission_style", "jo.decision", "jo.owned_error",
    "jo.first_guess", "jo.diagnosis", "jo.checked_spanner", "jo.swapped_tool",
    "jo.used_wedge", "jo.heard_tip", "jo.recognized_wrong",
    "mina.goal", "mina.trust", "mina.knows_wrong_guess", "mina.knows_actual_fault",
    "mina.delivery", "len.goal", "len.spanner_ready", "len.tip_given",
    "cart.location", "cart.status", "cart.load", "cart.capacity", "cart.name_marked",
    "cart.steadied", "cart.tested", "cart.test_passed", "cart.out_of_service",
    "cart.parked_checked", "cart.current_use", "cart.display_ready", "cart.note",
    "wheel.rattle", "wheel.side_play", "wheel.turns_freely", "wheel.nut",
    "wheel.spacer_location", "spanner.owner", "spanner.location", "spanner.fits",
    "spanner.kind", "spanner.used", "washer.available", "washer.location",
    "bench.level", "bench.vise_secure", "extra_pot.location",
})


def initial(params):
    if not isinstance(params, Parameters):
        raise TypeError("params must be a Parameters instance")
    state = {
        "story.started": False, "story.ended": False, "story.outcome": "",
        "jo.goal": "get Mina's seedling cart rolling safely",
        "jo.admission_style": params.admission_style, "jo.decision": "",
        "jo.owned_error": False, "jo.first_guess": "", "jo.diagnosis": "",
        "jo.checked_spanner": False, "jo.swapped_tool": False, "jo.used_wedge": False,
        "jo.heard_tip": False, "jo.recognized_wrong": False,
        "mina.goal": "carry seedling pots to the courtyard exchange", "mina.trust": 0,
        "mina.knows_wrong_guess": False, "mina.knows_actual_fault": False,
        "mina.delivery": "pending", "len.goal": "keep the courtyard tools useful",
        "len.spanner_ready": True, "len.tip_given": False,
        "cart.location": "bench", "cart.status": "untouched", "cart.load": params.cart_load,
        "cart.capacity": 2, "cart.name_marked": False, "cart.steadied": False,
        "cart.tested": False, "cart.test_passed": False, "cart.out_of_service": False,
        "cart.parked_checked": False, "cart.current_use": "hauling",
        "cart.display_ready": False, "cart.note": "",
        "wheel.rattle": True, "wheel.side_play": True, "wheel.turns_freely": True,
        "wheel.nut": "snug", "wheel.spacer_location": "missing",
        "spanner.owner": "len", "spanner.location": "toolbox",
        "spanner.fits": params.spanner_fits,
        "spanner.kind": "fixed" if params.spanner_fits else "short",
        "spanner.used": False,
        "washer.available": params.washer_available,
        "washer.location": "parts_tin" if params.washer_available else "none",
        "bench.level": params.bench_level, "bench.vise_secure": False,
        "extra_pot.location": "cart" if params.cart_load == 3 else "shelf",
    }
    validate(state)
    return state


def validate(state):
    if not isinstance(state, dict) or set(state) != _STATE_KEYS:
        raise StoryError("State keys do not match the declared courtyard world")
    bool_keys = (
        "story.started", "story.ended", "jo.owned_error", "jo.checked_spanner",
        "jo.swapped_tool", "jo.used_wedge", "jo.heard_tip", "jo.recognized_wrong",
        "mina.knows_wrong_guess", "mina.knows_actual_fault", "len.spanner_ready",
        "len.tip_given", "cart.name_marked", "cart.steadied", "cart.tested",
        "cart.test_passed", "cart.out_of_service", "cart.parked_checked",
        "cart.display_ready", "wheel.rattle", "wheel.side_play", "wheel.turns_freely",
        "spanner.fits", "spanner.used", "washer.available", "bench.level",
        "bench.vise_secure",
    )
    if any(type(state[k]) is not bool for k in bool_keys):
        raise StoryError("Boolean state has the wrong type")
    if type(state["cart.load"]) is not int or not 0 <= state["cart.load"] <= 3:
        raise StoryError("Cart load must be an integer from zero through three")
    if state["cart.capacity"] != 2 or type(state["cart.capacity"]) is not int:
        raise StoryError("The cart's two-pot capacity is fixed")
    if type(state["mina.trust"]) is not int or not 0 <= state["mina.trust"] <= 3:
        raise StoryError("Mina's trust must be an integer from zero through three")
    for key in ("story.outcome", "jo.goal", "jo.admission_style", "jo.decision",
                "jo.first_guess", "jo.diagnosis", "mina.goal", "mina.delivery",
                "len.goal", "cart.location", "cart.status", "cart.current_use", "cart.note",
                "wheel.nut", "wheel.spacer_location", "spanner.owner", "spanner.location",
                "spanner.kind", "washer.location", "extra_pot.location"):
        if not isinstance(state[key], str):
            raise StoryError(f"{key} must be text")
    if state["jo.admission_style"] not in ("early", "late"):
        raise StoryError("Invalid admission style")
    if state["jo.decision"] not in ("", "early", "late"):
        raise StoryError("Invalid choice")
    if state["jo.first_guess"] not in ("", "loose_nut"):
        raise StoryError("Unknown first diagnosis")
    if state["jo.diagnosis"] not in ("", "missing_spacer"):
        raise StoryError("Unknown diagnosis")
    if state["mina.delivery"] not in ("pending", "done_by_cart", "done_by_cart_plus_hand", "done_by_hand"):
        raise StoryError("Unknown delivery state")
    if state["cart.location"] not in ("bench", "exchange_table"):
        raise StoryError("Unknown cart location")
    if state["cart.status"] not in ("untouched", "jammed", "repaired", "parked"):
        raise StoryError("Unknown cart condition")
    if state["cart.current_use"] not in ("hauling", "display"):
        raise StoryError("Unknown cart use")
    if state["spanner.owner"] not in ("len", "jo"):
        raise StoryError("The spanner has one physical owner")
    if state["spanner.kind"] not in ("fixed", "short", "adjustable"):
        raise StoryError("Unknown spanner")
    if (state["spanner.kind"] == "short") == state["spanner.fits"]:
        raise StoryError("Spanner size and fit disagree")
    if state["spanner.owner"] == "jo" and state["spanner.location"] != "jo.hand":
        raise StoryError("Jo's borrowed spanner must be in Jo's hand")
    if state["spanner.owner"] == "len" and state["spanner.location"] not in ("toolbox", "len.hand"):
        raise StoryError("Len's spanner is not where its owner is")
    if state["spanner.location"] == "toolbox" and not state["len.spanner_ready"]:
        raise StoryError("A stored spanner should be ready to borrow")
    if state["spanner.location"] == "len.hand" and state["len.spanner_ready"]:
        raise StoryError("Len is still using the returned spanner")
    if state["spanner.kind"] == "fixed" and not state["spanner.fits"]:
        raise StoryError("The fixed spanner should fit")
    if state["spanner.kind"] == "adjustable" and not state["spanner.fits"]:
        raise StoryError("The adjusted spanner should fit")
    if state["washer.available"]:
        if state["washer.location"] not in ("parts_tin", "jo.hand", "axle"):
            raise StoryError("The available washer has an unknown location")
    elif state["washer.location"] != "none":
        raise StoryError("An unavailable washer cannot appear in the courtyard")
    if state["jo.heard_tip"] != state["len.tip_given"]:
        raise StoryError("The remembered advice must have been spoken")
    if state["cart.steadied"] and not state["bench.level"] and not state["jo.used_wedge"]:
        raise StoryError("A cart on the sloping bench needs a wedge")

    status = state["cart.status"]
    if status == "untouched":
        if not (state["wheel.nut"] == "snug" and state["wheel.turns_freely"]
                and state["wheel.side_play"] and state["wheel.rattle"]):
            raise StoryError("The untouched cart does not match its initial wheel")
    elif status == "jammed":
        if not (state["jo.first_guess"] == "loose_nut" and state["wheel.nut"] == "pinched"
                and not state["wheel.turns_freely"] and state["wheel.side_play"]
                and state["wheel.rattle"]):
            raise StoryError("The first, incorrect repair has inconsistent effects")
    elif status == "repaired":
        if not (state["washer.available"] and state["washer.location"] == "axle"
                and state["wheel.spacer_location"] == "axle" and state["wheel.nut"] == "snug"
                and state["wheel.turns_freely"] and not state["wheel.side_play"]
                and not state["wheel.rattle"] and state["jo.diagnosis"] == "missing_spacer"
                and state["cart.load"] <= state["cart.capacity"]):
            raise StoryError("The repaired wheel needs its spacer and safe clearance")
    else:
        if not (state["wheel.spacer_location"] == "missing" and state["wheel.nut"] == "snug"
                and state["wheel.turns_freely"] and state["wheel.side_play"]
                and state["wheel.rattle"] and state["cart.out_of_service"]
                and state["cart.display_ready"] and state["cart.current_use"] == "display"
                and state["cart.load"] == 0 and state["mina.delivery"] == "done_by_hand"):
            raise StoryError("The unrepaired cart must be secured and taken out of service")
    if state["cart.out_of_service"] != (status == "parked"):
        raise StoryError("Out-of-service status disagrees with the cart condition")
    if state["cart.display_ready"] != (status == "parked"):
        raise StoryError("Only the safely parked cart can be a display")
    if state["cart.current_use"] != ("display" if status == "parked" else "hauling"):
        raise StoryError("The cart's use disagrees with its condition")
    if state["cart.test_passed"] and not (state["cart.tested"] and status == "repaired"):
        raise StoryError("Only a tested repair can pass")
    if state["cart.tested"] and status not in ("repaired", "parked"):
        raise StoryError("An untouched or jammed cart cannot have a final test")
    if status == "parked" and state["cart.note"] != "SPACER NEEDED — DO NOT ROLL":
        raise StoryError("A parked cart needs a clear warning")
    if state["bench.vise_secure"] and not (
        state["spanner.owner"] == "len" and state["spanner.location"] == "toolbox"
        and state["len.spanner_ready"]
    ):
        raise StoryError("The returned spanner must be used before it is stored")
    if state["story.ended"]:
        if not state["story.outcome"] or not (
            state["story.started"] and state["cart.tested"]
            and state["mina.delivery"] != "pending" and state["cart.location"] == "bench"
            and state["cart.load"] == 0 and state["spanner.owner"] == "len"
            and state["spanner.location"] == "toolbox" and state["spanner.used"]
            and state["bench.vise_secure"] and state["jo.owned_error"]
        ):
            raise StoryError("The ending has unfinished physical or emotional business")
    elif state["story.outcome"]:
        raise StoryError("An unfinished story cannot have an outcome")


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f"Unknown scene: {scene_id}")
    validate(state)
    if state["story.ended"]:
        return False
    status = state["cart.status"]
    if scene_id == "borrow":
        return (not state["story.started"] and state["spanner.owner"] == "len"
                and status == "untouched")
    if not state["story.started"]:
        return False
    if scene_id == "chalk_names":
        return status == "untouched" and not state["cart.name_marked"]
    if scene_id == "first_attempt":
        return status == "untouched" and state["spanner.owner"] == "jo"
    if scene_id == "reinspect":
        return status == "jammed" and state["jo.first_guess"] == "loose_nut"
    if scene_id == "measure_story":
        return (status == "jammed" and state["jo.diagnosis"] == "missing_spacer"
                and not state["jo.heard_tip"])
    if scene_id == "admit_error":
        return (state["jo.diagnosis"] == "missing_spacer" and not state["jo.decision"]
                and state["jo.admission_style"] == "early")
    if scene_id == "keep_face":
        return (state["jo.diagnosis"] == "missing_spacer" and not state["jo.decision"]
                and state["jo.admission_style"] == "late")
    if scene_id == "repair":
        return (state["jo.diagnosis"] == "missing_spacer" and bool(state["jo.decision"])
                and status == "jammed" and state["washer.available"])
    if scene_id == "park_it":
        return (state["jo.diagnosis"] == "missing_spacer" and bool(state["jo.decision"])
                and status == "jammed" and not state["washer.available"])
    if scene_id == "test_roll":
        return status == "repaired" and not state["cart.tested"]
    if scene_id == "mark_out":
        return status == "parked" and not state["cart.tested"]
    if scene_id == "ending_repaired":
        return (status == "repaired" and state["cart.tested"] and state["cart.test_passed"]
                and state["jo.admission_style"] == "early")
    if scene_id == "ending_rebuilt":
        return (status == "repaired" and state["cart.tested"] and state["cart.test_passed"]
                and state["jo.admission_style"] == "late")
    if scene_id == "ending_stopped":
        return status == "parked" and state["cart.tested"] and not state["cart.test_passed"]
    raise StoryError(f"No guard for scene: {scene_id}")


@dataclass(frozen=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise TypeError("params must be a Parameters instance")
    validate(state)
    if not guard(scene_id, state):
        raise StoryError(f"Scene not compatible with current state: {scene_id}")
    x = LocalPlay(state, actors=("jo", "mina", "len"), validate=validate)

    if scene_id == "borrow":
        x.act("borrow_spanner", {"spanner.owner": "len", "len.spanner_ready": True},
              **{"spanner.owner": "jo", "spanner.location": "jo.hand",
                 "len.spanner_ready": False, "story.started": True})
    elif scene_id == "chalk_names":
        x.act("write_both_names", {"cart.name_marked": False}, **{"cart.name_marked": True})
    elif scene_id == "first_attempt":
        x.act("steady_cart_with_wedge" if not x.state["bench.level"] else "steady_cart_on_bench",
              {"cart.status": "untouched"}, **{
                  "cart.steadied": True,
                  "jo.used_wedge": not x.state["bench.level"],
              })
        x.act("check_spanner_jaws", {"spanner.owner": "jo"}, **{"jo.checked_spanner": True})
        if not x.state["spanner.fits"]:
            x.act("ask_len_for_adjustable_spanner", {"spanner.fits": False}, **{
                "spanner.fits": True, "spanner.kind": "adjustable", "jo.swapped_tool": True,
            })
        x.act("tighten_the_wrong_nut", {"jo.checked_spanner": True, "spanner.fits": True}, **{
            "cart.status": "jammed", "cart.steadied": False, "wheel.nut": "pinched",
            "wheel.turns_freely": False, "jo.first_guess": "loose_nut", "spanner.used": True,
        })
    elif scene_id == "reinspect":
        x.act("compare_hub_and_fork", {"cart.status": "jammed", "wheel.rattle": True}, **{
            "jo.diagnosis": "missing_spacer", "jo.recognized_wrong": True,
            "mina.knows_actual_fault": True,
        })
    elif scene_id == "measure_story":
        x.act("len_shares_old_repair_lesson", {"jo.heard_tip": False}, **{
            "jo.heard_tip": True, "len.tip_given": True,
        })
    elif scene_id == "admit_error":
        x.act("tell_mina_the_first_guess_was_wrong", {"jo.admission_style": "early"}, **{
            "jo.decision": "early", "jo.owned_error": True,
            "mina.knows_wrong_guess": True, "mina.trust": 2,
        })
    elif scene_id == "keep_face":
        x.act("put_off_the_admission", {"jo.admission_style": "late"}, **{
            "jo.decision": "late", "mina.knows_wrong_guess": False, "mina.trust": 0,
        })
    elif scene_id == "repair":
        if x.state["cart.load"] == 3:
            x.act("set_one_pot_on_the_bench_shelf", {"cart.load": 3, "extra_pot.location": "cart"}, **{
                "cart.load": 2, "extra_pot.location": "bench_shelf",
            })
        x.act("take_spare_washer_from_tin", {"washer.location": "parts_tin"}, **{
            "washer.location": "jo.hand",
        })
        x.act("fit_washer_and_set_clearance", {"washer.location": "jo.hand", "cart.status": "jammed"}, **{
            "washer.location": "axle", "wheel.spacer_location": "axle", "wheel.nut": "snug",
            "wheel.turns_freely": True, "wheel.side_play": False, "wheel.rattle": False,
            "cart.status": "repaired",
        })
    elif scene_id == "park_it":
        extra_location = "exchange_table" if x.state["extra_pot.location"] == "cart" else x.state["extra_pot.location"]
        x.act("refuse_an_unsafe_cardboard_shim", {"washer.available": False, "cart.status": "jammed"}, **{
            "wheel.nut": "snug", "wheel.turns_freely": True, "cart.status": "parked",
            "cart.out_of_service": True, "cart.display_ready": True, "cart.current_use": "display",
            "cart.note": "SPACER NEEDED — DO NOT ROLL", "cart.load": 0,
            "extra_pot.location": extra_location, "mina.delivery": "done_by_hand",
        })
    elif scene_id == "test_roll":
        delivery = "done_by_cart_plus_hand" if params.cart_load == 3 else "done_by_cart"
        changes = {
            "cart.tested": True, "cart.test_passed": True, "cart.location": "exchange_table",
            "cart.load": 0, "mina.delivery": delivery,
        }
        if params.cart_load == 3:
            changes["extra_pot.location"] = "exchange_table"
        x.act("roll_the_safe_load_to_the_exchange", {"cart.status": "repaired", "cart.load": 2}
              if x.state["cart.load"] == 2 else {"cart.status": "repaired"}, **changes)
    elif scene_id == "mark_out":
        x.act("check_the_wobble_without_rolling_and_tag_cart", {
            "cart.status": "parked", "cart.out_of_service": True,
        }, **{"cart.tested": True, "cart.parked_checked": True})
    else:
        # All three ending scenes enact the same physical return; their guards
        # and outcome labels distinguish what the children have earned.
        if scene_id == "ending_repaired":
            outcome = "cart_repaired_and_seedlings_delivered"
        elif scene_id == "ending_rebuilt":
            outcome = "cart_repaired_after_a_late_apology"
        else:
            outcome = "cart_parked_safely_and_seedlings_delivered_by_hand"
        x.act("return_borrowed_spanner", {"spanner.owner": "jo", "spanner.used": True}, **{
            "spanner.owner": "len", "spanner.location": "len.hand", "len.spanner_ready": False,
        })
        x.act("len_uses_spanner_on_bench_vise", {"spanner.owner": "len", "spanner.location": "len.hand"}, **{
            "spanner.location": "toolbox", "len.spanner_ready": True, "bench.vise_secure": True,
        })
        if x.state["cart.status"] == "repaired":
            x.act("park_delivered_cart_by_bench", {"cart.location": "exchange_table"}, **{
                "cart.location": "bench",
            })
        if not x.state["jo.owned_error"]:
            x.act("own_the_first_mistake_now", {"jo.owned_error": False}, **{
                "jo.owned_error": True, "mina.knows_wrong_guess": True, "mina.trust": 1,
            })
        x.act("finish_with_the_truth_told", {"cart.tested": True}, **{
            "story.ended": True, "story.outcome": outcome,
        })

    after = x.state
    validate(after)
    return Episode(
        id=scene_id, before=deepcopy(state), after=deepcopy(after),
        events=tuple(deepcopy(x.events)), text=render(scene_id, params, state, after),
    )


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(count) is not int or count not in (7, 8):
        raise ValueError("This adventure supports exactly seven or eight scenes")
    p = params if params is not None else parameters(seed)
    if not isinstance(p, Parameters):
        raise TypeError("params must be a Parameters instance")
    rng = random.Random(seed)
    attempts = 0
    expanded = 0
    seen = set()

    def search(state, episodes, used):
        nonlocal attempts, expanded
        expanded += 1
        if expanded > 5000:
            raise StoryError("Scene search budget exhausted")
        if len(episodes) == count:
            return episodes if state["story.ended"] else None
        if state["story.ended"]:
            return None
        remaining = count - len(episodes)
        signature = json.dumps([state, sorted(used), remaining], sort_keys=True)
        if signature in seen:
            return None
        seen.add(signature)
        choices = [scene_id for scene_id in SCENES if scene_id not in used and guard(scene_id, state)]
        if remaining != 1:
            choices = [s for s in choices if not s.startswith("ending_")]
        rng.shuffle(choices)
        for scene_id in choices:
            attempts += 1
            if attempts > 12000:
                raise StoryError("Scene search attempt budget exhausted")
            episode = play_scene(p, state, scene_id)
            answer = search(episode.after, episodes + (episode,), used | {scene_id})
            if answer is not None:
                return answer
        return None

    episodes = search(initial(p), (), frozenset())
    if episodes is None:
        raise StoryError("No compatible complete route at the requested length")
    story = "\n\n".join(e.text for e in episodes)
    return {
        "seed": seed,
        "parameters": asdict(p),
        "scene_count": count,
        "path": [e.id for e in episodes],
        "story": story,
        "episodes": [{
            "id": e.id, "before": deepcopy(e.before), "after": deepcopy(e.after),
            "events": deepcopy(list(e.events)), "text": e.text,
        } for e in episodes],
        "final_state": deepcopy(episodes[-1].after),
        "search_attempts": attempts,
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise TypeError("params must be a Parameters instance")
    state = initial(params)
    episodes = []
    used = set()
    for scene_id in path:
        if scene_id in used:
            raise StoryError(f"A scene cannot be repeated: {scene_id}")
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        used.add(scene_id)
        state = episode.after
    return tuple(episodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--scenes", type=int, choices=(7, 8), default=8)
    parser.add_argument("--params", help="JSON file containing Parameters keyword values")
    args = parser.parse_args()
    try:
        p = Parameters(**json.loads(open(args.params, encoding="utf-8").read())) if args.params else None
        row = generate(args.seed, count=args.scenes, params=p)
    except (ValueError, TypeError, json.JSONDecodeError, OSError) as exc:
        parser.error(str(exc))
    print(row["story"])


if __name__ == "__main__":
    main()
