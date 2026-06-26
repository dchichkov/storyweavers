#!/usr/bin/env python3
"""
A small story world about a coed group making drastic sound effects for a show,
working through conflict, and ending with a heartwarming shared performance.

Premise:
- A mixed-gender group of children wants to make a tiny stage show feel big.
- They love dramatic sound effects: stomps, claps, thunder sheets, squeaky doors.
- One child wants louder-and-louder effects; another worries it will drown out
  the speaking parts.

Turn:
- A conflict rises when a drastic choice makes the room too noisy.
- The group pauses, listens, and notices what each sound is for.

Resolution:
- They split the sounds by role, soften the biggest effects, and help each
  other perform.
- The ending is warm: everyone gets a turn, and the final show feels magical
  without hurting anyone's ears.

This script follows the Storyweavers world contract:
- one self-contained stdlib script
- eager import of storyworlds.results
- lazy import of storyworlds.asp in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- inline ASP_RULES twin, asp_facts(), and --verify parity
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    group: object | None = None
    helper: object | None = None
    leader: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "group":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str = "the school auditorium"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Activity:
    id: str
    name: str
    loudness: str
    trigger: str
    turn: str
    keyword: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    risk: str
    owner_kind: set[str] = field(default_factory=set)
    answer: str = ""
    question: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class SoundGear:
    id: str
    label: str
    helps: set[str]
    prep: str
    finish: str
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def safe_name(name: str) -> str:
    return "".join(c for c in name.lower() if c.isalnum() or c == "_") or "x"


def build_world(setting: Setting) -> World:
    return World(setting)


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    lead = world.facts.get("leader")
    if not lead:
        return out
    leader = world.get(lead)
    act = _safe_fact(world, world.facts, "activity")
    if leader.meters.get("noise", 0.0) < THRESHOLD:
        return out
    if (("noise",) in world.fired):
        return out
    world.fired.add(("noise",))
    leader.memes["pressure"] = leader.memes.get("pressure", 0.0) + 1
    out.append(f"The sound bounced around too hard and everyone had to pause.")
    return out


def _r_conflict(world: World) -> list[str]:
    leader = world.facts.get("leader")
    if not leader:
        return []
    kid = world.get(leader)
    if kid.memes.get("pressure", 0.0) < THRESHOLD:
        return []
    if ("conflict", kid.id) in world.fired:
        return []
    world.fired.add(("conflict", kid.id))
    kid.memes["conflict"] = kid.memes.get("conflict", 0.0) + 1
    return ["__conflict__"]


CAUSAL_RULES = [
    _r_noise,
    _r_conflict,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule(world)
            if items:
                changed = True
                produced.extend(x for x in items if x != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_noise(world: World, actor: Entity, activity: Activity) -> bool:
    sim = World(world.setting)
    sim.entities = {
        eid: Entity(
            id=e.id,
            kind=e.kind,
            type=e.type,
            label=e.label,
            phrase=e.phrase,
            owner=e.owner,
            caretaker=e.caretaker,
            worn_by=e.worn_by,
            plural=e.plural,
            meters=dict(e.meters),
            memes=dict(e.memes),
            traits=list(e.traits),
        )
        for eid, e in world.entities.items()
    }
    sim.facts = dict(world.facts)
    sim.get(actor.id).meters["noise"] = sim.get(actor.id).meters.get("noise", 0.0) + 1
    propagate(sim, narrate=False)
    return bool(sim.get(actor.id).memes.get("conflict", 0.0) >= THRESHOLD)


def intro(world: World, group: Entity) -> None:
    world.say(
        f"{group.id} was a small coed group of kids who loved making big moments out of tiny things."
    )


def love_sound(world: World, leader: Entity, activity: Activity) -> None:
    world.say(
        f"{leader.id} loved {activity.name}; {activity.loudness} made the room feel full of adventure."
    )


def gather(world: World, group: Entity, setting: Setting) -> None:
    world.say(
        f"One afternoon, the kids gathered in {setting.place} with paper props, bright eyes, and careful hands."
    )


def want(world: World, leader: Entity, activity: Activity) -> None:
    leader.memes["desire"] = leader.memes.get("desire", 0.0) + 1
    world.say(
        f"{leader.id} wanted to make the {activity.keyword} part drastic, so it would sound exciting enough to sparkle."
    )


def warn(world: World, parent: Entity, leader: Entity, item: Item, activity: Activity) -> bool:
    if not predict_noise(world, leader, activity):
        return False
    world.facts["warned"] = True
    world.say(
        f'"If it gets any louder, it will cover the voices," {parent.id} said gently. '
        f'"Then {item.label} may not be heard at all."'
    )
    return True


def conflict(world: World, leader: Entity, activity: Activity) -> None:
    leader.memes["stubborn"] = leader.memes.get("stubborn", 0.0) + 1
    world.say(
        f"{leader.id} frowned. {leader.pronoun().capitalize()} wanted the drastic version and tried to slam the props together."
    )
    leader.meters["noise"] = leader.meters.get("noise", 0.0) + 1
    propagate(world, narrate=False)
    if leader.memes.get("conflict", 0.0) >= THRESHOLD:
        world.say(
            f"That made the room feel too sharp and noisy, and the happy chatter turned into a real conflict."
        )


def pause_and_listen(world: World, group: Entity, activity: Activity) -> None:
    world.say(
        f"Then the kids paused. They listened to the stage, the chairs, and the little echo of the last sound."
    )
    world.say(
        f"They noticed the {activity.keyword} effects were supposed to support the story, not swallow it."
    )


def compromise(world: World, leader: Entity, helper: Entity, activity: Activity, item: Item, gear: SoundGear) -> bool:
    if activity.id not in gear.helps:
        return False
    world.say(
        f'{helper.id} smiled and offered a kinder idea: "{gear.prep} so the big sounds can stay fun but soft enough to hear."'
    )
    world.say(
        f"{leader.id} looked at the others, nodded, and helped {helper.id} with the quieter beats."
    )
    leader.memes["conflict"] = 0.0
    leader.memes["joy"] = leader.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.say(
        f"They used {gear.label}, shared the cues, and kept {item.label} clear. {gear.finish.capitalize()}, the show flowed like a warm song."
    )
    return True


def ending(world: World, group: Entity, activity: Activity, item: Item) -> None:
    world.say(
        f"In the end, everyone had a turn: some kids made whispery footsteps, some kids shook the thunder sheet, and {group.id} finished {activity.name} with smiles."
    )
    world.say(
        f"The audience heard every part of {item.label}, and the room felt cozy and kind as the last applause faded."
    )


SETTINGS = {
    "auditorium": Setting(place="the school auditorium", indoors=True, affords={"stage_fx", "door_fx", "thunder_fx"}),
    "classroom": Setting(place="the classroom stage", indoors=True, affords={"stage_fx", "door_fx"}),
    "gym": Setting(place="the gym hall", indoors=True, affords={"stage_fx", "thunder_fx"}),
}

ACTIVITIES = {
    "stage_fx": Activity(
        id="stage_fx",
        name="stage sound effects",
        loudness="little taps and pops",
        trigger="make the footsteps and claps",
        turn="the effects",
        keyword="sound effects",
        tags={"sound effects", "conflict"},
    ),
    "door_fx": Activity(
        id="door_fx",
        name="door sound effects",
        loudness="creaks and squeaks",
        trigger="add the door squeak",
        turn="the door cue",
        keyword="squeaky door",
        tags={"sound effects", "conflict"},
    ),
    "thunder_fx": Activity(
        id="thunder_fx",
        name="thunder sound effects",
        loudness="a deep rumble and a shake",
        trigger="roll the thunder sheet",
        turn="the thunder cue",
        keyword="thunder",
        tags={"sound effects", "conflict"},
    ),
}

ITEMS = {
    "script": Item(id="script", label="the script", phrase="the little play script", risk="needs clear voices", owner_kind={"group"}),
    "song": Item(id="song", label="the song", phrase="the cheerful song", risk="needs clear voices", owner_kind={"group"}),
}

GEAR = [
    SoundGear(
        id="soft_hands",
        label="soft hands",
        helps={"stage_fx", "door_fx", "thunder_fx"},
        prep="keep the claps soft and the steps light",
        finish="with softer hands and better timing",
    ),
    SoundGear(
        id="cue_cards",
        label="cue cards",
        helps={"stage_fx", "door_fx"},
        prep="hold up cue cards so everyone knows when to start",
        finish="with clear cue cards and calm voices",
    ),
    SoundGear(
        id="blanket",
        label="a folded blanket",
        helps={"thunder_fx"},
        prep="put a folded blanket under the thunder sheet to soften the rumble",
        finish="with the thunder gentled and the voices safe",
    ),
]

KIDS = [
    ("Maya", "girl", "bright"),
    ("Noah", "boy", "careful"),
    ("Zuri", "girl", "curious"),
    ("Eli", "boy", "cheerful"),
    ("Sofia", "girl", "playful"),
    ("Owen", "boy", "gentle"),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
    leader: str
    helper: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for item in ITEMS:
                combos.append((place, act, item))
    return combos


def reason_invalid(activity: Activity, item: Item) -> str:
    return f"(No story: {activity.name} and {item.label} do not fit the same small stage problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming coed sound-effects conflict story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--leader")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, item = rng.choice(list(combos))
    leader = getattr(args, "leader", None) or rng.choice([n for n, _, _ in KIDS])
    helper_choices = [n for n, _, _ in KIDS if n != leader]
    helper = getattr(args, "helper", None) or rng.choice(helper_choices)
    return StoryParams(place=place, activity=activity, item=item, leader=leader, helper=helper)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    item = _safe_lookup(ITEMS, params.item)
    world = build_world(setting)
    group = world.add(Entity(id="group", kind="group", type="group", label="the kids", plural=True))
    leader = world.add(Entity(id=params.leader, kind="character", type="child", traits=["leader"]))
    helper = world.add(Entity(id=params.helper, kind="character", type="child", traits=["helper"]))
    parent = world.add(Entity(id="MsRivera", kind="character", type="adult", label="Ms. Rivera"))
    world.facts.update(group=group, leader=leader.id, helper=helper.id, parent=parent.id, activity=activity, item=item, setting=setting)

    intro(world, group)
    love_sound(world, leader, activity)
    gather(world, group, setting)
    want(world, leader, activity)

    world.para()
    warn(world, parent, leader, item, activity)
    conflict(world, leader, activity)
    pause_and_listen(world, group, activity)

    world.para()
    chosen = None
    for gear in GEAR:
        if compromise(world, leader, helper, activity, item, gear):
            chosen = gear
            break
    ending(world, group, activity, item)

    world.facts["gear"] = chosen
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a heartwarming short story for a child about a coed group making sound effects for a tiny stage show.',
        f"Tell a story where {_safe_fact(world, f, "leader")} wants drastic sound effects, but {_safe_fact(world, f, "parent")} worries the voices will be covered.",
        f'Write a simple story about "{_safe_fact(world, f, "activity").keyword}" sound effects, conflict, and a kind compromise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    leader: Entity = _safe_fact(world, f, "leader")
    helper: Entity = _safe_fact(world, f, "helper")
    activity: Activity = _safe_fact(world, f, "activity")
    item: Item = _safe_fact(world, f, "item")
    gear: Optional[SoundGear] = f.get("gear")
    q = [
        QAItem(
            question=f"What was {leader.id} trying to do with the sound effects?",
            answer=f"{leader.id} wanted to make {activity.name} drastic so the little show would feel exciting.",
        ),
        QAItem(
            question=f"Why did Ms. Rivera worry about the louder plan?",
            answer=f"She worried the louder sounds would cover the voices and make {item.label} hard to hear.",
        ),
        QAItem(
            question=f"Who helped find a gentler way to do the sounds?",
            answer=f"{helper.id} helped by suggesting a quieter plan and working with {leader.id}.",
        ),
    ]
    if gear:
        q.append(
            QAItem(
                question=f"What did they use to keep the big sound from getting too loud?",
                answer=f"They used {gear.label} and followed its quiet, careful plan.",
            )
        )
    return q


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What are sound effects?", answer="Sound effects are little noises that help tell a story, like footsteps, a door creak, or a rumble of thunder."),
        QAItem(question="What does conflict mean in a story?", answer="Conflict is when characters want different things or have trouble agreeing, and they need to work it out."),
        QAItem(question="Why can softer sounds help in a play?", answer="Softer sounds can help because the actors' voices stay clear and the audience can still hear the story."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place, Activity, Item) :- place(Place), activity(Activity), item(Item), affords(Place, Activity).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="auditorium", activity="stage_fx", item="script", leader="Maya", helper="Noah"),
    StoryParams(place="classroom", activity="door_fx", item="song", leader="Zuri", helper="Eli"),
    StoryParams(place="gym", activity="thunder_fx", item="script", leader="Sofia", helper="Owen"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_stories())} valid stories")
        for t in asp_valid_stories():
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
