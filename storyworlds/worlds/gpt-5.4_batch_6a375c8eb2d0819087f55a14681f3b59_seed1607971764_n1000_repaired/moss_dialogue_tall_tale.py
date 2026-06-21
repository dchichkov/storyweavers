#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/moss_dialogue_tall_tale.py
====================================================

A standalone story world for a child-facing tall tale about a giant mossy climb,
a boastful promise, a slippery turn, and a safer plan.

Reference premise:
------------------
Two children in an exaggerated, tall-tale countryside spot something important
perched on a giant mossy landmark. One child boasts that climbing it will be
easy. The other child warns that moss is slick. In some variants the warning is
strong enough that they wait for help; in others the climber slips in a harmless
but scary near-miss. A calm grown-up brings the right climbing tool, the item is
retrieved, and the ending image proves the children changed how they handle big
brags and slippery places.

Run it
------
    python storyworlds/worlds/gpt-5.4/moss_dialogue_tall_tale.py
    python storyworlds/worlds/gpt-5.4/moss_dialogue_tall_tale.py --landmark millwheel --tool crate_steps
    python storyworlds/worlds/gpt-5.4/moss_dialogue_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/moss_dialogue_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/moss_dialogue_tall_tale.py --trace
    python storyworlds/worlds/gpt-5.4/moss_dialogue_tall_tale.py --json
    python storyworlds/worlds/gpt-5.4/moss_dialogue_tall_tale.py --verify
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
SENSE_MIN = 2
BRAG_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "uncle": "uncle",
            "aunt": "aunt",
        }.get(self.type, self.type)
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
class Place:
    id: str
    intro: str
    stretch: str
    sky: str
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
class Landmark:
    id: str
    label: str
    the: str
    perch: str
    top_item: str
    item_the: str
    item_phrase: str
    item_use: str
    height: int
    moss: int
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Tool:
    id: str
    label: str
    phrase: str
    reach: int
    grip: int
    sense: int
    setup_text: str
    climb_text: str
    qa_text: str
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


