"""Offline, bounded mini-adventure set in a school puppet theatre."""
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
    needle: str = "sharp"
    thread: str = "long"
    button_strength: str = "sound"
    curtain_weight: str = "heavy"
    minutes: int = 8
    spare_button: bool = True

    def __post_init__(self):
        choices = {
            "needle": ("sharp", "blunt"),
            "thread": ("long", "short"),
            "button_strength": ("sound", "cracked"),
            "curtain_weight": ("light", "heavy"),
        }
        for name, allowed in choices.items():
            value = getattr(self, name)
            if type(value) is not str or value not in allowed:
                raise ValueError(f"{name} must be one of {allowed}")
        if type(self.minutes) is not int or not 4 <= self.minutes <= 8:
            raise ValueError("minutes must be an integer from 4 through 8")
        if type(self.spare_button) is not bool:
            raise ValueError("spare_button must be boolean")


SCENES = (
    "borrow_kit", "find_moon", "button_vignette", "whisper_vignette",
    "repair_moon", "test_moon", "set_stage", "ending_rod", "ending_shadow",
)

STATE_KEYS = (
    "story.ended", "story.outcome", "leni.goal", "jo.goal",
    "leni.location", "jo.location", "ivo.location",
    "kit.owner", "kit.location", "kit.borrowed", "kit.returned", "kit.checked",
    "kit.used", "kit.used_for", "kit.needle", "kit.spare_button", "thread.length",
    "prop.location", "prop.found", "prop.inspected", "prop.repair", "prop.fastener",
    "prop.button_strength", "prop.tested", "prop.holds", "prop.attached", "prop.thread_snapped",
    "button.location", "button.checked", "curtain.weight", "curtain.position", "curtain.held",
    "rehearsal.minutes", "ivo.heard", "ivo.confidence", "ivo.at_controls", "ivo.performed",
    "jo.listened", "screen.ready", "stage.mode", "stage.performance",
)


def parameters(seed):
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    rng = random.Random(seed)
    return Parameters(
        needle=rng.choice(("sharp", "blunt")),
        thread=rng.choice(("long", "short")),
        button_strength=rng.choice(("sound", "cracked")),
        curtain_weight=rng.choice(("light", "heavy")),
        minutes=rng.choice((4, 8)),
        spare_button=rng.choice((True, False)),
    )


def initial(params):
    if not isinstance(params, Parameters):
        raise TypeError("params must be a Parameters instance")
    state = {
        "story.ended": False, "story.outcome": "",
        "leni.goal": "save the moon cue on time", "jo.goal": "let Ivo choose his place",
        "leni.location": "stage", "jo.location": "stage", "ivo.location": "stage",
        "kit.owner": "teacher", "kit.location": "costume_room", "kit.borrowed": False,
        "kit.returned": False, "kit.checked": False, "kit.used": False, "kit.used_for": "",
        "kit.needle": params.needle, "kit.spare_button": params.spare_button,
        "thread.length": params.thread,
        "prop.location": "curtain", "prop.found": False, "prop.inspected": False,
        "prop.repair": "untried", "prop.fastener": "old",
        "prop.button_strength": params.button_strength, "prop.tested": False,
        "prop.holds": False, "prop.attached": False, "prop.thread_snapped": False,
        "button.location": "kit" if params.spare_button else "absent", "button.checked": False,
        "curtain.weight": params.curtain_weight, "curtain.position": "closed", "curtain.held": False,
        "rehearsal.minutes": params.minutes,
        "ivo.heard": False, "ivo.confidence": False, "ivo.at_controls": False, "ivo.performed": False,
        "jo.listened": False, "screen.ready": False, "stage.mode": "none", "stage.performance": "none",
    }
    validate(state)
    return state


