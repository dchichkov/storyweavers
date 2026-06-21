#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/invert_sandbox_sharing_reconciliation_heartwarming.py
=================================================================================

A standalone story world about a sandbox misunderstanding: one child is carefully
finishing a sand creation, another child wants the same tool right away, a grab
makes the sand shape slump, and the children learn to share and make up.

The seed asked for:
- the word "invert"
- a sandbox setting
- sharing
- reconciliation
- a heartwarming tone

This world models a small, state-driven domain rather than swapping nouns into a
fixed paragraph. The children's feelings and the physical state of the sand toy
drive the middle turn and the ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/invert_sandbox_sharing_reconciliation_heartwarming.py
    python storyworlds/worlds/gpt-5.4/invert_sandbox_sharing_reconciliation_heartwarming.py --project castle --tool bucket
    python storyworlds/worlds/gpt-5.4/invert_sandbox_sharing_reconciliation_heartwarming.py --repair wait_turn
    python storyworlds/worlds/gpt-5.4/invert_sandbox_sharing_reconciliation_heartwarming.py --asp
    python storyworlds/worlds/gpt-5.4/invert_sandbox_sharing_reconciliation_heartwarming.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    portable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Project:
    id: str
    label: str
    phrase: str
    shape_word: str
    needs_tool: str
    careful_line: str
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    article: str
    release_text: str
    plural: bool = False
    invertible: bool = True
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
class Repair:
    id: str
    label: str
    needs_reset: bool
    success_text: str
    lesson_text: str
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
        return [e for e in self.entities.values() if e.role in {"builder", "wanter"}]

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


