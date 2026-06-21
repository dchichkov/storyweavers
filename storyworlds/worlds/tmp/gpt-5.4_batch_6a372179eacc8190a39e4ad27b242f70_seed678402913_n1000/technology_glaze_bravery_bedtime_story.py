#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/technology_glaze_bravery_bedtime_story.py
====================================================================

A small bedtime storyworld about a child who sees a strange shape on the wall.
The shape is not a monster at all. It comes from a little piece of technology
casting light onto something shiny with a glaze.

This world models:
- a bedtime room with a child and parent
- a light-making device
- a glazed object with a glossy surface
- fear, bravery, relief, and trust as emotional state
- a simple causal rule: moving light + glossy glaze -> spooky reflection
- a grounded resolution: use a sensible fix that actually breaks the reflection

Run it
------
    python storyworlds/worlds/gpt-5.4/technology_glaze_bravery_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/technology_glaze_bravery_bedtime_story.py --device projector --glazed moon_bank
    python storyworlds/worlds/gpt-5.4/technology_glaze_bravery_bedtime_story.py --glazed cloth_bunny
    python storyworlds/worlds/gpt-5.4/technology_glaze_bravery_bedtime_story.py --response hide_under_blanket
    python storyworlds/worlds/gpt-5.4/technology_glaze_bravery_bedtime_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/technology_glaze_bravery_bedtime_story.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    location: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    glossy: bool = False
    emits_light: bool = False
    moving_light: bool = False
    reachable_from_bed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    light_word: str
    motion_word: str
    location: str
    reachable_from_bed: bool
    emits_light: bool = True
    moving_light: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class GlazedThing:
    id: str
    label: str
    phrase: str
    sheen: str
    location: str
    glossy: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    target: str
    works_on: set[str]
    success_text: str
    qa_text: str
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


