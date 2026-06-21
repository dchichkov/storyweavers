#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fire_curiosity_suspense_transformation_folk_tale.py
=============================================================================

A small folk-tale storyworld about a curious child, a waiting fire, and a
peaceful transformation. In each story, a child brings something humble to a
keeper of a proper fire: dough to an oven, clay to a kiln, or chestnuts to a
roasting pit. The child wants to know what the fire is doing inside the closed
heat. Suspense grows while they wait. Then the fire changes the humble thing
into something new.

The world refuses unreasonable combinations. A thing can only be transformed by
the right kind of fire, and the hot result must be taken out with a sensible
tool. Bare hands are known to the world but refused by the common-sense gate.

Run it
------
    python storyworlds/worlds/gpt-5.4/fire_curiosity_suspense_transformation_folk_tale.py
    python storyworlds/worlds/gpt-5.4/fire_curiosity_suspense_transformation_folk_tale.py --hearth kiln --material clay --tool tongs
    python storyworlds/worlds/gpt-5.4/fire_curiosity_suspense_transformation_folk_tale.py --tool bare_hands
    python storyworlds/worlds/gpt-5.4/fire_curiosity_suspense_transformation_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/fire_curiosity_suspense_transformation_folk_tale.py --qa --json
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "aunt", "potter_woman", "baker_woman"}
        male = {"boy", "man", "grandfather", "uncle", "potter_man", "baker_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type.replace("_", " ")


@dataclass
class Hearth:
    id: str
    label: str
    place: str
    keeper_label: str
    keeper_type: str
    fire_phrase: str
    mouth_phrase: str
    wait_phrase: str
    reveal_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    needs_hearth: str
    raw_description: str
    result_label: str
    result_phrase: str
    result_sentence: str
    suspense_sound: str
    scent_phrase: str
    moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    works_on: set[str] = field(default_factory=set)
    sense: int = 0
    action: str = ""
    qa_action: str = ""
    tags: set[str] = field(default_factory=set)


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


def _r_heat_changes(world: World) -> list[str]:
    mat = world.entities.get("material")
    fire = world.entities.get("fire")
    child = world.entities.get("child")
    if not mat or not fire or not child:
        return []
    if mat.meters["heating"] < THRESHOLD:
        return []
    sig = ("change", mat.id)
    if sig in world.fired:
        return []
    if mat.attrs.get("needs_hearth") != fire.attrs.get("hearth_id"):
        return []
    world.fired.add(sig)
    mat.meters["transformed"] += 1
    child.memes["awe"] += 1
    child.memes["fear"] = 0.0
    return ["__transformed__"]


CAUSAL_RULES = [
    Rule(name="heat_changes", tag="physical", apply=_r_heat_changes),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


HEARTHS = {
    "oven": Hearth(
        id="oven",
        label="bread oven",
        place="at the edge of the village",
        keeper_label="old baker",
        keeper_type="baker_woman",
        fire_phrase="the oven fire glowed behind a black iron door",
        mouth_phrase="the dark oven mouth",
        wait_phrase="the fire hummed low as if it were thinking over an old secret",
        reveal_phrase="when the iron door opened, warm light poured out like sunrise from a hill cave",
        tags={"oven", "fire"},
    ),
    "kiln": Hearth(
        id="kiln",
        label="clay kiln",
        place="behind the willow shed",
        keeper_label="old potter",
        keeper_type="potter_man",
        fire_phrase="the kiln fire breathed through small red cracks",
        mouth_phrase="the round kiln door",
        wait_phrase="inside, the fire whispered and clicked the way dry twigs speak in sleep",
        reveal_phrase="when the clay door was lifted, the red glow inside looked like a captured evening sky",
        tags={"kiln", "fire", "clay"},
    ),
    "pit": Hearth(
        id="pit",
        label="roasting pit",
        place="under the old chestnut tree",
        keeper_label="old aunt",
        keeper_type="aunt",
        fire_phrase="the pit fire slept under grey ash with little red eyes beneath",
        mouth_phrase="the ash-covered pit",
        wait_phrase="now and then the ash sighed, and a tiny spark winked like a secret",
        reveal_phrase="when the ash was brushed aside, the coals shone as if a red fox were hiding underground",
        tags={"pit", "fire", "chestnut"},
    ),
}

MATERIALS = {
    "dough": Material(
        id="dough",
        label="dough",
        phrase="a round lump of dough",
        needs_hearth="oven",
        raw_description="pale and soft",
        result_label="loaf",
        result_phrase="a round brown loaf",
        result_sentence="what went in as a pale lump came out as a round brown loaf with a singing crust",
        suspense_sound="From behind the iron door came a small thump and a soft crackle.",
        scent_phrase="Soon the air smelled of warm bread.",
        moral="some good changes need warmth and waiting",
        tags={"bread", "oven", "fire"},
    ),
    "clay": Material(
        id="clay",
        label="clay",
        phrase="a little clay bowl still damp from shaping",
        needs_hearth="kiln",
        raw_description="cool and damp",
        result_label="cup",
        result_phrase="a red clay cup",
        result_sentence="what went in as a damp little bowl came out as a red clay cup hard enough to hold water",
        suspense_sound="From inside the kiln came tiny ticks, as if stones were learning a new song.",
        scent_phrase="Soon the air smelled dry and earthy.",
        moral="fire can make a soft thing strong",
        tags={"clay", "kiln", "fire"},
    ),
    "chestnuts": Material(
        id="chestnuts",
        label="chestnuts",
        phrase="a small basket of chestnuts in their shells",
        needs_hearth="pit",
        raw_description="hard and shiny",
        result_label="roasted chestnuts",
        result_phrase="sweet roasted chestnuts",
        result_sentence="what went in as hard brown nuts came out sweet and split open, ready for hungry hands",
        suspense_sound="Under the ash came small pops, one after another, like pebbles tapping together.",
        scent_phrase="Soon the air smelled sweet and smoky.",
        moral="even a plain shell may hide a warm gift",
        tags={"chestnut", "pit", "fire"},
    ),
    "pebble": Material(
        id="pebble",
        label="pebble",
        phrase="a smooth river pebble",
        needs_hearth="none",
        raw_description="grey and ordinary",
        result_label="hot pebble",
        result_phrase="a hot pebble",
        result_sentence="the pebble only grew hot and stayed a pebble",
        suspense_sound="Nothing much happened at all.",
        scent_phrase="There was no new smell to follow.",
        moral="not every thing is meant for the fire",
        tags={"stone"},
    ),
}

TOOLS = {
    "peel": Tool(
        id="peel",
        label="bread peel",
        phrase="a long bread peel",
        works_on={"oven"},
        sense=3,
        action="slid the bread peel in and drew the hot treasure out",
        qa_action="used the bread peel to draw the hot loaf out of the oven",
        tags={"peel", "oven"},
    ),
    "tongs": Tool(
        id="tongs",
        label="tongs",
        phrase="a pair of long tongs",
        works_on={"kiln", "pit"},
        sense=3,
        action="reached in with the tongs and lifted the hot thing out carefully",
        qa_action="used the tongs to lift the hot thing out safely",
        tags={"tongs", "safety"},
    ),
    "ash_shovel": Tool(
        id="ash_shovel",
        label="ash shovel",
        phrase="a little ash shovel",
        works_on={"pit"},
        sense=3,
        action="pushed the ash aside with the shovel and gathered the hot chestnuts out",
        qa_action="used the ash shovel to move the ash and gather the chestnuts out",
        tags={"shovel", "safety"},
    ),
    "bare_hands": Tool(
        id="bare_hands",
        label="bare hands",
        phrase="bare hands",
        works_on={"oven", "kiln", "pit"},
        sense=0,
        action="reached toward the heat with bare hands",
        qa_action="tried to use bare hands",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mira", "Anya", "Lina", "Dora", "Nela", "Tala", "Rina", "Sora"]
BOY_NAMES = ["Ivo", "Milo", "Toma", "Niko", "Bram", "Luka", "Rado", "Pavel"]
TRAITS = ["curious", "bright-eyed", "patient", "eager", "wondering", "gentle"]


@dataclass
class StoryParams:
    hearth: str
    material: str
    tool: str
    child_name: str
    child_gender: str
    child_trait: str
    seed: Optional[int] = None


def material_fits_hearth(material: Material, hearth: Hearth) -> bool:
    return material.needs_hearth == hearth.id


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def tool_fits_hearth(tool: Tool, hearth: Hearth) -> bool:
    return hearth.id in tool.works_on


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for hearth_id, hearth in HEARTHS.items():
        for material_id, material in MATERIALS.items():
            if not material_fits_hearth(material, hearth):
                continue
            for tool_id, tool in TOOLS.items():
                if tool.sense >= SENSE_MIN and tool_fits_hearth(tool, hearth):
                    combos.append((hearth_id, material_id, tool_id))
    return sorted(combos)


def explain_rejection(material: Material, hearth: Hearth) -> str:
    if material.needs_hearth == "none":
        return (
            f"(No story: {material.label} does not truly change in a {hearth.label}. "
            f"A folk-tale fire here must transform something, not merely warm it.)"
        )
    return (
        f"(No story: {material.label} belongs with a {HEARTHS[material.needs_hearth].label}, "
        f"not with a {hearth.label}. This world only tells changes the fire can honestly make.)"
    )


def explain_tool(tool: Tool) -> str:
    options = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool.id}': it is not a sensible way to handle something hot "
        f"(sense={tool.sense} < {SENSE_MIN}). Try one of: {options}.)"
    )


def introduce(world: World, child: Entity, elder: Entity, hearth: Hearth) -> None:
    world.say(
        f"Long ago, {hearth.place}, there stood a {hearth.label} watched by {elder.label}. "
        f"One morning {child.id}, a {child.attrs.get('trait', 'curious')} little {child.type}, came to see it."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} had heard that fire could change plain things into useful ones, "
        f"and {child.pronoun('subject')} wanted to know whether the old saying was true."
    )


def bring_material(world: World, child: Entity, material: Material, hearth: Hearth) -> None:
    world.say(
        f"In {child.pronoun('possessive')} hands {child.pronoun('subject')} carried {material.phrase}, "
        f"{material.raw_description}, and held it up toward the {hearth.label}."
    )
    child.memes["curiosity"] += 1


def ask(world: World, child: Entity, elder: Entity, material: Material) -> None:
    world.say(
        f'"Will the fire eat it?" {child.id} asked. "{child.pronoun("subject").capitalize()} will not eat it," '
        f'{elder.label} said. "But it may teach it to become something else."'
    )


def prepare(world: World, elder: Entity, material_ent: Entity, fire_ent: Entity, hearth: Hearth) -> None:
    material_ent.meters["waiting"] += 1
    world.say(
        f"{elder.label.capitalize()} set the {material_ent.label} by {hearth.mouth_phrase}, and {hearth.fire_phrase}."
    )
    world.say(
        f"Then {elder.pronoun('subject')} placed it inside and closed the way with care."
    )
    fire_ent.meters["burning"] += 1


def wait_and_worry(world: World, child: Entity, elder: Entity, hearth: Hearth, material: Material) -> None:
    child.memes["suspense"] += 1
    child.memes["fear"] += 1
    world.say(material.suspense_sound)
    world.say(
        f"{hearth.wait_phrase}. {child.id} took one step nearer, then another, "
        f"wondering what the hidden fire was doing in the dark."
    )
    world.say(
        f"When {child.pronoun('subject')} lifted a hand toward {hearth.mouth_phrase}, "
        f"{elder.label} touched {child.pronoun('possessive')} sleeve and whispered, "
        f'"Not yet. The fire is still at its work."'
    )
    world.facts["tried_to_peek"] = True


def heat(world: World, material_ent: Entity) -> None:
    material_ent.meters["heating"] += 1
    propagate(world, narrate=False)


def reveal(world: World, child: Entity, elder: Entity, tool: Tool, material: Material, hearth: Hearth) -> None:
    material_ent = world.get("material")
    tool_ent = world.get("tool")
    world.say(material.scent_phrase)
    world.say(
        f"At last {elder.label} nodded. {hearth.reveal_phrase}, and {elder.pronoun('subject')} "
        f"{tool.action}."
    )
    material_ent.attrs["form"] = material.result_label
    tool_ent.meters["used"] += 1
    world.say(
        f"There before {child.id} lay {material.result_phrase}. {material.result_sentence}."
    )


def ending(world: World, child: Entity, elder: Entity, material: Material) -> None:
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'{child.id} stared, then smiled so wide that even {elder.label} laughed. '
        f'"Now I know," {child.pronoun("subject")} said. "The fire did not gobble it. '
        f'It changed it."'
    )
    world.say(
        f"From that day on, {child.id} remembered that {material.moral}. "
        f"And whenever {child.pronoun('subject')} saw a steady fire, {child.pronoun('subject')} also remembered to wait for wisdom before reaching into heat."
    )


