#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/land_gerund_rhetoric_neon_teamwork_comedy.py
=======================================================================

A standalone story world about two children building a silly parade sign for
Word Day. The sign must carry three funny vocabulary cards -- "land-gerund",
"rhetoric", and "neon" -- and the comedy comes from one child trying to do too
much alone before learning that teamwork is faster, straighter, and much less
bonky.

The world model tracks:
- physical meters: wobble, crooked, torn, attached
- emotional memes: pride, worry, relief, joy, teamwork

Reasonableness gate:
- a support method must fit the frame surface
- a support method must be strong enough for the decoration's weight

Outcome model:
- the first solo attempt creates a mishap severity based on frame instability,
  decoration awkwardness, and delay
- low severity -> the original sign survives and the team fixes it together
- high severity -> the sign tears and they make a smaller backup sign together

Run it
------
python storyworlds/worlds/gpt-5.4/land_gerund_rhetoric_neon_teamwork_comedy.py
python storyworlds/worlds/gpt-5.4/land_gerund_rhetoric_neon_teamwork_comedy.py --frame wagon --decoration banner --support clips
python storyworlds/worlds/gpt-5.4/land_gerund_rhetoric_neon_teamwork_comedy.py --support tape_tabs
python storyworlds/worlds/gpt-5.4/land_gerund_rhetoric_neon_teamwork_comedy.py --all
python storyworlds/worlds/gpt-5.4/land_gerund_rhetoric_neon_teamwork_comedy.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/land_gerund_rhetoric_neon_teamwork_comedy.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher_f"}
        male = {"boy", "father", "dad", "man", "teacher_m"}
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
            "teacher_f": "teacher",
            "teacher_m": "teacher",
        }.get(self.type, self.type)


@dataclass
class Frame:
    id: str
    label: str
    phrase: str
    surface: str
    instability: int
    parade_line: str
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
class Decoration:
    id: str
    label: str
    phrase: str
    weight: int
    awkwardness: int
    funny_shape: str
    finale: str
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
class Support:
    id: str
    label: str
    phrase: str
    hold: int
    surfaces: set[str]
    fix_text: str
    qa_text: str
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


def _r_wobble(world: World) -> list[str]:
    sign = world.get("sign")
    frame = world.get("frame")
    if sign.meters["lifted"] < THRESHOLD:
        return []
    if world.facts.get("team_ready", False):
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    frame.meters["wobble"] += float(frame.attrs["instability"])
    for kid_id in ("leader", "partner"):
        world.get(kid_id).memes["worry"] += 1
    return ["__wobble__"]


