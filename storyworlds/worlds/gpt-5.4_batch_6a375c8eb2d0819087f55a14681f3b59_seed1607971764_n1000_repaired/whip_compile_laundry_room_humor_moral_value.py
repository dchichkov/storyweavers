#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/whip_compile_laundry_room_humor_moral_value.py
=========================================================================

A standalone story world for a tall-tale laundry-room story about a child who
tries to help with a grand "sock compiling" job, takes a silly shortcut with a
swinging whip-like tool, and causes a bubbling mess. The world model tracks
physical state (spill, suds, slickness, toppled stacks) and emotional state
(pride, worry, relief, humility), then renders a complete child-facing story
with humor, a moral, and a twist.

Core shape
----------
- A child and a grown-up are in the laundry room.
- The child wants to help compile the laundry into neat groups.
- The child swings something "like a whip" to hurry the work.
- A detergent bottle or laundry tower gets knocked over, and suds spread.
- A calm grown-up uses a sensible fix.
- The ending proves what changed: the child helps carefully, and the scary
  "laundry beast" turns out to be an ordinary laundry-room sound or pet.

Run it
------
python storyworlds/worlds/gpt-5.4/whip_compile_laundry_room_humor_moral_value.py
python storyworlds/worlds/gpt-5.4/whip_compile_laundry_room_humor_moral_value.py --task socks --tool rope --hazard detergent
python storyworlds/worlds/gpt-5.4/whip_compile_laundry_room_humor_moral_value.py --hazard dryer
python storyworlds/worlds/gpt-5.4/whip_compile_laundry_room_humor_moral_value.py --all
python storyworlds/worlds/gpt-5.4/whip_compile_laundry_room_humor_moral_value.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/whip_compile_laundry_room_humor_moral_value.py --verify
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
    spillable: bool = False
    noisy: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma"}
        male = {"boy", "father", "dad", "man", "grandpa"}
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
            "grandma": "grandma",
            "grandpa": "grandpa",
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
class Task:
    id: str
    job: str
    pile: str
    boast: str
    done: str
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
class Tool:
    id: str
    label: str
    phrase: str
    crack: str
    use_line: str
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
class Hazard:
    id: str
    label: str
    phrase: str
    spill_text: str
    danger_text: str
    spread: int = 1
    spillable: bool = True
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
class Fix:
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


@dataclass
class Twist:
    id: str
    rumor: str
    reveal: str
    ending: str
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


