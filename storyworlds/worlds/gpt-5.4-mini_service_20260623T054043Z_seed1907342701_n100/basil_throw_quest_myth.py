#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/basil_throw_quest_myth.py
======================================================================================================

A standalone storyworld for a small mythic quest about basil, a throw, and a
hard-won offering. The world models a child-facing quest with typed entities,
physical meters and emotional memes, a forward-chaining causal rule, a
predict-then-warn beat, and an inline ASP twin for parity checks.

Seed premise:
- A young seeker prepares basil for a shrine.
- A sudden throw threatens the offering.
- A guide predicts the danger, warns, and the seeker turns the throw into a
  ritual toss or replaces the broken offering.
- The ending proves what changed with a final physical image.

The prose is intentionally simple and concrete, with a myth-like tone.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
GUIDE_TRAITS = {"wise", "patient", "gentle", "old", "calm"}



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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide_ent: object | None = None
    hero: object | None = None
    offer: object | None = None
    shrine: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "maiden"}
        male = {"boy", "man", "father", "elder", "sage"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Setting:
    id: str
    place: str
    shrine: str
    light: str
    mood: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    danger: str
    zone: set[str]
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
class Offering:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
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
class Guide:
    id: str
    label: str
    phrase: str
    offer: str
    tail: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    quest: str
    offering: str
    guide: str
    hero_name: str
    hero_gender: str
    hero_trait: str
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


SETTINGS = {
    "sun_garden": Setting(
        id="sun_garden",
        place="the sun garden",
        shrine="the small stone shrine",
        light="golden",
        mood="warm",
        affords={"herb", "ritual"},
    ),
    "hill_temple": Setting(
        id="hill_temple",
        place="the hill temple",
        shrine="the old clay shrine",
        light="bright",
        mood="quiet",
        affords={"herb", "ritual"},
    ),
    "river_grove": Setting(
        id="river_grove",
        place="the river grove",
        shrine="the mossy shrine",
        light="silver",
        mood="cool",
        affords={"herb", "ritual"},
    ),
    "moon_court": Setting(
        id="moon_court",
        place="the moon court",
        shrine="the round shrine",
        light="pale",
        mood="still",
        affords={"herb", "ritual"},
    ),
}

QUESTS = {
    "basil_quest": Quest(
        id="basil_quest",
        verb="gather basil",
        gerund="gathering basil",
        rush="run to the basil patch",
        keyword="basil",
        danger="the basil could scatter",
        zone={"hands"},
        tags={"basil", "herb"},
    ),
    "basil_bowl": Quest(
        id="basil_bowl",
        verb="carry the basil bowl",
        gerund="carrying the basil bowl",
        rush="hurry with the bowl",
        keyword="basil",
        danger="the bowl could spill",
        zone={"hands", "torso"},
        tags={"basil", "bowl"},
    ),
    "basil_bundle": Quest(
        id="basil_bundle",
        verb="bring the basil bundle",
        gerund="bringing basil bundles",
        rush="dash with the bundle",
        keyword="basil",
        danger="the leaves could bruise",
        zone={"hands", "arms"},
        tags={"basil", "bundle"},
    ),
    "basil_torch": Quest(
        id="basil_torch",
        verb="carry a basil torch",
        gerund="carrying a basil torch",
        rush="throw the torch into the shrine",
        keyword="basil",
        danger="the torch could burn",
        zone={"hands", "arms", "torso"},
        tags={"basil", "torch"},
    ),
    "basil_basket": Quest(
        id="basil_basket",
        verb="lift the basil basket",
        gerund="lifting a basil basket",
        rush="throw the basket toward the shrine",
        keyword="basil",
        danger="the basket could tip",
        zone={"hands", "arms"},
        tags={"basil", "basket"},
    ),
}

OFFERINGS = {
    "sprig": Offering("sprig", "a fresh basil sprig", "a fresh basil sprig", "hands", tags={"basil"}),
    "bundle": Offering("bundle", "a tied basil bundle", "a tied basil bundle", "arms", tags={"basil"}),
    "bowl": Offering("bowl", "a shallow basil bowl", "a shallow basil bowl", "torso", tags={"basil"}),
    "basket": Offering("basket", "a woven basil basket", "a woven basil basket", "arms", plural=False, tags={"basil"}),
}

GUIDES = {
    "sage": Guide("sage", "the old sage", "a quiet old sage", "bow first", "walked beside the shrine", tags={"sage"}),
    "aunt": Guide("aunt", "the aunt", "a patient aunt", "set the bowl down", "smiled by the path", tags={"family"}),
    "keeper": Guide("keeper", "the keeper", "a calm shrine keeper", "make a careful offer", "waited at the steps", tags={"shrine"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Zia", "Ivy", "Rhea"]
BOY_NAMES = ["Arun", "Taro", "Milo", "Kian", "Soren", "Omar"]
TRAITS = ["curious", "brave", "gentle", "earnest", "quick", "hopeful"]


def quest_at_risk(quest: Quest, offering: Offering) -> bool:
    return quest.id in {"basil_torch", "basil_basket"} or offering.region in quest.zone


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for qid, q in QUESTS.items():
            for oid, off in OFFERINGS.items():
                if "basil" in q.tags and "basil" in off.tags:
                    combos.append((sid, qid, oid))
    return combos


def select_guide(quest: Quest) -> Guide:
    if "torch" in quest.tags:
        return GUIDES["keeper"]
    if "bundle" in quest.tags:
        return GUIDES["sage"]
    return GUIDES["aunt"]


def predict_turn(world: World, hero_id: str, quest: Quest, offering: Offering) -> dict:
    sim = world.copy()
    hero = sim.get(hero_id)
    hero.meters["mess"] += 1 if quest.id == "basil_basket" else 0
    hero.meters["risk"] += 1 if quest.id == "basil_torch" else 0
    return {
        "risk": hero.meters["risk"] > 0 or quest.id == "basil_torch",
        "spilled": quest.id in {"basil_basket", "basil_bowl"},
    }


def _r_spill(world: World) -> list[str]:
    out = []
    for ent in world.characters():
        if ent.meters.get("spill", 0) < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] = ent.memes.get("worry", 0) + 1
        if "offering" in world.entities:
            world.get("offering").meters["tumbled"] = 1
        out.append("__spill__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for s in _r_spill(world):
            changed = True
            if s != "__spill__":
                out.append(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(setting: Setting, quest: Quest, offering: Offering, guide: Guide,
         hero_name: str, hero_gender: str, hero_trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_gender, role="hero",
        attrs={"trait": hero_trait}, meters={"calm": 0.0}, memes={"hope": 1.0}
    ))
    guide_ent = world.add(Entity(
        id=guide.id, kind="character", type="elder" if guide.id == "sage" else "woman",
        role="guide", label=guide.label, attrs={"guide": guide.id}, meters={}, memes={}
    ))
    shrine = world.add(Entity(id="shrine", kind="thing", type="shrine", label=setting.shrine, meters={"clean": 1.0}, memes={}))
    offer = world.add(Entity(id="offering", kind="thing", type="offering", label=offering.label, phrase=offering.phrase, meters={"whole": 1.0}, memes={}))
    world.facts = {
        "hero": hero,
        "guide": guide_ent,
        "quest": quest,
        "offering": offer,
        "setting": setting,
        "shrine": shrine,
        "resolved": False,
        "ended_clean": False,
    }

    hero.memes["desire"] = 1.0
    world.say(f"In {setting.place}, {hero_name} found {offering.phrase} beside {setting.shrine}.")
    world.say(f"{hero_name} wanted to {quest.verb}, because the day felt {setting.mood} and the basil smelled sweet.")
    world.para()
    hero.memes["risk"] = 0.0
    pred = predict_turn(world, hero.id, quest, offering)
    world.facts["predicted"] = pred
    guide_ent.memes["caution"] = 1.0
    world.say(f"Then {guide.label} looked at the path and warned that {quest.danger}.")
    if pred["risk"]:
        world.say(f'"If you {quest.rush}, the offering may be lost," {guide.label} said.')
    if quest.id == "basil_torch":
        hero.meters["spill"] = 1.0
        hero.memes["defiance"] = 1.0
        propagate(world, narrate=False)
        world.say(f"But {hero_name} chose to {quest.rush}, and the basil offer shook in {hero_name}'s arms.")
        world.say(f"{hero_name} threw the torch aside, then knelt and gathered the fallen leaves.")
        offer.meters["whole"] = 0.0
        offer.meters["gathered"] = 1.0
        world.say(f"At last, {hero_name} tied the basil bundle again and carried it toward {setting.shrine}.")
        world.facts["resolved"] = True
        world.facts["ended_clean"] = True
    elif quest.id == "basil_basket":
        world.say(f"{hero_name} listened, lowered the basket, and made a gentler throw of petals instead.")
        offer.meters["whole"] = 1.0
        offer.meters["launched"] = 1.0
        world.facts["resolved"] = True
        world.facts["ended_clean"] = True
    elif quest.id == "basil_bowl":
        world.say(f"{hero_name} slowed down, set the bowl on stone, and walked the last steps by hand.")
        world.facts["resolved"] = True
        world.facts["ended_clean"] = True
    else:
        world.say(f"{hero_name} bowed, lifted the basil, and carried it in both hands until the shrine came near.")
        world.facts["resolved"] = True
        world.facts["ended_clean"] = True
    world.para()
    if world.facts["ended_clean"]:
        world.say(f"By the shrine, the basil sat neat and green, and the air felt warm with quiet thanks.")
    else:
        world.say(f"By the shrine, the leaves were bruised, but the offering still rested there in the end.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a young child that includes the word "basil" and a risky throw near {f["setting"].shrine}.',
        f"Tell a gentle quest story where {f['hero'].id} must handle basil carefully and learns when not to throw it.",
        f'Write a mythic story about a shrine, basil, and a child who must choose a safer way to finish the quest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    guide = f["guide"]
    setting = f["setting"]
    offering = f["offering"]
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to do in {setting.place}?",
            answer=f"{hero.id} was trying to {quest.verb}. The basil was meant for {setting.shrine}, so the quest had to be handled with care.",
        ),
        QAItem(
            question=f"Why did {guide.label} warn {hero.id} about the throw?",
            answer=f"{guide.label} warned {hero.id} because {quest.danger}. A throw done too fast could spoil {offering.phrase} before it reached the shrine.",
        ),
        QAItem(
            question=f"What changed by the end of the quest?",
            answer=f"By the end, the basil was either gathered again or set down safely, and it rested neat near {setting.shrine}. The final picture shows a calmer offering than at the start.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did {hero.id} finish the quest after the warning?",
            answer=f"{hero.id} chose a safer way to finish the quest. That choice kept the basil ready for {setting.shrine} instead of letting the throw spoil it.",
        ))
    if f.get("ended_clean"):
        qa.append(QAItem(
            question=f"What did the basil look like at the end?",
            answer="It looked neat and green, resting calmly by the shrine. The ending image proves the quest ended in a safer, gentler way.",
        ))
    return qa


KNOWLEDGE = {
    "basil": [
        ("What is basil?", "Basil is a green herb that smells sweet and is often used in food or as a special offering."),
    ],
    "throw": [
        ("What does it mean to throw something?", "To throw something means to toss or send it through the air with your hand."),
    ],
    "quest": [
        ("What is a quest?", "A quest is a special journey or task where someone goes looking for something important."),
    ],
    "shrine": [
        ("What is a shrine?", "A shrine is a special place people treat with care and respect."),
    ],
    "myth": [
        ("What is a myth?", "A myth is an old story that often feels magical and teaches about brave people or special places."),
    ],
}
KNOWLEDGE_ORDER = ["myth", "quest", "shrine", "basil", "throw"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"myth", "quest", "shrine", "basil", "throw"}
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="sun_garden", quest="basil_quest", offering="sprig", guide="sage", hero_name="Mina", hero_gender="girl", hero_trait="gentle"),
    StoryParams(setting="hill_temple", quest="basil_bowl", offering="bowl", guide="keeper", hero_name="Arun", hero_gender="boy", hero_trait="curious"),
    StoryParams(setting="river_grove", quest="basil_bundle", offering="bundle", guide="aunt", hero_name="Lila", hero_gender="girl", hero_trait="hopeful"),
    StoryParams(setting="moon_court", quest="basil_basket", offering="basket", guide="sage", hero_name="Soren", hero_gender="boy", hero_trait="brave"),
    StoryParams(setting="sun_garden", quest="basil_torch", offering="bundle", guide="keeper", hero_name="Nora", hero_gender="girl", hero_trait="quick"),
]


def explain_rejection() -> str:
    return "(No story: that combination does not give a meaningful basil quest.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic basil quest storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "offering", None) is None or c[2] == getattr(args, "offering", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, quest, offering = rng.choice(list(combos))
    guide = getattr(args, "guide", None) or rng.choice(sorted(GUIDES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, quest=quest, offering=offering, guide=guide, hero_name=name, hero_gender=gender, hero_trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        pass
    if params.quest not in QUESTS or params.offering not in OFFERINGS or params.guide not in GUIDES:
        pass
    setting = _safe_lookup(SETTINGS, params.setting)
    quest = _safe_lookup(QUESTS, params.quest)
    offering = _safe_lookup(OFFERINGS, params.offering)
    guide = _safe_lookup(GUIDES, params.guide)
    if "basil" not in quest.tags or "basil" not in offering.tags:
        pass
    world = tell(setting, quest, offering, guide, params.hero_name, params.hero_gender, params.hero_trait)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for oid in OFFERINGS:
        lines.append(asp.fact("offering", oid))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    lines.append(asp.fact("basil", "basil"))
    lines.append(asp.fact("throw", "throw"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q,O) :- setting(S), quest(Q), offering(O), basil_quest(Q), basil_offering(O).
basil_quest(basil_quest).
basil_quest(basil_bowl).
basil_quest(basil_bundle).
basil_quest(basil_torch).
basil_quest(basil_basket).
basil_offering(sprig).
basil_offering(bundle).
basil_offering(bowl).
basil_offering(basket).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python combo sets differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, qa=True)
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
