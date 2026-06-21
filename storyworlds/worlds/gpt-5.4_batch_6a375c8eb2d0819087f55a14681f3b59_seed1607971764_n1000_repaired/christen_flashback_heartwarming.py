#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/christen_flashback_heartwarming.py
=============================================================

A small heartwarming storyworld about a child who wants to christen a homemade
little boat. The child first learns that a name belongs on something ready to
sail, remembers that lesson in a brief flashback, and then helps mend the boat
before giving it its name and setting it afloat.

Run it
------
    python storyworlds/worlds/gpt-5.4/christen_flashback_heartwarming.py
    python storyworlds/worlds/gpt-5.4/christen_flashback_heartwarming.py --craft sailboat --material cardboard
    python storyworlds/worlds/gpt-5.4/christen_flashback_heartwarming.py --place creek
    python storyworlds/worlds/gpt-5.4/christen_flashback_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/christen_flashback_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/christen_flashback_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4/christen_flashback_heartwarming.py --asp
    python storyworlds/worlds/gpt-5.4/christen_flashback_heartwarming.py --verify
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
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }
        return mapping.get(self.type, self.type)
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
class Craft:
    id: str
    label: str
    phrase: str
    launch_line: str
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
class Material:
    id: str
    label: str
    float_score: int
    soak_risk: int
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
class Leak:
    id: str
    label: str
    where: str
    kind: str
    severity: int
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
    phrase: str
    works_for: set[str] = field(default_factory=set)
    max_soak_risk: int = 0
    qa_text: str = ""
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
class Place:
    id: str
    label: str
    water: str
    calmness: int
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


def _r_boat_ready(world: World) -> list[str]:
    boat = world.get("boat")
    sig = ("ready",)
    if sig in world.fired:
        return []
    if boat.meters["sealed"] >= THRESHOLD and boat.meters["leaking"] < THRESHOLD:
        world.fired.add(sig)
        boat.meters["ready"] += 1
        boat.memes["confidence"] += 1
        return ["__ready__"]
    return []


