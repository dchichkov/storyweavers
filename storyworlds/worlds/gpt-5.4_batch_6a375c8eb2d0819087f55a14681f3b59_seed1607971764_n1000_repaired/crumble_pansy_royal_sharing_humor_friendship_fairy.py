#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crumble_pansy_royal_sharing_humor_friendship_fairy.py
================================================================================

A standalone fairy-tale storyworld about two small friends, a warm crumble, a
royal place, and the funny little moment that teaches them to share.

The domain is intentionally narrow: two fairy friends carry a crumble toward a
royal tea table, meet a hungry little guest, and must decide whether to hold the
dessert tightly or open their hands. A comic mishap creates the turn, and a kind
act repairs the moment. Some combinations are rejected when there simply is not
enough food to make a plausible sharing story.

Run it
------
    python storyworlds/worlds/gpt-5.4/crumble_pansy_royal_sharing_humor_friendship_fairy.py
    python storyworlds/worlds/gpt-5.4/crumble_pansy_royal_sharing_humor_friendship_fairy.py --place royal_bridge
    python storyworlds/worlds/gpt-5.4/crumble_pansy_royal_sharing_humor_friendship_fairy.py --crumble plum --guest hedgehog
    python storyworlds/worlds/gpt-5.4/crumble_pansy_royal_sharing_humor_friendship_fairy.py --verify
    python storyworlds/worlds/gpt-5.4/crumble_pansy_royal_sharing_humor_friendship_fairy.py --qa --json
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
FRIENDS_COUNT = 2


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
        female = {"girl", "fairy_girl", "queen", "mother", "lady"}
        male = {"boy", "fairy_boy", "king", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    intro: str
    path: str
    helper: str
    helper_bonus: int
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
class Crumble:
    id: str
    label: str
    phrase: str
    aroma: str
    portions: int
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
class Guest:
    id: str
    label: str
    appetite: int
    manner: str
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
    setup: str
    slip: str
    laugh: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_spill(world: World) -> list[str]:
    crumble = world.get("crumble")
    if crumble.meters["clutched"] < THRESHOLD:
        return []
    if world.get("joke").meters["tickle"] < THRESHOLD:
        return []
    sig = ("spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crumble.meters["spill"] += 1
    crumble.meters["portions"] = max(0.0, crumble.meters["portions"] - 1.0)
    for kid in (world.get("friend1"), world.get("friend2")):
        kid.memes["laughter"] += 1
        kid.memes["embarrassment"] += 1
    return ["__spill__"]


def _r_help(world: World) -> list[str]:
    if world.get("intent").meters["share"] < THRESHOLD:
        return []
    if world.get("helper").meters["present"] < THRESHOLD:
        return []
    if world.get("crumble").meters["portions"] >= world.facts["need"]:
        return []
    sig = ("help",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("crumble").meters["portions"] += world.place.helper_bonus
    world.get("helper").memes["kindness"] += 1
    return ["__help__"]


def _r_shared(world: World) -> list[str]:
    if world.get("intent").meters["share"] < THRESHOLD:
        return []
    if world.get("crumble").meters["portions"] < world.facts["need"]:
        return []
    sig = ("shared",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("guest").meters["hunger"] = 0.0
    world.get("friend1").memes["friendship"] += 1
    world.get("friend2").memes["friendship"] += 1
    world.get("guest").memes["friendship"] += 1
    world.get("queen").memes["approval"] += 1
    world.get("crumble").meters["served"] += world.facts["need"]
    return ["__shared__"]


CAUSAL_RULES = [
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="help", tag="social", apply=_r_help),
    Rule(name="shared", tag="social", apply=_r_shared),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            if not s.startswith("__"):
                world.say(s)
    return out


def total_need(guest: Guest) -> int:
    return FRIENDS_COUNT + guest.appetite


def can_feed(place: Place, crumble: Crumble, guest: Guest) -> bool:
    return crumble.portions + place.helper_bonus >= total_need(guest)


def outcome_for(place: Place, crumble: Crumble, guest: Guest) -> str:
    return "direct_share" if crumble.portions >= total_need(guest) else "helped_share"


def predict_shortage(world: World) -> dict:
    sim = world.copy()
    sim.get("crumble").meters["clutched"] += 1
    sim.get("joke").meters["tickle"] += 1
    propagate(sim, narrate=False)
    before_help = sim.get("crumble").meters["portions"]
    enough_before = before_help >= sim.facts["need"]
    sim.get("intent").meters["share"] += 1
    propagate(sim, narrate=False)
    after_help = sim.get("crumble").meters["portions"]
    enough_after = after_help >= sim.facts["need"]
    return {
        "before_help": int(before_help),
        "enough_before": enough_before,
        "after_help": int(after_help),
        "enough_after": enough_after,
    }


def opening(world: World, f1: Entity, f2: Entity, crumble: Crumble) -> None:
    for kid in (f1, f2):
        kid.memes["joy"] += 1
    world.say(
        f"In {world.place.label}, where the flagstones shone like little mirrors, "
        f"{f1.id} and {f2.id} fluttered along with {crumble.phrase}. {world.place.intro}"
    )
    world.say(
        f"The warm {crumble.label} smelled of {crumble.aroma}, and both friends felt proud to carry it toward the royal tea table."
    )


def meet_guest(world: World, f1: Entity, guest: Entity, guest_cfg: Guest) -> None:
    guest.meters["hunger"] = float(guest_cfg.appetite)
    world.say(
        f"Beside the path grew a velvet pansy bed, and there {guest_cfg.label} appeared, {guest_cfg.manner}. "
        f'"Goodness," said {f1.id}, "you look as if breakfast flew away without you."'
    )


def dilemma(world: World, f1: Entity, f2: Entity, guest_cfg: Guest) -> None:
    pred = predict_shortage(world)
    world.facts["predicted"] = pred
    world.get("crumble").meters["clutched"] += 1
    world.say(
        f'{f2.id} hugged the dish a little tighter. "If we share now," {f2.pronoun()} whispered, '
        f'"will there still be enough for us and for our little guest?"'
    )
    if pred["enough_before"]:
        world.say(
            f"{f1.id} counted the spoonfuls with a careful finger and saw there would still be enough for all three."
        )
    else:
        world.say(
            f"{f1.id} counted the spoonfuls with a careful finger and saw a small worry: after any wobble, the crumble might fall short."
        )


def comic_turn(world: World, f2: Entity, joke: Joke) -> None:
    world.get("joke").meters["tickle"] += 1
    world.say(joke.setup.replace("{holder}", f2.id))
    propagate(world, narrate=False)
    if world.get("crumble").meters["spill"] >= THRESHOLD:
        world.say(joke.slip)
        world.say(joke.laugh.replace("{holder}", f2.id))


def choose_share(world: World, f1: Entity, f2: Entity, guest_cfg: Guest) -> None:
    world.get("intent").meters["share"] += 1
    f1.memes["generosity"] += 1
    f2.memes["generosity"] += 1
    world.say(
        f'"That settles it," said {f1.id}. "Hands that squeeze too hard make crumbs run away. Hands that share are wiser."'
    )
    world.say(
        f'{f2.id} looked at the missing bit, then at the hungry {guest_cfg.label}, and nodded. '
        f'"Then let us be wise together," {f2.pronoun()} said.'
    )
    propagate(world, narrate=False)


def helper_step(world: World) -> None:
    if world.get("helper").memes["kindness"] >= THRESHOLD:
        world.say(
            f"Just then {world.place.helper} saw their kind choice and added a shining spoonful from a silver pot, so the dish looked whole-hearted again."
        )


def share_feast(world: World, f1: Entity, f2: Entity, guest_cfg: Guest, crumble: Crumble) -> None:
    world.say(
        f"They set three neat bites onto broad pansy leaves and passed them around: one for {f1.id}, one for {f2.id}, and one for the {guest_cfg.label}."
    )
    world.say(
        f"The {crumble.label} tasted of {crumble.aroma}, and it tasted even sweeter because nobody was left out."
    )


def royal_ending(world: World, f1: Entity, f2: Entity, guest_cfg: Guest) -> None:
    for kid in (f1, f2):
        kid.memes["joy"] += 1
    world.say(
        f"The Queen of Dewdrops paused by the pansies and smiled at the tiny feast. "
        f'"A royal table grows grander when friendship sits at it," she said.'
    )
    world.say(
        f"{guest_cfg.label.capitalize()} bowed so low that everyone laughed again, and {f1.id} and {f2.id} walked on lighter than before. "
        f"They had started the morning carrying a dessert; they ended it carrying a stronger friendship."
    )


def tell(
    place: Place,
    crumble_cfg: Crumble,
    guest_cfg: Guest,
    joke_cfg: Joke,
    friend1_name: str = "Pip",
    friend1_type: str = "fairy_girl",
    friend2_name: str = "Moss",
    friend2_type: str = "fairy_boy",
) -> World:
    world = World(place)
    f1 = world.add(Entity(id=friend1_name, kind="character", type=friend1_type, role="friend"))
    f2 = world.add(Entity(id=friend2_name, kind="character", type=friend2_type, role="friend"))
    guest = world.add(Entity(id="guest", kind="character", type="creature", role="guest", label=guest_cfg.label))
    queen = world.add(Entity(id="queen", kind="character", type="queen", role="royal", label="the queen"))
    helper = world.add(Entity(id="helper", kind="character", type="sprite", role="helper", label=place.helper))
    if place.helper_bonus > 0:
        helper.meters["present"] = 1.0
    crumble = world.add(Entity(id="crumble", type="dessert", label=crumble_cfg.label))
    crumble.meters["portions"] = float(crumble_cfg.portions)
    world.add(Entity(id="joke", type="joke", label=joke_cfg.id))
    world.add(Entity(id="intent", type="intention", label="sharing intention"))
    world.add(Entity(id="pansy", type="flower", label="pansy"))

    world.facts["need"] = total_need(guest_cfg)
    world.facts["place"] = place
    world.facts["crumble_cfg"] = crumble_cfg
    world.facts["guest_cfg"] = guest_cfg
    world.facts["joke_cfg"] = joke_cfg
    world.facts["friend1"] = f1
    world.facts["friend2"] = f2

    opening(world, f1, f2, crumble_cfg)
    world.para()
    meet_guest(world, f1, guest, guest_cfg)
    dilemma(world, f1, f2, guest_cfg)
    comic_turn(world, f2, joke_cfg)
    world.para()
    choose_share(world, f1, f2, guest_cfg)
    helper_step(world)
    share_feast(world, f1, f2, guest_cfg, crumble_cfg)
    world.para()
    royal_ending(world, f1, f2, guest_cfg)

    world.facts.update(
        story_outcome=outcome_for(place, crumble_cfg, guest_cfg),
        shared=world.get("guest").meters["hunger"] < THRESHOLD,
        helper_used=world.get("helper").memes["kindness"] >= THRESHOLD,
        spilled=world.get("crumble").meters["spill"] >= THRESHOLD,
        final_portions=int(world.get("crumble").meters["portions"]),
        queen_approved=world.get("queen").memes["approval"] >= THRESHOLD,
    )
    return world


PLACES = {
    "royal_garden": Place(
        id="royal_garden",
        label="the royal garden",
        intro="Blue bells rang in the breeze, and a low wall of pansies nodded as if they knew a secret.",
        path="mossy path",
        helper="the royal honey-bee baker",
        helper_bonus=1,
        tags={"royal", "garden", "helper"},
    ),
    "opal_greenhouse": Place(
        id="opal_greenhouse",
        label="the opal royal greenhouse",
        intro="Glass above them glimmered like a morning bubble, and every corner held a smile of pansy color.",
        path="glass walk",
        helper="the palace jam sprite",
        helper_bonus=1,
        tags={"royal", "greenhouse", "helper"},
    ),
    "royal_bridge": Place(
        id="royal_bridge",
        label="the royal moon bridge",
        intro="Below the arch, the river kept whispering jokes to the reeds, while pots of pansies lined the rail.",
        path="bridge",
        helper="nobody at all",
        helper_bonus=0,
        tags={"royal", "bridge"},
    ),
}

CRUMBLES = {
    "apple": Crumble(
        id="apple",
        label="apple crumble",
        phrase="a warm apple crumble in a bright tin dish",
        aroma="butter and cinnamon",
        portions=4,
        tags={"crumble", "apple"},
    ),
    "plum": Crumble(
        id="plum",
        label="plum crumble",
        phrase="a jewel-dark plum crumble in a bright tin dish",
        aroma="plums and brown sugar",
        portions=3,
        tags={"crumble", "plum"},
    ),
    "pear": Crumble(
        id="pear",
        label="pear crumble",
        phrase="a golden pear crumble in a bright tin dish",
        aroma="pear and honey",
        portions=5,
        tags={"crumble", "pear"},
    ),
}

GUESTS = {
    "mouse": Guest(
        id="mouse",
        label="field mouse",
        appetite=1,
        manner="with whiskers twitching hopefully",
        tags={"mouse", "small_hunger"},
    ),
    "wren": Guest(
        id="wren",
        label="wren",
        appetite=1,
        manner="with a polite hop and a very empty little chirp",
        tags={"bird", "small_hunger"},
    ),
    "hedgehog": Guest(
        id="hedgehog",
        label="hedgehog",
        appetite=2,
        manner="with a slow bow and a tummy that rumbled like a toy drum",
        tags={"hedgehog", "big_hunger"},
    ),
}

JOKES = {
    "bee_tickle": Joke(
        id="bee_tickle",
        setup="A round bee circled {holder}'s nose as if it were a flower and gave such a tickly buzz that a sneeze popped out.",
        slip="The dish tipped, and one buttery corner of crumble went skittering onto the cloth like a naughty little hill.",
        laugh="{holder} blinked in surprise, and even the hungry guest gave a tiny snort of laughter.",
        tags={"bee", "humor"},
    ),
    "petal_sneeze": Joke(
        id="petal_sneeze",
        setup="A wandering pansy petal brushed {holder}'s nose, and a royal little sneeze escaped before anybody could catch it.",
        slip="At once a soft crumble edge hopped over the rim and landed with a plop beside the spoon.",
        laugh="For one startled breath {holder} looked scandalized, and then everybody laughed because the runaway crumb looked like a sleeping puffball.",
        tags={"pansy", "humor"},
    ),
    "cup_hiccup": Joke(
        id="cup_hiccup",
        setup="From the tea basket came the tiniest hiccup; the silver cup had bumped the plate, and {holder} gave a jump.",
        slip="That jump sent a crumbly ridge sliding down the side of the dish in a delicious little avalanche.",
        laugh="The sound was so silly that {holder} began to giggle first, and the rest followed at once.",
        tags={"tea", "humor"},
    ),
}


@dataclass
class StoryParams:
    place: str
    crumble: str
    guest: str
    joke: str
    friend1_name: str
    friend1_type: str
    friend2_name: str
    friend2_type: str
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


GIRL_NAMES = ["Pip", "Daisy", "Lark", "Nim", "Tansy", "Rue"]
BOY_NAMES = ["Moss", "Fern", "Cob", "Ash", "Thimble", "Bram"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for crumble_id, crumble in CRUMBLES.items():
            for guest_id, guest in GUESTS.items():
                if can_feed(place, crumble, guest):
                    combos.append((place_id, crumble_id, guest_id))
    return sorted(combos)


KNOWLEDGE = {
    "crumble": [
        ("What is a crumble?",
         "A crumble is a baked fruit dessert with soft fruit underneath and crumbly topping on top. It is sweet, warm, and easy to share with a spoon.")
    ],
    "pansy": [
        ("What is a pansy?",
         "A pansy is a garden flower with round soft petals and bright colors. People often grow pansies where they want a cheerful patch of color.")
    ],
    "sharing": [
        ("Why does sharing food feel kind?",
         "Sharing food tells another person, or even a tiny creature, that they matter too. It can turn one small treat into a friendly moment for everyone.")
    ],
    "friendship": [
        ("How can sharing help friendship?",
         "Sharing helps friendship because it shows trust and care. When friends make room for each other, they usually feel closer afterward.")
    ],
    "humor": [
        ("Why can a funny mistake help a story feel gentle?",
         "A funny mistake can loosen a tense moment and help everyone breathe again. Laughing together can make it easier to choose kindness instead of fussing.")
    ],
    "royal": [
        ("What does royal mean?",
         "Royal means connected to a king or queen and their palace or court. In fairy tales, royal places often feel grand and shiny.")
    ],
}
KNOWLEDGE_ORDER = ["crumble", "pansy", "sharing", "friendship", "humor", "royal"]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    crumble = world.facts["crumble_cfg"]
    guest = world.facts["guest_cfg"]
    f1 = world.facts["friend1"]
    f2 = world.facts["friend2"]
    return [
        f'Write a fairy tale for a 3-to-5-year-old that includes the words "crumble", "pansy", and "royal".',
        f"Tell a gentle story where two fairy friends, {f1.id} and {f2.id}, carry {crumble.label} through {place.label}, meet a hungry {guest.label}, and learn to share.",
        "Write a child-facing fairy tale with humor, friendship, and a kind ending where a funny little mishap leads to generosity.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    place = world.facts["place"]
    crumble = world.facts["crumble_cfg"]
    guest = world.facts["guest_cfg"]
    f1 = world.facts["friend1"]
    f2 = world.facts["friend2"]
    pred = world.facts.get("predicted", {})
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two fairy friends, {f1.id} and {f2.id}, carrying a {crumble.label} through {place.label}. They meet a hungry {guest.label} by a bed of pansies."
        ),
        (
            "What problem did the friends face?",
            f"They had one dessert and three hungry tummies to think about. At first, {f2.id} worried there might not be enough if they shared."
        ),
    ]
    if world.facts.get("spilled"):
        out.append((
            "What funny thing happened to the crumble?",
            f"A silly tickle made the dish wobble, and a little piece of crumble slid away. The funny slip showed that clutching the dessert tightly was not helping."
        ))
    if world.facts.get("helper_used"):
        out.append((
            "How did they make sure everyone could eat?",
            f"They chose to share first, and then {place.helper} noticed their kindness and added a little extra sweetness. That small help turned a worried dish into enough for all three."
        ))
    else:
        out.append((
            "How could they still share without extra help?",
            f"{f1.id} had counted the bites and knew the dish would still stretch far enough. Because the portions were enough already, they could share right away."
        ))
    out.append((
        "Why did the Queen smile at them?",
        f"The Queen smiled because they made room for a hungry guest instead of thinking only of themselves. Their kindness made the royal table feel warmer."
    ))
    if pred:
        if pred.get("enough_before"):
            extra = "there was already enough, even before any helper stepped in."
        else:
            extra = "the first count looked tight after the wobble, so kindness from a helper mattered."
        out.append((
            "Explain how the friends solved the problem.",
            f"They stopped squeezing the dish and decided to share it fairly on pansy leaves. {extra} That choice changed the mood from worry into laughter and friendship."
        ))
    return out


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    tags = {"crumble", "pansy", "sharing", "friendship", "humor", "royal"}
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  need={world.facts.get('need')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="royal_garden",
        crumble="apple",
        guest="mouse",
        joke="petal_sneeze",
        friend1_name="Pip",
        friend1_type="fairy_girl",
        friend2_name="Moss",
        friend2_type="fairy_boy",
    ),
    StoryParams(
        place="opal_greenhouse",
        crumble="plum",
        guest="hedgehog",
        joke="bee_tickle",
        friend1_name="Daisy",
        friend1_type="fairy_girl",
        friend2_name="Fern",
        friend2_type="fairy_boy",
    ),
    StoryParams(
        place="royal_bridge",
        crumble="pear",
        guest="hedgehog",
        joke="cup_hiccup",
        friend1_name="Lark",
        friend1_type="fairy_girl",
        friend2_name="Ash",
        friend2_type="fairy_boy",
    ),
]


def explain_rejection(place: Place, crumble: Crumble, guest: Guest) -> str:
    need = total_need(guest)
    have = crumble.portions + place.helper_bonus
    if place.helper_bonus:
        return (
            f"(No story: {crumble.label} offers at most {have} spoonfuls in {place.label}, "
            f"but feeding two friends and the {guest.label} needs {need}. Even with help, the dish would not stretch honestly.)"
        )
    return (
        f"(No story: {crumble.label} offers only {have} spoonfuls on {place.label}, "
        f"but feeding two friends and the {guest.label} needs {need}. There is no helper here to make a fair sharing ending plausible.)"
    )


ASP_RULES = r"""
need(G, 2 + A)        :- guest(G), appetite(G, A).
possible(P, C, G)     :- place(P), crumble(C), guest(G),
                         helper_bonus(P, B), portions(C, N), need(G, K), N + B >= K.
direct_share(P, C, G) :- possible(P, C, G), portions(C, N), need(G, K), N >= K.
helped_share(P, C, G) :- possible(P, C, G), portions(C, N), need(G, K), helper_bonus(P, B), N < K, N + B >= K.

scenario_need(2 + A)     :- chosen_guest(G), appetite(G, A).
scenario_possible        :- chosen_place(P), chosen_crumble(C), chosen_guest(G),
                            helper_bonus(P, B), portions(C, N), scenario_need(K), N + B >= K.
scenario_outcome(direct_share) :- scenario_possible, chosen_crumble(C), portions(C, N), scenario_need(K), N >= K.
scenario_outcome(helped_share) :- scenario_possible, chosen_place(P), helper_bonus(P, B),
                                  chosen_crumble(C), portions(C, N), scenario_need(K), N < K, N + B >= K.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("helper_bonus", pid, place.helper_bonus))
    for cid, crumble in CRUMBLES.items():
        lines.append(asp.fact("crumble", cid))
        lines.append(asp.fact("portions", cid, crumble.portions))
    for gid, guest in GUESTS.items():
        lines.append(asp.fact("guest", gid))
        lines.append(asp.fact("appetite", gid, guest.appetite))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show possible/3."))
    return sorted(set(asp.atoms(model, "possible")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_crumble", params.crumble),
        asp.fact("chosen_guest", params.guest),
    ])
    model = asp.one_model(asp_program(extra, "#show scenario_outcome/1."))
    atoms = asp.atoms(model, "scenario_outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a royal path, a crumble, a pansy bed, and a lesson in sharing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--crumble", choices=CRUMBLES)
    ap.add_argument("--guest", choices=GUESTS)
    ap.add_argument("--joke", choices=JOKES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_friend(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    kind = rng.choice(["fairy_girl", "fairy_boy"])
    pool = [n for n in (GIRL_NAMES if kind == "fairy_girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), kind


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.crumble and args.guest:
        place = PLACES[args.place]
        crumble = CRUMBLES[args.crumble]
        guest = GUESTS[args.guest]
        if not can_feed(place, crumble, guest):
            raise StoryError(explain_rejection(place, crumble, guest))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.crumble is None or c[1] == args.crumble)
        and (args.guest is None or c[2] == args.guest)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, crumble, guest = rng.choice(combos)
    joke = args.joke or rng.choice(sorted(JOKES))
    f1_name, f1_type = _pick_friend(rng)
    f2_name, f2_type = _pick_friend(rng, avoid=f1_name)
    return StoryParams(
        place=place,
        crumble=crumble,
        guest=guest,
        joke=joke,
        friend1_name=f1_name,
        friend1_type=f1_type,
        friend2_name=f2_name,
        friend2_type=f2_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.crumble not in CRUMBLES:
        raise StoryError(f"(Unknown crumble: {params.crumble})")
    if params.guest not in GUESTS:
        raise StoryError(f"(Unknown guest: {params.guest})")
    if params.joke not in JOKES:
        raise StoryError(f"(Unknown joke: {params.joke})")
    place = PLACES[params.place]
    crumble = CRUMBLES[params.crumble]
    guest = GUESTS[params.guest]
    if not can_feed(place, crumble, guest):
        raise StoryError(explain_rejection(place, crumble, guest))

    world = tell(
        place=place,
        crumble_cfg=crumble,
        guest_cfg=guest,
        joke_cfg=JOKES[params.joke],
        friend1_name=params.friend1_name,
        friend1_type=params.friend1_type,
        friend2_name=params.friend2_name,
        friend2_type=params.friend2_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure for seed {seed}.")
            break
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_for(PLACES[p.place], CRUMBLES[p.crumble], GUESTS[p.guest]):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("\nOK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show possible/3.\n#show direct_share/3.\n#show helped_share/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, crumble, guest) combos:\n")
        for place, crumble, guest in combos:
            mode = outcome_for(PLACES[place], CRUMBLES[crumble], GUESTS[guest])
            print(f"  {place:16} {crumble:8} {guest:9} [{mode}]")
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
            header = f"### {p.friend1_name} & {p.friend2_name}: {p.crumble} at {p.place} for {p.guest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
