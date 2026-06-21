#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/voodoo_swat_friendship_nursery_rhyme.py
==================================================================

A standalone story world for a soft nursery-rhyme friendship tale.

Two children share a little plaything or treat and sing a nonsense rhyme with
the word "voodoo" in it. A tiny winged visitor drifts or buzzes near what they
share. One child wants to swat. The other child predicts that a swat will spoil
their shared thing and pinch their friendship too, so they try a gentler way.

The world model tracks both physical state (meters) and feeling state (memes).
Its reasonableness gate only allows combinations where the visitor fits the
place, is plausibly drawn to the shared thing, and the chosen gentle response
actually works there. The outcome branches on friendship strength and the calm
friend's trait: either the swat is averted, or it happens, makes a little mess,
and the friendship is mended with apology and repair.

Run it
------
    python storyworlds/worlds/gpt-5.4/voodoo_swat_friendship_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/voodoo_swat_friendship_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/voodoo_swat_friendship_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/voodoo_swat_friendship_nursery_rhyme.py --trace
    python storyworlds/worlds/gpt-5.4/voodoo_swat_friendship_nursery_rhyme.py --asp
    python storyworlds/worlds/gpt-5.4/voodoo_swat_friendship_nursery_rhyme.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
IMPULSE_INIT = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)
    indoor: bool = False
    rhyme_image: str = ""
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
class Visitor:
    id: str
    label: str
    motion: str
    sound: str
    likes: set[str] = field(default_factory=set)
    nature: str = ""
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
class SharedThing:
    id: str
    label: str
    phrase: str
    the: str
    lure: str
    fragile: bool = True
    spoil: str = ""
    repair: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Response:
    id: str
    sense: int
    text: str
    success: str
    handles: set[str] = field(default_factory=set)
    works_in: set[str] = field(default_factory=set)
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
        return [e for e in self.entities.values() if e.role in {"instigator", "friend"}]

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


def _r_damage_strain(world: World) -> list[str]:
    shared = world.get("shared")
    if shared.meters["damaged"] < THRESHOLD:
        return []
    sig = ("damage_strain", "shared")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["sad"] += 1
    world.get("bond").meters["strain"] += 1
    return ["__damage__"]


def _r_guided_calm(world: World) -> list[str]:
    visitor = world.get("visitor")
    if visitor.meters["guided"] < THRESHOLD:
        return []
    sig = ("guided_calm", "visitor")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    visitor.meters["gone"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
    return ["__guided__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage_strain", tag="social", apply=_r_damage_strain),
    Rule(name="guided_calm", tag="social", apply=_r_guided_calm),
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


def visitor_fits(setting: Setting, visitor: Visitor) -> bool:
    return visitor.id in setting.affords


def visitor_drawn(visitor: Visitor, shared: SharedThing) -> bool:
    return shared.lure in visitor.likes


def response_works(setting: Setting, visitor: Visitor, response: Response) -> bool:
    return setting.id in response.works_in and visitor.id in response.handles


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for visitor_id, visitor in VISITORS.items():
            if not visitor_fits(setting, visitor):
                continue
            for shared_id, shared in SHARED_THINGS.items():
                if not visitor_drawn(visitor, shared):
                    continue
                for response_id, response in RESPONSES.items():
                    if response.sense >= SENSE_MIN and response_works(setting, visitor, response):
                        combos.append((setting_id, visitor_id, shared_id, response_id))
    return combos


CALM_BONUS = {
    "gentle": 2,
    "patient": 2,
    "kind": 1,
    "careful": 1,
    "bouncy": 0,
    "hasty": 0,
}
BOND_VALUE = {
    "best_friends": 3,
    "playmates": 2,
}


def would_avert(relation: str, trait: str) -> bool:
    calm = CALM_BONUS.get(trait, 0)
    bond = BOND_VALUE.get(relation, 0)
    return bond + calm + 1 >= IMPULSE_INIT


def predict_swat(world: World) -> dict:
    sim = world.copy()
    do_swat(sim, narrate=False)
    shared = sim.get("shared")
    bond = sim.get("bond")
    return {
        "damaged": shared.meters["damaged"] >= THRESHOLD,
        "strain": bond.meters["strain"],
    }


def play_setup(world: World, a: Entity, b: Entity, shared: SharedThing) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"In {world.setting.place}, {a.id} and {b.id} sat knee to knee with {shared.phrase}. "
        f"{world.setting.rhyme_image}"
    )
    world.say(
        f"They had made up a clap-and-tap nursery rhyme with the silly word voodoo in it, "
        f"because voodoo sounded round and funny when small hands met."
    )
    world.say(
        f'"Voodoo, voodoo, pat-a-cake blue; what I share, I share with you," they sang.'
    )


