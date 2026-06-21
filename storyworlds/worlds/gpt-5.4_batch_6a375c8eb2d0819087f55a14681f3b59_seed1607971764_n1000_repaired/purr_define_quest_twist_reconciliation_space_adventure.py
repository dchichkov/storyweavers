#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/purr_define_quest_twist_reconciliation_space_adventure.py
====================================================================================

A standalone story world for a tiny space-adventure tale with a clear quest,
a state-driven twist, and a reconciliation. Two young cadets and a ship's cat
cross a little moon outpost to relight a beacon for the greenhouse. Their
problem is not random word swapping: the world tracks path safety, the risk of
rolling cargo, fear, trust, hurt feelings, and repaired friendship.

The domain is intentionally small and constraint-checked:

- A quest target lives at a location with a path type.
- A chosen carrying tool must fit that path type.
- An impatient shortcut can trigger a twist: the cargo slips away.
- The cat's purr helps the children slow down and work together again.
- Invalid, weak combinations are rejected with StoryError.

Run it
------
    python storyworlds/worlds/gpt-5.4/purr_define_quest_twist_reconciliation_space_adventure.py
    python storyworlds/worlds/gpt-5.4/purr_define_quest_twist_reconciliation_space_adventure.py --target beacon --path ridge --tool rover
    python storyworlds/worlds/gpt-5.4/purr_define_quest_twist_reconciliation_space_adventure.py --path crack
    python storyworlds/worlds/gpt-5.4/purr_define_quest_twist_reconciliation_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/purr_define_quest_twist_reconciliation_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/purr_define_quest_twist_reconciliation_space_adventure.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/purr_define_quest_twist_reconciliation_space_adventure.py --json
    python storyworlds/worlds/gpt-5.4/purr_define_quest_twist_reconciliation_space_adventure.py --asp
    python storyworlds/worlds/gpt-5.4/purr_define_quest_twist_reconciliation_space_adventure.py --verify
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
CALM_MIN = 2


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        catish = {"cat", "robot_cat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in catish:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    id: str
    label: str
    sky: str
    home: str
    surface: str
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
class Target:
    id: str
    label: str
    phrase: str
    need: str
    result: str
    location: str
    path_type: str
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
    terrain: str
    danger: str
    path_type: str
    safe_with: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    calm: int
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        return [e for e in self.entities.values() if e.role in {"captain", "navigator"}]

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


def _r_scared(world: World) -> list[str]:
    cargo = world.get("cargo")
    if cargo.meters["lost"] < THRESHOLD:
        return []
    sig = ("scared", "cargo")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__lost__"]


def _r_hurt(world: World) -> list[str]:
    captain = world.get("captain")
    navigator = world.get("navigator")
    if captain.memes["blame"] < THRESHOLD:
        return []
    sig = ("hurt", "navigator")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    navigator.memes["hurt"] += 1
    navigator.memes["trust"] = max(0.0, navigator.memes["trust"] - 1.0)
    return ["__hurt__"]


def _r_repair(world: World) -> list[str]:
    captain = world.get("captain")
    navigator = world.get("navigator")
    cat = world.get("cat")
    if captain.memes["sorry"] < THRESHOLD or cat.memes["purr"] < THRESHOLD:
        return []
    sig = ("repair", "friendship")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    captain.memes["teamwork"] += 1
    navigator.memes["teamwork"] += 1
    captain.memes["fear"] = 0.0
    navigator.memes["fear"] = 0.0
    navigator.memes["hurt"] = 0.0
    navigator.memes["trust"] += 1
    return ["__repair__"]


CAUSAL_RULES = [
    Rule(name="scared", tag="emotional", apply=_r_scared),
    Rule(name="hurt", tag="social", apply=_r_hurt),
    Rule(name="repair", tag="social", apply=_r_repair),
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


def target_reachable(target: Target, path: Path, tool: Tool) -> bool:
    return target.path_type == path.path_type and path.id in tool.fits and tool.id in path.safe_with


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.calm >= CALM_MIN]


def best_tool_for(path_id: str) -> Optional[str]:
    choices = [tool.id for tool in sensible_tools() if path_id in tool.fits]
    return sorted(choices)[0] if choices else None


def quest_possible(path: Path, tool: Tool) -> bool:
    return path.id in tool.fits and tool.id in path.safe_with


def twist_happens(path: Path, tool: Tool, shortcut: bool) -> bool:
    return shortcut and not quest_possible(path, tool)


def predict_loss(path: Path, tool: Tool, shortcut: bool) -> bool:
    return twist_happens(path, tool, shortcut)


def introduce(world: World, captain: Entity, navigator: Entity, cat: Entity) -> None:
    world.say(
        f"Under {world.setting.sky}, {captain.id} and {navigator.id} raced through "
        f"{world.setting.home} in silver paper helmets. Their ship's cat, {cat.id}, "
        f"trotted after them with a bright little bell on its collar."
    )
    world.say(
        f"They were not just pretending. In their minds, {world.setting.home} was a "
        f"real station on {world.setting.surface}, and tonight they had an important quest."
    )


def quest_brief(world: World, target: Target, cargo: Entity) -> None:
    world.say(
        f"The {target.label} at {target.location} had gone dark, and the greenhouse needed it. "
        f"If they could carry {cargo.label} there, {target.result}."
    )
    world.say(
        f'"First," said the navigator, "we have to define the safest route."'
    )


def prepare(world: World, captain: Entity, navigator: Entity, target: Target, path: Path, tool: Tool) -> None:
    captain.memes["confidence"] += 1
    navigator.memes["care"] += 1
    world.say(
        f"{captain.id} wanted to hurry to {target.location} by way of {path.label}, "
        f"where {path.terrain}."
    )
    world.say(
        f"{navigator.id} pointed to the map and to {tool.phrase}. "
        f'"If we use {tool.label}, {tool.method}," {navigator.pronoun()} said.'
    )


def choose_shortcut(world: World, captain: Entity, navigator: Entity, tool: Tool, path: Path) -> None:
    captain.memes["defiance"] += 1
    world.say(
        f'But {captain.id} bounced on {captain.pronoun("possessive")} toes. '
        f'"We can be faster than that," {captain.pronoun()} said. '
        f'{captain.id} grabbed the cargo and hurried ahead before {navigator.id} could answer.'
    )
    world.facts["ignored_tool"] = tool.label
    world.facts["path_risk"] = path.danger


def careful_departure(world: World, captain: Entity, navigator: Entity, tool: Tool, path: Path) -> None:
    world.say(
        f'This time {captain.id} nodded. "{tool.label.capitalize()} first," '
        f'{captain.pronoun()} agreed.'
    )
    world.say(
        f"Together they set out over {path.label}, using {tool.phrase} so the cargo would stay steady."
    )


def lose_cargo(world: World, cargo: Entity, path: Path) -> None:
    cargo.meters["lost"] += 1
    cargo.meters["distance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came the twist. At the worst bump in {path.label}, the cargo jumped from "
        f"{cargo.attrs['owner_name']}'s hands, flashed once, and rolled into {path.danger}."
    )


def blame(world: World, captain: Entity, navigator: Entity) -> None:
    captain.memes["blame"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Why didn\'t you stop me?" {captain.id} cried.'
    )
    if navigator.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{navigator.id}'s face fell. {navigator.pronoun().capitalize()} had tried to help, "
            f"and now the words stung more than the cold moon wind."
        )


