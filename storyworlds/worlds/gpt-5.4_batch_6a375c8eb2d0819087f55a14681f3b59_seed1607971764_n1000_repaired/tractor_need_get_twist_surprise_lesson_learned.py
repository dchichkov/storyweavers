#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tractor_need_get_twist_surprise_lesson_learned.py
============================================================================

A standalone story world about a child who needs to get a giant garden prize to
a fair with the right tractor. The domain is small and comedic: the temptation
is always to choose the biggest, loudest machine, but the world itself enforces
that the *right* tractor depends on the path and the load.

The story shape is consistent:
- premise: a child and a grown-up need to get a huge garden prize to town
- tension: the child wants the showiest tractor, but the path and mud matter
- twist: the best tractor is often the smaller one
- surprise: an unexpected comic beat proves the day changed
- lesson learned: biggest is not always best; the right tool matters

Run it
------
    python storyworlds/worlds/gpt-5.4/tractor_need_get_twist_surprise_lesson_learned.py
    python storyworlds/worlds/gpt-5.4/tractor_need_get_twist_surprise_lesson_learned.py --cargo pumpkin --path narrow_gate
    python storyworlds/worlds/gpt-5.4/tractor_need_get_twist_surprise_lesson_learned.py --tractor big_red
    python storyworlds/worlds/gpt-5.4/tractor_need_get_twist_surprise_lesson_learned.py --all
    python storyworlds/worlds/gpt-5.4/tractor_need_get_twist_surprise_lesson_learned.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tractor_need_get_twist_surprise_lesson_learned.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "grandma", "woman", "aunt"}
        male = {"boy", "father", "grandpa", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandma": "grandma",
            "grandpa": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
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
class Cargo:
    id: str
    label: str
    phrase: str
    contest: str
    weight: int
    width: int
    wobble: str
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
class Path:
    id: str
    label: str
    intro: str
    max_width: int
    mud: int
    bump: int
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
class TractorCfg:
    id: str
    label: str
    phrase: str
    power: int
    width: int
    traction: int
    sound: str
    personality: str
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
class Aid:
    id: str
    label: str
    phrase: str
    mud_help: int
    use_text: str
    qa_text: str
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
class Animal:
    id: str
    label: str
    entrance: str
    ending: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        self.trace: list[str] = []

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
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        clone.trace = list(self.trace)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    path = world.facts["path_cfg"]
    tractor = world.facts["tractor_cfg"]
    aid = world.facts["aid_cfg"]
    cargo = world.facts["cargo_cfg"]
    if cargo.weight <= tractor.power and tractor.width <= path.max_width:
        need = path.mud
        grip = tractor.traction + aid.mud_help
        if need > grip:
            sig = ("stuck", tractor.id, path.id)
            if sig not in world.fired:
                world.fired.add(sig)
                world.get("tractor").meters["stuck"] += 1
                world.get("child").memes["worry"] += 1
                world.get("adult").memes["worry"] += 1
                out.append("__stuck__")
    return out


def _r_rattle(world: World) -> list[str]:
    out: list[str] = []
    path = world.facts["path_cfg"]
    cargo = world.facts["cargo_cfg"]
    if path.bump + cargo.width >= 3:
        sig = ("rattle", cargo.id, path.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("cargo").meters["wobbling"] += 1
            world.get("child").memes["worry"] += 1
            out.append("__wobble__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="stuck", tag="physical", apply=_r_stuck),
    Rule(name="rattle", tag="physical", apply=_r_rattle),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit == "__stuck__":
                world.say("The back wheel gave one muddy spin and then sat there as if it had changed its mind.")
            elif bit == "__wobble__":
                world.say("The load gave a silly side-to-side shimmy that made everybody grab the cart at once.")
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def fits_path(tractor: TractorCfg, path: Path) -> bool:
    return tractor.width <= path.max_width


def pulls_load(tractor: TractorCfg, cargo: Cargo) -> bool:
    return tractor.power >= cargo.weight


def clears_mud(tractor: TractorCfg, path: Path, aid: Aid) -> bool:
    return tractor.traction + aid.mud_help >= path.mud


def valid_combo(cargo: Cargo, path: Path, tractor: TractorCfg, aid: Aid) -> bool:
    return fits_path(tractor, path) and pulls_load(tractor, cargo) and clears_mud(tractor, path, aid)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for cargo_id, cargo in CARGOS.items():
        for path_id, path in PATHS.items():
            for tractor_id, tractor in TRACTORS.items():
                for aid_id, aid in AIDS.items():
                    if valid_combo(cargo, path, tractor, aid):
                        combos.append((cargo_id, path_id, tractor_id, aid_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    cargo = CARGOS[params.cargo]
    path = PATHS[params.path]
    tractor = TRACTORS[params.tractor]
    aid = AIDS[params.aid]
    if not valid_combo(cargo, path, tractor, aid):
        return "invalid"
    if path.mud > tractor.traction and aid.mud_help > 0:
        return "rescued"
    return "smooth"


def explain_rejection(cargo: Cargo, path: Path, tractor: TractorCfg, aid: Aid) -> str:
    if not fits_path(tractor, path):
        return (
            f"(No story: {tractor.label} is too wide for {path.label}. "
            f"The child may want the biggest tractor, but it cannot even get through.)"
        )
    if not pulls_load(tractor, cargo):
        return (
            f"(No story: {tractor.label} cannot pull the {cargo.label}. "
            f"This world only tells stories where the chosen tractor can really do the job.)"
        )
    if not clears_mud(tractor, path, aid):
        return (
            f"(No story: {path.label} is too muddy for {tractor.label} with {aid.label}. "
            f"You need more grip or a better way through the mud.)"
        )
    return "(No story: that combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_trip(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "stuck": sim.get("tractor").meters["stuck"] >= THRESHOLD,
        "wobble": sim.get("cargo").meters["wobbling"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def setup_need(world: World, child: Entity, adult: Entity, cargo: Cargo) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} had grown {cargo.phrase} with {adult.label_word}, and now they needed to get it to the town fair for the {cargo.contest}."
    )
    world.say(
        f"{child.pronoun().capitalize()} marched around it once, hands on hips, and said, "
        f'"We need a tractor. A glorious tractor. Maybe one so loud the tomatoes salute."'
    )


def set_scene(world: World, path: Path) -> None:
    world.say(path.intro)


def boast(world: World, child: Entity) -> None:
    child.memes["pride"] += 1
    world.say(
        f"{child.id} spread both arms wide. "
        f'"Let\'s get the biggest one on the farm," {child.pronoun()} declared. '
        f'"If it has three levers and a horn the size of a goose, even better."'
    )


def warn_and_measure(world: World, adult: Entity, child: Entity, tractor: TractorCfg, path: Path) -> None:
    pred = predict_trip(world)
    world.facts["predicted_stuck"] = pred["stuck"]
    world.facts["predicted_wobble"] = pred["wobble"]
    if path.max_width <= 1:
        world.say(
            f"{adult.label_word.capitalize()} squinted at {path.label}, held out the measuring stick, and smiled. "
            f'"Funny thing," {adult.pronoun()} said. "The path does not care about bragging. It only cares what fits."'
        )
    else:
        world.say(
            f"{adult.label_word.capitalize()} rubbed the muddy path with one boot and nodded toward the shed. "
            f'"Before we get excited, let\'s think about what can pull and what can keep its feet," {adult.pronoun()} said.'
        )
    if pred["stuck"]:
        world.say(
            f'"If we just hop on {tractor.label}, we will sit in the mud and make a fine statue of ourselves," {adult.pronoun()} added.'
        )
    elif pred["wobble"]:
        world.say(
            f'"This plan will roll, but it may jiggle that {world.facts["cargo_cfg"].label} like pudding," {adult.pronoun()} warned.'
        )
    else:
        world.say(
            f'"It may not look fancy, but the right little tractor can do honest work," {adult.pronoun()} said.'
        )


def get_tractor(world: World, child: Entity, adult: Entity, tractor: TractorCfg) -> None:
    world.get("tractor").meters["ready"] += 1
    child.memes["surprise"] += 1
    world.say(
        f"So instead of the enormous show-off machine, they got {tractor.phrase}. "
        f"It sounded {tractor.sound}, and somehow that made {child.id} grin."
    )
    world.say(
        f'"That one?" {child.id} asked. "{tractor.label.capitalize()}?" '
        f"{adult.label_word.capitalize()} nodded. "
        f'"Yes. It is small, but it is {tractor.personality}."'
    )


def load_up(world: World, child: Entity, cargo: Cargo) -> None:
    world.get("cargo").meters["loaded"] += 1
    child.memes["effort"] += 1
    world.say(
        f"They puffed and heaved and finally got the {cargo.label} onto the cart. "
        f"It sat there with {cargo.wobble}."
    )


def trip_start(world: World, tractor: TractorCfg, path: Path) -> None:
    world.say(
        f"{tractor.label.capitalize()} chugged toward {path.label}, and the little parade began."
    )
    propagate(world, narrate=True)


def aid_rescue(world: World, child: Entity, adult: Entity, aid: Aid) -> None:
    if aid.id == "none":
        return
    if world.get("tractor").meters["stuck"] >= THRESHOLD:
        world.get("tractor").meters["stuck"] = 0.0
        world.get("child").memes["relief"] += 1
        world.get("adult").memes["relief"] += 1
        world.say(aid.use_text)
        world.say(
            f'Soon the tractor gave one brave tug, then another, and climbed out with a wet slurp. "{aid.label.capitalize()} for the win," {child.id} cheered.'
        )


def wobble_save(world: World, child: Entity, adult: Entity, cargo: Cargo) -> None:
    if world.get("cargo").meters["wobbling"] >= THRESHOLD:
        world.get("cargo").meters["wobbling"] = 0.0
        child.memes["care"] += 1
        world.say(
            f"{child.id} grabbed the side of the cart while {adult.label_word} tightened the rope around the {cargo.label}. "
            f"After that, the big load stopped dancing."
        )


def surprise_animal(world: World, animal: Animal, cargo: Cargo) -> None:
    world.get("animal").memes["glee"] += 1
    world.facts["animal_gag"] = True
    world.say(animal.entrance.format(cargo=cargo.label))


def fair_arrival(world: World, child: Entity, adult: Entity, cargo: Cargo, tractor: TractorCfg, animal: Animal) -> None:
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"At last they rolled into the fair yard, and every head turned toward the {cargo.label} and the funny little tractor that had brought it there."
    )
    world.say(
        f'The judge blinked once and laughed. "Well, that is the neatest arrival I have seen all morning."'
    )
    world.say(
        f"{animal.ending} {child.id} laughed too, because the surprise no longer felt like a mistake. It felt like the best part of the story."
    )
    world.say(
        f'On the way home, {child.id} patted the fender and said, "I thought we needed the biggest tractor to get the job done." '
        f'{adult.label_word.capitalize()} smiled. "We needed the right one."'
    )
    world.say(
        f"After that, whenever {child.id} had to get something awkward from one place to another, {child.pronoun()} looked first, measured second, and bragged last."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    path: Path,
    tractor: Tractor,
    aid: Aid,
    animal: Animal,
    child_name: str,
    child_gender: str,
    adult_type: AdultType,
    trait: str,
    cargo=None,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait]))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the grown-up"))
    world.add(Entity(id="cargo", kind="thing", type="cargo", label=cargo.label))
    world.add(Entity(id="tractor", kind="thing", type="tractor", label=tractor.label))
    world.add(Entity(id="animal", kind="thing", type="animal", label=animal.label))

    world.facts.update(
        cargo_cfg=cargo,
        path_cfg=path,
        tractor_cfg=tractor,
        aid_cfg=aid,
        animal_cfg=animal,
        child=child,
        adult=adult,
        outcome="",
        animal_gag=False,
        predicted_stuck=False,
        predicted_wobble=False,
    )

    setup_need(world, child, adult, cargo)
    set_scene(world, path)

    world.para()
    boast(world, child)
    warn_and_measure(world, adult, child, tractor, path)
    get_tractor(world, child, adult, tractor)

    world.para()
    load_up(world, child, cargo)
    trip_start(world, tractor, path)
    aid_rescue(world, child, adult, aid)
    wobble_save(world, child, adult, cargo)

    world.para()
    surprise_animal(world, animal, cargo)
    fair_arrival(world, child, adult, cargo, tractor, animal)

    world.facts["used_aid"] = aid.id != "none" and path.mud > tractor.traction
    world.facts["had_wobble"] = path.bump + cargo.width >= 3
    world.facts["outcome"] = outcome_of(
        StoryParams(
            cargo=cargo.id,
            path=path.id,
            tractor=tractor.id,
            aid=aid.id,
            animal=animal.id,
            child_name=child_name,
            child_gender=child_gender,
            adult=adult_type,
            trait=trait,
            seed=None,
        )
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


CARGOS = {
    "pumpkin": Cargo(
        id="pumpkin",
        label="pumpkin",
        phrase="a pumpkin so round it looked as if it had swallowed a moon",
        contest="Big Pumpkin Table",
        weight=3,
        width=2,
        wobble="a proud orange wobble",
        tags={"pumpkin", "fair"},
    ),
    "melon": Cargo(
        id="melon",
        label="melon",
        phrase="a melon almost too big for one pair of arms",
        contest="Sweetest Melon Row",
        weight=2,
        width=1,
        wobble="a polite little wobble",
        tags={"melon", "fair"},
    ),
    "cabbage": Cargo(
        id="cabbage",
        label="cabbage",
        phrase="a cabbage as wide as a dinner plate and twice as bossy",
        contest="Crisp Cabbage Bench",
        weight=1,
        width=1,
        wobble="a leafy bob",
        tags={"cabbage", "fair"},
    ),
}

PATHS = {
    "muddy_lane": Path(
        id="muddy_lane",
        label="the muddy lane",
        intro="The shortest way to town was the muddy lane, a strip of brown squish with wagon tracks pressed into it like giant fingerprints.",
        max_width=3,
        mud=2,
        bump=1,
        tags={"mud", "lane"},
    ),
    "narrow_gate": Path(
        id="narrow_gate",
        label="the narrow orchard gate",
        intro="The quickest way out was the narrow orchard gate, squeezed between two fence posts that looked as if they had never met a hurry in their lives.",
        max_width=1,
        mud=0,
        bump=1,
        tags={"gate", "orchard"},
    ),
    "bumpy_row": Path(
        id="bumpy_row",
        label="the bumpy corn row",
        intro="The dry route ran along the bumpy corn row, where every root made a small hop and every hop had ideas of its own.",
        max_width=2,
        mud=1,
        bump=2,
        tags={"corn", "bumpy"},
    ),
}

TRACTORS = {
    "big_red": TractorCfg(
        id="big_red",
        label="big red tractor",
        phrase="the big red tractor with a shiny hood and a horn that sounded as if it knew it was handsome",
        power=4,
        width=3,
        traction=2,
        sound="HONK-huff-HONK",
        personality="steady when it has room",
        tags={"tractor", "big_tractor"},
    ),
    "little_blue": TractorCfg(
        id="little_blue",
        label="little blue tractor",
        phrase="the little blue tractor with the patched seat and the cheerful putter",
        power=3,
        width=1,
        traction=1,
        sound="putter-putter-peep",
        personality="small, stubborn, and smarter than it looks",
        tags={"tractor", "small_tractor"},
    ),
    "old_green": TractorCfg(
        id="old_green",
        label="old green tractor",
        phrase="the old green tractor with one sleepy headlight and a very serious tug",
        power=2,
        width=2,
        traction=1,
        sound="chug-chug-sniff",
        personality="patient and plain",
        tags={"tractor", "old_tractor"},
    ),
}

AIDS = {
    "none": Aid(
        id="none",
        label="no extra help",
        phrase="no extra help",
        mud_help=0,
        use_text="",
        qa_text="They did not need any extra help on the path.",
        tags=set(),
    ),
    "planks": Aid(
        id="planks",
        label="wooden planks",
        phrase="two wooden planks",
        mud_help=2,
        use_text="Grandpa fetched two wooden planks from the shed, and together they laid them over the worst patch like a tiny wooden road.",
        qa_text="They used wooden planks to make a firm path over the mud.",
        tags={"planks", "mud"},
    ),
}

ANIMALS = {
    "goose": Animal(
        id="goose",
        label="goose",
        entrance="Just then the farm goose marched up, flapped twice, and hopped onto the cart beside the {cargo} as if it had paid for the ride.",
        ending="The goose stayed there, looking so proud that even the ribbon table seemed to take it seriously.",
        tags={"goose"},
    ),
    "dog": Animal(
        id="dog",
        label="dog",
        entrance="Just then the farm dog trotted up, barked at the {cargo}, and sat on the trailer tongue as if it were the official traffic manager.",
        ending="The dog kept his chest puffed out all through judging, as though he had hauled the whole thing himself.",
        tags={"dog"},
    ),
    "hen": Animal(
        id="hen",
        label="hen",
        entrance="Just then the little brown hen fluttered onto the cart and began inspecting the {cargo} with the fierce face of a tiny inspector.",
        ending="The hen clucked at everyone who came close, which made the display look even more important.",
        tags={"hen"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Milo", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["dramatic", "hopeful", "bossy", "cheerful", "curious", "earnest"]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "tractor": [
        (
            "What does a tractor do?",
            "A tractor is a strong farm machine that pulls or carries heavy things. Farmers use it when a job is too hard to do by hand."
        )
    ],
    "mud": [
        (
            "Why can mud make wheels get stuck?",
            "Mud is soft and slippery, so wheels can sink and spin instead of gripping the ground. That is why heavy things move more slowly in mud."
        )
    ],
    "planks": [
        (
            "Why do wooden planks help in mud?",
            "Planks spread the weight out and make a firmer path over soft ground. That gives wheels something solid to push against."
        )
    ],
    "fair": [
        (
            "What is a town fair?",
            "A town fair is a place where people bring food, animals, games, and prizes together. Sometimes people even show their biggest vegetables there."
        )
    ],
    "pumpkin": [
        (
            "Why are giant pumpkins funny to look at?",
            "Giant pumpkins are funny because they are so big and round that they can look almost too large to be real. Their size makes ordinary jobs feel silly."
        )
    ],
    "goose": [
        (
            "Why do geese sometimes look bossy?",
            "Geese walk with their necks high and often honk as if they have important news. That makes them seem very sure of themselves."
        )
    ],
    "dog": [
        (
            "Why might a dog follow a cart?",
            "Dogs often like to go wherever their people go. A moving cart also gives them something exciting to watch and guard."
        )
    ],
    "hen": [
        (
            "Why does a hen peck at new things?",
            "Hens explore with quick pecks and close looks. It is one way they check whether something is food or simply interesting."
        )
    ],
}
KNOWLEDGE_ORDER = ["tractor", "mud", "planks", "fair", "pumpkin", "goose", "dog", "hen"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cargo = f["cargo_cfg"]
    path = f["path_cfg"]
    animal = f["animal_cfg"]
    child = f["child"]
    tractor = f["tractor_cfg"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "tractor", "need", and "get", where a child needs to get a giant {cargo.label} to a fair.',
        f"Tell a comedy about {child.id}, who thinks the biggest tractor must be best, but learns a twist on {path.label} when {tractor.label} is the right choice instead.",
        f"Write a story with a twist, a surprise, and a lesson learned: a child and a grown-up haul a giant garden prize with a tractor, and a {animal.label} steals part of the show.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    cargo = f["cargo_cfg"]
    path = f["path_cfg"]
    tractor = f["tractor_cfg"]
    aid = f["aid_cfg"]
    animal = f["animal_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {adult.label_word}, and a giant {cargo.label} they wanted to take to the fair. The story is also about choosing the right tractor for the job."
        ),
        (
            f"Why did {child.id} say they need a tractor?",
            f"They needed to get the huge {cargo.label} to the town fair, and it was too heavy to move by hand. The size of the load turned a simple trip into a farm problem."
        ),
        (
            "What was the twist in the story?",
            f"The twist was that the biggest, loudest tractor was not the best one after all. {adult.label_word.capitalize()} looked at {path.label} and chose {tractor.label}, because the path mattered as much as the load."
        ),
    ]

    if f.get("used_aid"):
        qa.append(
            (
                "How did they get through the muddy part?",
                f"They used {aid.phrase} to make a firmer path, and then the tractor pulled free. The rescue worked because the mud was the real problem, not the size of the engine."
            )
        )
    else:
        qa.append(
            (
                "Why did the trip work without getting stuck?",
                f"It worked because the tractor fit the path and had enough strength for the {cargo.label}. They chose a plan that matched the ground instead of just sounding impressive."
            )
        )

    if f.get("had_wobble"):
        qa.append(
            (
                f"What happened when the {cargo.label} started to wobble?",
                f"The load jiggled and everybody grabbed the cart at once. Then {adult.label_word} tightened the rope and {child.id} helped steady it, so the trip could continue safely."
            )
        )

    qa.append(
        (
            "What was the surprise at the fair?",
            f"The surprise was that the {animal.label} hopped onto the cart and acted as if it belonged in the parade. That comic little helper made everyone laugh and made the arrival even more memorable."
        )
    )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{child.id} learned that biggest is not always best. The right tool is the one that fits the job, the path, and the problem you really have."
        )
    )
    if outcome == "rescued":
        qa.append(
            (
                "Did the plan go perfectly from the start?",
                "No. The tractor needed extra help on the muddy patch before it could keep going. That little setback is what proved why planning matters."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"tractor", "fair"}
    cargo = world.facts["cargo_cfg"]
    path = world.facts["path_cfg"]
    aid = world.facts["aid_cfg"]
    animal = world.facts["animal_cfg"]

    tags |= cargo.tags
    tags |= path.tags
    tags |= aid.tags
    tags |= animal.tags

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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    cargo: str
    path: str
    tractor: str
    aid: str
    animal: str
    child_name: str
    child_gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        cargo="pumpkin",
        path="narrow_gate",
        tractor="little_blue",
        aid="none",
        animal="goose",
        child_name="Milo",
        child_gender="boy",
        adult="grandpa",
        trait="dramatic",
        seed=None,
    ),
    StoryParams(
        cargo="pumpkin",
        path="muddy_lane",
        tractor="big_red",
        aid="none",
        animal="dog",
        child_name="Lily",
        child_gender="girl",
        adult="grandma",
        trait="hopeful",
        seed=None,
    ),
    StoryParams(
        cargo="melon",
        path="muddy_lane",
        tractor="little_blue",
        aid="planks",
        animal="hen",
        child_name="Ben",
        child_gender="boy",
        adult="grandpa",
        trait="cheerful",
        seed=None,
    ),
    StoryParams(
        cargo="cabbage",
        path="bumpy_row",
        tractor="old_green",
        aid="none",
        animal="goose",
        child_name="Maya",
        child_gender="girl",
        adult="grandma",
        trait="curious",
        seed=None,
    ),
    StoryParams(
        cargo="pumpkin",
        path="bumpy_row",
        tractor="little_blue",
        aid="none",
        animal="dog",
        child_name="Nora",
        child_gender="girl",
        adult="grandpa",
        trait="bossy",
        seed=None,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(C,P,T,A) :- cargo(C), path(P), tractor(T), aid(A),
                  weight(C,W), power(T,PO), W <= PO,
                  max_width(P,MW), width(T,TW), TW <= MW,
                  mud(P,M), traction(T,TR), mud_help(A,H), TR + H >= M.

needs_help(P,T) :- path(P), tractor(T), mud(P,M), traction(T,TR), M > TR.
smooth(C,P,T,A) :- valid(C,P,T,A), not needs_help(P,T).
rescued(C,P,T,A) :- valid(C,P,T,A), needs_help(P,T), mud_help(A,H), H > 0.
outcome(smooth) :- chosen(C,P,T,A), smooth(C,P,T,A).
outcome(rescued) :- chosen(C,P,T,A), rescued(C,P,T,A).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cargo_id, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("weight", cargo_id, cargo.weight))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("max_width", path_id, path.max_width))
        lines.append(asp.fact("mud", path_id, path.mud))
    for tractor_id, tractor in TRACTORS.items():
        lines.append(asp.fact("tractor", tractor_id))
        lines.append(asp.fact("power", tractor_id, tractor.power))
        lines.append(asp.fact("width", tractor_id, tractor.width))
        lines.append(asp.fact("traction", tractor_id, tractor.traction))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("mud_help", aid_id, aid.mud_help))
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
            asp.fact("chosen", params.cargo, params.path, params.tractor, params.aid),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = 0
    for params in cases:
        if params.cargo in CARGOS and params.path in PATHS and params.tractor in TRACTORS and params.aid in AIDS:
            if asp_outcome(params) != outcome_of(params):
                mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child needs to get a giant garden prize to the fair with the right tractor."
    )
    ap.add_argument("--cargo", choices=sorted(CARGOS))
    ap.add_argument("--path", choices=sorted(PATHS))
    ap.add_argument("--tractor", choices=sorted(TRACTORS))
    ap.add_argument("--aid", choices=sorted(AIDS))
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["grandma", "grandpa"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.cargo not in CARGOS:
        raise StoryError(f"(Unknown cargo: {args.cargo})")
    if args.path and args.path not in PATHS:
        raise StoryError(f"(Unknown path: {args.path})")
    if args.tractor and args.tractor not in TRACTORS:
        raise StoryError(f"(Unknown tractor: {args.tractor})")
    if args.aid and args.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {args.aid})")
    if args.animal and args.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {args.animal})")

    if args.cargo and args.path and args.tractor and args.aid:
        cargo = CARGOS[args.cargo]
        path = PATHS[args.path]
        tractor = TRACTORS[args.tractor]
        aid = AIDS[args.aid]
        if not valid_combo(cargo, path, tractor, aid):
            raise StoryError(explain_rejection(cargo, path, tractor, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cargo is None or combo[0] == args.cargo)
        and (args.path is None or combo[1] == args.path)
        and (args.tractor is None or combo[2] == args.tractor)
        and (args.aid is None or combo[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cargo_id, path_id, tractor_id, aid_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    adult = args.adult or rng.choice(["grandma", "grandpa"])
    animal = args.animal or rng.choice(sorted(ANIMALS))
    trait = rng.choice(TRAITS)

    return StoryParams(
        cargo=cargo_id,
        path=path_id,
        tractor=tractor_id,
        aid=aid_id,
        animal=animal,
        child_name=child_name,
        child_gender=child_gender,
        adult=adult,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cargo not in CARGOS:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.path not in PATHS:
        raise StoryError(f"(Unknown path: {params.path})")
    if params.tractor not in TRACTORS:
        raise StoryError(f"(Unknown tractor: {params.tractor})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")

    cargo = CARGOS[params.cargo]
    path = PATHS[params.path]
    tractor = TRACTORS[params.tractor]
    aid = AIDS[params.aid]
    animal = ANIMALS[params.animal]

    if not valid_combo(cargo, path, tractor, aid):
        raise StoryError(explain_rejection(cargo, path, tractor, aid))

    world = tell(
        cargo=cargo,
        path=path,
        tractor=tractor,
        aid=aid,
        animal=animal,
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult,
        trait=params.trait,
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
        print(f"{len(combos)} compatible (cargo, path, tractor, aid) combos:\n")
        for cargo, path, tractor, aid in combos:
            print(f"  {cargo:8} {path:11} {tractor:11} {aid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.cargo} via {p.path} with {p.tractor} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
