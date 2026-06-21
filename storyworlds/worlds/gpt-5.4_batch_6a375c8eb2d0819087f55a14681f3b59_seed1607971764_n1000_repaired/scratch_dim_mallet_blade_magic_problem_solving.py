#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/scratch_dim_mallet_blade_magic_problem_solving.py
============================================================================

A standalone storyworld for a gentle ghost-story domain: a child in an old house
finds a lamp gone "scratch-dim", meets a lonely but friendly ghost, and solves a
small magical problem with a grown-up's help. The hidden keepsake that will wake
the light is shut inside a box, and the seal decides whether a mallet, a blade,
or both are needed.

The world model drives the prose:
- a scratch-dim lamp makes the room darker and the ghost lonelier
- opening the box reveals the right magical keepsake
- returning the keepsake to the lamp restores the glow
- the restored light lets the ghost rest peacefully

Run it
------
    python storyworlds/worlds/gpt-5.4/scratch_dim_mallet_blade_magic_problem_solving.py
    python storyworlds/worlds/gpt-5.4/scratch_dim_mallet_blade_magic_problem_solving.py --room attic --ghost tailor_ghost --seal mixed
    python storyworlds/worlds/gpt-5.4/scratch_dim_mallet_blade_magic_problem_solving.py --ghost cat_ghost --room nursery
    python storyworlds/worlds/gpt-5.4/scratch_dim_mallet_blade_magic_problem_solving.py --all
    python storyworlds/worlds/gpt-5.4/scratch_dim_mallet_blade_magic_problem_solving.py --qa --json
    python storyworlds/worlds/gpt-5.4/scratch_dim_mallet_blade_magic_problem_solving.py --asp
    python storyworlds/worlds/gpt-5.4/scratch_dim_mallet_blade_magic_problem_solving.py --verify
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def elder_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class RoomCfg:
    id: str
    label: str
    approach: str
    detail: str
    hiding_place: str
    ending_image: str
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
class GhostCfg:
    id: str
    label: str
    home: str
    whisper: str
    memory: str
    rest_line: str
    charm_id: str
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
class CharmCfg:
    id: str
    label: str
    phrase: str
    magic_effect: str
    belongs_to: str
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
class SealCfg:
    id: str
    label: str
    needs: tuple[str, ...]
    shelf_text: str
    open_text: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "used_tools": [],
            "opened": False,
            "restored": False,
            "rested": False,
            "predicted_dark": 0,
        }

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


