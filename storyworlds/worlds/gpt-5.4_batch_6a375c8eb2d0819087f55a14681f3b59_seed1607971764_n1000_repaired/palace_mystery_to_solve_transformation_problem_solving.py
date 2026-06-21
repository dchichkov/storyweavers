#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/palace_mystery_to_solve_transformation_problem_solving.py
====================================================================================

A standalone story world about small palace animals solving a gentle mystery.

Seed:
    Words: palace
    Features: Mystery to Solve, Transformation, Problem Solving
    Style: Animal Story

World premise
-------------
A young palace animal helper discovers that an important little object has gone
missing before a celebration. The clue only makes sense once another tiny
creature finishes a real transformation -- a caterpillar becomes a butterfly, a
tadpole becomes a frog, or a silkworm becomes a moth. The heroes solve the
mystery by choosing the method that actually fits the hiding place.

The world model enforces a compact common-sense constraint:

    mystery habitat must match transformation habitat
    and the chosen method must be the one that can actually reach/reveal the item

So the garden mystery is solved with a small ladder, the pond mystery with a
reed hook, and the hall mystery with a lantern search. Invalid explicit choices
raise StoryError with a plain explanation.

Run it
------
    python storyworlds/worlds/gpt-5.4/palace_mystery_to_solve_transformation_problem_solving.py
    python storyworlds/worlds/gpt-5.4/palace_mystery_to_solve_transformation_problem_solving.py --mystery moon_clasp
    python storyworlds/worlds/gpt-5.4/palace_mystery_to_solve_transformation_problem_solving.py --method lantern_search
    python storyworlds/worlds/gpt-5.4/palace_mystery_to_solve_transformation_problem_solving.py --all
    python storyworlds/worlds/gpt-5.4/palace_mystery_to_solve_transformation_problem_solving.py --qa --json
    python storyworlds/worlds/gpt-5.4/palace_mystery_to_solve_transformation_problem_solving.py --verify
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
        gender = self.attrs.get("gender", "")
        if gender == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        return self.label or self.type
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Mystery:
    id: str
    item_label: str
    item_the: str
    event_name: str
    habitat: str
    place_label: str
    missing_line: str
    clue_line: str
    reveal_line: str
    solve_line: str
    ending_line: str
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
class Transformation:
    id: str
    before_name: str
    after_name: str
    habitat: str
    place_label: str
    wait_line: str
    transform_line: str
    clue_result: str
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
class Method:
    id: str
    label: str
    habitat: str
    action_line: str
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


