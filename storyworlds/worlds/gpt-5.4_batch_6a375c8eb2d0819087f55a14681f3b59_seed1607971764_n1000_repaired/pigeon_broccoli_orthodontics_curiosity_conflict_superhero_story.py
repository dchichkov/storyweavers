#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pigeon_broccoli_orthodontics_curiosity_conflict_superhero_story.py
================================================================================================

A standalone storyworld for a tiny superhero story domain: a child goes to an
orthodontics visit, feels nervous, gets curious about the tools, and finds a
brave way through the conflict. A pigeon outside the clinic becomes a little
superhero image, and broccoli appears in the ending as a food the child wants to
crunch again once their teeth are being helped.

Run it
------
python storyworlds/worlds/gpt-5.4/pigeon_broccoli_orthodontics_curiosity_conflict_superhero_story.py
python storyworlds/worlds/gpt-5.4/pigeon_broccoli_orthodontics_curiosity_conflict_superhero_story.py --visit braces_check --support mirror_demo --food broccoli_soup
python storyworlds/worlds/gpt-5.4/pigeon_broccoli_orthodontics_curiosity_conflict_superhero_story.py --visit spacer_fit --food raw_broccoli
python storyworlds/worlds/gpt-5.4/pigeon_broccoli_orthodontics_curiosity_conflict_superhero_story.py --all --qa
python storyworlds/worlds/gpt-5.4/pigeon_broccoli_orthodontics_curiosity_conflict_superhero_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "orthodontist_woman"}
        male = {"boy", "father", "man", "orthodontist_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "mother":
            return "mom"
        if self.type == "father":
            return "dad"
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Visit:
    id: str
    label: str
    appliance: str
    challenge: str
    fear: int
    soreness: int
    question: str
    explain: str
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
class Support:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    power: int = 0
    action: str = ""
    qa_text: str = ""
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
class Food:
    id: str
    label: str
    phrase: str
    softness: int = 0
    ending: str = ""
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
    def __init__(self) -> None:
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
        clone = World()
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


def _r_chair_freeze(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["fear"] < THRESHOLD or child.meters["chair_ready"] < THRESHOLD:
        return []
    sig = ("freeze",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["conflict"] += 1
    return ["__freeze__"]


def _r_curiosity_helps(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["curiosity"] < THRESHOLD or child.meters["demo_seen"] < THRESHOLD:
        return []
    sig = ("curiosity_helps",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["bravery"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    return ["__curious_brave__"]


def _r_support_helps(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["support_used"] < THRESHOLD or world.facts.get("support_match", 0) < THRESHOLD:
        return []
    sig = ("support_helps",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["bravery"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    return ["__support__"]


def _r_visit_done(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["bravery"] < THRESHOLD or child.meters["chair_ready"] < THRESHOLD:
        return []
    sig = ("visit_done",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["visit_done"] += 1
    child.memes["conflict"] = 0.0
    child.memes["pride"] += 1
    child.meters["bite_future"] += 1
    return ["__done__"]


CAUSAL_RULES = [
    Rule(name="chair_freeze", tag="social", apply=_r_chair_freeze),
    Rule(name="curiosity_helps", tag="emotional", apply=_r_curiosity_helps),
    Rule(name="support_helps", tag="emotional", apply=_r_support_helps),
    Rule(name="visit_done", tag="physical", apply=_r_visit_done),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def support_matches(visit: Visit, support: Support) -> bool:
    return visit.challenge in support.helps


def food_safe(visit: Visit, food: Food) -> bool:
    return food.softness >= visit.soreness


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for visit_id, visit in VISITS.items():
        for support_id, support in SUPPORTS.items():
            if not support_matches(visit, support):
                continue
            for food_id, food in FOODS.items():
                if food_safe(visit, food):
                    combos.append((visit_id, support_id, food_id))
    return combos


@dataclass
class StoryParams:
    visit: str
    support: str
    food: str
    child_name: str
    child_gender: str
    parent: str
    orthodontist: str
    costume: str
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


def introduce(world: World, child: Entity, parent: Entity, costume: str) -> None:
    world.say(
        f"{child.id} liked to pretend that ordinary days were secret missions. "
        f"On this day, {child.pronoun('possessive')} {costume} was tied so neatly that "
        f"{child.pronoun()} felt almost ready to fly."
    )
    world.say(
        f"But the mission was not to save a city. It was to walk into the orthodontics clinic "
        f"with {child.pronoun('possessive')} {parent.label_word} and be brave."
    )


def arrive(world: World, child: Entity, parent: Entity, orthodontist: Entity) -> None:
    pigeon = world.get("pigeon")
    world.say(
        f"Outside the glass door, a pigeon strutted along the rail as if it were guarding the building. "
        f"{child.id} stopped to watch its shiny neck flash green and purple."
    )
    world.say(
        f'"Maybe that pigeon is the roof captain," {child.id} whispered. '
        f'{parent.label_word.capitalize()} smiled and opened the door.'
    )
    world.say(
        f"Inside, the room smelled clean, and {orthodontist.label} waved from beside the bright chair."
    )


def conflict(world: World, child: Entity, visit: Visit) -> None:
    child.meters["chair_ready"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Today was for {visit.label}. The chair looked big, the lamp looked brighter than a moon-beam, '
        f'and {child.id} suddenly wished the mission had been somewhere else.'
    )
    if child.memes["conflict"] >= THRESHOLD:
        world.say(
            f"{child.pronoun().capitalize()} took one step back and gripped the edge of {child.pronoun('possessive')} cape."
        )


def curiosity_question(world: World, child: Entity, orthodontist: Entity, visit: Visit) -> None:
    child.memes["curiosity"] += 1
    child.meters["demo_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then curiosity poked through the worry. {child.id} pointed at the tray and asked, "
        f'"{visit.question}"'
    )
    world.say(
        f'{orthodontist.label} crouched down and answered, "{visit.explain}"'
    )


def use_support(world: World, child: Entity, orthodontist: Entity, support: Support) -> None:
    world.facts["support_match"] = 1.0
    child.meters["support_used"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Next, {orthodontist.label} {support.action}. "
        f"{child.id} tried {support.phrase} the way a superhero would follow a training plan."
    )


def finish_visit(world: World, child: Entity, orthodontist: Entity, visit: Visit) -> None:
    propagate(world, narrate=False)
    if child.meters["visit_done"] < THRESHOLD:
        raise StoryError("The visit could not be completed with this support plan.")
    world.say(
        f"Soon the hard part was over. {orthodontist.label} said that {visit.appliance} was doing its job "
        f"and that patient practice now would help {child.id}'s teeth line up well later."
    )
    world.say(
        f"{child.id} slid out of the chair feeling taller than before, as if bravery had clicked into place too."
    )


def ending(world: World, child: Entity, parent: Entity, food: Food) -> None:
    pigeon = world.get("pigeon")
    world.say(
        f"Outside again, the pigeon was still there, bobbing along the rail like a tiny hero on patrol. "
        f"{child.id} gave it a solemn nod."
    )
    world.say(
        f'"Mission done," {child.id} said. On the way home, {parent.label_word} promised {food.phrase}, '
        f"and {child.id} imagined the broccoli like little green superhero trees."
    )
    world.say(food.ending)


def tell(
    visit: Visit,
    support: Support,
    food: Food,
    child_name: str = "Maya",
    child_gender: str = "girl",
    parent_type: str = "mother",
    orthodontist_type: str = "orthodontist_woman",
    costume: str = "red cape",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, role="child", label=child_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent", label="the parent"))
    orthodontist = world.add(
        Entity(
            id="orthodontist",
            kind="character",
            type=orthodontist_type,
            role="orthodontist",
            label="Dr. Bright",
        )
    )
    pigeon = world.add(Entity(id="pigeon", kind="thing", type="bird", role="bird", label="pigeon"))

    child.attrs["costume"] = costume
    child.memes["fear"] = float(visit.fear)
    child.memes["curiosity"] = 0.0
    child.memes["bravery"] = 0.0
    child.memes["conflict"] = 0.0
    child.memes["pride"] = 0.0
    child.meters["chair_ready"] = 0.0
    child.meters["demo_seen"] = 0.0
    child.meters["support_used"] = 0.0
    child.meters["visit_done"] = 0.0
    child.meters["bite_future"] = 0.0
    world.facts["support_match"] = 0.0

    introduce(world, child, parent, costume)
    world.para()
    arrive(world, child, parent, orthodontist)
    conflict(world, child, visit)
    curiosity_question(world, child, orthodontist, visit)
    use_support(world, child, orthodontist, support)
    world.para()
    finish_visit(world, child, orthodontist, visit)
    ending(world, child, parent, food)

    world.facts.update(
        child=child,
        parent=parent,
        orthodontist=orthodontist,
        pigeon=pigeon,
        visit=visit,
        support=support,
        food=food,
        brave=child.meters["visit_done"] >= THRESHOLD,
        conflict_seen=True,
        curiosity_used=child.meters["demo_seen"] >= THRESHOLD,
    )
    return world


VISITS = {
    "braces_check": Visit(
        id="braces_check",
        label="a braces check",
        appliance="the braces",
        challenge="mouth_open",
        fear=2,
        soreness=1,
        question="What does that little mirror do?",
        explain="It lets me see hidden tooth corners, like a tiny moon for small caves in your mouth.",
        tags={"braces", "orthodontics"},
    ),
    "xray_scan": Visit(
        id="xray_scan",
        label="an orthodontics picture scan",
        appliance="the growing teeth under the gums",
        challenge="stillness",
        fear=1,
        soreness=0,
        question="Why does that camera swing around the chair?",
        explain="It makes a careful picture map, so I can plan where each tooth should go.",
        tags={"xray", "orthodontics"},
    ),
    "spacer_fit": Visit(
        id="spacer_fit",
        label="a spacer fitting",
        appliance="the tiny spacer",
        challenge="tight_feel",
        fear=2,
        soreness=2,
        question="Why does the band look so small?",
        explain="Small parts can make just enough room, and a little room now can help bigger teeth later.",
        tags={"spacer", "orthodontics"},
    ),
}

SUPPORTS = {
    "mirror_demo": Support(
        id="mirror_demo",
        label="mirror demo",
        phrase="watching the mirror first",
        helps={"mouth_open"},
        power=2,
        action="held up a hand mirror and showed exactly where the tiny mouth mirror would go",
        qa_text="showed a mirror demonstration first",
        tags={"mirror"},
    ),
    "statue_breaths": Support(
        id="statue_breaths",
        label="statue breaths",
        phrase="three statue breaths and staying still like a rooftop guardian",
        helps={"stillness"},
        power=1,
        action="taught a game of slow statue breaths and asked the whole room to freeze for three counts",
        qa_text="used slow statue breaths to help stay still",
        tags={"breathing"},
    ),
    "finger_press": Support(
        id="finger_press",
        label="finger press practice",
        phrase="pressing a finger first and feeling that the strange part was only a short squeeze",
        helps={"tight_feel"},
        power=2,
        action="pressed gently on one finger first, then explained that the tight feeling would be quick and safe",
        qa_text="practiced the tight feeling on a finger first",
        tags={"practice"},
    ),
}

FOODS = {
    "broccoli_soup": Food(
        id="broccoli_soup",
        label="broccoli soup",
        phrase="warm broccoli soup with tiny star crackers",
        softness=2,
        ending="That evening, the spoon clinked softly against the bowl, and even a brave mouth could rest while it healed.",
        tags={"broccoli", "soft_food"},
    ),
    "steamed_broccoli": Food(
        id="steamed_broccoli",
        label="steamed broccoli",
        phrase="a plate of soft steamed broccoli with noodles",
        softness=1,
        ending="The broccoli was soft enough to nibble carefully, and the meal felt like a quiet victory feast after the mission.",
        tags={"broccoli", "soft_food"},
    ),
    "raw_broccoli": Food(
        id="raw_broccoli",
        label="raw broccoli",
        phrase="a bowl of crunchy raw broccoli trees",
        softness=0,
        ending="At dinner, the child proudly crunched the little green trees and laughed at the snap they made.",
        tags={"broccoli", "crunchy_food"},
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Max", "Sam", "Eli", "Noah", "Finn"]
COSTUMES = ["red cape", "blue cape", "silver mask", "lightning wristband"]


KNOWLEDGE = {
    "orthodontics": [
        (
            "What is orthodontics?",
            "Orthodontics is the kind of dental care that helps teeth and jaws grow in better positions. It can include braces, spacers, and special pictures of the teeth.",
        )
    ],
    "braces": [
        (
            "What do braces do?",
            "Braces put gentle pressure on teeth over time so the teeth can line up better. They work slowly, not all at once.",
        )
    ],
    "xray": [
        (
            "Why do dentists or orthodontists take pictures of teeth?",
            "They take pictures so they can see parts of the teeth that are hard to see from the outside. Good pictures help them plan safe care.",
        )
    ],
    "spacer": [
        (
            "What is a spacer for in orthodontics?",
            "A spacer is a tiny part that makes a little room between teeth. That room can help another orthodontic part fit later.",
        )
    ],
    "mirror": [
        (
            "Why does a dentist use a little mirror?",
            "A little mirror helps the dentist or orthodontist see the backs and sides of teeth. It lets them check places eyes cannot see directly.",
        )
    ],
    "breathing": [
        (
            "Why can slow breaths help when you feel worried?",
            "Slow breaths help your body calm down. When your body calms down, it is easier to stay still and listen.",
        )
    ],
    "practice": [
        (
            "Why does it help to practice a new feeling first?",
            "Practice makes a strange feeling less surprising. When you know what to expect, it can feel easier to be brave.",
        )
    ],
    "broccoli": [
        (
            "Why do people say broccoli is healthy?",
            "Broccoli is a vegetable with vitamins and fiber. Eating vegetables helps your body grow and stay strong.",
        )
    ],
    "soft_food": [
        (
            "Why might someone eat soft food after dental work?",
            "Soft food is gentle on a sore mouth. It can be easier to chew while your teeth or gums are settling down.",
        )
    ],
    "crunchy_food": [
        (
            "Why can crunchy food be hard for a sore mouth?",
            "Crunchy food pushes harder on teeth and gums. If a mouth feels sore, softer food can feel better for a while.",
        )
    ],
    "pigeon": [
        (
            "What is a pigeon?",
            "A pigeon is a bird often seen in towns and cities. It walks with a bobbing head and can fly up to roofs and rails.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "orthodontics",
    "braces",
    "xray",
    "spacer",
    "mirror",
    "breathing",
    "practice",
    "broccoli",
    "soft_food",
    "crunchy_food",
    "pigeon",
]


def explain_rejection(visit: Visit, support: Optional[Support] = None, food: Optional[Food] = None) -> str:
    if support is not None and not support_matches(visit, support):
        return (
            f"(No story: {support.label} does not honestly help with {visit.label}. "
            f"The support has to match the hard part of the visit, which here is {visit.challenge.replace('_', ' ')}.)"
        )
    if food is not None and not food_safe(visit, food):
        return (
            f"(No story: after {visit.label}, {food.label} is too hard for a mouth with that much soreness. "
            f"Pick a gentler broccoli meal.)"
        )
    return "(No valid combination matches the given options.)"


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    visit = world.facts["visit"]
    return [
        'Write a superhero story for a 3-to-5-year-old that includes the words "pigeon", "broccoli", and "orthodontics".',
        f"Tell a gentle story where a child named {child.label} feels nervous about {visit.label} but curiosity helps turn fear into bravery.",
        "Write a story with conflict at a clinic, a tiny bird image outside, and an ending that shows the child has changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    orthodontist = world.facts["orthodontist"]
    visit = world.facts["visit"]
    support = world.facts["support"]
    food = world.facts["food"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child who treats the orthodontics visit like a superhero mission. "
            f"{parent.label_word.capitalize()} and {orthodontist.label} help during the hard part.",
        ),
        (
            "Why did the visit feel like a conflict at first?",
            f"The chair and tools made {child.label} feel nervous, so {child.pronoun()} wanted to pull back instead of climbing in. "
            f"That fear created the conflict before the visit really began.",
        ),
        (
            "How did curiosity help?",
            f"{child.label} asked a question about the tools instead of only staring at them. "
            f"When {orthodontist.label} explained what they were for, the strange things felt more understandable and less scary.",
        ),
        (
            f"How did {orthodontist.label} help {child.label} be brave?",
            f"{orthodontist.label} {support.qa_text}. "
            f"That method matched the hard part of {visit.label}, so {child.label} could stay with the mission instead of backing away.",
        ),
        (
            "Why was broccoli mentioned at the end?",
            f"Broccoli was part of the going-home meal that fit what {child.label}'s mouth could handle after the visit. "
            f"The ending turns broccoli into superhero fuel, which shows the child is thinking about the day with pride instead of fear.",
        ),
        (
            "What was the pigeon doing in the story?",
            f"The pigeon outside the clinic became a little superhero image for {child.label}. "
            f"Seeing it again at the end made the finished mission feel real and complete.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"orthodontics", "pigeon"}
    visit = world.facts["visit"]
    support = world.facts["support"]
    food = world.facts["food"]
    tags |= set(visit.tags)
    tags |= set(support.tags)
    tags |= set(food.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:18}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% gate: a support is valid only if it helps with the visit's challenge.
support_matches(V,S) :- visit(V), support(S), challenge(V,C), helps(S,C).

% gate: food must be soft enough for the soreness level after the visit.
food_safe(V,F) :- visit(V), food(F), soreness(V,SV), softness(F,SF), SF >= SV.

valid(V,S,F) :- support_matches(V,S), food_safe(V,F).

% simple declarative outcome twin: matched support + curiosity explain a visit.
base_bravery(V,1) :- visit(V), fear(V,1).
base_bravery(V,1) :- visit(V), fear(V,2).
curiosity_bonus(V,1) :- visit(V).
support_bonus(V,1) :- visit(V), support_matches(V,S), chosen_support(S).
total_bravery(V,B0 + B1 + B2) :- chosen_visit(V), base_bravery(V,B0), curiosity_bonus(V,B1), support_bonus(V,B2).
done :- chosen_visit(V), fear(V,F), total_bravery(V,B), B >= F.
outcome(brave) :- done.
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for visit_id, visit in VISITS.items():
        lines.append(asp.fact("visit", visit_id))
        lines.append(asp.fact("challenge", visit_id, visit.challenge))
        lines.append(asp.fact("fear", visit_id, visit.fear))
        lines.append(asp.fact("soreness", visit_id, visit.soreness))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        for item in sorted(support.helps):
            lines.append(asp.fact("helps", support_id, item))
        lines.append(asp.fact("power", support_id, support.power))
    for food_id, food in FOODS.items():
        lines.append(asp.fact("food", food_id))
        lines.append(asp.fact("softness", food_id, food.softness))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    visit = VISITS[params.visit]
    support = SUPPORTS[params.support]
    brave = 1 + 1 + (1 if support_matches(visit, support) else 0)
    return "brave" if brave >= visit.fear else "stuck"


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_visit", params.visit),
            asp.fact("chosen_support", params.support),
            asp.fact("chosen_food", params.food),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        visit="braces_check",
        support="mirror_demo",
        food="steamed_broccoli",
        child_name="Maya",
        child_gender="girl",
        parent="mother",
        orthodontist="orthodontist_woman",
        costume="red cape",
    ),
    StoryParams(
        visit="xray_scan",
        support="statue_breaths",
        food="raw_broccoli",
        child_name="Leo",
        child_gender="boy",
        parent="father",
        orthodontist="orthodontist_man",
        costume="blue cape",
    ),
    StoryParams(
        visit="spacer_fit",
        support="finger_press",
        food="broccoli_soup",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        orthodontist="orthodontist_woman",
        costume="silver mask",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a superhero child, an orthodontics visit, curiosity, and courage."
    )
    ap.add_argument("--visit", choices=VISITS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--orthodontist", choices=["orthodontist_woman", "orthodontist_man"])
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.visit and args.support:
        visit = VISITS[args.visit]
        support = SUPPORTS[args.support]
        if not support_matches(visit, support):
            raise StoryError(explain_rejection(visit, support=support))
    if args.visit and args.food:
        visit = VISITS[args.visit]
        food = FOODS[args.food]
        if not food_safe(visit, food):
            raise StoryError(explain_rejection(visit, food=food))

    combos = [
        combo
        for combo in valid_combos()
        if (args.visit is None or combo[0] == args.visit)
        and (args.support is None or combo[1] == args.support)
        and (args.food is None or combo[2] == args.food)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    visit_id, support_id, food_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    orthodontist = args.orthodontist or rng.choice(["orthodontist_woman", "orthodontist_man"])
    costume = args.costume or rng.choice(COSTUMES)
    return StoryParams(
        visit=visit_id,
        support=support_id,
        food=food_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        orthodontist=orthodontist,
        costume=costume,
    )


def generate(params: StoryParams) -> StorySample:
    if params.visit not in VISITS:
        raise StoryError(f"(Unknown visit: {params.visit})")
    if params.support not in SUPPORTS:
        raise StoryError(f"(Unknown support: {params.support})")
    if params.food not in FOODS:
        raise StoryError(f"(Unknown food: {params.food})")
    visit = VISITS[params.visit]
    support = SUPPORTS[params.support]
    food = FOODS[params.food]
    if not support_matches(visit, support):
        raise StoryError(explain_rejection(visit, support=support))
    if not food_safe(visit, food):
        raise StoryError(explain_rejection(visit, food=food))

    world = tell(
        visit=visit,
        support=support,
        food=food,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        orthodontist_type=params.orthodontist,
        costume=params.costume,
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
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
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (visit, support, food) combos:\n")
        for visit_id, support_id, food_id in combos:
            print(f"  {visit_id:12} {support_id:15} {food_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.child_name}: {p.visit} with {p.support} ({p.food})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