def _r_slip(world: World) -> list[str]:
    climber = world.entities.get("hero")
    landmark = world.entities.get("landmark")
    if climber is None or landmark is None:
        return []
    if climber.meters["climbing"] < THRESHOLD:
        return []
    if landmark.meters["path_secure"] >= THRESHOLD:
        return []
    if landmark.meters["slippery"] < THRESHOLD:
        return []
    sig = ("slip", climber.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    climber.meters["slipped"] += 1
    climber.meters["muddy"] += 1
    climber.memes["fear"] += 1
    partner = world.entities.get("partner")
    if partner is not None:
        partner.memes["fear"] += 1
    return ["__slip__"]


def _r_secure(world: World) -> list[str]:
    tool = world.entities.get("tool")
    landmark = world.entities.get("landmark")
    hero = world.entities.get("hero")
    if tool is None or landmark is None or hero is None:
        return []
    if tool.meters["set"] < THRESHOLD:
        return []
    if landmark.meters["path_secure"] >= THRESHOLD:
        return []
    if tool.attrs.get("reach", 0) < landmark.attrs.get("height", 0):
        return []
    if tool.attrs.get("grip", 0) < landmark.attrs.get("moss", 0):
        return []
    sig = ("secure", tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    landmark.meters["path_secure"] += 1
    hero.memes["confidence"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="secure", tag="physical", apply=_r_secure),
    Rule(name="slip", tag="physical", apply=_r_slip),
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


def tool_fits(tool: Tool, landmark: Landmark) -> bool:
    return tool.reach >= landmark.height and tool.grip >= landmark.moss


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for landmark_id, landmark in LANDMARKS.items():
            for tool_id, tool in TOOLS.items():
                if tool_fits(tool, landmark) and tool.sense >= SENSE_MIN:
                    combos.append((place_id, landmark_id, tool_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_wait(relation: str, hero_age: int, partner_age: int, trait: str) -> bool:
    partner_older = relation == "siblings" and partner_age > hero_age
    authority = initial_caution(trait) + 1.0 + (4.0 if partner_older else 0.0)
    return partner_older and authority > BRAG_INIT


def predict_slip(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["climbing"] += 1
    propagate(sim, narrate=False)
    return {
        "slips": hero.meters["slipped"] >= THRESHOLD,
        "muddy": hero.meters["muddy"] >= THRESHOLD,
    }


def open_tale(world: World, place: Place, hero: Entity, partner: Entity, landmark: Landmark) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"In {place.intro}, things never knew when to stop growing. {place.stretch} "
        f"{place.sky}"
    )
    world.say(
        f"That morning, {hero.id} and {partner.id} spotted {landmark.the}, and up on "
        f"{landmark.perch} sat {landmark.item_the}."
    )
    world.say(
        f'"Land sakes," said {hero.id}, tipping {hero.pronoun("possessive")} chin up. '
        f'"There\'s {landmark.item_the}. We need it for {landmark.item_use}."'
    )


def brag(world: World, hero: Entity, landmark: Landmark) -> None:
    hero.memes["brag"] += 1
    world.say(
        f'"That little old climb?" {hero.id} said. "I could shin up {landmark.the} '
        f"faster than a squirrel can blink."
    )


def warn(world: World, partner: Entity, hero: Entity, helper: Entity, landmark: Landmark) -> None:
    pred = predict_slip(world)
    world.facts["predicted_slip"] = pred["slips"]
    partner.memes["caution"] += 1
    extra = " and that green moss is slicker than butter on a griddle" if pred["slips"] else ""
    world.say(
        f'"Hold your horses," said {partner.id}. "{landmark.The} is high{extra}. '
        f'Let\'s call {helper.label_word} before you go climbing."'
    )


def boast_and_wait(world: World, hero: Entity, partner: Entity, helper: Entity) -> None:
    hero.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f'{hero.id} puffed up for another answer, then looked at {partner.id} and let '
        f"the wind out of the boast. \"All right,\" {hero.pronoun()} said. "
        f'"I can wait long enough to do one smart thing."'
    )
    world.say(
        f"So the two of them hollered for {helper.label_word}, and their voices rolled "
        f"through the fields like wagon wheels on a wooden bridge."
    )


def defy(world: World, hero: Entity, partner: Entity, landmark: Landmark) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"If I wait any longer, {landmark.item_the} will think we forgot it," '
        f"{hero.id} said. Before {partner.id} could answer, {hero.pronoun()} grabbed "
        f"at the side of {landmark.the}."
    )


def climb_bare(world: World, hero: Entity, landmark_ent: Entity, landmark: Landmark) -> None:
    hero.meters["climbing"] += 1
    propagate(world, narrate=False)
    if hero.meters["slipped"] >= THRESHOLD:
        world.say(
            f"The moss gave a greasy wiggle under {hero.id}'s shoes. Down "
            f"{hero.pronoun()} slid, not all the way to next Tuesday, but far enough "
            f"to land on {hero.pronoun('possessive')} bottom in a patch of soft mud "
            f"beside {landmark.the}."
        )
    else:
        world.say(
            f"{hero.id} got one hand on a ledge of {landmark.the}, but the climb still "
            f"felt meaner than it had looked from the ground."
        )
    landmark_ent.meters["rattled"] += 1


def alarm(world: World, partner: Entity, hero: Entity) -> None:
    world.say(
        f'"{hero.id}!" cried {partner.id}. "I told you that moss was up to tricks!"'
    )


def helper_arrives(world: World, helper: Entity, tool: Tool) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"Just then, {helper.label_word.capitalize()} came striding over, carrying "
        f"{tool.phrase} as easily as another grown-up might carry a spoon."
    )
    world.say(
        f'"Nobody wrestles moss bare-handed," said {helper.label_word}. '
        f'"We\'ll do this the sensible way."'
    )


def set_tool(world: World, helper: Entity, tool_ent: Entity, landmark: Landmark, tool: Tool) -> None:
    tool_ent.meters["set"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} {tool.setup_text.format(landmark=landmark.the)}."
    )


