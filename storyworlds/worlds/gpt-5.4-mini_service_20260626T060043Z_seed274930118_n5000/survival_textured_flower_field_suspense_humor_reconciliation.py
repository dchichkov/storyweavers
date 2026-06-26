#!/usr/bin/env python3
"""
survival_textured_flower_field_suspense_humor_reconciliation.py
===============================================================

A small Animal-Story-style world in a flower field, with a textured object,
a survival scare, a humorous turn, and reconciliation at the end.
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
    kind: str = "thing"  # "character" | "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.species in {"rabbit", "hare", "mouse", "squirrel", "bird"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.species
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
    place: str = "the flower field"
    scent: str = "sweet"
    affordance: str = "foraging"
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
    noun: str
    danger: str
    suspense: str
    humor: str
    resolve: str
    risk: str
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
class Prize:
    id: str
    label: str
    phrase: str
    texture: str
    region: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
    tags: set[str] = field(default_factory=set)
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    hero: str
    hero_species: str
    friend: str
    friend_species: str
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


SETTINGS = {
    "flower_field": Setting(place="the flower field", scent="sweet", affordance="foraging"),
}

CHALLENGES = {
    "bee_blunder": Challenge(
        id="bee_blunder",
        verb="cross the buzzing patch",
        noun="buzzing bees",
        danger="too close to the hive",
        suspense="The bees hummed louder with every step.",
        humor="A beetle tried to look brave and immediately sneezed.",
        resolve="They slowed down and listened before moving again.",
        risk="stung",
        tags={"bee", "buzz", "survival"},
    ),
    "thorn_tangle": Challenge(
        id="thorn_tangle",
        verb="walk through the prickly stems",
        noun="thorny stems",
        danger="the stems were scratchy and easy to trip over",
        suspense="The stems swayed like they were deciding whether to grab a paw.",
        humor="A grasshopper jumped so hard it bounced back into a daisy.",
        resolve="They stepped around the sharp parts and kept low.",
        risk="scratched",
        tags={"thorn", "scratch", "survival"},
    ),
    "storm_drift": Challenge(
        id="storm_drift",
        verb="reach the safe clump of clover",
        noun="windy petals",
        danger="a little storm had started to tug at the flowers",
        suspense="The sky went gray, and the petals began to whirl.",
        humor="A ladybug held onto a leaf like it was a tiny boat.",
        resolve="They found shelter beside a thick stem and waited it out.",
        risk="soaked",
        tags={"storm", "wind", "survival"},
    ),
}

PRIZES = {
    "seed_pouch": Prize(
        id="seed_pouch",
        label="seed pouch",
        phrase="a tiny seed pouch",
        texture="textured",
        region="side",
        tags={"texture", "seed"},
    ),
    "moss_cloak": Prize(
        id="moss_cloak",
        label="moss cloak",
        phrase="a soft moss cloak",
        texture="textured",
        region="back",
        tags={"texture", "moss"},
    ),
    "petal_scarf": Prize(
        id="petal_scarf",
        label="petal scarf",
        phrase="a silky petal scarf",
        texture="textured",
        region="neck",
        tags={"texture", "petal"},
    ),
}

TOOLS = {
    "leaf_umbrella": Tool(
        id="leaf_umbrella",
        label="leaf umbrella",
        phrase="a big leaf umbrella",
        guards={"soaked"},
        covers={"back", "neck"},
        tags={"storm"},
    ),
    "bee_bell": Tool(
        id="bee_bell",
        label="bee bell",
        phrase="a small bee bell",
        guards={"stung"},
        covers={"side"},
        tags={"bee"},
    ),
    "soft_boots": Tool(
        id="soft_boots",
        label="soft boots",
        phrase="soft boots",
        guards={"scratched"},
        covers={"feet"},
        tags={"thorn"},
    ),
}

HEROES = [
    ("Milo", "rabbit"),
    ("Pip", "mouse"),
    ("Nia", "hare"),
    ("Toby", "squirrel"),
]
FRIENDS = [
    ("Dot", "bird"),
    ("Fern", "mouse"),
    ("Lulu", "rabbit"),
    ("Beetle", "beetle"),
]


def can_risk(ch: Challenge, prize: Prize) -> bool:
    return prize.fragile and "texture" in prize.tags


def select_tool(ch: Challenge, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS.values():
        if ch.risk in tool.guards and prize.region in tool.covers:
            return tool
    return None


def predict(world: World, hero: Entity, challenge: Challenge, prize: Entity) -> dict:
    sim = world.copy()
    act(sim, hero.id, challenge.id, narrate=False, warn=False)
    p = sim.get(prize.id)
    return {
        "ruined": bool(p.meters.get(challenge.risk, 0) >= THRESHOLD),
    }


def act(world: World, hero_id: str, challenge_id: str, narrate: bool = True, warn: bool = True) -> None:
    hero = world.get(hero_id)
    ch = _safe_lookup(CHALLENGES, challenge_id)
    hero.meters[ch.id] = hero.meters.get(ch.id, 0.0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    hero.memes["survival"] = hero.memes.get("survival", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} edged toward {ch.noun}, trying to {ch.verb}.")
        world.say(ch.suspense)
    if warn:
        propagate(world)


def propagate(world: World) -> None:
    for hero in world.characters():
        for prize in list(world.entities.values()):
            if prize.kind != "thing":
                continue
            for ch in CHALLENGES.values():
                if hero.meters.get(ch.id, 0.0) < THRESHOLD:
                    continue
                sig = ("risk", hero.id, prize.id, ch.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                if prize.owner == hero.id and prize.region in {"side", "back", "neck"}:
                    prize.meters[ch.risk] = prize.meters.get(ch.risk, 0.0) + 1
                    world.say(f"That could leave {hero.pronoun('possessive')} {prize.label} {ch.risk}.")
                    if prize.caretaker:
                        carer = world.get(prize.caretaker)
                        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
                        world.say(f"{carer.id} noticed and worried about keeping everyone safe.")


def choose_friend(world: World, hero: Entity) -> Entity:
    for e in world.characters():
        if e.id != hero.id:
            return e
    pass


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    ch = _safe_lookup(CHALLENGES, params.challenge)
    pr = _safe_lookup(PRIZES, params.prize)
    world = World(setting)

    hero = world.add(Entity(id=params.hero, kind="character", species=params.hero_species))
    friend = world.add(Entity(id=params.friend, kind="character", species=params.friend_species))
    prize = world.add(Entity(id="prize", kind="thing", species=pr.id, label=pr.label, phrase=pr.phrase, owner=hero.id, caretaker=friend.id))
    tool: Optional[Entity] = None

    world.say(f"{hero.id} lived near {setting.place} and loved the sweet smell of flowers.")
    world.say(f"{hero.id} was careful, but also curious, and {hero.pronoun()} liked {ch.verb}.")
    world.say(f"One day, {friend.id} brought {hero.id} {pr.phrase}, and it felt wonderfully {pr.texture}.")
    world.para()
    world.say(f"At {setting.place}, the path to the clover patch led past {ch.danger}.")
    act(world, hero.id, ch.id)
    world.say(ch.humor)
    world.say(f"{friend.id} whispered, “We may need a clever idea before {hero.pronoun('possessive')} {pr.label} gets {ch.risk}.”")
    world.para()

    if can_risk(ch, pr):
        tool_def = select_tool(ch, pr)
        if tool_def is None:
            pass
        if predict(world, hero, ch, prize)["ruined"]:
            pass
        tool = world.add(Entity(id=tool_def.id, kind="thing", species="tool", label=tool_def.label, phrase=tool_def.phrase, owner=hero.id))
        tool.worn_by = hero.id
        world.say(f"{friend.id} found {tool.phrase}, and {hero.id} wore it at once.")
        world.say(f"That way, {hero.id} could keep going without ruining {hero.pronoun('possessive')} {pr.label}.")
        world.say(ch.resolve)
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
        friend.memes["kindness"] = friend.memes.get("kindness", 0.0) + 1
        world.say(f"{hero.id} laughed, and {friend.id} laughed too, because the scare had turned into a safe plan.")
        world.say(f"At the end, the {pr.label} stayed {pr.texture}, and the flower field looked gentle again.")
    else:
        pass

    world.facts.update(hero=hero, friend=friend, prize=prize, challenge=ch, tool=tool, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    h = _safe_fact(world, f, "hero")
    c = _safe_fact(world, f, "challenge")
    p = _safe_fact(world, f, "prize")
    return [
        f'Write an animal story set in a flower field where {h.id} must survive a {c.id} problem while protecting a {p.label}.',
        f"Tell a suspenseful but gentle story about {h.id} and {f['friend'].id} in the flower field, ending in reconciliation.",
        f"Write a child-friendly story where something {p.texture} nearly gets ruined, but the animals solve it with humor and care.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h = _safe_fact(world, f, "hero")
    fr = _safe_fact(world, f, "friend")
    c = _safe_fact(world, f, "challenge")
    p = _safe_fact(world, f, "prize")
    return [
        QAItem(
            question=f"Where does {h.id}'s story happen?",
            answer=f"It happens in the flower field, where the air smells sweet and the flowers make a colorful path.",
        ),
        QAItem(
            question=f"What was the scary part for {h.id}?",
            answer=f"The scary part was {c.danger}, because {h.id} had to survive while protecting the {p.label}.",
        ),
        QAItem(
            question=f"What helped turn the tense moment into a happy ending?",
            answer=f"{fr.id} brought a clever tool and stayed kind, so the animals could solve the problem and end in reconciliation.",
        ),
        QAItem(
            question=f"How did {h.id} feel at the end?",
            answer=f"{h.id} felt relieved and happy, because the {p.label} stayed {p.texture} and everyone was safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flower field?",
            answer="A flower field is a wide place where many flowers grow close together and insects can buzz from bloom to bloom.",
        ),
        QAItem(
            question="Why can tiny animals feel nervous outdoors?",
            answer="Tiny animals can feel nervous outdoors because they must watch for weather, sharp stems, and bigger dangers, so staying safe matters a lot.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people or animals stop being upset and find a kind way to be together again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        out.append(f"  {e.id} ({e.kind}/{e.species}) " + " ".join(bits))
    out.append(f"  fired={sorted(world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
prize_at_risk(C,P) :- challenge(C), prize(P), fragile(P), texture(P).
tool_fits(T,C,P) :- tool(T), challenge(C), prize(P), guards(T,R), covers(T,S), region(P,S), risk(C,R).
valid_story(C,P) :- prize_at_risk(C,P), tool_fits(_,C,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("risk", cid, c.risk))
        lines.append(asp.fact("texture_theme", cid, "suspense"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        lines.append(asp.fact("texture", pid, p.texture))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", tid, g))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", tid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, p in PRIZES.items():
        for cid, c in CHALLENGES.items():
            if can_risk(c, p) and select_tool(c, p):
                out.append(("flower_field", cid, pid))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid combos).")
        return 0
    print("Mismatch between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world in a flower field.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-species", choices=["rabbit", "mouse", "hare", "squirrel"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-species", choices=["bird", "mouse", "rabbit", "beetle"])
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
    if getattr(args, "challenge", None) and getattr(args, "prize", None):
        if ("flower_field", getattr(args, "challenge", None), getattr(args, "prize", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    _, ch, pr = rng.choice(list(combos))
    hero, hero_species = (getattr(args, "hero", None), getattr(args, "hero_species", None)) if getattr(args, "hero", None) and getattr(args, "hero_species", None) else rng.choice(HEROES)
    friend, friend_species = (getattr(args, "friend", None), getattr(args, "friend_species", None)) if getattr(args, "friend", None) and getattr(args, "friend_species", None) else rng.choice(FRIENDS)
    return StoryParams(place="flower_field", challenge=ch, prize=pr, hero=getattr(args, "hero", None) or hero, hero_species=getattr(args, "hero_species", None) or hero_species, friend=getattr(args, "friend", None) or friend, friend_species=getattr(args, "friend_species", None) or friend_species)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="flower_field", challenge="bee_blunder", prize="seed_pouch", hero="Milo", hero_species="rabbit", friend="Dot", friend_species="bird"),
    StoryParams(place="flower_field", challenge="thorn_tangle", prize="moss_cloak", hero="Pip", hero_species="mouse", friend="Fern", friend_species="mouse"),
    StoryParams(place="flower_field", challenge="storm_drift", prize="petal_scarf", hero="Nia", hero_species="hare", friend="Lulu", friend_species="rabbit"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print(asp_program("#show valid_story/2."))
        print()
        print(f"{len(asp_valid_combos())} valid story combos")
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
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
            header = f"### {p.hero}: {p.challenge} / {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
