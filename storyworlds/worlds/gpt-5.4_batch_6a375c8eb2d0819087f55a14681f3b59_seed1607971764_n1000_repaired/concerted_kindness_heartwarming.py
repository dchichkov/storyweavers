#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/concerted_kindness_heartwarming.py
=============================================================

A standalone story world about a child whose costume tears just before a small
show, and friends answer with concerted kindness. The world model tracks a real
physical problem -- what kind of costume was damaged, how badly, what repair
tools are available in the setting, and whether the chosen repair is actually
strong enough in time -- along with emotional state such as worry, hope,
gratitude, and belonging.

The stories aim for a Heartwarming tone: a clear setup, a concrete turn, and an
ending image that proves kindness changed something in the world.

Run it
------
    python storyworlds/worlds/gpt-5.4/concerted_kindness_heartwarming.py
    python storyworlds/worlds/gpt-5.4/concerted_kindness_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/concerted_kindness_heartwarming.py --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/concerted_kindness_heartwarming.py --setting classroom --costume paper_crown
    python storyworlds/worlds/gpt-5.4/concerted_kindness_heartwarming.py --repair hold_it_together
    python storyworlds/worlds/gpt-5.4/concerted_kindness_heartwarming.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    event: str
    stage_name: str
    supply_spot: str
    available_repairs: set[str] = field(default_factory=set)
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
class Costume:
    id: str
    label: str
    phrase: str
    material: str
    part: str
    role_name: str
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
class Damage:
    id: str
    label: str
    text: str
    severity: int
    applies_to: set[str] = field(default_factory=set)
    effect: str = ""
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
    sense: int
    power: int
    materials: set[str] = field(default_factory=set)
    gather: str = ""
    action: str = ""
    qa_text: str = ""
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
        clone.facts = dict(self.facts)
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