def cat_finds(world: World, cat: Entity, cargo: Entity) -> None:
    cat.memes["purr"] += 1
    cargo.meters["heard"] += 1
    world.say(
        f"Before the argument could grow bigger, {cat.id} padded to the edge, sat very still, "
        f"and began to purr. The soft sound trembled through the metal grating."
    )
    world.say(
        f"Far below, the little crystal answered with a faint blue blink. The purr had helped them find it."
    )


def apologize(world: World, captain: Entity, navigator: Entity) -> None:
    captain.memes["sorry"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{captain.id} took a slow breath. "I am sorry," {captain.pronoun()} said. '
        f'"You were trying to keep the quest safe."'
    )


def recover(world: World, navigator: Entity, tool: Tool, cargo: Entity, path: Path) -> None:
    cargo.meters["lost"] = 0.0
    cargo.meters["secured"] += 1
    world.say(
        f"{navigator.id} clipped the cargo into {tool.phrase}, and together they eased it out of {path.danger}."
    )
    world.say(
        f"This time nobody rushed. Small careful steps brought the glowing crystal safely onward."
    )


def arrive(world: World, target: Target, cargo: Entity) -> None:
    target_ent = world.get("target")
    target_ent.meters["powered"] += 1
    cargo.meters["installed"] += 1
    world.say(
        f"At last they reached {target.location} and slid {cargo.label} into the waiting slot on the {target.label}."
    )
    world.say(
        f"Light spilled across the glass beds of leaves. {target.result.capitalize()}."
    )


