#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/element_joey_repetition_surprise_bravery_folk_tale.py
================================================================================================

A small folk-tale storyworld about a joey, a bright element, repeated tries,
a surprise helper, and a brave ending.

Seed tale sketch:
---
A little joey named Joey lived near a windy gum tree. One dusk, he found a tiny
glowing element stone that could light the burrow at night. But the creek had
swollen after rain, and the stone slipped from his paws onto a reedy bank.
Joey tried once, then twice, then a third time, to cross the creek and reach it.
At last, a surprised old platypus floated over on a bark bowl and offered help.
Joey took a brave breath, rode the little bowl, and brought the element stone
home so the burrow could shine.

World notes:
---
- Repetition is modeled as three attempts and a repeated hop-backs cadence.
- Surprise is modeled as an unexpected helper appearing after the third try.
- Bravery is modeled as a meme that rises when Joey chooses to cross anyway.
- Physical state changes drive narration: distance, water hazard, possession of
  the glowing element, and whether the burrow has light.

This script follows the Storyweavers contract:
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import of storyworlds/results.py
- lazy ASP import inside ASP helpers
- plain stdlib prose engine plus inline ASP_RULES twin
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper_ent: object | None = None
    joey: object | None = None
    stone: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"joey", "kangaroo"}:
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
    detail: str
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
    repeated_verb: str
    hazard: str
    turn: str
    location: str
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
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    location: str
    glowing: bool = True
    genders: set[str] = field(default_factory=lambda: {"joey"})
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
    surprise: str
    offer: str
    carry_phrase: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
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


SETTINGS = {
    "creek": Setting(
        place="the creek",
        detail="The creek sang under the reeds, and the mud smelled fresh after rain.",
        affords={"crossing"},
    ),
    "hollow": Setting(
        place="the hollow tree",
        detail="The hollow tree stood warm and round, with a tiny door under its roots.",
        affords={"crossing"},
    ),
    "meadow": Setting(
        place="the meadow",
        detail="The meadow shimmered with grass and little flowers nodding in the wind.",
        affords={"crossing"},
    ),
}

CHALLENGES = {
    "creek": Challenge(
        id="creek",
        verb="cross the creek",
        repeated_verb="try to hop over the creek",
        hazard="water was too wide and slippery",
        turn="an old helper arrived with a floating bark bowl",
        location="the creek bank",
        keyword="creek",
        tags={"water", "repeat", "surprise"},
    ),
    "wind": Challenge(
        id="wind",
        verb="reach the windy hill",
        repeated_verb="try to run up the windy hill",
        hazard="the wind kept pushing Joey back",
        turn="a surprise kite-string from a kindly wombat caught the breeze",
        location="the hill path",
        keyword="wind",
        tags={"wind", "repeat", "surprise"},
    ),
    "mud": Challenge(
        id="mud",
        verb="cross the muddy track",
        repeated_verb="try to step through the mud",
        hazard="the mud grabbed at Joey's feet",
        turn="a surprise log bridge appeared beside the path",
        location="the muddy track",
        keyword="mud",
        tags={"mud", "repeat", "surprise"},
    ),
}

PRIZES = {
    "element": Prize(
        id="element",
        label="element stone",
        phrase="a tiny glowing element stone",
        type="stone",
        location="the reeds",
    ),
    "lantern": Prize(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        type="lantern",
        location="the bank",
        glowing=True,
    ),
    "shell": Prize(
        id="shell",
        label="shell charm",
        phrase="a pale shell charm",
        type="charm",
        location="the moss",
        glowing=False,
    ),
}

HELPERS = {
    "platypus": Helper(
        id="platypus",
        label="old platypus",
        surprise="an old platypus bobbed up with a bark bowl",
        offer="Let me ferry you across",
        carry_phrase="floated Joey over the water",
        tags={"surprise", "water"},
    ),
    "wombat": Helper(
        id="wombat",
        label="kind wombat",
        surprise="a kind wombat came shuffling through the grass",
        offer="Take this branch and hold on",
        carry_phrase="guided Joey over the muddy ground",
        tags={"surprise", "mud"},
    ),
    "frog": Helper(
        id="frog",
        label="green frog",
        surprise="a green frog popped from the reeds",
        offer="Hop onto my lily pad",
        carry_phrase="pushed Joey gently toward the prize",
        tags={"surprise", "water"},
    ),
}

NAMES = ["Joey", "Jory", "Benny", "Milo", "Toby", "Pip"]
BACKGROUND = ["little", "brave", "quick", "curious", "gentle", "small"]


class Reasoner:
    @staticmethod
    def can_reasonably_happen(setting: Setting, challenge: Challenge, prize: Prize) -> bool:
        return challenge.id in setting.affords and prize.location in {"the reeds", "the bank", "the moss"}

    @staticmethod
    def helper_fits(challenge: Challenge, helper: Helper) -> bool:
        if challenge.id == "creek":
            return "water" in helper.tags
        if challenge.id == "mud":
            return "mud" in helper.tags
        if challenge.id == "wind":
            return "surprise" in helper.tags
        return False


