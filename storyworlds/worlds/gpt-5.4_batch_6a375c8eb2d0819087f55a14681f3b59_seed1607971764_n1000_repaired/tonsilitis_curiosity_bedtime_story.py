#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tonsilitis_curiosity_bedtime_story.py
================================================================

A standalone story world for a gentle bedtime tale about a curious child with a
sore throat. The child wants to understand the hurting feeling instead of simply
being told to sleep. A calm grown-up checks what is happening, chooses a sensible
comfort step, and either settles the child at home or takes them to a night
clinic if the signs are too strong.

The domain keeps one explicit seed word, "tonsilitis", in the story text. The
world model treats curiosity as a real force in the scene: the child's questions
change what they look at, what gets explained, and how the bedtime ending feels.

Run it
------
    python storyworlds/worlds/gpt-5.4/tonsilitis_curiosity_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/tonsilitis_curiosity_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/tonsilitis_curiosity_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tonsilitis_curiosity_bedtime_story.py --trace --seed 12
    python storyworlds/worlds/gpt-5.4/tonsilitis_curiosity_bedtime_story.py --json
    python storyworlds/worlds/gpt-5.4/tonsilitis_curiosity_bedtime_story.py --asp
    python storyworlds/worlds/gpt-5.4/tonsilitis_curiosity_bedtime_story.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
            "grandmother": "grandma",
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
class Setting:
    id: str
    room: str
    window_image: str
    hush: str
    lamp: str
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
class Symptom:
    id: str
    throat_severity: int
    fever_risk: int
    opening: str
    swallow_line: str
    look: str
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
class Wonder:
    id: str
    object_label: str
    question: str
    action: str
    discovery: str
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
class Remedy:
    id: str
    sense: int
    power: int
    mode: str
    offer: str
    comfort: str
    clinic_line: str
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


