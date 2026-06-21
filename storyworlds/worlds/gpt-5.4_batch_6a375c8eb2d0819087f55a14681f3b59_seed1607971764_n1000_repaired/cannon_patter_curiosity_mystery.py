#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cannon_patter_curiosity_mystery.py
=============================================================

A standalone storyworld about a curious child, an old cannon, and a small
mystery sound.

Seed premise
------------
A child visits an old fort-like place and hears a strange patter near an old
cannon. The sound feels spooky at first, but curiosity leads the child to look
closely, find the true cause, and help if help is needed. The ending image
proves that the mystery has turned into understanding.

Run it
------
    python storyworlds/worlds/gpt-5.4/cannon_patter_curiosity_mystery.py
    python storyworlds/worlds/gpt-5.4/cannon_patter_curiosity_mystery.py --place courtyard --source kitten_crate
    python storyworlds/worlds/gpt-5.4/cannon_patter_curiosity_mystery.py --source rain_gutter --tool stool
    python storyworlds/worlds/gpt-5.4/cannon_patter_curiosity_mystery.py --all
    python storyworlds/worlds/gpt-5.4/cannon_patter_curiosity_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cannon_patter_curiosity_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/cannon_patter_curiosity_mystery.py --asp
    python storyworlds/worlds/gpt-5.4/cannon_patter_curiosity_mystery.py --verify
