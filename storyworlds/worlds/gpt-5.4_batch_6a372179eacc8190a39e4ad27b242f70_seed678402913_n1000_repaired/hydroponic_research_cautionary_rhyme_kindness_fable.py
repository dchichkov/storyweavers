#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hydroponic_research_cautionary_rhyme_kindness_fable.py
=================================================================================

A standalone storyworld about a small hydroponic research club in a greenhouse.

This tiny domain models a cautionary fable: a young helper wants to rush a
hydroponic experiment by adding too much feed, a kinder and more careful friend
warns that living plants need measured care, and a calm mentor helps fix the
trouble or prevent it. The prose is child-facing and lightly rhymed, with an
ending image that proves the lesson changed the world.

Run it
------
    python storyworlds/worlds/gpt-5.4/hydroponic_research_cautionary_rhyme_kindness_fable.py
    python storyworlds/worlds/gpt-5.4/hydroponic_research_cautionary_rhyme_kindness_fable.py --crop basil
    python storyworlds/worlds/gpt-5.4/hydroponic_research_cautionary_rhyme_kindness_fable.py --crop plastic_vine
    python storyworlds/worlds/gpt-5.4/hydroponic_research_cautionary_rhyme_kindness_fable.py --all --qa
    python storyworlds/worlds/gpt-5.4/hydroponic_research_cautionary_rhyme_kindness_fable.py --verify
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
IMPULSE_INIT = 6.0
PATIENT_TRAITS = {"patient", "careful", "gentle", "steady"}


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
    living: bool = False
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "goose", "doe"}
        male = {"boy", "buck", "fox", "frog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "tortoise": "tortoise teacher",
            "heron": "heron teacher",
            "beaver": "beaver teacher",
        }.get(self.type, self.type)


@dataclass
class Lab:
    id: str
    place: str
    image: str
    shelves: str
    sendoff: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shortcut:
    id: str
    cry: str
    label: str
    where: str
    act: str
    line: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Crop:
    id: str
    label: str
    phrase: str
    leaves: str
    sensitivity: int
    living: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"


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
class SafeTool:
    id: str
    phrase: str
    glow: str
    use: str
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


