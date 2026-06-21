#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/meantime_flashback_tall_tale.py
==========================================================

A standalone story world for a child-facing tall tale with a flashback beat.

Premise
-------
A child grows something so huge it belongs in a tall tale: an enormous pumpkin
bound for a fair. On the way, the giant pumpkin meets one trouble spot on the
road. While the trouble is brewing, the child has a flashback to a grown-up's
earlier lesson and uses a matching fix. In the meantime, the road keeps getting
worse, so the timing and the method matter.

Design notes
------------
This world keeps one compact domain and uses state, not slot-swapped prose:

* physical meters: wobble, stuck, split, pressure, delay, road danger
* emotional memes: pride, worry, courage, memory, relief
* a flashback is triggered by the rising trouble
* the ending depends on whether the chosen fix is sensible and strong enough

Run it
------
python storyworlds/worlds/gpt-5.4/meantime_flashback_tall_tale.py
python storyworlds/worlds/gpt-5.4/meantime_flashback_tall_tale.py --route creek_bridge --trouble wobble
python storyworlds/worlds/gpt-5.4/meantime_flashback_tall_tale.py --fix broom   # rejected
python storyworlds/worlds/gpt-5.4/meantime_flashback_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/meantime_flashback_tall_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/meantime_flashback_tall_tale.py --verify
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
        return {
            "grandfather": "grandpa",
            "grandmother": "grandma",
            "father": "dad",
            "mother": "mom",
            "uncle": "uncle",
            "aunt": "aunt",
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
class Crop:
    id: str
    label: str
    phrase: str
    boast: str
    roll_line: str
    size: int
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
class Route:
    id: str
    label: str
    phrase: str
    view: str
    trouble_spots: set[str] = field(default_factory=set)
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
class Trouble:
    id: str
    label: str
    verb: str
    warning: str
    danger_line: str
    severity: int
    needs: set[str] = field(default_factory=set)
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
class Lesson:
    id: str
    elder_type: str
    elder_name: str
    line: str
    skill: str
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
    action: str
    success: str
    fail: str
    qa_text: str
    sense: int
    power: int
    handles: set[str] = field(default_factory=set)
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


def _r_wobble_fear(world: World) -> list[str]:
    out: list[str] = []
    crop = world.get("crop")
    hero = world.get("hero")
    if crop.meters["wobble"] >= THRESHOLD:
        sig = ("wobble_fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            world.get("road").meters["danger"] += 1
            out.append("__wobble__")
    return out


def _r_stuck_pressure(world: World) -> list[str]:
    out: list[str] = []
    crop = world.get("crop")
    hero = world.get("hero")
    if crop.meters["stuck"] >= THRESHOLD:
        sig = ("stuck_pressure",)
        if sig not in world.fired:
            world.fired.add(sig)
            crop.meters["pressure"] += 1
            hero.memes["worry"] += 1
            world.get("road").meters["danger"] += 1
            out.append("__stuck__")
    return out


def _r_danger_memory(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    road = world.get("road")
    if road.meters["danger"] >= THRESHOLD and hero.memes["memory"] < THRESHOLD:
        sig = ("memory",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["memory"] += 1
            hero.memes["courage"] += 1
            out.append("__memory__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble_fear", tag="physical", apply=_r_wobble_fear),
    Rule(name="stuck_pressure", tag="physical", apply=_r_stuck_pressure),
    Rule(name="danger_memory", tag="emotional", apply=_r_danger_memory),
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
        for s in produced:
            world.say(s)
    return produced


def compatible_fix(trouble: Trouble, fix: Fix) -> bool:
    return trouble.id in fix.handles or bool(trouble.needs & fix.handles)


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for crop_id in CROPS:
        crop = CROPS[crop_id]
        for route_id, route in ROUTES.items():
            for trouble_id, trouble in TROUBLES.items():
                if trouble_id not in route.trouble_spots:
                    continue
                for lesson_id, lesson in LESSONS.items():
                    if lesson.skill in trouble.needs:
                        combos.append((crop.id, route_id, trouble_id, lesson_id))
    return combos


def trouble_load(crop: Crop, trouble: Trouble, delay: int) -> int:
    return crop.size + trouble.severity + delay


def fix_holds(crop: Crop, trouble: Trouble, fix: Fix, delay: int) -> bool:
    return compatible_fix(trouble, fix) and fix.power >= trouble_load(crop, trouble, delay)


def explain_combo_rejection(route: Route, trouble: Trouble, lesson: Lesson) -> str:
    if trouble.id not in route.trouble_spots:
        return (
            f"(No story: {route.label} does not create the '{trouble.label}' trouble. "
            f"Pick a route that can honestly cause that problem.)"
        )
    if lesson.skill not in trouble.needs:
        return (
            f"(No story: {lesson.elder_name}'s lesson teaches {lesson.skill}, "
            f"but the '{trouble.label}' trouble needs {', '.join(sorted(trouble.needs))}. "
            f"The flashback must match the problem.)"
        )
    return "(No story: this combination does not fit the world.)"


def explain_fix_rejection(fix: Fix) -> str:
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix.id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_trouble(world: World, trouble_id: str) -> dict:
    sim = world.copy()
    crop = sim.get("crop")
    if trouble_id == "wobble":
        crop.meters["wobble"] += 1
    elif trouble_id == "stuck":
        crop.meters["stuck"] += 1
    elif trouble_id == "split":
        crop.meters["wobble"] += 1
        crop.meters["pressure"] += 1
        crop.meters["split"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("road").meters["danger"],
        "worry": sim.get("hero").memes["worry"],
        "memory": sim.get("hero").memes["memory"],
    }


def introduce(world: World, hero: Entity, crop: Crop, route: Route, town: str) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} grew {crop.phrase} behind the barn, and by the end of summer "
        f"{crop.boast}. Folks said even the moon leaned down to count its ribs."
    )
    world.say(
        f"When fair day came, {hero.pronoun()} set out for {town} along {route.phrase}. "
        f"{route.view}"
    )


def boast_and_goal(world: World, hero: Entity, crop: Crop, prize: str) -> None:
    world.say(
        f'"If this {crop.label} wins the blue ribbon for {prize}," {hero.id} said, '
        f'"I\'ll have bragging rights clear to next planting season."'
    )
    world.say(crop.roll_line)


def trouble_begins(world: World, hero: Entity, crop_ent: Entity, trouble: Trouble) -> None:
    if trouble.id == "wobble":
        crop_ent.meters["wobble"] += 1
    elif trouble.id == "stuck":
        crop_ent.meters["stuck"] += 1
    elif trouble.id == "split":
        crop_ent.meters["wobble"] += 1
        crop_ent.meters["pressure"] += 1
        crop_ent.meters["split"] += 1
    propagate(world, narrate=False)
    world.say(trouble.warning)
    world.say(trouble.danger_line)


def flashback(world: World, hero: Entity, lesson: Lesson, trouble: Trouble) -> None:
    pred = predict_trouble(world, trouble.id)
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f"In the meantime, while the giant trouble kept growing, a memory flashed "
        f"through {hero.id}'s mind."
    )
    world.say(
        f"{hero.id} remembered a day with {lesson.elder_name}, {hero.pronoun('possessive')} "
        f"{lesson.elder_type}. Back then, {lesson.line}"
    )
    world.say(
        f"That flashback did not feel dreamy at all. It felt like a tool {hero.pronoun()} "
        f"could hold in {hero.pronoun('possessive')} hands."
    )


def choose_fix(world: World, hero: Entity, fix: Fix) -> None:
    hero.memes["courage"] += 1
    world.say(
        f'"Then I know what to do," {hero.id} said, reaching for {fix.phrase}. '
        f"{hero.pronoun().capitalize()} moved fast but careful, because huge things "
        f"can make huge messes."
    )


def rescue_success(world: World, hero: Entity, crop_ent: Entity, fix: Fix, trouble: Trouble, prize: str) -> None:
    crop_ent.meters["wobble"] = 0.0
    crop_ent.meters["stuck"] = 0.0
    crop_ent.meters["pressure"] = 0.0
    world.get("road").meters["danger"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["worry"] = 0.0
    world.say(fix.success)
    world.say(
        f"Soon the way was steady again, and the giant {crop_ent.label} rolled on "
        f"toward town as if it had remembered its manners."
    )
    world.say(
        f"At the fair, it won the blue ribbon for {prize}, and people swore the band "
        f"had to play two extra songs before they could march all the way around it."
    )


def rescue_fail(world: World, hero: Entity, crop_ent: Entity, fix: Fix, trouble: Trouble) -> None:
    crop_ent.meters["split"] += 1
    world.get("road").meters["danger"] += 1
    hero.memes["worry"] += 1
    world.say(fix.fail)
    if trouble.id == "split":
        world.say(
            f"The crack in the giant {crop_ent.label} ran wider and wider until seeds "
            f"spilled like a hailstorm of saucers."
        )
    else:
        world.say(
            f"The giant {crop_ent.label} lurched once, then twice, and burst open with "
            f"a ploomp that made crows flap out of three counties."
        )


def ending_after_loss(world: World, hero: Entity, lesson: Lesson) -> None:
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id} did not get a ribbon that day, but {hero.pronoun()} still stood in the "
        f"road and caught {hero.pronoun('possessive')} breath."
    )
    world.say(
        f'"Grandpa was right," {hero.pronoun()} said softly. "A big job needs the right trick, '
        f'not just the fastest one."'
        if lesson.elder_type == "grandfather"
        else f'"{lesson.elder_name} was right," {hero.pronoun()} said softly. '
             f'"A big job needs the right trick, not just the fastest one."'
    )
    world.say(
        "Then the neighbors came with buckets, smiles, and pie tins, and by sunset the loss "
        "had turned into the biggest pumpkin supper the valley had ever seen."
    )


