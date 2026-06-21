#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/romp_profession_flashback_magic_rhyming_story.py
============================================================================

A standalone story world for a tiny rhyming tale about a child at play who
tries out a grown-up profession with a magical tool. The child begins in a
carefree romp, the magic copies that wild energy, trouble starts, and a
flashback to a mentor's rhyme teaches the calmer way to work.

The world model enforces a small common-sense constraint:
a profession, magical tool, and task must actually belong together.
A baker may use a whisk on batter, a gardener may use a watering can on
seedlings, and a painter may use a brush on a mural. Mismatched choices are
rejected because the story would lose its honest cause-and-effect middle.

Run it
------
    python storyworlds/worlds/gpt-5.4/romp_profession_flashback_magic_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/romp_profession_flashback_magic_rhyming_story.py --profession baker
    python storyworlds/worlds/gpt-5.4/romp_profession_flashback_magic_rhyming_story.py --profession gardener --task batter
    python storyworlds/worlds/gpt-5.4/romp_profession_flashback_magic_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/romp_profession_flashback_magic_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/romp_profession_flashback_magic_rhyming_story.py --verify
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
CALM_GOAL = 3


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
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Profession:
    id: str
    label: str
    place: str
    opening: str
    work_verb: str
    careful_verb: str
    tool_id: str
    task_id: str
    finish_image: str
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
class MagicTool:
    id: str
    label: str
    phrase: str
    action: str
    wild_effect: str
    calm_effect: str
    mishap_noun: str
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
class Task:
    id: str
    label: str
    phrase: str
    opening_image: str
    wild_mess: str
    saved_image: str
    spoiled_image: str
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
class Mentor:
    id: str
    type: str
    label: str
    rhyme_line1: str
    rhyme_line2: str
    gift_text: str
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


def _r_magic_mimics_romp(world: World) -> list[str]:
    child = world.get("child")
    tool = world.get("tool")
    task = world.get("task")
    if child.memes["romp"] < THRESHOLD:
        return []
    if tool.meters["awake"] < THRESHOLD:
        return []
    if child.memes["calm"] >= THRESHOLD:
        return []
    sig = ("mimic", task.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    task.meters["mess"] += 1
    child.memes["worry"] += 1
    return ["__mishap__"]


def _r_calm_repairs(world: World) -> list[str]:
    child = world.get("child")
    task = world.get("task")
    if child.memes["calm"] < THRESHOLD:
        return []
    if task.meters["mess"] < THRESHOLD:
        return []
    sig = ("repair", task.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    task.meters["mess"] = 0.0
    task.meters["saved"] += 1
    child.memes["hope"] += 1
    return ["__saved__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="magic_mimics_romp", tag="physical", apply=_r_magic_mimics_romp),
    Rule(name="calm_repairs", tag="physical", apply=_r_calm_repairs),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(profession: Profession, tool: MagicTool, task: Task) -> bool:
    return profession.tool_id == tool.id and profession.task_id == task.id


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for pid, p in PROFESSIONS.items():
        for tid in TOOLS:
            for task_id in TASKS:
                if valid_combo(p, TOOLS[tid], TASKS[task_id]):
                    out.append((pid, tid, task_id))
    return out


def predict_outcome(world: World, patience: int) -> dict:
    sim = world.copy()
    sim.get("child").memes["romp"] += 1
    propagate(sim, narrate=False)
    if patience >= CALM_GOAL:
        sim.get("child").memes["calm"] += 1
        propagate(sim, narrate=False)
    return {
        "mess": sim.get("task").meters["mess"],
        "saved": sim.get("task").meters["saved"],
    }


def introduce(world: World, child: Entity, profession: Profession, task: Task) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} skipped into {profession.place} with a hop and a stomp, "
        f"ready for a bright pretend-day romp."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} loved the sound of that grown-up profession, "
        f"and whispered, \"Today I will learn the {profession.label} profession.\""
    )
    world.say(
        f"There waited {task.opening_image}, quiet and sweet, "
        f"as if work and wonder were about to meet."
    )


def gift_flashback_setup(world: World, mentor: Mentor, tool: MagicTool) -> None:
    world.say(
        f"On a high wooden peg hung {tool.phrase}, "
        f"the very one from {mentor.label_word}'s old gift-days."
    )


