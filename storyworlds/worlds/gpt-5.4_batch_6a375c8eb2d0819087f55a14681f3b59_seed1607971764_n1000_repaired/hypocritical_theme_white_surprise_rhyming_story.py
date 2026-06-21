#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hypocritical_theme_white_surprise_rhyming_story.py
==============================================================================

A standalone story world for a small rhyming tale about children preparing a
surprise with a clear theme and a white decoration. One child gives a neatness
lecture, then breaks the same rule and makes a mess, which feels hypocritical.
The children must repair the surprise before the guest arrives.

The world is state-driven:
- typed entities carry physical meters and emotional memes
- a small causal engine turns stains into worry and apology into relief
- prose depends on outcome state, not frozen templates
- a Python reasonableness gate has an inline ASP twin

Run it
------
    python storyworlds/worlds/gpt-5.4/hypocritical_theme_white_surprise_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/hypocritical_theme_white_surprise_rhyming_story.py --theme moon --spill berry_juice --surface sheet
    python storyworlds/worlds/gpt-5.4/hypocritical_theme_white_surprise_rhyming_story.py --repair dab
    python storyworlds/worlds/gpt-5.4/hypocritical_theme_white_surprise_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/hypocritical_theme_white_surprise_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/hypocritical_theme_white_surprise_rhyming_story.py --verify
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
        female = {"girl", "mother", "grandmother", "woman", "aunt", "teacher_f"}
        male = {"boy", "father", "grandfather", "man", "uncle", "teacher_m"}
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
            "teacher_f": "teacher",
            "teacher_m": "teacher",
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
class Theme:
    id: str
    label: str
    decorations: str
    patch: str
    closing_image: str
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
class Spill:
    id: str
    label: str
    carry_phrase: str
    splash_text: str
    stain_kind: str
    severity: int
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
class Surface:
    id: str
    label: str
    phrase: str
    material: str
    role_text: str
    base_severity: int
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
class Repair:
    id: str
    label: str
    sense: int
    power: int
    materials: set[str]
    stain_kinds: set[str]
    text: str
    fail_text: str
    qa_text: str
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
class StoryParams:
    theme: str
    spill: str
    surface: str
    repair: str
    planner: str
    planner_gender: str
    helper: str
    helper_gender: str
    recipient: str
    delay: int = 0
    trait: str = "bossy"
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"planner", "helper"}]

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


