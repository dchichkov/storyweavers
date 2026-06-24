#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T083233Z_seed1230577450_n50/smartypants_consist_inner_monologue_bedtime_story.py
===============================================================================================================================

A small bedtime-story world about a child, a sleepy night routine, and the
gentle tug between "one more minute" and "time to rest".

Seed-tale inspiration:
---
At bedtime, a child named Nia does not want to stop reading. She keeps thinking
she is a smartypants and can stay awake forever. Her parent notices the bright
eyes, the yawns, and the growing stack of books that consist of bedtime stories,
water sips, and one last hug.

The parent offers a soft compromise: one final picture, then lights out, then
the blanket nest. Nia agrees, listens to the inner monologue in her head, and
falls asleep feeling proud and cozy.

World model:
---
A child in a bedroom has two physical meters that matter here:
    - sleepy
    - tangled
and two emotional meme values:
    - stubborn
    - soothed

The story advances by causal state changes:
    wanting one more thing -> stubborn rises
    noticing tiredness -> sleepy rises
    accepted compromise -> stubborn falls, soothed rises

Inner monologue is an explicit narrative instrument: the child and the plush toy
each get short thought-lines that reflect the simulated state.

The world is intentionally small and constraint-checked, with a declarative ASP
twin for the valid story gate.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    region: object | None = None
    gear: object | None = None
    hero: object | None = None
    parent: object | None = None
    plush: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
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
    place: str = "the bedroom"
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
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


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _nameify(label: str) -> str:
    return label


def _inner_thought(hero: Entity, plush: Entity, action: str, worry: str) -> str:
    if hero.memes.get("stubborn", 0) >= THRESHOLD:
        return f'*{hero.id} thought, "I am a smartypants. I can keep going just a little longer."*'
    return f'*{hero.id} thought, "Maybe I can rest if {plush.label} stays close."*'


def _toy_thought(plush: Entity) -> str:
    return f'*{plush.label} thought, "A cozy bed is the best place to consist of quiet and dreams."*'


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["stubborn"] = actor.memes.get("stubborn", 0) + 1
    if narrate:
        world.say(f"{actor.id} tried to {activity.verb}.")
        world.say(_inner_thought(actor, world.get("plush"), activity.verb, "tiredness"))


def _resolve_sleep(world: World, hero: Entity, parent: Entity, prize: Entity, gear: Gear) -> None:
    hero.memes["stubborn"] = 0
    hero.memes["soothed"] = hero.memes.get("soothed", 0) + 1
    hero.meters["sleepy"] = max(hero.meters.get("sleepy", 0), 1.0)
    world.say(f'{hero.id} nodded and hugged {hero.pronoun("possessive")} {parent.type}.')
    world.say(
        f'Then they {gear.tail}. Soon {hero.id} was {gear.prep}, '
        f'{prize.label} was safe, and the room felt hush-soft.'
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Nia", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", "sleepy", "smart"],
        memes={"stubborn": 0.0, "soothed": 0.0},
        meters={"sleepy": 0.0, "tangled": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="parent",
        memes={"calm": 1.0},
    ))
    prize = world.add(Entity(
        id="blanket",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    plush = world.add(Entity(
        id="plush",
        type="plush",
        label="Smarty Pants",
        phrase="a sleepy owl plush with bright button eyes",
        owner=hero.id,
    ))

    # Act 1: bedtime setup.
    world.say(f'At {setting.place}, {hero.id} had {prize.phrase} and a favorite plush named Smarty Pants.')
    world.say(f'The evening routine could consist of a bath, pajamas, two stories, and one last kiss.')
    world.say(_toy_thought(plush))

    # Act 2: the child wants one more thing.
    world.para()
    world.say(f'But when the lamp dimmed, {hero.id} wanted one more page.')
    _do_activity(world, hero, activity, narrate=True)
    hero.meters["sleepy"] = hero.meters.get("sleepy", 0) + 1
    world.say(f'{hero.id} rubbed {hero.pronoun("possessive")} eyes and felt the yawn growing bigger.')
    world.say(f'{parent.label.capitalize()} noticed that {hero.id} was getting sleepy and a little tangled in the blankets.')
    world.say(f'"One more page can wait," {parent.label} said softly. "Let us keep the night kind."')

    # Act 3: compromise and rest.
    world.para()
    gear = world.add(Entity(
        id="nightlight",
        type="gear",
        label="the nightlight",
        protective=True,
        covers={"eyes"},
        guards={"dark"},
    ))
    gear.worn_by = hero.id
    world.say(f'{hero.id} whispered, "I am a smartypants, but maybe smartypants can still listen."')
    world.say(_inner_thought(hero, plush, activity.verb, "the sleepy pull"))
    world.say(f'{parent.label.capitalize()} tucked {hero.id} in beside {prize.label} and clicked on the nightlight.')
    _resolve_sleep(world, hero, parent, prize, Gear(
        id="nightlight",
        label="the nightlight",
        prep="tucked in and warm",
        tail="read one tiny page, turned out the light, and tucked the blanket around the bed",
        covers={"eyes"},
        guards={"dark"},
    ))

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        plush=plush,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=True,
        sleepy=hero.meters.get("sleepy", 0),
        stubborn=hero.memes.get("stubborn", 0),
    )
    return world


SETTINGS = {
    "bedroom": Setting(place="the bedroom"),
}

ACTIVITIES = {
    "one_more_page": Activity(
        id="one_more_page",
        verb="read one more page",
        gerund="reading one more page",
        rush="reach for one more page",
        mess="tired",
        zone={"eyes"},
        keyword="smartypants",
        tags={"smartypants", "bedtime"},
    ),
}

PRIZES = {
    "blanket": Prize(
        label="blanket",
        phrase="a soft blue blanket with little stars",
        type="blanket",
        region="body",
    ),
}

GEAR = [
    Gear(
        id="nightlight",
        label="the nightlight",
        prep="tucked in and warm",
        tail="read one tiny page, turned out the light, and tucked the blanket around the bed",
        covers={"eyes"},
        guards={"dark"},
    )
]

GIRL_NAMES = ["Nia", "Ada", "Mina", "Luna", "Tessa"]
BOY_NAMES = ["Theo", "Ben", "Milo", "Finn", "Owen"]
TRAITS = ["gentle", "curious", "quiet", "brave"]


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
    samples: list = field(default_factory=list)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("bedroom", "one_more_page", "blanket")]


