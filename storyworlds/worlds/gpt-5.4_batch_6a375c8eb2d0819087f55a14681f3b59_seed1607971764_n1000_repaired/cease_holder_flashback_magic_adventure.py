#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cease_holder_flashback_magic_adventure.py
====================================================================

A standalone story world for a tiny magical adventure domain built from the seed
words "cease" and "holder" plus the features Flashback and Magic.

Premise
-------
A child goes on a small quest through a magical path, carrying a bright charm in
the right holder so it can be returned to an old shrine. A living obstacle
blocks the way. In the tense middle, the child remembers an earlier lesson from
a kind mentor: magic works best when the charm is kept in the right holder and
spoken to with a calm word. That flashback changes what the child does in the
present. The child then uses a fitting spell -- always including the word
"cease" -- to calm the obstacle and finish the adventure.

Reasonableness constraint
-------------------------
Not every charm belongs in every holder, and not every charm can calm every
obstacle. The world refuses mismatches. A sunmote in a thin glass holder is a
bad idea; a dawnreed cannot quiet a wall of wind. This world generates only
combinations where:

* the chosen route really contains the chosen obstacle,
* the chosen charm is the kind of magic that can calm that obstacle, and
* the chosen holder can safely carry that charm.

There are two happy-but-different outcomes:
* steady  -- the child faces the obstacle with enough nerve/support to act at once
* shaky   -- the child wobbles first, then the companion and the remembered lesson
             help the child recover