def ending(world: World, captain: Entity, navigator: Entity, cat: Entity, target: Target) -> None:
    captain.memes["joy"] += 1
    navigator.memes["joy"] += 1
    cat.memes["joy"] += 1
    world.say(
        f"{captain.id} and {navigator.id} looked at each other and smiled the shy smile that comes after making things right."
    )
    world.say(
        f'{navigator.id} reached down to scratch {cat.id} between the ears. '
        f'{cat.id} gave another happy purr, and the bright {target.label} shone over all three crew members.'
    )


def tell(
    setting: Setting,
    target: Target,
    path: Path,
    tool: Tool,
    captain_name: str = "Mira",
    captain_gender: str = "girl",
    navigator_name: str = "Jax",
    navigator_gender: str = "boy",
    cat_name: str = "Orbit",
    cat_type: str = "cat",
    relation: str = "friends",
    shortcut: bool = True,
) -> World:
    world = World(setting)
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type=captain_gender,
        label=captain_name,
        role="captain",
        attrs={"name": captain_name, "relation": relation},
    ))
    navigator = world.add(Entity(
        id="navigator",
        kind="character",
        type=navigator_gender,
        label=navigator_name,
        role="navigator",
        attrs={"name": navigator_name, "relation": relation},
    ))
    cat = world.add(Entity(
        id="cat",
        kind="character",
        type=cat_type,
        label=cat_name,
        role="helper",
    ))
    cargo = world.add(Entity(
        id="cargo",
        type="crystal",
        label="the spare glow-crystal",
        attrs={"owner_name": captain_name},
    ))
    target_ent = world.add(Entity(
        id="target",
        type="target",
        label=target.label,
    ))

    captain.memes["trust"] = 1.0
    navigator.memes["trust"] = 2.0
    captain.memes["fear"] = 0.0
    navigator.memes["fear"] = 0.0
    cat.memes["purr"] = 0.0
    cargo.meters["lost"] = 0.0
    cargo.meters["secured"] = 0.0
    target_ent.meters["powered"] = 0.0
    world.facts.update(
        setting=setting,
        target_cfg=target,
        path_cfg=path,
        tool_cfg=tool,
        captain_name=captain_name,
        navigator_name=navigator_name,
        cat_name=cat_name,
        shortcut=shortcut,
        relation=relation,
    )

    introduce(world, captain, navigator, cat)
    quest_brief(world, target, cargo)

    world.para()
    prepare(world, captain, navigator, target, path, tool)

    used_shortcut = shortcut
    safe = quest_possible(path, tool)

    if used_shortcut and not safe:
        choose_shortcut(world, captain, navigator, tool, path)

        world.para()
        lose_cargo(world, cargo, path)
        blame(world, captain, navigator)
        cat_finds(world, cat, cargo)

        world.para()
        apologize(world, captain, navigator)
        recover(world, navigator, tool, cargo, path)
        arrive(world, target, cargo)

        world.para()
        ending(world, captain, navigator, cat, target)
        outcome = "twist"
    else:
        careful_departure(world, captain, navigator, tool, path)

        world.para()
        arrive(world, target, cargo)

        world.para()
        cat.memes["purr"] += 1
        captain.memes["sorry"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{cat.label} curled around their boots and gave a warm purr anyway, as if blessing the careful plan."
        )
        world.say(
            f"They had finished the quest without a tumble, and the two young explorers felt even more like a team."
        )
        outcome = "smooth"

    world.facts.update(
        captain=captain,
        navigator=navigator,
        cat=cat,
        cargo=cargo,
        target=target_ent,
        outcome=outcome,
        lost_once=("scared", "cargo") in world.fired,
        reconciled=("repair", "friendship") in world.fired,
        powered=target_ent.meters["powered"] >= THRESHOLD,
        hurt=("hurt", "navigator") in world.fired,
    )
    return world


