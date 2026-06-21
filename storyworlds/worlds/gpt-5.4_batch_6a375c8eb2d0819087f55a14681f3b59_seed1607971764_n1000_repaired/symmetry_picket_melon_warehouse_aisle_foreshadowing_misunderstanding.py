#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/symmetry_picket_melon_warehouse_aisle_foreshadowing_misunderstanding.py
===================================================================================================

A standalone storyworld about two children playing superheroes in a warehouse
aisle, a neat melon display, a nearby stack of picket fence boards, and a
misunderstood warning that nearly turns a tidy scene into a rolling mess.

The world model tracks physical state (wobble, rolling, bruising, safety) and
emotional state (pride, caution, fear, embarrassment, relief). The rendered
story is driven by those state changes rather than by a single frozen template.

The core shape:

- Premise: superhero pretend-play in a warehouse aisle
- Foreshadowing: a melon near the edge already rocks a little
- Misunderstanding: a worker warns about the picket pallet, but the hero hears
  it as a crisis about the melon display
- Turn: the hero reaches for a melon to "save the day"
- Resolution: either the helper stops the mistake in time, or rolling melons are
  sensibly contained by a calm adult and worker

Run it
------
python storyworlds/worlds/gpt-5.4/symmetry_picket_melon_warehouse_aisle_foreshadowing_misunderstanding.py
python storyworlds/worlds/gpt-5.4/symmetry_picket_melon_warehouse_aisle_foreshadowing_misunderstanding.py --all
python storyworlds/worlds/gpt-5.4/symmetry_picket_melon_warehouse_aisle_foreshadowing_misunderstanding.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/symmetry_picket_melon_warehouse_aisle_foreshadowing_misunderstanding.py --trace
python storyworlds/worlds/gpt-5.4/symmetry_picket_melon_warehouse_aisle_foreshadowing_misunderstanding.py --verify
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
HERO_CONFIDENCE = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "watchful", "patient"}


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
    round_object: bool = False
    heavy: bool = False
    movable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class HeroTheme:
    id: str
    call: str
    boast: str
    finish: str
    team_word: str
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
class Display:
    id: str
    label: str
    the: str
    shape_text: str
    edge_text: str
    foreshadow: str
    severity: int
    rollable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class WarningLine:
    id: str
    text: str
    heard_as: str
    ambiguous: bool
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
        return [e for e in self.entities.values() if e.role in {"hero", "helper"}]

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


def _r_roll(world: World) -> list[str]:
    out: list[str] = []
    display = world.get("display")
    room = world.get("aisle")
    if display.meters["tipped"] < THRESHOLD:
        return out
    sig = ("roll", "display")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    display.meters["rolling"] += 1
    room.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__rolling__")
    return out


