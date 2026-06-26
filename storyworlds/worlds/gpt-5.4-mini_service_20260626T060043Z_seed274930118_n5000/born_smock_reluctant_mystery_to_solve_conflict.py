#!/usr/bin/env python3
"""
storyworlds/worlds/born_smock_reluctant_mystery_to_solve_conflict.py
====================================================================

A small adventure storyworld about a child, a reluctant choice, a smock,
and a mystery to solve.

Premise:
- A child was born with a strong wish to explore.
- They are sent on a quest to solve a small mystery.
- They feel reluctant about wearing a smock because it looks plain.
- The quest becomes a conflict when the mystery involves messy paint or dust.
- A helper offers a practical compromise so the child can continue the quest.

The story is state-driven:
- meters track physical conditions like dust, paint, and neatness
- memes track emotions like reluctance, courage, confusion, and joy

The domain is intentionally compact and constraint-checked.
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

# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    hero: object | None = None
    parent: object | None = None
    worn: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "paint": 0.0, "tired": 0.0}
        if not self.memes:
            self.memes = {"reluctance": 0.0, "courage": 0.0, "confusion": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str
    affords: set[str] = field(default_factory=set)
    indoor: bool = False
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
class Quest:
    id: str
    name: str
    verb: str
    gerund: str
    rush: str
    clue_noun: str
    clue_place: str
    mess: str
    soil: str
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
class Smock:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    plural: bool = False
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "studio": Setting(place="the paint studio", affords={"paint", "dust"}, indoor=True),
    "attic": Setting(place="the attic", affords={"dust", "maps"}, indoor=True),
    "garden": Setting(place="the garden shed", affords={"dust", "paint"}),
    "dock": Setting(place="the old dock", affords={"paint"}),
}

QUESTS = {
    "paint": Quest(
        id="paint",
        name="the painted clue",
        verb="search for the painted clue",
        gerund="searching for the painted clue",
        rush="hurry toward the easel",
        clue_noun="clue",
        clue_place="the wall by the easel",
        mess="paint",
        soil="spattered with paint",
        zone={"torso", "hands"},
        tags={"paint", "mystery", "quest"},
    ),
    "dust": Quest(
        id="dust",
        name="the dusty map piece",
        verb="find the dusty map piece",
        gerund="following the dusty trail",
        rush="climb up to the shelf",
        clue_noun="map piece",
        clue_place="the high shelf",
        mess="dust",
        soil="covered in dust",
        zone={"torso", "hands"},
        tags={"dust", "mystery", "quest"},
    ),
}

SMOCKS = [
    Smock(
        id="work_smock",
        label="smock",
        phrase="a clean smock",
        covers={"torso", "hands"},
        guards={"paint", "dust"},
    ),
    Smock(
        id="old_smock",
        label="old smock",
        phrase="an old smock with big pockets",
        covers={"torso", "hands"},
        guards={"paint", "dust"},
    ),
]

NAMES = {
    "girl": ["Mina", "Tara", "Lila", "Nora", "Ivy"],
    "boy": ["Arlo", "Finn", "Eli", "Jasper", "Theo"],
}

TRAITS = ["brave", "curious", "lively", "careful", "stubborn"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Logic
# ---------------------------------------------------------------------------
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


def quest_at_risk(quest: Quest, smock: Smock) -> bool:
    return quest.mess in smock.guards and bool(quest.zone & smock.covers)


def select_smock(quest: Quest) -> Optional[Smock]:
    for s in SMOCKS:
        if quest_at_risk(quest, s):
            return s
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            quest = _safe_lookup(QUESTS, qid)
            if select_smock(quest):
                combos.append((place, qid))
    return combos


def predict_soil(world: World, actor: Entity, quest: Quest, smock_id: str) -> bool:
    sim = world.copy()
    actor2 = sim.get(actor.id)
    actor2.meters[quest.mess] += 1
    sim.zone = set(quest.zone)
    smock = sim.entities.get(smock_id)
    if smock and smock.protective:
        return False
    for item in sim.worn_items(actor2):
        if item.protective or item.worn_by != actor2.id:
            continue
    return True


def _do_quest(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    world.zone = set(quest.zone)
    actor.meters[quest.mess] += 1
    if narrate:
        if quest.mess == "paint":
            world.say("Wet paint dusted the air like bright snow.")
        else:
            world.say("Dust puffed up around their shoes and sleeves.")


def _apply_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if not item.protective or item.caretaker is None:
                continue
        for region in world.zone:
            if actor.meters["paint"] >= THRESHOLD or actor.meters["dust"] >= THRESHOLD:
                for item in world.worn_items(actor):
                    if item.protective or region not in item.covers:
                        continue
                    if world.covered(actor, region):
                        continue
                    sig = ("soil", actor.id, item.id, region)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters["paint"] += actor.meters["paint"]
                    item.meters["dust"] += actor.meters["dust"]
                    out.append(f"{item.label.capitalize()} picked up the mess.")
    return out


def _apply_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["reluctance"] < THRESHOLD or actor.memes["confusion"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["courage"] += 0.5
        out.append("__conflict__")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        if _apply_soil(world):
            changed = True
        if _apply_conflict(world):
            changed = True


def tell(setting: Setting, quest: Quest, hero_name: str, hero_gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    clue = world.add(Entity(id="clue", type="thing", label=quest.clue_noun, phrase=quest.name, caretaker=parent.id))

    hero.memes["reluctance"] += 1
    hero.memes["confusion"] += 1

    world.say(f"{hero.id} was born ready for adventure, and everyone knew {hero.pronoun('subject')} had a nose for mysteries.")
    world.say(f"But {hero.id} was reluctant to wear a smock, because {hero.pronoun('subject')} thought it looked too plain for a quest.")
    world.say(f"That morning, {hero.id} and {hero.pronoun('possessive')} {parent.label} found a note about {quest.name}.")

    world.para()
    world.say(f"The note pointed to {quest.clue_place}, so they went to {setting.place} to {quest.verb}.")
    world.say(f"{hero.id} wanted to rush ahead, but the clue was hidden where paint or dust could cling to clothes.")
    world.say(f"{hero.id} followed the trail anyway, feeling both brave and uneasy.")

    world.para()
    _do_quest(world, hero, quest)
    hero.memes["confusion"] += 0.5
    hero.memes["reluctance"] += 0.5

    smock = select_smock(quest)
    if smock is None:
        pass
    worn = world.add(Entity(
        id=smock.id,
        type="smock",
        label=smock.label,
        phrase=smock.phrase,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(smock.covers),
    ))
    worn.worn_by = hero.id

    world.say(f"When the search got messy, {hero.pronoun('possessive')} {parent.label} held up {smock.phrase} and smiled.")
    world.say(f"'{hero.id}, you can keep going if you wear this,' {hero.pronoun('possessive')} {parent.label} said.")
    hero.memes["confusion"] += 0.5

    if quest.mess == "paint":
        world.say(f"{hero.id} looked at the smock, then at the painted clue, and the choice became clear.")
    else:
        world.say(f"{hero.id} looked at the smock, then at the dusty shelf, and nodded at last.")

    hero.memes["reluctance"] = 0.0
    hero.memes["joy"] += 1.0
    hero.memes["courage"] += 1.0

    world.para()
    world.say(f"Once the smock was on, {hero.id} climbed, reached, and solved the mystery.")
    world.say(f"The missing clue was right where the note said, and the quest was complete.")
    world.say(f"By the end, {hero.id} was no longer reluctant at all; {hero.pronoun('subject')} was proud, tidy, and grinning.")

    world.facts.update(
        hero=hero,
        parent=parent,
        clue=clue,
        quest=quest,
        setting=setting,
        smock=worn,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    return [
        f'Write a short adventure story for a child named {hero.id} who was born ready to solve mysteries.',
        f"Tell a gentle quest story where {hero.id} is reluctant to wear a smock but has to solve {quest.name}.",
        f'Write a small mystery adventure that uses the words "born", "smock", and "reluctant".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    quest = _safe_fact(world, f, "quest")
    smock = _safe_fact(world, f, "smock")
    return [
        QAItem(
            question=f"Why was {hero.id} reluctant at the start of the story?",
            answer=f"{hero.id} was reluctant because {hero.pronoun('subject')} thought the smock looked too plain for an adventure.",
        ),
        QAItem(
            question=f"What mystery were {hero.id} and {hero.pronoun('possessive')} {parent.label} trying to solve?",
            answer=f"They were trying to solve {quest.name}, which led them to {quest.clue_place}.",
        ),
        QAItem(
            question=f"How did the smock help {hero.id} finish the quest?",
            answer=f"The smock covered {sorted(smock.covers)[0]} and kept the paint or dust from ruining {hero.pronoun('possessive')} clothes while {hero.id} searched.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud, brave, and happy because the mystery was solved.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "smock": [
        QAItem(
            question="What is a smock for?",
            answer="A smock is a loose cover worn over clothes to help keep paint, dust, or other messes off them.",
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to find something, solve a problem, or reach a goal.",
        )
    ],
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is hidden, unknown, or not yet explained, so people try to figure it out.",
        )
    ],
    "conflict": [
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is the part where someone wants one thing, but something makes that choice hard.",
        )
    ],
    "born": [
        QAItem(
            question="What does it mean when someone is born?",
            answer="Being born means coming into the world as a baby at the start of life.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["born"])
    out.extend(WORLD_KNOWLEDGE["mystery"])
    out.extend(WORLD_KNOWLEDGE["quest"])
    out.extend(WORLD_KNOWLEDGE["conflict"])
    out.extend(WORLD_KNOWLEDGE["smock"])
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(Q, S) :- quest(Q), smock(S), mess_of(Q, M), guards(S, M), zone_of(Q, Z), covers(S, Z).
valid(Place, Q) :- affords(Place, Q), quest(Q), has_smock(Q).
has_smock(Q) :- prize_at_risk(Q, S), smock(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for q in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("mess_of", qid, q.mess))
        for z in sorted(q.zone):
            lines.append(asp.fact("zone_of", qid, z))
    for s in SMOCKS:
        lines.append(asp.fact("smock", s.id))
        for m in sorted(s.guards):
            lines.append(asp.fact("guards", s.id, m))
        for c in sorted(s.covers):
            lines.append(asp.fact("covers", s.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asv = set(valid_asp_combos())
    if py == asv:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python combo checks:")
    if py - asv:
        print("  only in python:", sorted(py - asv))
    if asv - py:
        print("  only in clingo:", sorted(asv - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="studio", quest="paint", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="attic", quest="dust", name="Arlo", gender="boy", parent="father", trait="brave"),
    StoryParams(place="garden", quest="paint", name="Lila", gender="girl", parent="mother", trait="stubborn"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure mystery storyworld with a reluctant smock.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest_id = rng.choice(list(combos))
    quest = _safe_lookup(QUESTS, quest_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = valid_asp_combos()
        print(f"{len(combos)} compatible (place, quest) combos:\n")
        for place, quest in combos:
            print(f"  {place:10} {quest}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
