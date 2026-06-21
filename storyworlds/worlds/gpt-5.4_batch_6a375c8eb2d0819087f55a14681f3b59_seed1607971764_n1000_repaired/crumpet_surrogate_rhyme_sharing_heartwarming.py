#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crumpet_surrogate_rhyme_sharing_heartwarming.py
===========================================================================

A standalone storyworld about one warm crumpet, a shy child at the edge of a
little rhyme circle, and a small surrogate heart that helps everyone make room.

This world models a cozy social problem instead of a physical accident:
someone wants to join, but is missing the little heart token the group uses to
begin its snack-and-rhyme game. A grown-up can make a sensible surrogate heart
from whatever the place actually has on hand, and the host child may either
share easily or need one more gentle nudge before splitting the crumpet.

The state matters:

- the crumpet has physical warmth and portions
- the guest has hunger and social hesitation
- the host has pride, care, and generosity
- a surrogate heart changes whether the guest feels included enough to join
- splitting the crumpet changes the ending image and the Q&A

Run it
------
    python storyworlds/worlds/gpt-5.4/crumpet_surrogate_rhyme_sharing_heartwarming.py
    python storyworlds/worlds/gpt-5.4/crumpet_surrogate_rhyme_sharing_heartwarming.py --place library_nook --surrogate paper_heart
    python storyworlds/worlds/gpt-5.4/crumpet_surrogate_rhyme_sharing_heartwarming.py --divider cookie_stamp
    python storyworlds/worlds/gpt-5.4/crumpet_surrogate_rhyme_sharing_heartwarming.py --all --qa
    python storyworlds/worlds/gpt-5.4/crumpet_surrogate_rhyme_sharing_heartwarming.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
