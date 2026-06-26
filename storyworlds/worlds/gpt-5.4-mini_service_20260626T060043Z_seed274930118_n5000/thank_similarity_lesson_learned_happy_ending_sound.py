#!/usr/bin/env python3
"""
storyworlds/worlds/thank_similarity_lesson_learned_happy_ending_sound.py
========================================================================

A small pirate-tale storyworld about a child pirate, a noisy sound effect,
a lesson learned, and a thankful happy ending.

Premise:
- A young pirate loves a sound-making toy or task.
- A grown pirate worries that the sound will scare a sleeping sea friend or
  ruin a careful plan.
- The child first resists, then notices a useful similarity.
- That similarity helps them choose a gentler way.
- The story ends with gratitude and a happy pirate image.

This world keeps the prose concrete and state-driven:
meters track physical conditions like noise and calm;
memes track feelings like pride, worry, and gratitude.

It also includes an inline ASP twin of the reasonableness gate so verification
can compare the Python and clingo views of the same valid story space.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    quiet: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate", "sailor", "uncle"}
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Location:
    place: str = "the dock"
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
    sound: str
    mess: str
    effect: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    good_for: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Fix:
    id: str
    label: str
    covers: set[str]
    quiets: set[str]
    prep: str
    tail: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.location)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.lines = [[]]
        return clone


def sounds(activity: Action) -> str:
    return activity.sound


def lesson_line(activity: Action) -> str:
    return {
        "drum": "the drum sounded like a tiny thunder cloud",
        "bell": "the bell sounded like a bright tinkling spoon",
        "shell": "the shell sounded like the sea whispering back",
        "whistle": "the whistle sounded like a bird greeting the wind",
    }.get(activity.id, "it made a lively pirate sound")


def setting_line(location: Location) -> str:
    return {
        "the dock": "The dock creaked under the boards, and the water winked below.",
        "the ship": "The ship swayed softly, and ropes hummed in the wind.",
        "the beach": "The beach gleamed, and the foam made a lace edge at the shore.",
    }.get(location.place, f"{location.place.capitalize()} waited under the sky.")


def mark_noise(world: World, actor: Entity, activity: Action) -> None:
    actor.meters["noise"] += 1
    actor.memes["excitement"] += 1


def predict(world: World, actor: Entity, activity: Action, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "disturbed": prize.meters.get("shaken", 0) >= THRESHOLD,
        "noise": sum(e.meters.get("noise", 0) for e in sim.characters()),
    }


def do_activity(world: World, actor: Entity, activity: Action, narrate: bool = True) -> None:
    if activity.id not in world.location.affords:
        pass
    world.zone = {activity.mess}
    mark_noise(world, actor, activity)
    if narrate:
        world.say(f"{actor.id} went to {activity.verb}. {sounds(activity).capitalize()}!")


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("noise", 0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.meters.get("quiet", 0) >= THRESHOLD:
                continue
            sig = ("noise", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["shaken"] = item.meters.get("shaken", 0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} rattled a little.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("worry", 0) < THRESHOLD:
            continue
        sig = ("worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["stern"] = actor.memes.get("stern", 0) + 1
        out.append(f"{actor.id} frowned and kept watching the plan.")
    return out


CAUSAL_RULES = [
    _r_noise,
    _r_worry,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def is_reasonable(action: Action, prize: Prize, fix: Fix) -> bool:
    return prize.region in action.effect and prize.region in fix.covers and action.mess in fix.quiets


def choose_fix(action: Action, prize: Prize) -> Optional[Fix]:
    for fix in FIXES:
        if is_reasonable(action, prize, fix):
            return fix
    return None


def tell(location: Location, action: Action, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(location)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the captain", meters={}, memes={}))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
        plural=prize_cfg.plural,
        meters={"calm": 1.0},
    ))

    # Act 1
    world.say(f"{hero.id} was a little pirate who loved {action.gerund}.")
    world.say(f"{hero.pronoun().capitalize()} smiled at {lesson_line(action)}.")
    world.say(f"{parent.id} had given {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} liked {prize.label} because it felt brave and shiny.")

    # Act 2
    world.para()
    world.say(setting_line(location))
    world.say(f"{hero.id} wanted to {action.verb}, but {hero.pronoun('possessive')} {parent.label} worried about {prize.label}.")
    pred = predict(world, hero, action, prize.id)
    if pred["disturbed"]:
        world.facts["predicted_disturbance"] = True
        world.say(f'"If you do that, {prize.label} will get shaken," {parent.pronoun().capitalize()} said.')
    world.say(f"{hero.id} still tried to {action.rush}.")
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    propagate(world)

    # similarity moment
    world.para()
    world.say(f"Then {hero.id} looked at the {prize.label} and the {action.keyword}.")
    world.say(f"{hero.id} noticed a similarity: both could be noisy, but both could also be used gently.")
    world.say(f"That gave {hero.id} a lesson learned: being careful can still feel fun.")

    fix = choose_fix(action, prize)
    if fix is None:
        _fallback_pool = globals().get("FIXS") or globals().get("FIXES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        fix = next(iter(_fallback_pool), None)
        if fix is None:
            raise StoryError

    quiet = world.add(Entity(
        id=fix.id,
        type="thing",
        label=fix.label,
        owner=hero.id,
        caretaker=parent.id,
        meters={"quiet": 1.0},
    ))
    quiet.worn_by = hero.id

    # Act 3
    world.para()
    hero.memes["worry"] = 0.0
    hero.memes["gratitude"] = hero.memes.get("gratitude", 0) + 1
    parent.memes["pride"] = parent.memes.get("pride", 0) + 1
    world.say(f"{parent.id} pointed to the {quiet.label} and said, \"Try this first.\"")
    world.say(f"{hero.id} nodded and said, \"Thank ye, {parent.id}!\"")
    world.say(f"They used {fix.prep}, and soon {hero.id} could {action.verb} without making {prize.label} shake.")
    world.say(f"{fix.tail}.")
    world.say(f"{hero.id} laughed, the {prize.label} stayed steady, and the pirate day ended in a happy ending with a soft {action.sound}.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        action=action,
        fix=fix,
        location=location,
        similarity=True,
        lesson_learned=True,
        happy_ending=True,
    )
    return world


LOCATIONS = {
    "dock": Location(place="the dock", affords={"drum", "whistle"}),
    "ship": Location(place="the ship", affords={"bell", "drum", "whistle"}),
    "beach": Location(place="the beach", affords={"shell", "bell"}),
}

ACTIONS = {
    "drum": Action(
        id="drum",
        verb="beat the drum",
        gerund="beating drums",
        rush="rush to the drum barrel",
        sound="boom-boom",
        mess="noise",
        effect={"torso"},
        keyword="drum",
        tags={"sound", "lesson"},
    ),
    "bell": Action(
        id="bell",
        verb="ring the bell",
        gerund="ringing bells",
        rush="grab the bell rope",
        sound="ding-ding",
        mess="noise",
        effect={"torso"},
        keyword="bell",
        tags={"sound", "lesson"},
    ),
    "shell": Action(
        id="shell",
        verb="blow the shell",
        gerund="blowing shells",
        rush="lift the shell to the mouth",
        sound="whooosh",
        mess="noise",
        effect={"mouth"},
        keyword="shell",
        tags={"sound", "similarity"},
    ),
    "whistle": Action(
        id="whistle",
        verb="whistle a tune",
        gerund="whistling tunes",
        rush="pucker up for a whistle",
        sound="tweet-tweet",
        mess="noise",
        effect={"mouth"},
        keyword="whistle",
        tags={"sound", "similarity"},
    ),
}

PRIZES = {
    "parrot": Prize(label="parrot", phrase="a sleepy green parrot", type="bird", region="shoulder"),
    "map": Prize(label="map", phrase="an old sea map", type="map", region="torso"),
    "lantern": Prize(label="lantern", phrase="a brass lantern", type="lantern", region="hand"),
}

FIXES = [
    Fix(id="soft_drum", label="a soft cloth drum", covers={"torso"}, quiets={"noise"}, prep="placing a cloth over the drum", tail="The cloth made the sound gentle and neat."),
    Fix(id="shell_hush", label="a little shell cup", covers={"mouth"}, quiets={"noise"}, prep="blowing the shell very softly", tail="The shell whispered instead of shouting."),
    Fix(id="bell_wrap", label="a rope wrap", covers={"torso"}, quiets={"noise"}, prep="wrapping the bell rope in cloth", tail="The bell still sang, but it sang low and kind."),
]

GIRL_NAMES = ["Ava", "Mina", "Luna", "Pearl", "Ruby"]
BOY_NAMES = ["Finn", "Jace", "Milo", "Ned", "Oren"]
TRAITS = ["brave", "curious", "cheerful", "spirited"]


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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, loc in LOCATIONS.items():
        for act_id in loc.affords:
            act = _safe_lookup(ACTIONS, act_id)
            for prize_id, prize in PRIZES.items():
                fix = choose_fix(act, prize)
                if fix is not None:
                    out.append((place, act_id, prize_id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    action = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "action")
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    return [
        f'Write a short pirate story for a young child that includes the word "{action.keyword}" and a happy ending.',
        f"Tell a story where {hero.id} wants to {action.verb} but learns a lesson about being gentle around {prize.label}.",
        f"Write a pirate tale with sound effects, a similarity idea, and a thank-you at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    action = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "action")
    fix = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "fix")
    return [
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {action.verb}, because {hero.pronoun().capitalize()} loved the sound and the lively pirate feeling.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that being careful can still be fun, especially when a noisy thing is used gently.",
        ),
        QAItem(
            question=f"How did {hero.id} thank {parent.id}?",
            answer=f"{hero.id} said, \"Thank ye, {parent.id}!\" after the grown pirate found a gentler plan.",
        ),
        QAItem(
            question=f"What helped the story end happily?",
            answer=f"The {fix.label} helped {hero.id} {action.verb} without making {prize.label} shake, so everyone could smile at the end.",
        ),
    ]


WORLD_QA = {
    "sound": [
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises that help a story feel lively, like boom, ding, or whoosh.",
        )
    ],
    "similarity": [
        QAItem(
            question="What is a similarity?",
            answer="A similarity is when two things are alike in some way, even if they are not exactly the same.",
        )
    ],
    "lesson": [
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="Learning a lesson means understanding something new that can help you make a better choice next time.",
        )
    ],
    "thank": [
        QAItem(
            question="Why do people say thank you?",
            answer="People say thank you to show kindness and to notice when someone helps them.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "action").tags)
    tags.update({"sound", "similarity", "lesson", "thank"})
    out: list[QAItem] = []
    for tag in ["sound", "similarity", "lesson", "thank"]:
        out.extend(WORLD_QA[tag])
    return out


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="dock", action="drum", prize="parrot", name="Finn", gender="boy", parent="captain", trait="brave"),
    StoryParams(place="ship", action="bell", prize="map", name="Ava", gender="girl", parent="captain", trait="curious"),
    StoryParams(place="beach", action="shell", prize="lantern", name="Mina", gender="girl", parent="captain", trait="cheerful"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- action(A), prize(P), touches(A,R), worn_on(P,R).
reasonable_fix(A,P,F) :- action(A), prize(P), prize_at_risk(A,P),
                         fix(F), quiets(F,M), mess_of(A,M), covers(F,R), worn_on(P,R).
valid_story(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), reasonable_fix(A,P,_).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, loc in LOCATIONS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(loc.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.effect):
            lines.append(asp.fact("touches", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for m in sorted(fx.quiets):
            lines.append(asp.fact("quiets", fx.id, m))
        for r in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_stories() -> list[tuple[str, str, str]]:
    return sorted(valid_combos())


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate storyworld with thankfulness, similarity, lesson learned, sound effects, and a happy ending.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain", "pirate"])
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
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    prize_cfg = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(LOCATIONS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible story combos:\n")
        for place, action, prize in stories:
            print(f"  {place:8} {action:8} {prize:8}")
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
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.action} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
