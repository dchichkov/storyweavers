#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kaput_repetition_tall_tale.py
========================================================

A standalone story world for a tall-tale domain: a child tries to haul an
impossibly huge farm prize to town in an old cart, the road bucks and bucks and
bucks, something goes kaput, and a helper must mend it sensibly.

The world is built to support:
- exaggerated, child-facing tall-tale prose
- explicit repetition in the traveling and boasting beats
- a reasonableness gate over which cargo/terrain combinations really create a
  "kaput cart" problem
- a common-sense gate over which repairs are sensible enough to tell
- an inline ASP twin for the compatibility and outcome logic

Run it
------
    python storyworlds/worlds/gpt-5.4/kaput_repetition_tall_tale.py
    python storyworlds/worlds/gpt-5.4/kaput_repetition_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/kaput_repetition_tall_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/kaput_repetition_tall_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/kaput_repetition_tall_tale.py --json
    python storyworlds/worlds/gpt-5.4/kaput_repetition_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
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
BREAK_LIMIT = 5
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
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
class Cargo:
    id: str
    label: str
    phrase: str
    heft: int
    wobble: int
    boast: str
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
class Terrain:
    id: str
    label: str
    path: str
    jolts: int
    refrain: str
    scene: str
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
class Fix:
    id: str
    label: str
    sense: int
    power: int
    action: str
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


@dataclass
class Destination:
    id: str
    label: str
    crowd: str
    ribbon: str
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


def _r_break(world: World) -> list[str]:
    cart = world.get("cart")
    if cart.meters["stress"] < BREAK_LIMIT:
        return []
    sig = ("break",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cart.meters["broken"] += 1
    cargo = world.get("cargo")
    cargo.meters["bruised"] += 1
    cargo.meters["sway"] += 1
    world.get("hero").memes["alarm"] += 1
    world.get("helper").memes["worry"] += 1
    return ["__kaput__"]


def _r_sag(world: World) -> list[str]:
    cart = world.get("cart")
    if cart.meters["broken"] < THRESHOLD:
        return []
    sig = ("sag",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("cargo").meters["danger"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="break", tag="physical", apply=_r_break),
    Rule(name="sag", tag="physical", apply=_r_sag),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def base_severity(cargo: Cargo, terrain: Terrain) -> int:
    return cargo.heft + cargo.wobble + terrain.jolts


def break_risk(cargo: Cargo, terrain: Terrain) -> bool:
    return base_severity(cargo, terrain) >= BREAK_LIMIT


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def total_severity(cargo: Cargo, terrain: Terrain, delay: int) -> int:
    return base_severity(cargo, terrain) + delay


def repair_holds(fix: Fix, cargo: Cargo, terrain: Terrain, delay: int) -> bool:
    return fix.power >= total_severity(cargo, terrain, delay)


def predict_kaput(world: World, cargo_cfg: Cargo, terrain: Terrain, delay: int) -> dict:
    sim = world.copy()
    roll_trip(sim, cargo_cfg, terrain, delay=delay, narrate=False)
    return {
        "kaput": sim.get("cart").meters["broken"] >= THRESHOLD,
        "bruised": sim.get("cargo").meters["bruised"],
        "stress": sim.get("cart").meters["stress"],
    }


def introduce(world: World, hero: Entity, helper: Entity, cargo_cfg: Cargo, destination: Destination) -> None:
    hero.memes["pride"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"Folks in Cloverpatch said {hero.id} could grow vegetables so large that sparrows used them for shade. "
        f"That summer {hero.pronoun()} raised {cargo_cfg.phrase}, {cargo_cfg.boast}."
    )
    world.say(
        f"{helper.id}, {hero.pronoun('possessive')} good neighbor, squinted at it and said it looked fit for {destination.label}."
    )


def load_cart(world: World, hero: Entity, helper: Entity, cargo_cfg: Cargo) -> None:
    cart = world.get("cart")
    cargo = world.get("cargo")
    cargo.meters["heft"] = float(cargo_cfg.heft)
    cargo.meters["sway"] = float(cargo_cfg.wobble)
    cart.meters["oldness"] = 1.0
    world.say(
        f"They rolled out an old farm cart with one squeaky wheel and one proud squeak besides. "
        f"It took {hero.id} pushing, {helper.id} pulling, and a fence post used as a lever to hoist the {cargo.label} aboard."
    )


def warn(world: World, hero: Entity, helper: Entity, cargo_cfg: Cargo, terrain: Terrain, delay: int) -> None:
    pred = predict_kaput(world, cargo_cfg, terrain, delay)
    world.facts["predicted_stress"] = pred["stress"]
    helper.memes["caution"] += 1
    world.say(
        f'{helper.id} tapped the wheel and said, "That road goes {terrain.refrain}. '
        f'That load goes wobble, wobble, wobble. If we are not careful, this cart will go kaput."'
    )
    if pred["kaput"]:
        world.say(
            f"{helper.id} could almost hear the axle groaning already. Even standing still, the trip looked harder than it looked."
        )


def boast(world: World, hero: Entity, terrain: Terrain, cargo_cfg: Cargo) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'{hero.id} grinned. "Kaput? Not this morning. I can take this {cargo_cfg.label} over {terrain.label}, '
        f'over {terrain.label}, over {terrain.label}, and still be in town before the lemonade gets warm."'
    )


def roll_trip(world: World, cargo_cfg: Cargo, terrain: Terrain, delay: int, narrate: bool = True) -> None:
    cart = world.get("cart")
    cargo = world.get("cargo")
    cart.meters["stress"] += float(total_severity(cargo_cfg, terrain, delay))
    cargo.meters["sway"] += float(terrain.jolts)
    produced = propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"Off they went along {terrain.path}, and the cart sang {terrain.refrain}, {terrain.refrain}, {terrain.refrain}."
        )
        if "__kaput__" in produced:
            world.say(
                f"Then there came a crack like a dry branch in winter, and one wheel went kaput, kaput, kaput."
            )


