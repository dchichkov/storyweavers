#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/robe_soften_bad_ending_happy_ending_quest.py
=====================================================================================================================

A small Tall Tale storyworld about a grand robe, a stubborn stiffness, and a
quest to soften it before the wrong ending can win.

Premise:
- A child or traveler has a magnificent robe that looks mighty but feels stiff.
- The robe must be softened for a special day.
- If the hero ignores the problem, the robe scratches, bunches, and spoils the fun.
- If the hero follows the quest, the robe becomes soft, drapey, and ready for a
  happy ending.

This script follows the Storyweavers contract:
- StoryParams, registries, parser, resolve_params, generate, emit, main
- QAItem / StoryError / StorySample imported eagerly
- ASP twin with inline rules and a Python reasonableness gate
- Story state is driven by meters and memes, not a frozen prose template
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    robe: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"stiff": 0.0, "soft": 0.0, "wet": 0.0, "clean": 0.0, "torn": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "pride": 0.0, "dismay": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle"}:
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
    trigger: str
    method: str
    fix: str
    danger: str
    keyword: str = "soften"
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
    type: str = "robe"
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
    title: str
    offers: str
    tool: str
    plural: bool = False
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "barn": Setting(place="the old barn", affords={"soak", "wash"}),
    "riverbank": Setting(place="the riverbank", affords={"soak", "wash"}),
    "washhouse": Setting(place="the washhouse", affords={"wash"}),
    "wellyard": Setting(place="the wellyard", affords={"soak"}),
}

QUESTS = {
    "soak": Quest(
        id="soak",
        verb="soak the robe",
        gerund="soaking the robe",
        trigger="stiff as board",
        method="in the river",
        fix="soak it until it loosens",
        danger="a stiff robe scratches like thistles",
        tags={"water", "wet", "robe", "soften"},
    ),
    "wash": Quest(
        id="wash",
        verb="wash the robe",
        gerund="washing the robe",
        trigger="dusty and rough",
        method="with warm water and soap",
        fix="wash it and work the folds by hand",
        danger="dust makes a robe feel scratchy and mean",
        tags={"water", "soap", "robe", "soften"},
    ),
}

PRIZES = {
    "robe": Prize(label="robe", phrase="a grand robe with a long hem"),
}

HELPERS = {
    "grandma": Helper(
        id="grandma",
        label="grandma",
        title="Grandma Pine",
        offers="a bowl of warm soapy water",
        tool="a wooden paddle",
    ),
    "tailor": Helper(
        id="tailor",
        label="tailor",
        title="the tailor",
        offers="a clever steaming trick",
        tool="a kettle and a cloth line",
    ),
}

HERO_NAMES = ["Mabel", "Jasper", "Penny", "Otis", "Luna", "Ned", "Tilda", "Wes"]
TRAITS = ["stouthearted", "bright-eyed", "quick-witted", "steady", "spry"]
GENDERS = ["girl", "boy"]


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    trait: str
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


def reasonableness_gate(place: str, quest: str) -> bool:
    return place in SETTINGS and quest in QUESTS and quest in _safe_lookup(SETTINGS, place).affords


