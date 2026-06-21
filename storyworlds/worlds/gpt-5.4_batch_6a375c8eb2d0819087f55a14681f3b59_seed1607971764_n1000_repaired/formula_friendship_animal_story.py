#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/formula_friendship_animal_story.py
=============================================================

A standalone story world for a gentle animal story about friendship, a broken
kite, and the right repair formula.

Premise
-------
Two young animal friends carry a handmade kite to a breezy place. A gust damages
the kite before it can fly. One friend feels afraid the special outing is over,
but the other friend stays, chooses a repair formula that actually fits the kind
of break, and helps mend the kite. They fly it together in the end.

Why the constraint exists
-------------------------
This little world knows a few kinds of kite trouble and a few repair formulas.
Not every formula fits every problem:

* tree-sap formula patches a torn sail
* clover-knot formula secures a loose tail
* twig-splint formula straightens a bent frame

A story is only valid when the chosen kite can plausibly suffer that damage
and the chosen formula truly repairs it. The world refuses mismatched choices,
because a weak fix would make the "formula" word feel arbitrary instead of
grounded in the state of the story.

Run it
------
    python storyworlds/worlds/gpt-5.4/formula_friendship_animal_story.py
    python storyworlds/worlds/gpt-5.4/formula_friendship_animal_story.py --kite leaf --damage torn_sail --formula sap
    python storyworlds/worlds/gpt-5.4/formula_friendship_animal_story.py --formula splint --damage loose_tail
    python storyworlds/worlds/gpt-5.4/formula_friendship_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/formula_friendship_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/formula_friendship_animal_story.py --trace
    python storyworlds/worlds/gpt-5.4/formula_friendship_animal_story.py --asp
    python storyworlds/worlds/gpt-5.4/formula_friendship_animal_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    material: str = ""
    # physical + emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "squirrel", "fox", "mouse", "hedgehog", "otter", "duck"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    breeze: str
    detail: str
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
class Kite:
    id: str
    label: str
    phrase: str
    material: str
    colors: str
    tail: str
    shape: str
    allowed_damage: set[str] = field(default_factory=set)
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
class Damage:
    id: str
    label: str
    start: str
    feeling: str
    repair_need: str
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
class Formula:
    id: str
    label: str
    spoken: str
    fixes: str
    method: str
    result: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_damage_worry(world: World) -> list[str]:
    out: list[str] = []
    kite = world.get("kite")
    if kite.meters["damaged"] < THRESHOLD:
        return out
    sig = ("damage_worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in (world.get("lead"), world.get("friend")):
        kid.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_repair_ready(world: World) -> list[str]:
    out: list[str] = []
    kite = world.get("kite")
    if kite.meters["patched"] < THRESHOLD:
        return out
    sig = ("repair_ready",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kite.meters["damaged"] = 0.0
    kite.meters["airworthy"] += 1
    world.get("lead").memes["relief"] += 1
    world.get("friend").memes["pride"] += 1
    out.append("__ready__")
    return out


def _r_launch_joy(world: World) -> list[str]:
    out: list[str] = []
    kite = world.get("kite")
    if kite.meters["launched"] < THRESHOLD or kite.meters["airworthy"] < THRESHOLD:
        return out
    sig = ("launch_joy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kite.meters["flying"] += 1
    for kid in (world.get("lead"), world.get("friend")):
        kid.memes["joy"] += 1
        kid.memes["belonging"] += 1
    out.append("__flying__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage_worry", tag="emotion", apply=_r_damage_worry),
    Rule(name="repair_ready", tag="physical", apply=_r_repair_ready),
    Rule(name="launch_joy", tag="emotion", apply=_r_launch_joy),
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


PLACES = {
    "hill": Place(
        id="hill",
        label="the clover hill",
        breeze="a steady hill breeze",
        detail="Below them, buttercups nodded and the little path curled through the grass.",
        tags={"wind", "hill"},
    ),
    "meadow": Place(
        id="meadow",
        label="the open meadow",
        breeze="a warm meadow breeze",
        detail="Tall grass swished around their ankles and little white clouds floated by.",
        tags={"wind", "meadow"},
    ),
    "lakeshore": Place(
        id="lakeshore",
        label="the sunny lakeshore",
        breeze="a cool breeze off the water",
        detail="The lake flashed like silver, and the reeds whispered at the edge.",
        tags={"wind", "lake"},
    ),
}

KITES = {
    "leaf": Kite(
        id="leaf",
        label="leaf kite",
        phrase="a leaf kite stitched from two broad green leaves",
        material="leaf",
        colors="green and gold",
        tail="a ribbon tail made of daisy stems",
        shape="diamond",
        allowed_damage={"torn_sail", "loose_tail"},
        tags={"kite", "leaf"},
    ),
    "bark": Kite(
        id="bark",
        label="bark kite",
        phrase="a bark kite with a smooth brown sail",
        material="bark",
        colors="brown and blue",
        tail="a tail trimmed with tiny feathers",
        shape="triangle",
        allowed_damage={"torn_sail", "loose_tail"},
        tags={"kite", "kite_tail"},
    ),
    "twig": Kite(
        id="twig",
        label="twig-frame kite",
        phrase="a twig-frame kite laced with pale grass thread",
        material="twig",
        colors="red and cream",
        tail="a fluttering tail of soft grass bows",
        shape="star",
        allowed_damage={"bent_frame", "loose_tail"},
        tags={"kite", "twig"},
    ),
}

DAMAGES = {
    "torn_sail": Damage(
        id="torn_sail",
        label="torn sail",
        start="A sharp gust snapped through the kite and opened a little tear in the sail.",
        feeling="The tear made the kite sag sadly in the middle.",
        repair_need="The sail needed a sticky patch before it could hold the wind again.",
        tags={"tear", "repair"},
    ),
    "loose_tail": Damage(
        id="loose_tail",
        label="loose tail",
        start="A twist of wind tugged hard, and the tail came loose with a soft flap.",
        feeling="Without its tail, the kite wobbled and would never balance in the air.",
        repair_need="The tail needed to be tied firmly so the kite could fly straight.",
        tags={"tail", "repair"},
    ),
    "bent_frame": Damage(
        id="bent_frame",
        label="bent frame",
        start="The kite bumped a stone by the path, and one thin frame stick bent sideways.",
        feeling="The crooked frame made the whole kite lean like a sleepy hat.",
        repair_need="The frame needed a careful splint before it could catch the wind.",
        tags={"frame", "repair"},
    ),
}

FORMULAS = {
    "sap": Formula(
        id="sap",
        label="tree-sap formula",
        spoken="the tree-sap formula",
        fixes="torn_sail",
        method="mixed a pearl of pine sap with three soft clover fuzzes and pressed the sticky patch over the tear",
        result="Soon the sail looked smooth again, with only a shiny line where the rip had been.",
        tags={"formula", "sap", "repair"},
    ),
    "knot": Formula(
        id="knot",
        label="clover-knot formula",
        spoken="the clover-knot formula",
        fixes="loose_tail",
        method="crossed the tail strings twice, tucked them through a clover loop, and pulled a snug little knot",
        result="The tail sat straight behind the kite, ready to dance in the breeze instead of falling off.",
        tags={"formula", "knot", "repair"},
    ),
    "splint": Formula(
        id="splint",
        label="twig-splint formula",
        spoken="the twig-splint formula",
        fixes="bent_frame",
        method="laid a tiny straight twig beside the bent stick and wrapped both with soft grass thread until the frame stood true again",
        result="The frame stopped leaning and held its starry shape nice and tall.",
        tags={"formula", "splint", "repair"},
    ),
}

ANIMALS = {
    "rabbit": {"type": "rabbit", "traits": ["quick", "bright"]},
    "squirrel": {"type": "squirrel", "traits": ["nimble", "busy"]},
    "fox": {"type": "fox", "traits": ["careful", "warm"]},
    "mouse": {"type": "mouse", "traits": ["small", "gentle"]},
    "hedgehog": {"type": "hedgehog", "traits": ["steady", "kind"]},
    "otter": {"type": "otter", "traits": ["playful", "helpful"]},
    "duck": {"type": "duck", "traits": ["cheerful", "calm"]},
}

NAMES = {
    "rabbit": ["Pip", "Mallow", "Clover"],
    "squirrel": ["Hazel", "Nutmeg", "Pipkin"],
    "fox": ["Fern", "Bramble", "Maple"],
    "mouse": ["Mimi", "Poppy", "Moss"],
    "hedgehog": ["Pebble", "Thistle", "Pine"],
    "otter": ["Ripple", "Sunny", "Drift"],
    "duck": ["Dottie", "Pebble", "Reed"],
}


def damage_allowed(kite: Kite, damage: Damage) -> bool:
    return damage.id in kite.allowed_damage


def formula_works(damage: Damage, formula: Formula) -> bool:
    return formula.fixes == damage.id


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for kite_id, kite in KITES.items():
            for damage_id, damage in DAMAGES.items():
                for formula_id, formula in FORMULAS.items():
                    if damage_allowed(kite, damage) and formula_works(damage, formula):
                        combos.append((place_id, kite_id, damage_id, formula_id))
    return combos


@dataclass
class StoryParams:
    place: str
    kite: str
    damage: str
    formula: str
    lead_species: str
    lead_name: str
    friend_species: str
    friend_name: str
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


CURATED = [
    StoryParams(
        place="hill",
        kite="leaf",
        damage="torn_sail",
        formula="sap",
        lead_species="rabbit",
        lead_name="Pip",
        friend_species="hedgehog",
        friend_name="Thistle",
        trait="hopeful",
        seed=None,
    ),
    StoryParams(
        place="meadow",
        kite="twig",
        damage="bent_frame",
        formula="splint",
        lead_species="mouse",
        lead_name="Mimi",
        friend_species="squirrel",
        friend_name="Hazel",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        place="lakeshore",
        kite="bark",
        damage="loose_tail",
        formula="knot",
        lead_species="duck",
        lead_name="Dottie",
        friend_species="otter",
        friend_name="Ripple",
        trait="cheerful",
        seed=None,
    ),
    StoryParams(
        place="hill",
        kite="twig",
        damage="loose_tail",
        formula="knot",
        lead_species="fox",
        lead_name="Fern",
        friend_species="rabbit",
        friend_name="Clover",
        trait="gentle",
        seed=None,
    ),
]


def _pick_species_name(rng: random.Random, avoid_name: str = "") -> tuple[str, str]:
    species = rng.choice(sorted(ANIMALS))
    names = [n for n in NAMES[species] if n != avoid_name]
    return species, rng.choice(names)


def explain_rejection(kite: Kite, damage: Damage, formula: Formula) -> str:
    if not damage_allowed(kite, damage):
        return (
            f"(No story: a {kite.label} would not plausibly suffer '{damage.label}' in this world. "
            f"Choose a damage the kite can really have.)"
        )
    return (
        f"(No story: {formula.label} does not repair a {damage.label}. "
        f"The formula must actually fit the break.)"
    )


def predict_repair(world: World, formula: Formula) -> dict:
    sim = world.copy()
    kite = sim.get("kite")
    if formula_works(sim.facts["damage_cfg"], formula):
        kite.meters["patched"] += 1
        propagate(sim, narrate=False)
    return {
        "airworthy": kite.meters["airworthy"] >= THRESHOLD,
        "damaged": kite.meters["damaged"] >= THRESHOLD,
    }


def introduce(world: World, lead: Entity, friend: Entity, kite: Kite) -> None:
    world.say(
        f"On a bright morning, {lead.id} the {lead.type} and {friend.id} the {friend.type} "
        f"carried {kite.phrase} between them."
    )
    world.say(
        f"It was {kite.colors}, with {kite.tail}, and the two friends had made it together the day before."
    )


def arrive(world: World, lead: Entity, friend: Entity) -> None:
    world.say(
        f"They climbed to {world.place.label}, where {world.place.breeze} was already moving through the grass."
    )
    world.say(world.place.detail)
    world.say(
        f'"Today our kite will fly the highest," {lead.id} said, and {friend.id} grinned and trotted faster.'
    )


def accident(world: World, lead: Entity, friend: Entity, damage: Damage) -> None:
    kite = world.get("kite")
    kite.meters["damaged"] += 1
    propagate(world, narrate=False)
    lead.memes["disappointment"] += 1
    world.say(damage.start)
    world.say(damage.feeling)
    world.say(
        f'{lead.id} stopped so suddenly that {friend.id} almost bumped into {lead.pronoun("object")}. '
        f'"Oh no," {lead.pronoun()} whispered. "We worked so hard on it."'
    )


def fear_losing_turn(world: World, lead: Entity, friend: Entity) -> None:
    world.say(
        f"{lead.id} lowered the kite and looked at the ground. "
        f'"You can still run in the wind if you want," {lead.pronoun()} said. '
        f'"I do not want to spoil the morning for you."'
    )
    friend.memes["loyalty"] += 1
    world.say(
        f'But {friend.id} moved close and shook {friend.pronoun("possessive")} head. '
        f'"A good flying day is better when we share it," {friend.pronoun()} said.'
    )


def choose_formula(world: World, friend: Entity, damage: Damage, formula: Formula) -> None:
    pred = predict_repair(world, formula)
    world.facts["predicted_airworthy"] = pred["airworthy"]
    friend.memes["care"] += 1
    world.say(
        f'{friend.id} studied the kite for a moment. "{damage.repair_need} '
        f'I know {formula.spoken}," {friend.pronoun()} said.'
    )


def mend(world: World, lead: Entity, friend: Entity, formula: Formula) -> None:
    kite = world.get("kite")
    kite.meters["patched"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they sat in the grass while {friend.id} {formula.method}."
    )
    world.say(formula.result)
    world.say(
        f"{lead.id}'s ears perked up again, and {friend.id} smiled when the kite felt steady in their paws."
    )


def launch(world: World, lead: Entity, friend: Entity, kite_cfg: Kite) -> None:
    kite = world.get("kite")
    kite.meters["launched"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {lead.id} held the line, {friend.id} lifted the {kite_cfg.label}, and they ran together."
    )
    world.say(
        f"The breeze caught it at once. Up went the {kite_cfg.shape}-shaped kite, bobbing and shining over their heads."
    )


def ending(world: World, lead: Entity, friend: Entity, formula: Formula) -> None:
    world.say(
        f'Soon both friends were laughing so hard that the line trembled in {lead.id}\'s paws. '
        f'When the kite made its highest loop, {friend.id} cheered as loudly as {lead.id}.'
    )
    world.say(
        f"Looking up, {lead.id} decided that the finest formula of all was not only {formula.spoken}. "
        f"It was a friend who stayed, helped, and held the string beside you."
    )


def tell(
    place: Place,
    kite_cfg: Kite,
    damage_cfg: Damage,
    formula_cfg: Formula,
    lead_species: str,
    lead_name: str,
    friend_species: str,
    friend_name: str,
    trait: str,
) -> World:
    world = World(place=place)
    lead = world.add(
        Entity(
            id=lead_name,
            kind="character",
            type=lead_species,
            label=lead_name,
            role="lead",
            traits=[trait] + ANIMALS[lead_species]["traits"],
            attrs={"friend": friend_name},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_species,
            label=friend_name,
            role="friend",
            traits=["loyal"] + ANIMALS[friend_species]["traits"],
            attrs={"friend": lead_name},
        )
    )
    kite = world.add(
        Entity(
            id="kite",
            kind="thing",
            type="kite",
            label=kite_cfg.label,
            material=kite_cfg.material,
            attrs={"shape": kite_cfg.shape},
        )
    )

    # Initialize any facts/rule-read state before propagation.
    world.facts["place_cfg"] = place
    world.facts["kite_cfg"] = kite_cfg
    world.facts["damage_cfg"] = damage_cfg
    world.facts["formula_cfg"] = formula_cfg
    world.facts["lead"] = lead
    world.facts["friend"] = friend
    world.facts["kite"] = kite
    world.facts["repaired"] = False
    world.facts["flying"] = False

    introduce(world, lead, friend, kite_cfg)
    arrive(world, lead, friend)

    world.para()
    accident(world, lead, friend, damage_cfg)
    fear_losing_turn(world, lead, friend)
    choose_formula(world, friend, damage_cfg, formula_cfg)

    world.para()
    mend(world, lead, friend, formula_cfg)
    launch(world, lead, friend, kite_cfg)
    ending(world, lead, friend, formula_cfg)

    world.facts["repaired"] = kite.meters["airworthy"] >= THRESHOLD
    world.facts["flying"] = kite.meters["flying"] >= THRESHOLD
    world.facts["damage_seen"] = kite.meters["patched"] >= THRESHOLD
    world.facts["friendship_help"] = friend.memes["care"] >= THRESHOLD and friend.memes["loyalty"] >= THRESHOLD
    return world


KNOWLEDGE = {
    "kite": [
        (
            "What does a kite need in order to fly well?",
            "A kite needs wind, a strong frame, and a sail and tail that are tied on properly. If one part is torn or loose, the kite wobbles or falls."
        )
    ],
    "formula": [
        (
            "What is a formula?",
            "A formula is a set way to do or make something. In this story, the formula is a careful repair method instead of a school problem."
        )
    ],
    "repair": [
        (
            "Why do small repairs matter?",
            "Small repairs matter because a tiny tear or loose knot can stop the whole thing from working. Fixing the right part can make something useful again."
        )
    ],
    "sap": [
        (
            "Why can sticky sap help mend a tear?",
            "Sticky sap can help hold torn pieces together for a while. It works best when the problem is a rip that needs a patch."
        )
    ],
    "knot": [
        (
            "Why does a kite tail need a firm knot?",
            "A kite tail helps balance the kite in the wind. If the tail comes loose, the kite can spin and wobble instead of flying straight."
        )
    ],
    "splint": [
        (
            "What does a splint do for a bent stick?",
            "A splint supports the weak part and helps hold it straight. That gives the frame a better shape again."
        )
    ],
    "friendship": [
        (
            "What does a good friend do when something goes wrong?",
            "A good friend stays nearby, helps with the problem, and does not rush off to enjoy the fun alone. Friendship often shows itself most clearly when plans go wrong."
        )
    ],
    "wind": [
        (
            "Why does wind help a kite rise?",
            "Moving air pushes against the kite's sail. When the kite is balanced, that push lifts it up into the sky."
        )
    ],
}
KNOWLEDGE_ORDER = ["kite", "formula", "repair", "sap", "knot", "splint", "friendship", "wind"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    kite_cfg = f["kite_cfg"]
    formula_cfg = f["formula_cfg"]
    damage_cfg = f["damage_cfg"]
    place = f["place_cfg"]
    return [
        (
            f'Write a short animal story for a 3-to-5-year-old that includes the word "formula". '
            f"Two animal friends bring a handmade {kite_cfg.label} to {place.label}, it suffers a {damage_cfg.label}, "
            f"and one friend helps fix it with {formula_cfg.label}."
        ),
        (
            f"Tell a gentle friendship story where {lead.id} the {lead.type} worries the day is spoiled, "
            f"but {friend.id} the {friend.type} stays to help mend the kite before they fly it together."
        ),
        (
            f'Write a simple animal story where the phrase "{formula_cfg.spoken}" matters because it is the right way '
            f"to repair a damaged kite and save a shared outing."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    kite_cfg = f["kite_cfg"]
    damage_cfg = f["damage_cfg"]
    formula_cfg = f["formula_cfg"]
    place = f["place_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} the {lead.type} and {friend.id} the {friend.type}. They are friends who carried a handmade {kite_cfg.label} to {place.label}."
        ),
        (
            "What problem happened to the kite?",
            f"The kite had a {damage_cfg.label}. {damage_cfg.start.split('. ')[0].strip()} made the kite stop feeling ready for the wind."
        ),
        (
            f"Why did {lead.id} think the morning might be spoiled?",
            f"{lead.id} saw that the kite was damaged and worried the flying plan was over. {lead.pronoun().capitalize()} even told {friend.id} to go on without {lead.pronoun('object')}, which shows how discouraged {lead.pronoun()} felt."
        ),
        (
            f"How did {friend.id} help?",
            f"{friend.id} stayed instead of rushing ahead and used {formula_cfg.spoken} to fix the problem. That help mattered because {formula_cfg.label} matched the {damage_cfg.label} the kite really had."
        ),
    ]
    if f.get("repaired"):
        qa.append(
            (
                "Why did the repair work?",
                f"The repair worked because the formula fit the exact break. {formula_cfg.result} After that, the kite was steady enough to catch the wind again."
            )
        )
    if f.get("flying"):
        qa.append(
            (
                "How did the story end?",
                f"The two friends ran together and the kite rose high above them. The ending proves something changed, because the morning began with worry but ended with shared laughter and a flying kite."
            )
        )
    if f.get("friendship_help"):
        qa.append(
            (
                "What does this story show about friendship?",
                f"It shows that friendship means staying when a problem appears, not just sharing the fun part. {friend.id} helped mend the kite first, and that is why both friends could enjoy the sky together."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"kite", "formula", "repair", "friendship"} | set(f["place_cfg"].tags)
    tags |= set(f["damage_cfg"].tags)
    tags |= set(f["formula_cfg"].tags)
    tags |= set(f["kite_cfg"].tags)
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
        if e.material:
            bits.append(f"material={e.material}")
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
damage_allowed(K, D) :- kite(K), damage(D), allows(K, D).
formula_works(D, F) :- damage(D), formula(F), fixes(F, D).
valid(P, K, D, F) :- place(P), kite(K), damage_allowed(K, D), formula_works(D, F).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for kid, kite in KITES.items():
        lines.append(asp.fact("kite", kid))
        for did in sorted(kite.allowed_damage):
            lines.append(asp.fact("allows", kid, did))
    for did in DAMAGES:
        lines.append(asp.fact("damage", did))
    for fid, formula in FORMULAS.items():
        lines.append(asp.fact("formula", fid))
        lines.append(asp.fact("fixes", fid, formula.fixes))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    tail = show or ""
    return f"{asp_facts()}\n{ASP_RULES}\n{tail}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases: list[StoryParams] = list(CURATED)
    try:
        generated = generate(resolve_params(build_parser().parse_args([]), random.Random(123)))
        smoke_cases.append(generated.params)
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE FAIL: default resolve/generate crashed: {err}")

    for params in smoke_cases[:3]:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            with io.StringIO() as buf:
                with redirect_stdout(buf):
                    emit(sample, trace=False, qa=True, header="smoke")
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"SMOKE FAIL for {params}: {err}")

    if rc == 0:
        print("OK: smoke-tested normal generate/emit paths.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal friendship storyworld: a broken kite, the right formula, and a shared ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--kite", choices=KITES)
    ap.add_argument("--damage", choices=DAMAGES)
    ap.add_argument("--formula", choices=FORMULAS)
    ap.add_argument("--lead-species", choices=sorted(ANIMALS))
    ap.add_argument("--friend-species", choices=sorted(ANIMALS))
    ap.add_argument("--lead-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.kite and args.damage and args.formula:
        kite = KITES[args.kite]
        damage = DAMAGES[args.damage]
        formula = FORMULAS[args.formula]
        if not (damage_allowed(kite, damage) and formula_works(damage, formula)):
            raise StoryError(explain_rejection(kite, damage, formula))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.kite is None or combo[1] == args.kite)
        and (args.damage is None or combo[2] == args.damage)
        and (args.formula is None or combo[3] == args.formula)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, kite_id, damage_id, formula_id = rng.choice(sorted(combos))

    lead_species = args.lead_species or rng.choice(sorted(ANIMALS))
    friend_species = args.friend_species or rng.choice(sorted(ANIMALS))

    if args.lead_name:
        lead_name = args.lead_name
    else:
        lead_name = rng.choice(NAMES[lead_species])

    if args.friend_name:
        friend_name = args.friend_name
    else:
        friend_choices = [n for n in NAMES[friend_species] if n != lead_name]
        if not friend_choices:
            _, picked_name = _pick_species_name(rng, avoid_name=lead_name)
            friend_name = picked_name
        else:
            friend_name = rng.choice(friend_choices)

    trait = rng.choice(["hopeful", "careful", "cheerful", "gentle", "eager", "bright"])

    return StoryParams(
        place=place_id,
        kite=kite_id,
        damage=damage_id,
        formula=formula_id,
        lead_species=lead_species,
        lead_name=lead_name,
        friend_species=friend_species,
        friend_name=friend_name,
        trait=trait,
        seed=None,
    )


def _require_key(registry: dict, key: str, label: str):
    if key not in registry:
        raise StoryError(f"(Invalid {label}: {key})")
    return registry[key]


def generate(params: StoryParams) -> StorySample:
    place = _require_key(PLACES, params.place, "place")
    kite = _require_key(KITES, params.kite, "kite")
    damage = _require_key(DAMAGES, params.damage, "damage")
    formula = _require_key(FORMULAS, params.formula, "formula")
    if not damage_allowed(kite, damage) or not formula_works(damage, formula):
        raise StoryError(explain_rejection(kite, damage, formula))
    if params.lead_species not in ANIMALS:
        raise StoryError(f"(Invalid lead species: {params.lead_species})")
    if params.friend_species not in ANIMALS:
        raise StoryError(f"(Invalid friend species: {params.friend_species})")
    if not params.lead_name.strip() or not params.friend_name.strip():
        raise StoryError("(Character names must not be empty.)")

    world = tell(
        place=place,
        kite_cfg=kite,
        damage_cfg=damage,
        formula_cfg=formula,
        lead_species=params.lead_species,
        lead_name=params.lead_name,
        friend_species=params.friend_species,
        friend_name=params.friend_name,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, kite, damage, formula) combos:\n")
        for place, kite, damage, formula in combos:
            print(f"  {place:10} {kite:8} {damage:11} {formula}")
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
            header = f"### {p.lead_name} & {p.friend_name}: {p.kite} / {p.damage} / {p.formula} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
