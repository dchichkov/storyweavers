#!/usr/bin/env python3
"""
Story world: a rhyming tale about a specimen, a technicolored mix-up,
humor, problem solving, and a lesson learned.

The simulated premise:
- A careful child helpers a museum keeper with a specimen display.
- A technicolored marker set causes a splashy mistake.
- The child uses a simple plan to fix the display.
- The ending proves the specimen is safe and the lesson sticks.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protected: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    entities: set[str] = field(default_factory=set)
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
    afford: set[str] = field(default_factory=set)
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
    tags: set[str] = field(default_factory=set)
    keyword: str = ""
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
    preserve: str
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
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

    def say(self, line: str) -> None:
        if line:
            self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        other = World(self.setting)
        other.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        other.lines = []
        other.facts = dict(self.facts)
        return other


SETTINGS = {
    "museum": Setting(place="the museum", afford={"paint", "glue", "glitter"}),
    "classroom": Setting(place="the classroom", afford={"paint", "glue", "glitter"}),
    "studio": Setting(place="the art studio", afford={"paint", "glue", "glitter"}),
}

ACTIVITIES = {
    "paint": Activity(
        id="paint",
        verb="paint a sign",
        gerund="painting a sign",
        rush="dash for the paints",
        mess="painted",
        soil="spotted with paint",
        tags={"humor", "problem_solving", "lesson", "technicolored"},
        keyword="technicolored",
    ),
    "glitter": Activity(
        id="glitter",
        verb="sprinkle glitter",
        gerund="sprinkling glitter",
        rush="grab the glitter jar",
        mess="sparkly",
        soil="sparkly all over",
        tags={"humor", "problem_solving", "lesson", "technicolored"},
        keyword="specimen",
    ),
    "glue": Activity(
        id="glue",
        verb="build a tiny frame",
        gerund="building a tiny frame",
        rush="reach for the glue",
        mess="sticky",
        soil="sticky and messy",
        tags={"humor", "problem_solving", "lesson"},
        keyword="specimen",
    ),
}

PRIZES = {
    "specimen": Prize(
        label="specimen",
        phrase="a delicate butterfly specimen in a glass case",
        type="specimen",
        preserve="careful",
        region="table",
    ),
    "poster": Prize(
        label="poster",
        phrase="a bright wall poster",
        type="poster",
        preserve="flat",
        region="wall",
    ),
    "card": Prize(
        label="card",
        phrase="a display card with neat print",
        type="card",
        preserve="dry",
        region="table",
    ),
}

FIXES = [
    Fix(
        id="cover_sheet",
        label="a clear cover sheet",
        prep="put a clear cover sheet over the specimen",
        tail="slipped a clear cover sheet on top",
        guards={"painted", "sparkly", "sticky"},
        covers={"table"},
    ),
    Fix(
        id="dry_cloth",
        label="a soft dry cloth",
        prep="wipe the table first with a soft dry cloth",
        tail="wiped the table dry first",
        guards={"painted", "sticky"},
        covers={"table"},
    ),
    Fix(
        id="marker_tray",
        label="a marker tray",
        prep="move the technicolored markers into a tray",
        tail="moved the technicolored markers into a tray",
        guards={"painted", "sparkly"},
        covers={"table"},
    ),
]

NAMES = ["Milo", "Nina", "Pip", "Tara", "Owen", "Ivy", "Lena", "Ezra"]
TYPES = ["girl", "boy"]
PARENTS = ["mother", "father"]
TRAITS = ["curious", "cheery", "funny", "gentle", "brave"]


def rhyme_line(*parts: str) -> str:
    return " ".join(parts).rstrip()


def risk(activity: Activity, prize: Prize) -> bool:
    return prize.region == "table" and activity.mess in {"painted", "sparkly", "sticky"}


def select_fix(activity: Activity, prize: Prize) -> Optional[Fix]:
    for fx in FIXES:
        if activity.mess in fx.guards and prize.region in fx.covers:
            return fx
    return None


def forecast(world: World, actor: Entity, activity: Activity, prize: Entity) -> bool:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return sim.get(prize.id).meters.get("dirty", 0.0) >= THRESHOLD


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["glee"] = actor.memes.get("glee", 0.0) + 1.0
    prize = world.facts.get("prize")
    if prize:
        pr = world.get(prize.id)
        if risk(activity, world.facts["prize_cfg"]) and world.facts.get("fixed") is None:
            pr.meters["dirty"] = pr.meters.get("dirty", 0.0) + 1.0
            pr.meters[activity.mess] = pr.meters.get(activity.mess, 0.0) + 1.0
            if narrate:
                world.say(f"{actor.id} made a little mess, and the specimen looked less than blessed.")
    if narrate:
        world.say(f"{actor.id} did {activity.gerund}, with a grin that was wide and bright as a sunbeam spin.")


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.memes.get('trait', 'curious')} {hero.type} with a step so spry and light.")


def setup(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(f"At {world.setting.place}, the child and {parent.label} prepared for a busy sight.")
    world.say(f"They loved the {prize.label}, neat and sweet, and the {activity.keyword or activity.id} made the day feel neat.")


def want(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} wanted to {activity.verb}, with a hop and a pop and a tip-top trot.")
    world.say(f"But the bins were near, and a funny idea appeared in the child's bright thought.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    if forecast(world, hero, activity, prize):
        world.say(f'"Careful now," said {parent.id}, "or the {prize.label} may end up in a spot of blot."')
        world.say(f'"That would be a mess," said {hero.id}, "and that would not be what we sought."')


def problem(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} paused in the middle, then chuckled a little, then thought and thought.")
    world.say(f"The tools were in sight, but the right one had to be chosen just right, not bought in a hasty lot.")


def fix_it(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Fix]:
    fx = select_fix(activity, prize)
    if fx is None:
        return None
    world.facts["fixed"] = fx
    world.say(f"Then {parent.id} smiled and said, \"Let's try {fx.label}, and keep the specimen from trouble and rot.\"")
    world.say(f"{hero.id} nodded and {fx.prep}, with a careful touch and a jolly lot.")
    return fx


def resolve(world: World, hero: Entity, activity: Activity, prize: Entity, fx: Optional[Fix]) -> None:
    if fx is None:
        return
    world.facts["prize"].meters["dirty"] = 0.0
    world.say(f"{fx.tail}, then {hero.id} could {activity.verb} with a giggle and a dot-dot-dot.")
    world.say(f"The specimen stayed safe and fine, and the room felt tidy, twinkly, and hot with not.")
    world.say(f"{hero.id} learned that a good fix, picked with care, can save the day from a flop and a flop and a flop.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"trait": trait}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg, activity=activity)
    introduce(world, hero)
    setup(world, hero, parent, prize, activity)
    want(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    problem(world, hero, activity)
    fx = fix_it(world, parent, hero, activity, prize)
    world.facts["fixed"] = fx
    resolve(world, hero, activity, prize, fx)
    return world


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story about a {f["prize"].label} and a technicolored problem.',
        f"Tell a child-friendly tale where {f['hero'].id} wants to {f['activity'].verb} but must solve a mess.",
        f"Write a funny lesson-learned story at {world.setting.place} with a specimen and a careful fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    fx = f.get("fixed")
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, and the wish was bright and full of cheer.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the {prize.label}?",
            answer=f"{parent.id} worried because the {prize.label} could get {act.soil if act.soil else 'messy'} if the fun got too near.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=(
                f"They used {fx.label} to protect the display and keep the specimen safe, "
                f"so {hero.id} could play without making a sticky smear."
                if fx else
                "They did not find a safe fix, so the plan had to wait a year."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a specimen?",
            answer="A specimen is an example of something kept to study or show, like a bug, leaf, or shell in a case.",
        ),
        QAItem(
            question="What does technicolored mean?",
            answer="Technicolored means full of many bright colors, like a rainbow on a page or wall.",
        ),
        QAItem(
            question="Why do people use a cover sheet?",
            answer="A cover sheet helps keep paint, glitter, or sticky bits away from something delicate.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about a specimen and a technicolored fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=TYPES)
    ap.add_argument("--parent", choices=PARENTS)
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
    activity = getattr(args, "activity", None) or rng.choice(sorted(_safe_lookup(SETTINGS, place).afford))
    prize = getattr(args, "prize", None) or "specimen"
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in TYPES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(TYPES)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    act = _safe_lookup(ACTIVITIES, activity)
    pr = _safe_lookup(PRIZES, prize)
    if not risk(act, pr):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent, params.trait)
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


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), splashes(A, table), worn_on(P, table).
fixes(A, P, F) :- prize_at_risk(A, P), guards(F, M), mess_of(A, M), covers(F, table).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), fixes(A, P, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        lines.append(asp.fact("splashes", aid, "table"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for g in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, g))
        for c in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for act in s.afford:
            for pr in PRIZES:
                if risk(_safe_lookup(ACTIVITIES, act), _safe_lookup(PRIZES, pr)) and select_fix(_safe_lookup(ACTIVITIES, act), _safe_lookup(PRIZES, pr)):
                    out.append((place, act, pr))
    return sorted(out)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
        return 0
    print("Mismatch.")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


CURATED = [
    StoryParams(place="museum", activity="paint", prize="specimen", name="Milo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="classroom", activity="glitter", prize="specimen", name="Ivy", gender="girl", parent="mother", trait="cheery"),
    StoryParams(place="studio", activity="glue", prize="specimen", name="Pip", gender="boy", parent="mother", trait="funny"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