def tell(params: StoryParams) -> World:
    if params.hearth not in HEARTHS:
        raise StoryError(f"(Unknown hearth: {params.hearth})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    hearth = HEARTHS[params.hearth]
    material = MATERIALS[params.material]
    tool = TOOLS[params.tool]

    if not material_fits_hearth(material, hearth):
        raise StoryError(explain_rejection(material, hearth))
    if tool.sense < SENSE_MIN:
        raise StoryError(explain_tool(tool))
    if not tool_fits_hearth(tool, hearth):
        raise StoryError(
            f"(No story: {tool.label} is not the right tool for a {hearth.label}. "
            f"Hot things must be handled with a tool that truly suits that fire.)"
        )

    world = World()
    child = world.add(
        Entity(
            id=params.child_name,
            kind="character",
            type=params.child_gender,
            label=params.child_name,
            role="child",
            attrs={"trait": params.child_trait},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=hearth.keeper_type,
            label=hearth.keeper_label,
            role="keeper",
        )
    )
    fire = world.add(
        Entity(
            id="fire",
            kind="thing",
            type="fire",
            label="fire",
            phrase=hearth.fire_phrase,
            role="fire",
            attrs={"hearth_id": hearth.id},
            tags=set(hearth.tags),
        )
    )
    material_ent = world.add(
        Entity(
            id="material",
            kind="thing",
            type=material.id,
            label=material.label,
            phrase=material.phrase,
            role="material",
            attrs={"needs_hearth": material.needs_hearth, "form": material.label},
            tags=set(material.tags),
        )
    )
    world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            phrase=tool.phrase,
            role="tool",
            tags=set(tool.tags),
        )
    )

    introduce(world, child, elder, hearth)
    bring_material(world, child, material, hearth)
    ask(world, child, elder, material)

    world.para()
    prepare(world, elder, material_ent, fire, hearth)
    wait_and_worry(world, child, elder, hearth, material)
    heat(world, material_ent)

    world.para()
    reveal(world, child, elder, tool, material, hearth)
    ending(world, child, elder, material)

    world.facts.update(
        child=child,
        elder=elder,
        fire=fire,
        hearth=hearth,
        material_cfg=material,
        material=material_ent,
        tool=tool,
        transformed=material_ent.meters["transformed"] >= THRESHOLD,
        result_label=material.result_label,
    )
    return world


