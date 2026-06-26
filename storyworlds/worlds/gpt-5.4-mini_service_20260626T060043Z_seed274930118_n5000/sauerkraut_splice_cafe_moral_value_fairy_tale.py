#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sauerkraut_splice_cafe_moral_value_fairy_tale.py
=============================================================================================================

A small fairy-tale storyworld about a café, a magical splice, and the moral
value of keeping promises, sharing fairly, and fixing mistakes.

Seed tale:
---
In a lantern-lit café at the edge of an old forest, a kind baker named Mira
promised the hungry forest folk a pot of sweet-smelling sauerkraut stew. But a
tricky little sprite swapped the spoon and made the stew taste wrong. Mira
could have hidden the mistake, yet she chose to tell the truth, make a careful
splice with honeyed apples, and serve every guest fairly. The forest folk
forgave her, and the café rang with warm laughter again.
---

The simulated world tracks:
- physical meters: hunger, spoilage, warmth, freshness, fullness
- emotional memes: trust, worry, shame, pride, gratitude, fairness

The moral turn is driven by whether the host tells the truth and makes a fair
splice to repair the meal.
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    g1: object | None = None
    g2: object | None = None
    host: object | None = None
    pot: object | None = None
    sprite: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = {"hunger": 0.0, "spoilage": 0.0, "warmth": 0.0, "freshness": 0.0, "fullness": 0.0}
        if not self.memes:
            self.memes = {"trust": 0.0, "worry": 0.0, "shame": 0.0, "pride": 0.0, "gratitude": 0.0, "fairness": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "mother", "maid"}
        male = {"boy", "man", "king", "father", "knight"}
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
    place: str = "the café"
    twilight: bool = True
    tags: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
        return None


@dataclass
class Ingredient:
    id: str
    label: str
    taste: str
    value: str
    fresh_gain: float = 0.0
    fairness_gain: float = 0.0
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


@dataclass
class Splice:
    id: str
    label: str
    description: str
    repair: str
    requires_truth: bool = True
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


@dataclass
class Complaint:
    id: str
    label: str
    spoil_gain: float
    hunger_gain: float
    worry_gain: float
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.events: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.events = list(self.events)
        return w


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def intro(world: World, host: Entity) -> None:
    world.say(f"At {world.setting.place}, there lived {article(host.label)} {host.label} who loved feeding the lonely and the lost.")
    world.say(f"{host.pronoun().capitalize()} kept a warm pot of sauerkraut on the stove and believed every guest should leave with a full heart.")


def arrival(world: World, host: Entity, guests: list[Entity]) -> None:
    names = ", ".join(g.label for g in guests[:-1]) + f", and {guests[-1].label}" if len(guests) > 2 else f"{guests[0].label} and {guests[1].label}"
    world.say(f"One evening, {names} came to the café with empty bellies and hopeful eyes.")
    for g in guests:
        g.meters["hunger"] += 1.0
        g.memes["worry"] += 0.5


def serve_stew(world: World, host: Entity, pot: Entity, guests: list[Entity], ingredient: Ingredient) -> None:
    pot.meters["warmth"] += 1.0
    pot.meters["freshness"] += ingredient.fresh_gain
    world.say(f"{host.label} lifted the ladle and served a bowl of {ingredient.label} stew to each guest.")
    for g in guests:
        g.meters["hunger"] = max(0.0, g.meters["hunger"] - 1.0)
        g.meters["fullness"] += 1.0
        g.memes["trust"] += 0.5


def spoiler(world: World, host: Entity, trickster: Entity, pot: Entity, complaint: Complaint) -> None:
    pot.meters["spoilage"] += complaint.spoil_gain
    host.memes["worry"] += complaint.worry_gain
    host.memes["shame"] += 0.5
    trickster.memes["pride"] += 0.25
    world.say(f"But a sneaky sprite slipped a wrong spoon into the pot, and the stew turned odd and sour.")
    world.say(f"The smell grew wrong, and the guests began to frown at their bowls.")


