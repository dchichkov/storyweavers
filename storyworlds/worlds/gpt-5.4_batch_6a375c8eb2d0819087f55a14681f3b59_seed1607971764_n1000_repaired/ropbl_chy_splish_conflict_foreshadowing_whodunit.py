#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ropbl_chy_splish_conflict_foreshadowing_whodunit.py
==============================================================================

A standalone storyworld for a tiny child-facing whodunit.

Premise
-------
Two children are setting up a small mystery game when an important object goes
missing. They begin to blame each other, but the room had already been full of
small foreshadowing sounds: "ropbl", "chy", and "splish". By following the
right clue instead of the loudest accusation, they solve the case, learn to
look before blaming, and end with the mystery game repaired.

This world models:
- a missing object with physical state
- a culprit that can reasonably move it
- a conflict beat caused by accusation
- foreshadowing sounds tied to the real culprit
- a reveal driven by simulated clues, not by swapping nouns in a fixed paragraph

Run it
------
python storyworlds/worlds/gpt-5.4/ropbl_chy_splish_conflict_foreshadowing_whodunit.py
python storyworlds/worlds/gpt-5.4/ropbl_chy_splish_conflict_foreshadowing_whodunit.py --all
python storyworlds/worlds/gpt-5.4/ropbl_chy_splish_conflict_foreshadowing_whodunit.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/ropbl_chy_splish_conflict_foreshadowing_whodunit.py --asp
python storyworlds/worlds/gpt-5.4/ropbl_chy_splish_conflict_foreshadowing_whodunit.py --verify
"""

from __future__ import annotations

import argparse
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        animal = {"puppy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    id: str
    place: str
    scene: str
    supports: set[str] = field(default_factory=set)
    has_window: bool = False
    has_puppy: bool = False
    has_sibling_nook: bool = False
    window_spot: str = ""
    puppy_spot: str = ""
    sibling_spot: str = ""
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
class MissingItem:
    id: str
    label: str
    phrase: str
    size: str
    light: bool
    soft: bool
    game_use: str
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
class Culprit:
    id: str
    label: str
    type: str
    sound: str
    clue: str
    reason: str
    apology_fix: str
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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
class StoryParams:
    setting: str
    item: str
    culprit: str
    sleuth: str
    sleuth_gender: str
    friend: str
    friend_gender: str
    adult: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"sleuth", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_missing_tension(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None or item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_tension",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room = world.get("room")
    room.meters["tension"] += 1
    for child in world.children():
        child.memes["worry"] += 1
    return []


def _r_accusation_conflict(world: World) -> list[str]:
    accuser = world.entities.get("sleuth")
    friend = world.entities.get("friend")
    if accuser is None or friend is None:
        return []
    if accuser.memes["accused"] < THRESHOLD:
        return []
    sig = ("accusation_conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] += 1
    friend.memes["conflict"] += 1
    accuser.memes["conflict"] += 1
    world.get("room").meters["conflict"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None or item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["tension"] = 0.0
    world.get("room").meters["conflict"] = 0.0
    for child in world.children():
        child.memes["relief"] += 1
        child.memes["worry"] = 0.0
        child.memes["conflict"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="missing_tension", tag="social", apply=_r_missing_tension),
    Rule(name="accusation_conflict", tag="social", apply=_r_accusation_conflict),
    Rule(name="found_relief", tag="social", apply=_r_found_relief),
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


SETTINGS = {
    "clubhouse": Setting(
        id="clubhouse",
        place="the clubhouse",
        scene="a blanket clubhouse with a tiny detective desk and a rain-speckled window",
        supports={"puppy", "sibling", "wind"},
        has_window=True,
        has_puppy=True,
        has_sibling_nook=True,
        window_spot="under the toy chest by the open window",
        puppy_spot="inside the puppy's soft basket",
        sibling_spot="inside the little blanket fort",
        tags={"clubhouse", "mystery"},
    ),
    "classroom": Setting(
        id="classroom",
        place="the classroom reading corner",
        scene="a reading corner with a chalkboard, cubbies, and a wide window cracked for fresh air",
        supports={"sibling", "wind"},
        has_window=True,
        has_puppy=False,
        has_sibling_nook=True,
        window_spot="behind the low bookcase near the open window",
        puppy_spot="",
        sibling_spot="inside the cardboard castle by the rug",
        tags={"classroom", "mystery"},
    ),
    "porch": Setting(
        id="porch",
        place="the back porch",
        scene="a covered porch with boot trays, a bench, and a drip pail by the steps",
        supports={"puppy", "wind"},
        has_window=False,
        has_puppy=True,
        has_sibling_nook=False,
        window_spot="",
        puppy_spot="under the bench beside the boot tray",
        sibling_spot="",
        tags={"porch", "mystery"},
    ),
}

ITEMS = {
    "ribbon": MissingItem(
        id="ribbon",
        label="blue ribbon",
        phrase="a shiny blue ribbon",
        size="small",
        light=True,
        soft=True,
        game_use="the prize ribbon for the winner of their make-believe mystery game",
        tags={"ribbon", "light"},
    ),
    "bell": MissingItem(
        id="bell",
        label="gold bell",
        phrase="a tiny gold bell",
        size="small",
        light=False,
        soft=False,
        game_use="the bell that was supposed to ring when the mystery was solved",
        tags={"bell", "metal"},
    ),
    "map": MissingItem(
        id="map",
        label="secret map",
        phrase="a folded secret map drawn in green crayon",
        size="small",
        light=True,
        soft=False,
        game_use="the map that showed where the next clue should be hidden",
        tags={"map", "paper"},
    ),
}

CULPRITS = {
    "puppy": Culprit(
        id="puppy",
        label="the puppy",
        type="puppy",
        sound="splish",
        clue="wet pawprints",
        reason="The puppy thought it was part of the game and carried it off to make a nest.",
        apology_fix="They tucked the item back where it belonged and gave the puppy a chew toy of its own.",
        tags={"puppy", "wet", "splish"},
    ),
    "sibling": Culprit(
        id="sibling",
        label="the little sibling",
        type="girl",
        sound="chy",
        clue="chalk dust and a crooked crown drawing",
        reason="The little sibling borrowed it to decorate a royal parade in the next nook.",
        apology_fix="They invited the little sibling to join the game instead of sneaking pieces away.",
        tags={"sibling", "chalk", "chy"},
    ),
    "wind": Culprit(
        id="wind",
        label="the gusty wind",
        type="thing",
        sound="ropbl",
        clue="a fluttering curtain and a wet sill beside the drip pail",
        reason="A gust slipped through and whisked the light object away before anyone noticed.",
        apology_fix="They closed the window, set the drip pail straight, and clipped the clue pieces down.",
        tags={"wind", "window", "ropbl"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Lucy", "Ella", "Maya"]
BOY_NAMES = ["Tom", "Max", "Sam", "Leo", "Ben", "Finn", "Eli", "Theo"]


def valid_combo(setting_id: str, item_id: str, culprit_id: str) -> bool:
    if setting_id not in SETTINGS or item_id not in ITEMS or culprit_id not in CULPRITS:
        return False
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    culprit = CULPRITS[culprit_id]
    if culprit.id not in setting.supports:
        return False
    if culprit.id == "wind":
        return setting.has_window and item.light
    if culprit.id == "puppy":
        return setting.has_puppy and item.size == "small"
    if culprit.id == "sibling":
        return setting.has_sibling_nook and item.size == "small"
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for item_id in ITEMS:
            for culprit_id in CULPRITS:
                if valid_combo(setting_id, item_id, culprit_id):
                    combos.append((setting_id, item_id, culprit_id))
    return combos


def hiding_place(setting: Setting, culprit: Culprit) -> str:
    if culprit.id == "puppy":
        return setting.puppy_spot
    if culprit.id == "sibling":
        return setting.sibling_spot
    if culprit.id == "wind":
        return setting.window_spot
    return "near the wall"


def soundscape_sentence(culprit: Culprit) -> str:
    parts = [
        'The drip pail near the door said "ropbl" whenever a fat drop fell in.',
        'A bit of chalk at the board whispered "chy" when it scraped.',
        'Wet shoes by the mat answered with a soft "splish".',
    ]
    if culprit.sound == "ropbl":
        parts.append("It was the sort of room where one tiny sound could turn out to matter.")
    elif culprit.sound == "chy":
        parts.append("That little chalky noise would matter more than anyone guessed.")
    else:
        parts.append("The wet little sound would matter more than anyone guessed.")
    return " ".join(parts)


def introduce(world: World, sleuth: Entity, friend: Entity, item: Entity, item_cfg: MissingItem) -> None:
    world.say(
        f"{sleuth.id} and {friend.id} had turned {world.setting.place} into a tiny detective office. "
        f"They were proud of {item_cfg.game_use}."
    )
    world.say(
        f"On the table between them rested {item_cfg.phrase}, and both children kept glancing at it as if the game could not begin without it."
    )


def foreshadow(world: World, culprit_cfg: Culprit) -> None:
    world.say(soundscape_sentence(culprit_cfg))


def vanish(world: World, item: Entity) -> None:
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        "Then they looked back at the table, and the important thing was gone."
    )
    world.say(
        f'"The {item.label}!" both children gasped at once.'
    )


def accuse(world: World, sleuth: Entity, friend: Entity) -> None:
    sleuth.memes["accused"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Did you take it?" {sleuth.id} blurted.'
    )
    world.say(
        f'{friend.id} drew back. "No! I thought you took it." The room suddenly felt much smaller than before.'
    )


def calm_adult(world: World, adult: Entity, sleuth: Entity, friend: Entity) -> None:
    world.say(
        f"{adult.label_word.capitalize()} came over, looked at both worried faces, and knelt beside the table."
    )
    world.say(
        f'"A good detective does not start with blame," {adult.pronoun()} said. "A good detective starts with clues."'
    )
    sleuth.memes["thinking"] += 1
    friend.memes["thinking"] += 1


def inspect_clue(world: World, sleuth: Entity, friend: Entity, culprit_cfg: Culprit, item_cfg: MissingItem) -> None:
    world.facts["lead_sound"] = culprit_cfg.sound
    world.facts["lead_clue"] = culprit_cfg.clue
    if culprit_cfg.id == "puppy":
        world.say(
            f"{friend.id} looked down first. 'Wait,' {friend.pronoun()} whispered. "
            f'Tiny {culprit_cfg.clue} curved away from the table, each one making a memory of that earlier "splish".'
        )
    elif culprit_cfg.id == "sibling":
        world.say(
            f"{sleuth.id} noticed a pale line near the rug. There was {culprit_cfg.clue}, and the scratchy little board sound -- 'chy' -- no longer seemed silly at all."
        )
    else:
        world.say(
            f"They both turned toward the pail. Another drop fell in with a round little 'ropbl', and beside it they saw {culprit_cfg.clue}. The sound from before had been warning them all along."
        )
    world.say(
        f"Now the mystery felt less like a fight and more like a trail."
    )
    world.facts["saw_clue"] = True


def reveal(world: World, sleuth: Entity, friend: Entity, culprit_ent: Entity, item: Entity,
           culprit_cfg: Culprit, setting: Setting) -> None:
    place = hiding_place(setting, culprit_cfg)
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    culprit_ent.meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they followed the clue trail to {place}."
    )
    if culprit_cfg.id == "wind":
        world.say(
            f"There lay the {item.label}, caught where the air had pushed it."
        )
    else:
        world.say(
            f"There was {culprit_cfg.label}, with the {item.label} right beside {culprit_ent.pronoun('object')}."
        )
    world.say(culprit_cfg.reason)
    world.facts["found_place"] = place


def mend_conflict(world: World, adult: Entity, sleuth: Entity, friend: Entity, culprit_cfg: Culprit) -> None:
    sleuth.memes["sorry"] += 1
    friend.memes["forgiven"] += 1
    world.say(
        f'{sleuth.id} looked at {friend.id} and spoke in a small voice. "I am sorry I blamed you before we looked."'
    )
    world.say(
        f'{friend.id} nodded and stepped close again. "{adult.label_word.capitalize()} was right," {friend.pronoun()} said. "Clues first."'
    )
    world.say(culprit_cfg.apology_fix)


def ending(world: World, sleuth: Entity, friend: Entity, item_cfg: MissingItem) -> None:
    world.say(
        f"Soon the mystery game began for real. This time {sleuth.id} and {friend.id} shared the clues, took turns speaking, and kept checking the room with careful detective eyes."
    )
    world.say(
        f"The {item_cfg.label} gleamed safely in its place, and the case of the missing thing became the first mystery they had solved together."
    )


def tell(
    setting: Setting,
    item_cfg: MissingItem,
    culprit_cfg: Culprit,
    sleuth_name: str,
    sleuth_gender: str,
    friend_name: str,
    friend_gender: str,
    adult_type: str,
) -> World:
    world = World(setting)
    sleuth = world.add(Entity(id="sleuth", kind="character", type=sleuth_gender, role="sleuth", label=sleuth_name))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, role="friend", label=friend_name))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, role="adult", label="the adult"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    item = world.add(Entity(id="item", kind="thing", type="object", label=item_cfg.label))
    culprit_ent = world.add(Entity(id="culprit", kind="thing", type=culprit_cfg.type, label=culprit_cfg.label))

    world.facts.update(
        sleuth=sleuth,
        friend=friend,
        adult=adult,
        room=room,
        item=item,
        item_cfg=item_cfg,
        culprit=culprit_ent,
        culprit_cfg=culprit_cfg,
        setting=setting,
        saw_clue=False,
        lead_sound="",
        lead_clue="",
        found_place="",
    )

    sleuth.attrs["name"] = sleuth_name
    friend.attrs["name"] = friend_name

    introduce(world, sleuth, friend, item, item_cfg)
    foreshadow(world, culprit_cfg)

    world.para()
    vanish(world, item)
    accuse(world, sleuth, friend)
    calm_adult(world, adult, sleuth, friend)

    world.para()
    inspect_clue(world, sleuth, friend, culprit_cfg, item_cfg)
    reveal(world, sleuth, friend, culprit_ent, item, culprit_cfg, setting)
    mend_conflict(world, adult, sleuth, friend, culprit_cfg)

    world.para()
    ending(world, sleuth, friend, item_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item_cfg = f["item_cfg"]
    setting = f["setting"]
    culprit_cfg = f["culprit_cfg"]
    sleuth = f["sleuth"]
    friend = f["friend"]
    return [
        f'Write a short child-friendly whodunit set in {setting.place} that includes the words "ropbl", "chy", and "splish".',
        f"Tell a mystery story where {sleuth.label} and {friend.label} begin by blaming each other when a {item_cfg.label} vanishes, but a clue tied to {culprit_cfg.sound} solves the case.",
        "Write a simple story with conflict and foreshadowing where the children learn to follow clues before making accusations.",
    ]


KNOWLEDGE = {
    "mystery": [
        ("What does a detective do?",
         "A detective looks for clues and asks careful questions to solve a puzzle. Good detectives notice small things before they decide what happened.")
    ],
    "puppy": [
        ("Why might a puppy carry something away?",
         "Puppies carry things because they are curious and like to chew or make little nests. They do not mean to spoil a game; they are just exploring.")
    ],
    "wind": [
        ("How can wind move light things?",
         "Wind is moving air, and when something is light, a gust can push or lift it. That is why papers and ribbons can slide or flutter away.")
    ],
    "chalk": [
        ("Why does chalk make a scratchy sound?",
         "Chalk is dry and dusty, so when it rubs on a board it can squeak or scrape. That sound can help you notice that someone was drawing there.")
    ],
    "wet": [
        ("Why do wet footprints make clues?",
         "Wet feet or paws leave darker marks on the floor for a little while. Those marks can show where someone walked.")
    ],
    "apology": [
        ("Why is it good to apologize after blaming someone unfairly?",
         "An apology helps mend hurt feelings and shows you want to do better. It tells the other person that you care about the truth and about them.")
    ],
}
KNOWLEDGE_ORDER = ["mystery", "puppy", "wind", "chalk", "wet", "apology"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleuth = f["sleuth"]
    friend = f["friend"]
    adult = f["adult"]
    item_cfg = f["item_cfg"]
    culprit_cfg = f["culprit_cfg"]
    setting = f["setting"]
    place = f["found_place"]
    qa = [
        (
            "Who was the story about?",
            f"It was about {sleuth.label} and {friend.label}, two children playing detective in {setting.place}. Their mystery began when the {item_cfg.label} disappeared."
        ),
        (
            f"Why did the missing {item_cfg.label} matter?",
            f"It mattered because it was {item_cfg.game_use}. Without it, their mystery game could not begin the way they had planned."
        ),
        (
            "What caused the conflict?",
            f"The conflict started when the important thing went missing and {sleuth.label} blurted out a blame question. That hurt {friend.label}'s feelings and made the room feel tense before they had any real proof."
        ),
        (
            f"How did they solve the mystery?",
            f"They stopped blaming and looked for a real clue instead. The clue tied to {culprit_cfg.sound} led them to {place}, where they found the missing {item_cfg.label}."
        ),
        (
            "What changed at the end?",
            f"They learned to act more like real detectives by looking for clues before accusing anyone. After the apology, they could play together again with calmer hearts."
        ),
    ]
    if culprit_cfg.id == "puppy":
        qa.append((
            "Who really took the missing thing, and why?",
            f"It was {culprit_cfg.label}. {culprit_cfg.reason}"
        ))
    elif culprit_cfg.id == "sibling":
        qa.append((
            "Who really had the missing thing, and why?",
            f"It was {culprit_cfg.label}. {culprit_cfg.reason}"
        ))
    else:
        qa.append((
            "Was there really a villain?",
            f"No one was being mean on purpose. {culprit_cfg.reason}"
        ))
    qa.append((
        f"What did {adult.label_word} teach them?",
        f"{adult.label_word.capitalize()} taught them that a good detective begins with clues, not blame. That advice helped turn their fight into a solved mystery."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mystery", "apology"}
    culprit_cfg = world.facts["culprit_cfg"]
    if culprit_cfg.id == "puppy":
        tags |= {"puppy", "wet"}
    elif culprit_cfg.id == "sibling":
        tags |= {"chalk"}
    else:
        tags |= {"wind"}
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="clubhouse",
        item="ribbon",
        culprit="puppy",
        sleuth="Lily",
        sleuth_gender="girl",
        friend="Tom",
        friend_gender="boy",
        adult="mother",
    ),
    StoryParams(
        setting="classroom",
        item="bell",
        culprit="sibling",
        sleuth="Max",
        sleuth_gender="boy",
        friend="Mia",
        friend_gender="girl",
        adult="father",
    ),
    StoryParams(
        setting="clubhouse",
        item="map",
        culprit="wind",
        sleuth="Nora",
        sleuth_gender="girl",
        friend="Finn",
        friend_gender="boy",
        adult="mother",
    ),
    StoryParams(
        setting="porch",
        item="ribbon",
        culprit="wind",
        sleuth="Sam",
        sleuth_gender="boy",
        friend="Ella",
        friend_gender="girl",
        adult="father",
    ),
]


def explain_rejection(setting_id: str, item_id: str, culprit_id: str) -> str:
    if setting_id not in SETTINGS:
        return f"(No story: unknown setting '{setting_id}'.)"
    if item_id not in ITEMS:
        return f"(No story: unknown item '{item_id}'.)"
    if culprit_id not in CULPRITS:
        return f"(No story: unknown culprit '{culprit_id}'.)"
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    culprit = CULPRITS[culprit_id]
    if culprit.id not in setting.supports:
        return (f"(No story: {setting.place} does not reasonably support culprit "
                f"'{culprit.id}' in this world.)")
    if culprit.id == "wind" and not item.light:
        return (f"(No story: wind can whisk light things like paper or ribbon, but "
                f"the {item.label} is not light enough for this mystery.)")
    if culprit.id == "wind" and not setting.has_window:
        return (f"(No story: a wind mystery needs an open window or airy gap, and "
                f"{setting.place} does not have that here.)")
    if culprit.id == "puppy" and not setting.has_puppy:
        return f"(No story: there is no puppy in {setting.place}.)"
    if culprit.id == "sibling" and not setting.has_sibling_nook:
        return f"(No story: there is no nearby sibling nook in {setting.place}.)"
    return "(No story: that combination is not reasonable in this world.)"


ASP_RULES = r"""
valid(S,I,C) :- setting(S), item(I), culprit(C), supports(S,C), reasonable(C,I,S).

