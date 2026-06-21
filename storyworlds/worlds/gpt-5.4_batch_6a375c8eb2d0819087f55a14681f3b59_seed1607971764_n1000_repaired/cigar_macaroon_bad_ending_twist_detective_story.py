#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cigar_macaroon_bad_ending_twist_detective_story.py
==============================================================================

A standalone story world for a tiny child-facing detective story with a twist:
a thief plants one clue to frame someone else, while the real clue points the
other way. Some stories end well when the young detective notices the trick;
some end badly when the wrong suspect is blamed and the culprit escapes.

Required seed words always appear in the world: cigar, macaroon.

Run it
------
    python storyworlds/worlds/gpt-5.4/cigar_macaroon_bad_ending_twist_detective_story.py
    python storyworlds/worlds/gpt-5.4/cigar_macaroon_bad_ending_twist_detective_story.py --culprit porter --planted macaroon_crumbs --detective hasty
    python storyworlds/worlds/gpt-5.4/cigar_macaroon_bad_ending_twist_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/cigar_macaroon_bad_ending_twist_detective_story.py --qa --seed 777
    python storyworlds/worlds/gpt-5.4/cigar_macaroon_bad_ending_twist_detective_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "cook", "duchess"}
        male = {"boy", "man", "porter", "magician"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class SuspectCfg:
    id: str
    label: str
    type: str
    title: str
    honest_job: str
    signature_clue: str
    own_text: str
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
class ClueCfg:
    id: str
    label: str
    phrase: str
    sensory: str
    points_to: str
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
class PrizeCfg:
    id: str
    label: str
    phrase: str
    shine: str
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
class LocationCfg:
    id: str
    label: str
    nook: str
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
class DetectiveCfg:
    id: str
    label: str
    carefulness: int
    style_line: str
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


def _r_frame_pressure(world: World) -> list[str]:
    culprit = world.get("culprit")
    if culprit.meters["planted"] < THRESHOLD:
        return []
    sig = ("frame_pressure", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective = world.get("detective")
    detective.memes["doubt"] += 1
    return []


def _r_wrong_accusation(world: World) -> list[str]:
    detective = world.get("detective")
    if detective.meters["accused_wrong"] < THRESHOLD:
        return []
    sig = ("wrong_accusation", detective.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit = world.get("culprit")
    culprit.memes["confidence"] += 1
    culprit.meters["escaped"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="frame_pressure", tag="social", apply=_r_frame_pressure),
    Rule(name="wrong_accusation", tag="social", apply=_r_wrong_accusation),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SUSPECTS = {
    "porter": SuspectCfg(
        id="porter",
        label="Mr. Brindle",
        type="porter",
        title="the hotel porter",
        honest_job="carried trunks and knew every corridor",
        signature_clue="cigar_ash",
        own_text="a sharp smell of cigar smoke that often clung to his red coat",
        tags={"porter", "cigar"},
    ),
    "cook": SuspectCfg(
        id="cook",
        label="Mrs. Vale",
        type="cook",
        title="the pastry cook",
        honest_job="baked sweets in the warm kitchen downstairs",
        signature_clue="macaroon_crumbs",
        own_text="pink macaroon crumbs that often dusted her apron",
        tags={"cook", "macaroon"},
    ),
    "magician": SuspectCfg(
        id="magician",
        label="Professor Vale",
        type="magician",
        title="the stage magician",
        honest_job="practised card tricks and kept white gloves in his case",
        signature_clue="glove_thread",
        own_text="a loose white glove thread from the cuffs he wore on stage",
        tags={"magician", "glove"},
    ),
}

CLUES = {
    "cigar_ash": ClueCfg(
        id="cigar_ash",
        label="cigar ash",
        phrase="a pinch of gray cigar ash",
        sensory="It smelled faintly like a cigar and looked far too neat, as if someone had sprinkled it there on purpose.",
        points_to="porter",
        tags={"cigar", "ash"},
    ),
    "macaroon_crumbs": ClueCfg(
        id="macaroon_crumbs",
        label="macaroon crumbs",
        phrase="three rosy macaroon crumbs",
        sensory="The crumbs were sweet and crisp, and one tiny flake had stuck to the thief's damp fingerprint.",
        points_to="cook",
        tags={"macaroon", "crumbs"},
    ),
    "glove_thread": ClueCfg(
        id="glove_thread",
        label="glove thread",
        phrase="a twist of white glove thread",
        sensory="The thread was caught on the brass latch, tugged loose by a hurried hand.",
        points_to="magician",
        tags={"glove", "thread"},
    ),
}

PRIZES = {
    "brooch": PrizeCfg(
        id="brooch",
        label="moon brooch",
        phrase="the Moon Duchess's silver moon brooch",
        shine="It flashed like a tiny moon whenever it caught the lamp light.",
        tags={"brooch", "silver"},
    ),
    "key": PrizeCfg(
        id="key",
        label="opal key",
        phrase="the hotel's opal key",
        shine="It glimmered with a pale blue sparkle in its little velvet tray.",
        tags={"key", "opal"},
    ),
}

LOCATIONS = {
    "parlor": LocationCfg(
        id="parlor",
        label="the blue parlor",
        nook="between the velvet curtains and the little marble fireplace",
        tags={"parlor"},
    ),
    "gallery": LocationCfg(
        id="gallery",
        label="the upstairs gallery",
        nook="beneath a row of dusty portraits",
        tags={"gallery"},
    ),
}

DETECTIVES = {
    "careful": DetectiveCfg(
        id="careful",
        label="careful",
        carefulness=3,
        style_line="noticed what did not fit, not only what looked loud and obvious",
        tags={"careful"},
    ),
    "hasty": DetectiveCfg(
        id="hasty",
        label="hasty",
        carefulness=1,
        style_line="leapt at the first clue and wanted the mystery solved at once",
        tags={"hasty"},
    ),
}


def real_clue_for(culprit_id: str) -> str:
    return SUSPECTS[culprit_id].signature_clue


def valid_combo(culprit: str, planted: str) -> bool:
    if culprit not in SUSPECTS or planted not in CLUES:
        return False
    return planted != real_clue_for(culprit)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for culprit in sorted(SUSPECTS):
        for planted in sorted(CLUES):
            if valid_combo(culprit, planted):
                combos.append((culprit, planted))
    return combos


@dataclass
class StoryParams:
    culprit: str
    planted: str
    prize: str
    location: str
    detective: str
    child_name: str
    child_gender: str
    guardian_type: str
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


def accused_suspect_id(params: StoryParams) -> str:
    if params.detective == "hasty":
        return CLUES[params.planted].points_to
    return params.culprit


def outcome_of(params: StoryParams) -> str:
    return "escaped" if accused_suspect_id(params) != params.culprit else "solved"


def explain_rejection(culprit: str, planted: str) -> str:
    if culprit not in SUSPECTS:
        return f"(No story: unknown culprit '{culprit}'.)"
    if planted not in CLUES:
        return f"(No story: unknown planted clue '{planted}'.)"
    if planted == real_clue_for(culprit):
        return (
            f"(No story: {SUSPECTS[culprit].title} cannot frame someone with "
            f"{CLUES[planted].label}, because that clue already points straight back "
            f"to the real culprit. Pick a different planted clue for the twist.)"
        )
    return "(No story: invalid combination.)"


def introduce(world: World, child: Entity, guardian: Entity, prize: PrizeCfg, location: LocationCfg) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"At twilight, {child.id} walked through the Grand Fern Hotel beside "
        f"{child.pronoun('possessive')} {guardian.label_word}. In {location.label}, "
        f"everyone had come to admire {prize.phrase}."
    )
    world.say(prize.shine)
    world.say(
        f"{child.id} loved little mysteries and had a notebook tucked in one pocket."
    )


def theft(world: World, culprit: Entity, prize: PrizeCfg, location: LocationCfg) -> None:
    culprit.meters["stolen"] += 1
    world.say(
        f"Then the lamps flickered, a tray crashed in the hall, and when the room "
        f"grew still again, {prize.phrase} was gone from its stand {location.nook}."
    )
    world.say(
        f"A soft murmur ran through the room. Somebody had stolen it."
    )


def inspect_scene(world: World, child: Entity, planted: ClueCfg, real: ClueCfg) -> None:
    child.memes["focus"] += 1
    world.say(
        f"{child.id} knelt by the empty stand and found two strange signs: "
        f"{planted.phrase}, and a second thing -- {real.phrase}."
    )
    world.say(planted.sensory)
    world.say(real.sensory)


def interview(world: World, child: Entity, suspects: list[Entity]) -> None:
    child.memes["nerve"] += 1
    bits = ", ".join(f"{s.label}, {s.attrs['cfg'].title}" for s in suspects[:-1])
    last = f"and {suspects[-1].label}, {suspects[-1].attrs['cfg'].title}"
    world.say(
        f"{child.id} questioned {bits}, {last}. Everyone sounded calm, but not everyone sounded true."
    )


def deduce(world: World, child: Entity, culprit: Entity, planted: ClueCfg, real: ClueCfg, detective_cfg: DetectiveCfg) -> None:
    world.say(
        f"{child.id} {detective_cfg.style_line}. The planted clue pointed toward "
        f"{SUSPECTS[planted.points_to].title}, but the other clue fit "
        f"{culprit.label} much better."
    )


def accuse_wrong(world: World, child: Entity, accused: Entity, culprit: Entity, guardian: Entity, planted: ClueCfg, prize: PrizeCfg) -> None:
    detective = world.get("detective")
    detective.meters["accused_wrong"] += 1
    propagate(world, narrate=False)
    accused.memes["hurt"] += 1
    guardian.memes["alarm"] += 1
    world.say(
        f'"I know who did it," {child.id} said, pointing at {accused.label}. '
        f'"It was {accused.pronoun("object")} because of the {planted.label}."'
    )
    world.say(
        f"But that was the twist: the clue had been planted. While everyone stared at "
        f"{accused.label}, {culprit.label} slipped down the back stairs with {prize.phrase} hidden away."
    )
    world.say(
        f"By the time the grown-ups understood the mistake, the night door was swinging open and the thief was gone."
    )


def accuse_right(world: World, child: Entity, culprit: Entity, guardian: Entity, real: ClueCfg, prize: PrizeCfg, location: LocationCfg) -> None:
    culprit.meters["caught"] += 1
    guardian.memes["pride"] += 1
    world.say(
        f'"The loud clue was a trick," {child.id} said at last. "The real clue is the '
        f'{real.label}. It points to {culprit.label}."'
    )
    world.say(
        f"{culprit.label} tried to laugh, but {culprit.pronoun('possessive')} face "
        f"went pale. Inside a hollow umbrella stand near {location.nook}, the grown-ups found {prize.phrase}."
    )
    world.say(
        f"The case was solved before the thief could reach the door."
    )


def endings(world: World, child: Entity, guardian: Entity, prize: PrizeCfg, outcome: str) -> None:
    if outcome == "escaped":
        child.memes["sorrow"] += 1
        world.say(
            f"Later, {child.id} sat very still with the notebook shut. "
            f"{guardian.label_word.capitalize()} put an arm around {child.pronoun('object')} and said that real detectives must look twice before they speak."
        )
        world.say(
            f"The empty stand still waited in the lamplight, and {prize.phrase} did not come back that night."
        )
    else:
        child.memes["relief"] += 1
        world.say(
            f"Afterward, {guardian.label_word} squeezed {child.pronoun('possessive')} shoulder. "
            f"{child.id} wrote one neat line in the notebook: Loud clues can lie."
        )
        world.say(
            f"Back on its stand, {prize.phrase} shone again, and the whole room felt safe."
        )


def tell(
    prize: PrizeCfg,
    location: LocationCfg,
    culprit_cfg: SuspectCfg,
    planted_cfg: ClueCfg,
    detective_cfg: DetectiveCfg,
    child_name: str = "Nell",
    child_gender: str = "girl",
    guardian_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="detective_child", label=child_name))
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type, role="guardian", label="the parent"))
    culprit = world.add(Entity(id="culprit", kind="character", type=culprit_cfg.type, role="culprit", label=culprit_cfg.label, attrs={"cfg": culprit_cfg}))
    porter = world.add(Entity(id="porter", kind="character", type=SUSPECTS["porter"].type, role="suspect", label=SUSPECTS["porter"].label, attrs={"cfg": SUSPECTS["porter"]}))
    cook = world.add(Entity(id="cook", kind="character", type=SUSPECTS["cook"].type, role="suspect", label=SUSPECTS["cook"].label, attrs={"cfg": SUSPECTS["cook"]}))
    magician = world.add(Entity(id="magician", kind="character", type=SUSPECTS["magician"].type, role="suspect", label=SUSPECTS["magician"].label, attrs={"cfg": SUSPECTS["magician"]}))
    detective = world.add(Entity(id="detective", kind="thing", type="mind", role="reasoner", label="reasoning"))

    detective.attrs["carefulness"] = detective_cfg.carefulness
    detective.memes["doubt"] = 0.0
    detective.meters["accused_wrong"] = 0.0
    culprit.meters["planted"] = 1.0
    culprit.meters["caught"] = 0.0
    culprit.meters["escaped"] = 0.0
    culprit.meters["stolen"] = 0.0
    culprit.memes["confidence"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["focus"] = 0.0
    child.memes["nerve"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["sorrow"] = 0.0
    guardian.memes["alarm"] = 0.0
    guardian.memes["pride"] = 0.0

    world.facts["prize"] = prize
    world.facts["location"] = location
    world.facts["culprit_cfg"] = culprit_cfg
    world.facts["planted_cfg"] = planted_cfg
    world.facts["real_cfg"] = CLUES[real_clue_for(culprit_cfg.id)]
    propagate(world, narrate=False)

    introduce(world, child, guardian, prize, location)
    world.para()
    theft(world, culprit, prize, location)
    inspect_scene(world, child, planted_cfg, world.facts["real_cfg"])
    suspects = [porter, cook, magician]
    interview(world, child, suspects)
    world.para()
    deduce(world, child, culprit, planted_cfg, world.facts["real_cfg"], detective_cfg)

    accused_id = accused_suspect_id(
        StoryParams(
            culprit=culprit_cfg.id,
            planted=planted_cfg.id,
            prize=prize.id,
            location=location.id,
            detective=detective_cfg.id,
            child_name=child_name,
            child_gender=child_gender,
            guardian_type=guardian_type,
        )
    )
    accused = world.get(accused_id)
    outcome = "escaped" if accused_id != culprit_cfg.id else "solved"
    if outcome == "escaped":
        accuse_wrong(world, child, accused, culprit, guardian, planted_cfg, prize)
    else:
        accuse_right(world, child, culprit, guardian, world.facts["real_cfg"], prize, location)
    world.para()
    endings(world, child, guardian, prize, outcome)

    world.facts.update(
        child=child,
        guardian=guardian,
        culprit=culprit,
        suspects=suspects,
        accused=accused,
        outcome=outcome,
        accused_id=accused_id,
        planted_points_to=planted_cfg.points_to,
        real_points_to=culprit_cfg.id,
        twist=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    prize = world.facts["prize"]
    planted = world.facts["planted_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "escaped":
        return [
            f'Write a child-friendly detective story with the words "cigar" and "macaroon", where a planted clue causes a bad ending.',
            f"Tell a detective tale about {child.id}, a missing treasure, and a twist: the first clue looks right but was planted to frame the wrong suspect.",
            f"Write a short mystery where {prize.phrase} is stolen, {planted.label} misleads the young detective, and the real thief escapes in the end.",
        ]
    return [
        f'Write a child-friendly detective story with the words "cigar" and "macaroon", where a planted clue creates a twist.',
        f"Tell a detective tale about {child.id}, a missing treasure, and a sharp-eyed child who notices that the obvious clue is a trick.",
        f"Write a short mystery where {prize.phrase} is stolen, the young detective spots the twist, and the real thief is caught.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    guardian = world.facts["guardian"]
    prize = world.facts["prize"]
    location = world.facts["location"]
    culprit = world.facts["culprit"]
    accused = world.facts["accused"]
    planted = world.facts["planted_cfg"]
    real = world.facts["real_cfg"]
    outcome = world.facts["outcome"]

    items: list[tuple[str, str]] = [
        (
            "What mystery began the story?",
            f"The mystery began when {prize.phrase} vanished from {location.label}. The missing treasure is what turned an ordinary evening into a detective case.",
        ),
        (
            f"What clues did {child.id} find?",
            f"{child.id} found {planted.phrase} and also {real.phrase}. One clue was meant to fool people, but the other clue fit the real thief.",
        ),
        (
            "What was the twist?",
            f"The twist was that the obvious clue had been planted to frame someone else. The thief hoped everybody would stare at the wrong suspect and miss the truer sign.",
        ),
    ]
    if outcome == "escaped":
        items.append(
            (
                f"Why did the case end badly?",
                f"It ended badly because {child.id} trusted the planted {planted.label} and accused {accused.label}. While everyone looked the wrong way, {culprit.label} escaped with {prize.phrase}.",
            )
        )
        items.append(
            (
                f"What did {child.id} learn?",
                f"{child.id} learned that a loud clue is not always an honest clue. In a detective story, noticing what does not fit can matter more than grabbing the first answer.",
            )
        )
    else:
        items.append(
            (
                f"How did {child.id} solve the case?",
                f"{child.id} saw that the {planted.label} was too neat and too convenient, but the {real.label} matched {culprit.label}. That careful second look uncovered the trick and led the grown-ups to the hidden treasure.",
            )
        )
        items.append(
            (
                "How did the story end?",
                f"It ended with the thief caught and {prize.phrase} returned to its stand. The bright ending shows that the careful clue, not the noisy one, told the truth.",
            )
        )
    items.append(
        (
            f"Who helped {child.id} feel better at the end?",
            f"{guardian.label_word.capitalize()} stayed close and spoke gently to {child.pronoun('object')}. That comfort matters because the mystery left a strong feeling behind, whether the case was solved or not.",
        )
    )
    return items


KNOWLEDGE = {
    "cigar": [
        (
            "What is a cigar?",
            "A cigar is a rolled tobacco stick that grown-ups sometimes smoke. It makes a strong smell and leaves ash behind.",
        )
    ],
    "macaroon": [
        (
            "What is a macaroon?",
            "A macaroon is a small sweet cookie, often crisp outside and soft inside. It can leave crumbs if someone eats or carries it.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to work out what really happened. Good detectives check carefully before deciding.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand a mystery. A footprint, a crumb, or a thread can all be clues.",
        )
    ],
    "twist": [
        (
            "What is a twist in a story?",
            "A twist is a surprising turn that changes what you think is true. It makes the story suddenly look different.",
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "clue", "cigar", "macaroon", "twist"]


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "clue", "twist", "cigar", "macaroon"}
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: (v.id if hasattr(v, "id") else v) for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} accused={world.facts.get('accused_id')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        culprit="porter",
        planted="macaroon_crumbs",
        prize="brooch",
        location="parlor",
        detective="hasty",
        child_name="Nell",
        child_gender="girl",
        guardian_type="mother",
    ),
    StoryParams(
        culprit="cook",
        planted="cigar_ash",
        prize="key",
        location="gallery",
        detective="careful",
        child_name="Theo",
        child_gender="boy",
        guardian_type="father",
    ),
    StoryParams(
        culprit="magician",
        planted="cigar_ash",
        prize="brooch",
        location="parlor",
        detective="hasty",
        child_name="Mira",
        child_gender="girl",
        guardian_type="mother",
    ),
    StoryParams(
        culprit="porter",
        planted="glove_thread",
        prize="key",
        location="gallery",
        detective="careful",
        child_name="Ben",
        child_gender="boy",
        guardian_type="father",
    ),
]


ASP_RULES = r"""
valid(C,P) :- suspect(C), clue(P), real_clue(C,R), P != R.
accused(A) :- detective(hasty), planted_points_to(A).
accused(A) :- detective(careful), culprit(C), A = C.
outcome(escaped) :- culprit(C), accused(A), A != C.
outcome(solved)  :- culprit(C), accused(A), A = C.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("real_clue", sid, suspect.signature_clue))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("planted_points_to", clue.points_to) if False else "")
    return "\n".join(line for line in lines if line)


def asp_program(extra: str, show: str) -> str:
    import asp
    lines: list[str] = []
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("real_clue", sid, suspect.signature_clue))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("points_to", cid, clue.points_to))
    program = "\n".join(lines)
    program += "\n" + ASP_RULES + "\n"
    program += extra + "\n"
    program += show + "\n"
    return program


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("culprit", params.culprit),
            asp.fact("planted", params.planted),
            asp.fact("planted_points_to", CLUES[params.planted].points_to),
            asp.fact("detective", params.detective),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny detective story world with a planted clue, a twist, and sometimes a bad ending."
    )
    ap.add_argument("--culprit", choices=sorted(SUSPECTS))
    ap.add_argument("--planted", choices=sorted(CLUES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--location", choices=sorted(LOCATIONS))
    ap.add_argument("--detective", choices=sorted(DETECTIVES))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--guardian-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid culprit/planted-clue combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Nell", "Mira", "Lucy", "Ada", "Ruth", "Ivy"]
BOY_NAMES = ["Theo", "Ben", "Max", "Eli", "Owen", "Noah"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.planted and not valid_combo(args.culprit, args.planted):
        raise StoryError(explain_rejection(args.culprit, args.planted))

    combos = [
        combo
        for combo in valid_combos()
        if (args.culprit is None or combo[0] == args.culprit)
        and (args.planted is None or combo[1] == args.planted)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    culprit, planted = rng.choice(sorted(combos))
    prize = args.prize or rng.choice(sorted(PRIZES))
    location = args.location or rng.choice(sorted(LOCATIONS))
    detective = args.detective or rng.choice(sorted(DETECTIVES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    guardian_type = args.guardian_type or rng.choice(["mother", "father"])

    return StoryParams(
        culprit=culprit,
        planted=planted,
        prize=prize,
        location=location,
        detective=detective,
        child_name=child_name,
        child_gender=child_gender,
        guardian_type=guardian_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.culprit not in SUSPECTS:
        raise StoryError(f"(No story: unknown culprit '{params.culprit}'.)")
    if params.planted not in CLUES:
        raise StoryError(f"(No story: unknown planted clue '{params.planted}'.)")
    if params.prize not in PRIZES:
        raise StoryError(f"(No story: unknown prize '{params.prize}'.)")
    if params.location not in LOCATIONS:
        raise StoryError(f"(No story: unknown location '{params.location}'.)")
    if params.detective not in DETECTIVES:
        raise StoryError(f"(No story: unknown detective style '{params.detective}'.)")
    if not valid_combo(params.culprit, params.planted):
        raise StoryError(explain_rejection(params.culprit, params.planted))

    world = tell(
        prize=PRIZES[params.prize],
        location=LOCATIONS[params.location],
        culprit_cfg=SUSPECTS[params.culprit],
        planted_cfg=CLUES[params.planted],
        detective_cfg=DETECTIVES[params.detective],
        child_name=params.child_name,
        child_gender=params.child_gender,
        guardian_type=params.guardian_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure at seed {seed}.")
            continue
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (culprit, planted clue) combos:\n")
        for culprit, planted in combos:
            print(f"  {culprit:9} {planted}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: culprit={p.culprit}, planted={p.planted}, outcome={outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
