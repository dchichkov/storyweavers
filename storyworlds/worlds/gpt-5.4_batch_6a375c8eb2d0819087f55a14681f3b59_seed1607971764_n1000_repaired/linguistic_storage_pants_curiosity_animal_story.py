#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/linguistic_storage_pants_curiosity_animal_story.py
==============================================================================

A standalone storyworld for a gentle animal story about curiosity, a storage
place, a pair of pants, and a big word: "linguistic".

Reference seed idea
-------------------
A small animal sees a label on a dress-up storage place that says
"linguistic games". The hero is curious about the word, and also wants the
special pants kept there for story circle. If the storage is low, the hero can
look safely. If it is high, the hero's curiosity leads to a risky tug that
spills word cards, and a calm grown-up helps in a safe way. The ending proves
what changed: the hero learns the word, gets the pants safely, and helps make
clear labels for the storage baskets.

Run it
------
    python storyworlds/worlds/gpt-5.4/linguistic_storage_pants_curiosity_animal_story.py
    python storyworlds/worlds/gpt-5.4/linguistic_storage_pants_curiosity_animal_story.py --storage tall_shelf
    python storyworlds/worlds/gpt-5.4/linguistic_storage_pants_curiosity_animal_story.py --response climb_boxes
    python storyworlds/worlds/gpt-5.4/linguistic_storage_pants_curiosity_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/linguistic_storage_pants_curiosity_animal_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/linguistic_storage_pants_curiosity_animal_story.py --verify
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
    portable: bool = False
    wearable: bool = False
    # physical meters / emotional memes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"owl", "mother", "mom", "aunt"}:
            table = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"badger", "father", "dad", "uncle"}:
            table = {"subject": "he", "object": "him", "possessive": "his"}
        else:
            table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]

    @property
    def label_word(self) -> str:
        return {
            "owl": "owl teacher",
            "badger": "badger parent",
            "aunt": "aunt",
            "mother": "mom",
            "father": "dad",
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
class AnimalKind:
    id: str
    species: str
    adjective: str
    move: str
    sound: str
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
class StoragePlace:
    id: str
    label: str
    phrase: str
    height: str
    capacity: int
    stable: bool
    open_verb: str
    location_line: str
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
class PantsItem:
    id: str
    label: str
    phrase: str
    bulk: int
    color_line: str
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
class LabelCard:
    id: str
    text: str
    meaning: str
    child_line: str
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
class Response:
    id: str
    sense: int
    power: int
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


def _r_wobble_spills_cards(world: World) -> list[str]:
    storage = world.get("storage")
    cards = world.get("cards")
    hero = world.get("hero")
    if storage.meters["wobble"] < THRESHOLD or cards.meters["scattered"] >= THRESHOLD:
        return []
    sig = ("spill", storage.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cards.meters["scattered"] += 1
    world.get("room").meters["mess"] += 1
    hero.memes["fear"] += 1
    hero.memes["surprise"] += 1
    return ["__scatter__"]


def _r_mess_needs_sorting(world: World) -> list[str]:
    cards = world.get("cards")
    helper = world.get("helper")
    if cards.meters["scattered"] < THRESHOLD:
        return []
    sig = ("sorting", cards.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.meters["work"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="wobble_spills_cards", tag="physical", apply=_r_wobble_spills_cards),
    Rule(name="mess_needs_sorting", tag="physical", apply=_r_mess_needs_sorting),
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


def storage_fits_pants(storage: StoragePlace, pants: PantsItem) -> bool:
    return pants.bulk <= storage.capacity


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def storage_need(storage: StoragePlace) -> int:
    return 1 if storage.height == "low" else 3


def response_works(storage: StoragePlace, response: Response) -> bool:
    return response.power >= storage_need(storage)


def outcome_of(params: "StoryParams") -> str:
    if params.storage not in STORAGES or params.response not in RESPONSES:
        return "?"
    storage = STORAGES[params.storage]
    response = RESPONSES[params.response]
    if storage.height == "low":
        return "safe_find"
    if response_works(storage, response):
        return "scatter_fix"
    return "stuck"


def predict_tug(world: World) -> dict:
    sim = world.copy()
    storage = sim.get("storage")
    if storage.attrs["height"] == "high":
        storage.meters["wobble"] += 1
        propagate(sim, narrate=False)
    return {
        "scattered": sim.get("cards").meters["scattered"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"],
    }


def introduce(world: World, hero: Entity, friend: Entity, animal: AnimalKind) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["joy"] += 1
    friend.memes["warmth"] += 1
    world.say(
        f"In the little story-room, {hero.id} the {animal.species} and {friend.id} "
        f"the {friend.type} loved dress-up time."
    )
    world.say(
        f"They {animal.move} past the cushions and puppet stage until they reached "
        f"the storage corner."
    )


def show_storage(world: World, storage: StoragePlace, pants: PantsItem, label: LabelCard) -> None:
    world.say(
        f"There stood {storage.phrase}, and on the front was a neat card that said "
        f'"{label.text}." {storage.location_line}'
    )
    world.say(
        f"Inside were {pants.phrase}. {pants.color_line}"
    )


def curiosity_beat(world: World, hero: Entity, label: LabelCard, pants: PantsItem) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'{hero.id} tipped {hero.pronoun("possessive")} head. '
        f'"I know the word storage, and I know the word pants," '
        f'{hero.pronoun()} said. "But what does linguistic mean?"'
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to wear the {pants.label} for story circle, "
        f"and now {hero.pronoun('possessive')} curiosity tugged just as hard as "
        f"{hero.pronoun('possessive')} wish to dress up."
    )


def warn(world: World, hero: Entity, friend: Entity, helper: Entity, storage: StoragePlace) -> None:
    pred = predict_tug(world)
    world.facts["predicted_scatter"] = bool(pred["scattered"])
    if storage.height == "low":
        world.say(
            f'{friend.id} smiled. "Let\'s open it together and ask {helper.id} about the big word after," '
            f'{friend.pronoun()} said.'
        )
        return
    friend.memes["caution"] += 1
    world.say(
        f'{friend.id} looked up at the high shelf and twitched {friend.pronoun("possessive")} whiskers. '
        f'"Please do not tug it," {friend.pronoun()} said. "If it wobbles, the cards could fall, '
        f'and then we would have a mess before story circle."'
    )


def safe_peek(world: World, hero: Entity, friend: Entity, storage: StoragePlace) -> None:
    storage_ent = world.get("storage")
    storage_ent.meters["opened"] += 1
    hero.memes["relief"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"Because the {storage.label} was low, {hero.id} and {friend.id} could {storage.open_verb} "
        f"without climbing at all."
    )
    world.say(
        f"They peeped inside together, and nothing tipped or scraped."
    )


def tug_and_spill(world: World, hero: Entity, friend: Entity, storage: StoragePlace) -> None:
    storage_ent = world.get("storage")
    storage_ent.meters["wobble"] += 1
    hero.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But curiosity got there first. {hero.id} rose on tiptoe and gave the "
        f"{storage.label} a little tug."
    )
    world.say(
        f"The shelf gave a small wobble. A flat box slipped, popped open, and bright word cards "
        f"fluttered down like startled leaves."
    )
    if world.get("cards").meters["scattered"] >= THRESHOLD:
        world.say(
            f'{hero.id} jumped back. "{friend.id}, I made a mess," {hero.pronoun()} whispered.'
        )


def helper_arrives(world: World, helper: Entity, response: Response, storage: StoragePlace,
                   label: LabelCard, pants: PantsItem) -> None:
    storage_ent = world.get("storage")
    cards = world.get("cards")
    pants_ent = world.get("pants")
    storage_ent.meters["opened"] += 1
    storage_ent.meters["wobble"] = 0.0
    pants_ent.meters["found"] += 1
    pants_ent.meters["worn"] += 1
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["relief"] += 1
    hero.memes["learning"] += 1
    hero.memes["fear"] = 0.0
    friend.memes["relief"] += 1
    helper.memes["care"] += 1
    if cards.meters["scattered"] >= THRESHOLD:
        cards.meters["sorted"] += 1
        cards.meters["scattered"] = 0.0
    world.say(
        f"{helper.id} came over at once and {response.text}."
    )
    world.say(
        f'"Linguistic is a word about language and words," {helper.pronoun()} explained. '
        f'"These are our linguistic games because they help us listen, rhyme, and tell stories."'
    )
    world.say(
        f"Then {helper.pronoun()} lifted out the {pants.label} and handed them to {hero.id}."
    )


def low_helper_explains(world: World, helper: Entity, label: LabelCard, pants: PantsItem) -> None:
    pants_ent = world.get("pants")
    pants_ent.meters["found"] += 1
    pants_ent.meters["worn"] += 1
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["learning"] += 1
    hero.memes["wonder"] += 1
    friend.memes["joy"] += 1
    world.say(
        f'{helper.id} heard the question and knelt beside them. "{label.child_line}" '
        f'{helper.pronoun()} said.'
    )
    world.say(
        f"With a gentle smile, {helper.pronoun()} helped {hero.id} into the {pants.label}."
    )


def repair_and_end(world: World, hero: Entity, friend: Entity, helper: Entity, label: LabelCard,
                   storage: StoragePlace) -> None:
    hero.memes["joy"] += 1
    hero.memes["care"] += 1
    friend.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After that, the three of them sorted the cards back into the storage baskets."
    )
    world.say(
        f"{helper.id} drew a tiny mouth, an ear, and a book on a fresh label under the word "
        f'"{label.text}," so even one quick glance could explain it.'
    )
    world.say(
        f"Soon {hero.id} was swishing about in the {world.get('pants').label}, "
        f"and when {hero.pronoun()} passed the {storage.label} again, "
        f"{hero.pronoun()} smiled instead of tugging. Curiosity still shone in "
        f"{hero.pronoun('possessive')} eyes, but now it walked beside patience."
    )


def tell(animal: AnimalKind, friend_kind: AnimalKind, helper_kind: AnimalKind,
         storage: StoragePlace, pants: PantsItem, label: LabelCard, response: Response,
         hero_name: str = "Pip", friend_name: str = "Moss", helper_name: str = "Tala") -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name, kind="character", type=animal.species, label=animal.species,
        role="hero", traits=[animal.adjective, "curious"], attrs={}
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_kind.species, label=friend_kind.species,
        role="friend", traits=["steady"], attrs={}
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_kind.species, label=helper_kind.species,
        role="helper", traits=["calm"], attrs={}
    ))
    world.add(Entity(id="room", type="room", label="story-room", attrs={}))
    world.add(Entity(
        id="storage", type="storage", label=storage.label,
        attrs={"height": storage.height, "stable": storage.stable}
    ))
    world.add(Entity(
        id="cards", type="cards", label="word cards", portable=True,
        attrs={"topic": label.text}
    ))
    world.add(Entity(
        id="pants", type="pants", label=pants.label, portable=True, wearable=True,
        attrs={"bulk": pants.bulk}
    ))

    world.facts.update(
        animal=animal,
        friend_kind=friend_kind,
        helper_kind=helper_kind,
        storage_cfg=storage,
        pants_cfg=pants,
        label_cfg=label,
        response=response,
    )

    introduce(world, hero, friend, animal)
    show_storage(world, storage, pants, label)
    world.para()
    curiosity_beat(world, hero, label, pants)
    warn(world, hero, friend, helper, storage)

    if storage.height == "low":
        safe_peek(world, hero, friend, storage)
        world.para()
        low_helper_explains(world, helper, label, pants)
        outcome = "safe_find"
    else:
        world.para()
        tug_and_spill(world, hero, friend, storage)
        world.para()
        helper_arrives(world, helper, response, storage, label, pants)
        outcome = "scatter_fix"

    world.para()
    repair_and_end(world, hero, friend, helper, label, storage)

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        outcome=outcome,
        cards_scattered=world.get("cards").meters["sorted"] >= THRESHOLD or world.get("room").meters["mess"] >= THRESHOLD,
        learned=hero.memes["learning"] >= THRESHOLD,
        wore_pants=world.get("pants").meters["worn"] >= THRESHOLD,
    )
    return world


