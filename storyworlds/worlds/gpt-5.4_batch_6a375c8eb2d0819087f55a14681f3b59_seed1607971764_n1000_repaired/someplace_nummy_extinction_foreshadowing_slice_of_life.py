#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/someplace_nummy_extinction_foreshadowing_slice_of_life.py
====================================================================================

A standalone storyworld for a small slice-of-life tale about a child in a
shared garden learning not to take every last tasty thing. The world centers on
a simple, concrete tension:

- there is only one little patch of a favorite edible plant left,
- the food looks nummy right now,
- but if every seed-bearing bit is taken, that plant may disappear from this
  tiny place next season.

The story uses light foreshadowing: before the main conflict, the child notices
signs that the plant used to be more plentiful. That early image becomes the
reason the grown-up's warning feels true later.

Run it
------
    python storyworlds/worlds/gpt-5.4/someplace_nummy_extinction_foreshadowing_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/someplace_nummy_extinction_foreshadowing_slice_of_life.py --place rooftop --crop peas
    python storyworlds/worlds/gpt-5.4/someplace_nummy_extinction_foreshadowing_slice_of_life.py --crop basil --method dry_pod
    python storyworlds/worlds/gpt-5.4/someplace_nummy_extinction_foreshadowing_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/someplace_nummy_extinction_foreshadowing_slice_of_life.py --qa --json
    python storyworlds/worlds/gpt-5.4/someplace_nummy_extinction_foreshadowing_slice_of_life.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
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
    image: str
    rest_spot: str
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
class Crop:
    id: str
    label: str
    phrase: str
    plural_label: str
    ripe_bits: str
    one_bit: str
    snack_line: str
    future_name: str
    foreshadow: str
    scarcity_image: str
    seed_form: str
    suitable_methods: set[str] = field(default_factory=set)
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
    action_text: str
    qa_text: str
    preserves_by: str
    fits: set[str] = field(default_factory=set)
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


