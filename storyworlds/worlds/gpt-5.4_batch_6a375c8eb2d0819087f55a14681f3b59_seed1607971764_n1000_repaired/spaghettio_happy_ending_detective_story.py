#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spaghettio_happy_ending_detective_story.py
=====================================================================

A standalone story world for a tiny child-facing detective story with a happy
ending. A child notices that a warm lunch of spaghettios is missing, spots one
small clue, and solves the case the sensible way.

The world model tracks:
- typed entities with physical meters and emotional memes
- a clue left by a harmless cause
- a detective method that may or may not fit the clue
- a recovered lunch and a mended feeling at the end

Run it
------
    python storyworlds/worlds/gpt-5.4/spaghettio_happy_ending_detective_story.py
    python storyworlds/worlds/gpt-5.4/spaghettio_happy_ending_detective_story.py --case lunchbox --cause puppy
    python storyworlds/worlds/gpt-5.4/spaghettio_happy_ending_detective_story.py --clue cooler_tag
    python storyworlds/worlds/gpt-5.4/spaghettio_happy_ending_detective_story.py --method accuse
    python storyworlds/worlds/gpt-5.4/spaghettio_happy_ending_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/spaghettio_happy_ending_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/spaghettio_happy_ending_detective_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        animal = {"puppy", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
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
class CaseFile:
    id: str
    title: str
    meal: str
    vessel: str
    opening_place: str
    hiding_place: str
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
class Cause:
    id: str
    actor_type: str
    actor_label: str
    actor_role: str
    motive: str
    moved_to: str
    kindness: str
    leaves: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    noun: str
    phrase: str
    place_text: str
    points_to: set[str] = field(default_factory=set)
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
class Method:
    id: str
    sense: int
    kind: str
    line: str
    solve_text: str
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


def _r_worry(world: World) -> list[str]:
    detective = world.get("detective")
    lunch = world.get("lunch")
    if lunch.attrs.get("missing") and detective.memes["confusion"] >= THRESHOLD:
        sig = ("worry", detective.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["worry"] += 1
    return []


def _r_clue_confidence(world: World) -> list[str]:
    detective = world.get("detective")
    clue = world.get("clue")
    if clue.attrs.get("found") and detective.memes["curiosity"] >= THRESHOLD:
        sig = ("confidence", detective.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["hope"] += 1
    return []


def _r_recovery_relief(world: World) -> list[str]:
    detective = world.get("detective")
    lunch = world.get("lunch")
    if lunch.attrs.get("found"):
        sig = ("relief", detective.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["relief"] += 1
            detective.memes["worry"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="clue_confidence", tag="emotional", apply=_r_clue_confidence),
    Rule(name="recovery_relief", tag="emotional", apply=_r_recovery_relief),
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


def clue_matches(cause: Cause, clue: Clue) -> bool:
    return clue.id in cause.leaves and cause.id in clue.points_to


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def method_works(cause: Cause, clue: Clue, method: Method) -> bool:
    if method.sense < SENSE_MIN:
        return False
    if not clue_matches(cause, clue):
        return False
    if method.kind == "follow":
        return clue.id in {"spaghettio", "paw_print", "ribbon"}
    if method.kind == "ask":
        return clue.id in {"crayon_note", "cooler_tag"}
    if method.kind == "check":
        return clue.id == "cooler_tag"
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for case_id in CASES:
        for cause_id, cause in CAUSES.items():
            for clue_id, clue in CLUES.items():
                for method_id, method in METHODS.items():
                    if clue_matches(cause, clue) and method_works(cause, clue, method):
                        out.append((case_id, cause_id, clue_id, method_id))
    return sorted(out)


def explain_clue_rejection(cause: Cause, clue: Clue) -> str:
    return (
        f"(No story: {clue.phrase} does not fit this case. "
        f"{cause.actor_label.capitalize()} would not leave that clue, so the detective "
        f"would have no honest trail to follow.)"
    )


def explain_method_rejection(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). A child detective should solve the case "
        f"by noticing clues and asking kindly. Try: {better}.)"
    )


def explain_combo_rejection(cause: Cause, clue: Clue, method: Method) -> str:
    if not clue_matches(cause, clue):
        return explain_clue_rejection(cause, clue)
    if not method_works(cause, clue, method):
        return (
            f"(No story: {method.id} does not fit {clue.phrase}. "
            f"The chosen clue would not honestly lead to the missing lunch that way.)"
        )
    return "(No valid combination matches the given options.)"


def predict_solution(world: World, clue_id: str, method_id: str) -> dict:
    sim = world.copy()
    clue = sim.get("clue")
    clue.attrs["found"] = True
    detective = sim.get("detective")
    detective.memes["curiosity"] += 1
    propagate(sim, narrate=False)
    works = method_works(sim.facts["cause_cfg"], CLUES[clue_id], METHODS[method_id])
    return {"works": works, "hope": detective.memes["hope"]}


def establish_case(world: World, detective: Entity, case_cfg: CaseFile, lunch: Entity) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"After school, {detective.id} padded into the kitchen and stopped short. "
        f"On the table sat an empty space where {detective.pronoun('possessive')} "
        f"{case_cfg.vessel} of {case_cfg.meal} should have been."
    )
    world.say(
        f'{detective.pronoun().capitalize()} narrowed {detective.pronoun("possessive")} eyes. '
        f'"This is {case_cfg.title}," {detective.pronoun()} whispered. '
        f'The case of the missing lunch had begun.'
    )
    lunch.attrs["missing"] = True
    detective.memes["confusion"] += 1
    propagate(world)


def inspect_scene(world: World, detective: Entity, clue_cfg: Clue) -> None:
    clue = world.get("clue")
    clue.attrs["found"] = True
    detective.memes["curiosity"] += 1
    propagate(world)
    world.say(
        f"{detective.id} looked carefully around {world.facts['case_cfg'].opening_place}. "
        f"There, {clue_cfg.place_text}, was {clue_cfg.phrase}."
    )
    world.say(
        f'"A clue," {detective.pronoun()} murmured. "{clue_cfg.noun.capitalize()} never lie."'
    )


def announce_method(world: World, detective: Entity, method: Method) -> None:
    pred = predict_solution(world, world.facts["clue_cfg"].id, method.id)
    world.facts["predicted_success"] = pred["works"]
    line = method.line
    if pred["hope"] >= THRESHOLD:
        line += " The clue made the plan feel possible."
    world.say(f'{detective.id} tapped {detective.pronoun("possessive")} chin. "{line}"')


def solve_case(world: World, detective: Entity, helper: Entity, lunch: Entity,
               case_cfg: CaseFile, cause: Cause, clue: Clue, method: Method) -> None:
    lunch.attrs["missing"] = False
    lunch.attrs["found"] = True
    lunch.meters["warmth"] += 1
    helper.memes["kindness"] += 1
    detective.memes["trust"] += 1
    world.facts["found_place"] = cause.moved_to
    if cause.id == "puppy":
        world.say(
            f"{detective.id} followed the tiny trail to {cause.moved_to}. "
            f"There sat {helper.label}, wagging hard beside the {case_cfg.vessel}."
        )
        world.say(
            f"{helper.label.capitalize()} had nosed it there because {cause.motive}. "
            f"He had not eaten the lunch at all. One lonely spaghettio had slipped onto the floor and given the whole game away."
        )
    elif cause.id == "sister":
        world.say(
            f"{detective.id} followed the clue to {cause.moved_to}. "
            f"There sat {helper.label} with two dolls, the {case_cfg.vessel} resting in the middle like a grand feast."
        )
        world.say(
            f"{helper.label.capitalize()} looked up and explained that {cause.motive}. "
            f"She had meant to set a surprise table, not steal anything."
        )
    else:
        world.say(
            f"{detective.id} checked {cause.moved_to}. "
            f"Inside was the missing {case_cfg.vessel}, tucked safely where it would stay warm."
        )
        world.say(
            f"{helper.label.capitalize()} smiled and explained that {cause.motive}. "
            f"The lunch had been protected, not lost."
        )
    world.say(method.solve_text.format(actor=helper.label, place=cause.moved_to))
    detective.memes["joy"] += 1
    propagate(world)


def make_amends(world: World, detective: Entity, helper: Entity, case_cfg: CaseFile, cause: Cause) -> None:
    detective.memes["warmth"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f"{detective.id} let out a long breath and smiled. {cause.kindness}"
    )
    if cause.id == "puppy":
        world.say(
            f"{detective.id} scratched {helper.label} behind the ears and set one safe noodle in a bowl nearby, then carried the lunch back for the real meal."
        )
    elif cause.id == "sister":
        world.say(
            f"{detective.id} invited {helper.label} to help carry spoons, and the pretend tea party turned into a real little lunch."
        )
    else:
        world.say(
            f"{detective.id} helped {helper.label} open the cooler, and together they set the lunch out with a pleased little flourish."
        )
    world.say(case_cfg.ending_image)


def tell(case_cfg: CaseFile, cause: Cause, clue_cfg: Clue, method: Method,
         detective_name: str = "Mina", detective_type: str = "girl",
         helper_name: str = "Pip", parent_type: str = "mother") -> World:
    world = World()

    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=detective_type,
        label=detective_name,
        role="detective",
        attrs={"name": detective_name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=cause.actor_type,
        label=helper_name if cause.actor_type == "puppy" else helper_name,
        role=cause.actor_role,
        attrs={"name": helper_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    lunch = world.add(Entity(
        id="lunch",
        kind="thing",
        type="lunch",
        label=case_cfg.vessel,
        owner=detective_name,
        attrs={"missing": False, "found": False},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue_cfg.noun,
        attrs={"found": False},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="place",
        label=case_cfg.opening_place,
    ))

    detective.memes["curiosity"] = 1.0
    detective.memes["confusion"] = 0.0
    detective.memes["worry"] = 0.0
    detective.memes["hope"] = 0.0
    detective.memes["joy"] = 0.0
    helper.memes["kindness"] = 0.0
    helper.memes["warmth"] = 0.0
    lunch.meters["warmth"] = 0.0

    world.facts.update(
        case_cfg=case_cfg,
        cause_cfg=cause,
        clue_cfg=clue_cfg,
        method_cfg=method,
        detective=detective,
        helper=helper,
        parent=parent,
        lunch=lunch,
    )

    establish_case(world, detective, case_cfg, lunch)
    world.para()
    inspect_scene(world, detective, clue_cfg)
    announce_method(world, detective, method)
    world.para()
    solve_case(world, detective, helper, lunch, case_cfg, cause, clue_cfg, method)
    make_amends(world, detective, helper, case_cfg, cause)
    world.facts["outcome"] = "solved"
    return world


CASES = {
    "lunchbox": CaseFile(
        id="lunchbox",
        title="Case Number One: The Missing Lunchbox",
        meal="spaghettios",
        vessel="little red lunchbox",
        opening_place="the kitchen table",
        hiding_place="a safe place nearby",
        ending_image="Soon the little red lunchbox was open on the table again, and the kitchen no longer looked like a mystery at all. It looked like lunchtime.",
        tags={"lunch", "detective", "happy"},
    ),
    "thermos": CaseFile(
        id="thermos",
        title="Case Number Two: The Vanished Thermos",
        meal="warm spaghettios",
        vessel="silver thermos",
        opening_place="the breakfast counter",
        hiding_place="a tucked-away warm place",
        ending_image="At the end, the silver thermos gleamed in the light, and everyone sat down together with the case cheerfully closed.",
        tags={"lunch", "detective", "happy"},
    ),
}

CAUSES = {
    "puppy": Cause(
        id="puppy",
        actor_type="puppy",
        actor_label="the puppy",
        actor_role="pet",
        motive="the puppy had smelled the tomato sauce and carried the lunchbox to his blanket so he could guard it",
        moved_to="the hall rug by the shoe basket",
        kindness="Nobody had been naughty. The helper had only tried to take care of something that smelled important.",
        leaves={"spaghettio", "paw_print"},
        tags={"pet", "trail"},
    ),
    "sister": Cause(
        id="sister",
        actor_type="girl",
        actor_label="little sister",
        actor_role="sibling",
        motive="little sister wanted to make a pretend café and thought the lunchbox looked exactly right for the middle of the doll table",
        moved_to="the playroom under the paper lanterns",
        kindness="It turned out to be a misunderstanding, and misunderstandings can be mended with gentle words.",
        leaves={"spaghettio", "ribbon", "crayon_note"},
        tags={"family", "play"},
    ),
    "parent": Cause(
        id="parent",
        actor_type="mother",
        actor_label="mom",
        actor_role="parent",
        motive="mom had tucked it into the picnic cooler early so it would stay warm for later",
        moved_to="the blue cooler by the back door",
        kindness="The missing lunch had really been a careful surprise.",
        leaves={"cooler_tag", "crayon_note"},
        tags={"family", "care"},
    ),
}

CLUES = {
    "spaghettio": Clue(
        id="spaghettio",
        noun="spaghettio",
        phrase="one small orange spaghettio",
        place_text="under the table leg",
        points_to={"puppy", "sister"},
        tags={"food", "trail"},
    ),
    "paw_print": Clue(
        id="paw_print",
        noun="paw print",
        phrase="a tiny saucey paw print",
        place_text="near the doorway",
        points_to={"puppy"},
        tags={"pet", "trail"},
    ),
    "ribbon": Clue(
        id="ribbon",
        noun="ribbon",
        phrase="a pink ribbon from the doll basket",
        place_text="on the chair",
        points_to={"sister"},
        tags={"play", "trail"},
    ),
    "crayon_note": Clue(
        id="crayon_note",
        noun="crayon note",
        phrase='a crayon note that said "For later!"',
        place_text="beside the fruit bowl",
        points_to={"sister", "parent"},
        tags={"writing", "family"},
    ),
    "cooler_tag": Clue(
        id="cooler_tag",
        noun="cooler tag",
        phrase="the blue cooler tag peeking from behind the curtain",
        place_text="by the back hallway",
        points_to={"parent"},
        tags={"cooler", "check"},
    ),
}

METHODS = {
    "follow": Method(
        id="follow",
        sense=3,
        kind="follow",
        line="I will follow the clue very slowly and see where it leads.",
        solve_text="Step by step, the clue led straight to {place}, where the mystery waited in plain sight.",
        fail_text="The detective rushed after the wrong thing and learned nothing at all.",
        qa_text="The detective followed the clue carefully until it led to the missing lunch.",
        tags={"observe", "trail"},
    ),
    "ask": Method(
        id="ask",
        sense=3,
        kind="ask",
        line="I will ask kindly before I guess. Good detectives use calm voices.",
        solve_text="{actor.capitalize()} answered the gentle question, and the truth came out at once.",
        fail_text="A sharp guess only hurt feelings and hid the truth.",
        qa_text="The detective asked kindly, and the helper explained where the lunch had gone.",
        tags={"kind", "talk"},
    ),
    "check": Method(
        id="check",
        sense=2,
        kind="check",
        line="I should check the sensible place that fits this clue.",
        solve_text="That careful check worked, because the clue matched the safe place exactly.",
        fail_text="Checking a silly place would only waste time.",
        qa_text="The detective checked the most sensible place for the clue and found the lunch there.",
        tags={"observe", "logic"},
    ),
    "accuse": Method(
        id="accuse",
        sense=1,
        kind="accuse",
        line="I will point at someone right away and say they did it.",
        solve_text="Nobody should solve a case by blaming first.",
        fail_text="Blaming first is not fair and does not make a good detective.",
        qa_text="The detective should not accuse people without evidence.",
        tags={"unkind"},
    ),
}


GIRL_NAMES = ["Mina", "Nora", "Ava", "Lulu", "Ivy", "Rosa"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Toby", "Finn", "Eli"]
HELPER_NAMES = ["Pip", "Dot", "June", "Max", "Sunny", "Kit"]


@dataclass
class StoryParams:
    case: str
    cause: str
    clue: str
    method: str
    detective_name: str
    detective_type: str
    helper_name: str
    parent_type: str
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
    "detective": [
        (
            "What does a detective do?",
            "A detective looks carefully, notices clues, and asks good questions. A good detective does not guess wildly first.",
        )
    ],
    "spaghettio": [
        (
            "What is a spaghettio?",
            "A spaghettio is one small ring of pasta in tomato sauce. Many spaghettios together make a soft, saucy meal.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. It can point you toward what happened next.",
        )
    ],
    "puppy": [
        (
            "Why do puppies carry things away?",
            "Puppies often carry things because they are curious or because a smell interests them. They do not always understand what belongs on the table.",
        )
    ],
    "cooler": [
        (
            "What is a cooler for?",
            "A cooler is a box that helps keep food at the right temperature. Families use it to carry or protect meals.",
        )
    ],
    "kind": [
        (
            "Why is it better to ask kindly than to accuse?",
            "A kind question helps people tell the truth without feeling scared. Blaming first can hurt feelings and make a problem harder to solve.",
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "spaghettio", "clue", "puppy", "cooler", "kind"]


CURATED = [
    StoryParams(
        case="lunchbox",
        cause="puppy",
        clue="spaghettio",
        method="follow",
        detective_name="Mina",
        detective_type="girl",
        helper_name="Pip",
        parent_type="mother",
    ),
    StoryParams(
        case="lunchbox",
        cause="sister",
        clue="ribbon",
        method="follow",
        detective_name="Owen",
        detective_type="boy",
        helper_name="June",
        parent_type="father",
    ),
    StoryParams(
        case="thermos",
        cause="parent",
        clue="cooler_tag",
        method="check",
        detective_name="Nora",
        detective_type="girl",
        helper_name="Mom",
        parent_type="mother",
    ),
    StoryParams(
        case="thermos",
        cause="parent",
        clue="crayon_note",
        method="ask",
        detective_name="Milo",
        detective_type="boy",
        helper_name="Mom",
        parent_type="mother",
    ),
]


def outcome_of(params: StoryParams) -> str:
    if params.case not in CASES or params.cause not in CAUSES or params.clue not in CLUES or params.method not in METHODS:
        return "invalid"
    cause = CAUSES[params.cause]
    clue = CLUES[params.clue]
    method = METHODS[params.method]
    if clue_matches(cause, clue) and method_works(cause, clue, method):
        return "solved"
    return "invalid"


def generation_prompts(world: World) -> list[str]:
    case_cfg = world.facts["case_cfg"]
    detective = world.facts["detective"]
    helper = world.facts["helper"]
    clue = world.facts["clue_cfg"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old about a missing lunch of {case_cfg.meal}. Include the word "{clue.noun}".',
        f"Tell a happy detective story where {detective.attrs['name']} solves the mystery of a missing {case_cfg.vessel} by noticing {clue.phrase} and speaking kindly.",
        f"Write a simple case-of-the-missing-lunch story with a harmless twist, a clear clue, and a warm ending involving {helper.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    detective = world.facts["detective"]
    helper = world.facts["helper"]
    case_cfg = world.facts["case_cfg"]
    clue = world.facts["clue_cfg"]
    cause = world.facts["cause_cfg"]
    method = world.facts["method_cfg"]
    found_place = world.facts.get("found_place", cause.moved_to)
    qas = [
        (
            "Who is the story about?",
            f"It is about {detective.attrs['name']}, who acted like a little detective when {detective.pronoun('possessive')} {case_cfg.vessel} of {case_cfg.meal} went missing. The case stayed gentle because the mystery was about finding lunch, not catching a villain.",
        ),
        (
            "What clue started the case?",
            f"The first clue was {clue.phrase}. It mattered because that clue honestly pointed toward where the missing lunch had gone.",
        ),
        (
            "How did the detective solve the mystery?",
            f"{method.qa_text} That worked because the clue matched the true path of the missing {case_cfg.vessel}.",
        ),
        (
            "Why was the lunch missing?",
            f"It was missing because {cause.motive}. The lunch was moved for a harmless reason, so the mystery ended in relief instead of trouble.",
        ),
        (
            "Where did they find the lunch?",
            f"They found it at {found_place}. Finding it there proved that the clue had been telling the truth all along.",
        ),
        (
            "Why is this a happy ending?",
            f"It is a happy ending because the lunch was safe, nobody had meant any harm, and the detective learned the truth without being unkind. At the end, everyone could smile and eat together.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "spaghettio", "clue", "kind"}
    if world.facts["cause_cfg"].id == "puppy":
        tags.add("puppy")
    if world.facts["clue_cfg"].id == "cooler_tag" or world.facts["cause_cfg"].id == "parent":
        tags.add("cooler")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
match_cause_clue(Cause, Clue) :- leaves(Cause, Clue), points_to(Clue, Cause).
sensible(Method) :- method(Method), sense(Method, S), sense_min(M), S >= M.

works_with(Clue, follow) :- clue(Clue), trail_clue(Clue).
works_with(Clue, ask)    :- clue(Clue), ask_clue(Clue).
works_with(cooler_tag, check).

valid(Case, Cause, Clue, Method) :-
    case(Case), cause(Cause), clue(Clue), method(Method),
    match_cause_clue(Cause, Clue),
    sensible(Method),
    works_with(Clue, Method).

% --- outcome for one chosen scenario ---------------------------------------
solved :- chosen_case(Case), chosen_cause(Cause), chosen_clue(Clue), chosen_method(Method),
          valid(Case, Cause, Clue, Method).
outcome(solved) :- solved.
outcome(invalid) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for case_id in CASES:
        lines.append(asp.fact("case", case_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for clue_id in sorted(cause.leaves):
            lines.append(asp.fact("leaves", cause_id, clue_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for cause_id in sorted(clue.points_to):
            lines.append(asp.fact("points_to", clue_id, cause_id))
        if clue_id in {"spaghettio", "paw_print", "ribbon"}:
            lines.append(asp.fact("trail_clue", clue_id))
        if clue_id in {"crayon_note", "cooler_tag"}:
            lines.append(asp.fact("ask_clue", clue_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_case", params.case),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child detective solves the case of missing spaghettios with a happy ending."
    )
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(args.method))
    if args.cause and args.clue:
        if not clue_matches(CAUSES[args.cause], CLUES[args.clue]):
            raise StoryError(explain_clue_rejection(CAUSES[args.cause], CLUES[args.clue]))
    if args.cause and args.clue and args.method:
        if not method_works(CAUSES[args.cause], CLUES[args.clue], METHODS[args.method]):
            raise StoryError(explain_combo_rejection(CAUSES[args.cause], CLUES[args.clue], METHODS[args.method]))

    combos = [
        combo for combo in valid_combos()
        if (args.case is None or combo[0] == args.case)
        and (args.cause is None or combo[1] == args.cause)
        and (args.clue is None or combo[2] == args.clue)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    case_id, cause_id, clue_id, method_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    detective_name = args.name or rng.choice(name_pool)
    cause = CAUSES[cause_id]
    if cause.actor_type == "puppy":
        helper_name = rng.choice(["Pip", "Scout", "Biscuit", "Dot"])
    elif cause.id == "parent":
        helper_name = "Mom" if (args.parent or "mother") == "mother" else "Dad"
    else:
        helper_name = rng.choice(HELPER_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    if cause.id == "parent":
        helper_name = "Mom" if parent_type == "mother" else "Dad"
    return StoryParams(
        case=case_id,
        cause=cause_id,
        clue=clue_id,
        method=method_id,
        detective_name=detective_name,
        detective_type=gender,
        helper_name=helper_name,
        parent_type=parent_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES:
        raise StoryError(f"(Unknown case: {params.case})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    case_cfg = CASES[params.case]
    cause = CAUSES[params.cause]
    clue = CLUES[params.clue]
    method = METHODS[params.method]

    if not clue_matches(cause, clue):
        raise StoryError(explain_clue_rejection(cause, clue))
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(params.method))
    if not method_works(cause, clue, method):
        raise StoryError(explain_combo_rejection(cause, clue, method))

    world = tell(
        case_cfg=case_cfg,
        cause=cause,
        clue_cfg=clue,
        method=method,
        detective_name=params.detective_name,
        detective_type=params.detective_type,
        helper_name=params.helper_name,
        parent_type=params.parent_type,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos parity matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {m.id for m in sensible_methods()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible methods:")
        print("  python:", sorted(py_sensible))
        print("  clingo:", sorted(asp_sens))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome parity matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} scenario outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (case, cause, clue, method) combos:\n")
        for case_id, cause_id, clue_id, method_id in combos:
            print(f"  {case_id:9} {cause_id:7} {clue_id:11} {method_id}")
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
            header = f"### {p.detective_name}: {p.case} / {p.cause} / {p.clue} / {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
