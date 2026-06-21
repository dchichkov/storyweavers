#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/interview_surprise_moral_value_inner_monologue_pirate.py
===================================================================================

A standalone story world about a child in a pirate-themed harbor interview who
faces a temptation before the interview begins. The child can act honestly,
peek and confess, or hide the truth. The surprise is that the captain cares
most about honesty, and the world state drives which ending appears.

Run it
------
    python storyworlds/worlds/gpt-5.4/interview_surprise_moral_value_inner_monologue_pirate.py
    python storyworlds/worlds/gpt-5.4/interview_surprise_moral_value_inner_monologue_pirate.py --interview lookout --temptation answer_card
    python storyworlds/worlds/gpt-5.4/interview_surprise_moral_value_inner_monologue_pirate.py --action hide_and_use
    python storyworlds/worlds/gpt-5.4/interview_surprise_moral_value_inner_monologue_pirate.py --all
    python storyworlds/worlds/gpt-5.4/interview_surprise_moral_value_inner_monologue_pirate.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/interview_surprise_moral_value_inner_monologue_pirate.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/interview_surprise_moral_value_inner_monologue_pirate.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "captain_woman", "woman"}
        male = {"boy", "father", "captain_man", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)
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
class InterviewKind:
    id: str
    title: str
    station: str
    task: str
    question: str
    good_answer: str
    skill_line: str
    reward: str
    ending_image: str
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
class Temptation:
    id: str
    label: str
    phrase: str
    clue: str
    owner_mark: str
    cheat_line: str
    topic: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "peeked": False,
            "returned_sealed": False,
            "confessed": False,
            "hid": False,
            "used_sheet": False,
            "honest_before_interview": False,
            "surprise_revealed": False,
            "test_began_early": False,
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


