#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/babe_symmetry_rapist_surprise_sound_effects_adventure.py
===================================================================================

A standalone storyworld for a tiny adventure domain built from a noisy seed.

The seed included the words "babe", "symmetry", and "rapist", plus the features
"Surprise" and "Sound Effects" in an adventure style. This world keeps the safe,
story-usable parts in child-facing prose ("babe" and "symmetry"), while the
unsafe seed token "rapist" is preserved only here in this module docstring and
never rendered in story text, QA, or prompts for children.

Domain:
    A child explorer and a calm grown-up helper enter a small wonder-place to
    rescue a lost baby animal. A symmetry puzzle blocks the best path. A sudden
    surprise noise may scare the little animal deeper into the place, but the
    child uses the right matching tool to open the puzzle and bring the animal
    safely home.

Run it:
    python storyworlds/worlds/gpt-5.4/babe_symmetry_rapist_surprise_sound_effects_adventure.py
    python storyworlds/worlds/gpt-5.4/babe_symmetry_rapist_surprise_sound_effects_adventure.py --place cave --obstacle mirror_gate --tool chalk
    python storyworlds/worlds/gpt-5.4/babe_symmetry_rapist_surprise_sound_effects_adventure.py --tool flute --obstacle rope_bridge
    python storyworlds/worlds/gpt-5.4/babe_symmetry_rapist_surprise_sound_effects_adventure.py --all
    python storyworlds/worlds/gpt-5.4/babe_symmetry_rapist_surprise_sound_effects_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/babe_symmetry_rapist_surprise_sound_effects_adventure.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "grandmother"}
        male = {"boy", "man", "father", "uncle", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def helper_word(self) -> str:
        return {
            "aunt": "aunt",
            "uncle": "uncle",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    path: str
    light: str
    echo: str
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
class Animal:
    id: str
    label: str
    phrase: str
    call: str
    home: str
    calmness: int
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
class Obstacle:
    id: str
    label: str
    barrier: str
    pattern: str
    need: str
    open_sound: str
    shortcut: str
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
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    solves: set[str] = field(default_factory=set)
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
class Surprise:
    id: str
    label: str
    sound: str
    source: str
    level: int
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


def _r_scatter(world: World) -> list[str]:
    animal = world.get("animal")
    if animal.meters["startled"] < THRESHOLD:
        return []
    sig = ("scatter", "animal")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.meters["distance"] += 1
    world.get("place").meters["risk"] += 1
    animal.memes["fear"] += 1
    return ["__scatter__"]


def _r_open(world: World) -> list[str]:
    gate = world.get("gate")
    if gate.meters["matched"] < THRESHOLD or gate.meters["open"] >= THRESHOLD:
        return []
    sig = ("open", "gate")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gate.meters["open"] += 1
    world.get("place").meters["hope"] += 1
    return ["__open__"]


RULES = [
    Rule(name="scatter", tag="physical", apply=_r_scatter),
    Rule(name="open", tag="physical", apply=_r_open),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def tool_fits(tool: Tool, obstacle: Obstacle) -> bool:
    return obstacle.need in tool.solves


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in SETTINGS:
        for animal_id in ANIMALS:
            for obstacle_id, obstacle in OBSTACLES.items():
                for tool_id, tool in TOOLS.items():
                    if tool_fits(tool, obstacle):
                        combos.append((place_id, animal_id, obstacle_id, tool_id))
    return combos


def surprise_scatters(animal: Animal, surprise: Surprise) -> bool:
    return surprise.level > animal.calmness


def predict_plan(world: World, animal: Animal, obstacle: Obstacle, tool: Tool, surprise: Surprise) -> dict:
    sim = world.copy()
    if surprise_scatters(animal, surprise):
        sim.get("animal").meters["startled"] += 1
        propagate(sim, narrate=False)
    if tool_fits(tool, obstacle):
        sim.get("gate").meters["matched"] += 1
        propagate(sim, narrate=False)
    return {
        "scatters": sim.get("animal").meters["distance"] >= THRESHOLD,
        "opens": sim.get("gate").meters["open"] >= THRESHOLD,
        "risk": sim.get("place").meters["risk"],
    }


def introduce(world: World, hero: Entity, helper: Entity, animal: Animal) -> None:
    hero.memes["wonder"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"{hero.id} loved small adventures, especially the kind with maps, pockets, and brave little footsteps."
    )
    world.say(
        f"That morning, {hero.id} and {helper.id} followed a trail into {world.setting.place}, where {world.setting.light} and {world.setting.echo}."
    )
    world.say(
        f"They were looking for {animal.phrase}, who had wandered away from {animal.home}."
    )


def find_sign(world: World, hero: Entity, animal: Animal) -> None:
    world.say(
        f"At a bend in {world.setting.path}, {hero.id} spotted tiny prints and heard a soft {animal.call} from ahead."
    )
    world.say(
        f'"There you are, little babe," {hero.id} whispered, hoping not to frighten {animal.label}.'
    )


def show_obstacle(world: World, helper: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"But the best way forward was blocked by {obstacle.barrier}. On both sides lay {obstacle.pattern}, almost asking for symmetry."
    )
    world.say(
        f'"This place likes matches," said {helper.id}. "If we make both sides answer each other, it may open."'
    )


def warn_with_prediction(world: World, hero: Entity, helper: Entity, animal: Animal, obstacle: Obstacle, tool: Tool, surprise: Surprise) -> None:
    pred = predict_plan(world, animal, obstacle, tool, surprise)
    world.facts["predicted_scatters"] = pred["scatters"]
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_opens"] = pred["opens"]
    if pred["scatters"]:
        world.say(
            f'{helper.id} listened hard and said, "If another surprise jumps out, {animal.label} may scamper deeper. We must move softly first, then use the {tool.label}."'
        )
    else:
        world.say(
            f'{helper.id} smiled. "If we stay gentle and use the {tool.label}, I think the path will open before {animal.label} gets scared."'
        )


def surprise_beat(world: World, hero: Entity, animal_ent: Entity, surprise: Surprise, animal: Animal) -> None:
    hero.memes["alarm"] += 1
    world.say(
        f"Then, all at once, {surprise.source} leapt from the shadows — {surprise.sound}!"
    )
    if surprise_scatters(animal, surprise):
        animal_ent.meters["startled"] += 1
        propagate(world, narrate=False)
        hero.memes["worry"] += 1
        world.say(
            f"{animal.label.capitalize()} gave one frightened hop and darted farther along the stones."
        )
    else:
        animal_ent.meters["startled"] += 0.0
        world.say(
            f"{animal.label.capitalize()} froze for a blink, ears up, but did not run."
        )


def solve_obstacle(world: World, hero: Entity, helper: Entity, gate: Entity, obstacle: Obstacle, tool: Tool) -> None:
    gate.meters["matched"] += 1
    hero.memes["focus"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} took out {tool.phrase} and {tool.method}. Line answered line, note answered note, and the old pattern settled into perfect symmetry."
    )
    world.say(
        f"At once the puzzle answered back: {obstacle.open_sound} The way opened into {obstacle.shortcut}."
    )


def rescue_direct(world: World, hero: Entity, helper: Entity, animal_ent: Entity, animal: Animal) -> None:
    animal_ent.meters["found"] += 1
    hero.memes["relief"] += 1
    animal_ent.memes["trust"] += 1
    world.say(
        f"Just beyond the opened path, {animal.label} was waiting beside a bright stone pool."
    )
    world.say(
        f"{hero.id} knelt low, held out careful hands, and {animal.label} padded right in."
    )
    world.say(
        f"{helper.id} tucked {animal.label} close, and together they headed back toward {animal.home}."
    )


def rescue_after_chase(world: World, hero: Entity, helper: Entity, animal_ent: Entity, animal: Animal, obstacle: Obstacle) -> None:
    animal_ent.meters["found"] += 1
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    animal_ent.memes["trust"] += 1
    world.say(
        f"Because the opened way was a shortcut, they reached the far side before {animal.label} could hide again."
    )
    world.say(
        f"{hero.id} sat very still beside {obstacle.shortcut} and copied {animal.call} in a tiny voice."
    )
    world.say(
        f"After a moment, {animal.label} peeked out, crept closer, and let {helper.id} scoop it up."
    )


def ending(world: World, hero: Entity, helper: Entity, animal: Animal) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"When they carried {animal.label} back to {animal.home}, the whole place felt different — less like a puzzle, more like a friend."
    )
    world.say(
        f'"Best adventures are the ones that end with everyone safe," said {helper.id}.'
    )
    world.say(
        f"{hero.id} looked back at the shining path and grinned. Next time, {hero.pronoun()} knew, brave would mean quiet hands, quick thinking, and a careful heart."
    )


def tell(
    setting: Setting,
    animal: Animal,
    obstacle: Obstacle,
    tool: Tool,
    surprise: Surprise,
    hero_name: str = "Nora",
    hero_type: str = "girl",
    helper_type: str = "aunt",
    helper_name: str = "Aunt May",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", label=helper_name))
    animal_ent = world.add(Entity(id="animal", kind="thing", type="animal", label=animal.label, role="animal"))
    gate = world.add(Entity(id="gate", kind="thing", type="obstacle", label=obstacle.label, role="gate"))
    place = world.add(Entity(id="place", kind="thing", type="place", label=setting.place, role="place"))

    hero.memes["wonder"] = 0.0
    hero.memes["alarm"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["focus"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["lesson"] = 0.0
    helper.memes["calm"] = 0.0
    animal_ent.meters["startled"] = 0.0
    animal_ent.meters["distance"] = 0.0
    animal_ent.meters["found"] = 0.0
    gate.meters["matched"] = 0.0
    gate.meters["open"] = 0.0
    place.meters["risk"] = 0.0
    place.meters["hope"] = 0.0

    world.facts["setting"] = setting
    world.facts["animal_cfg"] = animal
    world.facts["obstacle_cfg"] = obstacle
    world.facts["tool_cfg"] = tool
    world.facts["surprise_cfg"] = surprise
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["animal"] = animal_ent

    introduce(world, hero, helper, animal)
    find_sign(world, hero, animal)

    world.para()
    show_obstacle(world, helper, obstacle)
    warn_with_prediction(world, hero, helper, animal, obstacle, tool, surprise)

    world.para()
    surprise_beat(world, hero, animal_ent, surprise, animal)
    solve_obstacle(world, hero, helper, gate, obstacle, tool)

    world.para()
    if animal_ent.meters["distance"] >= THRESHOLD:
        rescue_after_chase(world, hero, helper, animal_ent, animal, obstacle)
        outcome = "chase"
    else:
        rescue_direct(world, hero, helper, animal_ent, animal)
        outcome = "direct"

    world.para()
    ending(world, hero, helper, animal)

    world.facts.update(
        gate=gate,
        place_ent=place,
        outcome=outcome,
        scattered=animal_ent.meters["distance"] >= THRESHOLD,
        opened=gate.meters["open"] >= THRESHOLD,
        rescued=animal_ent.meters["found"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "cave": Setting(
        id="cave",
        place="a moonlit cave behind the waterfall",
        path="the silver path",
        light="blue drops shone like tiny stars",
        echo="every step came back with a soft echo",
        tags={"cave", "echo"},
    ),
    "garden": Setting(
        id="garden",
        place="a secret garden of stone arches",
        path="the mossy walk",
        light="sunbeams slipped through the leaves in bright stripes",
        echo="fountains hummed under the birdsong",
        tags={"garden", "arches"},
    ),
    "ruin": Setting(
        id="ruin",
        place="an old cliff ruin above the sea",
        path="the windy stair",
        light="shells glimmered in the cracks of the wall",
        echo="the sea boomed far below",
        tags={"ruin", "sea"},
    ),
}

ANIMALS = {
    "lamb": Animal(
        id="lamb",
        label="the lamb",
        phrase="a woolly lamb named Babe",
        call="maa-aa",
        home="the warm sheep pen by the hill",
        calmness=1,
        tags={"lamb", "babe"},
    ),
    "seal": Animal(
        id="seal",
        label="the seal pup",
        phrase="a round seal pup",
        call="ow-ow",
        home="its smooth nest near the tide pool",
        calmness=2,
        tags={"seal"},
    ),
    "fox": Animal(
        id="fox",
        label="the fox cub",
        phrase="a red fox cub",
        call="yip-yip",
        home="the ferny den under a root",
        calmness=1,
        tags={"fox"},
    ),
}

OBSTACLES = {
    "mirror_gate": Obstacle(
        id="mirror_gate",
        label="the mirror gate",
        barrier="a low crystal gate",
        pattern="two empty circles carved into twin stones",
        need="draw",
        open_sound="click-click, shimmer!",
        shortcut="a narrow crystal hall",
        tags={"symmetry", "gate"},
    ),
    "bell_lock": Obstacle(
        id="bell_lock",
        label="the bell lock",
        barrier="a round bronze door",
        pattern="two hanging bells waiting in silence",
        need="music",
        open_sound="ding-ding, clack!",
        shortcut="a lamp-lit passage",
        tags={"symmetry", "bells"},
    ),
    "rope_bridge": Obstacle(
        id="rope_bridge",
        label="the rope bridge",
        barrier="a broken rope bridge folded against the wall",
        pattern="two loose ends with matching rings",
        need="tie",
        open_sound="swish-snap, thump!",
        shortcut="a steady bridge over the gap",
        tags={"symmetry", "bridge"},
    ),
}

TOOLS = {
    "chalk": Tool(
        id="chalk",
        label="chalk",
        phrase="a stub of white chalk",
        method="drew the missing shape on one stone, then the same shape on the other",
        solves={"draw"},
        tags={"chalk", "draw"},
    ),
    "flute": Tool(
        id="flute",
        label="flute",
        phrase="a small reed flute",
        method="played one clear note to the left bell and the same clear note to the right",
        solves={"music"},
        tags={"flute", "music"},
    ),
    "ribbon": Tool(
        id="ribbon",
        label="ribbon",
        phrase="a blue ribbon from {helper}'s pocket",
        method="looped one end through the left ring and matched it exactly on the right",
        solves={"tie"},
        tags={"ribbon", "tie"},
    ),
}

SURPRISES = {
    "owl": Surprise(
        id="owl",
        label="owl burst",
        sound="WHOOOSH!",
        source="an owl",
        level=2,
        tags={"owl", "sound"},
    ),
    "pebbles": Surprise(
        id="pebbles",
        label="pebble tumble",
        sound="clatter-clatter!",
        source="a string of pebbles",
        level=1,
        tags={"pebbles", "sound"},
    ),
    "frog": Surprise(
        id="frog",
        label="frog spring",
        sound="BRAAAP!",
        source="a fat frog",
        level=1,
        tags={"frog", "sound"},
    ),
}

GIRL_NAMES = ["Nora", "Mira", "Lily", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Finn", "Leo", "Sam", "Eli", "Noah", "Max"]
HELPERS = {
    "aunt": ["Aunt May", "Aunt June"],
    "uncle": ["Uncle Ben", "Uncle Ash"],
    "grandmother": ["Grandma Rose", "Grandma Nell"],
    "grandfather": ["Grandpa Theo", "Grandpa Reed"],
}


@dataclass
class StoryParams:
    place: str
    animal: str
    obstacle: str
    tool: str
    surprise: str
    name: str
    gender: str
    helper: str
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
    "symmetry": [
        (
            "What is symmetry?",
            "Symmetry means two sides match each other in shape or pattern. When something is symmetrical, one side answers the other in a neat, balanced way.",
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces off a wall or cliff and comes back to you. That is why caves and big stone places can sound extra boomy.",
        )
    ],
    "sound": [
        (
            "Why can a sudden loud sound scare an animal?",
            "Animals listen for danger, so a loud surprise can make them jump before they know what happened. Many small animals run first and figure things out later.",
        )
    ],
    "chalk": [
        (
            "What is chalk used for?",
            "Chalk is a soft stick you can use to draw marks on stone or a board. It helps you make clear shapes that can be wiped away later.",
        )
    ],
    "flute": [
        (
            "What does a flute do?",
            "A flute makes music when you blow air through it. Different notes can sound high, low, soft, or bright.",
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a long strip of cloth that can tie, wrap, or decorate something. It is soft and easy to loop into matching shapes.",
        )
    ],
    "lamb": [
        (
            "What is a lamb?",
            "A lamb is a young sheep with soft wool. Lambs often stay close to safe grown-up sheep and warm pens.",
        )
    ],
    "seal": [
        (
            "What is a seal pup?",
            "A seal pup is a baby seal. It rests near water and needs a safe place to stay warm and close to its family.",
        )
    ],
    "fox": [
        (
            "What is a fox cub?",
            "A fox cub is a young fox. Fox cubs are small, quick, and often hide when they feel scared.",
        )
    ],
}
KNOWLEDGE_ORDER = ["symmetry", "echo", "sound", "chalk", "flute", "ribbon", "lamb", "seal", "fox"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    animal = f["animal_cfg"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    setting = f["setting"]
    return [
        f'Write a short adventure for a 3-to-5-year-old about a child exploring {setting.place} to rescue {animal.phrase}. Include sound effects and the word "symmetry".',
        f"Tell a gentle rescue adventure where {hero.id} and {helper.id} face {obstacle.label}, use {tool.label}, and bring {animal.label} safely home after a surprise noise.",
        f"Write a simple story in which a child solves a matching puzzle, stays calm after a sudden sound, and ends by helping a lost baby animal feel safe again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    animal = f["animal_cfg"]
    obstacle = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    surprise = f["surprise_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child explorer, and {helper.id}, who went on a small rescue adventure together. They were trying to find {animal.phrase} and bring {animal.label} home.",
        ),
        (
            f"Why did {hero.id} and {helper.id} go into {world.setting.place}?",
            f"They went in to look for {animal.phrase}, who had wandered away from {animal.home}. The adventure began as a rescue, not just a game.",
        ),
        (
            f"What blocked their way?",
            f"The best path was blocked by {obstacle.barrier}. Its twin pattern needed symmetry, so the two sides had to match before the way would open.",
        ),
        (
            f"How did they open the obstacle?",
            f"{hero.id} used {tool.phrase.replace('{helper}', helper.id)} and {tool.method}. That made the two sides match, and the puzzle answered with {obstacle.open_sound}.",
        ),
    ]
    if f.get("scattered"):
        qa.append(
            (
                f"What did the surprise {surprise.label} do?",
                f"It startled {animal.label}, so {animal.pronoun() if isinstance(animal, Entity) else 'it'} ran deeper into the place for a moment. The loud sound mattered because small animals often move before they can tell whether a surprise is safe.",
            )
        )
        qa.append(
            (
                f"How did {hero.id} finally rescue {animal.label}?",
                f"The opened path gave them a shortcut, so they reached the far side in time. Then {hero.id} stayed very still and used a gentle voice, which helped {animal.label} trust them enough to come out.",
            )
        )
    else:
        qa.append(
            (
                f"Did the surprise noise make {animal.label} run away?",
                f"No. {animal.label.capitalize()} was startled for a blink, but did not run. That gave {hero.id} and {helper.id} time to open the path and reach it calmly.",
            )
        )
        qa.append(
            (
                f"How did the story end?",
                f"They rescued {animal.label} and carried it back to {animal.home}. The ending shows that the adventure changed from a noisy, risky search into a safe trip home.",
            )
        )
    qa.append(
        (
            f"What did {hero.id} learn?",
            f"{hero.id} learned that being brave does not mean rushing. It means staying calm, noticing what matches, and helping gently when someone small is scared.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"symmetry", "sound"}
    tags |= set(world.setting.tags)
    tags |= set(world.facts["animal_cfg"].tags)
    tags |= set(world.facts["tool_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(tool: Tool, obstacle: Obstacle) -> str:
    wants = obstacle.need
    have = ", ".join(sorted(tool.solves))
    return (
        f"(No story: {obstacle.label} needs a matching action of type '{wants}', "
        f"but {tool.label} only solves [{have}]. The adventure works only when the chosen tool can honestly make the symmetry puzzle open.)"
    )


CURATED = [
    StoryParams(
        place="cave",
        animal="lamb",
        obstacle="mirror_gate",
        tool="chalk",
        surprise="owl",
        name="Nora",
        gender="girl",
        helper="aunt",
        helper_name="Aunt May",
    ),
    StoryParams(
        place="ruin",
        animal="seal",
        obstacle="bell_lock",
        tool="flute",
        surprise="pebbles",
        name="Finn",
        gender="boy",
        helper="grandfather",
        helper_name="Grandpa Reed",
    ),
    StoryParams(
        place="garden",
        animal="fox",
        obstacle="rope_bridge",
        tool="ribbon",
        surprise="frog",
        name="Mira",
        gender="girl",
        helper="grandmother",
        helper_name="Grandma Rose",
    ),
    StoryParams(
        place="cave",
        animal="fox",
        obstacle="bell_lock",
        tool="flute",
        surprise="owl",
        name="Leo",
        gender="boy",
        helper="uncle",
        helper_name="Uncle Ash",
    ),
]


ASP_RULES = r"""
valid(P,A,O,T) :- place(P), animal(A), obstacle(O), tool(T), needs(O,N), solves(T,N).

scatters(A,S) :- animal(A), surprise(S), calmness(A,C), level(S,L), L > C.
direct(A,S)   :- animal(A), surprise(S), calmness(A,C), level(S,L), L <= C.

#show valid/4.
#show scatters/2.
#show direct/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in SETTINGS:
        lines.append(asp.fact("place", place_id))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        lines.append(asp.fact("calmness", animal_id, animal.calmness))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for need in sorted(tool.solves):
            lines.append(asp.fact("solves", tool_id, need))
    for surprise_id, surprise in SURPRISES.items():
        lines.append(asp.fact("surprise", surprise_id))
        lines.append(asp.fact("level", surprise_id, surprise.level))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_scatter_pairs() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "scatters")))


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_scatter = {
        (animal_id, surprise_id)
        for animal_id, animal in ANIMALS.items()
        for surprise_id, surprise in SURPRISES.items()
        if surprise_scatters(animal, surprise)
    }
    asp_scatter = set(asp_scatter_pairs())
    if py_scatter == asp_scatter:
        print(f"OK: scatter model matches ({len(py_scatter)} pairs).")
    else:
        rc = 1
        print("MISMATCH in scatter model:")
        if py_scatter - asp_scatter:
            print("  only in python:", sorted(py_scatter - asp_scatter))
        if asp_scatter - py_scatter:
            print("  only in clingo:", sorted(asp_scatter - py_scatter))

    try:
        sample = generate(CURATED[0])
        if not sample.story or sample.world is None:
            raise StoryError("smoke test produced an empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small rescue adventure with symmetry, surprise, and sound effects."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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


def _pick_child(rng: random.Random, gender: Optional[str]) -> tuple[str, str]:
    picked = gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if picked == "girl" else BOY_NAMES
    return rng.choice(pool), picked


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.obstacle:
        tool = TOOLS[args.tool]
        obstacle = OBSTACLES[args.obstacle]
        if not tool_fits(tool, obstacle):
            raise StoryError(explain_rejection(tool, obstacle))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.animal is None or combo[1] == args.animal)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, animal, obstacle, tool = rng.choice(sorted(combos))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    name, gender = _pick_child(rng, args.gender)
    helper = args.helper or rng.choice(sorted(HELPERS))
    helper_name = rng.choice(HELPERS[helper])

    if args.name:
        name = args.name

    return StoryParams(
        place=place,
        animal=animal,
        obstacle=obstacle,
        tool=tool,
        surprise=surprise,
        name=name,
        gender=gender,
        helper=helper,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (
        ("place", SETTINGS),
        ("animal", ANIMALS),
        ("obstacle", OBSTACLES),
        ("tool", TOOLS),
        ("surprise", SURPRISES),
        ("helper", HELPERS),
    ):
        value = getattr(params, key)
        if value not in table:
            raise StoryError(f"(Invalid {key}: {value})")

    if not tool_fits(TOOLS[params.tool], OBSTACLES[params.obstacle]):
        raise StoryError(explain_rejection(TOOLS[params.tool], OBSTACLES[params.obstacle]))

    world = tell(
        setting=SETTINGS[params.place],
        animal=ANIMALS[params.animal],
        obstacle=OBSTACLES[params.obstacle],
        tool=TOOLS[params.tool],
        surprise=SURPRISES[params.surprise],
        hero_name=params.name,
        hero_type=params.gender,
        helper_type=params.helper,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, animal, obstacle, tool) combos:\n")
        for place, animal, obstacle, tool in combos:
            print(f"  {place:8} {animal:6} {obstacle:12} {tool}")
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
            header = f"### {p.name}: {p.place}, {p.animal}, {p.obstacle}, {p.tool}, {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
