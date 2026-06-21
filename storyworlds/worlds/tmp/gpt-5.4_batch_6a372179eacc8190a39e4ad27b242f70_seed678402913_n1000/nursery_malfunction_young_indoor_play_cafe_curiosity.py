#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nursery_malfunction_young_indoor_play_cafe_curiosity.py
==================================================================================

A standalone storyworld about a young child's curiosity in an indoor play café.
In the nursery corner, a gentle play device malfunctions. The child wants to
peek and poke, but a caring grown-up guides that curiosity into asking, waiting,
and watching a safe fix.

The world model prefers plausible, calm fixes:
- a leak needs drying and power-off
- a jam needs power-off and a gentle clear
- a flicker or buzz needs a reset

The stories are written in a folk-tale style: warm, simple, concrete, and a
little musical, with a clear beginning, turn, and ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4/nursery_malfunction_young_indoor_play_cafe_curiosity.py
    python storyworlds/worlds/gpt-5.4/nursery_malfunction_young_indoor_play_cafe_curiosity.py --device pom_pom_tube --malfunction jam
    python storyworlds/worlds/gpt-5.4/nursery_malfunction_young_indoor_play_cafe_curiosity.py --malfunction leak
    python storyworlds/worlds/gpt-5.4/nursery_malfunction_young_indoor_play_cafe_curiosity.py --response towel_only
    python storyworlds/worlds/gpt-5.4/nursery_malfunction_young_indoor_play_cafe_curiosity.py --all
    python storyworlds/worlds/gpt-5.4/nursery_malfunction_young_indoor_play_cafe_curiosity.py --verify
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

# Make the shared result containers importable when this script is run directly.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    powered: bool = False
    soft: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
    glow: str
    motion: str
    nook_image: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Malfunction:
    id: str
    label: str
    sign: str
    danger: str
    worsens_line: str
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    sense: int
    fixes: set[str] = field(default_factory=set)
    text: str = ""
    qa_text: str = ""
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


def _r_malfunction_stirs(world: World) -> list[str]:
    out: list[str] = []
    device = world.get("device")
    child = world.get("child")
    if device.meters["malfunction"] >= THRESHOLD and ("stir", device.id) not in world.fired:
        world.fired.add(("stir", device.id))
        child.memes["curiosity"] += 1
        child.memes["worry"] += 1
        world.get("room").meters["unease"] += 1
    return out


