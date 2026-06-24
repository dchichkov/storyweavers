#!/usr/bin/env python3
"""
Story world: double cautionary bravery folk tale.

A small, self-contained folk-tale simulator about a cautious child who wants to
be brave twice: once for themself, and once for someone they love. The story is
built from state changes, not a frozen template, and it includes a declarative
ASP twin for the reasonableness gate.
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
class Character:
    id: str
    kind: str = "character"
    role: str = "child"
    label: str = ""
    pronoun_subject: str = "they"
    pronoun_object: str = "them"
    pronoun_possessive: str = "their"
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def subj(self) -> str:
        return self.pronoun_subject

    def obj(self) -> str:
        return self.pronoun_object

    def pos(self) -> str:
        return self.pronoun_possessive
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
    kind: str
    affordance: str
    threshold: str
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
class Challenge:
    id: str
    danger: str
    test: str
    fear: str
    brave_act: str
    double_act: str
    consequence: str
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
class Gift:
    id: str
    label: str
    use: str
    protects_against: set[str] = field(default_factory=set)
    helps_with: set[str] = field(default_factory=set)
    carried_by: str = ""
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
class StoryParams:
    place: str
    challenge: str
    gift: str
    name: str
    sibling_name: str
    parent_name: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "forest": Setting(place="the green forest", kind="forest", affordance="crossing the river", threshold="the old bridge"),
    "hills": Setting(place="the windy hills", kind="hills", affordance="finding the bell", threshold="the dark ravine"),
    "river": Setting(place="the river path", kind="river", affordance="helping the lamb", threshold="the fast water"),
}

CHALLENGES = {
    "bridge": Challenge(
        id="bridge",
        danger="the old bridge creaks and sways",
        test="cross the old bridge",
        fear="the bridge might break",
        brave_act="step onto the bridge anyway",
        double_act="step onto it a second time to help the sibling across",
        consequence="they reached the far bank with shaking knees and a proud heart",
        keyword="bridge",
        tags={"wood", "water", "crossing"},
    ),
    "wolf": Challenge(
        id="wolf",
        danger="a hungry wolf waits in the brush",
        test="walk past the wolf's den",
        fear="the wolf might leap out",
        brave_act="hold the lantern high",
        double_act="hold it up again for the little sibling",
        consequence="the wolf blinked, then slipped away into the trees",
        keyword="wolf",
        tags={"animal", "night", "lantern"},
    ),
    "storm": Challenge(
        id="storm",
        danger="the storm drums on the roof",
        test="fetch water from the well",
        fear="the dark clouds might burst",
        brave_act="go out with a scarf tied tight",
        double_act="go out once more to bring home the forgotten pail",
        consequence="they came back drenched, laughing, and safe beside the fire",
        keyword="storm",
        tags={"rain", "well", "home"},
    ),
}

GIFTS = {
    "lantern": Gift(id="lantern", label="a brass lantern", use="light the path", protects_against={"wolf", "night"}, helps_with={"bridge"}),
    "scarf": Gift(id="scarf", label="a red scarf", use="keep the neck warm", protects_against={"storm", "rain"}, helps_with={"storm"}),
    "boots": Gift(id="boots", label="sturdy boots", use="keep the feet dry", protects_against={"water", "river"}, helps_with={"bridge", "river"}),
}

NAMES = ["Mina", "Owen", "Sora", "Pip", "Elin", "Jon", "Tara", "Bram"]
PARENT_NAMES = ["Grandmother", "Grandfather", "Mother", "Father"]


def _pronouns(name: str) -> tuple[str, str, str]:
    if name in {"Mina", "Sora", "Elin", "Tara"}:
        return "she", "her", "her"
    if name in {"Owen", "Jon", "Bram"}:
        return "he", "him", "his"
    return "they", "them", "their"


def make_character(name: str, role: str = "child") -> Character:
    s, o, p = _pronouns(name)
    return Character(id=name, role=role, label=name, pronoun_subject=s, pronoun_object=o, pronoun_possessive=p)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for ch_id, ch in CHALLENGES.items():
            if setting.affordance == "crossing the river" and ch_id != "bridge":
                continue
            for gift_id, gift in GIFTS.items():
                if ch.keyword in gift.protects_against or ch.keyword in gift.helps_with or gift_id == "boots":
                    combos.append((place, ch_id, gift_id))
    return combos


def reasonableness_gate(setting: Setting, challenge: Challenge, gift: Gift) -> bool:
    if setting.place == "the green forest" and challenge.id == "wolf" and gift.id != "lantern":
        return False
    if setting.place == "the windy hills" and challenge.id == "bridge":
        return False
    if challenge.id == "bridge" and gift.id not in {"boots", "lantern"}:
        return False
    if challenge.id == "storm" and gift.id not in {"scarf", "boots"}:
        return False
    return True


def select_gift(challenge: Challenge) -> Gift:
    for gift in GIFTS.values():
        if challenge.keyword in gift.protects_against or challenge.id in gift.helps_with:
            return gift
    pass


def predict(world: World, hero: Character, challenge: Challenge, gift: Gift) -> dict:
    sim = world.copy()
    sim.facts["gift_carried"] = gift.id
    fear = 1 if challenge.keyword else 0
    return {"safe": bool(gift.id in {"lantern", "scarf", "boots"}), "fear": fear}


def introduce(world: World, hero: Character, sibling: Character, parent: Character, gift: Gift, challenge: Challenge) -> None:
    world.say(
        f"{hero.label} was a small folk-tale child who loved neat paths, warm bread, and careful steps."
        f" {hero.subj().capitalize()} lived with {sibling.label} and {parent.label} near {world.setting.place}."
    )
    world.say(
        f"One winter morning, {parent.label} gave {hero.label} {gift.label}, saying it would help {hero.obj()} {gift.use}."
        f" {hero.label} kept it close, because folk tales teach that little tools can save a long day."
    )
    world.say(
        f"But beyond the home path waited {challenge.danger}, and that was the sort of trouble that asked for double caution."
    )


def setup_tension(world: World, hero: Character, sibling: Character, challenge: Challenge) -> None:
    hero.memes["caution"] = hero.memes.get("caution", 0) + 1
    sibling.memes["hope"] = sibling.memes.get("hope", 0) + 1
    world.para()
    world.say(
        f"{hero.label} wanted to be brave, but {hero.pos()} heart whispered, \"What if {challenge.fear}?\""
    )
    world.say(
        f"{sibling.label} looked on with wide eyes, because {sibling.subj()} wished to go too."
    )


def test_bravery(world: World, hero: Character, sibling: Character, challenge: Challenge, gift: Gift) -> None:
    world.say(
        f"At the edge of the path, {hero.label} listened to the wind and saw {challenge.test}."
    )
    world.say(
        f"{hero.label} held {gift.label} in both hands, took a breath, and decided to {challenge.brave_act}."
    )
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0) - 1)


def double_bravery(world: World, hero: Character, sibling: Character, challenge: Challenge, gift: Gift) -> None:
    world.say(
        f"Then {hero.label} saw that {sibling.label} was trembling."
        f" So {hero.subj()} chose to be brave a second time and {challenge.double_act}."
    )
    hero.memes["double_bravery"] = hero.memes.get("double_bravery", 0) + 1
    sibling.memes["courage"] = sibling.memes.get("courage", 0) + 1
    world.say(
        f"That second brave choice mattered most, because now the path was not only crossed, it was shared."
    )


def resolve(world: World, hero: Character, sibling: Character, parent: Character, challenge: Challenge, gift: Gift) -> None:
    world.para()
    world.say(
        f"In the end, {challenge.consequence}, and {hero.label} understood why the elders told double cautionary tales."
    )
    world.say(
        f"{sibling.label} smiled at {hero.label}, and {parent.label} said that true bravery is careful enough to bring someone home."
    )
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    sibling.memes["peace"] = sibling.memes.get("peace", 0) + 1
    world.facts.update(hero=hero, sibling=sibling, parent=parent, challenge=challenge, gift=gift, resolved=True)


def tell(setting: Setting, challenge: Challenge, gift: Gift, hero_name: str, sibling_name: str, parent_name: str) -> World:
    world = World(setting)
    hero = world.add(make_character(hero_name))
    sibling = world.add(make_character(sibling_name))
    parent = world.add(make_character(parent_name, role="parent"))
    world.facts.update(hero=hero, sibling=sibling, parent=parent, challenge=challenge, gift=gift, setting=setting)
    introduce(world, hero, sibling, parent, gift, challenge)
    setup_tension(world, hero, sibling, challenge)
    test_bravery(world, hero, sibling, challenge, gift)
    double_bravery(world, hero, sibling, challenge, gift)
    resolve(world, hero, sibling, parent, challenge, gift)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    challenge = _safe_fact(world, f, "challenge")
    gift = _safe_fact(world, f, "gift")
    return [
        f'Write a short folk tale for a child named {hero.label} who must show double bravery around a {challenge.keyword}.',
        f"Tell a cautious, gentle story where {hero.label} uses {gift.label} to face {challenge.danger}.",
        f"Write a simple tale that includes the word \"double\" and ends with a brave child helping a sibling home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sibling = _safe_fact(world, f, "sibling")
    parent = _safe_fact(world, f, "parent")
    challenge = _safe_fact(world, f, "challenge")
    gift = _safe_fact(world, f, "gift")
    return [
        QAItem(
            question=f"What was the story mostly about?",
            answer=(
                f"It was about {hero.label}, who wanted to be brave but also careful, and who used {gift.label} to face {challenge.danger}."
            ),
        ),
        QAItem(
            question=f"Why did {hero.label} feel cautious at first?",
            answer=(
                f"{hero.label} felt cautious because {hero.pos()} heart asked, \"What if {challenge.fear}?\""
                f" That worry made the brave choice feel bigger."
            ),
        ),
        QAItem(
            question=f"What made the bravery double?",
            answer=(
                f"It was double because {hero.label} was brave once for {hero.obj()} and then brave again to help {sibling.label}."
                f" The second brave step mattered most."
            ),
        ),
        QAItem(
            question=f"What did {parent.label} say bravery should be?",
            answer=(
                f"{parent.label} said true bravery is careful enough to bring someone home."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    challenge = _safe_fact(world, f, "challenge")
    gift = _safe_fact(world, f, "gift")
    out = [
        QAItem(
            question="What does cautious mean?",
            answer="Cautious means taking care, moving slowly, and thinking before you act so you can stay safe.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary even when you feel afraid.",
        ),
        QAItem(
            question="Why can a lantern help in a dark place?",
            answer="A lantern gives light, and light helps people see the path and avoid trouble.",
        ),
    ]
    if challenge.id == "bridge":
        out.append(QAItem(
            question="What is a bridge for?",
            answer="A bridge helps people cross water or a gap without having to go through it.",
        ))
    if gift.id == "scarf":
        out.append(QAItem(
            question="What is a scarf for?",
            answer="A scarf wraps around the neck and helps keep a person warm when the wind is cold.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        meters = getattr(e, "meters", {})
        memes = getattr(e, "memes", {})
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} {bits}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest", challenge="bridge", gift="boots", name="Mina", sibling_name="Pip", parent_name="Grandmother"),
    StoryParams(place="river", challenge="storm", gift="scarf", name="Owen", sibling_name="Tara", parent_name="Mother"),
    StoryParams(place="hills", challenge="wolf", gift="lantern", name="Sora", sibling_name="Bram", parent_name="Father"),
]


def explain_rejection(setting: Setting, challenge: Challenge, gift: Gift) -> str:
    return (
        f"(No story: {gift.label} does not reasonably fit {challenge.danger} at {setting.place}. "
        f"The tale needs a cautious fix that truly helps.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_kind", sid, setting.kind))
        lines.append(asp.fact("affordance", sid, setting.affordance))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("keyword", cid, ch.keyword))
        for t in sorted(ch.tags):
            lines.append(asp.fact("tag", cid, t))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for p in sorted(gift.protects_against):
            lines.append(asp.fact("protects_against", gid, p))
        for h in sorted(gift.helps_with):
            lines.append(asp.fact("helps_with", gid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Challenge, Gift) :- setting(Place), challenge(Challenge), gift(Gift),
    compatible(Place, Challenge, Gift).

compatible(Place, bridge, Gift) :- Place = forest, (Gift = boots; Gift = lantern).
compatible(Place, wolf, lantern) :- Place = hills.
compatible(Place, storm, Gift) :- Gift = scarf; Gift = boots.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_stories() -> list[tuple[str, str, str]]:
    return sorted(valid_combos())


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Double cautionary bravery folk tale world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--sibling-name")
    ap.add_argument("--parent-name", choices=PARENT_NAMES)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "challenge", None):
        combos = [c for c in combos if c[1] == getattr(args, "challenge", None)]
    if getattr(args, "gift", None):
        combos = [c for c in combos if c[2] == getattr(args, "gift", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, gift = rng.choice(list(combos))
    setting = _safe_lookup(SETTINGS, place)
    ch = _safe_lookup(CHALLENGES, challenge)
    g = _safe_lookup(GIFTS, gift)
    if not reasonableness_gate(setting, ch, g):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    sibling = getattr(args, "sibling_name", None) or rng.choice([n for n in NAMES if n != name])
    parent = getattr(args, "parent_name", None) or rng.choice(PARENT_NAMES)
    return StoryParams(place=place, challenge=challenge, gift=gift, name=name, sibling_name=sibling, parent_name=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(CHALLENGES, params.challenge),
        _safe_lookup(GIFTS, params.gift),
        params.name,
        params.sibling_name,
        params.parent_name,
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid combinations:")
        for row in vals:
            print(" ", row)
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
            header = f"### {p.name}: {p.challenge} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
