#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sociology_dumb_tin_misunderstanding_conflict_quest_tall.py
=====================================================================================

A standalone story world about a child who mishears a school request for a
sociology fair, starts a wild tin quest, quarrels with a friend, and finally
learns what the town really needed.

This is told in a gentle Tall Tale mode: the prairie is too wide, the wind is
too loud, and the mistaken tin lion is much too large for good sense.

Run it
------
    python storyworlds/worlds/gpt-5.4/sociology_dumb_tin_misunderstanding_conflict_quest_tall.py
    python storyworlds/worlds/gpt-5.4/sociology_dumb_tin_misunderstanding_conflict_quest_tall.py --place canyon --helper blacksmith --stubborn 3
    python storyworlds/worlds/gpt-5.4/sociology_dumb_tin_misunderstanding_conflict_quest_tall.py --all
    python storyworlds/worlds/gpt-5.4/sociology_dumb_tin_misunderstanding_conflict_quest_tall.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sociology_dumb_tin_misunderstanding_conflict_quest_tall.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    skyline: str
    landmark: str
    booths: tuple[str, str]
    requires: set[str]
    stretch: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Helper:
    id: str
    title: str
    type: str
    phrase: str
    skills: set[str]
    patience: int
    entrance: str
    explain: str
    build: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class QuestStyle:
    id: str
    wrong_object: str
    quest_verb: str
    hauling: str
    failure: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "misunderstanding_active": False,
            "seeking_wrong": False,
            "line_built": False,
            "outcome": "",
        }

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "friend"}]

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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_wrong_quest(world: World) -> list[str]:
    if not world.facts.get("seeking_wrong"):
        return []
    hero = world.get("hero")
    friend = world.get("friend")
    lion = world.get("wrong")
    sig = ("wrong_quest", int(hero.meters["distance"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["distance"] += float(world.setting.stretch)
    lion.meters["clatter"] += 1.0
    hero.memes["pride"] += 1.0
    hero.memes["fatigue"] += 1.0
    friend.memes["frustration"] += 1.0
    friend.memes["care"] += 1.0
    return ["__wrong_quest__"]


def _r_conflict(world: World) -> list[str]:
    if not world.facts.get("misunderstanding_active"):
        return []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["pride"] < THRESHOLD or friend.memes["warning"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["conflict"] += 1.0
    friend.memes["conflict"] += 1.0
    return ["__conflict__"]


def _r_connection(world: World) -> list[str]:
    if not world.facts.get("line_built"):
        return []
    north = world.get("north")
    south = world.get("south")
    sig = ("connection",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    north.meters["signal"] += 1.0
    south.meters["signal"] += 1.0
    world.get("hero").memes["relief"] += 1.0
    world.get("friend").memes["relief"] += 1.0
    world.get("hero").memes["cooperation"] += 1.0
    world.get("friend").memes["cooperation"] += 1.0
    return ["__connection__"]


CAUSAL_RULES = [
    Rule(name="wrong_quest", tag="physical", apply=_r_wrong_quest),
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="connection", tag="social", apply=_r_connection),
]


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


def helper_can_fix(setting: Setting, helper: Helper) -> bool:
    return setting.requires.issubset(helper.skills)


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for place_id, setting in SETTINGS.items():
        for helper_id, helper in HELPERS.items():
            if helper_can_fix(setting, helper):
                out.append((place_id, helper_id))
    return out


def outcome_of(params: "StoryParams") -> str:
    helper = HELPERS[params.helper]
    return "early" if params.stubborn <= helper.patience else "late"


def predict_need(world: World) -> dict:
    sim = world.copy()
    sim.facts["line_built"] = True
    propagate(sim, narrate=False)
    north = sim.get("north")
    south = sim.get("south")
    return {
        "works": north.meters["signal"] >= THRESHOLD and south.meters["signal"] >= THRESHOLD,
        "distance": sim.get("hero").meters["distance"],
    }


def opening(world: World, hero: Entity, friend: Entity, teacher: Entity) -> None:
    a_booth, b_booth = world.setting.booths
    world.say(
        f"In {world.setting.place}, where {world.setting.skyline}, {hero.id} and {friend.id} could hear "
        f"the wind bragging to the fence posts. School was setting up two fair booths, {a_booth} and {b_booth}, "
        f"so wide apart that a sneeze from one could arrive at the other next Tuesday."
    )
    world.say(
        f"{teacher.id}, the teacher, called it the sociology booth, because the lesson was about how neighbors "
        f"listen, share, and pull together."
    )


def assign_task(world: World, hero: Entity, teacher: Entity) -> None:
    world.say(
        f'"{hero.id}," said {teacher.id}, "please bring me two tin cups and a line for the sociology booth. '
        f'We need people at both ends of the fair to hear one another over this windy day."'
    )


def mishear(world: World, hero: Entity, friend: Entity, quest: QuestStyle) -> None:
    world.facts["misunderstanding_active"] = True
    hero.memes["pride"] = 1.0
    friend.memes["warning"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f'''But the wind gave the words a tumble. {hero.id} blinked and heard not "two tin cups and a line" "'''
        f'but "two tin cubs and a lion."'
    )
    world.say(
        f'"A lion!" {hero.id} cried. "For sociology!"'
    )
    world.say(
        f'{friend.id} stared. "I think {teacher.id} said a line, not a lion."'
    )


def argue(world: World, hero: Entity, friend: Entity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'"A line is too small for a day this big," said {hero.id}. "{friend.id}, you just wait. '
            f'I will find the grandest tin thing in three counties and seven gusts."'
        )
        world.say(
            f'{friend.id} planted both feet. "And I think this is a dumb mix-up," {friend.pronoun()} said, '
            f'"but I am coming so you do not get carried off by your own idea."'
        )


def set_out(world: World, hero: Entity, friend: Entity, quest: QuestStyle) -> None:
    world.facts["seeking_wrong"] = True
    propagate(world, narrate=False)
    wrong = world.get("wrong")
    world.say(
        f"So off they went toward {world.setting.landmark}, where old scrap tin flashed in the sun. "
        f"{hero.id} {quest.quest_verb} for {wrong.phrase}, and the road stretched under them like a rolled-out gray ribbon."
    )
    dist = int(world.get("hero").meters["distance"])
    world.say(
        f"By the time they reached the ridge, they had walked {dist} giant-gulp steps, which in that country was nearly "
        f"half a forever."
    )


def build_wrong(world: World, hero: Entity, friend: Entity, helper_ent: Entity, quest: QuestStyle) -> None:
    wrong = world.get("wrong")
    world.say(
        f"They found a heap of bent tin sheets big enough to shingle a barn, and {hero.id} bent and banged them into "
        f"{wrong.phrase}. {quest.hauling}"
    )
    world.say(
        f"The creature gleamed so hard that the crows mistook it for a new sunrise. Still, {friend.id} kept peeking back "
        f"toward the fair and worrying that the real problem was waiting."
    )


def early_turn(world: World, hero: Entity, friend: Entity, helper_ent: Entity) -> None:
    pred = predict_need(world)
    world.say(helper_ent.attrs["entrance"])
    world.say(
        f'{helper_ent.id} listened once and laughed a warm laugh. "{hero.id}, no fair needs a lion to teach sociology," '
        f'{helper_ent.pronoun()} said. "It needs a way for one person to talk and another person to answer."'
    )
    world.say(
        f"{helper_ent.attrs['explain']} {hero.id} looked at the cups in {helper_ent.pronoun('possessive')} apron pocket, "
        f"then at the empty space between the booths, and the misunderstanding finally untied itself."
    )
    world.facts["misunderstanding_active"] = False
    world.facts["seeking_wrong"] = False
    hero.memes["pride"] = 0.0
    hero.memes["understanding"] += 1.0
    friend.memes["trust"] += 1.0


def late_turn(world: World, hero: Entity, friend: Entity, helper_ent: Entity, quest: QuestStyle) -> None:
    wrong = world.get("wrong")
    world.say(
        f"Back at the fair they hauled {wrong.phrase} in behind them. It clanged so loudly that pies shook on their plates."
    )
    world.say(
        f"Then {teacher_name(world)} said, 'My stars, I asked for two tin cups and a line.' {helper_ent.id} tipped "
        f"{helper_ent.pronoun('possessive')} hat and added, {helper_ent.attrs['explain'].lower()}"
    )
    world.say(
        f'{hero.id} felt the red climb into {hero.pronoun("possessive")} cheeks. It had been a mighty quest and a mighty mistake, '
        f'and the silliest part was how small the real fix had been all along.'
    )
    world.facts["misunderstanding_active"] = False
    world.facts["seeking_wrong"] = False
    hero.memes["pride"] = 0.0
    hero.memes["understanding"] += 1.0
    friend.memes["trust"] += 1.0
    wrong.meters["useless"] += 1.0
    world.say(quest.failure)


def build_line(world: World, hero: Entity, friend: Entity, helper_ent: Entity) -> None:
    world.facts["line_built"] = True
    propagate(world, narrate=False)
    a_booth, b_booth = world.setting.booths
    world.say(
        f"Then everybody worked at once. {helper_ent.attrs['build']} {hero.id} held one cup, {friend.id} held the other, "
        f"and the line ran from {a_booth} to {b_booth} as straight as a promise."
    )
    world.say(
        f'{hero.id} whispered into the first cup, "Can you hear me?" and {friend.id} grinned from far away. '
        f'"Clear as a dinner bell," {friend.pronoun()} answered.'
    )


def ending(world: World, hero: Entity, friend: Entity) -> None:
    world.facts["outcome"] = world.facts.get("outcome") or "early"
    world.say(
        f"After that, children and grown-ups took turns talking through the tin line about chores, cakes, missing mittens, "
        f"and who could lend a ladder. That was a better lesson in sociology than any shiny beast could have given."
    )
    if world.facts["outcome"] == "early":
        world.say(
            f"As the sun leaned west, {hero.id} and {friend.id} sat by the cups and laughed at the mix-up. "
            f"Their big quest had shrunk into a small wise fix, and the fair sounded friendlier for it."
        )
    else:
        world.say(
            f"As the sun leaned west, the great tin lion stood by the gate to hold down loose papers, while the real line sang with voices. "
            f"{hero.id} patted the lion's nose and laughed. Even a wrong idea could do a little honest work once the quarrel was over."
        )


def teacher_name(world: World) -> str:
    return world.get("teacher").id
@dataclass
class StoryParams:
    place: str
    helper: str
    quest: str = "lion"
    stubborn: int = 2
    hero_name: str = "Milo"
    hero_gender: str = "boy"
    friend_name: str = "Ada"
    friend_gender: str = "girl"
    teacher_name: str = "Miss Maple"
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


CURATED = [
    StoryParams(
        place="prairie",
        helper="kitemaker",
        quest="lion",
        stubborn=1,
        hero_name="Milo",
        hero_gender="boy",
        friend_name="Ada",
        friend_gender="girl",
        teacher_name="Miss Maple",
    ),
    StoryParams(
        place="canyon",
        helper="blacksmith",
        quest="lion",
        stubborn=3,
        hero_name="Jasper",
        hero_gender="boy",
        friend_name="June",
        friend_gender="girl",
        teacher_name="Mrs. Lark",
    ),
    StoryParams(
        place="riverside",
        helper="ferryman",
        quest="lion",
        stubborn=2,
        hero_name="Ruby",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        teacher_name="Miss Thistle",
    ),
    StoryParams(
        place="prairie",
        helper="tinker",
        quest="lion",
        stubborn=3,
        hero_name="Clara",
        hero_gender="girl",
        friend_name="Ned",
        friend_gender="boy",
        teacher_name="Mrs. Clover",
    ),
]


def explain_rejection(place: str, helper: str) -> str:
    setting = SETTINGS[place]
    h = HELPERS[helper]
    need = ", ".join(sorted(setting.requires))
    have = ", ".join(sorted(h.skills))
    return (
        f"(No story: {h.title} cannot honestly solve the fair's problem at {setting.place}. "
        f"The place needs skills for {need}, but this helper only has {have}.)"
    )


KNOWLEDGE = {
    "sociology": [
        (
            "What is sociology?",
            "Sociology is the study of how people live together in groups, help one another, and make rules and habits in a town or school."
        )
    ],
    "tin": [
        (
            "What is tin?",
            "Tin is a light metal. People can shape it into cups, signs, and other useful things."
        )
    ],
    "tin_line": [
        (
            "How can two tin cups and a line carry a voice?",
            "When someone speaks into one cup, the cup vibrates. Those little shakes travel along the tight line and make the other cup vibrate too, so the other person can hear."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when one person hears or understands something the wrong way. Talking calmly can help everyone fix it."
        )
    ],
    "blacksmith": [
        (
            "What does a blacksmith do?",
            "A blacksmith heats and shapes metal into useful things. That makes a blacksmith good at fixing sturdy tin or wire tools."
        )
    ],
    "tinker": [
        (
            "What does a tinker do?",
            "A tinker mends small metal things and carries tools from place to place. A tinker is handy when something tin needs to be fixed or built."
        )
    ],
    "ferryman": [
        (
            "Why is a ferryman good with knots?",
            "A ferryman works with ropes and boats all the time. Good knots keep things steady and safe."
        )
    ],
    "kitemaker": [
        (
            "Why does a kite-maker know about string?",
            "A kite-maker uses string to hold a kite steady in the wind. That skill helps when a line must stay tight and straight."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "sociology",
    "misunderstanding",
    "tin",
    "tin_line",
    "blacksmith",
    "tinker",
    "ferryman",
    "kitemaker",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper_cfg = f["helper_cfg"]
    setting = f["place"]
    return [
        f'Write a Tall Tale for a young child that includes the words "sociology", "dumb", and "tin".',
        f"Tell a story where {hero.id} mishears a school request at {setting.place}, starts a tin quest, quarrels with {friend.id}, and gets help from {helper_cfg.title}.",
        "Write a gentle misunderstanding story where a conflict turns into cooperation after children build something useful together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper_ent = f["helper"]
    setting = f["place"]
    quest = f["quest"]
    out = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two children at {setting.place}, and {helper_ent.id}, who helped them fix the problem."
        ),
        (
            "What was the misunderstanding?",
            f"{hero.id} heard 'two tin cups and a line' as 'two tin cubs and a lion.' Because the wind muddled the words, {hero.pronoun()} started chasing the wrong idea."
        ),
        (
            "Why were they talking about sociology?",
            "The school fair had a sociology booth about how neighbors listen and help one another. The children needed a way for people at two booths to speak across the windy fairground."
        ),
        (
            f"Why did {friend.id} argue with {hero.id}?",
            f"{friend.id} thought the teacher had asked for a line, not a lion. The quarrel came from wanting to solve the same problem in two very different ways."
        ),
    ]
    if out == "early":
        qa.append(
            (
                f"How was the conflict solved?",
                f"{helper_ent.id} stopped them before the wrong tin lion did any real harm and explained what the teacher truly meant. After that, the children dropped the argument and worked together on the real fix."
            )
        )
    else:
        qa.append(
            (
                f"What happened before {hero.id} understood the mistake?",
                f"{hero.id} and {friend.id} hauled the great {quest.wrong_object} all the way back to the fair. When it failed to help anyone hear, the mistake became clear at last."
            )
        )
    qa.append(
        (
            "How did they finally solve the fair's problem?",
            f"They stretched a line between two tin cups and ran it from one booth to the other. That worked because the cups and line carried voices across the windy space."
        )
    )
    qa.append(
        (
            "How did the story end?",
            "The fair ended with people talking through the cups, laughing at the mix-up, and helping one another more easily. The last image proves what changed: the noisy quarrel turned into useful connection."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sociology", "misunderstanding", "tin", "tin_line"}
    tags |= set(world.facts["helper_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
need_skill(P, S) :- place(P), requires(P, S).
has_skill(H, S) :- helper(H), skill(H, S).
valid(P, H) :- place(P), helper(H), not missing_skill(P, H).
missing_skill(P, H) :- need_skill(P, S), not has_skill(H, S).

outcome(early) :- stubborn(S), helper_patience(P), S <= P.
outcome(late)  :- stubborn(S), helper_patience(P), S > P.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        for need in sorted(setting.requires):
            lines.append(asp.fact("requires", place_id, need))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("patience", helper_id, helper.patience))
        for skill in sorted(helper.skills):
            lines.append(asp.fact("skill", helper_id, skill))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("stubborn", params.stubborn),
            asp.fact("helper_patience", HELPERS[params.helper].patience),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("smoke test produced incomplete sample")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke-test generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a windy misunderstanding about a tin line at a sociology fair."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--quest", choices=QUESTS, default=None)
    ap.add_argument("--stubborn", type=int, choices=[1, 2, 3], help="how long the hero clings to the wrong idea")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (place, helper) pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.helper and not helper_can_fix(SETTINGS[args.place], HELPERS[args.helper]):
        raise StoryError(explain_rejection(args.place, args.helper))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.helper is None or c[1] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, helper = rng.choice(sorted(combos))
    quest = args.quest or "lion"
    stubborn = args.stubborn if args.stubborn is not None else rng.choice([1, 2, 3])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    teacher_name_value = args.teacher_name or rng.choice(TEACHER_NAMES)

    return StoryParams(
        place=place,
        helper=helper,
        quest=quest,
        stubborn=stubborn,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        teacher_name=teacher_name_value,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest style: {params.quest})")
    if params.stubborn not in {1, 2, 3}:
        raise StoryError("(Stubbornness must be 1, 2, or 3.)")
    if not helper_can_fix(SETTINGS[params.place], HELPERS[params.helper]):
        raise StoryError(explain_rejection(params.place, params.helper))

    outcome = outcome_of(params)
    world = tell(
        setting=SETTINGS[params.place],
        helper=HELPERS[params.helper],
        quest=QUESTS[params.quest],
        outcome=outcome,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        teacher_name_value=params.teacher_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, helper) pairs:\n")
        for place, helper in combos:
            print(f"  {place:10} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.place} with {p.helper} (outcome: {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    setting: Setting,
    helper: Helper,
    quest: QuestStyle,
    outcome: str,
    hero_name: str = "Milo",
    hero_gender: str = "boy",
    friend_name: str = "Ada",
    friend_gender: str = "girl",
    teacher_name_value: str = "Miss Maple",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero"))
    hero.id = hero_name
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, phrase=friend_name, role="friend"))
    friend.id = friend_name
    teacher = world.add(Entity(id="teacher", kind="character", type="woman", label=teacher_name_value, phrase=teacher_name_value, role="teacher"))
    teacher.id = teacher_name_value
    helper_ent = world.add(Entity(
        id=helper.title,
        kind="character",
        type=helper.type,
        label=helper.title,
        phrase=helper.phrase,
        role="helper",
        attrs={"entrance": helper.entrance, "explain": helper.explain, "build": helper.build},
        tags=set(helper.tags),
    ))
    north = world.add(Entity(id="north", type="booth", label=setting.booths[0], phrase=setting.booths[0]))
    south = world.add(Entity(id="south", type="booth", label=setting.booths[1], phrase=setting.booths[1]))
    wrong = world.add(Entity(
        id="wrong",
        type="thing",
        label=quest.wrong_object,
        phrase=f"a {quest.wrong_object} hammered from old tin",
        tags=set(quest.tags),
    ))

    for ent in (hero, friend, teacher, helper_ent, north, south, wrong):
        ent.meters["signal"] += 0.0
        ent.meters["distance"] += 0.0
        ent.meters["clatter"] += 0.0
        ent.meters["useless"] += 0.0
        ent.memes["pride"] += 0.0
        ent.memes["warning"] += 0.0
        ent.memes["conflict"] += 0.0
        ent.memes["frustration"] += 0.0
        ent.memes["care"] += 0.0
        ent.memes["trust"] += 0.0
        ent.memes["understanding"] += 0.0
        ent.memes["cooperation"] += 0.0
        ent.memes["relief"] += 0.0
        ent.memes["fatigue"] += 0.0

    world.facts.update(
        place=setting,
        helper=helper_ent,
        helper_cfg=helper,
        quest=quest,
        hero=hero,
        friend=friend,
        teacher=teacher,
        wrong=wrong,
        request_text="two tin cups and a line",
        misheard_text="two tin cubs and a lion",
        actual_purpose="so the two fair booths could hear each other over the wind",
        outcome=outcome,
    )

    opening(world, hero, friend, teacher)
    assign_task(world, hero, teacher)

    world.para()
    mishear(world, hero, friend, quest)
    argue(world, hero, friend)
    set_out(world, hero, friend, quest)

    world.para()
    build_wrong(world, hero, friend, helper_ent, quest)

    if outcome == "early":
        early_turn(world, hero, friend, helper_ent)
    else:
        late_turn(world, hero, friend, helper_ent, quest)

    world.para()
    build_line(world, hero, friend, helper_ent)
    ending(world, hero, friend)
    return world


SETTINGS = {
    "prairie": Setting(
        id="prairie",
        place="the Longgrass Prairie School Fair",
        skyline="windmills bowed and the grass waved in long green rivers",
        landmark="Whistle Ridge",
        booths=("the north booth", "the south booth"),
        requires={"cups", "string"},
        stretch=3,
        tags={"wind", "fair"},
    ),
    "canyon": Setting(
        id="canyon",
        place="the Redwall Canyon School Fair",
        skyline="the cliffs tossed every word back twice before letting it land",
        landmark="Echo Gap",
        booths=("the rim booth", "the creek booth"),
        requires={"cups", "wire"},
        stretch=4,
        tags={"echo", "fair"},
    ),
    "riverside": Setting(
        id="riverside",
        place="the Willow River School Fair",
        skyline="the dock ropes creaked and the willow leaves whispered over the water",
        landmark="Tinwater Bend",
        booths=("the dock booth", "the meadow booth"),
        requires={"cups", "string", "knots"},
        stretch=3,
        tags={"river", "fair"},
    ),
}

HELPERS = {
    "blacksmith": Helper(
        id="blacksmith",
        title="Mr. Brindle",
        type="man",
        phrase="the blacksmith with soot on his sleeves",
        skills={"cups", "wire"},
        patience=1,
        entrance="Just then Mr. Brindle the blacksmith came clomping up the track, carrying two new tin cups that shone like moons.",
        explain="A line and two cups make a little talking road.",
        build="Mr. Brindle punched neat holes in the cups, fixed them with a humming wire, and pulled the wire tight with iron-strong hands.",
        tags={"blacksmith", "tin_line"},
    ),
    "tinker": Helper(
        id="tinker",
        title="Aunt Wren",
        type="woman",
        phrase="the town tinker with pockets full of nails and string",
        skills={"cups", "wire", "string"},
        patience=3,
        entrance="Along came Aunt Wren the tinker, with string on one shoulder and tin cups knocking at her knee.",
        explain="A line and two cups make a little talking road.",
        build="Aunt Wren tied the string, tested its pull with one finger, and set the cups singing from end to end.",
        tags={"tinker", "tin_line"},
    ),
    "ferryman": Helper(
        id="ferryman",
        title="Captain Reed",
        type="man",
        phrase="the ferryman who could tie a knot faster than a fish could wink",
        skills={"cups", "string", "knots"},
        patience=2,
        entrance="Captain Reed the ferryman hailed them from the path, swinging a coil of cord and two dented tin cups.",
        explain="A line and two cups make a little talking road.",
        build="Captain Reed tied sailor knots at both ends, stretched the cord dry above the grass, and set the cups ready for voices.",
        tags={"ferryman", "tin_line"},
    ),
    "kitemaker": Helper(
        id="kitemaker",
        title="Mrs. Gale",
        type="woman",
        phrase="the kite-maker whose strings never once lost an argument with the wind",
        skills={"cups", "string"},
        patience=2,
        entrance="Mrs. Gale the kite-maker came skipping over the hill with a reel of string and two bright tin cups tucked under one arm.",
        explain="A line and two cups make a little talking road.",
        build="Mrs. Gale measured the pull of the wind, chose the steadiest string in the county, and drew it tight as fiddle music.",
        tags={"kitemaker", "tin_line"},
    ),
}

QUESTS = {
    "lion": QuestStyle(
        id="lion",
        wrong_object="tin lion",
        quest_verb="went scouting",
        hauling="It took both children, a wagon, and one stubborn goat to drag the thing downhill.",
        failure="The giant lion looked noble, but it could not carry a whisper from one booth to the other.",
        tags={"misunderstanding", "lion"},
    ),
}

GIRL_NAMES = ["Ada", "Nora", "June", "Mabel", "Elsie", "Clara", "Tess", "Ruby"]
BOY_NAMES = ["Milo", "Eli", "Owen", "Jasper", "Finn", "Toby", "Cal", "Ned"]
TEACHER_NAMES = ["Miss Maple", "Miss Thistle", "Mrs. Lark", "Mrs. Clover"]

if __name__ == "__main__":
    main()