def _r_damage_feelings(world: World) -> list[str]:
    costume = world.entities.get("costume")
    child = world.entities.get("child")
    if not costume or not child:
        return []
    if costume.meters["damaged"] < THRESHOLD:
        return []
    sig = ("damage_feelings", costume.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["embarrassment"] += 1
    child.memes["confidence"] = max(0.0, child.memes["confidence"] - 1)
    return ["__damage__"]


def _r_comfort_to_hope(world: World) -> list[str]:
    child = world.entities.get("child")
    if not child or child.memes["worry"] < THRESHOLD:
        return []
    total = 0
    for ent in list(world.entities.values()):
        if ent.role == "helper" and ent.memes["comforting"] >= THRESHOLD:
            total += 1
    if total == 0:
        return []
    sig = ("comfort_to_hope", total)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["hope"] += 1
    return []


def _r_repair_restores(world: World) -> list[str]:
    costume = world.entities.get("costume")
    child = world.entities.get("child")
    if not costume or not child:
        return []
    if costume.meters["repaired"] < THRESHOLD:
        return []
    sig = ("repair_restores", costume.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    costume.meters["wearable"] += 1
    child.memes["worry"] = 0.0
    child.memes["embarrassment"] = 0.0
    child.memes["joy"] += 1
    child.memes["gratitude"] += 1
    child.memes["belonging"] += 1
    child.memes["confidence"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="damage_feelings", tag="emotional", apply=_r_damage_feelings),
    Rule(name="comfort_to_hope", tag="emotional", apply=_r_comfort_to_hope),
    Rule(name="repair_restores", tag="emotional", apply=_r_repair_restores),
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
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def damage_applies(costume: Costume, damage: Damage) -> bool:
    return costume.material in damage.applies_to


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def compatible_repairs(setting: Setting, costume: Costume, damage: Damage) -> list[Repair]:
    out: list[Repair] = []
    if not damage_applies(costume, damage):
        return out
    for rid in sorted(setting.available_repairs):
        repair = REPAIRS[rid]
        if repair.sense < SENSE_MIN:
            continue
        if costume.material in repair.materials:
            out.append(repair)
    return out


def repair_severity(damage: Damage, delay: int) -> int:
    return damage.severity + delay


def repair_holds(repair: Repair, damage: Damage, delay: int) -> bool:
    return repair.power >= repair_severity(damage, delay)


def predict_show_outcome(world: World, damage: Damage, repair: Repair, delay: int) -> dict:
    sim = world.copy()
    costume = sim.get("costume")
    costume.meters["damaged"] += 1
    costume.meters["severity"] = float(repair_severity(damage, delay))
    propagate(sim, narrate=False)
    fixed = repair_holds(repair, damage, delay)
    if fixed:
        costume.meters["repaired"] += 1
        propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "fixed": fixed,
        "worry": child.memes["worry"],
        "wearable": costume.meters["wearable"] >= THRESHOLD,
    }


def opening_scene(world: World, child: Entity, helper1: Entity, helper2: Entity,
                  teacher: Entity, costume: Costume) -> None:
    world.say(
        f"At {world.setting.place}, the little children were getting ready for {world.setting.event}. "
        f"{child.id} wore {costume.phrase} and kept smoothing {child.pronoun('possessive')} {costume.part} with a proud smile."
    )
    world.say(
        f'"You look ready already," said {helper1.id}, while {helper2.id} gave a happy nod. '
        f'Even {teacher.label_word} smiled when {child.id} twirled in a tiny circle.'
    )


def hopes_to_perform(world: World, child: Entity, costume: Costume) -> None:
    child.memes["anticipation"] += 1
    child.memes["confidence"] += 1
    world.say(
        f"{child.id} had practiced all week and wanted to step onto {world.setting.stage_name} feeling brave. "
        f"The {costume.part} made {child.pronoun('object')} feel exactly like {costume.role_name}."
    )


def accident(world: World, child: Entity, costume_ent: Entity, damage: Damage, costume: Costume) -> None:
    costume_ent.meters["damaged"] += 1
    costume_ent.meters["severity"] = float(damage.severity)
    propagate(world, narrate=False)
    world.say(
        f"But just as the children lined up, {damage.text}."
    )
    world.say(
        f"{child.id} looked down at {child.pronoun('possessive')} {costume.part} and went still. "
        f'"Oh no," {child.pronoun()} whispered. "{damage.effect}"'
    )


def comfort(world: World, child: Entity, helper1: Entity, helper2: Entity, teacher: Entity,
            damage: Damage, repair: Repair, delay: int) -> None:
    helper1.memes["comforting"] += 1
    helper2.memes["comforting"] += 1
    teacher.memes["comforting"] += 1
    pred = predict_show_outcome(world, damage, repair, delay)
    world.facts["predicted_fixed"] = pred["fixed"]
    world.facts["predicted_worry"] = pred["worry"]
    propagate(world, narrate=False)
    world.say(
        f"{helper1.id} touched {child.id}'s sleeve, and {helper2.id} moved close on the other side. "
        f'"We are not leaving you alone with this," {helper1.id} said.'
    )
    if pred["fixed"]:
        world.say(
            f'{teacher.label_word.capitalize()} knelt beside them. "We still have a moment," {teacher.pronoun()} said gently. '
            f'"If everyone helps, we can mend it."'
        )
    else:
        world.say(
            f'{teacher.label_word.capitalize()} knelt beside them. "We will help no matter what," {teacher.pronoun()} said gently. '
            f'"If the costume cannot be ready in time, we will still make sure you belong in the show."'
        )


def gather_repair(world: World, helper1: Entity, helper2: Entity, teacher: Entity,
                  repair: Repair) -> None:
    helper1.meters["help_steps"] += 1
    helper2.meters["help_steps"] += 1
    teacher.meters["help_steps"] += 1
    world.say(
        f"Then the room burst into concerted kindness. {helper1.id} {repair.gather}, "
        f"{helper2.id} held the costume steady, and {teacher.label_word} kept calm hands and a calm voice."
    )


def mend_success(world: World, child: Entity, costume_ent: Entity, repair: Repair,
                 costume: Costume, damage: Damage, delay: int) -> None:
    costume_ent.meters["repaired"] += 1
    costume_ent.meters["severity"] = float(repair_severity(damage, delay))
    propagate(world, narrate=False)
    world.say(
        f"Together they {repair.action}. The {costume.part} stopped slipping, and the hurt place looked neat again."
    )
    world.say(
        f"{child.id} took one careful breath, then another. Hope returned to {child.pronoun('possessive')} face before the music even began."
    )


def perform(world: World, child: Entity, helper1: Entity, helper2: Entity,
            costume: Costume) -> None:
    child.meters["performed"] += 1
    helper1.meters["performed"] += 1
    helper2.meters["performed"] += 1
    child.memes["joy"] += 1
    child.memes["belonging"] += 1
    world.say(
        f"When the curtain opened, {child.id} stepped onto {world.setting.stage_name} with {helper1.id} and {helper2.id}. "
        f"The lights touched {costume.phrase}, and this time {child.pronoun()} stood tall."
    )
    world.say(
        f"After the last bow, {child.id} squeezed both friends' hands. The show was lovely, but the warmest part was knowing kindness had carried {child.pronoun('object')} there."
    )


def mend_fail(world: World, child: Entity, repair: Repair, costume: Costume,
              damage: Damage, delay: int) -> None:
    world.say(
        f"They tried to help, and {repair.action}, but the {costume.part} would not stay safe enough before the music started."
    )
    world.say(
        f"{child.id}'s eyes filled with tears again when {child.pronoun()} saw the line still pulling open. "
        f"The damage was simply bigger than that quick fix."
    )


def comforted_role(world: World, child: Entity, helper1: Entity, helper2: Entity, teacher: Entity) -> None:
    child.memes["gratitude"] += 1
    child.memes["belonging"] += 1
    child.memes["worry"] = 0.0
    helper1.memes["kindness"] += 1
    helper2.memes["kindness"] += 1
    teacher.memes["kindness"] += 1
    child.meters["participated"] += 1
    world.say(
        f'But {teacher.label_word} was ready with another place for {child.id}. "{child.id} can ring the silver bell for the opening and stand with us for the final bow," {teacher.pronoun()} said.'
    )
    world.say(
        f"{helper1.id} and {helper2.id} made space at once, one on each side. "
        f"When the children walked out, {child.id} rang the bell with a small bright sound, and everyone smiled as if that had always been the plan."
    )
    world.say(
        f"At the end, the three children bowed together, shoulder to shoulder. The costume was not perfect, but the kindness around {child.id} was."
    )


def thank_you(world: World, child: Entity, helper1: Entity, helper2: Entity, teacher: Entity) -> None:
    world.say(
        f'Later, {child.id} whispered, "Thank you for helping me." '
        f'{helper2.id} smiled and answered, "That is what friends are for."'
    )
    world.say(
        f"{teacher.label_word.capitalize()} tucked the mended costume carefully onto a chair, and the whole room felt softer and brighter than before."
    )


def tell(setting: Setting, costume: Costume, damage: Damage, repair: Repair,
         child_name: str = "Lila", child_gender: str = "girl",
         helper1_name: str = "Milo", helper1_gender: str = "boy",
         helper2_name: str = "Nina", helper2_gender: str = "girl",
         teacher_type: str = "teacher", trait: str = "gentle",
         delay: int = 0) -> World:
    world = World(setting)

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        attrs={"trait": trait},
    ))
    helper1 = world.add(Entity(
        id=helper1_name,
        kind="character",
        type=helper1_gender,
        role="helper",
        traits=["helpful"],
        attrs={"friend_of": child_name},
    ))
    helper2 = world.add(Entity(
        id=helper2_name,
        kind="character",
        type=helper2_gender,
        role="helper",
        traits=["helpful"],
        attrs={"friend_of": child_name},
    ))
    teacher = world.add(Entity(
        id="Teacher",
        kind="character",
        type=teacher_type,
        role="teacher",
        label="the teacher",
        traits=["calm"],
        attrs={"group": "class"},
    ))
    costume_ent = world.add(Entity(
        id="costume",
        kind="thing",
        type="costume",
        label=costume.label,
        attrs={"material": costume.material, "part": costume.part},
    ))

    child.memes["anticipation"] = 0.0
    child.memes["confidence"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["hope"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["gratitude"] = 0.0
    child.memes["belonging"] = 0.0
    child.memes["embarrassment"] = 0.0

    opening_scene(world, child, helper1, helper2, teacher, costume)
    hopes_to_perform(world, child, costume)

    world.para()
    accident(world, child, costume_ent, damage, costume)
    comfort(world, child, helper1, helper2, teacher, damage, repair, delay)
    gather_repair(world, helper1, helper2, teacher, repair)

    fixed = repair_holds(repair, damage, delay)
    world.para()
    if fixed:
        mend_success(world, child, costume_ent, repair, costume, damage, delay)
        perform(world, child, helper1, helper2, costume)
        world.para()
        thank_you(world, child, helper1, helper2, teacher)
        outcome = "repaired"
    else:
        mend_fail(world, child, repair, costume, damage, delay)
        comforted_role(world, child, helper1, helper2, teacher)
        world.para()
        thank_you(world, child, helper1, helper2, teacher)
        outcome = "comforted"

    world.facts.update(
        child=child,
        helper1=helper1,
        helper2=helper2,
        teacher=teacher,
        costume=costume_ent,
        costume_cfg=costume,
        damage=damage,
        repair=repair,
        setting=setting,
        outcome=outcome,
        fixed=fixed,
        severity=repair_severity(damage, delay),
        delay=delay,
    )
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the sunny classroom",
        event="the spring play",
        stage_name="the little rug stage",
        supply_spot="the art shelf",
        available_repairs={"clear_tape", "glue_patch", "ribbon_knot"},
        tags={"classroom", "school"},
    ),
    "hall": Setting(
        id="hall",
        place="the neighborhood hall",
        event="the kindness concert",
        stage_name="the low wooden stage",
        supply_spot="the folding craft table",
        available_repairs={"clear_tape", "glue_patch", "safety_pins", "ribbon_knot"},
        tags={"hall", "concert"},
    ),
    "library": Setting(
        id="library",
        place="the library story room",
        event="the costume parade",
        stage_name="the story corner",
        supply_spot="the helper basket by the desk",
        available_repairs={"clear_tape", "glue_patch"},
        tags={"library", "books"},
    ),
}