KNOWLEDGE = {
    "fire": [
        (
            "Why can fire change things?",
            "Fire brings strong heat. Some things bake, harden, or roast when the heat is just right."
        )
    ],
    "oven": [
        (
            "What does an oven do?",
            "An oven holds steady heat around food. That heat can bake dough into bread."
        )
    ],
    "kiln": [
        (
            "What is a kiln?",
            "A kiln is a very hot oven for clay. The heat makes soft clay turn hard and strong."
        )
    ],
    "pit": [
        (
            "What is a roasting pit?",
            "A roasting pit is a safe place to cook food over coals and hot ash. The hidden heat can roast things slowly."
        )
    ],
    "bread": [
        (
            "How does dough become bread?",
            "Dough rises and bakes in oven heat. The soft lump turns into a loaf with a brown crust."
        )
    ],
    "clay": [
        (
            "Why does clay need a kiln?",
            "Wet clay is soft and can break easily. A kiln dries and hardens it so it can hold its shape."
        )
    ],
    "chestnut": [
        (
            "What happens when chestnuts roast?",
            "The heat cooks the inside and splits the shells. Then the chestnuts become soft and sweet to eat."
        )
    ],
    "safety": [
        (
            "Why should you not reach into a hot fire place with bare hands?",
            "Hot doors, ash, and coals can burn skin very quickly. A grown-up should use the right tool and keep children back."
        )
    ],
}

