#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hose_wildebeest_clobber_misunderstanding_slice_of_life.py
=====================================================================================

A standalone story world for a small slice-of-life misunderstanding:
a child is helping outside while a parent uses a hose near a handmade
wildebeest craft. The parent says "Watch the wildebeest while I turn off
the hose," but the child hears "Wash the wildebeest" through the spray.
A quick mistaken rinse turns into a calm family problem to solve.

The domain is intentionally small and concrete:
- one child
- one parent
- one handmade wildebeest
- one hose
- one spoken misunderstanding
- one grounded repair plan

The world model tracks physical meters like wetness and damage, plus emotional
memes like pride, worry, relief, and trust. The prose follows the simulated
state rather than swapping nouns into a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/hose_wildebeest_clobber_misunderstanding_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/hose_wildebeest_clobber_misunderstanding_slice_of_life.py --material cardboard --pressure blast --repair remake_sturdier
    python storyworlds/worlds/gpt-5.4/hose_wildebeest_clobber_misunderstanding_slice_of_life.py --material salt_dough --pressure blast --repair towel_sun
    python storyworlds/worlds/gpt-5.4/hose_wildebeest_clobber_misunderstanding_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/hose_wildebeest_clobber_misunderstanding_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/hose_wildebeest_clobber_misunderstanding_slice_of_life.py --verify
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    supports: set[str] = field(default_factory=set)
    opening: str = ""
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
class Material:
    id: str
    label: str
    phrase: str
    fragility: int
    save_tag: str
    reaction: str
    after: str
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
class Pressure:
    id: str
    label: str
    force: int
    spray_text: str
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
class Repair:
    id: str
    label: str
    mode: str
    tag: str
    power: int
    need: str
    text: str
    end_image: str
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


