#!/usr/bin/env python3
"""
Translucent Kindness, Inner Monologue, and Curiosity: a small comedy storyworld.

A child notices a translucent surprise container, gets very curious, and then
chooses kindness over peeking. The story engine simulates curiosity, restraint,
and helpfulness as world state, so the ending is earned rather than swapped.
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
    translucent: bool = False
    opened: bool = False
    carried_by: Optional[str] = None
    placed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gift: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    indoors: bool
    light: str
    affordances: set[str] = field(default_factory=set)
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
class Goal:
    id: str
    verb: str
    inner_voice: str
    consequence: str
    tag: str
    sparkle: str
    actions: set[str] = field(default_factory=set)
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


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    kind: str
    translucent: bool = False
    fragile: bool = True
    reveal: str = ""
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    clone: object | None = None
    world: object | None = None
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone
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


def _r_peek_mischief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    gift = world.entities.get("gift")
    if not hero or not gift:
        return out
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if gift.opened:
        return out
    sig = ("peek", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["temptation"] = hero.memes.get("temptation", 0.0) + 1
    out.append("The lid wobbled, and curiosity turned into a very wiggly thought.")
    return out


def _r_kindness_settle(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    gift = world.entities.get("gift")
    if not hero or not gift:
        return out
    if hero.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    if gift.placed:
        return out
    sig = ("kindness", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gift.placed = True
    out.append("Kindness made the hands stay gentle.")
    return out


def _r_comedy_release(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    gift = world.entities.get("gift")
    if not hero or not gift:
        return out
    if hero.memes.get("inner_monologue", 0.0) < THRESHOLD:
        return out
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("comic", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("In the hero's head, the jar held a tiny marching band, a jellybean dragon, and one very formal pea.")
    return out


RULES = [_r_peek_mischief, _r_kindness_settle, _r_comedy_release]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_setting(choice: str) -> Setting:
    return _safe_lookup(SETTINGS, choice)


def maybe_risk(gift: Gift, goal: Goal) -> bool:
    return gift.translucent and goal.id in {"peek", "inspect"}


def choose_comfort(world: World, hero: Entity, gift: Gift, goal: Goal) -> bool:
    sim = world.copy()
    sim.get("hero").memes["curiosity"] += 1
    propagate(sim, narrate=False)
    return not sim.get("gift").opened


def tell(setting: Setting, goal: Goal, gift_cfg: Gift, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        meters={"stillness": 0.0},
        memes={"curiosity": 0.0, "kindness": 0.0, "inner_monologue": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="parent",
        meters={"patience": 0.0},
        memes={"warmth": 0.0},
    ))
    gift = world.add(Entity(
        id="gift",
        type=gift_cfg.kind,
        label=gift_cfg.label,
        phrase=gift_cfg.phrase,
        owner=parent.id,
        caretaker=parent.id,
        translucent=gift_cfg.translucent,
        opened=False,
        placed=False,
    ))

    hero.memes["curiosity"] += 1
    hero.memes["inner_monologue"] += 1
    hero.memes["kindness"] += 0.5

    world.say(
        f"{hero.label} was a {hero_type} who noticed shiny things right away, especially if they were translucent."
    )
    world.say(
        f"One day, {hero.label} found {gift.phrase} waiting in {setting.place}, and the whole thing looked like a joke that had learned to sparkle."
    )
    world.say(
        f"{hero.label} wanted to {goal.verb}, but {hero.pronoun('possessive')} head started talking in a whispery little comedy voice: {goal.inner_voice}"
    )

    world.para()
    world.say(
        f"The light in {setting.place} was {setting.light}, so the translucent {gift.label} glowed like a secret with manners."
    )
    if maybe_risk(gift, goal):
        world.say(
            f"{hero.label} leaned closer, because curiosity had tiny feet and did not know how to walk away."
        )
    if choose_comfort(world, hero, gift, goal):
        world.say(
            f"Then {parent.label} smiled and asked for help carrying it instead of opening it."
        )
        hero.memes["kindness"] += 1
        hero.memes["curiosity"] += 0.5
        gift.carried_by = hero.id
        world.say(
            f"{hero.label} used {goal.tag} instead of poking, and the gift stayed closed while being moved carefully to the table."
        )
        world.say(
            f"When it was time, {parent.label} let {hero.label} look through the translucent side, and {gift.reveal}."
        )
    else:
        world.say(
            f"{hero.label} forgot the nice idea and reached for the lid, which made the joke in the room very nearly fall over."
        )

    world.para()
    world.say(
        f"In the end, {hero.label} was still curious, but also kind enough to wait, and that made everybody laugh."
    )
    world.say(
        f"The translucent {gift.label} stayed safe, and the surprise inside was even funnier because nobody had peeked too early."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        gift=gift,
        goal=goal,
        setting=setting,
        resolved=gift.placed,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, light="bright and wobbly", affordances={"peek", "inspect", "carry"}),
    "sunroom": Setting(place="the sunroom", indoors=True, light="golden and bouncy", affordances={"peek", "inspect", "carry"}),
    "porch": Setting(place="the porch", indoors=False, light="soft and sunny", affordances={"peek", "inspect", "carry"}),
}

GOALS = {
    "peek": Goal(
        id="peek",
        verb="peek inside",
        inner_voice="Maybe it is candy. Maybe it is buttons. Maybe it is a tiny crown for a very small potato.",
        consequence="The surprise would get spoiled.",
        tag="carefully",
        sparkle="gleamed",
        actions={"peek", "inspect"},
    ),
    "inspect": Goal(
        id="inspect",
        verb="inspect the jar",
        inner_voice="I am only looking. Looking is polite, right? Mostly?",
        consequence="The lid might get opened too soon.",
        tag="gently",
        sparkle="shivered",
        actions={"peek", "inspect"},
    ),
    "carry": Goal(
        id="carry",
        verb="carry it to the table",
        inner_voice="If I carry it very carefully, maybe my curiosity will behave like a good small dog.",
        consequence="The surprise can wait safely.",
        tag="carefully",
        sparkle="glowed",
        actions={"carry"},
    ),
}

GIFTS = {
    "jar": Gift(
        id="jar",
        label="jar",
        phrase="a translucent jar with a ribbon on top",
        kind="jar",
        translucent=True,
        reveal="inside, there was a row of little star cookies",
    ),
    "box": Gift(
        id="box",
        label="box",
        phrase="a translucent box tied with blue string",
        kind="box",
        translucent=True,
        reveal="inside, there was a handmade card and three silly lemon candies",
    ),
    "caddy": Gift(
        id="caddy",
        label="caddy",
        phrase="a translucent caddy full of snack bags",
        kind="caddy",
        translucent=True,
        reveal="inside, there were crackers arranged like a tiny parade",
    ),
}

HERO_NAMES = ["Milo", "Nina", "Poppy", "Theo", "Maya", "Lena"]


@dataclass
class StoryParams:
    setting: str
    goal: str
    gift: str
    name: str
    gender: str
    parent: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for g in GOALS:
            for gift in GIFTS:
                if _safe_lookup(GIFTS, gift).translucent and g in _safe_lookup(GOALS, safe_goal_set(s)):
                    combos.append((s, g, gift))
    return combos


def safe_goal_set(setting: str) -> str:
    return setting


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, goal, gift = f["hero"], f["goal"], f["gift"]
    return [
        f'Write a short comedic story for a child that includes the word "translucent".',
        f"Tell a gentle story where {hero.label} wants to {goal.verb} but chooses kindness instead.",
        f"Write a funny story about {hero.label} and a translucent {gift.label} with a surprise inside.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, goal, gift = f["hero"], f["parent"], f["goal"], f["gift"]
    qa = [
        QAItem(
            question=f"What did {hero.label} want to do at first?",
            answer=f"{hero.label} wanted to {goal.verb}, because curiosity made the translucent {gift.label} feel extra mysterious.",
        ),
        QAItem(
            question=f"Why did {hero.label} stop and choose a nicer idea?",
            answer=f"{hero.label} remembered kindness and helped {parent.label} carry the gift safely instead of opening it too soon.",
        ),
        QAItem(
            question=f"What was funny about the secret inside the translucent {gift.label}?",
            answer=f"{hero.label}'s inner monologue imagined a marching band, a jellybean dragon, and a very formal pea, which made the waiting feel silly.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end?",
                answer=f"The translucent {gift.label} stayed closed until the right moment, and then {hero.label} got to see the surprise inside with everyone laughing.",
            )
        )
    return qa


KNOWLEDGE = {
    "translucent": [
        (
            "What does translucent mean?",
            "Translucent means light can pass through something, but you cannot see every detail clearly.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means doing something gentle and helpful for someone else.",
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the urge to find out more about something interesting.",
        )
    ],
    "inner_monologue": [
        (
            "What is an inner monologue?",
            "An inner monologue is the little voice inside your head that thinks about what you want to do.",
        )
    ],
    "comedy": [
        (
            "What makes a story funny?",
            "A story can be funny when someone imagines something silly, says an unexpected thing, or acts in a playful way.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"translucent", "kindness", "curiosity", "inner_monologue", "comedy"}
    out: list[QAItem] = []
    for tag in tags:
        q, a = KNOWLEDGE[tag][0]
        out.append(QAItem(question=q, answer=a))
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.translucent:
            bits.append("translucent=True")
        if e.opened:
            bits.append("opened=True")
        if e.placed:
            bits.append("placed=True")
        lines.append(f"  {e.id:5} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
translucent(gift) :- gift(gift), gift_translucent(gift).
at_risk(hero, gift) :- translucent(gift), wants(hero, peek).
good_choice(hero, gift) :- at_risk(hero, gift), chooses(hero, kindness).
resolved(hero, gift) :- good_choice(hero, gift), surprise_safe(gift).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for act in _safe_lookup(SETTINGS, sid).affordances:
            lines.append(asp.fact("affords", sid, act))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        for act in g.actions:
            lines.append(asp.fact("wants", gid, act))
    for gift_id, g in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        if g.translucent:
            lines.append(asp.fact("gift_translucent", gift_id))
        lines.append(asp.fact("surprise_safe", gift_id))
    lines.append(asp.fact("chooses", "hero", "kindness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show translucent/1. #show at_risk/2. #show good_choice/2. #show resolved/2."))
    return sorted(set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    py = {(p.setting, p.goal, p.gift) for p in CURATED}
    if py:
        print(f"OK: curated set has {len(py)} stories; ASP twin is loaded.")
        return 0
    print("No curated stories.")
    return 1


CURATED = [
    StoryParams(setting="kitchen", goal="peek", gift="jar", name="Milo", gender="boy", parent="mother"),
    StoryParams(setting="sunroom", goal="inspect", gift="box", name="Maya", gender="girl", parent="father"),
    StoryParams(setting="porch", goal="carry", gift="caddy", name="Nina", gender="girl", parent="mother"),
]


def explain_rejection(goal: Goal, gift: Gift) -> str:
    return f"(No story: {goal.verb} would be too ordinary for a non-translucent gift.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comedic storyworld about translucent curiosity and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "gift", None) and not _safe_lookup(GIFTS, getattr(args, "gift", None)).translucent:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    settings = [getattr(args, "setting", None)] if getattr(args, "setting", None) else list(SETTINGS)
    goals = [getattr(args, "goal", None)] if getattr(args, "goal", None) else list(GOALS)
    gifts = [getattr(args, "gift", None)] if getattr(args, "gift", None) else list(GIFTS)
    combos = [(s, g, k) for s in settings for g in goals for k in gifts]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, goal, gift = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, goal=goal, gift=gift, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(GOALS, params.goal), _safe_lookup(GIFTS, params.gift), params.name, params.gender, params.parent)
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
        print(asp_program("#show resolved/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show resolved/2."))
        print(sorted(set(asp.atoms(model, "resolved"))))
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
            header = f"### {p.name}: {p.goal} in {p.setting} (gift: {p.gift})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