COSTUMES = {
    "paper_crown": Costume(
        id="paper_crown",
        label="paper crown",
        phrase="a gold paper crown with shiny stars",
        material="paper",
        part="crown",
        role_name="a tiny king or queen",
        tags={"paper", "costume"},
    ),
    "felt_cape": Costume(
        id="felt_cape",
        label="felt cape",
        phrase="a red felt cape with a silver moon",
        material="fabric",
        part="cape",
        role_name="a brave night-sky hero",
        tags={"fabric", "costume"},
    ),
    "ribbon_tail": Costume(
        id="ribbon_tail",
        label="ribbon tail",
        phrase="a blue ribbon tail tied with two soft bows",
        material="ribbon",
        part="tail",
        role_name="a dancing kite",
        tags={"ribbon", "costume"},
    ),
    "star_headband": Costume(
        id="star_headband",
        label="star headband",
        phrase="a star headband made from card and glitter",
        material="craft",
        part="headband",
        role_name="a sparkling evening star",
        tags={"craft", "costume"},
    ),
}

DAMAGES = {
    "small_tear": Damage(
        id="small_tear",
        label="small tear",
        text="the costume caught on a chair corner and made a small tear",
        severity=1,
        applies_to={"paper", "fabric", "craft"},
        effect="It tore",
        tags={"tear"},
    ),
    "loose_bow": Damage(
        id="loose_bow",
        label="loose bow",
        text="one quick turn made the bow slip loose and trail down",
        severity=1,
        applies_to={"ribbon", "fabric"},
        effect="It is coming untied",
        tags={"bow"},
    ),
    "split_seam": Damage(
        id="split_seam",
        label="split seam",
        text="a bigger tug opened a long split along one side",
        severity=2,
        applies_to={"fabric"},
        effect="It might fall right off",
        tags={"seam"},
    ),
    "crushed_star": Damage(
        id="crushed_star",
        label="crushed star",
        text="someone bumped past, and the front star bent and partly peeled away",
        severity=1,
        applies_to={"paper", "craft"},
        effect="The front is coming apart",
        tags={"craft"},
    ),
}