def _r_crooked(world: World) -> list[str]:
    sign = world.get("sign")
    frame = world.get("frame")
    if sign.meters["half_stuck"] < THRESHOLD or frame.meters["wobble"] < THRESHOLD:
        return []
    sig = ("crooked",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sign.meters["crooked"] += 1
    return ["__crooked__"]


def _r_tear(world: World) -> list[str]:
    sign = world.get("sign")
    if sign.meters["crooked"] < THRESHOLD:
        return []
    severity = int(world.facts["mishap_severity"])
    if severity < 4:
        return []
    sig = ("tear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sign.meters["torn"] += 1
    return ["__tear__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="crooked", tag="physical", apply=_r_crooked),
    Rule(name="tear", tag="physical", apply=_r_tear),
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


def support_fits(frame: Frame, support: Support) -> bool:
    return frame.surface in support.surfaces


def support_holds(decoration: Decoration, support: Support) -> bool:
    return support.hold >= decoration.weight


def valid_combo(frame: Frame, decoration: Decoration, support: Support) -> bool:
    return support_fits(frame, support) and support_holds(decoration, support)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for frame_id, frame in FRAMES.items():
        for decoration_id, decoration in DECORATIONS.items():
            for support_id, support in SUPPORTS.items():
                if valid_combo(frame, decoration, support):
                    combos.append((frame_id, decoration_id, support_id))
    return combos


def mishap_severity(frame: Frame, decoration: Decoration, delay: int) -> int:
    return frame.instability + decoration.awkwardness + delay


def outcome_of(params: "StoryParams") -> str:
    _check_params(params)
    severity = mishap_severity(FRAMES[params.frame], DECORATIONS[params.decoration], params.delay)
    return "backup" if severity >= 4 else "smooth"


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    sign = sim.get("sign")
    sign.meters["lifted"] += 1
    sign.meters["half_stuck"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("frame").meters["wobble"],
        "crooked": sim.get("sign").meters["crooked"],
        "torn": sim.get("sign").meters["torn"],
    }


def introduce(world: World, leader: Entity, partner: Entity, teacher: Entity,
              frame: Frame, decoration: Decoration) -> None:
    for kid in (leader, partner):
        kid.memes["joy"] += 1
    world.say(
        f"It was Word Day at school, and {leader.id} and {partner.id} were helping "
        f"{teacher.label_word} build {frame.phrase}."
    )
    world.say(
        f"On the table lay {decoration.phrase}, plus three giant word cards that made "
        f"everyone giggle: land-gerund, rhetoric, and neon."
    )
    world.say(
        f'The plan was simple: fasten the sign to {frame.phrase} and roll it into the hall. '
        f'The sign already looked {decoration.funny_shape}.'
    )


def boast(world: World, leader: Entity, decoration: Decoration) -> None:
    leader.memes["pride"] += 1
    world.say(
        f'{leader.id} puffed up and gave a grand little speech full of rhetoric. '
        f'"Please, please, stand back," {leader.pronoun()} said. "I shall attach this '
        f'{decoration.label} with the grace of a dancing goose."'
    )


def warn(world: World, partner: Entity, leader: Entity, frame: Frame, decoration: Decoration) -> None:
    pred = predict_mishap(world)
    world.facts["predicted_wobble"] = int(pred["wobble"])
    world.facts["predicted_torn"] = bool(pred["torn"] >= THRESHOLD)
    extra = "and the middle might rip" if pred["torn"] >= THRESHOLD else "and it could go on crooked"
    partner.memes["worry"] += 1
    world.say(
        f'{partner.id} looked at {frame.label} and then at the huge {decoration.label}. '
        f'"Maybe not alone," {partner.pronoun()} said. "If nobody steadies the frame, it will wobble, '
        f'{extra}."'
    )


def solo_attempt(world: World, leader: Entity, decoration: Decoration) -> None:
    sign = world.get("sign")
    sign.meters["lifted"] += 1
    sign.meters["half_stuck"] += 1
    leader.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {leader.id} was already reaching up on tiptoe, one corner of the {decoration.label} in "
        f"one hand and the fastener in the other."
    )


def mishap(world: World, leader: Entity, partner: Entity, frame: Frame, decoration: Decoration) -> None:
    sign = world.get("sign")
    if sign.meters["torn"] >= THRESHOLD:
        leader.memes["embarrassment"] += 1
        partner.memes["worry"] += 1
        world.say(
            f"The whole {frame.label} gave a comedy shimmy. The sign leaned left, leaned right, "
            f"and then made a sad paper rrrip straight through the bright middle."
        )
        world.say(
            f'"Oh, splendid," {leader.id} said in a tiny voice. "My solo masterpiece has become '
            f'a neon napkin."'
        )
    elif sign.meters["crooked"] >= THRESHOLD:
        leader.memes["embarrassment"] += 1
        partner.memes["worry"] += 1
        world.say(
            f"The {frame.label} wobbled, and the sign landed sideways. Now land-gerund was climbing uphill, "
            f"rhetoric was sliding downhill, and neon looked seasick."
        )
        world.say(
            f'{partner.id} bit {partner.pronoun("possessive")} lip, trying not to laugh at the crooked word parade.'
        )


def teacher_turn(world: World, teacher: Entity, leader: Entity, partner: Entity, support: Support) -> None:
    for kid in (leader, partner):
        kid.memes["relief"] += 1
    world.say(
        f'{teacher.label_word.capitalize()} stepped in before anyone could make a second speech. '
        f'"Let us try the miracle called teamwork," {teacher.pronoun()} said. '
        f'"{partner.id} can steady the frame, {leader.id} can line up the words, and I will hand over '
        f'{support.phrase}."'
    )


def team_fix(world: World, leader: Entity, partner: Entity, teacher: Entity,
             frame: Frame, decoration: Decoration, support: Support) -> None:
    sign = world.get("sign")
    world.facts["team_ready"] = True
    sign.meters["attached"] += 1
    sign.meters["crooked"] = 0.0
    for kid in (leader, partner):
        kid.memes["teamwork"] += 1
        kid.memes["joy"] += 1
    teacher.memes["joy"] += 1
    world.say(
        f'Soon {partner.id} held {frame.label} still with both hands while {leader.id} carefully pressed the '
        f'words into place. {teacher.label_word.capitalize()} {support.fix_text}.'
    )
    world.say(
        f"This time the funny sign stayed straight, and all three big words sat in a neat row like ducks who had "
        f"finally learned manners."
    )


def backup_fix(world: World, leader: Entity, partner: Entity, teacher: Entity,
               frame: Frame, decoration: Decoration, support: Support) -> None:
    sign = world.get("sign")
    sign.attrs["used_backup"] = True
    world.facts["team_ready"] = True
    sign.meters["attached"] += 1
    sign.meters["crooked"] = 0.0
    for kid in (leader, partner):
        kid.memes["teamwork"] += 1
        kid.memes["joy"] += 1
        kid.memes["relief"] += 1
    teacher.memes["joy"] += 1
    world.say(
        f'"No disaster," {teacher.label_word} said. "{teacher.pronoun().capitalize()} know a smaller trick." '
        f'Together they trimmed the torn part away, made a shorter backup sign, and used {support.phrase}.'
    )
    world.say(
        f'{partner.id} steadied the frame, {leader.id} lined up the words again, and this time even the silly word '
        f'land-gerund sat proudly without drooping.'
    )


def ending(world: World, leader: Entity, partner: Entity, frame: Frame,
           decoration: Decoration, outcome: str) -> None:
    sign = world.get("sign")
    leader.memes["pride"] = 0.0
    leader.memes["joy"] += 1
    partner.memes["joy"] += 1
    if outcome == "backup":
        world.say(
            f"When the class rolled {frame.label} into the hall, the smaller sign still glowed bright and funny. "
            f"The children marched beside it, laughing as if the whole wobble had been part of the show."
        )
    else:
        world.say(
            f"When the class rolled {frame.label} into the hall, {decoration.finale}. The word cards bounced a little, "
            f"but they stayed neat and proud."
        )
    world.say(
        f'{leader.id} looked at {partner.id} and grinned. "Next time," {leader.pronoun()} said, '
        f'"less rhetoric, more teamwork."'
    )
    if sign.attrs.get("used_backup"):
        world.say("That made everybody laugh the hardest of all.")
    else:
        world.say("Even the teacher laughed, because it was exactly the right lesson for a very silly sign.")


def tell(frame: Frame, decoration: Decoration, support: Support,
         leader_name: str = "Milo", leader_gender: str = "boy",
         partner_name: str = "Tia", partner_gender: str = "girl",
         teacher_type: str = "teacher_f", delay: int = 0) -> World:
    world = World()
    world.facts["team_ready"] = False
    world.facts["mishap_severity"] = mishap_severity(frame, decoration, delay)
    world.facts["delay"] = delay

    leader = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        label=leader_name,
        phrase=leader_name,
        role="leader",
        traits=["showy", "funny"],
        tags={"teamwork"},
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        label=partner_name,
        phrase=partner_name,
        role="partner",
        traits=["steady", "thoughtful"],
        tags={"teamwork"},
    ))
    teacher = world.add(Entity(
        id="Teacher",
        kind="character",
        type=teacher_type,
        label="the teacher",
        phrase="the teacher",
        role="teacher",
        traits=["calm"],
    ))
    frame_ent = world.add(Entity(
        id="frame",
        kind="thing",
        type="frame",
        label=frame.label,
        phrase=frame.phrase,
        attrs={"surface": frame.surface, "instability": frame.instability},
        tags=set(frame.tags),
    ))
    sign_ent = world.add(Entity(
        id="sign",
        kind="thing",
        type="sign",
        label=decoration.label,
        phrase=decoration.phrase,
        attrs={"weight": decoration.weight, "awkwardness": decoration.awkwardness, "used_backup": False},
        tags=set(decoration.tags),
    ))
    frame_ent.meters["wobble"] = 0.0
    sign_ent.meters["lifted"] = 0.0
    sign_ent.meters["half_stuck"] = 0.0
    sign_ent.meters["crooked"] = 0.0
    sign_ent.meters["torn"] = 0.0
    sign_ent.meters["attached"] = 0.0
    leader.memes["pride"] = 0.0
    leader.memes["embarrassment"] = 0.0
    partner.memes["worry"] = 0.0
    teacher.memes["joy"] = 0.0

    introduce(world, leader, partner, teacher, frame, decoration)
    world.para()
    boast(world, leader, decoration)
    warn(world, partner, leader, frame, decoration)
    solo_attempt(world, leader, decoration)
    mishap(world, leader, partner, frame, decoration)
    world.para()
    teacher_turn(world, teacher, leader, partner, support)

    outcome = "backup" if sign_ent.meters["torn"] >= THRESHOLD else "smooth"
    if outcome == "backup":
        backup_fix(world, leader, partner, teacher, frame, decoration, support)
    else:
        team_fix(world, leader, partner, teacher, frame, decoration, support)

    world.para()
    ending(world, leader, partner, frame, decoration, outcome)
    world.facts.update(
        leader=leader,
        partner=partner,
        teacher=teacher,
        frame_cfg=frame,
        decoration_cfg=decoration,
        support_cfg=support,
        frame=frame_ent,
        sign=sign_ent,
        outcome=outcome,
        used_backup=bool(sign_ent.attrs.get("used_backup")),
        predicted_torn=world.facts.get("predicted_torn", False),
    )
    return world


