#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/descriptive_scratch_subtract_transformation_space_adventure.py
=========================================================================================

A standalone story world about two children turning a cardboard box into a
spaceship, then facing a small making-and-mending problem. One child wants to
scratch away a mark from an important ship part. The other child warns that
scratching will damage it. A grown-up helps them solve the problem by using a
safer method and transforming the pretend ship into something better.

The seed asks for these words and instruments:
- descriptive
- scratch
- subtract
- Transformation
- Space Adventure style

This world models a tiny causal domain:
- a pretend spaceship has one important part (visor / control panel / star map)
- an unwanted mark or extra thing blocks the mission
- an impatient child may try to scratch it away with a coin
- scratching damages the part and blocks the mission
- a safer repair can restore or replace the part
- the ending image proves a transformation: the plain box becomes a brighter,
  better spaceship, and the children learn a new way to fix mistakes

Run it
------
python storyworlds/worlds/gpt-5.4/descriptive_scratch_subtract_transformation_space_adventure.py
python storyworlds/worlds/gpt-5.4/descriptive_scratch_subtract_transformation_space_adventure.py --mission comet --mark stickers --target panel
python storyworlds/worlds/gpt-5.4/descriptive_scratch_subtract_transformation_space_adventure.py --target stone
python storyworlds/worlds/gpt-5.4/descriptive_scratch_subtract_transformation_space_adventure.py --repair rub_harder
python storyworlds/worlds/gpt-5.4/descriptive_scratch_subtract_transformation_space_adventure.py --all
python storyworlds/worlds/gpt-5.4/descriptive_scratch_subtract_transformation_space_adventure.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/descriptive_scratch_subtract_transformation_space_adventure.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "patient", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    scratchable: bool = False
    important: bool = False
    transparent: bool = False
    surface: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Mission:
    id: str
    scene: str
    rig: str
    captain: str
    partner: str
    goal: str
    obstacle: str
    launch_line: str
    sendoff: str
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


@dataclass
class Mark:
    id: str
    label: str
    phrase: str
    action: str
    problem_line: str
    safe_repairs: set[str] = field(default_factory=set)
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
class Target:
    id: str
    label: str
    the: str
    phrase: str
    place: str
    job: str
    surface: str
    fragility: int
    scratchable: bool = True
    important: bool = True
    transparent: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
    sense: int
    power: int
    works_on_marks: set[str] = field(default_factory=set)
    works_on_surfaces: set[str] = field(default_factory=set)
    text: str = ""
    fail: str = ""
    qa_text: str = ""
    transform_text: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_damage_blocks(world: World) -> list[str]:
    out: list[str] = []
    target = world.entities.get("target")
    ship = world.entities.get("ship")
    if not target or not ship:
        return out
    if target.meters["scratched"] >= THRESHOLD and target.important:
        sig = ("blocked", target.id)
        if sig not in world.fired:
            world.fired.add(sig)
            ship.meters["blocked"] += 1
            for kid in world.kids():
                kid.memes["worry"] += 1
            out.append("__blocked__")
    return out


def _r_mark_blocks(world: World) -> list[str]:
    out: list[str] = []
    target = world.entities.get("target")
    ship = world.entities.get("ship")
    if not target or not ship:
        return out
    if target.meters["obscured"] >= THRESHOLD and target.important:
        sig = ("obscured", target.id)
        if sig not in world.fired:
            world.fired.add(sig)
            ship.meters["needs_fix"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="damage_blocks", tag="physical", apply=_r_damage_blocks),
    Rule(name="mark_blocks", tag="physical", apply=_r_mark_blocks),
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


def repair_matches(repair: Repair, mark: Mark, target: Target) -> bool:
    mark_ok = mark.id in repair.works_on_marks or "*" in repair.works_on_marks
    surface_ok = target.surface in repair.works_on_surfaces or "*" in repair.works_on_surfaces
    return mark_ok and surface_ok


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def repair_severity(target: Target, delay: int) -> int:
    return target.fragility + delay


def repair_succeeds(repair: Repair, mark: Mark, target: Target, delay: int) -> bool:
    if not repair_matches(repair, mark, target):
        return False
    return repair.power >= repair_severity(target, delay)