def tell(
    crop: Crop,
    route: Route,
    trouble: Trouble,
    lesson: Lesson,
    fix: Fix,
    hero_name: str = "Mabel",
    hero_gender: str = "girl",
    delay: int = 0,
    prize: str = "the biggest pumpkin",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type=lesson.elder_type,
            label=lesson.elder_name,
            role="elder",
            attrs={"skill": lesson.skill},
        )
    )
    road = world.add(Entity(id="road", type="road", label=route.label))
    crop_ent = world.add(Entity(id="crop", type="crop", label=crop.label))
    tool = world.add(Entity(id="tool", type="tool", label=fix.label))
    world.facts.update(
        hero=hero,
        elder=elder,
        route=route,
        crop_cfg=crop,
        crop=crop_ent,
        trouble=trouble,
        lesson=lesson,
        fix=fix,
        prize=prize,
        delay=delay,
        town="Mulebend Fair",
    )

    introduce(world, hero, crop, route, world.facts["town"])
    boast_and_goal(world, hero, crop, prize)

    world.para()
    trouble_begins(world, hero, crop_ent, trouble)
    flashback(world, hero, lesson, trouble)

    if delay > 0:
        crop_ent.meters["pressure"] += float(delay)
        world.say(
            f"But every heartbeat mattered. By the time {hero.id} grabbed the tool, "
            f"the trouble had already had {delay} extra head start{'s' if delay != 1 else ''}."
        )

    world.para()
    choose_fix(world, hero, fix)

    success = fix_holds(crop, trouble, fix, delay)
    if success:
        rescue_success(world, hero, crop_ent, fix, trouble, prize)
        outcome = "saved"
    else:
        rescue_fail(world, hero, crop_ent, fix, trouble)
        world.para()
        ending_after_loss(world, hero, lesson)
        outcome = "burst"

    world.facts["outcome"] = outcome
    world.facts["saved"] = success
    world.facts["flashback_used"] = hero.memes["memory"] >= THRESHOLD
    world.facts["trouble_load"] = trouble_load(crop, trouble, delay)
    return world


