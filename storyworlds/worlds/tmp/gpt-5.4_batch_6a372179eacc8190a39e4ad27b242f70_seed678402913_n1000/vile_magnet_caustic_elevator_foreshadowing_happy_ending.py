#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/vile_magnet_caustic_elevator_foreshadowing_happy_ending.py
======================================================================================

A standalone story world for a superhero-style elevator tale built from the seed
words "vile", "magnet", and "caustic".

Premise
-------
Two children ride an apartment elevator while pretending to be superheroes.
A maintenance cart nearby carries a bottle of caustic cleaner with a vile smell.
A shiny metal object slips near the elevator threshold, and one child wants to
use a magnet to fish it out like a hero. The other child or a grown-up warns
that the clever-looking shortcut could tip the cleaner or draw the wrong metal
part. Depending on ages, trust, response, and delay, the danger is either
averted, safely contained, or turns into a bigger building problem. The happy
ending path gives the children a safe tool and a better way to ask for help.

Run it
------
    python storyworlds/worlds/gpt-5.4/vile_magnet_caustic_elevator_foreshadowing_happy_ending.py
    python storyworlds/worlds/gpt-5.4/vile_magnet_caustic_elevator_foreshadowing_happy_ending.py --target key_ring
    python storyworlds/worlds/gpt-5.4/vile_magnet_caustic_elevator_foreshadowing_happy_ending.py --target plush_badge
    python storyworlds/worlds/gpt-5.4/vile_magnet_caustic_elevator_foreshadowing_happy_ending.py --response towel
    python storyworlds/worlds/gpt-5.4/vile_magnet_caustic_elevator_foreshadowing_happy_ending.py --all
    python storyworlds/worlds/gpt-5.4/vile_magnet_caustic_elevator_foreshadowing_happy_ending.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/vile_magnet_caustic_elevator_foreshadowing_happy_ending.py --verify
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
CAUTIOUS_TRAITS = {"careful", "patient", "sensible", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    magnetic: bool = False
    caustic: bool = False
    movable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "superheroine"}
        male = {"boy", "father", "dad", "man", "superhero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "superintendent": "super"}.get(self.type, self.type)


@dataclass
class Mission:
    id: str
    team_name: str
    boast: str
    costume_line: str
    quest: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    material: str
    place: str
    danger_line: str
    magnetic: bool = True
    snag_risk: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Cleaner:
    id: str
    label: str
    phrase: str
    smell: str
    warning: str
    caustic_word: str
    strength: int = 2
    caustic: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill_harms(world: World) -> list[str]:
    out: list[str] = []
    spill = world.entities.get("spill")
    if not spill or spill.meters["present"] < THRESHOLD:
        return out
    sig = ("spill_harms", "spill")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    elevator = world.get("elevator")
    elevator.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__spill__")
    return out


def _r_fumes(world: World) -> list[str]:
    out: list[str] = []
    spill = world.entities.get("spill")
    if not spill or spill.meters["present"] < THRESHOLD:
        return out
    sig = ("fumes", "spill")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spill.meters["fumes"] += 1
    out.append("The sharp smell grew even stronger, and nobody wanted to stand close.")
    return out


CAUSAL_RULES = [
    Rule(name="spill_harms", tag="physical", apply=_r_spill_harms),
    Rule(name="fumes", tag="physical", apply=_r_fumes),
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
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(target: Target, cleaner: Cleaner) -> bool:
    return target.magnetic and cleaner.caustic


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def spill_severity(target: Target, cleaner: Cleaner, delay: int) -> int:
    return target.snag_risk + cleaner.strength + delay


def is_contained(response: Response, target: Target, cleaner: Cleaner, delay: int) -> bool:
    return response.power >= spill_severity(target, cleaner, delay)


def predict_spill(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_magnet_try(sim, sim.get(target_id), narrate=False)
    spill = sim.get("spill")
    return {
        "spills": spill.meters["present"] >= THRESHOLD,
        "danger": sim.get("elevator").meters["danger"],
    }


def _do_magnet_try(world: World, target_ent: Entity, narrate: bool = True) -> None:
    target_ent.meters["tugged"] += 1
    world.get("cart").meters["jostled"] += 1
    world.get("bottle").meters["tipped"] += 1
    world.get("spill").meters["present"] += 1
    world.get("spill").meters["caustic"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, a: Entity, b: Entity, mission: Mission) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["heroic"] += 1
    world.say(
        f"After school, {a.id} and {b.id} stepped into the apartment elevator as "
        f"{mission.team_name}. {mission.costume_line}"
    )
    world.say(f'"{mission.boast}" {a.id} said, and even the small brass buttons seemed to shine.')
    world.say(
        "The elevator hummed upward, and beside the open doors in the hall waited a maintenance cart."
    )


def foreshadow(world: World, b: Entity, cleaner: Cleaner) -> None:
    world.say(
        f"On the cart sat {cleaner.phrase}. A vile smell slipped into the elevator, "
        f"and {b.id} wrinkled {b.pronoun('possessive')} nose."
    )
    world.say(
        f'Taped to the bottle was a bright warning: "{cleaner.warning}". It looked boring, '
        "but it felt important."
    )


def problem(world: World, a: Entity, b: Entity, mission: Mission, target: Target) -> None:
    a.memes["desire"] += 1
    world.say(
        f"Just then, {target.phrase} skittered to {target.place}. It was part of "
        f"{mission.quest}, so to {a.id} it did not look like a little problem. It looked like a mission."
    )
    world.say(f'"I can save it," {a.id} whispered.')


def tempt(world: World, a: Entity, target: Target) -> None:
    a.memes["bravado"] += 1
    world.say(
        f"{a.id} spotted a toy magnet clipped to the side of the cart. "
        f'"A magnet can pull the {target.label} right back," {a.pronoun()} said.'
    )


def warn(world: World, b: Entity, a: Entity, target: Target, cleaner: Cleaner, adult: Entity) -> None:
    pred = predict_spill(world, "target")
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} took one step back from the smell."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, don\'t. '
        f'That bottle is {cleaner.caustic_word}, and if the magnet snags the wrong metal bit, '
        f'it could tip the cart."{extra}'
    )
    world.say(
        f'{adult.label_word.capitalize()} had once said that when something slips near elevator doors, '
        "children should ask a grown-up instead of poking at it."
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"Real heroes act fast," {a.id} said. Because {a.id} was the older one, '
            f"{b.id} could not quite stop {a.pronoun('object')}."
        )
    else:
        world.say(f'"Real heroes act fast," {a.id} said, and reached for the magnet anyway.')


def back_down(world: World, a: Entity, b: Entity, mission: Mission, adult: Entity) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at the warning label, then at the ugly-smelling bottle, and lowered the magnet. '
        f'"Maybe the brave thing is calling {adult.label_word}," {a.pronoun()} admitted.'
    )
    world.say(
        f"{b.id} grinned. For a moment they stood still like superheroes waiting for instructions, "
        "and nothing bad happened."
    )
    world.say(
        f"Soon the mission changed from grabbing things to keeping the hallway safe until {adult.label_word} came."
    )