ANIMALS = {
    "mouse": AnimalKind(
        id="mouse", species="mouse", adjective="quick", move="scampered",
        sound="squeaked", tags={"mouse"}
    ),
    "rabbit": AnimalKind(
        id="rabbit", species="rabbit", adjective="soft-footed", move="hopped",
        sound="whispered", tags={"rabbit"}
    ),
    "squirrel": AnimalKind(
        id="squirrel", species="squirrel", adjective="bright-eyed", move="skittered",
        sound="chattered", tags={"squirrel"}
    ),
}

STORAGES = {
    "low_cubby": StoragePlace(
        id="low_cubby",
        label="cubby",
        phrase="a low wooden storage cubby",
        height="low",
        capacity=2,
        stable=True,
        open_verb="open the cubby door",
        location_line="It sat close to the rug, right where little paws could reach.",
        tags={"storage", "cubby"},
    ),
    "basket_shelf": StoragePlace(
        id="basket_shelf",
        label="basket shelf",
        phrase="a tall storage shelf full of labeled baskets",
        height="high",
        capacity=2,
        stable=True,
        open_verb="pull down the basket",
        location_line="The top basket rested far above nose level.",
        tags={"storage", "shelf"},
    ),
    "tall_shelf": StoragePlace(
        id="tall_shelf",
        label="tall shelf",
        phrase="a tall blue storage shelf with narrow steps drawn on the side",
        height="high",
        capacity=3,
        stable=True,
        open_verb="reach the upper box",
        location_line="The highest box sat above the puppet stage, high and tidy.",
        tags={"storage", "shelf"},
    ),
}

