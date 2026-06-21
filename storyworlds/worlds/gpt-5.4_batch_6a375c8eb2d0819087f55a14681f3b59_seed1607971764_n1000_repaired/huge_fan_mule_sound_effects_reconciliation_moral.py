#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/huge_fan_mule_sound_effects_reconciliation_moral.py
================================================================================

A standalone story world for a tall-tale flavored story about a child, a huge
fan, and a patient mule. The world models a boastful attempt to help on a hot
day, an overblown gust that causes a muddle, and a reconciliation grounded in
repair, apology, and kindness.

Reference seed:
---------------
Write a story that includes the words "huge", "fan", and "mule", using Sound
Effects, Reconciliation, and Moral Value in a Tall Tale style.

World premise:
--------------
A child sees a hardworking mule straining in the heat and boasts that a huge fan
can cool the mule faster than a cloud can cross the sky. Sometimes that braggy
help goes wrong: the wind startles the mule or scatters light cargo. The child
must then slow down, apologize, and choose a sensible way to make things right.
The ending proves the moral value: kindness is better than showing off, and
making amends matters.

Run it:
-------
python storyworlds/worlds/gpt-5.4/huge_fan_mule_sound_effects_reconciliation_moral.py
python storyworlds/worlds/gpt-5.4/huge_fan_mule_sound_effects_reconciliation_moral.py --place orchard --cargo apples
python storyworlds/worlds/gpt-5.4/huge_fan_mule_sound_effects_reconciliation_moral.py --cargo stones
python storyworlds/worlds/gpt-5.4/huge_fan_mule_sound_effects_reconciliation_moral.py --repair song
python storyworlds/worlds/gpt-5.4/huge_fan_mule_sound_effects_reconciliation_moral.py --all
python storyworlds/worlds/gpt-5.4/huge_fan_mule_sound_effects_reconciliation_moral.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/huge_fan_mule_sound_effects_reconciliation_moral.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    owner: Optional[str] = None
    # physical / emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        animal = {"mule"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    sky: str
    ground: str
    heat: int
    affords: set[str] = field(default_factory=set)
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
    pile: str
    spill_text: str
    gather_text: str
    heavy: bool
    blowable: bool
    heat_need: int
    sound: str
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
class FanKind:
    id: str
    label: str
    phrase: str
    boast: str
    gust_sound: str
    power: int
    bulky: bool = True
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
class Repair:
    id: str
    label: str
    sense: int
    calms_mule: int
    restores_cargo: int
    text: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "dust_flurry": False,
            "cargo_spilled": False,
            "mule_startled": False,
        }

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


def _r_heat(world: World) -> list[str]:
    out: list[str] = []
    mule = world.get("mule")
    cargo = world.get("cargo")
    if mule.meters["pulling"] < THRESHOLD:
        return out
    sig = ("heat", "mule")
    if sig in world.fired:
        return out
    if world.place.heat + int(cargo.attrs.get("heat_need", 0)) >= 4:
        world.fired.add(sig)
        mule.meters["hot"] += 1
        out.append("__hot__")
    return out


