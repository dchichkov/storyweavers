#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ridiculous_hangar_ash_happy_ending_moral_value.py
==============================================================================

A standalone story world for a small Animal Story domain:

Two young animals are making a flying toy in an old hangar for a windy-day
parade. One of them wants a dramatic shortcut: rubbing ash onto the wings to
make the toy look dark and fast. The other warns that ash can weaken light
materials. If the warning works, they choose a patient, honest finish and the
toy flies well. If it does not, the launch fails, feelings get hurt, and only
an honest confession plus careful repair brings the happy ending.

The seed words appear naturally in the prose: ridiculous, hangar, ash.

Run it
------
    python storyworlds/worlds/gpt-5.4/ridiculous_hangar_ash_happy_ending_moral_value.py
    python storyworlds/worlds/gpt-5.4/ridiculous_hangar_ash_happy_ending_moral_value.py --craft kite --material bark_board
    python storyworlds/worlds/gpt-5.4/ridiculous_hangar_ash_happy_ending_moral_value.py --response blow_on_it
    python storyworlds/worlds/gpt-5.4/ridiculous_hangar_ash_happy_ending_moral_value.py --all
    python storyworlds/worlds/gpt-5.4/ridiculous_hangar_ash_happy_ending_moral_value.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ridiculous_hangar_ash_happy_ending_moral_value.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    ash_sensitive: bool = False
    can_fly: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"goose", "hen", "ewe", "doe", "girl"}
        male = {"badger", "bear", "fox", "boy"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Craft:
    id: str
    label: str
    phrase: str
    made_of: str
    flies_as: str
    launch_line: str
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
class Material:
    id: str
    label: str
    phrase: str
    panel_word: str
    ash_sensitive: bool
    fragility: int
    dirty_text: str
    repair_text: str
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
class Finish:
    id: str
    label: str
    phrase: str
    bright_text: str
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
class Response:
    id: str
    sense: int
    text: str
    qa_text: str
    fail_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
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


def _r_ash_harms(world: World) -> list[str]:
    out: list[str] = []
    craft = world.get("craft")
    if craft.meters["ash"] < THRESHOLD or not craft.ash_sensitive:
        return out
    sig = ("ash_harms", craft.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    craft.meters["dusty"] += 1
    craft.meters["fragile"] += craft.attrs.get("fragility", 1)
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__ashy__")
    return out


def _r_bad_launch(world: World) -> list[str]:
    out: list[str] = []
    craft = world.get("craft")
    if craft.meters["launched"] < THRESHOLD or craft.meters["fragile"] < THRESHOLD:
        return out
    sig = ("bad_launch", craft.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    craft.meters["dipped"] += 1
    craft.meters["crumpled"] += 1
    for kid in world.kids():
        kid.memes["sadness"] += 1
        kid.memes["conflict"] += 1
    out.append("__dip__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="ash_harms", tag="physical", apply=_r_ash_harms),
    Rule(name="bad_launch", tag="physical_social", apply=_r_bad_launch),
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


def ash_risk(material: Material) -> bool:
    return material.ash_sensitive


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def would_listen(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > instigator_age
    authority = (5.0 if trait in CAUTIOUS_TRAITS else 3.0) + 1.0 + (4.0 if older else 0.0)
    return older and authority > BRAVERY_INIT


def outcome_of(params: "StoryParams") -> str:
    if would_listen(
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        trait=params.trait,
    ):
        return "listened"
    response = RESPONSES[params.response]
    return "mended" if response.sense >= SENSE_MIN else "spoiled"


def predict_failure(world: World) -> dict:
    sim = world.copy()
    craft = sim.get("craft")
    craft.meters["ash"] += 1
    propagate(sim, narrate=False)
    craft.meters["launched"] += 1
    propagate(sim, narrate=False)
    return {
        "dusty": craft.meters["dusty"] >= THRESHOLD,
        "fragile": craft.meters["fragile"],
        "dipped": craft.meters["dipped"] >= THRESHOLD,
    }


def scene_setup(world: World, a: Entity, b: Entity, craft_cfg: Craft, material: Material) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"Beside the old hangar at the edge of the meadow, {a.id} and {b.id} were "
        f"building {craft_cfg.phrase}. The {material.panel_word} was {craft_cfg.made_of}, "
        f"and both friends hoped it would shine in the Wind Parade."
    )
    world.say(
        f"{a.id} twitched with excitement. {a.pronoun().capitalize()} wanted {craft_cfg.label} "
        f"to look faster and grander than any other toy in the field."
    )


def desire_dark_finish(world: World, a: Entity) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'"If it has dark storm stripes, everyone will stare," {a.id} said. '
        f'"It will look wonderfully fierce instead of plain."'
    )


def tempt_with_ash(world: World, a: Entity) -> None:
    world.say(
        f"Near the hangar door sat a cold little pail of ash from last night's stove. "
        f'{a.id} pointed at it and grinned. "We can dust the wings with that. '
        f'It will look bold, and we will finish first."'
    )


def warn(world: World, b: Entity, a: Entity, material: Material) -> None:
    pred = predict_failure(world)
    b.memes["caution"] += 1
    world.facts["predicted_fragile"] = pred["fragile"]
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "That is a ridiculous shortcut," '
        f'{b.pronoun()} said. "Ash is soft and dirty, but on {material.phrase} it can '
        f"rub in, make the panel weak, and spoil the flight."
    )
    if pred["dipped"]:
        world.say(
            f'{b.id} looked at the thin wings and added, "If we launch it after that, '
            f'it may dip right down instead of riding the wind."'
        )


def back_down(world: World, a: Entity, b: Entity, finish: Finish) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} stared at the pail, then at {b.id}. At last {a.pronoun()} let out a small breath. '
        f'"You are right," {a.pronoun()} said. "Fast is no use if the wings turn weak."'
    )
    world.say(
        f"Instead of touching the ash, they opened their paint shell and used {finish.phrase}. "
        f"The careful color took longer, but it sat neatly on the wings."
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"We do not need to fuss so much," {a.id} said. "A little ash will not hurt." '
        f"{b.id} reached out, but {a.id} was already hurrying to the pail."
    )