def hazard_at_risk(mark: Mark, target: Target) -> bool:
    return target.scratchable and target.important and bool(mark.safe_repairs)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for mark_id, mark in MARKS.items():
            for target_id, target in TARGETS.items():
                if not hazard_at_risk(mark, target):
                    continue
                if any(repair_matches(r, mark, target) for r in sensible_repairs()):
                    combos.append((mission_id, mark_id, target_id))
    return combos


def predict_damage(world: World, mark_id: str, target_id: str) -> dict:
    sim = world.copy()
    _do_scratch(sim, sim.get(target_id), narrate=False)
    return {
        "blocked": sim.get("ship").meters["blocked"],
        "scratched": sim.get(target_id).meters["scratched"],
        "needs_fix": sim.get("ship").meters["needs_fix"],
        "mark_still_there": sim.get(target_id).meters["obscured"] >= THRESHOLD,
        "mark_id": mark_id,
    }


def _do_scratch(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["scratched"] += 1
    target.meters["damaged"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, mission: Mission, target: Target) -> None:
    ship = world.get("ship")
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"One afternoon, {a.id} and {b.id} turned a cardboard box into {mission.scene}. "
        f"{mission.rig}"
    )
    world.say(
        f"Across {target.the}, they had drawn little arrows and descriptive labels so the ship would feel real."
    )
    world.say(
        f'"{mission.captain} {a.id} and {mission.partner} {b.id}!" {a.id} said. "{mission.launch_line}"'
    )
    ship.meters["ready"] = 1.0


def discover_problem(world: World, b: Entity, mark: Mark, target: Target, mission: Mission) -> None:
    target_ent = world.get("target")
    target_ent.meters["obscured"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But right in the middle of {target.the} at {target.place}, there was {mark.phrase}. "
        f"It spoiled {target.job} and made {mission.obstacle} feel hard to reach."
    )
    world.say(f'{b.id} pointed. "{mark.problem_line}"')


def tempt(world: World, a: Entity, mark: Mark, target: Target) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} picked up a shiny coin. "I can scratch {mark.action} off {target.the} in one quick swipe," '
        f'{a.pronoun()} said.'
    )


def warn(world: World, b: Entity, a: Entity, mark: Mark, target: Target, parent: Entity) -> None:
    pred = predict_damage(world, mark.id, "target")
    b.memes["caution"] += 1
    world.facts["predicted_blocked"] = pred["blocked"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} sounded sure, not bossy, just careful."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "Please don\'t. If you scratch {target.the}, '
        f'we will hurt the part that does {target.job}. We should ask {parent.label_word} how to subtract '
        f'the extra mess the safe way."{extra}'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"It will be fine," {a.id} said. Because {a.pronoun()} was the older sibling, {b.id} could not stop '
            f'{a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"It will be fine," {a.id} said, and leaned closer with the coin.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity, target: Target) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["bravery"] = 0.0
    world.say(
        f'{a.id} looked at {target.the}, then at {b.id}, and lowered the coin. '
        f'"Okay," {a.pronoun()} said. "No scratch."'
    )
    world.say(
        f"They carried the box ship to {parent.label_word}, ready to ask for a safer fix before the mission began."
    )


def scratch_accident(world: World, a: Entity, mark: Mark, target: Target) -> None:
    target_ent = world.get("target")
    _do_scratch(world, target_ent, narrate=False)
    world.say(
        f"The coin made a tiny scratch, then another. The {mark.label} was still there, but now {target.the} "
        f"looked cloudy and hurt."
    )
    world.say(
        f"{target.The} could not do {target.job} properly anymore, and the cardboard spaceship suddenly felt less brave."
    )


def alarm(world: World, b: Entity, a: Entity, parent: Entity, target: Target) -> None:
    world.say(f'"{a.id}, stop! {target.The} is getting ruined!" {b.id} cried.')
    world.say(f'"{parent.label_word.upper()}!"')