def _r_guilt(world: World) -> list[str]:
    hero = world.get("hero")
    sheet = world.get("sheet")
    if hero.meters["peeked"] < THRESHOLD:
        return []
    sig = ("guilt", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["guilt"] += 1
    if sheet.meters["opened"] >= THRESHOLD:
        hero.memes["worry"] += 1
    return []


def _r_honest_trust(world: World) -> list[str]:
    hero = world.get("hero")
    captain = world.get("captain")
    if hero.meters["returned"] < THRESHOLD and hero.meters["confessed"] < THRESHOLD:
        return []
    sig = ("trust", hero.id, int(hero.meters["returned"]), int(hero.meters["confessed"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if hero.meters["returned"] >= THRESHOLD and hero.meters["peeked"] < THRESHOLD:
        captain.memes["trust"] += 2
        hero.memes["relief"] += 1
        world.facts["honest_before_interview"] = True
    elif hero.meters["confessed"] >= THRESHOLD:
        captain.memes["trust"] += 1
        hero.memes["relief"] += 1
    return []


def _r_hidden_consequence(world: World) -> list[str]:
    hero = world.get("hero")
    captain = world.get("captain")
    if hero.meters["hid"] < THRESHOLD:
        return []
    sig = ("hidden", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["guilt"] += 1
    captain.memes["trust"] -= 1
    return []


CAUSAL_RULES = [
    Rule(name="guilt", tag="emotion", apply=_r_guilt),
    Rule(name="honest_trust", tag="social", apply=_r_honest_trust),
    Rule(name="hidden_consequence", tag="social", apply=_r_hidden_consequence),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def matching_topic(interview: InterviewKind, temptation: Temptation) -> bool:
    return interview.id == temptation.topic


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for interview_id in sorted(setting.affords):
            interview = INTERVIEWS[interview_id]
            for temptation_id, temptation in TEMPTATIONS.items():
                if matching_topic(interview, temptation):
                    combos.append((setting_id, interview_id, temptation_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.action == "return_sealed":
        return "chosen"
    if params.action == "peek_then_confess":
        return "second_chance"
    return "not_chosen"


def explain_rejection(interview: InterviewKind, temptation: Temptation) -> str:
    return (
        f"(No story: {temptation.label} would not honestly help with the "
        f"{interview.title} interview. The temptation must match the interview task "
        f"or there is no real moral choice to make.)"
    )


def inner_monologue_for_action(action: str, temptation: Temptation) -> str:
    if action == "return_sealed":
        return (
            f'"That paper is not mine," thought the child. '
            f'"A true matey does not borrow a secret wind."'
        )
    if action == "peek_then_confess":
        return (
            f'"Just one little look," thought the child, fingers tingling. '
            f'"Oh dear. Now my chest feels heavier than an anchor."'
        )
    return (
        f'"If I tuck this away, maybe nobody will know," thought the child. '
        f'"But why does the secret already feel so loud?"'
    )


def introduce(world: World, hero: Entity, friend: Entity, captain: Entity,
              interview: InterviewKind) -> None:
    hero.memes["hope"] += 1
    friend.memes["support"] += 1
    world.say(
        f"Morning gulls wheeled over {world.setting.place}, where pennants snapped in the salt wind. "
        f"{hero.id} and {friend.id} hurried along the planks toward a pirate interview with "
        f"{captain.id}, who was choosing a new {interview.title} for the festival ship."
    )
    world.say(world.setting.detail)
    world.say(
        f"{hero.id} wanted the place badly. {interview.skill_line}"
    )


def approach_station(world: World, hero: Entity, friend: Entity,
                     interview: InterviewKind) -> None:
    world.say(
        f"At the foot of {interview.station}, a brass bell waited to ring the start. "
        f'"You will do fine," {friend.id} whispered. '
        f'{hero.id} nodded, though {hero.pronoun("possessive")} stomach gave a tiny flip.'
    )


def discover_temptation(world: World, hero: Entity, temptation: Temptation) -> None:
    sheet = world.get("sheet")
    sheet.attrs["sealed"] = True
    world.say(
        f"Then {hero.id} spotted {temptation.phrase} tucked beside a coil of rope. "
        f"{temptation.owner_mark} was written across the top, and below it lay "
        f"{temptation.clue}."
    )
    hero.memes["tempted"] += 1
    hero.memes["worry"] += 1
    world.say(inner_monologue_for_action(world.facts["planned_action"], temptation))


def friend_warning(world: World, hero: Entity, friend: Entity,
                   temptation: Temptation) -> None:
    world.say(
        f'{friend.id} leaned close. "Matey, that looks like {temptation.label}. '
        f"If it belongs to the captain, we should not use it before the interview."
    )
    hero.memes["pressure"] += 1


def do_return_sealed(world: World, hero: Entity, captain: Entity,
                     temptation: Temptation) -> None:
    sheet = world.get("sheet")
    hero.meters["returned"] += 1
    sheet.meters["returned_to_owner"] += 1
    world.facts["returned_sealed"] = True
    world.facts["test_began_early"] = True
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} picked up the packet carefully with two hands and carried it straight to {captain.id}. "
        f'"Captain, I found {temptation.label} before the interview," {hero.pronoun()} said. '
        f'"I did not open it."'
    )
    world.say(
        f"{captain.id}'s eyebrows rose, and {captain.pronoun()} took the packet without opening it."
    )


def do_peek_then_confess(world: World, hero: Entity, captain: Entity,
                         temptation: Temptation) -> None:
    sheet = world.get("sheet")
    hero.meters["peeked"] += 1
    hero.meters["confessed"] += 1
    sheet.meters["opened"] += 1
    sheet.attrs["sealed"] = False
    world.facts["peeked"] = True
    world.facts["confessed"] = True
    world.facts["used_sheet"] = False
    world.facts["test_began_early"] = True
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} unfolded the packet just enough to see {temptation.cheat_line}. "
        f"The words did not feel bright and helpful after all. They felt sticky."
    )
    world.say(
        f"{hero.id}'s ears grew warm. Before the bell could ring, "
        f"{hero.pronoun()} hurried to {captain.id} and blurted, "
        f'"Captain, I peeked at this and I should not have. I am sorry."'
    )


def do_hide_and_use(world: World, hero: Entity, temptation: Temptation) -> None:
    sheet = world.get("sheet")
    hero.meters["peeked"] += 1
    hero.meters["hid"] += 1
    sheet.meters["opened"] += 1
    sheet.attrs["sealed"] = False
    hero.attrs["remembered_line"] = temptation.cheat_line
    world.facts["peeked"] = True
    world.facts["hid"] = True
    world.facts["used_sheet"] = True
    world.facts["test_began_early"] = True
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} slipped the packet behind a barrel, stole a quick look at {temptation.cheat_line}, "
        f"and tried to stamp the words into memory."
    )
    world.say(
        f'When {friend.id if "friend" in world.entities else "the friend"} looked over, '
        f"{hero.id} only gave a tight little smile."
    )


def interview_scene(world: World, hero: Entity, captain: Entity,
                    interview: InterviewKind) -> None:
    remembered = hero.attrs.get("remembered_line", "")
    world.say(
        f"Soon the bell rang, and the interview began. {captain.id} asked, "
        f'"{interview.question}"'
    )
    if world.facts["used_sheet"] and remembered:
        world.say(
            f"{hero.id} answered quickly with the line {remembered!r}, hoping it sounded bold."
        )
    else:
        world.say(
            f"{hero.id} took a breath and answered as best {hero.pronoun()} could."
        )


def surprise_reveal(world: World, hero: Entity, captain: Entity,
                    interview: InterviewKind, temptation: Temptation) -> None:
    world.facts["surprise_revealed"] = True
    world.say(
        f"{captain.id} rested one hand on the rail and gave a slow pirate smile. "
        f'"Now for the truest part of the interview," {captain.pronoun()} said.'
    )
    world.say(
        f'"That {temptation.label} was mine. I left it where a sharp eye would find it, '
        f"because a ship needs more than quick answers. It needs honest hearts."
    )


def resolution_chosen(world: World, hero: Entity, friend: Entity, captain: Entity,
                      interview: InterviewKind) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.facts["outcome"] = "chosen"
    world.say(
        f'"You returned it sealed before the interview even started," {captain.id} said. '
        f'"That tells me I can trust you as {interview.title}."'
    )
    world.say(
        f"{friend.id} gave a happy hop, and {captain.id} pinned {interview.reward} onto "
        f"{hero.id}'s shirt."
    )
    world.say(interview.ending_image)


def resolution_second_chance(world: World, hero: Entity, friend: Entity, captain: Entity,
                             interview: InterviewKind) -> None:
    hero.memes["hope"] += 1
    hero.memes["relief"] += 1
    world.facts["outcome"] = "second_chance"
    world.say(
        f'"You made a wrong choice," {captain.id} said, "but you came straight and told the truth. '
        f'That matters too."'
    )
    world.say(
        f"{captain.pronoun().capitalize()} did not choose {hero.id} for {interview.title} that day, "
        f"but {captain.pronoun()} offered a surprise instead: a practice turn beside the crew so "
        f"{hero.pronoun()} could earn the place honestly next time."
    )
    world.say(
        f"{friend.id} squeezed {hero.id}'s hand. The sting in {hero.pronoun('possessive')} chest eased, "
        f"and the harbor no longer looked grey."
    )
    world.say(
        f"By sunset, {hero.id} was helping coil ropes beside the deck, learning slowly and fairly."
    )


def resolution_not_chosen(world: World, hero: Entity, friend: Entity, captain: Entity,
                          interview: InterviewKind) -> None:
    hero.memes["sadness"] += 1
    hero.memes["lesson"] += 1
    world.facts["outcome"] = "not_chosen"
    world.say(
        f'{captain.id} looked at {hero.id} kindly, not harshly. "You tried to carry a secret into '
        f'the interview," {captain.pronoun()} said. "A matey who hides the truth cannot keep watch for all."'
    )
    world.say(
        f"{captain.pronoun().capitalize()} chose another child for {interview.title}, and for one long moment "
        f"{hero.id} could only hear gulls and rigging in the wind."
    )
    world.say(
        f"Then {hero.id} went to fetch the hidden packet and handed it over at last. "
        f"{friend.id} stayed beside {hero.pronoun('object')} while {hero.pronoun()} whispered an apology."
    )
    world.say(
        f"On the walk home, {hero.id} knew the next brave thing would not be winning quickly. "
        f"It would be earning trust the honest way."
    )
@dataclass
class StoryParams:
    setting: str
    interview: str
    temptation: str
    action: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    captain_name: str
    captain_gender: str
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


KNOWLEDGE = {
    "interview": [
        (
            "What is an interview?",
            "An interview is a time when someone asks questions to learn what you know and how you act. It is not only about clever answers, but also about being truthful and calm."
        )
    ],
    "honesty": [
        (
            "Why is honesty important?",
            "Honesty helps other people trust you. Even when the truth feels hard to say, telling it gives people something solid to stand on."
        )
    ],
    "map": [
        (
            "What does a map reader do?",
            "A map reader studies where things are and helps others choose the right path. On a ship, that can help the crew avoid shallow places and reach the right spot."
        )
    ],
    "bell": [
        (
            "Why do ships use bells?",
            "Bells make clear sounds that can be heard quickly. A bell can warn people, mark time, or tell a crew to pay attention right away."
        )
    ],
    "lookout": [
        (
            "What does a lookout do on a ship?",
            "A lookout watches carefully for danger and for the safest way ahead. Good lookouts use sharp eyes and tell the truth fast when they notice something important."
        )
    ],
    "answer_card": [
        (
            "Why is using somebody else's answer card unfair?",
            "It is unfair because the answers are supposed to show what you know yourself. Borrowing secret help can make it look as if you earned something you did not."
        )
    ],
    "pirate": [
        (
            "What makes a pirate story feel adventurous?",
            "Pirate stories often have ships, wind, ropes, bells, maps, and brave choices near the sea. They feel adventurous because the world is full of motion and daring, but the best ones still care about right and wrong."
        )
    ],
}
KNOWLEDGE_ORDER = ["interview", "honesty", "lookout", "map", "bell", "answer_card", "pirate"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    interview = world.facts["interview"]
    temptation = world.facts["temptation"]
    action = world.facts["action"]
    if action == "return_sealed":
        return [
            'Write a pirate-tale story for a 3-to-5-year-old that includes the word "interview" and ends with honesty being rewarded.',
            f"Tell a gentle harbor story where {hero.id} finds {temptation.label} before a pirate interview and chooses to return it unopened.",
            "Write a story with a surprise ending where the captain cares more about honesty than about perfect answers."
        ]
    if action == "peek_then_confess":
        return [
            'Write a pirate-tale story for a 3-to-5-year-old that includes the word "interview" and shows a child making a mistake, then telling the truth.',
            f"Tell a harbor story where {hero.id} peeks at {temptation.label} before the {interview.title} interview but confesses before the test really begins.",
            "Write a story with inner monologue, a moral choice, and a kind surprise from the captain."
        ]
    return [
        'Write a pirate-tale story for a 3-to-5-year-old that includes the word "interview" and teaches that hiding the truth has consequences.',
        f"Tell a harbor story where {hero.id} hides {temptation.label} before a pirate interview and later learns the captain was testing honesty.",
        "Write a story with inner monologue, a moral value, and a gentle but sad ending that points toward doing better next time."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    captain = world.facts["captain"]
    interview = world.facts["interview"]
    temptation = world.facts["temptation"]
    action = world.facts["action"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who hurried to a pirate interview at {world.setting.place}, with {friend.id} nearby and {captain.id} asking the questions."
        ),
        (
            "What job did the child hope to get?",
            f"{hero.id} hoped to become {interview.title}. The child wanted to do that special ship job very much, which is why the temptation felt strong."
        ),
        (
            "What did the child find before the interview?",
            f"{hero.id} found {temptation.label} with captain's notes on it. Because it matched the interview topic, it looked like secret help."
        ),
    ]

    if action == "return_sealed":
        qa.append(
            (
                f"Why did {hero.id} give the packet to {captain.id} right away?",
                f"{hero.id} believed the packet was not {hero.pronoun('possessive')} to use, so {hero.pronoun()} returned it unopened. That choice showed honesty before the interview even began."
            )
        )
    elif action == "peek_then_confess":
        qa.append(
            (
                f"Why did {hero.id} confess after peeking?",
                f"{hero.id} peeked because the interview mattered a lot, but the secret answer made {hero.pronoun('possessive')} chest feel heavy instead of proud. The guilty feeling pushed {hero.pronoun('object')} to tell the truth before the test went any farther."
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.id} feel bad during the interview?",
                f"{hero.id} had hidden the packet and tried to use the secret line, so even the clever-sounding answer did not feel steady. The child was worried because hiding the truth had already made the moment feel wrong."
            )
        )

    qa.append(
        (
            "What was the surprise?",
            f"The surprise was that the packet belonged to the captain and had been left there on purpose. The interview was really testing honesty as well as skill."
        )
    )

    if outcome == "chosen":
        qa.append(
            (
                "How did the story end?",
                f"{captain.id} chose {hero.id} for the job and gave a small reward. The ending image shows the child standing taller because honesty led to trust."
            )
        )
    elif outcome == "second_chance":
        qa.append(
            (
                "How did the story end?",
                f"{hero.id} was not chosen that day, but {captain.id} offered a practice place with the crew. The kind surprise showed that telling the truth after a mistake can open a better path forward."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"{hero.id} was not chosen for the job and had to hand over the hidden packet at last. Even so, the ending points toward change, because the child decides to earn trust honestly next time."
            )
        )

    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pirate", "interview", "honesty"}
    interview = world.facts["interview"]
    temptation = world.facts["temptation"]
    tags |= set(interview.tags)
    tags |= set(temptation.tags)
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v or v is False}
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  world facts: {world.facts}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="harbor",
        interview="lookout",
        temptation="answer_card",
        action="return_sealed",
        hero_name="Nell",
        hero_gender="girl",
        friend_name="Toby",
        friend_gender="boy",
        captain_name="Captain Mara",
        captain_gender="captain_woman",
    ),
    StoryParams(
        setting="museum_ship",
        interview="map_reader",
        temptation="marked_chart",
        action="peek_then_confess",
        hero_name="Finn",
        hero_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        captain_name="Captain Reed",
        captain_gender="captain_man",
    ),
    StoryParams(
        setting="lighthouse_pier",
        interview="bell_keeper",
        temptation="signal_sheet",
        action="hide_and_use",
        hero_name="Mira",
        hero_gender="girl",
        friend_name="Kit",
        friend_gender="boy",
        captain_name="Captain Inez",
        captain_gender="captain_woman",
    ),
    StoryParams(
        setting="harbor",
        interview="bell_keeper",
        temptation="signal_sheet",
        action="return_sealed",
        hero_name="Sam",
        hero_gender="boy",
        friend_name="Poppy",
        friend_gender="girl",
        captain_name="Captain Sol",
        captain_gender="captain_man",
    ),
]


