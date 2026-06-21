#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nana_blur_mink_bad_ending_adventure.py
=================================================================

A standalone storyworld for a small adventure domain: a child explorer sees a
quick blur in the wild, decides it must be a mink leading to something exciting,
and faces a choice about how to cross rough ground. A careful elder called Nana
warns about the danger. In the bad-ending branch, the child takes the foolish
shortcut, gets stranded or loses the needed supplies, and the adventure ends in
loss instead of triumph.

The world model is intentionally small and concrete:
- typed entities carry physical meters and emotional memes
- terrain determines what kind of crossing is actually dangerous
- gear must match the hazard
- the child's choice drives the turn
- the ending image proves what changed

Run it
------
    python storyworlds/worlds/gpt-5.4/nana_blur_mink_bad_ending_adventure.py
    python storyworlds/worlds/gpt-5.4/nana_blur_mink_bad_ending_adventure.py --terrain creek --shortcut log
    python storyworlds/worlds/gpt-5.4/nana_blur_mink_bad_ending_adventure.py --shortcut fern_tunnel
    python storyworlds/worlds/gpt-5.4/nana_blur_mink_bad_ending_adventure.py --all
    python storyworlds/worlds/gpt-5.4/nana_blur_mink_bad_ending_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/nana_blur_mink_bad_ending_adventure.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/nana_blur_mink_bad_ending_adventure.py --json
    python storyworlds/worlds/gpt-5.4/nana_blur_mink_bad_ending_adventure.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "woman", "grandmother", "nana"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


# ---------------------------------------------------------------------------
# Domain configuration
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
class Setting:
    id: str
    place: str
    ground: str
    sky: str
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
class Terrain:
    id: str
    label: str
    the: str
    danger: str
    needs: str
    loss: str
    severity: int
    terrain_type: str
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
class Shortcut:
    id: str
    label: str
    phrase: str
    for_type: str
    stable: bool
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
class Gear:
    id: str
    label: str
    phrase: str
    protects: set[str]
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
class Quest:
    id: str
    start: str
    rumor: str
    prize: str
    ending_loss: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and rules
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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["crossing_risk"] < THRESHOLD:
        return out
    if child.meters["protected"] >= THRESHOLD:
        return out
    sig = ("slip", "child")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["slipped"] += 1
    child.memes["fear"] += 1
    child.memes["regret"] += 1
    pack = world.get("pack")
    pack.meters["lost"] += 1
    pack.meters["wet"] += 1
    out.append("__slip__")
    return out


