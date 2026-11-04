"""A bounded adventure selector with small, stateful scenes. No API calls.

Reuses runtime.transition for each local action. Scene selection searches for
an exact-length complete route; speculative actions never enter the saved story.
The party stays together in this deliberately small scenario.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import random
import re

from .runtime import Condition, Effect, Scene, StoryError, transition
from .smallest_sea_prose import render


@dataclass(frozen=True, kw_only=True)
class Parameters:
    captain: str = "Tom"
    explorer: str = "Lily"
    board_cm: int = 80
    gap_cm: int = 100
    board_sound: bool = True
    daylight: bool = False
    sticky_door: bool = True
    pot_mass: int = 3
    tight_lid: bool = True
    change_coat: bool = True
    grab_whole: bool = True
    map_upside_down: bool = True

    def __post_init__(self):
        for name in (self.captain, self.explorer):
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z'-]{0,23}", name):
                raise ValueError("Names must be short words, without markup")
        if self.captain.casefold() == self.explorer.casefold() or any(
            name.casefold() == "mom" for name in (self.captain, self.explorer)
        ):
            raise ValueError("The three characters need distinct names")
        for name, low, high in (("board_cm", 40, 200), ("gap_cm", 60, 140), ("pot_mass", 1, 4)):
            if type(getattr(self, name)) is not int or not low <= getattr(self, name) <= high:
                raise ValueError(f"{name} must be an integer in [{low}, {high}]")
        for name in ("board_sound", "daylight", "sticky_door", "tight_lid", "change_coat",
                     "grab_whole", "map_upside_down"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be boolean")


def parameters(seed):
    rng = random.Random(seed)
    return Parameters(
        board_cm=rng.choice((80, 140)), gap_cm=rng.choice((90, 110)),
        board_sound=rng.choice((True, True, False)), daylight=rng.choice((False, True)),
        sticky_door=rng.choice((True, False)), pot_mass=rng.choice((1, 3)),
        tight_lid=rng.choice((True, False)), change_coat=rng.choice((True, False)),
        grab_whole=rng.choice((True, False)), map_upside_down=rng.choice((True, False)),
    )


def initial(p):
    return {
        "party.location": "house", "party.route": "", "party.ended": False,
        "captain.goal": "", "captain.coat": "red", "captain.sleeve_wet": False,
        "captain.hands_wet": False, "captain.cooperation": 0, "captain.asked_help": False,
        "captain.clothing_decided": False, "explorer.requested_light": False,
        "red_coat.location": "captain", "green_jacket.location": "hook",
        "captain.role": "captain", "explorer.role": "explorer", "captain.will_ask": False,
        "explorer.afraid": False, "explorer.trust": 0, "explorer.bracing": False,
        "explorer.remembers_ship": False, "explorer.remembers_height": False,
        "party.boots_on": True, "map.owner": "mom", "map.read": False,
        "map.upside_down": p.map_upside_down, "map.mark": "", "flag.location": "behind_boots",
        "hat.owner": "captain", "hat.wet": False, "hat.folded": False,
        "summerhouse.door_open": False, "summerhouse.light_on": False,
        "summerhouse.daylight": p.daylight, "summerhouse.dark": not p.daylight,
        "summerhouse.sticky": p.sticky_door, "summerhouse.close_attempted": False,
        "summerhouse.apology": False, "summerhouse.light_tried": False,
        "board.length": p.board_cm, "puddle.width": p.gap_cm, "board.sound": p.board_sound,
        "board.location": "bank", "board.tested": False, "board.supported": False,
        "pot.mass": p.pot_mass, "captain.strength": 2, "explorer.strength": 2,
        "pot.tested": False, "pot.raised": False, "pot.holders": "",
        "tin.location": "under_pot", "tin.open": False, "tin.tight": p.tight_lid,
        "tin.lid_tried": False, "party.knows_contents": False,
        "biscuits.unallocated": 8, "captain.portion": 0, "explorer.portion": 0,
        "captain.eaten": 0, "explorer.eaten": 0, "captain.claimed_whole": False,
        "explorer.objected": False, "party.agreed_shares": False,
    }


def conditions(**values):
    return tuple(Condition(key=k, op="eq", value=v) for k, v in values.items())


def validate(state):
    if state["party.location"] not in {"house", "garden", "summerhouse", "tree"}:
        raise StoryError("Unknown location")
    if state["summerhouse.dark"] != (not state["summerhouse.daylight"] and not state["summerhouse.light_on"]):
        raise StoryError("Light and darkness disagree")
    worn = {"red": "red_coat.location", "green": "green_jacket.location"}
    if state["captain.coat"] not in {*worn, "none"} or any(
        (state[key] == "captain") != (state["captain.coat"] == color) for color, key in worn.items()
    ):
        raise StoryError("Worn and stored coats disagree")
    portions = [state[k] for k in ("biscuits.unallocated", "captain.portion", "explorer.portion",
                                  "captain.eaten", "explorer.eaten")]
    if any(type(n) is not int or n < 0 for n in portions) or sum(portions) != 8:
        raise StoryError("Biscuit portions must be conserved")
    if state["pot.raised"] != bool(state["pot.holders"]):
        raise StoryError("A raised pot needs someone holding it")
    if state["pot.raised"] and state["party.location"] != "tree":
        raise StoryError("Cannot leave while holding the pot")
    if state["board.supported"] and not (
        state["board.sound"] and state["board.length"] >= state["puddle.width"] + 20
        and state["board.location"] == "puddle" and state["board.tested"]
    ):
        raise StoryError("A bridge needs tested support on both banks")
    if state["tin.open"] and state["tin.location"] == "under_pot":
        raise StoryError("Cannot open an unretrieved tin")
    if state["party.ended"] and not (
        state["party.location"] == "house" and state["tin.location"] == "table"
        and state["captain.eaten"] == state["explorer.eaten"] == 4
        and not state["party.boots_on"] and not state["summerhouse.door_open"]
        and not state["summerhouse.light_on"]
    ):
        raise StoryError("Ending left a required action unfinished")


@dataclass(frozen=True, kw_only=True)
class Episode:
    id: str
    before: dict
    after: dict
    events: tuple[dict, ...]
    text: str


class LocalPlay:
    def __init__(self, state):
        validate(state)
        self.state = deepcopy(state)
        self.events = []

    def act(self, name, *, requires=None, sets=None, increments=None):
        before = self.state
        action = Scene(
            id=name, kernel=name, actors=("captain", "explorer"),
            requires=conditions(**(requires or {})), summary=name,
            effects=tuple(Effect(key=k, value=v) for k, v in (sets or {}).items())
            + tuple(Effect(key=k, value=v, op="inc") for k, v in (increments or {}).items()),
        )
        after = transition(before, action)
        if after is None:
            raise StoryError(f"Illegal or ineffective local action: {name}")
        validate(after)
        self.events.append({
            "action": name, "requires": requires or {},
            "changes": {k: {"before": before[k], "after": v} for k, v in after.items() if before[k] != v},
        })
        self.state = after

    def move(self, destination):
        origin = self.state["party.location"]
        edges = {("house", "garden"), ("garden", "house"), ("garden", "summerhouse"),
                 ("summerhouse", "garden"), ("garden", "tree"), ("tree", "garden")}
        if (origin, destination) not in edges:
            raise StoryError(f"No adjacent route: {origin} -> {destination}")
        req = {"party.location": origin, "pot.raised": False}
        if "summerhouse" in (origin, destination):
            req["summerhouse.door_open"] = True
        if "tree" in (origin, destination):
            route = self.state["party.route"]
            if route not in ("board", "detour"):
                raise StoryError("A crossing must be established before travelling")
            if route == "board":
                req.update({"board.location": "puddle", "board.supported": True})
        self.act(f"walk:{origin}:{destination}", requires=req, sets={"party.location": destination})

    def light(self, on):
        self.act("light_on" if on else "light_off", requires={"party.location": "summerhouse"},
                 sets={"summerhouse.light_on": on,
                       "summerhouse.dark": not on and not self.state["summerhouse.daylight"]})


def guard(scene_id, state):
    if state["party.ended"]:
        return False
    place = state["party.location"]
    if scene_id == "launch":
        return place == "house" and not state["captain.goal"]
    if not state["captain.goal"]:
        return False
    if scene_id in {"old_flag", "read_map", "change_clothes"}:
        done = {"old_flag": "explorer.remembers_ship", "read_map": "map.read",
                "change_clothes": "captain.clothing_decided"}[scene_id]
        return place == "house" and not state["party.route"] and not state[done]
    if scene_id in {"enter_summerhouse", "gutter", "crossing"}:
        return place in {"house", "garden"} and not state["party.route"]
    if scene_id == "lights":
        return place == "summerhouse" and state["summerhouse.light_on"] and not state["summerhouse.light_tried"]
    if scene_id == "height_marks":
        return place == "summerhouse" and not state["summerhouse.dark"] and not state["explorer.remembers_height"]
    if scene_id == "exit_summerhouse":
        return place == "summerhouse"
    if scene_id == "treasure":
        return place == "tree" and state["tin.location"] == "under_pot"
    if scene_id == "share":
        return place == "tree" and state["party.knows_contents"] and state["biscuits.unallocated"] == 8
    if scene_id.startswith("ending_"):
        if (place != "tree" or state["captain.eaten"] != 4 or state["explorer.eaten"] != 4
                or not state["party.agreed_shares"] or state["captain.cooperation"] < 1):
            return False
        if state["summerhouse.apology"]:
            return scene_id == "ending_together"
        return scene_id == ("ending_bridge" if state["party.route"] == "board" else "ending_explorer")
    raise StoryError(f"Unknown scene: {scene_id}")


SCENES = ("launch", "old_flag", "read_map", "change_clothes", "gutter", "enter_summerhouse",
          "lights", "height_marks", "exit_summerhouse", "crossing", "treasure", "share",
          "ending_bridge", "ending_explorer", "ending_together")


def play_scene(p, state, scene_id):
    if scene_id not in SCENES or not guard(scene_id, state):
        raise StoryError(f"Scene not compatible with current state: {scene_id}")
    x = LocalPlay(state)
    if scene_id == "launch":
        x.act("accept_expedition", requires={"map.owner": "mom"},
              sets={"captain.goal": "find_and_share_treasure", "map.owner": "explorer"})
    elif scene_id == "old_flag":
        x.act("remember_last_ship", requires={"flag.location": "behind_boots"},
              sets={"flag.location": "windowsill", "explorer.remembers_ship": True})
    elif scene_id == "read_map":
        x.act("orient_map", requires={"map.owner": "explorer"},
              sets={"map.upside_down": False, "map.read": True}, increments={"captain.cooperation": 1})
    elif scene_id == "change_clothes":
        x.act("decide_clothing", requires={"captain.coat": "red"},
              sets={"captain.coat": "green" if p.change_coat else "red", "captain.clothing_decided": True,
                    "red_coat.location": "hook" if p.change_coat else "captain",
                    "green_jacket.location": "captain" if p.change_coat else "hook"})
    elif scene_id == "gutter":
        if x.state["party.location"] == "house":
            x.move("garden")
        x.act("drip_on_hat", sets={"hat.wet": True})
        x.act("fold_wet_brim", requires={"hat.wet": True}, sets={"hat.folded": True})
    elif scene_id == "enter_summerhouse":
        if x.state["party.location"] == "house":
            x.move("garden")
        x.act("open_summerhouse", requires={"party.location": "garden"},
              sets={"summerhouse.door_open": True})
        x.move("summerhouse")
        x.light(True)
    elif scene_id == "lights":
        x.light(False)
        x.act("notice_light_change", sets={"summerhouse.light_tried": True,
                                          "explorer.afraid": x.state["summerhouse.dark"]})
        if x.state["explorer.afraid"]:
            x.act("ask_for_light", requires={"explorer.afraid": True}, sets={"explorer.requested_light": True})
            x.light(True)
            x.act("apologize_and_reassure", requires={"summerhouse.dark": False},
                  sets={"explorer.afraid": False, "summerhouse.apology": True},
                  increments={"explorer.trust": 1, "captain.cooperation": 1})
        else:
            x.light(True)
    elif scene_id == "height_marks":
        if x.state["summerhouse.dark"]:
            raise StoryError("Cannot read height marks in darkness")
        x.act("remember_small_captain", sets={"explorer.remembers_height": True})
    elif scene_id == "exit_summerhouse":
        if x.state["summerhouse.light_on"]:
            x.light(False)
        x.move("garden")
        x.act("try_latch", sets={"summerhouse.close_attempted": True,
                                 "summerhouse.door_open": x.state["summerhouse.sticky"]})
        if x.state["summerhouse.door_open"]:
            x.act("lift_and_latch", requires={"summerhouse.close_attempted": True},
                  sets={"summerhouse.door_open": False}, increments={"captain.cooperation": 1})
    elif scene_id == "crossing":
        if x.state["party.location"] == "house":
            x.move("garden")
        x.act("lay_board", requires={"board.location": "bank"}, sets={"board.location": "puddle"})
        supported = x.state["board.length"] >= x.state["puddle.width"] + 20 and x.state["board.sound"]
        x.act("test_board", requires={"board.location": "puddle"},
              sets={"board.tested": True, "board.supported": supported,
                    "captain.hands_wet": not supported, "captain.sleeve_wet": not supported})
        if supported:
            x.act("choose_board", requires={"board.tested": True, "board.supported": True},
                  sets={"party.route": "board"}, increments={"captain.cooperation": 1})
        else:
            x.act("retrieve_failed_board", requires={"board.tested": True, "board.supported": False},
                  sets={"board.location": "bank"})
            x.act("choose_long_path", sets={"party.route": "detour"}, increments={"captain.cooperation": 1})
        x.move("tree")
    elif scene_id == "treasure":
        alone = x.state["pot.mass"] <= x.state["captain.strength"]
        x.act("try_lift_pot", sets={"pot.tested": True, "pot.raised": alone,
                                    "pot.holders": "captain" if alone else ""})
        if not alone:
            if x.state["pot.mass"] > x.state["captain.strength"] + x.state["explorer.strength"]:
                raise StoryError("The pot is too heavy even for both children")
            x.act("lift_pot_together", requires={"pot.tested": True, "pot.raised": False},
                  sets={"pot.raised": True, "pot.holders": "both", "captain.asked_help": True},
                  increments={"captain.cooperation": 1})
        # Put the pot beside the tin before either child reaches under it.
        x.act("set_pot_aside", requires={"pot.raised": True},
              sets={"pot.raised": False, "pot.holders": "", "tin.location": "tree_ground"})
        x.act("pick_up_tin", requires={"tin.location": "tree_ground"}, sets={"tin.location": "explorer"})
        x.act("try_lid", requires={"tin.location": "explorer"}, sets={"tin.lid_tried": True})
        if x.state["captain.hands_wet"]:
            x.act("dry_hands", sets={"captain.hands_wet": False})
        if x.state["tin.tight"]:
            x.act("brace_tin", sets={"explorer.bracing": True}, increments={"captain.cooperation": 1})
        req = {"tin.location": "explorer", "captain.hands_wet": False}
        if x.state["tin.tight"]:
            req["explorer.bracing"] = True
        x.act("open_tin", requires=req, sets={"tin.open": True, "party.knows_contents": True,
                                            "explorer.bracing": False})
    elif scene_id == "share":
        if p.grab_whole:
            x.act("claim_whole_biscuit", sets={"captain.claimed_whole": True})
            x.act("object_to_shares", requires={"captain.claimed_whole": True}, sets={"explorer.objected": True})
        x.act("divide_biscuits", requires={"tin.open": True, "biscuits.unallocated": 8},
              sets={"biscuits.unallocated": 0, "captain.portion": 4, "explorer.portion": 4,
                    "party.agreed_shares": True}, increments={"captain.cooperation": 1})
        x.act("eat_together", requires={"captain.portion": 4, "explorer.portion": 4},
              sets={"captain.portion": 0, "explorer.portion": 0, "captain.eaten": 4, "explorer.eaten": 4})
    else:
        x.act("close_tin", requires={"tin.open": True}, sets={"tin.open": False})
        x.move("garden")
        x.move("house")
        x.act("put_tin_on_table", requires={"tin.location": "explorer"}, sets={"tin.location": "table"})
        x.act("take_off_boots", requires={"party.location": "house"}, sets={"party.boots_on": False})
        if x.state["captain.coat"] == "green" and x.state["captain.sleeve_wet"]:
            x.act("hang_wet_jacket", sets={"captain.coat": "none", "green_jacket.location": "hook"})
        if scene_id == "ending_bridge":
            x.act("draw_bridge", sets={"map.mark": "Biscuit Bridge"})
        else:
            x.act("offer_captaincy", sets={"hat.owner": "explorer", "captain.role": "explorer",
                                          "explorer.role": "captain"})
            if scene_id == "ending_explorer":
                x.act("draw_detour", sets={"map.mark": "Biscuit Passage"})
            else:
                x.act("promise_to_ask", requires={"summerhouse.apology": True}, sets={"captain.will_ask": True})
        x.act("finish_expedition", sets={"captain.goal": "satisfied", "party.ended": True})
    after = x.state
    return Episode(id=scene_id, before=deepcopy(state), after=after, events=tuple(x.events),
                   text=render(scene_id, p, state, after))


def minimum_remaining(state):
    if state["party.ended"]:
        return 0
    if not state["captain.goal"]:
        return 5
    if state["party.location"] == "summerhouse":
        played = state["summerhouse.light_tried"] or state["explorer.remembers_height"]
        return 5 + (not played)  # interior play if needed, exit, crossing, retrieval, sharing, ending
    if not state["party.route"]:
        return 4
    if state["tin.location"] == "under_pot":
        return 3
    if state["biscuits.unallocated"]:
        return 2
    return 1


def generate(seed=0, *, count=8, params=None):
    if type(count) is not int or count not in (7, 8):
        raise ValueError("This prototype supports exactly seven or eight scenes")
    p = params if params is not None else parameters(seed)
    rng = random.Random(seed)
    attempts = 0

    def search(state, episodes):
        nonlocal attempts
        remaining = count - len(episodes)
        if remaining < minimum_remaining(state):
            return None
        if not remaining:
            return episodes if state["party.ended"] else None
        used = {e.id for e in episodes}
        choices = [s for s in SCENES if s not in used and guard(s, state)
                   and (not s.startswith("ending_") or remaining == 1)
                   and (s != "exit_summerhouse" or state["summerhouse.light_tried"]
                        or state["explorer.remembers_height"])]
        rng.shuffle(choices)
        for scene_id in choices:
            attempts += 1
            if attempts > 10000:
                raise StoryError("Scene search budget exhausted")
            episode = play_scene(p, state, scene_id)
            result = search(episode.after, episodes + (episode,))
            if result is not None:
                return result
        return None

    episodes = search(initial(p), ())
    if episodes is None:
        raise StoryError("No complete route at the requested length")
    return {
        "schema": "smallest_sea.v1", "seed": seed, "parameters": asdict(p),
        "scene_count": count, "path": [e.id for e in episodes],
        "story": "\n\n".join(e.text for e in episodes),
        "episodes": [asdict(e) | {"events": list(e.events)} for e in episodes],
        "final_state": episodes[-1].after, "search_attempts": attempts,
    }


def replay(params, path):
    state = initial(params)
    episodes = []
    for scene_id in path:
        if scene_id in {e.id for e in episodes}:
            raise StoryError("A scene cannot be repeated in this scenario")
        episode = play_scene(params, state, scene_id)
        episodes.append(episode)
        state = episode.after
    return tuple(episodes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--scenes", type=int, choices=(7, 8), default=8)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--params", type=Path, help="JSON object overriding global parameters")
    parser.add_argument("--out", type=Path, help="New output directory; existing paths are never overwritten")
    args = parser.parse_args()
    if not 1 <= args.count <= 1000:
        parser.error("--count must be between 1 and 1000")
    if args.out and args.out.exists():
        parser.error("--out already exists; choose a new batch directory")
    overrides = json.loads(args.params.read_text()) if args.params else {}
    if not isinstance(overrides, dict):
        parser.error("--params must contain a JSON object")
    rows = [generate(seed, count=args.scenes, params=Parameters(**(asdict(parameters(seed)) | overrides)))
            for seed in range(args.seed, args.seed + args.count)]
    if args.out:
        args.out.mkdir(parents=True, exist_ok=False)
        (args.out / "stories.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        (args.out / "stories.md").write_text("# The Smallest Sea: Generated Stories\n\n" + "\n\n".join(
            f"## Seed {r['seed']}\n\n{r['story']}\n\n---\n\nPath: `{' -> '.join(r['path'])}`"
            for r in rows
        ) + "\n")
        files = (Path(__file__), Path(__file__).with_name("smallest_sea_prose.py"),
                 Path(__file__).with_name("runtime.py"))
        source = args.out / "source"
        source.mkdir()
        hashes = {}
        for path in files:
            data = path.read_bytes()
            (source / path.name).write_bytes(data)
            hashes[path.name] = hashlib.sha256(data).hexdigest()
        (args.out / "manifest.json").write_text(json.dumps({
            "schema": "smallest_sea.v1", "source_sha256": hashes,
            "seeds": [r["seed"] for r in rows], "scenes": args.scenes,
            "parameter_overrides": overrides, "api_calls": 0,
        }, indent=2) + "\n")
        print(f"Saved {len(rows)} stories to {args.out}")
    else:
        for row in rows:
            print(f"Seed {row['seed']} | {' -> '.join(row['path'])}\n\n{row['story']}\n")


if __name__ == "__main__":
    main()
