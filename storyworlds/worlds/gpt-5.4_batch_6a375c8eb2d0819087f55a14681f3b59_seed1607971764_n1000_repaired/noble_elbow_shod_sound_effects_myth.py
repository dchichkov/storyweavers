#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/noble_elbow_shod_sound_effects_myth.py
=================================================================

A standalone story world for a tiny mythic domain: a child must lead a noble,
metal-shod colt across a ringing way to the hill altar before sunrise. The
child first tries to hurry the frightened animal and bangs an elbow in the
confusion. A wiser helper chooses a sound-taming fix, and the ending proves
what changed in the world.

The model prefers *plausible* variants over broad coverage:

- A story only exists when the chosen surface would make a truly troubling echo.
- A response must be common-sense within the world.
- Some fixes are too weak if the fear has had too much time to grow.

Features:
- typed entities with physical meters and emotional memes
- a tiny forward-chaining rule layer
- sound effects in the prose ("CLANG-CLANG!", "clop-clop", "hush")
- a Python reasonableness gate plus an inline ASP twin
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
    shod: bool = False
    sacred: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "priestess"}
        male = {"boy", "man", "father", "herdsman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.type.replace("_", " ")
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
class Surface:
    id: str
    label: str
    phrase: str
    echo: int
    sound: str
    image: str
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
class Beast:
    id: str
    label: str
    phrase: str
    shoe_metal: str
    title: str
    cargo: str
    temper: str
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
class Fix:
    id: str
    sense: int
    power: int
    label: str
    apply_text: str
    fail_text: str
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


def _r_echo_spooks(world: World) -> list[str]:
    out: list[str] = []
    beast = world.entities.get("beast")
    way = world.entities.get("way")
    if not beast or not way:
        return out
    if beast.shod and way.meters["echo"] >= THRESHOLD and beast.meters["on_way"] >= THRESHOLD:
        sig = ("echo_spooks", beast.id, way.id)
        if sig not in world.fired:
            world.fired.add(sig)
            beast.memes["fear"] += way.meters["echo"]
            beast.meters["stopped"] += 1
            out.append("__spook__")
    return out


def _r_fear_spreads(world: World) -> list[str]:
    out: list[str] = []
    beast = world.entities.get("beast")
    hero = world.entities.get("hero")
    if not beast or not hero:
        return out
    if beast.memes["fear"] >= THRESHOLD:
        sig = ("fear_spreads", beast.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            out.append("__worry__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="echo_spooks", tag="physical", apply=_r_echo_spooks),
    Rule(name="fear_spreads", tag="emotional", apply=_r_fear_spreads),
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
                produced.extend(s for s in res if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def sound_hazard(beast: Beast, surface: Surface) -> bool:
    return surface.echo >= 2


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def severity(surface: Surface, delay: int) -> int:
    return surface.echo + delay


def success(fix: Fix, surface: Surface, delay: int) -> bool:
    return fix.power >= severity(surface, delay)


def predict_spook(world: World) -> dict:
    sim = world.copy()
    sim.get("beast").meters["on_way"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("beast").memes["fear"],
        "stopped": sim.get("beast").meters["stopped"],
    }


def opening(world: World, hero: Entity, helper: Entity, beast_cfg: Beast) -> None:
    hero.memes["duty"] += 1
    beast = world.get("beast")
    world.say(
        f"In the old hill country, where dawn was welcomed like a guest, "
        f"{hero.id} was chosen to lead {beast_cfg.phrase} to the altar of morning."
    )
    world.say(
        f"The little beast was called {beast_cfg.title}, for it was a noble colt, "
        f"shod in {beast_cfg.shoe_metal} shoes and carrying {beast_cfg.cargo} in a woven basket."
    )
    world.say(
        f"{helper.id}, the temple {helper.label_word}, walked beside them while the eastern sky "
        f"was still pale as milk."
    )
    beast.memes["trust"] += 1


def approach(world: World, hero: Entity, beast_cfg: Beast, surface: Surface) -> None:
    world.say(
        f"Soon they came to {surface.phrase}. {surface.image} "
        f"{hero.id} lifted the lead rope and stepped forward."
    )
    pred = predict_spook(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'But {hero.id} remembered how {beast_cfg.title} disliked hard ringing places. '
        f'"If the shoes strike there, it will sound {surface.sound}," {hero.pronoun()} murmured.'
    )


def first_steps(world: World, hero: Entity, beast: Entity, surface: Surface) -> None:
    beast.meters["on_way"] += 1
    world.get("way").meters["echo"] = float(surface.echo)
    propagate(world, narrate=False)
    world.say(
        f"The first hoof touched the way: {surface.sound}! {surface.sound}! "
        f"The noise leaped back from stone to stone."
    )
    if beast.meters["stopped"] >= THRESHOLD:
        world.say(
            f"{beast.id} threw up {beast.pronoun('possessive')} head and froze. "
            f"{hero.id} felt the rope turn hard in {hero.pronoun('possessive')} hands."
        )


def hurry(world: World, hero: Entity, beast: Entity, surface: Surface) -> None:
    hero.memes["haste"] += 1
    beast.memes["fear"] += 1
    hero.memes["worry"] += 1
    world.say(
        f'"Come, {beast.id}," {hero.id} said, and tugged too quickly, hoping to outrun the echo.'
    )
    hero.meters["elbow_hurt"] += 1
    world.say(
        f"But the frightened colt sprang sideways. Thump! {hero.id}'s elbow knocked against a gatepost, "
        f"and tears stung {hero.pronoun('possessive')} eyes."
    )


def counsel(world: World, helper: Entity, hero: Entity, beast_cfg: Beast, surface: Surface) -> None:
    helper.memes["calm"] += 1
    world.say(
        f'{helper.id} laid a steady hand on the rope. "A noble creature does not need more pulling," '
        f'{helper.pronoun()} said. "It needs less thunder."'
    )
    world.say(
        f'{hero.id} looked at the ringing way, at the bright-shod feet, and at {hero.pronoun("possessive")} sore elbow, '
        f'and knew the temple {helper.label_word} spoke truth.'
    )


def apply_fix(world: World, helper: Entity, hero: Entity, beast: Entity, fix: Fix) -> None:
    beast.meters["stopped"] = 0.0
    beast.meters["quieted"] += 1
    beast.memes["fear"] = max(0.0, beast.memes["fear"] - fix.power)
    hero.memes["hope"] += 1
    world.say(f"{helper.id} {fix.apply_text}")
    world.say(
        f"After that, the colt listened. The air seemed to lean closer, waiting to hear what would happen next."
    )


def crossing(world: World, hero: Entity, beast_cfg: Beast, surface: Surface) -> None:
    world.say(
        f"Again they tried the crossing. This time the steps answered only with a small "
        f"'{surface.sound.lower()}' far under the hush."
    )
    world.say(
        f"{beast_cfg.title} lowered its head, walked on, and bore {beast_cfg.cargo} safely toward the altar."
    )
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1
    beast = world.get("beast")
    beast.meters["crossed"] += 1


def sunrise(world: World, hero: Entity, helper: Entity, beast_cfg: Beast) -> None:
    world.say(
        f"When they reached the height, the first ray of the sun touched the basket of {beast_cfg.cargo}. "
        f"Gold spilled across the stones."
    )
    world.say(
        f'{helper.id} smiled. "{hero.id}," {helper.pronoun()} said, "strength is not only in the hand. '
        f'Sometimes it is in the listening."'
    )
    world.say(
        f"So the child and the noble colt stood together in the newborn light, and even {hero.id}'s sore elbow "
        f"seemed part of a wiser beginning."
    )


def fail_fix(world: World, helper: Entity, hero: Entity, beast: Entity, fix: Fix, surface: Surface) -> None:
    beast.meters["stopped"] += 1
    beast.memes["fear"] += 1
    hero.memes["sadness"] += 1
    world.say(f"{helper.id} {fix.fail_text}")
    world.say(
        f"But when the hoof touched the hard way again -- {surface.sound}! -- the fear sprang back at once."
    )


def missed_dawn(world: World, hero: Entity, helper: Entity, beast_cfg: Beast) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f"The eastern rim of the world brightened before they could cross, and the offering of {beast_cfg.cargo} "
        f"reached the altar late."
    )
    world.say(
        f'{helper.id} drew {hero.id} close and said, "The gods ask for truth more than hurry. '
        f'Remember what the echo taught you."'
    )
    world.say(
        f"From then on, whenever {hero.id} heard hard hooves ring, {hero.pronoun()} remembered to quiet the path "
        f"before asking courage to walk it."
    )


def tell(
    surface: Surface,
    beast_cfg: Beast,
    fix: Fix,
    hero_name: str = "Ione",
    hero_type: str = "girl",
    helper_name: str = "Thaleia",
    helper_type: str = "priestess",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    helper = world.add(
        Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name)
    )
    beast = world.add(
        Entity(
            id=beast_cfg.title,
            kind="thing",
            type="colt",
            role="beast",
            label=beast_cfg.label,
            shod=True,
            sacred=True,
            attrs={"temper": beast_cfg.temper, "cargo": beast_cfg.cargo, "shoe_metal": beast_cfg.shoe_metal},
        )
    )
    way = world.add(Entity(id="way", type="path", role="surface", label=surface.label))
    way.meters["echo"] = 0.0
    beast.meters["on_way"] = 0.0
    beast.meters["stopped"] = 0.0
    beast.meters["crossed"] = 0.0
    beast.meters["quieted"] = 0.0
    beast.memes["fear"] = 0.0
    hero.meters["elbow_hurt"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = 0.0
    hero.memes["lesson"] = 0.0
    hero.memes["hope"] = 0.0
    hero.memes["sadness"] = 0.0
    helper.memes["calm"] = 0.0

    opening(world, hero, helper, beast_cfg)
    world.para()
    approach(world, hero, beast_cfg, surface)
    first_steps(world, hero, beast, surface)
    hurry(world, hero, beast, surface)
    counsel(world, helper, hero, beast_cfg, surface)
    world.para()

    contained = success(fix, surface, delay)
    if contained:
        apply_fix(world, helper, hero, beast, fix)
        crossing(world, hero, beast_cfg, surface)
        world.para()
        sunrise(world, hero, helper, beast_cfg)
    else:
        apply_fix(world, helper, hero, beast, fix)
        fail_fix(world, helper, hero, beast, fix, surface)
        world.para()
        missed_dawn(world, hero, helper, beast_cfg)

    outcome = "crossed" if contained else "late"
    world.facts.update(
        hero=hero,
        helper=helper,
        beast=beast,
        beast_cfg=beast_cfg,
        surface=surface,
        fix=fix,
        delay=delay,
        outcome=outcome,
        elbow_hurt=hero.meters["elbow_hurt"] >= THRESHOLD,
        predicted_fear=world.facts.get("predicted_fear", 0),
        crossed=beast.meters["crossed"] >= THRESHOLD,
    )
    return world


SURFACES = {
    "bronze_bridge": Surface(
        id="bronze_bridge",
        label="bronze bridge",
        phrase="a bridge of hammered bronze over a narrow ravine",
        echo=3,
        sound="CLANG-CLANG",
        image="Below it, the stream whispered; above it, every footfall loved to boast.",
        tags={"bridge", "sound"},
    ),
    "marble_steps": Surface(
        id="marble_steps",
        label="marble steps",
        phrase="the white marble steps that climbed to the altar court",
        echo=2,
        sound="clop-clop",
        image="Each step was smooth as still water and just as ready to return a sound.",
        tags={"steps", "sound"},
    ),
    "granite_gate": Surface(
        id="granite_gate",
        label="granite gate road",
        phrase="the granite road before the Lion Gate",
        echo=2,
        sound="TONK-TONK",
        image="The gate towers stood like old giants, eager to throw voices back.",
        tags={"gate", "sound"},
    ),
    "moss_path": Surface(
        id="moss_path",
        label="moss path",
        phrase="a mossy path under olive trees",
        echo=0,
        sound="hush",
        image="It was soft as green wool and swallowed every step.",
        tags={"path"},
    ),
}

BEASTS = {
    "sun_colt": Beast(
        id="sun_colt",
        label="colt",
        phrase="a small colt from the royal meadow",
        shoe_metal="bronze",
        title="Helion",
        cargo="a basket of saffron and laurel",
        temper="proud",
        tags={"colt", "sunrise"},
    ),
    "moon_foal": Beast(
        id="moon_foal",
        label="foal",
        phrase="a silver-maned foal from the temple fold",
        shoe_metal="silver",
        title="Selon",
        cargo="white lilies and a little jar of honey",
        temper="gentle",
        tags={"foal", "altar"},
    ),
    "storm_pony": Beast(
        id="storm_pony",
        label="pony",
        phrase="a dark pony from the windy ridge",
        shoe_metal="iron",
        title="Bront",
        cargo="blue iris flowers and spring water",
        temper="quick-hearted",
        tags={"pony", "altar"},
    ),
}

FIXES = {
    "felt_wraps": Fix(
        id="felt_wraps",
        sense=3,
        power=3,
        label="felt wraps",
        apply_text="knelt and wrapped the bright shoes in thick felt strips until metal met the world softly",
        fail_text="wrapped the shoes in thin felt, but the strips slipped loose before the second step",
        qa_text="wrapped the colt's bright shoes in thick felt so the hard ringing sound would fade",
        tags={"felt", "quiet"},
    ),
    "reed_scatter": Fix(
        id="reed_scatter",
        sense=2,
        power=2,
        label="reed matting",
        apply_text="shook out reed matting across the worst of the hard stones, making a softer road for the hooves",
        fail_text="laid reed matting over the stones, but it covered too little of the ringing way",
        qa_text="spread reed matting over the hard stones so the hooves would not strike so sharply",
        tags={"reeds", "quiet"},
    ),
    "side_path": Fix(
        id="side_path",
        sense=3,
        power=4,
        label="side path",
        apply_text="led them away from the ringing stones and onto a side path where moss drank the sound",
        fail_text="turned toward a side path, but the dawn gate had already been shut and they had to come back",
        qa_text="guided the colt onto a softer side path where the sound could not leap back so loudly",
        tags={"path", "quiet"},
    ),
    "loud_song": Fix(
        id="loud_song",
        sense=1,
        power=1,
        label="loud song",
        apply_text="sang louder and louder, trying to drown the echo with a brave voice",
        fail_text="sang loudly at the echo, but more noise only made the colt flinch harder",
        qa_text="tried to sing over the noise",
        tags={"song"},
    ),
}


@dataclass
class StoryParams:
    surface: str
    beast: str
    fix: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
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


GIRL_NAMES = ["Ione", "Myrto", "Daphne", "Lysa", "Nerine", "Chloe"]
BOY_NAMES = ["Theron", "Leos", "Damon", "Phaon", "Nikos", "Aeson"]
HELPER_NAMES = ["Thaleia", "Melas", "Rhea", "Kyros", "Althea", "Timon"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for surface_id, surface in SURFACES.items():
        for beast_id, beast in BEASTS.items():
            if sound_hazard(beast, surface):
                combos.append((surface_id, beast_id))
    return combos


KNOWLEDGE = {
    "bridge": [
        (
            "Why can a bridge sound so loud under hooves?",
            "A hard bridge throws the sound back instead of soaking it up. That is why hooves on metal or stone can ring so sharply."
        )
    ],
    "steps": [
        (
            "Why do marble steps echo?",
            "Marble is hard and smooth, so sounds bounce from it easily. A hoofbeat on marble can seem louder than the same step on dirt."
        )
    ],
    "colt": [
        (
            "What is a colt?",
            "A colt is a young horse. Young horses can be brave one moment and jumpy the next if a strange noise startles them."
        )
    ],
    "foal": [
        (
            "What is a foal?",
            "A foal is a very young horse. Because it is young, it may need a calm guide when something feels scary."
        )
    ],
    "pony": [
        (
            "What is a pony?",
            "A pony is a small kind of horse. Even a strong pony can stop if the ground sounds frightening under its feet."
        )
    ],
    "felt": [
        (
            "What does felt do under a hard shoe?",
            "Felt is soft and thick, so it can muffle a sound. Putting felt between a hard shoe and a hard surface makes the step quieter."
        )
    ],
    "reeds": [
        (
            "Why would reed matting make a path quieter?",
            "Reeds make a soft layer over the hard ground. That softer layer keeps each hoofbeat from striking the stone so sharply."
        )
    ],
    "path": [
        (
            "Why is a mossy path quieter than stone?",
            "Moss is soft and springy, so it drinks in sound instead of throwing it back. That makes steps on a mossy path much gentler to hear."
        )
    ],
    "quiet": [
        (
            "Why can a frightened animal need quiet more than force?",
            "A frightened animal is already trying to protect itself. If the world grows calmer, it can listen and trust again."
        )
    ],
    "song": [
        (
            "Can making more noise always solve a noise problem?",
            "No. If the problem is that a sound feels too big or scary, adding even more noise can make the fear worse."
        )
    ],
    "sound": [
        (
            "What is an echo?",
            "An echo is a sound that bounces back after it hits a hard place. It can make one small step seem larger than it really was."
        )
    ],
    "sunrise": [
        (
            "Why do myths often care about sunrise offerings?",
            "Sunrise feels like the world's first bright moment each day, so many myths treat it as a special time for gifts, prayers, or thanks."
        )
    ],
    "altar": [
        (
            "What is an altar?",
            "An altar is a special place where people bring gifts or prayers. In stories, it often stands for honor, memory, or thanks."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "sound",
    "bridge",
    "steps",
    "colt",
    "foal",
    "pony",
    "felt",
    "reeds",
    "path",
    "quiet",
    "song",
    "sunrise",
    "altar",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    beast_cfg = f["beast_cfg"]
    surface = f["surface"]
    if f["outcome"] == "crossed":
        return [
            f'Write a short myth for young children about a noble child leading a {beast_cfg.label} across {surface.label}, using sound effects like "{surface.sound}!" and including the words "noble", "elbow", and "shod".',
            f"Tell a mythic story where {hero.id} hurts an elbow while trying to hurry a frightened, shod animal, then learns to quiet the path instead of pulling harder.",
            "Write a simple myth in which a ringing road causes trouble, a wiser elder gives calm advice, and sunrise proves that listening can be stronger than force.",
        ]
    return [
        f'Write a short myth for young children about a noble child leading a {beast_cfg.label} across {surface.label}, using sound effects like "{surface.sound}!" and including the words "noble", "elbow", and "shod".',
        f"Tell a mythic cautionary story where {hero.id} learns too late that more haste and more noise do not calm a frightened, shod animal.",
        "Write a simple myth with a wistful ending where a child misses the perfect dawn moment but keeps the lesson of quiet courage.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    beast_cfg = f["beast_cfg"]
    surface = f["surface"]
    fix = f["fix"]
    beast = f["beast"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, the temple {helper.label_word} {helper.id}, and {beast_cfg.title}, a noble young horse carrying {beast_cfg.cargo} toward the altar."
        ),
        (
            "Why did the crossing become difficult?",
            f"The colt was shod in {beast_cfg.shoe_metal} shoes, and {surface.label} threw each hoofbeat back as an echo. The hard sound frightened the animal and made it stop."
        ),
        (
            f"How did {hero.id} hurt {hero.pronoun('possessive')} elbow?",
            f"{hero.id} tried to hurry the frightened colt by tugging the rope too quickly. When the colt jumped sideways, {hero.pronoun('possessive')} elbow banged against a gatepost."
        ),
    ]
    if f["outcome"] == "crossed":
        qa.append(
            (
                f"How did {helper.id} solve the problem?",
                f"{helper.id} {fix.qa_text}. That changed the world around the colt, so the sound no longer rushed back at it so fiercely."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The child, the helper, and the colt reached the altar in time for sunrise. The ending image shows that quiet steps and patient hands carried the offering safely into the first gold light."
            )
        )
    else:
        qa.append(
            (
                f"Why did the offering arrive late?",
                f"The fix was not strong enough to quiet the ringing path before dawn came. Each hard hoofbeat brought the fear back, so the crossing took too long."
            )
        )
        qa.append(
            (
                "What did the child learn?",
                f"{hero.id} learned that fear cannot be dragged away by force. The sore elbow and the missed dawn both taught {hero.pronoun('object')} to quiet the path before asking a frightened creature to walk."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["surface"].tags) | set(world.facts["beast_cfg"].tags) | set(world.facts["fix"].tags)
    tags.add("quiet")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.shod:
            bits.append("shod=True")
        if ent.sacred:
            bits.append("sacred=True")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        surface="bronze_bridge",
        beast="sun_colt",
        fix="felt_wraps",
        hero="Ione",
        hero_type="girl",
        helper="Thaleia",
        helper_type="priestess",
        delay=0,
    ),
    StoryParams(
        surface="marble_steps",
        beast="moon_foal",
        fix="reed_scatter",
        hero="Theron",
        hero_type="boy",
        helper="Rhea",
        helper_type="priestess",
        delay=0,
    ),
    StoryParams(
        surface="granite_gate",
        beast="storm_pony",
        fix="side_path",
        hero="Daphne",
        hero_type="girl",
        helper="Kyros",
        helper_type="herdsman",
        delay=1,
    ),
    StoryParams(
        surface="bronze_bridge",
        beast="storm_pony",
        fix="reed_scatter",
        hero="Leos",
        hero_type="boy",
        helper="Althea",
        helper_type="priestess",
        delay=2,
    ),
]


def explain_rejection(surface: Surface, beast: Beast) -> str:
    if surface.echo < 2:
        return (
            f"(No story: {surface.label} is too soft or quiet to frighten a metal-shod animal. "
            f"Without a real sound problem, there is no honest mythic turn to solve.)"
        )
    return (
        f"(No story: {beast.title} would not face a meaningful sound hazard on that way.)"
    )


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.surface not in SURFACES or params.fix not in FIXES:
        return "?"
    return "crossed" if success(FIXES[params.fix], SURFACES[params.surface], params.delay) else "late"


ASP_RULES = r"""
hazard(S, B) :- surface(S), beast(B), echo(S, E), E >= 2, shod(B).
sensible(F)  :- fix(F), sense(F, V), sense_min(M), V >= M.
valid(S, B)  :- hazard(S, B).

severity(V) :- chosen_surface(S), echo(S, E), delay(D), V = E + D.
contains    :- chosen_fix(F), power(F, P), severity(V), P >= V.

outcome(crossed) :- contains.
outcome(late)    :- not contains.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, surface in SURFACES.items():
        lines.append(asp.fact("surface", sid))
        lines.append(asp.fact("echo", sid, surface.echo))
    for bid in BEASTS:
        lines.append(asp.fact("beast", bid))
        lines.append(asp.fact("shod", bid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_surface", params.surface),
            asp.fact("chosen_fix", params.fix),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generation() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "noble" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story was empty or malformed.")
    emit(sample, trace=False, qa=False, header="")


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

    py_sens = {f.id for f in sensible_fixes()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible fixes match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(asp_sens)} python={sorted(py_sens)}")

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError in resolve_params() during verify for seed {s}.")
            break
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_generation()
        print("OK: smoke generation succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a mythic child, a ringing path, and a sound-wise fix."
    )
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--beast", choices=BEASTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["priestess", "herdsman"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start for fear; higher means a harder recovery")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surface and args.beast:
        surface = SURFACES[args.surface]
        beast = BEASTS[args.beast]
        if not sound_hazard(beast, surface):
            raise StoryError(explain_rejection(surface, beast))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        c for c in valid_combos()
        if (args.surface is None or c[0] == args.surface)
        and (args.beast is None or c[1] == args.beast)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    surface_id, beast_id = rng.choice(sorted(combos))
    fix_id = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["priestess", "herdsman"])
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        surface=surface_id,
        beast=beast_id,
        fix=fix_id,
        hero=hero,
        hero_type=gender,
        helper=helper,
        helper_type=helper_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.surface not in SURFACES:
        raise StoryError(f"(Unknown surface: {params.surface})")
    if params.beast not in BEASTS:
        raise StoryError(f"(Unknown beast: {params.beast})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    surface = SURFACES[params.surface]
    beast_cfg = BEASTS[params.beast]
    fix = FIXES[params.fix]

    if not sound_hazard(beast_cfg, surface):
        raise StoryError(explain_rejection(surface, beast_cfg))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        surface=surface,
        beast_cfg=beast_cfg,
        fix=fix,
        hero_name=params.hero,
        hero_type=params.hero_type,
        helper_name=params.helper,
        helper_type=params.helper_type,
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
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (surface, beast) combos:\n")
        for surface, beast in combos:
            print(f"  {surface:13} {beast}")
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
            header = f"### {p.hero}: {p.beast} on {p.surface} ({p.fix}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