def scramble(world: World, hero: Entity, helper: Entity, cargo_cfg: Cargo) -> None:
    world.say(
        f"The great {cargo_cfg.label} tipped to one side, and both children sprang after it with their arms wide. "
        f"They did not let it roll away, but they did learn that bragging is lighter than hauling."
    )
    hero.memes["alarm"] += 1
    helper.memes["resolve"] += 1


def mend(world: World, hero: Entity, helper: Entity, fix: Fix) -> None:
    cart = world.get("cart")
    world.say(
        f"{helper.id} was not the sort to waste a good emergency. {helper.pronoun().capitalize()} {fix.action}."
    )
    cart.meters["repaired"] += 1
    cart.attrs["fix"] = fix.id
    hero.memes["hope"] += 1
    helper.memes["resolve"] += 1


def reach_town(world: World, hero: Entity, helper: Entity, destination: Destination, cargo_cfg: Cargo) -> None:
    cart = world.get("cart")
    cargo = world.get("cargo")
    cart.meters["broken"] = 0.0
    cart.meters["steady"] += 1
    cargo.meters["danger"] = 0.0
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After that, the cart rolled smooth as a song. It went over one bump, over another bump, over another bump, and never once complained."
    )
    world.say(
        f"When they reached {destination.label}, {destination.crowd} stared so hard you would have thought blinking had gone out of fashion."
    )
    world.say(
        f"The judges gave {hero.id} {destination.ribbon}, and children spent the rest of the afternoon patting the giant {cargo_cfg.label} as if it were a sleepy pony."
    )


