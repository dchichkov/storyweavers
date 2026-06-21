#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/doody_illusory_transformation_surprise_nursery_rhyme.py
==================================================================================

A standalone story world for a tiny nursery-rhyme-like domain:

A child finds a funny little lump, mistakes it for something yucky or ordinary,
and is surprised when gentle care reveals what it really is. The key turn is a
reasonable transformation: a bulb can bloom, an egg can hatch, and a cocoon can
open. The wrong care is refused. The prose stays playful and sing-song, while
the state model tracks the object's physical change and the child's feelings.

Run it
------
    python storyworlds/worlds/gpt-5.4/doody_illusory_transformation_surprise_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/doody_illusory_transformation_surprise_nursery_rhyme.py --source bulb --care water
    python storyworlds/worlds/gpt-5.4/doody_illusory_transformation_surprise_nursery_rhyme.py --source egg --care wait
    python storyworlds/worlds/gpt-5.4/doody_illusory_transformation_surprise_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/doody_illusory_transformation_surprise_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4/doody_illusory_transformation_surprise_nursery_rhyme.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
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
    opening: str
    affordances: set[str] = field(default_factory=set)
    helper_kind: str = "friend"
    helper_name: str = "Robin"
    helper_type: str = "bird"
    helper_line: str = "Try a kinder look before you call it a lump."
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
class Seeming:
    id: str
    label: str
    phrase: str
    rhyme: str
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
class ResultForm:
    id: str
    label: str
    reveal_line: str
    ending_image: str
    knowledge_tag: str
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


@dataclass
class Source:
    id: str
    label: str
    tiny_phrase: str
    required_care: str
    result: str
    seemings: set[str] = field(default_factory=set)
    first_motion: str = ""
    final_motion: str = ""
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
class Care:
    id: str
    label: str
    verb: str
    past: str
    line: str
    touch: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------
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


def _r_transform(world: World) -> list[str]:
    obj = world.get("mystery")
    if obj.meters["transformed"] >= THRESHOLD:
        return []
    required = obj.attrs["required_care"]
    if obj.meters[required] < THRESHOLD:
        return []
    sig = ("transform", obj.id, required)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obj.meters["transforming"] += 1
    obj.meters["transformed"] += 1
    child = world.get("child")
    child.memes["surprise"] += 1
    child.memes["joy"] += 1
    child.memes["disgust"] = 0.0
    return ["__transform__"]


