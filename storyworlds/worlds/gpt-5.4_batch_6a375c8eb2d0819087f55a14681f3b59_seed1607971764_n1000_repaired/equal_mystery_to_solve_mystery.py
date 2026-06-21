#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/equal_mystery_to_solve_mystery.py
============================================================

A small mystery storyworld about two children who make an equal arrangement of
things, discover that one side is no longer equal, and solve the tiny mystery by
reading clues from the world around them.

The domain is deliberately narrow and state-driven:

- Two children arrange objects into two equal groups.
- Something in the environment changes the count.
- They notice the groups are no longer equal.
- They investigate a clue, infer the likely culprit, search in the sensible way,
  and restore the equal arrangement.

Run it
------
    python storyworlds/worlds/gpt-5.4/equal_mystery_to_solve_mystery.py
    python storyworlds/worlds/gpt-5.4/equal_mystery_to_solve_mystery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/equal_mystery_to_solve_mystery.py --all
    python storyworlds/worlds/gpt-5.4/equal_mystery_to_solve_mystery.py --qa
    python storyworlds/worlds/gpt-5.4/equal_mystery_to_solve_mystery.py --json
    python storyworlds/worlds/gpt-5.4/equal_mystery_to_solve_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/equal_mystery_to_solve_mystery.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "teacher", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
            "grandmother": "grandma",
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
    scene: str
    affordances: set[str] = field(default_factory=set)
    outdoor: bool = False
    helper_type: str = "mother"
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
class ItemCfg:
    id: str
    label: str
    phrase: str
    plural: str
    pair_word: str
    adjective: str
    edible: bool = False
    light: bool = False
    shiny: bool = False
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
class Culprit:
    id: str
    label: str
    kind: str
    needs: set[str] = field(default_factory=set)
    clue: str = ""
    clue_detail: str = ""
    hiding_place: str = ""
    motive: str = ""
    recover_text: str = ""
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
    action: str
    works_for: set[str] = field(default_factory=set)
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