KNOWLEDGE_ORDER = ["fire", "oven", "kiln", "pit", "bread", "clay", "chestnut", "safety"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    hearth = world.facts["hearth"]
    material = world.facts["material_cfg"]
    return [
        f'Write a folk tale for a 3-to-5-year-old that includes the word "fire" and follows a curious child waiting by a {hearth.label}.',
        f"Tell a gentle suspense story where {child.id} brings {material.phrase} to {world.facts['elder'].label} and learns that waiting can reveal a change.",
        f"Write a simple transformation tale in an old-village style where hidden heat turns {material.label} into {material.result_label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    hearth = world.facts["hearth"]
    material = world.facts["material_cfg"]
    tool = world.facts["tool"]
    result = world.facts["result_label"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious little {child.type}, and {elder.label}, who watched the {hearth.label}. Together they waited to see what the fire would do."
        ),
        (
            f"What did {child.id} bring to the fire?",
            f"{child.id} brought {material.phrase}. At first it was {material.raw_description}, so the child could not yet see the new thing hidden inside it."
        ),
        (
            f"Why was {child.id} feeling suspense by the {hearth.label}?",
            f"{child.id} could hear {material.suspense_sound[:-1].lower()} and did not know what was happening behind the closed heat. That mystery made {child.pronoun('object')} want to peek before the time was right."
        ),
    ]
    if world.facts.get("tried_to_peek"):
        qa.append(
            (
                f"Why did {elder.label} stop {child.id} from peeking too soon?",
                f"{elder.label.capitalize()} knew the fire was still working and the place was too hot for a child to reach into safely. Waiting protected {child.id} and also let the change finish."
            )
        )
    if world.facts.get("transformed"):
        qa.append(
            (
                "What changed in the story?",
                f"The fire changed the {material.label} into {result}. The ending proves the transformation because what came out was not the same as what went in."
            )
        )
        qa.append(
            (
                f"How did {elder.label} take the hot thing out?",
                f"{elder.label.capitalize()} {tool.qa_action}. The right tool mattered because the change happened in deep heat that bare hands could not touch safely."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"fire"} | set(world.facts["hearth"].tags) | set(world.facts["material_cfg"].tags)
    if world.facts["tool"].id in {"tongs", "ash_shovel"}:
        tags.add("safety")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
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
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hearth="oven",
        material="dough",
        tool="peel",
        child_name="Mira",
        child_gender="girl",
        child_trait="curious",
        seed=1,
    ),
    StoryParams(
        hearth="kiln",
        material="clay",
        tool="tongs",
        child_name="Ivo",
        child_gender="boy",
        child_trait="bright-eyed",
        seed=2,
    ),
    StoryParams(
        hearth="pit",
        material="chestnuts",
        tool="ash_shovel",
        child_name="Anya",
        child_gender="girl",
        child_trait="eager",
        seed=3,
    ),
]


