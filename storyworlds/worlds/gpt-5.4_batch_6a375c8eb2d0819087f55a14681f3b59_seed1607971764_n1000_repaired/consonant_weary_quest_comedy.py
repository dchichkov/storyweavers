#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/consonant_weary_quest_comedy.py
==========================================================

A small storyworld about a child going on a comic quest to recover a missing
consonant tile from a snack-stand sign. The grown-up in charge is weary from
preparing treats, the sign looks ridiculous without its letter, and the child
must pick a sensible retrieval tool for the hiding place.

Run it
------
    python storyworlds/worlds/gpt-5.4/consonant_weary_quest_comedy.py
    python storyworlds/worlds/gpt-5.4/consonant_weary_quest_comedy.py --feast pretzels --location under_sofa --tool broom
    python storyworlds/worlds/gpt-5.4/consonant_weary_quest_comedy.py --location garden_path --tool broom
    python storyworlds/worlds/gpt-5.4/consonant_weary_quest_comedy.py --all
    python storyworlds/worlds/gpt-5.4/consonant_weary_quest_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/consonant_weary_quest_comedy.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Feast:
    id: str
    tray: str
    full_sign: str
    broken_sign: str
    missing_letter: str
    snack_phrase: str
    ending_line: str
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
class Location:
    id: str
    label: str
    place_line: str
    quest_name: str
    reach: str
    terrain: str
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
class Tool:
    id: str
    label: str
    phrase: str
    reaches: set[str]
    sense: int
    power: int
    action_text: str
    keeps_hands_clean: bool = False
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


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    letter = world.get("letter")
    hero = world.get("hero")
    tool = world.get("tool")
    if world.facts["location"].terrain != "dust":
        return out
    if letter.meters["retrieved"] < THRESHOLD:
        return out
    sig = ("dust", tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if not tool.attrs.get("keeps_hands_clean", False):
        hero.meters["dusty"] += 1
        hero.memes["surprise"] += 1
        out.append("__sneeze__")
    return out


def _r_mud(world: World) -> list[str]:
    out: list[str] = []
    letter = world.get("letter")
    if world.facts["location"].terrain != "mud":
        return out
    if letter.meters["retrieved"] < THRESHOLD:
        return out
    sig = ("mud",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    letter.meters["muddy"] += 1
    out.append("__mud__")
    return out


def _r_fixed(world: World) -> list[str]:
    out: list[str] = []
    sign = world.get("sign")
    letter = world.get("letter")
    hero = world.get("hero")
    helper = world.get("helper")
    grownup = world.get("grownup")
    if sign.meters["fixed"] < THRESHOLD:
        return out
    sig = ("fixed",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sign.meters["open"] += 1
    grownup.memes["relief"] += 1
    hero.memes["pride"] += 1
    helper.memes["joy"] += 1
    out.append("__open__")
    return out


CAUSAL_RULES = [
    Rule(name="dust", tag="physical", apply=_r_dust),
    Rule(name="mud", tag="physical", apply=_r_mud),
    Rule(name="fixed", tag="social", apply=_r_fixed),
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


FEASTS = {
    "pretzels": Feast(
        id="pretzels",
        tray="a tray of warm pretzels",
        full_sign="PRETZELS",
        broken_sign="PRETZELS".replace("R", "", 1),
        missing_letter="R",
        snack_phrase="pretzels with shiny salt on top",
        ending_line="Soon the pretend pretzel stand looked grand enough for a king and silly enough for a giggle.",
        tags={"pretzel", "sign"},
    ),
    "cookies": Feast(
        id="cookies",
        tray="a plate of crumbly cookies",
        full_sign="COOKIES",
        broken_sign="COOKIES".replace("K", "", 1),
        missing_letter="K",
        snack_phrase="cookies shaped like moons",
        ending_line="The cookie table looked ready for customers, especially customers who were teddy bears.",
        tags={"cookie", "sign"},
    ),
    "muffins": Feast(
        id="muffins",
        tray="a basket of blueberry muffins",
        full_sign="MUFFINS",
        broken_sign="MUFFINS".replace("F", "", 1),
        missing_letter="F",
        snack_phrase="blueberry muffins in paper cups",
        ending_line="The muffin booth looked so cheerful that even the socks on the radiator seemed invited.",
        tags={"muffin", "sign"},
    ),
}

LOCATIONS = {
    "under_sofa": Location(
        id="under_sofa",
        label="under the sofa",
        place_line="the tile under the sofa, deep in the shadow of Cushion Canyon",
        quest_name="Cushion Canyon",
        reach="low",
        terrain="dust",
        detail="Dust bunnies sat under the sofa like sleepy guards with fuzzy whiskers.",
        tags={"sofa", "dust"},
    ),
    "high_fridge": Location(
        id="high_fridge",
        label="on top of the fridge",
        place_line="the top of the fridge, high on the cold ledge of Fridge Cliff",
        quest_name="Fridge Cliff",
        reach="high",
        terrain="clean",
        detail="The tile had landed up high beside a paper crown and one lonely clothespin.",
        tags={"fridge", "high"},
    ),
    "garden_path": Location(
        id="garden_path",
        label="on the garden path",
        place_line="the garden path beyond the back step, at the splashy edge of Pebble Pass",
        quest_name="Pebble Pass",
        reach="ground",
        terrain="mud",
        detail="A rain puddle blinked around the tile, and the path made soft squish sounds.",
        tags={"garden", "mud"},
    ),
}

TOOLS = {
    "broom": Tool(
        id="broom",
        label="broom",
        phrase="the long kitchen broom",
        reaches={"low"},
        sense=2,
        power=2,
        action_text="lay flat on the floor and swept the tile out with careful little pushes",
        keeps_hands_clean=False,
        tags={"broom", "dust"},
    ),
    "grabber": Tool(
        id="grabber",
        label="grabber",
        phrase="the toy grabber",
        reaches={"low", "high"},
        sense=3,
        power=3,
        action_text="clicked the jaws open, pinched the tile neatly, and brought it back like treasure",
        keeps_hands_clean=True,
        tags={"grabber"},
    ),
    "step_stool": Tool(
        id="step_stool",
        label="step stool",
        phrase="the sturdy blue step stool",
        reaches={"high"},
        sense=3,
        power=3,
        action_text="climbed one step, reached up, and took the tile from the ledge",
        keeps_hands_clean=True,
        tags={"stool", "high"},
    ),
    "boots": Tool(
        id="boots",
        label="rain boots",
        phrase="the red rain boots",
        reaches={"ground"},
        sense=3,
        power=3,
        action_text="sploshed across the damp path and lifted the tile from the mud without slipping",
        keeps_hands_clean=False,
        tags={"boots", "mud"},
    ),
    "rolling_chair": Tool(
        id="rolling_chair",
        label="rolling chair",
        phrase="the wiggly rolling chair",
        reaches={"high"},
        sense=1,
        power=1,
        action_text="wobbled on the wheels and reached in a way no sensible quest should use",
        keeps_hands_clean=False,
        tags={"chair"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Theo", "Eli", "Finn", "Noah"]
TRAITS = ["cheerful", "dramatic", "brave", "curious", "bouncy", "determined"]


def compatible(location: Location, tool: Tool) -> bool:
    return location.reach in tool.reaches and tool.sense >= SENSE_MIN and tool.power >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for feast_id in FEASTS:
        for loc_id, loc in LOCATIONS.items():
            for tool_id, tool in TOOLS.items():
                if compatible(loc, tool):
                    combos.append((feast_id, loc_id, tool_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    loc = LOCATIONS[params.location]
    tool = TOOLS[params.tool]
    if loc.terrain == "dust" and not tool.keeps_hands_clean:
        return "sneezy"
    if loc.terrain == "mud":
        return "muddy"
    return "tidy"


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(tid for tid, t in TOOLS.items() if t.sense >= SENSE_MIN))
    return (
        f"(Refusing tool '{tool_id}': {tool.label} is too wobbly or silly for this quest "
        f"(sense={tool.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def explain_rejection(location: Location, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        return explain_tool(tool.id)
    return (
        f"(No story: {tool.label} cannot sensibly reach a tile {location.label}. "
        f"Pick a tool that works for {location.quest_name}.)"
    )


@dataclass
class StoryParams:
    feast: str
    location: str
    tool: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    grownup: str
    grownup_role: str
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


def predict_quest(world: World) -> dict:
    sim = world.copy()
    letter = sim.get("letter")
    letter.meters["retrieved"] += 1
    propagate(sim, narrate=False)
    return {
        "dusty_hero": sim.get("hero").meters["dusty"] >= THRESHOLD,
        "muddy_letter": sim.get("letter").meters["muddy"] >= THRESHOLD,
    }


def introduce(world: World, feast: Feast, hero: Entity, helper: Entity, grownup: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    grownup.memes["weariness"] += 1
    world.say(
        f"{hero.id} and {helper.id} had turned the kitchen into a royal snack hall. "
        f"On the table sat {feast.tray}, paper crowns, and a sign for the feast."
    )
    world.say(
        f'Only one consonant was missing, but it made the sign look very silly: '
        f'"{feast.broken_sign}."'
    )
    world.say(
        f"{hero.id}'s {grownup.label_word} looked weary from stirring and baking, "
        f"yet {grownup.pronoun()} still smiled at the nonsense on the sign."
    )


def call_to_quest(world: World, feast: Feast, hero: Entity, helper: Entity, grownup: Entity, location: Location) -> None:
    world.say(
        f'"The lost {feast.missing_letter} has rolled away," {grownup.label_word} said. '
        f'"Without it, our feast sign is a joke."'
    )
    world.say(
        f'{hero.id} lifted a cardboard tube like a trumpet. "Then we begin a quest!" '
        f'{hero.pronoun().capitalize()} declared.'
    )
    world.say(
        f"{helper.id} peered toward {location.label}. The trail led to {location.place_line}. "
        f"{location.detail}"
    )


def choose_tool(world: World, hero: Entity, helper: Entity, tool: Tool, location: Location) -> None:
    pred = predict_quest(world)
    world.facts["predicted_dusty_hero"] = pred["dusty_hero"]
    world.facts["predicted_muddy_letter"] = pred["muddy_letter"]
    world.say(
        f"{hero.id} chose {tool.phrase} for the trip into {location.quest_name}."
    )
    if pred["dusty_hero"]:
        world.say(
            f'{helper.id} eyed the shadows and said, "That will work, but your nose '
            f'might not enjoy the adventure."'
        )
    elif pred["muddy_letter"]:
        world.say(
            f'{helper.id} nodded. "Good. The path is wet, so we can cross it without '
            f'slipping and losing the tile again."'
        )
    else:
        world.say(
            f'{helper.id} grinned. "That looks sensible. Every proper quest needs '
            f'a tool and a plan."'
        )


def retrieve(world: World, hero: Entity, helper: Entity, location: Location, tool: Tool, feast: Feast) -> None:
    letter = world.get("letter")
    tool_ent = world.get("tool")
    tool_ent.attrs["keeps_hands_clean"] = tool.keeps_hands_clean
    letter.meters["retrieved"] += 1
    hero.memes["effort"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In {location.quest_name}, {hero.id} {tool.action_text}."
    )
    if hero.meters["dusty"] >= THRESHOLD:
        world.say(
            f"A puff of dust flew up. {hero.id} sneezed so loudly that a paper crown "
            f"jumped off the chair and {helper.id} laughed."
        )
    if letter.meters["muddy"] >= THRESHOLD:
        world.say(
            f"The tile came up with a brown splash on one corner, as if the garden "
            f"had tried to keep the treasure for itself."
        )
    world.say(
        f'Soon {hero.id} held the lost "{feast.missing_letter}" between two proud fingers.'
    )


def clean_tile(world: World, hero: Entity, helper: Entity, grownup: Entity) -> None:
    letter = world.get("letter")
    if letter.meters["muddy"] < THRESHOLD and hero.meters["dusty"] < THRESHOLD:
        return
    if letter.meters["muddy"] >= THRESHOLD:
        letter.meters["muddy"] = 0.0
        letter.meters["clean"] += 1
        world.say(
            f"{grownup.label_word.capitalize()} passed over a dish towel, and {hero.id} "
            f"rubbed the tile clean until its edges shone again."
        )
    if hero.meters["dusty"] >= THRESHOLD:
        hero.memes["relief"] += 1
        world.say(
            f"{helper.id} handed {hero.pronoun('object')} a napkin for one last sniffly wipe, "
            f"which made the brave explorer look much less like a dusty dragon."
        )


def fix_sign(world: World, feast: Feast, hero: Entity, helper: Entity, grownup: Entity) -> None:
    sign = world.get("sign")
    sign.meters["fixed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Back at the table, {hero.id} pressed the missing consonant into place. "
        f'The sign finally read "{feast.full_sign}."'
    )
    world.say(
        f'{grownup.label_word.capitalize()} let out a happy breath. "Now the feast '
        f'looks ready for guests instead of geese," {grownup.pronoun()} said.'
    )
    world.say(
        f"{helper.id} bowed to the stuffed bear, the sock dragon, and the wobbling line "
        f"of toy customers. {feast.ending_line}"
    )


def tell(
    feast: Feast,
    location: Location,
    tool: Tool,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    grownup_name: str,
    grownup_role: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        attrs={},
        tags={"quester"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        attrs={},
        tags={"helper"},
    ))
    grownup = world.add(Entity(
        id=grownup_name,
        kind="character",
        type=grownup_role,
        role="grownup",
        label="the grown-up",
        attrs={},
        tags={"adult"},
    ))
    sign = world.add(Entity(
        id="sign",
        type="sign",
        label="sign",
        attrs={"full_text": feast.full_sign, "broken_text": feast.broken_sign},
        tags={"sign"},
    ))
    letter = world.add(Entity(
        id="letter",
        type="tile",
        label=f'{feast.missing_letter} tile',
        attrs={"letter": feast.missing_letter},
        tags={"letter"},
    ))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        attrs={"keeps_hands_clean": tool.keeps_hands_clean},
        tags=set(tool.tags),
    ))

    hero.attrs["trait"] = trait
    hero.memes["quest"] = 0.0
    hero.memes["relief"] = 0.0
    helper.memes["joy"] = 0.0
    grownup.memes["weariness"] = 0.0
    sign.meters["fixed"] = 0.0
    letter.meters["retrieved"] = 0.0
    letter.meters["muddy"] = 0.0
    hero.meters["dusty"] = 0.0

    world.facts.update(
        feast=feast,
        location=location,
        tool=tool,
        hero=hero,
        helper=helper,
        grownup=grownup,
        sign=sign,
        letter=letter,
        outcome="",
    )

    introduce(world, feast, hero, helper, grownup)
    world.para()
    call_to_quest(world, feast, hero, helper, grownup, location)
    hero.memes["quest"] += 1
    choose_tool(world, hero, helper, tool, location)
    world.para()
    retrieve(world, hero, helper, location, tool, feast)
    clean_tile(world, hero, helper, grownup)
    world.para()
    fix_sign(world, feast, hero, helper, grownup)

    world.facts["outcome"] = outcome_of(StoryParams(
        feast=feast.id,
        location=location.id,
        tool=tool.id,
        hero=hero_name,
        hero_gender=hero_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        grownup=grownup_name,
        grownup_role=grownup_role,
        trait=trait,
    ))
    return world


KNOWLEDGE = {
    "consonant": [
        (
            "What is a consonant?",
            "A consonant is a letter that is not a vowel. Letters like B, R, and M are consonants."
        )
    ],
    "sign": [
        (
            "Why does one missing letter matter on a sign?",
            "One missing letter can change how a word looks and sounds. That can make the sign confusing or very funny."
        )
    ],
    "dust": [
        (
            "What are dust bunnies?",
            "Dust bunnies are little fluffy clumps of dust and lint that gather under furniture. They are not real bunnies, even though they look funny."
        )
    ],
    "mud": [
        (
            "Why does mud stick to things?",
            "Mud is wet dirt, so it clings to shoes and small objects. That is why muddy things often need to be wiped clean."
        )
    ],
    "broom": [
        (
            "What is a broom for?",
            "A broom is used to sweep dirt or small things across the floor. It can help reach under furniture from a safe distance."
        )
    ],
    "grabber": [
        (
            "What does a grabber do?",
            "A grabber lets you pinch and pick up something without putting your hand into a hard-to-reach place. It helps you reach safely."
        )
    ],
    "stool": [
        (
            "Why is a step stool useful?",
            "A step stool helps you reach something high in a steady way. It is better than climbing on wobbly furniture."
        )
    ],
    "boots": [
        (
            "Why do rain boots help on a wet path?",
            "Rain boots help keep feet dry and steady on damp ground. They make muddy places easier to cross safely."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    feast = world.facts["feast"]
    location = world.facts["location"]
    hero = world.facts["hero"]
    grownup = world.facts["grownup"]
    return [
        f'Write a short comedy story for a 3-to-5-year-old about a quest to find a missing consonant for a snack sign. Include the words "consonant" and "weary".',
        f"Tell a silly quest where {hero.id} must recover the letter {feast.missing_letter} from {location.label} after a weary {grownup.label_word} notices the sign is wrong.",
        f'Write a child-friendly story where one lost letter makes a feast sign look ridiculous, and two children solve the problem with a sensible plan and a funny ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    feast = world.facts["feast"]
    location = world.facts["location"]
    tool = world.facts["tool"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    grownup = world.facts["grownup"]
    out = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "What was the problem at the start of the story?",
            f'The feast sign was missing one consonant, so it said "{feast.broken_sign}" instead of "{feast.full_sign}." That made the sign look silly and started the quest.'
        ),
        (
            f"Why did {hero.id} start a quest?",
            f"{hero.id} wanted to bring back the missing {feast.missing_letter} tile so the feast sign would make sense again. {grownup.label_word.capitalize()} was weary from getting the food ready, so helping was a kind and useful thing to do."
        ),
        (
            f"Where did they find the tile, and how did they get it?",
            f"They tracked the tile to {location.label}. {hero.id} used {tool.phrase} to reach it in a sensible way instead of making the quest more troublesome."
        ),
    ]
    if out == "sneezy":
        qa.append((
            f"Why did {hero.id} sneeze during the quest?",
            f"The tile was hidden in a dusty place under the sofa, and the broom stirred the dust while {hero.id} swept it out. The tool worked, but it made the rescue funny and sniffly."
        ))
    elif out == "muddy":
        qa.append((
            "Why did they wipe the tile before fixing the sign?",
            f"The tile had come from a muddy path, so one corner was dirty when {hero.id} picked it up. They cleaned it before putting it back so the sign would look neat again."
        ))
    else:
        qa.append((
            "What changed at the end of the story?",
            f'The missing tile went back onto the sign, so it finally read "{feast.full_sign}." The quest ended with the feast ready and everyone feeling relieved and proud.'
        ))
    qa.append((
        "How did the story end?",
        f'The sign was fixed, the toy customers were welcomed, and the whole room felt cheerful again. {helper.id} and {hero.id} finished the quest by turning a small problem into a joke everyone could enjoy.'
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    location = world.facts["location"]
    tool = world.facts["tool"]
    tags = {"consonant", "sign"} | set(location.tags) | set(tool.tags)
    ordered = ["consonant", "sign", "dust", "mud", "broom", "grabber", "stool", "boots"]
    out: list[tuple[str, str]] = []
    for tag in ordered:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None, 0, 0.0, False)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        feast="pretzels",
        location="under_sofa",
        tool="broom",
        hero="Lily",
        hero_gender="girl",
        helper="Ben",
        helper_gender="boy",
        grownup="Aunt June",
        grownup_role="aunt",
        trait="dramatic",
    ),
    StoryParams(
        feast="cookies",
        location="high_fridge",
        tool="step_stool",
        hero="Max",
        hero_gender="boy",
        helper="Mia",
        helper_gender="girl",
        grownup="Dad",
        grownup_role="father",
        trait="determined",
    ),
    StoryParams(
        feast="muffins",
        location="garden_path",
        tool="boots",
        hero="Zoe",
        hero_gender="girl",
        helper="Theo",
        helper_gender="boy",
        grownup="Mom",
        grownup_role="mother",
        trait="cheerful",
    ),
    StoryParams(
        feast="cookies",
        location="under_sofa",
        tool="grabber",
        hero="Eli",
        hero_gender="boy",
        helper="Nora",
        helper_gender="girl",
        grownup="Uncle Rob",
        grownup_role="uncle",
        trait="curious",
    ),
    StoryParams(
        feast="pretzels",
        location="high_fridge",
        tool="grabber",
        hero="Ava",
        hero_gender="girl",
        helper="Finn",
        helper_gender="boy",
        grownup="Aunt May",
        grownup_role="aunt",
        trait="bouncy",
    ),
]


ASP_RULES = r"""
valid(F, L, T) :- feast(F), location(L), tool(T), needs(L, R), reaches(T, R), sense(T, S), sense_min(M), S >= M, power(T, P), P >= 2.

sneezy :- chosen_location(L), terrain(L, dust), chosen_tool(T), not keeps_clean(T).
muddy  :- chosen_location(L), terrain(L, mud).
tidy   :- chosen_location(L), terrain(L, clean).
tidy   :- chosen_location(L), terrain(L, dust), chosen_tool(T), keeps_clean(T).

outcome(sneezy) :- sneezy.
outcome(muddy)  :- muddy.
outcome(tidy)   :- tidy, not sneezy, not muddy.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for feast_id in FEASTS:
        lines.append(asp.fact("feast", feast_id))
    for loc_id, loc in LOCATIONS.items():
        lines.append(asp.fact("location", loc_id))
        lines.append(asp.fact("needs", loc_id, loc.reach))
        lines.append(asp.fact("terrain", loc_id, loc.terrain))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("power", tool_id, tool.power))
        for reach in sorted(tool.reaches):
            lines.append(asp.fact("reaches", tool_id, reach))
        if tool.keeps_hands_clean:
            lines.append(asp.fact("keeps_clean", tool_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_location", params.location),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comic quest storyworld about recovering a missing consonant tile."
    )
    ap.add_argument("--feast", choices=FEASTS)
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--grownup-role", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))
    if args.location and args.tool:
        loc = LOCATIONS[args.location]
        tool = TOOLS[args.tool]
        if not compatible(loc, tool):
            raise StoryError(explain_rejection(loc, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.feast is None or combo[0] == args.feast)
        and (args.location is None or combo[1] == args.location)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    feast_id, location_id, tool_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or _pick_name(rng, hero_gender)
    helper_name = args.helper or _pick_name(rng, helper_gender, avoid=hero_name)
    grownup_role = args.grownup_role or rng.choice(["mother", "father", "aunt", "uncle"])
    grownup_name = {
        "mother": "Mom",
        "father": "Dad",
        "aunt": rng.choice(["Aunt June", "Aunt May", "Aunt Bea"]),
        "uncle": rng.choice(["Uncle Rob", "Uncle Jay", "Uncle Mo"]),
    }[grownup_role]
    trait = rng.choice(TRAITS)
    return StoryParams(
        feast=feast_id,
        location=location_id,
        tool=tool_id,
        hero=hero_name,
        hero_gender=hero_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        grownup=grownup_name,
        grownup_role=grownup_role,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.feast not in FEASTS:
        raise StoryError(f"(Unknown feast: {params.feast})")
    if params.location not in LOCATIONS:
        raise StoryError(f"(Unknown location: {params.location})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    feast = FEASTS[params.feast]
    location = LOCATIONS[params.location]
    tool = TOOLS[params.tool]

    if not compatible(location, tool):
        raise StoryError(explain_rejection(location, tool))

    world = tell(
        feast=feast,
        location=location,
        tool=tool,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        grownup_name=params.grownup,
        grownup_role=params.grownup_role,
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

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid combos match ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (feast, location, tool) combos:\n")
        for feast, location, tool in combos:
            print(f"  {feast:10} {location:12} {tool}")
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
            header = (
                f"### {sample.params.hero}: {sample.params.feast} at {sample.params.location} "
                f"with {sample.params.tool} ({outcome_of(sample.params)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