def _r_touch_powered_risk(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    device = world.get("device")
    if child.meters["touching_device"] >= THRESHOLD and device.powered:
        sig = ("risk", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            device.meters["risk"] += 1
            child.memes["startle"] += 1
            out.append("__risk__")
    return out


def _r_switch_off_calm(world: World) -> list[str]:
    out: list[str] = []
    device = world.get("device")
    child = world.get("child")
    if not device.powered and device.meters["malfunction"] >= THRESHOLD:
        sig = ("calm_after_power_off", device.id)
        if sig not in world.fired:
            world.fired.add(sig)
            device.meters["risk"] = 0.0
            child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    return out


CAUSAL_RULES = [
    Rule(name="malfunction_stirs", tag="meme", apply=_r_malfunction_stirs),
    Rule(name="touch_powered_risk", tag="physical", apply=_r_touch_powered_risk),
    Rule(name="switch_off_calm", tag="physical", apply=_r_switch_off_calm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def compatible(device: Device, malfunction: Malfunction) -> bool:
    return malfunction.id in device.supports


def response_works(response: Response, malfunction: Malfunction) -> bool:
    return malfunction.id in response.fixes


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for did, device in DEVICES.items():
        for mid, malfunction in MALFUNCTIONS.items():
            if not compatible(device, malfunction):
                continue
            for rid, response in RESPONSES.items():
                if response.sense >= SENSE_MIN and response_works(response, malfunction):
                    combos.append((did, mid, rid))
    return sorted(combos)


def child_pokes(impulse: str, helper_near: str) -> bool:
    if impulse == "hasty":
        return True
    if impulse == "careful":
        return False
    return helper_near == "far"


def predict_risk(world: World, poke: bool) -> dict:
    sim = world.copy()
    if poke:
        sim.get("child").meters["touching_device"] += 1
        propagate(sim, narrate=False)
    return {
        "risk": sim.get("device").meters["risk"],
        "worry": sim.get("child").memes["worry"],
    }


def introduce(world: World, child: Entity, helper: Entity, device: Device) -> None:
    world.say(
        f"In the indoor play cafe called Button and Berry, there was a nursery corner as soft as a small cloud."
    )
    world.say(
        f"There, {child.id}, a young {child.type}, liked to sit with {helper.id} beside {device.phrase}. "
        f"It {device.motion}, and {device.glow}."
    )


def delight(world: World, child: Entity, device: Device) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Many afternoons, {child.id} watched it until the busy room felt slow and gentle. "
        f"To {child.pronoun('object')}, the little nursery nook seemed almost enchanted."
    )


def malfunction_begins(world: World, child: Entity, device_ent: Entity, malfunction: Malfunction) -> None:
    device_ent.meters["malfunction"] += 1
    world.facts["sign"] = malfunction.sign
    propagate(world, narrate=False)
    world.say(
        f"But one day the magic skipped. {malfunction.sign.capitalize()}, and the {device_ent.label} did not behave as it should."
    )
    world.say(
        f"{child.id} leaned forward at once. Curiosity tugged at {child.pronoun('object')} like a tiny hand."
    )


def warning(world: World, child: Entity, helper: Entity, malfunction: Malfunction) -> None:
    world.say(
        f'"Wait, little one," said {helper.id}. "{malfunction.danger} Curious eyes may look, but curious hands must ask first."'
    )


def poke_attempt(world: World, child: Entity, device_ent: Entity, malfunction: Malfunction) -> None:
    child.meters["touching_device"] += 1
    propagate(world, narrate=False)
    child.memes["defiance"] += 1
    world.say(
        f"But {child.id} was very young, and wonder moved faster than wisdom. {child.pronoun().capitalize()} stretched out one finger toward the trouble."
    )
    if device_ent.meters["risk"] >= THRESHOLD:
        world.say(
            f"At that same moment, {malfunction.worsens_line} The strange sound made {child.id} snatch the hand back."
        )


def ask_instead(world: World, child: Entity, helper: Entity) -> None:
    child.memes["trust"] += 1
    child.memes["restraint"] += 1
    world.say(
        f"{child.id} clasped both hands together instead. {child.pronoun().capitalize()} looked up and asked, "
        f'"Will you see what happened?"'
    )


def intervene(world: World, helper: Entity, child: Entity) -> None:
    child.memes["fear"] += 1
    world.say(
        f"{helper.id} gently gathered {child.id}'s hand into {helper.pronoun('possessive')} own and drew {child.pronoun('object')} half a step back."
    )


def fix_device(world: World, helper: Entity, device_ent: Entity, response: Response) -> None:
    device_ent.powered = False
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.id} did the sensible thing: {response.text}."
    )
    device_ent.meters["malfunction"] = 0.0
    device_ent.meters["fixed"] += 1
    device_ent.meters["risk"] = 0.0
    device_ent.powered = True


def explain(world: World, helper: Entity, child: Entity, malfunction: Malfunction) -> None:
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    world.say(
        f'{helper.id} knelt so their faces were close. "A malfunction is when a thing stops working the safe way," '
        f'{helper.pronoun()} said. "That is the very time to fetch grown-up hands, not tiny ones."'
    )
    world.say(
        f"{child.id} nodded. The word was new, but the meaning settled warmly inside {child.pronoun('object')}."
    )


def restored(world: World, child: Entity, device: Device, device_ent: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Soon the {device_ent.label} was itself again. It {device.motion}, and {device.glow}."
    )
    world.say(
        f"{child.id} watched from {helper_distance_image(world.facts['helper_near'])}, and this time {child.pronoun('possessive')} bright curiosity sat beside patience like two friends on one cushion."
    )


def ending(world: World, child: Entity, helper: Entity, device: Device) -> None:
    world.say(
        f"After that, whenever something in the nursery corner whirred the wrong way or blinked a crooked blink, "
        f"{child.id} did not poke first. {child.pronoun().capitalize()} called for {helper.id} and waited."
    )
    world.say(
        f"And so, in the indoor play cafe, the young child kept {child.pronoun('possessive')} wonder, but learned to carry it softly."
    )


def helper_distance_image(helper_near: str) -> str:
    if helper_near == "near":
        return "the safe crook of the bench beside " + "the grown-up"
    return "a snug little rug by the nursery gate"


def tell(
    device: Device,
    malfunction: Malfunction,
    response: Response,
    child_name: str = "Mina",
    child_type: str = "girl",
    helper_name: str = "Nora",
    helper_type: str = "mother",
    impulse: str = "careful",
    helper_near: str = "near",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=["young", "curious", impulse],
        attrs={"impulse": impulse},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
        role="helper",
        traits=["calm"],
    ))
    device_ent = world.add(Entity(
        id="device",
        kind="thing",
        type="device",
        label=device.label,
        phrase=device.phrase,
        powered=True,
        soft=True,
        tags=set(device.tags),
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="place",
        label="nursery corner",
        phrase="the nursery corner",
    ))

    world.facts.update(
        child=child,
        helper=helper,
        device_cfg=device,
        malfunction=malfunction,
        response=response,
        helper_near=helper_near,
    )

    introduce(world, child, helper, device)
    delight(world, child, device)

    world.para()
    malfunction_begins(world, child, device_ent, malfunction)
    warning(world, child, helper, malfunction)

    poke = child_pokes(impulse, helper_near)
    world.facts["predicted"] = predict_risk(world, poke)
    world.facts["poked"] = poke

    if poke:
        poke_attempt(world, child, device_ent, malfunction)
        intervene(world, helper, child)
    else:
        ask_instead(world, child, helper)

    world.para()
    fix_device(world, helper, device_ent, response)
    explain(world, helper, child, malfunction)

    world.para()
    restored(world, child, device, device_ent)
    ending(world, child, helper, device)

    world.facts["resolved"] = True
    world.facts["safe"] = device_ent.meters["fixed"] >= THRESHOLD
    return world