def arrival(world: World, a: Entity, b: Entity, visitor: Visitor, shared: SharedThing) -> None:
    visitor_ent = world.get("visitor")
    visitor_ent.meters["near"] += 1
    world.say(
        f"Then a {visitor.label} came {visitor.motion} by. It {visitor.sound} near {shared.the}, "
        f"as if {shared.lure} had called it close."
    )
    world.say(
        f"{a.id} leaned one way, {b.id} leaned two, and both stopped their rhyme in the middle."
    )


def tempt_swat(world: World, a: Entity, visitor: Visitor) -> None:
    a.memes["impulse"] += 1
    world.say(
        f'"Oh! I will swat it," said {a.id}, lifting a quick little hand. '
        f'The thought felt fast and easy.'
    )


def warn(world: World, b: Entity, a: Entity, shared: SharedThing, visitor: Visitor) -> None:
    pred = predict_swat(world)
    world.facts["predicted_damaged"] = pred["damaged"]
    world.facts["predicted_strain"] = pred["strain"]
    extra = ""
    if pred["damaged"]:
        extra = f" {shared.The} might get {shared.spoil}."
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "Please don\'t," {b.pronoun()} said softly. '
        f'"A swat is for hurry, not for care.{extra}"'
    )
    if pred["strain"] >= THRESHOLD:
        world.say(
            f'{b.pronoun().capitalize()} added, "If our game gets spoiled, our two-small tune may wobble too."'
        )


def back_down(world: World, a: Entity, b: Entity) -> None:
    a.memes["impulse"] = 0.0
    a.memes["listening"] += 1
    b.memes["trusted"] += 1
    world.say(
        f"{a.id} looked at the raised hand, then tucked it back into a lap as neat as a folded napkin."
    )
    world.say(
        f'"All right," said {a.id}. "No swat. We can be soft and clever."'
    )


def do_swat(world: World, narrate: bool = True) -> None:
    shared = world.get("shared")
    shared.meters["jolted"] += 1
    if shared.attrs.get("fragile", False):
        shared.meters["damaged"] += 1
    propagate(world, narrate=narrate)


def swat_oops(world: World, a: Entity, b: Entity, shared: SharedThing) -> None:
    a.memes["regret"] += 1
    do_swat(world)
    world.say(
        f"But the quick swat went slap by {shared.the}, and {shared.the} got {shared.spoil}."
    )
    world.say(
        f"{a.id} froze. {b.id}'s mouth made a small round O, and the rhyme fell quiet."
    )


def guide_visitor(world: World, a: Entity, b: Entity, response: Response, visitor: Visitor) -> None:
    visitor_ent = world.get("visitor")
    visitor_ent.meters["guided"] += 1
    propagate(world, narrate=False)
    world.say(response.text)
    world.say(
        f"The {visitor.label} {response.success}, and the air felt roomy again."
    )
    for kid in (a, b):
        kid.memes["calm"] += 1


