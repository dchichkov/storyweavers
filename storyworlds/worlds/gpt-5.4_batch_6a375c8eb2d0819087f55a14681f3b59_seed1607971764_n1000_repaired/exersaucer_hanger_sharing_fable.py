#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/exersaucer_hanger_sharing_fable.py
=============================================================

A standalone story world about sharing: one small child bounces in an exersaucer,
a bright toy hangs from a hanger, and another child wants to join the play.
The world model decides whether the children share smoothly or whether a snag
happens first, and the prose follows that state.

The style aims at a gentle fable: clear wants, a small mistake, a wise fix,
and an ending image that proves the lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/exersaucer_hanger_sharing_fable.py
    python storyworlds/worlds/gpt-5.4/exersaucer_hanger_sharing_fable.py --setting nursery --toy ribbon_streamer --method middle_hang
    python storyworlds/worlds/gpt-5.4/exersaucer_hanger_sharing_fable.py --method snatch_back
    python storyworlds/worlds/gpt-5.4/exersaucer_hanger_sharing_fable.py --all
    python storyworlds/worlds/gpt-5.4/exersaucer_hanger_sharing_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/exersaucer_hanger_sharing_fable.py --verify
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
PATIENT_TRAITS = {"patient", "gentle", "thoughtful"}


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
    opening: str
    perch: str
    affords: set[str] = field(default_factory=set)
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
class Toy:
    id: str
    label: str
    phrase: str
    color: str
    motion: str
    sound: str
    long: bool = False
    light: bool = True
    two_sided: bool = False
    durable: bool = True
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
    text: str
    closing: str
    qa_text: str
    simultaneous: bool = False
    needs_long: bool = False
    needs_light: bool = False
    needs_two_sided: bool = False
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"bouncer", "watcher"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_hoard_hurts(world: World) -> list[str]:
    out: list[str] = []
    bouncer = world.get("bouncer")
    watcher = world.get("watcher")
    toy = world.get("toy")
    if bouncer.memes["hoarding"] >= THRESHOLD and watcher.memes["want"] >= THRESHOLD:
        sig = ("hoard_hurts",)
        if sig not in world.fired:
            world.fired.add(sig)
            watcher.memes["sad"] += 1
            watcher.memes["envy"] += 1
            toy.meters["pulled_close"] += 1
            out.append("__sadness__")
    return out


def _r_tug_falls(world: World) -> list[str]:
    out: list[str] = []
    toy = world.get("toy")
    hanger = world.get("hanger")
    if hanger.meters["tugged"] >= THRESHOLD and toy.meters["hanging"] >= THRESHOLD:
        sig = ("tug_falls",)
        if sig not in world.fired:
            world.fired.add(sig)
            toy.meters["hanging"] = 0.0
            toy.meters["fallen"] += 1
            hanger.meters["swaying"] += 1
            for kid in world.kids():
                kid.memes["startled"] += 1
            out.append("__fall__")
    return out