PANTS = {
    "rain_pants": PantsItem(
        id="rain_pants",
        label="yellow rain pants",
        phrase="a folded pair of yellow rain pants",
        bulk=2,
        color_line="Their bright cuffs looked like two little strips of sunshine.",
        tags={"pants", "rain_pants"},
    ),
    "patch_pants": PantsItem(
        id="patch_pants",
        label="patchwork pants",
        phrase="a folded pair of patchwork pants",
        bulk=1,
        color_line="One knee had a blue patch and the other had a red one.",
        tags={"pants", "patch_pants"},
    ),
    "snow_pants": PantsItem(
        id="snow_pants",
        label="puffy snow pants",
        phrase="a folded pair of puffy snow pants",
        bulk=3,
        color_line="They were soft and puffy, with shiny silver snaps.",
        tags={"pants", "snow_pants"},
    ),
}

LABELS = {
    "linguistic_games": LabelCard(
        id="linguistic_games",
        text="linguistic games",
        meaning="games about words and language",
        child_line='That card says "linguistic games." Linguistic is a big word for things about words, sounds, and language.',
        tags={"linguistic", "words"},
    ),
    "linguistic_corner": LabelCard(
        id="linguistic_corner",
        text="linguistic corner",
        meaning="the corner for word play and language play",
        child_line='Linguistic means about language. This is the corner where we play with story words, rhymes, and sounds.',
        tags={"linguistic", "words"},
    ),
    "linguistic_cards": LabelCard(
        id="linguistic_cards",
        text="linguistic cards",
        meaning="cards used for language and story play",
        child_line='Those are linguistic cards, which means they are cards for word play and language play.',
        tags={"linguistic", "cards"},
    ),
}