def safe_climb(world: World, hero: Entity, partner: Entity, landmark: Landmark, tool: Tool) -> None:
    hero.meters["climbing"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["pride"] += 1
    hero.meters["retrieved"] += 1
    world.say(
        f"With the safe path set, {hero.id} climbed again. This time {hero.pronoun()} "
        f"{tool.climb_text}, reached {landmark.perch}, and lifted down {landmark.item_the}."
    )
    world.say(
        f'"Got it!" {hero.id} shouted. "{landmark.item_phrase[0].upper()}{landmark.item_phrase[1:]} '
        f'and all!"'
    )
    partner.memes["joy"] += 1


def lesson(world: World, hero: Entity, partner: Entity, helper: Entity, landmark: Landmark, tool: Tool) -> None:
    hero.memes["lesson"] += 1
    partner.memes["lesson"] += 1
    hero.memes["gratitude"] += 1
    partner.memes["gratitude"] += 1
    world.say(
        f'{helper.label_word.capitalize()} chuckled and wiped a bit of moss from '
        f'{hero.id}\'s sleeve. "A big brag can start a job," {helper.pronoun()} said, '
        f'"but a good plan finishes it."'
    )
    world.say(
        f'"Next time," said {partner.id}, hugging {landmark.item_the}, '
        f'"we ask for {tool.label} before we ask trouble for a dance."'
    )
    world.say(
        f'{hero.id} nodded. "Deal," {hero.pronoun()} said. "I like tall climbs better '
        f'when they have honest steps."'
    )


def ending(world: World, place: Place, hero: Entity, partner: Entity, landmark: Landmark) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"By evening, {landmark.item_the} was back where it belonged for {landmark.item_use}, "
        f"and {landmark.the} still glowed green in the sun."
    )
    world.say(
        f"But now, whenever {hero.id} and {partner.id} passed it, they tipped their heads "
        f"to the moss, grinned at each other, and went looking for the smart path first."
    )
@dataclass
class StoryParams:
    place: str
    landmark: str
    tool: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    helper: str
    trait: str
    relation: str = "siblings"
    hero_age: int = 5
    partner_age: int = 7
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
    "moss": [
        (
            "What is moss?",
            "Moss is a tiny green plant that grows in soft, velvety patches on rocks, logs, and other damp places. It can make a surface look pretty, but it can also be slippery."
        )
    ],
    "ladder": [
        (
            "Why does a ladder help you climb safely?",
            "A ladder gives your feet and hands steady places to go. That makes it easier to climb without slipping."
        )
    ],
    "rope": [
        (
            "What can a rope do on a climb?",
            "A rope can give you something firm to hold while you move. That extra support helps you keep your balance."
        )
    ],
    "stump": [
        (
            "What is a stump?",
            "A stump is the part of a tree trunk left behind after the tree is cut down or falls. Some stumps are low, but in stories they can be giant."
        )
    ],
    "boulder": [
        (
            "What is a boulder?",
            "A boulder is a very big rock. Big rocks can be hard to climb, especially if they are wet or mossy."
        )
    ],
    "millwheel": [
        (
            "What is a millwheel?",
            "A millwheel is a big wheel that turns with moving water at an old mill. If it is tall and slick, it is not a place for children to climb alone."
        )
    ],
}