def apply_ash(world: World, craft_cfg: Craft, material: Material) -> None:
    craft = world.get("craft")
    craft.meters["ash"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{craft_cfg.label.capitalize()} soon wore gray streaks of ash. At first the marks looked "
        f"dramatic, but when {a_or_they(world.get('instigator'))} brushed the wings, "
        f"{material.dirty_text}."
    )


def launch(world: World, craft_cfg: Craft, a: Entity, b: Entity) -> None:
    craft = world.get("craft")
    craft.meters["launched"] += 1
    propagate(world, narrate=False)
    if craft.meters["dipped"] >= THRESHOLD:
        world.say(
            f"They ran to the breezy strip beside the hangar and gave {craft_cfg.label} a launch. "
            f"For one hopeful blink it rose, and then it dipped, wobbled, and fell into the grass."
        )
        world.say(
            f'{b.id} gasped. "{craft_cfg.label.capitalize()} cannot hold the wind now," {b.id} said. '
            f'{a.id} stamped one foot and felt hot behind the eyes.'
        )
    else:
        world.say(
            f"They ran to the breezy strip beside the hangar and gave {craft_cfg.label} a launch. "
            f"It caught the wind at once and sailed in a bright curve over the clover."
        )


def quarrel(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f'For a moment the two friends stood in silence. Then {b.id} said, "I tried to warn you," '
        f"and {a.id} muttered that the idea had only been meant to help."
    )


