#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/debbie_music_alum_petting_zoo_bad_ending.py
======================================================================

A standalone story world about Debbie bringing music to a petting zoo with help
from a friend and a kind alum volunteer. The domain models a simple tension:
some animals enjoy gentle music, but a loud instrument too near a gate can scare
them into a panicky rush. Teamwork can prevent the trouble, or, if the choice is
poor and the response is too weak, the afternoon ends sadly.

The seed words "debbie", "music", and "alum" are included naturally in the
stories and prompt space. The tone stays child-facing and heartwarming even when
the ending is unhappy: the people care for one another, learn, and keep everyone
safe.

Run it
------
    python storyworlds/worlds/gpt-5.4/debbie_music_alum_petting_zoo_bad_ending.py
    python storyworlds/worlds/gpt-5.4/debbie_music_alum_petting_zoo_bad_ending.py --animal rabbits --instrument flute
    python storyworlds/worlds/gpt-5.4/debbie_music_alum_petting_zoo_bad_ending.py --animal rabbits --instrument drum
    python storyworlds/worlds/gpt-5.4/debbie_music_alum_petting_zoo_bad_ending.py --all
    python storyworlds/worlds/gpt-5.4/debbie_music_alum_petting_zoo_bad_ending.py --qa --json
    python storyworlds/worlds/gpt-5.4/debbie_music_alum_petting_zoo_bad_ending.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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


@dataclass
class AnimalCfg:
    id: str
    label: str
    group: str
    timid: int
    likes_music: bool = True
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
class InstrumentCfg:
    id: str
    label: str
    phrase: str
    loudness: int
    sound: str
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
class SpotCfg:
    id: str
    label: str
    phrase: str
    near_gate: bool
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
class HelpCfg:
    id: str
    label: str
    sense: int
    control: int
    text: str
    fail_text: str
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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.facts = copy.deepcopy(self.facts)
        return out


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