def _r_float(world: World) -> list[str]:
    boat = world.get("boat")
    sig = ("float",)
    if sig in world.fired:
        return []
    if boat.meters["launched"] >= THRESHOLD and boat.meters["ready"] >= THRESHOLD:
        world.fired.add(sig)
        boat.meters["floating"] += 1
        child = world.get("child")
        helper = world.get("helper")
        child.memes["joy"] += 1
        helper.memes["pride"] += 1
        return ["__float__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="boat_ready", tag="physical", apply=_r_boat_ready),
    Rule(name="float", tag="physical", apply=_r_float),
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


CRAFTS = {
    "sailboat": Craft(
        id="sailboat",
        label="sailboat",
        phrase="a little sailboat with a white paper sail",
        launch_line="set the little sailboat on the water and watched the sail lean into the breeze",
        tags={"boat", "sailboat"},
    ),
    "tugboat": Craft(
        id="tugboat",
        label="tugboat",
        phrase="a stout little tugboat with a round red chimney",
        launch_line="set the little tugboat on the water and watched it bob with a brave, steady nose",
        tags={"boat", "tugboat"},
    ),
    "skiff": Craft(
        id="skiff",
        label="skiff",
        phrase="a slim little skiff with a neat blue stripe",
        launch_line="set the little skiff on the water and watched it glide in a quiet straight line",
        tags={"boat", "skiff"},
    ),
}

MATERIALS = {
    "cork": Material(
        id="cork",
        label="cork",
        float_score=3,
        soak_risk=0,
        tags={"cork", "boat"},
    ),
    "wood": Material(
        id="wood",
        label="wood",
        float_score=2,
        soak_risk=1,
        tags={"wood", "boat"},
    ),
    "cardboard": Material(
        id="cardboard",
        label="cardboard",
        float_score=1,
        soak_risk=2,
        tags={"cardboard", "boat"},
    ),
}

LEAKS = {
    "seam": Leak(
        id="seam",
        label="a split seam",
        where="along one side seam",
        kind="seam",
        severity=1,
        tags={"leak", "repair"},
    ),
    "pinhole": Leak(
        id="pinhole",
        label="a pinhole",
        where="near the bottom",
        kind="pinhole",
        severity=1,
        tags={"leak", "repair"},
    ),
    "corner": Leak(
        id="corner",
        label="a soft corner",
        where="at one front corner",
        kind="corner",
        severity=2,
        tags={"leak", "repair"},
    ),
}

FIXES = {
    "wax": Fix(
        id="wax",
        label="beeswax",
        phrase="rubbed warm beeswax into the crack with a careful thumb",
        works_for={"seam", "pinhole"},
        max_soak_risk=1,
        qa_text="rubbed beeswax into the little crack to seal it",
        tags={"wax", "repair"},
    ),
    "glue": Fix(
        id="glue",
        label="wood glue",
        phrase="pressed a thin line of glue into the weak spot and held it still until it gripped",
        works_for={"seam", "corner"},
        max_soak_risk=1,
        qa_text="pressed glue into the weak place and let it hold",
        tags={"glue", "repair"},
    ),
    "tape": Fix(
        id="tape",
        label="clear tape",
        phrase="smoothed a strip of clear tape over the damp place until it lay flat and tight",
        works_for={"seam", "pinhole", "corner"},
        max_soak_risk=2,
        qa_text="smoothed clear tape over the weak place to keep water out",
        tags={"tape", "repair"},
    ),
}

PLACES = {
    "basin": Place(
        id="basin",
        label="the sunny washbasin on the back step",
        water="basin",
        calmness=3,
        tags={"water", "basin"},
    ),
    "pond": Place(
        id="pond",
        label="the duck pond by the willow tree",
        water="pond",
        calmness=2,
        tags={"water", "pond"},
    ),
    "creek": Place(
        id="creek",
        label="the little creek behind the garden",
        water="creek",
        calmness=1,
        tags={"water", "creek"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Ruby", "June", "Ivy", "Lucy"]
BOY_NAMES = ["Owen", "Eli", "Theo", "Noah", "Ben", "Finn", "Milo", "Jack"]
HELPERS = ["grandmother", "grandfather", "mother", "father"]
BOAT_NAMES = ["Morning Star", "Willow Wish", "Blue Dot", "Tiny Lantern", "Puddle Bird", "Kind Wind"]
TRAITS = ["careful", "eager", "bright", "patient", "hopeful", "gentle"]


def fix_works(material: Material, leak: Leak, fix: Fix) -> bool:
    return leak.kind in fix.works_for and material.soak_risk <= fix.max_soak_risk


def place_suits(material: Material, place: Place) -> bool:
    return material.float_score >= (4 - place.calmness)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for craft_id in CRAFTS:
        for material_id, material in MATERIALS.items():
            for leak_id, leak in LEAKS.items():
                for fix_id, fix in FIXES.items():
                    if not fix_works(material, leak, fix):
                        continue
                    for place_id, place in PLACES.items():
                        if place_suits(material, place):
                            combos.append((craft_id, material_id, leak_id, fix_id, place_id))
    return combos


@dataclass
class StoryParams:
    craft: str
    material: str
    leak: str
    fix: str
    place: str
    child_name: str
    child_gender: str
    helper_type: str
    child_trait: str
    boat_name: str
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


def explain_fix_rejection(material: Material, leak: Leak, fix: Fix) -> str:
    if leak.kind not in fix.works_for:
        kinds = ", ".join(sorted(fix.works_for))
        return (
            f"(No story: {fix.label} is not a good repair for {leak.label}. "
            f"It works for {kinds}, so the boat would not honestly be ready to christen.)"
        )
    return (
        f"(No story: {fix.label} is too weak for a {material.label} boat in this world. "
        f"The repair would not hold well enough to make the christening believable.)"
    )


def explain_place_rejection(material: Material, place: Place) -> str:
    return (
        f"(No story: a {material.label} boat is too delicate for {place.label}. "
        f"This world only tells stories where the mended boat can truly sail there.)"
    )


def predict_launch(world: World) -> dict:
    sim = world.copy()
    boat = sim.get("boat")
    boat.meters["launched"] += 1
    propagate(sim, narrate=False)
    return {
        "ready": boat.meters["ready"] >= THRESHOLD,
        "floating": boat.meters["floating"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper: Entity, craft: Craft, material: Material) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} had spent the morning with {helper.label_word} making {craft.phrase} from {material.label}. "
        f"By lunchtime, it sat on a folded towel, looking as if it wanted a story of its own."
    )


def bring_to_water(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"They carried it to {place.label}, where the water lay still enough to hold a sky."
    )
    world.say(
        f'{child.id} hugged the boat close and whispered, "I want to christen it today."'
    )


def spot_problem(world: World, child: Entity, boat: Entity, leak: Leak) -> None:
    child.memes["worry"] += 1
    boat.meters["leaking"] = float(leak.severity)
    world.say(
        f"But when {child.id} tipped the boat toward the light, {child.pronoun()} saw {leak.label} {leak.where}. "
        f"A bead of water from the basin test still shone there."
    )
    world.say(
        f"The little boat was lovely, but not ready yet, and that made {child.id}'s smile go small."
    )


def flashback(world: World, child: Entity, helper: Entity) -> None:
    child.memes["memory"] += 1
    ribbon = child.attrs.get("ribbon", "blue ribbon")
    world.say(
        f"{child.id} touched the {ribbon} tied around the bow, and a memory came back warm and clear."
    )
    world.say(
        f"That morning, while their hands were dusty with shavings and paper, {helper.label_word} had smiled and said, "
        f'"We can christen a boat after we make it ready. A good name should begin with care."'
    )


def choose_repair(world: World, child: Entity, helper: Entity, fix: Fix) -> None:
    child.memes["resolve"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"Remembering that, {child.id} took a breath instead of hurrying. "
        f'{helper.label_word.capitalize()} knelt beside {child.pronoun("object")} and said, "Then let us make it ready together."'
    )
    world.say(
        f"Very gently, they {fix.phrase}."
    )


def seal_boat(world: World, child: Entity, boat: Entity) -> None:
    boat.meters["sealed"] += 1
    boat.meters["leaking"] = 0.0
    propagate(world, narrate=False)
    if boat.meters["ready"] >= THRESHOLD:
        child.memes["relief"] += 1
        world.say(
            f"When they were done, no damp shine showed through. The hull felt snug and sure in {child.id}'s hands."
        )


def christen_boat(world: World, child: Entity, helper: Entity, boat: Entity, boat_name: str) -> None:
    child.memes["pride"] += 1
    boat.attrs["name"] = boat_name
    boat.meters["named"] += 1
    world.say(
        f'{helper.label_word.capitalize()} dipped two fingers into the water and let {child.id} tap a bright drop onto the bow. '
        f'"I christen you {boat_name}," {child.id} said.'
    )
    world.say(
        f"The words sounded small in the open air, but to {child.id}, they made the boat feel brave and real."
    )


def launch(world: World, child: Entity, helper: Entity, boat: Entity, craft: Craft, place: Place) -> None:
    boat.meters["launched"] += 1
    pred = predict_launch(world)
    world.facts["predicted_launch"] = pred
    propagate(world, narrate=False)
    if boat.meters["floating"] >= THRESHOLD:
        world.say(
            f"Then they {craft.launch_line} on {place.label}."
        )
        world.say(
            f"It floated without a wobble. {child.id} laughed, and {helper.label_word} laughed too, because the name had found the right boat at last."
        )


def close_story(world: World, child: Entity, helper: Entity, boat: Entity) -> None:
    child.memes["love"] += 1
    helper.memes["love"] += 1
    name = boat.attrs.get("name", "the little boat")
    world.say(
        f"For a long moment, they only watched {name} shine on the water. "
        f"After that, whenever {child.id} spoke the name, {child.pronoun()} remembered that good things can begin slowly and still begin beautifully."
    )


def tell(
    craft: Craft,
    material: Material,
    leak: Leak,
    fix: Fix,
    place: Place,
    child_name: str = "Lina",
    child_gender: str = "girl",
    helper_type: str = "grandfather",
    child_trait: str = "hopeful",
    boat_name: str = "Willow Wish",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[child_trait],
        attrs={"ribbon": "blue ribbon"},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        attrs={},
    ))
    boat = world.add(Entity(
        id="boat",
        kind="thing",
        type="boat",
        label=craft.label,
        attrs={"material": material.id, "name": ""},
    ))

    world.facts.update(
        craft=craft,
        material=material,
        leak_cfg=leak,
        fix_cfg=fix,
        place=place,
        child=child,
        helper=helper,
        boat=boat,
        boat_name=boat_name,
        flashback_used=False,
    )

    introduce(world, child, helper, craft, material)
    bring_to_water(world, child, helper, place)

    world.para()
    spot_problem(world, child, boat, leak)
    flashback(world, child, helper)
    world.facts["flashback_used"] = True

    world.para()
    choose_repair(world, child, helper, fix)
    seal_boat(world, child, boat)
    christen_boat(world, child, helper, boat, boat_name)
    launch(world, child, helper, boat, craft, place)

    world.para()
    close_story(world, child, helper, boat)

    world.facts.update(
        ready=boat.meters["ready"] >= THRESHOLD,
        floating=boat.meters["floating"] >= THRESHOLD,
        named=boat.meters["named"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "boat": [
        (
            "What does it mean to christen a boat?",
            "To christen a boat means to give it its name in a special little moment before it begins its trips. People do it to welcome the boat and mark a fresh start."
        )
    ],
    "repair": [
        (
            "Why should you fix a leak before using a little boat?",
            "A leak lets water sneak inside, which can make the boat heavy and tippy. Fixing it first helps the boat float the way it should."
        )
    ],
    "pond": [
        (
            "Why is calm water good for a tiny toy boat?",
            "Calm water does not push or spin the boat too hard. That makes it easier for a small boat to float safely."
        )
    ],
    "creek": [
        (
            "Why can a creek be harder for a toy boat than a pond?",
            "A creek keeps moving, so the water can tug a light boat away quickly. That is harder for a delicate little boat to handle."
        )
    ],
    "cardboard": [
        (
            "Why does cardboard need extra care near water?",
            "Cardboard gets soft when it stays wet. If it soaks through, it can bend and stop holding its shape."
        )
    ],
    "wood": [
        (
            "Why can wood make a good little boat?",
            "Wood is firm and can float well when it is shaped carefully. If you seal weak spots, it can stay strong on the water."
        )
    ],
    "cork": [
        (
            "Why does cork float so easily?",
            "Cork is light and full of tiny air spaces. Those little spaces help it stay up on the water."
        )
    ],
    "wax": [
        (
            "What can wax do in a small repair?",
            "Warm wax can press into a tiny crack and help block water. It works best on small weak spots."
        )
    ],
    "glue": [
        (
            "What does glue do when you repair something?",
            "Glue helps two weak edges hold together again. You have to give it a quiet moment so it can grip."
        )
    ],
    "tape": [
        (
            "How can clear tape help a small boat?",
            "Clear tape can cover a weak place and help keep water out for a while. It is handy for light repairs on simple craft projects."
        )
    ],
}
KNOWLEDGE_ORDER = ["boat", "repair", "pond", "creek", "cardboard", "wood", "cork", "wax", "glue", "tape"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    craft = f["craft"]
    material = f["material"]
    place = f["place"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that uses the word "christen" and includes a gentle flashback.',
        f"Tell a warm story where {child.id} wants to christen {craft.phrase}, but first notices a weak spot and remembers something {helper.label_word} said earlier that day.",
        f"Write a simple story about a child and {helper.label_word} mending a {material.label} {craft.label} before setting it on {place.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    craft = f["craft"]
    material = f["material"]
    leak = f["leak_cfg"]
    fix = f["fix_cfg"]
    place = f["place"]
    boat_name = f["boat_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper.label_word}, who made a little {material.label} {craft.label} together. They carried it to {place.label} for a special naming moment."
        ),
        (
            f"Why did {child.id} not christen the boat right away?",
            f"{child.id} saw {leak.label} {leak.where}, so the boat was not ready for water yet. The problem mattered because a christening was meant to begin a real launch, not cover up a leak."
        ),
        (
            "What was the flashback about?",
            f"{child.id} remembered {helper.label_word} saying that a good name should begin with care. That memory helped {child.pronoun()} slow down and choose to mend the boat first."
        ),
        (
            f"How did they make the boat ready?",
            f"They {fix.qa_text}. After that, the damp shine was gone and the hull felt snug in {child.id}'s hands."
        ),
        (
            f"What happened when {child.id} said, 'I christen you {boat_name}'?",
            f"After the repair, the naming felt true because the boat was finally ready to sail. Then they set it on the water, and it floated the way {child.id} had hoped."
        ),
        (
            "How did the story end?",
            f"It ended with the little boat floating calmly while {child.id} and {helper.label_word} watched together. The ending shows that patience turned a worried moment into a beautiful beginning."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"boat", "repair"}
    place = f["place"]
    material = f["material"]
    fix = f["fix_cfg"]
    if place.id == "pond" or place.id == "basin":
        tags.add("pond")
    if place.id == "creek":
        tags.add("creek")
    tags |= material.tags
    tags |= fix.tags
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        craft="sailboat",
        material="wood",
        leak="seam",
        fix="wax",
        place="pond",
        child_name="Lina",
        child_gender="girl",
        helper_type="grandfather",
        child_trait="hopeful",
        boat_name="Willow Wish",
    ),
    StoryParams(
        craft="tugboat",
        material="cardboard",
        leak="corner",
        fix="tape",
        place="basin",
        child_name="Owen",
        child_gender="boy",
        helper_type="grandmother",
        child_trait="eager",
        boat_name="Tiny Lantern",
    ),
    StoryParams(
        craft="skiff",
        material="cork",
        leak="pinhole",
        fix="wax",
        place="creek",
        child_name="Ruby",
        child_gender="girl",
        helper_type="mother",
        child_trait="careful",
        boat_name="Kind Wind",
    ),
    StoryParams(
        craft="sailboat",
        material="wood",
        leak="corner",
        fix="glue",
        place="pond",
        child_name="Theo",
        child_gender="boy",
        helper_type="father",
        child_trait="bright",
        boat_name="Morning Star",
    ),
]


ASP_RULES = r"""
works(M, L, F) :- material(M), leak(L), fix(F), works_for(F, K), leak_kind(L, K),
                  soak_risk(M, SR), max_soak(F, MX), SR <= MX.
suits(M, P) :- material(M), place(P), float_score(M, FS), calmness(P, C), FS >= 4 - C.
valid(Cr, M, L, F, P) :- craft(Cr), works(M, L, F), suits(M, P).

chosen_ready :- chosen_material(M), chosen_leak(L), chosen_fix(F), chosen_place(P),
                works(M, L, F), suits(M, P).
outcome(floating) :- chosen_ready.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for craft_id in CRAFTS:
        lines.append(asp.fact("craft", craft_id))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        lines.append(asp.fact("float_score", material_id, material.float_score))
        lines.append(asp.fact("soak_risk", material_id, material.soak_risk))
    for leak_id, leak in LEAKS.items():
        lines.append(asp.fact("leak", leak_id))
        lines.append(asp.fact("leak_kind", leak_id, leak.kind))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("max_soak", fix_id, fix.max_soak_risk))
        for kind in sorted(fix.works_for):
            lines.append(asp.fact("works_for", fix_id, kind))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("calmness", place_id, place.calmness))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_material", params.material),
        asp.fact("chosen_leak", params.leak),
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_place", params.place),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    material = MATERIALS[params.material]
    leak = LEAKS[params.leak]
    fix = FIXES[params.fix]
    place = PLACES[params.place]
    if fix_works(material, leak, fix) and place_suits(material, place):
        return "floating"
    return "?"


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
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcome differences.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child wants to christen a little boat, remembers a gentle lesson, and helps make it ready."
    )
    ap.add_argument("--craft", choices=sorted(CRAFTS))
    ap.add_argument("--material", choices=sorted(MATERIALS))
    ap.add_argument("--leak", choices=sorted(LEAKS))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    if gender == "girl":
        return rng.choice(GIRL_NAMES), "girl"
    return rng.choice(BOY_NAMES), "boy"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.material and args.leak and args.fix:
        material = MATERIALS[args.material]
        leak = LEAKS[args.leak]
        fix = FIXES[args.fix]
        if not fix_works(material, leak, fix):
            raise StoryError(explain_fix_rejection(material, leak, fix))

    if args.material and args.place:
        material = MATERIALS[args.material]
        place = PLACES[args.place]
        if not place_suits(material, place):
            raise StoryError(explain_place_rejection(material, place))

    combos = [
        combo for combo in valid_combos()
        if (args.craft is None or combo[0] == args.craft)
        and (args.material is None or combo[1] == args.material)
        and (args.leak is None or combo[2] == args.leak)
        and (args.fix is None or combo[3] == args.fix)
        and (args.place is None or combo[4] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    craft_id, material_id, leak_id, fix_id, place_id = rng.choice(sorted(combos))
    child_name, child_gender = _pick_child(rng)
    helper_type = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    boat_name = args.name or rng.choice(BOAT_NAMES)
    return StoryParams(
        craft=craft_id,
        material=material_id,
        leak=leak_id,
        fix=fix_id,
        place=place_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        child_trait=trait,
        boat_name=boat_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.craft not in CRAFTS:
        raise StoryError(f"(Unknown craft: {params.craft})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.leak not in LEAKS:
        raise StoryError(f"(Unknown leak: {params.leak})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.helper_type not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper_type})")

    craft = CRAFTS[params.craft]
    material = MATERIALS[params.material]
    leak = LEAKS[params.leak]
    fix = FIXES[params.fix]
    place = PLACES[params.place]

    if not fix_works(material, leak, fix):
        raise StoryError(explain_fix_rejection(material, leak, fix))
    if not place_suits(material, place):
        raise StoryError(explain_place_rejection(material, place))

    world = tell(
        craft=craft,
        material=material,
        leak=leak,
        fix=fix,
        place=place,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        child_trait=params.child_trait,
        boat_name=params.boat_name,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (craft, material, leak, fix, place) combos:\n")
        for craft, material, leak, fix, place in combos:
            print(f"  {craft:8} {material:9} {leak:8} {fix:5} {place}")
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
            header = f"### {p.child_name}: {p.craft} of {p.material} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
