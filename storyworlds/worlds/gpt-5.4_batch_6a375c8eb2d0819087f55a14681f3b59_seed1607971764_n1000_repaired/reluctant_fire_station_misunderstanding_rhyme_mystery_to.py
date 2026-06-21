#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reluctant_fire_station_misunderstanding_rhyme_mystery_to.py
=======================================================================================

A standalone story world about a child visiting a fire station, hearing a
mysterious sound, misunderstanding what it means, and solving the small mystery
with help from a firefighter. The prose keeps a gentle rhyming-story style.

Premise
-------
A child at the fire station hears a repeated sound and sees a clue. At first the
child makes a wrong guess and feels reluctant to keep looking. Then the world
state changes as clues are gathered, the real cause is found, and the ending
shows a safer, calmer understanding.

Run it
------
    python storyworlds/worlds/gpt-5.4/reluctant_fire_station_misunderstanding_rhyme_mystery_to.py
    python storyworlds/worlds/gpt-5.4/reluctant_fire_station_misunderstanding_rhyme_mystery_to.py --sound clang --cause dryer
    python storyworlds/worlds/gpt-5.4/reluctant_fire_station_misunderstanding_rhyme_mystery_to.py --all
    python storyworlds/worlds/gpt-5.4/reluctant_fire_station_misunderstanding_rhyme_mystery_to.py --verify
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
    movable: bool = False
    visible: bool = True
    warm: bool = False
    noisy: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "firefighter_woman"}
        male = {"boy", "father", "man", "firefighter_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "firefighter_woman":
            return "firefighter"
        if self.type == "firefighter_man":
            return "firefighter"
        return self.type
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
class Sound:
    id: str
    word: str
    line: str
    repeats: str
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
class Cause:
    id: str
    label: str
    place: str
    clue: str
    reveal: str
    hush: str
    not_emergency: str
    rhythm: str
    hot: bool = False
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
class Guess:
    id: str
    line: str
    mistaken_about: set[str] = field(default_factory=set)
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
class HelperStyle:
    id: str
    intro: str
    teach: str
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_misunderstanding(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["guessing_wrong"] < THRESHOLD:
        return []
    sig = ("misunderstanding", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["reluctance"] += 1
    return []


def _r_clue_confidence(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["clues_found"] < 2:
        return []
    sig = ("confidence", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    if child.memes["reluctance"] > 0:
        child.memes["reluctance"] -= 1
    return []


def _r_solution_relief(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["mystery_solved"] < THRESHOLD:
        return []
    sig = ("relief", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="misunderstanding", tag="social", apply=_r_misunderstanding),
    Rule(name="clue_confidence", tag="cognitive", apply=_r_clue_confidence),
    Rule(name="solution_relief", tag="emotional", apply=_r_solution_relief),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def guess_fits(sound: Sound, cause: Cause, guess: Guess) -> bool:
    return cause.id not in guess.mistaken_about


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sound_id in SOUNDS:
        for cause_id in CAUSES:
            for guess_id, guess in GUESSES.items():
                if guess_fits(SOUNDS[sound_id], CAUSES[cause_id], guess):
                    combos.append((sound_id, cause_id, guess_id))
    return combos


def predict_resolution(cause: Cause, guess: Guess) -> dict:
    return {
        "wrong_guess": cause.id in guess.mistaken_about,
        "solvable": cause.id not in guess.mistaken_about,
    }


def station_opening(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"At the fire station bright and wide, {child.id} walked softly at {helper.id}'s side."
    )
    world.say(
        "Red trucks shone with polished grace, and boots stood ready, row by row, in place."
    )
    child.memes["awe"] += 1
    child.memes["curiosity"] += 1


def hear_sound(world: World, child: Entity, sound: Sound) -> None:
    child.meters["heard_sound"] += 1
    world.say(
        f"Then through the hall there came {sound.line}, {sound.repeats}, a busy little sign."
    )


def first_guess(world: World, child: Entity, guess: Guess) -> None:
    child.memes["guessing_wrong"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"{guess.line}" {child.id} said, and shuffled one small shoe. '
        f'{child.pronoun().capitalize()} felt reluctant about what to do.'
    )


def helper_response(world: World, helper: Entity, style: HelperStyle) -> None:
    world.say(
        f'{helper.id} smiled and spoke {style.intro} '
        f'"Let us look for clues, not fears. Small sounds can fool our ears."'
    )


def find_first_clue(world: World, child: Entity, cause: Cause) -> None:
    child.meters["clues_found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They followed the sound past coats and hose, and there {cause.clue} close."
    )


def find_second_clue(world: World, child: Entity, sound: Sound, cause: Cause) -> None:
    child.meters["clues_found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{sound.word.capitalize()} here, {sound.word} there, the beat came from {cause.place} air."
    )


def solve_mystery(world: World, child: Entity, helper: Entity, style: HelperStyle, cause: Cause) -> None:
    child.meters["mystery_solved"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Aha!" said {helper.id}. "{cause.reveal}"'
    )
    world.say(
        f'{style.teach} "{cause.not_emergency}"'
    )
    world.say(
        f"{child.id} took one slower, braver breath. The mystery lost its worried teeth."
    )


def ending(world: World, child: Entity, sound: Sound, cause: Cause) -> None:
    world.say(
        f"Soon {child.id} could hear {sound.word} and grin, because {cause.hush}."
    )
    world.say(
        f"Now the fire station seemed less grim. {cause.rhythm}"
    )


SOUNDS = {
    "clang": Sound(
        id="clang",
        word="clang",
        line="a little clang in a metal ring",
        repeats="clang-cling, clang-cling",
        tags={"sound", "metal"},
    ),
    "hum": Sound(
        id="hum",
        word="hum",
        line="a low hum like a tucked-in drum",
        repeats="hum-hummm, hum-hummm",
        tags={"sound", "machine"},
    ),
    "tap": Sound(
        id="tap",
        word="tap",
        line="a quick tap with a skip and clap",
        repeats="tap-tap, tip-tap",
        tags={"sound", "small"},
    ),
}

CAUSES = {
    "dryer": Cause(
        id="dryer",
        label="gear dryer",
        place="the drying room",
        clue="warm gloves hung on a rack",
        reveal="The gear dryer was turning and making its tidy morning song.",
        hush="the warm dryer helped the firefighters get their gloves and coats ready",
        not_emergency="It is only the dryer today, not an emergency call.",
        rhythm="The gentle hum meant helping gear get dry, so brave coats would be ready by and by.",
        hot=True,
        tags={"dryer", "gear", "safety"},
    ),
    "locker": Cause(
        id="locker",
        label="swinging locker tag",
        place="the locker row",
        clue="a silver name tag bumping a door",
        reveal="A locker tag was swinging and tapping the metal when the fan blew by.",
        hush="a tiny tag had been tapping a locker door in the fan's breeze",
        not_emergency="It is only a loose tag today, not an emergency bell.",
        rhythm="The tapping tag was small, not dire; no rushing truck, no leaping fire.",
        tags={"locker", "metal", "wind"},
    ),
    "washer": Cause(
        id="washer",
        label="hose washer",
        place="the wash corner",
        clue="wet boots lined up by a spinning machine",
        reveal="The washer was swishing the muddy cloths from training time.",
        hush="the washer was cleaning station cloths with a splashy beat",
        not_emergency="It is only the washer today, not the station alarm.",
        rhythm="The splash and swish did not mean fright; it meant clean cloths by lunch-time light.",
        tags={"washer", "cleaning", "water"},
    ),
}

GUESSES = {
    "alarm": Guess(
        id="alarm",
        line="Is the alarm calling everyone to run?",
        mistaken_about={"dryer", "locker", "washer"},
    ),
    "monster": Guess(
        id="monster",
        line="Is there a clanky monster hiding by the truck?",
        mistaken_about={"dryer", "locker"},
    ),
    "mouse": Guess(
        id="mouse",
        line="Maybe a mouse is drumming in a boot?",
        mistaken_about={"washer", "dryer"},
    ),
}

HELPER_STYLES = {
    "calm": HelperStyle(
        id="calm",
        intro="in a calm, kind way.",
        teach="Then the firefighter knelt down and said,",
        tags={"calm", "teaching"},
    ),
    "playful": HelperStyle(
        id="playful",
        intro="with a soft little grin.",
        teach="Then the firefighter tipped a helmet and said,",
        tags={"playful", "teaching"},
    ),
}

GIRL_NAMES = ["Mia", "Lila", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Theo", "Finn"]


@dataclass
class StoryParams:
    sound: str
    cause: str
    guess: str
    helper_style: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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
    "fire_station": [
        (
            "What is a fire station?",
            "A fire station is the place where firefighters keep their trucks, tools, and gear. It is also where they get ready to help people quickly."
        )
    ],
    "alarm": [
        (
            "What does a fire station alarm do?",
            "A fire station alarm tells firefighters that they are needed fast. It helps them know when there is a real emergency."
        )
    ],
    "dryer": [
        (
            "Why do firefighters dry their gear?",
            "Firefighters dry wet gloves and coats so the gear is ready to use again. Dry gear is more comfortable and safer to wear."
        )
    ],
    "washer": [
        (
            "Why would a fire station use a washer?",
            "A fire station uses a washer to clean cloths, uniforms, or other washable items. Cleaning helps the station stay ready and neat."
        )
    ],
    "locker": [
        (
            "What is a locker for?",
            "A locker is a storage space where a person keeps their things. At a fire station, lockers can hold gear or personal items."
        )
    ],
    "mystery": [
        (
            "What is a mystery to solve?",
            "A mystery to solve is a question you do not know the answer to yet. You solve it by noticing clues and thinking carefully."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something means one thing, but it really means another. Talking and checking clues can fix it."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "fire_station",
    "mystery",
    "misunderstanding",
    "alarm",
    "dryer",
    "washer",
    "locker",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    sound = f["sound"]
    cause = f["cause"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old set in a fire station, where a child hears "{sound.word}" and becomes reluctant because of a misunderstanding.',
        f"Tell a gentle mystery-to-solve story in rhyme where {child.id} visits a fire station, guesses wrong about a strange sound, and learns it came from the {cause.label}.",
        'Write a child-facing story with rhyme, a misunderstanding, and a small mystery that ends with calm explanation instead of fear.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    sound = f["sound"]
    cause = f["cause"]
    guess = f["guess"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who visited a fire station, and {helper.id}, the firefighter who helped. Together they listened, searched, and solved a small mystery."
        ),
        (
            "What was the mystery to solve?",
            f"The mystery was what was making the {sound.word} sound in the station. At first nobody said the answer, so they had to follow clues and look carefully."
        ),
        (
            f"Why did {child.id} feel reluctant?",
            f"{child.id} made a wrong guess and worried that the sound meant something scary. That misunderstanding made {child.pronoun('object')} feel reluctant to keep looking at first."
        ),
        (
            f"What misunderstanding did {child.id} have?",
            f"{child.id} thought, \"{guess.line}\" But the sound did not mean that at all, because it was really coming from the {cause.label}."
        ),
        (
            "How did they solve the mystery?",
            f"They solved it by looking for clues, following the sound, and checking where it came from. They found {cause.clue}, then noticed the noise was really from {cause.place}."
        ),
        (
            "What was making the sound in the end?",
            f"In the end, the {cause.label} was making the sound. When the true cause was explained, the station felt calm again instead of scary."
        ),
        (
            f"How did {child.id} feel at the end?",
            f"{child.id} felt relieved and braver at the end. Once the mystery was solved, the sound no longer seemed frightening."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"fire_station", "mystery", "misunderstanding", "alarm"}
    tags |= set(f["cause"].tags)
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
        flags = [name for name, on in (
            ("movable", ent.movable),
            ("visible", ent.visible),
            ("warm", ent.warm),
            ("noisy", ent.noisy),
        ) if on]
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
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:10} ({ent.type:16}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def tell(
    sound: Sound,
    cause: Cause,
    guess: Guess,
    helper_style: HelperStyle,
    child_name: str = "Mia",
    child_gender: str = "girl",
    helper_name: str = "Chief Ana",
    helper_gender: str = "firefighter_woman",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        attrs={},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        attrs={},
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="machine" if cause.id in {"dryer", "washer"} else "object",
        label=cause.label,
        attrs={"place": cause.place},
        warm=cause.hot,
        noisy=True,
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=cause.clue,
        attrs={"cause": cause.id},
        visible=True,
    ))

    child.meters["heard_sound"] = 0.0
    child.meters["clues_found"] = 0.0
    child.meters["mystery_solved"] = 0.0
    child.memes["guessing_wrong"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["reluctance"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["awe"] = 0.0

    world.facts.update(
        child=child,
        helper=helper,
        sound=sound,
        cause=cause,
        guess=guess,
        helper_style=helper_style,
    )

    station_opening(world, child, helper)
    hear_sound(world, child, sound)

    world.para()
    first_guess(world, child, guess)
    helper_response(world, helper, helper_style)

    world.para()
    find_first_clue(world, child, cause)
    find_second_clue(world, child, sound, cause)
    solve_mystery(world, child, helper, helper_style, cause)

    world.para()
    ending(world, child, sound, cause)

    world.facts.update(
        solved=child.meters["mystery_solved"] >= THRESHOLD,
        reluctant=child.memes["reluctance"] >= THRESHOLD,
        wrong_guess=child.memes["guessing_wrong"] >= THRESHOLD,
    )
    return world


CURATED = [
    StoryParams(
        sound="clang",
        cause="dryer",
        guess="alarm",
        helper_style="calm",
        child_name="Mia",
        child_gender="girl",
        helper_name="Firefighter Ana",
        helper_gender="firefighter_woman",
    ),
    StoryParams(
        sound="tap",
        cause="locker",
        guess="monster",
        helper_style="playful",
        child_name="Ben",
        child_gender="boy",
        helper_name="Firefighter Luis",
        helper_gender="firefighter_man",
    ),
    StoryParams(
        sound="hum",
        cause="washer",
        guess="alarm",
        helper_style="calm",
        child_name="Nora",
        child_gender="girl",
        helper_name="Firefighter Jo",
        helper_gender="firefighter_woman",
    ),
]


def explain_rejection(sound: Sound, cause: Cause, guess: Guess) -> str:
    if cause.id in guess.mistaken_about:
        return (
            f"(No story: the chosen misunderstanding '{guess.id}' would already point away from the true cause "
            f"'{cause.id}', so the little mystery would not land cleanly. Pick a different guess.)"
        )
    return (
        f"(No story: {sound.id}, {cause.id}, and {guess.id} do not make a clean misunderstanding mystery.)"
    )


ASP_RULES = r"""
fits(S, C, G) :- sound(S), cause(C), guess(G), not mistaken_about(G, C).
valid(S, C, G) :- fits(S, C, G).

wrong_guess_for(C, G) :- cause(C), guess(G), fits(_, C, G).
solvable(C, G) :- fits(_, C, G).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SOUNDS:
        lines.append(asp.fact("sound", sid))
    for cid in CAUSES:
        lines.append(asp.fact("cause", cid))
    for gid, guess in GUESSES.items():
        lines.append(asp.fact("guess", gid))
        for cid in sorted(guess.mistaken_about):
            lines.append(asp.fact("mistaken_about", gid, cid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming fire-station mystery storyworld with misunderstanding and a reluctant child."
    )
    ap.add_argument("--sound", choices=sorted(SOUNDS))
    ap.add_argument("--cause", choices=sorted(CAUSES))
    ap.add_argument("--guess", choices=sorted(GUESSES))
    ap.add_argument("--helper-style", choices=sorted(HELPER_STYLES), dest="helper_style")
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["firefighter_woman", "firefighter_man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sound and args.cause and args.guess:
        if not guess_fits(SOUNDS[args.sound], CAUSES[args.cause], GUESSES[args.guess]):
            raise StoryError(explain_rejection(SOUNDS[args.sound], CAUSES[args.cause], GUESSES[args.guess]))

    combos = [
        combo for combo in valid_combos()
        if (args.sound is None or combo[0] == args.sound)
        and (args.cause is None or combo[1] == args.cause)
        and (args.guess is None or combo[2] == args.guess)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    sound_id, cause_id, guess_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["firefighter_woman", "firefighter_man"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    helper_name = args.helper_name or (
        "Firefighter Ana" if helper_gender == "firefighter_woman" else "Firefighter Luis"
    )
    helper_style = args.helper_style or rng.choice(sorted(HELPER_STYLES))
    return StoryParams(
        sound=sound_id,
        cause=cause_id,
        guess=guess_id,
        helper_style=helper_style,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.sound not in SOUNDS:
        raise StoryError(f"(Invalid sound: {params.sound})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.guess not in GUESSES:
        raise StoryError(f"(Invalid guess: {params.guess})")
    if params.helper_style not in HELPER_STYLES:
        raise StoryError(f"(Invalid helper style: {params.helper_style})")
    if not guess_fits(SOUNDS[params.sound], CAUSES[params.cause], GUESSES[params.guess]):
        raise StoryError(explain_rejection(SOUNDS[params.sound], CAUSES[params.cause], GUESSES[params.guess]))

    world = tell(
        sound=SOUNDS[params.sound],
        cause=CAUSES[params.cause],
        guess=GUESSES[params.guess],
        helper_style=HELPER_STYLES[params.helper_style],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (sound, cause, guess) combos:\n")
        for sound_id, cause_id, guess_id in combos:
            print(f"  {sound_id:6} {cause_id:8} {guess_id}")
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
            header = f"### {p.child_name}: {p.sound}/{p.cause}/{p.guess}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
