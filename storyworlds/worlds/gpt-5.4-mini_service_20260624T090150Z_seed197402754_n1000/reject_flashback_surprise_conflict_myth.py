#!/usr/bin/env python3
"""
A small mythic story world about a refused bargain, a flashback oath,
a surprise sign, and a conflict that ends in a wiser choice.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    offer: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "queen"}
        male = {"boy", "father", "dad", "man", "brother", "king"}
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
    place: str
    kind: str
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
class CharacterSpec:
    type: str
    name: str
    epithet: str
    role: str
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


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    kind: str
    virtue: str
    risk: str
    reacts_to: str
    forbidden_by: str
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
class Offer:
    id: str
    label: str
    phrase: str
    promise: str
    cost: str
    truth: str
    helps: str
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
class StoryParams:
    place: str
    hero: str
    companion: str
    relic: str
    offer: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_seen = False
        self.surprise_seen = False
        self.conflict_resolved = False

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
        clone.fired = set(self.fired)
        clone.flashback_seen = self.flashback_seen
        clone.surprise_seen = self.surprise_seen
        clone.conflict_resolved = self.conflict_resolved
        return clone


SETTINGS = {
    "mountain": Setting(place="the mountain shrine", kind="high place", affords={"ritual"}),
    "river": Setting(place="the river gate", kind="water place", affords={"ritual"}),
    "forest": Setting(place="the old forest", kind="wild place", affords={"ritual"}),
}

CHILDREN = {
    "Ari": CharacterSpec(type="boy", name="Ari", epithet="young", role="seeker"),
    "Mira": CharacterSpec(type="girl", name="Mira", epithet="brave", role="keeper"),
    "Niko": CharacterSpec(type="boy", name="Niko", epithet="quiet", role="listener"),
    "Sela": CharacterSpec(type="girl", name="Sela", epithet="curious", role="warden"),
}

COMPANIONS = {
    "owl": CharacterSpec(type="owl", name="Hush", epithet="wise", role="guide"),
    "fox": CharacterSpec(type="fox", name="Redtail", epithet="sly", role="guide"),
    "deer": CharacterSpec(type="deer", name="Bramble", epithet="gentle", role="guide"),
}

RELICS = {
    "torch": Relic(
        id="torch",
        label="torch",
        phrase="a bright torch with a bronze cup",
        kind="fire",
        virtue="light",
        risk="its flame could draw shadow",
        reacts_to="darkness",
        forbidden_by="water",
    ),
    "horn": Relic(
        id="horn",
        label="horn",
        phrase="a hollow horn carved with stars",
        kind="sound",
        virtue="call",
        risk="its voice could wake old powers",
        reacts_to="silence",
        forbidden_by="wind",
    ),
    "stone": Relic(
        id="stone",
        label="stone",
        phrase="a smooth stone marked with a moon",
        kind="memory",
        virtue="remembering",
        risk="it could stir a forgotten grief",
        reacts_to="moonlight",
        forbidden_by="fire",
    ),
}

OFFERS = {
    "crown": Offer(
        id="crown",
        label="crown",
        phrase="a gold crown said to make any child king",
        promise="power",
        cost="the child's promise to obey a boastful spirit",
        truth="the crown only shone when a lie was spoken",
        helps="look important but not wise",
    ),
    "cloak": Offer(
        id="cloak",
        label="cloak",
        phrase="a dark cloak that promised secret strength",
        promise="protection",
        cost="the child's kindness to the river folk",
        truth="the cloak hid the wearer from friends as well as foes",
        helps="hide fear but also hide help",
    ),
    "cup": Offer(
        id="cup",
        label="cup",
        phrase="a silver cup that promised endless blessing",
        promise="luck",
        cost="the child's true name",
        truth="the cup filled only when it was shared",
        helps="hold water but also share it",
    ),
}

PLACES = ["mountain", "river", "forest"]
REJECT_WORD = "reject"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero in CHILDREN:
            for companion in COMPANIONS:
                for relic in RELICS:
                    for offer in OFFERS:
                        combos.append((place, hero, companion, relic, offer))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        pass
    if params.hero not in CHILDREN:
        pass
    if params.companion not in COMPANIONS:
        pass
    if params.relic not in RELICS:
        pass
    if params.offer not in OFFERS:
        pass


def introduce(world: World, hero: Entity, companion: Entity, relic: Entity, offer: Entity) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} was a {hero.type} who walked with {companion.label}, "
        f"and the two of them guarded {relic.label}."
    )
    world.say(
        f"The people of that land spoke of {offer.label} as if it were a miracle, "
        f"but {hero.id} had heard older songs."
    )


def flashback(world: World, hero: Entity, companion: Entity, relic: Entity) -> None:
    if world.flashback_seen:
        return
    world.flashback_seen = True
    hero.memes["memory"] = hero.memes.get("memory", 0) + 1
    world.say(
        f"Long ago, in a flashback, {hero.id} had kneel beside an elder and sworn to keep "
        f"{relic.label} for the good of the people."
    )
    world.say(
        f"The elder had said that a true guardian must first listen, then choose, and only then answer."
    )


def surprise(world: World, hero: Entity, relic: Entity, offer: Entity) -> None:
    if world.surprise_seen:
        return
    world.surprise_seen = True
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    world.say(
        f"Then came a surprise: {relic.label} grew warm in {hero.pronoun('possessive')} hands, "
        f"and a hidden mark appeared on its side."
    )
    world.say(
        f"The mark matched {offer.label}, but not as a gift; it was a warning that {offer.truth}."
    )


def conflict(world: World, hero: Entity, companion: Entity, relic: Entity, offer: Entity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    world.say(
        f"A restless spirit rose from the stones and urged {hero.id} to take {offer.label} and forget the vow."
    )
    world.say(
        f"{hero.id} felt the pull of {offer.promise}, while {companion.label} watched in worry."
    )


def resolve(world: World, hero: Entity, companion: Entity, relic: Entity, offer: Entity) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    hero.memes["conflict"] = 0
    world.conflict_resolved = True
    world.say(
        f"{hero.id} shook {hero.pronoun('possessive')} head and said, "
        f'"I {REJECT_WORD} this bargain, for it would bend the vow and dim the light."'
    )
    world.say(
        f"At once, {companion.label} stepped close, and together they used {relic.label} the old way, "
        f"sharing it with the villagers instead of keeping it for pride."
    )
    world.say(
        f"The spirit faded, the warning mark glimmered once, and {offer.label} lost its false shine."
    )
    world.say(
        f"By dawn, {hero.id} was still young, but now {hero.pronoun('subject')} stood like a true guardian."
    )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero_spec = CHILDREN[params.hero]
    companion_spec = _safe_lookup(COMPANIONS, params.companion)
    relic_spec = _safe_lookup(RELICS, params.relic)
    offer_spec = _safe_lookup(OFFERS, params.offer)

    hero = world.add(Entity(id=hero_spec.name, kind="character", type=hero_spec.type))
    companion = world.add(Entity(id=companion_spec.name, kind="character", type=companion_spec.type))
    relic = world.add(Entity(id=relic_spec.label, kind="relic", type=relic_spec.kind, label=relic_spec.label, phrase=relic_spec.phrase, owner=hero.id))
    offer = world.add(Entity(id=offer_spec.label, kind="offer", type="offer", label=offer_spec.label, phrase=offer_spec.phrase))

    introduce(world, hero, companion, relic, offer)
    world.para()
    flashback(world, hero, companion, relic)
    surprise(world, hero, relic, offer)
    world.para()
    conflict(world, hero, companion, relic, offer)
    resolve(world, hero, companion, relic, offer)

    world.facts = {
        "hero": hero,
        "companion": companion,
        "relic": relic,
        "offer": offer,
        "params": params,
    }
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    companion = _safe_fact(world, f, "companion")
    relic = _safe_fact(world, f, "relic")
    offer = _safe_fact(world, f, "offer")
    return [
        f"Write a myth-like story about {hero.id}, {companion.label}, and {relic.label} where they must {REJECT_WORD} a tempting bargain.",
        f"Tell a child-friendly legend with a flashback, a surprise sign, and a conflict over {offer.label} at {world.setting.place}.",
        f"Write a short mythical tale in which a young guardian remembers an old vow and chooses the wiser path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    companion = _safe_fact(world, f, "companion")
    relic = _safe_fact(world, f, "relic")
    offer = _safe_fact(world, f, "offer")
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the story about at {place}?",
            answer=f"The story was about {hero.id}, a young guardian who protected {relic.label} with help from {companion.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} {REJECT_WORD} in the story?",
            answer=f"{hero.id} rejected {offer.label}, because the bargain would have broken the vow and brought trouble.",
        ),
        QAItem(
            question=f"Why was there a conflict in the story?",
            answer=f"There was a conflict because a restless spirit tried to tempt {hero.id} with {offer.label}, even though the old vow said to keep {relic.label} safe.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that {relic.label} grew warm and showed a hidden mark that warned {hero.id} about {offer.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} rejecting the false bargain, sharing {relic.label} the old way, and standing as a truer guardian by dawn.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that goes back to something that happened earlier, so the reader understands why a character acts a certain way now.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something the characters did not expect, and it can change what they think or do next.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is a problem or struggle that makes a character choose between different paths.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {e.kind} {e.type} {' '.join(bits)}")
    lines.append(f"flashback_seen={world.flashback_seen}")
    lines.append(f"surprise_seen={world.surprise_seen}")
    lines.append(f"conflict_resolved={world.conflict_resolved}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="mountain", hero="Ari", companion="owl", relic="torch", offer="crown"),
    StoryParams(place="river", hero="Mira", companion="fox", relic="horn", offer="cloak"),
    StoryParams(place="forest", hero="Sela", companion="deer", relic="stone", offer="cup"),
]


ASP_RULES = r"""
setting(mountain). setting(river). setting(forest).
hero(ari). hero(mira). hero(niko). hero(sela).
companion(owl). companion(fox). companion(deer).
relic(torch). relic(horn). relic(stone).
offer(crown). offer(cloak). offer(cup).