def validate(state):
    if not isinstance(state, dict) or set(state) != set(STATE_KEYS):
        raise StoryError("State must contain exactly the declared world keys")
    for key, value in state.items():
        if type(value) not in (str, bool, int):
            raise StoryError(f"State value must be a JSON scalar: {key}")
    bool_keys = (
        "story.ended", "kit.borrowed", "kit.returned", "kit.checked", "kit.used",
        "kit.spare_button", "prop.found", "prop.inspected", "prop.tested", "prop.holds",
        "prop.attached", "prop.thread_snapped", "button.checked", "curtain.held",
        "ivo.heard", "ivo.confidence", "ivo.at_controls", "ivo.performed", "jo.listened", "screen.ready",
    )
    if any(type(state[key]) is not bool for key in bool_keys):
        raise StoryError("Boolean state has the wrong type")
    enums = {
        "kit.owner": ("teacher", "friends"),
        "kit.location": ("costume_room", "friends"),
        "kit.needle": ("sharp", "blunt"), "thread.length": ("long", "short"),
        "kit.used_for": ("", "moon_stitch", "temporary_stitch", "shadow_scrap"),
        "prop.location": ("curtain", "friends", "rod", "table", "ivo_hand"),
        "prop.repair": ("untried", "secure", "temporary", "none"),
        "prop.fastener": ("old", "sound_button", "spare_button", "cloth_loop", "temporary_thread", "none"),
        "prop.button_strength": ("sound", "cracked"),
        "button.location": ("kit", "absent", "friends", "sewn"),
        "curtain.weight": ("light", "heavy"),
        "curtain.position": ("closed", "open", "gathered", "half"),
        "stage.mode": ("none", "puppet", "shadow"),
        "stage.performance": ("none", "moon_cue", "shadow_story"),
        "story.outcome": ("", "rehearsal_saved_with_puppet", "rehearsal_saved_as_shadow_story"),
        "leni.location": ("stage",), "jo.location": ("stage",), "ivo.location": ("stage",),
        "leni.goal": ("save the moon cue on time",), "jo.goal": ("let Ivo choose his place",),
    }
    for key, allowed in enums.items():
        if type(state[key]) is not str or state[key] not in allowed:
            raise StoryError(f"Invalid value for {key}")
    if type(state["rehearsal.minutes"]) is not int or not 4 <= state["rehearsal.minutes"] <= 8:
        raise StoryError("Invalid rehearsal time")

    if state["kit.owner"] == "friends":
        if state["kit.location"] != "friends" or not state["kit.borrowed"] or state["kit.returned"]:
            raise StoryError("Borrowed kit ownership and location disagree")
    else:
        if state["kit.location"] != "costume_room" or state["kit.returned"] != state["kit.borrowed"]:
            raise StoryError("Returned kit ownership and location disagree")
    if state["kit.used"] != bool(state["kit.used_for"]):
        raise StoryError("Kit use must have a recorded purpose")
    if state["kit.used"] and not state["kit.borrowed"]:
        raise StoryError("The friends cannot use an unborrowed kit")
    if state["kit.spare_button"] is False and state["button.location"] != "absent":
        raise StoryError("A nonexistent spare button cannot change location")
    if state["button.location"] in ("friends", "sewn") and not state["button.checked"]:
        raise StoryError("The spare button must be found before use")
    if state["button.location"] == "sewn" and state["prop.fastener"] != "spare_button":
        raise StoryError("A sewn spare button must be the recorded fastener")
    if state["prop.fastener"] == "spare_button" and state["button.location"] != "sewn":
        raise StoryError("The spare button cannot be used twice or disappear")

    if state["curtain.held"] and not (state["curtain.weight"] == "heavy" and state["curtain.position"] == "gathered"):
        raise StoryError("Only a gathered heavy curtain needs holding")
    if state["prop.found"] == (state["prop.location"] == "curtain"):
        raise StoryError("The moon's location disagrees with whether it was found")
    if state["prop.attached"] != (state["prop.location"] == "rod"):
        raise StoryError("Attachment and prop location disagree")
    if state["prop.repair"] == "untried":
        if state["prop.inspected"] or state["kit.used"] or state["prop.fastener"] != "old":
            raise StoryError("Untried repair contains effects from a repair attempt")
    else:
        if not state["prop.inspected"] or not state["kit.used"]:
            raise StoryError("A repair outcome requires an enacted kit use")
    expected_fastener = {"secure": ("sound_button", "spare_button", "cloth_loop"),
                         "temporary": ("temporary_thread",), "none": ("none",)}
    if state["prop.repair"] in expected_fastener and state["prop.fastener"] not in expected_fastener[state["prop.repair"]]:
        raise StoryError("Repair quality and fastener disagree")
    if state["prop.tested"]:
        if state["prop.repair"] == "untried":
            raise StoryError("An untried repair cannot be tested")
    elif state["prop.holds"] or state["prop.thread_snapped"]:
        raise StoryError("A test result cannot precede the test")
    if state["prop.holds"] and not (state["prop.tested"] and state["prop.repair"] == "secure"):
        raise StoryError("Only a tested secure repair can hold")
    if state["prop.thread_snapped"] and not (state["prop.tested"] and state["prop.repair"] == "temporary" and not state["prop.holds"]):
        raise StoryError("Only a failed temporary tie can snap")
    if state["prop.tested"] and not state["prop.holds"] and state["stage.mode"] == "none" and state["prop.location"] != "table":
        raise StoryError("A failed test leaves the loose moon on the table")

    if state["ivo.confidence"] and not state["ivo.heard"]:
        raise StoryError("Ivo's confidence requires someone to hear him")
    if state["jo.listened"] and not state["ivo.heard"]:
        raise StoryError("Listening cannot precede Ivo's whisper")
    if state["stage.mode"] == "none":
        if state["ivo.at_controls"] or state["stage.performance"] != "none":
            raise StoryError("Stage actions require an arranged mode")
    elif state["stage.mode"] == "puppet":
        if not (state["prop.holds"] and state["ivo.confidence"] and state["prop.location"] == "rod"
                and state["curtain.position"] == "open" and state["ivo.at_controls"]):
            raise StoryError("Rod performance requires a tested prop and Ivo's choice")
    else:
        if not (state["prop.location"] == "ivo_hand" and state["curtain.position"] == "half"
                and state["screen.ready"] and state["ivo.at_controls"]):
            raise StoryError("Shadow mode needs a hand-held moon and half-screen")
    if state["ivo.performed"] != (state["stage.performance"] != "none"):
        raise StoryError("Performance state is inconsistent")

    if state["story.ended"]:
        if not (state["story.outcome"] and state["kit.returned"] and state["ivo.performed"]):
            raise StoryError("The story cannot end before performance and kit return")
        expected = "rehearsal_saved_with_puppet" if state["stage.performance"] == "moon_cue" else "rehearsal_saved_as_shadow_story"
        if state["story.outcome"] != expected:
            raise StoryError("Outcome does not match the completed performance")
    elif state["story.outcome"]:
        raise StoryError("An unfinished story cannot have a final outcome")
    return None


