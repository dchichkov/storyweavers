#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/imaginary_wrench_ruffle_problem_solving_flashback_bad.py
===================================================================================

A standalone storyworld about a child who tries to fix a wobbly wagon wheel with
an imaginary tool instead of a real safe plan. The world models a concrete
problem, a memory of earlier good advice, a decision point, and either a careful
repair or a bad ending where the outing is spoiled.

Required seed words included in the domain and prose:
    imaginary, wrench, ruffle

Narrative features embodied in world state:
    * Problem Solving: the child must deal with a loose wheel.
    * Flashback: the child remembers a grown-up's earlier advice.
    * Bad Ending: some valid stories end with the wagon broken and the picnic lost.

Style:
    Child-facing, concrete, gently rhyming prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/imaginary_wrench_ruffle_problem_solving_flashback_bad.py
    python storyworlds/worlds/gpt-5.4/imaginary_wrench_ruffle_problem_solving_flashback_bad.py --all
    python storyworlds/worlds/gpt-5.4/imaginary_wrench_ruffle_problem_solving_flashback_bad.py --verify
    python storyworlds/worlds/gpt-5.4/imaginary_wrench_ruffle_problem_solving_flashback_bad.py -n 5 --seed 7 --qa
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    path: str
    breeze: str
    outing: str
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
class Vehicle:
    id: str
    label: str
    cargo: str
    wheel_part: str
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
class Problem:
    id: str
    label: str
    severity: int
    sign: str
    consequence: str
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
    kind: str
    real: bool
    works_for: set[str] = field(default_factory=set)
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
class HelperAction:
    id: str
    label: str
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


def _r_loose_causes_risk(world: World) -> list[str]:
    wagon = world.get("wagon")
    if wagon.meters["loose"] < THRESHOLD:
        return []
    sig = ("risk", "wagon")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    wagon.meters["risk"] += 1
    for ent in list(world.entities.values()):
        if ent.role == "child":
            ent.memes["worry"] += 1
    return []


def _r_bad_fix_slips(world: World) -> list[str]:
    wagon = world.get("wagon")
    if wagon.meters["pretend_fix"] < THRESHOLD:
        return []
    sig = ("slip", "wagon")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    wagon.meters["risk"] += 1
    wagon.meters["slip"] += 1
    return []


def _r_roll_breaks(world: World) -> list[str]:
    wagon = world.get("wagon")
    if wagon.meters["rolling"] < THRESHOLD or wagon.meters["risk"] < THRESHOLD:
        return []
    sig = ("break", "wagon")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    wagon.meters["broken"] += 1
    wagon.meters["usable"] = 0.0
    for ent in list(world.entities.values()):
        if ent.role == "child":
            ent.memes["sadness"] += 1
            ent.memes["worry"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="loose_causes_risk", tag="physical", apply=_r_loose_causes_risk),
    Rule(name="bad_fix_slips", tag="physical", apply=_r_bad_fix_slips),
    Rule(name="roll_breaks", tag="physical", apply=_r_roll_breaks),
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


def tool_fits_problem(tool: Tool, problem: Problem) -> bool:
    return problem.id in tool.works_for and tool.real


def sensible_actions() -> list[HelperAction]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    if params.child_choice == "ask":
        return "safe"
    tool = TOOLS[params.tool]
    problem = PROBLEMS[params.problem]
    action = ACTIONS[params.helper_action]
    if tool_fits_problem(tool, problem) and action.power >= problem.severity:
        return "safe"
    return "bad"


def explain_tool(problem: Problem, tool: Tool) -> str:
    if not tool.real:
        return (f"(No story: {tool.label} is imaginary, so it cannot truly tighten "
                f"{problem.label}. Pick a real tool or let the child ask for help.)")
    return (f"(No story: {tool.label} does not fit the problem with {problem.label}. "
            f"Pick a tool that can really fix it.)")


def explain_action(action_id: str) -> str:
    action = ACTIONS[action_id]
    return (f"(Refusing helper action '{action_id}': it scores too low on common sense "
            f"(sense={action.sense} < {SENSE_MIN}). Choose a steadier fix.)")


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for vehicle_id in VEHICLES:
            for problem_id, problem in PROBLEMS.items():
                for tool_id, tool in TOOLS.items():
                    if tool_fits_problem(tool, problem):
                        combos.append((setting_id, vehicle_id, problem_id, tool_id))
    return combos