def _r_stain_worry(world: World) -> list[str]:
    surface = world.entities.get("surface")
    if surface is None or surface.meters["stained"] < THRESHOLD:
        return []
    sig = ("stain_worry", surface.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    planner = world.entities.get("planner")
    if planner is not None:
        planner.memes["shame"] += 1
    return ["__stain__"]


def _r_apology_relief(world: World) -> list[str]:
    planner = world.entities.get("planner")
    helper = world.entities.get("helper")
    if planner is None or helper is None:
        return []
    if planner.memes["apology"] < THRESHOLD:
        return []
    sig = ("apology_relief", planner.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    planner.memes["relief"] += 1
    helper.memes["relief"] += 1
    helper.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="stain_worry", tag="emotion", apply=_r_stain_worry),
    Rule(name="apology_relief", tag="social", apply=_r_apology_relief),
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


THEMES = {
    "moon": Theme(
        id="moon",
        label="moonbeam",
        decorations="silver stars and round paper moons",
        patch="moon-shaped stickers",
        closing_image="their moonbeam surprise glowed soft and bright",
        tags={"theme", "moon"},
    ),
    "garden": Theme(
        id="garden",
        label="garden",
        decorations="paper petals and curling green vines",
        patch="flower cutouts",
        closing_image="their garden surprise bloomed in the lamplight",
        tags={"theme", "garden"},
    ),
    "ocean": Theme(
        id="ocean",
        label="ocean",
        decorations="blue fish and curling foam",
        patch="little fish cutouts",
        closing_image="their ocean surprise swayed like a tiny tide",
        tags={"theme", "ocean"},
    ),
}

SPILLS = {
    "berry_juice": Spill(
        id="berry_juice",
        label="berry juice",
        carry_phrase="a cup of berry juice",
        splash_text="a purple splash skipped from the cup and kissed the cloth",
        stain_kind="wet",
        severity=1,
        tags={"juice", "stain"},
    ),
    "blue_paint": Spill(
        id="blue_paint",
        label="blue paint",
        carry_phrase="a tray of blue paint",
        splash_text="a bright blue blob slid loose and plopped with a sticky flop",
        stain_kind="paint",
        severity=2,
        tags={"paint", "stain"},
    ),
    "muddy_gloves": Spill(
        id="muddy_gloves",
        label="muddy gloves",
        carry_phrase="muddy gloves and a string of tape",
        splash_text="a brown handprint bloomed where the glove gave one small bump",
        stain_kind="mud",
        severity=1,
        tags={"mud", "stain"},
    ),
}

SURFACES = {
    "sheet": Surface(
        id="sheet",
        label="sheet",
        phrase="a white sheet",
        material="cloth",
        role_text="the curtain for the surprise stage",
        base_severity=1,
        tags={"white", "cloth"},
    ),
    "banner": Surface(
        id="banner",
        label="banner",
        phrase="a white paper banner",
        material="paper",
        role_text="the sign above the surprise table",
        base_severity=1,
        tags={"white", "paper"},
    ),
}

REPAIRS = {
    "wash": Repair(
        id="wash",
        label="wash and dry",
        sense=3,
        power=3,
        materials={"cloth"},
        stain_kinds={"wet", "mud"},
        text="They hurried to rinse the mark, pat it with towels, and dry it by the fan",
        fail_text="They dabbed and rinsed, but the mark still spread in a pale ring",
        qa_text="They rinsed the stain, dried the cloth, and made it clean again",
        tags={"wash"},
    ),
    "cover": Repair(
        id="cover",
        label="cover with cutouts",
        sense=3,
        power=2,
        materials={"cloth", "paper"},
        stain_kinds={"wet", "mud", "paint"},
        text="They snipped themed shapes and covered the mark so neatly it looked planned all along",
        fail_text="They added cutouts, but the blot was so wide that the edges still peeked out",
        qa_text="They covered the stain with themed decorations so it looked like part of the design",
        tags={"cover"},
    ),
    "repaint": Repair(
        id="repaint",
        label="paint a fresh panel",
        sense=2,
        power=3,
        materials={"paper"},
        stain_kinds={"paint", "mud"},
        text="They made a fresh painted panel, then pinned it over the spoiled part of the banner",
        fail_text="They painted a new panel, but it stayed damp and wrinkled before the knock came",
        qa_text="They painted a fresh panel and pinned it over the spoiled part",
        tags={"repaint"},
    ),
    "dab": Repair(
        id="dab",
        label="dab with one napkin",
        sense=1,
        power=1,
        materials={"cloth", "paper"},
        stain_kinds={"wet", "mud", "paint"},
        text="They dabbed at the mark with one napkin and hoped for the best",
        fail_text="They dabbed at the mark with one napkin, but it hardly helped at all",
        qa_text="They only dabbed at the stain with a napkin",
        tags={"dab"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["bossy", "careful", "sparkly", "hasty", "earnest", "cheerful"]

RECIPIENT_TYPES = {
    "grandmother": "Grandma",
    "grandfather": "Grandpa",
    "teacher_f": "Teacher May",
    "teacher_m": "Teacher Ray",
}

KNOWLEDGE = {
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something kind that someone keeps secret for a little while and then reveals at a special moment."
        )
    ],
    "theme": [
        (
            "What is a theme at a party or show?",
            "A theme is the main idea that helps decorations and colors match. It makes many little parts feel like they belong together."
        )
    ],
    "white": [
        (
            "Why do stains show up quickly on white things?",
            "They show up quickly because white does not hide color well. Even a small splash can be easy to see."
        )
    ],
    "paint": [
        (
            "Why can paint be hard to clean?",
            "Paint can stick as it dries, so it may leave a mark if you do not fix it quickly."
        )
    ],
    "mud": [
        (
            "Why does mud make dirty marks?",
            "Mud is wet dirt, so it leaves dark smudges when it touches cloth or paper."
        )
    ],
    "juice": [
        (
            "Why can berry juice stain?",
            "Berry juice has strong color in it, so the purple or red can soak into cloth and leave a mark."
        )
    ],
    "wash": [
        (
            "How can washing help with some stains?",
            "Washing can lift away dirt or juice before it settles deep into cloth. It works best when you hurry."
        )
    ],
    "cover": [
        (
            "When can covering a mark be useful?",
            "Covering can help when you can safely hide a small stain with a patch or decoration that fits the picture."
        )
    ],
    "apology": [
        (
            "Why is an apology important after a mistake?",
            "An apology shows you know your choice hurt or troubled someone. It helps people mend trust while they fix the problem together."
        )
    ],
}
KNOWLEDGE_ORDER = ["surprise", "theme", "white", "juice", "paint", "mud", "wash", "cover", "apology"]


def repair_works(repair: Repair, surface: Surface, spill: Spill) -> bool:
    return surface.material in repair.materials and spill.stain_kind in repair.stain_kinds


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme_id in THEMES:
        for spill_id, spill in SPILLS.items():
            for surface_id, surface in SURFACES.items():
                if any(repair_works(r, surface, spill) and r.sense >= SENSE_MIN for r in REPAIRS.values()):
                    combos.append((theme_id, spill_id, surface_id))
    return sorted(combos)


def stain_severity(surface: Surface, spill: Spill, delay: int) -> int:
    return surface.base_severity + spill.severity + delay


def contained(repair: Repair, surface: Surface, spill: Spill, delay: int) -> bool:
    return repair_works(repair, surface, spill) and repair.power >= stain_severity(surface, spill, delay)


def explain_rejection(spill: Spill, surface: Surface, repair: Repair) -> str:
    if repair.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_repairs()))
        return (
            f"(Refusing repair '{repair.id}': it scores too low on common sense "
            f"(sense={repair.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    if surface.material not in repair.materials:
        return (
            f"(No story: {repair.label} does not fit a {surface.material} {surface.label}. "
            f"Pick a repair meant for {surface.material}.)"
        )
    if spill.stain_kind not in repair.stain_kinds:
        return (
            f"(No story: {repair.label} does not sensibly fix a {spill.label} mark.)"
        )
    return "(No story: this combination does not make a reasonable repair.)"


def outcome_of(params: StoryParams) -> str:
    surface = SURFACES[params.surface]
    spill = SPILLS[params.spill]
    repair = REPAIRS[params.repair]
    return "clean" if contained(repair, surface, spill, params.delay) else "patched"


def _do_stain(world: World, surface_ent: Entity, spill: Spill, delay: int, narrate: bool = True) -> None:
    surface_ent.meters["stained"] += 1
    surface_ent.meters["severity"] = float(spill.severity + delay)
    world.facts["stain_kind"] = spill.stain_kind
    propagate(world, narrate=narrate)


def setup(world: World, planner: Entity, helper: Entity, recipient: Entity, theme: Theme, surface: Surface) -> None:
    for kid in (planner, helper):
        kid.memes["joy"] += 1
    world.say(
        f"{planner.id} and {helper.id} were making a surprise for {recipient.label}. "
        f"They picked a {theme.label} theme, soft and light, and whispered as they worked that night."
    )
    world.say(
        f"Across two chairs they hung {surface.phrase} as {surface.role_text}, "
        f"then trimmed it with {theme.decorations} to make it bright."
    )


def warning(world: World, planner: Entity, helper: Entity, spill: Spill, surface: Surface) -> None:
    planner.memes["pride"] += 1
    helper.memes["trust"] += 1
    world.say(
        f'"Careful, careful," sang {planner.id}, "keep {spill.label} far from the {surface.phrase}; '
        f'one little splash could spoil the place."'
    )
    world.say(
        f"{helper.id} nodded and stepped back slow, while the white shine made the whole room glow."
    )


def hypocritical_turn(world: World, planner: Entity, helper: Entity, spill: Spill) -> None:
    planner.memes["haste"] += 1
    world.say(
        f"But then {planner.id} grew fast instead of wise and snatched up {spill.carry_phrase} with busy eyes."
    )
    world.say(
        f'{helper.id} blinked and said, "That is the very rule you said!"'
    )


def spill_event(world: World, planner: Entity, helper: Entity, surface_ent: Entity, spill: Spill, delay: int) -> None:
    _do_stain(world, surface_ent, spill, delay)
    world.say(
        f"Trip, tip, slip—{spill.splash_text}. The song went quiet; both hearts felt the hit."
    )
    world.say(
        f'"Oh dear," said {helper.id}, "that sounded hypocritical to me—'
        f'you warned me first, then hurried free."'
    )
    planner.memes["shame"] += 1


def apology(world: World, planner: Entity, helper: Entity) -> None:
    planner.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{planner.id} looked small and said, "You are right. I made the rule, then forgot it in my rush tonight."'
    )
    world.say(
        f'"I was hypocritical," {planner.pronoun()} said, "and I am sorry for the worry in your head."'
    )


