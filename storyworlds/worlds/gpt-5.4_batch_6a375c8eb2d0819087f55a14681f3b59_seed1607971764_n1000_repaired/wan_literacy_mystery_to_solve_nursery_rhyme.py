#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wan_literacy_mystery_to_solve_nursery_rhyme.py
===========================================================================

A standalone storyworld for a tiny nursery-rhyme-style mystery: a child arrives
for rhyme time and finds the reading board strangely bare and wan because the
day's rhyme card has gone missing. By noticing a concrete clue and using early
literacy -- matching letters, sounding out a word, and checking the right place
-- the child solves the mystery and brings the rhyme back.

The world models:
- typed entities with physical meters and emotional memes
- a small causal rule engine
- a reasonableness gate over clue/cause/place/method compatibility
- a declarative ASP twin for parity checks
- three Q&A sets generated from world state, not from parsing English

Run it:
    python storyworlds/worlds/gpt-5.4/wan_literacy_mystery_to_solve_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/wan_literacy_mystery_to_solve_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/wan_literacy_mystery_to_solve_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/wan_literacy_mystery_to_solve_nursery_rhyme.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    readable: bool = False
    container: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rhyme:
    id: str
    title: str
    object_label: str
    opening: str
    chant: str
    first_letter: str
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
class Cause:
    id: str
    label: str
    move_text: str
    clue_kind: str
    place_kind: str
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
class Place:
    id: str
    label: str
    phrase: str
    kind: str
    prep: str
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
    finds_kinds: set[str] = field(default_factory=set)
    text: str = ""
    qa_text: str = ""
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


def _r_board_wan(world: World) -> list[str]:
    card = world.get("card")
    board = world.get("board")
    if card.attrs.get("location") != "board":
        sig = ("board_wan",)
        if sig not in world.fired:
            world.fired.add(sig)
            board.meters["empty"] += 1
            board.meters["wan"] += 1
    return []


def _r_worry(world: World) -> list[str]:
    child = world.get("hero")
    board = world.get("board")
    if board.meters["wan"] < THRESHOLD:
        return []
    sig = ("worry", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    return []


def _r_curiosity(world: World) -> list[str]:
    child = world.get("hero")
    clue = world.get("clue")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("curiosity", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    child.memes["hope"] += 1
    return []


def _r_solve(world: World) -> list[str]:
    card = world.get("card")
    clue = world.get("clue")
    place = world.get("hiding_place")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    if place.meters["searched"] < THRESHOLD:
        return []
    if card.attrs.get("location") != place.id:
        return []
    sig = ("solved",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    card.meters["found"] += 1
    card.attrs["location"] = "hero"
    world.get("hero").memes["pride"] += 1
    world.get("helper").memes["pride"] += 1
    return []


def _r_restore(world: World) -> list[str]:
    card = world.get("card")
    board = world.get("board")
    if card.meters["found"] < THRESHOLD:
        return []
    if card.attrs.get("location") != "hero":
        return []
    sig = ("restore",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    card.attrs["location"] = "board"
    board.meters["wan"] = 0.0
    board.meters["bright"] += 1
    world.get("hero").memes["relief"] += 1
    world.get("teacher").memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="board_wan", tag="physical", apply=_r_board_wan),
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="curiosity", tag="emotional", apply=_r_curiosity),
    Rule(name="solve", tag="social", apply=_r_solve),
    Rule(name="restore", tag="physical", apply=_r_restore),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(res)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def compatible(cause: Cause, place: Place) -> bool:
    return cause.place_kind == place.kind


def method_works(method: Method, cause: Cause, place: Place) -> bool:
    return place.kind in method.finds_kinds and cause.place_kind == place.kind


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for rhyme_id in RHYMES:
        for cause_id, cause in CAUSES.items():
            for place_id, place in PLACES.items():
                if not compatible(cause, place):
                    continue
                for method_id, method in METHODS.items():
                    if method.sense >= SENSE_MIN and method_works(method, cause, place):
                        combos.append((rhyme_id, cause_id, place_id, method_id))
    return combos


def predict_success(world: World, place_id: str) -> bool:
    sim = world.copy()
    sim.get(place_id).meters["searched"] += 1
    propagate(sim, narrate=False)
    return sim.get("card").meters["found"] >= THRESHOLD


def introduce(world: World, hero: Entity, helper: Entity, teacher: Entity, rhyme: Rhyme) -> None:
    world.say(
        f"{hero.id} and {helper.id} came tip-tap-tapping to the reading rug. "
        f"{teacher.label_word.capitalize()} had promised a rhyme about {rhyme.object_label}."
    )
    world.say(
        f'The children liked letters, little sounds, and picture cards, and {hero.id} called it literacy magic.'
    )


def board_is_bare(world: World, hero: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} looked up, the rhyme board seemed wan and bare. "
        f"The clip was there, yet the card itself was gone."
    )


def teacher_wonders(world: World, teacher: Entity) -> None:
    teacher.memes["concern"] += 1
    world.say(
        f'"Oh dear," said the {teacher.label_word}, "our morning verse has wandered away."'
    )


def notice_clue(world: World, hero: Entity, helper: Entity, clue_text: str) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} knelt down and {helper.id} peeped near the board. '
        f'"Look," said {hero.id}, "{clue_text}"'
    )


