#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cease_wheel_meteoroid_bad_ending_surprise_space.py
==============================================================================

A standalone story world about a child-sized space rover game, a loose wheel,
a warning to cease rolling, and either a happy surprise or a bad ending.

The world rebuilds a simple "space adventure" tale from simulation state:

- Two children turn an everyday wheeled toy into a space rover.
- One child notices a wheel wobbling before they cross a bumpy "meteoroid field."
- The safer child warns that they should cease the mission and get help.
- If the warning is strong enough, the mission pauses safely and a grown-up fixes
  the rover before surprising them with a new way to explore.
- Otherwise they roll on, the loose wheel comes off, and the rover either gets
  repaired in time or the whole adventure has to cease for the night.

Run it
------
    python storyworlds/worlds/gpt-5.4/cease_wheel_meteoroid_bad_ending_surprise_space.py
    python storyworlds/worlds/gpt-5.4/cease_wheel_meteoroid_bad_ending_surprise_space.py --all
    python storyworlds/worlds/gpt-5.4/cease_wheel_meteoroid_bad_ending_surprise_space.py --qa --json
    python storyworlds/worlds/gpt-5.4/cease_wheel_meteoroid_bad_ending_surprise_space.py --verify
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
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible", "watchful"}


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
    wheeled: bool = False
    bumpy: bool = False
    fix_power: int = 0
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
        return {
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
class Theme:
    id: str
    scene: str
    opening: str
    mission: str
    hazard_name: str
    sendoff: str
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
class Vehicle:
    id: str
    label: str
    phrase: str
    cockpit: str
    wheel_word: str
    wheels: int
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
class Path:
    id: str
    label: str
    phrase: str
    pretend: str
    bump: int
    bumpy: bool = True
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


@dataclass
class Surprise:
    id: str
    phrase: str
    reveal: str
    ending: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"pilot", "partner"}]

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


