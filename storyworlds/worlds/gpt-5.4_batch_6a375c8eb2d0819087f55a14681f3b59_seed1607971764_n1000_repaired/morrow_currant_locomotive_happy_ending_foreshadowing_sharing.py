#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/morrow_currant_locomotive_happy_ending_foreshadowing_sharing.py
================================================================================================

A small storyworld about a child polishing a beloved toy locomotive, a tray of
currant buns, and an unexpected visitor who needs to be welcomed into the game.

The stories stay close to slice-of-life domestic play:

- a child is excited about a toy locomotive and tomorrow's plans
- a grown-up quietly foreshadows company by setting out one extra plate
- a friend or cousin arrives and admires the train
- the child hesitates, then learns a sensible way to share
- the ending image proves the home has grown warmer, not smaller

Run it
------
    python storyworlds/worlds/gpt-5.4/morrow_currant_locomotive_happy_ending_foreshadowing_sharing.py
    python storyworlds/worlds/gpt-5.4/morrow_currant_locomotive_happy_ending_foreshadowing_sharing.py --place hallway --locomotive wooden_pull --plan pull_together
    python storyworlds/worlds/gpt-5.4/morrow_currant_locomotive_happy_ending_foreshadowing_sharing.py --locomotive windup --plan side_by_side
    python storyworlds/worlds/gpt-5.4/morrow_currant_locomotive_happy_ending_foreshadowing_sharing.py --all
    python storyworlds/worlds/gpt-5.4/morrow_currant_locomotive_happy_ending_foreshadowing_sharing.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/morrow_currant_locomotive_happy_ending_foreshadowing_sharing.py --verify
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
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
class Place:
    id: str
    label: str
    afford_plans: set[str] = field(default_factory=set)
    clue: str = ""
    ending: str = ""
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
class LocomotiveCfg:
    id: str
    label: str
    phrase: str
    mode: str
    capacity: int
    shine: str
    sound: str
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
class GuestCfg:
    id: str
    label: str
    relation: str
    arrival: str
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
class PlayPlan:
    id: str
    label: str
    min_capacity: int
    allowed_modes: set[str] = field(default_factory=set)
    cue: str = ""
    action: str = ""
    ending: str = ""
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


