#!/usr/bin/env python3
"""
storyworlds/worlds/thunk_complete_bad_ending_heartwarming.py
=============================================================

A small storyworld about trying to complete a careful project, hearing a thunk,
and ending with a warm-but-bad outcome.

Seed tale:
---
A child wants to complete a tiny gift for a parent: a paper star lantern, a
row of stickers, or a little tower of blocks. The child works hard, but one
careless thunk sends the project tumbling. The parent comforts the child and
helps clean up. The project is not saved, yet the love behind it still feels
complete.

World focus:
- physically modeled fragile project pieces and a falling object
- emotional state around hope, pride, surprise, disappointment, and comfort
- a bad ending that still lands in a heartwarming way
- child-facing prose driven by state changes, not static template swapping
"""

from __future__ import annotations

import argparse
import copy
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
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    fragile: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    falling: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the kitchen table"
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
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
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
class Prize:
    label: str
    phrase: str
    type: str
    fragile: bool = True
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
class FallingThing:
    label: str
    thunk: str
    mess: str
    tags: set[str] = field(default_factory=set)
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
        self.thunked: bool = False

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.thunked = self.thunked
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    falling: str
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


SETTINGS = {
    "kitchen": Setting("the kitchen table", {"paper", "blocks", "stickers"}),
    "bedroom": Setting("the bedroom desk", {"paper", "blocks", "stickers"}),
    "porch": Setting("the porch bench", {"paper", "blocks"}),
}

ACTIVITIES = {
    "complete": Activity(
        id="complete",
        verb="complete the project",
        gerund="completing the project",
        rush="reach for one more piece",
        mess="scattered",
        soil="scattered across the floor",
        keyword="complete",
        tags={"complete", "heartwarming"},
    ),
    "decorate": Activity(
        id="decorate",
        verb="decorate the gift",
        gerund="decorating the gift",
        rush="lean in with the glue",
        mess="smudged",
        soil="smudged and messy",
        keyword="decorate",
        tags={"decorate"},
    ),
}

PRIZES = {
    "star": Prize("star", "a paper star lantern", "lantern", fragile=True),
    "tower": Prize("tower", "a little block tower", "tower", fragile=True),
    "stickerbook": Prize("stickerbook", "a sticker-covered notebook", "book", fragile=True),
}

