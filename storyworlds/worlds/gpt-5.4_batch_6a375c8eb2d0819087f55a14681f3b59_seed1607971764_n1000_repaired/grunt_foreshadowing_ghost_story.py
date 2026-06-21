#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/grunt_foreshadowing_ghost_story.py
=============================================================

A standalone story world for a tiny ghost-story domain: a child hears a spooky
grunt from a dark outbuilding, fears a ghost, notices clues that quietly
foreshadow an ordinary cause, and then learns the truth by helping.

This world models:
- a gloomy place at dusk,
- an animal trapped in a shelter,
- concrete clues that foreshadow the reveal,
- a helper whose calmness may steady the child,
- a tool that may or may not let them open the latch right away,
- a resolution that changes what the child believes.

Run it
------
    python storyworlds/worlds/gpt-5.4/grunt_foreshadowing_ghost_story.py
    python storyworlds/worlds/gpt-5.4/grunt_foreshadowing_ghost_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/grunt_foreshadowing_ghost_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/grunt_foreshadowing_ghost_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/grunt_foreshadowing_ghost_story.py --json
    python storyworlds/worlds/gpt-5.4/grunt_foreshadowing_ghost_story.py --verify
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
    attrs: dict = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    path: str
    shelter_word: str
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
class Shelter:
    id: str
    label: str
    phrase: str
    latch: str
    dark_detail: str
    cozy_for: set[str] = field(default_factory=set)
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
class Animal:
    id: str
    label: str
    phrase: str
    sound: str
    track: str
    clue_item: str
    warmth: str
    likes: str
    species_tag: str
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
class HelperCfg:
    id: str
    type: str
    phrase: str
    calm: int
    line: str
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    gives_light: bool
    opens: set[str] = field(default_factory=set)
    comfort: int = 0
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


