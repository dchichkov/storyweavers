#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/operate_inner_monologue_dialogue_mystery_to_solve.py
===============================================================================

A standalone story world about a child and a loving elder solving a tiny mystery:
a cozy toy or music device will not operate because one important piece is
missing. The pair notice a clue, follow it, and restore the missing piece in a
gentle, heartwarming ending.

The world is built around a small reasonableness gate:

- each device needs one specific part to operate
- each clue points to one specific hiding place
- each place can reasonably hold only certain parts

A valid story therefore needs a coherent chain:

    device -> required part -> plausible place -> clue pointing there

The world also tracks whether the place is easy for the child to reach. If it is
reachable, the child solves the mystery alone; if not, the child asks the elder
for help, and they solve it together.

Run it
------
    python storyworlds/worlds/gpt-5.4/operate_inner_monologue_dialogue_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/operate_inner_monologue_dialogue_mystery_to_solve.py --device music_box --clue gold_thread --place sewing_basket
    python storyworlds/worlds/gpt-5.4/operate_inner_monologue_dialogue_mystery_to_solve.py --device rug_train --place art_folder
    python storyworlds/worlds/gpt-5.4/operate_inner_monologue_dialogue_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/operate_inner_monologue_dialogue_mystery_to_solve.py --qa --json
    python storyworlds/worlds/gpt-5.4/operate_inner_monologue_dialogue_mystery_to_solve.py --verify
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
from contextlib import redirect_stdout
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    required_part: str
    operate_text: str
    ending_image: str
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
class Part:
    id: str
    label: str
    phrase: str
    attach_text: str
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
class Place:
    id: str
    label: str
    phrase: str
    accessible: bool = True
    search_text: str = ""
    open_text: str = ""
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
class Clue:
    id: str
    label: str
    notice_text: str
    thought_text: str
    points_to: str
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


