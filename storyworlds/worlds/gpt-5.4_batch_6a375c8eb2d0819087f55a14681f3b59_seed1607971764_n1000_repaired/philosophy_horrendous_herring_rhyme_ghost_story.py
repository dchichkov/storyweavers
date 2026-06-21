#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/philosophy_horrendous_herring_rhyme_ghost_story.py
==============================================================================

A standalone story world for a gentle ghost story with a seaside smell, a lost
book of philosophy, and a rhyming way to ask what the ghost needs.

The core tale rebuilt here is:

- a child sleeps in a creaky seaside place
- a horrendous herring smell drifts through the hall
- a ghostly whisper makes the room feel scary
- the child does not solve the problem by guessing about the smell alone
- with a lantern and a rhyme, the child learns the ghost wants an old philosophy
  book returned
- when the book is found and the herring barrel is shut, the room changes from
  eerie to peaceful

Run it
------
    python storyworlds/worlds/gpt-5.4/philosophy_horrendous_herring_rhyme_ghost_story.py
    python storyworlds/worlds/gpt-5.4/philosophy_horrendous_herring_rhyme_ghost_story.py --place lighthouse
    python storyworlds/worlds/gpt-5.4/philosophy_horrendous_herring_rhyme_ghost_story.py --spot chest
    python storyworlds/worlds/gpt-5.4/philosophy_horrendous_herring_rhyme_ghost_story.py --response rhyme_question
    python storyworlds/worlds/gpt-5.4/philosophy_horrendous_herring_rhyme_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/philosophy_horrendous_herring_rhyme_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/philosophy_horrendous_herring_rhyme_ghost_story.py --verify
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
        female = {"girl", "mother", "aunt", "grandmother", "woman"}
        male = {"boy", "father", "uncle", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
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
    opening: str
    herring_where: str
    afford_spots: set[str] = field(default_factory=set)
    eerie: int = 1
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
class Spot:
    id: str
    label: str
    phrase: str
    discover: str
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
class Response:
    id: str
    sense: int
    power: int
    couplet: tuple[str, str]
    intro: str
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


@dataclass
class HelperCfg:
    id: str
    type: str
    entrance: str
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


def _r_smell(world: World) -> list[str]:
    herring = world.get("herring")
    room = world.get("room")
    child = world.get("child")
    if herring.meters["open"] < THRESHOLD:
        return []
    sig = ("smell",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["smelly"] += 1
    child.memes["unease"] += 1
    return ["__smell__"]


def _r_haunt(world: World) -> list[str]:
    ghost = world.get("ghost")
    room = world.get("room")
    child = world.get("child")
    if ghost.meters["unrest"] < THRESHOLD:
        return []
    sig = ("haunt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["eerie"] += 1
    child.memes["fear"] += 1
    return ["__haunt__"]


def _r_return(world: World) -> list[str]:
    ghost = world.get("ghost")
    book = world.get("book")
    child = world.get("child")
    helper = world.get("helper")
    if book.meters["returned"] < THRESHOLD or ghost.memes["trust"] < THRESHOLD:
        return []
    sig = ("return",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["unrest"] = 0.0
    ghost.memes["peace"] += 1
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    return ["__peace__"]


CAUSAL_RULES = [
    Rule(name="smell", tag="physical", apply=_r_smell),
    Rule(name="haunt", tag="emotional", apply=_r_haunt),
    Rule(name="return", tag="resolution", apply=_r_return),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(place_id: str, spot_id: str) -> bool:
    if place_id not in PLACES or spot_id not in SPOTS:
        return False
    return spot_id in PLACES[place_id].afford_spots


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for spot_id in sorted(place.afford_spots):
            out.append((place_id, spot_id))
    return sorted(out)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def eerie_severity(place: Place, delay: int) -> int:
    return place.eerie + delay


def bright_enough(response: Response, place: Place, delay: int) -> bool:
    return response.power >= eerie_severity(place, delay)


def explain_combo(place_id: str, spot_id: str) -> str:
    if place_id not in PLACES:
        return f"(No story: unknown place '{place_id}'.)"
    if spot_id not in SPOTS:
        return f"(No story: unknown hiding spot '{spot_id}'.)"
    place = PLACES[place_id]
    spot = SPOTS[spot_id]
    return (
        f"(No story: in {place.label}, the old book would not reasonably be hidden "
        f"{spot.phrase}. Pick a spot that belongs in that place.)"
    )


def explain_response(response_id: str) -> str:
    if response_id not in RESPONSES:
        return f"(No story: unknown response '{response_id}'.)"
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_reveal(world: World, response: Response) -> dict:
    sim = world.copy()
    sim.get("ghost").memes["trust"] += 1
    revealed = bright_enough(response, sim.place, int(sim.facts["delay"]))
    if revealed:
        sim.get("book").meters["found"] += 1
    return {
        "revealed": revealed,
        "fear": sim.get("child").memes["fear"],
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"Late one foggy evening, {child.id} stayed with {child.pronoun('possessive')} "
        f"{helper.label_word} in {place.label}. {place.opening}"
    )
    world.say(
        f"{child.id} had brought a small lantern for the walk to bed and an old "
        f"philosophy book that lived on the hall shelf because everyone said the "
        f"house liked quiet thinking."
    )


def start_smell(world: World, child: Entity, place: Place) -> None:
    world.get("herring").meters["open"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a horrendous herring smell drifted in from {place.herring_where}. "
        f"{child.id} wrinkled {child.pronoun('possessive')} nose and pulled the blanket up."
    )


def haunting(world: World, child: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"A pale whisper slipped through the dark hall. It was not loud, but it "
        f"made the floorboards seem to listen, and {child.id}'s lantern glass trembled."
    )
    world.say(
        f'"Whooo left my book?" sighed the voice. {child.id} felt a cold tickle of fear.'
    )


def helper_enters(world: World, child: Entity, helper: Entity, cfg: HelperCfg) -> None:
    world.say(
        f"{cfg.entrance} {helper.label_word.capitalize()} came with slipper-soft steps "
        f"and stood beside {child.id} instead of sending {child.pronoun('object')} back under the covers."
    )


def choose_rhyme(world: World, child: Entity, helper: Entity, response: Response) -> None:
    pred = predict_reveal(world, response)
    world.facts["predicted_reveal"] = pred["revealed"]
    child.memes["courage"] += 1
    ghost = world.get("ghost")
    ghost.memes["trust"] += 1
    world.say(response.intro)
    world.say(f'"{response.couplet[0]}"')
    world.say(f'"{response.couplet[1]}"')


def reveal_book(world: World, child: Entity, spot: Spot) -> None:
    book = world.get("book")
    book.meters["found"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"At once the whisper changed. A cold little glow floated toward {spot.phrase}, "
        f"and there, {spot.discover}, lay the philosophy book."
    )


def search_longer(world: World, child: Entity, helper: Entity, spot: Spot) -> None:
    book = world.get("book")
    helper.memes["care"] += 1
    book.meters["found"] += 1
    world.say(
        f"The rhyme made the whisper softer, but not clear enough. So {helper.label_word} "
        f"lifted the lantern higher, and together they searched the hall until {child.id} "
        f"spotted a silver corner {spot.phrase}."
    )
    world.say(
        f"There, {spot.discover}, lay the philosophy book at last."
    )


def close_herring(world: World, helper: Entity, place: Place) -> None:
    world.get("herring").meters["open"] = 0.0
    world.say(
        f"{helper.label_word.capitalize()} shut the loose herring barrel lid from {place.herring_where}, "
        f"and the horrendous smell stopped crowding the room."
    )


def return_book(world: World, child: Entity, helper: Entity) -> None:
    book = world.get("book")
    ghost = world.get("ghost")
    book.meters["returned"] += 1
    ghost.memes["trust"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} carried the philosophy book back to the shelf with both hands, "
        f"and {helper.label_word} held the lantern steady."
    )


def peaceful_ending(world: World, child: Entity, helper: Entity) -> None:
    ghost = world.get("ghost")
    if ghost.meters["unrest"] < THRESHOLD:
        world.say(
            "The ghost gathered itself into a pearly hush. It bowed once, thin as moonlight, "
            "and the hall stopped creaking as if the whole house had finally taken a calm breath."
        )
    world.say(
        f'"Thank you," whispered the ghost, and this time the voice sounded sleepy instead of sad.'
    )
    world.say(
        f"{child.id} climbed back into bed. By the time the lantern was turned low, the sea "
        f"murmured outside, the shelf held its book again, and the night felt gentle."
    )


def tell(
    *,
    place: Place,
    spot: Spot,
    response: Response,
    helper_cfg: HelperCfg,
    child_name: str,
    child_gender: str,
    delay: int,
) -> World:
    world = World(place=place)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.type, role="helper"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", role="ghost"))
    room = world.add(Entity(id="room", type="room", label=place.label))
    herring = world.add(Entity(id="herring", type="barrel", label="herring barrel"))
    book = world.add(Entity(id="book", type="book", label="philosophy book"))

    child.id = child_name
    helper.label = helper_cfg.id
    helper.attrs["relation"] = helper_cfg.id
    ghost.label = "the ghost"

    ghost.meters["unrest"] = float(place.eerie + delay)
    child.memes["fear"] = 0.0
    child.memes["courage"] = 0.0
    child.memes["relief"] = 0.0
    helper.memes["relief"] = 0.0
    helper.memes["care"] = 0.0
    ghost.memes["trust"] = 0.0
    ghost.memes["peace"] = 0.0
    book.meters["found"] = 0.0
    book.meters["returned"] = 0.0
    herring.meters["open"] = 0.0
    room.meters["smelly"] = 0.0
    room.meters["eerie"] = 0.0

    world.facts.update(
        place=place,
        spot=spot,
        response=response,
        helper_cfg=helper_cfg,
        child=child,
        helper=helper,
        ghost=ghost,
        book=book,
        delay=delay,
    )

    introduce(world, child, helper, place)
    world.para()
    start_smell(world, child, place)
    haunting(world, child)
    helper_enters(world, child, helper, helper_cfg)

    world.para()
    choose_rhyme(world, child, helper, response)
    bright = bright_enough(response, place, delay)
    if bright:
        reveal_book(world, child, spot)
    else:
        search_longer(world, child, helper, spot)

    world.para()
    close_herring(world, helper, place)
    return_book(world, child, helper)
    peaceful_ending(world, child, helper)

    world.facts.update(
        bright=bright,
        outcome="bright" if bright else "slow",
        severity=eerie_severity(place, delay),
        revealed_directly=bright,
    )
    return world


PLACES = {
    "lighthouse": Place(
        id="lighthouse",
        label="the old lighthouse",
        opening="The round walls held the sea wind, and the stairs curled up like a shell.",
        herring_where="the little storage room under the stairs",
        afford_spots={"chest", "shelf"},
        eerie=2,
        tags={"lighthouse", "sea"},
    ),
    "harbor_inn": Place(
        id="harbor_inn",
        label="the harbor inn",
        opening="The hall was narrow, with framed ships and a rug that shivered when the door sighed.",
        herring_where="the pantry by the kitchen",
        afford_spots={"shelf", "bench"},
        eerie=1,
        tags={"inn", "sea"},
    ),
    "net_shed": Place(
        id="net_shed",
        label="the net shed by the pier",
        opening="Bundles of rope hung from beams, and the boards clicked softly whenever the tide moved below.",
        herring_where="the fish locker near the door",
        afford_spots={"bench", "chest"},
        eerie=3,
        tags={"shed", "sea"},
    ),
}

SPOTS = {
    "chest": Spot(
        id="chest",
        label="old chest",
        phrase="inside an old cedar chest",
        discover="under a folded rain cape and a spool of blue thread",
        tags={"chest"},
    ),
    "shelf": Spot(
        id="shelf",
        label="high shelf",
        phrase="on a high crooked shelf",
        discover="behind a brass compass and a sleepy moth",
        tags={"shelf"},
    ),
    "bench": Spot(
        id="bench",
        label="window bench",
        phrase="under the window bench",
        discover="beneath a striped cushion and a handful of dry shells",
        tags={"bench"},
    ),
}

RESPONSES = {
    "rhyme_question": Response(
        id="rhyme_question",
        sense=3,
        power=4,
        couplet=("Little light, soft and bright, show us what you need tonight.", "Ghost so pale by moonlit book, point the way and we will look."),
        intro="Instead of shouting, the child lifted the lantern and spoke in a careful rhyme.",
        qa_text="spoke a clear rhyming question and asked the ghost what it needed",
        tags={"rhyme", "lantern"},
    ),
    "kind_rhyme": Response(
        id="kind_rhyme",
        sense=3,
        power=3,
        couplet=("If you sigh, we will try. If you weep, we will not flee.", "Tell us true what troubles you, and we will set your spirit free."),
        intro="The child swallowed hard, then answered the whisper with a brave little rhyme.",
        qa_text="answered with a brave rhyme that invited the ghost to explain",
        tags={"rhyme", "kindness"},
    ),
    "humming": Response(
        id="humming",
        sense=2,
        power=2,
        couplet=("Hush and hum, here we come.", "Soft and slow, now we know."),
        intro="The child hummed a tiny rhyming tune, hoping the sound would make the room less scary.",
        qa_text="hummed a small rhyming tune to make the ghost less afraid",
        tags={"rhyme", "music"},
    ),
    "shout_back": Response(
        id="shout_back",
        sense=1,
        power=1,
        couplet=("Go away, ghost, do not stay!", "Leave this hall and leave us all!"),
        intro="The child barked back at the dark, making the whole hall feel harsher.",
        qa_text="shouted at the ghost",
        tags={"noise"},
    ),
}

HELPERS = {
    "mother": HelperCfg(
        id="mother",
        type="mother",
        entrance="A moment later,",
        tags={"mother"},
    ),
    "father": HelperCfg(
        id="father",
        type="father",
        entrance="A moment later,",
        tags={"father"},
    ),
    "aunt": HelperCfg(
        id="aunt",
        type="aunt",
        entrance="Soon,",
        tags={"aunt"},
    ),
    "grandfather": HelperCfg(
        id="grandfather",
        type="grandfather",
        entrance="Soon,",
        tags={"grandfather"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ivy", "Wren", "Zoe", "Ada"]
BOY_NAMES = ["Theo", "Ben", "Owen", "Finn", "Leo", "Jude", "Max", "Eli"]


@dataclass
class StoryParams:
    place: str
    spot: str
    response: str
    helper: str
    name: str
    gender: str
    delay: int = 0
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a story about a spooky spirit or a mysterious feeling in the dark. In gentle ghost stories, the scary feeling often turns into understanding by the end.",
        )
    ],
    "herring": [
        (
            "What is a herring?",
            "A herring is a kind of sea fish. When many herrings are kept in a barrel, they can smell very strong.",
        )
    ],
    "philosophy": [
        (
            "What is philosophy?",
            "Philosophy is slow thinking about big questions, like what is true or how people should act. A philosophy book is a book full of those careful thoughts.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes light in the dark so people can see where they are going. A steady light can make a scary place feel safer.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme uses words that sound alike, like bright and night. Rhymes are easy to remember, so they can feel calm and musical.",
        )
    ],
    "sea": [
        (
            "Why do old seaside buildings creak?",
            "Sea wind pushes on doors, boards, and ropes, so old seaside places often creak and tap. Those sounds can feel spooky at night even when they are ordinary things.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "herring", "philosophy", "lantern", "rhyme", "sea"]


CURATED = [
    StoryParams(
        place="harbor_inn",
        spot="shelf",
        response="rhyme_question",
        helper="mother",
        name="Mina",
        gender="girl",
        delay=0,
    ),
    StoryParams(
        place="lighthouse",
        spot="chest",
        response="kind_rhyme",
        helper="father",
        name="Theo",
        gender="boy",
        delay=1,
    ),
    StoryParams(
        place="net_shed",
        spot="bench",
        response="humming",
        helper="grandfather",
        name="Ivy",
        gender="girl",
        delay=1,
    ),
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    place = world.facts["place"]
    helper = world.facts["helper"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the words "philosophy", "horrendous", and "herring", and uses a rhyme to solve the mystery.',
        f"Tell a seaside ghost story where a child named {child.id} smells a horrendous herring odor in {place.label} and learns that a ghost wants an old philosophy book returned.",
        f"Write a ghost story with a warm ending where {child.id} and {helper.label_word} carry a lantern, speak in rhyme, and turn a scary whisper into a peaceful night.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    place = world.facts["place"]
    spot = world.facts["spot"]
    response = world.facts["response"]
    bright = world.facts["bright"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {helper.label_word}, and a sad ghost in {place.label}. The night changes because they choose to listen instead of panic.",
        ),
        (
            "What made the place feel spooky at first?",
            f"A horrendous herring smell drifted in, and then a ghostly whisper asked for its book. The smell and the whisper together made the hall feel much scarier.",
        ),
        (
            "What did the ghost want?",
            "The ghost wanted its old philosophy book put back where it belonged. It was restless because the missing book made the hall feel unfinished.",
        ),
        (
            f"How did {child.id} try to help?",
            f"{child.id} {response.qa_text}. The rhyme mattered because it made the ghost feel heard instead of chased away.",
        ),
    ]
    if bright:
        qa.append(
            (
                "How did they find the book so quickly?",
                f"The rhyme was strong enough to help the ghost point right toward {spot.phrase}. Because the ghost trusted them, the clue became clear at once.",
            )
        )
    else:
        qa.append(
            (
                "Why did it take longer to solve the problem?",
                f"The first rhyme made the room gentler, but it was not strong enough to show the hiding place right away. So {child.id} and {helper.label_word} had to search carefully by lantern light before they found the book.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"They shut the herring barrel, returned the philosophy book, and the ghost became peaceful. By the end, the same place that had felt eerie felt quiet and safe.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "herring", "philosophy", "rhyme", "sea"}
    if "lantern" in world.facts["response"].tags:
        tags.add("lantern")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
spot_allowed(P,S) :- affords(P,S).
valid(P,S) :- place(P), spot(S), spot_allowed(P,S).

sensible(R) :- response(R), sense(R,V), sense_min(M), V >= M.

severity(E + D) :- chosen_place(P), eerie(P,E), delay(D).
bright :- chosen_response(R), power(R,PR), severity(S), PR >= S.
outcome(bright) :- bright.
outcome(slow) :- not bright.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("eerie", place_id, place.eerie))
        for spot_id in sorted(place.afford_spots):
            lines.append(asp.fact("affords", place_id, spot_id))
    for spot_id in SPOTS:
        lines.append(asp.fact("spot", spot_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    return "bright" if bright_enough(RESPONSES[params.response], PLACES[params.place], params.delay) else "slow"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("(Verify failed: empty story.)")
    with io.StringIO() as buf, redirect_stdout(buf):
        emit(sample, trace=False, qa=True, header="verify-smoke")
        rendered = buf.getvalue()
    if "verify-smoke" not in rendered or "philosophy" not in sample.story or "herring" not in sample.story:
        raise StoryError("(Verify failed: smoke output missing expected content.)")


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    py_sens = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sens)} asp={sorted(asp_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue
    mismatches = 0
    for params in cases:
        try:
            if asp_outcome(params) != outcome_of(params):
                mismatches += 1
        except StoryError:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: normal generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"VERIFY SMOKE FAILURE: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle ghost-story world with rhyme, a lost philosophy book, and a horrendous herring smell."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--spot", choices=sorted(SPOTS))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra head start for the eerie unrest")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list ASP-derived valid combinations")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.spot and not valid_combo(args.place, args.spot):
        raise StoryError(explain_combo(args.place, args.spot))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.spot is None or combo[1] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, spot_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place_id,
        spot=spot_id,
        response=response_id,
        helper=helper_id,
        name=name,
        gender=gender,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.spot not in SPOTS:
        raise StoryError(f"(No story: unknown hiding spot '{params.spot}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if not valid_combo(params.place, params.spot):
        raise StoryError(explain_combo(params.place, params.spot))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown gender '{params.gender}'.)")

    world = tell(
        place=PLACES[params.place],
        spot=SPOTS[params.spot],
        response=RESPONSES[params.response],
        helper_cfg=HELPERS[params.helper],
        child_name=params.name,
        child_gender=params.gender,
        delay=params.delay,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible()
        print(f"sensible responses: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, spot) combos:\n")
        for place_id, spot_id in combos:
            print(f"  {place_id:11} {spot_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.name}: {p.place}, {p.spot}, {p.response} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
