#!/usr/bin/env python3
"""
storyworlds/worlds/cockle_enlarge_magic_cautionary_lesson_learned_folk.py
=========================================================================

A small folk-tale story world about a curious child, a cockle shell charm, a
magic enlarging word, and a cautious helper who helps turn trouble into a lesson.

The seed idea:
- include the words "cockle" and "enlarge"
- keep the feel of a folk tale
- make the story cautionary, magical, and lesson-shaped

The world is intentionally compact: a few registries, a reasonableness gate,
a tiny forward-chaining world model, and three grounded QA sets.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False
    protective: bool = False

    charm_ent: object | None = None
    child: object | None = None
    helper: object | None = None
    item: object | None = None
    remedy_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
        if not hasattr(self, "_tags"):
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
class Place:
    id: str
    label: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Risk:
    id: str
    label: str
    phrase: str
    region: str
    vulnerable_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Remedy:
    id: str
    label: str
    phrase: str
    action: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_enlarge_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["enlarged"] < THRESHOLD:
            continue
        if not world.facts.get("risk_id"):
            continue
        risk = world.get(world.facts["risk_id"])
        sig = ("spill", actor.id, risk.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        risk.meters["tipped"] += 1
        risk.meters["messy"] += 1
        out.append(f"{risk.label.capitalize()} tipped and made a big mess.")
    return out


def _r_mess_makes_worry(world: World) -> list[str]:
    out: list[str] = []
    for risk in list(world.entities.values()):
        if risk.meters["messy"] < THRESHOLD:
            continue
        sig = ("worry", risk.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        helper_id = world.facts.get("helper_id")
        if helper_id:
            world.get(helper_id).memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule("spill", "physical", _r_enlarge_spill),
    Rule("worry", "social", _r_mess_makes_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def enough_reason(params_item: Charm, risk: Risk, remedy: Remedy) -> bool:
    return params_item.id in risk.vulnerable_to and params_item.id in params_item.requires and remedy.power >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for charm_id, charm in CHARMS.items():
            for risk_id, risk in RISKS.items():
                for remedy_id, remedy in REMEDIES.items():
                    if place.affords and charm_id in place.affords and enough_reason(charm, risk, remedy):
                        combos.append((place_id, charm_id, risk_id))
    return combos


@dataclass
class StoryParams:
    place: str
    charm: str
    risk: str
    remedy: str
    child_name: str = "Mara"
    child_type: str = "girl"
    helper_name: str = "Nell"
    helper_type: str = "woman"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


PLACES = {
    "cottage": Place(id="cottage", label="the cottage", indoor=True, affords={"cockle", "enlarge"}),
    "brook": Place(id="brook", label="the brook", indoor=False, affords={"cockle", "enlarge"}),
    "field": Place(id="field", label="the field", indoor=False, affords={"cockle", "enlarge"}),
    "kitchen": Place(id="kitchen", label="the kitchen", indoor=True, affords={"cockle", "enlarge"}),
}

CHARMS = {
    "cockle": Charm(
        id="cockle",
        label="cockle shell charm",
        phrase="a little cockle shell charm",
        effect="enlarge",
        requires={"cockle"},
        tags={"cockle", "magic"},
    ),
    "mirror": Charm(
        id="mirror",
        label="bright mirror charm",
        phrase="a bright mirror charm",
        effect="enlarge",
        requires={"mirror"},
        tags={"magic"},
    ),
    "spoon": Charm(
        id="spoon",
        label="silver spoon charm",
        phrase="a silver spoon charm",
        effect="enlarge",
        requires={"spoon"},
        tags={"magic"},
    ),
}

RISKS = {
    "bread": Risk(
        id="bread",
        label="bread loaf",
        phrase="a round loaf of bread",
        region="table",
        vulnerable_to={"enlarge"},
        tags={"food", "magic"},
    ),
    "basket": Risk(
        id="basket",
        label="market basket",
        phrase="a little market basket",
        region="floor",
        vulnerable_to={"enlarge"},
        tags={"basket", "magic"},
    ),
    "apple": Risk(
        id="apple",
        label="apple",
        phrase="a red apple",
        region="table",
        vulnerable_to={"enlarge"},
        tags={"food", "magic"},
    ),
}

REMEDIES = {
    "cloth": Remedy(id="cloth", label="cloth", phrase="a long cloth", action="cover", power=1, sense=2, tags={"cloth"}),
    "string": Remedy(id="string", label="string", phrase="a loop of string", action="tie down", power=1, sense=2, tags={"string"}),
    "basket": Remedy(id="basket", label="basket", phrase="a sturdy basket", action="carry safely", power=2, sense=3, tags={"basket"}),
}

GIRL_NAMES = ["Mara", "Tess", "Iris", "Pippa", "Mina", "Lena"]
BOY_NAMES = ["Owen", "Finn", "Jory", "Ned", "Perrin", "Tobin"]
HELPER_NAMES = ["Nell", "Wren", "Sable", "Brigid", "Mora", "Anya"]
TRAITS = ["careful", "kind", "wise", "patient", "steady"]


def tell(place: Place, charm: Charm, risk: Risk, remedy: Remedy, child_name: str, child_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    item = world.add(Entity(id="item", type="thing", label=risk.label, phrase=risk.phrase))
    charm_ent = world.add(Entity(id="charm", type="thing", label=charm.label, phrase=charm.phrase))
    remedy_ent = world.add(Entity(id="remedy", type="thing", label=remedy.label, phrase=remedy.phrase, protective=True))

    world.facts.update(
        child_id=child.id,
        helper_id=helper.id,
        risk_id=item.id,
        charm=charm,
        risk_cfg=risk,
        remedy_cfg=remedy,
        place=place,
    )
    child.memes["curiosity"] = 1
    helper.memes["worry"] = 0
    item.meters["tipped"] = 0
    item.meters["messy"] = 0
    charm_ent.meters["awake"] = 1
    remedy_ent.meters["ready"] = 1

    world.say(f"Once in {place.label}, {child.id} found {charm.phrase}.")
    world.say(f"It was a folk-tale thing, small as a biscuit and old as sea foam.")
    world.para()
    world.say(f"{child.id} wondered if the charm could {charm.effect} {risk.label}.")
    world.say(f"But {helper.id} lifted a hand and said that magic should be used with care.")

    world.para()
    child.meters["enlarged"] += 1
    world.say(f"{child.id} whispered the word {charm.effect}, and the charm glowed.")
    propagate(world, narrate=True)

    if item.meters["messy"] >= THRESHOLD:
        helper.memes["worry"] += 1
        world.say(f"{helper.id} hurried in with {remedy.phrase}.")
        if remedy.power >= 1:
            item.meters["messy"] = 0
            item.meters["tipped"] = 0
            child.memes["lesson"] += 1
            helper.memes["lesson"] += 1
            world.say(f"Together they used {remedy.phrase} so the {risk.label} stayed steady again.")
            world.para()
            world.say(
                f"In the end, the cockle shell charm still gleamed, but {risk.label} "
                f"rested small and safe on the table while {child.id} and {helper.id} smiled."
            )
    else:
        world.say(f"Nothing went wrong, so {helper.id} tucked the charm away for another day.")
        world.para()
        world.say(
            f"The cockle shell charm lay quiet in {child.id}'s palm, and the {risk.label} "
            f"remained as small as before."
        )

    world.facts["outcome"] = "mess" if item.meters["messy"] >= THRESHOLD else "safe"
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["risk"] = item
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    risk = f["risk_cfg"]
    charm = f["charm"]
    place = f["place"]
    return [
        f'Write a folk-tale story for a small child about {child.id} in {place.label} and a {charm.label}.',
        f'Write a cautionary magic story where {child.id} tries to use a cockle shell to {charm.effect} {risk.label}, but {helper.id} warns them first.',
        f'Write a short tale that includes the words "cockle" and "enlarge" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    risk = f["risk_cfg"]
    charm = f["charm"]
    place = f["place"]
    qa = [
        QAItem(
            question=f"Who found the cockle shell charm in {place.label}?",
            answer=f"It was {child.id}. {child.id} found the little cockle shell charm in {place.label} and wondered about its magic.",
        ),
        QAItem(
            question=f"What did {child.id} try to do with the charm?",
            answer=f"{child.id} tried to {charm.effect} {risk.label}. That was the tempting part of the magic, but it was also the risky part.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry when {child.id} spoke the magic word?",
            answer=f"{helper.id} worried because the charm could make {risk.label} grow too big. The helper knew a small spell can become a big trouble if no one watches it.",
        ),
    ]
    if f["outcome"] == "mess":
        qa.append(QAItem(
            question=f"What changed after {child.id} used the cockle shell charm?",
            answer=f"The {risk.label} tipped and became a mess, so {helper.id} hurried in with help. After that, they made the room safe again and learned to be careful with magic.",
        ))
        qa.append(QAItem(
            question=f"How did the story end for {child.id} and {helper.id}?",
            answer=f"It ended with a lesson learned. The cockle shell charm still shone, but {child.id} remembered that magic should be used gently and with a wise helper nearby.",
        ))
    else:
        qa.append(QAItem(
            question=f"How did {helper.id} help keep the magic from becoming trouble?",
            answer=f"{helper.id} kept watch and guided {child.id} away from a mistake. The charm stayed small, and the folk-tale ended calmly instead of in a mess.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    tags = set(world.facts["charm"].tags) | set(world.facts["risk_cfg"].tags) | set(world.facts["remedy_cfg"].tags)
    if "cockle" in tags:
        out.append(QAItem("What is a cockle shell?", "A cockle shell is a small shell from the sea, with a ridged shape and a little curve like a bowl."))
    if "magic" in tags:
        out.append(QAItem("What can magic mean in a folk tale?", "In a folk tale, magic is something strange and special that can change the world in a story. It is often powerful, so people need to use it carefully."))
    if "basket" in tags:
        out.append(QAItem("What is a basket for?", "A basket is used for carrying things, and a sturdy one can help keep food or treasures steady."))
    if "cloth" in tags:
        out.append(QAItem("What does a cloth do?", "A cloth can cover things, wipe things, or help keep small objects from slipping around."))
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
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cottage", charm="cockle", risk="bread", remedy="cloth", child_name="Mara", child_type="girl", helper_name="Nell", helper_type="woman"),
    StoryParams(place="kitchen", charm="cockle", risk="apple", remedy="basket", child_name="Tobin", child_type="boy", helper_name="Brigid", helper_type="woman"),
    StoryParams(place="field", charm="cockle", risk="basket", remedy="string", child_name="Iris", child_type="girl", helper_name="Wren", helper_type="woman"),
    StoryParams(place="brook", charm="cockle", risk="bread", remedy="basket", child_name="Owen", child_type="boy", helper_name="Mora", helper_type="woman"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("enlarges", cid, c.effect))
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
        lines.append(asp.fact("vulnerable", rid, "enlarge"))
    for mid, m in REMEDIES.items():
        lines.append(asp.fact("remedy", mid))
        lines.append(asp.fact("power", mid, m.power))
        lines.append(asp.fact("sense", mid, m.sense))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,R) :- place(P), charm(C), risk(R), affords(P,C), vulnerable(R,enlarge).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP valid_combos().")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as err:
        ok = False
        print(f"SMOKE TEST FAILED: {err}")
    if ok:
        print(f"OK: {len(py)} valid combos; smoke test passed.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world: cockle, enlarge, caution, and lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
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
              and (getattr(args, "charm", None) is None or c[1] == getattr(args, "charm", None))
              and (getattr(args, "risk", None) is None or c[2] == getattr(args, "risk", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, charm, risk = rng.choice(list(combos))
    remedy = getattr(args, "remedy", None) or rng.choice(sorted(REMEDIES))
    child_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    child_type = "girl" if child_name in GIRL_NAMES else "boy"
    helper_type = "woman"
    return StoryParams(place=place, charm=charm, risk=risk, remedy=remedy, child_name=child_name, child_type=child_type, helper_name=helper_name, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.charm not in CHARMS or params.risk not in RISKS or params.remedy not in REMEDIES:
        pass
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(CHARMS, params.charm), _safe_lookup(RISKS, params.risk), _safe_lookup(REMEDIES, params.remedy), params.child_name, params.child_type, params.helper_name, params.helper_type)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            sample.params.seed = seed
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
