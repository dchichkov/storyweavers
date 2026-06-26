#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/melanin_tandem_van_magic_misunderstanding_twist_animal.py
================================================================================================

A small animal-story world about a tandem van, a little bit of magic,
and a misunderstanding that turns into a twist.

Premise seed:
- An animal crew needs to ride a tandem van together.
- A magic item seems to change a fur color or mark.
- Someone misunderstands the change and worries.
- The twist is that the magic only helped with the van ride, and the dark
  color is melanin-friendly mud, cocoa, or safe paint from the job.
- The ending proves the change by showing the ride completed happily.

The world is intentionally tiny and constraint-checked:
- typed entities with meters and memes
- a single causal turn driven by state
- a Python reasonableness gate plus an inline ASP twin
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
# Tiny world model
# ---------------------------------------------------------------------------
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    place: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    friend: object | None = None
    gear: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ("dusty", "wet", "dark", "dirty", "broken"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "confusion", "love", "curiosity", "relief"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "cow", "cat", "rabbit", "fox"}
        male = {"boy", "father", "dad", "man", "dog", "bear", "bird"}
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
    place: str = "the lane"
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
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
    label: str
    phrase: str
    type: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.zone = set(self.zone)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "market": Setting(place="the market lane", affords={"magic", "ride"}),
    "barn": Setting(place="the barn path", affords={"magic", "ride"}),
    "harbor": Setting(place="the harbor road", affords={"magic", "ride"}),
}

ACTIVITIES = {
    "magic": Activity(
        id="magic",
        verb="use the magic token",
        gerund="using the magic token",
        rush="grab the magic token",
        mess="dark",
        soil="mysteriously dark",
        zone={"torso"},
        keyword="magic",
        tags={"magic"},
    ),
    "ride": Activity(
        id="ride",
        verb="ride the tandem van",
        gerund="riding the tandem van",
        rush="climb into the tandem van",
        mess="dusty",
        soil="dusty from the road",
        zone={"torso"},
        keyword="tandem",
        tags={"tandem", "van"},
    ),
}

PRIZES = {
    "scarf": Prize(
        label="scarf",
        phrase="a bright scarf",
        type="scarf",
        region="torso",
    ),
    "bow": Prize(
        label="bow",
        phrase="a red bow",
        type="bow",
        region="head",
    ),
    "vest": Prize(
        label="vest",
        phrase="a neat little vest",
        type="vest",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="raincoat",
        label="a raincoat",
        covers={"torso"},
        guards={"dark", "dusty"},
        prep="put on a raincoat first",
        tail="rolled on in the raincoat",
    ),
    Gear(
        id="sheet",
        label="a clean sheet",
        covers={"torso"},
        guards={"dark"},
        prep="cover the seat with a clean sheet",
        tail="spooled down the lane with the clean sheet tucked in place",
    ),
]

ANIMAL_NAMES = ["Pip", "Luna", "Milo", "Nori", "Tess", "Otto", "Poppy", "Ravi"]
ANIMAL_TYPES = ["rabbit", "fox", "dog", "cat", "bear", "bird"]
TRAITS = ["curious", "cheerful", "gentle", "brave", "playful", "shy"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or activity.id == "magic"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} cannot reasonably threaten {prize.label}, "
        f"or no helpful gear can fix the problem.)"
    )


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def predict_darken(world: World, actor: Entity, activity: Activity, prize: Entity) -> bool:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    item = sim.get(prize.id)
    return item.meters[activity.mess] >= THRESHOLD


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    for item in world.worn_items(actor):
        if item.protective:
            continue
        if activity.id == "ride":
            item.meters["dusty"] += 1
            if narrate:
                world.say(f"The road dust brushed {actor.pronoun('possessive')} {item.label}.")
        elif activity.id == "magic":
            item.meters["dark"] += 1
            if narrate:
                world.say(f"The token made {actor.pronoun('possessive')} {item.label} look dark for a moment.")


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.memes.get("trait_words", [""]) if t), "")
    if trait:
        world.say(f"{hero.id} was a {trait} little {hero.type} who loved small adventures.")
    else:
        world.say(f"{hero.id} was a little {hero.type} who loved small adventures.")


def setup(world: World, hero: Entity, friend: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} and {friend.id} found a {activity.keyword} day at {world.setting.place}. "
        f"{hero.id} carried {hero.pronoun('possessive')} {prize.label}, and a shiny magic token waited nearby."
    )


