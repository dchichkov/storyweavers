#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hilarious_transformation_ghost_story.py
==================================================================

A small story world for a child-facing ghost story where a spooky shape turns
out not to be a ghost at all, and then gets transformed into something
hilarious.

The domain models a simple fear-to-laughter arc:

    dim room + pale cloth over a tall frame + a little motion
        -> a ghostly silhouette appears

    ghostly silhouette + enough light
        -> the "ghost" is recognized as an ordinary object

    recognized object + silly decoration
        -> the shape is transformed into a hilarious pretend ghost

This script follows the Storyweavers single-file storyworld contract:
stdlib only, eager import of results.py, lazy import of asp.py for ASP modes,
seeded parameter resolution, reasonableness checks, trace/QA/JSON output,
and parity verification between Python and inline ASP logic.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    intro: str
    detail: str
    darkness: int
    motion: str
    light_opening: str
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
class Frame:
    id: str
    label: str
    phrase: str
    need: int
    sways: bool
    revealed_as: str
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
class Cloth:
    id: str
    label: str
    phrase: str
    size: int
    pale: bool
    whisper: str
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
class Response:
    id: str
    label: str
    sense: int
    power: int
    act: str
    success: str
    weak: str
    qa_text: str
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
class Decoration:
    id: str
    label: str
    phrase: str
    transform_text: str
    final_image: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_ghostly(world: World) -> list[str]:
    shape = world.get("shape")
    hero = world.get("hero")
    if shape.meters["draped"] < THRESHOLD:
        return []
    if world.place.darkness < 1:
        return []
    if shape.attrs.get("cloth_pale") is not True:
        return []
    if shape.attrs.get("frame_sways") is not True:
        return []
    sig = ("ghostly",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shape.meters["ghostly"] += 1
    hero.memes["fear"] += 1
    return ["__ghostly__"]


def _r_recognize(world: World) -> list[str]:
    shape = world.get("shape")
    hero = world.get("hero")
    helper = world.get("helper")
    if shape.meters["ghostly"] < THRESHOLD:
        return []
    if world.facts.get("light_power", 0) < world.place.darkness:
        return []
    sig = ("recognized",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shape.meters["recognized"] += 1
    shape.meters["ghostly"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["brave"] += 1
    return ["__recognized__"]


def _r_funny(world: World) -> list[str]:
    shape = world.get("shape")
    hero = world.get("hero")
    helper = world.get("helper")
    if shape.meters["recognized"] < THRESHOLD:
        return []
    if shape.meters["decorated"] < THRESHOLD:
        return []
    sig = ("funny",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shape.meters["funny"] += 1
    hero.memes["giggles"] += 1
    helper.memes["giggles"] += 1
    return ["__funny__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="ghostly", tag="perception", apply=_r_ghostly),
    Rule(name="recognized", tag="perception", apply=_r_recognize),
    Rule(name="funny", tag="social", apply=_r_funny),
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


def looks_ghostly(place: Place, frame: Frame, cloth: Cloth) -> bool:
    return place.darkness >= 1 and frame.sways and cloth.pale and cloth.size >= frame.need


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def reveal_strength(place: Place, response: Response) -> bool:
    return response.power >= place.darkness


def explain_shape_rejection(place: Place, frame: Frame, cloth: Cloth) -> str:
    if cloth.size < frame.need:
        return (
            f"(No story: {cloth.phrase} is too small to hide {frame.phrase}, so it would "
            f"not make one tall spooky shape. Pick a bigger cloth or a smaller frame.)"
        )
    if not cloth.pale:
        return (
            f"(No story: {cloth.phrase} is not pale enough to read as a ghost in the dim "
            f"room. Pick a white or light cloth.)"
        )
    if not frame.sways:
        return (
            f"(No story: {frame.phrase} would just sit there and not wobble or sway, so "
            f"it would not feel ghostly enough for this story.)"
        )
    if place.darkness < 1:
        return "(No story: this place is not dim enough for a ghostly mistake.)"
    return "(No story: that combination would not make a believable ghostly shape.)"


def explain_response_rejection(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a clearer, braver choice like: {better}.)"
    )


def predict_reveal(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    recognized = sim.get("shape").meters["recognized"] >= THRESHOLD
    return {
        "recognized": recognized,
        "fear_after": sim.get("hero").memes["fear"],
    }


def introduce(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"One evening, {hero.id} and {helper.id} crept into {place.label}. "
        f"{place.intro} {place.detail}"
    )


def hear_and_see(world: World, hero: Entity, helper: Entity, cloth: Cloth, place: Place) -> None:
    hero.memes["curious"] += 1
    world.say(
        f"A soft {cloth.whisper} slipped through the room as the air moved, and both "
        f"children froze. Near the far wall, something pale rocked in the dark."
    )
    world.say(
        f'"Did you see that?" {hero.id} whispered. "{helper.id}, I think there is a ghost."'
    )


def build_shape(world: World, frame: Frame, cloth: Cloth) -> None:
    shape = world.get("shape")
    shape.meters["draped"] = 1.0
    shape.attrs["cloth_pale"] = cloth.pale
    shape.attrs["frame_sways"] = frame.sways
    propagate(world, narrate=False)


def fear_beat(world: World, hero: Entity, helper: Entity, frame: Frame, cloth: Cloth) -> None:
    if world.get("shape").meters["ghostly"] >= THRESHOLD:
        hero.memes["fear"] += 1
        world.say(
            f"The {cloth.label} hung over {frame.phrase} in a long lumpy shape, and every "
            f"little wobble made it look more alive. {hero.id}'s knees felt watery."
        )
        world.say(
            f'"It is watching us," {hero.id} murmured, edging closer to {helper.id}.'
        )


def choose_response(world: World, helper: Entity, response: Response) -> None:
    world.facts["light_power"] = response.power
    world.say(f'{helper.id} took a breath. "{response.act}," {helper.pronoun()} said.')


def quick_reveal(world: World, hero: Entity, helper: Entity, response: Response, frame: Frame) -> None:
    propagate(world, narrate=False)
    world.say(response.success)
    world.say(
        f"The terrible ghost did not float or howl at all. It was only {frame.revealed_as}."
    )
    world.say(
        f"{hero.id} blinked once, then twice, and the fear inside {hero.pronoun('object')} "
        f"began to melt into relief."
    )


def slow_reveal(world: World, hero: Entity, helper: Entity, parent: Entity,
                response: Response, frame: Frame, place: Place) -> None:
    hero.memes["fear"] += 1
    world.say(response.weak)
    world.say(
        f"For one more long second, the shape still looked ghostly in {place.label}, and "
        f"{hero.id} grabbed {helper.id}'s sleeve."
    )
    world.say(f'"{parent.label_word.capitalize()}!" both children called.')
    world.say(
        f"{parent.label_word.capitalize()} came in, {place.light_opening}, and the room "
        f"changed at once. The ghost was nothing but {frame.revealed_as}."
    )
    shape = world.get("shape")
    shape.meters["recognized"] = 1.0
    shape.meters["ghostly"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["brave"] += 1


def decorate(world: World, hero: Entity, helper: Entity, decoration: Decoration) -> None:
    shape = world.get("shape")
    shape.meters["decorated"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.id} spotted {decoration.phrase} nearby, and an idea popped into "
        f"{helper.pronoun('possessive')} head."
    )
    world.say(decoration.transform_text)
    world.say(
        f"In one moment the room had held a ghost, and in the next it held something "
        f"hilarious."
    )
    world.say(
        f"{hero.id} laughed so hard that the last of the fear flew away."
    )


def ending(world: World, hero: Entity, helper: Entity, decoration: Decoration) -> None:
    world.say(
        f"Soon {hero.id} and {helper.id} were marching around the room beside their new "
        f"pretend ghost friend. {decoration.final_image}"
    )


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        intro="The rafters were high and dusty.",
        detail="Moonlight squeezed through a tiny window, and old trunks made dark corners everywhere.",
        darkness=2,
        motion="draft",
        light_opening="pulled the attic cord so the bare bulb blinked on",
        tags={"attic", "dark", "light"},
    ),
    "hallway": Place(
        id="hallway",
        label="the upstairs hallway",
        intro="The floorboards were old and creaky.",
        detail="A little night-glow from the stairwell reached only halfway down the runner rug.",
        darkness=1,
        motion="draft",
        light_opening="reached over and clicked on the hall lamp",
        tags={"hallway", "dark", "light"},
    ),
    "laundry": Place(
        id="laundry",
        label="the laundry room",
        intro="The room smelled like soap and warm towels.",
        detail="The dryer had stopped, but one small window still rattled softly in its frame.",
        darkness=2,
        motion="window",
        light_opening="tapped the bright ceiling switch",
        tags={"laundry", "dark", "light"},
    ),
}

FRAMES = {
    "coat_rack": Frame(
        id="coat_rack",
        label="coat rack",
        phrase="a tall coat rack",
        need=2,
        sways=True,
        revealed_as="a tall coat rack with two scarves hanging from its hooks",
        tags={"rack"},
    ),
    "drying_rack": Frame(
        id="drying_rack",
        label="drying rack",
        phrase="a folding drying rack",
        need=2,
        sways=True,
        revealed_as="a folding drying rack with socks dangling from one bar",
        tags={"rack", "laundry"},
    ),
    "broom_stack": Frame(
        id="broom_stack",
        label="broom stack",
        phrase="a stack of brooms tied together in a bucket",
        need=1,
        sways=True,
        revealed_as="a bucket of brooms leaning together like tall reeds",
        tags={"broom"},
    ),
    "trunk": Frame(
        id="trunk",
        label="trunk",
        phrase="an old trunk",
        need=1,
        sways=False,
        revealed_as="an old trunk with brass corners",
        tags={"trunk"},
    ),
}

CLOTHS = {
    "sheet": Cloth(
        id="sheet",
        label="sheet",
        phrase="a white sheet",
        size=2,
        pale=True,
        whisper="flap-flap",
        tags={"sheet", "white"},
    ),
    "curtain": Cloth(
        id="curtain",
        label="lace curtain",
        phrase="a pale lace curtain",
        size=1,
        pale=True,
        whisper="shhh-shhh",
        tags={"curtain", "white"},
    ),
    "tablecloth": Cloth(
        id="tablecloth",
        label="tablecloth",
        phrase="a cream tablecloth",
        size=1,
        pale=True,
        whisper="rustle-rustle",
        tags={"cloth", "white"},
    ),
    "blanket": Cloth(
        id="blanket",
        label="striped blanket",
        phrase="a striped blanket",
        size=2,
        pale=False,
        whisper="fwump",
        tags={"blanket"},
    ),
}

RESPONSES = {
    "flashlight": Response(
        id="flashlight",
        label="flashlight",
        sense=3,
        power=3,
        act="Let's shine the flashlight right at it",
        success="A bright beam leapt across the room and cut the darkness open.",
        weak="A little flashlight beam wobbled over the shape, but the corners stayed thick with shadow.",
        qa_text="shone a flashlight on the shape",
        tags={"flashlight", "light"},
    ),
    "lamp_switch": Response(
        id="lamp_switch",
        label="lamp switch",
        sense=3,
        power=2,
        act="Let's turn on the nearest lamp",
        success="The lamp clicked on, and warm yellow light spread over the floorboards.",
        weak="The lamp made a small puddle of light, but the far end of the room still looked murky and strange.",
        qa_text="turned on a lamp",
        tags={"lamp", "light"},
    ),
    "open_door": Response(
        id="open_door",
        label="open door",
        sense=2,
        power=1,
        act="Let's open the door wider and let more light in",
        success="More light spilled in from the hall and washed the shape from head to toe.",
        weak="A strip of light slid in through the doorway, but the shape still looked tall and eerie beyond it.",
        qa_text="opened the door to let light in",
        tags={"door", "light"},
    ),
    "hide": Response(
        id="hide",
        label="hide",
        sense=1,
        power=0,
        act="Let's hide under the blanket",
        success="They hid, which did not really help at all.",
        weak="Hiding only made the room feel darker.",
        qa_text="hid under a blanket",
        tags={"hide"},
    ),
}

DECORATIONS = {
    "mustache": Decoration(
        id="mustache",
        label="paper mustache",
        phrase="a black paper mustache from a craft box",
        transform_text="They stuck the paper mustache right on the cloth, and the ghost instantly looked as if it was trying to be very serious and failing.",
        final_image='The "ghost" bobbed in the light with a curly mustache, and the children kept giggling every time they saluted it.',
        tags={"mustache", "craft"},
    ),
    "party_hat": Decoration(
        id="party_hat",
        label="party hat",
        phrase="a shiny party hat left from an old celebration",
        transform_text="They balanced the party hat on top, and the ghost went from spooky to silly so fast that both children burst out laughing.",
        final_image='Their ghost wore a crooked party hat and looked ready for cake instead of haunting.',
        tags={"party_hat", "party"},
    ),
    "bow": Decoration(
        id="bow",
        label="ribbon bow",
        phrase="a bright ribbon bow from a wrapping basket",
        transform_text="They tied the ribbon bow around the neck of the cloth, and suddenly the ghost looked dressed for a parade instead of a scare.",
        final_image='The bow bounced on the ghostly neck while the children paraded it from one corner to another.',
        tags={"bow", "ribbon"},
    ),
    "googly_eyes": Decoration(
        id="googly_eyes",
        label="googly eyes",
        phrase="two big googly eyes from the glue drawer",
        transform_text="They pressed on the googly eyes, and the ghost transformed into a wobbling face that looked more surprised than scary.",
        final_image='The googly-eyed ghost leaned by the wall, staring around in such a hilarious way that nobody could pretend to fear it anymore.',
        tags={"googly_eyes", "craft"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "careful", "brave", "quiet", "wide-eyed", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for frame_id, frame in FRAMES.items():
            for cloth_id, cloth in CLOTHS.items():
                if looks_ghostly(place, frame, cloth):
                    combos.append((place_id, frame_id, cloth_id))
    return combos


@dataclass
class StoryParams:
    place: str
    frame: str
    cloth: str
    response: str
    decoration: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    hero_trait: str
    helper_trait: str
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


def story_outcome(params: StoryParams) -> str:
    if params.place not in PLACES or params.response not in RESPONSES:
        raise StoryError("(No story: unknown place or response.)")
    return "quick" if reveal_strength(PLACES[params.place], RESPONSES[params.response]) else "slow"


KNOWLEDGE = {
    "ghost_story": [(
        "What is a ghost story?",
        "A ghost story is a spooky kind of story where something seems mysterious or haunted. In a child-friendly ghost story, the scary part often turns out to be safe in the end."
    )],
    "attic": [(
        "What is an attic?",
        "An attic is a room or space high up under the roof of a house. People often keep old boxes and things there."
    )],
    "laundry": [(
        "What happens in a laundry room?",
        "A laundry room is where clothes and towels are washed and dried. It often has baskets, soap, and drying racks."
    )],
    "hallway": [(
        "What is a hallway?",
        "A hallway is the part of a house that connects rooms. It is like a path inside the home."
    )],
    "sheet": [(
        "What is a sheet?",
        "A sheet is a large piece of cloth used on a bed. If it hangs over something, it can hide the shape underneath."
    )],
    "white": [(
        "Why can a pale cloth look spooky in the dark?",
        "A pale cloth stands out in dim light, so your eyes notice it first. If the shape underneath is hidden, your brain may guess the wrong thing."
    )],
    "light": [(
        "Why does turning on a light help when something looks scary?",
        "More light lets you see the real shape of things. When you can see clearly, a spooky guess often turns into an ordinary answer."
    )],
    "flashlight": [(
        "What is a flashlight?",
        "A flashlight is a small light you can carry in your hand. It helps you see in dark places."
    )],
    "mustache": [(
        "What is a mustache?",
        "A mustache is hair that grows above a person's lip. A paper mustache is a silly decoration people use for pretend play."
    )],
    "party_hat": [(
        "What is a party hat?",
        "A party hat is a fun hat people wear at celebrations. It can make almost anything look cheerful and silly."
    )],
    "googly_eyes": [(
        "What are googly eyes?",
        "Googly eyes are craft decorations with loose little pupils inside. They wobble when you move them."
    )],
    "bow": [(
        "What is a ribbon bow?",
        "A ribbon bow is ribbon tied into loops. People use bows to decorate gifts, clothes, and party things."
    )],
}
KNOWLEDGE_ORDER = [
    "ghost_story", "attic", "hallway", "laundry", "sheet", "white",
    "light", "flashlight", "mustache", "party_hat", "googly_eyes", "bow",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place_cfg"]
    decoration = f["decoration"]
    outcome = f["outcome"]
    base = (
        f'Write a short child-friendly ghost story that includes the word "hilarious" '
        f"and takes place in {place.label}."
    )
    if outcome == "slow":
        return [
            base,
            f"Tell a spooky-but-safe story where {hero.id} mistakes a covered object for a ghost, "
            f"{helper.id} tries a small light first, and a grown-up finally reveals the truth.",
            f"Write a Transformation story where a scary shape in {place.label} turns into a hilarious "
            f"pretend ghost after the children add {decoration.label}.",
        ]
    return [
        base,
        f"Tell a ghost story where {hero.id} and {helper.id} see a swaying shape in the dark, "
        f"then bravely use light to discover it is only an ordinary object.",
        f"Write a Transformation story where the false ghost is turned into something hilarious with "
        f"{decoration.label} at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    place = f["place_cfg"]
    frame = f["frame_cfg"]
    cloth = f["cloth_cfg"]
    response = f["response"]
    decoration = f["decoration"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {helper.id}, two children who saw a spooky shape in {place.label}. "
            f"The story also includes their {parent.label_word}, who helps if the room stays too dark."
        ),
        (
            f"Why did {hero.id} think there was a ghost?",
            f"{hero.id} saw {cloth.phrase} hanging over {frame.phrase} in a dim room, and the shape kept swaying. "
            f"In the dark, the hidden object looked alive instead of ordinary."
        ),
        (
            f"What did {helper.id} do when the room felt scary?",
            f"{helper.id} chose to {response.qa_text} instead of only standing there afraid. "
            f"That was the turning point, because light helps people see what is really in front of them."
        ),
    ]
    if outcome == "quick":
        qa.append((
            "What was the ghost really?",
            f"It was really {frame.revealed_as}. Once the light reached it, the ghostly mistake disappeared right away."
        ))
    else:
        qa.append((
            "Why did they call for a grown-up?",
            f"The first bit of light was not strong enough to show the whole shape clearly, so it still looked eerie. "
            f"They called {parent.label_word} to help, and the brighter light revealed the ordinary object."
        ))
    qa.append((
        "How did the scary thing become hilarious?",
        f"After the children understood it was safe, they decorated it with {decoration.label}. "
        f"That changed the same shape from spooky to silly, so fear turned into laughter."
    ))
    qa.append((
        "How did the story end?",
        f"It ended with the children laughing beside their pretend ghost friend. "
        f"The final image proves the transformation, because the thing they feared becomes part of the game."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"ghost_story"}
    f = world.facts
    tags |= set(f["place_cfg"].tags)
    tags |= set(f["cloth_cfg"].tags)
    tags |= set(f["response"].tags)
    tags |= set(f["decoration"].tags)

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


def tell(place: Place, frame: Frame, cloth: Cloth, response: Response, decoration: Decoration,
         hero_name: str = "Lily", hero_gender: str = "girl",
         helper_name: str = "Tom", helper_gender: str = "boy",
         parent_type: str = "mother", hero_trait: str = "curious",
         helper_trait: str = "brave") -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=[hero_trait],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[helper_trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    shape = world.add(Entity(
        id="shape",
        type="shape",
        label="the shape",
        attrs={
            "cloth_pale": cloth.pale,
            "frame_sways": frame.sways,
        },
    ))

    world.facts["light_power"] = 0
    world.facts["place_cfg"] = place
    world.facts["frame_cfg"] = frame
    world.facts["cloth_cfg"] = cloth
    world.facts["response"] = response
    world.facts["decoration"] = decoration

    introduce(world, hero, helper, place)
    hear_and_see(world, hero, helper, cloth, place)

    world.para()
    build_shape(world, frame, cloth)
    fear_beat(world, hero, helper, frame, cloth)

    world.para()
    choose_response(world, helper, response)
    predicted = predict_reveal(world)
    world.facts["predicted_recognized"] = predicted["recognized"]
    if predicted["recognized"]:
        quick_reveal(world, hero, helper, response, frame)
        outcome = "quick"
    else:
        slow_reveal(world, hero, helper, parent, response, frame, place)
        outcome = "slow"

    world.para()
    decorate(world, hero, helper, decoration)
    ending(world, hero, helper, decoration)

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        shape=shape,
        outcome=outcome,
        recognized=shape.meters["recognized"] >= THRESHOLD,
        transformed=shape.meters["funny"] >= THRESHOLD,
    )
    return world


CURATED = [
    StoryParams(
        place="attic",
        frame="coat_rack",
        cloth="sheet",
        response="flashlight",
        decoration="mustache",
        hero="Lily",
        hero_gender="girl",
        helper="Tom",
        helper_gender="boy",
        parent="mother",
        hero_trait="wide-eyed",
        helper_trait="brave",
    ),
    StoryParams(
        place="hallway",
        frame="broom_stack",
        cloth="curtain",
        response="open_door",
        decoration="party_hat",
        hero="Ben",
        hero_gender="boy",
        helper="Maya",
        helper_gender="girl",
        parent="father",
        hero_trait="curious",
        helper_trait="careful",
    ),
    StoryParams(
        place="laundry",
        frame="drying_rack",
        cloth="sheet",
        response="lamp_switch",
        decoration="googly_eyes",
        hero="Nora",
        hero_gender="girl",
        helper="Max",
        helper_gender="boy",
        parent="mother",
        hero_trait="quiet",
        helper_trait="brave",
    ),
    StoryParams(
        place="hallway",
        frame="broom_stack",
        cloth="tablecloth",
        response="flashlight",
        decoration="bow",
        hero="Sam",
        hero_gender="boy",
        helper="Ella",
        helper_gender="girl",
        parent="father",
        hero_trait="careful",
        helper_trait="playful",
    ),
    StoryParams(
        place="attic",
        frame="drying_rack",
        cloth="sheet",
        response="lamp_switch",
        decoration="party_hat",
        hero="Zoe",
        hero_gender="girl",
        helper="Leo",
        helper_gender="boy",
        parent="mother",
        hero_trait="curious",
        helper_trait="quiet",
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
ghostly_shape(P,F,C) :- place(P), frame(F), cloth(C),
                        darkness(P,D), D >= 1,
                        sways(F), pale(C),
                        need(F,N), size(C,S), S >= N.

sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(P,F,C) :- ghostly_shape(P,F,C).

% --- outcome model ---------------------------------------------------------
quick_reveal :- chosen_place(P), chosen_response(R),
                darkness(P,D), power(R,Po), Po >= D.
slow_reveal  :- chosen_place(P), chosen_response(R),
                darkness(P,D), power(R,Po), Po < D.

outcome(quick) :- quick_reveal.
outcome(slow)  :- slow_reveal.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("darkness", pid, place.darkness))
    for fid, frame in FRAMES.items():
        lines.append(asp.fact("frame", fid))
        lines.append(asp.fact("need", fid, frame.need))
        if frame.sways:
            lines.append(asp.fact("sways", fid))
    for cid, cloth in CLOTHS.items():
        lines.append(asp.fact("cloth", cid))
        lines.append(asp.fact("size", cid, cloth.size))
        if cloth.pale:
            lines.append(asp.fact("pale", cid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> str:
    bits = [sample.story]
    if sample.story_qa:
        bits.append(sample.story_qa[0].answer)
    return "\n".join(bits)


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

    py_sense = {r.id for r in sensible_responses()}
    asp_sense = set(asp_sensible())
    if py_sense == asp_sense:
        print(f"OK: sensible responses match ({sorted(py_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sense)} python={sorted(py_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random seed {seed}.")
            break

    bad = 0
    for params in cases:
        try:
            py = story_outcome(params)
            cl = asp_outcome(params)
            if py != cl:
                bad += 1
            sample = generate(params)
            rendered = _smoke_emit(sample)
            if not rendered.strip():
                raise RuntimeError("empty story output")
        except Exception as err:
            rc = 1
            print(f"Smoke test failed for {params}: {err}")
            return rc
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny ghost-story world: a spooky shape is revealed, then transformed into something hilarious."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--frame", choices=FRAMES)
    ap.add_argument("--cloth", choices=CLOTHS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--decoration", choices=DECORATIONS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(args.response))
    if args.place and args.frame and args.cloth:
        place = PLACES[args.place]
        frame = FRAMES[args.frame]
        cloth = CLOTHS[args.cloth]
        if not looks_ghostly(place, frame, cloth):
            raise StoryError(explain_shape_rejection(place, frame, cloth))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.frame is None or combo[1] == args.frame)
        and (args.cloth is None or combo[2] == args.cloth)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, frame_id, cloth_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    decoration_id = args.decoration or rng.choice(sorted(DECORATIONS))
    hero_name, hero_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)
    helper_trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        frame=frame_id,
        cloth=cloth_id,
        response=response_id,
        decoration=decoration_id,
        hero=hero_name,
        hero_gender=hero_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        hero_trait=hero_trait,
        helper_trait=helper_trait,
    )


def _get_or_fail(registry: dict, key: str, label: str):
    try:
        return registry[key]
    except KeyError as err:
        raise StoryError(f"(No story: unknown {label} '{key}'.)") from err


def generate(params: StoryParams) -> StorySample:
    place = _get_or_fail(PLACES, params.place, "place")
    frame = _get_or_fail(FRAMES, params.frame, "frame")
    cloth = _get_or_fail(CLOTHS, params.cloth, "cloth")
    response = _get_or_fail(RESPONSES, params.response, "response")
    decoration = _get_or_fail(DECORATIONS, params.decoration, "decoration")

    if not looks_ghostly(place, frame, cloth):
        raise StoryError(explain_shape_rejection(place, frame, cloth))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(params.response))

    world = tell(
        place=place,
        frame=frame,
        cloth=cloth,
        response=response,
        decoration=decoration,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        hero_trait=params.hero_trait,
        helper_trait=params.helper_trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  place={world.place.id} darkness={world.place.darkness}")
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v or v is False}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


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
        print(f"{len(combos)} compatible (place, frame, cloth) combos:\n")
        for place, frame, cloth in combos:
            print(f"  {place:8} {frame:12} {cloth}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for params in CURATED:
            samples.append(generate(params))
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
                f"### {p.hero} & {p.helper}: {p.cloth} over {p.frame} in {p.place} "
                f"({p.response}, {story_outcome(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
