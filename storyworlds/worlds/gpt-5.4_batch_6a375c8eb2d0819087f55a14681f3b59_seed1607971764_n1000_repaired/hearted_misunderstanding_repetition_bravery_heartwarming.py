#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hearted_misunderstanding_repetition_bravery_heartwarming.py
======================================================================================

A standalone storyworld about a child who misunderstands a secret surprise.

This tiny world centers on four beats:

- a warm friendship
- a repeated hidden sound that creates a misunderstanding
- one brave question
- a heartwarming reveal that changes the ending image

The word "hearted" appears naturally in the prose through phrases like
"kind-hearted" and "big-hearted".

Run it
------
    python storyworlds/worlds/gpt-5.4/hearted_misunderstanding_repetition_bravery_heartwarming.py
    python storyworlds/worlds/gpt-5.4/hearted_misunderstanding_repetition_bravery_heartwarming.py --setting shed --project welcome_sign --tool hammer
    python storyworlds/worlds/gpt-5.4/hearted_misunderstanding_repetition_bravery_heartwarming.py --tool pocketknife
    python storyworlds/worlds/gpt-5.4/hearted_misunderstanding_repetition_bravery_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/hearted_misunderstanding_repetition_bravery_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/hearted_misunderstanding_repetition_bravery_heartwarming.py --verify
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
BRAVE_TRAITS = {"brave", "steady", "openhearted"}
CLOSE_ENOUGH = 7


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    label: str
    place_line: str
    doorway: str
    ending_spot: str
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
class Project:
    id: str
    label: str
    phrase: str
    material: str
    repeated_sound: str
    repeated_line: str
    result_line: str
    clue: str
    ending_image: str
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
class Tool:
    id: str
    label: str
    phrase: str
    sound_word: str
    works_on: set[str] = field(default_factory=set)
    sense: int = 2
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
class Reason:
    id: str
    line: str
    comfort_line: str
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
            "heard_repetitions": 0,
            "secret_active": False,
            "listener_asked": False,
            "truth_spoken": False,
            "clue_seen": False,
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


