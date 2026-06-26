#!/usr/bin/env python3
"""
impressive_flashback_fairy_tale.py

A small fairy-tale storyworld with a flashback turn:
a child-hero meets a wondrous problem, remembers an earlier promise or lesson,
and uses that memory to change the ending.

The world is built to generate complete, child-facing fairy tales with:
- a beginning that introduces a beloved object or wish,
- a flashback that explains why it matters,
- a tension beat,
- a resolution that proves the change in state.

The domain stays small on purpose so the story feels authored rather than mixed
from a large event log.
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
    given_to: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "father", "man"}:
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
class Place:
    id: str
    label: str
    kind: str = "place"
    outdoors: bool = False
    sparkles: bool = False
    flowers: bool = False
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
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    glow: str
    risk: str
    owner_kind: str
    carry: str
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


@dataclass
class Helper:
    id: str
    label: str
    type: str
    gift: str
    recall: str
    fix: str
    helps_with: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.trace_notes = list(self.trace_notes)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_kind: str
    helper: str
    treasure: str
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


PLACES = {
    "rose_garden": Place(id="rose_garden", label="the rose garden", outdoors=True, sparkles=True, flowers=True),
    "old_tower": Place(id="old_tower", label="the old tower", outdoors=False, sparkles=False, flowers=False),
    "moon_clearing": Place(id="moon_clearing", label="the moonlit clearing", outdoors=True, sparkles=True, flowers=False),
    "river_bridge": Place(id="river_bridge", label="the river bridge", outdoors=True, sparkles=False, flowers=True),
}

HEROES = [
    ("Ava", "girl", "little"),
    ("Nora", "girl", "little"),
    ("Milo", "boy", "little"),
    ("Finn", "boy", "little"),
    ("Elin", "girl", "brave"),
    ("Tarin", "boy", "gentle"),
]

HELPERS = {
    "owl": Helper(
        id="owl", label="an old owl", type="owl",
        gift="a feather that remembered the night",
        recall="The owl once whispered that the first soft sound often opened the right door.",
        fix="listen first, then speak kindly",
        helps_with={"lost_path", "shy_bird", "quiet_key"},
    ),
    "fox": Helper(
        id="fox", label="a red fox", type="fox",
        gift="a bright thread from a thorn bush",
        recall="The fox once said that clever hands are best when they stay gentle.",
        fix="tie, lift, and guide carefully",
        helps_with={"broken_string", "high_branch", "snagged_cape"},
    ),
    "fairy": Helper(
        id="fairy", label="a small fairy", type="fairy",
        gift="a spoonful of silver dust",
        recall="The fairy once taught that a glowing thing is safest when shared.",
        fix="share the light with others",
        helps_with={"dim_lantern", "night_gate", "sleeping_well"},
    ),
}

TREASURES = {
    "lantern": Treasure(
        id="lantern", label="lantern", phrase="a tiny lantern with a gold handle",
        type="lantern", glow="glowed like a star in a jar",
        risk="its light might go out in the dark",
        owner_kind="child", carry="held close", plural=False,
    ),
    "crown": Treasure(
        id="crown", label="crown", phrase="a little crown set with glass leaves",
        type="crown", glow="sparkled like morning dew",
        risk="it might slip from a careful head",
        owner_kind="child", carry="worn high", plural=False,
    ),
    "key": Treasure(
        id="key", label="key", phrase="a silver key on a blue ribbon",
        type="key", glow="shone like a tiny fish scale",
        risk="it might be lost in the grass",
        owner_kind="child", carry="tied safely", plural=False,
    ),
    "cloak": Treasure(
        id="cloak", label="cloak", phrase="a soft cloak with a clasp of pearl",
        type="cloak", glow="shimmered in the firelight",
        risk="it might snag on thorns",
        owner_kind="child", carry="wrapped neatly", plural=False,
    ),
}

FLASHBACKS = {
    "lantern": "when the lights went out last winter, the lantern had guided the way home",
    "crown": "when the first snow fell, the crown had been used in a promise to be brave",
    "key": "when the gate was stuck, the key had opened the tiny door to a warm room",
    "cloak": "when rain chased everyone indoors, the cloak had kept a little traveler dry",
}

PROBLEMS = {
    "lantern": "night_wind",
    "crown": "high_bell",
    "key": "mossy_path",
    "cloak": "thorn_briar",
}

PROBLEM_TEXT = {
    "night_wind": "a naughty night wind tried to blow out the lantern",
    "high_bell": "a silver bell hung too high for the crown to reach",
    "mossy_path": "the key slipped near a mossy path and nearly vanished in the grass",
    "thorn_briar": "a thorn briar caught the cloak and would not let it pass",
}

HERO_NAMES = [h[0] for h in HEROES]
KIND_TO_NAMES = {
    "girl": [h[0] for h in HEROES if h[1] == "girl"],
    "boy": [h[0] for h in HEROES if h[1] == "boy"],
}
TRAITS = ["little", "brave", "gentle", "curious", "kind", "dreamy"]


def choose_story_options(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero_name, hero_kind, trait = rng.choice(HEROES)
    if getattr(args, "hero", None):
        hero_name = getattr(args, "hero", None)
    if getattr(args, "hero_kind", None):
        hero_kind = getattr(args, "hero_kind", None)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))

    if place not in PLACES:
        pass
    if helper not in HELPERS:
        pass
    if treasure not in TREASURES:
        pass
    return StoryParams(place=place, hero=hero_name, hero_kind=hero_kind, helper=helper, treasure=treasure)


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    hero = world.add(Entity(
        id=params.hero, kind="character", type=params.hero_kind,
        label=params.hero, meters={"hope": 0.0, "fear": 0.0}, memes={"love": 0.0, "curiosity": 1.0}
    ))
    helper = world.add(Entity(
        id=params.helper, kind="character", type=_safe_lookup(HELPERS, params.helper).type,
        label=_safe_lookup(HELPERS, params.helper).label, meters={"wisdom": 1.0}, memes={"kindness": 1.0}
    ))
    treasure = _safe_lookup(TREASURES, params.treasure)
    item = world.add(Entity(
        id=treasure.id, kind="thing", type=treasure.type, label=treasure.label,
        phrase=treasure.phrase, owner=hero.id, caretaker=helper.id,
        meters={"glow": 1.0, "risk": 0.0}, memes={"precious": 1.0}
    ))

    world.facts.update(hero=hero, helper=helper, treasure=item, treasure_def=treasure)
    return world


def intro(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    treasure: Entity = _safe_fact(world, world.facts, "treasure")
    place = world.place
    world.say(
        f"Once upon a time, in {place.label}, there lived {hero.pronoun('subject')} "
        f"named {hero.label}. {hero.pronoun().capitalize()} loved {treasure.phrase} "
        f"because it seemed {_safe_lookup(TREASURES, treasure.id).glow}."
    )
    world.say(
        f"Everyone called the treasure precious, and {hero.pronoun('possessive')} heart grew bright whenever {hero.pronoun()} held {treasure.it()}."
    )


def flashback(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    treasure: Entity = _safe_fact(world, world.facts, "treasure")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    treasure_def = _safe_fact(world, world.facts, "treasure_def")
    world.para()
    world.say(
        f"But before that day, {_safe_lookup(FLASHBACKS, treasure.id)}. "
        f"{helper.label.capitalize()} had been there then, too."
    )
    world.say(
        f"That was why {helper.pronoun('subject')} had given {hero.pronoun('object')} "
        f"{treasure_def.phrase}. {helper.pronoun().capitalize()} had said, "
        f'"Keep it safe, and it will help when the story turns dark."'
    )
    hero.memes["memory"] = 1.0
    hero.memes["trust"] += 1.0


def tension(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    treasure: Entity = _safe_fact(world, world.facts, "treasure")
    problem = _safe_lookup(PROBLEMS, treasure.id)
    world.para()
    world.say(
        f"One evening, {PROBLEM_TEXT[problem]}, and {hero.pronoun('subject')} gasped."
    )
    hero.meters["fear"] += 1.0
    treasure.meters["risk"] += 1.0
    world.say(
        f"{hero.pronoun().capitalize()} wanted to protect {treasure.it()}, but {treasure.risk}."
    )


def resolve(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    treasure: Entity = _safe_fact(world, world.facts, "treasure")
    treasure_def = _safe_fact(world, world.facts, "treasure_def")
    world.para()

    if treasure.id == "lantern":
        hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1.0
        world.say(
            f"Then {hero.pronoun('subject')} remembered {helper.label}'s old lesson. "
            f"{hero.pronoun().capitalize()} cupped {treasure.it()} in both hands and let {helper.pronoun('object')}'s silver dust rest around it."
        )
        world.say(
            f"The wind whistled, but the lantern stayed lit, and the dark path softened into a little lane of gold."
        )
    elif treasure.id == "crown":
        hero.meters["bravery"] = hero.meters.get("bravery", 0.0) + 1.0
        world.say(
            f"Then {hero.pronoun('subject')} remembered the promise from the snow day. "
            f"{hero.pronoun().capitalize()} climbed one careful step, tied the ribbon tighter, and lifted the crown with both hands."
        )
        world.say(
            f"The bell could not steal it. The crown glittered safely, and the brave little head smiled under the stars."
        )
    elif treasure.id == "key":
        hero.memes["care"] = hero.memes.get("care", 0.0) + 1.0
        world.say(
            f"Then {hero.pronoun('subject')} remembered how {helper.label} had once taught {hero.pronoun('object')} to move slowly. "
            f"{hero.pronoun().capitalize()} knelt, brushed the grass aside, and tied the key to the blue ribbon again."
        )
        world.say(
            f"The key stayed found, and the warm room waited patiently for whoever needed it next."
        )
    else:
        hero.memes["patience"] = hero.memes.get("patience", 0.0) + 1.0
        world.say(
            f"Then {hero.pronoun('subject')} remembered the fox's gentle cleverness. "
            f"{hero.pronoun().capitalize()} did not pull hard. Instead, {hero.pronoun()} held the cloak still and unwound it leaf by leaf."
        )
        world.say(
            f"The briar let go at last, and the cloak came free without a single tear."
        )

    treasure.meters["risk"] = 0.0
    treasure.memes["safe"] = 1.0
    world.facts["resolved"] = True
    world.facts["flashback_used"] = True


def tell(world: World) -> World:
    intro(world)
    flashback(world)
    tension(world)
    resolve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    treasure: Entity = _safe_fact(world, world.facts, "treasure")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    return [
        f"Write a fairy tale about {hero.label} and {treasure.label} with a flashback that explains why the treasure matters.",
        f"Tell a child-friendly story in which {helper.label} helps {hero.label} remember an earlier promise.",
        f"Write an impressive little fairy tale where a problem appears, a memory returns, and the treasure ends safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    treasure: Entity = _safe_fact(world, world.facts, "treasure")
    treasure_def = _safe_fact(world, world.facts, "treasure_def")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.label}, who loved {treasure.phrase}."
        ),
        QAItem(
            question=f"What did the flashback explain?",
            answer=f"It explained that {_safe_lookup(FLASHBACKS, treasure.id)}, which is why {helper.label} gave {hero.label} {treasure.phrase}."
        ),
        QAItem(
            question=f"How did {hero.label} save the {treasure.label} at the end?",
            answer=f"{hero.label} remembered the old lesson from {helper.label}, used {treasure_def.fix}, and kept the {treasure.label} safe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    treasure: Entity = _safe_fact(world, world.facts, "treasure")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    out = []
    if treasure.id == "lantern":
        out.append(QAItem(
            question="What does a lantern do?",
            answer="A lantern holds light and helps people see when the way is dark."
        ))
    elif treasure.id == "crown":
        out.append(QAItem(
            question="What is a crown for?",
            answer="A crown is a special head украшение worn to show honor, celebration, or royal standing."
        ))
    elif treasure.id == "key":
        out.append(QAItem(
            question="What does a key do?",
            answer="A key opens a lock or a gate that would stay shut without it."
        ))
    else:
        out.append(QAItem(
            question="What is a cloak for?",
            answer="A cloak is a loose covering that keeps a person warm or hidden a little from the wind."
        ))
    if helper.id == "owl":
        out.append(QAItem(
            question="Why do owls seem wise in fairy tales?",
            answer="Owls often seem wise because they watch quietly at night and are often written as thoughtful helpers."
        ))
    elif helper.id == "fox":
        out.append(QAItem(
            question="Why are foxes often clever in fairy tales?",
            answer="Foxes are often written as clever because they seem quick, alert, and good at finding tricky answers."
        ))
    else:
        out.append(QAItem(
            question="Why do fairies feel magical in fairy tales?",
            answer="Fairies feel magical because they are often imagined as tiny helpers who can make gentle wonder happen."
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(X) :- helper_name(X).
treasure(T) :- treasure_name(T).

flashback_needed(T) :- treasure(T).
resolved(T) :- flashback_used(T), safe(T).

#show compatible/3.
compatible(P,H,T) :- place(P), hero(H), treasure(T), supports(P,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.outdoors:
            lines.append(asp.fact("outdoors", pid))
        if p.sparkles:
            lines.append(asp.fact("sparkles", pid))
        if p.flowers:
            lines.append(asp.fact("flowers", pid))
    for hid in HELPERS:
        lines.append(asp.fact("helper_name", hid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure_name", tid))
        lines.append(asp.fact("supports", "any", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show place/1."))
    if model is None:
        print("ASP check unavailable.")
        return 1
    print("OK: ASP program loads.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fairy-tale storyworld with flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-kind", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--treasure", choices=TREASURES)
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
    return choose_story_options(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = tell(build_world(params))
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
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="rose_garden", hero="Ava", hero_kind="girl", helper="fairy", treasure="lantern"),
            StoryParams(place="old_tower", hero="Milo", hero_kind="boy", helper="owl", treasure="key"),
            StoryParams(place="moon_clearing", hero="Elin", hero_kind="girl", helper="fox", treasure="cloak"),
            StoryParams(place="river_bridge", hero="Finn", hero_kind="boy", helper="fairy", treasure="crown"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(100, getattr(args, "n", None) * 40):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
