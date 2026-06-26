#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/smart_inner_monologue_adventure.py
===============================================================================================================

A small adventure storyworld about a child using a smart inner monologue to
solve a tricky outdoor problem.
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    features: set[str] = field(default_factory=set)
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
class Challenge:
    id: str
    verb: str
    danger: str
    signal: str
    risk: str
    zone: set[str]
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
class Item:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    portable: bool = True
    answer: str = ""
    question: str = ""
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
    setting: str
    challenge: str
    item: str
    name: str
    gender: str
    helper: str
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
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def wearing(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


SETTINGS = {
    "forest": Setting(place="the forest trail", features={"trees", "trail", "birds"}, affords={"bridge", "cave"}),
    "river": Setting(place="the river bank", features={"water", "stones", "bank"}, affords={"bridge", "storm"}),
    "hill": Setting(place="the hill path", features={"hill", "wind", "grass"}, affords={"cave", "storm"}),
}

CHALLENGES = {
    "bridge": Challenge(
        id="bridge",
        verb="cross the shaky bridge",
        danger="the boards could wobble and drop someone into the water",
        signal="the planks creaked softly",
        risk="wobbly",
        zone={"feet", "legs"},
        keyword="bridge",
        tags={"bridge", "water"},
    ),
    "cave": Challenge(
        id="cave",
        verb="enter the dark cave",
        danger="the cave was dim and twisty, so a wrong step could make a child stumble",
        signal="the cave looked black at the mouth",
        risk="dark",
        zone={"feet", "hands"},
        keyword="cave",
        tags={"cave", "dark"},
    ),
    "storm": Challenge(
        id="storm",
        verb="hurry through the rainstorm",
        danger="the rain could soak clothes and make the path slippery",
        signal="the clouds grew heavy and gray",
        risk="wet",
        zone={"head", "torso", "feet"},
        keyword="storm",
        tags={"storm", "wet"},
    ),
}

ITEMS = {
    "lantern": Item(id="lantern", label="lantern", phrase="a little lantern", guards={"dark"}, covers={"hands"}),
    "boots": Item(id="boots", label="boots", phrase="a pair of boots", guards={"wet"}, covers={"feet"}),
    "rope": Item(id="rope", label="rope", phrase="a sturdy rope", guards={"wobble"}, covers={"hands"}),
    "raincoat": Item(id="raincoat", label="raincoat", phrase="a bright raincoat", guards={"wet"}, covers={"torso"}),
    "map": Item(id="map", label="map", phrase="a folded map", guards=set(), covers={"hands"}),
}

NAMES = ["Maya", "Nina", "Leo", "Owen", "Zara", "Milo", "Ivy", "Eli"]
HELPERS = ["mother", "father", "grandparent", "older sibling"]
TRAITS = ["smart", "curious", "brave", "careful", "thoughtful"]


def challenge_needs_item(challenge: Challenge, item: Item) -> bool:
    if challenge.id == "bridge":
        return "wobble" in item.guards
    if challenge.id == "cave":
        return "dark" in item.guards
    if challenge.id == "storm":
        return "wet" in item.guards
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, setting in SETTINGS.items():
        for c_id in setting.affords:
            ch = _safe_lookup(CHALLENGES, c_id)
            for i_id, item in ITEMS.items():
                if challenge_needs_item(ch, item):
                    out.append((s_id, c_id, i_id))
    return out


def select_item(challenge: Challenge) -> Optional[Item]:
    for item in ITEMS.values():
        if challenge_needs_item(challenge, item):
            return item
    return None


def predict(world: World, hero: Entity, challenge: Challenge, item: Item) -> dict:
    sim = world.copy()
    sim.zone = set(challenge.zone)
    sim.get(hero.id).meters["stress"] += 1
    if challenge.id == "bridge" and "wobble" not in item.guards:
        return {"safe": False}
    if challenge.id == "cave" and "dark" not in item.guards:
        return {"safe": False}
    if challenge.id == "storm" and "wet" not in item.guards:
        return {"safe": False}
    return {"safe": True}


def _advance(world: World, hero: Entity, challenge: Challenge, item: Item) -> None:
    hero.meters["courage"] += 1
    hero.memes["focus"] += 1
    if challenge.id == "bridge":
        if "wobble" not in item.guards:
            hero.meters["risk"] += 1
    elif challenge.id == "cave":
        if "dark" not in item.guards:
            hero.meters["risk"] += 1
    elif challenge.id == "storm":
        if "wet" not in item.guards:
            hero.meters["risk"] += 1


def tell(setting: Setting, challenge: Challenge, item_cfg: Item, name: str, gender: str, helper: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={"stress": 0.0}, memes={"curiosity": 1.0}))
    guide = world.add(Entity(id="helper", kind="character", type=helper, label=f"the {helper}", meters={"patience": 1.0}))
    item = world.add(Entity(id=item_cfg.id, type=item_cfg.label, label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id, carried_by=hero.id))
    hero.memes["smart"] += 1

    world.say(f"{hero.id} stood at {setting.place}, where {', '.join(sorted(setting.features))} made the air feel alive.")
    world.say(f"{hero.id} liked adventures, and {hero.pronoun()} had a smart little habit of thinking before acting.")
    world.say(f"{hero.id} carried {item_cfg.phrase}, because {helper} said it might help on a day like this.")

    world.para()
    world.say(f"At the trail ahead, {challenge.signal}. {challenge.danger}.")
    world.say(f"{hero.id} wanted to {challenge.verb}, but then {hero.pronoun('subject')} paused and listened to {hero.pronoun('possessive')} own inner monologue: \"Slow down. Look first. Smart choices keep adventures fun.\"")
    hero.memes["thoughtful"] += 1
    hero.meters["stress"] += 1

    world.say(f"{hero.id} looked at {item_cfg.label} and decided to use it in the cleverest way.")
    _advance(world, hero, challenge, item)
    world.say(f"{hero.id} and {guide.label} moved ahead together, one careful step at a time.")

    world.para()
    if challenge.id == "bridge":
        world.say(f"{hero.id} tied the {item_cfg.label} to a low post and held on tight. The bridge stopped feeling so scary.")
        if "wobble" in item_cfg.guards:
            world.say(f"The planks still creaked, but the {item_cfg.label} gave {hero.id} a steady way across.")
    elif challenge.id == "cave":
        world.say(f"{hero.id} lifted the {item_cfg.label} high and followed the pale edge of the wall. The dark cave became a place to explore, not fear.")
        if "dark" in item_cfg.guards:
            world.say(f"The little light made every stone look friendly and clear.")
    elif challenge.id == "storm":
        world.say(f"{hero.id} pulled on the {item_cfg.label} and stepped through the rain. The wind still blew, but the wet path did not win.")
        if "wet" in item_cfg.guards:
            world.say(f"The {item_cfg.label} kept {hero.pronoun('object')} dry enough to keep going.")
    hero.meters["joy"] += 1

    world.say(f"In the end, {hero.id} reached the safe side and smiled a big adventure smile. {hero.id} had not just gone forward; {hero.pronoun('subject')} had done it smartly.")
    world.facts.update(hero=hero, guide=guide, challenge=challenge, item=item, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ch = _safe_fact(world, f, "challenge")
    return [
        f'Write a short adventure story for a young child about a smart choice and the word "smart".',
        f"Tell a story where {hero.id} uses an inner monologue to solve a problem while trying to {ch.verb}.",
        f"Write a gentle adventure with a child, a helper, and a useful object that helps them keep going.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    ch = _safe_fact(world, f, "challenge")
    item = _safe_fact(world, f, "item")
    return [
        QAItem(
            question=f"Who was the adventure story about?",
            answer=f"It was about {hero.id}, a {hero.type} who liked to think carefully during adventures.",
        ),
        QAItem(
            question=f"What problem did {hero.id} face?",
            answer=f"{hero.id} wanted to {ch.verb}, but {ch.danger}.",
        ),
        QAItem(
            question=f"What did {hero.id}'s inner monologue help {hero.pronoun('object')} do?",
            answer=f"It helped {hero.id} slow down, think smartly, and use {item.phrase} in a clever way with {guide.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.id} got safely across, felt proud, and discovered that being smart could turn a hard moment into an adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    ch = _safe_fact(world, f, "challenge")
    item = _safe_fact(world, f, "item")
    base = [
        QAItem(
            question="What does an inner monologue mean?",
            answer="An inner monologue is the little voice in your mind that helps you think through a choice before you act.",
        ),
        QAItem(
            question="Why can a lantern help in a cave?",
            answer="A lantern gives light, so it helps you see the path in a dark place.",
        ),
        QAItem(
            question="Why are boots useful in rain?",
            answer="Boots help keep your feet drier when the ground is wet.",
        ),
        QAItem(
            question="Why is rope useful on a bridge?",
            answer="Rope can give a person something steady to hold, which makes crossing feel safer.",
        ),
    ]
    if ch.id == "bridge":
        base.append(QAItem(question="What is a bridge for?", answer="A bridge helps people cross over water or another gap." ))
    if ch.id == "cave":
        base.append(QAItem(question="What is a cave like?", answer="A cave is a natural space in rock, and it can be dark inside." ))
    if ch.id == "storm":
        base.append(QAItem(question="What is a rainstorm?", answer="A rainstorm is a time when a lot of rain falls and the wind can feel strong." ))
    if item.id == "map":
        base.append(QAItem(question="What does a map do?", answer="A map shows where things are and helps people find their way."))
    return base


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"zone={sorted(world.zone)}")
    return "\n".join(lines)


@dataclass
class ASPParams:
    pass
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


ASP_RULES = r"""
valid(S,C,I) :- setting(S), affords(S,C), challenge(C), item(I), fixes(I,C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", s_id))
        for c in sorted(setting.affords):
            lines.append(asp.fact("affords", s_id, c))
    for c_id in CHALLENGES:
        lines.append(asp.fact("challenge", c_id))
    for i_id, item in ITEMS.items():
        lines.append(asp.fact("item", i_id))
        for g in sorted(item.guards):
            lines.append(asp.fact("fixes", i_id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a smart inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "challenge", None):
        combos = [c for c in combos if c[1] == getattr(args, "challenge", None)]
    if getattr(args, "item", None):
        combos = [c for c in combos if c[2] == getattr(args, "item", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, challenge, item = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(setting=setting, challenge=challenge, item=item, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(CHALLENGES, params.challenge), _safe_lookup(ITEMS, params.item), params.name, params.gender, params.helper)
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
    StoryParams(setting="forest", challenge="cave", item="lantern", name="Maya", gender="girl", helper="mother"),
    StoryParams(setting="river", challenge="bridge", item="rope", name="Leo", gender="boy", helper="father"),
    StoryParams(setting="hill", challenge="storm", item="raincoat", name="Ivy", gender="girl", helper="grandparent"),
]


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
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