def _r_stalled(world: World) -> list[str]:
    child = world.get("child")
    device = world.get("device")
    part = world.get("part")
    if part.meters["attached"] >= THRESHOLD:
        return []
    sig = ("stalled", device.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    device.meters["stalled"] += 1
    child.memes["worry"] += 1
    child.memes["curiosity"] += 1
    return ["__stalled__"]


def _r_found_relief(world: World) -> list[str]:
    child = world.get("child")
    part = world.get("part")
    if part.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", part.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["hope"] += 1
    child.memes["relief"] += 1
    return []


def _r_need_help(world: World) -> list[str]:
    child = world.get("child")
    place = world.get("place")
    if child.memes["searching"] < THRESHOLD or place.attrs.get("accessible", True):
        return []
    sig = ("need_help", place.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["needs_help"] += 1
    return []


def _r_operating(world: World) -> list[str]:
    child = world.get("child")
    elder = world.get("elder")
    device = world.get("device")
    part = world.get("part")
    if part.meters["attached"] < THRESHOLD:
        return []
    sig = ("operating", device.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    device.meters["working"] += 1
    child.memes["joy"] += 1
    child.memes["confidence"] += 1
    elder.memes["joy"] += 1
    elder.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="stalled", tag="physical", apply=_r_stalled),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
    Rule(name="need_help", tag="social", apply=_r_need_help),
    Rule(name="operating", tag="physical", apply=_r_operating),
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


def part_for_device(device_id: str) -> str:
    return DEVICES[device_id].required_part


def clue_matches_place(clue_id: str, place_id: str) -> bool:
    return CLUES[clue_id].points_to == place_id


def place_holds_part(place_id: str, part_id: str) -> bool:
    return part_id in PLACES[place_id].tags


def valid_combo(device_id: str, clue_id: str, place_id: str) -> bool:
    if device_id not in DEVICES or clue_id not in CLUES or place_id not in PLACES:
        return False
    part_id = part_for_device(device_id)
    return clue_matches_place(clue_id, place_id) and place_holds_part(place_id, part_id)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for did in DEVICES:
        for cid in CLUES:
            for pid in PLACES:
                if valid_combo(did, cid, pid):
                    combos.append((did, cid, pid))
    return combos


def outcome_of(params: "StoryParams") -> str:
    place = PLACES[params.place]
    return "solo" if place.accessible else "with_helper"


def explain_rejection(device: Device, clue: Clue, place: Place) -> str:
    part = PARTS[device.required_part]
    if not clue_matches_place(clue.id, place.id):
        actual = PLACES[clue.points_to].label
        return (
            f"(No story: the clue '{clue.label}' points toward {actual}, not {place.label}. "
            f"A mystery needs the clue to lead somewhere honest.)"
        )
    if not place_holds_part(place.id, part.id):
        return (
            f"(No story: {place.label} is not a sensible place to find the {part.label} for the "
            f"{device.label}. Pick a place that could really hold that missing piece.)"
        )
    return "(No story: this device, clue, and place do not form a coherent mystery.)"


def setup_scene(world: World, child: Entity, elder: Entity, device_cfg: Device) -> None:
    for who in (child, elder):
        who.memes["warmth"] += 1
    world.say(
        f"On a soft afternoon at home, {child.id} sat close beside {elder.label_word} with "
        f"{device_cfg.phrase} between them."
    )
    world.say(
        f"{elder.label_word.capitalize()} had promised to teach {child.id} how to operate it, "
        f"and the room felt quiet and special, as if it were waiting for a tiny show."
    )


def invite_operate(world: World, child: Entity, elder: Entity, device_cfg: Device) -> None:
    child.memes["eagerness"] += 1
    world.say(
        f'"Ready?" asked {elder.label_word}. "{device_cfg.operate_text}"'
    )
    world.say(
        f'{child.id} nodded. "I am ready."'
    )


def failed_start(world: World, child: Entity, elder: Entity, device_cfg: Device, part_cfg: Part) -> None:
    child.memes["attempted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {child.id} tried, the {device_cfg.label} stayed still and quiet."
    )
    world.say(
        f'{child.id} blinked. "It will not work," {child.pronoun()} said.'
    )
    world.say(
        f'{child.id} thought, "Something important must be missing. If I look carefully, maybe the room will tell me where {part_cfg.label} went."'
    )
    elder.memes["calm"] += 1
    world.say(
        f'"Then we can solve the little mystery together," said {elder.label_word}, smiling instead of hurrying.'
    )


def notice_clue(world: World, child: Entity, clue_cfg: Clue) -> None:
    child.memes["searching"] += 1
    child.memes["observant"] += 1
    propagate(world, narrate=False)
    world.say(clue_cfg.notice_text)
    world.say(
        f'{child.id} thought, "{clue_cfg.thought_text}"'
    )


def search_open_place(world: World, child: Entity, place_cfg: Place, part_cfg: Part) -> None:
    child.meters["steps"] += 1
    world.say(place_cfg.search_text)
    part = world.get("part")
    part.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"There, tucked safely inside, was {part_cfg.phrase}."
    )


def ask_for_help(world: World, child: Entity, elder: Entity, place_cfg: Place) -> None:
    child.meters["steps"] += 1
    child.memes["trust"] += 1
    world.say(
        f'{child.id} looked up at {place_cfg.phrase} and then at {elder.label_word}. '
        f'"I know where to look," {child.pronoun()} said, "but I cannot reach it by myself."'
    )
    world.say(
        f'"That is what I am here for," said {elder.label_word}. {elder.pronoun().capitalize()} {place_cfg.open_text}.'
    )
    elder.memes["helped"] += 1


def search_closed_place(world: World, child: Entity, elder: Entity, place_cfg: Place, part_cfg: Part) -> None:
    ask_for_help(world, child, elder, place_cfg)
    part = world.get("part")
    part.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Inside they found {part_cfg.phrase}, waiting as if it had been hoping to be noticed."
    )


def attach_part(world: World, child: Entity, elder: Entity, device_cfg: Device, part_cfg: Part) -> None:
    part = world.get("part")
    part.meters["attached"] += 1
    device = world.get("device")
    device.meters["stalled"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{child.id} brought the {part_cfg.label} back, and together they {part_cfg.attach_text}."
    )
    world.say(
        f'"Try again," said {elder.label_word}.'
    )


def celebrate(world: World, child: Entity, elder: Entity, device_cfg: Device, part_cfg: Part) -> None:
    world.say(device_cfg.ending_image)
    if world.facts["outcome"] == "solo":
        world.say(
            f'{child.id} gave a proud little laugh. "{part_cfg.label.capitalize()} was the answer," {child.pronoun()} said.'
        )
    else:
        world.say(
            f'{child.id} leaned against {elder.label_word} and smiled. "We solved it together," {child.pronoun()} said.'
        )
    world.say(
        f"{elder.label_word.capitalize()} squeezed {child.id}'s shoulder. "
        f'"You noticed the clue, kept thinking, and did not give up. That is how little mysteries are solved."'
    )


