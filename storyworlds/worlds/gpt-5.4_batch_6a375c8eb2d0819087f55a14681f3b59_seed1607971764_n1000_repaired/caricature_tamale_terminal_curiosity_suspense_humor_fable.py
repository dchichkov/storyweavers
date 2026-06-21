#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/caricature_tamale_terminal_curiosity_suspense_humor_fable.py
=======================================================================================

A standalone story world for a small fable-shaped tale about curiosity at a
terminal: a young animal artist draws a silly caricature while waiting, notices
a mysterious tamale parcel, and learns that asking is wiser than meddling.

The domain is intentionally small and constraint-checked. Different terminals,
parcel types, and ways of satisfying curiosity all lead to different but
plausible stories. Some explicit choices are rejected when they are not
reasonable for the chosen parcel.

Run it
------
    python storyworlds/worlds/gpt-5.4/caricature_tamale_terminal_curiosity_suspense_humor_fable.py
    python storyworlds/worlds/gpt-5.4/caricature_tamale_terminal_curiosity_suspense_humor_fable.py --terminal ferry --parcel basket --method peek_cloth
    python storyworlds/worlds/gpt-5.4/caricature_tamale_terminal_curiosity_suspense_humor_fable.py --parcel tin --method peek_cloth
    python storyworlds/worlds/gpt-5.4/caricature_tamale_terminal_curiosity_suspense_humor_fable.py --all
    python storyworlds/worlds/gpt-5.4/caricature_tamale_terminal_curiosity_suspense_humor_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/caricature_tamale_terminal_curiosity_suspense_humor_fable.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/caricature_tamale_terminal_curiosity_suspense_humor_fable.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "goose", "cat"}
        male = {"boy", "father", "fox", "frog", "bear", "crow"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
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
class Terminal:
    id: str
    label: str
    waiting_line: str
    call: str
    floor: str
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
class Parcel:
    id: str
    label: str
    phrase: str
    closure: str
    clue_sound: str
    reveal: str
    risk: str
    wobble: int
    heat: int
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
    label: str
    sense: int
    works_on: set[str]
    style: str
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


class World:
    def __init__(self, terminal: Terminal) -> None:
        self.terminal = terminal
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
        clone = World(self.terminal)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_basket_spill(world: World) -> list[str]:
    parcel = world.get("parcel")
    if parcel.attrs.get("parcel_kind") != "basket" or parcel.meters["disturbed"] < THRESHOLD:
        return []
    sig = ("basket_spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    parcel.meters["spilled"] += parcel.attrs.get("wobble", 1)
    world.get("terminal").meters["mess"] += 1
    world.get("hero").memes["alarm"] += 1
    world.get("hero").memes["embarrassment"] += 1
    return ["__spill__"]


def _r_steamer_puff(world: World) -> list[str]:
    parcel = world.get("parcel")
    if parcel.attrs.get("parcel_kind") != "steamer" or parcel.meters["disturbed"] < THRESHOLD:
        return []
    sig = ("steamer_puff",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    parcel.meters["steam"] += max(1, parcel.attrs.get("heat", 1))
    world.get("terminal").meters["surprise"] += 1
    world.get("hero").memes["alarm"] += 1
    world.get("friend").memes["alarm"] += 1
    return ["__steam__"]


def _r_tin_clang(world: World) -> list[str]:
    parcel = world.get("parcel")
    if parcel.attrs.get("parcel_kind") != "tin" or parcel.meters["disturbed"] < THRESHOLD:
        return []
    sig = ("tin_clang",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    parcel.meters["clang"] += 1
    world.get("terminal").meters["noise"] += 1
    world.get("hero").memes["embarrassment"] += 1
    world.get("hero").memes["alarm"] += 1
    return ["__clang__"]


CAUSAL_RULES = [
    Rule(name="basket_spill", tag="physical", apply=_r_basket_spill),
    Rule(name="steamer_puff", tag="physical", apply=_r_steamer_puff),
    Rule(name="tin_clang", tag="physical", apply=_r_tin_clang),
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


def method_fits(parcel: Parcel, method: Method) -> bool:
    return parcel.id in method.works_on


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for terminal_id in TERMINALS:
        for parcel_id, parcel in PARCELS.items():
            for method_id, method in METHODS.items():
                if method.sense >= SENSE_MIN and method_fits(parcel, method):
                    combos.append((terminal_id, parcel_id, method_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.method == "ask_vendor":
        return "shared"
    if params.method == "peek_cloth":
        return "spilled"
    if params.method == "lift_lid":
        return "puffed"
    if params.method == "unlatch":
        return "clang"
    return "?"


def explain_method_rejection(parcel: Parcel, method: Method) -> str:
    if method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_methods()))
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). A fable should prefer a wiser, "
            f"clearer choice. Try one of: {better}.)"
        )
    return (
        f"(No story: {method.label} does not fit {parcel.phrase}. Its {parcel.closure} "
        f"cannot honestly be handled that way, so the curiosity beat would feel false.)"
    )


def predict_trouble(world: World, method: Method) -> dict:
    sim = world.copy()
    parcel = sim.get("parcel")
    if method.id != "ask_vendor":
        parcel.meters["disturbed"] += 1
        propagate(sim, narrate=False)
    return {
        "spill": parcel.meters["spilled"],
        "steam": parcel.meters["steam"],
        "clang": parcel.meters["clang"],
        "mess": sim.get("terminal").meters["mess"],
        "noise": sim.get("terminal").meters["noise"],
    }


def introduce(world: World, hero: Entity, friend: Entity, terminal: Terminal) -> None:
    hero.memes["joy"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"At {terminal.label}, {hero.id} waited beside {friend.id} and tried to make the long line feel shorter."
    )
    world.say(
        f"To pass the time, {hero.pronoun()} drew a caricature of the ticket clerk with a hat so tall it nearly bumped the hanging clock."
    )
    world.say(
        f"{terminal.waiting_line} Every few breaths, {terminal.call}"
    )


def notice_parcel(world: World, hero: Entity, friend: Entity, parcel: Parcel) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Then a smell drifted over them: warm corn, soft spice, and one very tempting tamale tucked inside {parcel.phrase}."
    )
    world.say(
        f"From inside came {parcel.clue_sound}. {friend.id} blinked, and even {hero.id} stopped drawing long enough to listen."
    )


def wonder(world: World, hero: Entity, parcel: Parcel, method: Method) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'"Who is making that funny little sound?" {hero.id} whispered. '
        f'The parcel looked as innocent as a nap on a bench, which only made {hero.pronoun("possessive")} curiosity hop harder.'
    )
    if method.id == "ask_vendor":
        world.say(
            f'{hero.id} licked {hero.pronoun("possessive")} lips and admitted that the smell of tamale and the mystery together were almost too much for {hero.pronoun("object")}.'
        )
    else:
        world.say(
            f'{hero.id} leaned a little closer, as if the parcel might tell its secret to one bold nose and not to the whole terminal.'
        )


def warn(world: World, friend: Entity, hero: Entity, method: Method) -> None:
    pred = predict_trouble(world, method)
    world.facts["prediction"] = pred
    friend.memes["caution"] += 1
    if method.id == "ask_vendor":
        world.say(
            f'"If you truly want to know," {friend.id} said, "ask. Questions open doors more gently than paws do."'
        )
        return
    if pred["spill"] >= THRESHOLD:
        world.say(
            f'"Careful," {friend.id} murmured. "That looks wobbly. One little {method.style}, and lunch may go skating across the floor."'
        )
    elif pred["steam"] >= THRESHOLD:
        world.say(
            f'"Careful," {friend.id} murmured. "That pot is hot. One little {method.style}, and the answer may leap up at your nose in a cloud."'
        )
    elif pred["clang"] >= THRESHOLD:
        world.say(
            f'"Careful," {friend.id} murmured. "That tin is the sort that shouts when surprised. One little {method.style}, and the whole terminal may listen."'
        )


def choose(world: World, hero: Entity, method: Method) -> None:
    if method.id == "ask_vendor":
        hero.memes["restraint"] += 1
        world.say(
            f"So {hero.id} put the charcoal stub behind {hero.pronoun('possessive')} ear, straightened up, and chose the brave kind of curiosity."
        )
    else:
        hero.memes["mischief"] += 1
        world.say(
            f"But curiosity in a hurry can sound very much like wisdom in a costume, and {hero.id} let it tug {hero.pronoun('object')} one step closer."
        )


def do_ask(world: World, vendor: Entity, hero: Entity, parcel: Parcel) -> None:
    vendor.memes["patience"] += 1
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    vendor.memes["generosity"] += 1
    world.say(
        f'{hero.id} cleared {hero.pronoun("possessive")} throat and asked the tamale seller, "{vendor.id}, what is making that tiny sound?"'
    )
    world.say(
        f'{vendor.id} smiled, lifted {parcel.closure}, and revealed {parcel.reveal}.'
    )
    world.say(
        f'"Only my spoon tapping the warm side," {vendor.pronoun()} chuckled. "Even a tamale likes to travel with company."'
    )


def do_disturb(world: World, hero: Entity, method: Method) -> None:
    parcel = world.get("parcel")
    parcel.meters["disturbed"] += 1
    propagate(world, narrate=False)
    if method.id == "peek_cloth":
        world.say(
            f'{hero.id} gave the cloth the tiniest peek, just one careful pinch.'
        )
    elif method.id == "lift_lid":
        world.say(
            f'{hero.id} lifted the lid a finger-width, trying to be quick as a whisper.'
        )
    elif method.id == "unlatch":
        world.say(
            f'{hero.id} clicked the latch loose, certain that a secret small enough to hide in a tin could not possibly make a big fuss.'
        )


def narrate_turn(world: World, hero: Entity, friend: Entity, vendor: Entity, parcel: Parcel, terminal: Terminal) -> None:
    if parcel.meters["spilled"] >= THRESHOLD:
        hero.memes["lesson"] += 1
        vendor.memes["patience"] += 1
        vendor.memes["generosity"] += 1
        world.say(
            f"At once the basket tipped, and two tamales rolled out like plump little logs escaping a hill."
        )
        world.say(
            f"One bumped the leg of a bench, one spun across {terminal.floor}, and {hero.id} had to chase both while {friend.id} tried not to laugh and gasp at the same time."
        )
        world.say(
            f'{vendor.id} hurried over, but when {hero.id} gathered the runaway tamales with hot cheeks and both paws full, {vendor.pronoun()} only said, "A question would have cost less running."'
        )
    elif parcel.meters["steam"] >= THRESHOLD:
        hero.memes["lesson"] += 1
        vendor.memes["patience"] += 1
        vendor.memes["generosity"] += 1
        world.say(
            f"A white puff of steam sprang up so suddenly that {hero.id} hopped backward and slapped the caricature paper right onto {hero.pronoun('possessive')} own face."
        )
        world.say(
            f"For one splendid moment, the terminal held its breath; then {friend.id} peeled the drawing away and discovered that the steam had curled the paper so the ticket clerk now wore an even sillier nose."
        )
        world.say(
            f'{vendor.id} came over laughing softly. "Hot secrets jump," {vendor.pronoun()} said. "Warm food does not like sneaky fingers."'
        )
    elif parcel.meters["clang"] >= THRESHOLD:
        hero.memes["lesson"] += 1
        vendor.memes["patience"] += 1
        vendor.memes["generosity"] += 1
        world.say(
            f"The lid flew open with a bright clang as the spoon inside struck the side, and half the waiting line looked up as if the departure bell had spoken early."
        )
        world.say(
            f"Three geese shuffled toward the wrong gate, and one old mole bowed to nobody at all before noticing the mistake."
        )
        world.say(
            f'{vendor.id} trotted back, saw {hero.id} frozen beside the open tin, and said with a twinkle, "Well, little artist, you have sketched yourself into the joke."'
        )


def repair_and_share(world: World, hero: Entity, friend: Entity, vendor: Entity, parcel: Parcel) -> None:
    hero.memes["embarrassment"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    friend.memes["relief"] += 1
    vendor.memes["generosity"] += 1
    if parcel.id == "basket":
        world.say(
            f"{hero.id} apologized, set the tamales back in order, and smoothed the cloth flat again."
        )
    elif parcel.id == "steamer":
        world.say(
            f"{hero.id} apologized and stepped back until the steam thinned into a harmless ribbon."
        )
    else:
        world.say(
            f"{hero.id} apologized, closed the tin, and helped point the wandering geese back to the proper line."
        )
    world.say(
        f"{vendor.id} saw that the lesson had already landed, so {vendor.pronoun()} broke one extra tamale in half and shared it between {hero.id} and {friend.id}."
    )
    world.say(
        f"It tasted better after honesty, and much less noisy too."
    )


def closing(world: World, hero: Entity, friend: Entity, terminal: Terminal, outcome: str) -> None:
    hero.memes["joy"] += 1
    if outcome == "shared":
        world.say(
            f"When the next call echoed through {terminal.label}, {hero.id} tucked the caricature into {hero.pronoun('possessive')} satchel and drew a new one beneath it: the same clerk, but kinder around the eyes."
        )
        world.say(
            f"From then on, whenever curiosity pricked {hero.pronoun('object')}, {hero.pronoun()} tried a question before a paw."
        )
    else:
        world.say(
            f"When the next call echoed through {terminal.label}, {hero.id} tucked away the crooked caricature and kept one warm piece of tamale in mind along with the lesson."
        )
        world.say(
            f"And from that day, {hero.pronoun()} remembered that curiosity can make a joke, but asking first keeps the joke from becoming trouble."
        )
def tell(
    parcel_cfg: Parcel,
    method: Method,
    hero_name: str,
    hero_type: HeroType,
    friend_name: str,
    friend_type: FriendType,
    vendor_type: VendorType,
    trait: Trait,
    terminal=None,
) -> World:
    world = World(terminal=terminal)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_type,
        label=friend_name,
        role="friend",
        traits=["careful"],
        attrs={},
    ))
    vendor = world.add(Entity(
        id="Toma",
        kind="character",
        type=vendor_type,
        label="the seller",
        role="vendor",
        traits=["patient"],
        attrs={},
    ))
    terminal_ent = world.add(Entity(
        id="terminal",
        kind="thing",
        type="terminal",
        label=terminal.label,
        attrs={},
    ))
    parcel = world.add(Entity(
        id="parcel",
        kind="thing",
        type="parcel",
        label=parcel_cfg.label,
        attrs={
            "parcel_kind": parcel_cfg.id,
            "closure": parcel_cfg.closure,
            "wobble": parcel_cfg.wobble,
            "heat": parcel_cfg.heat,
        },
    ))

    # Initialize meters/memes read by rules before any propagation.
    parcel.meters["disturbed"] = 0.0
    parcel.meters["spilled"] = 0.0
    parcel.meters["steam"] = 0.0
    parcel.meters["clang"] = 0.0
    terminal_ent.meters["mess"] = 0.0
    terminal_ent.meters["noise"] = 0.0
    terminal_ent.meters["surprise"] = 0.0
    hero.memes["alarm"] = 0.0
    hero.memes["embarrassment"] = 0.0
    hero.memes["lesson"] = 0.0
    hero.memes["curiosity"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["gratitude"] = 0.0
    friend.memes["alarm"] = 0.0
    friend.memes["relief"] = 0.0
    vendor.memes["generosity"] = 0.0
    vendor.memes["patience"] = 0.0

    introduce(world, hero, friend, terminal)
    notice_parcel(world, hero, friend, parcel_cfg)

    world.para()
    wonder(world, hero, parcel_cfg, method)
    warn(world, friend, hero, method)
    choose(world, hero, method)

    world.para()
    if method.id == "ask_vendor":
        do_ask(world, vendor, hero, parcel_cfg)
        outcome = "shared"
    else:
        do_disturb(world, hero, method)
        narrate_turn(world, hero, friend, vendor, parcel, terminal)
        world.para()
        repair_and_share(world, hero, friend, vendor, parcel)
        outcome = outcome_of(StoryParams(
            terminal=terminal.id,
            parcel=parcel_cfg.id,
            method=method.id,
            hero=hero_name,
            hero_type=hero_type,
            friend=friend_name,
            friend_type=friend_type,
            vendor_type=vendor_type,
            trait=trait,
            seed=None,
        ))

    world.para()
    closing(world, hero, friend, terminal, outcome)

    world.facts.update(
        hero=hero,
        friend=friend,
        vendor=vendor,
        terminal_cfg=terminal,
        parcel_cfg=parcel_cfg,
        parcel=parcel,
        method=method,
        outcome=outcome,
        shared=vendor.memes["generosity"] >= THRESHOLD,
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


TERMINALS = {
    "bus": Terminal(
        id="bus",
        label="the dusty bus terminal",
        waiting_line="Suitcases leaned like sleepy cows along the wall.",
        call="a driver called destinations in a voice like a brass trumpet.",
        floor="the dusty tiles",
        tags={"terminal", "travel"},
    ),
    "ferry": Terminal(
        id="ferry",
        label="the windy ferry terminal",
        waiting_line="Ropes knocked softly against posts outside, and travel trunks waited in a neat row.",
        call="the dock bell rang and a deckhand called for boarding papers.",
        floor="the salt-damp boards",
        tags={"terminal", "travel", "water"},
    ),
    "train": Terminal(
        id="train",
        label="the echoing train terminal",
        waiting_line="Boots and bundles made a tidy forest of waiting by the benches.",
        call="a porter sang out the next platform under the great iron roof.",
        floor="the shiny stone floor",
        tags={"terminal", "travel", "train"},
    ),
}

PARCELS = {
    "basket": Parcel(
        id="basket",
        label="basket",
        phrase="a cloth-covered basket",
        closure="a loose cloth cover",
        clue_sound="a rustle and a tiny tap from a spoon hidden beside the food",
        reveal="a neat row of tamales wrapped in husks, with a spoon bumping the basket each time the seller shifted the tray",
        risk="tip and spill",
        wobble=2,
        heat=0,
        tags={"tamale", "basket"},
    ),
    "steamer": Parcel(
        id="steamer",
        label="steamer",
        phrase="a round little steamer pot",
        closure="a warm lid with a knob",
        clue_sound="a whispery whistle where the steam squeezed out",
        reveal="a stack of tamales resting in fragrant steam",
        risk="puff hot steam",
        wobble=0,
        heat=2,
        tags={"tamale", "steam"},
    ),
    "tin": Parcel(
        id="tin",
        label="tin",
        phrase="a painted lunch tin",
        closure="a bright metal latch",
        clue_sound="a tiny clink from a spoon tapping the side whenever the bench shook",
        reveal="one wrapped tamale, a folded napkin, and a spoon that had been making all the mystery",
        risk="clang loudly",
        wobble=0,
        heat=0,
        tags={"tamale", "tin"},
    ),
}

METHODS = {
    "ask_vendor": Method(
        id="ask_vendor",
        label="ask the seller",
        sense=3,
        works_on={"basket", "steamer", "tin"},
        style="question",
        tags={"ask", "curiosity"},
    ),
    "peek_cloth": Method(
        id="peek_cloth",
        label="peek under the cloth",
        sense=2,
        works_on={"basket"},
        style="peek",
        tags={"peek", "basket"},
    ),
    "lift_lid": Method(
        id="lift_lid",
        label="lift the lid",
        sense=2,
        works_on={"steamer"},
        style="lid-lift",
        tags={"steam", "peek"},
    ),
    "unlatch": Method(
        id="unlatch",
        label="unlatch the tin",
        sense=2,
        works_on={"tin"},
        style="click",
        tags={"tin", "peek"},
    ),
    "shake": Method(
        id="shake",
        label="shake the parcel",
        sense=1,
        works_on={"basket", "steamer", "tin"},
        style="shake",
        tags={"bad_idea"},
    ),
}

FOX_NAMES = ["Pico", "Rufus", "Tavi", "Milo", "Nico"]
HEN_NAMES = ["Mina", "Pru", "Della", "Nell", "Lark"]
BEAR_NAMES = ["Toma", "Bram", "Marta", "Oso"]
TRAITS = ["nosy", "bright-eyed", "restless", "eager", "playful"]


KNOWLEDGE = {
    "terminal": [
        (
            "What is a terminal?",
            "A terminal is a place where trips begin or end, like for buses, trains, or ferries. People wait there, listen for calls, and carry bags from one place to another.",
        )
    ],
    "tamale": [
        (
            "What is a tamale?",
            "A tamale is food wrapped up for cooking, often in a corn husk or leaf. It stays warm inside its wrapping, which is why it can smell delicious before you open it.",
        )
    ],
    "caricature": [
        (
            "What is a caricature?",
            "A caricature is a funny drawing that makes one or two features bigger or sillier on purpose. People use caricatures to make others laugh, not to tell exact details.",
        )
    ],
    "steam": [
        (
            "Why does hot food make steam?",
            "Steam is water turning into warm vapor when something is very hot. That is why a covered pot can puff when you lift the lid.",
        )
    ],
    "ask": [
        (
            "Why is asking first a good idea?",
            "Asking first helps you learn without making a mess or touching something that is not yours. Questions can satisfy curiosity in a safe and polite way.",
        )
    ],
}
KNOWLEDGE_ORDER = ["terminal", "tamale", "caricature", "steam", "ask"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    terminal = f["terminal_cfg"]
    parcel = f["parcel_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    base = (
        f'Write a short fable for a 3-to-5-year-old set in {terminal.label} that uses the words "caricature", "tamale", and "terminal".'
    )
    if outcome == "shared":
        return [
            base,
            f"Tell a gentle, humorous story where {hero.id} grows curious about {parcel.phrase}, asks politely, and discovers the harmless reason for the sound.",
            f"Write a fable about wise curiosity: an animal artist at a terminal draws a caricature, smells a tamale, and learns that questions work better than meddling.",
        ]
    if outcome == "spilled":
        return [
            base,
            f"Tell a humorous fable where {hero.id} peeks under a cloth-covered tamale basket, causes a small spill, and learns a lesson about asking first.",
            f"Write a suspenseful but gentle story where a mysterious sound at a terminal tempts a childlike animal to meddle, but the ending turns kind and funny.",
        ]
    if outcome == "puffed":
        return [
            base,
            f"Tell a humorous fable where {hero.id} lifts the lid of a steamer, gets surprised by steam, and learns that hot secrets jump.",
            f"Write a child-friendly terminal story with curiosity, suspense, and a soft lesson about not touching hot food that is not yours.",
        ]
    return [
        base,
        f"Tell a funny fable where {hero.id} unlatches a tin at a terminal, the noise startles everyone, and kindness turns embarrassment into a lesson.",
        f"Write a story with suspense and humor where a tamale tin makes the wrong sound at the wrong moment, and an animal hero learns to ask first.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    vendor = f["vendor"]
    terminal = f["terminal_cfg"]
    parcel_cfg = f["parcel_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    parcel = f["parcel"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was waiting at {terminal.label} with {friend.id}. While waiting, {hero.pronoun()} drew a caricature and then became curious about a tamale parcel.",
        ),
        (
            "What made the hero curious?",
            f"The warm smell of tamale and the odd little sound from {parcel_cfg.phrase} made {hero.id} curious. The mystery felt bigger because the parcel looked ordinary while sounding secretive.",
        ),
        (
            f"What warning did {friend.id} give?",
            _warning_answer(world),
        ),
    ]
    if outcome == "shared":
        qa.append(
            (
                f"How did {hero.id} solve the mystery?",
                f"{hero.id} asked the seller instead of touching the parcel. The seller opened it and showed that the tiny sound was harmless, so curiosity was satisfied without trouble.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with laughter, a shared bite of tamale, and a calmer heart. {hero.id} learned that a question can travel farther than sneaky paws.",
            )
        )
    elif outcome == "spilled":
        qa.append(
            (
                f"What happened when {hero.id} used {method.label}?",
                f"The basket tipped and the tamales rolled away. The trouble came from touching a wobbly parcel instead of asking about it first.",
            )
        )
        qa.append(
            (
                f"Why did the seller still share food with {hero.id}?",
                f"The seller could see that {hero.id} was sorry and helped fix the mess. Kindness turned the embarrassing moment into a lesson instead of a scolding.",
            )
        )
    elif outcome == "puffed":
        qa.append(
            (
                f"What happened when {hero.id} lifted the lid?",
                f"A puff of steam jumped up and startled {hero.id}. Because the parcel was hot, the answer came out as a cloud before anyone could explain it.",
            )
        )
        qa.append(
            (
                "Why is this story funny after the scare?",
                f"It becomes funny because the steam curls the drawing and makes the caricature even sillier. The fright passes quickly, and everyone can laugh once the danger is gone.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} opened the tin?",
                f"The spoon struck the side with a loud clang, so people thought a signal had been given. One small curious action caused a big noisy misunderstanding.",
            )
        )
        qa.append(
            (
                "How was the problem fixed?",
                f"{hero.id} apologized, shut the tin, and helped straighten the line again. The seller answered with humor and kindness, which made the lesson easier to keep.",
            )
        )
    return qa


def _warning_answer(world: World) -> str:
    f = world.facts
    friend = f["friend"]
    method = f["method"]
    pred = f.get("prediction", {})
    if method.id == "ask_vendor":
        return (
            f'{friend.id} said that asking was the gentlest way to satisfy curiosity. That advice mattered because a polite question could reveal the truth without making a mess or a scene.'
        )
    if pred.get("spill", 0) >= THRESHOLD:
        return (
            f'{friend.id} warned that the basket looked wobbly and that peeking might send lunch sliding away. The warning was grounded in the parcel itself, not just in fear.'
        )
    if pred.get("steam", 0) >= THRESHOLD:
        return (
            f'{friend.id} warned that the steamer was hot and that lifting the lid could send steam right at {f["hero"].id}. The warning connected the mystery to a real physical risk.'
        )
    return (
        f'{friend.id} warned that the tin might make a loud sound if it was opened carelessly. That mattered because one noisy surprise in a terminal can confuse many people at once.'
    )


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"terminal", "tamale", "caricature", "ask"}
    if world.facts["parcel_cfg"].id == "steamer":
        tags.add("steam")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    terminal: str
    parcel: str
    method: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    vendor_type: str
    trait: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        terminal="bus",
        parcel="basket",
        method="peek_cloth",
        hero="Pico",
        hero_type="fox",
        friend="Mina",
        friend_type="hen",
        vendor_type="bear",
        trait="nosy",
        seed=None,
    ),
    StoryParams(
        terminal="ferry",
        parcel="steamer",
        method="lift_lid",
        hero="Rufus",
        hero_type="fox",
        friend="Pru",
        friend_type="hen",
        vendor_type="bear",
        trait="bright-eyed",
        seed=None,
    ),
    StoryParams(
        terminal="train",
        parcel="tin",
        method="unlatch",
        hero="Tavi",
        hero_type="fox",
        friend="Della",
        friend_type="hen",
        vendor_type="bear",
        trait="eager",
        seed=None,
    ),
    StoryParams(
        terminal="bus",
        parcel="steamer",
        method="ask_vendor",
        hero="Milo",
        hero_type="fox",
        friend="Nell",
        friend_type="hen",
        vendor_type="bear",
        trait="restless",
        seed=None,
    ),
]