CROPS = {
    "pumpkin": Crop(
        id="pumpkin",
        label="pumpkin",
        phrase="a pumpkin so round and orange it looked like a sunrise had sat down in the patch",
        boast="it was bigger than the wash tub, broader than the porch swing, and so heavy the wheelbarrow asked for mercy",
        roll_line="It rolled in front of the cart like a lazy golden boulder, and each turn left a track the ducks could have sailed in.",
        size=1,
        tags={"pumpkin", "fair"},
    ),
    "gourd": Crop(
        id="gourd",
        label="gourd",
        phrase="a bottle gourd long enough to make the fence posts feel short",
        boast="it leaned across two rows at once and made the scarecrow look like a coat peg",
        roll_line="It bumped and boomed along the wagon bed as if a green cannon had decided to become a vegetable.",
        size=2,
        tags={"gourd", "fair"},
    ),
    "squash": Crop(
        id="squash",
        label="squash",
        phrase="a yellow squash thick as a canoe and proud as a parade float",
        boast="its blossoms had once shaded a whole basket of chicks from the noon sun",
        roll_line="It slid and thumped with such importance that even the mule kept glancing back at it.",
        size=2,
        tags={"squash", "fair"},
    ),
}

ROUTES = {
    "creek_bridge": Route(
        id="creek_bridge",
        label="creek bridge",
        phrase="the plank bridge over Possum Creek",
        view="The water winked below, and the boards gave little creeky groans under every weighty step.",
        trouble_spots={"wobble", "split"},
        tags={"bridge", "creek"},
    ),
    "mud_hill": Route(
        id="mud_hill",
        label="mud hill",
        phrase="the red mud hill by Cider Knob",
        view="The road climbed slick and shiny, and wagon tracks curled through the clay like ribbons.",
        trouble_spots={"stuck", "split"},
        tags={"hill", "mud"},
    ),
    "windy_lane": Route(
        id="windy_lane",
        label="windy lane",
        phrase="the windy lane past Miller's field",
        view="The lane ran between high grass, and the breeze kept practicing its push on everything taller than a thistle.",
        trouble_spots={"wobble"},
        tags={"wind", "lane"},
    ),
}

