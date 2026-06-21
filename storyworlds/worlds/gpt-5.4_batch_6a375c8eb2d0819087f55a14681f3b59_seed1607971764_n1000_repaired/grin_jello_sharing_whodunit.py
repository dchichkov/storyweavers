#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/grin_jello_sharing_whodunit.py
=========================================================

A standalone story world for a tiny "sharing whodunit" domain: children make
jello to share, one cup goes missing, a gentle detective follows concrete clues,
and the mystery ends with a better act of sharing.

The model is state-driven rather than template-swapped. Physical state tracks
cups, chilling, hiding, and portions; emotional state tracks suspicion, guilt,
relief, and generosity. A small reasonableness gate constrains which motives and
fixes make sense for a given occasion, and an inline ASP twin mirrors that gate
plus the outcome classification.

Run it
------
    python storyworlds/worlds/gpt-5.4/grin_jello_sharing_whodunit.py
    python storyworlds/worlds/gpt-5.4/grin_jello_sharing_whodunit.py --occasion porch_party --motive save_for_late_friend
    python storyworlds/worlds/gpt-5.4/grin_jello_sharing_whodunit.py --fix fruit_toppers
    python storyworlds/worlds/gpt-5.4/grin_jello_sharing_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/grin_jello_sharing_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/grin_jello_sharing_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: str = ""
    openable: bool = False
    food: bool = False
    # World state axes
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
# Param registries
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
class Occasion:
    id: str
    place: str
    guests: int
    line: str
    share_line: str
    late_friend: bool = False
    fruit: bool = False
    extra_time: bool = False
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
class Flavor:
    id: str
    label: str
    color: str
    wobble: str
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
class CulpritConfig:
    id: str
    role: str
    clue: str
    grin_style: str
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
class Motive:
    id: str
    confession: str
    kind: str              # "selfish" | "protective"
    needs_late_friend: bool = False
    needs_crowd: bool = False
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
class Fix:
    id: str
    text: str
    qa_text: str
    needs_fruit: bool = False
    needs_time: bool = False
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
# Causal rules
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


def _r_shortage(world: World) -> list[str]:
    tray = world.get("tray")
    guests = world.facts["guest_count"]
    available = int(tray.meters["cups_visible"])
    if available >= guests:
        return []
    sig = ("shortage", available, guests)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["shortage"] += 1
    for child_id in ("detective", "maker", "friend"):
        if child_id in world.entities:
            world.get(child_id).memes["worry"] += 1
    return ["__shortage__"]


