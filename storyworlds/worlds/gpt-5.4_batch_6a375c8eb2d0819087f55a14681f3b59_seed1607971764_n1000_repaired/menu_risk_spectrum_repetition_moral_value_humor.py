#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/menu_risk_spectrum_repetition_moral_value_humor.py
==============================================================================

A standalone story world for a bedtime "menu" tale with a gentle risk lesson.

The children build a tiny pretend café before bed and make a funny menu. To
finish it, one child wants a special topping from a high shelf and picks an
unstable thing to stand on. The other child remembers a family "risk spectrum"
chart: green for safe, yellow for maybe, red for too risky. That prediction can
either stop the climb, or fail to stop it, which leads to a wobble, a grown-up
rescue, and a calmer safer ending.

The world uses:
- menu
- risk
- spectrum
- Repetition
- Moral Value
- Humor
- Bedtime-story tone

Run it
------
    python storyworlds/worlds/gpt-5.4/menu_risk_spectrum_repetition_moral_value_humor.py
    python storyworlds/worlds/gpt-5.4/menu_risk_spectrum_repetition_moral_value_humor.py --all
    python storyworlds/worlds/gpt-5.4/menu_risk_spectrum_repetition_moral_value_humor.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/menu_risk_spectrum_repetition_moral_value_humor.py --qa
    python storyworlds/worlds/gpt-5.4/menu_risk_spectrum_repetition_moral_value_humor.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "sensible", "patient", "thoughtful"}


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
    stable: bool = False
    fragile: bool = False
    # physical
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    # emotional / social
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
class Theme:
    id: str
    room_scene: str
    setup_props: str
    menu_name: str
    hero_title: str
    helper_title: str
    closing_line: str
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
class Treat:
    id: str
    label: str
    jar_phrase: str
    menu_item: str
    spill_text: str
    smell_text: str
    fragile: bool = True
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
class Shelf:
    id: str
    label: str
    reach_text: str
    height: int
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
class Support:
    id: str
    label: str
    phrase: str
    wobble: int
    stable: bool = False
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    support = world.get("support")
    child = world.get("instigator")
    jar = world.get("jar")
    if child.meters["climbing"] < THRESHOLD:
        return out
    if support.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble", support.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    world.get("room").meters["danger"] += 1
    jar.meters["teeter"] += 1
    out.append("__wobble__")
    return out


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    jar = world.get("jar")
    if jar.meters["teeter"] < THRESHOLD:
        return out
    if jar.meters["caught"] >= THRESHOLD:
        return out
    if jar.meters["broken"] >= THRESHOLD:
        return out
    if world.facts.get("allow_break_rule") is not True:
        return out
    sig = ("break", jar.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jar.meters["broken"] += 1
    jar.meters["spilled"] += 1
    world.get("room").meters["mess"] += 1
    for kid in world.kids():
        kid.memes["sadness"] += 1
    out.append("__break__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="break", tag="physical", apply=_r_break),
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


THEMES = {
    "moon_cafe": Theme(
        id="moon_cafe",
        room_scene="a sleepy moon café",
        setup_props="A blanket over two chairs became the café roof, a small lamp became the moon, and a cardboard card became the menu.",
        menu_name="Moonbeam Menu",
        hero_title="Chef",
        helper_title="Assistant",
        closing_line="their tiny café glowed on, soft and safe",
        tags={"menu", "bedtime"},
    ),
    "teddy_bistro": Theme(
        id="teddy_bistro",
        room_scene="a teddy-bear bistro",
        setup_props="A line of stuffed animals sat on pillows for customers, a silver spoon became the bell, and a cardboard card became the menu.",
        menu_name="Teddy Menu",
        hero_title="Cook",
        helper_title="Server",
        closing_line="the bears waited politely for supper in their pajamas",
        tags={"menu", "bedtime"},
    ),
    "star_diner": Theme(
        id="star_diner",
        room_scene="a starry little diner",
        setup_props="The rug became the dining floor, two cushions became booths, and a crayon card became the menu.",
        menu_name="Star Menu",
        hero_title="Captain Cook",
        helper_title="Menu Keeper",
        closing_line="the room felt cozy enough to tuck into a pocket of night",
        tags={"menu", "bedtime"},
    ),
}

TREATS = {
    "cinnamon_stars": Treat(
        id="cinnamon_stars",
        label="cinnamon stars",
        jar_phrase="a glass jar of cinnamon stars",
        menu_item="toast moons with cinnamon stars",
        spill_text="brown stars and sweet dust scattered over the floor",
        smell_text="the room smelled warm and sweet, like toast wearing a tiny coat",
        fragile=True,
        tags={"cinnamon", "glass"},
    ),
    "berry_sprinkles": Treat(
        id="berry_sprinkles",
        label="berry sprinkles",
        jar_phrase="a glass jar of berry sprinkles",
        menu_item="yogurt clouds with berry sprinkles",
        spill_text="pink sprinkles bounced under the chair like surprised ants",
        smell_text="the room smelled fruity and silly at the same time",
        fragile=True,
        tags={"berries", "glass"},
    ),
    "cocoa_comets": Treat(
        id="cocoa_comets",
        label="cocoa comets",
        jar_phrase="a glass jar of cocoa comets",
        menu_item="banana moons with cocoa comets",
        spill_text="tiny chocolate comets rolled away in every direction",
        smell_text="the room smelled like cookies trying not to giggle",
        fragile=True,
        tags={"cocoa", "glass"},
    ),
}

SHELVES = {
    "pantry_top": Shelf(
        id="pantry_top",
        label="the top pantry shelf",
        reach_text="high above the mugs",
        height=3,
        tags={"high_shelf"},
    ),
    "bookcase_top": Shelf(
        id="bookcase_top",
        label="the top of the bookcase",
        reach_text="above the storybooks and the sleepy clock",
        height=2,
        tags={"high_shelf"},
    ),
    "fridge_top": Shelf(
        id="fridge_top",
        label="the top of the little snack fridge",
        reach_text="above the magnets and drawings",
        height=3,
        tags={"high_shelf"},
    ),
    "counter_edge": Shelf(
        id="counter_edge",
        label="the low counter edge",
        reach_text="right beside the fruit bowl",
        height=1,
        tags={"low_shelf"},
    ),
}

SUPPORTS = {
    "rolling_chair": Support(
        id="rolling_chair",
        label="rolling chair",
        phrase="the rolling chair with squeaky wheels",
        wobble=3,
        stable=False,
        tags={"wheels", "red_zone"},
    ),
    "toy_drum": Support(
        id="toy_drum",
        label="toy drum",
        phrase="the round toy drum",
        wobble=2,
        stable=False,
        tags={"round", "red_zone"},
    ),
    "laundry_basket": Support(
        id="laundry_basket",
        label="laundry basket",
        phrase="the upside-down laundry basket",
        wobble=2,
        stable=False,
        tags={"basket", "red_zone"},
    ),
    "step_stool": Support(
        id="step_stool",
        label="step stool",
        phrase="the strong little step stool",
        wobble=0,
        stable=True,
        tags={"safe_support", "green_zone"},
    ),
}

RESPONSES = {
    "parent_lift": Response(
        id="parent_lift",
        sense=3,
        power=5,
        text="lifted {child} down with one arm and took the jar down safely with the other hand",
        fail="reached for {child}, but the jar had already slipped from the shelf",
        qa_text="lifted the child down and took the jar safely",
        tags={"ask_adult", "safe_reach"},
    ),
    "bring_stool": Response(
        id="bring_stool",
        sense=3,
        power=4,
        text="moved {child} away from the wobble, brought the real step stool, and reached the jar the calm way",
        fail="brought the step stool, but the jar had already tipped before anyone could steady it",
        qa_text="moved the child away, brought the step stool, and got the jar safely",
        tags={"step_stool", "safe_reach"},
    ),
    "reacher": Response(
        id="reacher",
        sense=2,
        power=3,
        text="set the wobbling thing aside and used the grabber tool to pull the jar down gently",
        fail="tried the grabber tool, but the jar was already tipping too fast",
        qa_text="used a grabber tool to pull the jar down gently",
        tags={"grabber", "safe_reach"},
    ),
    "broom_hook": Response(
        id="broom_hook",
        sense=1,
        power=1,
        text="hooked the jar with a broom handle and tugged it closer",
        fail="hooked for the jar with a broom handle, which only made it jump and slip",
        qa_text="tried to hook the jar with a broom handle",
        tags={"broom", "unsafe_fix"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["careful", "sensible", "curious", "sleepy", "thoughtful", "cheerful"]
COMFORTS = ["stuffed rabbit", "plush whale", "toy fox", "soft bear"]
PETS = ["the cat", "the puppy", "the hamster", "the old dog"]


def risk_exists(support: Support, shelf: Shelf, treat: Treat) -> bool:
    return (not support.stable) and support.wobble >= 2 and shelf.height >= 2 and treat.fragile


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(support: Support, shelf: Shelf, delay: int) -> int:
    return support.wobble + shelf.height + delay


def is_contained(response: Response, support: Support, shelf: Shelf, delay: int) -> bool:
    return response.power >= severity_of(support, shelf, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (3.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    sim.facts["allow_break_rule"] = False
    inst = sim.get("instigator")
    support = sim.get("support")
    support.meters["wobble"] = float(sim.facts["support_cfg"].wobble)
    inst.meters["climbing"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("room").meters["danger"],
        "teeter": sim.get("jar").meters["teeter"],
    }


@dataclass
class StoryParams:
    theme: str
    treat: str
    shelf: str
    support: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 5
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    comfort: str = ""
    pet: str = ""
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


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"One drowsy evening, {a.id} and {b.id} turned the living room into {theme.room_scene}. "
        f"{theme.setup_props}"
    )
    world.say(
        f'"{theme.hero_title} {a.id} and {theme.helper_title} {b.id}!" {a.id} whispered. '
        f'"Tonight\'s menu must be the finest in the house."'
    )


def make_menu(world: World, a: Entity, b: Entity, theme: Theme, treat: Treat) -> None:
    world.say(
        f"They thought up very serious dishes with very silly names. On the {theme.menu_name} "
        f"they wrote: sleepy toast, moon milk, and {treat.menu_item}."
    )
    pet = world.facts.get("pet")
    if pet:
        world.say(f"{pet.capitalize()} sat nearby as if ready to order everything at once.")


def need_treat(world: World, b: Entity, shelf: Shelf, treat: Treat) -> None:
    world.say(
        f"But the last ingredient, {treat.jar_phrase}, sat on {shelf.label}, {shelf.reach_text}. "
        f"{b.id} looked up and gave a tiny puff of breath."
    )
    world.say(f'"We can finish the menu only if we reach it," {b.id} said.')


def tempt(world: World, a: Entity, support: Support) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} pointed at {support.phrase}. "I know. I can stand on the {support.label}."'
    )
    world.say(
        '"Up, reach, grab. Up, reach, grab," '
        f"{a.id} chanted, as if saying it three times could make it wise."
    )


def warn(world: World, b: Entity, a: Entity, support: Support, shelf: Shelf, parent: Entity) -> None:
    pred = predict_wobble(world)
    world.facts["predicted_danger"] = pred["danger"]
    b.memes["caution"] += 1
    extra = ""
    if b.memes["caution"] >= 6:
        extra = " The red end of the spectrum felt very red indeed."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "That goes on the red side of the risk spectrum," '
        f'{b.pronoun()} said. "A {support.label} can wobble, and the jar can teeter. '
        f'Let\'s ask {parent.label_word} instead."{extra}'
    )
    world.say('"Too tippy for the menu, too tippy for bedtime, too tippy for noses," '
              f'{b.id} added.')


def defy(world: World, a: Entity, b: Entity, support: Support) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"It will be quick," {a.id} said. Because {a.id} was the older one, '
            f'{b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"It will be quick," {a.id} said, and stepped toward the {support.label} anyway.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity, theme: Theme) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["lesson"] += 1
    world.say(
        f"{a.id} looked up, then down, then up again. The climb suddenly seemed smaller than the risk."
    )
    world.say(
        f'"You\'re right," {a.id} said. "A funny menu is not worth a bumpy tumble." '
        f'Together they padded to find {parent.label_word}.'
    )
    world.para()
    world.say(
        f"{parent.label_word.capitalize()} listened, smiled at the careful choice, and lifted the jar down with no wobble at all."
    )
    world.say(
        f"They added the last line to the menu and giggled at how grand it sounded. Soon {theme.closing_line}, "
        "and the safest dish of all was the one made with help."
    )


def climb(world: World, a: Entity, support_ent: Entity, support: Support) -> None:
    a.meters["climbing"] += 1
    support_ent.meters["wobble"] = float(support.wobble)
    propagate(world, narrate=False)
    world.say(
        f"{a.id} climbed onto the {support.label}. At once it gave a wiggle, then a wobble, then another wiggle."
    )


def teeter(world: World, treat: Treat) -> None:
    world.say(
        f"The jar tipped with a tiny glassy click. For one second it seemed to think about flying."
    )
    world.say(
        f"{treat.jar_phrase[0].upper()}{treat.jar_phrase[1:]} leaned toward the edge, and everybody in the room forgot to blink."
    )


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.capitalize()}!" {b.id} squeaked. "The jar!"')


def rescue(world: World, parent: Entity, response: Response, child: Entity, jar: Entity) -> None:
    jar.meters["caught"] += 1
    jar.meters["teeter"] = 0.0
    child.meters["climbing"] = 0.0
    world.get("room").meters["danger"] = 0.0
    body = response.text.replace("{child}", child.id)
    world.say(f"{parent.label_word.capitalize()} came in softly but quickly and {body}.")
    world.say("Nothing broke. The only thing that spilled was everyone's breath.")


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "A menu can wait," {parent.pronoun()} said. '
        '"When something sits high and the risk is wobbly, we choose the green part of the spectrum and ask for help."'
    )
    world.say(
        f'{a.id} nodded. "{a.pronoun("possessive").capitalize()} feet wanted to be fast," {a.pronoun()} admitted. '
        f'"But my head needed to be slower."'
    )


def safe_finish(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, treat: Treat) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    comfort = b.attrs.get("comfort")
    world.say(
        f"Then {parent.label_word} set the jar on the table where little hands could reach it safely."
    )
    world.say(
        f"They sprinkled the {treat.label} onto their bedtime snack and added one more line to the menu: "
        '"Ask-first cocoa, served with calm knees."'
    )
    if comfort:
        world.say(f"{b.id} made the {comfort} the head customer, and it ordered two helpings.")
    world.say(
        f"Soon {theme.closing_line}, and the children remembered the rule they liked to repeat: "
        '"No wobble, no topple, no trouble."'
    )


def rescue_fail(world: World, parent: Entity, response: Response, child: Entity, jar: Entity, treat: Treat) -> None:
    world.facts["allow_break_rule"] = True
    body = response.fail.replace("{child}", child.id)
    world.say(f"{parent.label_word.capitalize()} hurried in and {body}.")
    propagate(world, narrate=False)
    jar.meters["broken"] = 1.0
    jar.meters["spilled"] = 1.0
    world.get("room").meters["mess"] = 1.0
    world.say(
        f"The jar slipped, bumped, and broke. {treat.spill_text}."
    )
    world.say(treat.smell_text)


def tidy_and_lesson(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["sadness"] += 1
        kid.memes["love"] += 1
    comfort = b.attrs.get("comfort")
    world.say(
        f'{parent.label_word.capitalize()} checked that both children were safe first, and only then fetched the broom.'
    )
    world.say(
        f'"Hands stay back from broken glass," {parent.pronoun()} said. "The menu is not ruined. We will just make a simpler one tonight."'
    )
    if comfort:
        world.say(f"{b.id} hugged the {comfort} while the sweeping was done.")
    world.say(
        f"Later they rewrote the menu with plain toast and warm milk, and even that felt cozy. "
        f"The little café closed early, but {theme.closing_line} all the same."
    )


def tell(
    theme: Theme,
    treat: Treat,
    shelf: Shelf,
    support: Support,
    response: Response,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 5,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
    comfort: str = "",
    pet: str = "",
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
    ))
    a.id = instigator
    world.entities[instigator] = world.entities.pop("instigator")
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation, "comfort": comfort},
    ))
    b.id = cautioner
    world.entities[cautioner] = world.entities.pop("cautioner")
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    room = world.add(Entity(id="room", type="room", label="the room"))
    support_ent = world.add(Entity(
        id="support",
        type="support",
        label=support.label,
        stable=support.stable,
    ))
    jar = world.add(Entity(
        id="jar",
        type="jar",
        label=treat.label,
        fragile=treat.fragile,
    ))
    shelf_ent = world.add(Entity(id="shelf", type="shelf", label=shelf.label))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    room.meters["danger"] = 0.0
    room.meters["mess"] = 0.0
    support_ent.meters["wobble"] = 0.0
    jar.meters["teeter"] = 0.0
    jar.meters["caught"] = 0.0
    jar.meters["broken"] = 0.0
    jar.meters["spilled"] = 0.0
    world.facts.update(
        theme=theme,
        treat_cfg=treat,
        shelf_cfg=shelf,
        support_cfg=support,
        response=response,
        instigator=a,
        cautioner=b,
        parent=parent,
        pet=pet,
        allow_break_rule=False,
    )

    play_setup(world, a, b, theme)
    make_menu(world, a, b, theme, treat)
    need_treat(world, b, shelf, treat)

    world.para()
    tempt(world, a, support)
    warn(world, b, a, support, shelf, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, parent, theme)
        outcome = "averted"
        contained = True
        severity = 0
    else:
        defy(world, a, b, support)
        world.para()
        climb(world, a, support_ent, support)
        teeter(world, treat)
        alarm(world, b, parent)
        severity = severity_of(support, shelf, delay)
        contained = is_contained(response, support, shelf, delay)
        world.para()
        if contained:
            rescue(world, parent, response, a, jar)
            lesson(world, parent, a, b)
            world.para()
            safe_finish(world, parent, a, b, theme, treat)
            outcome = "contained"
        else:
            rescue_fail(world, parent, response, a, jar, treat)
            tidy_and_lesson(world, parent, a, b, theme)
            outcome = "spilled"

    world.facts.update(
        shelf=shelf_ent,
        support=support_ent,
        jar=jar,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        promised=a.memes["lesson"] >= THRESHOLD or b.memes["lesson"] >= THRESHOLD,
    )
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for treat_id, treat in TREATS.items():
            for shelf_id, shelf in SHELVES.items():
                for support_id, support in SUPPORTS.items():
                    if risk_exists(support, shelf, treat):
                        combos.append((theme_id, treat_id, shelf_id, support_id))
    return combos


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
    th = f["theme"]
    treat = f["treat_cfg"]
    support = f["support_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "menu", '
        f'"risk", and "spectrum". Two children run a pretend café and one child wants '
        f"to stand on a {support.label} to reach {treat.jar_phrase}."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle story where {b.id} uses a risk spectrum idea to stop {a.id} before the climb happens, "
            "with repetition and a cozy ending.",
            f"Write a funny bedtime tale where the children make a silly menu, choose safety over hurry, and learn that asking for help is wise.",
        ]
    if outcome == "spilled":
        return [
            base,
            f"Tell a cautionary bedtime story where {a.id} ignores the warning, the jar breaks, and the family cleans up safely.",
            "Write a soft but clear moral tale with humor, repetition, and a simple lesson that a silly menu is never worth a risky wobble.",
        ]
    return [
        base,
        f"Tell a bedtime story where {a.id} ignores the warning, but a calm grown-up helps before anything breaks and explains the risk spectrum.",
        "Write a cozy story with humor and repetition that ends with a safer menu and a child-friendly lesson about asking for help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    treat = f["treat_cfg"]
    shelf = f["shelf_cfg"]
    support = f["support_cfg"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who made a pretend bedtime café together. "
            f"Their {pw} comes to help when the reaching idea becomes risky."
        ),
        (
            "What was on their menu?",
            f"They made a funny menu with sleepy food names and wanted to add {treat.menu_item}. "
            f"The menu mattered because they were trying to finish their tiny café before bed."
        ),
        (
            f"Why did {a.id} want to stand on the {support.label}?",
            f"{a.id} wanted to reach {treat.jar_phrase} on {shelf.label}. "
            f"The jar was the last thing needed to finish the menu, so the fast idea felt tempting."
        ),
        (
            f"What did {b.id} mean by the risk spectrum?",
            f"{b.id} meant that some choices are safer and some are more dangerous, like green, yellow, and red. "
            f"{support.label.capitalize()} belonged on the red end because it could wobble under a child."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What changed {a.id}'s mind?",
            f"{a.id} listened when {b.id} named the risk clearly and asked for help instead. "
            f"Because the danger was understood before the climb, the story turned safe without any wobble at all."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the jar brought down safely and the menu finished in a cozy way. "
            f"The ending shows that patience and help were more important than being quick."
        ))
    elif f["outcome"] == "contained":
        body = response.qa_text
        qa.append((
            f"How did {a.id}'s {pw} solve the problem?",
            f"{pw.capitalize()} {body}. "
            f"That worked because the grown-up replaced the wobbly plan with a steady one before the jar could fall."
        ))
        qa.append((
            "What lesson did the children learn?",
            f"They learned that a menu can wait, but safety cannot. "
            f"When something feels high and wobbly on the risk spectrum, asking for help is the smart and kind choice."
        ))
        qa.append((
            "Why is the ending funny as well as careful?",
            f"The menu ends with a silly item like 'Ask-first cocoa, served with calm knees.' "
            f"The joke makes the lesson feel warm instead of scary."
        ))
    else:
        qa.append((
            "What happened when the rescue came too late?",
            f"The jar broke and the treat spilled across the floor, though the children themselves stayed safe. "
            f"That happened because the risky climb had already gone too far before the grown-up could steady it."
        ))
        qa.append((
            "What was the moral value in the ending?",
            f"The story says that broken snacks matter less than safe people. "
            f"It also shows that mistakes can still turn into learning when everyone slows down, listens, and cleans up carefully."
        ))
    return qa