def repair_success(world: World, parent: Entity, repair: Repair, mark: Mark, target: Target, mission: Mission) -> None:
    target_ent = world.get("target")
    ship = world.get("ship")
    target_ent.meters["scratched"] = 0.0
    target_ent.meters["damaged"] = 0.0
    target_ent.meters["obscured"] = 0.0
    ship.meters["blocked"] = 0.0
    ship.meters["needs_fix"] = 0.0
    ship.meters["transformed"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came in, understood the problem at once, and {repair.text.format(target=target.label, mark=mark.label)}."
    )
    world.say(repair.transform_text.format(target=target.label, mission=mission.goal))
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
        kid.memes["lesson"] += 1


def repair_fail(world: World, parent: Entity, repair: Repair, mark: Mark, target: Target) -> None:
    target_ent = world.get("target")
    ship = world.get("ship")
    ship.meters["blocked"] += 1
    world.say(
        f"{parent.label_word.capitalize()} tried to help and {repair.fail.format(target=target.label, mark=mark.label)}."
    )
    world.say(
        f"The children could not launch right then, because {target.the} still was not ready for the game."
    )
    for kid in world.kids():
        kid.memes["sadness"] += 1
        kid.memes["lesson"] += 1


def lesson(world: World, parent: Entity, mark: Mark, target: Target) -> None:
    a = world.facts["instigator"]
    b = world.facts["cautioner"]
    world.say(
        f'Then {parent.label_word.capitalize()} knelt beside the box. "When something is in the wrong place," '
        f'{parent.pronoun()} said softly, "we do not scratch first. We subtract the problem with the right tool '
        f'or we replace the part gently."'
    )
    world.say(
        f'{b.id} touched {target.the} with one finger. "{mark.label.capitalize()} can go away," {b.pronoun()} said, '
        f'"but the ship part has to stay kind."'
    )
    world.say(f'"We know," whispered {a.id} and {b.id} together.')


def transformed_launch(world: World, a: Entity, b: Entity, mission: Mission, target: Target) -> None:
    world.say(
        f"When they climbed back in, the old cardboard box had gone through a little transformation. "
        f"{target.The} shone again, and the ship looked ready for {mission.goal}."
    )
    world.say(
        f'{a.id} pressed the pretend buttons, {b.id} checked the star path, and together they {mission.sendoff}.'
    )


def tomorrow_launch(world: World, parent: Entity, a: Entity, b: Entity, mission: Mission, target: Target) -> None:
    ship = world.get("ship")
    target_ent = world.get("target")
    ship.meters["blocked"] = 0.0
    ship.meters["transformed"] += 1
    target_ent.meters["scratched"] = 0.0
    target_ent.meters["damaged"] = 0.0
    target_ent.meters["obscured"] = 0.0
    world.say(
        f"The next day, {parent.label_word} helped them make a fresh {target.label} from safe craft things and tape it carefully in place."
    )
    world.say(
        f"The simple box looked transformed at last, and this time {a.id} waited while {b.id} checked every piece."
    )
    world.say(
        f"Then the two astronauts {mission.sendoff}, slower and wiser than before."
    )


