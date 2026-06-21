#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pour_necessity_leprechaun_repetition_misunderstanding_transformation_bedtime.py
==========================================================================================================

A standalone story world for a gentle bedtime misunderstanding tale:

A child and parent keep a tiny windowsill "leprechaun garden." At bedtime the
parent says they should pour only what is necessary for the little plant.
The child misunderstands "necessary" as if Necessity were the leprechaun's
name, so the child repeats a pouring ritual again and again. The garden state
changes: some stories land on the just-right amount, while others make a soft
little puddle that has to be mopped up and measured properly. In every version,
something transforms: a thirsty plant perks up, and sometimes a soggy paper
leprechaun changes too.

The world model drives the prose:
- physical meters: water, puddle, soggy, perk
- emotional memes: care, worry, relief, learning
- repeated pouring causes the misunderstanding beat
- resolution uses a sensible bedtime fix and ends with a calm changed image

Run it
------
    python storyworlds/worlds/gpt-5.4/pour_necessity_leprechaun_repetition_misunderstanding_transformation_bedtime.py
    python storyworlds/worlds/gpt-5.4/pour_necessity_leprechaun_repetition_misunderstanding_transformation_bedtime.py --plant clover --vessel teacup --attempts 2
    python storyworlds/worlds/gpt-5.4/pour_necessity_leprechaun_repetition_misunderstanding_transformation_bedtime.py --vessel pitcher --remedy counting_spoon
    python storyworlds/worlds/gpt-5.4/pour_necessity_leprechaun_repetition_misunderstanding_transformation_bedtime.py --all --qa
    python storyworlds/worlds/gpt-5.4/pour_necessity_leprechaun_repetition_misunderstanding_transformation_bedtime.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    need: int
    transform_text: str
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
class Vessel:
    id: str
    label: str
    phrase: str
    pour: int
    sound: str
    bedtime_place: str
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
class LeprechaunGuide:
    id: str
    label: str
    phrase: str
    material: str
    soak_threshold: int
    transform_text: str
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
class Remedy:
    id: str
    label: str
    phrase: str
    absorb: int
    sense: int
    cleanup_text: str
    measure_text: str
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


