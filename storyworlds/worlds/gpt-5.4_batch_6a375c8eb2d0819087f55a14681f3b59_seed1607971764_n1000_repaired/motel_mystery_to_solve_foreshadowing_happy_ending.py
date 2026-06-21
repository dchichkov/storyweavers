#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/motel_mystery_to_solve_foreshadowing_happy_ending.py
==============================================================================

A standalone story world for a gentle ghost-story-shaped mystery at a motel.

A child stays in a small roadside motel, notices a spooky sign in the night,
follows a trail of clues with a calm grown-up, and discovers that the "ghost"
was something ordinary after all. The ending is always happy, but the world
still enforces common-sense constraints: the chosen motel view must actually
afford the spooky signs, and the chosen helper must be a believable fix for the
real cause.

Run it
------
    python storyworlds/worlds/gpt-5.4/motel_mystery_to_solve_foreshadowing_happy_ending.py
    python storyworlds/worlds/gpt-5.4/motel_mystery_to_solve_foreshadowing_happy_ending.py --view sign_side --cause sign --helper toolbox
    python storyworlds/worlds/gpt-5.4/motel_mystery_to_solve_foreshadowing_happy_ending.py --view sign_side --cause cat
    python storyworlds/worlds/gpt-5.4/motel_mystery_to_solve_foreshadowing_happy_ending.py --all
    python storyworlds/worlds/gpt-5.4/motel_mystery_to_solve_foreshadowing_happy_ending.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/motel_mystery_to_solve_foreshadowing_happy_ending.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/motel_mystery_to_solve_foreshadowing_happy_ending.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
class View:
    id: str
    room_text: str
    night_text: str
    affords: set[str] = field(default_factory=set)
    clue_tags: set[str] = field(default_factory=set)
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
class Cause:
    id: str
    label: str
    spooky_sign: str
    clue_intro: str
    trace_clue: str
    solve_text: str
    ending_text: str
    needs: set[str] = field(default_factory=set)
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
class LightTool:
    id: str
    label: str
    phrase: str
    shine_text: str
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
class Helper:
    id: str
    label: str
    phrase: str
    fixes: set[str] = field(default_factory=set)
    action_text: str = ""
    qa_text: str = ""
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