def _r_repetition_stings(world: World) -> list[str]:
    listener = world.get("listener")
    if not world.facts["secret_active"]:
        return []
    if world.facts["truth_spoken"]:
        return []
    if world.facts["heard_repetitions"] < 2:
        return []
    sig = ("repetition_stings", world.facts["heard_repetitions"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    listener.memes["worry"] += 1
    listener.memes["hurt"] += 1
    return ["__misunderstanding__"]


def _r_clue_softens(world: World) -> list[str]:
    if not world.facts["clue_seen"]:
        return []
    listener = world.get("listener")
    sig = ("clue_softens",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    listener.memes["hope"] += 1
    return []


def _r_truth_heals(world: World) -> list[str]:
    if not world.facts["truth_spoken"]:
        return []
    listener = world.get("listener")
    maker = world.get("maker")
    sig = ("truth_heals",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    listener.memes["hurt"] = 0.0
    listener.memes["relief"] += 1
    maker.memes["relief"] += 1
    listener.memes["love"] += 1
    maker.memes["love"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="repetition_stings", tag="emotion", apply=_r_repetition_stings),
    Rule(name="clue_softens", tag="emotion", apply=_r_clue_softens),
    Rule(name="truth_heals", tag="emotion", apply=_r_truth_heals),
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


def tool_works(project: Project, tool: Tool) -> bool:
    return project.material in tool.works_on


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for project_id, project in PROJECTS.items():
            if project_id not in setting.affords:
                continue
            for tool_id, tool in TOOLS.items():
                if tool_works(project, tool) and tool.sense >= SENSE_MIN:
                    combos.append((setting_id, project_id, tool_id))
    return combos


def brave_enough(trait: str, closeness: int) -> bool:
    return trait in BRAVE_TRAITS or closeness >= CLOSE_ENOUGH


def outcome_of(params: "StoryParams") -> str:
    return "early" if brave_enough(params.trait, params.closeness) else "late"


def predict_hurt(world: World, repetitions: int) -> dict:
    sim = world.copy()
    sim.facts["heard_repetitions"] = repetitions
    sim.facts["secret_active"] = True
    propagate(sim, narrate=False)
    listener = sim.get("listener")
    return {
        "hurt": listener.memes["hurt"],
        "worry": listener.memes["worry"],
    }


def introduce(world: World, listener: Entity, maker: Entity, reason: Reason) -> None:
    listener.memes["trust"] += 1
    maker.memes["care"] += 1
    world.say(
        f"{listener.id} and {maker.id} were the sort of friends who noticed small feelings. "
        f"When one of them had a hard day, the other tried to make it softer."
    )
    world.say(reason.line)
    world.say(
        f"{maker.id} was a kind-hearted child, and {maker.pronoun()} wanted to do something gentle for {listener.id}."
    )


def begin_secret(world: World, maker: Entity, setting: Setting, project: Project, tool: Tool) -> None:
    maker.meters["progress"] = 0.0
    maker.attrs["project_name"] = project.label
    maker.attrs["tool_name"] = tool.label
    world.facts["secret_active"] = True
    world.say(
        f"So {maker.id} slipped to {setting.label} to make {project.phrase}. "
        f"From behind {setting.doorway} came {project.repeated_line}."
    )


def hear_once(world: World, listener: Entity, maker: Entity, project: Project) -> None:
    world.facts["heard_repetitions"] += 1
    maker.meters["progress"] += 1
    propagate(world, narrate=False)
    count = world.facts["heard_repetitions"]
    if count == 1:
        world.say(
            f"{listener.id} paused. {project.repeated_sound.capitalize()} came again from the other side, soft but busy."
        )
        world.say(f'"{maker.id}?" {listener.id} called.')
        world.say(f'"Not yet!" {maker.id} answered from inside.')
    elif count == 2:
        world.say(
            f"A little later came {project.repeated_line} once more. {listener.id} heard the same answer and felt a small pinch inside."
        )
    else:
        world.say(
            f"Then it happened again — {project.repeated_line} — and now the repeated sound felt heavier than before."
        )


def misunderstanding_beat(world: World, listener: Entity) -> None:
    if listener.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{listener.id} wondered if {maker.id} did not want company today. That thought was wrong, but it still made {listener.pronoun('object')} feel lonely."
        )


def see_clue(world: World, listener: Entity, project: Project) -> None:
    world.facts["clue_seen"] = True
    propagate(world, narrate=False)
    world.say(
        f"As {listener.id} turned away, {listener.pronoun()} noticed {project.clue} near the doorway. It did not explain everything, but it made the mystery seem softer."
    )


def brave_question(world: World, listener: Entity, maker: Entity, early: bool) -> None:
    world.facts["listener_asked"] = True
    listener.memes["bravery"] += 1
    adverb = "right then" if early else "after taking one deep breath"
    world.say(
        f"Asking felt scary, but {listener.id} was brave {adverb}. {listener.pronoun().capitalize()} knocked and said, "
        f'"Did I do something wrong, or are you making something secret?"'
    )


def reveal(world: World, listener: Entity, maker: Entity, project: Project, tool: Tool, reason: Reason) -> None:
    world.facts["truth_spoken"] = True
    propagate(world, narrate=False)
    maker.memes["care"] += 1
    listener.memes["trust"] += 1
    world.say(
        f"The door opened at once. {maker.id} looked surprised, then sorry. "
        f'"Oh no," {maker.pronoun()} said. "I was hiding the surprise, not hiding from you."'
    )
    world.say(
        f"Inside, {listener.id} saw {project.result_line}. {maker.id} explained that {tool.phrase} was making the repeated {tool.sound_word} sound while {maker.pronoun()} worked."
    )
    world.say(reason.comfort_line)


def finish_together(world: World, listener: Entity, maker: Entity, project: Project, setting: Setting) -> None:
    listener.memes["joy"] += 1
    maker.memes["joy"] += 1
    world.say(
        f"{listener.id}'s hurt feeling melted into relief. Soon the two friends were finishing {project.label} together, their heads bent close in {setting.label}."
    )
    world.say(
        f"When they were done, {project.ending_image} in {setting.ending_spot}, and both children smiled at how one brave question had made room for the truth."
    )


def tell(
    setting: Setting,
    project: Project,
    tool: Tool,
    reason: Reason,
    listener_name: str = "Lina",
    listener_gender: str = "girl",
    maker_name: str = "Owen",
    maker_gender: str = "boy",
    trait: str = "brave",
    closeness: int = 7,
    repetitions: int = 3,
) -> World:
    world = World(setting)
    listener = world.add(Entity(
        id="listener",
        kind="character",
        type=listener_gender,
        label=listener_name,
        phrase=listener_name,
        traits=[trait],
        role="listener",
        attrs={"display": listener_name, "closeness": closeness},
    ))
    maker = world.add(Entity(
        id="maker",
        kind="character",
        type=maker_gender,
        label=maker_name,
        phrase=maker_name,
        traits=["kind-hearted"],
        role="maker",
        attrs={"display": maker_name},
    ))
    workspace = world.add(Entity(
        id="workspace",
        kind="thing",
        type="place",
        label=setting.label,
        phrase=setting.label,
        attrs={"doorway": setting.doorway},
    ))

    world.facts.update({
        "setting": setting,
        "project": project,
        "tool": tool,
        "reason": reason,
        "listener_ent": listener,
        "maker_ent": maker,
        "workspace": workspace,
        "listener_name": listener_name,
        "maker_name": maker_name,
        "trait": trait,
        "closeness": closeness,
        "repetitions_target": repetitions,
    })

    introduce(world, listener, maker, reason)
    world.para()
    begin_secret(world, maker, setting, project, tool)
    for _ in range(repetitions):
        hear_once(world, listener, maker, project)
    misunderstanding_beat(world, listener)

    world.para()
    early = brave_enough(trait, closeness)
    if not early:
        see_clue(world, listener, project)
    brave_question(world, listener, maker, early=early)

    world.para()
    reveal(world, listener, maker, project, tool, reason)
    finish_together(world, listener, maker, project, setting)

    world.facts["outcome"] = "early" if early else "late"
    return world


SETTINGS = {
    "shed": Setting(
        id="shed",
        label="the little garden shed",
        place_line="the little garden shed smelled like pine and dust",
        doorway="the half-closed shed door",
        ending_spot="the sunny path outside",
        affords={"welcome_sign", "heart_chain", "birdhouse"},
        tags={"shed"},
    ),
    "porch": Setting(
        id="porch",
        label="the back porch",
        place_line="the back porch was cool and shady",
        doorway="the porch curtain",
        ending_spot="the porch steps",
        affords={"welcome_sign", "heart_chain"},
        tags={"porch"},
    ),
    "nook": Setting(
        id="nook",
        label="the reading nook by the stairs",
        place_line="the reading nook held pillows and a small basket of craft things",
        doorway="the blanket draped across the nook",
        ending_spot="the stair landing",
        affords={"heart_chain"},
        tags={"nook"},
    ),
}

PROJECTS = {
    "welcome_sign": Project(
        id="welcome_sign",
        label="a welcome sign",
        phrase="a welcome sign painted with stars",
        material="wood",
        repeated_sound="tap, tap, tap",
        repeated_line="tap, tap, tap",
        result_line="a wooden sign with bright letters and a little painted heart in one corner",
        clue="a loop of red ribbon and a card with the first letter of {listener}'s name".replace("{listener}", "the listener"),
        ending_image="the new sign leaned against the wall and glowed in the late light",
        tags={"welcome_sign", "wood"},
    ),
    "heart_chain": Project(
        id="heart_chain",
        label="a paper chain of hearts",
        phrase="a long paper chain of hearts",
        material="paper",
        repeated_sound="snip, snip, snip",
        repeated_line="snip, snip, snip",
        result_line="paper hearts linked together in a long soft line, pink and gold and red",
        clue="one tiny paper heart on the floor",
        ending_image="the heart chain fluttered gently above them",
        tags={"hearts", "paper"},
    ),
    "birdhouse": Project(
        id="birdhouse",
        label="a small birdhouse",
        phrase="a small birdhouse with a painted roof",
        material="wood",
        repeated_sound="tap, tap, tap",
        repeated_line="tap, tap, tap",
        result_line="a little birdhouse with a round door and a heart painted below it",
        clue="a dab of blue paint on the doorstep",
        ending_image="the birdhouse sat between them like a promise of small happy things",
        tags={"birdhouse", "wood"},
    ),
}

TOOLS = {
    "hammer": Tool(
        id="hammer",
        label="small hammer",
        phrase="the small hammer",
        sound_word="tap-tap",
        works_on={"wood"},
        sense=3,
        tags={"hammer", "wood"},
    ),
    "scissors": Tool(
        id="scissors",
        label="child scissors",
        phrase="the child scissors",
        sound_word="snip-snip",
        works_on={"paper"},
        sense=3,
        tags={"scissors", "paper"},
    ),
    "glue": Tool(
        id="glue",
        label="glue stick",
        phrase="the glue stick",
        sound_word="rub-rub",
        works_on={"paper"},
        sense=2,
        tags={"glue", "paper"},
    ),
    "pocketknife": Tool(
        id="pocketknife",
        label="pocketknife",
        phrase="the pocketknife",
        sound_word="scrape-scrape",
        works_on={"wood", "paper"},
        sense=1,
        tags={"knife"},
    ),
}

REASONS = {
    "first_day": Reason(
        id="first_day",
        line="That morning, school had felt long for the listener, and even playtime had not quite chased the heaviness away.",
        comfort_line='"{0}".format("I wanted to cheer you up after your hard morning,"'.replace("{0}", "") + f" {''}".rstrip(),
        tags={"school"},
    ),
    "move_in": Reason(
        id="move_in",
        line="A new family had just moved next door, and the day felt busy and unfamiliar.",
        comfort_line='"{0}".format("I thought we could finish it together and make the new neighbor feel welcome,"'.replace("{0}", "") + f" {''}".rstrip(),
        tags={"welcome"},
    ),
    "rainy": Reason(
        id="rainy",
        line="Rain had kept everyone inside, and the gray afternoon had made the house feel quieter than usual.",
        comfort_line='"{0}".format("I wanted to make something bright for our rainy day,"'.replace("{0}", "") + f" {''}".rstrip(),
        tags={"rain"},
    ),
}

# Clean up the comfort lines into ordinary prose.
REASONS["first_day"].comfort_line = '"I wanted to cheer you up after your hard morning," {maker} said.'
REASONS["move_in"].comfort_line = '"I thought we could finish it together and make the new neighbor feel welcome," {maker} said.'
REASONS["rainy"].comfort_line = '"I wanted to make something bright for our rainy day," {maker} said.'


GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Ava", "Lucy", "Zoe", "Anna"]
BOY_NAMES = ["Owen", "Leo", "Ben", "Sam", "Noah", "Finn", "Eli", "Theo"]
TRAITS = ["brave", "steady", "openhearted", "shy", "quiet", "careful"]


@dataclass
class StoryParams:
    setting: str
    project: str
    tool: str
    reason: str
    listener: str
    listener_gender: str
    maker: str
    maker_gender: str
    trait: str
    closeness: int = 7
    repetitions: int = 3
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    listener = f["listener_ent"]
    maker = f["maker_ent"]
    project = f["project"]
    setting = f["setting"]
    outcome = f["outcome"]
    timing = "asks right away" if outcome == "early" else "almost walks away, then turns back and asks"
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the word "hearted", a misunderstanding, repetition, and bravery.',
        f"Tell a gentle story where {maker.label} hides in {setting.label} to make {project.phrase}, and {listener.label} misunderstands the repeated sound.",
        f"Write a warm story in which one child hears the same secret sound again and again, feels hurt, then {timing} and learns the truth.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    listener = f["listener_ent"]
    maker = f["maker_ent"]
    project = f["project"]
    setting = f["setting"]
    tool = f["tool"]
    reason = f["reason"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {listener.label} and {maker.label}, two friends. {maker.label} wanted to make a surprise, and {listener.label} had to be brave enough to ask about it."
        ),
        (
            f"Why did {maker.label} go to {setting.label}?",
            f"{maker.label} went there to make {project.phrase}. {reason.line[0].upper() + reason.line[1:]}",
        ),
        (
            f"Why did {listener.label} feel hurt?",
            f"{listener.label} kept hearing {project.repeated_line} from behind {setting.doorway}, and each time {maker.label} said, 'Not yet.' Because the sound and the answer happened again and again, {listener.label} misunderstood and thought the secret might be about being left out."
        ),
        (
            f"Why was asking a brave thing to do?",
            f"Asking meant saying a worried feeling out loud, and that can feel scary. {listener.label} chose to ask instead of keeping the misunderstanding inside."
        ),
        (
            "What was the truth?",
            f"The truth was that {maker.label} was making {project.label}, not hiding from {listener.label}. The repeated sound came from {tool.phrase} while the surprise was being made."
        ),
    ]
    if outcome == "early":
        qa.append((
            f"How did the story end?",
            f"It ended warmly: {listener.label} asked the brave question right away, and the misunderstanding cleared quickly. After that, the two friends finished the surprise together."
        ))
    else:
        qa.append((
            f"What helped {listener.label} ask in the end?",
            f"A small clue near the doorway softened the lonely feeling and gave {listener.label} a little hope. Then {listener.pronoun('subject').capitalize()} took a breath and asked the brave question anyway."
        ))
    qa.append((
        "What changed by the last picture of the story?",
        f"At first the repeated sound made the space between the friends feel closed. By the end, they were standing together with {project.label}, and the ending image shows that the truth brought them close again."
    ))
    return qa


KNOWLEDGE = {
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something means one thing, but it really means another. Talking kindly can help clear it up."
        )
    ],
    "bravery": [
        (
            "Can asking a question be brave?",
            "Yes. It can be brave to ask a worried question because you are telling the truth about your feelings instead of hiding them."
        )
    ],
    "repetition": [
        (
            "What does repetition mean in a story?",
            "Repetition means something happens again and again, like the same sound or words coming back. It can make a feeling stronger each time."
        )
    ],
    "paper": [
        (
            "Why do scissors make a snip sound?",
            "Scissors make a snip sound because two blades slide past each other as they cut. That quick closing motion makes the little noise."
        )
    ],
    "wood": [
        (
            "Why does a hammer make a tap sound?",
            "A hammer makes a tap sound when it touches wood or a nail. The hard surfaces bump together and make the sound."
        )
    ],
    "welcome_sign": [
        (
            "What is a welcome sign for?",
            "A welcome sign tells people they are invited and wanted in a place. It helps a space feel friendly."
        )
    ],
    "hearts": [
        (
            "Why do people use hearts in decorations?",
            "Hearts are often used to show love, care, and kindness. A heart shape can make a gift feel extra warm."
        )
    ],
    "birdhouse": [
        (
            "What is a birdhouse?",
            "A birdhouse is a small house people make for birds. Birds may use it as a safe place to rest or nest."
        )
    ],
}
KNOWLEDGE_ORDER = ["misunderstanding", "repetition", "bravery", "paper", "wood", "welcome_sign", "hearts", "birdhouse"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"misunderstanding", "repetition", "bravery"} | set(f["project"].tags)
    if f["project"].material == "paper":
        tags.add("paper")
    if f["project"].material == "wood":
        tags.add("wood")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts['heard_repetitions']=}, clue_seen={world.facts['clue_seen']}, truth_spoken={world.facts['truth_spoken']}, outcome={world.facts.get('outcome')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="shed",
        project="welcome_sign",
        tool="hammer",
        reason="move_in",
        listener="Lina",
        listener_gender="girl",
        maker="Owen",
        maker_gender="boy",
        trait="brave",
        closeness=8,
        repetitions=3,
    ),
    StoryParams(
        setting="porch",
        project="heart_chain",
        tool="scissors",
        reason="rainy",
        listener="Ben",
        listener_gender="boy",
        maker="Maya",
        maker_gender="girl",
        trait="openhearted",
        closeness=6,
        repetitions=3,
    ),
    StoryParams(
        setting="nook",
        project="heart_chain",
        tool="glue",
        reason="first_day",
        listener="Nora",
        listener_gender="girl",
        maker="Theo",
        maker_gender="boy",
        trait="quiet",
        closeness=4,
        repetitions=2,
    ),
    StoryParams(
        setting="shed",
        project="birdhouse",
        tool="hammer",
        reason="rainy",
        listener="Leo",
        listener_gender="boy",
        maker="Ava",
        maker_gender="girl",
        trait="steady",
        closeness=5,
        repetitions=3,
    ),
]


