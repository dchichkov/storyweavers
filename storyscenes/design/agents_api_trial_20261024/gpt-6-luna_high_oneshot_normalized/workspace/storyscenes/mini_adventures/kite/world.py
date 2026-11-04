"""Seeded, bounded kite-adventure composition with traceable local actions."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import random

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .prose import render


@dataclass(frozen=True, kw_only=True)
class Parameters:
    wind: int = 1
    reel_wear: int = 0
    frame_strength: int = 3
    shyness: int = 1

    def __post_init__(self):
        for key, low, high in (("wind", 1, 3), ("reel_wear", 0, 2),
                               ("frame_strength", 1, 3), ("shyness", 1, 3)):
            value = getattr(self, key)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{key} must be an integer in [{low}, {high}]")


def parameters(seed):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    rng = random.Random(seed)
    return Parameters(wind=rng.randint(1, 3), reel_wear=rng.randint(0, 2),
                      frame_strength=rng.randint(1, 3), shyness=rng.randint(1, 3))


def initial(params):
    if not isinstance(params, Parameters):
        raise TypeError("params must be a Parameters instance")
    return {
        "story.stage": "start", "story.ended": False, "story.outcome": "",
        "nia.location": "workshop", "nia.wants": "fly a kite together",
        "nia.skill": 0,
        "pavel.location": "home", "pavel.wants": "join without being put on display",
        "pavel.shyness": params.shyness, "pavel.comfort": 0, "pavel.invited": False,
        "pavel.task": "none",
        "tamsin.location": "workshop",
        "workshop.willow_strength": params.frame_strength,
        "weather.wind": params.wind,
        "reel.owner": "Tamsin", "reel.location": "workshop", "reel.borrowed": False,
        "reel.returned": False, "reel.wear": params.reel_wear,
        "reel.string_left": 100, "reel.usefulness": "unused",
        "kite.location": "workshop", "kite.status": "unbuilt", "kite.ready": False,
        "kite.frame_strength": 0, "kite.ribbon": False,
        "practice.done": False,
        "flight.mode": "", "flight.result": "",
    }


STATE_KEYS = frozenset(initial(Parameters()).keys())
SCENES = (
    "workshop", "build", "invite", "ribbon", "practice", "hand_reel",
    "keep_reel", "launch", "ending_airborne_shared", "ending_airborne_guided",
    "ending_grounded",
)


@dataclass(frozen=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


def validate(state):
    if not isinstance(state, dict) or frozenset(state) != STATE_KEYS:
        raise StoryError("State has missing or undeclared keys")
    for key, value in state.items():
        if type(value) not in (str, bool, int, float):
            raise StoryError(f"State value is not a JSON scalar: {key}")
    if state["story.stage"] not in {"start", "borrowed", "prepared", "invited", "chosen",
                                    "flown", "returning", "ended"}:
        raise StoryError("Unknown story stage")
    if type(state["story.ended"]) is not bool or state["story.ended"] != (state["story.stage"] == "ended"):
        raise StoryError("Ending flag and stage disagree")
    if state["story.ended"] != bool(state["story.outcome"]):
        raise StoryError("An ended story needs exactly one nonempty outcome")
    if state["nia.location"] not in {"workshop", "field"} or state["pavel.location"] not in {"home", "field", "workshop"}:
        raise StoryError("Unknown character location")
    if state["kite.location"] not in {"workshop", "field", "air"}:
        raise StoryError("Unknown kite location")
    if state["reel.location"] not in {"workshop", "Nia", "Pavel"}:
        raise StoryError("Unknown reel location")
    if state["reel.owner"] != "Tamsin":
        raise StoryError("The workshop reel remains Tamsin's property")
    for key, low, high in (("weather.wind", 1, 3), ("reel.wear", 0, 2),
                           ("reel.string_left", 0, 100), ("workshop.willow_strength", 1, 3),
                           ("kite.frame_strength", 0, 3), ("pavel.shyness", 1, 3),
                           ("pavel.comfort", 0, 3), ("nia.skill", 0, 1)):
        if type(state[key]) is not int or not low <= state[key] <= high:
            raise StoryError(f"Invalid numeric state: {key}")
    for key in ("reel.borrowed", "reel.returned", "kite.ready", "kite.ribbon",
                "practice.done", "pavel.invited"):
        if type(state[key]) is not bool:
            raise StoryError(f"Invalid boolean state: {key}")
    if state["reel.returned"]:
        if (not state["reel.borrowed"] or state["reel.location"] != "workshop"
                or state["reel.usefulness"] != "ready for another flight"):
            raise StoryError("The borrowed reel must return useful to its owner")
    elif state["reel.borrowed"]:
        if state["reel.location"] not in {"Nia", "Pavel"}:
            raise StoryError("The borrowed reel has no current holder")
    elif state["reel.location"] != "workshop":
        raise StoryError("An unborrowed reel must remain in the workshop")
    if state["story.stage"] == "start":
        if state["reel.borrowed"] or state["kite.ready"]:
            raise StoryError("The opening state is already advanced")
    elif state["story.stage"] == "borrowed":
        if not state["reel.borrowed"] or state["kite.ready"]:
            raise StoryError("Borrowing and kite-building are out of order")
    elif state["story.stage"] in {"prepared", "invited", "chosen"}:
        if not state["reel.borrowed"] or not state["kite.ready"]:
            raise StoryError("Prepared scenes need the borrowed reel and built kite")
    if state["story.stage"] in {"start", "borrowed"}:
        if state["kite.status"] != "unbuilt" or state["kite.ready"]:
            raise StoryError("Unbuilt kite state is inconsistent")
    elif state["story.stage"] in {"prepared", "invited", "chosen"}:
        if state["kite.status"] != "ready" or not state["kite.ready"]:
            raise StoryError("Ready kite state is inconsistent")
    elif state["story.stage"] == "flown":
        if state["flight.result"] not in {"aloft", "grounded"} or state["kite.status"] != state["flight.result"]:
            raise StoryError("Flight result and kite condition disagree")
        if state["kite.location"] != ("air" if state["flight.result"] == "aloft" else "field"):
            raise StoryError("Flight location and result disagree")
    elif state["story.stage"] in {"returning", "ended"}:
        if state["kite.status"] != "recovered" or state["kite.location"] != "workshop":
            raise StoryError("The returned kite is not safely put away")
    if state["pavel.invited"] != (state["story.stage"] in {"invited", "chosen", "flown", "returning", "ended"}):
        raise StoryError("Invitation and story stage disagree")
    if state["story.stage"] in {"start", "borrowed", "prepared", "invited"}:
        if state["flight.mode"] or state["flight.result"]:
            raise StoryError("Flight began before the children chose how to fly")
    if state["story.stage"] in {"chosen", "flown", "returning", "ended"} and state["flight.mode"] not in {"Nia", "Pavel"}:
        raise StoryError("A flight needs a chosen reel holder")
    if state["story.stage"] in {"start", "borrowed", "prepared", "invited", "chosen"} and state["flight.result"]:
        raise StoryError("A flight result appeared too early")
    if state["story.ended"]:
        if not state["reel.returned"] or state["pavel.location"] != "workshop" or state["nia.location"] != "workshop":
            raise StoryError("The ending leaves the children or borrowed object unaccounted for")
        expected = {"shared_flight": ("aloft", "Pavel"),
                    "guided_flight": ("aloft", "Nia"),
                    "safe_landing": ("grounded", None)}
        if state["story.outcome"] not in expected:
            raise StoryError("Unknown ending outcome")
        result, mode = expected[state["story.outcome"]]
        if state["flight.result"] != result or (mode is not None and state["flight.mode"] != mode):
            raise StoryError("Ending does not match the flight that occurred")


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f"Unknown scene: {scene_id}")
    validate(state)
    stage = state["story.stage"]
    if state["story.ended"]:
        return False
    if scene_id == "workshop":
        return stage == "start"
    if scene_id == "build":
        return stage == "borrowed"
    if scene_id == "invite":
        return stage == "prepared"
    if scene_id == "ribbon":
        return stage == "invited" and not state["kite.ribbon"]
    if scene_id == "practice":
        return stage == "invited" and not state["practice.done"]
    if scene_id == "hand_reel":
        return stage == "invited" and state["pavel.comfort"] >= 2 and not state["flight.mode"]
    if scene_id == "keep_reel":
        return stage == "invited" and not state["flight.mode"]
    if scene_id == "launch":
        return stage == "chosen"
    if stage != "flown":
        return False
    if scene_id == "ending_airborne_shared":
        return state["flight.result"] == "aloft" and state["flight.mode"] == "Pavel"
    if scene_id == "ending_airborne_guided":
        return state["flight.result"] == "aloft" and state["flight.mode"] == "Nia"
    if scene_id == "ending_grounded":
        return state["flight.result"] == "grounded"
    return False


def _act(play, name, requires, changes):
    play.act(name, requires, **changes)


def play_scene(params, state, scene_id):
    if not isinstance(params, Parameters):
        raise TypeError("params must be a Parameters instance")
    validate(state)
    if not guard(scene_id, state):
        raise StoryError(f"Scene not compatible with current state: {scene_id}")
    before = deepcopy(state)
    x = LocalPlay(state, actors=("nia", "pavel"), validate=validate)

    if scene_id == "workshop":
        _act(x, "borrow_the_string_reel",
             {"story.stage": "start", "reel.owner": "Tamsin", "reel.location": "workshop"},
             {"reel.borrowed": True, "reel.location": "Nia", "story.stage": "borrowed"})
    elif scene_id == "build":
        _act(x, "build_the_willow_frame", {"story.stage": "borrowed"},
             {"kite.frame_strength": x.state["workshop.willow_strength"], "kite.ready": True,
              "kite.status": "ready", "story.stage": "prepared"})
    elif scene_id == "invite":
        comfort = 1 if params.shyness == 3 else 2
        action = "make_a_quiet_invitation" if params.shyness == 3 else "offer_a_small_first_job"
        _act(x, action, {"story.stage": "prepared", "pavel.location": "home"},
             {"pavel.invited": True, "pavel.location": "field", "nia.location": "field",
              "kite.location": "field", "pavel.comfort": comfort, "story.stage": "invited"})
    elif scene_id == "ribbon":
        _act(x, "tie_a_ribbon_to_the_tail", {"story.stage": "invited", "kite.ribbon": False},
             {"kite.ribbon": True})
    elif scene_id == "practice":
        _act(x, "practice_a_gentle_release", {"story.stage": "invited", "practice.done": False},
             {"practice.done": True, "nia.skill": 1,
              "pavel.comfort": min(3, x.state["pavel.comfort"] + 1)})
    elif scene_id == "hand_reel":
        _act(x, "let_pavel_hold_the_reel", {"story.stage": "invited", "pavel.comfort": 2,
                                                "reel.location": "Nia"},
             {"flight.mode": "Pavel", "pavel.task": "hold the reel", "reel.location": "Pavel",
              "story.stage": "chosen"})
    elif scene_id == "keep_reel":
        _act(x, "nia_keeps_the_reel_and_pavel_guides", {"story.stage": "invited", "reel.location": "Nia"},
             {"flight.mode": "Nia", "pavel.task": "guide the kite's tail", "story.stage": "chosen"})
    elif scene_id == "launch":
        frame_margin = x.state["kite.frame_strength"] + int(x.state["kite.ribbon"]) + x.state["nia.skill"]
        line_margin = 3 - x.state["reel.wear"] + int(x.state["practice.done"])
        success = frame_margin >= x.state["weather.wind"] + 1 and line_margin >= x.state["weather.wind"]
        result = "aloft" if success else "grounded"
        _act(x, "launch_and_pay_out_the_line", {"story.stage": "chosen", "kite.ready": True},
             {"flight.result": result, "kite.status": result,
              "kite.location": "air" if success else "field", "reel.string_left": 65 if success else 85,
              "reel.usefulness": "held a flying line" if success else "held a safe test line",
              "story.stage": "flown"})
    else:
        outcome = {"ending_airborne_shared": "shared_flight",
                   "ending_airborne_guided": "guided_flight",
                   "ending_grounded": "safe_landing"}[scene_id]
        holder = x.state["flight.mode"]
        _act(x, "bring_the_kite_and_children_back", {"story.stage": "flown"},
             {"nia.location": "workshop", "pavel.location": "workshop",
              "kite.location": "workshop", "kite.status": "recovered", "story.stage": "returning"})
        _act(x, "gather_the_spool", {"reel.location": holder}, {"reel.location": "Nia"})
        _act(x, "return_the_useful_borrowed_reel",
             {"reel.owner": "Tamsin", "reel.location": "Nia", "reel.borrowed": True},
             {"reel.location": "workshop", "reel.returned": True,
              "reel.usefulness": "ready for another flight"})
        _act(x, "finish_the_afternoon", {"story.stage": "returning", "reel.returned": True},
             {"story.stage": "ended", "story.ended": True, "story.outcome": outcome})

    after = deepcopy(x.state)
    text = render(scene_id, params, before, after)
    return Episode(scene_id, before, after, tuple(deepcopy(x.events)), text)


def _episode_dict(episode):
    return {"id": episode.id, "before": deepcopy(episode.before), "after": deepcopy(episode.after),
            "events": deepcopy(list(episode.events)), "text": episode.text}


def generate(seed=0, *, count=8, params=None):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(count) is not int or count not in (7, 8):
        raise ValueError("count must be exactly 7 or 8")
    p = parameters(seed) if params is None else params
    if not isinstance(p, Parameters):
        raise TypeError("params must be a Parameters instance")
    rng = random.Random(seed)
    attempts = 0
    budget = 5000

    def search(state, path, used):
        nonlocal attempts
        if len(path) == count:
            return path if state["story.ended"] else None
        if state["story.ended"]:
            return None
        remaining = count - len(path)
        candidates = [sid for sid in SCENES if sid not in used and guard(sid, state)]
        if remaining == 1:
            candidates = [sid for sid in candidates if sid.startswith("ending_")]
        else:
            candidates = [sid for sid in candidates if not sid.startswith("ending_")]
        rng.shuffle(candidates)
        for sid in candidates:
            attempts += 1
            if attempts > budget:
                raise StoryError(f"Scene search budget exhausted ({budget} attempts)")
            episode = play_scene(p, state, sid)
            answer = search(episode.after, path + (episode,), used | {sid})
            if answer is not None:
                return answer
        return None

    episodes = search(initial(p), (), frozenset())
    if episodes is None:
        raise StoryError("No complete route at the requested length")
    rows = [_episode_dict(ep) for ep in episodes]
    return {
        "seed": seed, "parameters": asdict(p), "scene_count": count,
        "path": [ep.id for ep in episodes],
        "story": "\n\n".join(ep.text for ep in episodes),
        "episodes": rows, "final_state": deepcopy(episodes[-1].after),
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
            raise StoryError("A scene cannot be repeated")
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode.after
        used.add(scene_id)
    return tuple(episodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--scenes", type=int, choices=(7, 8), default=8)
    args = parser.parse_args()
    row = generate(args.seed, count=args.scenes)
    print(row["story"])


if __name__ == "__main__":
    main()