RESPONSES = {
    "stool": Response(
        id="stool",
        sense=3,
        power=3,
        text="brought over the little step stool, reached the high basket safely, and set it on the rug",
        qa_text="used the little step stool to bring the basket down safely",
        tags={"stool", "safety"},
    ),
    "lift_down": Response(
        id="lift_down",
        sense=4,
        power=4,
        text="stood tall, lifted the basket down with both paws, and opened it where everyone could see",
        qa_text="lifted the basket down and opened it safely on the rug",
        tags={"lift_down", "safety"},
    ),
    "ladder": Response(
        id="ladder",
        sense=3,
        power=4,
        text="opened the short library ladder, climbed two careful steps, and brought the basket down",
        qa_text="used the little library ladder to bring the basket down safely",
        tags={"ladder", "safety"},
    ),
    "climb_boxes": Response(
        id="climb_boxes",
        sense=1,
        power=1,
        text="stacked loose boxes and tried to reach from there",
        qa_text="stacked loose boxes and tried to reach from them",
        tags={"unsafe"},
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for sid, storage in STORAGES.items():
        for pid, pants in PANTS.items():
            if storage_fits_pants(storage, pants):
                combos.append((sid, pid))
    return combos


@dataclass
class StoryParams:
    animal: str
    friend_animal: str
    helper_animal: str
    storage: str
    pants: str
    label: str
    response: str
    hero_name: str
    friend_name: str
    helper_name: str
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
    "linguistic": [
        (
            "What does linguistic mean?",
            "Linguistic means about language, words, and sounds. It is a big word people use when they are talking about speaking, listening, and stories.",
        )
    ],
    "storage": [
        (
            "What is storage?",
            "Storage is a place where things are kept so they stay tidy and easy to find later. Shelves, baskets, boxes, and cubbies can all be storage.",
        )
    ],
    "pants": [
        (
            "What are pants?",
            "Pants are clothes you wear on your legs. They help keep your body covered, and some kinds help keep you warm or dry too.",
        )
    ],
    "stool": [
        (
            "Why is a step stool safer than climbing loose boxes?",
            "A step stool is made to stand on, so it stays steadier than loose boxes. That makes it safer when a grown-up needs to reach something high.",
        )
    ],
    "ladder": [
        (
            "What is a ladder for?",
            "A ladder helps someone reach up high by climbing stable steps. A grown-up should make sure it is safe before using it.",
        )
    ],
    "cards": [
        (
            "Why do labels help in a room?",
            "Labels help everyone know where things belong. A good label makes it faster and easier to put things away and find them again.",
        )
    ],
}
KNOWLEDGE_ORDER = ["linguistic", "storage", "pants", "stool", "ladder", "cards"]

GIRLISH_NAMES = ["Pip", "Mimi", "Tansy", "Nell", "Poppy", "Fern"]
BOYISH_NAMES = ["Moss", "Bram", "Otis", "Nico", "Ash", "Tobin"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    storage = f["storage_cfg"]
    pants = f["pants_cfg"]
    label = f["label_cfg"]
    outcome = f["outcome"]
    prompts = [
        f'Write an animal story for a 3-to-5-year-old that includes the words "linguistic," "storage," and "pants."',
        f"Tell a gentle story where a curious {hero.type} wonders what the word "
        f'"{label.text}" means while looking at a {storage.label} that holds {pants.label}.',
    ]
    if outcome == "safe_find":
        prompts.append(
            "Write a cozy story where curiosity leads to a question, a calm explanation, "
            "and a tidy, happy ending."
        )
    else:
        prompts.append(
            "Write a story where a child's curiosity causes a small mess, then a calm grown-up "
            "solves the problem safely and teaches the word."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    storage = f["storage_cfg"]
    pants = f["pants_cfg"]
    label = f["label_cfg"]
    outcome = f["outcome"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, {friend.id}, and {helper.id}. "
            f"They were together in the story-room near the storage corner.",
        ),
        (
            f"Why was {hero.id} curious?",
            f"{hero.id} saw the card that said \"{label.text}\" and wanted to know what the big word meant. "
            f"{hero.pronoun().capitalize()} also wanted the {pants.label}, so the label and the pants pulled "
            f"at {hero.pronoun('possessive')} curiosity at the same time.",
        ),
        (
            f"What was in the storage place?",
            f"There were {pants.phrase} inside. The special pants made the storage place feel important to {hero.id}.",
        ),
    ]
    if outcome == "safe_find":
        items.append(
            (
                f"Why did nothing fall when {hero.id} looked inside?",
                f"Nothing fell because the {storage.label} was low enough to open safely from the floor. "
                f"There was no need to tug or climb, so the cards stayed tidy.",
            )
        )
    else:
        items.append(
            (
                f"What happened when {hero.id} tugged the shelf?",
                f"The shelf wobbled and a box of word cards popped open, so the cards scattered onto the rug. "
                f"That happened because the basket was high and curiosity made {hero.id} pull before waiting for help.",
            )
        )
        items.append(
            (
                f"How did {helper.id} fix the problem?",
                f"{helper.id} {f['response'].qa_text}. Then {helper.pronoun()} explained that linguistic means "
                f"something about language and words, so {hero.id} learned the answer and got the pants safely too.",
            )
        )
    items.append(
        (
            "How did the story end?",
            f"It ended with the cards sorted back into storage and {hero.id} wearing the {pants.label}. "
            f"The ending shows that curiosity was still bright, but now it was guided by patience and help.",
        )
    )
    return items


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"linguistic", "storage", "pants", "cards"}
    response = f["response"]
    if response.id in {"stool", "ladder"}:
        tags.add(response.id)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v is False}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="rabbit",
        friend_animal="mouse",
        helper_animal="owl",
        storage="low_cubby",
        pants="patch_pants",
        label="linguistic_games",
        response="stool",
        hero_name="Poppy",
        friend_name="Moss",
        helper_name="Teacher Wren",
    ),
    StoryParams(
        animal="mouse",
        friend_animal="rabbit",
        helper_animal="owl",
        storage="basket_shelf",
        pants="rain_pants",
        label="linguistic_corner",
        response="stool",
        hero_name="Pip",
        friend_name="Fern",
        helper_name="Teacher Wren",
    ),
    StoryParams(
        animal="squirrel",
        friend_animal="mouse",
        helper_animal="badger",
        storage="tall_shelf",
        pants="patch_pants",
        label="linguistic_cards",
        response="lift_down",
        hero_name="Nico",
        friend_name="Tansy",
        helper_name="Uncle Bramble",
    ),
    StoryParams(
        animal="rabbit",
        friend_animal="squirrel",
        helper_animal="owl",
        storage="tall_shelf",
        pants="rain_pants",
        label="linguistic_games",
        response="ladder",
        hero_name="Mimi",
        friend_name="Ash",
        helper_name="Teacher Wren",
    ),
]


