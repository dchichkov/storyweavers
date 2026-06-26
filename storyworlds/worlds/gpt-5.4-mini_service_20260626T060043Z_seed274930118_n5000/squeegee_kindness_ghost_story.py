#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/squeegee_kindness_ghost_story.py
============================================================================================================

A small story world in the shape of a gentle ghost story.

Premise:
- A child or friendly helper notices a shy ghost and a smeared, foggy window.
- The ghost cannot see clearly through the mist.
- A squeegee can clear the glass, but only if someone uses it with kindness.

Tension:
- The ghost is worried it will stay stuck in a blurry, lonely room.
- The helper might be startled, but kindness changes the feeling of the room.

Turn:
- The helper speaks softly, learns the ghost's wish, and uses the squeegee to clear the glass.

Resolution:
- The room brightens, the ghost feels seen, and the ending image proves the change.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    room: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    ghost: object | None = None
    item: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman"}
        masculine = {"boy", "father", "dad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str
    indoors: bool = True
    darkness: str = "dim"
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
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)
    ACTIVITY: object | None = None
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
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    is_gear: bool = False
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    needs_kindness: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _rule_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ghost in world.characters():
        if ghost.type != "ghost":
            continue
        if ghost.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        sig = ("kindness", ghost.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ghost.memes["fear"] = max(0.0, ghost.memes.get("fear", 0.0) - 1.0)
        ghost.memes["trust"] = ghost.memes.get("trust", 0.0) + 1.0
        out.append("The room felt a little warmer.")
    return out


def _rule_smear(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("squeegee", 0.0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.kind != "thing" or item.region not in world.zone:
                continue
            if item.id == "window":
                if world.facts.get("window_clear", False):
                    continue
                sig = ("clear", item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["fog"] = max(0.0, item.meters.get("fog", 0.0) - 1.0)
                item.meters["clean"] = item.meters.get("clean", 0.0) + 1.0
                world.facts["window_clear"] = True
                out.append("The squeegee drew a bright, clean path through the glass.")
    return out


def _rule_fear_to_friendship(world: World) -> list[str]:
    out: list[str] = []
    for ghost in world.characters():
        if ghost.type != "ghost":
            continue
        if ghost.memes.get("seen", 0.0) < THRESHOLD:
            continue
        sig = ("seen", ghost.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ghost.memes["lonely"] = max(0.0, ghost.memes.get("lonely", 0.0) - 1.0)
        ghost.memes["joy"] = ghost.memes.get("joy", 0.0) + 1.0
        out.append("The ghost no longer felt lonely in the dark.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_rule_kindness, _rule_smear, _rule_fear_to_friendship):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
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
    "attic": Setting(place="the attic", indoors=True, darkness="dim", affords={"squeegee"}),
    "hallway": Setting(place="the old hallway", indoors=True, darkness="blue-gray", affords={"squeegee"}),
    "sunroom": Setting(place="the sunroom", indoors=True, darkness="misty", affords={"squeegee"}),
}

TRAITS = ["brave", "gentle", "curious", "quiet", "kind"]

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Mia"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Ben", "Noah"]

ACTIVITY = Activity(
    id="squeegee",
    verb="clear the window",
    gerund="squeegeeing the glass",
    rush="scrub the fog away",
    mess="foggy",
    soil="blurry and cold",
    zone={"window"},
    keyword="squeegee",
    tags={"ghost", "kindness", "window", "fog"},
)

ITEMS = {
    "window": Item(
        id="window",
        label="window",
        phrase="a tall window with cloudy glass",
        region="window",
        plural=False,
        genders={"girl", "boy"},
    )
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            combos.append((place, act))
    return combos


def reasonableness_gate(place: str) -> bool:
    return place in SETTINGS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle ghost story about kindness, a foggy window, and a squeegee."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    if not reasonableness_gate(place):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait)


def introduce(world: World, child: Entity, ghost: Entity, parent: Entity, item: Entity) -> None:
    world.say(
        f"{child.id} was a {child.traits[0]} little {child.type} who noticed things other people missed."
    )
    world.say(
        f"In {world.setting.place}, {child.id} saw a shy ghost near {item.phrase}."
    )
    world.say(
        f"The ghost was not scary. It just looked lonely, like it had lost its way through the dark."
    )


def tension(world: World, child: Entity, ghost: Entity, item: Entity) -> None:
    child.memes["surprise"] = child.memes.get("surprise", 0.0) + 1.0
    ghost.memes["fear"] = ghost.memes.get("fear", 0.0) + 1.0
    ghost.memes["lonely"] = ghost.memes.get("lonely", 0.0) + 1.0
    world.say(
        f"The window was fogged over, and the ghost could not see the moon or the room beyond it."
    )
    world.say(
        f"{child.id} wanted to run, but {child.pronoun('possessive')} heart felt a soft kind tug instead."
    )
    world.say(
        f'"I can help," {child.id} whispered, because being kind felt braver than being afraid.'
    )


def turn(world: World, child: Entity, ghost: Entity, item: Entity) -> None:
    child.memes["kindness"] = child.memes.get("kindness", 0.0) + 1.0
    ghost.memes["seen"] = ghost.memes.get("seen", 0.0) + 1.0
    child.meters["squeegee"] = child.meters.get("squeegee", 0.0) + 1.0
    world.zone = {"window"}
    world.say(
        f"{child.id} picked up the squeegee and moved slowly, like they were petting the air."
    )
    world.say(
        f'"First I will make the glass clear," {child.id} said, "and then you can see where you are."'
    )
    propagate(world, narrate=True)


def resolution(world: World, child: Entity, ghost: Entity, parent: Entity, item: Entity) -> None:
    ghost.memes["kindness"] = ghost.memes.get("kindness", 0.0) + 1.0
    world.say(
        f"The fog slid away from the window, and a silver moon shone into the old room."
    )
    world.say(
        f"The ghost smiled, small and bright as a candle flame. It waved at {child.id} as if they were old friends."
    )
    world.say(
        f"{child.id} stood by the clear glass while {child.pronoun('possessive')} {parent.label} came to the door, smiling too."
    )


def tell(setting: Setting, hero_name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=gender, traits=[trait, "kind"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"{parent_type}"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", traits=["shy", "gentle"]))
    item = world.add(Entity(id="window", kind="thing", type="window", label="window", phrase="the old window"))

    world.say(
        f"One night, {child.id} walked into {setting.place}, where the air was blue-gray and very still."
    )
    world.say(
        f"Then a little ghost floated by the window, looking as if it had been waiting for a friendly voice."
    )
    world.para()
    introduce(world, child, ghost, parent, item)
    tension(world, child, ghost, item)
    world.para()
    turn(world, child, ghost, item)
    resolution(world, child, ghost, parent, item)

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        item=item,
        activity=ACTIVITY,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        'Write a gentle ghost story for a preschooler about a kind child and a foggy window.',
        f'Write a short story where {child.id} uses a squeegee to help a shy ghost in {world.setting.place}.',
        'Tell a spooky-but-safe story about kindness making a dark room feel warm.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    ghost = _safe_fact(world, f, "ghost")
    item = _safe_fact(world, f, "item")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who was the story about in {place}?",
            answer=f"It was about {child.id}, a {child.traits[0]} little {child.type}, and a shy ghost near the window.",
        ),
        QAItem(
            question="What problem did the ghost have?",
            answer="The window was fogged over, so the ghost could not see clearly and felt lonely in the dark room.",
        ),
        QAItem(
            question=f"What did {child.id} use to help?",
            answer="The child used a squeegee to clear the fog from the glass.",
        ),
        QAItem(
            question="How did kindness change the room?",
            answer="Kindness made the ghost feel safe, and the room felt warmer once the window was clear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a squeegee for?",
            answer="A squeegee is a tool with a flat edge that helps wipe water or fog off glass.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means acting gently and helpfully so someone else feels safe and cared for.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky story character that can be mysterious, but in a gentle story it can also be shy or friendly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the chosen place supports the squeegee scene.
valid_story(P) :- place(P), affords(P, squeegee).

% The ghost's fear is resolved when kindness and squeegee both happen.
resolved(P) :- valid_story(P), kindness(P), cleared(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    lines.append(asp.fact("activity", "squeegee"))
    lines.append(asp.fact("mood", "kindness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    clingo_places = {t[0] for t in asp.atoms(model, "valid_story")}
    python_places = {p for p, _ in valid_combos()}
    if clingo_places == python_places:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_places)} places).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_places - python_places))
    print("  only in python:", sorted(python_places - clingo_places))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.name, params.gender, params.parent, params.trait)
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


CURATED = [
    StoryParams(place="attic", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="hallway", name="Theo", gender="boy", parent="father", trait="kind"),
    StoryParams(place="sunroom", name="Ivy", gender="girl", parent="mother", trait="curious"),
]


def resolve_args_and_generate(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        places = sorted(set(asp.atoms(model, "valid_story")))
        print(places)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in CURATED:
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait)


if __name__ == "__main__":
    main()
