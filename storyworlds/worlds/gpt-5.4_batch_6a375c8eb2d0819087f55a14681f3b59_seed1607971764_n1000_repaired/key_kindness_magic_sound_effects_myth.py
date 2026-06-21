#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/key_kindness_magic_sound_effects_myth.py
===================================================================

A standalone story world for a tiny mythic domain: a child meets a small
guardian in a sacred place, chooses kindness first, receives a magic key, and
opens a locked blessing for the village.

This world is built to generate a few strong, reasoned variants rather than a
huge soup of weak substitutions. The core promise is always the same:

    need in the world -> locked sacred thing -> small creature in trouble
    -> child helps kindly -> creature gives a magic key
    -> key opens blessing -> ending image proves the world changed

The inline ASP twin mirrors the reasonableness gate:
- a creature/problem pair is only valid when the creature can actually be helped
  by that kindness act;
- a key must match the lock it can open.

Run it
------
    python storyworlds/worlds/gpt-5.4/key_kindness_magic_sound_effects_myth.py
    python storyworlds/worlds/gpt-5.4/key_kindness_magic_sound_effects_myth.py --place grove --creature dove --act untangle --lock cloud_gate
    python storyworlds/worlds/gpt-5.4/key_kindness_magic_sound_effects_myth.py --creature carp --act bandage
    python storyworlds/worlds/gpt-5.4/key_kindness_magic_sound_effects_myth.py --all
    python storyworlds/worlds/gpt-5.4/key_kindness_magic_sound_effects_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/key_kindness_magic_sound_effects_myth.py --verify
