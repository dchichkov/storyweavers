#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pest_while_humor_quest_lesson_learned_bedtime.py
==============================================================================

A standalone story world about a tiny bedtime pest, a humorous little quest,
and a calm lesson learned.

The world rebuilds a simple bedtime-tale shape:

- a child is settling down for sleep
- a tiny pest appears in the room while the house is getting quiet
- the child and a grown-up turn the problem into a gentle quest
- a calm method helps the pest find its way outside
- the ending image proves what changed: the room is peaceful again, and the
  child knows that small nighttime troubles are easier to solve slowly

Run it
------
    python storyworlds/worlds/gpt-5.4/pest_while_humor_quest_lesson_learned_bedtime.py
    python storyworlds/worlds/gpt-5.4/pest_while_humor_quest_lesson_learned_bedtime.py --room bedroom --pest moth --method lamp_window
    python storyworlds/worlds/gpt_5.4/pest_while_humor_quest_lesson_learned_bedtime.py --pest moth --method shoebox_ramp
    python storyworlds/worlds/gpt_5.4/pest_while_humor_quest_lesson_learned_bedtime.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt_5.4/pest_while_humor_quest_lesson_learned_bedtime.py --all
    python storyworlds/worlds/gpt_5.4/pest_while_humor_quest_lesson_learned_bedtime.py --verify
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
CALM_TRAITS = {"careful", "patient", "sleepy"}
BOUNCY_TRAITS = {"bouncy", "giggly", "curious"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Room:
    id: str
    label: str
    cozy: str
    bed: str
    window_text: str
    floor_text: str
    has_window: bool = True
    has_lamp: bool = True
    reachable: bool = True
    open_floor: bool = False
    cluttered: bool = False
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
class PestKind:
    id: str
    label: str
    phrase: str
    movement: str
    sound: str
    perch: str
    outside_place: str
    light_seek: bool = False
    nimble: bool = False
    slow_flyer: bool = False
    harmless: bool = True
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
class Method:
    id: str
    label: str
    setup: str
    success: str
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
class StoryParams:
    room: str
    pest: str
    method: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
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


def _r_disturb(world: World) -> list[str]:
    pest = world.get("pest")
    child = world.get("child")
    room = world.get("room")
    if pest.meters["outside"] >= THRESHOLD:
        return []
    if pest.meters["noticed"] < THRESHOLD:
        return []
    sig = ("disturb",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["disturbance"] += 1
    child.memes["worry"] += 1
    child.memes["sleepiness"] -= 1
    return ["__disturb__"]


def _r_silly(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    if child.memes["fluster"] < THRESHOLD:
        return []
    sig = ("silly",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["rumpled"] += 1
    child.memes["giggle"] += 1
    return ["__silly__"]


def _r_peace(world: World) -> list[str]:
    pest = world.get("pest")
    child = world.get("child")
    room = world.get("room")
    parent = world.get("parent")
    if pest.meters["outside"] < THRESHOLD:
        return []
    sig = ("peace",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["disturbance"] = 0.0
    child.memes["relief"] += 1
    child.memes["sleepiness"] += 1
    child.memes["worry"] = 0.0
    parent.memes["pride"] += 1
    return ["__peace__"]


CAUSAL_RULES = [
    Rule(name="disturb", tag="emotional", apply=_r_disturb),
    Rule(name="silly", tag="social", apply=_r_silly),
    Rule(name="peace", tag="emotional", apply=_r_peace),
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


ROOMS = {
    "bedroom": Room(
        id="bedroom",
        label="bedroom",
        cozy="a moon-blue bedroom with a quilt puffed up like a cloud",
        bed="a little bed tucked under a shelf of books",
        window_text="a window with curtains that breathed in and out with the night air",
        floor_text="a clear patch of floor beside the bed",
        has_window=True,
        has_lamp=True,
        reachable=True,
        open_floor=True,
        cluttered=False,
        tags={"bedroom", "sleep"},
    ),
    "nursery": Room(
        id="nursery",
        label="nursery",
        cozy="a warm nursery with a soft rug and a sleepy rabbit lamp",
        bed="a crib beside a basket of blocks",
        window_text="a small window over the rocking chair",
        floor_text="a tidy rug with room for careful knees",
        has_window=True,
        has_lamp=True,
        reachable=True,
        open_floor=False,
        cluttered=False,
        tags={"nursery", "sleep"},
    ),
    "bunkroom": Room(
        id="bunkroom",
        label="bunkroom",
        cozy="a bunkroom where star stickers shone on the ceiling",
        bed="the lower bunk, made into a snug little cave with a blanket",
        window_text="a window near the foot of the bunk",
        floor_text="a crowded floor with slippers, books, and one brave sock",
        has_window=True,
        has_lamp=True,
        reachable=True,
        open_floor=False,
        cluttered=True,
        tags={"bedroom", "sleep"},
    ),
    "attic_room": Room(
        id="attic_room",
        label="attic room",
        cozy="a slanted attic room where moonlight leaned through the glass",
        bed="a narrow bed under the beams",
        window_text="a tall little window set in the roof",
        floor_text="a broad wooden floor that creaked politely",
        has_window=True,
        has_lamp=False,
        reachable=True,
        open_floor=True,
        cluttered=False,
        tags={"attic", "sleep"},
    ),
}

PESTS = {
    "moth": PestKind(
        id="moth",
        label="moth",
        phrase="a powdery little moth",
        movement="fly",
        sound="made a soft fizzing flutter",
        perch="the lampshade",
        outside_place="the night garden",
        light_seek=True,
        nimble=True,
        slow_flyer=False,
        harmless=True,
        tags={"moth", "pest", "night"},
    ),
    "cricket": PestKind(
        id="cricket",
        label="cricket",
        phrase="a chirping little cricket",
        movement="jump",
        sound="rubbed out one bright chirp after another",
        perch="the edge of a slipper",
        outside_place="the patch of grass by the porch",
        light_seek=False,
        nimble=True,
        slow_flyer=False,
        harmless=True,
        tags={"cricket", "pest", "night"},
    ),
    "beetle": PestKind(
        id="beetle",
        label="beetle",
        phrase="a shiny little beetle",
        movement="crawl",
        sound="ticked softly along the wall like a tiny button on legs",
        perch="the baseboard",
        outside_place="the flower bed",
        light_seek=False,
        nimble=False,
        slow_flyer=False,
        harmless=True,
        tags={"beetle", "pest"},
    ),
    "ladybug": PestKind(
        id="ladybug",
        label="ladybug",
        phrase="a red-spotted ladybug",
        movement="fly",
        sound="buzzed in a tiny, polite circle",
        perch="the curtain tie",
        outside_place="the rose bush",
        light_seek=True,
        nimble=False,
        slow_flyer=True,
        harmless=True,
        tags={"ladybug", "pest", "garden"},
    ),
}

METHODS = {
    "lamp_window": Method(
        id="lamp_window",
        label="lamp and window trick",
        setup="opened the window a little and made one bright point for the visitor to follow",
        success="The tiny flyer drifted to the glow, circled once, and slipped out into the dark like a flying crumb of velvet.",
        qa_text="They opened the window and used the light to guide the pest outside",
        tags={"light", "window"},
    ),
    "cup_card": Method(
        id="cup_card",
        label="cup-and-card rescue",
        setup="brought a clear cup and a stiff postcard, moving as slowly as soup cools",
        success="The cup went over the little visitor, the card slid underneath, and the whole rescue wobbled only once before it was carried outside.",
        qa_text="They covered the pest with a cup, slid a card underneath, and carried it outside",
        tags={"cup", "gentle"},
    ),
    "shoebox_ramp": Method(
        id="shoebox_ramp",
        label="shoebox ramp",
        setup="set down an empty shoebox and tilted the lid into a little ramp toward freedom",
        success="After one doubtful pause, the tiny traveler climbed the ramp, disappeared into the box, and was tipped gently out beneath the stars.",
        qa_text="They used a shoebox like a little ramp and guided the pest out",
        tags={"box", "gentle"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ava", "Ella", "Ruby", "Maya", "Zoe"]
BOY_NAMES = ["Ben", "Theo", "Sam", "Max", "Leo", "Eli", "Noah", "Finn"]
TRAITS = ["careful", "patient", "sleepy", "bouncy", "giggly", "curious"]


def supports_pest(method: Method, pest: PestKind) -> bool:
    if method.id == "lamp_window":
        return pest.light_seek
    if method.id == "cup_card":
        return pest.movement in {"crawl", "jump"} or pest.slow_flyer
    if method.id == "shoebox_ramp":
        return pest.movement in {"crawl", "jump"}
    return False


def available_in_room(method: Method, room: Room) -> bool:
    if method.id == "lamp_window":
        return room.has_window and room.has_lamp
    if method.id == "cup_card":
        return room.reachable
    if method.id == "shoebox_ramp":
        return room.open_floor
    return False


def method_works(method: Method, pest: PestKind, room: Room) -> bool:
    return supports_pest(method, pest) and available_in_room(method, room)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id, room in ROOMS.items():
        for pest_id, pest in PESTS.items():
            for method_id, method in METHODS.items():
                if method_works(method, pest, room):
                    combos.append((room_id, pest_id, method_id))
    return combos


def is_silly_outcome(trait: str, pest: PestKind, room: Room) -> bool:
    if trait in BOUNCY_TRAITS and pest.nimble:
        return True
    if room.cluttered and pest.nimble:
        return True
    return False


def outcome_of(params: StoryParams) -> str:
    room = ROOMS.get(params.room)
    pest = PESTS.get(params.pest)
    method = METHODS.get(params.method)
    if room is None or pest is None or method is None:
        raise StoryError("(No story: one of the chosen options is unknown.)")
    if not method_works(method, pest, room):
        raise StoryError(explain_rejection(room, pest, method))
    return "silly" if is_silly_outcome(params.trait, pest, room) else "smooth"


def predict_success(world: World, method: Method) -> dict:
    sim = world.copy()
    pest = sim.get("pest")
    apply_method(sim, method, narrate=False)
    return {
        "outside": pest.meters["outside"] >= THRESHOLD,
        "disturbance": sim.get("room").meters["disturbance"],
    }


def bedtime_setup(world: World, child: Entity, parent: Entity, room_cfg: Room) -> None:
    child.memes["sleepiness"] += 2
    child.memes["cozy"] += 1
    world.say(
        f"One quiet night, {child.id} was getting ready for bed in {room_cfg.cozy}. "
        f"There was {room_cfg.bed}, and near it was {room_cfg.window_text}."
    )
    world.say(
        f"{child.id}'s {parent.label_word} tucked the blanket under {child.pronoun('possessive')} toes "
        f"while the room grew softer and softer."
    )


def pest_appears(world: World, child: Entity, pest_cfg: PestKind) -> None:
    pest = world.get("pest")
    pest.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {child.id} heard something odd. {pest_cfg.sound} near {pest_cfg.perch}, "
        f"and there it was: {pest_cfg.phrase}, a tiny bedtime pest that had wandered into the room."
    )
    world.say(
        f'"Oh!" whispered {child.id}. "There is a pest in here while I am trying to sleep."'
    )


def quest_frame(world: World, child: Entity, parent: Entity, room_cfg: Room, pest_cfg: PestKind) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{parent.label_word.capitalize()} looked, listened, and did not laugh at first. "
        f"Then the little visitor zigged the wrong way so grandly that both of them had to smile."
    )
    world.say(
        f'"This is not a monster quest," {parent.label_word} whispered. "It is a tiny helping quest. '
        f'We only have to show the little {pest_cfg.label} the way back to {pest_cfg.outside_place}."'
    )
    world.say(
        f"{child.id} sat up under the blanket and nodded as if a silver bell had just been rung for adventure."
    )


def choose_plan(world: World, child: Entity, parent: Entity, method: Method) -> None:
    prediction = predict_success(world, method)
    world.facts["predicted_outside"] = prediction["outside"]
    world.facts["predicted_disturbance"] = prediction["disturbance"]
    world.say(
        f'{parent.label_word.capitalize()} fetched what they needed and {method.setup}. '
        f'"Slow feet, soft hands," {parent.pronoun()} said.'
    )
    child.memes["trust"] += 1


def silly_detour(world: World, child: Entity, parent: Entity, pest_cfg: PestKind, room_cfg: Room) -> None:
    child.memes["fluster"] += 1
    propagate(world, narrate=False)
    if pest_cfg.id == "moth":
        world.say(
            f"But the moth had other ideas. It fluttered past the plan, landed on {parent.label_word}'s hair for one surprised second, "
            f"and made {child.id} clap both hands over {child.pronoun('possessive')} mouth to keep the giggles in."
        )
    elif pest_cfg.id == "cricket":
        world.say(
            f"But the cricket boinged sideways instead, straight into a slipper. For a moment the slipper looked as if it had found its own tiny violin."
        )
    elif pest_cfg.id == "ladybug":
        world.say(
            f"But the ladybug circled once around {child.id}'s nose before settling on the blanket, as if checking the map."
        )
    else:
        world.say(
            f"But the beetle marched the wrong way first, climbing onto the shoebox lid as solemnly as a knight who had forgotten which castle was his."
        )
    if room_cfg.cluttered:
        world.say(
            f"A book slid, a sock flopped over, and even the room seemed to snicker before everyone became quiet again."
        )
    world.say(
        f'{parent.label_word.capitalize()} took one slow breath. "{child.id}," {parent.pronoun()} whispered, "the pest is tiny, so our patience must be big."'
    )


def apply_method(world: World, method: Method, narrate: bool = True) -> None:
    pest = world.get("pest")
    room = world.get("room")
    if method.id == "lamp_window":
        pest.meters["at_window"] += 1
        pest.meters["outside"] += 1
        room.meters["window_open"] += 1
    elif method.id == "cup_card":
        pest.meters["trapped"] += 1
        pest.meters["outside"] += 1
    elif method.id == "shoebox_ramp":
        pest.meters["guided"] += 1
        pest.meters["outside"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(method.success)


def lesson(world: World, child: Entity, parent: Entity, pest_cfg: PestKind) -> None:
    child.memes["learned"] += 1
    child.memes["calm"] += 1
    world.say(
        f"When the room grew still again, {parent.label_word} sat on the edge of the bed and brushed back {child.id}'s hair."
    )
    world.say(
        f'"Even a tiny pest can feel enormous at bedtime," {parent.pronoun()} said softly. '
        f'"But small nighttime troubles are easier while we stay gentle and think first. '
        f'We do not have to be wild to be brave."'
    )
    world.say(
        f'{child.id} thought about the little {pest_cfg.label}, the slow hands, and the silly detour, and gave a sleepy nod.'
    )


def ending(world: World, child: Entity, room_cfg: Room, pest_cfg: PestKind) -> None:
    world.say(
        f"Soon the window was snug again, the blanket was smooth enough, and the room felt like a room for sleeping instead of a room for chasing."
    )
    world.say(
        f"Outside, somewhere in {pest_cfg.outside_place}, the little visitor was busy with its own night business. "
        f"Inside, {child.id} curled down in the bed, smiling a little at the memory of the quest."
    )
    world.say(
        f"Before long, in {room_cfg.label}, the only thing moving was a quiet dream."
    )


def tell(
    room_cfg: Room,
    pest_cfg: PestKind,
    method: Method,
    *,
    name: str = "Lila",
    gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World()

    child = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            label=name,
            role="child",
            traits=[trait],
            attrs={},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
            traits=["calm"],
            attrs={},
        )
    )
    room = world.add(
        Entity(
            id="room",
            kind="thing",
            type="room",
            label=room_cfg.label,
            role="room",
            attrs={
                "has_window": room_cfg.has_window,
                "has_lamp": room_cfg.has_lamp,
                "reachable": room_cfg.reachable,
                "open_floor": room_cfg.open_floor,
                "cluttered": room_cfg.cluttered,
            },
        )
    )
    pest = world.add(
        Entity(
            id="pest",
            kind="thing",
            type=pest_cfg.label,
            label=pest_cfg.label,
            role="pest",
            attrs={
                "movement": pest_cfg.movement,
                "light_seek": pest_cfg.light_seek,
                "nimble": pest_cfg.nimble,
                "slow_flyer": pest_cfg.slow_flyer,
                "harmless": pest_cfg.harmless,
            },
        )
    )

    world.facts.update(
        room_cfg=room_cfg,
        pest_cfg=pest_cfg,
        method_cfg=method,
        child=child,
        parent=parent,
        room=room,
        pest=pest,
        trait=trait,
    )

    bedtime_setup(world, child, parent, room_cfg)
    world.para()
    pest_appears(world, child, pest_cfg)
    quest_frame(world, child, parent, room_cfg, pest_cfg)

    world.para()
    choose_plan(world, child, parent, method)
    outcome = "silly" if is_silly_outcome(trait, pest_cfg, room_cfg) else "smooth"
    if outcome == "silly":
        silly_detour(world, child, parent, pest_cfg, room_cfg)
    apply_method(world, method, narrate=True)

    world.para()
    lesson(world, child, parent, pest_cfg)
    ending(world, child, room_cfg, pest_cfg)

    world.facts.update(
        outcome=outcome,
        guided_out=pest.meters["outside"] >= THRESHOLD,
        room_peaceful=room.meters["disturbance"] < THRESHOLD,
        silly=outcome == "silly",
        method_succeeded=pest.meters["outside"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "moth": [
        (
            "Why do moths fly toward lights at night?",
            "Many moths use light to help them find their way, so a bright lamp can confuse them and pull them off course. That is why a moth may flutter around a light in a room.",
        )
    ],
    "cricket": [
        (
            "Why do crickets chirp?",
            "Crickets make chirping sounds by rubbing parts of their bodies together. At night those sounds can seem extra loud because the house is quiet.",
        )
    ],
    "beetle": [
        (
            "Are beetles dangerous in a bedroom?",
            "Most little beetles that wander inside are not dangerous at all. They are simply small bugs in the wrong place and can be guided back outside.",
        )
    ],
    "ladybug": [
        (
            "What is a ladybug?",
            "A ladybug is a small round beetle with spots. It may look bright and cheerful, but it still needs to be outside where it belongs.",
        )
    ],
    "light": [
        (
            "How can light help guide a bug?",
            "Some bugs notice bright light and move toward it. If a window is open, the light can help lead them back outside.",
        )
    ],
    "cup": [
        (
            "Why use a cup and a card to move a bug?",
            "A cup can gently cover a little bug without hurting it, and a card can slide underneath so the bug can be carried safely. It is a calm way to help instead of squishing.",
        )
    ],
    "box": [
        (
            "Why would a shoebox help with a tiny pest?",
            "A shoebox can make a small tunnel or ramp, which helps a crawling or jumping bug move in the right direction. It turns a hard chase into an easy path.",
        )
    ],
    "gentle": [
        (
            "Why is it better to move slowly with a tiny pest?",
            "Small creatures get startled quickly. When people move slowly, the bug is less likely to dart around and the problem is easier to solve.",
        )
    ],
    "sleep": [
        (
            "Why do little problems feel bigger at bedtime?",
            "At bedtime the house is darker and quieter, so one odd sound can seem much larger than it really is. Tired bodies also make surprises feel harder.",
        )
    ],
}
KNOWLEDGE_ORDER = ["sleep", "moth", "cricket", "beetle", "ladybug", "light", "cup", "box", "gentle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    pest_cfg = f["pest_cfg"]
    room_cfg = f["room_cfg"]
    outcome = f["outcome"]
    extra = "Include the words \"pest\" and \"while\"."
    mood = "with a humorous middle" if outcome == "silly" else "with a calm, cozy middle"
    return [
        f"Write a bedtime story for a 3-to-5-year-old about a child who finds a tiny {pest_cfg.label} pest in a {room_cfg.label} while getting ready to sleep. {extra}",
        f"Tell a gentle quest story where {child.id} and a parent help a little {pest_cfg.label} back outside, {mood}, and end with a lesson learned.",
        f"Write a child-facing bedtime tale that turns a small nighttime problem into a funny, kind adventure and finishes with the room peaceful again. {extra}",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    pest_cfg = f["pest_cfg"]
    room_cfg = f["room_cfg"]
    method = f["method_cfg"]
    outcome = f["outcome"]
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {pw}, and a tiny {pest_cfg.label} that wandered into the {room_cfg.label}. The whole story happens while {child.id} is supposed to be settling down for bed.",
        ),
        (
            "What problem started the bedtime quest?",
            f"The problem started when {child.id} heard the little {pest_cfg.label} in the room and noticed a bedtime pest where the room should have been quiet. Because the house was settling down for sleep, the small sound felt much bigger.",
        ),
        (
            f"How did {child.id}'s {pw} try to solve the problem?",
            f"{pw.capitalize()} used the {method.label}. {method.qa_text}, which gave the tiny visitor a way out instead of turning the room into a wild chase.",
        ),
    ]

    if outcome == "silly":
        qa.append(
            (
                "Why did the middle of the story become funny?",
                f"It became funny because the little {pest_cfg.label} did not follow the plan at once and made a silly detour. That made {child.id} giggle, but it also showed why calm patience worked better than hurrying.",
            )
        )
    else:
        qa.append(
            (
                "Why did the plan work smoothly?",
                f"The plan worked smoothly because {child.id} and {pw} moved slowly and stayed gentle. The quiet method gave the tiny visitor one clear path back outside.",
            )
        )

    qa.append(
        (
            "What lesson did the child learn?",
            f"{child.id} learned that even a tiny pest can seem huge at bedtime, but small nighttime troubles are easier while people stay calm and kind. The peaceful ending proves that bravery did not need shouting or swatting.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the pest outside where it belonged and the room feeling sleepy again. {child.id} could curl back into bed because the quest had turned the trouble into peace.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["room_cfg"].tags) | set(f["pest_cfg"].tags) | set(f["method_cfg"].tags)
    tags.add("gentle")
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None, False)}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(room: Room, pest: PestKind, method: Method) -> str:
    if not supports_pest(method, pest):
        if method.id == "lamp_window":
            return (
                f"(No story: the {method.label} works for light-seeking flyers, but a {pest.label} does not follow that kind of glow. "
                f"Pick a method that gently contains or guides this pest instead.)"
            )
        if method.id == "cup_card":
            return (
                f"(No story: a {pest.label} is not a good fit for the {method.label} here. "
                f"Choose a method that matches how this pest moves.)"
            )
        return (
            f"(No story: the {method.label} does not match a {pest.label}'s way of moving. "
            f"Choose a method that this pest can actually follow.)"
        )
    if not available_in_room(method, room):
        if method.id == "lamp_window":
            return (
                f"(No story: the {room.label} does not have both the window and lamp needed for the {method.label}. "
                f"Choose a room with those features or a different rescue method.)"
            )
        if method.id == "shoebox_ramp":
            return (
                f"(No story: the {room.label} does not have enough open floor for the {method.label}. "
                f"This quest needs a clear path, not a cramped one.)"
            )
        return (
            f"(No story: the {method.label} is not practical in the {room.label}. "
            f"Choose a room where the helper can reach the pest calmly.)"
        )
    return "(No story: this bedtime rescue does not make sense with those choices.)"


ASP_RULES = r"""
supports(lamp_window,P) :- light_seek(P).
supports(cup_card,P) :- movement(P,crawl).
supports(cup_card,P) :- movement(P,jump).
supports(cup_card,P) :- slow_flyer(P).
supports(shoebox_ramp,P) :- movement(P,crawl).
supports(shoebox_ramp,P) :- movement(P,jump).

available(lamp_window,R) :- has_window(R), has_lamp(R).
available(cup_card,R) :- reachable(R).
available(shoebox_ramp,R) :- open_floor(R).

valid(R,P,M) :- room(R), pest(P), method(M), supports(M,P), available(M,R).

nimble_pest :- chosen_pest(P), nimble(P).
bouncy_child :- chosen_trait(T), bouncy(T).
cluttered_room :- chosen_room(R), cluttered(R).

outcome(silly) :- nimble_pest, bouncy_child.
outcome(silly) :- nimble_pest, cluttered_room.
outcome(smooth) :- not outcome(silly).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        if room.has_window:
            lines.append(asp.fact("has_window", room_id))
        if room.has_lamp:
            lines.append(asp.fact("has_lamp", room_id))
        if room.reachable:
            lines.append(asp.fact("reachable", room_id))
        if room.open_floor:
            lines.append(asp.fact("open_floor", room_id))
        if room.cluttered:
            lines.append(asp.fact("cluttered", room_id))
    for pest_id, pest in PESTS.items():
        lines.append(asp.fact("pest", pest_id))
        lines.append(asp.fact("movement", pest_id, pest.movement))
        if pest.light_seek:
            lines.append(asp.fact("light_seek", pest_id))
        if pest.nimble:
            lines.append(asp.fact("nimble", pest_id))
        if pest.slow_flyer:
            lines.append(asp.fact("slow_flyer", pest_id))
    for method_id in METHODS:
        lines.append(asp.fact("method", method_id))
    for trait in sorted(BOUNCY_TRAITS):
        lines.append(asp.fact("bouncy", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_room", params.room),
            asp.fact("chosen_pest", params.pest),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        if len(smoke.story_qa) < 3 or len(smoke.world_qa) < 2:
            raise StoryError("QA sets too small")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny bedtime pest, a gentle quest, and a lesson learned."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--pest", choices=PESTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (room, pest, method) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room is not None and args.room not in ROOMS:
        raise StoryError("(No story: unknown room.)")
    if args.pest is not None and args.pest not in PESTS:
        raise StoryError("(No story: unknown pest.)")
    if args.method is not None and args.method not in METHODS:
        raise StoryError("(No story: unknown method.)")
    if args.trait is not None and args.trait not in TRAITS:
        raise StoryError("(No story: unknown trait.)")

    if args.room and args.pest and args.method:
        room = ROOMS[args.room]
        pest = PESTS[args.pest]
        method = METHODS[args.method]
        if not method_works(method, pest, room):
            raise StoryError(explain_rejection(room, pest, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.pest is None or combo[1] == args.pest)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, pest_id, method_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        room=room_id,
        pest=pest_id,
        method=method_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    room = ROOMS.get(params.room)
    pest = PESTS.get(params.pest)
    method = METHODS.get(params.method)
    if room is None or pest is None or method is None:
        raise StoryError("(No story: one of the chosen options is unknown.)")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("(No story: gender must be 'girl' or 'boy'.)")
    if params.parent not in {"mother", "father"}:
        raise StoryError("(No story: parent must be 'mother' or 'father'.)")
    if params.trait not in TRAITS:
        raise StoryError("(No story: unknown trait.)")
    if not method_works(method, pest, room):
        raise StoryError(explain_rejection(room, pest, method))

    world = tell(
        room_cfg=room,
        pest_cfg=pest,
        method=method,
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
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


CURATED = [
    StoryParams(
        room="bedroom",
        pest="moth",
        method="lamp_window",
        name="Lila",
        gender="girl",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        room="nursery",
        pest="cricket",
        method="cup_card",
        name="Ben",
        gender="boy",
        parent="father",
        trait="sleepy",
    ),
    StoryParams(
        room="attic_room",
        pest="beetle",
        method="shoebox_ramp",
        name="Maya",
        gender="girl",
        parent="mother",
        trait="patient",
    ),
    StoryParams(
        room="bunkroom",
        pest="ladybug",
        method="cup_card",
        name="Theo",
        gender="boy",
        parent="father",
        trait="giggly",
    ),
    StoryParams(
        room="bunkroom",
        pest="cricket",
        method="cup_card",
        name="Ruby",
        gender="girl",
        parent="mother",
        trait="bouncy",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, pest, method) combos:\n")
        for room, pest, method in combos:
            print(f"  {room:10} {pest:8} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        tries = 0
        while len(samples) < args.n and tries < max(50, args.n * 50):
            seed = base_seed + tries
            tries += 1
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
            header = f"### {p.name}: {p.pest} in {p.room} ({p.method}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
