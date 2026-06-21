#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/basenji_cautionary_dialogue_lesson_learned_comedy.py
================================================================================

A standalone story world about a funny basenji, a tempting lunch, and a lesson
about safe ways to include a dog in a game. The stories are child-facing,
cautionary, dialogue-rich, and gently comic: a child gets a silly idea, another
child warns what might happen, the basenji either nearly causes a mess or does
cause one, and a grown-up teaches a better plan.

Run it
------
    python storyworlds/worlds/gpt-5.4/basenji_cautionary_dialogue_lesson_learned_comedy.py
    python storyworlds/worlds/gpt-5.4/basenji_cautionary_dialogue_lesson_learned_comedy.py --occasion picnic --lure sausage --perch chair
    python storyworlds/worlds/gpt-5.4/basenji_cautionary_dialogue_lesson_learned_comedy.py --perch stone_step
    python storyworlds/worlds/gpt-5.4/basenji_cautionary_dialogue_lesson_learned_comedy.py --all
    python storyworlds/worlds/gpt-5.4/basenji_cautionary_dialogue_lesson_learned_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/basenji_cautionary_dialogue_lesson_learned_comedy.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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
CAREFUL_TRAITS = {"careful", "patient", "sensible"}
IMPULSE_INIT = 5.0
SENSE_MIN = 2


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        dog = {"dog", "basenji"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in dog:
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
class Occasion:
    id: str
    scene: str
    setup: str
    food_line: str
    ending: str
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
class Lure:
    id: str
    label: str
    phrase: str
    smell: str
    warning: str
    plural: bool = False
    tempting: bool = True
    dog_safe: bool = False
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
class Perch:
    id: str
    label: str
    phrase: str
    wobble: int
    skid: str
    stable_reason: str
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
class Fix:
    id: str
    sense: int
    treat: str
    spot: str
    offer: str
    end_image: str
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
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_tip(world: World) -> list[str]:
    out: list[str] = []
    dog = world.get("dog")
    perch = world.get("perch")
    table = world.get("table")
    if dog.meters["on_perch"] < THRESHOLD:
        return out
    if perch.meters["wobble"] < THRESHOLD:
        return out
    sig = ("tip", dog.id, perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    perch.meters["tipped"] += 1
    table.meters["mess"] += 1
    dog.meters["startled"] += 1
    for kid in world.kids():
        kid.memes["surprise"] += 1
    out.append("__spill__")
    return out


def _r_smear(world: World) -> list[str]:
    out: list[str] = []
    table = world.get("table")
    dog = world.get("dog")
    if table.meters["mess"] < THRESHOLD:
        return out
    sig = ("smear", table.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dog.meters["sauce_on_nose"] += 1
    dog.memes["glee"] += 1
    out.append("__sauce__")
    return out


CAUSAL_RULES = [
    Rule(name="tip", tag="physical", apply=_r_tip),
    Rule(name="smear", tag="physical", apply=_r_smear),
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


def hazard_at_risk(lure: Lure, perch: Perch) -> bool:
    return lure.tempting and perch.wobble > 0


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if cautioner_older else 0.0)
    return cautioner_older and authority > IMPULSE_INIT


def predict_spill(world: World) -> dict:
    sim = world.copy()
    dog = sim.get("dog")
    dog.meters["on_perch"] += 1
    propagate(sim, narrate=False)
    return {
        "spill": sim.get("table").meters["mess"] >= THRESHOLD,
        "tipped": sim.get("perch").meters["tipped"] >= THRESHOLD,
    }


def play_setup(world: World, a: Entity, b: Entity, dog: Entity, occasion: Occasion) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    dog.memes["curiosity"] += 1
    world.say(
        f"One cheerful day, {a.id}, {b.id}, and their basenji, {dog.id}, were in {occasion.scene}. "
        f"{occasion.setup}"
    )
    world.say(
        f"{dog.id} trotted in neat little circles, tail curled tight as a cinnamon roll, "
        f"and made a tiny basenji roo-roo that sounded as if a toy trumpet had learned manners."
    )
    world.say(occasion.food_line)


def silly_idea(world: World, a: Entity, dog: Entity, lure: Lure, perch: Perch) -> None:
    a.memes["impulse"] += 1
    world.say(
        f'"I know how to make {dog.id} do a funny parade," {a.id} said. '
        f'"I can wiggle {lure.phrase} by {perch.phrase}, and {dog.id} will hop right up."'
    )


def warn(world: World, b: Entity, a: Entity, dog: Entity, lure: Lure, perch: Perch, parent: Entity) -> None:
    pred = predict_spill(world)
    world.facts["predicted_spill"] = pred["spill"]
    b.memes["caution"] += 1
    extra = ""
    if pred["spill"]:
        extra = f" {b.id} looked at {perch.phrase} and frowned. \"If {dog.id} jumps there, lunch could land everywhere.\""
    world.say(
        f'"Wait," said {b.id}. "{lure.warning} {dog.id} is fast, and {perch.phrase} looks wobbly. '
        f'We should ask {parent.label_word} for a dog game that happens on the floor."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, lure: Lure) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"It will be funny for one second," {a.id} said. "{b.id}, don\'t worry so much." '
        f"Then {a.pronoun()} pinched up {lure.phrase} and gave it a silly little wiggle."
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity, dog: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["impulse"] = 0.0
    world.say(
        f'{a.id} looked at the wobble, then at {dog.id}\'s bright eyes, and let out a puff of air. '
        f'"You\'re right," {a.pronoun()} said. "I want a laugh, not a disaster."'
    )
    world.say(
        f"They put their hands behind their backs and called for {parent.label_word}. "
        f"{dog.id} sat down with heroic confusion, as if he had been promised a show and received a math problem instead."
    )


def lure_jump(world: World, dog: Entity, lure: Lure, perch: Perch) -> None:
    dog.meters["on_perch"] += 1
    dog.memes["glee"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{dog.id}'s nose twitched at once. With one springy hop, the basenji leapt toward {perch.phrase}, "
        f"chasing the smell of {lure.label} as if it were the most important joke in the world."
    )
    if world.get("perch").meters["tipped"] >= THRESHOLD:
        world.say(
            f"{perch.phrase.capitalize()} went {perch.attrs['skid_word']}, the plates did a clattery dance, "
            f"and lunch slid across the table in one grand comic swoop."
        )


def alarm(world: World, a: Entity, b: Entity, parent: Entity, dog: Entity) -> None:
    if world.get("table").meters["mess"] >= THRESHOLD:
        world.say(f'"{parent.label_word.upper()}!" {b.id} yelped.')
        world.say(
            f'"I only wanted a tiny joke!" {a.id} cried, while {dog.id} stood very still with the innocent face of someone wearing sauce on his nose.'
        )


def adult_arrives(world: World, parent: Entity, dog: Entity) -> None:
    parent.memes["calm"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came over fast, took the tempting food away, and guided {dog.id} back to the floor before anything else could tumble."
    )


def clean_and_teach(world: World, parent: Entity, a: Entity, b: Entity, dog: Entity, fix: Fix, lure: Lure) -> None:
    world.get("table").meters["mess"] = 0.0
    world.get("perch").meters["tipped"] = 0.0
    dog.meters["on_perch"] = 0.0
    dog.meters["waiting"] += 1
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["embarrassment"] += 1
    world.say(
        f'"People food from the table is not a dog trick," {parent.label_word} said, wiping up the mess with brisk little swishes. '
        f'"If we tease {dog.id} toward chairs and plates, we teach him to jump where he should not jump."'
    )
    world.say(
        f'Then {parent.pronoun().capitalize()} held up {fix.treat} and tapped {fix.spot}. '
        f'"Watch this. {dog.id}, {fix.offer}."'
    )
    world.say(
        f"{dog.id} pranced to {fix.spot}, sat down, and stared so hard at the treat that even his ears seemed to be paying attention."
    )


def teach_after_nearmiss(world: World, parent: Entity, a: Entity, b: Entity, dog: Entity, fix: Fix) -> None:
    dog.meters["waiting"] += 1
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled when the children explained. "
        f'"Thank you for stopping before it became a mess," {parent.pronoun()} said. '
        f'"A basenji is clever and quick, so our rule is simple: dog games stay on the floor."'
    )
    world.say(
        f'Then {parent.pronoun()} showed them a better joke. Holding up {fix.treat}, '
        f'{parent.pronoun()} pointed to {fix.spot} and said, "{dog.id}, {fix.offer}."'
    )
    world.say(
        f"{dog.id} zipped to {fix.spot} and sat so straight that the children burst out laughing for the right reason."
    )


def ending(world: World, occasion: Occasion, a: Entity, b: Entity, dog: Entity, fix: Fix, averted: bool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    dog.memes["trust"] += 1
    if averted:
        start = "Soon"
    else:
        start = "A little later"
    world.say(
        f"{start}, {occasion.ending} {fix.end_image} {dog.id} waited on {fix.spot}, and the children laughed because the trick was tidy, not because lunch was flying."
    )
    world.say(
        f'"Floor first, food later," {a.id} said.'
    )
    world.say(
        f'"That is the whole lesson," {b.id} answered, and even {dog.id} gave a pleased little roo-roo, as if he agreed.'
    )


def tell(
    occasion: Occasion,
    lure: Lure,
    perch: Perch,
    fix: Fix,
    *,
    instigator: str = "Milo",
    instigator_gender: str = "boy",
    cautioner: str = "Nia",
    cautioner_gender: str = "girl",
    dog_name: str = "Pip",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    instigator_age: int = 6,
    cautioner_age: int = 7,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        traits=["funny"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    dog = world.add(Entity(
        id=dog_name,
        kind="character",
        type="basenji",
        role="dog",
        attrs={"breed": "basenji"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    perch_ent = world.add(Entity(
        id="perch",
        type="perch",
        label=perch.label,
        attrs={"skid_word": perch.skid},
    ))
    table = world.add(Entity(
        id="table",
        type="table",
        label="lunch table",
    ))
    perch_ent.meters["wobble"] = float(perch.wobble)
    a.memes["impulse"] = IMPULSE_INIT
    b.memes["caution"] = initial_caution(trait)
    table.meters["mess"] = 0.0
    dog.meters["on_perch"] = 0.0
    dog.meters["waiting"] = 0.0

    play_setup(world, a, b, dog, occasion)
    world.para()
    silly_idea(world, a, dog, lure, perch)
    warn(world, b, a, dog, lure, perch, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, parent, dog)
        world.para()
        teach_after_nearmiss(world, parent, a, b, dog, fix)
    else:
        defy(world, a, b, lure)
        world.para()
        lure_jump(world, dog, lure, perch)
        alarm(world, a, b, parent, dog)
        world.para()
        adult_arrives(world, parent, dog)
        clean_and_teach(world, parent, a, b, dog, fix, lure)

    world.para()
    ending(world, occasion, a, b, dog, fix, averted)

    outcome = "averted" if averted else "spill"
    world.facts.update(
        occasion=occasion,
        lure=lure,
        perch=perch,
        fix=fix,
        instigator=a,
        cautioner=b,
        dog=dog,
        parent=parent,
        relation=relation,
        outcome=outcome,
        spilled=world.get("table").meters["mess"] >= THRESHOLD or outcome == "spill",
        lesson_learned=a.memes["lesson"] >= THRESHOLD,
    )
    return world


OCCASIONS = {
    "picnic": Occasion(
        id="picnic",
        scene="the sunny backyard beside a low picnic table",
        setup="A striped cloth covered the table, cups of lemonade winked in the light, and sandwiches waited in tidy triangles.",
        food_line='"If Pip can march past the plates, he can be our picnic comedian," said one of the children.',
        ending="the backyard felt peaceful again,",
        tags={"picnic", "dog"},
    ),
    "porch_snack": Occasion(
        id="porch_snack",
        scene="the front porch during an after-school snack",
        setup="A small tray held apple slices, napkins, and a wobbling pitcher that looked much too proud of itself.",
        food_line='The snack looked so neat that it almost dared someone to disturb it.',
        ending="the porch stayed breezy and bright,",
        tags={"porch", "dog"},
    ),
    "tea_party": Occasion(
        id="tea_party",
        scene="the living room during a pretend tea party",
        setup="Paper flowers stood in a jar, crackers waited on a plate, and every chair had been invited to act very elegant.",
        food_line='Even the toy teapot seemed to be watching, ready for the silliest guest to arrive.',
        ending="the tea party finally looked proper again,",
        tags={"tea", "dog"},
    ),
}

LURES = {
    "sausage": Lure(
        id="sausage",
        label="sausage",
        phrase="a bit of sausage",
        smell="savory",
        warning="Table sausage is for people, not for dog tricks.",
        dog_safe=False,
        tags={"dog_food", "people_food"},
    ),
    "sandwich": Lure(
        id="sandwich",
        label="sandwich",
        phrase="half a sandwich corner",
        smell="toasty",
        warning="The table sandwich will only teach him to snatch lunch.",
        dog_safe=False,
        tags={"dog_food", "people_food"},
    ),
    "cupcake": Lure(
        id="cupcake",
        label="cupcake",
        phrase="a frosted cupcake top",
        smell="sweet",
        warning="Frosting is not for dogs, and a chair is not a stage.",
        dog_safe=False,
        tags={"dog_food", "sweets", "people_food"},
    ),
}

PERCHES = {
    "chair": Perch(
        id="chair",
        label="folding chair",
        phrase="the folding chair",
        wobble=2,
        skid="skritch-skrrt",
        stable_reason="a folding chair scoots when a quick dog lands on it",
        tags={"chair", "wobbly"},
    ),
    "crate": Perch(
        id="crate",
        label="milk crate",
        phrase="the milk crate",
        wobble=2,
        skid="thump-scrape",
        stable_reason="a milk crate rocks and can tip sideways",
        tags={"crate", "wobbly"},
    ),
    "bench": Perch(
        id="bench",
        label="picnic bench edge",
        phrase="the edge of the picnic bench",
        wobble=1,
        skid="bump-bump",
        stable_reason="a dog landing on the edge can bump plates and cups",
        tags={"bench", "wobbly"},
    ),
    "stone_step": Perch(
        id="stone_step",
        label="stone step",
        phrase="the stone step",
        wobble=0,
        skid="",
        stable_reason="a stone step does not wobble, so it would not make a comic spill",
        tags={"stone", "stable"},
    ),
}

FIXES = {
    "mat_biscuit": Fix(
        id="mat_biscuit",
        sense=3,
        treat="a crunchy dog biscuit",
        spot="the little blue mat",
        offer="mat",
        end_image="With one biscuit and one clear rule,",
        qa_text="used a dog biscuit to teach Pip to go to the little blue mat",
        tags={"dog_treat", "mat"},
    ),
    "kibble_towel": Fix(
        id="kibble_towel",
        sense=3,
        treat="three pieces of kibble",
        spot="the folded kitchen towel by the wall",
        offer="place",
        end_image="A tidy towel became a tiny stage, and",
        qa_text="used a few pieces of kibble to teach Pip to wait on the folded towel",
        tags={"dog_treat", "mat"},
    ),
    "carrot_rug": Fix(
        id="carrot_rug",
        sense=2,
        treat="a small carrot coin",
        spot="the round rug by the sofa",
        offer="rug",
        end_image="The round rug turned into the proper place for jokes, and",
        qa_text="used a safe dog snack to call Pip to the round rug and reward him there",
        tags={"dog_treat", "mat"},
    ),
}

GIRL_NAMES = ["Nia", "Lila", "Maya", "Tess", "Ava", "Rina", "Ella", "Zoe"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Finn", "Sam", "Leo", "Noah", "Eli"]
DOG_NAMES = ["Pip", "Zuzu", "Kito", "Dash"]
TRAITS = ["careful", "patient", "sensible", "curious", "chatty", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_fixes():
        return combos
    for occasion in OCCASIONS:
        for lure_id, lure in LURES.items():
            for perch_id, perch in PERCHES.items():
                if hazard_at_risk(lure, perch):
                    combos.append((occasion, lure_id, perch_id))
    return combos


@dataclass
class StoryParams:
    occasion: str
    lure: str
    perch: str
    fix: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    dog_name: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 7
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
    "basenji": [
        (
            "What is a basenji?",
            "A basenji is a small, quick dog breed with a curled tail. Basenjis are famous for making funny yodel-like sounds instead of ordinary barking.",
        )
    ],
    "people_food": [
        (
            "Why should dogs not grab food from the table?",
            "When dogs learn to snatch table food, they may jump near plates and cups and make a mess. Some people foods also are not good for dogs to eat.",
        )
    ],
    "sweets": [
        (
            "Why is frosting a bad treat for a dog?",
            "Frosting is very sugary and is made for people, not dogs. It can upset a dog's stomach and teaches the dog to beg for the wrong food.",
        )
    ],
    "chair": [
        (
            "Why can a folding chair be risky for a jumping dog?",
            "A folding chair can scoot or wobble when something lands on it fast. That makes it easy for nearby plates or cups to slide and spill.",
        )
    ],
    "crate": [
        (
            "Why can a milk crate tip over?",
            "A milk crate is light and can rock sideways if weight lands on the edge. A quick jump can turn it into a tippy little platform.",
        )
    ],
    "bench": [
        (
            "Why can the edge of a bench cause a spill?",
            "When something jumps onto the edge of a bench, the bump can shake the things nearby. If plates and cups are close, they can rattle and slide.",
        )
    ],
    "dog_treat": [
        (
            "Why is a dog treat better than table food for training?",
            "A dog treat is meant for the dog and keeps the lesson clear. It helps the dog learn where to go without begging at people's plates.",
        )
    ],
    "mat": [
        (
            "Why do people teach a dog to go to a mat?",
            "A mat gives the dog one clear place to wait. That makes family meals calmer because the dog knows where to be.",
        )
    ],
}
KNOWLEDGE_ORDER = ["basenji", "people_food", "sweets", "chair", "crate", "bench", "dog_treat", "mat"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, dog = f["instigator"], f["cautioner"], f["dog"]
    lure, perch, occasion = f["lure"], f["perch"], f["occasion"]
    if f["outcome"] == "averted":
        return [
            f'Write a short comedy for a 3-to-5-year-old about a basenji, a silly idea, and a lesson learned. Include the word "basenji".',
            f"Tell a cautionary dialogue story where {a.id} wants to tempt {dog.id} with {lure.label} near {perch.label}, but {b.id} talks {a.pronoun('object')} out of it.",
            f"Write a gentle story in which children almost make a lunch mess with a basenji, ask a grown-up instead, and end by teaching the dog a better trick on the floor.",
        ]
    return [
        f'Write a short comedy for a 3-to-5-year-old about a basenji, a table-food mistake, and a lesson learned. Include the word "basenji".',
        f"Tell a cautionary dialogue story where {a.id} teases a basenji with {lure.label} near {perch.label}, a funny spill happens, and a grown-up teaches a safer dog game.",
        f"Write a child-friendly story with jokes, direct speech, and a clear lesson that dogs should not be lured toward chairs and plates with people food.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, dog, parent = f["instigator"], f["cautioner"], f["dog"], f["parent"]
    lure, perch, fix, occasion = f["lure"], f["perch"], f["fix"], f["occasion"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and their basenji named {dog.id}. The children wanted the dog to be part of a funny meal-time game.",
        ),
        (
            f"What silly idea did {a.id} have?",
            f"{a.id} wanted to wiggle {lure.phrase} near {perch.phrase} so {dog.id} would hop up and make everyone laugh. The idea seemed funny, but it pulled the dog toward the wrong place.",
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} saw that {perch.phrase} was wobbly and guessed lunch could spill if the basenji jumped there. The warning came before the accident because {b.id} was thinking about what the fast dog might do next.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.extend([
            (
                f"What happened after {b.id} warned {a.id}?",
                f"{a.id} stopped and admitted that a laugh was not worth a mess. Then the children asked {parent.label_word} for help instead of teasing {dog.id} with table food.",
            ),
            (
                f"What did {parent.label_word} teach them to do?",
                f"{parent.label_word.capitalize()} showed them how to send {dog.id} to {fix.spot} with a proper dog reward. That made the trick funny and safe because the dog stayed on the floor.",
            ),
            (
                "What lesson did the children learn?",
                f"They learned that dog games should happen on the floor, not beside plates and wobbly furniture. Asking a grown-up first helped them keep both the joke and the lunch tidy.",
            ),
        ])
    else:
        qa.extend([
            (
                f"What happened when {a.id} teased {dog.id} with {lure.label}?",
                f"{dog.id} sprang toward {perch.phrase}, and the perch tipped enough to send lunch sliding. The comic mess happened because people food pulled the dog toward a wobbly place.",
            ),
            (
                f"How did {parent.label_word} fix the problem?",
                f"{parent.label_word.capitalize()} moved the tempting food away, cleaned up the spill, and {fix.qa_text}. That changed the dog's target from the table to a safe waiting place.",
            ),
            (
                "What lesson did the children learn?",
                f"They learned not to tease a dog with food from the table or invite a jump near cups and plates. A proper dog treat on the floor is safer and kinder, and it keeps the joke from turning into chaos.",
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"basenji"} | set(f["lure"].tags) | set(f["fix"].tags) | set(f["perch"].tags)
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        occasion="picnic",
        lure="sausage",
        perch="chair",
        fix="mat_biscuit",
        instigator="Milo",
        instigator_gender="boy",
        cautioner="Nia",
        cautioner_gender="girl",
        dog_name="Pip",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        occasion="tea_party",
        lure="cupcake",
        perch="crate",
        fix="kibble_towel",
        instigator="Lila",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        dog_name="Zuzu",
        parent="father",
        trait="chatty",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        occasion="porch_snack",
        lure="sandwich",
        perch="bench",
        fix="carrot_rug",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Maya",
        cautioner_gender="girl",
        dog_name="Dash",
        parent="mother",
        trait="patient",
        relation="siblings",
        instigator_age=6,
        cautioner_age=8,
    ),
    StoryParams(
        occasion="picnic",
        lure="cupcake",
        perch="chair",
        fix="mat_biscuit",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Eli",
        cautioner_gender="boy",
        dog_name="Kito",
        parent="father",
        trait="curious",
        relation="friends",
        instigator_age=5,
        cautioner_age=5,
    ),
]


def explain_rejection(lure: Lure, perch: Perch) -> str:
    if not perch.wobble:
        return (
            f"(No story: {perch.phrase} is too steady for this cautionary comedy. "
            f"If nothing wobbles, the basenji would not cause the lunch spill that gives the story its turn and lesson.)"
        )
    if not lure.tempting:
        return (
            f"(No story: {lure.label} would not honestly tempt the dog, so there is no reason for a risky jump.)"
        )
    return "(No story: this combination does not create a plausible comic hazard.)"


def explain_fix(fid: str) -> str:
    fx = FIXES[fid]
    better = ", ".join(sorted(x.id for x in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fx.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "spill"


ASP_RULES = r"""
hazard(L, P) :- tempting(L), wobble(P, W), W > 0.
sensible(F)  :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(O, L, P) :- occasion(O), lure(L), perch(P), hazard(L, P).

careful_now(T) :- trait(T), careful_trait(T).
init_caution(5) :- trait(T), careful_now(T).
init_caution(3) :- trait(T), not careful_now(T).

cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), impulse_init(I), A > I.

outcome(averted) :- averted.
outcome(spill) :- not averted.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for oid in OCCASIONS:
        lines.append(asp.fact("occasion", oid))
    for lid, lure in LURES.items():
        lines.append(asp.fact("lure", lid))
        if lure.tempting:
            lines.append(asp.fact("tempting", lid))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        lines.append(asp.fact("wobble", pid, perch.wobble))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("impulse_init", int(IMPULSE_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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

    clingo_fix, python_fix = set(asp_sensible()), {f.id for f in sensible_fixes()}
    if clingo_fix == python_fix:
        print(f"OK: sensible fixes match ({sorted(clingo_fix)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_fix)} python={sorted(python_fix)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a basenji, a tempting lunch, and a safer joke. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--occasion", choices=OCCASIONS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.perch and not PERCHES[args.perch].wobble:
        lure = LURES[args.lure] if args.lure else next(iter(LURES.values()))
        raise StoryError(explain_rejection(lure, PERCHES[args.perch]))
    if args.lure and args.perch:
        lure, perch = LURES[args.lure], PERCHES[args.perch]
        if not hazard_at_risk(lure, perch):
            raise StoryError(explain_rejection(lure, perch))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.occasion is None or combo[0] == args.occasion)
        and (args.lure is None or combo[1] == args.lure)
        and (args.perch is None or combo[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    occasion, lure, perch = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    dog_name = rng.choice(DOG_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)
    return StoryParams(
        occasion=occasion,
        lure=lure,
        perch=perch,
        fix=fix,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        dog_name=dog_name,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.occasion not in OCCASIONS:
        raise StoryError(f"(Unknown occasion: {params.occasion})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    lure = LURES[params.lure]
    perch = PERCHES[params.perch]
    fix = FIXES[params.fix]
    if not hazard_at_risk(lure, perch):
        raise StoryError(explain_rejection(lure, perch))
    if fix.sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        OCCASIONS[params.occasion],
        lure,
        perch,
        fix,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        dog_name=params.dog_name,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (occasion, lure, perch) combos:\n")
        for occasion, lure, perch in combos:
            print(f"  {occasion:12} {lure:10} {perch}")
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
            header = f"### {p.instigator}, {p.cautioner}, and {p.dog_name}: {p.lure} near {p.perch} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
