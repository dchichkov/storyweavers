#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pram_lake_flashback_nursery_rhyme.py
===============================================================

A standalone story world for a tiny, nursery-rhyme-flavored tale about a child,
a pram, and a lake. The central pattern is:

- a cozy outing to the lake with a toy riding in a pram
- a safety rule that matters because the path can slope toward the water
- a brief danger when the pram begins to roll
- a flashback to a remembered rhyme lesson
- a state-driven fix and an ending image that proves the child learned

This world refuses combinations that would not make honest sense. A flat picnic
green does not make a runaway-pram story; a stopping method that cannot stop the
motion is rejected. The inline ASP twin mirrors both the reasonableness gate and
the outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/pram_lake_flashback_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/pram_lake_flashback_nursery_rhyme.py --path willow_bank
    python storyworlds/worlds/gpt-5.4/pram_lake_flashback_nursery_rhyme.py --path meadow
    python storyworlds/worlds/gpt-5.4/pram_lake_flashback_nursery_rhyme.py --stop hand_only
    python storyworlds/worlds/gpt-5.4/pram_lake_flashback_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/pram_lake_flashback_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/pram_lake_flashback_nursery_rhyme.py --verify
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
class Path:
    id: str
    label: str
    phrase: str
    rhyme_place: str
    texture: str
    slope: int
    edge: str
    safe_spot: str
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
class Rider:
    id: str
    label: str
    phrase: str
    sound: str
    plural: bool = False
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
class Reminder:
    id: str
    elder_type: str
    elder_label: str
    earlier_time: str
    action: str
    rhyme: str
    lesson: str
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
class StopMethod:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    needs_memory: bool = False
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


def _r_rolling_worry(world: World) -> list[str]:
    pram = world.get("pram")
    child = world.get("child")
    if pram.meters["rolling"] < THRESHOLD:
        return []
    sig = ("rolling_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    world.get("lake").meters["risk"] += 1
    return ["__rolling__"]


def _r_splash(world: World) -> list[str]:
    pram = world.get("pram")
    rider = world.get("rider")
    child = world.get("child")
    if pram.meters["in_lake"] < THRESHOLD:
        return []
    sig = ("splash",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rider.meters["wet"] += 1
    child.memes["sad"] += 1
    child.memes["worry"] += 1
    return ["__splash__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="rolling_worry", tag="motion", apply=_r_rolling_worry),
    Rule(name="splash", tag="motion", apply=_r_splash),
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


def hazard_at_risk(path: Path) -> bool:
    return path.slope > 0


def sensible_stops() -> list[StopMethod]:
    return [m for m in STOP_METHODS.values() if m.sense >= SENSE_MIN]


def runaway_severity(path: Path, pause: int) -> int:
    return path.slope + pause


def memory_available(path: Path, pause: int) -> bool:
    return runaway_severity(path, pause) >= 2


def can_stop(method: StopMethod, path: Path, pause: int) -> bool:
    if method.needs_memory and not memory_available(path, pause):
        return False
    return method.power >= runaway_severity(path, pause)


def best_stop() -> StopMethod:
    return max(STOP_METHODS.values(), key=lambda m: (m.sense, m.power))


def predict_runaway(world: World) -> dict:
    sim = world.copy()
    start_roll(sim, narrate=False)
    return {
        "rolling": sim.get("pram").meters["rolling"] >= THRESHOLD,
        "risk": sim.get("lake").meters["risk"],
    }


def introduce(world: World, child: Entity, rider: Rider, path: Path) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} took a toy pram to the lake, "
        f"tripping along {path.phrase} with {rider.phrase} tucked inside."
    )
    world.say(
        f"Round went the little wheels, {rider.sound}, "
        f"while the lake made silver wiggles beside the path."
    )


def lake_rhyme(world: World, child: Entity, rider: Rider, path: Path) -> None:
    world.say(
        f'"Pram by the lake, do not rush or shake," {child.id} sang, '
        f"just to hear the words bounce nicely."
    )
    world.say(
        f"The {path.texture} path curved near {path.edge}, and the ducks floated "
        f"like bobbing buttons on the water."
    )


def pause_for_ducks(world: World, child: Entity, rider: Rider, path: Path) -> None:
    world.say(
        f"{child.id} stopped near {path.edge} to show the ducks to {rider.label}. "
        f"The toy pram pointed a little downhill toward the water."
    )


def warn(world: World, child: Entity, caregiver: Entity, reminder: Reminder, path: Path) -> None:
    pred = predict_runaway(world)
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f'{caregiver.label_word.capitalize()} said, "Mind the brake, dear heart. '
        f'{path.rhyme_place} is lovely, but a wheel can wander."'
    )
    if pred["risk"] >= THRESHOLD:
        world.say(
            f"{child.id} nodded, because even a tiny roll on {path.label} "
            f"could send the pram toward the lake."
        )