"""

from __future__ import annotations

import argparse
import copy
import contextlib
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
    kind: str = "thing"            # "character" | "thing" | "animal"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "guide_woman"}
        male = {"boy", "father", "man", "guide_man"}
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "guide_woman": "guide",
            "guide_man": "guide",
        }.get(self.type, self.type)
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
    mood: str
    detail: str
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
class Source:
    id: str
    label: str
    hint: str
    patter_line: str
    reveal: str
    ending_image: str
    need: str                    # "none" | "reach" | "gentle" | "light"
    needs_help: bool = False
    animal: bool = False
    wet: bool = False
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
    grants: set[str] = field(default_factory=set)
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


def _r_sound_stirs_curiosity(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    mystery = world.get("mystery")
    if mystery.meters["sound"] >= THRESHOLD and ("sound_stirs",) not in world.fired:
        world.fired.add(("sound_stirs",))
        child.memes["curiosity"] += 1
        child.memes["worry"] += 1
        out.append("__mystery__")
    return out


def _r_need_help(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    if (
        (source.meters["stuck"] >= THRESHOLD or source.meters["lost"] >= THRESHOLD or source.meters["wet"] >= THRESHOLD)
        and ("need_help",) not in world.fired
    ):
        world.fired.add(("need_help",))
        source.meters["needs_help"] += 1
        out.append("__need_help__")
    return out


def _r_reveal_bring_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if world.get("source").meters["found"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        child.memes["relief"] += 1
        child.memes["worry"] = 0.0
        out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="sound_stirs_curiosity", tag="emotion", apply=_r_sound_stirs_curiosity),
    Rule(name="need_help", tag="physical", apply=_r_need_help),
    Rule(name="reveal_bring_relief", tag="emotion", apply=_r_reveal_bring_relief),
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
    "courtyard": Setting(
        id="courtyard",
        place="the stone fort courtyard",
        mood="gray and drizzly",
        detail="The sea wind moved through the old stones, and the black cannon pointed quietly toward the harbor.",
        affords={"rain_gutter", "sparrow_tarp"},
        tags={"fort", "rain"},
    ),
    "boathouse": Setting(
        id="boathouse",
        place="the fort boathouse",
        mood="dim and creaky",
        detail="A salt smell hung in the air, and an old cannon stood beside stacked rope and empty crates.",
        affords={"kitten_crate", "rope_tap"},
        tags={"harbor", "boathouse"},
    ),
    "museum_hall": Setting(
        id="museum_hall",
        place="the little fort museum hall",
        mood="hushed and echoey",
        detail="Polished floorboards shone under soft lamps, and a small brass cannon sat behind a rope line.",
        affords={"map_moth", "rope_tap"},
        tags={"museum", "history"},
    ),
}

SOURCES = {
    "rain_gutter": Source(
        id="rain_gutter",
        label="rainwater from a cracked gutter",
        hint="a tiny silver drip in the gray light",
        patter_line="A soft patter came from the cannon, as if small secret feet were running over the metal.",
        reveal="A line of raindrops slipped from a cracked gutter and tapped the cannon barrel one by one.",
        ending_image="Soon the child could hear the rain as a pattern instead of a secret, and the old cannon only shone with beads of water.",
        need="none",
        needs_help=False,
        animal=False,
        wet=True,
        tags={"rain", "water"},
    ),
    "kitten_crate": Source(
        id="kitten_crate",
        label="a lost kitten in a powder crate",
        hint="a striped ear tucked behind a slat",
        patter_line="From beside the cannon came a nervous patter, quick and tiny, then a pause.",
        reveal="Inside an old powder crate, a little kitten was pacing in circles, its paws making that worried patter on the wood.",
        ending_image="When the kitten was warm in the guide's arms, the boathouse did not feel spooky anymore, and the cannon seemed to guard a small rescue instead of a secret.",
        need="reach",
        needs_help=True,
        animal=True,
        wet=False,
        tags={"kitten", "animal_help"},
    ),
    "sparrow_tarp": Source(
        id="sparrow_tarp",
        label="a sparrow tangled in the cannon cover",
        hint="a feather trembling under the canvas",
        patter_line="Something made a dry little patter across the cannon cover, then rustled and went still.",
        reveal="A sparrow had slipped under the canvas cover, and its frightened claws were pattering as it tried to find a way out.",
        ending_image="After the sparrow burst into the open air, the child watched it rise above the cannon, and the whole courtyard felt lighter.",
        need="gentle",
        needs_help=True,
        animal=True,
        wet=False,
        tags={"bird", "animal_help"},
    ),
    "map_moth": Source(
        id="map_moth",
        label="a moth near the old map case",
        hint="a pale wing flickering by the frame",
        patter_line="Near the little cannon came the faintest patter, so light it almost sounded like paper whispering.",
        reveal="A pale moth was bumping against the glass of the map case, and each tiny tap had bounced through the quiet hall.",
        ending_image="The child smiled at the still room after that, because the museum kept its mystery but not its fear, and the cannon looked peaceful under the lamp.",
        need="light",
        needs_help=False,
        animal=True,
        wet=False,
        tags={"moth", "museum"},
    ),
    "rope_tap": Source(
        id="rope_tap",
        label="a loose signal rope",
        hint="a frayed end swaying in the corner",
        patter_line="The patter seemed to come and go, as if an invisible visitor kept tapping and hiding near the cannon.",
        reveal="A loose signal rope was swinging in the draft and patting the cannon carriage with its frayed end.",
        ending_image="Once the rope was tied back, the hush returned, and the cannon looked like an ordinary old machine with no ghost in it at all.",
        need="none",
        needs_help=False,
        animal=False,
        wet=False,
        tags={"rope", "wind"},
    ),
}

TOOLS = {
    "listen": Tool(
        id="listen",
        label="careful listening",
        phrase="careful listening",
        grants={"none"},
        action="stood very still and listened for the rhythm of the sound",
        tags={"observe"},
    ),
    "stool": Tool(
        id="stool",
        label="wooden stool",
        phrase="a sturdy wooden stool",
        grants={"reach"},
        action="pulled over a wooden stool so they could look down into the crate",
        tags={"reach"},
    ),
    "crumbs": Tool(
        id="crumbs",
        label="bread crumbs",
        phrase="a little paper twist of bread crumbs",
        grants={"gentle"},
        action="sprinkled a few bread crumbs and waited with calm hands",
        tags={"gentle"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a small hand lantern",
        grants={"light"},
        action="lifted a lantern and sent a warm circle of light toward the sound",
        tags={"light"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Tess", "Ava", "Zoe", "Maya", "Ella"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Sam", "Max", "Eli", "Theo", "Ben"]
TRAITS = ["curious", "careful", "quiet", "thoughtful", "brave"]
HELPERS = ["mother", "father", "guide_woman", "guide_man"]


def tool_fits(source: Source, tool: Tool) -> bool:
    return source.need in tool.grants


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for source_id in sorted(setting.affords):
            source = SOURCES[source_id]
            for tool_id, tool in TOOLS.items():
                if tool_fits(source, tool):
                    combos.append((place_id, source_id, tool_id))
    return sorted(combos)


def explain_rejection(place: Optional[str], source: Optional[str], tool: Optional[str]) -> str:
    if place and source and source not in SETTINGS[place].affords:
        return (
            f"(No story: {SOURCES[source].label} is not a plausible mystery in {SETTINGS[place].place}. "
            f"Pick a source that belongs in that setting.)"
        )
    if source and tool and not tool_fits(SOURCES[source], TOOLS[tool]):
        need = SOURCES[source].need
        names = ", ".join(sorted(tid for tid, t in TOOLS.items() if need in t.grants))
        return (
            f"(No story: {TOOLS[tool].label} would not honestly solve this mystery. "
            f"The source '{source}' needs a tool for '{need}'. Try: {names}.)"
        )
    return "(No story: that combination is not a reasonable mystery here.)"


@dataclass
class StoryParams:
    place: str
    source: str
    tool: str
    child_name: str
    child_gender: str
    helper: str
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


def predict_find(world: World, tool_id: str) -> dict:
    sim = world.copy()
    source = sim.get("source")
    tool = TOOLS[tool_id]
    if tool_fits(SOURCES[source.attrs["source_id"]], tool):
        source.meters["found"] += 1
    propagate(sim, narrate=False)
    return {
        "found": source.meters["found"] >= THRESHOLD,
        "needs_help": source.meters["needs_help"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"{child.id} was a {child.traits[0]} {child.type} who liked old places because they always seemed to be hiding one more question."
    )
    world.say(
        f"One afternoon, {child.id} walked with {child.pronoun('possessive')} {helper.title_word} through {world.setting.place}. {world.setting.detail}"
    )


def set_mystery(world: World, child: Entity, source_cfg: Source) -> None:
    mystery = world.get("mystery")
    source = world.get("source")
    mystery.meters["sound"] = 1.0
    if source_cfg.needs_help:
        source.meters["stuck"] = 1.0
        source.meters["lost"] = 1.0
    if source_cfg.wet:
        source.meters["wet"] = 1.0
    propagate(world, narrate=False)
    world.say(f"The day felt {world.setting.mood}.")
    world.say(source_cfg.patter_line)
    if child.memes["curiosity"] >= THRESHOLD:
        world.say(
            f"{child.id} stopped at once. The sound was small, but it made the old cannon seem full of mystery."
        )


def wonder(world: World, child: Entity, helper: Entity, source_cfg: Source) -> None:
    world.say(
        f'"Did you hear that?" {child.id} whispered. "{helper.title_word.capitalize()}, what could make that patter?"'
    )
    world.say(
        f'{helper.title_word.capitalize()} listened too, then smiled a little. "Let us look before we guess," {helper.pronoun()} said.'
    )
    world.facts["first_hint"] = source_cfg.hint


def investigate(world: World, child: Entity, helper: Entity, tool_cfg: Tool, source_cfg: Source) -> None:
    pred = predict_find(world, tool_cfg.id)
    world.facts["predicted_found"] = pred["found"]
    world.facts["predicted_help"] = pred["needs_help"]
    child.memes["curiosity"] += 1
    world.say(
        f"Instead of backing away, {child.id}'s curiosity pulled {child.pronoun('object')} one careful step closer."
    )
    world.say(
        f"{helper.title_word.capitalize()} took {tool_cfg.phrase}, and together they {tool_cfg.action}."
    )
    src = world.get("source")
    src.meters["found"] = 1.0
    propagate(world, narrate=False)
    world.say(source_cfg.reveal)


def help_if_needed(world: World, child: Entity, helper: Entity, source_cfg: Source) -> None:
    source = world.get("source")
    if source.meters["needs_help"] < THRESHOLD:
        world.facts["outcome"] = "explained"
        return
    source.meters["safe"] = 1.0
    child.memes["kindness"] += 1
    if source_cfg.id == "kitten_crate":
        world.say(
            f'{helper.title_word.capitalize()} opened the crate, and the kitten stepped out with one last tiny patter before tucking itself against {helper.pronoun("possessive")} coat.'
        )
    elif source_cfg.id == "sparrow_tarp":
        world.say(
            f'{helper.title_word.capitalize()} lifted the edge of the cover slowly, and the sparrow hopped free, then flashed up into the air.'
        )
    world.facts["outcome"] = "helped"


def close_story(world: World, child: Entity, source_cfg: Source) -> None:
    child.memes["wonder"] += 1
    world.say(
        f'{child.id} let out a slow breath and smiled. "{source_cfg.hint.capitalize()}," {child.pronoun()} said, pleased to have noticed the clue at last.'
    )
    world.say(source_cfg.ending_image)


def tell(
    setting: Setting,
    source_cfg: Source,
    tool_cfg: Tool,
    child_name: str = "Lila",
    child_gender: str = "girl",
    helper_type: str = "guide_woman",
    trait: str = "curious",
) -> World:
    world = World(setting)

    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            attrs={"bravery": "small"},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="cannon",
            kind="thing",
            type="cannon",
            label="cannon",
            attrs={"old": True},
        )
    )
    world.add(
        Entity(
            id="mystery",
            kind="thing",
            type="mystery",
            label="mystery sound",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="source",
            kind="animal" if source_cfg.animal else "thing",
            type="source",
            label=source_cfg.label,
            attrs={"source_id": source_cfg.id},
        )
    )

    child.memes["curiosity"] = 1.0 if trait == "curious" else 0.5
    child.memes["worry"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["kindness"] = 0.0

    world.facts.update(
        setting=setting,
        source_cfg=source_cfg,
        tool_cfg=tool_cfg,
        child=child,
        helper=helper,
        hint=source_cfg.hint,
    )

    introduce(world, child, helper)
    world.para()
    set_mystery(world, child, source_cfg)
    wonder(world, child, helper, source_cfg)
    world.para()
    investigate(world, child, helper, tool_cfg, source_cfg)
    help_if_needed(world, child, helper, source_cfg)
    world.para()
    close_story(world, child, source_cfg)

    world.facts.update(
        found=world.get("source").meters["found"] >= THRESHOLD,
        needs_help=world.get("source").meters["needs_help"] >= THRESHOLD,
        safe=world.get("source").meters["safe"] >= THRESHOLD,
        curious=child.memes["curiosity"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "fort": [
        (
            "What is a cannon?",
            "A cannon is a big metal gun from long ago. Many old forts keep cannons as history objects, and people usually only look at them now."
        )
    ],
    "rain": [
        (
            "Why can rain make a patter sound?",
            "Raindrops tap on wood, stone, cloth, or metal one after another. Those tiny taps can join into a soft patter."
        )
    ],
    "kitten": [
        (
            "Why might a lost kitten sound small and quick?",
            "A kitten has light paws, so it makes tiny sounds when it walks. If it is worried, those steps can come fast and nervous."
        )
    ],
    "bird": [
        (
            "Why do birds need gentle help when they are trapped?",
            "Birds can get more frightened if people rush at them. Calm, gentle movements help them find a safe way out."
        )
    ],
    "moth": [
        (
            "Why can a moth tap against a light or window?",
            "Moths are often drawn toward light. When they flutter near glass or a lamp, their wings and bodies can make faint little taps."
        )
    ],
    "rope": [
        (
            "Why would a loose rope make a tapping sound?",
            "If wind or a draft moves a loose rope, its end can swing and tap against wood or metal again and again. That can sound mysterious until you see it."
        )
    ],
    "observe": [
        (
            "How can careful listening help solve a mystery?",
            "Careful listening helps you notice where a sound starts, stops, or repeats. That gives you clues before you even see the cause."
        )
    ],
    "reach": [
        (
            "Why is a stool useful for looking into a high place?",
            "A stool lifts you higher so you can see safely into a crate, shelf, or window ledge. It helps you solve problems without climbing somewhere wobbly."
        )
    ],
    "gentle": [
        (
            "Why can waiting quietly help an animal come out?",
            "A scared animal may hide if people move too fast. Quiet waiting makes the place feel safer for it."
        )
    ],
    "light": [
        (
            "Why does a lantern help in a dim place?",
            "A lantern sends light into dark corners, so hidden things are easier to see. Good light turns guessing into noticing."
        )
    ],
}
KNOWLEDGE_ORDER = ["fort", "rain", "kitten", "bird", "moth", "rope", "observe", "reach", "gentle", "light"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    source = f["source_cfg"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old about a curious child who hears a patter near an old cannon in {setting.place}.',
        f"Tell a gentle mystery where {child.id} follows a tiny sound instead of running away and discovers that it is really {source.label}.",
        "Write a child-facing story where curiosity solves a spooky-sounding problem and the ending feels calm instead of scary.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    source = f["source_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious {child.type}, and {child.pronoun('possessive')} {helper.title_word} in an old place with a cannon. They become the ones who solve the little mystery together."
        ),
        (
            "What made the mystery begin?",
            f"The mystery began when {child.id} heard a patter near the cannon and could not tell what was making it. The strange sound made the place feel spooky before anyone knew the true cause."
        ),
        (
            f"Why did {child.id} go closer instead of running away?",
            f"{child.id} felt a little worried, but curiosity was stronger. {child.pronoun().capitalize()} wanted to know what the sound really was, so {child.pronoun()} looked carefully instead of guessing."
        ),
        (
            f"How did they solve the mystery?",
            f"They used {tool.phrase} and paid close attention to the clue they noticed. That helped them discover that the sound was really {source.label}."
        ),
    ]
    if f["outcome"] == "helped":
        qa.append(
            (
                "What happened after they found the cause?",
                f"They saw that the creature needed help, so they acted gently and made it safe. The mystery changed into a rescue, which is why the ending felt warm instead of frightening."
            )
        )
    else:
        qa.append(
            (
                "What happened after they found the cause?",
                f"Once they understood the sound, the scary feeling melted away. Nothing dangerous was hiding there, and the old cannon became ordinary again."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with understanding instead of fear. {source.ending_image}"
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.setting.tags) | set(world.facts["source_cfg"].tags) | set(world.facts["tool_cfg"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="courtyard",
        source="rain_gutter",
        tool="listen",
        child_name="Lila",
        child_gender="girl",
        helper="guide_woman",
        trait="curious",
    ),
    StoryParams(
        place="boathouse",
        source="kitten_crate",
        tool="stool",
        child_name="Owen",
        child_gender="boy",
        helper="father",
        trait="thoughtful",
    ),
    StoryParams(
        place="courtyard",
        source="sparrow_tarp",
        tool="crumbs",
        child_name="Mina",
        child_gender="girl",
        helper="guide_man",
        trait="careful",
    ),
    StoryParams(
        place="museum_hall",
        source="map_moth",
        tool="lantern",
        child_name="Theo",
        child_gender="boy",
        helper="mother",
        trait="quiet",
    ),
    StoryParams(
        place="museum_hall",
        source="rope_tap",
        tool="listen",
        child_name="Nora",
        child_gender="girl",
        helper="guide_woman",
        trait="curious",
    ),
]


ASP_RULES = r"""
% registry side
valid(Place, Source, Tool) :- affords(Place, Source), source_need(Source, Need), grants(Tool, Need).

