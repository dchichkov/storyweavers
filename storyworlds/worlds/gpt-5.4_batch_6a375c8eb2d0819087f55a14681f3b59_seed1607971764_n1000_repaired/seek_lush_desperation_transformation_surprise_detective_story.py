#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/seek_lush_desperation_transformation_surprise_detective_story.py
================================================================================================

A standalone storyworld for a tiny child-facing detective story domain:
a child detective must seek a missing growing prize in a lush place, follows
clues, feels a moment of desperation, and discovers a gentle transformation
with a surprise ending.

Core shape
----------
A child and a helper care about a special plant bud. The bud seems to be gone.
The detective seeks clues in a lush setting. Different clue patterns support
different explanations:

* hidden       -> the bud was tucked behind leaves
* moved        -> a helper creature carried the pot
* transformed  -> the missing bud has turned into a flower

The world prefers transformations and concrete clues over arbitrary mystery.
The prose is state-driven: clue finding updates suspicion, desperation rises
after failed search, then the final reveal resolves the case.

Run it
------
    python storyworlds/worlds/gpt-5.4/seek_lush_desperation_transformation_surprise_detective_story.py
    python storyworlds/worlds/gpt-5.4/seek_lush_desperation_transformation_surprise_detective_story.py --place greenhouse --case transformed
    python storyworlds/worlds/gpt-5.4/seek_lush_desperation_transformation_surprise_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/seek_lush_desperation_transformation_surprise_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/seek_lush_desperation_transformation_surprise_detective_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    movable: bool = False
    fragrant: bool = False
    # physical and emotional dimensions
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.label or self.type
        )
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    lush_text: str
    hiding_spots: list[str]
    supports: set[str] = field(default_factory=set)
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
class MissingThing:
    id: str
    label: str
    phrase: str
    start_state: str
    transformed_label: str
    transformed_phrase: str
    scent: str
    attracts: str
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
class CaseType:
    id: str
    explanation: str
    reveal: str
    clue_power: int
    needs_transform: bool = False
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
class ClueSet:
    id: str
    clue_lines: list[str]
    supports: set[str]
    desperation_hit: int
    sense: int
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
class Helper:
    id: str
    label: str
    role_text: str
    method_text: str
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
        self.history: list[str] = []

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
        clone.history = list(self.history)
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