def spill(world: World, target_ent: Entity, target: Target, cleaner: Cleaner) -> None:
    _do_magnet_try(world, target_ent)
    world.say(
        f"The magnet did not pull only the {target.label}. It caught a metal clip on the cart with a snap, "
        f"and {cleaner.phrase} lurched sideways."
    )
    world.say(
        f"A thin stream splashed onto the elevator floor. The smell turned even more vile, "
        f"and the bright word {cleaner.caustic_word} suddenly seemed huge."
    )


def alarm(world: World, b: Entity, adult: Entity) -> None:
    world.say(f'"Back up!" {b.id} cried.')
    world.say(f'"{adult.label_word.upper()}! We need help by the elevator!"')


def rescue(world: World, adult: Entity, response: Response, mission: Mission) -> None:
    world.get("spill").meters["present"] = 0.0
    world.get("elevator").meters["danger"] = 0.0
    body = response.text
    world.say(f"{adult.label_word.capitalize()} came fast and {body}.")
    world.say(
        f"Soon the sharp smell faded, the floor was safe again, and the little elevator felt like "
        f"{mission.ending}."
    )


def lesson(world: World, adult: Entity, a: Entity, b: Entity, cleaner: Cleaner) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
    world.say("Nobody spoke for one breath.")
    world.say(
        f'Then {adult.label_word} crouched beside them. "I am glad you called," {adult.pronoun()} said. '
        f'"But remember this: a magnet is not a toy for elevator cracks, and {cleaner.caustic_word} cleaners '
        f'can burn skin. If something falls near the doors, you get a grown-up."'
    )
    world.say(f'"We will," said {b.id} and {a.id} together.')


