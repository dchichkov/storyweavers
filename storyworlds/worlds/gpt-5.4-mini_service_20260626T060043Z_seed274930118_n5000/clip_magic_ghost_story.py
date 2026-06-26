#!/usr/bin/env python3
"""
storyworlds/worlds/clip_magic_ghost_story.py
============================================

A small, self-contained storyworld for a gentle ghost tale with a magic clip.

Premise:
- A little ghost wants to drift and play in an old house.
- A special magic clip keeps a sheet-cape neat and safe.
- When the play gets messy or spooky, the wrong choice risks a tear or a scare.
- A careful helper uses the magic clip to solve the problem.

The world is tiny on purpose: a few locations, a few objects, and a single
causal turn from worry to resolution.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("dust", "tear", "glow"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "joy", "worry", "courage", "wonder", "comfort"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str = "clip"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["dust"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("dust", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dust"] += 1
            item.meters["tear"] += 1
            out.append(f"{actor.id}'s {item.label} got dusty and a little torn.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["tear"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That would worry {carer.label}.")
    return out


def _r_spook(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["fear"] < THRESHOLD:
            continue
        sig = ("spook", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["wonder"] += 1
        return ["__spook__"]
    return []


CAUSAL_RULES = [Rule("dust", _r_dust), Rule("worry", _r_worry), Rule("spook", _r_spook)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__spook__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters["tear"] >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little ghost who loved moonlit rooms and quiet corners.")


def loves_magic(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, especially when {activity.keyword} "
        f"gleamed in the dark like a tiny spell."
    )


def prize_line(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} kept {hero.pronoun('possessive')} {prize.label} close, because it was "
        f"the part of the costume that made the ghost feel brave."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One night, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(f"The old room was quiet, and a single draft kept the curtains gently moving.")


def want(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["courage"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, but the dusty corners looked a little spooky.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f'"If you {activity.verb}, your {prize.label} may get {activity.soil}," {parent.label} said softly.')
    return True


def hesitate(world: World, hero: Entity) -> None:
    hero.memes["fear"] += 1
    world.say(f"{hero.id} drifted back and made a small, shaky puff of air.")


def spook_turn(world: World, hero: Entity) -> None:
    hero.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(f"Then {hero.id} heard a creak in the floorboards and hovered very still.")


def offer_clip(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="thing",
        label=gear_def.label,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
        owner=hero.id,
        caretaker=parent.id,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{parent.label} lifted a small smile. "How about we use the magic clip first, '
        f"and then you can {activity.verb} safely?""
    )
    return gear_def


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["comfort"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} nodded, and the magic clip clicked shut with a tiny silver sparkle."
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {hero.pronoun('possessive')} "
        f"{prize.label} stayed clean, and the room felt spooky in a friendly way."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "ghost",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    intro(world, hero)
    loves_magic(world, hero, activity)
    prize_line(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    want(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    hesitate(world, hero)
    spook_turn(world, hero)

    world.para()
    gear_def = offer_clip(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, hero, parent, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear_def, resolved=gear_def is not None)
    return world


SETTINGS = {
    "hall": Setting(place="the old hall", indoor=True, affords={"float"}),
    "attic": Setting(place="the attic", indoor=True, affords={"float"}),
    "nursery": Setting(place="the nursery", indoor=True, affords={"float"}),
}

ACTIVITIES = {
    "float": Activity(
        id="float",
        verb="float through the dusty room",
        gerund="floating through dusty rooms",
        rush="rush through the dark",
        mess="dust",
        soil="dusty and torn",
        zone={"torso"},
        weather="",
        keyword="clip",
        tags={"ghost", "dust", "magic", "clip"},
    )
}

PRIZES = {
    "sheet": Prize(
        label="sheet",
        phrase="a white sheet-cape",
        type="sheet",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="magic_clip",
        label="magic clip",
        covers={"torso"},
        guards={"dust"},
        prep="fasten the magic clip to the sheet-cape",
        tail="carefully clipped the sheet-cape to keep it tidy",
    )
]

GIRL_NAMES = ["Mina", "Luna", "Nora"]
BOY_NAMES = ["Ivo", "Theo", "Pip"]
TRAITS = ["little", "quiet", "curious"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


KNOWLEDGE = {
    "ghost": [("What is a ghost?", "A ghost is a spooky character in a story, often shown as a floating shape or a sheet." संघर्ष? ],
}
