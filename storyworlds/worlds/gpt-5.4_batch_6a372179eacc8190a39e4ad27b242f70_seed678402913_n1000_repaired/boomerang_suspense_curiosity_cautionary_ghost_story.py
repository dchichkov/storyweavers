#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/boomerang_suspense_curiosity_cautionary_ghost_story.py
==================================================================================

A standalone storyworld for a small cautionary ghost-story domain centered on a
boomerang. Two children explore a spooky old place, curiosity makes one child
want to throw the boomerang into the dark, and the world decides whether a wiser
warning averts the trouble or whether the throw breaks something and proves that
"ghosts" can really be shadows, wind, and bad choices.

Run it
------
    python storyworlds/worlds/gpt-5.4/boomerang_suspense_curiosity_cautionary_ghost_story.py
    python storyworlds/worlds/gpt-5.4/boomerang_suspense_curiosity_cautionary_ghost_story.py --setting attic --target oil_lamp
    python storyworlds/worlds/gpt-5.4/boomerang_suspense_curiosity_cautionary_ghost_story.py --target trunk
    python storyworlds/worlds/gpt-5.4/boomerang_suspense_curiosity_cautionary_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/boomerang_suspense_curiosity_cautionary_ghost_story.py --qa --json
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "steady"}


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
    tags: set[str] = field(default_factory=set)
    fragile: bool = False
    lit: bool = False
    returns_when_thrown: bool = False
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    whisper: str
    hiding_spot: str
    bright_place: str
    tightness: int
    enclosed: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    article: str
    fragile: bool = True
    lit: bool = False
    severity: int = 1
    crash_text: str = ""
    after_text: str = ""
    qa_effect: str = ""
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"{self.article} {self.label}"

    @property
    def The(self) -> str:
        text = self.the
        return text[0].upper() + text[1:]


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    target: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    keepsake: str = ""
    pet: str = ""
    seed: Optional[int] = None


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
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_crash(world: World) -> list[str]:
    out: list[str] = []
    target = world.entities.get("target")
    if target is None or target.meters["broken"] < THRESHOLD:
        return out
    sig = ("crash", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["noise"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__crash__")
    return out


def _r_flame(world: World) -> list[str]:
    out: list[str] = []
    target = world.entities.get("target")
    if target is None or target.meters["broken"] < THRESHOLD or not target.lit:
        return out
    sig = ("flame", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__danger__")
    return out


def _r_ghostly(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["dark"] < THRESHOLD or room.meters["noise"] < THRESHOLD:
        return out
    sig = ("ghostly", "room")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["ghostly"] += 1
    for kid in world.kids():
        kid.memes["imagination"] += 1
    out.append("__ghostly__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="crash", tag="physical", apply=_r_crash),
    Rule(name="flame", tag="physical", apply=_r_flame),
    Rule(name="ghostly", tag="emotional", apply=_r_ghostly),
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


def hazard_at_risk(setting: Setting, target: Target) -> bool:
    return setting.enclosed and target.fragile


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def danger_severity(setting: Setting, target: Target, delay: int) -> int:
    return setting.tightness + target.severity + delay


def is_contained(response: Response, setting: Setting, target: Target, delay: int) -> bool:
    return response.power >= danger_severity(setting, target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_throw(world: World) -> dict:
    sim = world.copy()
    target = sim.get("target")
    _do_throw(sim, target, narrate=False)
    return {
        "broken": target.meters["broken"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
        "ghostly": sim.get("room").meters["ghostly"],
    }


def _do_throw(world: World, target: Entity, narrate: bool = True) -> None:
    boomerang = world.get("boomerang")
    boomerang.meters["moving"] += 1
    target.meters["broken"] += 1
    target.meters["struck"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, setting: Setting, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["curiosity"] += 1
    world.get("room").meters["dark"] += 1
    world.say(f"{setting.opening} {setting.whisper}")
    world.say(
        f"{a.id} and {b.id} climbed in together, close enough to hear each other's breathing."
    )
    world.say(
        f"In {setting.hiding_spot}, {a.id} found an old boomerang painted with fading red swirls."
    )


def ghost_guess(world: World, setting: Setting, a: Entity, b: Entity) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f'"Do you think something invisible lives in here?" {a.id} whispered. '
        f'The dark made every board and beam feel as if it were listening.'
    )
    world.say(
        f'{b.id} looked toward the shadows. "Maybe it is only the wind," {b.pronoun()} said, '
        f'but {b.pronoun("possessive")} voice came out small.'
    )


def tempt(world: World, a: Entity, target: Target) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} held up the boomerang. "I can throw it past {target.the}," '
        f'{a.pronoun()} said. "If it comes back by itself, we will know this place is haunted."'
    )


def warn(world: World, a: Entity, b: Entity, target: Target, parent: Entity) -> None:
    pred = predict_throw(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_ghostly"] = pred["ghostly"]
    extra = ""
    if pred["danger"] >= THRESHOLD and target.lit:
        extra = f" If the boomerang hit {target.the}, a little flame could jump out too."
    elif pred["broken"]:
        extra = f" If the boomerang hit {target.the}, the crash would sound much scarier in the dark."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, do not throw it in here. '
        f'Boomerangs come back, and this place is too cramped.{extra}"'
    )
    world.say(
        f'"If we are worried, we should call {parent.label_word}, not test the dark," {b.id} added.'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    older_sib = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older_sib and b.memes["trust"] >= 6:
        world.say(
            f'"Just one throw," {a.id} said, and because {a.id} was {b.pronoun("possessive")} '
            f'older sibling, {b.id} froze instead of grabbing the boomerang away.'
        )
    else:
        world.say(f'"Just one throw," {a.id} said, stepping back before {b.id} could stop {a.pronoun("object")}.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity, setting: Setting) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} stared into the dark for one more moment, then lowered the boomerang. '
        f'"No," {a.pronoun()} whispered. "This room already feels too strange."'
    )
    world.say(
        f"They took the boomerang straight to {parent.label_word}, who listened, smiled, "
        f"and promised to show them a better place for it in {setting.bright_place} the next day."
    )


def throw_boomerang(world: World, a: Entity, target_ent: Entity, target: Target) -> None:
    _do_throw(world, target_ent)
    world.say(
        f"{a.id} swung the boomerang through the stale air. It curved away into the shadows, "
        f"vanished for one heartbeat, then whipped back too low and too fast."
    )
    world.say(target.crash_text)
    if target.lit:
        world.say(
            "For a blink, a small sharp glow jumped up, and the room looked full of wild moving shadows."
        )


def alarm(world: World, a: Entity, b: Entity, target: Target, parent: Entity) -> None:
    world.say(f'"{a.id}!" {b.id} cried. "{target.The}!"')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, target: Target, setting: Setting) -> None:
    room = world.get("room")
    room.meters["danger"] = 0.0
    world.get("target").meters["broken"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came at once and {response.text.replace('{target}', target.label)}."
    )
    world.say(
        f'Soon the strangest sound in {setting.place} was only the children\'s own shaky breathing.'
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, target: Target) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "Dark rooms can make ordinary sounds feel like ghosts," '
        f'{parent.pronoun()} said softly. "But the real trouble began when the boomerang was thrown where it did not belong."'
    )
    world.say(
        f'"A boomerang needs open sky, not {target.the} and old walls all around it. Promise me you will only use it outside in daylight."'
    )
    world.say(f'"We promise," {a.id} and {b.id} said together.')


def safe_ending(world: World, parent: Entity, a: Entity, b: Entity, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    pet = world.facts.get("pet")
    tail = f" Even {pet} trotted after them." if pet else ""
    world.say(
        f"The next afternoon, {parent.label_word} took them to {setting.bright_place}, where there was room for wide careful throws."
    )
    world.say(
        f"The boomerang arced cleanly over the grass and came home to waiting hands instead of a frightened crash.{tail}"
    )
    world.say(
        "After that, whenever evening shadows made a place feel haunted, they reached for a grown-up and a better plan."
    )


def rescue_fail(world: World, parent: Entity, response: Response, target: Target, setting: Setting) -> None:
    room = world.get("room")
    room.meters["danger"] += 1
    world.say(
        f"{parent.label_word.capitalize()} rushed in and {response.fail.replace('{target}', target.label)}."
    )
    if target.lit:
        world.say(
            "A smoky curl slid along an old hanging cloth before the glow was finally stamped out."
        )
    else:
        world.say(
            f"The broken sound rolled through {setting.place} again and again until even the wind seemed to answer it."
        )


def costly_end(world: World, parent: Entity, a: Entity, b: Entity, target: Target, keepsake: str) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] += 1
    lost = keepsake or "a box of dress-up capes"
    if target.lit:
        world.say(
            f'The children hurried outside while {parent.label_word} made sure every spark was dead. '
            f'When they looked back later, {lost} smelled of smoke and had to be thrown away.'
        )
    else:
        world.say(
            f'The room had to be shut for the night, and {lost} stayed behind until the glass could be cleaned and the broken place fixed.'
        )
    world.say(
        f'{parent.label_word.capitalize()} held them close and said, "Now you know why we do not play guessing games with dark rooms and flying toys."'
    )
    world.say(
        "The boomerang was put away on a high shelf until a bright calm day could be trusted again."
    )


def tell(
    setting: Setting,
    target: Target,
    response: Response,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "grandmother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
    keepsake: str = "",
    pet: str = "",
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            age=instigator_age,
            attrs={"relation": relation},
            traits=["curious"],
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            age=cautioner_age,
            attrs={"relation": relation},
            traits=[trait],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the grown-up",
        )
    )
    world.add(Entity(id="room", type="room", label=setting.place))
    world.add(
        Entity(
            id="boomerang",
            type="boomerang",
            label="boomerang",
            phrase="the old painted boomerang",
            returns_when_thrown=True,
            tags={"boomerang"},
        )
    )
    world.add(
        Entity(
            id="target",
            type="target",
            label=target.label,
            phrase=target.phrase,
            fragile=target.fragile,
            lit=target.lit,
            tags=set(target.tags),
        )
    )

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)

    world.facts["pet"] = pet
    world.facts["relation"] = relation

    opening(world, setting, a, b)
    ghost_guess(world, setting, a, b)

    world.para()
    tempt(world, a, target)
    warn(world, a, b, target, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, parent, setting)
        world.para()
        safe_ending(world, parent, a, b, setting)
        severity = 0
        contained = True
    else:
        defy(world, a, b)
        world.para()
        throw_boomerang(world, a, world.get("target"), target)
        alarm(world, a, b, target, parent)
        severity = danger_severity(setting, target, delay)
        contained = is_contained(response, setting, target, delay)
        world.para()
        if contained:
            rescue(world, parent, response, target, setting)
            lesson(world, parent, a, b, target)
            world.para()
            safe_ending(world, parent, a, b, setting)
        else:
            rescue_fail(world, parent, response, target, setting)
            costly_end(world, parent, a, b, target, keepsake)

    outcome = "averted" if averted else ("contained" if contained else "costly")
    world.facts.update(
        setting=setting,
        target_cfg=target,
        response=response,
        instigator=a,
        cautioner=b,
        parent=parent,
        outcome=outcome,
        severity=severity,
        delay=delay,
        keptsafe=contained,
        keepsake=keepsake,
        boomerang=world.get("boomerang"),
        target=world.get("target"),
        ignited=target.lit and not averted,
    )
    return world


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic",
        opening="The attic smelled of cedar and dust.",
        whisper="The wind pressed at the roof and made the rafters murmur like a room full of secrets.",
        hiding_spot="a long flat trunk under the eaves",
        bright_place="the school field",
        tightness=1,
        enclosed=True,
        tags={"attic", "dark"},
    ),
    "barn_loft": Setting(
        id="barn_loft",
        place="the barn loft",
        opening="The barn loft was high, dim, and full of old hay shadows.",
        whisper="Loose boards clicked softly whenever the evening wind found them.",
        hiding_spot="a heap of old blankets by the wall",
        bright_place="the pasture behind the fence",
        tightness=1,
        enclosed=True,
        tags={"barn", "dark"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the long upstairs hallway",
        opening="The upstairs hallway was narrow and dusky, with moonlight lying in pale bars across the floor.",
        whisper="At the far end, a draft slipped under a door and made a low hollow hum.",
        hiding_spot="a crooked umbrella stand by the stairs",
        bright_place="the empty playground",
        tightness=0,
        enclosed=True,
        tags={"hallway", "dark"},
    ),
    "field": Setting(
        id="field",
        place="the open field",
        opening="The open field held only grass and sky.",
        whisper="Nothing there could pretend to be a ghost for long.",
        hiding_spot="the short grass by the fence",
        bright_place="the open field",
        tightness=0,
        enclosed=False,
        tags={"daylight"},
    ),
}

TARGETS = {
    "oil_lamp": Target(
        id="oil_lamp",
        label="oil lamp",
        phrase="an old oil lamp",
        article="the",
        fragile=True,
        lit=True,
        severity=2,
        crash_text="The boomerang struck the oil lamp with a hard ringing crack. Glass burst, and a little tongue of flame hopped where the lamp had swung.",
        after_text="The broken lamp left the room smelling sharp and smoky.",
        qa_effect="it broke the oil lamp and knocked out a small flame",
        tags={"lamp", "fire", "glass"},
    ),
    "lantern": Target(
        id="lantern",
        label="lantern",
        phrase="a tin lantern with a candle inside",
        article="the",
        fragile=True,
        lit=True,
        severity=1,
        crash_text="The boomerang clipped the lantern. It banged the wall, broke its glass, and a tiny bright flicker jumped onto the floorboards.",
        after_text="The cracked lantern made the shadows jump in all directions.",
        qa_effect="it broke the lantern and let a tiny flame jump out",
        tags={"lantern", "fire", "glass"},
    ),
    "window": Target(
        id="window",
        label="window",
        phrase="a thin old window",
        article="the",
        fragile=True,
        lit=False,
        severity=2,
        crash_text="The boomerang hit the window with a sharp clatter. The pane starred white, then broke open with a cry of glass and a long moaning gust.",
        after_text="Cold night air rushed through the broken pane.",
        qa_effect="it broke the window, and the wind made a ghostly moan through the crack",
        tags={"window", "glass", "wind"},
    ),
    "jar": Target(
        id="jar",
        label="glass jar",
        phrase="a tall glass jar of buttons",
        article="the",
        fragile=True,
        lit=False,
        severity=1,
        crash_text="The boomerang smacked the glass jar. It toppled, shattered, and sent buttons skipping across the boards like tiny running feet.",
        after_text="The scattering buttons sounded almost like something hurrying away.",
        qa_effect="it shattered the glass jar and made buttons rattle everywhere",
        tags={"glass", "jar"},
    ),
    "trunk": Target(
        id="trunk",
        label="wooden trunk",
        phrase="a heavy wooden trunk",
        article="the",
        fragile=False,
        lit=False,
        severity=0,
        crash_text="",
        after_text="",
        qa_effect="",
        tags={"trunk"},
    ),
}

RESPONSES = {
    "blanket_and_broom": Response(
        id="blanket_and_broom",
        sense=3,
        power=3,
        text="threw a wool blanket over the little mess, swept the broken pieces away from small feet, and opened the door for clean air",
        fail="tried to smother the mess with a wool blanket, but the trouble had already spread beyond one quick reach",
        qa_text="covered the danger with a wool blanket and swept the broken pieces away",
        tags={"blanket", "broom", "fire"},
    ),
    "flashlight_and_pan": Response(
        id="flashlight_and_pan",
        sense=3,
        power=2,
        text="clicked on a bright flashlight, guided the children back, and gathered the broken pieces into a dustpan",
        fail="clicked on a flashlight and reached for the broken {target}, but the dark confusion had already turned into a bigger mess",
        qa_text="used a flashlight to guide them back and cleaned up the broken pieces",
        tags={"flashlight", "glass"},
    ),
    "call_for_mop": Response(
        id="call_for_mop",
        sense=1,
        power=1,
        text="called down the stairs for a mop and waited",
        fail="called for a mop first, which was far too slow for what had happened to the {target}",
        qa_text="called for a mop",
        tags={"slow"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "sensible", "steady", "curious", "thoughtful"]
KEEPSAKES = ["a box of dress-up capes", "a paper star map", "grandpa's old puppet stage", ""]
PETS = ["the cat", "the little dog", "the sleepy terrier", ""]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for sid, setting in SETTINGS.items():
        for tid, target in TARGETS.items():
            if hazard_at_risk(setting, target):
                combos.append((sid, tid))
    return combos


KNOWLEDGE = {
    "boomerang": [
        (
            "What is a boomerang?",
            "A boomerang is a curved throwing toy or tool. When it is thrown the right way in open space, it can curve back toward the thrower.",
        )
    ],
    "attic": [
        (
            "What is an attic?",
            "An attic is a room just under the roof of a house. It can feel dark and echoey because it is high up and often full of old things.",
        )
    ],
    "barn": [
        (
            "What is a barn loft?",
            "A barn loft is the high part of a barn where hay or old things can be stored. Sounds can bounce around there and feel spooky at night.",
        )
    ],
    "lamp": [
        (
            "Why can an oil lamp be dangerous?",
            "An oil lamp has flame and glass, so if it is knocked over it can break and start a small fire. That is why it must be kept steady and used carefully.",
        )
    ],
    "lantern": [
        (
            "Why should you be careful around a lantern?",
            "A lantern may have glass and a real flame inside. If it is hit, the glass can break and the flame can jump where it should not be.",
        )
    ],
    "window": [
        (
            "Why can a broken window sound spooky at night?",
            "Wind blowing through a crack can make long humming or moaning sounds. That can feel ghostly even when it is only moving air.",
        )
    ],
    "glass": [
        (
            "Why is broken glass unsafe?",
            "Broken glass can be very sharp and can cut feet or hands. A grown-up should clean it up while children stay back.",
        )
    ],
    "fire": [
        (
            "What should you do if a small flame appears indoors?",
            "Move back and call a grown-up right away. Small flames can grow fast indoors, so quick help matters.",
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight helpful in the dark?",
            "A flashlight gives bright light without fire. It helps people see what is really there instead of guessing from shadows.",
        )
    ],
    "daylight": [
        (
            "Why are boomerangs better in open daylight?",
            "Open daylight gives the boomerang room to curve and return safely. In cramped dark places, it can hit walls or objects before anyone can track it.",
        )
    ],
}
KNOWLEDGE_ORDER = ["boomerang", "attic", "barn", "lamp", "lantern", "window", "glass", "fire", "flashlight", "daylight"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, setting, target = f["instigator"], f["cautioner"], f["setting"], f["target_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a gentle ghost-story for a 3-to-5-year-old that includes the word "boomerang" and ends safely.',
            f"Tell a suspenseful but child-friendly story where {a.id} finds a boomerang in {setting.place}, wants to test whether the dark is haunted, and {b.id} wisely stops the throw.",
            f"Write a cautionary story in a ghost-story mood where curiosity is strong, but the children choose daylight and open space instead of throwing a boomerang indoors.",
        ]
    if outcome == "costly":
        return [
            'Write a cautionary ghost-story for a young child that includes the word "boomerang".',
            f"Tell a spooky story where a child throws a boomerang in {setting.place}, hits {target.the}, and learns that dark guesses and indoor throwing can turn a mystery into real trouble.",
            "Write a suspenseful story where a frightening sound seems ghostly at first, but the true danger comes from a careless choice.",
        ]
    return [
        'Write a short ghost-story for a 3-to-5-year-old that includes the word "boomerang".',
        f"Tell a suspenseful story where children explore {setting.place}, mistake ordinary sounds for something haunted, and a boomerang crash scares them before a grown-up explains what really happened.",
        f"Write a cautionary story where curiosity leads to one bad throw near {target.the}, but the ending shows a safer way to play.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["instigator"], f["cautioner"], f["parent"]
    setting, target, response = f["setting"], f["target_cfg"], f["response"]
    pair = pair_noun(a, b, f.get("relation", "friends"))
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and their {pw} who helps when the dark turns scary.",
        ),
        (
            "Why did the place feel haunted at first?",
            f"The place was dark, and wind or old boards made whispering sounds. In the dark, those ordinary noises felt bigger and stranger than they really were.",
        ),
        (
            f"Why did {b.id} tell {a.id} not to throw the boomerang?",
            f"{b.id} knew a boomerang curves back and needs room. The place was cramped, so it could easily hit {target.the} and make the scary situation worse.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed after {b.id} warned {a.id}?",
                f"{a.id} stopped wanting to test the dark and lowered the boomerang. Because they listened instead of throwing, the mystery stayed only a mystery and no one had to be rescued.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended in daylight, with the children using the boomerang in open space instead of {setting.place}. The ending proves they learned the difference between spooky guessing and careful play.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What happened when {a.id} threw the boomerang?",
                f"It curved back and {target.qa_effect}. The crash sounded ghostly because the room was dark and echoing, but the real cause was the indoor throw.",
            )
        )
        qa.append(
            (
                f"How did {pw} help?",
                f"{pw.capitalize()} came in and {response.qa_text}. That calm help turned the frightening moment into a lesson instead of a bigger disaster.",
            )
        )
        qa.append(
            (
                "What did the children learn?",
                "They learned that shadows and wind can feel spooky, but careless choices are the real danger. After that, they saved the boomerang for open daylight and asked a grown-up when a dark place felt strange.",
            )
        )
    else:
        keepsake = f.get("keepsake") or "some old attic treasures"
        qa.append(
            (
                f"What happened after the boomerang hit {target.the}?",
                f"The trouble became too big for one quick fix, and {keepsake} was lost or left behind. That consequence made the warning feel real, because one curious throw changed the whole night.",
            )
        )
        qa.append(
            (
                "Was it really a ghost?",
                f"No. The sounds felt ghostly because of dark, wind, and the crash. The frightening part came from the boomerang hitting {target.the}, not from a real ghost.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                "It ended more sadly and carefully: everyone was safe, but the boomerang was put away and the room was closed or cleaned before play could happen again. The ending shows that being safe matters more than proving a spooky guess.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"boomerang", "daylight"} | set(f["setting"].tags) | set(f["target_cfg"].tags)
    if f["outcome"] != "averted":
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("fragile", ent.fragile), ("lit", ent.lit), ("returns", ent.returns_when_thrown)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="attic",
        target="oil_lamp",
        response="blanket_and_broom",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="grandmother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
        keepsake="a paper star map",
        pet="the cat",
    ),
    StoryParams(
        setting="barn_loft",
        target="window",
        response="flashlight_and_pan",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="grandfather",
        trait="thoughtful",
        delay=1,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=3,
        keepsake="grandpa's old puppet stage",
        pet="the little dog",
    ),
    StoryParams(
        setting="hallway",
        target="jar",
        response="flashlight_and_pan",
        instigator="Zoe",
        instigator_gender="girl",
        cautioner="Ella",
        cautioner_gender="girl",
        parent="mother",
        trait="sensible",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=4,
        keepsake="a box of dress-up capes",
        pet="",
    ),
    StoryParams(
        setting="attic",
        target="window",
        response="flashlight_and_pan",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="father",
        trait="cautious",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=2,
        keepsake="a box of dress-up capes",
        pet="the sleepy terrier",
    ),
]


def explain_rejection(setting: Setting, target: Target) -> str:
    if not setting.enclosed:
        return (
            f"(No story: {setting.place} is already open space, so a boomerang belongs there. "
            f"This world needs a cramped spooky place where an indoor throw could plausibly hit something.)"
        )
    if not target.fragile:
        return (
            f"(No story: {target.the} would not break, so the throw would not make a sharp cautionary turn. "
            f"Pick a fragile target like a lantern, oil lamp, jar, or window.)"
        )
    return "(No story: this setting and target do not form a good indoor boomerang hazard.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], SETTINGS[params.setting], TARGETS[params.target], params.delay)
    return "contained" if contained else "costly"


ASP_RULES = r"""
hazard(S, T) :- enclosed(S), fragile(T).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, T) :- setting(S), target(T), hazard(S, T).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(V + T + D) :- chosen_target(Tg), severity_base(Tg, V), chosen_setting(S), tightness(S, T), delay(D).
contained :- chosen_response(R), power(R, P), severity(SV), P >= SV.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(costly) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.enclosed:
            lines.append(asp.fact("enclosed", sid))
        lines.append(asp.fact("tightness", sid, setting.tightness))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if target.fragile:
            lines.append(asp.fact("fragile", tid))
        lines.append(asp.fact("severity_base", tid, target.severity))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sens, python_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(80):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a spooky place, a boomerang, and a cautionary choice."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start before the grown-up fully handles the mess")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump the world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible setting/target pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check inline ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.target:
        setting = SETTINGS[args.setting]
        target = TARGETS[args.target]
        if not hazard_at_risk(setting, target):
            raise StoryError(explain_rejection(setting, target))
    if args.setting and not SETTINGS[args.setting].enclosed:
        target_id = args.target or "window"
        raise StoryError(explain_rejection(SETTINGS[args.setting], TARGETS[target_id]))
    if args.target and not TARGETS[args.target].fragile:
        setting_id = args.setting or "attic"
        raise StoryError(explain_rejection(SETTINGS[setting_id], TARGETS[args.target]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.target is None or combo[1] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, target_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["grandmother", "grandfather", "mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    keepsake = rng.choice(KEEPSAKES)
    pet = rng.choice(PETS)

    return StoryParams(
        setting=setting_id,
        target=target_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
        keepsake=keepsake,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting '{params.setting}')")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target '{params.target}')")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}')")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(SETTINGS[params.setting], TARGETS[params.target]):
        raise StoryError(explain_rejection(SETTINGS[params.setting], TARGETS[params.target]))

    world = tell(
        setting=SETTINGS[params.setting],
        target=TARGETS[params.target],
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
        keepsake=params.keepsake,
        pet=params.pet,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, target) pairs:\n")
        for setting, target in combos:
            print(f"  {setting:10} {target}")
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
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.setting}, {p.target}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
