#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/augmentin_moral_value_surprise_sound_effects_bedtime.py
==================================================================================

A standalone storyworld about a child at bedtime who must take augmentin for an
infection. The world models a small, bedtime-scale conflict: the medicine tastes
bad, the child feels scared and tempted to hide that feeling, a surprising sound
briefly turns the room spooky, and a calm grown-up helps the child tell the truth,
take the medicine bravely, and settle to sleep.

The domain is intentionally narrow and state-driven:
- a child has an infection and discomfort,
- a doctor-prescribed dose of augmentin must be taken before sleep,
- some taking methods are age/form compatible and some are refused,
- a surprise sound may raise fear,
- honesty and help can turn the bedtime back toward rest.

Run it
------
    python storyworlds/worlds/gpt-5.4/augmentin_moral_value_surprise_sound_effects_bedtime.py
    python storyworlds/worlds/gpt-5.4/augmentin_moral_value_surprise_sound_effects_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/augmentin_moral_value_surprise_sound_effects_bedtime.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/augmentin_moral_value_surprise_sound_effects_bedtime.py --qa --json
    python storyworlds/worlds/gpt-5.4/augmentin_moral_value_surprise_sound_effects_bedtime.py --verify
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
TRUTH_MIN = 2


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Infection:
    id: str
    label: str
    symptom: str
    bedtime_line: str
    relief_line: str
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
class MedicineForm:
    id: str
    label: str
    phrase: str
    swallow_verb: str
    age_min: int
    bitter: int
    sound: str
    surprise_sound: str
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
class Method:
    id: str
    label: str
    works_for: set[str]
    comfort: int
    truth: int
    power: int
    setup: str
    dose_line: str
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
class Surprise:
    id: str
    label: str
    sound: str
    reveal: str
    harmless: bool = True
    fear: int = 1
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


