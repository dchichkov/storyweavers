#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gasoline_grab_gristle_foreshadowing_sharing_superhero_story.py
==========================================================================================

A standalone story world for a small superhero-style tale about children who want
their pretend rescue ride to go faster, notice a red can of gasoline, and learn
that real danger is not a toy. The story uses clear foreshadowing and ends with
sharing: the children solve their mission by taking turns and sharing jobs instead
of grabbing a dangerous shortcut.

Run it
------
python storyworlds/worlds/gpt-5.4/gasoline_grab_gristle_foreshadowing_sharing_superhero_story.py
python storyworlds/worlds/gpt-5.4/gasoline_grab_gristle_foreshadowing_sharing_superhero_story.py --all
python storyworlds/worlds/gpt-5.4/gasoline_grab_gristle_foreshadowing_sharing_superhero_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/gasoline_grab_gristle_foreshadowing_sharing_superhero_story.py --verify
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
BOLD_INIT = 6.0
CAREFUL_TRAITS = {"careful", "cautious", "thoughtful", "steady"}
SHARING_TRAITS = {"generous", "kind", "helpful", "steady"}


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
    flammable: bool = False
    rollable: bool = False
    shareable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    danger: str
    callout: str
    goal: str
    ending: str
    support_tags: set[str] = field(default_factory=set)
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
class Vehicle:
    id: str
    label: str
    phrase: str
    launch_line: str
    spill_scale: int
    rollable: bool = True
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
class SharedTool:
    id: str
    label: str
    phrase: str
    use_line: str
    swap_line: str
    supports: set[str] = field(default_factory=set)
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
class Fuel:
    id: str
    label: str
    phrase: str
    smell: str
    lesson: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


