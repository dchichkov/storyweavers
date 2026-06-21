#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sonar_stroke_mystery_to_solve_magic_bad.py
====================================================================

A standalone story world for a tall-tale mystery on enchanted waters: a child
rows out to solve a strange local problem using a magic tool, faces a water
hazard, and either restores the wonder or comes home with a bad ending and an
unsolved mystery.

Seed ingredients rebuilt as a world model:
- required words: "sonar", "stroke"
- features: Mystery to Solve, Magic, Bad Ending
- style: Tall Tale

Premise:
    In an outrageous waterside town, something impossible has gone wrong:
    a bell beneath the water has gone silent, a giant silver fish has vanished,
    or the ferry lights have disappeared into a wall of fog. A child rows out
    with a magic tool to solve the mystery. The same trip always carries some
    risk -- whirlpool, fog maze, or sleepy current. If the chosen helper is
    strong enough for the danger, the mystery is solved in a bright tall-tale
    ending. If not, the boat drifts, the tool is lost, and the town keeps its
    trouble.

Run it
------
    python storyworlds/worlds/gpt-5.4/sonar_stroke_mystery_to_solve_magic_bad.py
    python storyworlds/worlds/gpt-5.4/sonar_stroke_mystery_to_solve_magic_bad.py --all
    python storyworlds/worlds/gpt-5.4/sonar_stroke_mystery_to_solve_magic_bad.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sonar_stroke_mystery_to_solve_magic_bad.py --trace
    python storyworlds/worlds/gpt-5.4/sonar_stroke_mystery_to_solve_magic_bad.py --asp
    python storyworlds/worlds/gpt-5.4/sonar_stroke_mystery_to_solve_magic_bad.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    tags: set[str] = field(default_factory=set)
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
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    name: str
    brag: str
    water: str
    dock: str
    affords_mysteries: set[str] = field(default_factory=set)
    affords_risks: set[str] = field(default_factory=set)
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


@dataclass
class Mystery:
    id: str
    rumor: str
    object_label: str
    object_the: str
    hidden_as: str
    cause: str
    fix: str
    restored: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.object_the[0].upper() + self.object_the[1:]
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
class MagicTool:
    id: str
    label: str
    phrase: str
    action: str
    clue_line: str
    detects: set[str] = field(default_factory=set)
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
class Risk:
    id: str
    label: str
    arrive: str
    severity: int
    danger_line: str
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
class Helper:
    id: str
    label: str
    entrance: str
    success: str
    fail: str
    power: int
    counters: set[str] = field(default_factory=set)
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