def _r_bruise(world: World) -> list[str]:
    out: list[str] = []
    display = world.get("display")
    if display.meters["rolling"] < THRESHOLD:
        return out
    sig = ("bruise", "display")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    display.meters["bruised"] += 1
    out.append("__bruised__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="roll", tag="physical", apply=_r_roll),
    Rule(name="bruise", tag="physical", apply=_r_bruise),
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


def hazard_at_risk(display: Display, warning: WarningLine) -> bool:
    return display.rollable and warning.ambiguous


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def spill_severity(display: Display, delay: int) -> int:
    return display.severity + delay


def is_contained(response: Response, display: Display, delay: int) -> bool:
    return response.power >= spill_severity(display, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > hero_age
    authority = initial_caution(trait) + 1.0 + (4.0 if helper_older else 0.0)
    return helper_older and authority > HERO_CONFIDENCE


def predict_spill(world: World) -> dict:
    sim = world.copy()
    _do_grab(sim, narrate=False)
    return {
        "rolling": sim.get("display").meters["rolling"] >= THRESHOLD,
        "danger": sim.get("aisle").meters["danger"],
        "bruised": sim.get("display").meters["bruised"] >= THRESHOLD,
    }


def _do_grab(world: World, narrate: bool = True) -> None:
    display = world.get("display")
    display.meters["tipped"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, helper: Entity, parent: Entity,
          theme: HeroTheme, display: Display) -> None:
    for kid in (hero, helper):
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    world.say(
        f"On a bright shopping trip, {hero.id} and {helper.id} marched beside "
        f"{parent.label_word} through a warehouse aisle as if it were a secret rescue base."
    )
    world.say(
        f'"{theme.call}!" whispered {hero.id}. "{theme.boast}"'
    )
    world.say(
        f"At the end of the aisle stood {display.the}, stacked in {display.shape_text}. "
        f"The green rinds made a kind of symmetry that looked almost magical."
    )


def foreshadow(world: World, helper: Entity, display: Display) -> None:
    helper.memes["caution"] += 1
    world.say(
        f"But {helper.id} noticed something small: {display.foreshadow}. "
        f"{helper.pronoun().capitalize()} kept watching it instead of charging ahead."
    )


def picket_scene(world: World) -> None:
    world.say(
        "Right beside the fruit sat a long pallet of white picket boards wrapped in plastic, "
        "waiting to be wheeled to another part of the store."
    )


def worker_warning(world: World, worker: Entity, warning: WarningLine) -> None:
    world.say(
        f"A store worker in a bright vest lifted one hand and called, "
        f'"{warning.text}"'
    )


def misunderstanding(world: World, hero: Entity, helper: Entity, warning: WarningLine) -> None:
    pred = predict_spill(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_rolling"] = pred["rolling"]
    hero.memes["bravado"] += 1
    helper.memes["caution"] += 1
    world.say(
        f"{hero.id} blinked. To {hero.pronoun('object')}, it sounded as if {warning.heard_as}. "
        f"The warning was really about the picket pallet, but {hero.id} heard a superhero alarm."
    )
    world.say(
        f'"Then {theme_line(hero)}!" {hero.id} gasped, and {helper.id} opened '
        f"{helper.pronoun('possessive')} mouth to explain."
    )


def theme_line(hero: Entity) -> str:
    return hero.attrs.get("battle_cry", "hero time")


def back_down(world: World, hero: Entity, helper: Entity, parent: Entity,
              theme: HeroTheme) -> None:
    hero.memes["bravery"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'Before {hero.id} could touch anything, {helper.id} caught {hero.pronoun("possessive")} sleeve. '
        f'"Wait," {helper.pronoun()} said. "The worker means the picket pallet. '
        f'The melons are not asking for a rescue."'
    )
    world.say(
        f"{hero.id} froze, looked again, and saw that {helper.id} was right. "
        f"The aisle felt less like a battle and more like a place for careful feet."
    )
    world.say(
        f"{parent.label_word.capitalize()} squeezed both small shoulders. "
        f'"Real heroes look twice before they leap," {parent.pronoun()} said.'
    )
    world.para()
    world.say(
        f"A moment later the worker straightened the edge tray, the wobbling melon settled down, "
        f"and the lovely symmetry held. {hero.id} grinned at {helper.id}. "
        f'"Good catch, {theme.team_word}," {hero.pronoun()} said.'
    )
    world.say(
        f"Then the two aisle heroes rolled on with the cart, saving the day by leaving the melons exactly where they belonged."
    )


def charge(world: World, hero: Entity, theme: HeroTheme) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'{hero.id} did not wait. "{theme.finish}!" {hero.pronoun().capitalize()} cried, '
        f"darting toward the top melon with both hands ready."
    )


def topple(world: World, hero: Entity, helper: Entity, display: Display) -> None:
    _do_grab(world, narrate=False)
    world.say(
        f"The first touch was tiny, but it was enough. {display.The} lost its neat symmetry, "
        f"and one round melon bumped another."
    )
    world.say(
        f'"{hero.id}, stop!" shouted {helper.id}, but three melons were already rolling down the aisle like runaway cannonballs.'
    )


def alarm(world: World, parent: Entity, worker: Entity) -> None:
    world.say(f'"Easy! Back up, please!" called the worker.')
    world.say(f'{parent.label_word.capitalize()} pulled the children behind the cart in one quick step.')


def rescue(world: World, parent: Entity, worker: Entity, response: Response,
           display: Display) -> None:
    display_ent = world.get("display")
    display_ent.meters["rolling"] = 0.0
    display_ent.meters["tipped"] = 0.0
    world.get("aisle").meters["danger"] = 0.0
    body = response.text
    world.say(
        f"{worker.label.capitalize()} and {parent.label_word} moved at once. "
        f"{body}."
    )
    world.say(
        f"Soon the runaway melon thumps stopped, and only one scuffed corner of the display showed where the trouble had been."
    )


def lesson(world: World, parent: Entity, hero: Entity, helper: Entity,
           theme: HeroTheme) -> None:
    for kid in (hero, helper):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    hero.memes["embarrassment"] += 1
    world.say(
        f"{parent.label_word.capitalize()} knelt so {parent.pronoun()} was eye to eye with them. "
        f'"You were trying to help," {parent.pronoun()} said softly, "but helpers have to understand the danger first."'
    )
    world.say(
        f'{hero.id} nodded. "{theme.team_word.capitalize()} should listen before launching," {hero.pronoun()} admitted.'
    )
    world.say(
        f"{helper.id} slipped a hand into {hero.id}'s, and the two of them gave the worker a quiet sorry."
    )


def safe_job(world: World, worker: Entity, hero: Entity, helper: Entity,
             theme: HeroTheme) -> None:
    for kid in (hero, helper):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.para()
    world.say(
        f"The worker smiled and handed them a safe mission instead: holding the end of the paper list while the cart stayed still."
    )
    world.say(
        f"{hero.id} and {helper.id} stood straight as sidekicks on duty while the last melon was tucked back into place."
    )
    world.say(
        f"When they finally rolled away, the aisle looked calm again, the display's symmetry was whole, "
        f"and the heroes knew that careful listening could be its own superpower."
    )


def rescue_fail(world: World, parent: Entity, worker: Entity, response: Response) -> None:
    display = world.get("display")
    display.meters["rolling"] += 1
    world.get("aisle").meters["danger"] += 1
    world.say(
        f"{worker.label.capitalize()} and {parent.label_word} {response.fail}."
    )
    world.say(
        "The melons kept wobbling and knocking into one another until the whole front edge had to be emptied onto padded trays."
    )


def sad_end(world: World, parent: Entity, hero: Entity, helper: Entity) -> None:
    for kid in (hero, helper):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    hero.memes["embarrassment"] += 1
    world.say(
        f"No one was hurt, but several melons were bruised and the shining display was gone. "
        f"The warehouse aisle looked suddenly ordinary and tired."
    )
    world.say(
        f'{parent.label_word.capitalize()} hugged the children close. "Stores are for careful hands," '
        f'{parent.pronoun()} said. {hero.id} whispered sorry first, and {helper.id} whispered it too.'
    )
    world.say(
        "After that, they walked more slowly, and every warning they heard got listened to all the way to the end."
    )


def tell(theme: HeroTheme, display: Display, warning: WarningLine, response: Response,
         hero_name: str = "Milo", hero_gender: str = "boy",
         helper_name: str = "Nia", helper_gender: str = "girl",
         parent_type: str = "mother", worker_label: str = "the worker",
         trait: str = "careful", delay: int = 0, hero_age: int = 5,
         helper_age: int = 7, relation: str = "siblings", trust: int = 6) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        age=hero_age,
        traits=["bold"],
        attrs={"relation": relation, "battle_cry": theme.finish.lower()},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        age=helper_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    worker = world.add(Entity(
        id="Worker",
        kind="character",
        type="worker",
        role="worker",
        label=worker_label,
    ))
    aisle = world.add(Entity(
        id="aisle",
        type="place",
        label="the warehouse aisle",
        heavy=True,
        movable=False,
    ))
    display_ent = world.add(Entity(
        id="display",
        type="display",
        label=display.label,
        attrs={"config": display.id},
    ))
    picket = world.add(Entity(
        id="picket",
        type="pallet",
        label="the picket pallet",
        heavy=True,
        movable=False,
    ))

    hero.memes["bravery"] = HERO_CONFIDENCE
    helper.memes["caution"] = initial_caution(trait)
    helper.memes["trust"] = float(trust)
    aisle.meters["danger"] = 0.0
    display_ent.meters["tipped"] = 0.0
    display_ent.meters["rolling"] = 0.0
    display_ent.meters["bruised"] = 0.0
    world.facts["predicted_danger"] = 0
    world.facts["predicted_rolling"] = False

    setup(world, hero, helper, parent, theme, display)
    foreshadow(world, helper, display)
    picket_scene(world)

    world.para()
    worker_warning(world, worker, warning)
    misunderstanding(world, hero, helper, warning)

    averted = would_avert(relation, hero_age, helper_age, trait)

    if averted:
        back_down(world, hero, helper, parent, theme)
        severity = 0
        contained = True
    else:
        charge(world, hero, theme)
        world.para()
        topple(world, hero, helper, display)
        alarm(world, parent, worker)

        severity = spill_severity(display, delay)
        display_ent.meters["severity"] = float(severity)
        contained = is_contained(response, display, delay)

        world.para()
        if contained:
            rescue(world, parent, worker, response, display)
            lesson(world, parent, hero, helper, theme)
            safe_job(world, worker, hero, helper, theme)
        else:
            rescue_fail(world, parent, worker, response)
            sad_end(world, parent, hero, helper)

    outcome = "averted" if averted else ("contained" if contained else "spilled")
    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        worker=worker,
        theme=theme,
        display_cfg=display,
        display=display_ent,
        warning=warning,
        response=response,
        picket=picket,
        relation=relation,
        ignited=display_ent.meters["rolling"] >= THRESHOLD or outcome != "averted",
        outcome=outcome,
        severity=severity,
        delay=delay,
        rescued=contained,
        promised=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "comet": HeroTheme(
        id="comet",
        call="Aisle Avengers",
        boast="Captain Comet sees danger before anyone else",
        finish="Comet Save",
        team_word="partner",
        tags={"superhero"},
    ),
    "thunder": HeroTheme(
        id="thunder",
        call="Thunder Patrol",
        boast="Thunder Scout can zip trouble into a safe corner",
        finish="Thunder Dash",
        team_word="sidekick",
        tags={"superhero"},
    ),
    "shield": HeroTheme(
        id="shield",
        call="Shield Squad",
        boast="Shield Star keeps every shopper safe",
        finish="Shield Sweep",
        team_word="teammate",
        tags={"superhero"},
    ),
}

DISPLAYS = {
    "pyramid": Display(
        id="pyramid",
        label="melon pyramid",
        the="the melon pyramid",
        shape_text="a careful pyramid, green and striped from bottom to top",
        edge_text="one top melon sat nearest the edge",
        foreshadow="one top melon gave the faintest rock, then settled again",
        severity=2,
        rollable=True,
        tags={"melon", "symmetry"},
    ),
    "wall": Display(
        id="wall",
        label="melon wall",
        the="the melon wall",
        shape_text="a neat stepped wall, each round fruit nested against the next",
        edge_text="a side melon sat a little proud of the row",
        foreshadow="a side melon leaned the tiniest bit away from its cardboard lip",
        severity=1,
        rollable=True,
        tags={"melon", "symmetry"},
    ),
    "bin": Display(
        id="bin",
        label="melon bin",
        the="the melon bin",
        shape_text="a low produce bin with melons resting deep inside",
        edge_text="the melons sat well below the rim",
        foreshadow="even the shiniest melon stayed tucked safely in place",
        severity=0,
        rollable=False,
        tags={"melon"},
    ),
}

WARNINGS = {
    "clear_picket": WarningLine(
        id="clear_picket",
        text="Stay back from the picket pallet while I fix this display, please.",
        heard_as="the picket stack was making the melon display fail",
        ambiguous=True,
        tags={"misunderstanding", "picket"},
    ),
    "keep_symmetry": WarningLine(
        id="keep_symmetry",
        text="I need room by the picket side to keep the symmetry right here.",
        heard_as="someone had to save the symmetry of the melons this instant",
        ambiguous=True,
        tags={"misunderstanding", "picket", "symmetry"},
    ),
    "plain": WarningLine(
        id="plain",
        text="Please do not touch the melons while I tighten the tray.",
        heard_as="nothing confusing at all",
        ambiguous=False,
        tags={"clear"},
    ),
}

RESPONSES = {
    "cart_block": Response(
        id="cart_block",
        sense=3,
        power=3,
        text="the worker swung an empty flat cart across the open space while the parent caught the nearest rolling melon with both hands",
        fail="tried to block the rolling fruit with the cart, but the gap was already too wide",
        qa_text="used a flat cart to block the aisle and caught the nearest rolling melon",
        tags={"cart", "warehouse", "safety"},
    ),
    "cardboard_corral": Response(
        id="cardboard_corral",
        sense=3,
        power=2,
        text="the worker dropped two cardboard trays to make a little corral, and the parent nudged the rolling melon into it with a shoe",
        fail="threw down cardboard trays, but the melons slipped around them and kept going",
        qa_text="made a cardboard corral and guided the rolling melons into it",
        tags={"cardboard", "warehouse", "safety"},
    ),
    "hands_only": Response(
        id="hands_only",
        sense=2,
        power=1,
        text="the worker and parent knelt quickly and trapped the first melon between their palms before it could reach a shopper",
        fail="reached with their hands, but too many melons were already rolling at once",
        qa_text="knelt quickly and stopped the first rolling melon with their hands",
        tags={"hands", "safety"},
    ),
    "kick_stop": Response(
        id="kick_stop",
        sense=1,
        power=1,
        text="the worker kicked at a melon and knocked it toward the pallet",
        fail="kicked at the rolling fruit, which only made it skip farther down the aisle",
        qa_text="kicked at the rolling melon",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Nia", "Ava", "Maya", "Ruby", "Skye", "Lena", "Zoe", "Iris"]
BOY_NAMES = ["Milo", "Theo", "Jace", "Leo", "Finn", "Owen", "Ezra", "Noah"]
TRAITS = ["careful", "steady", "watchful", "patient", "curious", "quick"]
WORKER_LABELS = ["the worker", "the store worker", "the aisle helper"]


@dataclass
class StoryParams:
    theme: str
    display: str
    warning: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    worker_label: str
    delay: int = 0
    hero_age: int = 5
    helper_age: int = 7
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
    "symmetry": [
        (
            "What does symmetry mean?",
            "Symmetry means parts match each other in a balanced way. When something has symmetry, one side can look like the other side."
        )
    ],
    "picket": [
        (
            "What is a picket?",
            "A picket is one upright board in a picket fence. A bundle of pickets can be stacked together in a store before someone builds the fence."
        )
    ],
    "melon": [
        (
            "Why do melons roll easily?",
            "Melons are round, so they can start rolling when a display tips or someone bumps them. Round things do not stay still as easily as flat boxes."
        )
    ],
    "warehouse": [
        (
            "What is a warehouse aisle?",
            "A warehouse aisle is a long path inside a very big store where tall shelves and pallets hold goods. People walk carts through it to shop."
        )
    ],
    "cart": [
        (
            "Why can a cart help stop rolling things?",
            "A cart can make a firm barrier across an open space. That gives rolling things a place to stop instead of traveling farther."
        )
    ],
    "cardboard": [
        (
            "Why do stores use cardboard trays under fruit?",
            "Cardboard trays help hold round fruit in place so it does not roll away. They also keep groups of fruit together while workers stack them."
        )
    ],
    "safety": [
        (
            "What should you do when a worker gives a safety warning?",
            "Stop and listen to the whole warning first. Clear directions help you understand the real danger before you move."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or thinks the wrong meaning. Asking one calm question can often fix it."
        )
    ],
}
KNOWLEDGE_ORDER = ["warehouse", "melon", "symmetry", "picket", "cart", "cardboard", "safety", "misunderstanding"]


def pair_noun(hero: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and helper.type == "boy":
            return "two brothers"
        if hero.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    display = f["display_cfg"]
    warning = f["warning"]
    outcome = f["outcome"]
    base = (
        f'Write a short superhero story for a 3-to-5-year-old set in a warehouse aisle. '
        f'Include the words "symmetry", "picket", and "melon".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle story where {hero.id} misunderstands a worker's warning about a picket pallet, "
            f"but {helper.id} explains it in time and the melon display keeps its symmetry.",
            f"Write a superhero-style near-miss where a child almost rushes to rescue {display.the}, "
            f"then learns that listening carefully can be a real superpower from {parent.label_word}.",
        ]
    if outcome == "spilled":
        return [
            base,
            f"Tell a cautionary superhero story where {hero.id} mistakes '{warning.text}' for a cry of danger, "
            f"touches {display.the}, and several melons are bruised before the adults can stop the mess.",
            "Write a story with foreshadowing and misunderstanding where a child means well, causes a rolling fruit spill, and learns to listen all the way through.",
        ]
    return [
        base,
        f"Tell a superhero-style story where {hero.id} hears a worker's warning the wrong way, reaches for a melon, "
        f"and a calm grown-up team stops the rolling fruit safely.",
        f"Write a story that uses foreshadowing, includes a picket pallet beside a melon display, and ends with the children helping in a safer way.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    worker = f["worker"]
    display = f["display_cfg"]
    warning = f["warning"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(hero, helper, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {helper.id}, who were pretending to be superheroes in a warehouse aisle. "
            f"It also includes {hero.id}'s {parent.label_word} and {worker.label}."
        ),
        (
            "What did the children see in the aisle?",
            f"They saw {display.the} beside a pallet of picket boards. "
            f"The display looked special because its neat symmetry made the melons seem carefully lined up."
        ),
        (
            "What was the foreshadowing clue?",
            f"{helper.id} noticed that {display.foreshadow}. "
            f"That tiny wobble hinted that touching the display could make the trouble bigger."
        ),
        (
            f"What misunderstanding did {hero.id} have?",
            f"{hero.id} heard the worker's warning and thought {warning.heard_as}. "
            f"The worker was really talking about the picket pallet and needing space, not asking anyone to grab a melon."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How was the problem stopped before anything rolled?",
                f"{helper.id} caught {hero.id}'s sleeve and explained the warning in time. "
                f"Because {hero.id} paused and listened, the melon display kept its symmetry and no fruit rolled away."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended calmly and happily. The worker fixed the display, and the children moved on feeling proud that careful listening had saved the day."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                "What happened when the hero touched the display?",
                f"The neat stack lost its symmetry and several melons began to roll down the aisle. "
                f"The earlier wobble mattered because the display was already a little unstable."
            )
        )
        qa.append(
            (
                "How did the grown-ups solve the problem?",
                f"{worker.label.capitalize()} and {parent.label_word} {response.qa_text}. "
                f"They acted quickly and used the right method, so the rolling fruit stopped before the whole display had to come down."
            )
        )
        qa.append(
            (
                f"What did {hero.id} learn?",
                f"{hero.id} learned that wanting to help is not enough by itself. "
                f"A real helper listens carefully first so the rescue fits the real problem."
            )
        )
    else:
        qa.append(
            (
                "Why did the accident get worse?",
                f"The display was already a little wobbly, and the wrong rescue started the first shift. "
                f"After that, too many melons rolled at once for the response to stop them quickly."
            )
        )
        qa.append(
            (
                "How did the story end?",
                "No one got hurt, but several melons were bruised and the beautiful display had to be taken apart. "
                "The children left more quietly, having learned to listen to warnings all the way through."
            )
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"warehouse", "melon", "safety", "misunderstanding"}
    tags |= set(f["display_cfg"].tags)
    tags |= set(f["warning"].tags)
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
        theme="comet",
        display="pyramid",
        warning="clear_picket",
        response="cart_block",
        hero="Milo",
        hero_gender="boy",
        helper="Nia",
        helper_gender="girl",
        parent="mother",
        trait="careful",
        worker_label="the worker",
        delay=0,
        hero_age=5,
        helper_age=7,
        relation="siblings",
        trust=6,
    ),
    StoryParams(
        theme="shield",
        display="wall",
        warning="keep_symmetry",
        response="cardboard_corral",
        hero="Ruby",
        hero_gender="girl",
        helper="Leo",
        helper_gender="boy",
        parent="father",
        trait="quick",
        worker_label="the store worker",
        delay=0,
        hero_age=6,
        helper_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        theme="thunder",
        display="pyramid",
        warning="keep_symmetry",
        response="hands_only",
        hero="Theo",
        hero_gender="boy",
        helper="Maya",
        helper_gender="girl",
        parent="mother",
        trait="curious",
        worker_label="the aisle helper",
        delay=1,
        hero_age=6,
        helper_age=5,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        theme="shield",
        display="wall",
        warning="clear_picket",
        response="cart_block",
        hero="Skye",
        hero_gender="girl",
        helper="Iris",
        helper_gender="girl",
        parent="mother",
        trait="steady",
        worker_label="the worker",
        delay=0,
        hero_age=4,
        helper_age=7,
        relation="siblings",
        trust=7,
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for display_id, display in DISPLAYS.items():
        for warning_id, warning in WARNINGS.items():
            if hazard_at_risk(display, warning):
                combos.append((display_id, warning_id))
    return combos


def explain_rejection(display: Display, warning: WarningLine) -> str:
    if not display.rollable:
        return (
            f"(No story: {display.the} sits low and safe, so a misunderstanding would not create a believable rolling-melon problem.)"
        )
    if not warning.ambiguous:
        return (
            "(No story: this warning is too clear to support a misunderstanding, so the story's turn would not honestly happen.)"
        )
    return "(No story: this combination does not create the needed risk.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.helper_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], DISPLAYS[params.display], params.delay)
    return "contained" if contained else "spilled"


ASP_RULES = r"""
hazard(D, W) :- rollable(D), ambiguous(W).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(D, W) :- display(D), warning(W), hazard(D, W).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
helper_older :- relation(siblings), hero_age(H), helper_age(A), A > H.
bonus(4) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- helper_older, authority(A), hero_confidence(HC), A > HC.

severity(S + D) :- chosen_display(X), base_severity(X, S), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(spilled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for display_id, display in DISPLAYS.items():
        lines.append(asp.fact("display", display_id))
        if display.rollable:
            lines.append(asp.fact("rollable", display_id))
        lines.append(asp.fact("base_severity", display_id, display.severity))
    for warning_id, warning in WARNINGS.items():
        lines.append(asp.fact("warning", warning_id))
        if warning.ambiguous:
            lines.append(asp.fact("ambiguous", warning_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("hero_confidence", int(HERO_CONFIDENCE)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_display", params.display),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def _smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story is empty.")
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        emit(sample, trace=False, qa=True, header="### smoke")
    rendered = sink.getvalue()
    if "melon" not in sample.story or "picket" not in sample.story or "symmetry" not in sample.story:
        raise StoryError("Smoke test failed: required seed words are missing from the story.")
    if "Q:" not in rendered:
        raise StoryError("Smoke test failed: QA emission did not render.")


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

    c_sense = set(asp_sensible())
    p_sense = {r.id for r in sensible_responses()}
    if c_sense == p_sense:
        print(f"OK: sensible responses match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(120):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: superhero children, a warehouse aisle, a picket pallet, and a melon misunderstanding."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--display", choices=DISPLAYS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="How much head start the rolling fruit gets.")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.display and args.warning:
        display = DISPLAYS[args.display]
        warning = WARNINGS[args.warning]
        if not hazard_at_risk(display, warning):
            raise StoryError(explain_rejection(display, warning))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.display is None or combo[0] == args.display)
        and (args.warning is None or combo[1] == args.warning)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    display_id, warning_id = rng.choice(sorted(combos))
    theme_id = args.theme or rng.choice(sorted(THEMES))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero, hero_gender = _pick_kid(rng)
    helper, helper_gender = _pick_kid(rng, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    worker_label = rng.choice(WORKER_LABELS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    hero_age, helper_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)

    return StoryParams(
        theme=theme_id,
        display=display_id,
        warning=warning_id,
        response=response_id,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
        worker_label=worker_label,
        delay=delay,
        hero_age=hero_age,
        helper_age=helper_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme '{params.theme}'.)")
    if params.display not in DISPLAYS:
        raise StoryError(f"(Unknown display '{params.display}'.)")
    if params.warning not in WARNINGS:
        raise StoryError(f"(Unknown warning '{params.warning}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}'.)")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type '{params.parent}'.)")
    if params.response in RESPONSES and RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(DISPLAYS[params.display], WARNINGS[params.warning]):
        raise StoryError(explain_rejection(DISPLAYS[params.display], WARNINGS[params.warning]))

    world = tell(
        theme=THEMES[params.theme],
        display=DISPLAYS[params.display],
        warning=WARNINGS[params.warning],
        response=RESPONSES[params.response],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        worker_label=params.worker_label,
        trait=params.trait,
        delay=params.delay,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
        relation=params.relation,
        trust=params.trust,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (display, warning) combos:\n")
        for display_id, warning_id in combos:
            print(f"  {display_id:8} {warning_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.hero} & {p.helper}: {p.display} with {p.warning} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
