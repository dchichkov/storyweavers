#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/inlet_humor_fable.py
===============================================

A standalone story world for a humorous little fable at an inlet.

Premise
-------
Small animals gather by an inlet where the tide goes out and comes back in.
One animal spots a tempting thing on a sandbar and grows proudly certain that
the quickest, silliest plan must also be the best. A friend warns that the inlet
changes fast. If the proud animal chooses a method that truly suits the object,
the day ends in cheerful success; if not, there is a muddy, funny comeuppance
and a gentle lesson about listening before boasting.

The world model tracks:
- physical meters like muddy, dropped, soaked, delivered, stranded
- emotional memes like pride, caution, embarrassment, gratitude, joy

Reasonableness constraint
-------------------------
Not every carrying method honestly works for every object.

- rolling only works for round objects
- balancing on the head only works for light objects
- towing only works for items with a handle or cord
- a reed raft works for floatable objects and is the safest fix

The storyworld refuses invalid explicit choices with a legible StoryError.
It also includes an inline ASP twin for parity checks.

Run it
------
python storyworlds/worlds/gpt-5.4/inlet_humor_fable.py
python storyworlds/worlds/gpt-5.4/inlet_humor_fable.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/inlet_humor_fable.py --all
python storyworlds/worlds/gpt-5.4/inlet_humor_fable.py --verify
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
        female = {"hen", "duck", "mother", "woman"}
        male = {"fox", "toad", "father", "man"}
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
class Setting:
    id: str
    inlet_name: str
    shore_detail: str
    tide_voice: str
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
class Cargo:
    id: str
    label: str
    phrase: str
    goal: str
    shape: str
    weight: str
    floats: bool
    has_handle: bool
    comic_noise: str
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
    success_text: str
    fail_text: str
    qa_text: str
    safe: bool = False
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
class TraitStyle:
    id: str
    boast: str
    warning_push: str
    climb_image: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {"predicted_trouble": False, "prediction_reason": ""}

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
        clone = World(self.setting)
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


