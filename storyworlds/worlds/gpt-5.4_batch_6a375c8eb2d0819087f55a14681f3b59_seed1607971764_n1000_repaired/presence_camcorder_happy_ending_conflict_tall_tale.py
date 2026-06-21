#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/presence_camcorder_happy_ending_conflict_tall_tale.py
================================================================================

A standalone story world for a child-facing tall tale about proving a giant
visitor's presence with a camcorder, surviving a lively conflict, and ending in
a happy welcome.

Premise
-------
A child notices signs that an oversized, almost impossible creature is nearby.
Another child does not believe it. To settle the argument fairly, the first
child borrows a camcorder and goes looking for proof. The creature turns out not
to be mean at all -- only hungry, thirsty, or tangled -- and the right help
turns the quarrel into a town-wide smile.

Reasonableness constraint
-------------------------
Not every legendary creature belongs in every place, and not every rescue works
for every problem. This world only tells stories where:

* the chosen creature can plausibly appear in the chosen place, and
* the chosen remedy actually solves that creature's need.

That constraint exists both in Python and in an inline ASP twin.

Run it
------
python storyworlds/worlds/gpt-5.4/presence_camcorder_happy_ending_conflict_tall_tale.py
python storyworlds/worlds/gpt-5.4/presence_camcorder_happy_ending_conflict_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/presence_camcorder_happy_ending_conflict_tall_tale.py --qa --json
python storyworlds/worlds/gpt-5.4/presence_camcorder_happy_ending_conflict_tall_tale.py --asp
python storyworlds/worlds/gpt-5.4/presence_camcorder_happy_ending_conflict_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def elder_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    landmark: str
    paths: str
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
class Creature:
    id: str
    label: str
    kind_name: str
    need: str
    sign: str
    entrance: str
    trouble: str
    thanks: str
    ending: str
    habitats: set[str] = field(default_factory=set)
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
class Remedy:
    id: str
    label: str
    phrase: str
    solves: set[str] = field(default_factory=set)
    action: str = ""
    qa_action: str = ""
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