def search_place(world: World, hero: Entity, helper: Entity, place: Place, method: Method) -> None:
    target = world.get("hiding_place")
    target.meters["searched"] += 1
    world.facts["searched_place"] = place.id
    success = predict_success(world, place.id)
    world.say(
        f"{hero.id} used {method.label} and led {helper.id} {place.prep} {place.phrase}."
    )
    if success:
        world.say(
            f"They looked carefully {place.prep} {place.phrase}, not in a rush but letter by letter."
        )
    propagate(world, narrate=False)


def recover(world: World, hero: Entity, helper: Entity, teacher: Entity, rhyme: Rhyme, method: Method, place: Place) -> None:
    card = world.get("card")
    if card.meters["found"] < THRESHOLD:
        raise StoryError("The search did not truly find the missing rhyme card.")
    world.say(
        f"There it was {place.prep} {place.phrase}: the rhyme card with a big {rhyme.first_letter} at the top."
    )
    world.say(
        f'"{rhyme.first_letter} is for {rhyme.object_label}!" cried {hero.id}. '
        f'{helper.id} clapped because {method.qa_text}.'
    )
    propagate(world, narrate=False)
    if card.attrs.get("location") != "board":
        raise StoryError("The rhyme card was found but not restored to the board.")
    world.say(
        f"Soon the board looked bright instead of wan, and the room felt ready to sing."
    )
    world.say(
        f'Then the children chimed, "{rhyme.chant}" and even the quiet corners seemed to hum along.'
    )