def _r_extinction_risk(world: World) -> list[str]:
    crop = world.get("crop")
    if crop.meters["harvest_all"] < THRESHOLD:
        return []
    if crop.meters["seed_saved"] >= THRESHOLD:
        return []
    sig = ("extinction_risk", crop.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crop.meters["future_loss"] += 1
    for ent in list(world.entities.values()):
        if ent.role == "helper":
            ent.memes["worry"] += 1
        if ent.role == "child":
            ent.memes["worry"] += 1
    return []


def _r_future_safe(world: World) -> list[str]:
    crop = world.get("crop")
    if crop.meters["seed_saved"] < THRESHOLD:
        return []
    sig = ("future_safe", crop.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crop.meters["future"] += 1
    for ent in list(world.entities.values()):
        if ent.role == "child":
            ent.memes["relief"] += 1
            ent.memes["care"] += 1
        if ent.role == "helper":
            ent.memes["hope"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="extinction_risk", tag="future", apply=_r_extinction_risk),
    Rule(name="future_safe", tag="future", apply=_r_future_safe),
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
            world.say(sent)
    return produced


def compatible(place: Place, crop: Crop, method: Method) -> bool:
    return crop.id in place.affords and method.id in crop.suitable_methods and crop.id in method.fits


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for crop_id, crop in CROPS.items():
            for method_id, method in METHODS.items():
                if compatible(place, crop, method):
                    combos.append((place_id, crop_id, method_id))
    return combos


def explain_rejection(place: Place, crop: Crop, method: Method) -> str:
    if crop.id not in place.affords:
        return (
            f"(No story: {crop.plural_label} are not part of {place.label} in this world, "
            f"so there is no believable little patch to harvest there.)"
        )
    if method.id not in crop.suitable_methods:
        return (
            f"(No story: {method.label} does not fit {crop.plural_label}. "
            f"Choose a way of saving the plant that matches how {crop.plural_label} keep going.)"
        )
    return (
        f"(No story: {method.label} is not a believable way to prevent the {crop.future_name} "
        f"from disappearing from this tiny garden.)"
    )


def predict_outcome(world: World, method: Method) -> dict:
    sim = world.copy()
    crop = sim.get("crop")
    crop.meters["harvest_all"] += 1
    if method.preserves_by == "leave_some":
        crop.meters["saved_on_plant"] += 1
        crop.meters["seed_saved"] += 1
    elif method.preserves_by == "save_dry_seed":
        crop.meters["seed_saved"] += 1
        crop.meters["saved_in_packet"] += 1
    propagate(sim, narrate=False)
    return {
        "future_loss": crop.meters["future_loss"] >= THRESHOLD,
        "future": crop.meters["future"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper: Entity, crop: Crop) -> None:
    child.memes["joy"] += 1
    world.say(
        f"After breakfast, {child.id} walked with {helper.id} to {world.place.label}. "
        f"{world.place.image}"
    )
    world.say(
        f"They had come for {crop.ripe_bits}, because {crop.snack_line}."
    )


def foreshadow(world: World, child: Entity, helper: Entity, crop: Crop) -> None:
    crop_ent = world.get("crop")
    crop_ent.meters["scarce"] += 1
    helper.memes["remembering"] += 1
    world.say(
        f"At the end of one bed, {child.id} stopped. {crop.foreshadow} "
        f"{crop.scarcity_image}"
    )
    world.say(
        f'"Were there more {crop.plural_label} here before?" {child.id} asked.'
    )
    world.say(
        f'{helper.id} nodded. "There were. Now there is only this little patch left."'
    )


def tempt(world: World, child: Entity, crop: Crop) -> None:
    child.memes["hunger"] += 1
    world.say(
        f"{child.id} leaned close and spotted {crop.ripe_bits}. "
        f'"They look so nummy," {child.pronoun()} said. '
        f'"Can we pick every {crop.one_bit}?"'
    )


def warn(world: World, child: Entity, helper: Entity, crop: Crop, method: Method) -> None:
    pred = predict_outcome(world, method)
    world.facts["predicted_future_loss"] = pred["future_loss"]
    helper.memes["care"] += 1
    if pred["future_loss"]:
        world.say(
            f'{helper.id} touched the vine gently. "If we take every last {crop.one_bit}, '
            f'there may be no {crop.seed_form} left for next season. In a tiny place like this, '
            f'that can mean a kind of extinction right here in our garden."'
        )
    else:
        world.say(
            f'{helper.id} smiled a little. "We can have some today, but we must save '
            f'some way for the plant to come back next season."'
        )


def choose_method(world: World, child: Entity, helper: Entity, crop: Crop, method: Method) -> None:
    crop_ent = world.get("crop")
    crop_ent.meters["harvest_all"] += 1
    world.say(
        f'{child.id} looked again at the small patch and thought for a moment. '
        f'"Then let\'s not gobble all of it," {child.pronoun()} said.'
    )
    if method.preserves_by == "leave_some":
        crop_ent.meters["saved_on_plant"] += 1
        crop_ent.meters["seed_saved"] += 1
        world.say(
            method.action_text.format(
                child=child.id,
                helper=helper.id,
                one_bit=crop.one_bit,
                seed_form=crop.seed_form,
                rest_spot=world.place.rest_spot,
            )
        )
    elif method.preserves_by == "save_dry_seed":
        crop_ent.meters["saved_in_packet"] += 1
        crop_ent.meters["seed_saved"] += 1
        world.say(
            method.action_text.format(
                child=child.id,
                helper=helper.id,
                one_bit=crop.one_bit,
                seed_form=crop.seed_form,
                rest_spot=world.place.rest_spot,
            )
        )
    propagate(world, narrate=False)


def snack_and_end(world: World, child: Entity, helper: Entity, crop: Crop, method: Method) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    crop_ent = world.get("crop")
    if crop_ent.meters["future"] >= THRESHOLD:
        world.say(
            f"Then they picked just enough for a snack and carried them to {world.place.rest_spot}. "
            f'"This is a good someplace to sit," {helper.id} said.'
        )
        world.say(
            f"They ate slowly in the warm air. The {crop.plural_label} really were nummy, "
            f"but what made {child.id} smile most was the saved {crop.seed_form} for spring."
        )
        if method.preserves_by == "leave_some":
            world.say(
                f"When they stood up to go home, one last {crop.one_bit} was still waiting on the plant, "
                f"small and patient, like a promise."
            )
        else:
            world.say(
                f"When they stood up to go home, {child.id} tucked the little seed packet into "
                f"{child.pronoun('possessive')} pocket as carefully as treasure."
            )
    else:
        world.say(
            f"They still found someplace to sit, but the snack felt less bright. "
            f"{child.id} kept glancing back at the bare patch."
        )


def tell(
    place: Place,
    crop: Crop,
    method: Method,
    *,
    child_name: str = "Mina",
    child_type: str = "girl",
    helper_name: str = "Grandma June",
    helper_type: str = "grandmother",
) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    crop_ent = world.add(
        Entity(
            id="crop",
            kind="thing",
            type="plant",
            label=crop.label,
            attrs={"seed_form": crop.seed_form, "future_name": crop.future_name},
        )
    )
    crop_ent.meters["ripe"] = 1
    crop_ent.meters["scarce"] = 0
    crop_ent.meters["harvest_all"] = 0
    crop_ent.meters["seed_saved"] = 0
    crop_ent.meters["future"] = 0
    crop_ent.meters["future_loss"] = 0
    child.memes["joy"] = 0
    child.memes["worry"] = 0
    child.memes["relief"] = 0
    helper.memes["worry"] = 0
    helper.memes["hope"] = 0

    introduce(world, child, helper, crop)
    foreshadow(world, child, helper, crop)

    world.para()
    tempt(world, child, crop)
    warn(world, child, helper, crop, method)

    world.para()
    choose_method(world, child, helper, crop, method)
    snack_and_end(world, child, helper, crop, method)

    world.facts.update(
        child=child,
        helper=helper,
        crop_cfg=crop,
        method=method,
        place=place,
        extinction_risk=crop_ent.meters["future_loss"] >= THRESHOLD,
        future_safe=crop_ent.meters["future"] >= THRESHOLD,
        saved_on_plant=crop_ent.meters["saved_on_plant"] >= THRESHOLD,
        saved_in_packet=crop_ent.meters["saved_in_packet"] >= THRESHOLD,
    )
    return world


PLACES = {
    "rooftop": Place(
        id="rooftop",
        label="the rooftop garden",
        image="Wooden boxes sat in tidy rows, and the city hummed far below.",
        rest_spot="a shaded bench by the water barrel",
        affords={"peas", "beans", "basil"},
        tags={"garden", "city"},
    ),
    "schoolyard": Place(
        id="schoolyard",
        label="the schoolyard beds",
        image="A low fence held back the path, and paper pinwheels clicked softly in the breeze.",
        rest_spot="the steps near the little tool shed",
        affords={"peas", "sunflower"},
        tags={"garden", "school"},
    ),
    "backyard": Place(
        id="backyard",
        label="the backyard patch",
        image="The hose lay in a sleepy curve, and the dirt smelled warm and clean.",
        rest_spot="the porch step",
        affords={"beans", "basil", "sunflower"},
        tags={"garden", "home"},
    ),
}

CROPS = {
    "peas": Crop(
        id="peas",
        label="pea vine",
        phrase="a pea vine",
        plural_label="peas",
        ripe_bits="fat green pea pods",
        one_bit="pod",
        snack_line="fresh peas always tasted sweet and nummy straight from the shell",
        future_name="peas",
        foreshadow="Most of the trellis was bare string now.",
        scarcity_image="Only one vine still climbed up with any real life in it.",
        seed_form="peas to plant",
        suitable_methods={"leave_last", "dry_pod"},
        tags={"peas", "seeds", "garden_food"},
    ),
    "beans": Crop(
        id="beans",
        label="bean pole",
        phrase="a bean pole",
        plural_label="beans",
        ripe_bits="striped bean pods",
        one_bit="pod",
        snack_line="the young beans could be snapped open and munched, crisp and nummy",
        future_name="beans",
        foreshadow="Several poles stood empty except for old twine and one curled brown leaf.",
        scarcity_image="Only one green pole still held enough pods to matter.",
        seed_form="beans to plant",
        suitable_methods={"leave_last", "dry_pod"},
        tags={"beans", "seeds", "garden_food"},
    ),
    "basil": Crop(
        id="basil",
        label="basil patch",
        phrase="a basil patch",
        plural_label="basil plants",
        ripe_bits="soft basil leaves",
        one_bit="sprig",
        snack_line="basil on warm bread smelled so nummy that even the air seemed hungry",
        future_name="basil",
        foreshadow="Two corners of the bed were already empty and crumbly.",
        scarcity_image="Only one bushy plant still smelled bright and green.",
        seed_form="flower seeds",
        suitable_methods={"leave_flower"},
        tags={"basil", "seeds", "herbs"},
    ),
    "sunflower": Crop(
        id="sunflower",
        label="sunflower head",
        phrase="a sunflower head",
        plural_label="sunflowers",
        ripe_bits="plump sunflower seeds",
        one_bit="seed head",
        snack_line="roasted sunflower seeds were salty and nummy in a paper cup",
        future_name="sunflowers",
        foreshadow="Several stalks were already cut down, leaving only thick stubs in the soil.",
        scarcity_image="One tall sunflower still watched over the bed.",
        seed_form="sunflower seeds for spring",
        suitable_methods={"leave_flower", "dry_pod"},
        tags={"sunflower", "seeds", "garden_food"},
    ),
}

METHODS = {
    "leave_last": Method(
        id="leave_last",
        label="leave one on the plant",
        action_text="{helper} and {child} picked a few, then tied a bit of yarn around one last {one_bit} so nobody would take it by mistake. That one would stay for {seed_form}.",
        qa_text="They left one part of the plant to finish and make seeds for next season.",
        preserves_by="leave_some",
        fits={"peas", "beans"},
        tags={"seed_saving"},
    ),
    "dry_pod": Method(
        id="dry_pod",
        label="save a dry pod or seed head",
        action_text="{helper} found one overripe piece and opened it carefully into a little paper packet. Inside were the {seed_form} they could keep dry until planting time.",
        qa_text="They saved dry seeds in a little packet for planting later.",
        preserves_by="save_dry_seed",
        fits={"peas", "beans", "sunflower"},
        tags={"seed_packet"},
    ),
    "leave_flower": Method(
        id="leave_flower",
        label="leave flowers for seed",
        action_text="Instead of snipping every tasty bit, {helper} pointed out a few tiny flowers and asked {child} to leave them. Those blossoms would turn into {seed_form} later.",
        qa_text="They left some flowers so the plant could make seeds later.",
        preserves_by="leave_some",
        fits={"basil", "sunflower"},
        tags={"flowers", "seed_saving"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Ava", "Nora", "Ruby", "Tess"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Leo", "Finn", "Theo"]
HELPERS = [
    {"name": "Grandma June", "type": "grandmother"},
    {"name": "Grandpa Eli", "type": "grandfather"},
    {"name": "Mom", "type": "mother"},
    {"name": "Dad", "type": "father"},
    {"name": "Aunt May", "type": "aunt"},
]

KNOWLEDGE = {
    "seeds": [
        (
            "Why do gardeners save seeds?",
            "Gardeners save seeds so they can plant the same kind of plant again later. A seed is the plant's way of making a new start."
        )
    ],
    "extinction": [
        (
            "What does extinction mean?",
            "Extinction means a kind of living thing disappears and does not keep going anymore. In this story, the grown-up uses the word for the tiny garden patch, where one kind of plant could vanish from that one place."
        )
    ],
    "peas": [
        (
            "Where do new pea plants come from?",
            "New pea plants grow from peas used as seeds. If some peas are saved and planted, more vines can grow later."
        )
    ],
    "beans": [
        (
            "Can beans be planted?",
            "Yes. Dry beans can be planted to grow new bean plants. That is why gardeners sometimes save a few instead of eating every one."
        )
    ],
    "basil": [
        (
            "How does basil make more basil plants?",
            "Basil makes flowers, and the flowers can turn into seeds. If some flowers are left alone, those seeds can be planted later."
        )
    ],
    "sunflower": [
        (
            "What grows inside a sunflower head?",
            "A sunflower head can hold many seeds. Some can be eaten, and some can be planted to grow more sunflowers."
        )
    ],
    "flowers": [
        (
            "Why might someone leave flowers on a plant?",
            "Flowers are not only pretty. On many plants, flowers help make seeds for the future."
        )
    ],
    "seed_packet": [
        (
            "Why keep seeds in a paper packet?",
            "A paper packet helps keep small seeds together and dry until it is time to plant them. Then they are easier not to lose."
        )
    ],
}
KNOWLEDGE_ORDER = ["extinction", "peas", "beans", "basil", "sunflower", "flowers", "seeds", "seed_packet"]


@dataclass
class StoryParams:
    place: str
    crop: str
    method: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
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


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    crop = world.facts["crop_cfg"]
    place = world.facts["place"]
    method = world.facts["method"]
    return [
        f'Write a gentle slice-of-life story for a 3-to-5-year-old that includes the words "someplace", "nummy", and "extinction", set in {place.label}.',
        f"Tell a small family story where {child.id} wants to eat every last {crop.one_bit}, but a grown-up explains why saving some matters for next season.",
        f"Write a foreshadowing story in a garden where early signs of scarcity lead to a calm lesson about {method.label} and caring for the future.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    crop = world.facts["crop_cfg"]
    place = world.facts["place"]
    method = world.facts["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper.id} at {place.label}. They go there to gather something tasty from a small garden patch."
        ),
        (
            f"What was the early clue that something was wrong with the {crop.plural_label}?",
            f"Before the big choice, {child.id} saw that most of the patch was already empty. That foreshadowing showed there were only a few {crop.plural_label} left."
        ),
        (
            f"Why did {helper.id} not want to pick every last {crop.one_bit}?",
            f"{helper.id} worried that if they took every last {crop.one_bit}, there would be no {crop.seed_form} left for next season. In such a tiny garden, that could mean the {crop.future_name} disappear from that one place."
        ),
        (
            "How did they solve the problem?",
            f"They still took some food home, but they also chose to {method.label}. {method.qa_text}"
        ),
    ]
    if world.facts.get("future_safe"):
        qa.append(
            (
                "How did the ending show that the child had changed?",
                f"{child.id} still enjoyed the nummy snack, but now cared about next season too. The ending image of the saved {crop.seed_form} shows {child.pronoun()} was thinking beyond one afternoon."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    crop = world.facts["crop_cfg"]
    method = world.facts["method"]
    tags = set(crop.tags) | set(method.tags) | {"extinction", "seeds"}
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="rooftop",
        crop="peas",
        method="leave_last",
        child_name="Mina",
        child_type="girl",
        helper_name="Grandma June",
        helper_type="grandmother",
    ),
    StoryParams(
        place="schoolyard",
        crop="sunflower",
        method="dry_pod",
        child_name="Leo",
        child_type="boy",
        helper_name="Dad",
        helper_type="father",
    ),
    StoryParams(
        place="backyard",
        crop="basil",
        method="leave_flower",
        child_name="Ruby",
        child_type="girl",
        helper_name="Aunt May",
        helper_type="aunt",
    ),
    StoryParams(
        place="backyard",
        crop="beans",
        method="dry_pod",
        child_name="Milo",
        child_type="boy",
        helper_name="Grandpa Eli",
        helper_type="grandfather",
    ),
]


ASP_RULES = r"""
compatible(P,C,M) :- affords(P,C), crop_allows(C,M), method_fits(M,C).

future_safe(C,M)  :- compatible(_,C,M), method_kind(M,leave_some).
future_safe(C,M)  :- compatible(_,C,M), method_kind(M,save_dry_seed).

valid(P,C,M) :- compatible(P,C,M).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for crop_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, crop_id))
    for crop_id, crop in CROPS.items():
        lines.append(asp.fact("crop", crop_id))
        for method_id in sorted(crop.suitable_methods):
            lines.append(asp.fact("crop_allows", crop_id, method_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("method_kind", method_id, method.preserves_by))
        for crop_id in sorted(method.fits):
            lines.append(asp.fact("method_fits", method_id, crop_id))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _get_place_crop_method(params: StoryParams) -> tuple[Place, Crop, Method]:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.crop not in CROPS:
        raise StoryError(f"(Unknown crop: {params.crop})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    place = PLACES[params.place]
    crop = CROPS[params.crop]
    method = METHODS[params.method]
    if not compatible(place, crop, method):
        raise StoryError(explain_rejection(place, crop, method))
    return place, crop, method


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child learns to save part of a tiny garden for next season."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=[h["name"] for h in HELPERS])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (place, crop, method) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.crop and args.method:
        place = PLACES[args.place]
        crop = CROPS[args.crop]
        method = METHODS[args.method]
        if not compatible(place, crop, method):
            raise StoryError(explain_rejection(place, crop, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.crop is None or combo[1] == args.crop)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, crop_id, method_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_choice = None
    if args.helper is not None:
        helper_choice = next((h for h in HELPERS if h["name"] == args.helper), None)
        if helper_choice is None:
            raise StoryError(f"(Unknown helper: {args.helper})")
    else:
        helper_choice = rng.choice(HELPERS)

    return StoryParams(
        place=place_id,
        crop=crop_id,
        method=method_id,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_choice["name"],
        helper_type=helper_choice["type"],
    )


def generate(params: StoryParams) -> StorySample:
    place, crop, method = _get_place_crop_method(params)
    world = tell(
        place=place,
        crop=crop,
        method=method,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid combos match ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "nummy" not in sample.story or "someplace" not in sample.story or "extinction" not in sample.story:
            raise StoryError("(Smoke test failed: generated story missed required seed words or was empty.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(7))
        sample = generate(params)
        if not sample.story:
            raise StoryError("(Resolved-params smoke test produced empty story.)")
        print("OK: default resolve/generate path succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT PATH FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, crop, method) combos:\n")
        for place_id, crop_id, method_id in combos:
            print(f"  {place_id:10} {crop_id:10} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.crop} at {p.place} ({p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