def _r_gust_trouble(world: World) -> list[str]:
    out: list[str] = []
    mule = world.get("mule")
    fan = world.get("fan")
    cargo = world.get("cargo")
    if fan.meters["spinning"] < THRESHOLD:
        return out
    sig = ("gust", "trouble")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["dust_flurry"] = True
    if fan.attrs.get("power", 0) >= 3:
        mule.meters["startled"] += 1
        mule.memes["alarm"] += 1
        world.facts["mule_startled"] = True
    if cargo.attrs.get("blowable", False) and fan.attrs.get("power", 0) >= 2:
        cargo.meters["spilled"] += 1
        world.facts["cargo_spilled"] = True
    out.append("__gust__")
    return out


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    mule = world.get("mule")
    cargo = world.get("cargo")
    if mule.meters["startled"] < THRESHOLD and cargo.meters["spilled"] < THRESHOLD:
        return out
    sig = ("tension", "after")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["guilt"] += 1
    child.memes["pride"] = 0.0
    mule.memes["trust"] -= 1
    mule.memes["uneasy"] += 1
    if cargo.meters["spilled"] >= THRESHOLD:
        world.get("driver").meters["workload"] += 1
    out.append("__tension__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    mule = world.get("mule")
    cargo = world.get("cargo")
    repair = world.get("repair")
    if child.meters["apologized"] < THRESHOLD:
        return out
    if repair.attrs.get("calms_mule", 0) >= 1:
        mule.meters["startled"] = 0.0
        mule.memes["uneasy"] = 0.0
        mule.memes["trust"] += 1
    if cargo.meters["spilled"] >= THRESHOLD and repair.attrs.get("restores_cargo", 0) >= 1:
        cargo.meters["spilled"] = 0.0
        cargo.meters["restored"] += 1
        world.get("driver").meters["workload"] = max(0.0, world.get("driver").meters["workload"] - 1)
    sig = ("repair", repair.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["humility"] += 1
    child.memes["care"] += 1
    out.append("__repair__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="heat", tag="physical", apply=_r_heat),
    Rule(name="gust_trouble", tag="physical", apply=_r_gust_trouble),
    Rule(name="tension", tag="social", apply=_r_tension),
    Rule(name="repair", tag="social", apply=_r_repair),
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


def needs_cooling(place: Place, cargo: Cargo) -> bool:
    return cargo.heavy and place.heat >= cargo.heat_need


def repair_works(repair: Repair, cargo: Cargo) -> bool:
    if repair.sense < SENSE_MIN:
        return False
    needs_restore = cargo.blowable
    if needs_restore:
        return repair.calms_mule >= 1 and repair.restores_cargo >= 1
    return repair.calms_mule >= 1


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    fan = sim.get("fan")
    fan.meters["spinning"] += 1
    propagate(sim, narrate=False)
    return {
        "mule_startled": sim.facts["mule_startled"],
        "cargo_spilled": sim.facts["cargo_spilled"],
    }


def trouble_happens(fan: FanKind, cargo: Cargo) -> bool:
    return fan.power >= 3 or (fan.power >= 2 and cargo.blowable)


def explain_rejection(place: Place, cargo: Cargo) -> str:
    return (
        f"(No story: {cargo.label} on {place.label} does not make the mule hot enough "
        f"to need the huge fan, so there is no honest brag, blunder, and repair. "
        f"Pick a heavier load or a hotter place.)"
    )


def explain_repair(rid: str) -> str:
    rep = REPAIRS[rid]
    options = ", ".join(sorted(k for k, v in REPAIRS.items() if v.sense >= SENSE_MIN))
    return (
        f"(Refusing repair '{rid}': it is too weak or showy for a real reconciliation "
        f"(sense={rep.sense} < {SENSE_MIN} or it does not fix the problem). Try: {options}.)"
    )


def outcome_of(params: "StoryParams") -> str:
    place = PLACES[params.place]
    cargo = CARGOES[params.cargo]
    fan = FANS[params.fan]
    repair = REPAIRS[params.repair]
    if not trouble_happens(fan, cargo):
        return "smooth"
    if repair_works(repair, cargo):
        return "reconciled"
    return "soured"
def tell(
    cargo_cfg: Cargo,
    fan_cfg: Fan,
    repair_cfg: Repair,
    child_name: str,
    child_type: ChildType,
    driver_type: DriverType,
    child_trait: ChildTrait,
    mule_name: str,
    place=None,
) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        traits=["young", child_trait],
        attrs={},
    ))
    driver = world.add(Entity(
        id="Driver",
        kind="character",
        type=driver_type,
        role="driver",
        label="the driver",
        attrs={},
    ))
    mule = world.add(Entity(
        id=mule_name,
        kind="character",
        type="mule",
        role="mule",
        attrs={},
    ))
    cargo = world.add(Entity(
        id="cargo",
        kind="thing",
        type="cargo",
        label=cargo_cfg.label,
        attrs={
            "blowable": cargo_cfg.blowable,
            "heavy": cargo_cfg.heavy,
            "heat_need": cargo_cfg.heat_need,
            "sound": cargo_cfg.sound,
        },
    ))
    fan = world.add(Entity(
        id="fan",
        kind="thing",
        type="fan",
        label=fan_cfg.label,
        attrs={
            "power": fan_cfg.power,
            "bulky": fan_cfg.bulky,
        },
    ))
    repair = world.add(Entity(
        id="repair",
        kind="thing",
        type="repair",
        label=repair_cfg.label,
        attrs={
            "calms_mule": repair_cfg.calms_mule,
            "restores_cargo": repair_cfg.restores_cargo,
            "sense": repair_cfg.sense,
        },
    ))

    child.memes["pride"] = 1.0
    child.memes["care"] = 1.0
    mule.memes["trust"] = 1.0
    mule.meters["pulling"] = 1.0
    cargo.meters["loaded"] = 1.0
    driver.meters["workload"] = 0.0

    propagate(world, narrate=False)

    world.say(
        f"On {place.label}, under {place.sky}, {mule_name} the mule pulled {cargo_cfg.pile} "
        f"over {place.ground}. Folks said the day was so hot that fence posts wished for shade."
    )
    world.say(
        f"{child_name} trotted beside the wagon carrying {fan_cfg.phrase}, a huge fan so wide "
        f"it looked fit to cool a courthouse."
    )
    world.say(
        f'"I can help faster than a breeze can blink," {child_name} said. "{fan_cfg.boast}"'
    )

    world.para()
    world.say(
        f"{mule_name}'s hooves went {cargo_cfg.sound}, and sweat darkened the strap by his neck. "
        f"{child_name} meant to be kind, but the boast made the help feel bigger than it was."
    )

    pred = predict_trouble(world)
    world.facts["predicted_mule_startled"] = pred["mule_startled"]
    world.facts["predicted_cargo_spilled"] = pred["cargo_spilled"]

    driver_word = driver.label_word
    if pred["mule_startled"] or pred["cargo_spilled"]:
        warning_parts = []
        if pred["mule_startled"]:
            warning_parts.append(f"spook {mule_name}")
        if pred["cargo_spilled"]:
            warning_parts.append(f"send the {cargo_cfg.label} flying")
        joined = " and ".join(warning_parts)
        world.say(
            f'"Easy now," said the {driver_word}. "That mighty fan could {joined}."'
        )
    else:
        world.say(
            f'"Easy now," said the {driver_word}. "Kind hands help best when they go slow."'
        )

    world.para()
    fan.meters["spinning"] += 1
    world.say(
        f"But {child_name} gave the handle one eager crank. {fan_cfg.gust_sound}! The huge fan "
        f"pushed out a gust strong enough to rattle a signpost."
    )
    propagate(world, narrate=False)

    if world.facts["cargo_spilled"] and world.facts["mule_startled"]:
        world.say(
            f"{mule_name} lurched sideways with a startled hee-haw, and the top of the load "
            f"{cargo_cfg.spill_text}."
        )
    elif world.facts["mule_startled"]:
        world.say(
            f"{mule_name} jumped with a sharp snort and planted all four hooves, too startled to "
            f"pull another inch."
        )
    elif world.facts["cargo_spilled"]:
        world.say(
            f"The wind skipped under the load, and {cargo_cfg.spill_text}."
        )
    else:
        world.say(
            f"The breeze cooled {mule_name} without one bit of fuss, and even the wagon seemed to sigh."
        )

    world.para()
    if world.facts["mule_startled"] or world.facts["cargo_spilled"]:
        child.meters["apologized"] += 1
        world.say(
            f"The brag blew right out of {child_name}. {child.pronoun().capitalize()} lowered the fan, "
            f'''looked at {mule_name}, and whispered, \"I was trying to show off. I'm sorry.\"'''
        )
        world.say(
            repair_cfg.text.format(
                child=child_name,
                mule=mule_name,
                cargo=cargo_cfg.label,
                gather=cargo_cfg.gather_text,
                driver=driver_word,
            )
        )
        propagate(world, narrate=False)

        if repair_works(repair_cfg, cargo_cfg):
            if cargo_cfg.blowable:
                world.say(
                    f"Soon the road was orderly again, {mule_name}'s ears tipped forward, and the "
                    f"{driver_word} nodded. The work went on slower than bragging but stronger than noise."
                )
            else:
                world.say(
                    f"Little by little, {mule_name}'s neck loosened, and the wagon started forward again. "
                    f"The {driver_word} smiled because the help had finally turned gentle."
                )
            world.say(
                f"By the end of the road, folks were saying the biggest thing on {place.label} was not the "
                f"huge fan at all, but the size of a true apology."
            )
        else:
            world.say(
                f"But the fix was too small for the muddle. {mule_name} stayed uneasy, the {driver_word} "
                f"had more work than before, and {child_name} learned that sorry words need steady deeds."
            )
    else:
        world.say(
            f"{child_name} grinned, but this time {child.pronoun()} remembered to walk beside {mule_name} "
            f"instead of boasting ahead of him."
        )
        world.say(
            f"By sunset the whole road felt cooler, and the {driver_word} said that even a tall tale grows "
            f"better when kindness stands taller than pride."
        )

    world.facts.update(
        child=child,
        driver=driver,
        mule=mule,
        cargo_cfg=cargo_cfg,
        cargo=cargo,
        fan_cfg=fan_cfg,
        fan=fan,
        repair_cfg=repair_cfg,
        repair=repair,
        trouble=world.facts["mule_startled"] or world.facts["cargo_spilled"],
        outcome=outcome_of(StoryParams(
            place=place.id,
            cargo=cargo_cfg.id,
            fan=fan_cfg.id,
            repair=repair_cfg.id,
            child_name=child_name,
            child_gender=child_type,
            driver=driver_type,
            trait=child_trait,
            mule_name=mule_name,
            seed=None,
        )),
        moral="Kindness works better than showing off, and a real apology should be followed by helpful action.",
    )
    return world
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


PLACES = {
    "orchard": Place(
        id="orchard",
        label="the long orchard road",
        sky="a white-hot noon sky",
        ground="rutted dust between the apple trees",
        heat=3,
        affords={"apples", "hay"},
        tags={"heat", "orchard"},
    ),
    "mesa": Place(
        id="mesa",
        label="the red mesa trail",
        sky="a coppery sky with no cloud in it",
        ground="baked red earth",
        heat=3,
        affords={"hay", "beans", "stones"},
        tags={"heat", "trail"},
    ),
    "river": Place(
        id="river",
        label="the river market road",
        sky="a bright summer sky above the shallows",
        ground="a packed lane by the water",
        heat=2,
        affords={"apples", "beans"},
        tags={"river", "market"},
    ),
}

CARGOES = {
    "apples": Cargo(
        id="apples",
        label="apples",
        pile="a wagon stacked with apple crates",
        spill_text="three red apples bounded into the ditch, bump-bump-bump",
        gather_text="gathered the runaway apples and tucked them back into the crate",
        heavy=True,
        blowable=True,
        heat_need=2,
        sound="clop-clop",
        tags={"apples", "wagon"},
    ),
    "beans": Cargo(
        id="beans",
        label="bean sacks",
        pile="a wagon piled with bean sacks",
        spill_text="a loose sack tipped and beans pattered over the boards, pitter-patter-pat",
        gather_text="caught the loose sack and scooped the beans back before more could spill",
        heavy=True,
        blowable=True,
        heat_need=2,
        sound="chunk-clop",
        tags={"beans", "wagon"},
    ),
    "hay": Cargo(
        id="hay",
        label="hay bales",
        pile="a hay wagon stacked taller than a porch roof",
        spill_text="a ragged spray of hay whisked loose and spun across the ditch, fwish-fwish",
        gather_text="patted the loose hay back in place and tied the rope tighter",
        heavy=True,
        blowable=True,
        heat_need=3,
        sound="creak-clop",
        tags={"hay", "wagon"},
    ),
    "stones": Cargo(
        id="stones",
        label="flat stones",
        pile="a low cart of flat stones",
        spill_text="not one stone moved",
        gather_text="brushed dust off the cart",
        heavy=True,
        blowable=False,
        heat_need=3,
        sound="thunk-clop",
        tags={"stones", "cart"},
    ),
}

FANS = {
    "banner_fan": FanKind(
        id="banner_fan",
        label="banner fan",
        phrase="a canvas fan on a hickory pole",
        boast="This fan can cool a mule from nose to tail in one whoosh",
        gust_sound="WHUP-WHUP",
        power=2,
        tags={"fan", "wind"},
    ),
    "windmill_fan": FanKind(
        id="windmill_fan",
        label="windmill fan",
        phrase="a windmill fan with painted blades",
        boast="This fan can stir dust off the moon and still leave my mule smiling",
        gust_sound="WHIRR-THRUM",
        power=3,
        tags={"fan", "wind"},
    ),
}

REPAIRS = {
    "water_and_gather": Repair(
        id="water_and_gather",
        label="water and gathering",
        sense=3,
        calms_mule=1,
        restores_cargo=1,
        text=(
            "{child} fetched cool water for {mule}, stroked his nose, and then {gather}. "
            "After that, {child} walked quietly beside the wagon instead of making speeches."
        ),
        qa_text="brought the mule cool water, soothed him, and gathered the spilled load",
        tags={"water", "apology", "repair"},
    ),
    "retie_and_pat": Repair(
        id="retie_and_pat",
        label="retie and pat",
        sense=3,
        calms_mule=1,
        restores_cargo=1,
        text=(
            "{child} helped the {driver} retie the load, patted {mule}'s neck, and spoke in a low voice "
            "until his ears settled."
        ),
        qa_text="helped retie the load and calmed the mule with a gentle hand and quiet words",
        tags={"apology", "repair"},
    ),
    "song": Repair(
        id="song",
        label="a showy song",
        sense=1,
        calms_mule=0,
        restores_cargo=0,
        text=(
            "{child} sang a grand song to the sky, but singing did not gather the mess or steady the mule."
        ),
        qa_text="sang instead of fixing the real problem",
        tags={"song"},
    ),
}

GIRL_NAMES = ["Lula", "Mira", "Josie", "Nell", "Ruby", "Tess", "Ada", "Clara"]
BOY_NAMES = ["Jeb", "Eli", "Toby", "Finn", "Hank", "Cal", "Ben", "Otis"]
MULE_NAMES = ["Juniper", "Dusty", "Mossback", "Clover", "Whistle", "Brass Hoof"]
TRAITS = ["eager", "boastful", "helpful", "spirited", "bright"]
DRIVERS = ["mother", "father"]


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for cargo_id in sorted(place.affords):
            cargo = CARGOES[cargo_id]
            if not needs_cooling(place, cargo):
                continue
            for fan_id in FANS:
                if not trouble_happens(FANS[fan_id], cargo):
                    continue
                combos.append((place_id, cargo_id, fan_id))
    return combos


KNOWLEDGE = {
    "fan": [
        (
            "What does a fan do?",
            "A fan moves air. The moving air can help a hot person or animal feel cooler."
        )
    ],
    "mule": [
        (
            "What is a mule?",
            "A mule is a strong working animal. People often use mules to pull or carry heavy things."
        )
    ],
    "heat": [
        (
            "Why can a mule get tired on a hot day?",
            "Heat makes hard work feel heavier. A mule pulling a load in the sun can need rest, shade, and water."
        )
    ],
    "apples": [
        (
            "Why can apples roll away so easily?",
            "Apples are round, so once they start moving they can bounce and roll. That makes a spilled crate hard to tidy quickly."
        )
    ],
    "beans": [
        (
            "Why are loose beans hard to clean up?",
            "Small beans scatter in many directions. You have to slow down and gather them carefully."
        )
    ],
    "hay": [
        (
            "Why can hay blow in the wind?",
            "Hay is light and fluffy, so a strong gust can whisk it away. That is why hay loads are tied down."
        )
    ],
    "water": [
        (
            "Why does cool water help a tired animal?",
            "Cool water helps the body feel better after hard work in the heat. It is also a gentle way to care for an animal."
        )
    ],
    "repair": [
        (
            "What does it mean to make things right after a mistake?",
            "It means you do more than say sorry. You help fix the problem you caused."
        )
    ],
    "apology": [
        (
            "Why is an apology important?",
            "An apology shows that you understand you caused hurt or trouble. A good apology is followed by kinder actions."
        )
    ],
}
KNOWLEDGE_ORDER = ["fan", "mule", "heat", "apples", "beans", "hay", "water", "repair", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mule = f["mule"]
    cargo = f["cargo_cfg"]
    place = world.place
    outcome = f["outcome"]
    if outcome == "reconciled":
        return [
            f'Write a tall tale for a young child that includes the words "huge", "fan", and "mule". Set it on {place.label} and make the child cause a windy mess before making things right.',
            f"Tell a playful story where {child.id} tries to help {mule.id} the mule with a huge fan, but the gust causes trouble and the child must apologize and repair the mistake.",
            'Write a gentle tall tale with sound effects, reconciliation, and a clear moral that kindness matters more than showing off.',
        ]
    if outcome == "soured":
        return [
            f'Write a cautionary tall tale using "huge", "fan", and "mule" where a boastful helper makes a mess on {place.label} and learns that saying sorry without real help is not enough.',
            f"Tell a story where {child.id} tries to cool {mule.id} with a huge fan, but the chosen fix is too weak, so the lesson lands the hard way.",
            'Write a story with sound effects and a moral about pride, apology, and responsibility.',
        ]
    return [
        f'Write a tall tale using "huge", "fan", and "mule" where a child helps on a very hot road and remembers to be gentle instead of braggy.',
        f"Tell a warm story where {child.id} tries to cool a mule hauling {cargo.label} and learns that careful help is better than noisy help.",
        'Write a child-facing story with a clear moral about kindness and humility.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    driver = f["driver"]
    mule = f["mule"]
    cargo = f["cargo_cfg"]
    repair = f["repair_cfg"]
    driver_word = driver.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {mule.id} the mule, and the {driver_word} guiding the load. They are all trying to get the wagon down the road on a hot day."
        ),
        (
            "Why did the child bring the huge fan?",
            f"{child.id} wanted to cool the mule and also wanted to look impressive. The story turns when that kind wish gets mixed up with showing off."
        ),
        (
            f"What made the day hard for {mule.id}?",
            f"The sun was hot and the load of {cargo.label} was heavy. Pulling in that heat made the mule need gentle help, not a sudden blast."
        ),
    ]
    if f["trouble"]:
        trouble_bits = []
        if f["mule_startled"]:
            trouble_bits.append(f"the gust startled {mule.id}")
        if f["cargo_spilled"]:
            trouble_bits.append(f"the {cargo.label} spilled")
        joined = " and ".join(trouble_bits)
        qa.append((
            "What went wrong when the fan started?",
            f"When the fan began to roar, {joined}. The help went wrong because the child used big windy force instead of slow careful help."
        ))
        if f["outcome"] == "reconciled":
            qa.append((
                "How did the child make things right?",
                f"{child.id} apologized and then {repair.qa_text}. That mattered because the apology came with real work, which helped trust come back."
            ))
            qa.append((
                "What is the moral of the story?",
                f"The moral is that kindness is better than showing off. When you make a mistake, you should say sorry and help repair the harm."
            ))
        else:
            qa.append((
                "Why did the ending still feel unhappy?",
                f"The child said sorry, but the fix was not enough to calm the mule or undo the mess. The story shows that words alone are smaller than the work needed to mend a mistake."
            ))
    else:
        qa.append((
            "Did the fan help this time?",
            f"Yes. The fan cooled the mule without causing a fuss, because the child stayed gentle and did not let pride grow too loud."
        ))
        qa.append((
            "What is the moral of the story?",
            f"The story says that even in a tall tale, the best help is humble help. A big tool should be guided by a kind and careful heart."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"fan", "mule", "repair", "apology"}
    tags |= set(world.place.tags)
    tags |= set(world.facts["cargo_cfg"].tags)
    if world.facts["repair_cfg"].id == "water_and_gather":
        tags.add("water")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or isinstance(v, bool)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    place: str
    cargo: str
    fan: str
    repair: str
    child_name: str
    child_gender: str
    driver: str
    trait: str
    mule_name: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="orchard",
        cargo="apples",
        fan="windmill_fan",
        repair="water_and_gather",
        child_name="Lula",
        child_gender="girl",
        driver="father",
        trait="eager",
        mule_name="Juniper",
        seed=None,
    ),
    StoryParams(
        place="mesa",
        cargo="hay",
        fan="windmill_fan",
        repair="retie_and_pat",
        child_name="Jeb",
        child_gender="boy",
        driver="mother",
        trait="boastful",
        mule_name="Dusty",
        seed=None,
    ),
    StoryParams(
        place="mesa",
        cargo="stones",
        fan="windmill_fan",
        repair="retie_and_pat",
        child_name="Mira",
        child_gender="girl",
        driver="father",
        trait="helpful",
        mule_name="Mossback",
        seed=None,
    ),
    StoryParams(
        place="river",
        cargo="beans",
        fan="windmill_fan",
        repair="song",
        child_name="Eli",
        child_gender="boy",
        driver="mother",
        trait="spirited",
        mule_name="Whistle",
        seed=None,
    ),
]


