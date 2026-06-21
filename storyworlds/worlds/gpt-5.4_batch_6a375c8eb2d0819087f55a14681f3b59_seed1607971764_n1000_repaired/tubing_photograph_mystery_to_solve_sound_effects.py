#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tubing_photograph_mystery_to_solve_sound_effects.py
==============================================================================

A standalone story world about a missing photograph, a length of tubing, and a
small quest to solve a gentle mystery by following sounds. The prose leans
toward a nursery-rhyme cadence: child-facing, musical, and concrete.

Premise
-------
Two children are getting ready for a little display when a breeze whisks a
photograph into nearby tubing. The picture vanishes, a funny sound travels
through the tube, and the children set off on a quest to solve the mystery.
They follow the tubing, listen for the sound effects, and recover the
photograph with a sensible method.

Reasonableness gate
-------------------
The world refuses combinations that do not make physical sense:

* the chosen tubing must be wide enough for a photograph
* the destination must actually be reachable from that tubing in that place
* the retrieval method must work for that destination and must be gentle enough

The outcome model is also simple and state-based:

* dry destination, or quick recovery from a wet one -> crisp ending
* wet destination + delay -> damp ending

Run it
------
python storyworlds/worlds/gpt-5.4/tubing_photograph_mystery_to_solve_sound_effects.py
python storyworlds/worlds/gpt-5.4/tubing_photograph_mystery_to_solve_sound_effects.py --place garden --tube rain_spout --destination wash_bucket
python storyworlds/worlds/gpt-5.4/tubing_photograph_mystery_to_solve_sound_effects.py --tube narrow_whistle
python storyworlds/worlds/gpt-5.4/tubing_photograph_mystery_to_solve_sound_effects.py --all --qa
python storyworlds/worlds/gpt-5.4/tubing_photograph_mystery_to_solve_sound_effects.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    trail: str
    affords_tubes: set[str] = field(default_factory=set)
    has_destinations: set[str] = field(default_factory=set)
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
class Tube:
    id: str
    label: str
    phrase: str
    sound: str
    sound_line: str
    fit_photo: bool = True
    carries_sound: bool = True
    reaches: set[str] = field(default_factory=set)
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
class Destination:
    id: str
    label: str
    phrase: str
    wet: bool = False
    methods: set[str] = field(default_factory=set)
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
class Retrieval:
    id: str
    label: str
    gentle: int
    prose: str
    damp_prose: str
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
        return [e for e in self.entities.values() if e.role in {"hero", "helper"}]

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


