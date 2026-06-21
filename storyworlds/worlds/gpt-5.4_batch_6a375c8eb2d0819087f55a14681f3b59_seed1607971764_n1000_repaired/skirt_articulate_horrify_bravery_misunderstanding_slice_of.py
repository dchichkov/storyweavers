#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/skirt_articulate_horrify_bravery_misunderstanding_slice_of.py
=========================================================================================

A small slice-of-life story world about a child who notices a stain on someone's
skirt, misunderstands what it means, feels frightened, and then shows bravery by
speaking up clearly. The turn comes from the misunderstanding being corrected:
what looked alarming is harmless, and the ending image proves that brave,
articulate caring is a good thing.

The world models:
- physical state in meters: stain, checked, cleaned
- emotional/social state in memes: fear, courage, relief, trust, pride
- a reasonableness gate: only vivid spills on light skirts plausibly trigger the
  misunderstanding; dull stains on dark skirts are refused
- an inline ASP twin for the same gate and the simple outcome model

Run it
------
    python storyworlds/worlds/gpt-5.4/skirt_articulate_horrify_bravery_misunderstanding_slice_of.py
    python storyworlds/worlds/gpt-5.4/skirt_articulate_horrify_bravery_misunderstanding_slice_of.py --place classroom --spill jam --skirt yellow_school
    python storyworlds/worlds/gpt-5.4/skirt_articulate_horrify_bravery_misunderstanding_slice_of.py --spill mud
    python storyworlds/worlds/gpt-5.4/skirt_articulate_horrify_bravery_misunderstanding_slice_of.py --all --qa
    python storyworlds/worlds/gpt-5.4/skirt_articulate_horrify_bravery_misunderstanding_slice_of.py --verify
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
COURAGE_MIN = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Place:
    id: str
    label: str
    opening: str
    activity: str
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
    color: str
    vivid: bool
    harmless: bool
    source_line: str
    clue_line: str
    cleanup: str
    mistaken_for: str
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
class SkirtCfg:
    id: str
    phrase: str
    color: str
    light: bool
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
class SpeakerStyle:
    id: str
    line: str
    quality: str
    brave: int
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_horrify(world: World) -> list[str]:
    child = world.get("child")
    adult = world.get("adult")
    skirt = world.get("skirt")
    if skirt.meters["stained"] < THRESHOLD:
        return []
    if not world.facts.get("plausible_misread"):
        return []
    sig = ("horrify", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 2
    child.memes["concern"] += 1
    adult.memes["unaware"] += 1
    return ["__horrify__"]


def _r_speak(world: World) -> list[str]:
    child = world.get("child")
    adult = world.get("adult")
    if child.memes["fear"] < THRESHOLD:
        return []
    if child.memes["courage"] < THRESHOLD:
        return []
    if child.meters["spoke"] < THRESHOLD:
        return []
    sig = ("speak", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    adult.meters["checked"] += 1
    adult.memes["attention"] += 1
    child.memes["relief"] += 1
    return []


def _r_resolve(world: World) -> list[str]:
    adult = world.get("adult")
    skirt = world.get("skirt")
    child = world.get("child")
    if adult.meters["checked"] < THRESHOLD:
        return []
    if skirt.meters["stained"] < THRESHOLD:
        return []
    sig = ("resolve", adult.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    skirt.meters["cleaned"] += 1
    child.memes["fear"] = 0.0
    child.memes["relief"] += 2
    child.memes["pride"] += 1
    adult.memes["gratitude"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="horrify", tag="emotion", apply=_r_horrify),
    Rule(name="speak", tag="social", apply=_r_speak),
    Rule(name="resolve", tag="physical", apply=_r_resolve),
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


def plausible_misunderstanding(spill: Spill, skirt: SkirtCfg) -> bool:
    return spill.harmless and spill.vivid and skirt.light


def brave_enough(style: SpeakerStyle) -> bool:
    return style.brave >= COURAGE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for spill_id, spill in SPILLS.items():
            for skirt_id, skirt in SKIRTS.items():
                for style_id, style in STYLES.items():
                    if plausible_misunderstanding(spill, skirt) and brave_enough(style):
                        combos.append((place_id, spill_id, skirt_id, style_id))
    return combos


def predict_misread(world: World) -> dict:
    sim = world.copy()
    skirt = sim.get("skirt")
    skirt.meters["stained"] += 1
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "fear": child.memes["fear"],
        "concern": child.memes["concern"],
        "plausible": sim.facts.get("plausible_misread", False),
    }


def establish_scene(world: World, place: Place, child: Entity, adult: Entity, skirt: Entity) -> None:
    child.memes["calm"] += 1
    adult.memes["busy"] += 1
    world.say(
        f"It was a small ordinary afternoon at {place.label}. {place.opening}"
    )
    world.say(
        f"{child.id} was nearby while {adult.id} helped with {place.activity}. "
        f"{adult.pronoun().capitalize()} wore {skirt.label} that swayed softly when {adult.pronoun()} moved."
    )


def spill_happens(world: World, spill: Spill, adult: Entity, skirt: Entity) -> None:
    skirt.meters["stained"] += 1
    skirt.attrs["spill"] = spill.id
    propagate(world, narrate=False)
    world.say(
        spill.source_line.replace("{adult}", adult.id).replace("{skirt}", skirt.label)
    )
    world.say(
        f"A bright {spill.color} mark spread across the front of the skirt."
    )


def worry(world: World, child: Entity, spill: Spill, adult: Entity) -> None:
    pred = predict_misread(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_concern"] = pred["concern"]
    child.memes["noticed"] += 1
    world.say(
        f"{child.id} froze. From across the room, the mark looked so sudden and strange that the thought of {spill.mistaken_for} began to horrify {child.pronoun('object')}."
    )
    world.say(
        f"{child.pronoun().capitalize()} did not want to stare, but {child.pronoun()} also did not want to stay quiet if {adult.id} needed help."
    )


def hesitate(world: World, child: Entity) -> None:
    child.memes["hesitation"] += 1
    world.say(
        f"For one breath, {child.id} stood with a hot face and a tight throat, trying to find words that would be kind instead of rude."
    )


def articulate_concern(world: World, child: Entity, adult: Entity, style: SpeakerStyle) -> None:
    child.meters["spoke"] += 1
    child.memes["courage"] += style.brave
    propagate(world, narrate=False)
    world.say(
        f"Then {child.id} took a brave step closer and tried to articulate the worry as clearly as possible."
    )
    world.say(
        f'"{style.line}"'
    )


def check_and_explain(world: World, adult: Entity, spill: Spill, skirt: Entity, child: Entity) -> None:
    world.say(
        f"{adult.id} looked down, blinked once, and then touched the spot on {skirt.label}."
    )
    world.say(
        spill.clue_line.replace("{adult}", adult.id).replace("{child}", child.id)
    )
    world.say(
        f'It was only {spill.label}, not {spill.mistaken_for}. {adult.id} gave a small relieved laugh instead of a frightened one.'
    )


def praise(world: World, adult: Entity, child: Entity) -> None:
    child.memes["trust"] += 1
    adult.memes["warmth"] += 1
    world.say(
        f'"Thank you for telling me," {adult.id} said. "You were careful, and you were brave."'
    )
    world.say(
        f"{child.id}'s shoulders dropped at last. Being wrong felt a little embarrassing, but being silent would have felt worse."
    )


def ending(world: World, place: Place, child: Entity, adult: Entity, spill: Spill, skirt: Entity) -> None:
    world.say(
        spill.cleanup.replace("{adult}", adult.id).replace("{skirt}", skirt.label)
    )
    world.say(
        f"Soon the room felt ordinary again. {child.id} stayed near {adult.id}, and the afternoon went on with a cleaner skirt, an easier heart, and the quiet knowledge that speaking up kindly is its own sort of bravery."
    )


def tell(
    place: Place,
    spill: Spill,
    skirt_cfg: SkirtCfg,
    style: SpeakerStyle,
    child_name: str = "Mina",
    child_gender: str = "girl",
    adult_name: str = "Ms. Clara",
    adult_type: str = "teacher",
    child_trait: str = "careful",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[child_trait],
        attrs={"trait": child_trait},
    ))
    adult = world.add(Entity(
        id=adult_name,
        kind="character",
        type=adult_type,
        role="adult",
        attrs={},
    ))
    skirt = world.add(Entity(
        id="skirt",
        kind="thing",
        type="skirt",
        label=skirt_cfg.phrase,
        attrs={"color": skirt_cfg.color, "light": skirt_cfg.light},
    ))

    world.facts["place"] = place
    world.facts["spill_cfg"] = spill
    world.facts["skirt_cfg"] = skirt_cfg
    world.facts["style_cfg"] = style
    world.facts["plausible_misread"] = plausible_misunderstanding(spill, skirt_cfg)

    establish_scene(world, place, child, adult, skirt)
    world.para()
    spill_happens(world, spill, adult, skirt)
    worry(world, child, spill, adult)
    hesitate(world, child)
    world.para()
    articulate_concern(world, child, adult, style)
    check_and_explain(world, adult, spill, skirt, child)
    praise(world, adult, child)
    world.para()
    ending(world, place, child, adult, spill, skirt)

    world.facts.update(
        child=child,
        adult=adult,
        skirt=skirt,
        outcome="clarified",
        spoke=child.meters["spoke"] >= THRESHOLD,
        checked=adult.meters["checked"] >= THRESHOLD,
        cleaned=skirt.meters["cleaned"] >= THRESHOLD,
    )
    return world


PLACES = {
    "classroom": Place(
        id="classroom",
        label="the classroom",
        opening="Paper suns were drying by the window, and the room smelled faintly of glue and crayons.",
        activity="the children's collage table",
        tags={"school"},
    ),
    "community_hall": Place(
        id="community_hall",
        label="the community hall",
        opening="Folded chairs stood in neat rows, and a tray of snacks waited on a side table.",
        activity="the after-school craft shelf",
        tags={"community"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        opening="A bowl, a spoon, and a stack of napkins sat on the counter, ready for a simple treat.",
        activity="a plate of cut fruit and bread",
        tags={"home"},
    ),
}

SPILLS = {
    "jam": Spill(
        id="jam",
        label="strawberry jam",
        color="red",
        vivid=True,
        harmless=True,
        source_line="{adult} had just set down a cracker when a little spoonful of strawberry jam tipped from the plate and landed on {skirt}.",
        clue_line='"Oh goodness," {adult} said, "that is only strawberry jam from the snack tray."',
        cleanup="{adult} dabbed {skirt} with a wet cloth until the sticky red shine faded.",
        mistaken_for="a cut",
        tags={"jam", "red", "cleanup"},
    ),
    "paint": Spill(
        id="paint",
        label="poster paint",
        color="purple",
        vivid=True,
        harmless=True,
        source_line="A child at the table bumped a cup of purple poster paint, and one bright splash flicked onto {skirt}.",
        clue_line='{adult} smiled gently. "It is only poster paint, {child}, not anything scary."',
        cleanup="{adult} rinsed the spot with cool water and laughed when the purple streak thinned to a pale blur.",
        mistaken_for="a bruise or something hurtful",
        tags={"paint", "purple", "cleanup"},
    ),
    "sauce": Spill(
        id="sauce",
        label="tomato sauce",
        color="red",
        vivid=True,
        harmless=True,
        source_line="While carrying a little bowl, {adult} turned too fast, and a drop of tomato sauce skipped off the spoon and onto {skirt}.",
        clue_line='{adult} looked at the spoon and said, "Ah, tomato sauce. That explains the red spot."',
        cleanup="{adult} blotted {skirt} with a napkin and promised to wash it properly at home.",
        mistaken_for="blood",
        tags={"sauce", "red", "cleanup"},
    ),
    "mud": Spill(
        id="mud",
        label="mud",
        color="brown",
        vivid=False,
        harmless=True,
        source_line="A muddy shoe brushed the hem of {skirt} and left a dull brown smear there.",
        clue_line='{adult} brushed the hem and said, "Just a little mud from the floor."',
        cleanup="{adult} wiped the hem with a damp towel.",
        mistaken_for="something frightening",
        tags={"mud", "brown", "cleanup"},
    ),
}

SKIRTS = {
    "yellow_school": SkirtCfg(
        id="yellow_school",
        phrase="a pale yellow skirt",
        color="yellow",
        light=True,
        tags={"light_skirt"},
    ),
    "white_picnic": SkirtCfg(
        id="white_picnic",
        phrase="a white cotton skirt",
        color="white",
        light=True,
        tags={"light_skirt"},
    ),
    "navy_pleated": SkirtCfg(
        id="navy_pleated",
        phrase="a navy pleated skirt",
        color="navy",
        light=False,
        tags={"dark_skirt"},
    ),
}

STYLES = {
    "gentle": SpeakerStyle(
        id="gentle",
        line="Excuse me... I might be mistaken, but there is a red spot on your skirt, and I wanted to check if you are all right.",
        quality="gentle",
        brave=6,
        tags={"articulate", "bravery"},
    ),
    "plain": SpeakerStyle(
        id="plain",
        line="There is something on your skirt. I got scared, so I thought I should tell you.",
        quality="plain",
        brave=5,
        tags={"articulate", "bravery"},
    ),
    "mumbled": SpeakerStyle(
        id="mumbled",
        line="Um... your skirt...",
        quality="mumbled",
        brave=2,
        tags={"hesitant"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Ruby", "Tess", "Nora", "Ivy", "Sara", "June"]
BOY_NAMES = ["Owen", "Leo", "Milo", "Evan", "Theo", "Sam", "Noah", "Ben"]
ADULT_NAMES = ["Ms. Clara", "Ms. June", "Aunt Rosa", "Mom"]
TRAITS = ["careful", "thoughtful", "quiet", "kind", "observant"]


@dataclass
class StoryParams:
    place: str
    spill: str
    skirt: str
    style: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_type: str
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


KNOWLEDGE = {
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something means one thing, but it really means something else. It can feel big for a moment, and then a simple explanation can clear it up."
        )
    ],
    "bravery": [
        (
            "What can bravery look like in an ordinary day?",
            "Bravery does not always mean doing something loud or dangerous. Sometimes it means speaking up kindly when you are worried and telling the truth even if your voice shakes."
        )
    ],
    "articulate": [
        (
            "What does articulate mean?",
            "To articulate something means to put your thoughts into clear words. It helps other people understand what you are trying to say."
        )
    ],
    "skirt": [
        (
            "What is a skirt?",
            "A skirt is a piece of clothing that hangs down from the waist. Some skirts are light-colored, so spills show up on them very easily."
        )
    ],
    "jam": [
        (
            "Why does strawberry jam look so bright?",
            "Strawberry jam is made from red fruit, so it can leave a shiny red mark. On pale cloth, that mark can look much stronger than it really is."
        )
    ],
    "paint": [
        (
            "Why can paint splash on clothes so easily?",
            "Wet paint can flick or drip when a cup is bumped. That is why painters often use smocks or old clothes."
        )
    ],
    "sauce": [
        (
            "Why can tomato sauce be mistaken for something else?",
            "Tomato sauce is bright red, so from far away it can look alarming for a moment. Looking closely helps you understand what it really is."
        )
    ],
}


KNOWLEDGE_ORDER = ["misunderstanding", "bravery", "articulate", "skirt", "jam", "paint", "sauce"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    spill = f["spill_cfg"]
    skirt_cfg = f["skirt_cfg"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old where a child notices a stain on a grown-up\'s skirt and bravely speaks up.',
        f"Tell a gentle misunderstanding story set in {place.label} where {child.id} thinks a bright {spill.color} mark on {skirt_cfg.phrase} means something scary, but it turns out to be harmless.",
        f'Write a simple story that uses the words "skirt", "articulate", and "horrify", and shows that caring words can be brave.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    skirt = f["skirt"]
    spill = f["spill_cfg"]
    place = f["place"]
    style = f["style_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who notices something strange, and {adult.id}, who is wearing {skirt.label}. The story happens during an ordinary afternoon in {place.label}."
        ),
        (
            f"What did {child.id} see?",
            f"{child.id} saw a bright {spill.color} mark on {adult.id}'s skirt. Because it appeared suddenly on a light skirt, it looked much more alarming than it really was."
        ),
        (
            f"Why did the sight begin to horrify {child.id}?",
            f"{child.id} misunderstood the mark and feared it might mean {spill.mistaken_for}. That frightening guess came before {child.pronoun()} had enough information to know the truth."
        ),
        (
            f"How did {child.id} show bravery?",
            f"{child.id} did not keep the fear bottled up. {child.pronoun().capitalize()} walked over and tried to articulate the worry clearly by saying, \"{style.line}\""
        ),
        (
            "What was the misunderstanding?",
            f"The child thought the mark might mean something was wrong, but it was only {spill.label}. The misunderstanding ended as soon as {adult.id} looked closely and explained what had happened."
        ),
        (
            "How did the story end?",
            f"{adult.id} cleaned the skirt and thanked {child.id} for speaking up. The ending feels calm because the scary thought was wrong, but the brave kindness was still the right choice."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"misunderstanding", "bravery", "articulate", "skirt"}
    spill = world.facts["spill_cfg"]
    if spill.id == "jam":
        tags.add("jam")
    elif spill.id == "paint":
        tags.add("paint")
    elif spill.id == "sauce":
        tags.add("sauce")
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v is False}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="classroom",
        spill="jam",
        skirt="yellow_school",
        style="gentle",
        child_name="Mina",
        child_gender="girl",
        adult_name="Ms. Clara",
        adult_type="teacher",
        child_trait="observant",
        seed=1,
    ),
    StoryParams(
        place="community_hall",
        spill="paint",
        skirt="white_picnic",
        style="plain",
        child_name="Owen",
        child_gender="boy",
        adult_name="Ms. June",
        adult_type="teacher",
        child_trait="careful",
        seed=2,
    ),
    StoryParams(
        place="kitchen",
        spill="sauce",
        skirt="white_picnic",
        style="gentle",
        child_name="Ruby",
        child_gender="girl",
        adult_name="Mom",
        adult_type="mother",
        child_trait="kind",
        seed=3,
    ),
]


def explain_rejection(spill: Spill, skirt: SkirtCfg, style: SpeakerStyle) -> str:
    if not spill.vivid:
        return (
            f"(No story: {spill.label} is too dull-looking to support this misunderstanding. "
            f"The child would not honestly fear something alarming from that stain.)"
        )
    if not skirt.light:
        return (
            f"(No story: {skirt.phrase} is too dark for the bright mark to read clearly from across the room. "
            f"Use a light skirt so the misunderstanding is plausible.)"
        )
    if not brave_enough(style):
        return (
            f"(No story: the speaking style '{style.id}' is too weak for the bravery turn. "
            f"The child must speak clearly enough for the grown-up to check the problem.)"
        )
    return "(No story: this combination does not support the misunderstanding-and-bravery arc.)"


ASP_RULES = r"""
plausible_misread(Sp, Sk) :- spill(Sp), skirt(Sk), harmless(Sp), vivid(Sp), light_skirt(Sk).
brave_style(St) :- style(St), bravery(St, B), courage_min(M), B >= M.
valid(P, Sp, Sk, St) :- place(P), plausible_misread(Sp, Sk), brave_style(St).

outcome(clarified) :- chosen(Sp, Sk, St), plausible_misread(Sp, Sk), brave_style(St).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid, spill in SPILLS.items():
        lines.append(asp.fact("spill", sid))
        if spill.harmless:
            lines.append(asp.fact("harmless", sid))
        if spill.vivid:
            lines.append(asp.fact("vivid", sid))
    for kid, skirt in SKIRTS.items():
        lines.append(asp.fact("skirt", kid))
        if skirt.light:
            lines.append(asp.fact("light_skirt", kid))
    for stid, style in STYLES.items():
        lines.append(asp.fact("style", stid))
        lines.append(asp.fact("bravery", stid, style.brave))
    lines.append(asp.fact("courage_min", COURAGE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen", params.spill, params.skirt, params.style),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    spill = SPILLS[params.spill]
    skirt = SKIRTS[params.skirt]
    style = STYLES[params.style]
    if plausible_misunderstanding(spill, skirt) and brave_enough(style):
        return "clarified"
    return "?"


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
    for s in range(50):
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
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child notices a stain on a skirt, misunderstands it, and bravely speaks up."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--spill", choices=SPILLS)
    ap.add_argument("--skirt", choices=SKIRTS)
    ap.add_argument("--style", choices=STYLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--adult-name")
    ap.add_argument("--adult-type", choices=["teacher", "mother"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spill and args.skirt and args.style:
        spill = SPILLS[args.spill]
        skirt = SKIRTS[args.skirt]
        style = STYLES[args.style]
        if not (plausible_misunderstanding(spill, skirt) and brave_enough(style)):
            raise StoryError(explain_rejection(spill, skirt, style))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.spill is None or combo[1] == args.spill)
        and (args.skirt is None or combo[2] == args.skirt)
        and (args.style is None or combo[3] == args.style)
    ]
    if not combos:
        if args.spill and args.skirt and args.style:
            raise StoryError(explain_rejection(SPILLS[args.spill], SKIRTS[args.skirt], STYLES[args.style]))
        raise StoryError("(No valid combination matches the given options.)")

    place, spill, skirt, style = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult_type = args.adult_type or rng.choice(["teacher", "mother"])
    if adult_type == "mother":
        adult_name = args.adult_name or "Mom"
    else:
        teacher_names = [n for n in ADULT_NAMES if n != "Mom"]
        adult_name = args.adult_name or rng.choice(teacher_names)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        place=place,
        spill=spill,
        skirt=skirt,
        style=style,
        child_name=child_name,
        child_gender=gender,
        adult_name=adult_name,
        adult_type=adult_type,
        child_trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        spill = SPILLS[params.spill]
        skirt_cfg = SKIRTS[params.skirt]
        style = STYLES[params.style]
    except KeyError as err:
        raise StoryError(f"(Invalid params: unknown key {err.args[0]!r}.)") from None

    if not plausible_misunderstanding(spill, skirt_cfg):
        raise StoryError(explain_rejection(spill, skirt_cfg, style))
    if not brave_enough(style):
        raise StoryError(explain_rejection(spill, skirt_cfg, style))

    world = tell(
        place=place,
        spill=spill,
        skirt_cfg=skirt_cfg,
        style=style,
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_name=params.adult_name,
        adult_type=params.adult_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, spill, skirt, style) combos:\n")
        for place, spill, skirt, style in combos:
            print(f"  {place:14} {spill:8} {skirt:13} {style}")
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
            header = f"### {p.child_name}: {p.spill} on {p.skirt} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