def _r_salt_stress(world: World) -> list[str]:
    out: list[str] = []
    crop = world.entities.get("crop")
    basin = world.entities.get("basin")
    if crop is None or basin is None:
        return out
    if crop.meters["overfed"] < THRESHOLD:
        return out
    sig = ("salt_stress", crop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    basin.meters["saltiness"] += 1
    crop.meters["stress"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__stress__")
    return out


def _r_wilt(world: World) -> list[str]:
    out: list[str] = []
    crop = world.entities.get("crop")
    if crop is None or crop.meters["stress"] < THRESHOLD:
        return out
    sig = ("wilt", crop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crop.meters["wilt"] += 1
    out.append("__wilt__")
    return out


CAUSAL_RULES = [
    Rule(name="salt_stress", tag="physical", apply=_r_salt_stress),
    Rule(name="wilt", tag="physical", apply=_r_wilt),
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


def hazard_at_risk(shortcut: Shortcut, crop: Crop) -> bool:
    return crop.living


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def plant_severity(crop: Crop, delay: int) -> int:
    return crop.sensitivity + delay


def is_recovered(response: Response, crop: Crop, delay: int) -> bool:
    return response.power >= plant_severity(crop, delay)


def initial_patience(trait: str) -> float:
    return 5.0 if trait in PATIENT_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_partner = relation == "partners" and cautioner_age > instigator_age
    authority = (initial_patience(trait) + 1.0) + (4.0 if older_partner else 0.0)
    return older_partner and authority > IMPULSE_INIT


def predict_stress(world: World) -> dict:
    sim = world.copy()
    crop = sim.get("crop")
    crop.meters["overfed"] += 1
    propagate(sim, narrate=False)
    return {
        "stressed": crop.meters["stress"] >= THRESHOLD,
        "wilted": crop.meters["wilt"] >= THRESHOLD,
        "saltiness": sim.get("basin").meters["saltiness"],
    }


def introduce(world: World, lab: Lab, a: Entity, b: Entity, crop: Crop) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"In {lab.place}, {lab.image}. {lab.shelves}"
    )
    world.say(
        f"{a.id} and {b.id} were doing hydroponic research with {crop.phrase}. "
        f"They liked to whisper, \"Measure with care, and green things fare.\""
    )


def need_waiting(world: World, a: Entity, b: Entity, crop: Crop) -> None:
    world.say(
        f"But waiting is a slow little art, and {crop.the} had only tiny roots and {crop.leaves}. "
        f"The tray looked so still that {a.id} wanted to make the growing hurry."
    )
    world.say(
        f"{b.id} watched the roots in the clear water and listened for the soft pump's hum."
    )


def tempt(world: World, a: Entity, shortcut: Shortcut) -> None:
    a.memes["impulse"] += 1
    world.say(
        f'"{shortcut.cry}" said {a.id}. "{shortcut.line}"'
    )
    world.say(
        f"{a.id} reached toward {shortcut.where}, thinking a quick extra splash would be a clever dash."
    )


def warn(world: World, b: Entity, a: Entity, shortcut: Shortcut, crop: Crop, mentor: Entity) -> None:
    pred = predict_stress(world)
    b.memes["caution"] += 1
    world.facts["predicted_wilt"] = pred["wilted"]
    world.facts["predicted_saltiness"] = pred["saltiness"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} spoke very softly, because kind warnings land better than sharp ones."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, please do not {shortcut.act}. '
        f'Living roots are not racing toys. If we pour too much, {crop.the} may droop before {mentor.label_word} even comes to see our notes."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, shortcut: Shortcut, mentor: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["impulse"] = 0.0
    world.say(
        f'{a.id} looked at the shining bottle, then at {b.id}. '
        f'"Slow is not low," {a.pronoun()} murmured. "{shortcut.label} can wait."'
    )
    world.say(
        f"They left the bottle closed and went to fetch {mentor.label_word}, choosing patience before panic."
    )


def defy(world: World, a: Entity, b: Entity, shortcut: Shortcut) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"Just a little more will help it soar," {a.id} said, and before {b.id} could stop {a.pronoun("object")}, '
        f"{a.pronoun()} {shortcut.act}."
    )


def overfeed(world: World, crop_ent: Entity, crop: Crop, shortcut: Shortcut) -> None:
    crop_ent.meters["overfed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"For one blink the tray still shone. Then the water turned too rich, the roots took a sting, "
        f"and {crop.the} bent its {crop.leaves} as if the morning had gone wrong."
    )
    world.say(
        f"It was a small mistake, but small mistakes can make a tender plant ache."
    )


def alarm(world: World, b: Entity, crop: Crop, mentor: Entity) -> None:
    world.say(
        f'"Oh no, {crop.the} is drooping!" cried {b.id}. "{mentor.label_word.capitalize()}, please come quick!"'
    )


def rescue(world: World, mentor: Entity, response: Response, crop_ent: Entity, crop: Crop) -> None:
    crop_ent.meters["stress"] = 0.0
    crop_ent.meters["wilt"] = 0.0
    world.get("basin").meters["saltiness"] = 0.0
    world.say(
        f"{mentor.label_word.capitalize()} came without stomping or scolding and {response.text.replace('{crop}', crop.label)}."
    )
    world.say(
        f'Soon the leaves were no longer sagging, and the room felt easier to breathe in. '
        f'"Kind hands mend what hurried hands bend," {mentor.pronoun()} said.'
    )


def rescue_fail(world: World, mentor: Entity, response: Response, crop_ent: Entity, crop: Crop) -> None:
    crop_ent.meters["stress"] += 1
    crop_ent.meters["wilt"] += 1
    world.get("basin").meters["saltiness"] += 1
    world.say(
        f"{mentor.label_word.capitalize()} hurried over and {response.fail.replace('{crop}', crop.label)}."
    )
    world.say(
        f"But the roots had drunk too much, too fast. {crop.the.capitalize()} drooped lower, and even the pump sounded sad."
    )


def lesson(world: World, mentor: Entity, a: Entity, b: Entity, shortcut: Shortcut, crop: Crop) -> None:
    for kid in (a, b):
        kid.memes["kindness"] += 1
        kid.memes["lesson"] += 1
        kid.memes["worry"] = 0.0
    a.memes["guilt"] += 1
    world.say(
        f"{mentor.label_word.capitalize()} knelt beside them and touched neither ear nor wing in anger, only the notebook on the table."
    )
    world.say(
        f'"Research means watching kindly and writing truly," {mentor.pronoun()} said. '
        f'"{shortcut.lesson}. We do not rush a root just because we wish for fruit."'
    )
    world.say(
        f'{a.id} bowed {a.pronoun("possessive")} head. "{crop.The if hasattr(crop, "The") else crop.label.capitalize()} needed care, and I was not fair," {a.pronoun()} said.'
    )


def sad_lesson(world: World, mentor: Entity, a: Entity, b: Entity, shortcut: Shortcut, crop: Crop) -> None:
    for kid in (a, b):
        kid.memes["kindness"] += 1
        kid.memes["lesson"] += 1
    a.memes["guilt"] += 1
    world.say(
        f"{mentor.label_word.capitalize()} gathered them close beside the quiet tray."
    )
    world.say(
        f'"Little roots cannot speak, so careful hearts must speak for them," {mentor.pronoun()} said. '
        f'"{shortcut.lesson}, and once tenderness is lost, it cannot be poured back in a jug."'
    )
    world.say(
        f"{a.id} promised to remember that living things are helped by patience, not by hurry."
    )


def safe_tools(world: World, mentor: Entity, a: Entity, b: Entity, lab: Lab, t1: SafeTool, t2: SafeTool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next day, {mentor.label_word} set out {t1.phrase} and {t2.phrase}. {t1.glow} {t2.glow}"
    )
    world.say(
        f'"If you want to help the seedlings, {t1.use}, and {t2.use}," {mentor.pronoun()} said. '
        f'"That is how a kind lab stays bright."'
    )
    world.say(
        f"{a.id} measured while {b.id} wrote, and together they watched tiny green tips lift again. {lab.sendoff}"
    )


def tell(
    lab: Lab,
    shortcut: Shortcut,
    crop: Crop,
    tools: tuple[SafeTool, SafeTool],
    response: Response,
    *,
    instigator: str = "Pip",
    instigator_type: str = "fox",
    cautioner: str = "Mira",
    cautioner_type: str = "hen",
    caution_trait: str = "patient",
    mentor_type: str = "tortoise",
    delay: int = 0,
    instigator_age: int = 5,
    cautioner_age: int = 7,
    relation: str = "partners",
    trust: int = 5,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_type,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
        traits=["quick"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_type,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation},
        traits=[caution_trait],
    ))
    mentor = world.add(Entity(
        id="Mentor",
        kind="character",
        type=mentor_type,
        role="mentor",
        label="the mentor",
    ))
    crop_ent = world.add(Entity(
        id="crop",
        type="crop",
        label=crop.label,
        phrase=crop.phrase,
        living=crop.living,
        tags=set(crop.tags),
    ))
    world.add(Entity(id="basin", type="basin", label="the basin"))
    world.add(Entity(id="bottle", type="tool", label=shortcut.label))

    a.memes["impulse"] = IMPULSE_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_patience(caution_trait)

    introduce(world, lab, a, b, crop)
    need_waiting(world, a, b, crop)

    world.para()
    tempt(world, a, shortcut)
    warn(world, b, a, shortcut, crop, mentor)

    averted = would_avert(relation, instigator_age, cautioner_age, caution_trait)
    if averted:
        back_down(world, a, b, shortcut, mentor)
        world.para()
        safe_tools(world, mentor, a, b, lab, tools[0], tools[1])
        severity = 0
        recovered = True
    else:
        defy(world, a, b, shortcut)
        world.para()
        overfeed(world, crop_ent, crop, shortcut)
        alarm(world, b, crop, mentor)
        severity = plant_severity(crop, delay)
        crop_ent.meters["severity"] = float(severity)
        recovered = is_recovered(response, crop, delay)
        world.para()
        if recovered:
            rescue(world, mentor, response, crop_ent, crop)
            lesson(world, mentor, a, b, shortcut, crop)
            world.para()
            safe_tools(world, mentor, a, b, lab, tools[0], tools[1])
        else:
            rescue_fail(world, mentor, response, crop_ent, crop)
            sad_lesson(world, mentor, a, b, shortcut, crop)

    outcome = "averted" if averted else ("recovered" if recovered else "wilted")
    world.facts.update(
        lab=lab,
        shortcut=shortcut,
        crop_cfg=crop,
        crop=crop_ent,
        response=response,
        tools=tools,
        instigator=a,
        cautioner=b,
        mentor=mentor,
        relation=relation,
        outcome=outcome,
        severity=severity,
        delay=delay,
        trust=trust,
        overfed=crop_ent.meters["overfed"] >= THRESHOLD,
        promise=a.memes["lesson"] >= THRESHOLD if "lesson" in a.memes else False,
    )
    return world


THEMES = {
    "school_greenhouse": Lab(
        id="school_greenhouse",
        place="the school greenhouse",
        image="glass panes held the morning sun like warm, clear honey",
        shelves="Blue pipes hummed along the wall, and neat rows of jars gleamed above a bubbling tank.",
        sendoff="Under the glass roof, notes grew straighter and the seedlings stood lighter.",
        tags={"greenhouse", "research"},
    ),
    "library_sunroom": Lab(
        id="library_sunroom",
        place="the library sunroom",
        image="the windows made bright squares on the floor",
        shelves="A little hydroponic shelf purred in the corner, full of labels, tubes, and careful charts.",
        sendoff="By the tall windows, their chart grew longer and the little raft grew stronger.",
        tags={"library", "research"},
    ),
    "rooftop_shed": Lab(
        id="rooftop_shed",
        place="the rooftop shed",
        image="the city wind tapped the glass and then blew by",
        shelves="Inside, a silver pump sang softly under trays of roots and leaves.",
        sendoff="Above the roofs, they wrote true things and watched green stems make tiny springs.",
        tags={"rooftop", "research"},
    ),
}

SHORTCUTS = {
    "extra_scoop": Shortcut(
        id="extra_scoop",
        cry="I know a trick",
        label="plant food",
        where="the spoon beside the nutrient jar",
        act="tipped in an extra scoop of plant food",
        line="One extra scoop will make the basil loop and the lettuce shoot!",
        lesson="measuring first is kinder than guessing",
        tags={"measurement", "hydroponic"},
    ),
    "mystery_capful": Shortcut(
        id="mystery_capful",
        cry="Let us try this",
        label="feed bottle",
        where="the bright bottle near the basin",
        act="poured a capful from the feed bottle without measuring",
        line="A shiny capful will make the roots more dutiful!",
        lesson="labels and measures matter in a lab",
        tags={"measurement", "hydroponic"},
    ),
    "turn_dial": Shortcut(
        id="turn_dial",
        cry="Maybe this",
        label="nutrient dial",
        where="the little nutrient dial on the pump",
        act="twisted the nutrient dial higher than the mark",
        line="If the number is bigger, the leaves will wake up quicker!",
        lesson="more is not always better for a tender living thing",
        tags={"pump", "hydroponic"},
    ),
}

CROPS = {
    "lettuce": Crop(
        id="lettuce",
        label="lettuce",
        phrase="a floating tray of baby lettuce",
        leaves="round green leaves",
        sensitivity=1,
        living=True,
        tags={"lettuce", "plant"},
    ),
    "basil": Crop(
        id="basil",
        label="basil",
        phrase="a raft of sweet basil seedlings",
        leaves="small fragrant leaves",
        sensitivity=2,
        living=True,
        tags={"basil", "plant"},
    ),
    "strawberry": Crop(
        id="strawberry",
        label="strawberry starts",
        phrase="a line of young strawberry starts",
        leaves="tiny bright crowns",
        sensitivity=2,
        living=True,
        tags={"strawberry", "plant"},
    ),
    "plastic_vine": Crop(
        id="plastic_vine",
        label="plastic vine",
        phrase="a plastic vine on a dusty shelf",
        leaves="fake green leaves",
        sensitivity=0,
        living=False,
        tags={"plastic"},
    ),
}

RESPONSES = {
    "flush_refill": Response(
        id="flush_refill",
        sense=3,
        power=4,
        text="drained the basin, rinsed the roots with clean water, and mixed a fresh gentle solution for the {crop}",
        fail="drained the basin and mixed fresh water for the {crop}, but the roots had already taken too much shock",
        qa_text="drained the basin, rinsed the roots, and refilled it with a gentler mix",
        tags={"flush", "water", "repair"},
    ),
    "dilute_slowly": Response(
        id="dilute_slowly",
        sense=2,
        power=2,
        text="added clean water a little at a time, tested the basin, and lowered the strength until the {crop} could rest",
        fail="diluted the basin little by little, but the {crop} had already wilted too far to bounce back that day",
        qa_text="diluted the basin slowly and tested the water until it was gentler",
        tags={"dilute", "water", "repair"},
    ),
    "wait_and_hope": Response(
        id="wait_and_hope",
        sense=1,
        power=1,
        text="waited and hoped the {crop} would feel better on its own",
        fail="waited and hoped, but hope alone could not pull the extra feed back out of the roots",
        qa_text="waited and hoped",
        tags={"hope"},
    ),
}

SAFE_TOOLS = {
    "measuring_spoons": SafeTool(
        id="measuring_spoons",
        phrase="a ring of little measuring spoons",
        glow="They clicked together like tiny bells.",
        use="count each spoon before you pour",
        tags={"measurement", "spoon"},
    ),
    "research_log": SafeTool(
        id="research_log",
        phrase="a square research log with ruled pages",
        glow="Its pages waited for honest numbers.",
        use="write what you see before you change what you see",
        tags={"research", "logbook"},
    ),
    "test_strips": SafeTool(
        id="test_strips",
        phrase="a packet of test strips",
        glow="The colored tips shone like little flags.",
        use="test the water before you touch the pump",
        tags={"testing", "water"},
    ),
    "dropper": SafeTool(
        id="dropper",
        phrase="a clear little dropper",
        glow="It caught the light like a bead of rain.",
        use="add only one tiny drop when the notes say one tiny drop",
        tags={"dropper", "measurement"},
    ),
}

NAME_TYPES = [
    ("Pip", "fox"),
    ("Mira", "hen"),
    ("Tad", "frog"),
    ("Nell", "goose"),
    ("Bram", "buck"),
    ("Wren", "hen"),
    ("Moss", "fox"),
    ("Lark", "goose"),
]

CAUTION_TRAITS = ["patient", "careful", "gentle", "steady", "thoughtful", "quiet"]


@dataclass
class StoryParams:
    lab: str
    shortcut: str
    crop: str
    tool1: str
    tool2: str
    response: str
    instigator: str
    instigator_type: str
    cautioner: str
    cautioner_type: str
    mentor: str
    caution_trait: str
    delay: int = 0
    instigator_age: int = 5
    cautioner_age: int = 7
    relation: str = "partners"
    trust: int = 5
    seed: Optional[int] = None


KNOWLEDGE = {
    "hydroponic": [(
        "What does hydroponic mean?",
        "Hydroponic means plants are grown in water with nutrients instead of in soil. The roots still need careful light, air, and food."
    )],
    "research": [(
        "What is research?",
        "Research is careful learning. You watch closely, write true notes, and test one change at a time so you can understand what happened."
    )],
    "measurement": [(
        "Why is measuring important in a plant experiment?",
        "Measuring helps you give the same amount each time instead of guessing. That keeps the test fair and protects the plants from too much or too little."
    )],
    "flush": [(
        "How can a grown-up help if a hydroponic plant gets too much feed?",
        "A careful grown-up can remove the strong water and replace it with a gentler mix. That gives the roots a better chance to rest."
    )],
    "dilute": [(
        "What does it mean to dilute water?",
        "To dilute water means to make a strong mixture weaker by adding more plain water. In a plant system, that can make the water gentler for roots."
    )],
    "logbook": [(
        "Why do scientists keep a logbook?",
        "A logbook helps them remember what they saw and what they changed. Honest notes stop people from guessing later."
    )],
    "testing": [(
        "What are test strips for?",
        "Test strips help you check what is in water. They give a clue before you add more of something."
    )],
    "kindness": [(
        "How can you be kind to a plant?",
        "You can be kind to a plant by handling it gently, giving it the right amount of water and food, and not rushing just because you feel impatient."
    )],
}

KNOWLEDGE_ORDER = ["hydroponic", "research", "measurement", "flush", "dilute", "logbook", "testing", "kindness"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for lab_id in THEMES:
        for shortcut_id, shortcut in SHORTCUTS.items():
            for crop_id, crop in CROPS.items():
                if hazard_at_risk(shortcut, crop):
                    combos.append((lab_id, shortcut_id, crop_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    lab = f["lab"]
    crop = f["crop_cfg"]
    shortcut = f["shortcut"]
    tools = f["tools"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a gentle rhyming fable for ages 3 to 5 set in {lab.place} that includes the words "hydroponic" and "research".',
            f"Tell a cautionary kindness story where {a.id} wants to {shortcut.act}, but {b.id} warns {a.pronoun('object')} in a soft way and no harm is done.",
            f"Write a small fable where two young helpers choose measuring and note-taking instead of rushing, and end with {tools[0].phrase} and {tools[1].phrase}.",
        ]
    if outcome == "wilted":
        return [
            f'Write a cautionary rhyming fable that includes "hydroponic" and "research" and shows that hurrying can hurt a living plant.',
            f"Tell a story where {a.id} ignores a kind warning, overfeeds {crop.the}, and learns that patience is part of kindness.",
            "Write a fable with a sad but gentle lesson: a mistake cannot be undone at once, so careful measuring matters.",
        ]
    return [
        f'Write a kind cautionary fable with a light rhyme, using the words "hydroponic" and "research".',
        f"Tell a story where {a.id} rushes a plant experiment, {b.id} warns kindly, and a calm mentor helps fix the problem.",
        f"Write a child-facing story that ends with safe tools, careful notes, and a changed heart in the greenhouse.",
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "partners":
        return "two young research partners"
    return "two young helpers"


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    mentor = f["mentor"]
    crop = f["crop_cfg"]
    shortcut = f["shortcut"]
    response = f["response"]
    tools = f["tools"]
    relation = f["relation"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, relation)}, {a.id} and {b.id}, and their {mentor.label_word}. They were working with {crop.phrase} in a little lab."
        ),
        (
            "What were they doing?",
            f"They were doing hydroponic research, which means they were caring for plants growing in water instead of soil. Their work needed patient watching and true notes."
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} warned {a.id} because {shortcut.act} could make the water too strong for {crop.the}. The warning came from kindness, since the roots were living and tender."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What happened after {b.id} spoke?",
            f"{a.id} stopped and left the bottle or dial alone, so the plants were never harmed. The turn in the story is that a soft warning worked before any damage began."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with {tools[0].phrase} and {tools[1].phrase} on the table while the two partners measured and wrote. The ending image shows they had changed from hurry to care."
        ))
    elif outcome == "recovered":
        body = response.qa_text.replace("{crop}", crop.label)
        qa.append((
            f"What happened when {a.id} rushed the experiment?",
            f"{crop.the.capitalize()} drooped because the water became too rich after {a.id} {shortcut.act.split(' ', 1)[0] if ' ' in shortcut.act else shortcut.act}. The roots were stressed by too much feed all at once."
        ))
        qa.append((
            f"How did {mentor.label_word} help?",
            f"{mentor.label_word.capitalize()} {body}. That worked because a gentler basin gave the roots a chance to rest instead of drinking more strong feed."
        ))
        qa.append((
            "What lesson did the children learn?",
            f"They learned that research should be honest and kind, not hurried. Measuring first protected the plant, and kindness meant thinking about what the roots could bear."
        ))
    else:
        qa.append((
            f"Could {mentor.label_word} save the plant right away?",
            f"No. {mentor.label_word.capitalize()} tried, but the roots had already taken too much shock, so {crop.the} drooped badly. The sad turn teaches that some rushed mistakes cannot be quickly undone."
        ))
        qa.append((
            "What was the lesson at the end?",
            f"The lesson was that living things need patience, and kindness means not forcing them for faster results. Research is careful because guessing can hurt what cannot speak."
        ))
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"hydroponic", "research", "kindness", "measurement"}
    response = f.get("response")
    if response is not None:
        tags |= set(response.tags)
    for tool in f.get("tools", ()):
        if tool.id == "research_log":
            tags.add("logbook")
        if tool.id == "test_strips":
            tags.add("testing")
        if "measurement" in tool.tags:
            tags.add("measurement")
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.living:
            bits.append("living=True")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        lab="school_greenhouse",
        shortcut="extra_scoop",
        crop="lettuce",
        tool1="measuring_spoons",
        tool2="research_log",
        response="flush_refill",
        instigator="Pip",
        instigator_type="fox",
        cautioner="Mira",
        cautioner_type="hen",
        mentor="tortoise",
        caution_trait="patient",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="partners",
        trust=5,
    ),
    StoryParams(
        lab="library_sunroom",
        shortcut="mystery_capful",
        crop="basil",
        tool1="test_strips",
        tool2="research_log",
        response="dilute_slowly",
        instigator="Tad",
        instigator_type="frog",
        cautioner="Nell",
        cautioner_type="goose",
        mentor="heron",
        caution_trait="gentle",
        delay=0,
        instigator_age=6,
        cautioner_age=6,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        lab="rooftop_shed",
        shortcut="turn_dial",
        crop="strawberry",
        tool1="measuring_spoons",
        tool2="dropper",
        response="dilute_slowly",
        instigator="Bram",
        instigator_type="buck",
        cautioner="Wren",
        cautioner_type="hen",
        mentor="beaver",
        caution_trait="steady",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="partners",
        trust=3,
    ),
    StoryParams(
        lab="school_greenhouse",
        shortcut="turn_dial",
        crop="basil",
        tool1="test_strips",
        tool2="research_log",
        response="flush_refill",
        instigator="Moss",
        instigator_type="fox",
        cautioner="Lark",
        cautioner_type="goose",
        mentor="tortoise",
        caution_trait="careful",
        delay=0,
        instigator_age=4,
        cautioner_age=7,
        relation="partners",
        trust=6,
    ),
]


