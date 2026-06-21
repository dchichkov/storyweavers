#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/percussion_eligible_digestion_mystery_to_solve_bedtime.py
====================================================================================

A standalone story world for a bedtime mystery: a child hears a strange night
sound, makes a tiny suspect list, and solves the puzzle with a calm grown-up.
The world is built around two real causes that can overlap:

* a soft tapping sound outside or near the room, like tiny percussion
* a sleepy tummy making digestion sounds after a bedtime snack

The mystery feels bigger when both happen at once. The child and grown-up make
an eligible-suspect list, test the clues, fix the outside sound, explain the
inside sound, and end with a changed bedtime picture: the room is quiet, the
mystery is understood, and the child can rest.

Run it
------
    python storyworlds/worlds/gpt-5.4/percussion_eligible_digestion_mystery_to_solve_bedtime.py
    python storyworlds/worlds/gpt-5.4/percussion_eligible_digestion_mystery_to_solve_bedtime.py --weather windy --source branch_window --snack milk --fix tie_branch
    python storyworlds/worlds/gpt-5.4/percussion_eligible_digestion_mystery_to_solve_bedtime.py --source teacup_spoon --weather still
    python storyworlds/worlds/gpt-5.4/percussion_eligible_digestion_mystery_to_solve_bedtime.py --snack water
    python storyworlds/worlds/gpt-5.4/percussion_eligible_digestion_mystery_to_solve_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/percussion_eligible_digestion_mystery_to_solve_bedtime.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/percussion_eligible_digestion_mystery_to_solve_bedtime.py --verify
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
    attrs: dict = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
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
class Weather:
    id: str
    label: str
    bedtime_line: str
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
class TapSource:
    id: str
    label: str
    phrase: str
    place: str
    sound: str
    percussion_line: str
    active_weathers: set[str] = field(default_factory=set)
    required_fix: str = ""
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
class Snack:
    id: str
    label: str
    phrase: str
    digestion_level: int
    belly_line: str
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
class Fix:
    id: str
    label: str
    sense: int
    action_text: str
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


