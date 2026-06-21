#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/staff_transformation_kindness_bravery_ghost_story.py
===============================================================================

A standalone storyworld for a gentle ghost story about a child who finds a lost
staff, meets a frightening spirit, and uses kindness plus bravery to help the
spirit become whole again.

This world models one small domain:

    A child is out in a moonlit place.
    A ghost appears in a warped, scary form because it has lost its staff.
    The child feels afraid, but chooses to step closer.
    The child speaks kindly and returns the staff.
    The ghost transforms into its true, peaceful self and helps the child home.

The constraint gate keeps the combinations tight and plausible:
a given spirit belongs in certain places, and only the right kind of staff can
restore that spirit. Invalid explicit choices raise StoryError with an
explanation.

Run it
------
    python storyworlds/worlds/gpt-5.4/staff_transformation_kindness_bravery_ghost_story.py
    python storyworlds/worlds/gpt-5.4/staff_transformation_kindness_bravery_ghost_story.py --place orchard --ghost gardener --staff apple_staff
    python storyworlds/worlds/gpt-5.4/staff_transformation_kindness_bravery_ghost_story.py --place tower --ghost ferryman
    python storyworlds/worlds/gpt-5.4/staff_transformation_kindness_bravery_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/staff_transformation_kindness_bravery_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/staff_transformation_kindness_bravery_ghost_story.py --verify
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
GENTLE_MIN = 2
BRAVE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
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
    path: str
    night_sound: str
    light: str
    clue_spot: str
    ending_image: str
    ghost_ids: set[str] = field(default_factory=set)
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
class GhostTemplate:
    id: str
    title: str
    scary_form: str
    true_form: str
    voice: str
    sorrow: str
    thanks: str
    guide: str
    needs_staff: str
    places: set[str] = field(default_factory=set)
    staff_ids: set[str] = field(default_factory=set)
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
class StaffItem:
    id: str
    label: str
    phrase: str
    material: str
    detail: str
    glow: str
    owner_ghosts: set[str] = field(default_factory=set)
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
class Temperament:
    id: str
    bravery: int
    kindness: int
    opening: str
    steadying: str
    brave_line: str
    kind_line: str
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