def predict_bad_end(world: World, tool_id: str) -> dict:
    sim = world.copy()
    wagon = sim.get("wagon")
    tool = TOOLS[tool_id]
    problem = sim.facts["problem_cfg"]
    if tool.real and problem.id in tool.works_for:
        wagon.meters["fixed"] += 1
        wagon.meters["loose"] = 0.0
        wagon.meters["usable"] = 1.0
    else:
        wagon.meters["pretend_fix"] += 1
    wagon.meters["rolling"] += 1
    propagate(sim, narrate=False)
    return {
        "broken": wagon.meters["broken"] >= THRESHOLD,
        "risk": wagon.meters["risk"],
    }


def introduce(world: World, child: Entity, setting: Setting, vehicle: Vehicle) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In {setting.place}, where breezes puffed light and thin, "
        f"{child.id} pulled {vehicle.label} with a picnic tucked within."
    )
    world.say(
        f"The path ran by {setting.path}, the grass was soft and green, "
        f"and all the little morning felt as bright as it had been."
    )


def ruffle_beat(world: World, child: Entity, setting: Setting) -> None:
    child.memes["surprise"] += 1
    world.say(
        f"A sudden ruffle stirred the leaves and danced through hair and hat; "
        f"it made the napkins flutter up and made {child.id} laugh at that."
    )


def spot_problem(world: World, child: Entity, vehicle: Vehicle, problem: Problem) -> None:
    wagon = world.get("wagon")
    wagon.meters["loose"] = 1.0
    wagon.meters["usable"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But then {vehicle.wheel_part} gave a wobble, weak and small, "
        f"and {problem.sign}, which made the wagon tilt and crawl."
    )
    world.say(
        f"{child.id} knelt down close to look and listen at the sound. "
        f"{problem.consequence.capitalize()} if no safe fix was found."
    )


def flashback(world: World, child: Entity, helper: Entity, tool: Tool) -> None:
    child.memes["memory"] += 1
    world.say(
        f"Back came a flashback, clear and quick, from just the day before: "
        f'"If wheels act loose," said {helper.label_word}, "stop first and check once more."'
    )
    if tool.real:
        world.say(
            f'{helper.label_word.capitalize()} had shown a {tool.label} then, with careful hand and eye: '
            f'"Real tools can help when grown-ups guide, but guessing should not try."'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} had smiled at make-believe, then gently added too, '
            f'"An imaginary {tool.label} is fun for games, not work to do."'
        )


def choose_pretend(world: World, child: Entity, tool: Tool) -> None:
    child.memes["confidence"] += 1
    world.say(
        f'"I know!" cried {child.id}. "I can be quick. I know just what to fetch. '
        f"I'll fix it with my {tool.label} and give the bolt a stretch."
    )


def choose_ask(world: World, child: Entity, helper: Entity) -> None:
    child.memes["trust"] += 1
    world.say(
        f'"I should not guess," thought {child.id} at last. "I know a safer bench. '
        f"I'll call {helper.label_word} here to help with every wrench."
    )


def attempt_fix(world: World, child: Entity, tool: Tool, problem: Problem) -> None:
    wagon = world.get("wagon")
    if tool.real and problem.id in tool.works_for:
        wagon.meters["fixed"] += 1
        wagon.meters["loose"] = 0.0
        wagon.meters["usable"] = 1.0
        world.say(
            f"{child.id} held still, then passed the {tool.label} up with care. "
            f"A grown-up checked the wheel and snugged the loose bolt there."
        )
    else:
        wagon.meters["pretend_fix"] += 1
        propagate(world, narrate=False)
        world.say(
            f"But make-believe can mime a turn; it cannot truly clench. "
            f"The wheel stayed loose beneath the touch of that imaginary {tool.label} wrench."
        )


def helper_rescue(world: World, helper: Entity, action: HelperAction, problem: Problem) -> bool:
    wagon = world.get("wagon")
    if action.power >= problem.severity:
        wagon.meters["fixed"] += 1
        wagon.meters["loose"] = 0.0
        wagon.meters["usable"] = 1.0
        world.say(
            f"{helper.label_word.capitalize()} came close and {action.text}. "
            f"The wheel sat snug and straight again, a safer little scene."
        )
        return True
    world.say(
        f"{helper.label_word.capitalize()} {action.fail}. "
        f"The wagon still looked shaky, and the path no longer green."
    )
    return False