def _check_parameters(params, state):
    if not isinstance(params, Parameters):
        raise TypeError("params must be a Parameters instance")
    pairs = (("kit.needle", params.needle), ("thread.length", params.thread),
             ("prop.button_strength", params.button_strength), ("curtain.weight", params.curtain_weight),
             ("rehearsal.minutes", params.minutes), ("kit.spare_button", params.spare_button))
    if any(state[key] != value for key, value in pairs):
        raise StoryError("Parameters do not match the supplied world state")


def guard(scene_id, state):
    if scene_id not in SCENES:
        raise StoryError(f"Unknown scene: {scene_id}")
    validate(state)
    if state["story.ended"]:
        return False
    if scene_id == "borrow_kit":
        return not state["kit.borrowed"] and state["kit.owner"] == "teacher"
    if scene_id == "find_moon":
        return state["kit.owner"] == "friends" and not state["prop.found"]
    if scene_id == "button_vignette":
        return state["prop.found"] and not state["button.checked"] and state["prop.repair"] == "untried"
    if scene_id == "whisper_vignette":
        return state["prop.found"] and not state["ivo.heard"] and state["prop.repair"] == "untried"
    if scene_id == "repair_moon":
        return state["prop.found"] and state["kit.owner"] == "friends" and state["prop.repair"] == "untried"
    if scene_id == "test_moon":
        return state["prop.repair"] != "untried" and not state["prop.tested"]
    if scene_id == "set_stage":
        return state["prop.tested"] and state["stage.mode"] == "none"
    if scene_id == "ending_rod":
        return state["stage.mode"] == "puppet" and not state["story.ended"]
    if scene_id == "ending_shadow":
        return state["stage.mode"] == "shadow" and not state["story.ended"]
    return False


def _act(play, name, requires, changes):
    play.act(name, requires=requires, **changes)