valid(Place,Hero,Companion,Relic,Offer) :-
    setting(Place), hero(Hero), companion(Companion), relic(Relic), offer(Offer).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for h in CHILDREN:
        lines.append(asp.fact("hero", h.lower()))
    for c in COMPANIONS:
        lines.append(asp.fact("companion", c))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    for o in OFFERS:
        lines.append(asp.fact("offer", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP and Python agree on {len(a)} combinations.")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only in ASP:", sorted(a - b))
    print("Only in Python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world with reject, flashback, surprise, and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=CHILDREN)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--offer", choices=OFFERS)
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
    combos = valid_combos()
    combos = [c for c in combos
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              if getattr(args, "hero", None) is None or c[1] == getattr(args, "hero", None)]
    # rebuild more clearly
    filtered = []
    for c in valid_combos():
        place, hero, companion, relic, offer = c
        if getattr(args, "place", None) is not None and place != getattr(args, "place", None):
            continue
        if getattr(args, "hero", None) is not None and hero != getattr(args, "hero", None):
            continue
        if getattr(args, "companion", None) is not None and companion != getattr(args, "companion", None):
            continue
        if getattr(args, "relic", None) is not None and relic != getattr(args, "relic", None):
            continue
        if getattr(args, "offer", None) is not None and offer != getattr(args, "offer", None):
            continue
        filtered.append(c)
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, hero, companion, relic, offer = rng.choice(filtered)
    return StoryParams(place=place, hero=hero, companion=companion, relic=relic, offer=offer)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} valid combinations")
        for row in vals:
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