SETTINGS = {
    "moonbase": Setting(
        id="moonbase",
        label="Moonbase Lark",
        sky="a black sky pricked with quiet stars",
        home="Moonbase Lark",
        surface="the little moon plain beyond the dome",
        tags={"space", "moon"},
    ),
    "marsdome": Setting(
        id="marsdome",
        label="Mars Dome Fern",
        sky="a dusk-red sky and one brave evening star",
        home="Mars Dome Fern",
        surface="the rusty red yard outside the dome",
        tags={"space", "mars"},
    ),
    "ringship": Setting(
        id="ringship",
        label="the Ring Ship Marigold",
        sky="the long blue curve of a faraway planet",
        home="the Ring Ship Marigold",
        surface="the humming outer deck",
        tags={"space", "ship"},
    ),
}

TARGETS = {
    "beacon": Target(
        id="beacon",
        label="beacon",
        phrase="the beacon",
        need="light for the greenhouse path",
        result="the beacon glowed and the greenhouse path lit up again",
        location="Beacon Hill",
        path_type="ridge",
        tags={"beacon", "light"},
    ),
    "greenhouse": Target(
        id="greenhouse",
        label="greenhouse door",
        phrase="the greenhouse door",
        need="warmth for the seedlings",
        result="the greenhouse door blinked green and warm air hummed inside",
        location="the warm glass dome",
        path_type="deck",
        tags={"greenhouse", "plants"},
    ),
    "dish": Target(
        id="dish",
        label="weather dish",
        phrase="the weather dish",
        need="a steady signal for the station",
        result="the weather dish turned with a silver whirr and the station screens came awake",
        location="Signal Rise",
        path_type="ridge",
        tags={"signal", "weather"},
    ),
}

PATHS = {
    "ridge": Path(
        id="ridge",
        label="the narrow ridge path",
        terrain="silver dust slid off the stones like sugar",
        danger="a shallow crack full of blue shadow",
        path_type="ridge",
        safe_with={"harness", "sled"},
        tags={"ridge", "careful"},
    ),
    "deck": Path(
        id="deck",
        label="the outer deck",
        terrain="the floor was smooth but full of humming vents",
        danger="a humming vent grate",
        path_type="deck",
        safe_with={"cart", "harness"},
        tags={"deck", "station"},
    ),
    "crack": Path(
        id="crack",
        label="the broken shortcut",
        terrain="crumbly rocks tilted toward a long dark split",
        danger="the long dark split",
        path_type="ridge",
        safe_with={"harness"},
        tags={"crack", "risky"},
    ),
}