def tell(
    device_cfg: Device,
    clue_cfg: Clue,
    place_cfg: Place,
    child_name: str = "Nora",
    child_gender: str = "girl",
    elder_type: str = "grandfather",
    elder_name: str = "Grandpa",
) -> World:
    world = World()

    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=["gentle", "curious"],
        )
    )
    elder = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type=elder_type,
            label=elder_name,
            role="elder",
            traits=["patient", "warm"],
        )
    )
    device = world.add(
        Entity(
            id="device",
            kind="thing",
            type="device",
            label=device_cfg.label,
            phrase=device_cfg.phrase,
            attrs={"required_part": device_cfg.required_part},
        )
    )
    part = world.add(
        Entity(
            id="part",
            kind="thing",
            type="part",
            label=PARTS[device_cfg.required_part].label,
            phrase=PARTS[device_cfg.required_part].phrase,
            attrs={"home_place": place_cfg.id},
        )
    )
    place = world.add(
        Entity(
            id="place",
            kind="thing",
            type="place",
            label=place_cfg.label,
            phrase=place_cfg.phrase,
            attrs={"accessible": place_cfg.accessible},
        )
    )

    world.facts.update(
        child=child,
        elder=elder,
        device_cfg=device_cfg,
        part_cfg=PARTS[device_cfg.required_part],
        clue_cfg=clue_cfg,
        place_cfg=place_cfg,
        device=device,
        part=part,
        place=place,
        outcome="solo" if place_cfg.accessible else "with_helper",
        asked_help=not place_cfg.accessible,
    )

    setup_scene(world, child, elder, device_cfg)
    invite_operate(world, child, elder, device_cfg)

    world.para()
    failed_start(world, child, elder, device_cfg, PARTS[device_cfg.required_part])
    notice_clue(world, child, clue_cfg)

    world.para()
    if place_cfg.accessible:
        search_open_place(world, child, place_cfg, PARTS[device_cfg.required_part])
    else:
        search_closed_place(world, child, elder, place_cfg, PARTS[device_cfg.required_part])

    attach_part(world, child, elder, device_cfg, PARTS[device_cfg.required_part])

    world.para()
    celebrate(world, child, elder, device_cfg, PARTS[device_cfg.required_part])
    return world


DEVICES = {
    "starlight_projector": Device(
        id="starlight_projector",
        label="starlight projector",
        phrase="a small starlight projector with a moon painted on the side",
        required_part="star_disk",
        operate_text='Press the silver switch and watch the room fill with stars.',
        ending_image="This time the projector woke at once, and soft stars drifted over the ceiling and across their hands.",
        tags={"projector", "operate", "stars"},
    ),
    "music_box": Device(
        id="music_box",
        label="music box",
        phrase="a swan music box with a tiny shining platform",
        required_part="brass_key",
        operate_text='Turn it gently and listen for the song.',
        ending_image="This time the music box gave a bright little click, and the swan turned in a circle while its tune filled the room.",
        tags={"music_box", "operate", "key"},
    ),
    "rug_train": Device(
        id="rug_train",
        label="rug train",
        phrase="a little rug train with red wheels and a tiny paper station",
        required_part="red_controller",
        operate_text='Hold the controller steady and let the train circle the rug village.',
        ending_image="This time the train hummed along the rug track, passing the paper station as if it had somewhere important and cheerful to be.",
        tags={"train", "operate", "controller"},
    ),
    "paper_fan": Device(
        id="paper_fan",
        label="paper wind fan",
        phrase="a hand-run paper wind fan covered in painted flowers",
        required_part="turning_handle",
        operate_text='Fit the handle in place and turn it slowly so the petals can spin.',
        ending_image="This time the fan spun in a blur of flowers, stirring a cool little breeze that made them both laugh.",
        tags={"fan", "operate", "handle"},
    ),
}