def mend_friendship(world: World, a: Entity, b: Entity, shared: SharedThing) -> None:
    bond = world.get("bond")
    bond.meters["strain"] = 0.0
    a.memes["apology"] += 1
    b.memes["forgiveness"] += 1
    world.say(
        f'"I am sorry," whispered {a.id}. "My hand was quicker than my heart."'
    )
    world.say(
        f'{b.id} nodded and squeezed {a.pronoun("possessive")} fingers. '
        f'"We can mend {shared.the}, and mend us too."'
    )
    world.say(shared.repair)
    world.get("shared").meters["mended"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1


def ending(world: World, a: Entity, b: Entity, shared: SharedThing, outcome: str) -> None:
    if outcome == "averted":
        world.say(
            f"Soon the two friends were tapping their tune again, and {shared.ending_image}."
        )
    else:
        world.say(
            f"When the little fixing was done, {shared.ending_image}, and their friendship sat steady beside it."
        )
    world.say(
        f'"Voodoo, voodoo, one and two; gentle hands are strong and true," sang {a.id} and {b.id}.'
    )


def tell(
    setting: Setting,
    visitor: Visitor,
    shared_cfg: SharedThing,
    response: Response,
    *,
    instigator: str = "Mina",
    instigator_gender: str = "girl",
    friend: str = "Jo",
    friend_gender: str = "boy",
    caregiver: str = "mother",
    relation: str = "best_friends",
    trait: str = "gentle",
) -> World:
    world = World(setting)
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=friend,
        kind="character",
        type=friend_gender,
        label=friend,
        role="friend",
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Caregiver",
        kind="character",
        type=caregiver,
        label="the caregiver",
        role="caregiver",
    ))
    world.add(Entity(id="bond", type="bond", label="friendship"))
    world.add(Entity(
        id="shared",
        type="shared",
        label=shared_cfg.label,
        attrs={"fragile": shared_cfg.fragile},
        tags=set(shared_cfg.tags),
    ))
    world.add(Entity(
        id="visitor",
        type="visitor",
        label=visitor.label,
        tags=set(visitor.tags),
    ))

    a.memes["impulse"] = float(IMPULSE_INIT)
    b.memes["calm"] = float(CALM_BONUS.get(trait, 0))
    world.get("bond").meters["closeness"] = float(BOND_VALUE.get(relation, 0))
    world.facts["caregiver"] = parent

    play_setup(world, a, b, shared_cfg)
    world.para()
    arrival(world, a, b, visitor, shared_cfg)
    tempt_swat(world, a, visitor)
    warn(world, b, a, shared_cfg, visitor)

    averted = would_avert(relation, trait)
    world.para()
    if averted:
        back_down(world, a, b)
        guide_visitor(world, a, b, response, visitor)
        outcome = "averted"
    else:
        swat_oops(world, a, b, shared_cfg)
        guide_visitor(world, a, b, response, visitor)
        world.para()
        mend_friendship(world, a, b, shared_cfg)
        outcome = "mended"

    world.para()
    ending(world, a, b, shared_cfg, outcome)

    world.facts.update(
        instigator=a,
        friend=b,
        visitor_cfg=visitor,
        visitor=world.get("visitor"),
        shared_cfg=shared_cfg,
        shared=world.get("shared"),
        response=response,
        setting=setting,
        relation=relation,
        trait=trait,
        outcome=outcome,
        averted=averted,
        damaged=world.get("shared").meters["damaged"] >= THRESHOLD,
        mended=world.get("shared").meters["mended"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the nursery garden",
        affords={"bee", "butterfly"},
        indoor=False,
        rhyme_image="The gate clicked in the breeze, and marigolds nodded like yellow bells.",
    ),
    "porch": Setting(
        id="porch",
        place="the shaded porch",
        affords={"bee", "moth"},
        indoor=False,
        rhyme_image="A striped rug lay flat as toast, and the rails made skinny ladder-shadows.",
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom by the open sill",
        affords={"moth"},
        indoor=True,
        rhyme_image="Blocks slept in a basket, and the curtain hem gave a tiny tick to the wind.",
    ),
    "yard": Setting(
        id="yard",
        place="the nursery yard",
        affords={"butterfly", "bee"},
        indoor=False,
        rhyme_image="A chalk moon and chalk spoon curved on the paving stones.",
    ),
}