def _r_suds(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["spilled"] < THRESHOLD:
            continue
        sig = ("suds", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        room = world.get("room")
        room.meters["suds"] += 1
        room.meters["slick"] += 1
        for eid in ("child", "adult"):
            world.get(eid).memes["alarm"] += 1
        out.append("__suds__")
    return out


def _r_tumble(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["suds"] < THRESHOLD:
        return out
    tower = world.get("tower")
    if tower.meters["standing"] < THRESHOLD:
        return out
    sig = ("tumble", "tower")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tower.meters["standing"] = 0.0
    tower.meters["toppled"] += 1
    room.meters["mess"] += 1
    world.get("child").memes["embarrassment"] += 1
    out.append("__tumble__")
    return out


CAUSAL_RULES = [
    Rule(name="suds", tag="physical", apply=_r_suds),
    Rule(name="tumble", tag="physical", apply=_r_tumble),
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


def hazard_at_risk(tool: Tool, hazard: Hazard) -> bool:
    return hazard.spillable and tool.id in TOOL_TO_HAZARDS and hazard.id in TOOL_TO_HAZARDS[tool.id]


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def mess_severity(hazard: Hazard, delay: int) -> int:
    return hazard.spread + delay


def is_contained(fix: Fix, hazard: Hazard, delay: int) -> bool:
    return fix.power >= mess_severity(hazard, delay)


def predict_mess(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _do_spill(sim, sim.get(hazard_id), narrate=False)
    return {
        "suds": sim.get("room").meters["suds"],
        "slick": sim.get("room").meters["slick"],
        "tower_toppled": sim.get("tower").meters["toppled"] >= THRESHOLD,
    }


def _do_spill(world: World, hazard_ent: Entity, narrate: bool = True) -> None:
    hazard_ent.meters["spilled"] += 1
    world.get("room").meters["mess"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, adult: Entity, task: Task) -> None:
    child.memes["pride"] += 1
    world.say(
        f"One windy-washy afternoon, {child.id} stood in the laundry room beside "
        f"{child.pronoun('possessive')} {adult.label_word} and looked at {task.pile}."
    )
    world.say(
        f"In {child.id}'s mind, it was not a pile at all. It was {task.boast}."
    )
    world.say(
        f'"I can compile this whole mountain before the dryer blinks twice," '
        f'{child.id} declared.'
    )


def need_help(world: World, adult: Entity, task: Task) -> None:
    world.say(
        f"{adult.label_word.capitalize()} smiled and said the same thing {adult.pronoun()} "
        f"always said in that room: small hands could help, but careful hands helped most."
    )
    world.say(
        f"Together they began to {task.job}, one patient piece at a time."
    )


def tempt(world: World, child: Entity, tool: Tool) -> None:
    child.memes["showoff"] += 1
    world.say(
        f"Then {child.id} spotted {tool.phrase}. To a child with a big imagination, "
        f"it looked less like laundry gear and more like a hero's whip."
    )
    world.say(
        f'{child.pronoun("subject").capitalize()} grinned. "{tool.use_line}"'
    )


def warn(world: World, adult: Entity, child: Entity, tool: Tool, hazard: Hazard) -> None:
    pred = predict_mess(world, "hazard")
    world.facts["predicted_suds"] = pred["suds"]
    world.facts["predicted_slick"] = pred["slick"]
    world.facts["predicted_tumble"] = pred["tower_toppled"]
    extra = ""
    if pred["tower_toppled"]:
        extra = " and the folded tower could come tumbling down too"
    world.say(
        f'{adult.label_word.capitalize()} lifted a finger. "Easy now. If you snap '
        f"that {tool.label} around in here, you could hit {hazard.phrase}, and then "
        f"soap would slither over the floor{extra}."
    )


def defy(world: World, child: Entity, tool: Tool) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But tall tales make even ordinary rooms sound like battlefields, and "
        f"{child.id} was feeling ten feet tall."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} gave the {tool.label} a grand swing. {tool.crack}"
    )


def spill(world: World, child: Entity, hazard_ent: Entity, hazard: Hazard) -> None:
    _do_spill(world, hazard_ent)
    child.memes["fear"] += 1
    world.say(
        f"{hazard.spill_text} In a blink, the laundry room looked as if a bubble storm "
        f"had galloped through it."
    )


def alarm(world: World, child: Entity, adult: Entity, twist: Twist) -> None:
    world.say(
        f'"{adult.label_word.capitalize()}!" {child.id} yelped. "The {twist.rumor} is waking up!"'
    )


def rescue(world: World, adult: Entity, fix: Fix, hazard: Hazard) -> None:
    world.get("hazard").meters["spilled"] = 0.0
    world.get("room").meters["suds"] = 0.0
    world.get("room").meters["slick"] = 0.0
    world.get("room").meters["mess"] = 0.0
    body = fix.text.replace("{hazard}", hazard.label)
    world.say(
        f"{adult.label_word.capitalize()} did not holler. {adult.pronoun().capitalize()} {body}."
    )
    if world.get("tower").meters["toppled"] >= THRESHOLD:
        world.say(
            "The towel tower was soon standing up again, though it leaned like a sleepy sheep for a moment."
        )


def rescue_fail(world: World, adult: Entity, fix: Fix, hazard: Hazard) -> None:
    world.get("room").meters["suds"] += 1
    world.get("room").meters["slick"] += 1
    world.get("room").meters["mess"] += 1
    body = fix.fail.replace("{hazard}", hazard.label)
    world.say(
        f"{adult.label_word.capitalize()} {body}, but the bubbles kept marching across the floor."
    )
    world.say(
        "They did not turn dangerous, but they did make the whole room sloshy and ridiculous."
    )


def lesson(world: World, adult: Entity, child: Entity) -> None:
    child.memes["humility"] += 1
    child.memes["relief"] += 1
    child.memes["learning"] += 1
    adult.memes["care"] += 1
    world.say(
        f"Then {adult.label_word.capitalize()} knelt beside {child.id} and wiped one foamy spot from "
        f"{child.pronoun('possessive')} nose."
    )
    world.say(
        f'"Big helpers do not have to be wild helpers," {adult.pronoun()} said. '
        f'"Fast tricks can make slow messes. Careful work is the brave kind."'
    )


def careful_finish(world: World, child: Entity, adult: Entity, task: Task, twist: Twist) -> None:
    child.memes["pride"] += 1
    world.say(
        f"After that, {child.id} used both hands, quiet eyes, and no whip-cracks at all."
    )
    world.say(
        f"Sock by sock, towel by towel, {child.pronoun('subject')} helped {task.done}."
    )
    world.say(
        f"And then came the twist: {twist.reveal} {twist.ending}"
    )


def soggy_finish(world: World, child: Entity, adult: Entity, task: Task, twist: Twist) -> None:
    child.memes["relief"] += 1
    child.memes["humility"] += 1
    child.memes["learning"] += 1
    world.say(
        f"When the room was finally less slippery, {child.id} sat on an upside-down basket and took a long breath."
    )
    world.say(
        f'{adult.label_word.capitalize()} handed over one dry sock at a time. "We will still compile the laundry," '
        f'{adult.pronoun()} said, "just not like a thunderstorm."'
    )
    world.say(
        f"The twist came then too: {twist.reveal} Even {child.id} had to laugh."
    )
@dataclass
class StoryParams:
    task: str
    tool: str
    hazard: str
    fix: str
    twist: str
    child_name: str
    child_gender: str
    adult_type: str
    delay: int = 0
    pet: str = ""
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
    "socks": [(
        "What does it mean to pair socks?",
        "It means finding two socks that belong together. People often match them by color, size, or pattern."
    )],
    "folding": [(
        "Why do people fold towels?",
        "Folding towels keeps them neat and easy to stack. It also helps a laundry room stay tidy."
    )],
    "sorting": [(
        "What does compile mean in a story like this?",
        "Here it means putting things together into neat groups. It is a fancy word for gathering and organizing."
    )],
    "soap": [(
        "Why is spilled soap slippery?",
        "Soap mixes with water and makes a slick layer on the floor. That is why people clean it up quickly."
    )],
    "whip": [(
        "Why should you not swing things like a whip in a small room?",
        "A swinging rope or belt can hit bottles, baskets, or people. In a small room, silly swinging can make a real mess fast."
    )],
    "cleanup": [(
        "What should you do when soap spills on the floor?",
        "Tell a grown-up right away and clean it carefully. Soap can make the floor slippery, so people should move slowly."
    )],
    "cat": [(
        "Why do shadows look bigger in a busy room?",
        "Shadows can look strange when clothes hang, machines move, or pets sit still. Our eyes can turn ordinary shapes into silly monsters."
    )],
    "dryer": [(
        "Why does a dryer sometimes thump or buzz?",
        "A dryer can thump when something heavy tumbles inside, and it can buzz when a cycle ends. Those sounds can be surprising, but they are normal."
    )],
    "sound": [(
        "Why do normal sounds feel scary sometimes?",
        "When you do not know what made the sound, your imagination can grow it into something huge. Once you understand it, the sound feels ordinary again."
    )],
}
KNOWLEDGE_ORDER = ["sorting", "socks", "folding", "soap", "whip", "cleanup", "dryer", "cat", "sound"]


def pair_noun(gender: str) -> str:
    return "child" if gender in {"girl", "boy"} else "child"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, adult, task, tool, twist = f["child"], f["adult"], f["task"], f["tool"], f["twist"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old set in a laundry room. Include the words "whip" and "compile."',
        f"Tell a funny moral story where {child.label} tries to {task.job}, swings a {tool.label} like a whip, and learns that careful helping is better than showing off.",
        f"Write a playful story with a twist in which a child mistakes an ordinary laundry-room sound for the {twist.rumor}, but a calm {adult.label_word} helps fix the mess and explain what really happened.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    task = f["task"]
    tool = f["tool"]
    hazard = f["hazard_cfg"]
    fix = f["fix"]
    twist = f["twist"]
    child_name = child.label
    adult_word = adult.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, a child helping in the laundry room, and {child_name}'s {adult_word}. They start with an ordinary chore that grows into a very silly tall tale."
        ),
        (
            f"What did {child_name} want to do?",
            f"{child_name} wanted to {task.job}. {child.pronoun('subject').capitalize()} was proud and wanted to finish the job in a grand, showy way."
        ),
        (
            f"Why did {adult_word} warn {child_name} about the {tool.label}?",
            f"{adult_word.capitalize()} warned that swinging it like a whip could hit {hazard.phrase}. If that happened, soap could spill and make the laundry-room floor slick."
        ),
        (
            f"What happened when {child_name} swung the {tool.label}?",
            f"{hazard.spill_text} That turned the careful chore into a bubbling mess almost at once."
        ),
    ]
    if f["outcome"] == "contained":
        qa.append((
            f"How did {child_name}'s {adult_word} fix the problem?",
            f"{adult_word.capitalize()} {fix.qa_text}. The quick cleanup stopped the suds before the whole room turned into a slippery bubble field."
        ))
        qa.append((
            "What lesson did the child learn?",
            f"{child_name} learned that careful helping is better than flashy shortcuts. The mess happened because showing off was faster than thinking."
        ))
    else:
        qa.append((
            f"Did the mess get cleaned up right away?",
            f"Not right away. {adult_word.capitalize()} tried to help, but the bubbles kept spreading for a while, so the cleanup took longer and felt even sillier."
        ))
        qa.append((
            "What lesson did the child learn?",
            f"{child_name} learned that wild tricks can make a small chore much harder. Careful work would have kept the floor safe and the laundry calm."
        ))
    twist_answer = twist.reveal
    if "{child}" in twist_answer:
        twist_answer = twist_answer.replace("{child}", child_name)
    qa.append((
        "What was the twist at the end?",
        f"The scary thing was not a real monster at all. {twist_answer}."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["task"].tags) | set(f["tool"].tags) | set(f["hazard_cfg"].tags) | set(f["fix"].tags) | set(f["twist"].tags)
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        task="socks",
        tool="rope",
        hazard="detergent",
        fix="mop",
        twist="cat",
        child_name="Milo",
        child_gender="boy",
        adult_type="mother",
        delay=0,
        pet="the cat",
    ),
    StoryParams(
        task="towels",
        tool="belt",
        hazard="softener",
        fix="towels",
        twist="buzzer",
        child_name="Lila",
        child_gender="girl",
        adult_type="grandpa",
        delay=0,
        pet="",
    ),
    StoryParams(
        task="shirts",
        tool="sheet",
        hazard="dryer",
        fix="scoop",
        twist="goat",
        child_name="Finn",
        child_gender="boy",
        adult_type="father",
        delay=1,
        pet="",
    ),
    StoryParams(
        task="socks",
        tool="rope",
        hazard="basket",
        fix="towels",
        twist="buzzer",
        child_name="Ada",
        child_gender="girl",
        adult_type="grandma",
        delay=0,
        pet="",
    ),
]