def _r_notice_unequal(world: World) -> list[str]:
    left = world.get("left_group")
    right = world.get("right_group")
    if left.meters["count"] == right.meters["count"]:
        return []
    sig = ("unequal", int(left.meters["count"]), int(right.meters["count"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in (world.get("kid1"), world.get("kid2")):
        kid.memes["worry"] += 1
        kid.memes["curiosity"] += 1
    world.facts["unequal_now"] = True
    return ["__unequal__"]


def _r_restore_equal(world: World) -> list[str]:
    left = world.get("left_group")
    right = world.get("right_group")
    if left.meters["count"] < THRESHOLD or right.meters["count"] < THRESHOLD:
        return []
    if left.meters["count"] != right.meters["count"]:
        return []
    if world.get("missing").meters["found"] < THRESHOLD:
        return []
    sig = ("equal_restored", int(left.meters["count"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in (world.get("kid1"), world.get("kid2")):
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
        kid.memes["worry"] = 0.0
    world.facts["equal_restored"] = True
    return ["__restored__"]


CAUSAL_RULES = [
    Rule(name="notice_unequal", tag="physical", apply=_r_notice_unequal),
    Rule(name="restore_equal", tag="social", apply=_r_restore_equal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden",
        scene="Behind the house, the garden had a stone path, a low bench, and flowerpots with warm dirt.",
        affordances={"squirrel", "breeze"},
        outdoor=True,
        helper_type="mother",
        tags={"garden"},
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        scene="The front porch held a striped mat, a little bell by the door, and a railing bright in the sun.",
        affordances={"crow", "breeze"},
        outdoor=True,
        helper_type="grandmother",
        tags={"porch"},
    ),
    "classroom": Place(
        id="classroom",
        label="the classroom",
        scene="The classroom was quiet after art time, with a rug, a toy chest, and shelves full of paper and glue.",
        affordances={"mouse"},
        outdoor=False,
        helper_type="teacher",
        tags={"classroom"},
    ),
}

ITEMS = {
    "berries": ItemCfg(
        id="berries",
        label="blueberries",
        phrase="round blueberries",
        plural="blueberries",
        pair_word="rows",
        adjective="round",
        edible=True,
        light=False,
        shiny=False,
        tags={"berries", "counting"},
    ),
    "stars": ItemCfg(
        id="stars",
        label="paper stars",
        phrase="paper stars cut from yellow paper",
        plural="stars",
        pair_word="lines",
        adjective="light",
        edible=False,
        light=True,
        shiny=False,
        tags={"paper", "counting"},
    ),
    "buttons": ItemCfg(
        id="buttons",
        label="silver buttons",
        phrase="silver buttons from the craft jar",
        plural="buttons",
        pair_word="circles",
        adjective="shiny",
        edible=False,
        light=False,
        shiny=True,
        tags={"buttons", "counting"},
    ),
}

CULPRITS = {
    "squirrel": Culprit(
        id="squirrel",
        label="a squirrel",
        kind="animal",
        needs={"edible", "outdoor"},
        clue="tiny tooth marks",
        clue_detail="one berry had tiny tooth marks, and a purple dot of juice led toward a flowerpot",
        hiding_place="behind a flowerpot",
        motive="it wanted a snack",
        recover_text="They found the missing berries tucked behind a flowerpot where the squirrel had stopped to nibble.",
        tags={"squirrel", "animal"},
    ),
    "breeze": Culprit(
        id="breeze",
        label="the breeze",
        kind="weather",
        needs={"light", "outdoor"},
        clue="fluttering paper",
        clue_detail="a corner of yellow paper fluttered under the bench while the rest of the stars stayed still",
        hiding_place="under the bench",
        motive="it pushed the light paper along the porch or path",
        recover_text="They peered under the bench and found the missing star pressed against the leg by the soft breeze.",
        tags={"wind", "weather"},
    ),
    "crow": Culprit(
        id="crow",
        label="a crow",
        kind="animal",
        needs={"shiny", "outdoor"},
        clue="a black feather",
        clue_detail="a black feather lay by the railing, and one button was gone from the neat circle",
        hiding_place="in a nest by the porch roof",
        motive="it liked shiny things",
        recover_text="When they looked up, they spotted the missing button tucked in a small nest by the porch roof.",
        tags={"crow", "animal"},
    ),
    "mouse": Culprit(
        id="mouse",
        label="a mouse",
        kind="animal",
        needs={"small", "indoor"},
        clue="a faint squeak",
        clue_detail="from the toy chest came a faint squeak, and a little scrap of paper wiggled at the edge",
        hiding_place="inside the toy chest",
        motive="it had dragged the small thing to a cozy hiding place",
        recover_text="They opened the toy chest very gently and found the missing piece beside a tiny nest of paper scraps.",
        tags={"mouse", "animal"},
    ),
}

METHODS = {
    "follow_trail": Method(
        id="follow_trail",
        label="follow the little trail",
        action="knelt down and followed the little trail instead of guessing",
        works_for={"squirrel", "breeze"},
        tags={"clue", "trail"},
    ),
    "look_up": Method(
        id="look_up",
        label="look up high",
        action="stepped back and looked up instead of only staring at the floor",
        works_for={"crow"},
        tags={"clue", "up"},
    ),
    "listen_close": Method(
        id="listen_close",
        label="listen very still",
        action="went quiet and listened very still before they touched anything",
        works_for={"mouse"},
        tags={"clue", "sound"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Ruby", "Ivy"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Owen"]
TRAITS = ["careful", "patient", "bright", "curious", "steady", "thoughtful"]


def culprit_fits(place: Place, item: ItemCfg, culprit: Culprit) -> bool:
    if culprit.id not in place.affordances:
        return False
    if "outdoor" in culprit.needs and not place.outdoor:
        return False
    if "indoor" in culprit.needs and place.outdoor:
        return False
    if "edible" in culprit.needs and not item.edible:
        return False
    if "light" in culprit.needs and not item.light:
        return False
    if "shiny" in culprit.needs and not item.shiny:
        return False
    if "small" in culprit.needs and item.id not in {"stars", "buttons"}:
        return False
    return True


def sensible_methods_for(culprit_id: str) -> list[str]:
    return sorted(m.id for m in METHODS.values() if culprit_id in m.works_for)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for culprit_id, culprit in CULPRITS.items():
                if culprit_fits(place, item, culprit):
                    combos.append((place_id, item_id, culprit_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    item: str
    culprit: str
    method: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    helper: str
    trait1: str
    trait2: str
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def setup_equal(world: World, kid1: Entity, kid2: Entity, item: ItemCfg) -> None:
    for kid in (kid1, kid2):
        kid.memes["joy"] += 1
    left = world.get("left_group")
    right = world.get("right_group")
    left.meters["count"] = 4
    right.meters["count"] = 4
    world.say(
        f"{kid1.id} and {kid2.id} were making a neat little puzzle in {world.place.label}. "
        f"They laid out {item.phrase} in two equal {item.pair_word}, four on one side and four on the other."
    )
    world.say(world.place.scene)
    world.say(
        f'"Now they match exactly," {kid1.id} said. {kid2.id} nodded, pleased by how tidy and equal the pattern looked.'
    )


def vanish_one(world: World, culprit: Culprit) -> None:
    left = world.get("left_group")
    missing = world.get("missing")
    left.meters["count"] -= 1
    missing.meters["count"] = 1
    missing.attrs["with_culprit"] = culprit.id
    propagate(world, narrate=False)


def notice_problem(world: World, kid1: Entity, kid2: Entity, item: ItemCfg) -> None:
    left = world.get("left_group")
    right = world.get("right_group")
    world.say(
        f"Then {kid2.id} blinked and counted again. One side held {int(left.meters['count'])}, but the other still held {int(right.meters['count'])}."
    )
    world.say(
        f'"That is not equal anymore," {kid2.id} whispered. The pretty little mystery began right there.'
    )


def inspect_clue(world: World, kid1: Entity, kid2: Entity, culprit: Culprit, helper: Entity) -> None:
    for kid in (kid1, kid2):
        kid.memes["focus"] += 1
    world.facts["clue_text"] = culprit.clue_detail
    world.say(
        f"{helper.id} did not solve it for them. {helper.pronoun().capitalize()} just smiled and said, "
        f'"Good detectives look for the smallest clue first."'
    )
    world.say(
        f"So {kid1.id} and {kid2.id} looked closely. {culprit.clue_detail}."
    )


def predict_culprit(world: World, culprit: Culprit) -> str:
    sim = world.copy()
    sim.facts["predicted_culprit"] = culprit.id
    return culprit.id


def infer_and_search(world: World, kid1: Entity, kid2: Entity, culprit: Culprit, method: Method) -> None:
    predicted = predict_culprit(world, culprit)
    world.facts["predicted_culprit"] = predicted
    kid1.memes["curiosity"] += 1
    kid2.memes["curiosity"] += 1
    world.say(
        f'"Maybe it was {culprit.label}," {kid1.id} said. {kid2.id} thought about the clue and agreed.'
    )
    world.say(
        f"They {method.action}. That choice fit the clue, so the mystery began to loosen."
    )


def recover(world: World, culprit: Culprit) -> None:
    left = world.get("left_group")
    right = world.get("right_group")
    missing = world.get("missing")
    missing.meters["found"] = 1
    missing.meters["count"] = 0
    left.meters["count"] += 1
    world.facts["found_at"] = culprit.hiding_place
    world.say(culprit.recover_text)
    propagate(world, narrate=False)
    world.say(
        f"Soon both sides matched again: {int(left.meters['count'])} and {int(right.meters['count'])}, equal once more."
    )


def ending(world: World, kid1: Entity, kid2: Entity, helper: Entity, culprit: Culprit, item: ItemCfg) -> None:
    world.say(
        f'{helper.id} laughed softly. "You solved it by looking, listening, and thinking."'
    )
    world.say(
        f"{kid1.id} and {kid2.id} set the {item.plural} back into their neat pattern and admired it for a long moment."
    )
    world.say(
        f"The mystery was small, but their detective work felt grand, and the equal shape on the ground proved they had put the world right again."
    )
    world.facts["motive"] = culprit.motive


def tell(
    place: Place,
    item: ItemCfg,
    culprit: Culprit,
    method: Method,
    kid1_name: str,
    kid1_gender: str,
    kid2_name: str,
    kid2_gender: str,
    helper_name: str,
    trait1: str,
    trait2: str,
) -> World:
    world = World(place)
    kid1 = world.add(Entity(id=kid1_name, kind="character", type=kid1_gender, role="detective",
                            attrs={"trait": trait1}))
    kid2 = world.add(Entity(id=kid2_name, kind="character", type=kid2_gender, role="detective",
                            attrs={"trait": trait2}))
    helper = world.add(Entity(id=helper_name, kind="character", type=place.helper_type, role="helper"))
    world.add(Entity(id="left_group", type="group", label="left side"))
    world.add(Entity(id="right_group", type="group", label="right side"))
    world.add(Entity(id="missing", type="missing", label="missing thing"))
    world.facts.update(
        place=place,
        item=item,
        culprit=culprit,
        method=method,
        kid1=kid1,
        kid2=kid2,
        helper=helper,
        clue_text="",
        predicted_culprit="",
        found_at="",
        motive="",
        unequal_now=False,
        equal_restored=False,
    )

    setup_equal(world, kid1, kid2, item)
    world.para()
    vanish_one(world, culprit)
    notice_problem(world, kid1, kid2, item)
    inspect_clue(world, kid1, kid2, culprit, helper)
    world.para()
    infer_and_search(world, kid1, kid2, culprit, method)
    recover(world, culprit)
    world.para()
    ending(world, kid1, kid2, helper, culprit, item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    place = f["place"]
    culprit = f["culprit"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the word "equal" and takes place in {place.label}.',
        f"Tell a tiny detective story where two children notice that their equal pattern of {item.plural} is no longer equal, then solve the mystery by following a clue.",
        f"Write a child-friendly mystery about missing {item.plural}, a clue that points to {culprit.label}, and an ending where the pattern is equal again.",
    ]


KNOWLEDGE = {
    "counting": [
        (
            "What does equal mean when you are counting things?",
            "Equal means both groups have the same number. If one side has more or less, they are not equal."
        )
    ],
    "squirrel": [
        (
            "Why might a squirrel take a berry?",
            "Squirrels look for food, and berries are a snack. If food is left within reach, a squirrel may carry it off."
        )
    ],
    "wind": [
        (
            "How can a breeze move paper?",
            "Paper is light, so even a soft breeze can slide or lift it. That is why paper can drift under benches or along the ground."
        )
    ],
    "crow": [
        (
            "Why do crows sometimes pick up shiny things?",
            "Crows notice bright, shiny objects. Sometimes they carry them away because the objects catch their eye."
        )
    ],
    "mouse": [
        (
            "Why do mice hide in quiet places?",
            "Mice like small, cozy spaces where they feel safe. That is why they often hide in boxes, corners, or chests."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Detectives look for clues so they do not have to guess."
        )
    ],
}
KNOWLEDGE_ORDER = ["counting", "clue", "squirrel", "wind", "crow", "mouse"]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid1 = f["kid1"]
    kid2 = f["kid2"]
    helper = f["helper"]
    item = f["item"]
    culprit = f["culprit"]
    method = f["method"]
    found_at = f["found_at"]
    clue_text = f["clue_text"]
    qa = [
        (
            "What was the mystery in the story?",
            f"The mystery was that one {item.label} was missing, so the two groups were no longer equal. {kid1.id} and {kid2.id} had to find out what changed and where the missing one had gone."
        ),
        (
            "How did the children know something was wrong?",
            f"They counted both sides and saw that one side had fewer than the other. The pattern itself showed the problem because equal groups should match exactly."
        ),
        (
            "What clue helped them?",
            f"The clue was {clue_text}. That small sign gave them a direction, so they could investigate instead of making a wild guess."
        ),
        (
            f"Why did {kid1.id} and {kid2.id} try to {method.label}?",
            f"They chose that method because it fit the clue they had found. Careful detective work helped them look in the right place instead of the wrong one."
        ),
        (
            "Who or what caused the problem?",
            f"It was {culprit.label}. The clue matched that culprit, and the children found the missing {item.label} at {found_at}."
        ),
        (
            "How did the story end?",
            f"They put the missing {item.label} back and made both sides equal again. {helper.id} praised them for solving the mystery by thinking carefully."
        ),
    ]
    return qa


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"counting", "clue"}
    culprit = world.facts["culprit"]
    if culprit.id == "squirrel":
        tags.add("squirrel")
    elif culprit.id == "breeze":
        tags.add("wind")
    elif culprit.id == "crow":
        tags.add("crow")
    elif culprit.id == "mouse":
        tags.add("mouse")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: culprit={world.facts.get('culprit').id} method={world.facts.get('method').id} found_at={world.facts.get('found_at')}")
    return "\n".join(lines)


def explain_combo_rejection(place: Place, item: ItemCfg, culprit: Culprit) -> str:
    if culprit.id not in place.affordances:
        return f"(No story: {culprit.label} does not fit {place.label} in this world.)"
    if "outdoor" in culprit.needs and not place.outdoor:
        return f"(No story: {culprit.label} needs an outdoor place, but {place.label} is indoors.)"
    if "indoor" in culprit.needs and place.outdoor:
        return f"(No story: {culprit.label} needs an indoor place, but {place.label} is outdoors.)"
    if "edible" in culprit.needs and not item.edible:
        return f"(No story: {culprit.label} would not sensibly take {item.label}; it needs something edible.)"
    if "light" in culprit.needs and not item.light:
        return f"(No story: {culprit.label} only makes sense with something light enough to blow away.)"
    if "shiny" in culprit.needs and not item.shiny:
        return f"(No story: {culprit.label} is only a good fit for something shiny.)"
    if "small" in culprit.needs and item.id not in {'stars', 'buttons'}:
        return f"(No story: {culprit.label} only makes sense with a small object in this world.)"
    return "(No story: that place, item, and culprit do not make a reasonable mystery.)"


def explain_method_rejection(culprit: Culprit, method: Method) -> str:
    good = ", ".join(sensible_methods_for(culprit.id))
    return (
        f"(No story: method '{method.id}' does not fit the clue for {culprit.label}. "
        f"Try one of: {good}.)"
    )


CURATED = [
    StoryParams(
        place="garden",
        item="berries",
        culprit="squirrel",
        method="follow_trail",
        kid1="Lily",
        kid1_gender="girl",
        kid2="Ben",
        kid2_gender="boy",
        helper="Mom",
        trait1="careful",
        trait2="curious",
        seed=1,
    ),
    StoryParams(
        place="garden",
        item="stars",
        culprit="breeze",
        method="follow_trail",
        kid1="Nora",
        kid1_gender="girl",
        kid2="Tom",
        kid2_gender="boy",
        helper="Mom",
        trait1="patient",
        trait2="bright",
        seed=2,
    ),
    StoryParams(
        place="porch",
        item="buttons",
        culprit="crow",
        method="look_up",
        kid1="Max",
        kid1_gender="boy",
        kid2="Ava",
        kid2_gender="girl",
        helper="Grandma",
        trait1="steady",
        trait2="thoughtful",
        seed=3,
    ),
    StoryParams(
        place="classroom",
        item="stars",
        culprit="mouse",
        method="listen_close",
        kid1="Ruby",
        kid1_gender="girl",
        kid2="Finn",
        kid2_gender="boy",
        helper="Teacher May",
        trait1="careful",
        trait2="patient",
        seed=4,
    ),
]


ASP_RULES = r"""
fits_item(C, I) :- culprit(C), item(I), needs(C, edible), edible(I).
fits_item(C, I) :- culprit(C), item(I), needs(C, light), light(I).
fits_item(C, I) :- culprit(C), item(I), needs(C, shiny), shiny(I).
fits_item(C, I) :- culprit(C), item(I), needs(C, small), small(I).

fits_place(C, P) :- culprit(C), place(P), needs(C, outdoor), outdoor(P).
fits_place(C, P) :- culprit(C), place(P), needs(C, indoor), indoor(P).
fits_place(C, P) :- culprit(C), place(P), not needs(C, outdoor), not needs(C, indoor).

valid(P, I, C) :- place(P), item(I), culprit(C), affords(P, C),
                  fits_place(C, P),
                  not needs(C, edible).
valid(P, I, C) :- place(P), item(I), culprit(C), affords(P, C),
                  fits_place(C, P), needs(C, edible), edible(I).
valid(P, I, C) :- place(P), item(I), culprit(C), affords(P, C),
                  fits_place(C, P), needs(C, light), light(I).
valid(P, I, C) :- place(P), item(I), culprit(C), affords(P, C),
                  fits_place(C, P), needs(C, shiny), shiny(I).
valid(P, I, C) :- place(P), item(I), culprit(C), affords(P, C),
                  fits_place(C, P), needs(C, small), small(I).

sensible_method(C, M) :- works_for(M, C).

solved :- chosen_culprit(C), chosen_method(M), sensible_method(C, M).
outcome(restored) :- solved.
outcome(?) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.outdoor:
            lines.append(asp.fact("outdoor", pid))
        else:
            lines.append(asp.fact("indoor", pid))
        for c in sorted(p.affordances):
            lines.append(asp.fact("affords", pid, c))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.edible:
            lines.append(asp.fact("edible", iid))
        if item.light:
            lines.append(asp.fact("light", iid))
        if item.shiny:
            lines.append(asp.fact("shiny", iid))
        if iid in {"stars", "buttons"}:
            lines.append(asp.fact("small", iid))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        for need in sorted(culprit.needs):
            lines.append(asp.fact("needs", cid, need))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        for cid in sorted(method.works_for):
            lines.append(asp.fact("works_for", mid, cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods(culprit_id: str) -> list[str]:
    import asp

    extra = asp.fact("chosen_culprit", culprit_id)
    model = asp.one_model(asp_program(extra, "#show sensible_method/2."))
    return sorted(m for c, m in asp.atoms(model, "sensible_method") if c == culprit_id)


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "restored" if params.method in sensible_methods_for(params.culprit) else "?"


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

    for cid in sorted(CULPRITS):
        c_methods = set(asp_sensible_methods(cid))
        p_methods = set(sensible_methods_for(cid))
        if c_methods == p_methods:
            print(f"OK: sensible methods for {cid} match ({sorted(c_methods)}).")
        else:
            rc = 1
            print(f"MISMATCH in methods for {cid}: clingo={sorted(c_methods)} python={sorted(p_methods)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a tiny mystery about something missing from an equal pattern."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.culprit:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        culprit = CULPRITS[args.culprit]
        if not culprit_fits(place, item, culprit):
            raise StoryError(explain_combo_rejection(place, item, culprit))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, culprit_id = rng.choice(sorted(combos))
    if args.method is not None:
        if args.method not in METHODS:
            raise StoryError(f"(No story: unknown method '{args.method}'.)")
        method = METHODS[args.method]
        culprit = CULPRITS[culprit_id]
        if culprit_id not in method.works_for:
            raise StoryError(explain_method_rejection(culprit, method))
        method_id = args.method
    else:
        method_id = rng.choice(sensible_methods_for(culprit_id))

    kid1, kid1_gender = _pick_kid(rng)
    kid2, kid2_gender = _pick_kid(rng, avoid=kid1)
    helper = args.helper or (
        "Mom" if PLACES[place_id].helper_type == "mother"
        else "Grandma" if PLACES[place_id].helper_type == "grandmother"
        else "Teacher May"
    )
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice([t for t in TRAITS if t != trait1])

    return StoryParams(
        place=place_id,
        item=item_id,
        culprit=culprit_id,
        method=method_id,
        kid1=kid1,
        kid1_gender=kid1_gender,
        kid2=kid2,
        kid2_gender=kid2_gender,
        helper=helper,
        trait1=trait1,
        trait2=trait2,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(No story: unknown culprit '{params.culprit}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(No story: unknown method '{params.method}'.)")

    place = PLACES[params.place]
    item = ITEMS[params.item]
    culprit = CULPRITS[params.culprit]
    method = METHODS[params.method]

    if not culprit_fits(place, item, culprit):
        raise StoryError(explain_combo_rejection(place, item, culprit))
    if params.culprit not in method.works_for:
        raise StoryError(explain_method_rejection(culprit, method))

    world = tell(
        place=place,
        item=item,
        culprit=culprit,
        method=method,
        kid1_name=params.kid1,
        kid1_gender=params.kid1_gender,
        kid2_name=params.kid2,
        kid2_gender=params.kid2_gender,
        helper_name=params.helper,
        trait1=params.trait1,
        trait2=params.trait2,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_method/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, culprit) combos:\n")
        for place, item, culprit in combos:
            methods = ", ".join(asp_sensible_methods(culprit))
            print(f"  {place:10} {item:8} {culprit:8}  [{methods}]")
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
            header = f"### {p.place}: {p.item} / {p.culprit} / {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