def tell(
    rhyme: Rhyme,
    cause: Cause,
    place: Place,
    method: Method,
    hero_name: str = "Mina",
    hero_gender: str = "girl",
    helper_name: str = "Pip",
    helper_gender: str = "boy",
    teacher_type: str = "teacher",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    teacher = world.add(Entity(id="teacher", kind="character", type=teacher_type, label="the teacher", role="teacher"))
    board = world.add(Entity(id="board", type="board", label="rhyme board"))
    clue = world.add(Entity(id="clue", type="clue", label=cause.clue_kind))
    hiding = world.add(Entity(id="hiding_place", type="place", label=place.label, phrase=place.phrase, container=True))
    card = world.add(
        Entity(
            id="card",
            type="card",
            label="rhyme card",
            phrase=f"the {rhyme.title} rhyme card",
            movable=True,
            readable=True,
            attrs={"location": place.id, "rhyme": rhyme.id},
        )
    )

    world.facts.update(
        hero_name=hero_name,
        helper_name=helper_name,
        teacher_label=teacher.label_word,
        rhyme=rhyme,
        cause=cause,
        place=place,
        method=method,
        clue_text="",
        searched_place="",
    )

    propagate(world, narrate=False)

    introduce(world, hero, helper, teacher, rhyme)
    board_is_bare(world, hero)
    teacher_wonders(world, teacher)

    world.para()
    clue_text = {
        "feather": "a soft feather lay on the floor, all white and tickly",
        "yarn": "a curl of woolly yarn had snagged on the clip",
        "bookmark": f'a striped bookmark showed the letter "{rhyme.first_letter}"',
    }[cause.clue_kind]
    world.facts["clue_text"] = clue_text
    notice_clue(world, hero, helper, clue_text)
    world.say(
        f"The clue made sense to {hero.id}. {cause.move_text}, so the missing card might be hiding nearby."
    )

    world.para()
    search_place(world, hero, helper, place, method)
    recover(world, hero, helper, teacher, rhyme, method, place)

    world.facts.update(
        solved=world.get("card").meters["found"] >= THRESHOLD,
        restored=world.get("board").meters["bright"] >= THRESHOLD,
        board_wan=world.get("board").meters["wan"] < THRESHOLD,
    )
    return world


RHYMES = {
    "star": Rhyme(
        id="star",
        title="Star Song",
        object_label="star",
        opening="Twinkle, tipple, little star,",
        chant="Twinkle, tipple, little star, back you are where bright things are!",
        first_letter="S",
        tags={"letters", "rhyme", "star"},
    ),
    "moon": Rhyme(
        id="moon",
        title="Moon Tune",
        object_label="moon",
        opening="Round the room rolled the moon,",
        chant="Round the room rolled the moon, now we can all sing the tune!",
        first_letter="M",
        tags={"letters", "rhyme", "moon"},
    ),
    "sheep": Rhyme(
        id="sheep",
        title="Sleepy Sheep",
        object_label="sheep",
        opening="Baa-baa, sleepy sheep,",
        chant="Baa-baa, sleepy sheep, back from your hiding heap!",
        first_letter="S",
        tags={"letters", "rhyme", "sheep"},
    ),
}

CAUSES = {
    "bird": Cause(
        id="bird",
        label="window bird",
        move_text="A little window bird had fluttered in and batted the card away",
        clue_kind="feather",
        place_kind="high",
        tags={"bird", "feather"},
    ),
    "lamb": Cause(
        id="lamb",
        label="woolly lamb puppet",
        move_text="The woolly lamb puppet must have nudged the card while wobbling from the shelf",
        clue_kind="yarn",
        place_kind="soft",
        tags={"lamb", "yarn"},
    ),
    "bookworm": Cause(
        id="bookworm",
        label="book-loving toddler",
        move_text="The tiniest book-lover had tucked the card where books and markers sleep",
        clue_kind="bookmark",
        place_kind="books",
        tags={"bookmark", "books"},
    ),
}

PLACES = {
    "sill": Place(
        id="sill",
        label="window sill",
        phrase="the window sill",
        kind="high",
        prep="on",
        tags={"window"},
    ),
    "cushion_basket": Place(
        id="cushion_basket",
        label="cushion basket",
        phrase="the cushion basket",
        kind="soft",
        prep="in",
        tags={"basket", "soft"},
    ),
    "book_bin": Place(
        id="book_bin",
        label="book bin",
        phrase="the book bin",
        kind="books",
        prep="in",
        tags={"books"},
    ),
}

METHODS = {
    "look_up": Method(
        id="look_up",
        label="patient looking up high",
        sense=3,
        finds_kinds={"high"},
        text="tilted careful faces upward and checked the high places",
        qa_text="they looked up where a fluttering thing could land",
        tags={"look", "window"},
    ),
    "pat_soft": Method(
        id="pat_soft",
        label="gentle patting through the soft things",
        sense=3,
        finds_kinds={"soft"},
        text="patted through the soft pile with slow little hands",
        qa_text="they felt through the soft basket where a puppet could nudge it",
        tags={"touch", "basket"},
    ),
    "match_letter": Method(
        id="match_letter",
        label="matching the first letter on the clue",
        sense=3,
        finds_kinds={"books"},
        text="matched the printed letter and checked where bookmarks belong",
        qa_text="they followed the letter clue to the book bin",
        tags={"letters", "books", "literacy"},
    ),
    "under_rug": Method(
        id="under_rug",
        label="peeking under the rug",
        sense=1,
        finds_kinds=set(),
        text="peeked under the rug for no good reason",
        qa_text="they looked in a place that did not fit the clue",
        tags={"wrong"},
    ),
}

GIRL_NAMES = ["Mina", "Nell", "Dora", "Ruby", "Ivy", "Tessa", "Wren", "Lila"]
BOY_NAMES = ["Pip", "Ollie", "Ben", "Toby", "Finn", "Milo", "Ned", "Kit"]


@dataclass
class StoryParams:
    rhyme: str
    cause: str
    place: str
    method: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    teacher: str = "teacher"
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
    "literacy": [
        (
            "What is literacy?",
            "Literacy means learning how letters, sounds, and words work together. It helps children read signs, books, and little rhyme cards."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a little pattern of words with matching sounds. Rhymes make songs and verses easier to remember."
        )
    ],
    "letters": [
        (
            "Why can the first letter help solve a mystery?",
            "The first letter is a clue about what word you are looking for. If you know the sound it makes, you can search in the place that fits."
        )
    ],
    "feather": [
        (
            "What can a feather tell you?",
            "A feather can show that a bird has been nearby. It is a clue because it points to something that flutters."
        )
    ],
    "yarn": [
        (
            "Why does yarn make a good clue?",
            "Yarn can stick to woolly toys and puppets. If you see yarn, it may tell you which toy brushed past."
        )
    ],
    "bookmark": [
        (
            "What is a bookmark for?",
            "A bookmark keeps your place in a book. If a clue looks like a bookmark, it may lead you to books."
        )
    ],
    "window": [
        (
            "Why might something light land on a window sill?",
            "A light paper card can drift or be batted toward a sill. High ledges often catch light things."
        )
    ],
    "books": [
        (
            "Why would a missing card be checked near books?",
            "People often tuck flat things into book bins or between pages. A reading clue makes the book area a sensible place to search."
        )
    ],
    "basket": [
        (
            "Why do soft baskets hide things easily?",
            "Soft blankets and cushions can cover a small card. A flat paper can slip down and vanish under the pile."
        )
    ],
}
KNOWLEDGE_ORDER = ["literacy", "rhyme", "letters", "feather", "yarn", "bookmark", "window", "books", "basket"]


