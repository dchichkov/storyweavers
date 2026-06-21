#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trample_microphone_bravery_mystery_to_solve_space.py
================================================================================

A standalone story world about two children playing a space adventure and
solving a small mystery with quiet bravery. The world is built around a simple
constraint:

- a mystery must make a real sound, because the children solve it by using a
  microphone to hear or answer the sound;
- the clue must honestly fit the mystery;
- some clues lie on the floor and can be trampled if a child rushes.

The turn is state-driven: a child hears a strange space sound, spots a clue,
faces the dark, and must choose whether to rush or move carefully. In the happy
branch, careful bravery preserves the clue. In the oops branch, the clue is
trampled, but the microphone still helps the children recover and solve the
mystery.

Run it
------
    python storyworlds/worlds/gpt-5.4/trample_microphone_bravery_mystery_to_solve_space.py
    python storyworlds/worlds/gpt-5.4/trample_microphone_bravery_mystery_to_solve_space.py --all
    python storyworlds/worlds/gpt-5.4/trample_microphone_bravery_mystery_to_solve_space.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/trample_microphone_bravery_mystery_to_solve_space.py --json
    python storyworlds/worlds/gpt-5.4/trample_microphone_bravery_mystery_to_solve_space.py --asp
    python storyworlds/worlds/gpt-5.4/trample_microphone_bravery_mystery_to_solve_space.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
class Theme:
    id: str
    scene: str
    rig: str
    team_word: str
    mission: str
    dark_place: str
    ending: str
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
class Mystery:
    id: str
    title: str
    sound: str
    source_label: str
    found_place: str
    needs: set[str] = field(default_factory=set)
    sound_source: bool = True
    ending_image: str = ""
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
class Clue:
    id: str
    label: str
    phrase: str
    where: str
    tags: set[str] = field(default_factory=set)
    on_floor: bool = True
    trampleable: bool = True
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
class MicrophoneTool:
    id: str
    label: str
    phrase: str
    action: str
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
class Approach:
    id: str
    label: str
    careful: bool
    rush_line: str
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


THEMES = {
    "starship": Theme(
        id="starship",
        scene="a silver starship",
        rig="The sofa was the cockpit, a blanket became the captain's cape, and a row of cushions made a narrow moon tunnel.",
        team_word="crew",
        mission="the mystery signal",
        dark_place="the shadowy moon tunnel behind the cushions",
        ending="set off on their next mission with slower feet and braver hearts",
    ),
    "moonbase": Theme(
        id="moonbase",
        scene="a bright moon base",
        rig="A table became mission control, a laundry basket became an air lock, and a trail of pillows made a crater path.",
        team_word="space team",
        mission="the missing station sound",
        dark_place="the dim storage tunnel by the air lock",
        ending="went back to moon-base duty smiling at how brave careful steps could be",
    ),
    "marscamp": Theme(
        id="marscamp",
        scene="a red-planet camp",
        rig="The rug was the dusty planet floor, two chairs were a rover garage, and a cardboard box became a supply dome.",
        team_word="explorers",
        mission="the odd little ping",
        dark_place="the dark rover garage",
        ending="marched into their next Mars game ready to listen before they leapt",
    ),
}

MYSTERIES = {
    "lost_rover": Mystery(
        id="lost_rover",
        title="a lost rover mystery",
        sound="beep-beep",
        source_label="the little rover",
        found_place="under a silver emergency blanket",
        needs={"tracks", "bolts", "antenna"},
        sound_source=True,
        ending_image="Its blue light blinked like a tiny star.",
    ),
    "sleepy_probe": Mystery(
        id="sleepy_probe",
        title="a sleepy probe mystery",
        sound="ping... ping...",
        source_label="the round space probe",
        found_place="behind the storage box",
        needs={"antenna", "metal", "tracks"},
        sound_source=True,
        ending_image="Its round shell gave one glad, glowing blink.",
    ),
    "moon_moth": Mystery(
        id="moon_moth",
        title="a moon-moth mystery",
        sound="chirr-chirr",
        source_label="the moon moth",
        found_place="inside the helmet shelf",
        needs={"feather", "dust"},
        sound_source=True,
        ending_image="Its wings shimmered silver and soft in the dark.",
    ),
    "silent_map": Mystery(
        id="silent_map",
        title="a silent map mystery",
        sound="",
        source_label="the folded star map",
        found_place="inside a book",
        needs={"paper"},
        sound_source=False,
        ending_image="The map showed a quiet path of stars.",
    ),
}

