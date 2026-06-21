#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sushi_gang_suspense_ghost_story.py
=============================================================

A standalone storyworld for a small ghost-story-like domain: a child from the
"Sushi Gang" hears something spooky in a dim sushi place after closing time,
thinks a ghost may be hiding there, and learns that scary signs can come from
ordinary causes when a calm helper and the right light are used.

This world is intentionally small and constraint-driven:

- A place only supports certain mundane causes.
- A "ghost sign" must be something that cause can actually produce.
- Weak or unsafe investigation tools are known to the world but refused.
- The outcome is determined by simulated suspense versus the clarity/support of
  the investigation.

Run it
------
    python storyworlds/worlds/gpt-5.4/sushi_gang_suspense_ghost_story.py
    python storyworlds/worlds/gpt-5.4/sushi_gang_suspense_ghost_story.py --place sushi_shop --sign shadow
    python storyworlds/worlds/gpt-5.4/sushi_gang_suspense_ghost_story.py --tool candle
    python storyworlds/worlds/gpt-5.4/sushi_gang_suspense_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/sushi_gang_suspense_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/sushi_gang_suspense_ghost_story.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "aunt", "sister", "woman"}
        male = {"boy", "father", "uncle", "brother", "man", "grandfather"}
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
            "sister": "sister",
            "brother": "brother",
            "grandfather": "grandpa",
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
    label: str
    opening: str
    lost_spot: str
    dark_text: str
    ending_image: str
    darkness: int
    causes: set[str] = field(default_factory=set)
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
class Sign:
    id: str
    label: str
    line: str
    intensity: int
    image: str
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
    signs: set[str] = field(default_factory=set)
    explain: str = ""
    reveal: str = ""
    fix: str = ""
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
    clarity: int
    sense: int
    beam: str
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
    kind: str
    label: str
    support: int
    opening: str
    comfort: str
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


def _r_eerie(world: World) -> list[str]:
    room = world.get("room")
    cause = world.get("cause")
    hero = world.get("hero")
    sig = ("eerie", cause.id)
    if sig in world.fired:
        return []
    if room.meters["dark"] >= THRESHOLD and cause.meters["active"] >= THRESHOLD:
        world.fired.add(sig)
        room.meters["eerie"] += float(cause.attrs["intensity"])
        hero.memes["fear"] += 1.0
        return []
    return []


def _r_helper_steadies(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    sig = ("steady", helper.id)
    if sig in world.fired:
        return []
    if hero.memes["fear"] >= THRESHOLD and helper.memes["near"] >= THRESHOLD:
        world.fired.add(sig)
        hero.memes["courage"] += 1.0
        hero.memes["trust"] += 1.0
        return []
    return []


def _r_reveal_clears(world: World) -> list[str]:
    room = world.get("room")
    cause = world.get("cause")
    hero = world.get("hero")
    helper = world.get("helper")
    sig = ("reveal", cause.id)
    if sig in world.fired:
        return []
    if room.meters["lit"] >= THRESHOLD and cause.meters["seen"] >= THRESHOLD:
        world.fired.add(sig)
        room.meters["mystery"] = 0.0
        hero.memes["fear"] = 0.0
        hero.memes["relief"] += 1.0
        hero.memes["wonder"] += 1.0
        helper.memes["calm"] += 1.0
        return []
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="eerie", tag="mood", apply=_r_eerie),
    Rule(name="steady", tag="social", apply=_r_helper_steadies),
    Rule(name="reveal", tag="resolution", apply=_r_reveal_clears),
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
                produced.extend(sents)
            elif any((rule.name, x) in world.fired for x in []):
                pass
        fired_count = len(world.fired)
        for rule in CAUSAL_RULES:
            _ = rule
        if len(world.fired) != fired_count:
            changed = True
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "sushi_shop": Place(
        id="sushi_shop",
        label="the little sushi shop",
        opening="The last paper lantern outside the little sushi shop was still glowing red.",
        lost_spot="the back hall near the stacked trays",
        dark_text="The back hall was dim, and every shiny thing looked longer and stranger than it did in daylight.",
        ending_image="By the door, the lantern glowed softly again, and the Sushi Gang walked home smiling instead of shivering.",
        darkness=2,
        causes={"bamboo_blind", "ice_box", "cat_crate"},
        tags={"sushi_shop", "night"},
    ),
    "festival_stall": Place(
        id="festival_stall",
        label="the summer sushi stall",
        opening="At the summer festival, the sushi stall had gone quiet, and the string lights were being switched off one by one.",
        lost_spot="the cloth-covered shelf behind the stall",
        dark_text="Under the drooping stall cloth, the corners were patchy with shadow and full of rustly little sounds.",
        ending_image="Soon the festival lane felt cheerful again, and the Sushi Gang could see every noodle banner and every star.",
        darkness=1,
        causes={"bamboo_blind", "cat_crate"},
        tags={"festival", "night"},
    ),
    "home_kitchen": Place(
        id="home_kitchen",
        label="the family kitchen after sushi night",
        opening="After sushi night at home, the kitchen still smelled like warm rice and seaweed.",
        lost_spot="the pantry doorway beside the rice bag",
        dark_text="The pantry corner was dark enough to make one hanging towel look like a tall white shape.",
        ending_image="The kitchen felt friendly again, with the rice pot cooling on the counter and the Sushi Gang laughing at the silly scare.",
        darkness=1,
        causes={"ice_box", "towel_fan", "cat_crate"},
        tags={"home", "night"},
    ),
}

