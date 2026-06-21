#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/priest_humor_sharing_inner_monologue_nursery_rhyme.py
================================================================================

A standalone story world for a tiny nursery-rhyme-like domain:

    a child has a little treat,
    a tired priest comes by,
    the child argues inside their own head about whether to share,
    a silly joke loosens the knot,
    and the ending shows what changed.

The world is deliberately small and constraint-checked. A story is only made
when the chosen food and sharing method make ordinary sense:

* ``split`` is only valid for foods that can reasonably be divided.
* ``offer_piece`` is only valid when there are at least two pieces.
* ``offer_whole`` is always physically possible, but some endings may still be
  ungenerous if the child is especially clingy and no joke softens them enough.

The simulation tracks both physical meters (pieces left, hunger eased, crumbs,
jam smears) and emotional memes (greed, generosity, worry, relief, laughter).
The rendered story is driven by those states and by the recorded screenplay
beats rather than by slot-filling a single paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/priest_humor_sharing_inner_monologue_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/priest_humor_sharing_inner_monologue_nursery_rhyme.py --food loaf --share split
    python storyworlds/worlds/gpt-5.4/priest_humor_sharing_inner_monologue_nursery_rhyme.py --food pear --share split
    python storyworlds/worlds/gpt-5.4/priest_humor_sharing_inner_monologue_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/priest_humor_sharing_inner_monologue_nursery_rhyme.py --verify
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
    divisible: bool = False
    shareable_pieces: int = 1
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "nun"}
        male = {"boy", "man", "father", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    scene: str
    rhyme: str
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
class Food:
    id: str
    label: str
    phrase: str
    plural_phrase: str
    crumb_word: str
    sticky_word: str
    divisible: bool
    pieces: int
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
class ShareMove:
    id: str
    label: str
    needs_divisible: bool = False
    needs_many_pieces: bool = False
    give_amount: int = 1
    sense: int = 3
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
class Joke:
    id: str
    line: str
    image: str
    boost: int
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
class ChildKind:
    id: str
    type: str
    name_pool: list[str]
    title: str
    clutch_word: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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

    def note(self, event: str) -> None:
        self.history.append(event)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
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


def _r_empty_hands(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    treat = world.get("treat")
    if treat.meters["pieces_left"] > 0:
        return out
    sig = ("empty_hands",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["surprise"] += 1
    out.append("__empty__")
    return out


def _r_shared_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    priest = world.get("priest")
    if priest.meters["portion_received"] < THRESHOLD:
        return out
    sig = ("shared_relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    priest.meters["hunger"] = max(0.0, priest.meters["hunger"] - 1.0)
    child.memes["worry"] = 0.0
    child.memes["generosity"] += 1
    child.memes["relief"] += 1
    priest.memes["gratitude"] += 1
    out.append("__relief__")
    return out


def _r_jam_laugh(world: World) -> list[str]:
    out: list[str] = []
    priest = world.get("priest")
    child = world.get("child")
    treat = world.get("treat")
    if world.facts.get("joke_kind") != "jam_nose":
        return out
    if priest.meters["jam_on_nose"] < THRESHOLD:
        return out
    sig = ("jam_laugh",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["laughter"] += 1
    priest.memes["laughter"] += 1
    treat.meters["sticky"] += 1
    out.append("__laugh__")
    return out


CAUSAL_RULES = [
    Rule(name="empty_hands", tag="physical", apply=_r_empty_hands),
    Rule(name="shared_relief", tag="social", apply=_r_shared_relief),
    Rule(name="jam_laugh", tag="humor", apply=_r_jam_laugh),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_share(food: Food, share: ShareMove) -> bool:
    if share.needs_divisible and not food.divisible:
        return False
    if share.needs_many_pieces and food.pieces < 2:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for child_id in CHILDREN:
            for food_id, food in FOODS.items():
                for share_id, share in SHARES.items():
                    if valid_share(food, share):
                        combos.append((place_id, child_id, food_id, share_id))
    return combos


def decision_score(greed: int, shyness: int, joke_boost: int, share: ShareMove) -> int:
    return joke_boost + share.sense - greed - shyness


def would_share(greed: int, shyness: int, joke: Joke, share: ShareMove) -> bool:
    return decision_score(greed, shyness, joke.boost, share) >= 1


def predict_sharing(food: Food, share: ShareMove, greed: int, shyness: int, joke: Joke) -> dict:
    return {
        "valid": valid_share(food, share),
        "score": decision_score(greed, shyness, joke.boost, share),
        "will_share": would_share(greed, shyness, joke, share),
    }


def introduce(world: World, place: Place, child: Entity, treat: Entity, food: Food) -> None:
    child.memes["delight"] += 1
    world.say(
        f"In {place.label}, where {place.scene}, {child.id} came {place.rhyme}, "
        f"with {food.phrase} in {child.pronoun('possessive')} hand."
    )
    world.say(
        f"{child.id} skipped a little, sniffed the sweet air, and thought the treat "
        f"looked fine enough for a song."
    )
    world.note("setup_child_with_treat")


def priest_arrives(world: World, priest: Entity, place: Place) -> None:
    priest.meters["hunger"] = 1.0
    world.say(
        f"Along the path came a priest in black, with a kind round face and a careful step. "
        f"He had walked a long way through {place.label}, and his tummy gave a tiny grumble."
    )
    world.note("priest_arrives_hungry")


def inner_monologue(world: World, child: Entity, food: Food, priest: Entity, share: ShareMove, joke: Joke) -> None:
    child.memes["worry"] += 1
    world.facts["predicted"] = predict_sharing(
        FOODS[world.facts["food_id"]],
        SHARES[world.facts["share_id"]],
        int(child.memes["greed"]),
        int(child.memes["shyness"]),
        joke,
    )
    world.say(
        f'Inside {child.id}\'s head came a whispery rhyme: '
        f'"If I keep it all, it will taste so sweet... but {priest.label_word} looks tired, '
        f'and kindness walks on little feet."'
    )
    if share.id == "split":
        world.say(
            f'{child.id} peeped at {food.label} and thought, '
            f'"A half for him and a half for me? That sounds as fair as fair can be... maybe."'
        )
    elif share.id == "offer_piece":
        world.say(
            f'{child.id} counted softly inside: '
            f'"One for him and some for me. That would still leave plenty in the tree of my hand."'
        )
    else:
        world.say(
            f'{child.id} gulped and thought, '
            f'"The whole thing? Oh! That is grand and hard. My fingers hug it like a guard."'
        )
    world.note("inner_monologue")


def priest_jokes(world: World, priest: Entity, joke: Joke) -> None:
    world.facts["joke_kind"] = joke.id
    priest.memes["warmth"] += 1
    world.say(
        f'The priest smiled and said, "{joke.line}"'
    )
    world.say(joke.image)
    if joke.id == "jam_nose":
        priest.meters["jam_on_nose"] += 1
        propagate(world, narrate=False)
    else:
        child = world.get("child")
        child.memes["laughter"] += 1
        priest.memes["laughter"] += 1
    world.note("priest_jokes")


def choose_share(world: World, child: Entity, priest: Entity, treat: Entity, food: Food, share: ShareMove, joke: Joke) -> bool:
    if not would_share(int(child.memes["greed"]), int(child.memes["shyness"]), joke, share):
        child.memes["greed"] += 1
        child.memes["regret"] += 1
        world.say(
            f"{child.id} tucked {child.pronoun('possessive')} elbow in tight. "
            f'"Oh... perhaps not today," {child.pronoun()} said, though the words came out small.'
        )
        world.note("child_keeps_treat")
        return False

    give = share.give_amount
    treat.meters["pieces_left"] = max(0.0, treat.meters["pieces_left"] - give)
    priest.meters["portion_received"] += float(give)
    child.meters["shared_amount"] += float(give)
    if share.id == "split":
        world.say(
            f"So {child.id} broke the {food.label} right down the middle and held out the warmer half to the priest."
        )
    elif share.id == "offer_piece":
        piece_word = "piece" if give == 1 else "pieces"
        world.say(
            f"So {child.id} lifted one {piece_word} from {food.plural_phrase} and placed it in the priest's hand."
        )
    else:
        world.say(
            f"So {child.id} took a brave breath and offered the whole {food.label} to the priest."
        )
    propagate(world, narrate=False)
    world.note("child_shares")
    return True


def priest_receives(world: World, priest: Entity, child: Entity, food: Food, share: ShareMove) -> None:
    if priest.meters["portion_received"] < THRESHOLD:
        return
    if share.id == "offer_whole":
        world.say(
            f'The priest bowed his head and said, "That is a generous gift, and bigger than my own request."'
        )
    else:
        world.say(
            f'The priest took the bite with a smile and said, "A shared little supper can cheer a long road."'
        )
    if world.facts.get("joke_kind") == "jam_nose":
        world.say(
            f"A shiny spot of {food.sticky_word} still sat on his nose, and that made the thanks sound even funnier."
        )
    world.note("priest_receives")


def priest_shares_back(world: World, priest: Entity, child: Entity, place: Place, food: Food) -> None:
    if priest.meters["portion_received"] < THRESHOLD:
        return
    child.memes["belonging"] += 1
    child.memes["joy"] += 1
    priest.memes["kindness"] += 1
    world.say(
        f'Then the priest shared back a bouncing blessing: '
        f'"Crumb by crumb and cheer by cheer, the happiest mouths make room for dear."'
    )
    if child.memes["laughter"] >= THRESHOLD:
        world.say(
            f"{child.id} laughed so hard that a few {food.crumb_word} hopped onto the path like tiny dancing boots."
        )
        world.get("treat").meters["crumbs"] += 1
    world.note("priest_shares_rhyme")


def gentle_end_keep(world: World, child: Entity, priest: Entity, place: Place, food: Food) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"The priest only nodded. He asked for nothing more, and he walked on softly through {place.label}."
    )
    world.say(
        f"{child.id} ate in quiet nibbles, but the {food.label} did not taste quite as bright as before. "
        f"Inside came another little thought: kindness, once hidden, can make a full hand feel small."
    )
    world.say(
        f"So next time {child.pronoun()} would make a kinder start, and that promise sat warm in {child.pronoun('possessive')} heart."
    )
    world.note("ending_regret")


def happy_end(world: World, child: Entity, priest: Entity, place: Place, food: Food, share: ShareMove) -> None:
    child.memes["lesson"] += 1
    if share.id == "offer_whole":
        world.say(
            f"But the priest broke the gift again and gave part back, so neither hand stayed empty for long."
        )
        world.get("treat").meters["pieces_left"] += 1
        child.meters["shared_amount"] = max(1.0, child.meters["shared_amount"])
        child.memes["surprise"] += 1
    world.say(
        f"Together they stood in {place.label}, nibbling and chuckling, while the afternoon felt round and mild."
    )
    world.say(
        f"And {child.id} learned a nursery-truth worth keeping: when a little treat is shared, it somehow grows big enough for two smiles."
    )
    world.note("ending_happy")


def tell(
    place: Place,
    child_kind: ChildKind,
    food: Food,
    share: ShareMove,
    joke: Joke,
    *,
    child_name: str = "Molly",
    greed: int = 2,
    shyness: int = 1,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_kind.type,
            label=child_name,
            role="child",
            traits=[child_kind.title],
            attrs={"clutch_word": child_kind.clutch_word},
        )
    )
    priest = world.add(
        Entity(
            id="Father Reed",
            kind="character",
            type="priest",
            label="the priest",
            role="priest",
            traits=["gentle", "funny"],
            attrs={},
        )
    )
    treat = world.add(
        Entity(
            id="treat",
            kind="thing",
            type="food",
            label=food.label,
            role="treat",
            divisible=food.divisible,
            shareable_pieces=food.pieces,
            attrs={},
        )
    )
    child.memes["greed"] = float(greed)
    child.memes["shyness"] = float(shyness)
    child.memes["worry"] = 0.0
    child.memes["laughter"] = 0.0
    treat.meters["pieces_left"] = float(food.pieces)
    treat.meters["crumbs"] = 0.0
    treat.meters["sticky"] = 0.0
    priest.meters["portion_received"] = 0.0
    priest.meters["jam_on_nose"] = 0.0
    priest.meters["hunger"] = 0.0
    world.facts.update(
        place=place,
        child=child,
        priest=priest,
        food_cfg=food,
        share_cfg=share,
        joke_cfg=joke,
        food_id=food.id,
        share_id=share.id,
        child_kind=child_kind,
        greed=greed,
        shyness=shyness,
        predicted={},
    )

    introduce(world, place, child, treat, food)
    priest_arrives(world, priest, place)

    world.para()
    inner_monologue(world, child, food, priest, share, joke)
    priest_jokes(world, priest, joke)

    world.para()
    shared = choose_share(world, child, priest, treat, food, share, joke)
    if shared:
        priest_receives(world, priest, child, food, share)
        priest_shares_back(world, priest, child, place, food)
        happy_end(world, child, priest, place, food, share)
        outcome = "shared"
    else:
        gentle_end_keep(world, child, priest, place, food)
        outcome = "kept"

    world.facts.update(
        outcome=outcome,
        shared=shared,
        pieces_left=int(world.get("treat").meters["pieces_left"]),
        jam_nose=world.get("priest").meters["jam_on_nose"] >= THRESHOLD,
    )
    return world


PLACES = {
    "churchyard": Place(
        id="churchyard",
        label="the churchyard",
        scene="the bell flowers nodded by the stones",
        rhyme="trip-tap, trip-tap",
        tags={"churchyard"},
    ),
    "lane": Place(
        id="lane",
        label="the village lane",
        scene="the hedges hummed with bees",
        rhyme="skip-skip, clap-clip",
        tags={"lane"},
    ),
    "green": Place(
        id="green",
        label="the little village green",
        scene="the grass looked brushed and bright",
        rhyme="hop-hip, merry-slip",
        tags={"green"},
    ),
}

FOODS = {
    "bun": Food(
        id="bun",
        label="bun",
        phrase="a currant bun",
        plural_phrase="little bun pieces",
        crumb_word="bun crumbs",
        sticky_word="jam",
        divisible=True,
        pieces=2,
        tags={"bun", "sharing"},
    ),
    "loaf": Food(
        id="loaf",
        label="little loaf",
        phrase="a little honey loaf",
        plural_phrase="soft loaf pieces",
        crumb_word="loaf crumbs",
        sticky_word="honey",
        divisible=True,
        pieces=2,
        tags={"bread", "sharing"},
    ),
    "pear": Food(
        id="pear",
        label="pear",
        phrase="a ripe green pear",
        plural_phrase="pear slices",
        crumb_word="pear bits",
        sticky_word="pear juice",
        divisible=True,
        pieces=2,
        tags={"pear", "fruit"},
    ),
    "berries": Food(
        id="berries",
        label="berries",
        phrase="three sugared berries",
        plural_phrase="berries",
        crumb_word="sugar specks",
        sticky_word="berry juice",
        divisible=False,
        pieces=3,
        tags={"berries", "fruit"},
    ),
}

SHARES = {
    "split": ShareMove(
        id="split",
        label="split it in half",
        needs_divisible=True,
        needs_many_pieces=False,
        give_amount=1,
        sense=3,
        tags={"split", "sharing"},
    ),
    "offer_piece": ShareMove(
        id="offer_piece",
        label="offer one piece",
        needs_divisible=False,
        needs_many_pieces=True,
        give_amount=1,
        sense=2,
        tags={"piece", "sharing"},
    ),
    "offer_whole": ShareMove(
        id="offer_whole",
        label="offer the whole treat",
        needs_divisible=False,
        needs_many_pieces=False,
        give_amount=1,
        sense=1,
        tags={"whole", "sharing"},
    ),
}

JOKES = {
    "jam_nose": Joke(
        id="jam_nose",
        line="Goodness me, if I sniff that bun much longer, my nose may turn into a plum!",
        image="He crossed his eyes at the tip of his own nose, and somehow a shiny sticky smudge ended up right there.",
        boost=2,
        tags={"humor", "jam"},
    ),
    "singing_tummy": Joke(
        id="singing_tummy",
        line="My tummy is trying to sing the evening hymn before the bell does.",
        image="He laid a hand on his middle and hummed one very solemn note until it wobbled into a silly wobble.",
        boost=1,
        tags={"humor", "song"},
    ),
    "hat_pigeon": Joke(
        id="hat_pigeon",
        line="If I stand still too long, a pigeon may mistake my hat for a chapel roof.",
        image="He tipped his hat and looked up so carefully that even the child had to giggle.",
        boost=1,
        tags={"humor", "hat"},
    ),
}

CHILDREN = {
    "girl": ChildKind(
        id="girl",
        type="girl",
        name_pool=["Molly", "Daisy", "Nell", "Poppy", "Maisie", "Lark"],
        title="little lass",
        clutch_word="palm",
    ),
    "boy": ChildKind(
        id="boy",
        type="boy",
        name_pool=["Toby", "Ned", "Alfie", "Robin", "Jem", "Pip"],
        title="little lad",
        clutch_word="fist",
    ),
}


@dataclass
class StoryParams:
    place: str
    child_kind: str
    food: str
    share: str
    joke: str
    child_name: str
    greed: int = 2
    shyness: int = 1
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
    "priest": [
        (
            "What is a priest?",
            "A priest is a religious leader who prays, helps people, and often speaks kindly to a community. In many villages, children might know a priest as someone they greet at church or on the lane."
        )
    ],
    "sharing": [
        (
            "Why is sharing kind?",
            "Sharing lets another person feel welcome and cared for. Even a small bite can matter when it is given with a happy heart."
        )
    ],
    "inner_voice": [
        (
            "What is an inner voice?",
            "An inner voice is the quiet thinking you hear inside your own mind. It can help you choose between keeping something and doing the kinder thing."
        )
    ],
    "humor": [
        (
            "Why can a joke help people share?",
            "A joke can make everyone feel less stiff and worried. When people laugh together, kindness often feels easier."
        )
    ],
    "bun": [
        (
            "What is a bun?",
            "A bun is a small round bread or sweet roll. It is easy to break and share with someone else."
        )
    ],
    "bread": [
        (
            "Why is bread easy to share?",
            "Bread can often be torn or cut into smaller parts. That makes it a simple food for two people to enjoy together."
        )
    ],
    "pear": [
        (
            "Can a pear be shared?",
            "Yes. A pear can be cut or broken into pieces so more than one person can eat it."
        )
    ],
    "berries": [
        (
            "Can berries be shared?",
            "Yes. When there are several berries, one person can offer some and keep some."
        )
    ],
}
KNOWLEDGE_ORDER = ["priest", "sharing", "inner_voice", "humor", "bun", "bread", "pear", "berries"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    food = f["food_cfg"]
    return [
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old about a child, a priest, and a little food to share. Include the word "priest".',
        f"Tell a gentle funny story where {child.id} meets a priest in {place.label}, argues inside {child.pronoun('possessive')} own head about sharing {food.phrase}, and learns something kind.",
        f"Write a simple rhyming tale with inner monologue, humor, and sharing, ending with a clear picture of what changed in the child's heart.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    priest = f["priest"]
    place = f["place"]
    food = f["food_cfg"]
    share = f["share_cfg"]
    joke = f["joke_cfg"]
    predicted = f.get("predicted", {})
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child with {food.phrase}, and a priest who walked by looking tired and kind. They meet in {place.label}, where the little choice about food becomes the whole story."
        ),
        (
            f"What was {child.id} thinking inside?",
            f"{child.id} had an inner rhyme about whether to keep the treat or share it. The thought mattered because {child.pronoun()} wanted the food, but also noticed the priest might need a bite."
        ),
        (
            "Why did the priest make a joke?",
            f'The priest used a joke to make the moment lighter instead of demanding anything. That helped the child feel less tight and worried, so kindness had more room to grow.'
        ),
    ]
    if predicted:
        qa.append(
            (
                f"Did the child seem ready to share at first?",
                f"Not fully. {child.id} began with worry and a clutching feeling, and the inner monologue shows {child.pronoun()} was still deciding. The joke and the sight of the tired priest pushed the choice toward sharing."
            )
        )
    if f["outcome"] == "shared":
        action = {
            "split": f"{child.id} split the {food.label} and handed over half",
            "offer_piece": f"{child.id} offered one piece from the food",
            "offer_whole": f"{child.id} bravely offered the whole treat",
        }[share.id]
        qa.append(
            (
                f"How did {child.id} share the food?",
                f"{action}. That act eased the priest's hunger and also changed the child's own feelings from worry into relief."
            )
        )
        qa.append(
            (
                "What changed by the end?",
                f"By the end, the child had learned that a small treat can make two people happy when it is shared. The priest also shared back a playful blessing, so the ending proves kindness can come back in another form."
            )
        )
        if f.get("jam_nose"):
            qa.append(
                (
                    "What was funny in the story?",
                    f"The priest ended up with a shiny sticky spot on his nose while joking. That silly sight made the sharing moment feel warm and playful instead of stiff."
                )
            )
    else:
        qa.append(
            (
                f"Why did {child.id} keep the food?",
                f"{child.id} still felt too shy and clingy to let go of it, even after the joke. The child was not cruel, just not brave enough yet, and that is why the ending turns into a quiet lesson."
            )
        )
        qa.append(
            (
                "What did the child learn at the end?",
                f"The child learned that keeping everything did not feel as bright as expected. The last image shows a full hand but a smaller heart, which is why the promise to do better matters."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"priest", "sharing", "inner_voice", "humor"}
    food = world.facts["food_cfg"]
    tags |= set(food.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.divisible:
            bits.append("divisible=True")
        if e.shareable_pieces:
            bits.append(f"shareable_pieces={e.shareable_pieces}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} predicted={world.facts.get('predicted')}")
    lines.append(f"  history: {world.history}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="churchyard",
        child_kind="girl",
        food="bun",
        share="split",
        joke="jam_nose",
        child_name="Molly",
        greed=2,
        shyness=1,
    ),
    StoryParams(
        place="lane",
        child_kind="boy",
        food="berries",
        share="offer_piece",
        joke="hat_pigeon",
        child_name="Toby",
        greed=2,
        shyness=1,
    ),
    StoryParams(
        place="green",
        child_kind="girl",
        food="loaf",
        share="offer_whole",
        joke="singing_tummy",
        child_name="Daisy",
        greed=1,
        shyness=0,
    ),
    StoryParams(
        place="lane",
        child_kind="boy",
        food="bun",
        share="offer_whole",
        joke="hat_pigeon",
        child_name="Ned",
        greed=3,
        shyness=2,
    ),
]


def explain_rejection(food: Food, share: ShareMove) -> str:
    if share.needs_divisible and not food.divisible:
        return (
            f"(No story: {share.label} does not fit {food.phrase}. "
            f"That sharing move only makes sense for a food that can be divided.)"
        )
    if share.needs_many_pieces and food.pieces < 2:
        return (
            f"(No story: {share.label} needs more than one piece to offer, but {food.phrase} does not provide that.)"
        )
    return "(No story: this food and sharing move do not fit together.)"


def outcome_of(params: StoryParams) -> str:
    if params.place not in PLACES or params.child_kind not in CHILDREN or params.food not in FOODS or params.share not in SHARES or params.joke not in JOKES:
        raise StoryError("(No story: one or more parameter keys are unknown.)")
    if not valid_share(FOODS[params.food], SHARES[params.share]):
        raise StoryError(explain_rejection(FOODS[params.food], SHARES[params.share]))
    return "shared" if would_share(params.greed, params.shyness, JOKES[params.joke], SHARES[params.share]) else "kept"


ASP_RULES = r"""
valid(Place, Child, Food, Share) :-
    place(Place), child_kind(Child), food(Food), share(Share),
    not bad_combo(Food, Share).

bad_combo(Food, Share) :- needs_divisible(Share), not divisible(Food).
bad_combo(Food, Share) :- needs_many_pieces(Share), pieces(Food, N), N < 2.

score(S) :- chosen_joke(J), boost(J, B),
            chosen_share(Sh), sense(Sh, Se),
            greed(G), shyness(Y),
            S = B + Se - G - Y.

outcome(shared) :- score(S), S >= 1.
outcome(kept)   :- score(S), S < 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for child_id in CHILDREN:
        lines.append(asp.fact("child_kind", child_id))
    for food_id, food in FOODS.items():
        lines.append(asp.fact("food", food_id))
        lines.append(asp.fact("pieces", food_id, food.pieces))
        if food.divisible:
            lines.append(asp.fact("divisible", food_id))
    for share_id, share in SHARES.items():
        lines.append(asp.fact("share", share_id))
        lines.append(asp.fact("sense", share_id, share.sense))
        if share.needs_divisible:
            lines.append(asp.fact("needs_divisible", share_id))
        if share.needs_many_pieces:
            lines.append(asp.fact("needs_many_pieces", share_id))
    for joke_id, joke in JOKES.items():
        lines.append(asp.fact("joke", joke_id))
        lines.append(asp.fact("boost", joke_id, joke.boost))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_joke", params.joke),
            asp.fact("chosen_share", params.share),
            asp.fact("greed", params.greed),
            asp.fact("shyness", params.shyness),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases: list[StoryParams] = list(CURATED)
    for seed in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            mismatches += 1
            print(f"MISMATCH outcome for {params}: python={py} clingo={cl}")
    if mismatches == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a child, a priest, a joke, and a choice to share."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child-kind", choices=CHILDREN)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--joke", choices=JOKES)
    ap.add_argument("--name")
    ap.add_argument("--greed", type=int, choices=[0, 1, 2, 3], help="how tightly the child clings to the treat")
    ap.add_argument("--shyness", type=int, choices=[0, 1, 2, 3], help="how hard it is for the child to speak up")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.food and args.share:
        food = FOODS[args.food]
        share = SHARES[args.share]
        if not valid_share(food, share):
            raise StoryError(explain_rejection(food, share))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.child_kind is None or combo[1] == args.child_kind)
        and (args.food is None or combo[2] == args.food)
        and (args.share is None or combo[3] == args.share)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, child_kind, food, share = rng.choice(sorted(combos))
    joke = args.joke or rng.choice(sorted(JOKES))
    kind = CHILDREN[child_kind]
    name = args.name or rng.choice(kind.name_pool)
    greed = args.greed if args.greed is not None else rng.choice([1, 2, 2, 3])
    shyness = args.shyness if args.shyness is not None else rng.choice([0, 1, 1, 2])
    return StoryParams(
        place=place,
        child_kind=child_kind,
        food=food,
        share=share,
        joke=joke,
        child_name=name,
        greed=greed,
        shyness=shyness,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.child_kind not in CHILDREN:
        raise StoryError(f"(No story: unknown child kind '{params.child_kind}'.)")
    if params.food not in FOODS:
        raise StoryError(f"(No story: unknown food '{params.food}'.)")
    if params.share not in SHARES:
        raise StoryError(f"(No story: unknown share move '{params.share}'.)")
    if params.joke not in JOKES:
        raise StoryError(f"(No story: unknown joke '{params.joke}'.)")
    food = FOODS[params.food]
    share = SHARES[params.share]
    if not valid_share(food, share):
        raise StoryError(explain_rejection(food, share))

    world = tell(
        PLACES[params.place],
        CHILDREN[params.child_kind],
        food,
        share,
        JOKES[params.joke],
        child_name=params.child_name,
        greed=params.greed,
        shyness=params.shyness,
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
        print(f"{len(combos)} valid (place, child_kind, food, share) combos:\n")
        for place, child_kind, food, share in combos:
            print(f"  {place:10} {child_kind:8} {food:8} {share}")
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
            header = f"### {p.child_name}: {p.food} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