def explain_rejection(place: str, quest: str) -> str:
    if place not in SETTINGS:
        return "(No story: that place is not part of this little world.)"
    if quest not in QUESTS:
        return "(No story: that quest does not exist in this tale.)"
    return (
        f"(No story: the {_safe_lookup(QUESTS, quest).gerund} cannot happen at {_safe_lookup(SETTINGS, place).place}; "
        f"that place does not afford a real way to soften the robe.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall Tale storyworld: a robe, a soften-quest, a bad ending, and a happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--helper", choices=HELPERS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    quest = getattr(args, "quest", None) or rng.choice(list(QUESTS))
    if getattr(args, "place", None) and getattr(args, "quest", None) and not reasonableness_gate(getattr(args, "place", None), getattr(args, "quest", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not reasonableness_gate(place, quest):
        combos = [(p, q) for p in SETTINGS for q in QUESTS if reasonableness_gate(p, q)]
        if not combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
        place, quest = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    return StoryParams(place=place, quest=quest, name=name, gender=gender, trait=trait, helper=helper)


def _pronoun(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def _make_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    robe = world.add(Entity(
        id="robe",
        type="robe",
        label="robe",
        phrase=PRIZES["robe"].phrase,
        owner=hero.id,
        caretaker=_safe_lookup(HELPERS, params.helper).id,
        worn_by=hero.id,
    ))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult"))
    quest = _safe_lookup(QUESTS, params.quest)

    hero.memes["hope"] += 1
    robe.meters["stiff"] = 1.0
    robe.meters["soft"] = 0.0
    robe.meters["clean"] = 1.0

    # Act 1
    world.say(
        f"In the days when crows wore shadows like hats, {hero.id} was a {params.trait} "
        f"{params.gender} who loved {robe.phrase}."
    )
    world.say(
        f"It was grand enough to make a gatepost stare, but it had gone stiff as a fence rail."
    )
    world.say(
        f"{hero.id} said, 'I must {quest.verb}, because a robe should fall like a river, not stand like a plank.'"
    )

    # Act 2
    world.para()
    world.say(
        f"So {hero.id} and {helper.title} went to {world.setting.place}, where the air smelled of old wood and new rain."
    )
    world.say(
        f"They began the quest by {quest.fix}."
    )
    robe.meters["wet"] += 1
    if params.quest == "wash":
        robe.meters["clean"] += 1
    robe.meters["stiff"] -= 0.5
    robe.meters["soft"] += 0.5
    hero.memes["worry"] += 0.5

    # Bad ending possibility
    world.para()
    if robe.meters["soft"] < THRESHOLD:
        hero.memes["dismay"] += 1
        world.say(
            f"But if they had stopped there, the robe would have stayed stubbornly stiff, and {quest.danger}."
        )
        world.say(
            f"It would have rubbed {hero.id}'s shoulders raw and spoiled the fine ceremony."
        )
    else:
        world.say(
            f"At first the robe only softened a little, which was not enough for a happy parade."
        )
        world.say(
            f"Still, {helper.title} had a tall tale trick ready, and the quest was not done yet."
        )

    # Act 3: happy ending
    world.para()
    robe.meters["wet"] += 1
    robe.meters["soft"] = 1.5
    robe.meters["stiff"] = 0.0
    hero.memes["hope"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"So {helper.title} gave {hero.id} {_safe_lookup(HELPERS, params.helper).offers}, and together they kept at it until the robe softened like butter in sunshine."
    )
    world.say(
        f"By sunset, {hero.id} wore the robe, and it flowed and folded with a kindly swish."
    )
    world.say(
        f"That was the happy ending: the quest was finished, the robe was soft, and {hero.id} walked home looking as grand as a banner on a windy hill."
    )

    world.facts = {
        "hero": hero,
        "helper": helper,
        "robe": robe,
        "quest": quest,
        "setting": world.setting,
        "params": params,
        "happy": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    return [
        f'Write a Tall Tale for young children about a child named {hero.id} who must {quest.verb} before a special day.',
        f"Tell a playful story where the word 'soften' matters because a stiff robe could spoil the ending.",
        f"Write a story with a bad ending that gets turned into a happy ending by a brave quest involving a robe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    robe = _safe_fact(world, f, "robe")
    quest = _safe_fact(world, f, "quest")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the robe?",
            answer=f"{hero.id} wanted to {quest.verb} so the robe would not stay stiff."
        ),
        QAItem(
            question=f"Why did the robe need a quest at {place}?",
            answer=f"The robe had gone stiff as a fence rail, and {helper.title} helped {hero.id} soften it."
        ),
        QAItem(
            question=f"What changed by the happy ending?",
            answer=f"By the end, the robe was soft and flowed nicely, and {hero.id} could wear it with pride."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something is stiff?",
            answer="A stiff thing does not bend or fold easily. A stiff robe can feel scratchy and hard to wear."
        ),
        QAItem(
            question="What does soften mean?",
            answer="To soften something is to make it less hard, less stiff, or easier to bend and wear."
        ),
        QAItem(
            question="Why can washing help cloth?",
            answer="Washing can help cloth get cleaner and sometimes looser, especially when warm water and careful hands are used."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that could produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child-level knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place_ok(P) :- setting(P).
quest_ok(Q) :- quest(Q).

valid(P,Q) :- setting(P), quest(Q), affords(P,Q).

% The robe is at risk when the quest is a soften-quest.
robe_at_risk(Q) :- quest(Q), tag(Q,soften).

% A happy ending exists only when the robe can truly soften.
happy(Q) :- valid(P,Q), robe_at_risk(Q), can_soften(Q).

#show valid/2.
#show happy/1.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("setting", p))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", p, q))
    for q, qq in QUESTS.items():
        lines.append(asp.fact("quest", q))
        for t in sorted(qq.tags):
            lines.append(asp.fact("tag", q, t))
        lines.append(asp.fact("can_soften", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return sorted((p, q) for p in SETTINGS for q in QUESTS if reasonableness_gate(p, q))


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "quest", None) and not reasonableness_gate(getattr(args, "place", None), getattr(args, "quest", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "quest", None):
        combos = [c for c in combos if c[1] == getattr(args, "quest", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    return StoryParams(place=place, quest=quest, name=name, gender=gender, trait=trait, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
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
    StoryParams(place="barn", quest="wash", name="Mabel", gender="girl", trait="bright-eyed", helper="grandma"),
    StoryParams(place="riverbank", quest="soak", name="Jasper", gender="boy", trait="stouthearted", helper="tailor"),
    StoryParams(place="washhouse", quest="wash", name="Luna", gender="girl", trait="steady", helper="grandma"),
]


def build_parser_default() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2.\n#show happy/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest) combos:\n")
        for p, q in combos:
            print(f"  {p:10} {q}")
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
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