def roll_on(world: World, child: Entity, vehicle: Vehicle) -> None:
    wagon = world.get("wagon")
    wagon.meters["rolling"] += 1
    propagate(world, narrate=False)
    if wagon.meters["broken"] >= THRESHOLD:
        world.say(
            f"They tugged the {vehicle.label} one more time; then came a clack and lurch. "
            f"The wheel bent wrong, the basket tipped, and jam rolled in the dirt by the birch."
        )
    else:
        world.say(
            f"Soon {vehicle.label} rolled smooth and true along the sunny track. "
            f"No wobble sang beneath the wheel and no one needed back."
        )


def safe_ending(world: World, child: Entity, setting: Setting, vehicle: Vehicle) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(
        f"They spread the cloth for {setting.outing}, and every cup stayed right. "
        f"{child.id} learned that careful help can turn a fright to light."
    )
    world.say(
        f"Since then, when bolts or puzzles shook, {child.pronoun()} paused before the plunge: "
        f"real plans beat pretend repairs when wheels must carry lunch."
    )


def bad_ending(world: World, child: Entity, setting: Setting, vehicle: Vehicle) -> None:
    child.memes["sadness"] += 1
    world.say(
        f"The bread was squashed, the berries burst, and ants found crumbs for lunch. "
        f"{child.id} stood still beside the grass and felt a sorry hunch."
    )
    world.say(
        f"No picnic song was sung that noon in {setting.place} by the bench. "
        f"{child.id} learned too late that play is play, but work needs more than an imaginary wrench."
    )
