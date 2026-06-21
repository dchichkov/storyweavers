#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/damn_sill_teamwork_humor_pirate_tale.py
==================================================================

A small story world for a funny pirate-style teamwork tale.

Two children are playing pirates indoors. Their pretend treasure gets stranded
on a high window sill. One child is tempted to climb a wobbly stool alone, but
the other child predicts the wobble and pushes the crew toward a better plan.
They rescue the treasure together, laugh at a silly pirate squawk that includes
the word "damn", and end with a new crew rule: pirates use teamwork instead of
lone lunges.

Run it
------
    python storyworlds/worlds/gpt-5.4/damn_sill_teamwork_humor_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/damn_sill_teamwork_humor_pirate_tale.py --treasure shell_pouch
    python storyworlds/worlds/gpt-5.4/damn_sill_teamwork_humor_pirate_tale.py --method blanket_catch
    python storyworlds/worlds/gpt-5.4/damn_sill_teamwork_humor_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/damn_sill_teamwork_humor_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/damn_sill_teamwork_humor_pirate_tale.py --trace
    python storyworlds/worlds/gpt-5.4/damn_sill_teamwork_humor_pirate_tale.py --json
    python storyworlds/worlds/gpt-5.4/damn_sill_teamwork_humor_pirate_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    weight: int
    has_loop: bool
    soft: bool
    longish: bool = False
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
    max_weight: int
    needs_loop: bool
    needs_soft: bool
    requires_helper_hold: bool
    style: str
    finish: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_wobble(world: World) -> list[str]:
    support = world.entities.get("support")
    climber = world.entities.get("captain")
    if not support or not climber:
        return []
    if support.meters["climbed"] < THRESHOLD:
        return []
    if support.attrs.get("stable", False):
        return []
    if support.meters["steadied"] >= THRESHOLD:
        return []
    sig = ("wobble", support.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    support.meters["wobble"] += 1
    climber.memes["fear"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    return ["__wobble__"]


def _r_tumble(world: World) -> list[str]:
    treasure = world.entities.get("treasure")
    if not treasure or treasure.meters["tumbled"] < THRESHOLD:
        return []
    sig = ("tumble", treasure.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["laughter"] += 1
    return ["__tumble__"]


def _r_rescued(world: World) -> list[str]:
    treasure = world.entities.get("treasure")
    parrot = world.entities.get("parrot")
    if not treasure or treasure.meters["rescued"] < THRESHOLD:
        return []
    sig = ("rescued", treasure.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["teamwork"] += 1
    if parrot:
        parrot.memes["squawked"] += 1
    return ["__rescued__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="tumble", tag="comic", apply=_r_tumble),
    Rule(name="rescued", tag="social", apply=_r_rescued),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for item in produced:
            if item == "__wobble__":
                support = world.get("support")
                captain = world.get("captain")
                world.say(
                    f"The {support.label} gave a tiny sideways shimmy, and {captain.id}'s "
                    f"stomach did a matching shimmy inside {captain.pronoun('object')}."
                )
            elif item == "__tumble__":
                treasure = world.get("treasure")
                if world.facts.get("comic_outcome") == "unfurl":
                    world.say(
                        f"For one windy second, the {treasure.label} opened and flapped like "
                        f"a silly little sail before the crew caught it."
                    )
                else:
                    world.say(
                        f"The {treasure.label} dropped with a soft plop into the waiting cloth, "
                        f"which made both pirates bark out a laugh."
                    )
            elif item == "__rescued__":
                parrot = world.get("parrot")
                if parrot.memes["squawked"] >= THRESHOLD:
                    world.say(
                        f'{parrot.id} gave its favorite ridiculous pirate squeak: "damn the sill!"'
                    )
    return produced


def method_works(treasure: Treasure, method: Method) -> bool:
    if treasure.weight > method.max_weight:
        return False
    if method.needs_loop and not treasure.has_loop:
        return False
    if method.needs_soft and not treasure.soft:
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for tid, treasure in TREASURES.items():
        for mid, method in METHODS.items():
            if method_works(treasure, method):
                combos.append((tid, mid))
    return combos


@dataclass
class StoryParams:
    treasure: str
    method: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
    captain_trait: str
    mate_trait: str
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


def predict_solo_wobble(world: World) -> bool:
    sim = world.copy()
    sim.get("support").meters["climbed"] += 1
    propagate(sim, narrate=False)
    return sim.get("support").meters["wobble"] >= THRESHOLD


def introduce(world: World, captain: Entity, mate: Entity, parent: Entity) -> None:
    world.say(
        f"On a breezy afternoon, {captain.id} and {mate.id} turned the living room into "
        f"a pirate cabin with a striped blanket sail, a laundry basket prow, and a spoon "
        f"that served as the loudest silver cutlass on the carpet sea."
    )
    world.say(
        f"Their rubber parrot, Pickles, had only one grumpy pirate squeak -- "
        f'"damn!" -- and it came out so tiny that even {parent.label_word} laughed at it.'
    )
    world.say(
        f'"Captain {captain.id}!" cried {mate.id}. "Matey {mate.id}!" cried {captain.id}. '
        f"Then they both saluted so hard they nearly bonked foreheads."
    )


def strand_treasure(world: World, treasure_cfg: Treasure) -> None:
    treasure = world.get("treasure")
    treasure.meters["on_sill"] = 1
    world.say(
        f"Their pretend treasure was {treasure_cfg.phrase}. During a wild turn past the sofa, "
        f"it slid onto the window sill above the curtains and sat there as smug as a gull."
    )
    world.say(
        f"Both pirates looked up. The sill was too high for easy grabbing, and the treasure "
        f"looked much farther away now that it belonged to the sky."
    )


def tempt(world: World, captain: Entity, mate: Entity) -> None:
    captain.memes["bravado"] += 1
    world.say(
        f'"I can fetch it myself," said {captain.id}, eyeing the wobbly stool by the bookcase. '
        f'{mate.id} followed that look and made a face that said the plan smelled fishy.'
    )


def warn(world: World, captain: Entity, mate: Entity, parent: Entity) -> None:
    predicted = predict_solo_wobble(world)
    world.facts["predicted_wobble"] = predicted
    mate.memes["care"] += 1
    if predicted:
        world.say(
            f'{mate.id} caught {captain.id}\'s sleeve. "That stool will wobble," '
            f'{mate.pronoun()} said. "If it wiggles, the treasure might fall and you might bump '
            f'your chin. Let\'s be a crew, not two one-pirate disasters."'
        )
    else:
        world.say(
            f'{mate.id} still touched {captain.id}\'s sleeve. "Let\'s be a crew," '
            f'{mate.pronoun()} said softly. "Treasure hunting goes better with four hands."'
        )
    world.say(
        f"{parent.label_word.capitalize()} looked over from the doorway and nodded. "
        f'"A good crew uses teamwork," {parent.pronoun()} said.'
    )


def refuse_solo(world: World, captain: Entity) -> None:
    support = world.get("support")
    support.meters["climbed"] += 1
    propagate(world, narrate=True)
    support.meters["climbed"] = 0
    world.say(
        f"{captain.id} put one sneaker on the stool, felt the wobble, and stepped right back "
        f"down. Even bold pirates could tell when a plan was more swagger than sense."
    )


def plan_method(world: World, captain: Entity, mate: Entity, method: Method, treasure_cfg: Treasure) -> None:
    if method.id == "crate_grab":
        world.say(
            f'Then {mate.id} pointed to the sturdy milk crate. "There," {mate.pronoun()} said. '
            f'"I hold the crate. You climb just high enough. No wobble, no flying pirates."'
        )
    elif method.id == "mop_hook":
        world.say(
            f'{mate.id} spotted the mop with a loop of string tied near its handle and grinned. '
            f'"A hook!" {mate.pronoun().capitalize()} said. "You guide the tip, and I keep the pole '
            f"steady so it doesn't poke the moon."
        )
    else:
        world.say(
            f'{mate.id} spread a laundry blanket open like a catcher\'s net. '
            f'"You nudge the {treasure_cfg.label}," {mate.pronoun()} said, '
            f'"and I\'ll catch it. If it bounces, we bounce with it."'
        )
    world.say("That sounded much more like a real crew plan.")


def do_rescue(world: World, captain: Entity, mate: Entity, method: Method, treasure_cfg: Treasure) -> None:
    support = world.get("support")
    treasure = world.get("treasure")
    if method.id == "crate_grab":
        support.attrs["stable"] = True
        support.label = "milk crate"
        support.meters["steadied"] += 1
        support.meters["climbed"] += 1
        captain.memes["trust"] += 1
        mate.memes["pride"] += 1
        world.say(
            f"{mate.id} planted both feet and held the crate firm while {captain.id} climbed up. "
            f"From there, {captain.pronoun()} could finally reach the sill without stretching like "
            f"a noodle in a storm."
        )
        treasure.meters["rescued"] += 1
    elif method.id == "mop_hook":
        support.attrs["stable"] = True
        support.meters["steadied"] += 1
        captain.memes["focus"] += 1
        mate.memes["focus"] += 1
        world.say(
            f"{captain.id} lifted the mop while {mate.id} steadied the long handle with both hands. "
            f"Together they eased the string loop over the treasure and drew it slowly off the sill."
        )
        if treasure_cfg.longish:
            treasure.meters["tumbled"] += 1
            world.facts["comic_outcome"] = "unfurl"
        treasure.meters["rescued"] += 1
    else:
        support.attrs["stable"] = True
        mate.memes["focus"] += 1
        captain.memes["focus"] += 1
        world.say(
            f"{mate.id} held the blanket wide under the window while {captain.id} rose on tiptoe "
            f"and gave the treasure the gentlest pirate nudge."
        )
        treasure.meters["tumbled"] += 1
        world.facts["comic_outcome"] = "plop"
        treasure.meters["rescued"] += 1
    propagate(world, narrate=True)


def resolution(world: World, captain: Entity, mate: Entity, treasure_cfg: Treasure, parent: Entity) -> None:
    captain.memes["lesson"] += 1
    mate.memes["lesson"] += 1
    world.say(
        f"When the {treasure_cfg.label} was safe at last, both children bent over it and laughed "
        f"the breathy kind of laugh that comes after a tight little scare has floated away."
    )
    world.say(
        f'"Crew rule," said {mate.id}, raising one finger. "No lone lunges for high treasure." '
        f'"Crew rule," agreed {captain.id}. "Pirates use teamwork."'
    )
    world.say(
        f"{parent.label_word.capitalize()} bowed to them from the doorway. "
        f'"Then Captain and Mate may now divide the loot," {parent.pronoun()} said.'
    )
    if treasure_cfg.id == "biscuit_tin":
        world.say(
            "Inside the tin they found two round biscuits and one paper coin, which was not rich in "
            "money but was very rich in jokes."
        )
    elif treasure_cfg.id == "shell_pouch":
        world.say(
            "Inside the pouch they found smooth shells that clicked together like tiny pirate teeth."
        )
    else:
        world.say(
            "Inside the tube they found a rolled map that still had a fold shaped like a sneezing sea serpent."
        )
    world.say(
        "Pickles the parrot flopped onto the blanket sail, and the whole brave, silly crew looked much "
        "less like a disaster and much more like a ship."
    )


def tell(
    treasure_cfg: Treasure,
    method: Method,
    captain_name: str,
    captain_gender: str,
    mate_name: str,
    mate_gender: str,
    parent_type: str,
    captain_trait: str,
    mate_trait: str,
) -> World:
    world = World()
    world.facts["comic_outcome"] = ""
    world.facts["predicted_wobble"] = False

    captain = world.add(
        Entity(
            id=captain_name,
            kind="character",
            type=captain_gender,
            role="captain",
            traits=[captain_trait, "bold"],
            attrs={},
        )
    )
    mate = world.add(
        Entity(
            id=mate_name,
            kind="character",
            type=mate_gender,
            role="mate",
            traits=[mate_trait, "careful"],
            attrs={},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="support",
            type="stool",
            label="stool",
            attrs={"stable": False},
        )
    )
    world.add(
        Entity(
            id="treasure",
            type="treasure",
            label=treasure_cfg.label,
            phrase=treasure_cfg.phrase,
            attrs={
                "weight": treasure_cfg.weight,
                "has_loop": treasure_cfg.has_loop,
                "soft": treasure_cfg.soft,
                "longish": treasure_cfg.longish,
            },
        )
    )
    world.add(
        Entity(
            id="Pickles",
            type="parrot",
            label="rubber parrot",
            attrs={},
        )
    )

    introduce(world, captain, mate, parent)
    strand_treasure(world, treasure_cfg)

    world.para()
    tempt(world, captain, mate)
    warn(world, captain, mate, parent)
    refuse_solo(world, captain)

    world.para()
    plan_method(world, captain, mate, method, treasure_cfg)
    do_rescue(world, captain, mate, method, treasure_cfg)

    world.para()
    resolution(world, captain, mate, treasure_cfg, parent)

    world.facts.update(
        captain=captain,
        mate=mate,
        parent=parent,
        treasure_cfg=treasure_cfg,
        method=method,
        teamwork=True,
        rescued=world.get("treasure").meters["rescued"] >= THRESHOLD,
        tumbled=world.get("treasure").meters["tumbled"] >= THRESHOLD,
    )
    return world


TREASURES = {
    "biscuit_tin": Treasure(
        id="biscuit_tin",
        label="biscuit tin",
        phrase="a round biscuit tin painted with a gold skull",
        weight=3,
        has_loop=False,
        soft=False,
        longish=False,
        tags={"biscuit", "tin"},
    ),
    "shell_pouch": Treasure(
        id="shell_pouch",
        label="shell pouch",
        phrase="a velvet shell pouch with a drawstring loop",
        weight=1,
        has_loop=True,
        soft=True,
        longish=False,
        tags={"pouch", "shell"},
    ),
    "map_tube": Treasure(
        id="map_tube",
        label="map tube",
        phrase="a cardboard map tube with a string strap",
        weight=2,
        has_loop=True,
        soft=False,
        longish=True,
        tags={"map", "tube"},
    ),
}

METHODS = {
    "crate_grab": Method(
        id="crate_grab",
        label="crate grab",
        max_weight=3,
        needs_loop=False,
        needs_soft=False,
        requires_helper_hold=True,
        style="steady and climb",
        finish="lifted by hand from the sill",
        qa_text="One child held the crate steady while the other climbed just high enough to lift it down.",
        tags={"crate", "teamwork"},
    ),
    "mop_hook": Method(
        id="mop_hook",
        label="mop hook",
        max_weight=2,
        needs_loop=True,
        needs_soft=False,
        requires_helper_hold=True,
        style="guide and steady",
        finish="drawn off the sill with the hooked mop",
        qa_text="They used the mop like a hook: one guided the tip and the other steadied the long handle.",
        tags={"mop", "hook", "teamwork"},
    ),
    "blanket_catch": Method(
        id="blanket_catch",
        label="blanket catch",
        max_weight=1,
        needs_loop=False,
        needs_soft=True,
        requires_helper_hold=True,
        style="nudge and catch",
        finish="caught in a blanket after a gentle nudge",
        qa_text="One child nudged the treasure from the sill while the other held a blanket underneath to catch it.",
        tags={"blanket", "catch", "teamwork"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["brave", "cheerful", "clever", "careful", "bouncy", "thoughtful"]


CURATED = [
    StoryParams(
        treasure="biscuit_tin",
        method="crate_grab",
        captain="Tom",
        captain_gender="boy",
        mate="Lily",
        mate_gender="girl",
        parent="mother",
        captain_trait="brave",
        mate_trait="careful",
    ),
    StoryParams(
        treasure="shell_pouch",
        method="blanket_catch",
        captain="Mia",
        captain_gender="girl",
        mate="Ben",
        mate_gender="boy",
        parent="father",
        captain_trait="cheerful",
        mate_trait="thoughtful",
    ),
    StoryParams(
        treasure="map_tube",
        method="mop_hook",
        captain="Sam",
        captain_gender="boy",
        mate="Zoe",
        mate_gender="girl",
        parent="mother",
        captain_trait="clever",
        mate_trait="careful",
    ),
    StoryParams(
        treasure="shell_pouch",
        method="crate_grab",
        captain="Ella",
        captain_gender="girl",
        mate="Noah",
        mate_gender="boy",
        parent="father",
        captain_trait="bouncy",
        mate_trait="cheerful",
    ),
]


KNOWLEDGE = {
    "sill": [
        (
            "What is a window sill?",
            "A window sill is the flat ledge at the bottom of a window. Small things can end up there if they slide or are set down high."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another do one job together. A good team shares the work so the job is safer and easier."
        )
    ],
    "crate": [
        (
            "Why is a sturdy crate safer than a wobbly stool?",
            "A sturdy crate is less likely to tip or wiggle while someone stands on it. When another person steadies it too, the climber can balance better."
        )
    ],
    "mop": [
        (
            "How can a long tool help you reach something high?",
            "A long tool can reach farther than your arm. If a grown-up says it is okay and someone keeps the tool steady, it can help move something closer."
        )
    ],
    "blanket": [
        (
            "Why can a blanket help catch something soft?",
            "A blanket makes a soft place for the object to land. That can stop it from bumping the floor too hard."
        )
    ],
    "hook": [
        (
            "What does a hook do?",
            "A hook catches onto a loop or handle so you can pull something gently. It works best when the thing has somewhere safe for the hook to grab."
        )
    ],
    "map": [
        (
            "What is a map?",
            "A map is a picture that helps show where places are. Pirates in stories love maps because maps help them hunt for treasure."
        )
    ],
    "biscuit": [
        (
            "What is a biscuit tin?",
            "A biscuit tin is a metal container that can hold biscuits or other treats. Metal tins can feel a bit heavy compared with cloth bags."
        )
    ],
    "shell": [
        (
            "What is a shell pouch?",
            "A shell pouch is a small soft bag for carrying little things like shells. A drawstring loop helps keep the bag closed."
        )
    ],
}
KNOWLEDGE_ORDER = ["sill", "teamwork", "crate", "mop", "blanket", "hook", "map", "biscuit", "shell"]


def pair_noun(captain: Entity, mate: Entity) -> str:
    if captain.type == "boy" and mate.type == "boy":
        return "two young pirates"
    if captain.type == "girl" and mate.type == "girl":
        return "two young pirates"
    return "two young pirates"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    treasure = f["treasure_cfg"]
    method = f["method"]
    return [
        'Write a funny pirate-style story for a 3-to-5-year-old that includes the words "damn" and "sill" and ends with teamwork solving the problem.',
        f"Tell a pirate tale where {captain.id} and {mate.id} lose a {treasure.label} on a high sill, avoid a wobbly solo climb, and rescue it together using {method.label}.",
        "Write a gentle, silly story where children talk like a pirate crew, laugh at a ridiculous parrot squeak, and make a safer crew rule by the end.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    parent = f["parent"]
    treasure = f["treasure_cfg"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(captain, mate)}, {captain.id} and {mate.id}, who were pretending to be a pirate crew. {parent.label_word.capitalize()} watched from nearby and liked their good teamwork."
        ),
        (
            f"Where did the treasure get stuck?",
            f"The {treasure.label} slid onto the high window sill above the curtains. That made it hard to reach by hand, which is why the children had to stop and think."
        ),
        (
            f"Why did {mate.id} stop {captain.id} from climbing the stool alone?",
            f"{mate.id} could see the wobbly stool was a bad idea. A solo climb might have made the stool shimmy and could have made the treasure fall or {captain.id} bump {captain.pronoun('possessive')} chin."
        ),
        (
            "How did they solve the problem?",
            f"They solved it together. {method.qa_text} That teamwork made the rescue safer than a lone grab."
        ),
    ]
    if f["tumbled"]:
        if world.facts.get("comic_outcome") == "unfurl":
            qa.append(
                (
                    "What was the funny part during the rescue?",
                    f"When they pulled the map tube from the sill, it opened for a moment and flapped like a little sail. The crew still caught it, so the surprise turned into laughter instead of trouble."
                )
            )
        else:
            qa.append(
                (
                    "What was the funny part during the rescue?",
                    f"The treasure dropped into the waiting blanket with a soft plop. That silly bounce made both children laugh while they finished the job."
                )
            )
    qa.append(
        (
            "What changed by the end of the story?",
            f"At the end, the children had a new crew rule: no lone lunges for high treasure. They learned that pirate adventures go better when they use teamwork and a steadier plan."
        )
    )
    return qa


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sill", "teamwork"} | set(f["method"].tags) | set(f["treasure_cfg"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or isinstance(v, bool)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(treasure: Treasure, method: Method) -> str:
    reasons = []
    if treasure.weight > method.max_weight:
        reasons.append(
            f"the {treasure.label} is too heavy for {method.label}"
        )
    if method.needs_loop and not treasure.has_loop:
        reasons.append(
            f"{method.label} needs something with a loop or strap, and the {treasure.label} has none"
        )
    if method.needs_soft and not treasure.soft:
        reasons.append(
            f"{method.label} only makes sense for something soft enough to catch"
        )
    joined = "; ".join(reasons) if reasons else "this rescue plan does not fit"
    return f"(No story: {joined}. Pick a method that reasonably fits the treasure on the sill.)"


ASP_RULES = r"""
valid(T, M) :- treasure(T), method(M),
               t_weight(T, W), m_max_weight(M, MW), W <= MW,
               not bad_loop(T, M), not bad_soft(T, M).

bad_loop(T, M) :- m_needs_loop(M), not t_has_loop(T).
bad_soft(T, M) :- m_needs_soft(M), not t_soft(T).

comic(unfurl) :- chosen_treasure(T), chosen_method(mop_hook), t_longish(T).
comic(plop)   :- chosen_treasure(T), chosen_method(blanket_catch).
comic(none)   :- chosen_method(crate_grab).
comic(none)   :- chosen_method(mop_hook), chosen_treasure(T), not t_longish(T).

#show valid/2.
#show comic/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("t_weight", tid, treasure.weight))
        if treasure.has_loop:
            lines.append(asp.fact("t_has_loop", tid))
        if treasure.soft:
            lines.append(asp.fact("t_soft", tid))
        if treasure.longish:
            lines.append(asp.fact("t_longish", tid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("m_max_weight", mid, method.max_weight))
        if method.needs_loop:
            lines.append(asp.fact("m_needs_loop", mid))
        if method.needs_soft:
            lines.append(asp.fact("m_needs_soft", mid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_comic(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_treasure", params.treasure),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "comic")
    return atoms[0][0] if atoms else "none"


def comic_outcome_of(params: StoryParams) -> str:
    treasure = TREASURES[params.treasure]
    if params.method == "blanket_catch":
        return "plop"
    if params.method == "mop_hook" and treasure.longish:
        return "unfurl"
    return "none"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a funny pirate crew rescues sill-stranded treasure with teamwork."
    )
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid treasure/method pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treasure and args.method:
        treasure = TREASURES[args.treasure]
        method = METHODS[args.method]
        if not method_works(treasure, method):
            raise StoryError(explain_rejection(treasure, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.treasure is None or combo[0] == args.treasure)
        and (args.method is None or combo[1] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    treasure_id, method_id = rng.choice(sorted(combos))
    captain_gender = rng.choice(["girl", "boy"])
    mate_gender = rng.choice(["girl", "boy"])
    captain_name = _pick_name(rng, captain_gender)
    mate_name = _pick_name(rng, mate_gender, avoid=captain_name)
    return StoryParams(
        treasure=treasure_id,
        method=method_id,
        captain=captain_name,
        captain_gender=captain_gender,
        mate=mate_name,
        mate_gender=mate_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        captain_trait=rng.choice(TRAITS),
        mate_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    treasure = TREASURES[params.treasure]
    method = METHODS[params.method]
    if not method_works(treasure, method):
        raise StoryError(explain_rejection(treasure, method))

    world = tell(
        treasure_cfg=treasure,
        method=method,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
        captain_trait=params.captain_trait,
        mate_trait=params.mate_trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
        print(f"OK: ASP gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"FAILED: resolve_params crashed for seed {seed}.")
            continue
        params.seed = seed
        cases.append(params)

    comic_bad = 0
    for params in cases:
        if asp_comic(params) != comic_outcome_of(params):
            comic_bad += 1
    if comic_bad == 0:
        print(f"OK: comic outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: comic outcome differs on {comic_bad}/{len(cases)} scenarios.")

    smoke = CURATED[0]
    try:
        sample = generate(smoke)
        if not sample.story.strip():
            raise StoryError("empty story")
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover
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
        print(f"{len(combos)} valid (treasure, method) pairs:\n")
        for treasure, method in combos:
            print(f"  {treasure:12} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain} & {p.mate}: {p.treasure} with {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