def _r_shared_joy(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("shared_ready"):
        sig = ("shared_joy",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["joy"] += 1
                kid.memes["love"] += 1
                kid.memes["sad"] = 0.0
                kid.memes["envy"] = 0.0
            out.append("__shared__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hoard_hurts", tag="social", apply=_r_hoard_hurts),
    Rule(name="tug_falls", tag="physical", apply=_r_tug_falls),
    Rule(name="shared_joy", tag="social", apply=_r_shared_joy),
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
        for s in produced:
            if s == "__sadness__":
                watcher = world.get("watcher")
                world.say(
                    f"{watcher.id}'s mouth grew small, and the room felt less merry than before."
                )
            elif s == "__fall__":
                world.say(
                    "The hanger jerked, the bright toy slipped free, and everything stopped for one startled breath."
                )
    return produced


def method_compatible(toy: Toy, method: Method) -> bool:
    if method.needs_long and not toy.long:
        return False
    if method.needs_light and not toy.light:
        return False
    if method.needs_two_sided and not toy.two_sided:
        return False
    return True


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for toy_id, toy in TOYS.items():
            for method_id, method in METHODS.items():
                if method.sense < SENSE_MIN:
                    continue
                if method_id not in setting.affords:
                    continue
                if method_compatible(toy, method):
                    combos.append((setting_id, toy_id, method_id))
    return sorted(combos)


def outcome_of(params: "StoryParams") -> str:
    method = METHODS[params.method]
    if method.simultaneous:
        return "smooth"
    if params.wait == "short":
        return "smooth"
    if params.sharer_trait in PATIENT_TRAITS:
        return "smooth"
    return "snag"


def explain_method_rejection(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on good sense "
        f"(sense={method.sense} < {SENSE_MIN}). This world prefers kinder ways of sharing. "
        f"Try: {better}.)"
    )


def explain_combo_rejection(setting: Setting, toy: Toy, method: Method) -> str:
    if method.id not in setting.affords:
        return (
            f"(No story: {setting.place} has no good spot for the '{method.id}' sharing plan. "
            f"Pick a setting that supports that method.)"
        )
    if method.needs_long and not toy.long:
        return (
            f"(No story: {toy.phrase} is too short for '{method.id}'. "
            f"That method needs something long enough for two children to reach.)"
        )
    if method.needs_light and not toy.light:
        return (
            f"(No story: {toy.phrase} is too heavy for '{method.id}'. "
            f"A hanger can only hold the toy safely in the middle when it is light.)"
        )
    if method.needs_two_sided and not toy.two_sided:
        return (
            f"(No story: {toy.phrase} has no two easy ends to share at once. "
            f"That method only works for a toy with two clear sides.)"
        )
    return "(No story: this combination does not make a reasonable sharing plan.)"


def predict_waiting(world: World, method: Method, sharer_trait: str, wait: str) -> dict:
    sim = world.copy()
    _hoard(sim, narrate=False)
    if not method.simultaneous and wait == "long" and sharer_trait not in PATIENT_TRAITS:
        _tug(sim, narrate=False)
    return {
        "sad": sim.get("watcher").memes["sad"] >= THRESHOLD,
        "fallen": sim.get("toy").meters["fallen"] >= THRESHOLD,
    }


def _hang_toy(world: World, narrate: bool = True) -> None:
    toy = world.get("toy")
    hanger = world.get("hanger")
    toy.meters["hanging"] = 1.0
    hanger.meters["holding"] = 1.0
    if narrate:
        setting = world.setting
        world.say(
            f"Above the exersaucer, a hanger rested on {setting.perch}, and from it hung {toy.label}."
        )


def introduce(world: World, bouncer: Entity, watcher: Entity, parent: Entity, toy: Toy) -> None:
    setting = world.setting
    world.say(setting.opening)
    world.say(
        f"In the middle of the room stood an exersaucer, where {bouncer.id} bounced with bright little kicks."
    )
    _hang_toy(world, narrate=True)
    world.say(
        f"{bouncer.id} batted {toy.phrase}, and it {toy.motion} with {toy.sound}."
    )
    world.say(
        f"Beside the chair leg stood {watcher.id}, watching every swing while {parent.label_word} folded the last small towels."
    )


def desire(world: World, watcher: Entity, toy: Toy) -> None:
    watcher.memes["want"] += 1
    world.say(
        f'Soon {watcher.id} reached up. "May I play with the {toy.label} too?" {watcher.pronoun()} asked.'
    )


def _hoard(world: World, narrate: bool = True) -> None:
    bouncer = world.get("bouncer")
    bouncer.memes["hoarding"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f'But {bouncer.id} hugged the string close and said, "Mine first."'
        )


def warn(world: World, parent: Entity, method: Method, sharer_trait: str, wait: str) -> None:
    pred = predict_waiting(world, method, sharer_trait, wait)
    world.facts["predicted_sad"] = pred["sad"]
    world.facts["predicted_fall"] = pred["fallen"]
    if pred["fallen"]:
        world.say(
            f'{parent.label_word.capitalize()} looked at the swaying hanger and said softly, '
            f'"A toy is happiest when hands are gentle. If waiting grows too hard, a tug may bring it down."'
        )
    elif pred["sad"]:
        world.say(
            f'{parent.label_word.capitalize()} saw the small face beside the exersaucer and said, '
            f'"One merry toy should make two hearts glad, not one heart proud and one heart sore."'
        )


def snag_begins(world: World, watcher: Entity) -> None:
    watcher.memes["frustration"] += 1
    world.say(
        f"The waiting grew long. {watcher.id} shifted from one foot to the other and stared at the swinging prize."
    )


def _tug(world: World, narrate: bool = True) -> None:
    hanger = world.get("hanger")
    hanger.meters["tugged"] += 1
    propagate(world, narrate=narrate)


def tug(world: World, watcher: Entity) -> None:
    world.say(
        f"At last {watcher.id} gave the hanger a quick pull, not out of malice, but out of impatience."
    )
    _tug(world, narrate=True)


def repair(world: World, parent: Entity, toy: Toy) -> None:
    toy_ent = world.get("toy")
    hanger = world.get("hanger")
    toy_ent.meters["fallen"] = 0.0
    toy_ent.meters["hanging"] = 1.0
    hanger.meters["holding"] = 1.0
    world.say(
        f"{parent.label_word.capitalize()} picked up {toy.phrase}, steadied the hanger, and hung it back with careful fingers."
    )


def share_plan(world: World, parent: Entity, toy: Toy, method: Method, wait: str) -> None:
    if method.id == "turns":
        turn_words = "two short turns" if wait == "long" else "small turns"
        world.say(
            f'{parent.label_word.capitalize()} smiled and said, '
            f'"Then we shall share by {turn_words}. One child pats, then the other pats."'
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} {method.text.format(toy=toy.label)}."
        )


def sharing_happens(world: World, bouncer: Entity, watcher: Entity, toy: Toy, method: Method) -> None:
    world.facts["shared_ready"] = True
    propagate(world, narrate=False)
    if method.id == "turns":
        world.say(
            f"First {bouncer.id} tapped the {toy.label} and watched it {toy.motion}. Then {watcher.id} had a turn, and then another little turn came back again."
        )
    else:
        world.say(
            f"Soon both children could reach {toy.phrase} at once, and it {toy.motion} between them."
        )
    world.say(method.closing.format(bouncer=bouncer.id, watcher=watcher.id))


def moral(world: World, parent: Entity, toy: Toy, outcome: str) -> None:
    if outcome == "smooth":
        world.say(
            f'{parent.label_word.capitalize()} said, "See how the {toy.label} shines more brightly when it is shared?"'
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} said, "A grasping hand startles joy away, but a patient hand invites it back."'
        )