def _r_cat(world: World) -> list[str]:
    room = world.get("room")
    source = world.get("source")
    child = world.get("child")
    if source.attrs.get("cause") != "cat" or source.meters["active"] < THRESHOLD:
        return []
    sig = ("cat_signs",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["noise"] += 1
    room.meters["mystery"] += 1
    source.meters["hidden"] += 1
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    return []


def _r_sign(world: World) -> list[str]:
    room = world.get("room")
    source = world.get("source")
    child = world.get("child")
    if source.attrs.get("cause") != "sign" or source.meters["active"] < THRESHOLD:
        return []
    sig = ("sign_signs",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["noise"] += 1
    room.meters["flicker"] += 1
    room.meters["mystery"] += 1
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    return []


def _r_ice_machine(world: World) -> list[str]:
    room = world.get("room")
    source = world.get("source")
    child = world.get("child")
    if source.attrs.get("cause") != "ice_machine" or source.meters["active"] < THRESHOLD:
        return []
    sig = ("ice_signs",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["noise"] += 1
    room.meters["chill"] += 1
    room.meters["mystery"] += 1
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="cat_signs", tag="spooky", apply=_r_cat),
    Rule(name="sign_signs", tag="spooky", apply=_r_sign),
    Rule(name="ice_signs", tag="spooky", apply=_r_ice_machine),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = changed or False
    if narrate:
        for s in produced:
            world.say(s)
    return produced


VIEWS = {
    "courtyard": View(
        id="courtyard",
        room_text="Their little motel room opened onto a square courtyard with flower pots, a picnic table, and a row of sleepy doors.",
        night_text="Outside, the courtyard was washed in pale porch light, with dark spaces tucked under the stairs.",
        affords={"cat"},
        clue_tags={"pawprints", "bell", "courtyard"},
    ),
    "sign_side": View(
        id="sign_side",
        room_text="Their motel room faced the tall VACANCY sign at the edge of the parking lot, where red letters blinked over the gravel.",
        night_text="Outside, the sign hummed above the parked cars, and the window curtains glowed red, then dim, then red again.",
        affords={"sign"},
        clue_tags={"sign", "wind", "shadow"},
    ),
    "ice_alcove": View(
        id="ice_alcove",
        room_text="Their motel room sat near the far-end ice machine alcove, where a blue light shone over a humming metal box.",
        night_text="Outside, the end of the walkway looked colder than the rest, with silver rails and a patch of wet concrete.",
        affords={"cat", "ice_machine"},
        clue_tags={"ice", "mist", "bell"},
    ),
}

CAUSES = {
    "cat": Cause(
        id="cat",
        label="the motel owner's cat",
        spooky_sign="a soft jingle followed by a darting shadow under the railing",
        clue_intro="Earlier that evening, the child had noticed a tiny bowl by the office door and a silver bell collar hanging from a hook.",
        trace_clue="small pawprints and one bright bell note",
        solve_text="From behind the ice machine came a small gray cat with a bell on its collar. It had been hiding there after slipping out during supper.",
        ending_text="Soon the cat was purring in the owner's arms, and the courtyard did not seem haunted at all anymore.",
        needs={"courtyard", "ice_alcove"},
        tags={"cat", "bell", "pawprints"},
    ),
    "sign": Cause(
        id="sign",
        label="the loose motel sign",
        spooky_sign="a tapping rattle and a red shadow that slid across the wall",
        clue_intro="At sunset, the child had seen one chain on the old VACANCY sign twitching in the wind and one letter blinking late.",
        trace_clue="a loose chain and a moving red shadow",
        solve_text="The owner lifted the cover of the sign post and showed the loose chain that kept knocking against the pole whenever the wind pushed it.",
        ending_text="Once the chain was tightened, the room grew still, and the red light settled into a calm glow.",
        needs={"sign_side"},
        tags={"sign", "wind", "shadow"},
    ),
    "ice_machine": Cause(
        id="ice_machine",
        label="the rattling ice machine",
        spooky_sign="a clinking shiver and a curl of cold white mist",
        clue_intro="When they first carried in their bags, the child had seen a little puddle under the ice machine and heard it click like teeth.",
        trace_clue="a puddle, cold mist, and a clinking pipe",
        solve_text="The owner opened the side panel and found a loose cold-water line knocking against the machine whenever it chilled and shook.",
        ending_text="After the line was snug and the puddle was dried, the walkway felt ordinary again, just cool and quiet.",
        needs={"ice_alcove"},
        tags={"ice", "mist", "pipes"},
    ),
}

LIGHTS = {
    "flashlight": LightTool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        shine_text="made a clean white circle on the motel walkway",
        tags={"flashlight"},
    ),
    "lantern": LightTool(
        id="lantern",
        label="lantern",
        phrase="a battery lantern",
        shine_text="spread a warm yellow glow over the motel railing",
        tags={"lantern"},
    ),
}

HELPERS = {
    "treats": Helper(
        id="treats",
        label="cat treats",
        phrase="a tin of cat treats",
        fixes={"cat"},
        action_text="shook the little treat tin once, then knelt down with a patient hand",
        qa_text="used a tin of cat treats to coax the hidden cat out",
        tags={"cat", "treats"},
    ),
    "toolbox": Helper(
        id="toolbox",
        label="toolbox",
        phrase="a motel toolbox",
        fixes={"sign"},
        action_text="set down the motel toolbox, climbed the short step stool, and tightened the chain and bracket",
        qa_text="used the motel toolbox to tighten the loose sign",
        tags={"toolbox", "sign"},
    ),
    "wrench": Helper(
        id="wrench",
        label="wrench",
        phrase="an adjustable wrench and a stack of towels",
        fixes={"ice_machine"},
        action_text="used the wrench to snug the cold line and laid the towels over the puddle",
        qa_text="used a wrench and towels to stop the rattling ice machine line",
        tags={"wrench", "ice"},
    ),
}

GIRL_NAMES = ["Lina", "Mia", "Nora", "Ava", "Lucy", "Ella", "Ruby", "June"]
BOY_NAMES = ["Eli", "Ben", "Max", "Noah", "Leo", "Sam", "Theo", "Finn"]
TRAITS = ["careful", "curious", "brave", "quiet", "thoughtful", "observant"]


@dataclass
class StoryParams:
    view: str
    cause: str
    light: str
    helper: str
    child_name: str
    child_gender: str
    parent: str
    owner_name: str
    owner_gender: str
    trait: str
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


def valid_combo(view_id: str, cause_id: str, helper_id: str) -> bool:
    if view_id not in VIEWS or cause_id not in CAUSES or helper_id not in HELPERS:
        return False
    view = VIEWS[view_id]
    cause = CAUSES[cause_id]
    helper = HELPERS[helper_id]
    return cause_id in view.affords and view_id in cause.needs and cause_id in helper.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for view_id in sorted(VIEWS):
        for cause_id in sorted(CAUSES):
            for helper_id in sorted(HELPERS):
                if valid_combo(view_id, cause_id, helper_id):
                    out.append((view_id, cause_id, helper_id))
    return out


def explain_view_cause(view_id: str, cause_id: str) -> str:
    if view_id not in VIEWS or cause_id not in CAUSES:
        return "(No story: unknown view or cause.)"
    view = VIEWS[view_id]
    cause = CAUSES[cause_id]
    return (
        f"(No story: from {view.id.replace('_', ' ')}, the child could not honestly discover "
        f"{cause.label}. Pick a cause that belongs to that part of the motel.)"
    )


def explain_helper(cause_id: str, helper_id: str) -> str:
    if helper_id not in HELPERS or cause_id not in CAUSES:
        return "(No story: unknown helper or cause.)"
    helper = HELPERS[helper_id]
    cause = CAUSES[cause_id]
    return (
        f"(No story: {helper.phrase} is not a believable way to solve the mystery of "
        f"{cause.label}. Choose a helper that actually fits the cause.)"
    )


def predict_signs(world: World) -> dict:
    sim = world.copy()
    sim.get("source").meters["active"] = 1.0
    propagate(sim, narrate=False)
    room = sim.get("room")
    child = sim.get("child")
    return {
        "noise": room.meters["noise"],
        "flicker": room.meters["flicker"],
        "chill": room.meters["chill"],
        "mystery": room.meters["mystery"],
        "fear": child.memes["fear"],
        "curiosity": child.memes["curiosity"],
    }


def introduce(world: World, child: Entity, parent: Entity, view: View) -> None:
    world.say(
        f"After a long drive, {child.id} and {child.pronoun('possessive')} {parent.label_word} stopped for the night at a small motel beside the highway."
    )
    world.say(view.room_text)
    world.say(
        f"{child.id} was a {next((t for t in child.traits if t), 'quiet')} {child.type} who noticed the little things other people walked past."
    )


def settle_in(world: World, child: Entity, view: View, cause: Cause) -> None:
    world.say(
        f"The room smelled like clean soap and old wood, and the bedspread made soft hills under the lamp."
    )
    world.say(view.night_text)
    child.memes["calm"] += 1
    world.say(cause.clue_intro)


def first_sign(world: World, child: Entity, cause: Cause) -> None:
    world.get("source").meters["active"] = 1.0
    signs = predict_signs(world)
    world.facts["predicted_signs"] = signs
    propagate(world, narrate=False)
    world.say(
        f"Later, when the lamp was switched off, {child.id} heard {cause.spooky_sign}."
    )
    if signs["flicker"] >= THRESHOLD and signs["fear"] >= THRESHOLD:
        world.say(
            f"The moving light painted the wall and made the room feel, for one tiny moment, like a place from a ghost story."
        )
    elif signs["chill"] >= THRESHOLD:
        world.say(
            f"A little coldness slipped under the door, and the hush outside felt deeper than before."
        )
    else:
        world.say(
            f"{child.id} pulled the blanket to {child.pronoun('possessive')} chin and listened hard, wondering if a ghost had found the motel after all."
        )


def wake_parent(world: World, child: Entity, parent: Entity) -> None:
    child.memes["fear"] += 1
    world.say(
        f'"{parent.label_word.capitalize()}," {child.id} whispered, tapping {parent.pronoun("object")} on the shoulder. "Something spooky is out there."'
    )
    world.say(
        f"But even while {child.pronoun()} was scared, {child.pronoun()} was also listening carefully. The mystery felt frightening and important at the same time."
    )


def investigate(world: World, child: Entity, parent: Entity, owner: Entity, light: LightTool, cause: Cause) -> None:
    child.memes["bravery"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"{parent.label_word.capitalize()} did not laugh. {parent.pronoun().capitalize()} picked up {light.phrase}, which {light.shine_text}, and opened the door."
    )
    world.say(
        f"In the office doorway stood {owner.id}, the night owner, already peering out because {owner.pronoun()} had heard the strange sound too."
    )
    world.say(
        f"Together they stepped into the night and found {cause.trace_clue}. That made the mystery feel less like magic and more like a puzzle."
    )


def solve(world: World, child: Entity, owner: Entity, cause: Cause, helper: Helper) -> None:
    source = world.get("source")
    room = world.get("room")
    owner.memes["care"] += 1
    owner.memes["relief"] += 1
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    room.meters["mystery"] = 0.0
    room.meters["noise"] = 0.0
    room.meters["flicker"] = 0.0
    room.meters["chill"] = 0.0
    source.meters["active"] = 0.0
    source.meters["solved"] += 1
    world.say(
        f"{owner.id} {helper.action_text}."
    )
    world.say(cause.solve_text)
    if cause.id == "cat":
        world.get("cat").meters["safe"] += 1
    world.say(cause.ending_text)


def ending(world: World, child: Entity, parent: Entity, owner: Entity, cause: Cause) -> None:
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    snack = "hot cocoa" if parent.type == "mother" else "warm milk"
    world.say(
        f"Back inside the motel room, {child.id}'s heart no longer bumped with fear. It bumped with relief instead."
    )
    if cause.id == "cat":
        world.say(
            f"{owner.id} thanked {child.id} for listening so closely, because noticing the little bell had helped bring the lost cat home."
        )
    else:
        world.say(
            f"{owner.id} thanked {child.id} for speaking up, because the strange sound might have gone on all night if nobody had checked."
        )
    world.say(
        f"{parent.label_word.capitalize()} tucked the blanket around {child.id}, handed over {snack}, and smiled. \"Sometimes a spooky thing is only a secret thing waiting to be understood.\""
    )
    if cause.id == "sign":
        image = "Outside the window, the motel sign glowed red and steady, like a watchful ruby star."
    elif cause.id == "ice_machine":
        image = "At the end of the walkway, the ice machine sat quiet at last, with no mist and no clatter at all."
    else:
        image = "Across the courtyard, the cat curled in the office chair, its silver bell resting without a sound."
    world.say(
        f"{image} {child.id} smiled into the pillow and fell asleep feeling braver than before."
    )


def tell(
    view: View,
    cause: Cause,
    light: LightTool,
    helper: Helper,
    child_name: str = "Lina",
    child_gender: str = "girl",
    parent_type: str = "mother",
    owner_name: str = "Mrs. Vale",
    owner_gender: str = "girl",
    trait: str = "observant",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        attrs={"trait": trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        attrs={},
    ))
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type="mother" if owner_gender == "girl" else "father",
        role="owner",
        label="the owner",
        attrs={},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label="motel room",
        attrs={"view": view.id},
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="cause",
        label=cause.label,
        attrs={"cause": cause.id},
    ))
    cat = world.add(Entity(
        id="cat",
        kind="thing",
        type="animal",
        label="cat",
        attrs={"present": cause.id == "cat"},
    ))
    world.facts.update(
        view=view,
        cause=cause,
        light=light,
        helper=helper,
        child=child,
        parent=parent,
        owner=owner,
        room=room,
        source=source,
        signs_seen=[],
        solved=False,
    )

    introduce(world, child, parent, view)
    settle_in(world, child, view, cause)

    world.para()
    first_sign(world, child, cause)
    wake_parent(world, child, parent)

    world.para()
    investigate(world, child, parent, owner, light, cause)
    solve(world, child, owner, cause, helper)

    world.para()
    ending(world, child, parent, owner, cause)

    world.facts.update(
        solved=True,
        mystery_cleared=room.meters["mystery"] < THRESHOLD,
        cat_safe=world.get("cat").meters["safe"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "motel": [
        (
            "What is a motel?",
            "A motel is a place where travelers sleep during a trip. It usually has rooms by a parking lot so people can stop for the night."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in the dark?",
            "A flashlight makes a bright beam so you can see where you are going. It helps people check a dark place safely."
        )
    ],
    "lantern": [
        (
            "What does a battery lantern do?",
            "A battery lantern gives off a soft steady light. It lets people see without using a flame."
        )
    ],
    "cat": [
        (
            "Why might a cat make a spooky sound at night?",
            "A cat can jingle a bell, scratch lightly, or slip through shadows, which can sound strange in the dark. Things often seem spookier when you cannot see them clearly."
        )
    ],
    "sign": [
        (
            "Why can a loose sign sound scary at night?",
            "Wind can shake a loose sign so it taps and rattles over and over. In the dark, that sound can seem mysterious until someone finds where it comes from."
        )
    ],
    "ice": [
        (
            "Why can an ice machine make odd noises?",
            "An ice machine cools, clicks, and moves water, so it can clink or hum. If a part gets loose, the sound can seem much louder at night."
        )
    ],
    "wind": [
        (
            "How can wind make shadows move?",
            "Wind can wiggle signs, branches, or curtains, and then their shadows slide across a wall. The shadow is not alive; it is just moving because the object moved."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you solve a puzzle. It points you toward the real answer."
        )
    ],
}
KNOWLEDGE_ORDER = ["motel", "clue", "cat", "sign", "ice", "wind", "flashlight", "lantern"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    cause = world.facts["cause"]
    light = world.facts["light"]
    return [
        f'Write a gentle ghost-story-style mystery for a 3-to-5-year-old set at a motel, where a child hears something spooky and solves it safely. Include the word "motel".',
        f"Tell a story where a {child.type} named {child.id} follows clues through a motel at night, thinks there may be a ghost, and discovers that the sound really came from {cause.label}.",
        f"Write a child-friendly mystery with foreshadowing, a calm grown-up, {light.label} light, and a happy ending that turns fear into understanding.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    owner = world.facts["owner"]
    cause = world.facts["cause"]
    helper = world.facts["helper"]
    light = world.facts["light"]
    view = world.facts["view"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child staying at a motel with {child.pronoun('possessive')} {parent.label_word}. The night owner, {owner.id}, helps solve the mystery too."
        ),
        (
            "What made the motel seem spooky at first?",
            f"It seemed spooky because {child.id} heard {cause.spooky_sign}. In the dark, that strange sign felt ghostly before anyone knew what was causing it."
        ),
        (
            "What clue appeared before the mystery was solved?",
            f"There was foreshadowing earlier when {cause.clue_intro.lower()} That earlier detail mattered later because it pointed toward the real cause."
        ),
        (
            f"Why did {child.id} go outside instead of hiding under the blanket?",
            f"{child.id} was scared, but also curious enough to want the truth. With {parent.label_word} and {owner.id} there, the mystery felt safe enough to investigate."
        ),
        (
            "How was the mystery solved?",
            f"{owner.id} {helper.qa_text}. That worked because the real cause was {cause.label}, not a ghost."
        ),
    ]
    if cause.id == "cat":
        qa.append(
            (
                "Why was the ending happy?",
                f"The ending was happy because the spooky sound turned out to be a lost cat, and the cat was safely found. The motel felt friendly again once everyone knew the truth."
            )
        )
    else:
        qa.append(
            (
                "Why was the ending happy?",
                f"The ending was happy because the scary sound had an ordinary cause and it was fixed. After that, the motel room felt calm and safe again."
            )
        )
    qa.append(
        (
            "What changed for the child by the end?",
            f"At first {child.id} felt frightened by the mystery. By the end, {child.pronoun()} felt braver because {child.pronoun()} had followed clues and learned what was really there."
        )
    )
    if view.id == "sign_side":
        qa.append(
            (
                "Why did the red light matter?",
                "The red light mattered because it helped make the moving shadow that frightened the child. Once the sign was fixed, the light stopped looking ghostly and became ordinary again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"motel", "clue"} | set(world.facts["cause"].tags) | set(world.facts["light"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
can_host(V, C) :- view(V), cause(C), affords(V, C), needs(C, V).
can_fix(H, C)  :- helper(H), fixes(H, C).
valid(V, C, H) :- can_host(V, C), can_fix(H, C).

chosen_valid :- chosen_view(V), chosen_cause(C), chosen_helper(H), valid(V, C, H).
outcome(solved) :- chosen_valid.
:- chosen_view(V), chosen_cause(C), chosen_helper(H), not valid(V, C, H).

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for view_id, view in VIEWS.items():
        lines.append(asp.fact("view", view_id))
        for cause_id in sorted(view.affords):
            lines.append(asp.fact("affords", view_id, cause_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for need in sorted(cause.needs):
            lines.append(asp.fact("needs", cause_id, need))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for fix in sorted(helper.fixes):
            lines.append(asp.fact("fixes", helper_id, fix))
    for light_id in LIGHTS:
        lines.append(asp.fact("light", light_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_view", params.view),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        view="courtyard",
        cause="cat",
        light="lantern",
        helper="treats",
        child_name="Lina",
        child_gender="girl",
        parent="mother",
        owner_name="Mrs. Vale",
        owner_gender="girl",
        trait="observant",
    ),
    StoryParams(
        view="sign_side",
        cause="sign",
        light="flashlight",
        helper="toolbox",
        child_name="Eli",
        child_gender="boy",
        parent="father",
        owner_name="Mr. Vale",
        owner_gender="boy",
        trait="careful",
    ),
    StoryParams(
        view="ice_alcove",
        cause="ice_machine",
        light="lantern",
        helper="wrench",
        child_name="Ruby",
        child_gender="girl",
        parent="mother",
        owner_name="Mrs. Vale",
        owner_gender="girl",
        trait="curious",
    ),
    StoryParams(
        view="ice_alcove",
        cause="cat",
        light="flashlight",
        helper="treats",
        child_name="Max",
        child_gender="boy",
        parent="father",
        owner_name="Mr. Vale",
        owner_gender="boy",
        trait="quiet",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story motel mystery. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--view", choices=sorted(VIEWS))
    ap.add_argument("--cause", choices=sorted(CAUSES))
    ap.add_argument("--light", choices=sorted(LIGHTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--owner-name")
    ap.add_argument("--owner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.view and args.cause and args.view not in CAUSES.get(args.cause, Cause(
        id="",
        label="",
        spooky_sign="",
        clue_intro="",
        trace_clue="",
        solve_text="",
        ending_text="",
    )).needs:
        raise StoryError(explain_view_cause(args.view, args.cause))
    if args.cause and args.helper and args.cause not in HELPERS[args.helper].fixes:
        raise StoryError(explain_helper(args.cause, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.view is None or combo[0] == args.view)
        and (args.cause is None or combo[1] == args.cause)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    view_id, cause_id, helper_id = rng.choice(combos)
    light_id = args.light or rng.choice(sorted(LIGHTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    parent = args.parent or rng.choice(["mother", "father"])
    owner_gender = args.owner_gender or rng.choice(["girl", "boy"])
    owner_name = args.owner_name or ("Mrs. Vale" if owner_gender == "girl" else "Mr. Vale")
    trait = rng.choice(TRAITS)
    return StoryParams(
        view=view_id,
        cause=cause_id,
        light=light_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        owner_name=owner_name,
        owner_gender=owner_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.view not in VIEWS:
        raise StoryError(f"(No story: unknown view '{params.view}'.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(No story: unknown cause '{params.cause}'.)")
    if params.light not in LIGHTS:
        raise StoryError(f"(No story: unknown light '{params.light}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if not valid_combo(params.view, params.cause, params.helper):
        if params.cause not in HELPERS[params.helper].fixes:
            raise StoryError(explain_helper(params.cause, params.helper))
        raise StoryError(explain_view_cause(params.view, params.cause))

    world = tell(
        view=VIEWS[params.view],
        cause=CAUSES[params.cause],
        light=LIGHTS[params.light],
        helper=HELPERS[params.helper],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        trait=params.trait,
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
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = CURATED[:]
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    for params in cases:
        out = asp_outcome(params)
        if out != "solved":
            rc = 1
            print(f"MISMATCH in outcome for {params}: got {out!r}, expected 'solved'.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(0))
        smoke_params.seed = 0
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story")
        if not sample.story_qa or not sample.world_qa:
            raise StoryError("missing QA")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # noqa: BLE001
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
        print(f"{len(combos)} compatible (view, cause, helper) combos:\n")
        for view_id, cause_id, helper_id in combos:
            print(f"  {view_id:12} {cause_id:12} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.cause} from {p.view} at the motel"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
