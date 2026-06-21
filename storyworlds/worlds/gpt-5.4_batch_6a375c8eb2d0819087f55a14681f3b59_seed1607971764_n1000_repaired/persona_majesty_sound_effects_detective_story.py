#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/persona_majesty_sound_effects_detective_story.py
============================================================================

A standalone storyworld for a tiny child-facing detective story domain:
a young sleuth adopts a detective persona, notices that a royal play prop is
missing, follows a noisy clue, and solves the case in time for a pretend
majesty scene.

The world model is small and classical:

- a mover can only carry props light enough for it
- each mover can only reach some kinds of hiding spots
- a setting only affords some hiding spots
- a retrieval tool must actually reach the hiding spot

The prose is driven by the simulated state: worry rises when the prop goes
missing, a sound clue emerges from the world, the detective listens, the clue
points to the hiding place, and the correct tool lets the child recover the
prop.

Run it
------
    python storyworlds/worlds/gpt-5.4/persona_majesty_sound_effects_detective_story.py
    python storyworlds/worlds/gpt-5.4/persona_majesty_sound_effects_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/persona_majesty_sound_effects_detective_story.py --qa --seed 7
    python storyworlds/worlds/gpt-5.4/persona_majesty_sound_effects_detective_story.py --trace
    python storyworlds/worlds/gpt-5.4/persona_majesty_sound_effects_detective_story.py --asp
    python storyworlds/worlds/gpt-5.4/persona_majesty_sound_effects_detective_story.py --verify
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)
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
    scene: str
    royal_event: str
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
class MissingThing:
    id: str
    label: str
    phrase: str
    weight: int
    sound: str
    royal_use: str
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
class Mover:
    id: str
    label: str
    phrase: str
    power: int
    reaches: set[str] = field(default_factory=set)
    steps: str = ""
    likes: str = ""
    sound: str = ""
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
class Spot:
    id: str
    label: str
    phrase: str
    reach: str = ""
    shadow: bool = False
    hint: str = ""
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
    reaches: set[str] = field(default_factory=set)
    action: str = ""
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


