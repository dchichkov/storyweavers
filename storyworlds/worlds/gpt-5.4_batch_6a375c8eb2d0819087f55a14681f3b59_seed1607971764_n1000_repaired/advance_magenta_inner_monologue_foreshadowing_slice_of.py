#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/advance_magenta_inner_monologue_foreshadowing_slice_of.py
====================================================================================

A standalone story world for gentle slice-of-life stories about a child making a
magenta craft in advance for a small family or neighborhood event, feeling the
urge to rush, and learning to slow down long enough to carry the craft safely.

The domain is intentionally small and concrete:

- a child makes a handmade paper thing in magenta
- the paper is still wet or tacky
- a helper predicts what will happen if it is moved too soon
- they choose a drying method and a carrying method
- the final walk to the event proves whether they really solved the problem

The prose includes:
- inner monologue: the child quietly thinking about whether to rush
- foreshadowing: the shiny, damp surface that later matters

Run it
------
    python storyworlds/worlds/gpt-5.4/advance_magenta_inner_monologue_foreshadowing_slice_of.py
    python storyworlds/worlds/gpt-5.4/advance_magenta_inner_monologue_foreshadowing_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/advance_magenta_inner_monologue_foreshadowing_slice_of.py --qa --seed 7
    python storyworlds/worlds/gpt-5.4/advance_magenta_inner_monologue_foreshadowing_slice_of.py --verify
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    surface: str
    light: str
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
class Event:
    id: str
    label: str
    crowd: str
    closing: str
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
class Project:
    id: str
    label: str
    phrase: str
    shape_line: str
    carried_as: str
    display_line: str
    allowed_carriers: set[str] = field(default_factory=set)
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
class Medium:
    id: str
    label: str
    making_line: str
    shine_line: str
    wetness: int
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
class Carrier:
    id: str
    label: str
    phrase: str
    carry_line: str
    fits: set[str] = field(default_factory=set)
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
class Dryer:
    id: str
    label: str
    phrase: str
    power: int
    line: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    craft = world.get("craft")
    if craft.meters["moved"] < THRESHOLD or craft.meters["wet"] < THRESHOLD:
        return out
    sig = ("smudge", int(craft.meters["moved"]), int(craft.meters["wet"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    craft.meters["smudged"] += 1
    world.get("hero").memes["alarm"] += 1
    out.append("__smudge__")
    return out


CAUSAL_RULES = [
    Rule(name="smudge", tag="physical", apply=_r_smudge),
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


def carrier_fits(project: Project, carrier: Carrier) -> bool:
    return carrier.id in project.allowed_carriers and project.id in carrier.fits


def effective_drying(medium: Medium, dryer: Dryer, wait: int) -> int:
    return dryer.power + wait


def is_crisp(project: Project, medium: Medium, carrier: Carrier, dryer: Dryer, wait: int) -> bool:
    return carrier_fits(project, carrier) and effective_drying(medium, dryer, wait) >= medium.wetness


def predict_move(world: World, wait: int) -> dict:
    sim = world.copy()
    craft = sim.get("craft")
    craft.meters["wet"] = max(0.0, craft.meters["wet"] - wait)
    craft.meters["moved"] += 1
    propagate(sim, narrate=False)
    return {
        "smudged": craft.meters["smudged"] >= THRESHOLD,
        "wet_left": craft.meters["wet"],
    }


def make_craft(world: World, hero: Entity, event: Event, project: Project, medium: Medium) -> None:
    craft = world.add(Entity(
        id="craft",
        type=project.id,
        label=project.label,
        phrase=project.phrase,
        role="craft",
        attrs={"event": event.id, "color": "magenta", "project_id": project.id, "medium_id": medium.id},
    ))
    craft.meters["wet"] = float(medium.wetness)
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} started {project.phrase} in advance for {event.label}. "
        f"At {world.place.surface}, with {world.place.light}, {hero.pronoun()} worked carefully in magenta."
    )
    world.say(
        f"{medium.making_line} The {project.label} began to look just right for {event.label}."
    )


def foreshadow(world: World, hero: Entity, project: Project, medium: Medium) -> None:
    world.say(
        f"But the fresh color still looked alive on the paper. {medium.shine_line} "
        f"{project.shape_line}"
    )
    world.facts["foreshadowed"] = True


def inner_monologue(world: World, hero: Entity, event: Event, project: Project) -> None:
    hero.memes["impatience"] += 1
    world.say(
        f'{hero.id} looked toward the door and thought, '
        f'"If I carry the {project.label} there right now, maybe it will be fine. '
        f'I want to see it waiting for {event.label} already."'
    )


def helper_warning(world: World, hero: Entity, helper: Entity, project: Project, medium: Medium) -> None:
    pred_now = predict_move(world, wait=0)
    world.facts["predicted_smudge_now"] = pred_now["smudged"]
    world.facts["predicted_wet_now"] = pred_now["wet_left"]
    hero.memes["worry"] += 1
    if pred_now["smudged"]:
        world.say(
            f'{helper.id} noticed the shine and said, '
            f'"Not yet. The magenta is still damp, and if the {project.label} moves now, it will smear."'
        )
    else:
        world.say(
            f'{helper.id} ran a finger through the air above the paper and said, '
            f'"Almost. It needs one more quiet minute before we carry it."'
        )


def choose_fix(world: World, hero: Entity, helper: Entity, dryer: Dryer, carrier: Carrier, wait: int) -> None:
    craft = world.get("craft")
    world.say(
        f'{helper.id} helped {hero.id} {dryer.line} Then {helper.pronoun()} set out {carrier.phrase} for the walk.'
    )
    craft.attrs["dryer"] = dryer.id
    craft.attrs["carrier"] = carrier.id
    craft.attrs["wait"] = wait
    craft.meters["wet"] = max(0.0, craft.meters["wet"] - effective_drying(MEDIUMS[craft.attrs["medium_id"]], dryer, wait))
    craft.meters["supported"] = 1.0
    hero.memes["hope"] += 1
    if wait > 0:
        world.say(
            f"{hero.id} counted slowly to {10 * wait} and kept {hero.pronoun('possessive')} hands still."
        )
    else:
        world.say(
            f"{hero.id} tried to be patient, even though the door suddenly seemed very far away."
        )


def carry_out(world: World, hero: Entity, event: Event, project: Project, carrier: Carrier) -> None:
    craft = world.get("craft")
    craft.meters["moved"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When it was time to go, {hero.id} {carrier.carry_line} and walked toward {event.label}."
    )


def ending(world: World, hero: Entity, helper: Entity, event: Event, project: Project) -> None:
    craft = world.get("craft")
    if craft.meters["smudged"] >= THRESHOLD:
        hero.memes["disappointment"] += 1
        helper.memes["comfort"] += 1
        world.say(
            f"Halfway there, one magenta stroke slid softly to the side. The {project.label} was still readable, "
            f"but now it carried a blurry corner where the color had not finished drying."
        )
        world.say(
            f'{helper.id} squeezed {hero.id}\'s shoulder. "{event.label.capitalize()} will still know it was made with care," '
            f'{helper.pronoun()} said.'
        )
        world.say(
            f"At {event.label}, {project.display_line} The little blur reminded {hero.id} that starting in advance only helps "
            f"if you leave enough quiet time for the work to finish."
        )
        world.facts["outcome"] = "smudged"
    else:
        hero.memes["relief"] += 1
        hero.memes["joy"] += 1
        world.say(
            f"This time the paper stayed smooth. The magenta lines held their edges, and the {project.label} looked neat in the light."
        )
        world.say(
            f"At {event.label}, {project.display_line} {event.closing}"
        )
        world.say(
            f"{hero.id} felt proud all over again. Waiting had been the quiet part of the job, but it was part of the job all the same."
        )
        world.facts["outcome"] = "crisp"


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        surface="the kitchen table",
        light="late-window sunshine",
        tags={"home"},
    ),
    "bedroom": Place(
        id="bedroom",
        label="the bedroom",
        surface="a small bedroom desk",
        light="a warm lamp",
        tags={"home"},
    ),
    "hallway": Place(
        id="hallway",
        label="the hallway",
        surface="a bench by the front door",
        light="pale afternoon light",
        tags={"home"},
    ),
}