def _r_unmoored(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    if ghost.meters["missing_staff"] < THRESHOLD:
        return out
    sig = ("unmoored", "ghost")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.meters["scary"] += 1
    ghost.memes["lonely"] += 1
    world.get("place").meters["eerie"] += 1
    out.append("__eerie__")
    return out


def _r_restore(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    child = world.get("child")
    staff = world.get("staff")
    if ghost.meters["missing_staff"] < THRESHOLD:
        return out
    if child.memes["bravery"] < BRAVE_MIN or child.memes["kindness"] < GENTLE_MIN:
        return out
    if child.meters["holding_staff"] < THRESHOLD:
        return out
    if child.meters["offered_staff"] < THRESHOLD:
        return out
    sig = ("restore", "ghost")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.meters["missing_staff"] = 0.0
    ghost.meters["whole"] += 1
    ghost.meters["scary"] = 0.0
    ghost.memes["gratitude"] += 1
    ghost.memes["peace"] += 1
    child.memes["fear"] = 0.0
    child.memes["wonder"] += 1
    staff.meters["returned"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule(name="unmoored", tag="state", apply=_r_unmoored),
    Rule(name="restore", tag="state", apply=_r_restore),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "orchard": Place(
        id="orchard",
        label="the old orchard",
        opening="Beyond the last cottage stood the old orchard, where the trees leaned close as if they were whispering secrets to one another.",
        path="the silver path between the apple trees",
        night_sound="apples knocked softly together in the wind",
        light="Moonlight lay on the grass like milk.",
        clue_spot="a root by the crooked cider press",
        ending_image="By the time the child walked home, the orchard no longer looked haunted. It looked watched over.",
        ghost_ids={"gardener"},
        tags={"orchard", "ghost", "night"},
    ),
    "marsh": Place(
        id="marsh",
        label="the marsh bridge",
        opening="Past the reeds and still water stood the marsh bridge, all pale boards and quiet splashes in the dark.",
        path="the narrow bridge over the black water",
        night_sound="the reeds hissed and the water gave small, sleepy gulps",
        light="A thin moon shivered in the marsh water.",
        clue_spot="the last dry plank before the reeds",
        ending_image="When the child turned back for one last look, the bridge was no longer lonely. It held one steady silver line across the water.",
        ghost_ids={"ferryman"},
        tags={"marsh", "ghost", "night"},
    ),
    "tower": Place(
        id="tower",
        label="the bell tower hill",
        opening="On the hill above the village stood the bell tower, with ivy on the stones and night folded around the steps.",
        path="the worn steps circling the tower",
        night_sound="the loose bell rope tapped the wall in the wind",
        light="The stars made the tower windows shine like small eyes.",
        clue_spot="the third step below the tower door",
        ending_image="Afterward, the tower looked less like a place for shivers and more like a place that remembered its duty.",
        ghost_ids={"watcher"},
        tags={"tower", "ghost", "night"},
    ),
}

GHOSTS = {
    "gardener": GhostTemplate(
        id="gardener",
        title="the orchard gardener",
        scary_form="a ragged white shape stitched together from fog and leaves",
        true_form="a tall, gentle gardener with moonlit sleeves and kind old eyes",
        voice="a rustle like dry leaves under a shoe",
        sorrow="Without my staff, I cannot keep my shape. The wind keeps pulling me apart.",
        thanks="You were not cruel to me when I looked frightening.",
        guide="showed where the safe path curled back toward the cottages",
        needs_staff="apple_staff",
        places={"orchard"},
        staff_ids={"apple_staff"},
        tags={"ghost", "garden", "staff"},
    ),
    "ferryman": GhostTemplate(
        id="ferryman",
        title="the marsh ferryman",
        scary_form="a dripping shadow with long arms of mist and a face that flickered in and out",
        true_form="a calm ferryman wrapped in pale blue light, with water shining on his coat like stars",
        voice="a hollow murmur like water under boards",
        sorrow="My crossing staff is gone, and the marsh keeps smudging me into shadow.",
        thanks="You chose help when running away would have been easier.",
        guide="walked beside the child until the stones near the lane came into view",
        needs_staff="reed_staff",
        places={"marsh"},
        staff_ids={"reed_staff"},
        tags={"ghost", "marsh", "staff"},
    ),
    "watcher": GhostTemplate(
        id="watcher",
        title="the old night watch",
        scary_form="a bent dark figure with bells of frost shaking inside its chest",
        true_form="a straight-backed watchman, bright as pearl, with a quiet smile under his cap",
        voice="a whisper that seemed to come from every stone at once",
        sorrow="I dropped my watch staff, and now the hill answers with echoes instead of my own voice.",
        thanks="A brave heart and a gentle hand can mend more than people think.",
        guide="pointed out the lantern-lit lane below the hill and bowed",
        needs_staff="oak_staff",
        places={"tower"},
        staff_ids={"oak_staff"},
        tags={"ghost", "tower", "staff"},
    ),
}

STAFFS = {
    "apple_staff": StaffItem(
        id="apple_staff",
        label="apple-wood staff",
        phrase="an apple-wood staff",
        material="apple wood",
        detail="Its smooth handle held a tiny carving of leaves near the top.",
        glow="When the moon touched it, a soft greenish shine ran along the grain.",
        owner_ghosts={"gardener"},
        tags={"staff", "wood", "orchard"},
    ),
    "reed_staff": StaffItem(
        id="reed_staff",
        label="reed-bound staff",
        phrase="a reed-bound staff",
        material="reed and ash wood",
        detail="Fine strips of dried reed were wrapped around the middle so wet hands would not slip.",
        glow="A pale blue glimmer trembled around it like moonlight on water.",
        owner_ghosts={"ferryman"},
        tags={"staff", "water", "marsh"},
    ),
    "oak_staff": StaffItem(
        id="oak_staff",
        label="oak watch staff",
        phrase="an oak watch staff",
        material="oak wood",
        detail="A tiny bell was tied beneath the crook, though it made no sound at all.",
        glow="It caught the starlight in a clean silver line.",
        owner_ghosts={"watcher"},
        tags={"staff", "tower", "oak"},
    ),
    "pine_staff": StaffItem(
        id="pine_staff",
        label="pine walking staff",
        phrase="a pine walking staff",
        material="pine wood",
        detail="It smelled sharp and clean, as if it had come from a fresh-cut branch.",
        glow="It stayed plain and dark in the moonlight.",
        owner_ghosts=set(),
        tags={"staff", "pine"},
    ),
}

TEMPERAMENTS = {
    "tender": Temperament(
        id="tender",
        bravery=2,
        kindness=3,
        opening="Even when the dark made the child's stomach flutter, the child still noticed when something sounded sad instead of mean.",
        steadying="The child pressed one hand to a racing chest and stayed put.",
        brave_line='"I am scared," the child said, "but I will not be unkind just because I am scared."',
        kind_line='"Did you lose something?" the child asked. "If I can help, I will."',
        tags={"kindness", "bravery"},
    ),
    "steady": Temperament(
        id="steady",
        bravery=3,
        kindness=2,
        opening="The child had the sort of brave quiet that did not shout, but did not run either.",
        steadying="The child took one careful breath after another until the shaking slowed.",
        brave_line='"You do look frightening," the child admitted, "but I want to know why."',
        kind_line='"I found a staff," the child said. "If it belongs to you, you may have it back."',
        tags={"kindness", "bravery"},
    ),
    "softhearted": Temperament(
        id="softhearted",
        bravery=2,
        kindness=4,
        opening="The child was known for noticing lonely things: bent flowers, wet birds, and now, perhaps, even a ghost.",
        steadying="The child did not let fear boss the whole body around.",
        brave_line='"Please do not rush at me," the child whispered, standing firm. "I came to listen."',
        kind_line='"You sound lonely," the child said. "Here. I think this staff is yours."',
        tags={"kindness", "bravery"},
    ),
    "lanternhearted": Temperament(
        id="lanternhearted",
        bravery=3,
        kindness=3,
        opening="Some children stomp away from shadows. This one carried a little light inside, even on frightening nights.",
        steadying="The child swallowed hard, lifted the chin, and took a step instead of a dash.",
        brave_line='"I can be brave and gentle at the same time," the child murmured.',
        kind_line='"I will return what was lost," the child said, holding out the staff with both hands.',
        tags={"kindness", "bravery"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ivy", "Clara", "Elsie", "Ruth", "Wren"]
BOY_NAMES = ["Tomas", "Eli", "Jonah", "Milo", "Theo", "Rowan", "Silas", "Hugo"]
GUARDIANS = ["mother", "father", "grandmother", "grandfather"]


def valid_combo(place_id: str, ghost_id: str, staff_id: str) -> bool:
    if place_id not in PLACES or ghost_id not in GHOSTS or staff_id not in STAFFS:
        return False
    place = PLACES[place_id]
    ghost = GHOSTS[ghost_id]
    staff = STAFFS[staff_id]
    return ghost_id in place.ghost_ids and place_id in ghost.places and staff_id in ghost.staff_ids and ghost_id in staff.owner_ghosts


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id in sorted(PLACES):
        for ghost_id in sorted(GHOSTS):
            for staff_id in sorted(STAFFS):
                if valid_combo(place_id, ghost_id, staff_id):
                    combos.append((place_id, ghost_id, staff_id))
    return combos


def explain_rejection(place_id: str, ghost_id: str, staff_id: Optional[str] = None) -> str:
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    if ghost_id not in GHOSTS:
        return f"(No story: unknown ghost '{ghost_id}'.)"
    if staff_id is not None and staff_id not in STAFFS:
        return f"(No story: unknown staff '{staff_id}'.)"
    place = PLACES[place_id]
    ghost = GHOSTS[ghost_id]
    if ghost_id not in place.ghost_ids or place_id not in ghost.places:
        return (
            f"(No story: {ghost.title} does not belong in {place.label}. "
            f"This world keeps each spirit tied to the place it once watched.)"
        )
    if staff_id is not None:
        staff = STAFFS[staff_id]
        need = STAFFS[ghost.needs_staff].label
        return (
            f"(No story: {ghost.title} can only be restored by {need}, not by "
            f"{staff.label}. The transformation depends on returning the right staff.)"
        )
    return "(No story: that combination does not belong to this world.)"


def sensible_temperaments() -> list[Temperament]:
    return [t for t in TEMPERAMENTS.values() if t.bravery >= BRAVE_MIN and t.kindness >= GENTLE_MIN]


@dataclass
class StoryParams:
    place: str
    ghost: str
    staff: str
    temperament: str
    name: str
    gender: str
    guardian: str
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


def introduce(world: World, child: Entity, guardian: Entity, temp: Temperament) -> None:
    place = world.place
    world.say(f"One moonlit evening, {child.id} was walking near {place.label} after taking a small bundle to {guardian.label_word}.")
    world.say(place.opening)
    world.say(place.light)
    world.say(temp.opening)


def find_staff(world: World, child: Entity, staff_cfg: StaffItem) -> None:
    staff = world.get("staff")
    staff.meters["found"] += 1
    child.meters["holding_staff"] += 1
    world.say(
        f"On {world.place.path}, {child.id} noticed {staff_cfg.phrase} lying by {world.place.clue_spot}. "
        f"{staff_cfg.detail} {staff_cfg.glow}"
    )


def awaken_ghost(world: World, ghost_cfg: GhostTemplate) -> None:
    ghost = world.get("ghost")
    ghost.meters["missing_staff"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then the night changed. From the dark ahead rose {ghost_cfg.scary_form}. "
        f"It made {ghost_cfg.voice}, and even the air seemed to hold its breath."
    )


def fear_and_choice(world: World, child: Entity, temp: Temperament) -> None:
    child.memes["fear"] += 1
    child.memes["bravery"] += float(temp.bravery)
    child.memes["kindness"] += float(temp.kindness)
    world.say(f"{child.id}'s knees wanted to run, but {temp.steadying}")
    world.say(temp.brave_line)


def kind_question(world: World, ghost_cfg: GhostTemplate, temp: Temperament) -> None:
    ghost = world.get("ghost")
    ghost.memes["heard_kindness"] += 1
    world.say(temp.kind_line)
    world.say(f'The shape shivered. "{ghost_cfg.sorrow}" it answered.')


def offer_staff(world: World, child: Entity, staff_cfg: StaffItem) -> None:
    child.meters["offered_staff"] += 1
    world.say(
        f"{child.id} stepped close enough to feel the cold around the ghost and lifted the {staff_cfg.label} with both hands."
    )


def transform(world: World, ghost_cfg: GhostTemplate, child: Entity) -> None:
    propagate(world, narrate=False)
    ghost = world.get("ghost")
    if ghost.meters["whole"] < THRESHOLD:
        raise StoryError("(Internal story error: the ghost did not transform as expected.)")
    world.say(
        f"As soon as the ghost touched the staff, the frightening shape loosened like a knot coming undone. "
        f"The fog drew in, the shadows thinned, and there stood {ghost_cfg.true_form}."
    )
    world.say(
        f'"{ghost_cfg.thanks}" {ghost.pronoun()} said. The child was still trembling a little, but the fear had turned into wonder.'
    )


def guide_home(world: World, ghost_cfg: GhostTemplate, child: Entity, guardian: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    ghost = world.get("ghost")
    ghost.memes["care"] += 1
    world.say(
        f"The restored spirit {ghost_cfg.guide}. "
        f'"Go on, little one," {ghost.pronoun()} said. "Your {guardian.label_word} is waiting, and this path is safe now."'
    )
    world.say(world.place.ending_image)


def tell(
    place: Place,
    ghost_cfg: GhostTemplate,
    staff_cfg: StaffItem,
    temp: Temperament,
    name: str = "Lila",
    gender: str = "girl",
    guardian_type: str = "grandmother",
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            role="child",
            label=name,
            attrs={"temperament": temp.id},
            traits=[temp.id],
        )
    )
    guardian = world.add(
        Entity(
            id="Guardian",
            kind="character",
            type=guardian_type,
            role="guardian",
            label="the guardian",
            attrs={},
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            role="ghost",
            label=ghost_cfg.title,
            attrs={"template": ghost_cfg.id},
        )
    )
    world.add(Entity(id="place", type="place", label=place.label, attrs={}))
    world.add(
        Entity(
            id="staff",
            kind="thing",
            type="staff",
            role="staff",
            label=staff_cfg.label,
            attrs={"staff_id": staff_cfg.id},
        )
    )

    world.facts["place_cfg"] = place
    world.facts["ghost_cfg"] = ghost_cfg
    world.facts["staff_cfg"] = staff_cfg
    world.facts["temperament_cfg"] = temp
    world.facts["guardian"] = guardian
    world.facts["child"] = child
    world.facts["ghost"] = ghost
    world.facts["restored"] = False
    world.facts["staff_returned"] = False

    introduce(world, child, guardian, temp)
    world.para()
    find_staff(world, child, staff_cfg)
    awaken_ghost(world, ghost_cfg)
    fear_and_choice(world, child, temp)
    world.para()
    kind_question(world, ghost_cfg, temp)
    offer_staff(world, child, staff_cfg)
    transform(world, ghost_cfg, child)
    world.para()
    guide_home(world, ghost_cfg, child, guardian)

    world.facts["restored"] = world.get("ghost").meters["whole"] >= THRESHOLD
    world.facts["staff_returned"] = world.get("staff").meters["returned"] >= THRESHOLD
    world.facts["eerie_before"] = world.get("place").meters["eerie"] >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    ghost_cfg = world.facts["ghost_cfg"]
    staff_cfg = world.facts["staff_cfg"]
    place = world.facts["place_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "{staff_cfg.label.split()[0]}" and ends with a spirit transformed by kindness and bravery.',
        f"Tell a moonlit story where a {child.type} named {child.id} finds a lost staff in {place.label}, meets {ghost_cfg.title}, and helps the ghost become peaceful again.",
        f"Write a short ghost story in which a frightening spirit is restored when a child bravely returns the right staff instead of running away.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    ghost_cfg = world.facts["ghost_cfg"]
    staff_cfg = world.facts["staff_cfg"]
    guardian = world.facts["guardian"]
    place = world.facts["place_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child walking near {place.label}, and {ghost_cfg.title}. "
            f"The story begins when {child.id} finds {staff_cfg.phrase} in the dark.",
        ),
        (
            f"Why did the ghost look scary at first?",
            f"The ghost had lost its staff, so it could not keep its proper shape. "
            f"Without the staff, it came apart into a frightening form made of mist, shadow, or leaves.",
        ),
        (
            f"What made {child.id} brave?",
            f"{child.id} was afraid, but stayed to listen instead of running. "
            f"That choice was brave because the ghost looked frightening and the night place felt eerie.",
        ),
        (
            f"How did {child.id} show kindness?",
            f"{child.id} spoke gently and tried to help instead of mocking the spirit or running away. "
            f"Then {child.pronoun()} returned the lost staff, which was exactly what the ghost needed.",
        ),
    ]
    if world.facts.get("restored"):
        qa.append(
            (
                "What caused the transformation?",
                f"The transformation happened when the ghost touched its own staff after {child.id} offered it back. "
                f"Kindness opened the moment, and bravery let {child.id} step close enough to return the staff.",
            )
        )
        qa.append(
            (
                f"What changed at the end of the story?",
                f"The ghost became peaceful and whole instead of frightening, and the place no longer felt haunted. "
                f"The restored spirit even helped {child.id} find the safe way back to {guardian.label_word}.",
            )
        )
    return qa


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story with a spirit or haunting in it. Some ghost stories are scary, but gentle ones end with understanding instead of harm.",
        )
    ],
    "staff": [
        (
            "What is a staff?",
            "A staff is a long stick that someone can carry while walking or working. It can help support a person, point the way, or show that the staff belongs to them.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel afraid. It does not mean never feeling fear at all.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means treating someone gently and trying to help. Sometimes kindness changes a whole situation because it makes people feel safe enough to tell the truth.",
        )
    ],
    "transformation": [
        (
            "What does transformation mean in a story?",
            "Transformation means something changes from one form into another. In a story, that change often shows that a problem has been solved.",
        )
    ],
    "orchard": [
        (
            "What is an orchard?",
            "An orchard is a place where fruit trees are grown together. Apple orchards are rows of trees that can rustle and creak in the wind at night.",
        )
    ],
    "marsh": [
        (
            "What is a marsh?",
            "A marsh is wet, soft ground with grasses and reeds growing in it. Water moves quietly there, so sounds can feel strange at night.",
        )
    ],
    "tower": [
        (
            "What is a bell tower?",
            "A bell tower is a tall building or part of a building that holds a bell. From high up, a watchman can see far across the land.",
        )
    ],
}

KNOWLEDGE_ORDER = ["ghost", "staff", "bravery", "kindness", "transformation", "orchard", "marsh", "tower"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "staff", "bravery", "kindness", "transformation"}
    place = world.facts["place_cfg"]
    tags |= set(place.tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
belongs(P,G) :- place(P), ghost(G), haunts(P,G), keeps_to(G,P).
right_staff(G,S) :- ghost(G), staff(S), needs(G,S), belongs_owner(S,G).
valid(P,G,S) :- belongs(P,G), right_staff(G,S).

restored :- chosen_temperament(T), bravery(T,B), kindness(T,K), brave_min(BM), gentle_min(GM), B >= BM, K >= GM,
            chosen_ghost(G), chosen_staff(S), right_staff(G,S), chosen_place(P), belongs(P,G).
outcome(restored) :- restored.
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in sorted(PLACES):
        lines.append(asp.fact("place", pid))
    for gid, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        for place_id in sorted(ghost.places):
            lines.append(asp.fact("keeps_to", gid, place_id))
        lines.append(asp.fact("needs", gid, ghost.needs_staff))
    for pid, place in PLACES.items():
        for ghost_id in sorted(place.ghost_ids):
            lines.append(asp.fact("haunts", pid, ghost_id))
    for sid, staff in STAFFS.items():
        lines.append(asp.fact("staff", sid))
        for ghost_id in sorted(staff.owner_ghosts):
            lines.append(asp.fact("belongs_owner", sid, ghost_id))
    for tid, temp in TEMPERAMENTS.items():
        lines.append(asp.fact("temperament", tid))
        lines.append(asp.fact("bravery", tid, temp.bravery))
        lines.append(asp.fact("kindness", tid, temp.kindness))
    lines.append(asp.fact("brave_min", BRAVE_MIN))
    lines.append(asp.fact("gentle_min", GENTLE_MIN))
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
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_ghost", params.ghost),
            asp.fact("chosen_staff", params.staff),
            asp.fact("chosen_temperament", params.temperament),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "none"


CURATED = [
    StoryParams(
        place="orchard",
        ghost="gardener",
        staff="apple_staff",
        temperament="softhearted",
        name="Ivy",
        gender="girl",
        guardian="grandmother",
    ),
    StoryParams(
        place="marsh",
        ghost="ferryman",
        staff="reed_staff",
        temperament="steady",
        name="Milo",
        gender="boy",
        guardian="father",
    ),
    StoryParams(
        place="tower",
        ghost="watcher",
        staff="oak_staff",
        temperament="lanternhearted",
        name="Clara",
        gender="girl",
        guardian="mother",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a lost staff, and a ghost restored by kindness and bravery."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--ghost", choices=sorted(GHOSTS))
    ap.add_argument("--staff", choices=sorted(STAFFS))
    ap.add_argument("--temperament", choices=sorted(TEMPERAMENTS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (place, ghost, staff) combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.ghost and args.staff and not valid_combo(args.place, args.ghost, args.staff):
        raise StoryError(explain_rejection(args.place, args.ghost, args.staff))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.ghost is None or combo[1] == args.ghost)
        and (args.staff is None or combo[2] == args.staff)
    ]
    if not combos:
        if args.place and args.ghost:
            raise StoryError(explain_rejection(args.place, args.ghost, args.staff))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, ghost_id, staff_id = rng.choice(sorted(combos))
    temperament_id = args.temperament or rng.choice(sorted(t.id for t in sensible_temperaments()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    guardian = args.guardian or rng.choice(GUARDIANS)
    return StoryParams(
        place=place_id,
        ghost=ghost_id,
        staff=staff_id,
        temperament=temperament_id,
        name=name,
        gender=gender,
        guardian=guardian,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.place, params.ghost, params.staff):
        raise StoryError(explain_rejection(params.place, params.ghost, params.staff))
    if params.temperament not in TEMPERAMENTS:
        raise StoryError(f"(No story: unknown temperament '{params.temperament}'.)")
    if params.guardian not in GUARDIANS:
        raise StoryError(f"(No story: unknown guardian '{params.guardian}'.)")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown gender '{params.gender}'.)")

    world = tell(
        place=PLACES[params.place],
        ghost_cfg=GHOSTS[params.ghost],
        staff_cfg=STAFFS[params.staff],
        temp=TEMPERAMENTS[params.temperament],
        name=params.name,
        gender=params.gender,
        guardian_type=params.guardian,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        out = asp_outcome(params)
        if out != "restored":
            bad += 1
    if bad == 0:
        print(f"OK: outcome model says restored for {len(cases)} checked scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} scenarios did not restore in ASP.")

    try:
        sample = generate(cases[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, ghost, staff) combos:\n")
        for place_id, ghost_id, staff_id in combos:
            print(f"  {place_id:8} {ghost_id:10} {staff_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.ghost} at {p.place} with {p.staff}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