def begin_work(world: World, child: Entity, tool: Entity, profession: Profession, task: Task) -> None:
    tool.meters["awake"] = 1.0
    world.say(
        f"{child.id} took up {tool.label}, and with a gleam in {child.pronoun('possessive')} eye, "
        f"began to {profession.work_verb} and sing to the sky."
    )
    world.say(
        f"But soon {child.pronoun('subject')} twirled and leaped in a whirl of delight; "
        f"playful feet turned work into a bouncing sight."
    )


def romp_too_hard(world: World, child: Entity) -> None:
    child.memes["romp"] += 1
    child.memes["pride"] += 1
    propagate(world, narrate=False)


def mishap(world: World, child: Entity, tool: MagicTool, task: Task) -> None:
    world.say(
        f"The magic loved motion and copied the romp, "
        f"so {tool.wild_effect} with a skip and a stomp."
    )
    world.say(
        f"Then {task.wild_mess}, and {child.id} stood still. "
        f"The room was too lively; the work needed skill."
    )


def flashback(world: World, child: Entity, mentor: Mentor) -> None:
    child.memes["memory"] += 1
    child.memes["love"] += 1
    world.say(
        f"At once came a flashback, gentle and warm, "
        f"to a lap-side lesson on a drizzly morn."
    )
    world.say(
        f"{mentor.label_word.capitalize()} had smiled and sung, soft and clear: "
        f"\"{mentor.rhyme_line1}\""
    )
    world.say(f"Then came the next line, like a bell to the ear: \"{mentor.rhyme_line2}\"")


def steady_hands(world: World, child: Entity, profession: Profession, task: Task) -> None:
    child.memes["calm"] += 1
    child.memes["romp"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{child.id} breathed in once and slowed {child.pronoun('possessive')} beat, "
        f"then {profession.careful_verb} with patient, magical feet."
    )
    world.say(
        f"Little by little, the trouble grew mild, "
        f"and careful hands worked where the room had run wild."
    )


def good_ending(world: World, child: Entity, profession: Profession, task: Task) -> None:
    child.memes["joy"] += 1
    child.memes["confidence"] += 1
    world.say(
        f"Soon {task.saved_image}, tidy and bright, "
        f"proof that calm magic can set things right."
    )
    world.say(
        f"{child.id} grinned at {profession.finish_image}, all shining and classic: "
        f"\"A romp can be merry, but gentle hands are the magic.\""
    )


def oops_ending(world: World, child: Entity, profession: Profession, task: Task, mentor: Mentor) -> None:
    child.memes["sadness"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"But the mess stayed messy that afternoon hour; "
        f"{task.spoiled_image} had lost some of its power."
    )
    world.say(
        f"{child.id} touched {child.pronoun('possessive')} heart and remembered the song. "
        f"Next time, {child.pronoun('subject')} promised, {child.pronoun('subject')} would start calm from the first beat along."
    )
    world.say(
        f"And though the task was not perfect that day, "
        f"{mentor.label_word}'s rhyme still showed a wiser way."
    )


def tell(
    profession: Profession,
    tool_cfg: MagicTool,
    task_cfg: Task,
    mentor_cfg: Mentor,
    child_name: str = "Lina",
    child_type: str = "girl",
    patience: int = 3,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    child.attrs["name"] = child_name
    child.attrs["patience"] = patience
    child.memes["calm"] = 0.0
    child.memes["romp"] = 0.0
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=tool_cfg.label, role="tool", tags=set(tool_cfg.tags)))
    task = world.add(Entity(id="task", kind="thing", type="task", label=task_cfg.label, role="task", tags=set(task_cfg.tags)))
    mentor = world.add(Entity(id="mentor", kind="character", type=mentor_cfg.type, label=mentor_cfg.label, role="mentor", tags=set(mentor_cfg.tags)))
    task.meters["mess"] = 0.0
    task.meters["saved"] = 0.0
    tool.meters["awake"] = 0.0

    world.facts.update(
        profession=profession,
        tool_cfg=tool_cfg,
        task_cfg=task_cfg,
        mentor_cfg=mentor_cfg,
        patience=patience,
        child_name=child_name,
    )

    introduce(world, child, profession, task_cfg)
    gift_flashback_setup(world, mentor, tool_cfg)

    world.para()
    begin_work(world, child, tool, profession, task_cfg)
    romp_too_hard(world, child)
    if task.meters["mess"] >= THRESHOLD:
        mishap(world, child, tool_cfg, task_cfg)

    world.para()
    flashback(world, child, mentor_cfg)

    if patience >= CALM_GOAL:
        steady_hands(world, child, profession, task_cfg)
        outcome = "saved"
        good_ending(world, child, profession, task_cfg)
    else:
        outcome = "spoiled"
        oops_ending(world, child, profession, task_cfg, mentor_cfg)

    world.facts.update(
        child=child,
        tool=tool,
        task=task,
        mentor=mentor,
        outcome=outcome,
        mess_started=task.meters["mess"] >= THRESHOLD or outcome == "spoiled",
        remembered=True,
    )
    return world