def _r_pain_to_sleep(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child is None:
        return out
    if child.meters["pain"] >= THRESHOLD and child.meters["sleepy"] >= THRESHOLD:
        sig = ("restless", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["restless"] += 1
            out.append("__restless__")
    return out


def _r_fear_to_cling(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child is None:
        return out
    if child.memes["fear"] >= THRESHOLD:
        sig = ("cling", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["need_comfort"] += 1
            out.append("__cling__")
    return out


def _r_dose_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child is None:
        return out
    if child.meters["dose_taken"] >= THRESHOLD:
        sig = ("relief", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["pain"] = max(0.0, child.meters["pain"] - 1.0)
            child.memes["relief"] += 1
            child.memes["trust"] += 1
            out.append("__relief__")
    return out


def _r_honesty_to_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child is None:
        return out
    if child.memes["honesty"] >= THRESHOLD and child.memes["comforted"] >= THRESHOLD:
        sig = ("calm", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
            child.memes["bravery"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule(name="pain_to_sleep", tag="physical", apply=_r_pain_to_sleep),
    Rule(name="fear_to_cling", tag="emotional", apply=_r_fear_to_cling),
    Rule(name="dose_relief", tag="physical", apply=_r_dose_relief),
    Rule(name="honesty_to_calm", tag="social", apply=_r_honesty_to_calm),
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


def valid_method(form: MedicineForm, method: Method) -> bool:
    return form.id in method.works_for


def method_strength(method: Method) -> int:
    return method.power + method.comfort + method.truth


def can_finish_bedtime(method: Method, surprise: Surprise) -> bool:
    return method_strength(method) >= surprise.fear + TRUTH_MIN


def explain_method(form: MedicineForm, method: Method) -> str:
    return (
        f"(No story: {method.label} is not a reasonable way to give the {form.label} form here. "
        f"Pick a method that fits {form.label}.)"
    )


def predict_bedtime(world: World, method: Method, surprise: Surprise) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["fear"] += float(surprise.fear)
    if method.truth >= TRUTH_MIN:
        child.memes["honesty"] += 1
    child.memes["comforted"] += float(method.comfort)
    if can_finish_bedtime(method, surprise):
        child.meters["dose_taken"] += 1
    propagate(sim, narrate=False)
    return {
        "finished": child.meters["dose_taken"] >= THRESHOLD,
        "fear": child.memes["fear"],
        "relief": child.memes["relief"],
    }


def bedtime_setup(world: World, child: Entity, parent: Entity, infection: Infection, form: MedicineForm) -> None:
    child.meters["sleepy"] += 1
    child.meters["pain"] += 1
    child.memes["trust"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Moonlight laid a pale stripe across {child.id}'s blanket, and the house had almost settled into hush. "
        f"But {child.id} was still awake because {infection.bedtime_line}."
    )
    world.say(
        f"On the little table beside the bed stood {form.phrase} of augmentin, waiting for bedtime."
    )
    world.say(
        f'{parent.label_word.capitalize()} sat on the edge of the bed and rubbed {child.pronoun("possessive")} back. '
        f'"This medicine is here to help your {infection.label}," {parent.pronoun()} said.'
    )


def dislike(world: World, child: Entity, form: MedicineForm) -> None:
    child.memes["worry"] += 1
    child.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} looked at the bottle and made a tiny face. "{form.label.capitalize()} tastes bad," '
        f'{child.pronoun()} whispered.'
    )


def surprise_beat(world: World, child: Entity, surprise: Surprise) -> None:
    child.memes["fear"] += float(surprise.fear)
    propagate(world, narrate=False)
    world.say(
        f"Just then came a sudden sound from the room: {surprise.sound}! {child.id} gave a jump and pulled the blanket to {child.pronoun('possessive')} chin."
    )


def truth_invitation(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f'"You do not have to pretend to be brave before you feel brave," {parent.label_word} said softly. '
        f'"You can tell me the true thing."'
    )


def tell_truth(world: World, child: Entity) -> None:
    child.memes["honesty"] += 1
    world.say(
        f'{child.id} took a breath. "I do want to get better," {child.pronoun()} said, '
        f'"but I feel scared of the taste and the surprise sound too."'
    )


def reveal_sound(world: World, parent: Entity, surprise: Surprise) -> None:
    world.say(
        f'{parent.label_word.capitalize()} listened, then smiled. "{surprise.reveal}," {parent.pronoun()} said.'
    )


def comfort_with_method(world: World, child: Entity, parent: Entity, method: Method) -> None:
    child.memes["comforted"] += float(method.comfort)
    if method.truth >= TRUTH_MIN:
        child.memes["honesty"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{parent.label_word.capitalize()} did not rush. {parent.pronoun().capitalize()} {method.setup}.'
    )


def take_dose(world: World, child: Entity, form: MedicineForm, method: Method, infection: Infection) -> None:
    child.meters["dose_taken"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{form.sound}! {child.id} {form.swallow_verb} the augmentin dose. {method.dose_line}"
    )
    world.say(
        f"Soon the hardest part was over, and {infection.relief_line}"
    )


def fail_to_take(world: World, child: Entity, parent: Entity, method: Method) -> None:
    child.memes["fear"] += 1
    child.memes["sadness"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} tried, but the fear still felt too big. The bedtime room went quiet again, '
        f'and even {method.label} was not enough just then.'
    )
    world.say(
        f'{parent.label_word.capitalize()} kept an arm around {child.pronoun("object")} and promised to stay close while they called the doctor\'s advice line for help.'
    )


def close_happy(world: World, child: Entity, parent: Entity, infection: Infection, surprise: Surprise) -> None:
    child.memes["sleep"] += 1
    child.memes["peace"] += 1
    world.say(
        f'After that, {surprise.label} no longer sounded spooky at all. It was only part of the house saying good night.'
    )
    world.say(
        f'{child.id} curled against the pillow while {parent.label_word} tucked the blanket smooth. '
        f'{infection.symptom.capitalize()} did not feel so sharp now, and honesty had made room for courage.'
    )
    world.say(
        f'In a little while, the room was full of small bedtime sounds again—tick-tick, hush, sigh—and {child.id} drifted toward sleep.'
    )


def close_unfinished(world: World, child: Entity, infection: Infection) -> None:
    world.say(
        f'{child.id} was still loved and still safe, but {infection.symptom} kept bedtime uncomfortable.'
    )
    world.say(
        "The lesson stayed the same: telling the truth about fear is the first brave step, even on a hard night."
    )


def tell(
    infection: Infection,
    form: MedicineForm,
    method: Method,
    surprise: Surprise,
    *,
    child_name: str = "Mina",
    child_gender: str = "girl",
    parent_type: str = "mother",
    age: int = 5,
    comfort_item: str = "soft rabbit",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            attrs={"age": age, "comfort_item": comfort_item},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
            attrs={},
        )
    )
    world.add(Entity(id="medicine", type="medicine", label="augmentin", attrs={"form": form.id}))
    world.facts["comfort_item"] = comfort_item

    bedtime_setup(world, child, parent, infection, form)
    dislike(world, child, form)

    world.para()
    surprise_beat(world, child, surprise)
    truth_invitation(world, child, parent)
    tell_truth(world, child)
    reveal_sound(world, parent, surprise)

    world.para()
    comfort_with_method(world, child, parent, method)

    finished = can_finish_bedtime(method, surprise)
    if finished:
        take_dose(world, child, form, method, infection)
        world.para()
        close_happy(world, child, parent, infection, surprise)
    else:
        fail_to_take(world, child, parent, method)
        world.para()
        close_unfinished(world, child, infection)

    outcome = "finished" if finished else "unfinished"
    world.facts.update(
        child=child,
        parent=parent,
        infection=infection,
        form=form,
        method=method,
        surprise=surprise,
        outcome=outcome,
        took_dose=child.meters["dose_taken"] >= THRESHOLD,
        bravery=child.memes["bravery"],
        honesty=child.memes["honesty"],
        comforted=child.memes["comforted"],
    )
    return world


INFECTIONS = {
    "ear": Infection(
        id="ear",
        label="ear infection",
        symptom="ear hurt",
        bedtime_line="one ear ached in a hot, fussy way every time the pillow touched it",
        relief_line="the tight, thumpy feeling in the sore ear began to ease",
        tags={"earache", "medicine"},
    ),
    "throat": Infection(
        id="throat",
        label="throat infection",
        symptom="throat hurt",
        bedtime_line="swallowing made the throat sting, so even sleepy yawns felt uncomfortable",
        relief_line="the scratchy sting in the throat began to settle down",
        tags={"throat", "medicine"},
    ),
    "sinus": Infection(
        id="sinus",
        label="sinus infection",
        symptom="head felt stuffy",
        bedtime_line="the head felt stuffy and heavy, as if a little cloud had settled behind the nose",
        relief_line="the heavy, stuffed-up feeling began to loosen",
        tags={"sinus", "medicine"},
    ),
}

FORMS = {
    "liquid": MedicineForm(
        id="liquid",
        label="liquid medicine",
        phrase="a little bottle",
        swallow_verb="swallowed",
        age_min=3,
        bitter=2,
        sound="glug",
        surprise_sound="clink",
        tags={"liquid", "augmentin"},
    ),
    "chewable": MedicineForm(
        id="chewable",
        label="chewable tablet",
        phrase="a small cup",
        swallow_verb="chewed and swallowed",
        age_min=6,
        bitter=1,
        sound="chomp",
        surprise_sound="tap",
        tags={"tablet", "augmentin"},
    ),
}

METHODS = {
    "tiny_sips": Method(
        id="tiny_sips",
        label="tiny sips of water between breaths",
        works_for={"liquid", "chewable"},
        comfort=1,
        truth=2,
        power=1,
        setup="set a cup of cool water nearby and said they could take it slowly, one brave swallow at a time",
        dose_line="A sip of water followed, then another, and the taste did not stay as long as feared.",
        qa_text="used cool water and slow breaths to help with the dose",
        tags={"water", "bravery"},
    ),
    "story_count": Method(
        id="story_count",
        label="a counting story and cuddle",
        works_for={"liquid", "chewable"},
        comfort=2,
        truth=2,
        power=1,
        setup="wrapped an arm around the small shoulders and counted soft story-stars together—one, two, three—before the dose",
        dose_line="The counting turned the hard moment into a smaller one.",
        qa_text="counted softly and stayed close through the dose",
        tags={"counting", "comfort"},
    ),
    "spoon_song": Method(
        id="spoon_song",
        label="a spoon song",
        works_for={"liquid"},
        comfort=1,
        truth=1,
        power=1,
        setup="sang a tiny spoon song to make the medicine moment quicker",
        dose_line="The song helped a little, but mostly it reminded the child not to swallow alone.",
        qa_text="used a little song during the spoonful",
        tags={"song", "comfort"},
    ),
    "crunch_pair": Method(
        id="crunch_pair",
        label="a cracker nibble after the chew",
        works_for={"chewable"},
        comfort=1,
        truth=2,
        power=1,
        setup="placed a plain cracker on the saucer, explaining that the chewable tablet could be followed by a small nibble",
        dose_line="The cracker changed the taste in the mouth and made the next breath easier.",
        qa_text="followed the chewable dose with a little cracker nibble",
        tags={"cracker", "comfort"},
    ),
}

SURPRISES = {
    "radiator": Surprise(
        id="radiator",
        label="the old radiator",
        sound="clang-clang",
        reveal="the old radiator was waking with heat, not a monster at all",
        harmless=True,
        fear=1,
        tags={"sound", "house"},
    ),
    "cat": Surprise(
        id="cat",
        label="the hallway cat",
        sound="thump... jingle",
        reveal="the family cat had bumped a toy mouse in the hall",
        harmless=True,
        fear=1,
        tags={"sound", "cat"},
    ),
    "branch": Surprise(
        id="branch",
        label="the tree branch",
        sound="scritch-scritch",
        reveal="a windy branch was brushing the window like a sleepy finger",
        harmless=True,
        fear=2,
        tags={"sound", "window"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Tessa", "Ruby", "June", "Ella"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Ben", "Finn", "Eli", "Sam", "Noah"]
COMFORT_ITEMS = ["soft rabbit", "little bear", "blue blanket", "plush fox"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for inf_id in INFECTIONS:
        for form_id, form in FORMS.items():
            for method_id, method in METHODS.items():
                if valid_method(form, method):
                    combos.append((inf_id, form_id, method_id))
    return combos


@dataclass
class StoryParams:
    infection: str
    form: str
    method: str
    surprise: str
    child_name: str
    child_gender: str
    parent: str
    age: int = 5
    comfort_item: str = "soft rabbit"
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
    "augmentin": [
        (
            "What is augmentin?",
            "Augmentin is a medicine a doctor may prescribe to fight certain bacterial infections. A child should take it only when a grown-up gives it the way the doctor told them to."
        )
    ],
    "medicine": [
        (
            "Why do some children need medicine at bedtime?",
            "Sometimes bedtime is when the next safe dose is due. Taking medicine on time can help the body start feeling better."
        )
    ],
    "earache": [
        (
            "Why can an ear infection hurt more at bedtime?",
            "At bedtime everything is quieter, so throbbing pain can feel bigger. Lying on the sore side can make the ear feel tender too."
        )
    ],
    "throat": [
        (
            "Why can a throat infection make swallowing hurt?",
            "A sore throat can be swollen and tender. When food or spit moves past it, that tender place can sting."
        )
    ],
    "sinus": [
        (
            "Why can a stuffy head feel heavy?",
            "When the nose and sinus spaces are swollen, they can feel full and tight. That pressure can make the head feel heavy."
        )
    ],
    "truth": [
        (
            "Why is telling the truth about fear brave?",
            "Telling the truth helps a grown-up know how to help. Brave does not always mean not being scared; it can mean speaking honestly while scared."
        )
    ],
    "sound": [
        (
            "Why do little sounds seem bigger at night?",
            "Night is quieter, so clinks and scratches stand out more. A sound that feels spooky can turn out to be something ordinary."
        )
    ],
    "water": [
        (
            "Why can a sip of water help after medicine?",
            "A sip of water can wash away some of the taste left in the mouth. That can make the next breath feel easier."
        )
    ],
    "counting": [
        (
            "Why does counting help when something feels hard?",
            "Counting gives your mind one small step at a time. That can make a hard moment feel shorter and steadier."
        )
    ],
    "comfort": [
        (
            "How can a cuddle help at bedtime?",
            "A cuddle can make a child feel safe and less alone. Feeling safe often makes it easier to do something difficult."
        )
    ],
}
KNOWLEDGE_ORDER = ["augmentin", "medicine", "earache", "throat", "sinus", "truth", "sound", "water", "counting", "comfort"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    infection = f["infection"]
    method = f["method"]
    surprise = f["surprise"]
    outcome = f["outcome"]
    base = (
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "augmentin", '
        f'a surprising sound, and a gentle moral about honesty and bravery.'
    )
    if outcome == "finished":
        return [
            base,
            f"Tell a cozy night story where {child.id} feels nervous about augmentin for an {infection.label}, "
            f"hears {surprise.sound}, tells the truth about being scared, and is helped with {method.label}.",
            f"Write a soft bedtime tale where a child learns that saying the true thing can make room for courage, "
            f"and ends by settling peacefully to sleep after medicine.",
        ]
    return [
        base,
        f"Tell a bedtime story where {child.id} is frightened by {surprise.sound} and still cannot finish the augmentin dose that night, "
        f"but learns that telling the truth about fear is still brave.",
        "Write a gentle story where the hardest part is not solved quickly, yet the moral still teaches honesty, comfort, and asking for help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    infection = f["infection"]
    form = f["form"]
    method = f["method"]
    surprise = f["surprise"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who needed augmentin at bedtime, and {child.pronoun('possessive')} {pw} who stayed close to help."
        ),
        (
            "Why was bedtime hard for the child?",
            f"Bedtime was hard because {infection.bedtime_line}. That discomfort made the medicine feel like one more hard thing to face."
        ),
        (
            "What surprising thing happened?",
            f"The room suddenly filled with {surprise.sound}, which made {child.id} jump. Later they learned that {surprise.reveal}, so the sound was harmless after all."
        ),
        (
            "What was the true thing the child said?",
            f'{child.id} admitted being scared of the taste and the surprise sound. That honesty mattered because it let {pw} help with the real problem instead of guessing.'
        ),
    ]
    if f["outcome"] == "finished":
        qa.append(
            (
                f"How did {child.id}'s {pw} help with the augmentin?",
                f"{pw.capitalize()} {method.qa_text}. Staying calm and close turned the dose into something {child.id} could finish."
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                f"The story teaches that telling the truth about fear is a brave thing to do. Once {child.id} spoke honestly, comfort and courage could work together."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"{child.id} took the augmentin and began to settle down. The bedtime sounds felt gentle again, which showed the room had turned peaceful."
            )
        )
    else:
        qa.append(
            (
                "Did the child take the medicine that night?",
                f"No, not yet. The fear still felt too big, so {pw} stayed close and asked for more help instead of forcing the moment."
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                f"The moral is that honesty still matters even when a problem is not fixed right away. Telling the truth is the first brave step toward getting help."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"augmentin", "medicine", "truth", "sound"}
    infection = f["infection"]
    method = f["method"]
    if infection.id == "ear":
        tags.add("earache")
    elif infection.id == "throat":
        tags.add("throat")
    elif infection.id == "sinus":
        tags.add("sinus")
    if "water" in method.tags:
        tags.add("water")
    if "counting" in method.tags:
        tags.add("counting")
    if "comfort" in method.tags or method.comfort > 0:
        tags.add("comfort")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:9} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        infection="ear",
        form="liquid",
        method="story_count",
        surprise="radiator",
        child_name="Mina",
        child_gender="girl",
        parent="mother",
        age=5,
        comfort_item="soft rabbit",
    ),
    StoryParams(
        infection="throat",
        form="liquid",
        method="tiny_sips",
        surprise="cat",
        child_name="Owen",
        child_gender="boy",
        parent="father",
        age=4,
        comfort_item="blue blanket",
    ),
    StoryParams(
        infection="sinus",
        form="chewable",
        method="crunch_pair",
        surprise="branch",
        child_name="Theo",
        child_gender="boy",
        parent="mother",
        age=7,
        comfort_item="little bear",
    ),
    StoryParams(
        infection="ear",
        form="liquid",
        method="spoon_song",
        surprise="branch",
        child_name="Ruby",
        child_gender="girl",
        parent="mother",
        age=3,
        comfort_item="plush fox",
    ),
]


def explain_age(form: MedicineForm, age: int) -> str:
    return (
        f"(No story: {form.label} is only used here for ages {form.age_min}+; age {age} is too young for that choice.)"
    )


def outcome_of(params: StoryParams) -> str:
    form = FORMS[params.form]
    method = METHODS[params.method]
    surprise = SURPRISES[params.surprise]
    if params.age < form.age_min:
        return "invalid"
    if not valid_method(form, method):
        return "invalid"
    return "finished" if can_finish_bedtime(method, surprise) else "unfinished"


ASP_RULES = r"""
valid_combo(I, F, M) :- infection(I), form(F), method(M), works_for(M, F).

age_ok :- chosen_age(A), chosen_form(F), age_min(F, Min), A >= Min.
strength(S) :- chosen_method(M), power(M, P), comfort(M, C), truth(M, T), S = P + C + T.
finished :- age_ok, chosen_surprise(Su), fear(Su, F), strength(St), truth_min(Tm), St >= F + Tm.
outcome(finished) :- finished.
outcome(unfinished) :- age_ok, not finished.
outcome(invalid) :- not age_ok.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for inf_id in INFECTIONS:
        lines.append(asp.fact("infection", inf_id))
    for form_id, form in FORMS.items():
        lines.append(asp.fact("form", form_id))
        lines.append(asp.fact("age_min", form_id, form.age_min))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("power", method_id, method.power))
        lines.append(asp.fact("comfort", method_id, method.comfort))
        lines.append(asp.fact("truth", method_id, method.truth))
        for form_id in sorted(method.works_for):
            lines.append(asp.fact("works_for", method_id, form_id))
    for sid, surprise in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("fear", sid, surprise.fear))
    lines.append(asp.fact("truth_min", TRUTH_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join(
        [
            asp.fact("chosen_form", params.form),
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_surprise", params.surprise),
            asp.fact("chosen_age", params.age),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
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
        smoke = generate(CURATED[0])
        emit(smoke)
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: bedtime augmentin, a surprise sound, and a gentle lesson about honesty."
    )
    ap.add_argument("--infection", choices=INFECTIONS)
    ap.add_argument("--form", choices=FORMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--age", type=int, choices=[3, 4, 5, 6, 7])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (infection, form, method) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.form and args.age is not None:
        form = FORMS[args.form]
        if args.age < form.age_min:
            raise StoryError(explain_age(form, args.age))
    if args.form and args.method:
        form = FORMS[args.form]
        method = METHODS[args.method]
        if not valid_method(form, method):
            raise StoryError(explain_method(form, method))

    combos = [
        c for c in valid_combos()
        if (args.infection is None or c[0] == args.infection)
        and (args.form is None or c[1] == args.form)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    infection, form_id, method_id = rng.choice(sorted(combos))
    form = FORMS[form_id]

    age_choices = [a for a in [3, 4, 5, 6, 7] if a >= form.age_min]
    if args.age is not None:
        if args.age < form.age_min:
            raise StoryError(explain_age(form, args.age))
        age = args.age
    else:
        age = rng.choice(age_choices)

    gender = args.child_gender or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    comfort_item = rng.choice(COMFORT_ITEMS)

    return StoryParams(
        infection=infection,
        form=form_id,
        method=method_id,
        surprise=surprise,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
        age=age,
        comfort_item=comfort_item,
    )


def generate(params: StoryParams) -> StorySample:
    if params.infection not in INFECTIONS:
        raise StoryError(f"(Unknown infection: {params.infection})")
    if params.form not in FORMS:
        raise StoryError(f"(Unknown form: {params.form})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise: {params.surprise})")

    infection = INFECTIONS[params.infection]
    form = FORMS[params.form]
    method = METHODS[params.method]
    surprise = SURPRISES[params.surprise]

    if params.age < form.age_min:
        raise StoryError(explain_age(form, params.age))
    if not valid_method(form, method):
        raise StoryError(explain_method(form, method))

    world = tell(
        infection=infection,
        form=form,
        method=method,
        surprise=surprise,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        age=params.age,
        comfort_item=params.comfort_item,
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
        print(asp_program("", "#show valid_combo/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (infection, form, method) combos:\n")
        for infection, form, method in combos:
            print(f"  {infection:8} {form:9} {method}")
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
                f"### {p.child_name}: {p.infection}, {p.form}, {p.method}, "
                f"{p.surprise} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
