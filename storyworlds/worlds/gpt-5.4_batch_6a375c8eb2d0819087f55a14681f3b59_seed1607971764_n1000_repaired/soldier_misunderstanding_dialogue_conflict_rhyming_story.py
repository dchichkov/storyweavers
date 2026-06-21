#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/soldier_misunderstanding_dialogue_conflict_rhyming_story.py
======================================================================================

A standalone story world about a child pretending to be a soldier at the door of
a play fort. Another child arrives with something messy, hears the warning
wrong, and thinks the soldier is sending *them* away. The conflict is resolved
through dialogue, a clear explanation, and a small practical fix.

The stories are written in a gentle rhyming style, but the prose still comes
from simulated state:

- a place has a fragile inside and available cleanup methods
- a visitor brings a physical mess risk
- the soldier blocks entry to protect the fort
- the muffled doorway plus hurt feelings create a misunderstanding
- dialogue clarifies the meaning
- cleanup changes the physical state, then the fort can be shared safely

Run it
------
    python storyworlds/worlds/gpt-5.4/soldier_misunderstanding_dialogue_conflict_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/soldier_misunderstanding_dialogue_conflict_rhyming_story.py --place blanket_fort --risk muddy_boots
    python storyworlds/worlds/gpt-5.4/soldier_misunderstanding_dialogue_conflict_rhyming_story.py --place blanket_fort --risk sticky_hands
    python storyworlds/worlds/gpt-5.4/soldier_misunderstanding_dialogue_conflict_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/soldier_misunderstanding_dialogue_conflict_rhyming_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/soldier_misunderstanding_dialogue_conflict_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    scene: str
    roof: str
    fragile: str
    fragile_to: set[str] = field(default_factory=set)
    offers: set[str] = field(default_factory=set)
    muffled: bool = True
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
class Risk:
    id: str
    label: str
    mess: str
    carry_line: str
    warning_noun: str
    threaten_line: str
    cleanup_prompt: str
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
class Fix:
    id: str
    label: str
    fixes: set[str] = field(default_factory=set)
    do_line: str = ""
    result_line: str = ""
    qa_line: str = ""
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
    def __init__(self, place: Place) -> None:
        self.place_cfg = place
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
        clone = World(self.place_cfg)
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