RULES = [
    Rule(name="transform", tag="physical", apply=_r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def source_supports_seeming(source: Source, seeming: Seeming) -> bool:
    return seeming.id in source.seemings


def care_fits_source(source: Source, care: Care) -> bool:
    return source.required_care == care.id


def place_affords_care(place: Place, care: Care) -> bool:
    return care.id in place.affordances


def valid_combo(place: Place, source: Source, seeming: Seeming, care: Care) -> bool:
    return (
        source_supports_seeming(source, seeming)
        and care_fits_source(source, care)
        and place_affords_care(place, care)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            for seeming_id, seeming in SEEMINGS.items():
                for care_id, care in CARES.items():
                    if valid_combo(place, source, seeming, care):
                        combos.append((place_id, source_id, seeming_id, care_id))
    return combos


def explain_rejection(place: Place, source: Source, seeming: Seeming, care: Care) -> str:
    if not source_supports_seeming(source, seeming):
        return (
            f"(No story: {source.label} does not reasonably look like {seeming.phrase}. "
            f"This world only allows believable mistaken looks before the surprise.)"
        )
    if not care_fits_source(source, care):
        need = CARES[source.required_care].label
        return (
            f"(No story: a {source.label} does not change by {care.label}. "
            f"It needs {need} for the transformation to make sense.)"
        )
    if not place_affords_care(place, care):
        return (
            f"(No story: {place.label} does not support {care.label}. "
            f"Pick a place where that gentle help is available.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_reveal(world: World, care_id: str) -> dict:
    sim = world.copy()
    obj = sim.get("mystery")
    obj.meters[care_id] += 1
    propagate(sim, narrate=False)
    return {
        "transformed": obj.meters["transformed"] >= THRESHOLD,
        "result": obj.attrs["result"],
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, place: Place, helper: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{place.opening} little {child.id} went skipping light, "
        f"while {helper.id} kept a gentle sight."
    )


def discover(world: World, child: Entity, source: Source, seeming: Seeming, place: Place) -> None:
    obj = world.get("mystery")
    obj.meters["found"] += 1
    world.say(
        f"By {place.label}, tucked small and moody, "
        f"{child.id} found {source.tiny_phrase} that looked like {seeming.phrase}."
    )
    if seeming.id == "doody":
        child.memes["disgust"] += 1
        world.say(
            f'"Oh mercy me, it might be doody!" {child.id} sang, '
            f'and hopped back from the tiny thing.'
        )
    else:
        child.memes["unease"] += 1
        world.say(
            f'"It is a queer and crumbly sight, and maybe doody, maybe not quite," '
            f'{child.id} sang.'
        )


def caution(world: World, child: Entity, helper: Entity, seeming: Seeming) -> None:
    world.say(
        f'{helper.id} tilted {helper.pronoun("possessive")} head just so. '
        f'"Hush now, dear. Looks can play tricks. Some little lumps are illusory, '
        f'and not the thing you first suppose."'
    )
    world.facts["illlusion_named"] = True
    if seeming.id == "doody":
        child.memes["hope"] += 1


def suggest(world: World, helper: Entity, care: Care, source: Source, result: ResultForm) -> None:
    pred = predict_reveal(world, care.id)
    world.facts["predicted_reveal"] = pred["transformed"]
    world.say(
        f'"{care.line}," said {helper.id}. "If we are kind and quiet and right, '
        f'perhaps this {source.label} will show its true delight."'
    )


def apply_care(world: World, child: Entity, care: Care) -> None:
    obj = world.get("mystery")
    child.memes["care"] += 1
    obj.meters[care.id] += 1
    world.say(
        f"So {child.id} {care.past} the little bit, "
        f"with {care.touch} and a patient wit."
    )
    propagate(world, narrate=False)


def reveal(world: World, child: Entity, source: Source, result: ResultForm) -> None:
    obj = world.get("mystery")
    if obj.meters["transformed"] < THRESHOLD:
        raise StoryError("(Story bug: the mystery object failed to transform after valid care.)")
    world.say(
        f"Then came the turn, the twinkle bright: {source.first_motion} "
        f"{result.reveal_line}"
    )
    world.say(
        f"{child.id} clapped hard in sweet surprise. "
        f'"Not doody at all! What a merry disguise!"'
    )
    world.say(
        f"{source.final_motion} and there to see "
        f"was {result.ending_image} for all to see."
    )


def closing(world: World, child: Entity, helper: Entity, result: ResultForm, care: Care) -> None:
    child.memes["trust"] += 1
    child.memes["joy"] += 1
    world.say(
        f'So {child.id} learned in rhyme that day: '
        f'"Be kind before you toss away."'
    )
    world.say(
        f"And {helper.id} smiled. With {care.label} and grace, "
        f"small surprises may show a brighter face."
    )
    world.facts["lesson"] = "be_kind_before_you_toss"


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    source: Source,
    seeming: Seeming,
    care: Care,
    result: ResultForm,
    child_name: str = "Mimi",
    child_gender: str = "girl",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["little", "bouncy"],
        attrs={},
    ))
    helper = world.add(Entity(
        id=place.helper_name,
        kind="character",
        type=place.helper_type,
        label=place.helper_name,
        role="helper",
        traits=["gentle"],
        attrs={},
    ))
    mystery = world.add(Entity(
        id="mystery",
        kind="thing",
        type=source.id,
        label=source.label,
        role="mystery",
        attrs={
            "required_care": source.required_care,
            "result": source.result,
            "seeming": seeming.id,
        },
    ))

    # Initialize every field the rules may read before propagation.
    mystery.meters["water"] = 0.0
    mystery.meters["warm"] = 0.0
    mystery.meters["wait"] = 0.0
    mystery.meters["transforming"] = 0.0
    mystery.meters["transformed"] = 0.0
    child.memes["surprise"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["disgust"] = 0.0
    child.memes["unease"] = 0.0
    child.memes["care"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["hope"] = 0.0

    world.facts.update(
        place=place,
        source=source,
        seeming=seeming,
        care=care,
        result=result,
        child=child,
        helper=helper,
        transformed=False,
        predicted_reveal=False,
        lesson="",
    )

    introduce(world, child, place, helper)
    discover(world, child, source, seeming, place)

    world.para()
    caution(world, child, helper, seeming)
    suggest(world, helper, care, source, result)
    apply_care(world, child, care)

    world.para()
    reveal(world, child, source, result)
    closing(world, child, helper, result, care)

    world.facts["transformed"] = mystery.meters["transformed"] >= THRESHOLD
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "garden": Place(
        id="garden",
        label="the garden wall",
        opening="In the garden, bright with dew,",
        affordances={"water", "wait"},
        helper_kind="bird",
        helper_name="Robin",
        helper_type="bird",
        helper_line="A robin knows what waking things may need.",
        tags={"garden"},
    ),
    "windowsill": Place(
        id="windowsill",
        label="the sunny sill",
        opening="By the window, warm and still,",
        affordances={"warm", "water"},
        helper_kind="cat",
        helper_name="Nell",
        helper_type="cat",
        helper_line="A windowsill can warm a quiet secret.",
        tags={"home"},
    ),
    "hedge": Place(
        id="hedge",
        label="the hedge-side moss",
        opening="By the hedge where breezes pass,",
        affordances={"wait"},
        helper_kind="bird",
        helper_name="Wren",
        helper_type="bird",
        helper_line="Some small things open only when left in peace.",
        tags={"garden"},
    ),
}

SEEMINGS = {
    "doody": Seeming(
        id="doody",
        label="doody",
        phrase="a tiny doody blob",
        rhyme="moody",
        tags={"mess"},
    ),
    "mud": Seeming(
        id="mud",
        label="mud clod",
        phrase="a muddy little clod",
        rhyme="thud",
        tags={"mud"},
    ),
    "pebble": Seeming(
        id="pebble",
        label="pebble",
        phrase="a dull brown pebble",
        rhyme="treble",
        tags={"stone"},
    ),
    "leaf": Seeming(
        id="leaf",
        label="leaf curl",
        phrase="a crumpled leaf curl",
        rhyme="whirl",
        tags={"leaf"},
    ),
}

RESULTS = {
    "flower": ResultForm(
        id="flower",
        label="flower",
        reveal_line="the brown husk split, and up sprang a crocus with a cup of gold.",
        ending_image="a yellow flower nodding in the morning air",
        knowledge_tag="flower",
    ),
    "chick": ResultForm(
        id="chick",
        label="chick",
        reveal_line="the shell gave a peep, a crack, and out blinked a fluffy chick.",
        ending_image="a round chick blinking like a butter dot",
        knowledge_tag="chick",
    ),
    "moth": ResultForm(
        id="moth",
        label="moth",
        reveal_line="the hushed case loosened, and out unfurled a velvet moth.",
        ending_image="a soft moth opening moon-pale wings",
        knowledge_tag="moth",
    ),
}

SOURCES = {
    "bulb": Source(
        id="bulb",
        label="bulb",
        tiny_phrase="a brown button of a bulb",
        required_care="water",
        result="flower",
        seemings={"doody", "mud"},
        first_motion="A drip, a sip, a tiny light rustle—",
        final_motion="The old little lump forgot its grumpy pose,",
        tags={"bulb", "plant"},
    ),
    "egg": Source(
        id="egg",
        label="egg",
        tiny_phrase="a speckled little egg",
        required_care="warm",
        result="chick",
        seemings={"doody", "pebble"},
        first_motion="A wiggle, a peep, a small round knock—",
        final_motion="The illusory pebble was no pebble at all,",
        tags={"egg", "bird"},
    ),
    "cocoon": Source(
        id="cocoon",
        label="cocoon",
        tiny_phrase="a curled-up cocoon",
        required_care="wait",
        result="moth",
        seemings={"doody", "leaf"},
        first_motion="A hush, a shiver, a silken sway—",
        final_motion="The odd little bundle split its sleepy seam,",
        tags={"cocoon", "moth"},
    ),
}

CARES = {
    "water": Care(
        id="water",
        label="a sprinkle of water",
        verb="sprinkle",
        past="sprinkled",
        line="Fetch a little water, not a shove, not a kick",
        touch="careful fingers and a silver drip",
        tags={"water"},
    ),
    "warm": Care(
        id="warm",
        label="a patch of warmth",
        verb="warm",
        past="warmed",
        line="Set it where the sunshine keeps a kindly seat",
        touch="a folded cloth and a windowsill's heat",
        tags={"warmth"},
    ),
    "wait": Care(
        id="wait",
        label="a patient wait",
        verb="wait",
        past="waited beside",
        line="Leave it in peace and let slow time sing",
        touch="still knees and a whispering spring",
        tags={"patience"},
    ),
}

GIRL_NAMES = ["Mimi", "Nell", "Poppy", "Lila", "Tansy", "Rosie", "Dora", "Elsie"]
BOY_NAMES = ["Toby", "Milo", "Finn", "Pip", "Ollie", "Jem", "Nico", "Rory"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    source: str
    seeming: str
    care: str
    child_name: str
    child_gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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


KNOWLEDGE = {
    "bulb": [
        ("What is a bulb?",
         "A bulb is a small round plant part that waits underground with food tucked inside it. When it gets water and the right season, it can grow leaves and a flower.")
    ],
    "flower": [
        ("How can a flower come from a brown bulb?",
         "A bulb can look plain on the outside, but it holds a sleeping plant inside. Water wakes its growth, so roots and shoots begin to push out.")
    ],
    "egg": [
        ("What is inside an egg before it hatches?",
         "Inside a good egg, a baby chick can grow. It needs warmth and time before it is ready to peep and crack the shell.")
    ],
    "chick": [
        ("Why does a chick peep when it hatches?",
         "A chick peeps as it starts to move and break out of the shell. The sound shows it is alive and working hard to come into the world.")
    ],
    "cocoon": [
        ("What is a cocoon?",
         "A cocoon is a little case some insects rest in while their bodies change. From the outside it can look plain, dry, or even leaf-like.")
    ],
    "moth": [
        ("How does a moth come out of a cocoon?",
         "While it rests inside, the insect changes shape. When it is ready, the case opens and the moth crawls out and spreads its wings.")
    ],
    "water": [
        ("Why do plants need water?",
         "Plants need water to stay alive and grow. Water helps move food through the plant and wakes dry roots and shoots.")
    ],
    "warmth": [
        ("Why does warmth help an egg hatch?",
         "Warmth helps the baby inside an egg grow safely. Without enough warmth, the chick cannot keep developing.")
    ],
    "patience": [
        ("Why is patience important for small growing things?",
         "Some changes happen slowly and cannot be rushed. Waiting quietly gives living things time to open, hatch, or grow in their own way.")
    ],
    "mess": [
        ("What should you do if you find something yucky on the ground?",
         "You should not poke it right away. Ask a grown-up or look carefully from a safe distance, because sometimes things are not what they first seem.")
    ],
}
KNOWLEDGE_ORDER = ["mess", "bulb", "flower", "egg", "chick", "cocoon", "moth", "water", "warmth", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    source = f["source"]
    care = f["care"]
    result = f["result"]
    seeming = f["seeming"]
    place = f["place"]
    return [
        f'Write a short nursery-rhyme-style story for a 3-to-5-year-old where a child finds a tiny lump near {place.label} and mistakes it for {seeming.phrase}. Include the words "doody" and "illusory".',
        f"Tell a gentle transformation story where {child.id} gives a strange little {source.label} {care.label}, and the surprise reveal is a {result.label}.",
        f"Write a sing-song story in which something plain or yucky-looking turns out to be wonderful, and the ending shows what changed in a clear picture.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    source = f["source"]
    seeming = f["seeming"]
    care = f["care"]
    result = f["result"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about little {child.id}, who found a tiny mystery by {place.label}, and {helper.id}, who helped {child.pronoun('object')} look again. Together they stayed gentle long enough to discover the truth."
        ),
        (
            f"What did {child.id} think the little thing looked like?",
            f"{child.id} thought it looked like {seeming.phrase}, and even worried it might be doody. That first mistake is what made the surprise feel big when the object changed."
        ),
        (
            f"Why did {helper.id} call the lump illusory?",
            f"{helper.id} said the lump was illusory because its first look was tricking them. It seemed ordinary or yucky on the outside, but that appearance was not the whole truth."
        ),
        (
            f"What did {child.id} do instead of throwing the thing away?",
            f"{child.id} gave it {care.label}. That gentle choice mattered because this {source.label} needed exactly that kind of help before it could reveal itself."
        ),
        (
            "What was the surprise at the end?",
            f"The little lump transformed into {result.ending_image}. The ending proves the change with a new picture, so the child can see that the mystery was never only what it first seemed."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mess"}
    source = f["source"]
    result = f["result"]
    care = f["care"]
    tags |= set(source.tags)
    tags.add(result.knowledge_tag)
    if care.id == "water":
        tags.add("water")
    elif care.id == "warm":
        tags.add("warmth")
    elif care.id == "wait":
        tags.add("patience")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
looks_like(Src, Seem) :- source(Src), supports(Src, Seem).
care_fits(Src, C) :- source(Src), need(Src, C).
place_has(P, C) :- place(P), affords(P, C).
valid(P, Src, Seem, C) :- place(P), source(Src), seeming(Seem), care(C),
                          looks_like(Src, Seem), care_fits(Src, C), place_has(P, C).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for care_id in sorted(place.affordances):
            lines.append(asp.fact("affords", place_id, care_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("need", source_id, source.required_care))
        for seeming_id in sorted(source.seemings):
            lines.append(asp.fact("supports", source_id, seeming_id))
    for seeming_id in SEEMINGS:
        lines.append(asp.fact("seeming", seeming_id))
    for care_id in CARES:
        lines.append(asp.fact("care", care_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    rc = 0
    c_set = set(asp_valid_combos())
    p_set = set(valid_combos())
    if c_set == p_set:
        print(f"OK: valid combo gate matches ({len(c_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_set - p_set:
            print("  only in clingo:", sorted(c_set - p_set))
        if p_set - c_set:
            print("  only in python:", sorted(p_set - c_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in (0, 1, 7, 21):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Smoke test failed: empty story from resolved params.)")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED for seed {seed}: {err}")
    if rc == 0:
        print("OK: resolved random generation succeeded on smoke seeds.")
    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="garden",
        source="bulb",
        seeming="doody",
        care="water",
        child_name="Mimi",
        child_gender="girl",
    ),
    StoryParams(
        place="windowsill",
        source="egg",
        seeming="pebble",
        care="warm",
        child_name="Pip",
        child_gender="boy",
    ),
    StoryParams(
        place="hedge",
        source="cocoon",
        seeming="leaf",
        care="wait",
        child_name="Rosie",
        child_gender="girl",
    ),
    StoryParams(
        place="garden",
        source="cocoon",
        seeming="doody",
        care="wait",
        child_name="Toby",
        child_gender="boy",
    ),
]


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a mistaken lump, gentle care, and a surprising transformation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--seeming", choices=SEEMINGS)
    ap.add_argument("--care", choices=CARES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and args.seeming and args.care:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        seeming = SEEMINGS[args.seeming]
        care = CARES[args.care]
        if not valid_combo(place, source, seeming, care):
            raise StoryError(explain_rejection(place, source, seeming, care))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.seeming is None or combo[2] == args.seeming)
        and (args.care is None or combo[3] == args.care)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, seeming_id, care_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)

    return StoryParams(
        place=place_id,
        source=source_id,
        seeming=seeming_id,
        care=care_id,
        child_name=name,
        child_gender=gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.seeming not in SEEMINGS:
        raise StoryError(f"(Unknown seeming: {params.seeming})")
    if params.care not in CARES:
        raise StoryError(f"(Unknown care: {params.care})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.child_gender})")

    place = PLACES[params.place]
    source = SOURCES[params.source]
    seeming = SEEMINGS[params.seeming]
    care = CARES[params.care]
    if not valid_combo(place, source, seeming, care):
        raise StoryError(explain_rejection(place, source, seeming, care))

    result_id = source.result
    if result_id not in RESULTS:
        raise StoryError(f"(Unknown result form: {result_id})")
    result = RESULTS[result_id]

    world = tell(
        place=place,
        source=source,
        seeming=seeming,
        care=care,
        result=result,
        child_name=params.child_name,
        child_gender=params.child_gender,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, seeming, care) combos:\n")
        for place, source, seeming, care in combos:
            print(f"  {place:10} {source:7} {seeming:7} {care}")
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
            header = f"### {p.child_name}: {p.source} as {p.seeming} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