def generation_prompts(world: World) -> list[str]:
    rhyme = world.facts["rhyme"]
    cause = world.facts["cause"]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old about a missing rhyme card and a small mystery to solve. Include the words "wan" and "literacy".',
        f"Tell a gentle mystery where children notice a clue, use early literacy, and find a lost rhyme about a {rhyme.object_label}.",
        f"Write a sing-song story where a {cause.label} leaves a clue, two children search the right place, and the room ends bright with a rhyme."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    rhyme = world.facts["rhyme"]
    cause = world.facts["cause"]
    place = world.facts["place"]
    method = world.facts["method"]
    hero_name = world.facts["hero_name"]
    helper_name = world.facts["helper_name"]
    clue_text = world.facts["clue_text"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that the morning rhyme card had gone missing from the board. The board looked wan and bare, so the children knew something important had changed."
        ),
        (
            "What clue did the children notice?",
            f"They noticed that {clue_text}. That clue mattered because it pointed toward {cause.label} and helped them choose where to look."
        ),
        (
            f"How did {hero_name} use literacy to help solve the mystery?",
            f"{hero_name} paid attention to the letter clue and to what kind of place matched it. That early literacy thinking turned the search from guessing into a smart plan."
        ),
        (
            f"Why did {hero_name} and {helper_name} search {place.phrase}?",
            f"They searched {place.phrase} because the clue fit that place and because {method.qa_text}. The search worked because they followed cause and clue together instead of looking anywhere at random."
        ),
        (
            "How did the story end?",
            f"They found the rhyme card, clipped it back on the board, and the room felt bright again. The ending image proves the mystery was solved because the class could sing the rhyme at last."
        ),
    ]
    if cause.id == "bookworm":
        qa.append(
            (
                "Why was the book clue especially helpful?",
                f'The bookmark clue showed the letter "{rhyme.first_letter}", and that gave the children a reading clue as well as a hiding clue. It led them to the book bin, where flat paper belonged.'
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"literacy", "rhyme", "letters"}
    cause = world.facts["cause"]
    place = world.facts["place"]
    tags |= set(cause.tags)
    tags |= set(place.tags)
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
        attrs = {k: v for k, v in e.attrs.items() if v not in ("", None, 0)}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        rhyme="moon",
        cause="bookworm",
        place="book_bin",
        method="match_letter",
        hero_name="Mina",
        hero_gender="girl",
        helper_name="Pip",
        helper_gender="boy",
        teacher="teacher",
    ),
    StoryParams(
        rhyme="star",
        cause="bird",
        place="sill",
        method="look_up",
        hero_name="Ruby",
        hero_gender="girl",
        helper_name="Milo",
        helper_gender="boy",
        teacher="teacher",
    ),
    StoryParams(
        rhyme="sheep",
        cause="lamb",
        place="cushion_basket",
        method="pat_soft",
        hero_name="Nell",
        hero_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        teacher="teacher",
    ),
]