PARTS = {
    "star_disk": Part(
        id="star_disk",
        label="star disk",
        phrase="the round star disk",
        attach_text="slid the star disk into the slot behind the lamp",
        tags={"projector", "part"},
    ),
    "brass_key": Part(
        id="brass_key",
        label="brass key",
        phrase="the tiny brass key",
        attach_text="fit the brass key into the music box and turned it once",
        tags={"music_box", "key", "part"},
    ),
    "red_controller": Part(
        id="red_controller",
        label="red controller",
        phrase="the red controller",
        attach_text="plugged the red controller back into the train's side",
        tags={"train", "controller", "part"},
    ),
    "turning_handle": Part(
        id="turning_handle",
        label="turning handle",
        phrase="the painted turning handle",
        attach_text="clicked the turning handle back onto the fan's little stem",
        tags={"fan", "handle", "part"},
    ),
}

PLACES = {
    "art_folder": Place(
        id="art_folder",
        label="the art folder",
        phrase="the big art folder by the window",
        accessible=True,
        search_text="Nora hurried to the big art folder by the window and lifted its paper flap.",
        open_text="opened the art folder",
        tags={"star_disk", "art", "reachable"},
    ),
    "sewing_basket": Place(
        id="sewing_basket",
        label="the sewing basket",
        phrase="the round sewing basket near the rocking chair",
        accessible=True,
        search_text="Nora tiptoed to the round sewing basket near the rocking chair and peeked under the soft bundles of thread.",
        open_text="lifted the lid of the sewing basket",
        tags={"brass_key", "thread", "reachable"},
    ),
    "hall_cubby": Place(
        id="hall_cubby",
        label="the hall cubby",
        phrase="the high hall cubby above the coat hooks",
        accessible=False,
        search_text="Nora stared up at the high hall cubby above the coat hooks.",
        open_text="reached up to the high cubby and drew down its small wooden box",
        tags={"red_controller", "shelf", "ask_help"},
    ),
    "button_tin": Place(
        id="button_tin",
        label="the button tin",
        phrase="the round button tin on the top shelf",
        accessible=False,
        search_text="Nora looked toward the round button tin on the top shelf.",
        open_text="took down the button tin and opened it with a soft pop",
        tags={"turning_handle", "buttons", "ask_help"},
    ),
}

