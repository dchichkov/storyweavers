#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hoard_vacancy_bravery_happy_ending_lesson_learned.py
================================================================================

A standalone story world for a small fable-shaped domain: a woodland innkeeper
has let a winter hoard spill into the guest room, even though a "vacancy" sign
still hangs outside. On a stormy night, a tired traveler arrives. To make the
sign true again, the innkeeper must bravely carry the hoard to its proper store.

The world model drives the turn:
- a hoard on the guest bed removes the inn's vacancy
- a traveler arriving to no vacancy causes shame and worry
- moving the hoard into suitable storage restores vacancy and relief

Every generated story ends happily, but only when the requested combination is
reasonable: the storage must suit the hoard, the carrying method must be
sensible, and the method must be strong enough for the hoard's bulk.

Run it
------
    python storyworlds/worlds/gpt-5.4/hoard_vacancy_bravery_happy_ending_lesson_learned.py
    python storyworlds/worlds/gpt-5.4/hoard_vacancy_bravery_happy_ending_lesson_learned.py --hoard apples --storage loft
    python storyworlds/worlds/gpt-5.4/hoard_vacancy_bravery_happy_ending_lesson_learned.py --method apron_bundle
    python storyworlds/worlds/gpt-5.4/hoard_vacancy_bravery_happy_ending_lesson_learned.py --all
    python storyworlds/worlds/gpt-5.4/hoard_vacancy_bravery_happy_ending_lesson_learned.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "goose", "vixen", "doe", "mouse_f"}
        male = {"fox", "badger", "hare", "mouse_m"}
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
class HostKind:
    id: str
    label: str
    type: str
    title: str
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
class HoardKind:
    id: str
    label: str
    phrase: str
    pile: str
    storage_need: str
    bulk: int
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
class GuestKind:
    id: str
    label: str
    title: str
    arrival: str
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
class StorageKind:
    id: str
    label: str
    phrase: str
    style: str
    need: str
    risk: str
    arrival_place: str
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
    phrase: str
    sense: int
    power: int
    use_text: str
    fail_text: str
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


def _r_blocked_room(world: World) -> list[str]:
    inn = world.get("inn")
    hoard = world.get("hoard")
    if hoard.attrs.get("place") != "guest_bed":
        return []
    if ("blocked_room",) in world.fired:
        return []
    world.fired.add(("blocked_room",))
    inn.meters["vacancy"] = 0.0
    inn.meters["blocked"] += 1
    return ["__blocked__"]


def _r_guest_worry(world: World) -> list[str]:
    inn = world.get("inn")
    guest = world.get("guest")
    host = world.get("host")
    if guest.meters["arrived"] < THRESHOLD or inn.meters["vacancy"] >= THRESHOLD:
        return []
    if ("guest_worry",) in world.fired:
        return []
    world.fired.add(("guest_worry",))
    guest.memes["worry"] += 1
    host.memes["shame"] += 1
    return ["__no_vacancy__"]


def _r_restore_vacancy(world: World) -> list[str]:
    inn = world.get("inn")
    hoard = world.get("hoard")
    storage = world.get("storage")
    guest = world.get("guest")
    host = world.get("host")
    if hoard.attrs.get("place") != storage.id:
        return []
    if not storage.attrs.get("suitable"):
        return []
    if ("restore_vacancy",) in world.fired:
        return []
    world.fired.add(("restore_vacancy",))
    inn.meters["vacancy"] = 1.0
    inn.meters["blocked"] = 0.0
    guest.memes["relief"] += 1
    host.memes["relief"] += 1
    host.memes["lesson"] += 1
    return ["__vacancy_restored__"]