def tell(
    mission: Mission,
    mark: Mark,
    target: Target,
    repair: Repair,
    *,
    instigator: str = "Nova",
    instigator_gender: str = "girl",
    cautioner: str = "Leo",
    cautioner_gender: str = "boy",
    trait: str = "careful",
    parent_type: str = "mother",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
        traits=["bold"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation, "trust": trust},
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(id="ship", type="ship", label="box ship"))
    target_ent = world.add(Entity(
        id="target",
        type="target",
        label=target.label,
        scratchable=target.scratchable,
        important=target.important,
        transparent=target.transparent,
        surface=target.surface,
    ))
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)
    target_ent.meters["obscured"] = 0.0
    target_ent.meters["scratched"] = 0.0
    target_ent.meters["damaged"] = 0.0
    world.get("ship").meters["blocked"] = 0.0
    world.get("ship").meters["needs_fix"] = 0.0
    world.get("ship").meters["transformed"] = 0.0

    play_setup(world, a, b, mission, target)
    discover_problem(world, b, mark, target, mission)

    world.para()
    tempt(world, a, mark, target)
    warn(world, b, a, mark, target, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, parent, target)
        world.para()
        repair_success(world, parent, repair, mark, target, mission)
        lesson(world, parent, mark, target)
        world.para()
        transformed_launch(world, a, b, mission, target)
        outcome = "averted"
    else:
        defy(world, a, b)
        world.para()
        scratch_accident(world, a, mark, target)
        alarm(world, b, a, parent, target)

        success = repair_succeeds(repair, mark, target, delay)
        world.para()
        if success:
            repair_success(world, parent, repair, mark, target, mission)
            lesson(world, parent, mark, target)
            world.para()
            transformed_launch(world, a, b, mission, target)
            outcome = "repaired"
        else:
            repair_fail(world, parent, repair, mark, target)
            lesson(world, parent, mark, target)
            world.para()
            tomorrow_launch(world, parent, a, b, mission, target)
            outcome = "delayed"

    world.facts.update(
        mission=mission,
        mark=mark,
        target_cfg=target,
        target=target_ent,
        repair=repair,
        instigator=a,
        cautioner=b,
        parent=parent,
        delay=delay,
        relation=relation,
        trust=trust,
        outcome=outcome,
        blocked=world.get("ship").meters["blocked"] >= THRESHOLD,
        transformed=world.get("ship").meters["transformed"] >= THRESHOLD,
        damaged=target_ent.meters["damaged"] >= THRESHOLD,
    )
    return world


MISSIONS = {
    "moon": Mission(
        id="moon",
        scene="a silver moon rocket in the middle of the living room",
        rig="A blanket became the launch ramp, couch pillows became crater rocks, and a flashlight under the box made the floor glow like a landing pad.",
        captain="Captain",
        partner="Navigator",
        goal="the quiet moon",
        obstacle="the landing path",
        launch_line="Set course for the quiet moon!",
        sendoff="zoomed away through their living-room stars",
    ),
    "comet": Mission(
        id="comet",
        scene="a comet chaser with a long paper tail",
        rig="Ribbon streamers fluttered behind the box, spoons became antennae, and star stickers marched along the sides like tiny lights.",
        captain="Commander",
        partner="Scout",
        goal="the sleepy comet",
        obstacle="the comet trail",
        launch_line="We have to catch the sleepy comet!",
        sendoff="sailed after the comet trail with happy whooshing sounds",
    ),
    "ring": Mission(
        id="ring",
        scene="a ring-world explorer with cardboard fins",
        rig="Paper plates became planets, a laundry basket became the cargo bay, and blue tape lines on the rug showed the route through space.",
        captain="Pilot",
        partner="Map Keeper",
        goal="the shining ring planet",
        obstacle="the ring path",
        launch_line="Next stop, the shining ring planet!",
        sendoff="glided toward the ring planet with their helmets tipped high",
    ),
}

MARKS = {
    "marker": Mark(
        id="marker",
        label="marker swirl",
        phrase="a dark marker swirl",
        action="the marker swirl",
        problem_line="That scribble is covering the space part we need.",
        safe_repairs={"wipe_cloth", "replace_part"},
        tags={"marker", "wipe"},
    ),
    "stickers": Mark(
        id="stickers",
        label="extra star stickers",
        phrase="too many extra star stickers",
        action="those extra stars",
        problem_line="There are too many stars there. We only need the ones that help.",
        safe_repairs={"peel_gently", "replace_part"},
        tags={"stickers", "peel"},
    ),
    "dust": Mark(
        id="dust",
        label="silver dust smear",
        phrase="a silver dust smear from glittery craft powder",
        action="the dust smear",
        problem_line="That shiny dust is making the space part messy.",
        safe_repairs={"wipe_cloth", "replace_part"},
        tags={"dust", "wipe"},
    ),
}

