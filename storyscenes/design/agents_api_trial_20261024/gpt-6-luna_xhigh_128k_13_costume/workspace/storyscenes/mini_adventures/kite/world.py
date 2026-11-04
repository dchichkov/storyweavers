"""A costume-cupboard adventure with guarded local plays and persistent state.

Run with ``python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8``.
No network calls or runtime language models are used.
"""
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
    seam_allowance: int = 1
    pins_available: bool = True
    teacher_available: bool = True
    minutes_left: int = 2
    mirror_clear: bool = True
    stage_lamp: bool = True

    def __post_init__(self):
        if type(self.seam_allowance) is not int or not 0 <= self.seam_allowance <= 2:
            raise ValueError("seam_allowance must be an integer in [0, 2]")
        if type(self.minutes_left) is not int or not 1 <= self.minutes_left <= 3:
            raise ValueError("minutes_left must be an integer in [1, 3]")
        for name in ("pins_available", "teacher_available", "mirror_clear", "stage_lamp"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be boolean")


def parameters(seed):
    rng = random.Random(seed)
    return Parameters(
        seam_allowance=rng.choice((0, 1, 2)),
        pins_available=rng.choice((True, False)),
        teacher_available=rng.choice((True, False)),
        minutes_left=rng.choice((1, 2, 3)),
        mirror_clear=rng.choice((True, False)),
        stage_lamp=rng.choice((True, False)),
    )


def initial(params):
    if not isinstance(params, Parameters):
        raise TypeError("params must be a Parameters instance")
    state = {
        "story.started": False, "story.ended": False, "story.outcome": "",
        "place": "costume_cupboard", "ada.goal": "help Jo play the promised Storm role",
        "jo.promised_role": "Storm", "jo.spoke_up": False, "jo.label_seen": False,
        "jo.tunic_tried": False, "jo.tunic_attempted": False, "jo.costume": "moon_tunic",
        "jo.costume_fits": False, "jo.wears_costume": False, "jo.refitted": False,
        "jo.declined_tunic": False, "jo.saw_fit_issue": False, "jo.was_heard": False,
        "jo.performed": False, "jo.role_performed": "", "jo.performance_style": "",
        "jo.applause": False, "jo.plan": "",
        "teacher.available": params.teacher_available, "teacher.consulted": False,
        "teacher.answer": "unasked", "teacher.acknowledged": False,
        "minutes.start": params.minutes_left, "minutes.left": params.minutes_left,
        "costume.storm_reserved": False,
        "moon_tunic.location": "rack", "moon_tunic.design": "moon",
        "storm_coat.location": "teacher_rail" if params.teacher_available else "school_store",
        "pins.available": params.pins_available, "seam.allowance": params.seam_allowance,
        "cape.owner": "school", "cape.holder": "wardrobe", "cape.location": "cupboard_hook",
        "cape.borrowed": False, "cape.tested": False, "cape.used": False,
        "cape.use": "unused", "cape.returned": False,
        "mirror.clean": params.mirror_clear, "mirror.used": False,
        "ribbon.location": "drawer", "ribbon.chosen": False, "ribbon.used": False,
        "ribbon.returned": False, "rehearsal.ready": False,
        "performance.done": False,
    }
    validate(state)
    return state


def validate(state):
    required = {
        "story.started", "story.ended", "story.outcome", "place", "ada.goal",
        "jo.promised_role", "jo.spoke_up", "jo.label_seen", "jo.tunic_tried",
        "jo.tunic_attempted", "jo.costume", "jo.costume_fits", "jo.wears_costume",
        "jo.refitted", "jo.declined_tunic", "jo.saw_fit_issue", "jo.was_heard",
        "jo.performed", "jo.role_performed", "jo.performance_style", "jo.applause",
        "jo.plan", "teacher.available", "teacher.consulted", "teacher.answer",
        "teacher.acknowledged", "minutes.start", "minutes.left", "costume.storm_reserved",
        "moon_tunic.location", "moon_tunic.design", "storm_coat.location", "pins.available",
        "seam.allowance", "cape.owner", "cape.holder", "cape.location", "cape.borrowed",
        "cape.tested", "cape.used", "cape.use", "cape.returned", "mirror.clean",
        "mirror.used", "ribbon.location", "ribbon.chosen", "ribbon.used",
        "ribbon.returned", "rehearsal.ready", "performance.done",
    }
    missing = required - set(state)
    if missing:
        raise StoryError(f"Missing state keys: {sorted(missing)}")
    bools = ("story.started", "story.ended", "jo.spoke_up", "jo.label_seen", "jo.tunic_tried",
             "jo.tunic_attempted", "jo.costume_fits", "jo.wears_costume", "jo.refitted",
             "jo.declined_tunic", "jo.saw_fit_issue", "jo.was_heard", "jo.performed",
             "jo.applause", "teacher.available", "teacher.consulted", "teacher.acknowledged",
             "costume.storm_reserved", "pins.available", "cape.borrowed", "cape.tested",
             "cape.used", "cape.returned", "mirror.clean", "mirror.used", "ribbon.chosen",
             "ribbon.used", "ribbon.returned", "rehearsal.ready", "performance.done")
    for key in bools:
        if type(state[key]) is not bool:
            raise StoryError(f"{key} must be boolean")
    for key in ("minutes.start", "minutes.left", "seam.allowance"):
        if type(state[key]) is not int:
            raise StoryError(f"{key} must be an integer")
    strings = required - set(bools) - {"minutes.start", "minutes.left", "seam.allowance"}
    if any(not isinstance(state[key], str) for key in strings):
        raise StoryError("Text state values must be strings")
    if any(type(v) not in (str, bool, int, float) for v in state.values()):
        raise StoryError("State values must be JSON-native scalars")

    def need(condition, message):
        if not condition:
            raise StoryError(message)

    need(state["place"] in ("costume_cupboard", "backstage", "stage"), "Unknown location")
    need(state["jo.promised_role"] == "Storm", "The promised role changed")
    need(state["seam.allowance"] in (0, 1, 2), "Invalid seam allowance")
    need(state["minutes.start"] in (1, 2, 3), "Invalid starting time")
    need(0 <= state["minutes.left"] <= state["minutes.start"], "Invalid remaining time")
    need(state["cape.owner"] == "school", "The cape belongs to the school")
    need(state["cape.holder"] in ("wardrobe", "ada"), "Unknown cape holder")
    need(state["cape.use"] in ("unused", "wind_gust", "shadow", "wind_sail"), "Unknown cape use")
    need(state["cape.used"] == (state["cape.use"] != "unused"), "Cape use record disagrees")
    if state["cape.holder"] == "wardrobe":
        need(state["cape.location"] == "cupboard_hook" and not state["cape.borrowed"], "Cape custody disagrees")
        need(state["cape.returned"] == state["cape.used"], "Used cape must be returned")
    else:
        need(state["cape.location"] == "ada_hands" and state["cape.borrowed"] and not state["cape.returned"],
             "Borrowed cape custody disagrees")
    if state["cape.used"]:
        need(state["cape.tested"] and state["rehearsal.ready"], "Cape use needs the enacted rehearsal")
    need(state["moon_tunic.location"] in ("rack", "jo_hands", "jo"), "Unknown tunic location")
    need(state["storm_coat.location"] in ("teacher_rail", "school_store", "jo"), "Unknown Storm coat location")
    need(state["moon_tunic.design"] in ("moon", "storm"), "Unknown tunic design")
    if state["jo.costume"] == "storm_coat":
        need(state["jo.costume_fits"] and state["jo.wears_costume"], "Storm coat must fit when worn")
        need(state["storm_coat.location"] == "jo" and state["moon_tunic.location"] == "rack",
             "Costume exchange locations disagree")
        need(state["teacher.answer"] == "matching_coat", "No matching coat was offered")
    elif state["jo.costume"] == "moon_tunic":
        if state["jo.costume_fits"]:
            need(state["moon_tunic.design"] == "storm" and state["moon_tunic.location"] == "jo"
                 and state["jo.wears_costume"], "Altered tunic is not being worn")
        else:
            need(state["moon_tunic.design"] == "moon" and not state["jo.wears_costume"],
                 "An unsuitable tunic cannot be worn as a fit")
            need(state["moon_tunic.location"] in ("rack", "jo_hands"), "Unsuitable tunic is misplaced")
    else:
        raise StoryError("Unknown costume")
    if state["jo.refitted"] and not state["jo.costume_fits"]:
        need(state["jo.declined_tunic"] and state["moon_tunic.location"] == "rack",
             "An unfit costume must be declined and put back")
    if state["jo.costume_fits"]:
        need(state["jo.refitted"], "A fitting costume needs an enacted refit")
    if state["teacher.answer"] == "unasked":
        need(not state["teacher.consulted"] and state["minutes.left"] == state["minutes.start"],
             "Unasked teacher has no consultation cost")
    else:
        need(state["teacher.consulted"] and state["teacher.answer"] in ("matching_coat", "not_in_time"),
             "Invalid teacher answer")
        need(state["minutes.left"] == max(0, state["minutes.start"] - 1), "Consultation time was not recorded")
    if state["costume.storm_reserved"]:
        need(state["teacher.answer"] == "matching_coat" and state["storm_coat.location"] == "teacher_rail",
             "Reserved coat is unavailable")
    if state["teacher.answer"] == "matching_coat":
        need(state["teacher.available"] and state["minutes.start"] >= 2, "Coat appeared without time or teacher")
    if state["jo.tunic_attempted"]:
        need(state["teacher.consulted"] and state["teacher.answer"] == "not_in_time", "Seam test preceded the answer")
    if state["mirror.used"]:
        need(state["mirror.clean"] and state["story.started"] and state["jo.saw_fit_issue"], "Mirror scene incomplete")
    need(state["ribbon.location"] in ("drawer", "cape_edge"), "Unknown ribbon location")
    if state["ribbon.chosen"]:
        need(state["ribbon.location"] == ("drawer" if state["ribbon.returned"] else "cape_edge"),
             "Chosen ribbon is not with the cape or returned")
        need(state["ribbon.used"] == state["performance.done"], "Ribbon use must match the performance")
    else:
        need(state["ribbon.location"] == "drawer" and not state["ribbon.used"] and not state["ribbon.returned"],
             "Unchosen ribbon moved")
    if state["rehearsal.ready"]:
        need(state["jo.refitted"] and state["cape.used"] and state["place"] in ("backstage", "stage"),
             "Rehearsal lacks its preparation")
        need(state["jo.plan"] in ("storm_costume", "storm_shadow", "storm_sail"), "Missing performance plan")
    if state["place"] == "stage":
        need(state["rehearsal.ready"] and not state["performance.done"], "Invalid stage transition")
    if state["performance.done"]:
        need(state["place"] == "backstage" and state["jo.performed"] and state["jo.applause"],
             "Performance is incomplete")
        need(state["jo.role_performed"] == "Storm" and state["jo.performance_style"] == state["jo.plan"],
             "Performance does not match the rehearsal")
    else:
        need(state["jo.role_performed"] == "" and state["jo.performance_style"] == "", "Unperformed role recorded")
    need(state["story.ended"] == (state["story.outcome"] != ""), "Ending flag and outcome disagree")
    if state["story.ended"]:
        need(state["performance.done"] and state["cape.returned"] and state["jo.was_heard"]
             and state["teacher.acknowledged"] and state["place"] == "backstage", "Ending left a payoff unfinished")
        need(state["ribbon.returned"] == state["ribbon.chosen"], "Borrowed ribbon was not returned")
        expected = "storm_costume_restored" if state["jo.costume_fits"] else "storm_reimagined"
        need(state["story.outcome"] == expected, "Ending does not match the enacted outcome")
    else:
        need(state["story.outcome"] == "", "Premature outcome")


@dataclass(frozen=True, kw_only=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


SCENES = (
    "opening", "borrow_cape", "mirror_vignette", "ribbon_vignette", "consult_teacher",
    "refit_costume", "rehearse", "performance", "ending_fit", "ending_improvised",
)
_OPTIONAL = {"mirror_vignette", "ribbon_vignette"}
_ENDINGS = {"ending_fit", "ending_improvised"}


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f"Unknown scene: {scene_id}")
    validate(state)
    if state["story.ended"]:
        return False
    if scene_id == "opening":
        return not state["story.started"] and state["place"] == "costume_cupboard"
    if scene_id == "borrow_cape":
        return state["story.started"] and not state["cape.borrowed"] and state["place"] == "costume_cupboard"
    if scene_id == "mirror_vignette":
        return (state["story.started"] and not state["mirror.used"] and not state["teacher.consulted"]
                and state["place"] == "costume_cupboard")
    if scene_id == "ribbon_vignette":
        return (state["story.started"] and not state["ribbon.chosen"] and not state["teacher.consulted"]
                and state["place"] == "costume_cupboard")
    if scene_id == "consult_teacher":
        return (state["story.started"] and state["cape.borrowed"] and not state["teacher.consulted"]
                and state["place"] == "costume_cupboard")
    if scene_id == "refit_costume":
        return state["teacher.consulted"] and not state["jo.refitted"] and state["place"] == "costume_cupboard"
    if scene_id == "rehearse":
        return (state["jo.refitted"] and not state["rehearsal.ready"] and state["cape.borrowed"]
                and state["place"] == "costume_cupboard")
    if scene_id == "performance":
        return state["rehearsal.ready"] and not state["performance.done"] and state["place"] == "backstage"
    if scene_id == "ending_fit":
        return state["performance.done"] and state["jo.costume_fits"]
    if scene_id == "ending_improvised":
        return state["performance.done"] and not state["jo.costume_fits"]
    return False


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise TypeError("params must be a Parameters instance")
    if scene_id not in SCENES or not guard(scene_id, state):
        raise StoryError(f"Scene not compatible with current state: {scene_id}")
    x = LocalPlay(state, actors=("Ada", "Jo"), validate=validate)

    if scene_id == "opening":
        x.act("try_on_moon_tunic", {"moon_tunic.location": "rack"},
              **{"moon_tunic.location": "jo_hands", "jo.tunic_tried": True})
        x.act("say_the_promise", {"jo.promised_role": "Storm"},
              **{"story.started": True, "jo.spoke_up": True, "jo.label_seen": True})
    elif scene_id == "borrow_cape":
        x.act("borrow_school_cape", {"cape.holder": "wardrobe"},
              **{"cape.holder": "ada", "cape.location": "ada_hands", "cape.borrowed": True})
        x.act("test_wind_with_cape", {"cape.borrowed": True}, **{"cape.tested": True})
    elif scene_id == "mirror_vignette":
        if not x.state["mirror.clean"]:
            x.act("wipe_cupboard_mirror", {"mirror.clean": False}, **{"mirror.clean": True})
        x.act("look_together", {"mirror.clean": True},
              **{"mirror.used": True, "jo.saw_fit_issue": True})
    elif scene_id == "ribbon_vignette":
        x.act("tie_silver_ribbon_to_cape", {"ribbon.location": "drawer"},
              **{"ribbon.location": "cape_edge", "ribbon.chosen": True})
    elif scene_id == "consult_teacher":
        available = x.state["teacher.available"] and x.state["minutes.left"] >= 2
        answer = "matching_coat" if available else "not_in_time"
        x.act("ask_about_storm_costume", {"teacher.consulted": False}, **{
            "teacher.consulted": True, "teacher.answer": answer,
            "costume.storm_reserved": available,
            "minutes.left": max(0, x.state["minutes.left"] - 1),
        })
    elif scene_id == "refit_costume":
        if x.state["teacher.answer"] == "matching_coat":
            x.act("exchange_for_fitting_storm_coat", {"costume.storm_reserved": True}, **{
                "jo.costume": "storm_coat", "jo.costume_fits": True, "jo.wears_costume": True,
                "jo.refitted": True, "storm_coat.location": "jo", "moon_tunic.location": "rack",
                "costume.storm_reserved": False,
            })
            x.act("agree_to_the_fit", {"jo.costume_fits": True}, **{"jo.declined_tunic": False})
        else:
            x.act("test_tunic_seam", {"jo.tunic_tried": True}, **{"jo.tunic_attempted": True})
            if x.state["seam.allowance"] >= 1 and x.state["pins.available"]:
                x.act("let_out_seam_with_pins", {
                    "jo.tunic_attempted": True, "pins.available": True,
                    "seam.allowance": x.state["seam.allowance"],
                }, **{
                    "jo.costume_fits": True, "jo.wears_costume": True, "jo.refitted": True,
                    "jo.declined_tunic": False, "moon_tunic.design": "storm",
                    "moon_tunic.location": "jo", "pins.available": False,
                })
            else:
                x.act("decline_the_tight_tunic", {"jo.tunic_attempted": True}, **{
                    "jo.refitted": True, "jo.declined_tunic": True, "moon_tunic.location": "rack",
                })
    elif scene_id == "rehearse":
        if x.state["jo.costume_fits"]:
            plan, use = "storm_costume", "wind_gust"
        elif params.stage_lamp:
            plan, use = "storm_shadow", "shadow"
        else:
            plan, use = "storm_sail", "wind_sail"
        x.act("build_the_storm_picture", {"cape.tested": True, "jo.refitted": True}, **{
            "jo.plan": plan, "cape.use": use, "cape.used": True,
            "rehearsal.ready": True, "place": "backstage",
        })
    elif scene_id == "performance":
        x.act("take_the_stage_cue", {"place": "backstage"}, **{"place": "stage"})
        changes = {
            "place": "backstage", "performance.done": True, "jo.performed": True,
            "jo.role_performed": "Storm", "jo.performance_style": x.state["jo.plan"],
            "jo.applause": True,
        }
        if x.state["ribbon.chosen"]:
            changes["ribbon.used"] = True
        x.act("perform_the_promised_storm", {"place": "stage", "rehearsal.ready": True}, **changes)
    elif scene_id in _ENDINGS:
        x.act("acknowledge_jo", {"performance.done": True}, **{
            "jo.was_heard": True, "teacher.acknowledged": True,
        })
        x.act("return_useful_borrowed_cape", {
            "cape.holder": "ada", "cape.used": True,
        }, **{
            "cape.holder": "wardrobe", "cape.location": "cupboard_hook",
            "cape.borrowed": False, "cape.returned": True,
        })
        if x.state["ribbon.chosen"]:
            x.act("return_silver_ribbon", {"ribbon.location": "cape_edge", "ribbon.used": True}, **{
                "ribbon.location": "drawer", "ribbon.returned": True,
            })
        outcome = "storm_costume_restored" if scene_id == "ending_fit" else "storm_reimagined"
        x.act("close_the_play", {"jo.was_heard": True}, **{
            "story.ended": True, "story.outcome": outcome,
        })

    after = deepcopy(x.state)
    validate(after)
    return Episode(
        id=scene_id, before=deepcopy(state), after=after,
        events=tuple(deepcopy(x.events)), text=render(scene_id, params, state, after),
    )


def _episode_dict(episode):
    return {
        "id": episode.id, "before": deepcopy(episode.before), "after": deepcopy(episode.after),
        "events": deepcopy(list(episode.events)), "text": episode.text,
    }


def _required_scenes(state):
    return sum((
        not state["story.started"], not state["cape.borrowed"], not state["teacher.consulted"],
        not state["jo.refitted"], not state["rehearsal.ready"], not state["performance.done"],
        not state["story.ended"],
    ))


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(count) is not int or count not in (7, 8):
        raise ValueError("count must be exactly 7 or 8")
    p = params if params is not None else parameters(seed)
    if not isinstance(p, Parameters):
        raise TypeError("params must be a Parameters instance")
    rng = random.Random(seed)
    attempts = 0
    budget = 5000

    def search(state, episodes):
        nonlocal attempts
        remaining = count - len(episodes)
        needed = _required_scenes(state)
        if remaining < needed or remaining > needed + 1:
            return None
        if remaining > needed and not any(guard(s, state) for s in _OPTIONAL if s not in {e.id for e in episodes}):
            return None
        if remaining == 0:
            return episodes if state["story.ended"] else None
        used = {e.id for e in episodes}
        choices = [s for s in SCENES if s not in used and guard(s, state)]
        rng.shuffle(choices)
        for scene_id in choices:
            if scene_id in _ENDINGS and remaining != 1:
                continue
            attempts += 1
            if attempts > budget:
                raise StoryError(f"Bounded scene search exhausted ({budget} attempts)")
            episode = play_scene(p, state, scene_id)
            answer = search(episode.after, episodes + (episode,))
            if answer is not None:
                return answer
        return None

    episodes = search(initial(p), ())
    if episodes is None:
        raise StoryError("No compatible complete route at the requested length")
    episode_rows = [_episode_dict(e) for e in episodes]
    return {
        "seed": seed, "parameters": asdict(p), "scene_count": count,
        "path": [e.id for e in episodes],
        "story": "\n\n".join(e.text for e in episodes),
        "episodes": episode_rows, "final_state": deepcopy(episodes[-1].after),
        "search_attempts": attempts,
    }


def replay(params, path):
    if not isinstance(params, Parameters):
        raise TypeError("params must be a Parameters instance")
    state = initial(params)
    episodes = []
    for scene_id in path:
        if scene_id in {episode.id for episode in episodes}:
            raise StoryError(f"A scene cannot be repeated: {scene_id}")
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode.after
    return tuple(episodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--scenes", type=int, choices=(7, 8), default=8)
    parser.add_argument("--params", help="JSON object overriding generated Parameters")
    args = parser.parse_args()
    overrides = json.loads(args.params) if args.params else {}
    if not isinstance(overrides, dict):
        parser.error("--params must be a JSON object")
    try:
        p = Parameters(**(asdict(parameters(args.seed)) | overrides))
        row = generate(args.seed, count=args.scenes, params=p)
    except (TypeError, ValueError, StoryError) as exc:
        parser.error(str(exc))
    print(row["story"])


if __name__ == "__main__":
    main()
