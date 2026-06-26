#!/usr/bin/env python3
"""
storyworlds/worlds/microwave_kneel_inner_monologue_transformation_sound_effects.py
==================================================================================

A tiny mystery storyworld about a kitchen mystery: a microwave, a kneel,
an inner monologue, a transformation, and the sounds that reveal the truth.

The premise:
- A child notices something strange near the microwave.
- They kneel to look closer.
- Their inner monologue grows suspicious.
- The microwave's hum and beeps accompany a small transformation.
- The mystery resolves when the child learns what changed and why.

This script follows the Storyweavers standalone-world contract:
- self-contained stdlib script
- uses shared results containers eagerly
- imports ASP lazily only in ASP helpers
- provides StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    location: str = ""
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    microwave: object | None = None
    parent: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
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
    place: str = "the kitchen"
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
class Event:
    id: str
    action: str
    clue: str
    sound: str
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
class Target:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    transformed_into: str = ""
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    mystery: str = ""
    soundscape: list[str] = field(default_factory=list)

    clone: object | None = None
    world: object | None = None
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = _copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.mystery = self.mystery
        clone.soundscape = list(self.soundscape)
        return clone
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


def _set_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _set_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _rule_listen(world: World) -> list[str]:
    out = []
    child = world.get("child")
    microwave = world.get("microwave")
    if child.memes.get("curious", 0.0) >= THRESHOLD and (("listen",) not in world.fired):
        world.fired.add(("listen",))
        _set_meme(child, "focus", 1.0)
        out.append(f"{child.noun().capitalize()} listened hard to the microwave's low hum.")
    return out


def _rule_transform(world: World) -> list[str]:
    out = []
    snack = world.get("snack")
    if snack.meters.get("warmth", 0.0) >= THRESHOLD and snack.meters.get("changed", 0.0) < THRESHOLD:
        sig = ("transform", snack.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        snack.meters["changed"] = 1.0
        snack.type = snack.transformed_type if hasattr(snack, "transformed_type") else snack.type
        out.append(f"The snack changed shape in the warm glass dish.")
    return out


def _rule_smell_clue(world: World) -> list[str]:
    out = []
    if ("smell",) in world.fired:
        return out
    child = world.get("child")
    if child.memes.get("suspicion", 0.0) >= THRESHOLD:
        world.fired.add(("smell",))
        out.append("A sweet smell drifted out, like butter and honey.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_rule_listen, _rule_smell_clue, _rule_transform):
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
    name: str
    gender: str
    parent: str
    place: str
    event: str
    target: str
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
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"warmup", "wait"}),
    "pantry": Setting(place="the pantry", indoors=True, affords={"warmup", "wait"}),
    "breakfast_nook": Setting(place="the breakfast nook", indoors=True, affords={"warmup", "wait"}),
}

EVENTS = {
    "warmup": Event(
        id="warmup",
        action="warm something for a snack",
        clue="the microwave light blinked as if it knew a secret",
        sound="whirr",
        turn="The microwave hummed, then beeped twice.",
        keyword="microwave",
        tags={"microwave", "sound"},
    ),
    "wait": Event(
        id="wait",
        action="wait for the mystery to finish",
        clue="the little window stayed bright and glowing",
        sound="hum",
        turn="The sound slowed, and the room felt like it was holding its breath.",
        keyword="kneel",
        tags={"sound", "mystery"},
    ),
}

TARGETS = {
    "mallow": Target(
        label="marshmallow",
        phrase="a plain white marshmallow",
        type="marshmallow",
        location="dish",
        transformed_into="golden puff",
        genders={"girl", "boy"},
    ),
    "bread": Target(
        label="bread slice",
        phrase="a soft slice of bread",
        type="bread",
        location="dish",
        transformed_into="toasty square",
    ),
    "butter": Target(
        label="butter pat",
        phrase="a small pat of butter",
        type="butter",
        location="dish",
        transformed_into="shining melt",
    ),
}

GIRL_NAMES = ["Maya", "Luna", "Nina", "Ivy", "Zoe", "Pia"]
BOY_NAMES = ["Owen", "Milo", "Ezra", "Finn", "Theo", "Jude"]
TRAITS = ["quiet", "curious", "careful", "brave", "watchful", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for event in setting.affords:
            for target in TARGETS:
                combos.append((place, event, target))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with a microwave clue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--target", choices=TARGETS)
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
    if getattr(args, "gender", None) and getattr(args, "name", None) is None:
        pass
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "event", None) is None or c[1] == getattr(args, "event", None))
              and (getattr(args, "target", None) is None or c[2] == getattr(args, "target", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, event, target = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(TARGETS, target).genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent, place=place, event=event, target=target)


def _intro(world: World, child: Entity, parent: Entity, target: Entity) -> None:
    world.say(
        f"{child.noun().capitalize()} was a little {child.type} named {child.id}, and {child.pronoun('possessive')} "
        f"{parent.noun()} loved quiet afternoons in {world.setting.place}."
    )
    world.say(
        f"On the counter sat {target.phrase}, waiting beside the microwave like a clue in a case."
    )


def _inner_monologue(world: World, child: Entity, event: Event, target: Entity) -> None:
    _set_meme(child, "curious", 1.0)
    _set_meme(child, "suspicion", 1.0)
    world.say(
        f"{child.noun().capitalize()} heard {event.sound}... {event.sound}... and thought, "
        f'"Why does it sound like that? Did something happen to {target.label}?"'
    )
    propagate(world, narrate=True)


def _kneel(world: World, child: Entity) -> None:
    _set_meter(child, "kneel", 1.0)
    world.say(
        f"{child.noun().capitalize()} knelt on the cool floor and peeked under the counter."
    )


def _turn(world: World, child: Entity, parent: Entity, event: Event, target: Entity) -> None:
    world.say(event.turn)
    world.soundscape.append(event.sound)
    _set_meter(world.get("microwave"), "hum", 1.0)
    _set_meter(world.get("snack"), "warmth", 1.0)
    if target.id == "mallow":
        _set_meter(world.get("snack"), "warmth", 1.0)
    world.say(
        f"{child.id} blinked. In the dish, the {target.label} began to look puffier and brighter."
    )
    propagate(world, narrate=True)
    world.say(
        f"{parent.id} leaned over and smiled. \"It was only warming up,\" {parent.pronoun('subject')} said."
    )


def _resolve(world: World, child: Entity, parent: Entity, target: Entity) -> None:
    _set_meme(child, "relief", 1.0)
    _set_meme(child, "joy", 1.0)
    world.say(
        f"{child.id} grinned, because the mystery had a simple answer: the microwave had changed the snack."
    )
    world.say(
        f"Now the kitchen smelled sweet and warm, and {target.label} sat there like a tiny treasure revealed."
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    microwave = world.add(Entity(id="microwave", type="microwave", label="microwave", location=params.place))
    target_cfg = _safe_lookup(TARGETS, params.target)
    snack = world.add(Entity(
        id="snack",
        type=target_cfg.type,
        label=target_cfg.label,
        phrase=target_cfg.phrase,
        caretaker=parent.id,
        location="dish",
    ))
    setattr(snack, "transformed_type", target_cfg.transformed_into)

    world.mystery = "a warm kitchen mystery"

    _intro(world, child, parent, snack)
    world.para()
    _inner_monologue(world, child, _safe_lookup(EVENTS, params.event), snack)
    _kneel(world, child)
    world.para()
    _turn(world, child, parent, _safe_lookup(EVENTS, params.event), snack)
    world.para()
    _resolve(world, child, parent, snack)

    world.facts.update(child=child, parent=parent, microwave=microwave, snack=snack, event=_safe_lookup(EVENTS, params.event), target=target_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    event = _safe_fact(world, f, "event")
    target = _safe_fact(world, f, "target")
    return [
        f'Write a short mystery story for a young child that includes the word "microwave".',
        f"Tell a gentle story where {child.id} hears a strange {event.sound} sound, kneels to look closer, and discovers what happened to {target.label}.",
        f'Write a child-friendly mystery with an inner monologue, a kneeling clue, and a transformation in the kitchen.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    event = _safe_fact(world, f, "event")
    target = _safe_fact(world, f, "target")
    return [
        QAItem(
            question=f"What did {child.id} do when the microwave made a strange sound?",
            answer=f"{child.id} knelt on the kitchen floor and listened more closely because the sound felt like a mystery.",
        ),
        QAItem(
            question=f"What did {child.id} think about in {child.pronoun('possessive')} inner monologue?",
            answer=f"{child.id} wondered whether something had changed the {target.label} and why the microwave was humming so softly.",
        ),
        QAItem(
            question=f"What changed in the story?",
            answer=f"The {target.label} changed in the warm microwave, turning into {target.transformed_into} and showing that the sound had been part of cooking.",
        ),
        QAItem(
            question=f"Who explained the mystery at the end?",
            answer=f"{parent.id} explained that it was only warming up, which solved the little kitchen mystery for {child.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a microwave do?",
            answer="A microwave warms food quickly by using energy that makes the food heat up from the inside.",
        ),
        QAItem(
            question="Why might someone kneel to look at something?",
            answer="Someone might kneel to get closer to the floor or a low object so they can see it more clearly.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in your mind that says what you are thinking.",
        ),
        QAItem(
            question="Why do sounds matter in a mystery story?",
            answer="Sounds can give clues, because they help the character notice that something important is happening.",
        ),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.location:
            parts.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired if x))}")
    return "\n".join(lines)


ASP_RULES = r"""
% The microwave story has a simple declarative twin:
% a character kneels when curious, sound becomes a clue, and a warm snack transforms.