TROUBLES = {
    "wobble": Trouble(
        id="wobble",
        label="wobble",
        verb="wobble",
        warning="Halfway there, the giant load began to wobble from side to side, first as gently as a cradle and then as sharply as a sneeze.",
        danger_line="Every sway made the boards or wheels answer back, and one bad lurch could send the whole champion crop rolling where it pleased.",
        severity=1,
        needs={"brace", "tie"},
        tags={"wobble", "balance"},
    ),
    "stuck": Trouble(
        id="stuck",
        label="stuck",
        verb="stick",
        warning="At the worst part of the road, the giant load sank until the wheels looked knee-deep in mud and the cart gave up with a miserable squelch.",
        danger_line="The more it strained in one place, the more the giant crop pressed and twisted, and stuck things have a way of splitting when they are hurried.",
        severity=2,
        needs={"lever", "roll"},
        tags={"stuck", "mud"},
    ),
    "split": Trouble(
        id="split",
        label="split",
        verb="split",
        warning="Then a hard little crack whispered under the giant rind, the kind of sound that makes a gardener's heart jump clear to the brim of a hat.",
        danger_line="A giant crop under strain does not crack politely. It threatens to open all at once and turn the road into supper.",
        severity=2,
        needs={"wrap", "brace"},
        tags={"split", "rind"},
    ),
}

LESSONS = {
    "double_knot": Lesson(
        id="double_knot",
        elder_type="grandfather",
        elder_name="Grandpa Reed",
        line='Grandpa Reed had looped rope around a hay wagon and said, "Big things like to wiggle. Tie them twice, and they remember who is boss."',
        skill="tie",
        tags={"rope", "memory"},
    ),
    "fence_post_brace": Lesson(
        id="fence_post_brace",
        elder_type="grandmother",
        elder_name="Grandma June",
        line='Grandma June had steadied a leaning gate with two stout boards and said, "If a thing wants to wander, give it a shoulder to lean on."',
        skill="brace",
        tags={"boards", "memory"},
    ),
    "corncrib_lever": Lesson(
        id="corncrib_lever",
        elder_type="uncle",
        elder_name="Uncle Hal",
        line='Uncle Hal had once pried a wagon wheel from a rut with a long pole and said, "A small arm can borrow giant strength from a good lever."',
        skill="lever",
        tags={"pole", "memory"},
    ),
    "log_roll": Lesson(
        id="log_roll",
        elder_type="father",
        elder_name="Dad Amos",
        line='Dad Amos had rolled a rain barrel over scraps of pipe and said, "Round under round is a fine friend to heavy work."',
        skill="roll",
        tags={"rollers", "memory"},
    ),
    "patch_wrap": Lesson(
        id="patch_wrap",
        elder_type="aunt",
        elder_name="Aunt Tilly",
        line='Aunt Tilly had wrapped a split melon in cloth and twine and said, "If the skin wants to part, hug it close before it changes its mind."',
        skill="wrap",
        tags={"cloth", "memory"},
    ),
}

