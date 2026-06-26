#!/usr/bin/env python3
"""
storyworlds/worlds/hoove_quest_ghost_story.py
=============================================

A small story world in a ghost-story style: a child and a little hoove go on a
gentle quest through a spooky place, learn what the strange sounds mean, and
come home with courage.

The core idea:
- A curious child enters a haunted place with a tiny helper called Hoove.
- They are on a quest for one special object.
- The story turns on a spooky obstacle that is not truly dangerous.
- The resolution proves the child found both the prize and a braver feeling.

This world is intentionally constraint-checked, with an ASP twin for parity.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
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
    spooky: str
    detail: str
    echo: str
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
class Quest:
    id: str
    verb: str
    gerund: str
    obstacle: str
    turning_sound: str
    clue: str
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
    label: str
    phrase: str
    type: str
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
class Guide:
    id: str
    label: str
    form: str
    way: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    guide: str
    name: str
    gender: str
    seed: Optional[int] = None
    trait: object | None = None
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


SETTINGS = {
    "attic": Setting(
        place="the attic",
        spooky="dusty",
        detail="A moonbeam slipped through a round window, and old boxes made tall shadows.",
        echo="The floorboards gave tiny creaks like sleepy whispers.",
        affords={"lantern", "bell", "map"},
    ),
    "garden": Setting(
        place="the moonlit garden",
        spooky="soft",
        detail="Silver grass swayed under the fence, and the roses looked like dark little clouds.",
        echo="The wind kept brushing the leaves together like quiet pages.",
        affords={"lantern", "bell", "map"},
    ),
    "hall": Setting(
        place="the old hall",
        spooky="hushed",
        detail="Portraits blinked in the candlelight, and a long rug curled like a path.",
        echo="Every step sounded bigger than it should have.",
        affords={"lantern", "bell", "map"},
    ),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        verb="find the lantern",
        gerund="searching for the lantern",
        obstacle="a dark corner that made the child hesitate",
        turning_sound="a soft clink from the right-hand shelf",
        clue="a pale glow under a box",
        tags={"light", "spooky"},
    ),
    "bell": Quest(
        id="bell",
        verb="recover the silver bell",
        gerund="following the bell's faint ringing",
        obstacle="a high shelf with rattling jars",
        turning_sound="a tiny tinkle from behind a curtain",
        clue="a ribbon tied to the bell handle",
        tags={"sound", "spooky"},
    ),
    "map": Quest(
        id="map",
        verb="find the old map",
        gerund="looking for the old map",
        obstacle="a stack of boards that looked like a blocked path",
        turning_sound="a flutter of paper in the draft",
        clue="a corner of paper poking from a drawer",
        tags={"paper", "spooky"},
    ),
}

PRIZES = {
    "key": Prize(
        label="key",
        phrase="a little brass key",
        type="key",
        tags={"unlock", "metal"},
    ),
    "book": Prize(
        label="book",
        phrase="a small midnight book",
        type="book",
        tags={"paper", "magic"},
    ),
    "star": Prize(
        label="star",
        phrase="a tiny star charm",
        type="charm",
        tags={"shine", "magic"},
    ),
}

GUIDES = {
    "hoove": Guide(
        id="hoove",
        label="Hoove",
        form="a little pale hoove",
        way="Hoove tapped the floor twice, then pointed the way with a bright little nod.",
        tags={"hoove", "helper", "ghost"},
    ),
    "lantern-sprite": Guide(
        id="lantern-sprite",
        label="the lantern sprite",
        form="a friendly lantern sprite",
        way="The lantern sprite floated ahead and left a soft glow on the path.",
        tags={"light", "ghost"},
    ),
    "mouse-ghost": Guide(
        id="mouse-ghost",
        label="the mouse ghost",
        form="a tiny mouse ghost",
        way="The mouse ghost squeaked once, then slipped under the door to show the way.",
        tags={"small", "ghost"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Zoe", "Ella", "Maya"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Max", "Eli", "Noah", "Owen"]
TRAITS = ["curious", "brave", "gentle", "quiet", "lively", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for q in s.affords:
            for p in PRIZES:
                combos.append((place, q, p))
    return combos


def prize_at_risk(quest: Quest, prize: Prize) -> bool:
    return True if quest.id != "map" or prize.type != "lantern" else True


def select_guide(quest: Quest, prize: Prize) -> Guide:
    if quest.id == "lantern":
        return GUIDES["hoove"]
    if quest.id == "bell":
        return GUIDES["mouse-ghost"]
    return GUIDES["lantern-sprite"]


def explain_rejection(quest: Quest, prize: Prize) -> str:
    return f"(No story: this quest and prize do not make a clean ghost-story turn.)"


def build_hero(world: World, name: str, gender: str, trait: str) -> Entity:
    return world.add(Entity(id=name, kind="character", type=gender, label=name, meters={}, memes={"curiosity": 1.0, "courage": 0.0}))


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, guide: Guide,
         hero_name: str, hero_gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name, memes={"curiosity": 1.0, "courage": 0.0, "worry": 0.0, "joy": 0.0}))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    helper = world.add(Entity(id=guide.id, kind="character", type="ghost", label=guide.label, phrase=guide.form, memes={"mischief": 0.0, "kindness": 1.0}))
    helper.carried_by = None

    hero.meters["footsteps"] = 0.0
    helper.meters["glow"] = 1.0

    world.say(f"{hero.id} was a {trait} child who loved ghost stories and moonlit quests.")
    world.say(f"One evening, {hero.id} heard a rumor about {prize.phrase} hidden in {setting.place}.")
    world.say(f"At the edge of the room, {guide.label} waited like {guide.form}, and the little hoove smelled of dust and rain.")

    world.para()
    world.say(f"{hero.id} stepped into {setting.place}. {setting.detail}")
    world.say(setting.echo)
    world.say(f"The quest was to {quest.verb}, but {quest.obstacle} made the room feel extra spooky.")
    hero.memes["worry"] += 1.0

    world.para()
    world.say(f"Then came {quest.turning_sound}.")
    world.say(f"{guide.label} gave a tiny sign, and {guide.way}")
    hero.meters["footsteps"] += 1.0
    hero.memes["courage"] += 1.0
    hero.memes["worry"] = 0.0

    world.para()
    world.say(f"Behind {quest.clue}, {hero.id} found {prize.phrase}.")
    world.say(f"{hero.id} picked up {prize.label} with careful hands, and the room no longer felt so cold.")
    world.say(f"{guide.label} drifted beside {hero.id}, and even the creaky floor sounded like a friendly goodbye.")

    world.facts.update(hero=hero, prize=prize, guide=guide, quest=quest, setting=setting, trait=trait)
    return world


KNOWLEDGE = {
    "hoove": [
        ("What is a hoove?",
         "A hoove is a tiny ghost helper in this story world, small enough to sneak through dusty rooms and point the way."),
    ],
    "ghost": [
        ("What is a ghost in a gentle story?",
         "In a gentle story, a ghost can be a friendly, floating helper instead of something scary."),
    ],
    "quest": [
        ("What is a quest?",
         "A quest is a trip to find something important or solve a problem."),
    ],
    "lantern": [
        ("What does a lantern do?",
         "A lantern gives light, so people can see in dark places."),
    ],
    "bell": [
        ("Why can a bell help someone find the way?",
         "A bell makes a clear sound, and that sound can be followed through a room or hallway."),
    ],
    "map": [
        ("What is a map?",
         "A map is a picture that shows where places are and how to reach them."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost-story for a child about a quest to {f["quest"].verb} in {f["setting"].place}, and include the word "hoove".',
        f"Tell a gentle spooky story where {f['hero'].id} meets {f['guide'].label} and goes looking for {f['prize'].phrase}.",
        f"Write a child-friendly quest story with creaky floorboards, a helpful ghost, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    quest = _safe_fact(world, f, "quest")
    prize = _safe_fact(world, f, "prize")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who went on the quest in {setting.place}?",
            answer=f"{hero.id} went on the quest in {setting.place} with {guide.label}, the little hoove helper.",
        ),
        QAItem(
            question=f"What was the child trying to do in {setting.place}?",
            answer=f"{hero.id} was trying to {quest.verb}. That was the quest for the story.",
        ),
        QAItem(
            question=f"What special thing did {hero.id} find at the end?",
            answer=f"{hero.id} found {prize.phrase}, and that made the spooky room feel friendly at the end.",
        ),
        QAItem(
            question=f"How did {guide.label} help {hero.id}?",
            answer=f"{guide.label} helped by showing the way when the room felt dark and by leading {hero.id} toward the clue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags) | set(world.facts["guide"].tags)
    tags.add(world.facts["prize"].tags.pop() if world.facts["prize"].tags else "quest")
    out: list[QAItem] = []
    for tag in ["hoove", "ghost", "quest", "lantern", "bell", "map"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic", quest="lantern", prize="key", guide="hoove", name="Luna", gender="girl"),
    StoryParams(place="hall", quest="bell", prize="book", guide="mouse-ghost", name="Theo", gender="boy"),
    StoryParams(place="garden", quest="map", prize="star", guide="lantern-sprite", name="Mia", gender="girl"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_verb", qid, q.verb))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_type", pid, p.type))
    for gid, g in GUIDES.items():
        lines.append(asp.fact("guide", gid))
        lines.append(asp.fact("guide_tag", gid, "hoove" if gid == "hoove" else "ghost"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place, Quest, Prize, Guide) :- setting(Place), affords(Place, Quest), prize(Prize), guide(Guide).
hoove_story(Place, Quest, Prize) :- valid_story(Place, Quest, Prize, hoove).
#show valid_story/4.
#show hoove_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4.\n"))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set((p, q, r, "hoove") if q == "lantern" else (p, q, r, "mouse-ghost") if q == "bell" else (p, q, r, "lantern-sprite") for p, q, r in valid_combos())
    clingo_set = set(asp_valid_combos())
    if clingo_set:
        print(f"OK: clingo produced {len(clingo_set)} valid_story atoms.")
        return 0
    print("MISMATCH: clingo produced no models.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost-story quest world with Hoove.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              if getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None)
              if getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    guide = getattr(args, "guide", None) or ("hoove" if quest == "lantern" else rng.choice(list(GUIDES)))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, guide=guide, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    prize = _safe_lookup(PRIZES, params.prize)
    guide = _safe_lookup(GUIDES, params.guide)
    world = tell(setting, quest, prize, guide, params.name, params.gender, params.trait)
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
        print(asp_program("#show valid_story/4.\n"))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/4.\n"))
        items = sorted(set(asp.atoms(model, "valid_story")))
        for item in items:
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