def ending(world: World, bouncer: Entity, watcher: Entity, toy: Toy) -> None:
    world.say(
        f"By the end, the exersaucer bobbed, the hanger swayed only gently, and {bouncer.id} and {watcher.id} laughed at the same bright dance."
    )
def tell(
    bouncer_name: str,
    bouncer_gender: str,
    watcher_name: str,
    watcher_gender: str,
    parent_type: ParentType,
    sharer_trait: SharerTrait,
    wait: Wait,
) -> World:
    world = World(setting)
    parent = world.add(
        Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent")
    )
    bouncer = world.add(
        Entity(
            id=bouncer_name,
            kind="character",
            type=bouncer_gender,
            role="bouncer",
            traits=["little", "bouncy"],
            attrs={"trait": "bouncy"},
        )
    )
    watcher = world.add(
        Entity(
            id=watcher_name,
            kind="character",
            type=watcher_gender,
            role="watcher",
            traits=["little", sharer_trait],
            attrs={"trait": sharer_trait},
        )
    )
    toy_ent = world.add(
        Entity(
            id="toy",
            type="toy",
            label=toy.label,
            attrs={
                "toy_id": toy.id,
                "long": toy.long,
                "light": toy.light,
                "two_sided": toy.two_sided,
                "durable": toy.durable,
            },
        )
    )
    hanger = world.add(
        Entity(
            id="hanger",
            type="hanger",
            label="hanger",
            attrs={"steady": True},
        )
    )
    world.add(
        Entity(
            id="seat",
            type="exersaucer",
            label="exersaucer",
        )
    )
    world.facts.update(
        setting=setting,
        toy_cfg=toy,
        method=method,
        parent=parent,
        bouncer=bouncer,
        watcher=watcher,
        wait=wait,
        sharer_trait=sharer_trait,
        predicted_sad=False,
        predicted_fall=False,
        shared_ready=False,
    )
    bouncer.memes["joy"] = 1.0
    watcher.memes["want"] = 0.0
    watcher.memes["sad"] = 0.0
    hanger.meters["tugged"] = 0.0
    toy_ent.meters["hanging"] = 0.0
    toy_ent.meters["fallen"] = 0.0

    introduce(world, bouncer, watcher, parent, toy)
    world.para()
    desire(world, watcher, toy)
    _hoard(world, narrate=True)
    warn(world, parent, method, sharer_trait, wait)

    world.para()
    outcome = outcome_of(
        StoryParams(
            setting=setting.id,
            toy=toy.id,
            method=method.id,
            bouncer=bouncer_name,
            bouncer_gender=bouncer_gender,
            watcher=watcher_name,
            watcher_gender=watcher_gender,
            parent=parent_type,
            sharer_trait=sharer_trait,
            wait=wait,
            seed=None,
        )
    )
    if outcome == "snag":
        snag_begins(world, watcher)
        tug(world, watcher)
        repair(world, parent, toy)
        share_plan(world, parent, toy, method, "short")
        sharing_happens(world, bouncer, watcher, toy, method)
    else:
        share_plan(world, parent, toy, method, wait)
        sharing_happens(world, bouncer, watcher, toy, method)

    world.para()
    moral(world, parent, toy, outcome)
    ending(world, bouncer, watcher, toy)

    world.facts.update(
        outcome=outcome,
        fell=world.get("toy").meters["fallen"] >= THRESHOLD,
        shared=world.facts["shared_ready"],
    )
    return world
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


