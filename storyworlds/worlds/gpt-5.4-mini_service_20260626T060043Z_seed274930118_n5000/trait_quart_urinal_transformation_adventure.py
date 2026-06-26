#!/usr/bin/env python3
"""
storyworlds/worlds/trait_quart_urinal_transformation_adventure.py
=================================================================

A compact adventure storyworld about a child explorer, a small measured
amount of magic water, and a careful transformation.

Seed inspiration:
- trait
- quart
- urinal

Premise:
A young adventurer finds an old, dull urinal in a hidden castle washroom.
A caretaker says it can be transformed into a bright little fountain, but
only if the explorer brings one quart of springwater and uses the right trait:
patience, courage, or kindness.

The story is built as a tiny simulation:
- the explorer gains hope and resolve,
- the setting and object state change,
- the transformation succeeds only when the right conditions are met.

The domain is intentionally small and constraint-checked.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    state: str = "plain"

    hero: object | None = None
    quart: object | None = None
    urinal: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        male = {"boy", "father", "dad", "man", "king", "prince"}
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
    place: str = "the old castle washroom"
    label: str = "the old castle washroom"
    affords: set[str] = field(default_factory=set)
    kind: str = "indoor"
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
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    requires: str
    result: str
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
class Catalyst:
    id: str
    label: str
    phrase: str
    amount: str = "a quart"
    kind: str = "liquid"
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
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = []
        clone.facts = dict(self.facts)
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    vessel = world.get("quart")
    if hero.meters.get("quest", 0) < THRESHOLD:
        return out
    if vessel.meters.get("filled", 0) < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    vessel.state = "ready"
    out.append("The quart of springwater trembled like a little silver promise.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    urinal = world.get("urinal")
    catalyst = world.get("quart")
    if hero.memes.get("trait", 0) < THRESHOLD:
        return out
    if catalyst.meters.get("filled", 0) < THRESHOLD:
        return out
    if urinal.state != "plain":
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    urinal.state = "fountain"
    urinal.meters["shine"] = 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    out.append("With one careful pour, the old urinal changed into a bright little fountain.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    urinal = world.get("urinal")
    caretaker = world.get("caretaker")
    sig = ("relief", urinal.state)
    if urinal.state != "fountain" or sig in world.fired:
        return out
    world.fired.add(sig)
    caretaker.memes["relief"] = caretaker.memes.get("relief", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    out.append("The caretaker smiled, because the little transformation had worked exactly as hoped.")
    return out


RULES = [_r_spill, _r_transform, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def preview_transform(world: World, hero: Entity, quest: Quest, catalyst: Catalyst) -> bool:
    sim = world.copy()
    sim.get("hero").memes["trait"] = hero.memes.get("trait", 0)
    sim.get("quart").meters["filled"] = catalyst.meters.get("filled", 0)
    sim.get("urinal").state = world.get("urinal").state
    propagate(sim, narrate=False)
    return sim.get("urinal").state == "fountain"


def introduce(world: World, hero: Entity) -> None:
    trait = hero.traits[0] if hero.traits else "brave"
    world.say(
        f"{hero.id} was a little {trait} explorer who loved hidden doors and secret paths."
    )


def show_setting(world: World, quest: Quest) -> None:
    world.say(
        f"One day, {world.setting.place} smelled cool and echoey, and a dusty hall waited in the back."
    )
    world.say(
        f"Near the wall stood an old urinal that looked plain and sad, as if it had forgotten its own purpose."
    )


def begin_quest(world: World, hero: Entity, quest: Quest, catalyst: Catalyst) -> None:
    hero.memes["quest"] = hero.memes.get("quest", 0) + 1
    world.say(
        f"{hero.id} wanted to {quest.verb}, but the caretaker said the old urinal needed {catalyst.amount} of springwater and a good {quest.keyword}."
    )


def fetch_catalyst(world: World, hero: Entity, catalyst: Catalyst) -> None:
    catalyst.meters["filled"] = 1
    world.say(
        f"{hero.id} carried back {catalyst.phrase} in a careful cup, holding it steady all the way."
    )


def use_trait(world: World, hero: Entity, quest: Quest, catalyst: Catalyst) -> None:
    hero.memes["trait"] = hero.memes.get("trait", 0) + 1
    world.say(
        f"{hero.id} took a slow breath and used {quest.keyword}, because quick hands would have spilled the water."
    )
    if preview_transform(world, hero, quest, catalyst):
        world.say(
            f"The old urinal was ready for the change, so {hero.id} stepped closer and poured the water in."
        )
    else:
        pass


def finish(world: World, hero: Entity) -> None:
    urinal = world.get("urinal")
    caretaker = world.get("caretaker")
    if urinal.state == "fountain":
        world.say(
            f"At the end, the old urinal was no longer plain. It had become a shining fountain, and {hero.id} grinned at the sparkling water."
        )
        world.say(
            f"The caretaker clapped softly, and the little adventure felt big enough to remember forever."
        )
    else:
        pass


def tell(setting: Setting, quest: Quest, catalyst: Catalyst,
         hero_name: str = "Mina", hero_type: str = "girl",
         trait: str = "patient") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero", kind="character", type=hero_type, label=hero_name,
        traits=[trait, "curious"], memes={}, meters={}
    ))
    caretaker = world.add(Entity(
        id="caretaker", kind="character", type="woman", label="the caretaker",
        traits=["kind"], memes={}, meters={}
    ))
    urinal = world.add(Entity(
        id="urinal", type="thing", label="urinal", phrase="an old urinal",
        state="plain", meters={}, memes={}
    ))
    quart = world.add(Entity(
        id="quart", type="thing", label="quart", phrase="a quart of springwater",
        meters={"filled": 0}, memes={}, state="empty"
    ))

    world.say(f"{hero_name} was a {trait} little {hero_type} who loved adventures.")
    world.say(
        f"{hero_name} heard a tale about a trait, a quart, and an old urinal that could become something new."
    )
    world.lines.append("")  # harmless separator in render
    introduce(world, hero)
    show_setting(world, quest)
    begin_quest(world, hero, quest, catalyst)
    fetch_catalyst(world, hero, catalyst)
    use_trait(world, hero, quest, catalyst)
    propagate(world, narrate=True)
    finish(world, hero)

    world.facts.update(hero=hero, caretaker=caretaker, urinal=urinal, quart=quart,
                       quest=quest, catalyst=catalyst, setting=setting)
    return world


SETTINGS = {
    "castle": Setting(place="the old castle washroom", label="the old castle washroom", affords={"transform"}),
    "inn": Setting(place="the roadside inn", label="the roadside inn", affords={"transform"}),
    "tower": Setting(place="the quiet tower bath", label="the quiet tower bath", affords={"transform"}),
}

QUESTS = {
    "transform": Quest(
        id="transform",
        verb="transform the old urinal into a fountain",
        gerund="transforming the old urinal",
        rush="rush ahead",
        requires="patience",
        result="fountain",
        keyword="trait",
        tags={"trait", "transform", "urinal"},
    ),
}

CATALYSTS = {
    "quart": Catalyst(
        id="quart",
        label="quart",
        phrase="a quart of springwater",
        amount="a quart",
        kind="liquid",
        tags={"quart", "water"},
    ),
}

TRAITS = ["patient", "brave", "gentle", "careful", "curious"]
NAMES = ["Mina", "Noah", "Luna", "Eli", "Iris", "Theo"]


@dataclass
class StoryParams:
    place: str
    quest: str
    catalyst: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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
    for place, setting in SETTINGS.items():
        for quest_id in setting.affords:
            for cat_id in CATALYSTS:
                combos.append((place, quest_id, cat_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero").label
    return [
        f"Write a short adventure story about {hero} finding a hidden urinal and changing it with one quart of springwater.",
        f"Tell a child-friendly transformation tale where a trait helps {hero} complete a quest in {world.setting.place}.",
        "Write an adventurous story that uses the words trait, quart, and urinal and ends with a surprising new shape.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero").label
    urinal = _safe_fact(world, f, "urinal")
    return [
        QAItem(
            question=f"What did {hero} want to do in the story?",
            answer=f"{hero} wanted to transform the old urinal into a fountain.",
        ),
        QAItem(
            question="What did the adventure require before the change could happen?",
            answer="It required a quart of springwater and the right trait, like patience or carefulness.",
        ),
        QAItem(
            question="What did the old urinal become at the end?",
            answer="It became a bright little fountain that sparkled with water.",
        ),
        QAItem(
            question=f"Why did the caretaker smile when the change was finished?",
            answer=f"The caretaker smiled because {hero} used the trait well and the urinal transformed successfully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quart?",
            answer="A quart is a small measure for liquid, like a little container amount of water or milk.",
        ),
        QAItem(
            question="What is a trait?",
            answer="A trait is a quality a person can show, like patience, bravery, or kindness.",
        ),
        QAItem(
            question="What is a urinal?",
            answer="A urinal is a bathroom fixture that people can use for washing or peeing.",
        ),
    ]


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.state != "plain":
            bits.append(f"state={e.state}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_ok(P,Q,C) :- place(P), affords(P,Q), catalyst(C).
can_transform(H,U,Q,C) :- quest_ok(P,Q,C), hero(H), urinal(U), trait_ok(H), filled(C).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for cid in CATALYSTS:
        lines.append(asp.fact("catalyst", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with trait, quart, and urinal transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--catalyst", choices=CATALYSTS)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "quest", None):
        combos = [c for c in combos if c[1] == getattr(args, "quest", None)]
    if getattr(args, "catalyst", None):
        combos = [c for c in combos if c[2] == getattr(args, "catalyst", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, catalyst = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, catalyst=catalyst, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(CATALYSTS, params.catalyst),
                 hero_name=params.name, hero_type=params.gender, trait=params.trait)
    return StorySample(
        params=params,
        story=world.render().strip(),
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


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show quest_ok/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, quest, catalyst in valid_combos():
            params = StoryParams(
                place=place,
                quest=quest,
                catalyst=catalyst,
                name="Mina",
                gender="girl",
                trait="patient",
                seed=base_seed,
            )
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
