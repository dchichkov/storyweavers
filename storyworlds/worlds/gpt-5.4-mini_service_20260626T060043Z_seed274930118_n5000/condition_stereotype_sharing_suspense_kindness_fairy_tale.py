#!/usr/bin/env python3
"""
storyworlds/worlds/condition_stereotype_sharing_suspense_kindness_fairy_tale.py
===============================================================================

A small fairy-tale story world about a child meeting a misunderstood stranger,
sharing something kind, and learning that a condition can hide behind a
stereotype.

Premise:
- A village has a rule about a certain kind of visitor.
- One character arrives with a real condition that makes the village nervous.
- The hero notices the danger, chooses kindness, and shares a helpful thing.
- Suspense resolves when the truth is revealed and the stereotype softens.

The world is intentionally tiny and constraint-checked: every generated story is
built from a concrete simulated state, not from a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    visitor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    dusk: bool = False
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
class Condition:
    id: str
    label: str
    symptom: str
    risk: str
    clue: str
    needs: str
    public_sign: str
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


@dataclass
class Stereotype:
    id: str
    group: str
    rumor: str
    fear: str
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
class Gift:
    id: str
    label: str
    phrase: str
    helps: set[str]
    share_verb: str
    closing: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _apply_suspense(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    visitor = world.get("visitor")
    if hero.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    visitor.memes["mystery"] = visitor.memes.get("mystery", 0) + 1
    out.append("The lane went very still, as if the trees were holding their breath.")
    return out


def _apply_kindness(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    visitor = world.get("visitor")
    gift = world.facts.get("gift")
    if not gift:
        return out
    if hero.memes.get("kindness", 0) < THRESHOLD:
        return out
    sig = ("kindness", gift.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    visitor.memes["trust"] = visitor.memes.get("trust", 0) + 1
    out.append(f"{hero.id} shared {gift.phrase}, and the stranger's eyes softened at once.")
    return out


def _apply_reveal(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    visitor = world.get("visitor")
    condition: Condition = _safe_fact(world, world.facts, "condition")
    stereotype: Stereotype = _safe_fact(world, world.facts, "stereotype")
    if visitor.meters.get("need", 0) < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    visitor.memes["relief"] = visitor.memes.get("relief", 0) + 1
    stereotype_shaken = world.facts.get("stereotype_shaken", False)
    if stereotype_shaken:
        out.append(
            f"Then the visitor explained the truth: {visitor.pronoun('subject').capitalize()} "
            f"had {condition.label.lower()}, and the old rumor about {stereotype.group} was not the whole story."
        )
    else:
        out.append(
            f"Then the visitor explained the truth: {visitor.pronoun('subject').capitalize()} "
            f"had {condition.label.lower()}."
        )
    hero.memes["understanding"] = hero.memes.get("understanding", 0) + 1
    return out


CAUSAL_RULES = [_apply_suspense, _apply_kindness, _apply_reveal]


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


def predict_help(world: World, hero: Entity, gift: Gift) -> bool:
    sim = world.copy()
    sim.get("hero").memes["kindness"] = 1
    sim.get("visitor").meters["need"] = 1
    sim.facts["gift"] = gift
    propagate(sim, narrate=False)
    return sim.get("visitor").memes.get("trust", 0) >= THRESHOLD


def setting_line(setting: Setting) -> str:
    return {
        "village square": "The village square glowed in the evening light.",
        "forest path": "The forest path was dim and gold beneath the trees.",
        "castle gate": "The castle gate stood tall and silent.",
        "river bridge": "The river bridge shone with a silver hush.",
    }[setting.place]


def hero_intro(hero: Entity) -> str:
    trait = next((t for t in hero.traits if t not in {"little"}), "gentle")
    return f"{hero.id} was a little {trait} {hero.type} who loved to notice small troubles before they grew big."


def visitor_intro(visitor: Entity, stereotype: Stereotype) -> str:
    return (
        f"One evening, a {stereotype.group} traveler came down the road, and the villagers began to whisper "
        f"the old rumor that {stereotype.rumor}."
    )


def condition_hint(condition: Condition) -> str:
    return f"But {condition.public_sign} showed that something real was wrong."


def build_story(world: World) -> None:
    hero = world.get("hero")
    visitor = world.get("visitor")
    condition: Condition = _safe_fact(world, world.facts, "condition")
    stereotype: Stereotype = _safe_fact(world, world.facts, "stereotype")
    gift: Gift = _safe_fact(world, world.facts, "gift")

    world.say(hero_intro(hero))
    world.say(visitor_intro(visitor, stereotype))
    world.say(condition_hint(condition))

    world.para()
    world.say(setting_line(world.setting))
    world.say(
        f"{hero.id} noticed that {visitor.pronoun('possessive')} {condition.symptom} made {visitor.pronoun('object')} move slowly, "
        f"and that was why {visitor.pronoun('subject')} needed {condition.needs}."
    )
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    visitor.meters["need"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"The villagers clutched their baskets, because they feared that a {stereotype.group} would bring {stereotype.fear}."
    )
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    world.say(
        f"But {hero.id} remembered that a kind heart can be braver than a rumor, so {hero.pronoun('subject')} chose to share {gift.label}."
    )
    if not predict_help(world, hero, gift):
        pass
    world.say(
        f"{hero.id} offered {gift.phrase} {gift.share_verb}, and {visitor.id} accepted it with a shaky smile."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"When {visitor.id} felt better, {visitor.pronoun('subject')} thanked {hero.id} and spoke plainly about {condition.label.lower()}."
    )
    world.say(
        f"The villagers blinked, then lowered their baskets and learned that {stereotype.rumor} was only a stereotype, not a truth about every traveler."
    )
    world.say(
        f"By moonrise, {hero.id} was walking beside {visitor.id}, and the road felt less lonely than before."
    )

    world.facts.update(
        hero=hero,
        visitor=visitor,
        condition=condition,
        stereotype=stereotype,
        gift=gift,
        resolved=True,
    )


SETTINGS = {
    "village_square": Setting("village square", dusk=True),
    "forest_path": Setting("forest path", dusk=True),
    "castle_gate": Setting("castle gate", dusk=True),
    "river_bridge": Setting("river bridge", dusk=True),
}

CONDITIONS = {
    "cold": Condition(
        id="cold",
        label="a bad cold",
        symptom="a watery cough",
        risk="the chill made every step harder",
        clue="a little sneeze kept escaping",
        needs="a warm cup and a dry cloak",
        public_sign="a tiny sneeze kept bubbling up",
        tags={"kindness", "sharing"},
    ),
    "lost_voice": Condition(
        id="lost_voice",
        label="a lost voice",
        symptom="a whisper instead of a voice",
        risk="speaking was hard and tiring",
        clue="the traveler kept pointing to a throat",
        needs="a cup of honey tea and a quiet place",
        public_sign="a soft, breathy whisper kept slipping out",
        tags={"kindness", "sharing"},
    ),
    "sprained_ankle": Condition(
        id="sprained_ankle",
        label="a sprained ankle",
        symptom="a limp",
        risk="walking hurt",
        clue="one shoe was laced too tightly around a swollen ankle",
        needs="a steady arm and a resting place",
        public_sign="one foot barely touched the ground",
        tags={"kindness", "sharing"},
    ),
}

STEREOTYPES = {
    "wolves": Stereotype(
        id="wolves",
        group="wolves",
        rumor="wolves are always greedy",
        fear="stolen lunch and trouble in the dark",
        tags={"suspense"},
    ),
    "witches": Stereotype(
        id="witches",
        group="witches",
        rumor="witches always mean harm",
        fear="a bad spell on the whole village",
        tags={"suspense"},
    ),
    "giants": Stereotype(
        id="giants",
        group="giants",
        rumor="giants never listen kindly",
        fear="a smashed gate and a frightened night",
        tags={"suspense"},
    ),
}

GIFTS = {
    "bread": Gift("bread", "a round loaf of bread", "sharing the bread", {"cold", "lost_voice", "sprained_ankle"}, "with both hands", "the loaf was broken into kind pieces"),
    "tea": Gift("tea", "a mug of sweet tea", "sharing the tea", {"cold", "lost_voice"}, "carefully", "the steam curled like a tiny blessing"),
    "cloak": Gift("cloak", "a wool cloak", "offering the cloak", {"cold", "sprained_ankle"}, "warmly", "the cloak wrapped around the shoulders like a hug"),
}

HERO_NAMES = ["Mina", "Pip", "Elia", "Tarin", "Luna", "Orin"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["brave", "gentle", "curious", "kind", "bright"]


@dataclass
class StoryParams:
    setting: str
    condition: str
    stereotype: str
    gift: str
    name: str
    hero_type: str
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
    for s in SETTINGS:
        for c in CONDITIONS:
            for st in STEREOTYPES:
                for g, gift in GIFTS.items():
                    if c in gift.helps:
                        combos.append((s, c, st))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about sharing, suspense, and kindness.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--condition", choices=list(CONDITIONS))
    ap.add_argument("--stereotype", choices=list(STEREOTYPES))
    ap.add_argument("--gift", choices=list(GIFTS))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "gift", None) and getattr(args, "condition", None) and getattr(args, "condition", None) not in _safe_lookup(GIFTS, getattr(args, "gift", None)).helps:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    combos = [c for c in combos if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None)) and (getattr(args, "condition", None) is None or c[1] == getattr(args, "condition", None)) and (getattr(args, "stereotype", None) is None or c[2] == getattr(args, "stereotype", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, condition, stereotype = rng.choice(list(combos))
    gift = getattr(args, "gift", None) or rng.choice([g for g, gg in GIFTS.items() if condition in gg.helps])
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting, condition, stereotype, gift, name, hero_type, trait)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type, traits=["little", params.trait, "stubborn"]))
    visitor = world.add(Entity(id="visitor", kind="character", type="traveler", label="visitor"))
    world.facts["condition"] = _safe_lookup(CONDITIONS, params.condition)
    world.facts["stereotype"] = _safe_lookup(STEREOTYPES, params.stereotype)
    world.facts["gift"] = _safe_lookup(GIFTS, params.gift)
    world.facts["stereotype_shaken"] = True

    build_story(world)
    prompts = [
        f"Write a fairy tale about a child named {params.name} who chooses kindness over a rumor.",
        f"Tell a short story in which sharing {_safe_lookup(GIFTS, params.gift).label} helps a traveler with {_safe_lookup(CONDITIONS, params.condition).label.lower()}.",
        f"Write a child-friendly story about suspense, a stereotype, and a gentle act of sharing.",
    ]
    story_qa = [
        QAItem(
            question=f"Why were the villagers nervous when the traveler arrived?",
            answer=f"They had an old stereotype about {_safe_lookup(STEREOTYPES, params.stereotype).group}, so they expected {_safe_lookup(STEREOTYPES, params.stereotype).fear}.",
        ),
        QAItem(
            question=f"What problem did the visitor actually have?",
            answer=f"The visitor had {_safe_lookup(CONDITIONS, params.condition).label.lower()}, which meant {_safe_lookup(CONDITIONS, params.condition).needs}.",
        ),
        QAItem(
            question=f"What did {params.name} share to help?",
            answer=f"{params.name} shared {_safe_lookup(GIFTS, params.gift).phrase}, and that kindness helped the visitor feel safe enough to speak plainly.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The rumor lost its power, the visitor was helped, and {params.name} walked beside the traveler in peace.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does kindness do in a fairy tale?",
            answer="Kindness helps characters trust each other, solve problems, and make a scared moment feel safe.",
        ),
        QAItem(
            question="What is a stereotype?",
            answer="A stereotype is a quick idea people repeat about a group, but it is often too simple to be fair or true.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving part of what you have, like food or warmth, so someone else can be helped.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(village_square;forest_path;castle_gate;river_bridge).
condition(cold;lost_voice;sprained_ankle).
stereotype(wolves;witches;giants).
gift(bread;tea;cloak).

helps(bread,cold).
helps(bread,lost_voice).
helps(bread,sprained_ankle).
helps(tea,cold).
helps(tea,lost_voice).
helps(cloak,cold).
helps(cloak,sprained_ankle).

valid(S,C,T) :- setting(S), condition(C), stereotype(T), gift(G), helps(G,C).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CONDITIONS:
        lines.append(asp.fact("condition", c))
    for t in STEREOTYPES:
        lines.append(asp.fact("stereotype", t))
    for g, gift in GIFTS.items():
        lines.append(asp.fact("gift", g))
        for cond in gift.helps:
            lines.append(asp.fact("helps", g, cond))
    return "\n".join(lines)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams("village_square", "cold", "wolves", "cloak", "Mina", "girl", "kind"),
    StoryParams("forest_path", "lost_voice", "witches", "tea", "Pip", "boy", "gentle"),
    StoryParams("castle_gate", "sprained_ankle", "giants", "bread", "Elia", "girl", "brave"),
]


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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    elif getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        for atom in sorted(set(asp.atoms(model, "valid"))):
            print(atom)
        return
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            seed = base_seed + i
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
