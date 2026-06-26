#!/usr/bin/env python3
"""
flash_invasion_humor_fable.py
=============================

A tiny fable-like storyworld about a sudden flash, a comic invasion, and a
humble lesson learned in a small place.

The seed image:
---
One evening, a boastful lantern keeper loved the shiny flash of his own lamp.
When a noisy invasion of moths and fireflies swirled into the yard, he tried to
chase them away. But the flash only made the insects dance harder and the whole
courtyard looked like a silly festival. In the end, he learned that a little
light is good for guiding, but too much flashing only invites a crowd.

This world turns that seed into a small simulated domain:
- the light can flash,
- the invasion can spread,
- the hero can learn humility,
- the ending proves the lesson with a changed world state.

The tone aims for a child-friendly fable with humor, a clear turn, and a short
moral-shaped resolution.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    shade: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"man", "boy", "king", "keeper"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl", "queen", "keeperess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str = "the courtyard"
    indoors: bool = False
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
class Spark:
    id: str
    verb: str
    gerund: str
    rush: str
    flash: str
    mischief: str
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
    region: str
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
class Remedy:
    id: str
    label: str
    phrase: str
    covers: set[str]
    calms: set[str]
    prep: str
    tail: str
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
        self.facts: dict = {}
        self.flash_on: bool = False
        self.invasion: int = 0

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
        clone.flash_on = self.flash_on
        clone.invasion = self.invasion
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    spark: str
    prize: str
    remedy: str
    hero_name: str
    hero_type: str
    helper_type: str
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
    "courtyard": Setting(place="the courtyard", indoors=False, affords={"flash", "invasion"}),
    "garden": Setting(place="the garden", indoors=False, affords={"flash", "invasion"}),
    "barn": Setting(place="the barn loft", indoors=True, affords={"flash", "invasion"}),
    "porch": Setting(place="the porch", indoors=False, affords={"flash", "invasion"}),
}

SPARKS = {
    "lamp": Spark(
        id="lamp",
        verb="shine the lamp",
        gerund="shining the lamp",
        rush="wave the lamp faster",
        flash="a bright flash",
        mischief="more insects came fluttering in",
        tags={"flash", "light"},
    ),
    "mirror": Spark(
        id="mirror",
        verb="glint the mirror",
        gerund="glinting the mirror",
        rush="tilt the mirror again",
        flash="a sharp flash",
        mischief="the shiny beam invited more buzzing guests",
        tags={"flash", "light"},
    ),
    "pan": Spark(
        id="pan",
        verb="polish the pan",
        gerund="polishing the pan",
        rush="spin the pan around",
        flash="a comic flash",
        mischief="the gleam made the whole swarm swoop lower",
        tags={"flash", "humor"},
    ),
}

PRIZES = {
    "honeycake": Prize(id="honeycake", label="honey cake", phrase="a warm honey cake", region="table"),
    "seedbag": Prize(id="seedbag", label="seed bag", phrase="a tidy seed bag", region="hooks"),
    "teacup": Prize(id="teacup", label="teacup", phrase="a tiny teacup", region="shelf"),
}

REMEDIES = {
    "lanternshade": Remedy(
        id="lanternshade",
        label="a paper lantern shade",
        phrase="a soft paper shade",
        covers={"light"},
        calms={"flash"},
        prep="set a paper shade over the lamp",
        tail="placed the paper shade over the lamp",
    ),
    "curtain": Remedy(
        id="curtain",
        label="a cloth curtain",
        phrase="a thick cloth curtain",
        covers={"flash"},
        calms={"flash"},
        prep="draw the curtain over the bright place",
        tail="drew the curtain across the bright opening",
        plural=False,
    ),
    "hatbox": Remedy(
        id="hatbox",
        label="a hatbox lid",
        phrase="a round lid",
        covers={"light"},
        calms={"flash"},
        prep="put the lid on the shining object",
        tail="set the lid over the shine",
    ),
}

HERO_NAMES = ["Timo", "Mira", "Jori", "Nina", "Pip", "Luna", "Oren", "Sana"]
TYPES = ["keeper", "farmer", "baker", "child"]
HELPERS = ["mouse", "goat", "cat", "duck"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for spark in setting.affords:
            for prize in PRIZES:
                combos.append((place, spark, prize))
    return combos


def reasonableness_gate(spark: Spark, prize: Prize, remedy: Remedy) -> bool:
    return "flash" in spark.tags and "flash" in remedy.calms and prize.region in {"table", "hooks", "shelf"}


ASP_RULES = r"""
spark(S) :- spark_kind(S).
prize(P) :- prize_kind(P).
remedy(R) :- remedy_kind(R).