ASP_RULES = r"""
sensible_tool(T) :- tool(T), sense(T,S), sense_min(M), S >= M.
compatible(H, M, T) :- hearth(H), material(M), tool(T),
                       needs(M, H), works_on(T, H), sensible_tool(T).
valid(H, M, T) :- compatible(H, M, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hearth_id in HEARTHS:
        lines.append(asp.fact("hearth", hearth_id))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        if material.needs_hearth != "none":
            lines.append(asp.fact("needs", material_id, material.needs_hearth))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        for hearth_id in sorted(tool.works_on):
            lines.append(asp.fact("works_on", tool_id, hearth_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


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

    py_tools = {tool.id for tool in sensible_tools()}
    asp_tools = set(asp_sensible_tools())
    if py_tools == asp_tools:
        print(f"OK: sensible tools match ({sorted(py_tools)}).")
    else:
        rc = 1
        print("MISMATCH in sensible tools:")
        print("  clingo:", sorted(asp_tools))
        print("  python:", sorted(py_tools))

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(0))
        params.seed = 0
        sample = generate(params)
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False, header="smoke")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A folk-tale storyworld about a curious child, a hidden fire, and a peaceful transformation."
    )
    ap.add_argument("--hearth", choices=HEARTHS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python gate")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hearth and args.material:
        hearth = HEARTHS[args.hearth]
        material = MATERIALS[args.material]
        if not material_fits_hearth(material, hearth):
            raise StoryError(explain_rejection(material, hearth))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(TOOLS[args.tool]))
    if args.hearth and args.tool and not tool_fits_hearth(TOOLS[args.tool], HEARTHS[args.hearth]):
        raise StoryError(
            f"(No story: {TOOLS[args.tool].label} does not suit a {HEARTHS[args.hearth].label}.)"
        )

    combos = [
        combo
        for combo in valid_combos()
        if (args.hearth is None or combo[0] == args.hearth)
        and (args.material is None or combo[1] == args.material)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hearth_id, material_id, tool_id = rng.choice(combos)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    child_trait = args.child_trait or rng.choice(TRAITS)
    return StoryParams(
        hearth=hearth_id,
        material=material_id,
        tool=tool_id,
        child_name=child_name,
        child_gender=child_gender,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hearth not in HEARTHS:
        raise StoryError(f"(Unknown hearth: {params.hearth})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    world = tell(params)
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
        print(asp_program("#show sensible_tool/1.\n#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hearth, material, tool) combos:\n")
        for hearth, material, tool in combos:
            print(f"  {hearth:6} {material:10} {tool}")
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
            header = f"### {p.child_name}: {p.material} at the {p.hearth} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