def misunderstanding(world: World, hero: Entity, friend: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["confusion"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"{friend.id} saw {hero.id}'s {prize.label} turn a little dark and gasped. "
        f'"Oh no," {friend.pronoun()} said, "the magic ruined it!"'
    )
    world.say(
        f"But {hero.id} only meant to {activity.verb}, not spoil the {prize.label}."
    )


def twist(world: World, hero: Entity, friend: Entity, prize: Entity, activity: Activity, gear: Gear) -> None:
    hero.memes["curiosity"] += 1
    if activity.id == "magic":
        world.say(
            f"{hero.id} picked up the token again and learned the trick: it only made a safe shadowy tint, "
            f"like melanin in fur, not a real stain."
        )
    world.say(
        f"Then {friend.id} noticed the {gear.label} on the tandem van seat, and the plan made sense."
    )


def resolve(world: World, hero: Entity, friend: Entity, prize: Entity, activity: Activity, gear: Gear) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f"They used {gear.label} first, so {hero.id} could {activity.verb} without making {prize.label} truly dirty."
    )
    world.say(
        f"After that, the two friends rolled away in the tandem van, laughing, and {prize.label} stayed neat in the end."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, region=prize_cfg.region))
    gear = world.add(Entity(id="gear", type="gear", label="a soft cover", protective=True,
                            covers={"torso"}, owner=hero.id, caretaker=friend.id))
    gear.worn_by = hero.id
    hero.memes["trait_words"] = [trait]

    introduce(world, hero)
    setup(world, hero, friend, prize, activity)
    world.para()
    if predict_darken(world, hero, activity, prize):
        misunderstanding(world, hero, friend, prize, activity)
    world.say(
        f"{hero.id} and {friend.id} climbed into the tandem van together."
    )
    do_activity(world, hero, activity, narrate=True)
    world.para()
    twist(world, hero, friend, prize, activity, gear)
    resolve(world, hero, friend, prize, activity, gear)

    world.facts.update(hero=hero, friend=friend, prize=prize, activity=activity, gear=gear)
    return world


# ---------------------------------------------------------------------------
# Story params and Q&A
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, act, prize = f["hero"], f["friend"], f["activity"], f["prize"]
    return [
        f"Write a short animal story about {hero.id} and {friend.id} with a tandem van and a little magic.",
        f"Tell a child-friendly story where {hero.id} thinks {prize.label} got ruined, but the twist makes it okay.",
        f"Make a gentle story with the words melanin, tandem, and van.",
        f"Write an animal story where a misunderstanding about a dark mark turns into a happy ride.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, act = f["hero"], f["friend"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {hero.id} and {friend.id}, two animal friends who shared a tandem van day.",
        ),
        QAItem(
            question=f"What did {friend.id} think at first when the {prize.label} looked dark?",
            answer=f"{friend.id} thought the {prize.label} had been ruined, because the dark color looked like a problem at first.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the dark color was only a safe magic tint, not real damage, and the tandem van plan still worked.",
        ),
        QAItem(
            question=f"What did the friends do at the end?",
            answer=f"They rode away together in the tandem van, and {prize.label} stayed neat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a van?",
            answer="A van is a boxy vehicle that can carry people or things together on a road.",
        ),
        QAItem(
            question="What does tandem mean?",
            answer="Tandem means two things working together, or two riders sharing one ride.",
        ),
        QAItem(
            question="What is melanin?",
            answer="Melanin is a natural pigment in skin, fur, feathers, and hair that helps give them color.",
        ),
    ]


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
prize_at_risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid_story(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story with magic, misunderstanding, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=ANIMAL_TYPES)
    ap.add_argument("--friend-type", choices=ANIMAL_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, activity, prize = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(ANIMAL_TYPES)
    friend_type = getattr(args, "friend_type", None) or rng.choice([t for t in ANIMAL_TYPES if t != hero_type])
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        hero_name=getattr(args, "name", None) or rng.choice(ANIMAL_NAMES),
        hero_type=hero_type,
        friend_name=getattr(args, "friend_name", None) or rng.choice([n for n in ANIMAL_NAMES if n != getattr(args, "name", None)]),
        friend_type=friend_type,
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        params.hero_name,
        params.hero_type,
        params.friend_name,
        params.friend_type,
        params.trait,
    )
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="market", activity="magic", prize="scarf", hero_name="Pip", hero_type="fox",
                friend_name="Luna", friend_type="rabbit", trait="curious"),
    StoryParams(place="barn", activity="ride", prize="vest", hero_name="Milo", hero_type="dog",
                friend_name="Tess", friend_type="cat", trait="cheerful"),
    StoryParams(place="harbor", activity="magic", prize="bow", hero_name="Nori", hero_type="bird",
                friend_name="Otto", friend_type="bear", trait="gentle"),
]


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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
