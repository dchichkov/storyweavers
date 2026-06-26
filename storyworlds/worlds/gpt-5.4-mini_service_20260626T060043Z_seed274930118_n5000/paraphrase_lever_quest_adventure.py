#!/usr/bin/env python3
"""
storyworlds/worlds/paraphrase_lever_quest_adventure.py
=======================================================

A small adventure world about a quest, a lever, and the power of
paraphrasing a warning clearly.

Premise:
- A young adventurer wants to finish a quest and reach a goal.
- A gate, bridge, or door can be moved with a lever.
- A guide gives a clue, but the hero must paraphrase it correctly to avoid
  using the lever the wrong way.

This world keeps the action concrete:
- physical state uses meters
- social/emotional state uses memes
- the narrative is driven by world state, not by a fixed paragraph template
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    guide: object | None = None
    hero: object | None = None
    item: object | None = None
    lever: object | None = None
    obstacle: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "princess"}
        male = {"boy", "man", "father", "king", "prince"}
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
class Place:
    name: str
    afford: str
    detail: str
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
class QuestItem:
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Lever:
    label: str
    pull_text: str
    effect_text: str
    target_kind: str
    target_state: str
    requires_hint: bool = True
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
    quest: str
    item: str
    lever: str
    name: str
    gender: str
    guide: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


PLACES = {
    "stone_hall": Place("the stone hall", "lever", "A long hall of gray stone echoed softly."),
    "river_room": Place("the river room", "bridge", "A narrow room held a wooden span above water."),
    "gate_yard": Place("the gate yard", "gate", "Tall walls surrounded a rusty gate and a patch of moss."),
}

QUESTS = {
    "find_key": "find the hidden key",
    "reach_map": "reach the old map",
    "save_friend": "help the trapped friend",
}

QUEST_OBJECTS = {
    "key": QuestItem("key", "a little brass key", "hand"),
    "map": QuestItem("map", "an old folded map", "pack"),
    "friend": QuestItem("friend", "a small rescued friend", "heart"),
}

LEVERS = {
    "lift_bridge": Lever(
        label="bridge lever",
        pull_text="pull the bridge lever",
        effect_text="the bridge lowered with a soft clunk",
        target_kind="bridge",
        target_state="lowered",
    ),
    "open_gate": Lever(
        label="gate lever",
        pull_text="pull the gate lever",
        effect_text="the gate swung open with a groan",
        target_kind="gate",
        target_state="open",
    ),
    "raise_portcullis": Lever(
        label="portcullis lever",
        pull_text="pull the portcullis lever",
        effect_text="the heavy bars lifted high enough to pass under",
        target_kind="gate",
        target_state="raised",
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Ivy", "Lena", "Tia", "Rina"]
BOY_NAMES = ["Arlo", "Jasper", "Finn", "Theo", "Milo", "Noah"]
TRAITS = ["brave", "curious", "careful", "quick-thinking", "steady", "bold"]


def _meter_get(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem_get(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _set_mem(e: Entity, key: str, value: float) -> None:
    e.memes[key] = value


def _add_mem(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = _mem_get(e, key) + delta


def _add_meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = _meter_get(e, key) + delta


def _hero_desc(hero: Entity) -> str:
    trait = next((t for t in hero.meters.keys() if t), "")
    return trait


def tell(place: Place, quest_key: str, item_key: str, lever_key: str,
         hero_name: str, hero_gender: str, guide_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        meters={trait: 1.0},
        memes={"curiosity": 1.0},
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=guide_type,
        label=guide_type,
        memes={"care": 1.0},
    ))
    item = world.add(Entity(
        id="Prize",
        type=item_key,
        label=_safe_lookup(QUEST_OBJECTS, item_key).label,
        phrase=_safe_lookup(QUEST_OBJECTS, item_key).phrase,
        owner=hero.id,
        region=_safe_lookup(QUEST_OBJECTS, item_key).region,
        plural=_safe_lookup(QUEST_OBJECTS, item_key).plural,
    ))
    lever = world.add(Entity(
        id="Lever",
        type="lever",
        label=_safe_lookup(LEVERS, lever_key).label,
        phrase=_safe_lookup(LEVERS, lever_key).label,
        owner=place.name,
        meters={"stiff": 1.0},
    ))
    obstacle = world.add(Entity(
        id="Obstacle",
        type=_safe_lookup(LEVERS, lever_key).target_kind,
        label=_safe_lookup(LEVERS, lever_key).target_kind,
        phrase=_safe_lookup(LEVERS, lever_key).target_kind,
        meters={"closed": 1.0},
    ))

    world.say(
        f"{hero.id} was a {trait} young adventurer who had a simple quest: "
        f"to {_safe_lookup(QUESTS, quest_key)}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} carried {item.phrase} and came to {place.name}. "
        f"{place.detail}"
    )

    world.para()
    world.say(
        f"At the edge of the path, {guide.id} gave a careful clue. "
        f'"Before you touch anything, paraphrase the warning back to me," '
        f"{guide.pronoun('subject')} said."
    )
    _add_mem(hero, "listening", 1.0)
    _add_mem(hero, "worry", 0.5 if guide_type != "old owl" else 1.0)

    if guide_type == "old owl":
        world.say(
            f"{hero.id} paused and paraphrased the clue in a clear voice: "
            f'"The lever moves the {_safe_lookup(LEVERS, lever_key).target_kind}, so I should '
            f'pull it only when the path is ready."'
        )
        _add_mem(hero, "understanding", 1.0)
    else:
        world.say(
            f"{hero.id} tried to paraphrase it, but the words came out wobbly. "
            f'"I think it means I should yank the lever fast," {hero.pronoun()} said.'
        )
        _add_mem(hero, "confusion", 1.0)

    world.para()

    if _mem_get(hero, "understanding") >= THRESHOLD:
        world.say(
            f"{hero.id} waited, checked the {_safe_lookup(LEVERS, lever_key).target_kind}, and "
            f"then {_safe_lookup(LEVERS, lever_key).pull_text}."
        )
        _add_mem(hero, "courage", 1.0)
        _add_meter(obstacle, "closed", -1.0)
        _add_meter(obstacle, _safe_lookup(LEVERS, lever_key).target_state, 1.0)
        _add_mem(hero, "joy", 1.0)
        world.say(
            f"{_safe_lookup(LEVERS, lever_key).effect_text}. {hero.id} stepped through with "
            f"{item.phrase} safe in {hero.pronoun('possessive')} hands."
        )
        world.say(
            f"At the end of the quest, {hero.id} looked small beside the open way, "
            f"but {hero.pronoun()} had grown steadier and wiser."
        )
        world.facts["solved"] = True
    else:
        world.say(
            f"{hero.id} rushed forward and {_safe_lookup(LEVERS, lever_key).pull_text} too soon."
        )
        _add_meter(obstacle, "closed", 0.0)
        _add_mem(hero, "surprise", 1.0)
        _add_mem(hero, "embarrassment", 1.0)
        world.say(
            f"The {_safe_lookup(LEVERS, lever_key).target_kind} shuddered, but the path did not "
            f"help. {guide.id} frowned and asked for a better paraphrase."
        )
        world.say(
            f"{hero.id} took a breath, repeated the clue more clearly, and tried again. "
            f"This time the lever worked, and the way opened at last."
        )
        _add_mem(hero, "understanding", 1.0)
        _add_mem(hero, "joy", 1.0)
        _add_meter(obstacle, _safe_lookup(LEVERS, lever_key).target_state, 1.0)
        world.facts["solved"] = True

    world.facts.update(
        hero=hero,
        guide=guide,
        item=item,
        lever=lever,
        obstacle=obstacle,
        place=place,
        quest_key=quest_key,
        item_key=item_key,
        lever_key=lever_key,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    item = _safe_fact(world, f, "item")
    lever = _safe_fact(world, f, "lever")
    place = _safe_fact(world, f, "place")
    quest = _safe_fact(world, f, "quest_key")
    return [
        f'Write a short adventure story for a child who must {_safe_lookup(QUESTS, quest)} '
        f'at {place.name} by using {lever.label}.',
        f'Tell a quest story where {hero.id} must paraphrase a warning before '
        f'pulling {lever.label} and saving {item.phrase}.',
        f'Write a gentle adventure about a clever child, a lever, and a clue '
        f"that must be paraphrased clearly before action.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    item = _safe_fact(world, f, "item")
    lever = _safe_fact(world, f, "lever")
    place = _safe_fact(world, f, "place")
    quest = QUESTS[f["quest_key"]]
    qa = [
        QAItem(
            question=f"What quest was {hero.id} trying to finish at {place.name}?",
            answer=f"{hero.id} was trying to {quest}. That was the adventure goal at {place.name}.",
        ),
        QAItem(
            question=f"What did {guide.id} want {hero.id} to do before touching {lever.label}?",
            answer=f"{guide.id} wanted {hero.id} to paraphrase the warning back clearly before using {lever.label}.",
        ),
        QAItem(
            question=f"What did the lever help move on this quest?",
            answer=f"The lever helped move the {f['obstacle'].type}. That made the path open so {hero.id} could go on.",
        ),
    ]
    if f.get("solved"):
        qa.append(
            QAItem(
                question=f"How did {hero.id} finally get past the obstacle?",
                answer=(
                    f"{hero.id} listened, paraphrased the clue, and then pulled {lever.label} "
                    f"the right way. After that, the way opened and the quest could continue."
                ),
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel when the path opened?",
                answer=f"{hero.id} felt happy and steadier at the end, because the careful paraphrase helped the adventure succeed.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    out.append(QAItem(
        question="What does it mean to paraphrase something?",
        answer="To paraphrase means to say the same idea again using different words that still keep the original meaning.",
    ))
    out.append(QAItem(
        question="What is a lever?",
        answer="A lever is a bar or handle that can help move something heavy or stuck when you push or pull it the right way.",
    ))
    out.append(QAItem(
        question="What is a quest?",
        answer="A quest is a goal or mission in an adventure where someone goes looking for something or tries to solve a problem.",
    ))
    if f["lever_key"] == "open_gate":
        out.append(QAItem(
            question="Why would a gate lever be useful?",
            answer="A gate lever is useful because it can help open a stuck gate without needing to push the whole heavy gate by hand.",
        ))
    elif f["lever_key"] == "lift_bridge":
        out.append(QAItem(
            question="Why would a bridge lever be useful?",
            answer="A bridge lever is useful because it can lower or lift a bridge so someone can cross to the other side.",
        ))
    else:
        out.append(QAItem(
            question="Why would a portcullis lever be useful?",
            answer="A portcullis lever is useful because it can lift heavy bars high enough for a traveler to pass through safely.",
        ))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "stone_hall": PLACES["stone_hall"],
    "river_room": PLACES["river_room"],
    "gate_yard": PLACES["gate_yard"],
}

CURATED = [
    StoryParams(place="gate_yard", quest="find_key", item="key", lever="open_gate", name="Mina", gender="girl", guide="old owl", trait="brave"),
    StoryParams(place="river_room", quest="reach_map", item="map", lever="lift_bridge", name="Arlo", gender="boy", guide="wise turtle", trait="careful"),
    StoryParams(place="stone_hall", quest="save_friend", item="friend", lever="raise_portcullis", name="Ivy", gender="girl", guide="old owl", trait="quick-thinking"),
]

GUIDES = ["old owl", "wise turtle", "helpful fox"]
GENDER_NAMES = {
    "girl": GIRL_NAMES,
    "boy": BOY_NAMES,
}


ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- quest_name(Q).
item(I) :- quest_item(I).
lever(L) :- lever_name(L).

good_story(P, Q, I, L) :- setting(P), quest_name(Q), quest_item(I), lever_name(L),
                          needs_lever(Q, L), item_can_be_helped(I, L).

can_paraphrase(G) :- guide(G).
valid_story(P, Q, I, L, G) :- good_story(P, Q, I, L), can_paraphrase(G).
#show valid_story/5.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for q in QUESTS:
        lines.append(asp.fact("quest_name", q))
    for i in QUEST_OBJECTS:
        lines.append(asp.fact("quest_item", i))
    for l in LEVERS:
        lines.append(asp.fact("lever_name", l))
    for q, l in [("find_key", "open_gate"), ("reach_map", "lift_bridge"), ("save_friend", "raise_portcullis")]:
        lines.append(asp.fact("needs_lever", q, l))
    for i, l in [("key", "open_gate"), ("map", "lift_bridge"), ("friend", "raise_portcullis")]:
        lines.append(asp.fact("item_can_be_helped", i, l))
    for g in GUIDES:
        lines.append(asp.fact("guide", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out = []
    for place in SETTINGS:
        for q in QUESTS:
            for item in QUEST_OBJECTS:
                for lever in LEVERS:
                    if (
                        (q == "find_key" and lever == "open_gate" and item == "key")
                        or (q == "reach_map" and lever == "lift_bridge" and item == "map")
                        or (q == "save_friend" and lever == "raise_portcullis" and item == "friend")
                    ):
                        for guide in GUIDES:
                            out.append((place, q, item, lever, guide))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld about a quest, a lever, and paraphrasing a clue."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--item", choices=QUEST_OBJECTS)
    ap.add_argument("--lever", choices=LEVERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
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
    combos = valid_combos()
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))
              and (getattr(args, "lever", None) is None or c[3] == getattr(args, "lever", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None):
        combos = [c for c in combos if getattr(args, "gender", None) in {"girl", "boy"}]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, item, lever, guide = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if gender not in _safe_lookup(QUEST_OBJECTS, item).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(GENDER_NAMES, gender))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    guide = getattr(args, "guide", None) or guide
    return StoryParams(place=place, quest=quest, item=item, lever=lever, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.quest, params.item, params.lever,
                 params.name, params.gender, params.guide, params.trait)
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
        print(asp_program("#show valid_story/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, item, lever, guide) combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.quest} at {p.place} (item: {p.item}, lever: {p.lever})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