% simple ending model
helped(Source) :- source_needs_help(Source).
outcome(helped) :- chosen_source(Source), helped(Source).
outcome(explained) :- chosen_source(Source), not helped(Source).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        for source_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, source_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("source_need", source_id, source.need))
        if source.needs_help:
            lines.append(asp.fact("source_needs_help", source_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for grant in sorted(tool.grants):
            lines.append(asp.fact("grants", tool_id, grant))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    return "helped" if SOURCES[params.source].needs_help else "explained"


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_source", params.source),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    cases = list(CURATED)
    for s in range(60):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a curious child hears a patter near a cannon and solves a gentle mystery."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and args.source not in SETTINGS[args.place].affords:
        raise StoryError(explain_rejection(args.place, args.source, args.tool))
    if args.source and args.tool and not tool_fits(SOURCES[args.source], TOOLS[args.tool]):
        raise StoryError(explain_rejection(args.place, args.source, args.tool))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.source is None or c[1] == args.source)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, source, tool = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        source=source,
        tool=tool,
        child_name=name,
        child_gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.place]
        source_cfg = SOURCES[params.source]
        tool_cfg = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if params.source not in setting.affords or not tool_fits(source_cfg, tool_cfg):
        raise StoryError(explain_rejection(params.place, params.source, params.tool))

    world = tell(
        setting=setting,
        source_cfg=source_cfg,
        tool_cfg=tool_cfg,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, tool) combos:\n")
        for place, source, tool in combos:
            print(f"  {place:12} {source:14} {tool}")
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
            header = f"### {p.child_name}: {p.source} at {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