FRAMES = {
    "wagon": Frame(
        id="wagon",
        label="wagon",
        phrase="a red classroom wagon",
        surface="rail",
        instability=1,
        parade_line="the wagon squeaked like a mouse in tap shoes",
        tags={"wagon", "teamwork"},
    ),
    "arch": Frame(
        id="arch",
        label="arch",
        phrase="a broom-handle arch wrapped in silver paper",
        surface="pole",
        instability=2,
        parade_line="the arch had the manners of a sleepy flamingo",
        tags={"arch", "teamwork"},
    ),
    "board": Frame(
        id="board",
        label="display board",
        phrase="a tall cardboard display board on little wheels",
        surface="flat",
        instability=1,
        parade_line="the board rolled as grandly as a king on skates",
        tags={"board", "teamwork"},
    ),
}

DECORATIONS = {
    "banner": Decoration(
        id="banner",
        label="banner",
        phrase="a long strip of neon paper with bubble letters",
        weight=1,
        awkwardness=1,
        funny_shape="like a giant smile with corners",
        finale="the long banner glowed neon under the hall lights",
        tags={"neon", "paper"},
    ),
    "wheel": Decoration(
        id="wheel",
        label="word wheel",
        phrase="a spinning word wheel with three floppy arrows",
        weight=2,
        awkwardness=2,
        funny_shape="like a surprised robot pie",
        finale="the word wheel spun once and pointed dramatically at rhetoric",
        tags={"neon", "wheel"},
    ),
    "cloud": Decoration(
        id="cloud",
        label="word cloud",
        phrase="a puffy word cloud made from folded card and bright tape",
        weight=2,
        awkwardness=1,
        funny_shape="like a thundercloud that had eaten confetti",
        finale="the word cloud bobbed over the cart like a cheerful thought",
        tags={"neon", "cloud"},
    ),
}