def _r_sore_swallow(world: World) -> list[str]:
    out: list[str] = []
    throat = world.get("throat")
    child = world.get("child")
    if throat.meters["soreness"] >= THRESHOLD:
        sig = ("swallow_hurts",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["swallowing_hard"] += 1
            child.memes["unease"] += 1
            out.append("__swallow__")
    return out


def _r_fever_concern(world: World) -> list[str]:
    out: list[str] = []
    throat = world.get("throat")
    parent = world.get("parent")
    if throat.meters["fever"] >= THRESHOLD:
        sig = ("fever_concern",)
        if sig not in world.fired:
            world.fired.add(sig)
            parent.memes["concern"] += 1
            out.append("__concern__")
    return out


def _r_curiosity_steadies(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["curiosity"] >= THRESHOLD:
        sig = ("curiosity_steadies",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["bravery"] += 1
            out.append("__curious__")
    return out


def _r_remedy_comfort(world: World) -> list[str]:
    out: list[str] = []
    throat = world.get("throat")
    child = world.get("child")
    if throat.meters["soothed"] >= THRESHOLD:
        sig = ("comfort",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["calm"] += 1
            child.memes["fear"] = 0.0
            out.append("__comfort__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="sore_swallow", tag="physical", apply=_r_sore_swallow),
    Rule(name="fever_concern", tag="physical", apply=_r_fever_concern),
    Rule(name="curiosity_steadies", tag="emotional", apply=_r_curiosity_steadies),
    Rule(name="remedy_comfort", tag="emotional", apply=_r_remedy_comfort),
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


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def symptom_load(symptom: Symptom, fever: int) -> int:
    return symptom.throat_severity + fever + symptom.fever_risk


def is_home_enough(remedy: Remedy, symptom: Symptom, fever: int) -> bool:
    return remedy.power >= symptom_load(symptom, fever)


def valid_combo(setting_id: str, symptom_id: str, wonder_id: str, remedy_id: str) -> bool:
    return (
        setting_id in SETTINGS
        and symptom_id in SYMPTOMS
        and wonder_id in WONDERS
        and remedy_id in REMEDIES
        and REMEDIES[remedy_id].sense >= SENSE_MIN
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for setting_id in SETTINGS:
        for symptom_id in SYMPTOMS:
            for wonder_id in WONDERS:
                for remedy_id, remedy in REMEDIES.items():
                    if remedy.sense >= SENSE_MIN:
                        out.append((setting_id, symptom_id, wonder_id, remedy_id))
    return out


def predict_night(world: World, remedy: Remedy) -> dict:
    sim = world.copy()
    throat = sim.get("throat")
    symptom = sim.facts["symptom_cfg"]
    fever = sim.facts["fever_level"]
    throat.meters["soothed"] += 1
    propagate(sim, narrate=False)
    return {
        "home_enough": is_home_enough(remedy, symptom, fever),
        "load": symptom_load(symptom, fever),
    }


def introduce(world: World, child: Entity, setting: Setting) -> None:
    world.say(
        f"In {setting.room}, {child.id} lay under the blanket while {setting.window_image}. "
        f"{setting.hush} {setting.lamp}"
    )


def bedtime_stir(world: World, child: Entity, symptom: Symptom) -> None:
    child.memes["sleepiness"] += 1
    world.say(
        f"It should have been an easy bedtime, but {symptom.opening} "
        f"{child.id} swallowed and made a small face."
    )


def wonder_start(world: World, child: Entity, wonder: Wonder) -> None:
    child.memes["curiosity"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"{wonder.question}" {child.id} whispered. Curiosity was still shining in '
        f"{child.pronoun('possessive')} eyes, even though {child.pronoun()} felt poorly."
    )


def parent_arrives(world: World, parent: Entity, child: Entity) -> None:
    parent.memes["care"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came to the bedside and smoothed the hair back from "
        f"{child.id}'s forehead."
    )


def check_throat(world: World, parent: Entity, child: Entity, wonder: Wonder, symptom: Symptom) -> None:
    throat = world.get("throat")
    throat.meters["soreness"] = float(symptom.throat_severity)
    throat.meters["fever"] = float(world.facts["fever_level"])
    child.memes["fear"] += 1
    world.say(
        f'Together they used {wonder.object_label} as {wonder.action}. '
        f'{wonder.discovery} {symptom.look}.'
    )
    propagate(world, narrate=False)


def explain(world: World, parent: Entity, child: Entity, symptom: Symptom) -> None:
    predicted = predict_night(world, world.facts["remedy_cfg"])
    world.facts["predicted_load"] = predicted["load"]
    throat = world.get("throat")
    fever = throat.meters["fever"]
    extra = ""
    if fever >= 2:
        extra = " The warm forehead made the grown-up listen even more carefully."
    world.say(
        f'"Your throat looks sore," {parent.label_word} said softly. '
        f'"Those little pads in the back are called tonsils, and tonight they seem puffy."'
        f"{extra}"
    )
    world.say(
        f'{child.id} listened hard. "{symptom.swallow_line}" '
        f'"Yes," said {parent.label_word}, "and that big word the nurse might use is tonsilitis."'
    )


def choose_remedy(world: World, parent: Entity, child: Entity, remedy: Remedy) -> None:
    throat = world.get("throat")
    child.memes["trust"] += 1
    throat.meters["soothed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{parent.label_word.capitalize()} did not rush. "{remedy.offer}" '
        f'{parent.pronoun().capitalize()} said, and {child.id} nodded.'
    )


def settle_home(world: World, parent: Entity, child: Entity, remedy: Remedy, wonder: Wonder) -> None:
    child.memes["sleepiness"] += 1
    child.memes["relief"] += 1
    child.memes["curiosity"] += 1
    world.say(remedy.comfort)
    world.say(
        f"After that, {child.id} asked one more quiet question about the two tonsils, and "
        f"{parent.label_word} answered it in a voice as low as the room. "
        f"Soon the question could wait for morning."
    )
    world.say(
        f"{child.id} tucked {wonder.object_label} beside the pillow, breathed more easily, "
        f"and drifted off while {world.setting.window_image.lower()}."
    )


def night_clinic(world: World, parent: Entity, child: Entity, remedy: Remedy, wonder: Wonder) -> None:
    child.memes["fear"] += 1
    parent.memes["concern"] += 1
    world.say(remedy.clinic_line)
    world.say(
        f"So {parent.label_word} wrapped {child.id} in a blanket and carried "
        f"{child.pronoun('object')} through the dark, with {wonder.object_label} tucked in one hand."
    )
    world.say(
        "At the little night clinic, a gentle doctor looked in with a light, agreed it could be "
        'tonsilitis, and helped them make a plan for rest and medicine.'
    )
    world.say(
        f"On the way home, the car hummed like a lullaby. {child.id} fell asleep against "
        f"{parent.pronoun('possessive')} shoulder, holding the new answer close."
    )


def tell(
    setting: Setting,
    symptom: Symptom,
    wonder: Wonder,
    remedy: Remedy,
    *,
    child_name: str = "Mina",
    child_type: str = "girl",
    parent_type: str = "mother",
    fever: int = 1,
    blanket: str = "patchwork quilt",
    plush: str = "small rabbit",
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            role="child",
            traits=["curious", "sleepy"],
            attrs={"blanket": blanket, "plush": plush},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    throat = world.add(
        Entity(
            id="throat",
            kind="thing",
            type="throat",
            label="throat",
            role="body",
        )
    )

    world.facts.update(
        child=child,
        parent=parent,
        throat=throat,
        setting_cfg=setting,
        symptom_cfg=symptom,
        wonder_cfg=wonder,
        remedy_cfg=remedy,
        fever_level=fever,
        blanket=blanket,
        plush=plush,
    )

    introduce(world, child, setting)
    bedtime_stir(world, child, symptom)

    world.para()
    wonder_start(world, child, wonder)
    parent_arrives(world, parent, child)
    check_throat(world, parent, child, wonder, symptom)
    explain(world, parent, child, symptom)

    world.para()
    choose_remedy(world, parent, child, remedy)
    at_home = is_home_enough(remedy, symptom, fever)
    if at_home:
        settle_home(world, parent, child, remedy, wonder)
        outcome = "home_rest"
    else:
        night_clinic(world, parent, child, remedy, wonder)
        outcome = "clinic"

    world.facts.update(
        outcome=outcome,
        load=symptom_load(symptom, fever),
        at_home=at_home,
        promised_rest=True,
    )
    return world


SETTINGS = {
    "moon_room": Setting(
        id="moon_room",
        room="a quiet moonlit bedroom",
        window_image="a round moon rested above the curtains",
        hush="The floorboards held still, and even the toy basket seemed sleepy.",
        lamp="A tiny lamp made a golden puddle on the nightstand.",
        tags={"bedroom", "moon"},
    ),
    "rain_room": Setting(
        id="rain_room",
        room="a cozy bedroom while rain tapped outside",
        window_image="rain slid down the window in silver lines",
        hush="The house sounded tucked in and safe.",
        lamp="A bedside lamp glowed like a sleepy peach.",
        tags={"bedroom", "rain"},
    ),
    "attic_nook": Setting(
        id="attic_nook",
        room="a small attic room under the roof",
        window_image="the stars peeped through the little window",
        hush="The roof creaked softly, like an old cat settling down.",
        lamp="A reading lamp made the slanted ceiling warm and bright.",
        tags={"attic", "stars"},
    ),
}

SYMPTOMS = {
    "scratchy": Symptom(
        id="scratchy",
        throat_severity=1,
        fever_risk=0,
        opening="A scratchy sting lived in the back of the throat, so when",
        swallow_line="Why does swallowing feel prickly?",
        look="It was only a little red, but red all the same.",
        tags={"sore_throat"},
    ),
    "swollen": Symptom(
        id="swollen",
        throat_severity=2,
        fever_risk=1,
        opening="A thick sore ache sat in the throat, and each time",
        swallow_line="Why does it feel big in there?",
        look="The skin looked red and puffy, with two swollen bumps at the back.",
        tags={"sore_throat", "tonsils"},
    ),
    "hot": Symptom(
        id="hot",
        throat_severity=2,
        fever_risk=2,
        opening="The throat felt sore and hot, so when",
        swallow_line="Why does my throat hurt and my head feel warm too?",
        look="The throat looked angry-red, and the face above it was warm and tired.",
        tags={"sore_throat", "fever"},
    ),
}

WONDERS = {
    "mirror": Wonder(
        id="mirror",
        object_label="a small round mirror",
        question="Can I see the place that hurts?",
        action="a lookout glass for the tiny sore place",
        discovery="The mirror caught a pink little cavern inside the mouth.",
        tags={"mirror", "curiosity"},
    ),
    "flashlight": Wonder(
        id="flashlight",
        object_label="a tiny flashlight",
        question="What is hiding in my throat?",
        action="a careful beam to peek where bedtime shadows could not",
        discovery="The little light showed every shiny curve at the back of the mouth.",
        tags={"flashlight", "curiosity"},
    ),
    "picture_book": Wonder(
        id="picture_book",
        object_label="a body-picture book",
        question="What do tonsils do anyway?",
        action="a map while they compared the picture to the real throat",
        discovery="The page made the strange place feel less secret.",
        tags={"book", "curiosity"},
    ),
}

REMEDIES = {
    "honey_tea": Remedy(
        id="honey_tea",
        sense=3,
        power=3,
        mode="warm",
        offer="Let's sip warm honey tea, take your medicine, and let your throat rest",
        comfort="The warm tea slid down gently, and the medicine began to take the sharp edge away.",
        clinic_line="They tried warm honey tea and medicine first, but the heat in the little body still worried the grown-up.",
        qa_text="gave warm honey tea and medicine",
        tags={"tea", "medicine", "rest"},
    ),
    "ice_pop": Remedy(
        id="ice_pop",
        sense=2,
        power=2,
        mode="cool",
        offer="Let's try a cool ice pop, a sip of water, and very quiet breathing",
        comfort="The cold sweetness made the throat feel less fierce, and each breath came easier than the last.",
        clinic_line="They tried a cool ice pop and water, but the throat still looked too sore for the night to feel simple.",
        qa_text="gave a cool ice pop and water",
        tags={"ice_pop", "water", "rest"},
    ),
    "steam_and_medicine": Remedy(
        id="steam_and_medicine",
        sense=3,
        power=4,
        mode="steam",
        offer="Let's sit in the steamy bathroom for a minute, sip water, and have your night medicine",
        comfort="The warm steam softened the tight feeling, and the medicine helped the child stop wincing at each swallow.",
        clinic_line="They sat in the steam and used the night medicine, but the signs still seemed too strong to simply wait on.",
        qa_text="used steam, water, and night medicine",
        tags={"steam", "medicine", "rest"},
    ),
    "crackers": Remedy(
        id="crackers",
        sense=1,
        power=0,
        mode="rough",
        offer="Let's crunch a few dry crackers and hope your throat forgets",
        comfort="The crackers scratched all the way down, which was exactly the wrong kind of help.",
        clinic_line="Dry crackers only made the swallowing hurt more.",
        qa_text="offered dry crackers",
        tags={"food"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Tessa", "Ruby", "Anna", "Cora"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Eli", "Noah", "Leo", "Finn"]
BLANKETS = ["patchwork quilt", "soft blue blanket", "yellow star blanket", "warm striped quilt"]
PLUSHES = ["small rabbit", "little bear", "plush fox", "sleepy lamb"]


@dataclass
class StoryParams:
    setting: str
    symptom: str
    wonder: str
    remedy: str
    name: str
    gender: str
    parent: str
    fever: int = 1
    blanket: str = "patchwork quilt"
    plush: str = "small rabbit"
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "tonsils": [
        (
            "What are tonsils?",
            "Tonsils are two small pads at the back of your throat. They are part of your body and can get swollen when you are sick.",
        )
    ],
    "sore_throat": [
        (
            "Why can swallowing hurt when your throat is sore?",
            "When the skin in your throat is swollen or irritated, moving it can sting. That is why swallowing can feel sharp or scratchy.",
        )
    ],
    "fever": [
        (
            "What is a fever?",
            "A fever means your body is warmer than usual while it fights an illness. It is a sign that a grown-up should pay close attention.",
        )
    ],
    "mirror": [
        (
            "What does a mirror help you do?",
            "A mirror lets you see parts of yourself by bouncing light back at you. With a grown-up, it can help you peek at something hard to see.",
        )
    ],
    "flashlight": [
        (
            "Why does a flashlight help when you look in a mouth?",
            "A flashlight shines into dark places so you can see more clearly. It helps a grown-up notice whether a throat looks red or swollen.",
        )
    ],
    "book": [
        (
            "Why can a picture book help when you feel worried?",
            "A picture book can turn a mystery into something easier to understand. Knowing what a body part is can make it feel less scary.",
        )
    ],
    "tea": [
        (
            "Why can warm tea feel good on a sore throat?",
            "Warm drinks can feel gentle on irritated skin in the throat. They also help you stay hydrated while you rest.",
        )
    ],
    "ice_pop": [
        (
            "Why can a cool ice pop help a sore throat?",
            "Cold treats can numb a sore spot for a little while. That can make swallowing feel easier.",
        )
    ],
    "steam": [
        (
            "Why can steam feel soothing?",
            "Warm steam can make tight, dry breathing passages feel less harsh. It often feels gentler than dry air.",
        )
    ],
    "medicine": [
        (
            "Why do sick children need a grown-up for medicine?",
            "A grown-up chooses the right medicine and the right amount. Medicine is helpful only when it is given carefully.",
        )
    ],
    "rest": [
        (
            "Why is rest important when you are sick?",
            "Rest gives your body time and energy to fight the illness. Sleeping helps you heal while everything grows quiet.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "tonsils",
    "sore_throat",
    "fever",
    "mirror",
    "flashlight",
    "book",
    "tea",
    "ice_pop",
    "steam",
    "medicine",
    "rest",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    symptom = f["symptom_cfg"]
    wonder = f["wonder_cfg"]
    remedy = f["remedy_cfg"]
    if f["outcome"] == "clinic":
        return [
            'Write a bedtime story for a 3-to-5-year-old about a curious child with a sore throat and use the word "tonsilitis".',
            f"Tell a gentle night story where {child.id} keeps asking questions about a sore throat, a grown-up checks with {wonder.object_label}, and the family makes a calm trip to a night clinic.",
            f"Write a soft, reassuring story in which curiosity helps a child face {symptom.id} throat pain, even though bedtime changes because home care with {remedy.id.replace('_', ' ')} is not enough.",
        ]
    return [
        'Write a bedtime story for a 3-to-5-year-old about a curious child with a sore throat and use the word "tonsilitis".',
        f"Tell a gentle story where {child.id} asks what is happening in {child.pronoun('possessive')} throat, a grown-up checks with {wonder.object_label}, and bedtime ends peacefully at home.",
        f"Write a soothing bedtime story where curiosity turns a scary body feeling into something understandable, and {remedy.id.replace('_', ' ')} helps the child settle to sleep.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    symptom = f["symptom_cfg"]
    wonder = f["wonder_cfg"]
    remedy = f["remedy_cfg"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious child at bedtime, and {child.pronoun('possessive')} {pw} who came to help. The whole story happens while they try to understand why the throat hurts.",
        ),
        (
            f"Why was bedtime not easy for {child.id}?",
            f"Bedtime was hard because {child.id}'s throat felt sore when {child.pronoun()} swallowed. The hurting feeling kept tugging at {child.pronoun('possessive')} attention instead of letting sleep come.",
        ),
        (
            f"What question did {child.id} ask?",
            f"{child.id} asked, \"{wonder.question}\" The question matters because curiosity helped {child.pronoun('object')} look at the problem instead of only feeling afraid of it.",
        ),
        (
            f"How did {child.id}'s {pw} check what was wrong?",
            f"{pw.capitalize()} used {wonder.object_label} to look carefully at the sore throat. That helped them notice the redness and explain that the swollen pads were tonsils.",
        ),
        (
            "What did the grown-up say the big word might be?",
            'The grown-up said a nurse might call it "tonsilitis." The big word gave a name to the sore, puffy throat, which made the mystery smaller.',
        ),
    ]
    if f["outcome"] == "home_rest":
        qa.extend(
            [
                (
                    f"How did {child.id}'s {pw} help at home?",
                    f"{pw.capitalize()} {remedy.qa_text}. The comfort step soothed the throat enough for a quiet night at home.",
                ),
                (
                    "How did the story end?",
                    f"It ended with {child.id} calm and sleepy again. {child.pronoun().capitalize()} tucked {wonder.object_label} near the pillow and drifted off with an answer to hold onto until morning.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"Why did they go to the clinic instead of staying in bed?",
                    f"They tried a sensible comfort step first, but the sore throat and warmth still seemed too strong for the night. {child.id}'s {pw} wanted a doctor to check the signs instead of only waiting.",
                ),
                (
                    "How did the story end?",
                    f"It ended safely, not sadly. On the way home from the clinic, {child.id} fell asleep against {parent.pronoun('possessive')} shoulder because the mystery had been checked and a plan had been made.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["symptom_cfg"].tags) | set(f["wonder_cfg"].tags) | set(f["remedy_cfg"].tags)
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
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_room",
        symptom="scratchy",
        wonder="mirror",
        remedy="honey_tea",
        name="Mina",
        gender="girl",
        parent="mother",
        fever=0,
        blanket="yellow star blanket",
        plush="small rabbit",
    ),
    StoryParams(
        setting="rain_room",
        symptom="swollen",
        wonder="flashlight",
        remedy="ice_pop",
        name="Theo",
        gender="boy",
        parent="father",
        fever=1,
        blanket="soft blue blanket",
        plush="little bear",
    ),
    StoryParams(
        setting="attic_nook",
        symptom="hot",
        wonder="picture_book",
        remedy="ice_pop",
        name="Ruby",
        gender="girl",
        parent="mother",
        fever=2,
        blanket="patchwork quilt",
        plush="plush fox",
    ),
    StoryParams(
        setting="moon_room",
        symptom="swollen",
        wonder="picture_book",
        remedy="steam_and_medicine",
        name="Owen",
        gender="boy",
        parent="father",
        fever=1,
        blanket="warm striped quilt",
        plush="sleepy lamb",
    ),
]


def explain_rejection(remedy_id: str) -> str:
    remedy = REMEDIES[remedy_id]
    return (
        f"(Refusing remedy '{remedy_id}': it scores too low on common sense "
        f"(sense={remedy.sense} < {SENSE_MIN}). A sore throat at bedtime needs a soothing, "
        f"sensible response, not something rough like dry crackers.)"
    )


def outcome_of(params: StoryParams) -> str:
    return (
        "home_rest"
        if is_home_enough(REMEDIES[params.remedy], SYMPTOMS[params.symptom], params.fever)
        else "clinic"
    )


ASP_RULES = r"""
sensible(R) :- remedy(R), sense(R,S), sense_min(M), S >= M.
valid(Se, Sy, W, R) :- setting(Se), symptom(Sy), wonder(W), remedy(R), sensible(R).

load(S + F + K) :- chosen_symptom(Sy), throat_severity(Sy, S), chosen_fever(F), fever_risk(Sy, K).
power(P) :- chosen_remedy(R), remedy_power(R, P).

outcome(home_rest) :- power(P), load(L), P >= L.
outcome(clinic)    :- power(P), load(L), P < L.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for syid, symptom in SYMPTOMS.items():
        lines.append(asp.fact("symptom", syid))
        lines.append(asp.fact("throat_severity", syid, symptom.throat_severity))
        lines.append(asp.fact("fever_risk", syid, symptom.fever_risk))
    for wid in WONDERS:
        lines.append(asp.fact("wonder", wid))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, remedy.sense))
        lines.append(asp.fact("remedy_power", rid, remedy.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_symptom", params.symptom),
            asp.fact("chosen_remedy", params.remedy),
            asp.fact("chosen_fever", params.fever),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_remedies()}
    asp_sense = set(asp_sensible())
    if py_sensible == asp_sense:
        print(f"OK: sensible remedies match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(asp_sense)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story during smoke test")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a curious child, a sore throat, and a bedtime plan."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--symptom", choices=SYMPTOMS)
    ap.add_argument("--wonder", choices=WONDERS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--fever", type=int, choices=[0, 1, 2], help="how warm the child feels tonight")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.remedy and args.remedy in REMEDIES and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_rejection(args.remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.symptom is None or combo[1] == args.symptom)
        and (args.wonder is None or combo[2] == args.wonder)
        and (args.remedy is None or combo[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, symptom, wonder, remedy = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    fever = args.fever if args.fever is not None else rng.choice([0, 1, 2])
    blanket = rng.choice(BLANKETS)
    plush = rng.choice(PLUSHES)
    return StoryParams(
        setting=setting,
        symptom=symptom,
        wonder=wonder,
        remedy=remedy,
        name=name,
        gender=gender,
        parent=parent,
        fever=fever,
        blanket=blanket,
        plush=plush,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        symptom = SYMPTOMS[params.symptom]
        wonder = WONDERS[params.wonder]
        remedy = REMEDIES[params.remedy]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err})") from None

    if remedy.sense < SENSE_MIN:
        raise StoryError(explain_rejection(params.remedy))
    if params.gender not in {"girl", "boy"}:
        raise StoryError("(Gender must be 'girl' or 'boy'.)")
    if params.parent not in {"mother", "father"}:
        raise StoryError("(Parent must be 'mother' or 'father'.)")
    if params.fever not in {0, 1, 2}:
        raise StoryError("(Fever must be 0, 1, or 2.)")

    world = tell(
        setting=setting,
        symptom=symptom,
        wonder=wonder,
        remedy=remedy,
        child_name=params.name,
        child_type=params.gender,
        parent_type=params.parent,
        fever=params.fever,
        blanket=params.blanket,
        plush=params.plush,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, symptom, wonder, remedy) combos:\n")
        for setting, symptom, wonder, remedy in combos:
            print(f"  {setting:11} {symptom:8} {wonder:12} {remedy}")
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
                f"### {p.name}: {p.symptom} throat in {p.setting} "
                f"({p.wonder}, {p.remedy}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