def confess(world: World, a: Entity, b: Entity) -> None:
    a.memes["honesty"] += 1
    b.memes["softness"] += 1
    world.say(
        f'At last {a.id} lowered {a.pronoun("possessive")} ears and said, "I wanted a quick, grand look. '
        f'I was wrong, and I am sorry."'
    )
    world.say(
        f"{b.id}'s face softened. {b.pronoun().capitalize()} was still upset, but {b.pronoun()} nodded, "
        f"because honest words make room for mending."
    )


def repair(world: World, helper: Entity, response: Response, material: Material, finish: Finish) -> None:
    craft = world.get("craft")
    craft.meters["dusty"] = 0.0
    craft.meters["fragile"] = 0.0
    craft.meters["crumpled"] = 0.0
    craft.meters["repaired"] += 1
    craft.meters["finished_safely"] += 1
    world.say(
        f"Just then {helper.id}, the hangar goose who knew every spool and scrap, waddled over. "
        f"{helper.pronoun().capitalize()} listened, then {response.text}."
    )
    world.say(
        f"Little by little the dusty panel grew clean again, and {material.repair_text}. "
        f"Then they added {finish.phrase}, which was bright and light instead of grimy."
    )


def relaunch_success(world: World, craft_cfg: Craft, a: Entity, b: Entity, finish: Finish) -> None:
    craft = world.get("craft")
    craft.meters["launched"] += 1
    craft.meters["flying"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    world.say(
        f"They tried once more. This time {craft_cfg.label} {craft_cfg.flies_as}, "
        f"and the {finish.bright_text} flashed in the sun."
    )
    world.say(
        f"{a.id} laughed first, then {b.id} laughed too, and soon they were running under it together."
    )


def ending_moral(world: World, a: Entity, b: Entity) -> None:
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1
    world.say(
        f"By parade time, the toy flew true, and the two friends were proud for a better reason: "
        f"they had fixed their trouble with honesty and patient work."
    )
    world.say(
        f"Whenever {a.id} grew tempted by a flashy shortcut after that, {a.pronoun()} remembered the ash, "
        f"the wobble, and the happy repair. Good work, {a.pronoun()} learned, does not need a foolish hurry."
    )


def a_or_they(ent: Entity) -> str:
    return ent.pronoun("subject").capitalize()
@dataclass
class StoryParams:
    craft: str
    material: str
    finish: str
    response: str
    instigator: str
    instigator_type: str
    cautioner: str
    cautioner_type: str
    helper_name: str
    trait: str
    relation: str = "friends"
    instigator_age: int = 5
    cautioner_age: int = 6
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
    "ash": [
        (
            "What is ash?",
            "Ash is the soft gray powder left after wood burns. It can make things dirty and dusty very quickly.",
        )
    ],
    "kite": [
        (
            "What helps a kite fly?",
            "A kite flies when wind pushes on a light, balanced shape. If the covering is weak or bent, it cannot ride the air well.",
        )
    ],
    "glider": [
        (
            "Why does a glider need smooth wings?",
            "A glider needs smooth, light wings so the air can hold it up. A weak or crumpled wing makes it dip instead of glide.",
        )
    ],
    "pinwheel": [
        (
            "Why does a pinwheel spin?",
            "A pinwheel spins because the wind pushes on its angled blades. Light, tidy blades catch the breeze best.",
        )
    ],
    "repair": [
        (
            "Why is patient repair better than a quick shortcut?",
            "Patient repair fixes the real problem instead of hiding it for a moment. Careful work often saves a toy better than rushing.",
        )
    ],
    "paint": [
        (
            "Why can paint be safer than rubbing dirt on something?",
            "Paint is made to add color without grinding crumbs into a surface. Dirt and ash can rub in and spoil light materials.",
        )
    ],
    "honesty": [
        (
            "Why does telling the truth help after a mistake?",
            "Telling the truth helps because other people can understand what happened and help fix it. Honest words can stop a quarrel from growing bigger.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ash", "kite", "glider", "pinwheel", "paint", "repair", "honesty"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    craft_cfg = f["craft_cfg"]
    material_cfg = f["material_cfg"]
    if f["outcome"] == "listened":
        return [
            'Write an animal story for a young child that includes the words "ridiculous", "hangar", and "ash".',
            f"Tell a gentle story where {a.id} wants to decorate a {craft_cfg.label} with ash, but {b.id} warns that {material_cfg.phrase} would be hurt by it, and the friends choose a patient, happy solution.",
            "Write a short moral tale where a flashy shortcut is refused, careful work wins, and the ending shows the friends proud of doing things the honest way.",
        ]
    return [
        'Write an animal story for a young child that includes the words "ridiculous", "hangar", and "ash".',
        f"Tell a story where {a.id} ignores a warning, rubs ash on a {craft_cfg.label}, and the first launch goes wrong, but an honest apology and patient repair lead to a happy ending.",
        "Write a simple conflict-and-resolution tale where two animal friends quarrel over a foolish shortcut and learn that honesty and careful work can mend both toys and feelings.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    craft_cfg = f["craft_cfg"]
    material_cfg = f["material_cfg"]
    finish_cfg = f["finish_cfg"]
    response_cfg = f["response_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two young animals making {craft_cfg.phrase} beside an old hangar. {helper.id}, the wise goose, helps later when the trouble needs mending.",
        ),
        (
            f"Why did {a.id} want the {craft_cfg.label} to look dark?",
            f"{a.id} wanted it to seem bold and fast for the Wind Parade. That wish for a grand, quick result is what made the ash idea tempting.",
        ),
        (
            f"Why did {b.id} call the ash plan ridiculous?",
            f"{b.id} knew that ash would rub into {material_cfg.phrase} and weaken it. The warning was not about being unkind; it was about keeping the toy strong enough to fly.",
        ),
    ]
    if f["outcome"] == "listened":
        qa.append(
            (
                f"What happened after {b.id} warned {a.id}?",
                f"{a.id} listened and left the ash alone. Then they used {finish_cfg.phrase}, and the {craft_cfg.label} flew well because they chose a careful finish instead of a harmful shortcut.",
            )
        )
        qa.append(
            (
                "What lesson did the friends learn?",
                "They learned that patient work is better than a flashy shortcut. Taking a little more time kept the toy strong and let the day end happily.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when they launched the {craft_cfg.label} after using ash?",
                f"The first launch went badly: the {craft_cfg.label} dipped and fell because the ash had made the light wing weak. The failed flight also led to hurt feelings, so the problem became both physical and emotional.",
            )
        )
        qa.append(
            (
                f"How did {helper.id} help fix the problem?",
                f"{helper.id} {response_cfg.qa_text}. After that, the friends finished it with {finish_cfg.phrase}, so the toy became light and strong again.",
            )
        )
        qa.append(
            (
                "How was the conflict solved?",
                f"The conflict softened when {a.id} admitted the mistake and said sorry. Honest words made room for help, and working together on the repair let both the friendship and the flying toy recover.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ash", "repair", "honesty"}
    tags |= set(f["craft_cfg"].tags)
    tags |= set(f["finish_cfg"].tags)
    out: list[tuple[str, str]] = []
    mapped = {
        "kite": "kite",
        "glider": "glider",
        "pinwheel": "pinwheel",
        "paint": "paint",
        "berries": "paint",
        "flowers": "paint",
        "repair": "repair",
        "patch": "repair",
        "wash": "repair",
        "honesty": "honesty",
    }
    for raw in list(tags):
        if raw in mapped:
            tags.add(mapped[raw])
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.ash_sensitive:
            bits.append("ash_sensitive=True")
        if e.can_fly:
            bits.append("can_fly=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        craft="kite",
        material="paper",
        finish="berry_paint",
        response="clean_patch",
        instigator="Pip",
        instigator_type="fox",
        cautioner="Moss",
        cautioner_type="rabbit",
        helper_name="Greta",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        craft="glider",
        material="leaf_cloth",
        finish="flower_dye",
        response="wash_redye",
        instigator="Rusty",
        instigator_type="fox",
        cautioner="Poppy",
        cautioner_type="mouse",
        helper_name="Greta",
        trait="curious",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        craft="pinwheel",
        material="paper",
        finish="ribbon_tail",
        response="clean_patch",
        instigator="Milo",
        instigator_type="badger",
        cautioner="Thimble",
        cautioner_type="rabbit",
        helper_name="Greta",
        trait="steady",
        relation="friends",
        instigator_age=6,
        cautioner_age=5,
    ),
    StoryParams(
        craft="kite",
        material="leaf_cloth",
        finish="flower_dye",
        response="wash_redye",
        instigator="Fenn",
        instigator_type="fox",
        cautioner="Bramble",
        cautioner_type="rabbit",
        helper_name="Greta",
        trait="patient",
        relation="siblings",
        instigator_age=4,
        cautioner_age=6,
    ),
]


def explain_rejection(material: Material) -> str:
    return (
        f"(No story: ash does not honestly threaten {material.phrase}. "
        f"If the material would shrug the ash off, there is no real launch failure, "
        f"no grounded warning, and no need for a repair. Pick paper or leaf_cloth.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). The story prefers a real repair, "
        f"not a weak gesture. Try: {better}.)"
    )


ASP_RULES = r"""
% --- validity gate ---------------------------------------------------------
valid(C, M) :- craft(C), material(M), ash_sensitive(M).
sensible(R) :- response(R), sense(R, S), sense_min(Mn), S >= Mn.

% --- outcome model ---------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
listened :- cautioner_older, authority(A), bravery_init(BR), A > BR.

outcome(listened) :- listened.
outcome(mended) :- not listened, chosen_response(R), sensible(R).
outcome(spoiled) :- not listened, chosen_response(R), not sensible(R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for craft_id in CRAFTS:
        lines.append(asp.fact("craft", craft_id))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        if material.ash_sensitive:
            lines.append(asp.fact("ash_sensitive", material_id))
    for finish_id in FINISHES:
        lines.append(asp.fact("finish", finish_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
            asp.fact("chosen_response", params.response),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sense = set(asp_sensible())
    p_sense = {r.id for r in sensible_responses()}
    if c_sense == p_sense:
        print(f"OK: sensible responses match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a flashy ash shortcut, a conflict, and a happy mending."
    )
    ap.add_argument("--craft", choices=CRAFTS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--finish", choices=FINISHES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def pick_animal(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    pool = [
        ("fox", FOX_NAMES),
        ("rabbit", RABBIT_NAMES),
        ("mouse", MOUSE_NAMES),
        ("badger", BADGER_NAMES),
    ]
    animal_type, names = rng.choice(pool)
    options = [n for n in names if n != avoid]
    return rng.choice(options), animal_type


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.material and not MATERIALS[args.material].ash_sensitive:
        raise StoryError(explain_rejection(MATERIALS[args.material]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.craft is None or combo[0] == args.craft)
        and (args.material is None or combo[1] == args.material)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    craft_id, material_id = rng.choice(sorted(combos))
    finish_id = args.finish or rng.choice(sorted(FINISHES))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    relation = args.relation or rng.choice(RELATIONS)
    trait = args.trait or rng.choice(TRAITS)

    instigator, instigator_type = pick_animal(rng)
    cautioner, cautioner_type = pick_animal(rng, avoid=instigator)
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        craft=craft_id,
        material=material_id,
        finish=finish_id,
        response=response_id,
        instigator=instigator,
        instigator_type=instigator_type,
        cautioner=cautioner,
        cautioner_type=cautioner_type,
        helper_name="Greta",
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.craft not in CRAFTS:
        raise StoryError(f"(Unknown craft: {params.craft})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.finish not in FINISHES:
        raise StoryError(f"(Unknown finish: {params.finish})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not ash_risk(MATERIALS[params.material]):
        raise StoryError(explain_rejection(MATERIALS[params.material]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        craft_cfg=CRAFTS[params.craft],
        material_cfg=MATERIALS[params.material],
        finish_cfg=FINISHES[params.finish],
        response_cfg=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_type=params.instigator_type,
        cautioner=params.cautioner,
        cautioner_type=params.cautioner_type,
        helper_name=params.helper_name,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (craft, material) combos:\n")
        for craft_id, material_id in combos:
            print(f"  {craft_id:9} {material_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.craft} with {p.material} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    craft_cfg: Craft,
    material_cfg: Material,
    finish_cfg: Finish,
    response_cfg: Response,
    *,
    instigator: str = "Pip",
    instigator_type: str = "fox",
    cautioner: str = "Moss",
    cautioner_type: str = "rabbit",
    helper_name: str = "Greta",
    trait: str = "careful",
    relation: str = "friends",
    instigator_age: int = 5,
    cautioner_age: int = 6,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_type,
            label=instigator_type,
            traits=["bold"],
            role="instigator",
            age=instigator_age,
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_type,
            label=cautioner_type,
            traits=[trait],
            role="cautioner",
            age=cautioner_age,
            attrs={"relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type="goose",
            label="goose",
            role="helper",
            age=12,
            attrs={},
        )
    )
    craft = world.add(
        Entity(
            id="craft",
            kind="thing",
            type=craft_cfg.id,
            label=craft_cfg.label,
            attrs={"fragility": material_cfg.fragility},
            ash_sensitive=material_cfg.ash_sensitive,
            can_fly=True,
        )
    )

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = 5.0 if trait in CAUTIOUS_TRAITS else 3.0
    world.facts["predicted_fragile"] = 0
    world.facts["relation"] = relation

    scene_setup(world, a, b, craft_cfg, material_cfg)
    desire_dark_finish(world, a)

    world.para()
    tempt_with_ash(world, a)
    warn(world, b, a, material_cfg)

    listened = would_listen(
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        trait=trait,
    )
    if listened:
        back_down(world, a, b, finish_cfg)
        world.para()
        launch(world, craft_cfg, a, b)
        ending_moral(world, a, b)
        outcome = "listened"
    else:
        defy(world, a, b)
        world.para()
        apply_ash(world, craft_cfg, material_cfg)
        launch(world, craft_cfg, a, b)
        quarrel(world, a, b)
        world.para()
        confess(world, a, b)
        repair(world, helper, response_cfg, material_cfg, finish_cfg)
        relaunch_success(world, craft_cfg, a, b, finish_cfg)
        ending_moral(world, a, b)
        outcome = "mended"

    world.facts.update(
        craft_cfg=craft_cfg,
        material_cfg=material_cfg,
        finish_cfg=finish_cfg,
        response_cfg=response_cfg,
        instigator=a,
        cautioner=b,
        helper=helper,
        craft=craft,
        outcome=outcome,
        listened=listened,
        ash_used=craft.meters["ash"] >= THRESHOLD,
        failed_first_launch=craft.meters["dipped"] >= THRESHOLD,
        repaired=craft.meters["repaired"] >= THRESHOLD,
    )
    return world


THEMES = {"sky": "sky"}  # lightweight registry slot for ASP symmetry if needed

CRAFTS = {
    "kite": Craft(
        id="kite",
        label="kite",
        phrase="a small parade kite",
        made_of="stretched over a willow frame",
        flies_as="climbed and tugged at its string like a lively fish",
        launch_line="gave the kite a running start",
        tags={"kite", "flying"},
    ),
    "glider": Craft(
        id="glider",
        label="glider",
        phrase="a hand-sized glider",
        made_of="tied over a narrow reed frame",
        flies_as="sailed straight and smooth over the meadow path",
        launch_line="sent the glider skimming into the wind",
        tags={"glider", "flying"},
    ),
    "pinwheel": Craft(
        id="pinwheel",
        label="pinwheel",
        phrase="a parade pinwheel",
        made_of="fixed to a slim twig handle",
        flies_as="spun so happily that even the daisies seemed to clap",
        launch_line="held the pinwheel up to the wind",
        tags={"pinwheel", "wind"},
    ),
}

MATERIALS = {
    "paper": Material(
        id="paper",
        label="paper wing",
        phrase="thin paper",
        panel_word="skin",
        ash_sensitive=True,
        fragility=2,
        dirty_text="the paper looked smudged and felt weaker at the fold",
        repair_text="a fresh paper panel was pasted in place",
        tags={"paper", "ash"},
    ),
    "leaf_cloth": Material(
        id="leaf_cloth",
        label="leaf-cloth wing",
        phrase="stitched leaf-cloth",
        panel_word="cloth",
        ash_sensitive=True,
        fragility=1,
        dirty_text="the leaf-cloth turned dull and rubbed thin along the seam",
        repair_text="the seam was cleaned and neatly patched",
        tags={"cloth", "ash"},
    ),
    "bark_board": Material(
        id="bark_board",
        label="bark-board wing",
        phrase="light bark-board",
        panel_word="board",
        ash_sensitive=False,
        fragility=0,
        dirty_text="the bark-board only looked dusty for a moment",
        repair_text="the bark-board needed almost no mending",
        tags={"bark"},
    ),
}

FINISHES = {
    "berry_paint": Finish(
        id="berry_paint",
        label="berry paint",
        phrase="berry paint in deep blue swirls",
        bright_text="blue berry curls",
        tags={"paint", "berries"},
    ),
    "flower_dye": Finish(
        id="flower_dye",
        label="flower dye",
        phrase="flower dye in bright gold loops",
        bright_text="gold loops",
        tags={"flowers", "paint"},
    ),
    "ribbon_tail": Finish(
        id="ribbon_tail",
        label="ribbon tail",
        phrase="a ribbon tail with red knots",
        bright_text="red knots",
        tags={"ribbon"},
    ),
}

RESPONSES = {
    "clean_patch": Response(
        id="clean_patch",
        sense=3,
        text="showed them how to brush away the ash, smooth the frame, and patch the weak place with fresh paper",
        qa_text="brushed away the ash and patched the weak wing",
        fail_text="told them only to wave it harder in the wind",
        tags={"repair", "patch"},
    ),
    "wash_redye": Response(
        id="wash_redye",
        sense=3,
        text="dampened a cloth, lifted the ash away, and helped them color the wing again the patient way",
        qa_text="washed the ash off and helped them color the wing again",
        fail_text="told them to keep the dirty wing exactly as it was",
        tags={"repair", "wash"},
    ),
    "blow_on_it": Response(
        id="blow_on_it",
        sense=1,
        text="leaned down and blew at the dusty wing",
        qa_text="only blew on the wing",
        fail_text="only blew on the wing, which did not mend anything",
        tags={"repair"},
    ),
}

FOX_NAMES = ["Pip", "Rusty", "Milo", "Fenn"]
RABBIT_NAMES = ["Moss", "Thimble", "Bramble", "Nettle"]
MOUSE_NAMES = ["Poppy", "Nib", "Tansy", "Clover"]
BADGER_NAMES = ["Hob", "Burr", "Marten", "Rowan"]
TRAITS = ["careful", "steady", "sensible", "patient", "curious", "quick"]
RELATIONS = ["friends", "siblings"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for craft_id in CRAFTS:
        for material_id, material in MATERIALS.items():
            if ash_risk(material):
                combos.append((craft_id, material_id))
    return combos

if __name__ == "__main__":
    main()
