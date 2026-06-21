#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/glamour_crock_foreshadowing_ghost_story.py
=====================================================================

A standalone story world for a gentle ghost story about a child, a glamour over
an old crock, and the small signs that warn what is wrong before the ghost is
fully seen.

This world models a tiny haunted-house domain with typed entities, physical
meters, emotional memes, a reasonableness gate, and an inline ASP twin. The
core premise is simple:

- a child visits an old room at evening,
- a particular crock has been moved from the place it belongs,
- a ghostly glamour makes the crock look prettier than it is,
- small foreshadowing signs point toward the ghost's memory,
- the child and a calm grown-up return the crock to its proper place,
- the glamour melts away and the ghost rests.

Run it
------
    python storyworlds/worlds/gpt-5.4/glamour_crock_foreshadowing_ghost_story.py
    python storyworlds/worlds/gpt-5.4/glamour_crock_foreshadowing_ghost_story.py --room pantry --ghost cook --crock jam_crock
    python storyworlds/worlds/gpt-5.4/glamour_crock_foreshadowing_ghost_story.py --ghost gardener --crock milk_crock
    python storyworlds/worlds/gpt-5.4/glamour_crock_foreshadowing_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/glamour_crock_foreshadowing_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/glamour_crock_foreshadowing_ghost_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/glamour_crock_foreshadowing_ghost_story.py --verify
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
        female = {"girl", "mother", "aunt", "woman", "grandmother"}
        male = {"boy", "father", "uncle", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
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
    opener: str
    evening_detail: str
    home_shelf: str
    ambient_sound: str
    affords: set[str] = field(default_factory=set)
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
class Ghost:
    id: str
    label: str
    memory: str
    whisper: str
    omen: str
    scent: str
    affinity: set[str] = field(default_factory=set)
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
class Crock:
    id: str
    label: str
    phrase: str
    crack_line: str
    contents: str
    rightful_room: str
    shelf_spot: str
    omen_mark: str
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
class Glamour:
    id: str
    shine: str
    promise: str
    fade: str
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
class HelperStyle:
    id: str
    guidance: str
    move_text: str
    comfort_text: str
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


def _r_restless_cold(world: World) -> list[str]:
    crock = world.get("crock")
    ghost = world.get("ghost")
    room = world.get("room")
    if crock.meters["misplaced"] < THRESHOLD or ghost.memes["restless"] < THRESHOLD:
        return []
    sig = ("restless_cold",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["cold"] += 1
    world.get("child").memes["fear"] += 1
    return ["__cold__"]


def _r_glamour_hides_crack(world: World) -> list[str]:
    crock = world.get("crock")
    if crock.meters["glamour"] < THRESHOLD or crock.meters["cracked"] < THRESHOLD:
        return []
    sig = ("glamour_hides_crack",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crock.meters["hidden_crack"] += 1
    world.get("child").memes["curiosity"] += 1
    return ["__glamour__"]


def _r_return_soothes(world: World) -> list[str]:
    crock = world.get("crock")
    ghost = world.get("ghost")
    room = world.get("room")
    if crock.meters["returned"] < THRESHOLD:
        return []
    sig = ("return_soothes",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["restless"] = 0.0
    ghost.memes["peace"] += 1
    room.meters["cold"] = 0.0
    world.get("child").memes["fear"] = 0.0
    world.get("child").memes["comfort"] += 1
    return ["__peace__"]


CAUSAL_RULES = [
    Rule(name="restless_cold", tag="physical", apply=_r_restless_cold),
    Rule(name="glamour_hides_crack", tag="mystery", apply=_r_glamour_hides_crack),
    Rule(name="return_soothes", tag="social", apply=_r_return_soothes),
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


def ghost_matches_crock(ghost: Ghost, crock: Crock) -> bool:
    return crock.id in ghost.affinity


def room_matches_crock(room: Room, crock: Crock) -> bool:
    return crock.id in room.affords and crock.rightful_room == room.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id, room in ROOMS.items():
        for ghost_id, ghost in GHOSTS.items():
            for crock_id, crock in CROCKS.items():
                if room_matches_crock(room, crock) and ghost_matches_crock(ghost, crock):
                    combos.append((room_id, ghost_id, crock_id))
    return combos


def explain_rejection(room: Room, ghost: Ghost, crock: Crock) -> str:
    if not room_matches_crock(room, crock):
        return (
            f"(No story: {crock.label} does not properly belong in {room.label}. "
            f"This world only tells hauntings where the crock can honestly be returned to its rightful place.)"
        )
    if not ghost_matches_crock(ghost, crock):
        return (
            f"(No story: the {ghost.label} has no clear memory tied to the {crock.label}. "
            f"The ghost needs a believable bond to the crock for the haunting to make sense.)"
        )
    return "(No story: this combination is not part of the haunted-house logic.)"


def predict_haunting(world: World) -> dict:
    sim = world.copy()
    crock = sim.get("crock")
    ghost = sim.get("ghost")
    crock.meters["misplaced"] = 1
    crock.meters["glamour"] = 1
    ghost.memes["restless"] = 1
    propagate(sim, narrate=False)
    return {
        "cold": sim.get("room").meters["cold"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"] >= THRESHOLD,
        "hidden_crack": sim.get("crock").meters["hidden_crack"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper: Entity, room: Room) -> None:
    child.memes["calm"] += 1
    world.say(
        f"One dusky evening, {child.id} followed {helper.pronoun('possessive')} {helper.label_word} into {room.label}. "
        f"{room.opener}"
    )
    world.say(room.evening_detail)


def foreshadow(world: World, child: Entity, ghost: Ghost, crock: Crock, room: Room) -> None:
    world.facts["omens"] = [ghost.omen, crock.omen_mark, room.ambient_sound]
    child.memes["wonder"] += 1
    world.say(
        f"Before {child.id} saw anything strange, three little signs came first: {ghost.omen}, "
        f"{crock.omen_mark}, and {room.ambient_sound}."
    )
    world.say(
        f"The signs did not shout. They only seemed to whisper that someone in the room remembered {ghost.memory}."
    )


def notice_glamour(world: World, child: Entity, ghost: Ghost, crock_cfg: Crock, glamour: Glamour) -> None:
    crock = world.get("crock")
    ghost_ent = world.get("ghost")
    crock.meters["glamour"] = 1
    crock.meters["cracked"] = 1
    crock.meters["misplaced"] = 1
    ghost_ent.memes["restless"] = 1
    pred = predict_haunting(world)
    world.facts["predicted_cold"] = pred["cold"]
    world.facts["predicted_hidden_crack"] = pred["hidden_crack"]
    propagate(world, narrate=False)
    world.say(
        f"On a low table sat {crock_cfg.phrase}. A soft glamour lay over it, {glamour.shine}, "
        f"so it looked finer than the other old things in the room."
    )
    world.say(
        f'{child.id} stepped closer. It seemed to promise {glamour.promise}, and that made {child.pronoun("object")} want to touch it.'
    )


def lift_crock(world: World, child: Entity, ghost: Ghost, crock_cfg: Crock) -> None:
    child.memes["curiosity"] += 1
    world.get("crock").meters["lifted"] += 1
    world.say(
        f"When {child.id} lifted the crock, the room turned colder at once. Under the pretty shine ran {crock_cfg.crack_line}."
    )
    world.say(
        f"Then a thin voice rustled through the dark: {ghost.whisper}"
    )


def helper_guides(world: World, child: Entity, helper: Entity, ghost: Ghost, crock_cfg: Crock, room: Room, style: HelperStyle) -> None:
    helper.memes["care"] += 1
    child.memes["fear"] += 1
    world.say(
        f"{helper.label_word.capitalize()} did not snatch the crock away or laugh. {style.guidance}"
    )
    world.say(
        f'"Some things shine because they are lovely," {helper.pronoun()} said softly, '
        f'"and some shine because a ghost has wrapped them in glamour. This one belongs on {room.home_shelf}, where {ghost.memory} used to keep it."'
    )


def return_crock(world: World, child: Entity, helper: Entity, crock_cfg: Crock, room: Room, style: HelperStyle) -> None:
    crock = world.get("crock")
    crock.meters["returned"] = 1
    propagate(world, narrate=False)
    world.say(
        f"Together they carried the crock to {room.home_shelf}. {style.move_text}"
    )
    world.say(
        f"As soon as the crock touched its old spot, the glamour thinned and {GLAMOURS[world.facts['glamour_cfg'].id].fade}."
    )


def settle_ghost(world: World, child: Entity, helper: Entity, ghost: Ghost, style: HelperStyle) -> None:
    world.say(
        f"In the paling shimmer stood the {ghost.label}, no longer sharp with worry. The ghost gave one small nod, and the cold air loosened."
    )
    world.say(
        style.comfort_text
    )
    world.say(
        f"When they looked back, the room was only a room again, but kinder than before."
    )


def closing_image(world: World, child: Entity, crock_cfg: Crock, room: Room) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"Later, {child.id} glanced once more at {room.home_shelf}. The crock was plain now, with its crack easy to see, yet it seemed safer for being honest."
    )
    world.say(
        f"{child.pronoun().capitalize()} left the room with a steadier step, knowing that not every bright thing should be believed, and that even a ghost can rest when a lost belonging is gently put back."
    )


def tell(
    room: Room,
    ghost_cfg: Ghost,
    crock_cfg: Crock,
    glamour_cfg: Glamour,
    helper_style: HelperStyle,
    child_name: str = "Nora",
    child_gender: str = "girl",
    helper_type: str = "aunt",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the helper"))
    room_ent = world.add(Entity(id="room", type="room", label=room.label))
    ghost = world.add(Entity(id="ghost", type="ghost", label=ghost_cfg.label, role="ghost"))
    crock = world.add(Entity(id="crock", type="crock", label=crock_cfg.label, role="crock"))
    world.facts["omens"] = []
    world.facts["glamour_cfg"] = glamour_cfg

    room_ent.meters["cold"] = 0.0
    ghost.memes["restless"] = 0.0
    ghost.memes["peace"] = 0.0
    crock.meters["misplaced"] = 0.0
    crock.meters["glamour"] = 0.0
    crock.meters["cracked"] = 0.0
    crock.meters["hidden_crack"] = 0.0
    crock.meters["returned"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["comfort"] = 0.0

    introduce(world, child, helper, room)
    foreshadow(world, child, ghost_cfg, crock_cfg, room)

    world.para()
    notice_glamour(world, child, ghost_cfg, crock_cfg, glamour_cfg)
    lift_crock(world, child, ghost_cfg, crock_cfg)

    world.para()
    helper_guides(world, child, helper, ghost_cfg, crock_cfg, room, helper_style)
    return_crock(world, child, helper, crock_cfg, room, helper_style)
    settle_ghost(world, child, helper, ghost_cfg, helper_style)

    world.para()
    closing_image(world, child, crock_cfg, room)

    world.facts.update(
        room_cfg=room,
        ghost_cfg=ghost_cfg,
        crock_cfg=crock_cfg,
        helper_style=helper_style,
        child=child,
        helper=helper,
        room=room_ent,
        ghost=ghost,
        crock=crock,
        foreshadowed=bool(world.facts["omens"]),
        haunting_started=crock.meters["misplaced"] >= THRESHOLD and ghost_cfg.id is not None,
        resolved=crock.meters["returned"] >= THRESHOLD and ghost.memes["peace"] >= THRESHOLD,
    )
    return world


ROOMS = {
    "pantry": Room(
        id="pantry",
        label="the old pantry",
        opener="Rows of shelves stood in the half-light, and the window had begun to turn black like a pond at night.",
        evening_detail="The house smelled of flour, wood, and rain on stone.",
        home_shelf="the highest pantry shelf",
        ambient_sound="a tiny tap-tap came from a spoon swaying against a jar",
        affords={"jam_crock", "milk_crock"},
        tags={"pantry", "house"},
    ),
    "attic": Room(
        id="attic",
        label="the attic room",
        opener="The rafters leaned overhead, and moonlight lay across old trunks in pale bars.",
        evening_detail="Dust drifted through the beams like sleepy silver gnats.",
        home_shelf="a narrow shelf under the eaves",
        ambient_sound="something light clicked once inside a wooden chest",
        affords={"seed_crock", "jam_crock"},
        tags={"attic", "house"},
    ),
    "scullery": Room(
        id="scullery",
        label="the back scullery",
        opener="The sink was dark and quiet, and the tiles held the last cool breath of the day.",
        evening_detail="A wet smell lingered near the pump, though no water moved.",
        home_shelf="the little shelf beside the washbasin",
        ambient_sound="one drop fell somewhere, though the pipes were still",
        affords={"milk_crock"},
        tags={"kitchen", "house"},
    ),
}

GHOSTS = {
    "cook": Ghost(
        id="cook",
        label="cook's ghost",
        memory="stirring and saving sweet things for winter",
        whisper='"Not there. Not there. Put it back where hands remembered it."',
        omen="a warm sugar smell floated through the cold air",
        scent="sugar",
        affinity={"jam_crock", "milk_crock"},
        tags={"ghost", "cook"},
    ),
    "gardener": Ghost(
        id="gardener",
        label="gardener's ghost",
        memory="saving seeds and counting on spring",
        whisper='"The small sleeping things must wait in the right dark place."',
        omen="a thread of loose soil lay on the floorboards where no shoes had been",
        scent="earth",
        affinity={"seed_crock"},
        tags={"ghost", "gardener"},
    ),
    "grandmother": Ghost(
        id="grandmother",
        label="grandmother's ghost",
        memory="putting careful things back after the house had gone quiet",
        whisper='"A home feels wrong when one dear old thing is lost."',
        omen="a rocking chair gave one soft creak all by itself",
        scent="lavender",
        affinity={"jam_crock"},
        tags={"ghost", "grandmother"},
    ),
}

CROCKS = {
    "jam_crock": Crock(
        id="jam_crock",
        label="jam crock",
        phrase="a round crock painted with faded berries",
        crack_line="a hair-thin crack, hidden under the shine, from lid to foot",
        contents="jam",
        rightful_room="pantry",
        shelf_spot="the highest pantry shelf",
        omen_mark="a red stain on the cloth looked fresh though it was years old",
        tags={"crock", "jam"},
    ),
    "milk_crock": Crock(
        id="milk_crock",
        label="milk crock",
        phrase="a cream-colored crock with a blue rim",
        crack_line="a pale split along one side, like a line of trapped moonlight",
        contents="milk",
        rightful_room="scullery",
        shelf_spot="the little shelf beside the washbasin",
        omen_mark="the rim felt damp though the room was dry",
        tags={"crock", "milk"},
    ),
    "seed_crock": Crock(
        id="seed_crock",
        label="seed crock",
        phrase="a stout brown crock tied with a faded string",
        crack_line="a dark seam under the glaze where one side had once been bumped",
        contents="seeds",
        rightful_room="attic",
        shelf_spot="a narrow shelf under the eaves",
        omen_mark="three tiny seeds rested in a neat line on the floorboards",
        tags={"crock", "seed"},
    ),
}

GLAMOURS = {
    "silver": Glamour(
        id="silver",
        shine="making the glaze gleam like moonlit ice",
        promise="that it was treasure instead of trouble",
        fade="it slipped away like breath from a windowpane",
        tags={"glamour"},
    ),
    "golden": Glamour(
        id="golden",
        shine="turning every scratch to warm gold",
        promise="that it was richer and newer than any plain old crock",
        fade="the gold ran out of it like sunset leaving the floor",
        tags={"glamour"},
    ),
    "rosy": Glamour(
        id="rosy",
        shine="spreading a rosy bloom over the dull clay",
        promise="that it was friendly and harmless",
        fade="the pink light folded into itself and was gone",
        tags={"glamour"},
    ),
}

HELPER_STYLES = {
    "hush": HelperStyle(
        id="hush",
        guidance="A gentle hand settled over the child's shoulder until the shaking eased.",
        move_text="They set it down carefully, as if the shelf had been waiting all evening.",
        comfort_text='Helper whispered, "There now. We listened, and we were kind. That is how some hauntings end."',
        tags={"kindness"},
    ),
    "lantern": HelperStyle(
        id="lantern",
        guidance="Helper raised a small lantern, and its steady light made the trembling glamour easier to bear.",
        move_text="The lantern shone over their hands while they eased it into place.",
        comfort_text='Helper lowered the lantern and said, "Truth is better than glamour. Even ghosts rest easier by honest light."',
        tags={"light"},
    ),
    "song": HelperStyle(
        id="song",
        guidance="Helper hummed one calm note after another, until the room felt less like a trap and more like a listening place.",
        move_text="The low humming followed them as they tucked it into its old home.",
        comfort_text='The humming stopped, and Helper smiled. "Some old sadness only wanted someone to notice it."',
        tags={"song"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mina", "Ada", "Rose", "Clara", "Etta", "Mabel"]
BOY_NAMES = ["Theo", "Eli", "Ben", "Owen", "Jude", "Noah", "Sam", "Leo"]


@dataclass
class StoryParams:
    room: str
    ghost: str
    crock: str
    glamour: str
    helper_style: str
    child_name: str
    child_gender: str
    helper_type: str
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


KNOWLEDGE = {
    "ghost": [
        ("What is a ghost story?", "A ghost story is a tale about a spirit or haunting. It often feels spooky, but in a gentle story the danger is small and the mystery matters most.")
    ],
    "glamour": [
        ("What is glamour in this story?", "Here, glamour means a magic shine that makes something seem better or prettier than it really is. It can hide the truth for a little while.")
    ],
    "crock": [
        ("What is a crock?", "A crock is a sturdy clay pot or jar. People once used crocks to hold things like jam, milk, or seeds.")
    ],
    "foreshadowing": [
        ("What is foreshadowing?", "Foreshadowing is when a story gives small early clues about something important that will happen later. Those clues help the spooky part feel prepared instead of random.")
    ],
    "jam": [
        ("Why would jam be kept in a crock?", "A crock can hold jam safely and keep it in one place on a shelf. In an old house, a jam crock might be used again and again each season.")
    ],
    "milk": [
        ("Why would milk be kept in a crock?", "Before modern fridges, cool rooms and sturdy crocks helped people keep milk for a while. The crock protected it better than an open bowl.")
    ],
    "seed": [
        ("Why save seeds in a crock?", "Seeds need a dry, safe place if they are being saved for planting later. A covered crock can help keep them together until spring.")
    ],
}
KNOWLEDGE_ORDER = ["ghost", "glamour", "crock", "foreshadowing", "jam", "milk", "seed"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    room = f["room_cfg"]
    ghost = f["ghost_cfg"]
    crock = f["crock_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "glamour" and "crock". Set it in {room.label} and use foreshadowing before the ghost appears.',
        f"Tell a spooky-but-kind story where {child.id} notices small warning signs, finds a glamour over a {crock.label}, and learns why {ghost.label} cannot rest.",
        f"Write a short haunted-house tale in which early clues point to a misplaced crock, and the ending becomes peaceful when the old object is returned home.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    room = f["room_cfg"]
    ghost = f["ghost_cfg"]
    crock = f["crock_cfg"]
    glamour = f["glamour_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {helper.label_word if helper.label_word != 'the helper' else 'a calm grown-up'}, and {ghost.label}. The story centers on an old {crock.label} in {room.label}."
        ),
        (
            "What signs warned that something strange was coming?",
            f"Three little signs came first: {', '.join(f['omens'][:-1])}, and {f['omens'][-1]}. Those clues are foreshadowing because they quietly point to the haunting before the ghost speaks."
        ),
        (
            f"Why did the crock look special at first?",
            f"It was covered by a glamour, {glamour.shine}. The magic shine made the crock seem finer than it really was and hid the trouble in it."
        ),
        (
            "What was wrong with the crock?",
            f"The crock had been moved away from the place where it belonged, and it also had a crack hidden under the glamour. The ghost grew restless because the lost old thing made the room feel wrong."
        ),
        (
            f"Why did the room turn colder when {child.id} lifted the crock?",
            f"The cold came when the misplaced crock was touched and the haunting fully stirred. That happened because the ghost was tied to the crock's old home and wanted it put back."
        ),
        (
            "How was the problem solved?",
            f"They carried the crock back to {room.home_shelf} and set it in its old place. Once it was returned, the glamour faded and the ghost became peaceful."
        ),
        (
            "How did the story end?",
            f"It ended quietly and safely. The room lost its cold, the ghost rested, and the crock looked plain but honest on the shelf."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "glamour", "crock", "foreshadowing"}
    tags |= set(world.facts["crock_cfg"].tags)
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  omens: {world.facts.get('omens', [])}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="pantry",
        ghost="cook",
        crock="jam_crock",
        glamour="golden",
        helper_style="lantern",
        child_name="Nora",
        child_gender="girl",
        helper_type="aunt",
    ),
    StoryParams(
        room="scullery",
        ghost="cook",
        crock="milk_crock",
        glamour="silver",
        helper_style="hush",
        child_name="Theo",
        child_gender="boy",
        helper_type="father",
    ),
    StoryParams(
        room="attic",
        ghost="gardener",
        crock="seed_crock",
        glamour="rosy",
        helper_style="song",
        child_name="Mina",
        child_gender="girl",
        helper_type="uncle",
    ),
    StoryParams(
        room="pantry",
        ghost="grandmother",
        crock="jam_crock",
        glamour="silver",
        helper_style="hush",
        child_name="Ben",
        child_gender="boy",
        helper_type="mother",
    ),
]


ASP_RULES = r"""
matches_room(Room, Crock) :- room_affords(Room, Crock), rightful_room(Crock, Room).
matches_ghost(Ghost, Crock) :- ghost_affinity(Ghost, Crock).
valid(Room, Ghost, Crock) :- matches_room(Room, Crock), matches_ghost(Ghost, Crock).

returned.
peace :- returned.
resolved :- peace.

#show valid/3.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        for crock_id in sorted(room.affords):
            lines.append(asp.fact("room_affords", room_id, crock_id))
    for ghost_id, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", ghost_id))
        for crock_id in sorted(ghost.affinity):
            lines.append(asp.fact("ghost_affinity", ghost_id, crock_id))
    for crock_id, crock in CROCKS.items():
        lines.append(asp.fact("crock", crock_id))
        lines.append(asp.fact("rightful_room", crock_id, crock.rightful_room))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke-tested normal story generation.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in [0, 1, 7, 77]:
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError(f"empty story for seed {seed}")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED for seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a glamour, a crock, and a gentle ghost. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--crock", choices=CROCKS)
    ap.add_argument("--glamour", choices=GLAMOURS)
    ap.add_argument("--helper-style", choices=HELPER_STYLES, dest="helper_style")
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.ghost and args.crock:
        room = ROOMS[args.room]
        ghost = GHOSTS[args.ghost]
        crock = CROCKS[args.crock]
        if not (room_matches_crock(room, crock) and ghost_matches_crock(ghost, crock)):
            raise StoryError(explain_rejection(room, ghost, crock))

    combos = [
        c for c in valid_combos()
        if (args.room is None or c[0] == args.room)
        and (args.ghost is None or c[1] == args.ghost)
        and (args.crock is None or c[2] == args.crock)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, ghost_id, crock_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    glamour = args.glamour or rng.choice(sorted(GLAMOURS.keys()))
    helper_style = args.helper_style or rng.choice(sorted(HELPER_STYLES.keys()))
    return StoryParams(
        room=room_id,
        ghost=ghost_id,
        crock=crock_id,
        glamour=glamour,
        helper_style=helper_style,
        child_name=child_name,
        child_gender=gender,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.ghost not in GHOSTS:
        raise StoryError(f"(Unknown ghost: {params.ghost})")
    if params.crock not in CROCKS:
        raise StoryError(f"(Unknown crock: {params.crock})")
    if params.glamour not in GLAMOURS:
        raise StoryError(f"(Unknown glamour: {params.glamour})")
    if params.helper_style not in HELPER_STYLES:
        raise StoryError(f"(Unknown helper style: {params.helper_style})")
    room = ROOMS[params.room]
    ghost = GHOSTS[params.ghost]
    crock = CROCKS[params.crock]
    if not (room_matches_crock(room, crock) and ghost_matches_crock(ghost, crock)):
        raise StoryError(explain_rejection(room, ghost, crock))

    world = tell(
        room=room,
        ghost_cfg=ghost,
        crock_cfg=crock,
        glamour_cfg=GLAMOURS[params.glamour],
        helper_style=HELPER_STYLES[params.helper_style],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
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
        print(asp_program(show="#show valid/3.\n#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, ghost, crock) combos:\n")
        for room, ghost, crock in combos:
            print(f"  {room:9} {ghost:11} {crock}")
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
            header = f"### {p.child_name}: {p.ghost} / {p.crock} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