KNOWLEDGE_ORDER = ["moss", "stump", "boulder", "millwheel", "ladder", "rope"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    landmark = f["landmark_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a child-friendly tall tale with dialogue about two children and {landmark.the}. '
        f'Include the word "moss".'
    )
    if outcome == "waited":
        return [
            base,
            f"Tell a tall-tale story where {hero.id} wants to climb for {landmark.item_the}, but listens when {partner.id} warns that the moss is slick and waits for help.",
            f"Write a story with lively dialogue where a boast is softened by a wiser plan, and {tool.label} helps save the day.",
        ]
    return [
        base,
        f"Tell a tall-tale story where {hero.id} boasts, slips on moss in a harmless near-miss, and then a grown-up brings {tool.label} to fix the problem.",
        f"Write a playful cautionary story with dialogue, a slippery turn, and a safe ending that shows big jobs need better plans than bragging.",
    ]


def pair_noun(hero: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and partner.type == "boy":
            return "two brothers"
        if hero.type == "girl" and partner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    helper = f["helper"]
    landmark = f["landmark_cfg"]
    tool = f["tool_cfg"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, partner, relation)}, {hero.id} and {partner.id}, and {helper.label_word} who helps them. They are trying to get {landmark.item_the} down from {landmark.the}."
        ),
        (
            f"Why did {hero.id} want to climb {landmark.the}?",
            f"{hero.id} wanted to bring down {landmark.item_the} because it was needed for {landmark.item_use}. That need is what made the boast feel urgent."
        ),
        (
            f"What warning did {partner.id} give?",
            f"{partner.id} warned that the moss on {landmark.the} was slick and that they should call {helper.label_word} first. The warning came from seeing the climb was too risky to do bare-handed."
        ),
    ]
    if f["outcome"] == "waited":
        qa.append(
            (
                f"What did {hero.id} do after the warning?",
                f"{hero.id} stopped boasting and agreed to wait for help. That choice kept the scary part from happening at all."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} tried to climb without help?",
                f"{hero.id} slipped because the moss was slick and there was no safe path yet. The fall only dropped {hero.pronoun('object')} into soft mud, but it proved the warning was right."
            )
        )
    qa.append(
        (
            f"How did {helper.label_word} solve the problem?",
            f"{helper.label_word.capitalize()} {tool.qa_text}. That gave {hero.id} a steady way to climb and reach {landmark.item_the} safely."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {landmark.item_the} back in use for {landmark.item_use}, and the children choosing the smart path first. The ending shows they changed how they think about big slippery climbs."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["landmark_cfg"].tags) | set(f["tool_cfg"].tags)
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(tool: Tool, landmark: Landmark) -> str:
    if tool.sense < SENSE_MIN:
        return (
            f"(No story: {tool.label} is known in the world, but it is too flimsy or silly for a careful tall tale here. "
            f"Pick a safer tool like orchard_ladder, rope_hook, or cleat_ladder.)"
        )
    if tool.reach < landmark.height:
        return (
            f"(No story: {tool.label} cannot reach {landmark.the}. The climb is too tall for that tool.)"
        )
    if tool.grip < landmark.moss:
        return (
            f"(No story: {tool.label} does not have enough grip for the slick moss on {landmark.the}.)"
        )
    return "(No story: that tool-landmark pair is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    return "waited" if would_wait(params.relation, params.hero_age, params.partner_age, params.trait) else "slipped_then_fixed"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
fits(Tool, Landmark) :- tool(Tool), landmark(Landmark),
                        reach(Tool, R), height(Landmark, H), R >= H,
                        grip(Tool, G), moss(Landmark, M), G >= M.
sensible(Tool) :- tool(Tool), sense(Tool, S), sense_min(Min), S >= Min.
valid(Place, Landmark, Tool) :- place(Place), landmark(Landmark), tool(Tool),
                                fits(Tool, Landmark), sensible(Tool).

% --- outcome model ---------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

partner_older :- relation(siblings), hero_age(H), partner_age(P), P > H.
bonus(4)      :- partner_older.
bonus(0)      :- not partner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
waited        :- partner_older, authority(A), brag_init(BR), A > BR.

outcome(waited) :- waited.
outcome(slipped_then_fixed) :- not waited.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for landmark_id, landmark in LANDMARKS.items():
        lines.append(asp.fact("landmark", landmark_id))
        lines.append(asp.fact("height", landmark_id, landmark.height))
        lines.append(asp.fact("moss", landmark_id, landmark.moss))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        lines.append(asp.fact("grip", tool_id, tool.grip))
        lines.append(asp.fact("sense", tool_id, tool.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("brag_init", int(BRAG_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("partner_age", params.partner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        place="cedar_holler",
        landmark="boulder",
        tool="orchard_ladder",
        hero="June",
        hero_gender="girl",
        partner="Buck",
        partner_gender="boy",
        helper="uncle",
        trait="careful",
        relation="siblings",
        hero_age=5,
        partner_age=7,
    ),
    StoryParams(
        place="river_bend",
        landmark="millwheel",
        tool="rope_hook",
        hero="Eli",
        hero_gender="boy",
        partner="Mabel",
        partner_gender="girl",
        helper="aunt",
        trait="curious",
        relation="friends",
        hero_age=6,
        partner_age=6,
    ),
    StoryParams(
        place="sunflower_flat",
        landmark="stump",
        tool="cleat_ladder",
        hero="Pearl",
        hero_gender="girl",
        partner="Ruth",
        partner_gender="girl",
        helper="father",
        trait="steady",
        relation="siblings",
        hero_age=4,
        partner_age=7,
    ),
    StoryParams(
        place="river_bend",
        landmark="boulder",
        tool="rope_hook",
        hero="Cal",
        hero_gender="boy",
        partner="Dora",
        partner_gender="girl",
        helper="uncle",
        trait="sensible",
        relation="friends",
        hero_age=6,
        partner_age=5,
    ),
    StoryParams(
        place="cedar_holler",
        landmark="millwheel",
        tool="cleat_ladder",
        hero="Minnie",
        hero_gender="girl",
        partner="Bo",
        partner_gender="boy",
        helper="mother",
        trait="cautious",
        relation="siblings",
        hero_age=5,
        partner_age=8,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tall tale about a mossy climb, dialogue, and the smart path."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--landmark", choices=LANDMARKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=["mother", "father", "uncle", "aunt"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.landmark and args.tool:
        landmark = LANDMARKS[args.landmark]
        tool = TOOLS[args.tool]
        if not (tool_fits(tool, landmark) and tool.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(tool, landmark))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        landmark = LANDMARKS[args.landmark] if args.landmark else next(iter(LANDMARKS.values()))
        raise StoryError(explain_rejection(TOOLS[args.tool], landmark))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.landmark is None or combo[1] == args.landmark)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, landmark, tool = rng.choice(sorted(combos))
    hero, hero_gender = _pick_kid(rng)
    partner, partner_gender = _pick_kid(rng, avoid=hero)
    helper = args.helper or rng.choice(["mother", "father", "uncle", "aunt"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    hero_age, partner_age = rng.sample([4, 5, 6, 7, 8], 2)
    return StoryParams(
        place=place,
        landmark=landmark,
        tool=tool,
        hero=hero,
        hero_gender=hero_gender,
        partner=partner,
        partner_gender=partner_gender,
        helper=helper,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        partner_age=partner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.landmark not in LANDMARKS:
        raise StoryError(f"(Unknown landmark: {params.landmark})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.helper not in {"mother", "father", "uncle", "aunt"}:
        raise StoryError(f"(Unknown helper: {params.helper})")

    place = PLACES[params.place]
    landmark = LANDMARKS[params.landmark]
    tool = TOOLS[params.tool]
    if not (tool_fits(tool, landmark) and tool.sense >= SENSE_MIN):
        raise StoryError(explain_rejection(tool, landmark))

    world = tell(
        place=place,
        landmark=landmark,
        tool=tool,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        helper_type=params.helper,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        partner_age=params.partner_age,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {tool.id for tool in sensible_tools()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible tools match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(120):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible tools: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, landmark, tool) combos:\n")
        for place, landmark, tool in combos:
            print(f"  {place:15} {landmark:10} {tool}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.partner}: {p.landmark} at {p.place} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    place: Place,
    landmark: Landmark,
    tool: Tool,
    hero_name: str = "June",
    hero_gender: str = "girl",
    partner_name: str = "Buck",
    partner_gender: str = "boy",
    helper_type: str = "uncle",
    trait: str = "careful",
    relation: str = "siblings",
    hero_age: int = 5,
    partner_age: int = 7,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        age=hero_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        age=partner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
    ))
    landmark_ent = world.add(Entity(
        id="landmark",
        type="landmark",
        label=landmark.label,
        attrs={"height": landmark.height, "moss": landmark.moss},
    ))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        attrs={"reach": tool.reach, "grip": tool.grip},
    ))

    hero.memes["brag_power"] = BRAG_INIT
    partner.memes["caution"] = initial_caution(trait)
    landmark_ent.meters["slippery"] = float(landmark.moss)
    landmark_ent.meters["path_secure"] = 0.0
    tool_ent.meters["set"] = 0.0
    hero.meters["climbing"] = 0.0
    hero.meters["slipped"] = 0.0
    hero.meters["muddy"] = 0.0
    hero.meters["retrieved"] = 0.0

    open_tale(world, place, hero, partner, landmark)
    world.para()
    brag(world, hero, landmark)
    warn(world, partner, hero, helper, landmark)

    waited = would_wait(relation, hero_age, partner_age, trait)
    world.para()
    if waited:
        boast_and_wait(world, hero, partner, helper)
    else:
        defy(world, hero, partner, landmark)
        climb_bare(world, hero, landmark_ent, landmark)
        alarm(world, partner, hero)

    world.para()
    helper_arrives(world, helper, tool)
    set_tool(world, helper, tool_ent, landmark, tool)
    safe_climb(world, hero, partner, landmark, tool)

    world.para()
    lesson(world, hero, partner, helper, landmark, tool)
    ending(world, place, hero, partner, landmark)

    outcome = "waited" if waited else "slipped_then_fixed"
    world.facts.update(
        place=place,
        landmark_cfg=landmark,
        tool_cfg=tool,
        hero=hero,
        partner=partner,
        helper=helper,
        landmark=landmark_ent,
        tool=tool_ent,
        outcome=outcome,
        relation=relation,
        slipped=hero.meters["slipped"] >= THRESHOLD,
        retrieved=hero.meters["retrieved"] >= THRESHOLD,
        waited=waited,
    )
    return world


PLACES = {
    "cedar_holler": Place(
        id="cedar_holler",
        intro="Cedar Holler",
        stretch="The pumpkins were said to grow as wide as wagons, and the fence posts stood so tall they could scratch lazy clouds.",
        sky="Even the creek talked big there, bragging over the stones all afternoon.",
        tags={"field"},
    ),
    "river_bend": Place(
        id="river_bend",
        intro="River Bend",
        stretch="The willows leaned so far over the bank that they looked like green giants whispering secrets to the fish.",
        sky="When the wind came by, it bent the reeds in long laughing waves.",
        tags={"river"},
    ),
    "sunflower_flat": Place(
        id="sunflower_flat",
        intro="Sunflower Flat",
        stretch="The sunflowers were taller than porch roofs, and the crows needed nearly a whole morning to flap across one field.",
        sky="The air smelled warm enough to butter a biscuit all by itself.",
        tags={"farm"},
    ),
}

LANDMARKS = {
    "stump": Landmark(
        id="stump",
        label="mossy stump",
        the="the mossy stump",
        perch="its broad top",
        top_item="lunch pail",
        item_the="the tin lunch pail",
        item_phrase="the tin lunch pail",
        item_use="noon lunch under the shade tree",
        height=1,
        moss=1,
        tags={"moss", "stump"},
    ),
    "boulder": Landmark(
        id="boulder",
        label="mossy boulder",
        the="the mossy boulder",
        perch="its high round shoulder",
        top_item="red kite",
        item_the="the red kite",
        item_phrase="the red kite",
        item_use="afternoon flying before the breeze went lazy",
        height=2,
        moss=2,
        tags={"moss", "boulder"},
    ),
    "millwheel": Landmark(
        id="millwheel",
        label="mossy millwheel",
        the="the mossy millwheel",
        perch="the top spoke",
        top_item="fishing hat",
        item_the="the fishing hat",
        item_phrase="the fishing hat",
        item_use="the evening trip to the river bank",
        height=3,
        moss=2,
        tags={"moss", "millwheel"},
    ),
}

TOOLS = {
    "crate_steps": Tool(
        id="crate_steps",
        label="crate steps",
        phrase="two nailed-together crate steps",
        reach=1,
        grip=1,
        sense=1,
        setup_text="set the crate steps by {landmark}, but even from the ground it was plain they were too short and too tippy for a climb like that",
        climb_text="went slowly and carefully",
        qa_text="brought short crate steps",
        tags={"steps"},
    ),
    "orchard_ladder": Tool(
        id="orchard_ladder",
        label="orchard ladder",
        phrase="an orchard ladder with wide wooden rungs",
        reach=2,
        grip=2,
        sense=2,
        setup_text="leaned the orchard ladder against {landmark} and pressed each rung firm into place",
        climb_text="put one foot on each wide rung and kept both hands steady",
        qa_text="leaned an orchard ladder against the climb and held it steady",
        tags={"ladder"},
    ),
    "rope_hook": Tool(
        id="rope_hook",
        label="rope-and-hook rig",
        phrase="a rope-and-hook rig coiled over one shoulder",
        reach=3,
        grip=2,
        sense=3,
        setup_text="flipped the hook over the far side of {landmark}, pulled the rope snug, and made a safe line all the way up",
        climb_text="used the taut rope for balance and planted each foot where it belonged",
        qa_text="secured a rope-and-hook rig to make a safe climbing line",
        tags={"rope"},
    ),
    "cleat_ladder": Tool(
        id="cleat_ladder",
        label="cleated ladder",
        phrase="a cleated ladder with bark-gripping feet",
        reach=3,
        grip=3,
        sense=3,
        setup_text="planted the cleated ladder against {landmark} so firmly it looked rooted there",
        climb_text="trusted the bark-gripping feet and climbed as neat as a cat on a fence rail",
        qa_text="set a cleated ladder with grip enough for the slick moss",
        tags={"ladder"},
    ),
}

GIRL_NAMES = ["June", "Mabel", "Nell", "Dora", "Ada", "Ruth", "Pearl", "Minnie"]
BOY_NAMES = ["Buck", "Eli", "Jeb", "Tom", "Hank", "Cal", "Will", "Bo"]
TRAITS = ["careful", "cautious", "steady", "sensible", "curious", "cheerful"]

if __name__ == "__main__":
    main()
