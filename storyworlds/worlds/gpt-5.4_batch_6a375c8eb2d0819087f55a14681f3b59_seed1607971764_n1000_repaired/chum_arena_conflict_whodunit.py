#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chum_arena_conflict_whodunit.py
==========================================================

A standalone story world for a small child-facing whodunit: at a marine learning
arena, a bucket of chum is spilled before a feeding talk, one child is blamed,
and another child follows grounded clues to discover what really happened.

The domain is deliberately narrow and reasoned:

- The mystery always centers on a tipped chum bucket in an arena.
- A false clue belonging to the accused child starts a conflict.
- The real culprit must be physically compatible with the chosen arena.
- The chosen investigation method must be the kind that could honestly reveal
  the culprit's clue pattern.
- The ending always resolves the conflict and proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/chum_arena_conflict_whodunit.py
    python storyworlds/worlds/gpt-5.4/chum_arena_conflict_whodunit.py --arena dockside --culprit gull
    python storyworlds/worlds/gpt-5.4/chum_arena_conflict_whodunit.py --investigation look_up
    python storyworlds/worlds/gpt-5.4/chum_arena_conflict_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/chum_arena_conflict_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/chum_arena_conflict_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
DIRECT_TRAITS = {"careful", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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


@dataclass
class Arena:
    id: str
    label: str
    intro: str
    rail: str
    floor: str
    finish: str
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
class Culprit:
    id: str
    label: str
    kind: str
    clue: str
    reveal: str
    motive: str
    motion: str
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
class Herring:
    id: str
    label: str
    phrase: str
    found: str
    accuse_line: str
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
class Investigation:
    id: str
    label: str
    verb: str
    pattern: str
    discovery: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []

    bucket = world.get("bucket")
    floor = world.get("floor")
    detective = world.get("detective")
    accused = world.get("accused")
    accuser = world.get("accuser")
    caretaker = world.get("caretaker")

    if bucket.meters["spilled"] >= THRESHOLD and ("spill",) not in world.fired:
        world.fired.add(("spill",))
        floor.meters["slippery"] += 1
        floor.meters["smelly"] += 1
        accused.memes["worry"] += 1
        detective.memes["alarm"] += 1
        produced.append("__spill__")

    if accuser.memes["blame"] >= THRESHOLD and ("blame",) not in world.fired:
        world.fired.add(("blame",))
        accused.memes["sadness"] += 1
        accused.memes["hurt"] += 1
        detective.memes["doubt"] += 1
        caretaker.memes["concern"] += 1
        world.facts["friendship_strain"] = True
        produced.append("__conflict__")

    if detective.memes["certainty"] >= THRESHOLD and ("solve",) not in world.fired:
        world.fired.add(("solve",))
        accused.memes["relief"] += 1
        accused.memes["hurt"] = 0.0
        accuser.memes["guilt"] += 1
        detective.memes["pride"] += 1
        produced.append("__solved__")

    if accuser.memes["apology"] >= THRESHOLD and ("apology",) not in world.fired:
        world.fired.add(("apology",))
        detective.memes["peace"] += 1
        accused.memes["forgiveness"] += 1
        world.facts["friendship_repaired"] = True
        produced.append("__repaired__")

    if narrator := (narrate and False):
        _ = narrator
    return produced


ARENAS = {
    "dockside": Arena(
        id="dockside",
        label="the dockside arena",
        intro="a little learning arena built beside the rescue pool",
        rail="the wooden rail above the water",
        floor="the planks by the chum bucket",
        finish="The gulls stayed up on the posts, and the children stood shoulder to shoulder by the rail, much wiser now.",
        tags={"arena", "dock"},
    ),
    "splash": Arena(
        id="splash",
        label="the splash arena",
        intro="a round blue arena with a low wall and a shining pool in the middle",
        rail="the painted rim above the pool",
        floor="the wet path circling the pool",
        finish="The pool shone blue again, and the children waved together as the lesson began at last.",
        tags={"arena", "pool"},
    ),
    "sand": Arena(
        id="sand",
        label="the sand arena",
        intro="a warm sand arena beside the rescue tanks",
        rail="the rope rail around the ring",
        floor="the packed sand beside the chum pail",
        finish="The sand lay smooth again, and the two friends knelt side by side, ready to help in the safe feeding lesson.",
        tags={"arena", "sand"},
    ),
}

CULPRITS = {
    "gull": Culprit(
        id="gull",
        label="a hungry gull",
        kind="overhead",
        clue="a silver-gray feather caught on the rail",
        reveal="The clue was high, not low, and it pointed straight up to the rail where a gull had landed.",
        motive="It swooped down because the chum smelled fishy and strong.",
        motion="swooped from above and pecked at the chum lid",
        tags={"gull", "feather"},
    ),
    "seal_pup": Culprit(
        id="seal_pup",
        label="the curious seal pup",
        kind="tracks",
        clue="a line of wet flipper prints leading away from the bucket",
        reveal="The clue was a trail to follow, and it went from the bucket to the pup pool.",
        motive="It popped up because it knew chum meant feeding time.",
        motion="nudged the pail with its nose and flopped away",
        tags={"seal", "flipper"},
    ),
    "otter": Culprit(
        id="otter",
        label="the little otter",
        kind="tracks",
        clue="small wet pawprints and a shiny shell beside the bucket",
        reveal="The clue was a trail to follow, and it went to the otter's corner where a little shell lay glinting.",
        motive="It scampered over because the chum smelled interesting and because otters poke into everything.",
        motion="bumped the pail while reaching for a shiny shell",
        tags={"otter", "pawprint"},
    ),
}

HERRINGS = {
    "red_scarf": Herring(
        id="red_scarf",
        label="red scarf",
        phrase="a bright red scarf",
        found="the bright red scarf lying right beside the bucket",
        accuse_line='"Look! Your scarf is right there. You must have done it!"',
        tags={"scarf"},
    ),
    "yellow_boot": Herring(
        id="yellow_boot",
        label="yellow boot",
        phrase="a little yellow boot",
        found="one little yellow boot tipped on its side near the spill",
        accuse_line='"Your boot was by the bucket. I think you knocked it over!"',
        tags={"boot"},
    ),
    "blue_scoop": Herring(
        id="blue_scoop",
        label="blue scoop",
        phrase="a blue scoop",
        found="the blue scoop the accused child had been carrying that morning",
        accuse_line='"That is your scoop. You were closest, so it must have been you!"',
        tags={"scoop"},
    ),
}

INVESTIGATIONS = {
    "look_up": Investigation(
        id="look_up",
        label="look up high",
        verb="looked up instead of only down",
        pattern="overhead",
        discovery="A clue from above would never be found by staring at the floor.",
        tags={"look_up"},
    ),
    "follow_tracks": Investigation(
        id="follow_tracks",
        label="follow wet tracks",
        verb="followed the wet trail carefully",
        pattern="tracks",
        discovery="Wet tracks tell a story when someone patient follows where they go.",
        tags={"tracks"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ava", "Ivy", "Zoe", "Ella", "Ruby"]
BOY_NAMES = ["Finn", "Leo", "Max", "Owen", "Sam", "Toby", "Eli", "Jack"]
TRAITS = ["careful", "patient", "brave", "quick", "curious"]


def culprit_fits(arena: Arena, culprit: Culprit) -> bool:
    if culprit.id == "gull":
        return arena.id in {"dockside", "splash", "sand"}
    if culprit.id == "seal_pup":
        return arena.id in {"dockside", "splash"}
    if culprit.id == "otter":
        return arena.id in {"dockside", "sand"}
    return False


def investigation_fits(culprit: Culprit, investigation: Investigation) -> bool:
    return culprit.kind == investigation.pattern


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for arena_id, arena in ARENAS.items():
        for culprit_id, culprit in CULPRITS.items():
            if not culprit_fits(arena, culprit):
                continue
            for herring_id in HERRINGS:
                for inv_id, inv in INVESTIGATIONS.items():
                    if investigation_fits(culprit, inv):
                        combos.append((arena_id, culprit_id, herring_id, inv_id))
    return combos


def solve_style_of(params: "StoryParams") -> str:
    return "direct" if params.detective_trait in DIRECT_TRAITS else "helped"


@dataclass
class StoryParams:
    arena: str
    culprit: str
    herring: str
    investigation: str
    detective: str
    detective_gender: str
    accused: str
    accused_gender: str
    caretaker: str
    detective_trait: str
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


def introduce(world: World, arena: Arena, detective: Entity, accused: Entity, caretaker: Entity) -> None:
    world.say(
        f"On bright harbor morning, {detective.id} and {accused.id} hurried into {arena.label}, {arena.intro}."
    )
    world.say(
        f"They were helping {detective.id}'s {caretaker.label_word} get ready for the rescue talk, and the chum pail waited by {arena.floor}."
    )
    world.say(
        f"{detective.id} loved careful little mysteries, while {accused.id} was the child who always wanted to be first to help."
    )


def setup_bucket(world: World, herring: Herring, accused: Entity) -> None:
    world.say(
        f"{accused.id} had set down {herring.phrase} for one minute while carrying towels, and then the two children ran to straighten the picture signs."
    )


def spill(world: World, culprit: Culprit) -> None:
    bucket = world.get("bucket")
    bucket.meters["spilled"] += 1
    bucket.meters["full"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"A clatter broke the quiet. When they turned around, the chum pail was on its side, and a sharp fishy smell was spreading across the ground."
    )
    world.say(
        f"Whatever had done it had moved fast."
    )
    world.facts["culprit_motion"] = culprit.motion


def accusation(world: World, herring: Herring, detective: Entity, accused: Entity) -> None:
    accuser = world.get("accuser")
    accuser.memes["blame"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {detective.id} saw {herring.found}. {detective.id}'s eyes widened."
    )
    world.say(
        f'{herring.accuse_line} {detective.id} burst out.'
    )
    world.say(
        f"{accused.id}'s face fell. \"I didn't,\" {accused.pronoun()} whispered. \"I was carrying towels.\""
    )


def investigate_direct(
    world: World,
    arena: Arena,
    culprit: Culprit,
    investigation: Investigation,
    detective: Entity,
    caretaker: Entity,
) -> None:
    detective.memes["certainty"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But after one hot second, {detective.id} remembered that a real detective must look twice. {detective.pronoun().capitalize()} {investigation.verb}."
    )
    world.say(
        f"{investigation.discovery} There, {detective.pronoun()} found {culprit.clue}."
    )
    world.say(
        f"{culprit.reveal} \"Wait,\" {detective.id} said. \"{accused.id} didn't do it. {culprit.label.capitalize()} {culprit.motion}.\""
    )
    world.facts["solver"] = detective.id
    world.facts["helped_by_caretaker"] = False


def investigate_helped(
    world: World,
    arena: Arena,
    culprit: Culprit,
    investigation: Investigation,
    detective: Entity,
    caretaker: Entity,
) -> None:
    detective.memes["certainty"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} crouched down and tried to be brave, but the mystery felt bigger than one quick guess. {detective.pronoun().capitalize()} {investigation.verb} and frowned."
    )
    world.say(
        f'"Tell me what you notice, not what you fear," {caretaker.label_word} said softly.'
    )
    world.say(
        f"That helped. {investigation.discovery} Together they found {culprit.clue}."
    )
    world.say(
        f"\"So that is it,\" said {detective.id}. \"{culprit.label.capitalize()} {culprit.motion}. {accused.id} was only blamed because {HERRINGS[world.facts['herring'].id].label} was nearby.\""
    )
    world.facts["solver"] = f"{detective.id} and {caretaker.label_word}"
    world.facts["helped_by_caretaker"] = True


def reveal_and_repair(world: World, culprit: Culprit, detective: Entity, accused: Entity, caretaker: Entity) -> None:
    accuser = world.get("accuser")
    accuser.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{accused.id} looked where the clue pointed, and this time everyone could see it. {culprit.motive}"
    )
    world.say(
        f"Slowly, {detective.id}'s shoulders sank. \"I am sorry I blamed you first,\" {detective.pronoun()} said."
    )
    world.say(
        f"\"Thank you for saying that,\" said {accused.id}. {caretaker.label_word.capitalize()} nodded, glad the truth had come before the feeling turned into a bigger fight."
    )


def resolve(world: World, arena: Arena, culprit: Culprit, detective: Entity, accused: Entity, caretaker: Entity) -> None:
    bucket = world.get("bucket")
    bucket.meters["full"] += 1
    bucket.meters["spilled"] = 0.0
    world.get("floor").meters["slippery"] = 0.0
    world.say(
        f"Then they worked together. {caretaker.label_word.capitalize()} brought a clean pail, {accused.id} held the long spoon, and {detective.id} wiped the floor where the chum had splashed."
    )
    world.say(
        f"Soon the lesson could begin after all. Nobody was in trouble. The only thing that needed fixing had been the rushed accusation."
    )
    world.say(arena.finish)
    world.facts["resolved"] = True


def tell(
    arena: Arena,
    culprit: Culprit,
    herring: Herring,
    investigation: Investigation,
    detective_name: str,
    detective_gender: str,
    accused_name: str,
    accused_gender: str,
    caretaker_type: str,
    detective_trait: str,
) -> World:
    world = World()
    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            label=detective_name,
            role="detective",
            traits=[detective_trait],
        )
    )
    accused = world.add(
        Entity(
            id=accused_name,
            kind="character",
            type=accused_gender,
            label=accused_name,
            role="accused",
            traits=["helpful"],
        )
    )
    caretaker = world.add(
        Entity(
            id="Caretaker",
            kind="character",
            type=caretaker_type,
            label="the caretaker",
            role="caretaker",
        )
    )
    world.add(
        Entity(
            id="bucket",
            type="bucket",
            label="chum pail",
            attrs={"contents": "chum"},
        )
    )
    world.add(
        Entity(
            id="floor",
            type="ground",
            label=arena.floor,
        )
    )
    world.add(
        Entity(
            id="accuser",
            kind="character",
            type=detective_gender,
            label=detective_name,
            role="accuser",
        )
    )

    world.facts["arena"] = arena
    world.facts["culprit"] = culprit
    world.facts["herring"] = herring
    world.facts["investigation"] = investigation
    world.facts["detective"] = detective
    world.facts["accused"] = accused
    world.facts["caretaker"] = caretaker
    world.facts["solve_style"] = solve_style_of(
        StoryParams(
            arena=arena.id,
            culprit=culprit.id,
            herring=herring.id,
            investigation=investigation.id,
            detective=detective_name,
            detective_gender=detective_gender,
            accused=accused_name,
            accused_gender=accused_gender,
            caretaker=caretaker_type,
            detective_trait=detective_trait,
            seed=None,
        )
    )
    world.facts["friendship_strain"] = False
    world.facts["friendship_repaired"] = False
    world.facts["resolved"] = False

    introduce(world, arena, detective, accused, caretaker)
    setup_bucket(world, herring, accused)

    world.para()
    spill(world, culprit)
    accusation(world, herring, detective, accused)

    world.para()
    if world.facts["solve_style"] == "direct":
        investigate_direct(world, arena, culprit, investigation, detective, caretaker)
    else:
        investigate_helped(world, arena, culprit, investigation, detective, caretaker)
    reveal_and_repair(world, culprit, detective, accused, caretaker)

    world.para()
    resolve(world, arena, culprit, detective, accused, caretaker)
    return world