def select_helper(challenge: Challenge) -> Helper:
    for helper in HELPERS.values():
        if Reasoner.helper_fits(challenge, helper):
            return helper
    pass


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    challenge = _safe_lookup(CHALLENGES, params.challenge)
    prize = _safe_lookup(PRIZES, params.prize)
    world = World(setting)

    joey = world.add(Entity(
        id=params.name,
        kind="character",
        type="joey",
        meters={"distance": 0.0},
        memes={"bravery": 0.0, "hope": 0.0, "surprise": 0.0},
    ))
    stone = world.add(Entity(
        id="prize",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=joey.id,
        caretaker=joey.id,
        carried_by=None,
    ))

    helper = select_helper(challenge)

    world.say(f"{joey.id} was a {random.choice(BACKGROUND)} joey who lived by {setting.place}.")
    world.say(f"{joey.id} loved the little light of {prize.phrase}.")

    world.para()
    world.say(setting.detail)
    world.say(f"One evening, {stone.phrase} slipped away to {prize.location}, and {joey.id} wanted to {challenge.verb} to get it back.")

    world.para()
    for attempt in (1, 2, 3):
        joey.memes["hope"] += 1
        world.say(f"{joey.id} made the first hop, then the second hop, then the third hop.")
        if attempt < 3:
            world.say(f"But {challenge.hazard}.")
        else:
            world.say(f"Still, {joey.id} took a brave breath and kept going.")

    helper_ent = world.add(Entity(id=helper.id, kind="character", type=helper.id))
    joey.memes["surprise"] += 1
    world.say(f"Then, surprise! {helper.surprise}.")
    world.say(f'"{helper.offer}," said the {helper.label}.')
    world.say(f"The {helper.label} {helper.carry_phrase}, and {joey.id} held tight with brave paws.")

    world.para()
    joey.memes["bravery"] += 1
    stone.carried_by = joey.id
    joey.meters["distance"] = 1.0
    world.say(f"With one brave ride, {joey.id} reached {prize.location}, picked up the {prize.label}, and brought it home.")
    world.say(f"At the end, the burrow shone with the little light again, and {joey.id} stood tall and glad.")

    world.facts.update(
        hero=joey,
        helper=helper_ent,
        prize=stone,
        setting=setting,
        challenge=challenge,
        helper_key=helper.id,
        resolved=True,
        attempts=3,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child about {_safe_fact(world, f, "hero").id}, a {_safe_fact(world, f, "hero").type}, and a glowing element stone.',
        f'Tell a gentle story where {_safe_fact(world, f, "hero").id} must {_safe_fact(world, f, "challenge").verb}, try several times, and meet a surprising helper.',
        f'Write a story with repetition, surprise, and bravery in which {_safe_fact(world, f, "hero").id} brings the {_safe_fact(world, f, "prize").label} home.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    prize: Entity = _safe_fact(world, f, "prize")
    challenge: Challenge = _safe_fact(world, f, "challenge")
    helper: Entity = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"What did {hero.id} want to do for the glowing {prize.label}?",
            answer=f"{hero.id} wanted to {challenge.verb} so the {prize.label} would not be left behind.",
        ),
        QAItem(
            question=f"How many times did {hero.id} try before help arrived?",
            answer=f"{hero.id} tried three times, and the repeated tries showed both patience and bravery.",
        ),
        QAItem(
            question=f"Who surprised {hero.id} by helping at the end?",
            answer=f"An unexpected {helper.type if helper.type != 'platypus' else 'platypus'} helped, and that surprise changed the story.",
        ),
        QAItem(
            question=f"What changed after {hero.id} brought the prize home?",
            answer=f"The little burrow shone again, because {hero.id} carried the {prize.label} back safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone feels a little afraid but still does the right thing.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that happens and makes the story change in a new way.",
        ),
        QAItem(
            question="Why do stories repeat actions?",
            answer="Stories repeat actions to show effort, build a rhythm, and make the listener notice the change.",
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% The story is valid when the challenge fits the setting and the prize location is reachable.
valid_story(P, C, R) :- setting(P), challenge(C), prize(R), affords(P, C), prize_home(R).

% Repetition requires exactly three attempts.
repetition(C) :- attempts(C, 3).

% Surprise requires a helper that appears after the third try.
surprise(C, H) :- repetition(C), helper(H).

% Bravery is present when the hero continues despite hazard.
bravery(H) :- hero(H), resolved(H).

#show valid_story/3.
#show repetition/1.
#show surprise/2.
#show bravery/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("prize_home", "element"))
        lines.append(asp.fact("prize_home", "lantern"))
        lines.append(asp.fact("prize_home", "shell"))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_home", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_valid = set(asp.atoms(model, "valid_story"))
    py_valid = set()
    for sid, s in SETTINGS.items():
        for cid, c in CHALLENGES.items():
            for pid, p in PRIZES.items():
                if Reasoner.can_reasonably_happen(s, c, p):
                    py_valid.add((sid, cid, pid))
    if asp_valid == py_valid:
        print(f"OK: ASP and Python agree on {len(py_valid)} valid stories.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP only:", sorted(asp_valid - py_valid))
    print("Python only:", sorted(py_valid - asp_valid))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a joey, a glowing element, repetition, surprise, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    challenge = getattr(args, "challenge", None) or rng.choice(list(CHALLENGES))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if not Reasoner.can_reasonably_happen(_safe_lookup(SETTINGS, place), _safe_lookup(CHALLENGES, challenge), _safe_lookup(PRIZES, prize)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, challenge=challenge, prize=prize, name=name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        combos = [
            StoryParams(place=p, challenge=c, prize=r, name="Joey")
            for p in SETTINGS
            for c in CHALLENGES
            for r in PRIZES
            if Reasoner.can_reasonably_happen(_safe_lookup(SETTINGS, p), _safe_lookup(CHALLENGES, c), _safe_lookup(PRIZES, r))
        ]
        samples = [generate(p) for p in combos]
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