def _r_dim(world: World) -> list[str]:
    lamp = world.get("lamp")
    room = world.get("room")
    child = world.get("child")
    ghost = world.get("ghost")
    if lamp.meters["scratch_dim"] < THRESHOLD:
        return []
    sig = ("dim",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["darkness"] += 1
    child.memes["fear"] += 1
    ghost.memes["longing"] += 1
    return []


def _r_restore(world: World) -> list[str]:
    lamp = world.get("lamp")
    room = world.get("room")
    child = world.get("child")
    ghost = world.get("ghost")
    if lamp.meters["glow"] < THRESHOLD or ghost.meters["guided"] < THRESHOLD:
        return []
    sig = ("restore",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["darkness"] = 0.0
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    ghost.memes["peace"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="dim", tag="magic", apply=_r_dim),
    Rule(name="restore", tag="magic", apply=_r_restore),
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


ROOMS = {
    "attic": RoomCfg(
        id="attic",
        label="the attic",
        approach="up the narrow stairs to the attic",
        detail="The beams smelled of old cedar, and moonlight lay in thin bars across the floor.",
        hiding_place="inside a trunk under the slanting roof",
        ending_image="By the window, the attic looked less like a place for shivers and more like a place where stories could sleep.",
        tags={"attic"},
    ),
    "nursery": RoomCfg(
        id="nursery",
        label="the nursery",
        approach="down the quiet hall to the nursery",
        detail="A row of wooden toys watched from a shelf, and the wallpaper moons seemed to blink in the dark.",
        hiding_place="inside a toy chest beside the rocker",
        ending_image="The nursery glowed softly, and the little shadows under the crib looked ordinary again.",
        tags={"nursery"},
    ),
    "stairhall": RoomCfg(
        id="stairhall",
        label="the stair hall",
        approach="to the stair hall where the steps turned in a square",
        detail="Each banister post made a long black stripe, and the air smelled faintly of rain and polish.",
        hiding_place="inside a cupboard beneath the stairs",
        ending_image="The stair hall shone from top step to bottom, and no corner seemed lost anymore.",
        tags={"stairs"},
    ),
}

GHOSTS = {
    "tailor_ghost": GhostCfg(
        id="tailor_ghost",
        label="a tailor ghost",
        home="attic",
        whisper='A soft voice said, "I cannot find my moon-spool, and the lamp has gone scratch-dim."',
        memory="once measured cloth by lamplight",
        rest_line="The tailor ghost folded into the light like a sigh and finally looked done with wandering.",
        charm_id="moon_spool",
        tags={"ghost", "tailor"},
    ),
    "lullaby_ghost": GhostCfg(
        id="lullaby_ghost",
        label="a lullaby ghost",
        home="nursery",
        whisper='A humming voice said, "My music key is hidden away, and without it the lamp stays scratch-dim."',
        memory="once rocked sleepy babies to bed",
        rest_line="The lullaby ghost hummed one last warm note and grew still, as peaceful as a child already dreaming.",
        charm_id="music_key",
        tags={"ghost", "song"},
    ),
    "cat_ghost": GhostCfg(
        id="cat_ghost",
        label="a cat ghost",
        home="stairhall",
        whisper='A small silver cat shape blinked and seemed to say, "My stair bell is gone, and the lamp has gone scratch-dim."',
        memory="once padded up and down the stairs every night",
        rest_line="The cat ghost curled into a pale comma on the warm step and stopped looking for anything at all.",
        charm_id="stair_bell",
        tags={"ghost", "cat"},
    ),
}

CHARMS = {
    "moon_spool": CharmCfg(
        id="moon_spool",
        label="moon-spool",
        phrase="a little moon-spool wound with silver thread",
        magic_effect="The silver thread drank the scratches out of the glass as if it were sipping them away.",
        belongs_to="tailor_ghost",
        tags={"magic", "thread"},
    ),
    "music_key": CharmCfg(
        id="music_key",
        label="music key",
        phrase="a music key no bigger than a thumb",
        magic_effect="When the key touched the lamp, the faintest lullaby slipped through the room and the scratches melted away.",
        belongs_to="lullaby_ghost",
        tags={"magic", "music"},
    ),
    "stair_bell": CharmCfg(
        id="stair_bell",
        label="stair bell",
        phrase="a brass stair bell with a blue ribbon loop",
        magic_effect="The tiny bell gave one bright note, and the scratches skittered off the glass like beetles fleeing the dawn.",
        belongs_to="cat_ghost",
        tags={"magic", "bell"},
    ),
}

SEALS = {
    "nails": SealCfg(
        id="nails",
        label="tiny brass nails",
        needs=("mallet",),
        shelf_text="On a folded cloth nearby lay a small mallet and a careful little blade, waiting for the right job.",
        open_text="The box was fastened with tiny brass nails. The grown-up used the mallet in gentle taps until the lid loosened with a dry little click, while the blade stayed on the cloth, not needed after all.",
        qa_text="The grown-up used the mallet to tap the tiny nails loose and open the box.",
        tags={"mallet"},
    ),
    "twine": SealCfg(
        id="twine",
        label="silver twine",
        needs=("blade",),
        shelf_text="On a folded cloth nearby lay a small mallet and a careful little blade, waiting for the right job.",
        open_text="The box was wrapped in silver twine knotted hard as frost. The grown-up kept the mallet aside and used the blade to snip the twine cleanly, and the lid sprang up a finger-width.",
        qa_text="The grown-up used the blade to cut the silver twine and open the box.",
        tags={"blade"},
    ),
    "mixed": SealCfg(
        id="mixed",
        label="a bent hasp and a loop of twine",
        needs=("mallet", "blade"),
        shelf_text="On a folded cloth nearby lay a small mallet and a careful little blade, because this old house loved problems with more than one part.",
        open_text="The box had a bent little hasp and a loop of silver twine. First the grown-up tapped the crooked metal straight with the mallet, and then used the blade to nick the twine, so the lid could open at last.",
        qa_text="The grown-up used the mallet first and the blade second, because the box had two different kinds of seal.",
        tags={"mallet", "blade"},
    ),
}

GIRL_NAMES = ["Mina", "Elsie", "Nora", "Lucy", "Rose", "Ada", "Ivy", "Clara"]
BOY_NAMES = ["Owen", "Eli", "Theo", "Finn", "Milo", "Jasper", "Noah", "Hugo"]
TRAITS = ["careful", "curious", "steady", "brave", "thoughtful", "gentle"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for room_id, room in ROOMS.items():
        for ghost_id, ghost in GHOSTS.items():
            if ghost.home != room_id:
                continue
            for charm_id, charm in CHARMS.items():
                if charm.belongs_to != ghost_id:
                    continue
                for seal_id in SEALS:
                    combos.append((room_id, ghost_id, charm_id, seal_id))
    return combos


def explain_rejection(room_id: str, ghost_id: str, charm_id: str) -> str:
    parts: list[str] = []
    if room_id in ROOMS and ghost_id in GHOSTS and GHOSTS[ghost_id].home != room_id:
        parts.append(
            f"{GHOSTS[ghost_id].label.capitalize()} belongs in {ROOMS[GHOSTS[ghost_id].home].label}, not {ROOMS[room_id].label}"
        )
    if ghost_id in GHOSTS and charm_id in CHARMS and CHARMS[charm_id].belongs_to != ghost_id:
        parts.append(
            f"{CHARMS[charm_id].label} belongs to {GHOSTS[CHARMS[charm_id].belongs_to].label}, not {GHOSTS[ghost_id].label}"
        )
    if not parts:
        return "(No valid combination matches the given options.)"
    return "(No story: " + "; ".join(parts) + ".)"


def predict_darkness(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    room = sim.get("room")
    child = sim.get("child")
    return {
        "darkness": room.meters["darkness"],
        "fear": child.memes["fear"],
    }


def introduce(world: World, child: Entity, elder: Entity, room_cfg: RoomCfg) -> None:
    trait = child.traits[0] if child.traits else "careful"
    world.say(
        f"On a windy evening, {child.id}, a {trait} little {child.type}, followed {elder.elder_word} {room_cfg.approach}. "
        f"{room_cfg.detail}"
    )


def strange_lamp(world: World, child: Entity, room_cfg: RoomCfg) -> None:
    lamp = world.get("lamp")
    lamp.meters["scratch_dim"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In the middle of {room_cfg.label} stood an old glass lamp. Its light should have been golden, but tonight it was scratch-dim, "
        f"as if thin gray claws had rubbed the shine almost away."
    )


def ghost_appears(world: World, child: Entity, ghost_cfg: GhostCfg) -> None:
    ghost = world.get("ghost")
    ghost.memes["hope"] += 1
    world.say(
        f"{child.id} heard a tiny rustle, then saw {ghost_cfg.label} near the lamp. {ghost_cfg.whisper}"
    )


def elder_explains(world: World, elder: Entity, ghost_cfg: GhostCfg, room_cfg: RoomCfg) -> None:
    pred = predict_darkness(world)
    world.facts["predicted_dark"] = pred["darkness"]
    world.say(
        f'"Then we will think it through," said {elder.elder_word}. "{ghost_cfg.label.capitalize()} {ghost_cfg.memory}, and something that belongs to it must be hidden {room_cfg.hiding_place}. '
        f"If we mend the lamp, this room will not have to stay so dark."
    )


def choose_tools(world: World, seal_cfg: SealCfg) -> None:
    world.say(seal_cfg.shelf_text)


def open_box(world: World, elder: Entity, seal_cfg: SealCfg) -> None:
    box = world.get("box")
    if "mallet" in seal_cfg.needs:
        world.facts["used_tools"].append("mallet")
    if "blade" in seal_cfg.needs:
        world.facts["used_tools"].append("blade")
    box.meters["open"] += 1
    world.facts["opened"] = True
    world.say(seal_cfg.open_text)


def reveal_charm(world: World, charm_cfg: CharmCfg) -> None:
    charm = world.get("charm")
    charm.meters["found"] += 1
    world.say(
        f"Inside rested {charm_cfg.phrase}. Even before anyone touched it, a little silver gleam moved across the box like moonlight remembering its way."
    )


def mend_lamp(world: World, child: Entity, charm_cfg: CharmCfg) -> None:
    lamp = world.get("lamp")
    charm = world.get("charm")
    lamp.meters["scratch_dim"] = 0.0
    lamp.meters["glow"] += 1
    charm.meters["returned"] += 1
    world.facts["restored"] = True
    world.say(
        f"{child.id} held the charm close while the grown-up guided {child.pronoun('possessive')} hands to the lamp. {charm_cfg.magic_effect}"
    )


def ghost_rests(world: World, ghost_cfg: GhostCfg) -> None:
    ghost = world.get("ghost")
    ghost.meters["guided"] += 1
    propagate(world, narrate=False)
    world.facts["rested"] = True
    world.say(
        "The lamp brightened until every corner showed its true shape again. The room was still old, but it was not frightening now, only quiet."
    )
    world.say(ghost_cfg.rest_line)


def ending(world: World, child: Entity, room_cfg: RoomCfg) -> None:
    world.say(
        f"{child.id} looked around and smiled. {room_cfg.ending_image}"
    )
@dataclass
class StoryParams:
    room: str
    ghost: str
    charm: str
    seal: str
    child: str
    child_gender: str
    elder: str
    trait: str
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
        room="attic",
        ghost="tailor_ghost",
        charm="moon_spool",
        seal="mixed",
        child="Mina",
        child_gender="girl",
        elder="grandmother",
        trait="careful",
        seed=11,
    ),
    StoryParams(
        room="nursery",
        ghost="lullaby_ghost",
        charm="music_key",
        seal="twine",
        child="Owen",
        child_gender="boy",
        elder="grandfather",
        trait="curious",
        seed=12,
    ),
    StoryParams(
        room="stairhall",
        ghost="cat_ghost",
        charm="stair_bell",
        seal="nails",
        child="Lucy",
        child_gender="girl",
        elder="mother",
        trait="gentle",
        seed=13,
    ),
]


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with strange, spooky feelings and a spirit or ghost in it. In gentle ghost stories, the ghost may be lonely or lost instead of mean."
        )
    ],
    "magic": [
        (
            "What does magic mean in a story?",
            "Magic means something happens in a way that does not work like ordinary life. In stories, magic can make lights glow, objects sing, or hidden things wake up."
        )
    ],
    "mallet": [
        (
            "What is a mallet?",
            "A mallet is a small hammer with a softer, broader head than a nail hammer. Grown-ups can use it for careful tapping."
        )
    ],
    "blade": [
        (
            "What is a blade?",
            "A blade is the sharp cutting part of a knife or tool. Because it is sharp, a child should let a grown-up handle it."
        )
    ],
    "attic": [
        (
            "What is an attic?",
            "An attic is a room or space high in a house, just under the roof. People often keep old boxes and trunks there."
        )
    ],
    "nursery": [
        (
            "What is a nursery in a house?",
            "A nursery is a room where a baby or very young child sleeps and plays. It often has toys, a crib, and rocking chairs."
        )
    ],
    "stairs": [
        (
            "Why can stairs feel spooky in stories?",
            "Stairs have turns, shadows, and creaks, so they are good places for suspense in a story. A small sound there can seem bigger than it is."
        )
    ],
    "music": [
        (
            "Why can music feel magical in stories?",
            "Music can change how a place feels very quickly. A tiny song in a quiet room can make the room seem warm, safe, or enchanted."
        )
    ],
    "bell": [
        (
            "What does a little bell do in a story?",
            "A little bell makes a bright, clear sound that can guide attention. In a magical story, that sound can mark a change or show the way."
        )
    ],
    "thread": [
        (
            "What is thread used for?",
            "Thread is a thin string used for sewing cloth together. In stories, thread can also stand for mending, patience, and care."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "magic", "mallet", "blade", "attic", "nursery", "stairs", "music", "bell", "thread"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    room_cfg = f["room_cfg"]
    ghost_cfg = f["ghost_cfg"]
    seal_cfg = f["seal_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "scratch-dim" and takes place in {room_cfg.label}.',
        f"Tell a spooky-but-safe story where a child named {child.id} solves a magical problem for {ghost_cfg.label} with a grown-up's help, using a mallet and mentioning a blade.",
        f"Write a short story about a hidden box sealed with {seal_cfg.label}, a dim lamp, and a friendly ghost who can finally rest at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    ghost_cfg = f["ghost_cfg"]
    room_cfg = f["room_cfg"]
    charm_cfg = f["charm_cfg"]
    seal_cfg = f["seal_cfg"]
    used = list(f["used_tools"])
    tool_phrase = " and ".join(used) if used else "careful tools"
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {elder.elder_word}, and {ghost_cfg.label} in {room_cfg.label}. The ghost is lonely at first because the lamp has gone scratch-dim."
        ),
        (
            "What was the problem in the story?",
            f"The lamp in {room_cfg.label} had gone scratch-dim, so the room felt dark and uncertain. The ghost could not settle because its missing keepsake was still hidden away."
        ),
        (
            f"Why did {child.id} and the grown-up look for the box?",
            f"They thought the hidden box held something that belonged to the ghost. They were problem solving, because mending the lamp meant first finding the right magical keepsake."
        ),
        (
            "How did they open the box?",
            f"They opened it by dealing with {seal_cfg.label}. {seal_cfg.qa_text}"
        ),
        (
            f"What happened when {child.id} returned the {charm_cfg.label} to the lamp?",
            f"The magic woke up and the lamp shone properly again. That changed the whole room, because the darkness lifted and the ghost could finally rest."
        ),
        (
            "How did the story end?",
            f"It ended peacefully. {ghost_cfg.rest_line} {room_cfg.ending_image}"
        ),
    ]
    if "blade" in used:
        qa.append(
            (
                "Why did the child let the grown-up handle the blade?",
                f"The blade was sharp, so the grown-up used it carefully. That kept the problem solving safe as well as clever."
            )
        )
    if "mallet" in used:
        qa.append(
            (
                "Why was a mallet useful in this story?",
                f"The mallet was good for careful tapping without wild swinging. It helped open the box in a gentle, controlled way."
            )
        )
    qa.append(
        (
            "Which tools mattered in this story?",
            f"The important tools were {tool_phrase}. They mattered because the kind of seal on the box decided what careful action would work."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ghost", "magic"}
    tags |= set(f["room_cfg"].tags)
    tags |= set(f["seal_cfg"].tags)
    tags |= set(f["charm"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        shown_attrs = {k: v for k, v in ent.attrs.items() if v or v == 0}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Room, Ghost, Charm, Seal) :-
    room(Room), ghost(Ghost), charm(Charm), seal(Seal),
    ghost_home(Ghost, Room),
    charm_for(Charm, Ghost).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id in ROOMS:
        lines.append(asp.fact("room", room_id))
    for ghost_id, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", ghost_id))
        lines.append(asp.fact("ghost_home", ghost_id, ghost.home))
    for charm_id, charm in CHARMS.items():
        lines.append(asp.fact("charm", charm_id))
        lines.append(asp.fact("charm_for", charm_id, charm.belongs_to))
    for seal_id in SEALS:
        lines.append(asp.fact("seal", seal_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=False, header="")
        finally:
            sys.stdout = old
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample2 = generate(params)
        if not sample2.story.strip():
            raise StoryError("default smoke test produced an empty story")
        print("OK: smoke-tested curated and default generation.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story storyworld: a scratch-dim lamp, a hidden keepsake, and careful problem solving."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--seal", choices=SEALS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.ghost and args.ghost in GHOSTS and args.room in ROOMS:
        if GHOSTS[args.ghost].home != args.room:
            charm_probe = args.charm or GHOSTS[args.ghost].charm_id
            raise StoryError(explain_rejection(args.room, args.ghost, charm_probe))
    if args.ghost and args.charm and args.ghost in GHOSTS and args.charm in CHARMS:
        if CHARMS[args.charm].belongs_to != args.ghost:
            room_probe = args.room or GHOSTS[args.ghost].home
            raise StoryError(explain_rejection(room_probe, args.ghost, args.charm))

    combos = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.ghost is None or combo[1] == args.ghost)
        and (args.charm is None or combo[2] == args.charm)
        and (args.seal is None or combo[3] == args.seal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, ghost_id, charm_id, seal_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather", "mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        room=room_id,
        ghost=ghost_id,
        charm=charm_id,
        seal=seal_id,
        child=child_name,
        child_gender=gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.ghost not in GHOSTS:
        raise StoryError(f"(Unknown ghost: {params.ghost})")
    if params.charm not in CHARMS:
        raise StoryError(f"(Unknown charm: {params.charm})")
    if params.seal not in SEALS:
        raise StoryError(f"(Unknown seal: {params.seal})")

    room_cfg = ROOMS[params.room]
    ghost_cfg = GHOSTS[params.ghost]
    charm_cfg = CHARMS[params.charm]
    seal_cfg = SEALS[params.seal]

    if ghost_cfg.home != room_cfg.id or charm_cfg.belongs_to != ghost_cfg.id:
        raise StoryError(explain_rejection(room_cfg.id, ghost_cfg.id, charm_cfg.id))

    world = tell(
        room_cfg,
        ghost_cfg,
        charm_cfg,
        seal_cfg,
        child_name=params.child,
        child_gender=params.child_gender,
        elder_type=params.elder,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, ghost, charm, seal) combos:\n")
        for room_id, ghost_id, charm_id, seal_id in combos:
            print(f"  {room_id:10} {ghost_id:14} {charm_id:11} {seal_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child}: {p.ghost} in {p.room} ({p.seal})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    room_cfg: RoomCfg,
    ghost_cfg: GhostCfg,
    charm_cfg: CharmCfg,
    seal_cfg: SealCfg,
    *,
    child_name: str,
    child_gender: str,
    elder_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            traits=[trait],
            attrs={"asked_for_help": True},
            tags={"child"},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            attrs={"steady": True},
            tags={"grownup"},
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            role="ghost",
            label=ghost_cfg.label,
            attrs={"home": ghost_cfg.home},
            tags=set(ghost_cfg.tags),
        )
    )
    room = world.add(
        Entity(
            id="room",
            type="room",
            label=room_cfg.label,
            attrs={"hiding_place": room_cfg.hiding_place},
            tags=set(room_cfg.tags),
        )
    )
    lamp = world.add(
        Entity(
            id="lamp",
            type="lamp",
            label="lamp",
            attrs={"state": "scratch-dim"},
            tags={"lamp", "magic"},
        )
    )
    box = world.add(
        Entity(
            id="box",
            type="box",
            label="box",
            attrs={"seal": seal_cfg.id},
            tags={"box"},
        )
    )
    charm = world.add(
        Entity(
            id="charm",
            type="charm",
            label=charm_cfg.label,
            attrs={"belongs_to": charm_cfg.belongs_to},
            tags=set(charm_cfg.tags),
        )
    )
    mallet = world.add(
        Entity(
            id="mallet",
            type="tool",
            label="mallet",
            attrs={"safe_with_elder": True},
            tags={"mallet", "tool"},
        )
    )
    blade = world.add(
        Entity(
            id="blade",
            type="tool",
            label="blade",
            attrs={"sharp": True, "safe_with_elder": True},
            tags={"blade", "tool"},
        )
    )

    world.facts.update(
        child=child,
        elder=elder,
        ghost_cfg=ghost_cfg,
        ghost=ghost,
        room_cfg=room_cfg,
        room=room,
        lamp=lamp,
        box=box,
        charm_cfg=charm_cfg,
        charm=charm,
        seal_cfg=seal_cfg,
        seal=seal_cfg.id,
    )

    introduce(world, child, elder, room_cfg)
    strange_lamp(world, child, room_cfg)

    world.para()
    ghost_appears(world, child, ghost_cfg)
    elder_explains(world, elder, ghost_cfg, room_cfg)

    world.para()
    choose_tools(world, seal_cfg)
    open_box(world, elder, seal_cfg)
    reveal_charm(world, charm_cfg)

    world.para()
    mend_lamp(world, child, charm_cfg)
    ghost_rests(world, ghost_cfg)
    ending(world, child, room_cfg)

    return world

if __name__ == "__main__":
    main()
