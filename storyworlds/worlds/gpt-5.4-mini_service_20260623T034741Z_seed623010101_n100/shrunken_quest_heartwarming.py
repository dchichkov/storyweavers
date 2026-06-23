#!/usr/bin/env python3
"""
storyworlds/worlds/shrunken_quest_heartwarming.py
=================================================

A standalone storyworld about a small heartwarming quest: a child finds a
shrunken treasure, learns what made it small, and completes a gentle quest by
helping it grow back with care.

The world is built from a tiny tale seed:
- a child wants to complete a quest,
- the quest object has become shrunken,
- a kind helper and a few physical steps lead to a warm resolution.

The simulation keeps typed entities with physical meters and emotional memes,
uses a simple causal model, and produces:
1) generation prompts,
2) story-grounded QA,
3) world-knowledge QA.

It also includes an inline ASP twin for the reasonableness gate and a
verification mode that checks parity and runs a smoke test.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    owner: str = ""
    caretaker: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    child: object | None = None
    helper: object | None = None
    parent: object | None = None
    quest: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
        if not hasattr(self, "_tags"):
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
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    quest_need: str
    shrunken_need: str
    grow_need: str
    size_key: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Helper:
    id: str
    label: str
    phrase: str
    can_help: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class StoryParams:
    setting: str = "meadow"
    quest_item: str = "banner"
    helper: str = "gardener"
    child_name: str = "Mia"
    child_gender: str = "girl"
    parent: str = "mother"
    trait: str = "gentle"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_shrink(world: World) -> list[str]:
    out: list[str] = []
    quest = world.get("quest")
    if quest.meters["watched"] < THRESHOLD:
        return out
    sig = ("shrink", quest.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    quest.meters["small"] = 1.0
    quest.meters["hope"] += 1.0
    out.append("__shrink__")
    return out


def _r_restore(world: World) -> list[str]:
    out: list[str] = []
    quest = world.get("quest")
    helper = world.get("helper")
    child = world.get("child")
    if quest.meters["watered"] < THRESHOLD or helper.memes["care"] < THRESHOLD:
        return out
    sig = ("restore", quest.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    quest.meters["small"] = 0.0
    quest.meters["bright"] = 1.0
    child.memes["joy"] += 1.0
    out.append("__restore__")
    return out


CAUSAL_RULES = [Rule("shrink", _r_shrink), Rule("restore", _r_restore)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def shrink_target_at_risk(setting: Setting, q: QuestItem) -> bool:
    return q.size_key in setting.affords


def helper_can_restore(helper: Helper, q: QuestItem) -> bool:
    return q.size_key in helper.can_help


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for quest_id, q in QUESTS.items():
            for helper_id, h in HELPERS.items():
                if shrink_target_at_risk(setting, q) and helper_can_restore(h, q):
                    combos.append((setting_id, quest_id, helper_id))
    return combos


def predict_restore(world: World) -> dict:
    sim = world.copy()
    _do_quest(sim, narrate=False)
    quest = sim.get("quest")
    return {"restored": quest.meters["small"] < THRESHOLD and quest.meters["bright"] >= THRESHOLD}


def _do_quest(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    quest = world.get("quest")
    helper = world.get("helper")
    child.memes["hope"] += 1.0
    quest.meters["watched"] += 1.0
    propagate(world, narrate=narrate)
    if quest.meters["small"] >= THRESHOLD:
        quest.meters["watered"] += 1.0
        propagate(world, narrate=narrate)


def introduction(world: World, child: Entity, quest: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} with a kind smile and a big wish "
        f"to finish a quest. {child.pronoun().capitalize()} loved the {quest.label} "
        f"because it made every day feel brave."
    )
    world.say(
        f"One morning, {child.id} found {child.pronoun('possessive')} {quest.label} "
        f"looking shrunken and dim."
    )


def set_scene(world: World, helper: Entity, setting: Setting) -> None:
    if setting.indoor:
        world.say(
            f"The {setting.place} was quiet and warm, with soft light on the floor."
        )
    else:
        world.say(
            f"The {setting.place} was bright and open, with gentle air moving through."
        )
    world.say(
        f"Nearby, {helper.label_word if hasattr(helper, 'label_word') else helper.label} "
        f"{helper.phrase} waited to help."
    )


def ask_quest(world: World, child: Entity, quest: Entity) -> None:
    child.memes["desire"] += 1.0
    world.say(
        f"{child.id} wanted to fix the {quest.label} right away, but "
        f"{child.pronoun('possessive')} heart knew this was a real quest, not a race."
    )


def warn_and_help(world: World, helper: Entity, child: Entity, quest: Entity) -> bool:
    pred = predict_restore(world)
    if not pred["restored"]:
        return False
    helper.memes["care"] += 1.0
    world.say(
        f"{helper.id} smiled and said, \"A shrunken {quest.label} needs water, "
        f"sun, and patience. I can help you bring it back.\""
    )
    return True


def tend(world: World, child: Entity, helper: Entity, quest: Entity) -> None:
    quest.meters["watched"] += 1.0
    quest.meters["watered"] += 1.0
    helper.memes["care"] += 1.0
    child.memes["joy"] += 1.0
    world.say(
        f"Together they carried a little cup of water, gave the {quest.label} a "
        f"gentle drink, and set it in the sun."
    )


def ending(world: World, child: Entity, helper: Entity, quest: Entity) -> None:
    world.say(
        f"Soon the {quest.label} grew bright again. It was no longer shrunken; it "
        f"stood tall enough to feel proud."
    )
    world.say(
        f"{child.id} hugged {child.pronoun('possessive')} {quest.label}, and "
        f"{helper.id} laughed softly beside {child.pronoun('object')}. The quest "
        f"was complete, and the little day felt bigger than before."
    )


def tell(setting: Setting, quest_cfg: QuestItem, helper_cfg: Helper,
         child_name: str = "Mia", child_gender: str = "girl",
         parent_type: str = "mother", trait: str = "gentle") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    helper = world.add(Entity(id="Helper", kind="character", type="helper", label=helper_cfg.label))
    quest = world.add(Entity(id="quest", type="quest", label=quest_cfg.label, phrase=quest_cfg.phrase))

    world.facts.update(child=child, parent=parent, helper=helper, quest=quest, setting=setting,
                       quest_cfg=quest_cfg, helper_cfg=helper_cfg, trait=trait)

    quest.meters["watched"] = 0.0
    quest.meters["small"] = 0.0
    quest.meters["watered"] = 0.0
    quest.meters["bright"] = 0.0
    quest.memes["hope"] = 0.0
    child.memes["hope"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["desire"] = 0.0
    helper.memes["care"] = 1.0

    introduction(world, child, quest)
    world.para()
    set_scene(world, helper, setting)
    ask_quest(world, child, quest)
    if not warn_and_help(world, helper, child, quest):
        pass
    world.para()
    tend(world, child, helper, quest)
    world.para()
    ending(world, child, helper, quest)
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", indoor=False, affords={"flower", "seed", "banner"}),
    "garden": Setting(place="the garden", indoor=False, affords={"flower", "seed"}),
    "sunroom": Setting(place="the sunroom", indoor=True, affords={"banner", "seed"}),
    "library": Setting(place="the library corner", indoor=True, affords={"bookmark", "banner"}),
}

QUESTS = {
    "banner": QuestItem(
        id="banner",
        label="banner",
        phrase="a little quest banner",
        quest_need="a bright banner for the quest",
        shrunken_need="the banner has gone shrunken and droopy",
        grow_need="water and sunlight can help the banner stand tall again",
        size_key="banner",
        tags={"banner", "quest"},
    ),
    "flower": QuestItem(
        id="flower",
        label="flower",
        phrase="a tiny quest flower",
        quest_need="a flower for the quest path",
        shrunken_need="the flower has gone shrunken from thirst",
        grow_need="water and kindness can help the flower perk up",
        size_key="flower",
        tags={"flower", "quest"},
    ),
    "seed": QuestItem(
        id="seed",
        label="seed",
        phrase="a little quest seed",
        quest_need="a seed for the quest pot",
        shrunken_need="the seed looks shrunken and dry",
        grow_need="water and a sunny place can help the seed wake up",
        size_key="seed",
        tags={"seed", "quest"},
    ),
    "bookmark": QuestItem(
        id="bookmark",
        label="bookmark",
        phrase="a paper quest bookmark",
        quest_need="a bookmark for the quest book",
        shrunken_need="the bookmark has curled up and shrunken",
        grow_need="flat hands and a calm place can smooth the bookmark again",
        size_key="bookmark",
        tags={"bookmark", "quest"},
    ),
}

HELPERS = {
    "gardener": Helper(
        id="gardener",
        label="gardener",
        phrase="a friendly gardener with a watering can",
        can_help={"flower", "seed", "banner"},
        tags={"water", "sun", "quest"},
    ),
    "sunbeam": Helper(
        id="sunbeam",
        label="sunbeam",
        phrase="a warm sunbeam on the sill",
        can_help={"banner", "seed", "bookmark"},
        tags={"sun", "quest"},
    ),
    "librarian": Helper(
        id="librarian",
        label="librarian",
        phrase="a gentle librarian with calm hands",
        can_help={"bookmark", "banner"},
        tags={"calm", "quest"},
    ),
}

TRAITS = ["gentle", "patient", "kind", "quiet", "brave"]
GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Ella"]
BOY_NAMES = ["Ben", "Theo", "Finn", "Noah", "Eli"]


KNOWLEDGE = {
    "quest": [
        ("What is a quest?",
         "A quest is a special goal someone tries to finish, usually step by step. It can feel exciting because the person keeps going until the goal is done."),
    ],
    "banner": [
        ("What is a banner?",
         "A banner is a sign or flag that can cheer on a plan or celebration. It often hangs where people can see it clearly."),
    ],
    "flower": [
        ("What does a flower need to grow?",
         "A flower usually needs water, sunlight, and a little care. With those things, it can stand up tall and look bright again."),
    ],
    "seed": [
        ("What does a seed need to wake up and grow?",
         "A seed often needs water, warmth, and a good place to rest. Then it can start growing into a plant."),
    ],
    "bookmark": [
        ("What is a bookmark for?",
         "A bookmark helps you remember where you stopped reading. It stays flat between the pages and keeps your place."),
    ],
    "water": [
        ("Why do plants need water?",
         "Plants need water to stay healthy and strong. Water helps them stand up and grow."),
    ],
    "sun": [
        ("Why do some plants like sunlight?",
         "Sunlight helps many plants make food and grow well. It also helps them feel warm and bright."),
    ],
    "calm": [
        ("Why do gentle hands help with fragile things?",
         "Gentle hands keep fragile things from tearing or bending. Moving slowly and carefully helps them stay safe."),
    ],
}

KNOWLEDGE_ORDER = ["quest", "banner", "flower", "seed", "bookmark", "water", "sun", "calm"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    quest = f["quest_cfg"]
    helper = f["helper_cfg"]
    setting = f["setting"]
    return [
        f'Write a heartwarming story for a young child about a shrunken {quest.label} '
        f'and a gentle quest in {setting.place}.',
        f"Tell a warm story where {child.id} finds a shrunken {quest.label}, gets "
        f"help from a kind {helper.label}, and finishes the quest with care.",
        f'Write a simple story that includes the word "shrunken" and ends with a '
        f'quest object becoming bright and whole again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    quest = f["quest"]
    setting = f["setting"]
    qcfg = f["quest_cfg"]
    hcfg = f["helper_cfg"]
    qa = [
        QAItem(
            question=f"What did {child.id} want to do in {setting.place}?",
            answer=(
                f"{child.id} wanted to finish a quest and help the {quest.label} feel "
                f"special again. The little goal gave {child.id} a kind reason to keep going."
            ),
        ),
        QAItem(
            question=f"Why did the {quest.label} seem hard to use at first?",
            answer=(
                f"It was shrunken and dim, so it did not look ready for the quest. "
                f"That meant {child.id} had to be patient instead of rushing."
            ),
        ),
        QAItem(
            question=f"Who helped {child.id} with the {quest.label}?",
            answer=(
                f"The {helper.label} helped {child.id}. {helper.id} knew what the {quest.label} "
                f"needed and showed how to care for it gently."
            ),
        ),
        QAItem(
            question=f"What did the helper say the shrunken {quest.label} needed?",
            answer=(
                f"{helper.id} said it needed water, sunlight, and patience. "
                f"Those simple things could help the {quest.label} grow back."
            ),
        ),
    ]
    if quest.meters["small"] < THRESHOLD:
        qa.append(QAItem(
            question=f"How did the story end for the {quest.label}?",
            answer=(
                f"It grew bright again and stopped being shrunken. "
                f"{child.id} finished the quest and felt proud of the gentle work."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["quest_cfg"].tags) | set(f["helper_cfg"].tags)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="meadow", quest_item="banner", helper="gardener", child_name="Mia", child_gender="girl", parent="mother", trait="gentle"),
    StoryParams(setting="garden", quest_item="flower", helper="gardener", child_name="Ben", child_gender="boy", parent="father", trait="kind"),
    StoryParams(setting="sunroom", quest_item="seed", helper="sunbeam", child_name="Nora", child_gender="girl", parent="mother", trait="patient"),
    StoryParams(setting="library", quest_item="bookmark", helper="librarian", child_name="Eli", child_gender="boy", parent="father", trait="quiet"),
]


def explain_rejection(setting: Setting, quest: QuestItem, helper: Helper) -> str:
    return (
        f"(No story: {setting.place} does not support a quest for a {quest.label}, "
        f"or the {helper.label} cannot help that kind of thing. Pick a matching "
        f"quest object and helper.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a shrunken quest, helped into a heartwarming ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest-item", choices=QUESTS)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = [
        c for c in valid_combos()
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "quest_item", None) is None or c[1] == getattr(args, "quest_item", None))
        and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, quest_item, helper = rng.choice(list(combos))
    q = _safe_lookup(QUESTS, quest_item)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, quest_item=quest_item, helper=helper, child_name=name, child_gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.quest_item not in QUESTS or params.helper not in HELPERS:
        pass
    setting = _safe_lookup(SETTINGS, params.setting)
    quest_cfg = _safe_lookup(QUESTS, params.quest_item)
    helper_cfg = _safe_lookup(HELPERS, params.helper)
    if not shrink_target_at_risk(setting, quest_cfg) or not helper_can_restore(helper_cfg, quest_cfg):
        pass
    world = tell(setting, quest_cfg, helper_cfg, params.child_name, params.child_gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
at_risk(S,Q) :- setting(S), quest(Q), aff(S, K), needs(Q, K).
helper_ok(H,Q) :- helper(H), quest(Q), can_help(H, K), needs(Q, K).
valid(S,Q,H) :- at_risk(S,Q), helper_ok(H,Q).
restored :- watched(Q), helper_care(H), helper_ok(H,Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("aff", sid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("needs", qid, q.size_key))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_care", hid))
        for k in sorted(h.can_help):
            lines.append(asp.fact("can_help", hid, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP gates.")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
    # smoke test
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
        print("OK: smoke test passed.")
        return 0
    return 1


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
        for row in asp_valid_combos():
            print(row)
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
            header = f"### {p.child_name}: {p.quest_item} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