def _r_drift(world: World) -> list[str]:
    boat = world.entities.get("boat")
    hero = world.entities.get("hero")
    if boat is None or hero is None:
        return []
    if boat.meters["hazard_active"] < THRESHOLD:
        return []
    sig = ("drift", int(boat.meters["hazard_level"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boat.meters["drift"] += 1
    hero.memes["worry"] += 1
    hero.memes["awe"] += 1
    return ["__drift__"]


def _r_reveal(world: World) -> list[str]:
    clue = world.entities.get("clue")
    mystery = world.entities.get("mystery")
    hero = world.entities.get("hero")
    if clue is None or mystery is None or hero is None:
        return []
    if clue.meters["found"] < THRESHOLD:
        return []
    sig = ("reveal", mystery.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mystery.meters["revealed"] += 1
    hero.memes["hope"] += 1
    return ["__reveal__"]


def _r_loss(world: World) -> list[str]:
    boat = world.entities.get("boat")
    tool = world.entities.get("tool")
    hero = world.entities.get("hero")
    if boat is None or tool is None or hero is None:
        return []
    if boat.meters["drift"] < THRESHOLD or boat.meters["swamped"] < THRESHOLD:
        return []
    sig = ("loss", tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tool.meters["lost"] += 1
    hero.memes["grief"] += 1
    return ["__loss__"]


CAUSAL_RULES = [
    Rule(name="drift", tag="physical", apply=_r_drift),
    Rule(name="reveal", tag="mystery", apply=_r_reveal),
    Rule(name="loss", tag="physical", apply=_r_loss),
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


SETTINGS = {
    "cloud_lake": Setting(
        id="cloud_lake",
        name="Cloud Lake",
        brag="On Cloud Lake, a single splash could wash the freckles off the moon.",
        water="the lake shone like a silver skillet tipped toward the sky",
        dock="the crooked cedar dock",
        affords_mysteries={"silent_bell", "missing_sturgeon"},
        affords_risks={"whirlpool", "fog_maze"},
    ),
    "thunder_marsh": Setting(
        id="thunder_marsh",
        name="Thunder Marsh",
        brag="In Thunder Marsh, the frogs croaked so loud they could rattle loose buttons off a coat.",
        water="the marsh water lay black and glossy as a sleepy mirror",
        dock="the mossy ferry post",
        affords_mysteries={"vanished_lights", "missing_sturgeon"},
        affords_risks={"sleep_current", "fog_maze"},
    ),
    "moon_river": Setting(
        id="moon_river",
        name="Moon River Bend",
        brag="At Moon River Bend, every reed leaned east to hear the gossip of the tide.",
        water="the river curled in bright loops like a silver ribbon trying to tie itself",
        dock="the old stone landing",
        affords_mysteries={"silent_bell", "vanished_lights"},
        affords_risks={"whirlpool", "sleep_current"},
    ),
}

MYSTERIES = {
    "silent_bell": Mystery(
        id="silent_bell",
        rumor="the bell under the shoal had stopped ringing at dawn",
        object_label="bell",
        object_the="the silver bell",
        hidden_as="underwater",
        cause="a giant knot of riverweed had wrapped the bell rope and muffled every note",
        fix="cut the weed and free the bell rope",
        restored="The silver bell boomed again, and its note rolled over the water like a brass sunrise.",
        tags={"bell", "water"},
    ),
    "missing_sturgeon": Mystery(
        id="missing_sturgeon",
        rumor="the moon-backed sturgeon had quit leaping beside the boats",
        object_label="sturgeon",
        object_the="the moon-backed sturgeon",
        hidden_as="underwater",
        cause="a black net of snag-vine had trapped the deep channel where the fish liked to turn",
        fix="slice the snag-vine net and open the deep channel",
        restored="Up shot the moon-backed sturgeon, high enough to wink at a cloud before it splashed back down.",
        tags={"fish", "water"},
    ),
    "vanished_lights": Mystery(
        id="vanished_lights",
        rumor="the ferry lights had vanished from the fog line",
        object_label="ferry lights",
        object_the="the ferry lights",
        hidden_as="fog",
        cause="a fog sprite had pocketed the lantern-stars and hidden them in a white wall of mist",
        fix="coax the sprite to spill the lantern-stars back into their glass cups",
        restored="The ferry lights blinked awake in a golden row, and the whole shoreline looked stitched with fireflies.",
        tags={"light", "fog"},
    ),
}

MAGIC_TOOLS = {
    "echo_shell": MagicTool(
        id="echo_shell",
        label="echo shell",
        phrase="an echo shell as big as a dinner plate",
        action="held the shell to the water, and it began to sing sonar into the deep",
        clue_line="The sonar hum bounced back and drew a bright secret shape under the boat.",
        detects={"underwater"},
        tags={"sonar", "shell", "magic"},
    ),
    "star_glass": MagicTool(
        id="star_glass",
        label="star-glass",
        phrase="a square of star-glass that caught even sneaky light",
        action="lifted the star-glass to the mist, and every hidden gleam came peeping through",
        clue_line="Little sparks lined up inside the glass and pointed straight into the white murk.",
        detects={"fog"},
        tags={"glass", "magic", "light"},
    ),
    "whisper_reed": MagicTool(
        id="whisper_reed",
        label="whisper reed",
        phrase="a whisper reed that listened harder than a nosy aunt",
        action="dipped the reed over the side, and it quivered with gossip from the current",
        clue_line="The reed trembled toward the trouble as if the river itself had tattled.",
        detects={"underwater", "fog"},
        tags={"reed", "magic", "water"},
    ),
}

RISKS = {
    "whirlpool": Risk(
        id="whirlpool",
        label="whirlpool",
        arrive="a whirlpool opened its round blue eye and began to suck at the skiff",
        severity=2,
        danger_line="The boat spun so fast the oars hummed like fiddles.",
        tags={"whirlpool", "water"},
    ),
    "fog_maze": Risk(
        id="fog_maze",
        label="fog maze",
        arrive="a fog maze rose in folding white walls taller than barns",
        severity=1,
        danger_line="Every turn looked like the last, and the shore kept slipping away.",
        tags={"fog", "maze"},
    ),
    "sleep_current": Risk(
        id="sleep_current",
        label="sleepy current",
        arrive="a sleepy current rolled under the skiff and pulled at it like a heavy blanket",
        severity=2,
        danger_line="Each oar stroke grew slow and syrupy, and the bow forgot where it was going.",
        tags={"current", "water"},
    ),
}

HELPERS = {
    "iron_catfish": Helper(
        id="iron_catfish",
        label="iron catfish",
        entrance="an iron catfish rose from the deep with whiskers stiff as fence wire",
        success="nudged the skiff out of the spinning water with one mighty shove of its tail",
        fail="but even its iron head could not stop the pull in time",
        power=3,
        counters={"whirlpool"},
        tags={"catfish", "water", "magic"},
    ),
    "lantern_heron": Helper(
        id="lantern_heron",
        label="lantern heron",
        entrance="a lantern heron stepped out of nowhere, wearing a glow under each wing",
        success="walked ahead through the mist and opened a bright path home",
        fail="but its wing-lamps blurred and vanished in the thick white walls",
        power=2,
        counters={"fog_maze"},
        tags={"heron", "fog", "light", "magic"},
    ),
    "drum_beaver": Helper(
        id="drum_beaver",
        label="drum beaver",
        entrance="a drum beaver slapped the water with its tail until the river woke up",
        success="beat a hard rhythm that broke the sleepy pull of the current",
        fail="but the lazy water only yawned wider around the skiff",
        power=3,
        counters={"sleep_current"},
        tags={"beaver", "current", "magic"},
    ),
}

GIRL_NAMES = ["Mabel", "Nell", "Ada", "June", "Pearl", "Dora", "Ivy", "Mae"]
BOY_NAMES = ["Eli", "Bo", "Jasper", "Otis", "Finn", "Cal", "Toby", "Huck"]
TRAITS = ["brave", "curious", "stout-hearted", "quick-thinking", "restless", "bold"]
ELDER_TYPES = ["mother", "father", "aunt", "uncle"]


def setting_supports(setting: Setting, mystery: Mystery, risk: Risk) -> bool:
    return mystery.id in setting.affords_mysteries and risk.id in setting.affords_risks


def tool_matches(tool: MagicTool, mystery: Mystery) -> bool:
    return mystery.hidden_as in tool.detects


def helper_matches(helper: Helper, risk: Risk) -> bool:
    return risk.id in helper.counters


def risk_level(risk: Risk, extra_strokes: int) -> int:
    return risk.severity + extra_strokes


def rescued(helper: Helper, risk: Risk, extra_strokes: int) -> bool:
    return helper.power >= risk_level(risk, extra_strokes)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            for tid, tool in MAGIC_TOOLS.items():
                for rid, risk in RISKS.items():
                    for hid, helper in HELPERS.items():
                        if setting_supports(setting, mystery, risk) and tool_matches(tool, mystery) and helper_matches(helper, risk):
                            combos.append((sid, mid, tid, rid, hid))
    return combos


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    risk: str
    helper: str
    hero: str
    gender: str
    elder: str
    trait: str
    extra_strokes: int = 0
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


def opening(world: World, hero: Entity, elder: Entity, mystery: Mystery) -> None:
    world.say(world.setting.brag)
    world.say(
        f"That morning, {world.setting.water}, and folks at {world.setting.dock} kept whispering that {mystery.rumor}."
    )
    world.say(
        f"{hero.id}, a {next((t for t in hero.traits if t), 'brave')} little {hero.type}, heard the whisper and decided the water would not keep its secret all day."
    )
    world.say(
        f'"Wait for sense as well as courage," said {hero.pronoun("possessive")} {elder.label_word}, but {hero.id} was already squinting at the shine on the water.'
    )


def arm_for_trip(world: World, hero: Entity, elder: Entity, tool: MagicTool, mystery: Mystery, risk: Risk) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"{elder.label_word.capitalize()} handed {hero.pronoun('object')} {tool.phrase}. "
        f'"This will help you find {mystery.object_the}," {elder.pronoun()} said. '
        f'"But mind the {risk.label} if it wakes."'
    )
    world.say(
        f"{hero.id} climbed into a skiff no bigger than a bathtub and no more afraid of weather than a boot."
    )


def row_out(world: World, hero: Entity, boat: Entity, tool: MagicTool) -> None:
    boat.meters["strokes"] += 3
    hero.memes["pride"] += 1
    world.say(
        f"With every oar stroke, the skiff skipped farther than a sensible boat had any right to go."
    )
    world.say(
        f"{hero.id} {tool.action}"
    )


def find_clue(world: World, hero: Entity, clue: Entity, mystery: Mystery, tool: MagicTool) -> None:
    clue.meters["found"] += 1
    propagate(world, narrate=False)
    hero.memes["wonder"] += 1
    world.say(tool.clue_line)
    world.say(
        f"Soon {hero.id} understood the trouble: {mystery.cause}."
    )


def danger_wakes(world: World, hero: Entity, boat: Entity, risk: Risk, extra_strokes: int) -> None:
    boat.meters["hazard_active"] = 1.0
    boat.meters["hazard_level"] = float(risk_level(risk, extra_strokes))
    boat.meters["strokes"] += float(extra_strokes)
    world.facts["risk_level"] = risk_level(risk, extra_strokes)
    propagate(world, narrate=False)
    world.say(
        f"But before {hero.id} could act, {risk.arrive}."
    )
    world.say(risk.danger_line)
    if extra_strokes > 0:
        world.say(
            f"{hero.id} took {extra_strokes} more hard stroke{'s' if extra_strokes != 1 else ''} trying to outrun it, and that only made the danger meaner."
        )


def rescue_and_fix(world: World, hero: Entity, helper: Helper, mystery: Mystery, boat: Entity) -> None:
    mystery_ent = world.get("mystery")
    town = world.get("town")
    boat.meters["drift"] = 0.0
    boat.meters["safe"] += 1
    mystery_ent.meters["restored"] += 1
    town.memes["relief"] += 1
    hero.memes["relief"] += 1
    hero.memes["pride"] = 0.0
    world.say(
        f"Just then, {helper.entrance} and {helper.success}."
    )
    world.say(
        f"{hero.id} {mystery.fix}, and {mystery.restored}"
    )
    world.say(
        f"When the skiff came gliding back to {world.setting.dock}, everybody cheered so loudly that even the tadpoles must have known the mystery was solved."
    )


def fail_and_lose(world: World, hero: Entity, helper: Helper, mystery: Mystery, boat: Entity, tool_ent: Entity) -> None:
    town = world.get("town")
    boat.meters["swamped"] += 1
    propagate(world, narrate=False)
    hero.memes["fear"] += 1
    town.memes["sadness"] += 1
    world.say(
        f"Just then, {helper.entrance}, {helper.fail}."
    )
    if tool_ent.meters["lost"] >= THRESHOLD:
        world.say(
            f"The skiff tipped, the {tool_ent.label} flew from {hero.id}'s hands, and the dark water swallowed it without a burp."
        )
    world.say(
        f"{hero.id} made it back wet and empty, but {mystery.object_the} stayed lost in its trouble."
    )
    world.say(
        f"That night, {world.setting.name} felt smaller. The grown-ups spoke softly, the shore stayed dim or silent, and nobody could pretend the mystery had been beaten."
    )


def tell(
    setting: Setting,
    mystery: Mystery,
    tool: MagicTool,
    risk: Risk,
    helper: Helper,
    hero_name: str = "Mabel",
    gender: str = "girl",
    elder_type: str = "aunt",
    trait: str = "curious",
    extra_strokes: int = 0,
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=gender,
            label=hero_name,
            role="hero",
            traits=[trait],
            tags={"child"},
        )
    )
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type=elder_type,
            label=f"the {elder_type}",
            role="elder",
            tags={"adult"},
        )
    )
    boat = world.add(
        Entity(
            id="boat",
            type="skiff",
            label="skiff",
            role="boat",
            tags={"boat", "water"},
        )
    )
    mystery_ent = world.add(
        Entity(
            id="mystery",
            type="mystery",
            label=mystery.object_label,
            role="mystery",
            tags=set(mystery.tags),
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            type="clue",
            label="clue",
            role="clue",
            tags={"clue"},
        )
    )
    tool_ent = world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool.label,
            role="tool",
            tags=set(tool.tags),
        )
    )
    helper_ent = world.add(
        Entity(
            id="helper",
            type="helper",
            label=helper.label,
            role="helper",
            tags=set(helper.tags),
        )
    )
    risk_ent = world.add(
        Entity(
            id="risk",
            type="risk",
            label=risk.label,
            role="risk",
            tags=set(risk.tags),
        )
    )
    town = world.add(
        Entity(
            id="town",
            type="town",
            label=setting.name,
            role="town",
            tags={"town"},
        )
    )

    world.facts.update(
        setting=setting,
        mystery_cfg=mystery,
        tool_cfg=tool,
        risk_cfg=risk,
        helper_cfg=helper,
        hero=hero,
        elder=elder,
        boat=boat,
        mystery=mystery_ent,
        clue=clue,
        tool=tool_ent,
        helper=helper_ent,
        risk=risk_ent,
        town=town,
        extra_strokes=extra_strokes,
    )

    opening(world, hero, elder, mystery)
    world.para()
    arm_for_trip(world, hero, elder, tool, mystery, risk)
    row_out(world, hero, boat, tool)
    find_clue(world, hero, clue, mystery, tool)
    world.para()
    danger_wakes(world, hero, boat, risk, extra_strokes)

    good_end = rescued(helper, risk, extra_strokes)
    world.para()
    if good_end:
        rescue_and_fix(world, hero, helper, mystery, boat)
        outcome = "solved"
    else:
        fail_and_lose(world, hero, helper, mystery, boat, tool_ent)
        outcome = "lost"

    world.facts.update(
        outcome=outcome,
        clue_found=clue.meters["found"] >= THRESHOLD,
        revealed=mystery_ent.meters["revealed"] >= THRESHOLD,
        restored=mystery_ent.meters["restored"] >= THRESHOLD,
        tool_lost=tool_ent.meters["lost"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "sonar": [
        (
            "What is sonar?",
            "Sonar is a way of sending sound through water and listening for the sound that bounces back. Boats and submarines can use it to learn what is hidden below them.",
        )
    ],
    "whirlpool": [
        (
            "What is a whirlpool?",
            "A whirlpool is water spinning in a tight circle. It can pull a small boat off course and make rowing very hard.",
        )
    ],
    "fog": [
        (
            "Why is fog hard to travel through?",
            "Fog is made of tiny drops of water hanging in the air, and it hides what is far away. When you cannot see the shore or the path, it is easy to get lost.",
        )
    ],
    "current": [
        (
            "What is a current in a river?",
            "A current is moving water that pushes things along. A strong current can carry a boat even when someone is trying to row another way.",
        )
    ],
    "bell": [
        (
            "Why does a bell stop ringing underwater?",
            "A bell can stop ringing clearly if something tangles or blocks the part that moves it. If the rope or clapper cannot move, the sound becomes weak or stops.",
        )
    ],
    "fish": [
        (
            "Why might fish leave a place in the water?",
            "Fish move away when their path is blocked or the water no longer feels safe. If weeds or nets fill a channel, they often swim somewhere easier.",
        )
    ],
    "light": [
        (
            "Why do lights help people near water at night?",
            "Lights show where the shore, dock, or safe path is. Without them, it is much easier to lose direction in the dark.",
        )
    ],
    "boat": [
        (
            "What does an oar stroke do?",
            "An oar stroke pushes water backward so a boat can move forward or turn. Many steady strokes help a small boat travel where the rower wants it to go.",
        )
    ],
    "magic": [
        (
            "What is magic in a story like this?",
            "Magic is something impossible that the story treats as real, like a talking river tool or a glowing bird. It makes the world feel bigger than ordinary life.",
        )
    ],
}
KNOWLEDGE_ORDER = ["sonar", "boat", "whirlpool", "fog", "current", "bell", "fish", "light", "magic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery_cfg"]
    tool = f["tool_cfg"]
    risk = f["risk_cfg"]
    if f["outcome"] == "lost":
        return [
            'Write a tall-tale mystery for a young child that uses the word "sonar" and the word "stroke".',
            f"Tell a magical water mystery where {hero.label} rows out with a {tool.label} to solve why {mystery.rumor}, but a {risk.label} turns the trip into a bad ending.",
            f"Write a story about a child trying to solve a wonder-filled mystery on wild water, with a magical clue, a real danger, and a sad ending where the problem is not fixed.",
        ]
    return [
        'Write a tall-tale mystery for a young child that uses the word "sonar" and the word "stroke".',
        f"Tell a magical water mystery where {hero.label} rows out with a {tool.label} to solve why {mystery.rumor}, and a strange helper saves the day.",
        f"Write a story about a child solving an impossible mystery on enchanted water, with big tall-tale images, a magical clue, and a bright ending that proves the trouble is gone.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    mystery = f["mystery_cfg"]
    tool = f["tool_cfg"]
    risk = f["risk_cfg"]
    helper = f["helper_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child who rowed out to solve a mystery on {f['setting'].name}. {elder.label_word.capitalize()} helped at the start by giving {hero.pronoun('object')} a magical tool.",
        ),
        (
            "What was the mystery?",
            f"The mystery was that {mystery.rumor}. {hero.label} went out because the town could feel that something important had gone wrong.",
        ),
        (
            f"How did {hero.label} look for the answer?",
            f"{hero.label} used the {tool.label} while rowing the skiff. The magic tool helped reveal that {mystery.cause}.",
        ),
        (
            f"What danger appeared during the trip?",
            f"A {risk.label} rose up while {hero.label} was still on the water. That danger made the skiff drift and turned the mystery hunt into a race against trouble.",
        ),
    ]
    if outcome == "solved":
        qa.extend(
            [
                (
                    "How was the mystery solved?",
                    f"{helper.entrance.capitalize()} and {helper.success}. Because the helper beat the danger, {hero.label} could {mystery.fix} and set things right.",
                ),
                (
                    "How did the ending prove that things changed?",
                    f"The ending proved it because {mystery.restored} When the skiff returned, the whole town could hear or see that the trouble was over.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    "Why was this a bad ending?",
                    f"It was a bad ending because the danger beat the rescue. {hero.label} got back safely, but the {tool.label} was lost and {mystery.object_the} stayed trapped in its trouble.",
                ),
                (
                    "What was still wrong at the end?",
                    f"{mystery.The} was still not fixed, so the town stayed dimmer, quieter, or sadder than before. The last image matters because it shows the mystery remained unsolved.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"boat", "magic"}
    if "sonar" in f["tool_cfg"].tags:
        tags.add("sonar")
    if f["risk_cfg"].id == "whirlpool":
        tags.add("whirlpool")
    if f["risk_cfg"].id == "fog_maze":
        tags.add("fog")
    if f["risk_cfg"].id == "sleep_current":
        tags.add("current")
    if f["mystery_cfg"].id == "silent_bell":
        tags.add("bell")
    if f["mystery_cfg"].id == "missing_sturgeon":
        tags.add("fish")
    if f["mystery_cfg"].id == "vanished_lights":
        tags.add("light")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="cloud_lake",
        mystery="silent_bell",
        tool="echo_shell",
        risk="whirlpool",
        helper="iron_catfish",
        hero="Mabel",
        gender="girl",
        elder="aunt",
        trait="quick-thinking",
        extra_strokes=0,
    ),
    StoryParams(
        setting="thunder_marsh",
        mystery="vanished_lights",
        tool="star_glass",
        risk="fog_maze",
        helper="lantern_heron",
        hero="Bo",
        gender="boy",
        elder="uncle",
        trait="curious",
        extra_strokes=1,
    ),
    StoryParams(
        setting="moon_river",
        mystery="silent_bell",
        tool="whisper_reed",
        risk="whirlpool",
        helper="iron_catfish",
        hero="Ada",
        gender="girl",
        elder="father",
        trait="bold",
        extra_strokes=2,
    ),
    StoryParams(
        setting="thunder_marsh",
        mystery="missing_sturgeon",
        tool="echo_shell",
        risk="sleep_current",
        helper="drum_beaver",
        hero="Otis",
        gender="boy",
        elder="mother",
        trait="brave",
        extra_strokes=0,
    ),
]


def explain_combo(setting: Setting, mystery: Mystery, tool: MagicTool, risk: Risk, helper: Helper) -> str:
    if not setting_supports(setting, mystery, risk):
        return (
            f"(No story: {setting.name} does not support that mystery and danger together. "
            f"Pick a mystery and risk that belong to the same water place.)"
        )
    if not tool_matches(tool, mystery):
        return (
            f"(No story: the {tool.label} cannot honestly find this mystery. "
            f"It does not reveal things hidden in {mystery.hidden_as}.)"
        )
    if not helper_matches(helper, risk):
        return (
            f"(No story: the {helper.label} is not a sensible helper for a {risk.label}. "
            f"Pick a helper that actually counters that danger.)"
        )
    return "(No story: this combination does not fit the world.)"


def outcome_of(params: StoryParams) -> str:
    return "solved" if rescued(HELPERS[params.helper], RISKS[params.risk], params.extra_strokes) else "lost"


ASP_RULES = r"""
valid(S, M, T, R, H) :- setting(S), mystery(M), tool(T), risk(R), helper(H),
                        affords_mystery(S, M), affords_risk(S, R),
                        detects(T, Hide), hidden_as(M, Hide),
                        counters(H, R).

danger(R, X, D) :- severity(R, S), extra_strokes(X), D = S + X.
solved :- chosen_helper(H), chosen_risk(R), extra_strokes(X),
          power(H, P), danger(R, X, D), P >= D.
outcome(solved) :- solved.
outcome(lost) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for mid in sorted(setting.affords_mysteries):
            lines.append(asp.fact("affords_mystery", sid, mid))
        for rid in sorted(setting.affords_risks):
            lines.append(asp.fact("affords_risk", sid, rid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("hidden_as", mid, mystery.hidden_as))
    for tid, tool in MAGIC_TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for hide in sorted(tool.detects):
            lines.append(asp.fact("detects", tid, hide))
    for rid, risk in RISKS.items():
        lines.append(asp.fact("risk", rid))
        lines.append(asp.fact("severity", rid, risk.severity))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("power", hid, helper.power))
        for r in sorted(helper.counters):
            lines.append(asp.fact("counters", hid, r))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_risk", params.risk),
            asp.fact("extra_strokes", params.extra_strokes),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
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
        smoke = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=False, qa=True, header="smoke")
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale mystery on enchanted water. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=MAGIC_TOOLS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--elder", choices=ELDER_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--extra-strokes", type=int, choices=[0, 1, 2], default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mystery and args.tool and args.risk and args.helper:
        setting = SETTINGS[args.setting]
        mystery = MYSTERIES[args.mystery]
        tool = MAGIC_TOOLS[args.tool]
        risk = RISKS[args.risk]
        helper = HELPERS[args.helper]
        if not (
            setting_supports(setting, mystery, risk)
            and tool_matches(tool, mystery)
            and helper_matches(helper, risk)
        ):
            raise StoryError(explain_combo(setting, mystery, tool, risk, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.tool is None or combo[2] == args.tool)
        and (args.risk is None or combo[3] == args.risk)
        and (args.helper is None or combo[4] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mystery_id, tool_id, risk_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDER_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    extra_strokes = args.extra_strokes if args.extra_strokes is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        mystery=mystery_id,
        tool=tool_id,
        risk=risk_id,
        helper=helper_id,
        hero=hero,
        gender=gender,
        elder=elder,
        trait=trait,
        extra_strokes=extra_strokes,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        mystery = MYSTERIES[params.mystery]
        tool = MAGIC_TOOLS[params.tool]
        risk = RISKS[params.risk]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Unknown story parameter: {err.args[0]})") from None

    if not (
        setting_supports(setting, mystery, risk)
        and tool_matches(tool, mystery)
        and helper_matches(helper, risk)
    ):
        raise StoryError(explain_combo(setting, mystery, tool, risk, helper))

    world = tell(
        setting=setting,
        mystery=mystery,
        tool=tool,
        risk=risk,
        helper=helper,
        hero_name=params.hero,
        gender=params.gender,
        elder_type=params.elder,
        trait=params.trait,
        extra_strokes=params.extra_strokes,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery, tool, risk, helper) combos:\n")
        for setting, mystery, tool, risk, helper in combos:
            print(f"  {setting:13} {mystery:16} {tool:12} {risk:13} {helper}")
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
                f"### {p.hero}: {p.mystery} at {p.setting} "
                f"({p.tool}, {p.risk}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