EVENTS = {
    "bake_sale": Event(
        id="bake_sale",
        label="the building bake sale",
        crowd="neighbors",
        closing="Soon the sign stood beside the cookie plates, bright and cheerful.",
        tags={"bake_sale", "neighbors"},
    ),
    "music_night": Event(
        id="music_night",
        label="family music night",
        crowd="relatives",
        closing="Soon it rested near the piano, ready for everyone coming in with coats and smiles.",
        tags={"music", "family"},
    ),
    "welcome_visit": Event(
        id="welcome_visit",
        label="Grandma's visit",
        crowd="family",
        closing="Soon it leaned by the doorway, ready for Grandma to see first.",
        tags={"grandma", "family"},
    ),
}

PROJECTS = {
    "card": Project(
        id="card",
        label="card",
        phrase="a welcome card",
        shape_line="The folded edges wanted to spring open whenever a breeze crossed the room.",
        carried_as="the card",
        display_line="the little card propped up neatly on the side table.",
        allowed_carriers={"envelope", "folder"},
        tags={"card"},
    ),
    "poster": Project(
        id="poster",
        label="poster",
        phrase="a hand-lettered poster",
        shape_line="The wide paper gave the tiniest curl at one corner, as if it were thinking about flopping over.",
        carried_as="the poster",
        display_line="the poster sat straight against the wall, easy to read from the doorway.",
        allowed_carriers={"folder", "tray"},
        tags={"poster"},
    ),
    "banner": Project(
        id="banner",
        label="banner",
        phrase="a long paper banner",
        shape_line="The long strip of paper rippled a little whenever someone walked past.",
        carried_as="the banner",
        display_line="the banner unrolled across the shelf without a wrinkle.",
        allowed_carriers={"tube", "tray"},
        tags={"banner"},
    ),
}