reasonable(puppy,I,S) :- puppy_room(S), item_size(I,small).
reasonable(sibling,I,S) :- sibling_room(S), item_size(I,small).
reasonable(wind,I,S) :- windy_room(S), light_item(I).

lead_sound(puppy,splish).
lead_sound(sibling,chy).
lead_sound(wind,ropbl).

hide_spot(S,puppy,P) :- puppy_place(S,P).
hide_spot(S,sibling,P) :- sibling_place(S,P).
hide_spot(S,wind,P) :- window_place(S,P).

#show valid/3.
#show lead_sound/2.
#show hide_spot/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for culprit in sorted(setting.supports):
            lines.append(asp.fact("supports", setting_id, culprit))
        if setting.has_puppy:
            lines.append(asp.fact("puppy_room", setting_id))
            if setting.puppy_spot:
                lines.append(asp.fact("puppy_place", setting_id, setting.puppy_spot))
        if setting.has_sibling_nook:
            lines.append(asp.fact("sibling_room", setting_id))
            if setting.sibling_spot:
                lines.append(asp.fact("sibling_place", setting_id, setting.sibling_spot))
        if setting.has_window:
            lines.append(asp.fact("windy_room", setting_id))
            if setting.window_spot:
                lines.append(asp.fact("window_place", setting_id, setting.window_spot))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_size", item_id, item.size))
        if item.light:
            lines.append(asp.fact("light_item", item_id))
    for culprit_id in CULPRITS:
        lines.append(asp.fact("culprit", culprit_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sound_for(culprit_id: str) -> str:
    import asp
    model = asp.one_model(asp_program())
    atoms = asp.atoms(model, "lead_sound")
    for culprit, sound in atoms:
        if culprit == culprit_id:
            return sound
    return ""


def asp_hide_spot(setting_id: str, culprit_id: str) -> str:
    import asp
    model = asp.one_model(asp_program())
    atoms = asp.atoms(model, "hide_spot")
    for setting, culprit, place in atoms:
        if setting == setting_id and culprit == culprit_id:
            return place
    return ""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child-friendly whodunit with conflict and foreshadowing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--sleuth")
    ap.add_argument("--friend")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.culprit:
        if not valid_combo(args.setting, args.item, args.culprit):
            raise StoryError(explain_rejection(args.setting, args.item, args.culprit))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, culprit_id = rng.choice(sorted(combos))
    sleuth_name, sleuth_gender = _pick_name(rng)
    if args.sleuth:
        sleuth_name = args.sleuth
    friend_name, friend_gender = _pick_name(rng, avoid=sleuth_name)
    if args.friend:
        friend_name = args.friend
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting_id,
        item=item_id,
        culprit=culprit_id,
        sleuth=sleuth_name,
        sleuth_gender=sleuth_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.setting, params.item, params.culprit):
        raise StoryError(explain_rejection(params.setting, params.item, params.culprit))
    if params.setting not in SETTINGS or params.item not in ITEMS or params.culprit not in CULPRITS:
        raise StoryError("(No story: one or more parameters are unknown.)")

    world = tell(
        setting=SETTINGS[params.setting],
        item_cfg=ITEMS[params.item],
        culprit_cfg=CULPRITS[params.culprit],
        sleuth_name=params.sleuth,
        sleuth_gender=params.sleuth_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        adult_type=params.adult,
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
        print(f"OK: ASP valid combos match Python ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for culprit_id, culprit in CULPRITS.items():
        if asp_sound_for(culprit_id) != culprit.sound:
            rc = 1
            print(f"MISMATCH in lead sound for {culprit_id}.")
    if rc == 0:
        print("OK: lead sounds match.")

    for setting_id, setting in SETTINGS.items():
        for culprit_id, culprit in CULPRITS.items():
            if not valid_combo(setting_id, "ribbon" if culprit_id != "wind" else "map", culprit_id):
                continue
            py_place = hiding_place(setting, culprit)
            cl_place = asp_hide_spot(setting_id, culprit_id)
            if py_place != cl_place:
                rc = 1
                print(f"MISMATCH in hiding place for {setting_id}/{culprit_id}: {py_place!r} != {cl_place!r}")
    if rc == 0:
        print("OK: hiding places match.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="")
        print("\nOK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, culprit) combos:\n")
        for setting_id, item_id, culprit_id in combos:
            print(f"  {setting_id:10} {item_id:8} {culprit_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            header = f"### {p.setting}: {p.item} / {p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