def _r_missing_worry(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    hero = world.get("hero")
    friend = world.get("friend")
    if item.meters["missing"] >= THRESHOLD:
        sig = ("missing_worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            friend.memes["curiosity"] += 1
    return out


def _r_transformation_reveals_clue(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    place = world.get("place")
    if creature.meters["transformed"] >= THRESHOLD:
        sig = ("reveal_clue",)
        if sig not in world.fired:
            world.fired.add(sig)
            place.meters["clue_visible"] += 1
            out.append("__clue__")
    return out


def _r_find_item(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("place")
    item = world.get("item")
    if place.meters["clue_visible"] < THRESHOLD:
        return out
    if world.facts["chosen_method"] != world.facts["required_method"]:
        return out
    sig = ("find_item",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    out.append("__found__")
    return out


def _r_problem_solved(world: World) -> list[str]:
    out: list[str] = []
    event = world.get("event")
    item = world.get("item")
    hero = world.get("hero")
    friend = world.get("friend")
    if item.meters["found"] >= THRESHOLD:
        sig = ("problem_solved",)
        if sig not in world.fired:
            world.fired.add(sig)
            event.meters["ready"] += 1
            hero.memes["relief"] += 1
            hero.memes["pride"] += 1
            friend.memes["relief"] += 1
            out.append("__ready__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="transformation_reveals_clue", tag="physical", apply=_r_transformation_reveals_clue),
    Rule(name="find_item", tag="physical", apply=_r_find_item),
    Rule(name="problem_solved", tag="social", apply=_r_problem_solved),
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


def valid_combo(mystery: Mystery, transformation: Transformation, method: Method) -> bool:
    return (
        mystery.habitat == transformation.habitat
        and mystery.place_label == transformation.place_label
        and method.id == REQUIRED_METHOD[transformation.id]
        and method.habitat == transformation.habitat
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mid, mystery in MYSTERIES.items():
        for tid, transformation in TRANSFORMATIONS.items():
            for meth_id, method in METHODS.items():
                if valid_combo(mystery, transformation, method):
                    combos.append((mid, tid, meth_id))
    return combos


def predict_solution(world: World) -> dict:
    sim = world.copy()
    sim.get("creature").meters["transformed"] += 1
    propagate(sim, narrate=False)
    return {
        "clue_visible": sim.get("place").meters["clue_visible"] >= THRESHOLD,
        "found": sim.get("item").meters["found"] >= THRESHOLD,
    }


def introduce(world: World, mystery: Mystery) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    caretaker = world.get("caretaker")
    event = world.get("event")
    world.say(
        f"In the palace, {hero.id} the {hero.type} and {friend.id} the {friend.type} "
        f"were helping {caretaker.title} get ready for {event.label}."
    )
    world.say(
        f"They worked in {mystery.place_label}, carrying ribbon, straightening petals, "
        f"and trying to make every small thing look just right."
    )


def discover_missing(world: World, mystery: Mystery) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    item = world.get("item")
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(mystery.missing_line.format(hero=hero.id, friend=friend.id))
    world.say(mystery.clue_line)
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s ears drooped a little. {hero.pronoun().capitalize()} did not want "
            f"{mystery.event_name} to begin with {mystery.item_the} still missing."
        )


def inspect_and_wait(world: World, mystery: Mystery, transformation: Transformation) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    pred = predict_solution(world)
    world.facts["predicted_clue"] = pred["clue_visible"]
    world.say(
        f'"This feels like a real mystery," {friend.id} whispered. '
        f'"Let\'s look before we guess."'
    )
    world.say(transformation.wait_line)
    hero.memes["patience"] += 1
    friend.memes["curiosity"] += 1


def transform(world: World, mystery: Mystery, transformation: Transformation) -> None:
    creature = world.get("creature")
    creature.meters["transformed"] += 1
    creature.attrs["form"] = transformation.after_name
    propagate(world, narrate=False)
    world.say(transformation.transform_line)
    world.say(transformation.clue_result)
    world.say(mystery.reveal_line)


def solve(world: World, mystery: Mystery, method: Method) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    world.say(method.action_line.format(hero=hero.id, friend=friend.id))
    propagate(world, narrate=False)
    if world.get("item").meters["found"] >= THRESHOLD:
        world.say(mystery.solve_line.format(hero=hero.id, friend=friend.id))
    else:
        raise StoryError("The chosen method could not solve the mystery in this world.")


def finish(world: World, mystery: Mystery) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    caretaker = world.get("caretaker")
    event = world.get("event")
    world.say(
        f"{caretaker.title} smiled so wide that even {hero.id} stopped looking worried. "
        f"{event.label} was ready after all."
    )
    world.say(mystery.ending_line.format(hero=hero.id, friend=friend.id))


def tell(
    mystery: Mystery,
    transformation: Transformation,
    method: Method,
    *,
    hero_name: str,
    hero_species: str,
    hero_gender: str,
    friend_name: str,
    friend_species: str,
    friend_gender: str,
    caretaker_name: str,
    caretaker_species: str,
    caretaker_gender: str,
) -> World:
    world = World()
    world.facts.update(
        chosen_method=method.id,
        required_method=REQUIRED_METHOD[transformation.id],
        predicted_clue=False,
    )

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_species,
        label=hero_name,
        role="hero",
        attrs={"gender": hero_gender},
        tags={"helper"},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_species,
        label=friend_name,
        role="friend",
        attrs={"gender": friend_gender},
        tags={"helper"},
    ))
    caretaker = world.add(Entity(
        id="caretaker",
        kind="character",
        type=caretaker_species,
        label=caretaker_name,
        role="caretaker",
        attrs={"gender": caretaker_gender},
        tags={"adult"},
    ))
    event = world.add(Entity(
        id="event",
        type="event",
        label=mystery.event_name,
        tags={"celebration"},
    ))
    place = world.add(Entity(
        id="place",
        type="place",
        label=mystery.place_label,
        tags={mystery.habitat},
    ))
    item = world.add(Entity(
        id="item",
        type="object",
        label=mystery.item_label,
        tags=set(mystery.tags),
    ))
    creature = world.add(Entity(
        id="creature",
        kind="character",
        type=transformation.before_name,
        label=f"the little {transformation.before_name}",
        role="transformer",
        attrs={"form": transformation.before_name},
        tags=set(transformation.tags),
    ))

    hero.memes["worry"] = 0.0
    hero.memes["patience"] = 0.0
    hero.memes["pride"] = 0.0
    friend.memes["curiosity"] = 0.0
    friend.memes["relief"] = 0.0
    item.meters["missing"] = 0.0
    item.meters["found"] = 0.0
    place.meters["clue_visible"] = 0.0
    event.meters["ready"] = 0.0
    creature.meters["transformed"] = 0.0

    introduce(world, mystery)
    world.para()
    discover_missing(world, mystery)
    inspect_and_wait(world, mystery, transformation)
    world.para()
    transform(world, mystery, transformation)
    solve(world, mystery, method)
    world.para()
    finish(world, mystery)

    world.facts.update(
        hero=hero,
        friend=friend,
        caretaker=caretaker,
        event=event,
        place=place,
        item=item,
        creature=creature,
        mystery=mystery,
        transformation=transformation,
        method=method,
        solved=event.meters["ready"] >= THRESHOLD,
        transformed=creature.meters["transformed"] >= THRESHOLD,
    )
    return world


MYSTERIES = {
    "moon_clasp": Mystery(
        id="moon_clasp",
        item_label="moon clasp",
        item_the="the moon clasp",
        event_name="Moon Ribbon Parade",
        habitat="garden",
        place_label="the palace rose court",
        missing_line="{hero} reached for the silver moon clasp that should have held the first ribbon closed, but it was gone.",
        clue_line="On the jasmine arch nearby hung one pale cocoon and a curled leaf stitched with a shining thread.",
        reveal_line="Up in the vines, something silver winked where nobody had noticed it before.",
        solve_line="{hero} found the moon clasp caught in the silk near the arch. It must have snagged there while the ribbons were being carried past.",
        ending_line="Soon the ribbons shivered in the evening breeze, and {hero} and {friend} marched beneath them feeling as bright as the moon itself.",
        tags={"palace", "ribbon", "garden"},
    ),
    "bell_charm": Mystery(
        id="bell_charm",
        item_label="bell charm",
        item_the="the bell charm",
        event_name="Pond Welcome Song",
        habitat="pond",
        place_label="the palace lily pond",
        missing_line="{friend} lifted the little cord for the welcome bell, but the bell charm that made the sweetest note was missing.",
        clue_line="At the pond edge, a round patch of water trembled beside a lily cup, and a tadpole's old tail-skin floated like a tiny ribbon.",
        reveal_line="The lily cup tipped, and a small gold bell glimmered in the water folded inside it.",
        solve_line="{friend} hooked the bell charm gently from the lily cup before it could slip deeper into the pond. It had hidden in the folded leaf all along.",
        ending_line="When the song began, the bell answered with a bright clear ting, and {hero} and {friend} laughed to hear the palace wake up.",
        tags={"palace", "bell", "pond"},
    ),
    "silver_seal": Mystery(
        id="silver_seal",
        item_label="silver seal",
        item_the="the silver seal",
        event_name="Winter Guest Feast",
        habitat="hall",
        place_label="the palace velvet hall",
        missing_line="{hero} unrolled the guest list, and everyone saw that the silver seal for the first invitation was missing.",
        clue_line="High on the curtain cord rested a neat silk case, and the velvet below it showed a dust-soft shimmer.",
        reveal_line="When the curtain stirred, a tiny sparkle flashed deep in one pleat.",
        solve_line="{hero} spotted the silver seal tucked into the curtain fold. A flutter and a little dust had hidden it until now.",
        ending_line="That night the candles shone on sealed invitations, and {hero} and {friend} sat very straight, proud to have helped the palace feast begin.",
        tags={"palace", "invitation", "hall"},
    ),
}

TRANSFORMATIONS = {
    "butterfly": Transformation(
        id="butterfly",
        before_name="caterpillar",
        after_name="butterfly",
        habitat="garden",
        place_label="the palace rose court",
        wait_line="So they stood quietly under the arch, watching the pale cocoon sway and listening to bees hum in the roses.",
        transform_line="After a moment, the cocoon opened, and out came a soft new butterfly unfolding damp, careful wings.",
        clue_result="The butterfly's first flutter shook the vine just enough to tremble the leaves and silver thread.",
        tags={"caterpillar", "butterfly", "transformation"},
    ),
    "frog": Transformation(
        id="frog",
        before_name="tadpole",
        after_name="frog",
        habitat="pond",
        place_label="the palace lily pond",
        wait_line="So they crouched by the water and watched the lily leaves rock in little green circles.",
        transform_line="Then a tiny frog, fresh from tadpole days, kicked free and made its very first springing jump.",
        clue_result="Its jump tipped the folded lily cup and sent a ring of water winking across the pond.",
        tags={"tadpole", "frog", "transformation"},
    ),
    "moth": Transformation(
        id="moth",
        before_name="silkworm",
        after_name="moth",
        habitat="hall",
        place_label="the palace velvet hall",
        wait_line="So they lowered their voices and watched the silk case on the curtain cord instead of tugging the velvet at random.",
        transform_line="Soon the case split, and a small moth pushed out, fluttering its powdery wings in the warm hall air.",
        clue_result="Each wingbeat stirred the curtain and lifted a silver dust-glitter from one deep fold.",
        tags={"silkworm", "moth", "transformation"},
    ),
}

METHODS = {
    "ladder": Method(
        id="ladder",
        label="the gardener's ladder",
        habitat="garden",
        action_line="{hero} and {friend} borrowed the gardener's little ladder, held it steady together, and peered into the vine where the glimmer came from.",
        tags={"ladder", "search"},
    ),
    "reed_hook": Method(
        id="reed_hook",
        label="a reed hook",
        habitat="pond",
        action_line="{hero} bent a fallen reed into a tiny hook while {friend} leaned low and kept the lily cup from drifting away.",
        tags={"reed", "search"},
    ),
    "lantern_search": Method(
        id="lantern_search",
        label="a hand lantern",
        habitat="hall",
        action_line="{friend} fetched a hand lantern, and {hero} tipped its warm light across the velvet until the hidden sparkle showed itself.",
        tags={"lantern", "search"},
    ),
}

REQUIRED_METHOD = {
    "butterfly": "ladder",
    "frog": "reed_hook",
    "moth": "lantern_search",
}

HEROES = [
    ("Pip", "rabbit", "boy"),
    ("Nia", "mouse", "girl"),
    ("Moss", "squirrel", "boy"),
    ("Luma", "kitten", "girl"),
    ("Tumble", "mole", "boy"),
    ("Poppy", "rabbit", "girl"),
]

FRIENDS = [
    ("Tavi", "mouse", "boy"),
    ("Mimi", "dormouse", "girl"),
    ("Saffy", "sparrow", "girl"),
    ("Rill", "otter", "boy"),
    ("Bramble", "squirrel", "girl"),
    ("Nip", "hedgehog", "boy"),
]

CARETAKERS = [
    ("Aunt Fern", "tortoise", "girl"),
    ("Master Reed", "badger", "boy"),
    ("Lady Clover", "deer", "girl"),
]


@dataclass
class StoryParams:
    mystery: str
    transformation: str
    method: str
    hero_name: str
    hero_species: str
    hero_gender: str
    friend_name: str
    friend_species: str
    friend_gender: str
    caretaker_name: str
    caretaker_species: str
    caretaker_gender: str
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
    "palace": [
        (
            "What is a palace?",
            "A palace is a very large home where a king, queen, or another ruler might live. It often has big rooms, gardens, and places for special celebrations.",
        )
    ],
    "butterfly": [
        (
            "How does a caterpillar become a butterfly?",
            "A caterpillar makes a case around itself and changes inside it. When it comes out, it is a butterfly with wings.",
        )
    ],
    "frog": [
        (
            "How does a tadpole become a frog?",
            "A tadpole starts with a tail and lives in water. As it grows, it gets legs and changes into a frog.",
        )
    ],
    "moth": [
        (
            "What is a moth?",
            "A moth is a soft-winged insect a bit like a butterfly. Many moths begin life as worms or caterpillars and change inside a silk case.",
        )
    ],
    "ladder": [
        (
            "What is a ladder for?",
            "A ladder helps you reach something that is higher than your hands can go. You still have to use it carefully and hold it steady.",
        )
    ],
    "reed": [
        (
            "What is a reed?",
            "A reed is a long, thin plant that grows near water. Because it is light and bendy, small animals can sometimes use one like a tiny hook.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light so you can see in dim places. Good light helps you notice clues that would stay hidden in the dark.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem with an answer that is hidden at first. You solve it by noticing clues and thinking carefully about what they mean.",
        )
    ],
}
KNOWLEDGE_ORDER = ["palace", "mystery", "butterfly", "frog", "moth", "ladder", "reed", "lantern"]


def generation_prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    transformation = world.facts["transformation"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    method = world.facts["method"]
    return [
        f'Write an animal story for a 3-to-5-year-old set in a palace, where a small missing object creates a gentle mystery that is solved through transformation and careful problem solving.',
        f"Tell a story about {hero.id} the {hero.type} and {friend.id} the {friend.type} solving the mystery of {mystery.item_the} before {mystery.event_name}.",
        f"Write a story where a {transformation.before_name} becomes a {transformation.after_name}, and that transformation helps two animal friends notice a clue and solve the problem with {method.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery"]
    transformation = world.facts["transformation"]
    method = world.facts["method"]
    caretaker = world.facts["caretaker"]

    return [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and {friend.id} the {friend.type} helping {caretaker.title} in the palace. They are trying to get {mystery.event_name} ready.",
        ),
        (
            f"What was the mystery in the story?",
            f"The mystery was that {mystery.item_the} was missing just when the animals needed it. That mattered because the palace celebration was about to begin.",
        ),
        (
            "How did transformation help solve the mystery?",
            f"A {transformation.before_name} changed into a {transformation.after_name}, and that change made the hidden clue easier to see. The movement from the transformation revealed the place where the missing object had been hiding.",
        ),
        (
            "How did the friends solve the problem?",
            f"They did not grab or guess right away. First they watched carefully, and then they used {method.label} because it fit the hiding place and helped them reach the clue.",
        ),
        (
            "How did the story end?",
            f"They found {mystery.item_the}, so {mystery.event_name} could begin. At the end, the palace feels cheerful again because the problem is solved and the mystery makes sense.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    transformation = world.facts["transformation"]
    method = world.facts["method"]
    tags = {"palace", "mystery"}
    if transformation.id == "butterfly":
        tags.add("butterfly")
        tags.add("ladder")
    elif transformation.id == "frog":
        tags.add("frog")
        tags.add("reed")
    elif transformation.id == "moth":
        tags.add("moth")
        tags.add("lantern")
    tags |= set(method.tags)

    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mystery="moon_clasp",
        transformation="butterfly",
        method="ladder",
        hero_name="Poppy",
        hero_species="rabbit",
        hero_gender="girl",
        friend_name="Tavi",
        friend_species="mouse",
        friend_gender="boy",
        caretaker_name="Aunt Fern",
        caretaker_species="tortoise",
        caretaker_gender="girl",
    ),
    StoryParams(
        mystery="bell_charm",
        transformation="frog",
        method="reed_hook",
        hero_name="Moss",
        hero_species="squirrel",
        hero_gender="boy",
        friend_name="Saffy",
        friend_species="sparrow",
        friend_gender="girl",
        caretaker_name="Master Reed",
        caretaker_species="badger",
        caretaker_gender="boy",
    ),
    StoryParams(
        mystery="silver_seal",
        transformation="moth",
        method="lantern_search",
        hero_name="Nia",
        hero_species="mouse",
        hero_gender="girl",
        friend_name="Bramble",
        friend_species="squirrel",
        friend_gender="girl",
        caretaker_name="Lady Clover",
        caretaker_species="deer",
        caretaker_gender="girl",
    ),
    StoryParams(
        mystery="moon_clasp",
        transformation="butterfly",
        method="ladder",
        hero_name="Tumble",
        hero_species="mole",
        hero_gender="boy",
        friend_name="Mimi",
        friend_species="dormouse",
        friend_gender="girl",
        caretaker_name="Master Reed",
        caretaker_species="badger",
        caretaker_gender="boy",
    ),
    StoryParams(
        mystery="bell_charm",
        transformation="frog",
        method="reed_hook",
        hero_name="Luma",
        hero_species="kitten",
        hero_gender="girl",
        friend_name="Nip",
        friend_species="hedgehog",
        friend_gender="boy",
        caretaker_name="Aunt Fern",
        caretaker_species="tortoise",
        caretaker_gender="girl",
    ),
]


def explain_rejection(mystery: Mystery, transformation: Transformation, method: Method) -> str:
    if mystery.habitat != transformation.habitat:
        return (
            f"(No story: {mystery.item_the} went missing in {mystery.place_label}, but a "
            f"{transformation.before_name}-to-{transformation.after_name} transformation belongs in "
            f"a different part of the palace. The clue and the mystery need the same habitat.)"
        )
    if mystery.place_label != transformation.place_label:
        return (
            f"(No story: the missing object is in {mystery.place_label}, but this transformation "
            f"happens in {transformation.place_label}. The clue would not honestly reveal the mystery.)"
        )
    need = REQUIRED_METHOD[transformation.id]
    if method.id != need:
        return (
            f"(No story: {method.label} is not the right way to solve the {transformation.id} mystery. "
            f"Try --method {need}.)"
        )
    return "(No story: this combination does not form a reasonable mystery.)"


ASP_RULES = r"""
same_habitat(M, T) :- mystery(M), transformation(T), mystery_habitat(M, H), transformation_habitat(T, H).
same_place(M, T) :- mystery(M), transformation(T), mystery_place(M, P), transformation_place(T, P).
required_method(T, Me) :- transformation(T), solution_for(T, Me).
valid(M, T, Me) :- mystery(M), transformation(T), method(Me),
                   same_habitat(M, T), same_place(M, T), required_method(T, Me), method_habitat(Me, H), transformation_habitat(T, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("mystery_habitat", mid, mystery.habitat))
        lines.append(asp.fact("mystery_place", mid, mystery.place_label))
    for tid, transformation in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("transformation_habitat", tid, transformation.habitat))
        lines.append(asp.fact("transformation_place", tid, transformation.place_label))
        lines.append(asp.fact("solution_for", tid, REQUIRED_METHOD[tid]))
    for meth_id, method in METHODS.items():
        lines.append(asp.fact("method", meth_id))
        lines.append(asp.fact("method_habitat", meth_id, method.habitat))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 123
        sample = generate(params)
        if not sample.story_qa or not sample.world_qa:
            raise StoryError("Smoke test QA generation failed.")
        print("OK: default resolution + generate() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a palace mystery solved through transformation and careful problem solving."
    )
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--transformation", choices=sorted(TRANSFORMATIONS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid mystery/transformation/method combinations from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def _pick_pair(rng: random.Random, pool: list[tuple[str, str, str]], avoid_name: str = "") -> tuple[str, str, str]:
    options = [x for x in pool if x[0] != avoid_name]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mystery and args.transformation and args.method:
        mystery = MYSTERIES[args.mystery]
        transformation = TRANSFORMATIONS[args.transformation]
        method = METHODS[args.method]
        if not valid_combo(mystery, transformation, method):
            raise StoryError(explain_rejection(mystery, transformation, method))

    combos = [
        combo for combo in valid_combos()
        if (args.mystery is None or combo[0] == args.mystery)
        and (args.transformation is None or combo[1] == args.transformation)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        if args.mystery and args.transformation and args.method:
            raise StoryError(explain_rejection(MYSTERIES[args.mystery], TRANSFORMATIONS[args.transformation], METHODS[args.method]))
        raise StoryError("(No valid combination matches the given options.)")

    mystery_id, transformation_id, method_id = rng.choice(sorted(combos))
    hero_name, hero_species, hero_gender = _pick_pair(rng, HEROES)
    friend_name, friend_species, friend_gender = _pick_pair(rng, FRIENDS, avoid_name=hero_name)
    caretaker_name, caretaker_species, caretaker_gender = _pick_pair(rng, CARETAKERS)

    return StoryParams(
        mystery=mystery_id,
        transformation=transformation_id,
        method=method_id,
        hero_name=hero_name,
        hero_species=hero_species,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_species=friend_species,
        friend_gender=friend_gender,
        caretaker_name=caretaker_name,
        caretaker_species=caretaker_species,
        caretaker_gender=caretaker_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery: {params.mystery})")
    if params.transformation not in TRANSFORMATIONS:
        raise StoryError(f"(Unknown transformation: {params.transformation})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    mystery = MYSTERIES[params.mystery]
    transformation = TRANSFORMATIONS[params.transformation]
    method = METHODS[params.method]
    if not valid_combo(mystery, transformation, method):
        raise StoryError(explain_rejection(mystery, transformation, method))

    world = tell(
        mystery,
        transformation,
        method,
        hero_name=params.hero_name,
        hero_species=params.hero_species,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_species=params.friend_species,
        friend_gender=params.friend_gender,
        caretaker_name=params.caretaker_name,
        caretaker_species=params.caretaker_species,
        caretaker_gender=params.caretaker_gender,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mystery, transformation, method) combos:\n")
        for mystery_id, transformation_id, method_id in combos:
            print(f"  {mystery_id:12} {transformation_id:10} {method_id}")
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
            header = (
                f"### {sample.params.hero_name} & {sample.params.friend_name}: "
                f"{sample.params.mystery} with {sample.params.transformation}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