def explain_rejection(storage: StoragePlace, pants: PantsItem) -> str:
    return (
        f"(No story: {pants.label} are too bulky for the {storage.label}. "
        f"The storage place would not honestly hold them, so try a larger storage choice.)"
    )


def explain_response(response_id: str, storage_id: str) -> str:
    response = RESPONSES[response_id]
    storage = STORAGES[storage_id]
    if response.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_responses()))
        return (
            f"(Refusing response '{response_id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    if not response_works(storage, response):
        return (
            f"(No story: the response '{response_id}' is too weak for the {storage.label}. "
            f"Pick a response that can safely reach high storage.)"
        )
    return "(No story: unreasonable response.)"


ASP_RULES = r"""
% --- fit gate ---------------------------------------------------------------
fits(S, P) :- storage(S), pants(P), capacity(S, C), bulk(P, B), B <= C.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, P) :- fits(S, P).

need(S, 1) :- height(S, low).
need(S, 3) :- height(S, high).
works(S, R) :- need(S, N), power(R, P), P >= N.

outcome(safe_find) :- chosen_storage(S), height(S, low).
outcome(scatter_fix) :- chosen_storage(S), height(S, high), chosen_response(R), works(S, R).
outcome(stuck) :- chosen_storage(S), height(S, high), chosen_response(R), not works(S, R).

#show valid/2.
#show sensible/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, storage in STORAGES.items():
        lines.append(asp.fact("storage", sid))
        lines.append(asp.fact("capacity", sid, storage.capacity))
        lines.append(asp.fact("height", sid, storage.height))
    for pid, pants in PANTS.items():
        lines.append(asp.fact("pants", pid))
        lines.append(asp.fact("bulk", pid, pants.bulk))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_storage", params.storage),
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld: curiosity, a storage place, a big word, and a pair of pants."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--friend-animal", choices=ANIMALS)
    ap.add_argument("--helper-animal", choices=ANIMALS)
    ap.add_argument("--storage", choices=STORAGES)
    ap.add_argument("--pants", choices=PANTS)
    ap.add_argument("--label", choices=LABELS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> str:
    pool = [n for n in GIRLISH_NAMES + BOYISH_NAMES if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.storage and args.pants:
        storage = STORAGES[args.storage]
        pants = PANTS[args.pants]
        if not storage_fits_pants(storage, pants):
            raise StoryError(explain_rejection(storage, pants))
    if args.response:
        storage_id = args.storage if args.storage else "tall_shelf"
        if storage_id not in STORAGES:
            raise StoryError("(No story: unknown storage choice.)")
        if RESPONSES[args.response].sense < SENSE_MIN:
            raise StoryError(explain_response(args.response, storage_id))
        if args.storage and STORAGES[args.storage].height == "high" and not response_works(STORAGES[args.storage], RESPONSES[args.response]):
            raise StoryError(explain_response(args.response, args.storage))

    combos = [
        combo for combo in valid_combos()
        if (args.storage is None or combo[0] == args.storage)
        and (args.pants is None or combo[1] == args.pants)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    storage_id, pants_id = rng.choice(sorted(combos))
    storage = STORAGES[storage_id]

    response_choices = [
        rid for rid, response in RESPONSES.items()
        if response.sense >= SENSE_MIN and (storage.height == "low" or response_works(storage, response))
    ]
    if args.response is not None:
        if args.response not in response_choices:
            raise StoryError(explain_response(args.response, storage_id))
        response_id = args.response
    else:
        response_id = rng.choice(sorted(response_choices))

    animal_id = args.animal or rng.choice(sorted(ANIMALS))
    friend_choices = [k for k in sorted(ANIMALS) if k != animal_id] or [animal_id]
    friend_id = args.friend_animal or rng.choice(friend_choices)
    helper_id = args.helper_animal or rng.choice(sorted({"owl", "badger"} & set(ANIMALS.keys())) or sorted(ANIMALS))
    label_id = args.label or rng.choice(sorted(LABELS))
    hero_name = args.hero_name or _pick_name(rng)
    friend_name = args.friend_name or _pick_name(rng, avoid=hero_name)
    helper_name = args.helper_name or ("Teacher Wren" if helper_id == "owl" else "Uncle Bramble")

    return StoryParams(
        animal=animal_id,
        friend_animal=friend_id,
        helper_animal=helper_id,
        storage=storage_id,
        pants=pants_id,
        label=label_id,
        response=response_id,
        hero_name=hero_name,
        friend_name=friend_name,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    required = {
        "animal": ANIMALS,
        "friend_animal": ANIMALS,
        "helper_animal": ANIMALS,
        "storage": STORAGES,
        "pants": PANTS,
        "label": LABELS,
        "response": RESPONSES,
    }
    for field_name, registry in required.items():
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(No story: unknown {field_name.replace('_', ' ')} '{value}'.)")
    storage = STORAGES[params.storage]
    pants = PANTS[params.pants]
    response = RESPONSES[params.response]
    if not storage_fits_pants(storage, pants):
        raise StoryError(explain_rejection(storage, pants))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response, params.storage))
    if storage.height == "high" and not response_works(storage, response):
        raise StoryError(explain_response(params.response, params.storage))

    world = tell(
        animal=ANIMALS[params.animal],
        friend_kind=ANIMALS[params.friend_animal],
        helper_kind=ANIMALS[params.helper_animal],
        storage=storage,
        pants=pants,
        label=LABELS[params.label],
        response=response,
        hero_name=params.hero_name,
        friend_name=params.friend_name,
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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params failed unexpectedly for seed {seed}.")
            break
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
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
        sensible = asp_sensible()
        print(f"sensible responses: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (storage, pants) combos:\n")
        for storage, pants in combos:
            print(f"  {storage:12} {pants}")
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
            header = f"### {p.hero_name}: {p.storage} / {p.pants} / {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
