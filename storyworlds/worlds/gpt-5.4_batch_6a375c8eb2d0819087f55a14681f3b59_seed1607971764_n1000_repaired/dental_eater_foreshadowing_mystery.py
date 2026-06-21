#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dental_eater_foreshadowing_mystery.py
================================================================

A standalone story world for a tiny child-facing mystery with foreshadowing:
a child with a wiggly tooth saves a crunchy snack, wakes to find it half eaten,
and worries that a secret "midnight eater" came in the night. The clues can
lead to two grounded answers:

* the child sleepily bit the snack, the loose tooth popped free, and the child
  does not remember it clearly at first; or
* a pet reached the snack and nibbled it.

The world enforces a reasonableness gate: only combinations that create a real,
solvable mystery are allowed, and the chosen clue-finding tool must genuinely be
able to reveal the deciding clue.

Run it
------
    python storyworlds/worlds/gpt-5.4/dental_eater_foreshadowing_mystery.py
    python storyworlds/worlds/gpt-5.4/dental_eater_foreshadowing_mystery.py --all
    python storyworlds/worlds/gpt-5.4/dental_eater_foreshadowing_mystery.py --qa --seed 7
    python storyworlds/worlds/gpt-5.4/dental_eater_foreshadowing_mystery.py --asp
    python storyworlds/worlds/gpt-5.4/dental_eater_foreshadowing_mystery.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "cat"}
        male = {"boy", "father", "dad", "man", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Snack:
    id: str
    label: str
    phrase: str
    hardness: int
    crumbs: bool
    bite_shape: str
    safe_swap: str
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
    phrase: str
    near_bed: bool
    pet_reachable: bool
    clue_spot: str
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
class Tool:
    id: str
    label: str
    phrase: str
    reveals: set[str] = field(default_factory=set)
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
class PetCfg:
    id: str
    label: str
    type: str
    phrase: str
    likes_crunchy: bool
    paw_word: str
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


def _r_tooth_drop(world: World) -> list[str]:
    child = world.get("child")
    snack = world.get("snack")
    if child.meters["night_bite"] < THRESHOLD:
        return []
    if child.meters["loose_tooth"] < THRESHOLD:
        return []
    if snack.meters["hardness"] < 2:
        return []
    sig = ("tooth_drop",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["tooth_missing"] += 1
    child.meters["gum_tender"] += 1
    snack.meters["bitten"] += 1
    snack.meters["crumbs_bed"] += 1
    world.facts["clue_tooth"] = True
    world.facts["clue_pillow_crumbs"] = True
    return []


def _r_pet_crumbs(world: World) -> list[str]:
    pet_id = world.facts.get("pet_id", "none")
    if pet_id == "none":
        return []
    pet = world.get("pet")
    snack = world.get("snack")
    if pet.meters["night_nibble"] < THRESHOLD:
        return []
    sig = ("pet_crumbs",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    snack.meters["bitten"] += 1
    snack.meters["crumbs_floor"] += 1
    pet.meters["full"] += 1
    world.facts["clue_paw"] = True
    world.facts["clue_floor_crumbs"] = True
    return []


RULES = [
    Rule(name="tooth_drop", tag="physical", apply=_r_tooth_drop),
    Rule(name="pet_crumbs", tag="physical", apply=_r_pet_crumbs),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SNACKS = {
    "apple_slice": Snack(
        id="apple_slice",
        label="apple slice",
        phrase="a shiny apple slice shaped like a moon",
        hardness=2,
        crumbs=False,
        bite_shape="a neat moon-shaped bite",
        safe_swap="warm applesauce",
        tags={"apple", "teeth", "soft_food"},
    ),
    "toast_star": Snack(
        id="toast_star",
        label="toast star",
        phrase="a cinnamon toast star",
        hardness=2,
        crumbs=True,
        bite_shape="a crunchy star-point bite",
        safe_swap="soft banana slices",
        tags={"toast", "crumbs", "teeth", "soft_food"},
    ),
    "cracker_moon": Snack(
        id="cracker_moon",
        label="cracker moon",
        phrase="a little moon cracker",
        hardness=1,
        crumbs=True,
        bite_shape="a small tidy bite",
        safe_swap="yogurt",
        tags={"cracker", "crumbs", "soft_food"},
    ),
}

PLACES = {
    "pillow_tin": Place(
        id="pillow_tin",
        label="pillow tin",
        phrase="a tiny tin tucked beneath the pillow",
        near_bed=True,
        pet_reachable=False,
        clue_spot="on the sheet beside the pillow",
        tags={"bedroom", "pillow"},
    ),
    "bedside_saucer": Place(
        id="bedside_saucer",
        label="bedside saucer",
        phrase="a saucer on the little table beside the bed",
        near_bed=True,
        pet_reachable=False,
        clue_spot="on the blanket near the bed edge",
        tags={"bedroom", "table"},
    ),
    "step_stool_plate": Place(
        id="step_stool_plate",
        label="step-stool plate",
        phrase="a plate left on the step stool by the door",
        near_bed=False,
        pet_reachable=True,
        clue_spot="on the floor by the stool",
        tags={"floor", "stool"},
    ),
    "hall_rug_plate": Place(
        id="hall_rug_plate",
        label="hall rug plate",
        phrase="a plate on the hall rug near the kitchen light",
        near_bed=False,
        pet_reachable=True,
        clue_spot="across the rug",
        tags={"hall", "floor"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        reveals={"tooth", "crumbs"},
        tags={"flashlight"},
    ),
    "dental_mirror": Tool(
        id="dental_mirror",
        label="dental mirror",
        phrase="a little dental mirror from the bathroom cup",
        reveals={"tooth"},
        tags={"dental", "mirror"},
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a round magnifying glass",
        reveals={"paw", "crumbs"},
        tags={"magnifier"},
    ),
}

PETS = {
    "none": PetCfg(
        id="none",
        label="no pet",
        type="thing",
        phrase="no pet",
        likes_crunchy=False,
        paw_word="",
        tags=set(),
    ),
    "cat": PetCfg(
        id="cat",
        label="cat",
        type="cat",
        phrase="the soft gray cat",
        likes_crunchy=True,
        paw_word="tiny paw prints",
        tags={"cat", "pet"},
    ),
    "dog": PetCfg(
        id="dog",
        label="dog",
        type="dog",
        phrase="the little brown dog",
        likes_crunchy=True,
        paw_word="small paw marks",
        tags={"dog", "pet"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Zoe", "Ella", "Ruby", "Ivy"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Leo", "Finn", "Noah", "Eli"]
HELPER_GIRL_NAMES = ["June", "Maya", "Tess", "Anna", "Rose"]
HELPER_BOY_NAMES = ["Owen", "Jack", "Milo", "Cole", "Nico"]
TRAITS = ["careful", "curious", "quiet", "thoughtful", "brave"]


def self_possible(snack: Snack, place: Place) -> bool:
    return snack.hardness >= 2 and place.near_bed


def pet_possible(snack: Snack, place: Place, pet: PetCfg) -> bool:
    return pet.id != "none" and place.pet_reachable and pet.likes_crunchy and snack.crumbs


def actual_culprit(snack: Snack, place: Place, pet: PetCfg) -> str:
    if self_possible(snack, place):
        return "self"
    if pet_possible(snack, place, pet):
        return "pet"
    return "none"


def tool_solves(tool: Tool, culprit: str) -> bool:
    if culprit == "self":
        return "tooth" in tool.reveals
    if culprit == "pet":
        return "paw" in tool.reveals
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for snack_id, snack in SNACKS.items():
        for place_id, place in PLACES.items():
            for tool_id, tool in TOOLS.items():
                for pet_id, pet in PETS.items():
                    culprit = actual_culprit(snack, place, pet)
                    if culprit != "none" and tool_solves(tool, culprit):
                        combos.append((snack_id, place_id, tool_id, pet_id))
    return combos


@dataclass
class StoryParams:
    snack: str
    place: str
    tool: str
    pet: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
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


def predict_culprit(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    pet_id = sim.facts.get("pet_id", "none")
    culprit = actual_culprit(
        SNACKS[sim.facts["snack_id"]],
        PLACES[sim.facts["place_id"]],
        PETS[pet_id],
    )
    if culprit == "self":
        child.meters["night_bite"] += 1
    elif culprit == "pet" and pet_id != "none":
        sim.get("pet").meters["night_nibble"] += 1
    propagate(sim, narrate=False)
    return {
        "culprit": culprit,
        "tooth": bool(sim.facts.get("clue_tooth")),
        "paw": bool(sim.facts.get("clue_paw")),
        "crumbs_bed": bool(sim.facts.get("clue_pillow_crumbs")),
        "crumbs_floor": bool(sim.facts.get("clue_floor_crumbs")),
    }


def introduce(world: World, child: Entity, helper: Entity, parent: Entity,
              snack: Snack, place: Place, pet: PetCfg) -> None:
    world.say(
        f"On a dim, whispery evening, {child.id} set aside {snack.phrase} in "
        f"{place.phrase}. {child.pronoun('possessive').capitalize()} friend {helper.id} "
        f"said it looked like the sort of snack a mystery would choose."
    )
    if pet.id != "none":
        world.say(
            f"Nearby, {pet.phrase} watched with bright eyes, but {parent.label_word} "
            f"tapped the air and said the snack was for later, not for paws."
        )
    else:
        world.say(
            f"The room was so still that even the clock sounded secret."
        )


def foreshadow(world: World, child: Entity, parent: Entity, snack: Snack) -> None:
    child.meters["loose_tooth"] = 1.0
    child.meters["gum_tender"] = 1.0
    child.memes["uneasy"] += 1
    world.say(
        f"{child.id} kept touching one wiggly tooth with {child.pronoun('possessive')} tongue. "
        f'"That tooth is very loose," {parent.label_word} said. '
        f'"Tomorrow at the dental office, they may say soft foods are best."'
    )
    if snack.hardness >= 2:
        world.say(
            f"But {child.id} loved the look of the crunchy treat and whispered that "
            f"{child.pronoun()} would save it for the morning."
        )
    else:
        world.say(
            f"The snack was not very hard, but it still felt special enough to save."
        )


def night_event(world: World, snack: Snack, place: Place, pet: PetCfg) -> None:
    culprit = actual_culprit(snack, place, pet)
    if culprit == "self":
        world.get("child").meters["night_bite"] += 1
    elif culprit == "pet" and pet.id != "none":
        world.get("pet").meters["night_nibble"] += 1
    propagate(world, narrate=False)
    world.facts["culprit"] = culprit


def morning_discovery(world: World, child: Entity, helper: Entity, snack: Snack) -> None:
    child.memes["mystery"] += 1
    child.memes["fear"] += 1
    world.say(
        f"In the morning, {child.id} hurried back and froze. Half of the {snack.label} was gone."
    )
    world.say(
        f'"A midnight eater!" {child.id} gasped. "{helper.id}, something took a bite while I was asleep."'
    )


def inspect(world: World, child: Entity, helper: Entity, tool: Tool, place: Place) -> None:
    pred = predict_culprit(world)
    world.facts["predicted"] = pred
    world.say(
        f"{helper.id} fetched {tool.phrase}, and the two detectives bent close to look "
        f"{place.clue_spot}."
    )
    if pred["culprit"] == "self":
        if "tooth" in tool.reveals:
            world.say(
                f"The light caught a tiny white tooth tucked in the crease by the pillow, "
                f"and there were faint crumbs nearby."
            )
            world.facts["revealed"] = "tooth"
        else:
            world.facts["revealed"] = "none"
    elif pred["culprit"] == "pet":
        if "paw" in tool.reveals:
            pet = world.get("pet")
            world.say(
                f"{helper.id} spotted {pet.attrs['paw_word']} and a little trail of crumbs "
                f"leading away from the plate."
            )
            world.facts["revealed"] = "paw"
        else:
            world.facts["revealed"] = "none"


def solve_self(world: World, child: Entity, helper: Entity, parent: Entity, snack: Snack) -> None:
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came over, saw the tiny tooth, and smiled. "
        f'"There was no secret eater," {parent.pronoun()} said softly. '
        f'"You took a sleepy bite, your loose tooth popped out, and you stopped because your gum hurt."'
    )
    world.say(
        f"{child.id} blinked, then touched the new little gap and laughed. "
        f"The mystery had been hiding in {child.pronoun('possessive')} own mouth all along."
    )
    world.say(
        f"For breakfast, {parent.label_word} traded the rest of the crunchy {snack.label} for "
        f"{snack.safe_swap}, and {child.id} carried the tiny tooth as if it were the smallest clue in the world."
    )


def solve_pet(world: World, child: Entity, helper: Entity, parent: Entity, snack: Snack, pet: Entity) -> None:
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    pet.memes["ashamed"] += 1
    world.say(
        f"{parent.label_word.capitalize()} followed the crumb trail to {pet.label}, who was licking one last crumb "
        f"from {pet.pronoun('possessive')} nose."
    )
    world.say(
        f'"So that was our eater," {helper.id} said. {child.id} gave a surprised little laugh, '
        f"and even the mystery felt less dark once it had a whiskered face."
    )
    world.say(
        f"After that, {parent.label_word} put snacks high on a shelf, and because {child.id}'s tooth was still loose, "
        f"{parent.pronoun()} offered {snack.safe_swap} instead of another crunchy bite."
    )


def tell(snack: Snack, place: Place, tool: Tool, pet_cfg: PetCfg,
         child_name: str = "Nora", child_gender: str = "girl",
         helper_name: str = "Milo", helper_gender: str = "boy",
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        attrs={},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["careful"],
        attrs={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        attrs={},
    ))
    snack_ent = world.add(Entity(
        id="snack",
        kind="thing",
        type="snack",
        label=snack.label,
        attrs={},
    ))
    snack_ent.meters["hardness"] = float(snack.hardness)
    if pet_cfg.id != "none":
        pet = world.add(Entity(
            id="pet",
            kind="character",
            type=pet_cfg.type,
            role="pet",
            label=pet_cfg.label,
            attrs={"paw_word": pet_cfg.paw_word},
        ))
    else:
        pet = None

    world.facts.update(
        snack_id=snack.id,
        place_id=place.id,
        tool_id=tool.id,
        pet_id=pet_cfg.id,
        clue_tooth=False,
        clue_paw=False,
        clue_pillow_crumbs=False,
        clue_floor_crumbs=False,
    )

    introduce(world, child, helper, parent, snack, place, pet_cfg)
    foreshadow(world, child, parent, snack)

    world.para()
    night_event(world, snack, place, pet_cfg)
    morning_discovery(world, child, helper, snack)

    world.para()
    inspect(world, child, helper, tool, place)
    culprit = world.facts["culprit"]
    if culprit == "self":
        solve_self(world, child, helper, parent, snack)
    elif culprit == "pet" and pet is not None:
        solve_pet(world, child, helper, parent, snack, pet)
    else:
        raise StoryError("(No story: the clues do not point to any grounded eater.)")

    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        pet=pet,
        snack_cfg=snack,
        place_cfg=place,
        tool_cfg=tool,
        solved=True,
        dental_visit=True,
    )
    return world


KNOWLEDGE = {
    "dental": [(
        "What does dental mean?",
        "Dental means having to do with teeth or the care of teeth. A dental office is a place where people help keep teeth healthy."
    )],
    "teeth": [(
        "Why can a loose tooth feel sore when you bite something hard?",
        "A loose tooth is already wiggly, so a hard bite can press on it and make the gum feel tender. That is why soft foods can feel better for a little while."
    )],
    "soft_food": [(
        "Why do people sometimes choose soft food when a tooth is loose?",
        "Soft food does not push as hard on a sore tooth. It can make eating more comfortable until the tooth comes out."
    )],
    "flashlight": [(
        "Why is a flashlight useful in a mystery?",
        "A flashlight helps you see small things in dim corners. Good light can turn a hidden clue into an easy one to notice."
    )],
    "magnifier": [(
        "What does a magnifying glass do?",
        "A magnifying glass makes small details look bigger. That helps you notice tiny marks, crumbs, or prints."
    )],
    "cat": [(
        "Why do cats investigate food with their noses?",
        "Cats use their noses to learn what something is and whether it smells interesting. A tasty smell can make them come closer."
    )],
    "dog": [(
        "Why do dogs follow crumbs?",
        "Dogs are very good at smelling food. A crumb trail can lead them straight to where a snack was left."
    )],
}
KNOWLEDGE_ORDER = ["dental", "teeth", "soft_food", "flashlight", "magnifier", "cat", "dog"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    snack = f["snack_cfg"]
    tool = f["tool_cfg"]
    culprit = f["culprit"]
    if culprit == "self":
        return [
            'Write a gentle mystery for a 3-to-5-year-old that includes the words "dental" and "eater".',
            f"Tell a foreshadowing mystery where {child.id} has a loose tooth before bed, saves {snack.phrase}, and in the morning thinks a midnight eater came.",
            f"Write a child-friendly mystery where {helper.id} uses {tool.phrase} to solve a bedtime snack puzzle, and the ending explains that the clue came from a wiggly tooth.",
        ]
    return [
        'Write a gentle mystery for a 3-to-5-year-old that includes the words "dental" and "eater".',
        f"Tell a foreshadowing mystery where {child.id} has a loose tooth, a snack goes missing overnight, and {helper.id} looks for the true eater.",
        f"Write a simple mystery where {tool.label} reveals the clue that a pet, not a monster, nibbled the saved snack.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    snack = f["snack_cfg"]
    place = f["place_cfg"]
    tool = f["tool_cfg"]
    culprit = f["culprit"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {helper.id}, and {child.id}'s {parent.label_word}. They are trying to solve a small bedtime mystery about a half-eaten snack."
        ),
        (
            f"Why did the story hint early that something dental might matter later?",
            f"The story shows right away that {child.id} has a very loose tooth and that the grown-up talks about the dental office. That early clue matters later because the tooth becomes part of the answer."
        ),
        (
            f"What made {child.id} think there was a secret eater?",
            f"In the morning, part of the saved {snack.label} was missing from {place.phrase}. Because {child.id} had been asleep, the bite felt mysterious at first."
        ),
        (
            f"How did {helper.id} investigate the mystery?",
            f"{helper.id} brought {tool.phrase} and looked carefully where the snack had been left. The tool mattered because it could reveal the clue that fit the real answer."
        ),
    ]
    if culprit == "self":
        qa.append((
            "Who was the eater, really?",
            f"It was {child.id}, not a stranger. {child.pronoun('possessive').capitalize()} loose tooth popped out during a sleepy bite, so {child.pronoun()} stopped eating and did not understand the clue until morning."
        ))
        qa.append((
            "Why did the grown-up offer a softer breakfast at the end?",
            f"{child.id}'s gum was tender after the tooth came out. A softer food would be easier to eat and would not press hard on the sore spot."
        ))
    else:
        pet = f["pet"]
        qa.append((
            "Who was the eater, really?",
            f"It was {pet.label}, not a monster. The clue trail led away from the plate and showed that the pet had reached the snack in the night."
        ))
        qa.append((
            f"Why did the family change where snacks were kept after the mystery?",
            f"They learned that low places were easy for the pet to reach. Putting snacks on a shelf would stop the same kind of nibbling mystery from happening again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"dental", "teeth", "soft_food"} | set(world.facts["tool_cfg"].tags)
    pet = world.facts.get("pet")
    if pet is not None:
        if pet.type == "cat":
            tags.add("cat")
        if pet.type == "dog":
            tags.add("dog")
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: culprit={world.facts.get('culprit')} revealed={world.facts.get('revealed')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        snack="toast_star",
        place="pillow_tin",
        tool="dental_mirror",
        pet="cat",
        child_name="Nora",
        child_gender="girl",
        helper_name="Milo",
        helper_gender="boy",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        snack="apple_slice",
        place="bedside_saucer",
        tool="flashlight",
        pet="none",
        child_name="Ben",
        child_gender="boy",
        helper_name="June",
        helper_gender="girl",
        parent="father",
        trait="thoughtful",
    ),
    StoryParams(
        snack="cracker_moon",
        place="step_stool_plate",
        tool="magnifier",
        pet="dog",
        child_name="Lily",
        child_gender="girl",
        helper_name="Owen",
        helper_gender="boy",
        parent="mother",
        trait="quiet",
    ),
    StoryParams(
        snack="toast_star",
        place="hall_rug_plate",
        tool="magnifier",
        pet="cat",
        child_name="Theo",
        child_gender="boy",
        helper_name="Rose",
        helper_gender="girl",
        parent="father",
        trait="brave",
    ),
]


def explain_combo(snack: Snack, place: Place, tool: Tool, pet: PetCfg) -> str:
    culprit = actual_culprit(snack, place, pet)
    if culprit == "none":
        return (
            f"(No story: {snack.label} at {place.label} would not create a grounded mystery here. "
            f"There must be either a near-bed tooth clue or a pet-reachable crumb trail.)"
        )
    if not tool_solves(tool, culprit):
        need = "a tooth clue" if culprit == "self" else "paw clues"
        return (
            f"(No story: {tool.label} would not reveal the deciding clue. "
            f"This mystery needs {need}.)"
        )
    return "(No story: invalid combination.)"


ASP_RULES = r"""
self_possible(S,P) :- hardness(S,H), H >= 2, near_bed(P).
pet_possible(S,P,Pet) :- pet(Pet), Pet != none, pet_reachable(P), likes_crunchy(Pet), crumbs(S).
culprit(S,P,Pet,self) :- self_possible(S,P).
culprit(S,P,Pet,pet) :- not self_possible(S,P), pet_possible(S,P,Pet).
needs(self,tooth).
needs(pet,paw).
tool_solves(T,C) :- reveals(T,Need), needs(C,Need).
valid(S,P,T,Pet) :- culprit(S,P,Pet,C), tool_solves(T,C).
#show valid/4.
"""

OUTCOME_RULES = r"""
self_possible(S,P) :- hardness(S,H), H >= 2, near_bed(P).
pet_possible(S,P,Pet) :- pet(Pet), Pet != none, pet_reachable(P), likes_crunchy(Pet), crumbs(S).
outcome(self) :- chosen_snack(S), chosen_place(P), self_possible(S,P).
outcome(pet) :- chosen_snack(S), chosen_place(P), chosen_pet(Pet), not self_possible(S,P), pet_possible(S,P,Pet).
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("hardness", sid, snack.hardness))
        if snack.crumbs:
            lines.append(asp.fact("crumbs", sid))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.near_bed:
            lines.append(asp.fact("near_bed", pid))
        if place.pet_reachable:
            lines.append(asp.fact("pet_reachable", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for clue in sorted(tool.reveals):
            lines.append(asp.fact("reveals", tid, clue))
    for pet_id, pet in PETS.items():
        lines.append(asp.fact("pet", pet_id))
        if pet.likes_crunchy:
            lines.append(asp.fact("likes_crunchy", pet_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_outcome_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{OUTCOME_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_snack", params.snack),
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_pet", params.pet),
    ])
    model = asp.one_model(asp_outcome_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "none"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a foreshadowed bedtime mystery about a half-eaten snack, a loose tooth, and the true eater."
    )
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, helper: bool = False, avoid: str = "") -> str:
    if gender == "girl":
        pool = HELPER_GIRL_NAMES if helper else GIRL_NAMES
    else:
        pool = HELPER_BOY_NAMES if helper else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snack and args.place and args.tool and args.pet:
        snack = SNACKS[args.snack]
        place = PLACES[args.place]
        tool = TOOLS[args.tool]
        pet = PETS[args.pet]
        culprit = actual_culprit(snack, place, pet)
        if culprit == "none" or not tool_solves(tool, culprit):
            raise StoryError(explain_combo(snack, place, tool, pet))

    combos = [
        c for c in valid_combos()
        if (args.snack is None or c[0] == args.snack)
        and (args.place is None or c[1] == args.place)
        and (args.tool is None or c[2] == args.tool)
        and (args.pet is None or c[3] == args.pet)
    ]
    if not combos:
        if args.snack and args.place and args.tool and args.pet:
            raise StoryError(explain_combo(SNACKS[args.snack], PLACES[args.place], TOOLS[args.tool], PETS[args.pet]))
        raise StoryError("(No valid combination matches the given options.)")

    snack_id, place_id, tool_id, pet_id = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender, helper=False)
    helper_name = _pick_name(rng, helper_gender, helper=True, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        snack=snack_id,
        place=place_id,
        tool=tool_id,
        pet=pet_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.snack not in SNACKS or params.place not in PLACES or params.tool not in TOOLS or params.pet not in PETS:
        raise StoryError("(No story: one or more requested options are unknown.)")
    snack = SNACKS[params.snack]
    place = PLACES[params.place]
    tool = TOOLS[params.tool]
    pet = PETS[params.pet]
    culprit = actual_culprit(snack, place, pet)
    if culprit == "none" or not tool_solves(tool, culprit):
        raise StoryError(explain_combo(snack, place, tool, pet))

    world = tell(
        snack=snack,
        place=place,
        tool=tool,
        pet_cfg=pet,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in asp:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            continue

    bad = 0
    for p in cases:
        expected = actual_culprit(SNACKS[p.snack], PLACES[p.place], PETS[p.pet])
        got = asp_outcome(p)
        if expected != got:
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        print(OUTCOME_RULES)
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (snack, place, tool, pet) combos:\n")
        for snack, place, tool, pet in combos:
            print(f"  {snack:12} {place:16} {tool:14} {pet}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            culprit = actual_culprit(SNACKS[p.snack], PLACES[p.place], PETS[p.pet])
            header = f"### {p.child_name}: {p.snack} at {p.place} ({p.tool}, culprit={culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