def _r_reflection(world: World) -> list[str]:
    device = world.get("device")
    glazed = world.get("glazed")
    child = world.get("child")
    wall = world.get("wall")
    if not (
        device.emits_light
        and device.moving_light
        and glazed.glossy
        and device.meters["on"] >= THRESHOLD
        and glazed.meters["in_place"] >= THRESHOLD
    ):
        return []
    sig = ("reflection", device.id, glazed.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    wall.meters["reflection"] += 1
    child.memes["fear"] += 1
    return ["__reflection__"]


CAUSAL_RULES = [
    Rule(name="reflection", tag="physical", apply=_r_reflection),
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


DEVICES = {
    "projector": Device(
        id="projector",
        label="star projector",
        phrase="a little star projector",
        light_word="stars",
        motion_word="slowly turning dots of light",
        location="bedside table",
        reachable_from_bed=True,
        emits_light=True,
        moving_light=True,
        tags={"technology", "nightlight", "projector"},
    ),
    "monitor": Device(
        id="monitor",
        label="baby monitor",
        phrase="a baby monitor with a tiny blinking screen",
        light_word="a blue screen-glow",
        motion_word="small pulses of light",
        location="dresser",
        reachable_from_bed=False,
        emits_light=True,
        moving_light=True,
        tags={"technology", "monitor"},
    ),
    "sound_machine": Device(
        id="sound_machine",
        label="sound machine",
        phrase="a quiet sound machine",
        light_word="almost no light",
        motion_word="still darkness",
        location="shelf",
        reachable_from_bed=False,
        emits_light=False,
        moving_light=False,
        tags={"technology", "sleep"},
    ),
}

GLAZED = {
    "moon_bank": GlazedThing(
        id="moon_bank",
        label="moon bank",
        phrase="a little moon-shaped bank with silver glaze",
        sheen="The silver glaze made it shine when light touched it.",
        location="dresser",
        glossy=True,
        tags={"glaze", "ceramic", "moon"},
    ),
    "turtle_cup": GlazedThing(
        id="turtle_cup",
        label="turtle cup",
        phrase="a turtle cup with blue glaze",
        sheen="Its blue glaze looked soft by day and shiny by night.",
        location="windowsill",
        glossy=True,
        tags={"glaze", "ceramic", "cup"},
    ),
    "star_plate": GlazedThing(
        id="star_plate",
        label="star plate",
        phrase="a hand-painted star plate with honey glaze",
        sheen="The honey glaze gave it a warm, glassy shine.",
        location="bedside table",
        glossy=True,
        tags={"glaze", "ceramic", "star"},
    ),
    "cloth_bunny": GlazedThing(
        id="cloth_bunny",
        label="cloth bunny",
        phrase="a cloth bunny with floppy ears",
        sheen="It was soft and dull, not shiny at all.",
        location="pillow",
        glossy=False,
        tags={"toy"},
    ),
}

RESPONSES = {
    "press_button": Response(
        id="press_button",
        sense=3,
        target="device",
        works_on={"projector", "monitor"},
        success_text="pressed the button and the moving light stopped at once",
        qa_text="pressed the device button to stop the moving light",
        tags={"button", "technology"},
    ),
    "turn_object": Response(
        id="turn_object",
        sense=3,
        target="glazed",
        works_on={"moon_bank", "turtle_cup", "star_plate"},
        success_text="turned the shiny object so the light could not bounce from its glaze anymore",
        qa_text="turned the glazed object so the light could not reflect from it",
        tags={"glaze", "reflection"},
    ),
    "hide_under_blanket": Response(
        id="hide_under_blanket",
        sense=1,
        target="none",
        works_on=set(),
        success_text="hid under the blanket",
        qa_text="hid under the blanket",
        tags={"fear"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Tess", "Nora", "Ava", "Ivy", "Lucy", "Maya"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Eli", "Ben", "Noah", "Max", "Theo"]
TRAITS = ["gentle", "thoughtful", "sleepy", "curious", "careful", "quiet"]
COMFORTS = ["stuffed fox", "small blanket", "plush whale", "soft bear", "little pillow"]
PARENTS = ["mother", "father"]


def hazard_at_risk(device: Device, glazed: GlazedThing) -> bool:
    return device.emits_light and device.moving_light and glazed.glossy


def response_works(response: Response, device: Device, glazed: GlazedThing) -> bool:
    if response.target == "device":
        return device.id in response.works_on and device.emits_light and device.moving_light
    if response.target == "glazed":
        return glazed.id in response.works_on and glazed.glossy
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for did, device in DEVICES.items():
        for gid, glazed in GLAZED.items():
            for rid, response in RESPONSES.items():
                if hazard_at_risk(device, glazed) and response.sense >= SENSE_MIN and response_works(response, device, glazed):
                    combos.append((did, gid, rid))
    return combos


def child_can_fix_alone(device: Device, glazed: GlazedThing, response: Response, bravery: int) -> bool:
    if bravery < 3:
        return False
    if response.target == "device":
        return device.reachable_from_bed
    if response.target == "glazed":
        return glazed.location == "bedside table"
    return False


def predict_reflection(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "reflection": sim.get("wall").meters["reflection"],
        "fear": sim.get("child").memes["fear"],
    }


def introduce(world: World, child: Entity, parent: Entity, comfort: str, device_cfg: Device, glazed_cfg: GlazedThing) -> None:
    trait = child.attrs.get("trait", "sleepy")
    world.say(
        f"{child.id} was a little {trait} {child.type} who liked bedtime when the room felt soft and known."
    )
    world.say(
        f"On the shelf stood {device_cfg.phrase}, a bit of bedtime technology, and nearby rested {glazed_cfg.phrase}."
    )
    world.say(glazed_cfg.sheen)
    world.say(
        f"{child.id} tucked {child.pronoun('possessive')} {comfort} under one arm while {parent.label_word} pulled the blanket smooth."
    )


def settle(world: World, child: Entity, parent: Entity, device_cfg: Device) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f'"Good night," {parent.label_word} whispered. {child.id} watched {device_cfg.light_word} drift for a moment and tried to be still.'
    )


def strange_shape(world: World, child: Entity, device_ent: Entity, glazed_ent: Entity) -> None:
    device_ent.meters["on"] += 1
    glazed_ent.meters["in_place"] += 1
    pred = predict_reflection(world)
    world.facts["predicted_fear"] = pred["fear"]
    propagate(world, narrate=False)
    wall = world.get("wall")
    if wall.meters["reflection"] >= THRESHOLD:
        world.say(
            f"Then {device_ent.attrs['motion_word']} slid across the room, struck the {glazed_ent.label}, and bounced onto the wall."
        )
        world.say(
            f"A wobbly shape stretched tall in the dark. To sleepy eyes, it did not look like a cup or a bank at all."
        )


def brave_breath(world: World, child: Entity, bravery: int) -> None:
    child.memes["bravery"] += float(bravery)
    if bravery >= 3:
        world.say(
            f"{child.id}'s heart bumped fast, but {child.pronoun()} took one brave breath and looked again instead of hiding."
        )
    elif bravery == 2:
        world.say(
            f"{child.id} felt scared and squeezed the blanket, then remembered that brave children can use quiet voices."
        )
    else:
        world.say(
            f"{child.id} pulled the blanket to {child.pronoun('possessive')} chin and wished the odd shape would go away."
        )


def call_parent(world: World, child: Entity, parent: Entity) -> None:
    child.memes["trust"] += 1
    world.say(
        f'"{parent.label_word.capitalize()}?" {child.id} called in a small but steady voice. "Something on the wall looks wrong."'
    )


def explain(world: World, parent: Entity, child: Entity, device_cfg: Device, glazed_cfg: GlazedThing) -> None:
    world.say(
        f"{parent.label_word.capitalize()} came back, followed the light with calm eyes, and smiled."
    )
    world.say(
        f'"It is not a monster," {parent.pronoun()} said softly. "The {device_cfg.label} is making light, and the {glazed_cfg.label} is tossing it back because of its shiny glaze."'
    )
    world.say(
        f'"Sometimes technology makes funny shadows when it meets something glossy."'
    )


def fix_reflection(world: World, actor: Entity, response: Response, device_ent: Entity, glazed_ent: Entity) -> None:
    wall = world.get("wall")
    if response.target == "device":
        device_ent.meters["on"] = 0.0
    elif response.target == "glazed":
        glazed_ent.meters["in_place"] = 0.0
    wall.meters["reflection"] = 0.0
    child = world.get("child")
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    world.say(f"{actor.id} {response.success_text}.")
    world.say("At once the tall shape melted back into an ordinary room.")


def ending_alone(world: World, child: Entity, comfort: str) -> None:
    child.memes["pride"] += 1
    world.say(
        f"{child.id} blinked, felt the room grow gentle again, and gave {child.pronoun('possessive')} {comfort} a snug little hug."
    )
    world.say(
        f"Soon the wall was plain, the blanket was warm, and {child.id} fell asleep knowing bravery can be quiet."
    )


def ending_together(world: World, child: Entity, parent: Entity, comfort: str) -> None:
    child.memes["love"] += 1
    world.say(
        f"{parent.label_word.capitalize()} sat beside the bed for a minute while {child.id} cuddled {child.pronoun('possessive')} {comfort}."
    )
    world.say(
        f"The room still held night, but not fear anymore, and {child.id} drifted to sleep feeling brave in a different way."
    )


def tell(
    device_cfg: Device,
    glazed_cfg: GlazedThing,
    response: Response,
    *,
    child_name: str = "Lila",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "gentle",
    comfort: str = "soft bear",
    bravery: int = 2,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            attrs={"trait": trait},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    device_ent = world.add(
        Entity(
            id="device",
            type="device",
            label=device_cfg.label,
            phrase=device_cfg.phrase,
            location=device_cfg.location,
            emits_light=device_cfg.emits_light,
            moving_light=device_cfg.moving_light,
            reachable_from_bed=device_cfg.reachable_from_bed,
            attrs={"motion_word": device_cfg.motion_word},
            tags=set(device_cfg.tags),
        )
    )
    glazed_ent = world.add(
        Entity(
            id="glazed",
            type="object",
            label=glazed_cfg.label,
            phrase=glazed_cfg.phrase,
            location=glazed_cfg.location,
            glossy=glazed_cfg.glossy,
            tags=set(glazed_cfg.tags),
        )
    )
    world.add(Entity(id="wall", type="wall", label="wall"))

    introduce(world, child, parent, comfort, device_cfg, glazed_cfg)
    settle(world, child, parent, device_cfg)

    world.para()
    strange_shape(world, child, device_ent, glazed_ent)
    brave_breath(world, child, bravery)

    alone = child_can_fix_alone(device_cfg, glazed_cfg, response, bravery)
    if alone:
        world.say(
            f"From bed, {child.id} understood what needed to change."
        )
        fix_reflection(world, child, response, device_ent, glazed_ent)
        world.para()
        ending_alone(world, child, comfort)
        outcome = "alone"
    else:
        call_parent(world, child, parent)
        world.para()
        explain(world, parent, child, device_cfg, glazed_cfg)
        fix_reflection(world, parent, response, device_ent, glazed_ent)
        world.para()
        ending_together(world, child, parent, comfort)
        outcome = "together"

    world.facts.update(
        child=child,
        parent=parent,
        device_cfg=device_cfg,
        glazed_cfg=glazed_cfg,
        response=response,
        comfort=comfort,
        bravery=bravery,
        outcome=outcome,
        reflection_started=True,
        reflection_gone=world.get("wall").meters["reflection"] < THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    device: str
    glazed: str
    response: str
    name: str
    gender: str
    parent: str
    trait: str
    comfort: str
    bravery: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        device="projector",
        glazed="star_plate",
        response="press_button",
        name="Lila",
        gender="girl",
        parent="mother",
        trait="gentle",
        comfort="soft bear",
        bravery=3,
        seed=1,
    ),
    StoryParams(
        device="monitor",
        glazed="moon_bank",
        response="turn_object",
        name="Owen",
        gender="boy",
        parent="father",
        trait="thoughtful",
        comfort="small blanket",
        bravery=2,
        seed=2,
    ),
    StoryParams(
        device="projector",
        glazed="turtle_cup",
        response="turn_object",
        name="Mina",
        gender="girl",
        parent="mother",
        trait="quiet",
        comfort="plush whale",
        bravery=1,
        seed=3,
    ),
    StoryParams(
        device="monitor",
        glazed="star_plate",
        response="press_button",
        name="Theo",
        gender="boy",
        parent="father",
        trait="careful",
        comfort="stuffed fox",
        bravery=2,
        seed=4,
    ),
]


KNOWLEDGE = {
    "technology": [
        (
            "What is technology?",
            "Technology is a tool people make to help with a job, like giving light, sound, or a way to watch from another room. Some technology is helpful, but at night it can make surprising lights and shadows.",
        )
    ],
    "glaze": [
        (
            "What is glaze?",
            "Glaze is a smooth shiny coating baked onto clay. It can make a cup or plate glossy enough to catch and bounce light.",
        )
    ],
    "reflection": [
        (
            "What is a reflection?",
            "A reflection happens when light bounces off a surface. Shiny things can send light to another place, like a wall or ceiling.",
        )
    ],
    "projector": [
        (
            "What does a star projector do?",
            "A star projector shines little lights around a room. It can make bedtime feel cozy, but it can also make moving shapes if the light hits something shiny.",
        )
    ],
    "monitor": [
        (
            "What is a baby monitor?",
            "A baby monitor helps grown-ups listen or look in from another room. Some have small lights or screens that glow in the dark.",
        )
    ],
    "nightlight": [
        (
            "Why can a night-light make shadows?",
            "Any light can make shadows when it shines around objects. Moving lights can make those shadows seem more alive than they really are.",
        )
    ],
    "bravery": [
        (
            "What is bravery at bedtime?",
            "Bravery at bedtime does not always mean doing everything alone. Sometimes it means taking a breath, looking again, or calling a grown-up for help.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    device = f["device_cfg"]
    glazed = f["glazed_cfg"]
    outcome = f["outcome"]
    prompts = [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "technology" and "glaze".',
        f"Tell a gentle night story where a {child.type} named {child.id} sees a scary shape caused by {device.phrase} and {glazed.phrase}.",
        "Write a story about bravery at bedtime where a child learns that a strange wall shape has an ordinary cause.",
    ]
    if outcome == "alone":
        prompts.append(
            f"Make the child brave enough to solve the problem from bed by using the {device.label} without anyone getting in trouble."
        )
    else:
        prompts.append(
            "Let the child use bravery by asking for help, and let a calm grown-up explain the light and shadow."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    device = f["device_cfg"]
    glazed = f["glazed_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    comfort = f["comfort"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {child.type} getting ready for sleep. {parent.label_word.capitalize()} is there too, helping bedtime feel safe.",
        ),
        (
            "What made the scary shape on the wall?",
            f"The shape came from {device.phrase} shining onto the {glazed.label}. The light bounced from the object's glaze and stretched into a bigger shape on the wall.",
        ),
        (
            f"Why was {child.id} brave?",
            f"{child.id} was brave because {child.pronoun()} did something useful even while feeling scared. {child.pronoun().capitalize()} either looked carefully or used a steady voice instead of hiding from the feeling.",
        ),
    ]
    if outcome == "alone":
        qa.append(
            (
                f"How did {child.id} fix the problem?",
                f"{child.id} {response.qa_text}. That broke the path of the moving light, so the spooky shape vanished and the room looked ordinary again.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and safely. {child.id} hugged {child.pronoun('possessive')} {comfort} and fell asleep knowing that bravery can be small and steady.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {child.id} call for {parent.label_word}?",
                f"{child.id} could not fix the light from bed, or was too scared to do it alone. Calling for help was part of the brave choice because it brought in someone calm who could understand the room.",
            )
        )
        qa.append(
            (
                f"How did {parent.label_word} solve it?",
                f"{parent.label_word.capitalize()} {response.qa_text}. Once the light could no longer bounce from the shiny glaze, the shape on the wall disappeared.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The room was still dark, but it no longer felt mysterious or scary. {child.id} cuddled {child.pronoun('possessive')} {comfort} and went to sleep feeling safe.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"technology", "glaze", "reflection", "bravery"}
    device = f["device_cfg"]
    if "projector" in device.tags:
        tags.add("projector")
        tags.add("nightlight")
    if "monitor" in device.tags:
        tags.add("monitor")
    ordered = ["technology", "glaze", "reflection", "projector", "monitor", "nightlight", "bravery"]
    out: list[tuple[str, str]] = []
    for tag in ordered:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if ent.glossy:
            flags.append("glossy")
        if ent.emits_light:
            flags.append("emits_light")
        if ent.moving_light:
            flags.append("moving_light")
        if ent.reachable_from_bed:
            flags.append("reachable_from_bed")
        if flags:
            bits.append(f"flags={flags}")
        if ent.location:
            bits.append(f"location={ent.location}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(device: Device, glazed: GlazedThing) -> str:
    if not glazed.glossy:
        return (
            f"(No story: {glazed.phrase} is not shiny enough to bounce light, so it cannot make the spooky wall shape. "
            f"Pick a glazed ceramic object instead.)"
        )
    if not (device.emits_light and device.moving_light):
        return (
            f"(No story: {device.phrase} does not cast the kind of moving light that would make a strange wall shape. "
            f"Pick a light-making device like the projector or monitor.)"
        )
    return "(No story: this combination would not make the bedtime reflection.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(rid for rid, r in RESPONSES.items() if r.sense >= SENSE_MIN))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). A bedtime story should use a fix that actually changes the light. "
        f"Try: {better}.)"
    )


def explain_response_mismatch(response: Response, device: Device, glazed: GlazedThing) -> str:
    if response.target == "device":
        return (
            f"(No story: {response.id} only makes sense when the chosen device is the thing causing the moving light. "
            f"That is not true for {device.id}.)"
        )
    if response.target == "glazed":
        return (
            f"(No story: {response.id} only works when the chosen shiny object is one it can turn away from the light. "
            f"That is not true for {glazed.id}.)"
        )
    return "(No story: the chosen response does not solve the problem.)"


def outcome_of(params: StoryParams) -> str:
    device = DEVICES[params.device]
    glazed = GLAZED[params.glazed]
    response = RESPONSES[params.response]
    return "alone" if child_can_fix_alone(device, glazed, response, params.bravery) else "together"


ASP_RULES = r"""
hazard(D, G) :- device(D), glazed(G), emits_light(D), moving_light(D), glossy(G).

works(R, D, G) :- response(R), target(R, device), works_on_device(R, D), emits_light(D), moving_light(D), glazed(G).
works(R, D, G) :- response(R), target(R, glazed), works_on_glazed(R, G), glossy(G), device(D).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(D, G, R) :- hazard(D, G), sensible(R), works(R, D, G).

alone_reachable :- chosen_response(R), target(R, device), chosen_device(D), reachable_from_bed(D).
alone_reachable :- chosen_response(R), target(R, glazed), chosen_glazed(G), glazed_bedside(G).

outcome(alone) :- bravery(B), B >= 3, alone_reachable.
outcome(together) :- not outcome(alone).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did, device in DEVICES.items():
        lines.append(asp.fact("device", did))
        if device.emits_light:
            lines.append(asp.fact("emits_light", did))
        if device.moving_light:
            lines.append(asp.fact("moving_light", did))
        if device.reachable_from_bed:
            lines.append(asp.fact("reachable_from_bed", did))
    for gid, glazed in GLAZED.items():
        lines.append(asp.fact("glazed", gid))
        if glazed.glossy:
            lines.append(asp.fact("glossy", gid))
        if glazed.location == "bedside table":
            lines.append(asp.fact("glazed_bedside", gid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("target", rid, response.target))
        for did in sorted(response.works_on & set(DEVICES)):
            lines.append(asp.fact("works_on_device", rid, did))
        for gid in sorted(response.works_on & set(GLAZED)):
            lines.append(asp.fact("works_on_glazed", rid, gid))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_device", params.device),
            asp.fact("chosen_glazed", params.glazed),
            asp.fact("chosen_response", params.response),
            asp.fact("bravery", params.bravery),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    clingo_sensible = set(asp_sensible())
    python_sensible = {rid for rid, response in RESPONSES.items() if response.sense >= SENSE_MIN}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime reflection made by technology and glaze. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--glazed", choices=GLAZED)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
    ap.add_argument("--bravery", type=int, choices=[1, 2, 3])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.device and args.glazed:
        device = DEVICES[args.device]
        glazed = GLAZED[args.glazed]
        if not hazard_at_risk(device, glazed):
            raise StoryError(explain_rejection(device, glazed))
    if args.response:
        response = RESPONSES[args.response]
        if response.sense < SENSE_MIN:
            raise StoryError(explain_response(args.response))
        if args.device and args.glazed:
            if not response_works(response, DEVICES[args.device], GLAZED[args.glazed]):
                raise StoryError(explain_response_mismatch(response, DEVICES[args.device], GLAZED[args.glazed]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.device is None or combo[0] == args.device)
        and (args.glazed is None or combo[1] == args.glazed)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        if args.device and args.glazed and not hazard_at_risk(DEVICES[args.device], GLAZED[args.glazed]):
            raise StoryError(explain_rejection(DEVICES[args.device], GLAZED[args.glazed]))
        raise StoryError("(No valid combination matches the given options.)")

    device_id, glazed_id, response_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    comfort = rng.choice(COMFORTS)
    bravery = args.bravery if args.bravery is not None else rng.choice([1, 2, 3])

    return StoryParams(
        device=device_id,
        glazed=glazed_id,
        response=response_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        comfort=comfort,
        bravery=bravery,
    )


def generate(params: StoryParams) -> StorySample:
    if params.device not in DEVICES:
        raise StoryError(f"(Unknown device: {params.device})")
    if params.glazed not in GLAZED:
        raise StoryError(f"(Unknown glazed object: {params.glazed})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    device = DEVICES[params.device]
    glazed = GLAZED[params.glazed]
    response = RESPONSES[params.response]

    if not hazard_at_risk(device, glazed):
        raise StoryError(explain_rejection(device, glazed))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not response_works(response, device, glazed):
        raise StoryError(explain_response_mismatch(response, device, glazed))

    world = tell(
        device,
        glazed,
        response,
        child_name=params.name,
        child_gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
        comfort=params.comfort,
        bravery=params.bravery,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (device, glazed, response) combos:\n")
        for device, glazed, response in combos:
            print(f"  {device:14} {glazed:12} {response}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.name}: {params.device} + {params.glazed} ({outcome_of(params)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