def _r_desperation(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    clues = world.facts.get("clues_found", 0)
    searches = world.facts.get("search_steps", 0)
    if searches >= 2 and clues <= 1:
        sig = ("desperation", searches, clues)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["desperation"] += 1
            out.append("__desperation__")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    thing = world.get("thing")
    if world.facts.get("case") == "transformed" and thing.meters["bloom_ready"] >= THRESHOLD:
        sig = ("transformation", thing.id)
        if sig not in world.fired:
            world.fired.add(sig)
            thing.attrs["state"] = "flower"
            thing.meters["flowered"] += 1
            out.append("__transformation__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="desperation", tag="emotional", apply=_r_desperation),
    Rule(name="transformation", tag="physical", apply=_r_transformation),
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
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(place_id: str, thing_id: str, case_id: str, clues_id: str) -> bool:
    if place_id not in PLACES or thing_id not in THINGS or case_id not in CASES or clues_id not in CLUES:
        return False
    place = PLACES[place_id]
    case = CASES[case_id]
    clues = CLUES[clues_id]
    if case_id not in place.supports:
        return False
    if clues.sense < SENSE_MIN:
        return False
    if case_id not in clues.supports:
        return False
    if case.needs_transform and "flower" not in THINGS[thing_id].transformed_label:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for thing_id in sorted(THINGS):
            for case_id in sorted(CASES):
                for clues_id in sorted(CLUES):
                    if valid_combo(place_id, thing_id, case_id, clues_id):
                        combos.append((place_id, thing_id, case_id, clues_id))
    return combos


def sensible_clues() -> list[ClueSet]:
    return [cl for cl in CLUES.values() if cl.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    if params.case == "transformed":
        return "transformation"
    if params.case == "moved":
        return "found_elsewhere"
    return "found_hidden"


def explain_rejection(place_id: str, thing_id: str, case_id: str, clues_id: str) -> str:
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    if thing_id not in THINGS:
        return f"(No story: unknown missing thing '{thing_id}'.)"
    if case_id not in CASES:
        return f"(No story: unknown case '{case_id}'.)"
    if clues_id not in CLUES:
        return f"(No story: unknown clues '{clues_id}'.)"
    place = PLACES[place_id]
    case = CASES[case_id]
    clues = CLUES[clues_id]
    if case_id not in place.supports:
        return (
            f"(No story: {place.label} does not support the case '{case_id}'. "
            f"The final reveal would not fit that place.)"
        )
    if clues.sense < SENSE_MIN:
        return (
            f"(No story: clue set '{clues_id}' is too weak for a fair detective story "
            f"(sense={clues.sense} < {SENSE_MIN}).)"
        )
    if case_id not in clues.supports:
        return (
            f"(No story: clue set '{clues_id}' does not honestly point toward the case "
            f"'{case_id}'. The mystery would feel random instead of solvable.)"
        )
    if case.needs_transform and "flower" not in THINGS[thing_id].transformed_label:
        return (
            f"(No story: '{thing_id}' does not transform into a flower-like ending, "
            f"so the transformation case would not read clearly.)"
        )
    return "(No story: this combination is not reasonable.)"


def introduce(world: World, detective: Entity, helper_ent: Entity, place: Place, thing: MissingThing) -> None:
    detective.memes["care"] += 1
    helper_ent.memes["care"] += 1
    world.say(
        f"{detective.id} liked to call {detective.pronoun('possessive')} small notebook a detective book. "
        f"That morning, {detective.id} and {helper_ent.id} stepped into {place.label}, "
        f"where {place.lush_text}."
    )
    world.say(
        f"On the middle bench sat {thing.phrase}. {detective.id} had promised to watch it every day "
        f"until it changed."
    )


def vanish(world: World, detective: Entity, helper_ent: Entity, thing: MissingThing) -> None:
    detective.memes["alert"] += 1
    world.facts["search_steps"] = 0
    world.say(
        f"But when {detective.id} looked again, the {thing.label} seemed gone."
    )
    world.say(
        f'"A case!" whispered {detective.id}. {helper_ent.id} squeezed close and looked around with wide eyes.'
    )


def seek_setup(world: World, detective: Entity, helper_ent: Entity, helper_cfg: Helper, thing: MissingThing) -> None:
    world.say(
        f'"We must seek every clue," said {detective.id}. "{helper_cfg.method_text}"'
    )
    world.say(
        f'{helper_ent.id} nodded. For one moment, even the sweet smell of {thing.scent} could not calm the mystery.'
    )


def search_step(world: World, detective: Entity, helper_ent: Entity, place: Place, clues: ClueSet) -> None:
    world.facts["search_steps"] += 1
    idx = world.facts["search_steps"] - 1
    line = clues.clue_lines[min(idx, len(clues.clue_lines) - 1)]
    world.say(line)
    world.facts["clues_found"] += 1
    detective.memes["focus"] += 1
    helper_ent.memes["hope"] += 1
    propagate(world, narrate=False)


def false_turn(world: World, detective: Entity, place: Place) -> None:
    detective.memes["uncertainty"] += 1
    world.facts["search_steps"] += 1
    world.say(
        f"They checked {place.hiding_spots[-1]} and found only shadows and damp soil. "
        f"For the first time, the case felt bigger than {detective.id}'s notebook."
    )
    propagate(world, narrate=False)


def desperation_beat(world: World, detective: Entity) -> None:
    if detective.memes["desperation"] >= THRESHOLD:
        world.say(
            f"{detective.id} felt a pinch of desperation. If the little plant was truly lost, "
            f"the whole bright morning might end in tears."
        )


def reveal_hidden(world: World, detective: Entity, helper_ent: Entity, place: Place, thing: MissingThing, case: CaseType) -> None:
    thing_ent = world.get("thing")
    thing_ent.attrs["state"] = "found"
    thing_ent.meters["found"] += 1
    detective.memes["relief"] += 1
    helper_ent.memes["joy"] += 1
    world.say(
        f"Then {helper_ent.id} pointed behind a curtain of leaves. There was the {thing.label}, "
        f"tucked safely where the vines had leaned over it."
    )
    world.say(case.reveal)


def reveal_moved(
    world: World,
    detective: Entity,
    helper_ent: Entity,
    helper_cfg: Helper,
    thing: MissingThing,
    case: CaseType,
) -> None:
    thing_ent = world.get("thing")
    mover = world.get("mover")
    thing_ent.attrs["state"] = "found"
    thing_ent.meters["found"] += 1
    mover.meters["moved"] += 1
    detective.memes["relief"] += 1
    helper_ent.memes["joy"] += 1
    world.say(
        f"A soft rustle came from under the watering table. Out waddled {mover.label}, "
        f"nudging the little pot inch by inch."
    )
    world.say(case.reveal)
    world.say(
        f'{detective.id} laughed in surprise. "Our suspect was only trying to reach the smell of {thing.attracts}," '
        f"{detective.pronoun()} said."
    )


def reveal_transformed(
    world: World,
    detective: Entity,
    helper_ent: Entity,
    thing: MissingThing,
    case: CaseType,
) -> None:
    thing_ent = world.get("thing")
    thing_ent.meters["bloom_ready"] += 1
    propagate(world, narrate=False)
    detective.memes["relief"] += 1
    detective.memes["wonder"] += 1
    helper_ent.memes["joy"] += 1
    if thing_ent.attrs.get("state") != "flower":
        raise StoryError("(Internal story error: transformation reveal failed to bloom.)")
    world.say(
        f"At last {detective.id} tipped the pot toward the light. The missing {thing.label} had not vanished at all."
    )
    world.say(
        f"It had opened into {thing.transformed_phrase}, so new and bright that neither child knew it at first."
    )
    world.say(case.reveal)


def resolution(
    world: World,
    detective: Entity,
    helper_ent: Entity,
    helper_cfg: Helper,
    thing: MissingThing,
    case: CaseType,
) -> None:
    detective.memes["trust"] += 1
    helper_ent.memes["trust"] += 1
    detective.memes["lesson"] += 1
    world.say(
        f'"Case closed," said {detective.id}, pressing a neat line in the detective book. '
        f'"The answer was fair after all."'
    )
    if case.id == "transformed":
        world.say(
            f"{helper_ent.id} stroked the rim of the pot and smiled. The best surprise was that waiting had changed the mystery itself."
        )
    elif case.id == "moved":
        world.say(
            f"{helper_cfg.role_text.capitalize()} or not, {helper_ent.id} could see the funny truth now: not every suspect means harm."
        )
    else:
        world.say(
            f"The leaves no longer looked sneaky. They looked kind, as if the whole place had hidden the little plant just long enough for a detective to learn patience."
        )
def tell(
    thing: Thing,
    case: Case,
    clues: Clues,
    helper_cfg: Helper,
    detective_name: str,
    detective_type: DetectiveType,
    helper_name: str,
    helper_type: HelperType,
    grownup_type: GrownupType,
    place=None,
) -> World:
    world = World()
    world.facts["search_steps"] = 0
    world.facts["clues_found"] = 0
    world.facts["case"] = case.id

    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_type,
            role="detective",
            label=detective_name,
            traits=["careful", "curious"],
            attrs={"notebook": "detective book"},
            tags={"detective"},
        )
    )
    helper_ent = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            role="helper",
            label=helper_name,
            traits=["gentle", "observant"],
            attrs={"helper_role": helper_cfg.role_text},
            tags=set(helper_cfg.tags),
        )
    )
    grownup = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=grownup_type,
            role="grownup",
            label="the grown-up",
            traits=["patient"],
            tags={"grownup"},
        )
    )
    thing_ent = world.add(
        Entity(
            id="thing",
            type="plant",
            label=thing.label,
            role="missing_thing",
            movable=True,
            fragrant=True,
            attrs={"state": thing.start_state},
            tags=set(thing.tags),
        )
    )
    mover = world.add(
        Entity(
            id="mover",
            type="animal",
            label="a tiny tortoise",
            role="mover",
            movable=True,
            attrs={"reason": thing.attracts},
            tags={"animal", "tortoise"},
        )
    )

    introduce(world, detective, helper_ent, place, thing)
    world.para()
    vanish(world, detective, helper_ent, thing)
    seek_setup(world, detective, helper_ent, helper_cfg, thing)

    world.para()
    search_step(world, detective, helper_ent, place, clues)
    if clues.desperation_hit == 2:
        false_turn(world, detective, place)
    search_step(world, detective, helper_ent, place, clues)
    desperation_beat(world, detective)

    world.para()
    if case.id == "hidden":
        reveal_hidden(world, detective, helper_ent, place, thing, case)
    elif case.id == "moved":
        reveal_moved(world, detective, helper_ent, helper_cfg, thing, case)
    elif case.id == "transformed":
        reveal_transformed(world, detective, helper_ent, thing, case)
    else:
        raise StoryError(f"(No story: unsupported case '{case.id}'.)")

    world.para()
    resolution(world, detective, helper_ent, helper_cfg, thing, case)

    world.facts.update(
        detective=detective,
        helper=helper_ent,
        grownup=grownup,
        thing_cfg=thing,
        case_cfg=case,
        clues_cfg=clues,
        helper_cfg=helper_cfg,
        place=place,
        thing=thing_ent,
        mover=mover,
        outcome=outcome_of(
            StoryParams(
                place=place.id,
                thing=thing.id,
                case=case.id,
                clues=clues.id,
                helper=helper_cfg.id,
                detective_name=detective_name,
                detective_type=detective_type,
                helper_name=helper_name,
                helper_type=helper_type,
                grownup_type=grownup_type,
                seed=None,
            )
        ),
        transformed=thing_ent.meters["flowered"] >= THRESHOLD,
        desperate=detective.memes["desperation"] >= THRESHOLD,
        surprise=True,
    )
    return world
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