FIXES = {
    "rope_harness": Fix(
        id="rope_harness",
        label="rope harness",
        phrase="a rope harness and a farmer's knot",
        action="lashed the giant crop tight with rope",
        success="With two quick loops and one hard pull, the rope harness hugged the giant load tight, and the wobble settled down like a dog after supper.",
        fail="The rope bit in, but the great load still heaved against it until the knots sang and slipped.",
        qa_text="used a rope harness and tight knots to steady the load",
        sense=3,
        power=3,
        handles={"tie", "wobble"},
        tags={"rope", "knot"},
    ),
    "board_brace": Fix(
        id="board_brace",
        label="board brace",
        phrase="two stout boards for bracing",
        action="wedged boards along the sides to keep the load from wandering",
        success="The boards took the shove of every sway, and soon the giant crop rode snug between them as if the cart had been built for it from the start.",
        fail="The boards helped for one breath, but the giant load shoved past them and rattled loose again.",
        qa_text="braced the load with stout boards",
        sense=3,
        power=4,
        handles={"brace", "wobble", "split"},
        tags={"boards", "brace"},
    ),
    "roller_poles": Fix(
        id="roller_poles",
        label="roller poles",
        phrase="short poles and smooth rollers",
        action="slid rollers under the wheels and eased the cart forward",
        success="The wheels climbed onto the rollers one by one, and the whole cart came free with a slurp and a cheer from the blackbirds.",
        fail="The rollers turned, but the mud held tighter, and the burden twisted harder instead of coming free.",
        qa_text="used rollers and poles to free the cart from the mud",
        sense=3,
        power=5,
        handles={"lever", "roll", "stuck"},
        tags={"rollers", "mud"},
    ),
    "cloth_wrap": Fix(
        id="cloth_wrap",
        label="cloth wrap",
        phrase="a long strip of feed cloth and twine",
        action="wrapped the cracked rind snugly to hold it together",
        success="The cloth hugged the crack closed, the twine snugged it firm, and the split stopped spreading as if the giant rind had taken a deep breath.",
        fail="The cloth pulled tight, but the crack kept creeping underneath until the whole thing groaned apart.",
        qa_text="wrapped the cracked rind with cloth and twine",
        sense=2,
        power=4,
        handles={"wrap", "split"},
        tags={"cloth", "rind"},
    ),
    "broom": Fix(
        id="broom",
        label="broom",
        phrase="an old porch broom",
        action="poked at the problem with a broom",
        success="The impossible happened and the broom worked somehow.",
        fail="The broom only tickled the giant trouble and made it madder.",
        qa_text="tried a broom",
        sense=1,
        power=1,
        handles={"wobble"},
        tags={"broom"},
    ),
}

NAMES_GIRL = ["Mabel", "Clara", "Dolly", "Ruthie", "Nell", "Sadie", "Pearl"]
NAMES_BOY = ["Jeb", "Eli", "Otis", "Cal", "Ned", "Hank", "Will"]
PRIZES = [
    "the biggest pumpkin",
    "the heaviest gourd",
    "the grand champion squash",
    "the blue ribbon in giant vegetables",
]