def repair_scene(world: World, planner: Entity, helper: Entity, theme: Theme, repair: Repair,
                 surface: Surface, spill: Spill, delay: int) -> None:
    success = contained(repair, surface, spill, delay)
    world.facts["repair_success"] = success
    world.facts["repair_kind"] = repair.id
    if success:
        world.say(
            f"{repair.text}. Their fingers flew; their hope came back, and rhyme returned to the little track."
        )
        world.get("surface").meters["stained"] = 0.0
        world.get("surface").meters["mended"] += 1
        for kid in world.kids():
            kid.memes["relief"] += 1
    else:
        world.say(
            f"{repair.fail_text}. So {helper.id} cried, \"I know one more thing—let's make the mark part of the theme we bring.\""
        )
        world.get("surface").meters["patched"] += 1
        world.get("surface").meters["stained"] = 0.0
        world.get("surface").meters["mended"] += 1
        planner.memes["relief"] += 1
        helper.memes["relief"] += 1
        world.say(
            f"They added {theme.patch} around the spot, and soon the odd mark mattered not."
        )


def reveal(world: World, planner: Entity, helper: Entity, recipient: Entity, theme: Theme, outcome: str) -> None:
    for kid in (planner, helper):
        kid.memes["joy"] += 1
        kid.memes["love"] += 1
    world.say(
        f"Then came a knock—tap, tap, delight—and {recipient.label} stepped in from the hall of light."
    )
    if outcome == "clean":
        world.say(
            f'"Surprise!" the children chimed in tune, and {recipient.label} smiled beneath the paper moon.'
            if theme.id == "moon"
            else f'"Surprise!" the children chimed with pride, and {recipient.label} smiled at the lovely scene inside.'
        )
    else:
        world.say(
            f'"Surprise!" the children sang at last, and {recipient.label} laughed at the clever patch they had made so fast.'
        )
    world.say(
        f"{recipient.label} saw the care in every line, and {theme.closing_image}, gentle and fine."
    )