PROFESSIONS = {
    "baker": Profession(
        id="baker",
        label="baker",
        place="the warm kitchen",
        opening="sweet work",
        work_verb="whisk the bowl",
        careful_verb="stir the batter in patient rings",
        tool_id="whisk",
        task_id="batter",
        finish_image="a bowl smooth as moonlit cream",
        tags={"baker", "kitchen"},
    ),
    "gardener": Profession(
        id="gardener",
        label="gardener",
        place="the sunny greenhouse",
        opening="green work",
        work_verb="water the beds",
        careful_verb="pour in slow silver arcs",
        tool_id="watering_can",
        task_id="seedlings",
        finish_image="small green rows standing fresh and straight",
        tags={"gardener", "garden"},
    ),
    "painter": Profession(
        id="painter",
        label="painter",
        place="the bright art shed",
        opening="color work",
        work_verb="sweep color along the wall",
        careful_verb="brush color in neat gleaming curves",
        tool_id="brush",
        task_id="mural",
        finish_image="a wall glowing with tidy stars and hills",
        tags={"painter", "art"},
    ),
}

TOOLS = {
    "whisk": MagicTool(
        id="whisk",
        label="the silver whisk",
        phrase="a silver whisk with a twinkle at the tip",
        action="whisked",
        wild_effect="the silver whisk spun batter in frothy loops",
        calm_effect="the whisk circled softly",
        mishap_noun="splatter",
        tags={"whisk", "magic"},
    ),
    "watering_can": MagicTool(
        id="watering_can",
        label="the moon-blue watering can",
        phrase="a moon-blue watering can that hummed when lifted",
        action="poured",
        wild_effect="the can tossed sparkling water in jumpy sprays",
        calm_effect="the can poured in quiet ribbons",
        mishap_noun="splash",
        tags={"watering_can", "magic"},
    ),
    "brush": MagicTool(
        id="brush",
        label="the gold-tipped brush",
        phrase="a gold-tipped brush that shimmered with color",
        action="painted",
        wild_effect="the brush flicked bright paint in zigzags and dots",
        calm_effect="the brush glided in steady lines",
        mishap_noun="smear",
        tags={"brush", "magic"},
    ),
}

TASKS = {
    "batter": Task(
        id="batter",
        label="batter",
        phrase="a bowl of cake batter",
        opening_image="a bowl of pale batter waiting under the window light",
        wild_mess="the batter leaped in splats over the rim and onto the table",
        saved_image="the batter lay smooth in the bowl, ready for the oven",
        spoiled_image="the batter sat lumpy and splashed across the cloth",
        tags={"batter", "kitchen"},
    ),
    "seedlings": Task(
        id="seedlings",
        label="seedlings",
        phrase="a tray of tiny seedlings",
        opening_image="a tray of tiny seedlings lifting green noses from the soil",
        wild_mess="the seedlings bent under puddly splashes and muddy drips",
        saved_image="the seedlings stood pearled with just enough water",
        spoiled_image="the seedling tray looked soggy and slumped at the edges",
        tags={"seedlings", "garden"},
    ),
    "mural": Task(
        id="mural",
        label="mural",
        phrase="a chalked mural wall",
        opening_image="a chalked wall waiting for its first bright color",
        wild_mess="the mural blurred in streaks where colors bumped and ran",
        saved_image="the mural gleamed with clear stars, hills, and sky",
        spoiled_image="the mural kept a muddy blur where the colors had collided",
        tags={"mural", "art"},
    ),
}

MENTORS = {
    "grandma": Mentor(
        id="grandma",
        type="grandmother",
        label="the grandmother",
        rhyme_line1="Slow little hands make bright things grow,",
        rhyme_line2="Hush first the hurry, then magic will know.",
        gift_text="gave the tool with a soft kiss on the brow",
        tags={"grandma", "memory"},
    ),
    "grandpa": Mentor(
        id="grandpa",
        type="grandfather",
        label="the grandfather",
        rhyme_line1="Steady little hands help good work sing,",
        rhyme_line2="Calm is the secret in every bright thing.",
        gift_text="placed the tool there with a wink long ago",
        tags={"grandpa", "memory"},
    ),
}


