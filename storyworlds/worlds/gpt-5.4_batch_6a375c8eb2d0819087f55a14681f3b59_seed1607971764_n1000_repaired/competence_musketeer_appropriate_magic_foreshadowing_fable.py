#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/competence_musketeer_appropriate_magic_foreshadowing_fable.py
==========================================================================================

A standalone story world for a small fable-like domain: a young animal longs to
be called a musketeer, but must learn that real competence means choosing the
appropriate enchanted tool for a modest errand.

The domain is built around three linked ideas:

- a mentor gives a tiny gate-errand,
- a bit of foreshadowing honestly warns what trouble is coming,
- a magical tool helps only when it is the appropriate one for that trouble.

The story can end in two child-facing ways:
- a smooth success, when the hero heeds the omen and prepares carefully;
- a gentle retry, when the hero rushes, makes a small mistake, learns, and then
  succeeds.

Run it
------
    python storyworlds/worlds/gpt-5.4/competence_musketeer_appropriate_magic_foreshadowing_fable.py
    python storyworlds/worlds/gpt-5.4/competence_musketeer_appropriate_magic_foreshadowing_fable.py --route bridge --cargo soup --tool sling
    python storyworlds/worlds/gpt-5.4/competence_musketeer_appropriate_magic_foreshadowing_fable.py --tool plume_foil
    python storyworlds/worlds/gpt-5.4/competence_musketeer_appropriate_magic_foreshadowing_fable.py --all
    python storyworlds/worlds/gpt-5.4/competence_musketeer_appropriate_magic_foreshadowing_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/competence_musketeer_appropriate_magic_foreshadowing_fable.py --verify
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
        female = {"girl", "mother", "hen", "goose", "vixen"}
        male = {"boy", "father", "fox", "badger", "mouse"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Route:
    id: str
    label: str
    phrase: str
    hazard: str
    omen: str
    foreshadow: str
    hazard_text: str
    safe_arrival: str
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
class Cargo:
    id: str
    label: str
    phrase: str
    sensitive_to: str
    damage: str
    purpose: str
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
class Tool:
    id: str
    label: str
    phrase: str
    guard: str
    magic: str
    action: str
    sensible: bool = True
    flashy: bool = False
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
class MentorKind:
    id: str
    type: str
    title: str
    manner: str
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


def _r_guard(world: World) -> list[str]:
    route = world.get("route")
    tool = world.get("tool")
    cargo = world.get("cargo")
    hero = world.get("hero")
    if route.meters["crossing"] < THRESHOLD:
        return []
    if tool.meters["readied"] < THRESHOLD:
        return []
    if tool.attrs.get("guard") != route.attrs.get("hazard"):
        return []
    sig = ("guard", route.id, tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["shielded"] += 1
    tool.meters["sparked"] += 1
    hero.meters["competence"] += 1
    return ["__guard__"]


def _r_damage(world: World) -> list[str]:
    route = world.get("route")
    cargo = world.get("cargo")
    hero = world.get("hero")
    if route.meters["crossing"] < THRESHOLD:
        return []
    if cargo.meters["shielded"] >= THRESHOLD:
        return []
    sig = ("damage", route.id, cargo.id, int(route.meters["crossing"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["damaged"] += 1
    hero.memes["fear"] += 1
    hero.memes["humility"] += 1
    return ["__damage__"]


def _r_deliver(world: World) -> list[str]:
    route = world.get("route")
    cargo = world.get("cargo")
    hero = world.get("hero")
    if route.meters["crossing"] < THRESHOLD:
        return []
    if cargo.meters["damaged"] >= THRESHOLD:
        return []
    sig = ("deliver", route.id, cargo.id, int(route.meters["crossing"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["delivered"] += 1
    hero.memes["relief"] += 1
    return ["__deliver__"]


CAUSAL_RULES = [
    Rule(name="guard", tag="physical", apply=_r_guard),
    Rule(name="damage", tag="physical", apply=_r_damage),
    Rule(name="deliver", tag="social", apply=_r_deliver),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def cargo_matches_route(cargo: Cargo, route: Route) -> bool:
    return cargo.sensitive_to == route.hazard


def tool_matches_route(tool: Tool, route: Route) -> bool:
    return tool.sensible and tool.guard == route.hazard


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for route_id, route in ROUTES.items():
        for cargo_id, cargo in CARGOS.items():
            for tool_id, tool in TOOLS.items():
                if cargo_matches_route(cargo, route) and tool_matches_route(tool, route):
                    combos.append((route_id, cargo_id, tool_id))
    return combos


def predict_crossing(world: World, heed: bool) -> dict:
    sim = world.copy()
    route = sim.get("route")
    tool = sim.get("tool")
    cargo = sim.get("cargo")
    route.meters["crossing"] += 1
    if heed:
        tool.meters["readied"] += 1
    propagate(sim, narrate=False)
    return {
        "shielded": cargo.meters["shielded"] >= THRESHOLD,
        "damaged": cargo.meters["damaged"] >= THRESHOLD,
        "delivered": cargo.meters["delivered"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, mentor: Entity, cargo: Cargo) -> None:
    hero.memes["ambition"] += 1
    world.say(
        f"In a small walled valley, {hero.id} longed to be a musketeer of the gate. "
        f"{hero.pronoun().capitalize()} practiced bows with a twig and dreamed of blue plumes."
    )
    world.say(
        f"At the gate stood {mentor.id}, {mentor.attrs['title']}, who watched with "
        f"{mentor.attrs['manner']} eyes and cared more for competence than for glitter."
    )
    world.say(
        f"That morning {mentor.id} offered {hero.id} a humble test: carry {cargo.phrase} "
        f"{cargo.purpose}."
    )


def foreshadow(world: World, hero: Entity, mentor: Entity, route: Route, tool: Tool) -> None:
    world.facts["omen_seen"] = route.omen
    world.say(
        f"Before they set out, {route.foreshadow}. {mentor.id} listened a moment and said, "
        f'"A road gives a little warning before it gives a big trouble."'
    )
    world.say(
        f'{mentor.id} lifted {tool.phrase}. "{tool.magic}. Choose what is appropriate, '
        f'and the road will teach you kindly."'
    )
    world.say(
        f"{hero.id} nodded, though the bright word musketeer still rang in "
        f"{hero.pronoun('possessive')} ears louder than the quiet advice."
    )


def temptation(world: World, hero: Entity) -> None:
    hero.memes["vanity"] += 1
    world.say(
        f"By the peg rail hung a feathered foil for parade days, shiny and useless. "
        f"For one heartbeat {hero.id} imagined that a grand pose might look like wisdom."
    )


def prepare(world: World, hero: Entity, tool: Entity, route: Route, heed: bool) -> None:
    if heed:
        hero.meters["care"] += 1
        tool.meters["readied"] += 1
        hero.memes["attention"] += 1
        world.say(
            f"But {hero.id} remembered the omen. {hero.pronoun().capitalize()} checked "
            f"{tool.label}, spoke the little charm exactly as taught, and stepped toward {route.phrase}."
        )
    else:
        hero.meters["haste"] += 1
        world.say(
            f"But haste pulled at {hero.id}'s heels. {hero.pronoun().capitalize()} snatched "
            f"{tool.label} and hurried toward {route.phrase} without giving the charm its full breath."
        )


def first_crossing(world: World, hero: Entity, route: Entity, cargo: Entity, heed: bool) -> None:
    route.meters["crossing"] += 1
    propagate(world, narrate=False)
    if cargo.meters["shielded"] >= THRESHOLD and cargo.meters["delivered"] >= THRESHOLD:
        world.say(
            f"On {route.label}, {route.attrs['hazard_text']}, but the magic answered at once. "
            f"{world.get('tool').attrs['action']}."
        )
        world.say(route.attrs["safe_arrival"])
        return
    world.say(
        f"On {route.label}, {route.attrs['hazard_text']}, and {cargo.attrs['damage_text']}."
    )
    world.say(
        f"{hero.id} stopped with hot cheeks. The errand was small, yet the lesson in it felt large."
    )


def return_and_retry(world: World, hero: Entity, mentor: Entity, route: Entity, cargo: Entity, tool: Entity) -> None:
    world.say(
        f"{hero.id} carried the spoiled load back to the gate and bowed low. "
        f'"I wanted the name of musketeer before I had earned the competence for it," '
        f'{hero.pronoun()} admitted.'
    )
    mentor.memes["kindness"] += 1
    world.say(
        f'{mentor.id} did not scold. "{tool.attrs["magic"]}. Appropriate care is a quieter kind of courage," '
        f'{mentor.pronoun()} said.'
    )
    cargo.meters["damaged"] = 0.0
    cargo.meters["shielded"] = 0.0
    cargo.meters["delivered"] = 0.0
    tool.meters["readied"] = 1.0
    route.meters["crossing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"This time {hero.id} slowed down, spoke the charm carefully, and tried {route.label} again. "
        f"{tool.attrs['action']}. {route.attrs['safe_arrival']}"
    )
    hero.meters["competence"] += 1
    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1


def ending(world: World, hero: Entity, mentor: Entity, cargo: Entity) -> None:
    hero.memes["humility"] += 1
    world.say(
        f"When {hero.id} handed over {cargo.label}, {mentor.id} pinned a plain blue thread on "
        f"{hero.pronoun('possessive')} vest instead of a jeweled plume."
    )
    world.say(
        f'"A true musketeer begins with what is appropriate," {mentor.id} said. '
        f'"Fine feathers may wait. Competence should go first."'
    )
    world.say(
        f"So {hero.id} walked home straighter than before, prouder of a careful errand well done "
        f"than of any bright costume, and the valley children remembered the sight."
    )


def tell(
    route_cfg: Route,
    cargo_cfg: Cargo,
    tool_cfg: Tool,
    mentor_cfg: MentorKind,
    hero_name: str = "Pip",
    hero_type: str = "mouse",
    heed_omen: bool = True,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        attrs={},
    ))
    mentor = world.add(Entity(
        id=mentor_cfg.title,
        kind="character",
        type=mentor_cfg.type,
        label=mentor_cfg.title,
        role="mentor",
        attrs={"title": mentor_cfg.title, "manner": mentor_cfg.manner},
    ))
    route = world.add(Entity(
        id="route",
        type="route",
        label=route_cfg.label,
        attrs={
            "hazard": route_cfg.hazard,
            "hazard_text": route_cfg.hazard_text,
            "safe_arrival": route_cfg.safe_arrival,
        },
    ))
    cargo = world.add(Entity(
        id="cargo",
        type="cargo",
        label=cargo_cfg.label,
        attrs={"damage_text": cargo_cfg.damage},
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=tool_cfg.label,
        attrs={"guard": tool_cfg.guard, "magic": tool_cfg.magic, "action": tool_cfg.action},
    ))

    world.facts.update(
        route_cfg=route_cfg,
        cargo_cfg=cargo_cfg,
        tool_cfg=tool_cfg,
        mentor_cfg=mentor_cfg,
        heed_omen=heed_omen,
        hero=hero,
        mentor=mentor,
        route=route,
        cargo=cargo,
        tool=tool,
        omen_seen=route_cfg.omen,
        first_attempt_damaged=False,
        outcome="smooth",
    )

    introduce(world, hero, mentor, cargo_cfg)
    world.para()
    foreshadow(world, hero, mentor, route_cfg, tool_cfg)
    temptation(world, hero)
    prepare(world, hero, tool, route_cfg, heed_omen=heed_omen)

    world.para()
    first_crossing(world, hero, route, cargo, heed_omen=heed_omen)

    if cargo.meters["damaged"] >= THRESHOLD:
        world.facts["first_attempt_damaged"] = True
        world.facts["outcome"] = "retry"
        world.para()
        return_and_retry(world, hero, mentor, route, cargo, tool)
    else:
        world.facts["outcome"] = "smooth"

    world.para()
    ending(world, hero, mentor, cargo)
    world.facts["delivered"] = cargo.meters["delivered"] >= THRESHOLD
    return world


ROUTES = {
    "bridge": Route(
        id="bridge",
        label="the mill bridge",
        phrase="the mill bridge",
        hazard="wind",
        omen="the reeds by the stream hissed like tiny trumpets",
        foreshadow="the reeds by the stream hissed like tiny trumpets, and the weathercock twitched toward the mill",
        hazard_text="a sharp wind came racing between the rails",
        safe_arrival="The load stayed steady, and the gatekeeper on the far side received it with a smile.",
        tags={"wind", "foreshadowing"},
    ),
    "lane": Route(
        id="lane",
        label="the cabbage lane",
        phrase="the cabbage lane",
        hazard="rain",
        omen="gray clouds stitched themselves over the sun",
        foreshadow="gray clouds stitched themselves over the sun, and the crows tucked their beaks under damp wings",
        hazard_text="rain pattered down in a sudden silver curtain",
        safe_arrival="The parcel stayed dry, and the farmer at the far hedge clapped softly in thanks.",
        tags={"rain", "foreshadowing"},
    ),
    "grove": Route(
        id="grove",
        label="the root-dark grove",
        phrase="the root-dark grove",
        hazard="dark",
        omen="the fireflies hid early among the fern stems",
        foreshadow="the fireflies hid early among the fern stems, and the old roots looked like sleeping snakes",
        hazard_text="the path turned so dim that every stone tried to become a shadow",
        safe_arrival="The way shone clear enough for careful feet, and the old healer at the stump door welcomed the bundle.",
        tags={"dark", "foreshadowing"},
    ),
}

CARGOS = {
    "soup": Cargo(
        id="soup",
        label="the rosemary soup",
        phrase="a warm pot of rosemary soup",
        sensitive_to="wind",
        damage="the soup sloshed against the lid and splashed over the rim",
        purpose="to the watchmouse on the far post",
        tags={"soup", "wind"},
    ),
    "seeds": Cargo(
        id="seeds",
        label="the bean seeds",
        phrase="a paper packet of bean seeds",
        sensitive_to="rain",
        damage="the paper packet softened, sagged, and spotted with wet",
        purpose="to the farmer beyond the hedge",
        tags={"seeds", "rain"},
    ),
    "ribbon": Cargo(
        id="ribbon",
        label="the silver ribbon roll",
        phrase="a roll of silver ribbon for the healer's bandages",
        sensitive_to="dark",
        damage="the ribbon slipped from uncertain paws and tumbled into the moss",
        purpose="to the healer under the old stump",
        tags={"ribbon", "dark"},
    ),
}

TOOLS = {
    "sling": Tool(
        id="sling",
        label="the lidded sling",
        phrase="a lidded sling of willow cord",
        guard="wind",
        magic="Tie me straight and I remember how not to sway",
        action="The willow cords tightened and held the burden close to the chest",
        sensible=True,
        flashy=False,
        tags={"magic", "appropriate", "wind"},
    ),
    "satchel": Tool(
        id="satchel",
        label="the waxed satchel",
        phrase="a waxed satchel with a brass clasp",
        guard="rain",
        magic="Fasten me well and I keep dry secrets",
        action="The satchel beaded the rain into round pearls that rolled harmlessly away",
        sensible=True,
        flashy=False,
        tags={"magic", "appropriate", "rain"},
    ),
    "lantern": Tool(
        id="lantern",
        label="the firefly lantern",
        phrase="a firefly lantern no bigger than an apple",
        guard="dark",
        magic="Lift me level and I lend my borrowed stars",
        action="The lantern glowed softly, and each root laid down its shadow where it belonged",
        sensible=True,
        flashy=False,
        tags={"magic", "appropriate", "dark"},
    ),
    "plume_foil": Tool(
        id="plume_foil",
        label="the feathered foil",
        phrase="a feathered foil for parade bows",
        guard="show",
        magic="Wave me high and everyone will look at you",
        action="It flashed prettily and helped nothing at all",
        sensible=False,
        flashy=True,
        tags={"musketeer", "flashy"},
    ),
}

MENTORS = {
    "badger": MentorKind(
        id="badger",
        type="badger",
        title="Captain Bramble",
        manner="steady",
        tags={"mentor"},
    ),
    "goose": MentorKind(
        id="goose",
        type="goose",
        title="Dame Quill",
        manner="bright",
        tags={"mentor"},
    ),
    "fox": MentorKind(
        id="fox",
        type="fox",
        title="Master Sable",
        manner="patient",
        tags={"mentor"},
    ),
}

HEROES = {
    "mouse": ["Pip", "Nim", "Tilo", "Moss"],
    "hen": ["Dot", "Wren", "Poppy", "Merry"],
    "vixen": ["Fern", "Lark", "Bramble", "Nia"],
}


@dataclass
class StoryParams:
    route: str
    cargo: str
    tool: str
    mentor: str
    hero_type: str
    hero_name: str
    heed_omen: bool = True
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
    "musketeer": [(
        "What is a musketeer in this kind of fable?",
        "In this story, a musketeer is a brave guard or messenger who serves with discipline. The title matters less than being careful and trustworthy."
    )],
    "competence": [(
        "What does competence mean?",
        "Competence means being able to do a job well because you have learned how. It shows in careful actions, not just in proud words."
    )],
    "appropriate": [(
        "What does appropriate mean?",
        "Appropriate means right for the situation. An appropriate tool fits the problem instead of only looking impressive."
    )],
    "magic": [(
        "How can magic be helpful in a fable?",
        "Magic can help when it is used wisely and with care. In a fable, it often rewards attention and good judgment rather than showing off."
    )],
    "foreshadowing": [(
        "What is foreshadowing?",
        "Foreshadowing is a small hint that tells you something important may happen later. It helps a reader notice danger before the trouble arrives."
    )],
    "wind": [(
        "Why can wind make carrying soup hard?",
        "Wind can jolt your arms and tip a pot from side to side. Even a small gust can make soup slosh and spill."
    )],
    "rain": [(
        "Why is rain bad for paper packets?",
        "Paper grows soft and weak when it gets wet. Then the packet can sag or tear and stop protecting what is inside."
    )],
    "dark": [(
        "Why is darkness difficult on a path?",
        "Darkness makes it hard to see roots, stones, and turns in the road. When you cannot see clearly, it is easier to drop or lose what you carry."
    )],
}
KNOWLEDGE_ORDER = ["musketeer", "competence", "appropriate", "magic", "foreshadowing", "wind", "rain", "dark"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    route = f["route_cfg"]
    cargo = f["cargo_cfg"]
    tool = f["tool_cfg"]
    if f["outcome"] == "smooth":
        return [
            f'Write a short fable about a young animal who wants to be a musketeer and must prove competence with a small errand.',
            f'Include Magic and Foreshadowing in a child-facing story where {hero.id} notices an omen on {route.label} and uses {tool.label} in the appropriate way.',
            f'Write a gentle moral tale that includes the words "competence", "musketeer", and "appropriate", and ends with {cargo.label} arriving safely.',
        ]
    return [
        f'Write a short fable about a young animal who wants to be a musketeer, rushes once, and learns competence through a second careful try.',
        f'Include Magic and Foreshadowing in a story where {hero.id} ignores a warning on {route.label}, then returns to use {tool.label} in the appropriate way.',
        f'Write a moral tale that includes the words "competence", "musketeer", and "appropriate", with a small mistake, a kind mentor, and a wiser ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    route = f["route_cfg"]
    cargo = f["cargo_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young {hero.type} who wants to be a musketeer of the gate, and {mentor.id}, the mentor who tests {hero.pronoun('object')} with a small errand."
        ),
        (
            "What warning came before the trouble?",
            f"The warning was the omen that {f['omen_seen']}. That foreshadowing hinted what kind of trouble would soon appear on {route.label}."
        ),
        (
            f"Why was {tool.label} the appropriate tool?",
            f"{tool.label.capitalize()} was made for {route.hazard}, which was the danger on {route.label}. It matched the problem instead of only looking grand, so it turned magic into useful help."
        ),
    ]
    if f["outcome"] == "smooth":
        qa.append((
            f"How did {hero.id} show competence?",
            f"{hero.id} showed competence by slowing down, using the charm as taught, and trusting the warning signs. Because {hero.pronoun()} prepared carefully, the magic worked and {cargo.label} arrived safely."
        ))
    else:
        qa.append((
            f"What happened when {hero.id} hurried the first time?",
            f"When {hero.id} hurried, {cargo.damage}. The mistake came from rushing past the warning instead of preparing the enchanted tool the right way."
        ))
        qa.append((
            f"How did the problem get solved?",
            f"{hero.id} went back, admitted the mistake, and listened to {mentor.id} again. On the second trip {hero.pronoun()} used the tool carefully, so the road became manageable and the errand was finished."
        ))
    qa.append((
        "What is the lesson at the end?",
        f"The story teaches that competence matters more than showy pride. A real musketeer chooses what is appropriate and handles even a small duty with care."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"musketeer", "competence", "appropriate", "magic", "foreshadowing", f["route_cfg"].hazard}
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        route="bridge",
        cargo="soup",
        tool="sling",
        mentor="badger",
        hero_type="mouse",
        hero_name="Pip",
        heed_omen=True,
    ),
    StoryParams(
        route="lane",
        cargo="seeds",
        tool="satchel",
        mentor="goose",
        hero_type="hen",
        hero_name="Wren",
        heed_omen=False,
    ),
    StoryParams(
        route="grove",
        cargo="ribbon",
        tool="lantern",
        mentor="fox",
        hero_type="vixen",
        hero_name="Fern",
        heed_omen=True,
    ),
    StoryParams(
        route="bridge",
        cargo="soup",
        tool="sling",
        mentor="fox",
        hero_type="mouse",
        hero_name="Moss",
        heed_omen=False,
    ),
]


def explain_rejection(route: Route, cargo: Cargo, tool: Tool) -> str:
    if not tool.sensible:
        return (
            f"(No story: {tool.label} is a flashy parade piece, not an appropriate working tool. "
            f"This fable refuses to pretend that showy gear proves competence.)"
        )
    if cargo.sensitive_to != route.hazard:
        return (
            f"(No story: {cargo.label} is threatened by {cargo.sensitive_to}, but {route.label} brings {route.hazard}. "
            f"The danger and the errand do not fit each other closely enough for this fable.)"
        )
    if tool.guard != route.hazard:
        return (
            f"(No story: {tool.label} is made for {tool.guard}, not for {route.hazard}. "
            f"The chosen tool is not appropriate to the road's trouble.)"
        )
    return "(No story: this combination is not reasonable in the world model.)"


def outcome_of(params: StoryParams) -> str:
    return "smooth" if params.heed_omen else "retry"


ASP_RULES = r"""
% Reasonable story triples: cargo must be vulnerable to the route's hazard, and
% the tool must sensibly guard that same hazard.
hazard_match(R,C) :- route(R), cargo(C), route_hazard(R,H), cargo_sensitive(C,H).
tool_match(R,T)   :- route(R), tool(T), sensible(T), route_hazard(R,H), tool_guard(T,H).
valid(R,C,T)      :- hazard_match(R,C), tool_match(R,T).

% Outcome model: if the omen is heeded, the first trip is smooth; if not, the
% story becomes a retry-and-learn fable.
outcome(smooth) :- heed.
outcome(retry)  :- not heed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("route_hazard", route_id, route.hazard))
    for cargo_id, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("cargo_sensitive", cargo_id, cargo.sensitive_to))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_guard", tool_id, tool.guard))
        if tool.sensible:
            lines.append(asp.fact("sensible", tool_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("heed") if params.heed_omen else ""
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if py_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - clingo_set:
            print("  only in python:", sorted(py_set - clingo_set))
        if clingo_set - py_set:
            print("  only in clingo:", sorted(clingo_set - py_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome disagreements.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable story world: a small animal learns that competence beats glitter."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--mentor", choices=MENTORS)
    ap.add_argument("--hero-type", choices=sorted(HEROES))
    ap.add_argument("--hero-name")
    ap.add_argument(
        "--heed-omen",
        choices=["yes", "no"],
        help="whether the hero slows down and follows the foreshadowed warning",
    )
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid route/cargo/tool triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.cargo and args.tool:
        route = ROUTES[args.route]
        cargo = CARGOS[args.cargo]
        tool = TOOLS[args.tool]
        if (args.route, args.cargo, args.tool) not in set(valid_combos()):
            raise StoryError(explain_rejection(route, cargo, tool))
    if args.tool and not TOOLS[args.tool].sensible:
        route = ROUTES[args.route] if args.route else next(iter(ROUTES.values()))
        cargo = CARGOS[args.cargo] if args.cargo else next(iter(CARGOS.values()))
        raise StoryError(explain_rejection(route, cargo, TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route_id, cargo_id, tool_id = rng.choice(sorted(combos))
    mentor = args.mentor or rng.choice(sorted(MENTORS))
    hero_type = args.hero_type or rng.choice(sorted(HEROES))
    hero_name = args.hero_name or rng.choice(HEROES[hero_type])
    heed_map = {"yes": True, "no": False}
    heed_omen = heed_map[args.heed_omen] if args.heed_omen is not None else rng.choice([True, False])

    return StoryParams(
        route=route_id,
        cargo=cargo_id,
        tool=tool_id,
        mentor=mentor,
        hero_type=hero_type,
        hero_name=hero_name,
        heed_omen=heed_omen,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.cargo not in CARGOS:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.mentor not in MENTORS:
        raise StoryError(f"(Unknown mentor: {params.mentor})")
    if params.hero_type not in HEROES:
        raise StoryError(f"(Unknown hero type: {params.hero_type})")
    if params.hero_name not in HEROES[params.hero_type]:
        raise StoryError(f"(Hero name {params.hero_name!r} does not fit hero type {params.hero_type!r} here.)")

    route = ROUTES[params.route]
    cargo = CARGOS[params.cargo]
    tool = TOOLS[params.tool]
    if (params.route, params.cargo, params.tool) not in set(valid_combos()):
        raise StoryError(explain_rejection(route, cargo, tool))

    world = tell(
        route_cfg=route,
        cargo_cfg=cargo,
        tool_cfg=tool,
        mentor_cfg=MENTORS[params.mentor],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        heed_omen=params.heed_omen,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, cargo, tool) combos:\n")
        for route, cargo, tool in combos:
            print(f"  {route:8} {cargo:8} {tool}")
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
            header = f"### {p.hero_name}: {p.route}/{p.cargo}/{p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