@dataclass
class StoryParams:
    crop: str
    route: str
    trouble: str
    lesson: str
    fix: str
    hero_name: str
    hero_gender: str
    delay: int = 0
    prize: str = "the blue ribbon in giant vegetables"
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
    "pumpkin": [(
        "What is a pumpkin?",
        "A pumpkin is a round orange squash that grows on a vine. People use pumpkins for food, pies, and fall decorations."
    )],
    "gourd": [(
        "What is a gourd?",
        "A gourd is a hard-skinned plant that grows on a vine. Some gourds are used for food, and some are dried and used like containers or decorations."
    )],
    "squash": [(
        "What is squash?",
        "Squash is a kind of vine-grown vegetable. It can come in many sizes and colors, and some kinds are eaten cooked."
    )],
    "fair": [(
        "What happens at a county fair?",
        "At a county fair, people bring animals, crops, crafts, and food to share and judge. There are often ribbons, music, and big smiles."
    )],
    "rope": [(
        "Why do ropes help hold big things still?",
        "A rope can wrap around something and pull it snug. Good knots help spread the pull so the load does not slide around as easily."
    )],
    "brace": [(
        "What does it mean to brace something?",
        "To brace something is to support it so it cannot wobble or tip. A brace acts like a steady shoulder."
    )],
    "lever": [(
        "What is a lever?",
        "A lever is a stiff bar or pole that helps you lift or move something heavy. It lets a small push do a bigger job."
    )],
    "rollers": [(
        "Why do rollers help move heavy things?",
        "Rollers let a heavy thing roll instead of scrape. Rolling takes less force than dragging through mud or over rough ground."
    )],
    "flashback": [(
        "What is a flashback in a story?",
        "A flashback is when a story briefly remembers something that happened earlier. It helps explain what a character knows or why they make a choice."
    )],
    "mud": [(
        "Why can mud make a wagon get stuck?",
        "Mud is soft and slippery, so wheels sink down into it. Once the wheel is deep, it has to push through sticky ground instead of rolling freely."
    )],
    "split": [(
        "Why can a giant vegetable split?",
        "If something big is squeezed or twisted too hard, its skin can crack. Once a crack starts, more pressure can make it spread."
    )],
}
KNOWLEDGE_ORDER = ["flashback", "fair", "pumpkin", "gourd", "squash", "rope", "brace", "lever", "rollers", "mud", "split"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    crop = f["crop_cfg"]
    trouble = f["trouble"]
    route = f["route"]
    hero = f["hero"]
    lesson = f["lesson"]
    if f["outcome"] == "saved":
        return [
            f'Write a short Tall Tale for a 3-to-5-year-old about a child taking a giant {crop.label} to a fair. Include the word "meantime" and use a flashback.',
            f"Tell a child-friendly tall tale where {hero.label} faces a {trouble.label} on {route.phrase}, remembers {lesson.elder_name}'s advice in a flashback, and saves the day.",
            f"Write a big, funny farm story where the problem grows huge, but a remembered lesson gives the child the right fix."
        ]
    return [
        f'Write a gentle Tall Tale for a 3-to-5-year-old about a child taking a giant {crop.label} to a fair. Include the word "meantime" and use a flashback.',
        f"Tell a cautionary tall tale where {hero.label} remembers an earlier lesson, but the giant {crop.label} is too far gone to save.",
        f"Write a farm story with a flashback, an oversized problem, and an ending where people still turn trouble into something kind and shared."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    crop = f["crop_cfg"]
    route = f["route"]
    trouble = f["trouble"]
    lesson = f["lesson"]
    fix = f["fix"]
    prize = f["prize"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who grew a giant {crop.label} and took it toward the fair. The story also includes {lesson.elder_name}, whose earlier lesson mattered later."
        ),
        (
            f"What was {hero.label} trying to do?",
            f"{hero.label} was trying to bring the giant {crop.label} to the fair to win {prize}. That goal is what sent {hero.pronoun('object')} along {route.phrase} in the first place."
        ),
        (
            f"What problem happened on the road?",
            f"The giant {crop.label} ran into a {trouble.label} problem on {route.phrase}. That trouble made the trip dangerous because a huge load can cause a huge mess when it goes wrong."
        ),
        (
            "What was the flashback about?",
            f"The flashback was about {lesson.elder_name} teaching {lesson.skill} earlier. It gave {hero.label} an idea that fit the problem instead of just making {hero.pronoun('object')} panic."
        ),
    ]
    if f["outcome"] == "saved":
        qa.append((
            f"How did {hero.label} save the giant {crop.label}?",
            f"{hero.pronoun().capitalize()} {fix.qa_text}. That worked because the remembered lesson matched the kind of trouble the load was in."
        ))
        qa.append((
            "Why was the flashback important?",
            f"The flashback mattered because it turned an old memory into a useful plan. Without it, {hero.label} would have had a giant problem and no honest way to fix it."
        ))
        qa.append((
            "How did the story end?",
            f"The giant {crop.label} reached the fair and won {prize}. The ending proves the change because the load that nearly failed on the road arrived steady and proud."
        ))
    else:
        qa.append((
            f"Did the fix work in time?",
            f"No. {hero.label} tried {fix.label}, but the giant {crop.label} could not be saved. The trouble had grown too strong before the fix could fully help."
        ))
        qa.append((
            "Was the flashback still useful even though the crop burst?",
            f"Yes. The flashback still helped {hero.label} understand what should have been done and why the job needed the right method. It turned the loss into a lesson instead of just a disaster."
        ))
        qa.append((
            "How did the story end?",
            f"The crop burst, but the neighbors came together and shared food by sunset. The ending shows that the day changed from loss into kindness."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"flashback", "fair"}
    crop = f["crop_cfg"]
    trouble = f["trouble"]
    lesson = f["lesson"]
    fix = f["fix"]
    tags |= set(crop.tags) | set(trouble.tags) | set(lesson.tags) | set(fix.tags)
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
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        crop="pumpkin",
        route="creek_bridge",
        trouble="wobble",
        lesson="fence_post_brace",
        fix="board_brace",
        hero_name="Mabel",
        hero_gender="girl",
        delay=0,
        prize="the blue ribbon in giant vegetables",
    ),
    StoryParams(
        crop="gourd",
        route="mud_hill",
        trouble="stuck",
        lesson="corncrib_lever",
        fix="roller_poles",
        hero_name="Otis",
        hero_gender="boy",
        delay=1,
        prize="the heaviest gourd",
    ),
    StoryParams(
        crop="squash",
        route="creek_bridge",
        trouble="split",
        lesson="patch_wrap",
        fix="cloth_wrap",
        hero_name="Pearl",
        hero_gender="girl",
        delay=0,
        prize="the grand champion squash",
    ),
    StoryParams(
        crop="gourd",
        route="windy_lane",
        trouble="wobble",
        lesson="double_knot",
        fix="rope_harness",
        hero_name="Eli",
        hero_gender="boy",
        delay=1,
        prize="the blue ribbon in giant vegetables",
    ),
    StoryParams(
        crop="squash",
        route="mud_hill",
        trouble="split",
        lesson="fence_post_brace",
        fix="board_brace",
        hero_name="Sadie",
        hero_gender="girl",
        delay=2,
        prize="the grand champion squash",
    ),
]


