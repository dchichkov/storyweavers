#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/monarch_storage_radio_misunderstanding_cautionary_myth.py
====================================================================================

A standalone story world in a small myth-like kingdom: a child helper hears a
crackling royal radio near the storage house, misunderstands the message, and
nearly lets rain ruin the kingdom's winter food. The cautionary turn is not
about wickedness but about misunderstanding: mysterious voices and half-heard
orders must be checked with a grown-up before anyone acts.

Run it
------
    python storyworlds/worlds/gpt-5.4/monarch_storage_radio_misunderstanding_cautionary_myth.py
    python storyworlds/worlds/gpt-5.4/monarch_storage_radio_misunderstanding_cautionary_myth.py --store grain --message seal_door --mistake open_door
    python storyworlds/worlds/gpt-5.4/monarch_storage_radio_misunderstanding_cautionary_myth.py --mistake light_lantern
    python storyworlds/worlds/gpt-5.4/monarch_storage_radio_misunderstanding_cautionary_myth.py --all --qa
    python storyworlds/worlds/gpt-5.4/monarch_storage_radio_misunderstanding_cautionary_myth.py --verify
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
    openable: bool = False
    sheltering: bool = False
    stores_food: bool = False
    vulnerable_to_rain: bool = False
    speaks: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "mother", "lady"}
        male = {"boy", "man", "king", "father", "lord"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def title_word(self) -> str:
        return {"queen": "queen", "king": "king", "keeper": "keeper"}.get(self.type, self.type)
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
class Store:
    id: str
    label: str
    phrase: str
    treasure: str
    vessel: str
    spoil: str
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
class Message:
    id: str
    spoken: str
    true_meaning: str
    action_needed: str
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
class Mistake:
    id: str
    text: str
    opens_storage: bool
    adds_flame_risk: bool
    sense: int
    why_bad: str
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
    fail: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_rain_enters(world: World) -> list[str]:
    out: list[str] = []
    store = world.get("storage")
    room = world.get("store_room")
    sky = world.get("sky")
    if store.meters["open"] < THRESHOLD or sky.meters["storm"] < THRESHOLD:
        return out
    sig = ("rain_enters",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["wet"] += 1
    room.meters["danger"] += 1
    out.append("__rain__")
    return out


def _r_spoil_goods(world: World) -> list[str]:
    out: list[str] = []
    store = world.get("storage")
    goods = world.get("goods")
    room = world.get("store_room")
    if store.meters["open"] < THRESHOLD or room.meters["wet"] < THRESHOLD:
        return out
    sig = ("spoil",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    goods.meters["damp"] += 1
    goods.meters["spoiled"] += 1
    for eid in ("child", "keeper"):
        world.get(eid).memes["fear"] += 1
    out.append("__spoil__")
    return out


def _r_flame_scare(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.get("lantern")
    goods = world.get("goods")
    if lantern.meters["lit"] < THRESHOLD or goods.meters["smoke_risk"] < THRESHOLD:
        return out
    sig = ("flame_scare",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["fear"] += 1
    world.get("keeper").memes["alarm"] += 1
    world.get("store_room").meters["danger"] += 1
    out.append("__flame__")
    return out


CAUSAL_RULES = [
    Rule(name="rain_enters", tag="physical", apply=_r_rain_enters),
    Rule(name="spoil_goods", tag="physical", apply=_r_spoil_goods),
    Rule(name="flame_scare", tag="physical", apply=_r_flame_scare),
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


def hazard_at_risk(message: Message, mistake: Mistake) -> bool:
    if mistake.sense < SENSE_MIN:
        return False
    if message.action_needed == "keep_closed":
        return mistake.opens_storage or mistake.adds_flame_risk
    return mistake.adds_flame_risk


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def exposure_severity(store: Store, delay: int, mistake: Mistake) -> int:
    base = 1 + delay
    if mistake.opens_storage:
        base += 1
    if store.id == "seed":
        base += 1
    return base


def is_contained(response: Response, store: Store, delay: int, mistake: Mistake) -> bool:
    return response.power >= exposure_severity(store, delay, mistake)


def predict_misreading(world: World, message: Message, mistake: Mistake) -> dict:
    sim = world.copy()
    do_mistake(sim, mistake, narrate=False)
    return {
        "wet": sim.get("store_room").meters["wet"] >= THRESHOLD,
        "spoiled": sim.get("goods").meters["spoiled"] >= THRESHOLD,
        "danger": sim.get("store_room").meters["danger"],
    }


def introduce(world: World, child: Entity, monarch: Entity, store: Store) -> None:
    world.say(
        f"In the hill-ringed kingdom where the moon was said to polish the palace roof, "
        f"the {monarch.title_word} ruled kindly, and below the stone steps stood the royal "
        f"storage house where {store.phrase} waited for winter."
    )
    world.say(
        f"{child.id}, a small palace runner with quick feet and a wondering mind, liked to carry "
        f"notes between the courtyard and the storehouse door."
    )


def set_storm(world: World) -> None:
    world.get("sky").meters["storm"] = 1
    world.say(
        "That evening a storm climbed out of the western hills. Wind shook the fig leaves, "
        "and rain tapped on tiles like many little drums."
    )


def show_radio(world: World, child: Entity) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Beside the storage house sat the palace radio, an old speaking box of brass and wood. "
        f"When it crackled, {child.id} always felt as if a hidden throat inside the mountain had begun to sing."
    )


def royal_message(world: World, monarch: Entity, message: Message) -> None:
    world.say(
        f"From the high tower, the {monarch.title_word} sent a warning through the radio: "
        f'"{message.spoken}"'
    )


def misunderstanding(world: World, child: Entity, message: Message, mistake: Mistake, keeper: Entity) -> None:
    pred = predict_misreading(world, message, mistake)
    world.facts["predicted_spoil"] = pred["spoiled"]
    world.facts["predicted_danger"] = pred["danger"]
    child.memes["confusion"] += 1
    world.say(
        f"But rain hissed on the roof, the radio buzzed, and {child.id} heard the words only halfway. "
        f"{child.pronoun().capitalize()} thought the message meant {mistake.text}."
    )
    world.say(
        f"{keeper.id}, the old storage keeper, was down the path counting hooks and rope under the eaves, "
        f"so no grown-up heard the crackling mistake."
    )


def do_mistake(world: World, mistake: Mistake, narrate: bool = True) -> None:
    if mistake.opens_storage:
        world.get("storage").meters["open"] += 1
    if mistake.adds_flame_risk:
        world.get("lantern").meters["lit"] += 1
        world.get("goods").meters["smoke_risk"] += 1
    propagate(world, narrate=narrate)


def act_on_mistake(world: World, child: Entity, store: Store, mistake: Mistake) -> None:
    child.memes["duty"] += 1
    if mistake.id == "open_door":
        world.say(
            f"Wanting to obey what {child.pronoun()} believed was a royal order, {child.id} lifted the heavy bar "
            f"and pulled the storage door open. Damp wind hurried in and touched the {store.vessel}."
        )
    elif mistake.id == "raise_shutters":
        world.say(
            f"Thinking the voice had asked for more air, {child.id} raised the storm shutters of the storage house. "
            f"Rain came slanting through the gaps and beaded on the floor stones."
        )
    elif mistake.id == "light_lantern":
        world.say(
            f"Thinking the radio wanted a signal of light, {child.id} lit the old lantern and held it near the storage shelves. "
            f"The little flame wavered too close to sacks and straw."
        )
    do_mistake(world, mistake, narrate=False)


def alarm(world: World, child: Entity, store: Store, mistake: Mistake) -> None:
    goods = world.get("goods")
    if goods.meters["spoiled"] >= THRESHOLD:
        world.say(
            f"At once the room changed. The smell of dry {store.treasure} turned heavy and cold, "
            f"and {child.id} saw dark dampness spreading where no dampness should have been."
        )
    elif mistake.adds_flame_risk:
        world.say(
            f"The lantern hissed, and one bright thread of heat licked toward the straw. "
            f"{child.id}'s brave feeling fell away like a leaf in water."
        )
    else:
        world.say(
            f"{child.id} suddenly understood that the storm had been invited too close. "
            f"The warning in the radio had not sounded like a blessing anymore."
        )
    world.say(f'"Keeper!" {child.id} cried. "Please come quickly!"')


def rescue(world: World, keeper: Entity, response: Response, store: Store) -> None:
    world.get("storage").meters["open"] = 0.0
    world.get("store_room").meters["danger"] = 0.0
    world.get("store_room").meters["wet"] = 0.0
    world.get("lantern").meters["lit"] = 0.0
    world.say(
        f"{keeper.id} came at once and {response.text.replace('{store}', store.label)}."
    )


def rescue_fail(world: World, keeper: Entity, response: Response, store: Store) -> None:
    world.get("storage").meters["open"] = 0.0
    world.get("lantern").meters["lit"] = 0.0
    world.say(
        f"{keeper.id} came running and {response.fail.replace('{store}', store.label)}."
    )


def lesson(world: World, child: Entity, keeper: Entity, monarch: Entity, store: Store, message: Message) -> None:
    child.memes["lesson"] += 1
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    keeper.memes["care"] += 1
    world.say(
        f"The keeper knelt beside {child.id} and laid a steady hand on {child.pronoun('possessive')} shoulder. "
        f'"A crackling radio is not a clear command," {keeper.pronoun()} said. '
        f'"When the {monarch.title_word} warns us, we listen carefully and ask again before we move a bar or strike a flame."'
    )
    world.say(
        f"{child.id} bowed {child.pronoun('possessive')} head. "
        f"{child.pronoun().capitalize()} understood that loyalty without understanding can still harm the kingdom."
    )
    world.say(
        f"Later the {monarch.title_word} thanked {child.pronoun('object')} for calling for help quickly, "
        f"and repeated the true message: {message.true_meaning}."
    )


def ending_safe(world: World, child: Entity, monarch: Entity, store: Store) -> None:
    child.memes["trust"] += 1
    world.say(
        f"The next dawn, the door of the storage house stood shut and strong, and the {store.vessel} "
        f"rested dry in the cool dimness."
    )
    world.say(
        f"The {monarch.title_word} had the radio cleaned and taught every runner a simple rule: "
        f'when a message crackles, ask twice and act once.'
    )
    world.say(
        f"So {child.id} grew wiser, and whenever storm clouds gathered above the palace, "
        f"{child.pronoun()} listened with both ears before {child.pronoun()} moved even a single latch."
    )


def ending_loss(world: World, child: Entity, monarch: Entity, store: Store) -> None:
    child.memes["lesson"] += 1
    child.memes["sorrow"] += 1
    world.say(
        f"By morning, part of the {store.treasure} had to be spread in the courtyard and much of it was lost. "
        f"The kingdom would eat more sparingly before spring."
    )
    world.say(
        f"The {monarch.title_word} was not cruel, yet the loss was counted by every bowl and loaf. "
        f"{child.id} never forgot how a half-heard order had reached all the way to winter."
    )
    world.say(
        f"And in that kingdom people told their children this: when voices come through wind and wire, "
        f"do not hurry to seem faithful. First be sure you have understood."
    )


def tell(
    store: Store,
    message: Message,
    mistake: Mistake,
    response: Response,
    child_name: str = "Tarin",
    child_gender: str = "boy",
    monarch_type: str = "queen",
    keeper_name: str = "Old Sena",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    monarch = world.add(Entity(id="Monarch", kind="character", type=monarch_type, role="monarch", speaks=True))
    keeper = world.add(Entity(id=keeper_name, kind="character", type="keeper", role="keeper"))
    storage = world.add(
        Entity(
            id="storage",
            type="door",
            label=f"{store.label} door",
            role="storage",
            openable=True,
            sheltering=True,
            stores_food=True,
            vulnerable_to_rain=True,
        )
    )
    goods = world.add(
        Entity(
            id="goods",
            type="food",
            label=store.treasure,
            attrs={"store_id": store.id},
            meters=defaultdict(float, {"smoke_risk": 0.0, "damp": 0.0, "spoiled": 0.0}),
        )
    )
    room = world.add(Entity(id="store_room", type="room", label="storage room"))
    sky = world.add(Entity(id="sky", type="sky", label="storm sky"))
    radio = world.add(Entity(id="radio", type="radio", label="palace radio", speaks=True))
    lantern = world.add(Entity(id="lantern", type="lantern", label="old lantern"))

    storage.meters["open"] = 0.0
    room.meters["wet"] = 0.0
    room.meters["danger"] = 0.0
    sky.meters["storm"] = 0.0
    lantern.meters["lit"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["confusion"] = 0.0
    child.memes["duty"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["lesson"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["sorrow"] = 0.0
    keeper.memes["fear"] = 0.0
    keeper.memes["alarm"] = 0.0
    keeper.memes["care"] = 0.0

    introduce(world, child, monarch, store)
    set_storm(world)
    show_radio(world, child)
    royal_message(world, monarch, message)

    world.para()
    misunderstanding(world, child, message, mistake, keeper)
    act_on_mistake(world, child, store, mistake)
    alarm(world, child, store, mistake)

    severity = exposure_severity(store, delay, mistake)
    goods.meters["severity"] = float(severity)
    if delay > 0:
        goods.meters["spoiled"] += float(delay)
    contained = is_contained(response, store, delay, mistake)

    world.para()
    if contained:
        rescue(world, keeper, response, store)
        lesson(world, child, keeper, monarch, store, message)
        world.para()
        ending_safe(world, child, monarch, store)
        outcome = "contained"
    else:
        rescue_fail(world, keeper, response, store)
        lesson(world, child, keeper, monarch, store, message)
        world.para()
        ending_loss(world, child, monarch, store)
        outcome = "lost"

    world.facts.update(
        child=child,
        monarch=monarch,
        keeper=keeper,
        store_cfg=store,
        message_cfg=message,
        mistake_cfg=mistake,
        response=response,
        delay=delay,
        outcome=outcome,
        spoiled=world.get("goods").meters["spoiled"] >= THRESHOLD,
        severity=severity,
        radio=radio,
    )
    return world


STORES = {
    "grain": Store(
        id="grain",
        label="grain store",
        phrase="barrels of barley and sacks of wheat",
        treasure="grain",
        vessel="sacks",
        spoil="turned musty and clumped",
        tags={"grain", "storage"},
    ),
    "seed": Store(
        id="seed",
        label="seed store",
        phrase="the kingdom's spring seed in clay jars",
        treasure="seed",
        vessel="clay jars",
        spoil="swelled and failed",
        tags={"seed", "storage"},
    ),
    "honey": Store(
        id="honey",
        label="honey store",
        phrase="sealed crocks of honey for feast days",
        treasure="honey",
        vessel="crocks",
        spoil="ran thin and sour",
        tags={"honey", "storage"},
    ),
}

MESSAGES = {
    "seal_door": Message(
        id="seal_door",
        spoken="Seal the storage door before the storm deepens.",
        true_meaning="the door must be shut tight against the rain",
        action_needed="keep_closed",
        tags={"radio", "storm", "ask_again"},
    ),
    "guard_seed": Message(
        id="guard_seed",
        spoken="Guard the seed room and keep the shutters fast.",
        true_meaning="the shutters must stay fastened so the seed remains dry",
        action_needed="keep_closed",
        tags={"radio", "storm", "ask_again"},
    ),
    "save_honey": Message(
        id="save_honey",
        spoken="Save the honey store from the wet night wind.",
        true_meaning="nothing should be opened, and the wet must be kept outside",
        action_needed="keep_closed",
        tags={"radio", "storm", "ask_again"},
    ),
}

MISTAKES = {
    "open_door": Mistake(
        id="open_door",
        text="the storage door should be opened at once",
        opens_storage=True,
        adds_flame_risk=False,
        sense=2,
        why_bad="Opening the door invites rain into the storage house.",
        tags={"misunderstanding", "rain"},
    ),
    "raise_shutters": Mistake(
        id="raise_shutters",
        text="the storm shutters should be raised",
        opens_storage=True,
        adds_flame_risk=False,
        sense=2,
        why_bad="Raising shutters during a storm lets wet wind strike the stores.",
        tags={"misunderstanding", "rain"},
    ),
    "light_lantern": Mistake(
        id="light_lantern",
        text="a lantern should be lit beside the shelves",
        opens_storage=False,
        adds_flame_risk=True,
        sense=2,
        why_bad="A flame near straw and sacks can frighten people and start trouble.",
        tags={"misunderstanding", "fire"},
    ),
    "sing_back": Mistake(
        id="sing_back",
        text="the radio should be answered with a song",
        opens_storage=False,
        adds_flame_risk=False,
        sense=1,
        why_bad="Singing back would not create the cautionary danger this world models.",
        tags={"misunderstanding"},
    ),
}

RESPONSES = {
    "bar_and_cover": Response(
        id="bar_and_cover",
        sense=3,
        power=4,
        text="dropped the bar back into place, threw thick waxed cloths over the nearest {store}, and pushed the wet air out with steady hands",
        fail="barred the room and covered what could be covered, but the wet had already reached too much of the {store}",
        qa_text="shut the place tight and covered the stores before more wet could reach them",
        tags={"cover", "storage"},
    ),
    "move_inside": Response(
        id="move_inside",
        sense=3,
        power=3,
        text="closed everything fast and carried the front rows of {store} deeper into the dry inner room",
        fail="closed everything fast and moved some of the {store}, but too much dampness had already crept in",
        qa_text="closed the opening and moved the stores deeper into the dry room",
        tags={"move", "storage"},
    ),
    "sweep_and_pray": Response(
        id="sweep_and_pray",
        sense=1,
        power=1,
        text="swept at the puddles with a reed broom and whispered a hurried prayer over the {store}",
        fail="swept at the puddles and prayed, but the dampness stayed in the {store}",
        qa_text="tried to sweep the wet away",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Mira", "Sela", "Neri", "Iva", "Luma", "Rin", "Tala", "Aya"]
BOY_NAMES = ["Tarin", "Ivo", "Nalin", "Perr", "Sorin", "Eran", "Davi", "Lio"]
KEEPER_NAMES = ["Old Sena", "Keeper Oren", "Mist Hal", "Aunt Brin"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in STORES:
        for mid, msg in MESSAGES.items():
            for kid, mistake in MISTAKES.items():
                if hazard_at_risk(msg, mistake):
                    combos.append((sid, mid, kid))
    return combos


@dataclass
class StoryParams:
    store: str
    message: str
    mistake: str
    response: str
    child_name: str
    child_gender: str
    monarch: str
    keeper_name: str
    delay: int = 0
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
    "radio": [
        (
            "What is a radio?",
            "A radio is a box that carries voices and sounds through the air. If the sound is crackly, it can be hard to hear the words clearly.",
        )
    ],
    "storage": [
        (
            "Why do people keep food in storage?",
            "People keep food in storage so it stays safe for later days and harder seasons. Good storage helps a whole home or kingdom eat when fresh food is scarce.",
        )
    ],
    "storm": [
        (
            "Why is rain bad for stored grain or seed?",
            "Rain can make stored grain or seed damp, moldy, and useless. Food meant for later needs to stay dry.",
        )
    ],
    "ask_again": [
        (
            "What should you do if you hear an order but are not sure what it means?",
            "You should stop and ask a trusted grown-up or the speaker to repeat it. Guessing can turn a small confusion into a big problem.",
        )
    ],
    "grain": [
        (
            "Why must grain stay dry?",
            "Dry grain keeps well and can be ground into flour later. Wet grain clumps and spoils.",
        )
    ],
    "seed": [
        (
            "Why are seeds important to protect?",
            "Seeds are not only for eating. People also plant them later, so losing them can hurt the next season too.",
        )
    ],
    "honey": [
        (
            "Why do people save honey carefully?",
            "Honey is a sweet food that can last a long time when kept sealed and clean. If water gets in, it can turn thin and sour.",
        )
    ],
    "cover": [
        (
            "Why does covering stored food help in a storm?",
            "A thick cover keeps rain and damp air off the food. The drier the food stays, the safer it is.",
        )
    ],
    "move": [
        (
            "Why move food deeper into a room during trouble?",
            "The inside of a room is often drier and safer than the doorway. Moving food away from the wet gives it more protection.",
        )
    ],
}
KNOWLEDGE_ORDER = ["radio", "storage", "storm", "ask_again", "grain", "seed", "honey", "cover", "move"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    store = f["store_cfg"]
    message = f["message_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short myth-like cautionary story for a 3-to-5-year-old that includes the words '
        f'"monarch", "storage", and "radio". A child misunderstands a crackling message about a storage house.'
    )
    if outcome == "lost":
        return [
            base,
            f"Tell a gentle but cautionary myth where {child.id} mishears a royal radio warning about the {store.label}, acts too quickly, and part of the kingdom's food is lost.",
            f'Write a story in myth style where a monarch\'s message is misunderstood, and the ending teaches children to ask again before acting.',
        ]
    return [
        base,
        f"Tell a mythic story where {child.id} mishears the radio, nearly harms the {store.label}, but calls the keeper in time and learns to check confusing orders.",
        f'Write a cautionary palace tale where a misunderstanding causes danger, then wisdom and careful listening save the day.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    monarch = f["monarch"]
    keeper = f["keeper"]
    store = f["store_cfg"]
    message = f["message_cfg"]
    mistake = f["mistake_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a palace runner, the {monarch.title_word}, and {keeper.id}, who watches the royal storage house.",
        ),
        (
            "What message came through the radio?",
            f'The radio carried the warning "{message.spoken}" from the {monarch.title_word}. It was meant to protect the {store.label} from the storm.',
        ),
        (
            f"What misunderstanding did {child.id} make?",
            f"{child.id} thought the message meant {mistake.text}. That was dangerous because {mistake.why_bad}",
        ),
    ]
    if f["outcome"] == "contained":
        qa.append(
            (
                f"How was the {store.label} saved?",
                f"{keeper.id} came quickly and {response.qa_text}. That worked because the danger was caught before too much wetness or harm spread.",
            )
        )
        qa.append(
            (
                f"What did {child.id} learn?",
                f"{child.id} learned not to guess at crackling orders from the radio. {child.pronoun().capitalize()} learned that asking again is wiser than rushing to seem obedient.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the stores dry and the lesson remembered. The kingdom kept its food, and the radio became a sign to listen carefully, not hurriedly.",
            )
        )
    else:
        qa.append(
            (
                f"What happened to the {store.treasure}?",
                f"Part of the {store.treasure} was lost after the misunderstanding. The harm reached beyond one room because stored food is meant to feed many people later.",
            )
        )
        qa.append(
            (
                f"Was {child.id} trying to be bad?",
                f"No. {child.id} was trying to be loyal, but loyalty without understanding still caused trouble. That is why the story warns children to ask before acting on a half-heard order.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly but wisely, with the kingdom counting the loss and remembering the lesson. The final image shows that a misunderstanding can travel all the way into winter.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["message_cfg"].tags) | set(f["store_cfg"].tags) | set(f["response"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (
            ("openable", ent.openable),
            ("sheltering", ent.sheltering),
            ("stores_food", ent.stores_food),
            ("vulnerable_to_rain", ent.vulnerable_to_rain),
            ("speaks", ent.speaks),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        store="grain",
        message="seal_door",
        mistake="open_door",
        response="bar_and_cover",
        child_name="Tarin",
        child_gender="boy",
        monarch="queen",
        keeper_name="Old Sena",
        delay=0,
    ),
    StoryParams(
        store="seed",
        message="guard_seed",
        mistake="raise_shutters",
        response="move_inside",
        child_name="Mira",
        child_gender="girl",
        monarch="king",
        keeper_name="Keeper Oren",
        delay=1,
    ),
    StoryParams(
        store="honey",
        message="save_honey",
        mistake="light_lantern",
        response="bar_and_cover",
        child_name="Ivo",
        child_gender="boy",
        monarch="queen",
        keeper_name="Mist Hal",
        delay=0,
    ),
    StoryParams(
        store="seed",
        message="seal_door",
        mistake="open_door",
        response="move_inside",
        child_name="Sela",
        child_gender="girl",
        monarch="queen",
        keeper_name="Aunt Brin",
        delay=2,
    ),
]


def explain_rejection(message: Message, mistake: Mistake) -> str:
    if mistake.sense < SENSE_MIN:
        return (
            f"(No story: '{mistake.id}' is too weak or harmless for this cautionary world. "
            f"Pick a misunderstanding that actually creates danger around storage.)"
        )
    return (
        f"(No story: hearing '{message.spoken}' as '{mistake.text}' does not create the kind "
        f"of storage danger this world models.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is too weak for a sensible cautionary story "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "contained" if is_contained(RESPONSES[params.response], STORES[params.store], params.delay, MISTAKES[params.mistake]) else "lost"


ASP_RULES = r"""
hazard(Msg, Mis) :- message(Msg), mistake(Mis), action_needed(Msg, keep_closed), opens_storage(Mis).
hazard(Msg, Mis) :- message(Msg), mistake(Mis), action_needed(Msg, keep_closed), adds_flame_risk(Mis).
sensible_response(R) :- response(R), sense(R, S), sense_min(Mn), S >= Mn.
valid(Store, Msg, Mis) :- store(Store), message(Msg), mistake(Mis), mistake_sense(Mis, S), sense_min(Mn), S >= Mn, hazard(Msg, Mis).

base_severity(Store, 1) :- store(Store), not seed_store(Store).
base_severity(Store, 2) :- seed_store(Store).

severity(Store, Mis, Delay, V) :- valid(Store, _, Mis), base_severity(Store, B), delay(Delay),
                                  opens_storage(Mis), V = B + Delay + 1.
severity(Store, Mis, Delay, V) :- valid(Store, _, Mis), base_severity(Store, B), delay(Delay),
                                  not opens_storage(Mis), V = B + Delay.

contained :- chosen_response(R), chosen_store(Store), chosen_mistake(Mis), delay(Delay),
             power(R, P), severity(Store, Mis, Delay, V), P >= V.
outcome(contained) :- contained.
outcome(lost) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, store in STORES.items():
        lines.append(asp.fact("store", sid))
        if sid == "seed":
            lines.append(asp.fact("seed_store", sid))
    for mid, msg in MESSAGES.items():
        lines.append(asp.fact("message", mid))
        lines.append(asp.fact("action_needed", mid, msg.action_needed))
    for kid, mistake in MISTAKES.items():
        lines.append(asp.fact("mistake", kid))
        lines.append(asp.fact("mistake_sense", kid, mistake.sense))
        if mistake.opens_storage:
            lines.append(asp.fact("opens_storage", kid))
        if mistake.adds_flame_risk:
            lines.append(asp.fact("adds_flame_risk", kid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
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

    model = asp.one_model(asp_program("", "#show sensible_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_response"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_store", params.store),
            asp.fact("chosen_mistake", params.mistake),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sens = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sens)} python={sorted(py_sens)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke-test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth-like cautionary story world: a child mishears a royal radio warning and nearly harms the palace storage."
    )
    ap.add_argument("--store", choices=STORES)
    ap.add_argument("--message", choices=MESSAGES)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--monarch", choices=["queen", "king"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_child(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response is not None and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    if args.message is not None and args.mistake is not None:
        msg = MESSAGES[args.message]
        mis = MISTAKES[args.mistake]
        if not hazard_at_risk(msg, mis):
            raise StoryError(explain_rejection(msg, mis))

    combos = [
        combo
        for combo in valid_combos()
        if (args.store is None or combo[0] == args.store)
        and (args.message is None or combo[1] == args.message)
        and (args.mistake is None or combo[2] == args.mistake)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    store, message, mistake = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_name, child_gender = _pick_child(rng)
    monarch = args.monarch or rng.choice(["queen", "king"])
    keeper_name = rng.choice(KEEPER_NAMES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        store=store,
        message=message,
        mistake=mistake,
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        monarch=monarch,
        keeper_name=keeper_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        store = STORES[params.store]
        message = MESSAGES[params.message]
        mistake = MISTAKES[params.mistake]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not hazard_at_risk(message, mistake):
        raise StoryError(explain_rejection(message, mistake))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        store=store,
        message=message,
        mistake=mistake,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        monarch_type=params.monarch,
        keeper_name=params.keeper_name,
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
        print(asp_program("", "#show valid/3.\n#show sensible_response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (store, message, mistake) combos:\n")
        for store, message, mistake in combos:
            print(f"  {store:8} {message:10} {mistake}")
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
                f"### {p.child_name}: {p.store}, {p.message}, {p.mistake} "
                f"({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