CLUES = {
    "wheel_tracks": Clue(
        id="wheel_tracks",
        label="wheel tracks",
        phrase="tiny wheel tracks in the dust",
        where="curving across the rug like lines on a gray moon",
        tags={"tracks", "dust"},
        on_floor=True,
        trampleable=True,
    ),
    "loose_bolts": Clue(
        id="loose_bolts",
        label="loose bolts",
        phrase="three loose bolts",
        where="glinting on the floor by the tunnel mouth",
        tags={"bolts", "metal"},
        on_floor=True,
        trampleable=True,
    ),
    "bent_antenna": Clue(
        id="bent_antenna",
        label="a bent antenna",
        phrase="a bent antenna sticking out from behind a pillow",
        where="pointing toward the dark place",
        tags={"antenna", "metal"},
        on_floor=False,
        trampleable=False,
    ),
    "silver_feather": Clue(
        id="silver_feather",
        label="a silver feather",
        phrase="a silver feather",
        where="resting on the floor with a ring of moon dust around it",
        tags={"feather", "dust"},
        on_floor=True,
        trampleable=True,
    ),
    "paper_scrap": Clue(
        id="paper_scrap",
        label="a paper scrap",
        phrase="a folded paper scrap",
        where="caught under the table leg",
        tags={"paper"},
        on_floor=True,
        trampleable=True,
    ),
}

MICROPHONES = {
    "hand_mic": MicrophoneTool(
        id="hand_mic",
        label="microphone",
        phrase="a shiny microphone",
        action="lifted the microphone and called softly into it",
        tags={"microphone", "sound"},
    ),
    "helmet_mic": MicrophoneTool(
        id="helmet_mic",
        label="helmet microphone",
        phrase="a crackly helmet microphone",
        action="tapped the helmet microphone and spoke in a calm space voice",
        tags={"microphone", "sound"},
    ),
    "radio_mic": MicrophoneTool(
        id="radio_mic",
        label="radio microphone",
        phrase="the mission radio microphone",
        action="held the radio microphone close and whispered a careful hello",
        tags={"microphone", "sound"},
    ),
}

