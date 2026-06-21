#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/archer_mystery_to_solve_ghost_story.py
=================================================================

A standalone story world about a young archer who sees something that looks like
a ghost and has to solve the mystery calmly. The tale keeps a gentle ghost-story
mood, but the world model insists on a real explanation: a pale shape, a strange
sound, a windy dark place, careful clues, and a fix that proves what truly
changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/archer_mystery_to_solve_ghost_story.py
    python storyworlds/worlds/gpt-5.4/archer_mystery_to_solve_ghost_story.py --place orchard --cause scarecrow_sheet
    python storyworlds/worlds/gpt-5.4/archer_mystery_to_solve_ghost_story.py --tool candle
    python storyworlds/worlds/gpt-5.4/archer_mystery_to_solve_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/archer_mystery_to_solve_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/archer_mystery_to_solve_ghost_story.py --trace
    python storyworlds/worlds/gpt-5.4/archer_mystery_to_solve_ghost_story.py --asp
    python storyworlds/worlds/gpt-5.4/archer_mystery_to_solve_ghost_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "keeper_woman"}
        male = {"boy", "father", "man", "keeper_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "keeper_woman": "keeper",
            "keeper_man": "keeper",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    archery_spot: str
    wind_text: str
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
class Cause:
    id: str
    label: str
    places: set[str]
    sight: str
    sound: str
    clue: str
    reveal: str
    fix: str
    fixed_image: str
    spook: int
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
    brightness: int
    sense: int
    beam: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and causal rules
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
        return [e for e in self.entities.values() if e.role in {"hero", "companion"}]

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


def _r_haunting(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("place")
    mystery = world.get("mystery")
    if place.meters["wind"] < THRESHOLD:
        return out
    if mystery.meters["unmasked"] >= THRESHOLD:
        return out
    sig = ("haunting",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mystery.meters["shape_seen"] += 1
    mystery.meters["sound_heard"] += 1
    mystery.meters["active"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__haunting__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    companion = world.get("companion")
    mystery = world.get("mystery")
    if mystery.meters["active"] < THRESHOLD:
        return out
    if hero.meters["light"] < THRESHOLD:
        return out
    if hero.memes["focus"] < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["courage"] += 1
    hero.meters["examining"] += 1
    companion.memes["fear"] = max(0.0, companion.memes["fear"] - 1.0)
    out.append("__calm__")
    return out


def _r_identify(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    mystery = world.get("mystery")
    if hero.meters["examining"] < THRESHOLD:
        return out
    if mystery.meters["shape_seen"] < THRESHOLD or mystery.meters["sound_heard"] < THRESHOLD:
        return out
    sig = ("identify",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mystery.meters["unmasked"] += 1
    mystery.meters["active"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["wonder"] += 1
    companion = world.get("companion")
    companion.memes["relief"] += 1
    companion.memes["fear"] = 0.0
    out.append("__identify__")
    return out


CAUSAL_RULES = [
    Rule(name="haunting", tag="physical", apply=_r_haunting),
    Rule(name="calm", tag="emotional", apply=_r_calm),
    Rule(name="identify", tag="epistemic", apply=_r_identify),
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
# Constraint helpers and outcome model
# ---------------------------------------------------------------------------
def cause_fits(place: Place, cause: Cause) -> bool:
    return place.id in cause.places


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def hero_bonus(hero_trait: str) -> int:
    return 1 if hero_trait in {"careful", "patient", "sharp-eyed"} else 0


def companion_bonus(companion_trait: str) -> int:
    return 1 if companion_trait in {"steady", "curious"} else 0


def solve_score(tool: Tool, hero_trait: str, companion_trait: str) -> int:
    return tool.brightness + hero_bonus(hero_trait) + companion_bonus(companion_trait)


def outcome_of(params: "StoryParams") -> str:
    if params.place not in PLACES or params.cause not in CAUSES or params.tool not in TOOLS:
        raise StoryError("(Invalid params: unknown place, cause, or tool.)")
    place = PLACES[params.place]
    cause = CAUSES[params.cause]
    tool = TOOLS[params.tool]
    if not cause_fits(place, cause):
        raise StoryError(explain_rejection(place, cause))
    if tool.sense < SENSE_MIN:
        raise StoryError(explain_tool(params.tool))
    return "self_solved" if solve_score(tool, params.hero_trait, params.companion_trait) >= cause.spook else "keeper_helped"


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    if not sensible_tools():
        return combos
    for place_id, place in PLACES.items():
        for cause_id, cause in CAUSES.items():
            if cause_fits(place, cause):
                combos.append((place_id, cause_id))
    return combos


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_mystery(world: World) -> dict:
    sim = world.copy()
    sim.get("place").meters["wind"] += 1
    propagate(sim, narrate=False)
    mystery = sim.get("mystery")
    return {
        "shape": mystery.meters["shape_seen"] >= THRESHOLD,
        "sound": mystery.meters["sound_heard"] >= THRESHOLD,
        "fear": sim.get("hero").memes["fear"] + sim.get("companion").memes["fear"],
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def opening_scene(world: World, hero: Entity, companion: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    hero.memes["focus"] += 1
    world.say(
        f"{place.opening} {hero.id} was a young archer, and {hero.pronoun()} loved the quiet thump "
        f"of a practice arrow landing true."
    )
    world.say(
        f"{companion.id} stood nearby in {place.archery_spot}, counting each careful shot and smiling "
        f"when the last arrow landed close to the middle."
    )


def darken(world: World, place: Place) -> None:
    world.get("place").meters["dark"] += 1
    world.get("place").meters["wind"] += 1
    world.say(place.wind_text)


def first_haunt(world: World, cause: Cause) -> None:
    propagate(world, narrate=False)
    mystery = world.get("mystery")
    if mystery.meters["shape_seen"] >= THRESHOLD:
        world.say(
            f"Then both children saw it: {cause.sight}. It looked, for one chilly moment, like a ghost drifting in the dark."
        )
    if mystery.meters["sound_heard"] >= THRESHOLD:
        world.say(f"At the same time, they heard {cause.sound}, which made the whole place feel even stranger.")


def react(world: World, hero: Entity, companion: Entity) -> None:
    companion.memes["fear"] += 1
    world.say(
        f'"Did you see that?" {companion.id} whispered, moving close to {hero.id}. '
        f'"Maybe we should run."'
    )
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s hands felt cold too, but {hero.pronoun()} did not want the night to stay full of guessing."
        )


def decide(world: World, hero: Entity, companion: Entity, tool: Tool) -> None:
    pred = predict_mystery(world)
    world.facts["predicted_shape"] = pred["shape"]
    world.facts["predicted_sound"] = pred["sound"]
    world.facts["predicted_fear"] = pred["fear"]
    hero.meters["light"] += 1
    hero.memes["focus"] += 1
    world.say(
        f'{hero.id} took out {tool.phrase}. "{tool.beam}," {hero.pronoun()} said softly. '
        f'"If we look closely, maybe the ghost will turn back into something ordinary."'
    )
    propagate(world, narrate=False)


def inspect_alone(world: World, hero: Entity, companion: Entity, cause: Cause, tool: Tool) -> None:
    world.say(
        f"They crept forward together while the {tool.label} sent {tool.beam.lower()}. "
        f"Near the far edge of the dark, {hero.id} noticed {cause.clue}."
    )
    propagate(world, narrate=False)
    world.say(
        f'"It is not a ghost," {hero.id} said at last. "{cause.reveal}"'
    )


def call_keeper(world: World, hero: Entity, companion: Entity, keeper: Entity, cause: Cause, tool: Tool) -> None:
    hero.memes["prudence"] += 1
    world.say(
        f"{hero.id} lifted the {tool.label} again, but the shadows still felt too big to search alone."
    )
    world.say(
        f'So {hero.pronoun()} called for the old {keeper.label_word} who watched over the grounds. '
        f'"Please come see," {hero.pronoun()} said. "We think there is a ghost."'
    )
    world.say(
        f"{keeper.label_word.capitalize()} came with slow, steady steps, followed the pale shape with careful eyes, "
        f"and soon spotted {cause.clue}."
    )
    world.get("mystery").meters["unmasked"] += 1
    world.get("mystery").meters["active"] = 0.0
    hero.memes["relief"] += 1
    companion.memes["relief"] += 1
    companion.memes["fear"] = 0.0
    world.say(
        f'"There now," {keeper.label_word} said kindly. "{cause.reveal}"'
    )


def fix_and_close(world: World, hero: Entity, companion: Entity, keeper: Entity, cause: Cause, tool: Tool, outcome: str) -> None:
    world.get("mystery").meters["fixed"] += 1
    hero.memes["joy"] += 1
    hero.memes["fear"] = 0.0
    companion.memes["joy"] += 1
    world.say(cause.fix)
    if outcome == "self_solved":
        world.say(
            f"{companion.id} let out a shaky laugh. The place still looked old and silver in the night, "
            f"but now it felt friendly again."
        )
    else:
        world.say(
            f"{hero.id} and {companion.id} both laughed then, because the thing that had seemed so spooky "
            f"looked almost silly in the clear light."
        )
    world.say(
        f"Soon the mystery was gone. {cause.fixed_image} {hero.id} fetched the arrows again, and even in the ghostly-looking dark, "
        f"{hero.pronoun()} knew that careful looking was braver than guessing."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    cause: Cause,
    tool: Tool,
    hero_name: str = "Robin",
    hero_gender: str = "girl",
    companion_name: str = "Bram",
    companion_gender: str = "boy",
    hero_trait: str = "careful",
    companion_trait: str = "steady",
    keeper_gender: str = "keeper_woman",
) -> World:
    world = World()

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[hero_trait, "archer"],
        tags={"archer"},
    ))
    companion = world.add(Entity(
        id=companion_name,
        kind="character",
        type=companion_gender,
        label=companion_name,
        role="companion",
        traits=[companion_trait],
    ))
    keeper = world.add(Entity(
        id="Keeper",
        kind="character",
        type=keeper_gender,
        label="the keeper",
        role="keeper",
    ))
    place_ent = world.add(Entity(
        id="place",
        type="place",
        label=place.label,
        tags=set(place.tags),
    ))
    mystery = world.add(Entity(
        id="mystery",
        type="mystery",
        label="the ghostly thing",
        tags={"ghost", "mystery"},
    ))
    light = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        tags=set(tool.tags),
    ))

    place_ent.meters["dark"] = 0.0
    place_ent.meters["wind"] = 0.0
    mystery.meters["shape_seen"] = 0.0
    mystery.meters["sound_heard"] = 0.0
    mystery.meters["active"] = 0.0
    mystery.meters["unmasked"] = 0.0
    mystery.meters["fixed"] = 0.0
    hero.meters["light"] = 0.0
    hero.meters["examining"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["focus"] = 1.0 if hero_trait in {"careful", "patient", "sharp-eyed"} else 0.0
    hero.memes["courage"] = 0.0
    hero.memes["relief"] = 0.0
    companion.memes["fear"] = 0.0
    companion.memes["relief"] = 0.0

    opening_scene(world, hero, companion, place)
    world.para()
    darken(world, place)
    first_haunt(world, cause)
    react(world, hero, companion)
    world.para()
    decide(world, hero, companion, tool)

    outcome = "self_solved" if solve_score(tool, hero_trait, companion_trait) >= cause.spook else "keeper_helped"
    if outcome == "self_solved":
        inspect_alone(world, hero, companion, cause, tool)
    else:
        call_keeper(world, hero, companion, keeper, cause, tool)

    world.para()
    fix_and_close(world, hero, companion, keeper, cause, tool, outcome)

    world.facts.update(
        hero=hero,
        companion=companion,
        keeper=keeper,
        place_cfg=place,
        cause_cfg=cause,
        tool_cfg=tool,
        outcome=outcome,
        mystery_solved=world.get("mystery").meters["unmasked"] >= THRESHOLD,
        mystery_fixed=world.get("mystery").meters["fixed"] >= THRESHOLD,
        score=solve_score(tool, hero_trait, companion_trait),
        spook=cause.spook,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "orchard": Place(
        id="orchard",
        label="the orchard range",
        opening="At the edge of the old orchard, a row of straw targets stood under bent apple trees.",
        archery_spot="the cool grass beside the target bales",
        wind_text="When the sun slipped away, the orchard turned blue and hushed. A little wind wandered through the branches and made the leaves whisper.",
        tags={"orchard", "night"},
    ),
    "abbey_yard": Place(
        id="abbey_yard",
        label="the abbey yard",
        opening="Behind the old abbey wall, a small practice range had been marked with chalk and lantern posts.",
        archery_spot="the cracked stones near the archery straw",
        wind_text="Evening gathered in the abbey yard until the old stones looked almost silver. Then the wind slipped under the arch and stirred every hanging thing it could find.",
        tags={"abbey", "night"},
    ),
    "boathouse": Place(
        id="boathouse",
        label="the boathouse path",
        opening="Near the still black water, the boathouse path held a practice target leaned against a driftwood fence.",
        archery_spot="the narrow plank path by the reeds",
        wind_text="Soon the water darkened like ink. A damp wind came off the lake and made the boards creak under every little gust.",
        tags={"lake", "night"},
    ),
}

CAUSES = {
    "scarecrow_sheet": Cause(
        id="scarecrow_sheet",
        label="a scarecrow wearing a loose white sheet",
        places={"orchard"},
        sight="a tall white shape swaying between the apple trees",
        sound="a dry clack as one wooden arm tapped the post beside it",
        clue="straw peeking from one sleeve and a turnip-smile hidden under the cloth",
        reveal="It is only the orchard scarecrow with a sheet caught over it.",
        fix="Together they pulled the sheet free and tied it into a neat bundle so the wind could not lift it again.",
        fixed_image="The scarecrow stood plain and silly among the trees.",
        spook=3,
        tags={"scarecrow", "ghost", "wind"},
    ),
    "laundry_line": Cause(
        id="laundry_line",
        label="a white sheet flapping on a line",
        places={"orchard", "abbey_yard"},
        sight="a pale shape ballooning and shrinking in the wind",
        sound="clothespins clicking and a line rope twanging against a hook",
        clue="a row of wash pegs and one corner of sheet looped over a sagging line",
        reveal="It is just washing left out too late, with the wind making it dance.",
        fix="They clipped the sheet tight and lowered the loose line so it would stop flapping over the path.",
        fixed_image="The washing hung still and square, with no ghost shape left in it at all.",
        spook=2,
        tags={"laundry", "ghost", "wind"},
    ),
    "boat_tarp": Cause(
        id="boat_tarp",
        label="a loose white tarp over a boat",
        places={"boathouse"},
        sight="a pale back rising and falling beside the black water",
        sound="a hollow knock as rope and tarp slapped the boat's wooden side",
        clue="one untied rope dragging in the water and the tarp puffing like a sail",
        reveal="It is only a boat cover that came loose in the wind.",
        fix="The keeper knotted the rope tight, and the children helped smooth the tarp flat across the boat.",
        fixed_image="After that, the boat rested quietly, with the cover tucked down tight and calm.",
        spook=4,
        tags={"boat", "ghost", "lake"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a brass lantern",
        brightness=2,
        sense=3,
        beam="Hold the light low and look for real edges",
        tags={"lantern", "light"},
    ),
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        brightness=3,
        sense=3,
        beam="Let's shine the beam where the shape really begins and ends",
        tags={"flashlight", "light"},
    ),
    "glow_lamp": Tool(
        id="glow_lamp",
        label="camp lamp",
        phrase="a little camp lamp",
        brightness=2,
        sense=3,
        beam="A steady glow helps more than a frightened guess",
        tags={"lamp", "light"},
    ),
    "candle": Tool(
        id="candle",
        label="candle",
        phrase="a tiny candle",
        brightness=1,
        sense=1,
        beam="The little flame trembled too much to help much at all",
        tags={"candle", "light"},
    ),
}

GIRL_NAMES = ["Robin", "Elin", "Mara", "Nell", "Ivy", "Tessa", "Wren", "Lina"]
BOY_NAMES = ["Rowan", "Bram", "Owen", "Jude", "Finn", "Tobin", "Ash", "Milo"]
HERO_TRAITS = ["careful", "patient", "sharp-eyed", "brave"]
COMPANION_TRAITS = ["steady", "curious", "jumpy", "timid"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    cause: str
    tool: str
    hero_name: str
    hero_gender: str
    companion_name: str
    companion_gender: str
    hero_trait: str
    companion_trait: str
    keeper_gender: str
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
        place="orchard",
        cause="scarecrow_sheet",
        tool="flashlight",
        hero_name="Robin",
        hero_gender="girl",
        companion_name="Bram",
        companion_gender="boy",
        hero_trait="careful",
        companion_trait="steady",
        keeper_gender="keeper_woman",
    ),
    StoryParams(
        place="abbey_yard",
        cause="laundry_line",
        tool="lantern",
        hero_name="Rowan",
        hero_gender="boy",
        companion_name="Ivy",
        companion_gender="girl",
        hero_trait="patient",
        companion_trait="curious",
        keeper_gender="keeper_man",
    ),
    StoryParams(
        place="boathouse",
        cause="boat_tarp",
        tool="glow_lamp",
        hero_name="Mara",
        hero_gender="girl",
        companion_name="Owen",
        companion_gender="boy",
        hero_trait="brave",
        companion_trait="timid",
        keeper_gender="keeper_man",
    ),
    StoryParams(
        place="orchard",
        cause="laundry_line",
        tool="lantern",
        hero_name="Finn",
        hero_gender="boy",
        companion_name="Wren",
        companion_gender="girl",
        hero_trait="sharp-eyed",
        companion_trait="steady",
        keeper_gender="keeper_woman",
    ),
]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "ghost": [(
        "Why can something ordinary look like a ghost at night?",
        "In the dark, your eyes do not see clear edges as well. Wind, shadows, and guessing can make a sheet or tarp look spooky."
    )],
    "archer": [(
        "What is an archer?",
        "An archer is someone who practices shooting arrows with a bow. In a safe practice place, an archer aims carefully and pays close attention."
    )],
    "lantern": [(
        "What does a lantern do?",
        "A lantern gives steady light so you can see shapes, paths, and corners more clearly. Good light helps people notice what is really there."
    )],
    "flashlight": [(
        "Why is a flashlight useful in the dark?",
        "A flashlight sends a bright beam where you point it. That can help you check a strange shape instead of only guessing about it."
    )],
    "lamp": [(
        "What is a camp lamp?",
        "A camp lamp is a safe little light that glows steadily. People use it so they can see in the dark without stumbling."
    )],
    "wind": [(
        "How can wind make a mystery look scarier?",
        "Wind can flap cloth, rattle rope, and knock light things against wood. Those moving sounds and shapes can make ordinary things seem mysterious."
    )],
    "scarecrow": [(
        "What is a scarecrow?",
        "A scarecrow is a stuffed figure set in a field or orchard. From far away, especially in dim light, it can look like a person."
    )],
    "laundry": [(
        "Why does washing move so much on a line?",
        "Cloth is light, so the wind can puff it out and twist it around. That is why a sheet can billow and flap."
    )],
    "boat": [(
        "Why might a tarp on a boat make knocking sounds?",
        "If a tarp comes loose, the wind can pull it and the ropes against the boat. That can make hollow, bumping sounds."
    )],
}
KNOWLEDGE_ORDER = ["ghost", "archer", "wind", "lantern", "flashlight", "lamp", "scarecrow", "laundry", "boat"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cause = f["cause_cfg"]
    place = f["place_cfg"]
    outcome = f["outcome"]
    prompts = [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the word "archer" and ends by solving a spooky mystery.',
        f"Tell a story about a young archer named {hero.id} who sees something ghostly at {place.label} and decides to look for clues instead of only being scared.",
    ]
    if outcome == "self_solved":
        prompts.append(
            f"Write a mystery-to-solve story where the child figures out that the ghost is really {cause.label}, and the ending proves the place is safe again."
        )
    else:
        prompts.append(
            f"Write a ghost-story mystery where the child is brave enough to ask for help, and a kind keeper reveals that the ghost is really {cause.label}."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    keeper = f["keeper"]
    place = f["place_cfg"]
    cause = f["cause_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young archer, and {companion.id}, who is there through the strange night with {hero.pronoun('object')}. The mystery happens while they are near {place.label}."
        ),
        (
            "Why did the place seem haunted at first?",
            f"It seemed haunted because they saw {cause.sight} and heard {cause.sound}. In the dark and wind, those clues felt ghostly before anyone looked closely."
        ),
        (
            f"Why did {hero.id} use the {tool.label}?",
            f"{hero.id} used the {tool.label} to see the edges of the strange shape instead of guessing. Better light helped turn fear into a real search for clues."
        ),
    ]
    if outcome == "self_solved":
        qa.append((
            f"How did {hero.id} solve the mystery?",
            f"{hero.id} walked closer with the {tool.label} and noticed {cause.clue}. That clue showed {hero.pronoun('object')} that the ghost was really ordinary: {cause.reveal}"
        ))
    else:
        qa.append((
            f"Why did {hero.id} call the {keeper.label_word}?",
            f"The night still felt too big to search alone, so {hero.id} chose help instead of a wild guess. The {keeper.label_word} then followed the clues and explained that {cause.reveal}"
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the mystery solved and the spooky thing fixed: {cause.fix} The last image proves the change, because {cause.fixed_image.lower()}"
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "archer", "wind"} | set(f["tool_cfg"].tags) | set(f["cause_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace and rejections
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, cause: Cause) -> str:
    fits = ", ".join(sorted(cause.places))
    return (
        f"(No story: {cause.label} does not belong in {place.label}. "
        f"That mystery works only in: {fits}.)"
    )


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it is too weak or unsafe for a child-facing mystery walk "
        f"(sense={tool.sense} < {SENSE_MIN}). Try: {better}.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(P,C) :- place(P), cause(C), allowed(C,P).
sensible(T) :- tool(T), sense(T,S), sense_min(M), S >= M.
valid(P,C) :- fits(P,C).

hero_bonus(1) :- chosen_hero_trait(T), careful_trait(T).
hero_bonus(0) :- chosen_hero_trait(T), not careful_trait(T).

comp_bonus(1) :- chosen_companion_trait(T), steady_trait(T).
comp_bonus(0) :- chosen_companion_trait(T), not steady_trait(T).

score(B + H + C) :- chosen_tool(T), brightness(T,B), hero_bonus(H), comp_bonus(C).
outcome(self_solved) :- chosen_cause(K), spook(K,S), score(V), V >= S.
outcome(keeper_helped) :- chosen_cause(K), spook(K,S), score(V), V < S.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("spook", cause_id, cause.spook))
        for place_id in sorted(cause.places):
            lines.append(asp.fact("allowed", cause_id, place_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("brightness", tool_id, tool.brightness))
        lines.append(asp.fact("sense", tool_id, tool.sense))
    for trait in sorted({"careful", "patient", "sharp-eyed"}):
        lines.append(asp.fact("careful_trait", trait))
    for trait in sorted({"steady", "curious"}):
        lines.append(asp.fact("steady_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_hero_trait", params.hero_trait),
        asp.fact("chosen_companion_trait", params.companion_trait),
    ])
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

    c_tools = set(asp_sensible_tools())
    p_tools = {tool.id for tool in sensible_tools()}
    if c_tools == p_tools:
        print(f"OK: sensible tools match ({sorted(c_tools)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(c_tools)} python={sorted(p_tools)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        try:
            py = outcome_of(params)
        except StoryError:
            bad += 1
            continue
        asp_res = asp_outcome(params)
        if py != asp_res:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=False, qa=False, header="### smoke")
        finally:
            sys.stdout = old
        if "archer" not in sample.story.lower():
            raise StoryError("smoke test story omitted required word 'archer'")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story mystery world: a young archer sees a spooky shape and solves what it really is."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-trait", choices=HERO_TRAITS)
    ap.add_argument("--companion-trait", choices=COMPANION_TRAITS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("--keeper-gender", choices=["keeper_woman", "keeper_man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mysteries from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause:
        place = PLACES[args.place]
        cause = CAUSES[args.cause]
        if not cause_fits(place, cause):
            raise StoryError(explain_rejection(place, cause))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cause is None or combo[1] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cause_id = rng.choice(sorted(combos))
    tool_id = args.tool or rng.choice(sorted(tool.id for tool in sensible_tools()))
    hero_trait = args.hero_trait or rng.choice(HERO_TRAITS)
    companion_trait = args.companion_trait or rng.choice(COMPANION_TRAITS)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or rng.choice(["girl", "boy"])
    keeper_gender = args.keeper_gender or rng.choice(["keeper_woman", "keeper_man"])
    hero_name = pick_name(rng, hero_gender)
    companion_name = pick_name(rng, companion_gender, avoid=hero_name)

    return StoryParams(
        place=place_id,
        cause=cause_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        companion_name=companion_name,
        companion_gender=companion_gender,
        hero_trait=hero_trait,
        companion_trait=companion_trait,
        keeper_gender=keeper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    missing = [name for name, registry in [
        ("place", PLACES),
        ("cause", CAUSES),
        ("tool", TOOLS),
    ] if getattr(params, name) not in registry]
    if missing:
        raise StoryError(f"(Invalid params: unknown {', '.join(missing)}.)")

    place = PLACES[params.place]
    cause = CAUSES[params.cause]
    tool = TOOLS[params.tool]

    if not cause_fits(place, cause):
        raise StoryError(explain_rejection(place, cause))
    if tool.sense < SENSE_MIN:
        raise StoryError(explain_tool(params.tool))

    world = tell(
        place=place,
        cause=cause,
        tool=tool,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        companion_name=params.companion_name,
        companion_gender=params.companion_gender,
        hero_trait=params.hero_trait,
        companion_trait=params.companion_trait,
        keeper_gender=params.keeper_gender,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        tools = asp_sensible_tools()
        combos = asp_valid_combos()
        print(f"sensible tools: {', '.join(tools)}\n")
        print(f"{len(combos)} compatible (place, cause) combos:\n")
        for place_id, cause_id in combos:
            print(f"  {place_id:12} {cause_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.cause} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