def _r_noise(world: World) -> list[str]:
    animal = world.get("animal")
    shelter = world.get("shelter")
    if animal.meters["trapped"] < THRESHOLD:
        return []
    sig = ("noise", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("child").memes["fear"] += 1
    shelter.meters["spooky"] += 1
    return ["__noise__"]


def _r_clue_softens(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if world.facts.get("clues_seen", 0) < 2:
        return []
    if helper.attrs.get("calm", 0) < CALM_MIN:
        return []
    sig = ("soften", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    child.memes["wonder"] += 1
    child.memes["trust"] += 1
    return ["__soften__"]


def _r_free(world: World) -> list[str]:
    animal = world.get("animal")
    if animal.meters["trapped"] >= THRESHOLD or world.get("shelter").meters["open"] < THRESHOLD:
        return []
    sig = ("free", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child = world.get("child")
    helper = world.get("helper")
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.memes["ghost_belief"] = 0.0
    helper.memes["relief"] += 1
    return ["__free__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="clue_softens", tag="emotional", apply=_r_clue_softens),
    Rule(name="free", tag="physical", apply=_r_free),
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
    "orchard": Setting(
        id="orchard",
        place="the old orchard behind the house",
        sky="The evening sky was purple, and the last light sat thin on the branches.",
        path="a narrow path between crooked apple trees",
        shelter_word="shed",
        tags={"night", "orchard"},
    ),
    "marsh": Setting(
        id="marsh",
        place="the reed path by the marsh cottage",
        sky="Mist curled low over the reeds, and the moon looked blurred behind it.",
        path="a damp board path over the dark grass",
        shelter_word="boathouse",
        tags={"night", "marsh"},
    ),
    "hill": Setting(
        id="hill",
        place="the windy hill behind the farm",
        sky="Clouds slid over the moon, and the air smelled of rain and hay.",
        path="a stony path beside the fence",
        shelter_word="barn",
        tags={"night", "hill"},
    ),
}

SHELTERS = {
    "apple_shed": Shelter(
        id="apple_shed",
        label="shed",
        phrase="the leaning apple shed",
        latch="wooden_bar",
        dark_detail="Its door leaned crooked, and the black gap under it looked like a long mouth.",
        cozy_for={"piglet"},
        tags={"shed", "door"},
    ),
    "tool_boathouse": Shelter(
        id="tool_boathouse",
        label="boathouse",
        phrase="the little boathouse with peeling blue paint",
        latch="rope_knot",
        dark_detail="Its boards creaked against the water, and the shadows between them looked deep enough to hide secrets.",
        cozy_for={"piglet"},
        tags={"boathouse", "door"},
    ),
    "hay_barn": Shelter(
        id="hay_barn",
        label="barn",
        phrase="the small hay barn at the edge of the field",
        latch="iron_hook",
        dark_detail="Its high door stood shut, and every crack in the boards seemed to breathe cold air.",
        cozy_for={"piglet", "goat"},
        tags={"barn", "door"},
    ),
}

ANIMALS = {
    "piglet": Animal(
        id="piglet",
        label="piglet",
        phrase="a round little piglet",
        sound="a low frightened grunt",
        track="tiny split hoofprints",
        clue_item="a half-chewed apple core",
        warmth="warm pink ears",
        likes="apples",
        species_tag="hoof",
        tags={"animal", "piglet", "hoof", "grunt"},
    ),
    "goat": Animal(
        id="goat",
        label="goat kid",
        phrase="a shaggy baby goat",
        sound="a rough little grunt",
        track="small hoofprints and nibbled straw",
        clue_item="a strip of nibbled rope",
        warmth="a warm woolly neck",
        likes="hay",
        species_tag="hoof",
        tags={"animal", "goat", "hoof", "grunt"},
    ),
}

HELPERS = {
    "grandma": HelperCfg(
        id="grandma",
        type="grandmother",
        phrase="Grandma",
        calm=3,
        line="Ghosts do not usually leave crumbs and hoofprints.",
        tags={"adult", "grandma"},
    ),
    "grandpa": HelperCfg(
        id="grandpa",
        type="grandfather",
        phrase="Grandpa",
        calm=3,
        line="Let us look with our eyes before we let our fear do the talking.",
        tags={"adult", "grandpa"},
    ),
    "cousin": HelperCfg(
        id="cousin",
        type="girl",
        phrase="older cousin June",
        calm=2,
        line="Spooky sounds still come from something real.",
        tags={"child_helper", "cousin"},
    ),
}

TOOLS = {
    "lantern": ToolCfg(
        id="lantern",
        label="lantern",
        phrase="a brass lantern",
        gives_light=True,
        opens={"wooden_bar", "iron_hook"},
        comfort=1,
        tags={"light", "lantern"},
    ),
    "key": ToolCfg(
        id="key",
        label="hook key",
        phrase="a hook key on a string",
        gives_light=False,
        opens={"iron_hook"},
        comfort=0,
        tags={"key"},
    ),
    "rope_pull": ToolCfg(
        id="rope_pull",
        label="looped rope",
        phrase="a looped rope with a wooden handle",
        gives_light=False,
        opens={"rope_knot", "wooden_bar"},
        comfort=0,
        tags={"rope"},
    ),
    "lamp_and_key": ToolCfg(
        id="lamp_and_key",
        label="lamp and key",
        phrase="a small hand-lamp and the old hook key",
        gives_light=True,
        opens={"iron_hook"},
        comfort=1,
        tags={"light", "key", "lamp"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ivy", "June", "Rosa", "Elsie"]
BOY_NAMES = ["Owen", "Finn", "Eli", "Theo", "Milo", "Ben", "Jonah", "Toby"]
TRAITS = ["curious", "timid", "careful", "brave", "thoughtful", "watchful"]


def habitat_ok(shelter: Shelter, animal: Animal) -> bool:
    return animal.id in shelter.cozy_for


def useful_tool(shelter: Shelter, tool: ToolCfg) -> bool:
    return shelter.latch in tool.opens


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id in SETTINGS:
        for shelter_id, shelter in SHELTERS.items():
            for animal_id, animal in ANIMALS.items():
                if not habitat_ok(shelter, animal):
                    continue
                combos.append((setting_id, shelter_id, animal_id))
    return combos


def sensible_tools_for(shelter: Shelter) -> list[str]:
    return [tid for tid, tool in TOOLS.items() if useful_tool(shelter, tool)]


@dataclass
class StoryParams:
    setting: str
    shelter: str
    animal: str
    helper: str
    tool: str
    child_name: str
    child_gender: str
    child_trait: str
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


def hear_grunt(world: World, animal: Animal, shelter: Shelter) -> None:
    child = world.get("child")
    child.memes["ghost_belief"] += 1
    world.say(
        f"Then, from inside {shelter.phrase}, there came {animal.sound}. "
        f"To {child.id}, it did not sound like an animal at all. It sounded like the sort of noise a ghost might make if it were trying not to be heard."
    )
    propagate(world, narrate=False)


def show_clues(world: World, animal: Animal, setting: Setting) -> None:
    child = world.get("child")
    helper = world.get("helper")
    world.facts["clues_seen"] = 2
    world.say(
        f"As they stood on {setting.path}, {child.id} saw {animal.track} pressed into the damp ground."
    )
    world.say(
        f"Near the door lay {animal.clue_item}. It was such a small, ordinary thing that it felt almost silly beside the scary sound."
    )
    world.say(
        f'{helper.attrs["display"]} bent close and whispered, "{helper.attrs["line"]}"'
    )
    propagate(world, narrate=False)


def child_ready(world: World) -> bool:
    child = world.get("child")
    helper = world.get("helper")
    fear = child.memes["fear"] + child.memes["ghost_belief"]
    steady = child.memes["wonder"] + child.memes["trust"] + helper.attrs.get("calm", 0)
    if "brave" in child.traits:
        steady += 1
    if "timid" in child.traits:
        fear += 1
    return steady >= fear


def open_now(world: World) -> bool:
    return child_ready(world) and world.get("tool").attrs.get("can_open", False)


def introduce(world: World, setting: Setting, shelter: Shelter) -> None:
    child = world.get("child")
    helper = world.get("helper")
    world.say(
        f"{child.id} was walking with {helper.attrs['display']} through {setting.place} when the evening began to feel strange."
    )
    world.say(setting.sky)
    world.say(shelter.dark_detail)


def first_shiver(world: World) -> None:
    child = world.get("child")
    child.memes["fear"] += 1
    world.say(
        f"{child.id} stopped and listened. The path was quiet enough for little noises to seem bigger than they were."
    )


def choose_tool(world: World, tool: ToolCfg) -> None:
    helper = world.get("helper")
    child = world.get("child")
    if tool.gives_light:
        world.say(
            f'{helper.attrs["display"]} lifted {tool.phrase}. The warm circle of light made the dark door look smaller.'
        )
    else:
        world.say(
            f'{helper.attrs["display"]} took out {tool.phrase}. It was useful, but it did not make the shadows any less deep.'
        )
    if tool.comfort:
        child.memes["trust"] += 1


def rescue_night(world: World, animal: Animal, shelter: Shelter) -> None:
    child = world.get("child")
    helper = world.get("helper")
    tool = world.get("tool")
    shelter.meters["open"] += 1
    world.say(
        f"Very softly, {helper.attrs['display']} worked at the {shelter.latch.replace('_', ' ')} with the {tool.label}."
    )
    world.say(
        f"The door gave a tired scrape. Out blinked {animal.phrase}, shivering and confused, not a ghost at all."
    )
    world.get("animal").meters["trapped"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{child.id} let out a breath that felt as if it had been stuck inside {child.pronoun('object')} all evening."
    )
    world.say(
        f"When {child.pronoun()} touched {animal.warmth}, the last of the ghost-story feeling melted away."
    )


def dawn_wait(world: World, animal: Animal, shelter: Shelter) -> None:
    child = world.get("child")
    helper = world.get("helper")
    world.say(
        f"{child.id} wanted to be brave, but the night still felt too thick and strange."
    )
    world.say(
        f'{helper.attrs["display"]} did not laugh. "{helper.attrs["display"]} can wait for morning," {helper.pronoun()} said. "Fear grows bigger in the dark."'
    )
    world.para()
    world.say(
        f"At dawn they came back, and the world no longer looked haunted. There, behind the door of {shelter.phrase}, stood {animal.phrase}, hungry and tired."
    )
    world.say(
        f"In daylight, even the remembered grunt sounded different inside {child.id}'s mind."
    )
    world.get("shelter").meters["open"] += 1
    world.get("animal").meters["trapped"] = 0.0
    child.memes["ghost_belief"] = 0.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["relief"] += 1
    propagate(world, narrate=False)


def ending(world: World, animal: Animal) -> None:
    child = world.get("child")
    helper = world.get("helper")
    if world.facts["outcome"] == "night_rescue":
        world.say(
            f'That night, when the wind touched the windows, {child.id} still remembered the dark and the grunt. But now {child.pronoun()} remembered something else too: clues, hoofprints, and the warm weight of something real.'
        )
        world.say(
            f"After that, spooky noises made {child.pronoun('object')} listen harder before calling them ghosts."
        )
    else:
        world.say(
            f"Later, with {animal.likes} in a bowl and the frightened little creature safe, {child.id} felt a new kind of courage."
        )
        world.say(
            f"{helper.attrs['display']} smiled and said that not every ghost story ends with a ghost. Some end with kindness and a full supper."
        )


def tell(
    setting: Setting,
    shelter_cfg: Shelter,
    animal_cfg: Animal,
    helper_cfg: HelperCfg,
    tool_cfg: ToolCfg,
    child_name: str,
    child_gender: str,
    child_trait: str,
) -> World:
    world = World()

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        attrs={},
        traits=[child_trait],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.phrase,
        attrs={"calm": helper_cfg.calm, "display": helper_cfg.phrase, "line": helper_cfg.line},
        traits=["calm"],
        tags=set(helper_cfg.tags),
    ))
    animal = world.add(Entity(
        id="animal",
        kind="thing",
        type="animal",
        label=animal_cfg.label,
        attrs={"sound": animal_cfg.sound},
        tags=set(animal_cfg.tags),
    ))
    shelter = world.add(Entity(
        id="shelter",
        kind="thing",
        type="shelter",
        label=shelter_cfg.label,
        attrs={"latch": shelter_cfg.latch},
        tags=set(shelter_cfg.tags),
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_cfg.label,
        attrs={"can_open": useful_tool(shelter_cfg, tool_cfg), "light": tool_cfg.gives_light},
        tags=set(tool_cfg.tags),
    ))

    world.facts["clues_seen"] = 0
    animal.meters["trapped"] = 1.0
    shelter.meters["open"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["ghost_belief"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["joy"] = 0.0
    helper.memes["relief"] = 0.0

    introduce(world, setting, shelter_cfg)
    first_shiver(world)

    world.para()
    hear_grunt(world, animal_cfg, shelter_cfg)
    show_clues(world, animal_cfg, setting)
    choose_tool(world, tool_cfg)

    world.para()
    if open_now(world):
        rescue_night(world, animal_cfg, shelter_cfg)
        outcome = "night_rescue"
    else:
        dawn_wait(world, animal_cfg, shelter_cfg)
        outcome = "morning_rescue"

    world.para()
    ending(world, animal_cfg)

    world.facts.update(
        setting=setting,
        shelter_cfg=shelter_cfg,
        animal_cfg=animal_cfg,
        helper_cfg=helper_cfg,
        tool_cfg=tool_cfg,
        child=child,
        helper=helper,
        animal=animal,
        shelter=shelter,
        tool=tool,
        outcome=outcome,
        opened_at_night=outcome == "night_rescue",
        ghost_belief_cleared=child.memes["ghost_belief"] < THRESHOLD,
        clues_seen=2,
    )
    return world


KNOWLEDGE = {
    "ghost_story": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story shows small clues early on that hint at what will happen later. Those clues help the ending feel surprising and fair at the same time."
        )
    ],
    "hoof": [
        (
            "What can hoofprints tell you?",
            "Hoofprints can show that an animal with hard little feet walked there. They are clues about who passed by, even when you did not see the animal."
        )
    ],
    "lantern": [
        (
            "Why is a lantern useful in the dark?",
            "A lantern makes a steady light, so you can see where you are going. Light often makes confusing shadows less scary too."
        )
    ],
    "piglet": [
        (
            "What sound can a piglet make?",
            "A piglet can squeal, snuffle, or make a little grunt. If you cannot see it, that sound might seem strange or spooky."
        )
    ],
    "goat": [
        (
            "Can a baby goat sound strange at night?",
            "Yes. A baby goat can bleat, rustle, or make a rough little grunt, and nighttime can make ordinary sounds feel eerie."
        )
    ],
    "night": [
        (
            "Why do things seem scarier at night?",
            "At night, you can see less clearly, so your mind tries to fill in the missing parts. That can make ordinary sounds and shadows feel bigger than they are."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost_story", "night", "hoof", "lantern", "piglet", "goat"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper_cfg"]
    shelter = f["shelter_cfg"]
    animal = f["animal_cfg"]
    outcome = f["outcome"]
    if outcome == "night_rescue":
        return [
            'Write a gentle ghost story for a 3-to-5-year-old that includes the word "grunt" and uses foreshadowing clues.',
            f"Tell a spooky-but-kind story where {child.id} hears a grunt from {shelter.phrase}, fears a ghost, notices hoofy clues, and learns the noise came from {animal.phrase}.",
            f"Write a ghost-story-style tale with a calm helper like {helper.phrase}, two early clues, and an ending where fear turns into understanding."
        ]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the word "grunt" and uses foreshadowing clues.',
        f"Tell a night story where {child.id} thinks a ghost is hiding in {shelter.phrase}, but morning reveals {animal.phrase} instead.",
        "Write a spooky story with small honest clues that point to a real creature, and end with the child feeling braver than before."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    shelter = f["shelter_cfg"]
    animal = f["animal_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who heard a scary sound at {setting.place}, and {helper.attrs['display']}, who stayed calm. The story follows how they found out what was really making the noise."
        ),
        (
            "What made the place feel spooky at first?",
            f"The evening was dark, the shelter looked strange, and then a low grunt came from inside {shelter.phrase}. Those details made {child.id} imagine a ghost before {child.pronoun()} knew the truth."
        ),
        (
            "What clues foreshadowed the real answer?",
            f"The story showed {animal.track} and {animal.clue_item} before the door was opened. Those clues pointed to an animal, so the ending had been quietly hinted at all along."
        ),
    ]
    if outcome == "night_rescue":
        qa.append(
            (
                f"How did {child.id} stop being afraid?",
                f"{helper.attrs['display']} used calm words and real clues, and {tool.phrase} helped them look closely. Once the door opened and {child.id} saw {animal.phrase}, fear turned into relief because the scary sound had a real cause."
            )
        )
        qa.append(
            (
                f"Why was the {tool.label} important?",
                f"It helped them deal with the dark and open the shelter right away. Because they could act that same night, the mystery changed into a rescue instead of staying a ghost story in {child.id}'s head."
            )
        )
    else:
        qa.append(
            (
                f"Why did they wait until morning?",
                f"{child.id} was still too frightened to go closer in the dark. Waiting for daylight made everything easier to see, and that helped them discover the truth safely."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {animal.phrase} safe and fed, not with a ghost at all. The ending shows that scary guesses can shrink when light and patience arrive."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost_story", "night", "hoof"}
    if f["tool_cfg"].gives_light:
        tags.add("lantern")
    if f["animal_cfg"].id == "piglet":
        tags.add("piglet")
    if f["animal_cfg"].id == "goat":
        tags.add("goat")

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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: {{'outcome': {world.facts.get('outcome')!r}, 'clues_seen': {world.facts.get('clues_seen')!r}}}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="orchard",
        shelter="apple_shed",
        animal="piglet",
        helper="grandma",
        tool="lantern",
        child_name="Mina",
        child_gender="girl",
        child_trait="careful",
    ),
    StoryParams(
        setting="hill",
        shelter="hay_barn",
        animal="goat",
        helper="grandpa",
        tool="lamp_and_key",
        child_name="Owen",
        child_gender="boy",
        child_trait="curious",
    ),
    StoryParams(
        setting="marsh",
        shelter="tool_boathouse",
        animal="piglet",
        helper="cousin",
        tool="rope_pull",
        child_name="Ivy",
        child_gender="girl",
        child_trait="timid",
    ),
    StoryParams(
        setting="hill",
        shelter="hay_barn",
        animal="piglet",
        helper="cousin",
        tool="key",
        child_name="Theo",
        child_gender="boy",
        child_trait="timid",
    ),
]


def explain_rejection(shelter: Shelter, animal: Animal, tool: Optional[ToolCfg] = None) -> str:
    if not habitat_ok(shelter, animal):
        return (
            f"(No story: {animal.label} does not fit naturally in {shelter.phrase}. "
            f"The foreshadowing would feel unfair if the reveal did not belong there.)"
        )
    if tool is not None and not useful_tool(shelter, tool):
        return (
            f"(No story: {tool.label} does not open a {shelter.latch.replace('_', ' ')}. "
            f"Pick a tool that can actually help with that door.)"
        )
    return "(No story: this combination is not reasonable in the world model.)"


def outcome_of(params: StoryParams) -> str:
    shelter = SHELTERS[params.shelter]
    helper = HELPERS[params.helper]
    tool = TOOLS[params.tool]
    score = helper.calm + (1 if tool.gives_light else 0)
    if params.child_trait == "brave":
        score += 1
    if params.child_trait == "timid":
        score -= 1
    return "night_rescue" if useful_tool(shelter, tool) and score >= 2 else "morning_rescue"


ASP_RULES = r"""
% --- reasonableness --------------------------------------------------------
valid(Setting, Shelter, Animal) :- setting(Setting), shelter(Shelter), animal(Animal), cozy_for(Shelter, Animal).
useful_tool(Shelter, Tool) :- latch(Shelter, L), opens(Tool, L).

% --- outcome ---------------------------------------------------------------
trait_score(brave, 1).
trait_score(timid, -1).
trait_score(curious, 0).
trait_score(careful, 0).
trait_score(thoughtful, 0).
trait_score(watchful, 0).

light_bonus(1) :- chosen_tool(T), gives_light(T).
light_bonus(0) :- chosen_tool(T), not gives_light(T).

courage(TS + CS + LB) :-
    chosen_helper(H), calm(H, CS),
    chosen_trait(T), trait_score(T, TS),
    light_bonus(LB).

night_rescue :- chosen_shelter(S), chosen_tool(T), useful_tool(S, T), courage(C), C >= 2.
morning_rescue :- not night_rescue.

outcome(night_rescue) :- night_rescue.
outcome(morning_rescue) :- morning_rescue.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for shid, shelter in SHELTERS.items():
        lines.append(asp.fact("shelter", shid))
        lines.append(asp.fact("latch", shid, shelter.latch))
        for aid in sorted(shelter.cozy_for):
            lines.append(asp.fact("cozy_for", shid, aid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("calm", hid, helper.calm))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.gives_light:
            lines.append(asp.fact("gives_light", tid))
        for latch in sorted(tool.opens):
            lines.append(asp.fact("opens", tid, latch))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_useful_tools() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show useful_tool/2."))
    return sorted(set(asp.atoms(model, "useful_tool")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_shelter", params.shelter),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_trait", params.child_trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child hears a spooky grunt, follows clues, and learns what is real."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shelter", choices=SHELTERS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shelter and args.animal:
        shelter = SHELTERS[args.shelter]
        animal = ANIMALS[args.animal]
        if not habitat_ok(shelter, animal):
            raise StoryError(explain_rejection(shelter, animal))
    if args.shelter and args.tool:
        shelter = SHELTERS[args.shelter]
        tool = TOOLS[args.tool]
        if not useful_tool(shelter, tool):
            raise StoryError(explain_rejection(shelter, next(iter(ANIMALS.values())), tool))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.shelter is None or c[1] == args.shelter)
        and (args.animal is None or c[2] == args.animal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, shelter_id, animal_id = rng.choice(sorted(combos))
    shelter = SHELTERS[shelter_id]

    possible_tools = [
        tid for tid in sensible_tools_for(shelter)
        if args.tool is None or tid == args.tool
    ]
    if not possible_tools:
        raise StoryError("(No usable tool matches the given options.)")

    helper_id = args.helper or rng.choice(sorted(HELPERS))
    tool_id = rng.choice(sorted(possible_tools))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    child_trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        shelter=shelter_id,
        animal=animal_id,
        helper=helper_id,
        tool=tool_id,
        child_name=child_name,
        child_gender=gender,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        shelter = SHELTERS[params.shelter]
        animal = ANIMALS[params.animal]
        helper = HELPERS[params.helper]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]!r})") from None

    if not habitat_ok(shelter, animal):
        raise StoryError(explain_rejection(shelter, animal))
    if not useful_tool(shelter, tool):
        raise StoryError(explain_rejection(shelter, animal, tool))
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError("(No story: child gender must be 'girl' or 'boy'.)")
    if not params.child_name:
        raise StoryError("(No story: child_name must not be empty.)")

    world = tell(
        setting=setting,
        shelter_cfg=shelter,
        animal_cfg=animal,
        helper_cfg=helper,
        tool_cfg=tool,
        child_name=params.child_name,
        child_gender=params.child_gender,
        child_trait=params.child_trait,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_tools = {
        (sid, tid)
        for sid, shelter in SHELTERS.items()
        for tid, tool in TOOLS.items()
        if useful_tool(shelter, tool)
    }
    asp_tools = set(asp_useful_tools())
    if py_tools == asp_tools:
        print(f"OK: useful tools match ({len(py_tools)} pairs).")
    else:
        rc = 1
        print("MISMATCH in useful tools:")
        if asp_tools - py_tools:
            print("  only in clingo:", sorted(asp_tools - py_tools))
        if py_tools - asp_tools:
            print("  only in python:", sorted(py_tools - asp_tools))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    mismatch = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0] if cases else CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show useful_tool/2.\n#show outcome/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        tools = asp_useful_tools()
        print(f"{len(combos)} compatible (setting, shelter, animal) combos:\n")
        for setting_id, shelter_id, animal_id in combos:
            usable = sorted(t for s, t in tools if s == shelter_id)
            print(f"  {setting_id:8} {shelter_id:14} {animal_id:8}  tools=[{', '.join(usable)}]")
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
            header = f"### {p.child_name}: {p.shelter} / {p.animal} / {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