def _r_tension(world: World) -> list[str]:
    hero = world.entities.get("hero")
    guest = world.entities.get("guest")
    loco = world.entities.get("locomotive")
    if not hero or not guest or not loco:
        return []
    if hero.memes["clingy"] < THRESHOLD or guest.memes["hope"] < THRESHOLD:
        return []
    sig = ("tension", hero.id, guest.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    guest.memes["awkward"] += 1
    loco.meters["stillness"] += 1
    return ["__tension__"]


def _r_shared_warmth(world: World) -> list[str]:
    hero = world.entities.get("hero")
    guest = world.entities.get("guest")
    room = world.entities.get("room")
    if not hero or not guest or not room:
        return []
    if hero.memes["sharing"] < THRESHOLD or guest.memes["included"] < THRESHOLD:
        return []
    sig = ("warmth", hero.id, guest.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["joy"] += 1
    guest.memes["joy"] += 1
    room.meters["warmth"] += 1
    return ["__warmth__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="tension", tag="social", apply=_r_tension),
    Rule(name="shared_warmth", tag="social", apply=_r_shared_warmth),
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


def plan_fits(place: Place, locomotive: LocomotiveCfg, plan: PlayPlan) -> bool:
    return (
        plan.id in place.afford_plans
        and locomotive.capacity >= plan.min_capacity
        and locomotive.mode in plan.allowed_modes
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for loco_id, loco in LOCOMOTIVES.items():
            for plan_id, plan in PLANS.items():
                if plan_fits(place, loco, plan):
                    combos.append((place_id, loco_id, plan_id))
    return combos


def predict_sharing(place: Place, locomotive: LocomotiveCfg, plan: PlayPlan) -> dict:
    return {
        "works": plan_fits(place, locomotive, plan),
        "capacity": locomotive.capacity,
        "needed": plan.min_capacity,
    }


def introduce(world: World, hero: Entity, carer: Entity, loco: Entity, place: Place, loco_cfg: LocomotiveCfg) -> None:
    hero.memes["anticipation"] += 1
    loco.meters["polished"] += 1
    world.say(
        f"{hero.id} spent the slow afternoon in {place.label}, rubbing {loco_cfg.phrase} "
        f"with the corner of a soft cloth until it {loco_cfg.shine}."
    )
    world.say(
        f'"I want it to look nice on the morrow," {hero.pronoun()} said, because {hero.pronoun("possessive")} '
        f'{carer.label_word} had promised a small train table after breakfast.'
    )


def buns_and_clue(world: World, carer: Entity, hero: Entity, place: Place) -> None:
    tray = world.get("tray")
    tray.meters["warm"] += 1
    tray.attrs["snack"] = "currant buns"
    world.facts["snack"] = "currant buns"
    world.facts["clue_set"] = True
    world.say(
        f"From the kitchen came the sweet smell of currant buns. {carer.label_word.capitalize()} set "
        f"them on a tray and, without any fuss, {place.clue}"
    )
    world.say(
        f'{carer.pronoun().capitalize()} smiled at {hero.id}. "A home feels better when it is ready for one more."'
    )


def arrival(world: World, guest: Entity, guest_cfg: GuestCfg, loco_cfg: LocomotiveCfg) -> None:
    guest.memes["hope"] += 1
    world.facts["guest_arrived"] = True
    world.say(guest_cfg.arrival)
    world.say(
        f"{guest.id} stopped just inside the room and stared at the {loco_cfg.label}. "
        f'"What a lovely locomotive," {guest.pronoun()} whispered.'
    )


def hesitate(world: World, hero: Entity, guest: Entity, loco_cfg: LocomotiveCfg) -> None:
    hero.memes["clingy"] += 1
    propagate(world, narrate=False)
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.id} curled {hero.pronoun('possessive')} hand around the {loco_cfg.label} and held it close. "
            f"{hero.pronoun().capitalize()} had been dreaming about tomorrow, and suddenly sharing today felt hard."
        )
        world.say(
            f"{guest.id} took one small step back and folded {guest.pronoun('possessive')} hands, trying not to look too eager."
        )


def suggest(world: World, carer: Entity, hero: Entity, guest: Entity, plan: PlayPlan, loco_cfg: LocomotiveCfg, place: Place) -> None:
    pred = predict_sharing(place, loco_cfg, plan)
    world.facts["predicted_capacity"] = pred["capacity"]
    world.facts["predicted_needed"] = pred["needed"]
    world.say(
        f'{carer.label_word.capitalize()} noticed both children at once. "{plan.cue}," {carer.pronoun()} said softly. '
        f'"That way the {loco_cfg.label} can be fun for both of you."'
    )


def choose_share(world: World, hero: Entity, guest: Entity, plan: PlayPlan) -> None:
    hero.memes["sharing"] += 1
    guest.memes["included"] += 1
    propagate(world, narrate=False)
    world.facts["shared"] = True
    world.say(
        f"{hero.id} looked at the extra plate on the tray, then at {guest.id}, and let out a small breath."
    )
    world.say(
        f'"All right," {hero.pronoun()} said. "{plan.label}."'
    )


def play_together(world: World, hero: Entity, guest: Entity, plan: PlayPlan, loco_cfg: LocomotiveCfg) -> None:
    loco = world.get("locomotive")
    loco.meters["rolling"] += 1
    world.say(
        plan.action.format(hero=hero.id, guest=guest.id, locomotive=loco_cfg.label, sound=loco_cfg.sound)
    )
    if world.get("room").meters["warmth"] >= THRESHOLD:
        world.say(
            "The room changed all at once. It no longer felt like a place where someone might be left out."
        )


def snack_end(world: World, carer: Entity, hero: Entity, guest: Entity, place: Place, plan: PlayPlan) -> None:
    tray = world.get("tray")
    tray.meters["shared"] += 1
    hero.memes["full"] += 1
    guest.memes["full"] += 1
    world.say(
        f"Soon the children were sitting shoulder to shoulder with their currant buns, cheeks warm from play and from the oven's sweetness."
    )
    world.say(
        f"{carer.label_word.capitalize()} tapped the spare plate with one finger and gave a pleased little nod. "
        f"{plan.ending}"
    )
    world.say(place.ending)


def tell(
    *,
    place: Place,
    locomotive_cfg: LocomotiveCfg,
    guest_cfg: GuestCfg,
    plan: PlayPlan,
    hero_name: str = "Mara",
    hero_type: str = "girl",
    guest_name: str = "Ben",
    guest_type: str = "boy",
    carer_type: str = "grandfather",
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    guest = world.add(Entity(id="guest", kind="character", type=guest_type, label=guest_name, role="guest"))
    carer = world.add(Entity(id="carer", kind="character", type=carer_type, label="the grown-up", role="carer"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.label))
    tray = world.add(Entity(id="tray", kind="thing", type="tray", label="tray", attrs={"snack": "currant buns"}))
    locomotive = world.add(
        Entity(
            id="locomotive",
            kind="thing",
            type="toy",
            label=locomotive_cfg.label,
            attrs={"mode": locomotive_cfg.mode, "capacity": locomotive_cfg.capacity},
        )
    )

    world.facts.update(
        hero=hero,
        guest=guest,
        carer=carer,
        place=place,
        locomotive_cfg=locomotive_cfg,
        guest_cfg=guest_cfg,
        plan=plan,
        clue_set=False,
        guest_arrived=False,
        shared=False,
    )

    introduce(world, hero, carer, locomotive, place, locomotive_cfg)
    buns_and_clue(world, carer, hero, place)

    world.para()
    arrival(world, guest, guest_cfg, locomotive_cfg)
    hesitate(world, hero, guest, locomotive_cfg)

    world.para()
    suggest(world, carer, hero, guest, plan, locomotive_cfg, place)
    choose_share(world, hero, guest, plan)
    play_together(world, hero, guest, plan, locomotive_cfg)

    world.para()
    snack_end(world, carer, hero, guest, place, plan)

    world.facts["warm_ending"] = world.get("room").meters["warmth"] >= THRESHOLD
    return world


PLACES = {
    "hallway": Place(
        id="hallway",
        label="the front hallway",
        afford_plans={"turns", "pull_together"},
        clue="set out three small plates instead of two on the bench by the wall",
        ending="By evening, the hallway looked ordinary again, but it felt kinder than before.",
        tags={"sharing", "home"},
    ),
    "parlor": Place(
        id="parlor",
        label="the parlor rug",
        afford_plans={"turns", "side_by_side"},
        clue="laid a spare cushion beside the rug as if another child might soon need it",
        ending="When the lamps came on, the parlor rug still held the shape of two children leaning close over the train.",
        tags={"sharing", "home"},
    ),
    "garden_path": Place(
        id="garden_path",
        label="the covered garden path",
        afford_plans={"turns", "pull_together"},
        clue="balanced one extra napkin on the tray before carrying it outside",
        ending="At dusk the garden path smelled of damp leaves and currants, and the game had room for everyone.",
        tags={"sharing", "garden"},
    ),
}

LOCOMOTIVES = {
    "windup": LocomotiveCfg(
        id="windup",
        label="wind-up locomotive",
        phrase="a little wind-up locomotive",
        mode="single",
        capacity=1,
        shine="gleamed like a black pebble",
        sound="tick-tick",
        tags={"locomotive", "sharing"},
    ),
    "tin_track": LocomotiveCfg(
        id="tin_track",
        label="tin locomotive",
        phrase="a tin locomotive with a red stripe",
        mode="single",
        capacity=1,
        shine="caught a neat stripe of window light",
        sound="chuff-chuff",
        tags={"locomotive", "sharing"},
    ),
    "wooden_pull": LocomotiveCfg(
        id="wooden_pull",
        label="wooden locomotive",
        phrase="a wooden locomotive with a blue cord",
        mode="pull",
        capacity=2,
        shine="looked smooth as honey",
        sound="clack-clack",
        tags={"locomotive", "sharing"},
    ),
    "ride_box": LocomotiveCfg(
        id="ride_box",
        label="cardboard locomotive",
        phrase="a cardboard locomotive painted by hand",
        mode="ride",
        capacity=2,
        shine="looked bright under its fresh paint",
        sound="whoo-whoo",
        tags={"locomotive", "sharing"},
    ),
}

GUESTS = {
    "neighbor": GuestCfg(
        id="neighbor",
        label="neighbor",
        relation="neighbor",
        arrival='A tap came at the door, and the neighbor child from next door stood there with a rain-damp collar and a shy smile.',
        tags={"neighbor"},
    ),
    "cousin": GuestCfg(
        id="cousin",
        label="cousin",
        relation="cousin",
        arrival='A minute later, a cousin stepped in from the yard, brushing crumbs of dry leaf from one sleeve.',
        tags={"family"},
    ),
    "classmate": GuestCfg(
        id="classmate",
        label="classmate",
        relation="classmate",
        arrival='Then a classmate arrived with a borrowed book tucked under one arm and stopped when the train came into view.',
        tags={"friend"},
    ),
}

PLANS = {
    "turns": PlayPlan(
        id="turns",
        label="We can take turns",
        min_capacity=1,
        allowed_modes={"single", "pull", "ride"},
        cue="Why not take turns, one lap each and then one bun each",
        action="{hero} wound the {locomotive} and sent it along, and when it came back with its {sound}, {guest} had the next turn ready. Before long they were counting the laps together instead of guarding them.",
        ending="The extra plate had not been a mistake after all. It had been a welcome waiting quietly for the right moment.",
        qa_text="They took turns with the locomotive, so each child got a fair chance to play.",
        tags={"turns", "sharing"},
    ),
    "pull_together": PlayPlan(
        id="pull_together",
        label="Let us pull it together",
        min_capacity=2,
        allowed_modes={"pull"},
        cue="You could pull it together, one on each side of the string",
        action="{hero} and {guest} each took part of the cord and walked the {locomotive} down the floor with a soft {sound}. They had to match their steps, and the train rolled straighter when they listened to each other.",
        ending="The game worked best once the children stopped thinking about whose train it had been first.",
        qa_text="They pulled the locomotive together, so the play itself needed cooperation.",
        tags={"sharing", "cooperation"},
    ),
    "side_by_side": PlayPlan(
        id="side_by_side",
        label="We can sit side by side inside it",
        min_capacity=2,
        allowed_modes={"ride"},
        cue="There is room to sit side by side and make one long journey",
        action="{hero} lifted the flap of the {locomotive}, and soon both children were inside, knees tucked up, making a small {sound} into the afternoon. One called the stations while the other watched the corners.",
        ending="The children laughed so hard inside the cardboard train that even the walls seemed to smile back.",
        qa_text="They sat side by side in the locomotive, sharing one pretend journey together.",
        tags={"sharing", "cooperation"},
    ),
}


GIRL_NAMES = ["Mara", "Lina", "Nora", "Elsie", "Ruth", "Ivy", "Tessa", "Mina"]
BOY_NAMES = ["Ben", "Owen", "Theo", "Jude", "Milo", "Evan", "Cal", "Finn"]
CARERS = ["grandmother", "grandfather", "mother", "father"]


@dataclass
class StoryParams:
    place: str = "hallway"
    locomotive: str = "windup"
    guest: str = "neighbor"
    plan: str = "turns"
    hero_name: str = "Mara"
    hero_type: str = "girl"
    guest_name: str = "Ben"
    guest_type: str = "boy"
    carer_type: str = "grandfather"
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


CURATED = [
    StoryParams(
        place="hallway",
        locomotive="windup",
        guest="neighbor",
        plan="turns",
        hero_name="Mara",
        hero_type="girl",
        guest_name="Ben",
        guest_type="boy",
        carer_type="grandfather",
    ),
    StoryParams(
        place="garden_path",
        locomotive="wooden_pull",
        guest="cousin",
        plan="pull_together",
        hero_name="Theo",
        hero_type="boy",
        guest_name="Ivy",
        guest_type="girl",
        carer_type="grandmother",
    ),
    StoryParams(
        place="parlor",
        locomotive="ride_box",
        guest="classmate",
        plan="side_by_side",
        hero_name="Elsie",
        hero_type="girl",
        guest_name="Milo",
        guest_type="boy",
        carer_type="mother",
    ),
    StoryParams(
        place="parlor",
        locomotive="tin_track",
        guest="neighbor",
        plan="turns",
        hero_name="Cal",
        hero_type="boy",
        guest_name="Nora",
        guest_type="girl",
        carer_type="father",
    ),
]


KNOWLEDGE = {
    "currant": [
        (
            "What is a currant?",
            "A currant is a very small dried fruit. People often bake currants into buns, cakes, or bread for a sweet taste."
        )
    ],
    "locomotive": [
        (
            "What is a locomotive?",
            "A locomotive is the engine that pulls a train. In a toy version, it is the part children push, wind, or pretend to ride."
        )
    ],
    "sharing": [
        (
            "Why is sharing important in play?",
            "Sharing helps everyone feel included. When children share, the game often becomes bigger and more fun than it was for just one person."
        )
    ],
    "turns": [
        (
            "What does taking turns mean?",
            "Taking turns means one person goes first and another person goes next. It is a fair way to share when only one child can use something at a time."
        )
    ],
    "cooperation": [
        (
            "What does cooperation mean?",
            "Cooperation means working together on the same job or game. When people cooperate, they listen to each other and help the plan go smoothly."
        )
    ],
    "foreshadow": [
        (
            "What is a clue in a story?",
            "A clue is a small detail that hints something may happen later. It helps the ending feel prepared instead of sudden."
        )
    ],
}
KNOWLEDGE_ORDER = ["currant", "locomotive", "sharing", "turns", "cooperation", "foreshadow"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    guest = world.facts["guest"]
    place = world.facts["place"]
    loco = world.facts["locomotive_cfg"]
    plan = world.facts["plan"]
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the words "morrow," "currant," and "locomotive," and ends happily with sharing.',
        f"Tell a gentle home story where {hero.label} is excited about a {loco.label}, a grown-up quietly foreshadows a guest, and {guest.label} arrives to join the play in {place.label}.",
        f"Write a child-facing story where a treasured toy feels hard to share at first, but the children solve it by this plan: {plan.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    guest = world.facts["guest"]
    carer = world.facts["carer"]
    place = world.facts["place"]
    loco = world.facts["locomotive_cfg"]
    plan = world.facts["plan"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, {guest.label}, and {hero.label}'s {carer.label_word}. They spend an ordinary afternoon at home that turns into a shared game."
        ),
        (
            f"Why did {hero.label} care so much about the {loco.label}?",
            f"{hero.label} had been polishing it and thinking about showing it off on the morrow. Because the toy felt special and full of tomorrow's hopes, sharing it right away felt difficult."
        ),
        (
            "What was the clue that someone else might join them?",
            f"{carer.label_word.capitalize()} quietly made room for one more before anyone arrived. That clue mattered later, because the extra plate or cushion showed the house was already prepared to welcome a guest."
        ),
        (
            f"Why did {guest.label} look careful and shy at first?",
            f"{guest.label} admired the locomotive, but {hero.label} hugged it close. That made the moment feel delicate, so {guest.label} tried not to push in."
        ),
        (
            "How did they solve the problem?",
            f"{plan.qa_text} This worked because the plan matched the kind of locomotive they had, so sharing felt fair instead of forced."
        ),
        (
            "How did the story end?",
            f"It ended with both children eating currant buns and playing together in {place.label}. The ending feels happy because the home grew warmer once there was room for one more child."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"currant", "locomotive", "sharing", "foreshadow"} | set(world.facts["plan"].tags)
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
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, locomotive: LocomotiveCfg, plan: PlayPlan) -> str:
    if plan.id not in place.afford_plans:
        return (
            f"(No story: {place.label} does not support the plan '{plan.id}'. "
            f"That room fits {', '.join(sorted(place.afford_plans))} instead.)"
        )
    if locomotive.capacity < plan.min_capacity:
        return (
            f"(No story: the {locomotive.label} only has room for {locomotive.capacity}, "
            f"but the plan '{plan.id}' needs capacity {plan.min_capacity}.)"
        )
    if locomotive.mode not in plan.allowed_modes:
        return (
            f"(No story: the {locomotive.label} is a {locomotive.mode} kind of toy, "
            f"so it does not suit the plan '{plan.id}'.)"
        )
    return "(No story: that place, locomotive, and sharing plan do not fit together.)"


ASP_RULES = r"""
fits(Place, Loco, Plan) :-
    affords(Place, Plan),
    capacity(Loco, Cap),
    need(Plan, Need),
    Cap >= Need,
    mode(Loco, Mode),
    allows(Plan, Mode).

#show fits/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for plan_id in sorted(place.afford_plans):
            lines.append(asp.fact("affords", place_id, plan_id))
    for loco_id, loco in LOCOMOTIVES.items():
        lines.append(asp.fact("locomotive", loco_id))
        lines.append(asp.fact("capacity", loco_id, loco.capacity))
        lines.append(asp.fact("mode", loco_id, loco.mode))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("need", plan_id, plan.min_capacity))
        for mode in sorted(plan.allowed_modes):
            lines.append(asp.fact("allows", plan_id, mode))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "fits")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a treasured locomotive, an unexpected guest, and a happy act of sharing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--locomotive", choices=LOCOMOTIVES)
    ap.add_argument("--guest", choices=GUESTS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hero-name")
    ap.add_argument("--guest-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--guest-type", choices=["girl", "boy"])
    ap.add_argument("--carer-type", choices=CARERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.locomotive and args.plan:
        place = PLACES[args.place]
        locomotive = LOCOMOTIVES[args.locomotive]
        plan = PLANS[args.plan]
        if not plan_fits(place, locomotive, plan):
            raise StoryError(explain_rejection(place, locomotive, plan))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.locomotive is None or combo[1] == args.locomotive)
        and (args.plan is None or combo[2] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, locomotive_id, plan_id = rng.choice(sorted(combos))
    guest_id = args.guest or rng.choice(sorted(GUESTS.keys()))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    guest_type = args.guest_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    guest_name = args.guest_name or _pick_name(rng, guest_type, avoid=hero_name)
    carer_type = args.carer_type or rng.choice(CARERS)

    return StoryParams(
        place=place_id,
        locomotive=locomotive_id,
        guest=guest_id,
        plan=plan_id,
        hero_name=hero_name,
        hero_type=hero_type,
        guest_name=guest_name,
        guest_type=guest_type,
        carer_type=carer_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.locomotive not in LOCOMOTIVES:
        raise StoryError(f"(Unknown locomotive: {params.locomotive})")
    if params.guest not in GUESTS:
        raise StoryError(f"(Unknown guest type: {params.guest})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown sharing plan: {params.plan})")

    place = PLACES[params.place]
    locomotive_cfg = LOCOMOTIVES[params.locomotive]
    guest_cfg = GUESTS[params.guest]
    plan = PLANS[params.plan]

    if not plan_fits(place, locomotive_cfg, plan):
        raise StoryError(explain_rejection(place, locomotive_cfg, plan))

    world = tell(
        place=place,
        locomotive_cfg=locomotive_cfg,
        guest_cfg=guest_cfg,
        plan=plan,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        guest_name=params.guest_name,
        guest_type=params.guest_type,
        carer_type=params.carer_type,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(0))
        default_params.seed = 0
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAIL: resolve_params() crashed: {err}")

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            _ = sample.to_dict()
            _ = sample.to_json()
            if i == 1:
                emit(sample, trace=False, qa=False, header="")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"SMOKE FAIL on case {i}: {err}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, locomotive, plan) combos:\n")
        for place, locomotive, plan in combos:
            print(f"  {place:12} {locomotive:12} {plan}")
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
            header = f"### {p.hero_name} / {p.locomotive} / {p.plan} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