TOOLS = {
    "harness": Tool(
        id="harness",
        label="the tether harness",
        phrase="the tether harness",
        method="the crystal cannot bounce away, even on the steep parts",
        calm=3,
        fits={"ridge", "crack", "deck"},
        tags={"harness", "safety"},
    ),
    "cart": Tool(
        id="cart",
        label="the moon cart",
        phrase="the moon cart",
        method="the smooth wheels keep the crystal steady across the flat metal floor",
        calm=3,
        fits={"deck"},
        tags={"cart", "wheels"},
    ),
    "sled": Tool(
        id="sled",
        label="the glide sled",
        phrase="the glide sled",
        method="the low runners skim safely over the dusty stones",
        calm=2,
        fits={"ridge"},
        tags={"sled", "glide"},
    ),
    "rover": Tool(
        id="rover",
        label="the toy rover",
        phrase="the toy rover",
        method="it looks brave, but its tiny tray wobbles too much to trust",
        calm=1,
        fits={"deck"},
        tags={"rover"},
    ),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for target_id, target in TARGETS.items():
            for path_id, path in PATHS.items():
                if target.path_type != path.path_type:
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool.calm < CALM_MIN:
                        continue
                    if target_reachable(target, path, tool):
                        combos.append((setting_id, target_id, path_id, tool_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    target: str
    path: str
    tool: str
    captain: str
    captain_gender: str
    navigator: str
    navigator_gender: str
    cat: str
    relation: str
    shortcut: bool = True
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
    "beacon": [(
        "What is a beacon?",
        "A beacon is a bright signal light that helps people find a place or a path. In stories about space stations, a beacon can guide travelers through the dark."
    )],
    "greenhouse": [(
        "What is a greenhouse?",
        "A greenhouse is a place where plants grow warm and safe behind glass or clear walls. It helps keep seedlings protected from cold weather."
    )],
    "signal": [(
        "What does a weather dish do?",
        "A weather dish listens and sends signals so a station can learn what is happening outside. Signals help machines share information across a distance."
    )],
    "harness": [(
        "What does a tether harness do?",
        "A tether harness keeps something tied on safely so it cannot roll or float away. In a risky place, it helps explorers carry important things carefully."
    )],
    "cart": [(
        "Why is a cart good on a flat floor?",
        "A cart rolls best on smooth ground where its wheels can stay steady. On rough places, wheels can bump and tip."
    )],
    "sled": [(
        "Why can a sled work on dusty rocks?",
        "A sled can slide over a rough surface without depending on tiny wheels. That can make it steadier than a cart on uneven ground."
    )],
    "careful": [(
        "Why is it smart to move slowly with something fragile?",
        "Moving slowly gives your hands and feet time to stay steady. That helps keep fragile things from slipping or falling."
    )],
    "space": [(
        "Why do space explorers need teamwork?",
        "Space jobs can be tricky, and one person may notice a danger that another person misses. Teamwork helps explorers stay safe and solve problems together."
    )],
    "cat": [(
        "Why do cats purr?",
        "Cats often purr when they feel calm or friendly. People also notice that a purr can make a quiet moment feel softer and safer."
    )],
}
KNOWLEDGE_ORDER = ["space", "beacon", "greenhouse", "signal", "harness", "cart", "sled", "careful", "cat"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    target = f["target_cfg"]
    path = f["path_cfg"]
    tool = f["tool_cfg"]
    captain = f["captain_name"]
    navigator = f["navigator_name"]
    cat = f["cat_name"]
    outcome = f["outcome"]
    if outcome == "twist":
        return [
            f'Write a short Space Adventure story for a 3-to-5-year-old about a quest to relight a {target.label}. Include the words "purr" and "define".',
            f"Tell a space tale where {captain} and {navigator} must carry a glowing crystal over {path.label}, a twist makes it slip away, and {cat}'s purr helps them work together again.",
            f"Write a gentle story with Quest, Twist, and Reconciliation where two young explorers stop arguing, choose {tool.label}, and finish their mission safely.",
        ]
    return [
        f'Write a short Space Adventure story for a 3-to-5-year-old about a quest to relight a {target.label}. Include the words "purr" and "define".',
        f"Tell a calm mission story where {captain} and {navigator} define the safest route, use {tool.label}, and succeed together.",
        f"Write a simple space story where careful teamwork matters more than rushing, and end with a warm purr under a shining station light.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    navigator = f["navigator"]
    cat = f["cat"]
    cargo = f["cargo"]
    target_cfg = f["target_cfg"]
    path = f["path_cfg"]
    tool = f["tool_cfg"]
    captain_name = f["captain_name"]
    navigator_name = f["navigator_name"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {captain_name}, {navigator_name}, and their cat {cat.label}. They are a little space crew on a mission together."
        ),
        (
            "What was their quest?",
            f"They needed to carry {cargo.label} to the {target_cfg.label} at {target_cfg.location}. If they succeeded, {target_cfg.result}."
        ),
        (
            "Why did the navigator want to define the safest route?",
            f"{navigator_name} knew the path could be tricky and wanted the crew to think before rushing. Defining the route mattered because the crystal was important and could slip away."
        ),
    ]
    if f["outcome"] == "twist":
        qa.extend([
            (
                "What was the twist in the story?",
                f"The crystal jumped away on {path.label} and rolled into {path.danger}. That happened because {captain_name} hurried instead of using {tool.label} right away."
            ),
            (
                f"How did {cat.label}'s purr help?",
                f"{cat.label}'s purr made the children stop arguing and listen. It also helped them notice where the lost crystal was blinking in the dark."
            ),
            (
                "How did the children reconcile?",
                f"{captain_name} apologized for blaming {navigator_name}, and then they worked side by side to recover the crystal. Their friendship felt better because they chose teamwork after the mistake."
            ),
            (
                "How did the story end?",
                f"They reached the {target_cfg.label} and powered it again, and the station grew bright. The ending image shows them together under the shining light with the cat purring."
            ),
        ])
    else:
        qa.extend([
            (
                "How did they keep the crystal safe?",
                f"They used {tool.label} on {path.label} instead of rushing. That kept the crystal steady all the way to the {target_cfg.label}."
            ),
            (
                "Did they have a big argument?",
                f"No, because they listened to the careful plan before anything went wrong. The story stays calm and ends with teamwork instead of hurt feelings."
            ),
            (
                "How did the story end?",
                f"They finished the mission safely, and the {target_cfg.label} shone again. Their careful choice proved that working together was the right way to travel."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(world.setting.tags) | set(f["target_cfg"].tags) | set(f["path_cfg"].tags) | set(f["tool_cfg"].tags) | {"cat"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moonbase",
        target="beacon",
        path="ridge",
        tool="sled",
        captain="Mira",
        captain_gender="girl",
        navigator="Jax",
        navigator_gender="boy",
        cat="Orbit",
        relation="friends",
        shortcut=True,
    ),
    StoryParams(
        setting="marsdome",
        target="greenhouse",
        path="deck",
        tool="cart",
        captain="Theo",
        captain_gender="boy",
        navigator="Nora",
        navigator_gender="girl",
        cat="Pepper",
        relation="siblings",
        shortcut=True,
    ),
    StoryParams(
        setting="ringship",
        target="beacon",
        path="ridge",
        tool="harness",
        captain="Ava",
        captain_gender="girl",
        navigator="Finn",
        navigator_gender="boy",
        cat="Comet",
        relation="friends",
        shortcut=False,
    ),
    StoryParams(
        setting="moonbase",
        target="dish",
        path="ridge",
        tool="harness",
        captain="Leo",
        captain_gender="boy",
        navigator="Maya",
        navigator_gender="girl",
        cat="Nova",
        relation="siblings",
        shortcut=True,
    ),
    StoryParams(
        setting="ringship",
        target="greenhouse",
        path="deck",
        tool="harness",
        captain="Zoe",
        captain_gender="girl",
        navigator="Eli",
        navigator_gender="boy",
        cat="Tinsel",
        relation="friends",
        shortcut=False,
    ),
]

ASP_RULES = r"""
valid(S,T,P,Tool) :- setting(S), target(T), path(P), tool(Tool),
                     target_path(T, Kind), path_type(P, Kind),
                     calm(Tool, C), calm_min(M), C >= M,
                     fits(Tool, P), safe_with(P, Tool).

twist :- shortcut, chosen_path(P), chosen_tool(Tool),
         not fits(Tool, P).
twist :- shortcut, chosen_path(P), chosen_tool(Tool),
         not safe_with(P, Tool).
smooth :- not twist.

#show valid/4.
#show twist/0.
#show smooth/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("target_path", target_id, target.path_type))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("path_type", path_id, path.path_type))
        for tool_id in sorted(path.safe_with):
            lines.append(asp.fact("safe_with", path_id, tool_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("calm", tool_id, tool.calm))
        for path_id in sorted(tool.fits):
            lines.append(asp.fact("fits", tool_id, path_id))
    lines.append(asp.fact("calm_min", CALM_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(path_id: str, tool_id: str, shortcut: bool) -> str:
    import asp

    extra_lines = [
        asp.fact("chosen_path", path_id),
        asp.fact("chosen_tool", tool_id),
    ]
    if shortcut:
        extra_lines.append(asp.fact("shortcut"))
    model = asp.one_model(asp_program("\n".join(extra_lines)))
    if asp.atoms(model, "twist"):
        return "twist"
    return "smooth"


def explain_rejection(target: Target, path: Path, tool: Tool) -> str:
    if target.path_type != path.path_type:
        return (
            f"(No story: {target.phrase} is reached by a {target.path_type} route, "
            f"but {path.label} is a different kind of path. Pick a path that honestly leads to that target.)"
        )
    if tool.calm < CALM_MIN:
        better = ", ".join(sorted(t.id for t in sensible_tools()))
        return (
            f"(Refusing tool '{tool.id}': it is too wobbly or toy-like for this mission "
            f"(calm={tool.calm} < {CALM_MIN}). Try one of: {better}.)"
        )
    if path.id not in tool.fits:
        return (
            f"(No story: {tool.label} does not fit {path.label}. The crew needs gear that can actually travel that terrain.)"
        )
    if tool.id not in path.safe_with:
        return (
            f"(No story: {tool.label} is known in this world, but it is not a sensible way to carry fragile cargo over {path.label}.)"
        )
    return "(No story: this combination is not reasonable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small space quest with a twist and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--captain")
    ap.add_argument("--navigator")
    ap.add_argument("--cat")
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("--shortcut", dest="shortcut", action="store_true", default=None,
                    help="have the captain rush and cause the twist when the path/tool mismatch")
    ap.add_argument("--no-shortcut", dest="shortcut", action="store_false",
                    help="take the careful plan instead of rushing")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Mira", "Ava", "Zoe", "Nora", "Maya", "Lina", "Ivy", "Etta"]
BOY_NAMES = ["Jax", "Leo", "Finn", "Eli", "Theo", "Max", "Noah", "Sam"]
CAT_NAMES = ["Orbit", "Comet", "Nova", "Pepper", "Tinsel", "Pico"]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and args.path and args.tool:
        target = TARGETS[args.target]
        path = PATHS[args.path]
        tool = TOOLS[args.tool]
        if not target_reachable(target, path, tool):
            raise StoryError(explain_rejection(target, path, tool))
    elif args.tool:
        tool = TOOLS[args.tool]
        if tool.calm < CALM_MIN:
            dummy_target = TARGETS[args.target] if args.target else next(iter(TARGETS.values()))
            dummy_path = PATHS[args.path] if args.path else next(iter(PATHS.values()))
            raise StoryError(explain_rejection(dummy_target, dummy_path, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.target is None or combo[1] == args.target)
        and (args.path is None or combo[2] == args.path)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, target_id, path_id, tool_id = rng.choice(sorted(combos))
    captain_gender = rng.choice(["girl", "boy"])
    navigator_gender = rng.choice(["girl", "boy"])
    captain = args.captain or _pick_name(rng, captain_gender)
    navigator = args.navigator or _pick_name(rng, navigator_gender, avoid=captain)
    cat = args.cat or rng.choice(CAT_NAMES)
    relation = args.relation or rng.choice(["friends", "siblings"])
    shortcut = args.shortcut if args.shortcut is not None else rng.choice([True, True, False])

    return StoryParams(
        setting=setting_id,
        target=target_id,
        path=path_id,
        tool=tool_id,
        captain=captain,
        captain_gender=captain_gender,
        navigator=navigator,
        navigator_gender=navigator_gender,
        cat=cat,
        relation=relation,
        shortcut=shortcut,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.path not in PATHS:
        raise StoryError(f"(Unknown path: {params.path})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    setting = SETTINGS[params.setting]
    target = TARGETS[params.target]
    path = PATHS[params.path]
    tool = TOOLS[params.tool]
    if not target_reachable(target, path, tool):
        raise StoryError(explain_rejection(target, path, tool))

    world = tell(
        setting=setting,
        target=target,
        path=path,
        tool=tool,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        navigator_name=params.navigator,
        navigator_gender=params.navigator_gender,
        cat_name=params.cat,
        relation=params.relation,
        shortcut=params.shortcut,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    checked = 0
    for setting_id, target_id, path_id, tool_id in sorted(py_set)[:8]:
        for shortcut in (False, True):
            py_out = "twist" if twist_happens(PATHS[path_id], TOOLS[tool_id], shortcut) else "smooth"
            asp_out = asp_outcome(path_id, tool_id, shortcut)
            checked += 1
            if py_out != asp_out:
                rc = 1
                print(
                    f"MISMATCH outcome for ({setting_id}, {target_id}, {path_id}, {tool_id}, shortcut={shortcut}): "
                    f"python={py_out} clingo={asp_out}"
                )
    if rc == 0:
        print(f"OK: outcome model matches on {checked} checked scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        _ = sample.to_json()
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

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
        print(f"{len(combos)} compatible (setting, target, path, tool) combos:\n")
        for setting_id, target_id, path_id, tool_id in combos:
            print(f"  {setting_id:9} {target_id:10} {path_id:8} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain}, {p.navigator}, and {p.cat}: {p.target} via {p.path} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