"""

from __future__ import annotations

import argparse
import copy
import contextlib
import io
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
    kind: str = "thing"             # "character" | "thing" | "spirit"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "goddess", "mother"}
        male = {"boy", "man", "god", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    path: str
    sky: str
    ending_image: str
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
class Need:
    id: str
    village_line: str
    hope_line: str
    result_line: str
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
class Lock:
    id: str
    label: str
    phrase: str
    sound: str
    blessing: str
    opens_need: str
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
class Creature:
    id: str
    label: str
    phrase: str
    problem: str
    hurt_part: str
    cry: str
    gratitude: str
    gift_key: str
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
class KindAct:
    id: str
    verb: str
    line: str
    fixes: set[str]
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
class MagicKey:
    id: str
    label: str
    phrase: str
    shine: str
    opens: str
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


def _r_helped_creature(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    creature = world.get("creature")
    act: KindAct = world.facts["act_cfg"]
    if creature.attrs.get("problem") not in act.fixes:
        return out
    if child.meters["kind_help"] < THRESHOLD:
        return out
    sig = ("helped", creature.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.meters["relieved"] += 1
    creature.memes["trust"] += 1
    child.memes["kindness"] += 1
    out.append("__helped__")
    return out


def _r_receive_key(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    key = world.get("key")
    if creature.meters["relieved"] < THRESHOLD:
        return out
    sig = ("key", key.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    key.meters["revealed"] += 1
    key.memes["magic"] += 1
    out.append("__key__")
    return out


def _r_unlock(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    key = world.get("key")
    sacred = world.get("sacred")
    if key.meters["revealed"] < THRESHOLD or child.meters["used_key"] < THRESHOLD:
        return out
    if key.attrs.get("opens") != sacred.attrs.get("lock_id"):
        return out
    sig = ("unlocked", sacred.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sacred.meters["open"] += 1
    world.get("village").meters["blessed"] += 1
    child.memes["awe"] += 1
    child.memes["joy"] += 1
    out.append("__open__")
    return out


CAUSAL_RULES = [
    Rule(name="helped_creature", tag="social", apply=_r_helped_creature),
    Rule(name="receive_key", tag="magic", apply=_r_receive_key),
    Rule(name="unlock", tag="magic", apply=_r_unlock),
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


def act_can_help(creature: Creature, act: KindAct) -> bool:
    return creature.problem in act.fixes


def key_matches_lock(key: MagicKey, lock: Lock) -> bool:
    return key.opens == lock.id


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for need_id, need in NEEDS.items():
            for lock_id, lock in LOCKS.items():
                if lock.opens_need != need_id:
                    continue
                for creature_id, creature in CREATURES.items():
                    for act_id, act in ACTS.items():
                        key = KEYS[creature.gift_key]
                        if act_can_help(creature, act) and key_matches_lock(key, lock):
                            combos.append((place_id, need_id, lock_id, creature_id, act_id))
    return combos


def predict_kindness(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["kind_help"] += 1
    propagate(sim, narrate=False)
    return {
        "creature_relieved": sim.get("creature").meters["relieved"] >= THRESHOLD,
        "key_revealed": sim.get("key").meters["revealed"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, need: Need, lock: Lock) -> None:
    world.say(
        f"In the old days, when hills listened and streams remembered names, "
        f"there lived a child named {child.id}."
    )
    world.say(
        f"{need.village_line} So {child.id} followed {world.place.path} to "
        f"{lock.phrase}."
    )
    world.say(world.place.sky)


def find_creature(world: World, child: Entity, creature: Creature, lock: Lock) -> None:
    child.memes["care"] += 1
    world.say(
        f"Before {child.id} could touch the lock, {child.pronoun()} heard a small cry: "
        f'"{creature.cry}"'
    )
    world.say(
        f"By a stone root sat {creature.phrase}, and {creature.problem}. "
        f"The great {lock.label} stayed shut and silent."
    )


def choose_kindness(world: World, child: Entity, creature: Creature, act: KindAct) -> None:
    pred = predict_kindness(world)
    world.facts["predicted_help"] = pred["creature_relieved"]
    world.say(
        f"{child.id} knelt at once. {act.line} "
        f"{child.pronoun().capitalize()} did not ask for treasure or praise."
    )


def do_help(world: World, child: Entity) -> None:
    child.meters["kind_help"] += 1
    propagate(world, narrate=False)


def gratitude_and_key(world: World, creature_ent: Entity, creature: Creature, key: MagicKey) -> None:
    creature_ent.memes["gratitude"] += 1
    world.say(
        f'At once the little creature gave a softer sound: "{creature.gratitude}"'
    )
    world.say(
        f"From beneath {creature_ent.pronoun('possessive')} {creature.hurt_part} "
        f"slid {key.phrase}. {key.shine}"
    )


def gift_explained(world: World, creature: Creature, key: MagicKey, lock: Lock, need: Need) -> None:
    world.say(
        f'"Take this {key.label}," said the creature. "It is the key for the '
        f'{lock.label}. Only a kind hand can wake it, and beyond it sleeps '
        f'{lock.blessing}. {need.hope_line}"'
    )


def unlock_scene(world: World, child: Entity, key: MagicKey, lock: Lock) -> None:
    child.meters["used_key"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} set the {key.label} into the old lock. {lock.sound} "
        f"The stone shivered. Hummmm. Then came a bright {key.shine.lower()}"
    )


def blessing_scene(world: World, need: Need, lock: Lock) -> None:
    world.say(
        f"The {lock.label} opened, and {lock.blessing} poured out. "
        f"{need.result_line}"
    )


def ending(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"From that day on, people said the oldest magic was not hidden in gold "
        f"or thunder, but in a child who stopped to be kind."
    )
    world.say(
        f"And whenever {child.id} walked home through {place.ending_image}, "
        f"the world seemed to answer with one last soft sound: 'ting.'"
    )


def tell(
    place: Place,
    need: Need,
    lock: Lock,
    creature: Creature,
    act: KindAct,
    child_name: str = "Iris",
    child_gender: str = "girl",
) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    village = world.add(Entity(id="village", kind="thing", type="village", label="the village"))
    sacred = world.add(
        Entity(
            id="sacred",
            kind="thing",
            type="lock",
            label=lock.label,
            attrs={"lock_id": lock.id},
        )
    )
    creature_ent = world.add(
        Entity(
            id="creature",
            kind="spirit",
            type="spirit",
            label=creature.label,
            attrs={"problem": creature.problem},
        )
    )
    key = world.add(
        Entity(
            id="key",
            kind="thing",
            type="key",
            label=key_label_for(creature),
            attrs={"opens": KEYS[creature.gift_key].opens},
        )
    )

    world.facts["place_cfg"] = place
    world.facts["need_cfg"] = need
    world.facts["lock_cfg"] = lock
    world.facts["creature_cfg"] = creature
    world.facts["act_cfg"] = act
    world.facts["key_cfg"] = KEYS[creature.gift_key]

    introduce(world, child, need, lock)
    world.para()
    find_creature(world, child, creature, lock)
    choose_kindness(world, child, creature, act)

    world.para()
    do_help(world, child)
    gratitude_and_key(world, creature_ent, creature, KEYS[creature.gift_key])
    gift_explained(world, creature, KEYS[creature.gift_key], lock, need)

    world.para()
    unlock_scene(world, child, KEYS[creature.gift_key], lock)
    blessing_scene(world, need, lock)

    world.para()
    ending(world, child, place)

    world.facts.update(
        child=child,
        village=village,
        sacred=sacred,
        creature=creature_ent,
        kindness_done=child.meters["kind_help"] >= THRESHOLD,
        key_revealed=key.meters["revealed"] >= THRESHOLD,
        unlocked=sacred.meters["open"] >= THRESHOLD,
        blessed=village.meters["blessed"] >= THRESHOLD,
    )
    return world


def key_label_for(creature: Creature) -> str:
    return KEYS[creature.gift_key].label


PLACES = {
    "grove": Place(
        id="grove",
        label="the laurel grove",
        path="a laurel path under whispering leaves",
        sky="Above the grove, pale light moved over the branches like slow silver fish.",
        ending_image="the grove full of fresh green light",
        tags={"grove", "myth"},
    ),
    "cliff": Place(
        id="cliff",
        label="the wind cliff",
        path="a cliff road above the sea",
        sky="Far below, the sea knocked on the rocks, and the wind braided salt into the air.",
        ending_image="the cliff path sparkling with wet shells",
        tags={"sea", "myth"},
    ),
    "spring": Place(
        id="spring",
        label="the old spring hill",
        path="a white path around the spring hill",
        sky="The hill stood still as an old giant, while little grasses bowed and rose in the breeze.",
        ending_image="the hill where the water sang again",
        tags={"hill", "myth"},
    ),
}

NEEDS = {
    "rain": Need(
        id="rain",
        village_line="For many days the fields had thirsted, and the village jars felt too light.",
        hope_line="Let the dry fields drink again.",
        result_line="Soon water ran over the fields, and every thirsty root lifted its head.",
        tags={"rain", "village"},
    ),
    "dawn": Need(
        id="dawn",
        village_line="One strange morning, dawn did not come, and the village waited in a dim blue hush.",
        hope_line="Let morning find the rooftops.",
        result_line="Gold light spilled across the roofs, and every sleeping window woke at once.",
        tags={"sun", "village"},
    ),
    "song": Need(
        id="song",
        village_line="The village spring had fallen quiet, and without its singing water the children carried home only heavy silence.",
        hope_line="Let the spring sing and flow again.",
        result_line="Clear water leapt out laughing, and the empty jars filled with bright ringing sound.",
        tags={"water", "village"},
    ),
}

LOCKS = {
    "cloud_gate": Lock(
        id="cloud_gate",
        label="Cloud Gate",
        phrase="the Cloud Gate carved with curls of rain",
        sound="Clink-clink! Whoooosh!",
        blessing="a river of rain",
        opens_need="rain",
        tags={"gate", "rain", "magic"},
    ),
    "sun_door": Lock(
        id="sun_door",
        label="Sun Door",
        phrase="the Sun Door cut into warm gold stone",
        sound="Click! Fwmmm!",
        blessing="the first fire of morning",
        opens_need="dawn",
        tags={"door", "sun", "magic"},
    ),
    "spring_chest": Lock(
        id="spring_chest",
        label="Spring Chest",
        phrase="the Spring Chest set beside a dry basin",
        sound="Tink! Splashhh!",
        blessing="singing water",
        opens_need="song",
        tags={"chest", "water", "magic"},
    ),
}

CREATURES = {
    "dove": Creature(
        id="dove",
        label="dove spirit",
        phrase="a white dove spirit no bigger than two hands",
        problem="tangled_ribbon",
        hurt_part="wing",
        cry="peep-peep!",
        gratitude="coo-oo",
        gift_key="feather_key",
        tags={"bird", "kindness"},
    ),
    "fox": Creature(
        id="fox",
        label="fox spirit",
        phrase="a small amber fox spirit with one sore paw",
        problem="thorn_paw",
        hurt_part="paw",
        cry="yip!",
        gratitude="rrrroo",
        gift_key="ember_key",
        tags={"fox", "kindness"},
    ),
    "carp": Creature(
        id="carp",
        label="carp spirit",
        phrase="a silver carp spirit stranded in wet reeds",
        problem="stuck_reeds",
        hurt_part="tail",
        cry="plip!",
        gratitude="blub-blub",
        gift_key="shell_key",
        tags={"fish", "kindness"},
    ),
}

ACTS = {
    "untangle": KindAct(
        id="untangle",
        verb="untangle",
        line="With patient fingers, the child gently untangled the snag and set each strand free.",
        fixes={"tangled_ribbon", "stuck_reeds"},
        tags={"help", "gentle"},
    ),
    "bandage": KindAct(
        id="bandage",
        verb="bandage",
        line="The child tore a strip from an old scarf and wrapped the hurt place softly.",
        fixes={"thorn_paw"},
        tags={"help", "care"},
    ),
    "lift": KindAct(
        id="lift",
        verb="lift",
        line="The child cupped both hands and carefully lifted the little creature to safety.",
        fixes={"stuck_reeds"},
        tags={"help", "rescue"},
    ),
}

KEYS = {
    "feather_key": MagicKey(
        id="feather_key",
        label="feather key",
        phrase="a feather key, white and silver, thin as moonlight",
        shine="It shone with a milk-pale glow.",
        opens="cloud_gate",
        tags={"key", "magic", "rain"},
    ),
    "ember_key": MagicKey(
        id="ember_key",
        label="ember key",
        phrase="an ember key, red as the heart of a fire",
        shine="It glimmered with a warm copper light.",
        opens="sun_door",
        tags={"key", "magic", "sun"},
    ),
    "shell_key": MagicKey(
        id="shell_key",
        label="shell key",
        phrase="a shell key, curled like a sleeping wave",
        shine="It flashed with blue-green light.",
        opens="spring_chest",
        tags={"key", "magic", "water"},
    ),
}

GIRL_NAMES = ["Iris", "Thaleia", "Mira", "Daphne", "Lyra", "Selene"]
BOY_NAMES = ["Orin", "Tomas", "Panos", "Leo", "Nikos", "Dorian"]
TRAITS = ["gentle", "brave", "patient", "curious", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    need: str
    lock: str
    creature: str
    act: str
    name: str
    gender: str
    trait: str
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
    "key": [
        (
            "What is a key for?",
            "A key is used to open something that has been locked. In stories, a magic key can also mean the right kind of heart or action that makes help possible."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help or care for someone gently. A kind act can change how others feel and what happens next."
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old kind of story about wonders, spirits, and special places. Myths often teach what people believe matters most."
        )
    ],
    "rain": [
        (
            "Why is rain important to plants?",
            "Plants need water to grow. When rain falls, it helps roots drink and keeps fields from drying out."
        )
    ],
    "sun": [
        (
            "Why does morning light matter?",
            "Morning light helps the world wake up and begin the day. People can see, work, and travel when the sun rises."
        )
    ],
    "water": [
        (
            "Why is spring water useful?",
            "Fresh water is needed for drinking and growing things. A spring can help a whole village when it flows well."
        )
    ],
    "bird": [
        (
            "Why can a bird get stuck in ribbon or string?",
            "Soft string can twist around wings or feet and make moving hard. That is why tangled things can be dangerous to small animals."
        )
    ],
    "fox": [
        (
            "Why does a thorn hurt a paw?",
            "A thorn is sharp, so it can poke skin and make walking painful. Pulling it out gently helps the paw heal."
        )
    ],
    "fish": [
        (
            "Why is a fish in reeds in trouble?",
            "A fish needs enough water and room to move. If it is trapped in reeds or shallow water, it may not be able to swim away."
        )
    ],
    "magic": [
        (
            "What does magic mean in a story?",
            "Magic means something wondrous happens that does not work like ordinary everyday life. In a myth, magic often answers courage or kindness."
        )
    ],
}

KNOWLEDGE_ORDER = ["key", "kindness", "myth", "rain", "sun", "water", "bird", "fox", "fish", "magic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place_cfg"]
    creature = f["creature_cfg"]
    lock = f["lock_cfg"]
    need = f["need_cfg"]
    key = f["key_cfg"]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the word "key" and shows kindness leading to magic.',
        f"Tell a gentle myth where a child named {child.id} helps a {creature.label} at {place.label}, receives a {key.label}, and opens the {lock.label}.",
        f"Write a child-facing myth in which a locked wonder holds help for a village, and the true way to open it begins with kindness instead of asking for reward. Include sound effects when the magic wakes."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    creature_ent = f["creature"]
    creature = f["creature_cfg"]
    act = f["act_cfg"]
    lock = f["lock_cfg"]
    need = f["need_cfg"]
    key = f["key_cfg"]
    place = f["place_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who walked to {place.label}, and a small {creature.label} in trouble. Their meeting changed what happened to the whole village."
        ),
        (
            f"Why did {child.id} go to {lock.label}?",
            f"{need.village_line} {child.id} went there because the locked holy place seemed to hold the help everyone needed."
        ),
        (
            f"What did {child.id} do when {child.pronoun()} heard the little cry?",
            f"{child.id} stopped and chose to help the creature first. {act.line} That kind choice came before any magic key appeared."
        ),
        (
            "How did the child get the key?",
            f"After the creature was relieved, it trusted {child.id} and gave {child.pronoun('object')} the {key.label}. The key came as a gift of gratitude because kindness had already mended the trouble."
        ),
    ]
    if f.get("unlocked"):
        qa.append(
            (
                f"What happened when {child.id} used the key?",
                f"The {lock.label} opened with magical sounds, and {lock.blessing} came out. That blessing solved the village's problem, so the ending shows the world changed for everyone."
            )
        )
    if f.get("blessed"):
        qa.append(
            (
                "What is the lesson of the story?",
                "The story teaches that kindness can be the truest kind of power. The child did not earn the magic by grabbing or demanding, but by helping someone small who needed care."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"key", "kindness", "myth", "magic"}
    need = world.facts["need_cfg"]
    creature = world.facts["creature_cfg"]
    tags |= set(need.tags)
    tags |= set(creature.tags)
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
            bits.append(f"attrs={dict(e.attrs)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="grove",
        need="rain",
        lock="cloud_gate",
        creature="dove",
        act="untangle",
        name="Iris",
        gender="girl",
        trait="gentle",
    ),
    StoryParams(
        place="cliff",
        need="dawn",
        lock="sun_door",
        creature="fox",
        act="bandage",
        name="Orin",
        gender="boy",
        trait="brave",
    ),
    StoryParams(
        place="spring",
        need="song",
        lock="spring_chest",
        creature="carp",
        act="lift",
        name="Mira",
        gender="girl",
        trait="patient",
    ),
    StoryParams(
        place="grove",
        need="song",
        lock="spring_chest",
        creature="carp",
        act="untangle",
        name="Leo",
        gender="boy",
        trait="thoughtful",
    ),
]


def explain_rejection(creature: Creature, act: KindAct, lock: Optional[Lock] = None, key: Optional[MagicKey] = None) -> str:
    if not act_can_help(creature, act):
        return (
            f"(No story: {act.id} does not honestly solve the {creature.label}'s problem "
            f"({creature.problem}). A myth here begins with real kindness that actually helps.)"
        )
    if lock is not None and key is not None and not key_matches_lock(key, lock):
        return (
            f"(No story: the {key.label} does not open the {lock.label}. The gifted key must match the sacred lock.)"
        )
    return "(No story: this combination does not fit the world rules.)"


ASP_RULES = r"""
can_help(C,A) :- creature(C), act(A), problem_of(C,P), fixes(A,P).
matching_key(C,L) :- creature(C), gift_key(C,K), key(K), opens(K,L).