OPEN_TRAITS = {"bighearted", "gentle", "sharing"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian", "teacher"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "librarian": "librarian",
            "teacher": "teacher",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    nook: str
    materials: set[str] = field(default_factory=set)
    tools: set[str] = field(default_factory=set)
    sounds: str = ""
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
class Topping:
    id: str
    label: str
    shine: str
    scent: str
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
class Surrogate:
    id: str
    label: str
    material: str
    fold_text: str
    hold_text: str
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
class Divider:
    id: str
    label: str
    tool: str
    sense: int
    text: str
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


def _r_left_out(world: World) -> list[str]:
    out: list[str] = []
    guest = world.get("guest")
    if guest.memes["shy"] < THRESHOLD:
        return out
    if world.facts.get("has_surrogate"):
        return out
    sig = ("left_out", guest.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guest.memes["lonely"] += 1
    host = world.get("host")
    host.memes["worry"] += 1
    out.append("__left_out__")
    return out


def _r_share_joy(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("shared"):
        return out
    sig = ("share_joy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    host = world.get("host")
    guest = world.get("guest")
    host.memes["joy"] += 1
    guest.memes["joy"] += 1
    guest.memes["hunger"] = 0.0
    guest.memes["belonging"] += 1
    host.memes["pride"] = 0.0
    out.append("__share__")
    return out


def _r_surrogate_belongs(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("has_surrogate"):
        return out
    guest = world.get("guest")
    sig = ("surrogate_belongs", guest.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guest.memes["hope"] += 1
    guest.memes["shy"] = max(0.0, guest.memes["shy"] - 1.0)
    out.append("__surrogate__")
    return out


CAUSAL_RULES = [
    Rule(name="left_out", tag="social", apply=_r_left_out),
    Rule(name="share_joy", tag="social", apply=_r_share_joy),
    Rule(name="surrogate_belongs", tag="social", apply=_r_surrogate_belongs),
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


def place_supports(place: Place, surrogate: Surrogate, divider: Divider) -> bool:
    return surrogate.material in place.materials and divider.tool in place.tools


def sensible_dividers() -> list[Divider]:
    return [d for d in DIVIDERS.values() if d.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for topping_id in TOPPINGS:
            for surrogate_id, surrogate in SURROGATES.items():
                for divider_id, divider in DIVIDERS.items():
                    if divider.sense >= SENSE_MIN and place_supports(place, surrogate, divider):
                        combos.append((place_id, topping_id, surrogate_id, divider_id))
    return combos


def predict_left_out(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    guest = sim.get("guest")
    return {
        "lonely": guest.memes["lonely"] >= THRESHOLD,
        "worry": sim.get("host").memes["worry"],
    }


def outcome_of(params: "StoryParams") -> str:
    if params.host_trait in OPEN_TRAITS:
        return "easy_share"
    return "coaxed_share"


def introduce(world: World, host: Entity, helper: Entity, topping: Topping) -> None:
    crumpet = world.get("crumpet")
    host.memes["joy"] += 1
    world.say(
        f"In {world.place.nook}, {host.id} sat beside {helper.label_word} with a warm "
        f"crumpet on a little plate. {topping.scent} and {world.place.sounds}"
    )
    world.say(
        f"{host.id} had spread {topping.label} across the round top until the crumpet "
        f"{topping.shine}."
    )


def set_game(world: World, host: Entity) -> None:
    world.say(
        f'"Care to share, care to rhyme," {host.id} whispered, tapping the table in time. '
        f"It was the small beginning song for the morning circle."
    )


def arrive_guest(world: World, guest: Entity) -> None:
    guest.memes["hunger"] += 1
    guest.memes["shy"] += 1
    world.say(
        f"Then {guest.id} came to the edge of the nook and stopped. "
        f"{guest.pronoun().capitalize()} had empty hands and a hopeful face."
    )


def notice_missing(world: World, helper: Entity, guest: Entity) -> None:
    pred = predict_left_out(world)
    world.facts["predicted_lonely"] = pred["lonely"]
    world.facts["predicted_worry"] = pred["worry"]
    helper.memes["care"] += 1
    world.say(
        f'{helper.label_word.capitalize()} noticed the pause at once. "{guest.id}, where is your little heart token?" '
        f'{helper.pronoun()} asked softly.'
    )
    world.say(
        f'{guest.id} looked down. "I lost it on the way," {guest.pronoun()} said. '
        f'"And I do not have a snack either."'
    )


def hesitate(world: World, host: Entity, guest: Entity) -> None:
    host.memes["pride"] += 1
    world.say(
        f"{host.id} curled both hands around the plate. The crumpet was only one crumpet, "
        f"and it smelled too good to give away."
    )
    if guest.memes["lonely"] >= THRESHOLD:
        world.say(
            f"{guest.id} took one half-step back, as if {guest.pronoun()} might leave the circle before it began."
        )


def make_surrogate(world: World, helper: Entity, surrogate: Surrogate, guest: Entity) -> None:
    world.facts["has_surrogate"] = True
    heart = world.add(Entity(
        id="surrogate_heart",
        type="token",
        label=surrogate.label,
        role="surrogate",
        tags=set(surrogate.tags),
        attrs={"material": surrogate.material},
    ))
    heart.meters["present"] = 1
    propagate(world, narrate=False)
    world.say(
        f'{helper.label_word.capitalize()} smiled and {surrogate.fold_text}. '
        f'"Your real heart may be missing," {helper.pronoun()} said, '
        f'"but this {surrogate.label} can be a surrogate until we find it."'
    )
    world.say(
        f"{guest.id} {surrogate.hold_text}, and some of the tightness left {guest.pronoun('possessive')} shoulders."
    )


def nudge_with_rhyme(world: World, helper: Entity, host: Entity, guest: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.label_word.capitalize()} touched the table and sang, '
        f'"A bite for me, a bite for you, a kind heart makes room for two."'
    )
    world.say(
        f"{host.id} looked at {guest.id}, then at the little surrogate heart, and listened to the rhyme all the way to the end."
    )


def split_crumpet(world: World, host: Entity, guest: Entity, divider: Divider) -> None:
    crumpet = world.get("crumpet")
    if crumpet.meters["portions"] < 2:
        raise StoryError("(No story: the crumpet is too small to split fairly.)")
    crumpet.meters["portions"] = 2.0
    world.facts["shared"] = True
    host.memes["generosity"] += 1
    guest.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{host.id} nodded, took the {divider.label}, and {divider.text}. "
        f"One half stayed on the little plate, and the other half went to {guest.id}."
    )


def join_circle(world: World, host: Entity, guest: Entity) -> None:
    world.say(
        f"Soon the two children sat knee to knee, each with a warm piece of crumpet and a turn in the rhyme."
    )
    world.say(
        f'"Share and care, warm and fair," they sang together, and even the quiet nook seemed to hum back.'
    )


def ending_image(world: World, helper: Entity, guest: Entity) -> None:
    world.say(
        f"When the real token was still nowhere to be seen, nobody minded anymore. "
        f"The surrogate heart rested beside {guest.id}'s plate, and it had already done the most important job."
    )
    world.say(
        f"{helper.label_word.capitalize()} watched the crumbs, the smiles, and the easy little rhyme, and knew the circle had grown bigger in exactly the right way."
    )


def tell(
    place: Place,
    topping: Topping,
    surrogate: Surrogate,
    divider: Divider,
    host_name: str = "Mina",
    host_gender: str = "girl",
    guest_name: str = "Ollie",
    guest_gender: str = "boy",
    helper_type: str = "librarian",
    host_trait: str = "bighearted",
) -> World:
    world = World(place)
    host = world.add(Entity(
        id=host_name,
        kind="character",
        type=host_gender,
        role="host",
        traits=[host_trait],
        attrs={},
    ))
    guest = world.add(Entity(
        id=guest_name,
        kind="character",
        type=guest_gender,
        role="guest",
        traits=["shy"],
        attrs={},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        attrs={},
    ))
    crumpet = world.add(Entity(
        id="crumpet",
        type="food",
        label="crumpet",
        tags={"crumpet"},
        attrs={"topping": topping.id},
    ))
    crumpet.meters["warmth"] = 1
    crumpet.meters["portions"] = 2
    world.facts["has_surrogate"] = False
    world.facts["shared"] = False
    world.facts["host_trait"] = host_trait

    introduce(world, host, helper, topping)
    set_game(world, host)

    world.para()
    arrive_guest(world, guest)
    propagate(world, narrate=False)
    notice_missing(world, helper, guest)
    propagate(world, narrate=False)
    hesitate(world, host, guest)

    world.para()
    make_surrogate(world, helper, surrogate, guest)
    if host_trait in OPEN_TRAITS:
        split_crumpet(world, host, guest, divider)
        outcome = "easy_share"
    else:
        nudge_with_rhyme(world, helper, host, guest)
        split_crumpet(world, host, guest, divider)
        outcome = "coaxed_share"

    join_circle(world, host, guest)
    ending_image(world, helper, guest)

    world.facts.update(
        host=host,
        guest=guest,
        helper=helper,
        crumpet=crumpet,
        place_cfg=place,
        topping=topping,
        surrogate=surrogate,
        divider=divider,
        outcome=outcome,
        shared=world.facts["shared"],
        surrogate_ready=world.facts["has_surrogate"],
    )
    return world


PLACES = {
    "library_nook": Place(
        id="library_nook",
        label="library nook",
        nook="the sunniest corner of the library",
        materials={"paper", "bookmark_card"},
        tools={"knife", "wooden_spreader"},
        sounds="The radiator purred, and pages whispered from a nearby basket.",
        tags={"library"},
    ),
    "kitchen_table": Place(
        id="kitchen_table",
        label="kitchen table",
        nook="the warm kitchen table by the window",
        materials={"paper", "napkin"},
        tools={"knife", "spoon"},
        sounds="A kettle ticked itself quiet on the stove.",
        tags={"kitchen"},
    ),
    "garden_bench": Place(
        id="garden_bench",
        label="garden bench",
        nook="a painted bench near the garden gate",
        materials={"leaf", "napkin"},
        tools={"wooden_spreader", "spoon"},
        sounds="A blackbird hopped nearby, tipping its song into the morning.",
        tags={"garden"},
    ),
    "hall_step": Place(
        id="hall_step",
        label="hall step",
        nook="the chilly front hall step",
        materials={"button"},
        tools={"cookie_stamp"},
        sounds="The house was still and drafty.",
        tags={"hall"},
    ),
}

TOPPINGS = {
    "honey": Topping(
        id="honey",
        label="honey",
        shine="shone like a little gold pond",
        scent="It smelled sweet and warm",
        tags={"honey"},
    ),
    "berry_jam": Topping(
        id="berry_jam",
        label="berry jam",
        shine="glowed ruby-red in the holes",
        scent="It smelled bright and berry-sweet",
        tags={"jam"},
    ),
    "cinnamon_butter": Topping(
        id="cinnamon_butter",
        label="cinnamon butter",
        shine="looked soft and sunny at the edges",
        scent="It smelled buttery and snug",
        tags={"butter"},
    ),
}

SURROGATES = {
    "paper_heart": Surrogate(
        id="paper_heart",
        label="paper heart",
        material="paper",
        fold_text="folded a square of paper twice and snipped out a neat heart",
        hold_text="held the paper heart carefully in both hands",
        tags={"paper", "surrogate"},
    ),
    "napkin_heart": Surrogate(
        id="napkin_heart",
        label="napkin heart",
        material="napkin",
        fold_text="pressed a napkin flat and folded it into a soft white heart",
        hold_text="smoothed the napkin heart on the table as if it were precious",
        tags={"napkin", "surrogate"},
    ),
    "leaf_heart": Surrogate(
        id="leaf_heart",
        label="leaf heart",
        material="leaf",
        fold_text="found a broad green leaf and trimmed it into a tiny heart",
        hold_text="set the leaf heart beside the plate and smiled at it",
        tags={"leaf", "surrogate"},
    ),
}

DIVIDERS = {
    "butter_knife": Divider(
        id="butter_knife",
        label="butter knife",
        tool="knife",
        sense=3,
        text="cut the crumpet neatly through the middle",
        qa_text="cut the crumpet neatly in half with a butter knife",
        tags={"knife", "sharing"},
    ),
    "wooden_spreader": Divider(
        id="wooden_spreader",
        label="wooden spreader",
        tool="wooden_spreader",
        sense=3,
        text="pressed and parted the soft crumpet into two even halves",
        qa_text="used a wooden spreader to part the soft crumpet into two even halves",
        tags={"spreader", "sharing"},
    ),
    "teaspoon": Divider(
        id="teaspoon",
        label="teaspoon",
        tool="spoon",
        sense=2,
        text="gently pulled the soft middle apart until the crumpet made two tidy pieces",
        qa_text="used a teaspoon to pull the soft crumpet into two tidy pieces",
        tags={"spoon", "sharing"},
    ),
    "cookie_stamp": Divider(
        id="cookie_stamp",
        label="cookie stamp",
        tool="cookie_stamp",
        sense=1,
        text="poked at the crumpet with a cookie stamp",
        qa_text="poked at the crumpet with a cookie stamp",
        tags={"stamp"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tess", "Ruby", "Nora", "Poppy", "Elsie"]
BOY_NAMES = ["Ollie", "Ben", "Theo", "Max", "Finn", "Hugo", "Sam"]
TRAITS = ["bighearted", "gentle", "sharing", "careful", "proud", "hesitant"]


@dataclass
class StoryParams:
    place: str
    topping: str
    surrogate: str
    divider: str
    host_name: str
    host_gender: str
    guest_name: str
    guest_gender: str
    helper_type: str
    host_trait: str
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
    "crumpet": [(
        "What is a crumpet?",
        "A crumpet is a small round bread cooked on a griddle. It is soft inside, with little holes that can hold melted butter or jam."
    )],
    "surrogate": [(
        "What does surrogate mean?",
        "A surrogate is a stand-in that takes the place of something else for a while. In this story, the child used a small heart that stood in until the real one could be found."
    )],
    "sharing": [(
        "Why does sharing food sometimes help someone feel better?",
        "Sharing can help someone feel welcome because it says, \"There is room for you with me.\" When the food is split fairly, the kindness matters as much as the snack."
    )],
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme is when words sound alike at the end, like care and share. Rhymes can make a song or saying feel easy to remember."
    )],
    "paper": [(
        "Why is paper good for making a quick heart shape?",
        "Paper is easy to fold and cut into simple shapes. That makes it useful when you need a fast little stand-in."
    )],
    "napkin": [(
        "What is a napkin for?",
        "A napkin helps keep hands and tables clean during a snack. Because it folds softly, it can also be shaped into something gentle and temporary."
    )],
    "leaf": [(
        "Why can a leaf be used for a small craft?",
        "A broad leaf already has a clear shape and a firm surface. With care, it can become a tiny natural decoration."
    )],
}

KNOWLEDGE_ORDER = ["crumpet", "surrogate", "sharing", "rhyme", "paper", "napkin", "leaf"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    host = f["host"]
    guest = f["guest"]
    surrogate = f["surrogate"]
    place = f["place_cfg"]
    outcome = f["outcome"]
    mood = "shares right away" if outcome == "easy_share" else "needs a gentle rhyme before sharing"
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "crumpet" and "surrogate" and takes place in a {place.label}.',
        f"Tell a gentle snack-time story where {host.id} has one warm crumpet, {guest.id} arrives without the usual heart token, and a {surrogate.label} helps the shy child join the rhyme circle.",
        f"Write a cozy story about sharing where the host child {mood}, and the ending proves that kindness made room for two.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    host = f["host"]
    guest = f["guest"]
    helper = f["helper"]
    surrogate = f["surrogate"]
    divider = f["divider"]
    topping = f["topping"]
    place = f["place_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {host.id}, {guest.id}, and the {helper.label_word} in {place.label}. They began with one warm crumpet and ended with a fuller, friendlier circle."
        ),
        (
            f"Why did {guest.id} stop at the edge of the nook?",
            f"{guest.id} had lost the little heart token and did not have a snack either, so {guest.pronoun()} felt shy about joining in. Without both an invitation and a bite to eat, the circle felt like it might not have room for {guest.pronoun('object')}."
        ),
        (
            "What was the surrogate in the story?",
            f"The surrogate was a {surrogate.label} made as a stand-in for the missing token. It helped {guest.id} feel included right away, even before the real token could be found."
        ),
    ]
    if f["outcome"] == "easy_share":
        qa.append((
            f"How did {host.id} share the crumpet?",
            f"{host.id} used the {divider.label} and {divider.qa_text}. Then one warm half went to {guest.id}, which turned the lonely moment into a shared one."
        ))
    else:
        qa.append((
            f"What helped {host.id} decide to share?",
            f"The {helper.label_word} sang a small rhyme about making room for two, and {host.id} looked at {guest.id}'s surrogate heart while listening. That gentle nudge turned {host.pronoun('possessive')} hesitation into generosity."
        ))
        qa.append((
            f"How did {host.id} share the crumpet after that?",
            f"{host.id} used the {divider.label} and {divider.qa_text}. The fair split showed that the rhyme had changed the feeling at the table, not just the snack."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with both children sitting close together, each holding a warm piece of {topping.label} crumpet and singing a rhyme. The final image shows that sharing made the circle feel safe, full, and kind."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"crumpet", "surrogate", "sharing", "rhyme"}
    tags |= set(f["surrogate"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:15} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="library_nook",
        topping="honey",
        surrogate="paper_heart",
        divider="butter_knife",
        host_name="Mina",
        host_gender="girl",
        guest_name="Ollie",
        guest_gender="boy",
        helper_type="librarian",
        host_trait="bighearted",
    ),
    StoryParams(
        place="kitchen_table",
        topping="berry_jam",
        surrogate="napkin_heart",
        divider="teaspoon",
        host_name="Theo",
        host_gender="boy",
        guest_name="Ruby",
        guest_gender="girl",
        helper_type="mother",
        host_trait="careful",
    ),
    StoryParams(
        place="garden_bench",
        topping="cinnamon_butter",
        surrogate="leaf_heart",
        divider="wooden_spreader",
        host_name="Poppy",
        host_gender="girl",
        guest_name="Finn",
        guest_gender="boy",
        helper_type="teacher",
        host_trait="sharing",
    ),
    StoryParams(
        place="library_nook",
        topping="berry_jam",
        surrogate="paper_heart",
        divider="wooden_spreader",
        host_name="Nora",
        host_gender="girl",
        guest_name="Ben",
        guest_gender="boy",
        helper_type="librarian",
        host_trait="hesitant",
    ),
]


def explain_rejection(place: Place, surrogate: Surrogate, divider: Divider) -> str:
    if surrogate.material not in place.materials:
        return (
            f"(No story: {place.label} does not have the right material for a {surrogate.label}. "
            f"A surrogate heart should be made from something the place actually has.)"
        )
    if divider.sense < SENSE_MIN:
        return (
            f"(Refusing divider '{divider.id}': it scores too low on common sense "
            f"(sense={divider.sense} < {SENSE_MIN}). Splitting a soft crumpet should use a sensible tool.)"
        )
    if divider.tool not in place.tools:
        return (
            f"(No story: {place.label} does not have a suitable tool for {divider.label}. "
            f"The crumpet has to be split with something the place really provides.)"
        )
    return "(No story: this place cannot support that surrogate and divider together.)"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(P, T, S, D) :- place(P), topping(T), surrogate(S), divider(D),
                     needs_material(S, M), has_material(P, M),
                     needs_tool(D, Tool), has_tool(P, Tool),
                     sense(D, V), sense_min(Min), V >= Min.

% --- outcome inference -----------------------------------------------------
open_share :- host_trait(T), open_trait(T).
outcome(easy_share) :- open_share.
outcome(coaxed_share) :- not open_share.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for material in sorted(place.materials):
            lines.append(asp.fact("has_material", place_id, material))
        for tool in sorted(place.tools):
            lines.append(asp.fact("has_tool", place_id, tool))
    for topping_id in TOPPINGS:
        lines.append(asp.fact("topping", topping_id))
    for surrogate_id, surrogate in SURROGATES.items():
        lines.append(asp.fact("surrogate", surrogate_id))
        lines.append(asp.fact("needs_material", surrogate_id, surrogate.material))
    for divider_id, divider in DIVIDERS.items():
        lines.append(asp.fact("divider", divider_id))
        lines.append(asp.fact("needs_tool", divider_id, divider.tool))
        lines.append(asp.fact("sense", divider_id, divider.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(OPEN_TRAITS):
        lines.append(asp.fact("open_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("host_trait", params.host_trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params failed on seed {seed}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        with io.StringIO() as buf:
            old = sys.stdout
            try:
                sys.stdout = buf
                emit(smoke, trace=True, qa=True, header="### smoke")
            finally:
                sys.stdout = old
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: one warm crumpet, a surrogate heart, and a sharing rhyme."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--topping", choices=TOPPINGS)
    ap.add_argument("--surrogate", choices=SURROGATES)
    ap.add_argument("--divider", choices=DIVIDERS)
    ap.add_argument("--helper", choices=["mother", "father", "librarian", "teacher"])
    ap.add_argument("--host-trait", choices=TRAITS)
    ap.add_argument("--host-name")
    ap.add_argument("--guest-name")
    ap.add_argument("--host-gender", choices=["girl", "boy"])
    ap.add_argument("--guest-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.surrogate and args.divider:
        place = PLACES[args.place]
        surrogate = SURROGATES[args.surrogate]
        divider = DIVIDERS[args.divider]
        if not place_supports(place, surrogate, divider) or divider.sense < SENSE_MIN:
            raise StoryError(explain_rejection(place, surrogate, divider))
    if args.divider and DIVIDERS[args.divider].sense < SENSE_MIN:
        surrogate_id = args.surrogate or next(iter(SURROGATES))
        place_id = args.place or next(iter(PLACES))
        raise StoryError(explain_rejection(PLACES[place_id], SURROGATES[surrogate_id], DIVIDERS[args.divider]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.topping is None or combo[1] == args.topping)
        and (args.surrogate is None or combo[2] == args.surrogate)
        and (args.divider is None or combo[3] == args.divider)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, topping_id, surrogate_id, divider_id = rng.choice(sorted(combos))
    host_gender = args.host_gender or rng.choice(["girl", "boy"])
    guest_gender = args.guest_gender or rng.choice(["girl", "boy"])
    host_name = args.host_name or _pick_name(rng, host_gender)
    guest_name = args.guest_name or _pick_name(rng, guest_gender, avoid=host_name)
    helper_type = args.helper or rng.choice(["mother", "father", "librarian", "teacher"])
    host_trait = args.host_trait or rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        topping=topping_id,
        surrogate=surrogate_id,
        divider=divider_id,
        host_name=host_name,
        host_gender=host_gender,
        guest_name=guest_name,
        guest_gender=guest_gender,
        helper_type=helper_type,
        host_trait=host_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.topping not in TOPPINGS:
        raise StoryError(f"(Unknown topping: {params.topping})")
    if params.surrogate not in SURROGATES:
        raise StoryError(f"(Unknown surrogate: {params.surrogate})")
    if params.divider not in DIVIDERS:
        raise StoryError(f"(Unknown divider: {params.divider})")

    place = PLACES[params.place]
    surrogate = SURROGATES[params.surrogate]
    divider = DIVIDERS[params.divider]
    if not place_supports(place, surrogate, divider) or divider.sense < SENSE_MIN:
        raise StoryError(explain_rejection(place, surrogate, divider))

    world = tell(
        place=place,
        topping=TOPPINGS[params.topping],
        surrogate=surrogate,
        divider=divider,
        host_name=params.host_name,
        host_gender=params.host_gender,
        guest_name=params.guest_name,
        guest_gender=params.guest_gender,
        helper_type=params.helper_type,
        host_trait=params.host_trait,
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
        print(f"{len(combos)} compatible (place, topping, surrogate, divider) combos:\n")
        for place, topping, surrogate, divider in combos:
            print(f"  {place:13} {topping:16} {surrogate:12} {divider}")
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
            header = (
                f"### {p.host_name} & {p.guest_name}: {p.place}, {p.surrogate}, "
                f"{p.divider}, {outcome_of(p)}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