def _r_water_damage(world: World) -> list[str]:
    out: list[str] = []
    figure = world.get("figure")
    hose = world.get("hose")
    child = world.get("child")
    if figure.meters["wet"] < THRESHOLD:
        return out
    sig = ("water_damage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fragility = int(figure.attrs["fragility"])
    force = int(hose.attrs["force"])
    severity = fragility + force
    figure.meters["damage"] += severity
    figure.meters["sag"] += max(0, severity - 2)
    child.memes["worry"] += 1
    out.append("__damage__")
    return out


def _r_parent_alarm(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    parent = world.get("parent")
    figure = world.get("figure")
    if figure.meters["damage"] < THRESHOLD:
        return out
    sig = ("parent_alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.memes["concern"] += 1
    child.memes["guilt"] += 1
    out.append("__alarm__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="water_damage", tag="physical", apply=_r_water_damage),
    Rule(name="parent_alarm", tag="social", apply=_r_parent_alarm),
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


PLACES = {
    "backyard": Place(
        id="backyard",
        label="the backyard",
        supports={"sunny_spot", "table"},
        opening="The backyard smelled like warm dirt and mint, and a little table sat beside the flower pots.",
        tags={"yard"},
    ),
    "patio": Place(
        id="patio",
        label="the patio",
        supports={"sunny_spot", "table", "breezy_rail"},
        opening="The patio stones still held a little sun, and a folding table stood near the pots.",
        tags={"yard", "patio"},
    ),
    "side_yard": Place(
        id="side_yard",
        label="the side yard",
        supports={"table"},
        opening="The side yard was narrow and shady, with a work table tucked beside the fence.",
        tags={"yard"},
    ),
}

MATERIALS = {
    "cardboard": Material(
        id="cardboard",
        label="cardboard",
        phrase="a cardboard wildebeest with painted stripes",
        fragility=2,
        save_tag="patch",
        reaction="The cardboard drank the water at once, and one horn bent sideways.",
        after="the patched cardboard wildebeest stood a little straighter than before",
        tags={"cardboard", "craft"},
    ),
    "paper_mache": Material(
        id="paper_mache",
        label="paper-mâché",
        phrase="a paper-mâché wildebeest with a proud dark mane",
        fragility=2,
        save_tag="dry",
        reaction="The paper-mâché skin turned soft and dimpled, and the mane drooped over one eye.",
        after="the paper-mâché wildebeest dried with its mane brushed neat again",
        tags={"paper_mache", "craft"},
    ),
    "salt_dough": Material(
        id="salt_dough",
        label="salt dough",
        phrase="a salt-dough wildebeest with tiny thumbprint hooves",
        fragility=3,
        save_tag="paint",
        reaction="The salt dough turned tacky, and one side began to slump like warm bread.",
        after="the new wildebeest sat on the table, thicker and stronger than the first one",
        tags={"salt_dough", "craft"},
    ),
    "air_dry_clay": Material(
        id="air_dry_clay",
        label="air-dry clay",
        phrase="an air-dry-clay wildebeest with careful little horns",
        fragility=1,
        save_tag="paint",
        reaction="The clay held its shape, but the brown paint ran down the legs in thin tears.",
        after="the clay wildebeest dried on the table with fresh paint on its legs",
        tags={"clay", "craft"},
    ),
}

PRESSURES = {
    "mist": Pressure(
        id="mist",
        label="a soft mist",
        force=1,
        spray_text="Only a soft mist came out, bright in the sun like tiny beads.",
        tags={"gentle_water"},
    ),
    "stream": Pressure(
        id="stream",
        label="a quick stream",
        force=2,
        spray_text="A quick stream jumped from the hose and hit the little craft before the child could blink twice.",
        tags={"water"},
    ),
    "blast": Pressure(
        id="blast",
        label="a hard blast",
        force=3,
        spray_text="The hose gave a hard blast that pushed the little wildebeest half a step across the table.",
        tags={"water", "hard_water"},
    ),
}

REPAIRS = {
    "towel_sun": Repair(
        id="towel_sun",
        label="a towel and a sunny step",
        mode="save",
        tag="dry",
        power=3,
        need="sunny_spot",
        text="They patted the craft gently with a soft towel and set it in a bright sunny spot to dry slowly.",
        end_image="By late afternoon it was dry enough to smile at again from the sunny step.",
        qa_text="They dried it carefully with a towel and let the sun finish the job",
        tags={"drying", "sun"},
    ),
    "patch_paint": Repair(
        id="patch_paint",
        label="cardboard patches and fresh paint",
        mode="save",
        tag="patch",
        power=4,
        need="table",
        text="They slid a scrap of stiff card behind the weak part, taped it neatly, and brushed on fresh paint where the water had scuffed the color.",
        end_image="When they were done, the little wildebeest stood by the flower pot with a steadier horn and a brave painted face.",
        qa_text="They patched the weak part with stiff card and painted it again",
        tags={"patch", "paint"},
    ),
    "touchup_paint": Repair(
        id="touchup_paint",
        label="a patient repaint",
        mode="save",
        tag="paint",
        power=3,
        need="table",
        text="They let the surface rest, then used a tiny brush to paint the blurred parts again one careful stroke at a time.",
        end_image="At the end, the little wildebeest sat on the table with fresh color on its legs and horns.",
        qa_text="They let it dry and then painted the washed-off parts again",
        tags={"paint"},
    ),
    "remake_sturdier": Repair(
        id="remake_sturdier",
        label="making a sturdier new one together",
        mode="remake",
        tag="any",
        power=99,
        need="table",
        text="They set the soggy one aside, rolled up their sleeves, and made a sturdier new wildebeest together, this time with thicker legs and a safer place to dry.",
        end_image="Before supper, the new wildebeest was waiting on the table, and the hose was coiled far away.",
        qa_text="They made a sturdier new wildebeest together",
        tags={"craft", "remake"},
    ),
}


def place_supports(place: Place, repair: Repair) -> bool:
    return repair.need in place.supports


def damage_severity(material: Material, pressure: Pressure) -> int:
    return material.fragility + pressure.force


def can_save(place: Place, material: Material, pressure: Pressure, repair: Repair) -> bool:
    if repair.mode != "save":
        return False
    if repair.tag != material.save_tag:
        return False
    if repair.power < damage_severity(material, pressure):
        return False
    if not place_supports(place, repair):
        return False
    return True


def valid_combo(place_id: str, material_id: str, pressure_id: str, repair_id: str) -> bool:
    if place_id not in PLACES or material_id not in MATERIALS or pressure_id not in PRESSURES or repair_id not in REPAIRS:
        return False
    place = PLACES[place_id]
    material = MATERIALS[material_id]
    pressure = PRESSURES[pressure_id]
    repair = REPAIRS[repair_id]
    if repair.mode == "remake":
        return place_supports(place, repair)
    return can_save(place, material, pressure, repair)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for material_id in MATERIALS:
            for pressure_id in PRESSURES:
                for repair_id in REPAIRS:
                    if valid_combo(place_id, material_id, pressure_id, repair_id):
                        combos.append((place_id, material_id, pressure_id, repair_id))
    return combos


def explain_rejection(place: Place, material: Material, pressure: Pressure, repair: Repair) -> str:
    if not place_supports(place, repair):
        return (
            f"(No story: {place.label} does not have the right spot for {repair.label}. "
            f"Try a place that supports {repair.need.replace('_', ' ')}.)"
        )
    if repair.mode == "remake":
        return "(No story: this remake should have been valid.)"
    if repair.tag != material.save_tag:
        return (
            f"(No story: {repair.label} does not really fit a {material.label} wildebeest. "
            f"That material is better handled with a repair aimed at {material.save_tag.replace('_', ' ')}.)"
        )
    need = damage_severity(material, pressure)
    return (
        f"(No story: {repair.label} is too weak for {pressure.label} on {material.label}. "
        f"The damage severity is {need}, but that repair only handles {repair.power}. "
        f"Choose a stronger save or remake the craft together.)"
    )


def predict_damage(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    figure = sim.get("figure")
    hose = sim.get("hose")
    _do_spray(sim, child, figure, hose, narrate=False)
    return {
        "damage": sim.get("figure").meters["damage"],
        "wet": sim.get("figure").meters["wet"],
    }


def setup_scene(world: World, child: Entity, parent: Entity, material: Material) -> None:
    child.memes["pride"] += 1
    child.memes["trust"] += 1
    world.say(
        f"{child.id} was spending a slow afternoon with {child.pronoun('possessive')} "
        f"{parent.label_word} in {world.place.label}. {world.place.opening}"
    )
    world.say(
        f"On the table sat {material.phrase}. {child.id} had made it that morning and kept looking over to smile at it."
    )


def garden_work(world: World, parent: Entity) -> None:
    world.say(
        f"{parent.label_word.capitalize()} was watering the pots with a green hose, turning the stream low whenever it came near the craft table."
    )
    world.say(
        f'"Careful," {parent.pronoun()} said. "A hard spray can clobber a light little craft."'
    )


def misunderstanding(world: World, child: Entity, parent: Entity) -> None:
    pred = predict_damage(world)
    world.facts["predicted_damage"] = pred["damage"]
    world.facts["misheard_from"] = "watch"
    world.facts["misheard_to"] = "wash"
    child.memes["confusion"] += 1
    world.say(
        f"After a minute, {parent.label_word} bent to turn the faucet. Over the hiss of the water, "
        f'{parent.pronoun()} called, "Watch the wildebeest while I turn off the hose!"'
    )
    world.say(
        f"But the spray made the words slippery, and {child.id} heard, "
        f'"Wash the wildebeest while I turn off the hose."'
    )


def _do_spray(world: World, child: Entity, figure: Entity, hose: Entity, narrate: bool = True) -> None:
    figure.meters["wet"] += 1
    child.memes["helpfulness"] += 1
    propagate(world, narrate=narrate)


def mistaken_help(world: World, child: Entity, pressure: Pressure) -> None:
    hose = world.get("hose")
    figure = world.get("figure")
    hose.attrs["force"] = pressure.force
    world.say(
        f"Wanting to be useful, {child.id} lifted the hose a little and gave the wildebeest {pressure.label}."
    )
    _do_spray(world, child, figure, hose, narrate=False)
    world.say(pressure.spray_text)
    reaction = world.facts["material"].reaction
    world.say(reaction)


def clarify(world: World, child: Entity, parent: Entity) -> None:
    child.memes["embarrassment"] += 1
    world.say(
        f'"Oh, honey," {parent.label_word} said, hurrying back. "I said watch the wildebeest, not wash it."'
    )
    world.say(
        f"{child.id} looked at the damp little animal and blinked. "
        f'"I thought you wanted me to help," {child.pronoun()} whispered.'
    )


def comfort(world: World, child: Entity, parent: Entity) -> None:
    child.memes["trust"] += 1
    parent.memes["calm"] += 1
    world.say(
        f"{parent.label_word.capitalize()} knelt beside {child.id} and touched {child.pronoun('possessive')} shoulder."
    )
    world.say(
        f'"You were trying to help," {parent.pronoun()} said. '
        f'"When words sound strange over the hose, we stop and ask."'
    )


def save_craft(world: World, child: Entity, parent: Entity, repair: Repair) -> None:
    figure = world.get("figure")
    figure.meters["wet"] = 0.0
    figure.meters["saved"] = 1.0
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    world.say(repair.text)
    world.say(
        f"Little by little, the problem looked smaller. {repair.end_image}"
    )
    world.say(
        f'{child.id} let out a long breath. "Next time I will ask first," {child.pronoun()} said.'
    )


def remake_craft(world: World, child: Entity, parent: Entity, repair: Repair) -> None:
    figure = world.get("figure")
    figure.meters["remade"] = 1.0
    child.memes["sadness"] += 1
    child.memes["hope"] += 1
    world.say(
        "The first wildebeest was too soggy to keep its shape, even after they patted it dry."
    )
    world.say(repair.text)
    world.say(
        f"That made {child.id} feel better. {repair.end_image}"
    )
    world.say(
        f"The old mistake did not feel so big once their hands were busy side by side."
    )


def ending_image(world: World, child: Entity, parent: Entity) -> None:
    if world.facts["outcome"] == "saved":
        world.say(
            f"Before they went inside, {child.id} moved the craft to a safer place all by {child.pronoun('object')}."
        )
        world.say(
            f"The hose stayed coiled near the pots, and the little wildebeest watched the evening quietly from up high."
        )
    else:
        world.say(
            f"Later, when the pots needed water again, {child.id} stood back and listened carefully before touching the hose."
        )
        world.say(
            f"This time {child.pronoun()} asked, and {parent.label_word} smiled before answering."
        )


def tell(
    place: Place,
    material: Material,
    pressure: Pressure,
    repair: Repair,
    child_name: str = "Mia",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            traits=[trait],
            role="child",
            attrs={},
            tags=set(),
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
            attrs={},
            tags=set(),
        )
    )
    figure = world.add(
        Entity(
            id="figure",
            kind="thing",
            type="craft",
            label="wildebeest",
            phrase=material.phrase,
            attrs={"fragility": material.fragility, "save_tag": material.save_tag},
            tags=set(material.tags),
        )
    )
    hose = world.add(
        Entity(
            id="hose",
            kind="thing",
            type="tool",
            label="hose",
            attrs={"force": pressure.force},
            tags={"hose"},
        )
    )
    world.facts.update(
        child=child,
        parent=parent,
        figure=figure,
        hose=hose,
        place=place,
        material=material,
        pressure=pressure,
        repair=repair,
        misunderstanding=True,
        predicted_damage=0,
        misheard_from="",
        misheard_to="",
        outcome="",
    )

    setup_scene(world, child, parent, material)
    garden_work(world, parent)

    world.para()
    misunderstanding(world, child, parent)
    mistaken_help(world, child, pressure)

    world.para()
    clarify(world, child, parent)
    comfort(world, child, parent)

    world.para()
    if repair.mode == "save":
        save_craft(world, child, parent, repair)
        outcome = "saved"
    else:
        remake_craft(world, child, parent, repair)
        outcome = "remade"
    world.facts["outcome"] = outcome

    world.para()
    ending_image(world, child, parent)
    return world


@dataclass
class StoryParams:
    place: str
    material: str
    pressure: str
    repair: str
    name: str
    gender: str
    parent: str
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


GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Rose", "Ella", "Anna"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Finn", "Theo", "Max", "Eli", "Noah"]
TRAITS = ["careful", "helpful", "earnest", "patient", "busy", "gentle"]

CURATED = [
    StoryParams(
        place="patio",
        material="paper_mache",
        pressure="mist",
        repair="towel_sun",
        name="Mia",
        gender="girl",
        parent="mother",
        trait="helpful",
    ),
    StoryParams(
        place="backyard",
        material="cardboard",
        pressure="stream",
        repair="patch_paint",
        name="Ben",
        gender="boy",
        parent="father",
        trait="earnest",
    ),
    StoryParams(
        place="side_yard",
        material="air_dry_clay",
        pressure="stream",
        repair="touchup_paint",
        name="Nora",
        gender="girl",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        place="backyard",
        material="salt_dough",
        pressure="blast",
        repair="remake_sturdier",
        name="Theo",
        gender="boy",
        parent="father",
        trait="patient",
    ),
]


KNOWLEDGE = {
    "hose": [
        (
            "What is a hose?",
            "A hose is a long tube that carries water from a faucet. People use it to water plants or wash outdoor things."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding is when someone hears or understands something the wrong way. It can happen when words are noisy, fast, or unclear."
        )
    ],
    "cardboard": [
        (
            "Why can cardboard get weak when it gets wet?",
            "Cardboard is made from pressed paper, so water soaks into it and makes it soft. That is why it can bend or sag."
        )
    ],
    "paper_mache": [
        (
            "What is paper-mâché?",
            "Paper-mâché is paper mixed with paste and shaped into something new. It can be strong when dry, but fresh water can make it soft again."
        )
    ],
    "salt_dough": [
        (
            "What is salt dough?",
            "Salt dough is a simple craft dough made for shaping. Water can make it sticky and soft if it is not protected."
        )
    ],
    "paint": [
        (
            "Why can paint run when it gets wet?",
            "Some paint loosens when water touches it, so the color can slide or smear. Then it often has to dry before it can be painted again."
        )
    ],
    "drying": [
        (
            "Why do some wet crafts need time to dry?",
            "Wet crafts can be soft and easy to bend. Gentle drying gives them time to firm up again."
        )
    ],
    "repair": [
        (
            "What does it mean to repair something?",
            "To repair something is to fix it so it can be used or enjoyed again. Sometimes that means drying it, patching it, or painting it."
        )
    ],
    "remake": [
        (
            "When do people remake something instead of fixing it?",
            "People remake something when the first one is too damaged to save well. Then they can use what they learned to build a stronger new one."
        )
    ],
    "wildebeest": [
        (
            "What is a wildebeest?",
            "A wildebeest is a large animal with long legs and curved horns. It lives in Africa and is sometimes called a gnu."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "hose",
    "misunderstanding",
    "wildebeest",
    "cardboard",
    "paper_mache",
    "salt_dough",
    "paint",
    "drying",
    "repair",
    "remake",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    material = world.facts["material"]
    pressure = world.facts["pressure"]
    repair = world.facts["repair"]
    outcome = world.facts["outcome"]
    ending = "save the craft" if outcome == "saved" else "make a stronger new one"
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the words "hose", "wildebeest", and "clobber".',
        f"Tell a gentle misunderstanding story where {child.id} hears watch as wash over the sound of a hose and sprays a {material.label} wildebeest by mistake.",
        f"Write a small family story where a parent stays calm, the child was only trying to help, and together they {ending} after {pressure.label} causes trouble.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    material = world.facts["material"]
    pressure = world.facts["pressure"]
    repair = world.facts["repair"]
    outcome = world.facts["outcome"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {pw}, and a handmade little wildebeest. The family is sharing an ordinary afternoon outside."
        ),
        (
            "What mistake did the child make?",
            f"{child.id} heard watch as wash because the hose was hissing so loudly. {child.pronoun().capitalize()} sprayed the wildebeest while trying to be helpful."
        ),
        (
            "Why was the wildebeest in trouble?",
            f"It was made of {material.label}, and water was hard on that material. {pressure.spray_text[0].upper()}{pressure.spray_text[1:]} so the craft started to change right away."
        ),
        (
            f"Why was {child.id}'s {pw} not angry?",
            f"{pw.capitalize()} could see that {child.id} had been trying to help, not trying to make a mess. The problem came from a misunderstanding, so {pw} slowed down and explained the words clearly."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "How did they fix the problem?",
                f"They used {repair.label} to save the little craft. {repair.qa_text.capitalize()}, and that worked because the damage was still small enough to mend."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The wildebeest was safe again in a better spot. The ending shows that asking first can protect something special."
            )
        )
    else:
        qa.append(
            (
                "What did they do when the first craft could not be saved?",
                f"They made a sturdier new wildebeest together. That turned the mistake into a quieter, kinder afternoon of working side by side."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a new wildebeest on the table and the hose put safely away. The family had learned to ask and answer more clearly next time."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    material = world.facts["material"]
    repair = world.facts["repair"]
    tags = {"hose", "misunderstanding", "wildebeest", "repair"}
    if material.id == "cardboard":
        tags.add("cardboard")
    if material.id == "paper_mache":
        tags.add("paper_mache")
    if material.id == "salt_dough":
        tags.add("salt_dough")
    if material.id == "air_dry_clay":
        tags.add("paint")
    if repair.id == "towel_sun":
        tags.add("drying")
    if repair.mode == "remake":
        tags.add("remake")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(
        f"  outcome={world.facts.get('outcome')} misheard={world.facts.get('misheard_from')}->{world.facts.get('misheard_to')}"
    )
    return "\n".join(lines)


ASP_RULES = r"""
supports_need(P,R) :- place(P), repair(R), need(R,N), supports(P,N).

severity(M,Pr,S) :- material(M), pressure(Pr), fragility(M,F), force(Pr,W), S = F + W.

save_possible(P,M,Pr,R) :- place(P), material(M), pressure(Pr), repair(R),
                           repair_mode(R,save), save_tag(M,T), repair_tag(R,T),
                           supports_need(P,R), severity(M,Pr,S), repair_power(R,RP), RP >= S.

valid(P,M,Pr,R) :- save_possible(P,M,Pr,R).
valid(P,M,Pr,R) :- place(P), material(M), pressure(Pr), repair(R),
                   repair_mode(R,remake), supports_need(P,R).

outcome(saved)  :- chosen_place(P), chosen_material(M), chosen_pressure(Pr), chosen_repair(R),
                   save_possible(P,M,Pr,R).
outcome(remade) :- chosen_repair(R), repair_mode(R,remake).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for need in sorted(place.supports):
            lines.append(asp.fact("supports", place_id, need))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        lines.append(asp.fact("fragility", material_id, material.fragility))
        lines.append(asp.fact("save_tag", material_id, material.save_tag))
    for pressure_id, pressure in PRESSURES.items():
        lines.append(asp.fact("pressure", pressure_id))
        lines.append(asp.fact("force", pressure_id, pressure.force))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("repair_mode", repair_id, repair.mode))
        lines.append(asp.fact("repair_tag", repair_id, repair.tag))
        lines.append(asp.fact("repair_power", repair_id, repair.power))
        lines.append(asp.fact("need", repair_id, repair.need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    if params.place not in PLACES or params.material not in MATERIALS or params.pressure not in PRESSURES or params.repair not in REPAIRS:
        raise StoryError("(No story: unknown parameter key.)")
    repair = REPAIRS[params.repair]
    if repair.mode == "remake":
        return "remade"
    if can_save(PLACES[params.place], MATERIALS[params.material], PRESSURES[params.pressure], repair):
        return "saved"
    raise StoryError(explain_rejection(PLACES[params.place], MATERIALS[params.material], PRESSURES[params.pressure], repair))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_material", params.material),
            asp.fact("chosen_pressure", params.pressure),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    items = asp.atoms(model, "outcome")
    return items[0][0] if items else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP valid combos match Python ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a calm family misunderstanding around a hose and a handmade wildebeest."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--pressure", choices=PRESSURES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.material and args.pressure and args.repair:
        if not valid_combo(args.place, args.material, args.pressure, args.repair):
            raise StoryError(
                explain_rejection(
                    PLACES[args.place],
                    MATERIALS[args.material],
                    PRESSURES[args.pressure],
                    REPAIRS[args.repair],
                )
            )

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.material is None or combo[1] == args.material)
        and (args.pressure is None or combo[2] == args.pressure)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, material_id, pressure_id, repair_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        material=material_id,
        pressure=pressure_id,
        repair=repair_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.material not in MATERIALS:
        raise StoryError(f"(No story: unknown material '{params.material}'.)")
    if params.pressure not in PRESSURES:
        raise StoryError(f"(No story: unknown pressure '{params.pressure}'.)")
    if params.repair not in REPAIRS:
        raise StoryError(f"(No story: unknown repair '{params.repair}'.)")
    if not valid_combo(params.place, params.material, params.pressure, params.repair):
        raise StoryError(
            explain_rejection(
                PLACES[params.place],
                MATERIALS[params.material],
                PRESSURES[params.pressure],
                REPAIRS[params.repair],
            )
        )

    world = tell(
        place=PLACES[params.place],
        material=MATERIALS[params.material],
        pressure=PRESSURES[params.pressure],
        repair=REPAIRS[params.repair],
        child_name=params.name,
        child_gender=params.gender,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (place, material, pressure, repair) combos:\n")
        for place_id, material_id, pressure_id, repair_id in combos:
            print(f"  {place_id:10} {material_id:13} {pressure_id:7} {repair_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = (
                f"### {p.name}: {p.material} wildebeest in {p.place} "
                f"({p.pressure}, {p.repair}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