Run it
------
python storyworlds/worlds/gpt-5.4/cease_holder_flashback_magic_adventure.py
python storyworlds/worlds/gpt-5.4/cease_holder_flashback_magic_adventure.py --route cliff_path --obstacle wind_wall --charm stillstone --holder brass_holder
python storyworlds/worlds/gpt-5.4/cease_holder_flashback_magic_adventure.py --holder glass_holder --charm sunmote
python storyworlds/worlds/gpt-5.4/cease_holder_flashback_magic_adventure.py --all
python storyworlds/worlds/gpt-5.4/cease_holder_flashback_magic_adventure.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/cease_holder_flashback_magic_adventure.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "mentor_f"}
        male = {"boy", "man", "father", "uncle", "mentor_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Route:
    id: str
    place: str
    opening: str
    trail: str
    destination: str
    affords: set[str] = field(default_factory=set)
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
class Obstacle:
    id: str
    label: str
    phrase: str
    arrival: str
    motion: str
    threat: int
    spell_target: str
    after: str
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
class Charm:
    id: str
    label: str
    phrase: str
    glow: str
    solves: str
    spell: str
    memory_line: str
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
class Holder:
    id: str
    label: str
    phrase: str
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
class Companion:
    id: str
    label: str
    phrase: str
    type: str
    support: int
    cue: str
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


@dataclass
class MentorCfg:
    id: str
    name: str
    type: str
    title: str
    teaching: str
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
class Trait:
    id: str
    word: str
    nerve: int
    flavor: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_obstacle_fear(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    if obstacle.meters["blocking"] < THRESHOLD:
        return []
    sig = ("obstacle_fear", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.meters["halted"] += 1
    return ["__fear__"]


def _r_companion_steady(world: World) -> list[str]:
    hero = world.get("hero")
    companion = world.get("companion")
    if hero.memes["fear"] < THRESHOLD or companion.attrs.get("support", 0) <= 0:
        return []
    sig = ("companion_steady", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["courage"] += 1
    hero.memes["trust"] += 1
    return ["__steady__"]


def _r_spell_calm(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    charm = world.get("charm")
    if charm.meters["cast"] < THRESHOLD:
        return []
    if world.facts.get("charm_match") is not True:
        return []
    sig = ("spell_calm", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["blocking"] = 0.0
    obstacle.meters["calm"] += 1
    hero = world.get("hero")
    hero.meters["progress"] += 1
    hero.memes["relief"] += 1
    hero.memes["wonder"] += 1
    return ["__calmed__"]


CAUSAL_RULES = [
    Rule(name="obstacle_fear", tag="emotional", apply=_r_obstacle_fear),
    Rule(name="companion_steady", tag="social", apply=_r_companion_steady),
    Rule(name="spell_calm", tag="magic", apply=_r_spell_calm),
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


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def holder_fits(holder: Holder, charm: Charm) -> bool:
    return charm.id in holder.fits


def charm_solves(charm: Charm, obstacle: Obstacle) -> bool:
    return charm.solves == obstacle.id


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for route_id, route in ROUTES.items():
        for obstacle_id in route.affords:
            obstacle = OBSTACLES[obstacle_id]
            for charm_id, charm in CHARMS.items():
                if not charm_solves(charm, obstacle):
                    continue
                for holder_id, holder in HOLDERS.items():
                    if holder_fits(holder, charm):
                        combos.append((route_id, obstacle_id, charm_id, holder_id))
    return sorted(combos)


def outcome_of(params: "StoryParams") -> str:
    obstacle = OBSTACLES[params.obstacle]
    trait = TRAITS[params.trait]
    companion = COMPANIONS[params.companion]
    return "steady" if (trait.nerve + companion.support) >= (obstacle.threat + 1) else "shaky"


def predict_spell(world: World) -> dict:
    sim = world.copy()
    sim.get("charm").meters["cast"] += 1
    propagate(sim, narrate=False)
    return {
        "clears": sim.get("obstacle").meters["blocking"] < THRESHOLD,
        "relief": sim.get("hero").memes["relief"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, route: Route, companion: Companion) -> None:
    world.say(
        f"{hero.id} was a {TRAITS[hero.attrs['trait']].word} little adventurer who liked to follow paths that seemed to lead somewhere secret."
    )
    world.say(
        f"At the edge of {route.place}, {hero.pronoun()} set off with {companion.phrase}. "
        f"{route.opening}"
    )


def give_quest(world: World, hero: Entity, charm: Charm, holder: Holder, route: Route) -> None:
    hero.memes["purpose"] += 1
    world.say(
        f"In {hero.pronoun('possessive')} pocket rested {holder.phrase}, and inside it glowed {charm.phrase}. "
        f"{route.trail} {hero.id} had promised to carry the magic all the way to {route.destination}."
    )


def appear_obstacle(world: World, obstacle: Obstacle) -> None:
    obs = world.get("obstacle")
    obs.meters["blocking"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.arrival)
    world.say(obstacle.motion)


def wobble(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.meters["step_back"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} took one step forward, then one step back. The {obstacle.label} looked bigger up close, and for a moment {hero.pronoun()} did not know what to do."
    )


def flashback(world: World, hero: Entity, mentor: Entity, charm: Charm, holder: Holder) -> None:
    hero.memes["memory"] += 1
    world.facts["flashback_used"] = True
    world.say(
        f"Then a flashback rose in {hero.id}'s mind. {mentor.id} had once placed {charm.phrase} into {holder.phrase} and said, "
        f'"{mentor.attrs["teaching"]} {charm.memory_line}"'
    )


def companion_cue(world: World, companion: Companion) -> None:
    world.say(companion.cue)


def cast_spell(world: World, hero: Entity, charm: Charm, obstacle: Obstacle) -> None:
    pred = predict_spell(world)
    world.facts["predicted_clear"] = pred["clears"]
    world.get("charm").meters["cast"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} held up the holder, and {charm.glow}. "
        f'"{charm.spell.format(target=obstacle.spell_target)}" {hero.pronoun()} said.'
    )
    if pred["clears"]:
        world.say(obstacle.after)


def cross_and_finish(world: World, hero: Entity, route: Route, companion: Companion, charm: Charm) -> None:
    hero.meters["arrived"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"With the way open at last, {hero.id} hurried on to {route.destination} and set {charm.phrase} in its waiting place."
    )
    world.say(
        f"Light spread softly over the stones, and {companion.ending}."
    )
    world.say(
        f"{hero.id} smiled all the way home. The adventure had begun with a heavy pocket and a worried heart, and it ended with a brave memory shining brighter than the magic itself."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    obstacle_cfg: Obstacle,
    charm_cfg: Charm,
    holder_cfg: Holder,
    companion_cfg: Companion,
    mentor_cfg: Mentor,
    trait_cfg: Trait,
    hero_name: str,
    hero_type: HeroType,
    route=None,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        attrs={"trait": trait_cfg.id},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="thing",
        type=companion_cfg.type,
        label=companion_cfg.label,
        phrase=companion_cfg.phrase,
        role="companion",
        attrs={"support": companion_cfg.support},
    ))
    mentor = world.add(Entity(
        id=mentor_cfg.name,
        kind="character",
        type=mentor_cfg.type,
        label=mentor_cfg.title,
        role="mentor",
        attrs={"teaching": mentor_cfg.teaching},
    ))
    holder = world.add(Entity(
        id="holder",
        kind="thing",
        type="holder",
        label=holder_cfg.label,
        phrase=holder_cfg.phrase,
    ))
    charm = world.add(Entity(
        id="charm",
        kind="thing",
        type="charm",
        label=charm_cfg.label,
        phrase=charm_cfg.phrase,
    ))
    obstacle = world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle_cfg.label,
        phrase=obstacle_cfg.phrase,
    ))

    hero.memes["courage"] = float(trait_cfg.nerve)
    hero.memes["fear"] = 0.0
    hero.memes["memory"] = 0.0
    hero.memes["trust"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["wonder"] = 0.0
    hero.memes["joy"] = 0.0
    hero.meters["progress"] = 0.0
    hero.meters["halted"] = 0.0
    hero.meters["step_back"] = 0.0
    hero.meters["arrived"] = 0.0
    companion.meters["near"] = 1.0
    obstacle.meters["blocking"] = 0.0
    obstacle.meters["calm"] = 0.0
    charm.meters["cast"] = 0.0

    world.facts.update(
        route=route,
        obstacle_cfg=obstacle_cfg,
        charm_cfg=charm_cfg,
        holder_cfg=holder_cfg,
        companion_cfg=companion_cfg,
        mentor_cfg=mentor_cfg,
        trait_cfg=trait_cfg,
        hero=hero,
        companion=companion,
        mentor=mentor,
        obstacle=obstacle,
        holder=holder,
        charm=charm,
        flashback_used=False,
        charm_match=charm_solves(charm_cfg, obstacle_cfg),
    )

    introduce(world, hero, route, companion_cfg)
    give_quest(world, hero, charm_cfg, holder_cfg, route)

    world.para()
    appear_obstacle(world, obstacle_cfg)

    if outcome_of(StoryParams(
        route=route.id,
        obstacle=obstacle_cfg.id,
        charm=charm_cfg.id,
        holder=holder_cfg.id,
        companion=companion_cfg.id,
        mentor=mentor_cfg.id,
        trait=trait_cfg.id,
        hero_name=hero_name,
        hero_type=hero_type,
    )) == "shaky":
        wobble(world, hero, obstacle_cfg)
        companion_cue(world, companion_cfg)
    else:
        world.say(
            f"{hero.id}'s heart thumped, but {hero.pronoun()} kept hold of the magic holder and did not run."
        )

    world.para()
    flashback(world, hero, mentor, charm_cfg, holder_cfg)
    cast_spell(world, hero, charm_cfg, obstacle_cfg)

    world.para()
    cross_and_finish(world, hero, route, companion_cfg, charm_cfg)

    world.facts["outcome"] = outcome_of(StoryParams(
        route=route.id,
        obstacle=obstacle_cfg.id,
        charm=charm_cfg.id,
        holder=holder_cfg.id,
        companion=companion_cfg.id,
        mentor=mentor_cfg.id,
        trait=trait_cfg.id,
        hero_name=hero_name,
        hero_type=hero_type,
    ))
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
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


ROUTES = {
    "moonwood": Route(
        id="moonwood",
        place="Moonwood",
        opening="Silver leaves whispered over the path, and every root looked like a clue.",
        trail="At the end of the winding trail stood the old arch of dawn.",
        destination="the old arch of dawn",
        affords={"fog_veil"},
        tags={"forest", "adventure"},
    ),
    "cliff_path": Route(
        id="cliff_path",
        place="the cliff path above the sea",
        opening="Below, the waves boomed against black rocks, and above, gulls circled like tiny white kites.",
        trail="Past the last bend waited the eagle gate of the ridge.",
        destination="the eagle gate of the ridge",
        affords={"wind_wall"},
        tags={"cliff", "adventure"},
    ),
    "reed_marsh": Route(
        id="reed_marsh",
        place="the reed marsh",
        opening="Tall green reeds parted and closed again, as if the path itself were breathing.",
        trail="Beyond the wet boards glimmered the little tower of lantern reeds.",
        destination="the little tower of lantern reeds",
        affords={"shadow_pool"},
        tags={"marsh", "adventure"},
    ),
}

OBSTACLES = {
    "fog_veil": Obstacle(
        id="fog_veil",
        label="fog veil",
        phrase="a curtain of silver fog",
        arrival="Soon the path narrowed, and a curtain of silver fog slid down between the trees.",
        motion="It swirled across the trail until the stones ahead disappeared.",
        threat=1,
        spell_target="wandering mist",
        after="The fog shivered, thinned, and folded itself away from the path like a sleepy blanket.",
        tags={"fog", "magic"},
    ),
    "wind_wall": Obstacle(
        id="wind_wall",
        label="wind wall",
        phrase="a wall of shoving wind",
        arrival="Soon the trail climbed high, and a wall of shoving wind rose across the path.",
        motion="It pushed pebbles backward and tugged at sleeves as if the mountain wanted the travelers to turn around.",
        threat=2,
        spell_target="rushing wind",
        after="The wind gave one last wild spin, then sank to a patient breeze that only fluttered the grass.",
        tags={"wind", "magic"},
    ),
    "shadow_pool": Obstacle(
        id="shadow_pool",
        label="shadow pool",
        phrase="a pool of dark, glassy shadow",
        arrival="Soon the boards ended, and a pool of dark, glassy shadow spread over the way.",
        motion="It held no reflection at all, only a quiet darkness that made the next step hard to trust.",
        threat=2,
        spell_target="dark water",
        after="The shadow pool rippled, turned clear as tea in sunlight, and showed the stepping stones underneath.",
        tags={"shadow", "magic"},
    ),
}

CHARMS = {
    "sunmote": Charm(
        id="sunmote",
        label="sunmote",
        phrase="a sunmote no bigger than a plum seed",
        glow="gold light slipped between the fingers like warm morning",
        solves="fog_veil",
        spell="Cease, {target}, and let the road remember itself.",
        memory_line="When the path grows lost, ask the bright thing to help the world remember its shape.",
        tags={"sun", "magic"},
    ),
    "stillstone": Charm(
        id="stillstone",
        label="stillstone",
        phrase="a stillstone smooth as river glass",
        glow="a calm blue ring spread through the air",
        solves="wind_wall",
        spell="Cease, {target}, and be a kind breeze instead.",
        memory_line="Heavy magic likes a steady hand and a holder that will not shake.",
        tags={"stone", "magic"},
    ),
    "dawnreed": Charm(
        id="dawnreed",
        label="dawnreed",
        phrase="a dawnreed tied with silver thread",
        glow="pale green light ran along the reed like a waking firefly",
        solves="shadow_pool",
        spell="Cease, {target}, and show the stepping way.",
        memory_line="Gentle magic opens hidden paths when you speak to it softly.",
        tags={"reed", "magic"},
    ),
}

HOLDERS = {
    "brass_holder": Holder(
        id="brass_holder",
        label="brass holder",
        phrase="a brass holder with a warm lid",
        fits={"sunmote", "stillstone"},
        tags={"holder", "metal"},
    ),
    "glass_holder": Holder(
        id="glass_holder",
        label="glass holder",
        phrase="a glass holder wrapped in blue string",
        fits={"dawnreed"},
        tags={"holder", "glass"},
    ),
    "leather_holder": Holder(
        id="leather_holder",
        label="leather holder",
        phrase="a leather holder stitched with tiny stars",
        fits={"stillstone", "dawnreed"},
        tags={"holder", "leather"},
    ),
}

COMPANIONS = {
    "fox": Companion(
        id="fox",
        label="fox",
        phrase="a mossy little fox named Pip",
        type="animal",
        support=1,
        cue='Pip tapped the holder with one soft paw, as if to say, "You already know the way."',
        ending="Pip trotted in a proud little circle beside the glowing stones",
        tags={"animal", "fox"},
    ),
    "owl": Companion(
        id="owl",
        label="owl",
        phrase="a small moon owl named Fern",
        type="animal",
        support=2,
        cue='Fern dipped low in the air and gave one wise hoot that sounded very much like "Remember."',
        ending="Fern settled overhead and blinked at the new light as if guarding it",
        tags={"animal", "owl"},
    ),
    "beetle": Companion(
        id="beetle",
        label="beetle",
        phrase="a lantern beetle called Button",
        type="animal",
        support=1,
        cue='Button climbed onto the holder and glowed a little brighter, nudging the moment toward courage.',
        ending="Button traced bright green loops in the air like tiny cheers",
        tags={"animal", "beetle"},
    ),
}

MENTORS = {
    "grandma": MentorCfg(
        id="grandma",
        name="Grandma Iri",
        type="woman",
        title="grandma",
        teaching="Magic must be carried kindly, in the right holder, and spoken to without hurry.",
        tags={"mentor", "family"},
    ),
    "mapmaker": MentorCfg(
        id="mapmaker",
        name="Master Sen",
        type="man",
        title="mapmaker",
        teaching="Every path listens before it opens. Hold the charm steady, then speak the true word.",
        tags={"mentor", "teacher"},
    ),
    "aunt": MentorCfg(
        id="aunt",
        name="Aunt Vale",
        type="woman",
        title="aunt",
        teaching="Do not wrestle with wild magic. Ask it to cease, and give it a safe place to rest.",
        tags={"mentor", "family"},
    ),
}

TRAITS = {
    "bold": Trait(
        id="bold",
        word="bold",
        nerve=2,
        flavor="strode forward quickly",
        tags={"brave"},
    ),
    "careful": Trait(
        id="careful",
        word="careful",
        nerve=1,
        flavor="looked hard before each step",
        tags={"thoughtful"},
    ),
    "dreamy": Trait(
        id="dreamy",
        word="dreamy",
        nerve=1,
        flavor="noticed every shining thing",
        tags={"imaginative"},
    ),
    "timid": Trait(
        id="timid",
        word="timid",
        nerve=0,
        flavor="liked adventures best once they felt safe",
        tags={"fear"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tess", "Nora", "Asha", "Ivy", "Ruby", "Etta"]
BOY_NAMES = ["Finn", "Leo", "Milo", "Theo", "Oren", "Jules", "Eli", "Pax"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short memory that shows something from earlier. It helps explain why a character understands what to do now."
        )
    ],
    "holder": [
        (
            "What is a holder?",
            "A holder is something made to carry or keep another thing safely inside it. In this story world, the holder keeps the magic charm safe and ready to use."
        )
    ],
    "magic": [
        (
            "Why do magical stories still need rules?",
            "Rules make the magic feel real inside the story. When magic has limits, the brave choice matters more."
        )
    ],
    "fog": [
        (
            "What is fog?",
            "Fog is a cloud close to the ground. It makes it hard to see where you are going."
        )
    ],
    "wind": [
        (
            "What can strong wind do on a path?",
            "Strong wind can push at your body and make walking hard. It can also blow dust and small stones around."
        )
    ],
    "shadow": [
        (
            "Why can a dark path feel scary?",
            "When you cannot see clearly, your brain is not sure what comes next. That is why shadows can make a path feel spooky even before anything bad happens."
        )
    ],
    "owl": [
        (
            "Why might an owl fit a night adventure story?",
            "Owls can see well in dim light and move quietly. That makes them feel wise and magical in many stories."
        )
    ],
    "fox": [
        (
            "What makes a fox feel adventurous in a story?",
            "A fox often seems quick, alert, and clever. Those traits make it a lively companion for a journey."
        )
    ],
    "beetle": [
        (
            "How can a glowing beetle help in a story?",
            "A glowing beetle can give a little light and a little hope. Even a small helper can make a big moment feel less lonely."
        )
    ],
}
KNOWLEDGE_ORDER = ["flashback", "holder", "magic", "fog", "wind", "shadow", "owl", "fox", "beetle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    route = f["route"]
    obstacle = f["obstacle_cfg"]
    charm = f["charm_cfg"]
    holder = f["holder_cfg"]
    companion = f["companion_cfg"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "cease" and "holder", uses a flashback, and ends safely.',
        f"Tell a magical adventure where {hero.id} carries {charm.phrase} in {holder.phrase}, meets {obstacle.phrase} on the way through {route.place}, and remembers an earlier lesson at the right moment.",
        f"Write a gentle quest story with {companion.phrase}, a living obstacle, and a calm magic spell that helps the danger cease instead of getting fought."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    route = f["route"]
    obstacle = f["obstacle_cfg"]
    charm = f["charm_cfg"]
    holder = f["holder_cfg"]
    companion = f["companion_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little adventurer carrying {charm.phrase} in {holder.phrase}. {companion.phrase} travels along too."
        ),
        (
            "What was the quest?",
            f"{hero.id} was taking the charm to {route.destination}. The journey mattered because the magic belonged there, not hidden in a pocket forever."
        ),
        (
            f"What blocked {hero.id} on the path?",
            f"{obstacle.phrase} blocked the way. It turned the path into a place of doubt, so {hero.id} had to stop and think instead of hurrying ahead."
        ),
        (
            "What happened in the flashback?",
            f"{hero.id} remembered {mentor.id} teaching that magic should be carried in the right holder and spoken to calmly. That memory changed the next choice, because it reminded {hero.pronoun('object')} to use the charm carefully instead of panicking."
        ),
        (
            f"Why did the word 'cease' matter?",
            f"It was part of the spell that asked the obstacle to calm down. The magic worked because {hero.id} used the matching charm in the proper holder and spoke the true words at the right moment."
        ),
    ]
    if outcome == "shaky":
        qa.append((
            f"Did {hero.id} feel brave right away?",
            f"No. {hero.id} wobbled and stepped back first because the obstacle felt big and strange. Then {companion.label} and the remembered lesson helped {hero.pronoun('object')} steady {hero.pronoun('possessive')} heart."
        ))
    else:
        qa.append((
            f"How did {hero.id} act when the obstacle appeared?",
            f"{hero.id} felt the danger but stayed in place and kept hold of the holder. That steady moment made it possible to remember the lesson and use the magic well."
        ))
    qa.append((
        "How did the story end?",
        f"The path opened, and {hero.id} reached {route.destination} to return the charm. The ending image shows a changed world: the danger is quiet, the magic is home, and the child walks back braver than before."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"flashback", "holder", "magic"}
    obstacle = f["obstacle_cfg"]
    companion = f["companion_cfg"]
    if obstacle.id == "fog_veil":
        tags.add("fog")
    if obstacle.id == "wind_wall":
        tags.add("wind")
    if obstacle.id == "shadow_pool":
        tags.add("shadow")
    tags.add(companion.id)
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != 0}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    route: str
    obstacle: str
    charm: str
    holder: str
    companion: str
    mentor: str
    trait: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        route="moonwood",
        obstacle="fog_veil",
        charm="sunmote",
        holder="brass_holder",
        companion="fox",
        mentor="grandma",
        trait="careful",
        hero_name="Mira",
        hero_type="girl",
    ),
    StoryParams(
        route="cliff_path",
        obstacle="wind_wall",
        charm="stillstone",
        holder="leather_holder",
        companion="owl",
        mentor="mapmaker",
        trait="bold",
        hero_name="Theo",
        hero_type="boy",
    ),
    StoryParams(
        route="reed_marsh",
        obstacle="shadow_pool",
        charm="dawnreed",
        holder="glass_holder",
        companion="beetle",
        mentor="aunt",
        trait="timid",
        hero_name="Lina",
        hero_type="girl",
    ),
    StoryParams(
        route="cliff_path",
        obstacle="wind_wall",
        charm="stillstone",
        holder="brass_holder",
        companion="fox",
        mentor="grandma",
        trait="timid",
        hero_name="Finn",
        hero_type="boy",
    ),
]


def explain_rejection(route_id: str, obstacle_id: str, charm_id: str, holder_id: str) -> str:
    bits = []
    if route_id in ROUTES and obstacle_id in OBSTACLES and obstacle_id not in ROUTES[route_id].affords:
        bits.append(f"{ROUTES[route_id].place} does not contain {OBSTACLES[obstacle_id].phrase}")
    if charm_id in CHARMS and obstacle_id in OBSTACLES and not charm_solves(CHARMS[charm_id], OBSTACLES[obstacle_id]):
        bits.append(f"{CHARMS[charm_id].label} cannot calm {OBSTACLES[obstacle_id].label}")
    if holder_id in HOLDERS and charm_id in CHARMS and not holder_fits(HOLDERS[holder_id], CHARMS[charm_id]):
        bits.append(f"{HOLDERS[holder_id].label} cannot safely carry {CHARMS[charm_id].label}")
    if bits:
        return "(No story: " + "; ".join(bits) + ".)"
    return "(No story: this combination is not part of the world's reasonable quest logic.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(R,O,C,H) :- route(R), obstacle(O), charm(C), holder(H),
                  affords(R,O), calms(C,O), fits(H,C).

score(S) :- chosen_trait(T), trait_nerve(T,N),
            chosen_companion(C), support(C,P),
            S = N + P.
steady_need(V) :- chosen_obstacle(O), threat(O,T), V = T + 1.

outcome(steady) :- score(S), steady_need(V), S >= V.
outcome(shaky)  :- score(S), steady_need(V), S < V.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        for obstacle_id in sorted(route.affords):
            lines.append(asp.fact("affords", route_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("threat", obstacle_id, obstacle.threat))
    for charm_id, charm in CHARMS.items():
        lines.append(asp.fact("charm", charm_id))
        lines.append(asp.fact("calms", charm_id, charm.solves))
    for holder_id, holder in HOLDERS.items():
        lines.append(asp.fact("holder", holder_id))
        for charm_id in sorted(holder.fits):
            lines.append(asp.fact("fits", holder_id, charm_id))
    for companion_id, companion in COMPANIONS.items():
        lines.append(asp.fact("companion", companion_id))
        lines.append(asp.fact("support", companion_id, companion.support))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("trait_nerve", trait_id, trait.nerve))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_companion", params.companion),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story from generate()")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a magical obstacle, a flashback, and a fitting holder."
    )
    ap.add_argument("--route", choices=sorted(ROUTES))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--charm", choices=sorted(CHARMS))
    ap.add_argument("--holder", choices=sorted(HOLDERS))
    ap.add_argument("--companion", choices=sorted(COMPANIONS))
    ap.add_argument("--mentor", choices=sorted(MENTORS))
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
    ap.add_argument("--hero-name", dest="hero_name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible route/obstacle/charm/holder combos")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.obstacle and args.charm and args.holder:
        if (args.route, args.obstacle, args.charm, args.holder) not in set(valid_combos()):
            raise StoryError(explain_rejection(args.route, args.obstacle, args.charm, args.holder))

    combos = [
        combo for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.charm is None or combo[2] == args.charm)
        and (args.holder is None or combo[3] == args.holder)
    ]
    if not combos:
        route_id = args.route or next(iter(ROUTES))
        obstacle_id = args.obstacle or next(iter(OBSTACLES))
        charm_id = args.charm or next(iter(CHARMS))
        holder_id = args.holder or next(iter(HOLDERS))
        raise StoryError(explain_rejection(route_id, obstacle_id, charm_id, holder_id))

    route_id, obstacle_id, charm_id, holder_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    companion_id = args.companion or rng.choice(sorted(COMPANIONS))
    mentor_id = args.mentor or rng.choice(sorted(MENTORS))
    trait_id = args.trait or rng.choice(sorted(TRAITS))
    return StoryParams(
        route=route_id,
        obstacle=obstacle_id,
        charm=charm_id,
        holder=holder_id,
        companion=companion_id,
        mentor=mentor_id,
        trait=trait_id,
        hero_name=hero_name,
        hero_type=hero_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        route = ROUTES[params.route]
        obstacle = OBSTACLES[params.obstacle]
        charm = CHARMS[params.charm]
        holder = HOLDERS[params.holder]
        companion = COMPANIONS[params.companion]
        mentor = MENTORS[params.mentor]
        trait = TRAITS[params.trait]
    except KeyError as err:
        raise StoryError(f"(No story: unknown option {err}.)") from None

    if (params.route, params.obstacle, params.charm, params.holder) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.route, params.obstacle, params.charm, params.holder))

    world = tell(
        route=route,
        obstacle_cfg=obstacle,
        charm_cfg=charm,
        holder_cfg=holder,
        companion_cfg=companion,
        mentor_cfg=mentor,
        trait_cfg=trait,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, obstacle, charm, holder) combos:\n")
        for route_id, obstacle_id, charm_id, holder_id in combos:
            print(f"  {route_id:10} {obstacle_id:12} {charm_id:10} {holder_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
                f"### {p.hero_name}: {p.route} / {p.obstacle} / {p.charm} in {p.holder} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