MEDIUMS = {
    "paint": Medium(
        id="paint",
        label="paint",
        making_line="Small magenta brushstrokes bloomed across the paper in soft, careful lines.",
        shine_line="It shone in a damp way, like a tiny pond catching light.",
        wetness=2,
        tags={"paint", "magenta"},
    ),
    "ink": Medium(
        id="ink",
        label="ink",
        making_line="A magenta ink pen moved in slow loops and tidy letters.",
        shine_line="The newest strokes still glimmered whenever the paper tilted.",
        wetness=1,
        tags={"ink", "magenta"},
    ),
    "glitter_glue": Medium(
        id="glitter_glue",
        label="glitter glue",
        making_line="Magenta glitter glue made bright swirls that sparkled even before they dried.",
        shine_line="The shiny lines sat on top of the paper in little raised ridges.",
        wetness=1,
        tags={"glitter", "magenta"},
    ),
}

CARRIERS = {
    "envelope": Carrier(
        id="envelope",
        label="envelope",
        phrase="a big clean envelope",
        carry_line="slid the card into the envelope",
        fits={"card"},
        tags={"envelope"},
    ),
    "folder": Carrier(
        id="folder",
        label="folder",
        phrase="a stiff paper folder",
        carry_line="laid the paper inside the folder and held it flat with both hands",
        fits={"card", "poster"},
        tags={"folder"},
    ),
    "tray": Carrier(
        id="tray",
        label="tray",
        phrase="a flat baking tray",
        carry_line="carried the paper on the flat tray as carefully as a birthday cake",
        fits={"poster", "banner"},
        tags={"tray"},
    ),
    "tube": Carrier(
        id="tube",
        label="tube",
        phrase="a clean cardboard tube",
        carry_line="rolled the banner loosely and tucked it into the tube",
        fits={"banner"},
        tags={"tube"},
    ),
}

DRYERS = {
    "windowsill": Dryer(
        id="windowsill",
        label="windowsill",
        phrase="the windowsill",
        power=1,
        line="set the paper on the windowsill where the air could reach both sides.",
        tags={"air_dry"},
    ),
    "fan": Dryer(
        id="fan",
        label="fan",
        phrase="the fan",
        power=1,
        line="turned a little fan toward the paper and watched the fresh color stop shining so much.",
        tags={"fan"},
    ),
    "clothesline": Dryer(
        id="clothesline",
        label="clothesline",
        phrase="a string with clips",
        power=2,
        line="clipped the paper to a string by the window so it could hang flat and dry all over.",
        tags={"drying"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Ava", "Nora", "Lucy", "Maya", "Ella", "Zoe"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Eli", "Theo", "Max", "Sam", "Noah"]
TRAITS = ["careful", "eager", "thoughtful", "busy", "hopeful", "gentle"]


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str, str]] = []
    for place_id in PLACES:
        for event_id in EVENTS:
            for project_id, project in PROJECTS.items():
                for medium_id, medium in MEDIUMS.items():
                    if medium.wetness <= 0:
                        continue
                    for carrier_id, carrier in CARRIERS.items():
                        if not carrier_fits(project, carrier):
                            continue
                        for dryer_id in DRYERS:
                            combos.append((place_id, event_id, project_id, medium_id, carrier_id, dryer_id))
    return combos