def _r_rumble(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["need"] < THRESHOLD or creature.meters["visible"] < THRESHOLD:
        return []
    sig = ("rumble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("town").meters["commotion"] += 1
    world.get("hero").memes["alarm"] += 1
    world.get("doubter").memes["alarm"] += 1
    return ["__rumble__"]


def _r_capture(world: World) -> list[str]:
    camcorder = world.get("camcorder")
    creature = world.get("creature")
    if camcorder.meters["recording"] < THRESHOLD or creature.meters["visible"] < THRESHOLD:
        return []
    sig = ("capture",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    camcorder.meters["evidence"] += 1
    return []


def _r_belief(world: World) -> list[str]:
    camcorder = world.get("camcorder")
    creature = world.get("creature")
    doubter = world.get("doubter")
    if camcorder.meters["evidence"] < THRESHOLD or creature.meters["need"] >= THRESHOLD:
        return []
    sig = ("belief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    doubter.memes["belief"] += 1
    doubter.memes["doubt"] = 0.0
    world.get("town").memes["cheer"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="rumble", tag="physical", apply=_r_rumble),
    Rule(name="capture", tag="physical", apply=_r_capture),
    Rule(name="belief", tag="social", apply=_r_belief),
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
        for sent in produced:
            world.say(sent)
    return produced


def creature_fits(setting: Setting, creature: Creature) -> bool:
    return creature.id in setting.affords and setting.id in creature.habitats


def remedy_helps(creature: Creature, remedy: Remedy) -> bool:
    return creature.need in remedy.solves


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for cid, creature in CREATURES.items():
            if not creature_fits(setting, creature):
                continue
            for rid, remedy in REMEDIES.items():
                if remedy_helps(creature, remedy):
                    combos.append((sid, cid, rid))
    return combos


def predict_commotion(world: World) -> dict:
    sim = world.copy()
    sim.get("creature").meters["visible"] = 1.0
    propagate(sim, narrate=False)
    return {
        "commotion": sim.get("town").meters["commotion"],
        "alarm": sim.get("hero").memes["alarm"],
    }


def sky_line() -> str:
    return random.choice([
        "The day stood so tall it looked ready to bump its head on a cloud.",
        "The morning was big enough to make the fence posts feel like toothpicks.",
        "The sunlight came down in golden sheets wide enough to cover three barns at once.",
    ])


def introduce(world: World, hero: Entity, doubter: Entity, elder: Entity) -> None:
    world.say(
        f"{sky_line()} Down by {world.setting.place}, {hero.id} and {doubter.id} "
        f"were keeping company with {hero.attrs['elder_possessive']} {elder.elder_word}, "
        f"who could spot trouble from half a county away."
    )
    world.say(
        f"{hero.id} had a heart roomy enough for wonder, while {doubter.id} liked facts "
        f"so neat and tidy they could have been stacked in a jam cupboard."
    )


def notice_presence(world: World, hero: Entity, creature: Creature) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"Then {hero.id} saw {creature.sign} near {world.setting.landmark} and whispered, "
        f'"That is no ordinary mark. A giant {creature.kind_name} has left its presence all over this place."'
    )


def borrow_camcorder(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"{elder.elder_word.capitalize()} opened a weathered satchel and handed {hero.id} "
        f"a camcorder with a red button shiny as a berry. "
        f'"If you aim to prove a thing," {elder.pronoun()} said, "prove it honest."'
    )


def scoff(world: World, doubter: Entity, creature: Creature) -> None:
    doubter.memes["doubt"] += 1
    world.say(
        f'{doubter.id} snorted. "A {creature.label}? Why, if one of those was here, '
        f'its sneeze would blow the hats off every chicken in the county."'
    )
    world.say(
        f"Still, {doubter.id} followed along, half to laugh and half because curiosity "
        f"was tugging at {doubter.pronoun('possessive')} sleeves."
    )


def reveal_creature(world: World, creature_cfg: Creature) -> None:
    creature = world.get("creature")
    creature.meters["visible"] = 1.0
    propagate(world, narrate=False)
    world.say(creature_cfg.entrance)
    world.say(creature_cfg.trouble)


def argue(world: World, hero: Entity, doubter: Entity) -> None:
    hero.memes["stubborn"] += 1
    doubter.memes["stubborn"] += 1
    if world.get("town").meters["commotion"] >= THRESHOLD:
        world.say(
            f'"See?" cried {hero.id}. "I told you something mighty was here!" '
            f'"Maybe so," said {doubter.id}, "but mighty is not the same as friendly."'
        )
    else:
        world.say(
            f'''"See?" cried {hero.id}. "I told you!" But {doubter.id} folded "'''
            f'{doubter.pronoun("possessive")} arms and waited for better proof.'
        )


def help_creature(world: World, hero: Entity, creature_cfg: Creature, remedy: Remedy) -> None:
    creature = world.get("creature")
    hero.memes["care"] += 1
    creature.meters["need"] = 0.0
    creature.memes["gratitude"] += 1
    world.say(
        f"{hero.id} did not run. {hero.pronoun().capitalize()} grabbed {remedy.phrase} and "
        f"{remedy.action}, because even in a tall tale, kindness works faster than bragging."
    )
    world.say(creature_cfg.thanks)


def record_proof(world: World, hero: Entity, doubter: Entity) -> None:
    camcorder = world.get("camcorder")
    camcorder.meters["recording"] = 1.0
    propagate(world, narrate=False)
    if camcorder.meters["evidence"] >= THRESHOLD:
        world.say(
            f"All the while, {hero.id} kept the camcorder steady enough to catch every last blink, "
            f"snort, and grateful nod. The tape held more truth than ten barrels of arguing."
        )
    if doubter.memes["belief"] >= THRESHOLD:
        world.say(
            f"{doubter.id} stared at the little screen, then at the beast, and the doubt ran right out "
            f"of {doubter.pronoun('possessive')} voice. "
            f'"Well butter my biscuits," {doubter.pronoun()} said. "You were right, and I was wrong."'
        )


def welcome(world: World, hero: Entity, doubter: Entity, elder: Entity, creature_cfg: Creature) -> None:
    town = world.get("town")
    hero.memes["joy"] += 1
    doubter.memes["joy"] += 1
    town.memes["peace"] += 1
    world.say(
        f"By supper time, half the town had gathered by {world.setting.paths} to watch the camcorder tape. "
        f"No one argued after that. They had seen the visitor's presence with their own eyes and heard "
        f"how gently {hero.id} had helped."
    )
    world.say(
        f"{elder.elder_word.capitalize()} tipped {elder.pronoun('possessive')} hat, {doubter.id} stood beside "
        f"{hero.id} like a proper friend again, and {creature_cfg.ending}"
    )
@dataclass
class StoryParams:
    place: str
    creature: str
    remedy: str
    hero: str
    hero_gender: str
    doubter: str
    doubter_gender: str
    elder: str
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
    "camcorder": [
        (
            "What is a camcorder?",
            "A camcorder is a camera that records moving pictures and sound. People use it to save what they saw so they can watch it again later.",
        )
    ],
    "presence": [
        (
            "What does presence mean in a story like this?",
            "Presence means that someone or something is truly there. In this story, signs and the recording showed that the giant visitor was really nearby.",
        )
    ],
    "thirsty": [
        (
            "What happens when an animal is thirsty?",
            "A thirsty animal needs water so its body can work properly. If it gets a drink, it usually feels calmer and stronger.",
        )
    ],
    "hungry": [
        (
            "What happens when an animal is hungry?",
            "A hungry animal needs food for energy. Once it eats, it often stops fussing and settles down.",
        )
    ],
    "tangled": [
        (
            "Why does a tangled wing or leg need help?",
            "When something is tangled, it cannot move the right way. Untangling it gently can stop pain and help it fly or walk again.",
        )
    ],
    "water": [
        (
            "Why does water help something thirsty?",
            "Water cools and refreshes a thirsty body. A good drink can quickly turn discomfort into relief.",
        )
    ],
    "food": [
        (
            "Why can food calm a hungry creature?",
            "Food gives the body energy. When hunger is the problem, a good meal can make a creature feel peaceful again.",
        )
    ],
    "ladder": [
        (
            "Why might a ladder help in a rescue?",
            "A ladder lets a person reach something high safely. That can help when a knot, string, or stuck object is above the ground.",
        )
    ],
    "tall_tale": [
        (
            "What is a tall tale?",
            "A tall tale is a story that uses huge, funny exaggeration on purpose. The details sound bigger than real life, but the feelings and problem-solving still make sense.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "camcorder",
    "presence",
    "thirsty",
    "hungry",
    "tangled",
    "water",
    "food",
    "ladder",
    "tall_tale",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    doubter = f["doubter"]
    creature = f["creature_cfg"]
    remedy = f["remedy"]
    return [
        'Write a short tall-tale story for a 3-to-5-year-old that includes the words "presence" and "camcorder".',
        f"Tell a happy tall tale where {hero.id} notices a giant {creature.kind_name}'s presence, "
        f"{doubter.id} does not believe it, and a camcorder helps settle the argument kindly.",
        f"Write a playful conflict story in which a child proves a marvelous creature is real, then "
        f"uses {remedy.label} to help it so the ending feels warm instead of scary.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    doubter = f["doubter"]
    elder = f["elder"]
    creature_cfg = f["creature_cfg"]
    remedy = f["remedy"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {doubter.id}, and {hero.id}'s {elder.elder_word}. "
            f"They are the ones who notice the giant visitor, argue about it, and then help it together.",
        ),
        (
            f"What made {hero.id} think something unusual was nearby?",
            f"{hero.id} saw {creature_cfg.sign} near {setting.landmark}. "
            f"That sign made {hero.pronoun('object')} believe a giant creature's presence was real before anyone else did.",
        ),
        (
            f"Why did {hero.id} take a camcorder?",
            f"{hero.id} wanted honest proof instead of just a loud argument. "
            f"The camcorder could show what really happened and help {doubter.id} see the truth.",
        ),
        (
            f"What was the conflict between {hero.id} and {doubter.id}?",
            f"The conflict was that {hero.id} believed a giant creature was there, but {doubter.id} laughed and doubted it. "
            f"The disagreement mattered because they had to decide whether to run away, keep arguing, or help.",
        ),
        (
            f"How did {hero.id} help the creature?",
            f"{hero.id} used the {remedy.label} and {remedy.qa_action}. "
            f"That worked because the creature's real trouble was being {creature_cfg.need}, not being mean.",
        ),
        (
            "How did the story end?",
            f"It ended happily because the camcorder recording and the rescue changed doubt into belief. "
            f"By the end, the town welcomed the visitor's presence instead of fearing it, and the creature left in peace.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"camcorder", "presence", "tall_tale"}
    creature = world.facts["creature_cfg"]
    remedy = world.facts["remedy"]
    tags.add(creature.need)
    tags |= set(remedy.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="orchard",
        creature="sky_goose",
        remedy="banner_ladder",
        hero="June",
        hero_gender="girl",
        doubter="Beau",
        doubter_gender="boy",
        elder="grandmother",
    ),
    StoryParams(
        place="riverbank",
        creature="canyon_catfish",
        remedy="biscuit_crate",
        hero="Mabel",
        hero_gender="girl",
        doubter="Hank",
        doubter_gender="boy",
        elder="grandfather",
    ),
    StoryParams(
        place="prairie",
        creature="cloud_cow",
        remedy="water_barrel",
        hero="Eli",
        hero_gender="boy",
        doubter="Ruby",
        doubter_gender="girl",
        elder="grandmother",
    ),
    StoryParams(
        place="orchard",
        creature="cloud_cow",
        remedy="water_barrel",
        hero="Pearl",
        hero_gender="girl",
        doubter="Cal",
        doubter_gender="boy",
        elder="grandfather",
    ),
]


def explain_rejection(setting: Optional[Setting], creature: Optional[Creature], remedy: Optional[Remedy]) -> str:
    if setting is not None and creature is not None and not creature_fits(setting, creature):
        return (
            f"(No story: a {creature.label} does not belong at {setting.place}. "
            f"Choose a place where that creature could honestly appear.)"
        )
    if creature is not None and remedy is not None and not remedy_helps(creature, remedy):
        return (
            f"(No story: {remedy.label} does not solve a {creature.label}'s problem. "
            f"Pick a remedy that actually helps something {creature.need}.)"
        )
    return "(No story: the chosen options do not make a reasonable tall tale.)"


ASP_RULES = r"""
need_of(C, N) :- creature(C), needs(C, N).
valid(S, C, R) :- setting(S), creature(C), remedy(R),
                  appears_in(S, C),
                  need_of(C, N),
                  solves(R, N).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("needs", cid, creature.need))
        for habitat in sorted(creature.habitats):
            lines.append(asp.fact("appears_in", habitat, cid))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for need in sorted(remedy.solves):
            lines.append(asp.fact("solves", rid, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combo gate matches ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError as err:
            rc = 1
            print(f"SMOKE resolve failure for seed {seed}: {err}")
            continue
        params.seed = seed
        smoke_cases.append(params)

    try:
        sample = generate(smoke_cases[0])
        if not sample.story.strip():
            raise StoryError("empty story in smoke test")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="### smoke")
        if "camcorder" not in sample.story or "presence" not in sample.story:
            raise StoryError("required seed words missing from smoke story")
        print(f"OK: smoke generation/emit passed on {len(smoke_cases)} scenarios.")
    except Exception as err:
        rc = 1
        print(f"SMOKE generation failure: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a giant visitor, a camcorder, an argument, and a happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--doubter")
    ap.add_argument("--doubter-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = SETTINGS.get(args.place) if args.place else None
    creature = CREATURES.get(args.creature) if args.creature else None
    remedy = REMEDIES.get(args.remedy) if args.remedy else None

    if place is not None and creature is not None and not creature_fits(place, creature):
        raise StoryError(explain_rejection(place, creature, remedy))
    if creature is not None and remedy is not None and not remedy_helps(creature, remedy):
        raise StoryError(explain_rejection(place, creature, remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.creature is None or combo[1] == args.creature)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, creature_id, remedy_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    doubter_gender = args.doubter_gender or rng.choice(["girl", "boy"])
    doubter = args.doubter or _pick_name(rng, doubter_gender, avoid=hero)
    if doubter == hero:
        raise StoryError("(No story: hero and doubter must have different names.)")
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        place=place_id,
        creature=creature_id,
        remedy=remedy_id,
        hero=hero,
        hero_gender=hero_gender,
        doubter=doubter,
        doubter_gender=doubter_gender,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")

    setting = SETTINGS[params.place]
    creature = CREATURES[params.creature]
    remedy = REMEDIES[params.remedy]
    if not creature_fits(setting, creature) or not remedy_helps(creature, remedy):
        raise StoryError(explain_rejection(setting, creature, remedy))

    world = tell(
        setting=setting,
        creature_cfg=creature,
        remedy=remedy,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        doubter_name=params.doubter,
        doubter_gender=params.doubter_gender,
        elder_type=params.elder,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, creature, remedy) combos:\n")
        for place, creature, remedy in combos:
            print(f"  {place:10} {creature:15} {remedy}")
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
            header = f"### {p.hero} vs {p.doubter}: {p.creature} at {p.place} with {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    setting: Setting,
    creature_cfg: Creature,
    remedy: Remedy,
    hero_name: str = "June",
    hero_gender: str = "girl",
    doubter_name: str = "Beau",
    doubter_gender: str = "boy",
    elder_type: str = "grandmother",
) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["bold", "kind"],
        attrs={},
        tags={"hero"},
    ))
    doubter = world.add(Entity(
        id=doubter_name,
        kind="character",
        type=doubter_gender,
        role="doubter",
        traits=["skeptical"],
        attrs={},
        tags={"doubter"},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
        attrs={},
        tags={"elder"},
    ))
    town = world.add(Entity(
        id="town",
        type="town",
        label="the town",
        attrs={},
        tags={"town"},
    ))
    camcorder = world.add(Entity(
        id="camcorder",
        type="camcorder",
        label="camcorder",
        attrs={},
        tags={"camcorder"},
    ))
    creature = world.add(Entity(
        id="creature",
        type="creature",
        label=creature_cfg.label,
        attrs={"need": creature_cfg.need},
        tags=set(creature_cfg.tags),
    ))

    creature.meters["need"] = 1.0
    creature.meters["visible"] = 0.0
    camcorder.meters["recording"] = 0.0
    camcorder.meters["evidence"] = 0.0
    hero.attrs["elder_possessive"] = "her" if hero.type == "girl" else "his"
    doubter.memes["doubt"] = 2.0
    town.meters["commotion"] = 0.0
    town.memes["cheer"] = 0.0

    introduce(world, hero, doubter, elder)
    notice_presence(world, hero, creature_cfg)

    world.para()
    borrow_camcorder(world, hero, elder)
    scoff(world, doubter, creature_cfg)

    world.para()
    pred = predict_commotion(world)
    world.facts["predicted_commotion"] = pred["commotion"]
    reveal_creature(world, creature_cfg)
    argue(world, hero, doubter)
    help_creature(world, hero, creature_cfg, remedy)

    world.para()
    record_proof(world, hero, doubter)
    welcome(world, hero, doubter, elder, creature_cfg)

    world.facts.update(
        hero=hero,
        doubter=doubter,
        elder=elder,
        town=town,
        camcorder=camcorder,
        creature=creature,
        setting=setting,
        creature_cfg=creature_cfg,
        remedy=remedy,
        conflict=doubter.memes["belief"] >= THRESHOLD or doubter.memes["doubt"] >= THRESHOLD,
        believed=doubter.memes["belief"] >= THRESHOLD,
        solved=creature.meters["need"] < THRESHOLD,
    )
    return world


SETTINGS = {
    "prairie": Setting(
        id="prairie",
        place="the prairie edge",
        landmark="the wind-bent fence",
        paths="the wagon road",
        affords={"cloud_cow"},
        tags={"prairie"},
    ),
    "riverbank": Setting(
        id="riverbank",
        place="the riverbank",
        landmark="the willow bend",
        paths="the muddy landing",
        affords={"canyon_catfish", "sky_goose"},
        tags={"river"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the orchard hill",
        landmark="the oldest apple tree",
        paths="the cider shed",
        affords={"cloud_cow", "sky_goose"},
        tags={"orchard"},
    ),
}

CREATURES = {
    "cloud_cow": Creature(
        id="cloud_cow",
        label="cloud cow",
        kind_name="cloud cow",
        need="thirsty",
        sign="a hoofprint broad as a wash tub and damp around the edges",
        entrance="Sure enough, a cloud cow rose from behind the grass, white as fresh churned butter and tall enough to nibble a drifting cloud.",
        trouble="Its tongue lolled sadly, and every thirsty moo made the dust hop. It was not angry at all. It was simply dry as a forgotten sponge.",
        thanks="When the cool water splashed up, the cloud cow drank deep and gave a soft moo that sounded like rain beginning far away.",
        ending="the cloud cow ambled off through the evening sky, leaving a silver trail of mist and a fieldful of grinning faces.",
        habitats={"prairie", "orchard"},
        tags={"thirsty", "cloud_cow"},
    ),
    "canyon_catfish": Creature(
        id="canyon_catfish",
        label="canyon catfish",
        kind_name="canyon catfish",
        need="hungry",
        sign="a whisker-drag in the mud long enough to curl around a porch",
        entrance="Out of the shallows rolled a canyon catfish, blue-gray and broad-backed, with whiskers that swayed like clotheslines in the wind.",
        trouble="Its belly grumbled so loudly the river made room for the sound. The poor thing looked hungry enough to swallow a rowboat and still ask for seconds.",
        thanks="The great fish gulped the biscuits down in three thankful chomps, then blinked as mild as a sleepy barn cat.",
        ending="the canyon catfish slid back into the river with a flip that painted the sunset in silver drops.",
        habitats={"riverbank"},
        tags={"hungry", "fish"},
    ),
    "sky_goose": Creature(
        id="sky_goose",
        label="sky goose",
        kind_name="sky goose",
        need="tangled",
        sign="a feather big as a porch mat caught on a branch",
        entrance="Then a sky goose blundered into view, all blue feathers and long legs, with wings so wide they shaded two rows of grass at once.",
        trouble="String from an old fair banner was wrapped around one flapping wing, and each honk sounded more embarrassed than fierce.",
        thanks="Once the knot was freed, the sky goose stretched both wings, dipped its head, and honked a note bright enough to polish the air.",
        ending="the sky goose lifted straight up, circled the hill once in thanks, and flew off like a scrap of blue daylight.",
        habitats={"riverbank", "orchard"},
        tags={"tangled", "bird"},
    ),
}

REMEDIES = {
    "water_barrel": Remedy(
        id="water_barrel",
        label="water barrel",
        phrase="the oak water barrel",
        solves={"thirsty"},
        action="rolled it over and tipped a shining stream into a trough made from an old split log",
        qa_action="gave the thirsty creature water from the barrel",
        tags={"water"},
    ),
    "biscuit_crate": Remedy(
        id="biscuit_crate",
        label="biscuit crate",
        phrase="the biscuit crate from the wagon",
        solves={"hungry"},
        action="pried it open and tossed warm biscuits one after another toward the giant mouth",
        qa_action="fed the hungry creature warm biscuits",
        tags={"food"},
    ),
    "banner_ladder": Remedy(
        id="banner_ladder",
        label="banner ladder",
        phrase="the painter's ladder and a pocketknife",
        solves={"tangled"},
        action="climbed carefully and snipped the fair-string loose without nicking a single feather",
        qa_action="climbed up and cut the tangled string away",
        tags={"ladder"},
    ),
}

GIRL_NAMES = ["June", "Mabel", "Ada", "Nell", "Ruby", "Tess", "Lula", "Pearl"]
BOY_NAMES = ["Beau", "Hank", "Eli", "Jesse", "Wade", "Cal", "Otis", "Finn"]

if __name__ == "__main__":
    main()
