#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/residence_rhyme_foreshadowing_sound_effects_slice_of.py
==================================================================================

A small standalone storyworld about a child in a family residence who wants a
treat from a high shelf, chooses a wobbly way to reach it, and learns a calmer,
safer household habit.

This world aims for a gentle slice-of-life feel while using:
- the word "residence"
- sound effects ("creak", "clink", "thump", "plink")
- foreshadowing (the stool/chair sounds warn what might happen)
- rhyme as a repeated family saying

Run it
------
    python storyworlds/worlds/gpt-5.4/residence_rhyme_foreshadowing_sound_effects_slice_of.py
    python storyworlds/worlds/gpt-5.4/residence_rhyme_foreshadowing_sound_effects_slice_of.py --residence apartment --prize jar_cookies
    python storyworlds/worlds/gpt-5.4/residence_rhyme_foreshadowing_sound_effects_slice_of.py --unsafe rolling_chair   # rejected
    python storyworlds/worlds/gpt-5.4/residence_rhyme_foreshadowing_sound_effects_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/residence_rhyme_foreshadowing_sound_effects_slice_of.py --qa --json
    python storyworlds/worlds/gpt-5.4/residence_rhyme_foreshadowing_sound_effects_slice_of.py --verify
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
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2
BOLDNESS_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    edible: bool = False
    support: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Residence:
    id: str
    label: str
    phrase: str
    kitchen_line: str
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
class Prize:
    id: str
    label: str
    phrase: str
    container: str
    treat: str
    shelf: str
    shelf_height: int
    fragile: bool
    spill_word: str
    ending_line: str
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
class UnsafeTool:
    id: str
    label: str
    phrase: str
    reach: int
    stability: int
    sound: str
    warning_text: str
    fail_text: str
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
class SafeAid:
    id: str
    label: str
    phrase: str
    reach: int
    support: int
    action_text: str
    ending_text: str
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
    power: int
    text: str
    fail: str
    qa_text: str
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
        return [e for e in self.entities.values() if e.role in {"reacher", "cautioner"}]

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