@dataclass(frozen=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


def play_scene(params, state, scene_id):
    validate(state)
    _check_parameters(params, state)
    if not guard(scene_id, state):
        raise StoryError(f"Scene not compatible with current state: {scene_id}")
    play = LocalPlay(state, actors=("leni", "jo", "ivo"), validate=validate)

    if scene_id == "borrow_kit":
        _act(play, "borrow_sewing_kit",
             {"kit.owner": "teacher", "kit.location": "costume_room", "kit.borrowed": False},
             {"kit.owner": "friends", "kit.location": "friends", "kit.borrowed": True})

    elif scene_id == "find_moon":
        if params.curtain_weight == "heavy":
            _act(play, "gather_heavy_curtain", {"curtain.position": "closed", "curtain.weight": "heavy"},
                 {"curtain.position": "gathered", "curtain.held": True})
            _act(play, "free_moon_from_fold", {"curtain.held": True, "prop.found": False},
                 {"curtain.held": False, "prop.found": True, "prop.location": "friends"})
        else:
            _act(play, "part_light_curtain", {"curtain.position": "closed", "curtain.weight": "light"},
                 {"curtain.position": "open"})
            _act(play, "lift_moon_from_stage", {"curtain.position": "open", "prop.found": False},
                 {"prop.found": True, "prop.location": "friends"})

    elif scene_id == "button_vignette":
        if params.spare_button:
            _act(play, "find_spare_button", {"kit.owner": "friends", "button.location": "kit", "button.checked": False},
                 {"button.location": "friends", "button.checked": True, "kit.checked": True})
        else:
            _act(play, "check_empty_kit_lining", {"kit.owner": "friends", "button.location": "absent", "button.checked": False},
                 {"button.checked": True, "kit.checked": True})

    elif scene_id == "whisper_vignette":
        _act(play, "listen_to_ivo", {"ivo.heard": False, "prop.found": True},
             {"ivo.heard": True, "jo.listened": True})
        _act(play, "invite_ivo_to_choose", {"ivo.heard": True, "jo.listened": True},
             {"ivo.confidence": True})

    elif scene_id == "repair_moon":
        _act(play, "inspect_torn_loop", {"prop.found": True, "prop.inspected": False, "kit.owner": "friends"},
             {"prop.inspected": True, "kit.checked": True})
        has_anchor = (params.button_strength == "sound" or play.state["button.location"] == "friends"
                      or params.minutes >= 8)
        secure = params.needle == "sharp" and params.thread == "long" and has_anchor
        temporary = not secure and has_anchor and (params.thread == "long" or params.needle == "sharp")
        spare_used = secure and play.state["button.location"] == "friends" and params.button_strength == "cracked"
        if secure:
            if spare_used:
                fastener, purpose = "spare_button", "moon_stitch"
            elif params.button_strength == "sound":
                fastener, purpose = "sound_button", "moon_stitch"
            else:
                fastener, purpose = "cloth_loop", "moon_stitch"
            changes = {"prop.repair": "secure", "prop.fastener": fastener, "prop.location": "rod",
                       "prop.attached": True, "kit.used": True, "kit.used_for": purpose}
            if spare_used:
                changes["button.location"] = "sewn"
            _act(play, "sew_secure_loop", {"prop.inspected": True, "kit.owner": "friends"}, changes)
        elif temporary:
            _act(play, "tie_temporary_loop", {"prop.inspected": True, "kit.owner": "friends"},
                 {"prop.repair": "temporary", "prop.fastener": "temporary_thread", "prop.location": "rod",
                  "prop.attached": True, "kit.used": True, "kit.used_for": "temporary_stitch"})
        else:
            _act(play, "cut_shadow_scrap", {"prop.inspected": True, "kit.owner": "friends"},
                 {"prop.repair": "none", "prop.fastener": "none", "kit.used": True,
                  "kit.used_for": "shadow_scrap", "screen.ready": True})

    elif scene_id == "test_moon":
        if play.state["prop.repair"] == "secure":
            _act(play, "test_secure_stitch", {"prop.repair": "secure", "prop.location": "rod", "prop.attached": True},
                 {"prop.tested": True, "prop.holds": True})
        elif play.state["prop.repair"] == "temporary":
            _act(play, "test_temporary_tie", {"prop.repair": "temporary", "prop.location": "rod"},
                 {"prop.tested": True, "prop.holds": False, "prop.location": "table",
                  "prop.attached": False, "prop.thread_snapped": True})
        else:
            _act(play, "test_unattached_moon", {"prop.repair": "none", "prop.location": "friends"},
                 {"prop.tested": True, "prop.holds": False, "prop.location": "table"})

    elif scene_id == "set_stage":
        if play.state["prop.holds"] and play.state["ivo.confidence"]:
            _act(play, "give_ivo_the_rod", {"prop.tested": True, "prop.holds": True, "ivo.confidence": True},
                 {"stage.mode": "puppet", "curtain.position": "open", "ivo.at_controls": True})
        else:
            _act(play, "prepare_half_screen", {"prop.tested": True, "stage.mode": "none"},
                 {"stage.mode": "shadow", "curtain.position": "half", "screen.ready": True,
                  "prop.location": "ivo_hand", "prop.attached": False, "ivo.at_controls": True})

    elif scene_id == "ending_rod":
        _act(play, "perform_moon_cue", {"stage.mode": "puppet", "prop.location": "rod", "ivo.at_controls": True},
             {"ivo.performed": True, "stage.performance": "moon_cue"})
        _act(play, "return_sewing_kit", {"kit.owner": "friends", "kit.used": True},
             {"kit.owner": "teacher", "kit.location": "costume_room", "kit.returned": True})
        _act(play, "finish_rehearsal", {"ivo.performed": True, "kit.returned": True},
             {"story.ended": True, "story.outcome": "rehearsal_saved_with_puppet"})

    elif scene_id == "ending_shadow":
        _act(play, "perform_shadow_story", {"stage.mode": "shadow", "prop.location": "ivo_hand", "ivo.at_controls": True},
             {"ivo.performed": True, "stage.performance": "shadow_story"})
        _act(play, "return_sewing_kit", {"kit.owner": "friends", "kit.used": True},
             {"kit.owner": "teacher", "kit.location": "costume_room", "kit.returned": True})
        _act(play, "finish_rehearsal", {"ivo.performed": True, "kit.returned": True},
             {"story.ended": True, "story.outcome": "rehearsal_saved_as_shadow_story"})

    after = deepcopy(play.state)
    text = render(scene_id, params, state, after)
    return Episode(scene_id, deepcopy(state), after, tuple(deepcopy(play.events)), text)


def _episode_data(episode):
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
    start = initial(p)
    rng = random.Random(seed)
    attempts = 0

    def search(state, path):
        nonlocal attempts
        if len(path) == count:
            return path if state["story.ended"] else None
        used = {episode.id for episode in path}
        choices = [scene_id for scene_id in SCENES
                   if scene_id not in used and guard(scene_id, state)]
        rng.shuffle(choices)
        for scene_id in choices:
            attempts += 1
            if attempts > 10000:
                raise StoryError("Bounded scene search exceeded 10,000 attempts")
            episode = play_scene(p, state, scene_id)
            answer = search(episode.after, path + (episode,))
            if answer is not None:
                return answer
        return None

    chosen = search(start, ())
    if chosen is None:
        raise StoryError("No complete compatible route at the requested length")
    episode_data = [_episode_data(episode) for episode in chosen]
    story = "\n\n".join(episode["text"] for episode in episode_data)
    return {
        "seed": seed,
        "parameters": asdict(p),
        "scene_count": count,
        "path": [episode["id"] for episode in chosen],
        "story": story,
        "episodes": episode_data,
        "final_state": deepcopy(chosen[-1].after),
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
        used.add(scene_id)
        state = episode.after
    return tuple(episodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--scenes", type=int, choices=(7, 8), default=8)
    parser.add_argument("--params", help="Optional JSON object overriding this seed's parameters")
    args = parser.parse_args()
    try:
        overrides = json.loads(args.params) if args.params else {}
        if not isinstance(overrides, dict):
            raise ValueError("--params must be a JSON object")
        p = Parameters(**(asdict(parameters(args.seed)) | overrides))
        row = generate(args.seed, count=args.scenes, params=p)
    except (ValueError, TypeError, StoryError) as exc:
        parser.error(str(exc))
    print(row["story"])


if __name__ == "__main__":
    main()