CLUES = {
    "star_sketch": Clue(
        id="star_sketch",
        label="a page of star sketches",
        notice_text="Near the window, a page of star sketches peeked out from under a cushion.",
        thought_text="Stars go with the projector. If the sketch is here, maybe the missing piece was tucked into the art folder.",
        points_to="art_folder",
        tags={"clue", "art"},
    ),
    "gold_thread": Clue(
        id="gold_thread",
        label="a curl of gold thread",
        notice_text="On the table, a curl of gold thread glimmered beside the quiet music box.",
        thought_text="Gold thread belongs near Grandma's sewing things. Maybe the missing piece was set down in the sewing basket.",
        points_to="sewing_basket",
        tags={"clue", "thread"},
    ),
    "ticket_stub": Clue(
        id="ticket_stub",
        label="a tiny paper ticket",
        notice_text="By the rug station lay a tiny paper ticket, the kind Grandpa tucked into the hall cubby after playtime.",
        thought_text="If the ticket came from the hall cubby, maybe the train's missing piece was put away there too.",
        points_to="hall_cubby",
        tags={"clue", "ticket"},
    ),
    "button_rattle": Clue(
        id="button_rattle",
        label="a soft button rattle",
        notice_text="From the top shelf came a soft button rattle when the room grew quiet.",
        thought_text="That sound is coming from the button tin. Maybe the fan's missing handle was dropped in there by mistake.",
        points_to="button_tin",
        tags={"clue", "buttons"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Ella", "Lucy", "Ava", "Zoe", "Lina", "Ruby"]
BOY_NAMES = ["Leo", "Owen", "Max", "Sam", "Eli", "Noah", "Finn", "Theo"]
ELDER_NAMES = {
    "mother": ["Mom", "Mama"],
    "father": ["Dad", "Papa"],
    "grandmother": ["Grandma", "Nana"],
    "grandfather": ["Grandpa", "Pop-Pop"],
}


@dataclass
class StoryParams:
    device: str
    clue: str
    place: str
    child_name: str
    child_gender: str
    elder_type: str
    elder_name: str
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
    "operate": [
        (
            "What does operate mean?",
            "To operate something means to make it work in the right way. You might press, turn, or connect the part it needs so it can do its job."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. It does not tell the whole answer, but it points your thinking in the right direction."
        )
    ],
    "ask_help": [
        (
            "Why is it good to ask for help?",
            "Asking for help is wise when something is too high, too heavy, or too tricky to do alone. It helps people solve problems safely and together."
        )
    ],
    "projector": [
        (
            "What does a projector do?",
            "A projector shines light to make pictures appear somewhere else, like on a wall or ceiling. A small projector can turn a room into a sky full of shapes."
        )
    ],
    "music_box": [
        (
            "What is a music box?",
            "A music box is a little box that plays a tune when it is wound or opened. Many music boxes have a tiny figure that turns while the song plays."
        )
    ],
    "train": [
        (
            "What does a toy train need to move?",
            "A toy train needs the right parts connected so its power can reach the wheels. If one important piece is missing, it may stay still."
        )
    ],
    "fan": [
        (
            "What does a hand fan handle do?",
            "A turning handle gives your hand a safe place to make the fan spin. Without it, the moving part may not work the way it should."
        )
    ],
    "key": [
        (
            "What is a winding key for?",
            "A winding key stores a little twist of energy in a toy or music box. When the key is missing, the toy cannot start its motion or song."
        )
    ],
    "controller": [
        (
            "What does a controller do?",
            "A controller sends your choice to a toy so it knows when and how to move. It helps your hands guide the machine."
        )
    ],
    "thread": [
        (
            "Why would thread be a good clue near a sewing basket?",
            "Thread belongs with sewing things, so seeing it can point you toward the sewing basket. Good clues often connect to the place where matching objects are kept."
        )
    ],
    "buttons": [
        (
            "Why might a button sound point to a button tin?",
            "Buttons rattle softly when they bump together inside a tin. Hearing that sound can help you guess where a small missing object may have fallen."
        )
    ],
    "art": [
        (
            "Why would drawings belong in an art folder?",
            "An art folder keeps drawings and paper pieces flat and safe. That makes it a sensible place to look for something tucked in with art supplies."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "operate",
    "clue",
    "ask_help",
    "projector",
    "music_box",
    "train",
    "fan",
    "key",
    "controller",
    "thread",
    "buttons",
    "art",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    device_cfg = world.facts["device_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "solo":
        return [
            f'Write a heartwarming story for a 3-to-5-year-old where a child tries to operate a {device_cfg.label}, notices a clue, and solves a small mystery alone.',
            f"Tell a cozy story with dialogue and inner monologue where {child.id} realizes a needed piece is missing, follows an honest clue, and makes the {device_cfg.label} work again.",
            f'Write a gentle mystery-to-solve story that includes the word "operate" and ends with a child feeling proud after careful thinking.',
        ]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old where a child tries to operate a {device_cfg.label}, follows a clue, and asks a loving elder for help reaching the answer.',
        f"Tell a cozy story with dialogue and inner monologue where {child.id} and {elder.label_word} solve a tiny household mystery together.",
        f'Write a gentle mystery-to-solve story that includes the word "operate" and ends with a child and elder sharing a warm, happy moment.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    device_cfg = world.facts["device_cfg"]
    part_cfg = world.facts["part_cfg"]
    clue_cfg = world.facts["clue_cfg"]
    place_cfg = world.facts["place_cfg"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "What mystery did they need to solve?",
            f"They needed to find out why the {device_cfg.label} would not operate. The real problem was that {part_cfg.phrase} was missing."
        ),
        (
            f"What clue did {child.id} notice?",
            f"{child.id} noticed {clue_cfg.label}. That clue mattered because it pointed toward {place_cfg.label}, which was the place that really held the missing part."
        ),
        (
            f"How did {child.id} figure out where to look?",
            f"{child.id} stopped and thought about what the clue belonged with. That careful thinking connected {clue_cfg.label} to {place_cfg.label}."
        ),
    ]

    if outcome == "solo":
        qa.append(
            (
                f"Did {child.id} solve the mystery alone?",
                f"Yes. {child.id} could reach {place_cfg.label}, so {child.pronoun()} searched there and found {part_cfg.phrase}. That let {child.pronoun('object')} bring the piece back right away."
            )
        )
    else:
        qa.append(
            (
                f"Why did {child.id} ask {elder.label_word} for help?",
                f"{child.id} knew where the answer was, but {place_cfg.label} was too high to reach alone. Asking for help turned the clue into a shared solution instead of a stuck problem."
            )
        )

    qa.append(
        (
            f"How did the story end?",
            f"After they put {part_cfg.phrase} back, the {device_cfg.label} worked again. {device_cfg.ending_image.split('This time ', 1)[-1]}"
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["device_cfg"].tags)
    tags |= set(world.facts["part_cfg"].tags)
    tags |= set(world.facts["clue_cfg"].tags)
    tags |= set(world.facts["place_cfg"].tags)
    tags.add("operate")
    tags.add("clue")
    if world.facts["asked_help"]:
        tags.add("ask_help")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v is False}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        device="starlight_projector",
        clue="star_sketch",
        place="art_folder",
        child_name="Nora",
        child_gender="girl",
        elder_type="grandfather",
        elder_name="Grandpa",
    ),
    StoryParams(
        device="music_box",
        clue="gold_thread",
        place="sewing_basket",
        child_name="Leo",
        child_gender="boy",
        elder_type="grandmother",
        elder_name="Grandma",
    ),
    StoryParams(
        device="rug_train",
        clue="ticket_stub",
        place="hall_cubby",
        child_name="Mia",
        child_gender="girl",
        elder_type="grandfather",
        elder_name="Grandpa",
    ),
    StoryParams(
        device="paper_fan",
        clue="button_rattle",
        place="button_tin",
        child_name="Sam",
        child_gender="boy",
        elder_type="mother",
        elder_name="Mom",
    ),
]


ASP_RULES = r"""
valid(D, C, L) :- device(D), clue(C), place(L), needs(D, P), stores(L, P), points(C, L).

outcome(solo) :- chosen_place(L), accessible(L).
outcome(with_helper) :- chosen_place(L), not accessible(L).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did, device in DEVICES.items():
        lines.append(asp.fact("device", did))
        lines.append(asp.fact("needs", did, device.required_part))
    for pid in PARTS:
        lines.append(asp.fact("part", pid))
    for lid, place in PLACES.items():
        lines.append(asp.fact("place", lid))
        if place.accessible:
            lines.append(asp.fact("accessible", lid))
        for tag in sorted(place.tags):
            if tag in PARTS:
                lines.append(asp.fact("stores", lid, tag))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("points", cid, clue.points_to))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_place", params.place)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
        except StoryError:
            continue
        cases.append(params)

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
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child notices a clue and solves a small, heartwarming mystery."
    )
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--elder", choices=ELDER_NAMES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid mystery triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, gender: str, chosen_name: Optional[str] = None) -> str:
    if chosen_name:
        return chosen_name
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def pick_elder(rng: random.Random, elder_type: str) -> str:
    return rng.choice(ELDER_NAMES[elder_type])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.device and args.clue and args.place:
        if not valid_combo(args.device, args.clue, args.place):
            raise StoryError(explain_rejection(DEVICES[args.device], CLUES[args.clue], PLACES[args.place]))

    combos = [
        combo for combo in valid_combos()
        if (args.device is None or combo[0] == args.device)
        and (args.clue is None or combo[1] == args.clue)
        and (args.place is None or combo[2] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    device_id, clue_id, place_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = pick_child(rng, gender, args.child_name)
    elder_type = args.elder or rng.choice(sorted(ELDER_NAMES))
    elder_name = pick_elder(rng, elder_type)

    return StoryParams(
        device=device_id,
        clue=clue_id,
        place=place_id,
        child_name=child_name,
        child_gender=gender,
        elder_type=elder_type,
        elder_name=elder_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.device not in DEVICES:
        raise StoryError(f"(Unknown device: {params.device})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.elder_type not in ELDER_NAMES:
        raise StoryError(f"(Unknown elder type: {params.elder_type})")
    if not valid_combo(params.device, params.clue, params.place):
        raise StoryError(explain_rejection(DEVICES[params.device], CLUES[params.clue], PLACES[params.place]))

    world = tell(
        device_cfg=DEVICES[params.device],
        clue_cfg=CLUES[params.clue],
        place_cfg=PLACES[params.place],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        elder_name=params.elder_name,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (device, clue, place) mysteries:\n")
        for device_id, clue_id, place_id in combos:
            print(f"  {device_id:19} {clue_id:14} {place_id}")
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
            header = f"### {p.child_name}: {p.device} via {p.clue} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