def _r_grab_causes_slump(world: World) -> list[str]:
    toy = world.get("tool")
    sand = world.get("shape")
    if toy.meters["grabbed"] < THRESHOLD or sand.meters["packed"] < THRESHOLD:
        return []
    sig = ("slump",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sand.meters["collapsed"] += 1
    sand.meters["standing"] = 0.0
    for kid in world.kids():
        kid.memes["upset"] += 1
    world.get("builder").memes["sad"] += 1
    world.get("wanter").memes["guilt_seed"] += 1
    return ["__collapse__"]


def _r_apology_softens(world: World) -> list[str]:
    if world.get("wanter").memes["apology"] < THRESHOLD:
        return []
    sig = ("soften",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("builder").memes["anger"] = 0.0
    world.get("builder").memes["forgiveness"] += 1
    world.get("wanter").memes["relief"] += 1
    return []


def _r_help_rebuilds(world: World) -> list[str]:
    if world.get("wanter").memes["helping"] < THRESHOLD:
        return []
    sand = world.get("shape")
    tool = world.get("tool")
    sig = ("rebuild",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sand.meters["packed"] += 1
    if tool.meters["shared"] >= THRESHOLD:
        sand.meters["standing"] = 1.0
        sand.meters["collapsed"] = 0.0
    for kid in world.kids():
        kid.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="grab_causes_slump", tag="physical", apply=_r_grab_causes_slump),
    Rule(name="apology_softens", tag="social", apply=_r_apology_softens),
    Rule(name="help_rebuilds", tag="social", apply=_r_help_rebuilds),
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
        for sent in produced:
            world.say(sent)
    return produced


PROJECTS = {
    "castle": Project(
        id="castle",
        label="castle",
        phrase="a tall sand castle with two lumpy towers",
        shape_word="castle",
        needs_tool="bucket",
        careful_line="The towers needed one last pat before the bucket came off.",
        ending_image="two little flags of grass stood on the finished castle",
        tags={"castle", "sharing"},
    ),
    "turtle": Project(
        id="turtle",
        label="turtle",
        phrase="a round sand turtle with pebble eyes",
        shape_word="turtle",
        needs_tool="turtle_mold",
        careful_line="The shell needed a gentle tap before the mold came away.",
        ending_image="the pebble eyes looked up at them from the turtle's sandy face",
        tags={"turtle", "sharing"},
    ),
    "cupcake": Project(
        id="cupcake",
        label="cupcake",
        phrase="a pretend sand cupcake with a shell on top",
        shape_word="cupcake",
        needs_tool="cup",
        careful_line="The top had to stay smooth until the cup came off.",
        ending_image="a shiny shell sat on the cupcake like a cherry",
        tags={"cupcake", "sharing"},
    ),
}

TOOLS = {
    "bucket": ToolCfg(
        id="bucket",
        label="bucket",
        phrase="a red bucket",
        article="the bucket",
        release_text="lifted the bucket and then invert it onto the sand",
        plural=False,
        invertible=True,
        tags={"bucket", "sandbox_tool"},
    ),
    "turtle_mold": ToolCfg(
        id="turtle_mold",
        label="turtle mold",
        phrase="a green turtle mold",
        article="the turtle mold",
        release_text="pressed the mold down and then invert it with a tiny wiggle",
        plural=False,
        invertible=True,
        tags={"mold", "sandbox_tool"},
    ),
    "cup": ToolCfg(
        id="cup",
        label="cup",
        phrase="a striped cup",
        article="the cup",
        release_text="packed the cup full and then invert it very slowly",
        plural=False,
        invertible=True,
        tags={"cup", "sandbox_tool"},
    ),
    "shovel": ToolCfg(
        id="shovel",
        label="shovel",
        phrase="a blue shovel",
        article="the shovel",
        release_text="scraped sand into a pile",
        plural=False,
        invertible=False,
        tags={"shovel", "sandbox_tool"},
    ),
}

REPAIRS = {
    "wait_turn": Repair(
        id="wait_turn",
        label="take turns",
        needs_reset=False,
        success_text="They decided to take turns: one child finished a careful lift, and then the other used the tool for the next shape.",
        lesson_text="Waiting for a turn let both children use the same toy without grabbing.",
        tags={"turns", "sharing"},
    ),
    "rebuild_together": Repair(
        id="rebuild_together",
        label="rebuild together",
        needs_reset=True,
        success_text="They pressed the sand together again, patted the sides, and rebuilt the shape as a team.",
        lesson_text="Working together turned the mistake into a shared project.",
        tags={"teamwork", "reconciliation"},
    ),
    "apology_and_share": Repair(
        id="apology_and_share",
        label="apologize and share",
        needs_reset=True,
        success_text="First came a sorry, then small helping hands, and then a plan to share the tool gently.",
        lesson_text="The apology mattered because it showed the grab had hurt both the sand shape and a friend's feelings.",
        tags={"apology", "reconciliation", "sharing"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
TRAITS = ["patient", "sunny", "careful", "eager", "gentle", "bouncy"]


def required_tool(project_id: str) -> str:
    return PROJECTS[project_id].needs_tool


def valid_combo(project_id: str, tool_id: str, repair_id: str) -> bool:
    tool = TOOLS[tool_id]
    repair = REPAIRS[repair_id]
    if required_tool(project_id) != tool_id:
        return False
    if not tool.invertible:
        return False
    if repair_id == "wait_turn":
        return True
    if repair.needs_reset:
        return True
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for project_id in PROJECTS:
        for tool_id in TOOLS:
            for repair_id in REPAIRS:
                if valid_combo(project_id, tool_id, repair_id):
                    out.append((project_id, tool_id, repair_id))
    return out


def explain_rejection(project_id: str, tool_id: str, repair_id: Optional[str] = None) -> str:
    project = PROJECTS.get(project_id)
    tool = TOOLS.get(tool_id)
    if project is None or tool is None:
        return "(No story: unknown project or tool.)"
    if required_tool(project_id) != tool_id:
        right = TOOLS[required_tool(project_id)].label
        return (
            f"(No story: a {project.label} in this sandbox world is made by packing sand into "
            f"{right} and lifting it carefully. {tool.label.capitalize()} would not make the "
            f"same shape, so the sharing conflict would not be honest.)"
        )
    if not tool.invertible:
        return (
            f"(No story: the key turn here happens when the child must invert the tool to release "
            f"the sand shape. A {tool.label} is not used that way.)"
        )
    if repair_id is not None and repair_id not in REPAIRS:
        return "(No story: unknown repair choice.)"
    return "(No story: this combination does not fit the world's sharing logic.)"


def predict_grab(world: World) -> dict:
    sim = world.copy()
    sim.get("tool").meters["grabbed"] += 1
    propagate(sim, narrate=False)
    shape = sim.get("shape")
    return {
        "collapsed": shape.meters["collapsed"] >= THRESHOLD,
        "builder_sad": sim.get("builder").memes["sad"],
    }


def introduce(world: World, builder: Entity, wanter: Entity, project: Project, tool: ToolCfg) -> None:
    world.say(
        f"At the sandbox, {builder.id} and {wanter.id} knelt in the warm sand beside "
        f"{tool.phrase}. Sunlight made the grains sparkle like sugar."
    )
    world.say(
        f"{builder.id} was building {project.phrase}, and {wanter.id} scooped little roads around it with careful fingers."
    )


def careful_build(world: World, builder: Entity, project: Project, tool: ToolCfg) -> None:
    shape = world.get("shape")
    shape.meters["packed"] = 1.0
    builder.memes["focus"] += 1
    world.say(
        f'"Almost ready," {builder.id} whispered. {project.careful_line} '
        f'{builder.pronoun().capitalize()} had to {tool.release_text}.'
    )


def want_same_tool(world: World, wanter: Entity, tool: ToolCfg) -> None:
    wanter.memes["desire"] += 1
    world.say(
        f'{wanter.id} looked at {tool.article} and said, "Can I use it next? I want a turn too."'
    )


def unclear_answer(world: World, builder: Entity) -> None:
    builder.memes["stress"] += 1
    world.say(
        f'{builder.id} nodded, but only halfway. "Wait," {builder.pronoun()} said, still patting the sand.'
    )


def warning(world: World, wanter: Entity) -> None:
    pred = predict_grab(world)
    world.facts["predicted_collapse"] = pred["collapsed"]
    if pred["collapsed"]:
        wanter.memes["impatience"] += 1
        world.say(
            f"{wanter.id} could see the shape was not free yet, but wanting a turn right away made waiting feel very hard."
        )


def grab(world: World, wanter: Entity, tool: ToolCfg) -> None:
    world.get("tool").meters["grabbed"] += 1
    wanter.memes["grabby"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before the careful lift was done, {wanter.id} reached for {tool.article}. The sand gave a soft pluff."
    )


def collapse(world: World, builder: Entity, wanter: Entity, project: Project) -> None:
    world.say(
        f"The {project.shape_word} slumped sideways instead of standing tall. {builder.id}'s smile fell, and {wanter.id} pulled both hands back."
    )


def hurt_feelings(world: World, builder: Entity, wanter: Entity) -> None:
    builder.memes["anger"] += 1
    world.say(
        f'"I was going to share," {builder.id} said in a small hurt voice. "{builder.pronoun().capitalize()} just needed one more second."'
    )
    world.say(
        f'{wanter.id} blinked at the fallen sand and suddenly understood the mistake.'
    )


def apology(world: World, wanter: Entity, builder: Entity) -> None:
    wanter.memes["apology"] += 1
    wanter.memes["helping"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I am sorry," {wanter.id} said. "I thought you meant no, but you only meant not yet."'
    )
    world.say(
        f"{wanter.id} touched the sand gently and looked at {builder.id} instead of the toy."
    )


def repair_and_share(world: World, builder: Entity, wanter: Entity, project: Project,
                     tool: ToolCfg, repair: Repair) -> None:
    tool_ent = world.get("tool")
    shape = world.get("shape")
    tool_ent.meters["shared"] = 1.0
    if repair.needs_reset:
        shape.meters["collapsed"] = 0.0
        shape.meters["packed"] += 1.0
    propagate(world, narrate=False)
    world.say(repair.success_text)
    world.say(
        f"Together they patted the sand, held their breath, and let {builder.id} finish the careful lift before handing the tool across."
    )
    world.say(
        f"This time the {project.shape_word} held its shape. Then {wanter.id} got a turn, and {builder.id} stayed to help."
    )


def closing(world: World, builder: Entity, wanter: Entity, project: Project, repair: Repair) -> None:
    for kid in world.kids():
        kid.memes["peace"] += 1
        kid.memes["joy"] += 1
    world.say(
        f"Soon the sandbox held not one shape but two, side by side. {repair.lesson_text}"
    )
    world.say(
        f"When they looked down, {project.ending_image}, and the children smiled at each other as if the afternoon had been mended too."
    )


def tell(project: Project, tool: ToolCfg, repair: Repair,
         builder_name: str = "Lily", builder_gender: str = "girl",
         wanter_name: str = "Ben", wanter_gender: str = "boy",
         caregiver_type: str = "mother", trait_builder: str = "careful",
         trait_wanter: str = "eager") -> World:
    world = World()
    builder = world.add(Entity(
        id=builder_name,
        kind="character",
        type=builder_gender,
        role="builder",
        traits=[trait_builder],
        attrs={"likes_project": project.id},
    ))
    wanter = world.add(Entity(
        id=wanter_name,
        kind="character",
        type=wanter_gender,
        role="wanter",
        traits=[trait_wanter],
        attrs={"wants_tool": tool.id},
    ))
    caregiver = world.add(Entity(
        id="Caregiver",
        kind="character",
        type=caregiver_type,
        role="caregiver",
        label="the grown-up",
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        portable=True,
        plural=tool.plural,
    ))
    shape = world.add(Entity(
        id="shape",
        kind="thing",
        type="sand_shape",
        label=project.label,
    ))
    sandbox = world.add(Entity(
        id="sandbox",
        kind="thing",
        type="place",
        label="sandbox",
    ))

    world.facts.update(
        project=project,
        tool_cfg=tool,
        repair=repair,
        builder=builder,
        wanter=wanter,
        caregiver=caregiver,
        tool=tool_ent,
        shape=shape,
        sandbox=sandbox,
        predicted_collapse=False,
    )

    introduce(world, builder, wanter, project, tool)
    careful_build(world, builder, project, tool)

    world.para()
    want_same_tool(world, wanter, tool)
    unclear_answer(world, builder)
    warning(world, wanter)
    grab(world, wanter, tool)
    collapse(world, builder, wanter, project)
    hurt_feelings(world, builder, wanter)

    world.para()
    apology(world, wanter, builder)
    repair_and_share(world, builder, wanter, project, tool, repair)
    closing(world, builder, wanter, project, repair)

    world.facts.update(
        collapsed=shape.meters["collapsed"] < THRESHOLD and world.get("tool").meters["grabbed"] >= THRESHOLD,
        grabbed=world.get("tool").meters["grabbed"] >= THRESHOLD,
        reconciled=builder.memes["forgiveness"] >= THRESHOLD,
        shared=world.get("tool").meters["shared"] >= THRESHOLD,
        standing=shape.meters["standing"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    project: str
    tool: str
    repair: str
    builder_name: str
    builder_gender: str
    wanter_name: str
    wanter_gender: str
    caregiver: str
    builder_trait: str
    wanter_trait: str
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
    "sandbox_tool": [
        (
            "What can sandbox toys do?",
            "Sandbox toys help children scoop, pack, and shape sand. Different toys make different shapes, so children often need to take turns."
        )
    ],
    "bucket": [
        (
            "What does it mean to invert a bucket in the sand?",
            "To invert a bucket means to turn it upside down so the packed sand can slide out as one shape. If you lift too soon or grab it too quickly, the shape can fall apart."
        )
    ],
    "mold": [
        (
            "What is a sand mold?",
            "A sand mold is a toy you press into packed sand to make one special shape. When you lift it carefully, the shape stays behind."
        )
    ],
    "cup": [
        (
            "Why can a cup be used in a sandbox?",
            "A cup can hold packed sand just like a bucket, so children can turn it over and make a little sand shape. It works best when the sand is pressed in firmly."
        )
    ],
    "sharing": [
        (
            "Why is taking turns a good way to share?",
            "Taking turns lets each person use the same toy fairly. It also helps everyone know when to wait and when it is their turn."
        )
    ],
    "apology": [
        (
            "What does an apology do between friends?",
            "An apology shows that someone understands they caused hurt and wants to make things better. It opens the door for kindness and trust to come back."
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means making peace again after a problem or hurt feeling. People listen, say sorry, and choose a kinder way forward together."
        )
    ],
    "teamwork": [
        (
            "How can teamwork help fix a mistake?",
            "When people work together, one mistake does not have to stay a problem. Sharing hands and ideas can turn a broken start into a happy finish."
        )
    ],
}
KNOWLEDGE_ORDER = ["sandbox_tool", "bucket", "mold", "cup", "sharing", "apology", "reconciliation", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    project = world.facts["project"]
    tool = world.facts["tool_cfg"]
    builder = world.facts["builder"]
    wanter = world.facts["wanter"]
    repair = world.facts["repair"]
    return [
        f'Write a heartwarming sandbox story for a 3-to-5-year-old that includes the word "invert" and ends with sharing.',
        f"Tell a gentle story where {builder.id} is making a sand {project.shape_word}, {wanter.id} wants {tool.article}, and a misunderstanding is healed with an apology and {repair.label}.",
        f"Write a warm story about two children in a sandbox who almost argue over one toy, then reconcile and build something together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    builder = f["builder"]
    wanter = f["wanter"]
    project = f["project"]
    tool = f["tool_cfg"]
    repair = f["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {builder.id} and {wanter.id}, two children playing in a sandbox with one special {tool.label}. They both wanted the same toy, which is what started the trouble."
        ),
        (
            f"What was {builder.id} trying to make?",
            f"{builder.id} was trying to make {project.phrase}. The shape needed one careful moment at the end so it would stand up properly."
        ),
        (
            f"Why did {wanter.id} grab {tool.article}?",
            f"{wanter.id} wanted a turn and misunderstood {builder.id}'s quiet \"wait.\" {wanter.pronoun().capitalize()} thought it meant no, even though it really meant not yet."
        ),
        (
            f"What happened when {wanter.id} grabbed the toy?",
            f"The {project.shape_word} slumped instead of standing tall. The grab came before the sand shape was ready, so the careful lift was spoiled."
        ),
        (
            "How did the children make up?",
            f"{wanter.id} apologized and admitted the mistake, and {builder.id} listened. Then they used {repair.label} to fix the moment, which helped the hurt feelings settle too."
        ),
        (
            "How did the story end?",
            f"It ended with both children sharing the tool and making shapes side by side. The finished sand creations showed that the sandbox had become peaceful again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["tool_cfg"].tags) | set(world.facts["repair"].tags) | {"sharing", "reconciliation"}
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
        lines.append(f"  {e.id:9} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        project="castle",
        tool="bucket",
        repair="apology_and_share",
        builder_name="Lily",
        builder_gender="girl",
        wanter_name="Ben",
        wanter_gender="boy",
        caregiver="mother",
        builder_trait="careful",
        wanter_trait="eager",
    ),
    StoryParams(
        project="turtle",
        tool="turtle_mold",
        repair="rebuild_together",
        builder_name="Max",
        builder_gender="boy",
        wanter_name="Mia",
        wanter_gender="girl",
        caregiver="father",
        builder_trait="gentle",
        wanter_trait="bouncy",
    ),
    StoryParams(
        project="cupcake",
        tool="cup",
        repair="wait_turn",
        builder_name="Zoe",
        builder_gender="girl",
        wanter_name="Theo",
        wanter_gender="boy",
        caregiver="mother",
        builder_trait="patient",
        wanter_trait="sunny",
    ),
]


ASP_RULES = r"""
required_tool(castle,bucket).
required_tool(turtle,turtle_mold).
required_tool(cupcake,cup).

valid(Project, Tool, Repair) :-
    project(Project), tool(Tool), repair(Repair),
    required_tool(Project, Tool),
    invertible(Tool).

outcome(shared_happy) :- chosen_repair(wait_turn).
outcome(shared_happy) :- chosen_repair(rebuild_together).
outcome(shared_happy) :- chosen_repair(apology_and_share).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for project_id in PROJECTS:
        lines.append(asp.fact("project", project_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.invertible:
            lines.append(asp.fact("invertible", tool_id))
    for repair_id in REPAIRS:
        lines.append(asp.fact("repair", repair_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_repair", params.repair)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if params.repair in REPAIRS:
        return "shared_happy"
    return "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for case in cases:
        if asp_outcome(case) != outcome_of(case):
            rc = 1
            print(f"MISMATCH in outcome for {case}.")
            break
    else:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story or "sandbox" not in sample.story.lower():
            raise StoryError("smoke test generated an empty or off-domain story")
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming sandbox story world about sharing, misunderstanding, and reconciliation."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--builder-gender", choices=["girl", "boy"])
    ap.add_argument("--wanter-gender", choices=["girl", "boy"])
    ap.add_argument("--builder-name")
    ap.add_argument("--wanter-name")
    ap.add_argument("--caregiver", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.tool:
        if required_tool(args.project) != args.tool or not TOOLS[args.tool].invertible:
            raise StoryError(explain_rejection(args.project, args.tool, args.repair))
    if args.repair and args.repair not in REPAIRS:
        raise StoryError("(No story: unknown repair choice.)")

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.tool is None or combo[1] == args.tool)
        and (args.repair is None or combo[2] == args.repair)
    ]
    if not combos:
        if args.project and args.tool:
            raise StoryError(explain_rejection(args.project, args.tool, args.repair))
        raise StoryError("(No valid combination matches the given options.)")

    project_id, tool_id, repair_id = rng.choice(sorted(combos))
    builder_gender = args.builder_gender or rng.choice(["girl", "boy"])
    wanter_gender = args.wanter_gender or rng.choice(["girl", "boy"])
    builder_name = args.builder_name or pick_name(rng, builder_gender)
    wanter_name = args.wanter_name or pick_name(rng, wanter_gender, avoid=builder_name)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    builder_trait = rng.choice(TRAITS)
    wanter_trait = rng.choice(TRAITS)
    return StoryParams(
        project=project_id,
        tool=tool_id,
        repair=repair_id,
        builder_name=builder_name,
        builder_gender=builder_gender,
        wanter_name=wanter_name,
        wanter_gender=wanter_gender,
        caregiver=caregiver,
        builder_trait=builder_trait,
        wanter_trait=wanter_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"(No story: unknown project '{params.project}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(No story: unknown tool '{params.tool}'.)")
    if params.repair not in REPAIRS:
        raise StoryError(f"(No story: unknown repair '{params.repair}'.)")
    if not valid_combo(params.project, params.tool, params.repair):
        raise StoryError(explain_rejection(params.project, params.tool, params.repair))

    world = tell(
        project=PROJECTS[params.project],
        tool=TOOLS[params.tool],
        repair=REPAIRS[params.repair],
        builder_name=params.builder_name,
        builder_gender=params.builder_gender,
        wanter_name=params.wanter_name,
        wanter_gender=params.wanter_gender,
        caregiver_type=params.caregiver,
        trait_builder=params.builder_trait,
        trait_wanter=params.wanter_trait,
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
        print(f"{len(combos)} compatible (project, tool, repair) combos:\n")
        for project_id, tool_id, repair_id in combos:
            print(f"  {project_id:8} {tool_id:12} {repair_id}")
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
            header = f"### {p.builder_name} & {p.wanter_name}: {p.project} with {p.tool} ({p.repair})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