SETTINGS = {
    "nursery": Setting(
        id="nursery",
        place="the nursery",
        opening="In a snug cottage nursery, morning light lay in pale stripes on the floor.",
        perch="a low wall hook",
        affords={"turns", "middle_hang", "twin_knots"},
    ),
    "laundry_room": Setting(
        id="laundry_room",
        place="the laundry room",
        opening="In a warm laundry room behind the kitchen, the air smelled of soap and sunshine.",
        perch="the line where tiny clothes were drying",
        affords={"turns", "middle_hang"},
    ),
    "porch": Setting(
        id="porch",
        place="the porch",
        opening="On a shaded porch, where swallows stitched the air above the herbs, the day began softly.",
        perch="a peg beside the window",
        affords={"turns", "middle_hang", "twin_knots"},
    ),
}

TOYS = {
    "ribbon_streamer": Toy(
        id="ribbon_streamer",
        label="ribbon streamer",
        phrase="the long ribbon streamer",
        color="blue",
        motion="fluttered",
        sound="the faintest hush",
        long=True,
        light=True,
        two_sided=True,
        durable=True,
        tags={"ribbon", "sharing"},
    ),
    "bell_loop": Toy(
        id="bell_loop",
        label="bell loop",
        phrase="the small bell loop",
        color="gold",
        motion="jingled",
        sound="a silver chime",
        long=False,
        light=True,
        two_sided=False,
        durable=True,
        tags={"bell", "sharing"},
    ),
    "paper_fish": Toy(
        id="paper_fish",
        label="paper fish",
        phrase="the bright paper fish",
        color="red",
        motion="spun",
        sound="almost no sound at all",
        long=False,
        light=True,
        two_sided=False,
        durable=False,
        tags={"paper", "sharing"},
    ),
    "cloth_snakes": Toy(
        id="cloth_snakes",
        label="cloth braid",
        phrase="the soft cloth braid",
        color="green",
        motion="twisted",
        sound="a whispery swish",
        long=True,
        light=True,
        two_sided=True,
        durable=True,
        tags={"cloth", "sharing"},
    ),
}

METHODS = {
    "turns": Method(
        id="turns",
        sense=3,
        text='set a gentle rhythm: one pat for one child, then one pat for the other',
        closing="{bouncer} began to watch {watcher}'s delight as gladly as {bouncer} watched the toy itself.",
        qa_text="set short turns so each child could play",
        simultaneous=False,
        tags={"turns", "sharing"},
    ),
    "middle_hang": Method(
        id="middle_hang",
        sense=3,
        text='moved the hanger to the middle so both children could tap the {toy} together',
        closing="Neither child needed to clutch, because the toy belonged to the game they made together.",
        qa_text="moved the hanger so both children could reach the toy together",
        simultaneous=True,
        needs_long=True,
        needs_light=True,
        tags={"hanger", "sharing"},
    ),
    "twin_knots": Method(
        id="twin_knots",
        sense=2,
        text='tied the two ends lower on the hanger so the {toy} offered a side to each small hand',
        closing="Each child had a place, and because each had a place, neither child needed to snatch.",
        qa_text="tied the toy so each child had a side to hold",
        simultaneous=True,
        needs_two_sided=True,
        tags={"hanger", "sharing"},
    ),
    "snatch_back": Method(
        id="snatch_back",
        sense=1,
        text='pulled the toy out of reach and ended the game',
        closing="The room would have gone quiet and cross.",
        qa_text="pulled the toy away from both children",
        simultaneous=False,
        tags={"unkind"},
    ),
}

GIRL_NAMES = ["Mina", "Poppy", "Nell", "Ivy", "Lark", "Tansy", "Wren", "Mabel"]
BOY_NAMES = ["Pip", "Finn", "Rowan", "Otis", "Bram", "Ned", "Kit", "Tobin"]
TRAITS = ["patient", "gentle", "thoughtful", "hasty", "grabby", "restless"]