def _r_perk(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    need = int(plant.attrs["need"])
    if plant.meters["water"] >= need and ("perk", plant.id) not in world.fired:
        world.fired.add(("perk", plant.id))
        plant.meters["perk"] += 1
        out.append("__perk__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    excess = int(plant.meters["water"] - plant.attrs["need"])
    if excess > 0 and ("spill", plant.id, excess) not in world.fired:
        world.fired.add(("spill", plant.id, excess))
        world.get("tray").meters["puddle"] = float(excess)
        world.get("guide").meters["soggy"] += float(excess)
        child = world.get("child")
        child.memes["worry"] += 1
        out.append("__spill__")
    return out


def _r_guide_transform(world: World) -> list[str]:
    out: list[str] = []
    guide = world.get("guide")
    if guide.meters["soggy"] >= guide.attrs["soak_threshold"] and ("guide_transform", guide.id) not in world.fired:
        world.fired.add(("guide_transform", guide.id))
        guide.meters["changed"] += 1
        out.append("__guide_transform__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="perk", tag="physical", apply=_r_perk),
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="guide_transform", tag="physical", apply=_r_guide_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(x for x in lines if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLANTS = {
    "clover": Plant(
        id="clover",
        label="clover",
        phrase="a tiny pot of clover",
        need=2,
        transform_text="the little clover lifted its sleepy heads and looked greener",
        tags={"plant", "clover"},
    ),
    "moss": Plant(
        id="moss",
        label="moss",
        phrase="a velvet patch of moss",
        need=1,
        transform_text="the moss turned from dull to plush and bright",
        tags={"plant", "moss"},
    ),
    "sprouts": Plant(
        id="sprouts",
        label="sprouts",
        phrase="a cup of shamrock sprouts",
        need=3,
        transform_text="the shamrock sprouts straightened as if tiny green umbrellas had opened",
        tags={"plant", "sprouts"},
    ),
}

VESSELS = {
    "shell_spoon": Vessel(
        id="shell_spoon",
        label="shell spoon",
        phrase="a shell-shaped spoon",
        pour=1,
        sound="plink",
        bedtime_place="on the windowsill beside the moon lamp",
        tags={"pour", "spoon"},
    ),
    "teacup": Vessel(
        id="teacup",
        label="teacup",
        phrase="a doll-sized teacup",
        pour=2,
        sound="plip-plip",
        bedtime_place="beside the storybooks",
        tags={"pour", "cup"},
    ),
    "pitcher": Vessel(
        id="pitcher",
        label="little pitcher",
        phrase="a little silver pitcher",
        pour=3,
        sound="glup",
        bedtime_place="next to the curtain where moonlight fell",
        tags={"pour", "pitcher"},
    ),
}

LEPRECHAUNS = {
    "paper": LeprechaunGuide(
        id="paper",
        label="paper leprechaun",
        phrase="a paper leprechaun on a craft stick",
        material="paper",
        soak_threshold=1,
        transform_text="its green ink blurred into soft mint swirls and its beard curled into a new shape",
        tags={"leprechaun", "paper"},
    ),
    "felt": LeprechaunGuide(
        id="felt",
        label="felt leprechaun",
        phrase="a felt leprechaun with a stitched smile",
        material="felt",
        soak_threshold=2,
        transform_text="its hat drooped low and its beard puffed out like a sleepy cloud",
        tags={"leprechaun", "felt"},
    ),
    "wood": LeprechaunGuide(
        id="wood",
        label="wooden leprechaun",
        phrase="a painted wooden leprechaun",
        material="wood",
        soak_threshold=3,
        transform_text="its painted shoes shone darker and its gold buckle gleamed with wet moonlight",
        tags={"leprechaun", "wood"},
    ),
}

REMEDIES = {
    "counting_spoon": Remedy(
        id="counting_spoon",
        label="counting spoon",
        phrase="a tiny counting spoon",
        absorb=0,
        sense=3,
        cleanup_text="did not need to mop anything up, because the water had landed just right",
        measure_text="counted out the sleepy sips one by one with the little spoon",
        qa_text="used the counting spoon to give the garden only the amount it needed",
        tags={"measure", "spoon"},
    ),
    "towel_saucer": Remedy(
        id="towel_saucer",
        label="towel and saucer",
        phrase="a folded towel and a small saucer",
        absorb=3,
        sense=3,
        cleanup_text="set the pot on a saucer and dabbed the shiny ring of water with the folded towel",
        measure_text="drew a tiny line on the cup and said that line was the bedtime necessity",
        qa_text="used a saucer and towel to catch the extra water and then measured a smaller bedtime pour",
        tags={"cleanup", "measure", "saucer"},
    ),
    "dropper": Remedy(
        id="dropper",
        label="glass dropper",
        phrase="a little glass dropper",
        absorb=2,
        sense=3,
        cleanup_text="sipped the extra water back out with the dropper until the soil stopped shining",
        measure_text="gave the plant only careful drops after that",
        qa_text="used a dropper to take away the extra water and then give careful drops",
        tags={"cleanup", "measure", "dropper"},
    ),
    "tip_it_out": Remedy(
        id="tip_it_out",
        label="tip the pot out",
        phrase="tilting the pot over the sink",
        absorb=1,
        sense=1,
        cleanup_text="tipped the pot roughly over the sink",
        measure_text="guessed the next amount",
        qa_text="tipped the pot and guessed",
        tags={"rough"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Eva", "June", "Cora", "Ivy", "Tessa"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Jude", "Eli", "Noah", "Leo"]
TRAITS = ["sleepy", "careful", "curious", "gentle", "earnest", "dreamy"]


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def total_water(vessel: Vessel, attempts: int) -> int:
    return vessel.pour * attempts


def overflow_amount(plant: Plant, vessel: Vessel, attempts: int) -> int:
    return max(0, total_water(vessel, attempts) - plant.need)


def can_resolve(plant: Plant, vessel: Vessel, attempts: int, remedy: Remedy) -> bool:
    return overflow_amount(plant, vessel, attempts) <= remedy.absorb


def valid_combos() -> list[tuple[str, str, str, int]]:
    combos: list[tuple[str, str, str, int]] = []
    for plant_id, plant in PLANTS.items():
        for vessel_id, vessel in VESSELS.items():
            for remedy_id, remedy in REMEDIES.items():
                if remedy.sense < SENSE_MIN:
                    continue
                for attempts in (1, 2, 3):
                    if can_resolve(plant, vessel, attempts, remedy):
                        combos.append((plant_id, vessel_id, remedy_id, attempts))
    return combos


@dataclass
class StoryParams:
    plant: str
    vessel: str
    leprechaun: str
    remedy: str
    attempts: int
    child_name: str
    child_gender: str
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


def predict_after_pours(world: World, attempts: int) -> dict:
    sim = world.copy()
    for _ in range(attempts):
        sim.get("plant").meters["water"] += float(sim.get("vessel").attrs["pour"])
        propagate(sim, narrate=False)
    return {
        "water": int(sim.get("plant").meters["water"]),
        "puddle": int(sim.get("tray").meters["puddle"]),
        "guide_changed": sim.get("guide").meters["changed"] >= THRESHOLD,
        "plant_perked": sim.get("plant").meters["perk"] >= THRESHOLD,
    }


def intro(world: World, child: Entity, parent: Entity, plant: Plant, vessel: Vessel, guide: LeprechaunGuide) -> None:
    child.memes["care"] += 1
    world.say(
        f"Every night before bed, {child.id} and {child.pronoun('possessive')} "
        f"{parent.label_word} visited {plant.phrase} {vessel.bedtime_place}."
    )
    world.say(
        f"Beside the pot stood {guide.phrase}, as if a tiny leprechaun were keeping the garden company."
    )
    world.say(
        f"The room was dim and soft, with pajamas on, teeth brushed, and only one last bedtime job left to do."
    )


def explain_necessity(world: World, child: Entity, parent: Entity, plant: Plant, vessel: Vessel) -> None:
    world.say(
        f'"Tonight we pour only what is necessary," {parent.label_word} whispered, handing '
        f"{child.id} {vessel.phrase}. \"Just enough for the {plant.label} to sleep well.\""
    )


def misunderstanding(world: World, child: Entity, guide: LeprechaunGuide) -> None:
    child.memes["misunderstanding"] += 1
    world.say(
        f"{child.id} looked at {guide.label} and blinked. In the hush of bedtime, "
        f"{child.pronoun()} thought Necessity must be the leprechaun's very own name."
    )


def repeated_pours(world: World, child: Entity, plant: Plant, vessel: Vessel, attempts: int) -> None:
    count_words = {1: "Once", 2: "Twice", 3: "Three times"}
    lines = []
    for n in range(1, attempts + 1):
        world.get("plant").meters["water"] += float(vessel.pour)
        propagate(world, narrate=False)
        lines.append(
            f'{n}. "{vessel.sound} for the {plant.label}, {vessel.sound} for Necessity," '
            f"{child.id} murmured"
        )
    world.say(
        f'{count_words.get(attempts, str(attempts))}, {child.id} tipped {vessel.phrase}. '
        + "; ".join(lines[:-1] + [lines[-1] + "."])
    )


def notice_change(world: World, child: Entity, plant: Plant, guide: LeprechaunGuide) -> None:
    if world.get("tray").meters["puddle"] >= THRESHOLD:
        world.say(
            f"Then both of them saw it: the soil had gone shiny, a little puddle had slipped into the tray, "
            f"and even the {guide.label} was damp at the toes."
        )
    else:
        world.say(
            f"When the last drop settled, the room stayed neat and still, and the little pot simply drank in the bedtime pour."
        )
    if world.get("plant").meters["perk"] >= THRESHOLD:
        world.say(f"Soon {plant.transform_text}.")
    if world.get("guide").meters["changed"] >= THRESHOLD:
        world.say(
            f"The {guide.label} had changed too: {guide.transform_text}."
        )


def clarify(world: World, child: Entity, parent: Entity) -> None:
    child.memes["learning"] += 1
    world.say(
        f'"Oh, little one," {parent.label_word} said with a smile, '
        f'"necessity is not the leprechaun\'s name. It means only as much as we truly need."'
    )


def repair(world: World, child: Entity, parent: Entity, remedy: Remedy) -> None:
    tray = world.get("tray")
    excess = int(tray.meters["puddle"])
    if excess > 0:
        tray.meters["puddle"] = 0.0
        child.memes["relief"] += 1
        world.say(
            f"Together they moved slowly and softly. {parent.label_word.capitalize()} {remedy.cleanup_text}."
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} smiled because they were already close to right: {remedy.cleanup_text}."
        )
    world.say(
        f"Then {parent.pronoun()} {remedy.measure_text}, so the next pour would match the bedtime necessity."
    )


def ending(world: World, child: Entity, parent: Entity, plant: Plant, guide: LeprechaunGuide) -> None:
    child.memes["calm"] += 1
    child.memes["relief"] += 1
    world.say(
        f'{child.id} nodded. "So Necessity is a how-much word," {child.pronoun()} said, '
        f"carefully tasting the idea out loud."
    )
    world.say(
        f"{parent.label_word.capitalize()} kissed the top of {child.pronoun('possessive')} head, and together they tucked the "
        f"{plant.label} and the {guide.label} into the moonlit windowsill."
    )
    if world.get("tray").meters["puddle"] >= THRESHOLD:
        world.say("But now the tray was dry, the lesson was clear, and the room felt quiet again.")
    else:
        world.say("Everything looked just right, as if the room itself were pleased by the gentle measure.")
    world.say(
        f"When {child.id} glanced back from the doorway, {plant.transform_text}, and the tiny leprechaun seemed ready for sleep too."
    )


def tell(
    plant: Plant,
    vessel: Vessel,
    guide_cfg: LeprechaunGuide,
    remedy: Remedy,
    attempts: int,
    child_name: str = "Lila",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait], label=child_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    plant_ent = world.add(
        Entity(
            id="plant",
            type="plant",
            label=plant.label,
            phrase=plant.phrase,
            attrs={"need": plant.need, "transform_text": plant.transform_text},
        )
    )
    vessel_ent = world.add(
        Entity(
            id="vessel",
            type="vessel",
            label=vessel.label,
            phrase=vessel.phrase,
            attrs={"pour": vessel.pour},
        )
    )
    guide_ent = world.add(
        Entity(
            id="guide",
            type="guide",
            label=guide_cfg.label,
            phrase=guide_cfg.phrase,
            attrs={"soak_threshold": guide_cfg.soak_threshold, "transform_text": guide_cfg.transform_text},
        )
    )
    tray = world.add(Entity(id="tray", type="tray", label="tray"))
    plant_ent.meters["water"] = 0.0
    plant_ent.meters["perk"] = 0.0
    guide_ent.meters["soggy"] = 0.0
    guide_ent.meters["changed"] = 0.0
    tray.meters["puddle"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["learning"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["calm"] = 0.0

    intro(world, child, parent, plant, vessel, guide_cfg)
    explain_necessity(world, child, parent, plant, vessel)

    world.para()
    misunderstanding(world, child, guide_cfg)
    pred = predict_after_pours(world, attempts)
    world.facts["predicted"] = pred
    repeated_pours(world, child, plant, vessel, attempts)
    propagate(world, narrate=False)
    notice_change(world, child, plant, guide_cfg)

    world.para()
    clarify(world, child, parent)
    repair(world, child, parent, remedy)

    world.para()
    ending(world, child, parent, plant, guide_cfg)

    total = total_water(vessel, attempts)
    excess = overflow_amount(plant, vessel, attempts)
    outcome = "spill" if excess > 0 else "just_right"
    world.facts.update(
        child=child,
        parent=parent,
        plant_cfg=plant,
        vessel_cfg=vessel,
        guide_cfg=guide_cfg,
        remedy=remedy,
        attempts=attempts,
        total_water=total,
        excess=excess,
        outcome=outcome,
        plant_perked=plant_ent.meters["perk"] >= THRESHOLD,
        guide_changed=guide_ent.meters["changed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "necessity": [
        (
            "What does necessity mean?",
            "Necessity means something is needed. If you use only what is necessary, you use just enough and no more."
        )
    ],
    "pour": [
        (
            "What does pour mean?",
            "To pour means to let a liquid flow from one container into another place. Water, milk, and juice can all pour."
        )
    ],
    "leprechaun": [
        (
            "What is a leprechaun in stories?",
            "A leprechaun is a tiny make-believe figure from old stories, often shown in green clothes. In bedtime tales, a leprechaun can be playful and magical, even when it is only a decoration."
        )
    ],
    "plant": [
        (
            "Why do little plants need careful watering?",
            "Small plants need water to live, but too much can make the soil soggy. A gentle amount helps the roots without making a puddle."
        )
    ],
    "measure": [
        (
            "Why is measuring useful when you water something?",
            "Measuring helps you give the right amount instead of guessing. It is a calm way to match what the plant really needs."
        )
    ],
    "cleanup": [
        (
            "What should you do if you spill water by accident?",
            "Move slowly and wipe it up with help. Cleaning a spill right away keeps things safe and dry."
        )
    ],
    "paper": [
        (
            "What happens when paper gets wet?",
            "Paper can turn soft, wrinkly, or blurry when it gets wet. Its shape can change because the water soaks into it."
        )
    ],
    "felt": [
        (
            "What happens when felt gets wet?",
            "Felt can go floppy and heavy when it gets wet. It usually needs time to dry and puff up again."
        )
    ],
    "wood": [
        (
            "What happens when painted wood gets wet?",
            "Painted wood can look darker and shinier when it gets wet. After it dries, it often looks more like itself again."
        )
    ],
}
KNOWLEDGE_ORDER = ["necessity", "pour", "leprechaun", "plant", "measure", "cleanup", "paper", "felt", "wood"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    plant = f["plant_cfg"]
    vessel = f["vessel_cfg"]
    guide = f["guide_cfg"]
    outcome = f["outcome"]
    if outcome == "spill":
        return [
            f'Write a bedtime story for a 3-to-5-year-old that includes the words "pour", "necessity", and "leprechaun".',
            f"Tell a gentle story where {child.id} misunderstands the word necessity as the name of a tiny leprechaun and repeats a bedtime pour until a little puddle appears.",
            f"Write a soft misunderstanding story set by a windowsill garden, where repeated pouring changes the {plant.label} and the {guide.label}, and a parent explains what necessity really means.",
        ]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "pour", "necessity", and "leprechaun".',
        f"Tell a gentle repetition story where {child.id} thinks Necessity is a leprechaun's name, but the repeated pours happen to come out just right for the {plant.label}.",
        f"Write a calm bedtime misunderstanding tale in which a child learns that necessity means only the amount a small plant truly needs.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    plant = f["plant_cfg"]
    vessel = f["vessel_cfg"]
    guide = f["guide_cfg"]
    remedy = f["remedy"]
    attempts = f["attempts"]
    excess = f["excess"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {parent.label_word}, and a tiny bedtime garden watched by a {guide.label}. They share one quiet job before sleep."
        ),
        (
            "What misunderstanding did the child have?",
            f"{child.id} thought Necessity was the leprechaun's name instead of a word about how much water was needed. That is why {child.pronoun()} kept repeating the bedtime pour."
        ),
        (
            f"Why did {child.id} pour more than once?",
            f"{child.id} repeated the pour {attempts} times because {child.pronoun()} believed one sip should go to the {plant.label} and another to Necessity the leprechaun. The repeated words turned the misunderstanding into action."
        ),
    ]
    if excess > 0:
        qa.append(
            (
                "What problem happened after the repeated pouring?",
                f"The plant got more water than it needed, so a little puddle slipped into the tray and the {guide.label} became damp. The extra water came from pouring {vessel.phrase} again and again instead of stopping at the necessary amount."
            )
        )
        qa.append(
            (
                f"How did {child.id}'s {parent.label_word} fix it?",
                f"{parent.label_word.capitalize()} {remedy.qa_text}. That solved the puddle and turned the mistake into a calmer way to care for the garden."
            )
        )
    else:
        qa.append(
            (
                "Did the child make a puddle?",
                f"No. Even though {child.id} misunderstood the word, the total bedtime pour happened to match what the {plant.label} needed. So the garden changed quietly instead of making a spill."
            )
        )
    if f["guide_changed"]:
        qa.append(
            (
                f"How did the {guide.label} change?",
                f"It changed because some water reached it during the bedtime pours. After that, {guide.transform_text}."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the room calm again and {child.id} understanding that necessity means only the amount truly needed. In the final bedtime picture, {plant.transform_text}."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"necessity", "pour", "leprechaun", "plant", "measure"}
    if f["excess"] > 0:
        tags.add("cleanup")
    tags |= set(f["guide_cfg"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo_rejection(plant: Plant, vessel: Vessel, remedy: Remedy, attempts: int) -> str:
    excess = overflow_amount(plant, vessel, attempts)
    if remedy.sense < SENSE_MIN:
        return (
            f"(Refusing remedy '{remedy.id}': it is too rough for this bedtime world "
            f"(sense={remedy.sense} < {SENSE_MIN}). Choose a calmer fix like "
            f"{', '.join(sorted(r.id for r in sensible_remedies()))}.)"
        )
    return (
        f"(No story: {attempts} pours from {vessel.phrase} would give {total_water(vessel, attempts)} sips, "
        f"but the {plant.label} needs only {plant.need}. That leaves {excess} extra, and "
        f"{remedy.phrase} cannot calmly fix that much bedtime spill.)"
    )


def outcome_of(params: StoryParams) -> str:
    plant = PLANTS[params.plant]
    vessel = VESSELS[params.vessel]
    excess = overflow_amount(plant, vessel, params.attempts)
    return "spill" if excess > 0 else "just_right"


ASP_RULES = r"""
sensible_remedy(R) :- remedy(R), sense(R,S), sense_min(M), S >= M.
excess(P,V,A,E) :- need(P,N), pour(V,Q), attempts(A), E = Q*A - N, E > 0.
valid(P,V,R,A) :- plant(P), vessel(V), remedy(R), attempts(A), sensible_remedy(R),
                  need(P,N), pour(V,Q), X = Q*A - N, X <= absorb(R).

outcome(spill) :- chosen_plant(P), chosen_vessel(V), chosen_attempts(A),
                  need(P,N), pour(V,Q), Q*A > N.
outcome(just_right) :- chosen_plant(P), chosen_vessel(V), chosen_attempts(A),
                       need(P,N), pour(V,Q), Q*A <= N.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for plant_id, plant in PLANTS.items():
        lines.append(asp.fact("plant", plant_id))
        lines.append(asp.fact("need", plant_id, plant.need))
    for vessel_id, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vessel_id))
        lines.append(asp.fact("pour", vessel_id, vessel.pour))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("absorb", remedy_id, remedy.absorb))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
    for attempts in (1, 2, 3):
        lines.append(asp.fact("attempts", attempts))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
            asp.fact("chosen_plant", params.plant),
            asp.fact("chosen_vessel", params.vessel),
            asp.fact("chosen_attempts", params.attempts),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


CURATED = [
    StoryParams(
        plant="clover",
        vessel="shell_spoon",
        leprechaun="paper",
        remedy="counting_spoon",
        attempts=2,
        child_name="Lila",
        child_gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        plant="moss",
        vessel="teacup",
        leprechaun="felt",
        remedy="towel_saucer",
        attempts=1,
        child_name="Milo",
        child_gender="boy",
        parent="father",
        trait="gentle",
    ),
    StoryParams(
        plant="clover",
        vessel="teacup",
        leprechaun="paper",
        remedy="towel_saucer",
        attempts=2,
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        trait="earnest",
    ),
    StoryParams(
        plant="sprouts",
        vessel="pitcher",
        leprechaun="wood",
        remedy="dropper",
        attempts=1,
        child_name="Theo",
        child_gender="boy",
        parent="father",
        trait="dreamy",
    ),
    StoryParams(
        plant="sprouts",
        vessel="shell_spoon",
        leprechaun="felt",
        remedy="counting_spoon",
        attempts=3,
        child_name="Ivy",
        child_gender="girl",
        parent="mother",
        trait="careful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime misunderstanding about how much to pour into a tiny leprechaun garden."
    )
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--leprechaun", choices=LEPRECHAUNS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--attempts", type=int, choices=[1, 2, 3])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_combo_rejection(
            PLANTS[args.plant] if args.plant else next(iter(PLANTS.values())),
            VESSELS[args.vessel] if args.vessel else next(iter(VESSELS.values())),
            REMEDIES[args.remedy],
            args.attempts if args.attempts is not None else 1,
        ))

    if args.plant and args.vessel and args.remedy and args.attempts is not None:
        plant = PLANTS[args.plant]
        vessel = VESSELS[args.vessel]
        remedy = REMEDIES[args.remedy]
        if not can_resolve(plant, vessel, args.attempts, remedy) or remedy.sense < SENSE_MIN:
            raise StoryError(explain_combo_rejection(plant, vessel, remedy, args.attempts))

    combos = [
        c for c in valid_combos()
        if (args.plant is None or c[0] == args.plant)
        and (args.vessel is None or c[1] == args.vessel)
        and (args.remedy is None or c[2] == args.remedy)
        and (args.attempts is None or c[3] == args.attempts)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    plant_id, vessel_id, remedy_id, attempts = rng.choice(sorted(combos))
    leprechaun_id = args.leprechaun or rng.choice(sorted(LEPRECHAUNS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        plant=plant_id,
        vessel=vessel_id,
        leprechaun=leprechaun_id,
        remedy=remedy_id,
        attempts=attempts,
        child_name=name,
        child_gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        plant = PLANTS[params.plant]
        vessel = VESSELS[params.vessel]
        guide = LEPRECHAUNS[params.leprechaun]
        remedy = REMEDIES[params.remedy]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err.args[0]})") from None

    if remedy.sense < SENSE_MIN or not can_resolve(plant, vessel, params.attempts, remedy):
        raise StoryError(explain_combo_rejection(plant, vessel, remedy, params.attempts))

    world = tell(
        plant=plant,
        vessel=vessel,
        guide_cfg=guide,
        remedy=remedy,
        attempts=params.attempts,
        child_name=params.child_name,
        child_gender=params.child_gender,
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
        print(f"{len(combos)} compatible (plant, vessel, remedy, attempts) combos:\n")
        for plant, vessel, remedy, attempts in combos:
            print(f"  {plant:8} {vessel:11} {remedy:14} attempts={attempts}")
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
            header = f"### {p.child_name}: {p.plant} with {p.vessel} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