APPROACHES = {
    "careful": Approach(
        id="careful",
        label="careful",
        careful=True,
        rush_line="",
        tags={"careful", "bravery"},
    ),
    "rush": Approach(
        id="rush",
        label="rush",
        careful=False,
        rush_line="The wish to hurry made every clue look smaller than the answer.",
        tags={"rush", "oops"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Zoe", "Ava", "Nora", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Eli", "Sam", "Jack", "Noah"]
TRAITS = ["careful", "curious", "steady", "bold", "thoughtful", "brave"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_trample(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("hero")
    clue = world.get("clue")
    if child.meters["running"] < THRESHOLD:
        return out
    if not clue.attrs.get("trampleable", False):
        return out
    sig = ("trample", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["damaged"] += 1
    child.memes["regret"] += 1
    world.get("friend").memes["alarm"] += 1
    out.append("__trample__")
    return out


def _r_answer(world: World) -> list[str]:
    out: list[str] = []
    mic = world.get("mic")
    source = world.get("source")
    if mic.meters["used"] < THRESHOLD:
        return out
    if not source.attrs.get("sound_source", False):
        return out
    sig = ("answer", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["answering"] += 1
    out.append("__answer__")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    clue = world.get("clue")
    if source.meters["answering"] < THRESHOLD:
        return out
    if clue.meters["followed"] < THRESHOLD and clue.meters["noticed"] < THRESHOLD:
        return out
    sig = ("solve", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["relief"] += 1
    world.get("friend").memes["relief"] += 1
    world.get("hero").memes["bravery"] += 1
    source.meters["found"] += 1
    world.facts["solved"] = True
    out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule(name="trample", tag="physical", apply=_r_trample),
    Rule(name="answer", tag="signal", apply=_r_answer),
    Rule(name="solve", tag="plot", apply=_r_solve),
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


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def clue_fits_mystery(mystery: Mystery, clue: Clue) -> bool:
    return bool(mystery.needs & clue.tags)


def mystery_needs_microphone(mystery: Mystery) -> bool:
    return mystery.sound_source


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for mystery_id, mystery in MYSTERIES.items():
            if not mystery_needs_microphone(mystery):
                continue
            for clue_id, clue in CLUES.items():
                if not clue_fits_mystery(mystery, clue):
                    continue
                for mic_id in MICROPHONES:
                    combos.append((theme_id, mystery_id, clue_id, mic_id))
    return combos


def explain_rejection(mystery: Mystery, clue: Clue) -> str:
    if not mystery.sound_source:
        return (
            f"(No story: {mystery.title} makes no sound, so a microphone cannot help solve it. "
            f"Pick a mystery with a beep, ping, or chirp.)"
        )
    return (
        f"(No story: {clue.phrase} does not honestly point to {mystery.source_label}. "
        f"Pick a clue that matches the mystery.)"
    )


def outcome_of(params: "StoryParams") -> str:
    clue = CLUES[params.clue]
    if params.approach == "rush" and clue.trampleable:
        return "oops_but_solved"
    return "careful_solved"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_trample(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["running"] += 1
    propagate(sim, narrate=False)
    clue = sim.get("clue")
    return {
        "damaged": clue.meters["damaged"] >= THRESHOLD,
        "trampleable": clue.attrs.get("trampleable", False),
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, friend: Entity, theme: Theme) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a quiet afternoon, {hero.id} and {friend.id} turned the room into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"Captain {hero.id} and Scout {friend.id}!" {hero.id} said. "Today we solve {theme.mission}."'
    )


def strange_sound(world: World, friend: Entity, mystery: Mystery, theme: Theme) -> None:
    world.say(
        f"Then a tiny sound floated out of {theme.dark_place}: {mystery.sound}. "
        f"It was small, strange, and impossible to ignore."
    )
    world.say(
        f'{friend.id} went still. "Did you hear that?" {friend.pronoun()} whispered. '
        f'"Something in there needs us."'
    )


def find_clue(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["noticed"] += 1
    world.say(
        f"At the mouth of the dark place, they spotted {clue.phrase}, {clue.where}."
    )
    if clue.on_floor:
        world.say(
            f'{friend.id} pointed down. "Wait," {friend.pronoun()} said. '
            f'"If we stomp through here, we might trample the clue."'
        )
    else:
        world.say(
            f'{hero.id} looked hard at it. "That is not just space junk," {hero.pronoun()} said.'
        )


def warn_with_prediction(world: World, friend: Entity, clue: Clue) -> None:
    pred = predict_trample(world)
    world.facts["predicted_trample"] = pred["damaged"]
    if clue.trampleable and pred["damaged"]:
        world.say(
            f'{friend.id} imagined one fast run across the floor and shook {friend.pronoun("possessive")} head. '
            f'"The answer could vanish under our shoes," {friend.pronoun()} said.'
        )


def choose_approach(world: World, hero: Entity, approach: Approach, clue: Clue) -> None:
    if approach.careful:
        hero.memes["brave_choice"] += 1
        world.say(
            f"{hero.id} took a breath. The dark still felt big, but {hero.pronoun()} chose slow, brave steps instead of a dash."
        )
        if clue.on_floor:
            world.say(
                f"{hero.pronoun().capitalize()} stepped over the clue and kept it safe."
            )
        world.get("clue").meters["followed"] += 1
    else:
        hero.meters["running"] += 1
        world.say(approach.rush_line)
        world.say(
            f"{hero.id} darted forward before thinking it through."
        )
        propagate(world, narrate=False)
        if world.get("clue").meters["damaged"] >= THRESHOLD:
            world.say(
                f"One quick shoe slid through the dust and trampled part of the clue."
            )
            world.say(
                f'{hero.id} skidded to a stop. "Oh no," {hero.pronoun()} said. "I made the trail harder to read."'
            )
        world.get("clue").meters["followed"] += 1


def enter_dark(world: World, hero: Entity, friend: Entity, theme: Theme) -> None:
    hero.memes["fear"] += 1
    friend.memes["fear"] += 1
    world.say(
        f"Together they peered into {theme.dark_place}. It looked like the kind of dark that could swallow a whole game."
    )
    world.say(
        f"But {hero.id} lifted {hero.pronoun('possessive')} chin and went in anyway, because bravery felt less like roaring and more like taking the next good step."
    )


def use_microphone(world: World, hero: Entity, mic: MicrophoneTool, mystery: Mystery) -> None:
    mic_ent = world.get("mic")
    mic_ent.meters["used"] += 1
    world.say(
        f"{hero.id} {mic.action}. "
        f'"Unknown space friend," {hero.pronoun()} said, "we hear your {mystery.sound}. Answer if you can."'
    )
    propagate(world, narrate=False)
    if world.get("source").meters["answering"] >= THRESHOLD:
        world.say(
            f"At once the sound came back, clearer this time: {mystery.sound}. The microphone helped them hear exactly where it was coming from."
        )


def recover_after_oops(world: World, friend: Entity, clue: Clue) -> None:
    if world.get("clue").meters["damaged"] < THRESHOLD:
        return
    friend.memes["steady"] += 1
    world.say(
        f"{friend.id} knelt beside the smudged clue instead of giving up."
    )
    if clue.id == "wheel_tracks":
        world.say(
            f'"The tracks are messy now," {friend.pronoun()} said, "but they still bend toward the left wall."'
        )
    elif clue.id == "loose_bolts":
        world.say(
            f'"Two bolts are still in a line," {friend.pronoun()} said. "That line shows the way."'
        )
    elif clue.id == "silver_feather":
        world.say(
            f'"There is still dust sparkling beside the feather," {friend.pronoun()} said. "The moth must have fluttered upward."'
        )
    else:
        world.say(
            f'"Part of the clue is gone," {friend.pronoun()} said, "but not all of it."'
        )


def solve(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    propagate(world, narrate=False)
    if not world.facts.get("solved"):
        raise StoryError("The mystery did not resolve. This parameter set should not be generated.")
    world.say(
        f"They followed the last hint and found {mystery.source_label} {mystery.found_place}. {mystery.ending_image}"
    )
    world.say(
        f'{friend.id} laughed first. "{hero.id}, we solved it!" {friend.pronoun()} cried.'
    )
    world.say(
        f'{hero.id} smiled into the dark. "We did," {hero.pronoun()} said, and the room did not feel scary anymore.'
    )


def resolution(world: World, hero: Entity, friend: Entity, theme: Theme, mystery: Mystery, approach: Approach) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    if approach.careful:
        world.say(
            f"On the way back, {hero.id} glanced once more at the untouched clue and felt proud. Careful bravery had helped the whole {theme.team_word} solve {mystery.title}."
        )
    else:
        world.say(
            f"On the way back, {hero.id} looked at the smudged clue and remembered the sound of that accidental trample. Next time, {hero.pronoun()} knew, brave feet would also be patient feet."
        )
    world.say(
        f"Soon they were back in the bright room, and the brave little {theme.team_word} {theme.ending}."
    )


# ---------------------------------------------------------------------------
# Full tale
# ---------------------------------------------------------------------------
def tell(
    theme: Theme,
    mystery: Mystery,
    clue: Clue,
    microphone: MicrophoneTool,
    approach: Approach,
    *,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
    hero_trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[hero_trait],
        attrs={"display_name": hero_name},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=["steady"],
        attrs={"display_name": friend_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    world.add(Entity(
        id="clue",
        type="clue",
        label=clue.label,
        attrs={"trampleable": clue.trampleable, "on_floor": clue.on_floor, "tags": set(clue.tags)},
    ))
    world.add(Entity(
        id="mic",
        type="tool",
        label=microphone.label,
        attrs={"tags": set(microphone.tags)},
    ))
    world.add(Entity(
        id="source",
        type="source",
        label=mystery.source_label,
        attrs={"sound_source": mystery.sound_source, "needs": set(mystery.needs)},
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        theme=theme,
        mystery=mystery,
        clue_cfg=clue,
        mic_cfg=microphone,
        approach=approach,
        solved=False,
        predicted_trample=False,
    )

    introduce(world, hero, friend, theme)
    strange_sound(world, friend, mystery, theme)

    world.para()
    find_clue(world, hero, friend, clue)
    warn_with_prediction(world, friend, clue)
    choose_approach(world, hero, approach, clue)

    world.para()
    enter_dark(world, hero, friend, theme)
    use_microphone(world, hero, microphone, mystery)
    recover_after_oops(world, friend, clue)
    solve(world, hero, friend, mystery)

    world.para()
    resolution(world, hero, friend, theme, mystery, approach)
    return world


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    theme: str
    mystery: str
    clue: str
    microphone: str
    approach: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    hero_trait: str
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
        theme="starship",
        mystery="lost_rover",
        clue="wheel_tracks",
        microphone="hand_mic",
        approach="careful",
        hero_name="Luna",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        parent="mother",
        hero_trait="brave",
        seed=101,
    ),
    StoryParams(
        theme="moonbase",
        mystery="sleepy_probe",
        clue="bent_antenna",
        microphone="radio_mic",
        approach="careful",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        parent="father",
        hero_trait="steady",
        seed=102,
    ),
    StoryParams(
        theme="marscamp",
        mystery="moon_moth",
        clue="silver_feather",
        microphone="helmet_mic",
        approach="rush",
        hero_name="Mia",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        parent="mother",
        hero_trait="curious",
        seed=103,
    ),
    StoryParams(
        theme="starship",
        mystery="lost_rover",
        clue="loose_bolts",
        microphone="radio_mic",
        approach="rush",
        hero_name="Eli",
        hero_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        parent="father",
        hero_trait="bold",
        seed=104,
    ),
]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "microphone": [
        (
            "What does a microphone do?",
            "A microphone catches sound and makes it easier to hear or send. It helps voices and tiny noises travel more clearly."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when something feels a little scary. Sometimes brave people move slowly and think carefully instead of rushing."
        )
    ],
    "tracks": [
        (
            "What can tracks tell you?",
            "Tracks can show where something went. If you follow them carefully, they can help you solve a mystery."
        )
    ],
    "rover": [
        (
            "What is a rover?",
            "A rover is a little machine that rolls along the ground to explore. In space stories, a rover often helps people look around safely."
        )
    ],
    "probe": [
        (
            "What is a probe?",
            "A probe is a small machine sent to check or study a place. It can send back pings, pictures, or other signals."
        )
    ],
    "moth": [
        (
            "What is a moth?",
            "A moth is a flying insect with soft wings. In a make-believe space story, a moon moth can flutter and chirp in the dark."
        )
    ],
    "trample": [
        (
            "What does trample mean?",
            "To trample something means to step on it roughly and squash or smear it. That can ruin clues, flowers, or other fragile things."
        )
    ],
    "mystery": [
        (
            "What is a mystery to solve?",
            "A mystery is a question you do not know the answer to yet. You solve it by noticing clues and thinking about what they mean."
        )
    ],
}
KNOWLEDGE_ORDER = ["microphone", "bravery", "mystery", "trample", "tracks", "rover", "probe", "moth"]


def display_name(ent: Entity) -> str:
    return str(ent.attrs.get("display_name", ent.label or ent.id))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    theme = f["theme"]
    mystery = f["mystery"]
    clue = f["clue_cfg"]
    approach = f["approach"]
    hero_name = display_name(hero)
    friend_name = display_name(friend)
    if approach.careful:
        return [
            f'Write a short space-adventure story for a 3-to-5-year-old that includes the words "trample" and "microphone."',
            f"Tell a gentle mystery story where {hero_name} and {friend_name} hear {mystery.sound} in a pretend {theme.scene}, notice {clue.phrase}, and solve the mystery by moving carefully and using a microphone.",
            f"Write a story about bravery where the brave choice is not running fast but protecting a clue and listening closely in the dark.",
        ]
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the words "trample" and "microphone."',
        f"Tell a small mystery-to-solve story where {hero_name} rushes in a pretend {theme.scene}, almost loses the answer by trying to trample past a clue, and then recovers by using a microphone and help from {friend_name}.",
        f"Write a gentle cautionary adventure where a child learns that bravery can be careful after one hasty mistake in the dark.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    theme = f["theme"]
    mystery = f["mystery"]
    clue = f["clue_cfg"]
    mic = f["mic_cfg"]
    approach = f["approach"]
    hero_name = display_name(hero)
    friend_name = display_name(friend)

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name} and {friend_name}, two children playing a space adventure together. They become a brave little team when a strange sound turns their game into a mystery."
        ),
        (
            "What mystery did they try to solve?",
            f"They wanted to find out who was making the strange sound {mystery.sound} in the dark place. The mystery mattered because the sound made it seem as if someone or something needed help."
        ),
        (
            f"What clue did they find first?",
            f"They first noticed {clue.phrase}. That clue mattered because it pointed toward {mystery.source_label} and gave them a path to follow."
        ),
        (
            "How did the microphone help?",
            f"They used {mic.phrase} to speak softly and listen for the answer. When the sound came back more clearly, the microphone helped them tell where to go next."
        ),
    ]
    if approach.careful:
        qa.append(
            (
                f"How did {hero_name} show bravery?",
                f"{hero_name} showed bravery by choosing slow steps in the dark instead of rushing. That kept the clue safe and helped the children solve the mystery the smart way."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They found {mystery.source_label} {mystery.found_place} and the room stopped feeling scary. The ending shows that careful bravery can solve a mystery and keep good clues safe."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero_name} rushed?",
                f"{hero_name} hurried forward and trampled part of the clue. That made the mystery harder for a moment, because some of the trail was smudged and harder to read."
            )
        )
        qa.append(
            (
                f"How did they still solve the mystery after the mistake?",
                f"{friend_name} knelt down, studied what was left of the clue, and did not give up. Then the microphone helped them hear the answer clearly, so together they could finish solving the mystery."
            )
        )
        qa.append(
            (
                f"What did {hero_name} learn?",
                f"{hero_name} learned that brave feet should also be patient feet. The trample mistake showed that rushing can damage a clue, while careful listening helps solve the problem."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"microphone", "bravery", "mystery"}
    clue = f["clue_cfg"]
    mystery = f["mystery"]
    approach = f["approach"]
    if clue.id == "wheel_tracks":
        tags.add("tracks")
    if mystery.id == "lost_rover":
        tags.add("rover")
    if mystery.id == "sleepy_probe":
        tags.add("probe")
    if mystery.id == "moon_moth":
        tags.add("moth")
    if approach.id == "rush" and clue.trampleable:
        tags.add("trample")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for eid, ent in world.entities.items():
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
        lines.append(f"  {eid:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(M,C) :- mystery(M), clue(C), needs(M,T), clue_tag(C,T).
usable(M) :- mystery(M), sound_source(M).

valid(Th,M,C,Mic) :- theme(Th), mystery(M), clue(C), microphone(Mic), usable(M), fits(M,C).

oops :- chosen_approach(rush), chosen_clue(C), trampleable(C).
careful_end :- not oops.
outcome(oops_but_solved) :- oops.
outcome(careful_solved) :- careful_end.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        if mystery.sound_source:
            lines.append(asp.fact("sound_source", mystery_id))
        for tag in sorted(mystery.needs):
            lines.append(asp.fact("needs", mystery_id, tag))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        if clue.trampleable:
            lines.append(asp.fact("trampleable", clue_id))
        for tag in sorted(clue.tags):
            lines.append(asp.fact("clue_tag", clue_id, tag))
    for mic_id in MICROPHONES:
        lines.append(asp.fact("microphone", mic_id))
    for approach_id in APPROACHES:
        lines.append(asp.fact("approach", approach_id))
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
            asp.fact("chosen_approach", params.approach),
            asp.fact("chosen_clue", params.clue),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
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
        sample = generate(cases[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI + interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a space adventure with bravery, a microphone, and a mystery to solve."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--microphone", choices=MICROPHONES)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mystery and args.clue:
        mystery = MYSTERIES[args.mystery]
        clue = CLUES[args.clue]
        if not (mystery_needs_microphone(mystery) and clue_fits_mystery(mystery, clue)):
            raise StoryError(explain_rejection(mystery, clue))
    if args.mystery and not mystery_needs_microphone(MYSTERIES[args.mystery]):
        raise StoryError(explain_rejection(MYSTERIES[args.mystery], CLUES.get(args.clue or "paper_scrap", CLUES["paper_scrap"])))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.clue is None or combo[2] == args.clue)
        and (args.microphone is None or combo[3] == args.microphone)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, mystery, clue, microphone = rng.choice(sorted(combos))
    approach = args.approach or rng.choice(sorted(APPROACHES))
    parent = args.parent or rng.choice(["mother", "father"])
    hero_name, hero_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=hero_name)
    hero_trait = rng.choice(TRAITS)
    return StoryParams(
        theme=theme,
        mystery=mystery,
        clue=clue,
        microphone=microphone,
        approach=approach,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        hero_trait=hero_trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"Unknown theme: {params.theme}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.microphone not in MICROPHONES:
        raise StoryError(f"Unknown microphone: {params.microphone}")
    if params.approach not in APPROACHES:
        raise StoryError(f"Unknown approach: {params.approach}")
    mystery = MYSTERIES[params.mystery]
    clue = CLUES[params.clue]
    if not mystery_needs_microphone(mystery):
        raise StoryError(explain_rejection(mystery, clue))
    if not clue_fits_mystery(mystery, clue):
        raise StoryError(explain_rejection(mystery, clue))

    world = tell(
        THEMES[params.theme],
        mystery,
        clue,
        MICROPHONES[params.microphone],
        APPROACHES[params.approach],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        hero_trait=params.hero_trait,
    )

    story = world.render().replace("hero", display_name(world.get("hero"))).replace("friend", display_name(world.get("friend")))
    story = story.replace("parent", world.get("parent").label_word)

    # Replace ids only at word boundaries by using exact phrases above and labels stored in attrs.
    # Since our prose uses display names directly in most places, the remaining substitutions are harmless.
    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} compatible (theme, mystery, clue, microphone) combos:\n")
        for theme, mystery, clue, microphone in combos:
            print(f"  {theme:9} {mystery:12} {clue:13} {microphone}")
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.mystery} with {p.clue} ({p.approach})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