def explain_rejection(cause: Cause, place: Place, method: Method) -> str:
    if not compatible(cause, place):
        return (
            f"(No story: the clue from {cause.label} points to a {cause.place_kind} place, "
            f"but {place.phrase} is a {place.kind} place. The mystery would not be honest.)"
        )
    if method.sense < SENSE_MIN:
        return (
            f"(No story: the search method '{method.id}' is too weak for a sensible mystery. "
            f"Pick a method that actually fits the clue.)"
        )
    return (
        f"(No story: the method '{method.id}' does not fit {place.phrase}. "
        f"The search must follow the clue to the right kind of hiding place.)"
    )


ASP_RULES = r"""
compatible(C, P) :- cause(C), place(P), cause_place_kind(C, K), place_kind(P, K).
sensible(M) :- method(M), sense(M, S), sense_min(MN), S >= MN.
works(M, C, P) :- method_finds(M, K), cause_place_kind(C, K), place_kind(P, K).
valid(R, C, P, M) :- rhyme(R), compatible(C, P), sensible(M), works(M, C, P).

outcome(solved) :- chosen_cause(C), chosen_place(P), chosen_method(M),
                   compatible(C, P), sensible(M), works(M, C, P).
:- chosen_cause(C), chosen_place(P), chosen_method(M), not outcome(solved).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rhyme_id in RHYMES:
        lines.append(asp.fact("rhyme", rhyme_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_place_kind", cause_id, cause.place_kind))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("place_kind", place_id, place.kind))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for k in sorted(method.finds_kinds):
            lines.append(asp.fact("method_finds", method_id, k))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_cause", params.cause),
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    cause = CAUSES[params.cause]
    place = PLACES[params.place]
    method = METHODS[params.method]
    if compatible(cause, place) and method.sense >= SENSE_MIN and method_works(method, cause, place):
        return "solved"
    return "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme mystery storyworld: a missing rhyme card is solved with clues and literacy."
    )
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.place and not compatible(CAUSES[args.cause], PLACES[args.place]):
        method = METHODS[args.method] if args.method else next(iter(METHODS.values()))
        raise StoryError(explain_rejection(CAUSES[args.cause], PLACES[args.place], method))
    if args.method:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            cause = CAUSES[args.cause] if args.cause else next(iter(CAUSES.values()))
            place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
            raise StoryError(explain_rejection(cause, place, method))
        if args.cause and args.place and not method_works(method, CAUSES[args.cause], PLACES[args.place]):
            raise StoryError(explain_rejection(CAUSES[args.cause], PLACES[args.place], method))

    combos = [
        c for c in valid_combos()
        if (args.rhyme is None or c[0] == args.rhyme)
        and (args.cause is None or c[1] == args.cause)
        and (args.place is None or c[2] == args.place)
        and (args.method is None or c[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    rhyme_id, cause_id, place_id, method_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=hero_name)
    return StoryParams(
        rhyme=rhyme_id,
        cause=cause_id,
        place=place_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        teacher="teacher",
    )


def generate(params: StoryParams) -> StorySample:
    if params.rhyme not in RHYMES:
        raise StoryError(f"Unknown rhyme: {params.rhyme}")
    if params.cause not in CAUSES:
        raise StoryError(f"Unknown cause: {params.cause}")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.method not in METHODS:
        raise StoryError(f"Unknown method: {params.method}")

    rhyme = RHYMES[params.rhyme]
    cause = CAUSES[params.cause]
    place = PLACES[params.place]
    method = METHODS[params.method]
    if not compatible(cause, place) or method.sense < SENSE_MIN or not method_works(method, cause, place):
        raise StoryError(explain_rejection(cause, place, method))

    world = tell(
        rhyme=rhyme,
        cause=cause,
        place=place,
        method=method,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        teacher_type=params.teacher,
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
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sens = {m.id for m in sensible_methods()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible methods match ({sorted(py_sens)}).")
    else:
        rc = 1
        print("MISMATCH in sensible methods:")
        print("  python:", sorted(py_sens))
        print("  clingo:", sorted(asp_sens))

    cases: list[StoryParams] = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            break

    mismatches = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} scenario outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (rhyme, cause, place, method) combos:\n")
        for rhyme, cause, place, method in combos:
            print(f"  {rhyme:6} {cause:9} {place:15} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} & {p.helper_name}: {p.rhyme} mystery ({p.cause}, {p.place}, {p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