def _r_muddy(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["slipping"] < THRESHOLD:
        return out
    sig = ("muddy", "hero")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["muddy"] += 1
    hero.memes["embarrassment"] += 1
    out.append("__mud__")
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    cargo = world.get("cargo")
    if hero.meters["slipping"] < THRESHOLD or cargo.meters["secured"] >= THRESHOLD:
        return out
    sig = ("drop", cargo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["dropped"] += 1
    cargo.meters["muddy"] += 1
    hero.memes["embarrassment"] += 1
    out.append("__drop__")
    return out


def _r_tide(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["slipping"] < THRESHOLD and hero.meters["dawdling"] < THRESHOLD:
        return out
    sig = ("tide", "hero")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("inlet").meters["water_high"] += 1
    hero.meters["soaked"] += 1
    hero.memes["alarm"] += 1
    out.append("__tide__")
    return out


CAUSAL_RULES = [
    Rule(name="muddy", tag="physical", apply=_r_muddy),
    Rule(name="drop", tag="physical", apply=_r_drop),
    Rule(name="tide", tag="physical", apply=_r_tide),
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


def method_works(cargo: Cargo, method: Method) -> bool:
    if method.id == "roll":
        return cargo.shape == "round"
    if method.id == "balance":
        return cargo.weight == "light"
    if method.id == "tow":
        return cargo.has_handle
    if method.id == "raft":
        return cargo.floats
    return False


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for cargo_id, cargo in CARGOES.items():
            for method_id, method in METHODS.items():
                if method_works(cargo, method) and method.sense >= SENSE_MIN:
                    combos.append((setting_id, cargo_id, method_id))
    return combos


def predict_trouble(world: World, cargo: Cargo, method: Method) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    c_ent = sim.get("cargo")
    if not method_works(cargo, method):
        if method.id == "roll":
            reason = "The thing was not round, so it would stop and flop into the mud."
        elif method.id == "balance":
            reason = "The load was too heavy for a neat head-balancing trick."
        elif method.id == "tow":
            reason = "There was nothing to tie a cord to, so towing would fail."
        else:
            reason = "The inlet water would not kindly hold up that load."
        hero.meters["slipping"] += 1
        hero.meters["dawdling"] += 1
        propagate(sim, narrate=False)
        return {"trouble": True, "reason": reason}
    if method.id == "balance":
        return {"trouble": False, "reason": "The load was light enough to carry carefully."}
    if method.id == "roll":
        return {"trouble": False, "reason": "A round thing could roll over the firm sand."}
    if method.id == "tow":
        return {"trouble": False, "reason": "The handle gave the rope a proper place to hold."}
    if method.id == "raft":
        return {"trouble": False, "reason": "The little raft would float it over the inlet."}
    return {"trouble": True, "reason": "The plan made no sense in this little world."}


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"At {setting.inlet_name}, where {setting.shore_detail}, {hero.id} and {friend.id} "
        f"came down to the edge of the inlet to look for something lucky."
    )
    world.say(
        f"The tide made a soft sound in the reeds, as if it were saying, "
        f'"{setting.tide_voice}"'
    )


def discover(world: World, hero: Entity, cargo: Cargo) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"Soon {hero.id} spotted {cargo.phrase} resting on a wet sandbar. "
        f'"If I bring home {cargo.goal}," {hero.pronoun()} said, '
        f'"everyone will know I have the best nose on the whole shore."'
    )
    world.say(f"The {cargo.label} seemed to answer with a tiny {cargo.comic_noise}.")


def brag(world: World, hero: Entity, cargo: Cargo, trait_style: TraitStyle, method: Method) -> None:
    world.say(
        f"{hero.id} puffed up and announced {trait_style.boast} "
        f'"I shall fetch the {cargo.label} by {method.label}, and I shall do it without even wrinkling a whisker."'
    )


def warn(world: World, hero: Entity, friend: Entity, cargo: Cargo, method: Method, trait_style: TraitStyle) -> None:
    pred = predict_trouble(world, cargo, method)
    world.facts["predicted_trouble"] = pred["trouble"]
    world.facts["prediction_reason"] = pred["reason"]
    friend.memes["caution"] += 1
    extra = trait_style.warning_push
    if pred["trouble"]:
        world.say(
            f'{friend.id} looked from the sandbar to the inlet and said, '
            f'"Boasts are light, but real things have weight. {pred["reason"]} '
            f'{extra}"'
        )
    else:
        world.say(
            f'{friend.id} watched the water and said, '
            f'"If you go carefully, this may work. Still, the inlet likes to laugh at hurry, '
            f'so mind your feet."'
        )


def choose_proudly(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'But {hero.id} gave a grand sniff. "Advice is a fine coat for a cold day," '
        f'{hero.pronoun()} said, "but I am warm with my own cleverness."'
    )


def succeed(world: World, hero: Entity, friend: Entity, cargo_ent: Entity, cargo: Cargo, method: Method) -> None:
    cargo_ent.meters["secured"] += 1
    cargo_ent.meters["delivered"] += 1
    hero.memes["gratitude"] += 1
    hero.memes["joy"] += 1
    friend.memes["relief"] += 1
    world.say(method.success_text.format(cargo=cargo.label, goal=cargo.goal, hero=hero.id))
    world.say(
        f"When {hero.id} reached the near shore, {friend.id} laughed kindly and bowed. "
        f'"Well done," {friend.pronoun()} said. "Quick feet are good, but careful feet get home."'
    )


def fail(world: World, hero: Entity, friend: Entity, cargo_ent: Entity, cargo: Cargo, method: Method) -> None:
    hero.meters["slipping"] += 1
    hero.meters["dawdling"] += 1
    propagate(world, narrate=False)
    world.say(method.fail_text.format(cargo=cargo.label, goal=cargo.goal, hero=hero.id))
    if cargo_ent.meters["dropped"] >= THRESHOLD:
        world.say(
            f"The {cargo.label} landed with a comic plop, and a stripe of mud crossed "
            f"{hero.id}'s nose as neatly as if a painter-crab had done it on purpose."
        )
    if hero.meters["soaked"] >= THRESHOLD:
        world.say(
            f"Then the inlet, which had been listening all along, sent back a lick of water "
            f"around {hero.id}'s ankles. Pride grew suddenly quieter."
        )
    hero.memes["embarrassment"] += 1
    friend.memes["concern"] += 1


def rescue_with_raft(world: World, hero: Entity, friend: Entity, cargo_ent: Entity, cargo: Cargo) -> None:
    cargo_ent.meters["secured"] += 1
    cargo_ent.meters["delivered"] += 1
    hero.meters["stranded"] = 0.0
    hero.memes["gratitude"] += 1
    hero.memes["embarrassment"] += 1
    hero.memes["joy"] += 1
    friend.memes["relief"] += 1
    world.say(
        f'{friend.id} did not waste time saying "I told you so." Instead, {friend.pronoun()} '
        f'pulled a flat bundle of reeds from the bank, tied it into a little raft, and slid it over the water.'
    )
    world.say(
        f'Together they settled the {cargo.label} on top, and the tiny craft bobbed across the inlet as pleased as a duck. '
        f'Even {hero.id} had to laugh.'
    )
    world.say(
        f"In a moment they reached shore with {cargo.goal}, the mud still on {hero.id}'s nose and the lesson already in {hero.pronoun('possessive')} heart."
    )


def ending_success(world: World, hero: Entity, friend: Entity, cargo: Cargo, trait_style: TraitStyle) -> None:
    world.say(
        f"That evening {hero.id} shared {cargo.goal} instead of bragging over it, and {friend.id} noticed "
        f"that {trait_style.climb_image} no longer seemed to need an audience."
    )
    world.say(
        "So the reeds whispered what everyone at the inlet could understand: a little pride may strut ahead, "
        "but good sense carries supper home."
    )


def ending_funny_lesson(world: World, hero: Entity, friend: Entity, cargo: Cargo) -> None:
    world.say(
        f"That evening {hero.id} washed mud from {hero.pronoun('possessive')} whiskers and shared {cargo.goal} with {friend.id} first."
    )
    world.say(
        "From then on, whenever a boast grew too tall at the inlet, someone would ask whether it needed a reed raft. "
        "Everybody would smile, even the one doing the boasting."
    )


def tell(
    setting: Setting,
    cargo: Cargo,
    method: Method,
    hero_name: str = "Rill",
    hero_type: str = "fox",
    friend_name: str = "Moss",
    friend_type: str = "duck",
    trait_id: str = "grand",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        label=hero_name,
        attrs={"trait_id": trait_id},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_type,
        role="friend",
        label=friend_name,
        attrs={},
    ))
    inlet = world.add(Entity(
        id="inlet",
        kind="thing",
        type="place",
        label="the inlet",
        attrs={"setting": setting.id},
    ))
    cargo_ent = world.add(Entity(
        id="cargo",
        kind="thing",
        type="cargo",
        label=cargo.label,
        attrs={
            "shape": cargo.shape,
            "weight": cargo.weight,
            "floats": cargo.floats,
            "has_handle": cargo.has_handle,
        },
    ))

    hero.memes["pride"] = 2.0
    hero.memes["joy"] = 0.0
    hero.memes["defiance"] = 0.0
    hero.memes["gratitude"] = 0.0
    hero.memes["embarrassment"] = 0.0
    hero.memes["alarm"] = 0.0
    friend.memes["caution"] = 1.0
    friend.memes["relief"] = 0.0
    friend.memes["concern"] = 0.0
    inlet.meters["water_high"] = 0.0
    cargo_ent.meters["secured"] = 0.0
    cargo_ent.meters["delivered"] = 0.0
    cargo_ent.meters["dropped"] = 0.0
    cargo_ent.meters["muddy"] = 0.0

    style = TRAIT_STYLES[trait_id]

    introduce(world, hero, friend, setting)
    discover(world, hero, cargo)

    world.para()
    brag(world, hero, cargo, style, method)
    warn(world, hero, friend, cargo, method, style)
    choose_proudly(world, hero)

    world.para()
    if method_works(cargo, method):
        succeed(world, hero, friend, cargo_ent, cargo, method)
        world.para()
        ending_success(world, hero, friend, cargo, style)
        outcome = "success"
    else:
        fail(world, hero, friend, cargo_ent, cargo, method)
        world.para()
        rescue_with_raft(world, hero, friend, cargo_ent, cargo)
        world.para()
        ending_funny_lesson(world, hero, friend, cargo)
        outcome = "rescued"

    world.facts.update(
        hero=hero,
        friend=friend,
        inlet=inlet,
        setting=setting,
        cargo_cfg=cargo,
        cargo=cargo_ent,
        method=method,
        outcome=outcome,
        worked=method_works(cargo, method),
        moral="Good sense is quieter than pride, but it gets home first.",
    )
    return world


SETTINGS = {
    "reed_bend": Setting(
        id="reed_bend",
        inlet_name="Reed-Bend Inlet",
        shore_detail="silver reeds leaned over the water and fiddler crabs waved one bright claw each",
        tide_voice="Do not trust a quiet shore for too long.",
        tags={"inlet", "tide", "reeds"},
    ),
    "shell_nook": Setting(
        id="shell_nook",
        inlet_name="Shell-Nook Inlet",
        shore_detail="smooth stones shone like wet buttons and tiny fish winked in the shallows",
        tide_voice="I arrive smiling and leave your paws wet.",
        tags={"inlet", "tide", "stones"},
    ),
    "gull_cove": Setting(
        id="gull_cove",
        inlet_name="Gull-Cove Inlet",
        shore_detail="wind bent the grass and a few gulls stood about as if judging everybody",
        tide_voice="Hurry if you must, but I never hurry.",
        tags={"inlet", "tide", "gulls"},
    ),
}

CARGOES = {
    "gourd": Cargo(
        id="gourd",
        label="gourd",
        phrase="a round green gourd",
        goal="a fine stew-pot prize",
        shape="round",
        weight="heavy",
        floats=True,
        has_handle=False,
        comic_noise="bonk",
        tags={"round", "raft", "food"},
    ),
    "berry_pail": Cargo(
        id="berry_pail",
        label="berry pail",
        phrase="a little pail of berries with a bent wire handle",
        goal="berries for supper",
        shape="upright",
        weight="light",
        floats=False,
        has_handle=True,
        comic_noise="plink",
        tags={"berries", "handle", "food"},
    ),
    "cabbage": Cargo(
        id="cabbage",
        label="cabbage",
        phrase="a fat cabbage wrapped in pale leaves",
        goal="a cabbage for the cooking fire",
        shape="round",
        weight="light",
        floats=False,
        has_handle=False,
        comic_noise="thump",
        tags={"round", "light", "food"},
    ),
    "kettle": Cargo(
        id="kettle",
        label="kettle",
        phrase="a black kettle with a sturdy handle",
        goal="a kettle for the marsh tea",
        shape="upright",
        weight="heavy",
        floats=False,
        has_handle=True,
        comic_noise="clink",
        tags={"handle", "heavy"},
    ),
}

METHODS = {
    "roll": Method(
        id="roll",
        label="rolling it over the sand",
        sense=2,
        success_text="{hero} nudged the {cargo} along the firm sand, and it trundled across with surprising dignity.",
        fail_text="{hero} tried rolling the {cargo}, but it wobbled, sulked, and refused to behave like a wheel.",
        qa_text="rolled it over the sand",
        safe=False,
        tags={"roll", "careful"},
    ),
    "balance": Method(
        id="balance",
        label="balancing it on the head",
        sense=2,
        success_text="{hero} settled the {cargo} on top of {hero}'s head and tiptoed across so solemnly that even the gulls forgot to laugh.",
        fail_text="{hero} hoisted the {cargo} onto {hero}'s head, took three grand steps, and discovered that grand steps are not the same as steady ones.",
        qa_text="balanced it on the head",
        safe=False,
        tags={"balance", "comedy"},
    ),
    "tow": Method(
        id="tow",
        label="towing it with a cord",
        sense=2,
        success_text="{hero} looped a cord around the {cargo} and towed it behind like a very stubborn parade float.",
        fail_text="{hero} fetched a cord and tried towing the {cargo}, but there was nowhere sensible for the cord to hold.",
        qa_text="towed it with a cord",
        safe=False,
        tags={"tow", "comedy"},
    ),
    "raft": Method(
        id="raft",
        label="floating it on a reed raft",
        sense=3,
        success_text="{hero} tucked the {cargo} onto a little reed raft and guided it over the water while the inlet rocked it gently.",
        fail_text="{hero} pushed the reed raft out, but the {cargo} would not float kindly and slipped off at once.",
        qa_text="floated it on a reed raft",
        safe=True,
        tags={"raft", "safe"},
    ),
}

TRAIT_STYLES = {
    "grand": TraitStyle(
        id="grand",
        boast="with the voice of someone announcing a parade,",
        warning_push="Do not let your pride put on stilts.",
        climb_image="the hero's pride",
    ),
    "showy": TraitStyle(
        id="showy",
        boast="while arranging his whiskers as though they were royal banners,",
        warning_push="A plan is not improved merely because it sounds fancy.",
        climb_image="the little drum of pride",
    ),
    "pompous": TraitStyle(
        id="pompous",
        boast="like a magistrate judging a puddle,",
        warning_push="An inlet is not persuaded by speeches.",
        climb_image="that old puff of pride",
    ),
}

FOX_NAMES = ["Rill", "Pip", "Tumble", "Bram", "Nip"]
TOAD_NAMES = ["Moss", "Plop", "Peb", "Nettle", "Mudger"]
DUCK_NAMES = ["Moss", "Wade", "Feather", "Paddle", "Nip"]
HEN_NAMES = ["Dot", "Brisk", "Penny", "Tilda", "Peck"]

HERO_TYPES = ["fox", "toad"]
FRIEND_TYPES = ["duck", "hen"]


@dataclass
class StoryParams:
    setting: str
    cargo: str
    method: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
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
    "inlet": [
        (
            "What is an inlet?",
            "An inlet is a narrow place where water from the sea or a large river reaches into the land. The water there can rise and fall with the tide."
        )
    ],
    "tide": [
        (
            "Why does the water in an inlet change?",
            "The tide makes water come in and go out. A place that looks easy to cross at one moment can be wet and deep later."
        )
    ],
    "raft": [
        (
            "What is a raft?",
            "A raft is a simple floating platform made from things like reeds or wood tied together. It can help carry something across water."
        )
    ],
    "float": [
        (
            "Why do some things float and others sink?",
            "Some things stay up on the water because they are light for their size or shaped in a way that water can hold them up. Heavier or denser things may sink."
        )
    ],
    "roll": [
        (
            "Why do round things roll better?",
            "A round thing can keep turning as it moves, so it rolls along the ground. A flat-sided thing bumps and stops instead."
        )
    ],
    "handle": [
        (
            "Why is a handle useful?",
            "A handle gives your paw or a rope a safe place to hold. Without one, pulling something can be clumsy and slippery."
        )
    ],
    "boast": [
        (
            "What is boasting?",
            "Boasting is talking too proudly about what you can do. It can make you forget to listen to sensible advice."
        )
    ],
}
KNOWLEDGE_ORDER = ["inlet", "tide", "raft", "float", "roll", "handle", "boast"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cargo = f["cargo_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    if outcome == "success":
        return [
            f'Write a funny fable for a young child set at an inlet, where a proud {hero.type} tries {method.label} to bring home a {cargo.label}.',
            f'Write a short animal fable with gentle humor, an inlet, a warning about pride, and a happy ending where careful action really works.',
            f'Write a TinyStories-style fable using the word "inlet" and showing that boasting is louder than wisdom, but not stronger.',
        ]
    return [
        f'Write a funny little fable set at an inlet, where a proud {hero.type} chooses a silly plan for a {cargo.label}, slips, and must be helped.',
        f'Write a child-friendly animal story with humor and a fable-like moral: pride rushes first, but good sense rescues the day.',
        f'Write a short fable that includes the word "inlet", a comic muddy mishap, and a gentle lesson about listening.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    cargo = f["cargo_cfg"]
    method = f["method"]
    setting = f["setting"]
    outcome = f["outcome"]
    cargo_ent = f["cargo"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a proud little {hero.type}, and {friend.id}, a watchful {friend.type}. They were together at {setting.inlet_name}."
        ),
        (
            f"What did {hero.id} find at the inlet?",
            f"{hero.id} found {cargo.phrase} on a wet sandbar. {hero.pronoun().capitalize()} wanted to bring it home as {cargo.goal}."
        ),
        (
            f"Why did {friend.id} warn {hero.id}?",
            f"{friend.id} warned {hero.id} because the inlet changes quickly and the plan might not suit the thing being carried. {world.facts['prediction_reason']}"
        ),
    ]
    if outcome == "success":
        qa.append(
            (
                f"How did {hero.id} get the {cargo.label} home?",
                f"{hero.pronoun().capitalize()} {method.qa_text} and made it across safely. The plan worked because this kind of object honestly fit that method."
            )
        )
        qa.append(
            (
                f"What changed in {hero.id} by the end?",
                f"{hero.id} stopped boasting so much and shared the prize instead. Success still came, but it was kinder and quieter after the warning."
            )
        )
    else:
        mishap = []
        if hero.meters["muddy"] >= THRESHOLD:
            mishap.append(f"{hero.id} got muddy")
        if hero.meters["soaked"] >= THRESHOLD:
            mishap.append(f"the tide soaked {hero.pronoun('object')}")
        if cargo_ent.meters["dropped"] >= THRESHOLD:
            mishap.append(f"the {cargo.label} was dropped")
        qa.append(
            (
                f"What went wrong when {hero.id} tried the plan?",
                f"The plan failed because the method did not suit the {cargo.label}. As a result, " + ", and ".join(mishap) + "."
            )
        )
        qa.append(
            (
                f"How did {friend.id} help after the mishap?",
                f"{friend.id} made a little reed raft and helped carry the {cargo.label} over the inlet. That rescue worked because the raft matched the water and the load much better."
            )
        )
        qa.append(
            (
                "What lesson did the story teach?",
                f"It taught that pride can make a creature rush into a foolish plan. Listening first would have spared the muddy trouble."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"inlet", "tide", "boast"}
    method = world.facts["method"]
    cargo = world.facts["cargo_cfg"]
    if method.id == "raft" or world.facts["outcome"] == "rescued":
        tags.add("raft")
    if cargo.floats:
        tags.add("float")
    if cargo.shape == "round":
        tags.add("roll")
    if cargo.has_handle:
        tags.add("handle")
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v is False}
            bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="reed_bend",
        cargo="cabbage",
        method="roll",
        hero_name="Rill",
        hero_type="fox",
        friend_name="Moss",
        friend_type="duck",
        trait="grand",
    ),
    StoryParams(
        setting="shell_nook",
        cargo="berry_pail",
        method="tow",
        hero_name="Pip",
        hero_type="fox",
        friend_name="Dot",
        friend_type="hen",
        trait="showy",
    ),
    StoryParams(
        setting="gull_cove",
        cargo="gourd",
        method="raft",
        hero_name="Tumble",
        hero_type="toad",
        friend_name="Wade",
        friend_type="duck",
        trait="pompous",
    ),
    StoryParams(
        setting="reed_bend",
        cargo="kettle",
        method="balance",
        hero_name="Bram",
        hero_type="fox",
        friend_name="Penny",
        friend_type="hen",
        trait="grand",
    ),
    StoryParams(
        setting="shell_nook",
        cargo="berry_pail",
        method="roll",
        hero_name="Nip",
        hero_type="toad",
        friend_name="Moss",
        friend_type="duck",
        trait="showy",
    ),
]