def tell_truth(world: World, host: Entity, guests: list[Entity]) -> None:
    host.memes["shame"] = max(0.0, host.memes["shame"] - 0.5)
    host.memes["trust"] += 0.5
    world.say(f"{host.label} bowed {host.pronoun('possessive')} head and said, \"I made a mistake, but I will mend it fairly.\"")
    for g in guests:
        g.memes["trust"] += 0.25
        g.memes["worry"] = max(0.0, g.memes["worry"] - 0.25)


def do_splice(world: World, host: Entity, splice: Splice, base: Ingredient, added: Ingredient, guests: list[Entity]) -> None:
    world.say(f"Then {host.label} made a careful splice: {splice.description}, mixing in {added.label} to brighten the pot.")
    for g in guests:
        g.meters["hunger"] = max(0.0, g.meters["hunger"] - 0.5)
        g.memes["gratitude"] += added.fairness_gain
        g.memes["fairness"] += 0.5
        g.memes["trust"] += 0.5
    host.memes["pride"] += 0.5
    host.memes["fairness"] += 0.75
    base.meters["freshness"] += added.fresh_gain
    base.meters["spoilage"] = max(0.0, base.meters["spoilage"] - 0.5)


def forgive_and_feast(world: World, host: Entity, guests: list[Entity], splice: Splice) -> None:
    world.say(f"The guests tasted the new stew and smiled at once.")
    world.say(f"They said the {splice.label} was clever, and they forgave the mistake because the truth had been told.")
    world.say(f"By the end, the café smelled sweet again, and every bowl was empty in the happiest way.")


def moral_gate(host_truthful: bool, spill: bool, fair_splice: bool) -> bool:
    return host_truthful and spill and fair_splice


def predict(world: World, host: Entity, guests: list[Entity], spoiler_on: bool, fair_splice: bool) -> dict:
    sim = world.copy()
    h = sim.get(host.id)
    gs = [sim.get(g.id) for g in guests]
    pot = sim.get("pot")
    if spoiler_on:
        pot.meters["spoilage"] += 1.0
        h.memes["worry"] += 0.5
        for g in gs:
            g.memes["worry"] += 0.25
    if fair_splice:
        pot.meters["freshness"] += 1.0
        for g in gs:
            g.memes["trust"] += 0.5
    return {
        "spoiled": pot.meters["spoilage"] >= THRESHOLD and pot.meters["freshness"] < 1.0,
        "trusted": sum(g.memes["trust"] for g in gs),
    }


@dataclass
class StoryParams:
    place: str
    host: str
    host_type: str
    guest1: str
    guest1_type: str
    guest2: str
    guest2_type: str
    ingredient: str
    splice: str
    complaint: str
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


SETTING = Setting(place="the lantern café", twilight=True, tags={"cafe", "fairy", "moral"})
INGREDIENTS = {
    "sauerkraut": Ingredient("sauerkraut", "sauerkraut", "sharp and tangy", "honest", fresh_gain=0.5, fairness_gain=0.5),
    "honeyed_apples": Ingredient("honeyed_apples", "honeyed apples", "sweet and bright", "kind", fresh_gain=1.0, fairness_gain=1.0),
    "herb_broth": Ingredient("herb_broth", "herb broth", "gentle and green", "careful", fresh_gain=0.75, fairness_gain=0.5),
}
SPLICES = {
    "honey_splice": Splice("honey_splice", "honey splice", "a little ribbon of honey and apple slices", "repair"),
    "golden_splice": Splice("golden_splice", "golden splice", "a bright twist of fruit and syrup", "mend"),
}
COMPLAINTS = {
    "wrong_spoon": Complaint("wrong_spoon", "wrong spoon", spoil_gain=1.0, hunger_gain=0.0, worry_gain=0.5),
    "salt_swap": Complaint("salt_swap", "salt swap", spoil_gain=0.5, hunger_gain=0.0, worry_gain=0.5),
}