def _r_sound_clue(world: World) -> list[str]:
    photo = world.get("photo")
    tube = world.get("tube")
    if photo.meters["hidden"] < THRESHOLD:
        return []
    if tube.meters["singing"] < THRESHOLD:
        return []
    sig = ("sound_clue", world.facts["tube_cfg"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["curiosity"] += 1
    world.facts["heard_sound"] = world.facts["tube_cfg"].sound
    return ["__sound__"]


def _r_damp(world: World) -> list[str]:
    photo = world.get("photo")
    dest = world.facts["destination_cfg"]
    if photo.attrs.get("destination") != dest.id:
        return []
    if not dest.wet:
        return []
    if world.facts.get("delay", 0) <= 0:
        return []
    sig = ("damp", dest.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    photo.meters["damp"] += 1
    return ["__damp__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="sound_clue", tag="quest", apply=_r_sound_clue),
    Rule(name="damp", tag="physical", apply=_r_damp),
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
                produced.extend(bits)
    if narrate:
        for text in produced:
            if text.startswith("__"):
                continue
            world.say(text)
    return produced


def destination_reachable(place: Place, tube: Tube, destination: Destination) -> bool:
    return tube.id in place.affords_tubes and destination.id in place.has_destinations and destination.id in tube.reaches


def compatible_retrievals(destination: Destination) -> list[Retrieval]:
    return [
        r for r in RETRIEVALS.values()
        if r.id in destination.methods and r.gentle >= SENSE_MIN
    ]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for tube_id, tube in TUBES.items():
            for dest_id, dest in DESTINATIONS.items():
                if tube.fit_photo and destination_reachable(place, tube, dest) and compatible_retrievals(dest):
                    out.append((place_id, tube_id, dest_id))
    return out


def outcome_of(params: "StoryParams") -> str:
    dest = DESTINATIONS[params.destination]
    return "damp" if dest.wet and params.delay > 0 else "crisp"


def explain_combo_rejection(place: Optional[Place], tube: Tube, destination: Optional[Destination]) -> str:
    if not tube.fit_photo:
        return (
            f"(No story: {tube.phrase} is too narrow for a photograph, so the mystery cannot begin there. "
            f"Pick wider tubing.)"
        )
    if place and destination and not destination_reachable(place, tube, destination):
        return (
            f"(No story: {tube.label} in {place.label} does not lead to {destination.phrase}, "
            f"so the children would have no honest clue to follow.)"
        )
    return "(No story: this combination does not make a workable tubing mystery.)"


def explain_retrieval_rejection(rid: str, destination: Destination) -> str:
    r = RETRIEVALS[rid]
    if r.gentle < SENSE_MIN:
        return (
            f"(Refusing retrieval '{rid}': it is too rough for a keepsake photograph. "
            f"Choose a gentler method.)"
        )
    return (
        f"(No story: {r.label} does not work for {destination.phrase}. "
        f"Choose a method that fits the hiding place.)"
    )


def introduce(world: World, hero: Entity, helper: Entity, photograph_name: str) -> None:
    world.say(
        f"{hero.id} and {helper.id} had a tiny morning quest. "
        f"They wanted to set out {photograph_name}, a bright old photograph, and make a little show of it."
    )
    world.say(
        f'"Tap-tap, clap-clap," sang {helper.id}, while {hero.id} held the frame and grinned.'
    )


def setting_arrival(world: World) -> None:
    place = world.place
    world.say(
        f"In {place.label}, the path curved {place.trail}. "
        f"Everything looked ready for a rhyme and ready for a secret."
    )


def lose_photo(world: World, hero: Entity, tube: Tube) -> None:
    photo = world.get("photo")
    tube_ent = world.get("tube")
    photo.meters["hidden"] += 1
    photo.attrs["inside_tube"] = tube.id
    tube_ent.meters["singing"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"But swish went the breeze, and whisk went the photograph. "
        f"It skittered off the frame and slipped into {tube.phrase}."
    )
    propagate(world, narrate=False)
    sound = world.facts.get("heard_sound", tube.sound)
    world.say(
        f'{tube.sound_line} came the tubing. "{sound}!" cried {hero.id}. '
        f'"A mystery to solve!"'
    )


def choose_quest(world: World, hero: Entity, helper: Entity, tube: Tube) -> None:
    for kid in world.kids():
        kid.memes["quest"] += 1
    world.say(
        f'"We will not stomp and we will not race," said {helper.id}. '
        f'"We will walk the tubing and follow the sound with careful feet."'
    )
    world.say(
        f"So off they went on their quest, hand by hand, tracing the bend of the {tube.label}."
    )


def follow_tube(world: World, hero: Entity, helper: Entity, destination: Destination) -> None:
    world.say(
        f"Past the stones and past the shade, the sound grew near and the puzzle grew small. "
        f'"{world.facts["tube_cfg"].sound}! {world.facts["tube_cfg"].sound}!" sang the way.'
    )
    world.say(
        f"At last they stopped beside {destination.phrase}, where the whisper of the mystery came to rest."
    )
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1


def retrieve_photo(world: World, hero: Entity, helper: Entity, retrieval: Retrieval, destination: Destination) -> None:
    photo = world.get("photo")
    photo.attrs["destination"] = destination.id
    propagate(world, narrate=False)
    photo.meters["found"] += 1
    photo.meters["hidden"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["worry"] = 0.0
    if photo.meters["damp"] >= THRESHOLD:
        world.say(
            f"{helper.id} {retrieval.damp_prose}. Out came the photograph, safe but damp at one corner."
        )
    else:
        world.say(
            f"{hero.id} {retrieval.prose}. Out came the photograph, neat and bright as morning light."
        )


def ending(world: World, hero: Entity, helper: Entity, parent: Entity, photograph_name: str) -> None:
    photo = world.get("photo")
    parent_word = parent.label_word
    if photo.meters["damp"] >= THRESHOLD:
        world.say(
            f'{parent_word.capitalize()} spread the photograph on a sunny cloth. '
            f'"Softly now, and it will dry," {parent.pronoun()} said.'
        )
        world.say(
            f"Soon the little picture lay flat again, and {hero.id} and {helper.id} sang, "
            f'"Mystery mended, quest well done; hush now, picture, drink the sun."'
        )
    else:
        world.say(
            f'{parent_word.capitalize()} tucked the photograph back in its frame, and the children danced a ring around it.'
        )
        world.say(
            f'They sang, "Mystery mended, quest well done; tubing whispered, and we won."'
        )
    world.say(
        f"And there it stayed, {photograph_name} on display, proving the puzzling picture had found its way home."
    )


def tell(
    place: Place,
    tube: Tube,
    destination: Destination,
    retrieval: Retrieval,
    hero_name: str = "Mina",
    hero_gender: str = "girl",
    helper_name: str = "Jo",
    helper_gender: str = "boy",
    parent_type: str = "mother",
    photo_subject: str = "Grandma by the gate",
    delay: int = 0,
) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", label=helper_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="tube", type="tube", label=tube.label, phrase=tube.phrase))
    world.add(Entity(
        id="photo",
        type="photograph",
        label="photograph",
        phrase="a bright old photograph",
        attrs={"inside_tube": "", "destination": "", "subject": photo_subject},
    ))
    world.facts.update(
        place_cfg=place,
        tube_cfg=tube,
        destination_cfg=destination,
        retrieval_cfg=retrieval,
        delay=delay,
        heard_sound="",
    )

    introduce(world, hero, helper, photo_subject)
    setting_arrival(world)

    world.para()
    lose_photo(world, hero, tube)
    choose_quest(world, hero, helper, tube)

    world.para()
    follow_tube(world, hero, helper, destination)
    retrieve_photo(world, hero, helper, retrieval, destination)

    world.para()
    ending(world, hero, helper, parent, photo_subject)

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        photograph_name=photo_subject,
        outcome="damp" if world.get("photo").meters["damp"] >= THRESHOLD else "crisp",
        found=world.get("photo").meters["found"] >= THRESHOLD,
    )
    return world


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden",
        trail="past tulips and stepping stones",
        affords_tubes={"wide_cardboard", "rain_spout", "narrow_whistle"},
        has_destinations={"flowerpot", "wash_bucket", "basket"},
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        trail="under the swing and by the boots",
        affords_tubes={"play_tunnel", "rain_spout", "narrow_whistle"},
        has_destinations={"boot_tray", "wagon"},
    ),
    "shed": Place(
        id="shed",
        label="the shed yard",
        trail="past seed sacks and a little rake",
        affords_tubes={"wide_cardboard", "play_tunnel"},
        has_destinations={"seed_box", "scarf_basket"},
    ),
}

TUBES = {
    "wide_cardboard": Tube(
        id="wide_cardboard",
        label="cardboard tube",
        phrase="a wide roll of cardboard tubing",
        sound="whooo",
        sound_line='"Whooo-whoo, whooo-whoo,"',
        fit_photo=True,
        carries_sound=True,
        reaches={"flowerpot", "basket", "seed_box", "scarf_basket"},
        tags={"tubing", "sound"},
    ),
    "rain_spout": Tube(
        id="rain_spout",
        label="rain spout",
        phrase="the shiny rain tubing by the wall",
        sound="plink-plink",
        sound_line='"Plink-plink, clink-clink,"',
        fit_photo=True,
        carries_sound=True,
        reaches={"wash_bucket", "boot_tray", "wagon"},
        tags={"tubing", "rain", "sound"},
    ),
    "play_tunnel": Tube(
        id="play_tunnel",
        label="play tunnel",
        phrase="the bendy play tubing by the mat",
        sound="boing-boing",
        sound_line='"Boing-boing, bong-bong,"',
        fit_photo=True,
        carries_sound=True,
        reaches={"wagon", "seed_box", "scarf_basket"},
        tags={"tubing", "sound"},
    ),
    "narrow_whistle": Tube(
        id="narrow_whistle",
        label="whistle tube",
        phrase="a skinny whistle tube",
        sound="peep-peep",
        sound_line='"Peep-peep,"',
        fit_photo=False,
        carries_sound=True,
        reaches={"flowerpot"},
        tags={"sound"},
    ),
}

DESTINATIONS = {
    "flowerpot": Destination(
        id="flowerpot",
        label="flowerpot",
        phrase="a big blue flowerpot",
        wet=False,
        methods={"lift"},
        tags={"garden"},
    ),
    "wash_bucket": Destination(
        id="wash_bucket",
        label="wash bucket",
        phrase="the wash bucket under the spout",
        wet=True,
        methods={"tip", "hook"},
        tags={"water"},
    ),
    "basket": Destination(
        id="basket",
        label="basket",
        phrase="a basket of ribbons",
        wet=False,
        methods={"lift", "hook"},
        tags={"basket"},
    ),
    "boot_tray": Destination(
        id="boot_tray",
        label="boot tray",
        phrase="the boot tray by the step",
        wet=True,
        methods={"lift", "tip"},
        tags={"water"},
    ),
    "wagon": Destination(
        id="wagon",
        label="wagon",
        phrase="a little red wagon",
        wet=False,
        methods={"lift"},
        tags={"wagon"},
    ),
    "seed_box": Destination(
        id="seed_box",
        label="seed box",
        phrase="a wooden seed box",
        wet=False,
        methods={"lift"},
        tags={"shed"},
    ),
    "scarf_basket": Destination(
        id="scarf_basket",
        label="scarf basket",
        phrase="a basket of soft scarves",
        wet=False,
        methods={"lift", "hook"},
        tags={"basket"},
    ),
}

RETRIEVALS = {
    "lift": Retrieval(
        id="lift",
        label="lifted the edge carefully",
        gentle=3,
        prose="lifted the edge carefully and peeked beneath",
        damp_prose="lifted the edge carefully and let the water slip away",
        qa_text="They lifted the hiding place carefully and took the picture out.",
        tags={"gentle"},
    ),
    "tip": Retrieval(
        id="tip",
        label="tipped it slowly",
        gentle=2,
        prose="tipped it slowly until the picture slid into waiting hands",
        damp_prose="tipped it slowly until the picture slid free from the wet rim",
        qa_text="They tipped the hiding place slowly so the picture could slide out safely.",
        tags={"gentle"},
    ),
    "hook": Retrieval(
        id="hook",
        label="used a ribbon hook",
        gentle=2,
        prose="used a ribbon hook and drew the picture out by one loose corner",
        damp_prose="used a ribbon hook and drew the picture out before it soaked any more",
        qa_text="They used a soft ribbon hook to pull the picture out without scrunching it.",
        tags={"tool"},
    ),
    "poke": Retrieval(
        id="poke",
        label="poked hard",
        gentle=1,
        prose="poked hard until the picture popped free",
        damp_prose="poked hard until the picture flopped out",
        qa_text="They poked hard at the hiding place.",
        tags={"rough"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Poppy", "Nell", "Ivy", "Mabel", "Tess", "June"]
BOY_NAMES = ["Jo", "Toby", "Milo", "Ben", "Finn", "Ned", "Ollie", "Kit"]
PHOTO_SUBJECTS = [
    "Grandma by the gate",
    "the duck pond parade",
    "the moon kite picnic",
    "a cake with seven candles",
]


@dataclass
class StoryParams:
    place: str
    tube: str
    destination: str
    retrieval: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    photo_subject: str
    delay: int = 0
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


def pair_word(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two children"
    if a.type == "boy" and b.type == "boy":
        return "two children"
    return "two children"


KNOWLEDGE = {
    "tubing": [
        (
            "What is tubing?",
            "Tubing is a long hollow tube that can carry air or water from one place to another. If you talk or blow across some tubing, it can make funny sounds."
        )
    ],
    "sound": [
        (
            "Why did the tubing make a sound?",
            "Air moved through the tube and made it hum or ring. Different kinds of tubing can make different noises."
        )
    ],
    "photograph": [
        (
            "What is a photograph?",
            "A photograph is a picture made with a camera. People keep photographs because they help us remember a person, a place, or a happy day."
        )
    ],
    "water": [
        (
            "Why should you be careful with a photograph near water?",
            "Water can make a photograph bend, blur, or curl. That is why people try to keep pictures dry."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a little journey with a goal. You set out to find something, solve something, or help someone."
        )
    ],
    "gentle": [
        (
            "Why is it better to handle a keepsake gently?",
            "A keepsake can tear, crease, or get scratched if you are rough with it. Gentle hands help special things stay safe."
        )
    ],
}
KNOWLEDGE_ORDER = ["tubing", "sound", "photograph", "water", "quest", "gentle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    tube = f["tube_cfg"]
    return [
        f'Write a nursery-rhyme style story for a 3-to-5-year-old that includes the words "tubing" and "photograph", plus a mystery to solve and a quest.',
        f"Tell a gentle mystery where {hero.id} and {helper.id} follow the sound in {tube.phrase} to find a missing photograph.",
        "Write a musical, child-facing story with sound effects, a lost picture, and a happy little investigation.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    tube = f["tube_cfg"]
    destination = f["destination_cfg"]
    retrieval = f["retrieval_cfg"]
    photo_subject = f["photograph_name"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_word(hero, helper)}, {hero.id} and {helper.id}, who set out to find a missing photograph. {parent.label_word.capitalize()} is there at the end to help them settle it safely."
        ),
        (
            "What was the mystery to solve?",
            f"The mystery was where the photograph of {photo_subject} had gone after the breeze whisked it away. It vanished into the tubing, so the children had to follow a real clue instead of just guessing."
        ),
        (
            "What clue helped them on their quest?",
            f'The clue was the sound coming through the tubing: "{tube.sound}." They listened to that sound and followed the tube until they reached the hiding place.'
        ),
        (
            f"Where did they find the photograph?",
            f"They found it at {destination.phrase}. The tubing led there, so the end of the sound pointed them to the answer."
        ),
        (
            "How did they get the photograph back?",
            f"{retrieval.qa_text} They were careful because a photograph is easy to bend or tear."
        ),
    ]
    if outcome == "damp":
        qa.append(
            (
                "Was the photograph still perfect when they found it?",
                f"Not quite. It was safe, but one corner was damp because it had reached a wet place and the children were not there at once. Then {parent.label_word} spread it on a sunny cloth so it could dry."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with the photograph back in its frame. The ending image shows that the mystery was truly solved because the picture was home again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"tubing", "sound", "photograph", "quest", "gentle"}
    if world.facts["destination_cfg"].wet or world.facts["outcome"] == "damp":
        tags.add("water")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        tube="wide_cardboard",
        destination="flowerpot",
        retrieval="lift",
        hero_name="Mina",
        hero_gender="girl",
        helper_name="Jo",
        helper_gender="boy",
        parent="mother",
        photo_subject="Grandma by the gate",
        delay=0,
    ),
    StoryParams(
        place="porch",
        tube="rain_spout",
        destination="boot_tray",
        retrieval="tip",
        hero_name="Poppy",
        hero_gender="girl",
        helper_name="Ned",
        helper_gender="boy",
        parent="father",
        photo_subject="the duck pond parade",
        delay=1,
    ),
    StoryParams(
        place="shed",
        tube="play_tunnel",
        destination="scarf_basket",
        retrieval="hook",
        hero_name="Ivy",
        hero_gender="girl",
        helper_name="Kit",
        helper_gender="boy",
        parent="mother",
        photo_subject="the moon kite picnic",
        delay=0,
    ),
]


ASP_RULES = r"""
photo_fits(T) :- tube(T), fit_photo(T).

reachable(P,T,D) :- place(P), tube(T), destination(D),
                    affords_tube(P,T), has_destination(P,D), tube_reaches(T,D).

sensible_retrieval(R) :- retrieval(R), gentle(R,G), sense_min(M), G >= M.
usable_retrieval(D,R) :- destination_method(D,R), sensible_retrieval(R).

valid(P,T,D) :- photo_fits(T), reachable(P,T,D), usable_retrieval(D,_).

outcome(damp) :- chosen_destination(D), wet(D), delay(N), N > 0.
outcome(crisp) :- not outcome(damp).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for tid in sorted(place.affords_tubes):
            lines.append(asp.fact("affords_tube", pid, tid))
        for did in sorted(place.has_destinations):
            lines.append(asp.fact("has_destination", pid, did))
    for tid, tube in TUBES.items():
        lines.append(asp.fact("tube", tid))
        if tube.fit_photo:
            lines.append(asp.fact("fit_photo", tid))
        for did in sorted(tube.reaches):
            lines.append(asp.fact("tube_reaches", tid, did))
    for did, destination in DESTINATIONS.items():
        lines.append(asp.fact("destination", did))
        if destination.wet:
            lines.append(asp.fact("wet", did))
        for rid in sorted(destination.methods):
            lines.append(asp.fact("destination_method", did, rid))
    for rid, retrieval in RETRIEVALS.items():
        lines.append(asp.fact("retrieval", rid))
        lines.append(asp.fact("gentle", rid, retrieval.gentle))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_retrievals() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_retrieval/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_retrieval"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_destination", params.destination),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible_retrievals())
    python_sensible = {rid for rid, r in RETRIEVALS.items() if r.gentle >= SENSE_MIN}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible retrievals match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible retrievals: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: tubing, a missing photograph, and a nursery-rhyme mystery quest."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tube", choices=TUBES)
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--retrieval", choices=RETRIEVALS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="0 = quick recovery, 1 = late enough for a wet ending")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, tube, destination) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tube:
        tube = TUBES[args.tube]
        if not tube.fit_photo:
            raise StoryError(explain_combo_rejection(PLACES[args.place] if args.place else None, tube, DESTINATIONS[args.destination] if args.destination else None))

    if args.place and args.tube and args.destination:
        place = PLACES[args.place]
        tube = TUBES[args.tube]
        dest = DESTINATIONS[args.destination]
        if not destination_reachable(place, tube, dest) or not tube.fit_photo or not compatible_retrievals(dest):
            raise StoryError(explain_combo_rejection(place, tube, dest))

    if args.retrieval and args.destination:
        dest = DESTINATIONS[args.destination]
        if args.retrieval not in dest.methods or RETRIEVALS[args.retrieval].gentle < SENSE_MIN:
            raise StoryError(explain_retrieval_rejection(args.retrieval, dest))
    elif args.retrieval and RETRIEVALS[args.retrieval].gentle < SENSE_MIN:
        rough_destination = next(iter(DESTINATIONS.values()))
        raise StoryError(explain_retrieval_rejection(args.retrieval, rough_destination))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.tube is None or combo[1] == args.tube)
        and (args.destination is None or combo[2] == args.destination)
        and (args.retrieval is None or args.retrieval in DESTINATIONS[combo[2]].methods)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, tube_id, destination_id = rng.choice(sorted(combos))
    destination = DESTINATIONS[destination_id]
    retrieval_choices = [r.id for r in compatible_retrievals(destination)]
    if args.retrieval:
        if args.retrieval not in retrieval_choices:
            raise StoryError(explain_retrieval_rejection(args.retrieval, destination))
        retrieval_id = args.retrieval
    else:
        retrieval_id = rng.choice(sorted(retrieval_choices))

    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    photo_subject = rng.choice(PHOTO_SUBJECTS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)

    return StoryParams(
        place=place_id,
        tube=tube_id,
        destination=destination_id,
        retrieval=retrieval_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        photo_subject=photo_subject,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.tube not in TUBES:
        raise StoryError(f"(Unknown tube: {params.tube})")
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")
    if params.retrieval not in RETRIEVALS:
        raise StoryError(f"(Unknown retrieval: {params.retrieval})")

    place = PLACES[params.place]
    tube = TUBES[params.tube]
    destination = DESTINATIONS[params.destination]
    retrieval = RETRIEVALS[params.retrieval]

    if not tube.fit_photo or not destination_reachable(place, tube, destination) or not compatible_retrievals(destination):
        raise StoryError(explain_combo_rejection(place, tube, destination))
    if retrieval.id not in destination.methods or retrieval.gentle < SENSE_MIN:
        raise StoryError(explain_retrieval_rejection(retrieval.id, destination))

    world = tell(
        place=place,
        tube=tube,
        destination=destination,
        retrieval=retrieval,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        photo_subject=params.photo_subject,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible_retrieval/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible_retrievals()
        print(f"sensible retrievals: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, tube, destination) combos:\n")
        for place, tube, destination in combos:
            print(f"  {place:8} {tube:14} {destination}")
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
            header = f"### {p.hero_name} & {p.helper_name}: {p.tube} to {p.destination} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