ASP_RULES = r"""
sensible_method(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
compatible(P, M) :- parcel(P), method(M), works_on(M, P).
valid(T, P, M) :- terminal(T), parcel(P), sensible_method(M), compatible(P, M).

outcome(shared) :- chosen_method(ask_vendor).
outcome(spilled) :- chosen_method(peek_cloth).
outcome(puffed) :- chosen_method(lift_lid).
outcome(clang) :- chosen_method(unlatch).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in TERMINALS:
        lines.append(asp.fact("terminal", tid))
    for pid in PARCELS:
        lines.append(asp.fact("parcel", pid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        for pid in sorted(method.works_on):
            lines.append(asp.fact("works_on", mid, pid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_method", params.method)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: ASP outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: curiosity, a tamale parcel, and a terminal fable."
    )
    ap.add_argument("--terminal", choices=TERMINALS)
    ap.add_argument("--parcel", choices=PARCELS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.parcel and args.method:
        parcel = PARCELS[args.parcel]
        method = METHODS[args.method]
        if not method_fits(parcel, method) or method.sense < SENSE_MIN:
            raise StoryError(explain_method_rejection(parcel, method))
    if args.method and args.method in METHODS and METHODS[args.method].sense < SENSE_MIN:
        parcel = PARCELS[args.parcel] if args.parcel else next(iter(PARCELS.values()))
        raise StoryError(explain_method_rejection(parcel, METHODS[args.method]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.terminal is None or combo[0] == args.terminal)
        and (args.parcel is None or combo[1] == args.parcel)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    terminal_id, parcel_id, method_id = rng.choice(sorted(combos))
    hero = rng.choice(FOX_NAMES)
    friend = rng.choice([n for n in HEN_NAMES if n != hero])
    vendor_type = "bear"
    trait = rng.choice(TRAITS)
    return StoryParams(
        terminal=terminal_id,
        parcel=parcel_id,
        method=method_id,
        hero=hero,
        hero_type="fox",
        friend=friend,
        friend_type="hen",
        vendor_type=vendor_type,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        terminal = TERMINALS[params.terminal]
        parcel = PARCELS[params.parcel]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err.args[0]})") from None

    if not method_fits(parcel, method) or method.sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(parcel, method))

    world = tell(
        terminal=terminal,
        parcel_cfg=parcel,
        method=method,
        hero_name=params.hero,
        hero_type=params.hero_type,
        friend_name=params.friend,
        friend_type=params.friend_type,
        vendor_type=params.vendor_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (terminal, parcel, method) combos:\n")
        for terminal, parcel, method in combos:
            print(f"  {terminal:8} {parcel:8} {method}")
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
            header = f"### {p.hero}: {p.method} with {p.parcel} at {p.terminal} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