def _r_fear(world: World) -> list[str]:
    animal = world.get("animal")
    gate = world.get("gate")
    if animal.meters["startled"] < THRESHOLD:
        return []
    sig = ("fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.memes["fear"] += 1
    gate.meters["strain"] += 1
    for eid in ("debbie", "friend", "helper"):
        world.get(eid).memes["worry"] += 1
    return ["__fear__"]


def _r_escape(world: World) -> list[str]:
    animal = world.get("animal")
    gate = world.get("gate")
    if animal.memes["fear"] < THRESHOLD:
        return []
    if gate.meters["open"] < THRESHOLD:
        return []
    sig = ("escape",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.meters["escaped"] += 1
    world.get("yard").meters["closed"] += 1
    for eid in ("debbie", "friend", "helper"):
        world.get(eid).memes["sadness"] += 1
    return ["__escape__"]


CAUSAL_RULES = [
    Rule(name="fear", tag="emotional", apply=_r_fear),
    Rule(name="escape", tag="physical", apply=_r_escape),
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


ANIMALS = {
    "goats": AnimalCfg(
        id="goats",
        label="goats",
        group="the little goats",
        timid=2,
        likes_music=True,
        tags={"goat", "animals"},
    ),
    "lambs": AnimalCfg(
        id="lambs",
        label="lambs",
        group="the soft lambs",
        timid=3,
        likes_music=True,
        tags={"lamb", "animals"},
    ),
    "rabbits": AnimalCfg(
        id="rabbits",
        label="rabbits",
        group="the shy rabbits",
        timid=4,
        likes_music=True,
        tags={"rabbit", "animals"},
    ),
}

INSTRUMENTS = {
    "humming": InstrumentCfg(
        id="humming",
        label="humming",
        phrase="a soft humming tune",
        loudness=1,
        sound="a low, warm hum",
        tags={"music", "gentle_music"},
    ),
    "flute": InstrumentCfg(
        id="flute",
        label="flute",
        phrase="a small flute",
        loudness=2,
        sound="a thin silver tune",
        tags={"music", "flute"},
    ),
    "drum": InstrumentCfg(
        id="drum",
        label="drum",
        phrase="a hand drum",
        loudness=4,
        sound="a big bouncy boom",
        tags={"music", "drum"},
    ),
}

SPOTS = {
    "bench": SpotCfg(
        id="bench",
        label="bench",
        phrase="from the wooden bench outside the pen",
        near_gate=False,
        tags={"bench"},
    ),
    "fence": SpotCfg(
        id="fence",
        label="fence",
        phrase="beside the fence rail",
        near_gate=False,
        tags={"fence"},
    ),
    "gate": SpotCfg(
        id="gate",
        label="gate",
        phrase="right beside the half-latched gate",
        near_gate=True,
        tags={"gate"},
    ),
}

HELPS = {
    "close_gate": HelpCfg(
        id="close_gate",
        label="close the gate",
        sense=3,
        control=3,
        text="the alum volunteer clicked the gate shut while Debbie and her friend stepped back and kept the tune small and slow",
        fail_text="the alum volunteer lunged for the gate, but the frightened animals bumped it wider first",
        qa_text="the alum volunteer shut the gate and the children stepped back together",
        tags={"gate_safety", "teamwork"},
    ),
    "hay_screen": HelpCfg(
        id="hay_screen",
        label="hold up a hay screen",
        sense=3,
        control=2,
        text="the alum volunteer and Debbie lifted a light hay screen between the music and the pen while Debbie's friend whispered for everyone to stay still",
        fail_text="they lifted the hay screen, but the sound was already too sharp and the animals rushed before the screen was in place",
        qa_text="they used a hay screen and stood still together",
        tags={"teamwork", "calming_animals"},
    ),
    "call_keeper": HelpCfg(
        id="call_keeper",
        label="call the keeper",
        sense=2,
        control=1,
        text="the alum volunteer called the keeper over while the two children lowered the music and folded their hands",
        fail_text="they called the keeper, but the animals had already darted through the open gate",
        qa_text="they called the keeper and lowered the music",
        tags={"teamwork", "keeper"},
    ),
}

GIRL_NAMES = ["Debbie", "Lily", "Mia", "Anna", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Eli", "Jack"]


def acceptable_music(animal: AnimalCfg, instrument: InstrumentCfg) -> bool:
    return instrument.loudness <= animal.timid


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for animal_id, animal in ANIMALS.items():
        for inst_id, inst in INSTRUMENTS.items():
            if not acceptable_music(animal, inst):
                continue
            for spot_id in SPOTS:
                combos.append((animal_id, inst_id, spot_id))
    return combos


def panic_risk(animal: AnimalCfg, instrument: InstrumentCfg, spot: SpotCfg) -> int:
    return max(0, instrument.loudness - animal.timid) + (2 if spot.near_gate else 0)


def is_contained(animal: AnimalCfg, instrument: InstrumentCfg, spot: SpotCfg, help_cfg: HelpCfg) -> bool:
    risk = panic_risk(animal, instrument, spot)
    if risk <= 0:
        return True
    return help_cfg.control >= risk


def explain_rejection(animal: AnimalCfg, instrument: InstrumentCfg) -> str:
    return (
        f"(No story: {instrument.label} is too loud for {animal.group}. "
        f"This world only tells reasonable setups where the starting plan is kind "
        f"enough that music belongs at a petting zoo at all.)"
    )


@dataclass
class StoryParams:
    animal: str
    instrument: str
    spot: str
    help_action: str
    debbie_friend: str
    friend_gender: str
    alum_name: str
    alum_type: str
    parent_word: str = "teacher"
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


def introduce(world: World, animal: AnimalCfg, instrument: InstrumentCfg, spot: SpotCfg) -> None:
    debbie = world.get("debbie")
    friend = world.get("friend")
    helper = world.get("helper")
    animal_ent = world.get("animal")
    debbie.memes["joy"] += 1
    friend.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"One bright afternoon at the petting zoo, debbie and {friend.id} came with a little plan."
    )
    world.say(
        f"They wanted to share {instrument.phrase} {spot.phrase} so {animal.group} would hear something gentle while children brushed and fed them."
    )
    world.say(
        f"With them was {helper.id}, a kind school alum who volunteered on weekends and always moved as if the animals' feelings mattered."
    )
    animal_ent.memes["calm"] += 1


def teamwork_setup(world: World, animal: AnimalCfg, instrument: InstrumentCfg) -> None:
    debbie = world.get("debbie")
    friend = world.get("friend")
    helper = world.get("helper")
    debbie.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"Debbie held the music sheet, {world.get('friend').id} carried the brush basket, and {helper.id} checked the path with the keeper."
    )
    world.say(
        f"For a moment, everything felt warm and easy, and even {animal.group} seemed to listen with their noses lifted."
    )


def warning(world: World, animal: AnimalCfg, instrument: InstrumentCfg, spot: SpotCfg) -> None:
    helper = world.get("helper")
    if spot.near_gate:
        world.say(
            f'"Let us stay careful by the gate," {helper.id} said. "Animals can jump when a sound surprises them."'
        )
    else:
        world.say(
            f'"Soft music is best here," {helper.id} reminded them. "We want the animals to feel safe, not startled."'
        )


def start_music(world: World, animal: AnimalCfg, instrument: InstrumentCfg, spot: SpotCfg) -> None:
    debbie = world.get("debbie")
    friend = world.get("friend")
    animal_ent = world.get("animal")
    gate = world.get("gate")
    world.say(
        f"Then Debbie began {instrument.sound}, and {friend.id} smiled and found the beat with small careful steps."
    )
    risk = panic_risk(animal, instrument, spot)
    if risk > 0:
        animal_ent.meters["startled"] += 1
        if spot.near_gate:
            gate.meters["open"] += 1
        propagate(world, narrate=False)
        world.say(
            f"But the sound landed too hard for {animal.group}. Ears flicked, hooves or paws scrambled, and the happy little circle broke apart."
        )
    else:
        animal_ent.memes["calm"] += 1
        world.say(
            f"The tune stayed light and kind. {animal.group.capitalize()} shuffled closer, not from fear, but from simple curious listening."
        )


def try_to_fix(world: World, help_cfg: HelpCfg, contained: bool, animal: AnimalCfg, instrument: InstrumentCfg, spot: SpotCfg) -> None:
    helper = world.get("helper")
    debbie = world.get("debbie")
    friend = world.get("friend")
    debbie.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    if panic_risk(animal, instrument, spot) <= 0:
        world.say(
            f"{helper.id} nodded proudly as the three of them kept working together, each one making the quiet moment easier."
        )
        return
    if contained:
        world.say(
            f"No one shouted. The three of them moved together at once, and {help_cfg.text}."
        )
        world.get("gate").meters["open"] = 0.0
        world.get("animal").meters["escaped"] = 0.0
        world.get("animal").memes["fear"] = 0.0
        world.get("animal").memes["calm"] += 1
    else:
        world.say(
            f"They tried to help together, and {help_cfg.fail_text}."
        )
        world.get("animal").meters["escaped"] += 1
        world.get("yard").meters["closed"] += 1


def good_ending(world: World, animal: AnimalCfg, instrument: InstrumentCfg) -> None:
    debbie = world.get("debbie")
    friend = world.get("friend")
    helper = world.get("helper")
    debbie.memes["relief"] += 1
    friend.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"After that, Debbie changed the music to a smaller tune, and {animal.group} settled again."
    )
    world.say(
        f"Children took turns brushing soft fur and wool, and the alum volunteer smiled to see teamwork sound almost as sweet as the music itself."
    )
    world.say(
        f"When the afternoon ended, Debbie knew the best part had not been being loud or grand. It had been making something gentle together."
    )


def bad_ending(world: World, animal: AnimalCfg, instrument: InstrumentCfg) -> None:
    debbie = world.get("debbie")
    friend = world.get("friend")
    helper = world.get("helper")
    yard = world.get("yard")
    debbie.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    helper.memes["care"] += 1
    yard.meters["closed"] += 1
    world.say(
        f"One frightened animal slipped out, and the petting zoo had to close that corner while the keeper guided it back."
    )
    world.say(
        f"Nobody was hurt, and Debbie, {friend.id}, and {helper.id} stayed together quietly until the pen was safe again."
    )
    world.say(
        f"The music time was over for that day. Debbie went home sad, but with a tender new lesson in her chest: teamwork matters most when it begins early, before fear has started running."
    )


def tell(
    animal: AnimalCfg,
    instrument: InstrumentCfg,
    spot: SpotCfg,
    help_cfg: HelpCfg,
    debbie_friend: str,
    friend_gender: str,
    alum_name: str,
    alum_type: str,
    parent_word: str,
) -> World:
    world = World()
    debbie = world.add(Entity(id="Debbie", kind="character", type="girl", role="lead", label="debbie"))
    friend = world.add(Entity(id=debbie_friend, kind="character", type=friend_gender, role="friend"))
    helper = world.add(Entity(id=alum_name, kind="character", type=alum_type, role="helper", attrs={"alum": True}))
    animal_ent = world.add(Entity(id="animal", kind="thing", type="animal", label=animal.label, tags=set(animal.tags)))
    gate = world.add(Entity(id="gate", kind="thing", type="gate", label="gate"))
    yard = world.add(Entity(id="yard", kind="thing", type="yard", label="petting zoo yard"))

    world.facts["seed_word_debbie"] = "debbie"
    world.facts["seed_word_music"] = "music"
    world.facts["seed_word_alum"] = "alum"
    world.facts["parent_word"] = parent_word

    introduce(world, animal, instrument, spot)
    teamwork_setup(world, animal, instrument)

    world.para()
    warning(world, animal, instrument, spot)
    start_music(world, animal, instrument, spot)

    contained = is_contained(animal, instrument, spot, help_cfg)

    world.para()
    try_to_fix(world, help_cfg, contained, animal, instrument, spot)

    world.para()
    if contained:
        good_ending(world, animal, instrument)
        outcome = "contained"
    else:
        bad_ending(world, animal, instrument)
        outcome = "bad"

    world.facts.update(
        animal_cfg=animal,
        instrument_cfg=instrument,
        spot_cfg=spot,
        help_cfg=help_cfg,
        debbie=debbie,
        friend=friend,
        helper=helper,
        outcome=outcome,
        startled=world.get("animal").meters["startled"] >= THRESHOLD,
        escaped=world.get("animal").meters["escaped"] >= THRESHOLD,
        teamwork_used=True,
    )
    return world


KNOWLEDGE = {
    "music": [
        (
            "Why should music be gentle around animals?",
            "Animals can hear and feel sounds strongly, and a sudden loud noise can scare them. Gentle music gives them time to stay calm."
        )
    ],
    "goat": [
        (
            "How do goats show they feel jumpy?",
            "Goats may hop, bunch together, or bump toward the edge of a pen when they feel startled. Their quick feet show they want more space."
        )
    ],
    "lamb": [
        (
            "Why do lambs like calm handling?",
            "Lambs do best when people move softly and speak gently. Quiet handling helps them feel safe."
        )
    ],
    "rabbit": [
        (
            "Why can rabbits be frightened by noise?",
            "Rabbits are small and alert, so loud sounds can make them bolt before people even notice. Quiet places help them feel safe."
        )
    ],
    "drum": [
        (
            "Why might a drum be too loud for a petting zoo pen?",
            "A drum can make a strong booming sound that reaches animals all at once. That kind of sudden noise can feel scary in a small space."
        )
    ],
    "flute": [
        (
            "What does a flute sound like?",
            "A flute can sound light and airy, like a thin stream of song. Soft flute music can be gentle when it is played carefully."
        )
    ],
    "gentle_music": [
        (
            "What is gentle music?",
            "Gentle music is quiet, slow, and smooth enough that it does not startle others. It is the kind of sound that leaves room for calm."
        )
    ],
    "gate_safety": [
        (
            "Why must a gate stay shut at a petting zoo?",
            "A shut gate keeps animals in the place where they are meant to be safe. An open gate can let a frightened animal rush somewhere dangerous."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another toward the same safe goal. Small careful actions can fit together like puzzle pieces."
        )
    ],
    "keeper": [
        (
            "What does a zoo keeper do?",
            "A keeper watches over the animals and knows how to handle them safely. If something goes wrong, the keeper helps calm the situation."
        )
    ],
    "calming_animals": [
        (
            "How can people help calm scared animals?",
            "They can get quieter, move slowly, and give the animals more space. Calm people often help animals calm down too."
        )
    ],
    "animals": [
        (
            "Why do petting zoo animals need kind visitors?",
            "Petting zoo animals meet many people, so they need gentle hands and quiet choices. Kind visitors help the animals feel safe all day."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "animals",
    "music",
    "gentle_music",
    "drum",
    "flute",
    "goat",
    "lamb",
    "rabbit",
    "gate_safety",
    "calming_animals",
    "keeper",
    "teamwork",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal = f["animal_cfg"]
    instrument = f["instrument_cfg"]
    helper = f["helper"]
    outcome = f["outcome"]
    if outcome == "bad":
        return [
            f'Write a heartwarming-but-sad story set at a petting zoo that includes the exact words "debbie", "music", and "alum". Debbie tries to share {instrument.label} music with {animal.label}, and teamwork matters after things go wrong.',
            f"Tell a story where Debbie, a friend, and an alum volunteer work together at a petting zoo, but a frightened animal escapes and the music time ends early.",
            f"Write a gentle cautionary story for young children about kind music, animal feelings, and teamwork that comes too late to stop a bad ending.",
        ]
    return [
        f'Write a heartwarming story set at a petting zoo that includes the exact words "debbie", "music", and "alum". Debbie brings gentle {instrument.label} music and learns how teamwork keeps animals calm.',
        f"Tell a story where Debbie, a friend, and an alum volunteer cooperate during a petting zoo music activity and keep {animal.label} safe.",
        f"Write a child-friendly story about music, teamwork, and making careful choices around animals.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    animal = f["animal_cfg"]
    instrument = f["instrument_cfg"]
    spot = f["spot_cfg"]
    help_cfg = f["help_cfg"]
    friend = f["friend"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Debbie, {friend.id}, and {helper.id}, a kind alum volunteer at the petting zoo. They were trying to bring music to {animal.group} together."
        ),
        (
            "What did Debbie want to do?",
            f"Debbie wanted to share {instrument.phrase} near {animal.group}. She hoped the music would make the petting zoo feel gentle and welcoming."
        ),
        (
            "How did teamwork appear in the story?",
            f"Each person had a job: Debbie led the music, {friend.id} helped with the brushing basket, and {helper.id} watched the animals and the space. Their choices mattered because caring for animals works best when people pay attention together."
        ),
    ]
    if f["startled"]:
        qa.append(
            (
                f"Why did the animals get scared?",
                f"They were startled because the {instrument.label} was too strong for {animal.group} in that moment. The trouble grew faster because the music was happening {spot.phrase}."
            )
        )
    else:
        qa.append(
            (
                "Why did the animals stay calm?",
                f"They stayed calm because the music was gentle enough for {animal.group}. The careful place and soft sound gave them room to listen without fear."
            )
        )
    if outcome == "contained":
        qa.append(
            (
                "How did they solve the problem?",
                f"They solved it by working together right away: {help_cfg.qa_text}. Their quick, calm teamwork kept the pen safe and helped the animals settle again."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended warmly. Debbie kept the music gentle, the animals calmed down, and the afternoon became kind again."
            )
        )
    else:
        qa.append(
            (
                "What made the ending sad?",
                f"One animal slipped out and the petting zoo had to stop the music time. Nobody was hurt, but Debbie lost the happy afternoon she had hoped for because fear had already started the rush."
            )
        )
        qa.append(
            (
                "What did Debbie learn?",
                f"Debbie learned that kindness to animals must begin before the scary moment, not after it. Teamwork still helped keep everyone safe, but it could not give the music time back."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["animal_cfg"].tags) | set(f["instrument_cfg"].tags) | set(f["help_cfg"].tags) | {"teamwork"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
acceptable(A,I) :- animal(A), instrument(I), timid(A,T), loudness(I,L), L <= T.
valid(A,I,S) :- acceptable(A,I), spot(S).

risk(A,I,S,0) :- acceptable(A,I), spot(S), not near_gate(S).
risk(A,I,S,2) :- acceptable(A,I), spot(S), near_gate(S).

risk(A,I,S,R) :- animal(A), instrument(I), spot(S),
                 timid(A,T), loudness(I,L), L > T, not near_gate(S), R = L - T.
risk(A,I,S,R) :- animal(A), instrument(I), spot(S),
                 timid(A,T), loudness(I,L), L > T, near_gate(S), R = L - T + 2.

contained :- chosen_animal(A), chosen_instrument(I), chosen_spot(S), chosen_help(H),
             risk(A,I,S,R), control(H,C), R <= C.
outcome(contained) :- contained.
outcome(bad) :- not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        lines.append(asp.fact("timid", animal_id, animal.timid))
    for inst_id, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", inst_id))
        lines.append(asp.fact("loudness", inst_id, inst.loudness))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        if spot.near_gate:
            lines.append(asp.fact("near_gate", spot_id))
    for help_id, help_cfg in HELPS.items():
        lines.append(asp.fact("help", help_id))
        lines.append(asp.fact("control", help_id, help_cfg.control))
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
            asp.fact("chosen_animal", params.animal),
            asp.fact("chosen_instrument", params.instrument),
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_help", params.help_action),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        animal="goats",
        instrument="humming",
        spot="bench",
        help_action="close_gate",
        debbie_friend="Ben",
        friend_gender="boy",
        alum_name="Mara",
        alum_type="woman",
        parent_word="teacher",
    ),
    StoryParams(
        animal="lambs",
        instrument="flute",
        spot="fence",
        help_action="hay_screen",
        debbie_friend="Nora",
        friend_gender="girl",
        alum_name="Evan",
        alum_type="man",
        parent_word="teacher",
    ),
    StoryParams(
        animal="goats",
        instrument="humming",
        spot="gate",
        help_action="call_keeper",
        debbie_friend="Sam",
        friend_gender="boy",
        alum_name="Iris",
        alum_type="woman",
        parent_word="teacher",
    ),
    StoryParams(
        animal="rabbits",
        instrument="flute",
        spot="gate",
        help_action="call_keeper",
        debbie_friend="Mia",
        friend_gender="girl",
        alum_name="Noah",
        alum_type="man",
        parent_word="teacher",
    ),
]


def outcome_of(params: StoryParams) -> str:
    animal = ANIMALS[params.animal]
    inst = INSTRUMENTS[params.instrument]
    spot = SPOTS[params.spot]
    help_cfg = HELPS[params.help_action]
    return "contained" if is_contained(animal, inst, spot, help_cfg) else "bad"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: Debbie brings music to a petting zoo, helped by a friend and an alum volunteer."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--help-action", dest="help_action", choices=HELPS)
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
    ap.add_argument("--alum-name", dest="alum_name")
    ap.add_argument("--alum-type", dest="alum_type", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.instrument:
        animal = ANIMALS[args.animal]
        inst = INSTRUMENTS[args.instrument]
        if not acceptable_music(animal, inst):
            raise StoryError(explain_rejection(animal, inst))

    combos = [
        combo
        for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.instrument is None or combo[1] == args.instrument)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal_id, instrument_id, spot_id = rng.choice(sorted(combos))
    help_action = args.help_action or rng.choice(sorted(HELPS.keys()))
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    friend_name = args.friend or _pick_name(rng, friend_gender, avoid="Debbie")
    alum_type = args.alum_type or rng.choice(["woman", "man"])
    alum_name = args.alum_name or _pick_name(rng, "girl" if alum_type == "woman" else "boy", avoid=friend_name)
    return StoryParams(
        animal=animal_id,
        instrument=instrument_id,
        spot=spot_id,
        help_action=help_action,
        debbie_friend=friend_name,
        friend_gender=friend_gender,
        alum_name=alum_name,
        alum_type=alum_type,
        parent_word="teacher",
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.instrument not in INSTRUMENTS:
        raise StoryError(f"(Unknown instrument: {params.instrument})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.help_action not in HELPS:
        raise StoryError(f"(Unknown help action: {params.help_action})")

    animal = ANIMALS[params.animal]
    instrument = INSTRUMENTS[params.instrument]
    spot = SPOTS[params.spot]
    if not acceptable_music(animal, instrument):
        raise StoryError(explain_rejection(animal, instrument))

    world = tell(
        animal=animal,
        instrument=instrument,
        spot=spot,
        help_cfg=HELPS[params.help_action],
        debbie_friend=params.debbie_friend,
        friend_gender=params.friend_gender,
        alum_name=params.alum_name,
        alum_type=params.alum_type,
        parent_word=params.parent_word,
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
        print(f"{len(combos)} compatible (animal, instrument, spot) combos:\n")
        for animal, inst, spot in combos:
            print(f"  {animal:8} {inst:8} {spot}")
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
            header = f"### Debbie with {p.debbie_friend}: {p.instrument} for {p.animal} at {p.spot} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