@dataclass
class StoryParams:
    place: str
    event: str
    project: str
    medium: str
    carrier: str
    dryer: str
    wait: int = 1
    hero_name: str = "Mina"
    hero_gender: str = "girl"
    helper_name: str = "Mom"
    helper_type: str = "mother"
    trait: str = "careful"
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


def tell(
    place: Place,
    event: Event,
    project: Project,
    medium: Medium,
    carrier: Carrier,
    dryer: Dryer,
    wait: int,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_type: str,
    trait: str,
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        attrs={"trait": trait},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        attrs={},
    ))

    make_craft(world, hero, event, project, medium)
    foreshadow(world, hero, project, medium)

    world.para()
    inner_monologue(world, hero, event, project)
    helper_warning(world, hero, helper, project, medium)

    world.para()
    choose_fix(world, hero, helper, dryer, carrier, wait)
    carry_out(world, hero, event, project, carrier)
    ending(world, hero, helper, event, project)

    craft = world.get("craft")
    world.facts.update(
        hero=hero,
        helper=helper,
        event=event,
        project_cfg=project,
        medium=medium,
        carrier=carrier,
        dryer=dryer,
        craft=craft,
        wait=wait,
        crisp=craft.meters["smudged"] < THRESHOLD,
        predicted_smudge_now=world.facts.get("predicted_smudge_now", False),
    )
    return world