ASP_RULES = r"""
valid(S, I, T) :- setting(S), affords(S, I), interview(I), temptation(T), topic(T, I).

outcome(chosen) :- action(return_sealed).
outcome(second_chance) :- action(peek_then_confess).
outcome(not_chosen) :- action(hide_and_use).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for interview_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, interview_id))
    for interview_id in INTERVIEWS:
        lines.append(asp.fact("interview", interview_id))
    for temptation_id, temptation in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", temptation_id))
        lines.append(asp.fact("topic", temptation_id, temptation.topic))
    for action_id in ACTIONS:
        lines.append(asp.fact("action_name", action_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(action: str) -> str:
    import asp

    model = asp.one_model(
        asp_program(
            extra=asp.fact("action", action),
            show="#show outcome/1.",
        )
    )
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    bad = 0
    for action_id in ACTIONS:
        if asp_outcome(action_id) != ({aid: outcome_of(StoryParams(
            setting="harbor",
            interview="lookout",
            temptation="answer_card",
            action=aid,
            hero_name="Nell",
            hero_gender="girl",
            friend_name="Toby",
            friend_gender="boy",
            captain_name="Captain Mara",
            captain_gender="captain_woman",
        )) for aid in ACTIONS}[action_id]):
            bad += 1
    if bad == 0:
        print("OK: ASP outcome model matches outcome_of() for all actions.")
    else:
        rc = 1
        print(f"MISMATCH in outcome model ({bad} actions).")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate interview, a tempting shortcut, and a surprise about honesty."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--interview", choices=INTERVIEWS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + rules)")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.interview and args.temptation:
        interview = INTERVIEWS[args.interview]
        temptation = TEMPTATIONS[args.temptation]
        if not matching_topic(interview, temptation):
            raise StoryError(explain_rejection(interview, temptation))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.interview is None or combo[1] == args.interview)
        and (args.temptation is None or combo[2] == args.temptation)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, interview_id, temptation_id = rng.choice(sorted(combos))
    action = args.action or rng.choice(sorted(ACTIONS))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl" if rng.random() < 0.7 else hero_gender
    hero_name = pick_name(rng, hero_gender)
    friend_name = pick_name(rng, friend_gender, avoid=hero_name)
    captain_name, captain_gender = rng.choice(CAPTAINS)
    return StoryParams(
        setting=setting_id,
        interview=interview_id,
        temptation=temptation_id,
        action=action,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        captain_name=captain_name,
        captain_gender=captain_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.interview not in INTERVIEWS:
        raise StoryError(f"(Unknown interview: {params.interview})")
    if params.temptation not in TEMPTATIONS:
        raise StoryError(f"(Unknown temptation: {params.temptation})")
    if params.action not in ACTIONS:
        raise StoryError(f"(Unknown action: {params.action})")

    setting = SETTINGS[params.setting]
    interview = INTERVIEWS[params.interview]
    temptation = TEMPTATIONS[params.temptation]
    if not matching_topic(interview, temptation):
        raise StoryError(explain_rejection(interview, temptation))
    if interview.id not in setting.affords:
        raise StoryError(
            f"(No story: {setting.place} does not host the {interview.title} interview.)"
        )

    world = tell(
        setting=setting,
        interview=interview,
        temptation=temptation,
        action=params.action,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        friend_name=params.friend_name,
        friend_type=params.friend_gender,
        captain_name=params.captain_name,
        captain_type=params.captain_gender,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, interview, temptation) combos:\n")
        for setting_id, interview_id, temptation_id in combos:
            print(f"  {setting_id:15} {interview_id:12} {temptation_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name}: {p.interview} at {p.setting} "
                f"({p.action}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(setting: Setting, interview: InterviewKind, temptation: Temptation,
         action: str, hero_name: str = "Nell", hero_type: str = "girl",
         friend_name: str = "Toby", friend_type: str = "boy",
         captain_name: str = "Captain Mara", captain_type: str = "captain_woman") -> World:
    world = World(setting)
    world.facts["planned_action"] = action

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=["eager", "small"],
        tags={"child"},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_type,
        label=friend_name,
        role="friend",
        traits=["steady"],
        tags={"friend"},
    ))
    captain = world.add(Entity(
        id=captain_name,
        kind="character",
        type=captain_type,
        label=captain_name,
        role="captain",
        traits=["calm", "watchful"],
        tags={"captain"},
    ))
    world.add(Entity(
        id="sheet",
        kind="thing",
        type="paper",
        label=temptation.label,
        role="temptation",
        attrs={"sealed": True, "owner": captain.id},
        tags=set(temptation.tags),
    ))

    introduce(world, hero, friend, captain, interview)
    approach_station(world, hero, friend, interview)

    world.para()
    discover_temptation(world, hero, temptation)
    friend_warning(world, hero, friend, temptation)

    world.para()
    if action == "return_sealed":
        do_return_sealed(world, hero, captain, temptation)
    elif action == "peek_then_confess":
        do_peek_then_confess(world, hero, captain, temptation)
    elif action == "hide_and_use":
        do_hide_and_use(world, hero, temptation)
    else:
        raise StoryError(f"(Unknown action: {action})")

    interview_scene(world, hero, captain, interview)

    world.para()
    surprise_reveal(world, hero, captain, interview, temptation)

    if action == "return_sealed":
        resolution_chosen(world, hero, friend, captain, interview)
    elif action == "peek_then_confess":
        resolution_second_chance(world, hero, friend, captain, interview)
    else:
        resolution_not_chosen(world, hero, friend, captain, interview)

    world.facts.update(
        hero=hero,
        friend=friend,
        captain=captain,
        setting=setting,
        interview=interview,
        temptation=temptation,
        action=action,
    )
    return world


SETTINGS = {
    "harbor": Setting(
        id="harbor",
        place="the little harbor",
        detail="Tar smell rose from the pilings, and a painted practice ship bobbed at the quay like a patient old sea horse.",
        affords={"lookout", "map_reader", "bell_keeper"},
        tags={"harbor", "pirate"},
    ),
    "lighthouse_pier": Setting(
        id="lighthouse_pier",
        place="the lighthouse pier",
        detail="A red lantern blinked beyond the waves, and the boards shone pale under a wash of sea spray.",
        affords={"lookout", "bell_keeper"},
        tags={"pier", "pirate"},
    ),
    "museum_ship": Setting(
        id="museum_ship",
        place="the museum ship dock",
        detail="A grand old ship sat tied to shore, all polished rails and tall masts, waiting for children to play at voyages.",
        affords={"map_reader", "bell_keeper"},
        tags={"ship", "pirate"},
    ),
}

INTERVIEWS = {
    "lookout": InterviewKind(
        id="lookout",
        title="Lookout Mate",
        station="the crow's-nest ladder",
        task="spot the safest path through fog and rocks",
        question="If fog rolls in and you hear a bell to starboard, what should the lookout do first?",
        good_answer="Call the bell, point the captain toward open water, and keep watching.",
        skill_line="All week, the child had practiced peering past barrels and chimneys, pretending they were reefs.",
        reward="a little blue lookout ribbon",
        ending_image="With the ribbon bright on the shirt, the child climbed two safe rungs of the ladder and looked out over silver water, standing taller than before.",
        tags={"lookout", "interview"},
    ),
    "map_reader": InterviewKind(
        id="map_reader",
        title="Map Reader",
        station="the chart table under a striped awning",
        task="read a chart and guide the crew the right way",
        question="If the red X is beyond the shallow sandbar, how should the crew go?",
        good_answer="Follow the deep-water line around the sandbar and then turn toward the X.",
        skill_line="The child loved tracing old charts with one careful finger as if every wrinkle hid a cove.",
        reward="a rolled paper chart tied with green string",
        ending_image="Soon the child stood at the chart table with the gifted map tucked under one arm, while the harbor breeze fluttered the edges like eager sails.",
        tags={"map", "interview"},
    ),
    "bell_keeper": InterviewKind(
        id="bell_keeper",
        title="Bell Keeper",
        station="the brass bell stand near the gangplank",
        task="ring clear warnings at the right time",
        question="When should the bell ring two quick notes?",
        good_answer="When the gangplank is lifting and everyone must stand clear.",
        skill_line="Every clang in the harbor made the child listen hard, trying to learn which sounds meant hurry and which meant home.",
        reward="a small polished bell badge",
        ending_image="The badge gleamed like a drop of sun as the child practiced one careful ring, and even the gulls seemed to listen.",
        tags={"bell", "interview"},
    ),
}

TEMPTATIONS = {
    "answer_card": Temptation(
        id="answer_card",
        label="an answer card",
        phrase="a folded answer card",
        clue="a neat sentence about where to steer in fog",
        owner_mark="Captain's Interview Notes",
        cheat_line="Call the bell, point the captain toward open water, and keep watching.",
        topic="lookout",
        tags={"answer_card", "honesty", "interview"},
    ),
    "marked_chart": Temptation(
        id="marked_chart",
        label="a marked chart",
        phrase="a rolled chart with one corner peeking free",
        clue="a red line curling around a sandbar",
        owner_mark="Captain's Interview Notes",
        cheat_line="Follow the deep-water line around the sandbar and then turn toward the X.",
        topic="map_reader",
        tags={"map", "honesty", "interview"},
    ),
    "signal_sheet": Temptation(
        id="signal_sheet",
        label="a signal sheet",
        phrase="a crisp signal sheet",
        clue="two tiny bell marks inked beside a gangplank drawing",
        owner_mark="Captain's Interview Notes",
        cheat_line="Ring two quick notes when the gangplank is lifting and everyone must stand clear.",
        topic="bell_keeper",
        tags={"bell", "honesty", "interview"},
    ),
}

ACTIONS = {
    "return_sealed": "return the packet unopened",
    "peek_then_confess": "peek and then confess before the interview",
    "hide_and_use": "hide the packet and use the answer",
}

GIRL_NAMES = ["Nell", "Mira", "Ruby", "Lina", "Tess", "Poppy", "Wren", "Maisie"]
BOY_NAMES = ["Toby", "Finn", "Jory", "Kit", "Sam", "Owen", "Eli", "Ben"]
CAPTAINS = [
    ("Captain Mara", "captain_woman"),
    ("Captain Reed", "captain_man"),
    ("Captain Inez", "captain_woman"),
    ("Captain Sol", "captain_man"),
]

if __name__ == "__main__":
    main()