KNOWLEDGE = {
    "exersaucer": [
        (
            "What is an exersaucer?",
            "An exersaucer is a sturdy baby seat that lets a little child bounce and play while staying in one place. It can hold hanging toys where small hands and feet can reach them.",
        )
    ],
    "hanger": [
        (
            "What is a hanger?",
            "A hanger is a frame used to hold clothes up. In this story, it also works like a little bar to hang a toy from.",
        )
    ],
    "sharing": [
        (
            "Why is sharing good?",
            "Sharing lets more than one person have joy from the same thing. It also helps friends and family feel close instead of cross.",
        )
    ],
    "turns": [
        (
            "What does taking turns mean?",
            "Taking turns means one person goes first and another person goes next. It is a fair way to share when both cannot use the same thing at once.",
        )
    ],
    "patience": [
        (
            "What is patience?",
            "Patience is the calm skill of waiting without grabbing or shouting. It gives good choices time to grow.",
        )
    ],
}
KNOWLEDGE_ORDER = ["exersaucer", "hanger", "sharing", "turns", "patience"]
@dataclass
class StoryParams:
    setting: str
    toy: str
    method: str
    bouncer: str
    bouncer_gender: str
    watcher: str
    watcher_gender: str
    parent: str
    sharer_trait: str
    wait: str = "short"
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        setting="nursery",
        toy="ribbon_streamer",
        method="middle_hang",
        bouncer="Mina",
        bouncer_gender="girl",
        watcher="Pip",
        watcher_gender="boy",
        parent="mother",
        sharer_trait="gentle",
        wait="short",
        seed=1,
    ),
    StoryParams(
        setting="porch",
        toy="cloth_snakes",
        method="twin_knots",
        bouncer="Poppy",
        bouncer_gender="girl",
        watcher="Finn",
        watcher_gender="boy",
        parent="father",
        sharer_trait="thoughtful",
        wait="short",
        seed=2,
    ),
    StoryParams(
        setting="laundry_room",
        toy="bell_loop",
        method="turns",
        bouncer="Nell",
        bouncer_gender="girl",
        watcher="Otis",
        watcher_gender="boy",
        parent="mother",
        sharer_trait="patient",
        wait="long",
        seed=3,
    ),
    StoryParams(
        setting="nursery",
        toy="paper_fish",
        method="turns",
        bouncer="Kit",
        bouncer_gender="boy",
        watcher="Ivy",
        watcher_gender="girl",
        parent="father",
        sharer_trait="grabby",
        wait="long",
        seed=4,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    toy = f["toy_cfg"]
    method = f["method"]
    bouncer = f["bouncer"]
    watcher = f["watcher"]
    outcome = f["outcome"]
    if outcome == "snag":
        return [
            'Write a gentle fable for a small child about sharing that includes the words "exersaucer" and "hanger".',
            f"Tell a fable where {bouncer.id} plays with a {toy.label} above an exersaucer, {watcher.id} grows impatient while waiting, and a wise grown-up teaches both children how sharing restores joy.",
            f"Write a nursery fable with a small mistake, a repair, and a moral about patience and sharing.",
        ]
    return [
        'Write a gentle fable for a small child about sharing that includes the words "exersaucer" and "hanger".',
        f"Tell a fable where a bright toy hangs from a hanger above an exersaucer, and two children learn to share it kindly.",
        f"Write a short story in a fable style where {method.id.replace('_', ' ')} helps two children turn one merry toy into joy for both.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    bouncer = f["bouncer"]
    watcher = f["watcher"]
    parent = f["parent"]
    toy = f["toy_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {bouncer.id} and {watcher.id}, two little children, and their {pw} who helped them. One child was in the exersaucer while the other longed to join the game.",
        ),
        (
            f"What was hanging from the hanger?",
            f"{toy.phrase.capitalize()} was hanging from the hanger above the exersaucer. It caught the children's eyes because it moved and made {toy.sound}.",
        ),
        (
            f"Why did {watcher.id} feel sad at first?",
            f"{watcher.id} wanted to play too, but {bouncer.id} pulled the toy close and said it was for {bouncer.pronoun('object')} alone. That made the game feel lonely instead of shared.",
        ),
    ]
    if outcome == "smooth":
        qa.append(
            (
                f"How did their {pw} solve the problem?",
                f"Their {pw} {method.qa_text}. That plan fit the toy and let both children join the play fairly.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully, with both children laughing at the same bright dance. The ending shows that sharing made the toy seem merrier than before.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {watcher.id} stopped waiting patiently?",
                f"{watcher.id} tugged the hanger, and the toy fell down. The sudden fall startled both children and showed how impatience can spoil joy for everyone.",
            )
        )
        qa.append(
            (
                f"What did their {pw} do after the toy fell?",
                f"Their {pw} picked the toy up, hung it back, and made a kinder sharing plan with short turns. The repair mattered because it turned a mistake into a lesson both children could use right away.",
            )
        )
        qa.append(
            (
                "What was the lesson of the fable?",
                f"The lesson was that grasping and tugging drive happiness away, but patience and sharing bring it back. The room only grew merry again after the children stopped trying to keep all the joy to themselves.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"exersaucer", "hanger", "sharing"}
    method = world.facts["method"]
    if method.id == "turns":
        tags.add("turns")
    if world.facts["outcome"] == "snag" or world.facts["wait"] == "long":
        tags.add("patience")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(M) :- method(M), sense(M,S), sense_min(Min), S >= Min.

compatible(T, turns) :- toy(T).
compatible(T, middle_hang) :- toy(T), long(T), light(T).
compatible(T, twin_knots) :- toy(T), two_sided(T).

valid(S, T, M) :- setting(S), toy(T), method(M), sensible(M), affords(S, M), compatible(T, M).

smooth :- chosen_method(M), simultaneous(M).
smooth :- chosen_method(turns), wait(short).
patient_now :- sharer_trait(T), patient_trait(T).
smooth :- chosen_method(turns), wait(long), patient_now.

outcome(smooth) :- smooth.
outcome(snag) :- not smooth.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for mid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, mid))
    for tid, toy in TOYS.items():
        lines.append(asp.fact("toy", tid))
        if toy.long:
            lines.append(asp.fact("long", tid))
        if toy.light:
            lines.append(asp.fact("light", tid))
        if toy.two_sided:
            lines.append(asp.fact("two_sided", tid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        if method.simultaneous:
            lines.append(asp.fact("simultaneous", mid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(PATIENT_TRAITS):
        lines.append(asp.fact("patient_trait", trait))
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
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_method", params.method),
            asp.fact("wait", params.wait),
            asp.fact("sharer_trait", params.sharer_trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small fable-like sharing world with an exersaucer and a hanger."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--wait", choices=["short", "long"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(args.method))
    if args.setting and args.toy and args.method:
        setting = SETTINGS[args.setting]
        toy = TOYS[args.toy]
        method = METHODS[args.method]
        if not (method.id in setting.affords and method_compatible(toy, method) and method.sense >= SENSE_MIN):
            raise StoryError(explain_combo_rejection(setting, toy, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.toy is None or combo[1] == args.toy)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, toy_id, method_id = rng.choice(combos)
    bouncer, bouncer_gender = _pick_child(rng)
    watcher, watcher_gender = _pick_child(rng, avoid=bouncer)
    parent = args.parent or rng.choice(["mother", "father"])
    wait = args.wait or rng.choice(["short", "long"])
    sharer_trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        toy=toy_id,
        method=method_id,
        bouncer=bouncer,
        bouncer_gender=bouncer_gender,
        watcher=watcher,
        watcher_gender=watcher_gender,
        parent=parent,
        sharer_trait=sharer_trait,
        wait=wait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.toy not in TOYS:
        raise StoryError(f"(Unknown toy: {params.toy})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if params.wait not in {"short", "long"}:
        raise StoryError(f"(Unknown wait length: {params.wait})")

    setting = SETTINGS[params.setting]
    toy = TOYS[params.toy]
    method = METHODS[params.method]
    if method.sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(params.method))
    if not (method.id in setting.affords and method_compatible(toy, method)):
        raise StoryError(explain_combo_rejection(setting, toy, method))

    world = tell(
        setting,
        toy,
        method,
        bouncer_name=params.bouncer,
        bouncer_gender=params.bouncer_gender,
        watcher_name=params.watcher,
        watcher_gender=params.watcher_gender,
        parent_type=params.parent,
        sharer_trait=params.sharer_trait,
        wait=params.wait,
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
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

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
    parser = build_parser()
    for s in range(50):
        try:
            ns = parser.parse_args([])
            p = resolve_params(ns, random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            break
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show sensible/1.\n#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, toy, method) combos:\n")
        for setting, toy, method in combos:
            print(f"  {setting:13} {toy:16} {method}")
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
            header = f"### {p.setting}: {p.toy} with {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
