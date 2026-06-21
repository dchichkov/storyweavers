#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/splatter_emphasize_pound_happy_ending_humor_quest.py
================================================================================

A standalone storyworld for a tiny adventure domain: a child is sent on a funny
little quest to carry an important object through a tricky place without
spoiling it. The world model enforces a common-sense constraint:

    a cargo is only a reasonable quest cargo for an obstacle when the obstacle's
    challenge actually threatens that kind of cargo, and there is a sensible
    tool that protects it.

So a sloshy stew pot belongs on bumpy paths, a feather crown belongs in gusty
places, and a tiny brass key belongs in dark places. The guide predicts the
mishap with the world model before the child charges ahead, then equips the
right tool and the quest ends happily.

Required story words appear naturally in the prose:
- splatter
- emphasize
- pound

Run it
------
    python storyworlds/worlds/gpt-5.4/splatter_emphasize_pound_happy_ending_humor_quest.py
    python storyworlds/worlds/gpt-5.4/splatter_emphasize_pound_happy_ending_humor_quest.py --cargo stew_pot --obstacle stepping_stones
    python storyworlds/worlds/gpt-5.4/splatter_emphasize_pound_happy_ending_humor_quest.py --cargo brass_key --obstacle windy_bridge   # rejected
    python storyworlds/worlds/gpt-5.4/splatter_emphasize_pound_happy_ending_humor_quest.py --all
    python storyworlds/worlds/gpt-5.4/splatter_emphasize_pound_happy_ending_humor_quest.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/splatter_emphasize_pound_happy_ending_humor_quest.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )


# ---------------------------------------------------------------------------
# Domain registries
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Obstacle:
    id: str
    label: str
    place: str
    challenge: str
    approach: str
    cross: str
    detail: str
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
class Cargo:
    id: str
    label: str
    phrase: str
    property: str
    mission: str
    destination: str
    keeper: str
    mishap_meter: str
    mishap_word: str
    rescue_line: str
    ending_line: str
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
    solves: str
    ready_line: str
    use_line: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World state and narration