CAUSAL_RULES = [
    Rule(name="blocked_room", tag="physical", apply=_r_blocked_room),
    Rule(name="guest_worry", tag="social", apply=_r_guest_worry),
    Rule(name="restore_vacancy", tag="physical", apply=_r_restore_vacancy),
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
        for s in produced:
            world.say(s)
    return produced


HOSTS = {
    "mouse": HostKind(
        id="mouse",
        label="mouse",
        type="mouse_m",
        title="Mistress Nibble",
        tags={"mouse", "inn"},
    ),
    "hedgehog": HostKind(
        id="hedgehog",
        label="hedgehog",
        type="badger",
        title="Master Bristle",
        tags={"hedgehog", "inn"},
    ),
    "squirrel": HostKind(
        id="squirrel",
        label="squirrel",
        type="hare",
        title="Keeper Hazel",
        tags={"squirrel", "inn"},
    ),
}

HOARDS = {
    "acorns": HoardKind(
        id="acorns",
        label="acorns",
        phrase="a hoard of brown acorns",
        pile="small brown acorns",
        storage_need="dry",
        bulk=2,
        tags={"hoard", "acorn"},
    ),
    "apples": HoardKind(
        id="apples",
        label="apples",
        phrase="a hoard of winter apples",
        pile="round red apples",
        storage_need="cool",
        bulk=3,
        tags={"hoard", "apple"},
    ),
    "seeds": HoardKind(
        id="seeds",
        label="seeds",
        phrase="a hoard of striped seeds",
        pile="tiny striped seeds in little sacks",
        storage_need="dry",
        bulk=1,
        tags={"hoard", "seed"},
    ),
}

GUESTS = {
    "sparrow": GuestKind(
        id="sparrow",
        label="sparrow",
        title="a travel-worn sparrow",
        arrival="fluttered down to the step with rain on her feathers",
        tags={"bird", "guest"},
    ),
    "mole": GuestKind(
        id="mole",
        label="mole",
        title="a muddy mole",
        arrival="came tapping at the door with wet paws and a tired coat",
        tags={"mole", "guest"},
    ),
    "rabbit": GuestKind(
        id="rabbit",
        label="rabbit",
        title="a long-eared rabbit",
        arrival="stood at the threshold with a bundle under his arm and water on his whiskers",
        tags={"rabbit", "guest"},
    ),
}

STORAGES = {
    "cellar": StorageKind(
        id="cellar",
        label="cellar",
        phrase="the stone cellar",
        style="cool",
        need="cool",
        risk="down the dark cellar stairs while the storm drummed overhead",
        arrival_place="beneath the inn",
        tags={"cellar", "storage"},
    ),
    "loft": StorageKind(
        id="loft",
        label="loft",
        phrase="the beam-high loft",
        style="dry",
        need="dry",
        risk="up the creaking ladder into the windy loft",
        arrival_place="above the inn",
        tags={"loft", "storage"},
    ),
    "pantry": StorageKind(
        id="pantry",
        label="pantry",
        phrase="the narrow pantry",
        style="dry",
        need="dry",
        risk="through the narrow hall to the pantry at the back",
        arrival_place="behind the kitchen",
        tags={"pantry", "storage"},
    ),
}

METHODS = {
    "basket": Method(
        id="basket",
        label="basket",
        phrase="a wicker basket",
        sense=3,
        power=2,
        use_text="lifted the load into a wicker basket and carried it carefully",
        fail_text="tried to balance the load in a basket, but too much rolled out at once",
        tags={"basket", "carry"},
    ),
    "cart": Method(
        id="cart",
        label="cart",
        phrase="a little handcart",
        sense=3,
        power=3,
        use_text="stacked the load in a little handcart and pushed it steadily",
        fail_text="pushed a handcart toward the store, but it was far too awkward for the way",
        tags={"cart", "carry"},
    ),
    "apron_bundle": Method(
        id="apron_bundle",
        label="apron bundle",
        phrase="an apron bundle",
        sense=1,
        power=1,
        use_text="tied the load in an apron bundle and shuffled with both paws full",
        fail_text="knotted the load in an apron bundle, but the bundle sagged and split",
        tags={"bundle", "carry"},
    ),
}

GIRL_NAMES = ["Pip", "Mina", "Tansy", "Wren", "Poppy"]
BOY_NAMES = ["Bram", "Ned", "Rowan", "Otis", "Moss"]


def storage_matches(hoard: HoardKind, storage: StorageKind) -> bool:
    return hoard.storage_need == storage.need


def method_fits(method: Method, hoard: HoardKind, storage: StorageKind) -> bool:
    if method.power < hoard.bulk:
        return False
    if storage.id == "loft" and method.id == "cart":
        return False
    if storage.id == "cellar" and method.id == "cart":
        return True
    return True


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for host_id in HOSTS:
        for hoard_id, hoard in HOARDS.items():
            for guest_id in GUESTS:
                for storage_id, storage in STORAGES.items():
                    for method_id, method in METHODS.items():
                        if method.sense < SENSE_MIN:
                            continue
                        if storage_matches(hoard, storage) and method_fits(method, hoard, storage):
                            combos.append((host_id, hoard_id, guest_id, storage_id, method_id))
    return combos


@dataclass
class StoryParams:
    host: str
    hoard: str
    guest: str
    storage: str
    method: str
    host_name: str = ""
    parenthetical_moral: str = "what we hoard should not crowd out kindness"
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
        host="mouse",
        hoard="acorns",
        guest="sparrow",
        storage="pantry",
        method="basket",
        host_name="Pip",
        parenthetical_moral="a warm bed is worth more than a hidden pile",
    ),
    StoryParams(
        host="hedgehog",
        hoard="apples",
        guest="rabbit",
        storage="cellar",
        method="cart",
        host_name="Bram",
        parenthetical_moral="prudence is good, but kindness must have a place",
    ),
    StoryParams(
        host="squirrel",
        hoard="seeds",
        guest="mole",
        storage="loft",
        method="basket",
        host_name="Tansy",
        parenthetical_moral="bravery is often only kindness carrying a load",
    ),
]