def _r_misunderstanding_conflict(world: World) -> list[str]:
    soldier = world.get("soldier")
    visitor = world.get("visitor")
    if visitor.memes["misunderstanding"] < THRESHOLD:
        return []
    sig = ("conflict", visitor.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    visitor.memes["hurt"] += 1
    visitor.memes["conflict"] += 1
    soldier.memes["conflict"] += 1
    return []


def _r_enter_spoils(world: World) -> list[str]:
    fort = world.get("fort")
    visitor = world.get("visitor")
    if visitor.meters["inside"] < THRESHOLD:
        return []
    if visitor.meters["messy"] < THRESHOLD:
        return []
    sig = ("spoil", fort.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    fort.meters["spoiled"] += 1
    visitor.memes["regret"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="misunderstanding_conflict", tag="social", apply=_r_misunderstanding_conflict),
    Rule(name="enter_spoils", tag="physical", apply=_r_enter_spoils),
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
        for s in produced:
            world.say(s)
    return produced


def risk_threatens(place: Place, risk: Risk) -> bool:
    return risk.mess in place.fragile_to


def select_fix(place: Place, risk: Risk) -> Optional[Fix]:
    for fix_id in sorted(place.offers):
        fix = FIXES[fix_id]
        if risk.mess in fix.fixes:
            return fix
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for risk_id, risk in RISKS.items():
            if risk_threatens(place, risk) and select_fix(place, risk) is not None:
                combos.append((place_id, risk_id))
    return combos


def predict_spoil(world: World) -> dict:
    sim = world.copy()
    visitor = sim.get("visitor")
    visitor.meters["inside"] += 1
    propagate(sim, narrate=False)
    fort = sim.get("fort")
    return {
        "spoiled": fort.meters["spoiled"] >= THRESHOLD,
        "mess": visitor.meters["messy"] >= THRESHOLD,
    }


def introduce(world: World, soldier: Entity, visitor: Entity, place: Place) -> None:
    soldier.memes["duty"] += 1
    visitor.memes["hope"] += 1
    world.say(
        f"Under the table they built {place.scene}, with {place.roof} overhead "
        f"and {place.fragile} tucked safe inside."
    )
    world.say(
        f"{soldier.id} wore a paper hat and stood by the flap like a soldier on parade, "
        f"while {visitor.id} danced nearby, excited for the game they had made."
    )


def approach(world: World, visitor: Entity, risk: Risk) -> None:
    visitor.meters["messy"] += 1
    world.say(
        f"Soon {visitor.id} came hurrying back, {risk.carry_line}. "
        f"The doorway was close, and the fort looked snug and bright."
    )


def warn(world: World, soldier: Entity, visitor: Entity, risk: Risk, place: Place) -> None:
    pred = predict_spoil(world)
    world.facts["predicted_spoil"] = pred["spoiled"]
    soldier.memes["care"] += 1
    world.say(
        f'"Halt one tick!" called {soldier.id}. "Not with {risk.warning_noun}, '
        f'or {place.fragile} may lose its light."'
    )
    world.say(
        f"{soldier.id} was not trying to be grand or cold. "
        f"{risk.threaten_line}, and that was what {soldier.pronoun()} had been told."
    )


def mishear(world: World, soldier: Entity, visitor: Entity, place: Place) -> None:
    if not place.muffled:
        return
    visitor.memes["misunderstanding"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the blanket flap muffled the middle, soft and blue, "
        f"and poor {visitor.id} heard only, \"Not ... you.\""
    )
    world.say(
        f'{visitor.id} stopped short and frowned. "Not me?" {visitor.pronoun()} said. '
        f'"Do you not want me in your fort tonight?"'
    )


def quarrel(world: World, soldier: Entity, visitor: Entity) -> None:
    if visitor.memes["conflict"] < THRESHOLD:
        return
    soldier.memes["worry"] += 1
    world.say(
        f'"That is not fair!" said {soldier.id}, cheeks pink as a rose. '
        f'"I only asked you to stop at the door for a pause."'
    )
    world.say(
        f'"It sounded like you shut me out," said {visitor.id}, voice small but strong. '
        f'For one quick moment, the game felt all wrong.'
    )


def clarify(world: World, soldier: Entity, visitor: Entity, risk: Risk, fix: Fix) -> None:
    visitor.memes["misunderstanding"] = 0.0
    visitor.memes["conflict"] = 0.0
    visitor.memes["hurt"] = 0.0
    soldier.memes["conflict"] = 0.0
    visitor.memes["understanding"] += 1
    soldier.memes["relief"] += 1
    world.say(
        f'Then {soldier.id} took a slow breath and spoke nice and clear: '
        f'"I meant the {risk.label}, not you, my dear."'
    )
    world.say(
        f'"I wanted you with me," said {soldier.pronoun()}, "that part is true. '
        f'Let us {fix.do_line.lower()}, and then I will welcome you."'
    )


def apply_fix(world: World, visitor: Entity, fix: Fix, risk: Risk) -> None:
    visitor.meters["messy"] = 0.0
    visitor.meters["clean"] += 1
    visitor.memes["relief"] += 1
    world.say(
        f"So they {fix.do_line}, quick as a wink and right on cue. "
        f"{fix.result_line}"
    )


def enter_and_share(world: World, soldier: Entity, visitor: Entity, place: Place) -> None:
    visitor.meters["inside"] += 1
    soldier.meters["inside"] += 1
    soldier.memes["joy"] += 1
    visitor.memes["joy"] += 1
    soldier.memes["friendship"] += 1
    visitor.memes["friendship"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Then {soldier.id} lifted the flap and gave a grin so wide. '
        f'"Come in, come in," said {soldier.pronoun()}, "there is room for two inside."'
    )
    if world.get("fort").meters["spoiled"] >= THRESHOLD:
        world.say(
            f"But a little smudge had sneaked in first, a tiny warning mark. "
            f"They cleaned it up together before the fort turned dark."
        )
    else:
        world.say(
            f"They crawled into the fort at last, side by side with pride. "
            f"The paper star stayed neat and dry, and their hurt feelings slipped aside."
        )


def closing_image(world: World, soldier: Entity, visitor: Entity, risk: Risk, place: Place) -> None:
    world.say(
        f"Soon laughter filled {place.label}, gentle, bright, and free. "
        f"The soldier kept the fort safe, and still kept company."
    )
    world.say(
        f"From then on, when words came out in a tangle or a twinge, "
        f"they asked one more clear question before a quarrel reached the hinge."
    )


def tell(
    place: Place,
    risk: Risk,
    fix: Fix,
    *,
    soldier_name: str = "Nora",
    soldier_gender: str = "girl",
    visitor_name: str = "Ben",
    visitor_gender: str = "boy",
    soldier_trait: str = "careful",
    visitor_trait: str = "sensitive",
) -> World:
    world = World(place)
    soldier = world.add(
        Entity(
            id=soldier_name,
            kind="character",
            type=soldier_gender,
            role="soldier",
            traits=[soldier_trait],
            attrs={"pretend_job": "soldier"},
        )
    )
    visitor = world.add(
        Entity(
            id=visitor_name,
            kind="character",
            type=visitor_gender,
            role="visitor",
            traits=[visitor_trait],
            attrs={"friend": soldier_name},
        )
    )
    fort = world.add(
        Entity(
            id="fort",
            kind="thing",
            type="fort",
            label=place.label,
            attrs={"fragile": place.fragile, "muffled": place.muffled},
        )
    )

    # Initialize rule-read state before any propagation.
    soldier.meters["inside"] = 0.0
    visitor.meters["inside"] = 0.0
    visitor.meters["messy"] = 0.0
    fort.meters["spoiled"] = 0.0
    visitor.memes["misunderstanding"] = 0.0
    visitor.memes["conflict"] = 0.0
    visitor.memes["hurt"] = 0.0

    introduce(world, soldier, visitor, place)
    world.para()
    approach(world, visitor, risk)
    warn(world, soldier, visitor, risk, place)
    mishear(world, soldier, visitor, place)
    quarrel(world, soldier, visitor)
    world.para()
    clarify(world, soldier, visitor, risk, fix)
    apply_fix(world, visitor, fix, risk)
    enter_and_share(world, soldier, visitor, place)
    closing_image(world, soldier, visitor, risk, place)

    world.facts.update(
        soldier=soldier,
        visitor=visitor,
        fort=fort,
        place=place,
        risk=risk,
        fix=fix,
        misunderstanding=place.muffled,
        conflict_happened=True,
        resolved=visitor.meters["clean"] >= THRESHOLD and visitor.meters["inside"] >= THRESHOLD,
        protected=fort.meters["spoiled"] < THRESHOLD,
    )
    return world


PLACES = {
    "blanket_fort": Place(
        id="blanket_fort",
        label="the blanket fort",
        scene="a moonlit blanket fort",
        roof="a quilt roof",
        fragile="the quilt floor and paper moon map",
        fragile_to={"muddy", "wet"},
        offers={"doormat", "peg"},
        muffled=True,
        tags={"fort", "blanket"},
    ),
    "cardboard_castle": Place(
        id="cardboard_castle",
        label="the cardboard castle",
        scene="a cardboard castle",
        roof="a crinkly cardboard arch",
        fragile="the painted walls and paper flags",
        fragile_to={"muddy", "wet", "sticky"},
        offers={"doormat", "peg", "sink"},
        muffled=True,
        tags={"castle", "cardboard"},
    ),
    "sofa_tunnel": Place(
        id="sofa_tunnel",
        label="the sofa tunnel",
        scene="a sofa tunnel",
        roof="a patchwork sheet roof",
        fragile="the story books and cushion road",
        fragile_to={"muddy", "sticky"},
        offers={"doormat", "sink"},
        muffled=True,
        tags={"sofa", "fort"},
    ),
}

RISKS = {
    "muddy_boots": Risk(
        id="muddy_boots",
        label="muddy boots",
        mess="muddy",
        carry_line="with muddy boots clopping and little brown dots on the laces",
        warning_noun="those muddy boots",
        threaten_line="Mud would stamp onto the soft floor and smudge the waiting places",
        cleanup_prompt="wipe the boots on the mat",
        tags={"mud", "boots"},
    ),
    "drippy_cape": Risk(
        id="drippy_cape",
        label="dripping rain cape",
        mess="wet",
        carry_line="with a dripping rain cape that still held shiny drops from outside",
        warning_noun="that dripping cape",
        threaten_line="The drops could blur the paper things and make the corners curl and slide",
        cleanup_prompt="hang the cape to drip on the peg",
        tags={"rain", "wet"},
    ),
    "sticky_hands": Risk(
        id="sticky_hands",
        label="sticky hands",
        mess="sticky",
        carry_line="with sticky hands from peach jam and a smile as round as the sun",
        warning_noun="those sticky hands",
        threaten_line="Sticky fingers would cling to the walls and pull at the careful fun",
        cleanup_prompt="wash the hands at the sink",
        tags={"sticky", "hands"},
    ),
}

FIXES = {
    "doormat": Fix(
        id="doormat",
        label="the doormat",
        fixes={"muddy"},
        do_line="wiped the boots on the doormat",
        result_line="The brown dots stayed on the mat instead of marching into the fort.",
        qa_line="wiped the muddy boots clean on the doormat",
        tags={"doormat", "clean"},
    ),
    "peg": Fix(
        id="peg",
        label="the peg",
        fixes={"wet"},
        do_line="hung the dripping cape on the peg",
        result_line="The drops slid into a little puddle below, and the paper things stayed dry.",
        qa_line="hung the dripping cape on a peg so the water stayed outside the fort",
        tags={"peg", "dry"},
    ),
    "sink": Fix(
        id="sink",
        label="the sink",
        fixes={"sticky"},
        do_line="washed the sticky hands at the sink",
        result_line="The jam swirled away with the bubbles, and the walls were safe from smears.",
        qa_line="washed the sticky hands clean at the sink",
        tags={"sink", "wash"},
    ),
}


GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella", "Ruby", "Ivy", "Maya", "June"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Finn", "Owen", "Eli", "Theo", "Jack", "Noah"]
SOLDIER_TRAITS = ["careful", "steady", "kind", "brave"]
VISITOR_TRAITS = ["sensitive", "hopeful", "eager", "warm"]


@dataclass
class StoryParams:
    place: str
    risk: str
    soldier_name: str
    soldier_gender: str
    visitor_name: str
    visitor_gender: str
    soldier_trait: str
    visitor_trait: str
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
        place="blanket_fort",
        risk="muddy_boots",
        soldier_name="Nora",
        soldier_gender="girl",
        visitor_name="Ben",
        visitor_gender="boy",
        soldier_trait="careful",
        visitor_trait="sensitive",
    ),
    StoryParams(
        place="cardboard_castle",
        risk="drippy_cape",
        soldier_name="Max",
        soldier_gender="boy",
        visitor_name="Lily",
        visitor_gender="girl",
        soldier_trait="steady",
        visitor_trait="hopeful",
    ),
    StoryParams(
        place="cardboard_castle",
        risk="sticky_hands",
        soldier_name="Ava",
        soldier_gender="girl",
        visitor_name="Theo",
        visitor_gender="boy",
        soldier_trait="kind",
        visitor_trait="eager",
    ),
    StoryParams(
        place="sofa_tunnel",
        risk="muddy_boots",
        soldier_name="Leo",
        soldier_gender="boy",
        visitor_name="Maya",
        visitor_gender="girl",
        soldier_trait="brave",
        visitor_trait="warm",
    ),
]