def lesson(world: World, planner: Entity, helper: Entity, recipient: Entity) -> None:
    world.say(
        f'{recipient.label} hugged them both and said, "A mistake can sting, but telling the truth is a brave, bright thing."'
    )
    world.say(
        f"{planner.id} remembered then what was true: a rule sounds best when it is kept by you."
    )


def tell(theme: Theme, spill: Spill, surface: Surface, repair: Repair,
         planner_name: str = "Lily", planner_gender: str = "girl",
         helper_name: str = "Tom", helper_gender: str = "boy",
         recipient_type: str = "grandmother", delay: int = 0,
         trait: str = "bossy") -> World:
    world = World()
    planner = world.add(Entity(
        id="planner",
        kind="character",
        type=planner_gender,
        label=planner_name,
        role="planner",
        traits=[trait],
        attrs={},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        traits=["patient"],
        attrs={},
    ))
    recipient = world.add(Entity(
        id="recipient",
        kind="character",
        type=recipient_type,
        label=RECIPIENT_TYPES[recipient_type],
        role="recipient",
        attrs={},
    ))
    surface_ent = world.add(Entity(
        id="surface",
        kind="thing",
        type=surface.material,
        label=surface.label,
        role="surface",
        attrs={"material": surface.material, "color": "white"},
    ))

    world.facts.update(
        theme=theme,
        spill=spill,
        surface_cfg=surface,
        repair=repair,
        planner=planner,
        helper=helper,
        recipient=recipient,
        delay=delay,
        trait=trait,
    )

    setup(world, planner, helper, recipient, theme, surface)
    world.para()
    warning(world, planner, helper, spill, surface)
    hypocritical_turn(world, planner, helper, spill)
    world.para()
    spill_event(world, planner, helper, surface_ent, spill, delay)
    apology(world, planner, helper)
    world.para()
    repair_scene(world, planner, helper, theme, repair, surface, spill, delay)
    world.para()
    outcome = "clean" if contained(repair, surface, spill, delay) else "patched"
    reveal(world, planner, helper, recipient, theme, outcome)
    lesson(world, planner, helper, recipient)

    world.facts.update(
        outcome=outcome,
        stain_happened=True,
        recipient_name=recipient.label,
        planner_name=planner_name,
        helper_name=helper_name,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme = f["theme"]
    spill = f["spill"]
    surface = f["surface_cfg"]
    planner = f["planner"]
    helper = f["helper"]
    recipient = f["recipient"]
    return [
        (
            f'Write a rhyming surprise story for a 3-to-5-year-old that uses the words '
            f'"hypocritical," "theme," and "white," where two children prepare a {theme.label} surprise for {recipient.label}.'
        ),
        (
            f"Tell a gentle rhyming story where {planner.label} warns {helper.label} to keep "
            f"{spill.label} away from {surface.phrase}, then breaks the same rule and must help fix the mess."
        ),
        (
            f"Write a child-facing poem-story about a white decoration, a hurried mistake, "
            f"an apology, and a surprise ending that shows what the children learned."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    planner = f["planner"]
    helper = f["helper"]
    recipient = f["recipient"]
    theme = f["theme"]
    spill = f["spill"]
    surface = f["surface_cfg"]
    repair = f["repair"]
    outcome = f["outcome"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {planner.label} and {helper.label}, two children making a surprise for {recipient.label}. "
            f"They worked together on a {theme.label} theme."
        ),
        (
            "What was white in the story?",
            f"The children used {surface.phrase}. It was important because the white surface showed the stain right away."
        ),
        (
            f"Why did {helper.label} say {planner.label} sounded hypocritical?",
            f"{planner.label} had just warned everyone to keep {spill.label} away from the white decoration. "
            f"Then {planner.pronoun()} hurried with the same messy thing and caused the stain {planner.pronoun('possessive')}self."
        ),
        (
            "How did the mistake change the mood?",
            f"The room went from happy and busy to worried and quiet after the splash landed. "
            f"The stain made both children anxious because it might spoil the surprise."
        ),
        (
            f"How did they fix the problem?",
            f"{repair.qa_text}. After that, the surprise looked ready again and the children felt relieved."
        ),
    ]
    if outcome == "clean":
        qa.append(
            (
                "How did the story end?",
                f"It ended with the surprise looking neat and whole when {recipient.label} came in. "
                f"The ending image proves the children repaired the trouble before the reveal."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with the stain turned into part of the decoration, so the surprise still felt joyful. "
                f"The children learned that honesty and teamwork can mend a rushed mistake."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"surprise", "apology"} | set(f["theme"].tags) | set(f["surface_cfg"].tags) | set(f["spill"].tags) | set(f["repair"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="moon",
        spill="berry_juice",
        surface="sheet",
        repair="wash",
        planner="Lily",
        planner_gender="girl",
        helper="Tom",
        helper_gender="boy",
        recipient="grandmother",
        delay=0,
        trait="bossy",
    ),
    StoryParams(
        theme="garden",
        spill="blue_paint",
        surface="banner",
        repair="repaint",
        planner="Max",
        planner_gender="boy",
        helper="Mia",
        helper_gender="girl",
        recipient="teacher_f",
        delay=0,
        trait="earnest",
    ),
    StoryParams(
        theme="ocean",
        spill="blue_paint",
        surface="sheet",
        repair="cover",
        planner="Zoe",
        planner_gender="girl",
        helper="Ben",
        helper_gender="boy",
        recipient="grandfather",
        delay=1,
        trait="hasty",
    ),
    StoryParams(
        theme="garden",
        spill="muddy_gloves",
        surface="sheet",
        repair="wash",
        planner="Eli",
        planner_gender="boy",
        helper="Nora",
        helper_gender="girl",
        recipient="grandmother",
        delay=1,
        trait="careful",
    ),
]


ASP_RULES = r"""
% reasonableness gate
repair_works(R,S,P) :- repair(R), surface(S), spill(P),
                       fits_material(R,S), fits_stain(R,P).
sensible(R) :- repair(R), sense(R,V), sense_min(M), V >= M.
valid(T,P,S) :- theme(T), spill(P), surface(S), repair_works(R,S,P), sensible(R).

% outcome model
severity(SV + PV + D) :- chosen_surface(S), surface_base(S,SV),
                         chosen_spill(P), spill_severity(P,PV), delay(D).
contains :- chosen_repair(R), chosen_surface(S), chosen_spill(P),
            repair_works(R,S,P), repair_power(R,PW), severity(V), PW >= V.
outcome(clean) :- contains.
outcome(patched) :- not contains.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for spill_id, spill in SPILLS.items():
        lines.append(asp.fact("spill", spill_id))
        lines.append(asp.fact("spill_kind", spill_id, spill.stain_kind))
        lines.append(asp.fact("spill_severity", spill_id, spill.severity))
    for surface_id, surface in SURFACES.items():
        lines.append(asp.fact("surface", surface_id))
        lines.append(asp.fact("surface_material", surface_id, surface.material))
        lines.append(asp.fact("surface_base", surface_id, surface.base_severity))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("repair_power", repair_id, repair.power))
        for material in sorted(repair.materials):
            lines.append(asp.fact("fits_material", repair_id, material))
        for stain_kind in sorted(repair.stain_kinds):
            lines.append(asp.fact("fits_stain_kind", repair_id, stain_kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append("fits_material(R,S) :- surface_material(S,M), fits_material(R,M).")
    lines.append("fits_stain(R,P) :- spill_kind(P,K), fits_stain_kind(R,K).")
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

    scenario = "\n".join([
        asp.fact("chosen_surface", params.surface),
        asp.fact("chosen_spill", params.spill),
        asp.fact("chosen_repair", params.repair),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: a hypocritical mistake threatens a themed surprise."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--spill", choices=SPILLS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--recipient", choices=RECIPIENT_TYPES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the stain sits before the children repair it")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.repair is not None:
        repair = REPAIRS[args.repair]
        if repair.sense < SENSE_MIN:
            raise StoryError(explain_rejection(SPILLS[next(iter(SPILLS))], SURFACES[next(iter(SURFACES))], repair))

    if args.spill and args.surface and args.repair:
        spill = SPILLS[args.spill]
        surface = SURFACES[args.surface]
        repair = REPAIRS[args.repair]
        if not repair_works(repair, surface, spill) or repair.sense < SENSE_MIN:
            raise StoryError(explain_rejection(spill, surface, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.spill is None or combo[1] == args.spill)
        and (args.surface is None or combo[2] == args.surface)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, spill_id, surface_id = rng.choice(sorted(combos))

    candidate_repairs = [
        rid for rid, repair in REPAIRS.items()
        if repair.sense >= SENSE_MIN and repair_works(repair, SURFACES[surface_id], SPILLS[spill_id])
        and (args.repair is None or rid == args.repair)
    ]
    if not candidate_repairs:
        raise StoryError("(No sensible repair matches the given options.)")

    repair_id = rng.choice(sorted(candidate_repairs))
    planner_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    planner_name = _pick_name(rng, planner_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=planner_name)
    recipient = args.recipient or rng.choice(sorted(RECIPIENT_TYPES))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    trait = rng.choice(TRAITS)

    return StoryParams(
        theme=theme_id,
        spill=spill_id,
        surface=surface_id,
        repair=repair_id,
        planner=planner_name,
        planner_gender=planner_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        recipient=recipient,
        delay=delay,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.spill not in SPILLS:
        raise StoryError(f"(Unknown spill: {params.spill})")
    if params.surface not in SURFACES:
        raise StoryError(f"(Unknown surface: {params.surface})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.recipient not in RECIPIENT_TYPES:
        raise StoryError(f"(Unknown recipient: {params.recipient})")

    theme = THEMES[params.theme]
    spill = SPILLS[params.spill]
    surface = SURFACES[params.surface]
    repair = REPAIRS[params.repair]

    if repair.sense < SENSE_MIN or not repair_works(repair, surface, spill):
        raise StoryError(explain_rejection(spill, surface, repair))

    world = tell(
        theme=theme,
        spill=spill,
        surface=surface,
        repair=repair,
        planner_name=params.planner,
        planner_gender=params.planner_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        recipient_type=params.recipient,
        delay=params.delay,
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

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_repairs()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible repairs match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            emit(smoke_sample, trace=False, qa=False, header="")
        finally:
            sys.stdout = old_stdout
        if not smoke_sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, spill, surface) combos:\n")
        for theme_id, spill_id, surface_id in combos:
            print(f"  {theme_id:8} {spill_id:13} {surface_id}")
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
            header = (
                f"### {p.planner} & {p.helper}: {p.theme} / {p.spill} / "
                f"{p.surface} / {p.repair} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