VISITORS = {
    "bee": Visitor(
        id="bee",
        label="bee",
        motion="bobbing",
        sound="buzzed",
        likes={"flower", "sweet"},
        nature="A bee likes blossoms and sweet smells.",
        tags={"bee", "kindness"},
    ),
    "butterfly": Visitor(
        id="butterfly",
        label="butterfly",
        motion="drifting",
        sound="fluttered",
        likes={"flower", "bright"},
        nature="A butterfly likes bright petals and sunny things.",
        tags={"butterfly", "kindness"},
    ),
    "moth": Visitor(
        id="moth",
        label="moth",
        motion="fluttering",
        sound="softly bumped",
        likes={"bright"},
        nature="A moth often goes where a light is glowing.",
        tags={"moth", "light"},
    ),
}

SHARED_THINGS = {
    "flower_crown": SharedThing(
        id="flower_crown",
        label="flower crown",
        phrase="a daisy flower crown they had woven together",
        the="the flower crown",
        lure="flower",
        fragile=True,
        spoil="crooked and petal-loose",
        repair="Together they tucked the petals back in and set the circle round again.",
        ending_image="the flower crown sat between them, tidy as a small sun",
        tags={"flower", "friendship"},
    ),
    "jam_tart": SharedThing(
        id="jam_tart",
        label="jam tart",
        phrase="one round jam tart on a blue plate to share after the song",
        the="the jam tart",
        lure="sweet",
        fragile=True,
        spoil="smeared and lopsided",
        repair="Together they straightened the blue plate, wiped the jam from the edge, and laughed when the tart still looked tasty.",
        ending_image="the jam tart waited bright and ruby on the plate",
        tags={"sweet", "sharing"},
    ),
    "paper_lantern": SharedThing(
        id="paper_lantern",
        label="paper lantern",
        phrase="a paper lantern painted with moons and dots",
        the="the paper lantern",
        lure="bright",
        fragile=True,
        spoil="dented and crinkled",
        repair="Together they smoothed the paper sides and hung the lantern where it could glow without a bump.",
        ending_image="the paper lantern swayed with its moons unwrinkled",
        tags={"light", "sharing"},
    ),
}