# ---------------------------------------------------------------------------
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
        self.facts: dict = {
            "obstacle_started": False,
            "cargo_secured": False,
            "challenge": "",
            "mishap_meter": "",
            "mishap_word": "",
            "outcome": "",
            "companion_snack": "",
            "predicted_bad": False,
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_mishap(world: World) -> list[str]:
    if not world.facts["obstacle_started"]:
        return []
    if world.facts["cargo_secured"]:
        return []
    cargo = world.get("cargo")
    hero = world.get("hero")
    sig = ("mishap", cargo.id, world.facts["mishap_meter"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters[world.facts["mishap_meter"]] += 1
    cargo.meters["trouble"] += 1
    hero.memes["worry"] += 1
    return ["__mishap__"]


def _r_progress(world: World) -> list[str]:
    if not world.facts["obstacle_started"]:
        return []
    if not world.facts["cargo_secured"]:
        return []
    hero = world.get("hero")
    cargo = world.get("cargo")
    sig = ("progress", cargo.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["confidence"] += 1
    cargo.meters["safe"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="mishap", tag="physical", apply=_r_mishap),
    Rule(name="progress", tag="physical", apply=_r_progress),
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
                produced.extend(out)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraints and prediction
# ---------------------------------------------------------------------------
def cargo_at_risk(cargo: Cargo, obstacle: Obstacle) -> bool:
    return cargo.property == obstacle.challenge


def select_tool(cargo: Cargo, obstacle: Obstacle) -> Optional[Tool]:
    if not cargo_at_risk(cargo, obstacle):
        return None
    for tool in TOOLS.values():
        if tool.solves == obstacle.challenge:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for obstacle_id, obstacle in OBSTACLES.items():
        for cargo_id, cargo in CARGOS.items():
            tool = select_tool(cargo, obstacle)
            if tool is not None:
                combos.append((obstacle_id, cargo_id, tool.id))
    return sorted(combos)


def explain_rejection(cargo: Cargo, obstacle: Obstacle) -> str:
    if not cargo_at_risk(cargo, obstacle):
        return (
            f"(No story: {cargo.phrase} is threatened by {cargo.property}, but "
            f"{obstacle.label} is a {obstacle.challenge} obstacle. The danger would not "
            f"be honest, so this quest is rejected.)"
        )
    return (
        f"(No story: {obstacle.label} really does threaten {cargo.label}, but there is "
        f"no sensible tool in the catalog to solve that problem.)"
    )


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    sim.facts["obstacle_started"] = True
    propagate(sim, narrate=False)
    cargo = sim.get("cargo")
    meter = world.facts["mishap_meter"]
    return {
        "bad": cargo.meters[meter] >= THRESHOLD,
        "meter": meter,
        "word": world.facts["mishap_word"],
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, companion: Entity) -> None:
    hero.memes["bravery"] += 1
    companion.memes["mischief"] += 1
    world.say(
        f"{hero.id} loved any afternoon that sounded even a little bit like an expedition. "
        f"{companion.id}, {hero.pronoun('possessive')} cheerful sidekick, trotted along beside "
        f"{hero.pronoun('object')} with a grin that usually meant trouble."
    )


def assign_quest(world: World, guide: Entity, hero: Entity, cargo: Cargo) -> None:
    cargo_ent = world.get("cargo")
    cargo_ent.attrs["owner"] = guide.id
    hero.memes["pride"] += 1
    world.say(
        f"At the village gate, {guide.id} placed {cargo.phrase} into {hero.id}'s hands. "
        f'"This must reach {cargo.destination}," {guide.pronoun()} said. "{cargo.mission}"'
    )


def emphasize_map(world: World, guide: Entity, obstacle: Obstacle, cargo: Cargo) -> None:
    world.say(
        f"To emphasize how important the quest was, {guide.id} tapped a red circle on the map "
        f"right over {obstacle.place}. {guide.pronoun().capitalize()} warned that {obstacle.detail}."
    )


def set_off(world: World, hero: Entity, companion: Entity) -> None:
    snack = world.facts["companion_snack"]
    world.say(
        f"Off they went. {companion.id} promised to guard the map and {snack}, though "
        f"{hero.id} noticed that promise was already sticky around the edges."
    )


def approach_obstacle(world: World, hero: Entity, companion: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"Soon they reached {obstacle.place}, where {obstacle.detail}. "
        f'{hero.id} drew a quick breath. "There it is," {hero.pronoun()} said.'
    )
    world.say(
        f'{companion.id} tried to look heroic, but a tiny berry splatter landed on '
        f'{companion.pronoun("possessive")} nose and made {companion.pronoun("object")} blink cross-eyed.'
    )


def rush(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["impulse"] += 1
    world.say(
        f'"If I move fast, I can {obstacle.approach} and be done in a blink," {hero.id} said.'
    )


def warn(world: World, guide: Entity, hero: Entity, cargo: Cargo, obstacle: Obstacle) -> None:
    pred = predict_mishap(world)
    world.facts["predicted_bad"] = pred["bad"]
    hero.memes["caution"] += 1
    if pred["bad"]:
        world.say(
            f'{guide.id} shook {guide.pronoun("possessive")} head. "Not so fast. '
            f'If you charge through {obstacle.label}, the {cargo.label} could be {pred["word"]}. '
            f'This quest is supposed to end with cheering, not with gasps."'
        )
    else:
        world.say(
            f'{guide.id} studied the path and nodded. "That would be fine," {guide.pronoun()} said.'
        )


def equip(world: World, guide: Entity, hero: Entity, tool: Tool) -> None:
    cargo = world.get("cargo")
    tool_ent = world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            role="tool",
            attrs={"solves": tool.solves},
        )
    )
    tool_ent.attrs["used"] = True
    world.facts["cargo_secured"] = True
    cargo.attrs["secured_by"] = tool.id
    hero.memes["relief"] += 1
    world.say(
        f'{guide.id} handed over {tool.phrase}. "{tool.ready_line}" {guide.pronoun()} said.'
    )


def cross(world: World, hero: Entity, companion: Entity, obstacle: Obstacle, tool: Tool) -> None:
    world.facts["obstacle_started"] = True
    propagate(world, narrate=False)
    cargo = world.get("cargo")
    cargo.meters["carried"] += 1
    world.say(
        f"{hero.id} {tool.use_line} and {obstacle.cross}. {companion.id} followed, "
        f"trying very hard to march like a palace guard and mostly succeeding."
    )
    if cargo.meters["safe"] >= THRESHOLD:
        world.say(
            f"The {cargo.label} stayed safe, and that made {hero.id}'s steps feel lighter all at once."
        )


def arrive_and_pound(world: World, hero: Entity, cargo: Cargo) -> None:
    hero.memes["triumph"] += 1
    world.say(
        f"At last they reached {cargo.destination}. {hero.id} gave the door a brave pound, "
        f"and the sound bounced out into the evening like a tiny drumroll."
    )


def deliver(world: World, hero: Entity, companion: Entity, cargo: Cargo) -> None:
    cargo_ent = world.get("cargo")
    cargo_ent.meters["delivered"] += 1
    world.say(cargo.rescue_line)
    world.say(
        f"{cargo.keeper} laughed when {companion.id} tried to bow with jam still on "
        f'{companion.pronoun("possessive")} nose.'
    )


def celebrate(world: World, hero: Entity, guide: Entity, cargo: Cargo) -> None:
    hero.memes["joy"] += 1
    hero.memes["confidence"] += 1
    world.facts["outcome"] = "happy"
    world.say(
        f'Soon everyone was smiling. "{cargo.ending_line}" {guide.id} said, beaming at {hero.id}.'
    )
    world.say(
        f"{hero.id} stood a little taller on the walk home. The quest had begun with worry, "
        f"but it ended with laughter, safe hands, and a story worth telling again."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    *,
    obstacle: Obstacle,
    cargo: Cargo,
    tool: Tool,
    hero_name: str = "Nia",
    hero_gender: str = "girl",
    companion_name: str = "Pip",
    companion_gender: str = "boy",
    guide_type: str = "aunt",
    snack: str = "a jam bun",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    companion = world.add(
        Entity(id="companion", kind="character", type=companion_gender, label=companion_name, role="companion")
    )
    guide = world.add(Entity(id="guide", kind="character", type=guide_type, label="the guide", role="guide"))
    cargo_ent = world.add(
        Entity(
            id="cargo",
            kind="thing",
            type="cargo",
            label=cargo.label,
            role="cargo",
            attrs={"property": cargo.property, "secured_by": ""},
        )
    )

    hero.attrs["name"] = hero_name
    companion.attrs["name"] = companion_name
    guide.attrs["name"] = {"aunt": "Aunt Suri", "uncle": "Uncle Ren", "mother": "Mother Tala", "father": "Father Bo"}[
        guide_type
    ]
    world.facts["challenge"] = obstacle.challenge
    world.facts["mishap_meter"] = cargo.mishap_meter
    world.facts["mishap_word"] = cargo.mishap_word
    world.facts["companion_snack"] = snack

    introduce(world, hero, companion)
    assign_quest(world, guide, hero, cargo)
    emphasize_map(world, guide, obstacle, cargo)
    world.para()
    set_off(world, hero, companion)
    approach_obstacle(world, hero, companion, obstacle)
    rush(world, hero, obstacle)
    warn(world, guide, hero, cargo, obstacle)
    equip(world, guide, hero, tool)
    world.para()
    cross(world, hero, companion, obstacle, tool)
    arrive_and_pound(world, hero, cargo)
    deliver(world, hero, companion, cargo)
    celebrate(world, hero, guide, cargo)

    world.facts.update(
        hero=hero,
        companion=companion,
        guide=guide,
        obstacle=obstacle,
        cargo_cfg=cargo,
        cargo=cargo_ent,
        tool=tool,
        delivered=cargo_ent.meters["delivered"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
OBSTACLES = {
    "stepping_stones": Obstacle(
        id="stepping_stones",
        label="the stepping stones",
        place="the stepping stones over the brook",
        challenge="bumps",
        approach="skip from stone to stone",
        cross="picked a careful rhythm over the wet stones",
        detail="the stones bobbed your knees and made every carried thing wobble",
        tags={"brook", "bumps"},
    ),
    "spiral_stairs": Obstacle(
        id="spiral_stairs",
        label="the spiral stairs",
        place="the spiral stairs inside the watchtower hill",
        challenge="bumps",
        approach="bound up the stairs",
        cross="climbed the round stairs one steady step at a time",
        detail="each little thump up the stairs could jolt a load right out of line",
        tags={"stairs", "bumps"},
    ),
    "windy_bridge": Obstacle(
        id="windy_bridge",
        label="the windy bridge",
        place="the windy rope bridge",
        challenge="gusts",
        approach="dash across the planks",
        cross="leaned into the wind and crossed the swaying bridge",
        detail="gusts whistled between the ropes and loved to snatch light things away",
        tags={"bridge", "gusts"},
    ),
    "kite_hill": Obstacle(
        id="kite_hill",
        label="kite hill",
        place="kite hill above the market",
        challenge="gusts",
        approach="race straight over the ridge",
        cross="ducked low and crossed the hill under the tugging sky",
        detail="the hill caught every rude puff of wind the valley could throw",
        tags={"hill", "gusts"},
    ),
    "dark_tunnel": Obstacle(
        id="dark_tunnel",
        label="the dark tunnel",
        place="the dark tunnel under the old wall",
        challenge="gloom",
        approach="hurry through the dark",
        cross="walked through the tunnel with the shadows pushed politely back",
        detail="the tunnel swallowed shiny little objects as if it collected them for fun",
        tags={"tunnel", "gloom"},
    ),
    "echo_cave": Obstacle(
        id="echo_cave",
        label="echo cave",
        place="echo cave behind the mill",
        challenge="gloom",
        approach="rush into the cave",
        cross="moved through the cave while bright light skipped over the floor",
        detail="the cave was so dim that a small thing could vanish between one blink and the next",
        tags={"cave", "gloom"},
    ),
}

CARGOS = {
    "stew_pot": Cargo(
        id="stew_pot",
        label="stew pot",
        phrase="a warm pot of berry stew with a wobbling spoon",
        property="bumps",
        mission="The gate giant has waited all day for supper.",
        destination="the giant's gatehouse",
        keeper="The hungry gate giant",
        mishap_meter="splashed",
        mishap_word="splashed all over the path",
        rescue_line="The hungry gate giant lifted the lid, sniffed once, and sighed so happily that his mustache twitched.",
        ending_line="You carried supper like a real adventurer.",
        tags={"stew", "food"},
    ),
    "feather_crown": Cargo(
        id="feather_crown",
        label="feather crown",
        phrase="a ridiculous feather crown with blue streamers",
        property="gusts",
        mission="The parade goose refuses to march without it.",
        destination="the parade pen by the square",
        keeper="The parade goose",
        mishap_meter="blown",
        mishap_word="blown into the clouds",
        rescue_line="The parade goose accepted the crown with a royal honk and immediately looked pleased with the world.",
        ending_line="You saved the silliest parade in town.",
        tags={"crown", "parade"},
    ),
    "brass_key": Cargo(
        id="brass_key",
        label="brass key",
        phrase="a tiny brass key tied to a moon-shaped tag",
        property="gloom",
        mission="The clock tower door cannot be opened without it.",
        destination="the moon clock tower",
        keeper="The clock keeper",
        mishap_meter="lost",
        mishap_word="lost in the dark",
        rescue_line="The clock keeper turned the little key, and the tower bells answered with bright, happy notes.",
        ending_line="You brought the evening back on time.",
        tags={"key", "tower"},
    ),
}

TOOLS = {
    "tray": Tool(
        id="tray",
        label="tray",
        phrase="a flat brass tray with little raised edges",
        solves="bumps",
        ready_line="Keep it level and let the tray do the steadying.",
        use_line="balanced the cargo on the tray",
        qa_text="used a tray to keep the cargo level over the bumps",
        tags={"tray"},
    ),
    "ribbon": Tool(
        id="ribbon",
        label="ribbon",
        phrase="a bright ribbon to tie and anchor the cargo",
        solves="gusts",
        ready_line="Tie it snug, and the wind can brag all it likes.",
        use_line="tied the cargo down with the ribbon",
        qa_text="tied the cargo down with a ribbon so the wind could not snatch it",
        tags={"ribbon"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a small lantern with a golden hook",
        solves="gloom",
        ready_line="Hold the light low and let the path show itself.",
        use_line="lifted the lantern and kept the light near the ground",
        qa_text="used a lantern so the small cargo would not be lost in the dark",
        tags={"lantern"},
    ),
}

GIRL_NAMES = ["Nia", "Lila", "Mara", "Tess", "Ava", "Rina", "June", "Pia"]
BOY_NAMES = ["Pip", "Tomo", "Eli", "Ben", "Milo", "Otis", "Finn", "Rex"]
SNACKS = ["a jam bun", "a berry tart", "a sticky plum roll", "a little jelly cake"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    obstacle: str
    cargo: str
    tool: str
    hero_name: str
    hero_gender: str
    companion_name: str
    companion_gender: str
    guide_type: str
    snack: str = "a jam bun"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
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


KNOWLEDGE = {
    "bumps": [
        (
            "Why is it hard to carry a sloshy pot over bumpy ground?",
            "When the ground bumps your body up and down, the liquid inside the pot keeps moving too. That makes it wobble and splash unless you carry it very steadily.",
        )
    ],
    "gusts": [
        (
            "Why can the wind grab light things?",
            "Wind is moving air, and a strong gust can push or lift light things very quickly. That is why ribbons and ties help keep them in place.",
        )
    ],
    "gloom": [
        (
            "Why is a lantern useful in a dark place?",
            "A lantern makes light so your eyes can see the ground and the things in your hands. That keeps small objects from being dropped or lost in the dark.",
        )
    ],
    "tray": [
        (
            "What does a tray help you do?",
            "A tray gives a flat, steady surface under what you are carrying. Raised edges can help stop it from sliding when you walk carefully.",
        )
    ],
    "ribbon": [
        (
            "What can a ribbon do besides look pretty?",
            "A ribbon can tie something in place. If the wind is tugging, a good tie helps keep the object from flying away.",
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light you can carry with you. It helps people see safely when a place is dark.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a special trip with a goal. Someone sets out to do an important job and keeps going until the job is done.",
        )
    ],
}
KNOWLEDGE_ORDER = ["quest", "bumps", "gusts", "gloom", "tray", "ribbon", "lantern"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    cargo = world.facts["cargo_cfg"]
    obstacle = world.facts["obstacle"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old about a quest to carry {cargo.label} through {obstacle.label}. Include the words "splatter", "emphasize", and "pound".',
        f"Tell a funny quest where {hero.attrs['name']} wants to hurry, but a guide stops {hero.pronoun('object')} and helps {hero.pronoun('object')} carry something important the careful way.",
        f"Write a happy little adventure where a child crosses {obstacle.place} to deliver something important, and the ending proves the quest worked.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    guide = world.facts["guide"]
    cargo = world.facts["cargo_cfg"]
    obstacle = world.facts["obstacle"]
    tool = world.facts["tool"]
    out: list[tuple[str, str]] = [
        (
            "What was the quest?",
            f"{hero.attrs['name']} had to carry the {cargo.label} to {cargo.destination}. It mattered because {cargo.mission}",
        ),
        (
            f"Why did {guide.attrs['name']} warn {hero.attrs['name']} not to rush?",
            f"{guide.attrs['name']} knew that {obstacle.label} was dangerous for that kind of cargo. If {hero.attrs['name']} hurried without help, the {cargo.label} could be {cargo.mishap_word}.",
        ),
        (
            f"How did they solve the problem at {obstacle.place}?",
            f"They used {tool.phrase}. {tool.qa_text}, so the quest could continue without the cargo being ruined.",
        ),
        (
            "What made the story funny?",
            f"{companion.attrs['name']} kept trying to act grand and heroic, even with jam on {companion.pronoun('possessive')} nose. That tiny berry splatter made the serious quest feel silly in a good way.",
        ),
        (
            "How did the story end?",
            f"It ended happily because the {cargo.label} reached {cargo.destination} safely. Everyone laughed, and {hero.attrs['name']} came home feeling like a real adventurer.",
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    obstacle = world.facts["obstacle"]
    tool = world.facts["tool"]
    tags = {"quest", obstacle.challenge, tool.id}
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
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  facts={{{k: v for k, v in world.facts.items() if k not in {'hero', 'companion', 'guide', 'cargo_cfg', 'cargo', 'obstacle', 'tool'}}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        obstacle="stepping_stones",
        cargo="stew_pot",
        tool="tray",
        hero_name="Nia",
        hero_gender="girl",
        companion_name="Pip",
        companion_gender="boy",
        guide_type="aunt",
        snack="a jam bun",
    ),
    StoryParams(
        obstacle="windy_bridge",
        cargo="feather_crown",
        tool="ribbon",
        hero_name="Milo",
        hero_gender="boy",
        companion_name="June",
        companion_gender="girl",
        guide_type="uncle",
        snack="a berry tart",
    ),
    StoryParams(
        obstacle="dark_tunnel",
        cargo="brass_key",
        tool="lantern",
        hero_name="Lila",
        hero_gender="girl",
        companion_name="Otis",
        companion_gender="boy",
        guide_type="mother",
        snack="a sticky plum roll",
    ),
    StoryParams(
        obstacle="kite_hill",
        cargo="feather_crown",
        tool="ribbon",
        hero_name="Finn",
        hero_gender="boy",
        companion_name="Rina",
        companion_gender="girl",
        guide_type="father",
        snack="a little jelly cake",
    ),
    StoryParams(
        obstacle="spiral_stairs",
        cargo="stew_pot",
        tool="tray",
        hero_name="Tess",
        hero_gender="girl",
        companion_name="Ben",
        companion_gender="boy",
        guide_type="aunt",
        snack="a jam bun",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
cargo_at_risk(C, O) :- cargo(C), obstacle(O), cargo_property(C, P), challenge(O, P).
selected_tool(C, O, T) :- cargo_at_risk(C, O), tool(T), solves(T, P), cargo_property(C, P).
valid(O, C, T) :- selected_tool(C, O, T).

#show valid/3.
#show selected_tool/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("challenge", oid, obstacle.challenge))
    for cid, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("cargo_property", cid, cargo.property))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("solves", tid, tool.solves))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_selected_tools() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "selected_tool")))


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))
        if cl_valid - py_valid:
            print("  only in clingo:", sorted(cl_valid - py_valid))

    py_tools = set((o, c, select_tool(CARGOS[c], OBSTACLES[o]).id) for (o, c, _t) in valid_combos())
    cl_tools = set(asp_selected_tools())
    if py_tools == cl_tools:
        print(f"OK: selected tools match ({len(py_tools)} tool choices).")
    else:
        rc = 1
        print("MISMATCH in selected tools:")
        if py_tools - cl_tools:
            print("  only in python:", sorted(py_tools - cl_tools))
        if cl_tools - py_tools:
            print("  only in clingo:", sorted(cl_tools - py_tools))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        default_args = build_parser().parse_args([])
        params = resolve_params(default_args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default generation produced empty story")
        print("OK: default seeded generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child carries something important through a quest obstacle."
    )
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--guide", choices=["aunt", "uncle", "mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--companion-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.obstacle:
        cargo = CARGOS[args.cargo]
        obstacle = OBSTACLES[args.obstacle]
        if not cargo_at_risk(cargo, obstacle):
            raise StoryError(explain_rejection(cargo, obstacle))

    combos = [
        combo
        for combo in valid_combos()
        if (args.obstacle is None or combo[0] == args.obstacle)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    obstacle_id, cargo_id, tool_id = rng.choice(combos)
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    companion_name = args.companion_name or _pick_name(rng, companion_gender, avoid=hero_name)
    guide_type = args.guide or rng.choice(["aunt", "uncle", "mother", "father"])
    snack = rng.choice(SNACKS)
    return StoryParams(
        obstacle=obstacle_id,
        cargo=cargo_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        companion_name=companion_name,
        companion_gender=companion_gender,
        guide_type=guide_type,
        snack=snack,
    )


def generate(params: StoryParams) -> StorySample:
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.cargo not in CARGOS:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    obstacle = OBSTACLES[params.obstacle]
    cargo = CARGOS[params.cargo]
    tool = TOOLS[params.tool]
    expected = select_tool(cargo, obstacle)
    if expected is None:
        raise StoryError(explain_rejection(cargo, obstacle))
    if expected.id != tool.id:
        raise StoryError(
            f"(No story: {tool.label} does not solve {obstacle.label} for {cargo.label}. "
            f"Try --tool {expected.id}.)"
        )

    world = tell(
        obstacle=obstacle,
        cargo=cargo,
        tool=tool,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        companion_name=params.companion_name,
        companion_gender=params.companion_gender,
        guide_type=params.guide_type,
        snack=params.snack,
    )

    hero = world.facts["hero"]
    companion = world.facts["companion"]
    guide = world.facts["guide"]
    hero.id = hero.attrs["name"]
    companion.id = companion.attrs["name"]
    guide.id = guide.attrs["name"]

    return StorySample(
        params=params,
        story=world.render().replace("hero", hero.id).replace("companion", companion.id).replace("guide", guide.id),
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (obstacle, cargo, tool) combos:\n")
        for obstacle, cargo, tool in combos:
            print(f"  {obstacle:15} {cargo:14} {tool}")
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
            header = f"### {p.hero_name}: {p.cargo} through {p.obstacle}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