def forget(world: World, child: Entity) -> None:
    child.memes["distracted"] += 1
    world.say(
        f"But a bright feather skittered by, and {child.id} bent to pick it up. "
        f"In that little moment, the brake was forgotten."
    )


def start_roll(world: World, narrate: bool = True) -> None:
    pram = world.get("pram")
    pram.meters["rolling"] += 1
    pram.meters["distance_to_lake"] = max(0.0, pram.meters["distance_to_lake"] - 1.0)
    propagate(world, narrate=narrate)


def rolling_beat(world: World, path: Path) -> None:
    world.say(
        f"Tip and tick, tick and tip -- the toy pram gave a shiver, then rolled "
        f"down {path.phrase} toward the lake."
    )


def flashback(world: World, child: Entity, reminder: Reminder, path: Path) -> None:
    child.memes["memory"] += 1
    child.memes["care"] += 1
    world.say(
        f"Then, like a bell in the middle of the fright, a flashback fluttered in."
    )
    world.say(
        f"{reminder.earlier_time}, {reminder.elder_label} had {reminder.action} and said, "
        f'"{reminder.rhyme}"'
    )
    world.say(
        f"The remembered rhyme landed in {child.id}'s mind as neatly as a pebble "
        f"landing in a pail."
    )


def stop_pram(world: World, child: Entity, method: StopMethod, path: Path) -> None:
    pram = world.get("pram")
    pram.meters["rolling"] = 0.0
    pram.meters["stopped"] += 1
    pram.meters["distance_to_lake"] = max(1.0, pram.meters["distance_to_lake"])
    child.memes["relief"] += 1
    body = method.text
    world.say(
        f"{child.id} {body}, and the toy pram stopped at {path.safe_spot} with one "
        f"last tiny wobble."
    )


def lake_splash(world: World, child: Entity, rider: Rider, caregiver: Entity) -> None:
    pram = world.get("pram")
    pram.meters["rolling"] = 0.0
    pram.meters["in_lake"] += 1
    pram.meters["distance_to_lake"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Plop! The front wheels kissed the edge, and the toy pram tipped into the "
        f"shallow water. {rider.label.capitalize()} came up wet, and {child.id}'s "
        f"eyes filled with tears."
    )
    world.say(
        f"{caregiver.label_word.capitalize()} hurried over, lifted the toy pram out, "
        f"and wrapped {rider.label} in a dry towel from the bag."
    )


def lesson(world: World, child: Entity, caregiver: Entity, reminder: Reminder, happy: bool) -> None:
    child.memes["lesson"] += 1
    child.memes["worry"] = 0.0
    child.memes["sad"] = 0.0 if happy else child.memes["sad"]
    world.say(
        f'{caregiver.label_word.capitalize()} knelt beside {child.id} and spoke softly. '
        f'"{reminder.lesson}"'
    )
    if happy:
        world.say(
            f"{child.id} touched the brake lever and whispered the rhyme back, "
            f"this time meaning every word."
        )
    else:
        world.say(
            f"{child.id} sniffed, nodded, and whispered the rhyme back so it would "
            f"be harder to forget next time."
        )


def closing_walk(world: World, child: Entity, rider: Rider, path: Path, happy: bool) -> None:
    if happy:
        child.memes["joy"] += 1
        world.say(
            f"Soon they walked on beside the lake again, only slower now: "
            f"click for the brake, smile for the lake, and {rider.label} riding dry."
        )
        world.say(
            f"When another duck gave a quack, {child.id} stopped the toy pram first, "
            f"then laughed. That was how the day proved what had changed."
        )
    else:
        world.say(
            f"They sat on a bench by the lake until the drips were gone. "
            f"Then {child.id} pushed the toy pram home very carefully, saying the rhyme "
            f"with every step."
        )
        world.say(
            f"By the gate, the brake clicked on before the wheels rested. "
            f"That small click was the new ending."
        )