KNOWLEDGE = {
    "paint": [
        (
            "Why does wet paint smear?",
            "Wet paint sits on top of the paper until the water in it dries. If you touch it or move it too soon, the color can slide out of place."
        )
    ],
    "ink": [
        (
            "Can fresh ink smear?",
            "Yes. Fresh ink needs a little time to sink in and dry, so rubbing it too soon can blur the letters."
        )
    ],
    "glitter": [
        (
            "Why should glitter glue dry before you carry paper?",
            "Glitter glue is thick and shiny when it is fresh. If the paper bends while it is still wet, the glue can smear or clump."
        )
    ],
    "folder": [
        (
            "Why does a stiff folder help carry paper?",
            "A stiff folder keeps the paper flat. That means the page bends less and the fresh color is less likely to rub."
        )
    ],
    "tray": [
        (
            "Why is a flat tray useful for carrying art?",
            "A flat tray supports the whole paper from underneath. That makes it easier to carry a big piece without wobbling it."
        )
    ],
    "tube": [
        (
            "What does a cardboard tube do for a long banner?",
            "A tube gives a long paper banner an easy shape to travel in. It helps keep the banner together instead of flapping around."
        )
    ],
    "air_dry": [
        (
            "Why does waiting help wet paper art?",
            "Waiting gives the wet color time to dry. Sometimes the safest part of making something is the quiet minute after you finish."
        )
    ],
    "fan": [
        (
            "How can a fan help paper art dry?",
            "A fan moves air over the wet surface. That can help the damp color dry faster."
        )
    ],
    "drying": [
        (
            "Why hang paper art while it dries?",
            "Hanging paper lets air reach it well and can keep it flatter. That helps the whole piece dry more evenly."
        )
    ],
    "grandma": [
        (
            "Why do people make welcome signs for a visit?",
            "A welcome sign shows care before someone even comes in. It can make a guest feel noticed and loved."
        )
    ],
    "bake_sale": [
        (
            "What is a bake sale?",
            "A bake sale is a small event where people share or sell homemade treats. Signs help everyone know where to go."
        )
    ],
    "music": [
        (
            "Why put out a sign before family music night?",
            "A sign can set the mood before the music starts. It helps a room feel ready and special."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "paint",
    "ink",
    "glitter",
    "folder",
    "tray",
    "tube",
    "air_dry",
    "fan",
    "drying",
    "grandma",
    "bake_sale",
    "music",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    event = f["event"]
    project = f["project_cfg"]
    medium = f["medium"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that uses the words "advance" and "magenta" and follows a child making a {project.label} for {event.label}.',
        f"Tell a gentle story where {hero.id} finishes a magenta {project.label} in advance, thinks about rushing, and learns that waiting is part of caring for the work.",
        f"Write a story with inner monologue and foreshadowing: the wet shine of fresh {medium.label} should matter later when the child needs to carry the paper safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    event = f["event"]
    project = f["project_cfg"]
    medium = f["medium"]
    carrier = f["carrier"]
    dryer = f["dryer"]
    wait = f["wait"]
    outcome = "crisp" if f["crisp"] else "smudged"

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who made a magenta {project.label} in advance for {event.label}, and {helper.id}, who helped {hero.pronoun('object')} slow down."
        ),
        (
            f"Why did {hero.id} want to hurry?",
            f"{hero.id} was excited to see the {project.label} already waiting at {event.label}. In {hero.pronoun('possessive')} head, carrying it right away felt faster than stopping to let the fresh color settle."
        ),
        (
            "What was the foreshadowing clue?",
            f"The clue was the shiny, damp look of the fresh magenta {medium.label}. That mattered later because the shine showed the paper was not ready to be moved yet."
        ),
        (
            f"How did {helper.id} help solve the problem?",
            f"{helper.id} helped {hero.id} dry the {project.label} with {dryer.phrase} and carry it in {carrier.phrase}. Those two choices gave the paper more time and steadier support."
        ),
    ]
    if outcome == "crisp":
        qa.append(
            (
                "How did the story end?",
                f"The {project.label} arrived neat and smooth at {event.label}. It stayed clean because the drying time was enough and {hero.id} carried it carefully."
            )
        )
    else:
        qa.append(
            (
                "Why did the paper still get a blur?",
                f"The paper was safer than before, but it still had a little wetness left when they carried it. Because of that, one magenta stroke slid and made a blurry corner on the way."
            )
        )
        qa.append(
            (
                "What did the child learn?",
                f"{hero.id} learned that making something in advance does not only mean starting early. It also means leaving enough quiet time for the work to dry before moving it."
            )
        )
    if wait > 0:
        qa.append(
            (
                f"Why did counting slowly help {hero.id}?",
                f"Counting slowly gave the fresh color more time to dry and gave {hero.id} something calm to do with that waiting time. The pause turned impatience into care."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["medium"].tags) | set(f["carrier"].tags) | set(f["dryer"].tags) | set(f["event"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or isinstance(v, int)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="kitchen",
        event="welcome_visit",
        project="card",
        medium="ink",
        carrier="envelope",
        dryer="windowsill",
        wait=1,
        hero_name="Mina",
        hero_gender="girl",
        helper_name="Mom",
        helper_type="mother",
        trait="careful",
    ),
    StoryParams(
        place="bedroom",
        event="bake_sale",
        project="poster",
        medium="paint",
        carrier="folder",
        dryer="clothesline",
        wait=0,
        hero_name="Leo",
        hero_gender="boy",
        helper_name="Dad",
        helper_type="father",
        trait="eager",
    ),
    StoryParams(
        place="hallway",
        event="music_night",
        project="banner",
        medium="paint",
        carrier="tube",
        dryer="windowsill",
        wait=0,
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Mom",
        helper_type="mother",
        trait="hopeful",
    ),
    StoryParams(
        place="kitchen",
        event="bake_sale",
        project="poster",
        medium="glitter_glue",
        carrier="tray",
        dryer="fan",
        wait=1,
        hero_name="Owen",
        hero_gender="boy",
        helper_name="Dad",
        helper_type="father",
        trait="thoughtful",
    ),
]


def explain_rejection(project: Project, carrier: Carrier) -> str:
    return (
        f"(No story: {carrier.phrase} does not suit a {project.label}. "
        f"Choose a carrier that can really hold the paper safely.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "crisp" if is_crisp(
        PROJECTS[params.project],
        MEDIUMS[params.medium],
        CARRIERS[params.carrier],
        DRYERS[params.dryer],
        params.wait,
    ) else "smudged"


ASP_RULES = r"""
wet_medium(M) :- medium(M), wetness(M,W), W > 0.
valid(P,E,Pr,M,C,D) :- place(P), event(E), project(Pr), medium(M), wet_medium(M),
                       carrier(C), dryer(D), allows(Pr,C), fits(C,Pr).

dry_total(T) :- chosen_dryer(D), power(D,P), wait(W), T = P + W.
crisp :- chosen_project(Pr), chosen_medium(M), chosen_carrier(C), chosen_dryer(D),
         allows(Pr,C), fits(C,Pr), wetness(M,W), dry_total(T), T >= W.
outcome(crisp) :- crisp.
outcome(smudged) :- not crisp.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for event_id in EVENTS:
        lines.append(asp.fact("event", event_id))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        for carrier_id in sorted(project.allowed_carriers):
            lines.append(asp.fact("allows", project_id, carrier_id))
    for medium_id, medium in MEDIUMS.items():
        lines.append(asp.fact("medium", medium_id))
        lines.append(asp.fact("wetness", medium_id, medium.wetness))
    for carrier_id, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", carrier_id))
        for project_id in sorted(carrier.fits):
            lines.append(asp.fact("fits", carrier_id, project_id))
    for dryer_id, dryer in DRYERS.items():
        lines.append(asp.fact("dryer", dryer_id))
        lines.append(asp.fact("power", dryer_id, dryer.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_project", params.project),
        asp.fact("chosen_medium", params.medium),
        asp.fact("chosen_carrier", params.carrier),
        asp.fact("chosen_dryer", params.dryer),
        asp.fact("wait", params.wait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"resolve_params failed on seed {seed}")
            continue
        cases.append(params)

    mismatches = []
    for params in cases:
        py = outcome_of(params)
        asp_val = asp_outcome(params)
        if py != asp_val:
            mismatches.append((params, py, asp_val))
    if mismatches:
        rc = 1
        print(f"MISMATCH in outcomes: {len(mismatches)} cases")
        for params, py, asp_val in mismatches[:5]:
            print(f"  {params} python={py} asp={asp_val}")
    else:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world: a child makes a magenta paper craft in advance, wants to rush, and learns to wait."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--medium", choices=MEDIUMS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--dryer", choices=DRYERS)
    ap.add_argument("--wait", type=int, choices=[0, 1], help="extra quiet minute after drying help")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.carrier:
        if not carrier_fits(PROJECTS[args.project], CARRIERS[args.carrier]):
            raise StoryError(explain_rejection(PROJECTS[args.project], CARRIERS[args.carrier]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.event is None or c[1] == args.event)
        and (args.project is None or c[2] == args.project)
        and (args.medium is None or c[3] == args.medium)
        and (args.carrier is None or c[4] == args.carrier)
        and (args.dryer is None or c[5] == args.dryer)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, event_id, project_id, medium_id, carrier_id, dryer_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    helper_name = "Mom" if parent == "mother" else "Dad"
    trait = rng.choice(TRAITS)
    wait = args.wait if args.wait is not None else rng.choice([0, 1])

    return StoryParams(
        place=place_id,
        event=event_id,
        project=project_id,
        medium=medium_id,
        carrier=carrier_id,
        dryer=dryer_id,
        wait=wait,
        hero_name=name,
        hero_gender=gender,
        helper_name=helper_name,
        helper_type=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.event not in EVENTS:
        raise StoryError(f"(Unknown event: {params.event})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.medium not in MEDIUMS:
        raise StoryError(f"(Unknown medium: {params.medium})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")
    if params.dryer not in DRYERS:
        raise StoryError(f"(Unknown dryer: {params.dryer})")
    if not carrier_fits(PROJECTS[params.project], CARRIERS[params.carrier]):
        raise StoryError(explain_rejection(PROJECTS[params.project], CARRIERS[params.carrier]))

    world = tell(
        place=PLACES[params.place],
        event=EVENTS[params.event],
        project=PROJECTS[params.project],
        medium=MEDIUMS[params.medium],
        carrier=CARRIERS[params.carrier],
        dryer=DRYERS[params.dryer],
        wait=params.wait,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/6.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, event, project, medium, carrier, dryer) combos:\n")
        for combo in combos:
            print("  " + "  ".join(str(x) for x in combo))
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
                f"### {p.hero_name}: {p.project} for {p.event} "
                f"({p.medium}, {p.carrier}, {p.dryer}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
