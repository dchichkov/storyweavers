#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/spring_paper_intellectual_road_repair_inner_monologue.py
===================================================================================

A standalone story world about a child helping mend a village road in spring.

Seeded domain requirements:
- words: spring, paper, intellectual
- setting: road repair
- features: Inner Monologue, Transformation
- style: Myth

This world models a child who begins by trusting a clever plan on paper more than
the earth itself, then learns that road repair needs hands, material, and patient
craft. The story can end in two plausible ways: the patch holds, or spring rain
washes it loose. In both branches, the child changes.

Run it
------
    python storyworlds/worlds/gpt-5.4/spring_paper_intellectual_road_repair_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/spring_paper_intellectual_road_repair_inner_monologue.py --damage pothole --material gravel --tool tamper
    python storyworlds/worlds/gpt-5.4/spring_paper_intellectual_road_repair_inner_monologue.py --material paper_bundle
    python storyworlds/worlds/gpt-5.4/spring_paper_intellectual_road_repair_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/spring_paper_intellectual_road_repair_inner_monologue.py --verify
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
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
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
class Damage:
    id: str
    label: str
    phrase: str
    image: str
    severity: int
    crossing: str
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
    phrase: str
    strength: int
    suited: set[str] = field(default_factory=set)
    work_text: str = ""
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
    power: int
    works_with: set[str] = field(default_factory=set)
    action_text: str = ""
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
class Helper:
    id: str
    label: str
    kind: str
    bonus: int
    arrival_text: str
    wisdom_text: str
    closing_text: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_open_road(world: World) -> list[str]:
    road = world.get("road")
    if road.meters["gap"] < THRESHOLD:
        return []
    sig = ("open_road",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    road.meters["risk"] += 1
    for person in world.characters():
        person.memes["worry"] += 1
    return ["__open__"]


def _r_patch_holds(world: World) -> list[str]:
    road = world.get("road")
    if road.meters["attempted"] < THRESHOLD:
        return []
    if road.meters["patch_score"] < world.facts["target_score"]:
        return []
    sig = ("holds",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    road.meters["smooth"] += 1
    road.meters["gap"] = 0.0
    road.meters["risk"] = 0.0
    hero = world.get("hero")
    hero.memes["wisdom"] += 1
    hero.memes["pride"] = 0.0
    hero.memes["joy"] += 1
    return ["__holds__"]


def _r_patch_washes(world: World) -> list[str]:
    road = world.get("road")
    if road.meters["attempted"] < THRESHOLD:
        return []
    if road.meters["patch_score"] >= world.facts["target_score"]:
        return []
    if world.facts["rain"] <= 0:
        return []
    sig = ("washes",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    road.meters["washed"] += 1
    road.meters["risk"] += 1
    hero = world.get("hero")
    hero.memes["doubt"] += 1
    hero.memes["wisdom"] += 1
    return ["__washed__"]


CAUSAL_RULES = [
    Rule(name="open_road", tag="physical", apply=_r_open_road),
    Rule(name="patch_holds", tag="physical", apply=_r_patch_holds),
    Rule(name="patch_washes", tag="physical", apply=_r_patch_washes),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


DAMAGES = {
    "crack": Damage(
        id="crack",
        label="crack",
        phrase="a long crack running through the king's road",
        image="like a black snake asleep in the dust",
        severity=2,
        crossing="the goat carts had to roll with one wheel lifted",
        tags={"road", "crack"},
    ),
    "pothole": Damage(
        id="pothole",
        label="pothole",
        phrase="a round pothole in the middle of the village road",
        image="deep enough to hide a moon puddle",
        severity=3,
        crossing="the bread cart had to creep around it",
        tags={"road", "pothole"},
    ),
    "washout": Damage(
        id="washout",
        label="washout",
        phrase="a washout where the hillside had bitten the road away",
        image="as if a river spirit had taken one hungry mouthful",
        severity=4,
        crossing="nobody dared take the shrine wagon across it",
        tags={"road", "washout"},
    ),
}

MATERIALS = {
    "clay": Material(
        id="clay",
        label="clay",
        phrase="red clay from the ditch bank",
        strength=1,
        suited={"crack"},
        work_text="pressed the red clay into the wound with both thumbs",
        tags={"clay"},
    ),
    "gravel": Material(
        id="gravel",
        label="gravel",
        phrase="a basket of gravel that clicked like little teeth",
        strength=2,
        suited={"crack", "pothole"},
        work_text="poured the gravel in until the hollow began to lose its hunger",
        tags={"gravel"},
    ),
    "cobbles": Material(
        id="cobbles",
        label="cobbles",
        phrase="river cobbles smooth as old coins",
        strength=3,
        suited={"pothole", "washout"},
        work_text="laid the cobbles one by one, locking their shoulders together",
        tags={"stone", "cobbles"},
    ),
    "paper_bundle": Material(
        id="paper_bundle",
        label="paper bundle",
        phrase="a bundle of folded paper",
        strength=0,
        suited=set(),
        work_text="stuffed paper into the gap, but the road only spat it back out",
        tags={"paper"},
    ),
}

TOOLS = {
    "hands": Tool(
        id="hands",
        label="hands",
        phrase="bare hands",
        power=1,
        works_with={"clay"},
        action_text="smoothed the top with careful palms",
        tags={"hands"},
    ),
    "tamper": Tool(
        id="tamper",
        label="tamper",
        phrase="the iron tamper",
        power=2,
        works_with={"clay", "gravel", "cobbles"},
        action_text="raised the tamper and brought it down in patient beats until the earth answered back",
        tags={"tamper", "tool"},
    ),
    "lever": Tool(
        id="lever",
        label="lever",
        phrase="a long ash-wood lever",
        power=1,
        works_with={"cobbles"},
        action_text="nudged each heavy stone into place with the lever and a grunt",
        tags={"lever", "tool"},
    ),
}

HELPERS = {
    "mason": Helper(
        id="mason",
        label="old Nerin the mason",
        kind="man",
        bonus=1,
        arrival_text="Old Nerin the mason came with dust on his sleeves and steady feet.",
        wisdom_text='"A road is not healed by naming it," he said. "It is healed when weight and water both agree to pass."',
        closing_text="Nerin nodded once, the way a mountain nods when it keeps a promise.",
        tags={"mason", "repair"},
    ),
    "ox": Helper(
        id="ox",
        label="Blue the ox",
        kind="beast",
        bonus=1,
        arrival_text="Blue the ox leaned into the yoke and dragged the stone sledge as calmly as if he were pulling a piece of the moon.",
        wisdom_text='"Even an ox knows the ground must be packed before it can carry others," the road keeper said.',
        closing_text="Blue snorted warm steam over the repaired road, as if blessing it.",
        tags={"ox", "repair"},
    ),
    "keeper": Helper(
        id="keeper",
        label="the road keeper",
        kind="woman",
        bonus=0,
        arrival_text="The road keeper came with a lantern-colored scarf and eyes that noticed every rut before a wheel did.",
        wisdom_text='"Plans belong on paper first," she said, "but roads belong to rain, stone, and feet."',
        closing_text="The keeper touched the road with her staff, like a priest touching an altar step.",
        tags={"keeper", "repair"},
    ),
}

GIRL_NAMES = ["Ila", "Mira", "Tesa", "Rin", "Luma", "Seli"]
BOY_NAMES = ["Tarin", "Ivo", "Nemo", "Rusal", "Darin", "Pavel"]
TRAITS = ["patient", "bright", "curious", "earnest", "stubborn", "quick-minded"]


def valid_combo(damage_id: str, material_id: str, tool_id: str) -> bool:
    if damage_id not in DAMAGES or material_id not in MATERIALS or tool_id not in TOOLS:
        return False
    damage = DAMAGES[damage_id]
    material = MATERIALS[material_id]
    tool = TOOLS[tool_id]
    return damage.id in material.suited and material.id in tool.works_with


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for damage_id in sorted(DAMAGES):
        for material_id in sorted(MATERIALS):
            for tool_id in sorted(TOOLS):
                if valid_combo(damage_id, material_id, tool_id):
                    out.append((damage_id, material_id, tool_id))
    return out


def repair_score(material: Material, tool: Tool, helper: Helper) -> int:
    return material.strength + tool.power + helper.bonus


def outcome_for_ids(damage_id: str, material_id: str, tool_id: str, helper_id: str, rain: int) -> str:
    if not valid_combo(damage_id, material_id, tool_id):
        raise StoryError(explain_rejection(damage_id, material_id, tool_id))
    if helper_id not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{helper_id}'.)")
    damage = DAMAGES[damage_id]
    material = MATERIALS[material_id]
    tool = TOOLS[tool_id]
    helper = HELPERS[helper_id]
    return "held" if repair_score(material, tool, helper) >= damage.severity + rain else "washed"


def explain_rejection(damage_id: str, material_id: str, tool_id: str) -> str:
    if damage_id not in DAMAGES:
        return f"(No story: unknown damage '{damage_id}'.)"
    if material_id not in MATERIALS:
        return f"(No story: unknown material '{material_id}'.)"
    if tool_id not in TOOLS:
        return f"(No story: unknown tool '{tool_id}'.)"
    damage = DAMAGES[damage_id]
    material = MATERIALS[material_id]
    tool = TOOLS[tool_id]
    if damage.id not in material.suited:
        return (
            f"(No story: {material.label} is not a believable way to mend a {damage.label}. "
            f"The road needs a real road-repair material for that kind of wound.)"
        )
    if material.id not in tool.works_with:
        return (
            f"(No story: {tool.label} does not sensibly place or pack {material.label}. "
            f"Pick a tool that can really work with that material.)"
        )
    return "(No story: that repair combination is unreasonable.)"


def predict_outcome(world: World, damage: Damage, material: Material, tool: Tool, helper: Helper, rain: int) -> dict:
    sim = world.copy()
    sim.facts["target_score"] = damage.severity + rain
    road = sim.get("road")
    road.meters["patch_score"] += material.strength
    road.meters["patch_score"] += tool.power
    road.meters["patch_score"] += helper.bonus
    road.meters["attempted"] += 1
    propagate(sim, narrate=False)
    return {
        "score": int(road.meters["patch_score"]),
        "target": int(sim.facts["target_score"]),
        "held": road.meters["smooth"] >= THRESHOLD,
        "washed": road.meters["washed"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, elder: Entity, damage: Damage) -> None:
    road = world.get("road")
    hero.memes["pride"] += 1
    world.say(
        f"In the first green week of spring, when thaw water ran singing under the stones, "
        f"{hero.id} stood beside {road.label} and looked at {damage.phrase}, {damage.image}."
    )
    world.say(
        f"{damage.crossing}, and {elder.id}, the village {elder.label}, had been walking up and down the edge of the wound since dawn."
    )
    world.say(
        f"{hero.id} carried a sheet of paper covered in tidy lines and measurements from the schoolhouse."
    )


def inner_pride(world: World, hero: Entity, damage: Damage) -> None:
    world.say(
        f'"I can think this through," {hero.id} told {hero.pronoun("object")}self. '
        f'"If I am the little intellectual everyone jokes about, then surely I can teach even a {damage.label} to obey a drawing on paper."'
    )


def show_problem(world: World, elder: Entity) -> None:
    road = world.get("road")
    propagate(world, narrate=False)
    if road.meters["risk"] >= THRESHOLD:
        world.say(
            f'{elder.id} touched the broken edge with a boot. "The road is angry today," {elder.pronoun()} said. '
            f'"If we leave it open, a wheel will sink and an ankle will twist."'
        )


def helper_arrives(world: World, helper: Helper) -> None:
    world.say(helper.arrival_text)
    world.say(helper.wisdom_text)


def decide(world: World, hero: Entity, damage: Damage, material: Material, tool: Tool, helper: Helper, rain: int) -> None:
    pred = predict_outcome(world, damage, material, tool, helper, rain)
    world.facts["predicted_score"] = pred["score"]
    world.facts["predicted_target"] = pred["target"]
    world.facts["predicted_outcome"] = "held" if pred["held"] else "washed"
    if pred["held"]:
        world.say(
            f'{hero.id} looked from the paper to the earth and thought, '
            f'"The paper shows the shape, but the real answer is in weight, packing, and time. We can do this if I listen."'
        )
    else:
        world.say(
            f'{hero.id} looked from the paper to the earth and thought, '
            f'"My drawing is neat, but spring rain is stronger than neatness. If we do only this much, the road may remember its wound."'
        )


def repair_attempt(world: World, hero: Entity, elder: Entity, damage: Damage, material: Material, tool: Tool, helper: Helper) -> None:
    road = world.get("road")
    hero.memes["effort"] += 1
    road.meters["patch_score"] += material.strength
    world.say(
        f"Together they began. {hero.id} brought {material.phrase} and {material.work_text}."
    )
    road.meters["patch_score"] += tool.power
    world.say(
        f"Then {hero.pronoun()} took up {tool.phrase} and {tool.action_text}."
    )
    if helper.bonus:
        road.meters["patch_score"] += helper.bonus
        world.say(
            f"{helper.label} added strength of {helper.kind} and habit, and the patch sat deeper and firmer under that help."
        )
    else:
        world.say(
            f"{helper.label} did not add muscle, but gave the work rhythm, and even rhythm can keep foolish haste away."
        )
    road.meters["attempted"] += 1
    propagate(world, narrate=False)
    if road.meters["smooth"] >= THRESHOLD:
        world.say(
            f"When they stepped back, the broken place no longer looked hungry. It lay flat and dark, ready to carry feet again."
        )
    elif road.meters["washed"] >= THRESHOLD:
        world.say(
            f"For one small hour the patch looked obedient. Then a fresh spring runnel slipped down the hill and worried at it."
        )
    else:
        world.say(
            "The work changed the road, though the road had not yet decided whether to keep the gift."
        )
    world.facts["attempted_material"] = material.id
    world.facts["attempted_tool"] = tool.id


def held_ending(world: World, hero: Entity, elder: Entity, helper: Helper, damage: Damage) -> None:
    road = world.get("road")
    world.say(
        f"A little later the bread cart rolled over the repaired place, and the wheel did not dip. The village road kept its back straight."
    )
    world.say(helper.closing_text)
    world.say(
        f'{hero.id} folded the paper and tucked it away. '
        f'"I thought paper made me wise," {hero.pronoun()} said softly, "but wisdom is when the hand, the eye, and the earth agree."'
    )
    hero.memes["transformed"] += 1
    road.meters["blessing"] += 1
    world.say(
        f"From that day on, people still smiled and called {hero.id} an intellectual, but now they said it with warmth, because {hero.pronoun()} could think and mend in the same breath."
    )
    world.facts["outcome"] = "held"


def washed_ending(world: World, hero: Entity, elder: Entity, helper: Helper, damage: Damage, material: Material, tool: Tool) -> None:
    road = world.get("road")
    world.say(
        f"The water found a weak seam, and by evening part of the patch sagged back into the {damage.label}. Nobody was hurt, but the road was not healed."
    )
    world.say(
        f'{hero.id} stared at the paper in {hero.pronoun("possessive")} hand and thought, '
        f'"A drawing is a lantern, not a wall. I cannot ask paper to bear what stone and labor have not yet learned to bear."'
    )
    world.say(
        f'{elder.id} put a hand on {hero.pronoun("possessive")} shoulder. "Then tomorrow," {elder.pronoun()} said, "we repair it better."'
    )
    world.say(
        f"So at dawn, before the swallows finished their first circle, {hero.id} came back without boasting. {hero.pronoun().capitalize()} brought a fresh sheet of paper for notes, but this time {hero.pronoun()} came ready to learn the road's own language."
    )
    hero.memes["transformed"] += 1
    road.meters["hope"] += 1
    world.facts["outcome"] = "washed"


def tell(
    damage: Damage,
    material: Material,
    tool: Tool,
    helper: Helper,
    hero_name: str = "Tarin",
    hero_gender: str = "boy",
    elder_type: str = "mother",
    trait: str = "bright",
    rain: int = 1,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label="child",
        role="hero",
        traits=[trait],
        attrs={},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="road warden",
        role="elder",
        traits=["steady"],
        attrs={},
    ))
    road = world.add(Entity(
        id="road",
        kind="thing",
        type="road",
        label="the village road",
        attrs={},
    ))
    road.meters["gap"] = float(damage.severity)

    world.facts["damage"] = damage
    world.facts["material"] = material
    world.facts["tool"] = tool
    world.facts["helper"] = helper
    world.facts["rain"] = int(rain)
    world.facts["target_score"] = damage.severity + rain
    world.facts["hero"] = hero
    world.facts["elder"] = elder

    introduce(world, hero, elder, damage)
    inner_pride(world, hero, damage)
    show_problem(world, elder)

    world.para()
    helper_arrives(world, helper)
    decide(world, hero, damage, material, tool, helper, rain)

    world.para()
    repair_attempt(world, hero, elder, damage, material, tool, helper)

    world.para()
    if world.get("road").meters["smooth"] >= THRESHOLD:
        held_ending(world, hero, elder, helper, damage)
    else:
        washed_ending(world, hero, elder, helper, damage, material, tool)

    world.facts["score"] = repair_score(material, tool, helper)
    world.facts["road_fixed"] = world.get("road").meters["smooth"] >= THRESHOLD
    world.facts["road_washed"] = world.get("road").meters["washed"] >= THRESHOLD
    return world


@dataclass
class StoryParams:
    damage: str
    material: str
    tool: str
    helper: str
    name: str
    gender: str
    elder: str
    trait: str
    rain: int = 1
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
    "road": [
        (
            "Why do roads need repair in spring?",
            "In spring, thawing water and rain can loosen dirt and stones. That makes cracks wider and weak places softer."
        )
    ],
    "crack": [
        (
            "What is a road crack?",
            "A road crack is a split in the surface. If water keeps getting into it, the split can grow."
        )
    ],
    "pothole": [
        (
            "What is a pothole?",
            "A pothole is a hole in a road where the surface has broken away. Wheels can bump hard into it or sink into it."
        )
    ],
    "washout": [
        (
            "What is a washout?",
            "A washout happens when moving water carries soil away. It can leave part of a road missing or unsafe."
        )
    ],
    "paper": [
        (
            "Can paper fix a road by itself?",
            "No. Paper is good for plans and notes, but it cannot hold up carts and rain. Real road repair needs strong material and careful work."
        )
    ],
    "clay": [
        (
            "Why might clay help with a small crack?",
            "Clay can be pressed into a narrow space and shaped neatly. But it is better for small repairs than for deep holes."
        )
    ],
    "gravel": [
        (
            "Why is gravel useful in road repair?",
            "Gravel fills empty space with many small hard pieces. When it is packed down, it helps make the road firm."
        )
    ],
    "stone": [
        (
            "Why are stones good for a deep road repair?",
            "Stones are strong and heavy, so they can support weight well. Big repairs often need that strength."
        )
    ],
    "tamper": [
        (
            "What does a tamper do?",
            "A tamper presses loose material down so it becomes tighter and firmer. Packing the ground helps a repair last longer."
        )
    ],
    "lever": [
        (
            "What is a lever used for in lifting stones?",
            "A lever helps move something heavy by giving your hands more force. Workers use it to nudge and place stones more safely."
        )
    ],
    "repair": [
        (
            "Why is packing a road patch important?",
            "A loose patch can wash away or sink. Packing it tightly helps it stay in place under feet, wheels, and rain."
        )
    ],
}
KNOWLEDGE_ORDER = ["road", "crack", "pothole", "washout", "paper", "clay", "gravel", "stone", "tamper", "lever", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    damage = f["damage"]
    material = f["material"]
    tool = f["tool"]
    helper = f["helper"]
    outcome = f["outcome"]
    ending = "holds against the spring rain" if outcome == "held" else "partly fails in the spring rain, teaching humility"
    return [
        (
            f'Write a short myth-like story set in road repair that includes the words '
            f'"spring," "paper," and "intellectual," and gives the child an inner monologue.'
        ),
        (
            f"Tell a transformation story where {hero.id} helps mend a {damage.label} in a village road "
            f"using {material.label} and a {tool.label}, while {helper.label} guides the work."
        ),
        (
            f"Write a child-facing myth about a clever child who begins by trusting paper plans too much, "
            f"then learns through road repair what truly makes a road strong, and the repair {ending}."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    damage = f["damage"]
    material = f["material"]
    tool = f["tool"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who wants to help mend the village road in spring. "
            f"The story also follows {helper.label} and {elder.id}, who guide the work."
        ),
        (
            "What was wrong with the road?",
            f"The road had {damage.phrase}. That made crossing harder and gave the village a real reason to repair it."
        ),
        (
            f"Why did {hero.id} carry paper?",
            f"{hero.id} had drawn a plan on paper from the schoolhouse. "
            f"The paper mattered because it showed {hero.pronoun('object')} beginning as a proud little intellectual who trusted thinking more than labor."
        ),
        (
            f"What did {hero.id} think before the repair?",
            f"{hero.pronoun('subject').capitalize()} first believed a clever plan might be enough. "
            f"Then {hero.pronoun('subject')} realized the road would only listen to a repair that matched real weight, tools, and spring weather."
        ),
        (
            f"How did they try to fix the road?",
            f"They used {material.label} and a {tool.label} while {helper.label} helped. "
            f"That mattered because the material filled the wound and the tool helped set it firmly."
        ),
    ]
    if outcome == "held":
        qa.append(
            (
                "How did the repair turn out?",
                f"It held. The bread cart crossed without dipping, which proved the road had truly changed."
            )
        )
        qa.append(
            (
                f"How did {hero.id} change by the end?",
                f"{hero.id} changed from a child proud of paper cleverness into someone who respected craft. "
                f"{hero.pronoun('subject').capitalize()} learned that wisdom joins thought to hands, tools, and the earth."
            )
        )
    else:
        qa.append(
            (
                "How did the repair turn out?",
                f"It partly washed loose in the spring water, so the road was not healed yet. "
                f"The failure showed that the repair was too weak for the road's wound and the rain."
            )
        )
        qa.append(
            (
                f"How did {hero.id} change by the end?",
                f"{hero.id} became humbler and more teachable. "
                f"Instead of boasting about being an intellectual, {hero.pronoun('subject')} came back ready to learn the road's own language."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"road", "paper", "repair"}
    damage = world.facts["damage"]
    material = world.facts["material"]
    tool = world.facts["tool"]
    helper = world.facts["helper"]
    tags |= set(damage.tags)
    tags |= set(material.tags)
    tags |= set(tool.tags)
    tags |= set(helper.tags)
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.traits:
            parts.append(f"traits={ent.traits}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(parts)}")
    facts = {k: v for k, v in world.facts.items() if k in {"rain", "target_score", "predicted_score", "predicted_target", "predicted_outcome", "score", "outcome"}}
    lines.append(f"  facts={facts}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        damage="crack",
        material="clay",
        tool="hands",
        helper="mason",
        name="Ila",
        gender="girl",
        elder="mother",
        trait="earnest",
        rain=0,
    ),
    StoryParams(
        damage="pothole",
        material="gravel",
        tool="tamper",
        helper="keeper",
        name="Tarin",
        gender="boy",
        elder="father",
        trait="bright",
        rain=1,
    ),
    StoryParams(
        damage="washout",
        material="cobbles",
        tool="tamper",
        helper="ox",
        name="Mira",
        gender="girl",
        elder="mother",
        trait="patient",
        rain=1,
    ),
    StoryParams(
        damage="pothole",
        material="cobbles",
        tool="lever",
        helper="keeper",
        name="Ivo",
        gender="boy",
        elder="father",
        trait="curious",
        rain=2,
    ),
    StoryParams(
        damage="crack",
        material="gravel",
        tool="tamper",
        helper="keeper",
        name="Luma",
        gender="girl",
        elder="mother",
        trait="quick-minded",
        rain=2,
    ),
]


ASP_RULES = r"""
usable_material(D,M) :- suited(M,D).
usable_tool(M,T) :- works_with(T,M).
valid(D,M,T) :- damage(D), material(M), tool(T), usable_material(D,M), usable_tool(M,T).

repair_score(S) :- chosen_material(M), strength(M,MS), chosen_tool(T), power(T,TP),
                   chosen_helper(H), bonus(H,HB), S = MS + TP + HB.
target(V) :- chosen_damage(D), severity(D,DS), rain(R), V = DS + R.

outcome(held) :- repair_score(S), target(V), S >= V.
outcome(washed) :- repair_score(S), target(V), S < V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for damage_id, damage in DAMAGES.items():
        lines.append(asp.fact("damage", damage_id))
        lines.append(asp.fact("severity", damage_id, damage.severity))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        lines.append(asp.fact("strength", material_id, material.strength))
        for damage_id in sorted(material.suited):
            lines.append(asp.fact("suited", material_id, damage_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("power", tool_id, tool.power))
        for material_id in sorted(tool.works_with):
            lines.append(asp.fact("works_with", tool_id, material_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("bonus", helper_id, helper.bonus))
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
        asp.fact("chosen_damage", params.damage),
        asp.fact("chosen_material", params.material),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_helper", params.helper),
        asp.fact("rain", params.rain),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a mythic child learns that road repair needs more than a clever paper plan."
    )
    ap.add_argument("--damage", choices=sorted(DAMAGES))
    ap.add_argument("--material", choices=sorted(MATERIALS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("--rain", type=int, choices=[0, 1, 2], help="how hard the spring water presses on the repair")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid repair triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.damage and args.material and args.tool and not valid_combo(args.damage, args.material, args.tool):
        raise StoryError(explain_rejection(args.damage, args.material, args.tool))
    if args.helper and args.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{args.helper}'.)")

    combos = [
        combo for combo in valid_combos()
        if (args.damage is None or combo[0] == args.damage)
        and (args.material is None or combo[1] == args.material)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    damage_id, material_id, tool_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    elder = args.elder or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    rain = args.rain if args.rain is not None else rng.choice([0, 1, 2])

    return StoryParams(
        damage=damage_id,
        material=material_id,
        tool=tool_id,
        helper=helper_id,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
        rain=rain,
    )


def generate(params: StoryParams) -> StorySample:
    if params.damage not in DAMAGES:
        raise StoryError(f"(No story: unknown damage '{params.damage}'.)")
    if params.material not in MATERIALS:
        raise StoryError(f"(No story: unknown material '{params.material}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(No story: unknown tool '{params.tool}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown gender '{params.gender}'.)")
    if params.elder not in {"mother", "father"}:
        raise StoryError(f"(No story: unknown elder '{params.elder}'.)")
    if params.rain not in {0, 1, 2}:
        raise StoryError("(No story: rain must be 0, 1, or 2.)")
    if not valid_combo(params.damage, params.material, params.tool):
        raise StoryError(explain_rejection(params.damage, params.material, params.tool))

    world = tell(
        damage=DAMAGES[params.damage],
        material=MATERIALS[params.material],
        tool=TOOLS[params.tool],
        helper=HELPERS[params.helper],
        hero_name=params.name,
        hero_gender=params.gender,
        elder_type=params.elder,
        trait=params.trait,
        rain=params.rain,
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

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos() matches ASP ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid repair combinations:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for p in cases:
        py = outcome_for_ids(p.damage, p.material, p.tool, p.helper, p.rain)
        cl = asp_outcome(p)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches ASP on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} scenario outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(7))
        smoke_sample = generate(smoke_params)
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(smoke_sample, trace=False, qa=True, header="")
        if not smoke_sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke-tested normal generate()/emit() path.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (damage, material, tool) repair triples:\n")
        for damage_id, material_id, tool_id in combos:
            print(f"  {damage_id:8} {material_id:12} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            outcome = outcome_for_ids(p.damage, p.material, p.tool, p.helper, p.rain)
            header = (
                f"### {p.name}: {p.damage} with {p.material}/{p.tool} "
                f"and {p.helper} (rain={p.rain}, {outcome})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