def _r_wobble(world: World) -> list[str]:
    rover = world.get("rover")
    path = world.get("path")
    if rover.meters["rolling"] < THRESHOLD:
        return []
    if rover.meters["loose_wheel"] < THRESHOLD:
        return []
    if path.meters["bump"] < THRESHOLD:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rover.meters["wobble"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    return ["__wobble__"]


def _r_wheel_off(world: World) -> list[str]:
    rover = world.get("rover")
    path = world.get("path")
    if rover.meters["wobble"] < THRESHOLD:
        return []
    if path.meters["bump"] < 2:
        return []
    sig = ("wheel_off",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rover.meters["wheel_off"] += 1
    rover.meters["stopped"] += 1
    rover.meters["tipped"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__wheel_off__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="wheel_off", tag="physical", apply=_r_wheel_off),
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


def hazard_at_risk(vehicle: Vehicle, path: Path) -> bool:
    return vehicle.wheels > 0 and path.bumpy and path.bump >= 1


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(path: Path, delay: int) -> int:
    return path.bump + delay


def can_fix(response: Response, path: Path, delay: int) -> bool:
    return response.power >= severity_of(path, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_cease(relation: str, pilot_age: int, partner_age: int, trait: str) -> bool:
    partner_older = relation == "siblings" and partner_age > pilot_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if partner_older else 0.0)
    return partner_older and authority > BRAVERY_INIT


def predict_break(world: World) -> dict:
    sim = world.copy()
    rover = sim.get("rover")
    rover.meters["rolling"] += 1
    propagate(sim, narrate=False)
    return {
        "wheel_off": rover.meters["wheel_off"] >= THRESHOLD,
        "tipped": rover.meters["tipped"] >= THRESHOLD,
    }


def play_setup(world: World, pilot: Entity, partner: Entity, theme: Theme,
               vehicle: Vehicle, path: Path) -> None:
    for kid in (pilot, partner):
        kid.memes["joy"] += 1
    world.say(
        f"After dinner, {pilot.id} and {partner.id} turned the yard into {theme.scene}. "
        f"{theme.opening}"
    )
    world.say(
        f"Their {vehicle.label} became {vehicle.phrase}, and {path.phrase} became "
        f"{theme.hazard_name}, a pretend river of bouncing meteoroid rocks."
    )
    world.say(
        f'"Pilot {pilot.id} and Scout {partner.id}!" {pilot.id} cheered. '
        f'"Let\'s start {theme.mission}!"'
    )


def notice_problem(world: World, partner: Entity, vehicle: Vehicle) -> None:
    world.get("rover").meters["loose_wheel"] += 1
    partner.memes["caution"] += 1
    world.say(
        f"But when {partner.id} leaned near the {vehicle.cockpit}, "
        f"{partner.pronoun()} saw one {vehicle.wheel_word} wobble with a small, shaky tick."
    )


def tempt(world: World, pilot: Entity, theme: Theme, path: Path) -> None:
    pilot.memes["bravado"] += 1
    world.say(
        f'{pilot.id} grinned at {path.label}. "That is the biggest meteoroid field yet," '
        f'{pilot.pronoun()} said. "We can bounce right across it."'
    )


def warn(world: World, partner: Entity, pilot: Entity, helper: Entity,
         vehicle: Vehicle, theme: Theme) -> None:
    pred = predict_break(world)
    world.facts["predicted_break"] = pred["wheel_off"]
    extra = ""
    if partner.memes["caution"] >= 6:
        extra = f" {partner.pronoun().capitalize()} planted both feet and would not move."
    world.say(
        f'{partner.id} grabbed the side of the {vehicle.label}. "Cease the mission," '
        f'{partner.pronoun()} said. "{vehicle.wheel_word.capitalize()}s should not shake like that. '
        f'If we roll now, the rover could lose a wheel in the middle of {theme.hazard_name}. '
        f'Let\'s get {helper.label_word} first."{extra}'
    )


def defy(world: World, pilot: Entity, partner: Entity) -> None:
    pilot.memes["defiance"] += 1
    older = pilot.attrs.get("relation") == "siblings" and pilot.age > partner.age
    if older:
        rel = "big brother" if pilot.type == "boy" else "big sister"
        world.say(
            f'"It is only a little wobble," {pilot.id} said. Because {pilot.id} was '
            f'{partner.id}\'s {rel}, {partner.id} could not stop {pilot.pronoun("object")} in time.'
        )
    else:
        world.say(
            f'"It is only a little wobble," {pilot.id} said, and pushed off anyway.'
        )


def back_down(world: World, pilot: Entity, partner: Entity, helper: Entity,
              vehicle: Vehicle) -> None:
    pilot.memes["relief"] += 1
    partner.memes["relief"] += 1
    pilot.memes["bravery"] = 0.0
    world.say(
        f'{pilot.id} looked at the shaking {vehicle.wheel_word}, swallowed, and nodded. '
        f'"Okay," {pilot.pronoun()} said. "We will cease the mission for now."'
    )
    world.say(
        f"They steered the {vehicle.label} back to the porch and called for {helper.label_word} "
        f"instead of charging into the pretend meteoroid field."
    )


def launch(world: World, pilot: Entity, vehicle: Vehicle, path: Path) -> None:
    rover = world.get("rover")
    rover.meters["rolling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {vehicle.label} rattled forward over {path.label}. "
        f"For one thrilled second, it felt as if they really were crossing a river of meteoroid stones."
    )
    if rover.meters["wobble"] >= THRESHOLD:
        world.say(
            f"Then the loose {vehicle.wheel_word} began to shimmy harder and harder, making the whole rover sway."
        )
    if rover.meters["wheel_off"] >= THRESHOLD:
        world.say(
            f"With a clack, the {vehicle.wheel_word} popped free. The rover tipped sideways and skidded to a stop."
        )


def alarm(world: World, partner: Entity, pilot: Entity, helper: Entity) -> None:
    world.say(f'"{pilot.id}! The wheel!" {partner.id} cried.')
    world.say(f'"{helper.label_word.upper()}!"')


def rescue(world: World, helper: Entity, response: Response, surprise: Surprise,
           pilot: Entity, partner: Entity, vehicle: Vehicle) -> None:
    rover = world.get("rover")
    rover.meters["wheel_off"] = 0.0
    rover.meters["wobble"] = 0.0
    rover.meters["stopped"] = 0.0
    rover.meters["rolling"] = 0.0
    rover.meters["fixed"] += 1
    helper.meters["repair"] += 1
    body = response.text.format(vehicle=vehicle.label, wheel=vehicle.wheel_word)
    world.say(
        f"{helper.label_word.capitalize()} came running and {body}."
    )
    world.say(
        f'When the last bolt sat tight, {helper.pronoun()} smiled. "I have a surprise," '
        f'{helper.pronoun()} said. {surprise.reveal}'
    )
    world.say(
        f"{pilot.id} and {partner.id} stared with wide eyes. Soon they were {surprise.ending}"
    )
    for kid in (pilot, partner):
        kid.memes["joy"] += 1
        kid.memes["relief"] += 1
        kid.memes["wonder"] += 1


def lesson(world: World, helper: Entity, pilot: Entity, partner: Entity,
           vehicle: Vehicle) -> None:
    for kid in (pilot, partner):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"{helper.label_word.capitalize()} knelt beside them. "
        f'"A wobbling {vehicle.wheel_word} means stop and ask for help," '
        f'{helper.pronoun()} said softly. "The brave thing is to cease before the crash, '
        f'not after it."'
    )
    world.say(f'"We know," whispered {pilot.id} and {partner.id} together.')


def fail_fix(world: World, helper: Entity, response: Response, vehicle: Vehicle) -> None:
    rover = world.get("rover")
    rover.meters["broken"] += 1
    body = response.fail.format(vehicle=vehicle.label, wheel=vehicle.wheel_word)
    world.say(
        f"{helper.label_word.capitalize()} hurried over and {body}."
    )
    world.say(
        f"But the rover sagged crookedly on one side, and its mission lights stayed dark."
    )


def bad_ending(world: World, helper: Entity, pilot: Entity, partner: Entity,
               theme: Theme, vehicle: Vehicle, surprise: Surprise) -> None:
    rover = world.get("rover")
    rover.meters["rolling"] = 0.0
    rover.meters["stopped"] += 1
    for kid in (pilot, partner):
        kid.memes["sadness"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"There would be no more rolling that night. The adventure had to cease, "
        f"and the {vehicle.label} sat by the porch with one empty axle."
    )
    world.say(
        f"As the sky turned dark, {surprise.phrase} came out overhead. It was beautiful, "
        f"but {pilot.id} and {partner.id} were too quiet to cheer."
    )
    world.say(
        f"{helper.label_word.capitalize()} held them close and said that tomorrow they could build again, "
        f"but tonight {theme.sendoff} had ended in a hard, sad hush."
    )


THEMES = {
    "moon": Theme(
        id="moon",
        scene="a silver moon base",
        opening="A foil blanket became a star cape, a cereal box became mission control, and chalk stars curved across the stepping stones.",
        mission="the crater run",
        hazard_name="the Moon Lane",
        sendoff="their moon mission",
        tags={"space", "moon"},
    ),
    "mars": Theme(
        id="mars",
        scene="a dusty Mars outpost",
        opening="A red scarf became a captain's sash, a bucket became a sample pod, and little flags marked the edge of the garden.",
        mission="the red-planet patrol",
        hazard_name="the Mars Ridge",
        sendoff="their Mars patrol",
        tags={"space", "mars"},
    ),
    "saturn": Theme(
        id="saturn",
        scene="a station under Saturn's rings",
        opening="A colander became a shiny helmet, string lights became faraway stars, and pillows marked the edge of the launch pad.",
        mission="ring patrol",
        hazard_name="the Ring Belt",
        sendoff="their ring patrol",
        tags={"space", "saturn"},
    ),
}

VEHICLES = {
    "wagon": Vehicle(
        id="wagon",
        label="wagon",
        phrase="a moon rover with blinking sticker buttons",
        cockpit="red side panel",
        wheel_word="wheel",
        wheels=4,
        tags={"wagon", "wheel"},
    ),
    "pedal_cart": Vehicle(
        id="pedal_cart",
        label="pedal cart",
        phrase="a brave little rover with a low metal nose",
        cockpit="seat frame",
        wheel_word="wheel",
        wheels=4,
        tags={"cart", "wheel"},
    ),
    "scooter_board": Vehicle(
        id="scooter_board",
        label="scooter board",
        phrase="a tiny scout shuttle that skimmed the ground",
        cockpit="flat blue deck",
        wheel_word="wheel",
        wheels=4,
        tags={"scooter", "wheel"},
    ),
}

PATHS = {
    "gravel": Path(
        id="gravel",
        label="the gravel path",
        phrase="the gravel path by the flower bed",
        pretend="meteoroid field",
        bump=3,
        bumpy=True,
        tags={"gravel", "meteoroid"},
    ),
    "bricks": Path(
        id="bricks",
        label="the brick walk",
        phrase="the old brick walk to the gate",
        pretend="meteoroid belt",
        bump=2,
        bumpy=True,
        tags={"bricks", "meteoroid"},
    ),
    "deck_boards": Path(
        id="deck_boards",
        label="the deck boards",
        phrase="the wooden deck boards behind the house",
        pretend="asteroid bridge",
        bump=1,
        bumpy=True,
        tags={"deck", "meteoroid"},
    ),
    "grass": Path(
        id="grass",
        label="the grass",
        phrase="the flat patch of grass",
        pretend="soft moon dust",
        bump=0,
        bumpy=False,
        tags={"grass"},
    ),
}

RESPONSES = {
    "replace_wheel": Response(
        id="replace_wheel",
        sense=3,
        power=4,
        text="lifted the {vehicle}, found the runaway {wheel}, and fitted on a spare part from the tool shelf",
        fail="tried a spare part on the {vehicle}, but the bent axle would not hold the {wheel} straight",
        qa_text="fitted a spare wheel and tightened everything safely",
        tags={"repair", "spare_wheel"},
    ),
    "tighten_bolts": Response(
        id="tighten_bolts",
        sense=3,
        power=2,
        text="turned the rover over, tightened each bolt, and tested the {wheel} with both hands until it sat firm",
        fail="tightened the bolts on the {vehicle}, but the {wheel} still leaned badly",
        qa_text="tightened the bolts until the wheel sat firm",
        tags={"repair", "tools"},
    ),
    "tow_home": Response(
        id="tow_home",
        sense=2,
        power=1,
        text="pulled the {vehicle} back to the porch, steadied the loose {wheel}, and made the rover safe again for a short, slow roll",
        fail="pulled the {vehicle} back to the porch, but the loose {wheel} was too damaged to use again that night",
        qa_text="pulled the rover home and steadied the wheel",
        tags={"repair", "tow"},
    ),
    "tape_it": Response(
        id="tape_it",
        sense=1,
        power=1,
        text="wrapped tape around the {wheel} and hoped for the best",
        fail="wrapped tape around the {wheel}, but it slipped right off again",
        qa_text="wrapped tape around the wheel",
        tags={"tape"},
    ),
}

SURPRISES = {
    "star_projector": Surprise(
        id="star_projector",
        phrase="a real shower of stars",
        reveal='From behind the chair, {h} pulled out a little star projector that sprayed silver dots over the ceiling of the porch.'.replace("{h}", "they"),
        ending="driving their rover under a porch full of make-believe stars",
        tags={"projector", "surprise"},
    ),
    "glow_map": Surprise(
        id="glow_map",
        phrase="a stripe of pale starlight",
        reveal='From the hall shelf, {h} brought a glow-in-the-dark space map and spread it beside the porch steps.'.replace("{h}", "they"),
        ending="tracing planets with one finger while the fixed rover waited proudly nearby",
        tags={"map", "surprise"},
    ),
    "moon_cookies": Surprise(
        id="moon_cookies",
        phrase="the first evening stars",
        reveal='Out of the kitchen came a plate of round moon cookies, still warm, and a paper chart of safe missions.'.replace("{h}", "they"),
        ending="planning a gentler rover trip while nibbling moon cookies",
        tags={"cookies", "surprise"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Zoe", "Ava", "Nora", "Ivy", "June", "Ella"]
BOY_NAMES = ["Leo", "Max", "Finn", "Noah", "Eli", "Theo", "Owen", "Jack"]
TRAITS = ["careful", "steady", "sensible", "watchful", "curious", "bold"]


@dataclass
class StoryParams:
    theme: str
    vehicle: str
    path: str
    response: str
    surprise: str
    pilot: str
    pilot_gender: str
    partner: str
    partner_gender: str
    helper: str
    trait: str
    delay: int = 0
    pilot_age: int = 6
    partner_age: int = 4
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
    "meteoroid": [
        (
            "What is a meteoroid?",
            "A meteoroid is a small piece of rock moving through space. If it reaches the ground of a planet, people call it a meteorite."
        )
    ],
    "wheel": [
        (
            "What does a wheel do?",
            "A wheel helps a cart, bike, or rover roll smoothly. If a wheel is loose, the ride can wobble or stop."
        )
    ],
    "repair": [
        (
            "Why should a grown-up fix a loose wheel?",
            "A loose wheel can come off while something is moving. A grown-up can use tools and make sure it is tight and safe."
        )
    ],
    "spare_wheel": [
        (
            "What is a spare wheel?",
            "A spare wheel is an extra wheel kept ready in case one gets damaged. It helps the vehicle work again."
        )
    ],
    "tools": [
        (
            "What do bolts do on a wheel?",
            "Bolts hold parts together tightly. If they come loose, the wheel can wobble."
        )
    ],
    "tow": [
        (
            "What does it mean to tow something?",
            "To tow something means to pull it to safety when it cannot move well by itself."
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something you were not expecting. It can make a story suddenly feel different."
        )
    ],
    "projector": [
        (
            "What is a star projector?",
            "A star projector shines little lights on a wall or ceiling so a room can look full of stars."
        )
    ],
    "map": [
        (
            "What is a space map for?",
            "A space map helps you point to planets and stars and imagine where a mission might go."
        )
    ],
    "space": [
        (
            "Why do space stories talk about missions?",
            "A mission is a planned trip with a goal. In a space adventure, the goal might be to explore, rescue, or discover something."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "space",
    "meteoroid",
    "wheel",
    "repair",
    "spare_wheel",
    "tools",
    "tow",
    "surprise",
    "projector",
    "map",
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for vehicle_id, vehicle in VEHICLES.items():
            for path_id, path in PATHS.items():
                if hazard_at_risk(vehicle, path):
                    combos.append((theme_id, vehicle_id, path_id))
    return combos


def pair_noun(pilot: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if pilot.type == "boy" and partner.type == "boy":
            return "two brothers"
        if pilot.type == "girl" and partner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme = f["theme"]
    path = f["path_cfg"]
    vehicle = f["vehicle_cfg"]
    pilot = f["pilot"]
    partner = f["partner"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short space adventure for a 3-to-5-year-old that includes the words "cease", "wheel", and "meteoroid", where children stop a rover mission before a crash.',
            f"Tell a gentle story where {partner.id} notices a loose wheel, says to cease the mission, and the children listen before rolling into a pretend meteoroid field.",
            f"Write a story about a child-sized {vehicle.label} crossing {path.label}, but the bravest choice is stopping and asking a grown-up for help, followed by a happy surprise.",
        ]
    if outcome == "contained":
        return [
            f'Write a short space adventure for a 3-to-5-year-old that includes the words "cease", "wheel", and "meteoroid", where a rover almost crashes but help arrives in time.',
            f"Tell a story where {pilot.id} ignores a warning, a wheel comes off in a pretend meteoroid field, and a grown-up repairs the rover before the mission can continue.",
            f"Write a story with a surprise ending in which a broken rover is fixed and the children discover a safer way to keep their space game going.",
        ]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the words "cease", "wheel", and "meteoroid", and ends sadly after a rover breaks.',
        f"Tell a cautionary story where {pilot.id} does not cease the mission, a wheel comes off, and the adventure must stop for the night.",
        f"Write a child-facing bad ending story where a pretend meteoroid crossing goes wrong and the children learn that stopping early would have been wiser.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    pilot = f["pilot"]
    partner = f["partner"]
    helper = f["helper"]
    theme = f["theme"]
    vehicle = f["vehicle_cfg"]
    path = f["path_cfg"]
    response = f["response"]
    surprise = f["surprise"]
    pair = pair_noun(pilot, partner, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {pilot.id} and {partner.id}, pretending to be space explorers. Their {helper.label_word} helps when the rover mission goes wrong."
        ),
        (
            "What were they pretending?",
            f"They turned the yard into {theme.scene} and imagined {path.label} as a meteoroid field. Their {vehicle.label} became a space rover for {theme.mission}."
        ),
        (
            f"Why did {partner.id} tell {pilot.id} to cease the mission?",
            f"{partner.id} saw that one wheel was wobbling before they crossed the bumpy path. {partner.pronoun().capitalize()} knew the rover could lose that wheel in the middle of the pretend meteoroid field."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                "What happened after the children stopped?",
                f"They rolled the rover back instead of crossing the path, and they called for help. Because they ceased the mission early, nothing crashed and nobody got scared."
            )
        )
        qa.append(
            (
                f"What was the surprise?",
                f"The surprise was {surprise.phrase}, given as a new way to keep their space game going. It came after the helper made the rover safe, so the ending felt bright instead of scary."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                "What happened when they rolled on anyway?",
                f"The loose wheel came off and the rover tipped to a stop. The bumpy path shook the weak wheel until the game turned from exciting to frightening."
            )
        )
        qa.append(
            (
                f"How did {helper.label_word} help?",
                f"{helper.label_word.capitalize()} {response.qa_text}. That repair worked before the whole evening had to cease, so the children could calm down and enjoy the surprise."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with relief and wonder instead of tears. After the repair, the children got {surprise.phrase} and had a safer way to keep pretending."
            )
        )
    else:
        qa.append(
            (
                "Why was the ending sad?",
                f"The repair did not work well enough, so the rover could not roll again that night. The mission had to cease, and the children had to watch the evening sky without finishing their adventure."
            )
        )
        qa.append(
            (
                f"What did {pilot.id} and {partner.id} learn?",
                f"They learned that a wobbling wheel is a reason to stop right away. Waiting until after the crash made the whole ending harder and sadder."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["theme"].tags) | set(f["vehicle_cfg"].tags) | set(f["path_cfg"].tags)
    if f["outcome"] == "contained":
        tags |= set(f["response"].tags) | set(f["surprise"].tags)
    elif f["outcome"] == "averted":
        tags |= set(f["surprise"].tags) | {"repair"}
    else:
        tags |= set(f["response"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(theme: Theme, vehicle: Vehicle, path: Path, response: Response,
         surprise: Surprise, pilot_name: str = "Leo", pilot_gender: str = "boy",
         partner_name: str = "Mia", partner_gender: str = "girl",
         helper_type: str = "mother", trait: str = "careful", delay: int = 0,
         pilot_age: int = 6, partner_age: int = 4, relation: str = "siblings",
         trust: int = 6) -> World:
    world = World()
    pilot = world.add(Entity(
        id=pilot_name,
        kind="character",
        type=pilot_gender,
        role="pilot",
        age=pilot_age,
        attrs={"relation": relation},
        traits=["bold"],
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        age=partner_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
    ))
    rover = world.add(Entity(
        id="rover",
        type="rover",
        label=vehicle.label,
        wheeled=True,
        attrs={"wheel_word": vehicle.wheel_word},
    ))
    path_ent = world.add(Entity(
        id="path",
        type="path",
        label=path.label,
        bumpy=path.bumpy,
    ))
    path_ent.meters["bump"] = float(path.bump)
    pilot.memes["bravery"] = BRAVERY_INIT
    partner.memes["caution"] = initial_caution(trait)
    partner.memes["trust"] = float(trust)

    play_setup(world, pilot, partner, theme, vehicle, path)
    world.para()
    notice_problem(world, partner, vehicle)
    tempt(world, pilot, theme, path)
    warn(world, partner, pilot, helper, vehicle, theme)

    averted = would_cease(relation, pilot_age, partner_age, trait)
    if averted:
        back_down(world, pilot, partner, helper, vehicle)
        world.para()
        rescue(world, helper, response, surprise, pilot, partner, vehicle)
        world.para()
        lesson(world, helper, pilot, partner, vehicle)
        outcome = "averted"
        contained = True
    else:
        defy(world, pilot, partner)
        world.para()
        launch(world, pilot, vehicle, path)
        alarm(world, partner, pilot, helper)
        world.para()
        contained = can_fix(response, path, delay)
        if contained:
            rescue(world, helper, response, surprise, pilot, partner, vehicle)
            world.para()
            lesson(world, helper, pilot, partner, vehicle)
            outcome = "contained"
        else:
            fail_fix(world, helper, response, vehicle)
            world.para()
            bad_ending(world, helper, pilot, partner, theme, vehicle, surprise)
            outcome = "bad"

    world.facts.update(
        pilot=pilot,
        partner=partner,
        helper=helper,
        theme=theme,
        vehicle_cfg=vehicle,
        path_cfg=path,
        response=response,
        surprise=surprise,
        relation=relation,
        outcome=outcome,
        delay=delay,
        severity=severity_of(path, delay),
        averted=averted,
        contained=contained,
    )
    return world


CURATED = [
    StoryParams(
        theme="moon",
        vehicle="wagon",
        path="gravel",
        response="replace_wheel",
        surprise="star_projector",
        pilot="Leo",
        pilot_gender="boy",
        partner="Mia",
        partner_gender="girl",
        helper="mother",
        trait="careful",
        delay=0,
        pilot_age=5,
        partner_age=7,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        theme="mars",
        vehicle="pedal_cart",
        path="bricks",
        response="tighten_bolts",
        surprise="glow_map",
        pilot="Max",
        pilot_gender="boy",
        partner="Zoe",
        partner_gender="girl",
        helper="father",
        trait="watchful",
        delay=0,
        pilot_age=6,
        partner_age=5,
        relation="friends",
        trust=5,
    ),
    StoryParams(
        theme="saturn",
        vehicle="wagon",
        path="gravel",
        response="tow_home",
        surprise="moon_cookies",
        pilot="Nora",
        pilot_gender="girl",
        partner="Finn",
        partner_gender="boy",
        helper="mother",
        trait="steady",
        delay=1,
        pilot_age=7,
        partner_age=5,
        relation="siblings",
        trust=6,
    ),
    StoryParams(
        theme="moon",
        vehicle="scooter_board",
        path="deck_boards",
        response="replace_wheel",
        surprise="glow_map",
        pilot="Ivy",
        pilot_gender="girl",
        partner="June",
        partner_gender="girl",
        helper="aunt",
        trait="sensible",
        delay=0,
        pilot_age=4,
        partner_age=6,
        relation="siblings",
        trust=3,
    ),
]


def explain_rejection(vehicle: Vehicle, path: Path) -> str:
    if not path.bumpy or path.bump < 1:
        return (
            f"(No story: {path.label} is too smooth for a loose wheel to matter, "
            f"so there is no honest crash risk and no reason to say cease.)"
        )
    if vehicle.wheels <= 0:
        return (
            f"(No story: {vehicle.label} has no rolling wheel to come loose, "
            f"so this space-rover problem does not happen.)"
        )
    return "(No story: this combination has no meaningful wheel hazard.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_cease(params.relation, params.pilot_age, params.partner_age, params.trait):
        return "averted"
    return "contained" if can_fix(RESPONSES[params.response], PATHS[params.path], params.delay) else "bad"


ASP_RULES = r"""
hazard(V, P) :- vehicle(V), path(P), wheels(V, W), W > 0, bumpy(P), bump(P, B), B >= 1.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, V, P) :- theme(T), hazard(V, P).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
partner_older :- relation(siblings), pilot_age(PA), partner_age(PB), PB > PA.
bonus(4) :- partner_older.
bonus(0) :- not partner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- partner_older, authority(A), bravery_init(BR), A > BR.

severity(B + D) :- chosen_path(P), bump(P, B), delay(D).
resp_power(PW) :- chosen_response(R), power(R, PW).
contained :- resp_power(PW), severity(S), PW >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(bad) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for vehicle_id, vehicle in VEHICLES.items():
        lines.append(asp.fact("vehicle", vehicle_id))
        lines.append(asp.fact("wheels", vehicle_id, vehicle.wheels))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("bump", path_id, path.bump))
        if path.bumpy:
            lines.append(asp.fact("bumpy", path_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
    extra = "\n".join([
        asp.fact("chosen_path", params.path),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("pilot_age", params.pilot_age),
        asp.fact("partner_age", params.partner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sens = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sens)} clingo={sorted(asp_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    diffs = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not diffs:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(diffs)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a loose rover wheel, a warning to cease, and either a happy surprise or a bad ending."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long help takes to make the repair")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.path and not PATHS[args.path].bumpy:
        vehicle = VEHICLES[args.vehicle] if args.vehicle else next(iter(VEHICLES.values()))
        raise StoryError(explain_rejection(vehicle, PATHS[args.path]))
    if args.vehicle and args.path:
        vehicle = VEHICLES[args.vehicle]
        path = PATHS[args.path]
        if not hazard_at_risk(vehicle, path):
            raise StoryError(explain_rejection(vehicle, path))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.vehicle is None or combo[1] == args.vehicle)
        and (args.path is None or combo[2] == args.path)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, vehicle_id, path_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    surprise_id = args.surprise or rng.choice(sorted(SURPRISES))
    pilot_name, pilot_gender = _pick_kid(rng)
    partner_name, partner_gender = _pick_kid(rng, avoid=pilot_name)
    helper = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    pilot_age, partner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        theme=theme_id,
        vehicle=vehicle_id,
        path=path_id,
        response=response_id,
        surprise=surprise_id,
        pilot=pilot_name,
        pilot_gender=pilot_gender,
        partner=partner_name,
        partner_gender=partner_gender,
        helper=helper,
        trait=trait,
        delay=delay,
        pilot_age=pilot_age,
        partner_age=partner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.vehicle not in VEHICLES:
        raise StoryError(f"(Unknown vehicle: {params.vehicle})")
    if params.path not in PATHS:
        raise StoryError(f"(Unknown path: {params.path})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise: {params.surprise})")
    if params.helper not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError(f"(Unknown helper: {params.helper})")

    vehicle = VEHICLES[params.vehicle]
    path = PATHS[params.path]
    if not hazard_at_risk(vehicle, path):
        raise StoryError(explain_rejection(vehicle, path))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        theme=THEMES[params.theme],
        vehicle=vehicle,
        path=path,
        response=RESPONSES[params.response],
        surprise=SURPRISES[params.surprise],
        pilot_name=params.pilot,
        pilot_gender=params.pilot_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        helper_type=params.helper,
        trait=params.trait,
        delay=params.delay,
        pilot_age=params.pilot_age,
        partner_age=params.partner_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, vehicle, path) combos:\n")
        for theme_id, vehicle_id, path_id in combos:
            print(f"  {theme_id:8} {vehicle_id:12} {path_id}")
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
                f"### {p.pilot} & {p.partner}: {p.vehicle} on {p.path} "
                f"({p.theme}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
