#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rent_puny_babe_reconciliation_misunderstanding_comedy.py
===================================================================================

A standalone storyworld about a funny misunderstanding during a baby-parade plan:
one child says a parade ride looks puny and suggests they should rent a bigger one,
but another child only hears the words "puny" and "babe" together and thinks the
baby was insulted. The story resolves through explanation, apology, and shared play.

Run it
------
    python storyworlds/worlds/gpt-5.4/rent_puny_babe_reconciliation_misunderstanding_comedy.py
    python storyworlds/worlds/gpt-5.4/rent_puny_babe_reconciliation_misunderstanding_comedy.py --vehicle wagon
    python storyworlds/worlds/gpt-5.4/rent_puny_babe_reconciliation_misunderstanding_comedy.py --place hallway
    python storyworlds/worlds/gpt-5.4/rent_puny_babe_reconciliation_misunderstanding_comedy.py --verify
    python storyworlds/worlds/gpt-5.4/rent_puny_babe_reconciliation_misunderstanding_comedy.py --qa --json
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
SOFT_TRAITS = {"forgiving", "giggly", "tender"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        baby = {"baby"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in baby:
            return {"subject": "the baby", "object": "the baby", "possessive": "the baby's"}[case]
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


@dataclass
class Setting:
    id: str
    place: str
    parade_name: str
    rent_booth: bool
    bustle: str
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
    size: int
    wobble: str
    comfy: str
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
class Theme:
    id: str
    costume: str
    trim: str
    finale: str
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
    sense: int
    warmth: int
    text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {
            "misheard": False,
            "full_reconcile": False,
            "phrase": "",
            "explanation_line": "",
        }

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
        new = World(self.setting)
        new.entities = copy.deepcopy(self.entities)
        new.paragraphs = [[]]
        new.fired = set(self.fired)
        new.facts = copy.deepcopy(self.facts)
        return new


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


def _r_misunderstanding(world: World) -> list[str]:
    planner = world.get("planner")
    listener = world.get("listener")
    baby = world.get("baby")
    if listener.memes["heard_fragment"] < THRESHOLD:
        return []
    sig = ("misunderstood",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if world.facts.get("heard_words") == ("puny", "babe"):
        world.facts["misheard"] = True
        listener.memes["hurt"] += 1
        listener.memes["protective"] += 1
        planner.memes["confusion"] += 1
        baby.memes["fuss"] += 1
        world.get("crowd").meters["tension"] += 1
        return ["__misheard__"]
    return []


def _r_reconcile(world: World) -> list[str]:
    planner = world.get("planner")
    listener = world.get("listener")
    if planner.memes["explained"] < THRESHOLD or planner.memes["apologized"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    listener.memes["hurt"] = 0.0
    listener.memes["relief"] += 1
    planner.memes["relief"] += 1
    planner.memes["trust"] += 1
    listener.memes["trust"] += 1
    world.get("crowd").meters["tension"] = 0.0
    return ["__reconciled__"]


CAUSAL_RULES = [
    Rule(name="misunderstanding", tag="social", apply=_r_misunderstanding),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(x for x in produced if not x.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


PLACES = {
    "block_party": Setting(
        id="block_party",
        place="the block party",
        parade_name="the Laughing Wheels Parade",
        rent_booth=True,
        bustle="Neighbors were hanging streamers from folding chairs and laughing over paper cups of lemonade.",
        tags={"parade", "party"},
    ),
    "park_fair": Setting(
        id="park_fair",
        place="the park fair",
        parade_name="the Tiny Parade",
        rent_booth=True,
        bustle="A rental tent flapped by the path while kites bobbed above the grass.",
        tags={"parade", "fair"},
    ),
    "school_fun_day": Setting(
        id="school_fun_day",
        place="school fun day",
        parade_name="the Giggle Roll",
        rent_booth=True,
        bustle="Teachers taped bright arrows to the pavement and somebody kept testing a squeaky whistle.",
        tags={"parade", "school"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the apartment hallway",
        parade_name="the Very Small Hallway March",
        rent_booth=False,
        bustle="Only three doormats and a sleepy plant watched from the wall.",
        tags={"hallway"},
    ),
}

VEHICLES = {
    "stroller": Vehicle(
        id="stroller",
        label="stroller",
        phrase="a tiny stroller with one squeaky wheel",
        size=1,
        wobble="The ribbons on the handle drooped every time it bumped a crack.",
        comfy="It was safe, but it looked very small under all the decorations.",
        tags={"stroller", "small"},
    ),
    "doll_cart": Vehicle(
        id="doll_cart",
        label="doll cart",
        phrase="a doll cart borrowed from the playroom",
        size=1,
        wobble="Its little plastic wheels rattled like marbles in a tin cup.",
        comfy="It was meant for dolls, not for a big parade dream.",
        tags={"cart", "small"},
    ),
    "laundry_basket": Vehicle(
        id="laundry_basket",
        label="laundry basket on wheels",
        phrase="a laundry basket tied onto a rolling board",
        size=1,
        wobble="The whole thing shivered if anyone sneezed near it.",
        comfy="It held the pillows, but not much dignity.",
        tags={"basket", "small"},
    ),
    "wagon": Vehicle(
        id="wagon",
        label="wagon",
        phrase="a roomy red wagon",
        size=3,
        wobble="Its big wheels rolled as smooth as soup.",
        comfy="It already looked grand enough for any parade.",
        tags={"wagon", "large"},
    ),
}

THEMES = {
    "duck": Theme(
        id="duck",
        costume="duck parade",
        trim="yellow feathers and paper lily pads",
        finale="The baby quacked so loudly that even the judge laughed.",
        tags={"duck"},
    ),
    "moon": Theme(
        id="moon",
        costume="moon parade",
        trim="silver stars and a round cardboard moon",
        finale="The moon bonnet slipped over one eye and made the baby look like a sleepy astronaut.",
        tags={"moon"},
    ),
    "lion": Theme(
        id="lion",
        costume="lion parade",
        trim="a soft felt mane and curly orange ribbons",
        finale="The baby sneezed into the mane and looked more surprised than fierce.",
        tags={"lion"},
    ),
}

REPAIRS = {
    "explain": Repair(
        id="explain",
        sense=3,
        warmth=2,
        text='blurted out an apology and pointed at the little ride. "I said the stroller was puny, not the babe. I was trying to help the parade."',
        qa_text="apologized and explained that the small ride was the puny thing",
        tags={"apology", "explain"},
    ),
    "test_ride": Repair(
        id="test_ride",
        sense=3,
        warmth=3,
        text='apologized, pointed at the tiny ride, and then climbed in it for a silly test ride. The wheels squeaked so hard that everybody could see what had been meant.',
        qa_text="apologized and used a silly test ride to show the tiny ride was the problem",
        tags={"apology", "explain", "laugh"},
    ),
    "ribbon_peace": Repair(
        id="ribbon_peace",
        sense=2,
        warmth=2,
        text='said sorry, tied a shiny ribbon onto the handle, and explained that the words were about the ride, not the babe. The small peace-offering made the explanation easier to hear.',
        qa_text="said sorry, gave a ribbon peace-offering, and explained the words were about the ride",
        tags={"apology", "ribbon"},
    ),
    "mumble": Repair(
        id="mumble",
        sense=1,
        warmth=0,
        text='muttered a tiny sorry into the feathers and hoped the problem would walk away on its own',
        qa_text="mumbled instead of really explaining",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Lucy", "Ella", "Maya"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Finn", "Leo", "Jack", "Eli"]
BABY_NAMES = ["Pip", "Bibi", "June", "Toby", "Mimi", "Otis"]
TRAITS = ["forgiving", "dramatic", "giggly", "tender", "proud"]


def valid_combo(place: Setting, vehicle: Vehicle) -> bool:
    return place.rent_booth and vehicle.size <= 1


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for vehicle_id, vehicle in VEHICLES.items():
            if not valid_combo(place, vehicle):
                continue
            for theme_id in THEMES:
                out.append((place_id, vehicle_id, theme_id))
    return out


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def soft_bonus(trait: str) -> int:
    return 1 if trait in SOFT_TRAITS else 0


def full_reconciliation(repair: Repair, trait: str, delay: int) -> bool:
    return repair.warmth + soft_bonus(trait) >= delay + 2


def predict_misunderstanding(world: World) -> dict:
    sim = world.copy()
    sim.get("listener").memes["heard_fragment"] += 1
    sim.facts["heard_words"] = ("puny", "babe")
    propagate(sim, narrate=False)
    return {
        "misheard": sim.facts["misheard"],
        "hurt": sim.get("listener").memes["hurt"],
    }


def introduce(world: World, planner: Entity, listener: Entity, baby: Entity, parent: Entity, theme: Theme) -> None:
    world.say(
        f"On the morning of {world.setting.parade_name}, {planner.id} and {listener.id} were busy decorating for a {theme.costume}."
    )
    world.say(world.setting.bustle)
    world.say(
        f"Their {parent.label_word} had set {baby.id} in the ride with pillows, and the trim of {theme.trim} kept sliding into the baby's lap."
    )


def admire_and_wobble(world: World, planner: Entity, vehicle: Vehicle, baby: Entity) -> None:
    planner.memes["pride"] += 1
    world.say(
        f"They had chosen {vehicle.phrase} for {baby.id}. {vehicle.wobble} {vehicle.comfy}"
    )


def bold_plan(world: World, planner: Entity, vehicle: Vehicle) -> None:
    world.say(
        f'{planner.id} stepped back, squinted, and whispered, "This {vehicle.label} looks puny. Maybe we should rent a wagon."'
    )
    world.facts["phrase"] = f"This {vehicle.label} looks puny. Maybe we should rent a wagon."


def partial_hearing(world: World, listener: Entity, theme: Theme) -> None:
    pred = predict_misunderstanding(world)
    world.facts["predicted_hurt"] = pred["hurt"]
    listener.memes["heard_fragment"] += 1
    world.facts["heard_words"] = ("puny", "babe")
    propagate(world, narrate=False)
    world.say(
        f"But {listener.id} was bent behind a pile of {theme.trim}, and all {listener.pronoun()} really caught were the words 'puny' and 'babe' floating through the feathers."
    )


def accuse(world: World, listener: Entity, planner: Entity, baby: Entity) -> None:
    if world.facts["misheard"]:
        world.say(
            f'{listener.id} popped up so fast that a ribbon stuck to {listener.pronoun("possessive")} hair. "{planner.id}! Did you call {baby.id} a puny babe?"'
        )
        world.say(
            f"{baby.id} blinked at both of them and then grabbed a feather with great seriousness."
        )


def confusion(world: World, planner: Entity) -> None:
    planner.memes["embarrassment"] += 1
    world.say(
        f'{planner.id} turned pink clear up to {planner.pronoun("possessive")} ears. "What? No!"'
    )


def repair_scene(world: World, planner: Entity, listener: Entity, vehicle: Vehicle, repair: Repair) -> None:
    planner.memes["apologized"] += 1
    planner.memes["explained"] += 1
    world.facts["explanation_line"] = f"{planner.id} meant the {vehicle.label}, not the baby."
    propagate(world, narrate=False)
    world.say(f"{planner.id} {repair.text}")
    if repair.id == "test_ride":
        world.say(
            f"When {planner.pronoun()} sat in the little {vehicle.label}, {planner.pronoun('possessive')} knees stuck up like folding umbrellas."
        )
    elif repair.id == "ribbon_peace":
        world.say(
            f"The ribbon bobbed on the handle like it was nodding yes, yes, that was the problem all along."
        )


def parent_clarifies(world: World, parent: Entity, listener: Entity, vehicle: Vehicle, baby: Entity) -> None:
    world.say(
        f'{parent.label_word.capitalize()} could not help laughing. "{listener.id}, the puny part was {vehicle.label}, not {baby.id}. This babe is the star of the whole parade."'
    )


def settle(world: World, planner: Entity, listener: Entity, baby: Entity, repair: Repair, trait: str, delay: int) -> None:
    full = full_reconciliation(repair, trait, delay)
    world.facts["full_reconcile"] = full
    if full:
        listener.memes["joy"] += 1
        planner.memes["joy"] += 1
        baby.memes["joy"] += 1
        world.say(
            f"{listener.id} stared for one tiny second, then started laughing too. \"Oh! I thought you meant the babe,\" {listener.pronoun()} said."
        )
        world.say(
            f"Even {baby.id} kicked both feet and made a proud little parade noise, as if agreeing that the misunderstanding had been very silly indeed."
        )
    else:
        listener.memes["shy"] += 1
        planner.memes["shy"] += 1
        world.say(
            f"{listener.id}'s face softened, though {listener.pronoun()} still looked a little sheepish. \"I heard the wrong part,\" {listener.pronoun()} admitted."
        )
        world.say(
            f"{planner.id} gave a small nod, and the two of them stood closer to the ride while {baby.id} patted the pillows and waited for the parade."
        )


def ending(world: World, planner: Entity, listener: Entity, baby: Entity, theme: Theme) -> None:
    if world.facts["full_reconcile"]:
        world.say(
            f"Soon they were fixing the decorations together, with {planner.id} tying bows, {listener.id} straightening the feathers, and {baby.id} wearing the biggest smile in the line."
        )
    else:
        world.say(
            f"Soon they were fixing the decorations together more quietly, but every ribbon they tied made the room feel lighter again."
        )
    world.say(theme.finale)
    world.say(
        f"When the little parade rolled forward, nobody was worried about the misunderstanding anymore. They were too busy laughing to watch the wheels."
    )


def tell(
    setting: Setting,
    vehicle_cfg: Vehicle,
    theme: Theme,
    repair: Repair,
    planner_name: str = "Lily",
    planner_gender: str = "girl",
    listener_name: str = "Ben",
    listener_gender: str = "boy",
    baby_name: str = "Pip",
    parent_type: str = "mother",
    listener_trait: str = "forgiving",
    delay: int = 0,
) -> World:
    world = World(setting)

    planner = world.add(Entity(id="planner", kind="character", type=planner_gender, label=planner_name, role="planner"))
    listener = world.add(
        Entity(
            id="listener",
            kind="character",
            type=listener_gender,
            label=listener_name,
            role="listener",
            attrs={"trait": listener_trait},
        )
    )
    baby = world.add(Entity(id="baby", kind="character", type="baby", label=baby_name, role="baby"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    ride = world.add(Entity(id="ride", kind="thing", type="ride", label=vehicle_cfg.label, role="ride"))
    crowd = world.add(Entity(id="crowd", kind="thing", type="crowd", label="the crowd", role="crowd"))

    world.facts.update(
        planner=planner,
        listener=listener,
        baby=baby,
        parent=parent,
        ride=ride,
        vehicle_cfg=vehicle_cfg,
        theme=theme,
        repair=repair,
        delay=delay,
        listener_trait=listener_trait,
        planner_name=planner_name,
        listener_name=listener_name,
        baby_name=baby_name,
    )

    listener.memes["kindness"] = float(soft_bonus(listener_trait))
    listener.memes["heard_fragment"] = 0.0
    planner.memes["explained"] = 0.0
    planner.memes["apologized"] = 0.0
    crowd.meters["tension"] = 0.0

    introduce(world, planner, listener, baby, parent, theme)
    admire_and_wobble(world, planner, vehicle_cfg, baby)

    world.para()
    bold_plan(world, planner, vehicle_cfg)
    partial_hearing(world, listener, theme)
    accuse(world, listener, planner, baby)
    confusion(world, planner)

    if delay > 0:
        world.say(
            f"For a moment, everybody talked at once, which only made the mix-up wobble around longer."
        )

    world.para()
    repair_scene(world, planner, listener, vehicle_cfg, repair)
    parent_clarifies(world, parent, listener, vehicle_cfg, baby)
    settle(world, planner, listener, baby, repair, listener_trait, delay)

    world.para()
    ending(world, planner, listener, baby, theme)

    return world


def explain_rejection(place: Setting, vehicle: Vehicle) -> str:
    if not place.rent_booth:
        return (
            f"(No story: {place.place} has no place to rent a bigger ride, so the line about wanting to rent one would not make sense here.)"
        )
    return (
        f"(No story: a {vehicle.label} is already roomy enough, so calling it puny just to ask about rent would feel forced. Pick a smaller ride like a stroller or doll cart.)"
    )


def explain_repair(repair_id: str) -> str:
    repair = REPAIRS[repair_id]
    return (
        f"(Refusing repair '{repair_id}': it is too weak for a clean reconciliation "
        f"(sense={repair.sense} < {SENSE_MIN}). Pick a clearer repair like explain, test_ride, or ribbon_peace.)"
    )


@dataclass
class StoryParams:
    place: str
    vehicle: str
    theme: str
    repair: str
    planner_name: str
    planner_gender: str
    listener_name: str
    listener_gender: str
    baby_name: str
    parent: str
    listener_trait: str
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
    "rent": [
        (
            "What does it mean to rent something?",
            "To rent something means you borrow it for a while and give it back later. People often pay to use it for a short time."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or understands something the wrong way. Two people can mean different things even when they use some of the same words."
        )
    ],
    "apology": [
        (
            "Why does an apology help after hurt feelings?",
            "An apology shows that you care about the other person's feelings and want to make things right. It works even better when you also explain what really happened."
        )
    ],
    "stroller": [
        (
            "What is a stroller?",
            "A stroller is a little wheeled seat for a baby. It helps grown-ups move a baby around safely."
        )
    ],
    "wagon": [
        (
            "What is a wagon?",
            "A wagon is a small cart with wheels that can carry things or children. A roomy wagon can hold more than a tiny stroller."
        )
    ],
    "parade": [
        (
            "What is a parade?",
            "A parade is a cheerful line of people, costumes, or rides moving along together. People watch, wave, and enjoy the show."
        )
    ],
}

KNOWLEDGE_ORDER = ["rent", "misunderstanding", "apology", "stroller", "wagon", "parade"]


CURATED = [
    StoryParams(
        place="block_party",
        vehicle="stroller",
        theme="duck",
        repair="test_ride",
        planner_name="Lily",
        planner_gender="girl",
        listener_name="Ben",
        listener_gender="boy",
        baby_name="Pip",
        parent="mother",
        listener_trait="forgiving",
        delay=0,
    ),
    StoryParams(
        place="park_fair",
        vehicle="doll_cart",
        theme="moon",
        repair="explain",
        planner_name="Max",
        planner_gender="boy",
        listener_name="Nora",
        listener_gender="girl",
        baby_name="Mimi",
        parent="father",
        listener_trait="dramatic",
        delay=1,
    ),
    StoryParams(
        place="school_fun_day",
        vehicle="laundry_basket",
        theme="lion",
        repair="ribbon_peace",
        planner_name="Ava",
        planner_gender="girl",
        listener_name="Theo",
        listener_gender="boy",
        baby_name="Otis",
        parent="aunt",
        listener_trait="giggly",
        delay=0,
    ),
    StoryParams(
        place="block_party",
        vehicle="stroller",
        theme="moon",
        repair="ribbon_peace",
        planner_name="Eli",
        planner_gender="boy",
        listener_name="Maya",
        listener_gender="girl",
        baby_name="June",
        parent="uncle",
        listener_trait="proud",
        delay=1,
    ),
]


def generation_prompts(world: World) -> list[str]:
    planner = world.facts["planner"]
    listener = world.facts["listener"]
    baby = world.facts["baby"]
    place = world.setting
    theme = world.facts["theme"]
    vehicle = world.facts["vehicle_cfg"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the words "rent", "puny", and "babe".',
        f"Tell a comedy where {planner.label} says {vehicle.label} looks puny and wants to rent a wagon, but {listener.label} thinks {planner.pronoun('subject')} called {baby.label} a puny babe.",
        f"Write a gentle misunderstanding-and-reconciliation story set at {place.place} during a {theme.costume}, ending with everyone laughing together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    planner = world.facts["planner"]
    listener = world.facts["listener"]
    baby = world.facts["baby"]
    parent = world.facts["parent"]
    vehicle = world.facts["vehicle_cfg"]
    repair = world.facts["repair"]
    place = world.setting
    theme = world.facts["theme"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {planner.label}, {listener.label}, and the baby {baby.label} getting ready for {place.parade_name}. Their {parent.label_word} is there too, helping the little parade get started.",
        ),
        (
            "Why did the trouble start?",
            f"The trouble started because {planner.label} said the {vehicle.label} looked puny and wondered if they should rent something bigger. But {listener.label} only heard the words 'puny' and 'babe' together, so {listener.pronoun('subject')} thought the baby had been insulted.",
        ),
        (
            f"Did {planner.label} really mean to hurt {baby.label}'s feelings?",
            f"No. {planner.label} was talking about the small ride, not the baby. The misunderstanding happened because only part of the sentence was heard.",
        ),
        (
            "How did they fix the misunderstanding?",
            f"They fixed it when {planner.label} {repair.qa_text}. That clear apology and explanation helped {listener.label} understand what had really been meant.",
        ),
    ]
    if world.facts["full_reconcile"]:
        qa.append(
            (
                "How did the story end?",
                f"It ended with a full laugh and a happy parade. The children worked together again, and {theme.finale}",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended more quietly, but kindly. The children understood each other again and kept decorating together, which showed the hurt feelings were fading away.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"rent", "misunderstanding", "apology", "parade"}
    vehicle = world.facts["vehicle_cfg"]
    if vehicle.id == "stroller":
        tags.add("stroller")
    tags.add("wagon")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: misheard={world.facts.get('misheard')} full_reconcile={world.facts.get('full_reconcile')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,V,T) :- place(P), vehicle(V), theme(T), rent_booth(P), small(V).
sensible_repair(R) :- repair(R), sense(R,S), sense_min(M), S >= M.

soft_bonus(T,1) :- trait(T), soft_trait(T).
soft_bonus(T,0) :- trait(T), not soft_trait(T).

full_reconcile :- chosen_repair(R), warmth(R,W), listener_trait(T), soft_bonus(T,B), delay(D), W + B >= D + 2.
outcome(full) :- full_reconcile.
outcome(shy) :- not full_reconcile.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.rent_booth:
            lines.append(asp.fact("rent_booth", place_id))
    for vehicle_id, vehicle in VEHICLES.items():
        lines.append(asp.fact("vehicle", vehicle_id))
        if vehicle.size <= 1:
            lines.append(asp.fact("small", vehicle_id))
        lines.append(asp.fact("size", vehicle_id, vehicle.size))
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("warmth", repair_id, repair.warmth))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
    for trait in sorted(SOFT_TRAITS):
        lines.append(asp.fact("soft_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_repair/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_repair"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_repair", params.repair),
            asp.fact("listener_trait", params.listener_trait),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.listener_trait not in TRAITS:
        raise StoryError(f"(Unknown listener trait: {params.listener_trait})")
    return "full" if full_reconciliation(REPAIRS[params.repair], params.listener_trait, params.delay) else "shy"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_repairs = {r.id for r in sensible_repairs()}
    asp_repairs = set(asp_sensible_repairs())
    if py_repairs == asp_repairs:
        print(f"OK: sensible repairs match ({sorted(py_repairs)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(asp_repairs)} python={sorted(py_repairs)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy storyworld: a rent/puny/babe misunderstanding that ends in reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the confusion lingers before the explanation lands")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible place/vehicle/theme combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.vehicle:
        place = PLACES[args.place]
        vehicle = VEHICLES[args.vehicle]
        if not valid_combo(place, vehicle):
            raise StoryError(explain_rejection(place, vehicle))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.vehicle is None or combo[1] == args.vehicle)
        and (args.theme is None or combo[2] == args.theme)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, vehicle_id, theme_id = rng.choice(sorted(combos))
    repair_id = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    planner_gender = rng.choice(["girl", "boy"])
    listener_gender = rng.choice(["girl", "boy"])
    planner_name = _pick_name(rng, planner_gender)
    listener_name = _pick_name(rng, listener_gender, avoid=planner_name)
    baby_name = rng.choice(BABY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        place=place_id,
        vehicle=vehicle_id,
        theme=theme_id,
        repair=repair_id,
        planner_name=planner_name,
        planner_gender=planner_gender,
        listener_name=listener_name,
        listener_gender=listener_gender,
        baby_name=baby_name,
        parent=parent_type,
        listener_trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.vehicle not in VEHICLES:
        raise StoryError(f"(Unknown vehicle: {params.vehicle})")
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.parent not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if params.listener_trait not in TRAITS:
        raise StoryError(f"(Unknown listener trait: {params.listener_trait})")

    place = PLACES[params.place]
    vehicle = VEHICLES[params.vehicle]
    if not valid_combo(place, vehicle):
        raise StoryError(explain_rejection(place, vehicle))
    repair = REPAIRS[params.repair]
    if repair.sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))

    world = tell(
        setting=place,
        vehicle_cfg=vehicle,
        theme=THEMES[params.theme],
        repair=repair,
        planner_name=params.planner_name,
        planner_gender=params.planner_gender,
        listener_name=params.listener_name,
        listener_gender=params.listener_gender,
        baby_name=params.baby_name,
        parent_type=params.parent,
        listener_trait=params.listener_trait,
        delay=params.delay,
    )
    planner = world.facts["planner"]
    listener = world.facts["listener"]
    baby = world.facts["baby"]
    fixed_story = world.render().replace("planner", planner.label).replace("listener", listener.label).replace("baby", baby.label)
    # Replace only the temporary ids that might still appear in generated lines.
    fixed_story = fixed_story.replace("parent", world.facts["parent"].label_word)
    return StorySample(
        params=params,
        story=fixed_story,
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
        print(asp_program("", "#show valid/3.\n#show sensible_repair/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, vehicle, theme) combos:\n")
        for place, vehicle, theme in combos:
            print(f"  {place:14} {vehicle:16} {theme}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.planner_name}, {p.listener_name}, and {p.baby_name}: {p.vehicle} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