valid(Place,Need,Lock,Creature,Act) :-
    place(Place), need(Need), lock(Lock), creature(Creature), act(Act),
    opens_need(Lock,Need),
    can_help(Creature,Act),
    matching_key(Creature,Lock).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    for lock_id, lock in LOCKS.items():
        lines.append(asp.fact("lock", lock_id))
        lines.append(asp.fact("opens_need", lock_id, lock.opens_need))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("problem_of", creature_id, creature.problem))
        lines.append(asp.fact("gift_key", creature_id, creature.gift_key))
    for act_id, act in ACTS.items():
        lines.append(asp.fact("act", act_id))
        for problem in sorted(act.fixes):
            lines.append(asp.fact("fixes", act_id, problem))
    for key_id, key in KEYS.items():
        lines.append(asp.fact("key", key_id))
        lines.append(asp.fact("opens", key_id, key.opens))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story is empty")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            generate(params)
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke-tested for seeds 0-9.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mythic child, a kind deed, a magic key."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--lock", choices=LOCKS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature and args.act:
        creature = CREATURES[args.creature]
        act = ACTS[args.act]
        if not act_can_help(creature, act):
            raise StoryError(explain_rejection(creature, act))
    if args.lock and args.creature:
        lock = LOCKS[args.lock]
        creature = CREATURES[args.creature]
        key = KEYS[creature.gift_key]
        if not key_matches_lock(key, lock):
            raise StoryError(explain_rejection(creature, ACTS[next(iter(ACTS))], lock=lock, key=key))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.need is None or c[1] == args.need)
        and (args.lock is None or c[2] == args.lock)
        and (args.creature is None or c[3] == args.creature)
        and (args.act is None or c[4] == args.act)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, need_id, lock_id, creature_id, act_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        need=need_id,
        lock=lock_id,
        creature=creature_id,
        act=act_id,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        need = NEEDS[params.need]
        lock = LOCKS[params.lock]
        creature = CREATURES[params.creature]
        act = ACTS[params.act]
        key = KEYS[creature.gift_key]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if lock.opens_need != need.id:
        raise StoryError("(Invalid story: the chosen lock does not release the chosen blessing.)")
    if not act_can_help(creature, act):
        raise StoryError(explain_rejection(creature, act))
    if not key_matches_lock(key, lock):
        raise StoryError(explain_rejection(creature, act, lock=lock, key=key))

    world = tell(
        place=place,
        need=need,
        lock=lock,
        creature=creature,
        act=act,
        child_name=params.name,
        child_gender=params.gender,
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, need, lock, creature, act) combos:\n")
        for place, need, lock, creature, act in combos:
            print(f"  {place:7} {need:5} {lock:12} {creature:8} {act}")
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
                f"### {p.name}: {p.creature} helped with {p.act} at {p.place} "
                f"({p.lock} for {p.need})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