def _r_noise(world: World) -> list[str]:
    item = world.get("item")
    mover = world.get("mover")
    detective = world.get("detective")
    helper = world.get("helper")
    if item.meters["misplaced"] < THRESHOLD or item.meters["found"] >= THRESHOLD:
        return []
    sig = ("noise", world.facts["actual_spot"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["mystery"] += 1
    detective.memes["curiosity"] += 1
    helper.memes["worry"] += 1
    world.facts["combined_sound"] = f"{mover.attrs['sound_word']}! {item.attrs['sound_word']}!"
    return ["__noise__"]


def _r_found(world: World) -> list[str]:
    item = world.get("item")
    detective = world.get("detective")
    helper = world.get("helper")
    if world.facts["inspected_spot"] != world.facts["actual_spot"]:
        return []
    if not world.facts["tool_works"]:
        return []
    if item.meters["found"] >= THRESHOLD:
        return []
    sig = ("found", world.facts["actual_spot"], world.facts["tool"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["found"] += 1
    item.meters["misplaced"] = 0.0
    world.get("room").meters["mystery"] = 0.0
    detective.memes["pride"] += 1
    detective.memes["relief"] += 1
    helper.memes["worry"] = 0.0
    helper.memes["relief"] += 1
    return ["__found__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="found", tag="resolution", apply=_r_found),
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


SETTINGS = {
    "playroom": Setting(
        id="playroom",
        label="the playroom",
        scene="The reading rug had become a little palace with a blanket throne and a paper banner over the blocks.",
        royal_event="the royal welcome game",
        affords={"curtain_nook", "costume_trunk"},
        tags={"pretend_play", "indoors"},
    ),
    "library": Setting(
        id="library",
        label="the library corner",
        scene="A velvet chair stood like a throne, and a low book cart held shiny storybooks about castles and brave detectives.",
        royal_event="the storybook court",
        affords={"velvet_chair", "book_cart"},
        tags={"books", "quiet"},
    ),
    "stage": Setting(
        id="stage",
        label="the community stage",
        scene="Red curtains hung at the sides, and painted cardboard towers waited for the afternoon parade.",
        royal_event="the little parade for Her Majesty",
        affords={"curtain_nook", "high_shelf"},
        tags={"parade", "performance"},
    ),
}

ITEMS = {
    "crown": MissingThing(
        id="crown",
        label="crown",
        phrase="a bright paper crown with tiny bells",
        weight=1,
        sound="jingle-jingle",
        royal_use="so the child on the throne could look like majesty itself",
        tags={"crown", "royal", "bells"},
    ),
    "medal": MissingThing(
        id="medal",
        label="medal",
        phrase="a gold-colored medal on a ribbon",
        weight=1,
        sound="clink-clink",
        royal_use="to pin on the royal helper before the bow",
        tags={"medal", "ribbon", "metal"},
    ),
    "scepter": MissingThing(
        id="scepter",
        label="scepter",
        phrase="a wooden scepter with a silver star",
        weight=2,
        sound="tok-tok",
        royal_use="to tap the floor before the royal speech",
        tags={"scepter", "wood", "royal"},
    ),
}

MOVERS = {
    "kitten": Mover(
        id="kitten",
        label="kitten",
        phrase="a curious gray kitten",
        power=1,
        reaches={"floor", "seat", "inside"},
        steps="pitter-pat",
        likes="shiny things",
        sound="mew",
        tags={"kitten", "pet"},
    ),
    "duck": Mover(
        id="duck",
        label="wind-up duck",
        phrase="a tin wind-up duck",
        power=1,
        reaches={"floor", "inside"},
        steps="click-click",
        likes="anything that can bump and rattle",
        sound="quack-whirr",
        tags={"toy", "windup"},
    ),
    "robot": Mover(
        id="robot",
        label="rolling robot",
        phrase="a rolling toy robot with a little tray",
        power=2,
        reaches={"floor", "low", "inside"},
        steps="whirr-whirr",
        likes="important-looking treasures",
        sound="beep-beep",
        tags={"robot", "toy"},
    ),
}

SPOTS = {
    "curtain_nook": Spot(
        id="curtain_nook",
        label="curtain nook",
        phrase="the shadowy nook behind the curtain",
        reach="floor",
        shadow=True,
        hint="The curtain breathed in and out as if it were hiding a secret.",
        tags={"curtain", "shadow"},
    ),
    "costume_trunk": Spot(
        id="costume_trunk",
        label="costume trunk",
        phrase="the half-open costume trunk",
        reach="inside",
        shadow=True,
        hint="Feathers and capes peeked out from the lid.",
        tags={"trunk", "costumes"},
    ),
    "velvet_chair": Spot(
        id="velvet_chair",
        label="velvet chair",
        phrase="the deep velvet chair by the window",
        reach="seat",
        shadow=False,
        hint="One cushion had sunk lower than the other.",
        tags={"chair", "seat"},
    ),
    "book_cart": Spot(
        id="book_cart",
        label="book cart",
        phrase="the low book cart with squeaky wheels",
        reach="low",
        shadow=False,
        hint="A ribbon dangled beside the bottom shelf.",
        tags={"books", "cart"},
    ),
    "high_shelf": Spot(
        id="high_shelf",
        label="high shelf",
        phrase="the high prop shelf above the painted tower",
        reach="high",
        shadow=False,
        hint="Something up there gave a tiny knock whenever the shelf trembled.",
        tags={"shelf", "high"},
    ),
}

TOOLS = {
    "hands": Tool(
        id="hands",
        label="careful hands",
        phrase="careful hands",
        reaches={"floor", "inside", "seat", "low"},
        action="reached in with careful hands",
        tags={"search"},
    ),
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a little flashlight",
        reaches={"floor", "inside", "seat"},
        action="shined a little flashlight and reached in",
        tags={"flashlight", "light"},
    ),
    "step_stool": Tool(
        id="step_stool",
        label="step stool",
        phrase="a sturdy step stool",
        reaches={"high"},
        action="climbed onto a sturdy step stool and stretched up",
        tags={"stool", "reach"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Zoe", "Ella", "Lucy"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Theo", "Finn", "Jack"]
TRAITS = ["calm", "curious", "careful", "clever", "steady", "observant"]


def mover_can_carry(mover: Mover, item: MissingThing) -> bool:
    return mover.power >= item.weight


def mover_can_reach(mover: Mover, spot: Spot) -> bool:
    return spot.reach in mover.reaches


def tool_can_retrieve(tool: Tool, spot: Spot) -> bool:
    return spot.reach in tool.reaches


def valid_combo(setting_id: str, item_id: str, mover_id: str, spot_id: str, tool_id: str) -> bool:
    if setting_id not in SETTINGS or item_id not in ITEMS or mover_id not in MOVERS or spot_id not in SPOTS or tool_id not in TOOLS:
        return False
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    mover = MOVERS[mover_id]
    spot = SPOTS[spot_id]
    tool = TOOLS[tool_id]
    return (
        spot_id in setting.affords
        and mover_can_carry(mover, item)
        and mover_can_reach(mover, spot)
        and tool_can_retrieve(tool, spot)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id in ITEMS:
            for mover_id in MOVERS:
                for spot_id in SETTINGS[setting_id].affords:
                    for tool_id in TOOLS:
                        if valid_combo(setting_id, item_id, mover_id, spot_id, tool_id):
                            combos.append((setting_id, item_id, mover_id, spot_id, tool_id))
    return sorted(combos)


@dataclass
class StoryParams:
    setting: str
    item: str
    mover: str
    spot: str
    tool: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    grownup: str
    trait: str
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
        setting="playroom",
        item="crown",
        mover="kitten",
        spot="costume_trunk",
        tool="flashlight",
        detective_name="Lily",
        detective_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        grownup="mother",
        trait="observant",
    ),
    StoryParams(
        setting="library",
        item="medal",
        mover="robot",
        spot="book_cart",
        tool="hands",
        detective_name="Max",
        detective_gender="boy",
        helper_name="Nora",
        helper_gender="girl",
        grownup="teacher",
        trait="calm",
    ),
    StoryParams(
        setting="stage",
        item="scepter",
        mover="robot",
        spot="high_shelf",
        tool="step_stool",
        detective_name="Ava",
        detective_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
        grownup="father",
        trait="careful",
    ),
    StoryParams(
        setting="playroom",
        item="medal",
        mover="duck",
        spot="curtain_nook",
        tool="hands",
        detective_name="Sam",
        detective_gender="boy",
        helper_name="Lucy",
        helper_gender="girl",
        grownup="mother",
        trait="curious",
    ),
    StoryParams(
        setting="library",
        item="crown",
        mover="kitten",
        spot="velvet_chair",
        tool="hands",
        detective_name="Ella",
        detective_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        grownup="teacher",
        trait="steady",
    ),
]


def explain_rejection(setting_id: str, item_id: str, mover_id: str, spot_id: str, tool_id: str) -> str:
    if setting_id not in SETTINGS:
        return "(No story: unknown setting.)"
    if item_id not in ITEMS:
        return "(No story: unknown item.)"
    if mover_id not in MOVERS:
        return "(No story: unknown mover.)"
    if spot_id not in SPOTS:
        return "(No story: unknown hiding spot.)"
    if tool_id not in TOOLS:
        return "(No story: unknown retrieval tool.)"
    setting = SETTINGS[setting_id]
    item = ITEMS[item_id]
    mover = MOVERS[mover_id]
    spot = SPOTS[spot_id]
    tool = TOOLS[tool_id]
    if spot_id not in setting.affords:
        return (
            f"(No story: {setting.label} does not plausibly contain {spot.phrase}. "
            f"Pick a hiding spot the setting actually affords.)"
        )
    if not mover_can_carry(mover, item):
        return (
            f"(No story: {mover.phrase} is too weak to drag {item.phrase}. "
            f"The mystery should use a mover that could really carry the missing thing.)"
        )
    if not mover_can_reach(mover, spot):
        return (
            f"(No story: {mover.phrase} cannot get to {spot.phrase}. "
            f"The hiding place must be reachable for the mover.)"
        )
    if not tool_can_retrieve(tool, spot):
        return (
            f"(No story: {tool.phrase} would not reach {spot.phrase}. "
            f"The fix must honestly retrieve the missing thing.)"
        )
    return "(No story: this combination is not reasonable in the world model.)"


def sound_sentence(mover: Mover, item: MissingThing) -> str:
    return f"{mover.steps}! {item.sound}!"


def introduce(world: World, detective: Entity, helper: Entity, setting: Setting, item: MissingThing) -> None:
    world.say(
        f"On a bright afternoon, {detective.id} and {helper.id} were getting {setting.label} ready for {setting.royal_event}. "
        f"{setting.scene}"
    )
    world.say(
        f"{detective.id} straightened {detective.pronoun('possessive')} shoulders and put on {detective.pronoun('possessive')} best detective persona. "
        f'"No mystery is too small for me," {detective.pronoun()} whispered.'
    )
    world.say(
        f"They had set out {item.phrase} {item.royal_use}."
    )


def discover_missing(world: World, detective: Entity, helper: Entity, grownup: Entity, item: MissingThing) -> None:
    helper.memes["worry"] += 1
    world.say(
        f"But when {helper.id} turned back to the throne blanket, the {item.label} was gone."
    )
    world.say(
        f'"Oh no," said {helper.id}. "We cannot begin without it. The whole room was supposed to shine with majesty."'
    )
    world.say(
        f"{grownup.label_word.capitalize()} did not rush in with the answer. "
        f"{grownup.pronoun().capitalize()} only said, "
        f'"Detectives look with their eyes, and with their ears too."'
    )


def misplace(world: World, mover: Entity, item: Entity, spot: Spot) -> None:
    item.meters["misplaced"] += 1
    mover.meters["carrying"] += 1
    mover.attrs["hiding_spot"] = spot.id
    world.facts["actual_spot"] = spot.id
    propagate(world, narrate=False)


def listen(world: World, detective: Entity, helper: Entity, mover: Mover, item: MissingThing, spot: Spot) -> None:
    detective.memes["focus"] += 1
    world.facts["listened"] = True
    world.say(
        f"{detective.id} held up one finger. The room went still."
    )
    world.say(
        f"Then they heard it: {sound_sentence(mover, item)} coming from {spot.hint.lower()}"
    )
    if spot.shadow:
        world.say(
            f'"That sound is hiding in the dark," {detective.id} said. "{helper.id}, stay close."'
        )
    else:
        world.say(
            f'"That sound is telling on itself," {detective.id} said.'
        )


def inspect(world: World, detective: Entity, helper: Entity, tool: Tool, spot: Spot) -> None:
    world.facts["inspected_spot"] = spot.id
    world.facts["tool_works"] = tool_can_retrieve(tool, spot)
    world.say(
        f"They hurried to {spot.phrase}. {detective.id} {tool.action}."
    )
    propagate(world, narrate=False)


def reveal(world: World, detective: Entity, helper: Entity, grownup: Entity, item: MissingThing, mover: Mover, spot: Spot) -> None:
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"There it was: the {item.label}, tucked in {spot.phrase}, with {mover.phrase} beside it."
    )
    world.say(
        f"{mover.phrase.capitalize()} blinked at them. It had only followed {mover.likes}, and the noisy prize had told the whole story."
    )
    world.say(
        f'"Case solved," said {detective.id}. {grownup.label_word.capitalize()} smiled and nodded at {detective.pronoun('object')}.'
    )


def ending(world: World, detective: Entity, helper: Entity, item: MissingThing, setting: Setting, grownup: Entity) -> None:
    detective.memes["belonging"] += 1
    helper.memes["belonging"] += 1
    world.say(
        f"They set the {item.label} back where it belonged and began {setting.royal_event} at last."
    )
    world.say(
        f"When {helper.id} bowed and {detective.id} announced the royal entrance, the room felt full of laughter, light, and majesty."
    )
    world.say(
        f"After that, everyone remembered to hang the important props high or close, and {detective.id}'s detective persona became famous for listening before guessing."
    )


def tell(
    setting: Setting,
    item_cfg: MissingThing,
    mover_cfg: Mover,
    spot_cfg: Spot,
    tool_cfg: Tool,
    detective_name: str = "Lily",
    detective_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    grownup_type: str = "mother",
    trait: str = "observant",
) -> World:
    world = World(setting)
    world.facts = {
        "actual_spot": "",
        "combined_sound": "",
        "listened": False,
        "inspected_spot": "",
        "tool": tool_cfg.id,
        "tool_works": False,
    }

    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            role="detective",
            label=detective_name,
            attrs={"trait": trait},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            label=helper_name,
            attrs={},
        )
    )
    grownup = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=grownup_type,
            role="grownup",
            label="the grown-up",
            attrs={},
        )
    )
    world.add(Entity(id="room", kind="thing", type="room", label=setting.label, attrs={}))
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type=item_cfg.id,
            label=item_cfg.label,
            attrs={"sound_word": item_cfg.sound},
        )
    )
    mover = world.add(
        Entity(
            id="mover",
            kind="thing",
            type=mover_cfg.id,
            label=mover_cfg.label,
            attrs={"sound_word": mover_cfg.steps},
        )
    )

    detective.memes["confidence"] = 1.0
    helper.memes["trust"] = 1.0
    grownup.memes["calm"] = 1.0
    item.meters["misplaced"] = 0.0
    item.meters["found"] = 0.0
    mover.meters["carrying"] = 0.0
    world.get("room").meters["mystery"] = 0.0

    introduce(world, detective, helper, setting, item_cfg)
    world.para()
    discover_missing(world, detective, helper, grownup, item_cfg)
    misplace(world, mover, item, spot_cfg)
    listen(world, detective, helper, mover_cfg, item_cfg, spot_cfg)
    world.para()
    inspect(world, detective, helper, tool_cfg, spot_cfg)
    reveal(world, detective, helper, grownup, item_cfg, mover_cfg, spot_cfg)
    world.para()
    ending(world, detective, helper, item_cfg, setting, grownup)

    world.facts.update(
        setting=setting,
        item_cfg=item_cfg,
        mover_cfg=mover_cfg,
        spot_cfg=spot_cfg,
        tool_cfg=tool_cfg,
        detective=detective,
        helper=helper,
        grownup=grownup,
        solved=item.meters["found"] >= THRESHOLD,
        shadow=spot_cfg.shadow,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    item = f["item_cfg"]
    setting = f["setting"]
    mover = f["mover_cfg"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that includes the words "persona" and "majesty".',
        f"Tell a tiny mystery where {detective.id} and {helper.id} must find a missing {item.label} in {setting.label}, following a sound clue from {mover.label}.",
        f'Write a child-facing detective story with sound effects, a royal pretend-play problem, and a happy ending where listening carefully solves the case.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    grownup = f["grownup"]
    item = f["item_cfg"]
    mover = f["mover_cfg"]
    spot = f["spot_cfg"]
    tool = f["tool_cfg"]
    setting = f["setting"]
    sound = f["combined_sound"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, and {helper.id}, the friend helping with {setting.royal_event}. They were trying to find a missing {item.label} before the royal game could begin.",
        ),
        (
            f"Why were {detective.id} and {helper.id} upset when the {item.label} disappeared?",
            f"They needed the {item.label} for {setting.royal_event}, so the game could not start without it. {helper.id} worried because the room was supposed to feel full of majesty, and the missing prop spoiled that plan.",
        ),
        (
            f"What clue helped {detective.id} solve the mystery?",
            f"The clue was a sound: {sound}. {detective.id} listened instead of guessing, and the noisy clue led straight toward {spot.phrase}.",
        ),
        (
            f"Where was the {item.label}, and how did they get it back?",
            f"It was hidden in {spot.phrase}. {detective.id} used {tool.phrase} and found it there, which solved the case at once.",
        ),
        (
            f"Why was {mover.label} near the missing {item.label}?",
            f"{mover.phrase.capitalize()} had only followed {mover.likes}. The sound and the hiding place showed that it had dragged the interesting prop away without meaning to ruin the game.",
        ),
        (
            "How did the story end?",
            f"They put the {item.label} back and began {setting.royal_event}. The ending proves what changed, because the room that had felt worried now felt bright, playful, and ready for majesty again.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "crown": [
        (
            "What is a crown?",
            "A crown is something worn on the head to show a king, queen, or pretend ruler. In play, it helps children imagine a royal character."
        )
    ],
    "medal": [
        (
            "What is a medal?",
            "A medal is a round piece on a ribbon that can be given for honor or fun. It can clink when it bumps against something hard."
        )
    ],
    "scepter": [
        (
            "What is a scepter?",
            "A scepter is a special stick carried by a king or queen in stories and ceremonies. It is a sign of royal importance."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and solves puzzles. Good detectives listen, look carefully, and think before they guess."
        )
    ],
    "sound": [
        (
            "Why can sound be a clue?",
            "Sound can tell you where something is, even when you cannot see it yet. A rattle, jingle, or thump can point a detective in the right direction."
        )
    ],
    "flashlight": [
        (
            "What is a flashlight for?",
            "A flashlight helps you see in a dark place. It gives light without making a mess."
        )
    ],
    "stool": [
        (
            "What is a step stool?",
            "A step stool is a small sturdy thing you stand on to reach somewhere higher. It helps grown-ups and children reach safely when they are supervised."
        )
    ],
    "kitten": [
        (
            "Why do kittens chase shiny things?",
            "Kittens are curious and playful, so shiny or jingly things grab their attention. They often bat at little moving objects just for fun."
        )
    ],
    "windup": [
        (
            "What is a wind-up toy?",
            "A wind-up toy moves because a spring inside it is wound tight. As it unwinds, the toy can click, wobble, or whirr."
        )
    ],
    "robot": [
        (
            "Why might a toy robot move a small object?",
            "A rolling toy robot can push or carry light things if they fit on it or bump along in front of it. That is why it can become part of a tiny mystery."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "sound", "crown", "medal", "scepter", "flashlight", "stool", "kitten", "windup", "robot"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item = world.facts["item_cfg"]
    mover = world.facts["mover_cfg"]
    tool = world.facts["tool_cfg"]
    tags: set[str] = {"detective", "sound"} | set(item.tags) | set(mover.tags) | set(tool.tags)
    out: list[tuple[str, str]] = []
    if "bells" in tags:
        tags.add("crown")
    if "ribbon" in tags or "metal" in tags:
        tags.add("medal")
    if "wood" in tags:
        tags.add("scepter")
    if "light" in tags:
        tags.add("flashlight")
    if "reach" in tags:
        tags.add("stool")
    if "pet" in tags:
        tags.add("kitten")
    if "windup" in tags:
        tags.add("windup")
    if "robot" in tags:
        tags.add("robot")
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in world.facts.items() if k not in {'detective', 'helper', 'grownup', 'setting', 'item_cfg', 'mover_cfg', 'spot_cfg', 'tool_cfg'})}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
can_carry(M, I) :- mover(M), item(I), power(M, PM), weight(I, WI), PM >= WI.
can_reach(M, S) :- mover(M), spot(S), mover_reach(M, R), spot_reach(S, R).
tool_works(T, S) :- tool(T), spot(S), tool_reach(T, R), spot_reach(S, R).

valid(Se, I, M, S, T) :-
    setting(Se), item(I), mover(M), spot(S), tool(T),
    affords(Se, S),
    can_carry(M, I),
    can_reach(M, S),
    tool_works(T, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spot_id in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, spot_id))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("weight", iid, item.weight))
    for mid, mover in MOVERS.items():
        lines.append(asp.fact("mover", mid))
        lines.append(asp.fact("power", mid, mover.power))
        for reach in sorted(mover.reaches):
            lines.append(asp.fact("mover_reach", mid, reach))
    for sid, spot in SPOTS.items():
        lines.append(asp.fact("spot", sid))
        lines.append(asp.fact("spot_reach", sid, spot.reach))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for reach in sorted(tool.reaches):
            lines.append(asp.fact("tool_reach", tid, reach))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child detective follows a sound clue to solve a tiny royal mystery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--mover", choices=MOVERS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--grownup", choices=["mother", "father", "teacher"])
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit = [args.setting, args.item, args.mover, args.spot, args.tool]
    if all(x is not None for x in explicit):
        if not valid_combo(args.setting, args.item, args.mover, args.spot, args.tool):
            raise StoryError(explain_rejection(args.setting, args.item, args.mover, args.spot, args.tool))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.mover is None or combo[2] == args.mover)
        and (args.spot is None or combo[3] == args.spot)
        and (args.tool is None or combo[4] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, mover_id, spot_id, tool_id = rng.choice(combos)
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    detective_name = _pick_name(rng, detective_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=detective_name)
    grownup = args.grownup or rng.choice(["mother", "father", "teacher"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        item=item_id,
        mover=mover_id,
        spot=spot_id,
        tool=tool_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        grownup=grownup,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.setting, params.item, params.mover, params.spot, params.tool):
        raise StoryError(explain_rejection(params.setting, params.item, params.mover, params.spot, params.tool))
    try:
        setting = SETTINGS[params.setting]
        item = ITEMS[params.item]
        mover = MOVERS[params.mover]
        spot = SPOTS[params.spot]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(No story: invalid parameter {err.args[0]!r}.)") from err

    world = tell(
        setting=setting,
        item_cfg=item,
        mover_cfg=mover,
        spot_cfg=spot,
        tool_cfg=tool,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        grownup_type=params.grownup,
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


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "persona" not in sample.story or "majesty" not in sample.story:
            raise StoryError("smoke test story missing required story text or seed words")
        text = sample.story
        if not isinstance(text, str) or len(text) < 40:
            raise StoryError("smoke test story too short")
        if sample.world is None:
            raise StoryError("smoke test did not preserve world")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        parser = build_parser()
        params = resolve_params(parser.parse_args([]), random.Random(17))
        params.seed = 17
        sample = generate(params)
        if not sample.story_qa or not sample.world_qa or not sample.prompts:
            raise StoryError("default-generation smoke test missing QA/prompts")
        print("OK: default resolve/generate smoke test succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, mover, spot, tool) combos:\n")
        for setting_id, item_id, mover_id, spot_id, tool_id in combos:
            print(f"  {setting_id:8} {item_id:7} {mover_id:7} {spot_id:13} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.item} on {p.setting} ({p.mover} -> {p.spot}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