@dataclass
class StoryParams:
    setting: str
    vehicle: str
    problem: str
    tool: str
    helper_action: str
    child_name: str
    child_gender: str
    helper_type: str
    child_choice: str = "pretend"
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
    "imaginary": [(
        "What does imaginary mean?",
        "Imaginary means something you picture in your mind instead of something real in your hands. Imaginary things are wonderful for games, but they cannot tighten a wheel."
    )],
    "wrench": [(
        "What is a wrench?",
        "A wrench is a tool used to turn nuts or bolts. A real wrench helps hold metal tight so wheels do not wobble."
    )],
    "ruffle": [(
        "What can a breeze ruffle?",
        "A breeze can ruffle hair, leaves, cloth, or paper. It means the air stirs things with a light little flutter."
    )],
    "wheel": [(
        "Why is a loose wheel dangerous?",
        "A loose wheel can wobble and come off. Then the thing it carries may tip over or break."
    )],
    "repair": [(
        "What should you do when something with wheels seems broken?",
        "Stop using it and ask a grown-up or get the right tool. Moving a wobbly wheel can make the damage worse."
    )],
    "home": [(
        "Why might someone walk home for better tools?",
        "Because the safest fix sometimes means waiting for the right tool. A slow safe plan is better than a fast risky guess."
    )],
}
KNOWLEDGE_ORDER = ["imaginary", "wrench", "ruffle", "wheel", "repair", "home"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    problem = f["problem_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    prompts = [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the words "imaginary", "wrench", and "ruffle".',
        f"Tell a rhyming story where {child.id} finds {problem.label} on the way to {setting.outing} and must solve the problem safely.",
        f"Write a story with a flashback to earlier advice about tools, ending with a lesson about real help and careful choices.",
    ]
    if outcome == "bad":
        prompts.append(
            f"Give the story a bad ending where a pretend fix fails, the outing is spoiled, and the lesson lands clearly but gently."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    vehicle = f["vehicle_cfg"]
    problem = f["problem_cfg"]
    tool = f["tool_cfg"]
    action = f["action_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was pulling {vehicle.label} toward {setting.outing}, and {helper.label_word} who had given advice before. The trouble began when {problem.label} made the ride wobble."
        ),
        (
            "What problem did the child notice?",
            f"{child.id} noticed {problem.label}. That mattered because {problem.consequence}, so the wagon was not safe to keep pulling."
        ),
        (
            "What was the flashback about?",
            f"{child.id} remembered earlier advice from {helper.label_word} about stopping first and checking a loose wheel. The memory mattered because it pointed toward a real safe fix instead of guessing."
        ),
    ]
    if f["child_choice"] == "pretend":
        qa.append(
            (
                f"Why did using the {tool.label} not solve the problem?",
                f"It did not solve the problem because the {tool.label} was not a real tool that could tighten the wheel. It only looked brave in {child.id}'s mind, while the loose metal stayed loose."
            )
        )
    else:
        qa.append(
            (
                f"Why did {child.id} call for help?",
                f"{child.id} stopped and called for help because the wheel problem needed a careful fix. The flashback made {child.pronoun()} remember that real tools and grown-up guidance were safer than guessing."
            )
        )
    if f["outcome"] == "bad":
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly: the wagon broke, the food spilled, and the picnic was spoiled. That happened because the loose wheel was not fixed safely before they rolled on."
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child.id} learned that make-believe is lovely for play, but not for repairs. When something real is loose or broken, the right tool and a careful helper matter."
            )
        )
    else:
        qa.append(
            (
                f"How was the problem solved?",
                f"The problem was solved when {helper.label_word} {action.qa_text}. Because they stopped in time, the wagon could roll safely again."
            )
        )
        qa.append(
            (
                "How did the ending prove things changed?",
                f"The ending showed the change because the picnic could happen after the safe repair. {child.id} also understood that pausing for real help is part of being wise."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["tool_cfg"].tags) | set(f["problem_cfg"].tags)
    tags.add("ruffle")
    tags |= set(f["action_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="meadow",
        vehicle="wagon",
        problem="loose_nut",
        tool="imaginary_wrench",
        helper_action="tighten",
        child_name="Nell",
        child_gender="girl",
        helper_type="mother",
        child_choice="pretend",
    ),
    StoryParams(
        setting="orchard",
        vehicle="cart",
        problem="crooked_bolt",
        tool="imaginary_wrench",
        helper_action="tighten",
        child_name="Finn",
        child_gender="boy",
        helper_type="father",
        child_choice="pretend",
    ),
    StoryParams(
        setting="pond",
        vehicle="wagon",
        problem="loose_nut",
        tool="small_wrench",
        helper_action="tighten",
        child_name="Mara",
        child_gender="girl",
        helper_type="mother",
        child_choice="ask",
    ),
    StoryParams(
        setting="orchard",
        vehicle="cart",
        problem="crooked_bolt",
        tool="socket_key",
        helper_action="walk_home",
        child_name="Owen",
        child_gender="boy",
        helper_type="father",
        child_choice="ask",
    ),
    StoryParams(
        setting="meadow",
        vehicle="wagon",
        problem="loose_nut",
        tool="small_wrench",
        helper_action="walk_home",
        child_name="Tilly",
        child_gender="girl",
        helper_type="mother",
        child_choice="pretend",
    ),
]


ASP_RULES = r"""
% valid tool/problem pairs for ordinary generation
valid(S, V, P, T) :- setting(S), vehicle(V), problem(P), tool(T), real(T), works_for(T, P).

% outcome model
safe_choice :- child_choice(ask).

tool_succeeds :- chosen_tool(T), chosen_problem(P), real(T), works_for(T, P).
action_succeeds :- chosen_action(A), chosen_problem(P), power(A, Pw), severity(P, Sv), Pw >= Sv.

outcome(safe) :- safe_choice, action_succeeds.
outcome(safe) :- not safe_choice, tool_succeeds.
outcome(safe) :- not safe_choice, not tool_succeeds, action_succeeds.
outcome(bad)  :- not outcome(safe).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for vid in VEHICLES:
        lines.append(asp.fact("vehicle", vid))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("severity", pid, problem.severity))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.real:
            lines.append(asp.fact("real", tid))
        for p in sorted(tool.works_for):
            lines.append(asp.fact("works_for", tid, p))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, action.sense))
        lines.append(asp.fact("power", aid, action.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_problem", params.problem),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_action", params.helper_action),
            asp.fact("child_choice", params.child_choice),
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

    good_actions = {aid for aid, a in ACTIONS.items() if a.sense >= SENSE_MIN}
    if not good_actions:
        rc = 1
        print("MISMATCH: no sensible helper actions available.")
    else:
        print(f"OK: sensible helper actions available ({sorted(good_actions)}).")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or not isinstance(sample.story, str):
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: a loose wagon wheel, a flashback, and a careful or bad ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper-action", choices=ACTIONS, dest="helper_action")
    ap.add_argument("--choice", choices=["pretend", "ask"], dest="child_choice")
    ap.add_argument("--gender", choices=["girl", "boy"], dest="child_gender")
    ap.add_argument("--helper", choices=["mother", "father"], dest="helper_type")
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (setting, vehicle, problem, tool) combos")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.problem and args.child_choice != "ask":
        problem = PROBLEMS[args.problem]
        tool = TOOLS[args.tool]
        if not tool_fits_problem(tool, problem):
            raise StoryError(explain_tool(problem, tool))
    if args.helper_action and ACTIONS[args.helper_action].sense < SENSE_MIN:
        raise StoryError(explain_action(args.helper_action))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.vehicle is None or combo[1] == args.vehicle)
        and (args.problem is None or combo[2] == args.problem)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if args.child_choice == "ask":
        setting = args.setting or rng.choice(sorted(SETTINGS))
        vehicle = args.vehicle or rng.choice(sorted(VEHICLES))
        problem = args.problem or rng.choice(sorted(PROBLEMS))
        tool = args.tool or rng.choice(sorted(TOOLS))
    else:
        if not combos:
            raise StoryError("(No valid combination matches the given options.)")
        setting, vehicle, problem, tool = rng.choice(sorted(combos))

    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    helper_action = args.helper_action or rng.choice(sorted(a.id for a in sensible_actions()))
    child_choice = args.child_choice or rng.choice(["pretend", "ask", "pretend"])

    if child_choice == "pretend" and args.tool is not None and args.problem is not None:
        if not tool_fits_problem(TOOLS[tool], PROBLEMS[problem]):
            raise StoryError(explain_tool(PROBLEMS[problem], TOOLS[tool]))

    return StoryParams(
        setting=setting,
        vehicle=vehicle,
        problem=problem,
        tool=tool,
        helper_action=helper_action,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        child_choice=child_choice,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.vehicle not in VEHICLES:
        raise StoryError(f"(Unknown vehicle: {params.vehicle})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.helper_action not in ACTIONS:
        raise StoryError(f"(Unknown helper action: {params.helper_action})")
    if params.child_choice not in {"pretend", "ask"}:
        raise StoryError(f"(Unknown child choice: {params.child_choice})")
    if ACTIONS[params.helper_action].sense < SENSE_MIN:
        raise StoryError(explain_action(params.helper_action))
    if params.child_choice == "pretend" and not (tool_fits_problem(TOOLS[params.tool], PROBLEMS[params.problem]) or TOOLS[params.tool].id == "imaginary_wrench"):
        raise StoryError(explain_tool(PROBLEMS[params.problem], TOOLS[params.tool]))

    world = tell(
        SETTINGS[params.setting],
        VEHICLES[params.vehicle],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        ACTIONS[params.helper_action],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        child_choice=params.child_choice,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, vehicle, problem, tool) combos:\n")
        for setting, vehicle, problem, tool in combos:
            print(f"  {setting:8} {vehicle:7} {problem:12} {tool}")
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
                f"### {p.child_name}: {p.problem} with {p.tool} "
                f"({p.setting}, {p.vehicle}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    setting: Setting,
    vehicle: Vehicle,
    problem: Problem,
    tool: Tool,
    helper_action: HelperAction,
    *,
    child_name: str = "Nell",
    child_gender: str = "girl",
    helper_type: str = "mother",
    child_choice: str = "pretend",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the helper"))
    wagon = world.add(Entity(id="wagon", kind="thing", type="wagon", label=vehicle.label))
    wagon.meters["loose"] = 0.0
    wagon.meters["usable"] = 0.0
    wagon.meters["rolling"] = 0.0
    wagon.meters["broken"] = 0.0
    wagon.meters["fixed"] = 0.0
    wagon.meters["pretend_fix"] = 0.0
    wagon.meters["risk"] = 0.0
    wagon.meters["slip"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["memory"] = 0.0
    child.memes["sadness"] = 0.0
    child.memes["relief"] = 0.0

    world.facts.update(
        setting=setting,
        vehicle_cfg=vehicle,
        problem_cfg=problem,
        tool_cfg=tool,
        action_cfg=helper_action,
        child=child,
        helper=helper,
    )

    introduce(world, child, setting, vehicle)
    ruffle_beat(world, child, setting)

    world.para()
    spot_problem(world, child, vehicle, problem)
    flashback(world, child, helper, tool)

    world.para()
    if child_choice == "ask":
        choose_ask(world, child, helper)
        rescued = helper_rescue(world, helper, helper_action, problem)
        if not rescued:
            roll_on(world, child, vehicle)
    else:
        choose_pretend(world, child, tool)
        attempt_fix(world, child, tool, problem)
        if world.get("wagon").meters["fixed"] < THRESHOLD:
            rescued = helper_rescue(world, helper, helper_action, problem)
            if not rescued:
                roll_on(world, child, vehicle)
        else:
            rescued = True

    world.para()
    if world.get("wagon").meters["broken"] >= THRESHOLD:
        bad_ending(world, child, setting, vehicle)
        outcome = "bad"
    else:
        safe_ending(world, child, setting, vehicle)
        outcome = "safe"

    world.facts.update(
        child_choice=child_choice,
        outcome=outcome,
        rescued=world.get("wagon").meters["fixed"] >= THRESHOLD and world.get("wagon").meters["broken"] < THRESHOLD,
        broken=world.get("wagon").meters["broken"] >= THRESHOLD,
        remembered=child.memes["memory"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="the meadow lane",
        path="a clover path",
        breeze="soft",
        outing="a small picnic",
        tags={"meadow", "picnic"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the orchard path",
        path="rows of apple trees",
        breeze="sweet",
        outing="a snack under the trees",
        tags={"orchard", "picnic"},
    ),
    "pond": Setting(
        id="pond",
        place="the pond trail",
        path="the reeds by the water",
        breeze="cool",
        outing="a bread-and-berry lunch",
        tags={"pond", "picnic"},
    ),
}

VEHICLES = {
    "wagon": Vehicle(
        id="wagon",
        label="the little red wagon",
        cargo="a picnic basket",
        wheel_part="the left wheel nut",
        tags={"wagon"},
    ),
    "cart": Vehicle(
        id="cart",
        label="the small blue cart",
        cargo="a lunch tin",
        wheel_part="the front wheel bolt",
        tags={"cart"},
    ),
}

PROBLEMS = {
    "loose_nut": Problem(
        id="loose_nut",
        label="the loose wheel nut",
        severity=2,
        sign="it clicked against the rim",
        consequence="the basket might spill",
        tags={"wheel", "loose"},
    ),
    "crooked_bolt": Problem(
        id="crooked_bolt",
        label="the crooked wheel bolt",
        severity=3,
        sign="it scraped with a scratchy squeak",
        consequence="the wheel might twist free",
        tags={"wheel", "bolt"},
    ),
}

TOOLS = {
    "imaginary_wrench": Tool(
        id="imaginary_wrench",
        label="imaginary wrench",
        kind="pretend",
        real=False,
        works_for=set(),
        tags={"imaginary", "wrench"},
    ),
    "small_wrench": Tool(
        id="small_wrench",
        label="small wrench",
        kind="real",
        real=True,
        works_for={"loose_nut"},
        tags={"wrench", "tool"},
    ),
    "socket_key": Tool(
        id="socket_key",
        label="socket key",
        kind="real",
        real=True,
        works_for={"loose_nut", "crooked_bolt"},
        tags={"tool"},
    ),
}

ACTIONS = {
    "tighten": HelperAction(
        id="tighten",
        label="tighten the wheel",
        sense=3,
        power=3,
        text="steadied the wagon and tightened the wheel the proper way",
        fail="tried to tighten the crooked wheel, but the bent metal would not sit right",
        qa_text="steadied the wagon and tightened the wheel the proper way",
        tags={"repair"},
    ),
    "walk_home": HelperAction(
        id="walk_home",
        label="walk home for better tools",
        sense=3,
        power=4,
        text="said they should walk home for better tools before rolling any farther",
        fail="started to lead the wagon home, but the wheel slipped before they could go",
        qa_text="chose to stop and walk home for better tools",
        tags={"repair", "home"},
    ),
    "tap_stick": HelperAction(
        id="tap_stick",
        label="tap it with a stick",
        sense=1,
        power=1,
        text="tapped at the wheel with a stick until it happened to sit still",
        fail="tapped at the wheel with a stick, but that only made the wobble worse",
        qa_text="tapped at the wheel with a stick",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Nell", "Tilly", "Mara", "Lucy", "Poppy", "Ruth"]
BOY_NAMES = ["Finn", "Owen", "Milo", "Toby", "Hugo", "Ned"]

TRAITS = ["careful", "eager", "bright", "quick", "thoughtful"]

if __name__ == "__main__":
    main()