TARGETS = {
    "visor": Target(
        id="visor",
        label="porthole visor",
        the="the porthole visor",
        phrase="a clear porthole visor cut from a plastic lid",
        place="the front of the box",
        job="letting the astronauts see out",
        surface="plastic",
        fragility=2,
        scratchable=True,
        important=True,
        transparent=True,
        tags={"visor", "plastic"},
    ),
    "panel": Target(
        id="panel",
        label="control panel",
        the="the control panel",
        phrase="a shiny foil control panel",
        place="the side wall",
        job="showing the pretend buttons and numbers",
        surface="foil",
        fragility=1,
        scratchable=True,
        important=True,
        transparent=False,
        tags={"panel", "foil"},
    ),
    "map": Target(
        id="map",
        label="star map",
        the="the star map",
        phrase="a laminated star map",
        place="the inside wall",
        job="showing the route through pretend space",
        surface="laminated",
        fragility=2,
        scratchable=True,
        important=True,
        transparent=False,
        tags={"map", "laminated"},
    ),
    "stone": Target(
        id="stone",
        label="toy moon stone",
        the="the toy moon stone",
        phrase="a painted toy moon stone",
        place="the floor beside the ship",
        job="looking like a crater rock",
        surface="stone",
        fragility=0,
        scratchable=False,
        important=False,
        transparent=False,
        tags={"stone"},
    ),
}

REPAIRS = {
    "wipe_cloth": Repair(
        id="wipe_cloth",
        sense=3,
        power=3,
        works_on_marks={"marker", "dust"},
        works_on_surfaces={"plastic", "foil", "laminated"},
        text="used a soft damp cloth to lift the {mark} away from the {target}",
        fail="rubbed with a cloth, but the {mark} had already mixed with the damage on the {target}",
        qa_text="used a soft damp cloth to clean the mark away",
        transform_text="Then {parent_word} added one bright strip of tape around it, and suddenly the ship looked neater and more space-ready than before.",
        tags={"wipe", "cloth"},
    ),
    "peel_gently": Repair(
        id="peel_gently",
        sense=3,
        power=2,
        works_on_marks={"stickers"},
        works_on_surfaces={"plastic", "foil", "laminated"},
        text="lifted the edge of the extra stars with careful fingers and peeled them away one by one from the {target}",
        fail="tried to peel the extra stars away, but the {target} underneath was already too rough to look right",
        qa_text="peeled the extra stickers away gently",
        transform_text="After that, {parent_word} set the stars back in a neat line, and the pretend ship looked clearer and brighter than before.",
        tags={"peel", "stickers"},
    ),
    "replace_part": Repair(
        id="replace_part",
        sense=4,
        power=4,
        works_on_marks={"*"},
        works_on_surfaces={"*"},
        text="made a fresh {target} from safe craft supplies and taped it in place",
        fail="started to make a new {target}, but there was not enough time to finish it before bedtime",
        qa_text="replaced the damaged part with a fresh one",
        transform_text="The plain box changed shape in their eyes; with the new part in place, it looked like a real ship ready for {mission}.",
        tags={"replace", "craft"},
    ),
    "rub_harder": Repair(
        id="rub_harder",
        sense=1,
        power=1,
        works_on_marks={"marker", "dust", "stickers"},
        works_on_surfaces={"plastic", "foil", "laminated"},
        text="rubbed hard at the {target} with a dry sleeve",
        fail="rubbed harder and only made the {target} look more worn",
        qa_text="rubbed at it with a sleeve",
        transform_text="Nothing looked better after that.",
        tags={"bad_fix"},
    ),
}

for repair in REPAIRS.values():
    repair.transform_text = repair.transform_text.replace("{parent_word}", "the parent")

GIRL_NAMES = ["Nova", "Mira", "Luna", "Zoe", "Ava", "Ivy", "Nora", "Ruby"]
BOY_NAMES = ["Leo", "Max", "Finn", "Owen", "Eli", "Theo", "Kai", "Noah"]
TRAITS = ["careful", "cautious", "patient", "gentle", "curious", "clever"]


