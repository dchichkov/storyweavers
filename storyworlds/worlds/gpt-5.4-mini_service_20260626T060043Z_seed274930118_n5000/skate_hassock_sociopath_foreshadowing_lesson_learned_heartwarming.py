#!/usr/bin/env python3
"""
storyworlds/worlds/skate_hassock_sociopath_foreshadowing_lesson_learned_heartwarming.py
========================================================================================

A small heartwarming storyworld about a child, a hassock, and a pair of skates.

Seed image:
- A child wants to skate indoors.
- A hassock sits in the way and can cause a tumble.
- A foreshadowing detail hints that the skate path is too tight.
- A caring adult turns the moment into a lesson learned.

The seed words "skate", "hassock", and "sociopath" are included as required
world vocabulary. The story stays child-facing and heartwarming, while the odd
seed word is handled as an in-world book title and a generic world-knowledge
term rather than as a focal point of the tale.

Causal state updates:
- skating increases joy and speed
- skating near a hassock without moving it increases wobble and risk
- a wobble near a hard edge can lead to a bump or scare
- moving the hassock clears the route and allows a gentle, safe finish

Narrative instruments:
- Foreshadowing: a small early clue about the tight path and the hassock's legs
- Lesson Learned: the child realizes that safe play can still be fun
- Heartwarming tone: the adult helps, the child learns, and everyone ends happy
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

    child: object | None = None
    hassock: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
    place: str = "the front room"
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    clue: str
    lesson: str
    keyword: str = ""
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
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
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    hassock = world.get("hassock")
    skates = world.get("skates")
    if child.meters.get("skate", 0.0) < THRESHOLD:
        return out
    if hassock.meters.get("moved", 0.0) >= THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["startle"] = child.memes.get("startle", 0.0) + 1
    hassock.meters["wobble"] = hassock.meters.get("wobble", 0.0) + 1
    skates.meters["scrape"] = skates.meters.get("scrape", 0.0) + 1
    out.append("The hassock wobbled a little when the skates brushed past it.")
    return out


def _r_spill_risk(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    prize = world.get("prize")
    hassock = world.get("hassock")
    if child.meters.get("speed", 0.0) < THRESHOLD:
        return out
    if hassock.meters.get("moved", 0.0) >= THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    if child.memes.get("startle", 0.0) < THRESHOLD:
        return out
    world.fired.add(sig)
    prize.meters["risk"] = prize.meters.get("risk", 0.0) + 1
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1
    out.append(f"{child.pronoun('possessive').capitalize()} {prize.label} was in danger of a bump.")
    return out


CAUSAL_RULES = [_r_wobble, _r_spill_risk]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def try_move_hassock(world: World) -> bool:
    hassock = world.get("hassock")
    if hassock.meters.get("moved", 0.0) >= THRESHOLD:
        return True
    hassock.meters["moved"] = 1.0
    world.say("Their grown-up slid the hassock aside, where it could wait safely by the wall.")
    return True


def introduce(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a cheerful little {child.type} who loved to skate whenever the room was clear.")


def foreshadow(world: World, child: Entity, hassock: Entity) -> None:
    world.say(
        f"Before anyone rolled, {child.id} noticed the hassock's short legs and the narrow path around it. "
        f"It was a small clue that the floor might be tricky."
    )
    world.say(
        f"Near the bookshelf, a bright book called \"The Sociopath of Socks\" sat safely out of reach, "
        f"which made the room feel oddly crowded and full of things to step around."
    )


def begin_skate(world: World, child: Entity, prize: Entity) -> None:
    child.meters["skate"] = child.meters.get("skate", 0.0) + 1
    child.meters["speed"] = child.meters.get("speed", 0.0) + 1
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f"{child.id} tied on {child.pronoun('possessive')} skates and pushed off slowly, smiling at the smooth glide."
    )
    propagate(world, narrate=True)


def warn(world: World, parent: Entity, child: Entity, action: Action, prize: Prize) -> None:
    world.say(
        f'{parent.pronoun().capitalize()} said, "{action.clue}, and {prize.label} can get bumped if the path is too tight."'
    )


def stumble_warning(world: World, child: Entity) -> None:
    if child.memes.get("startle", 0.0) >= THRESHOLD:
        world.say(
            f"{child.id} wobbled, caught {child.pronoun('possessive')} balance, and hugged the air for a second."
        )


def lesson_learned(world: World, child: Entity, parent: Entity, action: Action, prize: Prize) -> None:
    child.memes["lesson"] = child.memes.get("lesson", 0.0) + 1
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f'{child.id} looked at the hassock, then at {parent.pronoun("object")}, and nodded. '
        f'"I get it now," {child.pronoun()} said. "{action.lesson}"'
    )


def finish(world: World, child: Entity, prize: Prize) -> None:
    child.meters["speed"] = 0.0
    world.say(
        f"With the hassock parked beside the wall, {child.id} made one last gentle circle. "
        f"{child.pronoun('possessive').capitalize()} {prize.label} stayed safe, and the whole room felt warm and proud."
    )


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="grown-up"))
    hassock = world.add(Entity(id="hassock", type="hassock", label="hassock"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=child.id, caretaker=parent.id, plural=prize_cfg.plural))

    world.facts.update(child=child, parent=parent, hassock=hassock, prize=prize, action=action, setting=setting)

    introduce(world, child)
    foreshadow(world, child, hassock)
    world.para()
    warn(world, parent, child, action, prize)
    begin_skate(world, child, prize)
    stumble_warning(world, child)
    world.para()
    try_move_hassock(world)
    lesson_learned(world, child, parent, action, prize)
    finish(world, child, prize)
    return world


SETTINGS = {
    "front_room": Setting(place="the front room", affords={"skate"}),
    "hall": Setting(place="the hall", affords={"skate"}),
    "porch": Setting(place="the porch", affords={"skate"}),
}

ACTIONS = {
    "skate": Action(
        id="skate",
        verb="skate around the room",
        gerund="skating around the room",
        rush="push too fast around the hassock",
        risk="the skates can bump the hassock legs",
        clue="The path was a little narrow",
        lesson="Slowing down and moving the hassock made the skating safe and fun",
        keyword="skate",
        tags={"skate", "lesson", "foreshadowing", "heartwarming"},
    )
}

PRIZES = {
    "ball": Prize(label="red ball", phrase="a bright red ball", type="ball", region="floor"),
    "cup": Prize(label="cup", phrase="a tiny paper cup", type="cup", region="floor"),
    "ribbon": Prize(label="ribbon", phrase="a silky ribbon", type="ribbon", region="floor"),
}

GIRL_NAMES = ["Mila", "Tessa", "Nora", "Luna", "Iris"]
BOY_NAMES = ["Finn", "Owen", "Theo", "Ben", "Arlo"]
TRAITS = ["careful", "brave", "curious", "gentle"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(action: Action, prize: Prize) -> str:
    return f"(No story: this world only tells a skating tale, and '{action.id}' must be possible in the chosen setting.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming skate-and-hassock storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if getattr(args, "activity", None) and getattr(args, "activity", None) not in ACTIONS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, prize = _safe_lookup(ACTIONS, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not any(True for _ in [1]):
            pass
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short heartwarming story about a child who wants to skate, a hassock in the way, and a gentle lesson learned.',
        f"Tell a story where {f['child'].label} wants to skate in {world.setting.place} but the hassock makes the path feel tight.",
        'Write a child-friendly story that includes the words skate, hassock, and sociopath, and ends with a safe, happy choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, prize, action = f["child"], f["parent"], f["prize"], f["action"]
    return [
        QAItem(
            question=f"What did {child.label} want to do in {world.setting.place}?",
            answer=f"{child.label} wanted to {action.verb} while wearing {prize.label} and enjoying the smooth floor.",
        ),
        QAItem(
            question="Why did the grown-up mention the hassock?",
            answer="Because the hassock sat in a narrow spot, and the skates might bump its little legs if nobody moved it first.",
        ),
        QAItem(
            question=f"What did {child.label} learn by the end?",
            answer="The child learned that slowing down, moving the hassock, and choosing a safe path can still make play feel wonderful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a skate?",
            answer="A skate is something you wear or ride to glide smoothly across a floor or ice.",
        ),
        QAItem(
            question="What is a hassock?",
            answer="A hassock is a small soft footstool or cushion you can sit on or rest your feet on.",
        ),
        QAItem(
            question="What does the word sociopath mean?",
            answer="It is a hard word for a person who does not care about other people's feelings and often hurts them; this story uses it only as a book title in the room.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(front_room).
setting(hall).
setting(porch).
affords(front_room,skate).
affords(hall,skate).
affords(porch,skate).

activity(skate).
mess_of(skate,smack).
splashes(skate,floor).

prize(ball).
worn_on(ball,floor).
prize(cup).
worn_on(cup,floor).
prize(ribbon).
worn_on(ribbon,floor).

gear(hassock).
covers(hassock,floor).

valid(Place,Act,Prize) :- affords(Place,Act), activity(Act), prize(Prize), worn_on(Prize,floor).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        for a in _safe_lookup(SETTINGS, pid).affords:
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, "floor"))
    lines.append(asp.fact("gear", "hassock"))
    lines.append(asp.fact("covers", "hassock", "floor"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in [StoryParams(place=pl, action=ac, prize=pr, name="Mila", gender="girl", parent="mother", trait="gentle") for (pl, ac, pr) in valid_combos()]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
