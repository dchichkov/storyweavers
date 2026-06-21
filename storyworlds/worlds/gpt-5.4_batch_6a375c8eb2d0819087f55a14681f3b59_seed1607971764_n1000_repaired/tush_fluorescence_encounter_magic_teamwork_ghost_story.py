#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tush_fluorescence_encounter_magic_teamwork_ghost_story.py
====================================================================================

A standalone storyworld for a gentle ghost story about two children who have a
night-time encounter with a sad ghost. The ghost is not dangerous; it is lonely
because a precious keepsake was lost in the dark. The children must use magic
and teamwork to search for it, calm their fear, and help the ghost rest.

This world uses:
- typed entities with physical meters and emotional memes
- a small forward-chaining causal model
- a reasonableness gate over compatible place/ghost/keepsake/magic choices
- an inline ASP twin for parity checking
- three Q&A sets grounded in simulated state

Required seed words are included in the rendered stories:
- tush
- fluorescence
- encounter
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    entry: str
    texture: str
    hiding_spot: str
    sound: str
    search_difficulty: int
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
class GhostKind:
    id: str
    label: str
    mood: str
    whisper: str
    longing: str
    sadness: int
    places: set[str] = field(default_factory=set)
    keepsakes: set[str] = field(default_factory=set)
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
class Keepsake:
    id: str
    label: str
    phrase: str
    material: str
    places: set[str] = field(default_factory=set)
    glow_line: str = ""
    ending_image: str = ""
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
class MagicAid:
    id: str
    label: str
    phrase: str
    action: str
    reveal_line: str
    power: int
    reveals: set[str] = field(default_factory=set)
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
class TeamworkStyle:
    id: str
    label: str
    bonus: int
    prepare_line: str
    search_line: str
    comfort_line: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "child"]

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