@dataclass
class StoryParams:
    mission: str
    mark: str
    target: str
    repair: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
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
    "visor": [(
        "What is a visor on a pretend spaceship?",
        "A visor is the clear part you look through. If it gets scratched, it can look cloudy and be hard to see through."
    )],
    "panel": [(
        "What is a control panel?",
        "A control panel is the place with buttons, switches, or pretend numbers. It helps people know what the machine is supposed to do."
    )],
    "map": [(
        "What is a star map?",
        "A star map is a picture that shows where stars or planets are. It helps a traveler know which way to go."
    )],
    "scratch": [(
        "Why is scratching clear plastic a bad idea?",
        "A scratch can leave a rough line that stays there. On something clear, that rough line can make it harder to see."
    )],
    "marker": [(
        "How can you remove a marker mark safely from the right surface?",
        "On some smooth surfaces, a grown-up can use a soft damp cloth to wipe the mark away gently. Scratching is not the same as cleaning."
    )],
    "stickers": [(
        "What does it mean to subtract extra stickers from a project?",
        "It means taking away the stickers you do not need anymore. You do it gently so the project underneath stays nice."
    )],
    "dust": [(
        "Why can glittery dust be messy?",
        "Tiny shiny dust can smear across a surface and make it look cloudy. It spreads easily if you rub it the wrong way."
    )],
    "wipe": [(
        "Why is a soft cloth safer than scratching for many small messes?",
        "A soft cloth can lift a mark without gouging the surface underneath. Scratching can solve one problem by making a new one."
    )],
    "replace": [(
        "What does transformation mean when you fix a craft?",
        "Transformation means the thing changes into a new and better form. A repaired craft can look brighter, stronger, or clearer than before."
    )],
}
KNOWLEDGE_ORDER = ["visor", "panel", "map", "scratch", "marker", "stickers", "dust", "wipe", "replace"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    mission = f["mission"]
    mark = f["mark"]
    target = f["target_cfg"]
    repair = f["repair"]
    outcome = f["outcome"]
    base = (
        f'Write a short space adventure for a 3-to-5-year-old where two children build a pretend spaceship, '
        f'face a small craft problem, and learn not to scratch {target.the}. Include the words "descriptive", '
        f'"scratch", and "subtract".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle near-miss story where {a.id} wants to scratch away {mark.phrase}, but {b.id} stops {a.pronoun('object')} and a grown-up shows them a safer fix.",
            f"Write a story about a cardboard spaceship transformation where the children ask for help before any damage happens and then launch happily.",
        ]
    if outcome == "delayed":
        return [
            base,
            f"Tell a space adventure where {a.id} scratches {target.the}, the ship cannot launch right away, and the family has to rebuild the part for tomorrow.",
            f"Write a cautionary but comforting story where the children learn to subtract a mistake with the right tool instead of making a deeper one.",
        ]
    return [
        base,
        f"Tell a child-friendly story where {a.id} scratches {target.the}, a calm grown-up repairs it, and the cardboard box is transformed into a better spaceship.",
        f"Write a simple story that ends with the children launching after a safe repair by {repair.qa_text}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    mission = f["mission"]
    mark = f["mark"]
    target = f["target_cfg"]
    repair = f["repair"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and their {pw} helping with a pretend space mission."
        ),
        (
            "What were the children pretending?",
            f"They were pretending the cardboard box was {mission.scene}. The game felt exciting because everything in the room had turned into part of a mission."
        ),
        (
            f"What problem did they find on {target.the}?",
            f"They found {mark.phrase} on {target.the}. That mattered because {target.the} was supposed to do {target.job}."
        ),
        (
            f"Why did {b.id} warn {a.id} not to scratch {target.the}?",
            f"{b.id} knew scratching could hurt the part itself, not just the mark. In this story, damaging {target.the} would block the mission instead of helping it."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What did {a.id} do after the warning?",
            f"{a.id} lowered the coin and chose not to scratch {target.the}. That gave the family a chance to fix the problem safely before the ship was damaged."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the cardboard ship transformed and ready to fly. The children launched happily because they asked for help before the pretend mission was spoiled."
        ))
    elif f["outcome"] == "repaired":
        qa.append((
            f"What happened when {a.id} scratched {target.the}?",
            f"The mark stayed, and {target.the} became scratched and cloudy or rough. So one quick scratch made the mission harder instead of easier."
        ))
        qa.append((
            f"How did {a.id}'s {pw} fix the problem?",
            f"{pw.capitalize()} {repair.qa_text}. That safe method removed the trouble without hurting the ship part further."
        ))
        qa.append((
            "What transformation happened at the end?",
            f"The plain box looked like a better spaceship than before. The repair did not only solve the problem; it changed the ship into something brighter and more ready for adventure."
        ))
    else:
        qa.append((
            f"Could they launch right away after {a.id} scratched {target.the}?",
            f"No. The damage meant the ship was not ready, so the game had to wait. That delay showed why the wrong fix can create a bigger problem."
        ))
        qa.append((
            "How did the story still end hopefully?",
            f"The next day, the family made a fresh part and transformed the ship together. So the children still got their launch, but only after learning patience and care."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    target = f["target_cfg"]
    if target.id in {"visor", "panel", "map"}:
        tags.add(target.id)
    tags.add("scratch")
    tags |= {t for t in f["mark"].tags if t in KNOWLEDGE}
    if f["repair"].id in {"wipe_cloth", "peel_gently"}:
        tags.add("wipe")
    if f["repair"].id == "replace_part" or f["transformed"]:
        tags.add("replace")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        flags = []
        if ent.scratchable:
            flags.append("scratchable")
        if ent.important:
            flags.append("important")
        if ent.transparent:
            flags.append("transparent")
        if ent.surface:
            bits.append(f"surface={ent.surface}")
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="moon",
        mark="marker",
        target="visor",
        repair="wipe_cloth",
        instigator="Nova",
        instigator_gender="girl",
        cautioner="Leo",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        mission="comet",
        mark="stickers",
        target="panel",
        repair="peel_gently",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mira",
        cautioner_gender="girl",
        parent="father",
        trait="patient",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        mission="ring",
        mark="dust",
        target="map",
        repair="wipe_cloth",
        instigator="Luna",
        instigator_gender="girl",
        cautioner="Finn",
        cautioner_gender="boy",
        parent="mother",
        trait="curious",
        delay=1,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        mission="moon",
        mark="stickers",
        target="visor",
        repair="replace_part",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Ruby",
        cautioner_gender="girl",
        parent="father",
        trait="cautious",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=3,
    ),
    StoryParams(
        mission="comet",
        mark="marker",
        target="map",
        repair="replace_part",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Kai",
        cautioner_gender="boy",
        parent="mother",
        trait="gentle",
        delay=0,
        instigator_age=4,
        cautioner_age=6,
        relation="siblings",
        trust=6,
    ),
]


def explain_rejection(mark: Mark, target: Target) -> str:
    if not target.scratchable or not target.important:
        return (
            f"(No story: {target.the} is not the kind of important ship part that a scratch would ruin. "
            f"Pick the visor, control panel, or star map instead.)"
        )
    if not any(repair_matches(r, mark, target) for r in sensible_repairs()):
        return (
            f"(No story: the world has no sensible safe repair for {mark.label} on {target.the}. "
            f"A story here needs a believable safer method, not just a warning.)"
        )
    return "(No story: this combination does not create a reasonable scratch-and-repair problem.)"


def explain_repair(repair_id: str) -> str:
    repair = REPAIRS[repair_id]
    better = ", ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{repair_id}': it scores too low on common sense "
        f"(sense={repair.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(M, T) :- mark(M), target(T), scratchable(T), important(T).
sensible(R) :- repair(R), sense(R, S), sense_min(M), S >= M.
repair_matches(R, M, T) :- repair(R), mark(M), target(T),
                           works_on_mark(R, M), works_on_surface(R, T).
repair_matches(R, M, T) :- repair(R), mark(M), target(T),
                           works_on_mark(R, any_mark), works_on_surface(R, T).
repair_matches(R, M, T) :- repair(R), mark(M), target(T),
                           works_on_mark(R, M), works_on_surface(R, any_surface).
repair_matches(R, M, T) :- repair(R), mark(M), target(T),
                           works_on_mark(R, any_mark), works_on_surface(R, any_surface).
has_safe_fix(M, T) :- repair_matches(R, M, T), sensible(R).
valid(Mission, M, T) :- mission(Mission), hazard(M, T), has_safe_fix(M, T).

% --- outcome inference -----------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(F + D) :- chosen_target(T), fragility(T, F), delay(D).
success :- chosen_repair(R), chosen_mark(M), chosen_target(T),
           repair_matches(R, M, T), power(R, P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(repaired) :- not averted, success.
outcome(delayed) :- not averted, not success.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for mark_id in MARKS:
        lines.append(asp.fact("mark", mark_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        if target.scratchable:
            lines.append(asp.fact("scratchable", target_id))
        if target.important:
            lines.append(asp.fact("important", target_id))
        lines.append(asp.fact("fragility", target_id, target.fragility))
        lines.append(asp.fact("surface_of", target_id, target.surface))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("power", repair_id, repair.power))
        for mark_id in sorted(repair.works_on_marks):
            lines.append(asp.fact("works_on_mark", repair_id, "any_mark" if mark_id == "*" else mark_id))
        for surface in sorted(repair.works_on_surfaces):
            lines.append(asp.fact("works_on_surface", repair_id, "any_surface" if surface == "*" else surface))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("works_on_surface", target_id, target.surface))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines).replace("works_on_surface(", "surface_stub(").replace("surface_stub", "works_on_surface")


def asp_program(extra: str, show: str) -> str:
    program = asp_facts()
    program += "\n"
    for target_id, target in TARGETS.items():
        program += f"works_on_surface_target({target_id},{target.surface}).\n"
    program += """
works_on_surface(R, T) :- works_on_surface(R, S), works_on_surface_target(T, S), repair(R), target(T).
"""
    program += ASP_RULES
    program += "\n"
    program += extra
    program += "\n"
    program += show
    program += "\n"
    return program


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
    extra = "\n".join([
        asp.fact("chosen_mark", params.mark),
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_repair", params.repair),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "repaired" if repair_succeeds(REPAIRS[params.repair], MARKS[params.mark], TARGETS[params.target], params.delay) else "delayed"


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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_repairs()}
    if c_sens == p_sens:
        print(f"OK: sensible repairs match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Random resolve failed unexpectedly for seed {seed}.")
            break

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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a cardboard spaceship, a scratch problem, and a safer transformation."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--mark", choices=MARKS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time before the grown-up repair")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target:
        target = TARGETS[args.target]
        if not target.scratchable or not target.important:
            mark = MARKS[args.mark] if args.mark else next(iter(MARKS.values()))
            raise StoryError(explain_rejection(mark, target))
    if args.mark and args.target:
        mark = MARKS[args.mark]
        target = TARGETS[args.target]
        if not any(repair_matches(r, mark, target) for r in sensible_repairs()):
            raise StoryError(explain_rejection(mark, target))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        c for c in valid_combos()
        if (args.mission is None or c[0] == args.mission)
        and (args.mark is None or c[1] == args.mark)
        and (args.target is None or c[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, mark_id, target_id = rng.choice(sorted(combos))
    compatible_repairs = [
        r.id for r in sensible_repairs()
        if repair_matches(r, MARKS[mark_id], TARGETS[target_id])
    ]
    if args.repair is not None:
        if args.repair not in compatible_repairs:
            raise StoryError(
                f"(No story: repair '{args.repair}' is not a safe match for {mark_id} on {target_id}.)"
            )
        repair_id = args.repair
    else:
        repair_id = rng.choice(sorted(compatible_repairs))

    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        mission=mission_id,
        mark=mark_id,
        target=target_id,
        repair=repair_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        mission = MISSIONS[params.mission]
        mark = MARKS[params.mark]
        target = TARGETS[params.target]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if not hazard_at_risk(mark, target):
        raise StoryError(explain_rejection(mark, target))
    if repair.sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))
    if not repair_matches(repair, mark, target):
        raise StoryError(f"(No story: repair '{repair.id}' does not match {mark.id} on {target.id}.)")

    world = tell(
        mission=mission,
        mark=mark,
        target=target,
        repair=repair,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible repairs: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (mission, mark, target) combos:\n")
        for mission, mark, target in combos:
            print(f"  {mission:8} {mark:9} {target}")
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
                f"### {p.instigator} & {p.cautioner}: {p.mark} on {p.target} "
                f"({p.mission}, {p.repair}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