def explain_rejection(cargo: Cargo, method: Method) -> str:
    if method.id == "roll":
        return (
            f"(No story: rolling only makes sense for a round object, and the {cargo.label} is not round enough for that.)"
        )
    if method.id == "balance":
        return (
            f"(No story: balancing on the head is only reasonable for a light load, and the {cargo.label} is too heavy.)"
        )
    if method.id == "tow":
        return (
            f"(No story: towing with a cord needs a handle or another good place to tie on, and the {cargo.label} has none.)"
        )
    if method.id == "raft":
        return (
            f"(No story: the reed raft method only works here for something that will float, and the {cargo.label} would not.)"
        )
    return "(No story: this carrying plan is not reasonable in this world.)"


ASP_RULES = r"""
works(C, roll)    :- cargo(C), shape(C, round).
works(C, balance) :- cargo(C), weight(C, light).
works(C, tow)     :- cargo(C), has_handle(C).
works(C, raft)    :- cargo(C), floats(C).

sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
valid(S, C, M) :- setting(S), cargo(C), method(M), works(C, M), sensible(M).

worked :- chosen_cargo(C), chosen_method(M), works(C, M).
outcome(success) :- worked.
outcome(rescued) :- not worked.

#show valid/3.
#show sensible/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("shape", cid, cargo.shape))
        lines.append(asp.fact("weight", cid, cargo.weight))
        if cargo.floats:
            lines.append(asp.fact("floats", cid))
        if cargo.has_handle:
            lines.append(asp.fact("has_handle", cid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
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
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_cargo", params.cargo),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    cargo = CARGOES[params.cargo]
    method = METHODS[params.method]
    return "success" if method_works(cargo, method) else "rescued"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a humorous inlet fable about pride, mud, and good sense."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
    ap.add_argument("--trait", choices=TRAIT_STYLES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def _pick_name(rng: random.Random, kind: str, avoid: str = "") -> str:
    if kind == "fox":
        pool = [n for n in FOX_NAMES if n != avoid]
    elif kind == "toad":
        pool = [n for n in TOAD_NAMES if n != avoid]
    elif kind == "duck":
        pool = [n for n in DUCK_NAMES if n != avoid]
    else:
        pool = [n for n in HEN_NAMES if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.method:
        cargo = CARGOES[args.cargo]
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            raise StoryError(
                f"(No story: method '{args.method}' is below the common-sense threshold for this world.)"
            )
        # explicit invalid choices are refused
        if not method_works(cargo, method):
            raise StoryError(explain_rejection(cargo, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cargo_id, method_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    friend_type = args.friend_type or rng.choice(FRIEND_TYPES)
    hero_name = _pick_name(rng, hero_type)
    friend_name = _pick_name(rng, friend_type, avoid=hero_name)
    trait = args.trait or rng.choice(sorted(TRAIT_STYLES))
    return StoryParams(
        setting=setting_id,
        cargo=cargo_id,
        method=method_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.cargo not in CARGOES:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.trait not in TRAIT_STYLES:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.hero_type not in HERO_TYPES:
        raise StoryError(f"(Unknown hero type: {params.hero_type})")
    if params.friend_type not in FRIEND_TYPES:
        raise StoryError(f"(Unknown friend type: {params.friend_type})")

    setting = SETTINGS[params.setting]
    cargo = CARGOES[params.cargo]
    method = METHODS[params.method]
    world = tell(
        setting=setting,
        cargo=cargo,
        method=method,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        trait_id=params.trait,
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible())
    p_sens = {m.id for m in sensible_methods()}
    if c_sens == p_sens:
        print(f"OK: sensible methods match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(60):
        try:
            args = build_parser().parse_args([])
            p = resolve_params(args, random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving params for seed {s}.")
            break

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python outcome on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover
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
        sens = asp_sensible()
        print(f"sensible methods: {', '.join(sens)}\n")
        print(f"{len(combos)} valid (setting, cargo, method) combos:\n")
        for setting_id, cargo_id, method_id in combos:
            print(f"  {setting_id:11} {cargo_id:10} {method_id}")
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
            header = f"### {p.hero_name}: {p.cargo} by {p.method} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
