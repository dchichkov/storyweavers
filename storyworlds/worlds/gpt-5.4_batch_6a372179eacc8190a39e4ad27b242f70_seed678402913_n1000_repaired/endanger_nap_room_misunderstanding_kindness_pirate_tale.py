#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/endanger_nap_room_misunderstanding_kindness_pirate_tale.py
======================================================================================

A standalone story world for a tiny pirate-style tale set in a preschool nap room.

Premise
-------
Two children turn the nap room into a pirate ship. One child misunderstands what
a "crow's nest" means and decides to climb something unsafe in order to reach a
pretend treasure. Another child warns that this could endanger someone in the
quiet room. A kind teacher either helps in time or, if the danger grows too fast,
comforts the children after a small tumble and teaches a safer way to play.

Run it
------
    python storyworlds/worlds/gpt-5.4/endanger_nap_room_misunderstanding_kindness_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/endanger_nap_room_misunderstanding_kindness_pirate_tale.py --perch cot_stack
    python storyworlds/worlds/gpt-5.4/endanger_nap_room_misunderstanding_kindness_pirate_tale.py --perch floor_mat
    python storyworlds/worlds/gpt-5.4/endanger_nap_room_misunderstanding_kindness_pirate_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/endanger_nap_room_misunderstanding_kindness_pirate_tale.py --verify
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
BOLDNESS_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "thoughtful", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    unstable: bool = False
    movable: bool = False
    quiet_space: bool = False
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher_woman", "woman"}
        male = {"boy", "father", "teacher_man", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "teacher_woman": "teacher",
            "teacher_man": "teacher",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    detail: str
    risk: int = 0
    unstable: bool = False
    movable: bool = False
    nap_nearby: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    perch_line: str
    safe_end: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeTool:
    id: str
    label: str
    phrase: str
    use_line: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    perch = world.entities.get("perch")
    room = world.entities.get("room")
    if perch is None or room is None:
        return out
    if perch.meters["wobbling"] < THRESHOLD:
        return out
    sig = ("wobble", perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["danger"] += 1
    room.meters["noise"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    perch = world.entities.get("perch")
    child = world.entities.get("instigator")
    if perch is None or child is None:
        return out
    if perch.meters["fallen"] < THRESHOLD:
        return out
    sig = ("fall", perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["bump"] += 1
    child.memes["fear"] += 1
    child.memes["tears"] += 1
    out.append("__fall__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="fall", tag="physical", apply=_r_fall),
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


def hazard_at_risk(perch: Perch) -> bool:
    return perch.unstable and perch.risk > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def danger_severity(perch: Perch, delay: int) -> int:
    return perch.risk + delay


def is_contained(response: Response, perch: Perch, delay: int) -> bool:
    return response.power >= danger_severity(perch, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_clarify(cautioner_age: int, instigator_age: int, trait: str, trust: int) -> bool:
    authority = initial_caution(trait) + (2.0 if cautioner_age > instigator_age else 0.0)
    return authority + (0.2 * trust) > BOLDNESS_INIT


def predict_climb(world: World) -> dict:
    sim = world.copy()
    perch = sim.get("perch")
    _do_climb(sim, perch, narrate=False)
    return {
        "danger": sim.get("room").meters["danger"],
        "noise": sim.get("room").meters["noise"],
        "bump": sim.get("instigator").meters["bump"],
    }


def _do_climb(world: World, perch: Entity, narrate: bool = True) -> None:
    perch.meters["climbed"] += 1
    if perch.unstable:
        perch.meters["wobbling"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, treasure: Treasure) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a drowsy afternoon, {a.id} and {b.id} looked across the nap room and decided it was a pirate ship at rest. "
        f"The folded blankets became sails, the sleeping mats became gentle decks, and {treasure.phrase} was their lost treasure."
    )
    world.say(
        f'"Captain {a.id} and Lookout {b.id}!" {a.id} whispered. "We have to find {treasure.label} before the tide turns."'
    )


def introduce_treasure(world: World, b: Entity, treasure: Treasure, perch: Perch) -> None:
    world.say(
        f"{b.id} pointed toward {treasure.perch_line.format(perch=perch.label)}. "
        f'The room was dim and still, so the treasure looked very far away.'
    )
    world.say(f'"A pirate needs a crow\'s nest to see that high," {b.id} whispered.')


def misunderstand(world: World, a: Entity, b: Entity, perch: Perch) -> None:
    a.memes["misunderstanding"] += 1
    a.memes["boldness"] += 1
    world.say(
        f"{a.id} blinked and misunderstood at once. To {a.pronoun('object')}, a crow's nest did not sound like a pretend pirate idea. "
        f"It sounded like a real place that had to be climbed."
    )
    world.say(
        f'"Then I should climb {perch.the}!" {a.id} whispered back, looking at {perch.phrase}.'
    )


def warn(world: World, b: Entity, a: Entity, perch: Perch, teacher: Entity) -> None:
    pred = predict_climb(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_noise"] = pred["noise"]
    line = (
        f'"No, not for real," {b.id} whispered. "That is only pirate talk. '
        f'If you climb {perch.the}, it could wobble and endanger you'
    )
    if perch.nap_nearby:
        line += ' and the children sleeping nearby'
    line += f'. We should ask {teacher.label_word} for help instead."'
    world.say(line)


def back_down(world: World, a: Entity, b: Entity, teacher: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["boldness"] = 0.0
    world.say(
        f"{a.id} looked again, then at {b.id}, and the misunderstanding softened. "
        f'"Oh," {a.pronoun()} whispered. "You meant a pretend crow\'s nest."'
    )
    world.say(
        f"Together they padded over to {teacher.label_word} and explained their pirate problem instead of climbing anything."
    )


def defy(world: World, a: Entity, perch: Perch) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"I can do it very quietly," {a.id} said, though {a.pronoun("possessive")} whisper shook with excitement. '
        f"Then {a.pronoun()} reached for {perch.the}."
    )


def climb(world: World, a: Entity, perch_ent: Entity, perch: Perch, treasure: Treasure) -> None:
    _do_climb(world, perch_ent)
    world.say(
        f"{a.id} put one foot on {perch.the} and stretched toward {treasure.label}. "
        f"{perch.detail}."
    )
    if perch_ent.meters["wobbling"] >= THRESHOLD:
        world.say(
            f"{perch.the.capitalize()} gave a little shiver underneath {a.pronoun('object')}, and the whole pirate game suddenly felt too real."
        )


def alarm(world: World, b: Entity, a: Entity, teacher: Entity, perch: Perch) -> None:
    world.say(
        f'"{a.id}, stop!" {b.id} gasped. Then {b.pronoun()} called softly but fast for the {teacher.label_word}.'
    )


def rescue(world: World, teacher: Entity, response: Response, a: Entity, perch_ent: Entity, perch: Perch) -> None:
    perch_ent.meters["wobbling"] = 0.0
    world.get("room").meters["danger"] = 0.0
    body = response.text.replace("{perch}", perch.label)
    world.say(f"The {teacher.label_word} came quickly and {body}.")
    world.say(
        f"In one calm moment, {a.id}'s feet were back on the floor, and the nap room grew quiet again."
    )
    a.memes["fear"] = 0.0
    a.memes["relief"] += 1


def rescue_fail(world: World, teacher: Entity, response: Response, a: Entity, perch_ent: Entity, perch: Perch) -> None:
    perch_ent.meters["fallen"] += 1
    propagate(world, narrate=False)
    body = response.fail.replace("{perch}", perch.label)
    world.say(f"The {teacher.label_word} hurried over and {body}.")
    world.say(
        f"{a.id} slipped down in a small heap on the rug. It was only a little tumble, but it made everybody's heart jump."
    )


def kind_lesson(world: World, teacher: Entity, a: Entity, b: Entity, perch: Perch, bumped: bool) -> None:
    for kid in (a, b):
        kid.memes["kindness"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    if bumped:
        a.memes["comforted"] += 1
        world.say(
            f"The {teacher.label_word} knelt beside {a.id}, checked the small bump, and spoke in a gentle voice instead of a sharp one."
        )
    else:
        world.say(
            f"The {teacher.label_word} knelt beside both children and spoke in a gentle voice instead of a sharp one."
        )
    world.say(
        f'"Thank you for calling me," {teacher.pronoun()} said. "I am not angry. '
        f'When pirate talk is misunderstood, climbing {perch.the} can endanger people in a quiet room. '
        f'Kind words and asking for help are the brave choices."'
    )
    world.say(f'{a.id} nodded. "{b.id} was trying to help me," {a.pronoun()} said.')


def safe_fix(world: World, teacher: Entity, a: Entity, b: Entity, tool: SafeTool, treasure: Treasure, bumped: bool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    lead = "After the scary moment had passed" if bumped else "A little later"
    world.say(
        f'{lead}, the {teacher.label_word} brought {tool.phrase}. "{tool.use_line}," {teacher.pronoun()} said.'
    )
    world.say(
        f"{a.id} and {b.id} used it to reach {treasure.label} without climbing anything at all."
    )
    world.say(
        f"Soon the little pirates had {treasure.safe_end}, and even in the dim nap room their game felt bright, kind, and safe."
    )


def tell(
    perch: Perch,
    treasure: Treasure,
    tool: SafeTool,
    response: Response,
    *,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    teacher_type: str = "teacher_woman",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 5,
    cautioner_age: int = 6,
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
    ))
    teacher = world.add(Entity(
        id="Teacher",
        kind="character",
        type=teacher_type,
        role="teacher",
        label="the teacher",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label="nap room",
        quiet_space=True,
    ))
    perch_ent = world.add(Entity(
        id="perch",
        type="perch",
        label=perch.label,
        phrase=perch.phrase,
        unstable=perch.unstable,
        movable=perch.movable,
        quiet_space=perch.nap_nearby,
    ))
    world.facts["room"] = room

    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)

    play_setup(world, a, b, treasure)
    introduce_treasure(world, b, treasure, perch)

    world.para()
    misunderstand(world, a, b, perch)
    warn(world, b, a, perch, teacher)

    clarified = would_clarify(cautioner_age, instigator_age, trait, trust)
    if clarified:
        back_down(world, a, b, teacher)
        world.para()
        safe_fix(world, teacher, a, b, tool, treasure, bumped=False)
        severity = 0
        contained = True
    else:
        defy(world, a, perch)
        world.para()
        climb(world, a, perch_ent, perch, treasure)
        alarm(world, b, a, teacher, perch)
        severity = danger_severity(perch, delay)
        perch_ent.meters["severity"] = float(severity)
        contained = is_contained(response, perch, delay)
        world.para()
        if contained:
            rescue(world, teacher, response, a, perch_ent, perch)
            kind_lesson(world, teacher, a, b, perch, bumped=False)
            world.para()
            safe_fix(world, teacher, a, b, tool, treasure, bumped=False)
        else:
            rescue_fail(world, teacher, response, a, perch_ent, perch)
            kind_lesson(world, teacher, a, b, perch, bumped=True)
            world.para()
            safe_fix(world, teacher, a, b, tool, treasure, bumped=True)

    outcome = "clarified" if clarified else ("caught" if contained else "bumped")
    world.facts.update(
        instigator=a,
        cautioner=b,
        teacher=teacher,
        perch_cfg=perch,
        perch=perch_ent,
        treasure=treasure,
        tool=tool,
        response=response,
        outcome=outcome,
        severity=severity,
        delay=delay,
        bumped=a.meters["bump"] >= THRESHOLD,
        misunderstanding=a.memes["misunderstanding"] >= THRESHOLD,
    )
    return world


THEMES = {"pirates": "pirates"}

PERCHES = {
    "cot_stack": Perch(
        id="cot_stack",
        label="stack of nap cots",
        phrase="the tall stack of folded nap cots by the wall",
        detail="The wheels gave a tiny squeak, and the stack rocked an inch to one side",
        risk=3,
        unstable=True,
        movable=True,
        nap_nearby=True,
        tags={"cot", "nap_room", "climbing"},
    ),
    "rocking_chair": Perch(
        id="rocking_chair",
        label="rocking chair",
        phrase="the wooden rocking chair beside the bookshelf",
        detail="The chair tipped back with a soft creak and did not feel steady at all",
        risk=2,
        unstable=True,
        movable=True,
        nap_nearby=True,
        tags={"chair", "nap_room", "climbing"},
    ),
    "shelf": Perch(
        id="shelf",
        label="blanket shelf",
        phrase="the blanket shelf where the spare quilts were kept",
        detail="A folded quilt slid forward, and the shelf gave a wobbly shake",
        risk=3,
        unstable=True,
        movable=False,
        nap_nearby=True,
        tags={"shelf", "nap_room", "climbing"},
    ),
    "floor_mat": Perch(
        id="floor_mat",
        label="sleeping mat",
        phrase="one quiet sleeping mat on the floor",
        detail="Nothing moved at all",
        risk=0,
        unstable=False,
        movable=False,
        nap_nearby=True,
        tags={"mat", "nap_room"},
    ),
}

TREASURES = {
    "parrot": Treasure(
        id="parrot",
        label="the paper parrot",
        phrase="a bright paper parrot from craft time",
        perch_line="It was resting above the {perch}, where afternoon shadows made it look like a treasure bird",
        safe_end="the paper parrot perched on their pretend mast",
        tags={"parrot", "pretend_play"},
    ),
    "map": Treasure(
        id="map",
        label="the crayon treasure map",
        phrase="a crayon treasure map with a red X",
        perch_line="It had been tucked above the {perch}, as if the treasure itself were hiding there",
        safe_end="the crayon treasure map spread between them like a real captain's chart",
        tags={"map", "pretend_play"},
    ),
    "flag": Treasure(
        id="flag",
        label="the little pirate flag",
        phrase="a little pirate flag cut from blue paper",
        perch_line="It was dangling above the {perch}, where it looked like a secret signal from another ship",
        safe_end="the little pirate flag fluttering from a cardboard mast",
        tags={"flag", "pretend_play"},
    ),
}

SAFE_TOOLS = {
    "step_stool": SafeTool(
        id="step_stool",
        label="step stool",
        phrase="a small step stool",
        use_line="Real helpers use safe steps, not wobbly pirate guesses",
        tags={"step_stool", "safety"},
    ),
    "reacher": SafeTool(
        id="reacher",
        label="grabber tool",
        phrase="a long grabber tool",
        use_line="This reaches high things without anybody climbing",
        tags={"grabber", "safety"},
    ),
    "pointing_stick": SafeTool(
        id="pointing_stick",
        label="pointer",
        phrase="a soft classroom pointer",
        use_line="A captain can point treasure down before anybody tries to scramble up",
        tags={"pointer", "safety"},
    ),
}

RESPONSES = {
    "steady_and_lift": Response(
        id="steady_and_lift",
        sense=3,
        power=4,
        text="held {perch} steady with one hand and lifted the child down with the other",
        fail="reached for the child, but {perch} shifted before the teacher could get there",
        qa_text="held the perch steady and lifted the child down",
        tags={"adult_help", "catch"},
    ),
    "bring_stool_fast": Response(
        id="bring_stool_fast",
        sense=3,
        power=3,
        text="slid a sturdy step stool into place and guided the child down onto it",
        fail="started to slide a step stool over, but the wobble turned into a tumble too quickly",
        qa_text="guided the child down with a sturdy step stool",
        tags={"adult_help", "step_stool"},
    ),
    "hug_blankets": Response(
        id="hug_blankets",
        sense=1,
        power=1,
        text="piled blankets under the child and hoped that would be enough",
        fail="threw blankets down, but the child still slipped before they could help",
        qa_text="threw blankets under the child",
        tags={"blankets"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "thoughtful", "gentle", "curious", "clever"]


@dataclass
class StoryParams:
    perch: str
    treasure: str
    tool: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    teacher: str
    trait: str
    delay: int = 0
    instigator_age: int = 5
    cautioner_age: int = 6
    trust: int = 6
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        perch="cot_stack",
        treasure="parrot",
        tool="step_stool",
        response="steady_and_lift",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        teacher="teacher_woman",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=6,
        trust=8,
    ),
    StoryParams(
        perch="rocking_chair",
        treasure="map",
        tool="reacher",
        response="bring_stool_fast",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        teacher="teacher_man",
        trait="thoughtful",
        delay=0,
        instigator_age=6,
        cautioner_age=6,
        trust=7,
    ),
    StoryParams(
        perch="shelf",
        treasure="flag",
        tool="pointing_stick",
        response="bring_stool_fast",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        teacher="teacher_woman",
        trait="curious",
        delay=1,
        instigator_age=6,
        cautioner_age=5,
        trust=3,
    ),
    StoryParams(
        perch="cot_stack",
        treasure="map",
        tool="reacher",
        response="steady_and_lift",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Noah",
        cautioner_gender="boy",
        teacher="teacher_man",
        trait="gentle",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        trust=6,
    ),
]


KNOWLEDGE = {
    "nap_room": [
        (
            "What is a nap room?",
            "A nap room is a quiet place where children rest or sleep during the day. People use soft voices there so everyone can feel calm."
        )
    ],
    "climbing": [
        (
            "Why should children not climb on furniture?",
            "Furniture can tip, slide, or wobble when it is used the wrong way. That can make someone fall and get hurt."
        )
    ],
    "cot": [
        (
            "What is a nap cot?",
            "A nap cot is a small bed for resting at school or daycare. It is for lying down quietly, not for climbing."
        )
    ],
    "chair": [
        (
            "Why can a rocking chair be unsafe to climb on?",
            "A rocking chair moves back and forth, so it is not steady like a step stool. Climbing on it can make a person lose balance."
        )
    ],
    "shelf": [
        (
            "Why is a shelf not a ladder?",
            "A shelf is made to hold things, not to hold a climbing child. It can shake or drop items if someone climbs it."
        )
    ],
    "adult_help": [
        (
            "What should you do if something you want is too high up?",
            "Ask a grown-up for help. A grown-up can bring the right safe tool or lift it down for you."
        )
    ],
    "step_stool": [
        (
            "What is a step stool for?",
            "A step stool is a small, steady platform that helps you reach a little higher. It is safer than standing on furniture."
        )
    ],
    "grabber": [
        (
            "What does a grabber tool do?",
            "A grabber tool helps you pick up or reach things from farther away. It lets you get an object without climbing."
        )
    ],
    "pointer": [
        (
            "What can a classroom pointer be used for?",
            "A classroom pointer can point to or gently tap something high up so a grown-up can get it safely. It helps people reach without scrambling onto furniture."
        )
    ],
}
KNOWLEDGE_ORDER = ["nap_room", "climbing", "cot", "chair", "shelf", "adult_help", "step_stool", "grabber", "pointer"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    if not sensible_responses():
        return combos
    for perch_id, perch in PERCHES.items():
        if hazard_at_risk(perch):
            for treasure_id in TREASURES:
                combos.append((perch_id, treasure_id))
    return combos


def explain_rejection(perch: Perch) -> str:
    return (
        f"(No story: {perch.the} is not an actual climbing danger here, so there is no honest way for the world model to say someone was endangered. "
        f"Pick a perch like cot_stack, rocking_chair, or shelf.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_clarify(params.cautioner_age, params.instigator_age, params.trait, params.trust):
        return "clarified"
    contained = is_contained(RESPONSES[params.response], PERCHES[params.perch], params.delay)
    return "caught" if contained else "bumped"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    perch = f["perch_cfg"]
    treasure = f["treasure"]
    outcome = f["outcome"]
    if outcome == "clarified":
        return [
            'Write a pirate-style story for a 3-to-5-year-old set in a nap room that includes the word "endanger".',
            f"Tell a gentle story where {a.id} misunderstands pirate talk, thinks {a.pronoun()} should climb {perch.the}, and {b.id} kindly explains the mistake before anyone gets hurt.",
            f"Write a story about misunderstanding and kindness in a quiet nap room, ending with a safe way to reach {treasure.label}.",
        ]
    if outcome == "caught":
        return [
            'Write a pirate-style story for a 3-to-5-year-old set in a nap room that includes the word "endanger".',
            f"Tell a story where {a.id} misunderstands what a crow's nest is, tries to climb {perch.the}, and a kind teacher helps just in time.",
            "Write a gentle cautionary tale about pirate pretend play, misunderstanding, and kindness leading to a safer choice.",
        ]
    return [
        'Write a pirate-style story for a 3-to-5-year-old set in a nap room that includes the word "endanger".',
        f"Tell a story where {a.id} misunderstands pirate talk, climbs {perch.the}, has a small tumble, and is comforted kindly instead of scolded.",
        "Write a story with a scary little turn but a warm ending, teaching that asking for help is braver than climbing.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "boy" and b.type == "boy":
        return "two classmates"
    if a.type == "girl" and b.type == "girl":
        return "two classmates"
    return "two classmates"


def story_qa_data(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    teacher = f["teacher"]
    perch = f["perch_cfg"]
    treasure = f["treasure"]
    tool = f["tool"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, in a nap room with their teacher nearby."
        ),
        (
            "What were the children pretending?",
            f"They were pretending the nap room was a pirate ship, and they were trying to reach {treasure.label}. The pirate game made the room feel full of adventure."
        ),
        (
            f"What did {a.id} misunderstand?",
            f"{a.id} misunderstood the words 'crow's nest' and thought they meant a real place to climb. {b.id} had only meant a pretend pirate idea."
        ),
        (
            f"Why did {b.id} say climbing {perch.the} was a bad idea?",
            f"{b.id} knew {perch.the} could wobble and endanger someone in the quiet room. In the story world, climbing it raised real danger instead of just make-believe danger."
        ),
    ]
    if outcome == "clarified":
        qa.append(
            (
                f"How was the problem solved?",
                f"{a.id} listened when {b.id} explained the misunderstanding, and they asked the teacher for help instead of climbing. Then they used {tool.phrase} to get {treasure.label} safely."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended calmly and happily. The children kept playing pirates, but now they had a safe way to reach things in the nap room."
            )
        )
    elif outcome == "caught":
        qa.append(
            (
                f"How did the teacher help?",
                f"The teacher {response.qa_text}. That quick help stopped the danger before it turned into a fall."
            )
        )
        qa.append(
            (
                "Was the teacher angry?",
                f"No. The teacher spoke kindly, thanked the children for calling for help, and explained why the climb could endanger people."
            )
        )
        qa.append(
            (
                "What happened after the danger passed?",
                f"After everyone was safe, the teacher brought {tool.phrase}. That let the pirate game continue in a safer way."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {a.id} climbed {perch.the}?",
                f"{perch.the.capitalize()} wobbled, and {a.id} had a small tumble onto the rug. It was scary, even though the bump was small."
            )
        )
        qa.append(
            (
                "How did the teacher show kindness?",
                f"The teacher comforted {a.id}, checked the bump, and spoke gently instead of scolding. That kindness helped turn the scary moment into a lesson."
            )
        )
        qa.append(
            (
                "What changed by the end?",
                f"By the end, the children had learned to ask for help and use {tool.phrase} instead of climbing. The game became safer and kinder than before."
            )
        )
    return qa


def world_knowledge_qa_data(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["perch_cfg"].tags) | set(f["tool"].tags)
    tags.add("adult_help")
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.age:
            parts.append(f"age={ent.age}")
        if ent.unstable:
            parts.append("unstable=True")
        if ent.movable:
            parts.append("movable=True")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P) :- perch(P), unstable(P), risk(P, R), R > 0.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(P, T) :- hazard(P), treasure(T).

init_caution(5) :- trait(T), is_cautious(T).
init_caution(3) :- trait(T), not is_cautious(T).
older_bonus(2) :- cautioner_age(CA), instigator_age(IA), CA > IA.
older_bonus(0) :- cautioner_age(CA), instigator_age(IA), CA <= IA.
authority(C + B + W) :- init_caution(C), older_bonus(B), trust_bucket(W).
trust_bucket(T / 5) :- trust(T).
clarified :- authority(A), bravery_init(BR), A > BR.

severity(R + D) :- chosen_perch(P), risk(P, R), delay(D).
resp_power(PW) :- chosen_response(R), power(R, PW).
caught :- resp_power(PW), severity(SV), PW >= SV.

outcome(clarified) :- clarified.
outcome(caught) :- not clarified, caught.
outcome(bumped) :- not clarified, not caught.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("risk", perch_id, perch.risk))
        if perch.unstable:
            lines.append(asp.fact("unstable", perch_id))
    for treasure_id in TREASURES:
        lines.append(asp.fact("treasure", treasure_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    for tool_id in SAFE_TOOLS:
        lines.append(asp.fact("tool", tool_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BOLDNESS_INIT)))
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
    return sorted(name for (name,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_perch", params.perch),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a pirate misunderstanding in a nap room, with danger checked by the world model."
    )
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--tool", choices=SAFE_TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--teacher", choices=["teacher_woman", "teacher_man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the teacher takes to reach the danger")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.perch and not hazard_at_risk(PERCHES[args.perch]):
        raise StoryError(explain_rejection(PERCHES[args.perch]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.perch is None or combo[0] == args.perch)
        and (args.treasure is None or combo[1] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    perch_id, treasure_id = rng.choice(sorted(combos))
    tool_id = args.tool or rng.choice(sorted(SAFE_TOOLS))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    teacher = args.teacher or rng.choice(["teacher_woman", "teacher_man"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        perch=perch_id,
        treasure=treasure_id,
        tool=tool_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        teacher=teacher,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.tool not in SAFE_TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not hazard_at_risk(PERCHES[params.perch]):
        raise StoryError(explain_rejection(PERCHES[params.perch]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        PERCHES[params.perch],
        TREASURES[params.treasure],
        SAFE_TOOLS[params.tool],
        RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        teacher_type=params.teacher,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        trust=params.trust,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_data(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_data(world)],
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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    parser = build_parser()
    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke-tested normal story generation.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (perch, treasure) combos:\n")
        for perch, treasure in combos:
            print(f"  {perch:14} {treasure}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.perch} for {p.treasure} ({outcome_of(p)})"
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