KNOWLEDGE = {
    "menu": [
        ("What is a menu?",
         "A menu is a list of foods or drinks that a cook or restaurant offers. In pretend play, children can make a funny menu with crayons and imagination.")
    ],
    "risk": [
        ("What does risk mean?",
         "Risk means there is a chance something unsafe or harmful could happen. A wise choice tries to make the risk smaller.")
    ],
    "spectrum": [
        ("What is a spectrum?",
         "A spectrum is a range that goes from one side to another. A risk spectrum can help people think about what feels safer and what feels more dangerous.")
    ],
    "glass": [
        ("Why should children be careful with glass jars?",
         "Glass can break into sharp pieces if it falls. That is why a grown-up should help with high or breakable things.")
    ],
    "step_stool": [
        ("What is a step stool for?",
         "A step stool is a small strong stool that helps someone reach a little higher. It is used carefully on flat ground, usually with a grown-up nearby.")
    ],
    "ask_adult": [
        ("When should you ask a grown-up for help?",
         "Ask a grown-up when something is high, heavy, hot, sharp, or wobbly. Asking for help is not babyish; it is smart.")
    ],
    "safe_reach": [
        ("Why is it safer to use a steady way to reach something high?",
         "A steady way lowers the chance of slipping, wobbling, or dropping things. Safe reaching protects both people and breakable objects.")
    ],
}
KNOWLEDGE_ORDER = ["menu", "risk", "spectrum", "glass", "step_stool", "ask_adult", "safe_reach"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"menu", "risk", "spectrum"} | set(f["treat_cfg"].tags) | set(f["response"].tags)
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
        if e.stable:
            bits.append("stable=True")
        if e.fragile:
            bits.append("fragile=True")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="moon_cafe",
        treat="cinnamon_stars",
        shelf="pantry_top",
        support="rolling_chair",
        response="parent_lift",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
        comfort="stuffed rabbit",
        pet="the cat",
    ),
    StoryParams(
        theme="teddy_bistro",
        treat="berry_sprinkles",
        shelf="bookcase_top",
        support="toy_drum",
        response="bring_stool",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="sensible",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
        comfort="plush whale",
        pet="the puppy",
    ),
    StoryParams(
        theme="star_diner",
        treat="cocoa_comets",
        shelf="fridge_top",
        support="laundry_basket",
        response="reacher",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="thoughtful",
        delay=1,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=3,
        comfort="toy fox",
        pet="the hamster",
    ),
    StoryParams(
        theme="moon_cafe",
        treat="berry_sprinkles",
        shelf="pantry_top",
        support="rolling_chair",
        response="bring_stool",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="father",
        trait="cheerful",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=2,
        comfort="soft bear",
        pet="the old dog",
    ),
]