def explain_tool_rejection(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    return (
        f"(Refusing tool '{tool_id}': {tool.label} scores too low on common sense "
        f"(sense={tool.sense} < {SENSE_MIN}). This world prefers child-safe, ordinary craft tools.)"
    )


def explain_combo_rejection(setting: Setting, project: Project, tool: Tool) -> str:
    if project.id not in setting.affords:
        return (
            f"(No story: {setting.label} does not fit making {project.label} in this small world. "
            f"Pick a project that belongs in that place.)"
        )
    if not tool_works(project, tool):
        return (
            f"(No story: {tool.label} does not honestly make {project.label}. "
            f"Pick a tool that works on {project.material}.)"
        )
    return "(No story: this combination is not part of the world.)"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(S, P, T) :- setting(S), project(P), tool(T), affords(S, P), material(P, M), works_on(T, M), sensible(T).
sensible(T)    :- tool(T), sense(T, X), sense_min(M), X >= M.

% --- outcome model ---------------------------------------------------------
early         :- closeness(C), close_enough(K), C >= K.
early         :- trait(T), brave_trait(T).
late          :- not early.
outcome(early) :- early.
outcome(late)  :- late.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for project_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, project_id))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("material", project_id, project.material))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        for material in sorted(tool.works_on):
            lines.append(asp.fact("works_on", tool_id, material))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("close_enough", CLOSE_ENOUGH))
    for trait in sorted(BRAVE_TRAITS):
        lines.append(asp.fact("brave_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("trait", params.trait),
        asp.fact("closeness", params.closeness),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a misunderstanding made by repeated secret sounds, then healed by one brave question."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--reason", choices=REASONS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--closeness", type=int, choices=list(range(0, 11)))
    ap.add_argument("--repetitions", type=int, choices=[2, 3], help="how many times the secret sound repeats")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool_rejection(args.tool))
    if args.setting and args.project and args.tool:
        setting = SETTINGS[args.setting]
        project = PROJECTS[args.project]
        tool = TOOLS[args.tool]
        combo = (args.setting, args.project, args.tool)
        if combo not in set(valid_combos()):
            raise StoryError(explain_combo_rejection(setting, project, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.project is None or combo[1] == args.project)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, project_id, tool_id = rng.choice(sorted(combos))
    reason_id = args.reason or rng.choice(sorted(REASONS))
    trait = args.trait or rng.choice(TRAITS)
    closeness = args.closeness if args.closeness is not None else rng.randint(3, 9)
    repetitions = args.repetitions if args.repetitions is not None else rng.choice([2, 3])
    listener_name, listener_gender = _pick_child(rng)
    maker_name, maker_gender = _pick_child(rng, avoid=listener_name)

    return StoryParams(
        setting=setting_id,
        project=project_id,
        tool=tool_id,
        reason=reason_id,
        listener=listener_name,
        listener_gender=listener_gender,
        maker=maker_name,
        maker_gender=maker_gender,
        trait=trait,
        closeness=closeness,
        repetitions=repetitions,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.reason not in REASONS:
        raise StoryError(f"(Unknown reason: {params.reason})")
    if params.tool in TOOLS and TOOLS[params.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool_rejection(params.tool))
    if (params.setting, params.project, params.tool) not in set(valid_combos()):
        raise StoryError(explain_combo_rejection(SETTINGS[params.setting], PROJECTS[params.project], TOOLS[params.tool]))

    world = tell(
        setting=SETTINGS[params.setting],
        project=PROJECTS[params.project],
        tool=TOOLS[params.tool],
        reason=REASONS[params.reason],
        listener_name=params.listener,
        listener_gender=params.listener_gender,
        maker_name=params.maker,
        maker_gender=params.maker_gender,
        trait=params.trait,
        closeness=params.closeness,
        repetitions=params.repetitions,
    )

    maker_name = world.facts["maker_ent"].label
    for item in story_qa(world):
        pass
    # Fill maker placeholder in comfort lines if it remained in prose source registry.
    story_text = world.render().replace("{maker}", maker_name)

    return StorySample(
        params=params,
        story=story_text,
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
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    py_sensible = {tool.id for tool in sensible_tools()}
    asp_sensible = set(asp_sensible_tools())
    if py_sensible == asp_sensible:
        print(f"OK: sensible tools match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: python={sorted(py_sensible)} asp={sorted(asp_sensible)}")

    parser = build_parser()
    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random seed {seed}.")
            break

    bad = 0
    for params in cases:
        if outcome_of(params) != asp_outcome(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches ASP on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        sink = io.StringIO()
        with redirect_stdout(sink):
            emit(sample, trace=True, qa=True, header="### smoke test")
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover
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
        tools = asp_sensible_tools()
        print(f"sensible tools: {', '.join(tools)}\n")
        print(f"{len(combos)} compatible (setting, project, tool) combos:\n")
        for setting, project, tool in combos:
            print(f"  {setting:8} {project:13} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.listener} & {p.maker}: {p.project} in {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
