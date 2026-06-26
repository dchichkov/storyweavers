#!/usr/bin/env python3
"""
storyworlds/worlds/consumption_inner_monologue_quest_bedtime_story.py
====================================================================

A standalone storyworld for a gentle bedtime tale about consumption:
a child wants one more bedtime bite, thinks through it in an inner monologue,
and completes a small quest with a soft compromise.

Seed premise:
---
At bedtime, a child feels hungry again and wants to keep consuming a snack.
A parent worries that too much nighttime consumption will make sleep hard.
The child thinks quietly, follows a tiny quest, and learns a calmer way to finish.

World model:
---
- Physical meters track fullness, sleepiness, crumbs, and neatness.
- Emotional memes track desire, worry, patience, and comfort.
- State changes drive the prose: choosing, carrying, nibbling, and settling.

This world keeps the style close to a bedtime story: warm, concrete, and gentle.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    snack: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
    place: str = "the bedroom"
    kitchen: str = "the kitchen"
    world: object | None = None
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
class Snack:
    id: str
    label: str
    phrase: str
    mess: str
    fullness: float
    bedtime_fit: str
    vessel: str
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
class Quest:
    id: str
    step1: str
    step2: str
    step3: str
    ending: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    portion: str
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


SNACKS = {
    "apple": Snack("apple", "apple slices", "some apple slices", "crumbly", 0.4, "light", "small plate", {"fruit"}),
    "oatmeal": Snack("oatmeal", "oatmeal", "a warm bowl of oatmeal", "soft", 0.6, "cozy", "little bowl", {"warm"}),
    "banana": Snack("banana", "banana", "a peeled banana", "soft", 0.3, "sleepy", "napkin", {"fruit"}),
    "toast": Snack("toast", "toast", "buttered toast", "crumbly", 0.5, "light", "small plate", {"bread"}),
    "milk": Snack("milk", "milk", "a little cup of milk", "splashy", 0.2, "gentle", "little cup", {"warm"}),
}

TOOLS = {
    "small_plate": Tool("small_plate", "small plate", "a small plate", {"crumbly"}, "a little bit"),
    "little_bowl": Tool("little_bowl", "little bowl", "a little bowl", {"soft"}, "a small helping"),
    "little_cup": Tool("little_cup", "little cup", "a little cup", {"splashy"}, "just a sip"),
    "napkin": Tool("napkin", "napkin", "a soft napkin", {"crumbly", "splashy", "soft"}, "one tidy bite"),
}

QUESTS = {
    "bedside": Quest(
        "bedside",
        "tiptoe to the kitchen",
        "bring the snack back to bed",
        "eat only a little and keep the rest neat",
        "curl up and let sleep come in quietly",
        {"bedtime", "quiet"},
    ),
    "lantern": Quest(
        "lantern",
        "follow the dim lamp glow to the table",
        "choose a gentle portion",
        "drink or nibble slowly",
        "settle under the blanket with a happy sigh",
        {"bedtime", "quiet"},
    ),
    "countstars": Quest(
        "countstars",
        "count three stars in the dark",
        "take three slow bites",
        "put the dish aside when the count is done",
        "close the eyes and dream of bright skies",
        {"bedtime", "counting"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Ben", "Noah", "Sam"]
TRAITS = ["sleepy", "curious", "gentle", "quiet", "stubborn", "softhearted"]


@dataclass
class StoryParams:
    snack: str
    quest: str
    name: str
    gender: str
    parent: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for snack_id, snack in SNACKS.items():
        for quest_id, quest in QUESTS.items():
            if "bedtime" in quest.tags:
                combos.append((snack_id, quest_id))
    return combos


def explain_rejection(snack: Snack) -> str:
    return f"(No story: {snack.label} has no gentle bedtime way to control consumption in this world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about consumption, inner monologue, and a small quest.")
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if getattr(args, "snack", None) and getattr(args, "snack", None) not in SNACKS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos() if (getattr(args, "snack", None) is None or c[0] == getattr(args, "snack", None)) and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    snack_id, quest_id = rng.choice(list(combos))
    snack = _safe_lookup(SNACKS, snack_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(snack=snack_id, quest=quest_id, name=name, gender=gender, parent=parent, trait=trait)


def _say_thought(world: World, hero: Entity, text: str) -> None:
    world.say(f"{hero.pronoun().capitalize()} thought, “{text}.”")


def tell(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"fullness": 0.0, "sleepiness": 0.0}, memes={"desire": 0.0, "comfort": 0.0, "patience": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent", meters={"worry": 0.0}, memes={"worry": 0.0, "tenderness": 0.0}))
    snack = world.add(Entity(id="snack", type="thing", label=_safe_lookup(SNACKS, params.snack).label, phrase=_safe_lookup(SNACKS, params.snack).phrase, caretaker=parent.id, meters={"portion": 1.0, "neatness": 1.0}, memes={"appeal": 1.0}))
    tool = None
    quest = _safe_lookup(QUESTS, params.quest)

    world.say(f"{hero.id} was a little {params.trait} {params.gender} who was ready for bed, but not quite ready to stop thinking about snack time.")
    _say_thought(world, hero, f"I am sleepy, but I am also still a little hungry")
    hero.memes["desire"] += 1.0
    world.say(f"On the bedside table, {snack.phrase} waited like a tiny moonlit treasure.")

    world.para()
    world.say(f"At {world.setting.place}, {hero.id} looked toward {world.setting.kitchen} and began a quiet quest.")
    world.say(f"First, {quest.step1}.")
    if params.snack in {"toast", "apple"}:
        tool = world.add(Entity(id=_safe_lookup(SNACKS, params.snack).vessel, type="thing", label=TOOLS["small_plate"].label, phrase=TOOLS["small_plate"].phrase))
    elif params.snack == "oatmeal":
        tool = world.add(Entity(id="little_bowl", type="thing", label=TOOLS["little_bowl"].label, phrase=TOOLS["little_bowl"].phrase))
    elif params.snack == "milk":
        tool = world.add(Entity(id="little_cup", type="thing", label=TOOLS["little_cup"].label, phrase=TOOLS["little_cup"].phrase))
    else:
        tool = world.add(Entity(id="napkin", type="thing", label=TOOLS["napkin"].label, phrase=TOOLS["napkin"].phrase))

    world.say(f"{parent.label_word} watched the small quest and said, “{hero.id}, if you are going to keep consuming anything tonight, let us do it the gentle way.”")
    parent.memes["worry"] += 1.0

    _say_thought(world, hero, f"Maybe one careful snack is enough")
    world.say(f"{hero.id} chose {tool.phrase} for the snack, because {snack.label} was best with a {_safe_lookup(SNACKS, params.snack).bedtime_fit} portion.")
    world.say(f"Then {quest.step2}.")
    hero.meters["fullness"] += _safe_lookup(SNACKS, params.snack).fullness
    hero.memes["comfort"] += 0.5

    if snack.mess in tool.meters if False else False:
        pass

    if snack.mess == "crumbly":
        hero.meters["crumbs"] = hero.meters.get("crumbs", 0.0) + 1.0
        world.say(f"A few crumbs tried to wander, but the plate kept them together like little sleepy stones.")
    elif snack.mess == "splashy":
        hero.meters["drops"] = hero.meters.get("drops", 0.0) + 1.0
        world.say(f"A tiny drop trembled at the rim, but the cup stayed steady in careful hands.")
    else:
        world.say(f"The snack stayed neat and warm, and the room felt softer for it.")

    if hero.meters["fullness"] >= 0.5:
        hero.meters["sleepiness"] += 0.6
    if hero.meters["sleepiness"] >= 0.5:
        hero.memes["patience"] += 0.5

    world.para()
    world.say(f"{hero.id} paused before the last part of the quest.")
    _say_thought(world, hero, f"I do not need to hurry")
    world.say(f"That was the third step: {quest.step3}.")
    hero.memes["comfort"] += 0.5
    parent.memes["tenderness"] += 1.0
    world.say(f"{parent.label_word} smiled, because the snack was not a big noisy consumption any more; it was just a calm little part of bedtime.")
    world.say(f"Finally, {quest.ending}.")

    hero.meters["sleepiness"] += 0.8
    hero.memes["comfort"] += 1.0
    hero.memes["desire"] = 0.0
    parent.memes["worry"] = 0.0

    world.facts.update(hero=hero, parent=parent, snack=snack, tool=tool, quest=quest)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, snack, quest = f["hero"], f["snack"], f["quest"]
    return [
        f'Write a bedtime story for a child who feels hungry and thinks about consumption while trying to stay sleepy.',
        f"Tell a gentle story where {hero.id} wants {snack.phrase}, follows a small quest, and learns to eat slowly before bed.",
        f"Write a soft bedtime tale with an inner monologue, a snack, and a quiet compromise about nighttime consumption.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, snack, quest = f["hero"], f["parent"], f["snack"], f["quest"]
    return [
        QAItem(
            question=f"What did {hero.id} want at bedtime?",
            answer=f"{hero.id} wanted {snack.phrase}, but {hero.pronoun()} also wanted to stay calm and sleepy.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry about the snack?",
            answer=f"{parent.label_word.capitalize()} worried that too much nighttime consumption would make {hero.id} too full to fall asleep easily.",
        ),
        QAItem(
            question=f"What was the small quest?",
            answer=f"The quest was to {quest.step1}, {quest.step2}, and then {quest.ending}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} feeling cozy, a little fuller, and ready for sleep after choosing a gentle bedtime portion.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does consumption mean?",
            answer="Consumption means using something up, like eating food or drinking a little milk.",
        ),
        QAItem(
            question="Why do people eat slowly at bedtime?",
            answer="People eat slowly at bedtime so their bodies can settle down and feel calm before sleep.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking a character does in their own head while thinking things through.",
        ),
        QAItem(
            question="What is a quest in a story?",
            answer="A quest is a small goal or journey a character follows step by step to reach something they want.",
        ),
        QAItem(
            question="Why can a snack feel cozy at night?",
            answer="A snack can feel cozy at night when it is warm, small, and part of a calm bedtime routine.",
        ),
    ]


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
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


CURATED = [
    StoryParams(snack="oatmeal", quest="bedside", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(snack="toast", quest="countstars", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(snack="milk", quest="lantern", name="Nora", gender="girl", parent="mother", trait="sleepy"),
]


ASP_RULES = r"""
snack(snack).
quest(quest).

bedtime_ok(S, Q) :- snack(S), quest(Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SNACKS:
        lines.append(asp.fact("snack", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bedtime_ok/2."))
    return sorted(set(asp.atoms(model, "bedtime_ok")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show bedtime_ok/2."))
        return
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} bedtime-friendly snack/quest combos:\n")
        for s, q in combos:
            print(f"  {s:10} {q}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.snack} / {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