KNOWLEDGE = {
    "chum": [
        (
            "What is chum?",
            "Chum is cut-up fish used to make a strong smell in the water so sea animals notice feeding time. Grown-ups handle it because it is messy and slippery."
        )
    ],
    "arena": [
        (
            "What is an arena?",
            "An arena is a special space where people gather to watch or learn something together. It can be round or ringed so everyone can see."
        )
    ],
    "gull": [
        (
            "Why might a gull come near fish food?",
            "A gull has a sharp nose and likes easy food. If it smells fish, it may swoop down to peck at it."
        )
    ],
    "seal": [
        (
            "What kind of marks can a seal pup leave?",
            "A seal pup can leave wet flipper prints when it slides or flops across the ground. Those prints can show where it went."
        )
    ],
    "otter": [
        (
            "What kind of clue can an otter leave behind?",
            "An otter can leave tiny wet pawprints, and sometimes it drops little things it was carrying. Those small signs can help someone solve a mystery."
        )
    ],
    "apology": [
        (
            "Why is it important to say sorry after blaming someone unfairly?",
            "Saying sorry helps heal hurt feelings and shows you care about the truth. It turns a fight into a chance to do better."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure out what happened. A good detective notices clues before making a guess."
        )
    ],
}
KNOWLEDGE_ORDER = ["chum", "arena", "clue", "gull", "seal", "otter", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    accused = f["accused"]
    arena = f["arena"]
    culprit = f["culprit"]
    return [
        f'Write a short whodunit story for a 3-to-5-year-old that includes the words "chum" and "arena".',
        f"Tell a gentle mystery where {detective.id} wrongly blames {accused.id} after a chum spill in {arena.label}, then follows clues to learn that {culprit.label} really did it.",
        f"Write a child-facing conflict story in whodunit style where a rushed accusation hurts a friend's feelings, but the truth and an apology repair the friendship.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    accused = f["accused"]
    arena = f["arena"]
    culprit = f["culprit"]
    herring = f["herring"]
    investigation = f["investigation"]
    caretaker = f["caretaker"]
    style = f["solve_style"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id} and {accused.id} in {arena.label}, with {detective.id}'s {caretaker.label_word} getting ready for a feeding lesson. The mystery begins when the chum pail tips over before the lesson can start."
        ),
        (
            "Why did the friends start arguing?",
            f"They started arguing because {detective.id} saw {herring.label} near the spill and guessed too fast that {accused.id} had knocked the pail over. That guess hurt {accused.id}'s feelings because {accused.pronoun()} had not done it."
        ),
        (
            f"How did {detective.id} figure out what really happened?",
            f"{detective.id} used the idea to {investigation.label} and found {culprit.clue}. That clue matched {culprit.label}, so the children could tell what had really happened instead of blaming the wrong person."
        ),
    ]
    if style == "helped":
        qa.append(
            (
                f"Did {detective.id} solve the mystery alone?",
                f"Not quite. {detective.id} began the search, but {caretaker.label_word} helped by saying to notice facts instead of fear. That calm advice helped the real clue stand out."
            )
        )
    else:
        qa.append(
            (
                f"What changed after {detective.id} looked again?",
                f"At first {detective.id} only noticed the false clue and blamed {accused.id}. After looking again, {detective.pronoun()} found the real clue and understood that {culprit.label} had spilled the chum."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with an apology, a clean floor, and the lesson starting at last. The ending proves the conflict changed because the children worked side by side again instead of arguing."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"chum", "arena", "clue", "apology"}
    culprit = world.facts["culprit"]
    if culprit.id == "gull":
        tags.add("gull")
    elif culprit.id == "seal_pup":
        tags.add("seal")
    elif culprit.id == "otter":
        tags.add("otter")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(
        f"  facts: solve_style={world.facts.get('solve_style')} repaired={world.facts.get('friendship_repaired')} resolved={world.facts.get('resolved')}"
    )
    return "\n".join(lines)


CURATED = [
    StoryParams(
        arena="dockside",
        culprit="gull",
        herring="red_scarf",
        investigation="look_up",
        detective="Lina",
        detective_gender="girl",
        accused="Finn",
        accused_gender="boy",
        caretaker="mother",
        detective_trait="careful",
        seed=101,
    ),
    StoryParams(
        arena="splash",
        culprit="seal_pup",
        herring="yellow_boot",
        investigation="follow_tracks",
        detective="Max",
        detective_gender="boy",
        accused="Ava",
        accused_gender="girl",
        caretaker="father",
        detective_trait="quick",
        seed=102,
    ),
    StoryParams(
        arena="sand",
        culprit="otter",
        herring="blue_scoop",
        investigation="follow_tracks",
        detective="Nora",
        detective_gender="girl",
        accused="Leo",
        accused_gender="boy",
        caretaker="mother",
        detective_trait="patient",
        seed=103,
    ),
    StoryParams(
        arena="dockside",
        culprit="seal_pup",
        herring="blue_scoop",
        investigation="follow_tracks",
        detective="Owen",
        detective_gender="boy",
        accused="Ruby",
        accused_gender="girl",
        caretaker="father",
        detective_trait="brave",
        seed=104,
    ),
]


def explain_rejection(arena_id: str, culprit_id: str, investigation_id: str) -> str:
    arena = ARENAS[arena_id]
    culprit = CULPRITS[culprit_id]
    inv = INVESTIGATIONS[investigation_id]
    if not culprit_fits(arena, culprit):
        return (
            f"(No story: {culprit.label} is not a reasonable culprit in {arena.label}. "
            f"Pick a culprit that could really reach the chum there.)"
        )
    if not investigation_fits(culprit, inv):
        return (
            f"(No story: '{inv.label}' would not honestly reveal clues from {culprit.label}. "
            f"Use an investigation that matches the culprit's clue pattern.)"
        )
    return "(No story: this combination does not make a grounded mystery.)"


ASP_RULES = r"""
fits(A, C) :- arena(A), culprit(C), overhead(C), open_air(A).
fits(A, seal_pup) :- arena(A), water_edge(A).
fits(A, otter) :- arena(A), otter_path(A).

works_for(C, I) :- clue_kind(C, K), method(I, K).

valid(A, C, H, I) :- arena(A), culprit(C), herring(H), investigation(I),
                     fits(A, C), works_for(C, I).

direct(T) :- trait(T), direct_trait(T).
helped(T) :- trait(T), not direct_trait(T).

solve_style(direct) :- chosen_trait(T), direct(T).
solve_style(helped) :- chosen_trait(T), helped(T).

#show valid/4.
#show solve_style/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for arena_id in ARENAS:
        lines.append(asp.fact("arena", arena_id))
    lines.append(asp.fact("open_air", "dockside"))
    lines.append(asp.fact("open_air", "splash"))
    lines.append(asp.fact("open_air", "sand"))
    lines.append(asp.fact("water_edge", "dockside"))
    lines.append(asp.fact("water_edge", "splash"))
    lines.append(asp.fact("otter_path", "dockside"))
    lines.append(asp.fact("otter_path", "sand"))

    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("clue_kind", culprit_id, culprit.kind))
        if culprit.kind == "overhead":
            lines.append(asp.fact("overhead", culprit_id))
    for herring_id in HERRINGS:
        lines.append(asp.fact("herring", herring_id))
    for inv_id, inv in INVESTIGATIONS.items():
        lines.append(asp.fact("investigation", inv_id))
        lines.append(asp.fact("method", inv_id, inv.pattern))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
    for trait in sorted(DIRECT_TRAITS):
        lines.append(asp.fact("direct_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solve_style(trait: str) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("chosen_trait", trait)))
    out = asp.atoms(model, "solve_style")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid mystery combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid mystery combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    style_bad = []
    for trait in TRAITS:
        if asp_solve_style(trait) != ("direct" if trait in DIRECT_TRAITS else "helped"):
            style_bad.append(trait)
    if not style_bad:
        print("OK: solve-style model matches detective traits.")
    else:
        rc = 1
        print("MISMATCH in solve-style traits:", style_bad)

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        if not sample.story_qa or not sample.world_qa:
            raise StoryError("Smoke test generated incomplete QA.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a chum spill in an arena becomes a small whodunit with conflict and apology."
    )
    ap.add_argument("--arena", choices=ARENAS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--herring", choices=HERRINGS)
    ap.add_argument("--investigation", choices=INVESTIGATIONS)
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mystery combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.arena and args.culprit and args.investigation:
        if not culprit_fits(ARENAS[args.arena], CULPRITS[args.culprit]) or not investigation_fits(
            CULPRITS[args.culprit], INVESTIGATIONS[args.investigation]
        ):
            raise StoryError(explain_rejection(args.arena, args.culprit, args.investigation))

    combos = [
        combo
        for combo in valid_combos()
        if (args.arena is None or combo[0] == args.arena)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.herring is None or combo[2] == args.herring)
        and (args.investigation is None or combo[3] == args.investigation)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    arena_id, culprit_id, herring_id, investigation_id = rng.choice(sorted(combos))
    detective_name, detective_gender = _pick_child(rng)
    accused_name, accused_gender = _pick_child(rng, avoid=detective_name)
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        arena=arena_id,
        culprit=culprit_id,
        herring=herring_id,
        investigation=investigation_id,
        detective=detective_name,
        detective_gender=detective_gender,
        accused=accused_name,
        accused_gender=accused_gender,
        caretaker=caretaker,
        detective_trait=trait,
        seed=None,
    )


def _require(mapping: dict, key: str, field_name: str):
    if key not in mapping:
        raise StoryError(f"(No story: unknown {field_name} '{key}'.)")
    return mapping[key]


def generate(params: StoryParams) -> StorySample:
    arena = _require(ARENAS, params.arena, "arena")
    culprit = _require(CULPRITS, params.culprit, "culprit")
    herring = _require(HERRINGS, params.herring, "herring")
    investigation = _require(INVESTIGATIONS, params.investigation, "investigation")
    if not culprit_fits(arena, culprit) or not investigation_fits(culprit, investigation):
        raise StoryError(explain_rejection(params.arena, params.culprit, params.investigation))

    world = tell(
        arena=arena,
        culprit=culprit,
        herring=herring,
        investigation=investigation,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        accused_name=params.accused,
        accused_gender=params.accused_gender,
        caretaker_type=params.caretaker,
        detective_trait=params.detective_trait,
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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (arena, culprit, herring, investigation) combos:\n")
        for arena_id, culprit_id, herring_id, investigation_id in combos:
            print(f"  {arena_id:9} {culprit_id:9} {herring_id:11} {investigation_id}")
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
            header = f"### {p.detective} and {p.accused}: {p.culprit} in {p.arena} ({solve_style_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
