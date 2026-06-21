#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hopperoo_debacle_prospector_curiosity_nursery_rhyme.py
==================================================================================

A standalone story world for a nursery-rhyme-flavored tale about curiosity,
a hopperoo, and a little prospector by the water.

Premise
-------
A child plays prospector beside a tinkling stream, swishing for shiny little
treasures. Then a hopperoo bounces onto an unsafe perch. Curiosity tugs the
child closer. If the child steps out on a risky perch, the pan can tip into
the water and a small debacle begins. A nearby grown-up helps in a sensible
way and then changes how the game is played.

The world model tracks:
- physical meters: wobble, slipped, soaked, spilled, danger, rescued
- emotional memes: curiosity, worry, fear, relief, lesson, joy

The prose is state-driven and shaped like a simple nursery rhyme rather than
a plain event log.

Run it
------
    python storyworlds/worlds/gpt-5.4/hopperoo_debacle_prospector_curiosity_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/hopperoo_debacle_prospector_curiosity_nursery_rhyme.py --setting orchard_creek --perch wobbly_log
    python storyworlds/worlds/gpt-5.4/hopperoo_debacle_prospector_curiosity_nursery_rhyme.py --perch steady_step
    python storyworlds/worlds/gpt-5.4/hopperoo_debacle_prospector_curiosity_nursery_rhyme.py --response shout_only
    python storyworlds/worlds/gpt-5.4/hopperoo_debacle_prospector_curiosity_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/hopperoo_debacle_prospector_curiosity_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/hopperoo_debacle_prospector_curiosity_nursery_rhyme.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CURIOSITY_INIT = 6.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    unstable: bool = False
    safe_tool: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandma", "woman"}
        male = {"boy", "father", "grandpa", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandma": "grandma",
            "grandpa": "grandpa",
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
class Setting:
    id: str
    place: str
    water: str
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
class Treasure:
    id: str
    label: str
    plural_label: str
    gleam: str
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
class Perch:
    id: str
    label: str
    line: str
    wobble: int
    risky: bool = True
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    safe_game: str
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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    perch = world.get("perch")
    pan = world.get("pan")
    stream = world.get("stream")
    if child.meters["on_perch"] < THRESHOLD or not perch.unstable:
        return out
    sig = ("slip", child.id, perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["slipped"] += 1
    child.meters["soaked"] += 1
    pan.meters["spilled"] += 1
    stream.meters["danger"] += 1
    child.memes["fear"] += 1
    helper = world.get("helper")
    helper.memes["worry"] += 1
    out.append("__slip__")
    return out


def _r_debacle(world: World) -> list[str]:
    out: list[str] = []
    pan = world.get("pan")
    stream = world.get("stream")
    if pan.meters["spilled"] < THRESHOLD:
        return out
    sig = ("debacle", pan.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pan.meters["lost"] += 1
    stream.meters["treasure_in_water"] += 1
    out.append("__debacle__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="debacle", tag="physical", apply=_r_debacle),
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


def hazardous(perch: Perch) -> bool:
    return perch.risky and perch.wobble > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def spill_severity(perch: Perch, delay: int) -> int:
    return perch.wobble + delay


def is_saved(response: Response, perch: Perch, delay: int) -> bool:
    return response.power >= spill_severity(perch, delay)


def predict_slip(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["on_perch"] += 1
    propagate(sim, narrate=False)
    return {
        "slips": sim.get("child").meters["slipped"] >= THRESHOLD,
        "spills": sim.get("pan").meters["spilled"] >= THRESHOLD,
        "danger": sim.get("stream").meters["danger"],
    }


def opening(world: World, child: Entity, helper: Entity, treasure: Treasure) -> None:
    child.memes["joy"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"By {world.setting.place}, where bright drops coo, little {child.id} played "
        f"prospector in the morning dew. {world.setting.detail}"
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} swished a tin pan with a silver swoon, "
        f"hoping for {treasure.plural_label} that winked like noon."
    )
    world.say(
        f"Near by stood {helper.label_word}, humming low and true, keeping watch on the "
        f"ripple-song and the child {helper.pronoun('subject')} knew."
    )


def hopperoo_appears(world: World, child: Entity, perch: Perch, treasure: Treasure) -> None:
    world.say(
        f"Then out popped a hopperoo — hop-a-roo, hop-a-roo — and over to {perch.line} it flew. "
        f"It twitched near something {treasure.gleam}, and {child.id}'s bright curiosity grew."
    )


def warning(world: World, child: Entity, helper: Entity, perch: Perch) -> None:
    pred = predict_slip(world)
    world.facts["predicted_spill"] = pred["spills"]
    world.facts["predicted_danger"] = pred["danger"]
    helper.memes["worry"] += 1
    world.say(
        f'"Softly now," said {helper.label_word}. "{perch.label.capitalize()} likes to wag and sway. '
        f'One peep too far, one leaning step, and splash will steal your pan away."'
    )


def tempted(world: World, child: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"But curiosity tugged like a kite-string tight. {child.id} wanted just one nearer sight."
    )


def climb(world: World, child: Entity, perch: Entity) -> None:
    child.meters["on_perch"] += 1
    perch.meters["loaded"] += 1
    propagate(world, narrate=False)


def accident(world: World, child: Entity, perch_cfg: Perch, treasure: Treasure) -> None:
    world.say(
        f"{child.id} stepped onto {perch_cfg.label}, light as a tune. Then wiggle went wood, and slip came soon."
    )
    world.say(
        f"Splash went the pan in {world.setting.water}; {treasure.plural_label} whirled away in a shining spatter. "
        f'"Oh dear," cried {child.id}, "what a debacle!"'
    )


def rescue(world: World, helper: Entity, response: Response, treasure: Treasure) -> None:
    child = world.get("child")
    pan = world.get("pan")
    stream = world.get("stream")
    child.meters["soaked"] = 0.0
    child.meters["slipped"] = 0.0
    pan.meters["lost"] = 0.0
    pan.meters["spilled"] = 0.0
    pan.meters["rescued"] += 1
    stream.meters["danger"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{helper.label_word.capitalize()} {response.text.replace('{treasure}', treasure.plural_label)}."
    )
    world.say(
        f"Soon the tin pan was safe again, and so were both small shoes. The stream kept singing, but it did not win the news."
    )


def lesson(world: World, child: Entity, helper: Entity, response: Response, perch: Perch) -> None:
    child.memes["joy"] += 1
    world.say(
        f'{helper.label_word.capitalize()} knelt beside {child.id} and brushed a damp sleeve dry. '
        f'"Curious eyes are lovely," {helper.pronoun("subject")} said, "but steady feet must try."'
    )
    world.say(
        f'"When a perch can wobble, we do not rush for a better view. We ask for the safe way first, and then the fun stays true."'
    )
    world.say(
        f"They tried again by {response.safe_game}, where hopperoo still went hop-a-roo."
    )


def rescue_fail(world: World, helper: Entity, response: Response, treasure: Treasure) -> None:
    child = world.get("child")
    pan = world.get("pan")
    stream = world.get("stream")
    child.memes["fear"] += 1
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    stream.meters["danger"] += 1
    world.say(
        f"{helper.label_word.capitalize()} {response.fail.replace('{treasure}', treasure.plural_label)}."
    )
    world.say(
        f"The pan bumped once, twice, and drifted to the reeds. The little prospector kept safe, but lost the morning's gleams and beads."
    )


def sad_end(world: World, child: Entity, helper: Entity, response: Response) -> None:
    world.say(
        f'{helper.label_word.capitalize()} wrapped {child.id} in a dry towel from the satchel side. '
        f'"You matter more than shiny things," {helper.pronoun("subject")} said with a cuddle wide.'
    )
    world.say(
        f"After that, the game moved back from the edge to {response.safe_game}. "
        f"{child.id} still watched for hopperoo, but from a place that did not sway."
    )


def tell(
    setting: Setting,
    treasure: Treasure,
    perch: Perch,
    response: Response,
    *,
    child_name: str = "June",
    child_type: str = "girl",
    helper_type: str = "grandma",
    delay: int = 0,
) -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=["curious"],
        attrs={"name": child_name},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    perch_ent = world.add(Entity(
        id="perch",
        type="perch",
        label=perch.label,
        unstable=perch.risky,
    ))
    pan = world.add(Entity(
        id="pan",
        type="pan",
        label="tin pan",
        owner=child.id,
    ))
    stream = world.add(Entity(
        id="stream",
        type="stream",
        label=setting.water,
    ))
    hopperoo = world.add(Entity(
        id="hopperoo",
        type="hopperoo",
        label="hopperoo",
        attrs={"song": "hop-a-roo"},
    ))

    child.memes["curiosity"] = CURIOSITY_INIT
    child.memes["fear"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["lesson"] = 0.0
    helper.memes["worry"] = 0.0
    pan.meters["spilled"] = 0.0
    pan.meters["lost"] = 0.0
    stream.meters["danger"] = 0.0
    child.meters["on_perch"] = 0.0
    child.meters["slipped"] = 0.0
    child.meters["soaked"] = 0.0

    opening(world, child, helper, treasure)
    hopperoo_appears(world, child, perch, treasure)
    world.para()
    warning(world, child, helper, perch)
    tempted(world, child)
    world.para()
    climb(world, child, perch_ent)
    accident(world, child, perch, treasure)

    contained = is_saved(response, perch, delay)
    world.para()
    if contained:
        rescue(world, helper, response, treasure)
        lesson(world, child, helper, response, perch)
        outcome = "contained"
    else:
        rescue_fail(world, helper, response, treasure)
        sad_end(world, child, helper, response)
        outcome = "lost"

    world.facts.update(
        child=child,
        helper=helper,
        setting=setting,
        treasure=treasure,
        perch_cfg=perch,
        response=response,
        delay=delay,
        outcome=outcome,
        slipped=True,
        recovered=contained,
        child_name=child_name,
    )
    return world


SETTINGS = {
    "garden_rill": Setting(
        id="garden_rill",
        place="the garden rill",
        water="the rill",
        detail="Pennywort leaves bobbed on the bank, and mint made the air smell cool.",
        tags={"stream", "garden"},
    ),
    "orchard_creek": Setting(
        id="orchard_creek",
        place="the orchard creek",
        water="the creek",
        detail="Apples nodded overhead, and the water chinked over roots like a spoon on a cup.",
        tags={"stream", "orchard"},
    ),
    "meadow_brook": Setting(
        id="meadow_brook",
        place="the meadow brook",
        water="the brook",
        detail="Clover heads bent in the breeze, and reeds whispered by the silver edge.",
        tags={"stream", "meadow"},
    ),
}

TREASURES = {
    "gold_flakes": Treasure(
        id="gold_flakes",
        label="gold flake",
        plural_label="gold-like flakes",
        gleam="golden",
        tags={"prospector", "shiny"},
    ),
    "sun_pebbles": Treasure(
        id="sun_pebbles",
        label="sun pebble",
        plural_label="sun-pebbles",
        gleam="sunny",
        tags={"prospector", "pebble"},
    ),
    "brass_buttons": Treasure(
        id="brass_buttons",
        label="brass button",
        plural_label="brass buttons",
        gleam="brassy",
        tags={"prospector", "button"},
    ),
}

PERCHES = {
    "mossy_stone": Perch(
        id="mossy_stone",
        label="the mossy stone",
        line="the mossy stone at the bend",
        wobble=1,
        risky=True,
        tags={"stone", "slippery"},
    ),
    "wobbly_log": Perch(
        id="wobbly_log",
        label="the wobbly log",
        line="the wobbly log by the water",
        wobble=2,
        risky=True,
        tags={"log", "slippery"},
    ),
    "sandy_edge": Perch(
        id="sandy_edge",
        label="the sandy edge",
        line="the sandy edge where the bank liked to crumble",
        wobble=2,
        risky=True,
        tags={"bank", "slippery"},
    ),
    "steady_step": Perch(
        id="steady_step",
        label="the steady stepping stone",
        line="the steady stepping stone in the shallow",
        wobble=0,
        risky=False,
        tags={"stone"},
    ),
}

RESPONSES = {
    "reach_and_lift": Response(
        id="reach_and_lift",
        sense=3,
        power=3,
        text="reached fast, caught the pan strap, and lifted both child and {treasure} from the water's tug",
        fail="reached for the pan strap, but the current had already tugged the {treasure} too far away",
        qa_text="reached fast, caught the pan strap, and lifted the pan out before it drifted away",
        safe_game="a flat plank laid on the grass",
        tags={"rescue", "help"},
    ),
    "lay_plank": Response(
        id="lay_plank",
        sense=3,
        power=2,
        text="slid a flat plank to the bank and used it like a safe little bridge to draw the pan back in",
        fail="slid a plank to the bank, but the pan had bobbed beyond easy reach with the {treasure}",
        qa_text="used a flat plank like a little bridge and drew the pan back to shore",
        safe_game="the flat plank on the bank",
        tags={"rescue", "bridge"},
    ),
    "hook_with_rake": Response(
        id="hook_with_rake",
        sense=2,
        power=1,
        text="hooked the pan with a garden rake and pulled the {treasure} back through the reeds",
        fail="tried to hook the pan with a garden rake, but it slipped free and the {treasure} scattered downstream",
        qa_text="hooked the pan with a garden rake and pulled it back",
        safe_game="the grassy side away from the edge",
        tags={"rescue", "tool"},
    ),
    "shout_only": Response(
        id="shout_only",
        sense=1,
        power=0,
        text="only shouted from the path",
        fail="only shouted from the path, and shouting could not pull a pan from water",
        qa_text="only shouted from the path",
        safe_game="the dry path",
        tags={"warning"},
    ),
}

GIRL_NAMES = ["June", "Molly", "Nell", "Ruby", "Tess", "Maisie", "Dora", "Poppy"]
BOY_NAMES = ["Finn", "Toby", "Milo", "Ned", "Otis", "Rory", "Jem", "Kit"]


@dataclass
class StoryParams:
    setting: str
    treasure: str
    perch: str
    response: str
    child_name: str
    child_gender: str
    helper: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for setting_id in SETTINGS:
        for treasure_id in TREASURES:
            for perch_id, perch in PERCHES.items():
                if hazardous(perch):
                    combos.append((setting_id, treasure_id, perch_id))
    return combos


KNOWLEDGE = {
    "prospector": [
        (
            "What does a prospector do?",
            "A prospector looks for useful or shiny things in earth or water, like gold or bright stones. In this story, the child was only pretending to be one in a playful way.",
        )
    ],
    "stream": [
        (
            "Why can a stream edge be slippery?",
            "Water makes stones, mud, and logs slick. That means your feet can slide even when you think you are stepping carefully.",
        )
    ],
    "slippery": [
        (
            "Why is a wobbly log not a safe place to stand?",
            "A wobbly log can roll or shift under your feet. If it moves suddenly, you can slip before you have time to catch yourself.",
        )
    ],
    "rescue": [
        (
            "What should you do if something falls in the water near a slippery edge?",
            "Call a grown-up and step back from the edge. A grown-up can use a safe tool or a better place to stand.",
        )
    ],
    "hopperoo": [
        (
            "What is a hopperoo in this story?",
            "A hopperoo is a little hopping creature from the rhyme-world of the tale. It bounces about and makes the child curious.",
        )
    ],
    "curiosity": [
        (
            "Is curiosity good or bad?",
            "Curiosity is good because it helps you notice and learn new things. It needs a safe plan, though, so wondering does not turn into trouble.",
        )
    ],
}
KNOWLEDGE_ORDER = ["prospector", "stream", "slippery", "rescue", "hopperoo", "curiosity"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    treasure = f["treasure"]
    perch = f["perch_cfg"]
    outcome = f["outcome"]
    helper = f["helper"]
    base = (
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words '
        f'"hopperoo", "debacle", and "prospector". A curious child looks for {treasure.plural_label} near water.'
    )
    if outcome == "contained":
        return [
            base,
            f"Tell a sing-song story where {child.attrs['name']} steps onto {perch.label}, the pan splashes, and {helper.label_word} rescues it in a calm, sensible way.",
            "Write a gentle rhyme-story where curiosity causes a small watery mishap, but the ending shows a safer way to keep playing.",
        ]
    return [
        base,
        f"Tell a cautionary nursery rhyme where {child.attrs['name']}'s curiosity leads to a spill on {perch.label}, and even help cannot save the shiny finds.",
        "Write a small sad-but-safe rhyme where the child loses the treasure, learns from the debacle, and moves the game away from the edge.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    treasure = f["treasure"]
    perch = f["perch_cfg"]
    response = f["response"]
    child_name = f["child_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a curious child named {child_name}, a nearby {helper.label_word}, and a hopping hopperoo. The child was playing prospector by the water.",
        ),
        (
            f"Why did {child_name} go closer to {perch.label}?",
            f"{child_name} wanted a better look at the hopperoo and the shiny {treasure.plural_label}. Curiosity pulled the child closer even after the warning.",
        ),
        (
            f"Why did {helper.label_word} warn {child_name} about {perch.label}?",
            f"{helper.label_word.capitalize()} knew that {perch.label} could sway or slip by the water. One wrong step there could send the pan splashing away and start a debacle.",
        ),
        (
            f"What made the story a debacle?",
            f"The child stepped onto {perch.label}, slipped, and the tin pan splashed into the water. That turned the bright little game into a messy problem all at once.",
        ),
    ]
    if f["outcome"] == "contained":
        qa.append(
            (
                f"How did {helper.label_word} fix the problem?",
                f"{helper.label_word.capitalize()} {response.qa_text.replace('{treasure}', treasure.plural_label)}. That worked because the help came quickly enough to beat the wobble and drift.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with the child calm again and the game moved to {response.safe_game}. The ending proves the child still stayed curious, but used a steadier place.",
            )
        )
    else:
        qa.append(
            (
                f"Could {helper.label_word} save the shiny things?",
                f"No. {helper.label_word.capitalize()} tried, but the pan and the {treasure.plural_label} drifted too far away. The child stayed safe, but the morning's treasure was lost.",
            )
        )
        qa.append(
            (
                "What did the child learn at the end?",
                f"The child learned that curious looking needs steady footing. After the debacle, the game moved back from the edge to a safer place.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"prospector", "stream", "hopperoo", "curiosity", "rescue"}
    if world.facts["perch_cfg"].wobble > 0:
        tags.add("slippery")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.unstable:
            bits.append("unstable=True")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:9} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden_rill",
        treasure="gold_flakes",
        perch="mossy_stone",
        response="reach_and_lift",
        child_name="June",
        child_gender="girl",
        helper="grandma",
        delay=0,
    ),
    StoryParams(
        setting="orchard_creek",
        treasure="sun_pebbles",
        perch="wobbly_log",
        response="lay_plank",
        child_name="Finn",
        child_gender="boy",
        helper="grandpa",
        delay=0,
    ),
    StoryParams(
        setting="meadow_brook",
        treasure="brass_buttons",
        perch="sandy_edge",
        response="hook_with_rake",
        child_name="Molly",
        child_gender="girl",
        helper="mother",
        delay=1,
    ),
    StoryParams(
        setting="garden_rill",
        treasure="sun_pebbles",
        perch="wobbly_log",
        response="lay_plank",
        child_name="Toby",
        child_gender="boy",
        helper="father",
        delay=1,
    ),
]


def explain_rejection(perch: Perch) -> str:
    return (
        f"(No story: {perch.label} is steady enough that a curious step would not cause a real mishap. "
        f"This world needs a risky perch so the warning, debacle, and lesson all make sense.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of these safer responses: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "contained" if is_saved(RESPONSES[params.response], PERCHES[params.perch], params.delay) else "lost"


ASP_RULES = r"""
hazard(P) :- perch(P), risky(P), wobble(P, W), W > 0.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, T, P) :- setting(S), treasure(T), hazard(P).

severity(W + D) :- chosen_perch(P), wobble(P, W), delay(D).
resp_power(Pw) :- chosen_response(R), power(R, Pw).

outcome(contained) :- resp_power(Pw), severity(V), Pw >= V.
outcome(lost) :- resp_power(Pw), severity(V), Pw < V.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for treasure_id in TREASURES:
        lines.append(asp.fact("treasure", treasure_id))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("wobble", perch_id, perch.wobble))
        if perch.risky:
            lines.append(asp.fact("risky", perch_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_perch", params.perch),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
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

    clingo_sens = set(asp_sensible())
    python_sens = {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        buf = io.StringIO()
        saved = sys.stdout
        sys.stdout = buf
        try:
            emit(smoke, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = saved
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke generation and emit succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: a curious little prospector, a hopperoo, and a watery debacle."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=["mother", "father", "grandma", "grandpa"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra drift time before the grown-up can fully help")
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.perch and not hazardous(PERCHES[args.perch]):
        raise StoryError(explain_rejection(PERCHES[args.perch]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.treasure is None or combo[1] == args.treasure)
        and (args.perch is None or combo[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, treasure_id, perch_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "grandma", "grandpa"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        setting=setting_id,
        treasure=treasure_id,
        perch=perch_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        helper=helper,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.helper not in {"mother", "father", "grandma", "grandpa"}:
        raise StoryError(f"(Unknown helper type: {params.helper})")
    if not hazardous(PERCHES[params.perch]):
        raise StoryError(explain_rejection(PERCHES[params.perch]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        SETTINGS[params.setting],
        TREASURES[params.treasure],
        PERCHES[params.perch],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_type=params.child_gender,
        helper_type=params.helper,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render().replace("little child", "little one"),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story.replace("child", sample.params.child_name))
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, treasure, perch) combos:\n")
        for setting_id, treasure_id, perch_id in combos:
            print(f"  {setting_id:13} {treasure_id:13} {perch_id}")
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
            header = (
                f"### {p.child_name}: {p.treasure} by {p.setting} "
                f"({p.perch}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