REPAIRS = {
    "clear_tape": Repair(
        id="clear_tape",
        label="clear tape",
        sense=3,
        power=1,
        materials={"paper", "craft"},
        gather="ran to fetch clear tape from the supply spot",
        action="smoothed the edges flat and pressed on careful strips of tape",
        qa_text="smoothed the torn part and fixed it with clear tape",
        tags={"tape", "repair"},
    ),
    "glue_patch": Repair(
        id="glue_patch",
        label="glue and patch paper",
        sense=3,
        power=2,
        materials={"paper", "fabric", "craft"},
        gather="brought glue and a little patch from the supply spot",
        action="added a patch behind the weak place and held it until it settled",
        qa_text="used glue and a small patch to strengthen the broken place",
        tags={"glue", "repair"},
    ),
    "safety_pins": Repair(
        id="safety_pins",
        label="safety pins",
        sense=3,
        power=2,
        materials={"fabric", "ribbon"},
        gather="found a little box of safety pins at the supply spot",
        action="closed the open edge with neat safety pins that stayed hidden under the fold",
        qa_text="used safety pins to hold the fabric safely together",
        tags={"pins", "repair"},
    ),
    "ribbon_knot": Repair(
        id="ribbon_knot",
        label="fresh ribbon knot",
        sense=2,
        power=1,
        materials={"ribbon", "fabric"},
        gather="picked up a spare ribbon from the supply spot",
        action="retied the loose part with a fresh, firm bow",
        qa_text="retied the loose ribbon with a fresh bow",
        tags={"ribbon", "repair"},
    ),
    "hold_it_together": Repair(
        id="hold_it_together",
        label="just hold it by hand",
        sense=1,
        power=0,
        materials={"paper", "fabric", "ribbon", "craft"},
        gather="offered to hold the costume with one hand",
        action="tried to keep the broken part in place with fingers alone",
        qa_text="tried to hold the broken part with a hand",
        tags={"weak_fix"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for cid, costume in COSTUMES.items():
            for did, damage in DAMAGES.items():
                if compatible_repairs(setting, costume, damage):
                    combos.append((sid, cid, did))
    return combos


@dataclass
class StoryParams:
    setting: str
    costume: str
    damage: str
    repair: str
    child_name: str
    child_gender: str
    helper1_name: str
    helper1_gender: str
    helper2_name: str
    helper2_gender: str
    teacher: str = "teacher"
    trait: str = "gentle"
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
    "tape": [(
        "What does clear tape do?",
        "Clear tape sticks light pieces together and helps small paper tears stay closed. It works best on light materials, not on every big rip."
    )],
    "glue": [(
        "What does glue do?",
        "Glue helps two pieces stay attached when it dries. If you add a small patch behind the weak place, the fix can be stronger."
    )],
    "pins": [(
        "What is a safety pin?",
        "A safety pin is a small pin with a cover that helps keep fabric together. A grown-up should handle it carefully."
    )],
    "ribbon": [(
        "Why can a ribbon bow come loose?",
        "A ribbon can slip if it was tied softly or pulled during play. A firmer knot helps it stay in place."
    )],
    "repair": [(
        "Why is it good to fix something together?",
        "Fixing something together lets each person do one helpful part. Teamwork can turn a big problem into a smaller one."
    )],
    "costume": [(
        "What is a costume?",
        "A costume is clothing or a special piece people wear to look like a character. It helps make a pretend story feel real."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness means noticing when someone needs help and choosing to be gentle and helpful. Small caring actions can make a worried person feel safe again."
    )],
    "concert": [(
        "What is a concert?",
        "A concert is a time when people perform music or songs for others. Sometimes children sing, move, or play small instruments together."
    )],
}
KNOWLEDGE_ORDER = ["kindness", "costume", "repair", "tape", "glue", "pins", "ribbon", "concert"]

GIRL_NAMES = ["Lila", "Nora", "Mia", "Ava", "Tessa", "Ruby", "Elsie", "June"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Leo", "Sam", "Owen", "Finn", "Jack"]
TRAITS = ["gentle", "hopeful", "careful", "shy", "bright", "soft-hearted"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    costume = f["costume_cfg"]
    setting = f["setting"]
    damage = f["damage"]
    outcome = f["outcome"]
    if outcome == "repaired":
        return [
            f'Write a heartwarming story for a 3-to-5-year-old that includes the word "concerted" and shows friends fixing a broken costume with kindness.',
            f"Tell a gentle story set in {setting.place} where {child.id}'s {costume.part} is damaged before {setting.event}, and friends work together so {child.pronoun()} can still join in.",
            f"Write a simple story where a child feels worried after {damage.label} ruins a costume, but calm helpers mend the problem and help the child feel brave again.",
        ]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "concerted" and shows kindness around a child whose costume cannot be fixed in time.',
        f"Tell a gentle story set in {setting.place} where {child.id}'s {costume.part} is damaged before {setting.event}, and friends make sure {child.pronoun()} still belongs even without the costume being fully repaired.",
        f"Write a simple story where teamwork does not make everything perfect, but it does keep a worried child from feeling left out.",
    ]


def pair_words(h1: Entity, h2: Entity) -> str:
    if h1.type == "girl" and h2.type == "girl":
        return "two friends"
    if h1.type == "boy" and h2.type == "boy":
        return "two friends"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper1 = f["helper1"]
    helper2 = f["helper2"]
    teacher = f["teacher"]
    costume = f["costume_cfg"]
    damage = f["damage"]
    repair = f["repair"]
    setting = f["setting"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {pair_words(helper1, helper2)} named {helper1.id} and {helper2.id}, and their {teacher.label_word}. They were getting ready for {setting.event} when the problem began."
        ),
        (
            f"What went wrong with {child.id}'s costume?",
            f"{damage.text.capitalize()}, so {child.id}'s {costume.part} was not ready anymore. That sudden damage made {child.pronoun('object')} worry about going on stage."
        ),
        (
            f"How did the others show kindness to {child.id}?",
            f"{helper1.id}, {helper2.id}, and the {teacher.label_word} stayed close instead of leaving {child.pronoun('object')} alone with the problem. Their concerted kindness gave {child.id} hope before the repair was even finished."
        ),
    ]
    if outcome == "repaired":
        qa.append((
            "How did they fix the costume?",
            f"They {repair.qa_text}. Because that repair matched the costume and was strong enough in time, {child.id} could wear it safely for the show."
        ))
        qa.append((
            f"Why could {child.id} go on stage after all?",
            f"The repair held, so the costume became wearable again. Once the physical problem was solved, {child.id}'s worry faded and {child.pronoun()} felt brave enough to perform."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with {child.id} stepping onto {setting.stage_name} and bowing beside friends. The final image shows that kindness did not just mend a costume; it helped mend a frightened heart."
        ))
    else:
        qa.append((
            "Did the repair work in time?",
            f"No. They tried to help, but the damage was bigger than that quick fix, so the costume was still not safe enough when the music started."
        ))
        qa.append((
            f"How was {child.id} included anyway?",
            f"The {teacher.label_word} gave {child.id} a bell to ring and a place in the final bow. That way, {child.pronoun()} still belonged in the performance even without a perfect costume."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the children bowing together, shoulder to shoulder. The costume was not perfect, but the kindness around {child.id} was, and that is what changed the room."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"kindness", "costume", "repair"} | set(f["repair"].tags)
    if "concert" in f["setting"].tags:
        tags.add("concert")
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="classroom",
        costume="paper_crown",
        damage="small_tear",
        repair="clear_tape",
        child_name="Lila",
        child_gender="girl",
        helper1_name="Milo",
        helper1_gender="boy",
        helper2_name="Nora",
        helper2_gender="girl",
        teacher="teacher",
        trait="gentle",
        delay=0,
    ),
    StoryParams(
        setting="hall",
        costume="felt_cape",
        damage="split_seam",
        repair="safety_pins",
        child_name="Theo",
        child_gender="boy",
        helper1_name="Ruby",
        helper1_gender="girl",
        helper2_name="Ben",
        helper2_gender="boy",
        teacher="teacher",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        setting="classroom",
        costume="felt_cape",
        damage="split_seam",
        repair="glue_patch",
        child_name="Ava",
        child_gender="girl",
        helper1_name="Leo",
        helper1_gender="boy",
        helper2_name="June",
        helper2_gender="girl",
        teacher="teacher",
        trait="shy",
        delay=1,
    ),
    StoryParams(
        setting="hall",
        costume="ribbon_tail",
        damage="loose_bow",
        repair="ribbon_knot",
        child_name="Finn",
        child_gender="boy",
        helper1_name="Mia",
        helper1_gender="girl",
        helper2_name="Sam",
        helper2_gender="boy",
        teacher="teacher",
        trait="hopeful",
        delay=0,
    ),
    StoryParams(
        setting="library",
        costume="star_headband",
        damage="crushed_star",
        repair="clear_tape",
        child_name="Ruby",
        child_gender="girl",
        helper1_name="Jack",
        helper1_gender="boy",
        helper2_name="Elsie",
        helper2_gender="girl",
        teacher="teacher",
        trait="soft-hearted",
        delay=0,
    ),
]


def explain_rejection(costume: Costume, damage: Damage, setting: Optional[Setting] = None) -> str:
    if not damage_applies(costume, damage):
        return (
            f"(No story: {damage.label} does not fit a {costume.label}. "
            f"That kind of damage does not naturally happen to {costume.material} costume material here.)"
        )
    if setting is not None and not compatible_repairs(setting, costume, damage):
        return (
            f"(No story: in {setting.place}, there is no sensible repair on hand for a "
            f"{costume.label} with {damage.label}. Pick a different setting, damage, or costume.)"
        )
    return "(No story: this combination has no sensible repair path.)"


def explain_repair(repair_id: str) -> str:
    repair = REPAIRS[repair_id]
    return (
        f"(Refusing repair '{repair_id}': it scores too low on common sense "
        f"(sense={repair.sense} < {SENSE_MIN}). Pick a sturdier, more believable repair.)"
    )


def outcome_of(params: StoryParams) -> str:
    repair = REPAIRS[params.repair]
    damage = DAMAGES[params.damage]
    return "repaired" if repair_holds(repair, damage, params.delay) else "comforted"


ASP_RULES = r"""
applies(C, D) :- material(C, M), damage_material(D, M).
sensible(R) :- repair(R), sense(R, S), sense_min(M), S >= M.
compatible_repair(S, C, D, R) :- available(S, R), sensible(R), applies(C, D),
                                 material(C, M), repair_material(R, M).
valid(S, C, D) :- setting(S), costume(C), damage(D), compatible_repair(S, C, D, _).

severity(V + Dly) :- chosen_damage(D), damage_severity(D, V), delay(Dly).
repair_power(P) :- chosen_repair(R), power(R, P).

outcome(repaired) :- repair_power(P), severity(S), P >= S.
outcome(comforted) :- repair_power(P), severity(S), P < S.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for rid in sorted(setting.available_repairs):
            lines.append(asp.fact("available", sid, rid))
    for cid, costume in COSTUMES.items():
        lines.append(asp.fact("costume", cid))
        lines.append(asp.fact("material", cid, costume.material))
    for did, damage in DAMAGES.items():
        lines.append(asp.fact("damage", did))
        lines.append(asp.fact("damage_severity", did, damage.severity))
        for mat in sorted(damage.applies_to):
            lines.append(asp.fact("damage_material", did, mat))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("power", rid, repair.power))
        for mat in sorted(repair.materials):
            lines.append(asp.fact("repair_material", rid, mat))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_damage", params.damage),
        asp.fact("chosen_repair", params.repair),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {r.id for r in sensible_repairs()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible repairs match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke test")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: concerted kindness helps fix a broken costume before a little show."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--damage", choices=DAMAGES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher", choices=["teacher"], default=None)
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra time pressure before the show starts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible setting/costume/damage combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.costume and args.damage:
        costume = COSTUMES[args.costume]
        damage = DAMAGES[args.damage]
        if not damage_applies(costume, damage):
            raise StoryError(explain_rejection(costume, damage))

    if args.setting and args.costume and args.damage:
        setting = SETTINGS[args.setting]
        costume = COSTUMES[args.costume]
        damage = DAMAGES[args.damage]
        if not compatible_repairs(setting, costume, damage):
            raise StoryError(explain_rejection(costume, damage, setting))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.costume is None or combo[1] == args.costume)
        and (args.damage is None or combo[2] == args.damage)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, costume_id, damage_id = rng.choice(sorted(combos))
    setting = SETTINGS[setting_id]
    costume = COSTUMES[costume_id]
    damage = DAMAGES[damage_id]

    allowed_repairs = compatible_repairs(setting, costume, damage)
    if args.repair:
        if args.repair not in REPAIRS:
            raise StoryError(f"(Unknown repair '{args.repair}'.)")
        repair = REPAIRS[args.repair]
        if repair.sense < SENSE_MIN:
            raise StoryError(explain_repair(args.repair))
        if repair.id not in {r.id for r in allowed_repairs}:
            raise StoryError(
                f"(No story: {repair.label} is not a sensible available repair for "
                f"{costume.label} with {damage.label} in {setting.place}.)"
            )
    else:
        repair = rng.choice(allowed_repairs)

    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender, set())
    helper1_gender = rng.choice(["girl", "boy"])
    helper1_name = _pick_name(rng, helper1_gender, {child_name})
    helper2_gender = rng.choice(["girl", "boy"])
    helper2_name = _pick_name(rng, helper2_gender, {child_name, helper1_name})
    teacher = args.teacher or "teacher"
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])

    return StoryParams(
        setting=setting_id,
        costume=costume_id,
        damage=damage_id,
        repair=repair.id,
        child_name=child_name,
        child_gender=child_gender,
        helper1_name=helper1_name,
        helper1_gender=helper1_gender,
        helper2_name=helper2_name,
        helper2_gender=helper2_gender,
        teacher=teacher,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting '{params.setting}'.)")
    if params.costume not in COSTUMES:
        raise StoryError(f"(Unknown costume '{params.costume}'.)")
    if params.damage not in DAMAGES:
        raise StoryError(f"(Unknown damage '{params.damage}'.)")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair '{params.repair}'.)")

    setting = SETTINGS[params.setting]
    costume = COSTUMES[params.costume]
    damage = DAMAGES[params.damage]
    repair = REPAIRS[params.repair]

    if repair.sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))
    if not damage_applies(costume, damage):
        raise StoryError(explain_rejection(costume, damage))
    if repair.id not in {r.id for r in compatible_repairs(setting, costume, damage)}:
        raise StoryError(
            f"(No story: {repair.label} is not a sensible available repair for "
            f"{costume.label} with {damage.label} in {setting.place}.)"
        )

    world = tell(
        setting=setting,
        costume=costume,
        damage=damage,
        repair=repair,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper1_name=params.helper1_name,
        helper1_gender=params.helper1_gender,
        helper2_name=params.helper2_name,
        helper2_gender=params.helper2_gender,
        teacher_type=params.teacher,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sens = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible repairs: {', '.join(sens)}\n")
        print(f"{len(combos)} compatible (setting, costume, damage) combos:\n")
        for setting, costume, damage in combos:
            print(f"  {setting:10} {costume:13} {damage}")
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
            header = (
                f"### {p.child_name}: {p.costume} / {p.damage} at {p.setting} "
                f"({p.repair}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