def explain_rejection(support: Support, shelf: Shelf, treat: Treat) -> str:
    if support.stable:
        return (
            f"(No story: a {support.label} is already a steady way to reach. "
            "This world is about a wobbly choice on the risk spectrum, so pick an unstable support instead.)"
        )
    if shelf.height < 2:
        return (
            f"(No story: {shelf.label} is low enough that the danger is too weak for this bedtime tale. "
            "Pick a higher shelf so the warning is honest.)"
        )
    if not treat.fragile:
        return (
            f"(No story: {treat.label} is not breakable here, so the turn loses its needed risk. "
            "Pick a glass-jar treat instead.)"
        )
    return "(No story: this combination does not create the needed wobble-and-jar risk.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a safer response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], SUPPORTS[params.support], SHELVES[params.shelf], params.delay) else "spilled"


ASP_RULES = r"""
hazard(Su, Sh, Tr) :- support(Su), shelf(Sh), treat(Tr),
                      unstable(Su), wobble(Su, W), W >= 2,
                      height(Sh, H), H >= 2,
                      fragile(Tr).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, Tr, Sh, Su) :- theme(T), hazard(Su, Sh, Tr).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(W + H + D) :- chosen_support(Su), wobble(Su, W),
                       chosen_shelf(Sh), height(Sh, H),
                       delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(spilled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for tr_id, tr in TREATS.items():
        lines.append(asp.fact("treat", tr_id))
        if tr.fragile:
            lines.append(asp.fact("fragile", tr_id))
    for sh_id, sh in SHELVES.items():
        lines.append(asp.fact("shelf", sh_id))
        lines.append(asp.fact("height", sh_id, sh.height))
    for su_id, su in SUPPORTS.items():
        lines.append(asp.fact("support", su_id))
        lines.append(asp.fact("wobble", su_id, su.wobble))
        if not su.stable:
            lines.append(asp.fact("unstable", su_id))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_support", params.support),
        asp.fact("chosen_shelf", params.shelf),
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime menu storyworld: a silly menu, a risky reach, and a safer choice."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--shelf", choices=SHELVES)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how late the grown-up help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.support and args.shelf and args.treat:
        su = SUPPORTS[args.support]
        sh = SHELVES[args.shelf]
        tr = TREATS[args.treat]
        if not risk_exists(su, sh, tr):
            raise StoryError(explain_rejection(su, sh, tr))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.treat is None or c[1] == args.treat)
        and (args.shelf is None or c[2] == args.shelf)
        and (args.support is None or c[3] == args.support)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, treat, shelf, support = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    comfort = rng.choice(COMFORTS + ["", ""])
    pet = rng.choice(PETS + ["", ""])
    return StoryParams(
        theme=theme,
        treat=treat,
        shelf=shelf,
        support=support,
        response=response,
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
        trust=trust,
        comfort=comfort,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.shelf not in SHELVES:
        raise StoryError(f"(Unknown shelf: {params.shelf})")
    if params.support not in SUPPORTS:
        raise StoryError(f"(Unknown support: {params.support})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not risk_exists(SUPPORTS[params.support], SHELVES[params.shelf], TREATS[params.treat]):
        raise StoryError(explain_rejection(SUPPORTS[params.support], SHELVES[params.shelf], TREATS[params.treat]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        theme=THEMES[params.theme],
        treat=TREATS[params.treat],
        shelf=SHELVES[params.shelf],
        support=SUPPORTS[params.support],
        response=RESPONSES[params.response],
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
        trust=params.trust,
        comfort=params.comfort,
        pet=params.pet,
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
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(200):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, treat, shelf, support) combos:\n")
        for theme, treat, shelf, support in combos:
            print(f"  {theme:12} {treat:16} {shelf:12} {support}")
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
                f"### {p.instigator} & {p.cautioner}: {p.support} -> {p.shelf} "
                f"({p.theme}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
