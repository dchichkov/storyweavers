#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/acreage_objectionable_decide_repetition_bad_ending_moral.py
=======================================================================================

A standalone story world about a child mystery on a farm: a repeated strange sign
on the family's acreage leads two children to decide whether to follow an
objectionable shortcut or ask for honest help. Some choices end safely; some end
badly. Every story carries a clear moral about telling the truth and choosing the
kind way.

The world model tracks both physical state (distance, wetness, lostness, foundness)
and emotional state (curiosity, fear, guilt, trust). The prose is generated from
state and branching history rather than from a single frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/acreage_objectionable_decide_repetition_bad_ending_moral.py
    python storyworlds/worlds/gpt-5.4/acreage_objectionable_decide_repetition_bad_ending_moral.py --clue lantern --place orchard --choice ask_adult
    python storyworlds/worlds/gpt-5.4/acreage_objectionable_decide_repetition_bad_ending_moral.py --choice pry_shed
    python storyworlds/worlds/gpt-5.4/acreage_objectionable_decide_repetition_bad_ending_moral.py --all --qa
    python storyworlds/worlds/gpt-5.4/acreage_objectionable_decide_repetition_bad_ending_moral.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    locked: bool = False
    hidden: bool = False
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    mood: str
    danger: int
    hiding_spot: str
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
    mark: str
    repeated_line: str
    trail: str
    real_item: str
    hint_text: str
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
class Choice:
    id: str
    sense: int
    honest: bool
    safe: bool
    needs_tool: bool
    text: str
    success_text: str
    fail_text: str
    moral: str
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