SUPPORTS = {
    "clips": Support(
        id="clips",
        label="binder clips",
        phrase="two shiny binder clips",
        hold=2,
        surfaces={"rail", "pole"},
        fix_text="clicked on two shiny binder clips and tugged the sign to test it",
        qa_text="used binder clips to fasten the sign",
        tags={"clips"},
    ),
    "loops": Support(
        id="loops",
        label="string loops",
        phrase="soft string loops",
        hold=2,
        surfaces={"pole", "rail"},
        fix_text="threaded soft string loops through the holes and tied them snugly",
        qa_text="tied the sign on with string loops",
        tags={"string"},
    ),
    "tape_tabs": Support(
        id="tape_tabs",
        label="tape tabs",
        phrase="thick tape tabs",
        hold=1,
        surfaces={"flat"},
        fix_text="pressed thick tape tabs across the back and smoothed every edge flat",
        qa_text="pressed thick tape tabs on the back of the sign",
        tags={"tape"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Tia", "Nora", "Zoe", "Pia", "Ava", "Mimi"]
BOY_NAMES = ["Milo", "Ben", "Owen", "Theo", "Max", "Leo", "Finn", "Eli"]


@dataclass
class StoryParams:
    frame: str
    decoration: str
    support: str
    leader: str
    leader_gender: str
    partner: str
    partner_gender: str
    teacher: str
    delay: int = 0
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


CURATED = [
    StoryParams(
        frame="wagon",
        decoration="banner",
        support="clips",
        leader="Milo",
        leader_gender="boy",
        partner="Tia",
        partner_gender="girl",
        teacher="teacher_f",
        delay=0,
    ),
    StoryParams(
        frame="arch",
        decoration="wheel",
        support="loops",
        leader="Nora",
        leader_gender="girl",
        partner="Ben",
        partner_gender="boy",
        teacher="teacher_m",
        delay=0,
    ),
    StoryParams(
        frame="board",
        decoration="cloud",
        support="tape_tabs",
        leader="Zoe",
        leader_gender="girl",
        partner="Max",
        partner_gender="boy",
        teacher="teacher_f",
        delay=1,
    ),
    StoryParams(
        frame="arch",
        decoration="cloud",
        support="clips",
        leader="Finn",
        leader_gender="boy",
        partner="Maya",
        partner_gender="girl",
        teacher="teacher_m",
        delay=1,
    ),
]


KNOWLEDGE = {
    "teamwork": [
        (
            "What does teamwork mean?",
            "Teamwork means people help each other do one job together. One person can hold, another can line things up, and the job often goes better that way.",
        )
    ],
    "neon": [
        (
            "What does neon mean?",
            "Neon means very bright, glowing color. It stands out fast, so people can spot it from far away.",
        )
    ],
    "rhetoric": [
        (
            "What is rhetoric?",
            "Rhetoric is a fancy word for using words to persuade or sound grand. In a funny story, too much rhetoric can mean a child talks big before doing the job.",
        )
    ],
    "madeup": [
        (
            "Can a funny story use a made-up word like land-gerund?",
            "Yes. A made-up word can sound silly and playful, and it can make people laugh because it feels surprising.",
        )
    ],
    "clips": [
        (
            "What is a binder clip for?",
            "A binder clip is a strong little clip that holds paper or card together. It squeezes tight, so it can keep something from slipping.",
        )
    ],
    "string": [
        (
            "What can string loops do on a craft project?",
            "String loops can tie something onto a pole or rail. They are useful when you need a soft, bendy way to hold a sign in place.",
        )
    ],
    "tape": [
        (
            "What do tape tabs do?",
            "Tape tabs stick flat things onto a flat surface. They work best when the piece is light and the back can lie smooth.",
        )
    ],
}
KNOWLEDGE_ORDER = ["teamwork", "neon", "rhetoric", "madeup", "clips", "string", "tape"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    frame = f["frame_cfg"]
    decoration = f["decoration_cfg"]
    outcome = f["outcome"]
    if outcome == "backup":
        return [
            'Write a funny story for a 3-to-5-year-old that includes the words "land-gerund," "rhetoric," and "neon," and make teamwork solve a craft disaster.',
            f"Tell a comedy where {leader.id} tries to hang a {decoration.label} alone on {frame.phrase}, it tears, and then {leader.id}, {partner.id}, and the teacher make a smaller backup sign together.",
            "Write a child-facing classroom story where big talk leads to a wobbly mistake, but teamwork turns the mistake into a cheerful parade ending.",
        ]
    return [
        'Write a funny story for a 3-to-5-year-old that includes the words "land-gerund," "rhetoric," and "neon," and make teamwork fix a silly problem.',
        f"Tell a classroom comedy where {leader.id} gives a grand speech, tries to attach a sign alone, and then works with {partner.id} to straighten it out.",
        "Write a simple story about a parade project where one child talks big, the craft goes crooked, and teamwork saves the day.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    teacher = f["teacher"]
    frame = f["frame_cfg"]
    decoration = f["decoration_cfg"]
    support = f["support_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {partner.id}, two children helping their teacher build a parade display. They are trying to hang a funny sign with the words land-gerund, rhetoric, and neon.",
        ),
        (
            "What were they making?",
            f"They were making a silly Word Day parade sign for {frame.phrase}. The sign was meant to look bright and funny so everyone in the hall would notice it.",
        ),
        (
            f"Why did {partner.id} warn {leader.id} not to do it alone?",
            f"{partner.id} could see the sign was big and the frame might wobble if nobody held it still. {partner.pronoun().capitalize()} was trying to stop a crooked or torn mess before it happened.",
        ),
    ]
    if outcome == "backup":
        qa.append(
            (
                "What went wrong on the first try?",
                f"The frame wobbled and the sign ripped through the middle. That happened because {leader.id} tried to lift and fasten the big piece alone instead of using teamwork.",
            )
        )
        qa.append(
            (
                "How did they solve the problem?",
                f"They worked together to make a smaller backup sign and {support.qa_text}. {partner.id} steadied the frame while {leader.id} lined up the words, so the second try stayed neat.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The class rolled the display into the hall with the smaller sign shining brightly. Everyone laughed, because the mistake turned into part of the funny show.",
            )
        )
    else:
        qa.append(
            (
                "What went wrong on the first try?",
                f"The sign landed crooked when the frame wobbled. The silly words ended up slanting in different directions because {leader.id} tried to do too many jobs at once.",
            )
        )
        qa.append(
            (
                "How did they fix it?",
                f"They used teamwork: {partner.id} held the frame still, {leader.id} lined up the sign, and the teacher {support.qa_text}. With steady hands and shared jobs, the sign went on straight.",
            )
        )
        qa.append(
            (
                "What did {leader.id} learn?",
                f"{leader.id} learned that big rhetoric is not as helpful as teamwork. Sharing the job made the sign straighter and the whole project much calmer.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"teamwork", "neon", "rhetoric", "madeup"} | set(f["support_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None, False)}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(frame: Frame, decoration: Decoration, support: Support) -> str:
    if not support_fits(frame, support):
        good = ", ".join(sorted(s.id for s in SUPPORTS.values() if support_fits(frame, s)))
        return (
            f"(No story: {support.label} do not fit {frame.phrase}. That support works on "
            f"{sorted(support.surfaces)}, but this frame has a {frame.surface} surface. Try: {good}.)"
        )
    if not support_holds(decoration, support):
        good = ", ".join(sorted(s.id for s in SUPPORTS.values() if support_holds(decoration, s)))
        return (
            f"(No story: {support.label} are too weak for {decoration.phrase}. The support must honestly "
            f"hold the sign up. Try: {good}.)"
        )
    return "(No story: this combination does not make a reasonable parade project.)"


def _check_params(params: StoryParams) -> None:
    if params.frame not in FRAMES:
        raise StoryError(f"(Unknown frame: {params.frame})")
    if params.decoration not in DECORATIONS:
        raise StoryError(f"(Unknown decoration: {params.decoration})")
    if params.support not in SUPPORTS:
        raise StoryError(f"(Unknown support: {params.support})")
    if params.delay not in (0, 1):
        raise StoryError("(Delay must be 0 or 1.)")
    frame = FRAMES[params.frame]
    decoration = DECORATIONS[params.decoration]
    support = SUPPORTS[params.support]
    if not valid_combo(frame, decoration, support):
        raise StoryError(explain_rejection(frame, decoration, support))


ASP_RULES = r"""
valid(F,D,S) :- frame(F), decoration(D), support(S), fits(F,S), strong_enough(D,S).

severity(V) :- chosen_frame(F), chosen_decoration(D), delay(T),
               instability(F,I), awkwardness(D,A), V = I + A + T.

outcome(backup) :- severity(V), V >= 4.
outcome(smooth) :- severity(V), V < 4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for frame_id, frame in FRAMES.items():
        lines.append(asp.fact("frame", frame_id))
        lines.append(asp.fact("instability", frame_id, frame.instability))
        lines.append(asp.fact("surface", frame_id, frame.surface))
    for decoration_id, decoration in DECORATIONS.items():
        lines.append(asp.fact("decoration", decoration_id))
        lines.append(asp.fact("weight", decoration_id, decoration.weight))
        lines.append(asp.fact("awkwardness", decoration_id, decoration.awkwardness))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        lines.append(asp.fact("hold", support_id, support.hold))
        for surf in sorted(support.surfaces):
            lines.append(asp.fact("supports_surface", support_id, surf))
    for frame_id, frame in FRAMES.items():
        for support_id, support in SUPPORTS.items():
            if support_fits(frame, support):
                lines.append(asp.fact("fits", frame_id, support_id))
    for decoration_id, decoration in DECORATIONS.items():
        for support_id, support in SUPPORTS.items():
            if support_holds(decoration, support):
                lines.append(asp.fact("strong_enough", decoration_id, support_id))
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
            asp.fact("chosen_frame", params.frame),
            asp.fact("chosen_decoration", params.decoration),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(smoke, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if "land-gerund" not in smoke.story or "neon" not in smoke.story or "rhetoric" not in smoke.story:
            raise StoryError("smoke story is missing required seed words")
        print("OK: smoke test generate()/emit() passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a funny Word Day parade sign that teaches teamwork."
    )
    ap.add_argument("--frame", choices=FRAMES)
    ap.add_argument("--decoration", choices=DECORATIONS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--teacher", choices=["teacher_f", "teacher_m"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra fumbling time before the team steps in")
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.frame and args.decoration and args.support:
        frame = FRAMES[args.frame]
        decoration = DECORATIONS[args.decoration]
        support = SUPPORTS[args.support]
        if not valid_combo(frame, decoration, support):
            raise StoryError(explain_rejection(frame, decoration, support))

    combos = [
        combo for combo in valid_combos()
        if (args.frame is None or combo[0] == args.frame)
        and (args.decoration is None or combo[1] == args.decoration)
        and (args.support is None or combo[2] == args.support)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    frame_id, decoration_id, support_id = rng.choice(sorted(combos))
    leader, leader_gender = _pick_child(rng)
    partner, partner_gender = _pick_child(rng, avoid=leader)
    teacher = args.teacher or rng.choice(["teacher_f", "teacher_m"])
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        frame=frame_id,
        decoration=decoration_id,
        support=support_id,
        leader=leader,
        leader_gender=leader_gender,
        partner=partner,
        partner_gender=partner_gender,
        teacher=teacher,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    _check_params(params)
    world = tell(
        frame=FRAMES[params.frame],
        decoration=DECORATIONS[params.decoration],
        support=SUPPORTS[params.support],
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        teacher_type=params.teacher,
        delay=params.delay,
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
        print(f"{len(combos)} compatible (frame, decoration, support) combos:\n")
        for frame_id, decoration_id, support_id in combos:
            print(f"  {frame_id:8} {decoration_id:10} {support_id}")
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
                f"### {p.leader} & {p.partner}: {p.decoration} on {p.frame} "
                f"with {p.support} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