KNOWLEDGE = {
    "nursery": [
        (
            "What is a nursery corner?",
            "A nursery corner is a soft, calm place for very young children. It has gentle toys and cozy places to sit and play."
        )
    ],
    "play_cafe": [
        (
            "What is an indoor play cafe?",
            "An indoor play cafe is a place where children can play inside while grown-ups stay nearby. It often has soft play spaces, small tables, and snacks."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to know more. It is a good feeling when you use it safely and ask questions."
        )
    ],
    "malfunction": [
        (
            "What does malfunction mean?",
            "Malfunction means a thing is not working the right way. When something malfunctions, it is smart to tell a grown-up instead of poking at it."
        )
    ],
    "leak": [
        (
            "Why can a leak be a problem near a machine?",
            "A leak can make things wet where they should stay dry. Wet parts and electric parts do not belong together."
        )
    ],
    "jam": [
        (
            "What is a jam in a machine?",
            "A jam is when something gets stuck and cannot move the way it should. Pulling at it carelessly can make the trouble worse."
        )
    ],
    "flicker": [
        (
            "What does it mean when a light flickers?",
            "A flicker is a light that blinks the wrong way instead of shining steadily. It can be a sign that something needs checking."
        )
    ],
    "unplug": [
        (
            "Why do grown-ups switch things off before fixing them?",
            "Switching a thing off makes it safer to check. A quiet, unpowered machine is safer than one still buzzing or spinning."
        )
    ],
    "ask_first": [
        (
            "What should a child do if a machine acts strangely?",
            "Step back and call a grown-up. Asking first keeps your curious hands safe."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "play_cafe",
    "nursery",
    "curiosity",
    "malfunction",
    "leak",
    "jam",
    "flicker",
    "unplug",
    "ask_first",
]


DEVICES = {
    "cloud_lamp": Device(
        id="cloud_lamp",
        label="cloud lamp",
        phrase="a round cloud lamp above the mat",
        glow="spilled pearly light over the cushions",
        motion="glowed in a calm white ring",
        nook_image="over the mat",
        supports={"flicker", "buzz"},
        tags={"nursery", "play_cafe"},
    ),
    "pom_pom_tube": Device(
        id="pom_pom_tube",
        label="pom-pom tube",
        phrase="a clear pom-pom tube by the wall",
        glow="made the red and yellow pom-poms shine like berries",
        motion="sent soft pom-poms dancing upward in a lazy swirl",
        nook_image="by the wall",
        supports={"jam", "buzz"},
        tags={"nursery", "play_cafe"},
    ),
    "bubble_panel": Device(
        id="bubble_panel",
        label="bubble panel",
        phrase="a bubble panel beside the nursery gate",
        glow="turned the water blue and silver",
        motion="lifted a ladder of bubbles through the panel",
        nook_image="beside the nursery gate",
        supports={"leak", "flicker"},
        tags={"nursery", "play_cafe"},
    ),
}

MALFUNCTIONS = {
    "flicker": Malfunction(
        id="flicker",
        label="flicker",
        sign="the light blinked, blinked again, and then went dim",
        danger="When a light flickers, it may need careful grown-up checking",
        worsens_line="the strange blinking skipped faster for one heartbeat",
        needs={"reset"},
        tags={"malfunction", "flicker", "unplug", "ask_first"},
    ),
    "buzz": Malfunction(
        id="buzz",
        label="buzz",
        sign="a wrong little buzz crept out, thin as an angry bee",
        danger="A buzzing machine may have something wrong inside it",
        worsens_line="the buzz gave one sharp jump and then a worried rattle",
        needs={"reset"},
        tags={"malfunction", "unplug", "ask_first"},
    ),
    "jam": Malfunction(
        id="jam",
        label="jam",
        sign="the soft pieces stopped halfway and trembled in one place",
        danger="When something is jammed, pulling at it can pinch or worsen the trouble",
        worsens_line="the stuck pieces shivered and wedged themselves more tightly",
        needs={"clear_jam"},
        tags={"malfunction", "jam", "unplug", "ask_first"},
    ),
    "leak": Malfunction(
        id="leak",
        label="leak",
        sign="a little thread of water slid down where no water should be",
        danger="A leak can make a wet place around a powered thing",
        worsens_line="another drop slipped free and ran onto the tray below",
        needs={"dry_leak"},
        tags={"malfunction", "leak", "unplug", "ask_first"},
    ),
}

RESPONSES = {
    "power_reset": Response(
        id="power_reset",
        label="switch it off and reset it",
        sense=3,
        fixes={"flicker", "buzz"},
        text="she switched the device off, checked the plug and button, and waited a quiet moment before resetting it",
        qa_text="switched the device off and reset it after checking the plug and button",
        tags={"unplug"},
    ),
    "dry_and_call": Response(
        id="dry_and_call",
        label="switch it off and dry the leak",
        sense=3,
        fixes={"leak"},
        text="she switched the device off at once, dried the wet place with towels, and asked the café keeper for help before turning it on again",
        qa_text="switched the device off, dried the leak, and asked the café keeper for help",
        tags={"unplug"},
    ),
    "switch_and_clear": Response(
        id="switch_and_clear",
        label="switch it off and clear the jam",
        sense=3,
        fixes={"jam"},
        text="she switched the device off, opened the safe little latch, and gently freed the stuck soft pieces before starting it again",
        qa_text="switched the device off and gently cleared the jam",
        tags={"unplug"},
    ),
    "towel_only": Response(
        id="towel_only",
        label="just dab it with a towel",
        sense=1,
        fixes=set(),
        text="she dabbed at it with a towel while it was still running",
        qa_text="dabbed at it with a towel while it was still running",
        tags=set(),
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Ava", "Zoe", "Tess", "Maya", "Ivy"]
BOY_NAMES = ["Oli", "Ben", "Leo", "Milo", "Finn", "Noah", "Eli", "Toby"]
IMPULSES = ["careful", "hasty"]
HELPER_NEAR = ["near", "far"]


@dataclass
class StoryParams:
    device: str
    malfunction: str
    response: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    impulse: str
    helper_near: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    malfunction = world.facts["malfunction"]
    device = world.facts["device_cfg"]
    poke = world.facts["poked"]
    if poke:
        turn = "a curious young child almost pokes a malfunctioning nursery device before a grown-up steps in"
    else:
        turn = "a curious young child sees a nursery device malfunction and asks a grown-up for help instead of touching it"
    return [
        'Write a short folk-tale style story for a 3-to-5-year-old set in an indoor play cafe. Include the words "nursery", "malfunction", and "young".',
        f"Tell a gentle story where {child.id}, a curious young {child.type}, notices a {malfunction.label} in the {device.label} in the nursery corner, and learns to ask before touching.",
        f"Write a calm cautionary tale about curiosity in a play café: {turn}.",
    ]


def pair_noun(child: Entity, helper: Entity) -> str:
    return f"{child.id} and {helper.id}"


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    device = world.facts["device_cfg"]
    malfunction = world.facts["malfunction"]
    response = world.facts["response"]
    poke = world.facts["poked"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a young and curious {child.type}, and {helper.id}, the calm grown-up nearby in the indoor play cafe."
        ),
        (
            "Where does the story happen?",
            "It happens in the nursery corner of an indoor play cafe. That soft little place is what makes the broken machine feel close and tempting."
        ),
        (
            f"What went wrong with the {device.label}?",
            f"It had a malfunction: {malfunction.sign}. The strange change is what made {child.id} stare and want to know more."
        ),
    ]
    if poke:
        qa.append(
            (
                f"Why did {helper.id} stop {child.id} from touching the device?",
                f"{helper.id} stopped {child.id} because the device was still powered while it was acting strangely. A curious poke could have worsened the trouble, so the safest move was to step back first."
            )
        )
    else:
        qa.append(
            (
                f"What did {child.id} do when curiosity pulled at {child.pronoun('object')}?",
                f"{child.id} kept both hands back and asked {helper.id} to look. That shows curiosity can stay gentle when it is guided by patience."
            )
        )
    qa.append(
        (
            f"How did {helper.id} fix the problem?",
            f"{helper.id} {response.qa_text}. The fix worked because it matched the kind of malfunction instead of guessing."
        )
    )
    qa.append(
        (
            "What did the child learn at the end?",
            f"{child.id} learned that a malfunction is the time to call grown-up hands, not tiny ones. The ending proves the lesson because {child.pronoun()} keeps curiosity, but uses it more safely."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"curiosity", "ask_first"} | set(world.facts["device_cfg"].tags) | set(world.facts["malfunction"].tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.powered:
            bits.append("powered=True")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        device="bubble_panel",
        malfunction="leak",
        response="dry_and_call",
        child_name="Mina",
        child_type="girl",
        helper_name="Nora",
        helper_type="mother",
        impulse="careful",
        helper_near="near",
    ),
    StoryParams(
        device="pom_pom_tube",
        malfunction="jam",
        response="switch_and_clear",
        child_name="Oli",
        child_type="boy",
        helper_name="Mara",
        helper_type="mother",
        impulse="hasty",
        helper_near="near",
    ),
    StoryParams(
        device="cloud_lamp",
        malfunction="flicker",
        response="power_reset",
        child_name="Ava",
        child_type="girl",
        helper_name="Uncle Ben",
        helper_type="man",
        impulse="careful",
        helper_near="far",
    ),
    StoryParams(
        device="pom_pom_tube",
        malfunction="buzz",
        response="power_reset",
        child_name="Leo",
        child_type="boy",
        helper_name="Sara",
        helper_type="mother",
        impulse="hasty",
        helper_near="far",
    ),
]


def explain_combo(device: Device, malfunction: Malfunction) -> str:
    return (
        f"(No story: {device.label} does not plausibly have the malfunction '{malfunction.id}' in this world. "
        f"Choose a malfunction it supports.)"
    )


def explain_response(response: Response, malfunction: Malfunction) -> str:
    if response.sense < SENSE_MIN:
        good = ", ".join(sorted(r.id for r in sensible_responses()))
        return (
            f"(Refusing response '{response.id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Try one of: {good}.)"
        )
    return (
        f"(No story: response '{response.id}' does not actually fix the malfunction '{malfunction.id}'. "
        f"The grown-up's fix must match the trouble.)"
    )


ASP_RULES = r"""
device_supports(D, M) :- supports(D, M).
works(R, M) :- fixes(R, M).
sensible(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.
valid(D, M, R) :- device(D), malfunction(M), response(R),
                  device_supports(D, M), works(R, M), sensible(R).

poked :- impulse(hasty).
poked :- impulse(careful), helper_near(far), not blocker.
blocker :- helper_near(near), impulse(careful).

outcome(asked) :- not poked.
outcome(poked) :- poked.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did, device in DEVICES.items():
        lines.append(asp.fact("device", did))
        for mid in sorted(device.supports):
            lines.append(asp.fact("supports", did, mid))
    for mid in MALFUNCTIONS:
        lines.append(asp.fact("malfunction", mid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        for mid in sorted(response.fixes):
            lines.append(asp.fact("fixes", rid, mid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("impulse", params.impulse),
            asp.fact("helper_near", params.helper_near),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "poked" if child_pokes(params.impulse, params.helper_near) else "asked"


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

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome calculations differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a young child in an indoor play cafe learns how to handle a nursery malfunction safely."
    )
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--malfunction", choices=MALFUNCTIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "woman", "man"])
    ap.add_argument("--impulse", choices=IMPULSES)
    ap.add_argument("--helper-near", choices=HELPER_NEAR)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke generation test")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def pick_name(rng: random.Random, child_type: str) -> str:
    return rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.device and args.malfunction:
        device = DEVICES[args.device]
        malfunction = MALFUNCTIONS[args.malfunction]
        if not compatible(device, malfunction):
            raise StoryError(explain_combo(device, malfunction))
    if args.response and args.malfunction:
        response = RESPONSES[args.response]
        malfunction = MALFUNCTIONS[args.malfunction]
        if not response_works(response, malfunction) or response.sense < SENSE_MIN:
            raise StoryError(explain_response(response, malfunction))
    if args.response and not args.malfunction:
        response = RESPONSES[args.response]
        if response.sense < SENSE_MIN:
            dummy = next(iter(MALFUNCTIONS.values()))
            raise StoryError(explain_response(response, dummy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.device is None or combo[0] == args.device)
        and (args.malfunction is None or combo[1] == args.malfunction)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    device_id, malfunction_id, response_id = rng.choice(combos)
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = pick_name(rng, child_type)
    helper_type = args.helper_type or rng.choice(["mother", "father", "woman", "man"])
    helper_name = {
        "mother": rng.choice(["Nora", "Mara", "Lena", "Sara"]),
        "father": rng.choice(["Tom", "Evan", "Milo", "Ben"]),
        "woman": rng.choice(["Aunt June", "Ms. Rey", "Tara"]),
        "man": rng.choice(["Uncle Ben", "Mr. Cole", "Dan"]),
    }[helper_type]
    impulse = args.impulse or rng.choice(IMPULSES)
    helper_near = args.helper_near or rng.choice(HELPER_NEAR)

    return StoryParams(
        device=device_id,
        malfunction=malfunction_id,
        response=response_id,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        impulse=impulse,
        helper_near=helper_near,
    )


def generate(params: StoryParams) -> StorySample:
    if params.device not in DEVICES:
        raise StoryError(f"(Unknown device: {params.device})")
    if params.malfunction not in MALFUNCTIONS:
        raise StoryError(f"(Unknown malfunction: {params.malfunction})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    device = DEVICES[params.device]
    malfunction = MALFUNCTIONS[params.malfunction]
    response = RESPONSES[params.response]

    if not compatible(device, malfunction):
        raise StoryError(explain_combo(device, malfunction))
    if response.sense < SENSE_MIN or not response_works(response, malfunction):
        raise StoryError(explain_response(response, malfunction))

    world = tell(
        device=device,
        malfunction=malfunction,
        response=response,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        impulse=params.impulse,
        helper_near=params.helper_near,
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
        print(f"{len(combos)} valid (device, malfunction, response) combos:\n")
        for device, malfunction, response in combos:
            print(f"  {device:12} {malfunction:10} {response}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.device} / {p.malfunction} / {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