def _r_hidden_guilt(world: World) -> list[str]:
    cup = world.get("hidden_cup")
    if cup.meters["hidden"] < THRESHOLD:
        return []
    culprit = world.get(world.facts["culprit_entity"])
    sig = ("guilt", culprit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.memes["guilt"] += 1
    culprit.memes["secret"] += 1
    return []


def _r_share_relief(world: World) -> list[str]:
    tray = world.get("tray")
    if tray.meters["portions_ready"] < world.facts["guest_count"]:
        return []
    sig = ("share_relief", int(tray.meters["portions_ready"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for child_id in ("detective", "maker", "friend"):
        if child_id in world.entities:
            child = world.get(child_id)
            child.memes["relief"] += 1
            child.memes["generosity"] += 1
            child.memes["worry"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="shortage", tag="physical", apply=_r_shortage),
    Rule(name="hidden_guilt", tag="social", apply=_r_hidden_guilt),
    Rule(name="share_relief", tag="social", apply=_r_share_relief),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def motive_ok(occasion: Occasion, motive: Motive) -> bool:
    if motive.needs_late_friend and not occasion.late_friend:
        return False
    if motive.needs_crowd and occasion.guests < 5:
        return False
    return True


def fix_ok(occasion: Occasion, fix: Fix) -> bool:
    if fix.needs_fruit and not occasion.fruit:
        return False
    if fix.needs_time and not occasion.extra_time:
        return False
    return True


def valid_combo(occasion: Occasion, motive: Motive, fix: Fix) -> bool:
    return motive_ok(occasion, motive) and fix_ok(occasion, fix)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for occ_id, occ in OCCASIONS.items():
        for motive_id, motive in MOTIVES.items():
            for fix_id, fix in FIXES.items():
                if valid_combo(occ, motive, fix):
                    out.append((occ_id, motive_id, fix_id))
    return out


def outcome_of(params: "StoryParams") -> str:
    motive = MOTIVES[params.motive]
    return "protective" if motive.kind == "protective" else "selfish"


# ---------------------------------------------------------------------------
# Predictive helper
# ---------------------------------------------------------------------------
def predict_shortage(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "shortage": sim.get("room").meters["shortage"] >= THRESHOLD,
        "visible": int(sim.get("tray").meters["cups_visible"]),
        "needed": sim.facts["guest_count"],
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def setup_party(world: World, detective: Entity, maker: Entity, friend: Entity,
                parent: Entity, occasion: Occasion, flavor: Flavor) -> None:
    tray = world.get("tray")
    detective.memes["curiosity"] += 1
    maker.memes["pride"] += 1
    friend.memes["excitement"] += 1
    world.say(
        f"{detective.id}, {maker.id}, and {friend.id} helped {parent.label_word} make "
        f"{flavor.label} jello in clear little cups for {occasion.place}. {occasion.line}"
    )
    world.say(
        f"When the cups had chilled, they stood in a shiny row on the tray, each one "
        f"{flavor.wobble} when the table bumped."
    )
    world.say(
        f'"Everybody gets one," {maker.id} said, with a pleased little grin as '
        f"{maker.pronoun()} counted the cups on the tray."
    )
    world.facts["initial_cups"] = int(tray.meters["cups_visible"])


def prepare_share(world: World, detective: Entity, occasion: Occasion) -> None:
    world.say(
        f"Soon it was nearly time for {occasion.share_line}, so {detective.id} reached "
        f"for the tray again."
    )


def discover_missing(world: World, detective: Entity) -> None:
    tray = world.get("tray")
    tray.meters["cups_visible"] -= 1
    world.get("hidden_cup").meters["hidden"] += 1
    propagate(world, narrate=False)
    detective.memes["suspicion"] += 1
    world.say(
        f"But one space on the tray was empty. The little paper circle underneath was "
        f"still damp and cold, and now there were only {int(tray.meters['cups_visible'])} cups left."
    )


def inspect_clue(world: World, detective: Entity, culprit_cfg: CulpritConfig,
                 flavor: Flavor) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} crouched down and looked carefully. There was {culprit_cfg.clue}, "
        f"and the trail ended near the refrigerator."
    )
    world.say(
        f'"This is a case," {detective.pronoun()} whispered. "A very wobbly {flavor.label} case."'
    )


def question_room(world: World, detective: Entity, maker: Entity, friend: Entity,
                  culprit: Entity) -> None:
    suspects = [maker.id, friend.id]
    if detective.id not in suspects:
        suspects.insert(0, detective.id)
    world.say(
        f"{detective.id} asked everyone soft questions instead of pointing fingers. "
        f"{maker.id} looked at the cups, {friend.id} looked at the floor, and the kitchen felt very still."
    )
    if culprit.role == "friend":
        world.say(
            f"Then {detective.id} noticed {culprit.id}'s {world.facts['culprit_cfg'].grin_style} grin fade into a worried line."
        )
    else:
        world.say(
            f"Then {detective.id} noticed {culprit.id}'s {world.facts['culprit_cfg'].grin_style} grin go small and nervous."
        )


def find_cup(world: World, detective: Entity, culprit: Entity, flavor: Flavor) -> None:
    culprit.memes["guilt"] += 1
    world.say(
        f"{detective.id} opened the refrigerator slowly. Behind the milk sat the missing cup of "
        f"{flavor.label}, still shining and trembling."
    )
    world.say(
        f'{detective.id} turned back gently. "{culprit.id}," {detective.pronoun()} said, '
        f'"did you hide it?"'
    )


def confess(world: World, culprit: Entity, motive: Motive, occasion: Occasion) -> None:
    culprit.memes["secret"] = 0.0
    culprit.memes["guilt"] += 1
    world.say(
        f"{culprit.id}'s shoulders drooped. {culprit.pronoun().capitalize()} nodded and said, "
        f'"{motive.confession}"'
    )
    if motive.kind == "protective":
        culprit.memes["care"] += 1
        world.say(
            f"It had not started as meanness. It had started as worry about whether there would be enough to share."
        )
    else:
        world.say(
            f"It was a selfish choice, but it sounded smaller and sadder once it was spoken out loud."
        )
    if occasion.late_friend and motive.needs_late_friend:
        world.say("Everyone could picture the late friend who was still hurrying over from down the street.")


def choose_fix(world: World, parent: Entity, detective: Entity, maker: Entity,
               culprit: Entity, fix: Fix, flavor: Flavor) -> None:
    tray = world.get("tray")
    hidden = world.get("hidden_cup")
    hidden.meters["hidden"] = 0.0
    if fix.id == "split_cups":
        tray.meters["cups_visible"] += 1
        tray.meters["portions_ready"] = float(world.facts["guest_count"])
    elif fix.id == "fruit_toppers":
        tray.meters["cups_visible"] += 1
        tray.meters["fruit_added"] += float(world.facts["guest_count"])
        tray.meters["portions_ready"] = float(world.facts["guest_count"])
    elif fix.id == "make_more":
        tray.meters["cups_visible"] += 1
        tray.meters["cups_made_late"] += 1
        tray.meters["portions_ready"] = float(world.facts["guest_count"])
    propagate(world, narrate=False)

    culprit.memes["generosity"] += 1
    maker.memes["generosity"] += 1
    detective.memes["relief"] += 1
    parent.memes["approval"] += 1

    world.say(
        f"{parent.label_word.capitalize()} did not scold first. {parent.pronoun().capitalize()} looked at the children, "
        f"looked at the tray, and helped them think about sharing."
    )
    world.say(fix.text.format(flavor=flavor.label))
    if fix.id == "split_cups":
        world.say(
            f"Soon each child had a smaller cup, but every wobbling bite belonged to the whole circle, not just one person."
        )
    elif fix.id == "fruit_toppers":
        world.say(
            "The bright fruit made the cups look extra special, and suddenly the mystery ended in a prettier dessert than before."
        )
    else:
        world.say(
            f"The fresh batch needed a few more minutes to set, so the children laid spoons on the table and waited together instead of grabbing first."
        )


def lesson_end(world: World, detective: Entity, maker: Entity, friend: Entity,
               culprit: Entity, motive: Motive, occasion: Occasion) -> None:
    culprit.memes["guilt"] = 0.0
    culprit.memes["relief"] += 1
    culprit.memes["generosity"] += 1
    maker.memes["relief"] += 1
    friend.memes["relief"] += 1
    detective.memes["satisfaction"] += 1

    if motive.kind == "protective":
        world.say(
            f'"Next time," {detective.id} said, "we can tell the worry instead of hiding the cup."'
        )
    else:
        world.say(
            f'"Next time," {maker.id} said, "we can ask for help instead of sneaking extra."'
        )

    last = occasion.place
    world.say(
        f"Then they carried the tray to {last}. The missing jello was not missing anymore, and when everyone took a turn, "
        f"{culprit.id} was the first one to pass a cup along with an honest grin."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(occasion: Occasion, flavor: Flavor, culprit_cfg: CulpritConfig,
         motive: Motive, fix: Fix,
         detective_name: str = "Nora", detective_gender: str = "girl",
         maker_name: str = "Ben", maker_gender: str = "boy",
         friend_name: str = "Mia", friend_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()

    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=detective_gender,
        label=detective_name,
        role="detective",
        attrs={"name": detective_name},
    ))
    maker = world.add(Entity(
        id="maker",
        kind="character",
        type=maker_gender,
        label=maker_name,
        role="maker",
        attrs={"name": maker_name},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        attrs={"name": friend_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    room = world.add(Entity(id="room", type="room", label="the kitchen"))
    room.meters["shortage"] = 0.0
    tray = world.add(Entity(id="tray", type="tray", label="the tray"))
    tray.meters["cups_visible"] = float(occasion.guests)
    tray.meters["portions_ready"] = float(occasion.guests - 1)
    tray.meters["fruit_added"] = 0.0
    tray.meters["cups_made_late"] = 0.0
    hidden_cup = world.add(Entity(id="hidden_cup", type="cup", label="the hidden cup", food=True))
    hidden_cup.meters["hidden"] = 0.0

    culprit_entity = culprit_cfg.role
    world.facts.update(
        occasion=occasion,
        flavor=flavor,
        culprit_cfg=culprit_cfg,
        motive=motive,
        fix=fix,
        guest_count=occasion.guests,
        culprit_entity=culprit_entity,
        detective_name=detective_name,
        maker_name=maker_name,
        friend_name=friend_name,
    )

    culprit = world.get(culprit_entity)

    setup_party(world, detective, maker, friend, parent, occasion, flavor)
    world.para()
    prepare_share(world, detective, occasion)
    discover_missing(world, detective)
    inspect_clue(world, detective, culprit_cfg, flavor)
    question_room(world, detective, maker, friend, culprit)
    world.para()
    find_cup(world, detective, culprit, flavor)
    confess(world, culprit, motive, occasion)
    world.para()
    choose_fix(world, parent, detective, maker, culprit, fix, flavor)
    lesson_end(world, detective, maker, friend, culprit, motive, occasion)

    world.facts.update(
        detective=detective,
        maker=maker,
        friend=friend,
        parent=parent,
        tray=tray,
        hidden_cup=hidden_cup,
        culprit=culprit,
        shortage=world.get("room").meters["shortage"] >= THRESHOLD,
        hidden_before_confession=True,
        portions_ready=int(tray.meters["portions_ready"]),
        outcome="protective" if motive.kind == "protective" else "selfish",
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
OCCASIONS = {
    "porch_party": Occasion(
        id="porch_party",
        place="the back porch",
        guests=5,
        line="A warm breeze pushed at the screen door, and five spoons waited in a jar.",
        share_line="the porch party",
        late_friend=True,
        fruit=True,
        extra_time=True,
        tags={"party", "sharing"},
    ),
    "reading_circle": Occasion(
        id="reading_circle",
        place="the library reading rug",
        guests=4,
        line="A picture book lay open nearby, and four napkins were folded like little tents.",
        share_line="reading circle",
        late_friend=False,
        fruit=False,
        extra_time=False,
        tags={"library", "sharing"},
    ),
    "garden_snack": Occasion(
        id="garden_snack",
        place="the garden table",
        guests=6,
        line="Sunlight made little gold squares on the chairs, and six spoons clinked in a cup.",
        share_line="garden snack",
        late_friend=False,
        fruit=True,
        extra_time=False,
        tags={"garden", "sharing"},
    ),
    "after_school": Occasion(
        id="after_school",
        place="the kitchen table",
        guests=4,
        line="Backpacks were by the door, and there was still enough time before homework.",
        share_line="after-school snack",
        late_friend=False,
        fruit=False,
        extra_time=True,
        tags={"home", "sharing"},
    ),
}

FLAVORS = {
    "strawberry": Flavor(
        id="strawberry",
        label="strawberry jello",
        color="red",
        wobble="gave a ruby wobble",
        tags={"jello", "dessert"},
    ),
    "lime": Flavor(
        id="lime",
        label="lime jello",
        color="green",
        wobble="shivered green and bright",
        tags={"jello", "dessert"},
    ),
    "orange": Flavor(
        id="orange",
        label="orange jello",
        color="orange",
        wobble="glowed and bobbled like sunset jelly",
        tags={"jello", "dessert"},
    ),
}

CULPRITS = {
    "maker": CulpritConfig(
        id="maker",
        role="maker",
        clue="a tiny sticky spoon print near the tray",
        grin_style="caught-looking",
        tags={"child", "culprit"},
    ),
    "friend": CulpritConfig(
        id="friend",
        role="friend",
        clue="one wobbling drop of jello on a sneaker toe",
        grin_style="quick",
        tags={"child", "culprit"},
    ),
}

MOTIVES = {
    "wanted_extra": Motive(
        id="wanted_extra",
        confession="I wanted two cups because this was my favorite flavor, and I did not want to wait to see if there would be leftovers.",
        kind="selfish",
        tags={"selfish", "sharing"},
    ),
    "worried_not_enough": Motive(
        id="worried_not_enough",
        confession="I thought someone might be left out, so I hid one cup until I could make sure everybody else had something.",
        kind="protective",
        needs_crowd=True,
        tags={"worry", "sharing"},
    ),
    "save_for_late_friend": Motive(
        id="save_for_late_friend",
        confession="I was saving one for the friend who is always last, because I was afraid the tray would be empty by the time they came.",
        kind="protective",
        needs_late_friend=True,
        tags={"late_friend", "sharing"},
    ),
}

FIXES = {
    "split_cups": Fix(
        id="split_cups",
        text='"{0}"'.format("They set the missing cup back on the tray, and then everyone helped spoon the jello into smaller cups so nobody would be left out."),
        qa_text="They divided the jello into smaller cups so everyone still got some.",
        tags={"sharing", "divide"},
    ),
    "fruit_toppers": Fix(
        id="fruit_toppers",
        text='"{0}"'.format("They set the missing cup back and topped each cup with banana slices and strawberries from the fruit bowl, so the snack felt full and special for everybody."),
        qa_text="They returned the hidden cup and added fruit to every serving so the snack stretched for the whole group.",
        needs_fruit=True,
        tags={"sharing", "fruit"},
    ),
    "make_more": Fix(
        id="make_more",
        text='"{0}"'.format("They put the hidden cup back, stirred one more quick bowl of {flavor}, and made an extra set while they cleaned up the spoons together."),
        qa_text="They put the cup back and made more jello because there was still time.",
        needs_time=True,
        tags={"sharing", "more_food"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Theo", "Max", "Sam", "Leo", "Jack", "Finn", "Eli"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    occasion: str = "porch_party"
    flavor: str = "lime"
    culprit: str = "friend"
    motive: str = "save_for_late_friend"
    fix: str = "fruit_toppers"
    detective_name: str = "Nora"
    detective_gender: str = "girl"
    maker_name: str = "Ben"
    maker_gender: str = "boy"
    friend_name: str = "Mia"
    friend_gender: str = "girl"
    parent: str = "mother"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "jello": [
        (
            "What is jello?",
            "Jello is a soft, wobbly dessert made from flavored gelatin and water. It holds its shape, but it jiggles when you move it."
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting other people have some of what you have. It is a way of being fair and kind in a group."
        )
    ],
    "mystery": [
        (
            "What is a whodunit story?",
            "A whodunit is a mystery story about finding out who did something. The characters notice clues and ask careful questions to solve it."
        )
    ],
    "fruit": [
        (
            "Why can fruit help stretch a snack?",
            "Fruit adds more food to the table, so each serving can feel fuller. That can help a group share fairly."
        )
    ],
    "waiting": [
        (
            "Why is it better to ask than to hide food?",
            "Asking gives everyone a chance to solve the problem together. Hiding food makes people confused and worried."
        )
    ],
}
KNOWLEDGE_ORDER = ["jello", "sharing", "mystery", "fruit", "waiting"]


def who_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    culprit = who_name(f["culprit"])
    flavor = f["flavor"].label
    occasion = f["occasion"]
    motive = f["motive"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old that includes the words "grin" and "jello", and ends with sharing.',
        f"Tell a mystery story where children make {flavor} to share at {occasion.place}, one cup goes missing, and a child detective solves the case kindly.",
        f"Write a story where {culprit} hides a cup of {flavor} because {motive.kind == 'protective' and 'they are worried about fairness' or 'they want extra for themself'}, and the ending shows a better way to share.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    maker = f["maker"]
    friend = f["friend"]
    culprit = f["culprit"]
    parent = f["parent"]
    occasion = f["occasion"]
    flavor = f["flavor"]
    motive = f["motive"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {who_name(detective)}, {who_name(maker)}, and {who_name(friend)} making {flavor.label} to share, plus their {parent.label_word} who helps at the end."
        ),
        (
            "What was the mystery?",
            f"One cup of {flavor.label} disappeared from the tray just before {occasion.share_line}. That meant there were not enough visible cups for everyone."
        ),
        (
            f"How did {who_name(detective)} solve the mystery?",
            f"{who_name(detective)} looked for clues instead of blaming anyone right away. The clue led to the refrigerator, where the hidden cup was still cold and wobbling."
        ),
        (
            f"Who hid the jello, and why?",
            f"{who_name(culprit)} hid the cup. {motive.confession} That motive mattered because it explains whether the mistake came from selfishness or from worried, muddled caring."
        ),
        (
            "How did the children fix the problem?",
            f"{fix.qa_text} They solved the shortage together, so the ending proved that sharing worked better than keeping a secret."
        ),
    ]
    if motive.kind == "protective":
        qa.append(
            (
                f"Was {who_name(culprit)} trying to be mean?",
                f"No. {who_name(culprit)} made a poor choice by hiding the cup, but the choice came from worry about somebody being left out. The story shows that fairness works better when you speak up instead of sneaking."
            )
        )
    else:
        qa.append(
            (
                f"What did {who_name(culprit)} learn?",
                f"{who_name(culprit)} learned that wanting extra is not a good reason to hide food from the group. Asking and sharing turned the snack back into something fair."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"jello", "sharing", "mystery", "waiting"}
    if world.facts["fix"].needs_fruit:
        tags.add("fruit")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(O, M, F) :- occasion(O), motive(M), fix(F), motive_ok(O, M), fix_ok(O, F).

motive_ok(O, M) :- motive(M), not needs_late_friend(M), not needs_crowd(M).
motive_ok(O, M) :- motive(M), needs_late_friend(M), late_friend(O).
motive_ok(O, M) :- motive(M), needs_crowd(M), guests(O, G), G >= 5.

fix_ok(O, F) :- fix(F), not needs_fruit(F), not needs_time(F).
fix_ok(O, F) :- fix(F), needs_fruit(F), has_fruit(O), not needs_time(F).
fix_ok(O, F) :- fix(F), needs_time(F), has_time(O), not needs_fruit(F).
fix_ok(O, F) :- fix(F), needs_fruit(F), has_fruit(O), needs_time(F), has_time(O).

outcome(protective) :- chosen_motive(M), motive_kind(M, protective).
outcome(selfish)    :- chosen_motive(M), motive_kind(M, selfish).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for occ_id, occ in OCCASIONS.items():
        lines.append(asp.fact("occasion", occ_id))
        lines.append(asp.fact("guests", occ_id, occ.guests))
        if occ.late_friend:
            lines.append(asp.fact("late_friend", occ_id))
        if occ.fruit:
            lines.append(asp.fact("has_fruit", occ_id))
        if occ.extra_time:
            lines.append(asp.fact("has_time", occ_id))
    for motive_id, motive in MOTIVES.items():
        lines.append(asp.fact("motive", motive_id))
        lines.append(asp.fact("motive_kind", motive_id, motive.kind))
        if motive.needs_late_friend:
            lines.append(asp.fact("needs_late_friend", motive_id))
        if motive.needs_crowd:
            lines.append(asp.fact("needs_crowd", motive_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        if fix.needs_fruit:
            lines.append(asp.fact("needs_fruit", fix_id))
        if fix.needs_time:
            lines.append(asp.fact("needs_time", fix_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_motive", params.motive),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome classifications differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("empty story from generate()")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        occasion="porch_party",
        flavor="lime",
        culprit="friend",
        motive="save_for_late_friend",
        fix="fruit_toppers",
        detective_name="Nora",
        detective_gender="girl",
        maker_name="Ben",
        maker_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent="mother",
    ),
    StoryParams(
        occasion="garden_snack",
        flavor="strawberry",
        culprit="maker",
        motive="worried_not_enough",
        fix="split_cups",
        detective_name="Theo",
        detective_gender="boy",
        maker_name="Lucy",
        maker_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        parent="father",
    ),
    StoryParams(
        occasion="after_school",
        flavor="orange",
        culprit="friend",
        motive="wanted_extra",
        fix="make_more",
        detective_name="Maya",
        detective_gender="girl",
        maker_name="Sam",
        maker_gender="boy",
        friend_name="Ella",
        friend_gender="girl",
        parent="mother",
    ),
    StoryParams(
        occasion="reading_circle",
        flavor="lime",
        culprit="maker",
        motive="wanted_extra",
        fix="split_cups",
        detective_name="Leo",
        detective_gender="boy",
        maker_name="Ava",
        maker_gender="girl",
        friend_name="Zoe",
        friend_gender="girl",
        parent="father",
    ),
]


def explain_invalid(occasion_id: str, motive_id: str, fix_id: str) -> str:
    occ = OCCASIONS[occasion_id]
    motive = MOTIVES[motive_id]
    fix = FIXES[fix_id]
    if not motive_ok(occ, motive):
        if motive.needs_late_friend:
            return (
                f"(No story: motive '{motive_id}' only makes sense when a late friend is expected, "
                f"but {occasion_id} has no late friend to save a cup for.)"
            )
        if motive.needs_crowd:
            return (
                f"(No story: motive '{motive_id}' only makes sense for a bigger crowd, "
                f"but {occasion_id} does not have enough guests to make that worry believable.)"
            )
    if not fix_ok(occ, fix):
        if fix.needs_fruit:
            return (
                f"(No story: fix '{fix_id}' needs fruit on hand, but {occasion_id} has no fruit bowl ready.)"
            )
        if fix.needs_time:
            return (
                f"(No story: fix '{fix_id}' needs extra time to make more jello, but {occasion_id} is too rushed.)"
            )
    return "(No story: this combination is not reasonable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a missing jello cup, a gentle mystery, and a better act of sharing."
    )
    ap.add_argument("--occasion", choices=OCCASIONS)
    ap.add_argument("--flavor", choices=FLAVORS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--fix", choices=FIXES)
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


def pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.occasion and args.motive and args.fix:
        if not valid_combo(OCCASIONS[args.occasion], MOTIVES[args.motive], FIXES[args.fix]):
            raise StoryError(explain_invalid(args.occasion, args.motive, args.fix))
    elif args.occasion and args.motive and not motive_ok(OCCASIONS[args.occasion], MOTIVES[args.motive]):
        raise StoryError(explain_invalid(args.occasion, args.motive, next(iter(FIXES))))
    elif args.occasion and args.fix and not fix_ok(OCCASIONS[args.occasion], FIXES[args.fix]):
        raise StoryError(explain_invalid(args.occasion, next(iter(MOTIVES)), args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.occasion is None or combo[0] == args.occasion)
        and (args.motive is None or combo[1] == args.motive)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    occasion_id, motive_id, fix_id = rng.choice(sorted(combos))
    flavor_id = args.flavor or rng.choice(sorted(FLAVORS))
    culprit_id = args.culprit or rng.choice(sorted(CULPRITS))
    parent = args.parent or rng.choice(["mother", "father"])

    detective_gender = rng.choice(["girl", "boy"])
    maker_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])

    used: set[str] = set()
    detective_name = pick_name(rng, detective_gender, used)
    used.add(detective_name)
    maker_name = pick_name(rng, maker_gender, used)
    used.add(maker_name)
    friend_name = pick_name(rng, friend_gender, used)
    used.add(friend_name)

    return StoryParams(
        occasion=occasion_id,
        flavor=flavor_id,
        culprit=culprit_id,
        motive=motive_id,
        fix=fix_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        maker_name=maker_name,
        maker_gender=maker_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.occasion not in OCCASIONS:
        raise StoryError(f"(Unknown occasion: {params.occasion})")
    if params.flavor not in FLAVORS:
        raise StoryError(f"(Unknown flavor: {params.flavor})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.motive not in MOTIVES:
        raise StoryError(f"(Unknown motive: {params.motive})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent: {params.parent})")

    occasion = OCCASIONS[params.occasion]
    motive = MOTIVES[params.motive]
    fix = FIXES[params.fix]
    if not valid_combo(occasion, motive, fix):
        raise StoryError(explain_invalid(params.occasion, params.motive, params.fix))

    world = tell(
        occasion=occasion,
        flavor=FLAVORS[params.flavor],
        culprit_cfg=CULPRITS[params.culprit],
        motive=motive,
        fix=fix,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        maker_name=params.maker_name,
        maker_gender=params.maker_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
    )

    world.get("detective").attrs["name"] = params.detective_name
    world.get("maker").attrs["name"] = params.maker_name
    world.get("friend").attrs["name"] = params.friend_name

    return StorySample(
        params=params,
        story=world.render().replace("detective", params.detective_name).replace("maker", params.maker_name).replace("friend", params.friend_name),
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
        print(f"{len(combos)} compatible (occasion, motive, fix) combos:\n")
        for occ, motive, fix in combos:
            print(f"  {occ:14} {motive:18} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.occasion}: {p.motive} with {p.fix} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