def _r_fumes(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    for ent in list(world.entities.values()):
        if ent.meters["gasoline_open"] < THRESHOLD:
            continue
        sig = ("fumes", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        room.meters["danger"] += 1
        room.meters["smell"] += 1
        for kid in world.kids():
            kid.memes["worry"] += 1
        out.append("__fumes__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["gasoline_spilled"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["slick"] += 1
        world.get("room").meters["danger"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__spill__")
    return out


def _r_grab_conflict(world: World) -> list[str]:
    a = world.get("instigator")
    b = world.get("cautioner")
    if a.memes["grabby"] < THRESHOLD:
        return []
    sig = ("grab_conflict", "kids")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    return ["__grab__"]


CAUSAL_RULES = [
    Rule(name="fumes", tag="physical", apply=_r_fumes),
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="grab_conflict", tag="social", apply=_r_grab_conflict),
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


def sharing_strength(trait: str) -> float:
    return 5.0 if trait in SHARING_TRAITS else 3.0


def careful_strength(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = careful_strength(trait) + 1.0 + (3.0 if older_sibling else 0.0)
    return older_sibling and authority > BOLD_INIT


def vehicle_at_risk(vehicle: Vehicle) -> bool:
    return vehicle.rollable


def compatible_tool(mission: Mission, tool: SharedTool) -> bool:
    return mission.id in tool.supports


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def spill_severity(vehicle: Vehicle, delay: int) -> int:
    return vehicle.spill_scale + delay


def is_contained(response: Response, vehicle: Vehicle, delay: int) -> bool:
    return response.power >= spill_severity(vehicle, delay)


def predict_danger(world: World) -> dict:
    sim = world.copy()
    can = sim.get("fuel")
    ride = sim.get("vehicle")
    can.meters["gasoline_open"] += 1
    can.meters["gasoline_spilled"] += 1
    ride.meters["gasoline_spilled"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("room").meters["danger"],
        "slick": ride.meters["slick"],
    }


def play_setup(world: World, a: Entity, b: Entity, mission: Mission, vehicle: Vehicle, dog: str) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["hero"] += 1
    world.say(
        f"After lunch, {a.id} and {b.id} turned the driveway into {mission.scene}. "
        f"{vehicle.phrase} became their rescue ride, and the chalk line by the fence "
        f"became the edge of danger."
    )
    if dog:
        world.say(f"Their little dog, {dog}, trotted after them like a sidekick in a comic book.")
    world.say(f'"{mission.callout}" {a.id} cried. "To {mission.goal}!"')


def foreshadow(world: World, parent: Entity, fuel: Fuel) -> None:
    world.say(
        f"Near the garage door sat {fuel.phrase}. Even before anyone touched it, "
        f"the air held {fuel.smell}, and a little sign over the workbench said, "
        f'"No sparks near the red can."'
    )
    world.say(
        f"{parent.label_word.capitalize()} had said that same thing before, which made the can feel less like treasure and more like trouble waiting its turn."
    )


def need_speed(world: World, b: Entity, vehicle: Vehicle, mission: Mission) -> None:
    world.say(
        f"But the rescue ride felt slow. {b.id} pushed {vehicle.label} a little way and watched it wobble."
    )
    world.say(
        f'"If we are going to {mission.goal}, we need a faster launch," {b.id} said.'
    )


def tempt(world: World, a: Entity, fuel: Fuel) -> None:
    a.memes["bold"] += 1
    world.say(
        f"{a.id}'s eyes shone. "
        f'"I know what could make it zoom -- {fuel.label}!"'
    )
    world.say(
        f"{a.pronoun().capitalize()} pointed at the red can and took a step as if to grab it."
    )


def warn(world: World, b: Entity, a: Entity, fuel: Fuel, parent: Entity) -> None:
    pred = predict_danger(world)
    b.memes["care"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_slick"] = pred["slick"]
    extra = ""
    if careful_strength(next(iter(b.traits), "")) >= 5.0:
        extra = f" {b.pronoun().capitalize()} sounded very sure."
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "{fuel.label.capitalize()} is not superhero fuel," '
        f'{b.pronoun()} said. "It makes dangerous fumes, and if it spills the floor gets slick."{extra}'
    )
    world.say(
        f'"Let\'s call {parent.label_word} instead of touching it."'
    )


def defy(world: World, a: Entity, fuel: Fuel) -> None:
    a.memes["grabby"] += 1
    a.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But the fast idea still sparkled in {a.id}\'s head. "{fuel.label.capitalize()} is real engine stuff," {a.pronoun()} said. "Maybe just a tiny bit."'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["bold"] = 0.0
    world.say(
        f"{a.id} looked at the can, then at {b.id}'s serious face, and stopped with {a.pronoun('possessive')} hand in the air."
    )
    world.say(
        f'"You are right," {a.pronoun()} said. "Let\'s not touch it. Let\'s get {parent.label_word}."'
    )


def open_and_spill(world: World, a: Entity, fuel: Fuel, vehicle: Entity) -> None:
    can = world.get("fuel")
    can.meters["gasoline_open"] += 1
    can.meters["gasoline_spilled"] += 1
    vehicle.meters["gasoline_spilled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} did grab the can. The cap twisted loose, and a little splash of {fuel.label} sloshed onto one wheel and the concrete below."
    )
    world.say(
        f"At once the sharp smell grew bigger, and the shiny puddle looked wrong in a place meant for play."
    )


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"Stop!" {b.id} cried. "{parent.label_word.capitalize()}!"')


def rescue(world: World, parent: Entity, response: Response) -> None:
    can = world.get("fuel")
    vehicle = world.get("vehicle")
    can.meters["gasoline_open"] = 0.0
    can.meters["gasoline_spilled"] = 0.0
    vehicle.meters["gasoline_spilled"] = 0.0
    vehicle.meters["slick"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came quickly and {response.text}."
    )
    world.say(
        "Soon the sharp smell faded, the shiny patch was gone, and the driveway felt safe again."
    )


def rescue_fail(world: World, parent: Entity, response: Response) -> None:
    world.get("room").meters["danger"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {response.fail}."
    )
    world.say(
        "The smell stayed too strong for play, so the rescue mission had to stop for the day."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, fuel: Fuel) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"Then {parent.label_word} knelt beside them. "
        f'"You were right to call me," {parent.pronoun()} said softly. '
        f'"{fuel.lesson}. Real helpers ask before they touch dangerous things."'
    )


def sharing_plan(world: World, a: Entity, b: Entity, tool: SharedTool, vehicle: Vehicle, mission: Mission, next_day: bool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["sharing"] += 1
    opener = "The next morning" if next_day else "A little later"
    world.say(
        f"{opener}, they tried a different kind of hero plan. They brought out {tool.phrase} and set {vehicle.label} back on the chalk road."
    )
    world.say(
        f"{a.id} and {b.id} decided not to grab the same job. {tool.use_line}"
    )
    world.say(tool.swap_line.replace("{a}", a.id).replace("{b}", b.id))
    world.say(
        f"That made the whole mission feel bigger, not smaller, because each hero helped the other. Together they {mission.ending}."
    )


def tell(
    mission: Mission,
    vehicle_cfg: Vehicle,
    tool_cfg: SharedTool,
    fuel: Fuel,
    response: Response,
    instigator: str = "Kai",
    instigator_gender: str = "boy",
    cautioner: str = "Mina",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 7,
    relation: str = "siblings",
    dog_name: str = "Gristle",
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"name": instigator, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"name": cautioner, "relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    room = world.add(Entity(id="room", type="driveway", label="the driveway"))
    _ = room
    world.add(Entity(
        id="vehicle",
        type="vehicle",
        label=vehicle_cfg.label,
        rollable=vehicle_cfg.rollable,
    ))
    world.add(Entity(
        id="fuel",
        type="can",
        label=fuel.label,
        flammable=True,
    ))
    world.facts["dog_name"] = dog_name
    world.facts["relation"] = relation
    a.memes["bold"] = BOLD_INIT
    b.memes["care"] = careful_strength(trait)
    b.memes["sharing"] = sharing_strength(trait)

    play_setup(world, a, b, mission, vehicle_cfg, dog_name)
    foreshadow(world, parent, fuel)
    need_speed(world, b, vehicle_cfg, mission)

    world.para()
    tempt(world, a, fuel)
    warn(world, b, a, fuel, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, parent)
        world.para()
        lesson(world, parent, a, b, fuel)
        world.para()
        sharing_plan(world, a, b, tool_cfg, vehicle_cfg, mission, next_day=False)
        severity = 0
        contained = True
        outcome = "averted"
    else:
        defy(world, a, fuel)
        world.para()
        open_and_spill(world, a, fuel, world.get("vehicle"))
        alarm(world, b, parent)
        severity = spill_severity(vehicle_cfg, delay)
        world.get("vehicle").meters["severity"] = float(severity)
        contained = is_contained(response, vehicle_cfg, delay)
        world.para()
        if contained:
            rescue(world, parent, response)
            lesson(world, parent, a, b, fuel)
            world.para()
            sharing_plan(world, a, b, tool_cfg, vehicle_cfg, mission, next_day=False)
            outcome = "cleaned"
        else:
            rescue_fail(world, parent, response)
            lesson(world, parent, a, b, fuel)
            world.para()
            sharing_plan(world, a, b, tool_cfg, vehicle_cfg, mission, next_day=True)
            outcome = "postponed"

    world.facts.update(
        mission=mission,
        vehicle_cfg=vehicle_cfg,
        tool_cfg=tool_cfg,
        fuel=fuel,
        response=response,
        instigator=a,
        cautioner=b,
        parent=parent,
        outcome=outcome,
        severity=severity,
        delay=delay,
        averted=averted,
        contained=contained,
        spilled=(outcome != "averted"),
        shared=True,
    )
    return world


MISSIONS = {
    "kitten": Mission(
        id="kitten",
        scene="Hero Alley, where every flowerpot could hide a secret",
        danger="Captain Zoom! Sidekick Shield! A kitten is trapped on the wall!",
        goal="save the pretend kitten on the garden wall",
        ending="rolled to the flowerpot fort, saluted the rescued kitten, and cheered",
        support_tags={"map", "bell"},
    ),
    "snacks": Mission(
        id="snacks",
        scene="Rescue Lane, where hungry neighbors waited for help",
        danger="Captain Zoom! Sidekick Shield! Snack rescue needs us now!",
        goal="deliver raisins and apple slices to the porch heroes",
        ending="delivered the snacks with big grins and superhero bows",
        support_tags={"basket", "map"},
    ),
    "cape": Mission(
        id="cape",
        scene="Cloud Street, where a windy fence looked like the top of a tower",
        danger="Captain Zoom! Sidekick Shield! A cape is flapping loose!",
        goal="save the cape from the windy fence",
        ending="reached the windy fence, untangled the cape, and let it fly behind them safely",
        support_tags={"clip", "bell"},
    ),
}

VEHICLES = {
    "wagon": Vehicle(
        id="wagon",
        label="the wagon",
        phrase="An old red wagon with a pillow inside",
        launch_line="They planted their feet as if a rocket launch were coming",
        spill_scale=1,
        rollable=True,
        tags={"wagon"},
    ),
    "crate_cart": Vehicle(
        id="crate_cart",
        label="the crate cart",
        phrase="A wooden crate on little wheels",
        launch_line="They crouched beside it like engineers at a moon base",
        spill_scale=2,
        rollable=True,
        tags={"cart"},
    ),
    "box_car": Vehicle(
        id="box_car",
        label="the cardboard rescue car",
        phrase="A cardboard box car taped to a low scooter board",
        launch_line="They counted down with their capes puffing behind them",
        spill_scale=2,
        rollable=True,
        tags={"car"},
    ),
    "cape_stack": Vehicle(
        id="cape_stack",
        label="the cape pile",
        phrase="A wobbling pile of folded capes",
        launch_line="They looked at it and laughed",
        spill_scale=0,
        rollable=False,
        tags={"capes"},
    ),
}

TOOLS = {
    "map": SharedTool(
        id="map",
        label="map",
        phrase="one crayon map",
        use_line="First {a} held the map while {b} pulled. Then they switched so each hero got a turn to lead.",
        swap_line="{a} pointed the next turn, and then {b} pointed the one after that.",
        supports={"kitten", "snacks"},
        tags={"map", "sharing"},
    ),
    "bell": SharedTool(
        id="bell",
        label="bell",
        phrase="one silver handlebar bell",
        use_line="First {a} rang the bell while {b} pulled. Then they traded places and the bell chimed for both of them.",
        swap_line="The bright ding-ding let {a} and {b} feel like one team instead of two kids tugging at the same moment.",
        supports={"kitten", "cape"},
        tags={"bell", "sharing"},
    ),
    "basket": SharedTool(
        id="basket",
        label="basket",
        phrase="one snack basket",
        use_line="First {a} carried the basket while {b} steered. Then they traded, so each hero carried part of the mission.",
        swap_line="By the last porch, {a} and {b} were swapping jobs without even being asked.",
        supports={"snacks"},
        tags={"basket", "sharing"},
    ),
    "clip": SharedTool(
        id="clip",
        label="clip",
        phrase="one giant clothespin clip",
        use_line="First {a} held the clip while {b} pushed. Then they switched so both hands got a hero turn.",
        swap_line="{a} laughed when the clip snapped shut, and {b} laughed too.",
        supports={"cape"},
        tags={"clip", "sharing"},
    ),
}

FUELS = {
    "gasoline": Fuel(
        id="gasoline",
        label="gasoline",
        phrase="a red can of gasoline",
        smell="a sharp gasoline smell",
        lesson="Gasoline is for grown-up machines, not for play, and even a little spill can make a place unsafe",
        tags={"gasoline", "flammable"},
    ),
}

RESPONSES = {
    "absorbent": Response(
        id="absorbent",
        sense=3,
        power=3,
        text="sprinkled absorbent over the spill, rolled the wagon aside, and cleaned the spot carefully before putting the can high out of reach",
        fail="sprinkled absorbent and wiped the spot, but the smell was still too strong to keep playing nearby",
        qa_text="cleaned the spill with absorbent and moved the can away",
        tags={"cleanup", "safe_help"},
    ),
    "garage_kit": Response(
        id="garage_kit",
        sense=3,
        power=4,
        text="opened the garage cleanup kit, covered the spill, and scrubbed until the wheel and the floor were safe again",
        fail="used the garage cleanup kit, but the area still needed more time to air out",
        qa_text="used the garage cleanup kit to make the spill safe",
        tags={"cleanup", "safe_help"},
    ),
    "rag_only": Response(
        id="rag_only",
        sense=1,
        power=1,
        text="wiped at the spill with one rag",
        fail="wiped at the spill with one rag, but that was not enough to make the area safe",
        qa_text="wiped at the spill with one rag",
        tags={"cleanup"},
    ),
}

GIRL_NAMES = ["Mina", "Ava", "Lila", "Nora", "Ruby", "Zoe", "Ella", "Maya"]
BOY_NAMES = ["Kai", "Ben", "Leo", "Max", "Eli", "Noah", "Finn", "Theo"]
TRAITS = ["careful", "cautious", "thoughtful", "steady", "kind", "helpful", "generous"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for mission_id, mission in MISSIONS.items():
        for vehicle_id, vehicle in VEHICLES.items():
            for tool_id, tool in TOOLS.items():
                if vehicle_at_risk(vehicle) and compatible_tool(mission, tool):
                    combos.append((mission_id, vehicle_id, tool_id))
    return combos


@dataclass
class StoryParams:
    mission: str
    vehicle: str
    tool: str
    fuel: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 7
    relation: str = "siblings"
    dog_name: str = "Gristle"
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
    "gasoline": [(
        "What is gasoline?",
        "Gasoline is a fuel for engines like cars or lawn tools. It has a strong smell, and children should never touch it."
    )],
    "flammable": [(
        "Why is gasoline dangerous?",
        "Gasoline can make dangerous fumes and can catch fire very easily. Even a small spill can make a place unsafe."
    )],
    "cleanup": [(
        "What should a child do after a dangerous spill?",
        "Step back and call a grown-up right away. A grown-up can clean it with the right tools and keep everyone safe."
    )],
    "sharing": [(
        "What does sharing mean in a team?",
        "Sharing means taking turns and letting everyone help. A team works better when no one tries to grab every job."
    )],
    "map": [(
        "What does a map help you do?",
        "A map helps you know where to go. In pretend play, it can make a mission feel real and help a team lead together."
    )],
    "bell": [(
        "What is a handlebar bell for?",
        "A handlebar bell makes a bright sound to let people know you are coming. It can also make a pretend rescue ride feel exciting."
    )],
    "basket": [(
        "What is a basket good for?",
        "A basket can carry snacks or small things from one place to another. Sharing one basket means each person can help with the job."
    )],
    "clip": [(
        "What can a giant clothespin clip do?",
        "A big clip can hold cloth or paper in place. In pretend play, it can become a superhero tool for a rescue mission."
    )],
}
KNOWLEDGE_ORDER = ["gasoline", "flammable", "cleanup", "sharing", "map", "bell", "basket", "clip"]


def kid_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


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
    a = kid_name(f["instigator"])
    b = kid_name(f["cautioner"])
    mission = f["mission"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short superhero story for a 3-to-5-year-old where two children see gasoline near their pretend rescue ride and learn a safer way to play. Include the words "gasoline" and "grab".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle superhero tale where {a} almost tries to grab a red can, but {b} notices the danger first and stops the mistake before anything spills.",
            f"Write a story with foreshadowing, one shared {tool.label}, and a happy ending where teamwork matters more than speed.",
        ]
    if outcome == "postponed":
        return [
            base,
            f"Tell a cautionary superhero story where {a} does grab the gasoline can, the mission must pause, and the children try again safely the next day by sharing one {tool.label}.",
            f"Write a story that uses foreshadowing to hint the red can is trouble, then ends with a calmer shared mission after a grown-up helps.",
        ]
    return [
        base,
        f"Tell a superhero story where {a} reaches for gasoline to make a toy ride faster, but a grown-up cleans the spill and the children solve the mission by sharing one {tool.label}.",
        f"Write a story with a clear warning beat, a quick cleanup, and an ending that shows sharing is better than grabbing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a_ent = f["instigator"]
    b_ent = f["cautioner"]
    parent = f["parent"]
    mission = f["mission"]
    vehicle = f["vehicle_cfg"]
    tool = f["tool_cfg"]
    fuel = f["fuel"]
    response = f["response"]
    a = kid_name(a_ent)
    b = kid_name(b_ent)
    pair = pair_noun(a_ent, b_ent, f.get("relation", "friends"))
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a} and {b}, playing superheroes in the driveway. Their grown-up helps when the pretend mission bumps into a real danger."
        ),
        (
            "What mission were the children pretending to do?",
            f"They were pretending to {mission.goal}. The superhero game made the slow little ride feel like a real rescue machine."
        ),
        (
            f"Why did {b} warn {a} about the {fuel.label}?",
            f"{b} warned {a} because {fuel.label} was not a toy and the story had already hinted it was trouble through the smell and the warning sign. {b} knew a spill could make dangerous fumes and a slick floor."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What happened when {a} was about to grab the can?",
            f"{a} stopped before touching it. {b}'s warning worked, so the danger stayed only a warning and never became a spill."
        ))
    else:
        qa.append((
            f"What happened when {a} did grab the can?",
            f"A little splash of gasoline sloshed onto {vehicle.label} and the concrete. That made the place smell sharper and turned the pretend mission into a real problem."
        ))
        if f["outcome"] == "cleaned":
            qa.append((
                "How did the grown-up fix the problem?",
                f"{parent.label_word.capitalize()} {response.qa_text}. That made the driveway safe again before the children went back to play."
            ))
        else:
            qa.append((
                "Could they keep playing right away?",
                f"No. Even after {parent.label_word} tried to help, the smell stayed too strong for play that day. They had to wait and come back to the mission later."
            ))
    qa.append((
        "How did sharing help at the end?",
        f"They stopped trying to grab the same exciting job and used {tool.phrase} by taking turns. Sharing turned them back into a real superhero team because each child got to help."
    ))
    qa.append((
        "Who is Gristle in the story?",
        "Gristle is the little dog trotting along like a sidekick. The name adds a funny superhero flavor while the children learn a serious safety lesson."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["fuel"].tags) | set(f["tool_cfg"].tags) | set(f["response"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (("flammable", e.flammable), ("rollable", e.rollable), ("shareable", e.shareable)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:11} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="kitten",
        vehicle="wagon",
        tool="bell",
        fuel="gasoline",
        response="garage_kit",
        instigator="Kai",
        instigator_gender="boy",
        cautioner="Mina",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        dog_name="Gristle",
    ),
    StoryParams(
        mission="snacks",
        vehicle="crate_cart",
        tool="basket",
        fuel="gasoline",
        response="absorbent",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Leo",
        cautioner_gender="boy",
        parent="father",
        trait="steady",
        delay=0,
        instigator_age=7,
        cautioner_age=6,
        relation="friends",
        dog_name="Gristle",
    ),
    StoryParams(
        mission="cape",
        vehicle="box_car",
        tool="clip",
        fuel="gasoline",
        response="absorbent",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Ruby",
        cautioner_gender="girl",
        parent="mother",
        trait="helpful",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        dog_name="Gristle",
    ),
]


def explain_rejection(vehicle: Vehicle, tool: SharedTool, mission: Mission) -> str:
    if not vehicle.rollable:
        return (
            f"(No story: {vehicle.label} cannot roll, so children would have no reason to imagine gasoline making it go faster. "
            f"Pick a ride like a wagon or cart instead.)"
        )
    return (
        f"(No story: {tool.phrase} does not fit the {mission.id} mission well enough to make sharing the ending feel honest. "
        f"Pick a tool that actually helps with that mission.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "cleaned" if is_contained(RESPONSES[params.response], VEHICLES[params.vehicle], params.delay) else "postponed"


ASP_RULES = r"""
% valid setup: rollable ride + a shared tool that really supports the mission
valid(M, V, T) :- mission(M), vehicle(V), tool(T), rollable(V), supports(T, M).

% outcome model
careful_now(T) :- trait(T), careful_trait(T).
init_care(5) :- careful_now(T), trait(T).
init_care(3) :- trait(T), not careful_now(T).
older_sibling :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
authority(C + 1 + B) :- init_care(C), older_bonus(B).
older_bonus(3) :- older_sibling.
older_bonus(0) :- not older_sibling.
averted :- older_sibling, authority(A), bold_init(B), A > B.

severity(SP + D) :- chosen_vehicle(V), spill_scale(V, SP), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(cleaned) :- not averted, contained.
outcome(postponed) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for vid, vehicle in VEHICLES.items():
        lines.append(asp.fact("vehicle", vid))
        if vehicle.rollable:
            lines.append(asp.fact("rollable", vid))
        lines.append(asp.fact("spill_scale", vid, vehicle.spill_scale))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for mid in sorted(tool.supports):
            lines.append(asp.fact("supports", tid, mid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("bold_init", int(BOLD_INIT)))
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

    scenario = "\n".join([
        asp.fact("chosen_vehicle", params.vehicle),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    sensible = {r.id for r in sensible_responses()}
    if sensible == {"absorbent", "garage_kit"}:
        print(f"OK: sensible responses match ({sorted(sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(80):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(s))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params failed under seed {s}")
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
            raise StoryError("smoke test produced empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero story world: children spot gasoline near a pretend rescue ride and learn sharing instead of grabbing."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fuel", choices=FUELS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long cleanup takes before the space feels safe")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible setup triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vehicle and not VEHICLES[args.vehicle].rollable:
        mission = MISSIONS[args.mission] if args.mission else next(iter(MISSIONS.values()))
        tool = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
        raise StoryError(explain_rejection(VEHICLES[args.vehicle], tool, mission))
    if args.mission and args.tool:
        mission = MISSIONS[args.mission]
        tool = TOOLS[args.tool]
        vehicle = VEHICLES[args.vehicle] if args.vehicle else next(v for v in VEHICLES.values() if v.rollable)
        if not (vehicle_at_risk(vehicle) and compatible_tool(mission, tool)):
            raise StoryError(explain_rejection(vehicle, tool, mission))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.mission is None or c[0] == args.mission)
        and (args.vehicle is None or c[1] == args.vehicle)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, vehicle_id, tool_id = rng.choice(sorted(combos))
    fuel_id = args.fuel or "gasoline"
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        mission=mission_id,
        vehicle=vehicle_id,
        tool=tool_id,
        fuel=fuel_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        dog_name="Gristle",
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.vehicle not in VEHICLES:
        raise StoryError(f"(Unknown vehicle: {params.vehicle})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.fuel not in FUELS:
        raise StoryError(f"(Unknown fuel: {params.fuel})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    mission = MISSIONS[params.mission]
    vehicle = VEHICLES[params.vehicle]
    tool = TOOLS[params.tool]
    fuel = FUELS[params.fuel]
    response = RESPONSES[params.response]
    if not vehicle_at_risk(vehicle) or not compatible_tool(mission, tool):
        raise StoryError(explain_rejection(vehicle, tool, mission))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        mission=mission,
        vehicle_cfg=vehicle,
        tool_cfg=tool,
        fuel=fuel,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        dog_name=params.dog_name,
    )

    # Replace internal ids with child-facing names in the final story.
    story = world.render().replace("instigator", params.instigator).replace("cautioner", params.cautioner)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, vehicle, tool) combos:\n")
        for mission, vehicle, tool in combos:
            print(f"  {mission:8} {vehicle:10} {tool}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.mission} with {p.vehicle} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