def explain_storage(hoard: HoardKind, storage: StorageKind) -> str:
    return (
        f"(No story: {hoard.phrase} should be kept somewhere {hoard.storage_need}, "
        f"but {storage.phrase} is meant for {storage.style} stores. The hoard needs a proper place.)"
    )


def explain_method(method: Method, hoard: HoardKind, storage: StorageKind) -> str:
    if method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_methods()))
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    if method.power < hoard.bulk:
        return (
            f"(No story: {method.phrase} is too small for {hoard.phrase}. "
            f"The hoard is bulk {hoard.bulk}, but the method can only carry {method.power}.)"
        )
    if storage.id == "loft" and method.id == "cart":
        return (
            "(No story: a little handcart cannot sensibly be pushed up a loft ladder. "
            "Choose a carried method instead.)"
        )
    return "(No story: that carrying method does not suit this storage path.)"


def _check_params(params: StoryParams) -> None:
    if params.host not in HOSTS:
        raise StoryError(f"(Unknown host: {params.host})")
    if params.hoard not in HOARDS:
        raise StoryError(f"(Unknown hoard: {params.hoard})")
    if params.guest not in GUESTS:
        raise StoryError(f"(Unknown guest: {params.guest})")
    if params.storage not in STORAGES:
        raise StoryError(f"(Unknown storage: {params.storage})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    hoard = HOARDS[params.hoard]
    storage = STORAGES[params.storage]
    method = METHODS[params.method]
    if not storage_matches(hoard, storage):
        raise StoryError(explain_storage(hoard, storage))
    if not method_fits(method, hoard, storage) or method.sense < SENSE_MIN:
        raise StoryError(explain_method(method, hoard, storage))


def predict_restored_vacancy(world: World) -> dict:
    sim = world.copy()
    sim.get("hoard").attrs["place"] = sim.get("storage").id
    propagate(sim, narrate=False)
    return {
        "vacancy": sim.get("inn").meters["vacancy"],
        "guest_relief": sim.get("guest").memes["relief"],
    }


def open_fable(world: World, host: Entity, host_cfg: HostKind, hoard: HoardKind) -> None:
    world.say(
        f"In a rainy corner of the wood stood a tiny inn kept by {host.id}, "
        f"{host_cfg.title}. Over the crooked door hung a little board that said, "
        f'"vacancy," though inside the guest room there was hardly room for a whisker.'
    )
    world.say(
        f"{host.id} meant no harm. Winter was coming, and {host.pronoun('possessive')} "
        f"care had turned into {hoard.phrase}, piled right across the guest bed."
    )


def describe_hoard(world: World, host: Entity, hoard: HoardKind) -> None:
    host.memes["caution"] += 1
    world.say(
        f"{host.pronoun().capitalize()} had told {host.pronoun('object')}self that one more pile "
        f"would be wise, then one more after that, until the hoard rose like a little hill."
    )


def guest_arrives(world: World, guest: Entity, guest_cfg: GuestKind, storage: StorageKind) -> None:
    guest.meters["arrived"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At dusk {guest_cfg.arrival}. {guest.pronoun().capitalize()} looked up at the sign, "
        f"then at the warm windowlight, and asked for a dry place to sleep."
    )
    if world.get("inn").meters["vacancy"] < THRESHOLD:
        world.say(
            f"Then {guest.pronoun('possessive')} eyes fell on the crowded room, and the false "
            f"vacancy shone on the sign outside like a small accusation."
        )
    world.facts["storage_place"] = storage.arrival_place


def shame_and_choice(world: World, host: Entity, guest: Entity, storage: StorageKind) -> None:
    world.say(
        f"{host.id}'s ears drooped. {host.pronoun().capitalize()} could have said, "
        f'"The sign is old," and sent the traveler back into the storm.'
    )
    world.say(
        f"Instead {host.pronoun()} looked from the tired guest to {host.pronoun('possessive')} own hoard, "
        f"and shame gave a little push to bravery."
    )
    pred = predict_restored_vacancy(world)
    world.facts["predicted_vacancy"] = pred["vacancy"]
    world.say(
        f'{host.pronoun().capitalize()} took a breath and said, "Wait here by the fire. '
        f'I can make a true vacancy before the kettle sings."'
    )
    host.memes["bravery"] += 1
    host.attrs["chosen_risk"] = storage.risk


def brave_move(world: World, host: Entity, hoard: HoardKind, storage: StorageKind, method: Method) -> None:
    world.say(
        f"So {host.id} seized {method.phrase} and went {storage.risk}. "
        f"{host.pronoun().capitalize()} {method.use_text}, though the boards creaked and the lamp shook."
    )
    world.get("hoard").attrs["place"] = storage.id
    world.get("storage").attrs["suitable"] = True
    propagate(world, narrate=False)


def welcome_guest(world: World, host: Entity, guest: Entity, hoard: HoardKind) -> None:
    inn = world.get("inn")
    if inn.meters["vacancy"] >= THRESHOLD:
        world.say(
            f"When {host.id} came back, the guest bed was clear, the blanket lay smooth, "
            f"and now the word vacancy meant what it said."
        )
        world.say(
            f'{host.pronoun().capitalize()} bowed to {guest.id} and said, "A traveler should find rest, '
            f'not a locked door made of someone else\'s hoard."'
        )
        world.say(
            f"The traveler slept warm and safe, and {host.id} slept even better, for kindness had made "
            f"the inn larger than any pile of {hoard.label} ever could."
        )


def lesson(world: World, host: Entity, moral: str) -> None:
    world.say(
        f"From that night on, {host.id} kept stores in their proper place and the guest room ready for need."
    )
    world.say(
        f"And the innkeeper learned this lesson: {moral}. In the wood, that was counted true wisdom."
    )


def tell(
    host_cfg: HostKind,
    hoard_cfg: HoardKind,
    guest_cfg: GuestKind,
    storage_cfg: StorageKind,
    method_cfg: Method,
    host_name: str,
    moral: str,
) -> World:
    world = World()

    host = world.add(
        Entity(
            id=host_name,
            kind="character",
            type=host_cfg.type,
            label=host_cfg.label,
            role="host",
            attrs={"chosen_risk": "", "moral": moral},
        )
    )
    guest_type = "hen" if guest_cfg.id == "sparrow" else ("badger" if guest_cfg.id == "mole" else "hare")
    guest = world.add(
        Entity(
            id=guest_cfg.title.split()[-1].capitalize(),
            kind="character",
            type=guest_type,
            label=guest_cfg.label,
            role="guest",
            attrs={},
        )
    )
    inn = world.add(
        Entity(
            id="inn",
            type="inn",
            label="the little inn",
            attrs={"sign": "vacancy"},
        )
    )
    inn.meters["vacancy"] = 1.0

    world.add(
        Entity(
            id="hoard",
            type="hoard",
            label=hoard_cfg.label,
            attrs={"place": "guest_bed", "bulk": hoard_cfg.bulk},
        )
    )
    world.add(
        Entity(
            id="storage",
            type="storage",
            label=storage_cfg.label,
            attrs={"suitable": False, "need": storage_cfg.need},
        )
    )
    world.add(
        Entity(
            id="method",
            type="method",
            label=method_cfg.label,
            attrs={"sense": method_cfg.sense, "power": method_cfg.power},
        )
    )

    propagate(world, narrate=False)

    open_fable(world, host, host_cfg, hoard_cfg)
    describe_hoard(world, host, hoard_cfg)

    world.para()
    guest_arrives(world, guest, guest_cfg, storage_cfg)
    shame_and_choice(world, host, guest, storage_cfg)

    world.para()
    brave_move(world, host, hoard_cfg, storage_cfg, method_cfg)
    welcome_guest(world, host, guest, hoard_cfg)

    world.para()
    lesson(world, host, moral)

    world.facts.update(
        host=host,
        host_cfg=host_cfg,
        guest=guest,
        guest_cfg=guest_cfg,
        inn=inn,
        hoard_cfg=hoard_cfg,
        storage_cfg=storage_cfg,
        method_cfg=method_cfg,
        vacancy_initial=0.0,
        vacancy_final=inn.meters["vacancy"],
        restored=inn.meters["vacancy"] >= THRESHOLD,
        brave=host.memes["bravery"] >= THRESHOLD,
        lesson_learned=host.memes["lesson"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "hoard": [
        (
            "What is a hoard?",
            "A hoard is a pile of things someone keeps and gathers together. A hoard can be useful for later, but it can also take up too much room if it is not kept wisely.",
        )
    ],
    "vacancy": [
        (
            "What does vacancy mean?",
            "Vacancy means there is an open place ready for someone to use. At an inn, it means there is a free room or bed for a guest.",
        )
    ],
    "cellar": [
        (
            "What is a cellar for?",
            "A cellar is a cool room kept lower than the house. People use it to store food that likes cool air.",
        )
    ],
    "loft": [
        (
            "What is a loft?",
            "A loft is a high storage space near the roof. It is good for dry things that need to be kept up and away.",
        )
    ],
    "pantry": [
        (
            "What is a pantry?",
            "A pantry is a small room or cupboard where food is stored. It is a tidy place for everyday keeping.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is choosing to do the right thing even when you feel afraid. It does not mean you feel no fear; it means kindness or duty matters more.",
        )
    ],
    "inn": [
        (
            "What is an inn?",
            "An inn is a place where travelers can rest, eat, and sleep. In old stories, an inn is often a place of welcome.",
        )
    ],
}
KNOWLEDGE_ORDER = ["hoard", "vacancy", "inn", "cellar", "loft", "pantry", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    host = f["host"]
    guest = f["guest_cfg"]
    hoard = f["hoard_cfg"]
    storage = f["storage_cfg"]
    return [
        (
            f'Write a short fable for young children that uses the words "hoard" and '
            f'"vacancy" and ends with a clear lesson.'
        ),
        (
            f"Tell a woodland-inn story where {host.id} has filled a guest room with {hoard.phrase}, "
            f"a tired {guest.label} arrives in the rain, and bravery makes room for kindness."
        ),
        (
            f"Write a gentle moral tale where an innkeeper carries a winter hoard to {storage.phrase} "
            f"so the sign outside can honestly promise a vacancy."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    host = f["host"]
    guest = f["guest"]
    hoard = f["hoard_cfg"]
    storage = f["storage_cfg"]
    method = f["method_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {host.id}, a small woodland innkeeper, and {guest.id}, a tired traveler seeking shelter. Their meeting matters because the inn's guest room had been crowded by a hoard.",
        ),
        (
            "Why was the sign outside a problem?",
            f"The sign said vacancy, but the guest bed was blocked by {hoard.phrase}. That made the sign untrue, and the innkeeper felt ashamed when a real traveler arrived.",
        ),
        (
            f"Why did {host.id} need bravery?",
            f"{host.id} had to go {storage.risk} to move the hoard into its proper place. It was brave because the night was stormy and the task would have been easier to avoid.",
        ),
        (
            f"How did {host.id} make room for the traveler?",
            f"{host.pronoun().capitalize()} used {method.phrase} and carried the hoard to {storage.phrase}. Once the pile was moved away from the guest bed, the inn truly had a vacancy again.",
        ),
        (
            "How did the story end?",
            f"It ended happily: the traveler slept warm and safe, and the innkeeper felt relief instead of shame. The clear bed proved that kindness had changed the house as well as the innkeeper's heart.",
        ),
        (
            "What lesson did the innkeeper learn?",
            f"{host.id} learned that stores should be kept wisely and that a hoard must not crowd out welcome. The lesson came from seeing that honesty and kindness made the inn better than extra piles of food ever could.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"hoard", "vacancy", "inn", "bravery", f["storage_cfg"].id}
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
            shown = {k: v for k, v in e.attrs.items() if v not in ("", None, False)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible_method(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

fits(H, S, M) :- hoard(H), storage(S), method(M),
                 need(H, N), style(S, N),
                 power(M, P), bulk(H, B), P >= B,
                 not bad_path(S, M).

valid(Host, H, G, S, M) :- host(Host), hoard(H), guest(G), storage(S),
                           sensible_method(M), fits(H, S, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for host_id in HOSTS:
        lines.append(asp.fact("host", host_id))
    for hoard_id, hoard in HOARDS.items():
        lines.append(asp.fact("hoard", hoard_id))
        lines.append(asp.fact("need", hoard_id, hoard.storage_need))
        lines.append(asp.fact("bulk", hoard_id, hoard.bulk))
    for guest_id in GUESTS:
        lines.append(asp.fact("guest", guest_id))
    for storage_id, storage in STORAGES.items():
        lines.append(asp.fact("storage", storage_id))
        lines.append(asp.fact("style", storage_id, storage.need))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("power", method_id, method.power))
    lines.append(asp.fact("bad_path", "loft", "cart"))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/5.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program(show="#show sensible_method/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible_method"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a hoard, a false vacancy, and a brave act of welcome."
    )
    ap.add_argument("--host", choices=HOSTS)
    ap.add_argument("--hoard", choices=HOARDS)
    ap.add_argument("--guest", choices=GUESTS)
    ap.add_argument("--storage", choices=STORAGES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--host-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hoard and args.storage:
        hoard = HOARDS[args.hoard]
        storage = STORAGES[args.storage]
        if not storage_matches(hoard, storage):
            raise StoryError(explain_storage(hoard, storage))
    if args.method:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            hoard = HOARDS[args.hoard] if args.hoard else next(iter(HOARDS.values()))
            storage = STORAGES[args.storage] if args.storage else next(iter(STORAGES.values()))
            raise StoryError(explain_method(method, hoard, storage))

    combos = [
        combo for combo in valid_combos()
        if (args.host is None or combo[0] == args.host)
        and (args.hoard is None or combo[1] == args.hoard)
        and (args.guest is None or combo[2] == args.guest)
        and (args.storage is None or combo[3] == args.storage)
        and (args.method is None or combo[4] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    host_id, hoard_id, guest_id, storage_id, method_id = rng.choice(sorted(combos))
    host_name = args.host_name
    if not host_name:
        pool = GIRL_NAMES if rng.choice([True, False]) else BOY_NAMES
        host_name = rng.choice(pool)
    moral_options = [
        "what we hoard should not crowd out kindness",
        "a true welcome is richer than a crowded store",
        "bravery is best when it opens the door to someone else",
    ]
    return StoryParams(
        host=host_id,
        hoard=hoard_id,
        guest=guest_id,
        storage=storage_id,
        method=method_id,
        host_name=host_name,
        parenthetical_moral=rng.choice(moral_options),
    )


def generate(params: StoryParams) -> StorySample:
    _check_params(params)
    world = tell(
        host_cfg=HOSTS[params.host],
        hoard_cfg=HOARDS[params.hoard],
        guest_cfg=GUESTS[params.guest],
        storage_cfg=STORAGES[params.storage],
        method_cfg=METHODS[params.method],
        host_name=params.host_name or HOSTS[params.host].title,
        moral=params.parenthetical_moral,
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

    c_methods = set(asp_sensible_methods())
    p_methods = {m.id for m in sensible_methods()}
    if c_methods == p_methods:
        print(f"OK: sensible methods match ({sorted(c_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_methods)} python={sorted(p_methods)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story.")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke test passed for seeds 0-9.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/5.\n#show sensible_method/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        methods = asp_sensible_methods()
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(methods)}\n")
        print(f"{len(combos)} compatible (host, hoard, guest, storage, method) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:10}" for part in combo))
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
            header = (
                f"### {p.host_name or p.host}: {p.hoard} for {p.guest} "
                f"({p.storage}, {p.method})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