def explain_rejection(tool: Tool, hazard: Hazard) -> str:
    if not hazard.spillable:
        return f"(No story: {hazard.label} would not spill, so the laundry-room mess never starts.)"
    return (
        f"(No story: a swinging {tool.label} is not modeled as likely to hit {hazard.phrase}. "
        f"Pick a nearby spill risk like detergent, softener, a dryer-sheet box, or a clothespin basket.)"
    )


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "contained" if is_contained(FIXES[params.fix], HAZARDS[params.hazard], params.delay) else "soggy"


ASP_RULES = r"""
hazard(Tool, Hazard) :- tool_hits(Tool, Hazard), spillable(Hazard).
sensible(Fix) :- fix(Fix), sense(Fix, S), sense_min(M), S >= M.
valid(Task, Tool, Hazard) :- task(Task), tool(Tool), hazard_item(Hazard), hazard(Tool, Hazard).

severity(Sp + D) :- chosen_hazard(H), spread(H, Sp), delay(D).
contained :- chosen_fix(F), power(F, P), severity(V), P >= V.
outcome(contained) :- contained.
outcome(soggy) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for tool_id in TOOLS:
        lines.append(asp.fact("tool", tool_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard_item", hazard_id))
        if hazard.spillable:
            lines.append(asp.fact("spillable", hazard_id))
        lines.append(asp.fact("spread", hazard_id, hazard.spread))
    for tool_id, hazards in TOOL_TO_HAZARDS.items():
        for hazard_id in sorted(hazards):
            lines.append(asp.fact("tool_hits", tool_id, hazard_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_hazard", params.hazard),
        asp.fact("chosen_fix", params.fix),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    csens = set(asp_sensible())
    psens = {f.id for f in sensible_fixes()}
    if csens == psens:
        print(f"OK: sensible fixes match ({sorted(csens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(csens)} python={sorted(psens)}")

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale laundry-room storyworld with humor, a twist, and a moral."
    )
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--adult-type", choices=ADULT_TYPES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the mess spreads before the grown-up fully gets control")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.hazard:
        tool = TOOLS[args.tool]
        hazard = HAZARDS[args.hazard]
        if not hazard_at_risk(tool, hazard):
            raise StoryError(explain_rejection(tool, hazard))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.task is None or combo[0] == args.task)
        and (args.tool is None or combo[1] == args.tool)
        and (args.hazard is None or combo[2] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    task, tool, hazard = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    twist = args.twist or rng.choice(sorted(TWISTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES[child_gender])
    adult_type = args.adult_type or rng.choice(ADULT_TYPES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    pet = rng.choice(PETS)
    return StoryParams(
        task=task,
        tool=tool,
        hazard=hazard,
        fix=fix,
        twist=twist,
        child_name=child_name,
        child_gender=child_gender,
        adult_type=adult_type,
        delay=delay,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.task not in TASKS:
        raise StoryError(f"(Unknown task: {params.task})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.twist not in TWISTS:
        raise StoryError(f"(Unknown twist: {params.twist})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.adult_type not in ADULT_TYPES:
        raise StoryError(f"(Unknown adult type: {params.adult_type})")

    tool = TOOLS[params.tool]
    hazard = HAZARDS[params.hazard]
    if not hazard_at_risk(tool, hazard):
        raise StoryError(explain_rejection(tool, hazard))
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        task=TASKS[params.task],
        tool=tool,
        hazard=hazard,
        fix=FIXES[params.fix],
        twist=TWISTS[params.twist],
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult_type,
        delay=params.delay,
        pet=params.pet,
    )
    story = world.render()
    child_name = params.child_name
    if params.twist == "goat":
        story = story.replace("{child}", child_name)

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (task, tool, hazard) combos:\n")
        for task, tool, hazard in combos:
            print(f"  {task:8} {tool:6} {hazard}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.child_name}: {p.task} with {p.tool} near {p.hazard} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    task: Task,
    tool: Tool,
    hazard: Hazard,
    fix: Fix,
    twist: Twist,
    child_name: str = "Milo",
    child_gender: str = "boy",
    adult_type: str = "mother",
    delay: int = 0,
    pet: str = "",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, role="child", label=child_name))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, role="adult", label="the adult"))
    room = world.add(Entity(id="room", type="room", label="laundry room"))
    room.meters["suds"] = 0.0
    room.meters["slick"] = 0.0
    room.meters["mess"] = 0.0
    tower = world.add(Entity(id="tower", type="towels", label="towel tower"))
    tower.meters["standing"] = 1.0
    hazard_ent = world.add(Entity(id="hazard", type="hazard", label=hazard.label, spillable=hazard.spillable))
    hazard_ent.meters["spilled"] = 0.0
    world.facts["pet"] = pet

    opening(world, child, adult, task)
    need_help(world, adult, task)

    world.para()
    tempt(world, child, tool)
    warn(world, adult, child, tool, hazard)
    defy(world, child, tool)

    world.para()
    spill(world, child, hazard_ent, hazard)
    alarm(world, child, adult, twist)

    severity = mess_severity(hazard, delay)
    contained = is_contained(fix, hazard, delay)

    world.para()
    if contained:
        rescue(world, adult, fix, hazard)
        lesson(world, adult, child)
        world.para()
        careful_finish(world, child, adult, task, twist)
        outcome = "contained"
    else:
        rescue_fail(world, adult, fix, hazard)
        lesson(world, adult, child)
        world.para()
        soggy_finish(world, child, adult, task, twist)
        outcome = "soggy"

    world.facts.update(
        child=child,
        adult=adult,
        task=task,
        tool=tool,
        hazard_cfg=hazard,
        fix=fix,
        twist=twist,
        outcome=outcome,
        delay=delay,
        severity=severity,
        toppled=world.get("tower").meters["toppled"] >= THRESHOLD,
        pet=pet,
    )
    return world


TASKS = {
    "socks": Task(
        id="socks",
        job="compile lonely socks into proper pairs",
        pile="a hill of socks",
        boast="the Great Sock Range, snowy at the toes and wild at the heels",
        done="compile the last sock pair into a neat little army",
        tags={"socks", "sorting"},
    ),
    "towels": Task(
        id="towels",
        job="compile the towels into straight folded stacks",
        pile="a tower of towels and washcloths",
        boast="the Soft Mountain of a Hundred Folds",
        done="compile the folded towels into square little towers",
        tags={"towels", "folding"},
    ),
    "shirts": Task(
        id="shirts",
        job="compile small shirts into tidy color groups",
        pile="a bright drift of shirts",
        boast="the Rainbow Prairie, waving sleeve by sleeve",
        done="compile the shirts into neat color rows",
        tags={"shirts", "sorting"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="clothesline rope",
        phrase="a coil of clothesline rope",
        crack="It swished through the air with a sharp little snap.",
        use_line="Watch me whip this line once, and the whole pile will jump into order",
        tags={"rope", "whip"},
    ),
    "belt": Tool(
        id="belt",
        label="robe belt",
        phrase="a long blue robe belt",
        crack="It gave a floppy snap that sounded far more heroic than it looked.",
        use_line="One mighty whip-swish, and this laundry will line up by itself",
        tags={"belt", "whip"},
    ),
    "sheet": Tool(
        id="sheet",
        label="rolled bedsheet",
        phrase="a rolled-up bedsheet",
        crack="The sheet snapped and boomed like the world's softest thunder.",
        use_line="Stand back and see the great laundry whip at work",
        tags={"sheet", "whip"},
    ),
}

HAZARDS = {
    "detergent": Hazard(
        id="detergent",
        label="detergent bottle",
        phrase="the big detergent bottle",
        spill_text="The bottle tipped, glugged, and poured a shining ribbon of soap onto the floor.",
        danger_text="soap on the floor makes it slick",
        spread=2,
        spillable=True,
        tags={"detergent", "soap"},
    ),
    "softener": Hazard(
        id="softener",
        label="softener jug",
        phrase="the softener jug",
        spill_text="The jug wobbled, bowed, and burped a puddle of slippery blue softener across the tiles.",
        danger_text="softener on tile makes a floor slippery",
        spread=2,
        spillable=True,
        tags={"softener", "soap"},
    ),
    "dryer": Hazard(
        id="dryer",
        label="dryer sheet box",
        phrase="the open dryer sheet box",
        spill_text="The box flipped over and dryer sheets flew out in a soft white blizzard while a little cup of soap nearby sloshed over too.",
        danger_text="spilled soap and scattered sheets make a silly mess",
        spread=1,
        spillable=True,
        tags={"dryer", "soap"},
    ),
    "basket": Hazard(
        id="basket",
        label="clothespin basket",
        phrase="the clothespin basket perched beside the soap cup",
        spill_text="The basket flew sideways, clothespins rattled everywhere, and the soap cup splashed a frothy puddle over the floor.",
        danger_text="a toppled basket can scatter things and spill soap nearby",
        spread=1,
        spillable=True,
        tags={"basket", "soap"},
    ),
}

FIXES = {
    "towels": Fix(
        id="towels",
        sense=3,
        power=2,
        text="snatched two old towels, laid them over the spill, and pressed the suds quiet before they could skate any farther",
        fail="threw towels over the {hazard}, but they were soon soaked through",
        qa_text="smothered the spill with old towels",
        tags={"towels", "cleanup"},
    ),
    "mop": Fix(
        id="mop",
        sense=3,
        power=3,
        text="grabbed the mop and a bucket, boxed the suds into one corner, and swept the floor clear again",
        fail="mopped around the {hazard}, but the bubbles spread faster than the mop could catch them",
        qa_text="mopped the suds up",
        tags={"mop", "cleanup"},
    ),
    "scoop": Fix(
        id="scoop",
        sense=2,
        power=1,
        text="righted the bottle, scooped up the worst of the soap with a dustpan, and wiped the rest with a rag",
        fail="tried to scoop and wipe the {hazard} mess, but the suds kept sneaking out under the rag",
        qa_text="righted the spill and wiped it with a rag",
        tags={"rag", "cleanup"},
    ),
    "fan": Fix(
        id="fan",
        sense=1,
        power=0,
        text="pointed a fan at the spill, which only pushed bubbles into fluffier hills",
        fail="pointed a fan at the {hazard} mess",
        qa_text="blew on the spill with a fan",
        tags={"fan", "cleanup"},
    ),
}

TWISTS = {
    "cat": Twist(
        id="cat",
        rumor="Laundry Beast",
        reveal="the terrible thumping noise came from a sneaker in the dryer, and the looming shadow was only the family cat sitting in a basket",
        ending="The cat blinked once, as if it had supervised the whole adventure.",
        tags={"cat", "dryer"},
    ),
    "buzzer": Twist(
        id="buzzer",
        rumor="Soap Dragon",
        reveal="the great roar was only the dryer buzzer and the washer's happy glug-glug",
        ending="After that, the laundry room sounded much less like a cave and much more like a room full of chores.",
        tags={"dryer", "sound"},
    ),
    "goat": Twist(
        id="goat",
        rumor="Lint Giant",
        reveal="the giant shape under the hanging shirts was only a wobbling hamper with a mop on top of it",
        ending="For a whole week, {child} called it the politest giant in town.",
        tags={"hamper", "sound"},
    ),
}

TOOL_TO_HAZARDS = {
    "rope": {"detergent", "softener", "dryer", "basket"},
    "belt": {"detergent", "softener", "basket"},
    "sheet": {"detergent", "softener", "dryer"},
}

CHILD_NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Tess", "Poppy", "Ada"],
    "boy": ["Milo", "Otis", "Finn", "Jasper", "Toby", "Leo"],
}
PETS = ["the cat", "the puppy", "", ""]
ADULT_TYPES = ["mother", "father", "grandma", "grandpa"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for task_id in TASKS:
        for tool_id, tool in TOOLS.items():
            for hazard_id, hazard in HAZARDS.items():
                if hazard_at_risk(tool, hazard):
                    combos.append((task_id, tool_id, hazard_id))
    return combos

if __name__ == "__main__":
    main()