def safe_tool(world: World, adult: Entity, a: Entity, b: Entity, mission: Mission) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next day, {adult.label_word} showed them a long plastic grabber with a soft rubber tip."
    )
    world.say(
        f'"This is for grown-up helpers," {adult.pronoun()} explained, "and the first power is still asking."'
    )
    world.say(
        f"{a.id} and {b.id} pretended the grabber was rescue gear, but this time they kept it far away from "
        "the real elevator doors."
    )
    world.say(f"In their game, the bravest heroes were the ones who stopped, thought, and kept everyone safe.")


def rescue_fail(world: World, adult: Entity, response: Response) -> None:
    world.get("elevator").meters["closed"] += 1
    body = response.fail
    world.say(f"{adult.label_word.capitalize()} {body}.")
    world.say(
        "The spill had spread too far, so yellow tape went up and the elevator had to stay closed for the rest of the day."
    )


def loss(world: World, a: Entity, b: Entity, mission: Mission) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"The children had to take the long stairs instead, and their superhero mission ended in tired feet and quiet faces."
    )
    world.say(
        f"No one was hurt, but the closed elevator made the whole hallway feel less like {mission.ending} and more like a warning."
    )


def grim_lesson(world: World, adult: Entity, a: Entity, b: Entity, cleaner: Cleaner) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{adult.label_word.capitalize()} kept them close and said, "You are safe, and that matters most. '
        f'But now you know why we never touch a {cleaner.caustic_word} spill and never reach into elevator gaps."'
    )
    world.say(
        f"After that, whenever a game made {a.id} or {b.id} feel too fast and bold, they remembered the smell and chose help first."
    )