def _r_retreat(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["slipped"] < THRESHOLD:
        return out
    sig = ("retreat", "party")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["quest_failed"] += 1
    world.get("nana").memes["worry"] += 1
    out.append("__retreat__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="retreat", tag="physical", apply=_r_retreat),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def shortcut_fits(terrain: Terrain, shortcut: Shortcut) -> bool:
    return terrain.terrain_type == shortcut.for_type


def gear_works(terrain: Terrain, gear: Gear) -> bool:
    return terrain.terrain_type in gear.protects


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for terrain_id, terrain in TERRAINS.items():
            for shortcut_id, shortcut in SHORTCUTS.items():
                if not shortcut_fits(terrain, shortcut):
                    continue
                for gear_id, gear in GEAR.items():
                    if gear_works(terrain, gear):
                        combos.append((setting_id, terrain_id, shortcut_id, gear_id))
    return combos


def explain_shortcut(terrain: Terrain, shortcut: Shortcut) -> str:
    return (
        f"(No story: {shortcut.phrase} does not honestly cross {terrain.the}. "
        f"This world only allows shortcuts that match the real obstacle.)"
    )


def explain_gear(terrain: Terrain, gear: Gear) -> str:
    return (
        f"(No story: {gear.label} would not make {terrain.the} safer. "
        f"The offered gear must actually fit the danger.)"
    )


# ---------------------------------------------------------------------------
# Prediction and verbs
# ---------------------------------------------------------------------------
def predict_disaster(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["crossing_risk"] = float(sim.facts["terrain"].severity)
    if sim.facts["obeys"]:
        child.meters["protected"] = 1.0
    propagate(sim, narrate=False)
    return {
        "slipped": child.meters["slipped"] >= THRESHOLD,
        "pack_lost": sim.get("pack").meters["lost"] >= THRESHOLD,
        "quest_failed": child.meters["quest_failed"] >= THRESHOLD,
    }


def intro(world: World, child: Entity, nana: Entity, setting: Setting, quest: Quest) -> None:
    child.memes["joy"] += 1
    child.memes["curiosity"] += 1
    nana.memes["care"] += 1
    world.say(
        f"{child.id} and Nana set out into {setting.place} on a small adventure. "
        f"{setting.sky} {setting.ground}"
    )
    world.say(
        f'Nana carried the lunch tin, and {child.id} carried a little field pack with a map and a red ribbon tied to the strap. '
        f'{quest.start}'
    )
    world.say(quest.rumor)


def spot_blur(world: World, child: Entity, terrain: Terrain) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Then a brown blur flashed past the reeds. It was a mink, quick as a wink, "
        f"darting toward {terrain.the}."
    )
    world.say(
        f'"A mink!" {child.id} gasped. "It looks like it knows the secret way."'
    )


def warning(world: World, nana: Entity, child: Entity, terrain: Terrain, gear: Gear) -> None:
    pred = predict_disaster(world)
    world.facts["predicted_slip"] = pred["slipped"]
    world.facts["predicted_pack_lost"] = pred["pack_lost"]
    nana.memes["worry"] += 1
    child.memes["impatience"] += 1
    if pred["slipped"]:
        world.say(
            f'Nana caught {child.id} by the sleeve. "{terrain.The} is {terrain.danger}," '
            f'she said. "If you rush across without {gear.phrase}, you could slip and lose your pack."'
        )
    else:
        world.say(
            f'Nana studied {terrain.the}. "{gear.phrase.capitalize()} is how we cross {terrain.the} safely," '
            f'she said. "Adventure is better when we come back with our things."'
        )


def choice_obey(world: World, child: Entity, nana: Entity, shortcut: Shortcut, gear: Gear) -> None:
    child.memes["trust"] += 1
    child.meters["protected"] = 1.0
    world.say(
        f"{child.id} still wanted to chase the mink, but listened. Together they used {gear.phrase} and "
        f"took {shortcut.phrase} the careful way."
    )


def choice_defy(world: World, child: Entity, shortcut: Shortcut) -> None:
    child.memes["defiance"] += 1
    child.meters["crossing_risk"] = float(world.facts["terrain"].severity)
    world.say(
        f'But the mink was already another blur ahead, and the thought of treasure pulled hard. '
        f'"I can do it!" {child.id} cried, and ran for {shortcut.phrase}.'
    )


def disaster(world: World, child: Entity, terrain: Terrain, quest: Quest) -> None:
    propagate(world, narrate=False)
    pack = world.get("pack")
    if child.meters["slipped"] >= THRESHOLD:
        world.say(
            f"The shortcut failed at once. {terrain.loss} "
            f"{child.id} sprawled on cold ground, and the little pack flew open."
        )
        world.say(
            f"The map blurred into wet paper, and the red ribbon went spinning away on the current. "
            f"{quest.ending_loss}"
        )
        pack.attrs["map_ruined"] = True


def retreat(world: World, nana: Entity, child: Entity, quest: Quest) -> None:
    child.memes["sadness"] += 1
    child.memes["fear"] += 1
    nana.memes["care"] += 1
    world.say(
        f'Nana reached {child.id} and pulled {child.pronoun("object")} close. '
        f'"We are going back now," she said, in the voice she used when there was no more arguing.'
    )
    world.say(
        f"They turned away from the trail. Ahead, the mink paused on a stone, bright-eyed and far beyond them, "
        f"and then vanished into the brush."
    )
    world.say(
        f"By the time they came home, the adventure was over. The map was ruined, the secret place was unfound, "
        f"and {child.id} knew that being fast for one moment had made the whole day smaller."
    )


def safe_finish(world: World, child: Entity, nana: Entity, quest: Quest) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(
        f"On the other side they found only a quiet track of paws and a hollow full of feathers. "
        f"The mink had been only a mink, not a guide to treasure."
    )
    world.say(
        f"But {child.id} still had the map, the ribbon, and Nana beside {child.pronoun('object')}. "
        f"They ate their lunch under a leaning tree and laughed at how wild the chase had felt."
    )
    world.say(
        f"The adventure ended small and safe, with muddy shoes perhaps, but everything important brought home."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    terrain: Terrain,
    shortcut: Shortcut,
    gear: Gear,
    quest: Quest,
    *,
    child_name: str = "Mira",
    child_gender: str = "girl",
    obeys: bool = False,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    nana = world.add(Entity(id="Nana", kind="character", type="nana", role="elder", label="Nana"))
    pack = world.add(Entity(id="pack", kind="thing", type="pack", label="field pack"))
    world.add(Entity(id="mink", kind="thing", type="animal", label="mink"))
    world.facts.update(
        setting=setting,
        terrain=terrain,
        shortcut=shortcut,
        gear=gear,
        quest=quest,
        obeys=obeys,
    )
    child.meters["crossing_risk"] = 0.0
    child.meters["protected"] = 0.0
    child.meters["slipped"] = 0.0
    child.meters["quest_failed"] = 0.0
    pack.meters["lost"] = 0.0
    pack.meters["wet"] = 0.0
    pack.attrs["map_ruined"] = False

    intro(world, child, nana, setting, quest)
    world.para()
    spot_blur(world, child, terrain)
    warning(world, nana, child, terrain, gear)
    world.para()

    if obeys:
        choice_obey(world, child, nana, shortcut, gear)
        world.para()
        safe_finish(world, child, nana, quest)
        outcome = "safe"
    else:
        choice_defy(world, child, shortcut)
        world.para()
        disaster(world, child, terrain, quest)
        retreat(world, nana, child, quest)
        outcome = "bad"

    world.facts.update(
        child=child,
        nana=nana,
        pack=pack,
        outcome=outcome,
        slipped=child.meters["slipped"] >= THRESHOLD,
        quest_failed=child.meters["quest_failed"] >= THRESHOLD,
        map_ruined=bool(pack.attrs["map_ruined"]),
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "marsh": Setting(
        id="marsh",
        place="the edge of the marsh",
        ground="Soft grass bent around dark water, and every path looked half-lost.",
        sky="The morning was bright, but the wind kept folding the tall reeds together.",
        tags={"marsh", "trail"},
    ),
    "pinewoods": Setting(
        id="pinewoods",
        place="the pine woods beyond the village",
        ground="Pine needles softened the path, and fern shadows hid the roots.",
        sky="Clouds sailed over the trees like slow gray ships.",
        tags={"woods", "trail"},
    ),
    "cliffs": Setting(
        id="cliffs",
        place="the windy cliff path above the cove",
        ground="Sea spray shone on the stones, and gulls cried over the drop below.",
        sky="The afternoon light flashed silver on the water.",
        tags={"cliff", "sea"},
    ),
}

TERRAINS = {
    "creek": Terrain(
        id="creek",
        label="creek",
        the="the rushing creek",
        danger="slick and fast",
        needs="dry footing",
        loss="The wet log rolled under one foot and tipped sideways.",
        severity=2,
        terrain_type="water",
        tags={"creek", "water"},
    ),
    "bog": Terrain(
        id="bog",
        label="bog",
        the="the sucking bog",
        danger="soft enough to grab a boot",
        needs="firm boards",
        loss="The mud gave a hungry slurp and swallowed one shoe to the ankle.",
        severity=2,
        terrain_type="mud",
        tags={"bog", "mud"},
    ),
    "ravine": Terrain(
        id="ravine",
        label="ravine",
        the="the narrow ravine",
        danger="crumbly at the edge",
        needs="steady footing",
        loss="Loose stones rattled down, and the child skidded onto both knees.",
        severity=3,
        terrain_type="height",
        tags={"ravine", "height"},
    ),
}

SHORTCUTS = {
    "log": Shortcut(
        id="log",
        label="log",
        phrase="a mossy fallen log",
        for_type="water",
        stable=False,
        tags={"log", "shortcut"},
    ),
    "fern_tunnel": Shortcut(
        id="fern_tunnel",
        label="fern tunnel",
        phrase="a narrow fern tunnel over hummocks",
        for_type="mud",
        stable=False,
        tags={"ferns", "shortcut"},
    ),
    "goat_path": Shortcut(
        id="goat_path",
        label="goat path",
        phrase="a goat path scratched along the side",
        for_type="height",
        stable=False,
        tags={"path", "shortcut"},
    ),
}

GEAR = {
    "grip_boots": Gear(
        id="grip_boots",
        label="grip boots",
        phrase="the grip boots",
        protects={"water", "mud"},
        tags={"boots"},
    ),
    "walking_staff": Gear(
        id="walking_staff",
        label="walking staff",
        phrase="the walking staff",
        protects={"water", "height"},
        tags={"staff"},
    ),
    "rope_belt": Gear(
        id="rope_belt",
        label="rope belt",
        phrase="the rope belt",
        protects={"height"},
        tags={"rope"},
    ),
    "bog_board": Gear(
        id="bog_board",
        label="bog board",
        phrase="the bog board",
        protects={"mud"},
        tags={"board"},
    ),
}

QUESTS = {
    "moonpool": Quest(
        id="moonpool",
        start="They were looking for the Moonpool, a hidden place Nana said gleamed like a coin under willow leaves.",
        rumor="Somebody in the village had whispered that a mink sometimes ran that way at dawn.",
        prize="the Moonpool",
        ending_loss="The trail to the Moonpool was gone before they had really begun.",
        tags={"pool", "quest"},
    ),
    "foxglove_arch": Quest(
        id="foxglove_arch",
        start="They were looking for the Foxglove Arch, a stone opening that children in the village talked about like a gate to another kingdom.",
        rumor="Nana had once seen a mink slip through that country before sunset and vanish where no ordinary footpath went.",
        prize="the Foxglove Arch",
        ending_loss="Whatever path led to the Foxglove Arch was lost to them now.",
        tags={"arch", "quest"},
    ),
    "salt_cave": Quest(
        id="salt_cave",
        start="They were looking for the Salt Cave above the cove, where the walls were said to shine pale in the dark.",
        rumor="A fisherman had laughed and said a mink knew every crack and ledge along that coast.",
        prize="the Salt Cave",
        ending_loss="The way to the Salt Cave stayed a story instead of becoming a place.",
        tags={"cave", "quest"},
    ),
}

GIRL_NAMES = ["Mira", "Tessa", "Lina", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Finn", "Leo", "Milo", "Eli", "Theo", "Sam"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    terrain: str
    shortcut: str
    gear: str
    quest: str
    child_name: str
    child_gender: str
    obeys: bool = False
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
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
    "mink": [
        (
            "What is a mink?",
            "A mink is a small animal with a long body and quick legs. It can move so fast that it looks like a blur when it runs.",
        )
    ],
    "creek": [
        (
            "Why is a wet log dangerous over a creek?",
            "A wet log can be slippery and roll under your feet. If it moves suddenly, you can fall into the water or drop what you are carrying.",
        )
    ],
    "bog": [
        (
            "Why is a bog hard to cross?",
            "A bog is soft, wet ground that can suck at shoes and make people stumble. It looks solid in places, but the mud underneath can grab you.",
        )
    ],
    "ravine": [
        (
            "Why should children be careful near a ravine?",
            "A ravine has steep sides and loose ground. Small feet can slip on stones or dirt near the edge.",
        )
    ],
    "boots": [
        (
            "What are grip boots for?",
            "Grip boots help your feet hold the ground better. They are useful on wet or muddy places where ordinary shoes might slide.",
        )
    ],
    "staff": [
        (
            "What does a walking staff do?",
            "A walking staff gives you another point to lean on. It helps you balance when the ground is narrow, uneven, or slippery.",
        )
    ],
    "rope": [
        (
            "Why can a rope belt help on a steep path?",
            "A rope belt lets a grown-up keep you close on a dangerous slope. It does not make the place harmless, but it can stop a bad slip from becoming worse.",
        )
    ],
    "adventure": [
        (
            "What makes an adventure safe instead of foolish?",
            "A safe adventure still feels exciting, but it uses the right gear and listens to warnings. Being brave does not mean pretending danger is not real.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mink", "creek", "bog", "ravine", "boots", "staff", "rope", "adventure"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    terrain = f["terrain"]
    quest = f["quest"]
    if f["outcome"] == "bad":
        return [
            'Write an adventure story for a 3-to-5-year-old that includes the words "nana", "blur", and "mink", and ends badly because a child ignores a warning.',
            f"Tell a small adventure where {child.id} and Nana follow a blur that turns out to be a mink near {terrain.the}, and the chase ends in loss instead of treasure.",
            f"Write a cautionary adventure about a child rushing after a mink while searching for {quest.prize}, with a sad ending that shows why listening matters.",
        ]
    return [
        'Write an adventure story for a 3-to-5-year-old that includes the words "nana", "blur", and "mink", and ends with the child choosing caution.',
        f"Tell a small adventure where {child.id} and Nana follow a blur that turns out to be a mink near {terrain.the}, but they stay safe.",
        f"Write a gentle adventure about looking for {quest.prize} and learning that careful choices can still feel brave.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    terrain = f["terrain"]
    gear = f["gear"]
    quest = f["quest"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and Nana on a little adventure together. They go out looking for {quest.prize}.",
        ),
        (
            "What was the blur in the story?",
            f"The blur was a mink running ahead of them. It looked exciting, so {child.id} thought it might be leading the way.",
        ),
        (
            f"Why did Nana warn {child.id}?",
            f'Nana warned {child.id} because {terrain.the} was {terrain.danger}. She knew that rushing across without {gear.phrase} could make {child.pronoun("object")} slip and lose the pack.',
        ),
    ]
    if f["outcome"] == "bad":
        out.extend(
            [
                (
                    f"What happened when {child.id} took the shortcut?",
                    f"{child.id} slipped because the shortcut was not safe for crossing {terrain.the}. The fall sent the pack flying, and the map was ruined, so the adventure could not go on.",
                ),
                (
                    "Why is the ending a bad ending?",
                    f"It is a bad ending because they had to turn back and never found {quest.prize}. The mistake did not just make a mess for one moment; it ended the whole adventure.",
                ),
                (
                    f"How did the story end?",
                    f"They went home without the secret place, and the mink vanished ahead of them. The last image is of a ruined map and a child who understands that rushing made the day smaller.",
                ),
            ]
        )
    else:
        out.extend(
            [
                (
                    f"How did {child.id} stay safe?",
                    f"{child.id} listened to Nana and used {gear.phrase}. That made the crossing safer, so the chase stayed exciting without turning into trouble.",
                ),
                (
                    "Did they find treasure?",
                    f"No, they only found tracks and a quiet place to eat lunch. But they kept their map and came home safely, which became the real success of the day.",
                ),
            ]
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mink", "adventure"}
    terrain = f["terrain"].id
    if terrain in {"creek", "bog", "ravine"}:
        tags.add(terrain)
    for tag in f["gear"].tags:
        if tag in KNOWLEDGE:
            tags.add(tag)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
shortcut_fits(Tg, Sc) :- terrain_type(Tg, Ty), shortcut_type(Sc, Ty).
gear_works(Tg, G) :- terrain_type(Tg, Ty), protects(G, Ty).
valid(S, Tg, Sc, G) :- setting(S), terrain(Tg), shortcut(Sc), gear(G),
                       shortcut_fits(Tg, Sc), gear_works(Tg, G).

slipped :- not obeys, chosen_terrain(Tg), severity(Tg, N), N >= 1.
quest_failed :- slipped.
outcome(safe) :- obeys.
outcome(bad) :- not obeys, quest_failed.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, terrain in TERRAINS.items():
        lines.append(asp.fact("terrain", tid))
        lines.append(asp.fact("terrain_type", tid, terrain.terrain_type))
        lines.append(asp.fact("severity", tid, terrain.severity))
    for sid, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        lines.append(asp.fact("shortcut_type", sid, shortcut.for_type))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for p in sorted(gear.protects):
            lines.append(asp.fact("protects", gid, p))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra_lines = [asp.fact("chosen_terrain", params.terrain)]
    if params.obeys:
        extra_lines.append(asp.fact("obeys"))
    model = asp.one_model(asp_program("\n".join(extra_lines), "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="marsh",
        terrain="creek",
        shortcut="log",
        gear="walking_staff",
        quest="moonpool",
        child_name="Mira",
        child_gender="girl",
        obeys=False,
    ),
    StoryParams(
        setting="pinewoods",
        terrain="bog",
        shortcut="fern_tunnel",
        gear="bog_board",
        quest="foxglove_arch",
        child_name="Finn",
        child_gender="boy",
        obeys=False,
    ),
    StoryParams(
        setting="cliffs",
        terrain="ravine",
        shortcut="goat_path",
        gear="rope_belt",
        quest="salt_cave",
        child_name="Lina",
        child_gender="girl",
        obeys=False,
    ),
    StoryParams(
        setting="marsh",
        terrain="bog",
        shortcut="fern_tunnel",
        gear="grip_boots",
        quest="moonpool",
        child_name="Theo",
        child_gender="boy",
        obeys=True,
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "safe" if params.obeys else "bad"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: Nana, a blur, a mink, and an adventure that can end badly."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--terrain", choices=TERRAINS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument(
        "--obeys",
        action="store_true",
        help="child listens to Nana; omitted means the bad-ending shortcut branch",
    )
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.terrain and args.shortcut:
        terrain = TERRAINS[args.terrain]
        shortcut = SHORTCUTS[args.shortcut]
        if not shortcut_fits(terrain, shortcut):
            raise StoryError(explain_shortcut(terrain, shortcut))
    if args.terrain and args.gear:
        terrain = TERRAINS[args.terrain]
        gear = GEAR[args.gear]
        if not gear_works(terrain, gear):
            raise StoryError(explain_gear(terrain, gear))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.terrain is None or combo[1] == args.terrain)
        and (args.shortcut is None or combo[2] == args.shortcut)
        and (args.gear is None or combo[3] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, terrain_id, shortcut_id, gear_id = rng.choice(sorted(combos))
    quest_id = args.quest or rng.choice(sorted(QUESTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    obeys = bool(args.obeys)
    return StoryParams(
        setting=setting_id,
        terrain=terrain_id,
        shortcut=shortcut_id,
        gear=gear_id,
        quest=quest_id,
        child_name=name,
        child_gender=gender,
        obeys=obeys,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        terrain = TERRAINS[params.terrain]
        shortcut = SHORTCUTS[params.shortcut]
        gear = GEAR[params.gear]
        quest = QUESTS[params.quest]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not shortcut_fits(terrain, shortcut):
        raise StoryError(explain_shortcut(terrain, shortcut))
    if not gear_works(terrain, gear):
        raise StoryError(explain_gear(terrain, gear))

    world = tell(
        setting=setting,
        terrain=terrain,
        shortcut=shortcut,
        gear=gear,
        quest=quest,
        child_name=params.child_name,
        child_gender=params.child_gender,
        obeys=params.obeys,
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
        print("MISMATCH in compatible combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    default_args = build_parser().parse_args([])
    for seed in range(20):
        try:
            p = resolve_params(default_args, random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError as err:
            rc = 1
            print("Unexpected resolve failure during verify:", err)
            break

    for p in cases:
        a = asp_outcome(p)
        b = outcome_of(p)
        if a != b:
            rc = 1
            print(f"MISMATCH outcome for {p}: asp={a} python={b}")

    try:
        smoke_params = resolve_params(default_args, random.Random(123))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        emit(smoke_sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    if rc == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, terrain, shortcut, gear) combos:\n")
        for setting_id, terrain_id, shortcut_id, gear_id in combos:
            print(f"  {setting_id:9} {terrain_id:7} {shortcut_id:11} {gear_id}")
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
            header = (
                f"### {p.child_name}: {p.quest} via {p.terrain} "
                f"({p.shortcut}, {p.gear}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
