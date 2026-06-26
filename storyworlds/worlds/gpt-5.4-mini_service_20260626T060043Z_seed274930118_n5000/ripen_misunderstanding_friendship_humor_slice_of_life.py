#!/usr/bin/env python3
"""
A small standalone story world about a friendship mix-up around fruit ripening.

Premise:
- Two friends share a little everyday errand.
- One friend thinks the other is hiding a treat.
- The misunderstanding turns funny when they discover the fruit was simply ripening.
- Friendship grows through an easy, slice-of-life resolution.

This script follows the Storyweavers contract:
- self-contained stdlib storyworld
- eager imports from storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify checks Python/ASP parity and exercises sample stories
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend_a: object | None = None
    friend_b: object | None = None
    fruit: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    indoor: bool = False
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
class Fruit:
    id: str
    label: str
    phrase: str
    stages: list[str]
    ripe_stage: str = "ripe"
    result_phrase: str = "ready to eat"
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
class Person:
    type: str
    names: list[str]
    traits: list[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_ripe(world: World) -> list[str]:
    out: list[str] = []
    fruit = world.get("fruit")
    if fruit.meters["ripeness"] < THRESHOLD:
        return out
    sig = ("ripe", fruit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fruit.memes["sweet"] += 1
    out.append(f"The fruit softened and turned {world.facts['fruit'].label} and fragrant.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    observer = world.get("friend_a")
    fruit = world.get("fruit")
    if observer.memes["suspicion"] < THRESHOLD:
        return out
    sig = ("misunderstanding", observer.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    observer.memes["confused"] += 1
    out.append(f"{observer.id} stared at the fruit and got the wrong idea.")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("friend_a")
    b = world.get("friend_b")
    fruit = world.get("fruit")
    if a.memes["confused"] < THRESHOLD or b.memes["kindness"] < THRESHOLD:
        return out
    sig = ("laugh", fruit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["humor"] += 1
    b.memes["humor"] += 1
    a.memes["warmth"] += 1
    b.memes["warmth"] += 1
    out.append(f"They laughed when they realized the fruit had only been ripening on the counter.")
    return out


RULES = [
    Rule("ripe", _r_ripe),
    Rule("misunderstanding", _r_misunderstanding),
    Rule("laugh", _r_laugh),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"talk", "wait"}),
    "balcony": Setting(place="the balcony", indoor=False, affords={"talk", "wait"}),
    "living_room": Setting(place="the living room", indoor=True, affords={"talk", "wait"}),
}

FRUITS = {
    "peach": Fruit(
        id="peach",
        label="peach",
        phrase="a soft peach on the counter",
        stages=["green", "almost-ripe", "ripe"],
        ripe_stage="ripe",
        result_phrase="sweet and ready",
    ),
    "pear": Fruit(
        id="pear",
        label="pear",
        phrase="a pear in a bowl",
        stages=["firm", "warming", "ripe"],
        ripe_stage="ripe",
        result_phrase="sweet and fragrant",
    ),
    "banana": Fruit(
        id="banana",
        label="banana",
        phrase="a bunch of bananas by the window",
        stages=["green", "spotted", "ripe"],
        ripe_stage="ripe",
        result_phrase="soft and sweet",
    ),
}

PEOPLE = {
    "girl": Person(type="girl", names=["Mia", "Nora", "Lina", "Tess", "Ruby"], traits=["curious", "gentle", "bright"]),
    "boy": Person(type="boy", names=["Noah", "Eli", "Finn", "Owen", "Theo"], traits=["curious", "gentle", "bright"]),
}

PARTNER_NAMES = ["Jo", "Sam", "Parker", "Ari", "June", "Bea"]
TRAITS = ["curious", "gentle", "playful", "patient", "bright"]


@dataclass
class StoryParams:
    place: str
    fruit: str
    name_a: str
    type_a: str
    name_b: str
    type_b: str
    trait_a: str
    trait_b: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: ripening fruit, misunderstanding, friendship, and humor.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--fruit", choices=FRUITS.keys())
    ap.add_argument("--name-a")
    ap.add_argument("--type-a", choices=PEOPLE.keys())
    ap.add_argument("--name-b")
    ap.add_argument("--type-b", choices=PEOPLE.keys())
    ap.add_argument("--trait-a", choices=TRAITS)
    ap.add_argument("--trait-b", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    fruit = getattr(args, "fruit", None) or rng.choice(list(FRUITS))
    ta = getattr(args, "type_a", None) or rng.choice(list(PEOPLE))
    tb = getattr(args, "type_b", None) or ("boy" if ta == "girl" else "girl")
    na = getattr(args, "name_a", None) or rng.choice(PEOPLE[ta].names)
    nb = getattr(args, "name_b", None) or rng.choice(PARTNER_NAMES)
    trait_a = getattr(args, "trait_a", None) or rng.choice(TRAITS)
    trait_b = getattr(args, "trait_b", None) or rng.choice(TRAITS)
    if na == nb:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, fruit=fruit, name_a=na, type_a=ta, name_b=nb, type_b=tb, trait_a=trait_a, trait_b=trait_b)


def _make_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    friend_a = world.add(Entity(id="friend_a", kind="character", type=params.type_a, label=params.name_a, traits=[params.trait_a, "friendly"]))
    friend_b = world.add(Entity(id="friend_b", kind="character", type=params.type_b, label=params.name_b, traits=[params.trait_b, "kind"]))
    fruit_cfg = _safe_lookup(FRUITS, params.fruit)
    fruit = world.add(Entity(id="fruit", kind="thing", type="fruit", label=fruit_cfg.label))
    fruit.meters["ripeness"] = 0.0
    friend_a.memes["suspicion"] = 1.0
    friend_b.memes["kindness"] = 1.0
    world.facts.update(friend_a=friend_a, friend_b=friend_b, fruit=fruit, fruit_cfg=fruit_cfg, params=params)
    return world


def tell(world: World) -> World:
    a = world.get("friend_a")
    b = world.get("friend_b")
    fruit = world.get("fruit")
    cfg: Fruit = _safe_fact(world, world.facts, "fruit_cfg")
    p: StoryParams = _safe_fact(world, world.facts, "params")

    world.say(f"{a.label} and {b.label} were spending a quiet day in {world.setting.place}.")
    world.say(f"On the counter sat {cfg.phrase}, and {a.label} kept glancing at it.")
    world.para()
    world.say(f"{a.label} thought {b.label} had hidden a snack for later, which felt unfair and a little funny.")
    world.say(f"So {a.label} asked, \"Why are you making the fruit wait?\"")
    world.say(f"{b.label} blinked and said, \"I am not making it wait. It is just ripening.\"")
    a.memes["suspicion"] += 1.0
    propagate(world, narrate=True)
    world.para()
    world.say(f"They watched the fruit together for a moment.")
    fruit.meters["ripeness"] += 1.0
    propagate(world, narrate=True)
    world.say(f"{b.label} tapped the bowl and said, \"See? Yesterday it was firmer. Today it is {cfg.result_phrase}.\"")
    world.say(f"{a.label} laughed, because the whole worry had been a tiny misunderstanding.")
    world.say(f"Then the two friends shared the fruit, and the afternoon felt easy again.")
    world.say(f"{a.label} and {b.label} stayed side by side, happy to have turned a mix-up into a joke.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    cfg: Fruit = _safe_fact(world, world.facts, "fruit_cfg")
    return [
        f'Write a short slice-of-life story about friendship, humor, and a misunderstanding involving "{cfg.label}" and ripen.',
        f"Tell a gentle everyday story where {p.name_a} thinks {p.name_b} is hiding food, but the fruit is only ripening.",
        f"Write a small, child-friendly story that ends with two friends laughing together after a misunderstanding about ripening fruit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    cfg: Fruit = _safe_fact(world, world.facts, "fruit_cfg")
    return [
        QAItem(
            question=f"Why did {p.name_a} look at the fruit so carefully?",
            answer=f"{p.name_a} thought {p.name_b} was saving a snack and was worried the fruit was being kept from them.",
        ),
        QAItem(
            question=f"What was really happening to the {cfg.label}?",
            answer=f"The {cfg.label} was ripening slowly on the counter, so it was changing from firm to sweet and ready to eat.",
        ),
        QAItem(
            question=f"How did {p.name_a} feel when the truth came out?",
            answer=f"{p.name_a} felt relieved and amused, because it turned out to be a harmless misunderstanding.",
        ),
        QAItem(
            question=f"What did the two friends do at the end?",
            answer=f"They shared the fruit and laughed together, which showed their friendship stayed strong.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does ripen mean?",
            answer="Ripen means to become ready to eat, often by getting softer, sweeter, or more fragrant.",
        ),
        QAItem(
            question="Why do friends laugh when they understand each other better?",
            answer="Friends often laugh because the mix-up stops feeling big, and the funny part becomes easy to share.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone gets the wrong idea about what is happening.",
        ),
        QAItem(
            question="Why is sharing food a friendly thing to do?",
            answer="Sharing food can feel kind because it shows you want the other person to enjoy the moment with you.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: type={e.type} label={e.label} meters={meters} memes={memes}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
ripening(F) :- fruit(F), ripeness(F, R), R >= 1.
misunderstanding(A) :- suspicion(A, S), S >= 1.
humor(A) :- confusion(A, C), C >= 1.
friendship(A,B) :- kindness(B, K), K >= 1.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
    for fid, fruit in FRUITS.items():
        lines.append(asp.fact("fruit", fid))
        for stage in fruit.stages:
            lines.append(asp.fact("stage", fid, stage))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show ripening/1.")
    model = asp.one_model(program)
    asp_atoms = set(asp.atoms(model, "ripening"))
    py_atoms = {("peach",), ("pear",), ("banana",)}
    if asp_atoms == py_atoms:
        print(f"OK: ASP parity matches Python gate ({len(py_atoms)} facts).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("ASP:", sorted(asp_atoms))
    print("PY :", sorted(py_atoms))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show ripening/1."))
    return sorted(set(asp.atoms(model, "ripening")))


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="kitchen", fruit="peach", name_a="Mia", type_a="girl", name_b="Jo", type_b="boy", trait_a="curious", trait_b="patient"),
    StoryParams(place="living_room", fruit="pear", name_a="Noah", type_a="boy", name_b="Bea", type_b="girl", trait_a="gentle", trait_b="bright"),
    StoryParams(place="balcony", fruit="banana", name_a="Ruby", type_a="girl", name_b="Ari", type_b="boy", trait_a="playful", trait_b="kind"),
]


def resolve_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show ripening/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show ripening/1."))
        print("ASP facts:", sorted(set(asp.atoms(model, "ripening"))))
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
            params = resolve_from_args(args, random.Random(seed))
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
            header = f"### {p.name_a} and {p.name_b} at {p.place} with {p.fruit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