def tell(
    mission: Mission,
    target: Target,
    cleaner: Cleaner,
    response: Response,
    *,
    instigator: str = "Max",
    instigator_gender: str = "boy",
    cautioner: str = "Lila",
    cautioner_gender: str = "girl",
    trait: str = "careful",
    adult_type: str = "superintendent",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
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
            traits=["bold"],
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
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            role="adult",
            label="the building super",
        )
    )
    world.add(Entity(id="elevator", type="elevator", label="the elevator"))
    world.add(Entity(id="cart", type="cart", label="the maintenance cart"))
    world.add(Entity(id="bottle", type="bottle", label=cleaner.label, caustic=cleaner.caustic))
    target_ent = world.add(
        Entity(id="target", type="target", label=target.label, magnetic=target.magnetic, tags=set(target.tags))
    )
    world.add(Entity(id="spill", type="spill", label="the spill", caustic=True, movable=False))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)

    opening(world, a, b, mission)
    foreshadow(world, b, cleaner)
    world.para()
    problem(world, a, b, mission, target)
    tempt(world, a, target)
    warn(world, b, a, target, cleaner, adult)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, mission, adult)
        world.para()
        safe_tool(world, adult, a, b, mission)
        severity = 0
        contained = True
    else:
        defy(world, a, b)
        world.para()
        spill(world, target_ent, target, cleaner)
        alarm(world, b, adult)
        severity = spill_severity(target, cleaner, delay)
        world.get("spill").meters["severity"] = float(severity)
        contained = is_contained(response, target, cleaner, delay)
        world.para()
        if contained:
            rescue(world, adult, response, mission)
            lesson(world, adult, a, b, cleaner)
            world.para()
            safe_tool(world, adult, a, b, mission)
        else:
            rescue_fail(world, adult, response)
            loss(world, a, b, mission)
            grim_lesson(world, adult, a, b, cleaner)

    outcome = "averted" if averted else ("contained" if contained else "closed")
    world.facts.update(
        mission=mission,
        target_cfg=target,
        cleaner=cleaner,
        response=response,
        instigator=a,
        cautioner=b,
        adult=adult,
        target=target_ent,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


MISSIONS = {
    "sky_shield": Mission(
        id="sky_shield",
        team_name="Sky Shield and Bolt Girl",
        boast="Citizens of Floor Nine, your elevator heroes are on patrol",
        costume_line="One towel became a cape, and a paper star on a string became their rescue badge",
        quest="finding the lost rescue badge",
        ending="a bright silver launch bay",
        tags={"superhero", "elevator"},
    ),
    "comet_team": Mission(
        id="comet_team",
        team_name="The Comet Team",
        boast="No tiny emergency is too tricky for us",
        costume_line="Their sneakers thumped like hero boots, and their hands made whooshing flight sounds",
        quest="saving the secret mission key",
        ending="a safe little hero tower",
        tags={"superhero", "elevator"},
    ),
    "thunder_twins": Mission(
        id="thunder_twins",
        team_name="The Thunder Twins",
        boast="Up, up, and safely away",
        costume_line="A scarf fluttered like a cape, and a cardboard wristband served as a power cuff",
        quest="recovering the hallway treasure token",
        ending="the headquarters of the kindest heroes",
        tags={"superhero", "elevator"},
    ),
}

TARGETS = {
    "key_ring": Target(
        id="key_ring",
        label="key ring",
        phrase="a little key ring",
        material="metal",
        place="the thin crack by the elevator threshold",
        danger_line="It had slipped where small hands should not reach",
        magnetic=True,
        snag_risk=1,
        tags={"key", "metal"},
    ),
    "badge_pin": Target(
        id="badge_pin",
        label="badge pin",
        phrase="a shiny badge pin",
        material="metal",
        place="the groove beside the sliding door",
        danger_line="It glittered just enough to make grabbing it seem easy",
        magnetic=True,
        snag_risk=2,
        tags={"metal", "pin"},
    ),
    "screw": Target(
        id="screw",
        label="loose screw",
        phrase="a loose screw",
        material="metal",
        place="the corner near the sill",
        danger_line="It looked tiny, but metal things near machines can matter",
        magnetic=True,
        snag_risk=2,
        tags={"metal", "machine"},
    ),
    "plush_badge": Target(
        id="plush_badge",
        label="cloth badge",
        phrase="a cloth badge",
        material="cloth",
        place="the crack by the elevator threshold",
        danger_line="It was soft cloth, not something a magnet could pull",
        magnetic=False,
        snag_risk=0,
        tags={"cloth"},
    ),
}

CLEANERS = {
    "drain_gel": Cleaner(
        id="drain_gel",
        label="drain gel",
        phrase="a squat bottle of caustic drain gel",
        smell="vile",
        warning="CAUSTIC - KEEP OFF SKIN",
        caustic_word="caustic",
        strength=2,
        tags={"caustic", "cleaner"},
    ),
    "oven_spray": Cleaner(
        id="oven_spray",
        label="oven spray",
        phrase="a can of caustic oven spray",
        smell="vile",
        warning="CAUSTIC CLEANER - DO NOT TOUCH",
        caustic_word="caustic",
        strength=2,
        tags={"caustic", "cleaner"},
    ),
    "stripper": Cleaner(
        id="stripper",
        label="floor stripper",
        phrase="a bottle of caustic floor stripper",
        smell="vile",
        warning="CAUSTIC - ADULTS ONLY",
        caustic_word="caustic",
        strength=3,
        tags={"caustic", "cleaner"},
    ),
}

RESPONSES = {
    "block_and_call": Response(
        id="block_and_call",
        sense=3,
        power=4,
        text="pressed the elevator hold button, moved the children back, blocked the hall, and used thick gloves and absorbent pads to gather the spill before calling for proper cleanup",
        fail="pressed the hold button and tried to control the spill, but too much of it had already spread under the door track to make the elevator safe right away",
        qa_text="blocked the elevator, kept everyone back, and cleaned the spill with gloves and absorbent pads",
        tags={"cleanup", "adult_help"},
    ),
    "neutralizer": Response(
        id="neutralizer",
        sense=3,
        power=5,
        text="closed the doors to the cart, brought out the spill kit, and treated the mess the careful building way before anyone came near it again",
        fail="used the spill kit, but the cleaner had already spread too far and the elevator still had to be closed",
        qa_text="used the building spill kit and made the area safe",
        tags={"cleanup", "adult_help", "spill_kit"},
    ),
    "paper_towels": Response(
        id="paper_towels",
        sense=2,
        power=2,
        text="kept the children back and blotted up the sharp cleaner with paper towels until the floor was dry enough to wash properly",
        fail="grabbed paper towels, but they soaked through too fast and could not make the caustic spill safe",
        qa_text="kept the children back and blotted up the cleaner with paper towels",
        tags={"cleanup", "adult_help"},
    ),
    "towel": Response(
        id="towel",
        sense=1,
        power=1,
        text="wiped the spill with one hallway towel",
        fail="wiped at the spill with one hallway towel, but it only smeared the mess wider",
        qa_text="wiped the spill with one towel",
        tags={"cleanup"},
    ),
}

GIRL_NAMES = ["Lila", "Nora", "Maya", "Ava", "Zoe", "Ivy", "Lucy", "Tess"]
BOY_NAMES = ["Max", "Eli", "Noah", "Finn", "Sam", "Leo", "Jack", "Ben"]
TRAITS = ["careful", "steady", "patient", "thoughtful", "sensible", "kind"]


@dataclass
class StoryParams:
    mission: str
    target: str
    cleaner: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    adult: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    seed: Optional[int] = None


KNOWLEDGE = {
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet pulls some kinds of metal toward it. That is why it can move certain things without your fingers touching them."
        )
    ],
    "caustic": [
        (
            "What does caustic mean?",
            "Caustic means a chemical is strong enough to burn or hurt skin. Children should never touch a caustic cleaner."
        )
    ],
    "elevator": [
        (
            "Why should children keep their hands out of elevator cracks?",
            "Elevator doors and tracks are machine parts, not play spaces. Small fingers can get pinched, and dropped things should be handled by grown-ups."
        )
    ],
    "spill": [
        (
            "What should you do if a strong cleaner spills?",
            "Move back right away and tell a grown-up. Strong cleaners can hurt skin and make bad fumes, so adults need to handle them."
        )
    ],
    "warning": [
        (
            "Why do warning labels matter?",
            "Warning labels tell you when something can hurt you. Reading and obeying them helps you stay safe before a problem grows."
        )
    ],
    "hero": [
        (
            "What makes someone a real hero?",
            "A real hero keeps people safe, even if that means stopping and asking for help. Brave does not mean rushing into danger."
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool that helps adults pick things up from a safer distance. It is useful, but children still need permission and help."
        )
    ],
    "spill_kit": [
        (
            "What is a spill kit?",
            "A spill kit is a set of safety supplies for cleaning up dangerous messes. It can include pads, gloves, and other things adults use to make an area safe."
        )
    ],
}
KNOWLEDGE_ORDER = ["hero", "magnet", "caustic", "warning", "elevator", "spill", "grabber", "spill_kit"]


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
    a = f["instigator"]
    b = f["cautioner"]
    mission = f["mission"]
    target = f["target_cfg"]
    cleaner = f["cleaner"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a superhero story for a 3-to-5-year-old set in an elevator that includes the words "vile", "magnet", and "{cleaner.caustic_word}".',
            f"Tell a cautionary-but-happy story where {a.id} wants to use a magnet to rescue a {target.label}, but {b.id} stops the risky plan before the caustic cleaner spills.",
            f"Write a foreshadowing story where a warning smell and label matter later, and the children learn that the bravest heroes ask a grown-up for help.",
        ]
    if outcome == "closed":
        return [
            f'Write a superhero story for a 3-to-5-year-old set in an elevator that includes the words "vile", "magnet", and "{cleaner.caustic_word}".',
            f"Tell a cautionary story where {a.id} uses a magnet near elevator doors, a caustic cleaner spills, and the elevator has to be closed even though everyone stays safe.",
            f"Write a foreshadowing story where a warning label is ignored at first and the ending proves why it mattered.",
        ]
    return [
        f'Write a superhero story for a 3-to-5-year-old set in an elevator that includes the words "vile", "magnet", and "{cleaner.caustic_word}".',
        f"Tell a happy cautionary story where children playing superheroes make one risky choice with a magnet, but a grown-up safely handles the caustic spill and teaches them what real bravery means.",
        f"Write a story with foreshadowing in which a bad smell and warning label appear early, then matter during the main danger and the safe ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    adult = f["adult"]
    mission = f["mission"]
    target = f["target_cfg"]
    cleaner = f["cleaner"]
    response = f["response"]
    pair = pair_noun(a, b, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, pretending to be superheroes in an elevator. The building {adult.label_word} is the grown-up who helps when the danger turns real."
        ),
        (
            "What was the early clue that something could go wrong?",
            f"The children noticed a vile smell and a warning label on {cleaner.phrase}. That foreshadowed the danger, because the bottle later became the source of the risky spill."
        ),
        (
            f"Why did {a.id} want the magnet?",
            f"{a.id} thought the magnet could rescue the {target.label} from {target.place}. It felt like a superhero shortcut, which is why the idea seemed exciting before it seemed dangerous."
        ),
        (
            f"Why was that a bad idea?",
            f"It was dangerous because the magnet could snag the wrong metal part near the elevator and jostle the cart. The cart held a {cleaner.caustic_word} cleaner, so one quick tug could create a much bigger problem."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What happened after {b.id} warned {a.id}?",
                f"{a.id} stopped and did not use the magnet after all. That kept the caustic cleaner from spilling and turned the children into careful heroes instead of rushed ones."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with the children learning a safer way to help. The next day they saw a proper grabber tool and understood that asking first is part of being brave."
            )
        )
    elif f["outcome"] == "contained":
        body = response.qa_text
        qa.append(
            (
                f"How did the building {adult.label_word} fix the problem?",
                f"The building {adult.label_word} {body}. That fast, calm response kept the danger from spreading and made the elevator safe again."
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that a magnet is not for fishing around elevator doors and that {cleaner.caustic_word} cleaners can hurt people. The lesson mattered because the early warning smell had already told them the bottle was not safe to touch."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a happy new picture of heroism: stopping, thinking, and getting help. The safe grabber tool at the end showed that good tools and good choices are different from reckless shortcuts."
            )
        )
    else:
        qa.append(
            (
                f"Could the building {adult.label_word} save the elevator right away?",
                f"No. The building {adult.label_word} tried, but the spill had spread too far and the elevator had to stay closed. Everyone was safe, yet the closed elevator proved that one risky choice can spoil the whole day."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely but sadly, with the children climbing the stairs and remembering the smell and warning label. They were not hurt, but the lost elevator made the caution feel real."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"hero", "magnet", "caustic", "warning", "elevator"}
    if f["outcome"] != "averted":
        tags.add("spill")
    if f["outcome"] in {"averted", "contained"}:
        tags.add("grabber")
    if "spill_kit" in f["response"].tags:
        tags.add("spill_kit")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [name for name, on in (("magnetic", e.magnetic), ("caustic", e.caustic), ("movable", e.movable)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:9} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="sky_shield",
        target="key_ring",
        cleaner="drain_gel",
        response="block_and_call",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Lila",
        cautioner_gender="girl",
        adult="superintendent",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        mission="comet_team",
        target="badge_pin",
        cleaner="oven_spray",
        response="neutralizer",
        instigator="Nora",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        adult="father",
        trait="steady",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        mission="thunder_twins",
        target="screw",
        cleaner="stripper",
        response="paper_towels",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Maya",
        cautioner_gender="girl",
        adult="superintendent",
        trait="patient",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="friends",
        trust=3,
    ),
    StoryParams(
        mission="sky_shield",
        target="badge_pin",
        cleaner="stripper",
        response="neutralizer",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Ivy",
        cautioner_gender="girl",
        adult="mother",
        trait="sensible",
        delay=0,
        instigator_age=4,
        cautioner_age=7,
        relation="siblings",
        trust=4,
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for target_id, target in TARGETS.items():
            for cleaner_id, cleaner in CLEANERS.items():
                if hazard_at_risk(target, cleaner):
                    combos.append((mission_id, target_id, cleaner_id))
    return combos


def explain_rejection(target: Target, cleaner: Cleaner) -> str:
    if not target.magnetic:
        return (
            f"(No story: the {target.label} is {target.material}, so a magnet would not pull it. "
            "Without that tempting shortcut, this elevator danger never honestly starts.)"
        )
    if not cleaner.caustic:
        return (
            f"(No story: {cleaner.label} is not modeled as a caustic danger here, so the warning-and-spill plot has no real stakes.)"
        )
    return "(No story: this combination has no plausible elevator hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a safer cleanup like {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], TARGETS[params.target], CLEANERS[params.cleaner], params.delay)
    return "contained" if contained else "closed"


ASP_RULES = r"""
hazard(Tg, C) :- magnetic_target(Tg), caustic_cleaner(C).
sensible(R)   :- response(R), sense(R, S), sense_min(M), S >= M.
valid(M, Tg, C) :- mission(M), target(Tg), cleaner(C), hazard(Tg, C).

cautious_now(T)  :- trait(T), is_cautious(T).
init_caution(5)  :- trait(T), cautious_now(T).
init_caution(3)  :- trait(T), not cautious_now(T).
cautioner_older  :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4)         :- cautioner_older.
bonus(0)         :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted          :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(Sn + St + D) :- chosen_target(Tg), snag_risk(Tg, Sn),
                         chosen_cleaner(C), strength(C, St), delay(D).
resp_power(P)    :- chosen_response(R), power(R, P).
contained        :- resp_power(P), severity(V), P >= V.

outcome(averted)   :- averted.
outcome(contained) :- not averted, contained.
outcome(closed)    :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        if target.magnetic:
            lines.append(asp.fact("magnetic_target", target_id))
        lines.append(asp.fact("snag_risk", target_id, target.snag_risk))
    for cleaner_id, cleaner in CLEANERS.items():
        lines.append(asp.fact("cleaner", cleaner_id))
        if cleaner.caustic:
            lines.append(asp.fact("caustic_cleaner", cleaner_id))
        lines.append(asp.fact("strength", cleaner_id, cleaner.strength))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_cleaner", params.cleaner),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(120):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: superheroes, an elevator, a magnet shortcut, and a caustic warning."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--cleaner", choices=CLEANERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["mother", "father", "superintendent"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and args.cleaner:
        target = TARGETS[args.target]
        cleaner = CLEANERS[args.cleaner]
        if not hazard_at_risk(target, cleaner):
            raise StoryError(explain_rejection(target, cleaner))
    if args.target and not TARGETS[args.target].magnetic:
        cleaner = CLEANERS[args.cleaner] if args.cleaner else next(iter(CLEANERS.values()))
        raise StoryError(explain_rejection(TARGETS[args.target], cleaner))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.mission is None or c[0] == args.mission)
        and (args.target is None or c[1] == args.target)
        and (args.cleaner is None or c[2] == args.cleaner)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission, target, cleaner = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    adult = args.adult or rng.choice(["mother", "father", "superintendent"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        mission=mission,
        target=target,
        cleaner=cleaner,
        response=response,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        adult=adult,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission '{params.mission}'.)")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target '{params.target}'.)")
    if params.cleaner not in CLEANERS:
        raise StoryError(f"(Unknown cleaner '{params.cleaner}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}'.)")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(TARGETS[params.target], CLEANERS[params.cleaner]):
        raise StoryError(explain_rejection(TARGETS[params.target], CLEANERS[params.cleaner]))

    world = tell(
        MISSIONS[params.mission],
        TARGETS[params.target],
        CLEANERS[params.cleaner],
        RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        adult_type=params.adult,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
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
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (mission, target, cleaner) combos:\n")
        for mission, target, cleaner in combos:
            print(f"  {mission:14} {target:10} {cleaner}")
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
                f"### {p.instigator} & {p.cautioner}: {p.target} with {p.cleaner} "
                f"({p.mission}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
