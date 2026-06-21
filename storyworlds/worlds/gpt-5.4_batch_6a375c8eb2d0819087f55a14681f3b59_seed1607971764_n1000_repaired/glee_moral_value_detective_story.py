#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/glee_moral_value_detective_story.py
==============================================================

A small storyworld about a child detective solving a gentle mystery in a shared
play place. The missing object was borrowed without asking; a clue points the
way; the detective chooses a kind approach; the borrower tells the truth, gives
the object back, and learns that honesty and asking first matter.

Run it
------
    python storyworlds/worlds/gpt-5.4/glee_moral_value_detective_story.py
    python storyworlds/worlds/gpt-5.4/glee_moral_value_detective_story.py --place classroom --item ruler --clue block_dust
    python storyworlds/worlds/gpt-5.4/glee_moral_value_detective_story.py --approach accuse_loudly
    python storyworlds/worlds/gpt-5.4/glee_moral_value_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/glee_moral_value_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/glee_moral_value_detective_story.py --trace --seed 77
    python storyworlds/worlds/gpt-5.4/glee_moral_value_detective_story.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    corner: str
    helper_type: str
    affords: set[str] = field(default_factory=set)
    clue_sites: dict[str, str] = field(default_factory=dict)
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
class MissingItem:
    id: str
    label: str
    phrase: str
    owner_group: str
    use_text: str
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
class Clue:
    id: str
    label: str
    marks: str
    trail_text: str
    reveal_place: str
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
class Approach:
    id: str
    sense: int
    gentle: bool
    text: str
    confession_style: str
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


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    detective = world.get("detective")
    borrower = world.get("borrower")
    out: list[str] = []
    if item.meters["missing"] >= THRESHOLD:
        sig = ("missing_worry", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["curiosity"] += 1
            borrower.memes["worry"] += 1
            out.append("__missing__")
    return out


def _r_clue_points(world: World) -> list[str]:
    detective = world.get("detective")
    item = world.get("item")
    clue = world.get("clue")
    out: list[str] = []
    if item.meters["missing"] >= THRESHOLD and clue.meters["noticed"] >= THRESHOLD:
        sig = ("clue_points", clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.meters["trail"] += 1
            detective.memes["confidence"] += 1
            out.append("__trail__")
    return out


def _r_kind_confession(world: World) -> list[str]:
    detective = world.get("detective")
    borrower = world.get("borrower")
    item = world.get("item")
    approach = world.get("approach")
    out: list[str] = []
    if item.meters["missing"] >= THRESHOLD and detective.meters["trail"] >= THRESHOLD and approach.meters["used"] >= THRESHOLD:
        sig = ("kind_confession",)
        if sig not in world.fired and approach.attrs.get("gentle"):
            world.fired.add(sig)
            borrower.memes["honesty"] += 1
            borrower.memes["shame"] += 1
            item.meters["returned"] += 1
            item.meters["missing"] = 0.0
            detective.memes["glee"] += 1
            detective.memes["relief"] += 1
            borrower.memes["relief"] += 1
            out.append("__confession__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="social", apply=_r_missing_worry),
    Rule(name="clue_points", tag="physical", apply=_r_clue_points),
    Rule(name="kind_confession", tag="moral", apply=_r_kind_confession),
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
    "classroom": Place(
        id="classroom",
        label="the classroom",
        corner="the block corner",
        helper_type="teacher",
        affords={"storybook", "ruler"},
        clue_sites={"bookmark": "the reading rug", "block_dust": "the block corner"},
        tags={"school"},
    ),
    "library": Place(
        id="library",
        label="the library room",
        corner="the reading rug",
        helper_type="teacher",
        affords={"storybook", "stamp"},
        clue_sites={"bookmark": "the reading rug", "ink_dot": "the little checkout desk"},
        tags={"library"},
    ),
    "art_room": Place(
        id="art_room",
        label="the art room",
        corner="the paint table",
        helper_type="teacher",
        affords={"glue_stick", "stamp"},
        clue_sites={"paper_bits": "the collage table", "ink_dot": "the little drying shelf"},
        tags={"art"},
    ),
}

ITEMS = {
    "storybook": MissingItem(
        id="storybook",
        label="storybook",
        phrase="the star-covered storybook",
        owner_group="the class",
        use_text="for quiet reading",
        tags={"book", "sharing"},
    ),
    "ruler": MissingItem(
        id="ruler",
        label="ruler",
        phrase="the long blue ruler",
        owner_group="the class",
        use_text="for making straight roads and careful lines",
        tags={"measuring", "sharing"},
    ),
    "glue_stick": MissingItem(
        id="glue_stick",
        label="glue stick",
        phrase="the fat purple glue stick",
        owner_group="the art shelf",
        use_text="for sticking paper pieces together",
        tags={"glue", "sharing"},
    ),
    "stamp": MissingItem(
        id="stamp",
        label="stamp pad",
        phrase="the shiny animal stamp pad",
        owner_group="the room",
        use_text="for pressing animal shapes onto paper",
        tags={"ink", "sharing"},
    ),
}

CLUES = {
    "bookmark": Clue(
        id="bookmark",
        label="bookmark",
        marks="a striped bookmark peeking out from under a cushion",
        trail_text="The bookmark did not belong near the floor, so it looked like a tiny arrow.",
        reveal_place="the reading rug",
        tags={"clue", "book"},
    ),
    "block_dust": Clue(
        id="block_dust",
        label="block dust",
        marks="a neat line of pale wooden dust beside a tower",
        trail_text="The dust matched the edges of the building blocks, as if the missing thing had been used there.",
        reveal_place="the block corner",
        tags={"clue", "blocks"},
    ),
    "paper_bits": Clue(
        id="paper_bits",
        label="paper bits",
        marks="curly paper bits stuck to the floor",
        trail_text="The little scraps glittered in the light and pointed toward a half-made collage.",
        reveal_place="the collage table",
        tags={"clue", "paper"},
    ),
    "ink_dot": Clue(
        id="ink_dot",
        label="ink dot",
        marks="a row of tiny blue ink dots",
        trail_text="The dots looked like careful stepping-stones leading to a page that was still wet.",
        reveal_place="the little checkout desk",
        tags={"clue", "ink"},
    ),
}

APPROACHES = {
    "ask_kindly": Approach(
        id="ask_kindly",
        sense=3,
        gentle=True,
        text="used a calm detective voice and asked what had happened before blaming anyone",
        confession_style="looked down, told the truth, and held the item out with both hands",
        qa_text="asked kindly and gave the borrower room to tell the truth",
        tags={"kindness", "honesty"},
    ),
    "whisper_privately": Approach(
        id="whisper_privately",
        sense=3,
        gentle=True,
        text="walked over quietly and whispered the question so no one else had to feel embarrassed",
        confession_style="took a brave breath, whispered the truth back, and returned the item right away",
        qa_text="asked in private so the borrower could be honest without feeling shamed",
        tags={"kindness", "honesty"},
    ),
    "accuse_loudly": Approach(
        id="accuse_loudly",
        sense=1,
        gentle=False,
        text="pointed across the room and shouted the guess before checking the facts",
        confession_style="went red and stiffened",
        qa_text="shouted an accusation instead of asking kindly",
        tags={"unkind"},
    ),
}


def item_fits_place(place: Place, item: MissingItem) -> bool:
    return item.id in place.affords


def clue_fits(place: Place, item: MissingItem, clue: Clue) -> bool:
    pairs = {
        ("classroom", "storybook"): {"bookmark"},
        ("classroom", "ruler"): {"block_dust"},
        ("library", "storybook"): {"bookmark"},
        ("library", "stamp"): {"ink_dot"},
        ("art_room", "glue_stick"): {"paper_bits"},
        ("art_room", "stamp"): {"ink_dot", "paper_bits"},
    }
    return clue.id in pairs.get((place.id, item.id), set())


def sensible_approaches() -> list[Approach]:
    return [a for a in APPROACHES.values() if a.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            if not item_fits_place(place, item):
                continue
            for clue_id, clue in CLUES.items():
                if clue_fits(place, item, clue):
                    combos.append((place_id, item_id, clue_id))
    return combos


@dataclass
class StoryParams:
    place: str
    item: str
    clue: str
    approach: str
    detective_name: str
    detective_gender: str
    borrower_name: str
    borrower_gender: str
    helper_name: str = "Ms. Fern"
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


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli"]


def introduce(world: World, detective: Entity, borrower: Entity, helper: Entity, item: MissingItem) -> None:
    world.say(
        f"{detective.id} liked mysteries so much that {detective.pronoun()} called "
        f"{detective.pronoun('possessive')} pocket notebook the Detective Book."
    )
    world.say(
        f"That morning in {world.place.label}, {helper.id} set out {item.phrase} for everyone to share."
    )
    world.say(
        f"{borrower.id} smiled at it too, because it was just right {item.use_text}."
    )


def discovery(world: World, detective: Entity, helper: Entity, item: MissingItem) -> None:
    thing = world.get("item")
    thing.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when circle time was about to begin, {helper.id} blinked at the shelf. "
        f'"Where did {item.phrase} go?" {helper.pronoun()} asked.'
    )
    world.say(
        f"{detective.id}'s eyes grew bright. A mystery had arrived before snack."
    )


def clue_scene(world: World, detective: Entity, clue: Clue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} crouched low and spotted {clue.marks}. {clue.trail_text}"
    )
    world.say(
        f'Softly, {detective.pronoun()} whispered, "Clues first, guesses later."'
    )


def track_scene(world: World, detective: Entity, borrower: Entity, item: MissingItem, clue: Clue) -> None:
    reveal = world.place.clue_sites.get(clue.id, clue.reveal_place)
    world.say(
        f"The tiny trail led {detective.id} to {reveal}, where {borrower.id} was using "
        f"{item.phrase} all alone."
    )
    world.say(
        f"{borrower.id} looked up quickly and hugged the missing {item.label} close."
    )


def approach_scene(world: World, detective: Entity, borrower: Entity, approach: Approach) -> None:
    approach_ent = world.get("approach")
    approach_ent.meters["used"] += 1
    approach_ent.attrs["gentle"] = approach.gentle
    propagate(world, narrate=False)
    world.say(
        f"{detective.id} {approach.text}."
    )
    if borrower.memes["honesty"] >= THRESHOLD:
        world.say(
            f"{borrower.id} {approach.confession_style}. "
            f'"I borrowed it because I wanted one more turn," {borrower.pronoun()} said. '
            f'"I should have asked first."'
        )


def repair_scene(world: World, detective: Entity, borrower: Entity, helper: Entity, item: MissingItem) -> None:
    world.say(
        f"{borrower.id} gave {item.phrase} back to {helper.id}, then turned to {detective.id}. "
        f'"I was worried you would be mad," {borrower.pronoun()} admitted.'
    )
    world.say(
        f'"I just wanted the true answer," {detective.id} said. '
        f'"Next time, ask, and we can share it fairly."'
    )


def ending_scene(world: World, detective: Entity, borrower: Entity, helper: Entity, item: MissingItem) -> None:
    world.say(
        f"{helper.id} smiled and thanked them both for choosing honesty over hiding."
    )
    world.say(
        f"Soon {item.phrase} was back on the table where everyone could see it."
    )
    world.say(
        f"{detective.id} felt a burst of glee, not because someone had been caught, "
        f"but because the room felt right again."
    )
    world.say(
        f"When choice time began, {borrower.id} asked for a turn properly, and {detective.id} nodded. "
        f"The mystery ended with the truth in the open and two kinder children beside the shelf."
    )


def tell(
    place: Place,
    item: MissingItem,
    clue: Clue,
    approach: Approach,
    detective_name: str,
    detective_gender: str,
    borrower_name: str,
    borrower_gender: str,
    helper_name: str,
) -> World:
    world = World(place)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    borrower = world.add(Entity(id=borrower_name, kind="character", type=borrower_gender, role="borrower"))
    helper = world.add(Entity(id=helper_name, kind="character", type=place.helper_type, role="helper", label="the helper"))
    item_ent = world.add(Entity(id="item", type=item.id, label=item.label, role="item", tags=set(item.tags)))
    clue_ent = world.add(Entity(id="clue", type=clue.id, label=clue.label, role="clue", tags=set(clue.tags)))
    approach_ent = world.add(Entity(id="approach", type=approach.id, label=approach.id, role="approach", attrs={"gentle": approach.gentle}))

    world.facts.update(
        place=place,
        item_cfg=item,
        clue_cfg=clue,
        approach_cfg=approach,
        detective=detective,
        borrower=borrower,
        helper=helper,
        item=item_ent,
        clue=clue_ent,
        approach=approach_ent,
    )

    detective.memes["kindness"] = 1.0
    borrower.memes["desire"] = 1.0
    borrower.memes["honesty"] = 0.0
    item_ent.meters["missing"] = 0.0
    item_ent.meters["returned"] = 0.0
    clue_ent.meters["noticed"] = 0.0
    approach_ent.meters["used"] = 0.0

    introduce(world, detective, borrower, helper, item)
    world.para()
    discovery(world, detective, helper, item)
    clue_scene(world, detective, clue)
    track_scene(world, detective, borrower, item, clue)
    world.para()
    approach_scene(world, detective, borrower, approach)
    repair_scene(world, detective, borrower, helper, item)
    world.para()
    ending_scene(world, detective, borrower, helper, item)

    world.facts.update(
        solved=item_ent.meters["returned"] >= THRESHOLD,
        moral="ask before borrowing and tell the truth",
        reveal_place=place.clue_sites.get(clue.id, clue.reveal_place),
    )
    return world


KNOWLEDGE = {
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Detectives notice clues instead of making wild guesses."
        )
    ],
    "honesty": [
        (
            "Why is honesty important?",
            "Honesty helps people trust each other. Telling the truth can feel hard for a moment, but it fixes problems faster."
        )
    ],
    "sharing": [
        (
            "Why should you ask before borrowing something?",
            "You should ask first because the other person may still need it or want to know where it went. Asking shows respect and keeps sharing fair."
        )
    ],
    "kindness": [
        (
            "Why is it better to ask kindly than to accuse someone loudly?",
            "A kind question gives a person room to explain the truth. Loud accusing can make people scared or embarrassed before you even know what happened."
        )
    ],
    "book": [
        (
            "What does a bookmark do?",
            "A bookmark keeps your place in a book so you can find the page again later."
        )
    ],
    "blocks": [
        (
            "What are building blocks for?",
            "Building blocks are for stacking, measuring, and making towers or roads. Children use them to build things with their hands."
        )
    ],
    "paper": [
        (
            "What is a collage?",
            "A collage is a picture made by sticking different paper pieces or materials onto one page."
        )
    ],
    "ink": [
        (
            "What is ink?",
            "Ink is colored liquid used for printing, drawing, or stamping. It can leave dots or smudges if it is still wet."
        )
    ],
}
KNOWLEDGE_ORDER = ["clue", "honesty", "sharing", "kindness", "book", "blocks", "paper", "ink"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    borrower = f["borrower"]
    item = f["item_cfg"]
    place = f["place"]
    clue = f["clue_cfg"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the word "glee" and teaches honesty.',
        f"Tell a gentle mystery set in {place.label} where {detective.id} follows {clue.label} clues to find a missing {item.label}, then solves the case with kindness.",
        f"Write a child-facing detective story where {borrower.id} borrows a shared {item.label} without asking, tells the truth, and learns a moral about sharing fairly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    borrower = f["borrower"]
    helper = f["helper"]
    item = f["item_cfg"]
    clue = f["clue_cfg"]
    approach = f["approach_cfg"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, {borrower.id}, who borrowed something without asking, and {helper.id}, who noticed it was missing."
        ),
        (
            f"What was missing in {place.label}?",
            f"{item.phrase} was missing. It mattered because it belonged to everyone there and was supposed to stay where the group could share it."
        ),
        (
            f"What clue helped {detective.id} solve the mystery?",
            f"The clue was {clue.marks}. It pointed {detective.id} toward {f['reveal_place']}, which is where the missing {item.label} turned up."
        ),
        (
            f"How did {detective.id} solve the case?",
            f"{detective.id} {approach.qa_text}. That kind choice helped {borrower.id} admit the truth and return the {item.label}."
        ),
        (
            f"Why did {borrower.id} give the {item.label} back?",
            f"{borrower.id} gave it back after telling the truth about borrowing it for one more turn. The gentle question made honesty feel safer than hiding."
        ),
        (
            "What is the moral of the story?",
            "The moral is that you should ask before borrowing and tell the truth when something has gone wrong. Those two choices help people trust each other again."
        ),
        (
            f"Why did {detective.id} feel glee at the end?",
            f"{detective.id} felt glee because the mystery was solved and the room felt fair again. The happy feeling came from truth and kindness winning together."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"clue", "honesty", "sharing", "kindness"}
    tags |= set(f["item_cfg"].tags)
    tags |= set(f["clue_cfg"].tags)
    tags |= set(f["approach_cfg"].tags)
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
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo_rejection(place: Place, item: MissingItem, clue: Clue) -> str:
    if not item_fits_place(place, item):
        return (
            f"(No story: {item.label} does not belong in {place.label}, so it would not be a natural missing object there.)"
        )
    return (
        f"(No story: {clue.label} is not a sensible clue for a missing {item.label} in {place.label}. Pick a clue that actually points to where the item was used.)"
    )


def explain_approach_rejection(approach_id: str) -> str:
    approach = APPROACHES[approach_id]
    return (
        f"(Refusing approach '{approach_id}': it scores too low on kindness and common sense "
        f"(sense={approach.sense} < {SENSE_MIN}). This world prefers detective work that checks facts kindly and leaves room for honesty.)"
    )


ASP_RULES = r"""
fits_place(P,I) :- place(P), item(I), affords(P,I).
valid_clue(P,I,C) :- place(P), item(I), clue(C), matches(P,I,C).

valid(P,I,C) :- fits_place(P,I), valid_clue(P,I,C).

sensible(A) :- approach(A), sense(A,S), sense_min(M), S >= M.
gentle(A)   :- approach(A), is_gentle(A).

solved :- chosen_approach(A), sensible(A), gentle(A),
          chosen_place(P), chosen_item(I), chosen_clue(C), valid(P,I,C).

outcome(restored) :- solved.
outcome(failed)   :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for item_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, item_id))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for place_id, item_id, clue_id in valid_combos():
        lines.append(asp.fact("matches", place_id, item_id, clue_id))
    for approach_id, approach in APPROACHES.items():
        lines.append(asp.fact("approach", approach_id))
        lines.append(asp.fact("sense", approach_id, approach.sense))
        if approach.gentle:
            lines.append(asp.fact("is_gentle", approach_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    item = ITEMS[params.item]
    clue = CLUES[params.clue]
    approach = APPROACHES[params.approach]
    ok = item_fits_place(place, item) and clue_fits(place, item, clue) and approach.sense >= SENSE_MIN and approach.gentle
    return "restored" if ok else "failed"


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_approach", params.approach),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle detective mystery about honesty, borrowing, and glee."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--detective-name")
    ap.add_argument("--borrower-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--borrower-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and not item_fits_place(PLACES[args.place], ITEMS[args.item]):
        clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
        raise StoryError(explain_combo_rejection(PLACES[args.place], ITEMS[args.item], clue))
    if args.place and args.item and args.clue:
        if not clue_fits(PLACES[args.place], ITEMS[args.item], CLUES[args.clue]):
            raise StoryError(explain_combo_rejection(PLACES[args.place], ITEMS[args.item], CLUES[args.clue]))
    if args.approach and APPROACHES[args.approach].sense < SENSE_MIN:
        raise StoryError(explain_approach_rejection(args.approach))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, clue_id = rng.choice(sorted(combos))
    approach_id = args.approach or rng.choice(sorted(a.id for a in sensible_approaches()))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    borrower_gender = args.borrower_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _pick_name(rng, detective_gender)
    borrower_name = args.borrower_name or _pick_name(rng, borrower_gender, avoid=detective_name)

    return StoryParams(
        place=place_id,
        item=item_id,
        clue=clue_id,
        approach=approach_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        borrower_name=borrower_name,
        borrower_gender=borrower_gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        item = ITEMS[params.item]
        clue = CLUES[params.clue]
        approach = APPROACHES[params.approach]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc})") from exc

    if not item_fits_place(place, item) or not clue_fits(place, item, clue):
        raise StoryError(explain_combo_rejection(place, item, clue))
    if approach.sense < SENSE_MIN:
        raise StoryError(explain_approach_rejection(params.approach))

    world = tell(
        place=place,
        item=item,
        clue=clue,
        approach=approach,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        borrower_name=params.borrower_name,
        borrower_gender=params.borrower_gender,
        helper_name=params.helper_name,
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


CURATED = [
    StoryParams(
        place="classroom",
        item="ruler",
        clue="block_dust",
        approach="ask_kindly",
        detective_name="Lily",
        detective_gender="girl",
        borrower_name="Max",
        borrower_gender="boy",
    ),
    StoryParams(
        place="library",
        item="storybook",
        clue="bookmark",
        approach="whisper_privately",
        detective_name="Ben",
        detective_gender="boy",
        borrower_name="Nora",
        borrower_gender="girl",
    ),
    StoryParams(
        place="art_room",
        item="glue_stick",
        clue="paper_bits",
        approach="ask_kindly",
        detective_name="Mia",
        detective_gender="girl",
        borrower_name="Sam",
        borrower_gender="boy",
    ),
    StoryParams(
        place="library",
        item="stamp",
        clue="ink_dot",
        approach="whisper_privately",
        detective_name="Leo",
        detective_gender="boy",
        borrower_name="Rose",
        borrower_gender="girl",
    ),
]


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos parity holds ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {a.id for a in sensible_approaches()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible approaches match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible approaches: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome parity holds on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcome checks differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible approaches: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (place, item, clue) combos:\n")
        for place_id, item_id, clue_id in combos:
            print(f"  {place_id:10} {item_id:10} {clue_id}")
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
            header = f"### {p.detective_name}: {p.item} missing in {p.place} ({p.clue}, {p.approach})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