@dataclass
class StoryParams:
    profession: str
    tool: str
    task: str
    mentor: str
    child_name: str
    child_type: str
    patience: int = 3
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
    "profession": [
        (
            "What is a profession?",
            "A profession is a kind of work someone learns to do well, like baking, painting, or gardening. People practice so they can do the job carefully and helpfully.",
        )
    ],
    "magic": [
        (
            "What makes a tool magical in a story?",
            "A magical tool can do more than an ordinary tool. In a story, it often listens to feelings or follows special rules.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick look back at something that happened earlier. It helps a character remember an important lesson or feeling.",
        )
    ],
    "whisk": [
        (
            "What does a whisk do?",
            "A whisk mixes soft foods like eggs or batter by moving them round and round. It helps make the mixture smooth.",
        )
    ],
    "watering_can": [
        (
            "What is a watering can for?",
            "A watering can carries water to plants. Its spout helps the water come out gently instead of all at once.",
        )
    ],
    "brush": [
        (
            "What does a paintbrush do?",
            "A paintbrush carries paint so you can spread color where you want it. A careful hand helps the lines stay neat.",
        )
    ],
    "batter": [
        (
            "Why should batter be mixed gently?",
            "Gentle mixing helps keep batter smooth instead of flinging it out of the bowl. Slow stirring also helps you keep the kitchen clean.",
        )
    ],
    "seedlings": [
        (
            "Why do seedlings need gentle watering?",
            "Seedlings are very young plants with small stems and roots. Too much water all at once can bend them over or wash the soil away.",
        )
    ],
    "mural": [
        (
            "Why does a mural need careful painting?",
            "A mural is a big picture on a wall, and the shapes need room to stay clear. If too many colors bump together, they can turn blurry or muddy.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "profession",
    "magic",
    "flashback",
    "whisk",
    "watering_can",
    "brush",
    "batter",
    "seedlings",
    "mural",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    profession = world.facts["profession"]
    tool_cfg = world.facts["tool_cfg"]
    task_cfg = world.facts["task_cfg"]
    outcome = world.facts["outcome"]
    ending = "happy" if outcome == "saved" else "bittersweet"
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "romp" and "profession".',
        f"Tell a magical rhyming story where {child.attrs['name']} pretends to be a {profession.label}, starts with a playful romp, and remembers a flashback lesson about using {tool_cfg.label} carefully.",
        f"Write a {ending} rhyming tale about {task_cfg.phrase}, a magical tool, and a remembered rhyme that changes how the child works.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    profession = world.facts["profession"]
    tool_cfg = world.facts["tool_cfg"]
    task_cfg = world.facts["task_cfg"]
    mentor = world.facts["mentor"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.attrs['name']}, a child pretending to learn the {profession.label} profession with a magical tool. {mentor.label_word.capitalize()} matters too, because the remembered rhyme helps guide the day.",
        ),
        (
            f"What was {child.attrs['name']} trying to do?",
            f"{child.attrs['name']} was trying to do {profession.label} work with {tool_cfg.label} and care for {task_cfg.phrase}. The child wanted the job to feel magical and fun.",
        ),
        (
            f"Why did the problem begin?",
            f"The problem began when the child turned the work into a wild romp. The magic tool copied that bouncy energy, so the {task_cfg.label} started to go wrong.",
        ),
        (
            "What happened in the flashback?",
            f"In the flashback, {mentor.label_word} was remembered singing a calm little rhyme. That memory gave the child a gentler way to move and think.",
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                f"How was the problem fixed?",
                f"{child.attrs['name']} slowed down and used calmer hands. Because the magic followed that calmer feeling, the {task_cfg.label} could be set right.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the work looking neat and bright instead of messy. The ending image shows that the child learned fun and care can belong together.",
            )
        )
    else:
        qa.append(
            (
                f"Did the task turn out perfectly?",
                f"No, the task stayed partly spoiled that day. Even so, the child still learned from the flashback and promised to begin more gently next time.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a lesson instead of a perfect fix. The child kept the rhyme in {child.pronoun('possessive')} heart, ready to use it another day.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"profession", "magic", "flashback"}
    tags |= set(world.facts["tool_cfg"].tags)
    tags |= set(world.facts["task_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        profession="baker",
        tool="whisk",
        task="batter",
        mentor="grandma",
        child_name="Lina",
        child_type="girl",
        patience=4,
    ),
    StoryParams(
        profession="gardener",
        tool="watering_can",
        task="seedlings",
        mentor="grandpa",
        child_name="Milo",
        child_type="boy",
        patience=3,
    ),
    StoryParams(
        profession="painter",
        tool="brush",
        task="mural",
        mentor="grandma",
        child_name="Nora",
        child_type="girl",
        patience=2,
    ),
]


def explain_rejection(profession: Profession, tool: MagicTool, task: Task) -> str:
    return (
        f"(No story: a {profession.label} using {tool.label} on {task.label} is not a grounded match here. "
        f"This world only tells stories where the profession, magical tool, and task honestly belong together.)"
    )


ASP_RULES = r"""
match_tool(P,T) :- profession(P), required_tool(P,T).
match_task(P,K) :- profession(P), required_task(P,K).
valid(P,T,K) :- profession(P), tool(T), task(K), match_tool(P,T), match_task(P,K).

saved :- patience(N), calm_goal(G), N >= G.
spoiled :- patience(N), calm_goal(G), N < G.
outcome(saved) :- saved.
outcome(spoiled) :- spoiled.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PROFESSIONS.items():
        lines.append(asp.fact("profession", pid))
        lines.append(asp.fact("required_tool", pid, p.tool_id))
        lines.append(asp.fact("required_task", pid, p.task_id))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for task_id in TASKS:
        lines.append(asp.fact("task", task_id))
    lines.append(asp.fact("calm_goal", CALM_GOAL))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("patience", params.patience)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "saved" if params.patience >= CALM_GOAL else "spoiled"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for patience in range(1, 6):
        cases.append(
            StoryParams(
                profession="baker",
                tool="whisk",
                task="batter",
                mentor="grandma",
                child_name="Test",
                child_type="girl",
                patience=patience,
            )
        )
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(
            StoryParams(
                profession="baker",
                tool="whisk",
                task="batter",
                mentor="grandma",
                child_name="Lina",
                child_type="girl",
                patience=4,
            )
        )
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming magical profession storyworld with flashbacks. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--profession", choices=PROFESSIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--mentor", choices=MENTORS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--patience", type=int, choices=[1, 2, 3, 4, 5])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


GIRL_NAMES = ["Lina", "Nora", "Mia", "Zoe", "Ava", "Ruby"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Leo", "Finn", "Owen"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.profession and args.tool and args.task:
        if not valid_combo(PROFESSIONS[args.profession], TOOLS[args.tool], TASKS[args.task]):
            raise StoryError(explain_rejection(PROFESSIONS[args.profession], TOOLS[args.tool], TASKS[args.task]))

    combos = [
        c
        for c in valid_combos()
        if (args.profession is None or c[0] == args.profession)
        and (args.tool is None or c[1] == args.tool)
        and (args.task is None or c[2] == args.task)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    profession, tool, task = rng.choice(sorted(combos))
    mentor = args.mentor or rng.choice(sorted(MENTORS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    patience = args.patience if args.patience is not None else rng.randint(1, 5)
    return StoryParams(
        profession=profession,
        tool=tool,
        task=task,
        mentor=mentor,
        child_name=child_name,
        child_type=child_type,
        patience=patience,
    )


def generate(params: StoryParams) -> StorySample:
    if params.profession not in PROFESSIONS:
        raise StoryError(f"(Unknown profession: {params.profession})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.task not in TASKS:
        raise StoryError(f"(Unknown task: {params.task})")
    if params.mentor not in MENTORS:
        raise StoryError(f"(Unknown mentor: {params.mentor})")
    if not valid_combo(PROFESSIONS[params.profession], TOOLS[params.tool], TASKS[params.task]):
        raise StoryError(explain_rejection(PROFESSIONS[params.profession], TOOLS[params.tool], TASKS[params.task]))

    world = tell(
        profession=PROFESSIONS[params.profession],
        tool_cfg=TOOLS[params.tool],
        task_cfg=TASKS[params.task],
        mentor_cfg=MENTORS[params.mentor],
        child_name=params.child_name,
        child_type=params.child_type,
        patience=params.patience,
    )
    world.get("child").id = params.child_name
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
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
        print(f"{len(combos)} compatible (profession, tool, task) combos:\n")
        for profession, tool, task in combos:
            print(f"  {profession:10} {tool:14} {task}")
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
            header = f"### {p.child_name}: {p.profession} with {p.tool} on {p.task} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