compatible(S,P,R) :- spark(S), prize(P), remedy(R), calms(R, flash), region(P, table; hooks; shelf).
valid(Place,S,P) :- affords(Place,S), spark(S), prize(P), compatible(S,P,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        if setting.indoors:
            lines.append(asp.fact("indoors", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for sid, s in SPARKS.items():
        lines.append(asp.fact("spark_kind", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("tag", sid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize_kind", pid))
        lines.append(asp.fact("region", pid, p.region))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy_kind", rid))
        for c in sorted(r.calms):
            lines.append(asp.fact("calms", rid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def tell(setting: Setting, spark: Spark, prize: Prize, remedy: Remedy,
         hero_name: str, hero_type: str, helper_type: str) -> World:
    w = World(setting)
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = w.add(Entity(id="Helper", kind="character", type=helper_type))
    item = w.add(Entity(id=prize.id, type=prize.id, label=prize.label, phrase=prize.phrase, owner=hero.id))
    shade = w.add(Entity(id=remedy.id, type="remedy", label=remedy.label, phrase=remedy.phrase, owner=hero.id, plural=remedy.plural))

    hero.memes["pride"] = 1
    hero.memes["curiosity"] = 1
    w.say(f"{hero_name} was a {hero_type} who loved a fine shine and thought every bright thing was a joke waiting to happen.")
    w.say(f"{hero.pronoun().capitalize()} kept {item.phrase} near the {setting.place}, where {helper_type}s and breezes could sniff around.")
    w.para()
    w.say(f"One evening, {hero_name} took up the {spark.id} and began {spark.gerund}.")
    w.say(f"The air answered with {spark.flash}, and soon {spark.mischief}.")
    hero.meters["flash"] += 1
    w.flash_on = True
    w.invasion += 1
    if spark.id == "pan":
        hero.memes["humor"] += 1

    # The comic invasion.
    hero.memes["alarm"] = 1
    helper.memes["busy"] = 1
    w.para()
    w.say(f"The little invasion grew into a buzzing parade of moths, beetles, and one very determined goose who had not been invited.")
    w.say(f"{hero_name} tried to {spark.rush}, but that only made the crowd wobble and swirl closer.")
    if w.flash_on:
        w.say(f"Every extra flash made the yard look like a festival for tiny wings.")

    # Turn: reasoned remedy.
    w.para()
    hero.memes["humility"] = 1
    w.say(f"{helper_type.capitalize()} looked up and said, 'If you keep boasting with that shine, the whole neighborhood will come to stare.'")
    w.say(f"{hero_name} blinked, chuckled at the silly little invasion, and chose a quieter trick.")
    shade.worn_by = hero.id
    w.flash_on = False
    w.say(f"{hero_name} {remedy.tail}, and the bright trouble began to settle.")

    # Resolution.
    hero.memes["joy"] = 1
    hero.memes["pride"] = 0
    hero.meters["calm"] = 1
    w.para()
    w.say(f"At last the yard grew peaceful again. The insects drifted toward the moon, the goose pecked a crumb, and {hero_name} shared {item.phrase} instead of shining for applause.")
    w.say(f"The little lesson was plain: a gentle light can guide, but a bragging flash only invites a crowd.")
    w.facts = {
        "hero": hero,
        "helper": helper,
        "prize": item,
        "remedy": shade,
        "spark": spark,
        "setting": setting,
    }
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    spark = _safe_fact(world, f, "spark")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short fable for a child about a {hero.type} named {hero.id}, a {spark.id}, and a comic invasion.',
        f'Tell a humorous story where {hero.id} learns that a loud flash can attract more trouble near {prize.label}.',
        f'Write a gentle moral story that includes the words "flash" and "invasion" and ends with a quieter solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    spark = _safe_fact(world, f, "spark")
    prize = _safe_fact(world, f, "prize")
    remedy = _safe_fact(world, f, "remedy")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero.type} who loved bright tricks and learned a wiser way.",
        ),
        QAItem(
            question=f"What caused the comic invasion?",
            answer=f"The invasion began when {hero.id} used the {spark.id} and made a {spark.flash.lower()} in the yard.",
        ),
        QAItem(
            question=f"What was {hero.id} supposed to protect?",
            answer=f"{hero.id} wanted to protect {prize.phrase} from the noisy crowd of insects and the silly goose.",
        ),
        QAItem(
            question=f"How did the trouble calm down?",
            answer=f"{hero.id} used {remedy.label} and stopped flashing so much, which let the invasion drift away.",
        ),
        QAItem(
            question=f"Who helped with the lesson?",
            answer=f"The {helper.type} helped by speaking plainly and reminding {hero.id} that boasting with light only makes more commotion.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flash?",
            answer="A flash is a quick burst of bright light that appears for a moment and then fades.",
        ),
        QAItem(
            question="What is an invasion?",
            answer="An invasion is when lots of visitors or things arrive all at once and crowd into a place.",
        ),
        QAItem(
            question="Why can too much shining be funny in a story?",
            answer="Too much shining can be funny because it can make characters act proudly and attract a silly crowd.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"{e.id}: ({e.type}) {' '.join(bits)}")
    out.append(f"flash_on={world.flash_on} invasion={world.invasion}")
    return "\n".join(out)


def explain_rejection() -> str:
    return "(No story: the requested choices do not support a believable flash-invasion fable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous fable world about flash and invasion.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--spark", choices=SPARKS.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--remedy", choices=REMEDIES.keys())
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--helper-type", choices=HELPERS)
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
    if getattr(args, "spark", None):
        combos = [c for c in combos if c[1] == getattr(args, "spark", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, spark, prize = rng.choice(list(combos))
    remedy = getattr(args, "remedy", None) or rng.choice(sorted(REMEDIES.keys()))
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPERS)
    return StoryParams(place=place, spark=spark, prize=prize, remedy=remedy, hero_name=hero_name, hero_type=hero_type, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SPARKS, params.spark), _safe_lookup(PRIZES, params.prize), _safe_lookup(REMEDIES, params.remedy), params.hero_name, params.hero_type, params.helper_type)
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


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("courtyard", "lamp", "honeycake", "lanternshade", "Timo", "keeper", "mouse"),
            StoryParams("garden", "mirror", "seedbag", "curtain", "Mira", "farmer", "goat"),
            StoryParams("barn", "pan", "teacup", "hatbox", "Jori", "baker", "duck"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
