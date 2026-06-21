#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/flush_adopt_happy_ending_ghost_story.py
==================================================================

A small story world for gentle ghost-story-shaped tales where a child hears a
"ghost" in the house, a household clue reveals the truth, and the family ends
by rescuing and adopting a frightened stray animal.

The seed asked for the words "flush" and "adopt", a happy ending, and a ghost
story style. This world therefore models:

- a spooky nighttime setup
- an eerie sound source that seems ghostly at first
- a reasoned investigation by a calm grown-up
- a concrete rescue that must fit the hiding place
- a warm ending where the family may adopt the rescued animal

The turning point is state-driven: a bathroom flush sends sound through the old
pipes or nearby spaces, helping the child and grown-up realize that the "ghost"
is really a living creature in trouble.

Run it
------
    python storyworlds/worlds/gpt-5.4/flush_adopt_happy_ending_ghost_story.py
    python storyworlds/worlds/gpt-5.4/flush_adopt_happy_ending_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/flush_adopt_happy_ending_ghost_story.py --seed 7 -n 5 --qa
    python storyworlds/worlds/gpt-5.4/flush_adopt_happy_ending_ghost_story.py --trace
    python storyworlds/worlds/gpt-5.4/flush_adopt_happy_ending_ghost_story.py --asp
    python storyworlds/worlds/gpt-5.4/flush_adopt_happy_ending_ghost_story.py --verify
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
    tiny: bool = False
    climby: bool = False
    likes_food: bool = False
    likes_warmth: bool = False
    has_paws: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"kitten", "puppy", "animal"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Mood:
    id: str
    opening: str
    light_line: str
    fear_line: str
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
class HidingPlace:
    id: str
    label: str
    the: str
    room: str
    spooky_detail: str
    echo_kind: str
    near_pipes: bool
    narrow: bool
    high: bool
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class AnimalType:
    id: str
    label: str
    cry: str
    adjective: str
    adopt_line: str
    tiny: bool = True
    climby: bool = False
    likes_food: bool = True
    likes_warmth: bool = True
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
class Reveal:
    id: str
    text: str
    works_near_pipes: bool
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
class RescueMethod:
    id: str
    sense: int
    needs_narrow: bool = False
    needs_high: bool = False
    requires_food: bool = False
    text: str = ""
    qa_text: str = ""
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