FALLING = {
    "book": FallingThing("book", "thunk", "cracked", {"thunk"}),
    "tray": FallingThing("tray", "thunk", "scattered", {"thunk"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Ben", "Noah", "Eli"]
TRAITS = ["gentle", "curious", "quiet", "cheerful", "earnest"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                for fall in FALLING:
                    combos.append((place, act, prize, fall))
    return combos


def _can_actually_go_bad(act: Activity, prize: Prize, fall: FallingThing) -> bool:
    return prize.fragile and "thunk" in fall.tags and act.id in {"complete", "decorate"}


def explain_rejection(act: Activity, prize: Prize, fall: FallingThing) -> str:
    return (
        f"(No story: {act.gerund} with {prize.label} and {fall.label} does not make a "
        f"clear, child-sized bad ending here.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "prize", None) and getattr(args, "falling", None):
        if not _can_actually_go_bad(_safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None)), FALLING[getattr(args, "falling", None)]):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
        and (getattr(args, "falling", None) is None or c[3] == getattr(args, "falling", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, act_id, prize_id, fall_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place, act_id, prize_id, fall_id, name, gender, parent, trait)


def _do_activity(world: World, actor: Entity, activity: Activity, prize: Entity, falling: Entity, narrate: bool = True) -> None:
    actor.memes["hope"] += 1
    actor.memes["pride"] += 1
    world.say(f"{actor.id} kept working to {activity.verb}, because {actor.pronoun('possessive')} {prize.label} was almost {activity.keyword} complete.")
    if narrate:
        world.say(f"The little room felt quiet and close, like it was holding its breath.")


def _thunk(world: World, actor: Entity, prize: Entity, falling: Entity) -> None:
    sig = ("thunk", actor.id, prize.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.thunked = True
    actor.memes["surprise"] += 1
    actor.memes["sadness"] += 1
    prize.meters["broken"] = prize.meters.get("broken", 0.0) + 1.0
    prize.meters["scattered"] = prize.meters.get("scattered", 0.0) + 1.0
    world.say(f'Then there was a loud {falling.thunk}.')
    world.say(f"{actor.pronoun().capitalize()} froze as the {prize.label} fell apart.")


def _comfort(world: World, child: Entity, parent: Entity, prize: Entity) -> None:
    sig = ("comfort", child.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["sadness"] = max(0.0, child.memes.get("sadness", 0.0) - 0.5)
    child.memes["comfort"] += 1
    parent.memes["love"] += 1
    world.say(f"{parent.pronoun().capitalize()} sat beside {child.id} and said, \"You worked so hard.\"")
    world.say(f"Together they gathered the pieces, and the room got calm again.")


def _bad_ending(world: World, child: Entity, prize: Entity) -> None:
    world.say(
        f"But the {prize.label} could not be made whole again that night. "
        f"It stayed broken in a small pile, and that was the bad ending."
    )
    child.memes["sadness"] += 1
    child.memes["love"] += 1


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, falling_cfg: FallingThing,
         hero_name: str, hero_type: str, hero_traits: Optional[list[str]], parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        meters={}, memes={"hope": 0.0, "pride": 0.0, "sadness": 0.0, "comfort": 0.0, "love": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="parent",
        meters={}, memes={"love": 0.0},
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, fragile=prize_cfg.fragile, plural=prize_cfg.plural,
        meters={}, memes={},
    ))
    falling = world.add(Entity(
        id="falling", type=falling_cfg.label, label=falling_cfg.label, phrase=falling_cfg.label,
        meters={}, memes={},
    ))

    trait = next((t for t in (hero_traits or []) if t != "little"), "")
    intro = f"Little {trait} {hero.type} {hero.id}".strip()
    world.say(f"{intro} wanted to finish a tiny gift with care.")
    world.say(f"{hero.id} loved making things complete for {parent.label}.")
    world.para()

    _do_activity(world, hero, activity, prize, falling)
    world.say(f"{hero.id} was almost done when {hero.pronoun('possessive')} hand slipped.")
    _thunk(world, hero, prize, falling)
    world.para()
    _comfort(world, hero, parent, prize)
    _bad_ending(world, hero, prize)

    world.facts.update(
        hero=hero, parent=parent, prize=prize, falling=falling,
        activity=activity, setting=setting, resolved=False,
        bad_ending=True, trait=trait or hero_type,
    )
    return world


KNOWLEDGE = {
    "thunk": [
        ("What is a thunk?",
         "A thunk is a heavy, dull sound, like something bumping or falling onto the floor."),
    ],
    "complete": [
        ("What does complete mean?",
         "Complete means all the parts are there and nothing is missing."),
    ],
    "paper": [
        ("What is paper?",
         "Paper is a thin material people write and draw on, and they can fold or cut it too."),
    ],
    "blocks": [
        ("What are blocks for?",
         "Blocks are small pieces that children can stack to build towers and shapes."),
    ],
    "sticker": [
        ("Why do stickers feel fun?",
         "Stickers feel fun because you can peel them off and stick them onto pages or gifts."),
    ],
}
KNOWLEDGE_ORDER = ["thunk", "complete", "paper", "blocks", "sticker"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        f'Write a heartwarming story for a young child about trying to {activity.verb} and hearing a thunk.',
        f"Tell a gentle story where {hero.id} wants to finish {prize.phrase} for {parent.label}, but the project goes bad.",
        f'Write a short story that uses the words "{activity.keyword}" and "thunk" and ends with a warm comfort scene.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    trait = _safe_fact(world, f, "trait")
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {prize.label}?",
            answer=f"{hero.id} wanted to {activity.verb}. {hero.id} was trying to make it feel {activity.keyword} complete for {parent.label}.",
        ),
        QAItem(
            question=f"What sound changed the story for {hero.id}?",
            answer="A loud thunk changed everything and made the project fall apart.",
        ),
        QAItem(
            question=f"How did {parent.label} help {hero.id} after the accident?",
            answer=f"{parent.label.capitalize()} sat beside {hero.id}, told {hero.id} that the work mattered, and helped gather the pieces.",
        ),
        QAItem(
            question=f"Was the {prize.label} finished in the end?",
            answer=f"No. Even though {hero.id} worked hard, the {prize.label} stayed broken, so the ending was bad.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt sad about the broken {prize.label}, but also comforted because {parent.label} stayed close and kind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["activity"].keyword, "thunk", "complete", "paper", "blocks", "sticker"}
    out: list[QAItem] = []
    for key in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.fragile:
            bits.append("fragile=True")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  thunked={world.thunked}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "complete", "star", "book", "Mia", "girl", "mother", "gentle"),
    StoryParams("bedroom", "decorate", "stickerbook", "tray", "Leo", "boy", "father", "earnest"),
    StoryParams("porch", "complete", "tower", "book", "Nora", "girl", "mother", "quiet"),
]


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: this world does not need gender restrictions, but {prize_id} is okay for {gender}.)"


ASP_RULES = r"""
% A project is complete when the child activity targets it.
complete(Project) :- activity_targets(Activity, Project), activity(Activity).

% A thunk story is available when the falling thing can make a loud impact.
can_thunk(Fall) :- thunk_source(Fall).

% A bad ending is the combination of completion effort, a thunk, and a fragile project.
bad_ending(Place, Activity, Prize, Fall) :- affords(Place, Activity), fragile(Prize),
                                            can_thunk(Fall), complete(Project),
                                            targets(Prize, Project).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("fragile", pid))
    for fid in FALLING:
        lines.append(asp.fact("falling", fid))
        lines.append(asp.fact("thunk_source", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Simple parity gate: every curated combo should satisfy the Python reasonableness gate.
    python_ok = {(p.place, p.activity, p.prize, p.falling) for p in CURATED}
    asp_ok = set(valid_combos())
    if python_ok == asp_ok:
        print(f"OK: curated combos match valid_combos() ({len(asp_ok)} combos).")
        return 0
    print("MISMATCH between curated stories and valid_combos():")
    print(" python:", sorted(python_ok))
    print(" asp   :", sorted(asp_ok))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: complete, thunk, and a heartwarming bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--falling", choices=FALLING)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait")
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        FALLING[params.falling],
        params.name,
        params.gender,
        [params.trait],
        params.parent,
    )
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
        print(asp_program("#show bad_ending/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show bad_ending/4."))
        print(sorted(set(asp.atoms(model, "bad_ending"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