def fail_mend(world: World, hero: Entity, helper: Entity, fix: Fix, cargo_cfg: Cargo) -> None:
    cart = world.get("cart")
    cargo = world.get("cargo")
    cart.meters["broken"] += 1
    cargo.meters["bruised"] += 1
    cargo.meters["split"] += 1
    hero.memes["sadness"] += 1
    helper.memes["sadness"] += 1
    world.say(
        f"{helper.id} {fix.fail}, but the old cart gave one mean shiver and went kaput all over again."
    )
    world.say(
        f"The giant {cargo_cfg.label} split with a soft thump, and seeds as big as pebbles bounced into the dust."
    )


def hopeful_ending(world: World, hero: Entity, helper: Entity, cargo_cfg: Cargo) -> None:
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"{hero.id} knelt and gathered the seeds instead of the brag. {helper.id} tucked them into a hat and said next year they could grow an even bigger one, only with a stronger cart from the start."
    )
    world.say(
        f"So the day was not a total loss: the prize was gone, but the promise of next year's giant {cargo_cfg.label} was already rattling in their pockets."
    )


def tell(
    cargo_cfg: Cargo,
    terrain: Terrain,
    fix: Fix,
    destination: Destination,
    hero_name: str = "Molly",
    hero_type: str = "girl",
    helper_name: str = "Jeb",
    helper_type: str = "boy",
    trait: str = "bold",
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", traits=["steady"]))
    cart = world.add(Entity(id="cart", type="cart", label="cart"))
    cargo = world.add(Entity(id="cargo", type="cargo", label=cargo_cfg.label))
    road = world.add(Entity(id="road", type="road", label=terrain.label, attrs={"terrain": terrain.id}))
    world.facts["repetition"] = terrain.refrain

    introduce(world, hero, helper, cargo_cfg, destination)
    load_cart(world, hero, helper, cargo_cfg)

    world.para()
    warn(world, hero, helper, cargo_cfg, terrain, delay)
    boast(world, hero, terrain, cargo_cfg)

    world.para()
    roll_trip(world, cargo_cfg, terrain, delay=delay, narrate=True)
    scramble(world, hero, helper, cargo_cfg)

    world.para()
    mend(world, hero, helper, fix)
    success = repair_holds(fix, cargo_cfg, terrain, delay)
    if success:
        reach_town(world, hero, helper, destination, cargo_cfg)
        outcome = "reached"
    else:
        fail_mend(world, hero, helper, fix, cargo_cfg)
        hopeful_ending(world, hero, helper, cargo_cfg)
        outcome = "split"

    world.facts.update(
        hero=hero,
        helper=helper,
        cart=cart,
        cargo_entity=cargo,
        road=road,
        cargo_cfg=cargo_cfg,
        terrain=terrain,
        fix=fix,
        destination=destination,
        delay=delay,
        severity=total_severity(cargo_cfg, terrain, delay),
        outcome=outcome,
        kaput=cart.meters["broken"] >= THRESHOLD or outcome == "split",
        repaired=cart.meters["repaired"] >= THRESHOLD,
        arrived=outcome == "reached",
        split=cargo.meters["split"] >= THRESHOLD,
    )
    return world


CARGOS = {
    "pumpkin": Cargo(
        id="pumpkin",
        label="pumpkin",
        phrase="a pumpkin so wide two calves could have napped in its shadow",
        heft=3,
        wobble=1,
        boast="orange as sunset and heavy as a week's worth of weather",
        tags={"pumpkin", "wagon"},
    ),
    "watermelon": Cargo(
        id="watermelon",
        label="watermelon",
        phrase="a watermelon as long as the washtub and twice as proud",
        heft=2,
        wobble=2,
        boast="striped like a little green planet with ideas of its own",
        tags={"watermelon", "wagon"},
    ),
    "cabbage": Cargo(
        id="cabbage",
        label="cabbage",
        phrase="a cabbage so round the geese tried to nest beside it",
        heft=2,
        wobble=1,
        boast="green, grand, and built like a rolled-up hill",
        tags={"cabbage", "wagon"},
    ),
    "turnip": Cargo(
        id="turnip",
        label="turnip",
        phrase="a turnip so enormous the moon looked at it twice",
        heft=4,
        wobble=1,
        boast="pale as cloud-light and stubborn as a stump",
        tags={"turnip", "wagon"},
    ),
}

TERRAINS = {
    "ruts": Terrain(
        id="ruts",
        label="the washboard ruts",
        path="the washboard ruts outside Cloverpatch",
        jolts=2,
        refrain="bumpity-bump",
        scene="The dirt road was ridged like a giant's old washboard.",
        tags={"road", "wheel"},
    ),
    "stony_hill": Terrain(
        id="stony_hill",
        label="the stony hill",
        path="the stony hill road",
        jolts=3,
        refrain="clatter-clack",
        scene="The hill was full of stones that stuck up like knuckles.",
        tags={"road", "wheel"},
    ),
    "creek_bridge": Terrain(
        id="creek_bridge",
        label="the creek bridge",
        path="the narrow plank bridge over Muddy Creek",
        jolts=2,
        refrain="thumpety-thump",
        scene="The planks hopped under wheels as if they had springs.",
        tags={"bridge", "wheel"},
    ),
    "meadow": Terrain(
        id="meadow",
        label="the soft meadow lane",
        path="the soft meadow lane",
        jolts=0,
        refrain="swish-swish",
        scene="The lane lay soft and level as a quilt.",
        tags={"road"},
    ),
}

FIXES = {
    "hickory_spokes": Fix(
        id="hickory_spokes",
        label="new hickory spokes",
        sense=3,
        power=6,
        action="cut fresh hickory spokes, drove them in snug, and wrapped the hub tight with farmer's twine",
        fail="cut fresh hickory spokes and jammed them in as fast as lightning",
        qa_text="mended the wheel with fresh hickory spokes and a tight wrap of twine",
        tags={"wheel", "hickory"},
    ),
    "iron_band": Fix(
        id="iron_band",
        label="an iron band",
        sense=3,
        power=7,
        action="borrowed an iron band from the smithy wagon, hammered it round the wheel, and made the axle sit straight again",
        fail="borrowed an iron band and hammered away bravely",
        qa_text="hammered an iron band around the wheel and straightened the axle",
        tags={"wheel", "iron"},
    ),
    "sap_glue": Fix(
        id="sap_glue",
        label="pine sap glue",
        sense=2,
        power=5,
        action="melted pine sap in a tin cup, packed the crack, and lashed the wheel with a strip of cloth until it held",
        fail="smeared pine sap into the crack and tied cloth around it",
        qa_text="sealed the cracked wheel with pine sap and cloth",
        tags={"wheel", "sap"},
    ),
    "rope_knot": Fix(
        id="rope_knot",
        label="a rope knot",
        sense=1,
        power=3,
        action="tied the wheel together with a rope knot and hoped hope would do the rest",
        fail="tied a rope knot around the wheel and gave it a hopeful pat",
        qa_text="tied the wheel with a rope knot",
        tags={"wheel", "rope"},
    ),
}

DESTINATIONS = {
    "county_fair": Destination(
        id="county_fair",
        label="the county fair",
        crowd="the pie judges and pie eaters and pie dreamers",
        ribbon="a blue ribbon as wide as a supper plate",
        tags={"fair"},
    ),
    "harvest_parade": Destination(
        id="harvest_parade",
        label="the harvest parade",
        crowd="the brass band and the crowd along Main Street",
        ribbon="a gold rosette that flapped like a happy sunflower",
        tags={"parade"},
    ),
    "market_day": Destination(
        id="market_day",
        label="market day",
        crowd="the grocers and gossipers under the striped awnings",
        ribbon="the mayor's brightest prize card",
        tags={"market"},
    ),
}

GIRL_NAMES = ["Molly", "Daisy", "Nell", "Ruby", "June", "Tess", "Sadie", "May"]
BOY_NAMES = ["Jeb", "Eli", "Hank", "Otis", "Beau", "Cal", "Ned", "Wes"]
TRAITS = ["bold", "cheerful", "stubborn", "plucky", "booming"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for cargo_id, cargo in CARGOS.items():
        for terrain_id, terrain in TERRAINS.items():
            if break_risk(cargo, terrain):
                combos.append((cargo_id, terrain_id))
    return combos


@dataclass
class StoryParams:
    cargo: str
    terrain: str
    fix: str
    destination: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    trait: str
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
    "wagon": [
        (
            "What does a farm cart or wagon wheel do?",
            "A wagon wheel helps a heavy cart roll instead of drag. If the wheel breaks, the cart tips and hauling gets much harder."
        )
    ],
    "wheel": [
        (
            "What does it mean when something mechanical is kaput?",
            "It means it is broken and not working the way it should. People often say it when a wheel, toy, or tool suddenly gives up."
        )
    ],
    "hickory": [
        (
            "Why is hickory wood good for a wheel?",
            "Hickory is a very tough wood, so it can take hard knocks without snapping easily. That is why people have used it for tool handles and wagon parts."
        )
    ],
    "iron": [
        (
            "Why would an iron band make a wheel stronger?",
            "Iron can hold the outer part of a wheel tight so the pieces stay together. A strong band helps the wheel keep its round shape under a heavy load."
        )
    ],
    "sap": [
        (
            "What is pine sap?",
            "Pine sap is the sticky stuff that comes from a pine tree. It can glue little things for a while, though it is not as strong as a real metal repair."
        )
    ],
    "pumpkin": [
        (
            "What is a pumpkin?",
            "A pumpkin is a round orange squash that grows on a vine. People eat it, carve it, and sometimes show the biggest ones at fairs."
        )
    ],
    "watermelon": [
        (
            "What is a watermelon?",
            "A watermelon is a big juicy fruit with a thick green rind. It is heavy because it is full of water."
        )
    ],
    "cabbage": [
        (
            "What is a cabbage?",
            "A cabbage is a leafy green vegetable that grows into a round head. The leaves wrap around each other in many layers."
        )
    ],
    "turnip": [
        (
            "What is a turnip?",
            "A turnip is a root vegetable that grows partly underground. It can be small, but in a tall tale it can grow to a silly giant size."
        )
    ],
    "fair": [
        (
            "What happens at a county fair?",
            "People bring animals, pies, vegetables, and crafts to show what they made or grew. Judges often hand out ribbons for the best ones."
        )
    ],
    "parade": [
        (
            "What is a parade?",
            "A parade is a line of people, music, floats, or wagons moving through town for everyone to watch. It is meant to be seen and cheered."
        )
    ],
    "market": [
        (
            "What is market day?",
            "Market day is a day when people bring goods to town to sell or trade. It is usually busy, noisy, and full of talking."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "wagon",
    "wheel",
    "hickory",
    "iron",
    "sap",
    "pumpkin",
    "watermelon",
    "cabbage",
    "turnip",
    "fair",
    "parade",
    "market",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cargo = f["cargo_cfg"]
    terrain = f["terrain"]
    destination = f["destination"]
    outcome = f["outcome"]
    if outcome == "reached":
        return [
            f'Write a tall-tale story for a 3-to-5-year-old that includes the word "kaput" and uses repetition. A child hauls a giant {cargo.label} over {terrain.label} to {destination.label}.',
            f'Write a funny farm tall tale where the road goes "{terrain.refrain}, {terrain.refrain}, {terrain.refrain}" and a cart wheel goes kaput before a clever repair saves the day.',
            f'Write a child-facing story with a giant vegetable, a broken cart, repeated sound words, and a happy ending at {destination.label}.',
        ]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the word "kaput" and uses repetition. A child hauls a giant {cargo.label} over {terrain.label}, but the repair does not hold.',
        f'Write a funny-but-gentle tall tale where the cart goes kaput, kaput, kaput and the giant {cargo.label} splits, yet the ending still leaves hope for next year.',
        f'Write a farm story with repeated travel sounds, an exaggerated load, and a lesson that a strong job needs a strong fix.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    cargo = f["cargo_cfg"]
    terrain = f["terrain"]
    fix = f["fix"]
    destination = f["destination"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who grew a giant {cargo.label}, and {helper.id}, the neighbor who helped with the cart. Together they tried to haul the enormous load to {destination.label}."
        ),
        (
            f"Why did {helper.id} think the cart might go kaput?",
            f"{helper.id} saw that the load was huge and the road went {terrain.refrain}, {terrain.refrain}, {terrain.refrain}. That meant the old wheel would have to take too many hard jolts for such a heavy trip."
        ),
        (
            "What part of the story uses repetition?",
            f"The story repeats the road sound -- {terrain.refrain}, {terrain.refrain}, {terrain.refrain} -- and even repeats kaput when the wheel breaks. The repetition makes the trip feel bouncy and bigger than life, like a tall tale should."
        ),
        (
            "What happened on the road?",
            f"As the cart rattled along {terrain.path}, the wheel cracked and went kaput. The giant {cargo.label} tipped hard because the rough trip put too much stress on the old cart."
        ),
    ]
    if outcome == "reached":
        qa.append(
            (
                f"How did {helper.id} fix the problem?",
                f"{helper.id} {fix.qa_text}. That repair was strong enough for the heavy load and the rough road, so the cart could roll the rest of the way safely."
            )
        )
        qa.append(
            (
                f"How did the story end?",
                f"{hero.id} reached {destination.label} with the giant {cargo.label}, and the crowd stared in amazement. The ending proves what changed: after the mend, the cart that had gone kaput could roll smoothly again."
            )
        )
    else:
        qa.append(
            (
                f"Why did the repair fail?",
                f"The fix was not strong enough for a load that heavy on a road that rough. So even after {helper.id} tried to mend it, the cart went kaput again and the giant {cargo.label} split."
            )
        )
        qa.append(
            (
                "Was the ending all bad?",
                f"No. They lost the prize for that day, but they saved the giant seeds and planned for next year. The story ends with hope because they learned that a big job needs a strong cart and a strong repair."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"wagon", "wheel"}
    tags |= set(f["cargo_cfg"].tags)
    tags |= set(f["fix"].tags)
    tags |= set(f["destination"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        cargo="pumpkin",
        terrain="ruts",
        fix="hickory_spokes",
        destination="county_fair",
        hero="Molly",
        hero_gender="girl",
        helper="Jeb",
        helper_gender="boy",
        trait="bold",
        delay=0,
    ),
    StoryParams(
        cargo="turnip",
        terrain="stony_hill",
        fix="iron_band",
        destination="harvest_parade",
        hero="Nell",
        hero_gender="girl",
        helper="Otis",
        helper_gender="boy",
        trait="plucky",
        delay=1,
    ),
    StoryParams(
        cargo="watermelon",
        terrain="creek_bridge",
        fix="sap_glue",
        destination="market_day",
        hero="Eli",
        hero_gender="boy",
        helper="Ruby",
        helper_gender="girl",
        trait="cheerful",
        delay=1,
    ),
    StoryParams(
        cargo="turnip",
        terrain="stony_hill",
        fix="sap_glue",
        destination="county_fair",
        hero="June",
        hero_gender="girl",
        helper="Cal",
        helper_gender="boy",
        trait="stubborn",
        delay=2,
    ),
    StoryParams(
        cargo="pumpkin",
        terrain="creek_bridge",
        fix="iron_band",
        destination="harvest_parade",
        hero="Wes",
        hero_gender="boy",
        helper="Daisy",
        helper_gender="girl",
        trait="booming",
        delay=0,
    ),
]


def explain_rejection(cargo: Cargo, terrain: Terrain) -> str:
    return (
        f"(No story: {cargo.label} over {terrain.label} would not strain the cart enough to make anything go kaput. "
        f"This world only tells versions where the trip honestly creates a broken-wheel problem.)"
    )


def explain_fix_rejection(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of these sturdier repairs: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return (
        "reached"
        if repair_holds(FIXES[params.fix], CARGOS[params.cargo], TERRAINS[params.terrain], params.delay)
        else "split"
    )


ASP_RULES = r"""
break_risk(C,T) :- cargo(C), terrain(T), heft(C,H), wobble(C,W), jolts(T,J), min_break(M), H + W + J >= M.
sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.
valid(C,T) :- cargo(C), terrain(T), break_risk(C,T).

severity(V) :- chosen_cargo(C), chosen_terrain(T), chosen_delay(D),
               heft(C,H), wobble(C,W), jolts(T,J), V = H + W + J + D.
holds :- chosen_fix(F), power(F,P), severity(V), P >= V.
outcome(reached) :- holds.
outcome(split) :- not holds.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cargo_id, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("heft", cargo_id, cargo.heft))
        lines.append(asp.fact("wobble", cargo_id, cargo.wobble))
    for terrain_id, terrain in TERRAINS.items():
        lines.append(asp.fact("terrain", terrain_id))
        lines.append(asp.fact("jolts", terrain_id, terrain.jolts))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
    lines.append(asp.fact("min_break", BREAK_LIMIT))
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
    return sorted(item for (item,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_cargo", params.cargo),
            asp.fact("chosen_terrain", params.terrain),
            asp.fact("chosen_fix", params.fix),
            asp.fact("chosen_delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    clingo_fixes = set(asp_sensible())
    python_fixes = {fix.id for fix in sensible_fixes()}
    if clingo_fixes == python_fixes:
        print(f"OK: sensible fixes match ({sorted(clingo_fixes)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_fixes)} python={sorted(python_fixes)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="verify smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a giant farm prize, a bumpy road, and a cart that may go kaput."
    )
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--terrain", choices=TERRAINS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra bumps after the first crack before the cart fully settles")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid cargo/terrain combos and sensible fixes from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.terrain:
        cargo = CARGOS[args.cargo]
        terrain = TERRAINS[args.terrain]
        if not break_risk(cargo, terrain):
            raise StoryError(explain_rejection(cargo, terrain))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cargo is None or combo[0] == args.cargo)
        and (args.terrain is None or combo[1] == args.terrain)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cargo_id, terrain_id = rng.choice(sorted(combos))
    fix_id = args.fix or rng.choice(sorted(fix.id for fix in sensible_fixes()))
    destination_id = args.destination or rng.choice(sorted(DESTINATIONS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or _pick_name(rng, hero_gender)
    helper_name = args.helper or _pick_name(rng, helper_gender, avoid=hero_name)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        cargo=cargo_id,
        terrain=terrain_id,
        fix=fix_id,
        destination=destination_id,
        hero=hero_name,
        hero_gender=hero_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cargo not in CARGOS:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.terrain not in TERRAINS:
        raise StoryError(f"(Unknown terrain: {params.terrain})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(params.fix))
    if not break_risk(CARGOS[params.cargo], TERRAINS[params.terrain]):
        raise StoryError(explain_rejection(CARGOS[params.cargo], TERRAINS[params.terrain]))

    world = tell(
        cargo_cfg=CARGOS[params.cargo],
        terrain=TERRAINS[params.terrain],
        fix=FIXES[params.fix],
        destination=DESTINATIONS[params.destination],
        hero_name=params.hero,
        hero_type=params.hero_gender,
        helper_name=params.helper,
        helper_type=params.helper_gender,
        trait=params.trait,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (cargo, terrain) combos:\n")
        for cargo_id, terrain_id in combos:
            print(f"  {cargo_id:10} {terrain_id}")
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
            header = (
                f"### {p.hero} hauls {p.cargo} over {p.terrain} "
                f"({p.fix}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