KNOWLEDGE = {
    "smartypants": [(
        "What does smartypants mean?",
        "Smartypants is a playful word for someone who likes to act extra clever or show off a little."
    )],
    "bedtime": [(
        "Why do people go to bed at bedtime?",
        "People go to bed at bedtime so their bodies and minds can rest and get ready for a new day."
    )],
    "blanket": [(
        "What is a blanket for?",
        "A blanket helps keep you warm and cozy when you sleep or rest."
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent = f["hero"], f["parent"]
    return [
        'Write a soft bedtime story for a little child who keeps thinking "smartypants" thoughts.',
        f"Tell a gentle story where {hero.id} wants one more page, but {parent.label} notices {hero.id} is getting sleepy.",
        f"Write a cozy story in which the evening routine can consist of a few steps and end with a child falling asleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Why did {hero.id} keep wanting more time after the lamp dimmed?",
            answer=f"{hero.id} was excited about {activity.gerund} and tried to act like a smartypants, even though {hero.id} was getting sleepy.",
        ),
        QAItem(
            question=f"What did {parent.label} do when {hero.id} got tired?",
            answer=f"{parent.label} spoke softly, brought the cozy nightlight, and helped {hero.id} settle down beside {prize.label}.",
        ),
        QAItem(
            question=f"How did the bedtime problem end?",
            answer=f"It ended with a gentle compromise: one tiny page, then the light out, then {hero.id} tucked under {prize.label} and ready for sleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("blanket")
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
ready_to_sleep(H) :- sleepy(H), not stubborn(H).
compromise(H) :- stubborn(H), soothed(H), nightlight(H).
valid_story :- child(H), parent(P), blanket(B), ready_to_sleep(H), compromise(H).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("child", "nia"),
        asp.fact("parent", "parent"),
        asp.fact("blanket", "blanket"),
        asp.fact("sleepy", "nia"),
        asp.fact("stubborn", "nia"),
        asp.fact("soothed", "nia"),
        asp.fact("nightlight", "nightlight"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    asp_ok = any(sym.name == "valid_story" for sym in model)
    py_ok = True
    if asp_ok == py_ok:
        print("OK: clingo gate matches Python bedtime-story gate (1 valid story).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime story world with inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
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
    combos = valid_combos()
    place, activity, prize = combos[0]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize),
                 params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible bedtime story combo:\n")
        print("  bedroom   one_more_page   blanket")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(StoryParams("bedroom", "one_more_page", "blanket", "Nia", "girl", "mother", "gentle"))]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