def _r_lost(world: World) -> list[str]:
    out: list[str] = []
    for child in [e for e in world.entities.values() if e.role in ("solver", "friend")]:
        if child.meters["distance"] < 2 or child.meters["guided"] >= THRESHOLD:
            continue
        sig = ("lost", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.meters["lost"] += 1
        child.memes["fear"] += 1
        out.append("__lost__")
    return out


def _r_found(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("missing")
    if item.meters["found"] < THRESHOLD:
        return out
    for child in [e for e in world.entities.values() if e.role in ("solver", "friend")]:
        sig = ("relief", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["relief"] += 1
        child.memes["fear"] = 0.0
        out.append("__found__")
    return out


CAUSAL_RULES = [
    Rule(name="lost", tag="physical", apply=_r_lost),
    Rule(name="found", tag="emotional", apply=_r_found),
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


PLACES = {
    "orchard": Place(
        id="orchard",
        label="orchard",
        phrase="the old orchard at the edge of the family acreage",
        mood="Rows of trees made long green hallways, and every shadow looked as if it might be hiding a secret.",
        danger=1,
        hiding_spot="under a low apple branch",
        tags={"orchard", "farm"},
    ),
    "barn": Place(
        id="barn",
        label="barn",
        phrase="the red barn in the middle of the family acreage",
        mood="The rafters creaked softly, and dust floated like tiny ghosts in the slanting light.",
        danger=1,
        hiding_spot="behind a stack of hay bales",
        tags={"barn", "farm"},
    ),
    "marsh": Place(
        id="marsh",
        label="marsh",
        phrase="the marshy corner beyond the fence on the family acreage",
        mood="The reeds whispered together, and the ground looked soft in a way that made brave feet less sure.",
        danger=3,
        hiding_spot="beside a crooked post near the reeds",
        tags={"marsh", "farm", "mud"},
    ),
}

CLUES = {
    "lantern": Clue(
        id="lantern",
        mark="a chalk lantern",
        repeated_line='Again they saw the same mark: "a chalk lantern, a chalk lantern, a chalk lantern."',
        trail="small chalk lanterns on posts",
        real_item="Grandpa's brass lantern",
        hint_text="Someone had been leaving a picture of a lantern wherever the trail turned.",
        tags={"lantern", "chalk", "mystery"},
    ),
    "feather": Clue(
        id="feather",
        mark="a white feather tied with blue thread",
        repeated_line='Again they found the same sign: "a feather, a feather, a feather."',
        trail="white feathers tied to twigs",
        real_item="the silver whistle from the feed room",
        hint_text="The same feather kept appearing as if it wanted them to keep looking.",
        tags={"feather", "mystery"},
    ),
    "bell": Clue(
        id="bell",
        mark="a tiny bell drawn in mud",
        repeated_line='Again the sign returned: "a bell, a bell, a bell."',
        trail="little bell shapes pressed into the mud",
        real_item="Aunt May's hand bell",
        hint_text="Each bell shape pointed the way to the next corner.",
        tags={"bell", "mud", "mystery"},
    ),
}

CHOICES = {
    "ask_adult": Choice(
        id="ask_adult",
        sense=3,
        honest=True,
        safe=True,
        needs_tool=False,
        text="decide to ask a grown-up before going farther",
        success_text="Together they told the truth, and the grown-up understood the clue at once.",
        fail_text="",
        moral="It is brave to decide to ask for help when a mystery grows too big.",
        tags={"help", "truth", "safe"},
    ),
    "follow_path": Choice(
        id="follow_path",
        sense=2,
        honest=True,
        safe=True,
        needs_tool=False,
        text="decide to follow the marked path, but only where the ground is safe",
        success_text="They stayed on the open path and solved the mystery without hiding anything.",
        fail_text="",
        moral="Curiosity is good when it walks beside care.",
        tags={"path", "truth", "safe"},
    ),
    "pry_shed": Choice(
        id="pry_shed",
        sense=1,
        honest=False,
        safe=False,
        needs_tool=True,
        text="decide on an objectionable shortcut and pry open the locked shed",
        success_text="",
        fail_text="They chose an objectionable thing to do, and the mystery turned sour at once.",
        moral="A secret solved the wrong way can hurt trust.",
        tags={"shortcut", "locked", "bad"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Ella", "Ruth", "Ivy", "Lucy"]
BOY_NAMES = ["Owen", "Jude", "Cal", "Eli", "Noah", "Finn"]


def safe_choices() -> list[Choice]:
    return [c for c in CHOICES.values() if c.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for clue_id in CLUES:
            for choice_id, choice in CHOICES.items():
                if choice.id == "pry_shed":
                    combos.append((place_id, clue_id, choice_id))
                elif place.danger <= 2:
                    combos.append((place_id, clue_id, choice_id))
                elif choice.safe:
                    combos.append((place_id, clue_id, choice_id))
    return combos


def explain_choice(choice_id: str) -> str:
    choice = CHOICES[choice_id]
    if choice.sense >= SENSE_MIN:
        return ""
    return (
        f"(Warning: '{choice_id}' is known to this world, but it is objectionable and unsafe. "
        f"It remains available because some stories end badly, to teach the moral more clearly.)"
    )


def explain_rejection(place: Place, choice: Choice) -> str:
    return (
        f"(No story: {choice.id} does not fit {place.label}. That place is too risky for that plan, "
        f"so the children would not honestly choose it here.)"
    )


def predict_bad_end(place: Place, choice: Choice) -> bool:
    return (not choice.safe) or (place.danger >= 3 and choice.id != "ask_adult")


def choice_outcome(place: Place, choice: Choice) -> str:
    return "bad" if predict_bad_end(place, choice) else "good"


def predict_world(place: Place, clue: Clue, choice: Choice) -> dict:
    world = World()
    solver = world.add(Entity(id="A", kind="character", type="girl", role="solver"))
    friend = world.add(Entity(id="B", kind="character", type="boy", role="friend"))
    missing = world.add(Entity(id="missing", kind="thing", type="treasure", label=clue.real_item))
    world.facts["place"] = place
    world.facts["clue"] = clue
    world.facts["choice"] = choice
    if choice.id == "ask_adult":
        solver.meters["guided"] += 1
        friend.meters["guided"] += 1
        missing.meters["found"] += 1
    elif choice.id == "follow_path":
        solver.meters["distance"] += 1
        friend.meters["distance"] += 1
        if place.danger <= 1:
            missing.meters["found"] += 1
    else:
        solver.meters["distance"] += 3
        friend.meters["distance"] += 3
        solver.memes["guilt"] += 1
        friend.memes["guilt"] += 1
    propagate(world, narrate=False)
    return {
        "bad": predict_bad_end(place, choice),
        "lost": solver.meters["lost"] >= THRESHOLD or friend.meters["lost"] >= THRESHOLD,
        "found": missing.meters["found"] >= THRESHOLD,
    }


def opening(world: World, solver: Entity, friend: Entity, adult: Entity, place: Place, clue: Clue) -> None:
    solver.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"On a gray afternoon, {solver.id} and {friend.id} were helping on {adult.pronoun('possessive')} family's acreage "
        f"when they noticed something odd near {place.phrase}."
    )
    world.say(place.mood)
    world.say(
        f"On the first post they saw {clue.mark}. On the next gate they saw {clue.mark} again. "
        f"On the third turn they saw it yet again."
    )
    world.say(clue.repeated_line)
    world.say(clue.hint_text)


def wonder(world: World, solver: Entity, friend: Entity, clue: Clue) -> None:
    world.say(
        f'"Who keeps making these signs?" {solver.id} whispered. '
        f'"And what are they trying to show us?"'
    )
    world.say(
        f'{friend.id} looked down the trail of {clue.trail} and felt the mystery pull a little harder.'
    )


def decision(world: World, solver: Entity, friend: Entity, choice: Choice) -> None:
    solver.memes["resolve"] += 1
    friend.memes["resolve"] += 1
    world.say(
        f"They had to decide what to do next. After one quiet breath, they {choice.text}."
    )
    if choice.id == "pry_shed":
        world.say(
            'It sounded bold for half a second, but even saying it aloud made it feel objectionable.'
        )


def ask_adult_path(world: World, solver: Entity, friend: Entity, adult: Entity, clue: Clue, place: Place) -> None:
    solver.meters["guided"] += 1
    friend.meters["guided"] += 1
    world.say(
        f"They ran back to {adult.label_word} and told the whole truth about the repeated signs."
    )
    world.say(
        f'{adult.label_word.capitalize()} smiled, then laughed softly. "{clue.mark.capitalize()} means {clue.real_item}," '
        f'{adult.pronoun()} said. "{adult.pronoun("possessive").capitalize()} brother hid it {place.hiding_spot} for the harvest game."'
    )
    missing = world.get("missing")
    missing.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"With the grown-up beside them, they found {clue.real_item} {place.hiding_spot}. "
        f"The mystery felt bright now instead of heavy."
    )


def follow_path_path(world: World, solver: Entity, friend: Entity, place: Place, clue: Clue) -> None:
    solver.meters["distance"] += 1
    friend.meters["distance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They kept to the open path and followed the trail of {clue.trail}. "
        f"Every repeated sign made them more certain they were close."
    )
    missing = world.get("missing")
    if place.danger <= 1:
        missing.meters["found"] += 1
        propagate(world, narrate=False)
        world.say(
            f"At last they looked {place.hiding_spot} and found {clue.real_item}. "
            f"They had solved the mystery carefully, and there was nothing to hide."
        )
    else:
        world.say(
            f"But the ground grew soft and squishy, and the mystery stopped feeling playful."
        )
        solver.meters["distance"] += 2
        friend.meters["distance"] += 2
        propagate(world, narrate=False)


def pry_bad_path(world: World, solver: Entity, friend: Entity, adult: Entity, place: Place) -> None:
    solver.meters["distance"] += 3
    friend.meters["distance"] += 3
    solver.memes["guilt"] += 1
    friend.memes["guilt"] += 1
    world.get("shed").locked = False
    propagate(world, narrate=False)
    world.say(
        "They slipped a rusty rake under the latch and tugged. The shed door flew open with a bang so loud that every brave feeling vanished."
    )
    world.say(
        f"Inside there was no treasure at all, only frightened hens flapping dust into the air. "
        f"One bird darted out, and the children had to chase it across the wet edge of the {place.label}."
    )
    if place.id == "marsh":
        solver.meters["stuck"] += 1
        friend.meters["stuck"] += 1
        solver.memes["fear"] += 1
        friend.memes["fear"] += 1
        world.say(
            "The mud caught their boots. By the time a grown-up reached them, both children were muddy, crying, and too ashamed to speak at first."
        )
    else:
        world.say(
            f"{adult.label_word.capitalize()} came running at the noise. {adult.pronoun().capitalize()} saw the broken latch at once, and the mystery was forgotten under a hard, sad silence."
        )


def closing_good(world: World, solver: Entity, friend: Entity, choice: Choice) -> None:
    solver.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"That evening, the repeated marks no longer felt spooky. They felt like a lesson written kindly across the land."
    )
    world.say(
        f"{choice.moral} {solver.id} and {friend.id} remembered that a mystery can stay magical when people choose honesty first."
    )


def closing_bad(world: World, solver: Entity, friend: Entity, adult: Entity, choice: Choice) -> None:
    solver.memes["trust"] = 0.0
    friend.memes["trust"] = 0.0
    world.say(
        f"At supper, no one talked much. The broken latch, the mud, and the frightened hens sat in the room like another shadow."
    )
    world.say(
        f"{adult.label_word.capitalize()} was glad the children were safe, but sad that they had chosen an objectionable shortcut. "
        f"{choice.moral} After that, {solver.id} and {friend.id} knew that the wrong way to solve a mystery can make the ending feel small and dark."
    )


def tell(
    *,
    place: Place,
    clue: Clue,
    choice: Choice,
    solver_name: str,
    solver_gender: str,
    friend_name: str,
    friend_gender: str,
    adult_type: str,
) -> World:
    world = World()
    solver = world.add(Entity(id=solver_name, kind="character", type=solver_gender, role="solver"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    adult = world.add(Entity(id="Parent", kind="character", type=adult_type, role="adult", label="the parent"))
    missing = world.add(
        Entity(id="missing", kind="thing", type="treasure", label=clue.real_item, portable=True, hidden=True)
    )
    shed = world.add(Entity(id="shed", kind="thing", type="shed", label="the shed", locked=True))

    world.facts.update(
        place=place,
        clue=clue,
        choice=choice,
        solver=solver,
        friend=friend,
        adult=adult,
        missing=missing,
        repeated=3,
        bad_end=False,
        moral=choice.moral,
    )

    opening(world, solver, friend, adult, place, clue)
    world.para()
    wonder(world, solver, friend, clue)
    decision(world, solver, friend, choice)
    world.para()

    if choice.id == "ask_adult":
        ask_adult_path(world, solver, friend, adult, clue, place)
        world.para()
        closing_good(world, solver, friend, choice)
        world.facts["bad_end"] = False
    elif choice.id == "follow_path":
        follow_path_path(world, solver, friend, place, clue)
        world.para()
        if world.get("missing").meters["found"] >= THRESHOLD and solver.meters["lost"] < THRESHOLD:
            closing_good(world, solver, friend, choice)
            world.facts["bad_end"] = False
        else:
            world.say(
                "They had not broken anything, but they had gone too far and too late. A grown-up had to come find them with a lamp."
            )
            closing_bad(world, solver, friend, adult, Choice(
                id="follow_path_bad",
                sense=1,
                honest=True,
                safe=False,
                needs_tool=False,
                text="",
                success_text="",
                fail_text="",
                moral="Even a fair plan needs a careful stopping point.",
                tags={"bad"},
            ))
            world.facts["bad_end"] = True
            world.facts["moral"] = "Even a fair plan needs a careful stopping point."
    else:
        pry_bad_path(world, solver, friend, adult, place)
        world.para()
        closing_bad(world, solver, friend, adult, choice)
        world.facts["bad_end"] = True

    world.facts.update(
        found=world.get("missing").meters["found"] >= THRESHOLD,
        lost=solver.meters["lost"] >= THRESHOLD or friend.meters["lost"] >= THRESHOLD,
        guilt=solver.memes["guilt"] >= THRESHOLD or friend.memes["guilt"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "orchard": [(
        "What is an orchard?",
        "An orchard is a place where fruit trees grow in rows. People walk between the trees to pick or care for the fruit.",
    )],
    "barn": [(
        "What is a barn?",
        "A barn is a big farm building used for animals, hay, or tools. It can feel echoey and mysterious because it is large and dim.",
    )],
    "marsh": [(
        "Why can a marsh be dangerous?",
        "A marsh has soft, wet ground that can trap boots and make walking hard. That is why children should stay with a grown-up there.",
    )],
    "lantern": [(
        "What is a lantern?",
        "A lantern is a light people can carry from place to place. It helps them see in the dark.",
    )],
    "truth": [(
        "Why is telling the truth helpful in a problem?",
        "Telling the truth lets helpers understand what really happened. Honest words can solve trouble faster and keep people safe.",
    )],
    "locked": [(
        "Why should children not pry open a locked shed?",
        "A locked shed means children are supposed to stay out. Prying it open can break property, scare animals, and put children in danger.",
    )],
    "mystery": [(
        "What is a mystery?",
        "A mystery is something hidden or not understood yet. People look for clues to figure it out.",
    )],
}
KNOWLEDGE_ORDER = ["mystery", "orchard", "barn", "marsh", "lantern", "locked", "truth"]


@dataclass
class StoryParams:
    place: str
    clue: str
    choice: str
    solver_name: str
    solver_gender: str
    friend_name: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    solver = f["solver"]
    friend = f["friend"]
    place = f["place"]
    clue = f["clue"]
    choice = f["choice"]
    tone = "bad ending" if f.get("bad_end") else "moral mystery"
    return [
        f'Write a child-friendly mystery story set on family acreage that includes the words "acreage", "objectionable", and "decide".',
        f"Tell a mystery about {solver.id} and {friend.id} finding a repeated clue in the {place.label}, then having to decide what kind of choice to make.",
        f"Write a {tone} story where the repeated sign is {clue.mark}, and the children's choice is {choice.id}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    solver = f["solver"]
    friend = f["friend"]
    adult = f["adult"]
    place = f["place"]
    clue = f["clue"]
    choice = f["choice"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {solver.id} and {friend.id} on their family's acreage. They notice a repeated clue and try to solve a mystery together.",
        ),
        (
            "What was repeated in the story?",
            f"The same clue kept appearing again and again: {clue.mark}. The repetition made the place feel mysterious and told the children that the signs were connected.",
        ),
        (
            "What did the children have to decide?",
            f"They had to decide whether to solve the mystery the honest way or to take a shortcut. That choice changed whether the mystery ended safely or sadly.",
        ),
    ]
    if choice.id == "ask_adult":
        qa.append((
            f"How was the mystery solved?",
            f"They told {adult.label_word} the truth about the repeated signs. The grown-up understood the clue and led them to {clue.real_item}, so the mystery was solved safely.",
        ))
        qa.append((
            "What is the moral of this story?",
            f"{f['moral']} The happy ending came because the children chose honesty before pride.",
        ))
    elif choice.id == "follow_path" and not f.get("bad_end"):
        qa.append((
            "Why did the ending stay happy?",
            f"The children followed the clue carefully and stayed on safe ground. Because they did not hide anything or break rules, the mystery stayed exciting instead of becoming trouble.",
        ))
        qa.append((
            "What is the moral of this story?",
            f"{f['moral']} The careful choice mattered as much as the clue itself.",
        ))
    else:
        qa.append((
            "Why was the ending bad?",
            f"The children chose an objectionable shortcut or went too far without stopping. That choice brought fear, trouble, and hurt trust instead of a proud solution.",
        ))
        qa.append((
            "What did the children learn?",
            f"{f['moral']} They learned that solving a mystery the wrong way can leave everyone sad even if the children only meant to be brave.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"mystery"}
    tags |= set(f["place"].tags)
    tags |= set(f["clue"].tags)
    tags |= set(f["choice"].tags)
    if "safe" in tags or "truth" in tags or f["choice"].honest:
        tags.add("truth")
    if "locked" in tags:
        tags.add("locked")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.locked:
            bits.append("locked=True")
        if e.hidden:
            bits.append("hidden=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="orchard",
        clue="lantern",
        choice="ask_adult",
        solver_name="Mina",
        solver_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        adult="mother",
    ),
    StoryParams(
        place="barn",
        clue="feather",
        choice="follow_path",
        solver_name="Nora",
        solver_gender="girl",
        friend_name="Cal",
        friend_gender="boy",
        adult="father",
    ),
    StoryParams(
        place="marsh",
        clue="bell",
        choice="follow_path",
        solver_name="Ivy",
        solver_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        adult="mother",
    ),
    StoryParams(
        place="barn",
        clue="lantern",
        choice="pry_shed",
        solver_name="Ella",
        solver_gender="girl",
        friend_name="Jude",
        friend_gender="boy",
        adult="father",
    ),
]

ASP_RULES = r"""
safe_place(P)      :- place(P), danger(P,D), D <= 2.
risky_place(P)     :- place(P), danger(P,D), D >= 3.

bad_choice(C)      :- choice(C), safe(C,0).
good_choice(C)     :- choice(C), safe(C,1).

valid(P, Cl, C)    :- place(P), clue(Cl), choice(C), C = pry_shed.
valid(P, Cl, C)    :- place(P), clue(Cl), choice(C), C != pry_shed, safe_place(P).
valid(P, Cl, C)    :- place(P), clue(Cl), choice(C), safe(C,1).

outcome(bad)       :- chosen_place(P), chosen_choice(C), safe(C,0).
outcome(bad)       :- chosen_place(P), risky_place(P), chosen_choice(C), C != ask_adult.
outcome(good)      :- chosen_place(P), chosen_choice(C), not outcome(bad), place(P), choice(C).

sensible(C)        :- choice(C), sense(C,S), sense_min(M), S >= M.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("danger", pid, place.danger))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for chid, choice in CHOICES.items():
        lines.append(asp.fact("choice", chid))
        lines.append(asp.fact("sense", chid, choice.sense))
        lines.append(asp.fact("safe", chid, 1 if choice.safe else 0))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_choice", params.choice),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if params.place not in PLACES or params.choice not in CHOICES:
        raise StoryError("(Invalid params for outcome check.)")
    return choice_outcome(PLACES[params.place], CHOICES[params.choice])


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    ps = {c.id for c in safe_choices()}
    cs = set(asp_sensible())
    if ps == cs:
        print(f"OK: sensible choices match ({sorted(ps)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible choices: clingo={sorted(cs)} python={sorted(ps)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(25):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    mismatches = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery story world on a family farm acreage. Unspecified choices are random but valid."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.choice:
        place = PLACES[args.place]
        choice = CHOICES[args.choice]
        if (args.place, args.clue or next(iter(CLUES)), args.choice) not in valid_combos() and not (
            choice.safe or choice.id == "pry_shed" or place.danger <= 2
        ):
            raise StoryError(explain_rejection(place, choice))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.clue is None or c[1] == args.clue)
        and (args.choice is None or c[2] == args.choice)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, clue_id, choice_id = rng.choice(sorted(combos))
    solver_name, solver_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=solver_name)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        clue=clue_id,
        choice=choice_id,
        solver_name=solver_name,
        solver_gender=solver_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.choice not in CHOICES:
        raise StoryError(f"(Unknown choice: {params.choice})")
    world = tell(
        place=PLACES[params.place],
        clue=CLUES[params.clue],
        choice=CHOICES[params.choice],
        solver_name=params.solver_name,
        solver_gender=params.solver_gender,
        friend_name=params.friend_name,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible choices: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue, choice) combos:\n")
        for place, clue, choice in combos:
            print(f"  {place:8} {clue:8} {choice}")
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
            header = f"### {p.solver_name} & {p.friend_name}: {p.clue} in {p.place} ({p.choice}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