def outcome_of(params: StoryParams) -> str:
    crop = CROPS[params.crop]
    trouble = TROUBLES[params.trouble]
    fix = FIXES[params.fix]
    return "saved" if fix_holds(crop, trouble, fix, params.delay) else "burst"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(C, R, T, L) :- crop(C), route(R), trouble(T), lesson(L),
                     route_has(R, T), needs(T, S), teaches(L, S).

sensible(F) :- fix(F), sense(F, X), sense_min(M), X >= M.
compatible(T, F) :- trouble(T), fix(F), handles(F, T).
compatible(T, F) :- trouble(T), needs(T, S), teaches_fix(F, S).

% --- outcome model ---------------------------------------------------------
load(V) :- chosen_crop(C), chosen_trouble(T), chosen_delay(D),
           crop_size(C, CS), severity(T, TS), V = CS + TS + D.
holds :- chosen_fix(F), chosen_trouble(T), compatible(T, F),
         power(F, P), load(V), P >= V.

outcome(saved) :- holds.
outcome(burst) :- not holds.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for crop_id, crop in CROPS.items():
        lines.append(asp.fact("crop", crop_id))
        lines.append(asp.fact("crop_size", crop_id, crop.size))
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        for trouble in sorted(route.trouble_spots):
            lines.append(asp.fact("route_has", route_id, trouble))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("severity", trouble_id, trouble.severity))
        for need in sorted(trouble.needs):
            lines.append(asp.fact("needs", trouble_id, need))
    for lesson_id, lesson in LESSONS.items():
        lines.append(asp.fact("lesson", lesson_id))
        lines.append(asp.fact("teaches", lesson_id, lesson.skill))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
        for handle in sorted(fix.handles):
            lines.append(asp.fact("teaches_fix", fix_id, handle))
            if handle in TROUBLES:
                lines.append(asp.fact("handles", fix_id, handle))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(item for (item,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_crop", params.crop),
        asp.fact("chosen_trouble", params.trouble),
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    python_sensible = {f.id for f in sensible_fixes()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible fixes match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
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
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a giant fair crop, a road problem, and a flashback fix."
    )
    ap.add_argument("--crop", choices=sorted(CROPS))
    ap.add_argument("--route", choices=sorted(ROUTES))
    ap.add_argument("--trouble", choices=sorted(TROUBLES))
    ap.add_argument("--lesson", choices=sorted(LESSONS))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra head start for the trouble")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.trouble and args.lesson:
        route = ROUTES[args.route]
        trouble = TROUBLES[args.trouble]
        lesson = LESSONS[args.lesson]
        if not (args.trouble in route.trouble_spots and lesson.skill in trouble.needs):
            raise StoryError(explain_combo_rejection(route, trouble, lesson))
    if args.fix:
        fix = FIXES[args.fix]
        if fix.sense < SENSE_MIN:
            raise StoryError(explain_fix_rejection(fix))

    combos = [
        combo for combo in valid_combos()
        if (args.crop is None or combo[0] == args.crop)
        and (args.route is None or combo[1] == args.route)
        and (args.trouble is None or combo[2] == args.trouble)
        and (args.lesson is None or combo[3] == args.lesson)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    crop_id, route_id, trouble_id, lesson_id = rng.choice(sorted(combos))
    trouble = TROUBLES[trouble_id]
    compatible = [fix.id for fix in sensible_fixes() if compatible_fix(trouble, fix)]
    if args.fix is not None:
        if args.fix not in compatible:
            raise StoryError(
                f"(No story: fix '{args.fix}' does not honestly match the '{trouble_id}' problem. "
                f"Pick one of: {', '.join(sorted(compatible))}.)"
            )
        fix_id = args.fix
    else:
        fix_id = rng.choice(sorted(compatible))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = NAMES_GIRL if gender == "girl" else NAMES_BOY
    name = args.name or rng.choice(name_pool)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    prize = rng.choice(PRIZES)
    return StoryParams(
        crop=crop_id,
        route=route_id,
        trouble=trouble_id,
        lesson=lesson_id,
        fix=fix_id,
        hero_name=name,
        hero_gender=gender,
        delay=delay,
        prize=prize,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        crop = CROPS[params.crop]
        route = ROUTES[params.route]
        trouble = TROUBLES[params.trouble]
        lesson = LESSONS[params.lesson]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if params.trouble not in route.trouble_spots or lesson.skill not in trouble.needs:
        raise StoryError(explain_combo_rejection(route, trouble, lesson))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(fix))
    if not compatible_fix(trouble, fix):
        raise StoryError(
            f"(No story: {fix.label} does not match the '{trouble.label}' problem in this world.)"
        )

    world = tell(
        crop=crop,
        route=route,
        trouble=trouble,
        lesson=lesson,
        fix=fix,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        delay=params.delay,
        prize=params.prize,
    )
    world.get("hero").label = params.hero_name

    story = world.render().replace("hero", params.hero_name)
    story = story.replace("hero's", f"{params.hero_name}'s")
    story = story.replace("hero ", f"{params.hero_name} ")

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible()
        print(f"sensible fixes: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (crop, route, trouble, lesson) combos:\n")
        for crop, route, trouble, lesson in combos:
            print(f"  {crop:8} {route:12} {trouble:8} {lesson}")
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
            header = (
                f"### {p.hero_name}: {p.crop} on {p.route} "
                f"({p.trouble}, {p.fix}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