def _r_wobble_warn(world: World) -> list[str]:
    out: list[str] = []
    tool = world.get("unsafe_tool")
    if tool.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble_warn", tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "room" in world.entities:
        world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_breakage(world: World) -> list[str]:
    out: list[str] = []
    tool = world.get("unsafe_tool")
    prize = world.get("prize")
    if tool.meters["wobble"] < 2.0 or prize.meters["held"] < THRESHOLD:
        return out
    sig = ("breakage", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if prize.fragile:
        prize.meters["broken"] += 1
    prize.meters["spilled"] += 1
    if "room" in world.entities:
        world.get("room").meters["mess"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble_warn", tag="physical", apply=_r_wobble_warn),
    Rule(name="breakage", tag="physical", apply=_r_breakage),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(x for x in lines if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def can_reach(tool: UnsafeTool, prize: Prize) -> bool:
    return tool.reach >= prize.shelf_height


def safe_can_reach(aid: SafeAid, prize: Prize) -> bool:
    return aid.reach >= prize.shelf_height


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def climb_severity(tool: UnsafeTool, delay: int) -> int:
    return tool.stability + delay


def is_contained(response: Response, tool: UnsafeTool, delay: int) -> bool:
    return response.power >= climb_severity(tool, delay)


def would_avert(relation: str, reacher_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > reacher_age
    authority = initial_caution(trait) + 1.0 + (3.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BOLDNESS_INIT


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    prize = sim.get("prize")
    tool = sim.get("unsafe_tool")
    tool.meters["wobble"] += tool.attrs["cfg"].stability
    prize.meters["held"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("room").meters["danger"],
        "spill": sim.get("prize").meters["spilled"] >= THRESHOLD,
    }


def setup_evening(world: World, reacher: Entity, cautioner: Entity, residence: Residence,
                  prize: Prize, adult: Entity) -> None:
    for child in (reacher, cautioner):
        child.memes["homey"] += 1
    world.say(
        f"At their {residence.label}, the kitchen in the family residence smelled warm and sweet. "
        f"{residence.kitchen_line}"
    )
    world.say(
        f"{reacher.id} and {cautioner.id} had come in from the hall with pink cheeks, "
        f"and {adult.label_word} was making tea while the evening settled down."
    )
    world.say(
        f"Up on {prize.shelf} sat {prize.phrase}. {reacher.id} looked up and whispered, "
        f'"A little {prize.treat} would be a lovely end to the day."'
    )


def rhyme_line() -> str:
    return '"Slow and low, that is how we go," the family liked to say.'


def notice_need(world: World, reacher: Entity, prize: Prize) -> None:
    reacher.memes["desire"] += 1
    world.say(
        f"But {prize.container} was well above {reacher.id}'s head. "
        f"{reacher.pronoun().capitalize()} wanted it right then."
    )


def tempt(world: World, reacher: Entity, tool: UnsafeTool) -> None:
    reacher.memes["boldness"] += 1
    world.say(
        f"{reacher.id}'s eyes slid to {tool.phrase}. "
        f'"I can use {tool.label}," {reacher.pronoun()} said.'
    )


def warn(world: World, cautioner: Entity, reacher: Entity, tool: UnsafeTool, adult: Entity) -> None:
    pred = predict_wobble(world)
    cautioner.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if pred["danger"] >= THRESHOLD:
        extra = f" {tool.sound.capitalize()}—{tool.sound}! Even the little noise sounded like a warning."
    world.say(
        f'{cautioner.id} listened as {tool.label} gave a tiny {tool.sound}. '
        f'"Please do not climb on {tool.label}," {cautioner.pronoun()} said. '
        f'"{tool.warning_text}"{extra}'
    )
    world.say(
        f'{adult.label_word.capitalize()} glanced over from the counter and repeated the rhyme: '
        f'{rhyme_line()}'
    )


def back_down(world: World, reacher: Entity, cautioner: Entity, tool: UnsafeTool) -> None:
    reacher.memes["relief"] += 1
    cautioner.memes["relief"] += 1
    reacher.memes["boldness"] = 0.0
    world.say(
        f"{reacher.id} put a hand on {tool.label}, then pulled it back. "
        f"{tool.sound.capitalize()} - {tool.sound()}"
    )


def defy(world: World, reacher: Entity, cautioner: Entity, tool: UnsafeTool) -> None:
    reacher.memes["defiance"] += 1
    world.say(
        f'"Just for one second," {reacher.id} said. Before anyone could stop {reacher.pronoun("object")}, '
        f"{reacher.pronoun()} dragged over {tool.phrase}."
    )


def climb(world: World, reacher: Entity, tool_cfg: UnsafeTool, prize: Prize) -> None:
    tool = world.get("unsafe_tool")
    tool.meters["wobble"] += tool_cfg.stability
    world.get("prize").meters["held"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{tool_cfg.sound.capitalize()} - {tool_cfg.sound()}"
    )


def alarm(world: World, cautioner: Entity, reacher: Entity, prize: Prize, adult: Entity,
          tool_cfg: UnsafeTool) -> None:
    tool = world.get("unsafe_tool")
    if tool.meters["wobble"] >= THRESHOLD:
        world.say(
            f"{tool_cfg.sound.capitalize()}! {tool_cfg.sound}! {tool_cfg.fail_text} "
            f'The {prize.container} gave a shaky little clink. "{reacher.id}!" {cautioner.id} cried.'
        )
        world.say(f'"{adult.label_word.upper()}!"')


def rescue(world: World, adult: Entity, response: Response, prize: Prize) -> None:
    world.get("unsafe_tool").meters["wobble"] = 0.0
    world.get("room").meters["danger"] = 0.0
    body = response.text.replace("{container}", prize.container)
    world.say(
        f"{adult.label_word.capitalize()} moved fast and {body}."
    )


def rescue_fail(world: World, adult: Entity, response: Response, prize: Prize) -> None:
    body = response.fail.replace("{container}", prize.container)
    world.say(
        f"{adult.label_word.capitalize()} hurried over and {body}."
    )
    world.get("unsafe_tool").meters["wobble"] = 2.0
    world.get("prize").meters["held"] = 1.0
    propagate(world, narrate=False)


def spill_scene(world: World, prize: Prize) -> None:
    p = world.get("prize")
    if p.meters["spilled"] >= THRESHOLD:
        if p.meters["broken"] >= THRESHOLD:
            world.say(
                f"Then came a sharp plink and a soft thump as {prize.container} slipped, "
                f"spilled {prize.spill_word}, and broke on the floor."
            )
        else:
            world.say(
                f"Then came a slippery slosh as {prize.container} tipped and {prize.spill_word} ran over the floor."
            )


def lesson(world: World, adult: Entity, reacher: Entity, cautioner: Entity,
           prize: Prize, safe_aid: SafeAid) -> None:
    for child in (reacher, cautioner):
        child.memes["relief"] += 1
        child.memes["lesson"] += 1
        child.memes["fear"] = 0.0
    world.say(
        f"{adult.label_word.capitalize()} let out a long breath and hugged them close. "
        f'"Treats can wait," {adult.pronoun()} said softly. "Bodies come first, dishes next, and crumbs last."'
    )
    world.say(
        f'{adult.pronoun().capitalize()} tapped {safe_aid.label} with a finger and added, '
        f'{rhyme_line()}'
    )


def sad_lesson(world: World, adult: Entity, reacher: Entity, cautioner: Entity,
               prize: Prize, safe_aid: SafeAid) -> None:
    for child in (reacher, cautioner):
        child.memes["lesson"] += 1
        child.memes["relief"] += 1
    world.say(
        f"{adult.label_word.capitalize()} knelt on the clean patch of floor and held both children tight. "
        f'"No {prize.treat} is worth a tumble," {adult.pronoun()} said. '
        f'"We can wipe up {prize.spill_word}, but we do not want anyone hurt."'
    )
    world.say(
        f"Even with the mess around them, the rhyme came back to all of them: {rhyme_line()}"
    )


def safe_finish(world: World, adult: Entity, reacher: Entity, cautioner: Entity,
                prize: Prize, safe_aid: SafeAid) -> None:
    for child in (reacher, cautioner):
        child.memes["joy"] += 1
        child.memes["safety"] += 1
    world.say(
        f"Then {adult.label_word} {safe_aid.action_text}. "
        f"This time there was no wobble at all."
    )
    world.say(
        f"{reacher.id} climbed up, reached {prize.container} safely, and handed the first {prize.treat} to {cautioner.id}. "
        f"{prize.ending_line}"
    )
    world.say(
        f"{safe_aid.ending_text} The kitchen felt quiet again, with only cups clinking and the evening light resting on the shelves."
    )


def averted_finish(world: World, adult: Entity, reacher: Entity, cautioner: Entity,
                   prize: Prize, safe_aid: SafeAid) -> None:
    for child in (reacher, cautioner):
        child.memes["joy"] += 1
        child.memes["safety"] += 1
    world.say(
        f"{reacher.id} stepped away from {world.get('unsafe_tool').label}, and the whole room seemed to settle. "
        f"Nothing fell. Nothing cracked. The warning had done its work."
    )
    world.say(
        f"Then {adult.label_word} {safe_aid.action_text}, and soon the {prize.treat} were shared the safe way. "
        f"{safe_aid.ending_text}"
    )
@dataclass
class StoryParams:
    residence: str
    prize: str
    unsafe: str
    safe_aid: str
    response: str
    reacher: str
    reacher_gender: str
    cautioner: str
    cautioner_gender: str
    adult: str
    trait: str
    delay: int = 0
    reacher_age: int = 5
    cautioner_age: int = 7
    relation: str = "siblings"
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for rid in RESIDENCES:
        for pid, prize in PRIZES.items():
            for uid, unsafe in UNSAFE_TOOLS.items():
                if not can_reach(unsafe, prize):
                    continue
                for sid, safe in SAFE_AIDS.items():
                    if safe_can_reach(safe, prize):
                        combos.append((rid, pid, uid, sid))
    return combos


KNOWLEDGE = {
    "residence": [(
        "What does residence mean?",
        "Residence means the place where someone lives. A residence can be an apartment, a house, or another home."
    )],
    "step_stool": [(
        "Why is a step stool safer than a wobbly chair?",
        "A step stool is made for standing, with broad steps and feet that grip the floor. A chair can slide or tip in ways that surprise you."
    )],
    "adult_help": [(
        "Why is it smart to ask a grown-up for help with a high shelf?",
        "A grown-up is taller and steadier, so they can reach things without risky climbing. Asking for help keeps both people and dishes safe."
    )],
    "glass": [(
        "Why can a glass jar break when it falls?",
        "Glass is hard but brittle, so a hard bump can crack or shatter it. That is why fallen glass must be cleaned by a grown-up."
    )],
    "fruit": [(
        "Why can fruit roll when it drops?",
        "Round fruit keeps moving because its curved shape lets it roll. On a smooth floor it can roll surprisingly far."
    )],
    "cookies": [(
        "What are crumbs?",
        "Crumbs are tiny broken bits of food, like little pieces of cookie or cracker that fall off when you eat or spill them."
    )],
    "safe_reach": [(
        "What is a safe way to get something from a high shelf?",
        "You can use a steady step stool with a grown-up nearby, or ask a grown-up to lift it down for you. Safe reaching means no wobbling and no rushing."
    )],
}
KNOWLEDGE_ORDER = ["residence", "glass", "fruit", "cookies", "step_stool", "adult_help", "safe_reach"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prize = f["prize_cfg"]
    residence = f["residence"]
    reacher = f["reacher"]
    cautioner = f["cautioner"]
    outcome = f["outcome"]
    base = (
        f'Write a gentle slice-of-life story for a 3-to-5-year-old set in a family {residence.phrase}. '
        f'Include the word "residence", some soft sound effects, a little foreshadowing, and a repeated rhyme.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a homey story where {reacher.id} wants a {prize.treat} from a high shelf, "
            f"but {cautioner.id} notices the warning sound first and stops the unsafe climb.",
            f"Write a story with a calm near-miss ending where a family rhyme helps a child choose the safe way."
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell a story where {reacher.id} climbs for {prize.container}, the wobble becomes real, "
            f"and a grown-up helps just in time before anything falls.",
            f"Write a story that uses sound effects like creak or clink to foreshadow a small household problem and its gentle fix."
        ]
    return [
        base,
        f"Tell a cautionary but gentle home story where {reacher.id} reaches for {prize.container}, "
        f"it spills, and the family learns a safer habit for next time.",
        f"Write a story with a sad little mess, a comforting grown-up, and an ending image that shows the home has become calmer and wiser."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    reacher = f["reacher"]
    cautioner = f["cautioner"]
    adult = f["adult"]
    prize = f["prize_cfg"]
    residence = f["residence"]
    unsafe = f["unsafe_cfg"]
    safe_aid = f["safe_aid_cfg"]
    response = f["response"]
    pair = pair_noun(reacher, cautioner, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {reacher.id} and {cautioner.id}, in their {residence.label}, and the grown-up who helped them. "
            f"The story stays close to one ordinary evening at home."
        ),
        (
            f"Why did {reacher.id} want to climb?",
            f"{reacher.id} wanted to reach {prize.container} from the high shelf because a small evening treat sounded good. "
            f"The problem was not the treat itself, but the risky way of trying to get it."
        ),
        (
            f"How did the story warn that trouble might come before anything fell?",
            f"The warning came from the little sounds and from {cautioner.id}'s notice of them. "
            f"When {unsafe.label} gave its tiny {unsafe.sound}, that foreshadowed the bigger wobble that could come next."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What stopped the accident?",
            f"{reacher.id} listened before climbing, so the near-accident never became a real one. "
            f"The warning sound, the family rhyme, and {cautioner.id}'s caution all helped {reacher.pronoun('object')} stop in time."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the treat being shared safely instead of grabbed in a rush. "
            f"The calm ending shows that the family learned to choose {safe_aid.label} or grown-up help over wobbling."
        ))
    elif f["outcome"] == "contained":
        body = response.qa_text.replace("{container}", prize.container)
        qa.append((
            f"How did the grown-up help?",
            f"The grown-up {body}. That quick help mattered because the wobble had already started and needed a steady answer right away."
        ))
        qa.append((
            f"What did {reacher.id} learn?",
            f"{reacher.id} learned that wanting something right away is not the same as reaching for it safely. "
            f"By the end, the family used {safe_aid.label} and the rhyme to turn a scary second into a better habit."
        ))
    else:
        qa.append((
            f"What happened when the help came too late?",
            f"{prize.container.capitalize()} slipped and made a mess on the floor. "
            f"The spill happened because the wobble had already grown bigger than words alone could stop."
        ))
        qa.append((
            "How did the family act after the spill?",
            f"They comforted each other first and cleaned the floor carefully after that. "
            f"The ending matters because the family did not stay upset; they changed the rule for next time and made the home safer."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"residence", "safe_reach"}
    tags |= set(f["prize_cfg"].tags)
    tags |= set(f["safe_aid_cfg"].tags)
    tags |= set(f["response"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        residence="apartment",
        prize="jar_cookies",
        unsafe="wobbly_stool",
        safe_aid="step_stool",
        response="steady_child",
        reacher="Nina",
        reacher_gender="girl",
        cautioner="Owen",
        cautioner_gender="boy",
        adult="mother",
        trait="careful",
        delay=0,
        reacher_age=5,
        cautioner_age=7,
        relation="siblings",
    ),
    StoryParams(
        residence="brick_house",
        prize="bowl_pears",
        unsafe="dining_chair",
        safe_aid="adult_lift",
        response="hold_chair",
        reacher="Milo",
        reacher_gender="boy",
        cautioner="Ruby",
        cautioner_gender="girl",
        adult="father",
        trait="thoughtful",
        delay=0,
        reacher_age=6,
        cautioner_age=5,
        relation="friends",
    ),
    StoryParams(
        residence="duplex",
        prize="tin_crackers",
        unsafe="crate",
        safe_aid="helper_stool",
        response="hold_chair",
        reacher="Lila",
        reacher_gender="girl",
        cautioner="Jude",
        cautioner_gender="boy",
        adult="grandmother",
        trait="patient",
        delay=1,
        reacher_age=6,
        cautioner_age=5,
        relation="siblings",
    ),
    StoryParams(
        residence="apartment",
        prize="jar_cookies",
        unsafe="dining_chair",
        safe_aid="step_stool",
        response="call_wait",
        reacher="Theo",
        reacher_gender="boy",
        cautioner="Mina",
        cautioner_gender="girl",
        adult="mother",
        trait="steady",
        delay=1,
        reacher_age=6,
        cautioner_age=5,
        relation="friends",
    ),
]


def explain_rejection(prize: Prize, unsafe: UnsafeTool, safe_aid: Optional[SafeAid] = None) -> str:
    if not can_reach(unsafe, prize):
        return (
            f"(No story: {unsafe.label} is not tall enough to reach {prize.container} on {prize.shelf}. "
            f"If the child cannot even reach it, the wobble problem never begins.)"
        )
    if safe_aid is not None and not safe_can_reach(safe_aid, prize):
        return (
            f"(No story: {safe_aid.label} would not reach {prize.container} either. "
            f"A safe fix has to solve the same shelf problem without the wobble.)"
        )
    return "(No story: this combination does not make a plausible reaching problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores below the common-sense threshold "
        f"(sense={r.sense} < {SENSE_MIN}). Try a steadier response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.reacher_age, params.cautioner_age, params.trait):
        return "averted"
    response = RESPONSES[params.response]
    unsafe = UNSAFE_TOOLS[params.unsafe]
    return "contained" if is_contained(response, unsafe, params.delay) else "spilled"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
reachable(U, P) :- unsafe(U), prize(P), u_reach(U, R), p_height(P, H), R >= H.
safe_reachable(S, P) :- safe_aid(S), prize(P), s_reach(S, R), p_height(P, H), R >= H.
valid(Rs, P, U, S) :- residence(Rs), prize(P), unsafe(U), safe_aid(S), reachable(U, P), safe_reachable(S, P).

% --- sensible responses ----------------------------------------------------
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

% --- outcome inference -----------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

cautioner_older :- relation(siblings), reacher_age(RA), cautioner_age(CA), CA > RA.
bonus(3) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), boldness_init(BI), A > BI.

severity(St + D) :- chosen_unsafe(U), u_stability(U, St), delay(D).
contained :- chosen_response(R), power(R, P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(spilled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in RESIDENCES:
        lines.append(asp.fact("residence", rid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("p_height", pid, prize.shelf_height))
    for uid, unsafe in UNSAFE_TOOLS.items():
        lines.append(asp.fact("unsafe", uid))
        lines.append(asp.fact("u_reach", uid, unsafe.reach))
        lines.append(asp.fact("u_stability", uid, unsafe.stability))
    for sid, safe in SAFE_AIDS.items():
        lines.append(asp.fact("safe_aid", sid))
        lines.append(asp.fact("s_reach", sid, safe.reach))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_unsafe", params.unsafe),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("reacher_age", params.reacher_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} scenario outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child in a residence, a high shelf, a wobble, and a safer habit."
    )
    ap.add_argument("--residence", choices=RESIDENCES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--unsafe", choices=UNSAFE_TOOLS)
    ap.add_argument("--safe-aid", dest="safe_aid", choices=SAFE_AIDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra beat before help reaches the wobble")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.unsafe and args.prize:
        prize = PRIZES[args.prize]
        unsafe = UNSAFE_TOOLS[args.unsafe]
        if not can_reach(unsafe, prize):
            raise StoryError(explain_rejection(prize, unsafe))
    if args.safe_aid and args.prize:
        prize = PRIZES[args.prize]
        safe = SAFE_AIDS[args.safe_aid]
        if not safe_can_reach(safe, prize):
            unsafe = UNSAFE_TOOLS[args.unsafe] if args.unsafe else next(iter(UNSAFE_TOOLS.values()))
            raise StoryError(explain_rejection(prize, unsafe, safe))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.residence is None or combo[0] == args.residence)
        and (args.prize is None or combo[1] == args.prize)
        and (args.unsafe is None or combo[2] == args.unsafe)
        and (args.safe_aid is None or combo[3] == args.safe_aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    residence_id, prize_id, unsafe_id, safe_id = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    reacher, reacher_gender = _pick_child(rng)
    cautioner, cautioner_gender = _pick_child(rng, avoid=reacher)
    adult = args.adult or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    relation = rng.choice(["siblings", "friends"])
    reacher_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        residence=residence_id,
        prize=prize_id,
        unsafe=unsafe_id,
        safe_aid=safe_id,
        response=response,
        reacher=reacher,
        reacher_gender=reacher_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        adult=adult,
        trait=trait,
        delay=delay,
        reacher_age=reacher_age,
        cautioner_age=cautioner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.residence not in RESIDENCES:
        raise StoryError(f"(Unknown residence: {params.residence})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.unsafe not in UNSAFE_TOOLS:
        raise StoryError(f"(Unknown unsafe tool: {params.unsafe})")
    if params.safe_aid not in SAFE_AIDS:
        raise StoryError(f"(Unknown safe aid: {params.safe_aid})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.response and RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not can_reach(UNSAFE_TOOLS[params.unsafe], PRIZES[params.prize]):
        raise StoryError(explain_rejection(PRIZES[params.prize], UNSAFE_TOOLS[params.unsafe]))
    if not safe_can_reach(SAFE_AIDS[params.safe_aid], PRIZES[params.prize]):
        raise StoryError(explain_rejection(PRIZES[params.prize], UNSAFE_TOOLS[params.unsafe], SAFE_AIDS[params.safe_aid]))

    world = tell(
        residence=RESIDENCES[params.residence],
        prize_cfg=PRIZES[params.prize],
        unsafe_cfg=UNSAFE_TOOLS[params.unsafe],
        safe_aid_cfg=SAFE_AIDS[params.safe_aid],
        response=RESPONSES[params.response],
        reacher_name=params.reacher,
        reacher_gender=params.reacher_gender,
        cautioner_name=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        adult_type=params.adult,
        trait=params.trait,
        delay=params.delay,
        reacher_age=params.reacher_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (residence, prize, unsafe, safe_aid) combos:\n")
        for residence, prize, unsafe, safe_aid in combos:
            print(f"  {residence:11} {prize:12} {unsafe:13} {safe_aid}")
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
            header = (
                f"### {p.reacher} & {p.cautioner}: {p.prize} from {p.residence} "
                f"({p.unsafe}, {p.safe_aid}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(residence: Residence, prize_cfg: Prize, unsafe_cfg: UnsafeTool, safe_aid_cfg: SafeAid,
         response: Response, reacher_name: str = "Nina", reacher_gender: str = "girl",
         cautioner_name: str = "Owen", cautioner_gender: str = "boy",
         adult_type: str = "mother", trait: str = "careful", delay: int = 0,
         reacher_age: int = 5, cautioner_age: int = 7, relation: str = "siblings") -> World:
    world = World()
    reacher = world.add(Entity(
        id=reacher_name,
        kind="character",
        type=reacher_gender,
        role="reacher",
        age=reacher_age,
        traits=["eager"],
    ))
    cautioner = world.add(Entity(
        id=cautioner_name,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    world.add(Entity(id="room", type="kitchen", label="the kitchen"))
    world.add(Entity(
        id="prize",
        type="prize",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        fragile=prize_cfg.fragile,
        edible=True,
    ))
    world.add(Entity(
        id="unsafe_tool",
        type="tool",
        label=unsafe_cfg.label,
        phrase=unsafe_cfg.phrase,
        support=True,
        attrs={"cfg": unsafe_cfg},
    ))
    world.facts.update(
        residence=residence,
        prize_cfg=prize_cfg,
        unsafe_cfg=unsafe_cfg,
        safe_aid_cfg=safe_aid_cfg,
        response=response,
        delay=delay,
        relation=relation,
    )

    reacher.memes["boldness"] = BOLDNESS_INIT
    cautioner.memes["caution"] = initial_caution(trait)
    world.get("unsafe_tool").meters["wobble"] = 0.0
    world.get("prize").meters["held"] = 0.0
    world.get("prize").meters["spilled"] = 0.0
    world.get("prize").meters["broken"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.get("room").meters["mess"] = 0.0

    setup_evening(world, reacher, cautioner, residence, prize_cfg, adult)
    notice_need(world, reacher, prize_cfg)

    world.para()
    tempt(world, reacher, unsafe_cfg)
    warn(world, cautioner, reacher, unsafe_cfg, adult)

    averted = would_avert(relation, reacher_age, cautioner_age, trait)

    if averted:
        reacher.memes["boldness"] = 0.0
        reacher.memes["relief"] += 1
        cautioner.memes["relief"] += 1
        world.say(
            f"{reacher.id} touched {unsafe_cfg.label}, heard its faint {unsafe_cfg.sound}, and stopped. "
            f'"You were right," {reacher.pronoun()} admitted.'
        )
        world.para()
        averted_finish(world, adult, reacher, cautioner, prize_cfg, safe_aid_cfg)
        outcome = "averted"
        contained = True
        severity = 0
    else:
        defy(world, reacher, cautioner, unsafe_cfg)
        world.para()
        world.get("unsafe_tool").meters["wobble"] += float(unsafe_cfg.stability)
        world.get("prize").meters["held"] += 1.0
        propagate(world, narrate=False)
        world.say(
            f"{unsafe_cfg.sound.capitalize()}! {unsafe_cfg.sound}! {reacher.id} climbed onto {unsafe_cfg.phrase}. "
            f"The little noise had warned them already, and now the wobble was real."
        )
        world.say(
            f"{prize_cfg.container.capitalize()} gave a thin clink on the shelf as {reacher.pronoun()} reached for it."
        )
        alarm(world, cautioner, reacher, prize_cfg, adult, unsafe_cfg)

        severity = climb_severity(unsafe_cfg, delay)
        contained = is_contained(response, unsafe_cfg, delay)

        world.para()
        if contained:
            rescue(world, adult, response, prize_cfg)
            lesson(world, adult, reacher, cautioner, prize_cfg, safe_aid_cfg)
            world.para()
            safe_finish(world, adult, reacher, cautioner, prize_cfg, safe_aid_cfg)
            outcome = "contained"
        else:
            rescue_fail(world, adult, response, prize_cfg)
            spill_scene(world, prize_cfg)
            sad_lesson(world, adult, reacher, cautioner, prize_cfg, safe_aid_cfg)
            world.para()
            world.say(
                f"After the floor was wiped and the sharp bits were swept away, "
                f"{adult.label_word} brought over {safe_aid_cfg.phrase} for next time."
            )
            world.say(
                f"No one reached for the high shelf again that night. Instead, they sat together at the table, "
                f"sharing fruit from a low bowl and remembering the rhyme."
            )
            outcome = "spilled"

    world.facts.update(
        reacher=reacher,
        cautioner=cautioner,
        adult=adult,
        averted=averted,
        contained=contained,
        severity=severity,
        outcome=outcome,
        spilled=world.get("prize").meters["spilled"] >= THRESHOLD,
        broken=world.get("prize").meters["broken"] >= THRESHOLD,
        promised=True,
    )
    return world


RESIDENCES = {
    "apartment": Residence(
        id="apartment",
        label="small apartment residence",
        phrase="a small apartment residence",
        kitchen_line="Steam curled from a kettle, and the window over the sink reflected the yellow hall light.",
        tags={"apartment", "residence"},
    ),
    "brick_house": Residence(
        id="brick_house",
        label="brick residence",
        phrase="a brick residence",
        kitchen_line="The floor held the day's last warmth, and a striped dish towel hung beside the stove.",
        tags={"house", "residence"},
    ),
    "duplex": Residence(
        id="duplex",
        label="duplex residence",
        phrase="a duplex residence",
        kitchen_line="Someone downstairs was humming, and the cupboards clicked softly as they cooled.",
        tags={"duplex", "residence"},
    ),
}

PRIZES = {
    "jar_cookies": Prize(
        id="jar_cookies",
        label="cookie jar",
        phrase="a glass cookie jar with round cinnamon cookies inside",
        container="the cookie jar",
        treat="cookie",
        shelf="the top pantry shelf",
        shelf_height=2,
        fragile=True,
        spill_word="crumbs",
        ending_line="Soon they were nibbling with smiles and brushing sugar from their lips.",
        tags={"cookies", "glass"},
    ),
    "bowl_pears": Prize(
        id="bowl_pears",
        label="pear bowl",
        phrase="a blue bowl full of little pears",
        container="the blue pear bowl",
        treat="pear",
        shelf="the high refrigerator shelf",
        shelf_height=2,
        fragile=True,
        spill_word="pears and a splash of water",
        ending_line="A sweet pear smell filled the kitchen while they ate in small, juicy bites.",
        tags={"fruit", "bowl"},
    ),
    "tin_crackers": Prize(
        id="tin_crackers",
        label="cracker tin",
        phrase="a tall tin of star crackers",
        container="the cracker tin",
        treat="cracker",
        shelf="the top cupboard shelf",
        shelf_height=3,
        fragile=False,
        spill_word="star crackers",
        ending_line="Soon crunchy little stars were vanishing one by one.",
        tags={"crackers", "tin"},
    ),
}

UNSAFE_TOOLS = {
    "wobbly_stool": UnsafeTool(
        id="wobbly_stool",
        label="the wobbly stool",
        phrase="the wobbly stool by the counter",
        reach=2,
        stability=1,
        sound="creak",
        warning_text="Its legs dance when anyone climbs on it.",
        fail_text="The stool shivered under small feet.",
        tags={"stool", "wobble"},
    ),
    "dining_chair": UnsafeTool(
        id="dining_chair",
        label="the dining chair",
        phrase="the dining chair with one loose leg cap",
        reach=2,
        stability=2,
        sound="scrape",
        warning_text="It slides first and steadies later, which is the wrong order for climbing.",
        fail_text="The chair skidded with a sharp scrape.",
        tags={"chair", "slide"},
    ),
    "rolling_chair": UnsafeTool(
        id="rolling_chair",
        label="the rolling chair",
        phrase="the rolling chair from the desk nook",
        reach=2,
        stability=3,
        sound="whirr",
        warning_text="Its wheels like to wander.",
        fail_text="The chair rolled the instant weight landed on it.",
        tags={"chair", "wheels"},
    ),
    "crate": UnsafeTool(
        id="crate",
        label="the apple crate",
        phrase="the upside-down apple crate",
        reach=3,
        stability=2,
        sound="clack",
        warning_text="It is tall enough, but its corners rock on the tile.",
        fail_text="The crate rocked corner to corner.",
        tags={"crate", "tall"},
    ),
}

SAFE_AIDS = {
    "step_stool": SafeAid(
        id="step_stool",
        label="the step stool",
        phrase="the step stool",
        reach=2,
        support=3,
        action_text="brought over the step stool with rubber feet",
        ending_text="The rhyme felt less like a warning now and more like part of home.",
        tags={"step_stool", "safe_reach"},
    ),
    "adult_lift": SafeAid(
        id="adult_lift",
        label="a grown-up lift",
        phrase="a grown-up lift",
        reach=3,
        support=4,
        action_text="lifted the treat down with a steady hand",
        ending_text="Even the shelf seemed friendlier once nobody had to wobble to reach it.",
        tags={"adult_help", "safe_reach"},
    ),
    "helper_stool": SafeAid(
        id="helper_stool",
        label="the helper stool",
        phrase="the helper stool with broad steps",
        reach=3,
        support=4,
        action_text="set the helper stool in place and held it steady",
        ending_text="The evening ended in the ordinary, lovely way it had begun.",
        tags={"step_stool", "safe_reach"},
    ),
}

RESPONSES = {
    "steady_child": Response(
        id="steady_child",
        sense=3,
        power=3,
        text="reached the child first, steadied small shoulders, and took {container} down before it could slip",
        fail="caught at {container}, but the wobble had already turned into a spill",
        qa_text="steadied the child and took the container down safely",
        tags={"adult_help", "catch"},
    ),
    "hold_chair": Response(
        id="hold_chair",
        sense=2,
        power=2,
        text="grabbed the seat and held it still long enough to get {container} back onto the shelf",
        fail="grabbed for the seat, but the slide had already started and {container} was tipping",
        qa_text="held the chair still and got the container safe again",
        tags={"adult_help", "catch"},
    ),
    "call_wait": Response(
        id="call_wait",
        sense=1,
        power=1,
        text="called out for everyone to freeze until the wobble stopped",
        fail="called out to wait, but words were slower than the wobble",
        qa_text="called out for everyone to freeze",
        tags={"wait_only"},
    ),
}

GIRL_NAMES = ["Nina", "Lila", "Maya", "Tess", "Ruby", "Cora", "Eva", "Mina"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Eli", "Noah", "Finn", "Jude"]
TRAITS = ["careful", "steady", "thoughtful", "patient", "curious", "quick"]

if __name__ == "__main__":
    main()