def explain_rejection(shortcut: Shortcut, crop: Crop) -> str:
    if not crop.living:
        return (
            f"(No story: {shortcut.label} cannot hurt {crop.the} because it is not a living hydroponic crop. "
            f"Pick a real plant like lettuce, basil, or strawberry starts.)"
        )
    return "(No story: this combination has no living plant at risk.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.caution_trait):
        return "averted"
    recovered = is_recovered(RESPONSES[params.response], CROPS[params.crop], params.delay)
    return "recovered" if recovered else "wilted"


ASP_RULES = r"""
hazard(S, C) :- shortcut(S), living(C).
sensible(R)  :- response(R), sense(R, S), sense_min(M), S >= M.
valid(L, S, C) :- lab(L), shortcut(S), crop(C), hazard(S, C).

patient_now(T) :- trait(T), patient_trait(T).
init_patience(5) :- trait(T), patient_now(T).
init_patience(3) :- trait(T), not patient_now(T).

older_partner :- relation(partners), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- older_partner.
bonus(0) :- not older_partner.
authority(P + 1 + B) :- init_patience(P), bonus(B).
averted :- older_partner, authority(A), impulse_init(I), A > I.

severity(Sn + D) :- chosen_crop(C), sensitivity(C, Sn), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
recovered :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(recovered) :- not averted, recovered.
outcome(wilted) :- not averted, not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for lab_id in THEMES:
        lines.append(asp.fact("lab", lab_id))
    for shortcut_id in SHORTCUTS:
        lines.append(asp.fact("shortcut", shortcut_id))
    for crop_id, crop in CROPS.items():
        lines.append(asp.fact("crop", crop_id))
        if crop.living:
            lines.append(asp.fact("living", crop_id))
        lines.append(asp.fact("sensitivity", crop_id, crop.sensitivity))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("impulse_init", int(IMPULSE_INIT)))
    for trait in sorted(PATIENT_TRAITS):
        lines.append(asp.fact("patient_trait", trait))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_crop", params.crop),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.caution_trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    py_sens = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sens)} python={sorted(py_sens)}")

    cases = list(CURATED)
    for seed in range(120):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(smoke, trace=False, qa=False, header="### smoke")
        print("OK: smoke generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Hydroponic research fable: a rushed shortcut, a kind warning, and a careful lesson."
    )
    ap.add_argument("--lab", choices=THEMES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--mentor", choices=["tortoise", "heron", "beaver"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the strong feed sits before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_pair(rng: random.Random) -> tuple[tuple[str, str], tuple[str, str]]:
    first = rng.choice(NAME_TYPES)
    second = rng.choice([pair for pair in NAME_TYPES if pair[0] != first[0]])
    return first, second


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.crop is not None:
        crop = CROPS[args.crop]
        shortcut = SHORTCUTS[args.shortcut] if args.shortcut else next(iter(SHORTCUTS.values()))
        if not hazard_at_risk(shortcut, crop):
            raise StoryError(explain_rejection(shortcut, crop))
    if args.shortcut and args.crop:
        shortcut = SHORTCUTS[args.shortcut]
        crop = CROPS[args.crop]
        if not hazard_at_risk(shortcut, crop):
            raise StoryError(explain_rejection(shortcut, crop))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.lab is None or combo[0] == args.lab)
        and (args.shortcut is None or combo[1] == args.shortcut)
        and (args.crop is None or combo[2] == args.crop)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    lab_id, shortcut_id, crop_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    tool1, tool2 = rng.sample(sorted(SAFE_TOOLS.keys()), 2)
    first, second = _pick_pair(rng)
    mentor = args.mentor or rng.choice(["tortoise", "heron", "beaver"])
    caution_trait = rng.choice(CAUTION_TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["partners", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(2, 8)
    return StoryParams(
        lab=lab_id,
        shortcut=shortcut_id,
        crop=crop_id,
        tool1=tool1,
        tool2=tool2,
        response=response_id,
        instigator=first[0],
        instigator_type=first[1],
        cautioner=second[0],
        cautioner_type=second[1],
        mentor=mentor,
        caution_trait=caution_trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.lab not in THEMES:
        raise StoryError(f"(Unknown lab: {params.lab})")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Unknown shortcut: {params.shortcut})")
    if params.crop not in CROPS:
        raise StoryError(f"(Unknown crop: {params.crop})")
    if params.tool1 not in SAFE_TOOLS or params.tool2 not in SAFE_TOOLS:
        raise StoryError("(Unknown safe tool.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(SHORTCUTS[params.shortcut], CROPS[params.crop]):
        raise StoryError(explain_rejection(SHORTCUTS[params.shortcut], CROPS[params.crop]))
    if params.tool1 == params.tool2:
        raise StoryError("(Choose two different safe tools.)")

    world = tell(
        THEMES[params.lab],
        SHORTCUTS[params.shortcut],
        CROPS[params.crop],
        (SAFE_TOOLS[params.tool1], SAFE_TOOLS[params.tool2]),
        RESPONSES[params.response],
        instigator=params.instigator,
        instigator_type=params.instigator_type,
        cautioner=params.cautioner,
        cautioner_type=params.cautioner_type,
        caution_trait=params.caution_trait,
        mentor_type=params.mentor,
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
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (lab, shortcut, crop) combos:\n")
        for lab_id, shortcut_id, crop_id in combos:
            print(f"  {lab_id:18} {shortcut_id:14} {crop_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.shortcut} with {p.crop} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