ASP_RULES = r"""
% valid setup: the place affords the cargo, the load genuinely needs cooling,
% and the chosen fan is strong enough to create the blunder this world is about.
needs_cooling(P,C) :- place(P), cargo(C), heavy(C), heat(P,PH), heat_need(C,CH), PH >= CH.
trouble(F,C) :- fan(F), cargo(C), power(F,PF), PF >= 3.
trouble(F,C) :- fan(F), cargo(C), power(F,PF), PF >= 2, blowable(C).
valid(P,C,F) :- affords(P,C), needs_cooling(P,C), trouble(F,C).

repair_works(R,C) :- repair(R), sense(R,S), sense_min(M), S >= M,
                     calms(R,1), not blowable(C).
repair_works(R,C) :- repair(R), sense(R,S), sense_min(M), S >= M,
                     calms(R,1), restores(R,1), blowable(C).

outcome(smooth) :- chosen_cargo(C), chosen_fan(F), not trouble(F,C).
outcome(reconciled) :- chosen_cargo(C), chosen_fan(F), trouble(F,C), chosen_repair(R), repair_works(R,C).
outcome(soured) :- chosen_cargo(C), chosen_fan(F), trouble(F,C), chosen_repair(R), not repair_works(R,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("heat", pid, place.heat))
        for cargo_id in sorted(place.affords):
            lines.append(asp.fact("affords", pid, cargo_id))
    for cid, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("heat_need", cid, cargo.heat_need))
        if cargo.heavy:
            lines.append(asp.fact("heavy", cid))
        if cargo.blowable:
            lines.append(asp.fact("blowable", cid))
    for fid, fan in FANS.items():
        lines.append(asp.fact("fan", fid))
        lines.append(asp.fact("power", fid, fan.power))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("calms", rid, repair.calms_mule))
        lines.append(asp.fact("restores", rid, repair.restores_cargo))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_cargo", params.cargo),
        asp.fact("chosen_fan", params.fan),
        asp.fact("chosen_repair", params.repair),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    pset = set(valid_combos())
    aset = set(asp_valid_combos())
    if pset == aset:
        print(f"OK: gate matches valid_combos() ({len(pset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if aset - pset:
            print("  only in clingo:", sorted(aset - pset))
        if pset - aset:
            print("  only in python:", sorted(pset - aset))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        emit(sample, trace=False, qa=False, header="### verify smoke test")
        print("OK: normal generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"VERIFY SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a huge fan, a hardworking mule, and a lesson about making things right."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--fan", choices=FANS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--driver", choices=DRIVERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--mule-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, cargo, fan) combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cargo:
        place = PLACES[args.place]
        cargo = CARGOES[args.cargo]
        if args.cargo not in place.affords or not needs_cooling(place, cargo):
            raise StoryError(explain_rejection(place, cargo))
    if args.repair:
        if args.repair not in REPAIRS:
            raise StoryError("(Unknown repair.)")
        if REPAIRS[args.repair].sense < SENSE_MIN:
            raise StoryError(explain_repair(args.repair))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.fan is None or combo[2] == args.fan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cargo_id, fan_id = rng.choice(sorted(combos))
    repair_choices = [
        rid for rid, repair in REPAIRS.items()
        if repair.sense >= SENSE_MIN
    ]
    repair_id = args.repair or rng.choice(sorted(repair_choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mule_name = args.mule_name or rng.choice(MULE_NAMES)
    driver = args.driver or rng.choice(DRIVERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        cargo=cargo_id,
        fan=fan_id,
        repair=repair_id,
        child_name=child_name,
        child_gender=gender,
        driver=driver,
        trait=trait,
        mule_name=mule_name,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    missing = [name for name, registry in (
        ("place", PLACES),
        ("cargo", CARGOES),
        ("fan", FANS),
        ("repair", REPAIRS),
    ) if getattr(params, name) not in registry]
    if missing:
        raise StoryError(f"(Unknown parameter value for {', '.join(missing)}.)")

    place = PLACES[params.place]
    cargo = CARGOES[params.cargo]
    fan = FANS[params.fan]
    repair = REPAIRS[params.repair]

    if (params.place, params.cargo, params.fan) not in set(valid_combos()):
        raise StoryError(explain_rejection(place, cargo))
    if repair.sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))

    world = tell(
        place=place,
        cargo_cfg=cargo,
        fan_cfg=fan,
        repair_cfg=repair,
        child_name=params.child_name,
        child_type=params.child_gender,
        driver_type=params.driver,
        child_trait=params.trait,
        mule_name=params.mule_name,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cargo, fan) combos:\n")
        for place, cargo, fan in combos:
            print(f"  {place:8} {cargo:8} {fan}")
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
            header = f"### {p.child_name}, {p.mule_name}, {p.cargo} on {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