PLACES = {
    "greenhouse": Place(
        id="greenhouse",
        label="the greenhouse",
        lush_text="lush vines climbed the glass, fern fronds brushed the benches, and drops of water shone like tiny mirrors",
        hiding_spots=["the mossy shelf", "the tall fern stand", "the cracked watering can", "the darkest corner by the seed trays"],
        supports={"hidden", "moved", "transformed"},
        tags={"greenhouse", "plants", "lush"},
    ),
    "winter_garden": Place(
        id="winter_garden",
        label="the winter garden",
        lush_text="lush leaves crowded the warm room, and broad flowers leaned over the stone path as if they were listening",
        hiding_spots=["the stone bench", "the orange tree tub", "the wicker basket", "the damp archway"],
        supports={"hidden", "transformed"},
        tags={"garden", "plants", "lush"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the courtyard",
        lush_text="lush ivy wrapped the brick walls, and rows of pots sat in soft puddles after the watering",
        hiding_spots=["the long bench", "the rain barrel", "the stack of empty pots", "the gate corner"],
        supports={"hidden", "moved"},
        tags={"courtyard", "plants", "lush"},
    ),
}

THINGS = {
    "bud": MissingThing(
        id="bud",
        label="bud",
        phrase="a shy silver bud in a blue pot",
        start_state="bud",
        transformed_label="flower",
        transformed_phrase="a silver flower with five shining petals",
        scent="mint and wet soil",
        attracts="cool leaves",
        tags={"bud", "flower", "plant"},
    ),
    "rosebud": MissingThing(
        id="rosebud",
        label="rosebud",
        phrase="a small rosebud in a painted clay pot",
        start_state="bud",
        transformed_label="flower",
        transformed_phrase="a rose opening wide like a tiny red lantern",
        scent="sweet petals and dark earth",
        attracts="sweet petals",
        tags={"rose", "flower", "plant"},
    ),
}

CASES = {
    "hidden": CaseType(
        id="hidden",
        explanation="The missing thing was hidden by overgrown leaves.",
        reveal="It was only hidden, and the children had mistaken a blanket of leaves for a theft.",
        clue_power=2,
        needs_transform=False,
        tags={"hidden", "surprise"},
    ),
    "moved": CaseType(
        id="moved",
        explanation="A harmless creature moved the pot.",
        reveal="The pot had not been stolen at all. A tiny tortoise had pushed it toward the wet shade.",
        clue_power=3,
        needs_transform=False,
        tags={"moved", "animal", "surprise"},
    ),
    "transformed": CaseType(
        id="transformed",
        explanation="The bud changed so much that the children did not recognize it.",
        reveal="The mystery solved itself with a transformation: the lost bud had become a flower.",
        clue_power=3,
        needs_transform=True,
        tags={"transformation", "flower", "surprise"},
    ),
}

CLUES = {
    "leaf_trail": ClueSet(
        id="leaf_trail",
        clue_lines=[
            "First they found a bent line of leaves leading away from the bench.",
            "Then they noticed a clean round mark in the wet dust where the pot had rested before.",
        ],
        supports={"hidden", "moved"},
        desperation_hit=2,
        sense=3,
        tags={"leaves", "trail"},
    ),
    "petal_light": ClueSet(
        id="petal_light",
        clue_lines=[
            "First a patch of bright color flashed from the side of the pot, but it did not look like the bud they remembered.",
            "Then a sweet new smell drifted up, richer than before, as if the plant had changed overnight.",
        ],
        supports={"transformed"},
        desperation_hit=1,
        sense=3,
        tags={"petal", "scent"},
    ),
    "mixed_clues": ClueSet(
        id="mixed_clues",
        clue_lines=[
            "First they found damp soil crumbs under the bench and a leaf caught on the pot stand.",
            "Then they saw something bright among the leaves, though neither child could tell what it meant yet.",
        ],
        supports={"hidden", "moved", "transformed"},
        desperation_hit=2,
        sense=2,
        tags={"soil", "leaf", "bright"},
    ),
    "guessing": ClueSet(
        id="guessing",
        clue_lines=[
            "They stared around and tried to guess with no real clue at all.",
            "The room stayed quiet, and guessing did not help.",
        ],
        supports={"hidden"},
        desperation_hit=1,
        sense=1,
        tags={"weak"},
    ),
}

HELPERS = {
    "whisperer": Helper(
        id="whisperer",
        label="plant whisperer",
        role_text="plant whisperer",
        method_text="Let's walk slowly and look where small things like shade",
        tags={"helper", "plants"},
    ),
    "mapmaker": Helper(
        id="mapmaker",
        label="map maker",
        role_text="map maker",
        method_text="Let's mark every clue and not skip a single bench",
        tags={"helper", "map"},
    ),
    "sniffer": Helper(
        id="sniffer",
        label="sniffer",
        role_text="sniffer",
        method_text="Let's follow the smell before we follow our guesses",
        tags={"helper", "scent"},
    ),
}

GIRL_NAMES = ["Nora", "Lina", "Mia", "Ava", "Ruby", "Ella", "June", "Ivy"]
BOY_NAMES = ["Ben", "Theo", "Max", "Sam", "Leo", "Eli", "Noah", "Finn"]


KNOWLEDGE = {
    "greenhouse": [
        (
            "What is a greenhouse?",
            "A greenhouse is a warm glass house where plants can grow. The walls let in light and help hold the warmth inside.",
        )
    ],
    "garden": [
        (
            "Why do plants like warm, bright places?",
            "Plants use light to grow, and many of them grow well when the air stays warm. Warmth and light help buds open and leaves stay healthy.",
        )
    ],
    "bud": [
        (
            "What is a bud?",
            "A bud is the small closed beginning of a flower or leaf. If it keeps growing, it can open into something bigger.",
        )
    ],
    "flower": [
        (
            "What does it mean when a bud turns into a flower?",
            "It means the plant changed as it grew. That kind of change is a transformation.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and uses them to figure out what happened. Good detectives do not just guess; they pay attention.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand something. One clue may not solve a mystery, but several clues together can help.",
        )
    ],
    "tortoise": [
        (
            "What is a tortoise?",
            "A tortoise is a slow animal with a hard shell. It walks on land and can nudge things with its nose or shell.",
        )
    ],
    "surprise": [
        (
            "What is a surprise ending?",
            "A surprise ending gives you an answer you did not expect at first. In a fair story, the clues still fit the answer when you look back.",
        )
    ],
}

KNOWLEDGE_ORDER = ["greenhouse", "garden", "bud", "flower", "detective", "clue", "tortoise", "surprise"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper_ent = f["helper"]
    place = f["place"]
    case = f["case_cfg"]
    thing = f["thing_cfg"]
    outcome = f["outcome"]
    if outcome == "transformation":
        return [
            f'Write a gentle detective story for a 3-to-5-year-old where a child must seek a missing plant in {place.label}. Include the words "seek", "lush", and "desperation".',
            f"Tell a mystery about {detective.id} and {helper_ent.id} searching for a missing {thing.label}, only to discover a transformation with a surprise ending.",
            f"Write a child-facing detective story where a lush place, careful clue-finding, and one moment of desperation lead to the discovery that the missing thing has changed shape.",
        ]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old where a child must seek a missing plant in {place.label}. Include the words "seek", "lush", and "desperation".',
        f"Tell a small mystery about {detective.id} and {helper_ent.id} following clues through a lush garden until the surprise reveal explains where the {thing.label} went.",
        f"Write a child-facing detective story with clear clues, a worried detective, and a fair surprise ending that solves the case without anyone being mean.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper_ent = f["helper"]
    thing = f["thing_cfg"]
    place = f["place"]
    case = f["case_cfg"]
    clues = f["clues_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, and {helper_ent.id}, the helper on the case. Together they searched in {place.label} for a missing {thing.label}.",
        ),
        (
            "What made the case begin?",
            f"The case began when the {thing.label} seemed to be gone from its place on the bench. That sudden change made {detective.id} treat the morning like a mystery.",
        ),
        (
            f"How did {detective.id} try to solve the mystery?",
            f"{detective.id} chose to seek clues instead of making a wild guess. {detective.pronoun().capitalize()} and {helper_ent.id} searched slowly, using what they saw and smelled to guide them.",
        ),
    ]
    if f.get("desperate"):
        qa.append(
            (
                f"Why did {detective.id} feel desperation for a moment?",
                f"{detective.id} felt desperation after the search grew harder and the answer still was not clear. The empty places and false turn made it seem as if the little plant might truly be lost.",
            )
        )
    qa.append(
        (
            "What clues did they find?",
            f"They found clues like {clues.clue_lines[0].rstrip('.').lower()} and {clues.clue_lines[1].rstrip('.').lower()}. Those clues mattered because they pointed toward the true answer instead of a random guess.",
        )
    )
    if outcome == "transformation":
        qa.append(
            (
                "What was the surprise ending?",
                f"The surprise was that nothing had really been stolen or taken away. The missing {thing.label} had transformed into {thing.transformed_phrase}, so the children did not recognize it at first.",
            )
        )
    elif outcome == "found_elsewhere":
        qa.append(
            (
                "Where had the missing plant gone?",
                f"It had been moved by a tiny tortoise into a shadier place. That was surprising, but the clues about movement made the answer fair.",
            )
        )
    else:
        qa.append(
            (
                "Where was the missing plant?",
                f"It was hidden behind leaves, not gone forever. The lush plants covered it so well that the children thought it had disappeared.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with relief and a closed case. The answer changed the children from worried searchers into smiling detectives because they had learned to trust clues and be patient.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"detective", "clue", "surprise"}
    place = f["place"]
    case = f["case_cfg"]
    thing = f["thing_cfg"]
    tags |= set(place.tags)
    tags |= set(case.tags)
    tags |= set(thing.tags)
    if case.id == "moved":
        tags.add("tortoise")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: search_steps={world.facts.get('search_steps')} clues_found={world.facts.get('clues_found')} case={world.facts.get('case')}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    place: str
    thing: str
    case: str
    clues: str
    helper: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    grownup_type: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="greenhouse",
        thing="bud",
        case="transformed",
        clues="petal_light",
        helper="sniffer",
        detective_name="Nora",
        detective_type="girl",
        helper_name="Ben",
        helper_type="boy",
        grownup_type="aunt",
        seed=101,
    ),
    StoryParams(
        place="courtyard",
        thing="rosebud",
        case="moved",
        clues="leaf_trail",
        helper="mapmaker",
        detective_name="Theo",
        detective_type="boy",
        helper_name="Ruby",
        helper_type="girl",
        grownup_type="uncle",
        seed=102,
    ),
    StoryParams(
        place="winter_garden",
        thing="bud",
        case="hidden",
        clues="mixed_clues",
        helper="whisperer",
        detective_name="Ivy",
        detective_type="girl",
        helper_name="Max",
        helper_type="boy",
        grownup_type="aunt",
        seed=103,
    ),
]


ASP_RULES = r"""
sensible_clue(C) :- clue_set(C), clue_sense(C,S), sense_min(M), S >= M.
supports_place(P, K) :- place_supports(P, K).
supports_clue(C, K) :- clue_supports(C, K).

valid(P, T, K, C) :- place(P), thing(T), case(K), clue_set(C),
                     supports_place(P, K),
                     sensible_clue(C),
                     supports_clue(C, K),
                     not bad_transform(T, K).

bad_transform(T, transformed) :- thing(T), transformed_label(T, L), not flower_word(L).
flower_word("flower").

outcome(transformation) :- chosen_case(transformed).
outcome(found_elsewhere) :- chosen_case(moved).
outcome(found_hidden) :- chosen_case(hidden).

#show valid/4.
#show sensible_clue/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for case_id in sorted(place.supports):
            lines.append(asp.fact("place_supports", place_id, case_id))
    for thing_id, thing in THINGS.items():
        lines.append(asp.fact("thing", thing_id))
        lines.append(asp.fact("transformed_label", thing_id, thing.transformed_label))
    for case_id in CASES:
        lines.append(asp.fact("case", case_id))
    for clues_id, clues in CLUES.items():
        lines.append(asp.fact("clue_set", clues_id))
        lines.append(asp.fact("clue_sense", clues_id, clues.sense))
        for case_id in sorted(clues.supports):
            lines.append(asp.fact("clue_supports", clues_id, case_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_clues() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(c for (c,) in asp.atoms(model, "sensible_clue"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_case", params.case)
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child detective seeks a missing plant in a lush place."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--clues", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--grownup-type", choices=["aunt", "uncle", "mother", "father"], default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.thing and args.case and args.clues:
        if not valid_combo(args.place, args.thing, args.case, args.clues):
            raise StoryError(explain_rejection(args.place, args.thing, args.case, args.clues))
    elif args.clues and CLUES[args.clues].sense < SENSE_MIN:
        place_id = args.place or next(iter(PLACES))
        thing_id = args.thing or next(iter(THINGS))
        case_id = args.case or next(iter(CASES))
        raise StoryError(explain_rejection(place_id, thing_id, case_id, args.clues))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.thing is None or combo[1] == args.thing)
        and (args.case is None or combo[2] == args.case)
        and (args.clues is None or combo[3] == args.clues)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, thing_id, case_id, clues_id = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _pick_name(rng, detective_type)
    helper_name = args.helper_name or _pick_name(rng, helper_type, avoid=detective_name)
    grownup_type = args.grownup_type or rng.choice(["aunt", "uncle", "mother", "father"])
    return StoryParams(
        place=place_id,
        thing=thing_id,
        case=case_id,
        clues=clues_id,
        helper=helper,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
        grownup_type=grownup_type,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    missing: list[str] = []
    if params.place not in PLACES:
        missing.append(f"place={params.place}")
    if params.thing not in THINGS:
        missing.append(f"thing={params.thing}")
    if params.case not in CASES:
        missing.append(f"case={params.case}")
    if params.clues not in CLUES:
        missing.append(f"clues={params.clues}")
    if params.helper not in HELPERS:
        missing.append(f"helper={params.helper}")
    if missing:
        raise StoryError("(No story: invalid params: " + ", ".join(missing) + ".)")
    if not valid_combo(params.place, params.thing, params.case, params.clues):
        raise StoryError(explain_rejection(params.place, params.thing, params.case, params.clues))

    world = tell(
        place=PLACES[params.place],
        thing=THINGS[params.thing],
        case=CASES[params.case],
        clues=CLUES[params.clues],
        helper_cfg=HELPERS[params.helper],
        detective_name=params.detective_name,
        detective_type=params.detective_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        grownup_type=params.grownup_type,
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

    c_sensible = set(asp_sensible_clues())
    p_sensible = {c.id for c in sensible_clues()}
    if c_sensible == p_sensible:
        print(f"OK: sensible clues match ({sorted(c_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible clues: clingo={sorted(c_sensible)} python={sorted(p_sensible)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            continue

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    smoke = CURATED[0]
    try:
        sample = generate(smoke)
        if not sample.story or "seek" not in sample.story.lower() or "lush" not in sample.story.lower():
            raise StoryError("(Smoke test failed: story missing required surface words.)")
        emit(sample, trace=False, qa=False, header="")  # ordinary generate/emit smoke test
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible clues: {', '.join(asp_sensible_clues())}\n")
        print(f"{len(combos)} compatible (place, thing, case, clues) combos:\n")
        for place_id, thing_id, case_id, clues_id in combos:
            print(f"  {place_id:13} {thing_id:8} {case_id:12} {clues_id}")
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
            header = f"### {p.detective_name}: {p.case} case in {p.place} ({p.thing}, {p.clues})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