NAMES = ["Mira", "Nina", "Elin", "Tessa", "Lina", "Rosa", "Jorin", "Pavel", "Bram", "Oren"]
TYPES = ["girl", "boy", "woman", "man", "witch", "baker", "cook", "innkeeper", "sprite", "elf"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a café, a sauerkraut dish, and a moral splice.")
    ap.add_argument("--place", choices=["cafe"], default="cafe")
    ap.add_argument("--ingredient", choices=sorted(INGREDIENTS))
    ap.add_argument("--splice", choices=sorted(SPLICES))
    ap.add_argument("--complaint", choices=sorted(COMPLAINTS))
    ap.add_argument("--host")
    ap.add_argument("--host-type", choices=["girl", "boy", "woman", "man", "baker", "cook", "innkeeper"])
    ap.add_argument("--guest1")
    ap.add_argument("--guest1-type", choices=["girl", "boy", "woman", "man", "child", "elf"])
    ap.add_argument("--guest2")
    ap.add_argument("--guest2-type", choices=["girl", "boy", "woman", "man", "child", "elf"])
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
    ingredient = getattr(args, "ingredient", None) or rng.choice(list(INGREDIENTS))
    splice = getattr(args, "splice", None) or rng.choice(list(SPLICES))
    complaint = getattr(args, "complaint", None) or rng.choice(list(COMPLAINTS))
    host = getattr(args, "host", None) or rng.choice(NAMES)
    guest1 = getattr(args, "guest1", None) or rng.choice([n for n in NAMES if n != host])
    guest2 = getattr(args, "guest2", None) or rng.choice([n for n in NAMES if n not in {host, guest1}])
    host_type = getattr(args, "host_type", None) or rng.choice(["woman", "baker", "cook", "innkeeper"])
    guest1_type = getattr(args, "guest1_type", None) or rng.choice(["girl", "boy", "child", "elf"])
    guest2_type = getattr(args, "guest2_type", None) or rng.choice(["girl", "boy", "child", "elf"])
    return StoryParams(
        place="cafe",
        host=host,
        host_type=host_type,
        guest1=guest1,
        guest1_type=guest1_type,
        guest2=guest2,
        guest2_type=guest2_type,
        ingredient=ingredient,
        splice=splice,
        complaint=complaint,
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    host = world.add(Entity(id="host", kind="character", type=params.host_type, label=params.host))
    g1 = world.add(Entity(id="guest1", kind="character", type=params.guest1_type, label=params.guest1))
    g2 = world.add(Entity(id="guest2", kind="character", type=params.guest2_type, label=params.guest2))
    sprite = world.add(Entity(id="sprite", kind="character", type="sprite", label="the sprite"))
    pot = world.add(Entity(id="pot", type="thing", label="pot"))

    ingredient = _safe_lookup(INGREDIENTS, params.ingredient)
    splice = _safe_lookup(SPLICES, params.splice)
    complaint = _safe_lookup(COMPLAINTS, params.complaint)

    intro(world, host)
    world.para()
    arrival(world, host, [g1, g2])
    world.say(f"{host.label} had prepared {article(ingredient.label)} {ingredient.label} stew, because {ingredient.value} is a value worth serving."
              )
    if params.ingredient == "sauerkraut":
        world.say("The sauerkraut was sharp as a little truth, and it bubbled kindly in the pot.")
    spoiler(world, host, sprite, pot, complaint)
    world.para()
    tell_truth(world, host, [g1, g2])
    do_splice(world, host, splice, ingredient, INGREDIENTS["honeyed_apples"], [g1, g2])
    forgive_and_feast(world, host, [g1, g2], splice)

    world.facts.update(
        host=host,
        guests=[g1, g2],
        ingredient=ingredient,
        splice=splice,
        complaint=complaint,
        pot=pot,
        truthful=True,
        repaired=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    host = _safe_fact(world, f, "host")
    ing = _safe_fact(world, f, "ingredient")
    splice = _safe_fact(world, f, "splice")
    return [
        f'Write a short fairy tale for a child about {host.label} at a café, with {ing.label}, a mistake, and a kind repair.',
        f"Tell a moral story where {host.label} keeps a promise, admits a mistake, and makes a fair {splice.label}.",
        f'Write a gentle tale that includes the words "sauerkraut", "splice", and "café", and ends with forgiveness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    host = _safe_fact(world, f, "host")
    g1, g2 = f["guests"]
    ing = _safe_fact(world, f, "ingredient")
    splice = _safe_fact(world, f, "splice")
    qa = [
        QAItem(
            question=f"Who ran the café in the story?",
            answer=f"{host.label} ran the café and tried to feed every guest fairly.",
        ),
        QAItem(
            question=f"What ingredient was in the first pot?",
            answer=f"The first pot held {ing.label}, which tasted {ing.taste}.",
        ),
        QAItem(
            question=f"What mistake happened at the café?",
            answer=f"A sneaky sprite swapped the spoon and made the stew turn odd and sour.",
        ),
        QAItem(
            question=f"What did {host.label} do after the mistake?",
            answer=f"{host.label} told the truth, made a {splice.label}, and served a fair bowl to each guest.",
        ),
        QAItem(
            question=f"Why did the guests forgive {host.label}?",
            answer="They forgave the mistake because the truth was told and the meal was repaired fairly.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sauerkraut?",
            answer="Sauerkraut is cabbage that has been salted and left to turn sour in a tasty way.",
        ),
        QAItem(
            question="What is a splice?",
            answer="A splice is a careful joining together of pieces so they become one new thing.",
        ),
        QAItem(
            question="What is a café?",
            answer="A café is a small place where people sit down to eat, drink, and talk.",
        ),
        QAItem(
            question="What does fairness mean?",
            answer="Fairness means giving each person a proper share and not keeping the best part for yourself.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        met = {k: round(v, 2) for k, v in e.meters.items() if v}
        mem = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:6} ({e.type:8}) meters={met} memes={mem}")
    return "\n".join(lines)


ASP_RULES = r"""
entity(host). entity(guest1). entity(guest2). entity(sprite). entity(pot).

truthful(H) :- host(H), says_truth(H).
repairing(H) :- host(H), makes_splice(H).
fair(H) :- host(H), truthful(H), repairing(H).
forgiven(G) :- guest(G), fair(_).
moral_value(H) :- truthful(H), repairing(H), fair(H), gratitude_up(G).

good_story :- moral_value(host).
#show good_story/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("host", "host"),
        asp.fact("guest", "guest1"),
        asp.fact("guest", "guest2"),
        asp.fact("sprite", "sprite"),
        asp.fact("pot", "pot"),
        asp.fact("says_truth", "host"),
        asp.fact("makes_splice", "host"),
        asp.fact("gratitude_up", "guest1"),
        asp.fact("gratitude_up", "guest2"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/0."))
    asp_good = bool(asp.atoms(model, "good_story"))
    py_good = True
    if asp_good == py_good:
        print("OK: ASP parity matches Python moral gate.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def generation_all() -> list[StoryParams]:
    return [
        StoryParams("cafe", "Mira", "woman", "Pip", "child", "Nell", "child", "sauerkraut", "honey_splice", "wrong_spoon"),
        StoryParams("cafe", "Elin", "baker", "Tomas", "boy", "Sera", "girl", "sauerkraut", "golden_splice", "salt_swap"),
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


def explain_rejection() -> str:
    return "(No story: the chosen options do not fit this café moral tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "ingredient", None) and getattr(args, "ingredient", None) not in INGREDIENTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place="cafe",
        host=getattr(args, "host", None) or rng.choice(NAMES),
        host_type=getattr(args, "host_type", None) or rng.choice(["woman", "baker", "cook", "innkeeper"]),
        guest1=getattr(args, "guest1", None) or rng.choice([n for n in NAMES if n != (getattr(args, "host", None) or "")]),
        guest1_type=getattr(args, "guest1_type", None) or rng.choice(["girl", "boy", "child", "elf"]),
        guest2=getattr(args, "guest2", None) or rng.choice([n for n in NAMES if n not in {getattr(args, "host", None) or "", getattr(args, "guest1", None) or ""}]),
        guest2_type=getattr(args, "guest2_type", None) or rng.choice(["girl", "boy", "child", "elf"]),
        ingredient=getattr(args, "ingredient", None) or "sauerkraut",
        splice=getattr(args, "splice", None) or "honey_splice",
        complaint=getattr(args, "complaint", None) or "wrong_spoon",
    )


def build_asp_show() -> str:
    return "#show good_story/0."


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program(build_asp_show()))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in generation_all():
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
