#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stagger_week_sound_effects_dialogue_ghost_story.py
=============================================================================

A standalone story world for a child-facing ghost-story domain: a child hears a
supposed ghost in an old house, fear grows through the night, and a careful
investigation reveals an ordinary cause. The prose is state-driven: wind, loose
objects, darkness, courage, and help determine what happens and how it is told.

This world keeps the mood of a ghost story while ending safely and concretely.
It also includes sound effects and dialogue in every sample, and always uses the
words "stagger" and "week" in the rendered story.

Run it
------
    python storyworlds/worlds/gpt-5.4/stagger_week_sound_effects_dialogue_ghost_story.py
    python storyworlds/worlds/gpt-5.4/stagger_week_sound_effects_dialogue_ghost_story.py --cause shutters --place attic
    python storyworlds/worlds/gpt-5.4/stagger_week_sound_effects_dialogue_ghost_story.py --cause mice --place chimney
    python storyworlds/worlds/gpt-5.4/stagger_week_sound_effects_dialogue_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/stagger_week_sound_effects_dialogue_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/stagger_week_sound_effects_dialogue_ghost_story.py --trace
    python storyworlds/worlds/gpt-5.4/stagger_week_sound_effects_dialogue_ghost_story.py --json
    python storyworlds/worlds/gpt-5.4/stagger_week_sound_effects_dialogue_ghost_story.py --verify
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
BRAVE_ENOUGH = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "grandmother", "woman"}
        male = {"boy", "father", "uncle", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    room: str
    phrase: str
    dark_feature: str
    echo: str
    allows: set[str] = field(default_factory=set)
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
class Cause:
    id: str
    label: str
    noise: str
    effect: str
    material: str
    needs_wind: bool = False
    needs_small_gap: bool = False
    moving_thing: str = ""
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
class LightTool:
    id: str
    phrase: str
    beam: str
    safe: bool = True
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
class HelperStyle:
    id: str
    title: str
    calm_line: str
    fix_line: str
    brave_bonus: int
    type: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_noise_spooks(world: World) -> list[str]:
    out: list[str] = []
    house = world.get("house")
    child = world.get("child")
    if house.meters["noise"] >= THRESHOLD:
        sig = ("spook", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            out.append("__spook__")
    return out


def _r_fear_shakes(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["fear"] >= THRESHOLD:
        sig = ("shake", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["shiver"] += 1
            out.append("__shake__")
    return out


def _r_light_reveals(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["lit"] >= THRESHOLD:
        sig = ("reveal", clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            clue.meters["seen"] += 1
            out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule(name="noise_spooks", tag="emotional", apply=_r_noise_spooks),
    Rule(name="fear_shakes", tag="physical", apply=_r_fear_shakes),
    Rule(name="light_reveals", tag="physical", apply=_r_light_reveals),
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


def place_fits(place: Place, cause: Cause) -> bool:
    return cause.id in place.allows


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for pid, place in PLACES.items():
        for cid, cause in CAUSES.items():
            if place_fits(place, cause):
                combos.append((pid, cid))
    return combos


def courage_after_help(trait: str, helper: HelperStyle) -> int:
    base = {"timid": 2, "careful": 3, "curious": 4, "steady": 4, "brave": 5}.get(trait, 3)
    return base + helper.brave_bonus


def can_investigate(trait: str, helper: HelperStyle) -> bool:
    return courage_after_help(trait, helper) >= BRAVE_ENOUGH


def predict_reveal(world: World, tool_id: str) -> bool:
    sim = world.copy()
    light = sim.get(tool_id)
    clue = sim.get("clue")
    light.meters["on"] += 1
    clue.meters["lit"] += 1
    propagate(sim, narrate=False)
    return clue.meters["seen"] >= THRESHOLD


def opening(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"For a whole week, {child.id} had been sleeping in {helper.label_word}'s old house, "
        f"and every evening {place.phrase} looked a little more shadowy."
    )
    world.say(
        f"The boards near {place.dark_feature} gave soft little sighs, and {place.echo} held the dark like a secret."
    )


def first_noise(world: World, child: Entity, cause: Cause) -> None:
    house = world.get("house")
    house.meters["noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That night, the sound came again: \"{cause.noise}\""
    )
    world.say(
        f"{child.id} sat up so fast that {child.pronoun('possessive')} blankets bunched around {child.pronoun('object')}."
    )


def ghost_guess(world: World, child: Entity, place: Place) -> None:
    if child.meters["shiver"] >= THRESHOLD:
        world.say(
            f"\"Is there a ghost in {place.room}?\" {child.id} whispered. "
            f"{child.pronoun().capitalize()} tried to stand, then had to stagger one step because {child.pronoun('possessive')} knees felt wobbly."
        )
    else:
        world.say(
            f"\"Is there a ghost in {place.room}?\" {child.id} whispered."
        )


def helper_arrives(world: World, child: Entity, helper: Entity, style: HelperStyle) -> None:
    helper.memes["care"] += 1
    child.memes["trust"] += 1
    world.say(
        f'\"{style.calm_line}\" said {helper.label_word.capitalize()}, coming to the doorway in slippers.'
    )
    world.say(
        f"{helper.pronoun().capitalize()} sat beside {child.id} and listened instead of laughing."
    )


def second_noise(world: World, cause: Cause, place: Place) -> None:
    house = world.get("house")
    house.meters["noise"] += 1
    world.facts["heard_twice"] = True
    propagate(world, narrate=False)
    world.say(
        f"Then it happened again from {place.room}: \"{cause.noise}\""
    )


def choose_to_check(world: World, child: Entity, helper: Entity, tool: LightTool, style: HelperStyle) -> None:
    child.memes["courage"] = float(courage_after_help(world.facts["trait"], style))
    if can_investigate(world.facts["trait"], style):
        world.say(
            f'\"If it is a ghost, we will still look carefully,\" {helper.label_word.capitalize()} said. '
            f'\"And if it is not, we will know the truth.\"'
        )
        world.say(
            f"{helper.pronoun().capitalize()} handed {child.id} {tool.phrase}, and the cool handle made {child.pronoun('object')} feel steadier."
        )
    else:
        world.say(
            f'\"You do not have to be brave all at once,\" {helper.label_word.capitalize()} said. '
            f'\"I will go first, and you may hold onto my sleeve.\"'
        )
        world.say(
            f"{helper.pronoun().capitalize()} clicked on {tool.phrase}, and {child.id} tucked close beside {helper.pronoun('object')}."
        )


def investigate(world: World, child: Entity, helper: Entity, tool: Entity, clue: Entity, place: Place, cause: Cause, style: HelperStyle) -> None:
    tool.meters["on"] += 1
    clue.meters["lit"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Step by step they went toward {place.room}. Floorboards went creak, creak under their feet."
    )
    if child.memes["fear"] >= 2:
        world.say(
            f"{child.id} squeezed {helper.label_word}'s hand, but kept going."
        )
    world.say(
        f"The beam {LIGHTS[world.facts['light']].beam} across the dark."
    )
    if clue.meters["seen"] >= THRESHOLD:
        world.say(
            f"At once the secret showed itself: {cause.effect}."
        )
        world.say(
            f'\"Oh!\" said {child.id}. \"That is not a ghost at all.\"'
        )
        world.say(
            f'\"Exactly,\" said {helper.label_word.capitalize()}. \"{style.fix_line}\"'
        )


def fix(world: World, child: Entity, helper: Entity, cause: Cause) -> None:
    house = world.get("house")
    clue = world.get("clue")
    clue.meters["secured"] += 1
    house.meters["noise"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{helper.label_word.capitalize()} {cause.material}, and the next time the night wind brushed the house, there was only a sleepy hush."
    )
    world.say(
        f"{child.id} let out a long breath {child.pronoun()} had been keeping inside."
    )


def restful_end(world: World, child: Entity, helper: Entity, tool: LightTool, place: Place) -> None:
    world.say(
        f'\"Can we leave {tool.phrase} by my bed anyway?\" asked {child.id}.'
    )
    world.say(
        f'\"Of course,\" said {helper.label_word.capitalize()}. \"But now you know what lives in {place.room}: no ghost, only an ordinary night with a noisy corner.\"'
    )
    world.say(
        f"After that, {child.id} still listened to the house each evening of the week, but now the shadows felt smaller, and sleep came before any ghost-story worry could grow."
    )


def timid_end(world: World, child: Entity, helper: Entity, tool: LightTool, place: Place) -> None:
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    child.memes["relief"] += 1
    world.say(
        f"They did not march all the way to {place.room} that night. Instead, {helper.label_word} opened the door wide, lifted {tool.phrase}, and showed enough of the truth for the room to stop feeling haunted."
    )
    world.say(
        f"{child.id} was still a little shaky, but no longer thought a ghost was waiting there."
    )
    world.say(
        f"For the rest of the week, {child.id} could pass the doorway without a stagger, because {child.pronoun()} knew the house was only making plain old house sounds."
    )


def tell(
    place: Place,
    cause: Cause,
    light: LightTool,
    helper_style: HelperStyle,
    child_name: str = "Mina",
    child_gender: str = "girl",
    helper_name: str = "Grandma",
    trait: str = "curious",
) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_style.type, role="helper", label="the helper"))
    house = world.add(Entity(id="house", kind="thing", type="house", label="house"))
    light_ent = world.add(Entity(id="light", kind="thing", type="tool", label=light.id))
    clue = world.add(Entity(id="clue", kind="thing", type="cause", label=cause.label))

    world.facts.update(
        place=place,
        cause=cause,
        light=light.id,
        helper_style=helper_style,
        trait=trait,
        child=child,
        helper=helper,
        house=house,
        clue=clue,
        outcome="resolved" if can_investigate(trait, helper_style) else "peeked",
        heard_twice=False,
    )

    opening(world, child, helper, place)
    world.para()
    first_noise(world, child, cause)
    ghost_guess(world, child, place)
    helper_arrives(world, child, helper, helper_style)
    second_noise(world, cause, place)
    world.para()
    choose_to_check(world, child, helper, light, helper_style)
    if can_investigate(trait, helper_style):
        investigate(world, child, helper, light_ent, clue, place, cause, helper_style)
        fix(world, child, helper, cause)
        world.para()
        restful_end(world, child, helper, light, place)
    else:
        light_ent.meters["on"] += 1
        clue.meters["lit"] += 1
        propagate(world, narrate=False)
        world.para()
        timid_end(world, child, helper, light, place)

    return world


PLACES = {
    "attic": Place(
        id="attic",
        room="the attic",
        phrase="the narrow stair to the attic",
        dark_feature="the attic door",
        echo="the sloping ceiling",
        allows={"shutters", "trunk_chain"},
        tags={"attic", "old_house"},
    ),
    "hallway": Place(
        id="hallway",
        room="the hallway",
        phrase="the long upstairs hallway",
        dark_feature="the bent coat stand",
        echo="the wallpapered walls",
        allows={"portrait_cord", "shutters"},
        tags={"hallway", "old_house"},
    ),
    "chimney": Place(
        id="chimney",
        room="the chimney corner",
        phrase="the brick chimney corner by the landing",
        dark_feature="the black iron grate",
        echo="the tall narrow bricks",
        allows={"mice", "portrait_cord"},
        tags={"chimney", "old_house"},
    ),
}

CAUSES = {
    "shutters": Cause(
        id="shutters",
        label="loose shutters",
        noise="BANG... tap-tap... BANG",
        effect="a pair of loose shutters knocking and trembling in the wind",
        material="tied the shutters back with a strip of cloth",
        needs_wind=True,
        moving_thing="shutters",
        tags={"wind", "shutters", "noise"},
    ),
    "portrait_cord": Cause(
        id="portrait_cord",
        label="a portrait cord",
        noise="scrrritch... thump",
        effect="an old portrait frame swinging on a frayed cord and bumping the wall",
        material="lifted the frame down and set it safely on a table",
        moving_thing="portrait",
        tags={"portrait", "swinging", "noise"},
    ),
    "trunk_chain": Cause(
        id="trunk_chain",
        label="a trunk chain",
        noise="clink-clink... claaank",
        effect="a brass chain on an old travel trunk sliding against its lock whenever the rafters shivered",
        material="wrapped the chain around the handle so it could not clink anymore",
        moving_thing="chain",
        tags={"trunk", "metal", "noise"},
    ),
    "mice": Cause(
        id="mice",
        label="mice",
        noise="skitter-skitter... squeak",
        effect="two tiny mice darting behind the grate with a walnut shell",
        material="propped the grate snugly and promised to ask for a mouse-safe trap in the morning",
        needs_small_gap=True,
        moving_thing="mice",
        tags={"mice", "animals", "noise"},
    ),
}

LIGHTS = {
    "flashlight": LightTool(
        id="flashlight",
        phrase="a flashlight",
        beam="cut a white path",
        tags={"flashlight", "light"},
    ),
    "lantern": LightTool(
        id="lantern",
        phrase="a little battery lantern",
        beam="spread a round golden glow",
        tags={"lantern", "light"},
    ),
    "nightlight": LightTool(
        id="nightlight",
        phrase="a star-shaped night-light",
        beam="made a soft blue puddle",
        tags={"nightlight", "light"},
    ),
}

HELPERS = {
    "grandma": HelperStyle(
        id="grandma",
        title="Grandma",
        calm_line="Old houses talk, dear, but talking is not haunting",
        fix_line="When something rattles, we look for what is loose",
        brave_bonus=2,
        type="grandmother",
        tags={"grandma", "adult_help"},
    ),
    "grandpa": HelperStyle(
        id="grandpa",
        title="Grandpa",
        calm_line="Let us hear the sound one more time before we name it",
        fix_line="A noise is a clue if you listen with calm ears",
        brave_bonus=2,
        type="grandfather",
        tags={"grandpa", "adult_help"},
    ),
    "aunt": HelperStyle(
        id="aunt",
        title="Aunt",
        calm_line="Spooky does not always mean dangerous",
        fix_line="We will follow the sound and see what the dark is hiding",
        brave_bonus=1,
        type="aunt",
        tags={"aunt", "adult_help"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Lila", "Etta", "Ruby", "Ivy", "Tess", "Wren"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Jude", "Eli", "Noah", "Bram"]
TRAITS = ["timid", "careful", "curious", "steady", "brave"]


KNOWLEDGE = {
    "flashlight": [
        (
            "What does a flashlight do?",
            "A flashlight makes a beam of light so you can see into dark places. It helps people check what is really there."
        )
    ],
    "lantern": [
        (
            "What is a battery lantern?",
            "A battery lantern is a safe light that glows without any flame. It can brighten a room all around you."
        )
    ],
    "nightlight": [
        (
            "What is a night-light for?",
            "A night-light gives a small gentle glow in the dark. It can help a room feel less scary at bedtime."
        )
    ],
    "wind": [
        (
            "Why can wind make spooky sounds in a house?",
            "Wind can push shutters, doors, and loose things so they knock or rattle. That can sound mysterious even when nothing magical is happening."
        )
    ],
    "mice": [
        (
            "Why do mice make little scratching sounds?",
            "Mice have tiny feet and small claws, so they skitter and scratch when they run. In a quiet house, those sounds can seem much bigger than they are."
        )
    ],
    "portrait": [
        (
            "Why would a picture frame thump against a wall?",
            "If a frame hangs loose, it can swing and bump when the air moves. The wall makes the sound echo louder."
        )
    ],
    "old_house": [
        (
            "Why do old houses creak?",
            "Old wood and old pipes move a little when wind or weather changes. That is why an old house can sound busy at night."
        )
    ],
    "adult_help": [
        (
            "What should a child do when a strange sound feels scary?",
            "Tell a trusted grown-up and listen together. A calm helper can check the sound safely and explain what caused it."
        )
    ],
}
KNOWLEDGE_ORDER = ["old_house", "wind", "mice", "portrait", "flashlight", "lantern", "nightlight", "adult_help"]


@dataclass
class StoryParams:
    place: str
    cause: str
    light: str
    helper: str
    child_name: str
    child_gender: str
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


def explain_rejection(place: Place, cause: Cause) -> str:
    return (
        f"(No story: {cause.label} is not a plausible source for {place.room}. "
        f"Pick a cause that fits that part of the house.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    cause = f["cause"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "stagger" and "week", and uses sound effects and dialogue.',
        f"Tell a spooky-but-safe story where {child.id} hears a strange noise in {place.room}, worries about a ghost, and discovers it is really {cause.label}.",
        f'Write a night-time story in an old house with creaks, whispers, and quoted dialogue, ending with a child learning that scary sounds can have ordinary causes.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    place: Place = f["place"]
    cause: Cause = f["cause"]
    light = LIGHTS[f["light"]]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who heard a scary sound in {place.room}, and {helper.label_word}, who came to help. Together they listened instead of running away from the mystery."
        ),
        (
            "Why did the sound seem like a ghost at first?",
            f"The house was dark, old, and full of echoes, so the noise sounded bigger and stranger than it really was. {child.id} could not see the cause yet, which let fear fill in the rest."
        ),
        (
            f"What sound did {child.id} hear?",
            f'{child.id} heard "{cause.noise}" coming from {place.room}. The strange rhythm made it seem spooky before anyone checked it closely.'
        ),
    ]
    if outcome == "resolved":
        qa.append(
            (
                f"How did {child.id} find out the truth?",
                f"{helper.label_word.capitalize()} and {child.id} went to look with {light.phrase}. The light showed that the sound came from {cause.effect}, so the mystery stopped being a ghost story and became a house problem."
            )
        )
        qa.append(
            (
                "What changed at the end?",
                f"The noise was fixed, and {child.id} was no longer frightened of {place.room}. For the rest of the week, {child.pronoun()} could listen to the house without believing a ghost was there."
            )
        )
    else:
        qa.append(
            (
                f"Did {child.id} have to be brave all at once?",
                f"No. {helper.label_word.capitalize()} let {child.id} stay close and only showed enough of the truth to calm the fear. That made the room feel ordinary again, even before a full investigation."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended more calmly than it began. {child.id} still felt a little shaky, but by the end of the week {child.pronoun()} could pass the doorway without thinking a ghost was waiting there."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["cause"].tags) | set(HELPERS[f["helper_style"].id].tags) | set(LIGHTS[f["light"]].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(P, C) :- allows(P, C).

base_courage(2) :- chosen_trait(timid).
base_courage(3) :- chosen_trait(careful).
base_courage(4) :- chosen_trait(curious).
base_courage(4) :- chosen_trait(steady).
base_courage(5) :- chosen_trait(brave).

courage(B + Bonus) :- base_courage(B), helper_bonus(H, Bonus), chosen_helper(H).
can_investigate :- courage(C), brave_enough(T), C >= T.

outcome(resolved) :- can_investigate.
outcome(peeked) :- not can_investigate.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for cid in sorted(place.allows):
            lines.append(asp.fact("allows", pid, cid))
    for cid in CAUSES:
        lines.append(asp.fact("cause", cid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_bonus", hid, helper.brave_bonus))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
    lines.append(asp.fact("brave_enough", BRAVE_ENOUGH))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show fits/2."))
    return sorted(set(asp.atoms(model, "fits")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_trait", params.trait),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_cause", params.cause),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "resolved" if can_investigate(params.trait, HELPERS[params.helper]) else "peeked"


CURATED = [
    StoryParams(
        place="attic",
        cause="shutters",
        light="lantern",
        helper="grandma",
        child_name="Mina",
        child_gender="girl",
        trait="curious",
    ),
    StoryParams(
        place="hallway",
        cause="portrait_cord",
        light="flashlight",
        helper="grandpa",
        child_name="Owen",
        child_gender="boy",
        trait="careful",
    ),
    StoryParams(
        place="chimney",
        cause="mice",
        light="nightlight",
        helper="aunt",
        child_name="Ruby",
        child_gender="girl",
        trait="timid",
    ),
    StoryParams(
        place="attic",
        cause="trunk_chain",
        light="flashlight",
        helper="grandma",
        child_name="Finn",
        child_gender="boy",
        trait="steady",
    ),
    StoryParams(
        place="hallway",
        cause="shutters",
        light="lantern",
        helper="aunt",
        child_name="Lila",
        child_gender="girl",
        trait="brave",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child hears a ghostly sound, checks it safely, and learns what made it."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (place, cause) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause:
        if not place_fits(PLACES[args.place], CAUSES[args.cause]):
            raise StoryError(explain_rejection(PLACES[args.place], CAUSES[args.cause]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cause is None or combo[1] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, cause = rng.choice(sorted(combos))
    light = args.light or rng.choice(sorted(LIGHTS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)

    return StoryParams(
        place=place,
        cause=cause,
        light=light,
        helper=helper,
        child_name=child_name,
        child_gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light: {params.light})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.child_gender})")

    place = PLACES[params.place]
    cause = CAUSES[params.cause]
    if not place_fits(place, cause):
        raise StoryError(explain_rejection(place, cause))

    world = tell(
        place=place,
        cause=cause,
        light=LIGHTS[params.light],
        helper_style=HELPERS[params.helper],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=HELPERS[params.helper].title,
        trait=params.trait,
    )
    world.facts["helper_style"] = HELPERS[params.helper]
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
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show fits/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cause) pairs:\n")
        for place, cause in combos:
            print(f"  {place:8} {cause}")
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
            header = f"### {p.child_name}: {p.cause} in {p.place} ({p.helper}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