KNOWLEDGE = {
    "mud": [
        (
            "Why can muddy boots make a mess indoors?",
            "Mud sticks to the bottoms of boots and comes off when you walk. That can leave dirty prints on rugs, floors, and blankets.",
        )
    ],
    "wet": [
        (
            "Why should wet clothes stay away from paper?",
            "Paper gets soft and wrinkly when it is wet. Water can blur drawings and make paper tear more easily.",
        )
    ],
    "sticky": [
        (
            "Why are sticky hands hard on toys and paper things?",
            "Sticky hands can grab too hard and leave smears behind. They also make dust and bits of paper cling where they should not.",
        )
    ],
    "dialogue": [
        (
            "What should you do if you think someone said something unkind?",
            "You can ask them to say it again and tell them what you heard. Clear dialogue helps fix misunderstandings before feelings grow bigger.",
        )
    ],
    "soldier": [
        (
            "What is a soldier in a pretend game?",
            "In a pretend game, a soldier is someone guarding a place or following a mission. It does not mean being mean; it can mean being careful and brave.",
        )
    ],
    "clean": [
        (
            "Why is it helpful to clean up before joining a game?",
            "Cleaning up protects the things everyone worked hard to build. It lets the game keep going without damage or upset.",
        )
    ],
}
KNOWLEDGE_ORDER = ["soldier", "mud", "wet", "sticky", "dialogue", "clean"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    soldier = f["soldier"]
    visitor = f["visitor"]
    place = f["place"]
    risk = f["risk"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the word "soldier" and features a misunderstanding, dialogue, and conflict.',
        f"Tell a rhyming story where {soldier.id} pretends to be a soldier guarding {place.label}, and {visitor.id} wrongly thinks a warning about {risk.label} is a personal rejection.",
        f"Write a gentle conflict story in rhyme where two children clear up hurt feelings by talking plainly and fixing the real problem first.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    soldier = f["soldier"]
    visitor = f["visitor"]
    place = f["place"]
    risk = f["risk"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {soldier.id}, who was pretending to be a soldier guarding {place.label}, and {visitor.id}, who wanted to come in and play. They cared about each other, but they got tangled up in a misunderstanding.",
        ),
        (
            f"Why did {soldier.id} stop {visitor.id} at the door?",
            f"{soldier.id} stopped {visitor.id} because of the {risk.label}, not because of who {visitor.pronoun('subject')} was. {risk.threaten_line}, so {soldier.pronoun('subject')} was trying to protect the fort.",
        ),
        (
            f"What was the misunderstanding?",
            f"The doorway muffled the warning, so {visitor.id} heard it as if {soldier.id} was saying \"not you.\" That hurt {visitor.pronoun('object')} because {visitor.pronoun('subject')} thought the friendship was being shut out, when really only the {risk.label} had to stay out for a moment.",
        ),
        (
            "How did they solve the conflict?",
            f"They solved it by talking clearly and then fixing the real problem. {soldier.id} explained, \"I meant the {risk.label}, not you,\" and together they {fix.qa_line}.",
        ),
        (
            "How did the story end?",
            f"They went into {place.label} together and the fragile things inside stayed safe. The ending shows that clear dialogue and a small cleanup can save both a game and a friendship.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"soldier", "dialogue", "clean"}
    risk = f["risk"]
    if risk.mess == "muddy":
        tags.add("mud")
    elif risk.mess == "wet":
        tags.add("wet")
    elif risk.mess == "sticky":
        tags.add("sticky")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, risk: Risk) -> str:
    if not risk_threatens(place, risk):
        return (
            f"(No story: {risk.label} would not reasonably damage {place.fragile}, "
            f"so the soldier would have no honest reason to stop the visitor.)"
        )
    if select_fix(place, risk) is None:
        return (
            f"(No story: {place.label} has no sensible cleanup or holding fix for {risk.label}, "
            f"so the conflict could not resolve fairly.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
threatens(P,R) :- place(P), risk(R), fragile_to(P,M), mess_of(R,M).
can_fix(P,R)   :- place(P), risk(R), offers(P,F), fix(F), fixes(F,M), mess_of(R,M).
valid(P,R)     :- threatens(P,R), can_fix(P,R).

misunderstanding(P) :- place(P), muffled(P).
outcome(P,R,resolved) :- valid(P,R), misunderstanding(P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.muffled:
            lines.append(asp.fact("muffled", place_id))
        for mess in sorted(place.fragile_to):
            lines.append(asp.fact("fragile_to", place_id, mess))
        for fix_id in sorted(place.offers):
            lines.append(asp.fact("offers", place_id, fix_id))
    for risk_id, risk in RISKS.items():
        lines.append(asp.fact("risk", risk_id))
        lines.append(asp.fact("mess_of", risk_id, risk.mess))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for mess in sorted(fix.fixes):
            lines.append(asp.fact("fixes", fix_id, mess))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_risk", params.risk),
            "selected_outcome(X) :- chosen_place(P), chosen_risk(R), outcome(P,R,X).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show selected_outcome/1."))
    atoms = asp.atoms(model, "selected_outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    risk = RISKS[params.risk]
    return "resolved" if risk_threatens(place, risk) and select_fix(place, risk) and place.muffled else "?"


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
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {s}.")
            break

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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a pretend soldier, a misunderstanding, and a clear-talking fix."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--risk", choices=RISKS)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.risk:
        place = PLACES[args.place]
        risk = RISKS[args.risk]
        if not (risk_threatens(place, risk) and select_fix(place, risk) is not None):
            raise StoryError(explain_rejection(place, risk))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.risk is None or combo[1] == args.risk)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, risk_id = rng.choice(sorted(combos))
    soldier_gender = rng.choice(["girl", "boy"])
    visitor_gender = rng.choice(["girl", "boy"])
    soldier_name = _pick_name(rng, soldier_gender)
    visitor_name = _pick_name(rng, visitor_gender, avoid=soldier_name)
    return StoryParams(
        place=place_id,
        risk=risk_id,
        soldier_name=soldier_name,
        soldier_gender=soldier_gender,
        visitor_name=visitor_name,
        visitor_gender=visitor_gender,
        soldier_trait=rng.choice(SOLDIER_TRAITS),
        visitor_trait=rng.choice(VISITOR_TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.risk not in RISKS:
        raise StoryError(f"(Unknown risk: {params.risk})")

    place = PLACES[params.place]
    risk = RISKS[params.risk]
    fix = select_fix(place, risk)
    if not risk_threatens(place, risk) or fix is None:
        raise StoryError(explain_rejection(place, risk))

    world = tell(
        place=place,
        risk=risk,
        fix=fix,
        soldier_name=params.soldier_name,
        soldier_gender=params.soldier_gender,
        visitor_name=params.visitor_name,
        visitor_gender=params.visitor_gender,
        soldier_trait=params.soldier_trait,
        visitor_trait=params.visitor_trait,
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
        print(asp_program("", "#show valid/2.\n#show outcome/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, risk) combos:\n")
        for place_id, risk_id in combos:
            print(f"  {place_id:17} {risk_id}")
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
            header = f"### {p.soldier_name} the soldier at {p.place} ({p.risk})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