def tell(
    path: Path,
    rider_cfg: Rider,
    reminder: Reminder,
    stop_method: StopMethod,
    *,
    child_name: str = "Mina",
    child_type: str = "girl",
    caregiver_type: str = "mother",
    pause: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    caregiver = world.add(
        Entity(id="Caregiver", kind="character", type=caregiver_type, role="caregiver", label="the caregiver")
    )
    pram = world.add(Entity(id="pram", type="pram", label="pram"))
    lake = world.add(Entity(id="lake", type="lake", label="lake"))
    rider = world.add(Entity(id="rider", type="toy", label=rider_cfg.label, attrs={"config_id": rider_cfg.id}))

    pram.meters["distance_to_lake"] = 2.0
    pram.meters["rolling"] = 0.0
    pram.meters["stopped"] = 1.0
    pram.meters["in_lake"] = 0.0
    rider.meters["wet"] = 0.0
    lake.meters["risk"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["sad"] = 0.0
    child.memes["memory"] = 0.0
    child.memes["lesson"] = 0.0

    world.facts["pause"] = pause
    world.facts["memory_available"] = memory_available(path, pause)

    introduce(world, child, rider_cfg, path)
    lake_rhyme(world, child, rider_cfg, path)

    world.para()
    pause_for_ducks(world, child, rider_cfg, path)
    warn(world, child, caregiver, reminder, path)
    forget(world, child)

    world.para()
    start_roll(world)
    rolling_beat(world, path)
    if memory_available(path, pause):
        flashback(world, child, reminder, path)

    happy = can_stop(stop_method, path, pause)
    if happy:
        stop_pram(world, child, stop_method, path)
    else:
        lake_splash(world, child, rider_cfg, caregiver)

    world.para()
    lesson(world, child, caregiver, reminder, happy)
    closing_walk(world, child, rider_cfg, path, happy)

    outcome = "stopped" if happy else "splashed"
    world.facts.update(
        child=child,
        caregiver=caregiver,
        pram=pram,
        lake=lake,
        rider_cfg=rider_cfg,
        rider=rider,
        path=path,
        reminder=reminder,
        stop_method=stop_method,
        outcome=outcome,
        happy=happy,
        wet=rider.meters["wet"] >= THRESHOLD,
    )
    return world


PATHS = {
    "willow_bank": Path(
        id="willow_bank",
        label="the willow bank",
        phrase="the willow-bank path",
        rhyme_place="By the willow bank",
        texture="smooth",
        slope=2,
        edge="the mossy edge",
        safe_spot="a patch of daisies",
        tags={"lake", "slope"},
    ),
    "pebble_bend": Path(
        id="pebble_bend",
        label="Pebble Bend",
        phrase="the pebbly bend",
        rhyme_place="At Pebble Bend",
        texture="pebbly",
        slope=1,
        edge="the stony edge",
        safe_spot="the shady bench",
        tags={"lake", "pebbles"},
    ),
    "meadow": Path(
        id="meadow",
        label="the meadow green",
        phrase="the flat meadow path",
        rhyme_place="On the meadow green",
        texture="soft",
        slope=0,
        edge="the far reeds",
        safe_spot="the buttercup patch",
        tags={"flat", "meadow"},
    ),
}

RIDERS = {
    "bunny": Rider(
        id="bunny",
        label="bunny",
        phrase="a floppy bunny tucked inside",
        sound="bumpity-bump",
        tags={"toy", "soft"},
    ),
    "duckling": Rider(
        id="duckling",
        label="duckling doll",
        phrase="a duckling doll tucked inside",
        sound="quackity-quack",
        tags={"toy", "duck"},
    ),
    "bear": Rider(
        id="bear",
        label="little bear",
        phrase="little bear tucked inside",
        sound="rumplety-rumple",
        tags={"toy", "bear"},
    ),
}

REMINDERS = {
    "grandma_song": Reminder(
        id="grandma_song",
        elder_type="grandmother",
        elder_label="Grandma",
        earlier_time="Last spring",
        action="shown how to park the toy pram under the pear tree",
        rhyme="Click the brake by the lake, for the little rider's sake.",
        lesson="Before you stop to stare or play, make the wheels stay where they are.",
        tags={"flashback", "brake", "grandma"},
    ),
    "dad_song": Reminder(
        id="dad_song",
        elder_type="father",
        elder_label="Dad",
        earlier_time="One bright morning before breakfast",
        action="tapped the brake with a finger and made a game of listening for the click",
        rhyme="Near the lake, click-click the brake.",
        lesson="A small click can stop a big worry before it starts.",
        tags={"flashback", "brake", "dad"},
    ),
    "grandpa_song": Reminder(
        id="grandpa_song",
        elder_type="grandfather",
        elder_label="Grandpa",
        earlier_time="In the yellow days of autumn",
        action="parked the toy pram by the gate and winked like it was a grand secret",
        rhyme="Pram by the lake? Brake first, then wait.",
        lesson="When wheels are still, your hands and heart can stay calm too.",
        tags={"flashback", "brake", "grandpa"},
    ),
}

STOP_METHODS = {
    "brake_click": StopMethod(
        id="brake_click",
        sense=3,
        power=3,
        text="remembered the rhyme, clicked the brake, and caught the handle",
        fail="tried to click the brake too late",
        qa_text="clicked the brake and caught the handle",
        needs_memory=True,
        tags={"brake", "safe"},
    ),
    "handle_grab": StopMethod(
        id="handle_grab",
        sense=3,
        power=2,
        text="snatched the handle with both hands and planted both shoes hard",
        fail="grabbed for the handle, but the wheels kept skittering downhill",
        qa_text="grabbed the handle with both hands and dug in with both shoes",
        tags={"hands", "safe"},
    ),
    "hand_only": StopMethod(
        id="hand_only",
        sense=1,
        power=1,
        text="reached with one hand for the handle",
        fail="reached with one hand for the handle, but the toy pram was already too fast",
        qa_text="reached with one hand for the handle",
        tags={"hands"},
    ),
}

GIRL_NAMES = ["Mina", "Lulu", "Nell", "Daisy", "Tilly", "Poppy", "May"]
BOY_NAMES = ["Ollie", "Toby", "Ned", "Finn", "Milo", "Jem", "Alfie"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for path_id, path in PATHS.items():
        for stop_id, method in STOP_METHODS.items():
            if hazard_at_risk(path) and method.sense >= SENSE_MIN:
                combos.append((path_id, stop_id))
    return combos


@dataclass
class StoryParams:
    path: str
    rider: str
    reminder: str
    stop: str
    name: str
    gender: str
    caregiver: str
    pause: int = 0
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
    "pram": [
        (
            "What is a pram?",
            "A pram is a little wheeled carriage for carrying a baby or a toy. If it is on a slope, it can roll unless someone holds it or puts the brake on.",
        )
    ],
    "lake": [
        (
            "What is a lake?",
            "A lake is a big body of water surrounded by land. The edges can be slippery, so wheels and running feet need extra care there.",
        )
    ],
    "brake": [
        (
            "What does a brake do on a pram?",
            "A brake helps keep the wheels from rolling. Clicking it on before you stop near a hill or a lake makes the pram stay where you put it.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick look back to something that happened earlier. It can help a character remember an important lesson right when they need it.",
        )
    ],
    "ducks": [
        (
            "Why might a child stop by a lake to look around?",
            "Lakes often have ducks, ripples, reeds, and shiny water to watch. Pretty things can distract you, which is why safety habits matter.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    rider = f["rider_cfg"]
    reminder = f["reminder"]
    path = f["path"]
    outcome = f["outcome"]
    if outcome == "splashed":
        return [
            'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "pram" and "lake" and uses a flashback.',
            f"Tell a gentle cautionary story where {child.id} pauses by {path.label} with a toy pram, remembers an old rhyme too late, and {rider.label} gets wet at the lake.",
            f'Write a story with sing-song lines and a flashback to an elder saying "{reminder.rhyme}" where the ending teaches the child to brake the pram before staring at ducks.',
        ]
    return [
        'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "pram" and "lake" and uses a flashback.',
        f"Tell a gentle lake-side story where {child.id}'s toy pram starts to roll, a flashback brings back an old rhyme, and the pram is stopped just in time.",
        f'Write a sing-song story where a child remembers "{reminder.rhyme}" and proves the lesson by safely stopping a pram near the lake.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    path = f["path"]
    rider_cfg = f["rider_cfg"]
    reminder = f["reminder"]
    stop_method = f["stop_method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child walking by the lake with a toy pram and {rider_cfg.label} inside. {caregiver.label_word.capitalize()} is nearby too, helping keep the walk safe.",
        ),
        (
            "Why was the pram in danger?",
            f"The toy pram was pointing downhill on {path.label}, so it could roll toward the lake if the brake was forgotten. The danger came from the sloping path and the distracted pause near the water.",
        ),
        (
            "What was the flashback about?",
            f"The flashback was about {reminder.elder_label} teaching a little rhyme about using the brake. It mattered because the old lesson came back exactly when the wheels began to move.",
        ),
    ]
    if f["outcome"] == "stopped":
        qa.append(
            (
                f"How did {child.id} stop the toy pram?",
                f"{child.id} {stop_method.qa_text}. The remembered rhyme helped {child.pronoun()} act quickly instead of freezing in fright.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with the toy pram still dry beside the lake. After that, {child.id} stopped the pram first before looking at the ducks, which shows the lesson had truly stuck.",
            )
        )
    else:
        qa.append(
            (
                f"What happened when {child.id} could not stop the toy pram in time?",
                f"The toy pram tipped into the shallow edge of the lake, and {rider_cfg.label} got wet. {caregiver.label_word.capitalize()} helped right away, but the splash made the lesson feel real.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a careful new habit. Even though {rider_cfg.label} got wet, {child.id} went home saying the rhyme and clicked the brake before resting the pram again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pram", "lake", "flashback", "brake"}
    if world.facts["rider_cfg"].id == "duckling":
        tags.add("ducks")
    out: list[tuple[str, str]] = []
    for key in ["pram", "lake", "brake", "flashback", "ducks"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        path="willow_bank",
        rider="bunny",
        reminder="grandma_song",
        stop="brake_click",
        name="Mina",
        gender="girl",
        caregiver="mother",
        pause=1,
    ),
    StoryParams(
        path="pebble_bend",
        rider="duckling",
        reminder="dad_song",
        stop="handle_grab",
        name="Ollie",
        gender="boy",
        caregiver="father",
        pause=0,
    ),
    StoryParams(
        path="willow_bank",
        rider="bear",
        reminder="grandpa_song",
        stop="handle_grab",
        name="Tilly",
        gender="girl",
        caregiver="grandmother",
        pause=1,
    ),
    StoryParams(
        path="pebble_bend",
        rider="bunny",
        reminder="grandma_song",
        stop="brake_click",
        name="Finn",
        gender="boy",
        caregiver="mother",
        pause=1,
    ),
    StoryParams(
        path="willow_bank",
        rider="duckling",
        reminder="dad_song",
        stop="brake_click",
        name="Poppy",
        gender="girl",
        caregiver="father",
        pause=2,
    ),
]


def explain_rejection(path: Path, method: StopMethod) -> str:
    if not hazard_at_risk(path):
        return (
            f"(No story: {path.label} is flat, so a runaway pram toward the lake is not a real risk. "
            f"Pick a sloping path like willow_bank or pebble_bend.)"
        )
    if method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_stops()))
        return (
            f"(Refusing stop method '{method.id}': it is too weak or careless for this world "
            f"(sense={method.sense} < {SENSE_MIN}). Try: {better}.)"
        )
    return "(No story: this combination does not make a reasonable runaway-pram tale.)"


def outcome_of(params: StoryParams) -> str:
    return "stopped" if can_stop(STOP_METHODS[params.stop], PATHS[params.path], params.pause) else "splashed"


ASP_RULES = r"""
hazard(P) :- path(P), slope(P, S), S > 0.
sensible_stop(M) :- stop_method(M), sense(M, S), sense_min(Min), S >= Min.
valid(P, M) :- path(P), stop_method(M), hazard(P), sensible_stop(M).

severity(S + P) :- chosen_path(Path), slope(Path, S), pause(P).
memory_ready :- chosen_path(Path), pause(P), slope(Path, S), S + P >= 2.
can_use(M) :- chosen_stop(M), needs_memory(M), memory_ready.
can_use(M) :- chosen_stop(M), not needs_memory(M).
contained :- chosen_stop(M), can_use(M), power(M, Pwr), severity(V), Pwr >= V.

outcome(stopped) :- contained.
outcome(splashed) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, path in PATHS.items():
        lines.append(asp.fact("path", pid))
        lines.append(asp.fact("slope", pid, path.slope))
    for mid, method in STOP_METHODS.items():
        lines.append(asp.fact("stop_method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("power", mid, method.power))
        if method.needs_memory:
            lines.append(asp.fact("needs_memory", mid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_stop/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible_stop"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_path", params.path),
            asp.fact("chosen_stop", params.stop),
            asp.fact("pause", params.pause),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sensible = set(asp_sensible())
    p_sensible = {m.id for m in sensible_stops()}
    if c_sensible == p_sensible:
        print(f"OK: sensible stop methods match ({sorted(c_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible stop methods: clingo={sorted(c_sensible)} python={sorted(p_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(120):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test failed: generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a pram, a lake, and a remembered rhyme."
    )
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--rider", choices=RIDERS)
    ap.add_argument("--reminder", choices=REMINDERS)
    ap.add_argument("--stop", choices=STOP_METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--pause", type=int, choices=[0, 1, 2], help="how long the child hesitates after the pram starts rolling")
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.path and args.stop:
        path = PATHS[args.path]
        method = STOP_METHODS[args.stop]
        if not (hazard_at_risk(path) and method.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(path, method))

    if args.stop and STOP_METHODS[args.stop].sense < SENSE_MIN:
        path = PATHS[args.path] if args.path else next(iter(PATHS.values()))
        raise StoryError(explain_rejection(path, STOP_METHODS[args.stop]))

    if args.path and not hazard_at_risk(PATHS[args.path]):
        method = STOP_METHODS[args.stop] if args.stop else best_stop()
        raise StoryError(explain_rejection(PATHS[args.path], method))

    combos = [
        c
        for c in valid_combos()
        if (args.path is None or c[0] == args.path)
        and (args.stop is None or c[1] == args.stop)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    path_id, stop_id = rng.choice(sorted(combos))
    rider_id = args.rider or rng.choice(sorted(RIDERS))
    reminder_id = args.reminder or rng.choice(sorted(REMINDERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    caregiver = args.caregiver or rng.choice(["mother", "father", "grandmother", "grandfather"])
    pause = args.pause if args.pause is not None else rng.choice([0, 1, 2])
    return StoryParams(
        path=path_id,
        rider=rider_id,
        reminder=reminder_id,
        stop=stop_id,
        name=name,
        gender=gender,
        caregiver=caregiver,
        pause=pause,
    )


def generate(params: StoryParams) -> StorySample:
    if params.path not in PATHS:
        raise StoryError(f"Unknown path: {params.path}")
    if params.rider not in RIDERS:
        raise StoryError(f"Unknown rider: {params.rider}")
    if params.reminder not in REMINDERS:
        raise StoryError(f"Unknown reminder: {params.reminder}")
    if params.stop not in STOP_METHODS:
        raise StoryError(f"Unknown stop method: {params.stop}")
    if params.caregiver not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"Unknown caregiver type: {params.caregiver}")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"Unknown gender: {params.gender}")

    path = PATHS[params.path]
    method = STOP_METHODS[params.stop]
    if not hazard_at_risk(path):
        raise StoryError(explain_rejection(path, method))
    if method.sense < SENSE_MIN:
        raise StoryError(explain_rejection(path, method))

    world = tell(
        path=path,
        rider_cfg=RIDERS[params.rider],
        reminder=REMINDERS[params.reminder],
        stop_method=method,
        child_name=params.name,
        child_type=params.gender,
        caregiver_type=params.caregiver,
        pause=params.pause,
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
        print(asp_program("", "#show valid/2.\n#show sensible_stop/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible stop methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (path, stop) combos:\n")
        for path_id, stop_id in combos:
            print(f"  {path_id:12} {stop_id}")
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
            header = f"### {p.name}: {p.path}, {p.stop}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