def _r_tap(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    room = world.get("room")
    child = world.get("child")
    if source.attrs.get("active") and source.meters["tapping"] < THRESHOLD:
        sig = ("tap", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            source.meters["tapping"] += 1
            room.meters["noise"] += 1
            child.memes["wonder"] += 1
            child.memes["unease"] += 1
            out.append("__tap__")
    return out


def _r_gurgle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    snack = world.get("snack")
    if snack.attrs.get("digesting") and child.meters["gurgle"] < THRESHOLD:
        sig = ("gurgle", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["gurgle"] += 1
            child.memes["wonder"] += 1
            out.append("__gurgle__")
    return out


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    room = world.get("room")
    if room.meters["noise"] >= THRESHOLD and child.meters["gurgle"] >= THRESHOLD:
        sig = ("mystery", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["puzzled"] += 1
            child.memes["unease"] += 1
            out.append("__mystery__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="tap", tag="physical", apply=_r_tap),
    Rule(name="gurgle", tag="physical", apply=_r_gurgle),
    Rule(name="mystery", tag="emotional", apply=_r_mystery),
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
            if sent == "__tap__":
                source_cfg = world.facts["source_cfg"]
                world.say(
                    f"From {source_cfg.place}, {source_cfg.sound}. "
                    f"To {world.get('child').id}, it sounded like tiny percussion in the dark."
                )
            elif sent == "__gurgle__":
                snack_cfg = world.facts["snack_cfg"]
                world.say(snack_cfg.belly_line)
            elif sent == "__mystery__":
                world.say(
                    "With a sound in the room and a sound inside the child as well, "
                    "the mystery felt twice as large for one quiet minute."
                )
    return produced


def source_active_in_weather(source: TapSource, weather: Weather) -> bool:
    return weather.id in source.active_weathers


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def fix_matches(source: TapSource, fix: Fix) -> bool:
    return source.required_fix == fix.id and fix.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for weather_id, weather in WEATHER.items():
        for source_id, source in SOURCES.items():
            if not source_active_in_weather(source, weather):
                continue
            for snack_id, snack in SNACKS.items():
                if snack.digestion_level < 1:
                    continue
                for fix_id, fix in FIXES.items():
                    if fix_matches(source, fix):
                        combos.append((weather_id, source_id, snack_id, fix_id))
    return combos


@dataclass
class StoryParams:
    weather: str
    source: str
    snack: str
    fix: str
    child_name: str
    child_gender: str
    parent: str
    comfort: str
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


def predict_mystery(weather: Weather, source: TapSource, snack: Snack) -> dict:
    return {
        "tap": source_active_in_weather(source, weather),
        "gurgle": snack.digestion_level >= 1,
        "double_mystery": source_active_in_weather(source, weather) and snack.digestion_level >= 1,
    }


def settle_in(world: World, child: Entity, parent: Entity, weather: Weather, snack: Snack) -> None:
    child.memes["sleepy"] += 1
    child.memes["safe"] += 1
    world.say(
        f"It was bedtime, and {weather.bedtime_line} "
        f"{child.id} was tucked under the blanket with {child.attrs.get('comfort', 'a soft toy')} nearby."
    )
    world.say(
        f"Before the light went low, {child.id} had eaten {snack.phrase} and listened "
        f"to {child.pronoun('possessive')} {parent.label_word}'s last good-night song."
    )


def first_clue(world: World, child: Entity) -> None:
    world.say(
        f"When the room had grown hush-hush, {child.id} opened one eye. "
        f"Something was making a small night sound."
    )
    propagate(world, narrate=True)
    if child.meters["gurgle"] >= THRESHOLD:
        world.say(
            f"{child.id} put a hand over {child.pronoun('possessive')} middle and listened even harder."
        )


def eligible_list(world: World, child: Entity, parent: Entity, weather: Weather, source: TapSource, snack: Snack) -> None:
    pred = predict_mystery(weather, source, snack)
    world.facts["predicted_double"] = pred["double_mystery"]
    world.facts["predicted_tap"] = pred["tap"]
    world.facts["predicted_gurgle"] = pred["gurgle"]
    child.memes["puzzled"] += 1
    world.say(
        f'"{parent.label_word.capitalize()}," whispered {child.id}, "there is a mystery to solve."'
    )
    world.say(
        f"{parent.label_word.capitalize()} sat on the edge of the bed and smiled in the dark. "
        f'"Then let us make an eligible suspect list," {parent.pronoun()} said. '
        f'"Only things that can truly make a sound tonight may be on it."'
    )
    suspects = [source.label, child.attrs.get("comfort", "the blanket"), "the moon"]
    world.facts["suspects"] = suspects
    world.say(
        f"They whispered the first few suspects: {suspects[0]}, {suspects[1]}, and the moon. "
        f"The moon looked lovely, but it was not an eligible suspect after all."
    )


def belly_clue(world: World, child: Entity, parent: Entity, snack: Snack) -> None:
    if child.meters["gurgle"] < THRESHOLD:
        return
    child.memes["curiosity"] += 1
    world.say(
        f"{parent.label_word.capitalize()} asked {child.id} to stay still for three breaths. "
        f"On the second breath came a little wobble from inside {child.pronoun('possessive')} belly."
    )
    world.say(
        f'"That part is digestion," {parent.pronoun()} said softly. '
        f'"Your tummy is busy turning {snack.label} into bedtime strength. It can talk in tiny glugs while it works."'
    )


def inspect_source(world: World, child: Entity, parent: Entity, source: TapSource) -> None:
    child.memes["brave"] += 1
    world.say(
        f"They followed the other clue with slipper-quiet steps. At {source.place}, "
        f"{parent.label_word.capitalize()} listened once, then twice."
    )
    world.say(source.percussion_line)


def solve_outside(world: World, child: Entity, parent: Entity, fix: Fix) -> None:
    source_ent = world.get("source")
    room = world.get("room")
    source_ent.attrs["active"] = False
    source_ent.meters["tapping"] = 0.0
    room.meters["noise"] = 0.0
    child.memes["unease"] = 0.0
    child.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {fix.action_text}. "
        f"After that, the outside tapping stopped at once."
    )


def explain_solution(world: World, child: Entity, parent: Entity, source: TapSource, snack: Snack) -> None:
    child.memes["understanding"] += 1
    child.memes["safe"] += 1
    child.memes["sleepy"] += 1
    world.say(
        f'"So the mystery had two pieces," {parent.label_word.capitalize()} said. '
        f'"{source.label.capitalize()} made the little percussion sound, and your digestion made the soft tummy sound."'
    )
    world.say(
        f"{child.id} thought about that, then nodded. A two-part mystery felt much smaller once both parts had names."
    )


def sleep_end(world: World, child: Entity, parent: Entity) -> None:
    comfort = child.attrs.get("comfort", "soft rabbit")
    world.say(
        f"They went back to bed. {child.id} tucked {comfort} under one arm, "
        f"and the room stayed still enough to hear only blankets, breathing, and one sleepy sigh."
    )
    world.say(
        f'"Good night, little solver," {parent.pronoun()} whispered. '
        f'Soon {child.id} was asleep, with no mystery left except where dreams begin.'
    )


def tell(
    weather: Weather,
    source_cfg: TapSource,
    snack_cfg: Snack,
    fix_cfg: Fix,
    *,
    child_name: str = "Nora",
    child_gender: str = "girl",
    parent_type: str = "mother",
    comfort: str = "a plush fox",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        attrs={"comfort": comfort},
        traits=["sleepy", "careful"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        attrs={},
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label="bedroom",
        attrs={},
    ))
    source = world.add(Entity(
        id="source",
        type="thing",
        label=source_cfg.label,
        attrs={"active": source_active_in_weather(source_cfg, weather)},
    ))
    snack = world.add(Entity(
        id="snack",
        type="thing",
        label=snack_cfg.label,
        attrs={"digesting": snack_cfg.digestion_level >= 1},
    ))

    world.facts.update(
        weather=weather,
        source_cfg=source_cfg,
        snack_cfg=snack_cfg,
        fix_cfg=fix_cfg,
        child=child,
        parent=parent,
        room=room,
        source=source,
        snack=snack,
        solved=False,
    )

    settle_in(world, child, parent, weather, snack_cfg)
    world.para()
    first_clue(world, child)
    eligible_list(world, child, parent, weather, source_cfg, snack_cfg)
    world.para()
    belly_clue(world, child, parent, snack_cfg)
    inspect_source(world, child, parent, source_cfg)
    solve_outside(world, child, parent, fix_cfg)
    explain_solution(world, child, parent, source_cfg, snack_cfg)
    world.para()
    sleep_end(world, child, parent)

    world.facts.update(
        solved=True,
        tap_was_real=source_active_in_weather(source_cfg, weather),
        belly_was_real=snack_cfg.digestion_level >= 1,
        quiet_after_fix=room.meters["noise"] < THRESHOLD,
        learned_digestion=child.memes["understanding"] >= THRESHOLD,
    )
    return world


WEATHER = {
    "windy": Weather(
        id="windy",
        label="windy",
        bedtime_line="Outside, the wind moved through the yard in slow, whispery swishes.",
        tags={"wind"},
    ),
    "rainy": Weather(
        id="rainy",
        label="rainy",
        bedtime_line="Outside, rain made silver dots on the dark window and hummed along the roof.",
        tags={"rain"},
    ),
    "cold": Weather(
        id="cold",
        label="cold",
        bedtime_line="Outside, the night was cold, and the house kept settling into its warm corners.",
        tags={"cold"},
    ),
    "still": Weather(
        id="still",
        label="still",
        bedtime_line="Outside, the night was still, with not even a leaf in a hurry.",
        tags={"still"},
    ),
}

SOURCES = {
    "branch_window": TapSource(
        id="branch_window",
        label="the branch by the window",
        phrase="a thin branch near the glass",
        place="the window",
        sound="tap-tap came against the pane",
        percussion_line="The branch was bobbing against the window in a neat little rhythm, like a finger practicing bedtime percussion.",
        active_weathers={"windy"},
        required_fix="tie_branch",
        tags={"branch", "window", "wind"},
    ),
    "gutter_drip": TapSource(
        id="gutter_drip",
        label="the loose gutter drop",
        phrase="a small drip from the loose gutter",
        place="the window corner",
        sound="plink... plink... came from the gutter",
        percussion_line="A drop was falling from the loose gutter to the stone below, making a tiny plink each time.",
        active_weathers={"rainy"},
        required_fix="set_bowl",
        tags={"gutter", "rain"},
    ),
    "teacup_spoon": TapSource(
        id="teacup_spoon",
        label="the spoon in the teacup",
        phrase="a spoon left in a teacup",
        place="the bedside table",
        sound="ting-ting came from the cup",
        percussion_line="A spoon trembled against the side of the teacup whenever the heater gave a small shiver through the floor.",
        active_weathers={"cold"},
        required_fix="remove_spoon",
        tags={"cup", "spoon", "cold"},
    ),
    "shell_mobile": TapSource(
        id="shell_mobile",
        label="the shell mobile",
        phrase="a shell mobile by the curtain",
        place="the curtain rod",
        sound="tik-tik-tik came from the hanging shells",
        percussion_line="The little shells were touching one another in the breeze and clicking softly like tiny bedtime bells.",
        active_weathers={"windy"},
        required_fix="move_mobile",
        tags={"mobile", "wind"},
    ),
}

SNACKS = {
    "milk": Snack(
        id="milk",
        label="warm milk",
        phrase="a small mug of warm milk",
        digestion_level=2,
        belly_line="Then came a polite little glug from the child's tummy, as if the warm milk were still finding its sleepy place.",
        tags={"milk", "digestion"},
    ),
    "apple": Snack(
        id="apple",
        label="apple slices",
        phrase="a plate of apple slices",
        digestion_level=1,
        belly_line="A soft burble answered from the child's tummy, the sort of sound an apple makes on its slow way to being digested.",
        tags={"apple", "digestion"},
    ),
    "porridge": Snack(
        id="porridge",
        label="porridge",
        phrase="a warm bowl of porridge with cinnamon",
        digestion_level=2,
        belly_line="From inside came a round little blurp, because the porridge was still settling into a cozy, sleepy digestion.",
        tags={"porridge", "digestion"},
    ),
    "water": Snack(
        id="water",
        label="water",
        phrase="a little glass of water",
        digestion_level=0,
        belly_line="",
        tags={"water"},
    ),
}

FIXES = {
    "tie_branch": Fix(
        id="tie_branch",
        label="tie the branch back",
        sense=3,
        action_text="looped a ribbon around the branch and tied it gently away from the glass",
        qa_text="tied the branch back so it could not tap the window",
        tags={"branch", "quiet"},
    ),
    "set_bowl": Fix(
        id="set_bowl",
        label="set a bowl under the drip",
        sense=3,
        action_text="set a little bowl under the drip so the stone would no longer make the plinking sound",
        qa_text="set a bowl under the drip so the plink would stop",
        tags={"rain", "quiet"},
    ),
    "remove_spoon": Fix(
        id="remove_spoon",
        label="remove the spoon",
        sense=3,
        action_text="lifted the spoon from the teacup and laid it on a folded cloth",
        qa_text="removed the spoon from the teacup so it could not ting against the cup",
        tags={"cup", "quiet"},
    ),
    "move_mobile": Fix(
        id="move_mobile",
        label="move the mobile",
        sense=3,
        action_text="moved the shell mobile away from the curtain where the breeze could not reach it",
        qa_text="moved the shell mobile away from the breeze",
        tags={"mobile", "quiet"},
    ),
    "shake_blanket": Fix(
        id="shake_blanket",
        label="shake the blanket",
        sense=1,
        action_text="shook the blanket hard",
        qa_text="shook the blanket",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Lily", "Ella", "Zoe", "Ava", "Lucy", "Anna"]
BOY_NAMES = ["Theo", "Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli"]
COMFORTS = ["a plush fox", "a floppy rabbit", "a little bear", "a moon pillow"]


KNOWLEDGE = {
    "percussion": [
        (
            "What is percussion?",
            "Percussion is music made by tapping, shaking, or striking something so it makes a beat. A tiny tap on glass or a little plink in a cup can sound like gentle percussion."
        )
    ],
    "digestion": [
        (
            "What is digestion?",
            "Digestion is the work your body does to turn food into energy your body can use. Sometimes that work makes small tummy sounds, especially when things are settling after a snack."
        )
    ],
    "wind": [
        (
            "Why can wind make tapping sounds at night?",
            "Wind can move branches, curtains, and hanging things until they touch something else. When they bump again and again, they can make a little repeating sound."
        )
    ],
    "rain": [
        (
            "Why do drips sound louder at night?",
            "At night a room is usually quieter, so small sounds stand out more. A drip landing in the same place over and over can seem very loud when everything else is still."
        )
    ],
    "mystery": [
        (
            "How do you solve a small mystery?",
            "You listen for clues, test good ideas, and keep only the ideas that fit what really happened. Calm thinking makes a mystery smaller."
        )
    ],
    "bedtime": [
        (
            "Why do little sounds seem bigger at bedtime?",
            "At bedtime there are fewer busy daytime noises around you. That makes tiny sounds easier to notice."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "bedtime", "percussion", "digestion", "wind", "rain"]


def explain_rejection(weather: Weather, source: TapSource, snack: Snack, fix: Optional[Fix] = None) -> str:
    if snack.digestion_level < 1:
        return (
            f"(No story: {snack.label} would not give this bedtime mystery an inside clue, "
            f"so the digestion part of the puzzle would be missing. Pick milk, apple, or porridge.)"
        )
    if not source_active_in_weather(source, weather):
        return (
            f"(No story: {source.label} does not make a tapping sound on a {weather.label} night. "
            f"Choose weather that can really trigger that sound.)"
        )
    if fix is not None and not fix_matches(source, fix):
        return (
            f"(No story: {fix.label} does not sensibly solve the sound from {source.label}. "
            f"Pick the fix that matches the real source.)"
        )
    return "(No story: this bedtime mystery does not fit the world's common-sense rules.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    source = f["source_cfg"]
    snack = f["snack_cfg"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old about a child who hears a tiny percussion sound in the dark and whispers that there is a mystery to solve. Include the words "percussion", "eligible", and "digestion".',
        f"Tell a gentle night story where {child.id} and {child.pronoun('possessive')} {parent.label_word} make an eligible suspect list, discover that {source.label} is one clue, and learn that {snack.label} can make quiet digestion sounds too.",
        'Write a cozy mystery-to-solve bedtime story where a puzzling sound has two real causes, and the ending image shows the room calm enough for sleep.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    source = f["source_cfg"]
    snack = f["snack_cfg"]
    fix = f["fix_cfg"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {pw} at bedtime. Together they listen carefully and solve a small night mystery."
        ),
        (
            "What made the mystery feel real to the child?",
            f"There were two clues at once: {source.label} made a tiny tapping sound, and {child.id}'s tummy made a soft sound too. Because both happened in the quiet room, the mystery felt bigger than it really was."
        ),
        (
            "What was the eligible suspect list for?",
            f"The list helped them keep only ideas that could truly make a sound that night. It turned guessing into careful listening, which is how they began to solve the mystery."
        ),
        (
            "What did the grown-up explain about digestion?",
            f"{parent.pronoun().capitalize()} explained that digestion is the body's work of turning food into strength, and that work can make little tummy glugs. That helped {child.id} understand that one of the clues was coming from inside, not from something scary outside."
        ),
        (
            "How did they stop the tapping sound?",
            f"{pw.capitalize()} {fix.qa_text}. Once the real source was handled, the room became quiet right away."
        ),
        (
            "How did the story end?",
            f"{child.id} went back to bed understanding both clues. The mystery was solved, the room was calm, and sleep finally felt easy."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "bedtime", "percussion", "digestion"}
    tags |= set(f["weather"].tags)
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


CURATED = [
    StoryParams(
        weather="windy",
        source="branch_window",
        snack="milk",
        fix="tie_branch",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        comfort="a plush fox",
    ),
    StoryParams(
        weather="rainy",
        source="gutter_drip",
        snack="apple",
        fix="set_bowl",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        comfort="a little bear",
    ),
    StoryParams(
        weather="cold",
        source="teacup_spoon",
        snack="porridge",
        fix="remove_spoon",
        child_name="Mia",
        child_gender="girl",
        parent="mother",
        comfort="a moon pillow",
    ),
    StoryParams(
        weather="windy",
        source="shell_mobile",
        snack="milk",
        fix="move_mobile",
        child_name="Leo",
        child_gender="boy",
        parent="father",
        comfort="a floppy rabbit",
    ),
]


ASP_RULES = r"""
active_source(W,S) :- weather(W), source(S), active_in(S,W).
noisy_snack(K) :- snack(K), digestion_level(K,D), D >= 1.
sensible_fix(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
matches(S,F) :- required_fix(S,F), sensible_fix(F).

valid(W,S,K,F) :- weather(W), source(S), snack(K), fix(F),
                  active_source(W,S), noisy_snack(K), matches(S,F).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for wid in WEATHER:
        lines.append(asp.fact("weather", wid))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        for wid in sorted(source.active_weathers):
            lines.append(asp.fact("active_in", sid, wid))
        lines.append(asp.fact("required_fix", sid, source.required_fix))
    for kid, snack in SNACKS.items():
        lines.append(asp.fact("snack", kid))
        lines.append(asp.fact("digestion_level", kid, snack.digestion_level))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "percussion" not in sample.story or "eligible" not in sample.story or "digestion" not in sample.story:
            raise StoryError("smoke test story missing required story words")
        print("OK: smoke generation succeeded on curated sample.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"FAIL: smoke generation crashed: {err}")

    try:
        parser = build_parser()
        params = resolve_params(parser.parse_args([]), random.Random(123))
        sample = generate(params)
        if not sample.story:
            raise StoryError("resolved default params produced empty story")
        print("OK: default resolve/generate smoke test succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"FAIL: default resolve/generate crashed: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime mystery with a tiny tapping sound and a tummy clue."
    )
    ap.add_argument("--weather", choices=WEATHER)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible parameter combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.weather and args.source:
        weather = WEATHER[args.weather]
        source = SOURCES[args.source]
        if not source_active_in_weather(source, weather):
            snack = SNACKS[args.snack] if args.snack else next(v for v in SNACKS.values() if v.digestion_level >= 1)
            raise StoryError(explain_rejection(weather, source, snack))
    if args.snack and SNACKS[args.snack].digestion_level < 1:
        weather = WEATHER[args.weather] if args.weather else next(iter(WEATHER.values()))
        source = SOURCES[args.source] if args.source else next(iter(SOURCES.values()))
        raise StoryError(explain_rejection(weather, source, SNACKS[args.snack]))
    if args.source and args.fix:
        source = SOURCES[args.source]
        fix = FIXES[args.fix]
        weather = WEATHER[args.weather] if args.weather else WEATHER[next(iter(source.active_weathers))]
        snack = SNACKS[args.snack] if args.snack else next(v for v in SNACKS.values() if v.digestion_level >= 1)
        if not fix_matches(source, fix):
            raise StoryError(explain_rejection(weather, source, snack, fix))

    combos = [
        c for c in valid_combos()
        if (args.weather is None or c[0] == args.weather)
        and (args.source is None or c[1] == args.source)
        and (args.snack is None or c[2] == args.snack)
        and (args.fix is None or c[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    weather_id, source_id, snack_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    parent = args.parent or rng.choice(["mother", "father"])
    comfort = rng.choice(COMFORTS)
    return StoryParams(
        weather=weather_id,
        source=source_id,
        snack=snack_id,
        fix=fix_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
        comfort=comfort,
    )


def generate(params: StoryParams) -> StorySample:
    if params.weather not in WEATHER:
        raise StoryError(f"Unknown weather: {params.weather}")
    if params.source not in SOURCES:
        raise StoryError(f"Unknown source: {params.source}")
    if params.snack not in SNACKS:
        raise StoryError(f"Unknown snack: {params.snack}")
    if params.fix not in FIXES:
        raise StoryError(f"Unknown fix: {params.fix}")

    weather = WEATHER[params.weather]
    source = SOURCES[params.source]
    snack = SNACKS[params.snack]
    fix = FIXES[params.fix]

    if snack.digestion_level < 1:
        raise StoryError(explain_rejection(weather, source, snack))
    if not source_active_in_weather(source, weather):
        raise StoryError(explain_rejection(weather, source, snack))
    if not fix_matches(source, fix):
        raise StoryError(explain_rejection(weather, source, snack, fix))

    world = tell(
        weather=weather,
        source_cfg=source,
        snack_cfg=snack,
        fix_cfg=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        comfort=params.comfort,
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (weather, source, snack, fix) combos:\n")
        for weather, source, snack, fix in combos:
            print(f"  {weather:6} {source:14} {snack:8} {fix}")
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
            header = f"### {p.child_name}: {p.source} on a {p.weather} night ({p.snack}, {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