curious(C) :- character(C), wants_to_know(C).
kneels(C) :- character(C), curious(C).
hears_clue(C) :- character(C), sound_effect(microwave_hum), kneels(C).
transform(S) :- snack(S), warmed(S).
solved(C) :- hears_clue(C), parent_explains.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        if setting.indoors:
            lines.append(asp.fact("indoors", place))
        for ev in setting.affords:
            lines.append(asp.fact("affords", place, ev))
    for ev in EVENTS.values():
        lines.append(asp.fact("event", ev.id))
        lines.append(asp.fact("sound_effect", f"{ev.keyword}_hum"))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("snack", tid))
        lines.append(asp.fact("warmed", tid))
        for g in sorted(target.genders):
            lines.append(asp.fact("wears", g, tid))
    lines.append(asp.fact("parent_explains"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show afford/2."))
    return sorted(set(asp.atoms(model, "affords")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(python_set - clingo_set))
    print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def explain_rejection() -> str:
    return "(No story: the chosen options do not fit this small mystery kitchen world.)"


CURATED = [
    StoryParams(name="Maya", gender="girl", parent="mother", place="kitchen", event="warmup", target="mallow"),
    StoryParams(name="Theo", gender="boy", parent="father", place="breakfast_nook", event="wait", target="bread"),
    StoryParams(name="Luna", gender="girl", parent="mother", place="pantry", event="warmup", target="butter"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show solved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show affords/2."))
        print("\n".join(f"{a} {b}" for a, b in sorted(set(asp.atoms(model, "affords")))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.event} at {p.place} (target: {p.target})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