def _r_eerie_sound(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("place")
    animal = world.get("animal")
    if animal.meters["trapped"] < THRESHOLD:
        return out
    sig = ("eerie", place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.meters["noise"] += 1
    for ent in list(world.entities.values()):
        if ent.role in {"child", "parent"}:
            ent.memes["alert"] += 1
    out.append("__eerie__")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.get("place").meters["noise"] < THRESHOLD:
        return out
    for ent in list(world.entities.values()):
        if ent.role != "child":
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("used_reveal"):
        return out
    place = world.get("place")
    if place.meters["echo_heard"] < THRESHOLD or world.get("animal").meters["trapped"] < THRESHOLD:
        return out
    sig = ("reveal", place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["ghost_guess"] = False
    world.facts["animal_located"] = True
    world.get("child").memes["hope"] += 1
    world.get("parent").memes["focus"] += 1
    out.append("__reveal__")
    return out


def _r_rescue(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("used_rescue"):
        return out
    if not world.facts.get("animal_located"):
        return out
    animal = world.get("animal")
    sig = ("rescue", animal.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.meters["trapped"] = 0.0
    animal.meters["safe"] += 1
    animal.memes["trust"] += 1
    child = world.get("child")
    parent = world.get("parent")
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["love"] += 1
    parent.memes["relief"] += 1
    out.append("__rescue__")
    return out


CAUSAL_RULES = [
    Rule(name="eerie_sound", tag="physical", apply=_r_eerie_sound),
    Rule(name="fear", tag="emotional", apply=_r_fear),
    Rule(name="reveal", tag="inference", apply=_r_reveal),
    Rule(name="rescue", tag="physical", apply=_r_rescue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def reveal_works(reveal: Reveal, place: HidingPlace) -> bool:
    return reveal.works_near_pipes and place.near_pipes


def rescue_works(method: RescueMethod, place: HidingPlace, animal: AnimalType) -> bool:
    if method.sense < SENSE_MIN:
        return False
    if method.needs_narrow and not place.narrow:
        return False
    if method.needs_high and not place.high:
        return False
    if method.requires_food and not animal.likes_food:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for mood_id in MOODS:
        for place_id, place in PLACES.items():
            for animal_id, animal in ANIMALS.items():
                for reveal_id, reveal in REVEALS.items():
                    if reveal_works(reveal, place):
                        combos.append((mood_id, place_id, animal_id, reveal_id))
    return combos


def sensible_rescues_for(place: HidingPlace, animal: AnimalType) -> list[str]:
    return [rid for rid, method in RESCUES.items() if rescue_works(method, place, animal)]


def predict_after_flush(place: HidingPlace, reveal: Reveal) -> dict:
    ghost_guess = True
    animal_located = False
    if reveal_works(reveal, place):
        ghost_guess = False
        animal_located = True
    return {"ghost_guess": ghost_guess, "animal_located": animal_located}


def introduce_night(world: World, child: Entity, mood: Mood, place: HidingPlace) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Late one windy evening, {child.id} lay awake while the house made its old nighttime sounds. "
        f"{mood.opening}"
    )
    world.say(
        f"From {place.the} came a thin little cry and a soft scratch-scratch, as if "
        f"{place.spooky_detail}."
    )


def fear_ghost(world: World, child: Entity, mood: Mood, place: HidingPlace) -> None:
    world.say(
        f"{child.id} pulled the blanket up to {child.pronoun('possessive')} chin. "
        f'"Is there a ghost in {place.the}?" {child.pronoun()} whispered.'
    )
    world.say(mood.fear_line)


def fetch_parent(world: World, child: Entity, parent: Entity) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"Instead of hiding alone, {child.id} padded down the hall and woke "
        f"{child.pronoun('possessive')} {parent.label}."
    )
    world.say(
        f'{parent.label.capitalize()} sat up, listened once, and took {child.pronoun("possessive")} hand. '
        f'"Let\'s look carefully," {parent.pronoun()} said. "Scary sounds still come from something real."'
    )


def investigate(world: World, child: Entity, parent: Entity, place: HidingPlace, animal: AnimalType) -> None:
    world.say(
        f"They followed the sound to {place.the} by the {place.room}. The cry came again: "
        f"{animal.cry}! Then everything went still."
    )
    world.say(
        f"The shadows looked long, and {mood_line(world)}"
    )


def mood_line(world: World) -> str:
    mood = world.facts["mood_cfg"]
    return mood.light_line


def do_flush_reveal(world: World, child: Entity, parent: Entity, place: HidingPlace, reveal: Reveal) -> None:
    pred = predict_after_flush(place, reveal)
    world.facts["predicted_located"] = pred["animal_located"]
    world.facts["used_reveal"] = True
    place_ent = world.get("place")
    place_ent.meters["echo_heard"] += 1
    propagate(world, narrate=False)
    world.say(reveal.text.format(place=place.the, room=place.room))
    if pred["animal_located"]:
        world.say(
            f"When the flush finished rushing through the pipes, the sound answered from one exact spot in {place.the}. "
            f'"That is not a ghost," {parent.label} said softly. "That sounds like a little animal."'
        )
    else:
        world.say(
            "The sound moved strangely through the walls, and for a moment the mystery only felt deeper."
        )


def prepare_rescue(world: World, child: Entity, parent: Entity, place: HidingPlace, animal: AnimalType) -> None:
    child.memes["hope"] += 1
    parent.memes["focus"] += 1
    world.say(
        f"{child.id}'s fear changed shape. It was still a little scary, but now the scary thing seemed hurt instead of haunted."
    )
    world.say(
        f'"If something tiny is stuck in {place.the}, we have to help it," {child.pronoun()} said.'
    )


def do_rescue(world: World, parent: Entity, place: HidingPlace, animal: AnimalType, method: RescueMethod) -> None:
    world.facts["used_rescue"] = True
    propagate(world, narrate=False)
    world.say(method.text.format(place=place.the, animal=animal.label, parent=parent.label))
    world.say(
        f"Out came a {animal.adjective} {animal.label}, shivering but alive, with bright eyes instead of ghost eyes."
    )


def comfort_and_adopt(world: World, child: Entity, parent: Entity, animal: AnimalType, mood: Mood) -> None:
    animal_ent = world.get("animal")
    animal_ent.memes["warmth"] += 1
    child.memes["love"] += 1
    child.memes["joy"] += 1
    parent.memes["love"] += 1
    world.say(
        f"{parent.label.capitalize()} wrapped the little {animal.label} in a towel, and {child.id} held out gentle hands."
    )
    world.say(
        f'Soon the tiny creature was drinking warm milk from a saucer and making a soft, sleepy sound. '
        f'"Can we adopt it?" {child.id} asked.'
    )
    world.say(
        f'{parent.label.capitalize()} smiled. "{animal.adopt_line}," {parent.pronoun()} said. '
        f'The house did not feel haunted anymore. {mood.ending_image}'
    )


def tell(
    mood: Mood,
    place: HidingPlace,
    animal_cfg: AnimalType,
    reveal: Reveal,
    rescue: RescueMethod,
    child_name: str = "Mina",
    child_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={},
    ))
    parent_label = "mom" if parent_type == "mother" else "dad"
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=parent_label,
        role="parent",
        attrs={},
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
        role="place",
        attrs={"room": place.room, "near_pipes": place.near_pipes, "narrow": place.narrow, "high": place.high},
    ))
    animal = world.add(Entity(
        id="animal",
        kind="thing",
        type=animal_cfg.id,
        label=animal_cfg.label,
        role="animal",
        attrs={},
        tiny=animal_cfg.tiny,
        climby=animal_cfg.climby,
        likes_food=animal_cfg.likes_food,
        likes_warmth=animal_cfg.likes_warmth,
    ))
    animal.meters["trapped"] = 1.0
    world.facts["ghost_guess"] = True
    world.facts["animal_located"] = False
    world.facts["used_reveal"] = False
    world.facts["used_rescue"] = False
    world.facts["mood_cfg"] = mood
    world.facts["place_cfg"] = place
    world.facts["animal_cfg"] = animal_cfg
    world.facts["reveal_cfg"] = reveal
    world.facts["rescue_cfg"] = rescue
    world.facts["child"] = child
    world.facts["parent"] = parent

    propagate(world, narrate=False)

    introduce_night(world, child, mood, place)
    fear_ghost(world, child, mood, place)

    world.para()
    fetch_parent(world, child, parent)
    investigate(world, child, parent, place, animal_cfg)
    do_flush_reveal(world, child, parent, place, reveal)

    world.para()
    prepare_rescue(world, child, parent, place, animal_cfg)
    do_rescue(world, parent, place, animal_cfg, rescue)
    comfort_and_adopt(world, child, parent, animal_cfg, mood)

    world.facts.update(
        resolved=world.get("animal").meters["safe"] >= THRESHOLD,
        adopted=True,
        story_kind="happy_ghost",
    )
    return world


MOODS = {
    "whispery": Mood(
        id="whispery",
        opening="The curtains lifted and settled like pale hands, and the moon made silver puddles on the floor.",
        light_line="even the moonlight looked like a row of quiet little ghosts on the tiles.",
        fear_line="The room felt full of whispers, though really it was only the child and the dark.",
        ending_image="Moonlight lay softly on the floor, and now it looked gentle instead of eerie.",
        tags={"ghost", "night"},
    ),
    "foggy": Mood(
        id="foggy",
        opening="Outside, mist pressed against the window, and every creak seemed to come from farther away than it really did.",
        light_line="the hallway bulb made a small gold island in a sea of dark.",
        fear_line="Every tiny noise sounded bigger at night, the way stories do when the house is quiet.",
        ending_image="The hallway lamp glowed warm and steady, and the shadows had nothing left to hide.",
        tags={"ghost", "night"},
    ),
    "hollow": Mood(
        id="hollow",
        opening="The old boards gave small sighs, and the night air slid under the doors with a hushy sound.",
        light_line="the shadows stretched thin and wobbly across the wall like slow gray smoke.",
        fear_line="For one shivery moment, the whole house seemed to be listening too.",
        ending_image="Soon the old house sounded friendly again, with only sleepy little rustles and a happy purr.",
        tags={"ghost", "night"},
    ),
}

PLACES = {
    "bath_panel": HidingPlace(
        id="bath_panel",
        label="the bathroom panel",
        the="the loose bathroom panel",
        room="the bathroom",
        spooky_detail="someone hidden behind the wall was whispering through the pipes",
        echo_kind="pipe_echo",
        near_pipes=True,
        narrow=True,
        high=False,
        tags={"bathroom", "pipes"},
    ),
    "tub_gap": HidingPlace(
        id="tub_gap",
        label="the gap beside the tub",
        the="the narrow gap beside the old tub",
        room="the bathroom",
        spooky_detail="a tiny voice had slipped into the wall and could not get back out",
        echo_kind="pipe_echo",
        near_pipes=True,
        narrow=True,
        high=False,
        tags={"bathroom", "pipes"},
    ),
    "laundry_vent": HidingPlace(
        id="laundry_vent",
        label="the laundry vent",
        the="the rattly laundry vent",
        room="the laundry room",
        spooky_detail="the house itself was breathing in a chilly iron throat",
        echo_kind="vent_echo",
        near_pipes=True,
        narrow=True,
        high=True,
        tags={"laundry", "vent", "pipes"},
    ),
}

ANIMALS = {
    "kitten": AnimalType(
        id="kitten",
        label="kitten",
        cry="mew",
        adjective="sooty",
        adopt_line="I think this little kitten has chosen us, and we can adopt it if we promise to care for it well",
        tiny=True,
        climby=True,
        likes_food=True,
        likes_warmth=True,
        tags={"kitten", "pet"},
    ),
    "puppy": AnimalType(
        id="puppy",
        label="puppy",
        cry="yip",
        adjective="mud-speckled",
        adopt_line="If we help this puppy, feed it, and keep it warm, yes, we can adopt it",
        tiny=True,
        climby=False,
        likes_food=True,
        likes_warmth=True,
        tags={"puppy", "pet"},
    ),
    "bunny": AnimalType(
        id="bunny",
        label="bunny",
        cry="sniff-sniff",
        adjective="trembling",
        adopt_line="We can ask the neighbors first, but if no one is missing this bunny, we can adopt it and make it a safe home",
        tiny=True,
        climby=False,
        likes_food=True,
        likes_warmth=True,
        tags={"bunny", "pet"},
    ),
}

REVEALS = {
    "toilet_flush": Reveal(
        id="toilet_flush",
        text='To test the sound, {parent} gave the toilet handle a careful push. A long flush swirled and rushed under {place}.',
        works_near_pipes=True,
        tags={"flush", "pipes"},
    ),
    "sink_flush": Reveal(
        id="sink_flush",
        text='To test the old pipes, {parent} turned the tap and then let the basin flush itself empty in a glugging swirl near {place}.',
        works_near_pipes=True,
        tags={"flush", "pipes"},
    ),
}

RESCUES = {
    "panel_lift": RescueMethod(
        id="panel_lift",
        sense=3,
        needs_narrow=True,
        needs_high=False,
        requires_food=False,
        text="{parent_cap} fetched a screwdriver, loosened the edge of {place}, and lifted it just enough to make a small safe opening.",
        qa_text="lifted the panel with a screwdriver to make a safe opening",
        tags={"rescue", "tool"},
    ),
    "towel_food": RescueMethod(
        id="towel_food",
        sense=3,
        needs_narrow=False,
        needs_high=False,
        requires_food=True,
        text="{parent_cap} spread a towel on the floor, set a little dish of food nearby, and waited quietly until the {animal} crept out from {place}.",
        qa_text="used a towel and a little food to coax the animal out",
        tags={"rescue", "food"},
    ),
    "step_stool_reach": RescueMethod(
        id="step_stool_reach",
        sense=3,
        needs_narrow=False,
        needs_high=True,
        requires_food=False,
        text="{parent_cap} brought a step stool, peered into {place}, and gently reached in with careful hands until the {animal} could be lifted free.",
        qa_text="used a step stool to reach up and lift the animal free",
        tags={"rescue", "high_place"},
    ),
    "broom_poke": RescueMethod(
        id="broom_poke",
        sense=1,
        needs_narrow=False,
        needs_high=False,
        requires_food=False,
        text="{parent_cap} poked clumsily with a broom at {place}.",
        qa_text="poked with a broom",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zoe", "Iris", "Ella", "Maya"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Ben", "Noah", "Finn", "Max", "Leo"]


@dataclass
class StoryParams:
    mood: str
    place: str
    animal: str
    reveal: str
    rescue: str
    child_name: str
    child_gender: str
    parent: str
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
        mood="whispery",
        place="bath_panel",
        animal="kitten",
        reveal="toilet_flush",
        rescue="panel_lift",
        child_name="Mina",
        child_gender="girl",
        parent="mother",
    ),
    StoryParams(
        mood="foggy",
        place="tub_gap",
        animal="bunny",
        reveal="toilet_flush",
        rescue="towel_food",
        child_name="Theo",
        child_gender="boy",
        parent="father",
    ),
    StoryParams(
        mood="hollow",
        place="laundry_vent",
        animal="puppy",
        reveal="sink_flush",
        rescue="step_stool_reach",
        child_name="Iris",
        child_gender="girl",
        parent="mother",
    ),
    StoryParams(
        mood="foggy",
        place="laundry_vent",
        animal="kitten",
        reveal="toilet_flush",
        rescue="step_stool_reach",
        child_name="Ben",
        child_gender="boy",
        parent="father",
    ),
    StoryParams(
        mood="whispery",
        place="tub_gap",
        animal="puppy",
        reveal="sink_flush",
        rescue="towel_food",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
    ),
]


KNOWLEDGE = {
    "flush": [
        (
            "What does flush mean in a bathroom?",
            "To flush means to send water rushing through a toilet or drain. The moving water can make a loud swirling sound in the pipes.",
        )
    ],
    "ghost": [
        (
            "Why can a house sound spooky at night?",
            "At night, small sounds can seem bigger because everything else is quiet. Pipes, wind, and creaky boards can make ordinary noises feel mysterious.",
        )
    ],
    "adopt": [
        (
            "What does adopt mean for a pet?",
            "To adopt a pet means to bring it into your family and promise to care for it. You give it food, safety, and a home.",
        )
    ],
    "kitten": [
        (
            "Why might a kitten hide in a tight place?",
            "A kitten is tiny and can squeeze into small spaces when it feels scared. Warm, hidden places can seem safe to it.",
        )
    ],
    "puppy": [
        (
            "Why does a puppy need help if it gets stuck?",
            "A puppy is small and can get frightened or trapped where it cannot climb back out. It needs a calm person to help it get safe again.",
        )
    ],
    "bunny": [
        (
            "Why do bunnies get scared easily?",
            "Bunnies are small prey animals, so sudden noises and strange places can frighten them. They feel safer in quiet, gentle hands.",
        )
    ],
    "pipes": [
        (
            "Why do pipes make echoes?",
            "Pipes are hollow, so sounds can bounce inside them and travel in odd ways. That can make a little sound seem far away or ghostly.",
        )
    ],
    "rescue": [
        (
            "What is a good way to rescue a trapped animal?",
            "Move slowly, stay gentle, and make a safe opening or a calm path out. Loud grabbing or poking can scare the animal more.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "flush", "pipes", "kitten", "puppy", "bunny", "rescue", "adopt"]


def normalize_rescue_text(text: str, parent_label: str) -> str:
    text = text.replace("{parent_cap}", parent_label.capitalize())
    text = text.replace("{parent}", parent_label)
    return text


def explain_reveal(place: HidingPlace, reveal: Reveal) -> str:
    if not place.near_pipes:
        return f"(No story: {reveal.id} would not help near {place.the} because there are no nearby pipes to carry the sound.)"
    return "(No story: this reveal does not fit the hiding place.)"


def explain_rescue(place: HidingPlace, animal: AnimalType, rescue: RescueMethod) -> str:
    if rescue.sense < SENSE_MIN:
        return (
            f"(Refusing rescue '{rescue.id}': it scores too low on common sense "
            f"(sense={rescue.sense} < {SENSE_MIN}). Pick a calmer, safer rescue.)"
        )
    if rescue.needs_high and not place.high:
        return f"(No story: {rescue.id} only makes sense for a high hiding place, but {place.the} is not high up.)"
    if rescue.needs_narrow and not place.narrow:
        return f"(No story: {rescue.id} is for a narrow opening, but {place.the} is not a narrow trap.)"
    if rescue.requires_food and not animal.likes_food:
        return f"(No story: {animal.label} would not be reasonably coaxed by food here.)"
    return "(No story: the rescue method does not fit this situation.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    mood = f["mood_cfg"]
    place = f["place_cfg"]
    animal = f["animal_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "flush" and "adopt" and ends happily.',
        f"Tell a spooky-but-kind story where {child.id} thinks a ghost is hiding in {place.the}, but {child.pronoun('possessive')} {parent.label} discovers a trapped {animal.label} instead.",
        f"Write a short night story with whispery shadows, one mysterious sound, and a warm ending where a family helps a tiny animal and decides to adopt it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    place = f["place_cfg"]
    animal = f["animal_cfg"]
    reveal = f["reveal_cfg"]
    rescue = f["rescue_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who heard a spooky sound at night, and {child.pronoun('possessive')} {parent.label}, who helped investigate it. Together they found a trapped {animal.label} instead of a ghost.",
        ),
        (
            f"Why did {child.id} think there might be a ghost?",
            f"{child.id} heard a thin cry and scratching from {place.the} in the dark. At night, the odd echo and the shadows made the sound seem much stranger than it really was.",
        ),
        (
            "What did the flush help them discover?",
            f"The flush sent rushing water through the old pipes and made the sound answer from one exact spot. That helped {parent.label} realize the noise came from a little animal trapped in {place.the}, not from a ghost.",
        ),
        (
            f"How did {parent.label} rescue the animal?",
            f"{parent.label.capitalize()} {rescue.qa_text}. The rescue worked because that method fit the place where the frightened {animal.label} was stuck.",
        ),
        (
            f"Why did the family decide to adopt the {animal.label}?",
            f"They had already helped the little creature, warmed it, and seen how scared it had been. By the end it felt safe in their hands, so adopting it turned the scary night into a loving new beginning.",
        ),
        (
            "How did the story end?",
            f"It ended happily, with the house feeling warm instead of haunted. The mysterious cry became a rescued {animal.label}, and the family chose to adopt it.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    animal = f["animal_cfg"]
    tags = {"ghost", "flush", "pipes", "rescue", "adopt", animal.id}
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
            shown = {k: v for k, v in ent.attrs.items() if v or isinstance(v, bool)}
            if shown:
                bits.append(f"attrs={shown}")
        flags = []
        if ent.tiny:
            flags.append("tiny")
        if ent.climby:
            flags.append("climby")
        if ent.likes_food:
            flags.append("likes_food")
        if ent.likes_warmth:
            flags.append("likes_warmth")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(M, P, A, Rv) :- mood(M), place(P), animal(A), reveal(Rv), works_reveal(Rv, P).
sensible_rescue(R) :- rescue(R), sense(R, S), sense_min(M), S >= M.

rescue_ok(R, P, A) :- rescue(R), sensible_rescue(R),
                      not needs_high(R), not needs_narrow(R), not needs_food(R).
rescue_ok(R, P, A) :- rescue(R), sensible_rescue(R),
                      needs_high(R), high(P),
                      not needs_narrow(R), not needs_food(R).
rescue_ok(R, P, A) :- rescue(R), sensible_rescue(R),
                      needs_narrow(R), narrow(P),
                      not needs_high(R), not needs_food(R).
rescue_ok(R, P, A) :- rescue(R), sensible_rescue(R),
                      needs_food(R), likes_food(A),
                      not needs_high(R), not needs_narrow(R).
rescue_ok(R, P, A) :- rescue(R), sensible_rescue(R),
                      needs_high(R), high(P),
                      needs_narrow(R), narrow(P),
                      not needs_food(R).
rescue_ok(R, P, A) :- rescue(R), sensible_rescue(R),
                      needs_high(R), high(P),
                      needs_food(R), likes_food(A),
                      not needs_narrow(R).
rescue_ok(R, P, A) :- rescue(R), sensible_rescue(R),
                      needs_narrow(R), narrow(P),
                      needs_food(R), likes_food(A),
                      not needs_high(R).
rescue_ok(R, P, A) :- rescue(R), sensible_rescue(R),
                      needs_high(R), high(P),
                      needs_narrow(R), narrow(P),
                      needs_food(R), likes_food(A).

% The happy ending in this world requires both the reveal and the rescue.
happy_story(M, P, A, Rv, R) :- valid(M, P, A, Rv), rescue_ok(R, P, A).

#show valid/4.
#show sensible_rescue/1.
#show rescue_ok/3.
#show happy_story/5.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mood_id in MOODS:
        lines.append(asp.fact("mood", mood_id))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.near_pipes:
            lines.append(asp.fact("near_pipes", pid))
        if place.narrow:
            lines.append(asp.fact("narrow", pid))
        if place.high:
            lines.append(asp.fact("high", pid))
    for aid, animal in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        if animal.likes_food:
            lines.append(asp.fact("likes_food", aid))
    for rid, reveal in REVEALS.items():
        lines.append(asp.fact("reveal", rid))
        if reveal.works_near_pipes:
            for pid, place in PLACES.items():
                if place.near_pipes:
                    lines.append(asp.fact("works_reveal", rid, pid))
    for rid, rescue in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("sense", rid, rescue.sense))
        if rescue.needs_high:
            lines.append(asp.fact("needs_high", rid))
        if rescue.needs_narrow:
            lines.append(asp.fact("needs_narrow", rid))
        if rescue.requires_food:
            lines.append(asp.fact("needs_food", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_rescues() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(r for (r,) in asp.atoms(model, "sensible_rescue"))


def asp_rescue_ok(place_id: str, animal_id: str) -> list[str]:
    import asp

    show = f"{asp_facts()}\n{ASP_RULES}\nchosen_place({place_id}).\nchosen_animal({animal_id}).\n#show ok/1.\nok(R) :- rescue_ok(R, {place_id}, {animal_id}).\n"
    model = asp.one_model(show)
    return sorted(r for (r,) in asp.atoms(model, "ok"))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: reveal gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid reveal combos:")
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))

    py_sens = {rid for rid, rescue in RESCUES.items() if rescue.sense >= SENSE_MIN}
    cl_sens = set(asp_sensible_rescues())
    if py_sens == cl_sens:
        print(f"OK: sensible rescues match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible rescues: clingo={sorted(cl_sens)} python={sorted(py_sens)}")

    bad = []
    for place_id, place in PLACES.items():
        for animal_id, animal in ANIMALS.items():
            py = set(sensible_rescues_for(place, animal))
            cl = set(asp_rescue_ok(place_id, animal_id))
            if py != cl:
                bad.append((place_id, animal_id, sorted(py), sorted(cl)))
    if not bad:
        print(f"OK: rescue compatibility matches on {len(PLACES) * len(ANIMALS)} place/animal pairs.")
    else:
        rc = 1
        print("MISMATCH in rescue compatibility:")
        for item in bad[:10]:
            print(" ", item)

    try:
        sample = generate(CURATED[0])
        if not sample.story or "flush" not in sample.story.lower() or "adopt" not in sample.story.lower():
            raise StoryError("smoke test failed: story missing required seed words")
        print("OK: smoke test generate() succeeded and includes required words.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story storyworld: a spooky sound, a flush through the pipes, a rescue, and a happy adopt ending."
    )
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations and compatible rescues from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.reveal:
        place = PLACES[args.place]
        reveal = REVEALS[args.reveal]
        if not reveal_works(reveal, place):
            raise StoryError(explain_reveal(place, reveal))

    combos = [
        combo for combo in valid_combos()
        if (args.mood is None or combo[0] == args.mood)
        and (args.place is None or combo[1] == args.place)
        and (args.animal is None or combo[2] == args.animal)
        and (args.reveal is None or combo[3] == args.reveal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mood_id, place_id, animal_id, reveal_id = rng.choice(sorted(combos))
    place = PLACES[place_id]
    animal = ANIMALS[animal_id]

    if args.rescue:
        if not rescue_works(RESCUES[args.rescue], place, animal):
            raise StoryError(explain_rescue(place, animal, RESCUES[args.rescue]))
        rescue_id = args.rescue
    else:
        rescue_choices = sensible_rescues_for(place, animal)
        if not rescue_choices:
            raise StoryError("(No sensible rescue fits the chosen place and animal.)")
        rescue_id = rng.choice(sorted(rescue_choices))

    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        mood=mood_id,
        place=place_id,
        animal=animal_id,
        reveal=reveal_id,
        rescue=rescue_id,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mood not in MOODS:
        raise StoryError(f"(Unknown mood: {params.mood})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.reveal not in REVEALS:
        raise StoryError(f"(Unknown reveal: {params.reveal})")
    if params.rescue not in RESCUES:
        raise StoryError(f"(Unknown rescue: {params.rescue})")

    mood = MOODS[params.mood]
    place = PLACES[params.place]
    animal = ANIMALS[params.animal]
    reveal = REVEALS[params.reveal]
    rescue = RESCUES[params.rescue]

    if not reveal_works(reveal, place):
        raise StoryError(explain_reveal(place, reveal))
    if not rescue_works(rescue, place, animal):
        raise StoryError(explain_rescue(place, animal, rescue))

    rescue_text = copy.deepcopy(rescue)
    rescue_text.text = normalize_rescue_text(rescue.text, "mom" if params.parent == "mother" else "dad")

    world = tell(
        mood=mood,
        place=place,
        animal_cfg=animal,
        reveal=reveal,
        rescue=rescue_text,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible rescues: {', '.join(asp_sensible_rescues())}\n")
        print(f"{len(asp_valid_combos())} valid (mood, place, animal, reveal) combos:\n")
        for mood_id, place_id, animal_id, reveal_id in asp_valid_combos():
            ok = asp_rescue_ok(place_id, animal_id)
            print(f"  {mood_id:10} {place_id:13} {animal_id:8} {reveal_id:13} rescues=[{', '.join(ok)}]")
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
            header = f"### {p.child_name}: {p.place}, {p.animal}, {p.rescue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