SIGNS = {
    "shadow": Sign(
        id="shadow",
        label="a sliding shadow",
        line="a long pale shape slipped across the dark doorway",
        intensity=2,
        image="It moved so smoothly that it did not look like a person at all.",
        tags={"shadow"},
    ),
    "whisper": Sign(
        id="whisper",
        label="a whispering sound",
        line='a soft "shhh... shhh..." came from the dark',
        intensity=2,
        image="The sound was so thin and close that it seemed to be speaking right into small ears.",
        tags={"wind"},
    ),
    "clatter": Sign(
        id="clatter",
        label="a tray-clatter",
        line="something gave a quick clink-clink among the trays",
        intensity=1,
        image="In the quiet, the little sound jumped like a dropped spoon.",
        tags={"noise"},
    ),
    "blue_glow": Sign(
        id="blue_glow",
        label="a blue glow",
        line="a cold blue light blinked from the dark room",
        intensity=2,
        image="For a moment it looked like one sleepy ghost eye opening and closing.",
        tags={"light"},
    ),
}

CAUSES = {
    "bamboo_blind": Cause(
        id="bamboo_blind",
        label="the loose bamboo blind by the back door",
        signs={"shadow", "whisper"},
        explain="the night breeze was slipping through the back door and moving the loose bamboo blind",
        reveal="The pale shape was only the bamboo blind swaying, and the whisper was its thin strips brushing together in the draft.",
        fix="They tied the blind neatly to one side so it could not sway and whisper anymore.",
        tags={"wind", "bamboo"},
    ),
    "ice_box": Cause(
        id="ice_box",
        label="the blinking ice box",
        signs={"blue_glow", "clatter"},
        explain="the old ice box was blinking while a loose metal scoop tapped against its side",
        reveal="The blue ghost-eye was only the tiny light on the ice box, and the clatter came from a scoop gently tapping the metal.",
        fix="The helper tucked the scoop onto a towel, and the little tapping sound stopped.",
        tags={"ice_box", "cold"},
    ),
    "cat_crate": Cause(
        id="cat_crate",
        label="the delivery cat behind the crate",
        signs={"shadow", "clatter"},
        explain="a neighbor's gray cat had slipped behind a crate and was nosing at the stacked trays",
        reveal="The moving shadow was only a gray cat with bright whiskers, and the clatter was its paw brushing the trays.",
        fix="They opened the side gate a little, and the cat trotted back out into the night.",
        tags={"cat", "animal"},
    ),
    "towel_fan": Cause(
        id="towel_fan",
        label="the kitchen towel near the fan",
        signs={"shadow", "whisper"},
        explain="a white kitchen towel was fluttering near the small fan",
        reveal="The tall white ghost was only a towel stirring in the fan, and the whisper was the cloth rubbing against the shelf.",
        fix="The helper folded the towel and switched the fan off.",
        tags={"fan", "cloth"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a bright flashlight",
        clarity=2,
        sense=3,
        beam="The flashlight made one clean path of light through the dark.",
        tags={"flashlight", "light"},
    ),
    "phone_light": Tool(
        id="phone_light",
        label="phone light",
        phrase="a phone light",
        clarity=1,
        sense=2,
        beam="The phone light made a small white circle that trembled a little but still helped.",
        tags={"phone_light", "light"},
    ),
    "paper_lantern": Tool(
        id="paper_lantern",
        label="paper lantern",
        phrase="a paper lantern with a safe battery candle inside",
        clarity=1,
        sense=2,
        beam="The paper lantern glowed warm and round, enough to soften the shadows.",
        tags={"lantern", "light"},
    ),
    "candle": Tool(
        id="candle",
        label="candle",
        phrase="a real candle",
        clarity=1,
        sense=1,
        beam="The candle made a shaky little flame.",
        tags={"candle", "fire"},
    ),
}

HELPERS = {
    "mom": HelperCfg(
        id="mom",
        kind="mother",
        label="mom",
        support=2,
        opening="Mom was wiping the counter and stacking soy-sauce dishes.",
        comfort="Mom bent down beside the child and spoke in the kind of quiet voice that makes a room feel smaller and safer.",
        tags={"mom"},
    ),
    "grandpa": HelperCfg(
        id="grandpa",
        kind="grandfather",
        label="grandpa",
        support=2,
        opening="Grandpa was rolling down the front shade and humming to himself.",
        comfort="Grandpa did not laugh at the fear. He only put one warm hand on the child's shoulder and listened first.",
        tags={"grandpa"},
    ),
    "big_sister": HelperCfg(
        id="big_sister",
        kind="sister",
        label="big sister",
        support=1,
        opening="Big Sister was tying up the napkin basket after helping all evening.",
        comfort="Big Sister swallowed once, then stood close enough that the child could feel they were being brave together.",
        tags={"sister"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Yumi", "Ava", "Zoe", "Maya", "Luna"]
BOY_NAMES = ["Ken", "Leo", "Noah", "Eli", "Taro", "Max", "Finn", "Kai"]
TRAITS = ["curious", "careful", "imaginative", "quiet", "brave", "thoughtful"]


def sign_possible(place: Place, sign: Sign, cause: Cause) -> bool:
    return cause.id in place.causes and sign.id in cause.signs


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def suspense_level(place: Place, sign: Sign) -> int:
    return place.darkness + sign.intensity


def can_solve(tool: Tool, helper: HelperCfg, place: Place, sign: Sign) -> bool:
    return tool.clarity + helper.support >= suspense_level(place, sign)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for sign_id, sign in SIGNS.items():
            for cause_id, cause in CAUSES.items():
                if sign_possible(place, sign, cause):
                    out.append((place_id, sign_id, cause_id))
    return out


@dataclass
class StoryParams:
    place: str
    sign: str
    cause: str
    tool: str
    helper: str
    hero_name: str
    hero_gender: str
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


def introduce(world: World, place: Place, hero: Entity, helper: Entity) -> None:
    world.say(place.opening)
    world.say(
        f"{hero.id} called the little club of after-dinner helpers the Sushi Gang, "
        f"because even rolling napkins felt grander with a name like that."
    )
    world.say(helper.attrs["opening"])


def lose_item(world: World, place: Place, hero: Entity) -> None:
    hero.memes["attachment"] += 1.0
    world.say(
        f"When the work was nearly done, {hero.id} gave a tiny gasp. "
        f'The Sushi Gang stamp book was missing, and {hero.pronoun("subject")} remembered leaving it in {place.lost_spot}.'
    )
    world.say(place.dark_text)


def awaken_sign(world: World, sign: Sign) -> None:
    room = world.get("room")
    cause = world.get("cause")
    room.meters["dark"] = 1.0
    cause.meters["active"] = 1.0
    room.meters["mystery"] = 1.0
    propagate(world, narrate=False)
    hero = world.get("hero")
    world.say(
        f"Just then, {sign.line}. {sign.image}"
    )
    world.say(
        f'{hero.id} stopped so fast that {hero.pronoun("possessive")} slippers squeaked. '
        f'"Did the sushi place get a ghost?" {hero.pronoun("subject")} whispered.'
    )


def comfort(world: World, helper: Entity) -> None:
    world.say(helper.attrs["comfort"])


def warn(world: World, tool: Tool) -> None:
    helper = world.get("helper")
    hero = world.get("hero")
    world.say(
        f'"We will not poke around in the dark with bare hands," {helper.label_word} said. '
        f'"If something is there, we will look the safe way."'
    )
    world.say(
        f'{helper.label_word.capitalize()} reached for {tool.phrase}.'
    )
    hero.memes["hope"] += 1.0


def creep_closer(world: World, tool: Tool) -> None:
    helper = world.get("helper")
    hero = world.get("hero")
    helper.memes["near"] = 1.0
    propagate(world, narrate=False)
    world.say(tool.beam)
    world.say(
        f"Together they took three slow steps toward the dark place. "
        f"{hero.id} held onto {helper.label_word}'s sleeve and listened."
    )


def reveal_cause(world: World, cause_cfg: Cause) -> None:
    room = world.get("room")
    cause = world.get("cause")
    cause.meters["seen"] = 1.0
    room.meters["lit"] = 1.0
    propagate(world, narrate=False)
    hero = world.get("hero")
    helper = world.get("helper")
    world.say(cause_cfg.reveal)
    world.say(
        f'{hero.id} let out a long breath. {helper.label_word.capitalize()} smiled and said, '
        f'"Scary things can look bigger before we see them clearly."'
    )
    world.say(cause_cfg.fix)
    world.facts["solved_with_helper"] = True


def retreat_and_fetch(world: World, cause_cfg: Cause, tool: Tool) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    room = world.get("room")
    world.say(
        f"The little circle of light was not quite enough. The dark still seemed to fold around the shelves, "
        f"so {helper.label_word} backed away instead of guessing."
    )
    world.say(
        f'"No creeping farther," {helper.label_word} said. "When a room still feels wrong, we get more light and more grown-up help."'
    )
    room.meters["lit"] = 1.0
    world.say(
        f"A bright ceiling light snapped on a moment later, and the whole corner shrank back to its ordinary size."
    )
    world.say(cause_cfg.reveal)
    world.say(
        f"{hero.id} blinked, then gave a small embarrassed laugh. "
        f"The ghost had only been {cause_cfg.explain}."
    )
    world.facts["solved_with_helper"] = False
    world.facts["retreated_first"] = True
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1.0
    helper.memes["calm"] += 1.0


def ending(world: World, place: Place) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    world.say(
        f"They found the Sushi Gang stamp book exactly where {hero.id} had left it, and somehow it did not look haunted at all anymore."
    )
    if world.facts.get("retreated_first"):
        world.say(
            f'{hero.id} tucked the book under {hero.pronoun("possessive")} arm and promised, '
            f'"Next time I will ask for help before I let one shadow become a whole ghost story."'
        )
    else:
        world.say(
            f'{hero.id} tucked the book under {hero.pronoun("possessive")} arm and whispered, '
            f'"The Sushi Gang is brave when it stays together."'
        )
    snack = "a tiny cucumber roll left from supper" if place.id == "home_kitchen" else "one last neat plate of sushi waiting to be covered"
    world.say(
        f"Back in the light, {helper.label_word} laughed softly, and {snack} no longer looked spooky at all. "
        f"{place.ending_image}"
    )


def tell(
    place: Place,
    sign: Sign,
    cause_cfg: Cause,
    tool: Tool,
    helper_cfg: HelperCfg,
    hero_name: str = "Mina",
    hero_gender: str = "girl",
    trait: str = "imaginative",
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.kind,
        label=helper_cfg.label,
        role="helper",
        attrs={
            "opening": helper_cfg.opening,
            "comfort": helper_cfg.comfort,
            "support": helper_cfg.support,
        },
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=place.label,
        attrs={"darkness": place.darkness},
    ))
    cause = world.add(Entity(
        id="cause",
        kind="thing",
        type="cause",
        label=cause_cfg.label,
        attrs={"intensity": sign.intensity, "cause_id": cause_cfg.id},
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        attrs={"clarity": tool.clarity, "sense": tool.sense},
    ))

    for ent in (hero, helper, room, cause, tool_ent):
        for key in ["dark", "lit", "eerie", "mystery", "active", "seen"]:
            ent.meters[key] = ent.meters[key]
        for key in ["fear", "courage", "trust", "relief", "wonder", "near", "calm", "hope", "attachment"]:
            ent.memes[key] = ent.memes[key]

    world.facts.update(
        place=place,
        sign=sign,
        cause_cfg=cause_cfg,
        tool_cfg=tool,
        helper_cfg=helper_cfg,
        hero=hero,
        helper=helper,
        room=room,
        cause=cause,
        tool=tool_ent,
        outcome="solved" if can_solve(tool, helper_cfg, place, sign) else "retreat",
        retreated_first=False,
        solved_with_helper=False,
    )

    introduce(world, place, hero, helper)
    lose_item(world, place, hero)

    world.para()
    awaken_sign(world, sign)
    comfort(world, helper)
    warn(world, tool)

    world.para()
    creep_closer(world, tool)
    if can_solve(tool, helper_cfg, place, sign):
        reveal_cause(world, cause_cfg)
    else:
        retreat_and_fetch(world, cause_cfg, tool)

    world.para()
    ending(world, place)
    return world


KNOWLEDGE = {
    "sushi": [
        (
            "What is sushi?",
            "Sushi is a food often made with rice and small toppings or fillings like fish, egg, or cucumber. People eat it in little bites."
        )
    ],
    "flashlight": [
        (
            "Why does a flashlight help in the dark?",
            "A flashlight sends bright light where you point it, so you can see what is really there. Seeing clearly helps small fears shrink."
        )
    ],
    "light": [
        (
            "Why can shadows look scary at night?",
            "At night, your eyes see less detail, so ordinary things can look bigger or stranger than they really are. A little more light often shows the truth."
        )
    ],
    "wind": [
        (
            "How can wind make spooky sounds?",
            "Wind can move blinds, cloth, or doors and make whispery noises. When you do not know the cause yet, the sounds can feel mysterious."
        )
    ],
    "cat": [
        (
            "Why do cats make surprising noises?",
            "Cats can knock light things with their paws and slip through tight spaces very quietly. That can make them seem to appear from nowhere."
        )
    ],
    "ice_box": [
        (
            "Why might a machine blink or hum at night?",
            "Some machines have little lights and soft sounds while they keep working. In a dark room, those tiny signals can feel much bigger."
        )
    ],
    "candle": [
        (
            "Why is a real candle not a good tool for poking around a dark shop?",
            "A real candle has a flame, so it can start a fire if it tips or brushes something. A flashlight is a much safer way to look around."
        )
    ],
    "mom": [
        (
            "What can a calm grown-up do in a scary moment?",
            "A calm grown-up can slow everyone down, choose a safe plan, and help children see what is really happening. That makes the fear easier to carry."
        )
    ],
    "sister": [
        (
            "How can an older sister help when something feels spooky?",
            "An older sister can stay close, share courage, and help ask for more light or more help. Being together often feels safer than facing a scary corner alone."
        )
    ],
    "grandpa": [
        (
            "How can a grandpa help with a mystery?",
            "A grandpa can listen carefully and stay unhurried. Sometimes calm listening is the first step to solving a mystery."
        )
    ],
}
KNOWLEDGE_ORDER = ["sushi", "light", "wind", "cat", "ice_box", "flashlight", "candle", "mom", "sister", "grandpa"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    sign = f["sign"]
    helper = f["helper"]
    tool = f["tool_cfg"]
    cause = f["cause_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short ghost-story-style story for a 3-to-5-year-old that includes the words "sushi" and "gang". '
        f'The story should take place in {place.label} and begin with {sign.label}.'
    )
    if outcome == "solved":
        return [
            base,
            f"Tell a suspenseful but gentle story where a child from the Sushi Gang hears {sign.label}, "
            f"then uses {tool.phrase} with {helper.label_word} to discover it was really {cause.label}.",
            f"Write a child-facing ghost story where the scary sign turns out to have an ordinary cause, "
            f"and the ending image proves the place feels safe again.",
        ]
    return [
        base,
        f"Tell a suspenseful story where the first light is not strong enough, so the child and {helper.label_word} step back, "
        f"get brighter light, and then learn the 'ghost' was really {cause.label}.",
        f"Write a gentle ghost story that teaches children not to creep deeper into the dark when they are unsure, "
        f"but to ask for more light and help instead.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    sign = f["sign"]
    cause = f["cause_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child in the Sushi Gang, and {helper.label_word}, who stayed close during the scare. "
            f"They were together in {place.label} after the day was almost over."
        ),
        (
            "Why did the child think there might be a ghost?",
            f"{sign.line.capitalize()}, and in the dark it felt eerie and hard to explain. "
            f"Because the Sushi Gang stamp book was lost in that same corner, the child had to keep looking at the scary place."
        ),
        (
            "What was the ghost really?",
            f"It was not a ghost at all. {cause.reveal}"
        ),
    ]
    if outcome == "solved":
        qa.append(
            (
                f"How did {helper.label_word} help solve the mystery?",
                f"{helper.label_word.capitalize()} slowed everything down and used {tool.phrase} instead of guessing. "
                f"That safe light made the ordinary cause visible, so the fear could melt into relief."
            )
        )
    else:
        qa.append(
            (
                "Why did they step back before solving the mystery?",
                f"The first light was not enough to make the dark corner feel clear, so they did not creep farther. "
                f"Stepping back for brighter light kept them safe and helped them learn the truth without panic."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"They found the Sushi Gang stamp book and the place felt ordinary again. "
            f"The ending proves what changed because the same corner that seemed haunted now looked small, bright, and harmless."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sushi"}
    tags |= set(f["sign"].tags)
    tags |= set(f["cause_cfg"].tags)
    tags |= set(f["tool_cfg"].tags)
    tags |= set(f["helper_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(name for name, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="sushi_shop",
        sign="shadow",
        cause="cat_crate",
        tool="flashlight",
        helper="mom",
        hero_name="Mina",
        hero_gender="girl",
        trait="imaginative",
    ),
    StoryParams(
        place="festival_stall",
        sign="whisper",
        cause="bamboo_blind",
        tool="paper_lantern",
        helper="grandpa",
        hero_name="Leo",
        hero_gender="boy",
        trait="curious",
    ),
    StoryParams(
        place="home_kitchen",
        sign="shadow",
        cause="towel_fan",
        tool="phone_light",
        helper="big_sister",
        hero_name="Yumi",
        hero_gender="girl",
        trait="careful",
    ),
    StoryParams(
        place="sushi_shop",
        sign="blue_glow",
        cause="ice_box",
        tool="phone_light",
        helper="big_sister",
        hero_name="Kai",
        hero_gender="boy",
        trait="quiet",
    ),
    StoryParams(
        place="festival_stall",
        sign="clatter",
        cause="cat_crate",
        tool="flashlight",
        helper="grandpa",
        hero_name="Nora",
        hero_gender="girl",
        trait="thoughtful",
    ),
]


def explain_rejection(place: Place, sign: Sign, cause: Cause) -> str:
    if cause.id not in place.causes:
        return (
            f"(No story: {cause.label} does not belong in {place.label}, so it cannot honestly explain the spooky sign there.)"
        )
    return (
        f"(No story: {cause.label} would not produce {sign.label}. Pick a sign that this cause can actually make.)"
    )


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it scores too low on common sense "
        f"(sense={tool.sense} < {SENSE_MIN}). Use a safer light like {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.place not in PLACES or params.sign not in SIGNS or params.tool not in TOOLS or params.helper not in HELPERS:
        return "?"
    return "solved" if can_solve(TOOLS[params.tool], HELPERS[params.helper], PLACES[params.place], SIGNS[params.sign]) else "retreat"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(P,S,C) :- place(P), sign(S), cause(C), affords(P,C), produces(C,S).
sensible_tool(T) :- tool(T), sense(T,V), sense_min(M), V >= M.

% --- suspense and outcome --------------------------------------------------
suspense(V) :- chosen_place(P), chosen_sign(S), darkness(P,D), intensity(S,I), V = D + I.
strength(V) :- chosen_tool(T), chosen_helper(H), clarity(T,C), support(H,S), V = C + S.

outcome(solved)  :- strength(A), suspense(B), A >= B.
outcome(retreat) :- strength(A), suspense(B), A < B.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("darkness", pid, place.darkness))
        for cause_id in sorted(place.causes):
            lines.append(asp.fact("affords", pid, cause_id))
    for sid, sign in SIGNS.items():
        lines.append(asp.fact("sign", sid))
        lines.append(asp.fact("intensity", sid, sign.intensity))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for sid in sorted(cause.signs):
            lines.append(asp.fact("produces", cid, sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("clarity", tid, tool.clarity))
        lines.append(asp.fact("sense", tid, tool.sense))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("support", hid, helper.support))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_sign", params.sign),
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    buf = io.StringIO()
    with redirect_stdout(buf):
        emit(sample, trace=False, qa=False, header="")
    if not buf.getvalue().strip():
        raise StoryError("Smoke test failed: emit() produced no output.")


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_tools = set(asp_sensible_tools())
    python_tools = {tool.id for tool in sensible_tools()}
    if clingo_tools == python_tools:
        print(f"OK: sensible tools match ({sorted(clingo_tools)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: clingo={sorted(clingo_tools)} python={sorted(python_tools)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test generate()/emit() passed.")
    except Exception as exc:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a Sushi Gang ghost-story suspense mystery. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.sign and args.cause:
        place = PLACES[args.place]
        sign = SIGNS[args.sign]
        cause = CAUSES[args.cause]
        if not sign_possible(place, sign, cause):
            raise StoryError(explain_rejection(place, sign, cause))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.sign is None or combo[1] == args.sign)
        and (args.cause is None or combo[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, sign_id, cause_id = rng.choice(sorted(combos))
    tool_id = args.tool or rng.choice(sorted(tool.id for tool in sensible_tools()))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        sign=sign_id,
        cause=cause_id,
        tool=tool_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.hero_gender})")
    if TOOLS[params.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(params.tool))

    place = PLACES[params.place]
    sign = SIGNS[params.sign]
    cause = CAUSES[params.cause]
    if not sign_possible(place, sign, cause):
        raise StoryError(explain_rejection(place, sign, cause))

    world = tell(
        place=place,
        sign=sign,
        cause_cfg=cause,
        tool=TOOLS[params.tool],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        trait=params.trait,
    )

    world.get("hero").label = params.hero_name

    story_text = world.render().replace("hero", params.hero_name)
    story_text = story_text.replace("helper", world.get("helper").label_word)
    story_text = story_text.replace("hero", params.hero_name)

    return StorySample(
        params=params,
        story=story_text,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a.replace("hero", params.hero_name)) for q, a in story_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible_tool/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible_tools()
        print(f"sensible tools: {', '.join(sensible)}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sign, cause) combos:\n")
        for place, sign, cause in combos:
            print(f"  {place:14} {sign:10} {cause}")
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
            header = f"### {p.hero_name}: {p.sign} in {p.place} ({p.cause}, {p.tool}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