RESPONSES = {
    "flower_detour": Response(
        id="flower_detour",
        sense=3,
        text="So they pointed to the marigolds and hummed low and slow, leading the tiny visitor toward a kinder feast.",
        success="turned from the shared thing and floated to the flowers instead",
        handles={"bee", "butterfly"},
        works_in={"garden", "yard"},
        tags={"flowers", "gentle_hands"},
    ),
    "cup_card": Response(
        id="cup_card",
        sense=3,
        text="So they fetched a clear cup and a stiff card, making a little moving wall instead of a smack.",
        success="was covered safely and carried away from their game before being let go",
        handles={"bee", "butterfly", "moth"},
        works_in={"garden", "yard", "porch", "playroom"},
        tags={"cup", "gentle_hands"},
    ),
    "open_window": Response(
        id="open_window",
        sense=3,
        text="So they opened the window wide and dimmed their own bright corner, giving the small wings a better road to follow.",
        success="fluttered out through the lighted opening",
        handles={"moth"},
        works_in={"playroom", "porch"},
        tags={"window", "light"},
    ),
    "napkin_wave": Response(
        id="napkin_wave",
        sense=2,
        text="So they waved a napkin softly, not to hit but to make a breeze that nudged the tiny guest away.",
        success="rode the little breeze off from the shared thing",
        handles={"butterfly", "bee"},
        works_in={"garden", "yard", "porch"},
        tags={"gentle_hands"},
    ),
    "hard_swat": Response(
        id="hard_swat",
        sense=1,
        text="",
        success="",
        handles={"bee", "butterfly", "moth"},
        works_in={"garden", "yard", "porch", "playroom"},
        tags={"swat"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Poppy", "Tess", "Ada", "Daisy", "Ruth"]
BOY_NAMES = ["Jo", "Ben", "Toby", "Milo", "Kit", "Finn", "Ollie", "Sam"]
TRAITS = ["gentle", "patient", "kind", "careful", "bouncy", "hasty"]
RELATIONS = ["best_friends", "playmates"]


@dataclass
class StoryParams:
    setting: str
    visitor: str
    shared: str
    response: str
    instigator: str
    instigator_gender: str
    friend: str
    friend_gender: str
    caregiver: str
    relation: str
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


KNOWLEDGE = {
    "bee": [(
        "Why should you be gentle with a bee?",
        "A bee is a tiny living creature, and rough hands can hurt it. Bees also help flowers by visiting them."
    )],
    "butterfly": [(
        "Why is a butterfly not for swatting?",
        "A butterfly has soft wings covered with tiny scales. Gentle looking is better than hitting."
    )],
    "moth": [(
        "Why do moths go near lights?",
        "Moths often follow light when they fly at night. An open window can give them a better place to go."
    )],
    "cup": [(
        "How can a cup and card help with a little bug?",
        "The cup covers the bug without squishing it. The card slides under so you can move it safely."
    )],
    "window": [(
        "Why does opening a window help a moth?",
        "The open window gives the moth a clear way out. Then it does not need to flutter around people and lamps."
    )],
    "flowers": [(
        "Why might a bee or butterfly go to flowers?",
        "Flowers have color and sweet smells that call small flying visitors close. That is a nicer place for them than a child's snack or game."
    )],
    "gentle_hands": [(
        "What do gentle hands do?",
        "Gentle hands move slowly and carefully. They help solve a problem without hurting someone or spoiling a shared thing."
    )],
    "friendship": [(
        "What helps friendship when a mistake happens?",
        "Saying sorry and helping to fix the trouble both matter. Friendship grows stronger when friends are honest and kind."
    )],
    "sharing": [(
        "Why do friends take care of shared things?",
        "A shared thing belongs to the moment between them, so both people matter. Taking care of it shows care for the friend too."
    )],
}
KNOWLEDGE_ORDER = ["bee", "butterfly", "moth", "flowers", "cup", "window", "gentle_hands", "friendship", "sharing"]


CURATED = [
    StoryParams(
        setting="garden",
        visitor="bee",
        shared="flower_crown",
        response="flower_detour",
        instigator="Mina",
        instigator_gender="girl",
        friend="Jo",
        friend_gender="boy",
        caregiver="mother",
        relation="best_friends",
        trait="gentle",
    ),
    StoryParams(
        setting="playroom",
        visitor="moth",
        shared="paper_lantern",
        response="open_window",
        instigator="Ben",
        instigator_gender="boy",
        friend="Lila",
        friend_gender="girl",
        caregiver="father",
        relation="playmates",
        trait="careful",
    ),
    StoryParams(
        setting="porch",
        visitor="bee",
        shared="jam_tart",
        response="cup_card",
        instigator="Tess",
        instigator_gender="girl",
        friend="Milo",
        friend_gender="boy",
        caregiver="mother",
        relation="playmates",
        trait="hasty",
    ),
    StoryParams(
        setting="yard",
        visitor="butterfly",
        shared="flower_crown",
        response="napkin_wave",
        instigator="Sam",
        instigator_gender="boy",
        friend="Poppy",
        friend_gender="girl",
        caregiver="father",
        relation="best_friends",
        trait="patient",
    ),
]


def explain_rejection(setting: Setting, visitor: Visitor, shared: SharedThing, response: Response) -> str:
    if not visitor_fits(setting, visitor):
        return (
            f"(No story: a {visitor.label} does not fit {setting.place} in this tiny world, "
            f"so the visit would feel ungrounded.)"
        )
    if not visitor_drawn(visitor, shared):
        return (
            f"(No story: {shared.the} does not plausibly draw a {visitor.label}, "
            f"so there is no honest reason for the visitor to hover there.)"
        )
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it is too rough for this friendship world. "
            f"Pick a gentler response.)"
        )
    return (
        f"(No story: the response '{response.id}' does not sensibly work for a {visitor.label} "
        f"in {setting.place}.)"
    )


def _pick_child(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    shared = f["shared_cfg"]
    visitor = f["visitor_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "voodoo" and "swat". Two friends share {shared.phrase}, and a {visitor.label} comes near it, but kindness stops the swat.',
            f"Tell a soft rhyming friendship story where {a.id} wants to swat a {visitor.label}, but {b.id} gently talks {a.pronoun('object')} out of it and helps guide it away.",
            f'Write a simple story where a silly voodoo rhyme turns into a lesson about gentle hands and friendship.'
        ]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "voodoo" and "swat". Two friends share {shared.phrase}, a {visitor.label} comes close, and a quick swat causes a little oops before they mend things together.',
        f"Tell a rhyming friendship story where {a.id} makes a hasty swat near {shared.the}, then says sorry and helps fix the trouble with {b.id}.",
        f'Write a child-facing story where a tiny mistake shakes a shared game, but kindness and repair make the ending warm again.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    visitor = f["visitor_cfg"]
    shared = f["shared_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    relation = f["relation"].replace("_", " ")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {relation}, {a.id} and {b.id}, sharing {shared.the}. They are together from the first rhyme to the last one."
        ),
        (
            f"Why did {a.id} want to swat?",
            f"{a.id} saw the {visitor.label} close to {shared.the} and thought a swat would be the fastest fix. The idea came from hurry, not from meanness."
        ),
        (
            f"What warning did {b.id} give?",
            f"{b.id} warned that a swat could spoil {shared.the}. {b.pronoun().capitalize()} also felt that a rough choice could wobble their shared game and their friendship."
        ),
    ]
    if outcome == "averted":
        qa.extend([
            (
                f"What did {a.id} do after listening to {b.id}?",
                f"{a.id} put the raised hand back down and chose not to swat. That listening is what kept the shared thing safe."
            ),
            (
                "How did they solve the problem?",
                f"They used {response.id.replace('_', ' ')} to guide the {visitor.label} away gently. The solution worked because it fit both the place and the little visitor."
            ),
            (
                "How did the story end?",
                f"It ended with the friends singing again beside {shared.the}. The ending image shows that both the shared thing and the friendship stayed whole."
            ),
        ])
    else:
        qa.extend([
            (
                "What happened when the swat came too fast?",
                f"{shared.The} got {shared.spoil}. The quick hand changed a tiny worry into a real little mess."
            ),
            (
                f"How did {a.id} and {b.id} fix things?",
                f"They first guided the {visitor.label} away with {response.id.replace('_', ' ')}. Then {a.id} said sorry and both children helped repair {shared.the} together."
            ),
            (
                "How did friendship matter at the end?",
                f"The friendship mattered because apology and help turned the oops into a mended moment. The story ends warm because they cared for each other as much as for the shared thing."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["visitor_cfg"].tags) | set(f["shared_cfg"].tags) | set(f["response"].tags)
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, V, H, R) :- setting(S), visitor(V), shared(H), response(R),
                     affords(S, V), likes(V, T), lure(H, T),
                     handles(R, V), works_in(R, S), sense(R, N), sense_min(M), N >= M.

calm_bonus(2) :- trait(gentle).
calm_bonus(2) :- trait(patient).
calm_bonus(1) :- trait(kind).
calm_bonus(1) :- trait(careful).
calm_bonus(0) :- trait(bouncy).
calm_bonus(0) :- trait(hasty).

bond_value(3) :- relation(best_friends).
bond_value(2) :- relation(playmates).

score(B + C + 1) :- bond_value(B), calm_bonus(C).
averted :- score(S), impulse_init(I), S >= I.

outcome(averted) :- averted.
outcome(mended) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for visitor_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, visitor_id))
    for visitor_id, visitor in VISITORS.items():
        lines.append(asp.fact("visitor", visitor_id))
        for like in sorted(visitor.likes):
            lines.append(asp.fact("likes", visitor_id, like))
    for shared_id, shared in SHARED_THINGS.items():
        lines.append(asp.fact("shared", shared_id))
        lines.append(asp.fact("lure", shared_id, shared.lure))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        for visitor_id in sorted(response.handles):
            lines.append(asp.fact("handles", response_id, visitor_id))
        for setting_id in sorted(response.works_in):
            lines.append(asp.fact("works_in", response_id, setting_id))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
    for relation in RELATIONS:
        lines.append(asp.fact("relation_name", relation))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("impulse_init", IMPULSE_INIT))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("trait", params.trait),
        asp.fact("relation", params.relation),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.relation, params.trait) else "mended"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    cases = list(CURATED)
    for seed in range(80):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params() smoke test for seed {seed}.")
            break

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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a nursery-rhyme friendship tale about a quick swat, a gentle fix, and the word voodoo."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--shared", choices=SHARED_THINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--caregiver", choices=["mother", "father"])
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing response '{args.response}': it is too rough for this friendship world.)"
        )

    if args.setting and args.visitor and args.shared and args.response:
        setting = SETTINGS[args.setting]
        visitor = VISITORS[args.visitor]
        shared = SHARED_THINGS[args.shared]
        response = RESPONSES[args.response]
        if not (
            visitor_fits(setting, visitor)
            and visitor_drawn(visitor, shared)
            and response_works(setting, visitor, response)
            and response.sense >= SENSE_MIN
        ):
            raise StoryError(explain_rejection(setting, visitor, shared, response))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.visitor is None or c[1] == args.visitor)
        and (args.shared is None or c[2] == args.shared)
        and (args.response is None or c[3] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, visitor_id, shared_id, response_id = rng.choice(sorted(combos))
    instigator_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    instigator = _pick_child(rng, instigator_gender)
    friend = _pick_child(rng, friend_gender, avoid=instigator)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    relation = args.relation or rng.choice(RELATIONS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        visitor=visitor_id,
        shared=shared_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        friend=friend,
        friend_gender=friend_gender,
        caregiver=caregiver,
        relation=relation,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.visitor not in VISITORS:
        raise StoryError(f"(Unknown visitor: {params.visitor})")
    if params.shared not in SHARED_THINGS:
        raise StoryError(f"(Unknown shared thing: {params.shared})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.relation not in RELATIONS:
        raise StoryError(f"(Unknown relation: {params.relation})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    setting = SETTINGS[params.setting]
    visitor = VISITORS[params.visitor]
    shared = SHARED_THINGS[params.shared]
    response = RESPONSES[params.response]
    if not (
        visitor_fits(setting, visitor)
        and visitor_drawn(visitor, shared)
        and response_works(setting, visitor, response)
        and response.sense >= SENSE_MIN
    ):
        raise StoryError(explain_rejection(setting, visitor, shared, response))

    world = tell(
        setting=setting,
        visitor=visitor,
        shared_cfg=shared,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        friend=params.friend,
        friend_gender=params.friend_gender,
        caregiver=params.caregiver,
        relation=params.relation,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, visitor, shared, response) combos:\n")
        for setting, visitor, shared, response in combos:
            print(f"  {setting:8} {visitor:10} {shared:14} {response}")
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
            header = (
                f"### {p.instigator} & {p.friend}: {p.visitor} near {p.shared} "
                f"at {p.setting} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