def _r_ghost_chill(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    room = world.get("room")
    if ghost.meters["appeared"] >= THRESHOLD:
        sig = ("ghost_chill",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["chill"] += 1
            for kid in world.kids():
                kid.memes["fear"] += 1
            out.append("__encounter__")
    return out


def _r_reveal_trail(world: World) -> list[str]:
    out: list[str] = []
    magic = world.get("magic")
    keepsake = world.get("keepsake")
    if magic.meters["cast"] >= THRESHOLD and keepsake.meters["revealed"] >= THRESHOLD:
        sig = ("reveal_trail",)
        if sig not in world.fired:
            world.fired.add(sig)
            room = world.get("room")
            room.meters["glow"] += 1
            for kid in world.kids():
                kid.memes["hope"] += 1
            out.append("__glow__")
    return out


def _r_find_keepsake(world: World) -> list[str]:
    out: list[str] = []
    if world.get("room").meters["glow"] < THRESHOLD:
        return out
    if world.facts.get("search_attempt", 0) < 1:
        return out
    keepsake = world.get("keepsake")
    sig = ("find_keepsake",)
    if sig not in world.fired:
        world.fired.add(sig)
        keepsake.meters["found"] += 1
        for kid in world.kids():
            kid.memes["hope"] += 1
        out.append("__found__")
    return out


def _r_soothe_ghost(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    keepsake = world.get("keepsake")
    if keepsake.meters["returned"] >= THRESHOLD and world.facts.get("score", 0) >= world.facts.get("difficulty", 99):
        sig = ("soothe_ghost",)
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.meters["peace"] += 1
            ghost.meters["appeared"] = 0.0
            world.get("room").meters["chill"] = 0.0
            for kid in world.kids():
                kid.memes["fear"] = 0.0
                kid.memes["relief"] += 1
                kid.memes["bravery"] += 1
            out.append("__peace__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="ghost_chill", tag="social", apply=_r_ghost_chill),
    Rule(name="reveal_trail", tag="magic", apply=_r_reveal_trail),
    Rule(name="find_keepsake", tag="search", apply=_r_find_keepsake),
    Rule(name="soothe_ghost", tag="social", apply=_r_soothe_ghost),
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


def compatible(place: Place, ghost: GhostKind, keepsake: Keepsake, magic: MagicAid) -> bool:
    return (
        place.id in ghost.places
        and keepsake.id in ghost.keepsakes
        and place.id in keepsake.places
        and keepsake.material in magic.reveals
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for ghost_id, ghost in GHOSTS.items():
            for keepsake_id, keepsake in KEEPSAKES.items():
                for magic_id, magic in MAGIC.items():
                    if compatible(place, ghost, keepsake, magic):
                        combos.append((place_id, ghost_id, keepsake_id, magic_id))
    return combos


def difficulty_of(place: Place, ghost: GhostKind, hesitate: int) -> int:
    return place.search_difficulty + ghost.sadness + hesitate


def score_of(magic: MagicAid, teamwork: TeamworkStyle) -> int:
    return magic.power + teamwork.bonus


def outcome_of(params: "StoryParams") -> str:
    place = PLACES[params.place]
    ghost = GHOSTS[params.ghost]
    magic = MAGIC[params.magic]
    teamwork = TEAMWORK[params.teamwork]
    return "rested" if score_of(magic, teamwork) >= difficulty_of(place, ghost, params.hesitate) else "waiting"


def explain_rejection(place: Place, ghost: GhostKind, keepsake: Keepsake, magic: MagicAid) -> str:
    if place.id not in ghost.places:
        return (
            f"(No story: {ghost.label} does not belong in {place.label}. "
            f"Choose a ghost that plausibly haunts that place.)"
        )
    if keepsake.id not in ghost.keepsakes:
        return (
            f"(No story: {ghost.label} is not searching for {keepsake.phrase}. "
            f"Pick a keepsake tied to that ghost.)"
        )
    if place.id not in keepsake.places:
        return (
            f"(No story: {keepsake.phrase} is not a plausible thing to lose in {place.label}. "
            f"Pick a keepsake that fits the place.)"
        )
    if keepsake.material not in magic.reveals:
        return (
            f"(No story: {magic.phrase} cannot reveal a {keepsake.material} keepsake. "
            f"Choose magic that could honestly find it.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


def predict_search(world: World, magic: MagicAid, teamwork: TeamworkStyle, hesitate: int) -> dict:
    sim = world.copy()
    sim.facts["score"] = score_of(magic, teamwork)
    sim.facts["difficulty"] = difficulty_of(sim.place, GHOSTS[sim.facts["ghost_cfg"].id], hesitate)
    sim.get("magic").meters["cast"] += 1
    sim.get("keepsake").meters["revealed"] += 1
    sim.facts["search_attempt"] = 1
    propagate(sim, narrate=False)
    sim.get("keepsake").meters["returned"] += 1
    propagate(sim, narrate=False)
    return {
        "found": sim.get("keepsake").meters["found"] >= THRESHOLD,
        "rested": sim.get("ghost").meters["peace"] >= THRESHOLD,
        "difficulty": sim.facts["difficulty"],
        "score": sim.facts["score"],
    }


def introduce(world: World, kid1: Entity, kid2: Entity, place: Place, teamwork: TeamworkStyle) -> None:
    for kid in (kid1, kid2):
        kid.memes["curiosity"] += 1
        kid.memes["together"] += 1
    world.say(
        f"At dusk, {kid1.id} and {kid2.id} slipped into {place.label}. "
        f"{place.entry} {place.texture}"
    )
    world.say(
        f"They had promised to stay close, and {teamwork.prepare_line} made the dark feel smaller."
    )


def hear_ghost(world: World, kid1: Entity, kid2: Entity, place: Place, ghost: GhostKind) -> None:
    ghost_ent = world.get("ghost")
    ghost_ent.meters["appeared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {place.sound}, and a pale shape gathered itself by {place.hiding_spot}. "
        f"It was {ghost.label}, looking {ghost.mood}."
    )
    world.say(
        f'This was their real encounter with a ghost, and for one heartbeat neither child moved. '
        f'"Please don\'t run," whispered the ghost. "{ghost.whisper}"'
    )
    kid2.memes["fear"] += 1
    world.say(
        f"{kid2.id} jumped backward and landed on {kid2.pronoun('possessive')} tush with a soft thump, "
        f"which would have been funny if the room had not turned so cold."
    )


def choose_to_help(world: World, kid1: Entity, kid2: Entity, ghost: GhostKind, keepsake: Keepsake) -> None:
    for kid in (kid1, kid2):
        kid.memes["kindness"] += 1
    world.say(
        f"{kid1.id} swallowed hard, then asked what was wrong. "
        f'The ghost folded misty hands and said it could not rest because {ghost.longing} '
        f"had lost {keepsake.phrase}."
    )
    world.say(
        f"{kid2.id} scooted up from the floor, rubbed {kid2.pronoun('possessive')} knees, "
        f"and chose to stay. If they helped together, the ghost might not have to be lonely anymore."
    )


def cast_magic(world: World, kid1: Entity, kid2: Entity, magic: MagicAid, teamwork: TeamworkStyle, hesitate: int) -> None:
    pred = predict_search(world, magic, teamwork, hesitate)
    world.facts["difficulty"] = pred["difficulty"]
    world.facts["score"] = pred["score"]
    world.get("magic").meters["cast"] += 1
    world.get("keepsake").meters["revealed"] += 1
    propagate(world, narrate=False)
    for kid in (kid1, kid2):
        kid.memes["bravery"] += 1
    pause = ""
    if hesitate == 1:
        pause = " They paused for one shaky breath before they began."
    elif hesitate == 2:
        pause = " They paused twice, listening to every creak, before they dared to begin."
    world.say(
        f'{kid1.id} lifted {magic.phrase}, and {kid2.id} joined in as {teamwork.search_line}. '
        f"{magic.action}.{pause}"
    )
    world.say(
        f"{magic.reveal_line} A ribbon of fluorescence shimmered through the dark and curled toward {world.place.hiding_spot}."
    )


def search(world: World, kid1: Entity, kid2: Entity, keepsake: Keepsake) -> None:
    world.facts["search_attempt"] = 1
    propagate(world, narrate=False)
    if world.get("keepsake").meters["found"] >= THRESHOLD:
        world.say(
            f"Following the glow, {kid1.id} knelt while {kid2.id} reached deep into the shadows. "
            f"Together they found {keepsake.phrase} tucked away where no living eyes had noticed it."
        )
    else:
        world.say(
            f"They followed the glow as far as they could and brushed dust from old boards and jars, "
            f"but the dark still felt thicker than their courage."
        )


def return_keepsake(world: World, kid1: Entity, kid2: Entity, keepsake: Keepsake, teamwork: TeamworkStyle) -> None:
    if world.get("keepsake").meters["found"] < THRESHOLD:
        return
    world.get("keepsake").meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{kid1.id} held out {keepsake.phrase}, and {kid2.id} added a soft promise: {teamwork.comfort_line}"
    )


def peaceful_ending(world: World, kid1: Entity, kid2: Entity, ghost: GhostKind, keepsake: Keepsake, teamwork: TeamworkStyle) -> None:
    world.say(
        f"The ghost touched {keepsake.label} to its chest. The chill thinned at once, and the room filled with a warm little glow."
    )
    world.say(
        f'"Thank you," the ghost whispered. "You were brave enough to help, and kind enough to do it together." '
        f"{keepsake.ending_image}"
    )
    world.say(
        f"When {kid1.id} and {kid2.id} stepped back into the night, the place no longer felt scary. "
        f"It felt remembered, and their teamwork turned the tale into a gentle one."
    )


def wistful_ending(world: World, kid1: Entity, kid2: Entity, ghost: GhostKind, magic: MagicAid, teamwork: TeamworkStyle) -> None:
    for kid in (kid1, kid2):
        kid.memes["resolve"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"The glow faded before they could reach the hidden place. Still, the ghost's face softened when it saw they had truly tried."
    )
    world.say(
        f'"You were kind to stay," the ghost said. "Come back with stronger help, and perhaps I can rest at last." '
        f"{kid1.id} and {kid2.id} nodded, already planning to return with {magic.phrase} and {teamwork.label} once more."
    )
    world.say(
        f"As they left, the cold was less sharp. The ghost was still waiting, but now it was waiting with hope."
    )


def tell(
    place: Place,
    ghost_cfg: GhostKind,
    keepsake_cfg: Keepsake,
    magic_cfg: MagicAid,
    teamwork_cfg: TeamworkStyle,
    *,
    kid1_name: str = "Mina",
    kid1_gender: str = "girl",
    kid2_name: str = "Owen",
    kid2_gender: str = "boy",
    relation: str = "friends",
    hesitate: int = 0,
) -> World:
    world = World(place)
    kid1 = world.add(Entity(id=kid1_name, kind="character", type=kid1_gender, role="child", label=kid1_name, attrs={"relation": relation}))
    kid2 = world.add(Entity(id=kid2_name, kind="character", type=kid2_gender, role="child", label=kid2_name, attrs={"relation": relation}))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", role="ghost", label=ghost_cfg.label, tags=set(ghost_cfg.tags)))
    keepsake = world.add(Entity(id="keepsake", kind="thing", type="keepsake", label=keepsake_cfg.label, tags=set(keepsake_cfg.tags)))
    magic = world.add(Entity(id="magic", kind="thing", type="magic", label=magic_cfg.label, tags=set(magic_cfg.tags)))
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.label, tags=set(place.tags)))

    world.facts["ghost_cfg"] = ghost_cfg
    world.facts["keepsake_cfg"] = keepsake_cfg
    world.facts["magic_cfg"] = magic_cfg
    world.facts["teamwork_cfg"] = teamwork_cfg
    world.facts["search_attempt"] = 0
    world.facts["difficulty"] = difficulty_of(place, ghost_cfg, hesitate)
    world.facts["score"] = score_of(magic_cfg, teamwork_cfg)
    world.facts["hesitate"] = hesitate
    world.facts["relation"] = relation

    introduce(world, kid1, kid2, place, teamwork_cfg)
    world.para()
    hear_ghost(world, kid1, kid2, place, ghost_cfg)
    choose_to_help(world, kid1, kid2, ghost_cfg, keepsake_cfg)
    world.para()
    cast_magic(world, kid1, kid2, magic_cfg, teamwork_cfg, hesitate)
    search(world, kid1, kid2, keepsake_cfg)
    return_keepsake(world, kid1, kid2, keepsake_cfg, teamwork_cfg)
    world.para()

    outcome = "rested" if ghost.meters["peace"] >= THRESHOLD else "waiting"
    if outcome == "rested":
        peaceful_ending(world, kid1, kid2, ghost_cfg, keepsake_cfg, teamwork_cfg)
    else:
        wistful_ending(world, kid1, kid2, ghost_cfg, magic_cfg, teamwork_cfg)

    world.facts.update(
        place=place,
        kid1=kid1,
        kid2=kid2,
        ghost=ghost,
        keepsake=keepsake,
        magic=magic,
        teamwork=teamwork_cfg,
        found=keepsake.meters["found"] >= THRESHOLD,
        returned=keepsake.meters["returned"] >= THRESHOLD,
        outcome=outcome,
        peaceful=ghost.meters["peace"] >= THRESHOLD,
    )
    return world


PLACES = {
    "attic": Place(
        id="attic",
        label="the old attic",
        entry="The rafters leaned overhead like sleepy giants.",
        texture="Dust floated in the narrow moonbeams, and every trunk seemed to be holding a secret.",
        hiding_spot="a cracked cedar trunk",
        sound="a slow creak traveled along the beams",
        search_difficulty=2,
        tags={"attic", "night"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the moonlit greenhouse",
        entry="Glass walls gleamed with silver drops from the evening mist.",
        texture="Tall leaves brushed the panes, and shadows of vines swung gently over the path.",
        hiding_spot="a tipped clay pot beneath the fern table",
        sound="the hanging panes gave a tiny ringing sigh",
        search_difficulty=1,
        tags={"greenhouse", "night"},
    ),
    "boathouse": Place(
        id="boathouse",
        label="the creaky boathouse",
        entry="The boards smelled of pond water and old rope.",
        texture="Oars rested against the wall, and black water winked through the slats below.",
        hiding_spot="a coil of rope beside the skiff",
        sound="the tied boat knocked softly under the floor",
        search_difficulty=3,
        tags={"boathouse", "night"},
    ),
}

GHOSTS = {
    "seamstress": GhostKind(
        id="seamstress",
        label="a seamstress ghost",
        mood="small and worried",
        whisper="I have searched and searched, but I cannot find what I once held close.",
        longing="the seamstress ghost",
        sadness=1,
        places={"attic"},
        keepsakes={"thimble", "lace_key"},
        tags={"ghost", "attic"},
    ),
    "gardener": GhostKind(
        id="gardener",
        label="a gardener ghost",
        mood="dew-soft and sad",
        whisper="The flowers still wake each dawn, but I have lost the little thing that opened my favorite gate.",
        longing="the gardener ghost",
        sadness=1,
        places={"greenhouse"},
        keepsakes={"lace_key", "moon_seed"},
        tags={"ghost", "garden"},
    ),
    "boat_child": GhostKind(
        id="boat_child",
        label="a boat-child ghost",
        mood="dripping and wistful",
        whisper="The pond remembers my songs, but I cannot remember where my small treasure slipped away.",
        longing="the boat-child ghost",
        sadness=2,
        places={"boathouse"},
        keepsakes={"brass_compass", "moon_seed"},
        tags={"ghost", "water"},
    ),
}

KEEPSAKES = {
    "thimble": Keepsake(
        id="thimble",
        label="thimble",
        phrase="a silver thimble",
        material="silver",
        places={"attic"},
        glow_line="The silver edge answered the spell with a shy blink.",
        ending_image="The silver thimble shone once, and then the ghost looked as light as a folded handkerchief in a breeze.",
        tags={"silver", "sewing"},
    ),
    "lace_key": Keepsake(
        id="lace_key",
        label="key",
        phrase="a tiny lace key",
        material="brass",
        places={"attic", "greenhouse"},
        glow_line="A tiny brass shape winked under the dust.",
        ending_image="The little key flashed gold, and every leaf and board around it seemed to sigh with relief.",
        tags={"brass", "key"},
    ),
    "moon_seed": Keepsake(
        id="moon_seed",
        label="seed",
        phrase="a glass moon-seed",
        material="glass",
        places={"greenhouse", "boathouse"},
        glow_line="The glass bead caught the spell and glimmered like a drop of captured moonlight.",
        ending_image="The moon-seed glowed softly, and the whole place looked less haunted and more loved.",
        tags={"glass", "garden"},
    ),
    "brass_compass": Keepsake(
        id="brass_compass",
        label="compass",
        phrase="a brass compass",
        material="brass",
        places={"boathouse"},
        glow_line="A dull brass circle trembled with light beneath the rope.",
        ending_image="The compass needle steadied, and the ghost's smile pointed home at last.",
        tags={"brass", "water"},
    ),
}

MAGIC = {
    "moon_hum": MagicAid(
        id="moon_hum",
        label="moon hum",
        phrase="their moon hum spell",
        action="They hummed one note together until the dark itself seemed to listen",
        reveal_line="The note skimmed across wood and glass",
        power=2,
        reveals={"silver", "glass"},
        tags={"magic", "song"},
    ),
    "chalk_rune": MagicAid(
        id="chalk_rune",
        label="chalk rune",
        phrase="a loop of glowing chalk",
        action="They drew a careful circle and tapped it twice",
        reveal_line="The chalk mark breathed out a searching glow",
        power=3,
        reveals={"brass", "silver", "glass"},
        tags={"magic", "chalk"},
    ),
    "mirror_blink": MagicAid(
        id="mirror_blink",
        label="mirror blink",
        phrase="a palm-sized mirror blink charm",
        action="They tilted the little mirror toward the shadows until it flashed",
        reveal_line="The brief flash scattered bright crumbs of light",
        power=1,
        reveals={"silver", "glass"},
        tags={"magic", "mirror"},
    ),
    "lantern_whisper": MagicAid(
        id="lantern_whisper",
        label="lantern whisper",
        phrase="an old lantern whisper charm",
        action="They breathed into the lantern together, and a pearly flame woke inside it",
        reveal_line="The pearly flame floated low to the ground",
        power=2,
        reveals={"brass", "glass"},
        tags={"magic", "lantern"},
    ),
}

TEAMWORK = {
    "hand_in_hand": TeamworkStyle(
        id="hand_in_hand",
        label="hand-in-hand courage",
        bonus=1,
        prepare_line="holding hands",
        search_line="they moved hand in hand so neither one had to be brave alone",
        comfort_line='"We found it together, so you do not have to be lonely alone."',
        tags={"teamwork"},
    ),
    "echo_song": TeamworkStyle(
        id="echo_song",
        label="an echo song",
        bonus=2,
        prepare_line="practicing their little echo song",
        search_line="they traded each line of the spell back and forth like a song",
        comfort_line='"We kept answering each other, and now we are answering you too."',
        tags={"teamwork", "song"},
    ),
    "split_search": TeamworkStyle(
        id="split_search",
        label="a split search plan",
        bonus=3,
        prepare_line="making a careful plan before taking one step",
        search_line="one child watched the glow while the other checked each hiding place, then they switched",
        comfort_line='"One of us looked, one of us listened, and both of us stayed."',
        tags={"teamwork", "plan"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Tess", "Wren", "Ava", "Zoe"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Finn", "Jude", "Max", "Theo", "Sam"]
RELATIONS = ["friends", "siblings"]


@dataclass
class StoryParams:
    place: str
    ghost: str
    keepsake: str
    magic: str
    teamwork: str
    kid1_name: str
    kid1_gender: str
    kid2_name: str
    kid2_gender: str
    relation: str
    hesitate: int = 0
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
        (
            "What is a ghost in a gentle story?",
            "In a gentle ghost story, a ghost is often a spirit from long ago who needs help, not a monster who wants to hurt people. The spooky feeling comes from mystery and sadness more than danger."
        )
    ],
    "magic": [
        (
            "What does magic do in this story world?",
            "Magic helps hidden things show themselves, like a trail, a glow, or a clue. It does not solve everything alone, because the children still have to be brave and work together."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means two or more people helping each other toward one goal. They share jobs, listen, and keep going together instead of one person doing everything."
        )
    ],
    "fluorescence": [
        (
            "What is fluorescence?",
            "Fluorescence is when something gives off a glowing light after it is excited by energy. In stories, that kind of glow can make magic feel bright and mysterious."
        )
    ],
    "attic": [
        (
            "What is an attic?",
            "An attic is a space up under the roof of a house. People often store old trunks, boxes, and keepsakes there."
        )
    ],
    "greenhouse": [
        (
            "What is a greenhouse?",
            "A greenhouse is a glass house for growing plants. The glass lets in light and helps the plants stay warm."
        )
    ],
    "boathouse": [
        (
            "What is a boathouse?",
            "A boathouse is a little building near water where boats, ropes, and oars are kept. It can sound creaky because wood and water move together."
        )
    ],
    "silver": [
        (
            "Why might silver shine in the dark?",
            "Silver is a bright metal that reflects light very well. Even a small bit of moonlight can make it glimmer."
        )
    ],
    "brass": [
        (
            "What is brass?",
            "Brass is a yellow-gold metal. People use it to make keys, bells, and other sturdy little objects."
        )
    ],
    "glass": [
        (
            "Why does glass sparkle?",
            "Glass can catch and bend light, so it can sparkle when even a tiny glow reaches it. That is why glass objects often look magical in stories."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ghost",
    "magic",
    "teamwork",
    "fluorescence",
    "attic",
    "greenhouse",
    "boathouse",
    "silver",
    "brass",
    "glass",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid1 = f["kid1"]
    kid2 = f["kid2"]
    place = f["place"]
    ghost = f["ghost_cfg"]
    keepsake = f["keepsake_cfg"]
    if f["outcome"] == "rested":
        return [
            f'Write a gentle ghost story for a 3-to-5-year-old where two children have an encounter with {ghost.label} in {place.label} and use magic plus teamwork to help it rest. Include the words "tush" and "fluorescence".',
            f"Tell a child-friendly spooky story where {kid1.id} and {kid2.id} find {keepsake.phrase} for {ghost.label}, and the ending proves the place feels peaceful afterward.",
            f'Write a soft ghost tale where fear turns into kindness, and two children solve the mystery together instead of running away.'
        ]
    return [
        f'Write a gentle-but-spooky story where two children meet {ghost.label} in {place.label}, try to help with magic, and promise to come back. Include the word "encounter".',
        f"Tell a child-friendly ghost story where {kid1.id} and {kid2.id} stay kind even though they cannot finish the job on the first night.",
        f'Write a story about teamwork in a haunted place where the children leave with hope instead of fear.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid1 = f["kid1"]
    kid2 = f["kid2"]
    place = f["place"]
    ghost_cfg = f["ghost_cfg"]
    keepsake_cfg = f["keepsake_cfg"]
    magic_cfg = f["magic_cfg"]
    teamwork_cfg = f["teamwork_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {kid1.id} and {kid2.id}, two children who explored {place.label} together. It is also about {ghost_cfg.label}, a sad ghost who needed help."
        ),
        (
            "What happened when the children met the ghost?",
            f"They had a real encounter with {ghost_cfg.label}, and the room turned cold with surprise. {kid2.id} was so startled that {kid2.pronoun('subject')} landed on {kid2.pronoun('possessive')} tush before deciding to stay and listen."
        ),
        (
            "Why was the ghost sad?",
            f"The ghost was sad because it had lost {keepsake_cfg.phrase}. Without that keepsake, the ghost felt unfinished and could not rest."
        ),
        (
            "How did the children try to help?",
            f"They used {magic_cfg.phrase} while working with {teamwork_cfg.label}. The magic revealed a glowing clue, and their teamwork let them keep going even while they were scared."
        ),
    ]
    if f["found"]:
        qa.append(
            (
                "How did they find the keepsake?",
                f"The magic made a trail of fluorescence through the dark, and the children followed it together. Because one watched the glow while the other searched the hiding place, they found {keepsake_cfg.phrase} at last."
            )
        )
    else:
        qa.append(
            (
                "Why could they not finish the search that night?",
                f"The children really tried, but the hidden place was harder than their first spell and courage could manage. Even so, their kindness mattered because it gave the ghost hope instead of leaving it alone."
            )
        )
    if f["outcome"] == "rested":
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully: the children returned {keepsake_cfg.phrase}, and the ghost finally rested. The warm glow at the end shows that the haunted place had changed."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with a promise instead of a full fix. The ghost was still waiting, but it was waiting hopefully because the children promised to come back."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "magic", "teamwork", "fluorescence", f["place"].id, f["keepsake_cfg"].material}
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} score={world.facts.get('score')} difficulty={world.facts.get('difficulty')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        ghost="seamstress",
        keepsake="thimble",
        magic="moon_hum",
        teamwork="echo_song",
        kid1_name="Mina",
        kid1_gender="girl",
        kid2_name="Owen",
        kid2_gender="boy",
        relation="friends",
        hesitate=0,
    ),
    StoryParams(
        place="greenhouse",
        ghost="gardener",
        keepsake="moon_seed",
        magic="lantern_whisper",
        teamwork="hand_in_hand",
        kid1_name="Ivy",
        kid1_gender="girl",
        kid2_name="Sam",
        kid2_gender="boy",
        relation="siblings",
        hesitate=0,
    ),
    StoryParams(
        place="boathouse",
        ghost="boat_child",
        keepsake="brass_compass",
        magic="chalk_rune",
        teamwork="split_search",
        kid1_name="Tess",
        kid1_gender="girl",
        kid2_name="Finn",
        kid2_gender="boy",
        relation="friends",
        hesitate=1,
    ),
    StoryParams(
        place="boathouse",
        ghost="boat_child",
        keepsake="moon_seed",
        magic="lantern_whisper",
        teamwork="hand_in_hand",
        kid1_name="Lila",
        kid1_gender="girl",
        kid2_name="Jude",
        kid2_gender="boy",
        relation="friends",
        hesitate=2,
    ),
    StoryParams(
        place="attic",
        ghost="seamstress",
        keepsake="lace_key",
        magic="chalk_rune",
        teamwork="hand_in_hand",
        kid1_name="Nora",
        kid1_gender="girl",
        kid2_name="Theo",
        kid2_gender="boy",
        relation="siblings",
        hesitate=1,
    ),
]


ASP_RULES = r"""
valid(P,G,K,M) :- place(P), ghost(G), keepsake(K), magic(M),
                  haunts(G,P), wants(G,K), hidden_in(K,P),
                  material(K,Mat), reveals(M,Mat).

difficulty(D) :- chosen_place(P), chosen_ghost(G), hesitate(H),
                 search_difficulty(P,PD), sadness(G,SD), D = PD + SD + H.

score(S) :- chosen_magic(M), chosen_teamwork(T),
            power(M,MP), bonus(T,TB), S = MP + TB.

outcome(rested) :- score(S), difficulty(D), S >= D.
outcome(waiting) :- score(S), difficulty(D), S < D.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("search_difficulty", place_id, place.search_difficulty))
    for ghost_id, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", ghost_id))
        lines.append(asp.fact("sadness", ghost_id, ghost.sadness))
        for place_id in sorted(ghost.places):
            lines.append(asp.fact("haunts", ghost_id, place_id))
        for keepsake_id in sorted(ghost.keepsakes):
            lines.append(asp.fact("wants", ghost_id, keepsake_id))
    for keepsake_id, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", keepsake_id))
        lines.append(asp.fact("material", keepsake_id, keepsake.material))
        for place_id in sorted(keepsake.places):
            lines.append(asp.fact("hidden_in", keepsake_id, place_id))
    for magic_id, magic in MAGIC.items():
        lines.append(asp.fact("magic", magic_id))
        lines.append(asp.fact("power", magic_id, magic.power))
        for material in sorted(magic.reveals):
            lines.append(asp.fact("reveals", magic_id, material))
    for teamwork_id, teamwork in TEAMWORK.items():
        lines.append(asp.fact("teamwork", teamwork_id))
        lines.append(asp.fact("bonus", teamwork_id, teamwork.bonus))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_ghost", params.ghost),
            asp.fact("chosen_magic", params.magic),
            asp.fact("chosen_teamwork", params.teamwork),
            asp.fact("hesitate", params.hesitate),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcome calculations differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: generate() smoke test succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story world: two children, one sad ghost, magic, and teamwork."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--teamwork", choices=TEAMWORK)
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("--hesitate", type=int, choices=[0, 1, 2], help="how many shaky pauses the children take before searching")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.ghost and args.keepsake and args.magic:
        place = PLACES[args.place]
        ghost = GHOSTS[args.ghost]
        keepsake = KEEPSAKES[args.keepsake]
        magic = MAGIC[args.magic]
        if not compatible(place, ghost, keepsake, magic):
            raise StoryError(explain_rejection(place, ghost, keepsake, magic))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.ghost is None or combo[1] == args.ghost)
        and (args.keepsake is None or combo[2] == args.keepsake)
        and (args.magic is None or combo[3] == args.magic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, ghost_id, keepsake_id, magic_id = rng.choice(sorted(combos))
    teamwork_id = args.teamwork or rng.choice(sorted(TEAMWORK))
    relation = args.relation or rng.choice(RELATIONS)
    hesitate = args.hesitate if args.hesitate is not None else rng.randint(0, 2)

    kid1_gender = rng.choice(["girl", "boy"])
    kid2_gender = rng.choice(["girl", "boy"])
    kid1_name = _pick_name(rng, kid1_gender)
    kid2_name = _pick_name(rng, kid2_gender, avoid=kid1_name)

    return StoryParams(
        place=place_id,
        ghost=ghost_id,
        keepsake=keepsake_id,
        magic=magic_id,
        teamwork=teamwork_id,
        kid1_name=kid1_name,
        kid1_gender=kid1_gender,
        kid2_name=kid2_name,
        kid2_gender=kid2_gender,
        relation=relation,
        hesitate=hesitate,
    )


def generate(params: StoryParams) -> StorySample:
    missing = [name for name, table in {
        "place": PLACES,
        "ghost": GHOSTS,
        "keepsake": KEEPSAKES,
        "magic": MAGIC,
        "teamwork": TEAMWORK,
    }.items() if getattr(params, name) not in table]
    if missing:
        raise StoryError(f"(Invalid params: unknown {', '.join(missing)}.)")

    place = PLACES[params.place]
    ghost = GHOSTS[params.ghost]
    keepsake = KEEPSAKES[params.keepsake]
    magic = MAGIC[params.magic]
    teamwork = TEAMWORK[params.teamwork]
    if not compatible(place, ghost, keepsake, magic):
        raise StoryError(explain_rejection(place, ghost, keepsake, magic))

    world = tell(
        place,
        ghost,
        keepsake,
        magic,
        teamwork,
        kid1_name=params.kid1_name,
        kid1_gender=params.kid1_gender,
        kid2_name=params.kid2_name,
        kid2_gender=params.kid2_gender,
        relation=params.relation,
        hesitate=params.hesitate,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, ghost, keepsake, magic) combos:\n")
        for place, ghost, keepsake, magic in combos:
            print(f"  {place:10} {ghost:11} {keepsake:13} {magic}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.kid1_name} & {p.kid2_name}: {p.ghost} in {p.place} ({p.magic}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
